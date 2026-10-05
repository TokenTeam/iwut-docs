<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-015 --spec tools/brief-specs/UC-AUTH-015.json -->
# Brief — UC-AUTH-015：兑换授权码并签发 OIDC 凭据

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-015` 兑换授权码并签发 OIDC 凭据 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAU-005`、`BR-OAU-006`、`BR-OAU-007`、`BR-OAU-008`、`BR-OAU-021` |
| 外部引用 BR | `BR-ACC-012`（来自 `UC-AUTH-025`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/app-oauth-client-v1.md`、`platform/contracts/auth-scope-catalog-v1.md`、`platform/contracts/oauth-delegation-v1.md`、`platform/contracts/oauth-oidc-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](../use-cases/UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 UC025 注销是删除本人 pairwise 映射的明确例外：Application sector 保留，旧 sub 不转让或复用。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

应用按登记认证方式兑换 code，得到独立 ID Token 和 access token。两种接入方式共用一次性授权码状态机，不签发通用平台 Session。

### 输入与输出

POST /token，grant_type=authorization_code、code、redirect_uri；PUBLIC 表单 client_id+code_verifier，CONFIDENTIAL HTTP Basic，并在发起时提交 PKCE 的情况下附 verifier。成功字段和 ID Token 校验约定见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

### 主流程

1. 读取稳定 client 元数据，按登记类型校验认证；secret 验证结果必须与当前 credentialRevision 一致。PUBLIC 不存在 credentialRevision。
2. 查 code 摘要，验证 client、code 中绑定的精确 redirect、PKCE、期限和用途；使用 code 保存的 expected runtime tuple（含 profileRevisionId）与 authId 重新调用 App `ResolveAuthorizationContext`，确认当前 Version 回调仍包含该精确 URI、当前公开资料未变化，并重新确认用户、Developer、grant revocationEpoch 及 scope。
3. 生成 opaque access token 与独立 ID Token；符合 UC-AUTH-016 时生成 refresh family。
4. 在原子确认点消费 code，登记凭据摘要、family 和审计，检查 grant/用户写入栅栏。
5. 仅确定提交成功后返回。客户端验证 OIDC 输出再建立自己的应用会话。

### 验收场景

- PUBLIC S256、CONFIDENTIAL Basic、CONFIDENTIAL Basic+S256 三条正向路径产生不同 id_token/access_token。
- 缺 secret、认证来源冲突、PKCE 降级、跨 client code、redirect 不匹配失败；共享 grant 的两类 client 也不能互相兑换 code。
- grantId 指向其他用户、应用或渠道时拒绝；另一 client 新增同意不扩大当前 code 的 scope。
- 并发兑换仅一份凭据提交，正确重放撤销原 family；错误 client 不能撤销他人 family。
- ID Token aud/nonce/at_hash 正确，同 Application 的 pairwise sub 跨 client/type/channel/Version 稳定且与学生关联无关。
- secret 轮换使旧 secret 无法继续兑换，但不撤销既有 grant 与已签发 token；新 secret 可用于之后的新请求。
- code 签发后 scope 停用，兑换返回 invalid_grant 且不消费 code；目录不可读为依赖错误，不伪装为用户撤回。
- 授权撤回、App 快照过期、事务/签名失败、未知提交不会多发可用凭据。
- code 创建后当前公开 ProfileRevision 改变时兑换失败，不能以旧展示资料对应的交互继续签发。
- 三渠道均覆盖 PUBLIC/CONFIDENTIAL；共享 sector/sub 不共享 grant/code/token。批准回调清单包含其它渠道时，TEST 授权仍可正常进行。
- STABLE 清空或 GREY 缩量/停止发生在 code 兑换前时重查资格及精确 runtime tuple，拒绝陈旧 code，不消费或跨渠道兜底。

### 依赖与实现边界

依赖 UC-AUTH-014、UC-APP-018/019 与 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。没有 UC-AUTH-016 时不签 refresh token；UC-AUTH-017 提供标准 UserInfo，UC-AUTH-019 为业务资源校验 access token。Mongo unique/TTL 索引与事务写入栅栏在实现工作包落实，不以 TTL 删除代替在线状态判断。

### 变更记录

- 2026-09-27：code 兑换以完整 App runtime/Tester tuple 重新解析，并确认当前批准 Version 仍包含 code 绑定的精确 redirect URI。
- 2026-09-30：App runtime tuple 纳入 profileRevisionId，code 兑换重新确认当前公开资料未变化。

## 业务规则（UC-AUTH-015 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-005 -->
### BR-OAU-005：客户端认证与证明不可降级

认证方式由稳定 client identity 决定，精确规则见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。secret 校验由 App 专用内部接口执行；Auth 必须把验证结果与本次 credentialRevision 对齐。PKCE challenge 已存在时没有 verifier/不匹配均失败；未提供 challenge 时提交 verifier 也拒绝，避免意外忽略证明。client 类型、code 绑定、nonce 和 verifier 不能由兑换请求重新指定。即使两个 client 共享 grant，也不能互相兑换 code；ID Token 的 aud 及新 token/family 的 client 归属仍为原 code 的 client。

<!-- 权威位置: use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-006 -->
### BR-OAU-006：授权码一次性兑换与重放处置

code 只能消费一次；校验失败不消费正确 code。并发兑换通过原子状态迁移至多一个成功；发现已正确绑定到调用 client 的 code 被再次兑换时，返回 invalid_grant 并撤销该 code 已产生的 token family（包含 access token，即使没有 refresh token）。先验证 client 和 code 的绑定/证明，不能让匿名猜测触发他人 family 撤销。

签发结果未知时不返回秘密、不缓存可再次取出的明文 token；客户端重新发起授权。事务回滚不能留下已消费 code 却无对应凭据的可见中间状态。

<!-- 权威位置: use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-007 -->
### BR-OAU-007：独立凭据与有界权限

access token 记录 tokenId/digest、authId、clientId、applicationId、固定 channel/rpcApiMajor、grantId/revision（审计）/revocationEpoch、client authorizationEpoch、testerMembershipId（TEST 必填，STABLE/GREY 为空）、签发时 App 资格版本、scope、audiences、familyId、签发/到期/撤销状态。所引用 grant 的 `(authId, applicationId, channel)` 必须与 code/token 及 App 确认的 client 归属一致，不能仅凭 grantId 或相同 sub 放行。scope 来自 code 且仍为当前 grant、应用许可和 UC014 定义的当前目录集合 C 的子集；code 中任一 scope 已停用则本次兑换失败，不消费 code、不静默缩小范围或签发包含停用项的凭据。audiences 只由 Auth 部署的 scope 资源映射得出。签发时 Version 用于审计和当次 code 一致性，不把 token 身份改成 Version 身份。只含 openid/email 的 token 仅可访问 UserInfo，不因此获取其它资源。

ID Token 是面向 client 的登录证据，格式和 pairwise sub 由 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md) 定义；不与 access token 复用值、用途或 verifier。用户的资料/身份关联不是默认 claims，subject 不能由客户端指定。

<!-- 权威位置: use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-008 -->
### BR-OAU-008：签发一致性与故障关闭

最终写入与 grant 撤销、family 撤销及用户可用状态检查共用 Auth 本地原子栅栏。App 外部快照只在限定时间有效，不声称跨库事务。secret 轮换导致旧 secret 认证失败、client 禁用、发布/Profile/渠道用户资格变化、当前 Version 不再包含 code 绑定的精确 redirect URI，或凭据记录与快照不一致，均拒绝本次兑换。轮换不会仅凭 credentialRevision 撤销已经签发的 token/family 或稳定 grant。

