<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-042 --spec tools/brief-specs/UC-APP-042.json -->
# Brief — UC-APP-042：创建与编辑脚本版本草稿

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-042` 创建与编辑脚本版本草稿 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-004`–`BR-SCR-006`（3 条） |
| 外部引用 BR | — |
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

### 目标与输入

持有 [maintain 权限](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002)的平台维护人，为指定资源创建独立版本草稿，或完整替换 DRAFT 内容。文本保存就是本轮的“上传”，不引入任意文件上传、压缩包、对象存储直传协议或服务端执行。

Create 输入为 resourceId、versionLabel、contentFormat、contentText；Replace 输入另含 versionId、expectedRevision，不允许更改所属资源或 versionLabel。服务生成 versionId、revision=1、DRAFT 及审计。拒绝版本可由维护人读取后预填成新草稿；不复活旧身份。

### 流程与验收

先核身份/权限，再校验输入、读取资源和版本，按状态及 revision 原子写入；并发创建依靠资源内标签唯一性，不能靠先查后写。成功返回元数据、正文、摘要和当前 revision，响应 private, no-store。

- 空白、超限、非法编码失败；含换行/BOM/不同 JSON 键顺序的受理文本逐字节往返并有对应摘要。
- 两个编辑及编辑与提交竞争，最多一个消费指定 revision；失败无部分内容更新。
- 无 maintain 不能写；已 SUBMITTED/APPROVED/REJECTED 不能改；重用任何历史标签失败。

## 业务规则（UC-APP-042 权威正文）

<!-- 权威位置: use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-004 -->
### BR-SCR-004：独立版本与不可复用标签

ScriptVersion 使用独立 UUIDv7，并永久绑定一个 ScriptResource。versionLabel 为 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，在同一资源内大小写敏感且永久唯一，不解析为 SemVer 或据此排序。修复拒绝内容创建新 ID 和新标签；不提供 REJECTED → DRAFT 或提交后的原位修改。

<!-- 权威位置: use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-005 -->
### BR-SCR-005：不透明文本及精确摘要

首期仅受理显式 `contentFormat=json`，非空且不全为空白、UTF-8 编码后不超过 1,048,576 bytes 的合法文本，拒绝 NUL 和非法 UTF-8。不 trim、不格式化、不改写 BOM/换行、不重排 JSON 键。摘要为 `SHA-256(受理原文的 UTF-8 bytes)`，小写十六进制；格式作为独立字段参与审核快照核对。HTTP JSON 转义仅为传输编码，不参与正文摘要。

后端不解析 JSON 结构、执行、推断权限或依据语法自动判为通过；即使 JSON 语法错误，满足文本边界仍可保存，逻辑正确性进入人工检查。`lua` 目前返回 UnsupportedScriptFormat，未来以新格式支持和新版本扩展，不推测格式、不转换旧文本、不建立未上线旧数据兼容分支。

<!-- 权威位置: use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-006 -->
### BR-SCR-006：草稿替换与受审冻结

只有 DRAFT 可编辑。Replace 以正数 expectedRevision 做完整替换，原子更新文本、格式、摘要、revision、审计及本版本内容贡献者集合。相同内容且 revision 匹配时返回原状态，不虚增 revision 或贡献者。提交后的正文、格式、标签和贡献事实冻结，任何权限都不能用草稿命令覆盖。

版本创建人和实际内容修改人属于贡献者；来源版本的文本复制不转移来源版本身份或审核结果。首期不提供草稿删除、撤回送审、附件、秘密变量或脚本内依赖图功能。

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

- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-042-manage-script-version-draft.md` | 38 | `bde6577028ae` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
