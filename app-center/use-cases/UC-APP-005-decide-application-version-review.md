# UC-APP-005：审核应用版本

状态：`ACCEPTED`

## 目标与范围

> 拥有 `app.version.review` 权限且不存在利益冲突的 reviewer，根据不可变 ApplicationReview snapshot 和一份明确版本的审核策略，对 `PENDING` attempt 作出一次 `APPROVED` 或 `REJECTED` 决定。

本用例负责：

- 验证 reviewer 权限和利益冲突。
- 使用 reviewer 实际看到的版本化审核策略。
- 批准前重新验证 scopes、公网 HTTPS launchUrl 和版本化 OAuth 回调。
- 批准前检查当前 admin 与 submittedBy 的暂停状态，并在任一人已暂停时由系统自动拒绝。
- 一次性写入不可修改的审核决定。
- 原子同步 ApplicationReview.status 与 ApplicationVersion.reviewStatus。

本用例不负责：

- 创建、编辑或提交草稿。
- 把 `REJECTED` 恢复为 `DRAFT`。
- 撤回或推翻已经作出的决定。
- 把 `APPROVED` Version 自动放入 test/grey/stable 槽位。
- reviewer 队列分配、锁单、SLA、通知或申诉。
- 保证自托管 URL 指向的网页内容永久不变。

`APPROVED` 只表示这个审核快照被接受，并使 Version 有资格进入后续发布用例；它不等于已上线。

## 参与者

```text
ReviewerIdentity {
  authId: string
  permissions: set<string>
}
```

Auth 拥有平台人员权限。App Center 只消费经过验证的身份上下文，并使用单一权限 `app.version.review`；不继续沿用旧实现含义过宽的 `is_admin` 布尔 claim。
Reviewer permission 使用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)
中同版本追加的 `permissions` claim；Reviewer 不要求 `developer_status`，入口只把已验签
的 `sub` 与 permissions 投影为 ReviewerIdentity。Developer 暂停状态由 Auth Center 的
[Auth Developer Status v1](../../platform/contracts/auth-developer-status-v1.md) 原生 gRPC
契约提供；App Center 仍通过最小 port 隔离 consumer adapter，测试可使用 deterministic
fake。生产调用使用 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)。

reviewer 不需要 developerStatus。一个人即使同时具有 Developer 和 Reviewer 身份，本用例仍通过利益冲突规则限制其能审核哪些应用。

## 决定结果

批准：

```text
ApplicationReview.status: PENDING -> APPROVED
ApplicationReview.decision: set once
ApplicationVersion.reviewStatus: SUBMITTED -> APPROVED
ApplicationVersion.revision: +1
ApplicationVersion.updatedBy: reviewer authId
ApplicationVersion.updatedAt: decidedAt
```

拒绝：

```text
ApplicationReview.status: PENDING -> REJECTED
ApplicationReview.decision: set once, reason required
ApplicationVersion.reviewStatus: SUBMITTED -> REJECTED
ApplicationVersion.revision: +1
ApplicationVersion.updatedBy: reviewer authId
ApplicationVersion.updatedAt: decidedAt
```

若 reviewer 请求批准时发现当前 admin 或 Review.submittedBy 已暂停，同样执行上述 `REJECTED` 迁移，但 `decision.decidedBy` 和 Version.updatedBy 使用 Auth Center 按 purpose 解析的 SYSTEM principal Auth ID，reason 使用稳定系统文本“当前应用管理员或审核提交者已被暂停，待处理审核已由系统自动拒绝。”。App Center 在首次需要时通过 [Auth System Principal v1](../../platform/contracts/auth-system-principal-v1.md) 查询并缓存成功结果；依赖失败时保持 PENDING，不使用静态配置或占位 ID。

Version 的运行内容和 ApplicationReview.snapshot 在两种决定中都不改变。

## 旧实现观察

