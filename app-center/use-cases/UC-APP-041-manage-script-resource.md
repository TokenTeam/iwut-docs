# UC-APP-041：管理本人爬虫脚本资源

状态：`ACCEPTED`

## 目标与范围

具备有效 Developer 资格的用户创建本人 ScriptResource，维护名称与用途。所有脚本均由用户上传。平台开发者也使用自己的用户账号和同一套作者规则。2026-11-11 用户确认此归属和创作模式。

脚本资源独立于 Application，不占 Application 创建配额。应用管理权转让、关闭或引用变化不改变脚本归属。独立版本由 [UC042](UC-APP-042-manage-script-version-draft.md) 管理。

## 参与者与操作

`ScriptAuthoringService` 提供 `CreateOwnScriptResource`（`POST /v1/users/me/script-resources`）和 `ReplaceOwnScriptResourceMetadata`（`PUT /v1/users/me/script-resources/{resource_id}/metadata`）。请求包含名称、用途，替换还需 resourceId 和 expectedRevision。服务从可信身份取得 ownerAuthId，生成 UUIDv7、revision=1、创建与更新审计。替换只改变元数据。相同内容且 revision 匹配时返回原状态，不新增业务审计。

## 业务规则

<a id="br-scr-001"></a>
### BR-SCR-001：脚本身份、本人归属与历史

ScriptResource 使用独立且永久不复用的 ID，必有一个不可变的 `ownerAuthId`。所有者是创建时已验签 USER 的 Auth ID，创建者审计记录实际操作者。系统只建立用户归属，归属不随 Developer 状态变化。版本沿 resourceId 继承归属。资源及其版本、审核和发布历史不提供物理删除、转让或平台接管入口。名称无需全局唯一。元数据更新不修改版本文本、审核快照或应用引用。

<a id="br-scr-002"></a>
### BR-SCR-002：作者授权与平台职责隔离

创建、改元数据、建版本、改稿和送审均要求可信 ACTIVE USER 的 `developer_status=APPROVED`。对既有资源的写入还要求 `ownerAuthId` 等于调用者 Auth ID。服务在写事务中核对归属及 [BR-APP-008](UC-APP-025-coordinate-account-owner-exit.md#br-app-008) 的账号退出栅栏。客户端不能自报所有者、角色或权限。本人读取规则见 [BR-SCR-013](UC-APP-045-query-script-management-and-reviews.md#br-scr-013)。

审核、独立发布、暂停分发和恢复分发分别要求 `app.script.review`、`app.script.publish`、`app.script.suspend`、`app.script.restore`。四项独立授撤，均不授予创作权限。平台管理员、Reviewer、应用所有者及 SYSTEM 不可代用户创作。旧 `app.script.maintain` 退出授权模型，旧平台创作入口退役。

作者资格取自现有 App audience 的 Auth 可信身份投影。资格变化后，Auth 后续签发使用当前状态，已签身份遵守既有期限与时钟容差。退出栅栏同时约束旧 APPROVED 身份。资格失效不改变既有审核或发布事实。

<a id="br-scr-003"></a>
### BR-SCR-003：资源元数据与乐观并发

name 去除首尾空白后为 1..128 UTF-8 bytes，purpose 为 1..2048 UTF-8 bytes；不含 NUL。resourceId、revision、时间与操作人不由正文指定。替换需正数 expectedRevision，过期即冲突，无部分写入。每次实际更新原子保存元数据、递增 revision 和可信身份/服务时钟审计；资源元数据 revision 与发布 revision 相互独立。

## 失败与验收

缺身份为 Unauthenticated。本人写入无有效 Developer 资格时在目标查找前返回 Forbidden。字段非法为 InvalidArgument，非本人或不存在的资源统一 NotFound。通过归属检查后才返回 revision 或状态冲突。退出栅栏阻止写入，必要事实损坏或存储失败时拒绝成功。

- 无脚本权限的 APPROVED Developer 可以创建和修改本人的资源。跨作者或仅持有平台治理权限的调用者不能写入其他人的资源。
- 两个相同 revision 的不同元数据更新最多一项成功；更新不改变已提交版本及摘要。
- 验证 Auth 的真实 Developer 签发与资格变更、跨作者隐藏、账号退出竞争，以及旧维护权限无法通过作者鉴权。
