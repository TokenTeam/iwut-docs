# Auth Center 设计标识符注册表

状态：`ACTIVE`

本文件只索引 Auth Center bounded context 的权威 UC 与 BR，不复制规则正文。跨系统契约位于 `platform/`，不登记为 Auth UC 或 BR。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Auth Center | `UC-AUTH-036` |
| Business Rule / Password Lifecycle | `BR-PWD-009` |
| Business Rule / Campus Certification | `BR-CMP-006` |
| Business Rule / Account Lifecycle | `BR-ACC-015` |
| Business Rule / Application User Storage | `BR-AUS-008` |
| Business Rule / Application Operations Permission | `BR-AOP-007` |
| Business Rule / Platform Administrator | `BR-ADM-009` |
| Business Rule / OAuth Authorization | `BR-OAU-033` |
| Business Rule / Identity Issuance | `BR-IDN-007` |
| Business Rule / Scope Catalog | `BR-SCP-006` |
| Business Rule / Developer Status | `BR-DEV-023` |
| Business Rule / System Principal | `BR-SYS-005` |
| Business Rule / Reviewer Permission | `BR-RVW-005` |
| Business Rule / User Profile | `BR-UPF-024` |
| Business Rule / User Registration | `BR-REG-009` |
| Business Rule / Login and Session | `BR-LGN-035` |
| Business Rule / Email Binding | `BR-EML-010` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `UC-AUTH-001` | 获取 Scope Catalog 快照 | `ACCEPTED` | [UC-AUTH-001-get-scope-catalog-snapshot.md](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | — | 第一个提供方纵切片；共享线格式见根级平台契约。 |
| `UC-AUTH-002` | 批量读取 Developer 状态 | `ACCEPTED` | [UC-AUTH-002-batch-get-developer-statuses.md](use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | — | 为 App Center 审核批准门禁提供 fail-closed 状态查询。 |
| `UC-AUTH-003` | 解析 System Principal | `ACCEPTED` | [UC-AUTH-003-resolve-system-principal.md](use-cases/UC-AUTH-003-resolve-system-principal.md) | — | 为跨服务系统动作提供 Auth-owned opaque actor。 |
| `UC-AUTH-004` | 管理用户的应用审核权限 | `ACCEPTED` | [UC-AUTH-004-manage-reviewer-permission.md](use-cases/UC-AUTH-004-manage-reviewer-permission.md) | — | 两项独立审核权限及 UC010 投影已实现，Auth/App/Gateway 联合验收通过；[brief](briefs/UC-AUTH-004.md)。 |
| `UC-AUTH-005` | 用户编辑自己的资料 | `ACCEPTED` | [UC-AUTH-005-edit-own-user-profile.md](use-cases/UC-AUTH-005-edit-own-user-profile.md) | — | 本人显式设置/删除、首批九字段、资料容量与单文档乐观并发；含多选片区、锚定年级和配套查询契约。 |
| `UC-AUTH-006` | 创建用户 | `ACCEPTED` | [UC-AUTH-006-create-user.md](use-cases/UC-AUTH-006-create-user.md) | — | 邮箱账号 v3 修订已 ACCEPTED/脚本 brief 后实施，注册密码/目录/初始钥与 Session 原子创建；最终回归通过。 |
| `UC-AUTH-007` | 登录并建立会话 | `ACCEPTED` | [UC-AUTH-007-login.md](use-cases/UC-AUTH-007-login.md) | — | 设备登录、会话检查、10 条有效会话上限与 LRU 淘汰。 [brief](briefs/UC-AUTH-007.md)。 |
| `UC-AUTH-008` | 撤销自己的当前 Session | `ACCEPTED` | [UC-AUTH-008-revoke-own-session.md](use-cases/UC-AUTH-008-revoke-own-session.md) | — | 由 token 定向、幂等撤销当前 Session，不改变设备凭据。 [brief](briefs/UC-AUTH-008.md)。 |
| `UC-AUTH-009` | 撤销自己的设备凭据 | `ACCEPTED` | [UC-AUTH-009-revoke-own-credential.md](use-cases/UC-AUTH-009-revoke-own-credential.md) | — | 新修订旧入口仅当前凭据退出，其他目标走 UC032 密码＋新签名；当前入口限制已实施并通过最终回归；UC032 仍 DRAFT。 |
| `UC-AUTH-010` | 由 Session 签发可信用户身份 | `ACCEPTED` | [UC-AUTH-010-issue-user-identity-from-session.md](use-cases/UC-AUTH-010-issue-user-identity-from-session.md) | — | 受授权服务以有效 Session 换取目标 audience 的短期用户 JWS；不缓存身份结果。 |
| `UC-AUTH-011` | 设置并激活邮箱 | `ACCEPTED` | [UC-AUTH-011-set-and-activate-email.md](use-cases/UC-AUTH-011-set-and-activate-email.md) | — | 邮箱列表唯一登录角色、切换密码保护、非登录绑定增删；v3 修订已 ACCEPTED/脚本 brief 后实施，旧 REGISTER/BIND 已退役；最终回归通过。 |
| `UC-AUTH-012` | 使用邮箱登录 | `ACCEPTED` | [UC-AUTH-012-login-with-email.md](use-cases/UC-AUTH-012-login-with-email.md) | — | 邮箱验证码授权本机设备，回到原账号并建立 Session；不自动注册。 |
| `UC-AUTH-013` | 申请 Developer | `ACCEPTED` | [UC-AUTH-013-apply-for-developer.md](use-cases/UC-AUTH-013-apply-for-developer.md) | — | 当前激活邮箱及可用邮箱登录为前提，自助开通 APPROVED；不增加人工资格审核。 |
| `UC-AUTH-014` | 用户确认应用授权并签发授权码 | `ACCEPTED` | [UC-AUTH-014](use-cases/UC-AUTH-014-authorize-application.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-015` | 兑换授权码并签发 OIDC 凭据 | `ACCEPTED` | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-016` | 刷新应用访问凭据 | `ACCEPTED` | [UC-AUTH-016](use-cases/UC-AUTH-016-refresh-application-tokens.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-017` | 读取 OIDC 用户信息 | `ACCEPTED` | [UC-AUTH-017](use-cases/UC-AUTH-017-get-oidc-user-info.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-018` | 查看及收回本人应用授权 | `ACCEPTED` | [UC-AUTH-018](use-cases/UC-AUTH-018-revoke-application-authorization.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-019` | 校验应用访问凭据并签发可信委托上下文 | `ACCEPTED` | [UC-AUTH-019](use-cases/UC-AUTH-019-issue-delegation-context.md) | — | OAuth/OIDC 新设计，未实现。 |
| `UC-AUTH-020` | 管理及回收同一账号的 Session | `ACCEPTED` | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md) | — | 有效会话列表与明确 Session ID 集合的原子回收；不扩展到关联组或设备凭据。 |
| `UC-AUTH-021` | 授予与撤销平台管理员资格 | `ACCEPTED` | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md) | — | 固定管理集合、最后管理员保护及一次性 bootstrap；尚未实现。 |
| `UC-AUTH-022` | 禁用与恢复用户账号 | `ACCEPTED` | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md) | — | 账号版本隔离全部旧认证材料；依赖 UC021 及认证消费路径扩展，尚未实现。 |
| `UC-AUTH-023` | 暂停与恢复 Developer 资格 | `ACCEPTED` | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md) | — | 管理侧资格状态转换、独立版本及恢复门禁；尚未实现。 |
| `UC-AUTH-024` | 本人退出 Developer 资格 | `ACCEPTED` | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md) | — | WITHDRAWN、永久 handle 占用及 App 归属屏障；尚未实现。 |
| `UC-AUTH-025` | 本人注销账号 | `ACCEPTED` | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md) | — | 2026-10-13 当前密码/凭据下界修订获接受、实施及最终回归完成；旧协调/终止/清理保留。 |
| `UC-AUTH-026` | 应用关闭授权收敛与近期认证 | `ACCEPTED` | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md) | — | 2026-10-13 app.close 当前密码门禁获接受、实施及最终回归完成；旧 tombstone/协调保留。 |
| `UC-AUTH-027` | 管理应用平台运维权限 | `ACCEPTED` | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md) | — | 独立 suspend/restore 权限；平台管理员管理但不自动获得操作权，App 暂停状态机独立交付。 |
| `UC-AUTH-028` | 向第三方应用披露用户资料字段 | `ACCEPTED` | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md) | — | 首批九字段一字段一 scope、固定 `iwut_profile` claim、多片区数组与封顶年级投影；[brief](briefs/UC-AUTH-028.md)。 |
| `UC-AUTH-029` | 管理下一次学年更新时间 | `ACCEPTED` | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md) | — | 平台管理员设置带年份的下一更新时间；缺省逐年 9 月 1 日；[brief](briefs/UC-AUTH-029.md)。 |
| `UC-AUTH-030` | 读写应用用户存储 | `ACCEPTED` | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md) | — | 用户/Application/channel 隔离的有界字符串 KV；OAuth 读写与生命周期清理语义已固定。 |
| `UC-AUTH-031` | 建立邮箱账号与校园成员认证 | `ACCEPTED` | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md) | — | 当前学校绑定为认证依据、最后依据解绑撤回；v3 修订已 ACCEPTED/脚本 brief 后实施，旧永久事实不授权；最终回归通过。 |
| `UC-AUTH-032` | 管理自己的设备登录凭据 | `ACCEPTED` | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md) | — | 列表、可选命名与同设备新签名移除其他凭据；用户 2026-10-13 授权继续完成；直接依赖已具备，脚本 brief 后实施。 |
| `UC-AUTH-033` | 管理密码与恢复账号 | `ACCEPTED` | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md) | — | Auth 后端公开改密/重置与通知已完成并验证；默认关闭，客户端与生产启用独立。 |
| `UC-AUTH-034` | 使用登录邮箱与密码登录 | `ACCEPTED` | [UC-AUTH-034](use-cases/UC-AUTH-034-login-with-password.md) | — | Auth 后端密码/设备证明登录与真实回归完成；默认关闭，客户端与生产启用独立。 |
| `UC-AUTH-035` | 在官方宿主内授权第三方应用 | `DRAFT` | [UC-AUTH-035](use-cases/UC-AUTH-035-authorize-application-in-host.md) | — | 宿主可信界面已确认；Auth 交互/code 协议待接受，RPC 与 Native 内部实现不是 Auth 开工前置。 |

## Business Rules

### Password Lifecycle (`BR-PWD`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-PWD-001` | 密码来源、策略与初始化 | Policy / Initialization | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-001) | — | ACCEPTED / IN_PROGRESS。 |
| `BR-PWD-002` | 安全存储与参数升级 | Cryptography / Storage | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-002) | — | ACCEPTED / IN_PROGRESS；Argon2id，不继承旧 SHA-256。 |
| `BR-PWD-003` | 危险动作的目标绑定验证 | Authentication / Boundary | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-003) | — | ACCEPTED / IN_PROGRESS；不授予业务权限。 |
| `BR-PWD-004` | 正常改密保留当前设备 | Lifecycle / Rotation | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-004) | — | ACCEPTED / IN_PROGRESS；新 Session 一次返回。 |
| `BR-PWD-005` | 登录邮箱恢复与全部设备清退 | Recovery / Revocation | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-005) | — | ACCEPTED / IN_PROGRESS；重置不自动登录。 |
| `BR-PWD-006` | 统一代际与不可复活的设备下界 | Versioning / Consistency | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-006) | — | ACCEPTED / IN_PROGRESS；复用 accountRevision，不新增 authenticationEpoch。 |
| `BR-PWD-007` | 原子提交、幂等与秘密恢复 | Atomicity / Retry | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-007) | — | ACCEPTED / IN_PROGRESS。 |
| `BR-PWD-008` | 限额、失败关闭与启用门禁 | Capacity / Delivery | [UC-AUTH-033](use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-008) | — | ACCEPTED / IN_PROGRESS。 |

