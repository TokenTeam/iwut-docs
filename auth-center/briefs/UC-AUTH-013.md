<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-013 --spec tools/brief-specs/UC-AUTH-013.json -->
# Brief — UC-AUTH-013：申请 Developer

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-013` 申请 Developer |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-DEV-006`–`BR-DEV-010`（5 条） |
| 外部引用 BR | `BR-DEV-004`，`BR-EML-004`，`BR-IDN-004`，`BR-LGN-004`、`BR-LGN-016`（来自 `UC-AUTH-002`、`UC-AUTH-007`、`UC-AUTH-010`、`UC-AUTH-011`、`UC-AUTH-012`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-developer-application-v1.md`、`platform/contracts/auth-device-session-v1.md` |

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

> 当前普通 USER 已具备激活邮箱和可用的邮箱登录方式，明确申请 Developer 后，由 Auth 检查前置条件并自助开通资格。

首版采用**满足条件直接 APPROVED，不设人工资格审核**。应用创建、资料/版本审核与发布仍由 App Center 各自用例决定；Developer 开通不代表任何应用自动获准发布，也不授予 Reviewer 或管理员权限。

本用例包含申请命令及本人资格/申请条件查询，不包含暂停、恢复、拒绝后重申、人工审批、资格注销或条款管理。Developer 是原 USER 的可选资格，不创建另一个身份或新的 authId。

### 参与者与前置条件

- 调用者持有有效 ACTIVE USER Session，可以来自 UC007 设备登录或 UC012 邮箱登录；不强制本次 Session 必须由邮箱登录取得。
- 申请目标只取自 Session 的 authId；SYSTEM、他人代申请或客户端自报角色均不允许。
- 首次开通时，该账号有 UC011 的当前激活邮箱，且部署已完整启用 UC012 邮箱登录及设备恢复流程；仅资料中填写邮箱、尚未验证的提案或客户端声称已验证都不够。
- 用户明确点击申请；普通注册、激活邮箱、登录或进入开发者页面不自动开通。

### 输入与输出

```text
ApplyForDeveloper {}

DeveloperApplicationResult {
  developerStatus: APPROVED
  activatedAt: Instant | null     // 既有资格无可核实开通记录时为 null
}

GetOwnDeveloperEligibility {}

OwnDeveloperEligibility {
  developerStatus: null | PENDING | APPROVED | REJECTED | SUSPENDED
  activatedAt: Instant | null
  canApply: bool
  blockers: []DeveloperApplicationBlocker
}

DeveloperApplicationBlocker =
  EMAIL_REQUIRED | EMAIL_LOGIN_UNAVAILABLE |
  ALREADY_DEVELOPER | EXISTING_APPLICATION | REAPPLICATION_NOT_ALLOWED
