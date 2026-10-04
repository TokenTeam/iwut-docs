# App Center 首版设计

状态：`PROPOSED`

本目录从业务用例出发设计 App Center 的首个正式版本。旧实现已经雪藏，只作为历史需求证据，不是迁移来源，也不是当前模型的规范。

## 当前迭代

当前已经定义二十一个活跃纵切片；UC-APP-017 已被否决并归档，UC-APP-022 已接受并进入实现：

- `UC-APP-001`：开发者新建一个最小应用。
- `UC-APP-002`：当前管理员创建一个 DRAFT 应用版本。
- `UC-APP-003`：当前管理员以乐观并发控制完整替换 DRAFT 应用版本。
- `UC-APP-004`：当前管理员提交 DRAFT，并创建独立审核快照。
- `UC-APP-005`：无利益冲突的 reviewer 批准或拒绝一次审核。
- `UC-APP-006`：当前管理员处理最新拒绝并把 Version 恢复为 DRAFT。
- `UC-APP-007`：当前管理员把兼容的 APPROVED Version 放入一个 RPC major 的 test 槽位。
- `UC-APP-008`：当前管理员为整个 Application 创建或原子轮换 Tester 加入链接。
- `UC-APP-009`：已登录用户通过有效链接，在容量上限内成为整个 Application 的 Tester。
- `UC-APP-010`：当前管理员按 membershipId 移除一个 ACTIVE Tester episode，并释放容量。
- `UC-APP-011`：当前管理员按 joinLinkId 显式撤销加入链接，不创建替代链接或移除 Tester。
- `UC-APP-012`：App Center 为已认证 Tester 解析当前兼容的 test 启动目标。
- `UC-APP-013`：当前管理员创建只含公开显示名称和可空简介的 DRAFT ApplicationProfileRevision。
- `UC-APP-014`：当前管理员以乐观并发控制完整替换 DRAFT ApplicationProfileRevision。
- `UC-APP-015`：当前管理员提交 DRAFT ProfileRevision，创建独立 PENDING ProfileReview 快照并迁移为 SUBMITTED。
- `UC-APP-016`：无利益冲突的资料 reviewer 批准或拒绝 ProfileReview；批准后自动成为当前公开资料。
- `UC-APP-018`：当前管理员管理 Application＋channel 级稳定 OAuth client identity 与 confidential credential。
- `UC-APP-019`：App Center 通过 Auth-only 原生 gRPC 提供 OAuth client、运行配置、用户资格和批准回调事实。
- `UC-APP-020`：当前管理员设置、替换或清空 exact-major stable 槽位，并启用 STABLE OAuth channel。
- `UC-APP-021`：当前管理员在 Stable 基线上建立、调整、替换或清空确定性 Grey rollout。
- `UC-APP-022`：当前管理员设置或清空无需审核、立即发布的 Application Filter Revision。

本轮 Application 只有四个业务字段：

```text
id
name
adminId
createdAt
```

除此之外的字段和能力都必须由后续具体用例引入。

创建还需要一个独立的开发者应用配额记录，但它不是 Application 字段。初始配额暂定为 10。

面向用户公开的资料由独立且需要审核的 ApplicationProfileRevision 表达，不属于 Application 创建字段。UC-APP-013 已建立 displayName、可空 description 和可空不透明 icon 字符串；受控资产能力留待以后显式扩展。

