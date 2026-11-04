# UC-APP-016：审核应用公开资料修订

状态：`ACCEPTED`

## 修订范围与审核状态

2026-11-04 用户已接受本次修订并要求开始更新。提交时固定政策、未上线不做旧模型/数据/接口兼容，均为当前实施依据；旧已交付基线和历史记录保留，本次接受不表示新增实现已完成。实施范围与依赖见[已接受提案](../implements/2026-11-03-submission-bound-review-policy-proposal.md)。

## 目标与边界

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

## 参与者与输入

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

## 成功结果

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

## 主流程

1. 从可信 ReviewerIdentity 取得 authId 和 permissions，校验 Command。
2. 加载 Application、ApplicationProfile、ProfileRevision 和 ProfileReview，确认它们的归属关系。
3. 确认可信 ReviewerIdentity 包含 `app.profile.review`，并且 Reviewer 不是当前 admin、Revision 创建者或 Review 提交者。
4. 确认 Review 为 PENDING 且 decision 为空；ProfileRevision 为 SUBMITTED，revision 匹配 expectedProfileRevisionRevision，当前内容与 snapshot 一致，并且 ApplicationProfile.workingProfileRevisionId 指向目标 Revision。
5. 读取 Review.policyBinding 指定的不可变 ProfileReviewPolicy，确认 expectedPolicyVersion 等于绑定版本，并计算该 snapshot 所需检查项；RETIRED 仍可决定。
6. outcome=APPROVE 时：
   - 确认 confirmedCheckIds 完整覆盖所需检查；
   - 重新验证 snapshot 的 displayName、description 和 icon；
   - 确认当前公开指针等于 expectedCurrentPublishedProfileRevisionId；
   - 构造 APPROVED decision。
7. outcome=REJECT 时：确认拒绝理由有效、confirmedCheckIds 为空，构造 REJECTED decision。
8. 在同一原子边界重新确认步骤 2–7 的状态、权限和并发条件，然后写入 decision、同步 Review/Revision 状态和审计；批准时同时替换当前公开资料指针。
9. 返回决定后的 Review、ProfileRevision，以及当前公开资料 ID。

## 失败结果

- 缺少可信 Reviewer 身份：`ReviewerIdentityRequired`。
- 缺少 `app.profile.review`：`ApplicationProfileReviewPermissionRequired`。
- Reviewer 存在利益冲突：`ApplicationProfileReviewConflictOfInterest`。
- ID、revision、outcome、policy version 或 APPROVE 所需公开指针前置值非法：`InvalidApplicationProfileReviewDecision`。
- Application、Revision、Review 不存在或归属不匹配：`ApplicationProfileReviewNotFound`。
- Review 不再是 PENDING、已有 decision 或 Revision 不再是 SUBMITTED：`ApplicationProfileReviewAlreadyDecided` 或 `ApplicationProfileReviewStateConflict`。
- ProfileRevision revision 不匹配：`ApplicationProfileRevisionConflict`。
- APPROVE 时当前公开指针已改变：`ApplicationProfilePublicationConflict`。
- Revision/Review 内容或 revision 关系不一致：`ApplicationProfileReviewStateInconsistent`。
- expectedPolicyVersion 与目标绑定不符：返回 `ProfileReviewPolicyMismatch`（409/ABORTED）；不因绑定版本已退休触发。
- 必需绑定缺失、引用或正式定义损坏：`ApplicationProfileReviewStateInconsistent` / INTERNAL；存储不可用沿用基础设施错误，均不猜测当前策略。
- 批准检查不完整或拒绝理由非法：`ProfileReviewChecksIncomplete` 或 `InvalidProfileReviewReason`。
- 批准时 snapshot 不再满足资料规则：`InvalidApplicationProfileContent`。
- 持久化失败：内部失败，不产生部分 decision、状态或公开指针变化。

归属不匹配按 NotFound 处理。网络超时后查询既有 Review；decision 不会因普通重试被覆盖。

## 业务规则

<a id="br-prf-023"></a>

### BR-PRF-023：Reviewer 权限与利益冲突

