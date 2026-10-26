# UC006：Version批准的真实Auth依赖不可用与恢复

状态：`ACCEPTED / IN_PROGRESS`，2026-10-23，按用户持续授权自行接受。承接[决定跨Session边界](2026-10-23-review-decision-session-boundaries.md)，本包只补UC006的一项依赖故障联合验收；前c60dd59的113项全量已终态109通过/4缓存头失败后才开始本包，未改其运行期冻结源码。

## 权威与范围

引用[UC006 BR-CRV-003/004及验收4](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-003)、[UC-APP-005流程及BR-REV-018](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md#br-rev-018)。APPROVE外部资格检查不可用不是已暂停事实，不得推导系统REJECTED；App的状态一致性仍由后端拥有。前端按稳定reason表达且保持RESULT_UNCERTAIN，明确读原Review，不自动重放或改发REJECT。

不包含策略发布/退休、Scope启停、Profile外部依赖或治理UI。当前固定API没有正式策略发布/退休及Scope启停命令，已有准备的Version scopes为空；提交错误expectedPolicyVersion或合成JSON不能当真实策略/Scope变化。Profile决定不调用这些Auth批准检查，不能机械复制成本包第二项证明。以上缺口继续OPEN。

## 复用资源与实际场景

在现有决定25项之后追加一项，预期专项26项、默认114项，以实际终态为准。复用既有独立Version Reviewer的peer/peerDriver及`resources[3].versions[1]`；此前只做跨能力403，须正式GET确认仍PENDING、eligible、策略定义完整，再捕获Review/Version revision、snapshot和Session/钥匙。不能增加账号、App、quota、登录、seed或业务准备写入。main失效fault不影响peer；若前置事实不满足就明确失败，不寻找新目标或补决定。

1. peer真实加载原Review，主动确认四项并进入提交预览；原profileOnly context可保持另一能力已加载非空视图，不能假称Version-only actor拥有Profile权限。
2. 只切断App→Auth内部gRPC传输；Gateway→Auth保持原直连，Auth、App、Mongo仍运行。禁止停整个Auth或用HTTP代理伪造预期503/业务JSON。
3. 唯一明确APPROVE得到真实App响应，期望HTTP503和固定API的`ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE`，并保留private/no-store断言。若镜像实际映射不同，记录真实差异，不能注入预期reason或放宽为任意5xx。有限代理只证明通道断链事实，业务reason必须来自真实App。
4. 页面明确RESULT_UNCERTAIN并聚焦，显示允许的稳定reason，不宣布成功或确定未提交；清确认、隐藏重复提交，无自动决定/详情重读/Session DELETE，当前Session/设备钥匙与另一能力保持。
5. 恢复传输后由用户明确重读同Review，正式GET确认PENDING/null decision、原Version revision/snapshot保持，四项未确认且不能直接再次提交。提示PENDING不证明原请求未在途、如再提交须重新评审确认。本包到此停止，不补第二决定、不以清理为由消费该PENDING。

## 最小产品修订

现有5xx通用RESULT_UNCERTAIN没有稳定reason。对ApiError的5xx仅追加既有safeReason白名单输出（否则HTTP状态），不呈现任意message/detail、URL或原始JSON，不修改Session或能力权限。两能力合成回归验证503及非法reason的安全降级、焦点与不重放；真实依赖业务证据只有上述Version一项，不能把组件Profile分支计为实际Profile依赖失败。

## 固定传输控制

需新增有限TCP透明转发器，正常模式原样pipe并处理背压；不解析/存储/记录gRPC、JWS、正文或认证材料。目标仅runner创建的Auth gRPC loopback映射，App使用该固定代理，Gateway仍直连原Auth容器。主机监听如为容器可达而绑定0.0.0.0，必须无HTTP管理面、固定上游、限制连接并在本轮finally精确关闭，不能成为任意target代理。Auth新增随机loopback发布只属隔离测试准备，不改部署配置。

每轮最多一次断链及其恢复，固定状态NORMAL→DISCONNECTED→RESTORED；断链关闭已有连接并拒绝新连接，恢复只接纳随后重连，不缓存/重放字节。观察只返回状态、有限计数（当前连接/已切断/被拒绝），不回传请求内容或地址。必须证明实际有既存连接被切断或新连接被拒绝，不能仅凭控制返回成功声称App外呼失败。

控制仅loopback bearer、精确固定method/path、无query/application-json空对象，不接收host/port/subject/Session/DB/URL/permission。未ready、并发、重复断链或非法相位失败关闭；finally恢复/关闭只处理原轮次，不重发业务请求。控制未知结果先观察固定状态，不能盲目重放命令。Auth/Gateway功能与资格/权限事实不改变，此故障不证明Auth内部数据库故障或正式治理命令。

## 交付与门禁

先用产品组件回归证明reason缺口RED→GREEN；TCP转发/限额/固定控制也先红后绿，覆盖正常字节、既存连接关闭、新连接拒绝、恢复新连接、背压/异常/关闭、边界和静态错误。严禁将TCP控制单测当真实依赖业务证据。

当前113项全量终态收齐后才允许实现本包；实现后统一测试、strict、官方固定pin生成/Edge检查并冻结，再每轮pull published latest跑26专项及114无参数全量。前包四条Gateway Session401及25条既有Application缓存头失败全部保留，不编译后端、不用本地compat、不push红门禁。完整UC006/007及其余角色/策略/Scope/并发和UC001/fencing继续开放。

## 已实现接线与冻结前检查

产品新增两cap×合法/非法reason四项组件回归，先4失败/原89通过，修复后93/93。5xx仅追加既有safeReason输出，非法reason退回HTTP_503、不呈现原message，RESULT_UNCERTAIN/焦点/明确同Review重读/清确认及Session与其它能力保持。不是新增Profile依赖业务证明。

纯TCP代理10项＋固定控制最初15项先25 RED，再25 GREEN；追加事后确认读失败回归后共26/26。固定loopback上游、listener host白名单、32连接、计数饱和2147483647、原样pipe背压/双端错误清理、正常/断链/恢复与未知变更冻结均覆盖。CLOSED仅finally资源关闭后的清理终态，不能恢复或第二次断链；observe返回四个有限公开字段，不含认证材料/地址/正文。

Runner仅为Auth gRPC新增随机loopback发布和固定TCP relay；App连接指向relay，Gateway继续原Auth容器直连。控制与原ready共享已正式准备的reviewDecisionFixture，loopback bearer/空JSON边界接入真实spec；finally只关闭本轮relay，断链时先直接恢复资源，不重发业务命令。

新增一项spec在原25之后复用peer及原PENDING，确认真实503/reason、有效断链计数、只有一个决定POST；原profileOnly队列在断链期间仍可经真实Gateway/Auth明确刷新。生产bound fetch的正常post-response Session校验允许一次，不等于自动详情重读；用户明确重读后累计两次校验/一个详情GET。断链/恢复未知回执先observe、不重放，finally不能靠补决定消费PENDING。

统一954 Vitest＋221 Node、strict/真实spec类型、官方同pin生成、Edge、Node语法/diff检查通过。尚未取得本包published26项专项或114项全量结果，不能把前包25/113或新合成测试作为本次真实依赖故障证据。接下来冻结产品/runtime/runner/spec运行，每轮重新pull latest、原29缓存头失败断言保持。

## published专项终态

冻结Console `09f7805`，轮次`iwut-console-real-155670`，26项全部执行、无skip/retry：25通过/1失败（2.9分钟、exit1）。全部26项body功能断言完成；最后一项被afterAll原4条Gateway Session401缺private的soft失败标红，安全坐标均`review-decisions.real.spec.ts:40:143`，无新功能失败。原25项在正常TCP转发路径再次通过，本包新增依赖场景用时3.8秒。

真实App在固定App→Auth断链后返回HTTP503及`ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE`，响应private/no-store均存在；不是代理业务JSON。实际断开的既存/拒绝的新连接计数大于零；Gateway→Auth仍直连，profileOnly经真实链路明确刷新非空队列成功。Version页面展示稳定reason且RESULT_UNCERTAIN聚焦，无自动决定/详情读取/Session DELETE；一次post-response Session校验按原路径完成，Session/carrier/钥匙与另一能力保持。

恢复仅切换relay接纳新连接，再由用户明确GET同Review：PENDING/null decision、Version原revision/SUBMITTED、完整Review与snapshot未变，四检查未确认、必须重新评审。自提交前开始的页面观测窗口累计决定POST1/恢复详情GET1/Session校验2/DELETE0；初始详情加载与独立driver的权威Session读不混入该窗口，无补第二决定。此终态读取证明业务未变化，不冒称再次批准或Auth内部数据库故障；恢复新TCP字节由单测分层证明，不把控制RESTORED本身当新批准成功。

本轮30个实际决定响应仅原4个Gateway Session401缺private，其余26个200/403/409/新503全部private/no-store为真。原4失败保持，前包Application25条仍须默认全量重验，不能从专项宣称消除。

每轮pull published latest，本轮Auth/App/Gateway/Mongo/Traefik五解析ID均与前c60dd59轮一致，API固定pin不变，strict/报告隐私和runner构建前置通过。专项容器/网络已检查为空，未编译后端或push；已在同一09f7805冻结启动默认无参数114项全量，当前尚无其终态，不以专项功能收齐标绿完整UC/门禁。下文或上文“尚无专项结果”为先前阶段记录。

## 同冻结无参数全量终态

冻结`09f7805b096eceac27f288327abf67a92c5005b5`，轮次`iwut-console-real-162274`，114项全部执行、无skip/retry：110通过/4失败（19.5分钟、exit1）。26项决定body功能断言再次完成，新增真实依赖故障用时3.6秒；其后Tester/真实UI恢复/Version分页等场景亦完成，正常TCP转发和恢复未造成新增功能失败。不能据此扩大为未列明Auth内部故障或完整UC。

全部29个失败安全坐标逐项核对，仅为原缓存头断言：管理转让`management-transfer.real.spec.ts:257:29`×3；owned-list的`:200:57`×4/`:201:58`×4/`:220:66`×1/`:221:67`×1（同`owned-application-pagination.real.spec.ts`，共10）；资格角色`qualification-read-matrix.real.spec.ts:368:54`×6/`:368:116`×6（共12）；决定afterAll `review-decisions.real.spec.ts:40:143`×4。前25条是Application错误响应头，后4条是Gateway Session401缺private；无新增非缓存硬失败，未删除断言或代理补头。

本轮30个实际决定响应观察与专项一致：新真实App503 private/no-store均真，只有原4个Gateway Session401缺private。新增fault保持仅断App内部Auth传输、Gateway鉴权/另一能力可用；页面未重放/清Cookie，明确读回PENDING/null decision、原revision/snapshot，四检查需重新确认。该读取证明失败后已观察状态，不把PENDING推断为任意未知请求一定未在途。

本轮重新pull latest且轮内固定解析ID：Auth `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9`，App `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`，Gateway `sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`，Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`，Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。官方API pin及显式NSS fixture同前轮，strict/报告隐私/runner构建前置通过；未编译后端、未改运行期product/runtime/runner/spec。

专项和全量容器/网络均已核对为空，本地及本次远端legacy仍`e68851e343bd0e077e5ccd0b680fe6813216ced0`，未push。统一954 Vitest＋221 Node、strict/官方生成/Edge及本包所列真实业务功能证据已收齐；完整门禁仍IN_PROGRESS，外部29缓存头与其它明确缺口保持OPEN。后续[Admin→Developer资料投影闭环](2026-10-23-profile-decision-developer-projection.md)仅已接受、尚未实现，不当本包完成项。