### Account Lifecycle (`BR-ACC`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-ACC-001` | 账号边界与状态转换 | Lifecycle / Boundary | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-001) | — | — |
| `BR-ACC-002` | 账号版本与不可复活 | Versioning / Revocation | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) | — | — |
| `BR-ACC-003` | 所有认证路径的版本闭合 | Authentication / Consistency | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-003) | — | — |
| `BR-ACC-004` | 可信身份与下游生效边界 | Identity / Propagation | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-004) | — | — |
| `BR-ACC-005` | OAuth 同意、开发者及应用边界 | OAuth / Ownership | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-005) | — | — |
| `BR-ACC-006` | 事务、并发与最后管理员保护 | Atomicity / Invariant | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-006) | — | — |
| `BR-ACC-007` | 审计、查询与错误边界 | Audit / Privacy | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-007) | — | — |
| `BR-ACC-008` | 完整交付与历史数据边界 | Delivery / Compatibility | [UC-AUTH-022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-008) | — | — |
| `BR-ACC-009` | 明确终止与不可恢复 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-009) | — | — |
| `BR-ACC-010` | 用途绑定的近期设备证明 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-010) | — | — |
| `BR-ACC-011` | 归属、治理与竞争 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-011) | — | — |
| `BR-ACC-012` | 清理范围与最小永久保留 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-012) | — | — |
| `BR-ACC-013` | 清理任务与备份恢复 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-013) | — | — |
| `BR-ACC-014` | 结果、审计与第三方边界 | Lifecycle / Governance | [UC-AUTH-025](use-cases/UC-AUTH-025-close-own-account.md#br-acc-014) | — | — |

### Platform Administrator (`BR-ADM`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-ADM-001` | 固定管理权限集合 | Authority / Boundary | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001) | — | — |
| `BR-ADM-002` | 在线授权与授予前置条件 | Authorization / Recovery | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-002) | — | — |
| `BR-ADM-003` | 最后有效管理员保护 | Invariant / Concurrency | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-003) | — | — |
| `BR-ADM-004` | 共享版本、原子审计与重试 | Atomicity / Audit | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-004) | — | — |
| `BR-ADM-005` | 一次性管理员初始化 | Bootstrap / Lifecycle | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-005) | — | — |
| `BR-ADM-006` | 最小查询与错误披露 | Query / Privacy | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-006) | — | — |
| `BR-ADM-007` | 签发投影与撤销边界 | Projection / Revocation | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-007) | — | — |
| `BR-ADM-008` | 恢复与初始化的边界 | Recovery / Boundary | [UC-AUTH-021](use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-008) | — | — |

