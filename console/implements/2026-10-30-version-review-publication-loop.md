# 版本拒绝、恢复与发布的真实闭环验证

状态：`DESIGN_ACCEPTED / IMPLEMENTATION_PENDING`，2026-10-30。依据持续 goal 的自主设计授权接受本工程验证工作包。本页没有新增业务规则或 UC，不表示已经修改 spec、准备账号、运行真实链路或取得通过结果。

## 目标与权威

补齐 [UC008 版本工作台](../use-cases/UC-CONSOLE-008-version-workspace.md) 已实现能力的代表真实链：Developer 已送审版本经独立 Reviewer 拒绝，原管理员明确恢复、编辑保存、重新送审，Reviewer 批准，管理员明确放入测试发布槽位。保留原创建、保存、送审和放弃草稿场景，不以本闭环替换它们。

业务语义引用 App [UC003 草稿更新](../../app-center/use-cases/UC-APP-003-update-draft-application-version.md)、[UC004 送审](../../app-center/use-cases/UC-APP-004-submit-application-version-review.md)、[UC005 审核决定](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md)、[UC006 拒绝后恢复](../../app-center/use-cases/UC-APP-006-restore-rejected-version-to-draft.md)、[UC007 测试槽位](../../app-center/use-cases/UC-APP-007-place-approved-version-in-test-slot.md) 和 [UC016 资料审核决定](../../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md)。Console 审核入口继续沿用 UC006–007，资料创建和编辑沿用 [UC010](../use-cases/UC-CONSOLE-010-edit-application-profile.md)。本页只说明验证编排，不重定义这些规则。

## 既有基础与最小增量

现有 `tests/real/developer-write-workspace.real.spec.ts` 在独立 `versionAccount` 的生产 React 页面创建一个新 Application，完成 Version 创建、自动保存和送审，完成 Profile 创建、自动保存和送审，再创建并放弃另一草稿，共九次实际 App 写入。此前结果与边界见 [Developer 写入工作包](2026-10-30-developer-write-workspace.md) 和 [集中验收记录](2026-10-30-console-integration-gates.md)。原九次写入不能冒充拒绝后恢复或发布的证据。

选择在原九次命令及其完整前缀断言完成后继续同一独立 App、原 Version 和原 Profile；不再创建 Application，也不触碰 Version 只读矩阵的两个 App。原 disposable draft 的明确放弃及其回读保持。闭环只增加管理员四次命令和 Reviewer 三次决定，因此实际 App 写入合计为 **9＋4＋3＝16**。

不复用 `reviewOwnerAccount` 新建 App：现有准备的 26 个读取 App 加四个审核决定 App 已占用该账号隔离部署的配额 30。本工作包没有放大配额、清理旧 App 或伪造管理员关系的需要。

## 参与者与邮件预算

- Developer 复用原 P0 `versionAccount` 的同一 BrowserContext、已建立 Session 和原不可导出设备钥匙。闭环不新增管理员 EMAIL、DEVICE 或 Auth Session。完整套件中该账号仍为注册一次、原 P0 邮箱登录一次、Version 读取矩阵邮箱登录一次，共三封；本增量为零封。
- 新建仅属于本链的普通 Reviewer 账号，不 Apply Developer、不授予平台管理员或 App 运维权限，也不复用其它 spec 的 Reviewer 预算或权限相位。由隔离准备中已有 governor 通过正式 `GET /auth-center/v1/users/:authId/application-review-permissions` 和两条精确 `PUT .../app.version.review`、`PUT .../app.profile.review` 授予审核权限。每条使用实际读取的 permission revision、正式 GRANT 与固定测试理由，随后读回确认；新账号预期 revision 从 1 到 2、再到 3。未知授权只读回核对，不盲目重发。
- 新 Reviewer 只需普通注册，不向浏览器导出注册凭据或 token。Admin 生产邮箱入口建立其独立 BrowserContext 和设备钥匙，注册加一次明确 EMAIL 登录，共两封。把注册回执的实际 `mailReadyAt` 纳入 runner 的共同冷却计算，不降低限额、不猜测其它 spec 已等待足够时间。
- 两个 actor 的 AuthId 必须不同。既有资格、审核读取和审核决定 fixture 的账号、权限、Session、资源与相位均不修改。上述两次 Auth GRANT 属于独立准备，不计入十六次 App 业务命令，也不冒充网页审核动作。

## 具体命令和回读

原九次命令完成后，目标 Version 为 `SUBMITTED / revision 3`，首次 Review 为 `PENDING / sourceVersionRevision 2 / attempt 1`；目标 Profile 为 `SUBMITTED / revision 3`，尚无公开资料指针。新增链如下：

