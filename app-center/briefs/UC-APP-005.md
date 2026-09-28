<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-005 --spec tools/brief-specs/UC-APP-005.json -->
# Brief — UC-APP-005：审核应用版本

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-005` 审核应用版本 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-REV-010`–`BR-REV-020`（11 条） |
| 外部引用 BR | `BR-VER-018`（来自 `UC-APP-002`） |
| ADR | `ADR-001`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/auth-developer-status-v1.md`、`platform/contracts/auth-scope-catalog-v1.md`、`platform/contracts/auth-system-principal-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

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

### 参与者

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

### 决定结果

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

### 输入

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

### 主流程

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

### 异常流程

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

### 最小领域行为

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

### 用例端口

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

### 数据模型变化

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

`oauth-redirects-reviewed` 要求 reviewer 确认 pkceRedirectUris 与 confidentialRedirectUris 中的 callback 分别适用于相应 client type；两个数组都为空时明确确认该版本未启用 OAuth/OIDC 回调。未来修改检查项必须使用新的 policy version；不能原地修改 v1 或 v2。`version_review_policies.version` 唯一，历史版本保留。所有新决定必须使用当前 ACTIVE v2；已经用 v1 作出的决定不重写。

### API 草图

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

### 测试与验收

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

### 已确认的实现边界

- `app.version.review` 的线格式已由 trusted-identity-v1 的 `permissions` claim 定义；
  权限申请、授予、暂停和撤销生命周期仍由后续 Auth Center 用例拥有。Developer Status、
  内部服务身份/allowlist 与 System principal resolve 均已有平台契约；App Center 不读取
  Auth 数据库，也不配置固定 SYSTEM Auth ID。
- ReviewPolicyProvider 首版由 App Center 本地 adapter 提供正式策略与历史版本；
  当前核心只实现了 port 契约和 fake 验证，生产启用前必须补齐不可变持久化实现。
- reviewer 访问未知自托管页面的 iframe/隔离浏览环境属于后续前端与安全运行环境，不属于本后端核心工作包，也不在当前注入 rpc-bridge。
- 批准时若当前 admin 或 submittedBy 已暂停，使用注入的 System Auth ID 和固定 reason 将 PENDING Review 与 SUBMITTED Version 原子迁移为 REJECTED。

## 业务规则（UC-APP-005 权威正文）

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-010 -->
### BR-REV-010：Reviewer 权限

Auth 是 reviewer 权限的权威来源。入口层验证身份和权限声明，UseCase 只接收可信 ReviewerIdentity。

本轮只有一个原子权限：`app.version.review`。查看审核队列是否也需要该权限由 Query 设计决定；批准、拒绝、撤销和发布不能因为一个笼统 `is_admin` 自动互相授权。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-011 -->
### BR-REV-011：利益冲突

以下任何条件成立都不能作出决定：

- reviewer.authId 等于 Application 当前 adminId。
- reviewer.authId 等于 ApplicationVersion.createdBy。
- reviewer.authId 等于 ApplicationReview.submittedBy。

检查必须在最终事务中基于当前 Application 管理员重新执行。未来加入 collaborators 后，是否把 collaborator 也视为利益冲突，需要由对应成员用例扩展本规则。

不提供隐藏的超级管理员绕过；紧急处置应使用独立、可审计的 revoke/下架用例。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-012 -->
### BR-REV-012：一次性决定

- 只有 status=`PENDING` 且 decision=null 的 Review 可以决定。
- 一个 Review 只允许写入一次 decision。
- 决定成功后不能原地修改 outcome、reason、检查项、审核人或时间。
- 两个 reviewer 并发决定时最多一个成功。

网络超时后客户端应查询 Review；重复 POST 不创建新决定，也不覆盖已有决定。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013 -->
### BR-REV-013：状态一致性

合法迁移只有：

```text
ApplicationReview: PENDING -> APPROVED
ApplicationVersion: SUBMITTED -> APPROVED

ApplicationReview: PENDING -> REJECTED
ApplicationVersion: SUBMITTED -> REJECTED
```

