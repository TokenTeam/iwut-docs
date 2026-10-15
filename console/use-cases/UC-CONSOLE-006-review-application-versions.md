# UC-CONSOLE-006：审核 Application Version

状态：`PROPOSED`

## 用户目标、权限与边界

具有精确 `app.version.review` 权限且无利益冲突的 Reviewer，在 Admin Console 查看真实待审队列及不可变详情，按当前正式策略确认检查后批准或拒绝一个 attempt，并在权限或并发变化时安全恢复。

后端权威为 [UC-APP-030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md) BR-REV-029–034、[UC-APP-005](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md) BR-REV-010–020；真实身份/当前能力投影引用 [UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)。前端不重定义授权、状态迁移、策略、Scope 或 URL 校验。

不包含权限授予/撤销 UI、审核分配/锁单、SLA、通知、申诉、批准撤销、版本编辑、发布槽位或自动上线。测试可由受控 Auth 管理路径准备 grant/revoke，不因此创建 Console 治理页面。

## 队列与详情

1. Admin Console 提供独立“版本审核”入口；不能把登录成功、平台管理员或另一项审核权限解释为已获权。首次请求由真实后端检查，无权限进入稳定拒绝态而非伪造空队列。
2. `ListPendingApplicationVersionReviews`：`POST /app-center/v1/reviews/application-versions:search`。默认全部待审，可按已知 applicationId 精确筛选，使用后端 pageSize/keyset 顺序。显示允许披露的应用/版本、attempt、提交时间及 decisionEligibility；冲突项保留并显示原因。
3. 点击记录或深链接，用 `GetApplicationVersionReview`：`GET /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}`。路径三 ID 绑定同一 Review，不补查管理员管理页。
4. 审核主体只能来自 `review.snapshot`，显示版本标签、launchUrl、兼容范围、capabilities、required/optional scopes 与 OAuth 回调。另行标注提交时 ScopeCatalog/preflight 版本、sourceVersionRevision、attempt、提交事实、当前 Application/Version 上下文、currentPolicy 与 eligibility 的 asOf。
5. 终态详情可读并显示实际 decision、理由、时间与批准验证事实，隐藏决定表单；Version 恢复后原 Review 仍按原终态显示，不把当前 Version 状态覆盖旧决定。

## 决定流程

- 只有当前详情为 PENDING、eligibility 允许且策略检查定义可解释时，才提供 APPROVE/REJECT。未读详情不能从队列直接批准；不预勾选检查项。
- APPROVE 显示当前策略版本和每一必需检查的正式定义，由 Reviewer 逐项主动确认，reason 可选。REJECT 要求符合后端规则的纯文本理由，发送空 confirmedCheckIds；切换结果清空此前确认，reason 可在本次页面内保留但不持久化。
- 提交前显示目标 attempt、决定方向、策略版本及理由供确认。对 launchUrl/回调/资料链接不自动嵌入执行；若 Reviewer 主动打开外部页面，使用隔离的新上下文，不附带 Console Cookie、Session 或受保护标头，不把“打开成功”当检查完成。
- `DecideApplicationVersionReview`：`POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision`。正文只使用现有 command 字段：outcome、读取的 expectedPolicyVersion、主动确认的 confirmedCheckIds 和可选 reason。不添加不存在的 expectedVersionRevision、客户端 reviewerId 或决定时间。
- 提交期间禁用重复操作，不阻止用户离开；迟到响应只更新原目标。成功以响应中的实际 outcome 为准；APPROVE 请求也可能按既有后端资格检查得到系统 REJECTED，必须如实显示，不能乐观显示批准。Version APPROVED 明确不等于已发布。

## 前端业务规则

<a id="br-crv-001"></a>
### BR-CRV-001：精确权限、利益冲突与在线重查

前端入口可帮助导航，不授予权限。每个队列、详情、决定请求都走 Admin Session→Gateway→真实 Auth→App 链路；不持有或重放旧 USER JWS。仅 `app.version.review` 授权版本审核；CURRENT_ADMIN、VERSION_CREATOR、REVIEW_SUBMITTER 提示必须显示，最终仍由后端决定。收到权限撤销/不足后清除该功能的私有审核内容并禁用提交，保留 Admin Session；重新获得权限后从正式查询重新进入，不从缓存恢复决定资格。