旧 App Center 允许平台 `is_admin` 直接更新 Application 的整体状态，也允许开发者更新发布相关 Version 状态。代码中没有独立 reviewer 行为、不可变决定、拒绝理由、利益冲突检查或审核策略版本。

### KEEP

- 平台侧权限与普通开发者权限分开。
- 审核结果需要成为可查询状态。
- 拒绝后需要保留可供开发者理解的原因。

### CHANGE

- 使用专门的 `app.version.review` 权限，不把所有平台管理员默认等同于 reviewer。
- reviewer 只能决定 `PENDING` ApplicationReview，不能直接写任意 Version status。
- 决定基于 ApplicationReview.snapshot，而不是审核时再次拼装可变草稿。
- 禁止审核自己创建、提交或当前管理的应用版本。
- 批准时重新验证 Scope Catalog 和公网 URL；拒绝不依赖这些外部检查。
- 保存审核策略版本和批准时明确确认的检查项。
- Review 和 Version 状态在同一原子操作中迁移。

### DROP

- 通用 `is_admin` 可以任意设置 `AUDITING/PUBLISHED/BANNED/...`。
- 开发者或 reviewer 直接把 Version 改成 `APPROVED`。
- 没有理由、审核人或时间的状态更新。
- 批准同时自动发布。
- 修改或删除过去的审核结论来表达重新审核。

### UNKNOWN

- `app.version.review` 权限的申请、授予、暂停和撤销流程；属于 Auth/平台治理。
- 检查项对应的详细内容政策文本与 reviewer 操作手册；策略 ID 与首版三个检查项由
  App Center 的版本化策略仓库拥有，政策文本仍需在启用生产审核前发布。
- reviewer 是否需要分组、双人批准或按风险等级升级。
- 已批准 Version 后续被发现有问题时采用 REVOKE、下架还是二者同时执行。

