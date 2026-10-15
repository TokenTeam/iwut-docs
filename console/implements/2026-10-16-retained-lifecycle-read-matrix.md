# UC002–005：保留生命周期历史读取矩阵

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。本包开始实施；仍须独立真实读取证据，不关闭此前App详情404响应头门禁。

## 范围与依据

落实[UC-CONSOLE-002](../use-cases/UC-CONSOLE-002-query-owned-applications.md)至[UC-CONSOLE-005](../use-cases/UC-CONSOLE-005-query-application-tester-management.md)中保留历史可读的验收。权威为App UC029/034/037/039，不重定义关闭、平台暂停、归档或授权。三个App状态维度正交；当前/最后adminId的读取权不能因CLOSING/CLOSED、SUSPENDED或ARCHIVED被前端抹去。只有UC029默认列表排除CLOSED；明确筛选及深链接仍可读取历史。

资格下降、独立Reviewer/运维角色、UC002大列表分页、UC001并发与Admin UC006–007仍另包。本包账号保持真实APPROVED，不把PENDING/REJECTED/null加ACTIVE资产构造为当前正式命令可达场景，也不借WITHDRAWN绕过归属退出屏障。

## 准备与真实性分层

专用真实注册/Developer/DEVICE账号正式Create四个App，建立真实ownership/quota且不超过默认10个配额。分别覆盖AVAILABLE/SUSPENDED×UNARCHIVED/ARCHIVED四格，再在三个读取阶段覆盖ACTIVE/CLOSING/CLOSED共12组合，不需要12次Create。归档可复用已生成API及已验证的正式准备命令；平台暂停和关闭历史明确使用validator约束的只读fixture，不宣称其治理/关闭命令执行。

当前Console runner未启用关闭/近期认证端点，也未接完整current-password＋新设备签名证明准备及App→Auth关闭调用授权。本包不得开启关闭工作流、签造proof/JWS、用旧device-only测试替代新认证门禁，或伪造Auth RPC成功。CLOSED fixture中的APPLIED/receipt仅为App历史读取输入，不是实际Auth已建立tombstone或应用token已撤销的证据；不验收运行、OAuth、关闭worker、真实配额释放命令或跨服务收敛。

每App准备最小合法Version+一对一OAuth、Profile及Tester历史，保持领域关系而非只满足BSON。平台状态须有匹配revision/event及必要outbox，归档保持其revision/audit；CLOSING/CLOSED必须有同App匹配closure，source revision与lifecycle revision对应，adminId/ownershipRevision保持。App fixture阶段迁移须在隔离Mongo事务中CAS固定四App/当前阶段，CLOSING阶段只一次把该账号usedCount从4改0，不让CLOSED再扣；这是read-fixture一致性维护，不是正式关闭命令证据。

关闭历史保留Version/Profile/Review与ACTIVE Membership；原ACTIVE链接应改为REVOKED/APPLICATION_CLOSURE，不为了页面方便保留可用加入链接。本包无OAuth registration/待转让时不凭空制造它们；不能省略合法closure去迎合详情错误。已核对实现：关闭端点开关不停止closure worker，worker仍每秒轮询，但只选择PENDING且nextAttemptAt不晚于当前时刻的记录。本包CLOSING固定nextAttemptAt为2100-01-01，并在phase自检中确认attempt=0和原状态未被改写，使fixture不入本轮due集合、不会触发跨服务协调；不修改后端或假称worker关闭。

## 最小验证矩阵

