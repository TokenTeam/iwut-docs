<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-018 --spec tools/brief-specs/UC-APP-018.json -->
# Brief — UC-APP-018：管理应用 OAuth Client

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-018` 管理应用 OAuth Client |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAC-001`–`BR-OAC-005`（5 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/app-oauth-client-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

Application 当前管理员为应用登记长期稳定的 OAuth client identity，查询元数据、轮换 confidential secret、禁用或重新启用 client。client identity 与 Application 同寿命，固定归属一个发布 channel，不随 ApplicationVersion 或 RPC API major 变化；redirect URI 与 scopes 属于受审核的 ApplicationVersion。

App Center 不签发用户 token、不保存 consent，也不把 launchUrl 推断成 redirect URI。

### 输入与输出

管理方法、字段、secret 编码与返回约定见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。所有命令使用既有可信 USER 身份，领域层从身份取得操作者，不接收请求体 adminId/developerHandle 覆盖。

### 主流程

登记 client identity：

1. 校验操作者为当前 Application 管理员，当前 Developer 为 `APPROVED`。
2. 校验 channel/type，并读取该 `(applicationId, channel)` 的 `ApplicationOAuthRegistration`；记录不存在时要求 expectedRegistrationRevision 为空，记录已存在时要求它等于当前 revision。
3. 若该 type 已有 clientId，返回已存在错误；否则分配全局唯一 clientId。CONFIDENTIAL 同时生成高熵 secret。
4. 在同一事务中通过 Application 管理员写栅栏复查归属，首次建立 registration 时写 revision=1，否则写入对应 type 的 clientId、`ACTIVE` 状态并递增 registrationRevision；CONFIDENTIAL 同时写入独立 `OAuthClientCredential` 的摘要与 credentialRevision=1。
5. 仅在确定提交后返回元数据；confidential secret 只在本次成功响应出现。

状态变更：

1. 校验当前管理员、Developer 门禁和 expectedRegistrationRevision。
2. 状态只接受 `ACTIVE` 或 `DISABLED`；相同状态为 no-op。
3. 在同一事务中复查管理员栅栏，更新 type 对应状态、递增 registrationRevision 并写审计。

secret 轮换：

1. 校验当前管理员、Developer 门禁、clientId 属于该 Application 的 CONFIDENTIAL identity，以及 expectedCredentialRevision。
2. 生成新 secret，在同一事务中复查管理员栅栏，替换摘要、递增 credentialRevision 并写审计。
3. 仅在确定提交后披露一次新 secret。该操作不修改 registrationRevision。

### 验收场景

- 普通用户、其他应用管理员和已转让的旧管理员拒绝；并发转让与登记/轮换不能越权。
- 同一 Application 每渠道每种 type 至多一个稳定 clientId；Version、major 或 hostname 变化不更换 identity，TEST/GREY/STABLE 的 clientId 和 credential 分别隔离。
- PUBLIC 没有 secret；CONFIDENTIAL secret 只返回一次，读取永远不含明文或摘要。
- registration CAS/no-op 与 credential CAS 相互独立；secret 轮换不改变 registrationRevision、grant 或已签发 token。
- client 可以在没有 Version、Review 或 Publication 时登记；运行解析仍必须满足 UC-APP-019 的完整资格。
- 与非空 OAuth 配置的发布并发时，registration 先提交则发布可成功；发布先观察到缺失则失败并允许重试。登记过程不读取或锁定 Publication/Version/hostname。
- 禁用后重新启用保持 clientId 不变，旧 clientId 永不重新分配。

### 依赖与实现边界

依赖既有 Application/Developer 可信身份、Mongo 事务和管理员写入栅栏。版本化 redirect 由 UC-APP-002 至 UC-APP-005 管理，UC-APP-007 发布，UC-APP-019 组合为 Auth 运行上下文。Proto/HTTP 路由仍需独立 API 工作包。

本用例的 registration/credential 可以在 Version OAuth 扩展之前独立交付。当前实现只开放管理员管理接口；Auth 专用读取、secret 验证和运行上下文解析属于 UC-APP-019，不因本用例保存了摘要就提前开放。

### API 实现契约

独立 API 仓库 package 为 `app_center.v1.oauth_client`，service 为 `OAuthClientService`。UC-APP-020/021 完成后接受 `TEST/GREY/STABLE`。

稳定 enum：

```text
OAuthChannel: UNSPECIFIED=0, TEST=1, GREY=2, STABLE=3
OAuthClientType: UNSPECIFIED=0, PUBLIC_PKCE=1, CONFIDENTIAL_SECRET=2
OAuthClientStatus: UNSPECIFIED=0, ACTIVE=1, DISABLED=2
```

