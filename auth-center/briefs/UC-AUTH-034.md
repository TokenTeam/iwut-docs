<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-034 --spec tools/brief-specs/UC-AUTH-034.json -->
# Brief — UC-AUTH-034：使用登录邮箱与密码登录

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-034` 使用登录邮箱与密码登录 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-LGN-031`–`BR-LGN-034`（4 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-password-v1.md` |

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

用户以当前唯一登录邮箱＋平台密码进入原 iWUT 账号，后台证明本机私钥持有、登记或复用当前有效设备凭据并建立 Session。密码登录作为默认主动登录入口，UC012 邮箱码登录保留为备用，UC007 继续记住登录；不要求每次额外邮件码。

2026-10-13 用户授权开始实现，协议及工程参数作为本工作包接受。不自动注册，不改邮箱/密码/校园认证/权限，不接受非登录学校地址，不把新生成设备密钥当作第二因子或标准 WebAuthn。入口须等 UC033、注册/邮箱及全部认证消费者交付并验收后才能启用。

### 参与者与依赖

- ACTIVE USER 已有 UC033 安全密码材料及 UC011 当前唯一已验证登录角色。
- 客户端准备系统安全存储的 P-256 新密钥，或使用原账号当前仍有效密钥；Auth 不接收私钥/自报 authId。
- 两个匿名入口明确不带 Session，不以已有身份决定目标，不能认证失败后创建账号。
- 硬依赖 UC033 策略/hash/统一代际与凭据下界、UC011 登录角色查询、UC007 Session/LRU 及所有消费路径；当前尚无实现。

### 输入与输出及 API 提案

独立 `auth_center.v1.password_login/PasswordLoginService`，HTTP/JSON/native gRPC，Gateway DIRECT；精确 byte/message/载体见[密码协议草案](../../platform/contracts/auth-password-v1.md)。

```text
BeginPasswordLogin { requestId, loginEmail, credentialProposal }
PasswordLoginStarted { operationId, challenge, signingPayload, protocolVersion, expiresAt }
CompletePasswordLogin { operationId, password, proof }
PasswordLoginResult { authId, credentialId, session: SessionEstablished }
```

Begin 不带密码，以避免把明文秘密存入挑战；Complete 经 TLS 带密码及本机签名。不返回验证码/邮箱存在/owner/内部版本，不调用 SMTP。不改变设备 `iwut-device-v1`，不复用 LOGIN 或 LOGIN_WITH_EMAIL 签名。

### 主流程

1. 用户明确密码登录，提交当前登录邮箱、公钥提案和 requestId；客户端保留对应私钥。
2. Auth 规范地址/公钥，保存独立 5 分钟挑战及当时登录角色/账号/密码版本，或不可登录占位；Begin 不登记凭据、不验证密码。
3. 客户端核对用途/部署/邮箱/公钥/期限，后台签名，Complete 提交密码与签名。
4. Auth 在共用昂贵额度下验证密码与新签名，最终事务再次确认 owner、ACTIVE、角色/密码/账号版本、操作、凭据状态和下界。
5. 同事务登记或复用合法凭据、建立 `PASSWORD_AND_DEVICE` Session、按 UC007 LRU 管容量、消费挑战/审计；确定提交后一次性返回 token。
6. 以后自动登录用 UC007；忘记密码可选择 UC012 备用登录或 UC033 明确重置，不把失败自动变成注册。

### 依赖与变更记录

[UC033/034 readiness](../implements/UC-AUTH-033-034-readiness.md)记录真实代码缺口，2026-10-13 用户授权实现，生成 UC034 brief 后开工；Proto/vector/consumer 完整检查是启用门禁，不迁移旧数据。

- 2026-10-12：建立默认邮箱密码＋后台设备证明登录 DRAFT；保留 UC012 备用码登录及 UC007 自动登录，新增 PASSWORD_AND_DEVICE 和密码/角色/统一代际门禁，待完整审核。

## 业务规则（UC-AUTH-034 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-034-login-with-password.md#br-lgn-031 -->
### BR-LGN-031：唯一登录邮箱与默认密码入口

只认 UC011 当前唯一已验证登录角色，不从邮箱列表任意匹配，备用邮箱码入口保持同样条件。密码存在只允许校验账号既有秘密，不能用“任意已验证地址＋正确密码”更改账号归属或绕过角色选择。未知/非登录/禁用等 Begin 固定不可接受，之后创建/换角色/恢复不会使旧操作有效。

普通密码登录不强制邮件码；前台选择密码或验证码是便利性分支，不改变账号、设备/Session/密码危险动作要求。无密码数据或旧测试缺字段失败关闭，不填默认密码/代际，不因本机密钥缺失自动注册。

<!-- 权威位置: use-cases/UC-AUTH-034-login-with-password.md#br-lgn-032 -->
### BR-LGN-032：独立挑战与密码验证

purpose=`LOGIN_WITH_PASSWORD`、challenge CSPRNG 32 字节、5 分钟、最多 5 次密码/签名验证失败；时刻等于到期即拒绝。签名 Frame 唯一由平台密码协议定义，绑定操作/邮箱/完整公钥/期限/预配 serviceId/applicationId，不包含密码。Complete 不能覆盖提案或由客户端指定验证结果。

密码验证遵守 UC033 Argon2id/NFC/昂贵限额；对不存在或不可接受账号使用同成本受控 dummy verifier，并统一认证错误，不承诺网络层严格等时。需要先捕获密码快照，最终比较版本，不能接受开始验密后发生改密/重置的旧结果。

每次验证失败计数原子更新，依赖故障不伪装为错误密码；一般请求也限流，不能换 challenge 绕过账号/地址桶。Begin 幂等按受保护规范地址＋requestId 24 小时，同键异提案冲突，不重造/延长挑战；容量有界。所有公开占位操作也占容量，不能无限登记任意公钥。

<!-- 权威位置: use-cases/UC-AUTH-034-login-with-password.md#br-lgn-033 -->
### BR-LGN-033：原子登录与不可复活

新公钥登记 credentialRevision=当前 accountRevision；同 owner 公钥只有未撤销且不低于 UC033 下界时可复用。已撤销/退休/他人公钥一律不能绑定或推进版本，须生成新密钥；只有 UC033 正常改密事务能保留当时的当前有效凭据。

Session 方法固定 `PASSWORD_AND_DEVICE`，必需 credentialId、passwordRevision>0、accountRevision 和认证时间；密码版本为签发快照，后续密码变更通过统一账号代际使旧 Session 失效，不用参数重哈希升级踢人。其 Session/LRU/检查/JWS/管理权限与其它合法方法一致，不要求一直保留短期登录操作作为 Session 可用依赖。

最终复核/凭据登记/Session/LRU/操作消费/审计同事务；密码与签名验证外部快照在事务重试时重新确认，旧校验不得穿过版本栅栏。密码/码/设备三种流程不因证明丢失互相降级。

已完成操作不再次披露 token，返回 PASSWORD_LOGIN_ALREADY_COMPLETED；响应未知保留本机私钥，通过 UC007 新挑战确认原账号。与改密/重置并发导致原公钥退休时，旧登录不得返回成功或复活凭据，应由用户重新明确登录并后台换新钥。

<!-- 权威位置: use-cases/UC-AUTH-034-login-with-password.md#br-lgn-034 -->
### BR-LGN-034：失败、隐私与交付

所有匿名失败不区分账号存在、登录角色、密码错误/版本变化、占位或挑战状态；已证明原账号密码/设备控制后才能披露受控公钥冲突。日志/审计只有必要操作标识/结果/时间，无密码/hash/完整邮箱/签名/token。

输入/载体错误 400；认证失败 401；同键异提案或已完成 409；共享昂贵验证/挑战容量 429；存储/hash/审计/提交未知 503。具体 reason/字段号采用已接受密码契约，公开向量与实现逐项交付；默认关闭，不以 UC012 备用入口掩盖 UC034 未交付。

验收必须含两种前台登录、默认/备用明确 UI、非登录地址拒绝、dummy 验证、NFC、挑战/版本/部署/用途串用、5 次失败、幂等/未知提交、同公钥并发和退休拒绝、与改密/重置/换邮箱/禁用/注销竞争，以及所有认证方法 HTTP/native gRPC/Wire/Mongo race/Console/Gateway 回归。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-password-v1.md`：平台密码与密码登录协议 v1 草案

