# UC-CONSOLE-015：管理平台人员资格与可用状态

状态：`ACCEPTED`（2026-11-04 本人运维发现、2026-11-08 平台应用发现与人员精确定位修订均获用户明确接受并授权串行实现）。2026-10-30 已 ACCEPTED 的人员治理与受限运维基线继续有效；本次联动 UC-AUTH-027 的本人读取，现已由本轮用户明确接受并授权实施；不依赖先前自行接受的授权，交付/联合验收状态仍单独跟踪。

## 用户目标与权威边界

获授权人员在 Admin Console 按明确目标管理平台管理员资格、两项应用审核权限、两项应用运维权限、账号禁用与恢复、Developer 暂停与恢复，以及 Application 平台暂停与恢复。登录 Admin Console 仅建立会话，不授予任何上述资格；Reviewer 可以继续独立使用既有审核页面。

业务规则分别引用 Auth [UC004](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md)、[UC021](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md)、[UC022](../../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md)、[UC023](../../auth-center/use-cases/UC-AUTH-023-suspend-and-restore-developer.md)、[UC027](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md)和 App [UC028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md)。本用例只规定前端结构、确认、读取和错误隔离，不另建角色、权限来源、治理状态机或客户端审计事实。

不包含初始化/应急恢复、人员模糊搜索或全用户浏览、任意权限编辑、账号注销、Developer 开通审批、批量动作、计划任务或审计列表。没有对应查询 API 时不以本地缓存、Developer 应用列表或审核队列拼出全平台目录。

## 当前登录者的能力发现

BrowserSession 只有会话身份及代际信息，没有 role 或 permissions。Admin 域名、登录邮箱、Developer 状态、曾经操作成功、另一个目标的权限状态都不能成为当前调用者的授权依据。

### 已核实的可用读取

1. 在当前 Session 内显式调用 `GetPlatformAdministrator({subjectAuthId: session.authId})`。它不是面向所有用户的“查询自己角色”接口，没有 self 特例。
2. Auth transport 要求 Auth audience USER JWS 含 `auth.platform-admin.manage`；repository 的 `RequireAdministratorTx` 还在线复核当前账号/身份版本、初始化标记、完整管理集合及有效状态。鉴权先于目标查询。
3. 成功资源只包含 `subjectAuthId`、`accountStatus`、`membership`、`effective`、`permissionRevision`、`grantBlockers`，不返回原始 permissions。仅当目标严格等于当前 authId、资源完整合法且为 ACTIVE / GRANTED / effective=true，前端才能把它用作“本次已确认完整平台管理资格”的观察。
4. 根据 [BR-ADM-001](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001)，该完整资格对应固定四项管理能力：`auth.platform-admin.manage`、`auth.reviewer.manage`、`auth.account.manage`、`auth.developer.manage`。这是依据权威固定集合解释响应，不是从响应解析出任意权限，也不包含任何审核执行权或 App 运维执行权。部分管理集合属于服务端不一致状态，不按四个可选角色展示。
5. `403 + PLATFORM_ADMIN_FORBIDDEN` 只关闭平台人员治理范围，不清理 Reviewer 读模型、不删除 Cookie、不声称 Session 失效。503/入口不可用与协议错误不能解释为“不是管理员”；页面显示无法确认，并允许明确重读。
6. 既有交付基线中，完整平台管理员才可调用 `GetApplicationOperationsPermissions(session.authId)` 发现自己的 App 运维权；它不能供普通运维人员调用。本次已接受替代链见下节，不扩大旧 Get 的资格，不先开放未交付的新入口。

人员治理与 App 运维的能力观察按 Session 和各自读取 attempt 隔离；人员治理确认完整管理员资格前不发治理目标查询，App 运维按下节独立发现。重新进入、Session 变化、自我资格变更后重新读取，不能将上次能力缓存当作持久权限。

### 本人运维能力发现（本次修订）

权威结果与失败语义引用 Auth [BR-AOP-007](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-007)、[BR-AOP-008](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-008)，不从管理 membership、App OR 状态读取或旧 JWS 推导。审核并交付后，应用平台运维页面独立调用 `GetOwnApplicationOperationsPermissions`，不以 `GetPlatformAdministrator` 成功为前置；完整管理员发现仍只控制人员治理范围。