```

申请命令不接受期望角色、目标 authId、审核通过标志、学生材料、邮箱字符串或 Developer 状态。没有申请理由表单或额外学校认证。activatedAt 是本用例首次实际开通时间；既有状态没有可核实开通记录时，查询返回 null，不通过查询虚构历史。

查询的 canApply 只是同一读取快照下的指引，提交时重新确认；允许普通 USER 的 developerStatus 为 null，不用 UC002 的内部批量查询冒充本人状态查询。

### 主流程

1. 用户查询本人资格；客户端对无邮箱账号引导 UC011，对未交付/暂未开放邮箱登录的部署显示暂不可申请。
2. 用户明确申请，Auth 在线检查 Session 和当前主体。
3. 在事务确认点检查当前 Developer 状态、激活邮箱、邮箱登录能力启用配置；只允许尚未进入 Developer 生命周期的普通 USER 首次开通。
4. 原子将 developerStatus 从 null 设为 APPROVED，记录 activatedAt/主体 updatedAt 和不可变开通审计，保留其它字段和权限。
5. 提交确定成功后返回结果。客户端沿用当前 Session，后续访问 App Center 时由 UC010 签发带有当前 Developer 状态的 JWS。

### 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 请求携带未知字段、query 参数或非法消息格式 | `INVALID_DEVELOPER_APPLICATION_REQUEST` | 400 / INVALID_ARGUMENT |
| Session 缺失、重复、编码非法、无效或主体不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 请求大小超限 | `DEVELOPER_APPLICATION_REQUEST_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 首次申请没有当前激活邮箱 | `DEVELOPER_EMAIL_REQUIRED` | 409 / FAILED_PRECONDITION |
| 首次申请时邮箱登录能力未启用 | `DEVELOPER_EMAIL_LOGIN_UNAVAILABLE` | 503 / UNAVAILABLE |
| 当前 PENDING | `DEVELOPER_APPLICATION_EXISTS` | 409 / ALREADY_EXISTS |
| 当前 REJECTED 或 SUSPENDED | `DEVELOPER_REAPPLICATION_NOT_ALLOWED` | 403 / PERMISSION_DENIED |
| 限流 | `DEVELOPER_APPLICATION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 仓储/审计故障、数据损坏或提交结果未知 | `DEVELOPER_APPLICATION_UNAVAILABLE` | 503 / UNAVAILABLE |

### 测试与验收

1. 激活邮箱且邮箱登录能力启用的普通 USER 明确申请，原 authId 变为 APPROVED；设备登录和邮箱登录 Session 均可申请。
2. 未绑定、仅有待验证提案、资料内邮箱、客户端自报验证成功均不能首次开通；未启用邮箱登录时拒绝首次开通。
3. 注册、邮箱激活、登录、本人查询不隐式授予 Developer；无需额外学生信息或角色输入。
4. 并发和重复申请只有一次迁移/审计，activatedAt 稳定；暂停或拒绝后重试不能复活历史成功状态；PENDING 不被自动批准。
5. Session/主体禁用、邮箱变化与申请并发有明确提交顺序；审计失败回滚，提交未知可重试/查询。
6. 权限、资料、关联和已有 Session 不被覆盖；UC002 读取 APPROVED，新的 UC010 App audience JWS 携带 APPROVED，Auth audience 投影不变。
7. 本人查询正确处理 null、全部已有枚举、blockers 和不可用；不能查询他人或以旧查询结果绕过提交校验。
8. App Center 仍执行自身配额和审核，Developer 不自动获得 Reviewer/管理员权限；已有 APPROVED 的历史数据不通过查询伪造激活记录。
9. 默认不注册入口；显式启用入口但恢复就绪声明或 UC012 功能关闭时，普通账号收到明确 blocker，已有 APPROVED 可幂等读取。配置非法拒绝启动，未知 RPC 不获得匿名访问。
10. HTTP 与 gRPC 返回同一 nullable 状态/时间语义；严格拒绝未知字段、query 和替代 Session 载体；全局及每账号限流有界并返回重试时间。

### 实现约定

- 接口及字段 presence 按 [Developer 自助申请协议 v1](../../platform/contracts/auth-developer-application-v1.md)；使用现有 Session 格式，无新签名算法或密钥。
- `AUTH_DEVELOPER_APPLICATION_ENABLED` 默认 false，与 `AUTH_USER_ENDPOINTS_ENABLED` 一起控制两个用户入口；显式启用前者但关闭后者视为配置错误。关闭时 HTTP/gRPC 均不注册这两个方法，不扩大其它方法权限。
- `AUTH_EMAIL_RECOVERY_READY` 默认 false，是运维确认 Gateway/客户端邮箱登录与设备恢复入口已交付的部署声明，不接受请求覆盖，也不表示 Auth 自动探测了 UI。首次申请的邮箱登录能力就绪条件为该声明为 true 且现有 `AUTH_EMAIL_LOGIN_ENABLED=true` 的配置已校验并成功组合真实邮件适配器。配置畸形按既有启动校验拒绝；合法关闭只使首次申请不可用，不阻止已开通账号查询/幂等申请。`AUTH_EMAIL_BINDING_ENABLED` 不作为额外条件，邮箱事实取当前权威绑定；既有邮箱登录可独立启用。
- 复用 [BR-LGN-004](../use-cases/UC-AUTH-007-login.md#br-lgn-004) 在线检查与 [BR-LGN-016](../use-cases/UC-AUTH-012-login-with-email.md#br-lgn-016) 的两类 Session，有效调用更新既有会话使用时间，不延长固定寿命。事务内重新确认，不能只信 middleware 的预检查。
- 当前邮箱按 [BR-EML-004](../use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-004) 的绑定记录读取：待验证提案不算激活邮箱；合法缺失返回 EMAIL_REQUIRED，损坏记录返回不可用。全局就绪配置在进程启动时固定，变更通过重启生效；申请不发送邮件、不新建邮箱目录。
- 开通记录按 authId 唯一，首次时间使用服务端 UTC 毫秒，并与审计、principal 更新同事务提交。记录含可核实的邮箱绑定 revision；状态 null 却已有开通记录、非法 revision/时间或未知枚举均失败关闭。已存在合法 Developer 状态但无开通记录允许作为历史数据读取，activatedAt 为 null；不在此用例回填。
- 申请结果优先按当前合法 Developer 状态处理；首次申请同时缺少邮箱和恢复能力时，先返回 DEVELOPER_EMAIL_REQUIRED。本人查询收集两个 blocker，遵守 BR-DEV-010 的固定顺序。存储读取/完整性失败不能伪装为业务 blocker。
- 单机部署使用有界全局和每账号限流；Apply 与查询均受限，参数、有限容量和超出容量行为在实现配置中明确并测试。未认证请求复用有界来源门禁；不因任意 token 创建无限账号桶，不引入 Redis。限流不写开通审计，幂等成功不重复写审计。
- 后端联合验收使用真实 Auth/Mongo 与实际 App Center verifier/服务入口，证明同一 Session 在开通后签发的 App audience JWS 可进入原有创建流程，且配额/权限约束继续生效；不需要为了本工作包先实现公网 Gateway 或移动客户端。公网三协议路由和 UI 仍独立交付，生产恢复就绪声明保持关闭，直至完成部署验收。

### 交付依赖

- UC011/012 后端已合入 `auth-center/v1` 的 `58f8a67`（API `46544d1`），且合入后通过 check、race、真实 Mongo/Wire/HTTP/gRPC 验收；后端实现无未满足的前置 UC。产品启用仍要求邮箱恢复链路实际交付，按上述部署声明控制。
- 后端复用 UC002 的权威状态、UC007/012 的有效 Session 和 UC010 的事务栅栏；新增开通记录/审计及 Apply/GetOwn 两个精确 RPC。
- HTTP/gRPC/gRPC-Web 经 Gateway DIRECT 携带原 Session 交给 Auth 在线检查；不得要求 Developer 权限或先交换含 Developer claim 的 JWS。精确路由和 Proto 字段已由共享契约固定；Auth/API 属于本次工作包，Gateway 转发与客户端交付单独验收。
- 完成真实 Mongo/HTTP/gRPC 并发与故障验收，及“申请成功后用原 Session 访问 App Center”的联合验收。全局和每账号请求限流有界，参数为部署选择。
- 人工资格审核、暂停/恢复、拒绝后重新申请、资格注销及历史 Developer 开通记录迁移不在本用例中静默处理。

## 业务规则（UC-AUTH-013 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-006 -->
### BR-DEV-006：本人显式申请与邮箱前置条件

只有当前有效 ACTIVE USER 可申请本人资格。首次开通要求 Auth 当前已激活邮箱，并且 UC012 的邮箱登录和本机设备登记能力已经实际交付及启用；不能拿客户端布尔值、邮箱资料字段、历史验证操作或“曾经绑定过”代替当前事实。

这里“可用”指部署的功能配置、必要密钥/邮件适配器配置校验通过，且产品入口已交付启用，不通过申请时给邮箱再发测试信判断。邮件服务临时故障不证明该账号失去邮箱控制权，也不自动撤销已有 Developer。停用整个邮箱登录能力时，禁止新增开通；既有资格保持原状态，由部署恢复该能力，不批量改成 SUSPENDED。

不要求用户先退出设备登录再做一次邮箱登录，不要求再次上传 associationToken、原始学号或学校凭据，也不宣称完成权威学生认证。日常设备登录的便利性保留。

<!-- 权威位置: use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-007 -->
### BR-DEV-007：自助开通与受限状态迁移

本用例唯一的新状态迁移是 `null → APPROVED`，在同一事务中完成，不先写 PENDING 再自动审批。现有状态枚举继续引用 [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004)，不删除 PENDING/REJECTED/SUSPENDED，也不改变消费方含义。

| 当前状态 | 申请结果 |
| --- | --- |
| null，前置条件满足 | 首次开通为 APPROVED |
| APPROVED | 幂等返回当前资格和可核实的 activatedAt，不新增审计或重置时间；既有记录没有开通时间时返回 null，不伪造历史 |
| PENDING | 已有申请，冲突，不在本入口自动审批 |
| REJECTED 或 SUSPENDED | 拒绝重新申请，不恢复资格 |
| 非法状态或数据不一致 | 不可用，失败关闭 |

重复成功申请仍需有效 Session 和当前 APPROVED 状态，但不把全局邮箱登录临时停用变成重做首次开通；已有资格是否可用于业务由当前状态和消费用例判断。后续状态变化后再重试必须返回当前拒绝/冲突，不能根据历史成功记录把资格写回 APPROVED。

本用例不设置人工审核任务，不需要 Reviewer permission，也不发送待审批通知。未来若要人工审核或重新申请，新增命令及迁移规则，不通过改一个运行配置悄悄改变本用例状态机。

<!-- 权威位置: use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-008 -->
### BR-DEV-008：资格写入与审计的一致性

当前 Session、主体状态、邮箱绑定与 Developer 状态必须在一次确认边界内检查。邮箱更换沿用 UC011 的原子替换，不产生中间无邮箱状态；未来若引入解绑，必须与本命令在同一认证事务栅栏内确认，避免申请与解绑并发破坏邮箱前置条件。

开发者状态、首次开通记录与审计原子提交。开通记录按 authId 唯一，记录首次 activatedAt；审计包含 actorAuthId/subjectAuthId（两者相同）、操作类型、null 到 APPROVED 的前后状态、用于决策的邮箱绑定 revision、时间和结果，不记录邮箱明文或任何凭据秘密。只更新所需主体字段，不覆盖 profile、学生关联、permissions 或 permissionRevision。

与 [BR-IDN-004](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 使用相同认证事务栅栏：开通提交后开始的新身份签发读取 APPROVED；之前已签发的短期 JWS 保持原 claims，不原地修改或追发。UC002 从同一权威 principal 读取新的 Developer 状态，不另建一个最终一致的状态副本。

并发首次申请最多一次 null 到 APPROVED 和一条开通事件，其余按当前结果处理。仓储失败、审计失败全部回滚；提交结果未知返回不可用。用户可以用原有效 Session 重试或查询本人状态，不需要新建账号、重新登录或用 requestId 强制重复申请。

<!-- 权威位置: use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-009 -->
### BR-DEV-009：资格与应用授权的边界

开通仅修改原 authId 的 developerStatus，不修改 principalType，不授予 `app.version.review`、`auth.reviewer.manage` 或其它原子权限，也不创建应用、预占 App Center 配额或签发 OAuth 凭据。

App Center 继续检查可信身份中的 APPROVED，并执行自身配额、管理员归属及审核规则；本 UC 不替代这些门禁。学校关联只是客户端声明，不保证“一个自然人只开通一个 Developer”，也不把关联组内其它账号一并升级。

Developer 日常可继续使用设备凭据。首版不提供邮箱解绑；未来解绑命令应禁止 Developer 移除最后可用邮箱登录方式，更换邮箱则继续使用 UC011 先验证后替换。UC009 撤销最后设备凭据保持允许，已激活邮箱可通过 UC012 在新设备恢复。邮箱服务偶发故障或用户日后失去邮箱访问权不自动等同于违规暂停。

<!-- 权威位置: use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-010 -->
### BR-DEV-010：本人资格查询与门禁解释

GetOwnDeveloperEligibility 只允许有效 Session 查询本人，返回当前合法状态及有序 blockers。普通 USER 的 null 是正常结果；SYSTEM/无效主体拒绝，不将未知或损坏状态解释为普通用户。

仅当状态为 null、存在当前激活邮箱且邮箱登录部署能力启用时 canApply 为 true。null 状态可同时返回 EMAIL_REQUIRED 和 EMAIL_LOGIN_UNAVAILABLE，顺序按枚举列出；非 null 状态分别返回 ALREADY_DEVELOPER、EXISTING_APPLICATION 或 REAPPLICATION_NOT_ALLOWED，canApply 为 false。查询不暴露邮箱地址或其它账号，也不隐式创建开通记录。

查询结果不作为提交凭证；读取失败返回不可用，不能回退到客户端缓存显示“可以申请”。本查询与 Apply 均不要求已有 Developer JWS，避免资格申请先要求资格的循环依赖。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-002`

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004 -->
### BR-DEV-004：状态语义

