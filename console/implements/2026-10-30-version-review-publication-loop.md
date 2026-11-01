# 版本拒绝、恢复与发布的真实闭环验证

状态：`IMPLEMENTED / TARGETED_ORDINARY_VERIFIED / REAL_REPRESENTATIVE_VERIFIED`，2026-11-01。依据既有自主设计授权接受本工程验证工作包。本页没有新增业务规则或 UC。Console 候选 `d5cc071` 的完整生产页面闭环已通过；同轮其它隔离场景失败与后续摘要读取修正另列，不将单链通过扩大为完整门禁。

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

Console `d5cc071` 已新增仅供本链使用的普通 Reviewer、正式双权限授予准备与两端生产页面闭环。原九次命令前缀及其断言保持；新增四次 owner 命令和三次 Reviewer 决定分别精确核对。准备异常只读回，不能自动重复未知写入。注册加一次 Admin EMAIL 的预算与实际 resendAfter 已纳入 runner，未改变原角色相位或服务限额。

集中前置检查通过：`test:ci-policy` 为 48 项 Node、21 项 Vitest（新增准备回归 8 项），`test:real:types` exit0。新增准备测试已纳入默认 CI policy 入口，包括未知授权已提交、未提交、读回失败、修订漂移和错误目标。它们不代替网页闭环成功证据。

2026-11-01 已冻结 `d5cc071ad72bd71a5e2588bad7e91ccd7c0e182d`，显式选择治理、版本写入和 25 条 Developer 隔离场景集中实测。Auth/App 重新拉取 `latest`，App 更新为 `sha256:18eacd03c1f0cd9b4841bd9b141b61c0d5dde89f6d0045f00322a056541b4027`；Gateway 保持明确授权的本地 artifact。该轮终态、实际发现数与静态冻结校验待补，不能依据启动成功关闭本包或完整门禁。未 push，legacy 保持。

首轮 409215 在浏览器启动前失败，exit1，Auth 与 App 均在 startup 退出，未发现或执行网页场景。原因是仓库外 Python 包装以 umask 0077 启动 runner，导致其明确以 0644 创建的容器挂载文件实际成为 0600；合成 Node 文件验证 0077 得到 0600、0022 得到 0644。仅改该私有包装的子进程 umask 为 0022，日志目录及日志文件仍私有；Console 源码指纹保持，失败轮容器/network 已清理。同一候选的新一轮 412805 已启动，不把首轮记作业务失败或通过，也没有编译、改动后端或放宽业务断言。

## 既有 UC008 的摘要读回遗漏

2026-11-01 有限只读核对发现：UC008 已要求命令后正式版本/管理摘要读回，而 `VersionWorkflow` 在送审、恢复后只读 Version。应用共享导航没有持续挂载的摘要查询，不能用它推定摘要已刷新。放弃后导航的版本主页会通过独立 PublicationPanel 重新读取摘要和版本列表，不能再对已放弃的版本强求成功详情。

依据既有授权接受如下修正，待 412805 终态后实施，不改变本轮冻结：送审、恢复后的同一只读核对流程追加正式 Application 管理摘要 GET，核对目标身份，沿用当前 Session/attempt/signal 边界；两份读取成功才提供新编辑基线入口。ACK 已成功但读回失败时保留“操作已确认”，明确重读只读请求，不自动重放命令；应用访问拒绝仍优先退场。摘要不直接当作 Version 快照，也不向正常用户展示修订。放弃保持成功回列表，并在真实 spec 核对该导航的摘要读取。

本项是已接受功能的遗漏修正，不新增 UC/BR 或后端契约。补充必要组件边界和同链正式读取证据后，再集中运行完整真实门禁；本轮专项通过不能冒充该修正已实现。

修正已实现并提交 Console `e7cdabb`：同 Session/attempt/signal 依序读 Version 和 Application，检查目标与 asOf、保留最低已确认版本修订，两份均有效才显示重新打开入口。ACK 成功后的读回错误仍保持 confirmed，明确恢复不发写命令；放弃保留回列表。真实闭环增加送审、恢复、再送审与放弃后摘要的正式读取核对。隔离 enterB 则等待既有独立发布摘要 GET 与实际内容渲染完成，再开始原严格页面不变断言。

组件最终 **15/15**、Developer strict、real types、隐私回归 **1/1** 和 diff 检查通过。组件首轮14通过/1失败因新增GET-only断言错误地不认可fetchSession的默认GET，修正只影响测试计数表达；最终明确核对两条App GET顺序且命令仍一次。没有在每次UI编辑后重复完整单测。当前已冻结 `e7cdabb34a893ba7e00c9a47e642493d71f58225` 启动**无参数完整真实门禁**，终态待记录，不能提前以412805单链通过代替本候选验收。

## 首轮实际闭环成功

412805 已终态，Console 冻结 `d5cc071`，真实闭环 **1/1 通过，30.8 秒**。原九次命令前缀、独立 Reviewer 的拒绝与两次批准、owner 恢复/保存/再送审/TEST 发布、版本修订 3→4→5→6→7→8、旧审核历史、Profile 首次公开指针、Publication 首次 201/revision1、正式后续 GET 与再次打开/跳转全部执行。owner 13 次、Reviewer 3 次 App 命令精确匹配；Session、设备钥匙与零自动登录/clear/外部请求断言通过。

