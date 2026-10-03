<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-019 --spec tools/brief-specs/UC-APP-019.json -->
# Brief — UC-APP-019：为 Auth 解析 OAuth 应用授权上下文

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-019` 为 Auth 解析 OAuth 应用授权上下文 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAC-006`–`BR-OAC-011`（6 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-oauth-client-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

向 Auth 提供稳定 OAuth client 元数据、confidential secret 验证、用户登录前可验证的当前运行配置，以及特定用户的授权资格快照。Auth 不依赖客户端上报的 redirect URI、scope、Version 或批准状态；App Center 不签发用户 token。

### 输入与输出

五个精确内部方法、权限和字段见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。clientId 必填；运行解析还必须给出 channel 和 rpcApiMajor。authId 只来自受信 Auth 服务身份，不开放普通用户查询。

### 主流程

1. 使用 App Center 本地 caller registry 验证服务 JWS、固定 audience `iwut-app-center` 和方法级 permission；仅注册原生 gRPC，不生成 HTTP annotation。
2. `GetClientConfiguration` 返回稳定 identity 元数据，并为 CONFIDENTIAL 返回当前 credentialRevision；`VerifyClientSecret` 只比较调用方刚读取的 expectedCredentialRevision 与当前摘要。
3. `ResolveClientRuntimeConfiguration` 由 clientId 找到 Application 和 type，先核对请求 channel 等于登记 channel，再使用该 channel/rpcApiMajor 在单个 Mongo snapshot 中读取当前 Publication、APPROVED Version/Review 及依附 Version 的 OAuth 配置，从批准 snapshot 取得该 type 的 redirect URIs 与 scopes。该方法不需要 authId，供 Auth 在登录前校验 redirect URI。
4. `ResolveAuthorizationContext` 在相同运行配置检查基础上读取指定用户当前 ACTIVE Tester，并校验调用方传入的 expected runtime tuple。
5. 从当前已批准公开 ProfileRevision 返回最小展示资料，并把 profileRevisionId 纳入短时运行版本；任何缺失或不一致失败关闭。

### 验收场景

- 服务凭据逐方法授权；错误 audience、USER token 和公网访问拒绝。
- 同一渠道 clientId 可解析不同 exact-major Publication；跨渠道解析拒绝，major 不存在不回退。
- sector 回调查询跨已启用渠道/major 取得同一应用的批准并集，忽略 draft；App 输出无 sector/sub。
- 登录前可取得当前受审核回调并精确校验，不需要伪造 authId；非法回调不发生重定向。
- 当前 Tester 正常解析；移除后重加返回新 membershipId，旧资格不能恢复。
- TEST 槽切换、major 不同、跨应用 Version、批准 snapshot 不一致或对应 redirect 数组为空失败。
- 没有当前公开资料时运行解析失败；损坏的公开资料指针返回 INTERNAL，不回退 Application 技术名称。
- 登录前后 ProfileRevision 切换时 expected runtime tuple 不匹配，Auth 必须重新开始或重新展示。
- secret 轮换与 Verify 交错由 credentialRevision 拒绝混合，但不改变 RuntimeConfiguration tuple。
- 开发版客户端直开任意 URL 不产生可授权上下文，也不能替代已审核 TEST Publication。

### 依赖与实现边界

依赖 UC-APP-018、版本依附的 OAuth redirect 配置、版本审核/TEST 发布/Tester 与公开资料读取。STABLE/灰度公开运行资格尚无 UC，不阻碍本 TEST 纵切片设计。Auth Scope Catalog 的生产来源仍需实现。

## 业务规则（UC-APP-019 权威正文）

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-006 -->
### BR-OAC-006：内部查询与最小披露

只允许显式配置的 Auth service principal，并按共享契约分离读取、验证、运行配置解析和用户上下文解析权限。输入 channel 必须等于 client 固定渠道；rpcApiMajor 只能选择该渠道服务端权威 Publication，不能替换批准 redirect URI、scopes、Version 或 adminAuthId；输出不含 secret/摘要、学生资料或用户邮箱。

GetClientConfiguration 可以返回 DISABLED 元数据供 Auth 解释；VerifyClientSecret、ResolveClientRuntimeConfiguration 和 ResolveAuthorizationContext 对 DISABLED client 均不成功。

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-007 -->
### BR-OAC-007：TEST 资格与批准运行配置

首版 channel 只接受 `TEST`，并复用 UC-APP-012 的 exact-major TEST Publication；用户上下文还要求 ACTIVE Tester。必须存在 client 所属 applicationId 与请求 rpcApiMajor 对应的 testVersionId，Version 属于该应用且 APPROVED，并与批准 Review snapshot 完全一致；不可回退 draft、其他 major 或任意历史批准版本。

