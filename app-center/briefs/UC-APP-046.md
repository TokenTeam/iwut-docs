<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-046 --spec tools/brief-specs/UC-APP-046.json -->
# Brief — UC-APP-046：管理脚本独立发布与分发门禁

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-046` 管理脚本独立发布与分发门禁 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-015`–`BR-SCR-018`（4 条） |
| 外部引用 BR | — |
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

### 目标与发布模型

首期只有一个独立 release head，不引入脚本 Test/Grey/Stable 三套渠道。发布 head 表示当前推荐版本，历史精确版本的分发资格单独保存。

命令为 PublishScriptVersion(resourceId, versionId, expectedPublicationRevision)、ClearScriptHead(resourceId, expectedPublicationRevision)、SuspendScriptDistribution 与 RestoreScriptDistribution(resourceId, expectedAvailabilityRevision, reason)。分别要求 [publish/suspend/restore 精确权限](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002)，reason trim 后 1..2048 UTF-8 bytes。

### 验收

- 获批未发布的 A 不可分发；发布 A 后再发布 B，引用 A 的应用仍获得 A。
- ClearHead 不让历史精确引用失效；暂停阻断所有版本，恢复只解除 gate。
- Publish 与 Suspend、两个发布的竞争按真实存储序列提交，不产生暂停后错误发放的新资格；App 发布/运行消费详见 UC047。
- 无 publish 不能发布，无 suspend/restore 不能相互替代；审计重试不制造重复实际变更。

## 业务规则（UC-APP-046 权威正文）

<!-- 权威位置: use-cases/UC-APP-046-manage-script-publication.md#br-scr-015 -->
### BR-SCR-015：批准与发布分离

新资源初始化 head=null、publicationRevision=1、availability=AVAILABLE、availabilityRevision=1。只有具有完整匹配 ScriptReview APPROVED 事实的版本可 Publish；首次成功发布原子新增不可变发布事件、永久已发布资格、head 和 publicationRevision。未获批不能以设置指针绕过审核，获批但未发布不能分发给运行客户端。

<!-- 权威位置: use-cases/UC-APP-046-manage-script-publication.md#br-scr-016 -->
### BR-SCR-016：历史精确版本与回退

曾成功发布的版本在资源 AVAILABLE 时持续可分发。发布 B、回退 head 到曾发布的 A 或 ClearHead 均不撤销其他历史版本资格，不改写应用引用或审核事实。ClearHead 仅清除推荐指针；若需立即停止全部后端内容分发，使用 Suspend。

首期不提供单个历史版本撤销/恢复或版本删除；有问题的历史版本以资源级 Suspend 阻止继续分发，再修复新版本并协调依赖应用更新。该粒度会影响同资源其他版本；后续若引入精确撤销，需先扩展本 UC。

<!-- 权威位置: use-cases/UC-APP-046-manage-script-publication.md#br-scr-017 -->
### BR-SCR-017：正交分发门禁

Suspend 仅将 AVAILABLE 改为 SUSPENDED；Restore 仅解除该 gate，不改变文本、批准、历史资格、head 或应用审核终态。暂停期间仍可维护/审核，但禁止新 Publish，运行内容获取和应用发布/启动须按 [UC047](../use-cases/UC-APP-047-resolve-application-script-content.md) 校验 gate。恢复不自动发布草稿，不重试应用批准，不宣称收回已下载字节或停止离线客户端执行。

<!-- 权威位置: use-cases/UC-APP-046-manage-script-publication.md#br-scr-018 -->
### BR-SCR-018：发布命令并发与审计

各命令核对对应正数 revision，过期即冲突。版本资格、head、gate、revision 和业务审计在命令边界原子生效。相同 revision 下设置现有 head、清空空 head、重复目标门禁为 no-op，不虚增 revision/事件；迟到旧 revision 仍冲突。首次发布不是 no-op。服务时钟及可信操作者记录操作和原因，故障不留半条资格记录。

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

- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `ADR-008`（adr/ADR-008-script-dependency-transactions-and-cascade.md）：背景、替代方案与后果

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-046-manage-script-publication.md` | 40 | `02903bd8680c` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
