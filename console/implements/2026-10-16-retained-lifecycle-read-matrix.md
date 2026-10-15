# UC002–005：保留生命周期历史读取矩阵

状态：`ACCEPTED / NOT_STARTED`，2026-10-16，按用户持续授权自行决定。下一独立工作包；本轮仅设计，尚无实现或测试通过证据，不关闭此前App详情404响应头门禁。

## 范围与依据

落实[UC-CONSOLE-002](../use-cases/UC-CONSOLE-002-query-owned-applications.md)至[UC-CONSOLE-005](../use-cases/UC-CONSOLE-005-query-application-tester-management.md)中保留历史可读的验收。权威为App UC029/034/037/039，不重定义关闭、平台暂停、归档或授权。三个App状态维度正交；当前/最后adminId的读取权不能因CLOSING/CLOSED、SUSPENDED或ARCHIVED被前端抹去。只有UC029默认列表排除CLOSED；明确筛选及深链接仍可读取历史。

资格下降、独立Reviewer/运维角色、UC002大列表分页、UC001并发与Admin UC006–007仍另包。本包账号保持真实APPROVED，不把PENDING/REJECTED/null加ACTIVE资产构造为当前正式命令可达场景，也不借WITHDRAWN绕过归属退出屏障。

## 准备与真实性分层

专用真实注册/Developer/DEVICE账号正式Create四个App，建立真实ownership/quota且不超过默认10个配额。分别覆盖AVAILABLE/SUSPENDED×UNARCHIVED/ARCHIVED四格，再在三个读取阶段覆盖ACTIVE/CLOSING/CLOSED共12组合，不需要12次Create。归档可复用已生成API及已验证的正式准备命令；平台暂停和关闭历史明确使用validator约束的只读fixture，不宣称其治理/关闭命令执行。

当前Console runner未启用关闭/近期认证端点，也未接完整current-password＋新设备签名证明准备及App→Auth关闭调用授权。本包不得开启关闭工作流、签造proof/JWS、用旧device-only测试替代新认证门禁，或伪造Auth RPC成功。CLOSED fixture中的APPLIED/receipt仅为App历史读取输入，不是实际Auth已建立tombstone或应用token已撤销的证据；不验收运行、OAuth、关闭worker、真实配额释放命令或跨服务收敛。

每App准备最小合法Version+一对一OAuth、Profile及Tester历史，保持领域关系而非只满足BSON。平台状态须有匹配revision/event及必要outbox，归档保持其revision/audit；CLOSING/CLOSED必须有同App匹配closure，source revision与lifecycle revision对应，adminId/ownershipRevision保持。App fixture阶段迁移须在隔离Mongo事务中CAS固定四App/当前阶段，CLOSING阶段只一次把该账号usedCount从4改0，不让CLOSED再扣；这是read-fixture一致性维护，不是正式关闭命令证据。

关闭历史保留Version/Profile/Review与ACTIVE Membership；原ACTIVE链接应改为REVOKED/APPLICATION_CLOSURE，不为了页面方便保留可用加入链接。本包无OAuth registration/待转让时不凭空制造它们；不能省略合法closure去迎合详情错误。关闭worker保持关闭，不能因fixture nextAttemptAt意外发出协议调用。

## 最小验证矩阵

1. 生产React分别在12组合读取Application详情、Version列表/详情、Profile列表/详情与Tester三区域；逐响应验证真实200、各自asOf、private/no-store及固定fixture身份。状态仅由App投影呈现，历史读取不产生写按钮或恢复/上线暗示。
2. 默认owned-list在ACTIVE/CLOSING各含四App且不因ARCHIVED/SUSPENDED被隐藏；CLOSED阶段默认空，明确CLOSED与已有平台/归档筛选能找到对应历史，筛选重置token。App默认排除CLOSED不能被前端误解为永久丧失历史管理权。
3. 每阶段Session public binding/generation保持、无DELETE及Auth个人资料补查；runtime/OAuth/opaque ID仍惰性，正文与token不进入Web Storage/前端URL。附属空态、成员保留及关闭链接历史分别验证，不把容量从首屏行数推算。
4. 测试control仅本轮loopback随机bearer、固定phase和空JSON，内部持有固定四App；禁止任意ID、URL、认证材料或Mongo语句。真实spec沿用报告隐私fixture，不接入产品QueryClient，不拦截或伪造业务响应。

先以真实镜像暴露分支差异；若需改产品，先补对应失败回归再修复。每轮重新pull已发布latest、轮内固定digest，不编译相邻后端。focused、普通/类型/生成检查、无参数全量、资源清理与本地提交分层记录；完整门禁继续保留已知App404 no-store断言。
