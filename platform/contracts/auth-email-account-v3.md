# 邮箱账号、密码注册与登录角色协议 v3 草案

状态：`ACCEPTED / EMAIL_CORE_COMPLETE`

## 范围与审核边界

UC006/011 拥有注册及邮箱集合规则，UC031 拥有当前校园依据，UC033 拥有密码策略/安全验证。本契约补齐原草案未固定的接口、集合版本及注册字节，2026-10-13 新增并经用户明确审核接受，授权 UC006/011/031 修订生成 brief 后实现；公开启用仍须完整验收。

用户已明确确认：最多 10 个已验证地址、所有地址跨账号全局唯一；切换唯一登录邮箱不清退现有设备/Session，但旧邮箱登录/恢复操作失效。本文不重新讨论这些规则。没有旧账号生产迁移；现有开发数据库不自动删除、补密码或补版本。

## 精确入口与载体

新 package `auth_center.v3.email_account`，service `EmailAccountService`。每个 exact full method 单独登记，不用匿名 wildcard。

| RPC | service-local HTTP | 身份 |
| --- | --- | --- |
| BeginEmailRegistration | POST `/v3/email-registrations` | Session 键不存在 |
| CompleteEmailRegistration | POST `/v3/email-registrations:complete` | Session 键不存在 |
| GetOwnEmails | GET `/v3/users/me/emails` | 当前有效 Session、no-touch |
| BeginAddOwnEmail | POST `/v3/users/me/email-verifications` | 当前有效 Session、no-touch |
| CompleteAddOwnEmail | POST `/v3/users/me/email-verifications:complete` | 同 authId 当前有效 Session、no-touch |
| SwitchOwnLoginEmail | POST `/v3/users/me/login-email:switch` | 当前有效 Session＋当前密码、no-touch |
| RemoveOwnEmail | POST `/v3/users/me/emails:remove` | 当前有效 Session、no-touch |

复用唯一 `x-iwut-session` 载体；无效/空 token 不匿名降级。所有正文严格 ProtoJSON、lowerCamelCase、bytes 标准 Base64、int64 JSON string，16 KiB、无 query/重复/未知/null 字段、no-store。用户名、owner、校园属性、版本和提交时间不能由客户端指定。密码只在 TLS Complete/Switch 正文出现，不进挑战/签名/日志。

## 消息字段提案

字段号从 1 起，不复用旧 REGISTER/BIND 消息；所有非 optional 请求字段必需且非空。注册 proof/proposal presence 必需；密码生命周期规则不在本契约另定义。

| 消息 | 字段号/类型 |
| --- | --- |
| BeginEmailRegistrationRequest | 1 string request_id；2 string email；3 v1.authentication.CredentialRegistrationProposal credential_proposal |
| EmailRegistrationStarted | 1 string operation_id；2 string target_email；3 bytes challenge；4 bytes signing_payload；5 string protocol_version；6 int64 expires_at_unix_ms；7 int64 resend_after_unix_ms |
| CompleteEmailRegistrationRequest | 1 string operation_id；2 string code；3 string password；4 v1.authentication.CredentialProof proof |
| EmailRegistrationCompleted | 1 string operation_id；2 v1.authentication.UserRegistrationResult registration_result |
| GetOwnEmailsRequest | 空 |
| OwnEmail | 1 string binding_id；2 string email；3 int64 verified_at_unix_ms；4 bool is_login；5 bool is_whut |
| OwnEmails | 1 int64 directory_revision；2 int64 login_role_revision；3 repeated OwnEmail emails；4 repeated PendingOwnEmail pending |
| PendingOwnEmail | 1 string operation_id；2 string target_email；3 int64 expires_at_unix_ms；4 int64 resend_after_unix_ms |
| BeginAddOwnEmailRequest | 1 string request_id；2 string email；3 int64 expected_directory_revision |
| OwnEmailVerificationStarted | 1 string operation_id；2 string target_email；3 int64 expires_at_unix_ms；4 int64 resend_after_unix_ms |
| CompleteAddOwnEmailRequest | 1 string operation_id；2 string code |
| OwnEmailAdded | 1 string operation_id；2 OwnEmails emails |
| SwitchOwnLoginEmailRequest | 1 string request_id；2 string target_binding_id；3 string current_password；4 int64 expected_directory_revision；5 int64 expected_login_role_revision |
| LoginEmailSwitched | 1 string operation_id；2 OwnEmails emails |
| RemoveOwnEmailRequest | 1 string request_id；2 string binding_id；3 int64 expected_directory_revision |
| OwnEmailRemoved | 1 string operation_id；2 OwnEmails emails |