Review 和 Version 的结果必须相同。Version 内容必须等于 snapshot，且决定前 Version.revision 必须为 `sourceVersionRevision + 1`。不满足表示出现绕过用例的写入或数据损坏，应中止并告警，不能尝试自动修复。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014 -->
### BR-REV-014：Version revision 与审计

决定成功后 Version.revision 原子增加 1，updatedBy 记录 decision.decidedBy，updatedAt 等于 decision.decidedAt。人工决定的 decidedBy 是 reviewer authId；暂停触发的自动拒绝使用注入的 System Auth ID。

createdBy、createdAt、submittedBy 和 submittedAt 都不因审核决定改变。审核人和审核时间属于 ApplicationReview.decision。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-015 -->
### BR-REV-015：拒绝理由

- REJECT 必须提供 reason。
- reason 为 1–2000 个 Unicode code point。
- 不允许首尾 Unicode whitespace，不允许 Unicode `Cc` 控制字符。
- 校验通过后原样保存，不接受纯 whitespace。
- APPROVE 可以省略 reason；提供时遵循相同格式。

暂停检查触发的 System 自动拒绝不使用请求中的 reason，只使用本用例规定的固定文本。

拒绝理由是给开发者和审计人员阅读的纯文本，不允许 HTML。敏感数据和内部安全细节的书写规范属于 reviewer 操作政策。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016 -->
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

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-017 -->
### BR-REV-017：批准检查确认

- confirmedCheckIds 在业务上是集合；输入重复直接拒绝。
- APPROVE 时，每个 ID 必须存在于当前策略，并包含策略针对该 snapshot 要求的全部检查。
- 校验后按 Unicode code point 字典序保存。
- REJECT 时 confirmedCheckIds 必须是空数组；失败事实写入 reason，不伪装成批准确认。

confirmedCheckIds 表示 reviewer 明确确认已经完成策略要求，不表示系统自动证明网页安全。需要结构化 PASS/FAIL 证据时，再由真实审核流程引入 ReviewCheckResult，而不是现在保存任意 JSON。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-018 -->
### BR-REV-018：批准时重新验证

APPROVE 必须针对 ApplicationReview.snapshot 重新执行：

- DeveloperSuspensionChecker 对当前 adminId 与 Review.submittedBy 的暂停检查。
- ScopeCatalog requestable 检查。
- LaunchURLSubmissionPolicy 公网 HTTPS 与 DNS 地址策略检查。
- BR-VER-018 的 OAuth 回调双数组结构、规范 URL 与安全限制检查。

使用 snapshot 而不是当前 Version 拼装输入。通过后把 catalog revision 和 URL policy version 写入 decision.approvalValidation。

REJECT 不执行这些外部检查，避免 Auth 或 DNS 故障阻止 reviewer 记录拒绝事实。Auth 在 consent/token 路径仍拥有最终授权决定。

暂停检查在业务上是批准门禁：任一主体已暂停时，不返回普通校验错误，而是使用 System Auth ID 将 Review 与 Version 原子迁移为 REJECTED。依赖不可用时不能假设已暂停，Review 保持 PENDING。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-019 -->
### BR-REV-019：审核与发布分离

APPROVED Version 只是后续 ApplicationPublication 可以引用的候选。审核决定不得：

- 自动修改 test/grey/stable 槽位。
- 自动生成 OAuth client 或密钥。
- 自动向普通用户目录公开。

发布必须由独立用例产生新的权限检查、发布记录和历史。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-020 -->
### BR-REV-020：弱内容保证

reviewer 实际观察的是某个时间点 launchUrl 返回的自托管内容，而 snapshot 只能冻结 URL 与权限声明。decision 记录审核人、时间、策略和确认项，但不是远端字节的密码学证明。

