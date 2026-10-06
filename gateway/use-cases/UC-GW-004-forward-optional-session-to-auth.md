# UC-GW-004：向 Auth 自认证入口保留可选 Session

状态：`PROPOSED`

## 目标与范围

> Gateway 对明确登记的 Auth 自认证接口允许 Session 完全缺失；若终端提供 Session，则只把这一个原始 Session 保留给 Auth，不执行 USER 身份交换。Session 的缺失与存在可以选择 Auth 的业务分支，但坏 Session 绝不能被删除后降级为匿名请求。

首批消费者是 [UC-AUTH-011](../../auth-center/use-cases/UC-AUTH-011-set-and-activate-email.md) 的两个双模式入口：

- `EmailBindingService/BeginSetEmail`；
- `EmailBindingService/CompleteSetEmail`。

注册模式允许完全无 Session；本人绑定/更换模式由 Auth 要求并验证 Session。Gateway 不解析请求正文中的 mode/oneof，不判断邮箱、operation 或账号归属，也不为这两个方法签发 `x-iwut-identity`。

`GetOwnEmailBinding` 始终要求 Session，属于 UC-GW-001 已有的必需 DIRECT Session 行为；它可与本用例同批实施，但不是“可选 Session”语义的一部分。本用例也不扩展到公开 App 查询、OAuth/OIDC、Cookie、Authorization 或任意 Auth package 通配路由。

## 路由策略

| RPC | 外部 HTTP | Session | USER 交换 | 下游保留 |
| --- | --- | --- | --- | --- |
| `EmailBindingService/BeginSetEmail` | `POST /auth-center/v1/email-bindings` | `OPTIONAL` | `NEVER` | Session 存在时仅保留 Session |
| `EmailBindingService/CompleteSetEmail` | `POST /auth-center/v1/email-bindings/{operation_id}/completion` | `OPTIONAL` | `NEVER` | Session 存在时仅保留 Session |

两条 Proto route 均目标支持 HTTP/JSON、原生 gRPC 和 gRPC-Web。Authorization、Cookie、外来 USER/委托身份、专用 terminal header 均不允许。路由策略固定为 `AUTH_OPTIONAL_DIRECT_SESSION`；不能根据请求正文、Session 外形或 Auth 响应改选另一个 Route。

## 主流程

1. 使用与转发相同的规范化 method/path 或 exact gRPC full method 唯一匹配 Route，并先删除外来内部身份与控制头。
2. 在调用 Auth 前检查全部终端认证载体。Session 完全缺失时选择无 Session 分支；只要出现 Session header/metadata 就选择有 Session 分支。
3. 无 Session 分支不调用 UC-AUTH-010、不构造空 Session 或匿名身份，清除其它未声明凭据后把原业务请求转发给 Auth。
4. 有 Session 分支要求单一、无逗号合并且符合设备协议载体形状的 `x-iwut-session`；Gateway 不在线判断撤销、账号状态或 operation 绑定。
5. Gateway 不执行身份交换，仅把唯一原始 Session 保留给固定 Auth upstream，并转发一次业务请求。
6. Auth 根据 UC-AUTH-011 判断注册或本人绑定分支并完成最终 Session 校验；Gateway 原样保持其业务/认证响应，不把请求凭据写入终端响应。

## 业务规则

<a id="br-gwr-014"></a>
### BR-GWR-014：可选 DIRECT 只由精确 Route 声明

`OPTIONAL + USER NEVER + preserve Session when present` 是静态目录中的有限合法组合，只能用于下游明确自行认证且允许 Session 缺失的精确方法。它不从 `DIRECT`、Auth 服务前缀或请求实际携带的 header 自动推导，也不使其它 DIRECT route 获得可选 Session。

Session 是否存在只能选择“无 Session 下传”或“原始 Session 下传”，不能改变 target、audience、RPC、HTTP path 或协议。Gateway 不读取 EmailMode、operation 状态或消息 oneof 决定凭据策略；业务正文仍由生成 API 与 Auth 严格解码。

<a id="br-gwr-015"></a>
### BR-GWR-015：出现 Session 后不得匿名降级

只有 `x-iwut-session` 完全缺失才进入无 Session 分支。空白、多值、逗号合并、别名或非规范形状在 Gateway 失败；规范形状但已过期、撤销、账号不可用、与 operation 不匹配等语义由 Auth 拒绝。Gateway 不得在任何拒绝后删除 Session 并重新以无 Session 请求调用 Auth，也不得把同一业务请求重放到注册分支。