redirect URIs、requiredScopes 和 optionalScopes 都从该批准 snapshot 取得。PUBLIC client 选择 `pkceRedirectUris`，CONFIDENTIAL client 选择 `confidentialRedirectUris`；对应数组为空时运行配置不可用。Auth 再按 UC-AUTH-001/014 检查当前权威 Scope Catalog 的 enabled。Provider 保留批准 snapshot 的 scope 原值，不按 App 缓存的 requestable 裁剪返回集合，也不把快照当成运行启用证明；宿主 capabilities 的完整匹配仍由 UC-APP-012 执行。

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-008 -->
### BR-OAC-008：一致快照与资格版本

一次 provider 响应的 registration、Publication、Version、Review、当前公开 ProfileRevision、回调和 scopes 来自同一个 Mongo snapshot。`RuntimeConfiguration` 返回 `(registrationRevision, authorizationEpoch, versionId, publicationRevision, profileRevisionId, adminAuthId)`；用户授权上下文在此基础上增加 `testerMembershipId`。Auth 必须把运行 tuple 作为不可拆分值比较，不能拼接不同调用的字段。

credentialRevision 只用于一次 confidential secret 验证，不属于运行 tuple。secret 轮换不会使已建立的 grant、授权交互、code 或 token 仅因 revision 改变而失效。移除后重新加入的 Tester 必须产生新的 membership episode；发布、公开资料、管理员或 client 状态变化后不能用旧查询继续成功。App 不回调 Auth；当前 Developer 状态由 Auth 自己确认。

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-009 -->
### BR-OAC-009：展示来源与失败关闭

consent 展示只能读取 `currentPublishedProfileRevisionId` 指向的同一 Application、status=`APPROVED` 的 ApplicationProfileRevision。`ApplicationDisplay` 固定包含 profileRevisionId、displayName、可空 description 和可空 icon；不提供技术名称 fallback，不展示未经审核的 DRAFT，也不返回应用控制的 HTML。

未知 client、无 TEST 发布、没有当前公开资料、对应 redirect 数组为空、非 Tester、批准事实不一致或依赖故障均不能产生可授权上下文。没有公开资料属于运行资格未满足，返回统一 `FAILED_PRECONDITION`；指针存在但 Revision 缺失、跨 Application、不是 APPROVED 或内容损坏属于内部数据不变量异常，返回 `INTERNAL`。面向 Auth 的无资格原因使用共享错误分类，不返回空 scopes、技术名或前端值兜底。

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-010 -->
### BR-OAC-010：登录前回调校验与两阶段一致性

Auth 必须先调用 `ResolveClientRuntimeConfiguration`，并在发起登录或任何可能跳转到应用的响应前，对请求 redirect URI 做完整字符串精确匹配。未知或非法 redirect URI 只在 Auth 本地显示错误，绝不跳转。

用户登录后，Auth 使用预登录取得的 runtime tuple 调用 `ResolveAuthorizationContext`。App 必须在同一 snapshot 复查 tuple 和 ACTIVE Tester；Version、Publication、Profile、管理员或 registration 任一字段变化都返回前置条件失败。Auth 不得把旧 runtime 的 redirect URI、展示资料与新 Version 的 scopes 或 Tester 资格组合。授权确认和 code 兑换仍重新解析并绑定精确 Version/Publication/Profile；grant 的历史同意集合不因版本许可减少而删减；已签发 token 以原 channel/major 的当前资格和有效 scope 交集决定访问，Version ID 或 ProfileRevision ID 变化本身不是撤销理由。

<!-- 权威位置: use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-011 -->
### BR-OAC-011：Auth sector 的回调事实来源

GetApplicationPublishedRedirects 仅向授权 Auth 服务返回单个应用当前批准且已发布回调的快照并集，具体字段与快照比较见共享契约。App 不生成 sector、不保存用户 sub；同一应用所有渠道/type 可归入一个 sector，但查询成功不授予任何用户运行资格。清单不含草稿或未发布历史版本，故障不得用空清单伪装成功。

## 架构决定（仅本次需要的章节）

### ADR-006：Proto v1 与独立 API 仓库协作（`ACCEPTED`）

#### 决定

新协议在 API 仓库使用独立命名空间和目录：

```text
app_center/v1/...
package app_center.v1.<capability>
```

`v1` 只表示共享协议命名空间，不进入 App Center 的领域 package、collection 名或业务身份。Schema revision 由 migration ledger 中的 `0001`、`0002` 等迁移 ID 管理，collection 名保持无版本的业务命名。

Proto 源文件继续由独立 API 仓库拥有。App Center 服务仓库固定引用一个明确的 API repository revision；不得依赖浮动分支或在服务仓库手工维护生成代码的私有修改。

协作顺序为：

