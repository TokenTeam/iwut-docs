# App Center Lifecycle Models

状态：`PROPOSED`

## 文档目的

本文集中描述三个主要生命周期：ApplicationVersion、ApplicationProfileRevision 和 ApplicationPublication。它与 [Domain Model](domain-model.md) 配合阅读，不定义 HTTP、数据库或代码结构。

图中的“当前”迁移已经有 UC 和 BR 权威正文；“目标”迁移来自 [首版产品范围](product-scope.md)，仍需要未来 UC 建立具体业务规则。

## ApplicationVersion 生命周期

### 状态图

```text
                         APPROVE
                    ┌──────────────► APPROVED
                    │                    │
CREATE               │                    └── [目标：REVOKE] ──► REVOKED
  │                  │
  ▼      SUBMIT      │
DRAFT ───────────► SUBMITTED
  ▲                  │
  │                  │ REJECT
  │                  ▼
  └──── RESTORE ── REJECTED
```

草稿内容更新是 `DRAFT -> DRAFT` 的真实修改；内容未变化的更新是 no-op。Test/Grey/Stable 槽位变化不会改变 Version 状态。

### 当前迁移

| 行为 | From | To | 主要事实 | 权威规则 |
| --- | --- | --- | --- | --- |
| Create Version | 不存在 | DRAFT | 分配身份、sequence 和初始 revision | [BR-VER-008](use-cases/UC-APP-002-create-application-version.md#br-ver-008)、[BR-VER-009](use-cases/UC-APP-002-create-application-version.md#br-ver-009) |
| Replace Draft | DRAFT | DRAFT | 完整替换受审核内容；真实变化增加 revision | [BR-VER-010](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-010)、[BR-VER-013](use-cases/UC-APP-003-update-draft-application-version.md#br-ver-013) |
| Submit Review | DRAFT | SUBMITTED | 创建不可变 Review snapshot 与 PENDING attempt | [BR-REV-002](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-002)、[BR-REV-009](use-cases/UC-APP-004-submit-application-version-review.md#br-rev-009) |
| Approve Review | SUBMITTED | APPROVED | Review 与 Version 同时得到 APPROVED 结果 | [BR-REV-013](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) |
| Reject Review | SUBMITTED | REJECTED | Review 与 Version 同时得到 REJECTED 结果 | [BR-REV-013](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) |
| Restore Draft | REJECTED | DRAFT | 保留拒绝决定，追加一次性 restoration | [BR-REV-023](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-023)、[BR-REV-025](use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-025) |

每次重新提交创建新的 ApplicationReview attempt，历史 snapshot 和 decision 保持不变。APPROVED 只表示具备发布候选资格，不会自动进入任何发布槽位，参见 [BR-REV-019](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-019)。

### 目标扩展

首版上线前还需要定义 APPROVED 资格如何被显式撤销。建议用 `APPROVED -> REVOKED` 表达未来禁止新发布和运行解析的终态，同时由独立处置行为决定如何清理仍引用该 Version 的 Publication。

该目标迁移尚无 BR。它需要先回答：谁可以撤销、是否允许恢复、现有 test/grey/stable 指针如何处理，以及紧急处置与普通审核纠错是否使用同一行为。

## ApplicationProfileRevision 生命周期

### 当前与目标状态图

```text
                         APPROVE
                    ┌──────────────► APPROVED
                    │
CREATE              │
  │                 │
  ▼      SUBMIT     │
DRAFT ─────────► SUBMITTED
                    │
                    │ REJECT
                    ▼
                 REJECTED (terminal)

DRAFT ── REPLACE ──► DRAFT
```

### 当前迁移

| 行为 | From | To | 主要事实 | 权威规则 |
| --- | --- | --- | --- | --- |
| Create Profile Revision | 不存在 | DRAFT | 分配身份、sequence；同一 Application 当前只有一份 DRAFT/SUBMITTED 工作修订 | [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)、[BR-PRF-007](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-007) |
| Replace Draft | DRAFT | DRAFT | 完整替换资料；真实变化增加 revision | [BR-PRF-008](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-008)、[BR-PRF-011](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-011) |
| Submit Profile Review | DRAFT | SUBMITTED | 冻结完整资料 snapshot，创建独立 PENDING Review attempt | [BR-PRF-018](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-018)、[BR-PRF-021](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-021) |
| Approve Profile Review | SUBMITTED | APPROVED | 一次性决定，并原子成为当前公开资料 | [BR-PRF-026](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-026)、[BR-PRF-030](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030) |
| Reject Profile Review | SUBMITTED | REJECTED | 保存一次性决定与拒绝理由，原公开资料不变 | [BR-PRF-027](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-027)、[BR-PRF-031](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) |

当前 BR 已定义从 DRAFT 创建、更新、提交，到批准或拒绝的完整审核流程。REJECTED 是终态；ProfileRevision 不承担紧急隐藏状态。

### 紧急隐藏不属于本状态机

公开资料的紧急隐藏被归为 Application 级禁用，而不是 `APPROVED -> REVOKED` 的 ProfileRevision 迁移。后续 Application Ownership 用例需要定义 admin/SysAdmin 权限、审计、对 Catalog 和运行解析的影响以及重新启用规则。ProfileRevision 与既有审核决定仍保留用于审计。

已定义的普通资料审核使用独立 `app.profile.review` 权限，不继承 Version Review 权限，也不授予 Application 禁用权限。

### 审核批准与自动公开

当前模型保留审核状态和当前公开指针两个事实，但在一个操作中同时改变它们。Profile Review 批准时：

```text
ProfileReview.status = APPROVED
ProfileRevision.reviewStatus = APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = approved revision
```

首版不提供独立 Publish 命令，也不提供选择旧 Revision 或回滚公开资料的操作。新 Revision 被批准时直接替换当前公开指针；新 Revision 被拒绝时，旧公开资料继续生效。

网页端如果要继续编辑被拒绝内容，会将其预填到新建表单，再通过 UC-APP-013 产生一个全新 DRAFT。这不是 `REJECTED -> DRAFT` 迁移，App Center 也不保存复制来源。

旧 Revision、Review snapshot 和 decision 继续保留用于审计。Application 被禁用时是否保留公开指针作为内部事实，由后续禁用用例决定；当前资料生命周期不做隐式回退。

SUBMITTED 继续占用 `workingProfileRevisionId`，审核决定清空它；因此 PENDING 期间不能创建下一份 DRAFT。icon 当前只是可空不透明字符串，外部内容失效不触发 App Center 生命周期迁移。两项规则分别见 [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006) 与 [BR-PRF-005](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005)。

## ApplicationPublication 生命周期

### Publication 不是线性版本状态机

ApplicationPublication 表示 `(applicationId, rpcApiMajor)` 当前的服务端发布配置。Test、Grey、Stable 是三个相互独立的槽位，不是 ApplicationVersion 的三个状态，也不是强制依次迁移的单一路径。

```text
ApplicationPublication(applicationId, rpcApiMajor)
  test:   EMPTY <──── set / replace / clear ────> VersionId
  grey:   EMPTY <── set / adjust / replace / clear ─> GreyRollout
  stable: EMPTY <──── set / replace / clear ────> VersionId

every real change
  revision + 1
  append PublicationHistory
```

当前权威设计已覆盖设置 Test 和 Stable 的设置/替换/清空；[UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md) 提出 Grey 的 set/adjust/replace/clear。槽位共享 Publication revision，并且一个槽位的命令不自动改变其他槽位，参见 [BR-PUB-006](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-006)、[BR-PUB-019](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-019) 与提案 [BR-PUB-030](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-030)。

### Publication 记录生命周期

| 阶段 | 含义 | 当前状态 |
| --- | --- | --- |
| ABSENT | 该 Application 与 RPC major 尚无 Publication | 已由首次设置 test 的预期 revision 语义间接定义 |
| CONFIGURED | 至少一个槽位存在 | Test/Stable 已实现；Grey 由 UC-APP-021 提案定义 |
| EMPTY | Publication 保留 revision 与历史，但所有槽位为空 | UC-APP-020 已接受由 clear stable 形成并保留空记录 |
| SUSPENDED | 平台临时停止该分区分发，但保留槽位 | 候选方案；尚未决定是否需要独立状态 |

首版需要在两种停止分发模型中作出选择：清空相关槽位，或者增加独立 SUSPENDED 状态。前者模型更小但恢复需要重新设置指针；后者恢复更直接，但增加权限、原因、期限和解析规则。

### 槽位变化

| 行为 | 影响 | 当前或目标 |
| --- | --- | --- |
| Set/Replace Test | 只改变 testVersionId | 当前已有设置/替换；clear 待设计 |
| Set/Adjust/Replace Grey | 设置目标 Version、万分比与稳定 cohort | UC-APP-021 提案 |
| Clear Grey | 停止灰度选择，保留 stable | UC-APP-021 提案 |
| Set/Replace Stable | 改变普通公开访问默认 Version | UC-APP-020 已接受；允许直接设置，不强制先经过 test/grey |
| Clear Stable | 停止普通公开访问；test 可以继续，grey 存在时拒绝 | UC-APP-020 已接受 |
| Roll Back | 将某一槽位重新指向仍具资格的历史 Version | UC-APP-020 已确认 stable 回退是普通受审计 replace |

所有槽位继续引用同一 Application、兼容当前 rpcApiMajor 且具有发布资格的 Version。Test 资格规则见 [BR-PUB-003](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003)，Stable 见 [BR-PUB-012](use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-012)，Grey 提案见 [BR-PUB-022](use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-022)。

“Test → Grey → Stable”描述常见发布旅程，不表示数据库中的自动状态推进。Stable 和 Grey 都不要求目标 Version 曾进入 Test；各槽位命令不做隐式提升。

### 服务端解析

目标服务端解析顺序为：

```text
if ACTIVE Tester Membership and compatible test exists:
    test
else if stable exists and grey rollout matches and compatible grey exists:
    grey
else if compatible stable exists:
    stable
else:
    unavailable
```

第一条 test-only 路径已有 [BR-RUN-001](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001) 至 [BR-RUN-005](use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005) 支持。Grey 分桶输入、比例单位、seed 生命周期和 rollout 调整语义尚待定义。

普通用户目录还需要当前已发布 Profile。Filter 不参与上述服务端槽位解析：服务端随候选 Application 返回 Filter 规则，客户端使用本地用户信息决定最终展示。

## 三个生命周期的关系

```text
ApplicationVersion APPROVED
        │ eligible reference
        ▼
ApplicationPublication slot ─────┐
                                 ├─► Catalog candidate + launch target
Published ProfileRevision ───────┘

Tester Membership ── enables test branch
Grey rollout ─────── server-side branch
Filter rule ──────── client-side display only
```

| 变化 | 不会隐式引起的变化 |
| --- | --- |
| Version 被批准 | 不自动设置 test/grey/stable，不自动公开 Profile |
| 设置或替换发布槽位 | 不修改 Version 审核状态，不修改 Profile |
| Profile 被批准并自动公开 | 不创建 stable，不选择运行 Version |
| 更换 test Version | 不移除 Tester Membership |
| 修改 Filter 规则 | 不改变服务端发布槽位或服务端授权 |

已有约束继续以 [BR-REV-019](use-cases/UC-APP-005-decide-application-version-review.md#br-rev-019)、[BR-PUB-004](use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-004) 和 Tester 相关 BR 为权威来源；未来关系需要在各自 UC 中分配新 BR。

## 后续设计顺序

生命周期缺口适合按依赖顺序补齐，但暂不在本文分配 UC 编号：

1. 评审并实现 [UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md)，随后设计 test clear。
2. Application 归档、普通停用与平台紧急 suspension。
3. 统一服务端启动目标解析与 Catalog Query Contract。
4. 独立 FilterRevision 的归属、审核/发布方式和客户端求值契约。
5. Public Profile 的普通用户对外查询契约；受控 icon 资产语义留待真实需求出现后扩展。
6. APPROVED Version 的资格撤销及引用处置。

在这些边界确定前，不需要继续按顺序预写二十多个完整 UC。
