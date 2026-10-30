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
