# UC-GW-006：携带用户身份与应用关闭高风险证明转发

状态：`ACCEPTED`

## 目标与范围

> Gateway 在关闭 Application 的精确 Route 上同时要求平台 Session 与 `x-iwut-high-risk-proof`：先用 Session 向 Auth 换取面向 App Center 的 USER JWS，只有身份交换成功后，才把唯一 USER JWS 和原始高风险证明一起转发给 App；Session 不下传，proof 的签名、用途、主体与 Application 绑定由 App 最终验证。

本用例服务于 [UC-APP-027](../../app-center/use-cases/UC-APP-027-close-application.md) 的 `CloseApplication`。proof 的签发属于 [UC-AUTH-026](../../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md) 与 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md)；Gateway 不签发、不刷新、不消费 proof，也不解析 claims 决定管理员资格。

`GetApplicationClosurePreview` 与 `GetApplicationClosure` 使用普通 `APP_USER` 策略，不接收 high-risk proof。它们可与本用例同批加入路由，但本用例新增的信任行为只适用于 `CloseApplication`。Application 生命周期、当前管理员、Developer 状态、revision、confirmation 和 proof jti 防重放均由 App Center 负责。

## 路由策略

| RPC | 外部 HTTP | Session / USER | terminal credential |
| --- | --- | --- | --- |
| `GetApplicationClosurePreview` | `GET /app-center/v1/applications/{application_id}/closure-preview` | `REQUIRED` → `iwut-app-center` USER JWS | high-risk proof `FORBIDDEN` |
| `CloseApplication` | `POST /app-center/v1/applications/{application_id}:close` | `REQUIRED` → `iwut-app-center` USER JWS | 唯一 `x-iwut-high-risk-proof` `REQUIRED` 并保留 |
| `GetApplicationClosure` | `GET /app-center/v1/applications/{application_id}/closure` | `REQUIRED` → `iwut-app-center` USER JWS | high-risk proof `FORBIDDEN` |

Authorization、Cookie 和 OAuth 委托凭据均禁止；外来内部身份先清除，不得影响身份交换。三条 Proto route 目标支持 HTTP/JSON、原生 gRPC 和 gRPC-Web；只有 Close route 可以把 proof 送到 App。

## 主流程

1. 使用规范化 method/path 或 exact gRPC full method 匹配 Route，固定 App upstream、audience=`iwut-app-center` 和 terminal credential 规则；删除外来 USER/委托身份与内部控制头。
2. 在调用 Auth 前完整检查载体集合。Close 必须同时出现唯一规范 Session 和唯一有界 high-risk proof；Preview/Get 必须有 Session 且 proof 完全缺失。混合 Authorization/Cookie 或重复值立即失败。
3. Close 对 proof 只执行单值、无控制字符、大小和 compact-JWS 载体形状检查；不验证签名或解析 claims。随后以 Session 和 Gateway service identity 恰好调用一次 UC-AUTH-010。
4. 只有 Auth 成功返回合格的 `iwut-app-center` USER JWS 才继续。Gateway 删除原始 Session 与 service credential，注入唯一 `x-iwut-identity`。
5. Close 额外保留原始 `x-iwut-high-risk-proof`；Preview/Get 不产生或保留该 header。Gateway 将业务请求恰好转发一次给 App。
6. App 分别验签 USER JWS 与 high-risk proof，并校验 subject、applicationId、purpose、时间、管理员资格与 jti 消费。Gateway 保留下游结果，不因 proof 拒绝重新签发、重新交换或重放 Close。

## 业务规则

<a id="br-gwr-022"></a>
### BR-GWR-022：双凭据组合只属于 Close 精确 Route

`Session REQUIRED + USER REQUIRED + required terminal proof` 是静态目录中的有限组合，只能登记到 `ApplicationClosureService/CloseApplication`。客户端不能通过提交 proof 把 Preview/Get 或其它 App Route 升级为高风险命令，也不能用 path/query/body 中的字符串代替 header。

Close 缺少任一载体都不能开始身份交换或业务转发。proof 出现在 Preview/Get、其它 application route 或错误 gRPC method 时按禁止凭据失败；不能静默删除后继续普通 USER 请求，以免调用者误以为高风险证明已被消费。

<a id="br-gwr-023"></a>
### BR-GWR-023：身份交换成功先于 proof 下传

Gateway 在任何 App 请求前先完成 UC-AUTH-010。Session 无效、Auth 不可用/超时、Gateway service identity 失败或签发响应不合格时，App upstream 零调用，proof 不离开 Gateway→Auth/App 信任边界中的 Gateway 进程。

成功后 App 只收到唯一 USER JWS 和 Close route 的唯一 proof；原始 Session、Gateway service JWS、Authorization/Cookie 均删除。Gateway 不缓存身份交换结果，不自动重试 UC-AUTH-010，也不重放 CloseApplication。