因此 APPROVED 的准确语义是“该 snapshot 按记录的策略被 reviewer 接受”，不是“这个 URL 永远安全”。内容撤换检测、摘要、平台托管和紧急撤销属于后续能力。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-002`

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-018 -->
### BR-VER-018：版本化 OAuth 回调

`oauthRedirects` 是受审核的版本内容，不属于 client registration，也不从 launchUrl 推导：

```text
OAuthRedirectConfiguration {
  pkceRedirectUris: []RedirectURI
  confidentialRedirectUris: []RedirectURI
}
```

- 两个数组都必须存在且非 null，各包含 0–10 个不重复 URI。空数组表示该 Version 不为对应 client type 提供 OAuth/OIDC 回调。
- 两个数组之间也不得重复；同一个回调不能同时声称由 PUBLIC PKCE 和 CONFIDENTIAL secret client 使用。
- URI 必须是绝对 HTTPS URL，最多 2048 UTF-8 bytes；禁止 userinfo、fragment、wildcard、IP literal、localhost，以及 [BR-REV-007](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-007) 固定的 IANA `2026-05-22` special-use 域名或其子域。
- 禁止预占 OAuth/OIDC 响应参数 `code/state/iss/error/error_description/error_uri`。
- hostname 使用 non-transitional UTS #46 Lookup 转为小写 ASCII A-label；输入必须已经是规范表示，不静默改写。同一数组可以包含多个 hostname，以支持受审核的环境切换和域名迁移。
- callback hostname、path、query 和 port 可以不同；运行时始终做完整字符串精确匹配，不做前缀匹配。客户端必须控制回调处理，App Center 不向回调地址发起探测请求。
- 两个数组分别按 Unicode code point 排序。输入顺序不表达业务含义。

`ApplicationVersionOAuthConfig` 使用独立 collection 保存，但它是 Version 的依附实体：创建、编辑与 Version 使用同一事务和 revision，不能独立修改或删除。client identity 可以在 Version 前后独立登记；发布时检查目标渠道对应 registration/credential 的存在性，运行时按 client 固定渠道和 type 组合。Version 不保存 sector；sector 由 Auth 按 Application 管理，redirect hostname 变化不重建 clientId 或 sector。

## 架构决定（仅本次需要的章节）

### ADR-001：Scope Catalog 权威来源与缓存（`PROPOSED`）

#### 权威来源

Auth 是 Scope Catalog 唯一权威来源。Auth 提供可读取完整快照的内部接口：

```text
ScopeCatalogSnapshot {
  revision: int64
  scopes: []ScopeDefinition
  generatedAt: Instant
}
```

revision 必须在 Auth 内单调递增。提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 定义；跨服务 `ScopeDefinition` 首版投影和 gRPC 方法由 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md) 定义。

ScopeCatalog adapter 在完成校验时一并返回所使用的 snapshot revision。创建和修改草稿可以忽略它；UC-APP-004 将它写入 ApplicationReview，用于说明提交时依据的 Auth 目录版本。

#### 第一阶段缓存

App Center 的 ScopeCatalog adapter 使用每进程 read-through cache：

- TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 使用 Go duration 文本配置，未设置时默认 `5m`；显式值为空、无法解析、为零或负数时进程组装失败，不静默回退。
- 进程启动或 cache miss 时同步读取 Auth 快照。
- TTL 内直接使用缓存快照。
- TTL 到期时同步刷新；使用 singleflight 合并同一时刻的刷新请求。
- 刷新失败时不使用过期快照创建版本，返回 `ScopeCatalogUnavailable`。
- Auth revision 发生回退时视为不可用并 fail closed，避免用较旧快照覆盖进程已经观察到的较新事实。
- 不为此单独引入 Redis。

这是有界缓存，不是 App Center 自己的 Scope Catalog。缓存内容不能被 App Center 管理接口修改。

环境变量只由 config/composition boundary 读取；Cache adapter 通过构造参数接收已经校验的 TTL、Clock 与 snapshot source，不直接读取进程环境。真实 Auth transport 必须实现共享 gRPC 契约；测试可以使用实现同一生成接口的 Auth Server 或 port fake，不得在生产代码中硬编码目录。

#### 多阶段校验

- 创建 DRAFT：使用上述有界缓存，尽早发现无效 scope。
- 提交审核：重新确认 scope 仍允许新版本申请。
- reviewer 批准：再次确认 snapshot 中的全部 scope，并把所用 catalog revision 写入 decision.approvalValidation；详见 UC-APP-005。
- 放入发布槽位：再次确认 approved snapshot 中的 scope，并把所用 catalog revision 写入 PublicationHistory；UC-APP-007 首先应用于 test 槽位。
- consent/token/用户数据读取：Auth 必须以自己的当前规则做最终授权，不能相信 App Center 过去的校验结果。

Scope 启用状态和兼容投影按 [UC-AUTH-001 / BR-SCP-004](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 执行：App 继续消费 requestable，Auth 自己在 OAuth 运行阶段检查当前 enabled。缓存仍可能在 TTL 内使管理操作按旧目录通过；这些结果不保证后续 OAuth 可用，也不阻止 Auth 排除已停用 scope。App 不新增独立 runtimeEnabled 状态或同步修改已批准 snapshot。

因此短暂缓存不构成实际用户授权依据。

### ADR-006：Proto v1 与独立 API 仓库协作（`ACCEPTED`）

#### 决定

新协议在 API 仓库使用独立命名空间和目录：

```text
app_center/v1/...
package app_center.v1.<capability>
```

`v1` 只表示共享协议命名空间，不进入 App Center 的领域 package、collection 名或业务身份。Schema revision 由 migration ledger 中的 `0001`、`0002` 等迁移 ID 管理，collection 名保持无版本的业务命名。

Proto 源文件继续由独立 API 仓库拥有。App Center 服务仓库固定引用一个明确的 API repository revision；不得依赖浮动分支或在服务仓库手工维护生成代码的私有修改。

协作顺序为：

1. Domain 与 UseCase 通过自己的 Command/Result 类型稳定业务行为。
2. 在 API 仓库增加或修改 v1 Proto、error reason 和生成配置。
3. 生成代码并在 API 仓库通过检查后提交。
4. App Center 更新固定 revision。
5. Transport adapter 显式完成 Proto 与 UseCase 类型转换。
6. 两个仓库分别使用各自可审查的 commit。

Proto 不直接复用 Domain struct，也不把生成 message 传入 Domain。字段 presence、oneof、timestamp、enum unknown value 和 transport validation 在 adapter 边界处理。

#### 协议演进

即使系统尚未上线，已提交到共享 API 仓库的 v1 字段编号也保持稳定：

- 不重用删除字段的编号或名称，使用 `reserved`。
- enum 保留明确的 `UNSPECIFIED = 0`，业务上不接受时由 adapter 拒绝。
- 不把数据库内部字段、comparison key、技术计数器或 secret 暴露为公共字段。
- 写请求不接受可信身份、服务端状态和审计字段。
- 分页 cursor 是不透明 bytes/string，不承诺内部编码。
- Error reason 与 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 的稳定业务 code 对齐。

HTTP annotation 和 gRPC service 共享同一 Proto 语义。HTTP API 使用 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 定义的标准状态映射。

#### 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/app-center-api-routing.md`：App Center API 路由 v1 契约