所有 ID 为小写 UUIDv4，authId 不放入上述本人输入。OwnEmails 必须恰好一个 isLogin；isWhut 精确域规则引用 UC031。emails 最多 10 个，按 `(verifiedAt,bindingId)` 升序；pending 最多 3 个，均为本人仍可完成 ADD 操作，不含匿名注册。不存在目录或角色不一致为依赖损坏，不伪装为空账号。

## 注册签名字节

设备 proposal 仍 `iwut-device-v1`，注册操作版本 `iwut-email-registration-v3`，用途 `REGISTER_WITH_PASSWORD_EMAIL`。仅该版本可以调用新的密码注册完成路径。基础 Frame/U64BE/UUID/P-256/严格 DER 引用设备 v1；恰好十字段：

```text
Frame(
  UTF8("iwut-email-registration-proof-v3"),
  UTF8("iwut-email-registration-v3"), UTF8("REGISTER_WITH_PASSWORD_EMAIL"),
  UTF8(serviceId), UTF8("iwut-client"), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65, UTF8(normalizedEmail))
```

challenge 32 随机字节、10 分钟、payload 最多 1024 字节；新密码不进入 Frame。Begin 不建 USER、不设置密码、不占邮箱归属；Complete 校验码、签名、新密码策略，在有界 Argon 执行器准备材料后，同一认证事务创建全部事实。密码策略失败不消费码；昂贵计算前扣共享额度，事务重试不重复 hash。

注册初始 principal.accountRevision/minimumCredentialRevision、独立密码记录的 passwordRevision、目录 revision、登录角色 revision、凭据 credentialRevision 均为 1。密码记录独立存储；初始设备 Session 的 DEVICE_CREDENTIAL 方法不伪称本次密码登录或现有 Session 重认证。操作完成后不再次返回秘密；丢失响应保留同一密钥→UC007 恢复。

## 邮箱目录与独立版本

新目录 `auth_email_directories` 每 authId 唯一：`revision`、`loginRoleRevision`、`loginBindingId`、`verifiedCount` 均在服务端管理；revision/role 为正 int64，verifiedCount 为 1..10。

`auth_email_bindings` 每 bindingId 一条：authId、规范 email、verifiedAt；bindingId 与规范 email 各全局唯一，authId 不是唯一键。一次查询最多读 11 个绑定并验证 count/角色/owner 一致；第 11 个或多个/缺失登录角色失败关闭。删除后的 bindingId 不复用；重新验证原地址得到新 ID。

新增/解绑推进 directoryRevision，不改变 loginRoleRevision。切换登录角色推进两者；同目标为验证密码后的幂等 no-op，不增加版本。登录提案和密码恢复绑定 loginRoleRevision，不因添加/移除无关非登录地址而失效；角色 A→B→A 后原提案仍不能使用。目录版本溢出拒绝变更，不重置版本。

添加 Begin 固定 owner、accountRevision、目标和 expectedDirectoryRevision；首次/重复提交均需同 owner 当前有效 Session。Complete 最终比较快照、目录 CAS 和地址全局归属，成功只添加非登录绑定；并发目录变更为冲突，不自动改角色或复用旧验证另做动作。切换新地址先 ADD 验证，再 SWITCH，不能把新邮箱码当作原账号密码。

Remove 最终确认目标不是登录绑定；始终保留当前登录地址。解绑最后学校依据时客户端提前提示失去认证，但不额外要求密码；服务端不信任客户端校园标志。切换登录邮箱不修改账号代际、设备或 Session，不隐式删旧地址；Auth 消费方读取新主角色，旧邮箱码/恢复的角色版本复核失败。

## 用途、HMAC 与重试

继续使用独立 `AUTH_EMAIL_BINDING_HMAC_KEY`，不与密码操作 key 混用。验证码 8 ASCII 数字、10 分钟/5 次错误/60 秒冷却；REGISTER/ADD/LOGIN/RESET 的发送共享既有账号、地址、来源额度，不按 v3 扩大预算。

```text
registerRequestMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-request-v3"), UTF8("REGISTER_WITH_PASSWORD_EMAIL"),
  UTF8(requestId), UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8("iwut-device-v1"), publicKey65))
addRequestMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-request-v3"), UTF8("ADD_VERIFIED_EMAIL"),
  UTF8(requestId), UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8(authId), U64BE(accountRevision), U64BE(expectedDirectoryRevision)))
codeMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-code-v3"), UTF8(purpose), UTF8(operationId),
  U64BE(expiresAtUnixMs), requestMac, UTF8(code8)))
```