决定者必须具有 Auth 授予的 `app.profile.review` 权限，并且 authId 不等于：

- Application 当前 adminId；
- ApplicationProfileRevision.createdBy；
- ApplicationProfileReview.submittedBy。

Reviewer 权限只从本次请求的可信 ReviewerIdentity 读取；当前 admin 等 App Center 本地事实在最终原子写入时重新确认。`app.version.review` 不隐式授予资料审核权限，通用 `is_admin` 也不构成绕过。

<a id="br-prf-024"></a>

### BR-PRF-024：一次性决定与前置状态

只有 status=`PENDING` 且 decision=null 的 ApplicationProfileReview 可以决定；对应 ProfileRevision 必须为 SUBMITTED，revision 等于 expectedProfileRevisionRevision。

一个 Review 只写入一次 decision。并发决定最多一个成功；已决定 Review 的 outcome、reason、检查项、审核人和时间都不能原地修改。

<a id="br-prf-025"></a>

### BR-PRF-025：Review、Revision 与 snapshot 一致性

作出决定前必须满足：

- Review、ProfileRevision 与 Application 属于同一路径；
- ProfileRevision 当前 displayName/description/icon 等于 Review.snapshot；
- `ProfileRevision.revision = Review.sourceRevision + 1`；
- Review 是该 ProfileRevision 当前 PENDING attempt。

发现内容漂移、悬空引用或 revision 关系异常时中止并告警，不自动修复。

<a id="br-prf-026"></a>

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

<a id="br-prf-027"></a>

### BR-PRF-027：决定理由

- REJECT 必须提供 reason；APPROVE 可以省略。
- 非空 reason 为 1–2000 个 Unicode code point。
- 首尾不允许 Unicode whitespace，不允许 Unicode `Cc` 控制字符，也不接受纯 whitespace。
- reason 是纯文本，不解释 HTML 或 Markdown。

校验后原样保存。Reviewer 不应在 reason 中写入敏感学生资料或无需向开发者公开的安全细节。

<a id="br-prf-028"></a>

### BR-PRF-028：版本化资料审核策略

Reviewer 提交自己实际阅读的 expectedPolicyVersion。App Center 拥有不可变、可按版本读取的 ProfileReviewPolicy：

```text
ProfileReviewPolicy {
  version
  requiredChecks: []ReviewCheckDefinition { id, title, description }
  status: ACTIVE | RETIRED
}
```

APPROVE 时 confirmedCheckIds 使用集合语义，并完整覆盖策略对 snapshot 要求的检查；REJECT 时 confirmedCheckIds 为空。policyBinding 在 UC015 提交时固定；expectedPolicyVersion 必须与它一致，decision.policyVersion 保存该值。历史政策保留；RETIRED 只禁止新提交选择，仍允许已绑定 PENDING 作新决定。

首版策略由 App Center migration 写入：version=`app-profile-review-v1`、status=`ACTIVE`，固定要求以下两项：

- `content-policy-reviewed`：Reviewer 已检查名称、描述符合内容规范。
- `icon-content-reviewed`：Reviewer 已检查图标内容合规；icon 为空时明确确认不适用，仍提交该检查项。

本次 v1 初始完整定义逐字承载上述已接受解释，标题仅用于展示，不新增政策义务：

| ID | 标题 | description 原文 |
| --- | --- | --- |
| `content-policy-reviewed` | 资料内容规范 | Reviewer 已检查名称、描述符合内容规范。 |
| `icon-content-reviewed` | 图标内容合规 | Reviewer 已检查图标内容合规；icon 为空时明确确认不适用，仍提交该检查项。 |

Profile 的完整定义直接保存在 ProfileReviewPolicy 中，首次初始化就完整写入；与 Version 一样按 version 稳定读取，不建立旧数据补充记录。以后新增政策使用新版本并保留新模型产生的完整历史。

策略内容不可原地修改；变更检查项或其含义使用新 version，历史定义保留。同版本已有不同定义时 migration 失败，不覆盖。不提供在线策略管理 API；Reviewer 使用 UC031 的 reviewPolicy 读取该次绑定定义，审核详情字段统一为 reviewPolicy，不再输出 currentPolicy。confirmedCheckIds 不接受重复、未知或缺失项，持久化按 ID 排序；REJECT 必须为空。

