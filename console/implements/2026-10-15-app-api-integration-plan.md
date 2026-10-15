# App 管理 API 与 Console 接入计划

状态：`PROPOSED`。这是非权威接入调查与待审工作包；页面实现尚未启动。2026-10-15 用户后续已明确授权“同时起草只读管理和审核页面设计”，对应 UC002–007 已起草但全部保持 PROPOSED。

日期：2026-10-15。

## 调查结论与边界

App 已交付 Application 管理查询、Version 查询、ProfileRevision 查询、Tester 管理查询、本人测试参与查询和指定 episode 退出。Console 具备认证与混合 BFF 的工程基础，但目前只有 [UC-CONSOLE-001](../use-cases/UC-CONSOLE-001-establish-console-session.md) 被接受；[产品范围](../product-scope.md) 仍为 PROPOSED，不能当作管理页面的实现授权。

`iwut-console/AGENTS.md` 的当前工作包明确要求：“不得提前实现 Developer/Application 管理或 Admin 审核业务页面”。[ADR-CONSOLE-002](../adr/ADR-CONSOLE-002-functional-documentation-boundary.md) 又要求页面状态、导航、并发冲突、结果未知、安全和可访问性在前端功能设计中定义。用户后续已授权同时起草只读管理与审核 UC；具体草案接受后才能实现。初次调查未分配编号；在用户后续授权下新增 UC002–007 和对应 registry 索引，均未接受。

可独立推进的工作是 Gateway 路由/API 基线核对、生成客户端准备和只读契约检查。Console 页面缺少已接受设计，不阻塞 App UC003–005 的后端联合验收。

调查输入：

| 输入 | 观察值 | 含义 |
| --- | --- | --- |
| Console committed HEAD | `ad179d9` | 登录页面与 BFF 工程基础；当前另有仓库独立性相关 dirty，未修改或纳入本计划交付 |
| Console 生成 API 输入 | `9f914c56a276155ac3b34a980e77ca158e099867` | 当前 `proto-files.txt` 只生成 authentication、email_login 及 Google HTTP 依赖；没有 App 客户端 |
| App API 当前 checkout | `a5d504c058c62cd91be451074d21608d69789918` | 已包含 UC039/040；还包含 Auth 新契约，不直接替 Console 决定升级全部 Auth 流程 |
| Gateway committed HEAD | `894221f882254cba2e292e26606469d48b9e6b24` | 调查时的路由目录未登记下表这些管理/Tester/审核查询 RPC；相邻 Gateway agent 的后续交付需重新核对 |
| Console 业务实现 | 两个应用目前只有 Session 入口 | 未发现 Application、Tester、审核业务页面；认证 E2E 未完成不能标记业务接入完成 |

最终接入须选择所有者已发布且可获取的统一 API 精确 SHA，重新生成并通过漂移检查；本地 checkout 包含接口不等于 Console CI 能获取该提交。以上是调查快照，不替代最终 source lock。

## 建议的页面、API 与身份矩阵

下表为待审页面建议；普通 API 一律沿用 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 的 Browser → Traefik → 对应 BFF Session ForwardAuth → Gateway → App。BFF 仅适配 Cookie；不增加完整业务请求代理、角色判定、数据库查询或第二套路由目录。路径统一外加 `/app-center`。

