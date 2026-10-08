# UC-GW-007：按路由编排 Console Session ForwardAuth

状态：`ACCEPTED`

## 目标与范围

> Gateway 对路由目录明确授权给 Developer Console、Admin Console 的普通 HTTP/JSON Route，先经对应 BFF 的 Session ForwardAuth 把该 surface 的 HttpOnly Cookie 交换为唯一内部 `x-iwut-session`，再进入现有 route-specific Gateway ForwardAuth；未声明 surface、错误 Host 或任一前置认证失败均不得抵达 Auth/App 业务处理器。

本用例只拥有 Gateway 路由目录、Traefik Router/middleware 生成、现有凭据矩阵组合与失败不抵达语义。Console Cookie 的格式、密钥、轮换、登录事务、Origin/Fetch Metadata 判断、Session query/clear 与聚合逻辑属于 [ADR-CONSOLE-004](../../console/adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 和 [UC-CONSOLE-001](../../console/use-cases/UC-CONSOLE-001-establish-console-session.md)，本文引用而不复制。

首版只改变普通 HTTP/JSON 的 Console Host 流量。原生 gRPC 与 gRPC-Web 继续使用现有 Gateway 入口，不从浏览器 Cookie 建立 Session；OAuth/OIDC Portal Cookie 仍只属于 [UC-GW-002](UC-GW-002-authenticate-oauth-and-forward.md)，不能借本用例提前启用。

## 路由与 surface 输入

Gateway 路由目录新增每 Route 的显式集合 `consoleSurfaces`，允许值固定为 `DEVELOPER`、`ADMIN`。字段缺失或空集表示两个 surface 均关闭；未知值、重复值、非 HTTP/JSON Route 上的声明以及未配置目标 surface 都使目录装载失败。该字段只决定 Edge 是否生成对应 Console Router，不改变 Route 的 target、audience、Session、USER exchange 或下游凭据保留策略。

这是新的公网暴露语义，不能在 `iwut.gateway.routes/v2` 标识下静默加入；实现工作包应升级严格 schema，并让目录解析、运行时摘要、Traefik 生成与 `--check` 使用同一模型。surface 部署表至少固定：逻辑 ID、精确 Host 配置项、私有 BFF Session ForwardAuth 地址配置项和 BFF-owned Router/service 引用。实际 Host/地址由部署注入，但配置必须是单一精确值，不接受通配 Host、客户端 header/query/body 或认证响应改写。

只有同时满足以下条件的 Route 才可声明 `consoleSurfaces`：

- 支持 `HTTP_JSON`；
- Authorization 为 `FORBIDDEN`、OAuth delegation 为 `NEVER`、Portal Cookie 未启用；
- 不要求、允许或保留任何专用 terminal credential；
- 现有 Session 策略是 `FORBIDDEN`、`OPTIONAL` 或 `REQUIRED` 的一个已验证组合。

因此本用例不能把 OAuth Bearer、OIDC Basic/Portal Cookie、账号注销 token 或 high-risk proof 改造成 Console Cookie 的附带能力。以后确有需求时必须先扩展权威凭据设计和联合验收，不能只向 `consoleSurfaces` 增加 Route。

## Router 与 middleware 组合

每个 Console surface 使用自己的精确 Host。实现启用前，现有公共 API Router 必须绑定精确公共 API Host 或独立 entrypoint，不能继续以无 Host 的 path-only Router 接住 Console Host。每个 Console Host 的 Router 类别及固定优先级为：

| Router 类别 | 优先级 | 行为 |
| --- | ---: | --- |
| BFF-owned 登录、恢复、Session、聚合精确 method/path | `40000` | 转发给对应 BFF；不进入普通 API chain |
| 目录生成的 Console 普通 API exact Route | `30000` | 执行本用例的 Console chain |
| `/auth-center`、`/app-center` 等 API 前缀兜底拒绝 | `20000` | 未登记 method/path 返回 404，不落入 Web SPA |
| 静态资源和前端导航 | `1000` | 转发对应 Web artifact |

BFF-owned 列表必须由版本控制输入精确提供；禁止一个 `/api/*` 通配代理覆盖普通 Gateway API，也禁止静态 fallback 接住未知 API。Developer 与 Admin 即使声明同一业务 Route，也生成不同 Host、不同 BFF ForwardAuth 和不同 Router 名称。

对已声明 surface 的普通 API Route，生成的顺序固定为：

1. `scrub-untrusted-console-headers` 删除浏览器提供的 `x-iwut-session`、USER/service/delegation identity、内部 route/audience/policy header 和不可信 Forwarded 别名；保留 Cookie 供下一步读取。Authorization 与已知 terminal header 不送给 BFF，但保留到现有 Gateway ForwardAuth，使既有凭据矩阵仍能拒绝而不是被静默忽略。
2. 当 Route Session 为 `OPTIONAL` 或 `REQUIRED` 时，调用该 surface 唯一的 BFF Session ForwardAuth。调用只允许 Cookie、Origin、`Sec-Fetch-*`、request ID 以及 Traefik 重建的 method、URI、host、scheme；不转发业务 body，`trustForwardHeader=false`，成功响应 body 为空，`authResponseHeaders` 只允许 `x-iwut-session`。
3. 在任何现有 Gateway 认证组件之前完全删除 Cookie。Route Session 为 `FORBIDDEN` 时跳过步骤 2，但仍执行步骤 1 和本步骤，确保 ambient Console Cookie 既不阻止匿名/self-authenticated Route，也不进入 Gateway 核心。
4. 执行现有 route-specific Gateway ForwardAuth。它按原 Route 的 Session/Authorization/terminal/USER exchange 矩阵重新核对 method/URI 和凭据；BFF 不能返回 routeId、audience、USER identity 或 target。
5. 执行现有 route-specific post-auth scrub、前缀处理和固定 upstream 转发，并在终端响应中删除内部身份与认证辅助 header。

Router/middleware 顺序是安全合同，生成器不得因去重而重排。任何声明组合若无法生成上述完整链，必须阻止启动，不能回退到公共 Router 或直接 upstream。

固定 Traefik `v3.7.13` 的 ForwardAuth 在目标连接拒绝时自身返回 `500`。本用例把 BFF 基础设施故障契约固定为任意 HTTP `5xx`，不要求 Edge 把不同 transport failure 重新分类为精确 `503/504`；BFF handler 自身明确返回的 `503` 也属于该集合。无论具体 `5xx` 为何，请求都必须在 Gateway ForwardAuth 与业务 upstream 前失败关闭，响应不得设置或清除 Console Cookie，前端也不得据此清理仍可能有效的登录态。

## Session 策略组合

| 现有 Route Session | Console Session ForwardAuth | 进入 Gateway 核心的结果 |
| --- | --- | --- |
| `FORBIDDEN` | 不调用 | 浏览器 `x-iwut-session` 与 Cookie 均已删除；现有 Route 继续禁止 Session |
| `OPTIONAL` | 调用 | 无 Cookie 时不产生 header，按现有匿名分支继续；有效 Cookie 产生唯一 Session；坏 Cookie 不降级 |
| `REQUIRED` | 调用 | 无 Cookie 时不产生 header并由现有 Gateway 返回缺少 Session；有效 Cookie 产生唯一 Session；坏 Cookie 不降级 |

BFF ForwardAuth 只可在成功响应返回零个或一个 `x-iwut-session`。无目标 Cookie 必须返回成功且无该 header；出现目标 Cookie 后，其重复、畸形、过期、无法解密或错误 surface 由 BFF 失败关闭。Gateway 不解析 Cookie，不持有 Console keyring，也不缓存 Cookie→Session 结果；它仍对 BFF 返回的 Session 执行原有单值、形状及 Route 策略校验。

该适配不能放宽现有凭据矩阵。浏览器伪造的 Session 永远不能替代 Cookie；Authorization 或 terminal credential 仍由现有 Gateway Route 判为禁止；BFF 返回 Session 也不能满足一个 Session `FORBIDDEN` Route，因为这类 Route 根本不调用 BFF。

## BFF-owned 路径、Cookie 与递归边界

BFF-owned 登录 Begin/Complete、结果不确定恢复、Session query/clear 和显式聚合路径使用更高优先级 exact Router，直接以 BFF 为 service。它们不经过 Console 普通 API chain；特别是匿名设备/邮箱登录不能因 ambient Console Cookie 自动生成 `x-iwut-session`。

BFF 调 Gateway 时必须使用仅部署内部可达、且不匹配任一 Console Host Router 的入口或精确内部 Host，并完全不携带浏览器 Cookie。该内部调用仍匹配同一 Gateway Route Catalog 和现有 route-specific ForwardAuth，但不能再次调用 Console Session ForwardAuth。拓扑或 Host 配置若可能递归，配置检查/启动必须失败。

普通 Console API Router 对最终 backend 响应无条件删除 `Set-Cookie`，不得让 Auth/App 创建、覆盖或清除 Console Cookie。只有 BFF-owned 登录/Session 路由的 BFF 响应可以修改对应 surface Cookie；首版普通 API 的 Session ForwardAuth 响应不借 `addAuthCookiesToResponse` 修改 Cookie。下游确认 `SESSION_INVALID` 后，浏览器按 UC-CONSOLE-001 调用本 surface 的 BFF Session clear 路径；Gateway/Auth/BFF 不因普通网络或 5xx 自动清除 Cookie。

## 业务规则

<a id="br-gwr-026"></a>
### BR-GWR-026：Console surface 逐 Route 显式启用且默认关闭

Developer/Admin 暴露只能来自当前 Route 的 `consoleSurfaces` 与受信 surface 部署表。缺失声明、未知 Host、未知 method/path、未配置 surface 或目录/生成摘要漂移全部失败关闭；不能用 Host 通配、API 前缀通配、客户端标记或“剩余 Route 继承”扩大暴露。

公共 API Router 与 Console Host 必须隔离，Console API 前缀必须有未知 Route 拒绝兜底。Router 优先级、Host 和 service target 都由生成配置固定，BFF 或认证响应不能改写。

<a id="br-gwr-027"></a>
### BR-GWR-027：Console 适配服从既有 Session 与凭据矩阵

是否调用 BFF 只由已匹配 Route 的 Session `FORBIDDEN/OPTIONAL/REQUIRED` 决定；Cookie 是否存在不能选择 Route 或策略。`OPTIONAL` 只允许 Cookie 完全缺失时匿名，一旦目标 Cookie 出现，BFF 拒绝不得被 Gateway 转成匿名。

Console 声明不改变 Authorization、OAuth、terminal credential、USER exchange、audience 或 preserve 规则。静态校验拒绝本用例不支持的组合；既有禁止凭据仍由 Gateway 核心分类拒绝，不能在前置层静默删除后继续业务请求。

<a id="br-gwr-028"></a>
### BR-GWR-028：只有对应 BFF 能从 Cookie 产生唯一 Session

外部 `x-iwut-session` 和内部身份在 BFF 前清除；Gateway 只接受本次对应 surface ForwardAuth 成功响应复制的零个或一个 Session。ForwardAuth 不接收业务 body，不返回 USER/service/delegation identity、Authorization、routeId、audience、target 或任意 header 正则集合。

Cookie 在进入现有 Gateway ForwardAuth 前必须完全删除。Gateway 核心继续把任何可见 Cookie 视为禁止凭据，且不实现 Console Cookie 解密、密钥轮换或 Session authority。

<a id="br-gwr-029"></a>
### BR-GWR-029：BFF-owned 流程、响应 Cookie 与内部调用隔离

BFF-owned exact Route 优先于普通 Console API，登录/恢复/聚合不会穿过 Cookie→Session chain；BFF→Gateway 使用非 Console 内部入口，不能递归。普通 backend 的任何 `Set-Cookie` 均被删除，只有对应 BFF-owned 登录/Session 响应能修改本 surface Cookie，两个 surface 不能互相设置或清除 Cookie。

这条边界不让 Gateway 判断登录事务或 Session 清理时机；这些语义仍由 Console 权威设计和 BFF 实现拥有。

<a id="br-gwr-030"></a>
### BR-GWR-030：HTTP-only、失败不抵达与真实隔离验收

本用例只生成 HTTP/JSON Console Router。原生 gRPC/gRPC-Web 配置、认证 adapter 和现有三协议 Route 不因 `consoleSurfaces` 改变；浏览器 Cookie 不能通过 gRPC metadata 或 gRPC-Web header 获得等价适配。

BFF 拒绝或不可用、Gateway 身份交换失败、错误 Host/Route、目录漂移及 middleware 缺失都必须在业务 upstream 前终止。只测 BFF handler 或生成 YAML 不足以完成验收；必须用真实 Traefik、两个独立 BFF、Gateway ForwardAuth、Auth 和记录调用的 backend 验证 Router 隔离与调用次数。

## 错误与失败语义

- BFF 对已提供 Cookie 的确定无效拒绝：返回稳定未登录错误，Gateway Auth 与业务 upstream 零调用；不得在 OPTIONAL Route 匿名降级。
- BFF 不可用或 timeout：HTTP 5xx，Gateway ForwardAuth 与业务 upstream 零调用，不设置或清除可能仍有效的 Cookie。
- REQUIRED Route 无 Cookie：BFF 成功且不返回 Session，由现有 Gateway 缺少凭据语义拒绝。
- Authorization/terminal credential 混入：由现有 Route 凭据矩阵拒绝，不因 Console 前置适配变成可用。
- Gateway/Auth 对 Session 的拒绝或依赖故障：保持 UC-GW-001/003/004 的既有分类，业务 upstream 零调用；Console 后续清理由 UC-CONSOLE-001 编排。
- 未声明 surface、错误 Host、未知 method/path：HTTP 404 或部署的统一拒绝，不落入公共 API Router、BFF 通配代理或 SPA。

日志、trace、metrics 和错误不得包含 Cookie、上游 Session、内部 JWS、Authorization 或 terminal credential。可记录 surface、routeId、requestId、失败阶段、结果类别与耗时；两个 ForwardAuth 阶段必须可以区分，但不能形成高基数 Host/Cookie 标签。

## 验收场景

1. 目录缺失 `consoleSurfaces` 时不生成 Console Router；未知/重复 surface、非 HTTP Route、未配置 surface 和不受支持凭据组合在装载期失败。
2. Browser 伪造 `x-iwut-session`、USER/service/delegation identity、routeId、audience 和 Forwarded 不能覆盖 BFF 结果或改变 target；Authorization/terminal credential 仍被现有 Route 拒绝。
3. 有效 Developer Cookie 只在 Developer Host/声明 Route 产生唯一 Session；交换到 Admin Host、错误 key/name/version、重复、过期、cross-origin/cross-site 时 Gateway Auth 与 backend 调用均为零，反向同样成立。
4. OPTIONAL 无 Cookie 以匿名进入现有 Gateway；REQUIRED 无 Cookie 由现有 Gateway 拒绝；FORBIDDEN 即使有 ambient Cookie 也不调用 BFF且下游看不到 Cookie/Session。
5. 到达 Gateway ForwardAuth 的普通 Console 请求恰好有零个或一个 BFF Session 且无 Cookie；Gateway 继续完成既有 USER exchange 或 DIRECT Session preserve，不改变 audience 和业务授权。
6. BFF-owned 登录/恢复/Session/聚合路径只到对应 BFF；BFF 的匿名 Gateway 调用不携带 Console Session、不再次命中 Console ForwardAuth，也不存在递归调用。
7. Auth/App 返回任意 `Set-Cookie` 时浏览器收不到；只有 BFF-owned 登录/Session 响应能设置或清除对应 Cookie。
8. 未声明 Route、错误 Host、API 前缀未知 path/method、较低优先级公共 Router 与静态 fallback 都不能绕过 Console chain 抵达 backend。
9. 真实 Traefik + Developer BFF + Admin BFF + Gateway ForwardAuth + Auth + 记录式 backend 联合覆盖成功、匿名、无凭据、坏 Cookie、surface 交换、BFF 不可用 5xx、Gateway 身份失败和 backend `Set-Cookie`，并断言每阶段调用次数及失败响应无 `Set-Cookie`。

## 依赖与实施边界

依赖 [ADR-CONSOLE-004](../../console/adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)、[UC-CONSOLE-001](../../console/use-cases/UC-CONSOLE-001-establish-console-session.md)、[UC-GW-001](UC-GW-001-authenticate-and-forward.md)、[UC-GW-003](UC-GW-003-attach-optional-user-identity.md)、[UC-GW-004](UC-GW-004-forward-optional-session-to-auth.md) 与 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md)。Console ADR/UC 与本 Gateway 用例均已接受。Gateway-owned 双 surface chain、BFF 内部 exact/deny Router、共享 Traefik 合并装载及当前 capability/登录/Session/SPA 路由已完成本地联合验收；UC-GW-007 仍为 `IN_PROGRESS`，直到 UC-CONSOLE-001 完成显式重发/迟到响应协调、完整结果恢复和真实 Auth/邮件链路验收。