Profile 以独立 policyKind=PROFILE 引用 [UC005 正式发布流程](UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)，提交和发布在 PROFILE 政策文档上串行；最终决定只读取目标绑定和不可变定义，不与政策退休争抢 ACTIVE 写栅栏。政策变化不清空既有确认、不重提、不改终态，也不创建补审或整改状态。

所有提交与 Reviewer 详情均要求完整绑定定义；按 [UC005 新模型初始化](UC-APP-005-decide-application-version-review.md#新模型初始化与运行门禁)直接建立 Profile v1，不支持旧 ID-only policy、补定义迁移或旧记录读取。其它新政策正文另审，不为接口调整制造 v2。

<a id="br-prf-029"></a>

### BR-PRF-029：批准时资料复检

APPROVE 针对 Review.snapshot 重新应用 [BR-PRF-003](UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](UC-APP-013-create-application-profile-revision.md#br-prf-005)。

当前 snapshot 包含 displayName、description 和可空 icon。icon 只按不透明字符串规则复检，不调用外部资产服务。REJECT 不执行批准复检，避免校验故障阻止 Reviewer 记录拒绝事实。

<a id="br-prf-030"></a>

### BR-PRF-030：批准后自动公开

Reviewer 从 [UC031 当前公开资料投影](UC-APP-031-query-application-profile-reviews.md#当前公开资料投影) 读取替换对象与明确 NONE。

APPROVE 必须提供 Reviewer 作出决定时观察到的 `expectedCurrentPublishedProfileRevisionId`，其值是某个 ProfileRevision ID 或明确的 `NONE`。它必须与当前指针匹配，再与以下变化处于同一原子边界：

```text
ProfileRevision.reviewStatus = APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = profileRevisionId
```

管理员不需要第二次 Publish 操作。公开指针前置值防止错误或过期客户端预期静默覆盖当前公开资料；不匹配时不写入决定或公开指针。按 [BR-PRF-006](UC-APP-013-create-application-profile-revision.md#br-prf-006)和 BR-PRF-026，同一 Application 当前仅有一个 DRAFT/SUBMITTED 工作修订，批准或拒绝并释放工作位后才能创建下一份；当前不将不同修订同时待审并发批准列为可达用户场景。此说明不放宽指针前置校验、一次性决定或原子写入。未来若开放并行工作修订，应另行接受业务设计并补真实并发验收。旧公开 Revision 保留 APPROVED 状态和审核历史，首版不提供重新选择或回滚资料的命令。

资料自动公开不创建 stable Version。没有兼容 stable 槽位时，Application 仍不进入普通用户候选目录。

<a id="br-prf-031"></a>

### BR-PRF-031：拒绝终止修订且不改变当前公开资料

REJECT 只把目标 Review/Revision 迁移为 REJECTED，并记录理由。`currentPublishedProfileRevisionId` 保持不变；没有既有公开资料时继续为空。

REJECTED 是该 ProfileRevision 的终态；新修订经 UC015 提交时重新绑定当时生效政策，不沿用被拒绝 Review 的绑定。服务端不提供 `REJECTED -> DRAFT`、复制或恢复命令，也不修改 ApplicationVersion 或发送通知。Review snapshot、decision、Revision 内容和审计事实保持不变。

重新编辑是网页端便利行为：网页端读取被拒绝资料并预填创建表单，然后调用 [UC-APP-013](UC-APP-013-create-application-profile-revision.md) 创建一份新 DRAFT。新草稿获得独立的 profileRevisionId、sequence 和创建审计；App Center 不记录它与被拒绝 Revision 的复制关系。

<a id="br-prf-032"></a>

### BR-PRF-032：Revision、审计与原子决定

决定成功后 ProfileRevision.revision 增加 1，updatedBy 记录 Reviewer authId，updatedAt 等于 decidedAt。createdBy、createdAt、submittedBy 和 submittedAt 保持不变。

以下事实全部成功或全部失败：

- 可信 ReviewerIdentity 权限、利益冲突、Review/Revision 状态与 revision 的最终检查；
- policy 与 confirmedCheckIds 校验；
- decision 写入和 Review 状态迁移；
- ProfileRevision 状态、revision 与更新审计变化；
- ApplicationProfile.workingProfileRevisionId 的匹配检查与清空；
- APPROVE 时当前公开资料指针前置值检查与替换。

## 领域模型影响

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

## 初始化与实时门禁

按 [UC005 新模型初始化与运行门禁](UC-APP-005-decide-application-version-review.md#新模型初始化与运行门禁)建立完整绑定及定义，不回填旧记录。本次不增加 Profile 决定的 Auth/Scope/DNS 依赖；现有权限、利益冲突、生命周期、内容校验和公开指针 CAS 保持。SUSPENDED 继续可审核，关闭不可借政策冻结绕过。

## 验收场景

- 具有 `app.profile.review` 且无利益冲突的 Reviewer 可以决定一致的 PENDING Review。
- 按 UC005 新语义矩阵验证 A 提交/B 生效/A 决定、B 新提交、拒绝后新建重提、提交/切换两种胜序、错误绑定、历史不变和实时门禁；2026-11-04 隔离组件/事务及双协议专项、完整 backend 门禁已通过，真实新政策的正式联合发布另行准备。
- APPROVE 原子写入 decision、把 Review/Revision 设为 APPROVED，并替换当前公开资料。
- REJECT 要求有效理由，把 Review/Revision 设为 REJECTED，且旧公开资料保持不变。
- Reviewer 不能审核自己创建、提交或当前管理的资料。
- 两个并发决定最多一个成功，decision 不可覆盖。
- stale ProfileRevision revision、snapshot 漂移或状态不一致均不会产生部分决定。
- APPROVE 的公开指针前置值过期时不会覆盖其他已批准资料。
- 验收分层：同一 Review 的真实双 Reviewer 竞争证明一次性决定；错误 expected pointer 的真实409证明协议防御；组件恢复证明重读/清确认/禁止自动重放；三者不冒充不同修订并发批准。
- 经正式命令验证工作位占用时不能创建第二修订，首次决定释放后可顺序创建、提交和批准下一修订，并核对 Admin→Developer 公开指针与保留历史；不 seed 平行 PENDING。
- 指针协议负例使用正式顺序批准形成历史 P0、当前 P1，再创建/提交唯一工作 R2；仅在 R2 命令故意传 P0，验证409和无部分写，不称为浏览器读到有效前置后发生真实不同修订竞态。
- 一条迟到旧 Review 请求在后续修订可创建时已是终态，应按 AlreadyDecided 恢复，不强行改报 PublicationConflict。不同 Application 的批准不竞争同一公开指针。
- 批准不会创建或修改 Test/Grey/Stable，也不会产生资料回滚入口。

## 后续方向

后续若设计紧急下架，应建立 Application 级禁用用例，明确 admin/SysAdmin 权限、对目录与运行解析的影响以及重新启用规则。系统内申诉渠道当前不建立，开发者直接联系平台。AI 对 DRAFT 的审核属于未来独立能力，当前不增加 AI 结论、状态或自动迁移。


## 实现依赖与交付边界

UC013–015 已完成并通过完整 backend 验收；本工作包交付 App Center Domain、UseCase、原子 Mongo Repository、migration、资源化 HTTP/原生 gRPC、Wire 与真实 Mongo E2E。权限仅来自可信请求，不调用 Auth Catalog、Developer Status、System principal、DNS 或资产服务。生产 Auth 的 `app.profile.review` 授予/签发尚未实现，作为独立外部交付记录，不以测试签名 token 冒充生产权限链路完成。

复用 Application `coordinationRevision` 真写栅栏，最终事务重查 BR-PRF-023–032 的本地事实。策略在同一事务中核对目标 attempt 绑定及按版本读取的不可变定义；退休不再是决定前置，也不对 ACTIVE 作决定写栅栏；不可变策略定义与可变 status/技术协调字段分离，不提供运行时策略 CRUD。时钟经端口取得，事务重试不重新生成决定时间。revision 和技术计数器溢出失败并回滚。

Review、Revision、ApplicationProfile 分别持久化。首次初始化完整 Review 的 APPROVED/REJECTED 与 decision 结构、状态一致性、理由与审计约束，保留既有唯一索引；建立独立 `profile_review_policies` 的 version 唯一索引并写入首版策略。migration/readiness 和迁移账本测试同步更新。已决定对象只能读取，不可再次写决定。

REJECT 的候选重建必须保持原始内容，先验证 BSON 字段存在/类型、metadata、路径、sourceRevision、当前 PENDING attempt、工作指针与逐字 snapshot 相等；不能调用无条件复检内容的提交/工作指针 helper，也不能规范化后再比较。仅 APPROVE 调用资料内容复检。决定后的 REJECTED 响应/历史重建同样保留原文。Revision 与 Review validator 仅在 REJECTED 状态把内容长度/字符规则放宽为完整 string/string-or-null 类型约束，其余结构、审计、decision 约束保持严格；其它状态仍要求完整资料内容规则。不得使用运行时 bypassDocumentValidation。

合法终态 Review 返回 `ApplicationProfileReviewAlreadyDecided`；尚为 PENDING 但目标修订非 SUBMITTED 返回 `ApplicationProfileReviewStateConflict`。非法状态/decision 组合、悬空/错误工作指针、内容漂移、sourceRevision 或 attempt 关系异常返回 `ApplicationProfileReviewStateInconsistent`，HTTP500/gRPC INTERNAL，并输出不含资料正文、reason、凭据或数据库错误的安全 ERROR 告警；不自动修复。stale revision 与公开指针冲突是业务冲突，不冒充内部异常。

完整验收执行 `make check-auth-app`（包含 backend 与现有真实 Auth 回归），覆盖 BR、双协议及实际生成 HTTP 客户端、真实副本集 validators/indexes、回滚、并发决定、管理员转让、退休后仍按绑定决定、公开指针前置冲突、revision 溢出、REJECT 坏内容与后续创建新 DRAFT。跨服务回归不代表尚未实现的 Auth 资料审核权限签发已验收。冻结 service/API/docs/涉及的 Auth 来源后验收，API 先本地提交再提交服务 gitlink；不得 push。

## API 实现契约

2026-11-03 修订已于 2026-11-04 接受并完成 App/API 后端实现与完整门禁：提交绑定、按绑定决定及 reviewPolicy 新字段替代退休打断决定。决定命令、单工作位及已交付指针契约保持；错误绑定使用 PolicyMismatch，绑定/定义损坏使用 INTERNAL。当前实现证据与跨端待办见实施记录。

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

错误映射：身份401/UNAUTHENTICATED；缺权限或利益冲突403/PERMISSION_DENIED；不存在或路径归属不匹配404/NOT_FOUND；非法输入、reason、checks或批准内容400/INVALID_ARGUMENT；已决定、状态/revision/公开指针冲突或政策绑定不符409/ABORTED；内部不变量或基础设施失败500/INTERNAL。错误码稳定且不泄漏存储细节。响应丢失后的管理查询仍单独交付，不在本 UC 添加 GET。

## 变更记录

- 2026-11-04：用户接受提交绑定与无旧模型兼容修订；App `a95bd13` / API `2dc002e` 已实现，完整 backend `check-full` 24/24 PASS。Gateway/Console 新契约消费及真实新政策发布另行验收；见[实施记录](../implements/2026-11-04-submission-bound-review-policy-implementation.md)。

- 2026-11-04：用户接受无旧模型兼容的提交政策绑定方案，开始实施；接受不代表交付完成。

- 2026-11-04：按用户确认的未上线前提，删除旧模型、旧数据和旧接口兼容，改为统一新模型初始化及单一契约交付。

- 2026-11-03：PROPOSED 修订采用提交时固定政策；替代退休打断待审决定，保留独立实时门禁及已交付历史，本次仅设计。

- 2026-10-26：用户接受正式策略发布流程和资料并发可达性澄清；保留单工作位、指针前置与原子公开，补验收分层，不新增历史重新发布能力。