| 建议工作包与 surface | 页面/用户目标 | 后端 UC 与 RPC | HTTP 内部路径 | 最终授权 |
| --- | --- | --- | --- | --- |
| C1，DEVELOPER | 我的 Application 列表、管理概览 | UC029：ListMyApplications / GetMyApplication | `POST /v1/applications:search`；`GET /v1/applications/{application_id}` | 当前 Application admin；不要求仍是 APPROVED Developer |
| C2，DEVELOPER | Version 列表、当前内容与最新审核摘要 | UC034：ListApplicationVersions / GetApplicationVersion | `POST /v1/applications/{application_id}/versions:search`；`GET /v1/applications/{application_id}/versions/{version_id}` | 当前 admin；保留生命周期历史可读，写权限另查 |
| C2，DEVELOPER | ProfileRevision 列表、原文与审核历史分页 | UC039：ListApplicationProfileRevisions / GetApplicationProfileRevision | `GET /v1/applications/{application_id}/profile-revisions`；同路径加 `/{profile_revision_id}` | 当前 admin；REJECTED 原文可读，不恢复或重提旧修订 |
| C3，DEVELOPER | Tester 容量、ACTIVE episode 和链接历史 | UC037：GetApplicationTesterManagement / ListApplicationTesterMemberships / ListApplicationTesterJoinLinks | `GET /v1/applications/{application_id}/tester-management`；`POST /v1/applications/{application_id}/tester-memberships:search`；`POST /v1/applications/{application_id}/tester-join-links:search` | 当前 admin；Tester 身份不授予管理权 |
| C4，surface 待审 | 我参与的测试、指定 episode 退出 | UC038：ListMyTestApplications / GetMyTestApplication；UC040：LeaveApplicationAsTester | `POST /v1/test-applications:search`；`POST /v1/test-applications/{application_id}:resolve`；`POST /v1/applications/{application_id}/tester-memberships/{membership_id}:leave` | 本人 USER；不要求 Developer、Reviewer 或 Application admin |
| C5，ADMIN | Version 待审队列、审核详情 | UC030：ListPendingApplicationVersionReviews / GetApplicationVersionReview | `POST /v1/reviews/application-versions:search`；`GET /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}` | 精确 `app.version.review`，不被其他角色替代 |
| C5，ADMIN | Profile 待审队列、审核详情 | UC031：ListPendingApplicationProfileReviews / GetApplicationProfileReview | `POST /v1/reviews/application-profiles:search`；`GET /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}` | 精确 `app.profile.review`，不被其他角色替代 |
| C5，ADMIN | Version APPROVE/REJECT | UC005：DecideApplicationVersionReview | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` | `app.version.review` 与最终利益冲突/策略检查 |
| C5，ADMIN | Profile APPROVE/REJECT | UC016：DecideApplicationProfileRevisionReview | `POST /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}/decision` | `app.profile.review`；批准另有公开指针正式读取依赖 |

依据：[UC029](../../app-center/use-cases/UC-APP-029-query-owned-application-management.md)、[UC034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md)、[UC037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)、[UC038](../../app-center/use-cases/UC-APP-038-query-my-test-applications.md)、[UC039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md)、[UC040](../../app-center/use-cases/UC-APP-040-leave-application-as-tester.md)、[UC030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md)、[UC031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md)。可执行字段、ProtoJSON 和正文映射以固定 API Proto 为准，页面不手写第二套业务 DTO。

C1–C3 仍为只读。Tester 移除/轮换/撤销、Version 编辑/提交、资料创建/提交和权限治理没有纳入新提案，不能因后端命令已存在而隐含启用。Admin 审核决定已纳入 UC006/007 待审设计，但不表示已交付审批流程。App UC003–005 联合验收使用真实链路和 Reviewer，不依赖这些页面。

## 当前待审设计与范围授权

用户已授权同时起草只读管理及 Admin 审核页面；以下已形成具体 UC 草案，仍需逐项或整组接受后实施，不再要求用户重复确认“是否起草”。

| 草案 | 审核内容 | 当前设计取向 |
| --- | --- | --- |
| UC-CONSOLE-002–005 | Application 概览、Version、资料历史、Tester 管理 | 纯只读；不因后端写命令已存在而加入创建/编辑/移除等按钮。Tester 管理首版 ACTIVE 为主，不展示 REMOVED Membership 历史入口 |
| UC-CONSOLE-006 | Admin 版本队列、详情与 APPROVE/REJECT | snapshot 与当前策略分离、逐项主动确认、精确权限、冲突和结果未知恢复；正式检查项定义来源未核验时禁止决定 |
| UC-CONSOLE-007 | Admin 资料队列、详情与 APPROVE/REJECT | 批准自动公开须明确确认替换；Reviewer 当前公开指针的正式读取依赖尚缺，允许分阶段先交队列/详情与拒绝，APPROVE 保持禁用直到正式补齐 |
| 本人 Tester 入口 | 未纳入这次 Console 草案 | 客户端目录继续暂缓；无真实宿主 runtime 不造值，Gateway 后端路由接入可独立进行 |

用户实施前主要审核三个前端取舍：只读管理不夹带写操作；审核确认和结果未知后的显式重读/再确认；资料批准缺前置读取时可否分阶段交付。既有后端权限、Scope/OCC、no-store 和 Cookie 边界无需再次重新设计。

## 分派与交付顺序

| 工作包 | 所有者与范围 | 开工条件 | 可审核交付与完成标准 |
| --- | --- | --- | --- |
| G0 | Gateway agent；统一 API 更新、上述 RPC 的精确路由与 surface 清单 | 已有 App/平台契约；不用等 Console 页面 | 固定 API SHA、路由差异、未知路径默认关闭、HTTP/gRPC/gRPC-Web 一致性；未接受页面只登记后端入口，Console surface 按实际待审设计保守关闭 |
| C0 | Console agent；API 生成输入与 transport/client 准备 | 与 G0 协调可获取的 API commit；不覆盖当前仓库独立性 dirty | 固定 source lock；增加所需 Proto 输入/生成类型与 HTTP client；漂移、strict ProtoJSON、方法/正文/无未知参数契约检查；不增加业务导航或按钮 |
| D1 | Console 设计所有者；只读管理 UC002–005 | 用户已授权起草，当前 PROPOSED | actor、状态、分页、错误/私有安全与验收已形成；等待用户接受才实现 |
| C1 → C2 → C3 | Console agent；按接受 UC 串行实现管理读页面 | D1 接受、G0/C0 可用、UC001 有真实有效 Session 基线 | 每包组件/BFF 边界/真实浏览器联合验收；双 surface、身份隔离、分页和 no-store；不要用 mock 报真实服务通过 |
| D2/C4 | 宿主/客户端所有者，或经用户明确授权的 Console 所有者 | 入口归属和 runtime 来源已接受；客户端暂缓解除 | 只复用 UC038/040，不增离线列表、参与历史、隐式退出所有 episode 或即时 token 撤销承诺 |
| D3/C5 | Console 设计与 Admin agent；审核 UC006/007 已起草 | 用户接受设计；正式检查定义/Reviewer 公开指针缺口解除；真实 Reviewer grant/revoke 基线可用 | 精确权限、两类审核分离、不可变 snapshot、当前策略、冲突/并发和结果未知；后端联合验收作为依赖证据 |

此分派是建议工作顺序，不创建其他 chat、不修改其他 agent 文件，也不替 G0/C0 所有者接受 API 升级。只读页面是否依赖 UC001 所有邮箱流程完成由工作包记录明确；使用预建测试 Session 验证页面时，必须写清没有验证完整登录邮件链路。

## 必须纳入后续 UC 和联合验收的清单

### 身份、读取和数据隔离

- 当前 admin 即使 Developer 被暂停仍能读保留历史；他人、旧管理员、Reviewer 身份不能绕过管理查询的统一 NOT_FOUND。转让后重新请求，不凭缓存恢复旧管理权。
- Admin Version/Profile 队列各自验证精确权限。grant/revoke 后走新请求取得真实 Auth 身份；按钮显隐和 decisionEligibility 不代替后端最终授权。利益冲突项可见但必须说明不能决定。
- 普通 API 经过对应 surface 的 Cookie→Session→真实 Auth USER 签发链；浏览器伪造身份被清理，错误 surface Cookie、跨源写、重复 Cookie、未登记路由失败关闭。
- 单个页面显示来自相应查询的事实；不能把 UC029 摘要、UC034 当前 Version 和旧 UC030 snapshot 混成同一时点，不能把未披露审核事实或用户资料补查后显示。

### 分页、刷新和缓存

- 使用不透明 keyset；切换身份、Application、过滤条件、查询种类或 runtime 时丢弃原 token 并从首批读取。Profile 列表与详情审核历史拥有独立 token 和顺序。不得 offset、解析/制造 cursor 或宣称跨页冻结。
- UC038 可返回空 items 加 nextPageToken；不能把空页误认为结束。只有 token 为空才结束；不返回总数，不一次无限扫描，不能因前端预算跳过待返回项。
- 后端成功、空页和领域错误的 `private, no-store` 穿透 Edge；不进入共享代理、Service Worker、localStorage/IndexedDB 持久化或持久 Query cache。页面内临时 Query state 需按 session/surface/目标隔离，失效、身份变化或失去管理权时清除。
- Profile 超预算按正式错误显示，不截断原文伪装完整；审核历史先后页不能改写 latestReview。REJECTED 原文展示不做会改变内容的规范化；后续预填创建仍由新建命令验证。

### 错误、并发与结果未知

- `SESSION_INVALID` 按 UC001 通过本 BFF 清除本 surface Cookie 并回登录；普通 API 响应不直接 Set-Cookie。403 展示权限不足；统一404不猜测“他人存在”；400非法/过期绑定游标提供从首批刷新；5xx/网络错误保持可用会话，明确暂不可用。
- OCC、审核已终结、当前策略变化与 Scope/目录变化按稳定 reason 和状态显示，不解析 message；不自动改 expectedRevision、忽略冲突或重放写命令。保留用户输入并刷新正式读模型，重新提交前明确当前目标。
- 退出仅作用于原 applicationId/membershipId。left=true/false 后刷新本人参与事实，迟到响应不能删除后来新 episode 的卡片；网络结果未知时保存原目标并提供用户触发的同目标重试。应用不可在线查询不代表能新增离线清单。
- C3 查询无 join secret/hash，不提供“恢复邀请链接”按钮；未来轮换一次性 secret 不进入日志、URL 遥测、Query cache 或持久存储。Tester 自退不声称强制结束运行页面或即时撤销 Auth token。

### 证明与交付记录

- 最少覆盖真实浏览器、两独立 BFF、固定 Gateway/Traefik、真实 Auth 与 App：管理员、普通 Tester、两类 Reviewer、无权限和撤销后权限；数据准备只能建立前置事实，不伪造 USER JWS 替代在线签发。
- 各包运行生成漂移、typecheck、组件/BFF 测试、build 和 Playwright；真实服务未连接时记 SKIP/未验收，MSW 只说明页面分支覆盖。
- 报告写明所有代码/API/文档 SHA、镜像 digest、登录或预建 Session 边界、测试命令与退出状态；锁定输入后再跑最终门禁。
- 所有交互键盘可达，loading/错误/空态有可读语义，焦点和重试状态可验证；无需用户预先定配色、像素布局或组件样式。

## 本次实际改动与未完成项

初次只新增本计划；用户后续授权后新增六份 PROPOSED Console UC，并更新 Console registry 与实现导航。未修改 Console 源码、生成物、Auth/App/Gateway/API 或生产配置；未 push、部署，未宣称 Console 真实 E2E 通过。

业务页面实现等待 UC002–007 审核接受；生成基线和 Gateway surface 属于工程接入缺口。审核另有正式检查定义来源、Reviewer 当前公开指针读取缺口，分别登记在 UC006/007。本人 Tester 入口仍受客户端暂缓与宿主上下文缺失约束。