首版只公开 `PENDING/APPROVED/REJECTED/SUSPENDED`。UC-APP-005 只把
`SUSPENDED` 判断为暂停，但 Auth 返回完整枚举，让消费方不需要用 bool 掩盖未知状态。

普通 USER 可以不是 Developer，此时 `developerStatus = null`；SYSTEM principal 也不具有
Developer 状态。两者都不能作为本查询的成功结果，且不得被伪装成 `PENDING`。

### 来自 `UC-AUTH-011`

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-004 -->
### BR-EML-004：更换与原子激活

本规则适用于 BIND。每个账号只保留一个当前可验证提案；新 Begin 成功创建操作时使旧提案失效，且必须先通过 revision 和限额检查。重发不延长旧验证码寿命，生成新验证码和新 operationId；晚到的旧邮件不能激活。Begin 的数据库失败不替换原提案。

邮箱绑定 revision 独立于用户资料 revision；未绑定为 0，每次成功激活递增一次。请求当前已激活的同一规范化地址返回 `EMAIL_ALREADY_ACTIVE`，不发邮件、不增加 revision。提交必须与 Begin 固定的 expectedRevision 相符，且操作仍是当前提案；冲突不自动覆盖新绑定。

激活将唯一邮箱归属、账号绑定、revision、操作成功结果和最小审计记录原子提交。旧邮箱在此之前始终有效；新验证码错误、过期、投递失败、冲突或事务回滚均不删除旧绑定。提交后旧地址释放，可被以后验证成功的账号使用；它不再具有原账号的认证资格。

