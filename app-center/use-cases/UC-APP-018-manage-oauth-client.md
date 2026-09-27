# UC-APP-018：管理应用 OAuth Client

状态：`PROPOSED`

## 目标与范围

Application 当前管理员为应用登记长期稳定的 OAuth client identity，查询元数据、轮换 confidential secret、禁用或重新启用 client。client identity 与 Application 同寿命，不随 ApplicationVersion、发布 channel 或 RPC API major 变化；redirect URI 与 scopes 属于受审核的 ApplicationVersion。

App Center 不签发用户 token、不保存 consent，也不把 launchUrl 推断成 redirect URI。

## 输入与输出

管理方法、字段、secret 编码与返回约定见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。所有命令使用既有可信 USER 身份，领域层从身份取得操作者，不接收请求体 adminId/developerHandle 覆盖。

## 主流程

登记 client identity：

1. 校验操作者为当前 Application 管理员，当前 Developer 为 `APPROVED`。
2. 校验 type，并读取 Application 的 `ApplicationOAuthRegistration`；记录不存在时要求 expectedRegistrationRevision 为空，记录已存在时要求它等于当前 revision。
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

## 业务规则

<a id="br-oac-001"></a>
### BR-OAC-001：应用归属与稳定接入身份

只有当前 Application 管理员且符合 Developer 门禁者可管理 client。每个 Application 至多拥有一个 PUBLIC clientId 和一个 CONFIDENTIAL clientId；二者均由服务端生成、全局唯一、永久不重用。

clientId 与 Application 同寿命，不包含 channel、rpcApiMajor、Version 或 hostname。Version 升级、redirect URI 调整、发布槽切换、应用改名、管理员转让和 Developer 公开 ID 变化都不重建 clientId。创建 client 不代表用户已经 consent，也不扩大 Version 已审核的 scopes。

<a id="br-oac-002"></a>
### BR-OAC-002：Registration 与 Version 配置分离

`ApplicationOAuthRegistration` 以 applicationId 为唯一身份，保存两种可选 client identity 的 clientId、状态和 registrationRevision。`ApplicationVersionOAuthConfig` 依附于 Version，保存该 Version 的 `pkceRedirectUris` 与 `confidentialRedirectUris`，不复制到 registration。

client identity 可以在首个 Version 或 Publication 之前创建；创建时不读取发布槽、redirect URI 或 scopes。hostname 迁移通过新 Version 的受审核 redirect 配置完成，不创建新 clientId，也不修改 registration。运行时由 UC-APP-019 使用调用方明确给出的 channel 和 rpcApiMajor 选择当前 Publication。

<a id="br-oac-003"></a>
### BR-OAC-003：高熵 secret 与一次披露

PUBLIC 不产生或保存 secret；CONFIDENTIAL 由 App 服务端生成，只在独立 `OAuthClientCredential` 中保存摘要。具体随机性、摘要域隔离和验证接口见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。不允许用户设置弱 secret，不提供读取旧 secret/摘要接口，不向浏览器包、移动安装包或宿主子应用注入 confidential secret。

轮换只保留一个当前 secret，旧 secret 立即不再通过后续认证。轮换不改变 clientId、registrationRevision、既有 grant、已签发 access token 或已签发 refresh family；它只改变以后 token/revoke 请求的 confidential client authentication。丢失响应时先查询 credential 元数据，再发起新轮换。

<a id="br-oac-004"></a>
### BR-OAC-004：分离的并发版本与原子管理

登记 identity、禁用和重新启用由 registrationRevision 执行 OCC；secret 轮换由 credentialRevision 独立执行 OCC。相同状态请求为 no-op，不增加 revision。redirect URI 或 scope 随 Version/Publication 变化，由 versionId/publicationRevision 表达，不增加这两个 revision。

registration 修改、credential 修改与当前管理员/Developer 门禁按现有 App 命令一致性策略确认，事务包含配置和审计；并发登记由 applicationId 和 clientId 唯一约束收敛。状态停用保留记录，不释放 clientId；重新启用同一 identity，不恢复或替换 secret。

<a id="br-oac-005"></a>
### BR-OAC-005：scope 与授权所有权

Registration 和 Credential 都不保存可由管理员自由编辑的 scope 白名单。当前批准 Version 声明的 requiredScopes/optionalScopes 由版本审核和发布规则决定，UC-APP-019 对 Auth 提供；scope 语义、consent、code、grant 和 token 归 Auth。

管理查询只返回当前管理员所需元数据；审计记录操作、ID/revision 和状态变化，不记录 secret。API 访问日志、HTTP 缓存和 trace 同样不能保留秘密。

## 验收场景

- 普通用户、其他应用管理员和已转让的旧管理员拒绝；并发转让与登记/轮换不能越权。
- 同一 Application 每种 type 至多一个稳定 clientId；Version、major、channel 或 hostname 变化均不产生第二个同 type identity。
- PUBLIC 没有 secret；CONFIDENTIAL secret 只返回一次，读取永远不含明文或摘要。
- registration CAS/no-op 与 credential CAS 相互独立；secret 轮换不改变 registrationRevision、grant 或已签发 token。
- client 可以在没有 Version、Review 或 Publication 时登记；运行解析仍必须满足 UC-APP-019 的完整资格。
- 禁用后重新启用保持 clientId 不变，旧 clientId 永不重新分配。

## 依赖与实现边界

依赖既有 Application/Developer 可信身份、Mongo 事务和管理员写入栅栏。版本化 redirect 由 UC-APP-002 至 UC-APP-005 管理，UC-APP-007 发布，UC-APP-019 组合为 Auth 运行上下文。Proto/HTTP 路由仍需独立 API 工作包。

## 变更记录

- 2026-09-27：建立 OAuth client 管理设计。
- 2026-09-27：redirect URI 改由 ApplicationVersion 保存、审核和发布。
- 2026-09-27：client identity 改为 Application 级稳定 registration；secret credential 与 Version 配置使用独立生命周期和 revision。
