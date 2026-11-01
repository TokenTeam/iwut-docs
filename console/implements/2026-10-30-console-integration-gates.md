# Console 新管理能力集中验收

状态：`ORDINARY_VERIFIED / FIRST_FULL_REAL_FAILED / FIXES_IN_PROGRESS`，2026-10-30。用户要求集中必要验证、避免每次UI修改后跑整套；本页登记UC008–015这一批接入的整体验证，不代替各用例或历史门禁。下方普通轮次与首次冻结保留当时状态，真实终态见末章；当前不是仍在运行或等待首跑。

## 输入与范围

- Console原有UI/发布工作已保存为 `869e2f9` 与 `checkpoint/2026-10-30-console-workspace`；原 `legacy=e68851e` 保持不变。
- 新应用/版本/资料写入、测试/OAuth/Filter、归档/转让和Admin治理均按接受的UC实现；UC010拒绝后新建预填完成普通验证。UC016不在本轮61dd9b3冻结中，其后已独立实现并提交31d0e38，见[本人资料接入](2026-10-30-own-account-profile.md)，不混入本轮产品成功声明。
- 固定官方API为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。显式本地Gateway `9d6a27f / 90cf10f0…` 配合published Auth/App latest；默认发布runner仍保留pull策略，不编译相邻后端。
- 代表实链已分别通过[P0/P1两专项](2026-10-30-developer-management-writes.md)及[归档/交接专项](2026-10-30-application-ownership-writes.md)。Admin治理的独立真实链与最终无筛选门禁尚待运行，旧128绿结果不作为新源码的完整证明。

## 第一轮普通门禁

`pnpm generate:check` 与完整 `pnpm typecheck` 均exit0；官方生成器从固定远程API重新验证全部输入。仓库独立性与diff空白检查通过。文档brief72份、App注册表367行检查通过；这两个工具不机械检查Console注册表，Console链接/编号另行人工核对。

第一轮 `pnpm test` exit1。Node共385项通过，无skip/cancel；共享packages、双BFF已完成的子批次通过。Developer为548通过/2失败，Admin子进程因递归首错停止，不能当作完整Admin通过。

两条失败分别为：

1. 原 `versions.test.tsx` 要求“网络写入未接通”且无提交按钮，已不符合本轮接受的默认写入。修订保留URL/Scope惰性内容断言，改为已有DRAFT提供明确送审/放弃、打开不发送任何写请求，不靠删除测试隐藏行为变化。
2. UC010新的取消导航用例发现当前TanStack blocker取消后navigate Promise可能不resolve；仅在finally清理内存handoff会留下可被后续直接新建误领的预填。按接受的增量修复：正文只在短命内存，导航state仅携带无内容/身份的随机关联token；目标精确匹配Session/应用/token并在commit后消费，刷新或已消费token不能恢复正文。继续以StrictMode取消、普通新建与重新进入回归核对，不用timeout猜测导航已完成。

本轮类型与单测执行时UC010最后一条仍在收尾，因此不是最终冻结。修复后需完成相应组件批次及集中门禁，不能直接把上述exit1改记为成功。

## 收尾进展

UC010已完成49组件（新增预填10＋原编辑/读取39）、client7与Developer strict。最终实现不在click时暂存正文，而在blocker允许后的精确Router导航事件内stage，取消导航没有正文残留；目标commit后精确消费，StrictMode、取消后普通新建、后退/前进旧token均有回归。本文第一轮观察及原因保留，具体功能决定见UC010。

第二轮 `pnpm test` 的Developer为550通过/1失败，UC010已全绿；唯一失败是根代理新增“不发写请求”断言把侧栏正式POST `applications:search`错误计为命令。已按精确method/path仅豁免该正式读取，不允许任何其它POST/PUT/PATCH/DELETE；版本URL/Scope惰性及独立审核分区断言保留。修订后版本25/25通过。第二轮仍为exit1，不据此宣称完整默认test已通过。

完整 `pnpm build` 已exit0，双静态Web及所有共享/BFF包成功；Vite仍报告现有大于500kB的chunk体积提示，未调高阈值隐藏。本批新增全页管理代码暂未另行做路由拆包；功能验收与后续体积优化分别处理。

Admin治理实际页面spec及正式准备已落盘，待最终types/privacy与完整runner执行。P0 spec继续补入新草稿明确放弃的既有能力，保留原七次写入并增加创建/放弃两次，正式DELETE/If-Match/回执和列表读回均按契约断言；尚未执行该新增动作。恢复被拒绝版本仍未有本轮独立真实证据。