同轮三文件总结果为 12 通过/4 失败/11 未执行，exit1；未将其它隔离失败隐藏或当作本闭环失败。生产双静态 JS 与 119394 相同，源码和静态产物到终态均未变。通过范围是本页原闭环，不含随后接受的摘要重读修正，也不证明 Stable/Grey/清空或完整并发矩阵。

## 发布浮窗的迟到读回覆盖

2026-11-01 只读核对发现的风险已由隔离组件试验证实。主工作区 `87901b4` 冻结供完整139项实链运行，试验在独立 worktree 中使用与主工作区逐字相同的 PublicationPanel/PublicationSettings、正式生成客户端及实际 Query observer，没有修改主工作区或构建产物。

受控顺序为初始发布 revision4，明确单次设置收到 ACK5，其后独立摘要 GET5 挂起；同一实际 Query 通过原 queryFn 的正常 refetch 取得 revision6，再释放旧 GET5。实际缓存从6回退到5、版本引用回退，浮窗读回区也显示旧引用。试验1项失败，3处断言均命中，只有一次写和三次摘要 GET；未通过直接注入缓存制造交错。这是组件级产品缺陷证据，不是后端实链失败。

依据 UC008 已接受的当前状态读回和迟到消费约束，接受最小修复：自动及手动独立读回均捕获实际 Query/data 所有权，在更新共享缓存或本地读回区前复核；被新读取取代的结果不得回填、开启新基线或触发旧错误副作用。保留正常焦点/重连刷新、ACK与当前读回分别确认、明确重读和禁止自动重放，不增加新 UC/BR 或后端契约。隔离候选先做必要组件回归，再于主轮次终态后集成；当前完整轮次仍只证明原冻结，不能挪作修复候选验收。

隔离候选已提交 `2f177316d28710780bec970d6e48ca0bc5bb2ab0`，仅修改 PublicationSettings 并新增正式组件回归。两入口共用 Query/data/页面 signal 所有权守卫；使用原 Session 绑定的原始客户端，在 PrivateReadAttempt 内部先核对成功或错误再消费，避免旧403退场较新视图。实际 Query 被替换或缺失时停用旧编辑上下文，允许关闭后重开；已采用的本地读回后来被新数据取代时也不能开启旧基线。保留 ACK、未知结论与明确只读恢复，未禁用焦点/重连刷新。

原 RED 转为正式新增 **8 项回归通过**：自动/手动迟到5、自动/手动过时403、同key替换、Query缺失、缺失后点击零写、当前403仍退场。合并既有发布设置及卡片组件测试为 **28/28**，diff通过。此前报告的“Developer strict exit0”已撤回：首次 strict 的测试 QueryCache.build 缺显式 queryKey，补充后其泛型仍不一致；后续 shell 命令的 exit0 掩盖了 tsc 失败。整合完整类型检查重新发现并确认此测试问题，生产无类型修订，失败记录保留，待单独核实真实退出码。没有构建或启动新实链。主工作区仍冻结 `87901b4`，本候选尚未集成，原139项轮次仍不能证明本修复已在真实镜像下通过。

随后保留原提交到唯一 backup refs，将该单一修复接到 `87901b4` 基线上。整合候选 `3ae5c52` 的完整 `pnpm test` **2039 Vitest＋420 Node通过，exit0，零skip/cancel**；首次完整 `pnpm typecheck` 则为 **exit1**，明确命中上述测试泛型。仅给 QueryCache.build 补正式显式类型参数，形成最终候选 `f4952f291a4ecb613994e43336d8fc0da40a329f`，生产文件与完整普通测试时逐字相同。最终 **28/28** 定向组件及**完整 typecheck** 均由独立子进程记录实际 **exit0**，各自源码指纹保持。root已直接复核机器汇总、日志计数和两候选差异，未用后续 git 命令覆盖检查退出码；不因纯测试类型改动机械重跑整套普通测试。候选仍仅一个提交、隔离区干净，主分支未动，待原实链终态后集成。

510774正常终态138通过/1失败后，main已fast-forward到`f4952f2`，未改动原轮次冻结证据，legacy及checkpoint保持。下一集中实链将验证本修复后的生产版本审核/发布代表链，同时复验该轮唯一失败的角色读取观察；在该轮完成前不将本修复标成实链已通过。

修复后的真实代表验证已完成：冻结f6e4c4d的540896 **5/5通过、exit0，1.4分钟**，其中本页完整16条命令闭环32.2秒。实际生产构建包含新读回守卫，正式首次TEST ACK、后续GET、关闭/再次打开/版本跳转及原Session/钥匙保护均通过。源码/静态hash保持、资源清空，详见[集中终态](2026-10-30-console-integration-gates.md#集中修正复验540896)。这证明正常真实发布链兼容；迟到5与新6、过时403等具体交错仍由明确标注的8项受控组件回归证明，不冒充逐个实链复现。