<a id="br-crv-002"></a>
### BR-CRV-002：snapshot、当前策略与确认绑定

当前可变 Version、提交时 snapshot、提交检查版本和当前决定策略分别标记。确认集合绑定 `(reviewId, currentPolicy.version, requiredCheckIds)`；刷新后任一变化清空确认并要求重读。currentPolicy 版本和 ID 从详情取得，不能硬编码“当前版本”。缺少已核验检查定义、策略未知、必需详情不完整或状态异常时失败关闭，不用 check ID 猜测政策含义。

<a id="br-crv-003"></a>
### BR-CRV-003：并发变化与结果未知恢复

策略退休/变化、已决定、状态冲突、Scope 失效、preflight 或其他依赖错误按稳定 reason 表达；不自动选择新策略、不补确认、不替换 outcome、不重放决定。已决定/冲突后重读同一详情，呈现实际终态或当前 PENDING，再由用户明确重新评审。

写请求超时、断网或无法确认响应时进入 RESULT_UNCERTAIN，保存本次页面内的原目标，不宣布成功/失败。先重新读取同一 Review：终态只报告已观察到的结果，不能断言由自己完成；仍 PENDING 也不能证明原请求未在途，不自动重发或改发相反决定。明确提示一次性决定由后端串行化，用户重读并重新确认后可发起新的明确提交，继续处理 already-decided/冲突。恢复读取失败或权限撤销时保持“无法确认”，提供退出/稍后刷新；不改用数据库、管理员查询或旧缓存推断。

<a id="br-crv-004"></a>
### BR-CRV-004：审核敏感状态与可访问性

队列分页遵循 BR-CMG-003；私有 no-store、Session 失效、内存隔离、迟到响应和可访问性遵循 BR-CMG-002/004。snapshot、reason、确认集合、submittedBy/decidedBy、策略与原始错误正文不进入 URL/遥测/持久存储。reason 作为纯文本渲染，不解释 HTML/Markdown。页面能通过键盘读取检查、选择结果、提交与恢复，错误与结果未知有焦点和明确状态文本。5xx 不清 Cookie，SESSION_INVALID 只清当前 Admin Cookie。

## 依赖事实、缺口与实现选项

UC030 详情与当前 Proto 已包含 `currentPolicy.version/requiredCheckIds`，因此策略版本与确认 ID 不是缺失 API；队列、详情与决定已有后端能力。客户端须固定生成输入，Gateway 须登记三个 ADMIN surface 路由。

当前公开详情只返回 requiredCheckIds，未返回 `ReviewCheckDefinition` 正式定义/文本。首版不能从英文 ID 自动翻译或套另一策略文案。本提案建议由 App 所有者确认正式定义的可消费来源；选项为后端既有策略投影的后续正式扩展，或与每个不可变 policy version 严格绑定、经过 App 所有者核验的只读定义包。后者不能把客户端包当“当前策略”权威；只用于解释详情返回的精确版本，未知版本关闭决定表单。定义来源未核验前，允许只读队列/详情，不宣称完整审核交付；本 UC 不创建 App API。

## 验收与完成标准

1. 真实 grant 后访问、revoke 后新请求拒绝，两类 Reviewer 交叉、无权限管理员和 Developer 均按精确授权；冲突三种原因可读不可决定，最终写仍拒绝。
2. 真实 PENDING 队列/详情、终态深链接、snapshot 与当前 Version 分离；过滤、keyset、空队列与损坏失败关闭有覆盖。
3. 正式策略逐项确认、未知定义、版本变化、缺/重复 checks、REJECT 理由与空 checks、非预期系统拒绝、批准不自动发布均通过。
4. 两个 Reviewer 并发、策略退休、Scope 失效、依赖故障、响应丢失/断网、PENDING 重读与终态重读通过真实后端；不自动重放，迟到响应不覆盖新目标。
5. 私有缓存、Header/Cookie 清理、权限撤销、SESSION_INVALID、5xx 保会话及键盘/焦点通过浏览器联合验收。定义来源、固定版本、真实服务证据齐全才可标记完整实现；当前仅 PROPOSED。