更换不撤销已有设备 Session，不修改设备密钥或 Developer 状态。邮箱登录操作及设备/Session 扩展由 [UC012 草案](../use-cases/UC-AUTH-012-login-with-email.md) 独立交付，不是本用例的前置依赖；其入口未实现时保持关闭。

### 来自 `UC-AUTH-010`

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004 -->
### BR-IDN-004：签发与撤销的一致性

签发授权确认点为步骤 5 的成功事务提交。与 Session/凭据撤销、账号禁用、权限及 Developer 状态修改有明确提交顺序：修改先提交时，后续确认不得使用旧状态；签发先提交的 JWS 是已授权的在途结果，随后撤销不追回它，最迟按 exp 与消费方容差停止接受。

Mongo 首版复用认证事务栅栏，并对参与确认的 Session、主体与认证凭据采用条件写以排除快照写偏差。后续 UC004 和 Developer 修改命令必须满足该一致性约定；不能先检查 Session，离开事务，再独立读取权限签发。

签发失败不提交 lastUsedAt；签发成功后，即使 Gateway 转发失败或后端拒绝业务，成功检查产生的 lastUsedAt 不回滚。不以权限不足为理由把一个仍有效的 Session 改为无效。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-004 -->
### BR-LGN-004：有效期与在线检查