实现工作包已把严格 route schema 升级为 `config/routes.v3.yaml`，完成逐 Route surface、部署 Host/BFF 地址校验、Traefik 生成与漂移检查；私有 Session ForwardAuth 仍由对应 Console BFF 提供。该工作包不修改 Auth/App Proto、不新增 Gateway 数据库/Redis、不把 BFF 登录或聚合逻辑移入 Gateway，也不启用 UC-GW-002。当前 `worktrees/iwut-gateway-ddd` 有未提交的 Go、路由目录、Traefik 生成物和部署说明改动；真实 Traefik + 两个 BFF + Gateway ForwardAuth + Auth/backend 联合 E2E 已覆盖成功、匿名、坏/过期/重复 Cookie、surface 隔离、伪造 Forwarded、Auth 拒绝、backend `Set-Cookie`、backend `500` 保持、BFF 连接拒绝，以及内部 exact/deny Router 的非递归和 Cookie 失败关闭。Gateway-owned topology 已本地验证，但 UC-CONSOLE-001 的显式重发/迟到响应协调、完整结果恢复及真实 Auth/邮件链路仍未完整验收，所以 UC 保持 `IN_PROGRESS`，不记为 `COMPLETE`；API submodule 不因本设计修改。

实施所有权分两部分：Gateway 包与生成器拥有普通 Console API exact Router、API 前缀 deny Router、各 surface Session ForwardAuth 引用，以及从同一 Route Catalog 生成的 BFF→Gateway 私有 entrypoint exact/deny Router；该内部 chain 复用 route-specific Gateway ForwardAuth，但绝不调用 Console Session ForwardAuth。Console deployment composition 拥有优先级 `40000` 的 BFF-owned `/api/*` 登录、Session、恢复、聚合 exact Router、优先级 `1000` 的 SPA/static Router、内部 entrypoint 的网络隔离和 BFF URL 注入。共享固定 Traefik 已验证当前登录/Session/SPA、两份动态文件合并、内部入口非递归、Cookie 拒绝及未知路径关闭；验收场景 6 的 Gateway-owned 部分已闭合，真实 Auth/邮件链路、页面和恢复仍依赖 UC-CONSOLE-001，因此 UC-GW-007 保持 `IN_PROGRESS`。

