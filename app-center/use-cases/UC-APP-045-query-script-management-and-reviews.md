# UC-APP-045：查询脚本管理与审核视图

状态：`ACCEPTED`

## 目标与查询

为平台脚本维护、审核和发布提供列表、版本详情、审核队列/详情、发布历史及级联进度。查询不产生决定，不分发普通客户端运行文本；客户端独立分发与应用关联读取使用 [UC047](UC-APP-047-resolve-application-script-content.md)，应用选取和应用 Reviewer 的受限视图由 [UC048](UC-APP-048-manage-application-script-dependencies.md) 定义。

## 业务规则

<a id="br-scr-013"></a>
### BR-SCR-013：按职责限定查询披露

maintain 可读取资源、全部版本正文及其审核结果；script.review 可读取脚本队列、全部审核快照正文/检查定义及相应资源和版本；publish 可读资源/版本摘要、批准事实和发布历史，不因此读取未获批正文；suspend/restore 可读分发门禁与发布摘要，不因此读取正文。任一上述权限可读资源最小元数据，不能因此取得其他职责编排权限。

完整审核中的原拒绝原因、人员审计及失败详情仅 maintain/script.review 可读；publish 与运维角色只取得状态、关联决定 ID 和操作所需门禁，不返回无关个人资料。利益冲突不禁止读，而是显式返回 canDecide=false 及冲突类别，写命令仍独立验证。

<a id="br-scr-014"></a>
### BR-SCR-014：一致详情与有界列表

详情提供同一次一致读取中的版本状态/revision、原文/digest、绑定政策和唯一决定，PENDING 队列仅包含待审。级联详情返回 taskId、状态、进度观测时间、已处理数量、实际拒绝/既有终态/关闭豁免的分别计数及受控失败分类，不将估计进度当作全局终态证明。完成以 [UC049](UC-APP-049-cascade-script-rejection.md) 的判据为准。

limit 默认20、最大100，按 createdAt + 唯一 ID 稳定倒序、opaque cursor 绑定过滤和调用者读取范围；非法/不匹配 cursor 报错。列表允许并发变动但不得用 offset 漏过同时间记录；决定前必须重读详情，列表不作为强一致批准凭证。正文只在详情中返回，避免列表放大。

所有视图 private, no-store；先鉴权再定位目标。未知 ID 返回 NotFound，关联必要事实损坏返回明确失败，不合成空政策、空正文或已完成级联。

## 验收

- 未获批正文不会因普通登录、App 归属或 publish 权限泄漏。
- Reviewer 获得完整政策文本和精确受审字节，可看到自身冲突但不能绕过决定门禁。
- 终态记录退出 PENDING 队列、历史仍可查询；同时间分页与过滤变更 cursor 有明确行为。
