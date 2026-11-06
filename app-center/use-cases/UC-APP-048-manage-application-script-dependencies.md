# UC-APP-048：管理应用版本的脚本审核依赖

状态：`ACCEPTED`

## 目标与既有用例关系

这是一份对现有创建、编辑、送审、决定和查询链路的增量设计，不另造平行 App 工作流。允许引用待审脚本并要求依赖先审核。本用例已接受；进入各受影响的串行工作包时同步既有 UC 及其生成 brief。

| 既有用例 | 对应工作包的修订 |
| --- | --- |
| UC002/003 | 创建/替换草稿显式提交 scriptReferences；脚本引用是受审内容，受现有 OCC 约束 |
| UC004 | 提交固定引用/摘要并原子登记反向依赖，允许 SUBMITTED 脚本 |
| UC005 | 批准加全部脚本获批前置，人工拒绝保留原规则 |
| UC006/035 | 恢复草稿保留引用供修改；放弃草稿不改脚本或历史依赖 |
| UC029/030/034 | 管理/审核详情展示精确引用、快照和实时阻塞状态；不等于授权决定脚本 |
| UC007/012/019/020/021/023/024/038 | 发布/在线消费按 [UC047](UC-APP-047-resolve-application-script-content.md) 扩展 |

## 业务规则

<a id="br-sdp-001"></a>
### BR-SDP-001：显式有界的精确引用

scriptReferences 为 0..16 项 `{scriptResourceId, scriptVersionId}`，每个资源最多一个版本，重复 ID、同资源多版本、未知/跨资源版本均报错，不能静默去重。新模型中空列表显式表示不使用脚本；不以字段缺失触发旧客户端兼容。服务保存确定排序的引用，不接受客户端自报 digest 或审核状态。只有 [UC042](UC-APP-042-manage-script-version-draft.md) 的文本内容保持原样，引用列表排序不改写脚本字节。

创建/编辑草稿可选 SUBMITTED 或 APPROVED 版本；不选 DRAFT/REJECTED。后来被拒绝的既有引用可留在应用 DRAFT 展示需修正，但再次编辑提交的完整引用列表须重新满足条件。脚本资源暂停/未发布不阻止准备或送审，不代表允许应用发布/运行。

<a id="br-sdp-002"></a>
### BR-SDP-002：候选选择与关联正文权限

具有现行 Developer 资格的当前 Application 管理员，可在该应用上下文查询 SUBMITTED/APPROVED 脚本候选的资源名称、用途、版本标签/ID、format、digest 和审核状态；不能因此取得未获批原文、审核员个人资料或拒绝原因。保留的失效草稿引用显示终态/需修正，不把它伪装成新可选项。

有权读取某次 ApplicationReview 的 App Reviewer，可读取该固定引用的脚本受审原文、摘要、完整脚本政策及关联决定状态，用于了解应用依赖；只覆盖所引用版本，不开放全部脚本队列。其能否决定脚本另按 [BR-SCR-010](UC-APP-044-decide-script-version-review.md#br-scr-010) 验证。普通 App 管理员的版本历史不增加未获批正文披露。候选列表分页复用 [BR-SCR-014](UC-APP-045-query-script-management-and-reviews.md#br-scr-014) 的有界模式。

<a id="br-sdp-003"></a>
### BR-SDP-003：送审冻结与依赖登记

ApplicationReview.snapshot 固定规范化引用、每项脚本 format/digest 和脚本审核 ID。应用提交只允许每项当前为 SUBMITTED 或 APPROVED 且受审事实匹配，不要求脚本已发布。在同一原子边界完成现行全部提交检查、Version → SUBMITTED、AppReview PENDING 和每个精确版本的反向依赖登记，任一失败全部回滚。

提交与脚本 REJECTED 迁移必须有可验证的串行关系：应用提交先完成则属于级联义务；脚本拒绝先完成则不允许新的应用待审登记。不能只读一次状态或事后异步登记依赖。工程实现见 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)。

<a id="br-sdp-004"></a>
### BR-SDP-004：批准前的全部脚本获批条件

在保留 UC005 所有身份、利益冲突、政策、Scope、管理员与提交者资格等检查的基础上，只有全部精确依赖具有匹配的 ScriptReview APPROVED 终态，才可批准应用。原文/摘要/引用关系缺失或损坏失败关闭，客户端 confirmedCheckIds 不能代替后端核对。

任一 SUBMITTED 则返回 ScriptDependencyPending 并保持原审核；任一 REJECTED 则返回 ScriptDependencyRejected 并等待/触发已存在的可靠级联，不得批准。该 gate 不妨碍现行资格规则先作合法系统拒绝，也不禁止 Reviewer 按原规则人工拒绝。脚本已批准但未发布或暂停不阻止应用人工审核，实际发布/运行由 UC047 校验。

应用批准记录保存实际依据的脚本审核决定 ID、versionId 和 digest。没有脚本的应用继续通过全部原有条件，不新增伪检查项，也不改变 App 已绑定政策的正式检查文本。

<a id="br-sdp-005"></a>
### BR-SDP-005：终态与历史引用不被重写

ScriptVersion APPROVED/REJECTED 相斥且不可改写；脚本发布 head 移动不改变 App snapshot。App 拒绝恢复 DRAFT 后可以修改引用，但旧 Review 及其反向关系作为历史保留，活跃级联不再作用于其终态。新送审创建新 attempt 和新依赖，不继承旧批准或旧拒绝结果；已拒绝脚本不能通过恢复草稿重新进入待审链路。

## 联合验收

- 待审脚本可被填入应用、两者可同时待审；批准应用先失败，脚本获批后原 AppReview 可继续合法人工批准。
- 脚本拒绝与应用送审的两个胜序均无遗漏；多脚本任一待审/拒绝均不能批准应用。
- 编辑引用与送审 OCC 正确；恢复后换引用不改旧快照；空列表与16项边界明确。
- 直接 API 调用也执行依赖检查；App Reviewer 可以读相关正文但无脚本权限不能决定，管理员不能借候选接口读待审正文。