## 接受记录

2026-10-07 接受本设计：每 Route 使用 `consoleSurfaces` 并升级 route schema；固定 Router 优先级 `40000/30000/20000/1000` 及公共 API Host/entrypoint 隔离；首版排除 Authorization/OAuth/terminal credential Route；普通 API ForwardAuth 不直接清 Cookie，确认 `SESSION_INVALID` 后统一经 BFF-owned Session clear Route 清理。实现工作包已启动，但接受不表示能力已经可用。

2026-10-07 接受失败契约修订：BFF Session ForwardAuth 的基础设施故障允许返回任意 HTTP `5xx`，不再要求精确 `503/504`。验收不变量是失败关闭、Gateway ForwardAuth 与业务 upstream 零调用、响应无 `Set-Cookie`；固定 Traefik `v3.7.13` 的连接拒绝实测为 `500`，不再构成实现阻塞。

2026-10-08 接受内部入口所有权细化：Gateway 从同一 Route Catalog 生成独立 `console-bff-internal` entrypoint 的 exact/deny Router 并复用既有 Gateway ForwardAuth chain；Console deployment 负责该端口仅内部可达、向两个 BFF 注入 URL，以及 BFF-owned 路由。联合 E2E 允许为验证显式发布内部端口，但生产部署禁止公网发布。该修订不改变 Cookie、登录事务和聚合仍由对应 BFF 独占的边界。