## 输入

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
reviewId: ApplicationReviewId
```

Command：

```text
DecideApplicationVersionReviewCommand {
  outcome: APPROVE | REJECT
  expectedPolicyVersion: string
  confirmedCheckIds: []string
  reason: optional string
}
```

reviewerId、decidedAt、approvalValidation 和最终状态不能由请求正文指定。

Command 使用动作词 `APPROVE/REJECT`；持久化后的结果状态使用 `APPROVED/REJECTED`。

## 主流程

共同流程：

1. 从可信身份上下文取得 reviewer authId 和 permissions。
2. 确认 permissions 包含 `app.version.review`。
3. 校验 outcome、expectedPolicyVersion、confirmedCheckIds 和 reason 的结构。
4. Repository 加载审核候选，并确认：
   - applicationId、versionId、reviewId 的关系正确。
   - ApplicationReview.status 是 `PENDING` 且 decision 为空。
   - ApplicationVersion.reviewStatus 是 `SUBMITTED`。
   - Version.revision 等于 `sourceVersionRevision + 1`。
   - Version 的受审核字段仍与 snapshot 完全一致。
   - reviewer 不是 Version.createdBy、Review.submittedBy 或 Application 当前 adminId。
5. ReviewPolicyProvider 取得 expectedPolicyVersion 对应且当前仍允许使用的策略，并根据 snapshot 得到 requiredCheckIds。

批准分支：

6. 确认 confirmedCheckIds 无重复、全部由策略定义，并覆盖本次全部 requiredCheckIds。
7. 通过 DeveloperSuspensionChecker 检查 candidate 中的当前 adminId 和 submittedBy。任一人已暂停时，跳过 ScopeCatalog 和 URL 检查，使用 System Auth ID 和固定 reason 构造自动 `REJECTED` decision，并进入步骤 11。
8. 通过 ScopeCatalog 再次确认 snapshot 中的 scopes 仍允许新版本申请，取得 approvalScopeCatalogRevision。
9. 通过 LaunchURLSubmissionPolicy 再次检查 snapshot.launchUrl，取得 approvalPreflightPolicyVersion；按 BR-VER-018 重新验证 snapshot.oauthRedirects。
10. 从 Clock 取得 decidedAt，构造 outcome=`APPROVED` 的不可变 decision。
11. Repository 原子重新确认步骤 4 的状态和利益冲突，并确认 current adminId 仍等于暂停检查所使用的 adminId，然后同时：
    - 将 ApplicationReview.status 改为 decision.outcome 并写入 decision。
    - 将 ApplicationVersion.reviewStatus 改为 decision.outcome。
    - 增加 Version.revision，并写入 updatedBy、updatedAt。
12. 返回更新后的 Review 和 Version 摘要。

拒绝分支：

6. 确认 confirmedCheckIds 为空，reason 符合规则且非空。
7. 从 Clock 取得 decidedAt，构造 outcome=`REJECTED` 的不可变 decision。
8. Repository 原子重新确认步骤 4 的状态和利益冲突，然后同时：
   - 将 ApplicationReview.status 改为 `REJECTED` 并写入 decision。
   - 将 ApplicationVersion.reviewStatus 改为 `REJECTED`。
   - 增加 Version.revision，并写入 updatedBy、updatedAt。
9. 返回更新后的 Review 和 Version 摘要。

批准的外部检查完成后仍必须在写入时重新检查本地状态。检查期间若另一 reviewer 已决定、管理员发生转让，或 Version 状态出现变化，本次批准失败且不覆盖已有结果。

## 异常流程

- 缺少可信身份：`ReviewerIdentityRequired`。
- 缺少 `app.version.review`：`ApplicationReviewPermissionRequired`。
- Application、Version 或 Review 不存在，或路径关系不匹配：`ApplicationReviewNotFound`。
- Review 不是 PENDING 或已经存在 decision：`ApplicationReviewAlreadyDecided`。
- Version 不是 SUBMITTED、revision 关系错误或内容与 snapshot 不一致：`ApplicationReviewStateInconsistent`。
- reviewer 与应用或提交存在利益冲突：`ApplicationReviewConflictOfInterest`。
- outcome 非法：`InvalidApplicationReviewOutcome`。
- expectedPolicyVersion 缺失或格式非法：`InvalidApplicationReviewPolicyVersion`。
- expectedPolicyVersion 未知、已 retired 或不再允许用于新决定：`ApplicationReviewPolicyChanged`。
- check ID 重复、未知或批准时缺少必要检查：`ApplicationReviewChecksIncomplete`。
- 拒绝时 confirmedCheckIds 非空：`InvalidApplicationReviewChecks`。
- 拒绝理由缺失或格式非法：`InvalidApplicationReviewReason`。
- 批准时 scope 不再允许申请：`InvalidApplicationScope`。
- 批准时 Scope Catalog 不可用：`ScopeCatalogUnavailable`。
- 批准时 URL 不再满足公网 HTTPS 策略：`ApplicationLaunchUrlNotReviewable`。
- 批准时 oauthRedirects 不再满足 BR-VER-018：`InvalidOAuthRedirectConfiguration`。
- 批准时 URL 检查依赖不可用：`LaunchUrlInspectionUnavailable`。
- 批准时开发者暂停状态依赖不可用：`DeveloperStatusUnavailable`；Review 保持 PENDING。
- 自动拒绝所需 System principal 不可解析：`SystemPrincipalUnavailable`；Review 保持 PENDING，后续请求可重试。
- 持久化失败：内部失败，Review 和 Version 都不产生部分状态。

路径关系不匹配统一返回 NotFound，不泄露其他应用的审核记录。自动批准检查失败时 Review 保持 PENDING，reviewer 可以稍后重试批准，或根据事实作出带理由的拒绝。

## 业务规则

<a id="br-rev-010"></a>
### BR-REV-010：Reviewer 权限

Auth 是 reviewer 权限的权威来源。入口层验证身份和权限声明，UseCase 只接收可信 ReviewerIdentity。

本轮只有一个原子权限：`app.version.review`。查看审核队列是否也需要该权限由 Query 设计决定；批准、拒绝、撤销和发布不能因为一个笼统 `is_admin` 自动互相授权。

<a id="br-rev-011"></a>
### BR-REV-011：利益冲突

以下任何条件成立都不能作出决定：

- reviewer.authId 等于 Application 当前 adminId。
- reviewer.authId 等于 ApplicationVersion.createdBy。
- reviewer.authId 等于 ApplicationReview.submittedBy。

检查必须在最终事务中基于当前 Application 管理员重新执行。未来加入 collaborators 后，是否把 collaborator 也视为利益冲突，需要由对应成员用例扩展本规则。

不提供隐藏的超级管理员绕过；紧急处置应使用独立、可审计的 revoke/下架用例。

<a id="br-rev-012"></a>
### BR-REV-012：一次性决定

- 只有 status=`PENDING` 且 decision=null 的 Review 可以决定。
- 一个 Review 只允许写入一次 decision。
- 决定成功后不能原地修改 outcome、reason、检查项、审核人或时间。
- 两个 reviewer 并发决定时最多一个成功。

网络超时后客户端应查询 Review；重复 POST 不创建新决定，也不覆盖已有决定。

<a id="br-rev-013"></a>
### BR-REV-013：状态一致性

合法迁移只有：

```text
ApplicationReview: PENDING -> APPROVED
ApplicationVersion: SUBMITTED -> APPROVED

