# UC-APP-049：因脚本拒绝自动拒绝关联待审应用

状态：`ACCEPTED`

## 目标与参与者

用户已确认：拒绝某一 ScriptVersion 后，自动拒绝所有引用它且所属 Application 仍为 ACTIVE 的待审 ApplicationVersion；已关闭应用按 BR-SDP-006 保存关闭豁免。由 App 内部持久 worker 有界完成；不开放普通用户、Gateway 或外部 SYSTEM 的任意批量拒绝接口。脚本 Reviewer 触发原始拒绝，worker 只执行该既存义务。

## 业务规则

<a id="br-sdp-006"></a>
### BR-SDP-006：精确级联集合与决定原因

实际自动拒绝目标为固定引用该 scriptVersionId/digest、所属 Application=ACTIVE 的 PENDING ApplicationReview；不作用于同资源其他脚本版本、未提交草稿、ProfileReview 或已决定 AppReview。每条成功处理原子保存 AppReview REJECTED、相应 Version REJECTED/revision 和审计，保留原 snapshot、政策绑定与提交事实。

对 CLOSING/CLOSED Application 的精确关联待审记录，worker 在同一 Application coordination fence 下确认关闭事实，保存幂等结果 `APPLICATION_CLOSED`、applicationId、closureId 和 closingStartedAt。该目标计为关闭豁免，保留 Review/Version 的原状态、快照及人员审计，不形成自动拒绝决定。缺失或不匹配的关闭事实属于不变量异常，不能按已关闭跳过。关闭与级联两种提交胜序均由同一 Application fence 串行化；自动拒绝先提交则保留其终态，关闭先提交则保存豁免。

系统 reason 使用稳定文案并存结构化 cause=`SCRIPT_VERSION_REJECTED`、scriptResourceId/versionId/digest、scriptReviewId/decisionId 和触发人；不把原脚本拒绝中的私有自由文本直接复制给无权应用管理员。系统拒绝是依赖终态传播，不要求完整 mandatory checks 已通过，不伪造 confirmedCheckIds。

<a id="br-sdp-007"></a>
### BR-SDP-007：可追溯的 SYSTEM 身份

自动决定的 decidedBy/Version.updatedBy 使用现有 [Auth System Principal](../../platform/contracts/auth-system-principal-v1.md) purpose=`APP_CENTER_REVIEW_AUTO_REJECTION` 解析的 SYSTEM Auth ID，不伪造、硬编码或冒充脚本 Reviewer。内部原因模型区分既有资格拒绝和脚本依赖拒绝；不改写人工拒绝原因。

解析失败或响应不可验证时保留任务待重试，不把脚本拒绝撤回，不允许应用批准；后端可以已有成功缓存按契约继续。Auth 所有者已确认该原因由现有 purpose 覆盖，依据见 [UC-AUTH-003 的目标与范围](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md#目标与范围)。

<a id="br-sdp-008"></a>
### BR-SDP-008：一次终态与可靠重试

多个脚本拒绝、重复任务、进程重启、人工拒绝和现行资格自动拒绝竞争时，同一 AppReview 最多一次终态及业务审计。幂等键关联源 scriptDecisionId 与 appReviewId，最终写入仍对 Review=PENDING 和匹配 Version 状态/revision 做条件核对；幂等记录与终态同事务保存。已被其他合法决定终结则保留赢家及其原因，保存 ALREADY_TERMINAL 目标结果；关闭豁免保存 APPLICATION_CLOSED。目标结果、任务进度与实际决定（如有）同事务提交，不覆盖旧审计。

数据库、SYSTEM 依赖或不变量失败不得将目标计作成功；可重试失败持续重试，损坏目标保持任务未完成并可受控观察/修复。不用达到最大重试次数或 lease 过期作为“全部完成”的证明。

<a id="br-sdp-009"></a>
### BR-SDP-009：有界执行与可验证完成

任务状态 PENDING → RUNNING → COMPLETE；RUNNING 允许 lease 到期重取。分批记录进度，不能用内存事件或无界大事务保证全部成功。COMPLETE 仅在全部已登记目标已决定或具有经验证的 APPLICATION_CLOSED 豁免，并完整复核精确依赖中不存在尚未决定且未获关闭豁免的待审记录时提交；完成判据不依赖某页数量为零的偶然观测。

通过 [BR-SDP-003](UC-APP-048-manage-application-script-dependencies.md#br-sdp-003) 的送审拒绝串行关系，REJECTED 后不可能新增合法依赖；故完整重扫可证明收敛。发现遗漏/损坏关系时报警并保持未完成，不凭“任务已发出”宣告成功。异步 ACK/进度披露遵循 [BR-SCR-012](UC-APP-044-decide-script-version-review.md#br-scr-012)。

## 验收

- 多应用、多脚本、一个应用多个拒绝依赖均准确收敛；同资源其他版本不受影响。
- 脚本拒绝落盘后立即崩溃、处理中崩溃、响应丢失、重复投递和 lease 竞争均不丢目标或重复决定。
- 送审和拒绝两个提交胜序均覆盖；拒绝完成后无新的引用该脚本的合法 PENDING 登记。
- 关闭和级联两个提交胜序均覆盖，关闭先提交则保存关联真实关闭事实的 APPLICATION_CLOSED 豁免，级联先提交则保留唯一拒绝决定。完成查询区分实际拒绝、既有终态和关闭豁免，关闭历史中的 PENDING 不阻止合法完成。
- 与人工/资格拒绝竞争保留赢家；已批准历史不被改写；等待 SYSTEM 时任务可见且应用不能批准。
- 拒绝后应用恢复草稿并改用新脚本，旧任务不能拒绝新的 Review attempt。
