<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-049 --spec tools/brief-specs/UC-APP-049.json -->
# Brief — UC-APP-049：因脚本拒绝自动拒绝关联待审应用

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-049` 因脚本拒绝自动拒绝关联待审应用 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SDP-006`–`BR-SDP-009`（4 条） |
| 外部引用 BR | `BR-SCR-012`，`BR-SDP-003`（来自 `UC-APP-044`、`UC-APP-048`） |
| ADR | `ADR-006`、`ADR-008` |
| 平台共享 | `platform/contracts/auth-system-principal-v1.md` |

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

### 目标与参与者

用户已确认：拒绝某一 ScriptVersion 后，自动拒绝所有引用它且所属 Application 仍为 ACTIVE 的待审 ApplicationVersion；已关闭应用按 BR-SDP-006 保存关闭豁免。由 App 内部持久 worker 有界完成；不开放普通用户、Gateway 或外部 SYSTEM 的任意批量拒绝接口。脚本 Reviewer 触发原始拒绝，worker 只执行该既存义务。

### 验收

- 多应用、多脚本、一个应用多个拒绝依赖均准确收敛；同资源其他版本不受影响。
- 脚本拒绝落盘后立即崩溃、处理中崩溃、响应丢失、重复投递和 lease 竞争均不丢目标或重复决定。
- 送审和拒绝两个提交胜序均覆盖；拒绝完成后无新的引用该脚本的合法 PENDING 登记。
- 关闭和级联两个提交胜序均覆盖，关闭先提交则保存关联真实关闭事实的 APPLICATION_CLOSED 豁免，级联先提交则保留唯一拒绝决定。完成查询区分实际拒绝、既有终态和关闭豁免，关闭历史中的 PENDING 不阻止合法完成。
- 与人工/资格拒绝竞争保留赢家；已批准历史不被改写；等待 SYSTEM 时任务可见且应用不能批准。
- 拒绝后应用恢复草稿并改用新脚本，旧任务不能拒绝新的 Review attempt。

## 业务规则（UC-APP-049 权威正文）

<!-- 权威位置: use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-006 -->
### BR-SDP-006：精确级联集合与决定原因

实际自动拒绝目标为固定引用该 scriptVersionId/digest、所属 Application=ACTIVE 的 PENDING ApplicationReview；不作用于同资源其他脚本版本、未提交草稿、ProfileReview 或已决定 AppReview。每条成功处理原子保存 AppReview REJECTED、相应 Version REJECTED/revision 和审计，保留原 snapshot、政策绑定与提交事实。

对 CLOSING/CLOSED Application 的精确关联待审记录，worker 在同一 Application coordination fence 下确认关闭事实，保存幂等结果 `APPLICATION_CLOSED`、applicationId、closureId 和 closingStartedAt。该目标计为关闭豁免，保留 Review/Version 的原状态、快照及人员审计，不形成自动拒绝决定。缺失或不匹配的关闭事实属于不变量异常，不能按已关闭跳过。关闭与级联两种提交胜序均由同一 Application fence 串行化；自动拒绝先提交则保留其终态，关闭先提交则保存豁免。

系统 reason 使用稳定文案并存结构化 cause=`SCRIPT_VERSION_REJECTED`、scriptResourceId/versionId/digest、scriptReviewId/decisionId 和触发人；不把原脚本拒绝中的私有自由文本直接复制给无权应用管理员。系统拒绝是依赖终态传播，不要求完整 mandatory checks 已通过，不伪造 confirmedCheckIds。

<!-- 权威位置: use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-007 -->
### BR-SDP-007：可追溯的 SYSTEM 身份

自动决定的 decidedBy/Version.updatedBy 使用现有 [Auth System Principal](../../platform/contracts/auth-system-principal-v1.md) purpose=`APP_CENTER_REVIEW_AUTO_REJECTION` 解析的 SYSTEM Auth ID，不伪造、硬编码或冒充脚本 Reviewer。内部原因模型区分既有资格拒绝和脚本依赖拒绝；不改写人工拒绝原因。

