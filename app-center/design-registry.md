# App Center 设计标识符注册表

状态：`ACTIVE`

本文件穷举已经分配的 UC、BR 和 ADR 标识符，用于避免重复编号并定位唯一权威正文。命名、编号和状态规则见 [document-conventions.md](document-conventions.md)。

完整设计内容以“权威位置”指向的文件或章节为准，本注册表不复制正文。

## 下一个可分配编号

<!-- 机器可读的已废弃编号声明；由 tools/registry.py 读取，用于计算 Next ID，不得删除。 -->
<!-- retired: UC-APP-017 BR-PRF-033 BR-PRF-034 BR-PRF-035 BR-PRF-036 BR-PRF-037 BR-PRF-038 BR-PRF-039 BR-PRF-040 -->

<!-- 下表由 tools/registry.py --write 生成；不要手工编辑。 -->

| 编号空间 | Next ID |
| --- | --- |
| Use Case / App Center | `UC-APP-018` |
| Business Rule / Application | `BR-APP-008` |
| Business Rule / Application Profile | `BR-PRF-041` |
| Business Rule / ApplicationVersion | `BR-VER-018` |
| Business Rule / Review | `BR-REV-029` |
| Business Rule / Publication | `BR-PUB-011` |
| Business Rule / Tester | `BR-TST-037` |
| Business Rule / Runtime Resolution | `BR-RUN-011` |
| Architecture Decision | `ADR-007` |

Next ID 只是分配提示。新增条目前仍须搜索整个文档目录，确认没有未登记的既有定义。

