<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-016 --spec tools/brief-specs/UC-APP-016.json -->
# Brief — UC-APP-016：审核应用公开资料修订

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-016` 审核应用公开资料修订 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PRF-023`–`BR-PRF-032`（10 条） |
| 外部引用 BR | `BR-PRF-003`–`BR-PRF-005`（3 条）（来自 `UC-APP-013`） |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

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

### 目标与边界

> 具有 `app.profile.review` 权限且不存在利益冲突的 Reviewer，对一条 PENDING ApplicationProfileReview 作出一次性批准或拒绝决定；批准时资料自动成为当前公开资料，拒绝时已有公开资料保持不变。

本用例负责：

- 校验 Reviewer 权限、利益冲突、Review/Revision 状态和乐观并发 revision。
- 根据版本化 ProfileReviewPolicy 记录批准或拒绝决定。
- 原子同步 ApplicationProfileReview 与 ApplicationProfileRevision 状态。
- 批准时原子更新 `currentPublishedProfileRevisionId`。

本用例不负责：

- Reviewer 分配、多人会签或修改既有 decision。当前不建立系统内申诉状态或接口；需要申诉时直接联系平台运营人员。
- 管理员手动发布资料或回滚到旧 ProfileRevision。
- 创建或编辑资料草稿；服务端不提供恢复 REJECTED Revision 的命令。
- 设置 Test/Grey/Stable、修改 FilterRule 或审核 ApplicationVersion。
- 使用 AI 审核 DRAFT 或自动批准、拒绝。未来 AI 审核的结论效力与状态模型由独立用例定义；当前只有人工 Reviewer 能写入本用例的 decision。
- 紧急隐藏公开资料。该需求属于由 Application admin 或 SysAdmin 发起的 Application 禁用，不是撤销某条 ProfileRevision。
- Auth 权限授予/签发、管理查询和前端；本次后端实现契约见文末。

### 参与者与输入

可信身份：

```text
ReviewerIdentity {
  authId
  permissions
}
```

Command：

```text
DecideApplicationProfileRevisionReview {
  applicationId
  profileRevisionId
  profileReviewId
  expectedProfileRevisionRevision
  expectedCurrentPublishedProfileRevisionId: ApplicationProfileRevisionId | NONE // APPROVE 时使用
  expectedPolicyVersion
  outcome: APPROVE | REJECT
  confirmedCheckIds
  reason?
}
```

authId 和 permissions 来自可信身份上下文。decision、decidedBy、decidedAt、Review/Revision 状态和当前公开指针不能由请求指定。

### 成功结果

批准：

```text
ApplicationProfileReview: PENDING -> APPROVED
ApplicationProfileRevision: SUBMITTED -> APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = profileRevisionId
ApplicationProfile.workingProfileRevisionId = null
```

拒绝：

```text
ApplicationProfileReview: PENDING -> REJECTED
ApplicationProfileRevision: SUBMITTED -> REJECTED
ApplicationProfile.currentPublishedProfileRevisionId = unchanged
ApplicationProfile.workingProfileRevisionId = null
```

两种结果都会写入一次性 decision，并把 ProfileRevision.revision 增加 1。

### 主流程

1. 从可信 ReviewerIdentity 取得 authId 和 permissions，校验 Command。
2. 加载 Application、ApplicationProfile、ProfileRevision 和 ProfileReview，确认它们的归属关系。
3. 确认可信 ReviewerIdentity 包含 `app.profile.review`，并且 Reviewer 不是当前 admin、Revision 创建者或 Review 提交者。
4. 确认 Review 为 PENDING 且 decision 为空；ProfileRevision 为 SUBMITTED，revision 匹配 expectedProfileRevisionRevision，当前内容与 snapshot 一致，并且 ApplicationProfile.workingProfileRevisionId 指向目标 Revision。
5. 加载 expectedPolicyVersion 对应的 ACTIVE ProfileReviewPolicy，并计算该 snapshot 所需检查项。
6. outcome=APPROVE 时：
   - 确认 confirmedCheckIds 完整覆盖所需检查；
   - 重新验证 snapshot 的 displayName、description 和 icon；
   - 确认当前公开指针等于 expectedCurrentPublishedProfileRevisionId；
   - 构造 APPROVED decision。
7. outcome=REJECT 时：确认拒绝理由有效、confirmedCheckIds 为空，构造 REJECTED decision。
8. 在同一原子边界重新确认步骤 2–7 的状态、权限和并发条件，然后写入 decision、同步 Review/Revision 状态和审计；批准时同时替换当前公开资料指针。
9. 返回决定后的 Review、ProfileRevision，以及当前公开资料 ID。

