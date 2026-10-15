# UC002：Application 累计分页与正式错误恢复

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。本包开始实施，仍须独立红绿与真实验证；保留既有App详情404 no-store缺口。

## 已核对的问题

`applications.tsx`仍比较短reason `INVALID_APPLICATION_MANAGEMENT_PAGE_TOKEN`，正式固定API wire为`ERROR_REASON_INVALID_APPLICATION_MANAGEMENT_PAGE_TOKEN`。下一批失败有上下两个错误入口，累积旧data和“加载更多”仍可能保留；400/成功协议错误未精确退场，后续503可能重新显示已拒绝旧投影。成功列表没有正常每批asOf，client直接fromJson会让缺items/asOf的成功对象成为默认投影或暴露原解码错误。API fixture还把非法`archiveStatuses:["ACTIVE"]`作为正例，须修为真实归档枚举而不改序列化契约。

依据为[UC-CONSOLE-002](../use-cases/UC-CONSOLE-002-query-owned-applications.md)、[UC-APP-029](../../app-center/use-cases/UC-APP-029-query-owned-application-management.md)与[私有读取边界](../query-contracts/private-read-boundary.md)。不增加写UI或管理员资格；默认生命周期仍只含ACTIVE/CLOSING，保留上一包已修正的默认文案及关闭历史摘要。

## 实施决定

1. 正式wire reason先取红；列表保留累计加载更多，唯一错误恢复入口。400/成功协议错误先遮蔽并精确清当前Query data，旧行、旧token和时间投影一起退场；之后503不能复活。仅明确重读或新成功恢复，不注销Session、不建权限黑名单，也不驱逐其它Session/无关Query。明确错误不随focus/reconnect自动重试。
2. 两个RPC对必要成功结构及fromJson失败统一静态ApiResponseError；request await在解码catch之外，真实fetch/正文TypeError、AbortError及HTTP ApiError原样分型。列表应有items/asOf且每项application存在；详情应有核心application、counts、profileState/filterState及正常数组/asOf。必要投影按正式DTO核对，不手写第二业务类型或把合理optional缺省判错。
3. 正常累积每批独立asOf；同上下文网络/5xx保留原批及原时间、可明确重取下一批。从头刷新仍可主动丢弃旧分页，不把它宣称为同批恢复。子/集合权限拒绝继续由已有attempt边界处理。

## 真实准备与验收

仅测试runner设置正式已有配置`APP_CENTER_INITIAL_APPLICATION_QUOTA=30`，专用真实注册/Developer/DEVICE账号顺序正式Create25个`Console_Owned_Page_01`…`25`。不seed owner/quota或附属资源、不改生产默认10；配置只用于新owner懒建quota，现有生命周期fixture仍以usedCount4/revision4及limit>=4校验。按真实Create的createdAt/applicationId降序排序，不假设毫秒级同时间时单纯倒序创建一定等于后端顺序。注册准备继续遵守真实限流和有界重试，不放宽Auth配额。

生产React验证20+5累计、无重复、首批重置、正常独立时间、空筛选、Session/设备不变；第二批单次真实200正文TRUNCATE用独立原生探针证明TypeError，再验证React原20项/asOf保留及明确续批恢复25。400/协议错误退场、后续503不复活和精确Query实例保护由组件/核心证据补齐，不向真实页面注入假响应。

原生同源探针使用真实opaque token验证坏编码、换调用者、真正不同的生命周期/平台/归档筛选400，以及改变pageSize合法续读。UC029 token绑定caller、规范化filter、createdAt/id和版本；空默认与显式ACTIVE+CLOSING等价，token不是授权结论。当前实现未HMAC且不绑定ownershipRevision/父App，不能套Tester的revision失效或“改任意合法位置必400”，也不造Version/Tester式父App token混用断言。没有本能力正式Profile预算413，不制造超预算验收。

2026-10-16 实施补充：换调用者探针使用独立仅注册的`ownedPeer`账号，不复用完整套件已经登录的转让接收者，避免依赖spec执行顺序绕过邮箱60秒冷却。新账号同样计入准备阶段的实际mail-ready时间；不提高Auth限流或重试未知写入。Create返回的Timestamp可含亚毫秒，而Mongo BSON Date排序仅精确到毫秒；准备器以bigint秒精算、仅截亚毫秒后检查safe integer，返回真实持久排序精度的`createdAtUnixMs`，不因合法nanos拒绝准备，也不假设创建顺序等于查询顺序。

每轮重新pull已发布latest、轮内固定digest，不编译相邻后端。保持成功/空态/错误private/no-store、报告隐私、惰性标识和仅内存token；focused与无参数完整门禁分层，记录失败、资源清理和本地提交，legacy不变。本包不关闭资格下降/角色矩阵、UC001/fencing或UC006–007。

## 实施与验证进展

正式wire reason/旧投影/每批时间组件先7红，必要成功DTO/静态协议错误client先21红，实施后Application组件25＋核心5、client45定向全绿。普通`pnpm test`为512项Vitest＋56项Node全绿（含7项新准备器合成测试），strict types、生成漂移、fixture浏览器8通过/4个Admin非目标跳过与Edge检查均通过。产品提交`2c55fe1`；准备和真实专项仍待独立结果，不以这些组件/fixture证据宣称真实完成。

首次专项命令错误地额外传了`--`，runner参数校验在创建环境之前拒绝，exit1；类型及报告隐私测试通过。修正为`pnpm test:real tests/real/owned-application-pagination.real.spec.ts`重新开始，不能把未启动一轮算作镜像联调失败。

### Focused 真实结果

轮次`iwut-console-real-833217`：三项中2通过/1失败，浏览器13.5秒。25个正式Create的真实排序、20+5累计、键盘分页、独立asOf、非空token的从头/筛选重置、真实空筛选和无附属资源详情合法默认值通过；两次独立单次TRUNCATE分别证明原生200正文TypeError及实际React原20项/时间保留、明确同cursor恢复25。两方Session/设备不变且无DELETE/外部资源/补查个人资料/业务写入。

第三项全部功能探针均执行：坏base64、不同生命周期/平台/归档filter、不同caller得到正式reason的400；改变pageSize=2和空默认等价显式ACTIVE+CLOSING合法继续读第21–22项，独立非Developer peer默认列表真实为空。失败恰为5个400响应各缺private与no-store的10条soft断言（第200/201/220/221行）；soft仅用于收齐其余证据，最终exit1，不能记为三项全通过。扩展确认App管理读取错误响应头缺口不限于此前Get404；不在Console临时补头或删断言掩盖，后续须新App镜像修复后重跑。

本轮重新pull的Auth/App/Gateway image ID分别为`sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、`sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、`sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，均与上一轮相同；Mongo/Traefik仍沿用该轮已打印固定标识。不编译后端；下一步无参数完整门禁，不能用focused替代。
