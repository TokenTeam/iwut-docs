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