#### 路由映射

App Center 的每个 HTTP 资源在 Proto 内部使用的路径**不含服务前缀**。Gateway 为外部请求增加且只增加一个服务前缀 `/app-center`。

首个正式资源 CreateApplication 的映射是：

| 层 | 方法与路径 | 说明 |
| --- | --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications` | 客户端唯一可见的地址；`app-center` 是服务前缀 |
| Gateway | 剥离前缀 `/app-center` | 只做前缀剥离，不重写其余路径 |
| 内部（Gateway → App Center） | `POST /v1/applications` | Proto `google.api.http` annotation 声明的路径；请求体 `body: "*"` |
| gRPC | `/app_center.v1.application.Application/CreateApplication` | proto package `app_center.v1.application`，service `Application`，rpc `CreateApplication` |

UC-APP-005 审核决定命令遵循同一映射规则：

| 层 | 方法与路径 |
| --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| Gateway | 只剥离前缀 `/app-center` |
| 内部（Gateway → App Center） | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| gRPC | `/app_center.v1.application_review.ApplicationReview/DecideApplicationVersionReview` |

规则：

- Gateway 必须按**服务名到前缀**的映射表工作，不得把 `/app-center` 硬编码进业务路径，也不得同时改写内部资源路径。
- 前缀剥离后必须保留查询串与请求体。
- 内部路径与 gRPC full method 由 Proto 定义，App Center 的 HTTP 路由注册必须与 Proto annotation 一致；两者不得各写一份。
- 写请求只通过请求体传递资源字段；可信身份只通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 定义的 `x-iwut-identity` 传递，路径或 query 不承载身份。
- 未匹配的服务前缀或缺少前缀的外部请求由 Gateway 拒绝，不转发给 App Center。

#### gRPC-Web 终止

- gRPC-Web 在 **Traefik** 终止，不进入 App Center 进程。
- App Center 后端只暴露**原生 gRPC**；不嵌入 `grpc-web` wrapper，也不注册 gRPC-Web 专用的 HTTP handler。
- 浏览器流量由 Traefik 完成 gRPC-Web ⇄ gRPC 转换后，以原生 gRPC 到达 App Center；身份键仍为 metadata `x-iwut-identity`。
- 因此 App Center 不为 gRPC-Web 增加 CORS、content-type 或协议转换配置；这些属于 Traefik。

#### 契约测试要求

外部到内部的映射必须由**自动化契约测试**机械验证，不能只靠文档。测试至少断言：

1. Proto HTTP annotation 的内部路径等于 `POST /v1/applications`。
2. 外部路径等于服务前缀 `/app-center` 加内部路径，即 `POST /app-center/v1/applications`。
3. 前缀映射只剥离 `/app-center`，得到的内部路径与第 1 项一致。
4. gRPC full method 等于 `/app_center.v1.application.Application/CreateApplication`。
5. 写请求 message 只包含 `name`，不包含身份字段（`authId`、`developer_status`）、服务端字段（`id`、`adminId`、`createdAt`）或持久化技术字段。
6. 响应 message 不包含 `nameKey`、`nextVersionSequence`、`nextProfileRevisionSequence` 或其它内部技术字段。
7. 审核决定的外部/内部路径与上述 UC-APP-005 映射精确一致，gRPC full method 使用同一生成 service。
8. UC-APP-005 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

外部路径可以作为 contract constant / fixture 存在于测试中，但它必须与内部路径、前缀和 gRPC method 在同一测试里被自动验证，任何一侧漂移都必须让测试失败。

### `platform/contracts/auth-developer-status-v1.md`：Auth Developer Status v1 跨服务契约

#### gRPC 方法

```text
/auth_center.v1.developer_status.DeveloperStatusDirectory/BatchGetDeveloperStatuses
```

```proto
service DeveloperStatusDirectory {
  rpc BatchGetDeveloperStatuses(BatchGetDeveloperStatusesRequest)
      returns (BatchGetDeveloperStatusesResponse);
}