Edge配置验证还存在无条件pull的工具差异，正在复用同一本地镜像policy；默认latest门禁不变。此工具改动完成后集中执行最后普通门禁，再提交/运行全量。

## 最终普通门禁

收尾后的完整 `pnpm test` **exit0**：**1595项Vitest＋392项Node**，没有skip/cancel。包含Developer551、Admin234、API client459，原两类审核、私有读取/Session及本轮新命令均在同一默认普通入口通过。原两轮exit1保留，不以定向通过替换默认门禁。

最终完整 `pnpm typecheck` **exit0**，包括新增UC015正式fixture与P0放弃草稿spec；先前 `governance-write-fixture.ts` TS7022仅通过为循环中的previous显式标注bigint修正，没有更改业务准备。`test:real:privacy` **1/1、exit0**。官方 `generate:check`、完整build、独立性检查均通过；最后只有测试和工具收尾，没有再改已构建的产品源。

Edge工具收尾复用同一policy，32项CI/CLI回归通过并纳入上述392项。实际执行 `E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f E2E_GATEWAY_PULL=false pnpm edge:e2e` **exit0**，CLI来源为explicit-local-gateway，renderer确实使用immutable `90cf10f0…`；原双surface静态/私有边界、六审核读写隔离与伪造头拒绝均通过。这只是独立无上游的路由失败关闭门禁，不冒充成功业务链。

Console改动文档的26个文件相对链接全部存在；brief72份与App注册表367行门禁再次通过。Console注册表含UC016且Next017已人工核对。原legacy与checkpoint分支仍指向原提交。

## 提交与真实冻结

产品、生成物、runner与spec已本地提交为 Console **`61dd9b3`**（`:sparkles: feat: enable Console management workflows`）。这是待完整真实验收的候选，不冒称全量通过；没有push，legacy仍为e68851e。文档与源码跨仓分别提交，不把无关resource-hub纳入。

## 待完成

- UC015准备诊断、旧UI断言兼容和Developer会话隔离试验的有界实证，修正后再次完整真实回归。P0新增放弃草稿已在139312通过，不再列为全缺失。UC010预填已有组件证据，未凭原实链扩证。
- 记录修正后的候选与真实结果，不覆盖legacy，不自行push。无关 `resource-hub/` 工作不进入Console文档提交。

账号资料UC016、特殊凭据/BFF、正式IP部署、独立运维权限发现与Cookie传输边界仍是后续工作，不因这一批验收关闭完整goal。

## 首轮无筛选真实回归：139312

冻结 Console `61dd9b3` 后，使用 `node scripts/test-real-services.mjs`，没有 spec 参数，实际发现134项。显式设置 `VITE_VERSION_DRAFT_WRITES=true`、`E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f`、`E2E_GATEWAY_PULL=false`，Auth/App仍按默认重新拉取published latest。使用仓库外私有cached-pnpm PATH wrapper与私有运行日志；没有编译后端，没有关闭缓存、Session或隐私断言。

终态为 **78通过、16失败、40未执行，exit1，浏览器阶段17.4分钟**。单worker、retry0，没有主动skip；40项是beforeAll/serial前置失败后未执行，不能计为通过。失败后没有自动重启或重跑全套，也没有把普通门禁1595＋392绿替代真实结果。

实际固定 image ID为 Auth `518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16`、App `68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01`、Gateway `90cf10f0ea832812ee756e686362e0114d493e090b2286aef76dd9304007fdd7`，均带 `sha256:` 前缀。来源是 explicit-local-gateway，不是published Gateway的完整成功门禁。

静态构建、setup/driver打包完成后即记录产物；源码随后可继续编辑，当轮dist冻结到终态，结束时再次验证hash完全一致：

| 产物 | SHA256 |
| --- | --- |
| Developer `index-D_Jwc6Oi.js` | `31f0ad2b23e6f42b94dbfa0ed4ee11be1fd7a04aa6420038c10213286491fe37` |
| Admin `index-De1AfXr-.js` | `21ceb83792ca2400e0d31d6536b2a8fab83c0b8e84f65edd963bc7b91b487f1b` |

本轮明确再次通过P0应用/版本/资料写入及新增草稿放弃，共九次写入（12.1秒）；P1测试邀请/OAuth/Filter共十一次写入（22.9秒）；UC014归档/转让共十次写入（27.0秒）。原Admin私有视图、主要审核决定链、CSP、上下文耗尽恢复、Session/Mongo fencing及账号禁用恢复也有本轮成功项；只有实际完成的78项构成通过证据。

