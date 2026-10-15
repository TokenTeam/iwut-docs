# UC-CONSOLE-007：审核 Application 公开资料

状态：`PROPOSED`

## 用户目标、权限与范围

具有精确 `app.profile.review` 权限且无利益冲突的 Reviewer 在 Admin Console 查阅资料待审队列与不可变 snapshot，依据正式当前策略批准或拒绝一次资料审核，并正确处理批准后自动公开的前置冲突。

后端权威为 [UC-APP-031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md) BR-PRF-041–046 与 [UC-APP-016](../../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md) BR-PRF-023–031；Auth 当前能力来自 UC-AUTH-010。前端复用 [UC-CONSOLE-006](UC-CONSOLE-006-review-application-versions.md#前端业务规则) BR-CRV-002–004 的 snapshot/策略绑定、并发/结果未知及私有安全要求，使用本 UC 的权限和输入差异。

不提供资料编辑、恢复 REJECTED 修订、管理员重新发布、历史回滚、审核撤销、权限治理或受控 icon 资产能力。Tester 本人入口继续暂缓。

## 队列与详情流程

1. Admin Console 提供与版本审核分开的“资料审核”入口；`ListPendingApplicationProfileReviews` 使用 `POST /app-center/v1/reviews/application-profiles:search`，默认全部 PENDING，可按 applicationId 筛选，以后端 keyset 顺序翻页。
2. 队列显示 Application、修订 sequence/displayName、attempt、提交时间和 decisionEligibility。冲突项保留并说明 CURRENT_ADMIN、REVISION_CREATOR、REVIEW_SUBMITTER；缺权限不是空队列。
3. `GetApplicationProfileReview` 使用 `GET /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}`。显示不可变 snapshot 的 displayName、description、icon 原始文本、sourceRevision、attempt、提交事实与 decision，以及独立的当前修订 revision、Application 上下文、currentPolicy 和 eligibility。
4. 终态详情只读；当前修订与 Review snapshot 分区，绝不从 UC039 管理查询替换审核材料。原文纯文本显示，未知或不可信 icon 字符串不自动执行/内嵌；不新增外链探测或资产代理。
5. APPROVE 前还须读取 Reviewer 被授权取得的当前公开资料指针及相应公开内容（如存在），明确本次批准将替换什么。该正式来源当前缺失，见依赖章节；不能用管理员查询或推测 null 代替。

## 决定流程与前端规则

<a id="br-crv-005"></a>
### BR-CRV-005：资料审核独立权限

只认 `app.profile.review`，`app.version.review`、Developer、Application 管理员及平台管理员不隐式授权。每次请求使用真实在线 Session 链路；权限撤销后清除该功能审核内容，禁用表单，保留 Session；重新获权须重新查询。冲突提示不替代最终决定检查，不能仅凭旧 eligibility 开放提交。

<a id="br-crv-006"></a>
### BR-CRV-006：资料批准的公开指针前置值

APPROVE 使用正式读取的当前 ProfileRevision revision、currentPolicy.version、用户主动确认的检查集合，以及明确的 expectedCurrentPublishedProfileRevisionId：具体 UUID 或显式 null 表示 NONE。缺少指针来源不是 NONE，不能省略或猜测。公开指针变更后重新展示被替换资料，清空旧批准确认并要求重新评审，禁止自动填新指针重试。

批准成功按后端响应显示当前公开资料已切换；无需、也不提供第二次 Publish 按钮。批准不承诺客户端缓存或已运行页面立即刷新。

<a id="br-crv-007"></a>
### BR-CRV-007：资料拒绝与实际终态

REJECT 提交有效非空纯文本理由、空 confirmedCheckIds，省略 expectedCurrentPublishedProfileRevisionId；使用详情返回的当前修订 revision 和策略版本。理由约束由 UC016 拥有，客户端提示不改变原文。拒绝成功显示旧公开资料保持不变、此修订不能原地恢复或再提交；不提供复制/新建写入口。

<a id="br-crv-008"></a>
### BR-CRV-008：资料决定确认与恢复

决定前展示目标 attempt、APPROVE/REJECT、策略与理由；APPROVE 额外明确自动公开及替换目标。`DecideApplicationProfileRevisionReview` 使用 `POST /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}/decision`，严格使用当前 Proto command；int64 revision 保持精确 ProtoJSON 字符串，null 与缺失保持区别。

提交互斥、迟到响应绑定原目标、策略/确认变化和 RESULT_UNCERTAIN 重读遵循 BR-CRV-002–004。stale revision、公开指针冲突、策略变化、已决定和权限撤销均不自动重发；重读失败不能回退管理员查询或伪造新 expected 值。REJECT 不触发批准外部复检，前端不能因图标读取失败自行阻止符合后端规则的拒绝。

## 外部依赖、缺口与方案

| 所需事实 | 当前已交付来源 | 判断与方案 |
| --- | --- | --- |
| PENDING 队列、snapshot、当前修订 revision、eligibility、currentPolicy.version/requiredCheckIds | UC031 详情/当前 Proto | 可接入；不是缺失策略版本 API |
| 正式检查定义 | UC016 BR-PRF-028 已定义 `app-profile-review-v1` 两项检查及含义；详情只返回 ID | 首版可按这个不可变精确版本制作经 App 所有者核验的只读解释包；icon 为空仍明确确认不适用，不省略该项。其他版本定义未核验时关闭决定；如未来需通用读取，交 App 所有者另行设计，不在本 UC 加 API |
| Reviewer 当前公开指针及被替换公开资料 | UC031 的 Application context/Proto 当前没有指针；UC029/039 只授权当前管理员，不能借用 | **阻塞 APPROVE**。建议 App 所有者评估正式扩展 Reviewer 详情，提供当前公开指针及最小公开对照事实，并按其 UC/BR 审核、实现、更新 API；替代方案为经论证的既有 Reviewer 可读权威查询。不能从公共 Catalog 某项缺失推断 NONE，不能从此前自己的决定缓存推断当前值 |
| 三个 ADMIN API surface、固定生成客户端及真实权限签发 | Gateway/Console/Auth 对应工程包 | 依赖对应 agent 验收；路由存在不代表权限或定义就绪 |

在公开指针依赖解除前，可实现经接受设计的队列/详情及 REJECT 分支；APPROVE 显示“批准前置读取尚未接入”并保持禁用，UC 整体继续未完成。是否接受分阶段交付由本提案审核确定，不借临时 DTO、DB 读取或 BFF 越权解除阻塞。

## 验收与完成标准

1. 真实 `app.profile.review` grant/revoke、单持版本权限、无权限平台管理员和三类利益冲突均覆盖；版本/资料队列与权限互不替代。
2. snapshot 与当前修订、终态详情与当前 policy 分开；两项正式检查逐项确认，icon 为空仍正确处理，未知版本失败关闭。
3. REJECT 不需公开指针，空 checks/理由和原文保留正确；APPROVE 缺指针保持禁用，显式 null 与 UUID 由正式来源读取，不能猜值。
4. 依赖补齐后，两个 Reviewer 分别批准不同修订导致公开指针冲突，须重读与重新确认；同一 Review 双决定、revision/策略变化、响应丢失和权限撤销走规定恢复。
5. 批准显示自动公开且无第二 Publish；拒绝保持既有公开资料且无恢复入口。真实浏览器/Auth/Gateway/App、no-store、无敏感持久化和可访问性验收齐全后才记 COMPLETE。
