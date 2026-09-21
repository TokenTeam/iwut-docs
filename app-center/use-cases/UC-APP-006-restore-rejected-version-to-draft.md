# UC-APP-006：将被拒绝的应用版本恢复为草稿

状态：`PROPOSED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 Version revision 为前提，把最新一次被拒绝的 ApplicationVersion 显式恢复为可编辑 DRAFT，并留下不可覆盖的恢复审计。

本用例负责：

- 确认目标是该 Version 最新且尚未处理的 `REJECTED` ApplicationReview。
- 在该 Review 上写入一次性 draftRestoration 审计。
- 将 ApplicationVersion.reviewStatus 从 `REJECTED` 改为 `DRAFT`。
- 增加 Version revision 并更新最近修改审计。

本用例不负责：

- 修改 Version 内容；恢复后使用 UC-APP-003。
- 自动重新提交审核；重新提交使用 UC-APP-004，并创建新的 attempt。
- 修改、删除或推翻原拒绝 decision。
- 重新检查 Scope Catalog、launchUrl 或审核策略。
- 撤回 SUBMITTED、撤销 APPROVED 或处理申诉。
- 发送审核通知。

## 为什么需要显式恢复

如果 UC-APP-003 直接允许编辑 `REJECTED`，第一次修改就会隐式改变生命周期，接口很难清楚表达“接受了哪一次拒绝并重新开始”。如果拒绝时直接自动回到 DRAFT，又会丢失 Version 当前处于被拒绝状态这一事实。

因此使用独立行为：

```text
REJECTED
  -- restore rejected review --> DRAFT
  -- UC-APP-003 -------------> edited DRAFT
  -- UC-APP-004 -------------> SUBMITTED + new review attempt
```

恢复本身不要求内容立即变化。拒绝可能源于远端网页、临时可用性、策略变化或误判，强迫开发者伪造一个字段修改并不能提高审核质量。

## 旧实现观察

旧实现没有版本审核 attempt，也没有 `REJECTED -> DRAFT` 的受控行为。开发者或平台管理员可以通过通用状态更新路径直接修改状态，无法保留“谁在何时处理了哪次拒绝”的稳定审计。

### KEEP

- 只有拥有应用管理权限的人可以重新开始版本开发。
- 被拒绝后允许开发者修改并再次进入审核流程。

### CHANGE

- 恢复必须针对明确的 rejected reviewId，而不是只写 Version.status。
- 只有当前 admin 且 developerStatus=`APPROVED` 可以恢复。
- Review 必须是该 Version 的最新 attempt，status=`REJECTED`，且尚未恢复。
- 恢复审计与 Version 状态/revision 更新原子提交。
- 原 decision、reason、snapshot 和审核人信息永不改写。

### DROP

- 通用 status setter 任意把 Version 改回可编辑状态。
- 修改 REJECTED 内容时隐式恢复。
- 重新使用或覆盖原 Review 作为下一次审核。
- 为通过校验而要求一次无意义的字段修改。

### UNKNOWN

- 开发者对拒绝决定的正式申诉流程。
- 是否需要限制反复恢复并提交相同内容的频率；当前由审核队列治理和后续滥用控制处理。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
reviewId: ApplicationReviewId
```

Command：

```text
RestoreRejectedApplicationVersionCommand {
  expectedVersionRevision: int64
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

restoredBy、restoredAt、resultVersionRevision 和最终 reviewStatus 不能由请求正文指定。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，expectedVersionRevision `>= 1`。
3. 从 Clock 取得 restoredAt。
4. Repository 在同一事务或等价原子边界中确认并更新：
   - Application 存在且 adminId 等于调用者 authId。
   - Version 属于路径中的 Application。
   - Version.reviewStatus 是 `REJECTED`。
   - Version.revision 等于 expectedVersionRevision。
   - Review 属于该 Application 和 Version。
   - Review 是该 Version attempt 最大的最新审核。
   - Review.status 和 decision.outcome 都是 `REJECTED`。
   - Review.draftRestoration 是 null。
   - Version.revision 等于 `Review.sourceVersionRevision + 2`。
   - 写入 Review.draftRestoration，包括 restoredBy、restoredAt 和 resultVersionRevision。
   - 将 Version.reviewStatus 改为 `DRAFT`。
   - 将 Version.revision 增加 1。
   - 将 Version.updatedBy 设为 authId，updatedAt 设为 restoredAt。
5. 返回带 draftRestoration 的 Review 摘要和更新后的 DRAFT Version 摘要。

步骤 4 的全部检查与写入必须处于同一个条件更新边界，不能先检查后无条件写入。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedVersionRevision 缺失或 `< 1`：`ApplicationVersionRevisionRequired`。
- Application、Version 或 Review 不存在，或路径关系不匹配：`ApplicationReviewNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 不是 `REJECTED`：`ApplicationVersionNotRejected`。
- Version revision 不匹配：`ApplicationVersionRevisionConflict`。
- Review 不是最新 attempt：`ApplicationReviewNotLatest`。
- Review 不是有效 REJECTED decision，或与 Version 状态/revision 不一致：`ApplicationReviewStateInconsistent`。
- draftRestoration 已存在：`ApplicationReviewAlreadyRestored`。
- 持久化失败：内部失败，不产生部分恢复。