### Application Operations Permission (`BR-AOP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-AOP-001` | 精确运维权限与职责分离 | Authorization / Separation | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-001) | — | — |
| `BR-AOP-002` | 平台管理员负责授权但不自动获得操作权 | Authority / Boundary | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-002) | — | — |
| `BR-AOP-003` | 共享权限版本与原子审计 | Consistency / Audit | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-003) | — | — |
| `BR-AOP-004` | Audience 最小投影与撤销窗口 | Projection / Revocation | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-004) | — | — |
| `BR-AOP-005` | 账号状态、恢复能力与授权事实 | Lifecycle / Recovery | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005) | — | — |
| `BR-AOP-006` | Auth 授权与 App 业务状态分离 | Boundary / Ownership | [UC-AUTH-027](use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-006) | — | — |

### Application User Storage (`BR-AUS`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-AUS-001` | 应用、用户与 channel 三重隔离 | Boundary / Isolation | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-001) | — | — |
| `BR-AUS-002` | 当前 OAuth 授权是每次访问的必要条件 | Authorization / Consistency | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-002) | — | — |
| `BR-AUS-003` | 有界字符串 KV 与精确容量 | Validation / Quota | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-003) | — | 首版固定配额。 |
| `BR-AUS-004` | 整命名空间 revision 与原子批量变更 | Concurrency / Atomicity | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-004) | — | — |
| `BR-AUS-005` | 撤权立即阻断访问，数据删除单独表达 | Lifecycle / Privacy | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-005) | — | 撤权保留，明确清除/关闭才删除。 |
| `BR-AUS-006` | 账号关闭与 Application 关闭的清理闭合 | Lifecycle / Cleanup | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-006) | — | — |
| `BR-AUS-007` | 不透明数据、最小观测与失败关闭 | Privacy / Failure | [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-007) | — | 普通 mutation 不单独审计。 |