由于 Auth 本身是业务 upstream，规范形状 Session 的权威有效性检查发生在 Auth；这不等于 Gateway 信任该值。Gateway 只保证载体唯一、形状有界及一次转发，Auth 继续拥有身份和业务判断。

<a id="br-gwr-016"></a>
### BR-GWR-016：可选保留不产生内部身份

本用例禁止调用 UC-AUTH-010，禁止注入 `x-iwut-identity` 或 `x-iwut-delegation`。有 Session 时只保留原始 `x-iwut-session`；无 Session 时 Auth 不应收到同名空 header/metadata。Authorization、Cookie、Gateway service JWS、外来内部身份和路由控制头都不得到达业务 handler。

客户端同时提交 Session 与任何未声明认证载体时按歧义或禁止凭据失败，不能优先选择其中一个。Gateway 不把 Session 放入日志、trace、metrics 标签、错误正文或响应 header。

<a id="br-gwr-017"></a>
### BR-GWR-017：三协议同一分支与单次转发

HTTP ForwardAuth、原生 gRPC 前置代理和转换后的 gRPC-Web 必须使用同一已验证 Route 与凭据判定。三者对 Session 缺失、规范 Session、畸形/重复 Session、混合凭据和 Auth 下游错误具有等价语义；gRPC 保留合法 status/trailer。

Gateway 不为 Auth 业务请求自动重试，不因 Auth 返回登录错误而切换分支，也不缓存 Session 判定。HTTP 前缀只剥离 `/auth-center`，gRPC 只注册两个 exact full method；任何内部 Auth RPC 或同 package 新方法仍默认拒绝。

## 错误语义

- Session 缺失：合法，转发给 Auth 的注册分支；
- Session 空白、形状非法：HTTP 401 / gRPC UNAUTHENTICATED；
- Session 重复、逗号合并或与禁止凭据混用：HTTP 400 / gRPC INVALID_ARGUMENT；
- 未登记 route：HTTP 404 / gRPC UNIMPLEMENTED 对应边界；
- Auth 返回的业务、认证、限流或不可用错误：保留 Auth 语义，不改写成匿名成功；
- 转发 deadline/cancel：不重试，不把结果未知描述为安全失败。

错误和日志不得披露 Session、authId、邮箱、operation、注册/绑定分支的内部诊断或 Auth 响应中的敏感 header。

## 验收场景

- Begin/Complete 在 Session 完全缺失时不调用 UC-AUTH-010，Auth 只收到一次无 Session 请求，注册流程可按 UC-AUTH-011 工作。
- 唯一规范 Session 在三协议中逐字节到达 Auth，Gateway 不生成 USER JWS；本人绑定/更换由 Auth 最终验证。
- 空白、重复、逗号合并、非法形状 Session 以及 Session 与 Authorization/Cookie/外来身份混用在 Auth 业务 handler 前失败。
- 规范形状但过期、撤销、跨账号或与 operation 不匹配的 Session 由 Auth 拒绝，Gateway 不删除它后重放匿名请求。
- 请求正文 mode/oneof、路径 operationId、query 或客户端 header 不能改变 target、策略或是否执行身份交换。
- 无 Session 分支不产生空 header；有 Session 分支只保留 Session；两条分支均不泄露内部身份或请求凭据。
- 使用真实 Traefik、Gateway、Auth production composition/Mongo，对 HTTP/JSON、原生 gRPC、gRPC-Web 覆盖注册、本人绑定、坏 Session 不降级和业务 upstream 调用次数。

## 依赖与实施边界

依赖 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md)、[Auth 邮箱绑定契约](../../platform/contracts/auth-email-binding-v1.md)、[设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md) 和已实现的 UC-AUTH-011/API。实现需要扩展 Gateway v2 配置校验，使可选 Session 可以在 USER `NEVER` 时按精确 route 条件保留；不得放宽现有可选 USER 身份或必需 DIRECT Session 组合。

本用例接受及本地联合验证前，两条路由保持未登记；Auth 后端或 feature flag 已存在不等于 Gateway 可以公开入口。实现工作包可以同时加入 `GetOwnEmailBinding` 的普通必需 DIRECT route，但必须分别测试它不允许 Session 缺失。

## 变更记录

- 2026-10-07：建立提案；定义 Auth 双模式入口的可选原始 Session、坏凭据不降级、无 USER 交换与三协议单次转发边界。
