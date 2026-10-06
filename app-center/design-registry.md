# App Center 设计标识符注册表

状态：`ACTIVE`

本文件穷举已经分配的 UC、BR 和 ADR 标识符，用于避免重复编号并定位唯一权威正文。命名、编号和状态规则见 [document-conventions.md](document-conventions.md)。

完整设计内容以“权威位置”指向的文件或章节为准，本注册表不复制正文。

## 下一个可分配编号

<!-- 机器可读的已废弃编号声明；由 tools/registry.py 读取，用于计算 Next ID，不得删除。 -->
<!-- retired: BR-PRF-033 BR-PRF-034 BR-PRF-035 BR-PRF-036 BR-PRF-037 BR-PRF-038 BR-PRF-039 BR-PRF-040 -->

<!-- 下表由 tools/registry.py --write 生成；不要手工编辑。 -->

| 编号空间 | Next ID |
| --- | --- |
| Use Case / App Center | `UC-APP-028` |
| Business Rule / Application | `BR-APP-029` |
| Business Rule / Application Profile | `BR-PRF-041` |
| Business Rule / ApplicationVersion | `BR-VER-019` |
| Business Rule / Review | `BR-REV-029` |
| Business Rule / Publication | `BR-PUB-031` |
| Business Rule / Tester | `BR-TST-037` |
| Business Rule / Runtime Resolution | `BR-RUN-021` |
| Business Rule / Application Catalog | `BR-CAT-011` |
| Business Rule / OAuth Client | `BR-OAC-014` |
| Business Rule / Application Filter | `BR-FLT-011` |
| Architecture Decision | `ADR-007` |

Next ID 只是分配提示。新增条目前仍须搜索整个文档目录，确认没有未登记的既有定义。

