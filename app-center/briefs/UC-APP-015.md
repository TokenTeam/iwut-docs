<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-015 --spec tools/brief-specs/UC-APP-015.json -->
# Brief — UC-APP-015：提交应用公开资料修订审核

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-015` 提交应用公开资料修订审核 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PRF-015`–`BR-PRF-022`（8 条） |
| 外部引用 BR | `BR-PRF-003`–`BR-PRF-006`（4 条）（来自 `UC-APP-013`） |
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

> developerStatus 为 `APPROVED` 的当前 Application 管理员，提交一份 DRAFT ApplicationProfileRevision；App Center 冻结本次资料快照，创建独立的 PENDING ApplicationProfileReview，并把资料修订迁移为 SUBMITTED。

本用例负责：

- 检查当前管理员、DRAFT 状态和乐观并发 revision。
- 重新验证当前完整资料内容。
- 创建具有独立身份的 ApplicationProfileReview attempt 与不可变 snapshot。
- 原子执行 `DRAFT -> SUBMITTED`、revision 和最近修改审计更新。

本用例不负责：

- 批准、拒绝或分配 Reviewer。
- 改变当前公开资料。后续 Profile Review 批准时才会自动公开。
- 创建下一份资料草稿；根据 [BR-PRF-006](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)，SUBMITTED 期间工作位仍被占用。
- 添加 FilterRule、运行版本字段或发布槽位。
- 使用 AI 审核 DRAFT、作出决定或改变审核状态；未来 AI 审核的输入、结论效力与状态模型需要由独立用例定义，不属于当前流程。
- 定义 HTTP、数据库、缓存或 Go 实现。

### 参与者与输入

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

### 成功结果

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

### 主流程

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

### 失败结果

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

### 领域模型影响

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

### 验收场景

- APPROVED Developer 且为当前 admin 时，可以提交匹配 revision 的 DRAFT。
- 成功后 ProfileRevision 为 SUBMITTED、revision 增加 1，并存在唯一 PENDING Review snapshot。
- snapshot 与提交时规范化后的 displayName、description、icon 完全一致，之后不可修改。
- 旧管理员、非 APPROVED Developer、非 DRAFT 或 stale revision 均不能提交。
- 并发提交同一 sourceRevision 最多产生一个 Review attempt。
- 任一步失败都不留下孤立 Review 或半完成状态迁移。
- 提交不改变当前公开资料，也不修改任何运行版本或发布槽位。
- 首次提交但尚未批准时，普通用户目录仍看不到该资料。

### 实现依赖与交付边界

本次交付为当前后端工作包：Domain、UseCase、MongoDB 原子 Repository、显式 migration、独立 API Proto 及生成物、可信身份 HTTP/原生 gRPC、Wire 和真实 MongoDB E2E。前端、生产 Gateway、资料管理查询和 UC-APP-016 审核决定分别交付，不阻塞当前命令实现。不得调用 Auth Scope Catalog、DNS、图标 URL 或资产服务。

沿用 Application `coordinationRevision` 技术写栅栏，在事务内保护当前管理员资格；资料生命周期、revision 和工作指针同时受最终条件检查保护。数据不变量异常使用 `ApplicationProfileStateInconsistent`，HTTP 500 / gRPC INTERNAL，并输出脱敏 ERROR 告警；不得伪装成客户端冲突或自动修复损坏状态。数据库驱动错误、完整资料文本和身份凭据不进入错误响应或普通日志。

验收必须运行 `make check-full`，覆盖所有 BR 的单元测试、真实副本集 validator/index、回滚、管理员转让竞争和 HTTP/gRPC E2E；冻结代码、API 和设计来源后运行，交付报告与本地 commit，禁止 push。

前置依赖是 UC-APP-013 和 UC-APP-014 已完成且通过各自完整验证；提交命令不等待 UC016、Reviewer 身份签发或审核策略。独立的 ApplicationProfileReview 聚合仍属于 `internal/profile` 能力；不复用运行版本 Review 的 scopes、URL 预检或恢复逻辑。

