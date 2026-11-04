# UC-CONSOLE-006：审核 Application Version

状态：`ACCEPTED`

2026-11-04 按用户已接受的[提交绑定设计](../../app-center/implements/2026-11-03-submission-bound-review-policy-proposal.md)修订：每次提交绑定不可变审核策略，后续策略发布不影响已提交记录；全体消费者统一新契约，不做上线前旧数据或旧接口兼容。本段及下文修订规则替代旧“决定采用最新 ACTIVE / 策略退休触发重审”的要求。

2026-10-16按用户持续授权自行接受完整用例，按[首阶段实现记录](../implements/2026-10-16-admin-review-queries.md)先实施真实队列/详情与权限恢复。决定及其全部验收仍属于本UC，依赖未齐不得标记完整交付。

## 用户目标、权限与边界

具有精确 `app.version.review` 权限且无利益冲突的 Reviewer，在 Admin Console 查看真实待审队列及不可变详情，按该次提交绑定的正式策略确认检查后批准或拒绝一个 attempt，并在权限或并发变化时安全恢复。

后端权威为 [UC-APP-030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md) BR-REV-029–034、[UC-APP-005](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md) BR-REV-010–020；真实身份/当前能力投影引用 [UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)。前端不重定义授权、状态迁移、策略、Scope 或 URL 校验。

不包含权限授予/撤销 UI、审核分配/锁单、SLA、通知、申诉、批准撤销、版本编辑、发布槽位或自动上线。测试可由受控 Auth 管理路径准备 grant/revoke，不因此创建 Console 治理页面。

## 队列与详情

1. Admin Console 提供独立“版本审核”入口；不能把登录成功、平台管理员或另一项审核权限解释为已获权。首次请求由真实后端检查，无权限进入稳定拒绝态而非伪造空队列。
2. `ListPendingApplicationVersionReviews`：`POST /app-center/v1/reviews/application-versions:search`。默认全部待审，可按已知 applicationId 精确筛选，使用后端 pageSize/keyset 顺序。显示允许披露的应用/版本、attempt、提交时间及 decisionEligibility；冲突项保留并显示原因。
3. 点击记录或深链接，用 `GetApplicationVersionReview`：`GET /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}`。路径三 ID 绑定同一 Review，不补查管理员管理页。
4. 审核主体只能来自 `review.snapshot`，显示版本标签、launchUrl、兼容范围、capabilities、required/optional scopes 与 OAuth 回调。另行标注提交时 ScopeCatalog/preflight 版本、sourceVersionRevision、attempt、提交事实、当前 Application/Version 上下文、reviewPolicy 与 eligibility 的 asOf。
5. 终态详情可读并显示实际 decision、理由、时间与批准验证事实，隐藏决定表单；Version 恢复后原 Review 仍按原终态显示，不把当前 Version 状态覆盖旧决定。

## 决定流程

- 只有当前详情为 PENDING、eligibility 允许且策略检查定义可解释时，才提供 APPROVE/REJECT。未读详情不能从队列直接批准；不预勾选检查项。
- APPROVE 显示提交时绑定的策略版本和每一必需检查的正式定义，由 Reviewer 逐项主动确认，reason 可选。REJECT 要求符合后端规则的纯文本理由，发送空 confirmedCheckIds；切换结果清空此前确认，reason 可在本次页面内保留但不持久化。
- 提交前显示目标 attempt、决定方向、策略版本及理由供确认。对 launchUrl/回调/资料链接不自动嵌入执行；若 Reviewer 主动打开外部页面，使用隔离的新上下文，不附带 Console Cookie、Session 或受保护标头，不把“打开成功”当检查完成。
- `DecideApplicationVersionReview`：`POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision`。正文只使用现有 command 字段：outcome、读取的 expectedPolicyVersion、主动确认的 confirmedCheckIds 和可选 reason。不添加不存在的 expectedVersionRevision、客户端 reviewerId 或决定时间。
- 提交期间禁用重复操作，不阻止用户离开；迟到响应只更新原目标。成功以响应中的实际 outcome 为准；APPROVE 请求也可能按既有后端资格检查得到系统 REJECTED，必须如实显示，不能乐观显示批准。Version APPROVED 明确不等于已发布。

## 前端业务规则

<a id="br-crv-001"></a>
### BR-CRV-001：精确权限、利益冲突与在线重查

前端入口可帮助导航，不授予权限。每个队列、详情、决定请求都走 Admin Session→Gateway→真实 Auth→App 链路；不持有或重放旧 USER JWS。仅 `app.version.review` 授权版本审核；CURRENT_ADMIN、VERSION_CREATOR、REVIEW_SUBMITTER 提示必须显示，最终仍由后端决定。收到权限撤销/不足后清除该功能的私有审核内容并禁用提交，保留 Admin Session；重新获得权限后从正式查询重新进入，不从缓存恢复决定资格。

<a id="br-crv-002"></a>
### BR-CRV-002：snapshot、提交绑定策略与确认绑定

