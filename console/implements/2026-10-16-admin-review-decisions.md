# UC006–007：Admin 审核决定接入

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。产品实现提交`70e752242c516c24d7da42a371d64102330b4f19`，键盘验收增量`543fe2a9010aa129fd7d409c3359a8267f738f98`，测试Reviewer隔离`2e783ac536c5e2cf4ab09d2024bd89525f6e1b3e`，恢复边界最小加固后最终冻结`52d2598397f7e0f7e400fa32af5d4cf94d191df9`（均本地，未push）。用户明确授权按App/API→Gateway→Console串行推进，并接受两项App补齐设计；本包只实施既有[UC006](../use-cases/UC-CONSOLE-006-review-application-versions.md)及[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)的决定流程，不新增业务用例或Developer写页面。上层UC和默认已发布镜像全量门禁不因此关闭。

## 权威、来源和范围

- Version正式定义来自固定App设计提交3b16200的[UC005 BR-REV-016](https://github.com/TokenTeam/iwut-docs/blob/3b16200/app-center/use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016)及其[v3正式人工检查对应表](https://github.com/TokenTeam/iwut-docs/blob/3b16200/app-center/use-cases/UC-APP-005-decide-application-version-review.md#v3-正式人工检查定义)，[BR-REV-017](https://github.com/TokenTeam/iwut-docs/blob/3b16200/app-center/use-cases/UC-APP-005-decide-application-version-review.md#br-rev-017)约束确认集合，UC030定义正式详情投影；本次启用不可变v3，不给历史v1/v2追写新正文。
- Profile解释只绑定UC016的`app-profile-review-v1`两项原定义；Reviewer的当前公开资料来自UC031扩展后的同次详情投影，不借Developer管理查询或数据库推断NONE。
- 本轮App权威输入为根docs工作树读取的已接受设计提交`3b16200`及其后实现记录。Console专属docs工作树起点`3d191395acd8d3d126196e4722d81a45a50b22c6`尚未包含该设计，其本地相对链接的App源仍为旧版本、没有本次定义/投影，不能作为新契约来源。此记录固定提交与实际根工作树读取来源，不复制或修改本工作树App权威源、不自行合并分支；以后合并docs分支再收敛相对链接。
- 共享BR-CRV-001–008、BR-CMG-002–004及ADR-CONSOLE-003/004/005继续约束权限、Query/表单内存、Cookie、私有响应与恢复。
- API为官方`https://github.com/TokenTeam/iwut-api-proto.git`精确commit `27c9743d2d7476511932a83563e103aee5b4e28e`，所有既有输入统一重新生成并写入source-lock SHA256。该提交尚未push；本地使用进程级Git url.insteadOf从同一官方仓库的已提交mirror fetch，不改生成器信任URL、不复制或手改生成物。远端CI必须等待API发布后才能拉取。
- 初始固定本地artifact为App `review-3a83152` / ID `b6d0b68f921eca043d75708182bcdc5d9ac7d82da1cf0488f7485005cae2cee8`、Gateway `review-3e8a59c` / ID `951d4a2b3aa923743623a0323f8cbcc445d53d54c438d4fd12d36e4869bbe886`、Auth `22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`。本包只消费artifact，不编译App/Auth/Gateway、不push或部署。

## 已实现行为

两类生成决定client只序列化command，三元路径ID不进body，不发送身份或客户端时间，不重试。Profile APPROVE的指针通过生成Value明确输出null或UUID，REJECT真正省略该字段、发送空checks并保留有效reason原文；int64全程精确bigint/ProtoJSON字符串。响应严格拒绝未知字段、目标/终态不一致、source+2关系错误、REJECT得到APPROVED和Profile批准后指针不指向目标；Version APPROVE得到合法System REJECTED则如实展示。

表单只在当前PENDING、上下文关系一致、eligibility允许且定义完整时开放。Version v3核对已接受的四ID与定义顺序/完整性，正文只取服务端title/description；未知版本、旧v1/v2和不完整定义只读，不能用ID猜义。Profile只使用其独立v1两项解释，空icon仍逐项确认不适用，不套Version v3同名ID正文。全部检查默认未选，没有全选。

提交前显示attempt、实际读到的policy version、方向和原文理由。Profile批准另展示正式公开资料对照和自动替换效果；缺失/空/非法state不是NONE，非零NullValue不合法。icon/描述/理由只作纯文本。Version批准不等于发布；Profile批准自动公开，没有第二Publish。

表单状态随Session/attempt/三元目标隔离；policy/定义/当前revision/公开指针变化用layout同步清确认，派生guard及冻结confirmationBinding也阻止旧预览提交。结果提示按Session/attempt/目标绑定，迟到回执不能出现在新目标。两个决定复用独立capability失效广播与按代Session恢复；明确403先卸载私有表单和对应查询，保留其它能力及有效Session。

写请求有30秒浏览器deadline和同步互斥，不阻止离开。409必须重新读取同一Review并重新确认。超时、断网、5xx或畸形成功进入RESULT_UNCERTAIN，不宣称失败、不自动重放/改方向。先回查同一Review，终态只呈现已观察结果；PENDING明确不能证明原请求未在途，重新评审后才允许一次新的明确提交。恢复失败仍保留无法确认提示和退出路径。焦点、fieldset/label、状态文本和键盘动作覆盖所列恢复流程。

## 验证入口和证据边界

`pnpm test:real`仍默认每轮pull已发布latest，保留既有88项及缓存头断言。`pnpm test:real:review-compat`是明确的本地兼容性来源，校验三服务ID、不pull替换本地artifact；无spec才是全量，附spec仅为focused。E2E_*override另标`explicit-image-override`，本地固定入口不接受override。

新增决定spec暂时只在local-compatibility来源运行；默认published-latest明确skip新增决定，因为API/定义/指针/ADMIN决定依赖尚未发布。发布后必须把Formal准备与该spec迁回默认全量、解除临时source gate，并重拉latest验证；不能长期从默认交付门禁排除决定。

真实准备复用正式注册/Apply/Create/grant的owner和独立Reviewer，额外正式Create4App、各Create/Submit3Version和1Profile；首次批准后再正式创建/提交下一Profile。没有seed新决定对象、权限、状态或公开指针。当前host的DNS把外部域名映至benchmark地址，正式App预检会拒绝；仅local入口的App容器增加受控NSS fixture：www.wikipedia.org→198.35.26.224（HTTPS DNS核验的公网A），真实App预检仍运行，不抓取外部HTTP，不证明页面内容安全或部署DNS。

真实spec不使用page.route/MSW或Recorder业务成功。固定loopback/bearer控制只收精确POST/application/json/空对象，不收任意subject、URL或数据库；透明代理只延迟、丢弃或截断真实请求/响应。隐私护栏继续使用tests/real/test.ts，禁用trace/截图/video，标准错误只留安全位置；新增诊断只含kind/status/private/noStore布尔。

## 执行记录（持续追加）

- 普通回归已通过889项Vitest（其中Admin144、API204）及122项Node；strict、精确生成漂移与独立性通过。初轮fixture浏览器10worker为7失败/3通过/6非目标skip；独立workers=1全量为10通过/6非目标skip（9.3秒），前轮原因未证明，不把串行通过当成已修复该偶发。Edge默认published Gateway失败关闭通过。
- focused第1轮：正式Submit拒绝example.com专用域名（422 APPLICATION_LAUNCH_URL_NOT_REVIEWABLE），未进入决定。第2轮换正常公网域名后仍422，定位本机DNS实际返回198.18.x/2001:2::benchmark；不改App规则，以显式NSS fixture继续。
- focused第3轮：Formal准备已过，首个Version实际决定返回200，但决定响应private缓存断言失败；没有删断言或当作完整通过。
- focused第4轮：前4项真实React通过Version批准/拒绝、Profile NONE批准→UUID替换批准及拒绝。Profile错误公开指针native协议负例409保持PENDING和原公开内容；不当作不同修订UI并发。安全观测Version决定200缺private和no-store；Profile决定200/409有no-store但缺private。决定缓存断言集中afterAll保留红。第5项的透明gate release helper误期望200，实际控制契约是204，造成测试失败/后续serial跳过；已改正并增加finally清理，不冒称并发/unknown已过。
- 初轮默认published全量在准备资格权限时遇到上游504（2秒）而未进入浏览器；当时有两套独立真实栈并行，因果未证明。清理后已在无local-real栈竞争时重新启动无参数published门禁。
- App负责方已复现决定响应头遗漏并在既有范围修复；新固定candidate为`review-cache-candidate` / ID `a34ff33dd624ca55a162006c51580282aecf73ea42c676b81582c654568cf166`，来源3a83152+冻结patch SHA256 `2243592d3da95f2dd40c93529c3decc18ce407c2ad0aa09d2c58e3ec24eb78af`、API27c、Go1.25.5/CGO0，只修两决定响应头及回归。local入口已更新并精确校验该ID；App规定的check-full正在最终Mongo/race阶段，正式commit绑定待其报告。默认published门禁与后续focused/full compatibility串行运行，完整结果和资源清理随后记录。

## 未关闭范围与结构化gap

1. **UC007不同修订并发改公开指针**：同App只有一个working DRAFT/SUBMITTED，当前尚未证明通过既有命令建立两个不同修订同时批准的可达UI准备路径。不新增发布/回滚命令，不改DB指针；只登记实际NONE/UUID替换与native错误pointer409。App已有真实Mongo指针CAS证据可交叉引用，不能替代Console UI矩阵。UC不因此改写。
2. **全部决定故障矩阵**：本包列明已运行场景，策略退休、Scope失效、全部App依赖故障与每一种跨Session/迟到组合仍须分别验收；组件交错和旧读取矩阵不扩大为真实决定全矩阵或全heap清理保证。
3. **已发布默认门禁**：未发布依赖与原Application管理GET404/List400缓存头缺口仍开放；不得删原断言、代理补头或把整体Console/UC记为COMPLETE。

### 已发布镜像工作快照诊断轮（非最终冻结证据）

`iwut-console-real-510605` 的无参数默认轮终态100项：84通过、4失败、12新增决定明确skip，浏览器17.0分钟，exit1。81条错误仍全部是原缓存头（Admin56、管理转让3、owned游标10、资格12），无新增非缓存硬失败。Auth22795、App6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b、Gatewaya048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9各轮重新pull；Mongo/Traefik固定输入不变。轮次容器已清理。

该轮从70提交前的working tree启动，运行期间仍补过仅local控制/固定candidate来源、控制负例及决定client显式strict选项（原默认亦false），之后又有543的键盘helper。它不能标成70或543全部字节冻结的完整证据。即使新增决定当轮skip，也不以“推测无影响”替代冻结门禁；最终将在candidate focused/full之后，以最终冻结源码再执行无参数published full。

当前543干净源码已串行启动candidate focused12项；产品提交后的键盘测试通过focus+Space逐项确认，预览/首次提交focus+Enter。除证据文档外，运行中不改源码、spec或artifact来源。最终focused/full compatibility和冻结published结果待追加。

### 冻结543的candidate决定专项

`pnpm test:real:review-compat tests/real/review-decisions.real.spec.ts`在干净543源码和精确candidate ID下终态12/12通过，浏览器1.2分钟、exit0。产品与测试来源运行期间未改；只有外部证据文档继续登记。全部轮次容器清理后才启动下一完整门禁，未重复focused。

逐项收齐：

- Version四条服务端正文由键盘focus+Space逐项确认，预览/首次提交focus+Enter；批准返回APPROVED和revision3，UI明确不等于发布；拒绝切换清checks、空数组/原文reason和终态正确。
- Profile首次批准显式null、当前revision字符串2、两个独立v1检查；正式创建/提交下一修订后展示被替换资料，显式UUID批准自动切换；拒绝真正省略pointer并保持旧公开值。
- 固定错误pointer的native协议负例得到409 APPLICATION_PROFILE_PUBLICATION_CONFLICT，随后正式Reviewer GET仍PENDING、原公开指针未变；它不代表不同修订UI并发。
- A的真实决定POST在透明REQUEST HOLD期间，B用另一真实Reviewer Session提交成功；释放未修改的A得到409 ALREADY_DECIDED。A明确重读实际终态，不重放，证明请求重叠及一次性决定。
- Version/Profile真实200正文截断后React进入RESULT_UNCERTAIN；fault同时证明upstream200及bodyTruncated，随后同Review GET观察REJECTED，写次数始终1。没有从gate状态单独推断JS行为。
- 原请求在途时另一个真实GET可见PENDING；SPA返回队列后释放原请求，App实际REJECTED且迟到回执不回填新页面。另有真实30秒deadline使React进入unknown，重新读取仍PENDING，焦点说明不能证明原请求未在途，确认全部清空、写次数1、Session保持。
- 单项Reviewer对另一能力的真实决定403、Admin Cookie不能经Developer surface决定、owner虽有精确双权限但三项利益冲突仍403且UI禁用；负例后目标保持PENDING。
- 加载表单后正式revoke单项权限，实际POST403使React卸载理由/表单、保留有效Session；另一审核能力可读，正式regrant后明确重新进入且无旧checks。
- 正式SUSPEND owner后，发送APPROVE，实际返回REJECTED、决定人区别于Reviewer且空checks；React如实显示实际拒绝，随后正式RESTORE owner。

共观察16个真实决定响应：Version200×6、409×1、403×3；Profile200×4、409×1、403×1，全部private=true且noStore=true。缓存断言未删除且afterAll通过。HTTP正文截断仍由真实200响应提供证据，超时没有伪造业务成功。

App负责方随后报告相同内容已通过check-full24/24且changed_sources=[]，正式本地commit为`52ea87aff89e66d32621d508bc2eb6cd486bd984`；真实Mongo/race1279.308秒、HTTP/gRPC E2E162.054秒，末stage1285.093秒，报告`.artifacts/verification/20261016T081304Z-muguvlfv/report.json`。candidate ID a34ff33...不变，另加`review-52ea87a`tag；本轮不因身份标签变化重建或改输入。该后端报告交叉支持业务规则，不能替代上述Console UI证据。

同一543已开始无参数full compatibility，结束后还需最终冻结published full。当前12/12不等于任何一套完整门禁通过。

### 冻结543完整compat与测试准备隔离

`iwut-console-real-540173` / `pnpm test:real:review-compat` 在干净543及上述三个精确本地artifact下终态100项：85通过、4失败、11未运行，浏览器16.9分钟、exit1。全部旧Admin查询场景及其56条缓存断言已通过；剩余三项旧失败仍为Application管理错误缓存头，管理转让3、owned游标10、资格12条原断言均保留。第4项失败为新增决定spec的beforeAll共享资格R账号`beginEmail`调用，首个业务case未运行，后11个serial跳过；不能把focused12/12替代此轮完整结果。报告隐私护栏只保留可信源码坐标，没有保留上游HTTP码/reason；紧邻资格矩阵复用EMAIL导致共享冷却只是诊断推断，**没有直接观测429**。容器已清理。

本地提交`2e783ac`仅改测试准备/文档，产品实现仍70e7522：只在local兼容入口正式注册独立主Reviewer，普通DEVICE验证，G查询初始精确空双权限后逐项CAS grant并读回。不调用Apply，不复用R的EMAIL状态，不改原V/P/资格账号、权限相位或Auth冷却规则；注册后仍加入已有的真实mailReadyAt等待，没有固定长sleep。grant回执未知只读确认、不得重放；重复actor/非空初始权限/错revision失败关闭。

两个新增合成准备检查只证明actor/授权控制：正常与回执丢失均精确两次grant、unknown-before-write/错误CAS/readback失败不重放，重复actor在设备外呼前停止。合成在首个App Create故意中止，不伪造业务成功。原真实空body/bearer/method/query/任意subject/database/URL控制负例保留。统一889项Vitest＋124项Node、strict及官方精确pin生成漂移通过；2e783ac干净冻结后直接运行完整compat，不重复focused。该轮和随后最终published full终态待追加。

### 冻结2e的完整compat终态

`iwut-console-real-554453` 的无参数`pnpm test:real:review-compat`终态100项：**97通过、3失败、无skip**，浏览器17.9分钟、exit1。新主Reviewer在全部既有前置矩阵后正式EMAIL登录成功，全部12个决定场景再次通过；16个决定响应的private/no-store均真。原V/P与资格矩阵保持原账号和相位。仅原Application错误响应缓存头导致管理转让、owned游标、资格三项失败，3+10+12=25条原断言未删。56条旧Admin查询缓存断言已随固定App修复通过。本轮容器已清理，代码/测试/artifact运行期间未改。

### 恢复边界最小加固及最终默认冻结

完整compat终态后，静态走查确认两处既有BR-CRV-003边界：unknown→同Review重读403会卸载原提示；决定的明确利益冲突403会被原查询执行器误判成整个Reviewer能力撤销。本地`52d2598`最小加固：denied页总是以条件式说明“若有尚未确认的决定，其结果仍无法确认；恢复访问后再读取原 Review，勿据此重发”，不保留reason/checks/快照；只有决定调用、对应cap的实际HTTP `ERROR_REASON_APPLICATION_REVIEW_CONFLICT_OF_INTEREST` / `ERROR_REASON_APPLICATION_PROFILE_REVIEW_CONFLICT_OF_INTEREST` 403保留能力，让现有明确ApiError流程要求重读同Review并更新eligibility。查询403、错cap reason、去前缀短名、正式PERMISSION_REQUIRED继续原清理；没有把403伪装unknown。

新增10项core分类核验及两能力各2项组件交错：unknown后重读权限403仍有无法确认提示，清当前data/理由/检查、保留Session/另一能力，原POST1次；加载后关系冲突403不清同能力其它目标，必须重读并观察CURRENT_ADMIN禁用，原POST1次。首轮新增fixture把生成枚举写成字符串，2项与strict先红，改用生成枚举后Admin全158项及全workspace strict通过。该证据是组件/core，不冒称真实关系在加载后改变的UI矩阵。

完整compat仍仅绑定2e，不因低影响分类/文案加固再执行第三套全兼容，不将2e全量冒称52全部字节证据。52d2598干净源码随后启动最终无参数`pnpm test:real`，运行中不再改源；最终默认终态待追加。

### 最终冻结52d的published-latest全量终态

`iwut-console-real-607614` 在干净`52d2598397f7e0f7e400fa32af5d4cf94d191df9`源码下执行无参数`pnpm test:real`，终态100项：**84通过、4失败、12明确skip**，浏览器16.5分钟、exit1。不是前述pre-70工作快照诊断的复用。运行中没有改code/spec/来源；runner在浏览器启动前实际成功执行完整`pnpm build`，使用本轮两App生产dist及两个BFF dist/server.js；最终源无需重复构建。strict与报告隐私前置均通过。

五镜像重新pull，Auth `22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、Gateway `a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`与前轮一致；Mongo `e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`固定。没有静默替换成本地candidate。

81条错误全部为原缓存头断言：Admin查询28个响应各缺private/no-store共56，管理转让Application404缺no-store共3，owned游标错误共10，资格角色共12。可信调用栈全部落在原cache断言源码位置，无新增非缓存硬失败。全部旧88项均执行，新增12只因未发布依赖明确skip，不能称完整审核已发布验收通过；默认临时source gate解除条件和后续命令仍按上文规定。两个签发上限、25个Developer跨Session、12个Admin跨Session、真实双副本与Mongo提交故障等按原场景通过，不扩大为所有决定矩阵。

最终轮次容器（含已退出容器）及network均为空，Console工作区干净。本地及远端只读核验legacy仍`e68851e343bd0e077e5ccd0b680fe6813216ced0`；提交仅本地、没有push或部署。本包工程可审阅，但整体Console/UC与已发布门禁仍IN_PROGRESS。直接真实成功决定证据为543 focused12/12及2e完整轮中的12/12；52边界追加仅有上述158项组件/core与strict、最终生产构建及默认全量证据，不能混称其已重跑本地决定完整链路。

### 2026-10-22：重新拉取已发布镜像后的接线前置检查

用户通知已push并授权重拉镜像继续；若Gateway未接入，允许暂时中止。本轮Console仍为干净`52d2598397f7e0f7e400fa32af5d4cf94d191df9`，没有修改生产代码、spec、source gate或本地compat输入。

三个已发布`latest`均实际重新pull并inspect，解析到的image ID/RepoDigest如下：

| 镜像 | 实际ID/digest | 相对上轮已发布验收 |
| --- | --- | --- |
| Auth | `sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9` | 已更新 |
| App | `sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a` | 已更新 |
| Gateway | `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` | 未变化 |

不只根据digest推断缺口：以该精确Gateway镜像，在`--network none --read-only`下实际运行镜像内`/gateway-config --render --routes /config/routes.v3.yaml`，配置独立的`admin.example.test`、`developer.example.test`及测试服务地址，直接核对生成Traefik配置。四条ADMIN审核查询均存在；下列两条ADMIN决定router均不存在：

- `admin-console-app-decide-application-version-review-http`
- `admin-console-app-decide-application-profile-revision-review-http`

两条普通API host决定路由和BFF internal决定路由仍存在，但没有ADMIN host对应决定路由，不能用其它入口替代既定Browser→Admin Session→Gateway链路。本次是已发布镜像配置证据，不是相邻Gateway源码检查或运行中身份链路E2E；没有启动明知缺路由的完整套件。生成配置SHA256为`c6aebb57b24296ab3244f02c5b50bbc18e8d25df7239a6493bed413ab6cffa7c`（只适用于本次上述测试地址）。

同时，不使用本地mirror重定向执行`pnpm generate:check`成功：官方API精确pin `27c9743d2d7476511932a83563e103aee5b4e28e`已可远程取得，现有生成物与固定输入一致。API发布依赖已有新证据，但不能因此解除Gateway或整个默认决定门禁。

按用户允许的条件暂时停止后续联调，不编译后端、不换回本地artifact、不删断言或把新增决定长期skip当通过。尚未对新App/Auth运行完整回归，因此不声称旧缓存头已修复或新镜像业务验收通过。解除条件是已发布Gateway包含上述两条ADMIN决定接线；之后重新pull latest、将正式准备/决定spec纳入默认门禁并执行最终源码的真实决定与无参数全量。临时配置目录已清理，未留下运行容器；本地和本次远端只读核验legacy不变，未push Console或docs。

### 2026-10-22：已发布审核决定迁入默认门禁（ACCEPTED / IN_PROGRESS）

用户通知Gateway CI完成后，重新pull得到`sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`。以该精确镜像实际运行`/gateway-config`，已确认两条ADMIN决定router均存在，且中间件为scrub→Admin Session→remove-cookie→对应Gateway ForwardAuth→post-auth scrub→strip-prefix；官方API同pin远程`generate:check`再次通过。这仅解除镜像接线前置阻塞，不能代替真实决定验收。

按既有用户授权自行接受本增量，范围和决定如下：

1. 移除新增12项决定spec的local-only skip；主Reviewer正式独立注册、邮件冷却等待、固定空body/bearer控制及Formal Create/Submit准备同样接入默认`pnpm test:real`。保留原正式授权、CAS/unknown不重放、actor隔离和旧88项全部断言，不seed决定资源、不伪造响应。
2. runner对镜像实际生成的两条决定router增加缺失/重复即失败的轻量前置检查；此检查只证明生成入口存在，不冒称鉴权正确。Edge扩大到六条ADMIN查询/决定入口，检查认证上游不可用和伪造头均失败关闭、Developer拒绝、无SPA兜底。任何未来latest退回缺路由时直接失败，不自动skip。
3. 保留显式local-compat命令仅用于历史诊断，但不再控制决定是否执行，绝不把其结果冒称published-latest。默认仍逐轮pull并固定本轮解析ID，不编译相邻后端、不隐式回退本地artifact。
4. DNS准备边界显式延续：本次`getent ahostsv4 www.wikipedia.org`实际为`198.18.3.15`，Cloudflare HTTPS DNS同次查询的公网A为`198.35.26.224`。测试App容器统一使用此前已接受的固定NSS输入`www.wikipedia.org:198.35.26.224`，不再只限local来源；真实App Submit/Decide预检仍执行，不发外部HTTP、不修改App网络规则，也不证明宿主/部署DNS或内容安全。该输入不是产品DNS配置。
5. 先普通回归、strict/生成漂移/Edge，再冻结源码跑published专项12项和无参数全量100项，必须以实际运行数/失败/skip为准。专项不替代完整门禁；未过原缓存头或其它断言不push，不关闭完整UC、不同修订指针并发、全部决定故障矩阵或Session遗留缺口。

当前仅完成上述接线/远程API/DNS前置证据；源码迁移和真实测试终态后续追加。

迁移已本地提交并冻结为`65a9ea0`：新增8项路由准备检查先8 RED后8 GREEN，普通统一903项Vitest＋132项Node全部通过，strict/真实spec类型、远程同pin生成漂移、shell/Node语法及仓库独立性通过。新Edge六入口均通过认证上游不可用、伪造头不旁路与Developer api-deny检查，使用已发布Gateway `2953ae7f…`；这是路由隔离证据，不当作成功审核E2E。生产App/BFF代码未改；源码、spec与来源在后续真实轮次保持冻结。

开始默认published-latest的12项决定专项，仍逐轮重拉五镜像并运行真实生产build/报告隐私前置；该专项未达终态前不记作通过，之后须另起空环境执行无参数全量100项。原local-only skip已删除，不再将12项排除在默认门禁。

#### 已发布专项终态

冻结`65a9ea0`，轮次`iwut-console-real-202804`执行`pnpm test:real tests/real/review-decisions.real.spec.ts`，12项全部通过（浏览器1.1分钟、exit0、无skip/retry）。全部正式准备及产品React操作使用published-latest来源；16个真实决定响应的private/no-store均为true，200/403/409检查全部保留。两类批准/拒绝、NONE→UUID公开替换、重叠决定一次性提交、200正文丢失后的unknown回查、30秒deadline后PENDING不推断失败、单权限/利益冲突/撤权、实际System拒绝均收齐本spec列明证据。

Auth ID为`sha256:c2f06d8fe4ca2734a32e07e70f6ab7ba8c0207932336222c2c92986e073de8b9`，App为`sha256:2af4af71e8eb8f1ea46e92bfdaa3e8e14944cb0bc4ca46b95c9a05db6c46340a`，Gateway为`sha256:2953ae7fb81da7d06586b735340e4d3d320e523bb67f7700cc2571602e728303`；Mongo/Traefik仍为既有固定输入。本轮容器（含退出）与network均为空后，保持相同源码/spec冻结，启动另一空环境的默认无参数全量100项。不把上述12项或本次路由补齐当作所有决定故障组合/不同修订指针并发或完整UC已完成，也未复用本地compat结果。