### Campus Certification (`BR-CMP`)

以下规则属于已 ACCEPTED 的 UC031 v3 修订；旧永久独立事实仅为历史基线，现行认证由当前绑定及解绑语义决定。

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-CMP-001` | 邮箱账号与学校信息脱离 | Registration / Boundary | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-001) | — | v3 修订 ACCEPTED。 |
| `BR-CMP-002` | 服务端邮件验证与当前绑定依据 | Verification / Lifecycle | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-002) | — | DRAFT；不再无条件永久保存。 |
| `BR-CMP-003` | 账号认证与应用一次性领取分离 | Boundary / Entitlement | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-003) | — | DRAFT；重新绑定不重置应用领取。 |
| `BR-CMP-004` | 披露授权与权益职责 | Disclosure / Ownership | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-004) | — | DRAFT；当前依据撤回后停止披露。 |
| `BR-CMP-005` | 并发、审计与注销清理 | Atomicity / Privacy | [UC-AUTH-031](use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-005) | — | DRAFT；邮箱绑定、投影与恢复一致性。 |

### Scope Catalog (`BR-SCP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SCP-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001) | — | — |
| `BR-SCP-002` | 完整一致快照 | Snapshot / Consistency | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-002) | — | — |
| `BR-SCP-003` | 单调 revision 与生成时间 | Versioning / Audit | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003) | — | — |
| `BR-SCP-004` | ScopeDefinition 投影 | Field / Projection | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) | — | enabled 单状态；requestable 兼容投影。 |
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
| `BR-DEV-013` | 独立资格与单调版本 | Lifecycle / Governance | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-013) | — | — |
| `BR-DEV-014` | 保留普通功能与传播边界 | Lifecycle / Governance | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-014) | — | — |
| `BR-DEV-015` | 暂停优先与退出竞争 | Lifecycle / Governance | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-015) | — | — |
| `BR-DEV-016` | OAuth 恢复及 handle 连续性 | Lifecycle / Governance | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-016) | — | — |
| `BR-DEV-017` | 审计与并发一致性 | Lifecycle / Governance | [UC-AUTH-023](use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-017) | — | — |
| `BR-DEV-018` | 明确本人退出与稳定身份 | Lifecycle / Governance | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-018) | — | — |
| `BR-DEV-019` | 先处置应用再退出 | Lifecycle / Governance | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-019) | — | — |
| `BR-DEV-020` | 可取消准备与不可逆提交 | Lifecycle / Governance | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-020) | — | — |
| `BR-DEV-021` | 状态消费与历史审核 | Lifecycle / Governance | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-021) | — | — |
| `BR-DEV-022` | 原子性、查询与审计 | Lifecycle / Governance | [UC-AUTH-024](use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-022) | — | — |