路径关系不匹配统一返回 NotFound，不泄露其他应用或版本的审核记录。所有失败都保持 Review 和 Version 不变。

## 业务规则

<a id="br-rev-021"></a>
### BR-REV-021：恢复权限

恢复者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终写入时仍是 Application 当前 adminId。

恢复者不必是 Version.createdBy 或 Review.submittedBy。管理员转让后，新管理员可以继续处理旧管理员留下的拒绝版本。

<a id="br-rev-022"></a>
### BR-REV-022：只恢复最新拒绝

目标 Review 必须：

- 属于路径中的 Application 和 Version。
- 是该 Version attempt 最大的记录。
- status=`REJECTED` 且 decision.outcome=`REJECTED`。
- draftRestoration=null。

不能针对历史拒绝 attempt 改变当前 Version，也不能恢复 PENDING 或 APPROVED Review。

<a id="br-rev-023"></a>
### BR-REV-023：状态与 revision

合法迁移只有：

```text
ApplicationVersion: REJECTED -> DRAFT
```

恢复前 Version.revision 必须等于 Review.sourceVersionRevision + 2：一次提交和一次拒绝决定分别增加过一次 revision。恢复成功后 revision 再增加 1，resultVersionRevision 保存增加后的值。

若这些关系不成立，说明存在绕过用例的写入或数据损坏；系统必须中止并告警，不能猜测应恢复哪条记录。

<a id="br-rev-024"></a>
### BR-REV-024：恢复不修改内容

恢复只改变 lifecycle、revision 和审计字段。以下内容保持不变：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
```

恢复后的内容仍应与被拒绝 Review.snapshot 相同，直到 UC-APP-003 发生一次实际编辑。

允许恢复后不修改内容就再次提交。系统不能仅凭数据库字段判断远端自托管网页是否已改变，也可能出现策略更新或原审核误判。反复提交的滥用限制应作为独立规则设计。

<a id="br-rev-025"></a>
### BR-REV-025：拒绝事实不可变

恢复不得修改：

- Review.status=`REJECTED`。
- Review.snapshot 和 sourceVersionRevision。
- Review.decision 的 outcome、reason、policy、checks、decidedBy、decidedAt 或 approvalValidation。
- Review.submittedBy 和 submittedAt。

Version 回到 DRAFT 不表示拒绝被撤销，只表示管理员开始处理这次拒绝。

<a id="br-rev-026"></a>
### BR-REV-026：一次性恢复审计

draftRestoration 从 null 只能设置一次：

```text
ApplicationReviewDraftRestoration {
  restoredBy: AuthId
  restoredAt: Instant
  resultVersionRevision: int64
}
```

它创建后不可修改。新的审核 attempt 若再次被拒绝，会在新的 ApplicationReview 上产生自己的 draftRestoration，不覆盖旧记录。

<a id="br-rev-027"></a>
### BR-REV-027：原子恢复

以下操作必须全部成功或全部失败：

- 当前 admin、Version 状态和 expectedVersionRevision 检查。
- Review 所属、最新 attempt、拒绝 decision 和未恢复检查。
- draftRestoration 写入。
- Version 的 `REJECTED -> DRAFT`、revision 和更新审计变更。

管理员转让与恢复并发时，旧 admin 不能在转让完成后恢复。两个恢复请求并发时最多一个成功。

<a id="br-rev-028"></a>
### BR-REV-028：不提前重新验证

恢复 DRAFT 不调用 ScopeCatalog、LaunchURLSubmissionPolicy 或 ReviewPolicyProvider。DRAFT 可以暂时包含已经过期的 scope 或不再可提交的 URL；开发者必须能先进入草稿状态，才能通过 UC-APP-003 修正它们。

UC-APP-004 在下一次提交时重新执行提交校验，因此跳过恢复时的外部检查不会降低审核入口约束。

## 最小领域行为

```text
ApplicationVersion.RestoreDraft(
  expectedRevision,
  restoredBy,
  restoredAt,
) -> ApplicationVersion

ApplicationReview.RecordDraftRestoration(
  restoredBy,
  restoredAt,
  resultVersionRevision,
) -> ApplicationReviewDraftRestoration
```

实体分别保护状态和一次性字段；跨 Application、Version、Review 的当前管理员、最新 attempt 和 revision 关系由 Repository 原子操作共同保护。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type RejectedApplicationVersionRepository interface {
    RestoreDraft(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        reviewID ApplicationReviewID,
        expectedAdminID AuthID,
        expectedVersionRevision int64,
        restoredAt time.Time,
    ) (*RestoreRejectedVersionResult, error)
}
```