ApplicationReview: PENDING -> REJECTED
ApplicationVersion: SUBMITTED -> REJECTED
```

Review 和 Version 的结果必须相同。Version 内容必须等于 snapshot，且决定前 Version.revision 必须为 `sourceVersionRevision + 1`。不满足表示出现绕过用例的写入或数据损坏，应中止并告警，不能尝试自动修复。

<a id="br-rev-014"></a>
### BR-REV-014：Version revision 与审计

决定成功后 Version.revision 原子增加 1，updatedBy 记录 decision.decidedBy，updatedAt 等于 decision.decidedAt。人工决定的 decidedBy 是 reviewer authId；暂停触发的自动拒绝使用注入的 System Auth ID。

createdBy、createdAt、submittedBy 和 submittedAt 都不因审核决定改变。审核人和审核时间属于 ApplicationReview.decision。

<a id="br-rev-015"></a>
### BR-REV-015：拒绝理由

- REJECT 必须提供 reason。
- reason 为 1–2000 个 Unicode code point。
- 不允许首尾 Unicode whitespace，不允许 Unicode `Cc` 控制字符。
- 校验通过后原样保存，不接受纯 whitespace。
- APPROVE 可以省略 reason；提供时遵循相同格式。

暂停检查触发的 System 自动拒绝不使用请求中的 reason，只使用本用例规定的固定文本。

拒绝理由是给开发者和审计人员阅读的纯文本，不允许 HTML。敏感数据和内部安全细节的书写规范属于 reviewer 操作政策。

<a id="br-rev-016"></a>
### BR-REV-016：版本化审核策略

reviewer 作决定时必须提交自己实际阅读的 expectedPolicyVersion。App Center 拥有不可变、可按版本读取的 VersionReviewPolicy；历史策略定义必须保留，不能让同一个版本标识指向不同内容。

```text
VersionReviewPolicy {
  version: ReviewPolicyVersion
  requiredChecks: []ReviewCheckDefinition
  status: ACTIVE | RETIRED
}
```

策略版本为 1–50 个 ASCII 字符，只允许 `[A-Za-z0-9._-]`。`RETIRED` 策略可用于解释历史决定，但不能用于新决定。

本用例定义机制，不在领域实体中硬编码学校政策文本。首版由 App Center
拥有并持久化正式策略及历史版本，`ReviewPolicyProvider` 从 App Center 自己的
不可变版本仓库读取；同一 version 不得被覆盖，历史版本不得删除。未来如果出现
独立的政策发布团队、审批生命周期或多个 bounded context 共同消费同一政策，再通过
新的 ADR 与跨服务契约评估提取策略发布能力；当前 UC 不依赖 ConfCenter。在真实
adapter 提供正式且不可变的策略版本前，不能将审核能力标记为生产可用。

<a id="br-rev-017"></a>
### BR-REV-017：批准检查确认

- confirmedCheckIds 在业务上是集合；输入重复直接拒绝。
- APPROVE 时，每个 ID 必须存在于当前策略，并包含策略针对该 snapshot 要求的全部检查。
- 校验后按 Unicode code point 字典序保存。
- REJECT 时 confirmedCheckIds 必须是空数组；失败事实写入 reason，不伪装成批准确认。

confirmedCheckIds 表示 reviewer 明确确认已经完成策略要求，不表示系统自动证明网页安全。需要结构化 PASS/FAIL 证据时，再由真实审核流程引入 ReviewCheckResult，而不是现在保存任意 JSON。

<a id="br-rev-018"></a>
### BR-REV-018：批准时重新验证

APPROVE 必须针对 ApplicationReview.snapshot 重新执行：

- DeveloperSuspensionChecker 对当前 adminId 与 Review.submittedBy 的暂停检查。
- ScopeCatalog requestable 检查。
- LaunchURLSubmissionPolicy 公网 HTTPS 与 DNS 地址策略检查。
- BR-VER-018 的 OAuth 回调结构、规范 hostname 与安全限制检查。

使用 snapshot 而不是当前 Version 拼装输入。通过后把 catalog revision 和 URL policy version 写入 decision.approvalValidation。

REJECT 不执行这些外部检查，避免 Auth 或 DNS 故障阻止 reviewer 记录拒绝事实。Auth 在 consent/token 路径仍拥有最终授权决定。

暂停检查在业务上是批准门禁：任一主体已暂停时，不返回普通校验错误，而是使用 System Auth ID 将 Review 与 Version 原子迁移为 REJECTED。依赖不可用时不能假设已暂停，Review 保持 PENDING。

<a id="br-rev-019"></a>
### BR-REV-019：审核与发布分离

APPROVED Version 只是后续 ApplicationPublication 可以引用的候选。审核决定不得：

- 自动修改 test/grey/stable 槽位。
- 自动生成 OAuth client 或密钥。
- 自动向普通用户目录公开。

发布必须由独立用例产生新的权限检查、发布记录和历史。

<a id="br-rev-020"></a>
### BR-REV-020：弱内容保证

reviewer 实际观察的是某个时间点 launchUrl 返回的自托管内容，而 snapshot 只能冻结 URL 与权限声明。decision 记录审核人、时间、策略和确认项，但不是远端字节的密码学证明。

因此 APPROVED 的准确语义是“该 snapshot 按记录的策略被 reviewer 接受”，不是“这个 URL 永远安全”。内容撤换检测、摘要、平台托管和紧急撤销属于后续能力。

## 最小领域行为

```text
ApplicationReview.Approve(
  policyVersion,
  confirmedCheckIds,
  optionalReason,
  approvalValidation,
  decidedBy,
  decidedAt,
) -> ApplicationReviewDecision