### 失败结果

- 缺少可信 Reviewer 身份：`ReviewerIdentityRequired`。
- 缺少 `app.profile.review`：`ApplicationProfileReviewPermissionRequired`。
- Reviewer 存在利益冲突：`ApplicationProfileReviewConflictOfInterest`。
- ID、revision、outcome、policy version 或 APPROVE 所需公开指针前置值非法：`InvalidApplicationProfileReviewDecision`。
- Application、Revision、Review 不存在或归属不匹配：`ApplicationProfileReviewNotFound`。
- Review 不再是 PENDING、已有 decision 或 Revision 不再是 SUBMITTED：`ApplicationProfileReviewAlreadyDecided` 或 `ApplicationProfileReviewStateConflict`。
- ProfileRevision revision 不匹配：`ApplicationProfileRevisionConflict`。
- APPROVE 时当前公开指针已改变：`ApplicationProfilePublicationConflict`。
- Revision/Review 内容或 revision 关系不一致：`ApplicationProfileReviewStateInconsistent`。
- 策略不存在、已 RETIRED 或 expectedPolicyVersion 不是当前可用版本：`ProfileReviewPolicyUnavailable`。
- 批准检查不完整或拒绝理由非法：`ProfileReviewChecksIncomplete` 或 `InvalidProfileReviewReason`。
- 批准时 snapshot 不再满足资料规则：`InvalidApplicationProfileContent`。
- 持久化失败：内部失败，不产生部分 decision、状态或公开指针变化。

归属不匹配按 NotFound 处理。网络超时后查询既有 Review；decision 不会因普通重试被覆盖。

### 领域模型影响

ApplicationProfileReview.decision 从 null 一次性变为：

```text
ApplicationProfileReviewDecision {
  outcome: APPROVED | REJECTED
  policyVersion
  confirmedCheckIds
  reason?
  decidedBy
  decidedAt
}
```

ApplicationProfileReview、ApplicationProfileRevision 和 ApplicationProfile 仍是独立聚合边界，由应用服务在本地原子操作中协调。批准自动公开是这三个聚合之间的业务一致性要求，不意味着它们需要存储在同一个文档中。

### 验收场景

- 具有 `app.profile.review` 且无利益冲突的 Reviewer 可以决定一致的 PENDING Review。
- APPROVE 原子写入 decision、把 Review/Revision 设为 APPROVED，并替换当前公开资料。
- REJECT 要求有效理由，把 Review/Revision 设为 REJECTED，且旧公开资料保持不变。
- Reviewer 不能审核自己创建、提交或当前管理的资料。
- 两个并发决定最多一个成功，decision 不可覆盖。
- stale ProfileRevision revision、snapshot 漂移或状态不一致均不会产生部分决定。
- APPROVE 的公开指针前置值过期时不会覆盖其他已批准资料。
- 批准不会创建或修改 Test/Grey/Stable，也不会产生资料回滚入口。

### 实现依赖与交付边界

UC013–015 已完成并通过完整 backend 验收；本工作包交付 App Center Domain、UseCase、原子 Mongo Repository、migration、资源化 HTTP/原生 gRPC、Wire 与真实 Mongo E2E。权限仅来自可信请求，不调用 Auth Catalog、Developer Status、System principal、DNS 或资产服务。生产 Auth 的 `app.profile.review` 授予/签发尚未实现，作为独立外部交付记录，不以测试签名 token 冒充生产权限链路完成。

复用 Application `coordinationRevision` 真写栅栏，最终事务重查 BR-PRF-023–032 的本地事实。策略在同一事务中取得 ACTIVE 版本并使用真实技术写栅栏，使并发退休与决定可串行；不可变策略定义与可变 status/技术协调字段分离，不提供运行时策略 CRUD。时钟经端口取得，事务重试不重新生成决定时间。revision 和技术计数器溢出失败并回滚。

Review、Revision、ApplicationProfile 分别持久化。新增 migration 升级 Review 的 APPROVED/REJECTED 与 decision 结构、状态一致性、理由与审计约束，保留既有唯一索引；建立独立 `profile_review_policies` 的 version 唯一索引并写入首版策略。migration/readiness 和迁移账本测试同步更新。已决定对象只能读取，不可再次写决定。

