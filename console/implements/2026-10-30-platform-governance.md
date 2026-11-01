# Admin 平台人员治理与应用运维接入

状态：`IMPLEMENTED / FOCUSED_LOCAL_VERIFIED / REAL_REPRESENTATIVE_VERIFIED`，2026-11-01。依据既有自主设计和实施授权接入 [UC-CONSOLE-015](../use-cases/UC-CONSOLE-015-manage-platform-governance.md)。412805 已通过真实治理代表链，见文末；下方初始验证与待验收描述为历史阶段，不把代表链扩大为全部角色组合或完整 Console 门禁。

## 实际范围与自主决定

Admin 主框架已增加“审核 / 平台治理”任务导航，既有版本审核、资料审核业务组件保持原职责。新增 `/governance/personnel` 与 `/governance/applications`；登录本身仅表示 Session 已建立，首页不再把它描述成已具备管理员资格。页面沿用 Tailwind、HeroUI 和同一亮/暗骨架；主题只改变语义外观，不复制业务页面。

人员治理分为平台管理员、应用审核权限、应用运维权限、账号状态、Developer 资格五个分区。管理员名单消费真实 `ListPlatformAdministrators` 分页，其余使用明确 Auth ID 的目标表单，不提供不存在的用户搜索或全平台用户表格。Application 运维使用明确 Application ID 的状态表单，不从 Developer 所有权列表或审核队列拼造全平台应用目录。

能力发现按实际后端入口处理：

- BrowserSession 不包含 role/permissions。`GetPlatformAdministrator(self)` 仍要求完整平台管理资格，没有普通用户 self 例外；合法 ACTIVE / GRANTED / effective 响应只证明固定管理 bundle，不证明审核或 App 运维执行权。
- 已确认完整平台管理员后，使用权威 `GetApplicationOperationsPermissions(self)`，分别按两项 `effective` 控制暂停和恢复。平台管理员没有自动 App 运维权，不从 suspend 推出 restore。
- 独立非平台管理员运维人员仍可以按已知 Application ID 读取状态。现有状态 GET 只能证明至少一项运维权限，无法区分具体哪项；权限发现失败时页面明确说明这一限制，不展示猜测所得写入按钮，不为探权发送命令。本包没有修改 Auth/Gateway 契约，也没有自行新增能力发现 RPC。

功能影响和服务端保护仍引用 UC015 所链接的 Auth UC004/021/022/023/027 与 App UC028。前端不实现另一份最后管理员计数、不绕过 blocker、不把账号恢复解释为旧 Session 复活，也不把 App 恢复解释为可运行保证。

## 产品边界

| 部分 | 实际实现 |
| --- | --- |
| API 客户端 | `packages/api-client/src/governance-client.ts`，覆盖 14 个普通 ADMIN 方法；原生成资源保留在 `kind + resource` 判别结构内，没有手写第二套业务 wire DTO |
| 人员治理 | 平台管理集合授予/撤销、两项审核权限独立授予/撤销、两项 App 运维权限独立授予/撤销、账号禁用/恢复、Developer 暂停/恢复 |
| App 运维 | 专用状态读取；已权威确认的精确权限才显示对应暂停/恢复动作；生命周期与平台可用性分开消费 |
| 私有 runtime | `apps/admin-console/src/governance-runtime.ts`，独立人员治理、App 读取、App 暂停、App 恢复 attempt；不注册到 Reviewer `versions` / `profiles` 的拒绝范围 |
| 页面与导航 | `governance.tsx` 及 `app.tsx` 两路由接线；已知 ID 先明确读取，短确认包含目标、动作、影响与原因；编辑目标或离页清除原确认 |
| Session 清理 | `private-read-core.ts` 仅在整代 Session 范围匹配中追加 `admin-governance` 根；Reviewer 能力限定匹配不扩大到治理 |