message BatchGetDeveloperStatusesRequest {
  repeated string auth_ids = 1;
}

message BatchGetDeveloperStatusesResponse {
  repeated DeveloperStatusEntry entries = 1;
}

message DeveloperStatusEntry {
  string auth_id = 1;
  DeveloperStatus developer_status = 2;
}

enum DeveloperStatus {
  DEVELOPER_STATUS_UNSPECIFIED = 0;
  DEVELOPER_STATUS_PENDING = 1;
  DEVELOPER_STATUS_APPROVED = 2;
  DEVELOPER_STATUS_REJECTED = 3;
  DEVELOPER_STATUS_SUSPENDED = 4;
}
```

该方法没有 `google.api.http` annotation，不经 Gateway 暴露，也不提供 gRPC-Web。

#### 完整批量语义

- 请求包含 `1..100` 个唯一 Auth ID。
- 成功响应 entries 数量与请求相同，顺序一致，auth_id 逐项相等。
- `DEVELOPER_STATUS_UNSPECIFIED` 永远不能出现在成功响应。
- 任一主体未知或状态无法读取时整个 RPC 失败，不返回部分 entries。
- 请求和响应只包含 opaque authId 与 Developer 状态，不投影用户资料。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证
内部服务身份。Auth Center 在验签后按固定 full method → `auth.developer-status.read`
映射检查 caller 注册表；测试 server 不能被当作生产无认证入口。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_DEVELOPER_STATUS_READ_FORBIDDEN` |
| 批量输入非法 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_DEVELOPER_STATUS_QUERY` |
| 任一主体未知或不适用 | `NOT_FOUND` | `ERROR_REASON_DEVELOPER_STATUS_NOT_FOUND` |
| 权威状态暂不可读取或记录损坏 | `UNAVAILABLE` | `ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含 MongoDB 查询、用户资料、服务凭证或堆栈。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. package/service/rpc 的 full method 精确一致。
2. request 只有 `auth_ids = 1`，没有用户或服务身份字段。
3. response 和 enum 字段号保持稳定。
4. entries 与请求一一对应并保持顺序。
5. UNSPECIFIED、缺项、额外项、重复项或错序不能作为成功结果。
6. INVALID_ARGUMENT、NOT_FOUND、UNAVAILABLE 和稳定 reason 映射一致。
7. App Center 测试 Auth Server 实现同一生成接口，不维护手写 wire model。

