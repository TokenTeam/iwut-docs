# 平台密码与密码登录协议 v1 草案

状态：`ACCEPTED / IMPLEMENTATION_PENDING`

## 权威与兼容边界

业务规则唯一见 [UC033 密码管理/恢复](../../auth-center/use-cases/UC-AUTH-033-manage-password-and-recovery.md)、[UC034 密码登录](../../auth-center/use-cases/UC-AUTH-034-login-with-password.md)，邮箱角色见 UC011、密码注册见 UC006。本文只固定客户端/Auth/Gateway 的消息与安全载体提案，不是可执行 Proto，也未提供已验收的公开向量。

2026-10-13 用户授权开始实现，本文字段号、编码和默认参数随 UC033/034 接受。既有设备 LOGIN、邮箱码 LOGIN_WITH_EMAIL 和无密码邮箱注册 v2 字节不被改写；新密码字段/入口必须显式版本化，不通过向旧消息追加秘密、复用退役字段或自动降级实现。公开向量、可执行 API 和启用验证独立跟踪，接受不表示交付完成。

## 秘密输入与载体

- 仅 TLS 传密码，密码为用户输入的 UTF-8 string；规范化/策略/存储唯一见 BR-PWD-001/002。不由客户端 SHA-256 后把摘要当认证密码，密码不进入 Frame/signingPayload、URL、日志、审计、错误或邮件。
- JSON 固定 lowerCamelCase、bytes 为标准 ProtoJSON Base64、时间为 int64 UTC Unix 毫秒（JSON string）、requestId/operationId 为小写 UUIDv4。body 最大 16 KiB，严格拒绝未知/重复/null/错误分支/query，响应 no-store。
- Session 唯一载体仍 `x-iwut-session`；不接受 Authorization/Cookie/JWS/OAuth token 替代。要求匿名的入口 Session 键必须不存在，已提供空/失效 token 不允许删除后重试匿名。
- Gateway DIRECT 只转发精确方法，不验证密码/owner、不签发“已验证密码”身份头；未知方法默认拒绝，正文与秘密不进入代理日志。

## 方法与逻辑消息

package `auth_center.v1.password_management` / `PasswordManagementService`：

| 方法 | 内部 HTTP 提案 | 载体/成功 |
| --- | --- | --- |
| ChangeOwnPassword | POST `/v1/users/me/password:change` | 有效 Session；PasswordChanged，含一次性新 Session |
| GetOwnPasswordChange | POST `/v1/users/me/password-changes:get` | 有效 Session；本人 requestId 的无秘密状态 |
| BeginPasswordReset | POST `/v1/password-resets` | 明确匿名；PasswordResetStarted |
| CompletePasswordReset | POST `/v1/password-resets:complete` | 明确匿名；PasswordResetCompleted，无 Session |

package `auth_center.v1.password_login` / `PasswordLoginService`：

| 方法 | 内部 HTTP 提案 | 载体/成功 |
| --- | --- | --- |
| BeginPasswordLogin | POST `/v1/password-logins` | 明确匿名；PasswordLoginStarted |
| CompletePasswordLogin | POST `/v1/password-logins:complete` | 明确匿名；PasswordLoginResult，一次性 Session |

完整 RPC 为 `/<package>.<service>/<method>`，六个 exact 方法分别登记，原生 gRPC/HTTP 同语义。以下字段号已接受，独立 API 按本契约实施；表中路径不是现有生产清单。

| 消息 | 字段号/类型 |
| --- | --- |
| ChangeOwnPasswordRequest | 1 string request_id；2 string current_password；3 string new_password |
| PasswordChanged | 1 string operation_id；2 Auth.SessionEstablished session |
| GetOwnPasswordChangeRequest | 1 string request_id |
| OwnPasswordChange | 1 PasswordChangeStatus status；2 optional string operation_id；3 int64 observed_at_unix_ms |
| BeginPasswordResetRequest | 1 string request_id；2 string login_email |
| PasswordResetStarted | 1 string operation_id；2 int64 expires_at_unix_ms；3 int64 resend_after_unix_ms |
| CompletePasswordResetRequest | 1 string operation_id；2 string code；3 string new_password |
| PasswordResetCompleted | 1 string operation_id |
| BeginPasswordLoginRequest | 1 string request_id；2 string login_email；3 Auth.CredentialRegistrationProposal credential_proposal |
| PasswordLoginStarted | 1 string operation_id；2 bytes challenge；3 bytes signing_payload；4 string protocol_version；5 int64 expires_at_unix_ms |
| CompletePasswordLoginRequest | 1 string operation_id；2 string password；3 Auth.CredentialProof proof |
| PasswordLoginResult | 1 string auth_id；2 string credential_id；3 Auth.SessionEstablished session |

