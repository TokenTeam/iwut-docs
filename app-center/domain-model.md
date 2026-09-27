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

Application 是稳定业务身份和当前管理权的聚合根。当前业务字段保持 `id`、`name`、`adminId`、`createdAt`；公开资料不属于它，依据 [BR-APP-004](use-cases/UC-APP-001-create-application.md#br-app-004) 由独立资料模型表达。

Application 提供其他聚合共同引用的 `applicationId` 和当前 `adminId`。版本序号与资料序号的分配器属于创建协调所需状态，不增加 Application 的公开业务含义。

未来的改名、归档和管理员转让会扩展这一聚合的行为；它们不会把 Version、Profile、Publication 或 Tester 实体搬入 Application。

### DeveloperApplicationQuota

DeveloperApplicationQuota 以 `adminId` 为身份，表达一个 Developer 当前可拥有的 Application 数量上限和占用量。它独立于单个 Application，因为约束跨越同一管理员的全部 Application。

DeveloperApplicationQuota 自身的 `limit` 与 `usedCount` 是配额的唯一权威状态。缺少该聚合时，创建 Application 使用进程组装时注入的初始上限惰性建立它；该配置默认 10。已存在配额的 `limit` 不得被启动配置或创建路径覆盖，只能由未来的独立配额调整用例修改。具体配置契约、持久化形状由对应 UC 和 adapter 定义。

创建 Application 时的名称占用、配额消费和 Application 创建具有一个业务一致性要求，权威规则见 [BR-APP-005](use-cases/UC-APP-001-create-application.md#br-app-005) 与 [BR-APP-006](use-cases/UC-APP-001-create-application.md#br-app-006)。管理员转让和归档出现后，需要重新判断配额归属与释放语义。

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

ApplicationOAuthRegistration 是每个 Application 至多一个的聚合根，以 applicationId 为身份。它保存可选 publicClientId/publicStatus、confidentialClientId/confidentialStatus 和 registrationRevision。两个 clientId 都是全局稳定身份，不包含 channel、rpcApiMajor、Version 或 hostname；PUBLIC 与 CONFIDENTIAL 使用不同 clientId，分别执行不可降级的安全规则。

OAuthClientCredential 只属于 confidentialClientId，保存 secret 摘要、credentialRevision 与 rotatedAt。它使用独立 revision，使常见的 secret 轮换不改变 registration、Version、grant 或发布资格。轮换只影响以后 confidential client authentication。

Registration 不保存 redirect URI 或 scopes；这些事实由当前 Publication 指向的批准 ApplicationVersion snapshot 提供。切换 Version、RPC major 或 redirect hostname 不重建 clientId。App Center 只提供配置与资格快照，Auth 拥有 consent、code、grant 和 token。

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

当前只有 testVersionId 已有权威规则。分区依据见 [BR-PUB-002](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-002)，Version 发布资格见 [BR-PUB-003](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003)。GreyRollout 和 stableVersionId 是首版目标模型，具体字段与行为等待后续 UC。

ApplicationPublicationHistory 是不可修改的操作审计记录，不是 event-sourcing 的权威状态；当前槽位仍由 ApplicationPublication 表达，参见 [BR-PUB-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007)。

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

## 主要实体与关系

| 实体 | 身份 | 直接归属 | 关键关系 |
| --- | --- | --- | --- |
| Application | ApplicationId | Application | 引用当前 adminId；被所有下级聚合引用 |
| ApplicationVersion | ApplicationVersionId | ApplicationVersion | 属于一个 Application；拥有多个 Review attempt |
| ApplicationReview | ApplicationReviewId | ApplicationReview | 引用一个 Version；冻结 snapshot 并保存一次性决定 |
| ApplicationVersionOAuthConfig | ApplicationVersionId | ApplicationVersion | 一对一依附 Version；与 Version 共用 revision 和审核生命周期 |
| ApplicationOAuthRegistration | ApplicationId | ApplicationOAuthRegistration | 属于一个 Application；保存两种可选稳定 client identity |
| OAuthClientCredential | ConfidentialClientId | OAuthClientCredential | 属于 confidential identity；使用独立 credentialRevision |
| ApplicationProfileRevision | ApplicationProfileRevisionId | ApplicationProfile | 属于一个 Application；可被资料 Review 和当前公开指针引用 |
| ApplicationProfileReview | ApplicationProfileReviewId | ApplicationProfileReview | 引用一个 ProfileRevision；冻结 snapshot 并保存一次性决定 |
| ApplicationPublication | ApplicationPublicationId | ApplicationPublication | 对应一个 Application 与一个 RPC major；引用 Version |
| ApplicationPublicationHistory | HistoryId | ApplicationPublication | 记录一次真实槽位变化 |
| ApplicationTesterJoinLink | JoinLinkId | ApplicationTesterAccess | 向匿名持有者提供申请 Tester Membership 的凭证 |
| ApplicationTesterMembership | MembershipId | ApplicationTesterAccess | 连接 Application 与 testerAuthId 的一次资格 episode |

表中的“直接归属”表示负责保护生命周期与不变量的聚合，不表示数据库嵌套方式。

## 值对象

| 值对象 | 含义 |
| --- | --- |
| ApplicationId、ApplicationVersionId 等 | 类型化 UUIDv7 身份，避免不同实体 ID 混用 |
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
| GreyRollout | 待定义的 grey version、比例与稳定分桶参数组合 |
| TesterJoinTokenHash | Tester 加入 secret 的不可逆校验值 |
| FilterRule | 服务端保存和分发、客户端使用本地用户信息求值的规则；结构尚未确定 |

值对象没有独立生命周期；字段限制继续引用各 UC 中的权威 BR，而不在本文复制一份易漂移的规则。

## 领域服务与查询模型

### CatalogResolver

CatalogResolver 是跨聚合的只读组合服务。它读取 Application、已发布 Profile、TesterAccess、ApplicationPublication 和 ApplicationVersion，为每个候选 Application 产生唯一服务端启动目标，并附带 FilterRule。

它不成为这些事实的新权威来源，也不保存客户端 Filter 求值结果。现有 TestLaunchDescriptor 是这个方向的第一个窄查询模型；规则见 [BR-RUN-001](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001) 至 [BR-RUN-010](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-010)。

### ReviewPolicyProvider 与发布资格检查

ReviewPolicyProvider 与 ProfileReviewPolicyProvider 分别提供版本化的运行版本审核策略和公开资料审核策略；ScopeCatalog 和 LaunchURLSubmissionPolicy 提供外部校验事实。它们是领域端口或策略服务，不是聚合内实体。

客户端 RPC 契约是 capability 名称与演进的权威所有者；App Center 当前只保存 ApplicationVersion 声明的 CapabilitySet，不维护或查询第二份 Capability Catalog。Auth 则是 Scope Catalog 的唯一权威所有者；Version 核心通过 ScopeCatalog port 取得可申请性事实和 catalog revision，具体 Auth transport 与有界缓存留在 adapter。

发布资格检查组合 Version、最新批准 Review 与外部复检结果。它服务于 Publication 命令，但不会把 Version 或 Review 移入 Publication 聚合。

## FilterRule 的未决归属

FilterRule 已进入首版产品范围，但尚无足够用例决定其聚合归属。当前保留三种候选：

| 候选 | 适用条件 | 主要影响 |
| --- | --- | --- |
| ProfileContent 的一部分 | Filter 与公开资料总是一起审核，并随批准自动公开 | 模型最小，但资料变化会连带 Filter |
| Application 的独立字段 | Filter 几乎不修订且不需要独立审核 | 简单，但审计与历史表达较弱 |
| ApplicationFilterRevision 独立聚合 | Filter 有独立草稿、审核、回滚或策略版本 | 边界清晰，但增加一条生命周期 |

在明确“谁编辑、谁审核、何时生效、是否回滚”之前，本文只把 FilterRule 作为 Catalog 输出需要引用的领域概念，不提前选择其中一种。

## 需要后续 UC 验证的聚合切分

- ApplicationProfile 在实现中是否能如 UC-APP-013 和 UC-APP-016 要求的那样，在并发创建和审核时同时保护单一 DRAFT/SUBMITTED 工作修订与当前公开指针。
- ApplicationTesterAccess 在并发加入时是否应作为单一聚合，还是拆分后使用显式一致性协议。
- ApplicationReview 作为独立聚合后，与 ApplicationVersion 状态迁移的本地原子协调方式。
- 管理员转让如何跨 Application、Quota 及下级聚合重新建立权限与名称占用关系。
- FilterRule 最终归属及其审核、修订和发布模型。

这些问题用于验证边界，不要求现在为每个问题创建独立 UC。