首版采用固定绝对有效期：T_session 通过 AUTH_SESSION_TTL 配置，为部署必填的正时长，创建时固定 expiresAt；缺失/非法配置拒绝接流量。配置采用 Go duration 格式，示例部署值为 `720h`（30 天）；该示例不是隐式默认值。本轮不自动滑动续期、不签发 refresh token，也不因请求活跃无限延长会话。到期后必须重新完成本用例的设备认证并建立新 Session，不延长旧会话的 expiresAt。后续若增加续期，另行设计轮换与并发语义。

一次成功会话检查必须得到一致、当前的事实：token 摘要匹配，Session 未撤销且 `now < expiresAt`，所属主体为 ACTIVE USER，作为会话认证依据的设备凭据仍有效且归属一致。缺失、损坏、超时或无法读取均失败关闭，不能回退到客户端缓存或只凭旧 JWT 放行。

首版不缓存正向会话授权结果，权威读取不得使用可能落后的副本。建议使用一致快照读取主体、凭据和 Session；检查与撤销/禁用存在并发时，以明确的检查快照为边界。变更提交后才开始的新检查必须看到变更；先已通过的请求可能继续执行，不承诺取消在途业务。

成功检查还须完成 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010) 的使用时间更新；不能先返回检查成功，再异步记录使用时间。此更新不改变固定 expiresAt。

