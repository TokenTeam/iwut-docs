<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-044 --spec tools/brief-specs/UC-APP-044.json -->
# Brief — UC-APP-044：审核脚本版本

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-044` 审核脚本版本 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-010`–`BR-SCR-012`（3 条） |
| 外部引用 BR | `BR-SCR-007`，`BR-SDP-004`（来自 `UC-APP-043`、`UC-APP-048`） |
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

### 目标与输入

独立脚本 Reviewer 对 PENDING ScriptReview 做一次 APPROVE 或 REJECT。输入为 resourceId、versionId、reviewId、expectedVersionRevision、policyVersion、decision、confirmedCheckIds、reason；身份与决定时间不能自报。读取 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md) 的固定原文、摘要、政策和利益冲突后再操作。

### 验收与失败

- 缺权限/利益冲突禁止；拥有两类审核权也必须分别决定脚本和应用。
- 缺必检项、错误政策、并发双决定失败；绑定政策退休不阻止合法决定。
- 拒绝保存或级联任务保存任一失败都回滚；响应丢失后查询既有决定，不制造第二个任务。
- 脚本拒绝已提交、级联未完成时，应用批准仍被 [BR-SDP-004](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-004) 阻止。

## 业务规则（UC-APP-044 权威正文）

<!-- 权威位置: use-cases/UC-APP-044-decide-script-version-review.md#br-scr-010 -->
### BR-SCR-010：审核资格与利益冲突

要求可信 ACTIVE USER 精确持有 `app.script.review`，且不是该版本的创建人、任何实际内容修改人或提交人。批准与拒绝均执行冲突检查。依据 [BR-SCR-007](../use-cases/UC-APP-043-submit-script-version-review.md#br-scr-007)，脚本作者必然属于这些冲突角色。决定事务核对资源归属、版本贡献者与提交者的一致性，损坏时失败。作者当前 Developer 资格不影响已提交审核的处理。客户端不能覆盖冲突检查。

<!-- 权威位置: use-cases/UC-APP-044-decide-script-version-review.md#br-scr-011 -->
### BR-SCR-011：明确检查与相斥终态

决定必须匹配 Review 固定的 policyVersion、Version revision、完整快照和摘要。批准提交全部 mandatory checkId，重复或未知项均非法，reason 可空且最多 2048 UTF-8 bytes；拒绝提交空 confirmedCheckIds 及 trim 后 1..2048 UTF-8 bytes 的 reason，无须声明必检项通过。此为客户端人工声明，不能代替后端状态/权限验证。

事务内重核 PENDING Review 与 SUBMITTED Version 的关系，将 Review 决定、Version APPROVED/REJECTED、revision 及同一审计一次提交。批准与拒绝只能一项成功，终态不能覆盖或互转。状态、快照、摘要或绑定定义损坏时失败关闭。批准不自动发布，也不自动批准任何应用。

<!-- 权威位置: use-cases/UC-APP-044-decide-script-version-review.md#br-scr-012 -->
### BR-SCR-012：拒绝事实与级联义务同生

脚本拒绝与唯一持久级联任务在同一事务保存；任务固定 scriptVersionId、digest、reviewId、decisionId、原决定时间及决定人。无法保存任务则拒绝命令整体失败，不能留下无级联义务的 REJECTED。

拒绝 ACK 表示脚本终态和义务已落盘，返回 cascadeTaskId、cascadeStatus=PENDING，不表示所有应用已经拒绝；查询可观察 PENDING/RUNNING/COMPLETE 与待处理/失败信息，按 [UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 可靠收敛。即使没有依赖也由 worker 核实后完成。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-043`

<!-- 权威位置: use-cases/UC-APP-043-submit-script-version-review.md#br-scr-007 -->
### BR-SCR-007：单次提交与固定受审对象

每个 ScriptVersion 首期最多一次审核。ScriptReview.snapshot 固定 resourceId、versionId、versionLabel、contentFormat、完整原文、digest、源 revision 及贡献者，并保存提交时的资源名称、用途和元数据 revision。submittedBy/At 来自可信身份和服务时钟。版本创建者、实际贡献者和提交者须与资源所有者一致。Version → SUBMITTED 与 Review → PENDING 同成同败。重复提交或过期 revision 返回冲突，作者可按 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md) 查询当前结果。

### 来自 `UC-APP-048`

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-004 -->
### BR-SDP-004：批准前的全部脚本获批条件

在保留 UC005 所有身份、利益冲突、政策、Scope、管理员与提交者资格等检查的基础上，只有全部精确依赖具有匹配的 ScriptReview APPROVED 终态，才可批准应用。原文/摘要/引用关系缺失或损坏失败关闭，客户端 confirmedCheckIds 不能代替后端核对。

任一 SUBMITTED 则返回 ScriptDependencyPending 并保持原审核；任一 REJECTED 则返回 ScriptDependencyRejected 并等待/触发已存在的可靠级联，不得批准。该 gate 不妨碍现行资格规则先作合法系统拒绝，也不禁止 Reviewer 按原规则人工拒绝。脚本已批准但未发布或暂停不阻止应用人工审核，实际发布/运行由 UC047 校验。

应用批准记录保存实际依据的脚本审核决定 ID、versionId 和 digest。没有脚本的应用继续通过全部原有条件，不新增伪检查项，也不改变 App 已绑定政策的正式检查文本。

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

- `UC-APP-043`（use-cases/UC-APP-043-submit-script-version-review.md）：目标与主流程、结果与验收
- `UC-APP-048`（use-cases/UC-APP-048-manage-application-script-dependencies.md）：目标与既有用例关系、联合验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `ADR-008`（adr/ADR-008-script-dependency-transactions-and-cascade.md）：背景、替代方案与后果
- `platform/contracts/auth-system-principal-v1.md`（docs 根级共享文档）：目的与所有权、gRPC 方法、错误边界

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-044-decide-script-version-review.md` | 35 | `720c59eb37aa` |
| `use-cases/UC-APP-043-submit-script-version-review.md` | 42 | `762062591a0c` |
| `use-cases/UC-APP-048-manage-application-script-dependencies.md` | 62 | `b525385463a4` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
| `platform/contracts/auth-system-principal-v1.md` | 60 | `7d4081b9bf90` |