16条失败保留原结果与位置，分为：

- UC015专用治理fixture的prepare控制请求非200，页面操作尚未开始。原两层静态异常包装隐藏了内部阶段，单凭152毫秒或控制端500不足以判定是权限、正式接口还是fixture契约问题，不能将其写成已验证治理成功链。
- `console`的旧应用链接定位、`owned-application-pagination`的折叠技术摘要与旧标题；`lifecycle`、`qualification`的Version入口旧文本定位；`management-transfer`和`private-view`的旧应用纯文本定位。
- `review-decisions`中的owner资料视图，以及`tester`、`version`、`developer-withdrawal`读取矩阵，仍要求任何创建/编辑/发布等控件总数为0。这与本轮已接受的显式写入入口不一致，需改为不自动发送命令、不产生确认或一次性凭据、非DRAFT内容保持只读，不能直接删除保护。
- `developer-private-view`五项：首项的oldSeen实际断言失败，随后若干scope在beforeAll/driver登录级联失败。旧响应可见性与Session断言均须保留；是否与Rail和主列表的同路径读取/单请求gate命中有关尚待隔离实证，不归入已解释的selector错误。

后续兼容修订只发生在真实spec与专用fixture诊断：保留原HTTP响应、缓存、Session、私有持久化与业务写次数断言；POST `:search`仅作为正式读取豁免，不允许其他自动POST/PUT/PATCH/DELETE。UC015新增安全诊断只允许固定阶段、数值HTTP状态和白名单reason，拒绝额外字段；不返回原始响应、目标、凭据、URL或异常cause。修订后的真实专项尚未执行，不能改写本轮exit1。

本轮全部容器（含停止项）和network均清理为0，预览36959的五个容器继续运行；运行材料在仓库外，没有验证码、Session、私钥、加入URL或一次Secret进入文档。trace/截图/video关闭，失败报告继续使用 `./test` 隐私包装。UC016在静态冻结后属于另一批源码工作，不扩大139312的实际成功范围。

## 恢复后的四项诊断：35230

测试兼容、固定阶段诊断、显式筛选和UC016独立普通账号接线已提交为 `cbe165d`，没有push。启动前CI policy为41项Node＋6项Vitest通过，真实类型与隐私门禁exit0。默认无参数仍完整发现；本轮显式选择三个spec并使用title grep，只发现四项，不能当完整门禁。

使用与139312相同的Auth/App latest和显式本地Gateway，重新pull与inspect后确认image ID未变。终态 **2通过、2失败、exit1**，浏览器阶段27.7秒，无skip/retry：

- Developer旧owned 200在新身份建立后不可投影旧内容、不可清新Session，实际通过（5.0秒）。Rail在同document预热后主列表才接收gate，原oldSeen、Session、Cookie与零业务写断言保留；不由此推定其余401场景已通过。
- Admin普通用户本人资料五类型set及单字段remove、正式读回与Session保持通过（3.2秒）。没有Developer/治理授权或App请求。
- Developer本人资料失败在匿名页查找“使用邮箱登录”，尚未发资料命令。产品SessionBoundary仅提供返回首页链接，无法在账号路由就地登录；下一修订增加本页登录并保留路径，不把spec改为经App首页绕行。
- UC015准备在 `operator-state-read` 收到404，诊断reason为HTTP_ERROR，没有页面治理操作。检查发现隔离runner漏开 `AUTH_PLATFORM_ADMIN_ENDPOINTS_ENABLED`，并同时缺少后续运维授权与App运维的两个显式开关；这三项配置已修订待复验，不归咎Gateway缺路由，也不预称真实治理成功。

当轮静态字节保持到终态：Developer `index-8CjIfp2Y.js` SHA256 `455fa73517ad72d0df147d96a5c0faeb96e03ba8b0d9cb3bfa07aa44e1a2ffc3`；Admin `index-xR2iIKAh.js` SHA256 `76e2427002221b7d1ef58b128ee479c3877e65003554385dd415bfc014a1ce7e`。35230全部容器（含停止项）与network已清理为0。恢复时原预览容器已不在运行，本轮没有重建或删除其私有持久目录；不能沿用139312时“预览仍运行”的历史描述。

