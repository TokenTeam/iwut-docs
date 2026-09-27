# OAuth 委托上下文与 Traefik 契约 v1

状态：`PROPOSED` — 2026-09-27；扩展现有 Gateway OAUTH2 预留分支，默认关闭。

## 链路与身份隔离

```text
应用 ─ Bearer access token → Traefik
  HTTP：ForwardAuth → Gateway → Auth 在线校验 + 签发委托 JWS
        Traefik 复制委托 JWS → 固定 Router → 资源服务验签与业务授权
  gRPC：Traefik → Gateway 精确 unary 代理 → Auth → 资源服务
  gRPC-Web：Traefik 协议转换 → 同一 unary 代理
```

Traefik 阶段完成入口检查，但 token 真伪、grant、scope 的权威判断仍由 Auth 完成。随机 access token 不可本地验签；Traefik 不持有 Auth 私钥，也不查询 Mongo。不开 Redis，不缓存 token 校验结果或签发结果。

委托上下文使用 `x-iwut-delegation`，与 SESSION 的 [x-iwut-identity](trusted-identity-v1.md) 分离。ID Token、平台 Session、service JWS 不可作为 OAuth Bearer token。第三方应用不能通过 OAuth scope 获得原有 developer/reviewer/管理员 USER 身份；管理端原有 SESSION 路由继续只接受平台 Session。

规则归属：[UC-AUTH-019](../../auth-center/use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-GW-002](../../gateway/use-cases/UC-GW-002-authenticate-oauth-and-forward.md)。本契约与 [ADR-GW-001](../../gateway/adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) 配合，保留其固定 Traefik 版本和三协议适配方式。

## Auth 签发 RPC

唯一新内部方法为 `/auth_center.v1.oauth_delegation.OAuthDelegationService/IssueDelegationContext`。仅 native gRPC/TLS，调用者必须是授权 Gateway service principal，permission=`auth.oauth.delegation.issue`，audience 为 Auth，metadata：

- `authorization: Bearer <Gateway service JWS>`；按既有 service identity 验证。
- `x-iwut-access-token: <opaque token>`，恰好一个值，不带 Bearer。

请求字段：routeId、policyDigest、protocol、method、targetPath；签名协议值固定 HTTP 或 GRPC，gRPC-Web 转换后也是 GRPC。HTTP method 为大写方法名；gRPC method 为完整 RPC 名且不发送 targetPath。响应字段：delegationJws、expiresAt。不接收 userId、clientId、scope、角色、上游 URL 或任意 audience 覆盖。

部署路由目录是静态可信输入，同一工具生成 Gateway 路由与 Auth 的 OAuth route policy 清单。每项固定 routeId、目标 audience/upstream、协议与方法、HTTP 精确路径或受限路径模板及重写规则、requiredScopes（全部满足）、allowedChannels、策略版本；对规范化完整清单取 SHA-256 得 policyDigest。Auth/Gateway digest 不匹配拒绝服务，不从请求补全策略。OAuth 路由必须有明确非空 scope 要求；只拥有 openid 不自动获得业务 API 权限。

Gateway 以已匹配的静态路由构造请求，Auth 根据本地清单复核 method/path/audience。现有服务签发允许列表新增此精确 RPC 与允许 routeId/audience，不能用 `auth_center.*` 通配。UserInfo 是 Auth 自行认证的标准 DIRECT 端点，不再调用自身委托 RPC。

## 委托 JWS

单个 compact JWS、不带 Bearer，大小至多 8 KiB。RS256、独立用途的签名 key/kid；header `typ=iwut-delegation+jwt`，不与公开 OIDC JWKS 或 USER/service 验证器共享可接受密钥集。

| claim | 语义 |
| --- | --- |
| iss、aud | 配置的 Auth issuer、单个目标资源 audience |
| sub | 内部 authId，只在平台内网下游使用，不向应用返回 |
| client_id、application_id | 已认证 token 所属 client 和应用 |
| grant_id、grant_revision、grant_revocation_epoch | 当前用户授权、审计 revision 与撤销 epoch |
| channel、rpc_api_major、client_authorization_epoch | token 固定运行上下文及 client 状态 epoch |
| scopes | UC-AUTH-019 计算的有效交集 E；不包含当前版本未允许的历史同意或 token 外的新增 scope |
| route_id、policy_digest、protocol、method | 绑定本次路由/策略/协议/操作 |
| target_path | HTTP 重写后的 escaped path；gRPC 不出现 |
| iat、nbf、exp、jti | 签发时间、当前有效、最长 5 秒、独立随机 ID |

exp 不晚于 access token 到期时间。无 permissions、developer_status、email、学校关联值、平台 Session 或 token 原文。Auth 检查 token 对本 audience 的许可；token 的 audience 集合由已授予 scope 的受信映射产生，客户端不能自报。

资源服务必须验证签名、固定算法/typ/kid/issuer/audience、时限和本次 method/route/policy/target_path，再以 sub 做数据归属检查，以 client_id/application_id/channel 做应用环境约束。route policy 显式配置非空 allowedChannels；首版只能启用 TEST。仅限正式渠道的路由拒绝 TEST token；允许多个渠道的共享资源仍分别检查各自 grant/E，不能因为 OIDC sub 相同绕过渠道许可。可验证委托 JWS 不等于全部业务许可。不得把委托转换成通用 USER 管理身份。只在配置明确启用的 OAuth 方法接受该 header，未知入口拒绝。

HTTP path 必须经过路由生成器规定的单次解析和固定重写；拒绝非法 percent encoding、编码斜线/反斜线、dot segment 和无法唯一匹配的路径。Gateway 签发请求与后端收到的 escaped path 必须字节相等；查询参数不作为路径签名的一部分，业务仍验证其中的资源 ID/过滤条件，不能把 query 当授权范围来源。

