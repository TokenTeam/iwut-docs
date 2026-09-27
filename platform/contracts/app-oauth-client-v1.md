# App OAuth Client 提供方契约 v1

状态：`PROPOSED` — 2026-09-27。

## 所有权与调用方

App Center 持有 Application 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，协议见 [OAuth OIDC v1](oauth-oidc-v1.md)。

管理接口接受 SESSION 转换后的 [trusted identity](trusted-identity-v1.md) USER 身份。内部接口只接受 Auth 的 [service identity](trusted-service-identity-v1.md)，audience 为部署固定的 App Center audience，逐方法授权；不经过公网、HTTP 或 gRPC-Web，也不把 client secret 当服务间凭据。

## 三种生命周期

`ApplicationOAuthRegistration` 以 applicationId 唯一，字段为 applicationId、publicClientId、publicStatus、confidentialClientId、confidentialStatus、registrationRevision、createdAt、updatedAt。两个 clientId 均为服务端 UUIDv4、全局唯一、永久不重用；type 由其所在 slot 确定，状态为 `ACTIVE/DISABLED`。client identity 不包含 channel、rpcApiMajor、Version 或 hostname。

`OAuthClientCredential` 以 confidentialClientId 唯一，字段为 confidentialClientId、applicationId、secretDigest、credentialRevision、rotatedAt。它只服务于以后 confidential client authentication；secret 轮换不改变 registrationRevision。

`ApplicationVersionOAuthConfig` 以 applicationVersionId 唯一，字段为 applicationVersionId、applicationId 和：

```text
oauthRedirects {
  pkceRedirectUris: []RedirectURI
  confidentialRedirectUris: []RedirectURI
}
```

它使用独立 collection 存储，但生命周期严格依附 ApplicationVersion：与 Version 同事务创建/编辑，使用同一个 Version revision 做 OCC，提交时深拷贝进 Review snapshot，提交后不可独立修改。两个数组均非 null、各 0–10 项、内部唯一且彼此不交叉。详细 URI 规则见 [BR-VER-018](../../app-center/use-cases/UC-APP-002-create-application-version.md#br-ver-018)。

## 管理接口

建议服务 `app_center.v1.oauth_client.OAuthClientService`。可执行 Proto、字段号与 HTTP annotation 在独立 API 仓库落地。

| 方法 | 输入 | 输出 |
| --- | --- | --- |
| RegisterOAuthClient | applicationId、type、optional expectedRegistrationRevision | registration；仅 confidential 额外返回一次 clientSecret |
| GetApplicationOAuthRegistration | applicationId | 当前管理员可见的 registration 元数据 |
| SetOAuthClientStatus | clientId、expectedRegistrationRevision、status | 新 registration；相同状态为 no-op |
| GetOAuthClientCredentialMetadata | clientId | credentialRevision、rotatedAt；不含 secret/摘要 |
| RotateOAuthClientSecret | clientId、expectedCredentialRevision | 新 credential 元数据及一次性 clientSecret |

每个 Application 每种 type 至多登记一次。registration 尚不存在时 expectedRegistrationRevision 必须为空，结果 revision=1；已存在且补登记另一 type 时必须提交当前 revision。登记不依赖 Version、Review 或 Publication；丢失登记响应时先查询，secret 丢失则轮换。禁用和重新启用使用 SetOAuthClientStatus，不删除 identity。

secret 为 32 随机字节的 base64url 无 padding 字符串。App 仅存 `SHA-256("iwut-oauth-client-secret-v1\0" || clientId || "\0" || secret)`，使用恒定时间比较；只保留当前摘要。创建/轮换成功响应使用 no-store；提交结果未知时不能返回可能未提交的 secret。

## Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | identity 元数据、tokenEndpointAuthMethod；CONFIDENTIAL 含 credentialRevision |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedCredentialRevision | verified、credentialRevision；不返回摘要 |
| `/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` | clientId、channel、rpcApiMajor、expectedRegistrationRevision | 当前批准的运行配置 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、channel、rpcApiMajor、expectedRegistrationRevision、expectedRuntimeVersion | 当前用户授权上下文 |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。permission 只授予指定 Auth 服务主体；SYSTEM、USER 和第三方 access token 均不能调用。Verify 对未知 client、错误 secret、PUBLIC、DISABLED 或 credential revision 不一致返回 `verified=false`。原 secret 只经 TLS 内网发送，拦截器和代理禁止记录 metadata/body。

`RuntimeConfiguration` 包含 clientId、applicationId、type、channel、rpcApiMajor、registrationRevision、adminAuthId、versionId、publicationRevision、redirectUris、requiredScopes、optionalScopes、display、observedAt、validUntil。

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和 testerMembershipId。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, adminAuthId)`；expectedRegistrationRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置和 Tester 资格。

redirectUris 来自批准 snapshot：PUBLIC 读取 pkceRedirectUris，CONFIDENTIAL 读取 confidentialRedirectUris；对应数组必须非空。requiredScopes/optionalScopes 来自同一 snapshot。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记；channel/rpcApiMajor 只是选择权威 Publication 的显式运行输入。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。登录前后 registrationRevision 和 runtime tuple 必须一致，否则重新开始或失败关闭。credentialRevision 只约束一次 secret 验证，不进入 runtime tuple。

Grant 以 `(authId, clientId)` 为稳定身份。授权交互和 code 绑定精确 `(versionId, publicationRevision, testerMembershipId, adminAuthId)`、redirect URI 和 scope；access token 记录签发时运行上下文用于审计。Version 变化或 secret 轮换本身不撤销 grant/已签发 token，Auth 应按当前运行资格和允许 scope 的交集决定是否继续使用；新增 scope 必须重新 consent。

## 资格变化与失败

client 不可用、对应回调数组为空、非 ACTIVE Tester、无 exact-major Publication 或批准记录不一致均不可授权。首版只支持 channel=`TEST`。不存在或无资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。未来 STABLE/灰度发布必须先定义公开运行资格，再扩展 channel。

## 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认和 code 兑换重新解析用户上下文。refresh、UserInfo 和每次委托签发按 OAuth/OIDC v1 的当前资格规则验证。confidential secret 只在 token/revoke 操作验证。

双方至少测试：每种 type 的 clientId 稳定；metadata 无 redirect/secret；一次 secret 返回；registration 与 credential revision 并发隔离；跨应用管理员；runtime tuple 混合；同 clientId 跨 Version/major 选择；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；hostname 迁移；快照过期；服务 permission；Auth→App 故障时零签发。