#### 秘密输入与载体

- 仅 TLS 传密码，密码为用户输入的 UTF-8 string；规范化/策略/存储唯一见 BR-PWD-001/002。不由客户端 SHA-256 后把摘要当认证密码，密码不进入 Frame/signingPayload、URL、日志、审计、错误或邮件。
- JSON 固定 lowerCamelCase、bytes 为标准 ProtoJSON Base64、时间为 int64 UTC Unix 毫秒（JSON string）、requestId/operationId 为小写 UUIDv4。body 最大 16 KiB，严格拒绝未知/重复/null/错误分支/query，响应 no-store。
- Session 唯一载体仍 `x-iwut-session`；不接受 Authorization/Cookie/JWS/OAuth token 替代。要求匿名的入口 Session 键必须不存在，已提供空/失效 token 不允许删除后重试匿名。
- Gateway DIRECT 只转发精确方法，不验证密码/owner、不签发“已验证密码”身份头；未知方法默认拒绝，正文与秘密不进入代理日志。

#### 方法与逻辑消息

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

2026-10-13 六个消息/RPC 已进入独立 API Proto 并生成 Go/gRPC/HTTP 客户端；Auth 公开服务仍未注册。新注册/邮箱目录方案见[已接受的邮箱账号 v3 契约](../../platform/contracts/auth-email-account-v3.md)，已实施邮箱核心，但不属于已交付的普通密码登录/重置 API。

