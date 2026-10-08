# ADR-CONSOLE-004：Console 混合 BFF 与 Session ForwardAuth 流量边界

状态：`ACCEPTED`

日期：2026-10-07

## 背景

[ADR-CONSOLE-001](ADR-CONSOLE-001-repository-and-application-boundaries.md) 已决定 Developer Console 与 Admin Console 使用独立应用、BFF、Origin、Cookie 和 Session 边界。[UC-CONSOLE-001](../use-cases/UC-CONSOLE-001-establish-console-session.md) 又要求 Auth Session token 永不进入浏览器可读状态，并由 Console 服务端设施把安全 Cookie 恢复为 Gateway 使用的 `x-iwut-session`。

如果所有登录后请求都由 Hono BFF 完整代理，BFF 会转发大量无需聚合的普通 Auth/App HTTP/JSON 请求及响应体；如果每套 Console 还部署独立 Traefik，则重复承担 TLS、Router 和 middleware 运行时。另一方面，把登录、恢复、Cookie、聚合和所有 BFF 行为整体并入 Gateway，会让 Gateway 拥有前端流程状态并扩大其职责。

现有 Gateway 已有按路由生成的 Traefik middleware chain，并坚持 Gateway 认证核心拒绝 Cookie、只按路由凭据矩阵消费 `x-iwut-session`。Console 需要在不改变该不变量的前提下，让普通已登录请求避开 BFF 的请求体代理。

## 决定

采用共享 Traefik 与混合 BFF 流量模式。两个 Hono BFF 保留为独立部署和 Cookie 权威；普通 Console API 请求由共享 Traefik 调用对应 BFF 的轻量 Session ForwardAuth 后进入现有 Gateway ForwardAuth，登录、恢复和聚合请求仍由 BFF 处理。

### 请求分类

| 请求类别 | 路径所有者 | 流量路径 |
| --- | --- | --- |
| Console 静态资源与前端导航 | 对应 Console Web 构建 | Browser → 共享 Traefik → Web artifact |
| 登录 Begin/Complete、Session query/clear、结果不确定恢复 | 对应 Console BFF | Browser → 共享 Traefik → BFF → Gateway/Auth |
| 明确登记的聚合或服务端组合请求 | 对应 Console BFF | Browser → 共享 Traefik → BFF → Gateway/Auth/App |
| 明确允许该 Console surface 使用的普通 HTTP/JSON API | Gateway 路由目录 | Browser → 共享 Traefik → Console Session ForwardAuth → 现有 Gateway ForwardAuth → Auth/App |

BFF 自己调用 Gateway 时使用部署控制的内部入口，不再次经过 Browser Cookie 的 Console middleware chain，避免递归和匿名登录被残留 Console Cookie 污染。该入口的 exact Router、API 前缀 deny 与 route-specific Gateway ForwardAuth chain 由 Gateway 从同一 Route Catalog 生成；Console deployment 只负责将监听限制在内部网络、向两个 BFF 注入 URL，并保证容器端口不被公网发布。BFF 发起调用时不得转发浏览器 Cookie。

首版只把普通 HTTP/JSON 请求纳入此模式。原生 gRPC 与 gRPC-Web 继续遵循现有 Gateway 协议适配设计；若以后需要让浏览器 Cookie 驱动 gRPC-Web，必须另行设计凭据式 CORS、失败编码和同源边界。

### 普通 API middleware chain

对每个被显式登记的 Console surface 和 Gateway HTTP/JSON route，生成以下有序链：

```text
Browser
  │ Console HttpOnly Cookie
  ▼
Traefik Console Router（精确 Host + 精确 route）
  │
  ├─ 1. scrub-untrusted-console-headers
  │      删除客户端提供的 x-iwut-session、x-iwut-identity、
  │      service/delegation identity 和不可信 Forwarded 别名；
  │      Authorization/terminal credential 不进入 BFF auth 子请求，
  │      但保留在原请求上供 Gateway 凭据矩阵拒绝；保留 Cookie 与必要浏览器请求元数据
  │
  ├─ 2. 对应 BFF 的 Console Session ForwardAuth
  │      解密本 surface Cookie，校验请求来源，只返回 x-iwut-session
  │
  ├─ 3. remove-cookie
  │      在进入现有 Gateway 认证链前完全删除 Cookie
  │
  ├─ 4. 现有 route-specific Gateway ForwardAuth
  │      按既有凭据矩阵完成 Session 校验、USER identity 签发与路由核对
  │
  ├─ 5. 现有 route-specific post-auth scrub
  │      按路由决定是否向 Auth 保留 Session，并清理内部凭据/响应头
  ▼
Auth / App
```