ApplicationReview.Reject(
  policyVersion,
  reason,
  decidedBy,
  decidedAt,
) -> ApplicationReviewDecision
```

实体保护 PENDING 和 decision 只能设置一次；跨 Review、Version、Application 的状态一致性与利益冲突由 Repository 原子操作共同保护。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ReviewPolicyProvider interface {
    RequireUsable(
        ctx context.Context,
        expectedVersion ReviewPolicyVersion,
        snapshot ApplicationVersionReviewSnapshot,
    ) (*VersionReviewPolicy, error)
}

type DeveloperSuspensionChecker interface {
    AnySuspended(
        ctx context.Context,
        authIDs []AuthID,
    ) (bool, error)
}

type ScopeCatalog interface {
    EnsureAllRequestable(
        ctx context.Context,
        scopes []ScopeName,
    ) (ScopeCatalogRevision, error)
}

type LaunchURLSubmissionPolicy interface {
    Inspect(
        ctx context.Context,
        launchURL LaunchURL,
    ) (PreflightPolicyVersion, error)
}

type SystemPrincipalResolver interface {
    ResolveReviewAutoRejection(ctx context.Context) (AuthID, error)
}

type ApplicationReviewDecisionRepository interface {
    LoadDecisionCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        reviewID ApplicationReviewID,
        reviewerID AuthID,
    ) (*ApplicationReviewDecisionCandidate, error)

    Decide(
        ctx context.Context,
        candidate ApplicationReviewDecisionCandidate,
        reviewerID AuthID,
        decision ApplicationReviewDecision,
    ) (*ApplicationReviewDecisionResult, error)
}
```

