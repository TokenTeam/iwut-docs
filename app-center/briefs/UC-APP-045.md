<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-045 --spec tools/brief-specs/UC-APP-045.json -->
# Brief — UC-APP-045：查询脚本管理与审核视图

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-045` 查询脚本管理与审核视图 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-013`、`BR-SCR-014` |
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

### 目标与查询

作者读取本人的脚本、版本和审核结果。平台 Reviewer、发布人员和分发运维人员使用各自的管理视图。客户端独立分发与应用关联读取见 [UC047](../use-cases/UC-APP-047-resolve-application-script-content.md)，应用选取与 App Reviewer 的关联视图见 [UC048](../use-cases/UC-APP-048-manage-application-script-dependencies.md)。

| `ScriptAuthoringService` 本人查询 | App 内部 HTTP |
| --- | --- |
| `ListOwnScriptResources` | `GET /v1/users/me/script-resources` |
| `GetOwnScriptResource` | `GET /v1/users/me/script-resources/{resource_id}` |
| `ListOwnScriptVersions` | `GET /v1/users/me/script-resources/{resource_id}/versions` |
| `GetOwnScriptVersion` | `GET /v1/users/me/script-resources/{resource_id}/versions/{version_id}` |
| `GetOwnScriptReviewResult` | `GET /v1/users/me/script-resources/{resource_id}/versions/{version_id}/reviews/{review_id}` |

### 验收

- 作者可在资格失效后读取本人草稿和原拒绝原因。其他账号猜测 ID、替换父 ID 或重放游标均不能取得本人视图。
- 审核、发布和分发运维入口隐藏未送审草稿，角色组合也不得扩大到他人的草稿。
- Reviewer 获得完整政策文本和精确受审字节，可看到自身冲突但不能绕过决定门禁。
- 终态记录退出 PENDING 队列、历史仍可查询；同时间分页与过滤变更 cursor 有明确行为。

## 业务规则（UC-APP-045 权威正文）

<!-- 权威位置: use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013 -->
### BR-SCR-013：按职责限定查询披露

本人视图要求有效可信 USER 且 `ownerAuthId` 为调用者。Developer 资格失效后，仍可登录的作者可以读取本人历史、草稿和审核结果。本人入口从可信身份确定范围，平台权限不会扩大该范围。未送审的 DRAFT 仅向本人披露，治理视图不列出 DRAFT 或仅有 DRAFT 的资源。

本人资源列表及详情返回 resourceId、名称、用途、revision、时间和最近创建版本的最小摘要。无版本时摘要为空，最近版本按 createdAt 和 versionId 判定。本人版本列表返回 resourceId、versionId、标签、状态、format、digest、revision、时间和已有 reviewId，详情另返回原文。作者审核结果返回 resourceId、versionId、reviewId、审核状态、提交时间、提交时的名称/用途、资源 revision、源版本 revision、format、digest 和 policyVersion。终态另返回决定 ID、结果、决定时间和已保存理由。该投影省略审核人员身份、平台内部审计和跨应用级联信息。

`app.script.review` 可读取脚本队列、受审原文和检查定义、相关资源与已送审版本、决定与级联详情。利益冲突仍可读，详情显示 `canDecide=false` 及冲突类别，决定入口独立校验。`app.script.publish` 可读已送审资源与版本摘要、批准事实和发布历史。`app.script.suspend` 和 `app.script.restore` 可读分发门禁和发布摘要。发布和运维按职责只披露相应摘要与状态。治理查询无权读取作者的私有草稿，也不授予本人写操作。

<!-- 权威位置: use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-014 -->
### BR-SCR-014：一致详情与有界列表

详情在同一次一致读取中校验资源归属、resourceId/versionId/reviewId 关联、状态、原文/digest、绑定政策和唯一决定，并按职责投影。PENDING 队列仅包含待审。Reviewer 的级联详情返回 taskId、状态、进度观测时间、已处理数量、实际拒绝/既有终态/关闭豁免的分别计数及受控失败分类。完成以 [UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 的判据为准。

limit 默认 20、最大 100，按 createdAt 和唯一 ID 稳定倒序。本人的版本列表可按状态过滤。先按所有者或平台职责过滤，再做有界分页。opaque cursor 绑定调用者、查询范围、父资源、过滤与排序。非法或不匹配 cursor 报错。正文只在详情返回，决定前重读详情。

所有视图为 `private, no-store`。先鉴权再定位目标。本人查询的未知、非本人或路径关联不匹配统一 NotFound。必要事实损坏时明确失败。

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
| `use-cases/UC-APP-045-query-script-management-and-reviews.md` | 42 | `deb5f31b4fbd` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
