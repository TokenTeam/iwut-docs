# UC006–007：Admin 审核查询首阶段

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行接受完整[UC006](../use-cases/UC-CONSOLE-006-review-application-versions.md)与[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)，先交付队列/详情，不缩减批准、拒绝、并发决定与结果未知恢复的最终范围。

## 权威与当前依赖

查询权限、队列资格、不可变snapshot、分页及一致性分别由[App UC030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md)、[UC031](../../app-center/use-cases/UC-APP-031-query-application-profile-reviews.md)拥有。完整决定的缺口继续由[Version决定准备](../query-contracts/version-review-decision-readiness.md)及UC007依赖表跟踪：Version完整正式检查定义未核验，两个决定尚无ADMIN surface，Profile APPROVE缺Reviewer可读的当前公开指针/对照内容。不得复制后端规则、发明政策解释或借管理查询越权补齐。

固定API仍为`a5d504c058c62cd91be451074d21608d69789918`，只增加审核查询及其依赖Proto生成输入。Gateway工作区四个查询已有ADMIN声明，但不是镜像验收；本包须重新pull已发布latest验证实际四路由及混合认证链，不能根据相邻源码宣称运行时可用。

## 本阶段功能决定

- Admin会话入口面向获授权的审核人员/平台管理人员，不要求Reviewer先成为Developer或平台管理员。页面入口不是授权投影，每次请求继续由真实Session→USER身份链检查精确权限。
- 两个独立入口`/reviews/versions`、`/reviews/profiles`；详情路径分别为`/reviews/versions/{applicationId}/{versionId}/{reviewId}`、`/reviews/profiles/{applicationId}/{profileRevisionId}/{profileReviewId}`。三元ID逐项校验；不补查Developer管理面或Auth个人资料。
- 队列固定pageSize20，使用显式上一页/下一页替换整页而非累计跨时点拼接。applicationId可选精确筛选，仅合法UUID进入请求/URL；筛选、刷新、Session和能力attempt变化均回第一页。token仅存Query内存，不进入URL或持久存储；前页token栈不代表冻结快照，每页显示原asOf。
- 两类队列保留全部冲突项及正式原因；Profile队列没有submittedBy，不能为了统一表格补查或推断。空队列、权限不足、资源不存在与请求失败分开表达。
- 详情审核材料只能来自review.snapshot；当前Application/Version/ProfileRevision上下文、source revision、attempt、提交事实、当前policy/required IDs、eligibility/asOf、终态decision和Version draftRestoration分别表达。大整数精确保留。历史终态不能被当前DRAFT/ACTIVE policy覆盖成待处理。
- launchUrl、OAuth回调、description、icon和reason均为惰性纯文本，不外链、不嵌图、不预取。Profile null、空字符串和空白原文分别保留；google.protobuf.Value严格接受契约规定的形状，不把任意JSON当安全详情。
- 本阶段没有批准/拒绝表单、决定请求、写按钮或政策ID猜译。PENDING明确说明“审核决定尚未接入”；无冲突不表达为“已获批准资格”。未知policy可原样读取版本和ID，但不能因此开放决定。终态如实显示已有结果，不提供第二Publish或资料恢复。

## 私有读取与失效决定

Admin Version和Profile为两个独立capability，不复用Developer按App清理的scope。Query包含Admin Session binding/generation、capability attempt和filter/三元目标；不持久化私有响应。Session明确失效沿用按代清理，仅影响Admin，不清Developer Cookie或设备。

精确权限不足403先遮蔽并回收当前Session的该capability队列和详情；另一审核能力保留。迟到成功不能写回已退场attempt。只在用户明确重新读取/重新进入时创建新attempt，不建永久黑名单或自动循环；恢复后的旧权限错误不能清新attempt。详情404只退场该三元目标，不能伪称整项权限被撤销。Session类错误先按已有会话恢复分类；其它明确401/403亦失败关闭，但不清有效Session。

400或完整畸形成功是当前Query协议退场：清除捕获Query实例的数据，后续503不复活旧内容。网络、成功正文断流、5xx保留同上下文已核验数据与其原asOf并标旧快照；没有旧数据则只显示失败，不伪造空页。变换filter/目标/Session后不借用旧上下文数据。生产页面键盘可访问，错误/拒绝有明确状态和焦点恢复，不把原始服务错误正文渲染/记录。

