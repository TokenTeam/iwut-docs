# UC-CONSOLE-007：审核 Application 公开资料

状态：`ACCEPTED`

2026-11-04 按已接受的[提交绑定设计](../../app-center/implements/2026-11-03-submission-bound-review-policy-proposal.md)同步：资料提交时绑定独立完整策略，审核按该绑定执行；统一新接口，不兼容上线前旧数据。详情使用 reviewPolicy 及完整定义，策略退休不要求待审重提。

2026-10-16按用户持续授权自行接受完整用例，按[首阶段实现记录](../implements/2026-10-16-admin-review-queries.md)先实施真实队列/详情与权限恢复。批准/拒绝及其全部验收保留；公开指针与决定surface后来已按[决定接入工作包](../implements/2026-10-16-admin-review-decisions.md)补齐并验证，不再作为当前接入阻塞，也不以局部通过替代完整验收。

## 用户目标、权限与范围

具有精确 `app.profile.review` 权限且无利益冲突的 Reviewer 在 Admin Console 查阅资料待审队列与不可变 snapshot，依据该次提交绑定的正式策略批准或拒绝一次资料审核，并正确处理批准后自动公开的前置冲突。

后端权威为 [UC-APP-031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md) BR-PRF-041–046 与 [UC-APP-016](../../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md) BR-PRF-023–031；Auth 当前能力来自 UC-AUTH-010。前端复用 [UC-CONSOLE-006](UC-CONSOLE-006-review-application-versions.md#前端业务规则) BR-CRV-002–004 的 snapshot/策略绑定、并发/结果未知及私有安全要求，使用本 UC 的权限和输入差异。

不提供资料编辑、恢复 REJECTED 修订、管理员重新发布、历史回滚、审核撤销、权限治理或受控 icon 资产能力。Tester 本人入口继续暂缓。

## 队列与详情流程

1. Admin Console 提供与版本审核分开的“资料审核”入口；`ListPendingApplicationProfileReviews` 使用 `POST /app-center/v1/reviews/application-profiles:search`，默认全部 PENDING，可按 applicationId 筛选，以后端 keyset 顺序翻页。
2. 队列显示 Application、修订 sequence/displayName、attempt、提交时间和 decisionEligibility。冲突项保留并说明 CURRENT_ADMIN、REVISION_CREATOR、REVIEW_SUBMITTER；缺权限不是空队列。
3. `GetApplicationProfileReview` 使用 `GET /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}`。显示不可变 snapshot 的 displayName、description、icon 原始文本、sourceRevision、attempt、提交事实与 decision，以及独立的当前修订 revision、Application 上下文、reviewPolicy 和 eligibility。
4. 终态详情只读；当前修订与 Review snapshot 分区，绝不从 UC039 管理查询替换审核材料。原文纯文本显示，未知或不可信 icon 字符串不自动执行/内嵌；不新增外链探测或资产代理。
5. APPROVE 前还须读取 Reviewer 被授权取得的当前公开资料指针及相应公开内容（如存在），明确本次批准将替换什么。正式来源为同次Reviewer详情的`currentPublishedProfile`，见依赖章节；不能用管理员查询或推测 null 代替。

## 决定流程与前端规则

<a id="br-crv-005"></a>
### BR-CRV-005：资料审核独立权限

只认 `app.profile.review`，`app.version.review`、Developer、Application 管理员及平台管理员不隐式授权。每次请求使用真实在线 Session 链路；权限撤销后清除该功能审核内容，禁用表单，保留 Session；重新获权须重新查询。冲突提示不替代最终决定检查，不能仅凭旧 eligibility 开放提交。

<a id="br-crv-006"></a>
### BR-CRV-006：资料批准的公开指针前置值

APPROVE 使用正式读取的当前 ProfileRevision revision、reviewPolicy.version、用户主动确认的检查集合，以及明确的 expectedCurrentPublishedProfileRevisionId：具体 UUID 或显式 null 表示 NONE。缺少指针来源不是 NONE，不能省略或猜测。公开指针变更后重新展示被替换资料，清空旧批准确认并要求重新评审，禁止自动填新指针重试。

批准成功按后端响应显示当前公开资料已切换；无需、也不提供第二次 Publish 按钮。批准不承诺客户端缓存或已运行页面立即刷新。

<a id="br-crv-007"></a>
### BR-CRV-007：资料拒绝与实际终态

REJECT 提交有效非空纯文本理由、空 confirmedCheckIds，省略 expectedCurrentPublishedProfileRevisionId；使用详情返回的当前修订 revision 和提交绑定策略版本。理由约束由 UC016 拥有，客户端提示不改变原文。拒绝成功显示旧公开资料保持不变、此修订不能原地恢复或再提交；不提供复制/新建写入口。

<a id="br-crv-008"></a>
### BR-CRV-008：资料决定确认与恢复

决定前展示目标 attempt、APPROVE/REJECT、策略与理由；APPROVE 额外明确自动公开及替换目标。`DecideApplicationProfileRevisionReview` 使用 `POST /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}/decision`，严格使用当前 Proto command；int64 revision 保持精确 ProtoJSON 字符串，null 与缺失保持区别。

提交互斥、迟到响应绑定原目标、策略/确认变化和 RESULT_UNCERTAIN 重读遵循 BR-CRV-002–004。stale revision、公开指针冲突、请求与绑定策略不符、已决定和权限撤销均不自动重发；重读失败不能回退管理员查询或伪造新 expected 值。REJECT 不触发批准外部复检，前端不能因图标读取失败自行阻止符合后端规则的拒绝。

## 外部依赖、缺口与方案

2026-11-04：App `a95bd13` / API `2dc002e` 已实现提交绑定、Profile 唯一策略选择及完整定义，App 完整 backend 门禁 24/24 通过。Reviewer 详情仅接受 `reviewPolicy.version/requiredCheckIds/requiredCheckDefinitions`，不再内置 Profile v1 文案或兼容旧字段。任意完整合法的绑定版本按服务端定义展示；已退休政策仍供已绑定记录决定。错误绑定为 `PROFILE_REVIEW_POLICY_MISMATCH`。

当前公开指针仍来自同次详情的 `currentPublishedProfile`，缺失不视为 NONE，公开指针 CAS、单工作位及当前权限检查保留。沿用既有 Gateway 路由与权限，descriptor 和新 reason 透传、Console 新契约实链仍需部署准备。此前发布镜像的审核、公开资料投影、私有隔离和 Scope 场景属于历史已验证基线，不能作为本次新契约部署证据。

无需为策略退休触发重审或新 Profile 版本单独编写前端白名单。正式新政策联合发布须有获批真实内容与环境，不创建同义政策凑验收；事务、组件刷新保持及正式联合链证据分层记录。

## 验收与完成标准

1. 真实 `app.profile.review` grant/revoke、单持版本权限、无权限平台管理员和三类利益冲突均覆盖；版本/资料队列与权限互不替代。
2. snapshot 与当前修订分区，终态展示原绑定 policy；逐项确认本次完整服务端定义，icon 为空仍按绑定规则处理。完整合法的新版本无需前端白名单；定义缺失、损坏或集合不一致时失败关闭。
3. REJECT 不需公开指针，空 checks/理由和原文保留正确；APPROVE 缺指针保持禁用，显式 null 与 UUID 由正式来源读取，不能猜值。
4. 同一 Review 的双 Reviewer 决定经真实链路验证最多一个成功，另一个按稳定冲突 reason 重读，不自动重放。按单工作位规则验证首次批准后顺序创建、提交并批准下一修订，以及当前公开指针与历史投影。公开指针前置冲突单列为协议防御验收：一条合法 PENDING 使用与正式当前指针不相符的 expected 值时真实返回409且无部分写；该负例不称为“不同修订并发”。前端对该 reason 的重读、展示替换目标、清空确认和重新评审由明确标注的组件/状态恢复证据验证，不伪造为当前可达的浏览器业务竞态。revision、错误绑定、响应丢失与权限撤销仍按规定恢复。策略发布单独验证 A 下提交、B 后原记录仍按 A 决定，新提交/拒绝后重提绑定 B，历史不变且无补审期限；需要正式准备能力的项保持待验收。
5. 批准显示自动公开且无第二 Publish；拒绝保持既有公开资料且无恢复入口。真实浏览器/Auth/Gateway/App、no-store、无敏感持久化和可访问性验收齐全后才记 COMPLETE。