`UC-APP-017` 与 `BR-PRF-033`–`BR-PRF-040` 在进入实现前按产品决定直接删除：ProfileRevision 不提供服务端恢复行为。这些编号不再分配，不构成已登记设计项；它们登记在上面的 `retired` 声明中，因此不会被重新分配。

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `UC-APP-001` | 开发者新建应用 | `ACCEPTED` | [UC-APP-001-create-application.md](use-cases/UC-APP-001-create-application.md) | — | Domain、UseCase、MongoDB、Proto、HTTP/gRPC Transport、可信身份、Composition Root 与真实 MongoDB 端到端测试已闭合；实现状态见 `implements/README.md`。 |
| `UC-APP-002` | 创建应用版本 | `ACCEPTED` | [UC-APP-002-create-application-version.md](use-cases/UC-APP-002-create-application-version.md) | — | Domain、UseCase、MongoDB 持久化、Scope Catalog cache 与事务集成测试已闭合；实现状态见 `implements/README.md`。 |
| `UC-APP-003` | 更新草稿应用版本 | `ACCEPTED` | [UC-APP-003-update-draft-application-version.md](use-cases/UC-APP-003-update-draft-application-version.md) | — | Domain、UseCase、MongoDB 持久化、显式 migration 与事务并发集成测试已闭合；实现状态见 `implements/README.md`。 |
| `UC-APP-004` | 提交应用版本审核 | `ACCEPTED` | [UC-APP-004-submit-application-version-review.md](use-cases/UC-APP-004-submit-application-version-review.md) | — | Domain、UseCase、MongoDB 持久化、显式 migration 与事务并发集成测试已闭合；实现状态见 `implements/README.md`。 |
| `UC-APP-005` | 审核应用版本 | `ACCEPTED` | [UC-APP-005-decide-application-version-review.md](use-cases/UC-APP-005-decide-application-version-review.md) | — | Auth/ConfCenter 与暂停检查使用 ports，核心测试使用 deterministic fakes；实现状态见 `implements/README.md`。 |
| `UC-APP-006` | 将被拒绝的应用版本恢复为草稿 | `ACCEPTED` | [UC-APP-006-restore-rejected-version-to-draft.md](use-cases/UC-APP-006-restore-rejected-version-to-draft.md) | — | — |
| `UC-APP-007` | 将已批准应用版本放入测试发布槽位 | `ACCEPTED` | [UC-APP-007-place-approved-version-in-test-slot.md](use-cases/UC-APP-007-place-approved-version-in-test-slot.md) | — | Domain、UseCase、MongoDB、Proto、HTTP/gRPC 与 consumer E2E 已交付；外部依赖见 `implements/README.md`。 |
| `UC-APP-008` | 创建或轮换 Tester 加入链接 | `ACCEPTED` | [UC-APP-008-create-or-rotate-tester-join-link.md](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) | — | 当前 mock 入口后端工作包 COMPLETE，含 env URL 前缀、原子轮换、API 与真实 MongoDB E2E；见 `implements/README.md`。 |
| `UC-APP-009` | 通过有效链接加入 Application Tester 列表 | `PROPOSED` | [UC-APP-009-join-application-as-tester.md](use-cases/UC-APP-009-join-application-as-tester.md) | — | — |
| `UC-APP-010` | 管理员移除 Application Tester | `PROPOSED` | [UC-APP-010-remove-application-tester.md](use-cases/UC-APP-010-remove-application-tester.md) | — | — |
| `UC-APP-011` | 管理员显式撤销 Tester 加入链接 | `PROPOSED` | [UC-APP-011-revoke-tester-join-link.md](use-cases/UC-APP-011-revoke-tester-join-link.md) | — | — |
| `UC-APP-012` | 为 Tester 解析 Application 的 test 启动目标 | `PROPOSED` | [UC-APP-012-resolve-test-launch-target-for-tester.md](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) | — | — |
| `UC-APP-013` | 创建应用公开资料修订草稿 | `PROPOSED` | [UC-APP-013-create-application-profile-revision.md](use-cases/UC-APP-013-create-application-profile-revision.md) | — | — |
| `UC-APP-014` | 更新应用公开资料修订草稿 | `PROPOSED` | [UC-APP-014-update-draft-application-profile-revision.md](use-cases/UC-APP-014-update-draft-application-profile-revision.md) | — | — |
| `UC-APP-015` | 提交应用公开资料修订审核 | `PROPOSED` | [UC-APP-015-submit-application-profile-revision-review.md](use-cases/UC-APP-015-submit-application-profile-revision-review.md) | — | — |
| `UC-APP-016` | 审核应用公开资料修订 | `PROPOSED` | [UC-APP-016-decide-application-profile-revision-review.md](use-cases/UC-APP-016-decide-application-profile-revision-review.md) | — | — |

## Business Rules