PasswordChangeStatus：UNSPECIFIED=0（不允许成功）、NOT_FOUND=1、COMPLETED=2；NOT_FOUND 没有 operationId，COMPLETED 必须有。所有 string 请求字段非空且必需，proof/proposal/session presence 必需，当前旧 Session 无效不得返回完成秘密。密码校验输入不套用新设置的 blocklist/最短门限，验证已有 hash；所有路径按其规范化版本处理且有原始长度上限，新设置必须满足 UC033 策略。

注册还需单独受版本保护的“邮箱验证＋密码设置＋设备证明”完成请求（UC011），不能让旧无密码 REGISTER 绕过新模型。添加非登录邮箱与切换登录角色须区分：Session＋新邮箱码不足以切换。危险动作采用所属 UC 的 Complete 带当前密码，在 Auth 最终提交边界复核；不签发通用解锁 token。

2026-10-13 六个消息/RPC 已进入独立 API Proto 并生成 Go/gRPC/HTTP 客户端；Auth 公开服务仍未注册。新注册/邮箱目录方案见[已接受的邮箱账号 v3 契约](auth-email-account-v3.md)，已实施邮箱核心，但不属于已交付的普通密码登录/重置 API。

## 密码登录签名字节

设备提案仍 `protocolVersion="iwut-device-v1"`；挑战版本为 `iwut-password-login-v1`，purpose=`LOGIN_WITH_PASSWORD`。基础 UTF8/Frame/U64BE、UUID 文本、P-256/SHA-256、公钥和严格 DER/high-S/low-S 引用[设备契约](auth-device-session-v1.md)。恰好 10 字段：

```text
Frame(
  UTF8("iwut-password-login-proof-v1"),
  UTF8("iwut-password-login-v1"), UTF8("LOGIN_WITH_PASSWORD"),
  UTF8(serviceId), UTF8("iwut-client"), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65, UTF8(normalizedLoginEmail)
)
```

challenge32 CSPRNG、5 分钟，payload 最多 1024 字节；operationId/邮箱/公钥/期限均来自 Begin 不可变上下文。客户端按自己发起输入及预配 `AUTH_AUTHENTICATION_SERVICE_ID` 逐字重建匹配，才签名；密码经 Complete 独立 TLS 字段提交，并与同操作密码/角色/账号版本复核，不能混用其他操作的证明。authId/passwordRevision/accountRevision 为服务端快照，不在匿名挑战披露。

不能以十字段形状相同为由接受 LOGIN_WITH_EMAIL/REGISTER，domain/version/action 全部精确匹配。不把 password 登录签名当 MFA：本机新私钥只证明这把新公钥可用。

## 密码验证与幂等记录

新操作 HMAC 秘密独立于邮箱/JWS/设备算法；提案使用 `AUTH_PASSWORD_OPERATION_HMAC_KEY`，严格标准 Base64 随机 32 字节，keyId 用设备 Frame 标签隔离后 SHA-256 派生。该 key 不是密码 salt，不代替 Argon2id。

改密请求指纹编码提案：

```text
HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-change-request-v1"), UTF8(authId), UTF8(requestId),
  UTF8(originalSessionId), U64BE(originalAccountRevision), U64BE(originalPasswordRevision),
  UTF8(normalizedCurrentPassword), UTF8(normalizedNewPassword)
))
```

只持久化 tag/keyId 与必要版本/标识，不保存上述含密码明文的 Frame；24 小时窗口后删除。完成重试使用记录原 sourceSessionId/版本重建 tag，不以新 Session 改写原操作；不重返秘密。重置用途为 RESET_PASSWORD，提案编码如下（U64BE 整数均服务端生成、非负，角色版本属于唯一登录角色）：

