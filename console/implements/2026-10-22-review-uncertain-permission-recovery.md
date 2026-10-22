# UC006–007：结果未知后读取权限撤销的真实恢复

状态：`ACCEPTED / IN_PROGRESS`，2026-10-22，按用户持续授权自行决定并接受。承接[已发布审核决定接入](2026-10-16-admin-review-decisions.md)，实现/验证UC006 BR-CRV-001/003/004和UC007 BR-CRV-005/008的一个实际故障组合，不缩减完整审核用例，不改App/Auth/Gateway业务规则。

## 范围与准备决定

现有52d边界加固只有组件证据，原12项真实决定尚未串起unknown→权限撤销→重读403→重新获权恢复。本包追加两项真实生产React场景，分别覆盖Version/Profile。复用现有主双权限Reviewer、Session和正式Create/Submit资源：`resources[0].versions[2]`与`resources[3].profile`，在原12项后执行并先确认实际PENDING/eligible，亦核对前一项owner恢复已生效。不增加注册、EMAIL/DEVICE、BrowserContext、业务App、quota或读取seed；既有owner的26查询App＋4决定App已经达到测试配置30的上限，不能为方便测试扩大它。

新增四个固定loopback bearer控制，仅针对本轮主Reviewer，以有限相位0→撤Version→授Version→撤Profile→授Profile执行。请求只允许精确POST路径、application/json、空对象、无query，不接收subject、permission、revision、数据库或URL。与原单项V Reviewer的revoke/regrant控制分开，不改变原资格/权限相位。正式Auth查询校验subject、两条完整不同权限行及精确revision；只改变目标一项，另一项保持true。每个写按已读revision做CAS、写前登记pending，回执丢失或读回失败后只读确认原相位，不重放未知写；同相位并发共享promise，错序或混合状态失败关闭。该控制是测试准备，不是治理UI。

## 两项真实场景

1. 打开实际PENDING且eligible的目标；同context另一标签页预先打开另一能力的既有终态详情（Version故障对应已拒绝Profile，Profile故障对应已批准Version）。两页仅复用浏览器正常Cookie，不复制钥匙或storageState。
2. 正常填拒绝理由并预览，只提交一次；透明代理对该精确决定POST执行RESPONSE/TRUNCATE。必须同时观察真实上游200、实际正文截断及生产React的RESULT_UNCERTAIN，不能只根据gate状态推断JS失败。
3. 正式撤销目标能力，再键盘触发“重新读取同一 Review”。捕获同一精确三元路径GET的403、完整cap对应PERMISSION_REQUIRED reason及private/no-store；目标页须聚焦不可访问标题，说明结果仍无法确认、勿据此重发，并移除原表单、理由、snapshot、检查项和提交按钮。
4. 另一能力已加载的DOM保持；其明确刷新仍获真实200。权威Session、设备钥匙保持原值，没有DELETE Session或新增决定POST。浏览器DOM/网络证据不冒称同一QueryClient内存或全heap保证。
5. 正式重授目标权限，在原目标页按“重新读取”获得同一Review实际REJECTED终态及原理由；不重新提交，不把刚恢复的访问当作新决定成功。表单仍不出现，另一能力和Session继续保持；两case结束后主Reviewer精确双权限恢复。

## 验证与完成边界

固定控制相位、CAS、重复调用、丢回执、读回不可用、错序/非目标权限变化及敏感错误包装先做Node合成回归，不能当作真实治理写证明。普通回归、strict、官方固定pin漂移、Edge通过后冻结运行时/spec；每轮重新pull已发布latest，先14项决定专项，再无参数102项完整门禁。原Application管理25条缓存头断言全部保留，不代理补头、不回退本地镜像、不在运行中改源。

每例仅清理自己的页面和故障gate，finally尽力恢复已尝试撤销的固定权限。HELD可释放；ARMED不得通过重发业务POST消耗，应明确失败并终止该轮后续serial场景，最终整体清理隔离环境。TRUNCATE之后不能为清理再写相同决定。任何失败、准备未执行或serial skip均按实际记录，不算通过。

本包只关闭上述两种权限恢复组合的证据缺口；不同修订公开指针并发、加载后关系冲突、策略退休、Scope/全部依赖故障、全部Session交错及UC001/fencing仍OPEN。发现真实产品缺陷时按最小范围修复并追加红绿证据，不能以两项通过关闭完整UC。

## 实施与预检

Console源码冻结于`dcdb08f`。本次仅增加固定准备控制和两项真实spec，无产品UI变更。统一903项Vitest、143项Node回归全部通过，`pnpm typecheck`、`pnpm generate:check`（官方同pin输入）与`pnpm edge:e2e`均exit0；Node新增11项只证明相位/CAS/错序/未知回执及固定subject接线，不代替真实Auth治理。已启动published-latest专项，实际终态尚待记录；不把预期14/102写成通过结果。运行时、runner和spec在轮次期间冻结，未push。
