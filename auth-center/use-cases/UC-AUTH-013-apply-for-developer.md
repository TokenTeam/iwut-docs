# UC-AUTH-013：申请 Developer

状态：`ACCEPTED`

## 目标与范围

> 当前普通 USER 已具备激活邮箱和可用的邮箱登录方式，明确申请 Developer 后，由 Auth 检查前置条件并自助开通资格。

首版采用**满足条件直接 APPROVED，不设人工资格审核**。应用创建、资料/版本审核与发布仍由 App Center 各自用例决定；Developer 开通不代表任何应用自动获准发布，也不授予 Reviewer 或管理员权限。

本用例包含申请命令及本人资格/申请条件查询，不包含暂停、恢复、拒绝后重申、人工审批、资格注销或条款管理。Developer 是原 USER 的可选资格，不创建另一个身份或新的 authId。

## 参与者与前置条件

- 调用者持有有效 ACTIVE USER Session，可以来自 UC007 设备登录或 UC012 邮箱登录；不强制本次 Session 必须由邮箱登录取得。
- 申请目标只取自 Session 的 authId；SYSTEM、他人代申请或客户端自报角色均不允许。
- 首次开通时，该账号有 UC011 的当前激活邮箱，且部署已完整启用 UC012 邮箱登录及设备恢复流程；仅资料中填写邮箱、尚未验证的提案或客户端声称已验证都不够。
- 用户明确点击申请；普通注册、激活邮箱、登录或进入开发者页面不自动开通。

## 输入与输出

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

## 主流程

1. 用户查询本人资格；客户端对无邮箱账号引导 UC011，对未交付/暂未开放邮箱登录的部署显示暂不可申请。
2. 用户明确申请，Auth 在线检查 Session 和当前主体。
3. 在事务确认点检查当前 Developer 状态、激活邮箱、邮箱登录能力启用配置；只允许尚未进入 Developer 生命周期的普通 USER 首次开通。
4. 原子将 developerStatus 从 null 设为 APPROVED，记录 activatedAt/主体 updatedAt 和不可变开通审计，保留其它字段和权限。
5. 提交确定成功后返回结果。客户端沿用当前 Session，后续访问 App Center 时由 UC010 签发带有当前 Developer 状态的 JWS。

## 业务规则

<a id="br-dev-006"></a>
### BR-DEV-006：本人显式申请与邮箱前置条件

只有当前有效 ACTIVE USER 可申请本人资格。首次开通要求 Auth 当前已激活邮箱，并且 UC012 的邮箱登录和本机设备登记能力已经实际交付及启用；不能拿客户端布尔值、邮箱资料字段、历史验证操作或“曾经绑定过”代替当前事实。

这里“可用”指部署的功能配置、必要密钥/邮件适配器配置校验通过，且产品入口已交付启用，不通过申请时给邮箱再发测试信判断。邮件服务临时故障不证明该账号失去邮箱控制权，也不自动撤销已有 Developer。停用整个邮箱登录能力时，禁止新增开通；既有资格保持原状态，由部署恢复该能力，不批量改成 SUSPENDED。

不要求用户先退出设备登录再做一次邮箱登录，不要求再次上传 associationToken、原始学号或学校凭据，也不宣称完成权威学生认证。日常设备登录的便利性保留。

<a id="br-dev-007"></a>
### BR-DEV-007：自助开通与受限状态迁移

本用例唯一的新状态迁移是 `null → APPROVED`，在同一事务中完成，不先写 PENDING 再自动审批。现有状态枚举继续引用 [BR-DEV-004](UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004)，不删除 PENDING/REJECTED/SUSPENDED，也不改变消费方含义。

| 当前状态 | 申请结果 |
| --- | --- |
| null，前置条件满足 | 首次开通为 APPROVED |
| APPROVED | 幂等返回当前资格和可核实的 activatedAt，不新增审计或重置时间；既有记录没有开通时间时返回 null，不伪造历史 |
| PENDING | 已有申请，冲突，不在本入口自动审批 |
| REJECTED 或 SUSPENDED | 拒绝重新申请，不恢复资格 |
| 非法状态或数据不一致 | 不可用，失败关闭 |

重复成功申请仍需有效 Session 和当前 APPROVED 状态，但不把全局邮箱登录临时停用变成重做首次开通；已有资格是否可用于业务由当前状态和消费用例判断。后续状态变化后再重试必须返回当前拒绝/冲突，不能根据历史成功记录把资格写回 APPROVED。

