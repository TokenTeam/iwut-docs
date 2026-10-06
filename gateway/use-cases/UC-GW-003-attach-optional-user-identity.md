# UC-GW-003：为公开读取附加可选用户身份

状态：`ACCEPTED`

## 目标与范围

> Gateway 对明确登记的公开读取允许调用者完全不提供 Session；若调用者提供 Session，则必须先由 Auth 完整验证并换取目标 audience 的可信 USER JWS，再把请求转发给下游。任何已提供但无效的凭据都不能降级为匿名。

本用例只定义 Gateway 的可选身份编排。匿名/已登录用户得到什么业务结果仍由下游用例决定。首批消费者是：

- [UC-APP-023](../../app-center/use-cases/UC-APP-023-resolve-unified-launch-target.md) 的统一启动目标解析；
- [UC-APP-024](../../app-center/use-cases/UC-APP-024-query-public-application-catalog.md) 的普通 Catalog 列表与详情。

本用例不负责业务缓存、Tester/Grey/Stable 选择、Catalog 候选资格、Session 签发/撤销、OAuth Bearer 委托、OIDC 门户登录，或为所有 DIRECT 路由自动启用可选身份。

## 输入与输出

输入为严格路由目录匹配到的 HTTP/JSON、原生 gRPC 或 gRPC-Web 请求，以及零个或一个 `x-iwut-session`。Route 固定目标服务、audience、协议和 `WHEN_SESSION_PRESENT` 身份交换策略；客户端不能在 path/query/body/header 中选择策略、audience 或 upstream。

输出为以下之一：

- Session 完全缺失：删除全部身份/内部控制头，以匿名请求转发；
- 唯一 Session 验证成功：注入本次取得的唯一 `x-iwut-identity` 后转发；
- Session 或其它凭据非法、歧义，或 Auth 交换失败：返回稳定认证/依赖错误，业务 upstream 零调用；
- 下游业务响应：保持其协议状态、正文和 trailer，并不得向终端泄露内部 USER JWS。

## 主流程

1. 使用与转发相同的规范化 method/path 或 exact gRPC full method 唯一匹配 Route，并先清除外来 USER/委托身份及内部控制头。
2. 检查该 Route 的凭据矩阵。`x-iwut-session` 完全缺失时选择匿名分支；出现任何值时选择已认证分支，不能再回退。
3. 匿名分支不调用 Auth，不构造空身份 header；清除终端 Session、Authorization、Cookie 和未声明专用 header 后转发。
4. 已认证分支用 Route 固定 audience、唯一 Session 和 Gateway 服务身份恰好调用一次 [UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)。
5. 只有取得合格 USER JWS 才写入唯一 `x-iwut-identity`；随后删除原始 Session、Authorization、Gateway service JWS 和全部内部辅助 header，再转发一次业务请求。
6. 返回下游结果。认证、超时、取消或协议故障都不自动重试身份交换，也不重放业务请求。

## 业务规则

<a id="br-gwr-010"></a>
### BR-GWR-010：匿名与已认证分支只由载体是否缺失决定

可选身份只允许在静态目录明确登记的 Route 上启用。`x-iwut-session` 完全缺失才是匿名；Gateway 不从 Cookie、Authorization、query、body 或自报 authId 补取 Session，也不根据业务参数选择身份分支。Route 一旦匹配，target、audience、method/path 与策略在整个请求内保持不变。

匿名分支不调用 UC-AUTH-010，也不注入空值、anonymous token 或伪造的 USER JWS。下游通过身份 header 是否存在区分匿名和可信用户，具体业务结果引用自己的 UC。

<a id="br-gwr-011"></a>
### BR-GWR-011：已提供凭据必须失败关闭

一旦请求出现 `x-iwut-session`，空白、多值、逗号合并、别名、非法形状、过期、撤销、主体不可用或 Auth 拒绝都必须结束请求；不能删除坏值后走匿名分支。请求同时携带 Authorization、Portal Cookie、外来 `x-iwut-identity`/`x-iwut-delegation` 或该 Route 未声明的认证载体时，按伪造/歧义策略清理并拒绝，不能以优先级猜测调用者意图。

客户端伪造的内部身份 header 永不因“无 Session”而获得匿名透传。其清理、重复 header 防护和 Forwarded 信任边界继续遵守 BR-GWR-003 与 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md)。

<a id="br-gwr-012"></a>
### BR-GWR-012：成功交换才允许携带可信身份转发

已认证分支逐请求调用 UC-AUTH-010，不缓存 Session 验证结果或 USER JWS。Auth 不可用、超时、服务身份失败、返回空/多值/过大/非法形状或无剩余寿命的 JWS 时，业务 upstream 零调用。Gateway 不解析 claims 决定 Tester、Grey、Developer 或业务权限，也不自行签名或改变 audience。