`UC-APP-017` 在进入实现前被产品决定否决；其归档正文是依据现行规则重建的历史摘要，而非找回的原始提案。原计划分配给它的 `BR-PRF-033`–`BR-PRF-040` 没有可恢复的权威正文，继续登记在上面的 `retired` 声明中，不再分配。

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
| `UC-APP-009` | 通过有效链接加入 Application Tester 列表 | `ACCEPTED` | [UC-APP-009-join-application-as-tester.md](use-cases/UC-APP-009-join-application-as-tester.md) | — | — |
| `UC-APP-010` | 管理员移除 Application Tester | `ACCEPTED` | [UC-APP-010-remove-application-tester.md](use-cases/UC-APP-010-remove-application-tester.md) | — | — |
| `UC-APP-011` | 管理员显式撤销 Tester 加入链接 | `ACCEPTED` | [UC-APP-011-revoke-tester-join-link.md](use-cases/UC-APP-011-revoke-tester-join-link.md) | — | — |
| `UC-APP-012` | 为 Tester 解析 Application 的 test 启动目标 | `ACCEPTED` | [UC-APP-012-resolve-test-launch-target-for-tester.md](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) | — | — |
| `UC-APP-013` | 创建应用公开资料修订草稿 | `ACCEPTED` | [UC-APP-013-create-application-profile-revision.md](use-cases/UC-APP-013-create-application-profile-revision.md) | — | — |
| `UC-APP-014` | 更新应用公开资料修订草稿 | `ACCEPTED` | [UC-APP-014-update-draft-application-profile-revision.md](use-cases/UC-APP-014-update-draft-application-profile-revision.md) | — | — |
| `UC-APP-015` | 提交应用公开资料修订审核 | `ACCEPTED` | [UC-APP-015-submit-application-profile-revision-review.md](use-cases/UC-APP-015-submit-application-profile-revision-review.md) | — | — |
| `UC-APP-016` | 审核应用公开资料修订 | `ACCEPTED` | [UC-APP-016-decide-application-profile-revision-review.md](use-cases/UC-APP-016-decide-application-profile-revision-review.md) | — | — |
| `UC-APP-017` | 将被拒绝的应用公开资料修订恢复为草稿 | `SUPERSEDED` | [归档重建](archive/UC-APP-017-restore-rejected-profile-revision-to-draft.md) | [UC-APP-013](use-cases/UC-APP-013-create-application-profile-revision.md)＋[UC-APP-016 / BR-PRF-031](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) | 未实现；以新建独立修订取代服务端恢复。 |
| `UC-APP-018` | 管理应用 OAuth Client | `ACCEPTED` | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md) | — | TEST-only 管理后端已完成；provider/runtime 由 UC019 完成。 |
| `UC-APP-019` | 为 Auth 解析 OAuth 应用授权上下文 | `ACCEPTED` | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md) | — | Auth-only 原生 gRPC provider 已完成；实现证据见 `implements/README.md`。 |
| `UC-APP-020` | 管理稳定发布槽位 | `ACCEPTED` | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md) | — | Stable set/replace/clear、EMPTY Publication 与 STABLE OAuth channel 已完成；实现证据见 `implements/README.md`。 |
| `UC-APP-021` | 管理灰度发布 | `ACCEPTED` | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md) | — | Stable 基线、确定性 cohort、比例调整、清空与 GREY OAuth 已实现；见 implements。 |
| `UC-APP-022` | 管理 Application Filter | `ACCEPTED` | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md) | — | 无审核的 Application 级不可变 Revision、类型化规则和客户端求值契约；后端管理纵切片已交付。 |
| `UC-APP-023` | 解析 Application 的统一启动目标 | `ACCEPTED` | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md) | — | 统一 Test/Grey/Stable 单 Application 解析；后续 Catalog 列表与详情复用。 |
| `UC-APP-024` | 查询普通 Application Catalog 列表与详情 | `ACCEPTED` | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md) | — | Stable-backed 普通目录，组合公开 Profile、UC023 唯一目标与 Filter。 |
| `UC-APP-025` | 协调账号归属退出与个人状态清理 | `ACCEPTED` | [UC-APP-025](use-cases/UC-APP-025-coordinate-account-owner-exit.md) | — | Auth 治理交付依赖，零归属屏障与注销个人状态清理。 |
| `UC-APP-026` | 转让 Application 管理权 | `PROPOSED` | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md) | — | 发起—接受转让、配额原子移动、账号退出屏障及可选 CONFIDENTIAL secret 轮换。 |
| `UC-APP-027` | 关闭 Application | `PROPOSED` | [UC-APP-027](use-cases/UC-APP-027-close-application.md) | — | 不可逆 CLOSING/CLOSED、本地即时隔离、配额释放和持久 Auth 授权撤销收敛。 |

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
| `BR-APP-008` | 归属屏障与零义务准备 | Lifecycle / Consistency | [UC-APP-025](use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-008) | — | — |
| `BR-APP-009` | 单调终局与持久收敛 | Lifecycle / Consistency | [UC-APP-025](use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-009) | — | — |
| `BR-APP-010` | 注销个人状态清理 | Lifecycle / Consistency | [UC-APP-025](use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010) | — | — |
| `BR-APP-011` | 退出与终止状态的消费 | Lifecycle / Consistency | [UC-APP-025](use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-011) | — | — |
| `BR-APP-012` | 转让身份与参与者 | Identity / Authorization | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-012) | — | — |
| `BR-APP-013` | 单一待处理申请与固定过期 | Lifecycle / Invariant | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-013) | — | — |
| `BR-APP-014` | 新鲜 Auth 资格与有界竞态 | Authorization / Consistency | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-014) | — | — |
| `BR-APP-015` | 管理权 revision 与共享写栅栏 | Concurrency / Consistency | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-015) | — | — |
| `BR-APP-016` | 所有权、配额与名称原子转移 | Invariant / Consistency | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-016) | — | — |
| `BR-APP-017` | 账号退出屏障与确定锁序 | Concurrency / Consistency | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-017) | — | — |
| `BR-APP-018` | Credential 与 Tester 链接处理 | Security / Lifecycle | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-018) | — | — |
| `BR-APP-019` | 终态审计、幂等与最小披露 | Audit / Privacy | [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md#br-app-019) | — | — |
| `BR-APP-020` | 不可逆生命周期与稳定身份 | Lifecycle / Identity | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-020) | — | — |
| `BR-APP-021` | 关闭权限、明确确认与近期认证 | Authorization / Security | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-021) | — | — |
| `BR-APP-022` | CLOSING 即时本地隔离 | Lifecycle / Security | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-022) | — | — |
| `BR-APP-023` | OAuth 本地禁用与 Auth 永久撤销 | Security / Consistency | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-023) | — | — |
| `BR-APP-024` | 依附状态保留与待处理操作终止 | Lifecycle / Audit | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-024) | — | — |
| `BR-APP-025` | 配额、名称与 owner 义务 | Invariant / Consistency | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-025) | — | — |
| `BR-APP-026` | 持久收敛、幂等与未知结果 | Consistency / Idempotency | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-026) | — | — |
| `BR-APP-027` | 共享写栅栏与竞态 | Concurrency / Consistency | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-027) | — | — |
| `BR-APP-028` | 终态审计、隐私与错误边界 | Audit / Privacy | [UC-APP-027](use-cases/UC-APP-027-close-application.md#br-app-028) | — | — |

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
| `BR-VER-018` | 版本化 OAuth 回调 | Field / Security / Invariant | [UC-APP-002](use-cases/UC-APP-002-create-application-version.md#br-ver-018) | — | — |

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
| `BR-PUB-011` | Stable 管理权限 | Authorization | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-011) | — | — |
| `BR-PUB-012` | Stable 发布资格与直接发布 | Lifecycle / Eligibility | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-012) | — | — |
| `BR-PUB-013` | 公开默认目标边界 | Boundary / Resolution | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-013) | — | — |
| `BR-PUB-014` | 共享乐观并发与 no-op | Concurrency / Command Semantics | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-014) | — | — |
| `BR-PUB-015` | Stable PublicationHistory | Audit / Invariant | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-015) | — | — |
| `BR-PUB-016` | 设置前复检与 STABLE OAuth | Validation / Security | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-016) | — | — |
| `BR-PUB-017` | 清空、空记录与 Grey 基线 | Lifecycle / Invariant | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017) | — | — |
| `BR-PUB-018` | Stable 变化原子性 | Consistency / Concurrency | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-018) | — | — |
| `BR-PUB-019` | 不隐式扩散 | Boundary | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-019) | — | — |
| `BR-PUB-020` | Grey 管理权限与 Stable 基线 | Authorization / Invariant | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-020) | — | — |
| `BR-PUB-021` | Grey rollout 身份与比例 | Identity / Field / Invariant | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-021) | — | — |
| `BR-PUB-022` | Grey Version 发布资格 | Lifecycle / Eligibility | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-022) | — | — |
| `BR-PUB-023` | 确定性已登录用户分桶 | Resolution / Privacy | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-023) | — | — |
| `BR-PUB-024` | cohort 生命周期与最小披露 | Lifecycle / Security | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-024) | — | — |
| `BR-PUB-025` | 共享 OCC、变化分类与 no-op | Concurrency / Command Semantics | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-025) | — | — |
| `BR-PUB-026` | Grey PublicationHistory | Audit / Invariant | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-026) | — | — |
| `BR-PUB-027` | 按风险方向复检 | Validation / Availability | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-027) | — | — |
| `BR-PUB-028` | 清空与损坏状态 | Lifecycle / Invariant | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-028) | — | — |
| `BR-PUB-029` | Grey 变化原子性 | Consistency / Concurrency | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-029) | — | — |
| `BR-PUB-030` | 不隐式提升或扩散 | Boundary | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-030) | — | — |

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
| `BR-RUN-011` | 可信可选身份与匿名语义 | Identity / Security | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-011) | — | — |
| `BR-RUN-012` | Exact-major 与统一快照 | Resolution / Consistency | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-012) | — | — |
| `BR-RUN-013` | 兼容 Test 优先 | Resolution / Authorization | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-013) | — | — |
| `BR-RUN-014` | 服务端 Grey 选择 | Resolution / Privacy | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-014) | — | — |
| `BR-RUN-015` | Stable 公开回退 | Resolution / Boundary | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-015) | — | — |
| `BR-RUN-016` | 能力回退与不变量失败关闭 | Compatibility / Invariant | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-016) | — | — |
| `BR-RUN-017` | 唯一目标与最小披露 | Query Result / Privacy | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-017) | — | — |
| `BR-RUN-018` | 只读热路径 | Boundary / Availability | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-018) | — | — |
| `BR-RUN-019` | 并发快照语义 | Consistency / Concurrency | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-019) | — | — |
| `BR-RUN-020` | Catalog 复用与边界 | Boundary / Reuse | [UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-020) | — | — |

