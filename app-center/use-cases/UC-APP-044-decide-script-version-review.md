# UC-APP-044：审核脚本版本

状态：`ACCEPTED`

## 目标与输入

独立脚本 Reviewer 对 PENDING ScriptReview 做一次 APPROVE 或 REJECT。输入为 resourceId、versionId、reviewId、expectedVersionRevision、policyVersion、decision、confirmedCheckIds、reason；身份与决定时间不能自报。读取 [UC045](UC-APP-045-query-script-management-and-reviews.md) 的固定原文、摘要、政策和利益冲突后再操作。

## 业务规则

<a id="br-scr-010"></a>
### BR-SCR-010：审核资格与利益冲突

要求可信 ACTIVE USER 精确持有 `app.script.review`，且不是该版本的创建人、任何实际内容修改人或提交人。批准与拒绝均执行冲突检查。依据 [BR-SCR-007](UC-APP-043-submit-script-version-review.md#br-scr-007)，脚本作者必然属于这些冲突角色。决定事务核对资源归属、版本贡献者与提交者的一致性，损坏时失败。作者当前 Developer 资格不影响已提交审核的处理。客户端不能覆盖冲突检查。

<a id="br-scr-011"></a>
### BR-SCR-011：明确检查与相斥终态

决定必须匹配 Review 固定的 policyVersion、Version revision、完整快照和摘要。批准提交全部 mandatory checkId，重复或未知项均非法，reason 可空且最多 2048 UTF-8 bytes；拒绝提交空 confirmedCheckIds 及 trim 后 1..2048 UTF-8 bytes 的 reason，无须声明必检项通过。此为客户端人工声明，不能代替后端状态/权限验证。

事务内重核 PENDING Review 与 SUBMITTED Version 的关系，将 Review 决定、Version APPROVED/REJECTED、revision 及同一审计一次提交。批准与拒绝只能一项成功，终态不能覆盖或互转。状态、快照、摘要或绑定定义损坏时失败关闭。批准不自动发布，也不自动批准任何应用。

<a id="br-scr-012"></a>
### BR-SCR-012：拒绝事实与级联义务同生

脚本拒绝与唯一持久级联任务在同一事务保存；任务固定 scriptVersionId、digest、reviewId、decisionId、原决定时间及决定人。无法保存任务则拒绝命令整体失败，不能留下无级联义务的 REJECTED。

拒绝 ACK 表示脚本终态和义务已落盘，返回 cascadeTaskId、cascadeStatus=PENDING，不表示所有应用已经拒绝；查询可观察 PENDING/RUNNING/COMPLETE 与待处理/失败信息，按 [UC049](UC-APP-049-cascade-script-rejection.md) 可靠收敛。即使没有依赖也由 worker 核实后完成。

## 验收与失败

- 缺权限/利益冲突禁止；拥有两类审核权也必须分别决定脚本和应用。
- 缺必检项、错误政策、并发双决定失败；绑定政策退休不阻止合法决定。
- 拒绝保存或级联任务保存任一失败都回滚；响应丢失后查询既有决定，不制造第二个任务。
- 脚本拒绝已提交、级联未完成时，应用批准仍被 [BR-SDP-004](UC-APP-048-manage-application-script-dependencies.md#br-sdp-004) 阻止。