清理过期会话只是存储维护；即使记录未被删除也不能再通过检查。更改配置不追溯改变已有 expiresAt；紧急失效使用显式撤销，不通过重解释时间或静默换令牌完成。

### 来自 `UC-AUTH-012`

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-016 -->
### BR-LGN-016：邮箱登录 Session 与邮箱更换边界

本次 Session 的 authenticationMethod 明确为 `EMAIL_CODE_AND_DEVICE`，credentialId 必填，并记录登录时邮箱绑定 revision 作为认证来源证据，不保存邮箱明文或验证码。既有 `DEVICE_CREDENTIAL` Session 语义不变。Session token、固定时长、在线检查、10 条上限和 LRU 复用 UC007 的 BR-LGN-003、BR-LGN-004 和 BR-LGN-010；撤销复用 UC008/009。

邮箱登录成功即已授权本机设备，后续 Session 有效性依赖当前主体、Session 与所引用的设备凭据。**后来更换邮箱不撤销已授权设备及其 Session**，认证来源 revision 不是每次在线检查的额外相等条件。更换邮箱只使旧绑定的未完成邮箱登录操作失败；收回已授权设备访问需 UC009 撤销凭据，只退出会话用 UC008。这与普通设备登录保持一致，不能把改邮箱宣称为退出全部设备。

本机后续通过 UC007 自动登录得到 `DEVICE_CREDENTIAL` Session；它与最初邮箱登录 Session 共享同一凭据撤销边界。UC007 的检查器、UC008/009、UC010 签发与所有有效 Session 入口必须明确支持新认证方法并检查 credentialId，未知方法仍拒绝；不能仅改数据库 method 字符串就开放入口。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- Reviewer 管理的 `subject_auth_id` 由路径绑定，覆盖消息体中同名值。
- 普通设备注册/登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

#### 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖九个资料/认证 HTTP 方法与两个 Reviewer 管理方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/auth-developer-application-v1.md`：Developer 自助申请协议 v1

#### 范围与兼容性

本契约固定 [UC013](../use-cases/UC-AUTH-013-apply-for-developer.md) 在客户端、Gateway 与 Auth 之间的格式。资格前置条件、迁移、审计和部署就绪含义由 UC013 拥有；不改变 UC002 内部批量查询或既有 JWS claims。

#### RPC 与认证载体

