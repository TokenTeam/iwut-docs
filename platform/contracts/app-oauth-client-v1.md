# App OAuth Client 提供方契约 v1

状态：`PROPOSED` — 2026-09-27。

## 所有权与调用方

App Center 持有 OAuth client 身份、状态、secret 摘要，以及 ApplicationVersion 中受审核的 redirect URI 和 scopes。Auth 不保存另一份可独立修改的注册表。管理规则见 [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，协议见 [OAuth OIDC v1](oauth-oidc-v1.md)。

管理接口接受 SESSION 转换后的 [trusted identity](trusted-identity-v1.md) USER 身份。内部接口只接受 Auth 的 [service identity](trusted-service-identity-v1.md)，audience 为部署固定的 App Center audience，逐方法授权；不经过公网、HTTP 或 gRPC-Web，也不把 client secret 当服务间凭据。

## Client 元数据与版本运行配置

`OAuthClient` 字段：clientId、applicationId、type、channel、rpcApiMajor、sector、status、configRevision、hasSecret、secretRotatedAt、createdAt、updatedAt。

clientId 为服务端 UUIDv4，与 applicationId、nameKey、developerHandle 分离。type 为 `PUBLIC_PKCE/CONFIDENTIAL_SECRET`；channel 首版仅 `TEST`；rpcApiMajor 为正整数；status 为 `ACTIVE/DISABLED`。applicationId、type、channel、rpcApiMajor 和 sector 创建后不可修改。元数据不包含 redirect URI、secret 或摘要。

`ApplicationVersion.oauthRedirects` 是数组，每项为 `{clientType, redirectUris}`；同一 type 至多一项。Version 的审核 snapshot 冻结该数组。Provider 只从 exact-major 当前 TEST Publication 指向的 APPROVED Version 及其批准 snapshot 解析有效回调，不读取 OAuthClient 旧值或前端上报值。

## 管理接口

建议服务 `app_center.v1.oauth_client.OAuthClientService`。可执行 Proto、字段号与 HTTP annotation 在独立 API 仓库落地。

| 方法 | 输入 | 输出 |
| --- | --- | --- |
| CreateOAuthClient | applicationId、type、channel、rpcApiMajor | client；仅 confidential 额外返回一次 clientSecret |
| GetOAuthClient | clientId | 当前管理员可见的 client 元数据 |
| ListOAuthClients | applicationId、分页游标、pageSize≤50 | 元数据列表，不含 secret |
| SetOAuthClientStatus | clientId、expectedRevision、status | 新元数据；相同状态为 no-op |
| RotateOAuthClientSecret | clientId、expectedRevision | 新元数据及一次性 clientSecret |

同一 `(applicationId, channel, rpcApiMajor, type)` 只允许一个 client。创建时必须存在 exact-major 当前 TEST Publication，且批准 snapshot 为该 type 提供非空回调组；sector 从其唯一规范 hostname 派生。丢失创建响应后先查询，secret 丢失则轮换。禁用和重新启用使用 SetOAuthClientStatus。

secret 为 32 随机字节的 base64url 无 padding 字符串。App 仅存 `SHA-256("iwut-oauth-client-secret-v1\0" || clientId || "\0" || secret)`，使用恒定时间比较；只保留当前摘要。创建/轮换成功响应使用 no-store；提交结果未知时不能返回可能未提交的 secret。

## Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | client 元数据及 tokenEndpointAuthMethod |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedConfigRevision | verified、configRevision；不返回摘要 |
| `/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` | clientId、expectedConfigRevision | 当前批准的运行配置 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、expectedConfigRevision、expectedRuntimeVersion | 当前用户授权上下文 |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。permission 只授予指定 Auth 服务主体；SYSTEM、USER 和第三方 access token 均不能调用。Verify 对未知 client、错误 secret、禁用或 revision 不一致返回 `verified=false`。原 secret 只经 TLS 内网发送，拦截器和代理禁止记录 metadata/body。

`RuntimeConfiguration` 包含 clientId、applicationId、type、channel、rpcApiMajor、sector、configRevision、adminAuthId、versionId、publicationRevision、redirectUris、requiredScopes、optionalScopes、display、observedAt、validUntil。

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和 testerMembershipId。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, adminAuthId)`；expectedConfigRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置和 Tester 资格。

redirectUris 来自批准 snapshot 中与 client.type 匹配的回调组，必须非空且全部具有与 client.sector 相同的规范 hostname。requiredScopes/optionalScopes 来自同一 snapshot。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。Verify、RuntimeConfiguration 和 AuthorizationContext 的 configRevision 必须一致；登录前后 runtime tuple 必须一致，否则重新开始或失败关闭。

Grant、code 和 token 绑定的应用资格版本为 `(configRevision, versionId, publicationRevision, testerMembershipId, adminAuthId)`，授权请求还绑定精确 redirect URI。display 不参与权限指纹。

## 资格变化与失败

client 不可用、回调组缺失/sector 不一致、非 ACTIVE Tester、无 exact-major TEST Publication 或批准记录不一致均不可授权。不存在或无资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。未来 STABLE/灰度发布必须先定义公开运行资格，再扩展 channel。

## 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认、code 兑换、refresh、UserInfo 和每次委托签发再解析用户上下文。confidential secret 只在 token/revoke 操作验证。

双方至少测试：metadata 无 redirect/secret；一次 secret 返回；轮换/禁用并发；跨应用管理员；revision/tuple 混合；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；sector 不一致；快照过期；服务 permission；Auth→App 故障时零签发。
