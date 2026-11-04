# UC-APP-005：审核应用版本

状态：`ACCEPTED`

## 修订范围与审核状态

2026-11-04 用户已接受本次修订并要求开始更新。提交时固定政策、未上线不做旧模型/数据/接口兼容，均为当前实施依据；旧已交付基线和历史记录保留，本次接受不表示新增实现已完成。实施范围与依赖见[已接受提案](../implements/2026-11-03-submission-bound-review-policy-proposal.md)。

## 目标与范围

治理扩展：批准门禁的角色区分、WITHDRAWN/CLOSED 和账号状态条件由 [BR-APP-011](UC-APP-025-coordinate-account-owner-exit.md#br-app-011) 定义，替代仅判断 AnySuspended 的门禁；本文其余“暂停检查”均表示该完整批准资格检查。依赖故障仍保持 PENDING。

> 拥有 `app.version.review` 权限且不存在利益冲突的 reviewer，根据不可变 ApplicationReview snapshot 和本次提交已绑定版本的审核策略，对 `PENDING` attempt 作出一次 `APPROVED` 或 `REJECTED` 决定。

本用例负责：

- 验证 reviewer 权限和利益冲突。
- 使用 reviewer 实际看到的版本化审核策略。
- 批准前重新验证 scopes、公网 HTTPS launchUrl 和版本化 OAuth 回调。
- 批准前检查当前 admin 与 submittedBy 的暂停状态，并在任一人已暂停时由系统自动拒绝。
- 一次性写入不可修改的审核决定。
- 原子同步 ApplicationReview.status 与 ApplicationVersion.reviewStatus。
- 约束审核策略的正式发布与退休，见[策略正式发布与运维读回](#策略正式发布与运维读回)；这是部署治理流程，不增加 Reviewer 在线策略管理权。

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

若 reviewer 请求批准时发现当前 admin 或 Review.submittedBy 已暂停，同样执行上述 `REJECTED` 迁移，但 `decision.decidedBy` 和 Version.updatedBy 使用 Auth Center 按 purpose 解析的 SYSTEM principal Auth ID，reason 使用稳定系统文本“当前应用管理员或审核提交者不满足账号与开发者资格要求，待处理审核已由系统自动拒绝。”。App Center 在首次需要时通过 [Auth System Principal v1](../../platform/contracts/auth-system-principal-v1.md) 查询并缓存成功结果；依赖失败时保持 PENDING，不使用静态配置或占位 ID。

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
- 当前 v3 正式定义已由下文接受并存储；下一份真实政策与扩展操作手册仍需另审，不能为测试编造。
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
5. 从目标 Review.policyBinding 按版本读取不可变策略，确认 expectedPolicyVersion 与绑定版本相同，并根据该策略和 snapshot 得到 requiredCheckIds；不要求该版本仍为全局 ACTIVE。

批准分支：

6. 确认 confirmedCheckIds 无重复、全部由策略定义，并覆盖本次全部 requiredCheckIds。
7. 通过 DeveloperReviewEligibilityChecker 检查 candidate 中的当前 adminId 和 submittedBy。任一人已暂停时，跳过 ScopeCatalog 和 URL 检查，使用 System Auth ID 和固定 reason 构造自动 `REJECTED` decision，并进入步骤 11。
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
- expectedPolicyVersion 与目标 attempt 的绑定不符：返回 `ApplicationReviewPolicyMismatch`（409/ABORTED），不写决定；表示请求与绑定前置不符。
- 应有绑定缺失、绑定政策不存在或定义损坏：`ApplicationReviewStateInconsistent` / INTERNAL；存储不可用按依赖失败处理，不伪装成政策已切换。
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

每次成功提交在 Review.policyBinding 固定一份正式政策，参见 [UC004 BR-REV-004/009](UC-APP-004-submit-application-version-review.md#br-rev-004)。Reviewer 的 expectedPolicyVersion 必须等于目标 attempt 的绑定版本，而不是决定时的最新版本；decision.reviewPolicyVersion 保存相同版本。App 拥有 VersionReviewPolicy 的不可变 version、requiredChecks（id/title/description）和独立的 ACTIVE/RETIRED 选择状态，版本为 1–50 ASCII `[A-Za-z0-9._-]`。

ACTIVE 仅表示供新提交选择；RETIRED 仍允许已有绑定 attempt 批准或拒绝，并用于解释历史。两类政策独立维护且历史不可删除或原地改义。新政策不自动产生补审、撤销批准、整改期限或运行/发布状态变化。正式发布见下文；不增加在线政策 CRUD 或独立政策服务。

本次替代原“退休后不能作新决定”和“决定必须使用当前唯一 ACTIVE”的规则。当前尚未上线，本方案不接收无绑定的旧模型记录；所有 PENDING 和终态均从提交时获得真实绑定。策略完整定义的缺失与存储错误失败关闭，不能通过当前策略替补绑定。

<a id="br-rev-017"></a>
### BR-REV-017：批准检查确认

- confirmedCheckIds 在业务上是集合；输入重复直接拒绝。
- APPROVE 时，每个 ID 必须存在于本次 attempt 绑定的策略，并包含该策略针对 snapshot 要求的全部检查。
- 校验后按 Unicode code point 字典序保存。
- REJECT 时 confirmedCheckIds 必须是空数组；失败事实写入 reason，不伪装成批准确认。

confirmedCheckIds 表示 reviewer 明确确认已经完成策略要求，不表示系统自动证明网页安全。需要结构化 PASS/FAIL 证据时，再由真实审核流程引入 ReviewCheckResult，而不是现在保存任意 JSON。

<a id="br-rev-018"></a>
### BR-REV-018：批准时重新验证

APPROVE 必须针对 ApplicationReview.snapshot 重新执行：

- DeveloperReviewEligibilityChecker 对当前 adminId 与 Review.submittedBy 的暂停检查。
- ScopeCatalog requestable 检查。
- LaunchURLSubmissionPolicy 公网 HTTPS 与 DNS 地址策略检查。
- BR-VER-018 的 OAuth 回调双数组结构、规范 URL 与安全限制检查。

使用 snapshot 而不是当前 Version 拼装输入。通过后把 catalog revision 和 URL policy version 写入 decision.approvalValidation。审核政策绑定不冻结这些依赖：Scope 仍按当前 requestable 与既有 TTL/实例窗口判断；URL/DNS、OAuth 结构按现行技术安全规则复检，preflightPolicyVersion 是独立技术策略版本。审核正文不能借冻结豁免这些规则。

REJECT 不执行这些外部检查，避免 Auth 或 DNS 故障阻止 reviewer 记录拒绝事实。Auth 在 consent/token 路径仍拥有最终授权决定。

暂停检查在业务上是批准门禁：任一主体已暂停时，不返回普通校验错误，而是使用 System Auth ID 将 Review 与 Version 原子迁移为 REJECTED。依赖不可用时不能假设已暂停，Review 保持 PENDING。

<a id="br-rev-019"></a>
### BR-REV-019：审核与发布分离

APPROVED Version 只是后续 ApplicationPublication 可以引用的候选。政策 A 退休、B 激活不使 A 的合法批准自动失效；后续发布/运行仍执行其已有实时门禁，不单因审核政策不是当前 ACTIVE 拒绝。审核决定不得：

- 自动修改 test/grey/stable 槽位。
- 自动生成 OAuth client 或密钥。
- 自动向普通用户目录公开。

发布必须由独立用例产生新的权限检查、发布记录和历史。

<a id="br-rev-020"></a>
### BR-REV-020：弱内容保证

reviewer 实际观察的是某个时间点 launchUrl 返回的自托管内容，而 snapshot 只能冻结 URL 与权限声明。decision 记录审核人、时间、策略和确认项，但不是远端字节的密码学证明。

因此 APPROVED 的准确语义是“该 snapshot 按记录的策略被 reviewer 接受”，不是“这个 URL 永远安全”。内容撤换检测、摘要、平台托管和紧急撤销属于后续能力。

## 最小领域行为

`ApplicationReview.Approve/Reject` 只使用自身 policyBinding 指定的政策；decision 的 reviewPolicyVersion 必须等于该版本，且只写一次。RETIRED 不是拒绝该 attempt 决定的理由。状态、snapshot、绑定一致性及 Application 当前事实在最终事务复查，不写全局政策选择状态，也不修改政策状态。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ReviewPolicyProvider interface {
    LoadBoundDefinition(
        ctx context.Context,
        boundVersion ReviewPolicyVersion,
        snapshot ApplicationVersionReviewSnapshot,
    ) (*VersionReviewPolicy, error)
}

type DeveloperReviewEligibilityChecker interface {
    ApprovalBlocked(
        ctx context.Context,
        currentAdminID AuthID,
        submittedBy AuthID,
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

`Decide` 必须重新读取并比较 Review.policyBinding 与 decision 的版本一致性、Review 状态、decision、Version 状态/revision/content 以及当前 Application.adminId，不能相信较早加载的 candidate 仍然有效。SYSTEM Auth ID 由 `SystemPrincipalResolver` 从 Auth Center 解析并在 adapter 内缓存，不由命令、静态配置或数据库直读指定。

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

App Center 以 `version_review_policies` 保存不可变正式策略。首次初始化不导入旧实验模型的 v1/v2 ID-only 记录。当前已有完整正式定义的基线为 `app-version-review-v3`；本次修订后决定使用 attempt 绑定版本，不以 ACTIVE 强制换版。不得原地补写 v1/v2 未定义的政策正文。

v3 的 requiredChecks 按以下顺序保存。每项包含 id、title、description（下表第三列原文），纯文本 UTF-8，title 为 1–80、description 为 1–2000 个 Unicode scalar values，无首尾空白或控制字符。ID 唯一，四项完整；Domain 不硬编码政策文本。正式文本由 migration 精确核对和不可变存储保护。

### v3 正式人工检查定义

以下文字于 2026-10-16 获用户接受，是 v3 的完整人工检查基线。它不引用尚未交付的学校政策、外部内容标准或隐含评分规则。

| ID | 标题 | 定义与确认条件 |
| --- | --- | --- |
| `content-policy-reviewed` | 应用内容与声明 | 已阅读提交快照中的应用声明，并结合实际入口确认其用途可识别且与展示功能一致；未发现冒充平台或其他主体、诱骗提交账号凭据、隐瞒实际收集用途或诱导执行恶意程序的内容。无法辨明用途或无法完成这些确认时，不得确认通过。 |
| `launch-url-content-reviewed` | 实际入口内容 | 已访问该审核快照的 launchUrl，并检查入口及其正常跳转后可达的主要功能；能实际观察到与声明用途一致的应用内容，未发现伪装登录、凭据窃取或恶意下载引导。入口不可达、仅有占位内容或必须使用 Reviewer 无法取得的访问条件而无法完成检查时，不得确认通过。 |
| `requested-access-reviewed` | 请求能力与 Scope | 已逐项检查快照声明的能力和 Scope，并结合其正式目录含义与实际功能确认用途可说明、请求范围与所展示功能相符，未发现无关或明显多余的访问请求。空集合表示已明确确认该版本未声明相应访问请求；目录含义或用途无法查明时，不得确认通过。 |
| `oauth-redirects-reviewed` | OAuth 回调用途 | 已分别检查 pkceRedirectUris 与 confidentialRedirectUris 中每个回调与应用用途、接收方及对应 client type 的关系，确认回调由预期接收方使用，且无明显无关接收方。两个数组均为空时，明确确认该版本未配置 OAuth/OIDC 回调。不能确认接收方或用途时，不得确认通过。 |

人工判断针对审核快照和当次可观察内容，不承诺穷尽所有页面、实际 OAuth 运行成功、远端内容永不变化或所有恶意行为均已排除。系统继续独立执行 Scope requestable、HTTPS/DNS、OAuth 结构及 Developer 暂停门禁；人工勾选不能跳过这些检查。

现有 Version snapshot 没有用途说明正文；这里的“声明”仅指其已有 label、入口、能力、Scope 与回调配置，用途结合实际入口内容判断，不假设已存在额外说明字段，也不以当前可变 Profile 代替提交快照。

Reviewer 不能预勾选、用“全选”代替逐项确认，或在无法观察时猜测通过。不能完成检查时可以保留 PENDING；确认不满足要求并决定拒绝时，REJECT 继续使用有效 reason 和空 confirmedCheckIds，不新增第三种决定或结构化证据系统。

本提案只定义 Version 策略；Profile 策略及其已有检查文本不随同改写。

### 初始正式策略

新模型首次初始化即写入具有完整定义的 `app-version-review-v3`，与独立的 Profile v1 一起作为当前正式基线。不设计从 v1/v2 旧数据升级、补定义或旧页面过渡；已有实验数据和夹具按新模型重建。版本名沿用已接受的政策内容标识，不为本次模型调整制造同义 v4。

## 策略正式发布与运维读回

本节替代 2026-10-26 发布工作包中的“切换使旧 PENDING 失去决定资格”及配套409恢复验收。保留低频、获批的专用发布 migration，不新增在线 CRUD、政策服务或公网运维 API；Profile 通过 BR-PRF-028 引用同一机制，政策种类相互独立。

### 主体与必要输入

真实新政策经用户/指定政策责任人批准，由获目标环境部署授权的主体执行受审发布包。Reviewer 权限不授予发布权。包只需明确 kind、唯一 migrationId、预期 fromVersion、全新 toVersion 与不可变完整定义、批准依据及 release 来源；同版本异内容拒绝，版本不得靠字符串排序推断新旧，不为测试制造同义 v4/v2。

### 原子切换与提交栅栏

每类正常服务时恰好一个 ACTIVE，定义不可变且可按版本读取。发布在同一事务核对 fromVersion/原内容，插入 B、将 A 退休、在原 ACTIVE 文档上完成退休条件写，并记录该专用 migration 的最小成功标识。提交与发布在原 ACTIVE 政策文档上作真实条件写，协议以 [UC004](UC-APP-004-submit-application-version-review.md#策略绑定与提交并发)为准；决定不与发布争抢此栅栏，也不对退休状态施加 ACTIVE 前置。已绑定 A 的 PENDING 在任一胜序下继续按 A 决定。

并发 A→B/A→C 最多一个成功，失败方重读报告基线变化，不能自动改为 B→C。发布不改任何 Review、终态 decision、snapshot、批准资格、运行/发布槽位；不删除/改写旧定义，不重新激活退休版本。发布包或实现校验失败时停止该发布并修复；定义仍可解释且实时门禁满足的旧绑定决定不因全局政策变化被关闭。

### 最小恢复与读回

专用 migration 使用现有 ledger 保存 migrationId、kind、from/toVersion、定义清单摘要和 appliedAt，与本次切换同事务提交；批准依据及部署身份留在现有发布审计，以 migrationId 关联。不扩展通用 ledger 为政策治理产品，不另建 CHANGE_ID_CONFLICT/BASE_CHANGED 状态机、通用发布 CLI 或 policy-status 服务。

同 migrationId/同内容重复执行只核对原记录；异内容拒绝。unknown commit 先按 ADR004 恢复原事务提交，再读该标识及不可变定义、当前 ACTIVE，不能因退出码不明而换 ID 或重演历史激活。后来已 B→C 时只核对旧 A→B 成功记录，不回拨政策状态。缺标识或事实不一致时停止并人工核查，不能把“无回执”当成回滚成功。readiness/迁移校验输出这一最小只读结果即可，不要求单独建设新运维入口。

### 设计验收与真实联合证据

分别验证 A 下提交→发布 B→仍按 A 批准/拒绝，B 后新提交与拒绝后重提绑定 B，提交/发布两种胜序、发布重复/回滚/未知结果和历史保留。错误 expectedPolicyVersion 负例只能证明绑定校验，不能冒充真实切换。

组件/事务层可使用明确标记的隔离测试政策 A/B；真实联合验收须有已获批的真实新政策及正式发布准备条件，未具备时标待准备，不为凑测试生成生产版本。政策切换本身不清空旧 attempt 页面确认，也不要求重提。Scope 变化、权限撤销、公开指针等独立冲突继续按各自现行契约恢复。

## API 草图

以下 v2 片段保留历史线格式示例，不代表当前可用于新决定的版本。当前 ACTIVE 基线为 v3；实际命令从 UC030 本次详情取得版本和完整检查定义，按 BR-REV-016/017 确认，不能直接复用已退休示例的 expectedPolicyVersion 或把当前文字套入历史 decision。

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
- 已决定、状态冲突或请求政策与绑定不符：`409 Conflict`；绑定/定义损坏为 INTERNAL，不与普通冲突混淆。
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
- expectedPolicyVersion 必须等于目标绑定；A→B 不妨碍 A attempt 决定。完整矩阵见本 UC 新语义设计验收。
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
- 设计阶段核对的旧基线按全局 ACTIVE 工作。2026-11-04 App/API 已完成提交绑定、按绑定决定/查询、新模型初始化及发布事务原语，并通过完整 backend 门禁；真实新政策及正式发布联合证据待准备。2026-10-26 仅为打断待审决定设计的工作不再列为待实现目标。
- reviewer 访问未知自托管页面的 iframe/隔离浏览环境属于后续前端与安全运行环境，不属于本后端核心工作包，也不在当前注入 rpc-bridge。
- 批准时若当前 admin 或 submittedBy 已暂停，使用注入的 System Auth ID 和固定 reason 将 PENDING Review 与 SUBMITTED Version 原子迁移为 REJECTED。

## 后续用例

UC-APP-005 之后用于完成被拒绝开发闭环的用例是：

```text
UC-APP-006：将被拒绝的 ApplicationVersion 恢复为 DRAFT
```

它只负责 `REJECTED -> DRAFT`、revision 和审计更新，然后复用 UC-APP-003 编辑及 UC-APP-004 重新提交。详见 [UC-APP-006](UC-APP-006-restore-rejected-version-to-draft.md)。

## 新模型初始化与运行门禁

本节由 BR-REV-016 拥有，Profile 的 BR-PRF-028 引用同一原则。设计阶段只读核对的是 App `5b42ed7`、API `6fea3db`；当时尚无提交政策绑定，实施进度见本 UC 变更记录。用户明确当前未上线，因此采用统一的新模型，不承接旧数据库、旧审核记录或旧接口。

### 初始数据与约束

首次初始化建立新模型的 policy、Review 与 validator。Version 使用已接受的 v3 完整定义，Profile 使用 BR-PRF-028 的 v1 完整定义；两者独立保存。所有 Review 无论 PENDING、APPROVED 或 REJECTED，都必须具有在成功提交时写入的 `policyBinding { version }`，终态 decision 的政策版本必须与绑定一致。

不回填既有 PENDING，不从旧 decision 推断提交政策，不提供 ID-only 历史分支或新旧数据双读。测试库、样例数据及夹具按新模型重新创建；本轮只修改设计，没有重建或清空任何数据库。

完整政策定义直接随本类 policy 保存，均包含 id/title/description；不为旧 Profile v1 设计补充记录或 sidecar 集合。缺绑定、定义不完整、引用不存在或 decision 版本不一致都是数据不变量异常，失败关闭；不存在兼容性只读降级。

新模型运行以后，A 下已绑定的记录在发布 B 后继续使用 A，A 的完整定义随业务历史保留。这是新模型自身的审核规则，不是对上线前旧实现的兼容。已有合法终态不重写，未来发布仍遵循前述原子切换及必要恢复约束。

### 独立实时门禁

| 边界 | 本次绑定后的行为 |
| --- | --- |
| 人工审核政策、检查定义、提交内容 | 使用本次绑定版本和 snapshot；B 增加人工检查不强加到 A attempt |
| Reviewer 身份、accountStatus、精确权限、利益冲突 | 沿用本次请求可信身份及既有短期凭证/撤销窗口，本地事实最终事务复查；不把提交身份当 Reviewer 权限 |
| Version 批准的 admin/submittedBy 账号和 Developer 资格 | 继续按 BR-APP-011 与 BR-REV-018 的现行检查和 SYSTEM 自动拒绝/依赖失败语义 |
| Profile 决定 | 保留 BR-PRF-023–032 的现行门禁，不增加原本没有的 Auth Developer/Scope/DNS 调用 |
| Application 生命周期与平台暂停 | ACTIVE 是可决定前提；CLOSING/CLOSED 拒绝，SUSPENDED 继续允许审核修复 |
| Scope、URL/DNS、OAuth 技术安全复检 | Version 批准按当前独立契约，记录实际 catalog/preflight 版本，保留 Scope 已有 TTL/实例/在途窗口 |
| Profile 内容校验、公开指针 | 继续按现行字段安全规则及指针 CAS |
| 发布/运行 | 沿既有资格与运行门禁；不因审核政策退休本身撤销旧批准或改变发布资格 |

被冻结的是人工审核定义，preflightPolicyVersion、Scope Catalog 和共享安全校验不属于人工政策。若发布同时改人工规则与技术安全校验，分开版本化并按各自授权评审；不能把新人工检查藏进实时校验，迫使旧 attempt 补审。本次不设计存量整改、期限或复审流程。

### 新语义设计验收

Version 和 Profile 各覆盖：A 下成功提交→发布 B→A attempt 仍按 A 批准/拒绝；B 后新提交绑定 B；拒绝后重提绑定 B；提交/发布两个胜序及重试归属；错误 expectedPolicyVersion 无法决定目标 attempt；政策退休不改页面确认、终态或运行资格。权限/账号/资格、Scope、关闭和公开指针等实时门禁继续生效，SUSPENDED 仍可审核。

初始化与协议测试只创建完整的新模型数据，覆盖缺绑定/坏定义/错版本的失败关闭、统一字段与严格解码；不编写旧数据升级、旧客户端、新旧形状双读或维护切换验收。以上仍为待实施验收设计，不是本轮已运行的业务测试。

## 初始化说明

本次采用上节的新模型初始化及夹具重建，不提供旧实验数据库升级方案。Schema 仍通过显式初始化/迁移机制建立；这里的工程入口不代表兼容旧数据。原 v2/v3 变更过程只保留在历史文档和 Git 记录，不作为本次实施指令。

## 变更记录

- 2026-11-04：用户接受提交绑定与无旧模型兼容修订；App `a95bd13` / API `2dc002e` 已实现，完整 backend `check-full` 24/24 PASS。Gateway/Console 新契约消费及真实新政策发布另行验收；见[实施记录](../implements/2026-11-04-submission-bound-review-policy-implementation.md)。

- 2026-11-04：用户接受无旧模型兼容的提交政策绑定方案，开始实施；接受不代表交付完成。

- 2026-11-04：按用户确认的未上线前提，删除旧模型、旧数据和旧接口兼容，改为统一新模型初始化及单一契约交付。

- 2026-11-03：PROPOSED 修订采用提交时固定政策；替代退休打断待审决定，保留独立实时门禁及已交付历史，本次仅设计。

- 2026-10-26：用户接受正式发布治理方向；补发布主体、唯一 ACTIVE 原子切换、不可变历史、审计回执/未知恢复、正式读回与联合验收；不新增在线策略管理或虚构下一版政策。
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
