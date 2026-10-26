# WITHDRAWN 与正式关闭后的历史读取

状态：ACCEPTED / VERIFIED（2026-10-27，依据持续目标授权自行决定、记录并接受；仅所列有界链）。

## 目的与权威来源

补齐 UC002–005 已接受只读功能在本人正式退出 Developer 后的有限证据，不增加关闭、退出、治理或 Developer 写 UI。资格/会话语义由 [Auth UC024](../../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md) 拥有；关闭与配额/owner 义务由 [App UC027](../../app-center/use-cases/UC-APP-027-close-application.md#br-app-025) 拥有；近期认证使用 [正式双证明契约](../../platform/contracts/application-close-reauth-proof-v1.md)。历史读取分别引用 [UC029](../../app-center/use-cases/UC-APP-029-query-owned-application-management.md)、[UC034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md)、[UC037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)、[UC039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md)，不重新定义后端规则。

转让后失去 adminId 的账号、直接 seed WITHDRAWN/CLOSED 或旧生命周期 readseed 均不能替代本链。只以 App 正式 CLOSED 读回观察持久关闭协议的完成点；不虚构未向用户公开的 Auth receipt 字段，也不代验全部 OAuth 撤销矩阵。

## 自行接受的有限设计

1. 新增一个专用普通 owner，正式注册、Apply、两项 Reviewer grant、Create 一个 App、各一个 Version/Profile 并正式 Submit，以及一个加入链接/ACTIVE Tester episode。复用现有 G 与 Tester 的普通 DEVICE actor；不增加它们的 EMAIL 次数，不污染原121项的固定主体。专用 owner 浏览器仅 Developer origin 一次 EMAIL，加注册共2封；Node 准备只用 DEVICE。保留真实限额、冷却与 Session 容量，不增 quota 上限、不 seed 本链任何事实。
2. 只有该账号的合成注册密码在 Node 私有闭包中保留，供当前密码＋同一 Node Session/credential 的新签名使用；不进入公开 fixture、浏览器、文件、日志、URL 或 App 请求。原始 Frame 依正式域/动作、UUID 网络字节与 challenge32 构造，只做一次SHA-256/ECDSA；沿用当前设备协议接受合法 high-S/low-S，不自造签名规范。proof 只以固定 Close 路径的专用 header 传给 App。
3. 复用已有 Scope TLS App provider、CA 与独立 oauth-service key，新增正式 owner-exit/closure caller 精确权限和隔离实例开关。公网 OAuth 保持关闭，身份/服务/OIDC/delegation 密钥边界不变。App closure worker 本来就在运行；原历史 seed 的2100年due/attempt0及自检必须保留，不假称flag能暂停worker。固定官方 API `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6` 远程生成所需子集，不能手写漂移业务DTO。
4. 使用 `zy-developer-withdrawal.real.spec.ts` 三项串行测试，位于现有末尾账号禁用包之前；两包主体和准备互不复用。固定 loopback bearer 控制器只允许 prepare / observe / block / close / ready / withdraw，POST空对象、无query、无任意subject/App/密码参数；准备 Promise 即使失败也保留，不重复 Apply/grant/Create/Submit。

## 三项真实浏览器证据

1. ACTIVE＋APPROVED 时九个管理 RPC 与生产 React 读取非空目标；固定 Prepare 得到 BLOCKED/OWNED_APPLICATIONS，资格/revision、Session/钥匙及数据保持，不能把未发布应用解释成零义务。
2. 独立固定 Node DEVICE Session 正式 Begin/Complete 双证明、单次 Close；按真实时间有限只读等待 App CLOSED，验证 Version/Profile/Review 保留，ACTIVE Membership仍为历史、链接因关闭REVOKED、当前链接为空。冻结实际 CLOSED 管理投影，列表默认排除CLOSED，显式筛选才含目标。生产概览、Version/Profile详情及Tester视图保持可读，清晰显示关闭状态；不把读权解释为写/owner义务恢复。
3. 关闭后新 requestId Prepare READY，再独立明确 Confirm 到 WITHDRAWN；从正式 Get 与 G/本人状态读回确认同一authId、handle保留、Developer revision仅加1、account/permission revision与Reviewer权限保持。原浏览器Session/generation和不可导出钥匙不变，零自动重登/DELETE；九RPC及代表React视图逐字段对照关闭后基线（仅asOf自然变化）。不新增审核决定或其它业务写，不恢复资格、应用或授权。

## 未知结果、安全及验收门禁

每个副作用在await前保存attempt，最多一次；相位重复只读，拒绝并发、跳相位和漂移。已知operationId的退出状态通过Get读回；Close未知只读固定App closure，404不证明未提交。不生成替代closure或补偿写。reauth只有Begin/Complete，无Get；未知Begin/Complete不能纯读找回proof，因此停止该subject后续写，不重新签发或读数据库。Prepare未知且未拿到operationId也停止，不把requestId冒充operationId。Confirm未知仅Get原operation。已知PREPARING/CLOSING使用有界真实等待，不fake clock；到界仍未收敛就保留失败，不回滚事实。

先验证签名Frame/有界状态和runtime配置，再跑普通测试、strict、官方生成漂移、Edge/docs。冻结产品/runtime/runner/spec后，每轮重新pull published latest并轮内固定ID；先3项专项，再默认124项全量，原121和缓存头/隐私断言全部保留。遇未接入或契约不符，保留实际失败，不编译相邻后端、不换local artifact、不主动消息外部agent。每轮核验退出码、容器（含停止项）/network清理及legacy本地/远端不变；只本地提交、不push。

只关闭所列WITHDRAWN历史读取链；App政策发布回执/下一真实政策、33+carrier架构及完整UC/goal继续独立开放，不自动扩展无穷状态排列。

## 实施与静态验证

运行配置8项、签名Frame11项、runner source-wiring6项、typed相位16项及正式owner准备8项共49项新增Node回归通过；状态机先缺模块RED，再补齐实现，并由坏Close回执/重复密码消费回归再次RED→GREEN。静态接线检查不冒充运行时安全或真实业务结果；合成transport不冒充后端收敛证据。专用工厂Promise失败也保留；只读控制返回最小事实，不返回密码、Node凭据、Session或proof。普通954 Vitest＋344 Node、strict、官方固定API远程生成检查、Edge检查和docs72份brief/367行8退休编号检查通过。静态门禁本身不足以证明真实链；专项/默认124门禁以以下实际轮次记录为准。

## Published latest 真实验收

Console产品/runtime/runner/spec固定在 `ae46e5c7927e7d6ace90ff6dd9f24ceb01ceb249`；实际生产Web/BFF行为未改，本包仅测试基础、生成子集和元数据。专项轮 `iwut-console-real-344878`：`pnpm test:real tests/real/zy-developer-withdrawal.real.spec.ts`，**3/3通过、35.7秒浏览器阶段、exit0**。同冻结全量轮 `iwut-console-real-350177`：无参数 `pnpm test:real`，**124/124通过、23.8分钟浏览器阶段、exit0**，无skip/retry；原118基线、本包3项和账号状态3项均收齐。两轮均先通过实际随机私有输入的报告隐私检查，重新pull published latest后轮内固定镜像ID；没有用专项替代全量。

两轮后端镜像相同：Auth `sha256:518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16`；App `sha256:68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01`；Gateway `sha256:444c75a71fc74fb14840718b259aeec14fbe2bbcda0a9832340c70b64ed099b0`。Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。未编译后端、未换本地artifact、未向其它agent发需求或push。

ACTIVE时正式Prepare观测BLOCKED/OWNED_APPLICATIONS；当前密码＋同一Node DEVICE凭据新签名正式Close，App固定closure收敛CLOSED/lifecycleRevision3；正式新Prepare READY与独立Confirm后Developer WITHDRAWN/revision2，accountRevision1、Reviewer权限及permissionRevision、永久handle保持。Version/Profile仍SUBMITTED、其Review仍PENDING，ACTIVE会员/容量保留，链接正式REVOKED/APPLICATION_CLOSURE、当前链接为空。默认列表不含CLOSED，显式筛选读回原App；九生成RPC和代表生产React视图在WITHDRAWN后对照真实CLOSED基线保持（仅各顶层asOf自然变化），原Developer Session/generation/不可导出钥匙未变，无浏览器App业务写/自动登录/DELETE。以上不是关闭/退出UI、全OAuth撤销矩阵或全部状态排列的交付。

两轮结束后核验容器（含停止项）与network为空；工作树在全量期间干净、冻结未变。legacy本地/远程均保持 `e68851e343bd0e077e5ccd0b680fe6813216ced0`。全部结果仅本地提交；App政策发布回执/下一真实政策、33+carrier架构、完整UC和持续目标继续开放，不以本包全绿自动关闭。
