# Auth Center 设计标识符注册表

状态：`ACTIVE`

本文件只索引 Auth Center bounded context 的权威 UC 与 BR，不复制规则正文。跨系统契约位于 `platform/`，不登记为 Auth UC 或 BR。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Auth Center | `UC-AUTH-014` |
| Business Rule / Identity Issuance | `BR-IDN-007` |
| Business Rule / Scope Catalog | `BR-SCP-006` |
| Business Rule / Developer Status | `BR-DEV-013` |
| Business Rule / System Principal | `BR-SYS-005` |
| Business Rule / Reviewer Permission | `BR-RVW-005` |
| Business Rule / User Profile | `BR-UPF-012` |
| Business Rule / User Registration | `BR-REG-009` |
| Business Rule / Login and Session | `BR-LGN-019` |
| Business Rule / Email Binding | `BR-EML-010` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `UC-AUTH-001` | 获取 Scope Catalog 快照 | `ACCEPTED` | [UC-AUTH-001-get-scope-catalog-snapshot.md](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | — | 第一个提供方纵切片；共享线格式见根级平台契约。 |
| `UC-AUTH-002` | 批量读取 Developer 状态 | `ACCEPTED` | [UC-AUTH-002-batch-get-developer-statuses.md](use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | — | 为 App Center 审核批准门禁提供 fail-closed 状态查询。 |
| `UC-AUTH-003` | 解析 System Principal | `ACCEPTED` | [UC-AUTH-003-resolve-system-principal.md](use-cases/UC-AUTH-003-resolve-system-principal.md) | — | 为跨服务系统动作提供 Auth-owned opaque actor。 |
| `UC-AUTH-004` | 管理 Reviewer 权限 | `ACCEPTED` | [UC-AUTH-004-manage-reviewer-permission.md](use-cases/UC-AUTH-004-manage-reviewer-permission.md) | — | PLATFORM_ADMIN 管理显式 reviewer grant/revoke。后端已实现；[brief](briefs/UC-AUTH-004.md)。 |
| `UC-AUTH-005` | 用户编辑自己的资料 | `ACCEPTED` | [UC-AUTH-005-edit-own-user-profile.md](use-cases/UC-AUTH-005-edit-own-user-profile.md) | — | 本人显式设置/删除、字段定义、资料容量与单文档乐观并发；含配套查询契约。 |
| `UC-AUTH-006` | 创建用户 | `ACCEPTED` | [UC-AUTH-006-create-user.md](use-cases/UC-AUTH-006-create-user.md) | — | 显式创建、设备证明、必填学生关联、原子提交及未知结果恢复。 [brief](briefs/UC-AUTH-006.md)。 |
| `UC-AUTH-007` | 登录并建立会话 | `ACCEPTED` | [UC-AUTH-007-login.md](use-cases/UC-AUTH-007-login.md) | — | 设备登录、会话检查、10 条有效会话上限与 LRU 淘汰。 [brief](briefs/UC-AUTH-007.md)。 |
| `UC-AUTH-008` | 撤销自己的当前 Session | `ACCEPTED` | [UC-AUTH-008-revoke-own-session.md](use-cases/UC-AUTH-008-revoke-own-session.md) | — | 由 token 定向、幂等撤销当前 Session，不改变设备凭据。 [brief](briefs/UC-AUTH-008.md)。 |
| `UC-AUTH-009` | 撤销自己的设备凭据 | `ACCEPTED` | [UC-AUTH-009-revoke-own-credential.md](use-cases/UC-AUTH-009-revoke-own-credential.md) | — | 有效用户撤销本人凭据，并使引用它的 Session 后续检查失败。 [brief](briefs/UC-AUTH-009.md)。 |
| `UC-AUTH-010` | 由 Session 签发可信用户身份 | `ACCEPTED` | [UC-AUTH-010-issue-user-identity-from-session.md](use-cases/UC-AUTH-010-issue-user-identity-from-session.md) | — | 受授权服务以有效 Session 换取目标 audience 的短期用户 JWS；不缓存身份结果。 |
| `UC-AUTH-011` | 设置并激活邮箱 | `ACCEPTED` | [UC-AUTH-011-set-and-activate-email.md](use-cases/UC-AUTH-011-set-and-activate-email.md) | — | 无 Session 验证后创建账号，有效 Session 绑定/更换；已有账号邮箱登录独立交付。 |
| `UC-AUTH-012` | 使用邮箱登录 | `ACCEPTED` | [UC-AUTH-012-login-with-email.md](use-cases/UC-AUTH-012-login-with-email.md) | — | 邮箱验证码授权本机设备，回到原账号并建立 Session；不自动注册。 |
| `UC-AUTH-013` | 申请 Developer | `ACCEPTED` | [UC-AUTH-013-apply-for-developer.md](use-cases/UC-AUTH-013-apply-for-developer.md) | — | 当前激活邮箱及可用邮箱登录为前提，自助开通 APPROVED；不增加人工资格审核。 |

## Business Rules

### Scope Catalog (`BR-SCP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SCP-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001) | — | — |
| `BR-SCP-002` | 完整一致快照 | Snapshot / Consistency | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-002) | — | — |
| `BR-SCP-003` | 单调 revision 与生成时间 | Versioning / Audit | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003) | — | — |
| `BR-SCP-004` | ScopeDefinition 投影 | Field / Projection | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) | — | — |
| `BR-SCP-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-005) | — | 使用 trusted-service-identity-v1。 |

### Developer Status (`BR-DEV`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-DEV-001` | Developer 状态权威所有权 | Boundary / Authority | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-001) | — | — |
| `BR-DEV-002` | 有界且唯一的批量输入 | Validation / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-002) | — | — |
| `BR-DEV-003` | 完整结果与 fail closed | Consistency / Failure | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-003) | — | — |
| `BR-DEV-004` | 状态语义 | Field / Projection | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) | — | — |
| `BR-DEV-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-005) | — | 使用 trusted-service-identity-v1。 |
| `BR-DEV-006` | 本人显式申请与邮箱前置条件 | Authorization / Recovery | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-006) | — | — |
| `BR-DEV-007` | 自助开通与受限状态迁移 | Lifecycle / Boundary | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-007) | — | — |
| `BR-DEV-008` | 资格写入与审计的一致性 | Atomicity / Audit | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-008) | — | — |
| `BR-DEV-009` | 资格与应用授权的边界 | Authority / Separation | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-009) | — | — |
| `BR-DEV-010` | 本人资格查询与门禁解释 | Query / Eligibility | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-010) | — | — |
| `BR-DEV-011` | 开发者公开 ID 与唯一占用 | Identity / Uniqueness | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-011) | — | — |
| `BR-DEV-012` | 已开通账号首次补设公开 ID | Compatibility / Atomicity | [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md#br-dev-012) | — | — |

### System Principal (`BR-SYS`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SYS-001` | Auth 所有权与不可登录 | Boundary / Authority | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-001) | — | — |
| `BR-SYS-002` | 按 purpose 唯一且稳定 | Identity / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-002) | — | — |
| `BR-SYS-003` | 最小授权解析 | Authorization / Boundary | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-003) | — | — |
| `BR-SYS-004` | 消费方失败关闭 | Failure / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-004) | — | — |

