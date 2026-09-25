# 邮箱登录协议 v1

状态：`ACCEPTED`

## 范围与兼容性

本契约固定 [UC012](../../auth-center/use-cases/UC-AUTH-012-login-with-email.md) 的客户端、Auth 和 Gateway 协议。它授权邮箱持有人登录原账号并登记/复用本机设备，不是注册协议，也不增加邮箱字符串到 JWS 的投影。

Frame、UTF8、U64BE、规范 UUID、公钥及 DER 签名编码引用 [设备协议](auth-device-session-v1.md)。credentialProposal.protocol_version 仍为 `iwut-device-v1`，供后续 UC007 使用；本次 challenge.protocol_version 独立为 `iwut-email-login-v1`。旧 REGISTER/LOGIN 和 [邮箱注册协议](auth-email-binding-v1.md) 的格式与向量均不变。

## 邮箱登录签名字节

唯一的邮箱登录待签消息由以下恰好 10 个字段组成：

```text
signingPayload = Frame(
  UTF8("iwut-email-login-proof-v1"),
  UTF8("iwut-email-login-v1"), UTF8("LOGIN_WITH_EMAIL"),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65, UTF8(normalizedEmail)
)
```

- serviceId 使用既有 AUTH_AUTHENTICATION_SERVICE_ID 及其校验范围，applicationId 固定 iwut-client；客户端用预配置核对。operationId 是服务端 UUIDv4，challenge 是 32 字节密码学随机数。
- expiresAtUnixMs 为 Begin 服务端时间加 10 分钟，持久化到毫秒；now 等于或超过该值即失效。签名是对完整 payload 做一次 SHA-256 的 ECDSA P-256，严格 DER、合法 high-S/low-S 规则与旧设备协议相同。
- publicKey65 为经过曲线校验的完整 65 字节非压缩公钥。normalizedEmail 按 UC011 BR-EML-002 规范化。payload 上限 1024 字节，严格解析字段数量、长度、UTF8、用途和版本，拒绝任何尾随数据，不协商降级。
- 客户端签名前核对请求邮箱、本机公钥、operationId、挑战、期限及服务/应用上下文；服务端从不可变操作重建 payload，不接受 Complete 替换这些字段。
- 不包含 associationToken、associationDigest、authId、邮箱绑定 revision 或验证码；内部账号/revision/可登录性由 Begin 快照固定，验证码另以同一 operationId 验证。向匿名调用者返回这些内部事实不是验签所需条件。
- 邮箱注册、设备 LOGIN、REGISTER 以及邮箱登录各自有独立上下文；即使同一密钥、邮箱、挑战和期限，证明也不能跨用。

## RPC 与认证载体

