# App OAuth Client 提供方契约 v1

状态：`PROPOSED` — 2026-09-27。

## 所有权与调用方

App Center 持有 OAuth client 配置和 secret 摘要；Auth 不保存另一份可独立修改的注册表。管理规则见 [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md)。授权/凭据协议见 [OAuth OIDC v1](oauth-oidc-v1.md)。

管理接口接受现有 SESSION→[trusted-identity-v1](trusted-identity-v1.md) 的 USER 身份，由 App 检查当前 Application 管理员与 Developer 条件。内部接口只接受 Auth 的 [service identity](trusted-service-identity-v1.md)，audience 为部署固定的 App Center audience，逐方法授权；不经过公网、HTTP 或 gRPC-Web。不把 client secret 当服务间调用凭据。

## Client 元数据

`OAuthClient` 字段：clientId、applicationId、type、channel、rpcApiMajor、redirectUris、sector、status、configRevision、hasSecret、secretRotatedAt、createdAt、updatedAt。

clientId 为服务端 UUIDv4，与应用 UUID、nameKey、developerHandle 分离。协议拼写为 client_id。type 为 PUBLIC_PKCE/CONFIDENTIAL_SECRET；channel 首版仅 TEST；rpcApiMajor 为正整数。status 为 ACTIVE/DISABLED，revision 为递增正整数。元数据不返回 secret 或其摘要。subject sector 与 redirect 限制见 [OIDC 身份格式](oauth-oidc-v1.md#凭据与身份格式)。

## 管理接口

以下是必须实现的消息语义和方法名；可执行 Proto、字段号与 HTTP annotation 在独立 API 仓库一次性落地。建议服务 `app_center.v1.oauth_client.OAuthClientService`，仅下列明确登记方法对外开放，不按包前缀放行。

| 方法 | 输入 | 输出 |
| --- | --- | --- |
| CreateOAuthClient | applicationId、type、channel、rpcApiMajor、redirectUris | client；仅 confidential 额外返回一次 clientSecret |
| GetOAuthClient | clientId | 当前管理员可见的 client 元数据 |
| ListOAuthClients | applicationId、分页游标、pageSize≤50 | 元数据列表，不含 secret |
| UpdateOAuthClient | clientId、expectedRevision、完整 redirectUris、status | 新元数据；不支持改变不可变字段 |
| RotateOAuthClientSecret | clientId、expectedRevision | 新元数据及一次性 clientSecret |

同一 `(applicationId, channel, rpcApiMajor, type)` 只允许一个 client；丢失创建响应后先查询元数据，需要 secret 时轮换，不能请求再次读取旧值。禁用通过 Update 实现；重新启用也递增 revision。secret 轮换立即替换，无双 secret 宽限窗口，运维可安排冷切换。

secret 为 32 随机字节的 base64url 无 padding 字符串。App 仅存 `SHA-256("iwut-oauth-client-secret-v1\0" || clientId || "\0" || secret)`，比较恒定时间；高熵随机 secret 不使用人类密码。只保留当前摘要；审计不记录原值/摘要。创建/轮换成功响应 no-store；提交结果未知时不返回可能未提交的 secret。

## Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`，精确方法和 permission：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | 上述配置及 tokenEndpointAuthMethod；含当前 revision |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedConfigRevision | verified、configRevision；不返回摘要 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、expectedConfigRevision | 下述应用授权快照 |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。service permission 只给指定 Auth 服务主体；SYSTEM/USER/第三方 access token 均不能调用。Verify 对未知 client、错误 secret、禁用、revision 不一致均返回 verified=false；未通过服务认证在进入领域查询前拒绝。只经 TLS 内网发送原 secret，拦截器和代理禁止记录 metadata/body。

`AuthorizationContext` 包含 clientId、applicationId、configRevision、adminAuthId、channel、rpcApiMajor、versionId、publicationRevision、testerMembershipId、requiredScopes、optionalScopes、display（当前已公开资料或明确标记的技术名称 fallback）、observedAt、validUntil。

本版 scope 集合来自精确 TEST 槽位的当前 APPROVED Version 及其批准 snapshot，不允许前端指定 versionId、scope、adminAuthId 或“审核通过”标记。用户身份参数由 Auth 从 Session/token 解析后填写。App 不接收学校账号、学生关联值或邮箱。该查询只确认访问资格，不等同 UC-APP-012 的完整宿主启动能力匹配，不绕过宿主的 capability 检查。

所有返回字段取自同一个 Mongo snapshot；observedAt 取建立该 snapshot 时刻，不能在慢查询结束后重新计时；validUntil 不晚于 observedAt+5 秒。Auth 每次操作重新读取，不缓存复用；超时或过期重读，不通过延长 validUntil 继续签发。Verify 返回 revision 必须与 Resolve 和本次已取得配置一致，否则重新读取一次或失败关闭，不能混合新配置与旧 secret 验证结论。

Grant/code/token 需要绑定的应用资格版本为 `(configRevision, versionId, publicationRevision, testerMembershipId, adminAuthId)`。任何成员变化都需要重新发起授权，旧凭据不因恢复原配置或 Tester 重新加入而复活。App 返回 display 不参与权限指纹，不能因应用改展示文案使全体 token 失效。

## 资格变化与失败

client 不可用、非 ACTIVE Tester、无 TEST 发布或批准记录不一致均不可授权；不存在/无资格面向 Auth 返回统一 FAILED_PRECONDITION，具体原因只在受控内部诊断字段中体现。非法输入 INVALID_ARGUMENT；未授权服务 UNAUTHENTICATED/PERMISSION_DENIED；存储/超时 UNAVAILABLE。Auth 不用失败前的成功快照兜底。

App 不在此查询回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 APPROVED Developer 状态，避免循环 RPC。单次 provider 读取是权威快照，不宣称跨 App/Auth 原子提交。App 状态更新后的在途快照窗口、短期委托 JWS 窗口见 [传播边界](oauth-delegation-v1.md#撤销与时钟边界)。未来 STABLE/灰度发布需先有独立的公开运行资格用例，再扩展 channel；不能拿 TEST client 作为生产所有用户入口。

## 消费点与契约验收

Auth 在授权页准备、用户确认、code 兑换、refresh、UserInfo 和每次委托签发时都重新确认 App 资格；client secret 只在 confidential 的 token/revoke 操作验证，不随每个资源请求发送。

双方至少测试：metadata 无 secret；一次返回和未知提交；轮换/禁用并发；跨应用管理员；revision 混合；伪造 version/scopes；Tester 移除后重加；发布槽位变化；快照过期；Auth 无 service permission；Auth→App 故障时零签发。接口不是 public introspection，也不允许资源服务自行抓取 secret 来验用户 token。