### Application (`BR-APP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-APP-001` | Application ID | Identity / Invariant | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-001) | — | — |
| `BR-APP-002` | 开发者资格与管理员 | Authorization / Relationship | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-002) | — | — |
| `BR-APP-003` | 名称 | Field / Invariant | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-003) | — | — |
| `BR-APP-004` | 公开资料不属于 Application | Boundary | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-004) | — | — |
| `BR-APP-005` | 创建配额 | Policy / Invariant | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-005) | — | — |
| `BR-APP-006` | 并发原子性 | Consistency | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-006) | — | — |
| `BR-APP-007` | 创建时间 | Audit / Invariant | [UC-APP-001](use-cases/UC-APP-001-create-application.md#br-app-007) | — | — |

### Application Profile (`BR-PRF`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-PRF-001` | 资料修订身份与序号 | Identity / Invariant | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-001) | — | — |
| `BR-PRF-002` | 创建权限 | Authorization | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-002) | — | — |
| `BR-PRF-003` | displayName | Field / Content Safety | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003) | — | — |
| `BR-PRF-004` | description | Field / Content Safety | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) | — | — |
| `BR-PRF-005` | 完整资料快照与图标边界 | Boundary / Snapshot | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005) | — | — |
| `BR-PRF-006` | 初始生命周期与单一工作修订 | Lifecycle / Invariant | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006) | — | — |
| `BR-PRF-007` | 原子创建与初始审计 | Consistency / Audit | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-007) | — | — |
| `BR-PRF-008` | 仅草稿可编辑 | Lifecycle / Precondition | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-008) | — | — |
| `BR-PRF-009` | 完整替换 | Command Semantics | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-009) | — | — |
| `BR-PRF-010` | 不可变身份与创建审计 | Identity / Audit / Invariant | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-010) | — | — |
| `BR-PRF-011` | 乐观并发与 no-op | Concurrency / Command Semantics | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-011) | — | — |
| `BR-PRF-012` | 字段规则复用与图标边界 | Rule Reuse / Boundary | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-012) | — | — |
| `BR-PRF-013` | 权限、状态与更新原子性 | Authorization / Consistency | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-013) | — | — |
| `BR-PRF-014` | 草稿修改审计粒度 | Audit Policy | [UC-APP-014](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-014) | — | — |
| `BR-PRF-015` | 提交权限 | Authorization | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-015) | — | — |
| `BR-PRF-016` | 提交前状态与乐观并发 | Lifecycle / Concurrency | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-016) | — | — |
| `BR-PRF-017` | 提交时内容复检 | Validation / Boundary | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-017) | — | — |
| `BR-PRF-018` | 不可变审核快照 | Snapshot / Invariant | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-018) | — | — |
| `BR-PRF-019` | 审核 attempt 身份 | Identity / Invariant | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-019) | — | — |
| `BR-PRF-020` | ProfileRevision 状态与审计 | Lifecycle / Audit | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-020) | — | — |
| `BR-PRF-021` | 原子提交与重复请求 | Consistency / Idempotency | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-021) | — | — |
| `BR-PRF-022` | 提交不改变当前公开资料 | Boundary | [UC-APP-015](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-022) | — | — |
| `BR-PRF-023` | Reviewer 权限与利益冲突 | Authorization / Policy | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-023) | — | — |
| `BR-PRF-024` | 一次性决定与前置状态 | Lifecycle / Invariant | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-024) | — | — |
| `BR-PRF-025` | Review、Revision 与 snapshot 一致性 | Consistency / Invariant | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-025) | — | — |
| `BR-PRF-026` | 状态同步 | Lifecycle / Consistency | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-026) | — | — |
| `BR-PRF-027` | 决定理由 | Field / Policy | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-027) | — | — |
| `BR-PRF-028` | 版本化资料审核策略 | Policy / Audit | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028) | — | — |
| `BR-PRF-029` | 批准时资料复检 | Validation / Content Safety | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-029) | — | — |
| `BR-PRF-030` | 批准后自动公开 | Lifecycle / Consistency | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030) | — | — |
| `BR-PRF-031` | 拒绝终止修订且不改变当前公开资料 | Boundary / Lifecycle | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) | — | — |
| `BR-PRF-032` | Revision、审计与原子决定 | Concurrency / Audit / Consistency | [UC-APP-016](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-032) | — | — |

### ApplicationVersion (`BR-VER`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-VER-001` | 版本身份与序号 | Identity / Invariant | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-001) | — | — |
| `BR-VER-002` | 创建权限 | Authorization | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-002) | — | — |
| `BR-VER-003` | versionLabel | Field / Invariant | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-003) | — | — |
| `BR-VER-004` | launchUrl | Field / Policy | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-004) | — | — |
| `BR-VER-005` | RPC 兼容范围 | Field / Compatibility | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-005) | — | — |
| `BR-VER-006` | requiredCapabilities | Field | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-006) | — | — |
| `BR-VER-007` | scopes | Field / Invariant | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-007) | — | — |
| `BR-VER-008` | 初始生命周期 | Lifecycle / Invariant | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-008) | — | — |
| `BR-VER-009` | 原子创建 | Consistency | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-009) | — | — |
| `BR-VER-010` | 仅草稿可编辑 | Lifecycle / Precondition | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-010) | — | — |
| `BR-VER-011` | 完整替换 | Command Semantics | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-011) | — | — |
| `BR-VER-012` | 不可变身份与创建审计 | Identity / Audit / Invariant | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-012) | — | — |
| `BR-VER-013` | 乐观并发 | Concurrency | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-013) | — | — |
| `BR-VER-014` | 集合规范化 | Field / Command Semantics | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-014) | — | — |
| `BR-VER-015` | 字段规则复用 | Rule Reuse | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-015) | — | — |
| `BR-VER-016` | 权限与更新原子性 | Authorization / Consistency | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-016) | — | — |
| `BR-VER-017` | 草稿审计粒度 | Audit Policy | [UC-APP-003](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-017) | — | — |