1. 原生同源协议分别在12组合读取Application详情、Version列表/详情、Profile列表/详情与Tester三个RPC；逐响应验证真实200、各自asOf、private/no-store及固定fixture身份。生产React每阶段读取四App管理概览，再以SUSPENDED＋ARCHIVED App走完Version列表/详情、Profile列表/详情及Tester页面。协议全矩阵与UI三阶段代表路径分别登记，不把原生探针夸大为12组合全部React交互；状态仅由App投影呈现，历史读取不产生写按钮或恢复/上线暗示。
2. 默认owned-list在ACTIVE/CLOSING各含四App且不因ARCHIVED/SUSPENDED被隐藏；CLOSED阶段默认空，明确CLOSED与已有平台/归档筛选能找到对应历史，筛选重置token。App默认排除CLOSED不能被前端误解为永久丧失历史管理权。
3. 每阶段Session public binding/generation保持、无DELETE及Auth个人资料补查；runtime/OAuth/opaque ID仍惰性，正文与token不进入Web Storage/前端URL。附属空态、成员保留及关闭链接历史分别验证，不把容量从首屏行数推算。
4. 测试control仅本轮loopback随机bearer、固定phase和空JSON，内部持有固定四App；禁止任意ID、URL、认证材料或Mongo语句。真实spec沿用报告隐私fixture，不接入产品QueryClient，不拦截或伪造业务响应。

先以真实镜像暴露分支差异；若需改产品，先补对应失败回归再修复。每轮重新pull已发布latest、轮内固定digest，不编译相邻后端。focused、普通/类型/生成检查、无参数全量、资源清理与本地提交分层记录；完整门禁继续保留已知App404 no-store断言。

## 已核对的前端缺口与实施决定

当前生命周期默认选项显示“全部”，实际发送空lifecycleStatuses数组，后端按UC029只返回ACTIVE/CLOSING。改为明确“默认（正常、关闭中）”，保留原请求语义及显式CLOSED选择，不为了文案把默认查询改为三状态。平台/归档缺省仍是真正不限制。

当前详情忽略固定API已返回的closure。按UC002已有范围补最小关闭历史摘要：closureId、状态、Auth撤销回执状态与开始/完成时间，ACTIVE无closure不显示；不补查receipt/proof/内部task，不把读取摘要解释为发起/恢复关闭权限。先取组件RED再实现，随后真实fixture只验证App返回历史事实的呈现，不把合成APPLIED字段记为Auth撤销验收。

## 实施中证据

Application组件新增默认标签与CLOSING/CLOSED摘要3项，先得到3失败/10通过，再实现后13项全部通过，Developer严格类型通过。扩展默认→显式CLOSED→重置时断言真实client输入为空/单值/空filter及首批token；不是非空真实游标的联合验收。ACTIVE不显示closure，关闭中无完成时间，两终态保留三个只读子入口且不出现关闭/恢复按钮、不DELETE Session。产品独立本地提交`df92aed`。

类型检查曾暴露测试误用Playwright的ByRole exact参数，扩展筛选断言又遇到option与badge同文定位歧义；均修正为Testing Library支持的参数及限定实际列表，未改产品状态或删断言。上述是组件证据，真实12组合协议和三阶段React仍待执行；当前不能把本包登记完成。

首轮focused在浏览器启动前由真实注册返回429/PASSWORD_RATE_LIMITED而失败，未登记任何浏览器场景通过。新增账号将同源连续密码工作量推进到21次，不能靠调高后端限额、伪源IP、删账号隔离或改Mongo密码事实绕过。已核对Auth该拒绝在创建提交前发生，正式transport返回Retry-After。测试准备仅在Complete明确这个reason且header为1..60秒时等待后最多重试一次同一序列化正文，保留operation/code/password/proof；Begin、其它429、网络/5xx/正文错误不重放未知写入，重复429或缺失/超限header直接失败。1秒等待切片保持中断可用，失败只记静态状态/reason、不保留正文/cause。该准备器新增8项Node合成回归通过；第二轮已重新pull latest开始验证，不把有界重试当作生产前端恢复策略。

普通门禁现为455项Vitest/48项Node通过，完整strict及固定API生成漂移通过；fixture浏览器8通过/4 Admin非目标跳过、同镜像Edge通过。fixture合成测试覆盖4App事务/CAS/整体rollback、Int32配额4→0与Long revision4→8只一次、实际初始coordinationRevision0（仅Archive后1）、同phase不写、worker漂移和脏关系失败关闭；这些不能替代真实validator/index/协议联合验收。