`clientId` 是服务端生成的小写 UUIDv4 字符串。它是公开、不透明、区分大小写的 OAuth client identifier；输入只接受规范小写 UUIDv4，永久不重用。registrationRevision、credentialRevision 和 authorizationEpoch 均为正 int64；所有增加操作在溢出时失败并完整回滚。

管理 RPC 与内部 HTTP annotation：

| RPC | HTTP | 请求正文 |
| --- | --- | --- |
| `RegisterOAuthClient` | `POST /v1/applications/{application_id}/oauth-registrations/{channel}/clients` | `command`：type、optional expectedRegistrationRevision |
| `GetApplicationOAuthRegistration` | `GET /v1/applications/{application_id}/oauth-registrations/{channel}` | 无 |
| `SetOAuthClientStatus` | `PUT /v1/oauth-clients/{client_id}/status` | `command`：expectedRegistrationRevision、status |
| `GetOAuthClientCredentialMetadata` | `GET /v1/oauth-clients/{client_id}/credential` | 无 |
| `RotateOAuthClientSecret` | `POST /v1/oauth-clients/{client_id}/credential-rotations` | `command`：expectedCredentialRevision |

`expectedRegistrationRevision` 在首次创建 registration 时必须省略；已有 registration 补登记另一 type 时必须存在且匹配。SetStatus 的 expectedRegistrationRevision 和 Rotate 的 expectedCredentialRevision 必须存在且为正数；相同状态也先校验 expected revision，再返回 no-op，revision、epoch、审计时间均不改变。

`OAuthClientIdentityResource` 返回 clientId/type/status/authorizationEpoch/createdBy/createdAt/statusUpdatedBy/statusUpdatedAt。`ApplicationOAuthRegistrationResource` 返回 applicationId/channel、两个 optional identity slot、registrationRevision/createdAt/updatedAt。`OAuthClientCredentialMetadata` 只返回 clientId/credentialRevision/rotatedBy/rotatedAt，不返回摘要。CONFIDENTIAL 登记和轮换响应额外返回一次性 `clientSecret`；PUBLIC 响应不存在该字段。所有管理响应使用 `Cache-Control: no-store`，日志、错误、trace 和 metrics 不记录 secret、摘要或完整请求体。

错误 reason 至少固定为：`INVALID_APPLICATION_ID`、`INVALID_OAUTH_CHANNEL`、`OAUTH_CHANNEL_NOT_ENABLED`、`INVALID_OAUTH_CLIENT_TYPE`、`INVALID_OAUTH_CLIENT_ID`、`INVALID_OAUTH_CLIENT_STATUS`、`INVALID_OAUTH_REGISTRATION_REVISION`、`INVALID_OAUTH_CREDENTIAL_REVISION`、`APPLICATION_NOT_FOUND`、`APPLICATION_ADMIN_REQUIRED`、`OAUTH_REGISTRATION_NOT_FOUND`、`OAUTH_CLIENT_ALREADY_EXISTS`、`OAUTH_CLIENT_NOT_FOUND`、`OAUTH_REGISTRATION_CHANGED`、`OAUTH_CLIENT_CREDENTIAL_NOT_FOUND`、`OAUTH_CLIENT_CREDENTIAL_CHANGED`、`OAUTH_CLIENT_STATE_INCONSISTENT` 和 `INTERNAL`，并复用既有 Developer 身份/批准 reason。非法输入映射 INVALID_ARGUMENT；未找到映射 NOT_FOUND；重复登记映射 ALREADY_EXISTS；revision 竞争映射 ABORTED；渠道未启用映射 FAILED_PRECONDITION；越权映射 PERMISSION_DENIED；存储不变量异常映射 INTERNAL。

Mongo migration 建立 `application_oauth_registrations` 与 `oauth_client_credentials`。前者以 `(applicationId,channel)` 唯一，两个非空 clientId 分别具有全局唯一 sparse/partial 索引；后者以 clientId 唯一。validator 固定 slot、状态、正 revision/epoch、UTC 审计与 32-byte digest。CONFIDENTIAL 首次登记必须在同一事务同时创建 registration slot、credential 和审计；任何一步失败都不提交 identity。管理员归属通过 Application `coordinationRevision` 真写栅栏在最终事务复查。

完整验收使用 `make check-auth-app`：覆盖 Domain/UseCase、Proto 生成物、HTTP/gRPC、真实 Mongo validators/indexes/事务/回滚、管理员转让竞争、双 type 并发登记、registration/credential OCC 隔离、secret 一次披露与日志脱敏。Auth 回归只证明既有身份链路未回退，不表示 UC-APP-019 provider 已实现。