UC-APP-002 为 Application 的持久化投影增加 nextVersionSequence 技术计数器，并为每个 Version 建立一对一依附的 ApplicationVersionOAuthConfig，但不增加 Application 业务字段。UC-APP-003 为 ApplicationVersion 增加 revision、updatedBy 和 updatedAt，并让依附 OAuth 配置共用该 revision。UC-APP-004 新增 ApplicationReview，UC-APP-005 为其增加一次性 decision，UC-APP-006 为被拒绝 Review 增加一次性 draftRestoration。UC-APP-007 新增按 RPC major 分区的 ApplicationPublication 与追加式 History。UC-APP-008 新增 Application 级 TesterJoinLink，UC-APP-009 新增最多 100 个 ACTIVE Tester 的 ApplicationTesterMembership，UC-APP-010 完成 Membership 的移除终态，UC-APP-011 完成加入链接的 MANUAL 撤销终态。UC-APP-012 只读组合这些事实并返回 TestLaunchDescriptor。UC-APP-013 新增 ApplicationProfileRevision，并为 Application 持久化投影增加 nextProfileRevisionSequence 技术计数器；同一 Application 的 DRAFT 或 SUBMITTED 共享唯一工作修订位。UC-APP-014 完成资料草稿的完整替换和乐观并发语义；UC-APP-015 新增独立 ApplicationProfileReview snapshot，并把资料草稿迁移为 SUBMITTED；UC-APP-016 定义独立资料审核权限、一次性 decision、批准后自动公开和 REJECTED 终态，并在决定时释放工作位。UC-APP-018/019 设计 Application＋channel 级稳定 OAuth registration、独立 credential 和按发布上下文解析 Version 配置；UC-APP-020/021 在 Publication 内增加 Stable 和 Grey 运行配置。这些用例仍不改变 Application 的四个业务字段。

## 文档入口