1. 使用当前 BrowserSession/attempt 发起一次明确本人读取，空请求且不传 authId/permission 清单。成功资源必须匹配当前 Session authId、正数精确 int64 permissionRevision 与完整 effectivePermissions 集合。HTTP 缺字段、null、错类型、非法/重复 ID、错主体或非法版本均为协议失败，不用生成器 repeated 默认值补成 `[]`。合法但不认识的新增 ID 不影响资源解码，但不赋予本客户端任何新动作。
2. 只按认识的精确 `app.application.search` / `app.application.suspend` / `app.application.restore` ID 分别控制目录与对应动作，并结合专用 Application 状态及双 revision。成功 `[]` 关闭 App 目录与运维私有目标范围及写操作，说明当前无这两项权限；不关闭人员治理或 Reviewer。仅一项失效只关闭该动作/确认，另一项仍以当前成功观察为准。
3. 失败是“无法确认”，不是“无权限”；禁止据旧快照发新命令，不保留可操作的旧确认。状态 GET 的成功只证明两项的 OR，不反推具体写权；新读取未交付/关闭/失败时不得自动回退旧管理员 GET 或以 App 写入试探。原本可用的按已知 App ID 只读入口仍由 App OR 鉴权独立保护，失败时清理其目标内容，不混淆两个读取结果。
4. 打开确认和实际提交前，分别完成当前 Session/attempt 的明确本人读取及目标专用 availability 核对。两个服务不是原子快照；subject/permissionRevision/精确集合或目标双 revision 与已确认基线不符时使确认失效，要求重新读取、重新明确确认。共享 permissionRevision 也可能因其它人员权限变化而前进，不能推断是哪项变化或自动替换确认；较低版本不得覆盖同 Session 的已知读取下界。
5. 本人 permissionRevision 仅用于观察与旧确认失效，不是 App 授权证明，不新增 App 命令参数。App 命令继续各自服务端精确鉴权；读取后撤权仍存在 Auth BR-AOP-004 的短期 JWS 边界，不宣称即时撤权。
6. 能力只存在当前私有页面/Query 内存，不进入 BrowserSession、URL、本地存储或遥测，不返回/解析原始 JWS，不轮询续权。Session 换代、离页、目标切换、迟到响应和未知写结果沿本文既有 attempt/Query 身份隔离；旧拒绝或 ACK 不能处理新页面或新 Session。

### 历史缺口与交付边界

以下记录此前缺口，2026-11-08 本工作包按新固定API与明确接受设计接入；不能把历史待实现描述当作当前接口不存在。2026-11-04 已从[本人运维权限发现提案](../../auth-center/implements/2026-11-04-own-application-operations-permissions-proposal.md)展开为 UC-AUTH-027/本 UC 的已接受修订。设计依赖已有闭合方案，但 API/Auth/Gateway/Console 均未实施或联合验收，以下旧交付边界继续有效。

独立 App 运维人员可以合法不具备平台管理员资格。当前 `GetApplicationOperationsPermissions` 同样要求调用者是完整平台管理员，即使 subject 是自己也没有例外；`GetApplicationPlatformAvailability` 只证明调用者拥有两项运维权中的至少一项，响应没有指出是哪项。因此现有 API 无法向这类调用者权威区分 suspend-only / restore-only / both。

