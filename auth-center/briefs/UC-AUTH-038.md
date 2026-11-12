<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-038 --spec tools/brief-specs/UC-AUTH-038.json -->
# Brief — UC-AUTH-038：管理脚本权限

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-038` 管理脚本权限 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SMP-001`–`BR-SMP-005`（5 条） |
| 外部引用 BR | `BR-AOP-005`，`BR-IDN-002`、`BR-IDN-004`（来自 `UC-AUTH-010`、`UC-AUTH-027`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-session-identity-issuance-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

平台管理员按目标用户独立查询、授予或撤销 `app.script.review`、`app.script.publish`、`app.script.suspend`、`app.script.restore` 四项权限。Auth 管理人员权限并向 App 签发当前有效权限。App 使用 [UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002) 现有的 `developer_status=APPROVED` 作为作者资格输入，并校验本人归属与写入资格。

### 参与者与接口边界

- 管理者使用既有 SESSION → Auth audience USER JWS 链，入口要求 `auth.platform-admin.manage`，事务内按 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md) 在线复核当前 ACTIVE 账号与完整管理员资格。
- 提供独立的目标查询和授撤命令，不放宽 UC004、UC027 的固定权限范围。查询以 subjectAuthId 定位目标，从同一快照返回四项权限各自的授权事实 `granted`、当前效力 `effective` 和正数共享 `permissionRevision`。
- 本人读取者是任意有效 ACTIVE USER，沿 SESSION → Auth audience USER JWS 查询自己的四项脚本状态，无需先持有脚本或管理 permission。
- 授撤命令只接受 subjectAuthId、单一 permission 枚举、`GRANT | REVOKE`、正数 int64 expectedPermissionRevision 和原因（去两端空白后 1–1024 UTF-8 bytes）。仅接受下列四个精确枚举，不接受通配、任意权限 ID 或自报 actor。成功返回同次提交的四项目标状态；错误不合成为未授权状态。

### API 契约

`auth_center.v1.script_permission.ScriptPermissionService` 提供原生 gRPC 与 HTTP/JSON。

| RPC | Auth 服务内部 HTTP 路径 | 请求 |
| --- | --- | --- |
| `GetOwnScriptPermissions` | `GET /v1/users/me/script-permissions` | 空请求，仅可信身份本人 |
| `GetScriptPermissions` | `POST /v1/script-permissions:get` | subjectAuthId |
| `ManageScriptPermission` | `POST /v1/script-permissions:manage` | subjectAuthId、permission、action、expectedPermissionRevision、reason |

成功响应为 HTTP 200，返回 `subjectAuthId`、`permissionRevision` 和 `permissions`，按枚举顺序完整返回四个 `{permission, granted, effective}` 对象。permission 枚举依次为 `SCRIPT_PERMISSION_REVIEW=2`、`SCRIPT_PERMISSION_PUBLISH=3`、`SCRIPT_PERMISSION_SUSPEND=4`、`SCRIPT_PERMISSION_RESTORE=5`。编号 `1` 和名称 `SCRIPT_PERMISSION_MAINTAIN` 预留为退役项。授撤拒绝 `0`、`1` 和未知值。action 的 `GRANT=1`、`REVOKE=2`。

原 `ScriptMaintainerPermissionService` 和两条 `/v1/script-maintainer-permissions:*` HTTP 路由退役。三个保留方法使用标准 ProtoJSON int64，拒绝 query、未知或重复字段。消息上限 16 KiB，响应为 `private, no-store`。限流按已认证 actor 计数，默认每分钟读 60、写 10。

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少/无效 USER 身份、当前身份代际不匹配 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 不具备完整平台管理员资格 | `SCRIPT_PERMISSION_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 请求非法 | `INVALID_SCRIPT_PERMISSION_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不存在或不可管理 | `SCRIPT_PERMISSION_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| 版本冲突或重复动作 | `SCRIPT_PERMISSION_CONFLICT` | 409 / ABORTED |
| 授予门槛不满足、共享版本耗尽 | `SCRIPT_PERMISSION_GRANT_BLOCKED` / `PERMISSION_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 超过限流 | `SCRIPT_PERMISSION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 权威数据损坏、存储故障、提交结果未知 | `SCRIPT_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