Repository 必须区分 NotFound、NotAdmin、NotRejected、RevisionConflict、NotLatest、AlreadyRestored、StateInconsistent 和基础设施失败。

## 数据模型变化

UC-APP-006 不增加 collection。`application_reviews` 增加一次性、可空的 draftRestoration：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `draftRestoration` | 对拒绝结果的草稿恢复审计 | object | 仅 REJECTED Review 可从 null 写入一次 | no | yes |
| `draftRestoration.restoredBy` | 执行恢复的当前 admin | string | opaque authId | no | no when draftRestoration exists |
| `draftRestoration.restoredAt` | 恢复时间 | datetime | UTC / RFC 3339 | no | no when draftRestoration exists |
| `draftRestoration.resultVersionRevision` | 恢复后的 Version revision | int64 | `>= 1`；等于恢复前 revision + 1 | no | no when draftRestoration exists |

validator 必须保证：

- draftRestoration 为 null，或三个子字段完整存在。
- 只有 status=`REJECTED` 且 decision.outcome=`REJECTED` 的 Review 可以拥有 draftRestoration。
- draftRestoration 创建后不可修改。

`application_versions` 不增加字段。本用例更新 reviewStatus、revision、updatedBy 和 updatedAt。

## API 草图

```text
POST /applications/{applicationId}/versions/{versionId}/reviews/{reviewId}/draft-restoration
Authorization: <authenticated developer identity>
```

请求：

```json
{
  "expectedVersionRevision": 5
}
```

成功：`200 OK`

```json
{
  "review": {
    "reviewId": "review-uuid",
    "status": "REJECTED",
    "draftRestoration": {
      "restoredBy": "current-admin-auth-id",
      "restoredAt": "2026-09-15T16:00:00Z",
      "resultVersionRevision": 6
    }
  },
  "version": {
    "versionId": "version-uuid",
    "reviewStatus": "DRAFT",
    "revision": 6,
    "updatedBy": "current-admin-auth-id",
    "updatedAt": "2026-09-15T16:00:00Z"
  }
}
```

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- 路径关系不存在：`404 Not Found`。
- revision 不匹配、非 REJECTED、非最新 attempt、已恢复或状态不一致：`409 Conflict`，使用领域错误码区分。
- expectedVersionRevision 格式非法：`400 Bad Request`。

## 测试与验收

领域测试：

- REJECTED Version 可以恢复为 DRAFT，并增加 revision。
- 其他 Version 状态不能使用恢复行为。
- draftRestoration 只能设置一次且创建后不可修改。
- 恢复不修改 Version 内容或原 Review decision。
- resultVersionRevision 与 Version 新 revision 一致。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以恢复。
- 新 admin 可以恢复前任创建和提交的 Version。
- expectedVersionRevision、restoredBy 和 restoredAt 来源正确。
- 本用例不调用 ScopeCatalog、LaunchURLSubmissionPolicy 或 ReviewPolicyProvider。
- Repository 业务错误映射正确。

Repository 集成测试：

- draftRestoration 与 Version 状态/revision/审计全部提交或全部回滚。
- 两个并发恢复最多一个成功。
- 管理员转让与恢复并发时旧 admin 不会成功。
- 历史 rejected reviewId 不能恢复当前 Version。
- Review/Version 状态或 revision 关系损坏时拒绝并告警。
- 恢复后可以由 UC-APP-003 更新，或由 UC-APP-004 直接创建递增的新 attempt。

API 测试：

- 正确请求返回 REJECTED Review 的恢复审计和 DRAFT Version 摘要。
- 请求不能指定 restoredBy、restoredAt、resultVersionRevision 或最终状态。
- 路径、身份、状态、revision 和重复恢复错误映射正确。

## 后续方向

到 UC-APP-006 为止，开发者版本审核闭环已经连通：

```text
create -> edit -> submit -> approve
                        -> reject -> restore -> edit/resubmit
```

下一个用例不再扩展审核状态机，而是：

```text
UC-APP-007：将 APPROVED ApplicationVersion 放入 test 发布槽位
```

该用例选择由当前管理员显式设置，并让 Publication 按 rpcApiMajor 分区；详见 [UC-APP-007](UC-APP-007-place-approved-version-in-test-slot.md) 和 [ADR-002](../adr/ADR-002-partition-publication-by-rpc-api-major.md)。test 槽位可以在 tester 为零时先存在，但不会向普通用户公开。

## 迁移说明

服务从未上线，不迁移旧通用 Version status 更新入口。新的恢复行为必须同时写入 draftRestoration 和 Version 状态，不能通过数据库脚本只改一边。

## 变更记录

- 2026-09-15：建立 UC-APP-006；以最新 rejected review 为恢复对象，新增一次性 draftRestoration 审计，并原子执行 `REJECTED -> DRAFT`。
- 2026-09-15：后续 UC-APP-007 选择由当前管理员按 rpcApiMajor 设置 test 槽位，审核闭环与发布边界保持分离。
