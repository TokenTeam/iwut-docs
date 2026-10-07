# Application Profile 管理与审核查询契约

状态：`PROPOSED`（管理员查询）；Reviewer 查询已由 UC-APP-031 接受并交付

## 定位

本文档定义 Application Profile 管理和审核的应用层读取语义。它介于网页端与读模型之间，回答“谁可以读取哪些业务事实，结果表示什么”。

本文档包含四个查询：

```text
ListApplicationProfileRevisionsForAdmin
GetApplicationProfileRevisionForAdmin
ListPendingApplicationProfileReviews
GetApplicationProfileReviewForReviewer
```

这些查询不改变领域状态，不产生新的 ProfileRevision、ProfileReview、decision 或审计事实。它们也不定义 HTTP/RPC、JSON 序列化、数据库、索引、缓存或页面布局。

管理员列表/详情仍是候选查询语义。Reviewer 队列/详情已由 [UC-APP-031](../use-cases/UC-APP-031-query-application-profile-reviews.md) 及 `BR-PRF-041`–`046` 固化，本文只作导航，不再单独扩展其规则。状态、权限和不变量继续以 UC-APP-013–016、UC-APP-031 中的 `BR-PRF-*` 为权威正文；本契约如与 BR 冲突，以 BR 为准。

## 共享约定

### 可信身份

管理员查询使用：

```text
AuthenticatedIdentity {
  authId
}
```

管理员读取权来自 Application 当前 `adminId`。查询不使用 developerStatus 代替所有权检查；Developer 资格影响写命令，不改写已有 Application 的当前管理关系。

Reviewer 查询使用：

```text
ReviewerIdentity {
  authId
  permissions
}
```

Reviewer 查询只接受包含 `app.profile.review` 的可信身份。`app.version.review` 不隐式授予资料审核读取权，与 [BR-PRF-023](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-023) 保持一致。

### 身份隐藏

管理员查询中，Application 不存在、ProfileRevision 不属于 Application，或调用者不是当前 admin，都返回同一类 `ApplicationProfileNotFound` 结果，避免向非管理员暴露资料是否存在。

Reviewer 查询先检查可信身份和 `app.profile.review`，再读取审核事实。缺少权限返回 `ApplicationProfileReviewPermissionRequired`；Review 不存在或引用路径不一致返回 `ApplicationProfileReviewNotFound`。

### 分页

列表查询使用不透明 cursor，不使用可受并发插入影响的页码偏移。

```text
PageRequest {
  cursor?
  limit: 1..100 = 20
}

Page<T> {
  items: T[]
  nextCursor?
  asOf
}
```

`asOf` 表示该页结果所依据的读取时点，不是业务审计时间。cursor 的编码不对调用者承诺。

### 一致性

- 尚未交付的管理员列表可来自读投影，允许短暂滞后，并返回 `asOf`。
- UC-APP-031 的 Reviewer 单页和详情在同一个 MongoDB snapshot 中构造，不允许以投影滞后隐藏不变量损坏。
- 详情查询从 App Center 权威事实构造单个内部一致的快照。
- 查询结果不是写入授权。UC-APP-014、015 和 016 在执行时继续校验当前 admin、状态、revision、利益冲突和公开指针前置值。

## 管理员查询

### ListApplicationProfileRevisionsForAdmin

用途：为 Application 管理页提供公开资料修订列表。

输入：

```text
ListApplicationProfileRevisionsForAdmin {
  applicationId
  reviewStatus?: DRAFT | SUBMITTED | APPROVED | REJECTED
  page: PageRequest
}
```

结果按 `sequence DESC` 排序；sequence 在单个 Application 内唯一，因此排序稳定。

```text
AdminProfileRevisionSummary {
  profileRevisionId
  sequence
  reviewStatus
  displayName
  description
  icon
  revision
  createdAt
  updatedAt
  isCurrentWorkingRevision
  isCurrentPublished
  latestReview?: {
    profileReviewId
    attempt
    status
    submittedAt
    decidedAt?
    outcome?
  }
}
```

description 返回完整纯文本，不由查询契约截断。页面如需摘要，由展示层处理。

### GetApplicationProfileRevisionForAdmin

用途：查看修订内容、审核历史和当前协调状态；该结果也是网页端重新编辑被拒绝内容的数据来源。

输入：

```text
GetApplicationProfileRevisionForAdmin {
  applicationId
  profileRevisionId
}
```

返回：