Repository 使用业务原子方法 SubmitDraft，输入 applicationId、profileRevisionId、expectedAdminId、expectedRevision、profileReviewId、submittedAt，返回提交后的 ProfileRevision 与 ProfileReview。事务内部重新加载内容并验证，使用当前持久化内容形成快照；不信任事务外或客户端传来的 snapshot。UUIDv7 与时钟经端口提供，技术重试不重新分配外部身份或时间。

新增 `application_profile_reviews` migration：profileReviewId 唯一、(profileRevisionId,attempt) 唯一、(profileRevisionId,sourceRevision) 唯一、PENDING profileRevisionId 部分唯一。applicationId/profileRevisionId/profileReviewId 为 UUIDv7，attempt 为正 int32，sourceRevision 为正 int64；snapshot 三字段必需且遵守已有资料规则；submittedBy 为可信 authId，submittedAt 为 UTC datetime，decision 字段必须存在且当前为 null，status 当前只写 PENDING。由服务负责不可变快照，测试不得用被引用的可变指针替代复制。attempt 在事务内取该修订已有最大值加一，检查溢出；正常新修订首次为1，无历史恢复入口。ProfileRevision revision 同样防溢出。

工作指针丢失/指错、DRAFT 已存在 PENDING 或同一 sourceRevision 的 Review 等属于内部不变量异常，按500/INTERNAL失败并回滚。合法重复请求见已 SUBMITTED 时返回 `ApplicationProfileRevisionNotDraft`（409/ABORTED），不作为幂等成功，也不创建第二份 Review。并发 loser 可按最终状态返回 NotDraft 或 revision conflict；只允许一个成功。字段复检失败为 `InvalidApplicationProfileContent`，不创建 Review。当前公开指针必须逐字保持。

### API 实现契约

内部 `POST /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews`；外部只加 `/app-center`。原生 gRPC：`app_center.v1.application_profile_review.ApplicationProfileReview/SubmitApplicationProfileRevisionReview`。复用 UC004 提交审核惯例，HTTP 正文为 `{ "expectedRevision": "3" }`（Proto int64 JSON 形状），gRPC command.expected_revision；本命令不使用 If-Match。正文只接受 expectedRevision，不接受 snapshot、身份、归属、attempt 或审计；query 不可覆盖正文和路径。

成功 HTTP201 返回 `{ "profileRevision": <完整提交后修订>, "review": <完整审核记录> }`，ETag 为提交后 ProfileRevision.revision。Review 包含 profileReviewId、applicationId、profileRevisionId、attempt、sourceRevision、status、snapshot、submittedBy、submittedAt、decision:null；snapshot 的 description/icon 沿用 UC013 的 string/null 表达。decision 在 Proto 使用 google.protobuf.Value 且只输出 null_value 表示当前唯一合法形状，UC016 再定义 object 内容契约；不预建审核决定业务。

错误：身份401/UNAUTHENTICATED，Developer/管理员不足403/PERMISSION_DENIED，归属错误或不存在404/NOT_FOUND，非法输入/内容400/INVALID_ARGUMENT，非DRAFT或stale409/ABORTED，内部不变量或基础设施失败500/INTERNAL。response loss 后查询的读模型契约独立交付，不在本工作包偷偷增加 GET，也不能声称完整管理端流程已可用。

## 业务规则（UC-APP-015 权威正文）

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-015 -->
### BR-PRF-015：提交权限

提交者必须同时满足：

- developerStatus 为 `APPROVED`；
- 在最终原子写入时仍是 Application 当前 adminId。

submittedBy 记录本次实际提交者。管理员转让不会改写 ProfileRevision.createdBy；新管理员可以提交旧管理员创建的 DRAFT。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-016 -->
### BR-PRF-016：提交前状态与乐观并发

只有属于该 Application、reviewStatus=`DRAFT` 且 revision 等于 expectedRevision 的 ProfileRevision 可以提交。

提交成功后，较早读取到的草稿更新不能覆盖 SUBMITTED 状态。SUBMITTED、APPROVED 和 REJECTED 都不能再次直接提交；REJECTED 是终态，继续编辑时由网页端预填后调用 UC-APP-013 创建新修订。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-017 -->
### BR-PRF-017：提交时内容复检