## Traefik HTTP 契约

OAUTH2 路由中间件顺序固定：

1. 拒绝重复/别名/下划线混淆的身份或凭据 header；删除外部 x-iwut-identity、x-iwut-delegation、x-iwut-session、x-iwut-access-token、service/policy 身份头及旧用户头。保留待检查的单个 Authorization。清理外部伪造 Forwarded/X-Forwarded-*，由可信入口重新构造。
2. ForwardAuth 指向内网 Gateway，URL 路径中的 routeId 来自生成配置；Gateway 与受信转发 method/URI 对照匹配，不能从用户 header 选择路由。认证 listener 不暴露公网，只接受 Traefik 受信网络/连接。
3. 配置 `trustForwardHeader=false`、`forwardBody=false`、显式 authRequestHeaders 最小白名单（Authorization 及受控追踪 ID）；由 Traefik 生成的转发元数据在受信边界内校验。`authResponseHeaders=[x-iwut-delegation]`，禁止宽泛正则复制身份头；限制认证响应 body 为 4096 字节、上下文 header 为 8 KiB。
4. 仅认证 200 且有恰好一个合法形状的委托 JWS 才继续。Traefik 复制该 header，随后移除 Authorization、全部内部请求凭据、官方门户 Cookie 与路由策略辅助 header，再按同一固定路由转发。认证响应不向最终客户端泄露内部 JWS。
5. 业务 upstream 不对公网可达；资源服务仍按前节独立验签。不得把认证成功当作省略验签的理由。

以上行为需用固定版本的真实 Traefik 验收；若 ForwardAuth 200 缺 header 无法由原生配置拒绝，Gateway 的认证处理器必须将缺失签名转换为 503，资源服务也必须拒绝缺失身份。关闭 authSigninURL 等自动 API 登录跳转。签发/转发每步有界 deadline（初始建议总鉴权 2 秒）；认证失败不得转发业务请求，不自动重试业务 mutation。

`OIDC_HTTP` DIRECT 另设明确凭据白名单：/token 与 /revoke 可保留 Basic；/userinfo 可保留 Bearer；/authorize 与 /portal/* 只向 Auth 传门户 cookie/指定 Session；其他 client 身份头仍先清理。只有明确登记的 POST /portal/session 可保留 x-iwut-session。不允许为了 token endpoint 全局打开 Authorization 转发。Auth sector URI 的专用 host 路由也仅 GET /redirect-uris.json，Traefik 按部署受信后缀及固定 UUID 主机名格式匹配到 Auth upstream，Auth 再核对完整 host 与已分配 sector 的归属。新增 sector 无需重新生成每应用 Router；未知 UUID 由 Auth 返回 404。不得把请求 Host 当作新 sector 的创建依据或自由上游地址，未知 host 拒绝。发现/JWKS 只 GET；授权页面及标准端点不经 gRPC-Web 转换。

## 错误与协议适配

| 情况 | HTTP | native gRPC / gRPC-Web |
| --- | --- | --- |
| token 缺失、非法、过期、授权已撤回 | 401，Bearer invalid_token | UNAUTHENTICATED |
| token 有效但本路由 scope 不足 | 403，Bearer insufficient_scope | PERMISSION_DENIED |
| 限流 | 429、Retry-After | RESOURCE_EXHAUSTED |
| Auth/App 不可用、内部凭据/策略配置失效 | 503 | UNAVAILABLE |

native gRPC 与转换后的 gRPC-Web 必须经现有 Gateway unary 前置代理构造合法 gRPC status/trailer，不直接套 HTTP ForwardAuth 错误。非法路由/方法沿用现有未知入口拒绝规则，不猜测 token 类型或降级 SESSION/DIRECT。scope 错误只公开该路由可公开的要求，不泄露用户其它授权。

## 撤销与时钟边界

Auth 本地 grant/token 撤销与最终签发共用原子栅栏：撤销提交后开始的新检查不得再成功。已签发的委托 JWS 最长 5 秒，资源服务只允许 1 秒时钟容差；部署必须监测时钟偏移，超界停止签发。

App 使用最长 5 秒的单次快照，Auth 只在快照未过期时完成本次决策；它不是跨库锁或永久租约。故 App 配置/资格变化到最后一个旧委托可被接受的上界为约 11 秒（快照 5 秒 + JWS 5 秒 + 时钟差 1 秒）。Auth 本地撤回的上界为约 6 秒。已开始的业务操作不回滚，长任务/流式 RPC 不在首版范围，不能声称全链路即时撤回。

token 校验不依赖原登录 Session 继续存在；用户退出平台 Session 不隐式撤回第三方 grant。账号不可用、grant/refresh family 撤销、client/config/资格变化按相关 UC 拒绝；第三方自己的登录会话、已下载数据不由此自动删除。

## 验收与启用门禁

新增路由必须同时具备 Auth scope/audience 定义、App 批准 scope、资源服务专用委托验证器与业务权限测试。未具备时编译/启动校验拒绝启用该路由。测试伪造头、错误 token 用途、错误 aud/typ、route 混淆、跨应用 token、授权撤回、App 快照到期、secret 轮换、三协议失败零转发和直接绕过 Edge；ID Token 无论签名是否正确都不能调用业务 API。

配置行为依据 [Traefik ForwardAuth v3.7](https://doc.traefik.io/traefik/v3.7/reference/routing-configuration/http/middlewares/forwardauth/)。先完成 UC-GW-002 和联合验收，再改变现有 OAUTH2 默认关闭状态；本文不要求现有 SESSION 路由改用新的 header 或期限。
