# UC-AUTH-038：管理脚本权限

状态：`ACCEPTED`（用户明确接受五项权限修订并授权实施；交付状态见 implements）

2026-11-10 用户明确接受本人脚本权限发现修订，权威语义已合入正文；先生成 brief 后实施。

## 目标与范围

平台管理员按目标用户独立查询、授予或撤销五项权限：`app.script.maintain`、`app.script.review`、`app.script.publish`、`app.script.suspend`、`app.script.restore`。Auth 管理人员权限并向 App 签发当前有效权限；[App UC041 的精确权限规则](../../app-center/use-cases/UC-APP-041-manage-script-resource.md#br-scr-002) 拥有脚本业务鉴权。Auth 不读取或修改脚本资源。

## 参与者与接口边界

- 管理者使用既有 SESSION → Auth audience USER JWS 链，入口要求 `auth.platform-admin.manage`，事务内按 [UC021](UC-AUTH-021-manage-platform-administrators.md) 在线复核当前 ACTIVE 账号与完整管理员资格。
- 提供独立的目标查询和授撤命令，不放宽 UC004、UC027 的固定权限范围。查询以 subjectAuthId 定位目标，从同一快照返回五项权限各自的授权事实 `granted`、当前效力 `effective` 和正数共享 `permissionRevision`。
- 本人读取者是任意有效 ACTIVE USER，沿 SESSION → Auth audience USER JWS 查询自己的五项脚本状态，无需先持有脚本或管理 permission。
- 新命令只接受 subjectAuthId、单一 permission 枚举、`GRANT | REVOKE`、正数 int64 expectedPermissionRevision 和原因（去两端空白后 1–1024 UTF-8 bytes）。仅接受下列五个精确枚举，不接受通配、任意权限 ID 或自报 actor。成功返回同次提交的五项目标状态；错误不合成为未授权状态。

## API 契约

新服务 `auth_center.v1.script_permission.ScriptPermissionService` 与旧服务 `auth_center.v1.script_maintainer_permission.ScriptMaintainerPermissionService` 均提供原生 gRPC 与 HTTP/JSON：

| RPC | Auth 服务内部 HTTP 路径 | 请求 |
| --- | --- | --- |
| `GetOwnScriptPermissions` | `GET /v1/users/me/script-permissions` | 空请求，仅可信身份本人 |
| `GetScriptPermissions` | `POST /v1/script-permissions:get` | subjectAuthId |
| `ManageScriptPermission` | `POST /v1/script-permissions:manage` | subjectAuthId、permission、action、expectedPermissionRevision、reason |
| `GetScriptMaintainerPermission` | `POST /v1/script-maintainer-permissions:get` | subjectAuthId |
| `ManageScriptMaintainerPermission` | `POST /v1/script-maintainer-permissions:manage` | subjectAuthId、action、expectedPermissionRevision、reason |

新方法成功 200，返回 `subjectAuthId`、`permissionRevision` 和 `permissions`，按枚举顺序完整返回五个 `{permission, granted, effective}` 对象。permission 枚举依次为 `SCRIPT_PERMISSION_MAINTAIN=1`、`SCRIPT_PERMISSION_REVIEW=2`、`SCRIPT_PERMISSION_PUBLISH=3`、`SCRIPT_PERMISSION_SUSPEND=4`、`SCRIPT_PERMISSION_RESTORE=5`；0 和未知值无效。action 的 `GRANT=1`、`REVOKE=2`。

旧方法的请求、响应及错误 reason 不变，固定操作 maintain，仍返回 `subjectAuthId`、`granted`、`effective`、`permissionRevision`。两组方法都使用标准 ProtoJSON int64，拒绝 query、未知或重复字段，消息上限 16 KiB，响应私有 no-store。共用按已认证 actor 计数的读写限流（默认每分钟读 60、写 10）。

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少/无效 USER 身份、当前身份代际不匹配 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 不具备完整平台管理员资格 | `SCRIPT_MAINTAINER_PERMISSION_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 请求非法 | `INVALID_SCRIPT_MAINTAINER_PERMISSION_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不存在或不可管理 | `SCRIPT_MAINTAINER_PERMISSION_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| 版本冲突或重复动作 | `SCRIPT_MAINTAINER_PERMISSION_CONFLICT` | 409 / ABORTED |
| 授予门槛不满足、共享版本耗尽 | `SCRIPT_MAINTAINER_PERMISSION_GRANT_BLOCKED` / `PERMISSION_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 超过限流 | `SCRIPT_MAINTAINER_PERMISSION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 权威数据损坏、存储故障、提交结果未知 | `SCRIPT_MAINTAINER_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

新方法使用上表相同状态码与错误语义，将 reason 中的 `SCRIPT_MAINTAINER_PERMISSION` 替换为 `SCRIPT_PERMISSION`，共用的身份与版本耗尽 reason 不变。


本人方法的精确 full method 为 `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions`。新增空 `GetOwnScriptPermissionsRequest`，返回现有 `ScriptPermissions`。HTTP 拒绝 query 与任何正文，原生 gRPC 空消息拒绝未知字段；HTTP 明确输出五个完整状态对象和 false 布尔字段，按标准 ProtoJSON int64 输出共享版本。该方法普通 USER 无权限也可成功读取，身份失效、数据损坏和依赖失败使用既有身份或 SCRIPT_PERMISSION 错误，不能合成为五项 false。


## 业务规则

<a id="br-smp-001"></a>
### BR-SMP-001：独立显式授权与目标门槛

Developer、Application 管理员、Reviewer、App 运维人员、完整平台管理员及 SYSTEM 均不自动获得任何脚本权限。五项权限之间无推导关系，持有任一项也不授予管理他人权限。五项均为平台用户权限，不是 OAuth Scope、应用 consent 或第三方可申请能力。

授予门槛沿用 [UC027 / BR-AOP-005](UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005)：目标是 ACTIVE USER，且具备已验证邮箱与部署就绪的恢复能力。合法 ACTIVE 或 DISABLED USER 可由管理员查询，已有授权可撤销；查询和撤销不读取目标邮箱，也不依赖恢复就绪。DISABLED 保留 grant 但不生效；恢复不复活旧认证材料。SYSTEM、未知、CLOSED 不可管理；未授权调用在目标读取前拒绝，不泄露目标存在性。

<a id="br-smp-002"></a>
### BR-SMP-002：共享版本、事务与审计

复用 `auth_principals.permissions`、共享 `permissionRevision` 和 `auth_permission_audit_events`。在现有 Auth 认证事务栅栏中复核管理者和目标，按目标共享版本 CAS，只增删明确选中的一项权限，保留其它权限。一次真实变化递增一次版本，与记录 actor/subject、精确 permission、action、reason、前后状态与版本、时间的不可变审计同事务提交。旧接口与新接口使用同一个版本；两个请求使用相同预期版本修改不同权限时至多一个成功。过期版本、重复动作、坏数据、审计失败和未确认提交不得报成功；结果未知时走正式查询，不盲目换版本重放。不记录 JWS、Session 或邮箱原文。

<a id="br-smp-003"></a>
### BR-SMP-003：只向 App audience 投影已授权项

按 [UC010 / BR-IDN-002](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002) 将五项脚本权限纳入 `iwut-app-center` 服务端投影清单，只投影 ACTIVE USER 当前实际拥有的精确项。Auth audience 不披露这些权限，UC010 所列其它既有 App 权限继续独立投影。签发仍使用同一 Session 检查、JWS 格式、签名与有效期；不把权限加进 BrowserSession，也不新增角色 claim。

授撤与签发遵循 [BR-IDN-004](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 的事务提交顺序。撤销提交后新签发不再包含被撤销项；此前已签发身份仍受原 exp 与验签时钟容差约束，不承诺即时追回。


<a id="br-smp-004"></a>
### BR-SMP-004：本人最小权限读取

本人方法以可信身份 authId 为唯一主体，空请求不接收目标或权限清单。目标 Get/Manage 及旧 maintain 方法继续要求完整管理员，查询本人也不例外。

返回 subjectAuthId、共享正数 permissionRevision 和 permissions，严格复用本 UC 当前五项枚举、状态对象和枚举顺序。五项均来自本次权威观察，返回完整、唯一集合，不分页或截断，不附带其他人员权限、资料、邮箱、恢复 blocker 或审计。

每项仍含 granted 和 effective。该方法只允许 ACTIVE USER 成功，因此每项 effective 与 granted 相等。零授权时仍成功返回全部五项，五个 granted/effective 都为 false；完整平台管理员也只有在另获显式 grant 后才有相应 true。成功的零权限与请求失败保持区分。

标准 ProtoJSON int64 按十进制字符串精确处理。HTTP 成功响应显式输出所有五项对象及 false 布尔字段，客户端先验证 subjectAuthId、正数版本、数组完整性、枚举唯一性与字段存在，再消费生成模型。漏项、重复项、缺布尔或不一致状态属于协议/数据错误，不能用 protobuf repeated 或 bool 的默认值合成为“无权限”。

<a id="br-smp-005"></a>
### BR-SMP-005：本人在线观察与失败关闭

Auth 在现有认证事务协调边界内，以可信身份的 authId 和 accountRevision 确认当前 USER、ACTIVE 状态及有效代际，同时读取权威 permissions 和共享 permissionRevision。完整权限集合及正数版本必须结构有效；损坏、存储故障或提交结果未知失败关闭。不能从入站 JWS 的权限副本、BrowserSession、前端角色或管理者目标 snapshot 推导结果。

本人读取不要求完整管理员 bundle、管理员初始化标记、邮箱或恢复就绪，也不调用目标管理员 Get 来绕道实现。读取不改变 grant、permissionRevision、授权审计或 Session 业务状态，复用既有认证事务栅栏进行在线确认。

UNKNOWN、SYSTEM、DISABLED、CLOSED 或失效代际按身份拒绝处理，不返回五项 false 的成功结果。账号禁用时原 grant 按 BR-SMP-001 保留，管理员目标 Get 仍可观察 granted=true/effective=false；本人方法停止提供成功读取。账号恢复后按既有登录与代际规则建立有效身份，再读取保留授权。

授撤、账号变更与本人读取有明确事务提交顺序。读取可观察并发变更之前或之后的完整快照，集合与 revision 不得混用。撤权提交后发起的新本人读取排除该项，新的 App 身份签发按 BR-SMP-003 排除该项；已签 App JWS 沿既有 exp/容差窗口到期。本人读取结果只供本次职责发现，不作为 App 凭据、整个 Session 的权限租约或业务命令的 CAS 参数。

## 交付依赖与部署

依赖核对：现有权限存储、共享 CAS/审计、管理员在线复核及 UC010 签发链可复用。旧 UC038 入口固定处理 maintain；其余四项需要新管理入口及 UC010 投影增量。App 的通用 USER 验签器复用现有 claim。App UC045 的字段披露与 UC044/046 的命令鉴权由 App 自行实现。

复用现有集合、索引、audience、密钥与 TTL，无需迁移、回填或默认 grant。旧入口沿用 `AUTH_SCRIPT_MAINTAINER_PERMISSION_ENDPOINTS_ENABLED`；新入口由 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED` 独立启用。两者默认关闭，复用用户端点、签发与邮箱恢复配置。入口开关控制目标管理与本人读取调用。部署新版签发器前只读排查历史同名 grant，存在时先核明来源及处置。使用正式管理 API 验收。Gateway 的精确 Admin 路由和 Console 管理界面独立接入，Auth/App 后端联验直接使用受保护的 Auth API 与既有签发 RPC。

复用 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED`，默认关闭；启用要求已有用户运行时和身份签发配置。新增方法按精确 full method 进入普通 USER 分支，原目标 Get/Manage 按精确方法保持管理员分支。旧 maintain 开关不启用本人读取。本人和管理员读取共用该权限族现有 actor 读预算，默认每分钟 60、最多 4096 个有界桶。

Gateway 依既有 SESSION 编排为 Auth audience 签发 USER 身份，只增加该精确查询的路由及 typed adapter。公网及 Admin Console 的 HTTP、原生 gRPC、gRPC-Web 由路由 owner 固定，Console surface 为 ADMIN。Developer surface 不开放该脚本工作台读取。BFF 绑定当前 BrowserSession，只转发当前 Session，不接收浏览器自报 subjectAuthId。客户端在进入职责页面及权限失败恢复时重新读取，不缓存权限进 BrowserSession。

成功及错误均 private, no-store。身份缺失或失效沿用 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY（401 / UNAUTHENTICATED）；非法空请求载荷使用现有 INVALID_SCRIPT_PERMISSION_REQUEST（400 / INVALID_ARGUMENT）。超限沿 SCRIPT_PERMISSION_RATE_LIMITED（429 / RESOURCE_EXHAUSTED），损坏、存储/事务故障沿 SCRIPT_PERMISSION_UNAVAILABLE（503 / UNAVAILABLE）。入口关闭或路由未交付是能力不可用，不能映射为成功零权限。该方法不要求某项 permission，合法零授权 ACTIVE USER 不返回 403。

## 验收

1. 在真实 Mongo 副本集和生产 Wire 下，用已获签发权限的服务身份与同一 ACTIVE USER 的同一有效 Session，分别在未授予、正式授予提交后、正式撤销提交后调用现有 `IssueUserIdentityFromSession`。由 App 真实验签器检查三个新签 USER JWS 的同一 sub、独立 jti、正确 audience 和该权限依次缺失、存在、缺失。逐项覆盖五项权限，验证撤销一项时其他显式授权保持有效。
2. Auth audience 不披露脚本权限；UC010 所列其它既有 App 权限不回归；现有角色、其他脚本权限和错误 audience 不产生隐式授权。旧 maintain 接口与新接口读写同一授权。App 业务入口按各自 UC 验证实际命令与查询。
3. 覆盖管理员门禁、授予条件与 DISABLED 撤销、同版本并发冲突、重复动作、审计失败回滚以及授撤与签发竞争。不得把旧 JWS 在原有效窗口内仍可使用误报为撤销未生效。

用户已接受并授权实施：先生成本 UC 的实施 brief，再改 API 与 Auth；不直接修改实际数据库授权或生产配置。

新增 API 精确方法、Auth 本人事务读、精确鉴权分流及对应客户端验收。复用现有存储、版本、响应、限流和开关，无需新集合、索引、迁移或默认 grant。UC027 的三项 Application 本人公开 allowlist 保持其已接受范围，UC010 的 App 签发规则直接引用既有定义。共享路由契约和 Console 接入由对应 owner 跟进。

验收包括任意 ACTIVE USER 的零授权完整五项、每项独立 grant 与组合、完整管理员无隐式 grant；subject 注入、body/query/未知 wire 字段及错误 audience；无管理员初始化或邮箱恢复就绪仍可读取本人；停用/CLOSED/代际失效身份失败与权威数据损坏；同一 Session 正式授撤后的本人结果和新签 App 身份变化；撤权与读取的提交竞争；保持原目标方法对本人仍要求完整管理员。通过真实 Mongo、生产 Wire 和生成客户端证明。

<a id="proposed-own-script-permissions"></a>
## 本人读取修订记录

2026-11-10 用户明确接受该修订。原待审锚点保留供审核链接定位，语义唯一位于 API、BR-SMP-004/005 和交付章节。
