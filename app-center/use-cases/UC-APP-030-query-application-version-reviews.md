# UC-APP-030：查询 ApplicationVersion 审核队列与审核详情

状态：`ACCEPTED`

## 目标与范围

> 具备 `app.version.review` 的 Reviewer 查询待处理 ApplicationVersion 审核队列，并读取完成或审计一次审核所需的不可变详情。

本用例只读取 [UC-APP-004](UC-APP-004-submit-application-version-review.md) 建立的 `ApplicationReview` 和 [UC-APP-005](UC-APP-005-decide-application-version-review.md) 写入的决定。它不改变 Review，不提供分配、抢单、锁单、SLA、通知、申诉或自动裁决。

## 身份与精确权限

两个查询都要求可信 USER 身份和精确权限 `app.version.review`。`app.profile.review`、管理员身份或 Developer 资格不隐式授予读取权。缺少身份返回 `ReviewerIdentityRequired`；缺少权限返回 `ApplicationReviewPermissionRequired`。

权限先于业务对象查找检查，避免无权限调用者根据 NOT_FOUND 枚举审核事实。

## 待处理队列

输入：

```text
ListPendingApplicationVersionReviewsQuery {
  applicationId?
  pageSize: 1..100 = 20
  pageToken?
}
```

队列只包含 `ApplicationReview.status=PENDING` 且所属 Application `lifecycleStatus=ACTIVE` 的记录。平台 `SUSPENDED` 不移除审核项；暂停期间管理员仍可修复配置，Reviewer 仍可完成审核。`CLOSING/CLOSED` 项按 UC027 从队列排除。

结果按 `(submittedAt ASC, reviewId ASC)` 排序，使用绑定 Reviewer、可选 applicationId filter 与最后 key 的不透明 keyset token。队列项包含：Application ID/name、Version ID/label、Review ID/attempt、submittedBy/submittedAt，以及根据查询时事实计算的 `decisionEligibility`。

`decisionEligibility` 的 conflicts 为 `CURRENT_ADMIN | VERSION_CREATOR | REVIEW_SUBMITTER`。冲突项仍显示在队列，便于解释无法处理的原因；它只是提示，UC005 决定事务必须重新计算。

## 审核详情

详情输入 `applicationId/versionId/reviewId`，三者必须匹配同一 Review，否则统一 `ApplicationReviewNotFound`。

返回：

```text
ApplicationVersionReviewDetail {
  application { applicationId, name, adminId, lifecycleStatus, platformAvailabilityStatus }
  version { versionId, sequence, reviewStatus, revision, createdBy }
  review {
    reviewId, attempt, status, sourceVersionRevision,
    snapshot, scopeCatalogRevision, preflightPolicyVersion,
    submittedBy, submittedAt, draftRestoration?, decision?
  }
  currentPolicy { version, requiredCheckIds }
  decisionEligibility
  asOf
}
```

审核内容只能取 `ApplicationReview.snapshot`，不能用当前可变 Version 字段替换。终态 Review 仍可读取以支持审计。当前 policy 用于渲染下一次决定输入；它不是授权或并发保证，UC005 仍在写入时复查 policy version、check IDs、Scope Catalog 和 preflight。

详情不返回管理员管理页的其他 Version、OAuth secret、Tester 或用户资料。

## 一致性、分页与错误

队列每页和详情都在单个 MongoDB majority snapshot 中完成。Application、Version 与 Review 的引用或 snapshot 不变量损坏返回 `ApplicationReviewStateInconsistent` / INTERNAL；不得跳过坏项形成看似成功的短页。

合法空队列返回空 items 和空 next token。非法 pageSize/pageToken 返回 INVALID_ARGUMENT。详情中合法终态不是冲突；写决定仍由 UC005 返回 already decided 等错误。

## 最小查询模型与索引

沿用 `(status, submittedAt, reviewId)` 队列索引，并确保 Application/Version lookup 使用唯一索引。查询 port 返回独立 read model，不把队列行为放进 Review 聚合。

## API 草图

```text
rpc ListPendingApplicationVersionReviews(...)
  POST /v1/reviews/application-versions:search body=query

rpc GetApplicationVersionReview(...)
  GET /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}
```

## 验收场景

1. 只有精确 `app.version.review` 权限可读取队列和详情。
2. PENDING+ACTIVE 进入队列；CLOSING/CLOSED 排除；SUSPENDED 保留。
3. applicationId filter、升序 keyset、tie-break 和非法 token 稳定。
4. 冲突 Reviewer 仍看到项和全部 conflict 原因，但决定命令继续独立复查。
5. 详情使用提交 snapshot，即使当前 Version 文档后来变化也不改写审核输入。
6. APPROVED/REJECTED Review 可由 ID 读取但不回到 pending 队列。
7. 三元路径不匹配统一 NOT_FOUND；无权限先返回 PERMISSION_DENIED。
8. 损坏引用或 snapshot 返回 INTERNAL，队列不静默跳项。
9. HTTP 与原生 gRPC 行为一致，响应禁止共享缓存。

## 实现依赖与交付边界

ApplicationReview 队列索引、Version、Application 和版本审核 policy 已存在；无需 migration，除非当前部署缺失已定义索引。实现新增 read port/usecase、Mongo snapshot 查询、Proto/transport/wiring 和真实 MongoDB 验收。

## 业务规则

<a id="br-rev-029"></a>
### BR-REV-029：Reviewer 查询精确授权

Version 审核队列与详情只接受具备 `app.version.review` 的可信 Reviewer；其他角色不隐式获得读取权。

<a id="br-rev-030"></a>
### BR-REV-030：待处理队列资格

队列只包含 PENDING 且 Application 生命周期为 ACTIVE 的 Review；SUSPENDED 保留，CLOSING/CLOSED 排除。

<a id="br-rev-031"></a>
### BR-REV-031：审核快照权威

Reviewer 看到和裁决依据的内容来自提交时不可变 snapshot，当前 Version 不能替换该内容。

<a id="br-rev-032"></a>
### BR-REV-032：利益冲突提示不替代写检查

队列与详情计算 eligibility 仅供说明；决定事务必须重新计算利益冲突及全部前置条件。

<a id="br-rev-033"></a>
### BR-REV-033：稳定队列分页

队列按 `(submittedAt, reviewId)` 升序 keyset 分页，token 绑定 Reviewer 与 filter。

<a id="br-rev-034"></a>
### BR-REV-034：审核查询一致性与失败关闭

单页和详情必须内部一致；损坏引用或快照导致整次查询 INTERNAL，不能静默跳过。

## 变更记录

- 2026-10-07：补足 UC004/005 未交付的 Reviewer 读取面，设计进入 `ACCEPTED`。
