# UC-AUTH-011：设置并激活邮箱

状态：`PROPOSED`

## 目标与范围

> 用户主动提交邮箱并验证控制权：发起时有有效 Session，激活邮箱到当前账号；发起时明确不携带 Session，验证后创建新账号并激活邮箱。更换邮箱时，新邮箱验证成功后才替换旧邮箱。

注册页提供两个明确选择：“一键注册”沿用 [UC-AUTH-006](UC-AUTH-006-create-user.md)；“使用邮箱注册”走本 UC 的匿名注册分支，不需要先一键注册取得 Session。本 UC 同时覆盖已有账号的首次绑定、更换、重发验证和本人绑定查询。

邮箱注册复用已有的设备密钥和必填 associationToken，验证成功后原子创建账号、初始设备凭据、首次 Session 及邮箱绑定，用户立即进入普通登录功能。客户端准备设备密钥不要求额外生物识别，也不等于提前创建平台账号。

不要求学校邮箱，不设置平台密码，不自动修改学生资料，不合并账号，不授予 Developer 资格。**已有账号的邮箱登录、恢复及新增设备凭据仍须独立用例**；本次注册签发首次 Session 不代表邮箱恢复已经交付。

## 参与者与前置条件

- Begin 未携带 Session 时选择 `REGISTER`；携带有效 ACTIVE USER Session 时选择 `BIND`。提交了空值、格式错误、过期、已撤销 Session 或不可用主体时拒绝，绝不降级为匿名注册。
- 模式在 Begin 固定。BIND 同时固定 Session 对应的 authId，Complete 必须有同一账号的有效 Session；REGISTER 的 Complete 不携带 Session，通过邮箱验证码和新设备私钥证明完成注册。途中登录、退出或切换账号不能改变操作模式；客户端要切换流程需重新 Begin。
- REGISTER 要求用户明确选择创建新平台账号，提交新设备凭据提案与必填学校账号关联声明；客户端已保存学校账号密码的前置流程及隐私边界引用 UC006，不上传学校密码或原始学号。
- BIND 不接受注册提案或关联声明，不改变已有账号的学校关联。authId 只取自 Session，不能由请求体指定；当前身份和凭据有效性遵守 [BR-LGN-004](UC-AUTH-007-login.md#br-lgn-004)。
- 用户明确提交目标邮箱。客户端不得从学校数据、资料字段或本机缓存自动发起注册或绑定。Auth 配有邮件发送适配器，邮件系统不决定账号归属。

## 输入与输出

```text
BeginSetEmail {
  requestId: UUID
  email: string
  // 以下两组互斥，且必须与 Session 是否提供一致：
  binding: { expectedRevision: int64 } | null
  registration: {
    credentialProposal: CredentialRegistrationProposal
    association: StudentAssociationDeclaration
  } | null
}

EmailVerificationStarted {
  operationId: UUID
  mode: REGISTER | BIND           // 服务端固定，不是客户端可信声明
  targetEmail: string
  expiresAt: Instant
  resendAfter: Instant
  registrationChallenge: null | {
    challenge: Bytes
    signingPayload: Bytes
    protocolVersion: string
  }
}

CompleteSetEmail {
  operationId: UUID
  code: string
  registrationProof: CredentialRegistrationProof | null
}

EmailActivated {
  operationId: UUID
  mode: REGISTER | BIND
  email: string
  verifiedAt: Instant
  revision: int64
  registrationResult: UserRegistrationResult | null
  // REGISTER 首次成功包含 authId、credentialId 和首次 Session；BIND 为 null
}

GetOwnEmailBinding {}             // 仍要求有效 Session

OwnEmailBinding {
  revision: int64                 // 账号尚未绑定时为 0
  activeEmail: null | { email, verifiedAt }
  pending: null | { operationId, targetEmail, expiresAt, resendAfter }
}
```

以上是逻辑消息。UUID、时间、已有凭据公钥/签名编码引用 [设备认证与 Session 契约](../../platform/contracts/auth-device-session-v1.md)，注册提案和结果类型引用 UC006。REGISTER 另需邮箱注册专用的签名上下文，不能直接把 UC006 的 REGISTER 签名用于本接口，交付要求见下文。

BIND 的 expectedRevision 必填，首次绑定为 0；REGISTER 不能提交已有账号的 revision。Complete 的 REGISTER 分支必须提交设备证明，BIND 分支不接受该字段。客户端不能提交 authId、verified、emailLoginEnabled、角色或服务器时间。

重发使用新 requestId 再次 Begin，并保留原模式和提案；REGISTER 保留同一设备密钥与关联声明，不因发信失败重建密钥。本人查询不向匿名用户开放，pending 只表示本人仍可验证的 BIND 提案；匿名注册依靠 Begin 幂等响应恢复操作元数据。

## 主流程

1. 用户选择邮箱注册，或者在已登录账号中设置邮箱。Auth 检查 Session 的缺失/有效/无效三种情况，固定 REGISTER 或 BIND，并验证对应输入。
2. Auth 检查地址、提案、幂等键和限额，保存一次性验证操作。REGISTER 此时只保存提案，不创建 USER、凭据或 Session；BIND 保持旧邮箱有效。
3. 操作提交后，Auth 向目标邮箱发送对应注册或绑定用途的验证码，返回操作信息。发送适配器接受邮件不等于收件箱已送达。
4. 用户输入验证码。REGISTER 同时以本次提案私钥签署邮箱注册挑战；BIND 携带同一账号的有效 Session。
5. Auth 校验固定模式、操作上下文、验证码、有效期和尝试次数，并验证该分支的设备证明或 Session。
6. REGISTER 按 BR-EML-009 原子创建账号、初始设备凭据、学生关联、首次 Session 和激活邮箱；BIND 按 BR-EML-004 原子更新现有账号邮箱。两者都消费操作并记录结果。
7. 提交确定成功后返回 EmailActivated。REGISTER 客户端保存凭据标识和首次 Session；BIND 保留原登录状态，不额外创建 Session。

## 业务规则

<a id="br-eml-001"></a>
### BR-EML-001：邮箱凭据与资料、身份分离

邮箱绑定由 Auth 独立管理，不写入用户资料 KV；资料中的邮箱即使文字相同，也不成为已验证凭据，二者不自动同步。邮箱验证只证明本次操作期间的邮箱控制权，不证明学生身份、真实姓名或永久所有权。

首版每个 authId 最多有一个激活邮箱，每个规范化邮箱最多属于一个 authId。待验证提案不占用全局邮箱归属，不能阻止真实邮箱持有人操作。已激活邮箱只允许由其所属账号更换，不能因另一个账号提供了正确验证码就转移归属。已占用地址无论在 REGISTER 还是 BIND 分支都不能再次激活。冲突不创建或合并 USER，也不沿学生关联寻找账号；即使验证码正确，也不自动登录占用该邮箱的旧账号。

<a id="br-eml-002"></a>
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

<a id="br-eml-003"></a>
### BR-EML-003：分支授权与验证码隔离

REGISTER 用新设备私钥持有证明加邮箱验证码授权创建；BIND 用原账号有效 Session 加新邮箱验证码授权绑定或更换。首版不额外要求生物识别、旧邮箱验证码或学校认证。GetOwnEmailBinding 始终需要有效 Session。Session 无效与 Session 缺失不是同一情况，不能用认证失败触发注册。

验证码由服务端密码学随机生成，首版为均匀的 8 位十进制字符串，保留前导零，寿命 10 分钟，最多 5 次错误尝试；等于 expiresAt 时即过期。BIND 操作的 purpose 为 `BIND_EMAIL`，固定 authId、目标邮箱、绑定 revision 与部署上下文；REGISTER 操作的 purpose 为 `REGISTER_WITH_EMAIL`，固定目标邮箱、新设备公钥、关联声明快照与部署上下文，不预先建立 USER。

REGISTER 的设备签名覆盖独立用途、operationId、随机挑战、期限、服务/应用上下文、规范化邮箱、公钥及关联声明摘要。验证码与设备签名必须对应同一个操作；不能拼接两个操作的证明。邮箱注册挑战随本操作使用 10 分钟期限，不改变 UC006/007 原有 5 分钟挑战。Complete 不接受改写 Begin 的输入；邮箱登录/找回验证码、普通设备注册签名和邮箱注册证明不能跨用途使用。

持有邮箱验证码而没有原账号有效 Session，不能绑定或更换原账号邮箱；这不阻止用户走匿名 REGISTER 创建独立新账号。只有 operationId 也不能完成注册。错误验证码或设备证明共用有界失败尝试计数，计数与关闭操作原子更新；并发不能突破限制。过期判断使用服务端时间，不依赖 Mongo TTL。

<a id="br-eml-004"></a>
### BR-EML-004：更换与原子激活

本规则适用于 BIND。每个账号只保留一个当前可验证提案；新 Begin 成功创建操作时使旧提案失效，且必须先通过 revision 和限额检查。重发不延长旧验证码寿命，生成新验证码和新 operationId；晚到的旧邮件不能激活。Begin 的数据库失败不替换原提案。

邮箱绑定 revision 独立于用户资料 revision；未绑定为 0，每次成功激活递增一次。请求当前已激活的同一规范化地址返回 `EMAIL_ALREADY_ACTIVE`，不发邮件、不增加 revision。提交必须与 Begin 固定的 expectedRevision 相符，且操作仍是当前提案；冲突不自动覆盖新绑定。

激活将唯一邮箱归属、账号绑定、revision、操作成功结果和最小审计记录原子提交。旧邮箱在此之前始终有效；新验证码错误、过期、投递失败、冲突或事务回滚均不删除旧绑定。提交后旧地址释放，可被以后验证成功的账号使用；它不再具有原账号的认证资格。

更换不撤销已有设备 Session，不修改设备密钥或 Developer 状态。本 UC 不定义尚未存在的邮箱认证 Session；未来邮箱登录用例必须定义凭据版本引用、待登录挑战在更换后的失效，以及既有邮箱 Session 的处理，再开放该登录入口。

<a id="br-eml-005"></a>
### BR-EML-005：重试与提交结果不确定

Begin 的幂等范围为 BIND 的 `(authId, requestId)` 或 REGISTER 的 `(规范公钥指纹, requestId)`，至少保留 24 小时。相同请求要求模式、规范化目标邮箱及对应提案一致（BIND 的 revision；REGISTER 的完整凭据和关联声明）。关联提案比较遵守 BR-REG-008 的秘密存储边界；幂等记录仅额外保留以邮件验证密钥保护、覆盖完整请求上下文的 HMAC 指纹，不另存明文 token 或公开摘要，保留期与幂等窗口一致。同键不同提案返回冲突；窗口内相同请求返回原操作元数据，不重复发信、不延长寿命、不复活失效操作。REGISTER 已完成时 Begin 重试返回 REGISTRATION_ALREADY_COMPLETED；已失效或无法重建挑战时返回 EMAIL_VERIFICATION_FAILED，不要求保留已清理的关联密文以重建 signingPayload。窗口后不保证 Begin 去重，不得把旧 requestId 用于新业务请求。

BIND 的成功结果至少保留 24 小时。窗口内同一账号使用有效 Session 和原验证码重试，只返回该操作的历史结果，不重复变更或恢复被更换的旧邮箱；当前状态以 GetOwnEmailBinding 为准。保留窗口后返回操作不可用。Session 已失效时仍拒绝绑定、查询和成功结果恢复。

REGISTER 遵守 [BR-REG-006](UC-AUTH-006-create-user.md#br-reg-006) 的一次性注册结果语义：同操作最多创建一个账号及首次 Session，成功重放只返回 `REGISTRATION_ALREADY_COMPLETED`，不再次披露 Session token 或账号资料。完成标记的保留不得短于 Begin 幂等窗口；即使操作记录后来清理，公钥唯一归属也不释放。客户端在响应丢失、提交未知或已完成时保留原私钥，通过 UC007 发起新的设备登录恢复同一账号，不能换密钥重建账号。

Begin 和 Complete 提交结果未知时返回不可用，不声称已回滚。Begin 使用原 requestId 重试取回操作元数据；未完成且无法投递时，冷却后显式重发。REGISTER 重试不依赖原本不存在的 Session；BIND 重试不得因丢失 Session 而变成 REGISTER。服务端也不能因为 Complete 恰好携带了一个 Session 就更改匿名操作的模式。

<a id="br-eml-006"></a>
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认 BIND 按账号、REGISTER 按规范公钥指纹控制发送间隔至少 60 秒，两分支共用目标邮箱至少 60 秒的发送间隔；每账号/公钥指纹及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次。匿名注册还复用 BR-REG-007 的未完成挑战容量限制，不以可任意更换的公钥指纹作为唯一防滥用依据；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；以独立的邮件验证 HMAC 密钥保护校验值，输入覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较。不与学生关联密钥、Session 摘要或 JWS 签名密钥共用秘密。密钥由 ENV 注入；首版冷更新换钥可使未完成验证码失效，不需要为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功 BIND 操作可能无法凭原码重放，客户端以当前查询恢复状态；已完成 REGISTER 通过设备登录恢复。

REGISTER 的关联声明快照、加密、清理与冷更新轮换继承 [BR-REG-008](UC-AUTH-006-create-user.md#br-reg-008)：轮换必须一并关闭未完成邮箱注册操作并清除关联密文，不能遗漏新增的操作类型；已完成账号与完成标记保持不变。

邮箱明文是用户主动提供的认证数据，仅在 Auth 的绑定、短期操作及邮件投递中使用；不自动加入用户 JWS、对外资料接口或 Developer 状态投影。审计只保留 authId、operationId、绑定 revision、时间和结果，不记录完整邮箱、验证码或 Session token。过期操作和成功结果在所需保留窗口后清理。

<a id="br-eml-007"></a>
### BR-EML-007：查询与占用披露边界

本人查询必须使用有效 Session，返回一致快照，包含当前激活地址及当前待验证提案；不接受按邮箱或他人 authId 查询。Begin 对空闲邮箱和被其它账号占用的邮箱采用相同正常验证流程、响应结构和邮件措辞，不提供预查“是否已注册”接口。

只有已通过当前操作邮箱验证码验证后，Complete 才可返回 `EMAIL_UNAVAILABLE` 表示地址不可用于本账号，不返回占用者 authId、资料或 Developer 状态。占用判断必须在提交点重新确认，不能把 Begin 时查重当成承诺。REGISTER 冲突时不创建新账号，也不自动切换为邮箱登录；客户端提示使用已有账号登录入口，该入口未交付时不能伪装成可用恢复方式。

<a id="br-eml-008"></a>
### BR-EML-008：恢复与 Developer 开通边界

BIND 激活邮箱不签发 Session、不添加设备公钥；REGISTER 只为本次新账号建立初始设备凭据及首次 Session。两者都不自动开放已有账号的邮箱登录，也不为账号加 Developer 标记。未来邮箱登录必须独立验证当前邮箱控制权并回到原 authId；新增设备凭据也要有独立授权与私钥持有证明，不能继承旧设备私钥或由 associationToken 授权。

后续 Developer 开通用例应以“已有激活邮箱，且平台已交付可用的邮箱登录能力”为前置条件，不能仅检查资料中存在邮箱或本 UC 的 activeEmail 非空。日常设备凭据登录不因此被禁止。邮箱移除不在本 UC 内；未来若提供移除，应确保 Developer 不失去最后可用的邮箱登录方式，更换则沿用本 UC 的先验证后替换。

<a id="br-eml-009"></a>
### BR-EML-009：邮箱注册的原子创建

REGISTER 复用 UC006 的 [主体初始化](UC-AUTH-006-create-user.md#br-reg-002)、[凭据唯一归属](UC-AUTH-006-create-user.md#br-reg-003)、[关联声明](UC-AUTH-006-create-user.md#br-reg-004)及[关联组](UC-AUTH-006-create-user.md#br-reg-005)规则，首次 Session 复用 UC007。设备证明和邮箱验证码均通过前，不创建临时 USER，不建立设备归属，不占用邮箱地址。

一次 Mongo 事务提交新 USER、初始设备凭据、必需的关联成员关系及必要的新关联组、首次 Session、revision 为 1 的已验证邮箱绑定、邮箱唯一归属、操作消费与审计。任何失败全部回滚；不能先调用 UC006 Complete 建号，再单独绑定邮箱。邮件发送在事务外，初始登录令牌仅在确定提交后返回。

每个规范公钥指纹只允许一个当前待验证 REGISTER 提案；同一密钥重发使旧邮箱注册提案失效，不影响其它密钥的操作，不能仅按收件地址作废其它用户的挑战。已登记公钥不能用本分支给旧账号补绑邮箱，也不能创建第二账号。邮箱注册和 UC006 一键注册并发使用同一公钥时，凭据唯一性确保最多一个账号成功；失败方必须先通过 UC007 登录确认结果，再以 Session 发起 BIND，不能默默将注册验证码用于旧账号绑定。

同一关联声明仍可对应多个独立 authId，关联声明不用于查找并登录旧账号。被占用邮箱或公钥冲突不留下半创建账号；“有 Session 绑定、无 Session 注册”的选择只在 Begin 生效，后续不能重新推断目标。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 地址、标识、对应分支提案、必填 revision 或验证码格式非法 | `INVALID_EMAIL_REQUEST` | 400 / INVALID_ARGUMENT |
| 提交的 Session 无效；BIND Complete 缺少有效 Session | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 请求携带情况与固定模式不符，例如 REGISTER Complete 携带 Session | `EMAIL_FLOW_MISMATCH` | 409 / FAILED_PRECONDITION |
| 未知/他人/过期/被替代/次数耗尽的操作，或验证码/注册证明错误 | `EMAIL_VERIFICATION_FAILED` | 400 / INVALID_ARGUMENT |
| BIND 的 revision 冲突 | `EMAIL_REVISION_CONFLICT` | 409 / ABORTED |
| 同一幂等键的提案不同 | `EMAIL_REQUEST_CONFLICT` | 409 / ALREADY_EXISTS |
| 本人已激活该地址 | `EMAIL_ALREADY_ACTIVE` | 409 / ALREADY_EXISTS |
| 验证通过但地址已被占用 | `EMAIL_UNAVAILABLE` | 409 / ALREADY_EXISTS |
| 初始公钥已经登记 | `CREDENTIAL_ALREADY_REGISTERED` | 409 / ALREADY_EXISTS |
| REGISTER 操作已经成功，不再次返回 token | `REGISTRATION_ALREADY_COMPLETED` | 409 / ALREADY_EXISTS |
| 请求、发送或未完成操作额度耗尽 | `EMAIL_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 邮件发送失败或结果不确定 | `EMAIL_DELIVERY_UNAVAILABLE` | 503 / UNAVAILABLE |
| 存储不可用或提交结果未知 | `EMAIL_BINDING_UNAVAILABLE` | 503 / UNAVAILABLE |

优先检查提交的 Session；失效 token 不作为匿名身份继续处理。错误不回显邮箱、验证码、占用者或关联组信息。成功 Begin 不证明送达；成功 Complete 只在事务确定提交后返回。

## 测试与验收

1. 无 Session 的邮箱注册在验证码与设备证明通过后，原子创建正式 USER、设备凭据、必填学生关联、已激活邮箱及首次 Session；Begin、取消或验证失败均不留账号。
2. 有效 Session 的首次绑定/更换只操作当前账号，不另建 USER 或 Session；缺失注册关联声明、公钥或证明不能注册成功。
3. 空值、错误、过期、撤销 Session 均不降级成注册；BIND 中途掉线、REGISTER 中途登录、跨账号切换均不改变固定模式。
4. 格式边界、大小写规范化、前导零验证码、`+tag` 和点号不合并；HTTP/gRPC 共用校验。
5. 更换验证前旧邮箱有效；投递失败、错误、过期、冲突不改变旧绑定；成功原子切换并增加一次 revision。
6. REGISTER/REGISTER、REGISTER/BIND 和 BIND/BIND 并发争用同一邮箱最多一个成功；不能凭验证码抢占已有绑定或自动登录旧账号。
7. 同一公钥在一键注册与邮箱注册中并发，最多创建一个账号；失败方不能隐式绑定到胜出账号。
8. 重发使同账号 BIND 或同公钥 REGISTER 的旧操作失效，不作废其它公钥的邮箱注册提案；并发失败计数、限额及验证码消费有界且跨重启有效。
9. 设备签名篡改邮箱、公钥、关联声明、用途、期限或操作标识时失败；不能跨用途或跨操作组合邮箱码与设备证明。
10. Begin 幂等不重复发信；BIND Complete 幂等不重复变更。REGISTER 完成重放不泄露 Session token，丢失首次响应可用原设备密钥登录同一账号。
11. Mongo 回滚、唯一冲突、提交未知和投递前后中断不产生半创建账号或误报成功；禁用/撤销与 BIND 激活遵守现有认证事务确认边界。
12. 本人查询拒绝匿名和他人访问；邮箱/秘密不出现在 JWS、普通日志或审计；关联密钥轮换覆盖未完成邮箱注册操作。
13. 两分支均不授予 Developer 或恢复旧账号，不改变 UC008/009 撤销语义。

## 交付依赖与边界

- 复用 UC006/007 已有主体初始化、凭据唯一性、关联存储、首次 Session 和事务设施；新增组合用例调用领域能力，不在客户端顺序调用“先创建再绑定”冒充原子邮箱注册。
- 接受/生成实现 brief 前，将 REGISTER_WITH_EMAIL 的独立签名上下文、精确字节格式与公开测试向量加入共享协议；保留现有 REGISTER/LOGIN 的格式及期限不变。当前草案不表示旧协议已支持邮箱注册。
- 补齐 EmailBinding 服务 Proto、HTTP annotation 和精确方法鉴权：Begin 允许无 Session 注册或有效 Session 绑定，但拒绝无效 Session；Complete 按持久化模式验证；GetOwnEmailBinding 始终要求有效 Session。Gateway 走 DIRECT，由 Auth 检查原始 Session 载体及证明，不统一套用必需 Session middleware，也不把带错 token 的请求转成匿名。
- 新增邮箱唯一索引、revision、操作/幂等记录、持久化限额、原子审计与邮件适配器；将邮箱注册操作纳入关联密钥冷更新门禁及清理。生产邮件配置由部署注入，不写入仓库。
- 后端使用真实 Mongo 事务和可控邮件接收端验收；公网投递、客户端注册页两种选择及结果恢复独立验收，不向真实用户发送自动化测试信。
- 后续设计已有账号的邮箱登录与新设备凭据登记，闭合恢复能力后再启用 Developer 开通；解绑、旧设备迁移和账号注销分别设计。

## 变更记录

- 2026-09-24：提出设置并激活邮箱草案，定义验证码激活、先验证后更换、唯一归属、重试与邮箱登录/Developer 开通边界。
- 2026-09-24：按注册页两种选择修订：Begin 无 Session 走邮箱注册，有效 Session 走已有账号绑定；固定操作模式，拒绝失效 Session 降级，邮箱注册原子创建账号与首次 Session。仍为 PROPOSED，尚未实现。