后续修订 `5cbd03d` 补齐三个端点开关，并让其余初始401在同document预热真实Rail后经SPA导航进入目标；Version列表用现有两请求batch暂扣其额外Application GET，Tester仍用原三请求batch。详情先真实打开列表，均保留Session/oldSeen/零业务写与零DELETE，新增document marker证明没有hard reload；真实types通过，不扩proxy能力。产品 `a9bee4b` 修复本人资料登录，79项集中组件与Developer strict通过。下一验证选择完整Developer隔离文件25项＋治理1项＋双端资料2项，不是全仓完整门禁。

## 三文件完整专项：51965

冻结 `a9bee4b`，显式选择上述三个完整spec，实际发现28项，retry0。终态 **6通过、6失败、16未执行、exit1**，浏览器阶段1.2分钟。Auth/App重新pull latest后仍为518b0917/68ee32b1，Gateway显式本地90cf10f0。不是全仓门禁，也不把16项前置失败后的未执行计作成功。

双端本人资料五类型set/remove全部通过（各3.0秒），从匿名直接访问实际账号页，正式EMAIL建立Session，不经过App首页；正式读回、未涉及字段保持、原Session、零App请求均验证。Application组的旧owned200/401、旧application200/401均通过（5.6/5.3/5.2/5.3秒）。这些是新增实证，不推定Version/Profile/Tester组通过。

首个隔离失败位于旧owned DELETE204的同document再次进入：旧spec仍点击品牌“返回开发者工作台”并等待Session读取；品牌现已按用户结构要求指向 `/applications`，在owned路径上是同路由无动作。随后worker重建导致若干组EMAIL准备失败，不能视为这些组的产品隔离结论。修订 `5d48798` 使用实际Rail“创建新应用”空页面进入，必须收到真实GET `/api/session` 的完整B会话，再经平台应用栏目进入非空B列表；document marker、oldSeen、旧204及零业务写断言保持。

治理已越过原404准备阶段，但在等待页面响应时超时，原隐私包装仅定位到共用observe行，尚不足以确定哪个动作或原因。`5d48798` 仅增加固定枚举阶段与固定RPC名称/写次数诊断，不输出目标、URL、正文或原因材料；不据此声明后端写成功，也不自动重放未知写入。下一轮有界诊断聚焦此场景及旧清理/剩余401的顺序。

静态冻结至终态一致：Developer `index-DHUbemp8.js` SHA256 `94cfdb81363ffb74a2d1610d8e48ede4a7d42f4a936a3a43762696a64d4fc986`；Admin `index-xR2iIKAh.js` SHA256 `76e2427002221b7d1ef58b128ee479c3877e65003554385dd415bfc014a1ce7e`。51965全部容器（含停止项）与network清理为0；未启动或修改原持久预览数据。

## 顺序诊断：95759

冻结 `5d48798`，显式两个spec＋title筛选，发现7项，终态 **1通过、5失败、1未执行，exit1**，浏览器阶段1.5分钟，retry0。旧owned DELETE204同document非空B页面实际通过（6.8秒）；前轮品牌同路径无动作的测试准备问题得到这条实证，原Session、marker、oldSeen和写入保护保留。

治理固定诊断明确为 `administrator-list` 等待，实际仅观测 `get-admin,list-admin`，写次数0；没有发生页面治理命令。修订让明确刷新前先等待初次名单数据真正显示，避免刷新合并初始请求的观察竞态；仍需真实复验，不以源码推断替代运行结论。

Version401失败在 `arm-initial-old-read`：底层支持2–3条，但控制入口仍只验证完整Tester三条，新的Version两条请求在控制校验就被400拒绝，尚未暂扣任何请求。`ccaf196` 只为固定A的Version列表POST＋Application GET增加完整组合分派；原Tester规则不变，不开放任意双请求/目标或修改底层proxy。新增正负例后17项Node fixture、real types和diff通过。其余组前置失败及未执行不算产品结论；下一轮才验证这些修订。

本轮Auth/App/Gateway固定ID和两个静态hash与51965相同，终态再次核对无字节变化。全部95759容器（含停止项）与network清理为0。UC017后来新增源码不属于本轮：其普通检查和真实Mongo证据独立记录，不能挪作本轮通过结果。

## 四文件专项：119394

冻结 `5a6e723`，四个完整spec、无title筛选，实际30项；终态 **28通过、2失败、exit1**，浏览器阶段6.7分钟，retry0、没有skip或未执行项。Auth/App重新pull latest仍为518b0917/68ee32b1，Gateway显式本地90cf10f0。默认完整无参数门禁仍待，不用本轮专项代替。

