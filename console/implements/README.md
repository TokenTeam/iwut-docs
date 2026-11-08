# iWUT Console 实现状态

2026-11-08 用户已接受UC014/015搜索与本人待接收转让修订，权威UC和导航已更新，按[串行实施工作包](2026-11-08-search-and-incoming-transfer.md)接入。实现和后端镜像验收分别记录，不以原139或App backend通过替代新增React实链。

## 当前状态

2026-11-04 [提交绑定审核策略](2026-11-04-submission-bound-review-policy.md)已完成 Console 本地适配：固定 API `2dc002e`、严格 `reviewPolicy` 和两类完整定义、按绑定决定及刷新保留确认；UC006/007 同步接受设计。客户端540＋Admin241项、夹具105项、完整类型检查、生成漂移、独立性及完整构建通过。API尚未远程发布，本次生成显式使用进程级同 revision mirror；仓库不加入本地路径。App新镜像与Gateway新descriptor链仍待准备，未运行本次真实139项或正式新政策联合发布；下面139绿及旧政策阻塞为历史基线。


2026-11-01 修正候选的[无参数完整551006](2026-10-30-console-integration-gates.md#修正候选的完整门禁551006)已**139/139通过、exit0，25.5分钟，无skip/retry**。冻结1b3650e的源码与静态hash保持，本轮容器含停止项/network清空；已保存`checkpoint/2026-11-01-console-139-verified`，legacy不变。整合普通2039 Vitest＋420 Node及最终类型检查证据保留。当前前端批次完整门禁已通过，正式政策、Cookie恢复及非平台ops发现仍按[交付核对](2026-11-01-management-delivery-audit.md)开放，不将全绿等同完整UC/goal完成；App实施消息仍待明确授权，未push。以下551006仍运行等为历史阶段。

2026-11-01 已冻结`1b3650e`启动[修正候选无参数完整551006](2026-10-30-console-integration-gates.md#修正候选的完整门禁551006)，后台PID已确认live；Auth/App继续pull latest，Gateway及基础镜像沿用显式来源。本次补齐同一修正候选的完整命令证据，实际发现及终态待记，不用已通过5项替代完整结果。App跨聊天实施请求仍待明确授权，Goal active、未push。

2026-11-01 修正后的[540896集中实链](2026-10-30-console-integration-gates.md#集中修正复验540896)已**5/5通过、exit0，无skip/retry**：包含新生产发布读回守卫的审核→恢复→TEST发布，以及完整资格/角色文件。源码及静态hash保持，本轮资源清空；明确取消的兄弟请求已被实际观察。整合普通2039 Vitest＋420 Node通过，最终28组件和完整typecheck均真实exit0。原无参数138通过/1失败保留，不拼成新候选139全绿；[当前交付核对](2026-11-01-management-delivery-audit.md)区分已交付范围与正式政策、Cookie架构及非平台ops发现依赖。Goal active，未push。

2026-11-01 无参数完整[510774终态](2026-10-30-console-integration-gates.md#无参数完整轮次510774)为**138通过/1失败、exit1，139项全部执行**。源码/静态hash保持且本轮资源清空；唯一失败是角色版本页等待两份并发响应头，正修正不成立的观察前提，保留原生精确权限断言。发布迟到读回修复`f4952f2`已在终态后合入main；整合普通2039 Vitest＋420 Node通过，仅测试类型修正后28组件及完整typecheck真实exit0。两项修正将集中实链复验，不借138项或普通绿宣称完整门禁关闭，Goal active、未push。

2026-11-01 只读核实[公开向量远端CI](2026-10-27-protocol-vector-ci.md#2026-11-01-远端工作流核实)：GitHub run40429054771及全部步骤成功，实际日志确认正式协议测试19项通过。关闭该工作包的远端运行证据缺口，不外推当前139项实链或整体Goal。

2026-11-01 UC018及private-view联合实链4/4通过后，默认全量503436在DockerHub Mongo拉取EOF前置阶段退出，未开始浏览器；手动重拉同失败。已实现87901b4的[显式固定基础镜像模式](2026-10-30-local-gateway-runner.md#2026-11-01基础镜像的显式缓存模式)，CI policy57 Node＋21 Vitest通过；新无参数完整回归正在运行，Auth/App仍每轮pull latest，固定Mongo/Traefik与本地Gateway来源分别记录。完整门禁尚未关闭，Goal active、未push。

2026-11-01 [UC018新用户资格→首个App](2026-11-01-developer-application.md#真实首次开通与创建497011)与完整private-view联合专项**4/4通过、exit0**；原Session/Cookie/不可导出钥匙保持，普通用户资格未由fixture预先授予。完整普通2031 Vitest＋411 Node/full strict已通过，当前1326562的无参数完整回归进行中。未宣称全部用例或完整Goal已完成，legacy保持、未push。

2026-11-01 [UC018本人Developer资格](2026-11-01-developer-application.md)已集成main1e9e6af，完整普通**2031 Vitest＋411 Node**、full strict/隐私通过；真实新用户明确申请后沿原Session创建App的联合专项进行中。旧clear480853已1/1通过，补齐此前未执行的同document迟到204边界；仍不拼接为完整138项全绿。新默认真实套件将包含139项，实际无参数终态另记，Goal active、legacy不变、未push。

2026-11-01 三项实链适配已提交 `e6566d7`，real types/隐私与观察器7项检查通过；[四文件专项](2026-10-30-console-integration-gates.md#有界适配候选-e6566d7)正在复验独立Rail刷新、B前既存文本与新旧响应区分、并发拒绝正文取消，并补跑上轮未完成的账号状态。产品仍为92d3516的实现，尚无本候选专项或完整138项全绿声明，Goal继续active。

2026-11-01 `92d3516`的[无参数439913](2026-10-30-console-integration-gates.md#439913-无参数回归外部143中断)发现138项，在末段外部143中断，已观察130通过/3失败/2项serial未执行、末3项未完成，**没有完整通过结论**。全部25项Developer隔离、版本审核恢复/TEST发布含摘要GET、治理严格时间读回及UC014/P1通过。3项失败集中在旧Rail整页观察/独立刷新前提、并发拒绝后的特定正文消费，正在保持保护断言的前提下有界适配；运行资源已清理。用户已恢复Goal，继续处理，不扩大为新后端需求。

2026-11-01 Console `92d3516` 已修复[设置显式读取的迟到副作用](2026-10-30-console-integration-gates.md#设置读取修正)：旧Query结果不会再先污染新Query的修订下界或用旧403触发新视图退场。集中完整普通**1899项Vitest＋411项Node**、工作区strict通过；新候选无参数真实门禁进行中。前一候选422340因确认此产品问题主动中止，未记作完整通过，原失败/中止证据保留。

2026-11-01 App已推送后的[412805专项](2026-10-30-console-integration-gates.md#新-app-镜像后的专项412805)终态为**12通过/4失败/11未执行、exit1**。更新App `latest=18eacd03…` 后，UC015全部16条真实治理命令及暂停/恢复ACK/GET严格比较通过，[时间差异](2026-10-30-app-operation-time-readback-gap.md)已有发布镜像修复证据；[UC008拒绝→恢复→再审核→TEST发布](2026-10-30-version-review-publication-loop.md)完整16条命令也通过。隔离首个失败是Version列表独立发布摘要尚未稳定时的完整页面比较，后续worker EMAIL准备失败和未执行据实保留。下一候选补齐其等待，以及既有UC008送审/恢复后管理摘要读取，再集中完整真实回归；不以单链通过改写整轮exit1。下方“时间待诊断/闭环未实施”等为各历史阶段。

2026-10-30[119394四文件实链](2026-10-30-console-integration-gates.md#四文件专项119394)已终态**28通过/2失败、无skip/retry**：UC017双端退出与UC016双端资料通过；Developer25项隔离中24通过。治理App暂停ACK/GET全资源差异正在增加安全诊断，Tester旧clear的缺失区域检测已修订待复验。UC017已取得真实Auth在线撤销、peer保持及设备保留/明确重登代表证据，不能继续当“只准备未执行”；完整无参数门禁仍待。UC008拒绝/恢复/批准/发布按[已接受的有限工作包](2026-10-30-version-review-publication-loop.md)准备，尚未实施。

2026-10-30 [UC017退出](2026-10-30-current-console-sign-out.md)已实现并本地提交 `8dd231e`：专用BFF/Edge、共享client/面板与按代Query实例宿主接线，旧clear不增加Auth副作用。集中普通1866项Vitest＋404项Node、full strict/build、独立owned Mongo3项与Edge通过；最后结果变化后的入口小修订另32项/strict通过。真实Auth relay/spec接线另行进行，不能把这些绿结果写为实际退出成功。治理/隔离顺序诊断95759为1通过/5失败/1未执行，原失败与后续有限修订见[集中记录](2026-10-30-console-integration-gates.md)。

2026-10-30恢复后的[真实诊断](2026-10-30-console-integration-gates.md)已记录35230的2通过/2失败、51965的6通过/6失败/16未执行。UC016修正匿名直入登录后，双端普通USER五类型set/remove代表链通过；Application旧owned/application的200/401隔离通过，旧clear回执入口和治理响应等待继续修正。旧完整139312失败仍保留，没有借专项绿关闭全仓门禁。[UC017显式退出](2026-10-30-current-console-sign-out.md)已自主接受，待实现专用BFF、Edge和双端入口；不把既有clear当作已撤销Auth。

2026-10-30 [本人账号资料UC016](2026-10-30-own-account-profile.md)已实现两端共用全页，客户端33、共享包117、路由/Session182定向通过；完整1756项Vitest＋392项Node、工作区strict/build通过。目录失败仍可纯删除、正式Session拒绝先清数据再恢复；真实spec/测试目录已准备，未宣称实链成功。上一候选61dd9b3的完整139312轮已终态78通过/16失败/40未执行，按[集中记录](2026-10-30-console-integration-gates.md)分项修复，不能继续当“尚在运行”。

2026-10-30 [本批集中普通门禁](2026-10-30-console-integration-gates.md)已通过：1595项Vitest＋392项Node、完整strict/build、固定官方API生成、Edge与文档一致性均exit0。前两轮单测失败及修复保留；下一步冻结提交后执行无spec筛选真实回归，当前未宣布全量成功。UC015和P0新增放弃草稿将在该轮实际验证。

2026-10-30 [归档与管理权交接](2026-10-30-application-ownership-writes.md)首轮真实专项114910为**1/1、exit0，无skip/retry**；归档/恢复、取消/拒绝/KEEP/ROTATE及原管理员失权、链接撤销/成员保留均通过。UC010拒绝后新建预填已补齐，49组件与7client定向通过；[UC015治理](2026-10-30-platform-governance.md)已实现并定向验证，真实spec已准备。当前[集中验收](2026-10-30-console-integration-gates.md)进行中，不借单项绿宣称全仓完成。UC016本人账号资料仅接受设计，后续实施。

2026-10-30 [Developer测试、OAuth与展示规则](2026-10-30-developer-management-writes.md)代表性真实写链已通过：轮次100874同跑P1与P0，**2/2、exit0，无skip/retry**。生产React完成P1的11次写与P0的七次写，types/privacy前置通过；Auth/App重新pull latest，Gateway显式本地9d6a27f。资源清空、原预览保留。归档/转让和Admin治理另包推进；这不是旧128项全量复验。下方“P1尚未验证/正在验证”等为历史阶段，不重新列为当前全缺失。

2026-10-30 [P0真实写入成功链](2026-10-30-developer-write-workspace.md)已通过1/1：生产React正式创建App、Version创建/自动保存/送审、Profile创建/自动保存/送审，精确HTTP201/200与If-Match/ETag、后续GET/review、七次写/零外域/Session保持均核对。本地Gateway90cf10f0、Auth/App published latest，测试资源清理；预览开启版本写入并保留原数据。前两轮测试误期望200的失败保留。恢复/放弃、审核后发布、P1及完整回归仍未由此证明，整体goal保持进行中。

2026-10-30 goal恢复后，[Developer 写入工作区](2026-10-30-developer-write-workspace.md)已实现 UC009应用创建、UC008版本写入/送审动作、UC010资料创建/保存/送审；Gateway本地9d6a27f镜像已接入且数据保留。集中组件/类型检查通过，独立真实P0链正在验证；[本地镜像 runner](2026-10-30-local-gateway-runner.md)已允许显式不pull Gateway。以下旧“版本命令未开放/写入未实现”为各阶段历史，不再当作当前源码缺口；本轮仍不能借过去128项绿宣称真实写入已成功。

2026-10-30 用户要求整理 [Gateway Console 能力缺口与本地构建交接](2026-10-30-gateway-console-capability-gaps.md)：先补创建/编辑/送审 P0，再补显式管理 surface；账号安全/BFF 与 IP 加端口部署边界单列。本次允许 gateway 自仓构建显式本地镜像加速联调，默认发布 `latest` 验证保留；当前为请求，不表示路由、镜像或页面已经补齐。

2026-10-27 用户要求补齐[Developer 应用配置页面](2026-10-27-application-configuration-pages.md)：接入配置、展示规则与应用设置三个只读首版，六模块导航补齐；复用 UC002 管理摘要与私有读取边界，不新增业务命令。完整规则、OAuth/归档/转让/关闭专用操作仍未接通，视觉与真实浏览器验收独立开放。

2026-10-27 根据用户试用反馈实现[平台导航与应用切换](2026-10-27-application-rail.md)：平台栏目与持续应用切换分层、局部应用导航、悬浮锚定展开与延迟收起；爬虫栏目仅规划说明，无新业务 API/写入。视觉与动画待实际试用，不借此前真实套件记录宣称本轮浏览器验收完成。

2026-10-27 用户接受的 [Developer 版本工作区初版](2026-10-27-version-workspace.md)已实现应用平级导航、版本与发布主页及复用整页表单，按 [UC008](../use-cases/UC-CONSOLE-008-version-workspace.md)迭代。网络写入因 Gateway 创建/更新缺少 DEVELOPER surface 默认关闭；提交、发布等命令仍未接入，视觉验收待补。下文 HeroUI、128 项真实全量和其他历史结果不代表本包已通过实链。

2026-10-27 用户授权的 [HeroUI 组件基础接入](2026-10-27-heroui-foundation.md)已VERIFIED：1068项Vitest＋377项Node、strict/固定API生成/生产构建与published-latest样式键盘专项2/2通过；双端真实邮箱登录和私有读取抽查通过，CSP不放宽。原预览后端数据保留、宿主服务恢复，需重新登录；[页面结构规划](../page-architecture.md)为待审阅草案，未改路由或新增业务命令。以下128项真实全量属于此前冻结，不挪作本包验收；用户已确认此前提交的远端普通CI通过，本包仍未commit/push。

当前有限包[UC001浏览器凭据校验](2026-10-27-browser-credential-validation.md)已VERIFIED：冻结ec34375，published-latest专项4/4、默认128/128通过（1.4/23.9分钟浏览器阶段，exit0，无skip/retry）；1056 Vitest＋359 Node、strict/官方生成/Edge/docs通过。非法点/标量/配对/快照/BOM及命名协议护栏先RED后修，双origin native IDB实际拒绝且保留坏记录，原126完整保留。旧Node合成UUIDv7误用于DEVICE的9项失败与修正过程保留，不弱化协议。两轮五镜像重拉且轮内固定，资源清理、legacy本地/远程未变、不push。[公开向量CI定义](2026-10-27-protocol-vector-ci.md)已LOCAL_VERIFIED（1056 Vitest＋376 Node及全普通门禁、6静态产物逐字一致），实际远端run未获授权执行；外部/架构边界仍开放，不改后端或扩业务UI。

2026-10-27最新[完成性审计](2026-10-27-completion-audit.md)发现的[拒绝后焦点](2026-10-27-private-denial-focus.md)与[双静态Strict CSP](2026-10-27-strict-static-csp.md)已VERIFIED：冻结29aa09b，published-latest专项3/3、默认126/126（31.6秒/23.9分钟浏览器阶段，exit0，无skip/retry），957 Vitest＋359 Node、strict/官方生成/Edge/docs通过。真实parser负例、handler/connect/base/object拒绝、正常生产认证/私有/决定与焦点键盘链均收齐；首轮非parser负例错误及拉取EOF保留。资源清理、legacy本地/远程未变，只本地提交不push。协议/损坏本地记录已有直接有限复现，公开向量CI证据仍需收齐；这是明确后续，不把126全绿当整体UC/goal完成。App政策发布和Cookie33+独立开放。

2026-10-27当前增量：[WITHDRAWN 与正式关闭后的历史读取](2026-10-27-withdrawn-closed-history.md)有界链已VERIFIED。Console冻结ae46e5c，published-latest专项3/3、默认无参数124/124通过（35.7秒/23.8分钟浏览器阶段，exit0、无skip/retry），954 Vitest＋344 Node、strict/官方API6fea生成/Edge/docs门禁通过。专用普通owner正式准备一个App及已提交Version/Profile、Link/Tester；ACTIVE先BLOCKED，正式关闭到CLOSED后Prepare/Confirm退出，原Session/钥匙、九RPC和代表React历史视图保持。未增关闭/退出UI、不seed本链、不编译后端、不push；两轮资源清理、legacy本地/远程未变，旧121全保留。App政策发布及Cookie架构仍独立开放，不关闭完整UC/goal。

2026-10-27此前增量：[账号禁用与恢复后的读取](2026-10-26-account-status-read-recovery.md)有界链已验证，冻结b60fcb6的published-latest专项3/3、默认无参数121/121通过（1.3/21.1分钟、exit0、无skip/retry）。正式专用owner账号1→2→3、Developer实际401退场、恢复后旧Admin/普通Auth Session不复活、两origin原不可导出钥匙显式DEVICE新代读取原App/Review及peer保持通过。954 Vitest＋295 Node、strict/官方API6fea生成/Edge/docs门禁通过，资源清理、legacy未变、未push。初始空时间错误与旧冻结复用owner第6封邮件429（原118通过/1失败/2未执行）均保留；接受专用owner正式准备后邮箱仅注册＋两EMAIL共3次，不放宽限额。只关闭所列代表链，不自动扩成全部状态×页面；WITHDRAWN正式关闭/退出、App策略发布与Cookie架构边界仍开放。

2026-10-26当前增量：[正式Scope启停与旧审核页面恢复](2026-10-26-scope-review-change.md)有界链已验证，内容冻结ba1e1706，published-latest专项30/30、默认全量118/118通过（3.1/19.8分钟浏览器阶段、exit0、无skip/retry）。正式管理员启停/原编号回执、非空openid见证目录revision、旧email APPROVE422后PENDING/清确认/不重放、停用期间REJECT和前向恢复后明确APPROVE均完成。954 Vitest＋249 Node、strict/官方API6fea生成/Edge/docs静态门禁通过，测试资源已清理、legacy未变、未push。两次新增测试预期错误及首轮27/1/2、第二轮29/1保留；App策略发布、角色剩余有界验收和Cookie架构边界仍开放，完整UC/goal未完成。

2026-10-26：[新发布契约组合基线复验](2026-10-26-published-scope-contract-baseline.md)完成，Console冻结e1db0af，Auth518b0917/App68ee32b1/Gateway444c75a7的published-latest审核专项27/27、默认完整115/115通过（2.9/19.2分钟浏览器阶段，exit0、无skip/retry）。普通954 Vitest＋221 Node、strict/官方固定API生成/Edge通过，容器与network清理、legacy未变。Gateway新增三条Scope管理SESSION路由已在发布镜像确认，不开放Console surface符合设计；持久目录配置、正式Scope启停与App真实TTL/Console旧页面恢复的新增准备尚未接入，不能用115项基线关闭。App本次只更新API依赖，政策发布回执/运维读回仍未实现。以下2026-10-23结果保留为历史基线，不是本轮待重跑项。

截至2026-10-23，最新[缓存头修复复验](2026-10-23-published-cache-header-fix-verification.md)已完成：Console冻结6b8834e，published专项35/35（4.4分钟）、默认无参数115/115（19.5分钟）全部通过，均exit0、无skip/retry。原29条缓存头断言全部保留且两轮恢复，无新增功能失败；App latest更新为8e499500、Gateway为509acf96，Auth不变。954 Vitest＋221 Node、strict/官方同pin生成/新Gateway Edge通过；生成检查首次GitHub网络超时及同源重试成功均如实记录。

[阶段收口与继续条件](2026-10-23-console-stage-closeout.md)中的缓存头阻塞已解除，不再要求修复同一组错误或重复无变化全量；仍不自动扩大测试排列/未接受UI。策略/Scope真实变化验收和33+carrier架构边界继续开放；2026-10-26不同修订并发可达性已按用户接受的单工作位设计分层，见UC007验收，门禁全绿不等于整体目标或完整UC已完成。

本轮产品/runtime/runner/spec与32e83da相同，仅更换已发布镜像；五latest每轮重拉并轮内固定，轮次资源已清理、legacy本地/远程未变、未push。旧32e83da镜像组合的111/115及29条失败保留在[原记录](2026-10-23-profile-decision-developer-projection.md)，不能再把旧红门禁当当前状态。

当前跨端投影已实现并收齐所列真实证据，此前因外部缓存头而标红的问题已通过本轮完整门禁解除。生产Developer概览/列表/两详情对照原Admin两次实际批准，独立owner EMAIL/context/钥匙、业务只读、唯一replacement公开指针均验证；不把旧APPROVED当当前公开，不新增发布操作。本页以下先登记当前有界覆盖，再保留历史轮次及首包说明。历史段落中的“待真实验收”“尚无终态”“尚未接线”只描述当时冻结，不重新生成当前待办；最新实际证据以对应工作包为准。

## 当前能力与有界覆盖

本表区分产品实现与已实际覆盖范围；`IMPLEMENTED`仅指所列产品范围，不把接受的UC状态提升为`COMPLETE`。真实业务链、readseed历史投影、fixture与组件直接Query对象证据按各工作包分别记录；已完成的Session/capability/App scope矩阵不等于全heap清理保证，也不外推未列出的角色或生命周期。

| 工作包 | 设计与产品实现 | 已实际覆盖 | 有限未覆盖或门禁 |
| --- | --- | --- | --- |
| Console工程初始化 | UC001 `ACCEPTED`；工程范围`IMPLEMENTED` | pnpm workspace、严格TypeScript、固定统一API生成和校验；双应用/BFF及独立surface真实链已接入 | 不再把“尚未建立真实E2E”作为工程待办；UC001整体仍未关闭 |
| 共享浏览器Session | UC001 `ACCEPTED / IN_PROGRESS`；设备/邮箱码与Session v2基线已实现 | 双origin真实邮件/设备登录、原Begin恢复、提交/恢复等待取消、旧carrier/清理回执、双生产副本/提交点故障，以及两个origin实际32次签发后的显式重建，见[Session v2接线](2026-10-16-session-v2-wiring.md)和[context恢复](2026-10-16-context-exhaustion-recovery.md) | 任意33+迟到carrier的无损Cookie自助恢复仍需独立架构处理；不以此关闭完整UC001/fencing |
| 前端安全与可访问性增量 | [Strict CSP](2026-10-27-strict-static-csp.md)、[拒绝后焦点](2026-10-27-private-denial-focus.md)及[浏览器凭据校验](2026-10-27-browser-credential-validation.md)所列范围`VERIFIED` | CSP/焦点3专项/126全量通过；凭据/协议原生拒绝与正常链兼容4专项/128全量通过，曲线/fingerprint/配对/快照、严格标量和精确上下文均落实 | [CI定义及远端运行](2026-10-27-protocol-vector-ci.md)已核实；不宣称防已受信同源脚本、生产EO已验证或完整UC关闭 |
| Developer Console功能 | UC001–005 `ACCEPTED`；认证入口与四类只读页面已实现，整体`IN_PROGRESS` | 真实成功读取、25项[跨Session读取矩阵](2026-10-16-developer-private-session-matrix.md)、正式管理权转让退场、SUSPEND/RESTORE资格读取与保留生命周期历史投影；Admin→Developer资料闭环、账号禁用/恢复代表链，以及[正式关闭后WITHDRAWN历史读取](2026-10-27-withdrawn-closed-history.md)完成，缓存头门禁已恢复 | 账号状态与WITHDRAWN只声明所列有限链，不外推全部页面×状态；UC001架构边界另列 |
| Admin Console功能 | UC001/006/007 `ACCEPTED`；双队列/详情、批准/拒绝、独立权限/Session恢复已实现，整体`IN_PROGRESS` | [查询及权限读取](2026-10-16-admin-review-queries.md)、12项[读取跨Session矩阵](2026-10-16-admin-private-session-fencing.md)，以及原26项决定功能：双Reviewer、真实期限/结果未知、撤重授、加载后利益冲突、六项决定跨Session交错和真实App→Auth断链/恢复；原4条401缓存头已恢复；追加3项Scope变化/恢复及账号恢复后旧审核Session拒绝/原钥匙重登已在121全量通过 | Scope及账号状态所列有界链已验证，真实策略变化仍待准备；资料并发按已接受的单工作位与指针防御分层核对，文档修正不新增实际覆盖，见下表；不再把决定surface/正式定义/Reviewer公开指针接入列为当前缺失 |
| Developer Application概览 | UC002 `ACCEPTED`；只读产品范围`IMPLEMENTED` | [25个正式Create的20+5累计分页](2026-10-16-owned-application-pagination-and-recovery.md)、筛选/游标/空态、正式转让后的管理权回收、跨Session及SUSPEND/RESTORE、ACTIVE/CLOSING/CLOSED保留历史读取，错误缓存头门禁恢复；[账号禁用/恢复](2026-10-26-account-status-read-recovery.md)和[WITHDRAWN正式关闭历史](2026-10-27-withdrawn-closed-history.md)代表链通过 | 不把有限链扩大为全部页面×状态；不新增Developer写入口 |
| Developer Application Version | UC003 `ACCEPTED`；只读产品范围`IMPLEMENTED` | [四状态/恢复DRAFT、20+5、正式错误码与断流恢复](2026-10-16-version-pagination-and-recovery.md)，当前内容与latestReview分区、bigint/惰性文本、管理权/Session及上述保留历史读取；正式关闭→WITHDRAWN后SUBMITTED/PENDING原历史读取通过 | 账号状态采用本页代表链及既有Session隔离证据，不宣称本页独立治理矩阵；不新增完整审核历史或发布管理，APPROVED不解释为已发布 |
| Developer Application资料修订 | UC004 `ACCEPTED`；只读产品范围`IMPLEMENTED` | [四状态、20+5列表及独立历史、页外指针、原文/隐私与真实413](2026-10-16-profile-pagination-and-budget.md)，管理权/Session、SUSPEND/RESTORE及保留历史读取；[Admin→Developer实际批准投影](2026-10-23-profile-decision-developer-projection.md)及正式关闭→WITHDRAWN后SUBMITTED/PENDING原历史读取完成 | 账号状态采用本页代表链及既有Session隔离证据，不宣称本页独立治理矩阵，不把已有读取重新登记为未验收 |
| Developer Application Tester管理 | UC005 `ACCEPTED`；三个独立只读区域`IMPLEMENTED` | [25条ACTIVE成员/26条链接、分页/筛选/空态、区域断流及真实精确撤销](2026-10-16-tester-pagination-and-privacy.md)，权威容量与成员保持、管理权/Session和上述资格/历史读取；正式关闭→WITHDRAWN后ACTIVE历史成员、REVOKED链接及空当前链接读取通过 | 账号状态采用本页代表链及既有Session隔离证据，不宣称本页独立治理矩阵；REMOVED/ALL成员、secret恢复与本人Tester入口仍非本阶段范围，不因索引整理新增待办 |

## 有限开放项与外部边界

| 类型 | 当前开放项与推进条件 | 依据 |
| --- | --- | --- |
| UC001协议已补齐，CI远端交付独立 | 合成非法点/零DER/损坏记录签名缺口与命名重放/等到期/单次哈希已由[凭据包](2026-10-27-browser-credential-validation.md)修复并通过4专项/128完整门禁；不再当全部未实施。CI定义7b32305已通过本地1056 Vitest＋376 Node及全普通门禁，同配置6静态产物逐字一致；旧stub首轮失败与恢复保留。远端run40429054771及协议测试日志已核实，关闭此项远端证据缺口，不扩大为当前完整候选已远端验证 | [完成性审计](2026-10-27-completion-audit.md)、[CI包](2026-10-27-protocol-vector-ci.md)、[UC001验收](../use-cases/UC-CONSOLE-001-establish-console-session.md#测试与验收) |
| 已完成的有限角色证据，范围不外推 | WITHDRAWN正式关闭→退出→CLOSED历史读取已由3专项/124全量验证，非SUSPEND或旧readseed替代；账号禁用/恢复所列代表链已通过3专项/121全量，并在124全量再次通过。不再登记为全部缺失，也不自动扩成全部角色×页面组合 | [WITHDRAWN证据](2026-10-27-withdrawn-closed-history.md)、[账号状态证据](2026-10-26-account-status-read-recovery.md)、[资格与角色边界](2026-10-16-qualification-and-role-read-boundaries.md) |
| 正式变化准备与联合验收 | App已接受正式发布流程，原子回执/运维读回尚未实现，下一份真实政策另审；Auth UC036正式启停、Gateway接线、App真实TTL后目录revision消费与Console旧页恢复的有界链已由30/118门禁验证；Auth自身全量与生产启用仍按其所有者独立门禁，不由Console代验。错误expectedPolicyVersion、合成policy JSON或直接改库不是真实加载后变化证明 | [App发布流程](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[Profile兼容门槛](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md#策略版本兼容门槛)、[Scope联合证据](2026-10-26-scope-review-change.md)、[Auth交付边界](../../auth-center/implements/UC-AUTH-036-readiness.md) |
| 已接受的可达性分层，证据保持原范围 | UC007验收4已按用户接受的单工作位方案同步：同Review双决定、顺序替换、错误pointer409协议防御与组件恢复分别标记；不同修订同时PENDING不是当前可达业务要求，不seed平行PENDING。既有证据不改名，不因文字同步宣称新增真实链通过 | [UC007验收](../use-cases/UC-CONSOLE-007-review-application-profiles.md#验收与完成标准)、[单一工作修订](../../app-center/use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006) |
| 架构问题 | 任意33+迟到carrier后的无损Cookie自助恢复未交付；实际32次context签发后的显式重建已覆盖，不把两者混作同一待办。有限诊断已证明浏览器可发送应用handler到达前被HTTP解析器拒绝的Cookie头，单加BFF清理路由不足以覆盖完整问题 | [传输边界分析](2026-10-23-cookie-recovery-transport-boundary-analysis.md)、[context恢复边界](2026-10-16-context-exhaustion-recovery.md)、[fencing记录](../query-contracts/login-flow-fencing.md) |
| 已登记、未确认修复的观察 | 早期fixture偶发缺数据经多轮未再现，因果仍OPEN；不是本次真实全量新增功能失败，也不能以重复绿宣称已修复 | [读取消费边界](2026-10-16-developer-read-consumption.md)、[Admin读取恢复](2026-10-16-admin-read-recovery-and-late-responses.md) |

本索引不改变任何BR、完成标准或当前允许范围。密码入口、显式退出/设备治理、Developer创建/编辑/提交/发布UI、Tester本人入口等未在当前阶段接受的功能须另行决定，不借“补覆盖”顺手实施。其它决定依赖如DNS/ScopeCatalog/System principal故障不由本次一项Developer Status通道断链外推为已覆盖；若后续选取，须单独说明用户价值与有限证据，不能由“完整矩阵”自动生成无穷排列。

## 历史实施与轮次记录

以下保留原冻结、失败、中断和阶段性未完成描述，便于追溯；它们不是与上文并列的当前状态。各工作包的实际输入、镜像、失败与清理记录仍以对应原文为准。

[Version批准Auth依赖恢复](2026-10-23-version-decision-auth-dependency-recovery.md)已实现且published专项功能收齐：冻结09f7805，26项25通过/1失败（2.9分钟、无skip/retry）。新场景真实App503/DEVELOPER_STATUS_UNAVAILABLE，断链仅App→Auth、Gateway与另一能力仍工作；unknown/reason/焦点、不重放/不清Session、恢复后明确读同Review PENDING/revision/snapshot保持通过。最后项仅被原4条Gateway Session401缺private的afterAll标红，新503本身private/no-store均存在。954 Vitest＋221 Node、strict/官方生成/Edge通过，专项资源清理；同冻结114项默认全量已启动，尚无终态，完整门禁/UC保持IN_PROGRESS、不push。策略退休/Scope启停等缺口不以此替代。

决定Session边界最新终态：同冻结`c60dd59`的published专项25项24通过/1失败（2.7分钟），默认无参数113项109通过/4失败、无skip/retry（19.0分钟、exit1）。两轮25项body功能断言全部完成，29条失败逐项仅为原Application缓存头25＋新Gateway决定Session401缺private4；不删断言、不推送红门禁。950 Vitest＋195 Node、strict/官方生成/Edge通过，五镜像每轮重拉latest且解析ID未变、测试资源清空、legacy不变。完整UC/门禁仍IN_PROGRESS；下一项[Version批准Auth依赖恢复](2026-10-23-version-decision-auth-dependency-recovery.md)仅ACCEPTED/NOT_STARTED，不把缺失的策略退休/Scope启停API用合成响应替代。下文“全量正在运行”属于前阶段记录。

[决定跨Session边界](2026-10-23-review-decision-session-boundaries.md)已补齐固定外部失效fault和两cap旧401/旧DELETE204/旧200六项实际交错，并修复旧attempt返回后仍读Session/解码正文的问题。最终c60dd59冻结published专项25项24通过/1失败（2.7分钟、无skip/retry）：25项body功能断言完成，afterAll保留4条Gateway Session401缺private的失败（no-store存在），不宣称全绿。950 Vitest＋195 Node、strict/官方生成/Edge通过；专项资源清理、legacy本地/远程不变、未push。同冻结无参数113全量正在运行，不能用前040的107或本专项替代新全量。下文第一阶段尚未接线/19项等为历史，完整UC及其它缺口继续OPEN。

[决定跨Session边界](2026-10-23-review-decision-session-boundaries.md)已接受并完成第一阶段局部修复：两cap组件先红复现决定401后等待旧DELETE ACK时snapshot/表单残留，修复将精确Session错误送入原捕获详情Query并cancel旧读、清data，由父详情统一恢复；新增17 core＋6组件先红后绿。产品`238bc07`，统一926 Vitest＋183 Node、strict/官方同pin生成/build/Edge通过，fixture浏览器10通过/6既有非目标skip。六项真实决定Session交错/计划25专项与113全量尚未接线执行，改后真实门禁未过，仍IN_PROGRESS/未push；不把前040轮次19/107挪作新证据。

[Profile加载后管理关系变化](2026-10-23-profile-loaded-conflict-recovery.md)所列增量已实现：在原18项后正式Create/Submit第三份资料，复用既有APPROVED主Reviewer且零重复Apply，以固定独立双向转让验证旧表单实际403只要求同Review重读、不撤整个能力，转回后仍PENDING且须重新确认。无新账号/App/quota/Session/seed或Developer写UI。冻结`040cfc7`，903项Vitest＋183项Node、strict/官方同pin生成/Edge通过；published专项19/19（2.2分钟），默认无参数107项104通过/3失败、无skip/retry（18.8分钟、exit1），全部19项决定再次通过，23决定响应private/no-store全真。25条失败仍为原Application错误缓存头（转让3/owned10/资格12），无新增非缓存硬失败；两轮资源为空、legacy本地/本次远端不变、未push。完整门禁与UC继续IN_PROGRESS，其它决定/Session矩阵仍开放。

[Profile决定并发与迟到回执](2026-10-23-profile-decision-concurrency-and-late-receipts.md)所列增量已实现：原15项后复用已有账号/App/context/Session，正式Create/Submit两份新Profile补同Review双决定、真实deadline/PENDING恢复及重新明确提交后的迟到成功回执。固定准备未知写只读确认、不扩Developer写UI。冻结`a89e2e4`，903项Vitest＋172项Node、strict/官方固定pin生成/Edge通过；published专项18/18通过（2.1分钟），默认无参数106项103通过/3失败、无skip/retry（18.7分钟、exit1），全部18项决定再次通过，22个决定响应private/no-store全真。25条失败仍全部为原Application错误缓存头（转让3/owned10/资格12），无新增非缓存硬失败。两轮资源清理、legacy本地/远程不变、未push；完整门禁与UC仍IN_PROGRESS，不以本包关闭其余矩阵。

[Version加载后管理关系变化](2026-10-23-review-loaded-conflict-recovery.md)所列增量已实现：既有Reviewer正式Apply/双向转让制造加载后的CURRENT_ADMIN，实际403保留能力并同Review重读冲突，转回后重新读取eligible，Session/钥匙保持、无决定重放。不扩账号/App/quota/登录或前端写UI，资格APPROVED不可逆只发生在原14项后。冻结`77201dd`，903项Vitest＋160项Node、strict/生成/Edge通过；published专项15/15（1.7分钟），默认无参数103项100通过/3失败、无skip（22.5分钟、exit1），15项决定再次全过。全部25条错误仍是原Application缓存头（转让3/owned10/资格12），无新增非缓存硬失败。两轮资源为空、legacy本地/远程不变、未push；完整门禁和UC仍IN_PROGRESS，Profile并发/迟到响应仅为未实施候选。

[结果未知后的权限撤销恢复](2026-10-22-review-uncertain-permission-recovery.md)已实现所列两项：复用正式PENDING资源和主双权限Reviewer，Version/Profile的unknown→正式revoke→真实GET403→regrant→同Review终态读取通过，保留另一能力/Session且不重放决定，不增加账号、配额或业务seed。冻结`dcdb08f`，published专项14/14通过；2026-10-23最终无参数102项99通过/3失败、无skip（17.9分钟、exit1），14项决定再次全过。全部25条错误仍为原Application缓存头（转让3/owned10/资格12），无新增非缓存硬失败。903项Vitest＋143项Node、strict/生成漂移/Edge通过；资源清理、legacy本地/远程不变、未push。完整门禁及其余决定/Session矩阵仍IN_PROGRESS；后续加载后CURRENT_ADMIN仅为已记录候选，尚未实施。

2026-10-22[已发布审核决定验收](2026-10-16-admin-review-decisions.md#已发布无参数全量终态)：Gateway latest已更新为`2953ae7f…`并补齐两条ADMIN决定接线，API同pin官方远程检查通过，决定12项已迁入默认门禁、不再skip。冻结Console `65a9ea0`的published专项12/12通过（1.1分钟）；最终默认无参数100项97通过/3失败、无skip（17.8分钟、exit1），新增12再次全过。仅25条原Application错误缓存头断言仍红（转让3/owned10/资格12），Admin原56条已全部通过。903项Vitest＋132项Node、strict/生成漂移/六入口Edge通过；两轮资源均清理、legacy本地/远程不变、未push。完整门禁及未列明决定故障/不同修订指针并发仍IN_PROGRESS；下文较早镜像和只读阶段为历史记录。

[Developer全读取入口跨会话矩阵](2026-10-16-developer-private-session-matrix.md)专项25项全部通过（3.8分钟、exit0），冻结`6043f31`的最终无参数88项中84通过/4失败（16.6分钟、exit1），新增25项再次全过。81条错误逐条仍是原App缓存头（Admin56/转让3/owned10/资格12），无新增硬失败。统一837项Vitest＋122项Node、strict/固定生成漂移/build/fixture浏览器/Edge通过；首轮外部中断单独记录并精确清理，最终轮资源为空、legacy本地/远程不变、未push。完整门禁仍IN_PROGRESS，不把本25项或组件测试当所有角色/生命周期完成。

[Developer私有读取消费边界](2026-10-16-developer-read-consumption.md)已实现、完整门禁IN_PROGRESS：请求级Abort/lifetime＋本地Session检查、未知错误精确退场、Tester区域自动恢复限制及旧Query对象数据清理先红后绿。统一837项Vitest＋103项Node、strict/固定生成漂移/build/Edge通过；fixture首轮Tester偶发失败，独立10次和完整3轮随后通过，但因果仍OPEN。冻结`0676e64`后新拉latest无参数63项59通过/4失败（13.1分钟），81条均为原App缓存头，未增非缓存失败。资源清理、legacy不变、提交仅本地；不关闭所有页面/角色跨Session矩阵或完整UC。

### 早期工作包与验收阶段（历史）

[Admin私有视图真实跨会话隔离](2026-10-16-admin-private-session-fencing.md)已接受：两个独立单项Reviewer、四读取入口×旧200/401/204十二例，使用正式授权和真实生产React，不改现有R权限相位。新旧Cookie/Session/DOM与同document清理回执均须真实验证，不以已有组件或Developer证据关闭Admin矩阵；实现/验收待完成。

[Admin读取恢复与迟到响应](2026-10-16-admin-read-recovery-and-late-responses.md)已实现、门禁IN_PROGRESS：同页队列刷新、请求级取消隔离、未许可错误精确退场及语义精确时间已接入；690项Vitest＋89项Node、strict/生成漂移/build/Edge通过。重启后专项7通过/1失败（57.2秒），最终无参数51项47通过/4失败（11.9分钟、exit1）；新增四项两能力队列/详情的原生200正文TypeError、React原投影/asOf保留、键盘恢复和前页栈均再次通过。81条失败全部为原App错误头（Admin56/转让3/owned10/资格12），无新增非缓存失败。首轮宿主机重启中断已核验清理，后续两轮资源也为空；五镜像ID不变、legacy未变、未push。首轮fixture两项多轮未复现但因果仍OPEN，不宣称已修；完整审核决定、真实Admin跨Session及原错误头门禁继续开放。

Gateway CI完成后的[最新无参数复验](2026-10-16-admin-review-queries.md#gateway-ci-完成后的无参数全量复验)：Console `72de336`，轮次`iwut-console-real-924773`，47项终态43通过/4失败（11.7分钟、exit1）；匿名来源修订已纳入完整运行，81条失败全部为既有App查询错误响应头断言（Admin56、转让3、owned游标10、资格角色12），无新增非缓存失败。Edge、普通633项Vitest＋89项Node、strict、生成漂移及仓库独立性再次通过；重新pull latest五镜像ID不变，容器/网络已清理、legacy未变、未push。下文较早“修订后未重跑47项”仅为历史轮次状态；最新完整门禁仍IN_PROGRESS，不缩减完整UC或审核决定范围。

[Admin审核查询首阶段](2026-10-16-admin-review-queries.md)已实现、完整门禁IN_PROGRESS：固定同pin四client、双队列/三元详情、snapshot/current/历史决定分区与能力/Session隔离；普通633项Vitest/89项Node、strict、生成漂移、build、fixture浏览器10通过/6非目标skip及Edge通过。47项无参数全量43通过/4失败（11.6分钟），原三项仅App错误头，新Admin项另有匿名元数据测试预期错误；终态后修订来源/认证分层，最终focused四项3通过/1失败（45.4秒），所列权限/撤重授/Session/匿名/跨surface功能均完整执行，唯一56条错误为Reviewer查询28个400/403/404各缺private/no-store。三轮重新pull latest、digest相同，资源已清理、提交仅本地、legacy本地/远程不变。修订后未重跑47项，不以focused替代完整门禁；完整审核决定与其三类接入依赖仍开放。

[Version分页与正式错误码恢复](2026-10-16-version-pagination-and-recovery.md)增量已实现、整体门禁仍IN_PROGRESS：正式reason先红后绿，400/成功协议错误精确退场与每批asOf已实现；普通452项Vitest/32项Node、strict、生成漂移、fixture浏览器、Edge及focused真实4项通过，含四状态/恢复DRAFT、20+5与断流恢复。无参数完整门禁终态33项中32通过/1失败（8.9分钟），仍仅3条App管理详情404 no-store断言失败，其余全部通过；资源已清理、提交仅本地、legacy不变。不套用Profile预算或Tester token绑定，不因本包独立通过关闭上层UC。

[保留生命周期历史读取矩阵](2026-10-16-retained-lifecycle-read-matrix.md)增量已实现、整体门禁仍IN_PROGRESS：四正式Create/二正式Archive、三阶段readseed与12组合×8RPC和React代表路径focused3项通过；默认生命周期文案、关闭摘要展示先红后绿，普通455项Vitest/49项Node、strict、生成漂移、fixture浏览器和Edge通过。无参数全量终态36项中35通过/1失败（9.9分钟），新增三阶段含加强计数全部通过，仍仅原3条App详情404 no-store断言失败；首两轮准备暴露的密码429/全局hash冲突已修复并保留门禁。资源已清理、提交仅本地、legacy不变；平台/关闭历史seed不当治理/关闭命令或Auth撤销收敛证据，不绕过当前密码＋新设备签名近期认证、不扩展生产写UI，资格下降另包。

[UC002累计分页与正式错误恢复](2026-10-16-owned-application-pagination-and-recovery.md)增量已实现、完整门禁仍IN_PROGRESS：正式reason、拒绝投影精确退场/后续503不复活及每批asOf先红后绿，普通512项Vitest/56项Node、strict、生成漂移、fixture浏览器和Edge通过。仅测试实例以正式初始quota配置30准备25个真实Create的App，不seed owner/quota、不改变生产默认10；独立peer只注册并遵守邮件冷却。focused三项2通过/1失败（13.5秒）；最终无参数39项全量为37通过/2失败（10.1分钟、exit1），新20+5/非空cursor刷新与筛选重置/空详情及正文断流恢复、原其余35项全部通过。两失败项仅为原Get404的3条no-store及5个List400各缺private/no-store的10条soft断言，功能/Session断言仍收齐；未删断言或补代理头。每轮重拉latest、digest相同，资源已清理、提交仅本地、legacy不变。UC029 token不套用Tester ownershipRevision、父App或HMAC假设，当前包不关闭资格下降、UC001/fencing或UC006–007。

[资格下降与非管理员角色读取边界](2026-10-16-qualification-and-role-read-boundaries.md)增量已实现、完整门禁IN_PROGRESS：四真实角色正式bootstrap/grant/Create/Join/SUSPEND/RESTORE，不seed本包权限/资格/依附数据，不扩生产写UI。原43项全量40通过/3失败含Tester取消正文测试竞态，修订focused4项3通过/1失败；后续Admin无参数47项回归已包含修订及全部原43项，终态43通过/4失败（11.6分钟、exit1）。本包三阶段通过，G/R/T全部原生/React/最终Session断言完成，唯一12条soft错误仍是Application GET404缺private/no-store，没有正文取消硬失败；Admin权限相位恢复双权限未污染本包。五镜像ID相同、资源已清理、提交仅本地；WITHDRAWN/账号禁用、原错误头及上层UC继续开放。

[真实Tester分页、容量与最小披露](2026-10-16-tester-pagination-and-privacy.md)已接受：补25条ACTIVE成员、历史episode、独立链接分页/筛选、容量与无当前链接的真实读取矩阵，以及畸形成功的区域级退场；不增加产品写入口或REMOVED成员入口。

[真实资料分页、历史与预算错误](2026-10-16-profile-pagination-and-budget.md)已接受：在两个正式Create的测试App中按唯一索引准备四状态及25条遗留读取历史，补真实keyset、页外指针与413错误；不绕过validator，不增加资料写UI，不关闭既有镜像响应头缺口。

[真实管理权转让与私有读取回收](2026-10-16-management-access-loss.md)已接受：修复同Session明确404后旧数据保留，验证归档Application真实转让和UC002–005旧/新管理员页面，不增加写UI或Reviewer授权。

[context签发上限显式重建](2026-10-16-context-exhaustion-recovery.md)已交付：精确旧context终止、稳定receipt重试和两个独立origin实际32次签发后的React显式恢复通过；完整真实套件21项通过。没有放宽Cookie硬上限或自动重放登录，全部私有页/管理权变化矩阵仍待补。

实现目录为独立的 `iwut-console` 仓库。UC001 接受后已初始化 pnpm workspace；本页的 `IN_PROGRESS` 不表示真实 E2E 或 UC 完成。

[真实镜像浏览器联合验收工作包](2026-10-16-real-service-browser-verification.md) 已自行接受并交付，`pnpm test:real` 的 2 项真实 Browser/BFF/Gateway/Auth/App 测试通过，覆盖双 Console 邮件/设备登录、UC002–005 成功读取及 Session 失效回收。各 UC 的完整状态/恢复/并发验收矩阵仍继续实施；测试只使用已发布 backend latest 镜像，不依赖相邻源码路径。

[UC001 邮箱重发与浏览器恢复控制增量](2026-10-16-login-recovery-controls.md) 已自行接受并交付，真实 SMTP 重发后登录验证通过。页面回调隔离与 Cookie 的跨请求顺序不是同一保证；[登录 flow fencing 缺口](../query-contracts/login-flow-fencing.md) 独立保持 OPEN，UC001 整体仍为 IN_PROGRESS。

[ADR-CONSOLE-005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) 已接受共享持久 Session 与不同代认证 carrier；[持久状态原子核心工作包](2026-10-16-durable-session-core.md) 后续扩展至24项真实 Mongo 测试，已由 Session v2 接线替换旧无状态 BFF。缺口只有在真实跨副本/浏览器故障门禁完成后才能关闭。

[Session v2 接线工作包](2026-10-16-session-v2-wiring.md) 已同步接入 Browser/BFF/Edge，通过17项真实 Mongo双连接/双Hono交错、fixture浏览器及2项真实镜像成功主链；完整浏览器/生产副本故障矩阵继续实施。精确 wire 与恢复/会话版本边界见 [接线契约](../query-contracts/console-session-v2.md)。

[真实浏览器 Session fencing 验收](2026-10-16-real-session-fencing.md) 已交付7项真实迟到响应头、双标签页、两生产副本及Auth提交点崩溃/依赖故障场景，与原2项UI成功主链联合通过；Begin未知、失败兄弟恢复、Mongo回执丢失及真实UI/cache故障矩阵仍开放。

[未知结果与真实 UI 恢复验收](2026-10-16-unknown-result-and-ui-recovery.md) 已交付实际Begin原请求恢复、两次DEVICE认证失败后原EMAIL成功，以及Mongo提交回执丢失两个分支；修复UI对Begin5xx的未知结果分类，联合真实测试13项通过。迟到Begin与真实私有DOM/cache矩阵仍待补，UC001/fencing不关闭。

[真实浏览器失败报告隐私护栏](2026-10-16-real-report-privacy.md) 已交付：合成定位器/hook/API回归保持4失败/1通过，当前标准报告无随机输入材料；共用fixture后重新拉取latest，13项真实测试再次全通过。不以隐藏诊断替代失败状态，不改变上述真实验收的完成边界。

[真实UI迟到与私有视图隔离验收](2026-10-16-real-ui-concurrency.md) 已交付：实际Begin等待取消/新意图替换及旧业务成功/SESSION_INVALID与新身份交错；完整真实套件16项通过。直接Query内存检查与真实DOM/网络证据分层记录；Complete/Recover等待取消、旧清理回执与新同页缓存交错、context上限恢复仍开放，UC001/fencing不关闭。

[提交/恢复等待取消与旧清理回执](2026-10-16-pending-cancel-and-clear-ack.md) 已交付，补EMAIL/DEVICE等待与恢复新root取消，以及同一实际SPA文档内新B私有视图建立后旧A清理回执迟到的交错；无参数完整真实套件19项通过。context上限重建及全部私有页/权限变化矩阵仍待补，仍不关闭UC001/fencing。

## 历史：UC-CONSOLE-002 首个实现工作包

当时状态：`IMPLEMENTED`（首包时真实浏览器联合验收仍待完成；后续已覆盖范围见上方当前表及对应工作包）。以下保留首包原始边界与结果。

接受输入与范围：

- 固定统一 API commit `a5d504c058c62cd91be451074d21608d69789918`；
- 生成 `app_center/v1/application_management` 类型并提供严格 ProtoJSON fetch client；
- Developer Console 增加 `/applications` 列表与 `/applications/{applicationId}` 只读详情；
- 列表覆盖服务端默认筛选、生命周期/平台/归档状态筛选、不透明 token 逐页加载与显式刷新；归档默认不限制且不能从管理面隐藏；
- 详情覆盖深链接、统一不可访问、刷新、返回列表和 UC003–005 的禁用/未交付导航表达；
- `SESSION_INVALID` 只清 Developer Session 并返回登录入口，网络/5xx 不清 Session；
- 所有业务响应只在内存 Query cache 中短暂存在，不启用持久化，不写入 Web Storage、IndexedDB 或日志。

非目标：

- Application 创建、编辑、转让、关闭、归档或任何其它写命令；
- UC003–005 的 Version、ProfileRevision、Tester 具体页面；
- 用 mock 或组件测试宣称真实管理授权链完成。

验证命令：

```bash
pnpm generate:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test
pnpm edge:e2e
```

2026-10-15 实现结果：

- `@iwut/api-client` 已按固定输入生成 Application Management 类型；浏览器 transport 只接受同源绝对路径并使用 `credentials: same-origin`、`cache: no-store` 和严格 ProtoJSON 解析，BFF 登录 transport 继续使用 `credentials: omit`；
- Developer Console 已交付 `/applications` 和 `/applications/{applicationId}`，筛选写入 URL search，分页 token 只留在 Query 内存状态；默认请求不施加归档过滤，因此保留 `ARCHIVED` 与 `UNARCHIVED`；
- `SESSION_INVALID` 会清除当前 surface Session 和私有 Query，BFF 清理失败也不会把旧页面继续当作已登录；网络/5xx 不主动清 Session；
- Vitest 覆盖 client、筛选、详情、不可恢复 secret 和 Session 失效；Playwright 在真实浏览器 origin 上覆盖同源请求、归档默认可见、筛选和详情导航，但业务响应仍为类型化 fixture；
- Console `edge:e2e` 拉取 Gateway `latest`（验证 digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`），确认 UC002 两条 Developer route 与失败关闭；Gateway 协议 E2E 使用 Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、真实 Mongo/BFF/Gateway 验证身份交换和 16 条管理查询/本人退出路由。

剩余验收只限于把已实现页面连接到同一套真实服务环境，准备真实管理员与 Application 数据并由 Playwright 操作页面；完成前不得把 fixture 浏览器测试表述为完整业务 E2E。

## 历史：UC-CONSOLE-003 首个实现工作包

当时状态：`IMPLEMENTED`（首包时真实浏览器联合验收仍待完成；后续已覆盖范围见上方当前表及对应工作包）。以下保留首包原始边界与结果。

接受输入与范围：

- 继续使用统一 API commit `a5d504c058c62cd91be451074d21608d69789918`；
- 生成 `app_center/v1/application_version` 类型并提供严格 ProtoJSON 同源 fetch client；
- Developer Console 增加 Version 列表与详情路由，UC002 详情启用 Version 导航；
- 列表覆盖服务端默认查询、DRAFT/SUBMITTED/APPROVED/REJECTED 单状态筛选、不透明 token 加载更多和显式刷新；
- 详情把当前 Version、latestReview decision/restoration、capability/scope 与 OAuth redirect 明确分区；运行声明只显示文本；
- 复用 UC002 的身份隔离、`SESSION_INVALID`、统一404、无效 token 从头刷新和仅内存 Query cache 规则。

非目标：

- Version 创建、编辑、提交、恢复、放弃草稿或发布槽位写操作；
- Reviewer snapshot、完整审核历史、当前 policy、confirmed checks 或 Reviewer 身份；
- 把 launch URL / OAuth redirect 变成可执行导航，或用 fixture 宣称真实管理链完成。

验证命令沿用 UC002，并要求 Gateway `latest` 显式包含 `ListApplicationVersions` 与 `GetApplicationVersion` 的 DEVELOPER surface route。

2026-10-15 实现结果：

- `@iwut/api-client` 已生成 Application Version 类型；list 正文严格为直接 query ProtoJSON，detail 无正文，两个 ID 均按独立 path segment 编码，`int64` 保持 `bigint`；
- Developer Console 已交付 Version 列表/详情、单状态 URL 筛选、显式游标翻页、无效 token 从头刷新、同 token 分页重试与共享 Session 失效回收；
- 当前 Version 与 latestReview 独立展示，覆盖恢复后 DRAFT + 最近 REJECTED 摘要；launch URL、capability、scope 与 OAuth redirect 都是不可点击的惰性纯文本，不执行预取或外部探测；
- Vitest 覆盖 direct query body、strict ProtoJSON、大 int64、四状态基础表达、筛选、坏 token 与详情隐私边界；Playwright 在真实浏览器 origin 上覆盖同源 list/detail、筛选、导航与不可执行 URL，但业务响应仍为类型化 fixture；
- Console `edge:e2e` 已显式确认 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` 包含两条 Version DEVELOPER route，并验证 BFF 不可用时失败关闭；同 digest 的 Gateway 协议 E2E 已通过真实 Auth/App/Mongo 和 BFF Cookie 身份交换，Version 两条路由包含在已验收的 16 条管理查询/本人退出路由中。

剩余验收是让浏览器页面直接连接同一套真实 Gateway/Auth/App 环境，使用真实管理员及四状态 Version 数据覆盖管理权变化、生命周期组合、no-store 与迟到响应；完成前不得把 fixture 浏览器测试表述为完整业务 E2E。

## 历史：UC-CONSOLE-004 首个实现工作包

当时状态：`IMPLEMENTED`（首包时真实浏览器联合验收仍待完成；后续已覆盖范围见上方当前表及对应工作包）。以下保留首包原始边界与结果。

首包实现固定 API 的 ProfileRevision List/Get 同源 client、资料列表/详情路由、单状态筛选、独立修订/审核历史 token、页级指针、latestReview 与原文纯文本表达。`null`、空字符串和有值必须分开，不执行 icon/正文/reason 内容。复用 UC002 的身份、错误、Session 和仅内存缓存规则。

非目标包括所有资料写操作、Reviewer queue/snapshot/decision、Admin Console、受控 icon 资产、外链代理、跨页冻结和持久缓存。验证命令沿用 UC002，并要求 Gateway `latest` 显式包含两个 ProfileRevision DEVELOPER surface route。

2026-10-16 实现结果：

- 生成并固定 ProfileRevision ProtoJSON 类型；两个同源 GET client 只发白名单 query、无正文，拒绝未知字段、畸形必需对象与非 `null | string` Value；
- Developer Console 提供资料列表/详情、单状态筛选、显式前后页、页级指针、当前内容、latestReview 和独立审核历史页；当前 token 进入仅内存 query key，身份、Application、筛选或修订变化即重置；
- 审核翻页返回的新完整详情整体替换旧页，不拼接跨时点 snapshot；原文保留空白并区分 null/空串，所有 URL 形字符串都是不可执行文本；
- Session 失效回收覆盖新增私有 query root；404、坏 token、413、5xx/网络均有独立恢复边界；UC002 详情中的资料入口已启用，所有写操作和 Reviewer/Admin 入口仍不存在；
- `generate:check`、strict typecheck、全量 Vitest、production build、Playwright 与 `git diff --check` 通过；Playwright 共 7 项通过、3 项按 Admin surface 跳过；
- `edge:e2e` 从 CNB 拉取 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，确认两个 ProfileRevision route 存在且 BFF 不可用时 fail closed。浏览器业务响应仍是 fixture，真实后端浏览器联合验收待补。

## 历史：UC-CONSOLE-005 首个实现工作包

当时状态：`IMPLEMENTED`（首包时真实浏览器联合验收仍待完成；后续已覆盖范围见上方当前表及对应工作包）。以下保留首包原始边界与结果。

首包实现固定 API 的 Tester Management Get 与两类 Search 同源 client、Developer Tester 路由、容量/当前链接 overview、固定 ACTIVE Membership 列表及 ACTIVE/REVOKED/ALL JoinLink 列表。三个区域各自维护 asOf/loading/error/refresh，两类 token 仅在当前身份、Application、查询种类和 filter 的内存上下文内使用。

非目标包括 REMOVED/ALL Membership UI、创建/轮换/撤销链接、移除 Tester、任何 join URL/secret/hash 恢复或复制、Auth 用户补查、本人 Tester 客户端入口、Admin Console、跨 RPC 原子 snapshot 和持久缓存。验证命令沿用 UC002，并要求 Gateway `latest` 显式包含三个 Tester Management DEVELOPER surface route。

2026-10-16 实现结果：

- 按固定 API 输入生成 Tester Management 类型与完整 enum/error reason，并实现一个 GET 和两个直接 Query body 的 POST 同源 client；Application ID 独立编码，所有方法支持取消，成功响应在 Proto 默认值生效前验证必需 envelope；
- 真实镜像联合验收纠正了首包的内容协商判断：App 实际依赖 Kratos v2.9.2，其 `application/json` codec 对 protobuf 消息已经使用 ProtoJSON；首包误根据缓存 v3 实现改用 `application/protojson`，真实镜像返回 400。现已修回 `Accept: application/json` 与正文 `Content-Type: application/json`，继续使用生成客户端的 camelCase、完整字符串 enum 和 RFC3339 Timestamp；
- Developer Console 交付 `/applications/{applicationId}/testers`，overview、ACTIVE Membership 和 JoinLink 三块使用独立 query key、loading/error/asOf/refresh 和分页状态；JoinLink 首次与重置均显式发送 ACTIVE，切换 ACTIVE/REVOKED/ALL 时只重置该列表 token；
- 容量以 overview 为权威，不从行数计算；Tester Auth ID、Membership ID 和 JoinLink ID 仅作不可点击的不透明文本，不进行 Auth enrichment，也不展示或拼接 URL、secret、hash、actor、复制、导出或写操作；
- 任一查询返回 401/统一 404 时取消并清除三块私有缓存；`SESSION_INVALID` 继续走共享 Session 回收；网络/5xx 的刷新失败保留并明确标记带 asOf 的旧快照；坏 token 只重置对应列表；
- `generate:check`、strict typecheck、全量 Vitest、production build与 Playwright 协议测试通过；浏览器测试核对两个 POST 无 URL query、body 不包 `query`、完整 enum 和 ProtoJSON headers，但业务响应仍为 fixture；
- `edge:e2e` 拉取 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，确认三条 Tester Management DEVELOPER route 存在且 BFF 不可用时均 fail closed。真实 Browser/BFF/Gateway/Auth/App 成功数据链仍待联合验收。

## 历史：UC-CONSOLE-001 首个实现工作包

当时状态：`IN_PROGRESS`。下列初始范围、未接线描述与旧API输入仅为首包历史；后续Session v2和真实验收见上方当前表，不从旧待办推导当前缺失。

代码范围：

- 根 workspace、严格 TypeScript、统一检查命令和固定 lockfile；
- `developer-console`、`admin-console` 的独立 Vite/Router/Query 应用入口；
- `developer-bff`、`admin-bff` 的独立 Hono 进程，以及共享但无产品授权逻辑的 `bff-auth` Cookie/Origin/Session 机制；两个 BFF 分别注入 Cookie 命名空间、密钥、Origin 与超时配置；
- 按 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 为两个 BFF 增加私有 Session ForwardAuth；普通 HTTP/JSON API 由共享 Traefik 经 BFF Cookie 交换后进入现有 Gateway ForwardAuth，登录、恢复与聚合仍经过 BFF；
- 初始固定统一 API `9f914c5` 的可复现 TypeScript 生成输入，以及原生 fetch/ProtoJSON runtime；当前代码输入已随 UC002 升级为 `a5d504c058c62cd91be451074d21608d69789918`；
- 共享浏览器设备密钥、签名协议、会话 DTO、错误映射和测试设施；
- UC001 的设备登录、邮箱登录、结果不确定恢复、Session 摘要与失效处理；
- Vitest/Testing Library/BFF 集成测试，并为真实 Playwright E2E 建立入口。

非目标：

- Developer/Application 管理和 Admin 审核业务页面；
- OAuth consent bridge、多账号管理、显式 Session/设备管理；
- 生产部署、生产邮件就绪声明和像素级视觉定稿；
- 用 MSW 或 fixture 代替 UC001 要求的最终真实 Auth/Gateway/邮件 E2E。

首个工作包验证命令：

```bash
pnpm install --frozen-lockfile
pnpm generate:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test
pnpm edge:e2e
```

真实服务 E2E 需要单独的受控环境与 Auth 邮件配置；本地浏览器测试未连接真实服务时必须明确跳过，不能报告为通过。

## 历史：2026-10-07 首个实现增量

`worktrees/iwut-console` 已交付工程与认证安全基线：两个独立 React/Vite 应用、两个独立 Hono BFF、共享且不包含产品授权逻辑的 BFF Session 封装、浏览器 P-256 设备密钥与协议校验、固定 `9f914c5` 的 Proto TypeScript 生成物、原生 fetch transport，以及单元/BFF/壳层浏览器测试。

本增量没有宣称 UC001 完成：登录按钮尚未接入 Begin/Complete 流程，BFF 尚未消费 Gateway 登录 RPC，结果不确定恢复、邮件收取和真实 Auth/Gateway/邮件 Playwright E2E 均待后续增量。Playwright 壳层测试拦截 `/api/session`，只能证明两个前端入口可运行，不能替代真实登录验收。

2026-10-07 接受 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)。两个 BFF 已提供同构的私有 `/internal/forward-auth`：无 Cookie 时不产生 Session，合法 Cookie 只返回一个 `x-iwut-session`，出现但无效的 Cookie 与来源不匹配均失败关闭。该 ForwardAuth 拒绝响应不直接设置或清除 Cookie；Cookie 清理由显式 BFF Session 路径拥有。Gateway route schema v3、两个 surface chain 及其真实 Traefik E2E 已通过。

## 历史：2026-10-08 共享 Edge composition 增量

Console 侧已增加共享 Traefik 的 BFF/SPA 动态配置生成器，并以固定 Traefik 镜像验证两份动态文件可合并装载、Session 与 SPA Router 按固定优先级命中、私有 ForwardAuth 不可公开访问、Gateway 链在 BFF 基础设施失败时保持失败关闭。BFF 登录/恢复调用 Gateway 的内部入口与真实 Auth/邮件 E2E 仍待 UC001 后续增量。

同日后续增量新增两个 surface 共用的设备/邮箱登录 BFF 编排：四条固定同源 Begin/Complete 路径通过生成的 ProtoJSON 类型调用非 Console Gateway origin，完全不转发浏览器 Cookie 或 Session；BFF 用独立、加密、HttpOnly 的短期 flow Cookie 将 Complete 绑定到 Begin，校验 Auth challenge/Session 形状，并只在确定成功后写入对应 Console Session Cookie。共享 Traefik 已为四条路径生成优先级 `40000` 的精确 Router。浏览器页面状态机、签名接线、结果不确定恢复及真实 Auth/邮件 E2E 尚未完成，因此 UC001 继续保持 `IN_PROGRESS`。

本机设备登录页面随后接入两个 Console：页面只读取不含私钥的 IndexedDB 凭据摘要，完整 challenge 的 protocol/purpose/service/application/operation/locator/expiry 全部通过后才要求凭据适配器签名；React state、Query cache 和表单均不接触 `CryptoKey`。目标 `AUTH_AUTHENTICATION_SERVICE_ID` 由 `VITE_AUTH_SERVICE_ID` 预配置，缺失或非法时入口失败关闭；成功响应更新安全 Session 投影与本机 credentialId。该组件测试使用 mock BFF，只验证浏览器分支，不能替代真实设备登录 E2E。邮箱页面和结果不确定恢复仍待实现。

邮箱页面增量随后接入：BFF 以默认关闭的 `EMAIL_LOGIN_ENABLED` 发布只读 capability；浏览器严格复现平台 ASCII 邮箱规范，在 Begin 前生成并持久化 non-extractable P-256 密钥，使用 8 位字符串验证码并核对邮箱协议十字段签名上下文。Begin 网络结果不确定时页面保留原 requestId、邮箱和同一 localId 进行幂等重试；Complete 结果不确定时可先用同一公钥 fingerprint 走设备登录探测，也可保留原验证码重试。Playwright 已在两个真实浏览器 origin 上覆盖 Web Crypto/IndexedDB、签名和 Session 投影，但 BFF/Auth/SMTP 均为拦截响应，不能代替真实邮件验收。服务端 `resendAfter` 冷却后的显式重发、迟到响应竞争与完整真实链路仍待实现，因此 UC001 保持 `IN_PROGRESS`。

## 实现登记原则

- 设计状态与实现状态分开维护；
- MSW 页面演示不等于 API、Gateway 或端到端交付；
- 每个工作包登记目标 UC/ADR、代码范围、非目标、验证命令和真实外部依赖；
- 两个应用分别记录构建、组件测试、BFF 测试和 Playwright 验收；
- 涉及浏览器认证协议时必须复用平台公开测试向量，并包含真实 Auth/Gateway 验证。

## 历史：2026-10-15 App 管理与审核页面设计草案

用户当时明确授权“同时起草只读管理和审核页面设计”。以下表格保留起草和早期分包阶段的登记；其中待真实验收、决定surface/正式定义/Reviewer公开指针缺失均不是当前状态。当前有界实现/验收范围与仍开放项以上方当前表及后续工作包为准，不以这张历史表重复生成待办：

| 草案 | 页面范围 | 实现前置与当前缺口 |
| --- | --- | --- |
| [UC-CONSOLE-002：查询我的 Application 管理概览](../use-cases/UC-CONSOLE-002-query-owned-applications.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-003：只读管理 Application Version](../use-cases/UC-CONSOLE-003-query-owned-application-versions.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-004：只读管理 Application 资料修订](../use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-005：只读查询 Application Tester 管理](../use-cases/UC-CONSOLE-005-query-application-tester-management.md) | `ACCEPTED / IMPLEMENTED` | 三块独立只读区域、隐私/恢复边界与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-006：审核 Application Version](../use-cases/UC-CONSOLE-006-review-application-versions.md) | `ACCEPTED / IN_PROGRESS` | [查询阶段](2026-10-16-admin-review-queries.md)开始；完整决定ADMIN surface、正式检查定义及真实验收仍开放；currentPolicy 版本和 ID 已有 |
| [UC-CONSOLE-007：审核 Application 公开资料](../use-cases/UC-CONSOLE-007-review-application-profiles.md) | `ACCEPTED / IN_PROGRESS` | 查询阶段开始；精确权限链和决定surface待验收；Reviewer 当前公开指针缺失仍阻塞APPROVE，不以读取交付替代完整用例 |

接入调查与分包见 [App API 接入计划](2026-10-15-app-api-integration-plan.md)。Console 页面的业务授权由相应 App/Auth UC 拥有；新提案仅规定前端编排、安全与恢复。Tester 本人 UC038/040 入口继续暂缓，未创建其 Console UC，未伪造宿主 runtime。

本次没有修改 Console 源码、App/Auth/Gateway/API 或生成 brief。正式检查定义、Reviewer 公开指针等后端缺口只记录交接方案；不得以 BFF 数据库读取、管理员查询或临时 DTO 绕过。设计接受前仅可做已授权工程核对，不将草案标记为已实现。最终页面验收仍需真实 Browser/BFF/Gateway/Auth/App，mock 不计真实 E2E。

[Admin审核决定接入](2026-10-16-admin-review-decisions.md)按已接受UC006–007与用户串行授权实施；精确API生成、正式定义/指针、决定UI、恢复与独立local-compatibility验证的分层证据见该记录。完整UC及默认published门禁继续IN_PROGRESS。
