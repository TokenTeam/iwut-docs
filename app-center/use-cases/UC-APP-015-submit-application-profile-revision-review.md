# UC-APP-015：提交应用公开资料修订审核

状态：`ACCEPTED`

## 目标与边界

> developerStatus 为 `APPROVED` 的当前 Application 管理员，提交一份 DRAFT ApplicationProfileRevision；App Center 冻结本次资料快照，创建独立的 PENDING ApplicationProfileReview，并把资料修订迁移为 SUBMITTED。

本用例负责：

- 检查当前管理员、DRAFT 状态和乐观并发 revision。
- 重新验证当前完整资料内容。
- 创建具有独立身份的 ApplicationProfileReview attempt 与不可变 snapshot。
- 原子执行 `DRAFT -> SUBMITTED`、revision 和最近修改审计更新。

本用例不负责：

- 批准、拒绝或分配 Reviewer。
- 改变当前公开资料。后续 Profile Review 批准时才会自动公开。
- 创建下一份资料草稿；根据 [BR-PRF-006](UC-APP-013-create-application-profile-revision.md#br-prf-006)，SUBMITTED 期间工作位仍被占用。
- 添加 FilterRule、运行版本字段或发布槽位。
- 使用 AI 审核 DRAFT、作出决定或改变审核状态；未来 AI 审核的输入、结论效力与状态模型需要由独立用例定义，不属于当前流程。
- 定义 HTTP、数据库、缓存或 Go 实现。

## 参与者与输入

可信身份：

```text
DeveloperIdentity {
  authId
  developerStatus
}
```

Command：

```text
SubmitApplicationProfileRevisionReview {
  applicationId
  profileRevisionId
  expectedRevision
}
```

`applicationId` 和 `profileRevisionId` 使用各自的 UUIDv7 类型；`expectedRevision >= 1`。profileReviewId、attempt、snapshot、状态与审计字段由 App Center 生成，调用者不能指定。

## 成功结果

```text
ApplicationProfileRevision
  reviewStatus: DRAFT -> SUBMITTED
  revision: expectedRevision + 1
  updatedBy: submittedBy
  updatedAt: submittedAt

ApplicationProfileReview
  status: PENDING
  decision: null
  snapshot: submitted ProfileContent
  sourceRevision: expectedRevision

ApplicationProfile
  workingProfileRevisionId: target revision (unchanged)
```

当前 `currentPublishedProfileRevisionId` 保持不变。首次提交尚未有公开资料时，Application 仍不会因为 SUBMITTED 而进入普通用户目录。

## 主流程

1. 从可信身份取得 authId 和 developerStatus，并校验 Command 的类型与 revision。
2. 加载 Application、ApplicationProfile 和目标 ProfileRevision，确认调用者是当前 admin。
3. 确认目标属于该 Application、状态为 DRAFT、revision 等于 expectedRevision，且 ApplicationProfile.workingProfileRevisionId 指向目标。
4. 依据现有资料字段规则重新验证规范化后的 displayName、description 和 icon；FilterRule 不属于本次资料快照。
5. 为 ApplicationProfileReview 生成 UUIDv7，分配该 ProfileRevision 下的下一个 attempt，并取得 submittedAt。
6. 从 ProfileRevision 当前内容创建不可变 snapshot。
7. 在同一原子边界重新确认管理员、归属、DRAFT、revision 和不存在重复 PENDING Review，然后：
   - 创建 PENDING ApplicationProfileReview；
   - 把 ProfileRevision 迁移为 SUBMITTED；
   - 增加 ProfileRevision.revision，并更新 updatedBy/updatedAt；
   - 保持 ApplicationProfile.workingProfileRevisionId 指向目标 SUBMITTED 修订，不修改当前公开资料。
8. 返回提交后的 ProfileRevision 和新建的 ProfileReview。

## 失败结果

- 缺少可信身份：`DeveloperIdentityRequired`。
- developerStatus 不是 APPROVED：`DeveloperApprovalRequired`。
- ID 或 expectedRevision 非法：`InvalidApplicationProfileReviewSubmission`。
- Application、ProfileRevision 不存在或归属不匹配：`ApplicationProfileRevisionNotFound`。
- 调用者不是当前管理员：`ApplicationAdminRequired`。
- ProfileRevision 不是 DRAFT：`ApplicationProfileRevisionNotDraft`。
- expectedRevision 不匹配：`ApplicationProfileRevisionConflict`。
- 当前内容不再满足资料字段规则：`InvalidApplicationProfileContent`。
- 同一状态已经创建 Review 或存在不一致的 PENDING Review：`ApplicationProfileReviewAlreadyPending` 或内部一致性失败。
- ID、时钟或持久化失败：内部失败，不留下部分 Review 或状态迁移。

路径归属不匹配按 NotFound 处理，避免泄露其他 Application 的资料。网络超时后，调用方查询 ProfileRevision 与最新 Review；普通重试不创建第二个 attempt。

## 业务规则

<a id="br-prf-015"></a>

### BR-PRF-015：提交权限

提交者必须同时满足：

- developerStatus 为 `APPROVED`；
- 在最终原子写入时仍是 Application 当前 adminId。

submittedBy 记录本次实际提交者。管理员转让不会改写 ProfileRevision.createdBy；新管理员可以提交旧管理员创建的 DRAFT。

<a id="br-prf-016"></a>

### BR-PRF-016：提交前状态与乐观并发

只有属于该 Application、reviewStatus=`DRAFT` 且 revision 等于 expectedRevision 的 ProfileRevision 可以提交。

提交成功后，较早读取到的草稿更新不能覆盖 SUBMITTED 状态。SUBMITTED、APPROVED 和 REJECTED 都不能再次直接提交；REJECTED 是终态，继续编辑时由网页端预填后调用 UC-APP-013 创建新修订。

<a id="br-prf-017"></a>

### BR-PRF-017：提交时内容复检

提交时重新应用 [BR-PRF-003](UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](UC-APP-013-create-application-profile-revision.md#br-prf-005)。

本次可提交的完整资料包含 displayName、可空 description 和可空 icon。FilterRule、Application.name 和任何 ApplicationVersion 字段不进入本次资料审核。

<a id="br-prf-018"></a>

### BR-PRF-018：不可变审核快照

ApplicationProfileReview.snapshot 复制提交时已经规范化的完整资料：

```text
ApplicationProfileReviewSnapshot {
  displayName
  description
  icon
}
```

snapshot、sourceRevision、submittedBy 和 submittedAt 创建后不可修改。后续 Reviewer 读取 snapshot，不使用可能已经存在的其他草稿或当前公开资料拼装审核输入。

<a id="br-prf-019"></a>

### BR-PRF-019：审核 attempt 身份

- profileReviewId 是系统生成的全局唯一 UUIDv7。
- attempt 在单个 profileRevisionId 内从 1 开始严格递增。
- `(profileRevisionId, attempt)` 唯一。
- `(profileRevisionId, sourceRevision)` 唯一，防止同一 ProfileRevision 状态被重复提交。
- 同一 ProfileRevision 同时最多有一个 PENDING Review。

一个 ProfileRevision 不从 REJECTED 恢复。网页端可以预填其内容并通过 UC-APP-013 创建拥有新身份的新修订；新修订的 attempt 从 1 开始，不覆盖旧 Review。

<a id="br-prf-020"></a>

### BR-PRF-020：ProfileRevision 状态与审计

提交只执行以下生命周期变化：

```text
ApplicationProfileRevision: DRAFT -> SUBMITTED
revision: expectedRevision -> expectedRevision + 1
updatedBy: submittedBy
updatedAt: submittedAt
```

profileRevisionId、applicationId、sequence、createdBy、createdAt、displayName、description 和 icon 保持不变。ApplicationProfileReview.sourceRevision 保存迁移前的 expectedRevision。

<a id="br-prf-021"></a>

### BR-PRF-021：原子提交与重复请求

以下事实必须全部成功或全部失败：

- 当前管理员、ProfileRevision 归属、DRAFT 和 expectedRevision 的最终检查；
- ApplicationProfile.workingProfileRevisionId 仍指向目标的检查；
- Review attempt 分配与重复检查；
- PENDING ApplicationProfileReview 创建；
- ProfileRevision 状态、revision 和更新审计变更；
- ApplicationProfile.workingProfileRevisionId 仍指向目标 SUBMITTED Revision。

同一 sourceRevision 的并发提交最多一个成功。提交成功但响应丢失时，客户端通过查询发现 SUBMITTED 和对应 Review；重复命令不会创建第二条记录，也不会增加 revision。

<a id="br-prf-022"></a>

### BR-PRF-022：提交不改变当前公开资料

提交审核不会修改 `currentPublishedProfileRevisionId`。只有未来的 Profile Review 批准行为会在记录批准决定的同时自动把对应 ProfileRevision 设为当前公开资料。

提交也不会修改 ApplicationVersion、ApplicationPublication、Tester Membership、FilterRule 或 Auth 数据。

## 领域模型影响

本用例首次具体化独立聚合根 ApplicationProfileReview：

```text
ApplicationProfileReview {
  profileReviewId
  applicationId
  profileRevisionId
  attempt
  sourceRevision
  status: PENDING
  snapshot: ApplicationProfileReviewSnapshot
  submittedBy
  submittedAt
  decision: null
}
```

ApplicationProfileReview 引用 ProfileRevision，但不放入 ApplicationProfileRevision 聚合内部。应用服务在本地原子边界内协调 ApplicationProfile、ProfileRevision 和 ProfileReview。

本用例不决定 Review decision 的结构，也不引入 Reviewer 权限或审核策略。这些内容由下一条“审核 ApplicationProfileRevision”命令定义。

## 验收场景

- APPROVED Developer 且为当前 admin 时，可以提交匹配 revision 的 DRAFT。
- 成功后 ProfileRevision 为 SUBMITTED、revision 增加 1，并存在唯一 PENDING Review snapshot。
- snapshot 与提交时规范化后的 displayName、description、icon 完全一致，之后不可修改。
- 旧管理员、非 APPROVED Developer、非 DRAFT 或 stale revision 均不能提交。
- 并发提交同一 sourceRevision 最多产生一个 Review attempt。
- 任一步失败都不留下孤立 Review 或半完成状态迁移。
- 提交不改变当前公开资料，也不修改任何运行版本或发布槽位。
- 首次提交但尚未批准时，普通用户目录仍看不到该资料。

## 后续方向

后续命令已由 [UC-APP-016](UC-APP-016-decide-application-profile-revision-review.md) 定义：Reviewer 批准或拒绝 PENDING ApplicationProfileReview。批准将原子记录 decision、把 ProfileRevision 迁移为 APPROVED，并自动更新当前公开资料；拒绝将迁移为 REJECTED，但不会影响旧公开资料。

## 实现依赖与交付边界

本次交付为当前后端工作包：Domain、UseCase、MongoDB 原子 Repository、显式 migration、独立 API Proto 及生成物、可信身份 HTTP/原生 gRPC、Wire 和真实 MongoDB E2E。前端、生产 Gateway、资料管理查询和 UC-APP-016 审核决定分别交付，不阻塞当前命令实现。不得调用 Auth Scope Catalog、DNS、图标 URL 或资产服务。

沿用 Application `coordinationRevision` 技术写栅栏，在事务内保护当前管理员资格；资料生命周期、revision 和工作指针同时受最终条件检查保护。数据不变量异常使用 `ApplicationProfileStateInconsistent`，HTTP 500 / gRPC INTERNAL，并输出脱敏 ERROR 告警；不得伪装成客户端冲突或自动修复损坏状态。数据库驱动错误、完整资料文本和身份凭据不进入错误响应或普通日志。

验收必须运行 `make check-full`，覆盖所有 BR 的单元测试、真实副本集 validator/index、回滚、管理员转让竞争和 HTTP/gRPC E2E；冻结代码、API 和设计来源后运行，交付报告与本地 commit，禁止 push。

前置依赖是 UC-APP-013 和 UC-APP-014 已完成且通过各自完整验证；提交命令不等待 UC016、Reviewer 身份签发或审核策略。独立的 ApplicationProfileReview 聚合仍属于 `internal/profile` 能力；不复用运行版本 Review 的 scopes、URL 预检或恢复逻辑。

Repository 使用业务原子方法 SubmitDraft，输入 applicationId、profileRevisionId、expectedAdminId、expectedRevision、profileReviewId、submittedAt，返回提交后的 ProfileRevision 与 ProfileReview。事务内部重新加载内容并验证，使用当前持久化内容形成快照；不信任事务外或客户端传来的 snapshot。UUIDv7 与时钟经端口提供，技术重试不重新分配外部身份或时间。

新增 `application_profile_reviews` migration：profileReviewId 唯一、(profileRevisionId,attempt) 唯一、(profileRevisionId,sourceRevision) 唯一、PENDING profileRevisionId 部分唯一。applicationId/profileRevisionId/profileReviewId 为 UUIDv7，attempt 为正 int32，sourceRevision 为正 int64；snapshot 三字段必需且遵守已有资料规则；submittedBy 为可信 authId，submittedAt 为 UTC datetime，decision 字段必须存在且当前为 null，status 当前只写 PENDING。由服务负责不可变快照，测试不得用被引用的可变指针替代复制。attempt 在事务内取该修订已有最大值加一，检查溢出；正常新修订首次为1，无历史恢复入口。ProfileRevision revision 同样防溢出。

工作指针丢失/指错、DRAFT 已存在 PENDING 或同一 sourceRevision 的 Review 等属于内部不变量异常，按500/INTERNAL失败并回滚。合法重复请求见已 SUBMITTED 时返回 `ApplicationProfileRevisionNotDraft`（409/ABORTED），不作为幂等成功，也不创建第二份 Review。并发 loser 可按最终状态返回 NotDraft 或 revision conflict；只允许一个成功。字段复检失败为 `InvalidApplicationProfileContent`，不创建 Review。当前公开指针必须逐字保持。

## API 实现契约

内部 `POST /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews`；外部只加 `/app-center`。原生 gRPC：`app_center.v1.application_profile_review.ApplicationProfileReview/SubmitApplicationProfileRevisionReview`。复用 UC004 提交审核惯例，HTTP 正文为 `{ "expectedRevision": "3" }`（Proto int64 JSON 形状），gRPC command.expected_revision；本命令不使用 If-Match。正文只接受 expectedRevision，不接受 snapshot、身份、归属、attempt 或审计；query 不可覆盖正文和路径。

成功 HTTP201 返回 `{ "profileRevision": <完整提交后修订>, "review": <完整审核记录> }`，ETag 为提交后 ProfileRevision.revision。Review 包含 profileReviewId、applicationId、profileRevisionId、attempt、sourceRevision、status、snapshot、submittedBy、submittedAt、decision:null；snapshot 的 description/icon 沿用 UC013 的 string/null 表达。decision 在 Proto 使用 google.protobuf.Value 且只输出 null_value 表示当前唯一合法形状，UC016 再定义 object 内容契约；不预建审核决定业务。

错误：身份401/UNAUTHENTICATED，Developer/管理员不足403/PERMISSION_DENIED，归属错误或不存在404/NOT_FOUND，非法输入/内容400/INVALID_ARGUMENT，非DRAFT或stale409/ABORTED，内部不变量或基础设施失败500/INTERNAL。response loss 后查询的读模型契约独立交付，不在本工作包偷偷增加 GET，也不能声称完整管理端流程已可用。