双端UC017真实退出均通过（各1.1分钟，包含真实邮件冷却）：固定Node闭包在原Auth token撤销前GET200、原正式DELETE一次、撤销后GET401/SESSION_INVALID；同时只读Mongo核对同一EMAIL Session行已撤销、peer及两设备凭据有效。浏览器仅发送原binding/generation，当前Console变为SIGNED_OUT，另一origin原Session与在线读取保持。两端原不可导出钥匙/指纹保持，没有自动DEVICE；用户明确返回再选本机凭据后，同credential建立不同generation且原peer不变。浏览器无App/Auth直连命令、`DELETE /api/session`、token header或外域请求；退出写经专用BFF完成。此两条证明正常退出代表链，不扩为所有失败与迟到矩阵。

UC016两端五类型set/remove再次通过（3.4/3.5秒）。Developer隔离25项中24通过：Application六项、Version六项、Profile六项及Tester旧200/401六项全部通过；原Session/Cookie、oldSeen、非空B、document marker与零业务写保护保留。

两条失败均保留：治理在App Suspend ACK及随后GET完成后，spec159的全资源JSON相等断言失败；此前已完成14条Auth治理命令及其读回，实际页面请求写15次，尚未执行App Restore。当前只有差异存在的证据，后续增加只输出固定字段名/时间相等布尔的诊断，不提前归因镜像。Tester旧overview DELETE204在clear回执HELD后，absent辅助函数对已卸载的区域调用单节点evaluate并超时；修订为evaluateAll，空区域自然表示无旧内容，原exact-text和oldSeen断言均保留。该修订尚待实链复验，不写成当前轮通过。

当轮静态hash保持到终态：Developer `index-BN-ovSVj.js` SHA256 `aeaf719980d0211c55583703de16b0a99dbd0ac71af17f042b8795dc1081af11`；Admin `index-WOdw1UdI.js` SHA256 `ce20163411847382cee89a3b5ae6ef071385775d82ba129083da193ab6f5681e`。全部119394容器（含停止项）和network清理为0，未改原预览私有数据。

## 新 App 镜像后的专项412805

2026-11-01 用户反馈 App 已 push，重新拉取 `latest`，实际 App image ID 更新为 `sha256:18eacd03c1f0cd9b4841bd9b141b61c0d5dde89f6d0045f00322a056541b4027`；Auth 仍为 `518b0917…`，Gateway 显式本地 `90cf10f0…`。Console 冻结 `d5cc071ad72bd71a5e2588bad7e91ccd7c0e182d`，三份完整 spec：治理、Developer 隔离、版本写入/审核/发布，没有 title 筛选。

首轮409215因私有包装继承 umask0077，使容器挂载文件实际0600，Auth/App startup失败，浏览器未开始，exit1。合成Node文件验证后，仅修私有包装的子进程umask0022；日志仍私有，候选源码未改。该轮资源已清理，不计为业务场景发现或通过。

412805 实际发现27项，终态 **12通过、4失败、11未执行，exit1，2.6分钟**，retry0，没有主动skip。两条新增代表业务链均通过：

- UC015治理 **26.6秒**：真实React完成14条Auth治理命令及App暂停/恢复，共16条，专用读回和双App修订通过。App ACK/GET全资源严格比较通过，确认 [已交接时间差异](2026-10-30-app-operation-time-readback-gap.md) 在新发布镜像上修复，没有增加毫秒容差。
- UC008版本闭环 **30.8秒**：保留原九次前缀，完成真实Reviewer拒绝、owner恢复/保存/再送审、Version与Profile批准、首次TEST发布与读回。精确13次owner＋3次Reviewer命令、历史审核/快照、Session/设备与零自动登录/clear/外域断言通过，详见 [本包](2026-10-30-version-review-publication-loop.md)。

Developer隔离10项通过。首个失败为Version列表旧DELETE204，在`unchanged-B-document`阶段完整main投影严格相等断言失败；此前实际业务/Session/clear/navigation额外流量均为0。其后三项失败在worker重启后的group EMAIL准备，另11项未执行，不当作已通过或已确认产品故障。源代码检查发现B列表读取完成不代表独立PublicationPanel摘要已完成，现为enterB追加该正式GET及成功内容等待，再开始原完整main比较和零额外流量窗口；没有删除完整投影、document marker、oldSeen、Cookie或原Session断言。修订待新候选实测，不将推测当终态。

双静态hash与119394完全相同，wrapper记录源码指纹和静态hash到终态均未变。全部409215/412805容器（含停止项）与network已清理为0，原私有预览数据未动，legacy保持。集中前置CI policy48 Node＋21 Vitest、real types通过；不以此代替完整普通或无参数真实门禁。