本人方法的精确 full method 为 `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions`。新增空 `GetOwnScriptPermissionsRequest`，返回现有 `ScriptPermissions`。HTTP 拒绝 query 与任何正文，原生 gRPC 空消息拒绝未知字段；HTTP 明确输出四个完整状态对象和 false 布尔字段，按标准 ProtoJSON int64 输出共享版本。该方法普通 USER 无权限也可成功读取，身份失效、数据损坏和依赖失败使用既有身份或 SCRIPT_PERMISSION 错误，不能合成为四项 false。

### 交付依赖与部署

四项权限复用 Auth 存储、共享 CAS 与审计、管理员复核及 UC010 签发链。目标 Get/Manage 与本人读取由默认关闭的 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED` 启用，并要求用户端点与身份签发配置。目标方法要求完整管理员，本人方法沿普通 USER 鉴权。两种读取共用 actor 预算，最多 4096 个桶。

`app.script.maintain` 退出授撤白名单、目标查询、本人发现与 App JWS 投影。历史记录中的旧 ID 不具有授权效力。复用现有存储与审计，无需回填或迁移。部署时移除 `AUTH_SCRIPT_MAINTAINER_PERMISSION_ENDPOINTS_ENABLED` 及对应 Gateway 路由，Console 使用四项状态。

Gateway 依既有 SESSION 编排为 Auth audience 签发 USER 身份，保留该精确查询的路由及 typed adapter。公网及 Admin Console 的 HTTP、原生 gRPC、gRPC-Web 由路由 owner 固定，Console surface 为 ADMIN。Developer surface 不开放该脚本工作台读取。BFF 绑定当前 BrowserSession，只转发当前 Session，不接收浏览器自报 subjectAuthId。客户端在进入职责页面及权限失败恢复时重新读取，不缓存权限进 BrowserSession。

成功及错误均 private, no-store。身份缺失或失效沿用 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY（401 / UNAUTHENTICATED）；非法空请求载荷使用现有 INVALID_SCRIPT_PERMISSION_REQUEST（400 / INVALID_ARGUMENT）。超限沿 SCRIPT_PERMISSION_RATE_LIMITED（429 / RESOURCE_EXHAUSTED），损坏、存储/事务故障沿 SCRIPT_PERMISSION_UNAVAILABLE（503 / UNAVAILABLE）。入口关闭或路由未交付是能力不可用，不能映射为成功零权限。该方法不要求某项 permission，合法零授权 ACTIVE USER 不返回 403。

### 验收

1. 在真实 Mongo 副本集和生产 Wire 下，用已获签发权限的服务身份与同一 ACTIVE USER 的同一有效 Session，分别在未授予、正式授予提交后、正式撤销提交后调用现有 `IssueUserIdentityFromSession`。由 App 真实验签器检查三个新签 USER JWS 的同一 sub、独立 jti、正确 audience 和该权限依次缺失、存在、缺失。逐项覆盖四项权限，验证撤销一项时其他显式授权保持有效。
2. Auth audience 不披露脚本权限；UC010 所列其它既有 App 权限不回归；现有角色、其他脚本权限和错误 audience 不产生隐式授权。退役枚举编号和名称授撤返回 INVALID_ARGUMENT，旧专用 RPC 与 HTTP 路由退役。仅含历史 maintain 的用户返回四项 false，新签 App JWS 排除该权限。App 业务入口按各自 UC 验证实际命令与查询。
3. 覆盖管理员门禁、授予条件与 DISABLED 撤销、同版本并发冲突、重复动作、审计失败回滚以及授撤与签发竞争。不得把旧 JWS 在原有效窗口内仍可使用误报为撤销未生效。

验收包括任意 ACTIVE USER 的零授权完整四项、每项独立 grant 与组合、完整管理员无隐式 grant；subject 注入、body/query/未知 wire 字段及错误 audience；无管理员初始化或邮箱恢复就绪仍可读取本人；停用/CLOSED/代际失效身份失败与权威数据损坏；同一 Session 正式授撤后的本人结果和新签 App 身份变化；撤权与读取的提交竞争；保持原目标方法对本人仍要求完整管理员。通过真实 Mongo、生产 Wire 和生成客户端证明。

<a id="proposed-own-script-permissions"></a>

## 业务规则（UC-AUTH-038 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-001 -->
### BR-SMP-001：独立显式授权与目标门槛

Developer、Application 管理员、Reviewer、App 运维人员、完整平台管理员及 SYSTEM 均不自动获得任何脚本权限。四项权限之间无推导关系，持有任一项也不授予管理他人权限。四项均为平台用户权限，不是 OAuth Scope、应用 consent 或第三方可申请能力。

授予门槛沿用 [UC027 / BR-AOP-005](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005)：目标是 ACTIVE USER，且具备已验证邮箱与部署就绪的恢复能力。合法 ACTIVE 或 DISABLED USER 可由管理员查询，已有授权可撤销；查询和撤销不读取目标邮箱，也不依赖恢复就绪。DISABLED 保留 grant 但不生效；恢复不复活旧认证材料。SYSTEM、未知、CLOSED 不可管理；未授权调用在目标读取前拒绝，不泄露目标存在性。

<!-- 权威位置: use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-002 -->
### BR-SMP-002：共享版本、事务与审计

复用 `auth_principals.permissions`、共享 `permissionRevision` 和 `auth_permission_audit_events`。在现有 Auth 认证事务栅栏中复核管理者和目标，按目标共享版本 CAS，只增删明确选中的一项权限，保留其它权限。一次真实变化递增一次版本，与记录 actor/subject、精确 permission、action、reason、前后状态与版本、时间的不可变审计同事务提交。两个请求使用相同预期版本修改不同权限时至多一个成功。过期版本、重复动作、坏数据、审计失败和未确认提交不得报成功；结果未知时走正式查询，不盲目换版本重放。不记录 JWS、Session 或邮箱原文。

<!-- 权威位置: use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-003 -->
### BR-SMP-003：只向 App audience 投影已授权项

按 [UC010 / BR-IDN-002](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002) 将四项脚本权限纳入 `iwut-app-center` 服务端投影清单，只投影 ACTIVE USER 当前实际拥有的精确项。Auth audience 不披露这些权限，UC010 所列其它既有 App 权限继续独立投影。签发仍使用同一 Session 检查、JWS 格式、签名与有效期；不把权限加进 BrowserSession，也不新增角色 claim。

授撤与签发遵循 [BR-IDN-004](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 的事务提交顺序。撤销提交后新签发不再包含被撤销项；此前已签发身份仍受原 exp 与验签时钟容差约束，不承诺即时追回。

<!-- 权威位置: use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-004 -->
### BR-SMP-004：本人最小权限读取

本人方法以可信身份 authId 为唯一主体，空请求不接收目标或权限清单。目标 Get/Manage 继续要求完整管理员，查询本人也不例外。

返回 subjectAuthId、共享正数 permissionRevision 和 permissions，严格复用本 UC 当前四项枚举、状态对象和枚举顺序。四项均来自本次权威观察，返回完整、唯一集合，不分页或截断，不附带其他人员权限、资料、邮箱、恢复 blocker 或审计。

每项仍含 granted 和 effective。该方法只允许 ACTIVE USER 成功，因此每项 effective 与 granted 相等。零授权时仍成功返回全部四项，四个 granted/effective 都为 false；完整平台管理员也只有在另获显式 grant 后才有相应 true。成功的零权限与请求失败保持区分。

标准 ProtoJSON int64 按十进制字符串精确处理。HTTP 成功响应显式输出所有四项对象及 false 布尔字段，客户端先验证 subjectAuthId、正数版本、数组完整性、枚举唯一性与字段存在，再消费生成模型。漏项、重复项、缺布尔或不一致状态属于协议/数据错误，不能用 protobuf repeated 或 bool 的默认值合成为“无权限”。

<!-- 权威位置: use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-005 -->
### BR-SMP-005：本人在线观察与失败关闭

Auth 在现有认证事务协调边界内，以可信身份的 authId 和 accountRevision 确认当前 USER、ACTIVE 状态及有效代际，同时读取权威 permissions 和共享 permissionRevision。完整权限集合及正数版本必须结构有效；损坏、存储故障或提交结果未知失败关闭。不能从入站 JWS 的权限副本、BrowserSession、前端角色或管理者目标 snapshot 推导结果。

本人读取不要求完整管理员 bundle、管理员初始化标记、邮箱或恢复就绪，也不调用目标管理员 Get 来绕道实现。读取不改变 grant、permissionRevision、授权审计或 Session 业务状态，复用既有认证事务栅栏进行在线确认。

UNKNOWN、SYSTEM、DISABLED、CLOSED 或失效代际按身份拒绝处理，不返回四项 false 的成功结果。账号禁用时原 grant 按 BR-SMP-001 保留，管理员目标 Get 仍可观察 granted=true/effective=false；本人方法停止提供成功读取。账号恢复后按既有登录与代际规则建立有效身份，再读取保留授权。

授撤、账号变更与本人读取有明确事务提交顺序。读取可观察并发变更之前或之后的完整快照，集合与 revision 不得混用。撤权提交后发起的新本人读取排除该项，新的 App 身份签发按 BR-SMP-003 排除该项；已签 App JWS 沿既有 exp/容差窗口到期。本人读取结果只供本次职责发现，不作为 App 凭据、整个 Session 的权限租约或业务命令的 CAS 参数。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-027`

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005 -->
### BR-AOP-005：账号状态、恢复能力与授权事实

