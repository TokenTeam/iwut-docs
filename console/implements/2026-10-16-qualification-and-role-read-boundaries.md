# UC002–005：资格下降与非管理员角色读取边界

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。累计分页包无参数39项门禁已终态37通过/2错误头失败并清理，本包现在开始独立实施；不把只读调查或接受决定记作实现，保留已有App错误头缺口。

## 目标与权威

验证当前Application管理员在Developer暂停和恢复后仍可读取UC002–005，而审核人员、Tester本人及平台治理者不因角色取得他人的管理投影。引用[UC002](../use-cases/UC-CONSOLE-002-query-owned-applications.md)、[UC003](../use-cases/UC-CONSOLE-003-query-owned-application-versions.md)、[UC004](../use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md)、[UC005](../use-cases/UC-CONSOLE-005-query-application-tester-management.md)；授权继续由[App UC029](../../app-center/use-cases/UC-APP-029-query-owned-application-management.md)、[UC034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md)、[UC039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md)和[UC037](../../app-center/use-cases/UC-APP-037-query-application-tester-management.md)拥有。

不得从名称、seed中的reviewer归因字段、拥有一个Session或其他fixture中的testerAuthId推断正式角色。本包不用当前`ownedPeer`充当Reviewer/Tester，也不改变既有测试账号角色。

## 正式准备决定

使用四个独立真实注册账号：A为Developer/当前owner，G为平台治理者，R为两项Reviewer权限持有者，T为该App的ACTIVE Tester。选择四个而不是让A兼任治理者：多一个测试账号能直接验证平台管理员也无隐式读取权，并避免A读取成功混合owner与治理资格解释。G/R/T均不Apply Developer；原`actor()`会自动Apply，不能用于其普通身份准备。

1. 在隔离Mongo与本轮重新拉取的同一Auth `latest`镜像上，按[Auth UC021 / BR-ADM-005](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-005)停Auth容器，执行一次性`bootstrap-platform-admin --auth-id G`，校验成功后重启原Auth容器并等真实入口就绪。不启动第二个监听实例，不直接改权限、审计、bootstrap消费标记，不把运维CLI伪称浏览器功能。
2. G以真实Session经现有内部Gateway SESSION路由，按[Auth UC004](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md)分别正式授予R `app.profile.review`和`app.version.review`，以真实查询的共享permissionRevision逐次CAS；验证两项都已授予。平台权限不自动等于Reviewer权限。
3. A正式Apply Developer、DEVICE登录并Create一个专用App；再按[App UC002](../../app-center/use-cases/UC-APP-002-create-application-version.md)和[UC013](../../app-center/use-cases/UC-APP-013-create-application-profile-revision.md)各正式创建一个最小DRAFT Version/Profile。Version使用RPC范围[1,2)、合法惰性URL、空capability/scope和显式空OAuth数组；Profile用明确displayName和显式null description/icon。固定API生成DTO，正文按正式body映射，不seed owner/quota、依附数据或工作指针。
4. A按[App UC008](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)正式创建首条链接；Node内存解析joinUrl后，T以自己的真实注册Session或不Apply的DEVICE登录，按[UC009](../../app-center/use-cases/UC-APP-009-join-application-as-tester.md)正式Join，验证新ACTIVE episode与capacity=1。secret/joinUrl不放入REAL_FIXTURE、控制响应、文件或日志，浏览器不访问凭证落地页。
5. 仅测试实例开启已有`AUTH_DEVELOPER_MANAGEMENT_ENDPOINTS_ENABLED=true`，其它恢复就绪配置沿用现有真实邮箱准备。G按[Auth UC023](../../auth-center/use-cases/UC-AUTH-023-suspend-and-restore-developer.md)真实查询A的developerRevision，分别SUSPEND/RESTORE并查询确认。该UC不要求密码/新签名/high-risk proof，不套App关闭的近期认证。未知提交先查询，不自动重发状态变更；不降低限流。有限loopback bearer控制只协调固定A/阶段，不能成为任意治理代理。

需要的developer_management、reviewer_permission、tester_membership Proto已经在固定`a5d504c058c62cd91be451074d21608d69789918`中。仅同pin增加生成输入并通过漂移检查，不手写第二DTO、不升级API。注册账号全部计入既有真实邮件冷却及有界PASSWORD_RATE_LIMITED重试；私钥/Session留Node闭包，公开fixture仅含合成邮箱、opaque ID和核验所需的非敏感状态/版本。