`Decide` 必须重新读取并比较 Review 状态、decision、Version 状态/revision/content 以及当前 Application.adminId，不能相信较早加载的 candidate 仍然有效。SYSTEM Auth ID 由 `SystemPrincipalResolver` 从 Auth Center 解析并在 adapter 内缓存，不由命令、静态配置或数据库直读指定。

## 数据模型变化

审核决定本身不增加 collection；`application_reviews` 的 `decision` 从 null 一次性写为以下对象：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `decision` | 一次性审核决定 | object | 本表以下字段；PENDING 时为 null | no | yes |
| `decision.outcome` | 决定结果 | string enum | `APPROVED/REJECTED`；必须等于 Review.status | no | no when decision exists |
| `decision.reviewPolicyVersion` | 使用的审核策略 | string | 1–50 ASCII `[A-Za-z0-9._-]` | no | no when decision exists |
| `decision.confirmedCheckIds` | 批准时确认的检查项 | array&lt;string&gt; | 已排序、元素唯一；拒绝时为 `[]` | no | no when decision exists |
| `decision.reason` | 批准备注或拒绝理由 | string | 1–2000 code points；首尾无 whitespace；禁止 `Cc` | no | yes for APPROVED; no for REJECTED |
| `decision.decidedBy` | 决定主体 Auth ID | string | 人工决定为 reviewer；自动拒绝为注入的 System Auth ID | no | no when decision exists |
| `decision.decidedAt` | 决定时间 | datetime | UTC / RFC 3339 | no | no when decision exists |
| `decision.approvalValidation` | 批准时的自动检查版本 | object | APPROVED 时存在；REJECTED 时为 null | no | yes |
| `decision.approvalValidation.scopeCatalogRevision` | 批准使用的 Auth catalog revision | int64 | Auth 单调递增版本 | no | no when approvalValidation exists |
| `decision.approvalValidation.preflightPolicyVersion` | 批准使用的 URL 策略版本 | string | 1–50 ASCII `[A-Za-z0-9._-]` | no | no when approvalValidation exists |

validator 必须保证：

- PENDING 时 decision 为 null。
- APPROVED/REJECTED 时 decision 非 null，且 decision.outcome 与 status 相同。
- APPROVED 时 approvalValidation 存在，confirmedCheckIds 满足策略；reason 可空。
- REJECTED 时 approvalValidation 为 null、confirmedCheckIds 为 `[]`、reason 非空。
- decision 写入后不可修改。

`application_versions` 不增加字段。决定时原子更新 reviewStatus、revision、updatedBy 和 updatedAt。

App Center 另以 `version_review_policies` 保存自己拥有的不可变正式策略。历史 v1 保留供解释既有决定；引入版本化 OAuth 回调后，新 migration 将 v1 标为 RETIRED，并写入以下 ACTIVE v2。任何已存在同版本但内容不同时 migration 必须失败，运行时不提供覆盖或删除接口：

```text
version: app-version-review-v1
requiredChecks:
  - content-policy-reviewed
  - launch-url-content-reviewed
  - requested-access-reviewed
status: RETIRED

version: app-version-review-v2
requiredChecks:
  - content-policy-reviewed
  - launch-url-content-reviewed
  - requested-access-reviewed
  - oauth-redirects-reviewed
status: ACTIVE
```