未知/过期/错误 code 及错误 verifier 统一 invalid_grant；服务故障用 temporarily_unavailable。日志、审计和 metrics 不记录任何 token、code、secret 或 verifier。

<!-- 权威位置: use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021 -->
### BR-OAU-021：Application 级 sector 与主体映射

Auth 唯一保存 applicationId→sectorId/sectorIdentifierUri，以及 `(authId,sectorId)→sub`。只有通过 App 受授权 provider 确认 clientId 所属 Application 后，才能首次原子创建该应用的随机 sector；applicationId、sectorId/hostname、映射键分别有唯一约束，并发首次登录得到同一结果。主体映射首次生成随机 UUID，之后永久稳定、不重用、不由请求方指定。

同一 Application 的所有渠道、major、版本、回调 hostname 和两种 client 类型共享 sector/sub；不同 Application 不因开发者相同而共享。App 不保存 sector 副本或执行用户映射，Auth 不复制另一份可修改的 client 注册表。学校 association 与该映射无关。

sector 在部署的稳定域名空间中分配，不随常规 issuer 配置、secret 或签名密钥轮换重建；搬迁 sector 域名属于独立身份迁移，不能当作普通环境变量变更。标准 sector URI 的地址、回调清单和校验规则见 OAuth/OIDC v1。映射数据库及长期域名属于必须保留的身份数据，读取错误不能重新分配 sub。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-025`

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-012 -->
### BR-ACC-012：清理范围与最小永久保留

首版数据策略如下；期限是上限而非必须保存到最后一天。实施时必须检查与各现行永久占用/审计规则的冲突并同步修改，不以本草案直接删除生产数据。

| 数据 | 终止后处理 |
| --- | --- |
| 主体、资料 | 活动存储删除资料 values、显示资料及业务能力；永久最小墓碑仅保留 authId、principalType=USER、CLOSED、最终 accountRevision、terminatedAt、closureOperationId，保证历史引用和不可复活，不保留学校关联、邮箱或公钥 |
| 激活/待绑定邮箱、短期邮件操作 | 清理邮箱原文、唯一归属及短期材料；移除唯一占用的事务提交后才可由新账号重新验证注册。清理前统一不能用该邮箱恢复 CLOSED 账号，不将旧验证码改绑新账号 |
| 设备凭据 | 删除公钥及使用元数据；永久保留规范公钥指纹和 CLOSED authId 的最小占用墓碑，防止旧设备密钥跨账号重用，延续 UC009 不释放密钥归属的约束。新注册必须使用新密钥 |
| Session、挑战及结果、授权交互、code/access/refresh/family | 删除秘密摘要、操作内容及业务记录；由永久主体墓碑防重建，不为检测重放继续保存已终止账号全部 token 历史 |
| grant、pairwise 用户映射 | 删除该 authId 的 consent 内容及 `(authId,sectorId)→sub` 映射；不删除 Application 的 sector。旧 sub 不转交新账号，日志/第三方引用不宣称被删除 |
| 学生关联 | 删除本账号的成员关系及其专属材料；组仍有其他成员时保留组，不暴露或改变其他成员；无成员且无合法未决引用时，在关联事务栅栏下删除 lookup/关联密文和空组。并发注册加成员不得误删共享组 |
| developerHandle | 永久保留规范 handle、原 authId、claimedAt 和终止占用标记；不转让、不释放、不连同邮箱/资料保留。该最小公开命名空间墓碑明确向本人披露 |
| Auth 审计 | 只读期内保留最小事件归因，不保留 token/邮箱/资料副本；账号相关普通事件上限为事件发生后 180 天，已超期的随本次任务清理。注销事件保留 180 天；期满按专用保留任务删除，不由业务更新覆盖 |
| 协调决定、清理进度及查询令牌 | App 确认终局前保留必要决定；查询摘要最多 30 天，详细清理任务在全部步骤完成且终局回执后清理，永久终止事实由最小墓碑承担 |

默认活动存储清理目标为终止后 24 小时，超时告警并保留失败进度，绝不伪报完成。普通日志不应保存上述秘密，已经存在的可识别普通日志轮转上限 30 天；备份自然淘汰上限 30 天。部署未落实这些期限时不得展示该承诺或启用入口。

现有审计的 append-only 表示保留期内不可更新/删除；接受本 UC 时需要明确增加受控保留期清理例外，不能由普通业务账号任意删除审计。永久墓碑的字段就是允许保留的完整集合，不能附加整份 principal 或自由文本快照。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/app-oauth-client-v1.md`：App OAuth Client 提供方契约 v1

#### 所有权与调用方