### Review (`BR-REV`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-REV-001` | 提交权限 | Authorization | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-001) | — | — |
| `BR-REV-002` | 提交前状态 | Lifecycle / Precondition | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-002) | — | — |
| `BR-REV-003` | 乐观并发与 Version revision | Concurrency | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-003) | — | — |
| `BR-REV-004` | 审核快照 | Snapshot / Invariant | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004) | — | — |
| `BR-REV-005` | 审核 attempt | Identity / Invariant | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-005) | — | — |
| `BR-REV-006` | Scope 重新验证 | External Validation | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-006) | — | — |
| `BR-REV-007` | 公网 HTTPS 预检 | External Validation / Security | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-007) | — | — |
| `BR-REV-008` | 自托管内容的弱保证 | Limitation | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-008) | — | — |
| `BR-REV-009` | 原子提交 | Consistency | [UC-APP-004](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-009) | — | — |
| `BR-REV-010` | Reviewer 权限 | Authorization | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-010) | — | — |
| `BR-REV-011` | 利益冲突 | Authorization / Policy | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-011) | — | — |
| `BR-REV-012` | 一次性决定 | Lifecycle / Invariant | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-012) | — | — |
| `BR-REV-013` | 状态一致性 | Consistency / Invariant | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) | — | — |
| `BR-REV-014` | Version revision 与审计 | Concurrency / Audit | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014) | — | — |
| `BR-REV-015` | 拒绝理由 | Field / Policy | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-015) | — | — |
| `BR-REV-016` | 版本化审核策略 | Policy / Audit | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016) | — | — |
| `BR-REV-017` | 批准检查确认 | Policy / Audit | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-017) | — | — |
| `BR-REV-018` | 批准时重新验证 | External Validation | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-018) | — | — |
| `BR-REV-019` | 审核与发布分离 | Boundary / Invariant | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-019) | — | — |
| `BR-REV-020` | 弱内容保证 | Limitation | [UC-APP-005](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-020) | — | — |
| `BR-REV-021` | 恢复权限 | Authorization | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-021) | — | — |
| `BR-REV-022` | 只恢复最新拒绝 | Lifecycle / Invariant | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-022) | — | — |
| `BR-REV-023` | 状态与 revision | Lifecycle / Concurrency | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-023) | — | — |
| `BR-REV-024` | 恢复不修改内容 | Command Semantics | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-024) | — | — |
| `BR-REV-025` | 拒绝事实不可变 | Audit / Invariant | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-025) | — | — |
| `BR-REV-026` | 一次性恢复审计 | Audit / Invariant | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-026) | — | — |
| `BR-REV-027` | 原子恢复 | Consistency | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-027) | — | — |
| `BR-REV-028` | 不提前重新验证 | Command Semantics | [UC-APP-006](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-028) | — | — |

