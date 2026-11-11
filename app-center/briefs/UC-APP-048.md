<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-048 --spec tools/brief-specs/UC-APP-048.json -->
# Brief — UC-APP-048：管理应用版本的脚本审核依赖

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-048` 管理应用版本的脚本审核依赖 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SDP-001`–`BR-SDP-005`（5 条） |
| 外部引用 BR | `BR-SCR-010`、`BR-SCR-014`（来自 `UC-APP-044`、`UC-APP-045`） |
| ADR | `ADR-006`、`ADR-008` |

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

### 目标与既有用例关系

这是一份对现有创建、编辑、送审、决定和查询链路的增量设计，不另造平行 App 工作流。允许引用待审脚本并要求依赖先审核。本用例已接受；进入各受影响的串行工作包时同步既有 UC 及其生成 brief。

| 既有用例 | 对应工作包的修订 |
| --- | --- |
| UC002/003 | 创建/替换草稿显式提交 scriptReferences；脚本引用是受审内容，受现有 OCC 约束 |
| UC004 | 提交固定引用/摘要并原子登记反向依赖，允许 SUBMITTED 脚本 |
| UC005 | 批准加全部脚本获批前置，人工拒绝保留原规则 |
| UC006/035 | 恢复草稿保留引用供修改；放弃草稿不改脚本或历史依赖 |
| UC029/030/034 | 管理/审核详情展示精确引用、快照和实时阻塞状态；不等于授权决定脚本 |
| UC007/012/019/020/021/023/024/038 | 发布/在线消费按 [UC047](../use-cases/UC-APP-047-resolve-application-script-content.md) 扩展 |

### 联合验收

- 待审脚本可被填入应用、两者可同时待审；批准应用先失败，脚本获批后原 AppReview 可继续合法人工批准。
- 脚本拒绝与应用送审的两个胜序均无遗漏；多脚本任一待审/拒绝均不能批准应用。
- 编辑引用与送审 OCC 正确；恢复后换引用不改旧快照；空列表与16项边界明确。
- 直接 API 调用也执行依赖检查；App Reviewer 可以读相关正文但无脚本权限不能决定，管理员不能借候选接口读待审正文。

## 业务规则（UC-APP-048 权威正文）

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-001 -->
### BR-SDP-001：显式有界的精确引用

scriptReferences 为 0..16 项 `{scriptResourceId, scriptVersionId}`，每个资源最多一个版本，重复 ID、同资源多版本、未知/跨资源版本均报错，不能静默去重。新模型中空列表显式表示不使用脚本；不以字段缺失触发旧客户端兼容。服务保存确定排序的引用，不接受客户端自报 digest 或审核状态。只有 [UC042](../use-cases/UC-APP-042-manage-script-version-draft.md) 的文本内容保持原样，引用列表排序不改写脚本字节。

创建/编辑草稿可选 SUBMITTED 或 APPROVED 版本；不选 DRAFT/REJECTED。后来被拒绝的既有引用可留在应用 DRAFT 展示需修正，但再次编辑提交的完整引用列表须重新满足条件。脚本资源暂停/未发布不阻止准备或送审，不代表允许应用发布/运行。

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-002 -->
### BR-SDP-002：候选选择与关联正文权限

具有现行 Developer 资格的当前 Application 管理员，可在该应用上下文查询 SUBMITTED/APPROVED 脚本候选的资源名称、用途、版本标签/ID、format、digest 和审核状态；不能因此取得未获批原文、审核员个人资料或拒绝原因。保留的失效草稿引用显示终态/需修正，不把它伪装成新可选项。

有权读取某次 ApplicationReview 的 App Reviewer，可读取该固定引用的脚本受审原文、摘要、完整脚本政策及关联决定状态，用于了解应用依赖；只覆盖所引用版本，不开放全部脚本队列。其能否决定脚本另按 [BR-SCR-010](../use-cases/UC-APP-044-decide-script-version-review.md#br-scr-010) 验证。普通 App 管理员的版本历史不增加未获批正文披露。候选列表分页复用 [BR-SCR-014](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-014) 的有界模式。

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-003 -->
### BR-SDP-003：送审冻结与依赖登记

ApplicationReview.snapshot 固定规范化引用、每项脚本 format/digest 和脚本审核 ID。应用提交只允许每项当前为 SUBMITTED 或 APPROVED 且受审事实匹配，不要求脚本已发布。在同一原子边界完成现行全部提交检查、Version → SUBMITTED、AppReview PENDING 和每个精确版本的反向依赖登记，任一失败全部回滚。

提交与脚本 REJECTED 迁移必须有可验证的串行关系：应用提交先完成则属于级联义务；脚本拒绝先完成则不允许新的应用待审登记。不能只读一次状态或事后异步登记依赖。工程实现见 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)。

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-004 -->
### BR-SDP-004：批准前的全部脚本获批条件