实施安全补充：控制权限只覆盖本轮固定A的revision1→2→3，不允许恢复后再次SUSPEND写出revision4才由公开投影拒绝。写前核对允许的源状态/版本；相同已达目标只观察，未知写入继续只读确认。真实spec另验证缺/错bearer、非POST、query、非空/数组正文和未知phase在进入治理前被拒绝，随后正式观察仍为APPROVED/revision1。不增加生产路由或任意治理代理。

## 分层验收

- 准备器合成测试先红后绿：精确生成请求、普通账号不Apply、治理CAS、不重试未知写入、secret不返回/落盘、错误静态化；不当作真实业务证据。
- 原生同源真实读取：A在APPROVED→SUSPENDED→APPROVED三阶段读取owned-list和八个管理RPC；G/R/T的owned-list为正常空页，对A的八个管理RPC均统一404。确认Reviewer grant、ACTIVE Membership及正式暂停事实，不只靠账号命名。
- 生产React：A暂停前后走完管理详情、Version列表/详情、Profile列表/详情、Tester六类页面，恢复后重新真实读取；G/R/T分别访问六类深链均统一不可访问，无旧正文、计数、指针、分页或写按钮。Session public binding/generation和非可导出设备不变，无DELETE/外部资源/个人资料补查。Query精确内存与迟到Promise仍由已有组件证据承担，不扩大为全heap保证。
- 成功、空态、404保留private/no-store断言；已有App Get404/List400缺头不因本包放过。专项之后仍运行无参数完整门禁，每轮pull latest、记录digest及资源清理，不编译相邻后端、不提前push。

## 非目标与后续边界

不开放Admin治理/审核页面、Reviewer queue/decision、Tester客户端加入页或任何生产写UI。正式写命令仅用于隔离测试准备，不等于交付相应前端UC。PENDING/REJECTED/null owner不是正常Create后下降路径，不用seed制造；WITHDRAWN涉及正式归属退出屏障及资产处置，另包，不把SUSPENDED当WITHDRAWN替代。账号DISABLED也不等于资格下降，本包不验证或改变其Session失效规则。上层UC001/fencing、UC002–005完整并发矩阵及UC006–007不因接受本包而关闭。

## 实施与验证进展

固定API同pin扩充三份Proto生成输入和对应产物，未升级`a5d504c`、未手写业务DTO或开放生产治理client。准备器初始接口存在性1红后实现（仅证明接口缺失）；正式G/R/T非Developer查询缺失再取1业务红，权限revision默认0/Tester limit非100也先红后绿，不把接口红扩大为全部协议红。最终12项资格准备合成测试覆盖四真实DEVICE请求形状、仅A Apply、两独立grant共享revision、null Profile/空OAuth声明、正式Join与secret保护、权威重读和未知状态提交不重放；8项bootstrap合成测试覆盖原容器归属/镜像/网络、停服与CLI次序、未知结果/清理/重启就绪失败及中断，不当作真实后台角色证据。

普通`pnpm test`终态512项Vitest＋76项Node全绿；strict types、同pin生成漂移、fixture浏览器8通过/4个Admin非目标跳过及Edge检查均通过。四项真实spec已写好，先进行独立focused再无参数全量；准备器/runner/spec在真实轮次中冻结，不提前登记真实通过。

### Focused 真实结果

轮次`iwut-console-real-857321`，专项4项终态**3通过/1失败**，52.2秒，exit1。正式停服CLI bootstrap、同一Auth容器重启就绪、G经Gateway两项grant/权威查询、A正式Create App/Version/Profile及T真实Join全部成功，不依赖Auth资格/权限或App依附seed。A三阶段APPROVED1→SUSPENDED2→APPROVED3各自完成owned-list＋八RPC和六类生产React页面，Session/设备不变。

第4项G/R/T三个角色的正常空owned-list、对A的八RPC统一404及六类React深链隐藏、最小错误内容、无写按钮/个人资料补查/外部请求/DELETE、四方Session/非可导出钥匙保持均执行通过。唯一失败为每角色各一次原生/一次React Application GET404均缺private和no-store，即6个响应×2共12条soft断言；Version/Profile/Tester隐藏响应头通过。soft只用于收齐其它证据，未删除断言或把整项记为通过。

本轮Auth/App/Gateway image ID依次为`sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、`sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、`sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；Mongo`sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`、Traefik`sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。全部按本轮重新pull打印，未编译后端；终态后额外查询匹配containers（含停止）和network均为空。

专项终态后才继续有限phase写前护栏与控制HTTP负例，不在运行中改源码。最终源码仍须普通回归和无参数43项全量；本专项不是最终源码完整门禁，不能提前关闭本包或既有App错误头缺口。