## 业务规则（UC-APP-018 权威正文）

<!-- 权威位置: use-cases/UC-APP-018-manage-oauth-client.md#br-oac-001 -->
### BR-OAC-001：应用归属与稳定接入身份

只有当前 Application 管理员且符合 Developer 门禁者可管理 client。每个 Application 每渠道至多拥有一个 PUBLIC clientId 和一个 CONFIDENTIAL clientId；二者均由服务端生成、全局唯一、永久不重用。

clientId 与 Application 同寿命，固定归属一个 channel，不包含 rpcApiMajor、Version 或 hostname。Version 升级、redirect URI 调整、发布槽切换、应用改名、管理员转让和 Developer 公开 ID 变化都不重建 clientId。创建 client 不代表用户已经 consent，也不扩大 Version 已审核的 scopes。

<!-- 权威位置: use-cases/UC-APP-018-manage-oauth-client.md#br-oac-002 -->
### BR-OAC-002：Registration 与 Version 配置分离

`ApplicationOAuthRegistration` 以 `(applicationId, channel)` 为唯一身份，保存两种可选 client identity 的 clientId、状态和 registrationRevision。`ApplicationVersionOAuthConfig` 依附于 Version，保存该 Version 的 `pkceRedirectUris` 与 `confidentialRedirectUris`，不复制到 registration。

