# UC-APP-042：创建与编辑脚本版本草稿

状态：`ACCEPTED`

## 目标与输入

符合 [BR-SCR-002](UC-APP-041-manage-script-resource.md#br-scr-002) 的 Developer 为本人资源创建独立版本草稿，或完整替换 DRAFT 内容。上传以保存脚本文本完成。`CreateOwnScriptVersionDraft` 使用 `POST /v1/users/me/script-resources/{resource_id}/versions`。`ReplaceOwnScriptVersionDraft` 使用 `PUT /v1/users/me/script-resources/{resource_id}/versions/{version_id}/draft`。

Create 输入为 resourceId、versionLabel、contentFormat、contentText。Replace 输入为 resourceId、versionId、expectedRevision、contentFormat、contentText。服务生成 versionId、revision=1、DRAFT 及审计。作者可读取本人的拒绝版本并预填新草稿。

## 业务规则

<a id="br-scr-004"></a>
### BR-SCR-004：独立版本与不可复用标签

ScriptVersion 使用独立 UUIDv7，并永久绑定一个 ScriptResource。versionLabel 为 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，在同一资源内大小写敏感且永久唯一，不解析为 SemVer 或据此排序。修复拒绝内容创建新 ID 和新标签；不提供 REJECTED → DRAFT 或提交后的原位修改。

<a id="br-scr-005"></a>
### BR-SCR-005：不透明文本及精确摘要

首期仅受理显式 `contentFormat=json`，非空且不全为空白、UTF-8 编码后不超过 1,048,576 bytes 的合法文本，拒绝 NUL 和非法 UTF-8。不 trim、不格式化、不改写 BOM/换行、不重排 JSON 键。摘要为 `SHA-256(受理原文的 UTF-8 bytes)`，小写十六进制；格式作为独立字段参与审核快照核对。HTTP JSON 转义仅为传输编码，不参与正文摘要。

后端不解析 JSON 结构、执行、推断权限或依据语法自动判为通过；即使 JSON 语法错误，满足文本边界仍可保存，逻辑正确性进入人工检查。`lua` 目前返回 UnsupportedScriptFormat，未来以新格式支持和新版本扩展，不推测格式、不转换旧文本、不建立未上线旧数据兼容分支。

<a id="br-scr-006"></a>
### BR-SCR-006：草稿替换与受审冻结

只有 DRAFT 可编辑。Replace 以正数 expectedRevision 做完整替换，原子更新文本、格式、摘要、revision、审计及本版本内容贡献者集合。相同内容且 revision 匹配时返回原状态，不虚增 revision 或贡献者。提交后的正文、格式、标签和贡献事实冻结，任何权限都不能用草稿命令覆盖。

版本创建人和实际内容修改人属于贡献者；来源版本的文本复制不转移来源版本身份或审核结果。首期不提供草稿删除、撤回送审、附件、秘密变量或脚本内依赖图功能。

## 流程与验收

先核身份与 Developer 资格，再校验输入。在同一写事务内先检查退出栅栏，再核对本人资源、版本关联、状态与 revision。并发创建通过资源内标签唯一约束裁决。成功返回元数据、正文、摘要和当前 revision，响应 `private, no-store`。

- 空白、超限、非法编码失败；含换行/BOM/不同 JSON 键顺序的受理文本逐字节往返并有对应摘要。
- 两个编辑及编辑与提交竞争，最多一个消费指定 revision；失败无部分内容更新。
- 非本人目标与不存在目标统一 NotFound。资格失效或退出栅栏禁止写入。已 SUBMITTED/APPROVED/REJECTED 的版本禁止改稿，历史标签禁止复用。