<a id="br-gwr-024"></a>
### BR-GWR-024：proof 对 Gateway 不透明且按 Route 最小转发

Gateway 只验证 `x-iwut-high-risk-proof` 是单值、去除 HTTP/gRPC 载体歧义后仍为非空有界 compact JWS；上限固定为 16 KiB。它不选择 Auth key、不验证签名，不解析 issuer/audience/sub/purpose/applicationId/jti/时间，也不比较 USER JWS 的 subject；这些是 App 的权威安全边界。

形状合格不表示 proof 有效。App 对错误签名、跨用户、跨 Application、错误 purpose/audience、过期或重放的拒绝必须原样返回；Gateway 不把它改写为 Session 错误，不调用 reauth Complete，不请求新 proof，也不尝试另一个 Application。

<a id="br-gwr-025"></a>
### BR-GWR-025：高风险载体的三协议与隐私边界

HTTP ForwardAuth、原生 gRPC 与转换后的 gRPC-Web 必须共享同一 Route、先验载体检查、UC-AUTH-010 次数和下游 header/metadata 集合。ForwardAuth 只能把本次终端 proof 送往匹配的 App Router；不得把 proof 放入认证响应正文、错误响应或其它 Router 可见的通用 header 集合。

Gateway 日志、trace、metrics 和错误不得包含 proof、Session、USER JWS、jti 或 claims；只记录 routeId、requestId、阶段、结果类别与耗时。客户端取消、Auth/App deadline 或下游结果未知都不触发自动重放。

## 错误语义

- Session 或 high-risk proof 缺失、形状非法：HTTP 401 / gRPC UNAUTHENTICATED；
- 任一载体重复/合并、proof 出现在错误 Route、与 Authorization/Cookie 混用：HTTP 400 / gRPC INVALID_ARGUMENT；伪造内部身份按既有边界清除；
- Session 被 Auth 拒绝：HTTP 401 / gRPC UNAUTHENTICATED，App 零调用；
- UC-AUTH-010 依赖故障或 deadline：HTTP 503/504 / gRPC UNAVAILABLE/DEADLINE_EXCEEDED；
- App 对 proof、管理员资格、revision 或生命周期的拒绝：保持 UC-APP-027 语义，不改写为 Gateway 认证成功或 Session 错误；
- 未登记 route：HTTP 404 / gRPC UNIMPLEMENTED 对应边界。

## 验收场景

- Close 同时具有唯一有效 Session 与合法载体形状 proof 时，三协议均恰好调用一次 UC-AUTH-010 和一次 App；App 只收到 USER JWS + 原 proof。
- 只有 proof、只有 Session、任一空白/重复/逗号合并、proof 超过 16 KiB、非 compact JWS、与 Authorization/Cookie 混用时，在 Auth/App 调用前按阶段失败。
- Session 无效、撤销或 Auth 不可用/超时使 App 调用次数为零，proof 不出现在 Auth identity RPC、响应或日志中。
- 形状合格但错误签名、跨 subject/application、错误 purpose/audience、过期或已消费 proof 到达真实 App 后由 App 拒绝；Gateway 不解析或重试。
- Preview/Get 使用普通 APP_USER，携带 high-risk proof 时失败而不是静默忽略；其它 App Route 同样不能获得 proof。
- 外来 `x-iwut-identity`、`x-iwut-delegation`、routeId/audience/Forwarded 控制头不能覆盖新 USER JWS、改变 target 或绕过 proof 要求。
- 使用真实 Traefik、Gateway、Auth production composition/Mongo 与 App production composition/Mongo，完成 HTTP/JSON、原生 gRPC、gRPC-Web 的成功、身份失败、proof 失败及下游调用次数联合测试。

## 依赖与实施边界

依赖 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md)、[UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)、[UC-AUTH-026](../../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md)、[UC-APP-027](../../app-center/use-cases/UC-APP-027-close-application.md) 与 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md)。Gateway `293ebc9` 已让 v2 schema 对 terminal credential 表达 `FORBIDDEN/REQUIRED`、精确名称、大小/形状和保留，并把它与必需 USER 身份交换绑定为有限矩阵，没有变成任意 header passthrough。

Close/Preview/Get 三条 App route 与 Begin/Complete reauth 两条 Auth 配套 route 已登记，并通过 usecase、ForwardAuth、gRPC proxy 与生成配置测试。Auth/App 功能开关仍需部署时显式开启；真实 proof 签发、USER 交换、App 消费与三协议业务拒绝的联合验收仍是发布门禁。

## 变更记录

- 2026-10-07：建立提案；固定 Close 的 Session→App USER JWS 与 required high-risk proof 双载体、身份交换先于下游、Gateway 不解析 proof、错误 Route 拒绝及三协议隐私边界。
- 2026-10-07：接受设计；Gateway `293ebc9` 登记 App 三条与 Auth reauth 两条配套路由，交付 16 KiB compact-JWS 载体、身份交换先后关系、最小下传与三适配器测试。