顺序是安全语义，不能重排。第一步必须使浏览器无法伪造 Session；第三步必须保证现有 Gateway ForwardAuth 永远看不到 Cookie。普通直达后端的 Console Router 还必须删除响应中的 `Set-Cookie`；只有明确的 BFF Session 路由可以签发或清除 Console Cookie。

Traefik 的 Console ForwardAuth 使用正向请求头 allowlist，至少只传递该 BFF 所需的 Cookie、Origin、`Sec-Fetch-*`、请求 ID，以及由 Traefik 重建的 method、URI、host、scheme。它不得转发业务 body，`trustForwardHeader` 必须为 false，成功响应 body 为空，`authResponseHeaders` 只允许单个 `x-iwut-session`。

### 路由驱动与默认关闭

Gateway 的人工维护路由目录必须显式决定一个 HTTP/JSON route 是否可经 Developer Console、Admin Console 或两者的 Cookie 适配器访问。未声明的 surface 默认不生成 Console Router；不能用一个 Host 通配 Router 把全部 Gateway 路由自动暴露给两个 Console。

具体 schema 由 Gateway 自己的 ADR/实现固定，但必须满足：

- surface 选择和 ForwardAuth 地址来自受版本控制的生成输入，不读取客户端 header、query 或 body；
- Console Cookie 的必需、可选或禁止直接服从该 route 已有 Session 凭据策略，BFF 不维护第二套路由目录；
- Session 禁止的 route 不调用 BFF ForwardAuth，只清除 Cookie，不把它转换为 Session；
- Session 可选或必需的 route 调用同一个 surface ForwardAuth；没有 Cookie 时 ForwardAuth 成功但不返回 `x-iwut-session`，再由现有 Gateway route policy 决定匿名通过或以 `SESSION_INVALID` 拒绝；
- 一旦请求携带目标 Cookie，重复、无效或过期必须在 BFF ForwardAuth 失败关闭，不能在可选 route 上静默降级为匿名；
- BFF-owned 路径使用更精确的 Router/优先级，不能误入普通 API chain；普通 API 也不能命中跳过 Console Session ForwardAuth 的同 Host Router。

surface 暴露只决定 Edge 流量路径，不授予 Developer、Reviewer 或平台管理员权限；最终业务授权仍由 Auth/App 使用可信身份完成。

### Cookie 与 ForwardAuth 所有权

Developer BFF 和 Admin BFF 仍分别是各自 Console Cookie 的唯一权威：

- 分别签发、解密、到期和清除自己的 `__Host-` Cookie；
- 使用不同 Cookie 名、Origin、密钥/轮换 keyring 和会话命名空间；
- 不接受另一个 surface 的 Cookie，也不共享可互解密的默认密钥；
- 登录 Complete 仍由 BFF 接管 Auth Session secret，并绑定自身保存的登录事务上下文；
- ForwardAuth 只做 Cookie 到单个上游 Session 的适配，不创建登录流程、不签发 USER identity、不判断产品权限。

Console Session ForwardAuth 端点仅对 Traefik/部署内部网络开放，不作为 Browser API 发布。不得在 Gateway 与 BFF 中复制两套 Cookie 加密实现或让二者共同持有相同解密密钥。若未来要消除 BFF 容器，必须先以新 ADR 建立唯一的 Console Session Authority 及受保护的 mint/open/clear 内部契约。

共享 Traefik 还提供一个仅供 BFF 调用的独立内部 entrypoint。它不匹配 Console Host、不调用任一 Console Session ForwardAuth，也不公开 `/internal/forward-auth`；只接受 Gateway Route Catalog 已登记的精确 HTTP/JSON method/path，未知 API 由内部 deny Router 关闭。该端口只在本地联合 E2E 显式发布，生产容器或编排不得把它暴露到公网负载均衡器。

### 请求来源与失败语义

ForwardAuth 对 Browser API 使用方法相关的来源校验：

- 会改变状态的方法必须同时具有本 surface 的精确 Origin 和 `Sec-Fetch-Site: same-origin`；
- GET/HEAD 等安全读取在 Origin 缺失时，仍必须具有可信 Traefik 重建的 host/scheme 和允许的同源 Fetch Metadata；若提供 Origin，则必须精确匹配；
- cross-site、重复/畸形来源头、导航到 API 路径或不符合 allowlist 的 Fetch Metadata 失败关闭；
- SameSite Cookie 只是附加防线，不替代上述校验。

没有 Console Cookie 时，ForwardAuth 返回成功且不产生 Session，由现有 route policy 处理 REQUIRED/OPTIONAL；请求一旦携带目标 Cookie，无效、重复或过期必须返回稳定的未登录错误。普通 API 的 ForwardAuth 拒绝不返回 `Set-Cookie`，Cookie 只能由显式 BFF-owned Session 路由设置或清除。ForwardAuth 自身或其网络依赖不可用时返回任意 HTTP 5xx；具体状态由固定 Edge 实现决定，但必须失败关闭、不得进入 Gateway Auth 或业务 upstream，也不能清除仍可能有效的 Cookie。