同时有限核对UC008发现送审/恢复仅重读Version而遗漏管理摘要，已按既有UC接受修正并待本轮终态后实施。放弃后由列表及PublicationPanel读取，真实spec将补该摘要证据。下一候选合并该实现与独立摘要等待后，集中执行必要前置和完整无参数真实回归，不重复已终态进程或覆盖失败记录。未push。

## 摘要读回修正与完整复验候选

候选 Console `e7cdabb34a893ba7e00c9a47e642493d71f58225` 已本地提交：送审/恢复后的Version＋Application摘要同边界读回、错误与迟到保护、真实闭环的四个摘要GET证据，以及隔离B页面对既有PublicationPanel正式GET/成功渲染的等待。完整页面投影与零额外流量断言保留。

必要前置最终组件15/15、Developer strict、real types、隐私1/1通过。无参数真实轮次422340已启动，默认完整发现与终态待补；本段不是全绿声明。普通完整单测/工作区strict同时集中运行，不改dist或正在冻结的业务源码。来源仍是发布Auth/App latest＋显式本地Gateway，不写成发布Gateway全链成功。

### 422340 主动中止与已确认的设置读取副作用

集中工作区 strict 已通过。完整普通 `pnpm test` exit1：Node411项通过；Developer564通过/1失败，Admin递归未完整执行，不能记为全部普通通过。失败是已有 `application-settings.test.tsx` 的“迟到显式读取不覆盖替换Query”用例，新实例的synthetic sentinel变为undefined。单独现有文件9/9通过未覆盖该全量失败。

仓库外可控顺序实验确认了产品原因，排除了正常GC：replacement始终有observer，gcTime300000。旧显式读GET挂起后替换Query；旧返回revision5虽被setData的对象/data身份检查拒绝，但 `useSettingsResource.refresh` 先执行remember，仍将共享下界从4抬到5；replacement observer的正常GET4随后被拒绝，projection清除数据。实验1/1确认当前缺陷，不记为修复测试通过。

根据既有UC014安全读取职责接受修正：显式读取在处理成功或错误、提升下界和改写本地状态前，必须核对捕获的Query实例与原data身份；过期结果完全不消费，不让旧成功/失败干扰替换实例。保留正常ACK下界与同Query更新保护，增加控制返回先后的回归。此项不改变后端契约、业务修订规则或缓存容量。

发现确定产品缺陷后，主动SIGTERM中止旧候选422340，浏览器已发现138项但未完成；观察到14条完成通过，正在执行的一项在停止过程中被中断，后续没有完整终态报告，不将其计为业务断言失败/成功或全量完成。wrapper exit1，源码指纹与静态产物保持；Developer `index-CTguEGFF.js` SHA256 `8993614e01548bc24680134a774afe589a4278adc0b8da521c2c9c3a175ec084`，Admin沿用119394 hash。全部owned容器（含停止项）和network已清理为0。

该中止用于修复已确认的候选问题，不借重复重跑掩盖失败。修复后集中普通门禁和新的无参数真实门禁另记，legacy不变、未push。

### 设置读取修正

已将身份核对提前到 `remember`、缓存和readError消费之前；过期错误在进入runtime共享attempt拒绝处理前转换为AbortError，防旧403先让新视图退场。当前有效403仍保留原拒绝处理，正常命令ACK下界不变。同步busy锁保证同一显式操作结束前不重入，finally仅释放自己的reading。

新增确定顺序回归：旧显式GET5先返回仍不得提升replacement的下界，随后replacement实际GET4可以成功，保持同一新实例与observer、零写入；对替换实例和同实例较新data分别验证旧503/403无副作用，并保留当前有效403退场。设置、转让、配置三文件最终 **59/59**、Developer strict、diff检查通过，没有靠移除断言或改变服务限额修复。完整ordinary与工作区strict集中重跑，终态另补；未build或改写已中止轮次的输入。

修复已本地提交 `92d35164b30fd28e6ee2426e62813922ad272fa5`。集中最终 `pnpm test` **exit0，1899项Vitest＋411项Node**，`pnpm typecheck` **exit0**；之前完整普通exit1仍保留。新候选已启动无参数真实门禁，等待实际完整终态，未宣称138项全部通过。未push。

## 439913 无参数回归：外部143中断

冻结 `92d3516`、Auth/App重新pull latest为518b0917/18eacd03、显式本地Gateway90cf10f0，无spec/title筛选，实际发现138项。运行末段被外部以143终止，runner和Playwright均已退出，没有最终Playwright汇总；不能记录为完整通过或正常完成。