## 分层验收与边界

先实现并测试生成client、严格投影、两类页面与能力隔离；组件用typed fixture，不记为真实业务交付。Edge检查必须增加四条ADMIN查询，验证未获得Developer同源surface、缺Cookie/伪造header/认证上游不可用失败关闭，不能误落静态fallback。

真实浏览器使用已发布Auth/App/Gateway latest与隔离Mongo。正式注册、bootstrap与grant建立真实角色，不seed Auth权限。读取fixture可以准备PENDING/终态/冲突/分页事实，但须校验validator/引用/当前与snapshot分离，不能当Submit/Decide命令证据。真实授权至少覆盖双Reviewer、单项权限交叉、无权限平台治理者/Developer、revoke后新请求拒绝、regrant后明确恢复及Session保持；测试过程的治理命令不是生产UI。

首阶段实现及专项通过不能关闭完整UC006/007或原App错误头门禁。验证仍包含普通测试、strict、固定生成漂移、生产build、fixture浏览器、Edge和真实镜像；最终完整门禁继续无参数运行，不能删旧缺头断言。需要新的后端权威决定时只记录最小缺口，不自行改后端或跨chat要求其他agent实施。

## 实施记录

本次先接受设计并开放上述读取实现。实际代码、红绿证据、镜像digest、真实结果与清理将在完成后追加；当前不登记任何新增功能为已实现。

准备决定落定：使用独立reviewOwner、两个新普通单项Reviewer V/P，复用已有G平台治理者与R双Reviewer；不改变资格包A/G/R/T的既有资源。reviewOwner正式Apply、26次Create、正式grant双权限用于三重利益冲突，V/P各只grant一项。25个独立App各准备一份SUBMITTED Version/Profile及PENDING Review，26th保存APPROVED/REJECTED、Version恢复后DRAFT历史和null/空串/空白/惰性资料。所有这些终态仅为明确readseed，不能作为真实提交/决定/恢复命令证据。事务内校验真实validator、BSON精度、引用/snapshot/OAuth和工作槽，只CAS新App序列计数，不seed ownership/quota/Auth权限。

已有fixture还会贡献待审记录，不能为了凑20+5改写旧数据或声称默认队列只有25条。真实测试要求每页最多20、存在续页、自有25条全部覆盖且无重复、整页替换和按某App精确筛选一条；不添加未定义队列状态筛选。固定R的撤Version/重授/撤Profile/重授是四个有界CAS相位，未知回执只读确认，控制端点不接受任意subject或permission。