只有 ACTIVE USER 且具备激活邮箱和部署就绪恢复能力时可以 GRANT。账号被禁用时保留三项 grant 事实但不生效，Auth 不向该账号签发新的可信身份；账号恢复后仍须重新登录，既有 grant 可再次投影。账号 CLOSED 后由 UC025 的清理和保留规则处理，不作为可查询运维人员继续存在。

撤销不要求目标仍有邮箱或恢复能力，避免无法收紧权限。授予和撤销不改变 Developer、Reviewer、平台管理员、Session、设备凭据或 OAuth 状态。

### 来自 `UC-AUTH-010`

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002 -->
### BR-IDN-002：权威能力与 audience 投影

Auth 从 `auth_principals` 读取当前能力，不能信任 Session 创建时的能力副本、Gateway 传入的 claims 或客户端标签。`permissions` 必须是唯一字符串集合，permissionRevision 为正 int64；不合法的权威记录按不可用拒绝，不静默修复或忽略损坏权限。

每个 audience 配置可披露的 permission 集合及是否披露 developerStatus；签发权限为当前集合与 audience 集合的交集，稳定排序。首批最小策略：

| audience | 可披露权限 | Developer 状态 |
| --- | --- | --- |
| `iwut-app-center` | `app.application.restore`、`app.application.search`、`app.application.suspend`、`app.profile.review`、`app.script.publish`、`app.script.restore`、`app.script.review`、`app.script.suspend`、`app.version.review` | 有合法非 null 状态时携带 |
| `iwut-auth-center` | UC021/BR-ADM-001 固定四项管理权限 | 不携带 |

