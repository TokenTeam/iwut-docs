<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-021 --spec tools/brief-specs/UC-AUTH-021.json -->
# Brief — UC-AUTH-021：授予与撤销平台管理员资格

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-021` 授予与撤销平台管理员资格 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-ADM-001`–`BR-ADM-008`（8 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

平台管理员向已有用户授予或撤销固定的平台管理权限集合，查询管理员名单与指定账号的资格，并以事务保证平台不会通过正常管理操作失去最后一个有效管理员。

系统尚未上线，本用例按首次部署设计管理员初始化，不提供旧 bootstrap 数据迁移或历史管理资格兼容分支。它不提供任意权限编辑、可配置角色、管理员分级、双人审批、用户搜索、账号禁用、Developer 暂停或账号注销。后三类治理动作由后续 UC 定义；本用例授予其管理权限不表示相应接口已经可用。

本设计已接受；UC004 的 bootstrap 与 UC010 的 Auth audience 投影同步引用本用例。权限仍须显式初始化或授予，不因部署启动自动扩权。

### 参与者与身份

- 操作人是 ACTIVE USER，持有面向 `iwut-auth-center` 的可信 USER JWS；JWS 必须包含 `auth.platform-admin.manage`，Auth 还在线复核其当前完整管理员资格。
- 目标通过明确的 subjectAuthId 定位。学校账号、associationToken、associationId、邮箱相同或同设备使用均不构成管理授权，不传播到其他 authId。
- 授予目标必须为 ACTIVE USER，已有激活邮箱且邮箱恢复部署就绪；不要求 Developer，也不要求已有审核权限。沿用 [UC013 恢复能力配置](../use-cases/UC-AUTH-013-apply-for-developer.md#实现约定) 所用的 `AUTH_EMAIL_RECOVERY_READY` 与 `AUTH_EMAIL_LOGIN_ENABLED` 就绪判断，不探测邮箱收件箱可达性。
- 撤销允许目标为 ACTIVE 或 DISABLED USER；邮箱未就绪或邮件服务临时故障不阻止撤销。SYSTEM 不能成为管理员。

### 输入与输出

```text
ManagePlatformAdministrator {
  subjectAuthId: AuthId
  action: GRANT | REVOKE
  expectedPermissionRevision: Int64  // 必填，正数
  reason: String                    // 去除两端空白后 1..1024 UTF-8 bytes
}
GetPlatformAdministrator { subjectAuthId: AuthId }
ListPlatformAdministrators {
  pageSize: Int?       // 缺省 20，范围 1..50；显式 0 非法
  afterAuthId: AuthId? // 缺省或空字符串为第一页
}
PlatformAdministratorState {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  membership: NONE | GRANTED
  effective: Bool                    // ACTIVE 且 GRANTED
  permissionRevision: Int64
  grantBlockers: GrantBlocker[]
}
PlatformAdministratorPage {
  items: PlatformAdministratorState[]
  nextAfterAuthId: AuthId?
  observedAt: Instant
}
```

Get 和 Manage 返回 PlatformAdministratorState。membership 表示保存的权限集合事实，effective 表示当前能否作为有效管理员，不以客户端提供的 role 字段为依据。grantBlockers 固定按 `ALREADY_GRANTED, ACCOUNT_DISABLED, EMAIL_REQUIRED, EMAIL_RECOVERY_UNAVAILABLE` 顺序返回所有适用项；它是观察时的门禁提示，提交时必须重新验证。

### API

独立 package `auth_center.v1.platform_administrator`，service `PlatformAdministratorService`：

| 方法 | Auth HTTP 路径 | 请求与成功响应 |
| --- | --- | --- |
| `ManagePlatformAdministrator` | `POST /v1/platform-administrators:manage` | 命令 → 200，状态 |
| `GetPlatformAdministrator` | `POST /v1/platform-administrators:get` | 指定 authId → 200，状态 |
| `ListPlatformAdministrators` | `POST /v1/platform-administrators:list` | 分页条件 → 200，列表 |

三个方法均为 Gateway SESSION 路由、audience=`iwut-auth-center`，外部前缀 `/auth-center`；Gateway 通过 UC010 换取 USER JWS 后转发。Auth 入口只接受 trusted-identity-v1，不接受 OAuth access token、service JWS 或直接提交 Session 代替。body 不包含 actor、permissions 或管理员集合版本。

实现同时交付 HTTP/JSON 与原生 gRPC，完整 RPC 名逐项加入鉴权表；Gateway 三协议路由独立验收，不以 service 通配符开放。采用 ProtoJSON、Timestamp/UTC、optional revision/pageSize presence；拒绝未知/重复 JSON 字段、query、非法枚举及超过 16 KiB 的解码请求。响应 no-store，错误和日志不记录 JWS、邮箱或 Session。

### 主流程

#### 授予或撤销

1. 验证 USER JWS、方法权限、参数与限额。
2. 进入 Auth 认证事务协调边界，确认治理初始化完成，在线复核操作人是 ACTIVE 且持有完整管理权限集合。
3. 读取目标 USER、当前集合、共享 permissionRevision；损坏记录拒绝，不自动修复。
4. 校验 expectedPermissionRevision。GRANT 检查目标状态、邮箱及恢复就绪；REVOKE 检查当前存在管理权限，并检查最后管理员约束。
5. 原子修改固定管理集合，严格增加一次目标 permissionRevision，保存不可变治理审计；保留所有非管理权限。
6. 确认提交后返回同一事务的目标状态。允许撤销自己的管理资格；成功响应不要求操作人仍有被撤销的资格，但后续请求必须拒绝。

结果未知返回不可用。客户端先读取现状，再决定是否以新 revision 提交；成功撤销自身后无法查询管理接口，应回到普通用户界面，不凭失败响应重新授予自己。

#### 查询

Get 对存在且结构合法的 USER 返回当前资格，允许返回 NONE 和 DISABLED；不存在或 SYSTEM 统一返回目标不可用。List 仅列 GRANTED（包括 DISABLED），不列普通用户；授予前可按明确 authId 查询目标。

分页按 authId 的字节字典序递增，使用简单二进制排序规则和最后返回 authId 作游标，游标不要求仍存在于名单中。返回最多 pageSize 条，以额外一条判断是否存在下一页。每页同一检查点复核操作人并读取结果，跨页不承诺快照；管理操作始终使用最新目标 revision。列表不附带邮箱、学生资料、完整 permissions 或在线设备信息。

### 错误语义与运行约束

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效 USER JWS | 沿用 trusted-identity-v1 | 401 / UNAUTHENTICATED |
| 当前调用者无完整管理资格或非 ACTIVE | `PLATFORM_ADMIN_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 非法输入 | `INVALID_PLATFORM_ADMIN_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不存在或为 SYSTEM | `PLATFORM_ADMIN_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| 版本不符、重复授予或撤销 | `PLATFORM_ADMIN_CONFLICT` | 409 / ABORTED |
| GRANT 目标 DISABLED、无激活邮箱或恢复未就绪 | `PLATFORM_ADMIN_GRANT_BLOCKED` | 409 / FAILED_PRECONDITION，携带首个 blocker |
| 会失去最后有效管理员 | `LAST_PLATFORM_ADMIN_REQUIRED` | 409 / FAILED_PRECONDITION |
| 版本耗尽 | `PERMISSION_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 入口限额 | `PLATFORM_ADMIN_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 未初始化、损坏记录、存储故障、未知提交结果 | `PLATFORM_ADMIN_UNAVAILABLE` | 503 / UNAVAILABLE |

三个入口由独立默认关闭的 `AUTH_PLATFORM_ADMIN_ENDPOINTS_ENABLED` 和用户入口总开关共同控制；显式开启而用户入口关闭属于配置错误。命令行初始化不依赖 HTTP 入口开关。限流按已认证 actorAuthId 分离读写桶，初始默认每分钟读 60、写 10，容量有界，不以目标 authId 建立无限桶；具体部署参数可调整但不能关闭身份复核。

### 测试与验收

1. NONE、完整集合、非法部分集合（含仅有审核管理权限）；授予/撤销保留两项审核权限、其他权限、Developer 状态和 Session。SYSTEM、禁用目标授予失败，但可撤销禁用目标。
2. 邮箱或恢复未就绪阻止授予；不阻止已授予管理员查询和撤销。无邮箱普通用户仍可由 UC011 先完成激活，不通过治理接口代填邮箱。
3. 只有审核管理权限、伪造权限、App audience、service/OAuth token 均不能访问；撤销前签发的旧管理 JWS 在撤销后读写均失败。
4. 最后一名 ACTIVE 管理员不能自撤；另一名为 DISABLED 仍不足。两个管理员并发互撤/自撤、同目标与 UC004 并发写入、撤销操作人与其授予第三人并发，均有明确事务先后且无写偏差。
5. 并发初始化只有一次写入；同目标重跑返回已执行，其他目标拒绝；成功后撤销资格再重跑不会复活；旧格式或不一致标记拒绝且不修改。审计/标记写入失败回滚，未知提交重跑不重复事件。
6. GRANT/REVOKE 与 UC010 签发竞争，撤销提交后新签发不含权限；App audience 和 OAuth 不泄露管理权限。
7. 查询只返回允许字段；分页游标目标被撤销后仍可翻页；跨页变化不影响提交时 CAS。自撤成功返回状态，下一次管理查询拒绝。
8. 真实 Mongo 副本集、生产 Wire、真实签名及生成 HTTP/gRPC 客户端覆盖上述规则；不能以只有 mock 的领域测试替代并发和事务验收。Gateway SESSION 三协议及 CLI 首次初始化分别验证。

### 实现依赖与联动

UC004、UC010、UC011/012 后端已具备基础；本用例不依赖后续账号或 Developer 治理 UC 的实现。没有 App 新接口依赖。

实施时同步修改 UC004 的 bootstrap 权限集合与初始化定义、UC010 的 Auth audience 投影、共享路由/鉴权契约、治理权限存储校验、API、首次部署与恢复说明，并生成脚本 brief；本用例已 ACCEPTED，四项固定集合与相关用例同步生效。后续禁用/注销用例接受前必须引用 BR-ADM-003 并验证共享协调边界。

## 业务规则（UC-AUTH-021 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001 -->
### BR-ADM-001：固定管理权限集合

管理员集合 v1 固定为以下四项：

| permission | 能力边界 |
| --- | --- |
| `auth.platform-admin.manage` | 本用例的管理员资格管理与查询 |
| `auth.reviewer.manage` | UC004 的两项审核权限管理 |
| `auth.account.manage` | 后续账号禁用与恢复用例 |
| `auth.developer.manage` | 后续 Developer 暂停与恢复用例 |

不新增 principalType，不存第二份可独立修改的 role/granted 布尔值，不从 Developer 身份推导资格。四项全部存在为 GRANTED，四项均不存在为 NONE。

只包含部分管理权限（包括仅有 auth.reviewer.manage）的集合不符合本用例数据约束，失败关闭，不能视为普通用户或由 GRANT 静默补齐。与四项无关的权限不参与该分类。

GRANT 将 NONE 转为 GRANTED；REVOKE 将 GRANTED 转为 NONE，删除整个管理集合。管理权限不记录多个叠加授予来源。审核权限本身、Developer 状态、设备凭据和 Session 均保留。不得通过 UC004 修改集合中的任何一项。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-002 -->
### BR-ADM-002：在线授权与授予前置条件

所有读写入口都同时验证 JWS 中的管理权限与当前数据库中的 ACTIVE USER、完整管理员集合；仅有过期前的旧管理 JWS 不足以继续操作。缺少初始化标记或数据损坏按不可用处理。

授予管理员时检查当前激活邮箱及恢复就绪配置。该条件不强制管理员日常使用邮箱登录或生物识别，也不因为邮件临时不可用而撤销现有资格。未来允许解绑邮箱的 UC 必须防止管理员移除最后恢复方式；本用例不引入解绑。恢复就绪配置关闭时仍允许现有管理员查询和撤销。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-003 -->
### BR-ADM-003：最后有效管理员保护

治理初始化成功后，正常治理命令提交时必须至少保留一个 ACTIVE USER 且 membership=GRANTED。DISABLED 管理员、SYSTEM 及损坏记录不能用于满足此约束。该判定不依赖瞬时 SMTP 健康，不声称能够证明某人仍掌握登录材料。

允许自我撤销，但必须存在另一个满足条件的管理员。禁止两个管理员在并发撤销中分别基于旧快照把双方都移除。后续账号禁用、注销及任何减少有效管理员数量的入口必须复用这一约束，不能只在本用例做检查。

统计和修改须参与同一可写事务协调点；单纯 Mongo snapshot 下 count 后更新不同主体不能防止并发写偏差。复用现有全局认证事务栅栏并确认它覆盖所有相关写入口；若实现调整为专用治理栅栏，仍须与身份签发、UC004 和后续账号状态变更建立一致锁顺序。无需 Redis 或跨服务事务。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-004 -->
### BR-ADM-004：共享版本、原子审计与重试

沿用 UC004 的 auth_principals.permissionRevision，整个集合变更只增加一次；不得另设管理员专属版本绕开其他权限写入。相同目标、相同 revision 的 UC004 与本用例并发写入最多一个成功。重复 GRANT 已完整授予的目标、重复 REVOKE 无任何管理权限的目标均冲突，不新增审计或递增版本。版本耗尽拒绝写入。

独立 append-only `auth_platform_admin_audit_events` 保存 eventId、operation、actorType、actorAuthId（用户操作才有）、subjectAuthId、reason、集合版本 1、before/after 管理权限子集、before/after permissionRevision、occurredAt。普通操作 actorType=USER；初始化使用 BOOTSTRAP_COMMAND 命令来源，不伪造用户操作人。事件 ID 唯一，查询索引按 subjectAuthId/occurredAt/eventId；不复用 Developer 的一次性开通审计唯一约束。

权限集合、目标版本、审计及初始化标记（若涉及）在同一事务提交；审计失败全部回滚。事务重试重新检查操作人、最后管理员与目标版本，保留同一候选事件 ID。未知提交结果返回不可用，不声称成功或安全未发生。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-005 -->
### BR-ADM-005：一次性管理员初始化

使用单个 `auth_runtime/platform-admin-bootstrap` 消费标记，记录 subjectAuthId、eventId、occurredAt 和管理集合版本 1。不增加第二个治理初始化标记。该记录表示首次初始化已经消费，不是权限来源副本，不因管理员被撤销而清除。 原始 bootstrap 审计可受 UC025 的注销保留期清理约束；清理器只在原事件已满 180 天且原 subject 为合法 CLOSED 墓碑时，在同一 Auth 事务中设置此消费标记的 auditRetiredAt 并删除事件。消费校验在事件存在时仍严格核对；缺失事件仅在 auditRetiredAt 不早于 occurredAt+180 天、不晚于当前时间且 subject 仍为合法 CLOSED 时接受，任意缺失或损坏仍失败关闭。该收据不授予权限、不替代消费标记，不保存整份历史审计。

首次部署使用显式停服运维命令，不启动监听，不接受远程匿名调用，不因 ENV 或普通启动自动授予：

```text
auth-center bootstrap-platform-admin --auth-id <existing-user-auth-id>
```

仅当消费标记不存在、没有任何四项管理权限记录时可首次执行。目标必须已有 ACTIVE USER、激活邮箱及恢复就绪能力；在一个事务中授予完整集合、增加一次 permissionRevision、写治理审计并消费标记。其他用户审核权限不影响初始化，不自动授予应用审核权限。

同一目标命令重跑且消费标记完整一致时，仅返回 applied=false 和原事件 ID，不再写权限、版本或审计；该检查先于目标当前邮箱/权限条件，所以后来撤销也不会被重跑恢复。不同目标或损坏标记拒绝。首次执行才返回 applied=true。后续授予必须走已认证管理 API。

本用例实施时直接调整 UC004 的首次 bootstrap 定义与实现，不增加 migrate 命令、旧状态转换或自动补齐权限。治理 API 要求初始化标记符合本集合版本；旧格式标记或部分管理权限记录按不兼容数据拒绝，不自动清除或修复。开发测试环境通过显式重建测试数据验证新流程；本文不授权删除任何现存数据，也不要求保留上线前测试库的升级兼容性。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-006 -->
### BR-ADM-006：最小查询与错误披露

只有当前有效管理员可查询目标及列表，未授权者不能通过错误区别目标存在与否。鉴权先于读取目标。Auth ID 参数沿用现有 AuthId 的语法与长度校验；查询不提供邮箱或学号搜索，也不自动把管理员名单开放给普通用户。

管理写入以目标版本冲突优先于状态迁移判定；GRANT 在版本通过后按账号、邮箱、恢复就绪顺序检查；REVOKE 再检查是否存在管理权限与最后管理员约束。权威数据损坏始终按不可用，不转成普通门禁失败。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-007 -->
### BR-ADM-007：签发投影与撤销边界

本用例实施时，UC010 的 `iwut-auth-center` allowlist 扩展为 BR-ADM-001 四项；`iwut-app-center` 不增加这些管理权限。权限只取当前权威集合，不进入 OAuth Scope Catalog、ID token 或用户 consent，不向第三方委托。

授予/撤销与 UC010 签发共用认证事务协调边界，已确认撤销后不得新签含撤销权限的身份。已经签出的 USER JWS 沿用既有 TTL/leeway，不能保证离线消费方立即失效；本用例与 UC004 写入口在线复核当前管理权限，因此旧 JWS 不能继续完成相应管理写入。其他权限和 Session 不因本操作自动撤销。

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-008 -->
### BR-ADM-008：恢复与初始化的边界

最后管理员保护防止正常命令使有效管理员数量归零，不解决管理员丢失全部凭据、邮箱不可访问或数据损坏。初始化不能充当重复恢复后门。

首版正常恢复复用 UC012 邮箱登录。全部管理员无法恢复时，必须由部署运营者按独立、可审计的停服恢复规程处置；该规程及其身份核验、备份、命令授权属于生产上线前依赖，不以手工直接改 Mongo、清空消费标记或重复 bootstrap 代替。应急恢复 CLI 尚未由本 UC 定义，不宣称已经交付。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。UC020 独立入口的缺失/畸形或混用载体为 INVALID_SESSION_TOKEN（400），载体合法但当前资格失效为 SESSION_INVALID（401），不得沿用 UC008 的免有效性检查。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-021`（use-cases/UC-AUTH-021-manage-platform-administrators.md）：主流程/授予或撤销、主流程/查询、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-021-manage-platform-administrators.md` | 207 | `c21e150ed9b5` |
| `platform/contracts/auth-device-session-v1.md` | 125 | `5ff17feb92f9` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