本用例不设置人工审核任务，不需要 Reviewer permission，也不发送待审批通知。未来若要人工审核或重新申请，新增命令及迁移规则，不通过改一个运行配置悄悄改变本用例状态机。

<a id="br-dev-008"></a>
### BR-DEV-008：资格写入与审计的一致性

当前 Session、主体状态、邮箱绑定与 Developer 状态必须在一次确认边界内检查。邮箱更换沿用 UC011 的原子替换，不产生中间无邮箱状态；未来若引入解绑，必须与本命令在同一认证事务栅栏内确认，避免申请与解绑并发破坏邮箱前置条件。

开发者状态、首次开通记录与审计原子提交。开通记录按 authId 唯一，记录首次 activatedAt；审计包含 actorAuthId/subjectAuthId（两者相同）、操作类型、null 到 APPROVED 的前后状态、用于决策的邮箱绑定 revision、时间和结果，不记录邮箱明文或任何凭据秘密。只更新所需主体字段，不覆盖 profile、学生关联、permissions 或 permissionRevision。

与 [BR-IDN-004](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 使用相同认证事务栅栏：开通提交后开始的新身份签发读取 APPROVED；之前已签发的短期 JWS 保持原 claims，不原地修改或追发。UC002 从同一权威 principal 读取新的 Developer 状态，不另建一个最终一致的状态副本。

并发首次申请最多一次 null 到 APPROVED 和一条开通事件，其余按当前结果处理。仓储失败、审计失败全部回滚；提交结果未知返回不可用。用户可以用原有效 Session 重试或查询本人状态，不需要新建账号、重新登录或用 requestId 强制重复申请。

<a id="br-dev-009"></a>
### BR-DEV-009：资格与应用授权的边界

开通仅修改原 authId 的 developerStatus，不修改 principalType，不授予 `app.version.review`、`auth.reviewer.manage` 或其它原子权限，也不创建应用、预占 App Center 配额或签发 OAuth 凭据。

App Center 继续检查可信身份中的 APPROVED，并执行自身配额、管理员归属及审核规则；本 UC 不替代这些门禁。学校关联只是客户端声明，不保证“一个自然人只开通一个 Developer”，也不把关联组内其它账号一并升级。

Developer 日常可继续使用设备凭据。首版不提供邮箱解绑；未来解绑命令应禁止 Developer 移除最后可用邮箱登录方式，更换邮箱则继续使用 UC011 先验证后替换。UC009 撤销最后设备凭据保持允许，已激活邮箱可通过 UC012 在新设备恢复。邮箱服务偶发故障或用户日后失去邮箱访问权不自动等同于违规暂停。

<a id="br-dev-010"></a>
### BR-DEV-010：本人资格查询与门禁解释

GetOwnDeveloperEligibility 只允许有效 Session 查询本人，返回当前合法状态及有序 blockers。普通 USER 的 null 是正常结果；SYSTEM/无效主体拒绝，不将未知或损坏状态解释为普通用户。

仅当状态为 null、存在当前激活邮箱且邮箱登录部署能力启用时 canApply 为 true。null 状态可同时返回 EMAIL_REQUIRED 和 EMAIL_LOGIN_UNAVAILABLE，顺序按枚举列出；非 null 状态分别返回 ALREADY_DEVELOPER、EXISTING_APPLICATION 或 REAPPLICATION_NOT_ALLOWED，canApply 为 false。查询不暴露邮箱地址或其它账号，也不隐式创建开通记录。

查询结果不作为提交凭证；读取失败返回不可用，不能回退到客户端缓存显示“可以申请”。本查询与 Apply 均不要求已有 Developer JWS，避免资格申请先要求资格的循环依赖。

## 错误语义

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

## 测试与验收

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

## 实现约定

- 接口及字段 presence 按 [Developer 自助申请协议 v1](../../platform/contracts/auth-developer-application-v1.md)；使用现有 Session 格式，无新签名算法或密钥。
- `AUTH_DEVELOPER_APPLICATION_ENABLED` 默认 false，与 `AUTH_USER_ENDPOINTS_ENABLED` 一起控制两个用户入口；显式启用前者但关闭后者视为配置错误。关闭时 HTTP/gRPC 均不注册这两个方法，不扩大其它方法权限。
- `AUTH_EMAIL_RECOVERY_READY` 默认 false，是运维确认 Gateway/客户端邮箱登录与设备恢复入口已交付的部署声明，不接受请求覆盖，也不表示 Auth 自动探测了 UI。首次申请的邮箱登录能力就绪条件为该声明为 true 且现有 `AUTH_EMAIL_LOGIN_ENABLED=true` 的配置已校验并成功组合真实邮件适配器。配置畸形按既有启动校验拒绝；合法关闭只使首次申请不可用，不阻止已开通账号查询/幂等申请。`AUTH_EMAIL_BINDING_ENABLED` 不作为额外条件，邮箱事实取当前权威绑定；既有邮箱登录可独立启用。
- 复用 [BR-LGN-004](UC-AUTH-007-login.md#br-lgn-004) 在线检查与 [BR-LGN-016](UC-AUTH-012-login-with-email.md#br-lgn-016) 的两类 Session，有效调用更新既有会话使用时间，不延长固定寿命。事务内重新确认，不能只信 middleware 的预检查。
- 当前邮箱按 [BR-EML-004](UC-AUTH-011-set-and-activate-email.md#br-eml-004) 的绑定记录读取：待验证提案不算激活邮箱；合法缺失返回 EMAIL_REQUIRED，损坏记录返回不可用。全局就绪配置在进程启动时固定，变更通过重启生效；申请不发送邮件、不新建邮箱目录。
- 开通记录按 authId 唯一，首次时间使用服务端 UTC 毫秒，并与审计、principal 更新同事务提交。记录含可核实的邮箱绑定 revision；状态 null 却已有开通记录、非法 revision/时间或未知枚举均失败关闭。已存在合法 Developer 状态但无开通记录允许作为历史数据读取，activatedAt 为 null；不在此用例回填。
- 申请结果优先按当前合法 Developer 状态处理；首次申请同时缺少邮箱和恢复能力时，先返回 DEVELOPER_EMAIL_REQUIRED。本人查询收集两个 blocker，遵守 BR-DEV-010 的固定顺序。存储读取/完整性失败不能伪装为业务 blocker。
- 单机部署使用有界全局和每账号限流；Apply 与查询均受限，参数、有限容量和超出容量行为在实现配置中明确并测试。未认证请求复用有界来源门禁；不因任意 token 创建无限账号桶，不引入 Redis。限流不写开通审计，幂等成功不重复写审计。
- 后端联合验收使用真实 Auth/Mongo 与实际 App Center verifier/服务入口，证明同一 Session 在开通后签发的 App audience JWS 可进入原有创建流程，且配额/权限约束继续生效；不需要为了本工作包先实现公网 Gateway 或移动客户端。公网三协议路由和 UI 仍独立交付，生产恢复就绪声明保持关闭，直至完成部署验收。

## 交付依赖

- UC011/012 后端已合入 `auth-center/v1` 的 `58f8a67`（API `46544d1`），且合入后通过 check、race、真实 Mongo/Wire/HTTP/gRPC 验收；后端实现无未满足的前置 UC。产品启用仍要求邮箱恢复链路实际交付，按上述部署声明控制。
- 后端复用 UC002 的权威状态、UC007/012 的有效 Session 和 UC010 的事务栅栏；新增开通记录/审计及 Apply/GetOwn 两个精确 RPC。
- HTTP/gRPC/gRPC-Web 经 Gateway DIRECT 携带原 Session 交给 Auth 在线检查；不得要求 Developer 权限或先交换含 Developer claim 的 JWS。精确路由和 Proto 字段已由共享契约固定；Auth/API 属于本次工作包，Gateway 转发与客户端交付单独验收。
- 完成真实 Mongo/HTTP/gRPC 并发与故障验收，及“申请成功后用原 Session 访问 App Center”的联合验收。全局和每账号请求限流有界，参数为部署选择。
- 人工资格审核、暂停/恢复、拒绝后重新申请、资格注销及历史 Developer 开通记录迁移不在本用例中静默处理。

## 变更记录

- 2026-09-26：确认 UC011/012 后端依赖已合入并通过测试，接受 UC013；固定 RPC/HTTP、nullable 字段、限流/失败语义及默认关闭的恢复就绪声明，生成实现 brief。
- 2026-09-24：提出 Developer 自助申请草案，以当前激活邮箱和已启用邮箱登录为门禁，直接 null 到 APPROVED，不增加人工资格审核。