### Reviewer Permission (`BR-RVW`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-RVW-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-001) | — | — |
| `BR-RVW-002` | 管理员不隐式成为 Reviewer | Authorization / Separation | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-002) | — | — |
| `BR-RVW-003` | 乐观并发与不可变审计 | Concurrency / Audit | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-003) | — | — |
| `BR-RVW-004` | 撤销传播上界 | Security / Revocation | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-004) | — | — |

### User Profile (`BR-UPF`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-UPF-001` | 主动提交与资料信任边界 | Boundary / Consent | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001) | — | — |
| `BR-UPF-002` | 平台字段定义与稳定标识 | Field / Catalog | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002) | — | — |
| `BR-UPF-003` | 字段值类型与声明式校验 | Field / Validation | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-003) | — | — |
| `BR-UPF-004` | 仅当前可用用户编辑本人资料 | Authorization / Boundary | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004) | — | — |
| `BR-UPF-005` | 显式设置与删除 | Command / Mutation | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-005) | — | — |
| `BR-UPF-006` | 写入校验与删除独立 | Validation / Deletion | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-006) | — | — |
| `BR-UPF-007` | 操作与资料容量上限 | Capacity / Boundary | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007) | — | 首版容量规则已接受。 |
| `BR-UPF-008` | 资料初始化与乐观并发 | Lifecycle / Concurrency | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008) | — | — |
| `BR-UPF-009` | 无变化与结果不确定的重试 | Concurrency / Retry | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009) | — | — |
| `BR-UPF-010` | 主体内嵌资料与单文档原子提交 | Persistence / Atomicity | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010) | — | — |
| `BR-UPF-011` | 资料披露与操作记录 | Privacy / Observability | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-011) | — | — |

### User Registration (`BR-REG`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-REG-001` | 显式创建与平台账号独立 | Boundary / Identity | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-001) | — | — |
| `BR-REG-002` | 正式主体与最小初始化 | Lifecycle / Provision | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-002) | — | — |
| `BR-REG-003` | 设备凭据持有证明与唯一归属 | Authentication / Ownership | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-003) | — | — |
| `BR-REG-004` | 学号关联的声明与隐私边界 | Privacy / Trust | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-004) | — | — |
| `BR-REG-005` | 关联组独立与应用隔离 | Identity / Association | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-005) | — | — |
| `BR-REG-006` | 原子创建与结果不确定的恢复 | Atomicity / Retry | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-006) | — | — |
| `BR-REG-007` | 注册入口的限额与秘密最小暴露 | Capacity / Privacy | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-007) | — | — |
| `BR-REG-008` | 关联密钥隔离与单实例离线轮换 | Security / Migration | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-008) | — | ENV 注入当前/上一密钥组；启动前每批 500 条迁移、全量核验，按版本幂等重跑。 |