官方 API 输入仍固定 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。依 UC015 清单通过官方生成流程追加 Auth `platform_administrator/platform_administrator.proto`、`application_operations_permission/application_operations_permission.proto` 与 App `application_operations/application_operations.proto`、`application_operations/error_reason.proto`；原 reviewer/account/developer_management 生成输入复用。生成和 barrel 接线由主 agent 集中处理，本包未手工修改生成类型。

客户端使用同 origin 普通 HTTP/JSON、标准 ProtoJSON 与精确 bigint OCC。审核授权写 `expectedRevision`，平台及运维授权写 `expectedPermissionRevision`，账号/Developer 使用各自修订；App 同时发送同一次读取的两个 expected revision，并按 `body: command` 直接序列化内部命令，不加错误 envelope。GET 无 body/query；POST 查询保持正式方法。管理员名单游标按服务端返回使用，顺序校验采用 UTF-8 字节序，不把 JavaScript UTF-16 字符串比较当作后端字节排序。

## 确认、读取与安全退场

所有写入都要求当前目标专用成功读取、非空合规原因和明确确认；一次确认只发一次命令。正常 UI 不显示或要求输入 revision，没有自动写、批量串行授权或未知写重试。客户端核对 ACK 的目标、动作状态和准确修订变化；权限 ACK 还检查未选择的另一项未被改写，App ACK 检查 lifecycle 未被改变并有新操作回执。

已确认 ACK 与后续 GET 分开表达。失败读回不会把已确认命令改称未执行；未知命令不声称成功或失败，暂停后续写入，仅提供明确只读核对。读回当前事实不证明原未知请求由谁完成；后续动作须重新确认。自我撤销完整平台资格后退出人员治理，不清理独立 Reviewer/Session；自我禁用时以 Session 安全退场优先，不为了显示 ACK 绕过会话复核。

读取下界按目标与版本种类隔离，平台、审核和运维授权共享 permissionRevision 下界，账号/Developer/App 不混用。ACK、已采用 GET、当前缓存和已读取管理员名单中的更高修订只提升下界；失败、较旧响应和替换 Query 不能使其回退。App 另保留 lifecycle 修订下界。

每次请求捕获当前 Session/attempt 生命周期；采用或改写缓存前核对捕获的 Query 对象与 data 身份。目标变化、旧 Session、同 key 新 Query 的迟到响应不覆盖当前内容。能力查询与手填目标查询使用不同 purpose，每个读取组件再有独立 readId；成功快照不因焦点、重连或同 key Query 重新挂载而隐式重读，新的读取组件和明确“重新读取”仍执行正式 GET。

治理 403 不清理 Reviewer 或 Cookie；Reviewer 403 不清理治理。App 单项命令拒绝只关闭对应动作，不抹去仍可读状态。明确目标 404 清除目标快照与原因，不合成为未授予/正常账号。真正 Session 拒绝走既有整代恢复，新加治理根随旧 Session 清理；旧 clear ACK 不能清理替换 Session 的治理或审核 Query。

## 集中定向验证与修正过程

遵守用户集中必要验证的偏好，没有每次 UI 修改后运行整套测试，也未在本包运行 build、重写 dist、操作预览容器或提交代码。

| 证据 | 结果与范围 |
| --- | --- |
| API 客户端最终定向 | **34/34**，覆盖六类专用读取、正向及反向命令、精确大整数与 JSON 绑定、错目标/错修订/另一项权限被改写等 ACK、404/403 不吞空态、实际名单游标、最后管理员冲突与未知不重放 |
| 新治理 runtime | **9/9**，覆盖治理与 Reviewer 双向隔离、真实 Session 全范围恢复、单项 App 动作隔离、旧 Session 迟到结果、Query 对象/data 身份、确认下界、不同版本种类与双 App 下界 |
| 新治理组件最终定向 | **16/16**，覆盖五分区/已知 ID、明确确认和重复点击、实际 GET 核对、未知只读恢复、ACK 后失败/旧读、替换 Query 与低读回、换目标、ops-only 不猜写、精确 effective、自撤、最后管理员拒绝、self 双查询身份、目标 404、旧 Session clear ACK |
| 原 Admin 读取与 Session 定向 | **209/209**；首轮集中批次保留原 private-read-core、private-activation、session、session-entry、review-decisions、reviews 断言 |
| Admin strict | 最终 `tsc -p apps/admin-console/tsconfig.json` exit0 |
| 文件检查 | 限定 diff 检查与新文件尾随空白检查通过 |