停止前可逐项核验 **130通过、3失败、2项因serial前置失败未执行**；最后3项没有完成证据。双端本人资料/退出、全部25项Developer跨代隔离、新版版本恢复与审核/TEST发布及四次摘要GET、UC015治理与App严格时间读回、P1和UC014写链、Scope真实变化/审核决定、正式关闭与WITHDRAWN历史读取均有该轮完成的通过项。不能把已完成项扩大到最后3项账号状态场景。

3项失败的精确边界如下：

| 场景 | 失败处与已知事实 | 后续核对 |
| --- | --- | --- |
| management-transfer | `source-list-after-transfer`，spec157全page旧名count0；主列表实际空读回及空态此前均通过，六详情退场已完成 | 主列表与持续Rail是独立默认范围/读取时间；按已有入口明确刷新Rail，再保留全page无旧名断言，不假造跨document失权广播 |
| private-view旧200 | spec70 sticky `oldSeen`；B身份及正式空列表均已通过 | observer在B建立前安装，任意mutation扫描body可能匹配合法旧Rail静态文本；应区分新插入/变更A内容与既存A，B采用后仍全body禁止A，不简单缩main |
| qualification角色版本页 | `governor-production-hidden-versions`，spec202在DevTools response.json失败，尚未到隐藏内容/UI断言 | Version查询与PublicationPanel独立App GET共享拒绝边界，先完成的404可取消同级正文；保留两实际HTTP404/缓存头及首个完整响应reason/minimal，原native各RPC负例不变 |

这三项的脱敏artifact均无私有DOM/ARIA/HTML；只有固定源代码框，不能据此宣称已直接观察到某个Rail节点或新的后端故障。文档依据为页面结构中Rail独立范围/读取时间，以及UC002按当次投影读取的规则；未要求主列表刷新所有组件。已接受最小测试适配，不为旧测试前提新增全页刷新协议、削弱wholepage/Session/zero-clear保护或改后端。

外部终止后逐一核对owned标签，清理5个残留容器（含停止项）、独立network及该轮临时运行目录，其他容器未动。外部终态记录核对HEAD保持92d3516、tracked diff为空，双静态SHA256保持：Developer `index-DJBQLy6e.js` 为 `5e4886d0ca58cc66a29634461b9bba19b4c5fc5c339e3b33a205545690bb65fa`，Admin继续 `ce201634…`。原wrapper未能生成正常terminal文件，明确保留外部143而非补写正常退出。

后续私有运行包装预存源码指纹，长轮次采用独立session的后台monitor并持续写终态材料，避免依赖单次工具会话一直存活；不改变仓库默认runner、镜像策略或业务超时。下一候选先集中复验上述3项相关完整spec及末段未完成的账号状态，不静默重新运行已终态进程；完整门禁仍未关闭。Goal依用户恢复为active，继续推进，未push。

### 有界适配候选 e6566d7

三份真实spec的最小适配已提交 `e6566d734ea84e317135d9a0a9c72a9ba9d196ed`，没有更改产品源码或后端：

- 转让后的源列表依原交互分别刷新主列表和Rail，Rail请求严格为默认pageSize20、正式空读回；保留全page旧名0、原六详情退场、两Session和零clear/业务写断言。
- 旧响应观察在B权威确认后、释放旧响应前启动，既存合法A Text节点只作为内存WeakSet基线。新增/变更A文本立即记为复活；包括同task插入后删除、字符A→空，不靠最终paint推定从未出现。B身份首次可见即检查整body并进入持续全body模式，最终wholepage无A和原sticky seen保护均保留，没有缩到main或访问产品缓存。直接AST提取当前install函数的仓库外jsdom检查7/7通过，覆盖静态/移除基线不误报、瞬时插入与adopt前后边界，日志仅布尔和计数。
- 角色版本页预挂两个精确HTTP响应，各自严格404/private/no-store；仅对首个requestfinished完成的响应解码并继续原reason/minimal断言。原native各RPC、UI退场、角色/Session/设备和零补查/写入保护保留，不对取消的兄弟正文伪造结果或吞掉状态错误。

集中real types、隐私1/1和diff检查通过。已启动四份完整spec：management-transfer、private-view、qualification-read-matrix及zz-account-status，暂无实际终态；这是专项，不替代138项无参数门禁。使用独立后台monitor，源码指纹已预存，Auth/App仍重新pull latest、Gateway显式本地；不因上轮143固定旧镜像或修改业务超时。Goal保持active，无新后端改动要求、未push。