REJECT 的候选重建必须保持原始内容，先验证 BSON 字段存在/类型、metadata、路径、sourceRevision、当前 PENDING attempt、工作指针与逐字 snapshot 相等；不能调用无条件复检内容的提交/工作指针 helper，也不能规范化后再比较。仅 APPROVE 调用资料内容复检。决定后的 REJECTED 响应/历史重建同样保留原文。Revision 与 Review validator 仅在 REJECTED 状态把内容长度/字符规则放宽为完整 string/string-or-null 类型约束，其余结构、审计、decision 约束保持严格；其它状态仍要求完整资料内容规则。不得使用运行时 bypassDocumentValidation。

合法终态 Review 返回 `ApplicationProfileReviewAlreadyDecided`；尚为 PENDING 但目标修订非 SUBMITTED 返回 `ApplicationProfileReviewStateConflict`。非法状态/decision 组合、悬空/错误工作指针、内容漂移、sourceRevision 或 attempt 关系异常返回 `ApplicationProfileReviewStateInconsistent`，HTTP500/gRPC INTERNAL，并输出不含资料正文、reason、凭据或数据库错误的安全 ERROR 告警；不自动修复。stale revision 与公开指针冲突是业务冲突，不冒充内部异常。

完整验收执行 `make check-auth-app`（包含 backend 与现有真实 Auth 回归），覆盖 BR、双协议及实际生成 HTTP 客户端、真实副本集 validators/indexes、回滚、并发决定、管理员转让和策略退休、公开指针前置冲突、revision 溢出、REJECT 坏内容与后续创建新 DRAFT。跨服务回归不代表尚未实现的 Auth 资料审核权限签发已验收。冻结 service/API/docs/涉及的 Auth 来源后验收，API 先本地提交再提交服务 gitlink；不得 push。

### API 实现契约

内部 `POST /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}/decision`；外部只加 `/app-center`。原生 gRPC 为 `app_center.v1.application_profile_review.ApplicationProfileReview/DecideApplicationProfileRevisionReview`。

Proto Request 使用匹配路径模板的显式 json_name，正文 annotation 为 `body: "command"`；HTTP 正文仅为 command 字段，不接受身份、快照、归属、decision 或审计注入，不允许 query 覆盖。命令字段如下：

```json
{
  "expectedProfileRevisionRevision": "2",
  "expectedCurrentPublishedProfileRevisionId": null,
  "expectedPolicyVersion": "app-profile-review-v1",
  "outcome": "APPROVE",
  "confirmedCheckIds": ["content-policy-reviewed", "icon-content-reviewed"]
}
```

expectedProfileRevisionRevision 是正 int64（ProtoJSON 表达），不使用 If-Match。expectedCurrentPublishedProfileRevisionId 使用 `google.protobuf.Value` 保留 presence：APPROVE 时必须显式 string(UUIDv7) 或 null（NONE），缺失或其它类型非法；REJECT 时省略该字段，不检查或改变公开指针。outcome 只接受 APPROVE/REJECT。expectedPolicyVersion 为 1–50 ASCII `[A-Za-z0-9._-]`。reason 使用可选 string，省略代表无理由，显式空串非法；REJECT 必须有有效 reason，原样保存、不规范化。

HTTP200 返回 `{ "profileRevision": <完整决定后修订>, "review": <完整审核记录>, "currentPublishedProfileRevisionId": <string|null> }`，ETag 是决定后 ProfileRevision.revision。保留已提交的 ReviewRecord.decision 的 field 10 与 `google.protobuf.Value` 类型；PENDING 输出 null，终态输出对象：outcome（APPROVED/REJECTED）、policyVersion、confirmedCheckIds（排序）、reason（string/null）、decidedBy、decidedAt（UTC RFC3339）。其它已提交字段编号/类型不改。

错误映射：身份401/UNAUTHENTICATED；缺权限或利益冲突403/PERMISSION_DENIED；不存在或路径归属不匹配404/NOT_FOUND；非法输入、reason、checks或批准内容400/INVALID_ARGUMENT；已决定、状态/revision/公开指针冲突或策略不可用409/ABORTED；内部不变量或基础设施失败500/INTERNAL。错误码稳定且不泄漏存储细节。响应丢失后的管理查询仍单独交付，不在本 UC 添加 GET。

## 业务规则（UC-APP-016 权威正文）

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-023 -->
### BR-PRF-023：Reviewer 权限与利益冲突

决定者必须具有 Auth 授予的 `app.profile.review` 权限，并且 authId 不等于：

