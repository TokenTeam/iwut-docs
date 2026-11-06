# UC-APP-049：因脚本拒绝自动拒绝关联待审应用

状态：`ACCEPTED`

## 目标与参与者

用户已确认：拒绝某一 ScriptVersion 后，自动拒绝所有引用它的待审 ApplicationVersion。由 App 内部持久 worker 有界完成；不开放普通用户、Gateway 或外部 SYSTEM 的任意批量拒绝接口。脚本 Reviewer 触发原始拒绝，worker 只执行该既存义务。

## 业务规则

<a id="br-sdp-006"></a>
### BR-SDP-006：精确级联集合与决定原因

目标为固定引用该 scriptVersionId/digest 的 PENDING ApplicationReview；不作用于同资源其他脚本版本、未提交草稿、ProfileReview 或已决定 AppReview。每条成功处理原子保存 AppReview REJECTED、相应 Version REJECTED/revision 和审计，保留原 snapshot、政策绑定与提交事实。

系统 reason 使用稳定文案并存结构化 cause=`SCRIPT_VERSION_REJECTED`、scriptResourceId/versionId/digest、scriptReviewId/decisionId 和触发人；不把原脚本拒绝中的私有自由文本直接复制给无权应用管理员。系统拒绝是依赖终态传播，不要求完整 mandatory checks 已通过，不伪造 confirmedCheckIds。

<a id="br-sdp-007"></a>
### BR-SDP-007：可追溯的 SYSTEM 身份

自动决定的 decidedBy/Version.updatedBy 使用现有 [Auth System Principal](../../platform/contracts/auth-system-principal-v1.md) purpose=`APP_CENTER_REVIEW_AUTO_REJECTION` 解析的 SYSTEM Auth ID，不伪造、硬编码或冒充脚本 Reviewer。内部原因模型区分既有资格拒绝和脚本依赖拒绝；不改写人工拒绝原因。

解析失败或响应不可验证时保留任务待重试，不把脚本拒绝撤回，不允许应用批准；后端可以已有成功缓存按契约继续。该 purpose 能否覆盖新增原因由实施前与 Auth 所有者确认；若需扩展由其设计，App 工作包不修改 Auth UC/代码或创建占位 ID。

<a id="br-sdp-008"></a>
### BR-SDP-008：一次终态与可靠重试

多个脚本拒绝、重复任务、进程重启、人工拒绝和现行资格自动拒绝竞争时，同一 AppReview 最多一次终态及业务审计。幂等键关联源 scriptDecisionId 与 appReviewId，最终写入仍对 Review=PENDING 和匹配 Version 状态/revision 做条件核对；幂等记录与终态同事务保存。已被其他合法决定终结则保留赢家及其原因，标记该目标无需处理，不覆盖旧审计。

数据库、SYSTEM 依赖或不变量失败不得将目标计作成功；可重试失败持续重试，损坏目标保持任务未完成并可受控观察/修复。不用达到最大重试次数或 lease 过期作为“全部完成”的证明。

<a id="br-sdp-009"></a>
### BR-SDP-009：有界执行与可验证完成

任务状态 PENDING → RUNNING → COMPLETE；RUNNING 允许 lease 到期重取。分批记录进度，不能用内存事件或无界大事务保证全部成功。COMPLETE 仅在全部已登记目标已终结且重新确认不存在仍待审的精确依赖时提交；完成判据不依赖某页数量为零的偶然观测。

通过 [BR-SDP-003](UC-APP-048-manage-application-script-dependencies.md#br-sdp-003) 的送审拒绝串行关系，REJECTED 后不可能新增合法依赖；故完整重扫可证明收敛。发现遗漏/损坏关系时报警并保持未完成，不凭“任务已发出”宣告成功。异步 ACK/进度披露遵循 [BR-SCR-012](UC-APP-044-decide-script-version-review.md#br-scr-012)。

## 验收

- 多应用、多脚本、一个应用多个拒绝依赖均准确收敛；同资源其他版本不受影响。
- 脚本拒绝落盘后立即崩溃、处理中崩溃、响应丢失、重复投递和 lease 竞争均不丢目标或重复决定。
- 送审和拒绝两个提交胜序均覆盖；拒绝完成后无新的引用该脚本的 PENDING。
- 与人工/资格拒绝竞争保留赢家；已批准历史不被改写；等待 SYSTEM 时任务可见且应用不能批准。
- 拒绝后应用恢复草稿并改用新脚本，旧任务不能拒绝新的 Review attempt。