keyId 继续使用邮箱 v1 域；新 request/code 域防止旧码复用。Begin 幂等 24 小时，键分别为 `(purpose,publicKeyFingerprint,requestId)`、`(purpose,authId,requestId)`，不受 keyId 冷换影响；同键异参冲突、不重发/延期。完成操作不重新给 token 或重新创建绑定。

每 owner 最多 3 个有效 ADD，同 owner/目标的新成功 Begin 只替代该地址原提案，不替代其它地址；容量和共享发信额度检查后才替代。同公钥 REGISTER 最多 1 个，沿用全局 10000 PENDING、1000000 保留记录的拒绝式容量边界，不能驱逐活跃/幂等记录。换 key 废止旧未完成操作，不释放幂等键，不影响已验证绑定。

Switch/Remove 幂等 24 小时，按 `(authId,purpose,requestId)` 固定目标/期望版本。Switch 的指纹由密码 operation key 以新专用域 HMAC 绑定参数和规范当前密码；不存明文密码，不签发通用解锁 token。完成重放只能恢复无秘密当前状态，不重复变更；后续目录已变化不能把历史结果冒充当前快照。

## 校园依据与旧入口退役

校园 true 只从当前 verified WHUT 绑定集合导出，不另写永久 true 记录。OwnCampusCertification 的 certifiedAt 定义为**当前有效 WHUT 依据中最早 verifiedAt**；删除最早依据可能改变此时间，删除最后依据为 false 且无时间，重新绑定产生新验证时间。它不是首次领取/自然人身份，不得用其重置权益活动。

独立旧校园 Begin/Complete 作为受同一目录/容量/额度约束的 ADD 验证别名，使用新 ADD 用途；不再写旧永久集合，不因已经认证拒绝添加第二个学校地址。Get 与 UserInfo 在同一当前授权事务读取目录/绑定；最后依据移除提交后即不披露认证。坏目录整次拒绝。

旧 v1 EmailBindingService 的 BeginSetEmail/CompleteSetEmail（无密码 REGISTER、隐式更换主邮箱 BIND）退役，不允许通过开关恢复；旧只读 Get 可投影当前主邮箱及 loginRoleRevision，不提供旧 pending。历史 v2 向量保留，不改其字节或作为 v3 输入。Campus 旧永久文档不作为认证依据，无自动迁移。

## 错误、依赖与启用

沿用邮箱规范错误，并增加 EMAIL_DIRECTORY_CONFLICT（409）、EMAIL_LOGIN_ROLE_CONFLICT（409）、EMAIL_BINDING_LIMIT_REACHED（409）、LOGIN_EMAIL_REMOVAL_FORBIDDEN（409）、EMAIL_BINDING_NOT_FOUND（404）。密码错误/成本额度/依赖按 UC033，不披露另一账号 owner。匿名注册的地址冲突只在证明该地址和新私钥控制后给出受控冲突，不提供存在性预查询。

硬依赖：本契约审核与公开 v3 正反向量、独立 API、密码初始化、目录角色读取和 UC012/013/017/033/034 的角色版本复核、共享邮件/昂贵额度、校园目录投影、UC025 清理/终止清单及旧入口防旁路。首版配置启用必须覆盖完整链路；不能先开密码 API 而保留旧无密码创建/换主入口。

2026-10-13 用户明确接受并授权实现；同步 UC006/011/031 ACCEPTED、脚本生成 brief 后开工。实现覆盖和启用门禁独立记录，不以接受代替验收。

## 实施证据与公开向量（2026-10-13）

[v3 公开向量](test-vectors/auth-email-account-v3.json)由 `tools/auth_email_account_v3_vectors.py --write/--check` 生成和验证。Go 对照十字段 Frame、恰好一次 SHA-256、严格 DER/high-S/low-S、域/用途/字段篡改及 register/add/code/switch/remove MAC。固定密钥、密码、nonce、地址均为公开测试，不得作为运行配置。旧设备/邮箱 v1/v2 文件保持不变。

私有变更 HMAC 的实现编码为 `Frame("iwut-email-mutation-request-v3",purpose,authId,requestId,bindingId,U64BE(expectedDirectoryRevision),U64BE(expectedLoginRoleRevision),U64BE(passwordRevision),U64BE(accountRevision)[,normalizedCurrentPassword])`：Switch 使用密码 operation key/其 keyId；Remove 使用邮箱 key/其 keyId，role/password revision 为零，不带密码。只保存 MAC，不保存含密码的 Frame。该编码不新增公开登录证明或通用解锁凭证。

当前公开 v3 核心/Wire 已实施且专项通过，尚不表示 UC033/034 普通密码登录/重置/通知或危险动作依赖交付。当前验证和完整启用门禁见 [实现入口](../../auth-center/implements/README.md)。
