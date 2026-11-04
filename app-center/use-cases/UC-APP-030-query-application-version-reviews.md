# UC-APP-030：查询 ApplicationVersion 审核队列与审核详情

状态：`ACCEPTED`

## 修订范围与审核状态

2026-11-04 用户已接受本次修订并要求开始更新。提交时固定政策、未上线不做旧模型/数据/接口兼容，均为当前实施依据；旧已交付基线和历史记录保留，本次接受不表示新增实现已完成。实施范围与依赖见[已接受提案](../implements/2026-11-03-submission-bound-review-policy-proposal.md)。

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

详情路径精确匹配目标 Review，保留 application、当前 Version/Revision 状态、不可变 review.snapshot、原 decision、decisionEligibility 与 asOf；Profile 另保留当前公开投影及指针前置。审核政策统一使用 reviewPolicy：

```text
reviewPolicy {
  version
  requiredCheckIds[]
  requiredCheckDefinitions { id, title, description }[]
}
```

所有状态的 Review 均有真实 policyBinding，查询按该引用读取完整定义，ID/定义集合与顺序严格一致；终态 decision 的版本与绑定一致。A→B 后 A 的详情继续展示 A，Reviewer 用 reviewPolicy.version 填 expectedPolicyVersion，无需清空确认或换 B。

不输出当前全局策略，也不依赖当前 ACTIVE 才能解释已有绑定。缺绑定、未知引用、定义不完整或 decision 不一致均为 INTERNAL；客户端对缺失/非法响应报错，不猜测或进入旧模型只读模式。响应仍 private, no-store，不扩大管理员或公共目录的政策披露。统一数据约束见 [UC005 初始化](UC-APP-005-decide-application-version-review.md#新模型初始化与运行门禁)。

## 一致性、分页与错误

队列每页和详情都在单个 MongoDB majority snapshot 中完成。Application、Version 与 Review 的引用或 snapshot 不变量损坏返回 `ApplicationReviewStateInconsistent` / INTERNAL；不得跳过坏项形成看似成功的短页。

合法空队列返回空 items 和空 next token。非法 pageSize/pageToken 返回 INVALID_ARGUMENT。详情中合法终态不是冲突；写决定仍由 UC005 返回 already decided 等错误。

## 策略接口与交付

当前尚未上线，App/API、生成客户端、Gateway descriptor 和 Console 直接按单一新契约交付，不设计旧服务/旧客户端并行或分阶段兼容输出。

两类详情将原字段4直接改为 `review_policy`（JSON reviewPolicy），使用包含完整定义的统一语义；删除 currentPolicy 字段与旧形状。无需新增候选字段7/8、deprecated 别名或 reserve 过渡安排。既有无关字段不作无目的改动；最终新类型和字段号由 API 所有者在实施前冻结并统一生成。

提交命令仍只接受草稿 revision，决定请求的 expectedPolicyVersion 验证目标绑定。错误绑定使用明确的 `ApplicationReviewPolicyMismatch` / `ProfileReviewPolicyMismatch`（HTTP409/gRPC ABORTED）；不为保留旧 PolicyChanged/Unavailable 名称而引入歧义。缺绑定或坏定义属于 INTERNAL，不冒充版本前置冲突。

API 定义/生成、App、Console/BFF 严格解码和夹具按新契约配套更新，再运行新模型的端到端验收；严格解码只接受新形状，不 fallback currentPolicy。Gateway 不新增路由或权限，只核对新 descriptor、三协议与错误透传。本次未修改 Proto 或业务代码。

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
10. A 提交后发布 B，A 的待审与终态详情仍返回 A/完整定义；缺绑定/坏定义不 fallback B，严格解码仅接受新契约。

## 实现依赖与交付边界

ApplicationReview 队列索引、Version、Application 和版本审核 policy 已存在；本次绑定修订依赖 UC004/005 的新写模型及首次初始化；不实现旧数据过渡。实现新增 read port/usecase、Mongo snapshot 查询、Proto/transport/wiring 和真实 MongoDB 验收。

## 业务规则

<a id="br-rev-029"></a>
### BR-REV-029：Reviewer 查询精确授权

Version 审核队列与详情只接受具备 `app.version.review` 的可信 Reviewer；其他角色不隐式获得读取权。

<a id="br-rev-030"></a>
### BR-REV-030：待处理队列资格

队列只包含 PENDING 且 Application 生命周期为 ACTIVE 的 Review；SUSPENDED 保留，CLOSING/CLOSED 排除。

<a id="br-rev-031"></a>
### BR-REV-031：审核快照权威

Reviewer 看到和裁决依据的内容来自提交时不可变 snapshot，政策来自同一 attempt 的不可变 policyBinding；当前 Version 或全局 ACTIVE 都不能替换它们。

<a id="br-rev-032"></a>
### BR-REV-032：利益冲突提示不替代写检查

队列与详情计算 eligibility 仅供说明；决定事务必须重新计算利益冲突及全部前置条件。

<a id="br-rev-033"></a>
### BR-REV-033：稳定队列分页

队列按 `(submittedAt, reviewId)` 升序 keyset 分页，token 绑定 Reviewer 与 filter。

<a id="br-rev-034"></a>
### BR-REV-034：审核查询一致性与失败关闭

单页和详情必须内部一致；损坏引用、快照、必要绑定或绑定定义导致整次查询 INTERNAL，不能静默跳过或补齐部分定义。

## 变更记录

- 2026-11-04：用户接受提交绑定与无旧模型兼容修订；App `a95bd13` / API `2dc002e` 已实现，完整 backend `check-full` 24/24 PASS。Gateway/Console 新契约消费及真实新政策发布另行验收；见[实施记录](../implements/2026-11-04-submission-bound-review-policy-implementation.md)。

- 2026-11-04：用户接受无旧模型兼容的提交政策绑定方案，开始实施；接受不代表交付完成。

- 2026-11-04：按用户确认的未上线前提，删除旧模型、旧数据和旧接口兼容，改为统一新模型初始化及单一契约交付。

- 2026-11-03：PROPOSED 修订以 reviewPolicy 返回 attempt 绑定定义，弃用全局 currentPolicy 的决定用途；未实施。

- 2026-10-26：关联用户接受的正式策略发布与真实变化验收；保持现有正式定义读模型和字段不变。
- 2026-10-16：用户接受 v3 正式检查定义及详情输出扩展，保持历史策略语义。
- 2026-10-07：补足 UC004/005 未交付的 Reviewer 读取面，设计进入 `ACCEPTED`。