### Publication (`BR-PUB`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-PUB-001` | 设置权限 | Authorization | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-001) | — | — |
| `BR-PUB-002` | 按 RPC major 分区 | Identity / Invariant | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-002) | — | — |
| `BR-PUB-003` | Version 发布资格 | Lifecycle / Invariant | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003) | — | — |
| `BR-PUB-004` | 测试槽位不是审核状态 | Boundary / Invariant | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-004) | — | — |
| `BR-PUB-005` | 测试可见性 | Policy | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-005) | — | — |
| `BR-PUB-006` | Publication 乐观并发 | Concurrency | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-006) | — | — |
| `BR-PUB-007` | PublicationHistory | Audit / Invariant | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007) | — | — |
| `BR-PUB-008` | 发布前复检 | External Validation | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-008) | — | — |
| `BR-PUB-009` | 原子写入 | Consistency | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-009) | — | — |
| `BR-PUB-010` | 不自动扩散 | Boundary | [UC-APP-007](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-010) | — | — |

### Tester (`BR-TST`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-TST-001` | 管理权限 | Authorization | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-001) | — | — |
| `BR-TST-002` | Application 级凭证 | Boundary / Invariant | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-002) | — | — |
| `BR-TST-003` | 单一有效链接 | Lifecycle / Invariant | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-003) | — | — |
| `BR-TST-004` | Secret 与哈希 | Security / Invariant | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) | — | — |
| `BR-TST-005` | 创建与轮换语义 | Command Semantics | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-005) | — | — |
| `BR-TST-006` | 乐观并发 | Concurrency | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-006) | — | — |
| `BR-TST-007` | 原子生命周期与审计 | Consistency / Audit | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-007) | — | — |
| `BR-TST-008` | 二维码只是展示 | Boundary / Security | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008) | — | — |
| `BR-TST-009` | 不产生 Tester Membership | Boundary | [UC-APP-008](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-009) | — | — |
| `BR-TST-010` | 可信身份与自助加入 | Authorization / Identity | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-010) | — | — |
| `BR-TST-011` | 链接凭证验证 | Security / Precondition | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-011) | — | — |
| `BR-TST-012` | Application 级 Membership | Boundary / Invariant | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-012) | — | — |
| `BR-TST-013` | ACTIVE Membership 幂等 | Command Semantics / Idempotency | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-013) | — | — |
| `BR-TST-014` | Tester 数量上限 | Policy / Invariant | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-014) | — | — |
| `BR-TST-015` | 移除后可以重新加入 | Lifecycle / Policy | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-015) | — | — |
| `BR-TST-016` | Membership episode 与唯一性 | Identity / Invariant | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-016) | — | — |
| `BR-TST-017` | 原子加入与容量竞争 | Consistency / Concurrency | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-017) | — | — |
| `BR-TST-018` | 与发布和 Auth 分离 | Boundary | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-018) | — | — |
| `BR-TST-019` | 凭证和隐私边界 | Security / Privacy | [UC-APP-009](use-cases/UC-APP-009-join-application-as-tester.md#br-tst-019) | — | — |
| `BR-TST-020` | 移除权限 | Authorization | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-020) | — | — |
| `BR-TST-021` | 按 Membership episode 定位 | Identity / Command Semantics | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-021) | — | — |
| `BR-TST-022` | 幂等移除 | Command Semantics / Idempotency | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-022) | — | — |
| `BR-TST-023` | REMOVED 终态与审计 | Lifecycle / Audit | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-023) | — | — |
| `BR-TST-024` | 原子释放容量 | Consistency / Invariant | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-024) | — | — |
| `BR-TST-025` | 不建立黑名单 | Policy / Boundary | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-025) | — | — |
| `BR-TST-026` | 加入链接独立 | Boundary | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-026) | — | — |
| `BR-TST-027` | 并发线性化 | Concurrency | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-027) | — | — |
| `BR-TST-028` | 边界与隐私 | Boundary / Privacy | [UC-APP-010](use-cases/UC-APP-010-remove-application-tester.md#br-tst-028) | — | — |
| `BR-TST-029` | 撤销权限 | Authorization | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-029) | — | — |
| `BR-TST-030` | 按链接身份定位 | Identity / Command Semantics | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-030) | — | — |
| `BR-TST-031` | MANUAL 撤销终态 | Lifecycle / Audit | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-031) | — | — |
| `BR-TST-032` | 幂等撤销 | Command Semantics / Idempotency | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-032) | — | — |
| `BR-TST-033` | 凭证立即失效 | Security / Invariant | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-033) | — | — |
| `BR-TST-034` | 并发线性化 | Concurrency | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-034) | — | — |
| `BR-TST-035` | 与 Tester Membership 独立 | Boundary | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-035) | — | — |
| `BR-TST-036` | 边界、审计与隐私 | Boundary / Audit / Privacy | [UC-APP-011](use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-036) | — | — |