- Application 当前 adminId；
- ApplicationProfileRevision.createdBy；
- ApplicationProfileReview.submittedBy。

Reviewer 权限只从本次请求的可信 ReviewerIdentity 读取；当前 admin 等 App Center 本地事实在最终原子写入时重新确认。`app.version.review` 不隐式授予资料审核权限，通用 `is_admin` 也不构成绕过。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-024 -->
### BR-PRF-024：一次性决定与前置状态

只有 status=`PENDING` 且 decision=null 的 ApplicationProfileReview 可以决定；对应 ProfileRevision 必须为 SUBMITTED，revision 等于 expectedProfileRevisionRevision。

一个 Review 只写入一次 decision。并发决定最多一个成功；已决定 Review 的 outcome、reason、检查项、审核人和时间都不能原地修改。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-025 -->
### BR-PRF-025：Review、Revision 与 snapshot 一致性

作出决定前必须满足：

- Review、ProfileRevision 与 Application 属于同一路径；
- ProfileRevision 当前 displayName/description/icon 等于 Review.snapshot；
- `ProfileRevision.revision = Review.sourceRevision + 1`；
- Review 是该 ProfileRevision 当前 PENDING attempt。

发现内容漂移、悬空引用或 revision 关系异常时中止并告警，不自动修复。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-026 -->
### BR-PRF-026：状态同步

合法决定迁移只有：

```text
ApplicationProfileReview: PENDING -> APPROVED
ApplicationProfileRevision: SUBMITTED -> APPROVED

ApplicationProfileReview: PENDING -> REJECTED
ApplicationProfileRevision: SUBMITTED -> REJECTED
```

Review 与 ProfileRevision 的结果必须相同。决定不修改 snapshot、sourceRevision、submittedBy 或 submittedAt。
无论批准还是拒绝，决定同时清空指向目标修订的 `ApplicationProfile.workingProfileRevisionId`，释放下一份 DRAFT 的工作位。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-027 -->
### BR-PRF-027：决定理由

- REJECT 必须提供 reason；APPROVE 可以省略。
- 非空 reason 为 1–2000 个 Unicode code point。
- 首尾不允许 Unicode whitespace，不允许 Unicode `Cc` 控制字符，也不接受纯 whitespace。
- reason 是纯文本，不解释 HTML 或 Markdown。

校验后原样保存。Reviewer 不应在 reason 中写入敏感学生资料或无需向开发者公开的安全细节。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028 -->
### BR-PRF-028：版本化资料审核策略

Reviewer 提交自己实际阅读的 expectedPolicyVersion。App Center 拥有不可变、可按版本读取的 ProfileReviewPolicy：

```text
ProfileReviewPolicy {
  version
  requiredChecks
  status: ACTIVE | RETIRED
}
```

APPROVE 时 confirmedCheckIds 使用集合语义，并完整覆盖策略对 snapshot 要求的检查；REJECT 时 confirmedCheckIds 为空。历史 policy 保留用于解释既有 decision，RETIRED policy 不用于新决定。

首版策略由 App Center migration 写入：version=`app-profile-review-v1`、status=`ACTIVE`，固定要求以下两项：

- `content-policy-reviewed`：Reviewer 已检查名称、描述符合内容规范。
- `icon-content-reviewed`：Reviewer 已检查图标内容合规；icon 为空时明确确认不适用，仍提交该检查项。

策略内容不可原地修改；变更检查项使用新 version，历史定义保留。同版本已有不同定义时 migration 失败，不覆盖。首版不提供策略管理或查询接口。confirmedCheckIds 不接受重复、未知或缺失项，持久化按 ID 排序；REJECT 必须为空。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-029 -->
### BR-PRF-029：批准时资料复检

APPROVE 针对 Review.snapshot 重新应用 [BR-PRF-003](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005)。

当前 snapshot 包含 displayName、description 和可空 icon。icon 只按不透明字符串规则复检，不调用外部资产服务。REJECT 不执行批准复检，避免校验故障阻止 Reviewer 记录拒绝事实。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030 -->
### BR-PRF-030：批准后自动公开

APPROVE 必须提供 Reviewer 作出决定时观察到的 `expectedCurrentPublishedProfileRevisionId`，其值是某个 ProfileRevision ID 或明确的 `NONE`。它必须与当前指针匹配，再与以下变化处于同一原子边界：

```text
ProfileRevision.reviewStatus = APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = profileRevisionId
```