#### 密码登录签名字节

设备提案仍 `protocolVersion="iwut-device-v1"`；挑战版本为 `iwut-password-login-v1`，purpose=`LOGIN_WITH_PASSWORD`。基础 UTF8/Frame/U64BE、UUID 文本、P-256/SHA-256、公钥和严格 DER/high-S/low-S 引用[设备契约](../../platform/contracts/auth-device-session-v1.md)。恰好 10 字段：

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

#### Session 与安全代际

- UC034 新登录方法 `PASSWORD_AND_DEVICE`：credentialId、passwordRevision>0，新的 accountRevision/认证时间；必须有本次新签名。
- UC033 正常改密换发方法 `PASSWORD_AND_SESSION`：credentialId、sourceSessionId、passwordRevision>0、新 accountRevision/认证时间；来源是旧 Session＋当前密码，不伪造 device 签名。token/sessionId 新建，旧来源 Session 不继续有效。
- 保留既有 DEVICE_CREDENTIAL、EMAIL_CODE_AND_DEVICE；所有方法都要求合法当前凭据、owner、UC033 凭据下界和 UC022 账号代际，并在 LRU/列表/身份签发/OAuth 绑定/退出等消费路径完整分派；未知/缺字段失败关闭。

设备凭据新字段 credentialRevision 与 principal.minimumCredentialRevision 只在服务端持久化/检查，不添加到既有 LOGIN 字节。正常改密/重置推进 accountRevision，旧 Auth audience identity 与 opaque OAuth 材料拒绝；App 离线 JWS/第三方自有登录态的旧残余窗口不由新 Session 格式收回。

#### 接受与交付门禁

统一 reason：400 INVALID_PASSWORD_REQUEST/PASSWORD_POLICY_REJECTED/PASSWORD_UNCHANGED；401 SESSION_INVALID/PASSWORD_AUTHENTICATION_FAILED/PASSWORD_RESET_FAILED；409 PASSWORD_REVISION_CONFLICT/PASSWORD_REQUEST_CONFLICT/PASSWORD_CHANGE_ALREADY_COMPLETED/PASSWORD_LOGIN_ALREADY_COMPLETED；429 PASSWORD_RATE_LIMITED；503 PASSWORD_UNAVAILABLE。正文过大为 413 PASSWORD_REQUEST_TOO_LARGE；邮件明确投递故障沿用 EMAIL_DELIVERY_UNAVAILABLE。密码登录除语法/限流/依赖外统一 PASSWORD_AUTHENTICATION_FAILED，包含密码、owner、角色、签名、操作无效，不区分不存在账号。

字段/HMAC 已接受；须补公开 Frame/hash/MAC/NFC 正反向量、验证注册版本及敏感动作无旁路；算法参数压测、blocklist 正式来源和容量实际测试为启用门禁。脚本开工 brief 已配置，可执行 API 独立交付，不改变历史向量。

公开测试向量：[auth-password-v1.json](../../platform/contracts/test-vectors/auth-password-v1.json)；生成/校验脚本 `tools/auth_password_protocol_vectors.py --write/--check`，需 cryptography 和 argon2-cffi（独立 libargon2）。Go 使用 x/crypto 校验同一 hash/Frame/MAC/NFC 与 DER 正反向量；所有固定密码/salt/key/码仅供公开测试，绝不能作为运行默认。原设备/邮箱 v1/v2 文件未改写。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `platform/contracts/auth-password-v1.md`（docs 根级共享文档）：权威与兼容边界、密码验证与幂等记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-034-login-with-password.md` | 82 | `c2c660ad9c52` |
| `platform/contracts/auth-password-v1.md` | 124 | `0ac9cd7021d3` |
