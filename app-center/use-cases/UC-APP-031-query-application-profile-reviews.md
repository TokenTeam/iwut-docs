# UC-APP-031：查询 ApplicationProfileRevision 审核队列与审核详情

状态：`ACCEPTED`

## 目标与范围

> 具备 `app.profile.review` 的 Reviewer 查询待处理公开资料审核队列，并读取一次资料审核的不可变详情。

本用例将 [资料管理与审核查询契约](../query-contracts/profile-management.md) 中的 Reviewer 查询交付为正式 API。管理员 ProfileRevision 列表/详情仍是独立管理查询范围；本用例不实现分配、锁单、SLA、通知、申诉或恢复被拒绝修订。

## 身份与精确权限

两个查询只接受可信 USER 身份和 `app.profile.review`。`app.version.review`、Application 管理员或 Developer 资格都不隐式授予权限。权限检查先于对象查找。

缺少身份返回 `ReviewerIdentityRequired`；缺少精确权限返回 `ApplicationProfileReviewPermissionRequired`。

## 待处理队列

```text
ListPendingApplicationProfileReviewsQuery {
  applicationId?
  pageSize: 1..100 = 20
  pageToken?
}
```

队列只包含 `ApplicationProfileReview.status=PENDING` 且所属 Application `lifecycleStatus=ACTIVE` 的记录。`SUSPENDED` 不阻止审核；`CLOSING/CLOSED` 按 UC027 排除。

按 `(submittedAt ASC, profileReviewId ASC)` 稳定 keyset 分页。队列项包含 Application ID/name、ProfileRevision ID/sequence/displayName、ProfileReview ID/attempt、submittedAt，以及查询时计算的：

```text
decisionEligibility {
  eligible
  conflicts: CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER []
}
```

冲突项不从队列隐藏。eligibility 是界面提示，UC016 的决定事务仍重新计算。

## 审核详情

详情路径中的 `applicationId/profileRevisionId/profileReviewId` 必须匹配。结果包含：

```text
ApplicationProfileReviewDetail {
  application { applicationId, name, adminId, lifecycleStatus, platformAvailabilityStatus }
  profileRevision { profileRevisionId, sequence, reviewStatus, revision, createdBy }
  review {
    profileReviewId, attempt, status, sourceRevision,
    snapshot { displayName, description, icon },
    submittedBy, submittedAt, decision?
  }
  currentPolicy { version, requiredCheckIds }
  decisionEligibility
  asOf
}
```

内容必须取不可变 Review snapshot。终态 Review 可按 ID 读取。当前 policy 第一版为 `app-profile-review-v1` 及其固定检查项，但查询结果不替代 UC016 在写入时对 expected policy 和 confirmed checks 的复查。

## 一致性与错误

单页和详情在 MongoDB majority snapshot 中构造。Application、ProfileRevision、Review 的引用、sourceRevision 或 snapshot 不一致时返回 `ApplicationProfileReviewStateInconsistent` / INTERNAL；不能省略坏项或回退到当前 ProfileRevision 内容。

不存在或路径不匹配返回 `ApplicationProfileReviewNotFound`。合法空队列成功返回空页。pageSize/pageToken 非法返回 INVALID_ARGUMENT。响应使用 `private, no-store`。

## 最小查询模型与索引

复用或补齐 `(status, submittedAt, profileReviewId)` 索引。read port 独立于决定 repository；队列通过批量 lookup 读取 Application 和 ProfileRevision，禁止 N+1。

## API 草图

```text
rpc ListPendingApplicationProfileReviews(...)
  POST /v1/reviews/application-profiles:search body=query

rpc GetApplicationProfileReview(...)
  GET /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}
```

## 验收场景

1. 只有精确 `app.profile.review` 可读取；Version Reviewer 单独权限不足。
2. PENDING+ACTIVE 入队；CLOSING/CLOSED 排除；SUSPENDED 保留。
3. applicationId filter、升序 keyset、tie-break 与 token 绑定稳定。
4. 当前管理员、revision creator、submitter 冲突被完整提示而不隐藏队列项。
5. 详情返回 immutable snapshot 与当前固定 policy/checks。
6. 终态 Review 可查询但不进入 pending 队列。
7. 路径不匹配统一 NOT_FOUND；无权限先失败。
8. sourceRevision/snapshot/引用损坏返回 INTERNAL，不产生部分结果。
9. HTTP 与原生 gRPC 一致，真实 MongoDB 验证索引与 snapshot 行为。

## 实现依赖与交付边界

ProfileRevision、ProfileReview、固定 policy 和决定流程均已交付。现有查询契约提供读取语义；本工作包新增 API、read port/usecase、Mongo query、必要索引、transport/wiring 和验收，不改变 UC013–016 写模型。

## 业务规则

<a id="br-prf-041"></a>
### BR-PRF-041：Profile Reviewer 查询精确授权

资料审核队列与详情只接受具备 `app.profile.review` 的可信 Reviewer，权限检查先于对象查找。

<a id="br-prf-042"></a>
### BR-PRF-042：待处理资料队列资格

队列只包含 PENDING 且 Application 生命周期 ACTIVE 的资料 Review；SUSPENDED 保留，CLOSING/CLOSED 排除。

<a id="br-prf-043"></a>
### BR-PRF-043：资料审核快照权威

队列摘要和详情的内容来自提交时不可变 snapshot，不能用当前 ProfileRevision 替换。

<a id="br-prf-044"></a>
### BR-PRF-044：利益冲突提示不替代决定检查

查询计算的 eligibility 只用于 Reviewer 界面；UC016 在决定事务中重新计算全部冲突和前置条件。

<a id="br-prf-045"></a>
### BR-PRF-045：稳定资料队列分页

队列按 `(submittedAt, profileReviewId)` 升序 keyset 分页，token 绑定 Reviewer 与 filter。

<a id="br-prf-046"></a>
### BR-PRF-046：资料审核查询失败关闭

引用、sourceRevision 或 snapshot 损坏导致整次查询 INTERNAL；不能跳项、降级或返回部分详情。

## 变更记录

- 2026-10-07：将既有 PROPOSED Reviewer 查询语义收敛为正式工作包，设计进入 `ACCEPTED`。