### Runtime Resolution (`BR-RUN`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-RUN-001` | Tester 授权 | Authorization | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001) | — | — |
| `BR-RUN-002` | 按 exact RPC major 解析 | Resolution / Compatibility | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-002) | — | — |
| `BR-RUN-003` | test 槽位优先且不回退 | Resolution / Boundary | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003) | — | — |
| `BR-RUN-004` | Version 一致性与发布资格 | Invariant / Consistency | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-004) | — | — |
| `BR-RUN-005` | Capabilities 覆盖 | Compatibility | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005) | — | — |
| `BR-RUN-006` | 启动描述 | Query Result | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-006) | — | — |
| `BR-RUN-007` | 一致快照与并发 | Consistency / Concurrency | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-007) | — | — |
| `BR-RUN-008` | 只读且不做同步外部复检 | Boundary / Availability | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-008) | — | — |
| `BR-RUN-009` | 敏感信息与缓存 | Security / Privacy | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-009) | — | — |
| `BR-RUN-010` | 客户端与相邻上下文边界 | Boundary | [UC-APP-012](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-010) | — | — |

## Architecture Decision Records

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `ADR-001` | Scope Catalog 权威来源与缓存 | `PROPOSED` | [ADR-001-scope-catalog-cache.md](adr/ADR-001-scope-catalog-cache.md) | — | — |
| `ADR-002` | ApplicationPublication 按 RPC API major 分区 | `PROPOSED` | [ADR-002-partition-publication-by-rpc-api-major.md](adr/ADR-002-partition-publication-by-rpc-api-major.md) | — | — |
| `ADR-003` | Go package 与依赖边界 | `ACCEPTED` | [ADR-003-go-package-and-dependency-boundaries.md](adr/ADR-003-go-package-and-dependency-boundaries.md) | — | 代码仓库根目录的 architecture test 自动执行核心边界。 |
| `ADR-004` | MongoDB 事务与 Schema 管理 | `PROPOSED` | [ADR-004-mongodb-transactions-and-schema-management.md](adr/ADR-004-mongodb-transactions-and-schema-management.md) | — | — |
| `ADR-005` | 领域错误与 Transport 映射 | `PROPOSED` | [ADR-005-domain-errors-and-transport-mapping.md](adr/ADR-005-domain-errors-and-transport-mapping.md) | — | — |
| `ADR-006` | Proto v1 与独立 API 仓库协作 | `ACCEPTED` | [ADR-006-proto-v1-and-api-repository.md](adr/ADR-006-proto-v1-and-api-repository.md) | — | — |

## 注册表维护规则

- 新增 ID 时，必须同时更新对应的 Next ID。
- ID 改名时只修改标题，不修改编号。
- 权威正文退出活跃设计文档时，将其移入 `docs/app-center/archive/`，保留原 ID、标题和正文，并在同一次变更中更新“权威位置”链接。
- 标记为 `SUPERSEDED` 时，必须在“替代项”中填写新 ID；“备注”用于记录替代原因、迁移说明或其他必要上下文。
- 同一个 BR 被多个 UC 使用时，只保留一个权威位置；其他 UC 通过链接引用。
- BR 状态继承其权威正文所属 UC 的状态，注册表不单独保存 BR 状态。
- `类型` 用于检索和理解，不参与编号，也不改变权威规则正文。