`oauth-redirects-reviewed` 要求 reviewer 确认所有已登记 callback 与声明的 client type 相符；数组为空时明确确认该版本未启用 OAuth/OIDC 回调。未来修改检查项必须使用新的 policy version；不能原地修改 v1 或 v2。`version_review_policies.version` 唯一，历史版本保留。所有新决定必须使用当前 ACTIVE v2；已经用 v1 作出的决定不重写。

## API 草图

```text
POST /applications/{applicationId}/versions/{versionId}/reviews/{reviewId}/decision
Authorization: <authenticated reviewer identity>
```

批准请求：

```json
{
  "outcome": "APPROVE",
  "expectedPolicyVersion": "app-version-review-v2",
  "confirmedCheckIds": [
    "content-policy-reviewed",
    "launch-url-content-reviewed",
    "requested-access-reviewed",
    "oauth-redirects-reviewed"
  ]
}
```

拒绝请求：

```json
{
  "outcome": "REJECT",
  "expectedPolicyVersion": "app-version-review-v2",
  "confirmedCheckIds": [],
  "reason": "应用在未说明用途的情况下请求了用户课表读取权限。"
}
```

成功：`200 OK`，返回完整 Review 和 Version 摘要：

```json
{
  "review": {
    "reviewId": "review-uuid",
    "status": "APPROVED",
    "decision": {
      "outcome": "APPROVED",
      "reviewPolicyVersion": "app-version-review-v2",
      "confirmedCheckIds": [
        "content-policy-reviewed",
        "launch-url-content-reviewed",
        "requested-access-reviewed",
        "oauth-redirects-reviewed"
      ],
      "reason": null,
      "decidedBy": "reviewer-auth-id",
      "decidedAt": "2026-09-15T14:00:00Z",
      "approvalValidation": {
        "scopeCatalogRevision": 18,
        "preflightPolicyVersion": "submit-v1"
      }
    }
  },
  "version": {
    "versionId": "version-uuid",
    "reviewStatus": "APPROVED",
    "revision": 5,
    "updatedBy": "reviewer-auth-id",
    "updatedAt": "2026-09-15T14:00:00Z"
  }
}
```

候选 HTTP 映射：

- 缺少 reviewer 身份：`401 Unauthorized`。
- 缺少权限或存在利益冲突：`403 Forbidden`，使用领域错误码区分。
- 路径关系不存在：`404 Not Found`。
- 已决定、状态不一致或策略已变化：`409 Conflict`。
- outcome、policy version 格式、checks 或 reason 非法：`422 Unprocessable Content`。
- 批准检查依赖不可用：`503 Service Unavailable`。

## 测试与验收

领域测试：

- PENDING Review 可以且只能决定一次。
- APPROVE 要求全部策略检查项，并规范化 confirmedCheckIds。
- REJECT 要求合法非空 reason，且不接受 confirmedCheckIds。
- 决定对象写入后不可修改。
- Review status 与 decision.outcome 必须一致。

UseCase 测试：

- 缺少 reviewer 权限在访问 Repository 前被拒绝。
- 当前 admin、Version 创建者或 Review 提交者不能审核。
- expectedPolicyVersion 必须仍可用于新决定。
- APPROVE 重新验证 snapshot scopes 和 launchUrl 并保存验证版本。
- APPROVE 发现当前 admin 或 submittedBy 已暂停时，不调用 ScopeCatalog/LaunchURLSubmissionPolicy，而是使用 System Auth ID 和固定 reason 永久拒绝。
- 暂停状态依赖不可用时 Review 保持 PENDING。
- REJECT 不调用 ScopeCatalog 或 LaunchURLSubmissionPolicy。
- Clock 是 decidedAt 的唯一来源；decidedBy 只能来自可信 reviewer 身份或 Auth 解析的 SYSTEM principal。
- System principal 查询失败时不写决定；成功结果可进程内缓存，失败不得缓存。
- 批准外部检查失败时不调用最终 Decide，Review 保持 PENDING。

