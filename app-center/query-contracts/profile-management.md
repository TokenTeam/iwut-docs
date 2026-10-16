# Application Profile 管理与审核查询契约

状态：`ACCEPTED`；管理员查询由 UC-APP-039 接受，Reviewer 查询由 UC-APP-031 接受并交付

## 定位

本文档定义 Application Profile 管理和审核的应用层读取语义。它介于网页端与读模型之间，回答“谁可以读取哪些业务事实，结果表示什么”。

本文档包含四个查询：

```text
ListApplicationProfileRevisions
GetApplicationProfileRevision
ListPendingApplicationProfileReviews
GetApplicationProfileReviewForReviewer
```

这些查询不改变领域状态，不产生新的 ProfileRevision、ProfileReview、decision 或审计事实。它们也不定义 HTTP/RPC、JSON 序列化、数据库、索引、缓存或页面布局。

管理员列表/详情已由 [UC-APP-039](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md) 及 BR-PRF-047–056 接受。Reviewer 队列/详情由 [UC-APP-031](../use-cases/UC-APP-031-query-application-profile-reviews.md) 及 BR-PRF-041–046 固化。本文作查询导航，业务语义以对应 UC/BR 为唯一权威；不重复维护另一套投影定义。

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

管理员查询中，Application 不存在、ProfileRevision 不属于 Application，或调用者不是当前 admin，都返回同一类 `ApplicationProfileManagementNotFound` 结果，避免向非管理员暴露资料是否存在。

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

- UC-APP-039 管理员列表与详情在同一个 MongoDB majority read-only snapshot 中构造，不使用滞后投影。
- UC-APP-031 的 Reviewer 单页和详情在同一个 MongoDB snapshot 中构造，不允许以投影滞后隐藏不变量损坏。
- 详情查询从 App Center 权威事实构造单个内部一致的快照。
- 查询结果不是写入授权。UC-APP-014、015 和 016 在执行时继续校验当前 admin、状态、revision、利益冲突和公开指针前置值。

## 管理员查询

[ListApplicationProfileRevisions](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md#列表投影) 提供状态过滤、私有签名 keyset、完整内容摘要、当前工作/公开指针与最小最新审核摘要。

[GetApplicationProfileRevision](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md#详情与审核历史) 提供完整当前内容、createdBy/必要时间、协调状态、最新 Review 与一页可遍历的审核历史。REJECTED 原文保留，前端重新编辑仍调用普通创建命令。

管理员查询的生命周期可见性、ownership-bound token、历史分页、2 MiB 响应预算、错误和隐私字段以 UC039 为准；不返回 updatedBy/submittedBy/Reviewer 身份、snapshot 正文、内部检查或当前 policy。历史不作为一份无界数组返回。所有响应 private, no-store，查询没有写副作用。

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
  currentPublishedProfile: { oneof state { none | published { profileRevisionId, displayName, description?, icon? } } }
  currentPolicy: {
    version
    requiredCheckIds
  }
  asOf
}
```

`currentPolicy` 来自查询时唯一 ACTIVE 的不可变 ProfileReviewPolicy。Reviewer 将实际阅读的 version 作为 `expectedPolicyVersion` 传给 UC-APP-016。如果在查询后发生策略、Revision、管理员或当前公开指针变化，UC-APP-016 通过自己的前置条件拒绝过期决定。

当前公开资料投影的 presence、授权、snapshot、失败关闭与指针 CAS 交互以 [UC031 当前公开资料投影](../use-cases/UC-APP-031-query-application-profile-reviews.md#当前公开资料投影) 为准。`none` 必须显式返回；不能把缺字段或 Catalog 不可见当作 NONE。

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
- 列表排序和 cursor 分页在并发插入下保持稳定；管理员详情内的 Review、Revision、Profile 指针来自一个一致快照，Reviewer 详情另外包括其权限允许读取的当前策略。
- 所有查询都是无副作用的读取；最终写入权限与并发检查仍由对应 Command UC 承担。
- icon 作为可空不透明字符串原样返回；查询层不验证其指向内容，也不获取外部资产。