### 四文件465078及旧clear导航的后续诊断

465078正常终态 **11项中10通过/1失败，exit1，3.0分钟，无skip/retry**；源码指纹和双静态hash到终态不变，全部owned容器/network清理为0。原439913的三项失败均在这轮通过：管理转让的独立Rail正式刷新及全page旧名0、旧200响应与B隔离、角色版本页两HTTP404与首个完整拒绝。角色四场景、账号DISABLE/RESTORE/两端原钥匙明确DEVICE恢复三场景也全部完成，补上了439913末段的缺证据。

唯一失败是此前因private-view serial前置失败未执行的旧clear第三项，固定阶段entry-read：旧“返回开发者工作台”链接仍指向相同applications路由，没有触发新的Session读取。沿已在25项矩阵证明的方案，改用同document的真实空创建页读取B，不填/提交表单，先等待其独立Rail正式空读取，再转主列表；原document marker/held204/零额外流量不变。提交8344af8后，473794三项诊断2通过/1失败，exit1、33.2秒：新Session和Rail读回已过，失败推进至B-view，因为私有创建页按现有UI不显示entry页的raw authId标签。

后续e24b98d只修这条测试的采用前提：entry分支继续原可见身份断言；空创建页分支使用已经精确核对的B Session和按B代读取的Rail，再核对实际空创建表单/路径后执行全body observer adopt；不要求产品额外展示内部ID。原Session/旧响应/全page无A/零clear、业务写及同document断言保留。real types通过，已启动该旧clear单项实链，终态待补。上述两次exit1均保留，不将导航前提失败当作已确认后端或产品fencing故障。

480853已正常终态 **1/1通过，exit0，9.1秒浏览器阶段（场景6.5秒），无skip/retry**。同document空创建页读取B、独立Rail空读回、再入B列表、旧clear204释放与零额外读取/clear/navigation、原Session/Cookie和钥匙保护均执行通过。源码指纹和静态hash保持，owned容器/network清理为0。这补齐该旧clear的有界证据，不拼接成同一候选138项完整通过。

## UC018集成候选

新增已接受的本人Developer自助资格由隔离分支实现并以1e9e6af集成，f3c690b记录检查点，见[实施证据](2026-11-01-developer-application.md)。完整普通2031 Vitest＋411 Node、full strict/隐私通过；默认真实发现将增加一个未Apply普通用户的自助开通→同Session创建链。当前冻结f3c690b进行该新链与完整private-view三项的联合专项，终态未有；旧失败、中断和已通过边界均保留，Goal保持active。

497011联合专项已正常 **4/4通过，exit0，24.2秒，无skip/retry**；新普通用户首次Apply→同Session创建代表链4.6秒、private-view三项5.2/5.7/6.2秒。源码指纹/静态hash保持，owned资源清空，完整输入及首次用户边界见UC018实施记录，不把它与旧130项拼成无参数全绿。随后冻结1326562（仅工作检查点）启动新的无参数完整门禁；使用后台monitor及预存源码指纹，Auth/App继续latest，无新后端编译或配置放宽。实际发现数及终态待记录，Goal保持active。

503436已terminal exit1，源码指纹保持；在DockerHub拉取固定Mongo镜像时referrers请求EOF，未到构建/静态ready或浏览器发现阶段。随后直接重拉mongo8.2.12在manifest HEAD同样EOF。正常terminal材料已保留，0 owned容器/network；staticUnchanged=false表示没有ready基准，不记为产物漂移。没有静默重启进程或将本轮记作业务测试失败。

当前正实现[基础设施显式缓存模式](2026-10-30-local-gateway-runner.md#2026-11-01基础镜像的显式缓存模式)，只对已inspect核对的不可变Mongo/Traefik生效，默认pull、Auth/App latest和Gateway原规则保持。完成相应Node门禁后再冻结新候选重启完整回归，记录实际来源；Goal仍active。

87901b4已实现显式基础设施模式，CI policy57 Node＋21 Vitest通过。已冻结该候选重新启动无参数完整轮次，基础设施来源明确为explicit-cached-infrastructure，Mongo/Traefik分别强制inspect既有e0ce8c35/24841fe2，Gateway仍显式local90cf10f0；Auth/App继续pull latest并核对实际ID。此轮不是默认全发布来源，也没有以pull失败自动改旧后端。实际发现数、源码/产物冻结和终态待补；不要重启仍live的后台runner。Goal保持active，未push。