channel 在登记后不可变。TEST 已由本用例首批交付，[UC-APP-020 / BR-OAC-012](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-oac-012) 启用 STABLE，[UC-APP-021 / BR-OAC-013](../use-cases/UC-APP-021-manage-grey-rollout.md#br-oac-013) 启用 GREY；三个渠道不能彼此代用。client identity 可以在首个 Version 或 Publication 之前创建；创建时不读取发布槽、redirect URI 或 scopes。hostname 迁移通过新 Version 的受审核 redirect 配置完成，不创建新 clientId，也不修改 registration。运行时由 UC-APP-019 及其后续渠道规则使用调用方明确给出的 channel 和 rpcApiMajor 选择当前 Publication。

<!-- 权威位置: use-cases/UC-APP-018-manage-oauth-client.md#br-oac-003 -->
### BR-OAC-003：高熵 secret 与一次披露

PUBLIC 不产生或保存 secret；CONFIDENTIAL 由 App 服务端生成，只在独立 `OAuthClientCredential` 中保存摘要。具体随机性、摘要域隔离和验证接口见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。不允许用户设置弱 secret，不提供读取旧 secret/摘要接口，不向浏览器包、移动安装包或宿主子应用注入 confidential secret。

轮换只保留一个当前 secret，旧 secret 立即不再通过后续认证。轮换不改变 clientId、registrationRevision、既有 grant、已签发 access token 或已签发 refresh family；它只改变以后 token/revoke 请求的 confidential client authentication。丢失响应时先查询 credential 元数据，再发起新轮换。

<!-- 权威位置: use-cases/UC-APP-018-manage-oauth-client.md#br-oac-004 -->
### BR-OAC-004：分离的并发版本与原子管理

登记 identity、禁用和重新启用由 registrationRevision 执行 OCC；secret 轮换由 credentialRevision 独立执行 OCC。相同状态请求为 no-op，不增加 revision。redirect URI 或 scope 随 Version/Publication 变化，由 versionId/publicationRevision 表达，不增加这两个 revision。

registration 修改、credential 修改与当前管理员/Developer 门禁按现有 App 命令一致性策略确认，事务包含配置和审计；并发登记由 `(applicationId, channel)` 和 clientId 唯一约束收敛。状态停用保留记录，不释放 clientId；重新启用同一 identity，不恢复或替换 secret。每个 slot 另存 authorizationEpoch（初始 1），每次实际禁用或重新启用递增；登记另一 type、secret 轮换和 Version 变化不改变该 slot 的 epoch。token/family 绑定它，防止禁用后重新启用复活旧凭据，也避免另一 type 的登记使已有 token 失效。

<!-- 权威位置: use-cases/UC-APP-018-manage-oauth-client.md#br-oac-005 -->
### BR-OAC-005：scope 与授权所有权

sector、sector_identifier_uri 和用户 sub 均由 Auth 管理，App 不保存副本；两个渠道或两种 type 的 clientId 不同不代表它们的 sector 不同。Registration 和 Credential 都不保存可由管理员自由编辑的 scope 白名单。当前批准 Version 声明的 requiredScopes/optionalScopes 由版本审核和发布规则决定，UC-APP-019 对 Auth 提供；scope 语义、consent、code、grant 和 token 归 Auth。

管理查询只返回当前管理员所需元数据；审计记录操作、ID/revision 和状态变化，不记录 secret。API 访问日志、HTTP 缓存和 trace 同样不能保留秘密。

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

### `platform/contracts/app-center-api-routing.md`：App Center API 路由 v1 契约

#### 路由映射

App Center 的每个 HTTP 资源在 Proto 内部使用的路径**不含服务前缀**。Gateway 为外部请求增加且只增加一个服务前缀 `/app-center`。

首个正式资源 CreateApplication 的映射是：

| 层 | 方法与路径 | 说明 |
| --- | --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications` | 客户端唯一可见的地址；`app-center` 是服务前缀 |
| Gateway | 剥离前缀 `/app-center` | 只做前缀剥离，不重写其余路径 |
| 内部（Gateway → App Center） | `POST /v1/applications` | Proto `google.api.http` annotation 声明的路径；请求体 `body: "*"` |
| gRPC | `/app_center.v1.application.Application/CreateApplication` | proto package `app_center.v1.application`，service `Application`，rpc `CreateApplication` |

UC-APP-005 审核决定命令遵循同一映射规则：

| 层 | 方法与路径 |
| --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| Gateway | 只剥离前缀 `/app-center` |
| 内部（Gateway → App Center） | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| gRPC | `/app_center.v1.application_review.ApplicationReview/DecideApplicationVersionReview` |

规则：

- Gateway 必须按**服务名到前缀**的映射表工作，不得把 `/app-center` 硬编码进业务路径，也不得同时改写内部资源路径。
- 前缀剥离后必须保留查询串与请求体。
- 内部路径与 gRPC full method 由 Proto 定义，App Center 的 HTTP 路由注册必须与 Proto annotation 一致；两者不得各写一份。
- 写请求只通过请求体传递资源字段；可信身份只通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 定义的 `x-iwut-identity` 传递，路径或 query 不承载身份。
- 未匹配的服务前缀或缺少前缀的外部请求由 Gateway 拒绝，不转发给 App Center。

#### gRPC-Web 终止

- gRPC-Web 在 **Traefik** 终止，不进入 App Center 进程。
- App Center 后端只暴露**原生 gRPC**；不嵌入 `grpc-web` wrapper，也不注册 gRPC-Web 专用的 HTTP handler。
- 浏览器流量由 Traefik 完成 gRPC-Web ⇄ gRPC 转换后，以原生 gRPC 到达 App Center；身份键仍为 metadata `x-iwut-identity`。
- 因此 App Center 不为 gRPC-Web 增加 CORS、content-type 或协议转换配置；这些属于 Traefik。

#### 契约测试要求

外部到内部的映射必须由**自动化契约测试**机械验证，不能只靠文档。测试至少断言：

1. Proto HTTP annotation 的内部路径等于 `POST /v1/applications`。
2. 外部路径等于服务前缀 `/app-center` 加内部路径，即 `POST /app-center/v1/applications`。
3. 前缀映射只剥离 `/app-center`，得到的内部路径与第 1 项一致。
4. gRPC full method 等于 `/app_center.v1.application.Application/CreateApplication`。
5. 写请求 message 只包含 `name`，不包含身份字段（`authId`、`developer_status`）、服务端字段（`id`、`adminId`、`createdAt`）或持久化技术字段。
6. 响应 message 不包含 `nameKey`、`nextVersionSequence`、`nextProfileRevisionSequence` 或其它内部技术字段。
7. 审核决定的外部/内部路径与上述 UC-APP-005 映射精确一致，gRPC full method 使用同一生成 service。
8. UC-APP-005 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

外部路径可以作为 contract constant / fixture 存在于测试中，但它必须与内部路径、前缀和 gRPC method 在同一测试里被自动验证，任何一侧漂移都必须让测试失败。

### `platform/contracts/app-oauth-client-v1.md`：App OAuth Client 提供方契约 v1

#### 所有权与调用方

App Center 持有 Application＋channel 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，STABLE/GREY 渠道扩展分别见 [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 与 [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md)，协议见 [OAuth OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

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

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-018`（use-cases/UC-APP-018-manage-oauth-client.md）：变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/app-oauth-client-v1.md`（docs 根级共享文档）：Auth 专用接口、Sector 的只读配置来源、资格变化与失败、STABLE 扩展、GREY 扩展、消费点与契约验收
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-018-manage-oauth-client.md` | 131 | `038010878b34` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