当前可变 Version、提交时 snapshot、提交检查版本和本次提交绑定的策略分别标记。确认集合绑定本次 Review、reviewPolicy 的完整定义及决定前置事实。刷新返回相同绑定时保留确认；后续发布新政策不触发切换、清确认或强制重提。完整定义或决定前置事实发生变化时清空确认；缺定义、顺序/集合不一致或非法响应失败关闭。版本、ID 和文案全部来自本次详情，不维护前端版本白名单或按 ID 推测政策含义；已退休的绑定策略仍可决定。

<a id="br-crv-003"></a>
### BR-CRV-003：并发变化与结果未知恢复

请求策略与绑定不符、已决定、状态冲突、Scope 失效、preflight 或其他依赖错误按稳定 reason 表达；不自动选择新策略、不补确认、不替换 outcome、不重放决定。单纯策略发布或退休不是该待审记录的冲突。已决定/冲突后重读同一详情，呈现实际终态或当前 PENDING，再由用户明确重新评审。

写请求超时、断网或无法确认响应时进入 RESULT_UNCERTAIN，保存本次页面内的原目标，不宣布成功/失败。先重新读取同一 Review：终态只报告已观察到的结果，不能断言由自己完成；仍 PENDING 也不能证明原请求未在途，不自动重发或改发相反决定。明确提示一次性决定由后端串行化，用户重读并重新确认后可发起新的明确提交，继续处理 already-decided/冲突。恢复读取失败或权限撤销时保持“无法确认”，提供退出/稍后刷新；不改用数据库、管理员查询或旧缓存推断。

<a id="br-crv-004"></a>
### BR-CRV-004：审核敏感状态与可访问性

队列分页遵循 BR-CMG-003；私有 no-store、Session 失效、内存隔离、迟到响应和可访问性遵循 BR-CMG-002/004。snapshot、reason、确认集合、submittedBy/decidedBy、策略与原始错误正文不进入 URL/遥测/持久存储。reason 作为纯文本渲染，不解释 HTML/Markdown。页面能通过键盘读取检查、选择结果、提交与恢复，错误与结果未知有焦点和明确状态文本。5xx 不清 Cookie，SESSION_INVALID 只清当前 Admin Cookie。

## 依赖事实、缺口与实现选项

2026-11-04：App `a95bd13` / API `2dc002e` 已实现提交绑定，App 完整 backend 门禁 24/24 通过；详情只返回 `reviewPolicy`，Version 绑定不符 reason 为 `APPLICATION_REVIEW_POLICY_MISMATCH`。Console 必须重新生成固定 API 并严格消费完整定义；缺绑定政策投影/缺定义不接受旧协议只读兜底。既有 Gateway 路由与精确权限不变，其 descriptor 和错误透传仍需核对。

此前固定策略、Scope 变化、私有隔离和普通审核决定的发布镜像证据继续保留在历史实施记录，但不能证明本次新契约已部署。真实新政策切换的联合验收须有正式准备条件；不为测试制造生产政策。后端事务测试、前端组件刷新保持测试和正式联合发布证据分别说明，不互相替代。

## 验收与完成标准

同日实现补充：[正式Scope变化链](../implements/2026-10-26-scope-review-change.md)已以固定API6fea和发布镜像验证，专项30/30、默认全量118/118通过。真实email停用后原批准422、PENDING无部分写、明确重读清确认、不自动重放；停用期间独立REJECT、前向恢复后新目录revision见证及重新确认APPROVE均完成。此有界项不再列为缺准备；上段Gateway/Scope待接线描述属于本次增量前状态。App真实策略发布仍待准备，完整UC不因本项关闭。

1. 真实 grant 后访问、revoke 后新请求拒绝，两类 Reviewer 交叉、无权限管理员和 Developer 均按精确授权；冲突三种原因可读不可决定，最终写仍拒绝。
2. 真实 PENDING 队列/详情、终态深链接、snapshot 与当前 Version 分离；过滤、keyset、空队列与损坏失败关闭有覆盖。
3. 正式策略逐项确认、完整服务端定义、绑定不符、缺/重复 checks、REJECT 理由与空 checks、非预期系统拒绝、批准不自动发布均通过。
4. 两个 Reviewer 并发、依赖故障、响应丢失/断网及 PENDING/终态重读经真实后端验证。正式策略变化采用“A 下提交→发布 B→原记录仍按 A 决定；新提交及拒绝后重提绑定 B”的语义，历史不改写，不新增补审或期限。Scope 失效仍使用 Auth 正式入口，重读后人工确认、不自动重放。缺少正式新政策准备时保留联合验收待准备，不以错误绑定参数或组件合成响应冒充真实发布。
5. 私有缓存、Header/Cookie 清理、权限撤销、SESSION_INVALID、5xx 保会话及键盘/焦点通过浏览器联合验收。定义来源、固定版本、真实服务证据齐全才可标记完整实现；接受首阶段不代表完整决定流程已实现。
