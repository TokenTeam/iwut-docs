# 邮箱设置与注册协议 v2

状态：`ACCEPTED`

## 范围与兼容性

2026-10-12 后续修订边界：本文仍固定已交付的无密码 REGISTER/单邮箱 BIND 字节与字段，不是新增密码/邮箱列表的完整契约。UC006/011 已因注册设置密码、唯一登录角色切换密码验证、非登录绑定增删回到 DRAFT；新字段/版本/接口和旧入口防旁路须审核后另行交付，不擅自修改本 v2 十字段消息或公开向量。本文 BIND 的 Session＋验证码授权仅描述旧基线，不能作为新产品切换登录邮箱的授权。

本契约固定官方客户端、Auth、Gateway 对 UC011 的签名和消息约定，业务规则属于 UC011。2026-10-12 随 UC031 接受；Auth/API 后端与公开 v2 向量已交付，客户端安全存储/交互与 Gateway 公网路由独立验收。应用次数不属于此接口。

基础 Frame、UTF8、U64BE、UUID、严格 Base64url、设备公钥和 ECDSA 编码引用 [设备认证协议](auth-device-session-v1.md)。新设备仍登记 `credentialProposal.protocol_version = "iwut-device-v1"`，设备凭据之后可用于原有 UC007。邮箱注册的待签消息使用独立版本 `iwut-email-registration-v2`，只放在返回的 registrationChallenge 中，不能把它写成设备凭据协议版本。

UC007 LOGIN 与 UC012 LOGIN_WITH_EMAIL 字节格式和既有 Session 载体不变。无邮箱 REGISTER 与邮箱注册 v1 退役，旧证明必须拒绝；不以省略、补零关联摘要或忽略尾随字段实现兼容。旧协议文档和向量仅保留为历史证据。

## 邮箱注册签名字节

REGISTER 分支唯一的签名消息如下，共 10 个 Frame 字段：

```text
signingPayload = Frame(
  UTF8("iwut-email-registration-proof-v2"),
  UTF8("iwut-email-registration-v2"),
  UTF8("REGISTER_WITH_EMAIL"),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65,
  UTF8(normalizedEmail)
)
```

- challenge32 为服务端生成的 32 随机字节；operationId 为服务端 UUIDv4。expiresAtUnixMs 是 Begin 服务端时间加 UC011 的 10 分钟，以 UTC Unix 毫秒精确保存；`now >= expiresAt` 拒绝。
- serviceId 使用既有 `AUTH_AUTHENTICATION_SERVICE_ID` 及其校验范围，applicationId 固定 `iwut-client`；客户端根据部署配置核对，不能仅信任服务端返回的任意上下文。
- publicKey65 是 Begin 中经过 P-256 曲线校验的完整 65 字节非压缩公钥，不是 PEM、SPKI 或指纹。不包含关联摘要；邮箱按 UC011 BR-EML-002 规范化，未规范化的用户输入不能用于验签。
- 签名是对完整 payload 做一次 SHA-256 后的 ECDSA P-256，使用既有严格 DER 验证，接受合法 high-S/low-S。不允许双重哈希。服务端根据操作快照重建待签字节；Complete 只带 DER 签名，不能带可覆盖快照的邮箱、公钥、算法或学校声明。
- payload 最多 1024 字节，必须恰好解出 10 个字段；拒绝非法 UTF8、错误域标签/版本/用途、错误长度、尾随字节、额外字段。客户端核对本次操作的邮箱、公钥、随机挑战、operationId、期限和预配上下文后签名。
- 签名没有验证码字段；验证码由同一 operationId 的服务端记录另行校验，两种证明必须同时通过。BIND 分支没有注册签名挑战或设备证明，以该账号有效 Session 和绑定验证码授权。
- 不保存 signingPayload 明文，不记录验证码或完整证明；操作按 UC011 保存邮箱、公钥和上下文，不保存学校关联快照、不调用关联迁移。

## 退役字段与入口

`RegisterEmailIntent` 的字段 2 和名称 `association` 保留，不重用或转换为资料字段；严格 JSON/二进制输入校验拒绝已退役的关联输入，不把它静默忽略后建号。旧无邮箱注册消息不再作为服务输入，保留已有编号/名称以防复用；`UserRegistrationResult` 和设备提案/证明仍供邮箱注册复用。

移除 BeginUserRegistration/CompleteUserRegistration 的 HTTP 路由，旧 gRPC 方法返回 UNIMPLEMENTED 或不再注册，绝不能委托新邮箱注册自动创建。不得把“停用旧注册”解释成停用 BeginDeviceLogin/CompleteDeviceLogin 或删除设备密钥。