### 最终源码回归与镜像接入复核

有限phase写前护栏新增第13项合成测试先红后绿，验证正式恢复到revision3后拒绝再次SUSPEND、外部revision9漂移不触发写入。最终源码普通回归512项Vitest＋77项Node、strict types通过。首次生成漂移检查因远程Git传输低于速率下限而超时（curl28、early EOF、index-pack失败）；原命令终态失败后仅重跑`pnpm generate:check`，同pin检查通过，未放宽网络期限或改成本地API输入。

用户通知Gateway CI完成后，独立`pnpm edge:e2e`再次pull已发布`latest`，实际image ID仍为上述`a048de73…`。镜像内`/gateway-config --render`成功；九条Developer管理路由存在、两个Session入口与静态入口分流、私有ForwardAuth不可公开访问，认证上游不可用时管理API fail closed。该检查不是成功业务读取的替代证据，也不声称新增镜像版本已经发布。

冻结源码`f003d0e`的无参数43项全量轮次`iwut-console-real-865240`终态为**40通过/3失败**，10.6分钟、exit1。正式准备、控制HTTP负例、A三阶段和其余37项通过；转让场景3条Get404 no-store、owned分页5个List400各缺private/no-store的10条soft断言继续失败。

角色场景本轮不能记作全部功能通过：G的原生八RPC及前五类React隐藏已执行，但Tester页并行请求中某一明确拒绝会触发正常共享退场、取消兄弟请求；测试固定等待overview响应头后读取其正文，在G阶段发生正文读取失败。此外G的Application原生/React GET404共4条缺private/no-store的soft断言已收集。后续R/T及该项末尾四方Session断言未执行，不能沿用focused证据声称本轮收齐，也不能把第三项归为仅缺响应头。终态后额外查询本轮containers（含停止）与network均为空。

仅在上述终态及清理后修正spec等待方式：Tester React深链等待三类真实请求中首个`requestfinished`，立即读取该完整响应并核验实际查询种类的404/reason/private/no-store；仍要求统一不可访问DOM、无私有内容/写操作/副作用及Session保持。未放过正文读取失败或用mock替代；八个原生真实RPC继续逐个完整检查。其它五类单请求页面不变，不修改生产取消逻辑或App响应头。strict real types与diff检查通过；修订后的四项专项单独重跑，不把原43项门禁改写为通过。

### 取消竞态修订后的真实复验

冻结修订`20efa21`，轮次`iwut-console-real-876561`，四项专项终态**3通过/1失败**、exit1。三阶段分别8.0/8.3/7.8秒，角色项25.0秒。控制HTTP负例及正式四角色准备再次通过；G/R/T均完成原生空owned-list＋八RPC、六类React深链隐藏、最小披露、无写操作/个人资料补查/外部请求/DELETE，以及末尾四方Session/非可导出设备和正式角色权威重读。没有正文读取硬失败，也未用catch吞掉失败；唯一12条错误全部来自每角色Application GET404原生/React各一次、各缺private/no-store。

本轮重新pull的五个image ID与前两轮相同；未编译后端、代理补头或改动生产代码。终态后containers（含停止）和network额外查询为空，仓库独立性与diff检查通过。源码和记录仅本地提交，未push；本地legacy仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。本次远程legacy只读核验遇到GitHub30秒低速超时，不能写成本次已重新核验远端。

当前完整门禁仍以此前43项40通过/3失败记录为准；修订后只有四项专项证据，未假称再次跑过完整43项。后续须App发布补齐Application管理错误响应头的新镜像，再重新pull latest、运行无参数完整门禁。该外部缺口不等于Gateway配置工具或混合认证链路不可用，也不关闭UC001/全部读取矩阵及其它前端工作包。

### 后续完整回归（当前证据）

[Admin查询阶段](2026-10-16-admin-review-queries.md)的后续无参数轮次`iwut-console-real-905126`已包含本包修订及全部原43项，共47项终态43通过/4失败（11.6分钟、exit1）。本包三阶段通过，角色项完整执行G/R/T原生/React隐藏及末尾Session/设备保持，唯一12条错误仍是六个Application GET404各缺private/no-store；不再有读取被取消正文的硬失败。因此此前“修订后仅focused”的时间点不再是本包当前验证范围。

新增Admin准备与R权限四相位撤重授已恢复原双权限，未污染本包资格事实；本轮五镜像ID同上，终态资源已清理，原管理详情/List错误头及新的Reviewer错误头仍使完整门禁失败，不能据本包功能回归通过关闭整体UC。