### Login and Session (`BR-LGN`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-LGN-001` | 账号来源与认证方法隔离 | Authentication / Boundary | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-001) | — | — |
| `BR-LGN-002` | 挑战绑定与一次性证明 | Authentication / Replay | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-002) | — | — |
| `BR-LGN-003` | 会话权威与秘密令牌 | Session / Secret | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-003) | — | — |
| `BR-LGN-004` | 有效期与在线检查 | Session / Validation | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-004) | — | — |
| `BR-LGN-005` | 当前 Session 的定向撤销 | Session / Revocation | [UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md#br-lgn-005) | — | 只撤销所提交 token 对应的 Session，不撤销设备凭据。 |
| `BR-LGN-006` | 多账号与会话独立 | Identity / Isolation | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-006) | — | — |
| `BR-LGN-007` | 原子登录与重试 | Atomicity / Retry | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-007) | — | — |
| `BR-LGN-008` | 会话检查与可信身份签发衔接 | Boundary / Issuance | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-008) | — | — |
| `BR-LGN-009` | 认证入口的失败与披露边界 | Failure / Privacy | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-009) | — | — |
| `BR-LGN-010` | 会话容量与 LRU 淘汰 | Capacity / Lifecycle | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-010) | — | 每账号 10 个有效会话，按 lastUsedAt 淘汰；与新会话创建原子提交。 |
| `BR-LGN-011` | 登录触发与客户端边界 | Authentication / Boundary | [UC-AUTH-007](use-cases/UC-AUTH-007-login.md#br-lgn-011) | — | 手动与自动触发使用相同服务端证明、限流和 Session 规则。 |
| `BR-LGN-012` | 本人设备凭据的授权撤销 | Credential / Revocation | [UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md#br-lgn-012) | — | 只允许有效 USER 撤销同一 authId 的凭据；不物理删除或释放公钥归属。 |
| `BR-LGN-013` | 邮箱登录定位与用途隔离 | Authentication / Identity | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-013) | — | — |
| `BR-LGN-014` | 邮箱验证码与有界投递 | Verification / Delivery | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-014) | — | — |
| `BR-LGN-015` | 邮箱授权下的设备凭据登记 | Credential / Authorization | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-015) | — | — |
| `BR-LGN-016` | 邮箱登录 Session 与邮箱更换边界 | Session / Lifecycle | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-016) | — | — |
| `BR-LGN-017` | 原子登录与结果恢复 | Atomicity / Retry | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-017) | — | — |
| `BR-LGN-018` | 邮箱登录隐私与失败关闭 | Privacy / Failure | [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md#br-lgn-018) | — | — |

## 维护规则

- UC 使用 `UC-AUTH-NNN`；业务规则按能力使用 `BR-SCP/DEV/SYS/RVW/UPF/REG/LGN/IDN/EML-NNN`。
- `UPF` 表示 User Profile，覆盖用户资料字段定义与资料编辑；不复用 App Center 的 `PRF` 编号空间。
- `REG` 表示用户创建及初始关联，`LGN` 表示登录、Session 与设备凭据撤销规则。
- `EML` 表示邮箱绑定与激活；邮箱认证用例不得复用绑定挑战。
- BR 状态继承其权威 UC，不单独保存状态。
- 新增编号时同时更新 Next ID；废弃编号不得重新分配。
- 同一规则只有一个权威正文；其它 bounded context 通过链接引用。

### Identity Issuance (`BR-IDN`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-IDN-001` | 双重认证与受限签发 | Authentication / Boundary | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-001) | — | — |
| `BR-IDN-002` | 权威能力与 audience 投影 | Authority / Projection | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002) | — | — |
| `BR-IDN-003` | 短期签名与 Session 边界 | Security / Lifetime | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-003) | — | — |
| `BR-IDN-004` | 签发与撤销的一致性 | Consistency / Revocation | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) | — | — |
| `BR-IDN-005` | 首版不缓存认证结果 | Architecture / Consistency | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-005) | — | — |
| `BR-IDN-006` | 失败关闭与秘密边界 | Failure / Privacy | [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-006) | — | — |

### Email Binding (`BR-EML`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-EML-001` | 邮箱凭据与资料、身份分离 | Boundary / Identity | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-001) | — | — |
| `BR-EML-002` | 地址规范化与唯一性 | Validation / Uniqueness | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-002) | — | — |
| `BR-EML-003` | 分支授权与验证码隔离 | Authorization / Verification | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-003) | — | — |
| `BR-EML-004` | 更换与原子激活 | Lifecycle / Atomicity | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-004) | — | — |
| `BR-EML-005` | 重试与提交结果不确定 | Retry / Consistency | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-005) | — | — |
| `BR-EML-006` | 投递、限额与秘密保护 | Delivery / Privacy | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-006) | — | — |
| `BR-EML-007` | 查询与占用披露边界 | Query / Privacy | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-007) | — | — |
| `BR-EML-008` | 恢复与 Developer 开通边界 | Boundary / Recovery | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-008) | — | — |
| `BR-EML-009` | 邮箱注册的原子创建 | Registration / Atomicity | [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-009) | — | — |