API 目录 `auth_center/v1/email_login/`；package `auth_center.v1.email_login`；service `EmailLoginService`；Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/email_login;email_login`。

| full method | 认证 |
| --- | --- |
| `/auth_center.v1.email_login.EmailLoginService/BeginEmailLogin` | 有界匿名；无 Session，仅创建不可变邮箱/设备提案和验证码挑战。 |
| `/auth_center.v1.email_login.EmailLoginService/CompleteEmailLogin` | 有界匿名；验证同一操作的邮箱验证码及设备签名，再确认当前账号/邮箱/凭据。 |

这两个方法要求 `x-iwut-session` 键完全缺失；只要键存在，无论有效、过期、空值或多值，均返回 INVALID_EMAIL_LOGIN_REQUEST，不检查它选择目标账号，也不删除旧账号 Session。不得由 Gateway 清理后转成合法匿名调用。Authorization、cookie 或 x-iwut-identity 不作为替代身份来源；精确方法表只开放上述方法，未知方法仍默认拒绝。

## 消息字段

`Auth.*` 复用 `auth_center.v1.authentication` 消息。以下为设计字段表，不是本仓库的可执行 Proto；独立 API 仓库生成实现。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `BeginEmailLoginRequest` | `1: string request_id`；`2: string email`；`3: Auth.CredentialRegistrationProposal credential_proposal` |
| `EmailLoginChallenge` | `1: string operation_id`；`2: bytes challenge`；`3: bytes signing_payload`；`4: string protocol_version`；`5: int64 expires_at_unix_ms`；`6: int64 resend_after_unix_ms` |
| `CompleteEmailLoginRequest` | `1: string operation_id`；`2: string code`；`3: Auth.CredentialProof proof` |
| `EmailLoginResult` | `1: string auth_id`；`2: string credential_id`；`3: Auth.SessionEstablished session` |

requestId/operationId 使用小写规范 UUIDv4；code 恰好 8 个 ASCII 数字，保留前导零，不 trim。credentialProposal 和 proof presence 必需，JSON null 不满足必需项；未知/重复字段和畸形公钥/签名编码拒绝。请求不含 authId、revision、角色、关联声明或可信校验标志。时间为 int64 UTC Unix 毫秒；ProtoJSON int64 响应为字符串，bytes 遵守标准 Base64。

成功时 auth_id、credential_id 与内嵌 Session 必须一致；认证方法及邮箱绑定 revision 是服务端内部事实，不新增客户端可以指定的 Session 字段。错误不返回部分成功结果或候选 token。

## HTTP 与 Gateway

| HTTP | Auth 内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

Proto annotation 的 body 为 `"*"`。Complete 路径 operation_id 覆盖消息体同名值，body 提交 code 和 proof。公共 HTTP 前缀 `/auth-center` 转发前剥离；原生 gRPC full method 不加前缀，gRPC-Web 沿用既有终止方案。

禁止 query 作为消息输入；继承 [Auth API 路由](auth-center-api-routing.md) 的严格 JSON、默认 16 KiB 请求上限、415 压缩/内容类型拒绝和 Cache-Control: no-store。DIRECT 不是跳过证明验证；不执行 SESSION-to-JWS，也不清除非法 Session 载体以绕过拒绝。

reason/HTTP/gRPC 状态遵守 UC012。超大消息使用 EMAIL_LOGIN_REQUEST_TOO_LARGE（413 / RESOURCE_EXHAUSTED）；限流带正整数秒的 retryAfterSeconds 错误 metadata 和 HTTP Retry-After。已完成操作返回 LOGIN_ALREADY_COMPLETED，不重发 Session token。

## Session 兼容边界

邮箱登录产生的 Session authenticationMethod 为 EMAIL_CODE_AND_DEVICE，credentialId 必填，保存正整数 emailBindingRevision 作为认证来源记录。UC007 的 DEVICE_CREDENTIAL Session 保持原状；EMAIL_CODE_AND_DEVICE 的在线有效性依旧检查当前主体、设备凭据和 Session，不要求来源 revision 等于当前邮箱 revision。

部署必须在开放邮箱登录前完成所有 Session 使用入口对该方法的兼容，包括 UC008/009/010、UC011 BIND/查询和后续需要有效 Session 的命令；未知 authenticationMethod 一律拒绝。不增加下游服务需要识别的 JWS claim，Gateway 与 App Center 仍接收原来的可信用户身份。

## 公开测试向量

[auth-email-login-v1.json](test-vectors/auth-email-login-v1.json) 由 `python3 tools/auth_email_login_vectors.py --write` 生成，`--check` 校验。全部密钥、地址、挑战为公开测试数据；生产不得使用。

向量覆盖精确字节、邮箱规范化、公钥/用途/邮箱/服务/应用/操作/期限篡改、Frame 和 DER 拒绝、双重哈希、旧 LOGIN 与邮箱 REGISTER_WITH_EMAIL 的双向证明隔离，以及 now == expiresAt 的拒绝。固定签名字节不要求生产逐字复现，只要求相同输入验证通过。

旧 `tools/auth_protocol_vectors.py --check` 及 `tools/auth_email_protocol_vectors.py --check` 必须继续通过；本用例不修改旧 fixture。服务端存储 HMAC、事务和审计约定由 UC012 自身定义。

## 交付依赖

协议接受不等于 UC011 实现已完成。UC012 依赖其激活邮箱目录、统一邮件额度、真实邮件适配器及认证事务设施；缺少稳定 UC011 基线时，可在隔离 worktree 实现协议/领域层，但不能用 fixture 或另一个邮箱目录代替该依赖，也不能标记整项实现完成。

- 2026-09-25：固定邮箱登录签名、字段、精确 RPC/HTTP 与 Session 兼容契约；保持其它认证协议兼容。