成功后原始 Session 与 Gateway service credential 不到达 App Center；App Center 只收到目标 audience 的唯一 USER JWS 并自行验签。内部 JWS 不写入终端响应、日志、trace 或 metrics 标签。

<a id="br-gwr-013"></a>
### BR-GWR-013：三协议一致与私有响应边界

HTTP/JSON 使用受信 Traefik ForwardAuth 链路，原生 gRPC 与转换后的 gRPC-Web 使用精确 unary 前置代理；三者对匿名、有效 Session、无效 Session、歧义凭据、Auth 不可用和 deadline 必须有等价语义。认证失败不得到达业务 upstream，gRPC 路径必须保留合法 status/trailer。

Gateway 必须保留下游 `Cache-Control: private, no-store` 等安全响应头，不能把可能依赖 Tester/Grey 身份的结果改成共享可缓存响应。首版不在 Gateway 缓存匿名或已认证结果；未来若增加缓存，必须把身份存在性及业务查询边界纳入隔离设计并另行接受，不能仅依赖 URL 作为 cache key。

## 错误语义

- 未登记/不匹配的 route：HTTP 404 / gRPC UNIMPLEMENTED 对应边界；
- Session 缺失：不是错误，按匿名转发；
- Session 非法、失效或 Auth 判定不可认证：HTTP 401 / gRPC UNAUTHENTICATED；
- 重复、别名或与禁止载体混用：HTTP 400 / gRPC INVALID_ARGUMENT；
- Gateway service identity、Auth 依赖或签发响应协议故障：HTTP 503 / gRPC UNAVAILABLE；
- 身份交换 deadline：HTTP 504 / gRPC DEADLINE_EXCEEDED；
- 已成功转发后的业务错误：保留下游语义，不改写成认证错误。

错误响应不得披露 Session 是否曾存在、authId、Tester/Grey 状态、JWS、服务凭据或 Auth 内部诊断。日志仅记录 routeId、requestId、匿名/已认证分支、结果类别和耗时，不记录原始凭据或完整身份。

## 验收场景

- 三个首批 App 查询在完全无 Session 时均只调用一次业务 upstream、零调用 Auth，且下游看不到身份 header；匿名结果按 App UC 只走 Stable 语义。
- 唯一有效 Session 在三协议中都恰好调用一次真实 Auth UC010，App verifier 收到正确 `iwut-app-center` audience 的唯一 JWS，原始 Session 不到达 App。
- 空白、重复、逗号合并、过期、撤销、错误签名 Session，以及 Session 与 Bearer/Cookie 混用均失败且业务 upstream 计数为零；不存在匿名降级。
- 伪造 `x-iwut-identity`、`x-iwut-delegation`、内部 routeId/audience 和 Forwarded 头不能改变分支、目标或身份。
- Auth 401/403/503、timeout、取消、空成功响应、错误 JWS 形状都失败关闭，不缓存上次成功身份。
- HTTP、原生 gRPC、gRPC-Web 的状态映射和下游调用次数一致；响应保持 `private, no-store`，终端与日志不出现内部 JWS。
- 使用真实 Traefik、Gateway、Auth production composition/Mongo 和真实 App Center transport/verifier，覆盖匿名、有效身份与无效凭据三条端到端路径；不能只用 verifier fake 代替 App 进程。

## 依赖与实施边界

依赖 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md) 的路由凭据矩阵、[ADR-PLAT-004](../../platform/adr/ADR-PLAT-004-unified-api-integration-baseline.md) 的共同 API revision、已完成的 UC-AUTH-010，以及 UC-APP-023/024 的稳定 API/transport。Application suspension/restore 建模后，App 业务查询应自行把该状态加入候选资格；Gateway 不根据 Application 状态做授权。

Gateway `0009947` 已把 `ResolveLaunchTarget`、`ListPublicApplications` 与 `GetPublicApplication` 登记为 Session `OPTIONAL`、USER `WHEN_SESSION_PRESENT`、audience `iwut-app-center`，并通过统一 API `9f914c5` 的 descriptor 严格校验。匿名、有效 Session、无效 Session、不允许的 Authorization、内部身份清理和三协议适配由单元测试覆盖；真实 Traefik + Auth + App + Mongo E2E 覆盖三个公开查询的匿名路径，以及 Catalog 列表的有效 Session 与无效 Session 路径。

联合验收同时发现并修复 App 空 Catalog 返回 500 的边界缺陷（App `b93fb25`），其 Mongo 集成回归测试和 App quick verification 通过。当前实现已在本地完成验证，但尚未 push 或生产部署；远端发布统一 API 与服务提交仍是 CI/发布前置事项。

## 变更记录

- 2026-10-06：建立提案；定义公开读取的匿名/可选 Session 分支、无效凭据不降级、三协议一致及首批 App UC023/024 接入边界。
- 2026-10-07：接受并完成本地实现；Gateway `0009947` 固定统一 API `9f914c5`，真实 Auth/App 三协议 E2E 通过。