| 顺序 | 执行者与真实入口 | 正式命令与预期结果 |
| --- | --- | --- |
| 10 | Admin Reviewer 打开首次 Version Review 的精确详情 | 明确 REJECT，经 `POST .../reviews/:reviewId/decision` 返回 200；Version 从 revision 3 到 4，Review 保持可读取的终态 REJECTED 和原 snapshot |
| 11 | 原 Developer 明确刷新 Version 工作页并确认恢复 | `POST .../reviews/:reviewId/draft-restoration`，正文为 `expectedVersionRevision: "4"`，200；Version 为 DRAFT / revision 5，原 Review 仍为 REJECTED，恢复审计指向 resultVersionRevision 5 |
| 12 | 同一全页编辑工作区只改一次版本名称并等待保存完成 | `PUT .../versions/:versionId`，强 `If-Match: "5"`，200 与 ETag `"6"`；完整内容保存为 DRAFT / revision 6，随后真实读取确认，不用本地表单值冒充存储成功 |
| 13 | Developer 明确确认再次送审 | `POST .../versions/:versionId/reviews`，`expectedRevision: "6"`，201；Version 为 SUBMITTED / revision 7，新 Review 为 attempt 2、sourceVersionRevision 6、与旧 Review 不同的 UUID，snapshot 含新保存名称 |
| 14 | Admin Reviewer 打开新的精确 Review 并完成本次检查确认 | `POST .../reviews/:newReviewId/decision`，200；Version 为 APPROVED / revision 8，新 Review 为 APPROVED；旧拒绝决定、原 snapshot 和恢复审计仍通过正式读取保留 |
| 15 | 同一独立 Reviewer 打开原 P0 Profile 的精确 Review | 按实际 currentPolicy 确认并明确 APPROVE，200；携带 observed Profile revision 3 和显式 NONE 公开指针，资料升为 APPROVED / revision 4，并建立该 App 的当前公开 Profile 指针 |
| 16 | Developer 进入版本与发布，明确配置测试渠道 | 点击现有测试渠道入口，明确 major 1，从 APPROVED 候选选择目标 Version 并确认；`PUT /app-center/v1/applications/:appId/publications/1/test-slot` 首次创建返回 201，Publication revision 1，testVersionId 为目标 Version，History 为 SET_TEST_VERSION |

版本修订链为 **3 → 4 → 5 → 6 → 7 → 8**。每一阶段以正式 ACK 和后续 GET 证明，未知结果只按现有 UI 明确核对，不为了跑完后续步骤重放命令或直接修改数据。

原九次 owner 命令及顺序断言全部保留；新增 owner 命令仅恢复、保存、再送审、发布，共四次，总计十三次。Reviewer BrowserContext 仅有三次 App 决定命令。两者的计数分别核对再合计十六，不把正式 POST `:search` 读取算作命令，也不豁免其它写请求。

## 发布前置与独立策略

测试发布要求同 App 已有实际 APPROVED 的当前公开资料，不能将 P0 的 Profile 送审成功当作资料发布成功。步骤 15 必须通过 Reviewer React 正式批准，验证首次公开指针从 NONE 指向原 P0 Profile，再通过管理员管理摘要读回。不得 seed 指针、伪造批准终态或绕过 Profile 前置。

Version 与 Profile 审核都复用当前生产审核 UI 的两阶段确认：读取本次详情的 currentPolicy、requiredCheckDefinitions 和 requiredCheckIds，再逐项确认并提交本次决定。当前 Version 正式目录有四条检查、Profile 有两条；不从旧页复制批准状态，不用 Node 决定接口代替 Reviewer 页面。拒绝命令不夹带批准检查，原理由按文本保存和显示。

延用 runner 已有的 Auth Scope catalog、App review policy 与公网 HTTPS/DNS 策略接线。Version 保留原 P0 的空 required/optional scopes、RPC 范围 `[1,2)`、公网 HTTPS 入口和空 OAuth 回调集合。Scope 与 URL 仍由后端在送审、批准和发布时正式复检，不为了测试手写通过回执、关闭检查或新增 Scope 启停相位。空 OAuth 回调允许本 Version 不提供 OAuth 接入，因此本链不需要额外 registration、secret 或 OAuth fixture。

首次 Publication 的预期不存在通过生成的可选 expectedPublicationRevision 未设置表示；当前 client 按 ProtoJSON 省略该字段，不发送 0、伪造修订、If-Match 或客户端审计字段。实际请求应仅含目标 versionId。发布回执验证精确 App、major、Version、revision 1、changed 与 History 引用；随后正式 GET Application 管理摘要读回发布指针和独立 asOf。发布不应改变 Version 的 APPROVED / revision 8。再次打开渠道可检查当前选择、基本信息及精确工作页跳转，读取和关闭不得产生第二次发布。

## 验收与隔离

沿用真实测试隐私包装，trace、截图和 video 保持关闭。登录由真实 SMTP 与双端生产页面完成；浏览器只有 Cookie，没有原 token、签名能力或 Node 凭据副本。原设备钥匙仍不可导出，两个 BrowserContext 的公开 Session binding/generation 在业务闭环前后保持，不能有自动重新登录、Session DELETE 或外部站点请求。入口 URL 和审核理由不执行，表单、确认、一次性秘密不进入持久存储或报告。

不修改已有 `review-decisions.real.spec.ts` 的十四项或后续恢复、Scope、Session 场景，不挪用它们的目标和账号状态；只复用其正式 Review 路径、语义和 UI 确认做法。原九次前缀、Profile 前置、新旧审核历史及发布读回均必须实际执行，任一失败据实保留，后续未运行不记为通过。

本包只补一条代表版本闭环和首次 TEST 发布，不据此宣称 Stable、Grey、清空或并发发布矩阵全覆盖，也不无限扩展排列。组件、fixture 准备、普通门禁和真实冻结的证据分开登记，默认镜像策略及显式本地 Gateway 模式沿用现有工程决定，不编译相邻后端。

## 当前完成边界

仅本工程验证设计已接受并记录，状态保持 `IMPLEMENTATION_PENDING`。尚未新增 Reviewer fixture、修改 spec、创建账号、发送授权或决定命令、构建产物、执行 runner 或修改注册表和入口索引。后续实施必须等待当前独立真实轮次终态，再冻结新的候选集中验证；本设计不能改变正在运行轮次的输入和结果。