提交时重新应用 [BR-PRF-003](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005)。

本次可提交的完整资料包含 displayName、可空 description 和可空 icon。FilterRule、Application.name 和任何 ApplicationVersion 字段不进入本次资料审核。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-018 -->
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

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-019 -->
### BR-PRF-019：审核 attempt 身份

- profileReviewId 是系统生成的全局唯一 UUIDv7。
- attempt 在单个 profileRevisionId 内从 1 开始严格递增。
- `(profileRevisionId, attempt)` 唯一。
- `(profileRevisionId, sourceRevision)` 唯一，防止同一 ProfileRevision 状态被重复提交。
- 同一 ProfileRevision 同时最多有一个 PENDING Review。

一个 ProfileRevision 不从 REJECTED 恢复。网页端可以预填其内容并通过 UC-APP-013 创建拥有新身份的新修订；新修订的 attempt 从 1 开始，不覆盖旧 Review。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-020 -->
### BR-PRF-020：ProfileRevision 状态与审计

提交只执行以下生命周期变化：

```text
ApplicationProfileRevision: DRAFT -> SUBMITTED
revision: expectedRevision -> expectedRevision + 1
updatedBy: submittedBy
updatedAt: submittedAt
```

profileRevisionId、applicationId、sequence、createdBy、createdAt、displayName、description 和 icon 保持不变。ApplicationProfileReview.sourceRevision 保存迁移前的 expectedRevision。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-021 -->
### BR-PRF-021：原子提交与重复请求

以下事实必须全部成功或全部失败：

- 当前管理员、ProfileRevision 归属、DRAFT 和 expectedRevision 的最终检查；
- ApplicationProfile.workingProfileRevisionId 仍指向目标的检查；
- Review attempt 分配与重复检查；
- PENDING ApplicationProfileReview 创建；
- ProfileRevision 状态、revision 和更新审计变更；
- ApplicationProfile.workingProfileRevisionId 仍指向目标 SUBMITTED Revision。

同一 sourceRevision 的并发提交最多一个成功。提交成功但响应丢失时，客户端通过查询发现 SUBMITTED 和对应 Review；重复命令不会创建第二条记录，也不会增加 revision。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-022 -->
### BR-PRF-022：提交不改变当前公开资料

提交审核不会修改 `currentPublishedProfileRevisionId`。只有未来的 Profile Review 批准行为会在记录批准决定的同时自动把对应 ProfileRevision 设为当前公开资料。

提交也不会修改 ApplicationVersion、ApplicationPublication、Tester Membership、FilterRule 或 Auth 数据。

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

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006 -->
### BR-PRF-006：初始生命周期与单一工作修订

- 新 ProfileRevision 的 reviewStatus 固定为 `DRAFT`；调用者不能指定其他状态。
- 每个 Application 同时最多存在一条 reviewStatus 为 DRAFT 或 SUBMITTED 的工作修订。
- DRAFT 不属于公开目录，不改变已发布资料，也不会让 Application 自动公开。
- DRAFT 迁移为 SUBMITTED 后继续占用该工作位；在 PENDING ProfileReview 得到 APPROVED 或 REJECTED 决定前，不创建下一份 DRAFT。
- APPROVED 或 REJECTED 决定产生后释放工作位；它们不阻止后续创建新 DRAFT。

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
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
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

- `UC-APP-015`（use-cases/UC-APP-015-submit-application-profile-revision-review.md）：后续方向
- `UC-APP-013`（use-cases/UC-APP-013-create-application-profile-revision.md）：目标与范围、业务边界、输入与身份、网页端重新编辑被拒绝资料、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、尚未决定但不阻塞文档、后续用例、迁移说明、变更记录、实现依赖与交付边界
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-015-submit-application-profile-revision-review.md` | 254 | `726a36ab708e` |
| `use-cases/UC-APP-013-create-application-profile-revision.md` | 404 | `42ec2452522f` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