1. Domain 与 UseCase 通过自己的 Command/Result 类型稳定业务行为。
2. 在 API 仓库增加或修改 v1 Proto、error reason 和生成配置。
3. 生成代码并在 API 仓库通过检查后提交。
4. App Center 更新固定 revision。
5. Transport adapter 显式完成 Proto 与 UseCase 类型转换。
6. 两个仓库分别使用各自可审查的 commit。

Proto 不直接复用 Domain struct，也不把生成 message 传入 Domain。字段 presence、oneof、timestamp、enum unknown value 和 transport validation 在 adapter 边界处理。

#### 协议演进

即使系统尚未上线，已提交到共享 API 仓库的 v1 字段编号也保持稳定：

- 不重用删除字段的编号或名称，使用 `reserved`。
- enum 保留明确的 `UNSPECIFIED = 0`，业务上不接受时由 adapter 拒绝。
- 不把数据库内部字段、comparison key、技术计数器或 secret 暴露为公共字段。
- 写请求不接受可信身份、服务端状态和审计字段。
- 分页 cursor 是不透明 bytes/string，不承诺内部编码。
- Error reason 与 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 的稳定业务 code 对齐。

HTTP annotation 和 gRPC service 共享同一 Proto 语义。HTTP API 使用 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 定义的标准状态映射。

#### 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/app-oauth-client-v1.md`：App OAuth Client 提供方契约 v1

#### 所有权与调用方