解析失败或响应不可验证时保留任务待重试，不把脚本拒绝撤回，不允许应用批准；后端可以已有成功缓存按契约继续。Auth 所有者已确认该原因由现有 purpose 覆盖，依据见 [UC-AUTH-003 的目标与范围](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md#目标与范围)。

<!-- 权威位置: use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-008 -->
### BR-SDP-008：一次终态与可靠重试

多个脚本拒绝、重复任务、进程重启、人工拒绝和现行资格自动拒绝竞争时，同一 AppReview 最多一次终态及业务审计。幂等键关联源 scriptDecisionId 与 appReviewId，最终写入仍对 Review=PENDING 和匹配 Version 状态/revision 做条件核对；幂等记录与终态同事务保存。已被其他合法决定终结则保留赢家及其原因，保存 ALREADY_TERMINAL 目标结果；关闭豁免保存 APPLICATION_CLOSED。目标结果、任务进度与实际决定（如有）同事务提交，不覆盖旧审计。

数据库、SYSTEM 依赖或不变量失败不得将目标计作成功；可重试失败持续重试，损坏目标保持任务未完成并可受控观察/修复。不用达到最大重试次数或 lease 过期作为“全部完成”的证明。

<!-- 权威位置: use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-009 -->
### BR-SDP-009：有界执行与可验证完成

任务状态 PENDING → RUNNING → COMPLETE；RUNNING 允许 lease 到期重取。分批记录进度，不能用内存事件或无界大事务保证全部成功。COMPLETE 仅在全部已登记目标已决定或具有经验证的 APPLICATION_CLOSED 豁免，并完整复核精确依赖中不存在尚未决定且未获关闭豁免的待审记录时提交；完成判据不依赖某页数量为零的偶然观测。

通过 [BR-SDP-003](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-003) 的送审拒绝串行关系，REJECTED 后不可能新增合法依赖；故完整重扫可证明收敛。发现遗漏/损坏关系时报警并保持未完成，不凭“任务已发出”宣告成功。异步 ACK/进度披露遵循 [BR-SCR-012](../use-cases/UC-APP-044-decide-script-version-review.md#br-scr-012)。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-044`

<!-- 权威位置: use-cases/UC-APP-044-decide-script-version-review.md#br-scr-012 -->
### BR-SCR-012：拒绝事实与级联义务同生

脚本拒绝与唯一持久级联任务在同一事务保存；任务固定 scriptVersionId、digest、reviewId、decisionId、原决定时间及决定人。无法保存任务则拒绝命令整体失败，不能留下无级联义务的 REJECTED。

拒绝 ACK 表示脚本终态和义务已落盘，返回 cascadeTaskId、cascadeStatus=PENDING，不表示所有应用已经拒绝；查询可观察 PENDING/RUNNING/COMPLETE 与待处理/失败信息，按 [UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 可靠收敛。即使没有依赖也由 worker 核实后完成。

### 来自 `UC-APP-048`

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-003 -->
### BR-SDP-003：送审冻结与依赖登记

ApplicationReview.snapshot 固定规范化引用、每项脚本 format/digest 和脚本审核 ID。应用提交只允许每项当前为 SUBMITTED 或 APPROVED 且受审事实匹配，不要求脚本已发布。在同一原子边界完成现行全部提交检查、Version → SUBMITTED、AppReview PENDING 和每个精确版本的反向依赖登记，任一失败全部回滚。

提交与脚本 REJECTED 迁移必须有可验证的串行关系：应用提交先完成则属于级联义务；脚本拒绝先完成则不允许新的应用待审登记。不能只读一次状态或事后异步登记依赖。工程实现见 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)。

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

#### 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

### ADR-008：脚本依赖同库事务与拒绝级联（`ACCEPTED`）

#### 决定

沿用 [ADR004](../adr/ADR-004-mongodb-transactions-and-schema-management.md) 的 MongoDB 副本集事务、显式 schema migration 和有界重试；不新增 Resource Hub、数据库、服务 audience 或跨服务事务协议。

1. 在 ScriptVersion 权威文档维护 adapter-only dependencyFence。App 送审对所有依赖按确定 ID 顺序做真实条件递增，条件为精确身份/摘要及允许状态，再在同事务创建 AppReview、迁移 Version、写入每个反向依赖。脚本批准/拒绝写同一权威文档，产生真实写冲突并重试；只读、no-op `$set` 或仅插独立依赖行不能充当栅栏。
2. 拒绝决定与唯一持久 cascade task 同事务写入。任务内有源决定 ID、状态、lease、分页进度和失败观测；没有内存通知依赖。worker 以稳定键集分批扫描不可变反向依赖，逐目标条件事务终结，App 原有 writer 共享既有栅栏/锁序，不建立第二个 App 决定通道。
3. 反向依赖唯一键为 `(appReviewId, scriptVersionId)`，查询索引以 scriptVersionId 为首列；任务源 scriptDecisionId 唯一。历史关系保留，当前 Review 状态决定是否需处理。分批后重新验证无 PENDING 目标才能 COMPLETE；已拒绝状态和送审真实写栅栏保证不会有后来的合法登记。
4. App 最终批准在同一决定事务校验固定脚本批准事实。脚本已批准为不可变终态，故无后续拒绝翻转；仍核对一致的身份、摘要和决定关系。分发暂停使用独立 availability 文档/栅栏，不复用不可变审核结果。
5. Script Publish 与 Suspend 通过同一资源 gate 的真实条件写串行化。App 发布在原 Publication 事务中按确定资源顺序消费该 gate 栅栏，核对精确版本的已发布事实；在线解析/内容读取采用一致快照，响应可线性化在暂停前或后。不能把跨请求缓存当作实时 gate。

具体 collection/schema、索引名、批大小、lease 和重试参数在对应 UC 的实施工作包中落定。栅栏溢出、关联缺失、摘要不符必须失败关闭。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-system-principal-v1.md`：Auth System Principal v1 跨服务契约

#### 调用与缓存语义

- 调用使用 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，同时要求 `auth.system-principal.resolve` permission 与 caller 的 purpose allowlist。
- 现有 `SYSTEM_PRINCIPAL_PURPOSE_APP_CENTER_REVIEW_AUTO_REJECTION=1` 映射到 `app-center.review-auto-rejection`。其用途覆盖范围由 [UC-AUTH-003 的目标与范围](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md#目标与范围) 定义，包含脚本拒绝引发的 ApplicationReview 自动拒绝。消费方在本地记录具体 cause 与来源。
- Auth 启动时幂等 provision 已知 purpose；同一 purpose 在同一环境中映射到唯一、稳定、非空 authId。
- App Center 不以该 ID 作为启动依赖。首次需要自动审核决定时查询；成功结果可缓存到进程结束。
- 查询失败或返回不匹配 purpose/空 ID 时不得缓存，当前决定 fail closed；后续请求可重试。

#### 契约测试要求

Provider/consumer 必须验证 full method、字段号、purpose 枚举、稳定 ID、身份与 purpose allowlist、失败不缓存，以及 App 自动拒绝最终写入 Auth 返回的 SYSTEM authId。

脚本级联消费方还须验证最终决定记录保留 `cause=SCRIPT_VERSION_REJECTED` 及 App 用例要求的源决定关联，使用相同 purpose 解析的 authId；解析失败且无成功缓存时保留任务重试，恢复后仍使用该稳定身份完成决定。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-044`（use-cases/UC-APP-044-decide-script-version-review.md）：目标与输入、验收与失败
- `UC-APP-048`（use-cases/UC-APP-048-manage-application-script-dependencies.md）：目标与既有用例关系、联合验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `ADR-008`（adr/ADR-008-script-dependency-transactions-and-cascade.md）：背景、替代方案与后果
- `platform/contracts/auth-system-principal-v1.md`（docs 根级共享文档）：目的与所有权、gRPC 方法、错误边界

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-049-cascade-script-rejection.md` | 48 | `6d31ee0e3b68` |
| `use-cases/UC-APP-044-decide-script-version-review.md` | 35 | `720c59eb37aa` |
| `use-cases/UC-APP-048-manage-application-script-dependencies.md` | 62 | `b525385463a4` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
| `platform/contracts/auth-system-principal-v1.md` | 60 | `7d4081b9bf90` |