App Center 持有 Application＋channel 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，STABLE/GREY 渠道扩展分别见 [UC-APP-020](../../app-center/use-cases/UC-APP-020-manage-stable-publication-slot.md) 与 [UC-APP-021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md)，协议见 [OAuth OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

管理接口接受 SESSION 转换后的 [trusted identity](../../platform/contracts/trusted-identity-v1.md) USER 身份。内部接口只接受 Auth 的 [service identity](../../platform/contracts/trusted-service-identity-v1.md)，audience 固定为 `iwut-app-center`，权限来自 App Center 本地 caller registry；逐方法授权，不经过公网、HTTP 或 gRPC-Web，也不把 client secret 当服务间凭据。

#### 三种生命周期

`ApplicationOAuthRegistration` 以 `(applicationId, channel)` 唯一，字段为 applicationId、channel、publicClientId、publicStatus、publicAuthorizationEpoch、confidentialClientId、confidentialStatus、confidentialAuthorizationEpoch、registrationRevision、createdAt、updatedAt。两个 clientId 均为服务端 UUIDv4、全局唯一、永久不重用；type 由其所在 slot 确定，状态为 `ACTIVE/DISABLED`。client identity 固定归属一个 channel，不包含 rpcApiMajor、Version 或 hostname。

`OAuthClientCredential` 以 confidentialClientId 唯一，字段为 confidentialClientId、applicationId、secretDigest、credentialRevision、rotatedAt。channel 从 confidentialClientId 的 registration 确认，不能跨渠道使用。它只服务于以后 confidential client authentication；secret 轮换不改变 registrationRevision。

`ApplicationVersionOAuthConfig` 以 applicationVersionId 唯一，字段为 applicationVersionId、applicationId 和：

```text
oauthRedirects {
  pkceRedirectUris: []RedirectURI
  confidentialRedirectUris: []RedirectURI
}
```

它使用独立 collection 存储，但生命周期严格依附 ApplicationVersion：与 Version 同事务创建/编辑，使用同一个 Version revision 做 OCC，提交时深拷贝进 Review snapshot，提交后不可独立修改。两个数组均非 null、各 0–10 项、内部唯一且彼此不交叉。详细 URI 规则见 [BR-VER-018](../../app-center/use-cases/UC-APP-002-create-application-version.md#br-ver-018)。

#### 管理接口

建议服务 `app_center.v1.oauth_client.OAuthClientService`。可执行 Proto、字段号与 HTTP annotation 在独立 API 仓库落地。

| 方法 | 输入 | 输出 |
| --- | --- | --- |
| RegisterOAuthClient | applicationId、channel、type、optional expectedRegistrationRevision | registration；仅 confidential 额外返回一次 clientSecret |
| GetApplicationOAuthRegistration | applicationId、channel | 当前管理员可见的 registration 元数据 |
| SetOAuthClientStatus | clientId、expectedRegistrationRevision、status | 新 registration；相同状态为 no-op |
| GetOAuthClientCredentialMetadata | clientId | credentialRevision、rotatedAt；不含 secret/摘要 |
| RotateOAuthClientSecret | clientId、expectedCredentialRevision | 新 credential 元数据及一次性 clientSecret |

每个 Application 每渠道每种 type 至多登记一次。registration 尚不存在时 expectedRegistrationRevision 必须为空，结果 revision=1；已存在且补登记另一 type 时必须提交当前 revision。登记不依赖 Version、Review 或 Publication；丢失登记响应时先查询，secret 丢失则轮换。禁用和重新启用使用 SetOAuthClientStatus，不删除 identity。

secret 为 32 随机字节的 base64url 无 padding 字符串。App 仅存 `SHA-256("iwut-oauth-client-secret-v1\0" || clientId || "\0" || secret)`，使用恒定时间比较；只保留当前摘要。创建/轮换成功响应使用 no-store；提交结果未知时不能返回可能未提交的 secret。

#### Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | identity 元数据（含固定 channel、registrationRevision、该 slot 的 authorizationEpoch）、tokenEndpointAuthMethod；CONFIDENTIAL 含 credentialRevision |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedCredentialRevision | verified、credentialRevision；不返回摘要 |
| `/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` | clientId、channel、rpcApiMajor、expectedRegistrationRevision | 当前批准的运行配置 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、channel、rpcApiMajor、expectedRegistrationRevision、expectedRuntimeVersion | 当前用户授权上下文 |
| `/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` | applicationId | PublishedRedirectSnapshot |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。permission 只授予指定 Auth 服务主体；SYSTEM、USER 和第三方 access token 均不能调用。Verify 对未知 client、错误 secret、PUBLIC、DISABLED 或 credential revision 不一致返回 `verified=false`。原 secret 只经 TLS 内网发送，拦截器和代理禁止记录 metadata/body。

`RuntimeConfiguration` 包含 clientId、applicationId、type、channel、rpcApiMajor、registrationRevision、authorizationEpoch、adminAuthId、versionId、publicationRevision、redirectUris、requiredScopes、optionalScopes、display、observedAt、validUntil。

`ApplicationDisplay` 包含 profileRevisionId、displayName、可空 description 和可空 icon。全部内容来自 `currentPublishedProfileRevisionId` 指向的同一 Application、APPROVED ProfileRevision；不提供 Application 技术名称 fallback，也不返回 HTML。运行 tuple 中的 profileRevisionId 即 `display.profileRevisionId`，不在 RuntimeConfiguration 顶层重复保存。

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和可空 testerMembershipId。TEST 必须返回当前 ACTIVE Tester episode；STABLE/GREY 为空。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, profileRevisionId, adminAuthId)`；expectedRegistrationRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置、当前公开资料和渠道用户资格。

redirectUris 来自批准 snapshot：PUBLIC 读取 pkceRedirectUris，CONFIDENTIAL 读取 confidentialRedirectUris；对应数组必须非空。requiredScopes/optionalScopes 来自同一 snapshot，不按 App 的 requestable 缓存过滤；Auth 根据 [Scope Catalog 契约](../../platform/contracts/auth-scope-catalog-v1.md) 对应的当前权威 enabled 和 OAuth UC 执行最终授权。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记；channel 必须与 client 登记值完全相等，rpcApiMajor 只选择该渠道的权威 Publication；TEST/GREY/STABLE client 不能互相替代。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。登录前后 registrationRevision 和 runtime tuple 必须一致；Profile 批准后当前公开指针发生变化也必须重新开始或重新展示。credentialRevision 只约束一次 secret 验证，不进入 runtime tuple。

Grant 按 [UC-AUTH-014 / BR-OAU-002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 的 `(authId, applicationId, channel)` 业务主键保存，同应用同渠道的两类 client 及各 major 共享历史同意。App 提供可信的 client→applicationId/channel 归属，不管理 grant；Auth 不能从前端自报值推导共享范围。授权交互和 code 绑定精确 runtime tuple、redirect URI 和 scope；access/refresh 绑定不可变 channel/rpcApiMajor、authorizationEpoch、Tester episode。Version ID 只用于审计，后续在 token 原来的 major 上重新解析当前版本，不能由资源请求改选 major。Auth 保留历史同意集合，按当前有效交集决定权限；具体规则只由 UC-AUTH-014/016/018/019 定义。

#### Sector 的只读配置来源

Auth 唯一拥有 `applicationId → sector` 和 `(authId, sector) → sub`。App 的上述接口只提供可信 clientId/applicationId/channel/type 关系，不接受或返回客户端指定的 sector，不保有第二份 sector 映射。

`PublishedRedirectSnapshot` 包含 applicationId、entries、redirectUris、observedAt、validUntil。entries 按 `(channel,rpcApiMajor)` 排序，含 versionId/publicationRevision；redirectUris 是该应用当前已启用渠道、全部已发布 major 的批准 snapshot 中两类回调的去重排序并集。未发布 draft、历史已替换版本、没有对应 registration 的 type 不纳入；DISABLED client 不导致已有 sector 删除。无已发布回调时返回空集合；事实不一致或存储故障返回不可用，不伪造空成功。一次 snapshot 读完，期限同上；只读该应用，不能因它包含正式渠道就授予 TEST 用户正式权限。

Auth 用此快照提供标准 sector URI 的 JSON 清单。准备 OIDC 注册元数据时，对照同次 runtime 使用的 `(channel,major,versionId,publicationRevision)`；两份快照若不匹配就重新读取或失败关闭，不用跨版本拼接的清单完成注册验证。此查询不回调 Auth，不公开用户、secret、scope 或运行资格；标准清单的公开范围和协议见 OAuth/OIDC v1。

#### 资格变化与失败

client 不可用、对应回调数组为空、无 exact-major 渠道 Publication、无当前已批准公开资料或批准记录不一致均不可授权；TEST 还要求 ACTIVE Tester，GREY 还要求可信 authId 命中当前 rollout cohort。设计支持 channel=`TEST/GREY/STABLE`；GREY 随 UC-APP-021 工作包交付。正常缺少运行资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因；公开资料指针存在但目标缺失、跨应用、非 APPROVED 或内容损坏返回 `INTERNAL`。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照或 Application 技术名称兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。

#### 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认和 code 兑换重新解析用户上下文。refresh、UserInfo 和每次委托签发按 OAuth/OIDC v1 的当前资格规则验证。confidential secret 只在 token/revoke 操作验证。

双方至少测试：每种 type 的 clientId 稳定；metadata 无 redirect/secret；一次 secret 返回；registration 与 credential revision 并发隔离；跨应用管理员；runtime tuple 混合；同 clientId 跨 Version/major 选择；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；公开资料切换和损坏指针；hostname 迁移；快照过期；服务 permission；Auth→App 故障时零签发。

#### STABLE 扩展

[UC-APP-020](../../app-center/use-cases/UC-APP-020-manage-stable-publication-slot.md) 沿用同一组五个 provider 方法：STABLE runtime 精确读取 stableVersionId，用户上下文不要求 Tester Membership，testerMembershipId 按渠道为 TEST 必填/STABLE 为空，批准回调进入 sector 并集；管理面启用独立 `(applicationId, STABLE)` registration/credential。TEST 语义保持不变，STABLE client 不能代替 TEST client，Auth grant 继续按 `(authId, applicationId, channel)` 隔离。

#### GREY 扩展

[UC-APP-021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md) 沿用同一组五个 provider 方法：GREY runtime 精确读取 exact-major GreyRollout 的 versionId；用户上下文使用 Publication 内部 cohortSeed 对可信 authId 重算 `grey-bucket-v1`，未命中时返回统一 runtime unavailable，不能披露 bucket 或 seed。GREY 不要求 Tester Membership，testerMembershipId 为空；批准回调进入 sector 并集。管理面启用独立 `(applicationId, GREY)` registration/credential，Auth grant 继续按 `(authId, applicationId, channel)` 隔离。

比例、目标 Version 或 Clear 都改变共享 publicationRevision，因此登录前 runtime tuple 不能跨 rollout 变化继续使用。Provider 不负责 `test > grey > stable` 默认路由；后续统一解析先选择 channel，Provider 再验证明确的 GREY client 和用户 cohort。

### `platform/contracts/auth-scope-catalog-v1.md`：Auth Scope Catalog v1 跨服务契约

#### 目的与所有权

本契约定义读取 Auth 权威 Scope Catalog 完整快照的线格式和原生 gRPC 边界。业务行为由 [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 及其 `BR-SCP-*` 拥有；本文件不复制 Auth 的内部持久化或目录管理规则。

Auth Center 是提供方，App Center 是首个消费方。可执行 Proto 由独立 API 仓库拥有，目标目录为 `auth_center/v1/scope_catalog/`。

#### gRPC 方法

首版只提供内部原生 gRPC：

```text
/auth_center.v1.scope_catalog.ScopeCatalog/GetScopeCatalogSnapshot
```

Proto 结构：

```proto
service ScopeCatalog {
  rpc GetScopeCatalogSnapshot(GetScopeCatalogSnapshotRequest)
      returns (GetScopeCatalogSnapshotResponse);
}

message GetScopeCatalogSnapshotRequest {}

message GetScopeCatalogSnapshotResponse {
  int64 revision = 1;
  google.protobuf.Timestamp generated_at = 2;
  repeated ScopeDefinition scopes = 3;
}

message ScopeDefinition {
  string name = 1;
  bool requestable = 2;
}
```

不声明 `google.api.http` annotation，不经 Gateway 暴露，不提供浏览器或 gRPC-Web 入口。

#### 快照语义

- `revision` 必须大于零，并遵循 [BR-SCP-003](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- `requestable` 固定投影 Auth 当前 `enabled`，状态定义唯一引用 [BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。停用项仍返回，值为 false；不增加独立 runtimeEnabled 字段。
- App 消费方继续把 `requestable = true` 的 name 用于版本申请、审核和发布规则的目录检查；它不是最终用户授权结果。Auth OAuth 路径直接检查自己的当前权威状态，不以 App 缓存或历史批准快照代替。
- 消费方遇到未知追加字段时必须忽略，以保持向后兼容。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证内部服务身份。Auth Center 在验签后按固定 full method → `auth.scope-catalog.read` 映射检查 caller 注册表；认证成功不自动产生读取权限。

测试 Auth Server 可以验证 consumer 行为，但生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_SCOPE_CATALOG_READ_FORBIDDEN` |
| 权威目录暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含凭证、存储查询、连接地址、Scope 私有元数据或堆栈。调用方不得把失败时持有的过期快照包装成本次成功响应。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. gRPC full method 与 package/service/rpc 名称准确。
2. request message 没有业务字段或用户身份字段。
3. response 字段号和类型与本契约一致。
4. 空目录编码为空列表，不是错误或伪造占位 Scope。
5. duplicate/empty name、非正 revision、无效 generatedAt 或非稳定排序不能作为成功快照。
6. `UNAUTHENTICATED`、`PERMISSION_DENIED`、`UNAVAILABLE` 与稳定 reason 映射一致。
7. App Center E2E 的测试 Auth Server 实现同一生成接口，不维护另一份手写 wire model。
8. Provider 的 enabled 状态与 requestable 投影一致，启停递增 revision；完整快照保留停用项，App 的既有布尔校验无需新增状态分支。

#### 兼容性

- 本次 enabled 单状态决定保留 `bool requestable = 2`、消息名和 full method，不要求 App 修改 Proto 或 UC-APP-018 client 管理逻辑；App 无需持久化第二份 enabled。现有“true 可申请、false 不可申请”的消费方式保持兼容，新增约束是 Auth 从唯一状态生成该投影。
- v1 可以追加 optional 字段或新增错误 reason，但不得改变现有字段号、字段类型或 full method。
- 删除字段时保留其 field number 和 name 为 `reserved`。
- 改变完整快照、revision 或 requestable 的语义需要新的平台契约评审；不能只修改某一方实现。

#### 关联文档

- [UC-AUTH-001：获取 Scope Catalog 快照](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)
- [ADR-001：Scope Catalog 权威来源与缓存](../../app-center/adr/ADR-001-scope-catalog-cache.md)
- [UC-APP-002：创建应用版本](../../app-center/use-cases/UC-APP-002-create-application-version.md)

### `platform/contracts/oauth-delegation-v1.md`：OAuth 委托上下文与 Traefik 契约 v1

#### 链路与身份隔离

```text
应用 ─ Bearer access token → Traefik
  HTTP：ForwardAuth → Gateway → Auth 在线校验 + 签发委托 JWS
        Traefik 复制委托 JWS → 固定 Router → 资源服务验签与业务授权
  gRPC：Traefik → Gateway 精确 unary 代理 → Auth → 资源服务
  gRPC-Web：Traefik 协议转换 → 同一 unary 代理
```

Traefik 阶段完成入口检查，但 token 真伪、grant、scope 的权威判断仍由 Auth 完成。随机 access token 不可本地验签；Traefik 不持有 Auth 私钥，也不查询 Mongo。不开 Redis，不缓存 token 校验结果或签发结果。

委托上下文使用 `x-iwut-delegation`，与 SESSION 的 [x-iwut-identity](../../platform/contracts/trusted-identity-v1.md) 分离。ID Token、平台 Session、service JWS 不可作为 OAuth Bearer token。第三方应用不能通过 OAuth scope 获得原有 developer/reviewer/管理员 USER 身份；管理端原有 SESSION 路由继续只接受平台 Session。

规则归属：[UC-AUTH-019](../use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-GW-002](../../gateway/use-cases/UC-GW-002-authenticate-oauth-and-forward.md)。本契约与 [ADR-GW-001](../../gateway/adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) 配合，保留其固定 Traefik 版本和三协议适配方式。

#### Auth 签发 RPC

可执行 route manifest、规范摘要字节与本地时钟观测格式见 [OAuth route policy v1](../../platform/contracts/oauth-route-policy-v1.md)。

唯一新内部方法为 `/auth_center.v1.oauth_delegation.OAuthDelegationService/IssueDelegationContext`。仅 native gRPC/TLS，调用者必须是授权 Gateway service principal，permission=`auth.oauth.delegation.issue`，audience 为 Auth，metadata：

- `authorization: Bearer <Gateway service JWS>`；按既有 service identity 验证。
- `x-iwut-access-token: <opaque token>`，恰好一个值，不带 Bearer。

请求字段：routeId、policyDigest、protocol、method、targetPath；签名协议值固定 HTTP 或 GRPC，gRPC-Web 转换后也是 GRPC。HTTP method 为大写方法名；gRPC method 为完整 RPC 名且不发送 targetPath。响应字段：delegationJws、expiresAt。不接收 userId、clientId、scope、角色、上游 URL 或任意 audience 覆盖。

部署路由目录是静态可信输入，同一工具生成 Gateway 路由与 Auth 的 OAuth route policy 清单。每项固定 routeId、目标 audience/upstream、协议与方法、HTTP 精确路径或受限路径模板及重写规则、requiredScopes（全部满足）、allowedChannels、策略版本；对规范化完整清单取 SHA-256 得 policyDigest。Auth/Gateway digest 不匹配拒绝服务，不从请求补全策略。OAuth 路由必须有明确非空 scope 要求；只拥有 openid 不自动获得业务 API 权限。

Gateway 以已匹配的静态路由构造请求，Auth 根据本地清单复核 method/path/audience。现有服务签发允许列表新增此精确 RPC 与允许 routeId/audience，不能用 `auth_center.*` 通配。UserInfo 是 Auth 自行认证的标准 DIRECT 端点，不再调用自身委托 RPC。

#### 委托 JWS

单个 compact JWS、不带 Bearer，大小至多 8 KiB。RS256、独立用途的签名 key/kid；header `typ=iwut-delegation+jwt`，不与公开 OIDC JWKS 或 USER/service 验证器共享可接受密钥集。

| claim | 语义 |
| --- | --- |
| iss、aud | 配置的 Auth issuer、单个目标资源 audience |
| sub | 内部 authId，只在平台内网下游使用，不向应用返回 |
| client_id、application_id | 已认证 token 所属 client 和应用 |
| grant_id、grant_revision、grant_revocation_epoch | 按用户、应用及渠道共享的授权引用、审计 revision 与撤销 epoch；同渠道不同 client 可携带相同 grant_id |
| channel、rpc_api_major、client_authorization_epoch | token 固定运行上下文及 client 状态 epoch |
| scopes | UC-AUTH-019 计算的有效交集 E；不包含当前版本未允许的历史同意或 token 外的新增 scope |
| route_id、policy_digest、protocol、method | 绑定本次路由/策略/协议/操作 |
| target_path | HTTP 重写后的 escaped path；gRPC 不出现 |
| iat、nbf、exp、jti | 签发时间、当前有效、最长 5 秒、独立随机 ID |

exp 不晚于 access token 到期时间。无 permissions、developer_status、email、学校关联值、平台 Session 或 token 原文。Auth 检查 token 对本 audience 的许可；token 的 audience 集合由已授予 scope 的受信映射产生，客户端不能自报。

client_id 始终为本次 access token 所属 client，不因 grant 共享而替换；Auth 按 [BR-OAU-018](../use-cases/UC-AUTH-019-issue-delegation-context.md#br-oau-018) 验证 token、grant 和 App client 归属一致。

资源服务必须验证签名、固定算法/typ/kid/issuer/audience、时限和本次 method/route/policy/target_path，再以 sub 做数据归属检查，以 client_id/application_id/channel 做应用环境约束。route policy 显式配置非空 allowedChannels，允许 TEST/GREY/STABLE 的唯一子集；未知或重复项拒绝。仅限正式渠道的路由拒绝 TEST token；允许多个渠道的共享资源仍分别检查各自 grant/E，不能因为 OIDC sub 相同绕过渠道许可。可验证委托 JWS 不等于全部业务许可。不得把委托转换成通用 USER 管理身份。只在配置明确启用的 OAuth 方法接受该 header，未知入口拒绝。

HTTP path 必须经过路由生成器规定的单次解析和固定重写；拒绝非法 percent encoding、编码斜线/反斜线、dot segment 和无法唯一匹配的路径。Gateway 签发请求与后端收到的 escaped path 必须字节相等；查询参数不作为路径签名的一部分，业务仍验证其中的资源 ID/过滤条件，不能把 query 当授权范围来源。

#### Traefik HTTP 契约

OAUTH2 路由中间件顺序固定：

1. 拒绝重复/别名/下划线混淆的身份或凭据 header；删除外部 x-iwut-identity、x-iwut-delegation、x-iwut-session、x-iwut-access-token、service/policy 身份头及旧用户头。保留待检查的单个 Authorization。清理外部伪造 Forwarded/X-Forwarded-*，由可信入口重新构造。
2. ForwardAuth 指向内网 Gateway，URL 路径中的 routeId 来自生成配置；Gateway 与受信转发 method/URI 对照匹配，不能从用户 header 选择路由。认证 listener 不暴露公网，只接受 Traefik 受信网络/连接。
3. 配置 `trustForwardHeader=false`、`forwardBody=false`、显式 authRequestHeaders 最小白名单（Authorization 及受控追踪 ID）；由 Traefik 生成的转发元数据在受信边界内校验。`authResponseHeaders=[x-iwut-delegation]`，禁止宽泛正则复制身份头；限制认证响应 body 为 4096 字节、上下文 header 为 8 KiB。
4. 仅认证 200 且有恰好一个合法形状的委托 JWS 才继续。Traefik 复制该 header，随后移除 Authorization、全部内部请求凭据、官方门户 Cookie 与路由策略辅助 header，再按同一固定路由转发。认证响应不向最终客户端泄露内部 JWS。
5. 业务 upstream 不对公网可达；资源服务仍按前节独立验签。不得把认证成功当作省略验签的理由。

以上行为需用固定版本的真实 Traefik 验收；若 ForwardAuth 200 缺 header 无法由原生配置拒绝，Gateway 的认证处理器必须将缺失签名转换为 503，资源服务也必须拒绝缺失身份。关闭 authSigninURL 等自动 API 登录跳转。签发/转发每步有界 deadline（初始建议总鉴权 2 秒）；认证失败不得转发业务请求，不自动重试业务 mutation。

`OIDC_HTTP` DIRECT 另设明确凭据白名单：/token 与 /revoke 可保留 Basic；/userinfo 可保留 Bearer；/authorize 与 /portal/* 只向 Auth 传门户 cookie/指定 Session；其他 client 身份头仍先清理。只有明确登记的 POST /portal/session 可保留 x-iwut-session。不允许为了 token endpoint 全局打开 Authorization 转发。Auth sector URI 的专用 host 路由也仅 GET /redirect-uris.json，Traefik 按部署受信后缀及固定 UUID 主机名格式匹配到 Auth upstream，Auth 再核对完整 host 与已分配 sector 的归属。新增 sector 无需重新生成每应用 Router；未知 UUID 由 Auth 返回 404。不得把请求 Host 当作新 sector 的创建依据或自由上游地址，未知 host 拒绝。发现/JWKS 只 GET；授权页面及标准端点不经 gRPC-Web 转换。

#### 错误与协议适配

| 情况 | HTTP | native gRPC / gRPC-Web |
| --- | --- | --- |
| token 缺失、非法、过期、授权已撤回 | 401，Bearer invalid_token | UNAUTHENTICATED |
| token 有效但本路由 scope 不足 | 403，Bearer insufficient_scope | PERMISSION_DENIED |
| 限流 | 429、Retry-After | RESOURCE_EXHAUSTED |
| Auth/App 不可用、内部凭据/策略配置失效 | 503 | UNAVAILABLE |

native gRPC 与转换后的 gRPC-Web 必须经现有 Gateway unary 前置代理构造合法 gRPC status/trailer，不直接套 HTTP ForwardAuth 错误。非法路由/方法沿用现有未知入口拒绝规则，不猜测 token 类型或降级 SESSION/DIRECT。scope 错误只公开该路由可公开的要求，不泄露用户其它授权。

#### 撤销与时钟边界

Auth 本地 grant/token 撤销与最终签发共用原子栅栏：撤销提交后开始的新检查不得再成功。已签发的委托 JWS 最长 5 秒，资源服务只允许 1 秒时钟容差；部署必须监测时钟偏移，超界停止签发。

App 使用最长 5 秒的单次快照，Auth 只在快照未过期时完成本次决策；它不是跨库锁或永久租约。故 App 配置/资格变化到最后一个旧委托可被接受的上界为约 11 秒（快照 5 秒 + JWS 5 秒 + 时钟差 1 秒）。Auth 本地撤回的上界为约 6 秒。已开始的业务操作不回滚，长任务/流式 RPC 不在首版范围，不能声称全链路即时撤回。

token 校验不依赖原登录 Session 继续存在；用户退出平台 Session 不隐式撤回第三方 grant。账号不可用、grant/refresh family 撤销、client/config/资格变化按相关 UC 拒绝；第三方自己的登录会话、已下载数据不由此自动删除。

#### 验收与启用门禁

新增路由必须同时具备 Auth scope/audience 定义、App 批准 scope、资源服务专用委托验证器与业务权限测试。未具备时编译/启动校验拒绝启用该路由。测试伪造头、错误 token 用途、错误 aud/typ、route 混淆、跨应用 token、授权撤回、App 快照到期、secret 轮换、三协议失败零转发和直接绕过 Edge；ID Token 无论签名是否正确都不能调用业务 API。

配置行为依据 [Traefik ForwardAuth v3.7](https://doc.traefik.io/traefik/v3.7/reference/routing-configuration/http/middlewares/forwardauth/)。先完成 UC-GW-002 和联合验收，再改变现有 OAUTH2 默认关闭状态；本文不要求现有 SESSION 路由改用新的 header 或期限。

### `platform/contracts/oauth-oidc-v1.md`：OAuth 与 OIDC 接入协议 v1

#### 范围与职责

提供 Authorization Code Flow，用 OIDC ID Token 表达应用登录结果，用独立的 opaque access token 表达委托访问。Auth 拥有登录、consent、grant 和 token；App 拥有 client 身份/secret，以及 ApplicationVersion 中受审核的 redirect URI 和 scopes；Traefik/Gateway 执行入口鉴权，资源服务执行业务授权。

相关业务规则由 [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) 至 [019](../use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) 至 [021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md) 拥有。跨服务 App 接口见 [App OAuth Client v1](../../platform/contracts/app-oauth-client-v1.md)，入口和下游身份见 [OAuth 委托上下文 v1](../../platform/contracts/oauth-delegation-v1.md)。

#### 客户端配置

| 配置 | 使用场景 | token endpoint 认证 | PKCE |
| --- | --- | --- | --- |
| `PUBLIC_PKCE` | 原生客户端、浏览器应用，不能保守 secret | `none`，表单必须含 client_id | 必须 S256 |
| `CONFIDENTIAL_SECRET` | 能保守 secret 的应用后端 | `client_secret_basic` | 支持且建议叠加；一旦授权请求提交 challenge，兑换必须验证 |

两者都是授权码流程；client secret 认证应用后端，PKCE 绑定本次发起者与兑换者。不是 `client_credentials` 登录用户，也不支持 implicit/password grant。不支持 `client_secret_post`、`plain` PKCE、URL 中的 secret；多个认证来源或重复单值参数直接拒绝。Basic 按 RFC 6749 §2.3.1 编码。

PUBLIC client 不能提交 secret 冒充 confidential；CONFIDENTIAL client 不能省略 secret 降级为 public。无 PKCE 的 confidential OIDC 客户端必须依照下述 nonce 检查，在验证 ID Token 前不得建立应用会话或使用返回的 token。

每个 Application 每渠道（TEST/GREY/STABLE）分别登记稳定 PUBLIC/CONFIDENTIAL clientId 和 confidential secret；clientId 固定 channel，不绑定 RPC major、Version 或 hostname。不同渠道不得互用 client、grant、code、access/refresh token；App Center 已通过 UC-APP-019/020/021 交付 TEST/STABLE/GREY provider，Auth 按 UC014 的渠道资格规则消费。redirect URI 不保存在 client registration 中，而在当前批准并发布的 ApplicationVersion 中以 `pkceRedirectUris/confidentialRedirectUris` 表达。切换 Version 可以改变完整 URI，包括 hostname，而不重建 clientId。PUBLIC 与 CONFIDENTIAL 可以同时受支持，但使用两个 clientId，分别执行各自不可降级的安全规则。

#### 公网端点与响应

部署固定 HTTPS issuer，例如 `https://auth.example.org/auth-center/oidc`。issuer、端点和签发内容都来自受信配置，不能从请求 Host/Forwarded 推导。

| 相对 issuer 的路径 | 方法 | 入口策略与用途 |
| --- | --- | --- |
| `/.well-known/openid-configuration` | GET | DIRECT；discovery |
| `/jwks` | GET | DIRECT；仅 OIDC 公钥 |
| `/authorize` | GET、POST | DIRECT；Auth 自行校验参数及官方登录门户会话 |
| `/token` | POST | DIRECT；Auth 自行校验 client/code/verifier 或 refresh token |
| `/userinfo` | GET、POST | DIRECT；Auth 自行在线校验 access token，不使用 Session |
| `/revoke` | POST | DIRECT；Auth 自行校验 client 与待撤销 token |

上述 DIRECT 不等于无鉴权，只是不经过 Session→用户 JWS 的转换。标准端点属于 `OIDC_HTTP`，显式加入 Gateway 路由 schema；不能假造 HTTP annotation 或套用 Kratos ProtoJSON envelope。POST authorize/token/revoke 使用 `application/x-www-form-urlencoded`；UserInfo 的 token 仅接受 `Authorization: Bearer …`。不支持 query/body 传 access token。Discovery/JWKS 可公开缓存，其余响应 `Cache-Control: no-store`、`Pragma: no-cache`。

成功兑换示例（示例值不是可用凭据）：

```json
{
  "token_type": "Bearer",
  "access_token": "<opaque random token>",
  "expires_in": 900,
  "id_token": "<signed JWT, different from access_token>",
  "scope": "openid email"
}
```

只有按 UC-AUTH-016 获得离线授权时才增加 `refresh_token`。刷新响应保留 access_token/token_type/expires_in/scope/refresh_token，首版不重新签发 ID Token。

Discovery 必须准确声明 issuer、authorization_endpoint、token_endpoint、userinfo_endpoint、jwks_uri、revocation_endpoint；`response_types_supported=[code]`、`grant_types_supported=[authorization_code,refresh_token]`、`subject_types_supported=[pairwise]`、`id_token_signing_alg_values_supported=[RS256]`、`token_endpoint_auth_methods_supported=[none,client_secret_basic]`、`code_challenge_methods_supported=[S256]`。`response_modes_supported=[query]`、`authorization_response_iss_parameter_supported=true`；revocation 同样支持 none/basic。scopes_supported 仅列出实际装载、enabled=true 且已实现的 scope；不宣称动态注册、logout、introspection 或 JWT access token profile 已实现。

#### Scope 启用与兼容投影

Scope 单一启用状态与 requestable 投影唯一由 [UC-AUTH-001 / BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 定义；OAuth 当前目录许可集合 C 及授权/恢复边界见 [UC-AUTH-014 / BR-OAU-001、002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-001)。本协议不增加 requestable 与 runtimeEnabled 两个独立开关。

App 继续使用已有 requestable 字段进行版本管理检查；Auth 的 authorize、code 兑换、refresh、UserInfo 和委托签发分别遵循 UC014–019 的当前目录检查。停用不会调用用户撤销用例或抹掉历史同意。目录故障使用依赖错误，Discovery 缓存或 App 旧快照不改变运行判断。

#### 授权请求与登录门户

必填 `response_type=code`、client_id、精确 redirect_uri、含 `openid` 的 scope、state、nonce，以及产品扩展参数 `iwut_channel=TEST|GREY|STABLE`、正整数 `iwut_rpc_api_major`；PUBLIC 额外必填 code_challenge/code_challenge_method。channel 必须精确等于 client 登记渠道；major 只选择该渠道 App Center 的权威 Publication，不能覆盖 Version、回调或 scope。两者绑定到 code/token/family，后续资源请求、UserInfo 或 refresh 不接受改选。客户端每次新建至少 32 随机字节的 state、nonce；服务端接受 43–128 字符的 base64url 值，不把 nonce 当用户身份。PKCE verifier 为 RFC 7636 规定的 43–128 个 unreserved ASCII 字符；challenge 为 SHA-256 后无 padding 的 base64url，固定 43 字符。

Auth 在建立登录 interaction 前以 clientId、iwut_channel 和 iwut_rpc_api_major 调用 App 的 `ResolveClientRuntimeConfiguration`，从 exact-major 当前渠道 Publication 的批准 Version snapshot 取得 effective redirect URIs 和 scopes，并从当前已批准 ProfileRevision 取得展示资料，再先精确匹配 redirect_uri。runtime tuple 包含 versionId、publicationRevision、profileRevisionId 和 adminAuthId；用户登录后以该 tuple 调用 `ResolveAuthorizationContext`，确认和 code 兑换时继续重查。任何 tuple 变化都不能把旧回调或展示资料与新 scopes、Profile、Tester 或 Grey cohort 资格拼接。

Grant 业务主键为 `(authId, applicationId, channel)`，具体约束由 [BR-OAU-002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 定义。同应用同渠道的 PUBLIC/CONFIDENTIAL client 及各 major 共享历史同意；grantId 是稳定引用 ID，不以 client 或 Version 为授权身份。code、access/refresh token 和 family 仍各自绑定 client，不能跨 client 兑换、刷新或撤销；共享同意不省略各自的 client authentication/PKCE、当前版本资格或 offline_access 确认。历史同意集合 G 不因当前版本 scope 减少而删减；只有本次请求超出 G 的部分需要新增同意。实际访问使用 token、G、当前批准版本及 Auth 当前目录许可集合 C 的交集，UC014/016/018/019 定义唯一业务规则。revision 用于 OCC/审计，用户撤回递增共享 grant 的独立 revocationEpoch，对同应用同渠道所有 client 的旧凭据生效；新增同意不使旧 token 失效，也不自动扩大旧 token。授权交互和 code 始终绑定其创建时的精确 runtime tuple 与 redirect URI；旧 code 不能因 grant 可延续而兑换到新 Version 的回调。secret 轮换只影响之后的 confidential client authentication，不单独撤销 grant、access token 或 refresh family。

支持 `prompt=none|login|consent`（首版单值）、非负整数 max_age。申请 offline_access 必须 prompt=consent 并实际确认，缺失时返回 invalid_request，不静默授予离线访问。无 prompt 时可复用尚有效的平台登录与既有 grant；none 不允许显示 UI，缺登录/新权限分别返回 login_required/consent_required。login/max_age 要求重新走 UC007/012 的认证，不能靠刷新门户 cookie 伪造 auth_time。nonce 写入最终 ID Token，state 原样返回。重新认证不得复用进入 prompt=login 前的同一 Session；auth_time 取 Auth 记录的实际认证时间，不接受浏览器上报。

官方 Auth 登录/consent 门户是交付的一部分；下述 /portal 路径也相对 issuer，不是站点根目录。浏览器先走既有注册/登录能力，取得平台 Session 后，在同源 `POST /portal/session` 用 `x-iwut-session` 建立 `__Host-iwut-portal` cookie：值为原 Session，Secure、HttpOnly、Path=/、SameSite=Lax，寿命不长于 Session；Auth 仍逐次在线验证。该桥接只接受配置的官方 Origin、JSON 和自定义 header，禁止跨域 CORS。cookie 只在 Auth 专用主机使用，代理不能传给应用。

门户确认使用同源 `POST /portal/interactions/{interactionId}/confirm`，含绑定 Session/interaction 的服务端随机 CSRF token、用户选择的 optional scopes 与同意/拒绝决定。Auth 重新检查 Session 归属及 interaction；请求体不接受可覆盖的 authId/client/redirect/scope 定义。禁止第三方 iframe 嵌入（CSP frame-ancestors 'none'），页面 Referrer-Policy 为 no-referrer，不加载第三方统计脚本。交互标识本身不是用户授权凭据。

原生应用使用系统浏览器和已登记的 HTTPS app/universal link 回调；前端 verifier/state/nonce 只保存在发起端。首版不设计 custom scheme、loopback 回调或把原生平台 Session 放入浏览器 URL 的 SSO 桥。官方宿主已有 Session 的无感浏览器迁移另行交付；允许在门户重新认证。

成功通过 303 跳回精确登记的 redirect_uri，仅附加 code、state、iss；客户端核对 iss 与发起时保存的 issuer。错误只有在 client 与 redirect_uri 已通过校验后才允许回跳；恶意/未知回调留在 Auth 本地报错。回调登记禁止占用 code/state/iss/error 等响应参数。应用处理一次回调后清除 URL 中的 code，不在日志或 Referer 中传播。

#### 凭据与身份格式

授权码、access token、refresh token 分别由 CSPRNG 产生 32 字节，base64url 无 padding；用途隔离的 SHA-256 摘要建索引，原值只在成功响应中出现。Session、三类 OAuth 凭据即使形状相同也只能查各自的存储，禁止自动回退。数据库 TTL 清理不代替 expiresAt 检查。

| 对象 | 首版有效期 | 消费方 |
| --- | --- | --- |
| 授权交互 | 10 分钟 | 官方门户 |
| 授权码 | 90 秒，一次性 | token endpoint |
| access token | 15 分钟，仍逐次在线查授权 | UserInfo / Gateway |
| ID Token | 5 分钟 | 该 client 的登录处理 |
| refresh family | 30 天未成功刷新失效；自首次签发起最长 180 天 | token endpoint；滑动闲置期限＋固定绝对上限 |

上述天数按 24 小时计算。refresh 的滑动更新、到期边界和 access token 剩余寿命截断规则唯一由 [UC-AUTH-016 / BR-OAU-010](../use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-010) 定义；轮换改变 token 值，续期只移动闲置截止时间，不重置整条链的绝对上限。

ID Token 使用独立 OIDC RSA 签名密钥与 JWKS（RS256，RSA 至少 2048 bit）。header 为 `alg=RS256,typ=JWT,kid=<configured key>`；claims 为 iss、sub、单值 aud=client_id、iat、exp、auth_time、nonce、at_hash。at_hash 按 OIDC RS256 的 SHA-256 左半摘要规则，从实际 access token 计算。不包含平台 Session、内部 authId、学生关联值、developer/reviewer 权限或全量资料。

client 必须用预先信任 issuer 的 discovery/JWKS 验签，检查算法、iss、aud、exp、nonce、at_hash；ID Token 的时钟容差最多 30 秒，max_age 请求还须检查 auth_time；未知 kid 只允许对固定 JWKS 地址进行有界刷新，不访问 JWT 提供的 URL。ID Token 不作为 API Bearer token；取得后 client 可自行建立应用会话，其寿命由应用管理。OIDC 签名密钥退役前保留公钥至少覆盖已签 token 的有效期、容许时钟差和 JWKS 缓存期限。

pairwise sub 的业务所有权和持久化由 [BR-OAU-021](../use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021) 定义：一个 Application 一个稳定 sector，所有 channel/type/major/Version 共用。Auth 从 App 验证 clientId→applicationId 后创建映射；App 不保存 sector/sub，用户和开发者不能自选其他应用的 sector。同一 sector 下 PUBLIC/CONFIDENTIAL 的 sub 相同，但 ID Token 的 aud 仍分别为各自 clientId，不能跨 client 使用 ID Token 登录。

#### 标准 sector 注册与回调清单

Auth 配置专用稳定 HTTPS 域名后缀 `sectors.<platform-domain>`，为每个应用生成随机 UUID sectorId，并保存完整 URI，例如 `https://<sectorId>.sectors.example.org/redirect-uris.json`。**URI 的 hostname 才是标准 Sector Identifier**；不同 Application 必须不同 hostname，不能只靠同一 host 下不同路径实现隔离。所有该应用的 client 注册元数据使用同一个 sector_identifier_uri，按 `(authId, sectorId)` 的持久映射生成 sub。已分配的 host/URI 不随版本或环境密钥变化；需要稳定 DNS、TLS 和备份，不能临时重建。

这是服务端受控的静态注册，不要求公开动态 client 注册接口。sector_identifier_uri 为 Auth 生成的只读元数据，客户端不需要获取 sector 才能登录；App 只提供 applicationId/client 归属和 [GetApplicationPublishedRedirects](../../platform/contracts/app-oauth-client-v1.md#sector-的只读配置来源) 的批准回调事实，不保存或更新 sector。

标准 URI 仅 GET，成功直接返回 `application/json` 的字符串数组，不加 envelope。数组为该 Application 当前已启用渠道、已发布 major、两种 type 的批准回调去重排序并集；它是注册描述，不是实际授权回调白名单。每次 authorize/code 兑换仍只允许选中 client/channel/major 的精确回调，不允许因 URI 清单含有别的渠道就跨渠道跳转。

Auth 为运行配置准备/更新静态 OIDC 注册元数据时，确认本 client 生效的所有 redirect_uris 均包含在同一有效快照的 JSON 清单中；hostname 迁移或新增 major 回调时重新确认。App 仍是唯一配置权威，Auth 不维护可独立修改的回调副本。验证可直接消费生成 JSON 的同一受信快照，不要求 Auth 经公网请求自己；对外端点必须与该 JSON 语义一致。版本并发变化按 provider 的 entries/version 对照规则重读或失败关闭，不使用陈旧白名单。

清单公开仅包含回调 URI，不含 scopes、client secret、用户、学校关联或 token；URI 的 query 本就不得嵌入秘密。已分配 sector 暂无发布回调可返回空数组；未知 sector 404，App 故障或快照过期 503，不能返回旧值或假空数组。响应 no-store。清单读取不创建新 sector，不接受任意外部 URL，也不能用于 SSRF 代理。

跨域回调使用同一个稳定 sector URI，其清单只随批准发布事实更新，用户 sub 不变。认证套件用于验证此已明确的 sector/注册契约，不再把是否补 sector 元数据留作实现时决定。标准依据见 [OIDC Core §8.1](https://openid.net/specs/openid-connect-core-1_0.html#PairwiseAlg) 和 [Registration §5](https://openid.net/specs/openid-connect-registration-1_0.html#SectorIdentifierValidation)。

#### 错误、CORS 与限额

协议端点返回 OAuth/OIDC JSON error，不包装业务 envelope。无效 client 统一 invalid_client（Basic 失败 HTTP 401 并带 WWW-Authenticate）；失效 code/verifier/refresh 统一 invalid_grant（400）；非法参数 invalid_request，越界 scope invalid_scope。不要向攻击者区分 secret、用户、grant 是否存在。依赖故障返回 503 与 temporarily_unavailable，不当成用户拒绝或已撤销。

UserInfo 无效 token 返回 401 Bearer invalid_token；scope 不够返回 403 insufficient_scope。API 不返回登录 302。revocation 已失效/未知/不属于调用 client 的 token 统一 200；不支持的 token 类型用 unsupported_token_type。

PUBLIC token/UserInfo/revoke 的浏览器 CORS 只允许当前批准并发布 Version 中 PUBLIC_PKCE effective callbacks 对应的 HTTPS origin（无 cookie credentials），缺 Origin 的原生调用仍按协议认证；preflight 无 token 时仅根据当前 effective public origins 联集返回允许的方法/headers，实际请求仍按认证后的 client 再匹配 Origin；验证 preflight 不授予访问权限。CONFIDENTIAL token/revoke 不启用跨域浏览器访问。授权端点仅允许顶层导航，不提供跨域 fetch 登录。

请求体最大 16 KiB、scope 最多 32 项、单项最多 128 ASCII 字符；单值参数重复、未知 grant/response_type 均拒绝。默认每 IP 120 次/分钟、每 client 300 次/分钟、每登录用户 30 次授权确认/分钟，可部署调小；429 携 Retry-After。code、token、secret、verifier、cookie、签名上下文、邮件及用户资料不得进入访问日志、trace、metrics 标签或审计原文。

#### 交付依赖与验收

1. App 先扩展 UC-APP-002/003/004/005 的 Version 依附 oauthRedirects 创建、编辑、审核与策略，再由 UC-APP-018 提供 Application＋channel 级稳定 identity/credential，UC-APP-007/019 负责发布检查与运行资格快照。
2. Auth 实现 UC-AUTH-014/015/017/018/019，门户与 Gateway 同步交付；UC-AUTH-016 是独立离线授权工作包，未启用时 discovery 必须去掉 refresh_token，拒绝 offline_access，不能部分宣称支持。
3. 初版最小生产 scope 装载 `openid`、`email`、`offline_access`：Auth 维护稳定语义/用户可读说明/映射；App 版本仍须声明并通过原有审核。其他业务 scope 必须有已交付资源服务、scope→audience→route 映射；不接受开发 fixture。生产 Catalog 装载能力是实现依赖，不需要先做在线 Catalog 管理 UC。
4. Gateway OAUTH2、OIDC_HTTP 与资源服务委托验证通过真实三方联合测试后显式启用。当前 ACTIVE 契约继续有效，本文不使旧实现自动具备新能力。

验收至少覆盖两种 client、confidential+PKCE、code/refresh 重放、nonce/state 错配、同一 clientId 的 Version/hostname/major 回调切换与未登记回调、登录前后 runtime tuple 变化、scope 越权、跨 major 历史授权保留、渠道授权隔离、仅新增 scope 重新 consent、同应用所有渠道/type 的 sub 一致及不同应用隔离、secret 轮换不撤销 grant/既有 token、App 停用、UserInfo 最小披露、HTTP/原生 gRPC/gRPC-Web，以及依赖故障时不转发。启用前还需实际 OIDC 客户端库互通测试；未通过认证不得宣称通过 OpenID Certification。

#### 标准依据

[OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html) 定义认证结果、ID Token 校验与 pairwise sector；[OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html) 定义元数据。[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.1.1) 要求 public client 使用 PKCE，建议 confidential client 也使用；[RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html) 固定 verifier/challenge 编码。[RFC 9207](https://www.rfc-editor.org/rfc/rfc9207.html) 定义授权响应中的 issuer 标识。[RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)、[RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html) 分别约束 client 认证与撤销端点。本文的期限、权限集合和发布资格是 iWUT 的产品决定。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：目标与范围、认证与资格、API 与确认过程、主流程、首版运行与协议固定值、错误、限额与验收、实现依赖与联动、变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-015-exchange-authorization-code.md` | 81 | `cbaee4baf6fe` |
| `use-cases/UC-AUTH-025-close-own-account.md` | 155 | `6b6f375f1aad` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/auth-scope-catalog-v1.md` | 94 | `4c1bae67fbf9` |
| `platform/contracts/oauth-delegation-v1.md` | 97 | `1f431b468864` |
| `platform/contracts/oauth-oidc-v1.md` | 134 | `b08d5fc257b6` |