普通 USER 的 developerStatus 为 null 时省略该 claim，仍可签发合法用户身份；当前支持的非 null 状态见 [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004)。permissions 始终输出数组，允许为空，不自动推导管理员或 Reviewer 权限。

两项应用审核权限均来自 UC004 的独立显式 grant；不能从管理权限、Developer 状态或另一项审核权限推导。向 App 签发时保留精确值并稳定排序，只拥有其中一项时只签该项；不向 App 披露任何管理权限，不向 Auth audience 披露应用审核权限。

这只是允许 token 携带哪些能力，不表示调用者已获准执行目标业务。UC004 等后端继续检查其必需权限。新业务权限可扩充明确的服务端投影目录，不开放客户端自选权限，也不自动透传未知权限。不携带学生资料、关联 token、关联组、Session token 或私钥。首版不增加 role claim。

四项脚本权限的投影由已接受的 [UC-AUTH-038 / BR-SMP-003](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-003) 定义。仅 App audience 可见当前有效的显式授权。脚本作者沿用 App audience 的 `developer_status`。2026-11-11 修订移除 `app.script.maintain`，历史同名授权不进入签发结果。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004 -->
### BR-IDN-004：签发与撤销的一致性

签发授权确认点为步骤 5 的成功事务提交。与 Session/凭据撤销、账号禁用、权限及 Developer 状态修改有明确提交顺序：修改先提交时，后续确认不得使用旧状态；签发先提交的 JWS 是已授权的在途结果，随后撤销不追回它，最迟按 exp 与消费方容差停止接受。

Mongo 首版复用认证事务栅栏，并对参与确认的 Session、主体与认证凭据采用条件写以排除快照写偏差。后续 UC004 和 Developer 修改命令必须满足该一致性约定；不能先检查 Session，离开事务，再独立读取权限签发。