App Center 持有 Application＋channel 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，协议见 [OAuth OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

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

它使用独立 collection 存储，但生命周期严格依附 ApplicationVersion：与 Version 同事务创建/编辑，使用同一个 Version revision 做 OCC，提交时深拷贝进 Review snapshot，提交后不可独立修改。两个数组均非 null、各 0–10 项、内部唯一且彼此不交叉。详细 URI 规则见 [BR-VER-018](../use-cases/UC-APP-002-create-application-version.md#br-ver-018)。

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

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和 testerMembershipId。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, profileRevisionId, adminAuthId)`；expectedRegistrationRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置、当前公开资料和 Tester 资格。

redirectUris 来自批准 snapshot：PUBLIC 读取 pkceRedirectUris，CONFIDENTIAL 读取 confidentialRedirectUris；对应数组必须非空。requiredScopes/optionalScopes 来自同一 snapshot，不按 App 的 requestable 缓存过滤；Auth 根据 [Scope Catalog 契约](../../platform/contracts/auth-scope-catalog-v1.md) 对应的当前权威 enabled 和 OAuth UC 执行最终授权。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记；channel 必须与 client 登记值完全相等，rpcApiMajor 只选择该渠道的权威 Publication；不能把 TEST client 当成 STABLE client。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。登录前后 registrationRevision 和 runtime tuple 必须一致；Profile 批准后当前公开指针发生变化也必须重新开始或重新展示。credentialRevision 只约束一次 secret 验证，不进入 runtime tuple。

Grant 按 [UC-AUTH-014 / BR-OAU-002](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 的 `(authId, applicationId, channel)` 业务主键保存，同应用同渠道的两类 client 及各 major 共享历史同意。App 提供可信的 client→applicationId/channel 归属，不管理 grant；Auth 不能从前端自报值推导共享范围。授权交互和 code 绑定精确 runtime tuple、redirect URI 和 scope；access/refresh 绑定不可变 channel/rpcApiMajor、authorizationEpoch、Tester episode。Version ID 只用于审计，后续在 token 原来的 major 上重新解析当前版本，不能由资源请求改选 major。Auth 保留历史同意集合，按当前有效交集决定权限；具体规则只由 UC-AUTH-014/016/018/019 定义。

#### Sector 的只读配置来源

Auth 唯一拥有 `applicationId → sector` 和 `(authId, sector) → sub`。App 的上述接口只提供可信 clientId/applicationId/channel/type 关系，不接受或返回客户端指定的 sector，不保有第二份 sector 映射。

`PublishedRedirectSnapshot` 包含 applicationId、entries、redirectUris、observedAt、validUntil。entries 按 `(channel,rpcApiMajor)` 排序，含 versionId/publicationRevision；redirectUris 是该应用当前已启用渠道、全部已发布 major 的批准 snapshot 中两类回调的去重排序并集。未发布 draft、历史已替换版本、没有对应 registration 的 type 不纳入；DISABLED client 不导致已有 sector 删除。无已发布回调时返回空集合；事实不一致或存储故障返回不可用，不伪造空成功。一次 snapshot 读完，期限同上；只读该应用，不能因它包含正式渠道就授予 TEST 用户正式权限。

Auth 用此快照提供标准 sector URI 的 JSON 清单。准备 OIDC 注册元数据时，对照同次 runtime 使用的 `(channel,major,versionId,publicationRevision)`；两份快照若不匹配就重新读取或失败关闭，不用跨版本拼接的清单完成注册验证。此查询不回调 Auth，不公开用户、secret、scope 或运行资格；标准清单的公开范围和协议见 OAuth/OIDC v1。

#### 资格变化与失败

client 不可用、对应回调数组为空、非 ACTIVE Tester、无 exact-major Publication、无当前已批准公开资料或批准记录不一致均不可授权。首版只支持 channel=`TEST`。正常缺少运行资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因；公开资料指针存在但目标缺失、跨应用、非 APPROVED 或内容损坏返回 `INTERNAL`。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照或 Application 技术名称兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。未来 STABLE/灰度发布必须先定义公开运行资格，再扩展 channel。

#### 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认和 code 兑换重新解析用户上下文。refresh、UserInfo 和每次委托签发按 OAuth/OIDC v1 的当前资格规则验证。confidential secret 只在 token/revoke 操作验证。

双方至少测试：每种 type 的 clientId 稳定；metadata 无 redirect/secret；一次 secret 返回；registration 与 credential revision 并发隔离；跨应用管理员；runtime tuple 混合；同 clientId 跨 Version/major 选择；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；公开资料切换和损坏指针；hostname 迁移；快照过期；服务 permission；Auth→App 故障时零签发。

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center`，App Center 为 `iwut-app-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### App Center 固定授权映射

App Center 首版只开放原生 gRPC 的 OAuth provider，不生成 HTTP annotation。完整方法与本地 caller registry permission 固定为：

| gRPC 方法 | 必需 permission |
| --- | --- |
| `OAuthClientProviderService/GetClientConfiguration` | `app.oauth.client.read` |
| `OAuthClientProviderService/VerifyClientSecret` | `app.oauth.client.verify` |
| `OAuthClientProviderService/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` |
| `OAuthClientProviderService/ResolveAuthorizationContext` | `app.oauth.context.resolve` |
| `OAuthClientProviderService/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` |

未知方法默认拒绝。普通 USER/SYSTEM trusted identity、第三方 access token、client secret 和网络位置都不能替代 Auth service identity。

#### ENV 配置

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_IDENTITY_ID` | `serviceId` |
| `APP_CENTER_SERVICE_IDENTITY_KID` | 当前签名 key ID |
| `APP_CENTER_SERVICE_IDENTITY_AUDIENCE` | 默认 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_PRIVATE_KEY_PEM_B64` | PKCS#1 或 PKCS#8 RSA private-key PEM 的 strict standard Base64 |
| `APP_CENTER_SERVICE_IDENTITY_TTL` | 正 Go duration；默认 `1m` |

Auth Center 必须提供 `AUTH_CENTER_SERVICE_CALLERS_B64`：以下 JSON UTF-8 bytes 的 strict standard Base64。

```json
{
  "iwut-app-center": {
    "status": "ACTIVE",
    "keys": {
      "app-center-2026-01": {
        "publicKeyPemB64": "<RSA public-key PEM 的 strict standard Base64>"
      }
    },
    "permissions": [
      "auth.scope-catalog.read",
      "auth.developer-status.read",
      "auth.system-principal.resolve"
    ],
    "systemPrincipalPurposes": [
      "app-center.review-auto-rejection"
    ]
  }
}
```

外层 Base64 只解决环境变量传输与转义，不提供保密性。部署必须用 secret 管理 App 私钥；不得把值提交到仓库、镜像、日志或诊断输出。Auth 公钥注册表不含私钥，可以由 config 或 secret 注入。缺失、未知字段、重复权限、非法 key、未知 permission/purpose 或空注册表必须阻止启动。

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_CALLERS_B64` | 与 Auth caller registry 相同的 strict Base64 JSON schema；首版登记 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` | 接受的最大 token TTL，默认 `1m` |
| `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW` | claims 时钟偏差，默认 `30s` |

App Center registry 中 `iwut-auth-center` 只允许上述五个 `app.oauth.*` permission，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

#### 契约测试要求

至少验证合法调用、缺失/错误签名、未知 serviceId、未知 kid、错误 audience、过长 TTL、disabled caller、缺少 RPC permission 和未允许 purpose。生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor，不能只验证同接口 fake server。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-019`（use-cases/UC-APP-019-resolve-oauth-authorization-context.md）：变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-oauth-client-v1.md`（docs 根级共享文档）：管理接口
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：Auth Center 固定授权映射

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-019-resolve-oauth-authorization-context.md` | 88 | `45eb46f1ff39` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-oauth-client-v1.md` | 88 | `bb275737b743` |
| `platform/contracts/trusted-service-identity-v1.md` | 112 | `696ad25845e5` |