```text
resetRequestMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-request-v1"), UTF8(requestId), UTF8(normalizedLoginEmail),
  UTF8(serviceId), UTF8("iwut-client")))
resetCodeMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-code-v1"), UTF8("RESET_PASSWORD"), UTF8(operationId),
  UTF8(authId), U64BE(loginRoleRevision), U64BE(passwordRevision), U64BE(accountRevision),
  U64BE(expiresAtUnixMs), resetRequestMac, UTF8(code8)))
resetCompletionMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-completion-v1"), UTF8(operationId), resetCodeMac,
  UTF8(normalizedNewPassword)))
keyId = SHA256(Frame(UTF8("iwut-password-operation-key-id-v1"), K_operation))
```

占位 resetCodeMac 用随机 dummy owner/版本，只用于 acceptable=false，不给真实账号补默认。真实码/完成 tag 最终复核固定版本，不赋新授权。短期重置记录可在 Auth 保护的存储保存规范地址，幂等唯一键 `(normalizedLoginEmail,requestId)` 不依赖可冷换 operation key，因此换钥不能绕过原幂等窗口；邮箱不进日志/审计。匿名地址限流桶采用既有邮件额度的受保护地址键，operation key 不为它派生新预算。

冷换操作 key 应使未完成操作不可消费，不影响长期 Argon2id 密码；完成记录只能按 UC033 只读恢复，不能借旧 HMAC 制造新变更。密码变更与账号治理/登录角色切换的版本复核优先于历史幂等成功。

## Session 与安全代际

- UC034 新登录方法 `PASSWORD_AND_DEVICE`：credentialId、passwordRevision>0，新的 accountRevision/认证时间；必须有本次新签名。
- UC033 正常改密换发方法 `PASSWORD_AND_SESSION`：credentialId、sourceSessionId、passwordRevision>0、新 accountRevision/认证时间；来源是旧 Session＋当前密码，不伪造 device 签名。token/sessionId 新建，旧来源 Session 不继续有效。
- 保留既有 DEVICE_CREDENTIAL、EMAIL_CODE_AND_DEVICE；所有方法都要求合法当前凭据、owner、UC033 凭据下界和 UC022 账号代际，并在 LRU/列表/身份签发/OAuth 绑定/退出等消费路径完整分派；未知/缺字段失败关闭。

设备凭据新字段 credentialRevision 与 principal.minimumCredentialRevision 只在服务端持久化/检查，不添加到既有 LOGIN 字节。正常改密/重置推进 accountRevision，旧 Auth audience identity 与 opaque OAuth 材料拒绝；App 离线 JWS/第三方自有登录态的旧残余窗口不由新 Session 格式收回。

## 接受与交付门禁

统一 reason：400 INVALID_PASSWORD_REQUEST/PASSWORD_POLICY_REJECTED/PASSWORD_UNCHANGED；401 SESSION_INVALID/PASSWORD_AUTHENTICATION_FAILED/PASSWORD_RESET_FAILED；409 PASSWORD_REVISION_CONFLICT/PASSWORD_REQUEST_CONFLICT/PASSWORD_CHANGE_ALREADY_COMPLETED/PASSWORD_LOGIN_ALREADY_COMPLETED；429 PASSWORD_RATE_LIMITED；503 PASSWORD_UNAVAILABLE。正文过大为 413 PASSWORD_REQUEST_TOO_LARGE；邮件明确投递故障沿用 EMAIL_DELIVERY_UNAVAILABLE。密码登录除语法/限流/依赖外统一 PASSWORD_AUTHENTICATION_FAILED，包含密码、owner、角色、签名、操作无效，不区分不存在账号。

字段/HMAC 已接受；须补公开 Frame/hash/MAC/NFC 正反向量、验证注册版本及敏感动作无旁路；算法参数压测、blocklist 正式来源和容量实际测试为启用门禁。脚本开工 brief 已配置，可执行 API 独立交付，不改变历史向量。

公开测试向量：[auth-password-v1.json](test-vectors/auth-password-v1.json)；生成/校验脚本 `tools/auth_password_protocol_vectors.py --write/--check`，需 cryptography 和 argon2-cffi（独立 libargon2）。Go 使用 x/crypto 校验同一 hash/Frame/MAC/NFC 与 DER 正反向量；所有固定密码/salt/key/码仅供公开测试，绝不能作为运行默认。原设备/邮箱 v1/v2 文件未改写。