### Application Catalog (`BR-CAT`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-CAT-001` | Stable 支撑的普通公开候选 | Eligibility / Boundary | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-001) | — | — |
| `BR-CAT-002` | 可信可选身份 | Identity / Security | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-002) | — | — |
| `BR-CAT-003` | 复用唯一运行解析 | Resolution / Reuse | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-003) | — | — |
| `BR-CAT-004` | 最小公开 Profile | Query Result / Privacy | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-004) | — | — |
| `BR-CAT-005` | Filter 分发与客户端求值 | Boundary / Privacy | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-005) | — | — |
| `BR-CAT-006` | 列表与详情同一投影 | Query Contract | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-006) | — | — |
| `BR-CAT-007` | 稳定 keyset 分页 | Pagination / Consistency | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-007) | — | — |
| `BR-CAT-008` | 一致快照与失败关闭 | Consistency / Invariant | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-008) | — | — |
| `BR-CAT-009` | 批量只读热路径 | Performance / Boundary | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-009) | — | — |
| `BR-CAT-010` | 最小披露与私有缓存 | Privacy / Caching | [UC-APP-024](use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-010) | — | — |

### OAuth Client (`BR-OAC`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-OAC-001` | 应用归属与稳定接入身份 | Authorization / Boundary | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md#br-oac-001) | — | — |
| `BR-OAC-002` | Registration 与 Version 配置分离 | Authorization / Boundary | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md#br-oac-002) | — | — |
| `BR-OAC-003` | 高熵 secret 与一次披露 | Authorization / Boundary | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md#br-oac-003) | — | — |
| `BR-OAC-004` | 分离的并发版本与原子管理 | Authorization / Boundary | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md#br-oac-004) | — | — |
| `BR-OAC-005` | scope 与授权所有权 | Authorization / Boundary | [UC-APP-018](use-cases/UC-APP-018-manage-oauth-client.md#br-oac-005) | — | — |
| `BR-OAC-006` | 内部查询与最小披露 | Authorization / Boundary | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-006) | — | — |
| `BR-OAC-007` | TEST 资格与批准运行配置 | Authorization / Boundary | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-007) | — | — |
| `BR-OAC-008` | 一致快照与资格版本 | Authorization / Boundary | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-008) | — | — |
| `BR-OAC-009` | 展示来源与失败关闭 | Authorization / Boundary | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-009) | — | — |
| `BR-OAC-010` | 登录前回调校验与两阶段一致性 | Authorization / Consistency | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-010) | — | — |
| `BR-OAC-011` | Auth sector 的回调事实来源 | Boundary / Query | [UC-APP-019](use-cases/UC-APP-019-resolve-oauth-authorization-context.md#br-oac-011) | — | App 只返回批准回调事实。 |
| `BR-OAC-012` | STABLE OAuth channel 激活 | Boundary / Authorization | [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-oac-012) | — | UC020 接受后扩展 UC018/019 的现有模型，不建立第二套 registration。 |
| `BR-OAC-013` | GREY OAuth channel 与 cohort 资格 | Boundary / Authorization | [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md#br-oac-013) | — | 扩展 UC018/019 的现有模型，并由 Provider 重算用户 cohort。 |

### Application Filter (`BR-FLT`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-FLT-001` | Application 级公开展示策略 | Boundary / Policy | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-001) | — | — |
| `BR-FLT-002` | 无需审核的不可变 Revision | Lifecycle / Audit | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-002) | — | — |
| `BR-FLT-003` | 默认允许与显式 Clear | Command Semantics / Lifecycle | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-003) | — | — |
| `BR-FLT-004` | 类型化有界规则 | Field / Invariant | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-004) | — | — |
| `BR-FLT-005` | 字段目录解耦 | Boundary / Compatibility | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-005) | — | — |
| `BR-FLT-006` | 客户端确定性求值 | Client Contract / Privacy | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-006) | — | — |
| `BR-FLT-007` | Filter 不是安全边界 | Security / Boundary | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-007) | — | — |
| `BR-FLT-008` | OCC、no-op 与序号 | Concurrency / Command Semantics | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-008) | — | — |
| `BR-FLT-009` | 管理员与原子写栅栏 | Authorization / Consistency | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-009) | — | — |
| `BR-FLT-010` | 最小披露与不可变历史 | Audit / Privacy | [UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md#br-flt-010) | — | — |


## Architecture Decision Records

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `ADR-001` | Scope Catalog 权威来源与缓存 | `ACCEPTED` | [ADR-001-scope-catalog-cache.md](adr/ADR-001-scope-catalog-cache.md) | — | App Center 已实现有界缓存、失败关闭和 revision 对账。 |
| `ADR-002` | ApplicationPublication 按 RPC API major 分区 | `ACCEPTED` | [ADR-002-partition-publication-by-rpc-api-major.md](adr/ADR-002-partition-publication-by-rpc-api-major.md) | — | UC-APP-007/012/019 已按该分区实现并验证。 |
| `ADR-003` | Go package 与依赖边界 | `ACCEPTED` | [ADR-003-go-package-and-dependency-boundaries.md](adr/ADR-003-go-package-and-dependency-boundaries.md) | — | 代码仓库根目录的 architecture test 自动执行核心边界。 |
| `ADR-004` | MongoDB 事务与 Schema 管理 | `ACCEPTED` | [ADR-004-mongodb-transactions-and-schema-management.md](adr/ADR-004-mongodb-transactions-and-schema-management.md) | — | 显式 migration、事务重试与真实副本集验证已成为实现基线。 |
| `ADR-005` | 领域错误与 Transport 映射 | `ACCEPTED` | [ADR-005-domain-errors-and-transport-mapping.md](adr/ADR-005-domain-errors-and-transport-mapping.md) | — | 稳定 reason 与 HTTP/gRPC 映射已在现有纵切片统一使用。 |
| `ADR-006` | Proto v1 与独立 API 仓库协作 | `ACCEPTED` | [ADR-006-proto-v1-and-api-repository.md](adr/ADR-006-proto-v1-and-api-repository.md) | — | — |

## 注册表维护规则

- 新增 ID 时，必须同时更新对应的 Next ID。
- ID 改名时只修改标题，不修改编号。
- 权威正文退出活跃设计文档时，将其移入 `docs/app-center/archive/`，保留原 ID、标题和正文，并在同一次变更中更新“权威位置”链接。
- 标记为 `SUPERSEDED` 时，必须在“替代项”中填写新 ID；“备注”用于记录替代原因、迁移说明或其他必要上下文。
- 同一个 BR 被多个 UC 使用时，只保留一个权威位置；其他 UC 通过链接引用。
- BR 状态继承其权威正文所属 UC 的状态，注册表不单独保存 BR 状态。
- `类型` 用于检索和理解，不参与编号，也不改变权威规则正文。
