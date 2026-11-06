# UC-APP-041：管理平台爬虫脚本资源

状态：`ACCEPTED`

## 目标与范围

平台维护人创建独立 ScriptResource，维护名称与用途。用户于 2026-11-06 接受本用例并要求串行执行。工作顺序和进度见[脚本用例评审清单](../design-notes/2026-11-05-crawler-script-use-case-review.md)。

资源不属于某个 Application 或其管理员，不占 Application 创建配额。账号转让、应用关闭和应用删除均不删除脚本或改变其归属。独立版本由 [UC042](UC-APP-042-manage-script-version-draft.md) 管理。

## 参与者与操作

可信 ACTIVE USER 执行 CreateScriptResource 或 ReplaceScriptResourceMetadata。请求只含名称、用途；替换另含 resourceId、expectedRevision。服务生成 UUIDv7、revision=1、创建与更新审计。替换只改变元数据，revision 加一；相同内容在 revision 匹配时返回原状态，不新增业务审计。

## 业务规则

<a id="br-scr-001"></a>
### BR-SCR-001：平台脚本身份与历史

ScriptResource 使用服务生成的独立且永久不复用 ID。资源、版本、审核和发布历史均不提供物理删除入口。名称不充当身份，不要求全局唯一。资源元数据变化不修改版本文本、审核快照或应用引用。

<a id="br-scr-002"></a>
### BR-SCR-002：精确权限与职责隔离

在既有 App audience 下新增独立 permission：`app.script.maintain`（资源及草稿维护、送审）、`app.script.review`（脚本审核）、`app.script.publish`（独立发布）、`app.script.suspend` 与 `app.script.restore`（分发门禁）。命令逐项核对可信 ACTIVE USER 的精确权限，不接受请求自报角色或权限。

现有 Developer、Application 管理员、App Reviewer、完整平台管理员及 SYSTEM 均不自动获得这些权限。首期不新增可由用户调用的脚本 SYSTEM 写入口，不要求平台维护人同时拥有 Developer 资格。授予/撤销和 JWS 投影由 Auth 所有者另行设计；App 权限契约已接受；真实签发和授予/撤销尚未接入，不能用自造声明代替。签名、audience、时效和撤销残余窗口沿现有可信身份契约，不新增永久权限缓存。

<a id="br-scr-003"></a>
### BR-SCR-003：资源元数据与乐观并发

name 去除首尾空白后为 1..128 UTF-8 bytes，purpose 为 1..2048 UTF-8 bytes；不含 NUL。resourceId、revision、时间与操作人不由正文指定。替换需正数 expectedRevision，过期即冲突，无部分写入。每次实际更新原子保存元数据、递增 revision 和可信身份/服务时钟审计；资源元数据 revision 与发布 revision 相互独立。

## 失败与验收

缺身份为 Unauthenticated；无 maintain 为 Forbidden，且先于资源查找；字段非法为 InvalidArgument，目标不存在为 NotFound，revision 过期为 Conflict；损坏或存储失败不得返回成功。

- 同名资源可有不同 ID，应用管理员不能凭归属关系维护平台脚本。
- 两个相同 revision 的不同元数据更新最多一项成功；更新不改变已提交版本及摘要。
- 无权请求不泄漏资源是否存在；真实 Auth 权限签发、授予和撤销通过联合验收后才视为接入。