### System Principal (`BR-SYS`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SYS-001` | Auth 所有权与不可登录 | Boundary / Authority | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-001) | — | — |
| `BR-SYS-002` | 按 purpose 唯一且稳定 | Identity / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-002) | — | — |
| `BR-SYS-003` | 最小授权解析 | Authorization / Boundary | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-003) | — | — |
| `BR-SYS-004` | 消费方失败关闭 | Failure / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-004) | — | — |

### Application Review Permissions (`BR-RVW`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-RVW-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-001) | — | — |
| `BR-RVW-002` | 管理权与审核权限隔离 | Authorization / Separation | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-002) | — | — |
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
| `BR-UPF-012` | 一字段一 Scope 的稳定映射 | Catalog / Compatibility | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-012) | — | — |
| `BR-UPF-013` | 审核、同意与当前有效集合共同授权 | Authorization / Consent | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-013) | — | — |
| `BR-UPF-014` | 固定 claim 与最小当前值投影 | Projection / Privacy | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-014) | — | — |
| `BR-UPF-015` | 在线当前读取与生命周期传播 | Consistency / Lifecycle | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-015) | — | — |
| `BR-UPF-016` | 损坏、依赖故障与隐私边界 | Failure / Privacy | [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-016) | — | — |
| `BR-UPF-017` | 首批生产字段目录 | Field / Catalog | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017) | — | 九个可选用户资料字段。 |
| `BR-UPF-018` | 当前就读年级的锚定与阶段内推进 | Lifecycle / Derivation | [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018) | — | 用户确认锚点；阶段内递增、最后学年封顶，不自动跨阶段。 |
| `BR-UPF-019` | 权威时间表与九月一日缺省 | Configuration / Derivation | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-019) | — | 缺省每年 9 月 1 日；读取输出下一次时间。 |
| `BR-UPF-020` | 完整平台管理员在线授权 | Authorization / Boundary | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-020) | — | 不扩充管理员固定权限 bundle。 |
| `BR-UPF-021` | 未来锚点与逐年推进 | Lifecycle / Derivation | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-021) | — | 输入带年份；2 月 29 日下一次为 3 月 1 日。 |
| `BR-UPF-022` | 乐观并发与不可变审计 | Concurrency / Audit | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-022) | — | 单一 revision、事务内设置与审计。 |
| `BR-UPF-023` | 消费一致性与文件配置退役 | Consistency / Migration | [UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-023) | — | 接受后忽略 AUTH_ACADEMIC_CALENDAR_FILE，不因残留拒绝启动。 |

