<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-043 --spec tools/brief-specs/UC-APP-043.json -->
# Brief — UC-APP-043：提交脚本版本审核

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-043` 提交脚本版本审核 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-007`–`BR-SCR-009`（3 条） |
| 外部引用 BR | `BR-SCR-002`（来自 `UC-APP-041`） |
| ADR | `ADR-006` |

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

### 目标与主流程

符合 [BR-SCR-002](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002) 的 Developer 使用 `SubmitOwnScriptVersionReview`（`POST /v1/users/me/script-resources/{resource_id}/versions/{version_id}/reviews`）提交本人的 DRAFT。输入为 resourceId、versionId、expectedRevision。服务在同一写事务检查退出栅栏、本人归属、父子关系、状态和 revision，取得 ACTIVE 脚本政策，原子保存固定快照和 PENDING ScriptReview，同时把 ScriptVersion 改为 SUBMITTED 并递增 revision。

### 结果与验收

成功返回 reviewId、SUBMITTED、版本新 revision、提交时间和绑定政策；不批准、不发布、不修改引用它的应用。依赖的应用仍依 [UC048](../use-cases/UC-APP-048-manage-application-script-dependencies.md) 可提交。

- 提交与编辑竞争，不得得到摘要/原文混搭的快照。
- Developer 只能提交本人版本。平台治理授权不能代他人送审。非本人目标或跨资源版本统一 NotFound。
- 政策切换的两个提交胜序各绑定一个完整政策，不能取到两个版本的混合检查。
- 已提交文本不能再编辑；政策定义缺失使读取/决定失败关闭，不临时套用新政策。

## 业务规则（UC-APP-043 权威正文）

<!-- 权威位置: use-cases/UC-APP-043-submit-script-version-review.md#br-scr-007 -->
### BR-SCR-007：单次提交与固定受审对象

每个 ScriptVersion 首期最多一次审核。ScriptReview.snapshot 固定 resourceId、versionId、versionLabel、contentFormat、完整原文、digest、源 revision 及贡献者，并保存提交时的资源名称、用途和元数据 revision。submittedBy/At 来自可信身份和服务时钟。版本创建者、实际贡献者和提交者须与资源所有者一致。Version → SUBMITTED 与 Review → PENDING 同成同败。重复提交或过期 revision 返回冲突，作者可按 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md) 查询当前结果。

<!-- 权威位置: use-cases/UC-APP-043-submit-script-version-review.md#br-scr-008 -->
### BR-SCR-008：提交时绑定正式脚本政策

政策由后端固定管理，不复用 App v3 的检查 ID。Review 保存 policyBinding 和完整不可变政策定义；读取/决定使用该提交绑定版本，后续切换 ACTIVE 不能打断既有待审。首期为 `crawler-script-manual-v1`，每项 mandatory=true，正式文本如下：

| checkId | title | description |
| --- | --- | --- |
| `declared-purpose` | 用途符合平台说明 | 人工确认文本实现的采集用途与资源用途一致，不夹带无关行为。 |
| `client-execution` | 客户端可执行性 | 人工确认目标客户端能够按声明格式处理该文本，必要入口、规则与失败处理可用；此确认不是后端运行证明。 |
| `data-and-credentials` | 数据与凭据边界 | 人工确认不存在内置账号凭据、令牌或将用户凭据及采集数据发送到未经说明目标的逻辑。 |
| `network-and-resource` | 网络与资源使用 | 人工检查访问目标、请求频率、终止条件和资源使用，确认没有与用途无关的请求或无界采集。 |

审核详情返回完整 id/title/description/mandatory，前端不凭 ID 猜政策。无 ACTIVE 或绑定政策不可验证时送审失败，不能降级为无检查项。首期不新增运行时编辑政策后台或机器检查执行器。

<!-- 权威位置: use-cases/UC-APP-043-submit-script-version-review.md#br-scr-009 -->
### BR-SCR-009：未来机器检查的事实边界

未来检查证据以固定 versionId、digest 和检查器/政策版本关联，不能改写正文或既有人工决定。本轮不创建虚假的机器通过项、自动执行器或未接受的检查状态机；是否影响最终批准须另行修订政策和 UC。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-041`

<!-- 权威位置: use-cases/UC-APP-041-manage-script-resource.md#br-scr-002 -->
### BR-SCR-002：作者授权与平台职责隔离

创建、改元数据、建版本、改稿和送审均要求可信 ACTIVE USER 的 `developer_status=APPROVED`。对既有资源的写入还要求 `ownerAuthId` 等于调用者 Auth ID。服务在写事务中核对归属及 [BR-APP-008](../use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-008) 的账号退出栅栏。客户端不能自报所有者、角色或权限。本人读取规则见 [BR-SCR-013](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013)。

审核、独立发布、暂停分发和恢复分发分别要求 `app.script.review`、`app.script.publish`、`app.script.suspend`、`app.script.restore`。四项独立授撤，均不授予创作权限。平台管理员、Reviewer、应用所有者及 SYSTEM 不可代用户创作。旧 `app.script.maintain` 退出授权模型，旧平台创作入口退役。

作者资格取自现有 App audience 的 Auth 可信身份投影。资格变化后，Auth 后续签发使用当前状态，已签身份遵守既有期限与时钟容差。退出栅栏同时约束旧 APPROVED 身份。资格失效不改变既有审核或发布事实。

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-041`（use-cases/UC-APP-041-manage-script-resource.md）：目标与范围、参与者与操作、失败与验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-043-submit-script-version-review.md` | 42 | `762062591a0c` |
| `use-cases/UC-APP-041-manage-script-resource.md` | 42 | `260106d12ddb` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