- [implements/README.md](implements/README.md)：新实现参与者和 agent 的首个阅读入口、当前工作范围与完成标准。
- [implementation-conventions.md](implements/implementation-conventions.md)：新实现的统一代码、测试、持久化、API 与 commit message 约定。
- [product-scope.md](product-scope.md)：首版端到端用户旅程、能力边界、Filter 含义和明确非目标。
- [capability-map.md](capability-map.md)：六项一级业务能力、事实流向、当前覆盖度和首版缺口。
- [domain-model.md](domain-model.md)：聚合、实体、值对象、领域服务及其关系。
- [lifecycle-models.md](lifecycle-models.md)：Version、ProfileRevision 与 Publication 的集中生命周期模型。
- [profile-management.md](query-contracts/profile-management.md)：Application Profile 管理员与 Reviewer 的读取语义。
- [vision.md](vision.md)：当前阶段的目标和非目标。
- [glossary.md](glossary.md)：当前已经出现的统一语言。
- [context-map.md](context-map.md)：当前已知的业务所有权和依赖。
- [document-conventions.md](document-conventions.md)：UC、BR、ADR 的命名、编号和状态规范。
- [design-registry.md](design-registry.md)：所有已分配 UC、BR、ADR 的完整注册表和权威位置。
- [open-questions.md](open-questions.md)：尚未决定、会影响后续设计的问题。
- [UC-APP-001-create-application.md](use-cases/UC-APP-001-create-application.md)：第一个完整纵切片。
- [UC-APP-002-create-application-version.md](use-cases/UC-APP-002-create-application-version.md)：创建 DRAFT ApplicationVersion。
- [UC-APP-003-update-draft-application-version.md](use-cases/UC-APP-003-update-draft-application-version.md)：完整替换 DRAFT ApplicationVersion。
- [UC-APP-004-submit-application-version-review.md](use-cases/UC-APP-004-submit-application-version-review.md)：提交 DRAFT 并创建 ApplicationReview 快照。
- [UC-APP-005-decide-application-version-review.md](use-cases/UC-APP-005-decide-application-version-review.md)：reviewer 批准或拒绝 ApplicationReview。
- [UC-APP-006-restore-rejected-version-to-draft.md](use-cases/UC-APP-006-restore-rejected-version-to-draft.md)：处理拒绝并恢复 DRAFT。
- [UC-APP-007-place-approved-version-in-test-slot.md](use-cases/UC-APP-007-place-approved-version-in-test-slot.md)：把 APPROVED Version 放入 test 槽位。
- [UC-APP-008-create-or-rotate-tester-join-link.md](use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)：创建或轮换 Application 级 Tester 加入链接。
- [UC-APP-009-join-application-as-tester.md](use-cases/UC-APP-009-join-application-as-tester.md)：已登录用户通过有效链接自助加入 Application Tester 列表。
- [UC-APP-010-remove-application-tester.md](use-cases/UC-APP-010-remove-application-tester.md)：当前管理员移除一个 ACTIVE Tester Membership episode。
- [UC-APP-011-revoke-tester-join-link.md](use-cases/UC-APP-011-revoke-tester-join-link.md)：当前管理员显式撤销 Tester 加入链接。
- [UC-APP-012-resolve-test-launch-target-for-tester.md](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md)：App Center 为 Tester 解析 test 启动目标。
- [UC-APP-013-create-application-profile-revision.md](use-cases/UC-APP-013-create-application-profile-revision.md)：当前管理员创建 DRAFT ApplicationProfileRevision。
- [UC-APP-014-update-draft-application-profile-revision.md](use-cases/UC-APP-014-update-draft-application-profile-revision.md)：完整替换 DRAFT ApplicationProfileRevision。
- [UC-APP-015-submit-application-profile-revision-review.md](use-cases/UC-APP-015-submit-application-profile-revision-review.md)：提交 DRAFT ProfileRevision 并创建 PENDING ProfileReview snapshot。
- [UC-APP-016-decide-application-profile-revision-review.md](use-cases/UC-APP-016-decide-application-profile-revision-review.md)：批准或拒绝 PENDING ProfileReview，批准后自动公开。
- [UC-APP-017 归档重建](archive/UC-APP-017-restore-rejected-profile-revision-to-draft.md)：被否决的资料恢复提案；现行规则改为新建独立修订。
- [UC-APP-018-manage-oauth-client.md](use-cases/UC-APP-018-manage-oauth-client.md)：管理稳定 OAuth client identity、状态和 confidential credential。
- [UC-APP-019-resolve-oauth-authorization-context.md](use-cases/UC-APP-019-resolve-oauth-authorization-context.md)：为 Auth 提供 OAuth client 与当前 TEST 运行上下文。
- [UC-APP-020-manage-stable-publication-slot.md](use-cases/UC-APP-020-manage-stable-publication-slot.md)：管理 stable 槽位并启用 STABLE OAuth channel。
- [UC-APP-021-manage-grey-rollout.md](use-cases/UC-APP-021-manage-grey-rollout.md)：管理 Stable 基线上的确定性 Grey rollout。
- [UC-APP-022-manage-application-filter.md](use-cases/UC-APP-022-manage-application-filter.md)：管理 Application 级客户端展示 Filter。
- [administrator-transfer.md](design-notes/administrator-transfer.md)：管理员转让的后续用例方向。
- [application-version.md](design-notes/application-version.md)：版本、审核和发布的拆分建议。
- [ADR-001-scope-catalog-cache.md](adr/ADR-001-scope-catalog-cache.md)：Scope Catalog 权威来源、缓存与消息策略。
- [ADR-002-partition-publication-by-rpc-api-major.md](adr/ADR-002-partition-publication-by-rpc-api-major.md)：Publication 为什么按 RPC API major 分区。
- [ADR-003-go-package-and-dependency-boundaries.md](adr/ADR-003-go-package-and-dependency-boundaries.md)：新实现的 Go package 组织和依赖方向。
- [ADR-004-mongodb-transactions-and-schema-management.md](adr/ADR-004-mongodb-transactions-and-schema-management.md)：MongoDB 事务拓扑、重试、迁移与集成测试边界。
- [ADR-005-domain-errors-and-transport-mapping.md](adr/ADR-005-domain-errors-and-transport-mapping.md)：协议无关领域错误及 HTTP/gRPC 映射。
- [ADR-006-proto-v1-and-api-repository.md](adr/ADR-006-proto-v1-and-api-repository.md)：Proto v1 命名空间与独立 API 仓库协作方式。

## 当前已接受与实现覆盖

UC-APP-001 至 UC-APP-016、UC-APP-018 至 UC-APP-022 均为 `ACCEPTED`；UC-APP-017 为 `SUPERSEDED`。设计状态不代表实现状态，逐项实现证据以 [implements/README.md](implements/README.md) 为准：UC-APP-002 至 UC-APP-005 仍受其登记的 Auth 生产依赖影响而为 `IN_PROGRESS`；UC-APP-022 是当前实现工作包；其余已接受活跃 UC 的当前后端工作包均为 `COMPLETE`。

OAuth/OIDC 的 App Center TEST 范围已经由 UC-APP-018/019 及 UC-APP-002 至 UC-APP-007 的 Version OAuth 扩展交付，UC-APP-020/021 已启用 STABLE/GREY。Auth 的 consent、code、token、grant、sector 和 sub 继续由 Auth Center 拥有。