如果 Cookie 解密成功，但后续 Gateway/Auth 返回 `SESSION_INVALID`，前端按 UC-CONSOLE-001 调用本 BFF 的 Session clear 接口并回到未登录状态；前置 ForwardAuth 不重复调用 Auth 来预判该结果。所有认证响应使用 `Cache-Control: no-store`，不得缓存 Cookie 到 Session 的交换结果。

## 验证要求

实现至少覆盖：

1. Browser 伪造的 `x-iwut-session`、`x-iwut-identity`、Authorization 和 terminal credential 在 BFF ForwardAuth 前被删除，不能覆盖解密结果。
2. Developer/Admin Cookie 交换、Cookie 名重复、错误 key/version、过期、跨 Origin 和 cross-site Fetch Metadata 均被拒绝，backend 调用次数为零。
3. 携带有效 Console Cookie 的普通 API 到达现有 Gateway ForwardAuth 时恰好有一个内部 `x-iwut-session` 且完全没有 Cookie；无 Cookie 的 OPTIONAL route 没有 Session，REQUIRED route 被现有 Gateway policy 拒绝；Gateway 后续仍按 route policy 清理或保留 Session。
4. 未显式声明 surface 的 route、错误 Host、未知 path/method 和能够绕过 Console ForwardAuth 的候选 Router 均不抵达 backend。
5. BFF 登录和恢复路由不进入普通 API chain；匿名邮箱/设备 Begin 请求不携带现有 Session。
6. 普通 backend 即使返回 `Set-Cookie` 也不能修改 Console Cookie；只有 BFF-owned Session 响应可以设置/清除它。
7. Console ForwardAuth 基础设施 5xx 不清除 Cookie，且 Gateway ForwardAuth/业务 upstream 调用均为零；下游 `SESSION_INVALID` 触发客户端经 BFF 清理，网络/业务 5xx 不触发清理。
8. 使用真实 Traefik、两个 BFF、现有 Gateway ForwardAuth、Auth 和记录调用的 backend 完成隔离 E2E；只直接调用 ForwardAuth handler 不构成验收。
9. BFF 内部 entrypoint 对登记 Route 只调用一次 Gateway ForwardAuth、完全不调用 Console Session ForwardAuth；即使 BFF 不可用仍不会递归。携带 Cookie、未知 API 或 `/internal/forward-auth` 的内部请求均失败关闭且不抵达 backend。

## 结果

优点：

- 普通请求体和响应体不再经过 Hono BFF 二次代理；
- 两套 Console 可以复用现有 Traefik Edge，避免重复 Traefik 容器和配置；
- Gateway 核心继续拒绝 Cookie，已有凭据矩阵与 Auth/App 授权边界不被绕过；
- BFF 仍单独拥有 Cookie 密钥、登录竞态和聚合逻辑，两个 surface 保持独立会话。

代价：

- 普通请求包含 Console Session ForwardAuth 和现有 Gateway ForwardAuth 两次有界认证子请求；
- BFF 不再只是页面 API，其 ForwardAuth 可用性会影响本 surface 的普通 API；
- Traefik 生成器必须理解 surface 暴露、middleware 顺序、Router 优先级和响应 `Set-Cookie` 清理；
- 共享 Traefik 扩大配置错误的影响面，需要真实 Host/Router 隔离测试。

## 考虑过的替代方案

### 所有 Console 请求完整经过 BFF

Cookie 所有权简单，但普通单服务请求产生额外 body 代理、序列化和连接管理；不作为默认路径，登录、恢复和聚合仍保留此模式。

### 把整个 BFF 合并进 Gateway

可以减少进程数量，但会让 Gateway 拥有前端登录事务、Cookie、聚合和页面恢复语义，并扩大两个 Console 密钥的共同故障域，因此不采用。

### Gateway 与 BFF 共同实现 Cookie 加解密

需要共享密钥、跨语言同步密文格式和轮换行为，容易形成两个权威实现，因此禁止。未来若要移动所有权，必须先建立单一 Session Authority，再一次性迁移签发与解密职责。

## 修订记录

2026-10-07 修订并接受基础设施失败分类：固定 Traefik `v3.7.13` 在 ForwardAuth 连接拒绝时实测返回 HTTP `500`，因此不再要求 Edge 把所有不可用状态强制映射为 `503/504`。权威语义改为任意 HTTP 5xx，但失败关闭、Gateway Auth/业务 upstream 零调用和不清 Cookie 保持不变；不得为统一状态码引入会读取 Console Cookie 的 Gateway 代理或把业务 5xx 一并重写的全局错误 middleware。