Edge新增四查询与隔离检查已用已发布Gateway latest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`通过。首轮新增检查错误预期Developer为404而实际502：核对真实生成配置确认未匹配surface会进入Gateway `developer-console-api-deny`，但隔离smoke刻意不监听Gateway，所以502是基础设施拒绝而非SPA兜底。修正为检查502及四条access-log的实际api-deny/gateway-http选择；ADMIN认证上游不可用仍500、伪造身份头不旁路、两个私有ForwardAuth均404。真实完整栈仍须独立验证Developer拒绝404和Admin缺Cookie401，不用隔离502替代。

### 代码及本地验证

Console提交`0b8e36c`实现同pin八份审核Proto及四个严格只读client；`c3dd826`实现Admin双队列/三元详情与capability/Session边界；`c1395bd`保存Edge、真实准备器和四项浏览器场景。没有决定client、BFF通用业务代理或生产治理/决定UI。所有实现目前仅本地提交。

API新增68项测试：接口未接时2红；接通生成解码后缺envelope仍被Proto默认值吞掉2项业务红；细化必需对象/snapshot/Value/精度/conflict等51红后严格guards转绿。API包182项通过，未知完整JSON统一静态ApiResponseError，真实网络/成功正文TypeError/AbortError和明确HTTP错误不被吞并。

Admin最终57项（页面44、核心9、原Session4）通过：入口缺导航1红、同能力多attempt迟到成功/AbortError2红、捕获Query对象残留data4红、同filter从头刷新晚403误清新页1红均修复。活动attempt用QueryClient弱引用集合，403广播遮蔽同能力页面并精确清捕获Query.data，404仅同三元目标；显式重启建立新attempt，旧回调不能伤新页。实际双mounted Version＋Profile组件证明同能力双DOM退场而另一能力保留；新generation建立后旧clear回执不能改其Profile视图/路由/Query/Session。这些是组件/Query层直接证据，不扩大为全heap或真实网络故障验收。

新准备器和BSON/事务readseed合成测试12项通过，不冒充真实Mongo业务证据。新fixture浏览器两项为补测后绿（页面已经实现，不伪造缺页面RED）；整个fixture套件终态10通过/6个跨surface非目标跳过，4.6秒。

冻结源码的统一`pnpm test`终态633项Vitest＋89项Node通过；strict、固定生成漂移、生产build与diff通过。构建保留大于500KB的chunk警告，未放宽阈值或声称性能验收。真实四项专项现已启动；未得到真实终态前，不登记新页面为联合验收已交付，更不关闭完整UC或既有App错误头缺口。

### 首轮真实专项及定位修订

轮次`iwut-console-real-899807`终态1通过/1失败/2未运行（12.5秒、exit1）。真实注册/停服bootstrap/grant/26次Create、Mongo validator/BSON/snapshot/OAuth事务自检及控制HTTP负例全部成功；两个真实默认队列分页、自有25条全覆盖、整页替换、过滤/从头刷新和Session保持通过。详情已读到两类PENDING及若干终态，但某Profile的sequence与revision同为3，测试在“当前对象上下文”按纯数字找元素发生严格多匹配，因此不能登记详情矩阵或后两项角色/撤权通过。

终态后额外查询本轮containers（含停止）/network均为空，随后只修订spec定位：按section中的字段dt/dd配对断言source/current/restoration revision、终态结果及当前DRAFT，不删数值检查或改产品显示。另给最终权限矩阵增加测试善后：先正式观察R，仅明确单权限的既定相位才调用对应固定重授；未决写仍只读确认，不重放revoke/unknown CAS，不让一个UI断言失败污染后续资格包，也不吞掉原失败。修订`9f0bb0a`严格real types与diff通过，产品代码未变；接下来直接无参数47项完整门禁验收，不以focused替代全量。

本轮重新pull实际image ID：Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`，App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`，Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`，Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。相邻后端只作设计/源码核对，不成为测试编译输入。

### 无参数完整门禁

冻结修订`9f0bb0a`，轮次`iwut-console-real-905126`，47项终态**43通过/4失败**（11.6分钟、exit1），五个实际image ID与首轮相同。Admin前三项全部通过：两个默认队列与分页/过滤、全部PENDING/APPROVED/REJECTED/恢复DRAFT/原文详情和bigint/asOf、真实owner三冲突。原有43项中40通过，三失败仅为管理转让3条Get404 no-store、owned分页5个List400各缺private/no-store共10条、资格角色6个Application GET404各缺private/no-store共12条。资格角色的原生/React/G/R/T/最终Session断言均完成，没有上轮正文取消硬失败；Admin准备及有限重授未污染旧矩阵。

Admin最终矩阵收齐了两种token页大小/绑定负例、单项Reviewer交叉、G无权限/Developer无隐式权限、两能力分别正式revoke/regrant及另一能力保留、各次Session/设备保持、Version三元不匹配隐藏和重新读正确目标。已有26个Reviewer查询错误响应各缺private/no-store，累计52条soft断言；这把App缺头范围实际扩大至Reviewer队列/详情400/403/404，不能通过代理补头或删检查解除。

该项另外一条硬失败位于匿名POST的预期：Playwright APIRequestContext不发送浏览器Fetch Metadata，因此实际先得到403 CONSOLE_REQUEST_REJECTED，而不是401。读取当前BFF request-boundary并对本轮实际入口做只读诊断：无元数据403，同源完整元数据但无Session401 SESSION_INVALID，附无效客户端Session/identity头仍401；两种Developer查询均404。诊断只选择当前子进程的非敏感公开origin，未输出/传出环境或凭据，也不替代浏览器spec。原项在首次匿名预期处停止，Profile三元/剩余路由与最后整体Session断言未执行，不能记作完整矩阵已绿。

终态后containers（含停止）/network额外查询为空，随后仅在spec修订来源/认证分层：Node无元数据明确验证403，真正同源匿名浏览器fetch（包含无效客户端头负例）由浏览器自动提供Origin/Fetch Metadata并核验401及SESSION_INVALID；不手工伪造元数据来冒充浏览器。生产BFF/页面未改，修订`f9bc0f3`严格real types/diff通过，四项专项重新pull latest复验中；尚未再次运行47项，不以专项替代完整门禁。