管理员不需要第二次 Publish 操作。指针前置值使两个针对不同 ProfileRevision 的并发批准不会静默相互覆盖；后一个 Reviewer 必须重新读取已改变的公开资料后再决定。旧的当前公开 Revision 保留 APPROVED 状态和审核历史，但首版不提供重新选择它或回滚资料的命令。

资料自动公开不创建 stable Version。没有兼容 stable 槽位时，Application 仍不进入普通用户候选目录。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031 -->
### BR-PRF-031：拒绝终止修订且不改变当前公开资料

REJECT 只把目标 Review/Revision 迁移为 REJECTED，并记录理由。`currentPublishedProfileRevisionId` 保持不变；没有既有公开资料时继续为空。

REJECTED 是该 ProfileRevision 的终态：服务端不提供 `REJECTED -> DRAFT`、复制或恢复命令，也不修改 ApplicationVersion 或发送通知。Review snapshot、decision、Revision 内容和审计事实保持不变。

重新编辑是网页端便利行为：网页端读取被拒绝资料并预填创建表单，然后调用 [UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md) 创建一份新 DRAFT。新草稿获得独立的 profileRevisionId、sequence 和创建审计；App Center 不记录它与被拒绝 Revision 的复制关系。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-032 -->
### BR-PRF-032：Revision、审计与原子决定

决定成功后 ProfileRevision.revision 增加 1，updatedBy 记录 Reviewer authId，updatedAt 等于 decidedAt。createdBy、createdAt、submittedBy 和 submittedAt 保持不变。

以下事实全部成功或全部失败：

- 可信 ReviewerIdentity 权限、利益冲突、Review/Revision 状态与 revision 的最终检查；
- policy 与 confirmedCheckIds 校验；
- decision 写入和 Review 状态迁移；
- ProfileRevision 状态、revision 与更新审计变化；
- ApplicationProfile.workingProfileRevisionId 的匹配检查与清空；
- APPROVE 时当前公开资料指针前置值检查与替换。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-013`

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003 -->
### BR-PRF-003：displayName

- 是面向普通用户的公开显示名称，不承担路由、唯一键或授权职责。
- 输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–80 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 不要求全局唯一，也不要求在同一管理员或 Application 范围内唯一。
- Application.name 不作为 displayName 的默认值；调用者必须明确提供。

公开展示时仍必须按普通文本转义。displayName 不是 HTML、Markdown 或富文本。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004 -->
### BR-PRF-004：description

- description 是可空的公开应用简介；没有简介时保存 `null`，不保存空字符串。
- 非空输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–1000 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 当前只保存纯文本，不解释 HTML、Markdown、链接或富文本语法。

公开展示时必须按普通文本转义。若未来需要多段或富文本简介，应通过新用例和明确的内容安全规则扩展，而不是放宽当前字段的隐式解释。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005 -->
### BR-PRF-005：完整资料快照与图标边界

- 一条 ApplicationProfileRevision 表示一版完整资料，而不是字段 patch。
- 本用例的完整快照由 displayName、description 和 icon 构成；缺失 displayName 不会回退到 Application.name。
- ProfileRevision 不复制 ApplicationVersion 的 versionLabel、launchUrl、RPC 声明、capabilities、scopes 或发布状态。
- icon 可为 `null`；非空值按 Unicode NFC 规范化，长度为 1–512 个 Unicode code point，首尾不允许 Unicode whitespace，不允许 `Cc/Cf/Cs/Zl/Zp`。
- icon 是不透明纯字符串；App Center 不解析 scheme、不验证资产存在性、不请求指向内容，也不把它宣称为受控或不可变资产。
- 未来把 icon 收紧为受控资产引用时，通过新用例、新字段语义和显式迁移完成，不在当前字符串上隐式增加强保证。

## 架构决定（仅本次需要的章节）

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-016`（use-cases/UC-APP-016-decide-application-profile-revision-review.md）：后续方向
- `UC-APP-013`（use-cases/UC-APP-013-create-application-profile-revision.md）：目标与范围、业务边界、输入与身份、网页端重新编辑被拒绝资料、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、尚未决定但不阻塞文档、后续用例、迁移说明、变更记录、实现依赖与交付边界
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-016-decide-application-profile-revision-review.md` | 312 | `32bcd54ca110` |
| `use-cases/UC-APP-013-create-application-profile-revision.md` | 404 | `42ec2452522f` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `cfaa02fcbb8c` |