签发失败不提交 lastUsedAt；签发成功后，即使 Gateway 转发失败或后端拒绝业务，成功检查产生的 lastUsedAt 不回滚。不以权限不足为理由把一个仍有效的 Session 改为无效。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

UC038 新增已接受的本人读取 `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions`，GET `/v1/users/me/script-permissions`，空请求返回本人四项状态和共享版本。Gateway 采用 SESSION → Auth audience、ADMIN Console surface，原生 gRPC/HTTP/gRPC-Web 按精确方法接入。该本人方法不要求管理或脚本 permission，目标管理方法沿原规则鉴权。开关、无权限与失败区分唯一见 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-004)。


UC039 的 `ManagedUserSearchService/SearchUsers` 使用 `POST /v1/managed-users:search` 和原生 gRPC，业务及最小披露见 [UC039](../use-cases/UC-AUTH-039-search-users-for-administration.md)。Gateway 接入时使用 SESSION → Auth audience，限定 Admin surface。UC027 的固定管理和本人公开范围已接受增加精确 `app.application.search`，沿用现有方法及线格式。


UC038 的目标脚本权限查询和授撤方法按 [UC038 API 契约](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#api-契约) 固定 HTTP 和原生 gRPC。Gateway 按精确 RPC 接入 Admin 管理路由，采用 SESSION → Auth audience USER JWS，管理权限由 Auth 复核。旧 `ScriptMaintainerPermissionService` 及其两条 HTTP 路由退役。

2026-10-12 下表仅已交付基线。密码管理/恢复、默认密码登录已展开 UC033/034 DRAFT 和 auth-password-v1 草案，未注册真实入口；旧 REGISTER/BIND/凭据撤销、注销 Prepare/app.close Complete 须同步密码与防旁路门禁，新修订未实施，不提前启用或登记虚构公网清单。

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/device-logins` | AuthenticationService/BeginDeviceLogin | DIRECT | 200 |
| POST | `/v1/device-logins/{operation_id}/completion` | AuthenticationService/CompleteDeviceLogin | DIRECT | 201 |
| DELETE | `/v1/sessions/current` | AuthenticationService/RevokeCurrentSession | DIRECT | 200 |
| DELETE | `/v1/users/me/credentials/{credential_id}` | AuthenticationService/RevokeOwnCredential | DIRECT | 200 |
| GET | `/v1/users/me/profile` | UserProfileService/GetOwnProfile | SESSION | 200 |
| PATCH | `/v1/users/me/profile` | UserProfileService/EditOwnProfile | SESSION | 200 |
| GET | `/v1/user-profile-schema` | UserProfileService/GetProfileEditingSchema | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/ManageReviewerPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/GetReviewerPermission | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | ReviewerPermissionService/ManageApplicationReviewPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-review-permissions` | ReviewerPermissionService/GetApplicationReviewPermissions | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | ApplicationOperationsPermissionService/ManageApplicationOperationsPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-operation-permissions` | ApplicationOperationsPermissionService/GetApplicationOperationsPermissions | SESSION | 200 |
| GET | `/v1/academic-year-policy/schedule` | AcademicYearPolicyService/GetAcademicYearSchedule | SESSION | 200 |
| PUT | `/v1/academic-year-policy/schedule/next-rollover` | AcademicYearPolicyService/UpdateNextAcademicYearRollover | SESSION | 200 |
| DELETE | `/v1/users/me/application-user-storage/{application_id}` | ApplicationUserStorageService/ClearOwnApplicationUserStorage | SESSION | 200 |

原 `/v1/registrations` 和 completion 路径不注册，旧 BeginUserRegistration/CompleteUserRegistration RPC 返回 UNIMPLEMENTED；不重定向、不代为发起注册，也不因启用用户入口恢复旧方法。

UC011 是唯一注册入口，三个 DIRECT 路由的字段及 Session 例外见[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](../../platform/contracts/auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AcademicYearPolicyService package 为 `auth_center.v1.academic_year_policy`，两个方法由 Auth 在线复核当前完整平台管理员资格；精确时间、递推、并发和审计语义唯一见 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md)。管理入口由独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED` 控制且默认关闭；关闭管理入口不影响 Auth 内部消费已 provision 的时间表。

ApplicationUserStorageService package 为 `auth_center.v1.application_user_storage`。本人清除使用 SESSION 身份，`application_id` 仅由路径绑定，一次删除该用户与 Application 的 TEST/GREY/STABLE 数据，不返回应用 key/value。第三方读写另使用 `POST /v1/application-user-storage:batchGet` 与 `POST /v1/application-user-storage:mutate`；两者是 Auth 直接验证 opaque OAuth Bearer token 的 HTTP-only 资源端点，不经 SESSION 转换、不生成原生 gRPC 第三方方法。三个入口均由 `AUTH_APPLICATION_USER_STORAGE_ENABLED` 控制且默认关闭，精确语义见 [UC030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

### `platform/contracts/auth-session-identity-issuance-v1.md`：Session 到可信用户身份签发 v1

#### 内部 RPC

独立 API 路径 `auth_center/v1/identity/identity.proto`，package `auth_center.v1.identity`：

```text
/auth_center.v1.identity.UserIdentityService/IssueUserIdentityFromSession

IssueUserIdentityFromSessionRequest {
  string audience = 1;
}
IssuedUserIdentity {
  string identity_jws = 1;
  int64 expires_at_unix_seconds = 2;
}
```

以上为设计线格式，正式 Proto 及生成代码在实现时进入独立 API 仓库。首版仅 unary 原生 gRPC；不注册终端 HTTP、gRPC-Web 或网关公开路由。

- `authorization`：由 Gateway 自己生成的内部服务 Bearer JWS，严格遵循 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，不能使用客户端 Authorization。
- `x-iwut-session`：本次终端请求提供的唯一 token，采用 [auth-device-session-v1 的 Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，消息体不重复承载。
- 不接收 `x-iwut-identity` 作为签发授权，也不通过 JWS 自身换取新 JWS。
- 目标 audience 精确匹配预登记值；无空白修剪、URL 解释或客户端动态指定。首批值为 `iwut-auth-center` 和 `iwut-app-center`。
- body、metadata、返回体均不得进入通用请求/响应日志；传输必须受保护。客户端 token 与服务 token 均不能透传给最终业务服务。

#### 应用审核权限投影

用户能力投影唯一遵循 [UC010 / BR-IDN-002](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002)：App audience 可携带用户实际拥有的 `app.application.search`、`app.profile.review`、`app.version.review`、`app.application.suspend` 与 `app.application.restore`；Auth 管理权限不因此下发给 App。审核权限由 [UC004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) 管理，运维权限由 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 管理；均复用现有 `permissions` claim 和签发 RPC。平台管理员不会被自动投影为 Reviewer 或 Application 运维人员。

已接受的四项脚本权限按 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md) 独立授撤，按 UC010 的 App audience 清单投影。继续使用现有 `permissions` claim、签发 RPC 和 caller audience 配置。App 作者沿用 UC010 的 `developer_status`。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-038`（use-cases/UC-AUTH-038-manage-script-maintainer-permission.md）：本人读取修订记录
- `UC-AUTH-027`（use-cases/UC-AUTH-027-manage-application-operations-permissions.md）：目标与范围、参与者与依赖、输入与输出、API 契约、主流程、错误语义与运行约束、验收场景、实现依赖与交付边界、变更记录、2026-11-08 已接受的搜索权限交付
- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、交付依赖与非目标、参考、变更记录、2026-11-08 已接受的搜索权限投影
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：校园认证入口（UC031）、UC032 本人设备凭据管理、JSON 与载体、部署开关与验收、治理工作包路由、UC027 本人运维权限读取、UC020 同账号 Session 管理
- `platform/contracts/auth-session-identity-issuance-v1.md`（docs 根级共享文档）：范围与权威来源、服务授权扩展、签名与验签配置、请求与凭据流向、与现有契约的衔接

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-038-manage-script-maintainer-permission.md` | 111 | `e4ea641c92d6` |
| `use-cases/UC-AUTH-027-manage-application-operations-permissions.md` | 245 | `9fd8067fe545` |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 155 | `8e754f73c2f4` |
| `platform/contracts/auth-center-api-routing.md` | 171 | `ec86209bbd44` |
| `platform/contracts/auth-session-identity-issuance-v1.md` | 85 | `298ed207961b` |