### `platform/contracts/auth-scope-catalog-v1.md`：Auth Scope Catalog v1 跨服务契约

#### gRPC 方法

首版只提供内部原生 gRPC：

```text
/auth_center.v1.scope_catalog.ScopeCatalog/GetScopeCatalogSnapshot
```

Proto 结构：

```proto
service ScopeCatalog {
  rpc GetScopeCatalogSnapshot(GetScopeCatalogSnapshotRequest)
      returns (GetScopeCatalogSnapshotResponse);
}

message GetScopeCatalogSnapshotRequest {}

message GetScopeCatalogSnapshotResponse {
  int64 revision = 1;
  google.protobuf.Timestamp generated_at = 2;
  repeated ScopeDefinition scopes = 3;
}

message ScopeDefinition {
  string name = 1;
  bool requestable = 2;
}
```

不声明 `google.api.http` annotation，不经 Gateway 暴露，不提供浏览器或 gRPC-Web 入口。

#### 快照语义

- `revision` 必须大于零，并遵循 [BR-SCP-003](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- `requestable` 固定投影 Auth 当前 `enabled`，状态定义唯一引用 [BR-SCP-004](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。停用项仍返回，值为 false；不增加独立 runtimeEnabled 字段。
- App 消费方继续把 `requestable = true` 的 name 用于版本申请、审核和发布规则的目录检查；它不是最终用户授权结果。Auth OAuth 路径直接检查自己的当前权威状态，不以 App 缓存或历史批准快照代替。
- 消费方遇到未知追加字段时必须忽略，以保持向后兼容。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证内部服务身份。Auth Center 在验签后按固定 full method → `auth.scope-catalog.read` 映射检查 caller 注册表；认证成功不自动产生读取权限。

测试 Auth Server 可以验证 consumer 行为，但生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_SCOPE_CATALOG_READ_FORBIDDEN` |
| 权威目录暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含凭证、存储查询、连接地址、Scope 私有元数据或堆栈。调用方不得把失败时持有的过期快照包装成本次成功响应。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. gRPC full method 与 package/service/rpc 名称准确。
2. request message 没有业务字段或用户身份字段。
3. response 字段号和类型与本契约一致。
4. 空目录编码为空列表，不是错误或伪造占位 Scope。
5. duplicate/empty name、非正 revision、无效 generatedAt 或非稳定排序不能作为成功快照。
6. `UNAUTHENTICATED`、`PERMISSION_DENIED`、`UNAVAILABLE` 与稳定 reason 映射一致。
7. App Center E2E 的测试 Auth Server 实现同一生成接口，不维护另一份手写 wire model。
8. Provider 的 enabled 状态与 requestable 投影一致，启停递增 revision；完整快照保留停用项，App 的既有布尔校验无需新增状态分支。

### `platform/contracts/auth-system-principal-v1.md`：Auth System Principal v1 跨服务契约

#### 目的与所有权

Auth Center 拥有不可登录的 SYSTEM principal 及其 opaque Auth ID。消费方只按稳定 purpose 解析 ID，不创建、猜测或通过部署配置复制它。提供方业务语义由 [UC-AUTH-003](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md) 拥有。

#### gRPC 方法

```text
/auth_center.v1.system_principal.SystemPrincipalDirectory/ResolveSystemPrincipal
```

```proto
service SystemPrincipalDirectory {
  rpc ResolveSystemPrincipal(ResolveSystemPrincipalRequest)
      returns (ResolveSystemPrincipalResponse);
}

enum SystemPrincipalPurpose {
  SYSTEM_PRINCIPAL_PURPOSE_UNSPECIFIED = 0;
  SYSTEM_PRINCIPAL_PURPOSE_APP_CENTER_REVIEW_AUTO_REJECTION = 1;
}

message ResolveSystemPrincipalRequest {
  SystemPrincipalPurpose purpose = 1;
}

message ResolveSystemPrincipalResponse {
  string auth_id = 1;
  SystemPrincipalPurpose purpose = 2;
}
```

只提供内部原生 gRPC，不声明 HTTP annotation，不经 Gateway，不提供 gRPC-Web。

#### 调用与缓存语义

- 调用使用 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，同时要求 `auth.system-principal.resolve` permission 与 caller 的 purpose allowlist。
- Auth 启动时幂等 provision 已知 purpose；同一 purpose 在同一环境中映射到唯一、稳定、非空 authId。
- App Center 不以该 ID 作为启动依赖。首次需要自动审核决定时查询；成功结果可缓存到进程结束。
- 查询失败或返回不匹配 purpose/空 ID 时不得缓存，当前决定 fail closed；后续请求可重试。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 服务身份缺失/无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 无 RPC 或 purpose 权限 | `PERMISSION_DENIED` | `ERROR_REASON_SYSTEM_PRINCIPAL_READ_FORBIDDEN` |
| purpose 未指定/未知 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_SYSTEM_PRINCIPAL_PURPOSE` |
| principal 不存在 | `NOT_FOUND` | `ERROR_REASON_SYSTEM_PRINCIPAL_NOT_FOUND` |
| 存储暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SYSTEM_PRINCIPAL_UNAVAILABLE` |

#### 契约测试要求

Provider/consumer 必须验证 full method、字段号、purpose 枚举、稳定 ID、身份与 purpose allowlist、失败不缓存，以及 App 自动拒绝最终写入 Auth 返回的 SYSTEM authId。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### Auth Center 固定授权映射

| gRPC 方法 | 必需 permission |
| --- | --- |
| `ScopeCatalog/GetScopeCatalogSnapshot` | `auth.scope-catalog.read` |
| `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | `auth.developer-status.read` |
| `SystemPrincipalDirectory/ResolveSystemPrincipal` | `auth.system-principal.resolve` |
| `UserIdentityService/IssueUserIdentityFromSession` | `auth.identity.issue` |

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-005`（use-cases/UC-APP-005-decide-application-version-review.md）：旧实现观察、后续用例、迁移说明、变更记录
- `UC-APP-002`（use-cases/UC-APP-002-create-application-version.md）：目标与范围、当前 ApplicationVersion、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、后续接口工作、迁移说明、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/auth-developer-status-v1.md`（docs 根级共享文档）：目的与所有权、兼容性
- `platform/contracts/auth-scope-catalog-v1.md`（docs 根级共享文档）：目的与所有权、兼容性、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：ENV 配置、契约测试要求

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-005-decide-application-version-review.md` | 618 | `7a595b829792` |
| `use-cases/UC-APP-002-create-application-version.md` | 475 | `29c68f062589` |
| `adr/ADR-001-scope-catalog-cache.md` | 114 | `1e3b8ddba7e4` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/auth-developer-status-v1.md` | 91 | `24ff16ab6589` |
| `platform/contracts/auth-scope-catalog-v1.md` | 94 | `4c1bae67fbf9` |
| `platform/contracts/auth-system-principal-v1.md` | 57 | `5191d48e8707` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `cfaa02fcbb8c` |
| `platform/contracts/trusted-service-identity-v1.md` | 88 | `3c091a708b32` |