首轮客户端 **28/28**、Admin strict 通过；Admin 集中 **230 项中 228 通过、2 失败**。两项失败都发生在新治理组件：DISABLE 成功后动作变为 RESTORE，按动作设置的 React key 卸载原命令组件，使成功核对反馈消失；实际 GET 和目标状态已经正确更新。修正为目标层保留完成反馈，单状态动作保留组件身份，没有删除原成功反馈断言。

同轮静态核对另发现，自能力查询与用户明确输入自己的目标查询可能共用同一个 key，目标重读会牵动资格区刷新与草稿生命周期。随后将 capability / target purpose 分开，并增加 self 表单稳定性回归；该问题不伪记为首轮失败原因。

追加反向命令与必要边界回归后，客户端 **34/34**、Admin strict 通过；新治理 **25 项中 24 通过、1 失败**。失败来自替换 Query 回归：旧 ACK 已被对象身份保护拒绝，但同 key 新 Query 重新挂载触发隐式读取，低修订被下界挡住后原命令核对区被卸载。修正每个读取组件的 readId 与显式重读语义，继续保留 replacement=99、旧 ACK=2、旧 GET=2 不得覆盖的断言。最终 runtime + 组件 **25/25**，Admin strict 与文件检查再次通过。没有用重复重跑、重试或放宽低修订断言掩盖失败。

上述 34、25、209 是各自有界定向证据，不是同一轮默认全量总数；后续全仓 ordinary test/typecheck/官方生成漂移/build 由主 agent 集中运行并另行登记，本文当前不声称这些门禁已经完成。

## 尚未关闭的事项

- 本包没有 UC015 真实浏览器治理链证据。正式普通入口上的授权变化、账号禁用恢复、Developer 暂停恢复和 App 暂停恢复，需要隔离账号/应用与真实镜像单独验证；合成 ACK/GET 不替代后端事务、最后管理员保护或权限传播窗口验证。
- 非平台管理员运维人员的精确自身能力发现仍缺，依 UC015 保留最小依赖；可读状态不等于全部运维角色已完整接入。
- 未新增初始化、应急恢复、全平台搜索、审计查询、Scope/学年编辑、批量操作或后端治理契约。真实 spec 后续追加和运行的状态不能由本记录预先推定。
- 本包无独立 commit/push；最终源码冻结点和整体门禁结果由主 agent 在实际执行后记录，不能将本页实现状态当作完整 Console goal 已完成。

## 2026-11-01 真实代表链

冻结 Console `d5cc071`，发布 Auth `518b0917…`、更新 App `18eacd03…`、显式本地 Gateway `90cf10f0…`，412805 中治理场景 **1/1 通过，26.6 秒**。真实 Admin React 完成平台资格授予/撤销、两项审核权限各自授予/撤销、两项运维权限各自授予/撤销、Developer 暂停/恢复、账号禁用/恢复，以及 App 暂停/恢复，共 16 次正式命令与后续专用 GET。管理员名单和禁用账号的 Developer 下一实际请求 401/精确退场均核对；原 Session 保持、零外部请求成立。

App ACK/GET 时间差异由后端 `5b42ed7` 修复后，发布镜像上的完整资源严格比较已通过，见 [交接与复验](2026-10-30-app-operation-time-readback-gap.md)。同轮三文件总结果仍 exit1，不能以本场景通过覆盖其它隔离失败；完整门禁与非平台管理员精确能力发现依赖仍开放。没有新增治理后端规则、编译相邻源码或 push Console。
