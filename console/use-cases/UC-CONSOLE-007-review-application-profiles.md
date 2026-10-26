# UC-CONSOLE-007：审核 Application 公开资料

状态：`ACCEPTED`

2026-10-16按用户持续授权自行接受完整用例，按[首阶段实现记录](../implements/2026-10-16-admin-review-queries.md)先实施真实队列/详情与权限恢复。批准/拒绝及其全部验收保留；公开指针与决定surface后来已按[决定接入工作包](../implements/2026-10-16-admin-review-decisions.md)补齐并验证，不再作为当前接入阻塞，也不以局部通过替代完整验收。

## 用户目标、权限与范围

具有精确 `app.profile.review` 权限且无利益冲突的 Reviewer 在 Admin Console 查阅资料待审队列与不可变 snapshot，依据正式当前策略批准或拒绝一次资料审核，并正确处理批准后自动公开的前置冲突。

后端权威为 [UC-APP-031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md) BR-PRF-041–046 与 [UC-APP-016](../../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md) BR-PRF-023–031；Auth 当前能力来自 UC-AUTH-010。前端复用 [UC-CONSOLE-006](UC-CONSOLE-006-review-application-versions.md#前端业务规则) BR-CRV-002–004 的 snapshot/策略绑定、并发/结果未知及私有安全要求，使用本 UC 的权限和输入差异。

不提供资料编辑、恢复 REJECTED 修订、管理员重新发布、历史回滚、审核撤销、权限治理或受控 icon 资产能力。Tester 本人入口继续暂缓。

## 队列与详情流程

1. Admin Console 提供与版本审核分开的“资料审核”入口；`ListPendingApplicationProfileReviews` 使用 `POST /app-center/v1/reviews/application-profiles:search`，默认全部 PENDING，可按 applicationId 筛选，以后端 keyset 顺序翻页。
2. 队列显示 Application、修订 sequence/displayName、attempt、提交时间和 decisionEligibility。冲突项保留并说明 CURRENT_ADMIN、REVISION_CREATOR、REVIEW_SUBMITTER；缺权限不是空队列。
3. `GetApplicationProfileReview` 使用 `GET /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}`。显示不可变 snapshot 的 displayName、description、icon 原始文本、sourceRevision、attempt、提交事实与 decision，以及独立的当前修订 revision、Application 上下文、currentPolicy 和 eligibility。
4. 终态详情只读；当前修订与 Review snapshot 分区，绝不从 UC039 管理查询替换审核材料。原文纯文本显示，未知或不可信 icon 字符串不自动执行/内嵌；不新增外链探测或资产代理。
5. APPROVE 前还须读取 Reviewer 被授权取得的当前公开资料指针及相应公开内容（如存在），明确本次批准将替换什么。正式来源为同次Reviewer详情的`currentPublishedProfile`，见依赖章节；不能用管理员查询或推测 null 代替。

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
| Reviewer 当前公开指针及被替换公开资料 | 固定API27c的UC031同次详情`currentPublishedProfile`，以显式NONE或published分支返回指针与最小公开对照 | 已接入并经真实首次批准/替换验证，不再阻塞APPROVE。UC029/039仍只授权当前管理员，不能借用；缺失/未知分支仍失败关闭，不能从Catalog缺项或此前决定缓存推断NONE/当前值 |
| 三个 ADMIN API surface、固定生成客户端及真实权限签发 | 已发布Gateway及Console固定生成/Auth在线签发 | 已接入并经真实决定链验证，不仅是路由存在检查；范围和未覆盖项见实施记录，不推导其它组合已通过 |

2026-10-23依已发布接入证据更新本节。最初公开指针未交付时的阶段限制已解除，APPROVE/REJECT均已实现；不得继续把旧“批准前置读取尚未接入”当当前待办，也不能用临时DTO、DB读取或BFF越权替代正式来源。固定输入与真实证据见[决定接入](../implements/2026-10-16-admin-review-decisions.md)，缓存头门禁已由[已发布复验](../implements/2026-10-23-published-cache-header-fix-verification.md)关闭。

2026-10-26依用户已接受的[单工作位与指针防御说明](../../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)同步第4项：分别记录同Review竞争、顺序替换、错误expected指针的协议负例及组件恢复，不再把不同修订同时PENDING作为真实业务准备要求；不新增第二工作位或历史重新发布。正式策略发布及[新Profile版本兼容门槛](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md#策略版本兼容门槛)仍待实现或准备，详见[当前有界覆盖](../implements/README.md)。既有BR与实际断言保留，文档同步不代表新增验收已通过，UC整体仍未完成。

## 验收与完成标准

1. 真实 `app.profile.review` grant/revoke、单持版本权限、无权限平台管理员和三类利益冲突均覆盖；版本/资料队列与权限互不替代。
2. snapshot 与当前修订、终态详情与当前 policy 分开；两项正式检查逐项确认，icon 为空仍正确处理，未知版本失败关闭。
3. REJECT 不需公开指针，空 checks/理由和原文保留正确；APPROVE 缺指针保持禁用，显式 null 与 UUID 由正式来源读取，不能猜值。
4. 同一 Review 的双 Reviewer 决定经真实链路验证最多一个成功，另一个按稳定冲突 reason 重读，不自动重放。按单工作位规则验证首次批准后顺序创建、提交并批准下一修订，以及当前公开指针与历史投影。公开指针前置冲突单列为协议防御验收：一条合法 PENDING 使用与正式当前指针不相符的 expected 值时真实返回409且无部分写；该负例不称为“不同修订并发”。前端对该 reason 的重读、展示替换目标、清空确认和重新评审由明确标注的组件/状态恢复证据验证，不伪造为当前可达的浏览器业务竞态。revision、策略变化、响应丢失与权限撤销仍按规定恢复；需要正式准备能力的项保持待验收。
5. 批准显示自动公开且无第二 Publish；拒绝保持既有公开资料且无恢复入口。真实浏览器/Auth/Gateway/App、no-store、无敏感持久化和可访问性验收齐全后才记 COMPLETE。