在保留 UC005 所有身份、利益冲突、政策、Scope、管理员与提交者资格等检查的基础上，只有全部精确依赖具有匹配的 ScriptReview APPROVED 终态，才可批准应用。原文/摘要/引用关系缺失或损坏失败关闭，客户端 confirmedCheckIds 不能代替后端核对。

任一 SUBMITTED 则返回 ScriptDependencyPending 并保持原审核；任一 REJECTED 则返回 ScriptDependencyRejected 并等待/触发已存在的可靠级联，不得批准。该 gate 不妨碍现行资格规则先作合法系统拒绝，也不禁止 Reviewer 按原规则人工拒绝。脚本已批准但未发布或暂停不阻止应用人工审核，实际发布/运行由 UC047 校验。

应用批准记录保存实际依据的脚本审核决定 ID、versionId 和 digest。没有脚本的应用继续通过全部原有条件，不新增伪检查项，也不改变 App 已绑定政策的正式检查文本。

<!-- 权威位置: use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-005 -->
### BR-SDP-005：终态与历史引用不被重写

ScriptVersion APPROVED/REJECTED 相斥且不可改写；脚本发布 head 移动不改变 App snapshot。App 拒绝恢复 DRAFT 后可以修改引用，但旧 Review 及其反向关系作为历史保留，活跃级联不再作用于其终态。新送审创建新 attempt 和新依赖，不继承旧批准或旧拒绝结果；已拒绝脚本不能通过恢复草稿重新进入待审链路。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-044`

<!-- 权威位置: use-cases/UC-APP-044-decide-script-version-review.md#br-scr-010 -->
### BR-SCR-010：审核资格与利益冲突

要求可信 ACTIVE USER 精确持有 `app.script.review`，且不是该版本的创建人、任何实际内容修改人或提交人；这些冲突对批准和拒绝均适用。平台 maintain/publish 权限及 App Reviewer 权限不能替代脚本审核权。客户端不能覆盖冲突检查。

### 来自 `UC-APP-045`

<!-- 权威位置: use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-014 -->
### BR-SCR-014：一致详情与有界列表

详情提供同一次一致读取中的版本状态/revision、原文/digest、绑定政策和唯一决定，PENDING 队列仅包含待审。级联详情返回 taskId、状态、进度观测时间、已处理数量、实际拒绝/既有终态/关闭豁免的分别计数及受控失败分类，不将估计进度当作全局终态证明。完成以 [UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 的判据为准。

limit 默认20、最大100，按 createdAt + 唯一 ID 稳定倒序、opaque cursor 绑定过滤和调用者读取范围；非法/不匹配 cursor 报错。列表允许并发变动但不得用 offset 漏过同时间记录；决定前必须重读详情，列表不作为强一致批准凭证。正文只在详情中返回，避免列表放大。

所有视图 private, no-store；先鉴权再定位目标。未知 ID 返回 NotFound，关联必要事实损坏返回明确失败，不合成空政策、空正文或已完成级联。

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-044`（use-cases/UC-APP-044-decide-script-version-review.md）：目标与输入、验收与失败
- `UC-APP-045`（use-cases/UC-APP-045-query-script-management-and-reviews.md）：目标与查询、验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `ADR-008`（adr/ADR-008-script-dependency-transactions-and-cascade.md）：背景、替代方案与后果

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-048-manage-application-script-dependencies.md` | 60 | `0a5bf525c397` |
| `use-cases/UC-APP-044-decide-script-version-review.md` | 35 | `5a95a707c6ad` |
| `use-cases/UC-APP-045-query-script-management-and-reviews.md` | 31 | `82cf1e37e4d6` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