API 目录 `auth_center/v1/developer_application/`；package `auth_center.v1.developer_application`；service `DeveloperApplicationService`；Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/developer_application;developer_application`。

| full method | 认证 |
| --- | --- |
| `/auth_center.v1.developer_application.DeveloperApplicationService/ApplyForDeveloper` | 必需有效 USER Session，只申请本人 |
| `/auth_center.v1.developer_application.DeveloperApplicationService/GetOwnDeveloperEligibility` | 必需有效 USER Session，只查询本人 |

两者使用 [设备协议的 Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)：恰好一个规范 `x-iwut-session` 值。缺失、空值、多值或非规范编码返回 SESSION_INVALID；Authorization、cookie、x-iwut-identity 或 body 中的 token 均不能替代它。替代身份头的拒绝规则沿用既有 Session 入口。DEVICE_CREDENTIAL 与 EMAIL_CODE_AND_DEVICE 均接受，其它认证方法失败关闭；不能要求已有 Developer 身份或权限。方法逐项登记，未知 RPC 默认拒绝。

#### 消息字段

以下是设计字段表；可执行 Proto 及生成代码进入独立 API 仓库。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `ApplyForDeveloperRequest` | 空消息 |
| `DeveloperApplicationResult` | `1: auth_center.v1.developer_status.DeveloperStatus developer_status`；`2: optional int64 activated_at_unix_ms` |
| `GetOwnDeveloperEligibilityRequest` | 空消息 |
| `OwnDeveloperEligibility` | `1: optional auth_center.v1.developer_status.DeveloperStatus developer_status`；`2: optional int64 activated_at_unix_ms`；`3: bool can_apply`；`4: repeated DeveloperApplicationBlocker blockers` |

复用 UC002 的 DeveloperStatus 枚举，不创建另一套状态数字。Apply 成功时 developer_status 必为 DEVELOPER_STATUS_APPROVED；本人查询普通用户的状态字段 absent，代表业务 null。presence 为真但值为 UNSPECIFIED 或未知枚举均不是合法业务输出。

activated_at_unix_ms 是正整数 UTC Unix 毫秒；没有可核实开通记录时 absent，不用 0 伪造时间。ProtoJSON 对 absent optional 字段省略，对 int64 输出十进制字符串；客户端把省略映射为业务 null。can_apply=false 和空 blockers 可按标准 ProtoJSON 省略，客户端读取其默认值。字段名推荐 lowerCamelCase。

DeveloperApplicationBlocker 固定数字：`DEVELOPER_APPLICATION_BLOCKER_UNSPECIFIED=0`、`EMAIL_REQUIRED=1`、`EMAIL_LOGIN_UNAVAILABLE=2`、`ALREADY_DEVELOPER=3`、`EXISTING_APPLICATION=4`、`REAPPLICATION_NOT_ALLOWED=5`；后五个 Proto 枚举名统一加 `DEVELOPER_APPLICATION_BLOCKER_` 前缀。服务端不输出 UNSPECIFIED 或重复 blocker，顺序由 UC013 BR-DEV-010 决定。

两个请求拒绝未知字段（包括原生 gRPC 的 protobuf unknown fields）；不接受 authId、邮箱、状态、requestId 或客户端就绪声明。查询没有一次性凭据，申请天然按当前账号状态幂等。

#### HTTP 与 Gateway

| HTTP | Auth 内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

Apply annotation body 为 `"*"`，客户端提交空 JSON 对象 `{}`，拒绝空 body、null 或数组；GET 无 body。两个入口均拒绝 query 参数。公共 HTTP 前缀 `/auth-center` 在转发前剥离；原生 gRPC full method 不加前缀，gRPC-Web 沿用既有终止契约。

遵守 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md) 的严格 JSON、默认 16 KiB 消息上限、415 内容类型/压缩拒绝及 Cache-Control: no-store。DIRECT 保留原 Session 并交 Auth 在线验证，不执行 SESSION-to-JWS，不清洗非法身份载体。

错误 reason/HTTP/gRPC 状态由 UC013 定义；超大消息为 DEVELOPER_APPLICATION_REQUEST_TOO_LARGE。限流带正整数秒 retryAfterSeconds metadata 和 HTTP Retry-After。空结果/部分结果不得用于掩盖事务失败；提交未知返回不可用，允许用户沿用原 Session 查询或重试。

#### 交付边界

两个用户方法受 UC013 的默认关闭部署开关控制，HTTP/gRPC 注册保持一致。Auth/API 实现不等于 Gateway 路由或客户端入口已交付。内部 UC002 继续只提供原生 gRPC，不因新增本人查询开放给终端。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-013`（use-cases/UC-AUTH-013-apply-for-developer.md）：变更记录
- `UC-AUTH-002`（use-cases/UC-AUTH-002-batch-get-developer-statuses.md）：目标与范围、调用者与输入、输出、主流程、异常流程、数据模型、API 契约、测试与验收、非目标、变更记录
- `UC-AUTH-011`（use-cases/UC-AUTH-011-set-and-activate-email.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、实现约定、交付依赖与边界、变更记录
- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、交付依赖与非目标、参考、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-012`（use-cases/UC-AUTH-012-login-with-email.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、实现约定、交付依赖、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：路由边界
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-013-apply-for-developer.md` | 163 | `ba7680baf68d` |
| `use-cases/UC-AUTH-002-batch-get-developer-statuses.md` | 151 | `98d2b3e33077` |
| `use-cases/UC-AUTH-011-set-and-activate-email.md` | 277 | `fe77d446d400` |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 136 | `bf30266c7c29` |
| `use-cases/UC-AUTH-007-login.md` | 250 | `c38e3a56e232` |
| `use-cases/UC-AUTH-012-login-with-email.md` | 201 | `e2692ee1e896` |
| `platform/contracts/auth-center-api-routing.md` | 98 | `2e9488c5ba40` |
| `platform/contracts/auth-developer-application-v1.md` | 54 | `c1c3edf0c679` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