## RPC 与 Session 鉴权

独立 API 目录 `auth_center/v1/email_binding/`，package `auth_center.v1.email_binding`，service `EmailBindingService`，Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/email_binding;email_binding`。

| full method | Auth 鉴权 |
| --- | --- |
| `/auth_center.v1.email_binding.EmailBindingService/BeginSetEmail` | 无 Session 只接受 registration；有效 Session 只接受 binding；任何已提供但无效的 Session 均拒绝。 |
| `/auth_center.v1.email_binding.EmailBindingService/CompleteSetEmail` | 先检查已提供的 Session；按操作固定模式，REGISTER 必须无 Session 且双证明有效，BIND 必须有同账号当前有效 Session。 |
| `/auth_center.v1.email_binding.EmailBindingService/GetOwnEmailBinding` | 必须有当前有效 ACTIVE USER Session，只读本人一致快照。 |

载体只使用 HTTP/gRPC 的 `x-iwut-session`。**缺失**表示 header/metadata 中根本不存在该键；存在但空、空白、重复、逗号合并或非法编码均为无效，不得当成缺失。提供了合法形状但已失效的 token 同样不得匿名降级。禁止从 cookie、query、Authorization 或 x-iwut-identity 回退恢复用户 Session。

Begin 的输入分支与载体不匹配返回 EMAIL_FLOW_MISMATCH；分支缺失、两个分支并存、未知枚举或结构非法返回 INVALID_EMAIL_REQUEST。Complete 中已提供的无效 Session 优先返回 SESSION_INVALID；有效 Session 用于 REGISTER 返回 EMAIL_FLOW_MISMATCH；缺失 Session 用于 BIND 返回 SESSION_INVALID；有效但属于他人的 Session 访问 BIND 操作统一 EMAIL_VERIFICATION_FAILED。未知 operationId 在已提供 Session 校验后统一 EMAIL_VERIFICATION_FAILED。

精确方法表不得把整个 email_binding package 当作匿名，不把 GetOwn 与 Begin/Complete 共用无条件匿名策略；也不将 Begin/Complete 套进必须有 Session 的 middleware。有效 Session 的主体、凭据及使用时间更新复用现有在线检查，业务提交点仍须在事务内再次确认授权。

## 消息字段与 presence

以下为设计字段表，可执行 Proto 及生成物由独立 API 仓库交付。`Auth.*` 表示导入既有 `auth_center.v1.authentication` 消息。所有时间字段使用 int64 UTC Unix 毫秒，与既有 Authentication 消息一致；不另用 Timestamp。ProtoJSON int64 响应为字符串，bytes 遵守标准 ProtoJSON Base64。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `BeginSetEmailRequest` | `1: string request_id`；`2: string email`；`oneof intent { 3: BindEmailIntent binding; 4: RegisterEmailIntent registration; }` |
| `BindEmailIntent` | `1: optional int64 expected_revision`，presence 必需，允许显式 0 |
| `RegisterEmailIntent` | `1: Auth.CredentialRegistrationProposal credential_proposal`，必需；`reserved 2; reserved "association";`，不得复用 |
| `EmailVerificationStarted` | `1: string operation_id`；`2: EmailMode mode`；`3: string target_email`；`4: int64 expires_at_unix_ms`；`5: int64 resend_after_unix_ms`；`6: EmailRegistrationChallenge registration_challenge` |
| `EmailRegistrationChallenge` | `1: bytes challenge`；`2: bytes signing_payload`；`3: string protocol_version` |
| `CompleteSetEmailRequest` | `1: string operation_id`；`2: string code`；`3: Auth.CredentialProof registration_proof` |
| `EmailActivated` | `1: string operation_id`；`2: EmailMode mode`；`3: string email`；`4: int64 verified_at_unix_ms`；`5: int64 revision`；`6: Auth.UserRegistrationResult registration_result` |
| `GetOwnEmailBindingRequest` | 空消息 |
| `OwnEmailBinding` | `1: int64 revision`；`2: ActiveEmail active_email`；`3: PendingEmailBinding pending` |
| `ActiveEmail` | `1: string email`；`2: int64 verified_at_unix_ms` |
| `PendingEmailBinding` | `1: string operation_id`；`2: string target_email`；`3: int64 expires_at_unix_ms`；`4: int64 resend_after_unix_ms` |

EmailMode 枚举固定 `EMAIL_MODE_UNSPECIFIED=0`、`EMAIL_MODE_REGISTER=1`、`EMAIL_MODE_BIND=2`，0 不作为成功结果。mode 不接受请求声明；所有 requestId/operationId 为规范小写 UUIDv4。code 必须恰好 8 个 ASCII 数字，不 trim、不转整数。

REGISTER 的响应必须有 registration_challenge / registration_result，BIND 必须缺省这些字段。BIND Complete 不允许 registration_proof；REGISTER Complete 要求存在且签名非空。presence 不由默认值推断：JSON null 等价于未提供 message，不能满足必需项。本人查询的空 active_email/pending 表示不存在，可省略或按 ProtoJSON 配置输出 null；客户端必须同等处理两种表示，不能以空消息冒充已绑定。

## HTTP 与 Gateway

| HTTP | Auth 内部路径 | 方法 | 成功状态 |
| --- | --- | --- | --- |
| POST | `/v1/email-bindings` | BeginSetEmail | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | CompleteSetEmail | 200（两分支一致） |
| GET | `/v1/users/me/email-binding` | GetOwnEmailBinding | 200 |

POST 的 Proto annotation 使用 body `"*"`。Complete 的 operation_id 由路径绑定并覆盖体中同名值，body 包含 code 和 REGISTER 所需的 registrationProof，不沿用普通设备 Complete 的“只有 proof”。GET 无 body。禁止 query 作为输入；其余严格 JSON、重复字段/oneof 冲突拒绝、16 KiB 请求上限、不支持压缩、no-store 及错误映射遵守 [Auth API 路由](auth-center-api-routing.md)。

三个接口的 Gateway 策略都是 DIRECT；公共 HTTP 前缀 `/auth-center`，转发前剥离；原生 gRPC full method 不加该前缀，gRPC-Web 沿用既有终止方案。DIRECT 必须保留 Session 键是否出现及多值/非法值，不能清理坏 token 后转成匿名；禁止伪造 x-iwut-identity 代替 Session。不因模式为 REGISTER 就把整个服务对外公开，只开放表中三个精确方法。

HTTP 与 gRPC 的 reason/状态由 UC011 错误表拥有；未知枚举/字段等协议错误统一 INVALID_EMAIL_REQUEST。大小超限为 EMAIL_REQUEST_TOO_LARGE（HTTP 413 / gRPC RESOURCE_EXHAUSTED）。限流返回 EMAIL_RATE_LIMITED，附 `retryAfterSeconds`（metadata 字符串，正整数）及 HTTP Retry-After；网络/存储故障不伪装成输入错误。

## 公开测试向量

公开向量为 [auth-email-binding-v2.json](test-vectors/auth-email-binding-v2.json)，由 `python3 tools/auth_email_protocol_v2_vectors.py --write/--check` 确定性生成/验证，独立覆盖十字段消息、规范化、签名和拒绝场景。Auth 的 Go Payload 验证同一 fixture。旧 v1 fixture 保留历史，不用于新注册验收；测试私钥不能作为配置。

后端与移动端验收邮箱规范化、10 字段精确 payload、DER、用途/邮箱/公钥/服务/应用/操作/期限篡改、旧 REGISTER 与邮箱注册 v1 拒绝、关联字段/额外字段拒绝、双重哈希和时间边界。设备 LOGIN 与邮箱登录 v1 既有向量继续回归，旧 REGISTER 正例仅为历史协议检查，不代表旧注册入口可用。

## 交付状态

这里的“完成”仅指此前 v2 基线，不包含平台密码、邮箱列表、登录角色切换或密码恢复；新需求代码未实施，不能直接启用旧无密码接口并声称符合新注册规则。

2026-10-12 完成记录取代下方初建时的待实施说明：公开 v2 向量、独立 API 和 Auth 后端已实现，严格 JSON/二进制退役字段拒绝、真实 SMTP/Wire/Mongo/race 回归通过；客户端/Gateway 与部署仍独立交付。

2026-10-12 随 UC031 接受；v2 向量、API/Go 实现和真实 Wire/Mongo 验收已完成，公网与移动端接入未交付。UC011 后端负责 API/生成代码、严格 HTTP/gRPC transport、邮件适配器、持久化与真实 Mongo/Wire 验收；客户端与 Gateway 路由是独立交付，不能仅凭后端通过就声称公网注册可用。

- 2026-10-12：新建去除学校声明的邮箱注册 v2 设计；保留 BIND 字段与载体、设备 LOGIN 和邮箱 LOGIN 字节，退役旧注册入口。公开 v2 向量、API/代码和客户端尚未实施。
