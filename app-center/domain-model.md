# App Center Domain Model

状态：`PROPOSED`

## 文档目的

本文把 [Capability Map](capability-map.md) 中的能力映射为聚合、实体、值对象和领域服务。它只描述业务模型与关系，不规定 HTTP、数据库、缓存、消息系统或 Go package。

本文是设计检查点，不替代现有 UC 中的 `BR-*` 权威正文。这里提出的聚合边界需要在后续命令 UC 和测试中验证；“属于同一聚合”也不表示数据需要嵌入同一个存储文档。

## 模型总览

```text
AuthId ─────────────────────────────────────────────────────────┐
                                                                │
DeveloperApplicationQuota                                      │
  └─ constrains                                                 │
       Application (aggregate root) ◄───────────────────────────┘
         ├─ 0..* ApplicationAdminTransfer (aggregate root)
         ├─ 0..1 ApplicationClosure (aggregate root)
         ├─ 1 ApplicationProfile (aggregate root)
         │     ├─ 0..* ApplicationProfileRevision
         │     └─ 0..1 currentPublishedProfileRevisionId
         ├─ 0..* ApplicationProfileReview (aggregate root, references ProfileRevision)
         ├─ 0..* ApplicationVersion (aggregate root)
         │     └─ 1 ApplicationVersionOAuthConfig (dependent entity/value)
         ├─ 0..* ApplicationReview (aggregate root, references Version)
         ├─ 0..1 ApplicationOAuthRegistration (aggregate root)
         │     ├─ 0..1 PUBLIC client identity
         │     ├─ 0..1 CONFIDENTIAL client identity
         │     └─ 0..1 OAuthClientCredential (separate revision)
         ├─ 0..* ApplicationPublication (aggregate root, one per RPC major)
         │     └─ 0..* ApplicationPublicationHistory
         ├─ 0..1 ApplicationFilter (aggregate root)
         │     └─ 0..* ApplicationFilterRevision
         └─ 1 ApplicationTesterAccess (aggregate root)
               ├─ 0..* ApplicationTesterJoinLink
               └─ 0..* ApplicationTesterMembership episode

CatalogResolver (domain/query service)
  reads Application + published profile + Publication + Version + TesterAccess
  returns candidate application + resolved launch target + Filter rule
```

所有下级对象都通过 `applicationId` 归属于同一个 Application，但 Application 不因此成为保存整个应用平台状态的巨大聚合。

## 聚合

### Application