### User Registration (`BR-REG`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-REG-001` | 显式创建与平台账号独立 | Boundary / Identity | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-001) | — | — |
| `BR-REG-002` | 正式主体与最小初始化 | Lifecycle / Provision | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-002) | — | — |
| `BR-REG-003` | 设备凭据持有证明与唯一归属 | Authentication / Ownership | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-003) | — | — |
| `BR-REG-004` | 停止学号关联上传 | Privacy / Retirement | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-004) | — | — |
| `BR-REG-005` | 账号身份与应用权益边界 | Identity / Boundary | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-005) | — | — |
| `BR-REG-006` | 原子创建与结果不确定的恢复 | Atomicity / Retry | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-006) | — | — |
| `BR-REG-007` | 注册入口的限额与秘密最小暴露 | Capacity / Privacy | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-007) | — | — |
| `BR-REG-008` | 关联配置与离线迁移退役 | Retirement / Migration | [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md#br-reg-008) | — | 关联 ENV/写入/启动迁移不再是依赖，不设计未部署系统的生产历史迁移。 |

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
| `BR-LGN-019` | 同账号授权边界 | Authorization / Ownership | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-019) | — | — |
| `BR-LGN-020` | 有效会话列表与只读语义 | Query / Lifecycle | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-020) | — | — |
| `BR-LGN-021` | 明确目标集合的幂等回收 | Revocation / Idempotency | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-021) | — | — |
| `BR-LGN-022` | 回收与登录检查的原子顺序 | Atomicity / Concurrency | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-022) | — | — |
| `BR-LGN-023` | 会话回收与设备、OAuth 生命周期隔离 | Boundary / Lifecycle | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-023) | — | — |
| `BR-LGN-024` | 有界处理、审计与错误 | Failure / Audit | [UC-AUTH-020](use-cases/UC-AUTH-020-manage-own-sessions.md#br-lgn-024) | — | — |
| `BR-LGN-025` | 凭据管理与本人边界 | Boundary / Ownership | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-025) | — | ACCEPTED；不宣称物理设备可信身份。 |
| `BR-LGN-026` | 仍可登录凭据的有界列表 | Query / Pagination | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-026) | — | ACCEPTED；没有 Session 也可列出，不 touch LRU。 |
| `BR-LGN-027` | 名称校验与独立乐观并发 | Metadata / Concurrency | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-027) | — | ACCEPTED。 |
| `BR-LGN-028` | 目标绑定的新设备证明与无旁路要求 | Authentication / Revocation | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-028) | — | ACCEPTED；UC009 已收紧，当前密码＋原 Session 同设备签名单目标撤销。 |
| `BR-LGN-029` | 证明与撤销的原子提交及重试 | Atomicity / Idempotency | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-029) | — | ACCEPTED；不签发可复用 proof token。 |
| `BR-LGN-030` | 有界请求、审计与生命周期清理 | Capacity / Privacy | [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md#br-lgn-030) | — | ACCEPTED；名称、挑战与审计纳入注销清单。 |
| `BR-LGN-031` | 唯一登录邮箱与默认密码入口 | Authentication / Role | [UC-AUTH-034](use-cases/UC-AUTH-034-login-with-password.md#br-lgn-031) | — | ACCEPTED / IN_PROGRESS。 |
| `BR-LGN-032` | 独立挑战与密码验证 | Authentication / Proof | [UC-AUTH-034](use-cases/UC-AUTH-034-login-with-password.md#br-lgn-032) | — | ACCEPTED / IN_PROGRESS；不算新设备第二因子。 |
| `BR-LGN-033` | 原子登录与不可复活 | Atomicity / Session | [UC-AUTH-034](use-cases/UC-AUTH-034-login-with-password.md#br-lgn-033) | — | ACCEPTED / IN_PROGRESS。 |
| `BR-LGN-034` | 失败、隐私与交付 | Failure / Delivery | [UC-AUTH-034](use-cases/UC-AUTH-034-login-with-password.md#br-lgn-034) | — | ACCEPTED / IN_PROGRESS。 |

## 维护规则

- UC 使用 `UC-AUTH-NNN`；业务规则按能力使用 `BR-SCP/DEV/SYS/RVW/UPF/REG/LGN/IDN/EML/OAU/ADM/ACC/AOP/PWD-NNN`。
- `PWD` 表示平台密码策略/验证、修改/恢复及密码安全变更的凭据收敛；邮箱角色仍由 `EML` 拥有。
- `UPF` 表示 User Profile，覆盖用户资料字段定义与资料编辑；不复用 App Center 的 `PRF` 编号空间。
- `REG` 表示用户创建及初始关联，`LGN` 表示登录、Session 与设备凭据撤销规则。
- `EML` 表示邮箱绑定与激活；邮箱认证用例不得复用绑定挑战。
- `ADM` 表示平台管理员资格、初始化及治理连续性约束。
- `ACC` 表示账号生命周期与账号级认证材料失效。
- `AOP` 表示由 Auth 管理并投影给 App Center 的平台级 Application 运维权限。
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

### OAuth Authorization (`BR-OAU`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-OAU-001` | 授权来源与运行资格 | Authorization / Boundary | [UC-AUTH-014](use-cases/UC-AUTH-014-authorize-application.md#br-oau-001) | — | — |
| `BR-OAU-002` | 显式同意与最小授权 | Authorization / Boundary | [UC-AUTH-014](use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) | — | — |
| `BR-OAU-003` | 交互和授权码原子性 | Authorization / Boundary | [UC-AUTH-014](use-cases/UC-AUTH-014-authorize-application.md#br-oau-003) | — | — |
| `BR-OAU-004` | 门户与撤销语义隔离 | Authorization / Boundary | [UC-AUTH-014](use-cases/UC-AUTH-014-authorize-application.md#br-oau-004) | — | — |
| `BR-OAU-005` | 客户端认证与证明不可降级 | Authorization / Boundary | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-005) | — | — |
| `BR-OAU-006` | 授权码一次性兑换与重放处置 | Authorization / Boundary | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-006) | — | — |
| `BR-OAU-007` | 独立凭据与有界权限 | Authorization / Boundary | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-007) | — | — |
| `BR-OAU-008` | 签发一致性与故障关闭 | Authorization / Boundary | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-008) | — | — |
| `BR-OAU-009` | 离线访问须单独同意 | Authorization / Boundary | [UC-AUTH-016](use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-009) | — | — |
| `BR-OAU-010` | 旋转重放与并发边界 | Authorization / Boundary | [UC-AUTH-016](use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-010) | — | — |
| `BR-OAU-011` | 刷新不得扩权或复活 | Authorization / Boundary | [UC-AUTH-016](use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-011) | — | — |
| `BR-OAU-012` | UserInfo 在线授权与 subject 一致性 | Authorization / Boundary | [UC-AUTH-017](use-cases/UC-AUTH-017-get-oidc-user-info.md#br-oau-012) | — | — |
| `BR-OAU-013` | 最小资料披露 | Authorization / Boundary | [UC-AUTH-017](use-cases/UC-AUTH-017-get-oidc-user-info.md#br-oau-013) | — | — |
| `BR-OAU-014` | 资料读取的撤销与故障语义 | Authorization / Boundary | [UC-AUTH-017](use-cases/UC-AUTH-017-get-oidc-user-info.md#br-oau-014) | — | — |
| `BR-OAU-015` | 本人查询和范围撤销 | Authorization / Boundary | [UC-AUTH-018](use-cases/UC-AUTH-018-revoke-application-authorization.md#br-oau-015) | — | — |
| `BR-OAU-016` | 撤销版本和重授隔离 | Authorization / Boundary | [UC-AUTH-018](use-cases/UC-AUTH-018-revoke-application-authorization.md#br-oau-016) | — | — |
| `BR-OAU-017` | 应用 token 撤销与平台登录分离 | Authorization / Boundary | [UC-AUTH-018](use-cases/UC-AUTH-018-revoke-application-authorization.md#br-oau-017) | — | — |
| `BR-OAU-018` | 服务调用者和用户授权双重门禁 | Authorization / Boundary | [UC-AUTH-019](use-cases/UC-AUTH-019-issue-delegation-context.md#br-oau-018) | — | — |
| `BR-OAU-019` | 路由许可与委托身份隔离 | Authorization / Boundary | [UC-AUTH-019](use-cases/UC-AUTH-019-issue-delegation-context.md#br-oau-019) | — | — |
| `BR-OAU-020` | 签发撤销一致性与在线依赖 | Authorization / Boundary | [UC-AUTH-019](use-cases/UC-AUTH-019-issue-delegation-context.md#br-oau-020) | — | — |
| `BR-OAU-021` | Application 级 sector 与主体映射 | Identity / Privacy | [UC-AUTH-015](use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021) | — | Auth 唯一拥有 sector/sub。 |
| `BR-OAU-022` | 永久 Application 授权墓碑 | Lifecycle / Revocation | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-022) | — | — |
| `BR-OAU-023` | 全部 OAuth 路径的最终闭合 | Authorization / Consistency | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-023) | — | — |
| `BR-OAU-024` | 服务身份、幂等回执与未知结果 | Identity / Retry | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-024) | — | — |
| `BR-OAU-025` | 同设备新挑战证明近期认证 | Authentication / Proof | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-025) | — | — |
| `BR-OAU-026` | Proof 最小权力与固定时限 | Authorization / Time | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-026) | — | — |
| `BR-OAU-027` | Proof 幂等与单次业务消费 | Retry / Replay | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-027) | — | — |
| `BR-OAU-028` | 并发、故障关闭与审计边界 | Atomicity / Audit | [UC-AUTH-026](use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-028) | — | — |
| `BR-OAU-029` | 宿主调用上下文与应用归属 | Host / Boundary | [UC-AUTH-035](use-cases/UC-AUTH-035-authorize-application-in-host.md#br-oau-029) | — | DRAFT；未冻结协议。 |
| `BR-OAU-030` | 官方用户决定与秘密隔离 | Host / Consent | [UC-AUTH-035](use-cases/UC-AUTH-035-authorize-application-in-host.md#br-oau-030) | — | 宿主可信界面方向已确认；整体 DRAFT，确认协议待闭合。 |
| `BR-OAU-031` | 发起事务与授权结果绑定 | Host / Delivery | [UC-AUTH-035](use-cases/UC-AUTH-035-authorize-application-in-host.md#br-oau-031) | — | DRAFT；PUBLIC/CONFIDENTIAL 交付未冻结。 |
| `BR-OAU-032` | 失效、取消与结果不确定 | Host / Recovery | [UC-AUTH-035](use-cases/UC-AUTH-035-authorize-application-in-host.md#br-oau-032) | — | DRAFT；取消与提交竞争待协议闭合。 |