```text
AdminProfileRevisionDetail {
  applicationId
  profileRevisionId
  sequence
  reviewStatus
  revision
  content: {
    displayName
    description
    icon
  }
  audit: {
    createdBy
    createdAt
    updatedBy
    updatedAt
    submittedBy?
    submittedAt?
  }
  profileState: {
    workingProfileRevisionId?
    currentPublishedProfileRevisionId?
  }
  reviews: AdminProfileReviewSummary[]
}

AdminProfileReviewSummary {
  profileReviewId
  attempt
  status
  sourceRevision
  submittedAt
  decision?: {
    outcome
    reason?
    policyVersion
    decidedAt
  }
}
```

`reviews` 按 `attempt ASC` 返回完整历史。管理员视图返回可向开发者展示的审核结果和 reason，不返回 `confirmedCheckIds`、Reviewer 内部备注或其他内部审核信息。

对 REJECTED Revision，结果照常包含完整 `content`。网页端可以将其复制到本地表单，然后调用 [UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md) 创建全新 DRAFT。该查询不返回复制 token，也不生成服务端恢复能力，与 [BR-PRF-031](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) 保持一致。

## Reviewer 查询

### ListPendingApplicationProfileReviews

用途：为资料 Reviewer 提供 PENDING 审核队列。

输入：

```text
ListPendingApplicationProfileReviews {
  applicationId?
  page: PageRequest
}
```

结果只包含 status=`PENDING` 且所属 Application 生命周期为 ACTIVE 的 ApplicationProfileReview；平台 SUSPENDED 不排除审核，CLOSING/CLOSED 排除。结果按 `submittedAt ASC, profileReviewId ASC` 排序，使较早提交稳定地排在前面。

```text
PendingProfileReviewSummary {
  applicationId
  applicationName
  profileRevisionId
  sequence
  profileReviewId
  attempt
  displayName
  submittedAt
  decisionEligibility: {
    eligible
    conflicts: (CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER)[]
  }
}
```

队列不隐藏利益冲突项，而是返回根据查询时当前事实计算的 `decisionEligibility`，使 Reviewer 能够理解为何无法处理某项。该字段只是界面提示；[UC-APP-016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md) 在写入 decision 时重新计算利益冲突。

### GetApplicationProfileReviewForReviewer

用途：返回 Reviewer 完成一次审核所需的快照、当前状态和策略输入，或查看已作出的决定。

输入：

```text
GetApplicationProfileReviewForReviewer {
  applicationId
  profileRevisionId
  profileReviewId
}
```

返回：

```text
ReviewerProfileReviewDetail {
  application: {
    applicationId
    name
    adminId
    lifecycleStatus
    platformAvailabilityStatus
  }
  profileRevision: {
    profileRevisionId
    sequence
    reviewStatus
    revision
    createdBy
  }
  review: {
    profileReviewId
    attempt
    status
    sourceRevision
    snapshot: {
      displayName
      description
      icon
    }
    submittedBy
    submittedAt
    decision?
  }
  decisionEligibility: {
    eligible
    conflicts: (CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER)[]
  }
  currentPolicy: {
    version
    requiredCheckIds
  }
  asOf
}
```

`currentPolicy` 来自查询时唯一 ACTIVE 的不可变 ProfileReviewPolicy。Reviewer 将实际阅读的 version 作为 `expectedPolicyVersion` 传给 UC-APP-016。如果在查询后发生策略、Revision、管理员或当前公开指针变化，UC-APP-016 通过自己的前置条件拒绝过期决定。

已决定 Review 保留 decision 供审计查看。查询本身不领取、锁定、分配或标记审核任务。

## 明确不提供的查询行为

- 没有“复制被拒绝 ProfileRevision”的服务端 Query。
- 没有返回复制 token、sourceProfileRevisionId 或预绑定新草稿的查询。
- 没有在查询时隐式创建 DRAFT、改变 Review 状态或写入“已读”审计。
- 普通用户读取当前公开 Profile 已由 UC-APP-024 的 Catalog 查询交付，不属于本文档。

## 验收要点

- 当前 admin 可以列出和读取自己 Application 下所有状态的 ProfileRevision，包括 REJECTED 完整内容。
- 非当前 admin 无法通过管理员查询区分 Application 或 Revision 是否存在。
- 具有 `app.profile.review` 的 Reviewer 可以读取 PENDING 队列和审核详情，并看到查询时的利益冲突提示。
- Reviewer 详情在可决定时返回构造 UC-APP-016 Command 所需的并发前置值和审核策略。
- 列表排序和 cursor 分页在并发插入下保持稳定；详情内的 Review、Revision、Profile 指针和策略来自一个内部一致快照。
- 所有查询都是无副作用的读取；最终写入权限与并发检查仍由对应 Command UC 承担。
- icon 作为可空不透明字符串原样返回；查询层不验证其指向内容，也不获取外部资产。