本次设计选择新增本人最小 RPC，而不放宽既有目标 Get/Manage、不扩充 BrowserSession。Auth 拥有人员权限及本次权威投影，API/Gateway 交付边界见 UC027 和[待审路由增量](../../platform/contracts/auth-center-api-routing.md#uc027-本人运维权限读取)；Console 不自行增加后端授权规则。

在该依赖交付前，完整平台管理员经上述自查询获得明确运维权的链路可实施；非平台管理员运维人员保留独立“应用平台运维”入口和按已知 Application ID 的状态读取，但不通过 OR 读取成功展示成两项均已授权，不为试探权限发送写命令，也不把不可确认的精确权限当作已拒绝。其精确操作控件保持不可用并解释能力尚无法确认。此缺口不阻塞平台人员治理或 Reviewer 页面；不能宣称已支持全部运维角色。

## 页面结构与导航

Admin 主导航保留“版本审核”“资料审核”，增加相互独立的“平台人员治理”“应用平台运维”。入口存在不代表获授权；每个页面先完成自己的能力观察。人员治理页面包含以下功能分区，结构不规定具体视觉样式。

| 分区 | 目标与读取 | 可用操作 |
| --- | --- | --- |
| 平台管理员 | `ListPlatformAdministrators` 的真实分页名单；另支持明确 authId 查询 | 完整管理集合 GRANT / REVOKE |
| 应用审核权限 | 已知 authId；`GetApplicationReviewPermissions` | 分别管理 `app.profile.review`、`app.version.review` |
| 应用运维权限 | 已知 authId；`GetApplicationOperationsPermissions` | 分别管理 `app.application.search`、`app.application.suspend`、`app.application.restore` |
| 账号状态 | 已知 authId；`GetUserAccountStatus` | DISABLE / RESTORE |
| Developer 资格 | 已知 authId；`GetManagedDeveloperStatus` | SUSPEND / RESTORE |

目标输入在用户明确“读取”后生效；编辑输入不会逐键请求，也不悄悄把旧资源上的按钮改绑到新 ID。成功资源显示精确目标 ID 与该能力最小状态。变更目标、切换分区、失权或离页清除旧确认与原因草稿；不在 URL、持久化存储或通用遥测中保存原因。

只有管理员名单存在全量分页 API。该名单只表达已保存 GRANTED 的人员（可能包括 DISABLED），不伪装成所有用户或所有有效管理员；使用服务端 `nextAfterAuthId`，跨页不宣称快照，提交前重新读目标。其他分区保留已知 authId 的目标表单，并按下节新增仅完整管理员可用的精确人员查找，不造全体人员表格。

应用平台运维页面独立按已知 Application ID 读取 `GetApplicationPlatformAvailability`，显示 lifecycle 与平台可用状态及必要变更时间。只持有 suspend 可以读取但不能 restore；反之亦然。应用不在 Developer 所有权列表中不妨碍已授权运维；运维读取不额外索要公开资料、owner、OAuth、发布或审核内容。

## 平台应用发现与人员精确定位（2026-11-08 修订）

### 平台应用目录

在 `/governance/applications` 增加独立“查找应用”区域。业务权威为 [App UC051 / BR-APP-063–066](../../app-center/use-cases/UC-APP-051-query-platform-application-directory.md) 与[目录读契约](../../app-center/query-contracts/platform-application-directory.md)；精确search grant、本人与管理读取及签发以 [Auth UC027](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md)、UC010为准。

本人读取独立识别 `app.application.search`，不先要求完整管理员。search-only可查目录及最小摘要但不能暂停/恢复；没有search的运维人员仍按已知ID读取其专用状态。人员治理的目标权限资源按三项完整集合严格解码并逐项授撤，不把新ID映射为另一动作。成功空集合、未知权限ID和读取失败继续严格区分；只缺暂停/恢复不能清search-only的目录。

`SearchPlatformApplications` 使用 `POST /app-center/v1/platform/applications:search`，正文为query，不包请求外层；用户明确搜索或明确查看空筛选目录。筛选为精确Application ID、技术名称前缀、owner Auth ID及生命周期/平台可用性/归档三独立维度，按服务端AND语义；不搜索Profile或人员资料。结果只显示最小摘要，技术revision不作为普通提示。

每页20，沿正式token明确续读。短页/空页仍有token时允许继续，不无限自动扫描、不推算总数；改变筛选或刷新重建分页链，每页保留自身asOf。失败不伪装空结果或丢弃损坏项，不用我的应用/公开目录/审核队列拼全平台目录。

选中后调用 `GetPlatformApplicationSummary`（`GET /app-center/v1/platform/applications/{application_id}`，无query别名）重新读取最小摘要；不据此打开私有owner配置或写确认。仅已有相应运维权时进入原专用availability读取，确认前和提交前继续核对本人权限与目标双revision。search撤权只清目录/摘要，不隐式清独立运维/人员/Reviewer；搜索摘要不是命令基线。

### 人员精确查找

在 `/governance/personnel` 目标区域增加Auth ID/完整邮箱两种方式，仅当前已确认完整管理员可发查询。权威为 [Auth UC039 / BR-USR-001–005](../../auth-center/use-cases/UC-AUTH-039-search-users-for-administration.md)。Reviewer、独立App搜索/运维者不能获得用户目录。

`SearchUsers` 使用 `POST /auth-center/v1/managed-users:search`，正文只有authId或email一个selector；不提供空查询、前缀/模糊搜索、分页/排序/总数或自动联想。Auth ID原值提交，邮箱语义引用Auth；不在前端剥离+tag/点号或自行定义规范化。邮箱仅在POST正文与当前表单内存，不进URL、持久存储、遥测或Query key。切换方式、修改输入、重新查询清旧结果/已选目标/确认，旧响应不能恢复。

结果只能零或一项，显示Auth ID、账号状态、nullable Developer状态及asOf，null为未申请。零项只说明没有匹配的可治理账号，不判定邮箱历史。返回不含邮箱/Profile/权限/revision。选择后以返回Auth ID读取当前治理模块专用Get，取得正式状态与revision，再走原确认/OCC；邮箱后来换绑不悄悄换掉已选主体。

人员搜索不用于Developer转让对象选择。它的拒绝与App目录/本人能力及Reviewer分开退场；明确Session失效沿既有Session恢复。三类发现只持有当前Session/attempt/Query私有内存，错误和成功验证private/no-store，旧成功/拒绝不处理新查询或新Session。

### 增量验收

覆盖none/search-only/suspend-only/restore-only/search+动作及完整管理员、Reviewer、owner无grant组合；同Session正式授撤后的新读取；三状态筛选、空页可继续、损坏与故障分型、选中摘要后专用读回、三项权限管理与旧确认失效。人员查找覆盖两个selector、零/一项、nullable Developer、DISABLED、邮箱归一化权威边界、改输入/换主体/旧响应、无目录权限和不用于转让。真实Auth授撤、Console Cookie链和React命令分别验收，不沿用后端绿色结果。

## 命令与确认

1. 所有操作先有本能力专用、当前成功读取；正常操作不展示技术 revision，也不提供手填 revision。
2. 用户选定单项动作并填写原因，再显示短明确确认，包含完整目标 ID、当前状态、所选权限/动作及实际将提交的原因。确认不是整页复杂编辑器；不得用“保存全部”把多项权限串成隐式批量写入。
3. 确认绑定打开时的 Session、目标、动作及基线。目标、权限观察或基线变化使旧确认失效；单次确认只发一个命令，在途禁止重复点击、自动重试与失焦提交。
4. 原因按对应后端的 UTF-8 长度与空白规则验证，确认内容与实际发送一致；不加入 actor、角色、声称的新状态或客户端审计事件。
5. 平台资格、两项审核权限与三项应用读取/运维权限共用目标 `permissionRevision`，但每条命令使用自己最新专用 GET 的资源。任何已观察到更高的同目标共享修订都会使旧确认失效并要求重读；不把其他分区的旧 permissions 拼接或据更高数字自动补写。
6. 账号命令只用 `accountRevision`，Developer 命令只用 `developerRevision`。App 命令同时使用同一次 availability 读取的 `lifecycleRevision` 与 `platformAvailabilityRevision`。精确 int64 使用 bigint/官方 ProtoJSON，不经 JavaScript number 转换。
7. 成功回执须匹配目标、动作状态与预期修订变化；App 回执同时核对 lifecycle 未被命令改变。已确认修订成为只增不减的读取下界。随后以专用只读接口核对当前状态，ACK 与读回失败分开表达，不因读回失败重发命令。

前端确认影响只引用后端规则：

- 撤销自身平台资格后退出平台人员治理，不撤销独立 Reviewer 或 App 运维资格；引用 [BR-ADM-001](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001)。最后有效管理员保护由 [BR-ADM-003](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-003) 服务端事务执行。前端不能凭名单总数/当前页预测一定能撤销或禁用；`LAST_PLATFORM_ADMIN_REQUIRED` 显示明确阻止原因，不提供覆盖入口。
- 账号禁用与恢复的影响依 [BR-ACC-001](../../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-001)、[BR-ACC-002](../../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002)；恢复后需重新认证，不声称旧会话恢复。自我禁用需额外明确提醒将失去当前登录，之后由其他有效管理员恢复；安全退场优先于展示成功。若 Session 复核阻止消费 ACK，不能猜测是否提交成功。
- Developer 暂停不等于禁用账号或下架应用；只按 [BR-DEV-013](../../auth-center/use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-013) 展示合法转换；恢复的邮箱门禁由后端判定，不把不可管理目标的 404 当成可申请 Developer 的空态。
- App 暂停、恢复依 [BR-APP-029](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md#br-app-029)至 [BR-APP-037](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md#br-app-037)；CLOSING/CLOSED 不可恢复，解除门禁不承诺可运行、不自动恢复 client 或发布配置，也不声称能收回已交付页面/数据。

## 错误、并发与私有数据隔离

治理能力与现有 `versions` / `profiles` Reviewer attempt 必须分开，不将治理请求包进现有某个审核边界。人员治理各能力、App 运维状态读取、suspend 和 restore 的拒绝分开归属；例如单项 restore 被拒绝，不能清掉仍可访问的 suspend、人员治理或审核页面。完整管理员资格明确失效时关闭依赖该 bundle 的人员治理范围，但不推断独立 App 权限同时失效。

| 返回/情形 | 前端处理 |
| --- | --- |
| `SESSION_INVALID` / 当前 `CONSOLE_SESSION_CHANGED` | 复用当前 Session 绑定恢复，清理旧 Session 所有私有范围、草稿、确认与在途消费资格；旧响应不能处理新 Session |
| 治理 401/403，未明确是 Session 拒绝 | 清理相应能力内容并关闭写入；401 可复核当前 Session，不能仅凭下游身份错误删除独立有效 Cookie；403 不触发全局登出 |
| 目标专用 404 | 清理该目标，显示不存在或不可管理；不合成为 NONE / ACTIVE / 未授予，不清掉同能力其他目标或独立 Reviewer |
| stale revision / 重复动作 / 非法状态转换 409 | 不乐观覆盖、不自动新 revision 重试；要求专用只读核对，之后重新确认 |
| grant/restore blocker、最后管理员保护、版本耗尽 | 显示对应明确门禁；不绕过、不借恢复其他资格强行重试 |
| 429 | 保留安全范围内输入，显示稍后重新读取/确认；不定时重放命令 |
| 只读网络/5xx | 可保留同能力旧快照并标记读取失败，但禁止基于失败读取发送新命令 |
| 写入断流、5xx、畸形成功、回执目标/状态/版本不符 | 结果未知，保留未知提示且停止进一步写入；仅显式只读核对，不暗示原命令一定成功或未执行 |

未知读回只说明当前事实，不证明哪个操作写成，也不能恢复旧原因或追加审计；用户核对后如仍需要动作，基于新读取重新明确确认。不得在 mutation 缓存、离线队列或页面恢复时重放治理命令。

请求复用 `createBoundPrivateFetch` 与当前 attempt 生命周期，命令成功和错误消费都核对当前 Session。缓存键隔离 Session/能力/目标/attempt；更新、取消与清理只触及捕获且仍同一实例的 Query，采用读回前再次验证 Query/data 身份与修订下界。离页、换目标、旧 Session 的迟到 ACK、拒绝、读回都不能改新页面、清理替换 Query 或触发后续写入。

## 客户端与接口边界

API 输入固定 [6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6](https://github.com/TokenTeam/iwut-api-proto/tree/6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6)，不读取相邻源码作为运行依赖、不手写第二套 DTO。本轮只登记后续生成需要，不在本设计提交生成物。

该固定输入只涵盖既有交付基线，**不含本次本人 RPC**。审核后必须由 API/Auth owner 交付新固定提交，再更新 Console 输入及官方生成物，之后才能接入上方新发现链；不得把本轮草案名称当作现有客户端方法。Gateway 同步固定 descriptor/精确 route 并完成 Session 透传链，不通过特权 BFF 新增旁路。

现有生成清单已包含且复用：

- `auth_center/v1/reviewer_permission/reviewer_permission.proto`
- `auth_center/v1/account_management/account_management.proto`
- `auth_center/v1/developer_management/developer_management.proto`

须从同一固定输入追加的精确 proto：

- `auth_center/v1/platform_administrator/platform_administrator.proto`
- `auth_center/v1/application_operations_permission/application_operations_permission.proto`
- `app_center/v1/application_operations/application_operations.proto`
- `app_center/v1/application_operations/error_reason.proto`

依赖的 Google annotations/http/Timestamp 继续沿用现有官方生成工具链。前三类 Auth 服务没有独立 error_reason.proto，不臆造输入文件。App wire reason 使用真实 `ERROR_REASON_*` 前缀；Auth 使用其正式字符串 reason，不将 UC 表格中的简称直接当作 App 错误码。

后续客户端分为 Auth 人员治理与 App 平台运维两个边界，使用同 origin 普通 HTTP/JSON、`/auth-center` 与 `/app-center` 前缀；不经特权 BFF 聚合、不向浏览器返回 USER JWS。精确方法如下：

| 服务 | 方法及 HTTP 绑定 |
| --- | --- |
| PlatformAdministratorService | Manage/Get/List，分别 `POST /v1/platform-administrators:manage`、`:get`、`:list` |
| ReviewerPermissionService | `GetApplicationReviewPermissions` / `ManageApplicationReviewPermission`，GET 两项状态、PUT 路径所选 permission；不用 legacy `ManageReviewerPermission` |
| ApplicationOperationsPermissionService | GET `/v1/users/{subject_auth_id}/application-operation-permissions`；PUT 同路径 `/{permission}` |
| ApplicationOperationsPermissionService（本次修订） | `GetOwnApplicationOperationsPermissions`，GET `/v1/users/me/application-operation-capabilities`；响应语义唯一引用 UC027 |
| AccountManagementService | Manage/Get，`POST /v1/user-accounts:manage-status`、`:get-status` |
| DeveloperManagementService | Manage/Get，`POST /v1/developers:manage-status`、`:get-managed-status` |
| ApplicationOperationsService | GET `/v1/applications/{application_id}/platform-availability`；POST `/v1/applications/{application_id}:suspend` / `:restore` |

GET 无 body/query；POST 查询仍按官方 JSON request 发送且不自动重试。路径身份不在正文另设可替换目标；App POST 的 `body: command` 只序列化内部命令，不能再套 `command` envelope。审核写正文是 action / expectedRevision / reason；运维授权写正文是 action / expectedPermissionRevision / reason，不能混用字段名。客户端拒绝未知枚举、非法/缺失修订、错目标或不完整两项权限资源，不以默认值补成功。

页面层分别拥有能力观察、名单分页、目标读取、命令确认和未知核对；复用会话设施但不混合授权。组件库、Tailwind 与同一 light/dark 骨架沿既有技术 ADR；本文不规定卡片尺寸、颜色或像素布局。

## 核对依据与验收边界

本设计除上述 UC 与固定 API 外，已只读核对 Auth `UserCapabilityIdentityMiddleware`、`PlatformAdministratorService`、`RequireAdministratorTx`、`PlatformAdministratorRepository.Get`、`ApplicationOperationsPermissionRepository.Get`、Reviewer/账号/Developer 的各自 transport/repository，以及 App `ApplicationOperationsHandlers` / `ApplicationOperationsService`。这些实现观察用于发现依赖，不替代后端权威规则。Gateway 普通 ADMIN 声明已覆盖表中 14 个精确方法，不由 service 通配授权；源声明存在不等于当前构建或真实链路验收完成。

后续必要定向验收覆盖：普通用户/独立 Reviewer/完整管理员/管理员另获单项 App 运维权；非管理员运维发现缺口明确保留；四类人员治理拒绝不影响审核与 Session；两项审核/两项运维权限各自独立及共享修订竞争；名单分页与已知 ID 表单；最后管理员拒绝、自撤、自禁用安全退场；账号与 Developer/App 三种状态互不冒充；双 App revision、未知只读核对、准确 JSON 绑定；Session/目标换代与旧 Query 替换下的迟到响应。真实授权、禁用恢复与 App 状态变化需用正式入口和镜像单独取证，不能把设计、合成测试或名单查询作为写链完成证据。

本次新增验收计划（未执行）：非管理员 none/suspend-only/restore-only/both、完整管理员无 App grant；同 Session 正式授撤后新集合/版本；成功空集合与 401/403/429/5xx/畸形成功的明确区分；集合含合法新 ID、缺字段/null/非法/重复 ID、错主体及 int64 精度；确认打开/提交前变更权限或目标；新链失败不回退探权；人员治理/Reviewer 不被独立运维读取拒绝清理。旧管理 GET 非管理员查本人仍拒绝，App 各写权限、双 revision 和短期 JWS 边界保持。设计审核后按 Auth → Gateway → Console 固定各输入串行交付及联合验收，不以本轮文档更新宣称缺口已实现。

## 变更记录

- 2026-10-30：接受首版前端职责设计；明确平台资格自查询的真实授权门槛、不返回 permissions，以及独立 App 运维人员精确能力发现的最小依赖。仅交付文档，未实施产品、生成物或真实治理写入。
- 2026-11-04：新增独立本人能力发现消费设计，本次修订 DRAFT 待用户审核；原人员治理及受限 App 运维基线继续有效，不实施新发现链。
- 2026-11-04：用户明确接受本次本人读取/消费修订并授权实现；依赖复核通过，同步 ACCEPTED 后脚本生成 brief，开始串行实施；未授权自动 commit/push 或生产启用。
