# UC-APP-046：管理脚本独立发布与分发门禁

状态：`ACCEPTED`

## 目标与发布模型

首期只有一个独立 release head，不引入脚本 Test/Grey/Stable 三套渠道。发布 head 表示当前推荐版本，历史精确版本的分发资格单独保存。

命令为 PublishScriptVersion(resourceId, versionId, expectedPublicationRevision)、ClearScriptHead(resourceId, expectedPublicationRevision)、SuspendScriptDistribution 与 RestoreScriptDistribution(resourceId, expectedAvailabilityRevision, reason)。分别要求 [publish/suspend/restore 精确权限](UC-APP-041-manage-script-resource.md#br-scr-002)，reason trim 后 1..2048 UTF-8 bytes。

## 业务规则

<a id="br-scr-015"></a>
### BR-SCR-015：批准与发布分离

新资源初始化 head=null、publicationRevision=1、availability=AVAILABLE、availabilityRevision=1。只有具有完整匹配 ScriptReview APPROVED 事实的版本可 Publish；首次成功发布原子新增不可变发布事件、永久已发布资格、head 和 publicationRevision。未获批不能以设置指针绕过审核，获批但未发布不能分发给运行客户端。

<a id="br-scr-016"></a>
### BR-SCR-016：历史精确版本与回退

曾成功发布的版本在资源 AVAILABLE 时持续可分发。发布 B、回退 head 到曾发布的 A 或 ClearHead 均不撤销其他历史版本资格，不改写应用引用或审核事实。ClearHead 仅清除推荐指针；若需立即停止全部后端内容分发，使用 Suspend。

首期不提供单个历史版本撤销/恢复或版本删除；有问题的历史版本以资源级 Suspend 阻止继续分发，再修复新版本并协调依赖应用更新。该粒度会影响同资源其他版本；后续若引入精确撤销，需先扩展本 UC。

<a id="br-scr-017"></a>
### BR-SCR-017：正交分发门禁

Suspend 仅将 AVAILABLE 改为 SUSPENDED；Restore 仅解除该 gate，不改变文本、批准、历史资格、head 或应用审核终态。暂停期间仍可维护/审核，但禁止新 Publish，运行内容获取和应用发布/启动须按 [UC047](UC-APP-047-resolve-application-script-content.md) 校验 gate。恢复不自动发布草稿，不重试应用批准，不宣称收回已下载字节或停止离线客户端执行。

<a id="br-scr-018"></a>
### BR-SCR-018：发布命令并发与审计

各命令核对对应正数 revision，过期即冲突。版本资格、head、gate、revision 和业务审计在命令边界原子生效。相同 revision 下设置现有 head、清空空 head、重复目标门禁为 no-op，不虚增 revision/事件；迟到旧 revision 仍冲突。首次发布不是 no-op。服务时钟及可信操作者记录操作和原因，故障不留半条资格记录。

## 验收

- 获批未发布的 A 不可分发；发布 A 后再发布 B，引用 A 的应用仍获得 A。
- ClearHead 不让历史精确引用失效；暂停阻断所有版本，恢复只解除 gate。
- Publish 与 Suspend、两个发布的竞争按真实存储序列提交，不产生暂停后错误发放的新资格；App 发布/运行消费详见 UC047。
- 无 publish 不能发布，无 suspend/restore 不能相互替代；审计重试不制造重复实际变更。