### 最终修订专项与当前门禁边界

冻结`f9bc0f3`，轮次`iwut-console-real-915568`终态**3通过/1失败**，45.4秒、exit1。前三项分别4.5/7.1/3.2秒，最后矩阵28.0秒。治理控制负例、角色与26 App正式准备、事务自检再次通过；默认分页/过滤/空cursor重置、全部不可变/终态/恢复/原文详情、bigint/asOf和三冲突再次通过。

最后矩阵这次完整执行：token绑定caller/filter且pageSize可变，V/P单项交叉、G与Developer无隐式权限，R两项权限各自真实撤销/重授及另一能力保留，Version/Profile三元404的React隐藏和正确目标重新进入，Node缺浏览器元数据403、真实同源匿名浏览器401（含无效客户端头负例、实际Origin/Sec-Fetch-Site核对），Developer两条查询404，末尾Session/不可导出设备、无DELETE/业务写入/外部资源/个人资料补查与有限控制善后全部通过。无硬失败；报告56条错误全部为28个Reviewer查询400/403/404响应各缺private/no-store。保留每条断言，未补代理头、改状态或吞正文失败。它证明本轮选定负例拒绝，不扩大为所有可能有效恶意凭据/标头组合的完整安全证明。

本轮五个image ID仍与前两轮相同；containers（含停止）/network终态后额外查询为空。源码、设计与证据仅本地提交，未push；本地和本次只读核验的远程legacy均为`e68851e343bd0e077e5ccd0b680fe6813216ced0`，未覆盖备份。

完整门禁仍按最近47项43通过/4失败记录，修订后只重跑了本专项，未假称全量已绿。本阶段代码/所列真实功能已实现，但工作包保持IN_PROGRESS：App需在Application管理及这四个Reviewer查询的错误路径补齐正式私有响应头、发布新镜像，再重新pull latest跑无参数全量。完整UC006/007的决定、正式策略解释/绑定、写冲突与结果未知恢复仍未交付；Version正式检查定义、两个决定ADMIN surface、Profile批准公开指针/对照内容继续开放，不能借本次读取阶段缩减最终范围。

### Gateway CI 完成后的无参数全量复验

用户通知Gateway CI完成后，冻结Console `72de336`，重新执行`pnpm edge:e2e`及无参数`pnpm test:real`，不读取相邻后端作为构建输入。两项均重新pull已发布latest；Gateway仍解析为上文`sha256:a048de73…`，Auth/App/Mongo/Traefik五个完整image ID均与上一轮相同，不根据CI完成推断tag内容已经改变。镜像内`/gateway-config`生成与实际Traefik加载、四条ADMIN审核查询及Developer api-deny隔离、伪造头不旁路、私有ForwardAuth不外露和认证上游不可用时失败关闭再次通过。

真实轮次`iwut-console-real-924773`终态**43通过/4失败**（47项、11.7分钟、exit1）。这是匿名来源测试修订后的完整运行，不再只引用focused结果。全部81条失败位置均为既有缓存响应头断言：

| 失败项 | 实际错误断言 |
| --- | --- |
| Admin权限/游标/隔离矩阵 | 28个Reviewer查询400/403/404各缺private和no-store，共56条 |
| 管理权转让 | 3个Application GET404缺no-store，共3条 |
| owned Application游标负例 | 5个List400各缺private和no-store，共10条 |
| 资格/角色读取边界 | 6个Application GET404各缺private和no-store，共12条 |

Admin匿名真实浏览器401、缺元数据Node403、两项权限正式撤销/重授及Session保持等本轮所列非缓存断言完整执行，没有旧匿名预期硬失败；原43项也无新增非缓存失败。其它通过项不抵消这些失败，不补代理头、不跳过或放宽断言。普通633项Vitest＋89项Node、strict、同pin生成漂移、仓库独立性及报告隐私前置回归再次通过；生产build由真实runner在本轮完成，仍保留chunk体积警告。

终态后额外检查该轮全部容器（含停止）及network均为空；本地和本次远程只读核验的legacy仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。未修改后端或生产页面/测试源码，未push。Gateway当前接线已满足本阶段读取联调要求，但完整门禁仍IN_PROGRESS，需修复上述App查询错误响应头并发布后再重拉latest复验；完整UC和审核决定依赖不因此关闭。