Application 是稳定业务身份和当前管理权的聚合根。业务字段为 `id`、`name`、`adminId`、`createdAt`；[UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md) 增加只服务管理权 OCC 的正数 `ownershipRevision`；[UC-APP-027](use-cases/UC-APP-027-close-application.md) 提出 `lifecycleStatus` 和 `lifecycleRevision`。公开资料不属于它，依据 [BR-APP-004](use-cases/UC-APP-001-create-application.md#br-app-004) 由独立资料模型表达。

Application 提供其他聚合共同引用的 `applicationId` 和当前 `adminId`。版本序号与资料序号的分配器属于创建协调所需状态，不增加 Application 的公开业务含义。

管理员转让只改变 adminId 并增加 ownershipRevision；申请过程由独立 ApplicationAdminTransfer 保存。关闭只推进 Application 生命周期；过程、Auth 回执与收敛状态由独立 ApplicationClosure 保存。它们都不会把 Version、Profile、Publication 或 Tester 实体搬入 Application。

### ApplicationAdminTransfer

ApplicationAdminTransfer 是一次管理权转让过程的聚合根，保存 applicationId、fromAdminId、toAdminId、sourceOwnershipRevision、PENDING/终态和审计时间。它与 Application 分开，使拒绝、取消、过期及多次历史申请不会污染当前管理权结果。

每个 Application 同时最多一个 PENDING 申请。目标显式接受时，应用服务在同一本地事务内协调 Transfer、Application、双方 DeveloperApplicationQuota、可选 OAuthClientCredential 和当前 TesterJoinLink；具体生命周期与原子边界以 [BR-APP-013](use-cases/UC-APP-026-transfer-application-administration.md#br-app-013)、[BR-APP-016](use-cases/UC-APP-026-transfer-application-administration.md#br-app-016) 和 [BR-APP-018](use-cases/UC-APP-026-transfer-application-administration.md#br-app-018) 为准。

### ApplicationClosure

ApplicationClosure 是一个 Application 唯一且不可逆的关闭过程，保存 source ownership/lifecycle revision、发起者、绑定的 high-risk proof jti、`CLOSING/CLOSED`、Auth 撤销回执和时间。它与 Application 分开，使持久重试元数据和跨服务回执不会污染稳定身份，同时以 applicationId 唯一约束保证关闭不能重建或取消。

进入 CLOSING 的本地事务协调 Application、管理员配额、PENDING ApplicationAdminTransfer、ACTIVE TesterJoinLink 和现有 OAuth client slot；Version/Profile/Review/Publication/Filter/Membership 保留原样。App 本地 gate 立即生效，Auth application tombstone 经持久协议异步收敛；权威边界见 [UC-APP-027](use-cases/UC-APP-027-close-application.md) 和 [Application Closure v1](../platform/contracts/application-closure-v1.md)。

### DeveloperApplicationQuota

DeveloperApplicationQuota 以 `adminId` 为身份，表达一个 Developer 当前可拥有的 Application 数量上限和占用量。它独立于单个 Application，因为约束跨越同一管理员的全部 Application。

DeveloperApplicationQuota 自身的 `limit` 与 `usedCount` 是配额的唯一权威状态。缺少该聚合时，创建 Application 使用进程组装时注入的初始上限惰性建立它；该配置默认 10。已存在配额的 `limit` 不得被启动配置或创建路径覆盖，只能由未来的独立配额调整用例修改。具体配置契约、持久化形状由对应 UC 和 adapter 定义。

创建 Application 时的名称占用、配额消费和 Application 创建具有一个业务一致性要求，权威规则见 [BR-APP-005](use-cases/UC-APP-001-create-application.md#br-app-005) 与 [BR-APP-006](use-cases/UC-APP-001-create-application.md#br-app-006)。管理员转让把一个占用从源配额原子移动到目标配额；目标容量不足或同名时拒绝，见 [BR-APP-016](use-cases/UC-APP-026-transfer-application-administration.md#br-app-016)。不可逆关闭在进入 CLOSING 时释放一个配额占用但永久保留原命名空间技术名称，见 [BR-APP-025](use-cases/UC-APP-027-close-application.md#br-app-025)；未来归档是否释放配额仍需独立定义。

### ApplicationVersion

每个 ApplicationVersion 是独立聚合根，负责一份运行声明及其审核生命周期：

```text
ApplicationVersion
  identity: versionId + applicationId + sequence
  content: versionLabel + launchUrl + RpcApiRange + CapabilitySet + ScopeRequest + OAuthRedirectConfiguration
  lifecycle: reviewStatus + revision + audit
```

`ApplicationVersionOAuthConfig` 以 versionId 一对一依附 Version，保存 pkceRedirectUris 与 confidentialRedirectUris。它可以物理拆表，但与 Version 同事务创建/编辑、共用 Version revision、提交后不能独立修改；ApplicationReview snapshot 深拷贝其内容。

ApplicationReview 不放在 ApplicationVersion 聚合内部；二者通过 versionId、attempt 和 sourceVersionRevision 建立关系。Version 聚合保存自己的内容、依附 OAuth 配置、reviewStatus、revision 与审计事实。

ApplicationPublication 只引用 Version，不属于该聚合；发布槽位变化也不改变 Version 的审核状态，参见 [BR-PUB-004](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-004)。

### ApplicationOAuthRegistration 与 OAuthClientCredential

ApplicationOAuthRegistration 是每个 Application 每渠道至多一个的聚合根，以 `(applicationId, channel)` 为身份。它保存可选 publicClientId/publicStatus、confidentialClientId/confidentialStatus 、各 slot 的 authorizationEpoch 和 registrationRevision。两个 clientId 都是全局稳定身份，固定归属一个 channel，不包含 rpcApiMajor、Version 或 hostname；PUBLIC 与 CONFIDENTIAL 使用不同 clientId，分别执行不可降级的安全规则。

OAuthClientCredential 只属于 confidentialClientId，保存 secret 摘要、credentialRevision 与 rotatedAt。它使用独立 revision，使常见的 secret 轮换不改变 registration、Version、grant 或发布资格。轮换只影响以后 confidential client authentication。

Registration 不保存 redirect URI 或 scopes；这些事实由当前 Publication 指向的批准 ApplicationVersion snapshot 提供。同渠道切换 Version、RPC major 或 redirect hostname 不重建 clientId。App Center 只提供配置与资格快照，Auth 拥有 consent、code、grant 和 token。

### ApplicationReview

每个 ApplicationReview 是独立聚合根，表示一次审核 attempt。它保存不可变 `ApplicationVersionReviewSnapshot`、一次性 decision 和可选 draft restoration，并适合独立进入审核队列与审计查询。

提交、决定和拒绝后恢复仍需要同时改变 Review 与 Version。App Center 应用服务使用同一个本地原子边界协调两个聚合，保持 [BR-REV-009](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-009)、[BR-REV-013](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) 与 [BR-REV-027](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-027) 已定义的一致性。这种协调关系不要求把 Review 变成 Version 的内部实体。

### ApplicationProfile

ApplicationProfile 是每个 Application 的资料协调聚合，目标模型包含：

```text
ApplicationProfile
  applicationId
  workingProfileRevisionId?
  currentPublishedProfileRevisionId?
  revisions: ApplicationProfileRevision[]
  revision
```

ApplicationProfileRevision 是一版完整公开资料，不是字段 patch。现有字段为 displayName、可空 description 和可空 icon；icon 当前是不透明字符串，不承担受控资产身份或可用性保证。资料修订与 ApplicationVersion 相互独立，权威边界见 [BR-PRF-005](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005)。

`workingProfileRevisionId` 用来表达单一工作修订约束：它在 DRAFT 创建时设置，提交为 SUBMITTED 后继续保留，并在审核批准或拒绝时清空。因此 PENDING 期间不能并行创建下一份 DRAFT，权威规则见 [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)。`currentPublishedProfileRevisionId` 明确当前目录展示的资料；它不是管理员可单独操作的发布槽位。Profile Review 批准时，目标 Revision 进入 APPROVED，并在同一业务操作中自动成为当前公开资料。

新资料审核被拒绝时，当前公开指针保持不变。新资料审核通过时，指针替换为新 Revision；首版不提供选择旧 Revision 或回滚公开资料的行为。历史 Revision 与审核决定仍保留用于审计。

### ApplicationProfileReview

UC-APP-015 已把 ApplicationProfileReview 定义为引用 ProfileRevision 的独立聚合根，并建立 PENDING、不可变提交快照、sourceRevision 和提交审计。UC-APP-016 增加 `app.profile.review`、版本化 ProfileReviewPolicy 和一次性 decision。ProfileReview 没有 draftRestoration；REJECTED Revision 与拒绝决定保持不变。

批准资料需要原子协调 ApplicationProfileRevision、ApplicationProfileReview、`workingProfileRevisionId` 与 `currentPublishedProfileRevisionId`；拒绝也会清空工作指针。权威规则见 [BR-PRF-026](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-026)、[BR-PRF-030](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030) 与 [BR-PRF-032](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-032)。被拒绝内容的重新编辑不是领域迁移：网页端预填创建表单，App Center 按照普通创建处理一个新 ProfileRevision。

公开资料的紧急隐藏不扩展为 ProfileRevision 的 REVOKED 状态。后续应由 Application Ownership 定义 Application 级禁用：Application admin 或 SysAdmin 发起，并统一影响目录与运行分发。其权限、审计、重新启用及槽位处理尚未具体化为 UC。

### ApplicationPublication

ApplicationPublication 以 `(applicationId, rpcApiMajor)` 作为业务身份，拥有该分区的服务端发布槽位、共享 revision 和变更审计：

```text
ApplicationPublication
  testVersionId?
  greyRollout?
  stableVersionId?
  revision
  history: ApplicationPublicationHistory[]
```

testVersionId 的规则由 UC-APP-007 定义；[UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md) 已接受可空 stableVersionId、保留 EMPTY Publication 和 stable History/OAuth 语义。[UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md) 已接受把 GreyRollout 定义为稳定身份、目标 Version、万分比和内部 cohortSeed 的组合。分区依据见 [BR-PUB-002](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-002)，共同发布资格见 [BR-PUB-003](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003)。

ApplicationPublicationHistory 是不可修改的操作审计记录，不是 event-sourcing 的权威状态；当前槽位仍由 ApplicationPublication 表达，参见 [BR-PUB-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007)。

ApplicationVersion 的 APPROVED 状态只表达渠道无关的发布资格，不把 Version 自动放入任何槽位。TEST、GREY、STABLE 各自选择已批准 Version 并执行自己的资格规则；设置 Version 时共享相同的批准约束。TEST 额外要求当前已批准 ApplicationProfile，并在运行解析时结合 Tester Membership。开发版客户端直开任意 URL 不创建 ApplicationPublication，也不能绕过 Version 或 Profile 审核。

### ApplicationTesterAccess

ApplicationTesterAccess 是每个 Application 的测试访问协调聚合：

```text
ApplicationTesterAccess
  applicationId
  activeJoinLinkId?
  activeTesterCount
  testerLimit
  joinLinks: ApplicationTesterJoinLink[]
  memberships: ApplicationTesterMembership[]
```

ApplicationTesterJoinLink 和 ApplicationTesterMembership 是生命周期独立的实体：轮换或撤销链接不移除 Membership，移除 Membership 也不撤销链接。它们仍放在同一协调聚合下，以表达加入时对有效链接、ACTIVE Membership 唯一性和容量的联合检查；相关权威规则见 [BR-TST-017](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-017) 与 [BR-TST-026](use-cases/UC-APP-010-remove-application-tester.md#br-tst-026)。

Membership 是一次 episode。REMOVED 历史不会恢复，重新加入产生新 membershipId，参见 [BR-TST-016](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-016)。历史记录可以独立读取；聚合执行命令时只需要装载保护当前不变量所需的状态。

### ApplicationFilter 与 ApplicationFilterRevision

ApplicationFilter 是每个 Application 至多一个的公开展示策略协调聚合。它保存 currentFilterRevisionId、revision、nextSequence 和最近更新审计；聚合不存在等价于 revision 0 的 `ALLOW_ALL`。

ApplicationFilterRevision 是不可变且创建后立即发布的规则事实，mode 为 `RULE` 或 `ALLOW_ALL`。Filter 不需要草稿、提交或审核生命周期；每次真实 Set/Clear 创建下一 sequence 的 Revision 并原子推进 current pointer。规则属于 Application，不按 Version、Publication channel 或 rpcApiMajor 复制，因此同一当前规则同时随 Grey/Stable Catalog 候选分发，Test 入口不执行 Filter。

规则树采用 `profile-filter-v1`，字段 key 与四种标量复用 Auth ProfileFieldDefinition 的稳定语法，但 App Center 不读取字段目录或用户值。Filter 修改不改变 Publication、Profile、Version、OAuth 或服务端运行资格。权威规则见 [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md)。

## 主要实体与关系

| 实体 | 身份 | 直接归属 | 关键关系 |
| --- | --- | --- | --- |
| Application | ApplicationId | Application | 引用当前 adminId 和 ownershipRevision；被所有下级聚合引用 |
| ApplicationAdminTransfer | ApplicationAdminTransferId | ApplicationAdminTransfer | 引用一个 Application、源/目标管理员和发起时 ownershipRevision |
| ApplicationClosure | ApplicationClosureId | ApplicationClosure | 一个 Application 至多一个；保存不可逆关闭与 Auth 回执 |
| ApplicationVersion | ApplicationVersionId | ApplicationVersion | 属于一个 Application；拥有多个 Review attempt |
| ApplicationReview | ApplicationReviewId | ApplicationReview | 引用一个 Version；冻结 snapshot 并保存一次性决定 |
| ApplicationVersionOAuthConfig | ApplicationVersionId | ApplicationVersion | 一对一依附 Version；与 Version 共用 revision 和审核生命周期 |
| ApplicationOAuthRegistration | ApplicationId | ApplicationOAuthRegistration | 属于一个 Application；保存两种可选稳定 client identity |
| OAuthClientCredential | ConfidentialClientId | OAuthClientCredential | 属于 confidential identity；使用独立 credentialRevision |
| ApplicationProfileRevision | ApplicationProfileRevisionId | ApplicationProfile | 属于一个 Application；可被资料 Review 和当前公开指针引用 |
| ApplicationProfileReview | ApplicationProfileReviewId | ApplicationProfileReview | 引用一个 ProfileRevision；冻结 snapshot 并保存一次性决定 |
| ApplicationPublication | ApplicationPublicationId | ApplicationPublication | 对应一个 Application 与一个 RPC major；引用 Version |
| ApplicationPublicationHistory | HistoryId | ApplicationPublication | 记录一次真实槽位变化 |
| ApplicationFilter | ApplicationId | ApplicationFilter | 当前 Filter Revision 指针和独立 OCC |
| ApplicationFilterRevision | FilterRevisionId | ApplicationFilterRevision | 属于一个 Application；不可变且创建后立即发布 |
| ApplicationTesterJoinLink | JoinLinkId | ApplicationTesterAccess | 向匿名持有者提供申请 Tester Membership 的凭证 |
| ApplicationTesterMembership | MembershipId | ApplicationTesterAccess | 连接 Application 与 testerAuthId 的一次资格 episode |

表中的“直接归属”表示负责保护生命周期与不变量的聚合，不表示数据库嵌套方式。

## 值对象

| 值对象 | 含义 |
| --- | --- |
| ApplicationId、ApplicationVersionId 等 | 类型化 UUIDv7 身份，避免不同实体 ID 混用 |
| ApplicationAdminTransferId | 类型化 UUIDv7 转让申请身份 |
| ApplicationClosureId | 类型化 UUIDv7 关闭过程身份 |
| AuthId | Auth 提供的不透明用户身份引用 |
| ApplicationName | 技术名称原值及大小写不敏感比较键 |
| VersionLabel | 开发者自用、大小写敏感且不参与排序的标签 |
| LaunchURL | 已分类并规范校验的应用入口 |
| RpcApiRange | `[min, maxExclusive)` 的宿主 RPC major 兼容范围 |
| CapabilitySet | 按客户端 RPC 契约命名、由 App Center 本地校验格式、拒绝重复并稳定排序的宿主能力集合；当前没有在线 Catalog |
| ScopeRequest | requiredScopes 与 optionalScopes 的互斥规范化集合；名称是 Auth Catalog 的不透明 token |
| OAuthRedirectConfiguration | pkceRedirectUris/confidentialRedirectUris 两个互斥、稳定排序并随 Version 审核的精确 HTTPS 回调集合 |
| ApplicationVersionReviewSnapshot | 一次版本审核读取的不可变内容 |
| ApplicationDisplayName、ApplicationDescription | NFC 规范化的公开纯文本 |
| ProfileContent | 一版完整资料内容；未来可以加入受控 IconAssetId |
| ApplicationProfileReviewSnapshot | 一次资料审核读取的不可变完整内容 |
| PublicationRevision | 一个 RPC major 下全部槽位共享的乐观并发版本 |
| GreyRollout | UC-APP-021 定义的 rolloutId、grey Version、万分比与内部稳定 cohortSeed 组合 |
| TesterJoinTokenHash | Tester 加入 secret 的不可逆校验值 |
| FilterRule | `profile-filter-v1` 类型化有界树；服务端保存和分发，客户端使用本地用户信息求值 |

值对象没有独立生命周期；字段限制继续引用各 UC 中的权威 BR，而不在本文复制一份易漂移的规则。

## 领域服务与查询模型

### CatalogResolver

CatalogResolver 是跨聚合的只读组合服务。它读取 Application、已发布 Profile、TesterAccess、ApplicationPublication 和 ApplicationVersion，为每个候选 Application 产生唯一服务端启动目标，并附带 FilterRule。[UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md) 把单 Application 的 `TEST > GREY > STABLE` 选择收敛为可被列表与详情复用的统一解析端口。

[UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md) 以兼容 Stable 作为普通公开候选基线，在同一只读页面或详情快照中组合当前公开 Profile、UC023 目标和当前 Filter。它不成为这些事实的新权威来源，也不保存客户端 Filter 求值结果或物化 Catalog item。

### ReviewPolicyProvider 与发布资格检查

ReviewPolicyProvider 与 ProfileReviewPolicyProvider 分别提供版本化的运行版本审核策略和公开资料审核策略；ScopeCatalog 和 LaunchURLSubmissionPolicy 提供外部校验事实。它们是领域端口或策略服务，不是聚合内实体。

客户端 RPC 契约是 capability 名称与演进的权威所有者；App Center 当前只保存 ApplicationVersion 声明的 CapabilitySet，不维护或查询第二份 Capability Catalog。Auth 则是 Scope Catalog 的唯一权威所有者；Version 核心通过 ScopeCatalog port 取得可申请性事实和 catalog revision，具体 Auth transport 与有界缓存留在 adapter。

发布资格检查组合 Version、最新批准 Review 与外部复检结果。它服务于 Publication 命令，但不会把 Version 或 Review 移入 Publication 聚合。

## FilterRule 的归属

[UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md) 已确认 ApplicationFilter＋不可变 ApplicationFilterRevision。Filter 无需审核，每次修改立即发布；它与 Profile、Version 和 Publication 独立演进。客户端求值线格式由 [Application Filter v1](../platform/contracts/application-filter-v1.md) 固定。

## 需要后续 UC 验证的聚合切分

- ApplicationProfile 在实现中是否能如 UC-APP-013 和 UC-APP-016 要求的那样，在并发创建和审核时同时保护单一 DRAFT/SUBMITTED 工作修订与当前公开指针。
- ApplicationTesterAccess 在并发加入时是否应作为单一聚合，还是拆分后使用显式一致性协议。
- ApplicationReview 作为独立聚合后，与 ApplicationVersion 状态迁移的本地原子协调方式。
- ApplicationClosure 的实现是否能以有界本地事务完成配额、转让、链接和 OAuth slot 的原子变化，并在 Auth 长期故障时可靠保留收敛任务。

这些问题用于验证边界，不要求现在为每个问题创建独立 UC。

OAuth 身份隔离：client/credential 按渠道隔离；major 共用同渠道 client。Application 级 sector 与用户 sub 仅由 Auth 保存，App 仅提供 client 归属及批准回调事实，见 [提供方契约](../platform/contracts/app-oauth-client-v1.md)。
