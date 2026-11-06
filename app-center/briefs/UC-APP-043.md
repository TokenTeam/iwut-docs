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

平台维护人以 resourceId、versionId、expectedRevision 提交 DRAFT。身份采用 [BR-SCR-002](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002)。读取并校验当前草稿，取得服务端 ACTIVE 脚本政策，在单次原子提交中创建独立 PENDING ScriptReview、固定快照及政策绑定，同时把 ScriptVersion 改为 SUBMITTED 并递增 revision。输入不能选择 policy、reviewId、状态、摘要或提交人。

### 结果与验收

成功返回 reviewId、SUBMITTED、版本新 revision、提交时间和绑定政策；不批准、不发布、不修改引用它的应用。依赖的应用仍依 [UC048](../use-cases/UC-APP-048-manage-application-script-dependencies.md) 可提交。

- 提交与编辑竞争，不得得到摘要/原文混搭的快照。
- 政策切换的两个提交胜序各绑定一个完整政策，不能取到两个版本的混合检查。
- 已提交文本不能再编辑；政策定义缺失使读取/决定失败关闭，不临时套用新政策。

## 业务规则（UC-APP-043 权威正文）

<!-- 权威位置: use-cases/UC-APP-043-submit-script-version-review.md#br-scr-007 -->
### BR-SCR-007：单次提交与固定受审对象

每个 ScriptVersion 首期最多一次审核。ScriptReview.snapshot 固定 resourceId、versionId、versionLabel、contentFormat、完整原文、digest、源 revision 及贡献者，并保存提交时的资源名称、用途和元数据 revision 作为受审上下文；后续资源元数据更新不改此上下文。submittedBy/At 来自可信身份和服务时钟。Version → SUBMITTED 与 Review → PENDING 同成同败，不允许无快照的待审版本。重复提交或过期 revision 返回冲突并可重新查询，不生成第二个审核。

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
### BR-SCR-002：精确权限与职责隔离

在既有 App audience 下新增独立 permission：`app.script.maintain`（资源及草稿维护、送审）、`app.script.review`（脚本审核）、`app.script.publish`（独立发布）、`app.script.suspend` 与 `app.script.restore`（分发门禁）。命令逐项核对可信 ACTIVE USER 的精确权限，不接受请求自报角色或权限。

现有 Developer、Application 管理员、App Reviewer、完整平台管理员及 SYSTEM 均不自动获得这些权限。首期不新增可由用户调用的脚本 SYSTEM 写入口，不要求平台维护人同时拥有 Developer 资格。授予/撤销和 JWS 投影由 Auth 所有者另行设计；App 权限契约已接受；真实签发和授予/撤销尚未接入，不能用自造声明代替。签名、audience、时效和撤销残余窗口沿现有可信身份契约，不新增永久权限缓存。

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
| `use-cases/UC-APP-043-submit-script-version-review.md` | 41 | `9beeb1b56477` |
| `use-cases/UC-APP-041-manage-script-resource.md` | 40 | `5213190b7a01` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