Repository 集成测试：

- Review 决定与 Version 状态/revision/审计全部提交或全部回滚。
- 两个 reviewer 并发作出相同或相反决定时最多一个成功。
- 审核与管理员转让并发时，新的利益冲突条件在最终写入生效。
- Review/Version 状态、revision 或 snapshot 内容不一致时拒绝并告警。
- decision 不能被第二次更新。
- 批准不创建或修改任何 publication 槽位。

API 测试：

- APPROVE 和 REJECT 请求映射到同一个决定用例。
- 请求不能指定 decidedBy、decidedAt、approvalValidation 或最终状态。
- 权限、利益冲突、状态冲突、策略变化和字段错误映射正确。
- 重复决定返回冲突，不覆盖第一次结果。

## 已确认的实现边界

- `app.version.review` 的线格式已由 trusted-identity-v1 的 `permissions` claim 定义；
  权限申请、授予、暂停和撤销生命周期仍由后续 Auth Center 用例拥有。Developer Status、
  内部服务身份/allowlist 与 System principal resolve 均已有平台契约；App Center 不读取
  Auth 数据库，也不配置固定 SYSTEM Auth ID。
- ReviewPolicyProvider 首版由 App Center 本地 adapter 提供正式策略与历史版本；
  当前核心只实现了 port 契约和 fake 验证，生产启用前必须补齐不可变持久化实现。
- reviewer 访问未知自托管页面的 iframe/隔离浏览环境属于后续前端与安全运行环境，不属于本后端核心工作包，也不在当前注入 rpc-bridge。
- 批准时若当前 admin 或 submittedBy 已暂停，使用注入的 System Auth ID 和固定 reason 将 PENDING Review 与 SUBMITTED Version 原子迁移为 REJECTED。

## 后续用例

UC-APP-005 之后用于完成被拒绝开发闭环的用例是：

```text
UC-APP-006：将被拒绝的 ApplicationVersion 恢复为 DRAFT
```

它只负责 `REJECTED -> DRAFT`、revision 和审计更新，然后复用 UC-APP-003 编辑及 UC-APP-004 重新提交。详见 [UC-APP-006](UC-APP-006-restore-rejected-version-to-draft.md)。

## 迁移说明

既有实现需要 migration 不可变地加入 `app-version-review-v2`、retire v1，并同步 oauthRedirects snapshot 复检、策略测试与 API 示例；不得改写 v1 的检查项或历史 decision。旧 `is_admin` 直接设置 Application 状态的接口继续不保留。

## 变更记录

- 2026-09-15：建立 UC-APP-005；引入专用 reviewer 权限、利益冲突、版本化审核策略、一次性决定和批准时的 scope/URL 复检。
- 2026-09-15：UC-APP-006 明确拒绝后通过独立行为恢复 DRAFT，不由审核决定或普通编辑隐式迁移。
- 2026-09-20：确认 Auth/ConfCenter 通过 port 隔离并在核心测试中使用 fake；隔离浏览环境不属于后端核心；admin 或 submittedBy 暂停时由 System 永久自动拒绝。设计进入 `ACCEPTED`。
- 2026-09-21：首版 VersionReviewPolicy 改由 App Center 本地拥有和持久化；
  ConfCenter 不再是 UC-APP-005 的上线依赖，未来提取必须另行评审。
- 2026-09-22：trusted-identity-v1 兼容增加 `permissions` claim；确定首版
  `app-version-review-v1` 的三个正式检查项及本地不可变策略仓库。
- 2026-09-22：使用 caller-signed service JWS 调用 Auth；自动拒绝的 SYSTEM principal
  改为按 purpose 延迟解析并缓存，移除静态 System Auth ID 启动依赖。
- 2026-09-27：增加 OAuth 回调复检和 `app-version-review-v2`；v1 仅保留用于解释历史决定。
