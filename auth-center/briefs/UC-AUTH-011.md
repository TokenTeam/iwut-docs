<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-011 --spec tools/brief-specs/UC-AUTH-011.json -->
# Brief — UC-AUTH-011：设置并激活邮箱

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-011` 设置并激活邮箱 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-EML-001`–`BR-EML-009`（9 条） |
| 外部引用 BR | `BR-ACC-012`，`BR-IDN-004`，`BR-LGN-003`、`BR-LGN-004`、`BR-LGN-009`、`BR-LGN-010`，`BR-REG-002`–`BR-REG-008`（7 条）（来自 `UC-AUTH-006`、`UC-AUTH-007`、`UC-AUTH-010`、`UC-AUTH-025`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-email-binding-v1.md` |

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

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](../use-cases/UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

> 用户主动提交邮箱并验证控制权：发起时有有效 Session，激活邮箱到当前账号；发起时明确不携带 Session，验证后创建新账号并激活邮箱。更换邮箱时，新邮箱验证成功后才替换旧邮箱。

注册页提供两个明确选择：“一键注册”沿用 [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md)；“使用邮箱注册”走本 UC 的匿名注册分支，不需要先一键注册取得 Session。本 UC 同时覆盖已有账号的首次绑定、更换、重发验证和本人绑定查询。

邮箱注册复用已有的设备密钥和必填 associationToken，验证成功后原子创建账号、初始设备凭据、首次 Session 及邮箱绑定，用户立即进入普通登录功能。客户端准备设备密钥不要求额外生物识别，也不等于提前创建平台账号。

不要求学校邮箱，不设置平台密码，不自动修改学生资料，不合并账号，不授予 Developer 资格。**已有账号的邮箱登录及邮箱授权下的本机设备登记由 [UC012](../use-cases/UC-AUTH-012-login-with-email.md) 草案定义**；本次注册签发首次 Session 不代表邮箱恢复已经交付。

### 参与者与前置条件

- Begin 未携带 Session 时选择 `REGISTER`；携带有效 ACTIVE USER Session 时选择 `BIND`。提交了空值、格式错误、过期、已撤销 Session 或不可用主体时拒绝，绝不降级为匿名注册。
- 模式在 Begin 固定。BIND 同时固定 Session 对应的 authId，Complete 必须有同一账号的有效 Session；REGISTER 的 Complete 不携带 Session，通过邮箱验证码和新设备私钥证明完成注册。途中登录、退出或切换账号不能改变操作模式；客户端要切换流程需重新 Begin。
- REGISTER 要求用户明确选择创建新平台账号，提交新设备凭据提案与必填学校账号关联声明；客户端已保存学校账号密码的前置流程及隐私边界引用 UC006，不上传学校密码或原始学号。
- BIND 不接受注册提案或关联声明，不改变已有账号的学校关联。authId 只取自 Session，不能由请求体指定；当前身份和凭据有效性遵守 [BR-LGN-004](../use-cases/UC-AUTH-007-login.md#br-lgn-004)。
- 用户明确提交目标邮箱。客户端不得从学校数据、资料字段或本机缓存自动发起注册或绑定。Auth 配有邮件发送适配器，邮件系统不决定账号归属。

### 输入与输出

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

以上是逻辑消息。UUID、时间、已有凭据公钥/签名编码引用 [设备认证与 Session 契约](../../platform/contracts/auth-device-session-v1.md)，注册提案和结果类型引用 UC006。REGISTER 的独立签名上下文、精确消息字段与 RPC/HTTP 鉴权由 [邮箱设置与注册协议 v1](../../platform/contracts/auth-email-binding-v1.md) 固定，不能直接把 UC006 的 REGISTER 签名用于本接口。

BIND 的 expectedRevision 必填，首次绑定为 0；REGISTER 不能提交已有账号的 revision。Complete 的 REGISTER 分支必须提交设备证明，BIND 分支不接受该字段。客户端不能提交 authId、verified、emailLoginEnabled、角色或服务器时间。

重发使用新 requestId 再次 Begin，并保留原模式和提案；REGISTER 保留同一设备密钥与关联声明，不因发信失败重建密钥。本人查询不向匿名用户开放，pending 只表示本人仍可验证的 BIND 提案；匿名注册依靠 Begin 幂等响应恢复操作元数据。

### 主流程

1. 用户选择邮箱注册，或者在已登录账号中设置邮箱。Auth 检查 Session 的缺失/有效/无效三种情况，固定 REGISTER 或 BIND，并验证对应输入。
2. Auth 检查地址、提案、幂等键和限额，保存一次性验证操作。REGISTER 此时只保存提案，不创建 USER、凭据或 Session；BIND 保持旧邮箱有效。
3. 操作提交后，Auth 向目标邮箱发送对应注册或绑定用途的验证码，返回操作信息。发送适配器接受邮件不等于收件箱已送达。
4. 用户输入验证码。REGISTER 同时以本次提案私钥签署邮箱注册挑战；BIND 携带同一账号的有效 Session。
5. Auth 校验固定模式、操作上下文、验证码、有效期和尝试次数，并验证该分支的设备证明或 Session。
6. REGISTER 按 BR-EML-009 原子创建账号、初始设备凭据、学生关联、首次 Session 和激活邮箱；BIND 按 BR-EML-004 原子更新现有账号邮箱。两者都消费操作并记录结果。
7. 提交确定成功后返回 EmailActivated。REGISTER 客户端保存凭据标识和首次 Session；BIND 保留原登录状态，不额外创建 Session。

### 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 请求超过有界大小 | `EMAIL_REQUEST_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
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

### 测试与验收

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

### 实现约定

以下固定本工作包的技术默认，不增加客户端产品确认环节；协议字段的权威来源仍是共享契约。

#### 事务与存储

- 复用既有 Mongo 副本集与认证事务栅栏，注册原子写入范围按 BR-EML-009；不得在事务外先完成 UC006 注册后再补绑定。必要时提取内部事务方法，保持旧 API 行为和 DDD 依赖方向不变。
- 邮箱绑定独立 collection，authId 与规范邮箱分别唯一；每账号一个文档维护 activeEmail/revision 与当前 BIND 操作引用。普通旧 USER 没有该文档视为未绑定、revision 0，首次 Begin 可以建立邮箱能力记录，但不修改主体资料或伪造已激活邮箱。未激活邮箱不占全局唯一键，可用 partial unique index。
- 操作保存不可变模式、身份/公钥定位、规范邮箱、requestId、期限、邮件校验值、请求指纹、状态及失败次数，REGISTER 关联快照按 BR-REG-008 加密。允许复用既有操作集合或专用集合，但轮换门禁和清理必须覆盖全部邮箱注册快照。
- 本人查询返回同一一致快照中的 revision、activeEmail 和当前有效 pending；主动关闭、被替代、过期或耗尽尝试的操作不返回 pending。BIND 成功与操作结果、绑定变更及审计同事务；邮箱替换、禁用、凭据撤销与注册/绑定都参加现有认证栅栏。
- 邮箱 revision 使用非负 int64；到最大值时拒绝再激活并返回 EMAIL_REVISION_CONFLICT，不溢出或重置。审计写入失败则业务回滚。
- REGISTER 提交后清除关联密文，保留完成标记及请求 HMAC 至至少 24 小时幂等窗口结束；失效/过期操作也及时清除关联密文。BIND 历史结果保留至少 24 小时。TTL 仅做物理清理，校验永远使用操作期限/状态。

#### 邮件校验与幂等指纹

`K_email` 是 `AUTH_EMAIL_BINDING_HMAC_KEY` 提供的独立 32 字节随机密钥，使用标准 Base64 编码。校验 HMAC 与请求 HMAC 通过不同用途标签隔离；不得与关联加密/查找密钥或其它认证能力的密钥共用。基础编码引用共享协议。

```text
REGISTER requestBytes = Frame(
  UTF8("iwut-email-request-v1"), UTF8("REGISTER"), UTF8(requestId),
  UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8(credentialProtocolVersion), publicKey65, UTF8(schemeVersion), associationToken32)
BIND requestBytes = Frame(
  UTF8("iwut-email-request-v1"), UTF8("BIND"), UTF8(requestId),
  UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8(authId), U64BE(expectedRevision))
requestMac = HMAC-SHA256(K_email, requestBytes)
codeMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-code-v1"), UTF8(purpose), UTF8(operationId),
  U64BE(expiresAtUnixMs), requestMac, UTF8(code8)))
keyId = SHA256(Frame(UTF8("iwut-email-key-id-v1"), K_email))
```

purpose 分别为 BIND_EMAIL / REGISTER_WITH_EMAIL。requestBytes 中的 token 只在受控内存处理，不能持久化；保存 requestMac 和 codeMac，不保存请求明文编码或 signingPayload。keyId 只用于内部识别校验密钥变化，不对外发布，也不作为密钥使用。

冷更新识别 keyId 变化时关闭旧 keyId 的未完成操作并清除其关联密文；已完成 REGISTER 标记保持，后续同键 Begin 返回已完成而不重新披露 token。旧 keyId 的 BIND 历史验证码不可重放，通过本人查询确认当前状态。保留窗口内旧操作占用原幂等键，不能因换钥创建同键新操作；其它旧/失效操作重试返回 EMAIL_VERIFICATION_FAILED。无需旧邮件 HMAC 密钥继续驻留。日常同密钥重启保留未过期操作。

#### 限额与投递

- 发送采用过去 60 分钟滑动窗口；默认额度引用 BR-EML-006，最近一次发送与 now 间隔不足 60 秒时冷却拒绝。账号/公钥、目标邮箱及可信来源的额度在同一事务中扣除，重试同一 requestId 不重复扣除或投递。限额存储有 TTL、总容量和失效清理，容量耗尽时拒绝新操作，不能丢弃活跃桶以绕过额度。
- SMTP 是首版具体适配器。配置启用开关 `AUTH_EMAIL_BINDING_ENABLED`，默认 false；为 true 时要求已有 `AUTH_USER_ENDPOINTS_ENABLED=true`，HMAC 和 SMTP 配置完整。关闭时不注册三个 HTTP 路由，三个 gRPC 方法返回 UNIMPLEMENTED，不回退为其它认证方法。
- 必需邮件配置：`AUTH_SMTP_ADDR`（host:port）、`AUTH_SMTP_FROM`（平台控制的单个发件地址）、`AUTH_SMTP_TLS_MODE`（仅 `implicit_tls` 或 `starttls`）。`AUTH_SMTP_USERNAME`/`AUTH_SMTP_PASSWORD` 同时配置或同时为空；TLS 必须验证证书及目标主机名，不允许明文降级。可选 `AUTH_SMTP_CA_FILE` 提供受信 CA，包括隔离测试环境的测试 CA；超时 `AUTH_SMTP_TIMEOUT` 默认 10s，必须为正。
- 启动时校验参数、密钥格式和 CA，不给真实邮箱发探测邮件；网络不可用由实际投递返回 EMAIL_DELIVERY_UNAVAILABLE。SMTP 适配器只在事务确认之后调用一次；Begin 幂等重放无论上次投递成功、失败或未知都不再次发送，用户以新 requestId 重发。
- 邮件是固定用途模板，说明本次请求、验证码及期限，不包含学号、关联信息、authId、完整设备公钥或登录链接；目标是否被占用不改变模板。头部地址经过校验，不能拼接用户输入注入任意邮件头。验证码/地址及 SMTP 凭据不记录到日志；发送失败不返回 SMTP 原始正文。
- 用可控 TLS SMTP 接收端验收实际生产适配器，包括超时、拒绝及事务已提交而响应丢失；不把仅 fake sender 的测试当作生产投递已实现，不向真实用户发信。

### 交付依赖与边界

- 复用 UC006/007 已有主体初始化、凭据唯一性、关联存储、首次 Session 和事务设施；Session 秘密/寿命/容量遵守 BR-LGN-003、BR-LGN-004、BR-LGN-010，认证限额遵守 BR-LGN-009，与现有签发/撤销的事务确认遵守 BR-IDN-004；新增组合用例调用领域能力，不在客户端顺序调用“先创建再绑定”冒充原子邮箱注册。
- [邮箱设置与注册协议 v1](../../platform/contracts/auth-email-binding-v1.md) 已固定 REGISTER_WITH_EMAIL 的字节格式、字段号、RPC/HTTP 及 Session 鉴权；公开向量由 tools/auth_email_protocol_vectors.py 生成/校验，旧 REGISTER/LOGIN 格式及向量不变。
- 补齐 EmailBinding 服务 Proto、HTTP annotation 和精确方法鉴权：Begin 允许无 Session 注册或有效 Session 绑定，但拒绝无效 Session；Complete 按持久化模式验证；GetOwnEmailBinding 始终要求有效 Session。Gateway 走 DIRECT，由 Auth 检查原始 Session 载体及证明，不统一套用必需 Session middleware，也不把带错 token 的请求转成匿名。
- 新增邮箱唯一索引、revision、操作/幂等记录、持久化限额、原子审计与邮件适配器；将邮箱注册操作纳入关联密钥冷更新门禁及清理。生产邮件配置由部署注入，不写入仓库。
- 后端使用真实 Mongo 事务和可控邮件接收端验收；公网投递、客户端注册页两种选择及结果恢复独立验收，不向真实用户发送自动化测试信。
- UC012/013 保持 PROPOSED，不包含在本工作包；邮箱登录、Developer、移动端及 Gateway 公网交付不作为 UC011 后端完成的前提，也不能被声称已经完成。

## 业务规则（UC-AUTH-011 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-001 -->
### BR-EML-001：邮箱凭据与资料、身份分离

邮箱绑定由 Auth 独立管理，不写入用户资料 KV；资料中的邮箱即使文字相同，也不成为已验证凭据，二者不自动同步。邮箱验证只证明本次操作期间的邮箱控制权，不证明学生身份、真实姓名或永久所有权。

首版每个 authId 最多有一个激活邮箱，每个规范化邮箱最多属于一个 authId。待验证提案不占用全局邮箱归属，不能阻止真实邮箱持有人操作。已激活邮箱只允许由其所属账号更换，不能因另一个账号提供了正确验证码就转移归属。已占用地址无论在 REGISTER 还是 BIND 分支都不能再次激活。冲突不创建或合并 USER，也不沿学生关联寻找账号；即使验证码正确，也不自动登录占用该邮箱的旧账号。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-002 -->
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-003 -->
### BR-EML-003：分支授权与验证码隔离

REGISTER 用新设备私钥持有证明加邮箱验证码授权创建；BIND 用原账号有效 Session 加新邮箱验证码授权绑定或更换。首版不额外要求生物识别、旧邮箱验证码或学校认证。GetOwnEmailBinding 始终需要有效 Session。Session 无效与 Session 缺失不是同一情况，不能用认证失败触发注册。

验证码由服务端密码学随机生成，首版为均匀的 8 位十进制字符串，保留前导零，寿命 10 分钟，最多 5 次错误尝试；等于 expiresAt 时即过期。BIND 操作的 purpose 为 `BIND_EMAIL`，固定 authId、目标邮箱、绑定 revision 与部署上下文；REGISTER 操作的 purpose 为 `REGISTER_WITH_EMAIL`，固定目标邮箱、新设备公钥、关联声明快照与部署上下文，不预先建立 USER。

REGISTER 的设备签名覆盖独立用途、operationId、随机挑战、期限、服务/应用上下文、规范化邮箱、公钥及关联声明摘要。验证码与设备签名必须对应同一个操作；不能拼接两个操作的证明。邮箱注册挑战随本操作使用 10 分钟期限，不改变 UC006/007 原有 5 分钟挑战。Complete 不接受改写 Begin 的输入；邮箱登录/找回验证码、普通设备注册签名和邮箱注册证明不能跨用途使用。

持有邮箱验证码而没有原账号有效 Session，不能绑定或更换原账号邮箱；这不阻止用户走匿名 REGISTER 创建独立新账号。只有 operationId 也不能完成注册。错误验证码或设备证明共用有界失败尝试计数，计数与关闭操作原子更新；并发不能突破限制。过期判断使用服务端时间，不依赖 Mongo TTL。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-004 -->
### BR-EML-004：更换与原子激活

本规则适用于 BIND。每个账号只保留一个当前可验证提案；新 Begin 成功创建操作时使旧提案失效，且必须先通过 revision 和限额检查。重发不延长旧验证码寿命，生成新验证码和新 operationId；晚到的旧邮件不能激活。Begin 的数据库失败不替换原提案。

邮箱绑定 revision 独立于用户资料 revision；未绑定为 0，每次成功激活递增一次。请求当前已激活的同一规范化地址返回 `EMAIL_ALREADY_ACTIVE`，不发邮件、不增加 revision。提交必须与 Begin 固定的 expectedRevision 相符，且操作仍是当前提案；冲突不自动覆盖新绑定。

激活将唯一邮箱归属、账号绑定、revision、操作成功结果和最小审计记录原子提交。旧邮箱在此之前始终有效；新验证码错误、过期、投递失败、冲突或事务回滚均不删除旧绑定。提交后旧地址释放，可被以后验证成功的账号使用；它不再具有原账号的认证资格。

更换不撤销已有设备 Session，不修改设备密钥或 Developer 状态。邮箱登录操作及设备/Session 扩展由 [UC012 草案](../use-cases/UC-AUTH-012-login-with-email.md) 独立交付，不是本用例的前置依赖；其入口未实现时保持关闭。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-005 -->
### BR-EML-005：重试与提交结果不确定

Begin 的幂等范围为 BIND 的 `(authId, requestId)` 或 REGISTER 的 `(规范公钥指纹, requestId)`，至少保留 24 小时。相同请求要求模式、规范化目标邮箱及对应提案一致（BIND 的 revision；REGISTER 的完整凭据和关联声明）。关联提案比较遵守 BR-REG-008 的秘密存储边界；幂等记录仅额外保留以邮件验证密钥保护、覆盖完整请求上下文的 HMAC 指纹，不另存明文 token 或公开摘要，保留期与幂等窗口一致。同键不同提案返回冲突；窗口内相同请求返回原操作元数据，不重复发信、不延长寿命、不复活失效操作。REGISTER 已完成时 Begin 重试返回 REGISTRATION_ALREADY_COMPLETED；已失效或无法重建挑战时返回 EMAIL_VERIFICATION_FAILED，不要求保留已清理的关联密文以重建 signingPayload。窗口后不保证 Begin 去重，不得把旧 requestId 用于新业务请求。

BIND 的成功结果至少保留 24 小时。窗口内同一账号使用有效 Session 和原验证码重试，只返回该操作的历史结果，不重复变更或恢复被更换的旧邮箱；当前状态以 GetOwnEmailBinding 为准。保留窗口后返回操作不可用。Session 已失效时仍拒绝绑定、查询和成功结果恢复。

REGISTER 遵守 [BR-REG-006](../use-cases/UC-AUTH-006-create-user.md#br-reg-006) 的一次性注册结果语义：同操作最多创建一个账号及首次 Session，成功重放只返回 `REGISTRATION_ALREADY_COMPLETED`，不再次披露 Session token 或账号资料。完成标记的保留不得短于 Begin 幂等窗口；即使操作记录后来清理，公钥唯一归属也不释放。客户端在响应丢失、提交未知或已完成时保留原私钥，通过 UC007 发起新的设备登录恢复同一账号，不能换密钥重建账号。

Begin 和 Complete 提交结果未知时返回不可用，不声称已回滚。Begin 使用原 requestId 重试取回操作元数据；未完成且无法投递时，冷却后显式重发。REGISTER 重试不依赖原本不存在的 Session；BIND 重试不得因丢失 Session 而变成 REGISTER。服务端也不能因为 Complete 恰好携带了一个 Session 就更改匿名操作的模式。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-006 -->
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认 BIND 按账号、REGISTER 按规范公钥指纹控制发送间隔至少 60 秒，两分支共用目标邮箱至少 60 秒的发送间隔；每账号/公钥指纹及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次。匿名注册还复用 BR-REG-007 的未完成挑战容量限制，不以可任意更换的公钥指纹作为唯一防滥用依据；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；以独立的邮件验证 HMAC 密钥保护校验值，输入覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较。不与学生关联密钥、Session 摘要或 JWS 签名密钥共用秘密。密钥由 ENV 注入；首版冷更新换钥可使未完成验证码失效，不需要为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功 BIND 操作可能无法凭原码重放，客户端以当前查询恢复状态；已完成 REGISTER 通过设备登录恢复。

REGISTER 的关联声明快照、加密、清理与冷更新轮换继承 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008)：轮换必须一并关闭未完成邮箱注册操作并清除关联密文，不能遗漏新增的操作类型；已完成账号与完成标记保持不变。

邮箱明文是用户主动提供的认证数据，仅在 Auth 的绑定、短期操作及邮件投递中使用；不自动加入用户 JWS、对外资料接口或 Developer 状态投影。审计只保留 authId、operationId、绑定 revision、时间和结果，不记录完整邮箱、验证码或 Session token。过期操作和成功结果在所需保留窗口后清理。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-007 -->
### BR-EML-007：查询与占用披露边界

本人查询必须使用有效 Session，返回一致快照，包含当前激活地址及当前待验证提案；不接受按邮箱或他人 authId 查询。Begin 对空闲邮箱和被其它账号占用的邮箱采用相同正常验证流程、响应结构和邮件措辞，不提供预查“是否已注册”接口。

只有已通过当前操作邮箱验证码验证后，Complete 才可返回 `EMAIL_UNAVAILABLE` 表示地址不可用于本账号，不返回占用者 authId、资料或 Developer 状态。占用判断必须在提交点重新确认，不能把 Begin 时查重当成承诺。REGISTER 冲突时不创建新账号，也不自动切换为邮箱登录；客户端提示使用已有账号登录入口，该入口未交付时不能伪装成可用恢复方式。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-008 -->
### BR-EML-008：恢复与 Developer 开通边界

BIND 激活邮箱不签发 Session、不添加设备公钥；REGISTER 只为本次新账号建立初始设备凭据及首次 Session。两者都不自动开放已有账号的邮箱登录，也不为账号加 Developer 标记。[UC012](../use-cases/UC-AUTH-012-login-with-email.md) 独立验证当前邮箱控制权并回到原 authId，同时通过验证码授权和私钥证明登记本机设备；不继承旧私钥，也不由 associationToken 授权。

Developer 开通由 [UC013 草案](../use-cases/UC-AUTH-013-apply-for-developer.md) 独立交付，不是本用例的前置依赖；本用例成功不自动开通资格。邮箱移除不在本 UC 内；未来若提供移除，应确保 Developer 不失去最后可用的邮箱登录方式，更换则沿用本 UC 的先验证后替换。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-009 -->
### BR-EML-009：邮箱注册的原子创建

REGISTER 复用 UC006 的 [主体初始化 BR-REG-002](../use-cases/UC-AUTH-006-create-user.md#br-reg-002)、[凭据唯一归属 BR-REG-003](../use-cases/UC-AUTH-006-create-user.md#br-reg-003)、[关联声明 BR-REG-004](../use-cases/UC-AUTH-006-create-user.md#br-reg-004)及[关联组 BR-REG-005](../use-cases/UC-AUTH-006-create-user.md#br-reg-005)规则，首次 Session 复用 UC007。设备证明和邮箱验证码均通过前，不创建临时 USER，不建立设备归属，不占用邮箱地址。

一次 Mongo 事务提交新 USER、初始设备凭据、必需的关联成员关系及必要的新关联组、首次 Session、revision 为 1 的已验证邮箱绑定、邮箱唯一归属、操作消费与审计。任何失败全部回滚；不能先调用 UC006 Complete 建号，再单独绑定邮箱。邮件发送在事务外，初始登录令牌仅在确定提交后返回。

每个规范公钥指纹只允许一个当前待验证 REGISTER 提案；同一密钥重发使旧邮箱注册提案失效，不影响其它密钥的操作，不能仅按收件地址作废其它用户的挑战。已登记公钥不能用本分支给旧账号补绑邮箱，也不能创建第二账号。邮箱注册和 UC006 一键注册并发使用同一公钥时，凭据唯一性确保最多一个账号成功；失败方必须先通过 UC007 登录确认结果，再以 Session 发起 BIND，不能默默将注册验证码用于旧账号绑定。

同一关联声明仍可对应多个独立 authId，关联声明不用于查找并登录旧账号。被占用邮箱或公钥冲突不留下半创建账号；“有 Session 绑定、无 Session 注册”的选择只在 Begin 生效，后续不能重新推断目标。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-025`

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-012 -->
### BR-ACC-012：清理范围与最小永久保留

首版数据策略如下；期限是上限而非必须保存到最后一天。实施时必须检查与各现行永久占用/审计规则的冲突并同步修改，不以本草案直接删除生产数据。

| 数据 | 终止后处理 |
| --- | --- |
| 主体、资料 | 活动存储删除资料 values、显示资料及业务能力；永久最小墓碑仅保留 authId、principalType=USER、CLOSED、最终 accountRevision、terminatedAt、closureOperationId，保证历史引用和不可复活，不保留学校关联、邮箱或公钥 |
| 激活/待绑定邮箱、短期邮件操作 | 清理邮箱原文、唯一归属及短期材料；移除唯一占用的事务提交后才可由新账号重新验证注册。清理前统一不能用该邮箱恢复 CLOSED 账号，不将旧验证码改绑新账号 |
| 设备凭据 | 删除公钥及使用元数据；永久保留规范公钥指纹和 CLOSED authId 的最小占用墓碑，防止旧设备密钥跨账号重用，延续 UC009 不释放密钥归属的约束。新注册必须使用新密钥 |
| Session、挑战及结果、授权交互、code/access/refresh/family | 删除秘密摘要、操作内容及业务记录；由永久主体墓碑防重建，不为检测重放继续保存已终止账号全部 token 历史 |
| grant、pairwise 用户映射 | 删除该 authId 的 consent 内容及 `(authId,sectorId)→sub` 映射；不删除 Application 的 sector。旧 sub 不转交新账号，日志/第三方引用不宣称被删除 |
| 学生关联 | 删除本账号的成员关系及其专属材料；组仍有其他成员时保留组，不暴露或改变其他成员；无成员且无合法未决引用时，在关联事务栅栏下删除 lookup/关联密文和空组。并发注册加成员不得误删共享组 |
| developerHandle | 永久保留规范 handle、原 authId、claimedAt 和终止占用标记；不转让、不释放、不连同邮箱/资料保留。该最小公开命名空间墓碑明确向本人披露 |
| Auth 审计 | 只读期内保留最小事件归因，不保留 token/邮箱/资料副本；账号相关普通事件上限为事件发生后 180 天，已超期的随本次任务清理。注销事件保留 180 天；期满按专用保留任务删除，不由业务更新覆盖 |
| 协调决定、清理进度及查询令牌 | App 确认终局前保留必要决定；查询摘要最多 30 天，详细清理任务在全部步骤完成且终局回执后清理，永久终止事实由最小墓碑承担 |

默认活动存储清理目标为终止后 24 小时，超时告警并保留失败进度，绝不伪报完成。普通日志不应保存上述秘密，已经存在的可识别普通日志轮转上限 30 天；备份自然淘汰上限 30 天。部署未落实这些期限时不得展示该承诺或启用入口。

现有审计的 append-only 表示保留期内不可更新/删除；接受本 UC 时需要明确增加受控保留期清理例外，不能由普通业务账号任意删除审计。永久墓碑的字段就是允许保留的完整集合，不能附加整份 principal 或自由文本快照。

### 来自 `UC-AUTH-010`

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004 -->
### BR-IDN-004：签发与撤销的一致性

签发授权确认点为步骤 5 的成功事务提交。与 Session/凭据撤销、账号禁用、权限及 Developer 状态修改有明确提交顺序：修改先提交时，后续确认不得使用旧状态；签发先提交的 JWS 是已授权的在途结果，随后撤销不追回它，最迟按 exp 与消费方容差停止接受。

Mongo 首版复用认证事务栅栏，并对参与确认的 Session、主体与认证凭据采用条件写以排除快照写偏差。后续 UC004 和 Developer 修改命令必须满足该一致性约定；不能先检查 Session，离开事务，再独立读取权限签发。

签发失败不提交 lastUsedAt；签发成功后，即使 Gateway 转发失败或后端拒绝业务，成功检查产生的 lastUsedAt 不回滚。不以权限不足为理由把一个仍有效的 Session 改为无效。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-003 -->
### BR-LGN-003：会话权威与秘密令牌

Auth 保存 Session 权威状态，每个 Session 只对应一个 authId。sessionId 是非秘密的记录标识，sessionToken 是 CSPRNG 生成、至少 256 bit 随机性的 bearer secret；二者不得互相替代。令牌不编码学号、邮箱、权限或用户资料，不要求 JWT。

token 线格式、摘要输入和认证载体引用[Session 载体契约](../../platform/contracts/auth-device-session-v1.md#session-载体)。服务端持久化 token 的 SHA-256 摘要并建立唯一索引，不保存明文令牌；高熵随机令牌不同于低熵密码，不从密码/学号派生。客户端通过 TLS 传输并安全存储令牌，不在 URL、普通日志、分析事件或崩溃报告中包含它。拥有有效 bearer token 即可使用会话，本规则不宣称自动具有设备持有证明或防重放能力。

每条 Session 记录本次认证方法、凭据引用（设备认证时必填）、authenticatedAt、createdAt、lastUsedAt、expiresAt、撤销状态与时间。lastUsedAt 的使用与更新规则见 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010)。Session 不包含私钥，不被 profile、学生关联或客户端设备名称决定归属。以后添加邮箱方法时必须扩展明确的认证记录语义。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-004 -->
### BR-LGN-004：有效期与在线检查

首版采用固定绝对有效期：T_session 通过 AUTH_SESSION_TTL 配置，为部署必填的正时长，创建时固定 expiresAt；缺失/非法配置拒绝接流量。配置采用 Go duration 格式，示例部署值为 `720h`（30 天）；该示例不是隐式默认值。本轮不自动滑动续期、不签发 refresh token，也不因请求活跃无限延长会话。到期后必须重新完成本用例的设备认证并建立新 Session，不延长旧会话的 expiresAt。后续若增加续期，另行设计轮换与并发语义。

一次成功会话检查必须得到一致、当前的事实：token 摘要匹配，Session 未撤销且 `now < expiresAt`，所属主体为 ACTIVE USER，作为会话认证依据的设备凭据仍有效且归属一致。缺失、损坏、超时或无法读取均失败关闭，不能回退到客户端缓存或只凭旧 JWT 放行。

首版不缓存正向会话授权结果，权威读取不得使用可能落后的副本。建议使用一致快照读取主体、凭据和 Session；检查与撤销/禁用存在并发时，以明确的检查快照为边界。变更提交后才开始的新检查必须看到变更；先已通过的请求可能继续执行，不承诺取消在途业务。

成功检查还须完成 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010) 的使用时间更新；不能先返回检查成功，再异步记录使用时间。此更新不改变固定 expiresAt。

清理过期会话只是存储维护；即使记录未被删除也不能再通过检查。更改配置不追溯改变已有 expiresAt；紧急失效使用显式撤销，不通过重解释时间或静默换令牌完成。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-009 -->
### BR-LGN-009：认证入口的失败与披露边界

Begin/Complete 需要请求大小、挑战尝试次数、创建速率和未完成操作容量限制；按来源/操作/凭据等维度组合，不信任客户端设备 ID。初始参数如下，必须在上线前配置校验，不由学生关联分组代替。

认证入口工程默认值：解压后消息上限 16 KiB、单挑战最多 5 次失败、全局 Begin 每分钟 600 次、全局 Complete 每分钟 1200 次、同来源 Begin 每分钟 30 次、同定位 Complete 每分钟 60 次、未完成挑战最多 10000 条。参数可配置但必须有限且为正，非法配置拒绝启动；总体容量和全局限速即使来源不可确认也必须生效。未知 operationId 的 Complete 同样计入全局 Complete 限流，不能通过制造新定位或未知操作绕过总量保护。来源默认使用受信网络对端，不信任终端自填 forwarded header；Gateway 精细来源限流以后通过受信转发契约接入。挑战次数和未完成容量在 Auth 持久化层原子确认；单进程速率桶允许重启清空，不称为跨重启风控。每来源及每定位桶的存储必须有有限容量、过期淘汰和容量耗尽策略，不能因任意客户端定位形成无限内存增长；即使无法新增细分桶，全局限流仍须生效。

错误不区分未知账号、已撤销凭据、错误签名与账号禁用的具体身份事实。依赖不可用与错误凭据区分，便于客户端重试而不是误创建账号。对外不返回账号是否绑定邮箱、关联组成员、内部验签细节或堆栈。

认证请求/响应正文不进入常规日志；禁止记录 token、完整挑战/证明或任何私钥。操作元数据可以记录 operationId、sessionId、结果和时间，已确认身份后才记录可信 authId。Session 不含用户资料，认证事件不广播敏感声明。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-010 -->
### BR-LGN-010：会话容量与 LRU 淘汰

首版确定单账号最多 10 个有效 Session，即 `N_session = 10`。容量按 authId 统计，覆盖该账号全部设备，不按设备、公钥或学生关联组分别计算；它不是设备凭据数量上限。已撤销、已过期或认证凭据已失效的会话不占有效容量，其物理记录可随后清理，不等待 TTL 删除后才释放名额。

有效登录将创建新 Session 时，若当前有效会话数为 M，先从既有有效会话中按 LRU 选择 `max(0, M + 1 - N_session)` 条撤销，保证提交后的有效数量不超过上限。通常满额时淘汰一条；若既有数据超过上限，在下一次成功登录一并收敛。容量满额本身不拒绝已通过认证的新登录，入口限流规则仍然适用。Begin、无效证明、登录失败和已完成操作的重放均不能触发淘汰。

LRU 以服务端保存的 `lastUsedAt` 升序决定；相同时依次按 createdAt、sessionId 升序确定顺序。新会话的 lastUsedAt 初始化为 createdAt；从未被使用的会话按建立时间参与排序，包括成功响应丢失后遗留的会话。新会话不参加本次既有会话的淘汰候选。

“使用”指 Auth 成功完成 BR-LGN-004 的权威会话检查。检查成功返回前，以服务端时间单调更新 lastUsedAt，不接收客户端提供的使用时间，不因失败检查、退出请求或查询会话列表刷新。后续业务因权限或参数等原因失败，不回滚已发生的会话使用；业务服务仅本地验证既有 JWS 不产生新的 Auth 会话使用事件。首版每次成功检查同步记录，不引入异步写回或时间窗口合并；若以后接受近似 LRU，须显式修改本规则。lastUsedAt 更新不延长 expiresAt。

会话检查及使用时间更新，与 LRU 选择/撤销必须有一致的并发顺序：先完成的使用更新影响后发生的淘汰选择；先被淘汰的会话不能再通过检查或被使用时间更新复活。并发冲突时重新确认状态和候选，不用陈旧候选强制撤销；更新失败不能返回会话检查成功。单机多请求也须满足此规则，具体存储栅栏与 BR-LGN-007 一并验收。

淘汰采用逻辑删除，即写入 revokedAt 并立即停止接受其后续会话检查；物理删除沿用生命周期清理策略。被淘汰会话的设备凭据、账号资料和其他账号会话保持不变，用户仍可用有效凭据重新登录。淘汰、挑战消费与新 Session 创建遵循 BR-LGN-007 的同一原子提交：创建失败则不丢失旧会话；提交成功但响应丢失时，已发生的淘汰不回滚，客户端按既有未知结果规则重新认证。

### 来自 `UC-AUTH-006`

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-002 -->
### BR-REG-002：正式主体与最小初始化

创建时 principalType 为 USER、accountStatus 为 ACTIVE，createdAt/updatedAt 使用同一服务端 UTC 提交时间；developerStatus 为 null，permissions 为空，permissionRevision 从正整数 1 开始。资格与权限含义引用 [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) 和 [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#数据模型)。

profile 初始化严格引用 [BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)，物理结构引用 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。不自动从学校系统、客户端缓存或关联声明推导任何资料值。

首个凭据和首次 Session 必须归属于本次 authId。SYSTEM 不走此入口；不接受客户端声明管理员、Developer 或 Reviewer 身份。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-003 -->
### BR-REG-003：设备凭据持有证明与唯一归属

Auth 只接受已发布、受支持协议的注册证明，校验公钥/算法及证明的绑定关系，并确认调用者持有对应私钥。协议级挑战约束见 BR-LGN-002。客户端“设备验证成功”布尔值不是服务器认证证据；本轮不声称已证明设备未被修改或完成学生真实性验证。

首次注册保留显式创建平台账号和提交关联声明的确认，不要求额外的生物识别或每次签名确认；后续设备登录的服务端证明与触发边界引用 [BR-LGN-011](../use-cases/UC-AUTH-007-login.md#br-lgn-011)，客户端自动登录和本地清理建议见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。具体凭据协议须满足该产品目标，不能把 App 自管设备密钥称作或实现成标准 Passkey。

凭据的稳定标识与归一化公钥指纹由服务端/受信协议适配器确定。首版一个凭据只属于一个 authId，禁止将已有凭据改绑另一个账号；客户端不能通过不同编码、换 credentialId 或新注册 operation 绕过公钥唯一性。具体规范化由凭据协议规定。

同一公钥已注册时，不创建第二个主体，也不直接发放已有主体的 Session；引导使用 UC-AUTH-007 完成新的登录证明。不能复用已消费的注册证明作为登录证明。撤销记录不立即释放公钥唯一归属，注销后的保留/清理另行设计。

一个 authId 可以拥有多条独立 credential 记录，每条保存 credentialId、公钥、协议及状态；服务端不保存私钥。首版每台新设备或每次失去原安全存储后的独立安装都生成新密钥，并在邮箱登录、旧设备授权或其他恢复方式确认同一 authId 后新增一条 credential；不复制、导出或下载旧私钥。服务端凭据撤销由 [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 定义，本机私钥删除与退出编排见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)；只撤销当前 Session 是 [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) 的独立能力。新增凭据和凭据列表仍由后续管理用例授权，当前匿名注册入口不能向既有 authId 添加凭据。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-004 -->
### BR-REG-004：学号关联的声明与隐私边界

关联声明只表示客户端提供了相同的学校账号关联输入，可信度固定为 CLIENT_ASSERTED，不是已验证自然人或已认证学生身份。相同组成员仍是独立账号；关联不得用于认证、找回、账号删除、读取其他成员数据或继承权限。

客户端通过明确版本的规范化与确定性散列生成 associationToken，首版仅面向武汉理工大学，输入为本地保存的该校学号，不增加学校 namespace 或可选学校字段；固定盐或用途字符串按公开信息对待。学号规范化不得丢失前导零或擅自把不同账号折叠。算法、规范化规则和测试向量引用[学号关联声明契约](../../platform/contracts/auth-device-session-v1.md#学号关联声明)，客户端不能自行换版本。

Auth 不通过学校接口验证，也不接收原始学号或学校凭据。注册页说明会提交用于关联的派生信息及其用途，用户明确选择创建平台账号即确认本次提交，不因本地已保存学校账号密码而提前上传。它不是“未上传任何学校相关信息”，固定盐散列也不保证学号无法被枚举。只校验声明形状/版本不能发现伪造：攻击者可能改值领取多份配额，也可能提交他人对应值消耗其配额。

Auth 用专用于关联查找的服务端密钥对规范编码的版本和 token 做 HMAC，持久化 lookupKey；为支持不依赖客户端再次上线的密钥轮换，另保存 associationToken 的认证加密密文。明文只在请求处理或迁移内存中短暂存在，不进入日志或明文持久化快照。挑战快照绑定 lookupKey，并暂存完成注册所需的 token 密文。存储、密钥隔离与轮换规则见 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008)。此措施仅降低单独数据库泄漏的风险，不承诺服务器本身无法枚举学号；密文属于服务器可恢复的派生关联信息，不等于完全不保留该信息。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-005 -->
### BR-REG-005：关联组独立与应用隔离

同一规范化声明的 lookupKey 映射到稳定、服务端随机生成的 associationId；并发首次创建也只产生一个组。多个 authId 可关联同组。经本用例成功创建的每个新账号恰好绑定一个组，修改、解绑、关联方案升级不由注册接口提供。

关联声明是平台注册的必填输入：association 缺失/null，或 schemeVersion、associationToken 缺失/为空/格式不合法时，Begin 在创建挑战前拒绝；未知方案版本按未支持处理。Complete 只能使用已绑定的有效声明，不能省略或替换关联。关联存储不可用时不得降级创建无关联账号，失败的平台注册不删除客户端学校凭据，也不阻断既有无需平台后端的功能。

该要求只保证新建账号具有一份结构有效的客户端声明，不提升其真实性等级、不限制同组只能有一个账号，也不赋予学生关联账号控制权。历史账号如何补充关联不在本用例中隐式迁移；不得把新注册的必填规则直接变成既有登录的额外认证证明。

未来对外仅提供应用范围内的关联标识，建议保存唯一 `(appId, associationId)` 到随机 applicationAssociationId 的映射；不向应用披露 lookupKey、内部 associationId、原始 token 或其他成员账号。appId 来自服务端确认的应用上下文，不由终端任意选择。该映射不需要派生密钥，也不替换对外账号身份标识。

未来若扩展其他学校，必须先设计关联方案版本与既有分组迁移，不通过新增一个默认学校字段静默重算武汉理工大学的既有标识。

本 UC 只建立内部关系，不提供对外映射查询/签发接口。应用授权、缺失值、删除/重新创建后的配额连续性及关联保留期限，由后续对外能力用例定义；不能因一个成员退出登录或注销就隐式重建整个组。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-006 -->
### BR-REG-006：原子创建与结果不确定的恢复

首版采用 Mongo 多文档事务，一次提交 USER、凭据、Session、必需的账号关联绑定、必要的新关联组、操作完成标记和 REGISTER 挑战的消费；任一失败全部回滚。必须在支持事务的部署上交付；不能用顺序写入加“后续修复”冒充原子性。生成标识、Session 秘密和提交候选在事务自动重试期间保持一致，未确认提交不得把 Session 秘密返回客户端。

operationId 只标识一次注册操作，不是登录凭证。相同 operation 最多创建一个 USER 和一个首次 Session；并发 Complete 只有一个消费成功。已消费操作的重放返回 REGISTRATION_ALREADY_COMPLETED，不重新创建、不再次披露 Session 令牌。不同 operation 的同一公钥由唯一索引阻止重复账号。

响应丢失或提交结果未知时，客户端保留原私钥，可先重试同一操作确认，再通过 UC-AUTH-007 发起全新登录。只返回“已完成”不代表已取得可用 Session；不得因为未知结果而自动生成新私钥创建新账号。新挑战的登录成功证明了原账号可用；暂时不可用时继续保留凭据并提示重试。

首次响应遗失可能留下一条客户端未取得令牌的 Session，它不产生额外账号；按会话有效期失效。不得为了重发响应而明文持久化 Session 令牌或无限保留可兑换的注册证明。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-007 -->
### BR-REG-007：注册入口的限额与秘密最小暴露

Begin/Complete 都是有界入口，需要独立限流、挑战有效期、尝试次数和未完成挑战容量限制。限流不能只依赖可伪造的设备 ID 或关联声明；不把“一组只准一个账号”用作去重或滥用防护。入口阈值和输入容量引用 [BR-LGN-009](../use-cases/UC-AUTH-007-login.md#br-lgn-009)，不以无限制默认值上线；客户端兼容矩阵独立验收。

不记录私钥、Session 令牌、完整挑战/证明、学校密码、邮箱恢复秘密或 associationToken。允许记录 operationId、结果、已建立的 authId/credentialId 和时间等受控操作元数据；不得通过失败响应返回匹配关联组、其他成员、已绑定邮箱或数据库内部信息。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-008 -->
### BR-REG-008：关联密钥隔离与单实例离线轮换

首版采用单实例夜间冷更新，迁移内置于 Auth 正式接收请求之前的启动阶段，不要求独立迁移服务或人工先运行迁移脚本。部署时先停止旧进程、等待在途写入结束，再启动新进程；启动门禁通过前不接收业务请求、不启动关联数据写入任务，也不报告 ready，确保不存在其他关联数据写入者。迁移或核验失败则启动失败并退出，不在新旧版本混合时开放服务。暂不设计多实例在线轮换、分布式锁或迁移进度检查点；k8s 改造时再评审在线并发更新方案。

**存储与密钥用途**

- 每个关联组保存 `associationId`、`schemeVersion`、`keyVersion`、`lookupKey`、`nonce`、`ciphertext`（包含认证标签）。`schemeVersion` 是客户端关联方案版本，`keyVersion` 是服务端密钥组版本，二者独立；换服务端密钥不改变客户端 token、关联组或成员绑定。
- 每个密钥组包含独立随机生成的 `K_encrypt` 与 `K_lookup`，分别用于 AES-256-GCM 和 HMAC-SHA-256，不与彼此、Session 或 JWS 签名密钥复用。HMAC 输入为带用途标识的、无歧义编码的 `(schemeVersion, associationToken)`；唯一查找索引为 `(keyVersion, lookupKey)`。
- AES-GCM 使用 12 字节随机 nonce 和完整 16 字节认证标签；同一加密密钥下不得重复 nonce。AAD 使用带用途标识的无歧义编码，绑定 `associationId`、`schemeVersion` 与 `keyVersion`。错误密钥、损坏数据或 AAD 不匹配均认证失败，不使用未通过认证的明文。
- Begin 的操作快照保存同版本 lookupKey 及 token 密文；快照的 AAD 改为绑定 `operationId`，并使用独立的用途标识。Complete 解密并检查与快照 lookupKey 一致，创建新组时以组的 AAD 和新 nonce 重新加密，不能直接复制操作密文。操作完成、失效或过期后清除其 token 密文，保留必要的消费/完成标记。

**精确编码**

基础 Frame/UTF8 编码引用[基础编码契约](../../platform/contracts/auth-device-session-v1.md#基础编码)。本规则固定：

```text
lookupKey = HMAC-SHA256(K_lookup,
  Frame(UTF8("iwut-association-lookup-v1"), UTF8(schemeVersion), token32))
groupAAD = Frame(UTF8("iwut-association-group-v1"),
  UTF8(associationId), UTF8(schemeVersion), UTF8(keyVersion))
operationAAD = Frame(UTF8("iwut-association-operation-v1"),
  UTF8(operationId), UTF8(schemeVersion), UTF8(keyVersion))
```

keyVersion 为部署自定的 1–64 位 ASCII 字母、数字、`.`、`_`、`-` 字符串，精确比较，不解析为数字或排序。associationId 使用服务端 UUIDv4。认证加密明文仅为 token32；ciphertext 为 AES-GCM 密文后连接 16 字节 tag，nonce 单独保存。正常调用每次生成新随机 nonce；向量固定 key/nonce 仅用于验证兼容性。

REGISTER 不明文持久化 signingPayload 或 associationDigest；返回消息从受控快照重建，关联明文仅在受控内存使用，遵守本规则的加密快照和清理边界。

**ENV 配置**

此处配置的是服务端密钥，不是客户端提交的 associationToken。日常启动只注入当前密钥组；轮换启动额外注入上一组，由同一 Auth 进程在启动阶段完成迁移，不维护无限增长的历史密钥列表。变量如下：

| 变量 | 含义 |
| --- | --- |
| `AUTH_ASSOC_KEY_VERSION` | 当前版本；迁移时表示目标版本。 |
| `AUTH_ASSOC_ENCRYPT_KEY` | 当前 K_encrypt，Base64 编码的 32 字节随机密钥。 |
| `AUTH_ASSOC_LOOKUP_KEY` | 当前 K_lookup，Base64 编码的 32 字节随机密钥。 |
| `AUTH_ASSOC_PREVIOUS_KEY_VERSION` | 仅迁移时注入的源版本。 |
| `AUTH_ASSOC_PREVIOUS_ENCRYPT_KEY` | 源 K_encrypt，格式同上。 |
| `AUTH_ASSOC_PREVIOUS_LOOKUP_KEY` | 源 K_lookup，用于核对旧 lookupKey，格式同上。 |

缺少必需项、上一组配置不完整、版本相同、密钥格式非法或加密/查找密钥混用时拒绝执行。配置及密钥不得输出到日志。没有上一组配置时不尝试迁移旧记录，直接执行当前版本的全量核验；发现旧版或未知版本则启动失败，不能把查不到旧 lookupKey 当成新的关联声明。日常启动不因本门禁作废当前版本的未完成注册挑战。

**迁移与幂等重跑**

1. 旧进程停服并排空写入后，新进程加载当前/上一密钥组；使全部未完成 REGISTER 操作失效并清除操作 token 密文，同时清除其他已完成/失效/过期操作遗留的 token 密文；保持已完成操作的完成标记。尚未完成注册的客户端恢复后保留原设备私钥，重新 Begin；已完成或结果未知的注册仍按 BR-REG-006 恢复。
2. 预检查记录版本只能为源版本或目标版本；按不会被迁移更新的 `_id` 顺序完整扫描关联组，游标 batchSize 为 500，不保存上次处理位置。
3. 目标版本记录跳过更新。源版本记录用源 K_encrypt 验证并解密，以源 K_lookup 核对原 lookupKey；计算目标 lookupKey，用目标 K_encrypt 和新 nonce 加密。将 `keyVersion`、`lookupKey`、`nonce`、`ciphertext` 组成一个单文档原子更新，条件包含 `_id` 和源 keyVersion，保留 associationId、schemeVersion 和全部成员关系，不使用 upsert。
4. 首版每批最多 500 条，通过 ordered bulkWrite 提交这些单文档更新，末批不足 500 条也要提交；不建立覆盖整批或全表的多文档事务。批量成功后检查匹配及修改数量与提交数一致，持久化确认至少为 `w:1, j:true`，部署要求更强时遵从更强配置。批次可能部分成功，不把 bulkWrite 当作整批原子提交。
5. 解密失败、查找值不符、未知版本、唯一索引冲突、更新数量不符或数据库错误时停止并报错，不覆盖失败记录、不创建替代关联组。已完成的记录不回滚；修复原因后使用同一源/目标配置重新启动，全表重扫并跳过已迁移记录。写入结果未知也通过重新读取持久化版本判断，不依赖进程内计数或批次完成标记。
6. 完成后全量核验：所有组均为目标版本，能通过目标密钥解密及 lookupKey 一致性检查，关联组总数不变且唯一索引存在，操作快照不再遗留旧密文；核验失败则启动失败。成功后同一进程仅使用当前密钥处理业务，开放请求并报告 ready，无需为开放服务再启动一次。日常启动即使没有迁移写入，也须通过当前版本的全量核验。
7. 确认迁移成功后从部署配置移除上一组 ENV，后续启动只注入当前组；修改部署配置不会清除正在运行的进程已继承的环境，若需立即移除则再安排一次重启。必须完成本轮后才能开始下一次轮换，禁止让第三个版本进入迁移。

幂等指重复执行收敛到相同关联关系和目标版本，不要求重加密得到相同密文字节。2026-09-22 的远端实测（工作区 `benchmarks/key-rotation-20260922/REPORT.md`）中，10 万条关联记录的批量迁移加全量核验三轮中位数为 18.74 秒，已完成迁移后的扫描跳过加核验为 2.93 秒；逐条更新为 166.48 秒。这支持当前启动前批量迁移方案，首次冷更新暂按 5 分钟维护预算准备，备份等额外操作另计；这些数字不是启动超时阈值或耗时上限。

实测环境为 2 vCPU、温热缓存、standalone MongoDB 和 `w:1, j:true`，不能当作 1 vCPU 或正式事务部署的性能保证。正式部署仍须满足 BR-REG-006 的事务要求，并按实际副本集、持久化和网络配置复测；上线验收补充批次部分成功/结果未知恢复、连续两次轮换及仅当前 ENV 启动。基准使用的合成明文 fixture 只为测试对照，生产启动核验不依赖保留原始 token 样本。

移除运行时旧密钥与销毁所有旧密钥副本是两件事：若备份仍含旧密文，需在有限的备份保留期内保有对应恢复能力，或先迁移/淘汰相关备份再销毁旧密钥；备份恢复也必须经过版本检查及必要迁移后才恢复服务。正常 Auth 进程不因此长期注入历史密钥。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核权限管理的 subject_auth_id 由路径绑定，新写方法还绑定 permission，覆盖消息体中同名值。旧方法不接受新增 permission 字段；新字段取值及错误规则见 UC004。
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

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖九个资料/认证 HTTP 方法、两个旧 Reviewer 管理方法与两个新增应用审核权限方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### 基础编码

- `UTF8(s)` 是字符串的 UTF-8 字节，不添加 BOM、终止符或隐式 Unicode 规范化。
- `LP(b) = U32BE(len(b)) || b`；长度为字节数，U32BE 是 4 字节无符号大端整数。`Frame(b1,...,bn)` 为依次连接各 LP，无额外分隔符或字段数量。每种消息固定字段数量，拒绝尾随数据、截断及超过上限的字段。
- `B64U(b)` 为 RFC 4648 URL-safe Base64，无 `=` 填充。解码必须严格并满足重新编码逐字相等，不接受空白、标准 Base64 的 `+`/`/` 或非零尾部填充位。
- 下述 Proto `bytes` 字段传原始字节；JSON 映射遵循 Proto 标准。文档向量的 hex 仅为测试展示，不能作为线上 bytes 字段的另一种编码。
- 新 operationId、credentialId、sessionId 使用小写标准连字符 UUIDv4；authId 沿用主体的 opaque 标识语义，不能由客户端指定或从学号派生。
- 时间采用 UTC Unix 毫秒；签名输入中为 8 字节无符号大端整数。服务端使用整数毫秒创建挑战并持久化，避免 Proto 与 MongoDB 精度转换改变签名。时间过期规则仍由 UC 拥有。

#### 公钥与签名

`protocolVersion = "iwut-device-v1"`，唯一支持的算法为 ECDSA P-256（secp256r1）配合 SHA-256。

公钥使用固定 65 字节未压缩 SEC1 / X9.63 点编码：`0x04 || X[32] || Y[32]`，坐标为无符号大端、保留左侧零字节。拒绝压缩点、PEM、SPKI、其它曲线、无穷点和不在 P-256 曲线上的坐标。Android 的 SPKI 公钥需要在客户端提取坐标转换，不能直接上传证书或 SubjectPublicKeyInfo。

规范公钥指纹为 32 字节：

```text
fingerprint = SHA256(Frame(UTF8("iwut-device-public-key-v1"), publicKey65))
```

`CredentialRegistrationProposal` 的具体字段为 `protocolVersion: string` 与 `publicKey: bytes`。两类 proof 均只有 `signature: bytes`；服务器从 operation 快照取得算法、公钥及待签消息，不接受 Complete 指定新算法、公钥或可信布尔值。

签名为对完整 signingPayload 做一次 SHA-256 后的 ECDSA，在线格式是严格 ASN.1 DER `SEQUENCE(INTEGER r, INTEGER s)`。要求最短 DER、无尾随字节、`1 <= r,s < curveOrder`，最多 72 字节。接受合法 high-S 和 low-S，不把签名字节当幂等键；一次性消费依据 operationId。Android 可使用 `SHA256withECDSA` 对原始 payload 签名；CryptoKit 使用对 Data 签名的 API 并导出 `derRepresentation`。调用会自行哈希的 API 时不得先手动哈希一次。

选型依据：[Apple SecureEnclave P-256 签名](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing)、[Apple P256 公钥表示](https://developer.apple.com/documentation/cryptokit/p256/signing/publickey)、[Android KeyGenParameterSpec 的 P-256 / SHA256withECDSA 示例](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec)。客户端优先使用系统密钥设施，不要求用户认证标志；具体设备不可用时明确报错或采用经客户端验证的系统安全存储方案，不把私钥写入普通业务存储。

#### 挑战与待签消息

注册和登录的挑战响应都增加 `signingPayload: bytes`。服务器保存结构化不可变快照，返回下式的准确字节，Complete 必须从快照重建并验证。客户端签名前严格解析 payload，核对协议、purpose、operationId、challenge、expiresAt、本地预期 serviceId/applicationId，以及自己刚提交的定位与关联摘要；不能把它当作签署任意服务端字节的通用 API。

REGISTER 的 signingPayload 和无密钥 associationDigest 仅在请求内存中生成，不单独持久化、不进入日志；operation 只按 BR-REG-008 保存 lookupKey 与 token 的认证加密密文。Complete 验证解密 token 后重建摘要与 payload，避免明文摘要绕过关联信息的数据库保护。

```text
signingPayload = Frame(
  UTF8("iwut-device-proof-v1"), UTF8(protocolVersion), UTF8(purpose),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs),
  UTF8(locatorKind), locatorValue, associationDigest
)
```

- `purpose` 精确为 `REGISTER` 或 `LOGIN`；challenge 为 CSPRNG 生成的 32 字节，寿命固定 5 分钟，过期不加客户端时钟容差。
- `serviceId` 为服务端部署必填的 `AUTH_AUTHENTICATION_SERVICE_ID`，1–128 个 ASCII 字符，允许字母、数字、`.`、`_`、`:`、`-`。示例 `iwut-auth-center:prod` 与 `iwut-auth-center:test` 必须不同。官方客户端为其目标环境预配置相同值，不能只相信响应。首版 applicationId 固定为 `iwut-client`；不提供动态选择应用参数。
- REGISTER 的 locatorKind 固定 `PUBLIC_KEY_FINGERPRINT`，locatorValue 为新公钥的指纹；associationDigest 为 `SHA256(Frame(UTF8(schemeVersion), associationToken32))`。
- LOGIN 的 locatorKind 为 `CREDENTIAL_ID` 或 `PUBLIC_KEY_FINGERPRINT`，locatorValue 分别为提交的 UUID 文本 UTF-8 或原始 32 字节指纹；associationDigest 为空字节串。BeginDeviceLogin 使用 oneof，必须恰好一个定位值。
- 登录的 payload 保留请求定位方式，不将指纹静默转换为 credentialId。对于未知、禁用、已撤销凭据，Begin 仍返回同形状的 v1 挑战，不返回 authId、credentialId、账号状态或恢复方式；Complete 统一认证失败。依赖故障与限流可以分别返回不可用和限流错误。
- LOGIN 操作保存 Begin 时的内部凭据解析结果；当时不可接受的目标在本操作中始终不可接受。后来注册同公钥或重新启用账号不会让这个旧挑战变成有效登录操作；需重新 Begin。Begin 时有效也不免除 Complete 的当前状态复核。
- 客户端签名输入上限 1024 字节。未知版本、枚举变体、字段错位及额外字段均拒绝；不协商降级到其它算法。
- 成功设备登录结果补充 `credentialId`，使注册响应丢失后通过指纹登录的客户端能恢复非秘密定位信息。它来自成功认证后的服务端凭据，不能成为客户端选择 authId 的输入。

#### 学号关联声明

`schemeVersion = "iwut-student-association-v1"`。首版只有武汉理工大学，没有学校 namespace 或学校选择参数。

客户端先去掉输入两端的 ASCII SP、HT、CR、LF，再要求 1–64 个 ASCII 数字 `0`–`9`。内部空白、全角数字、符号、空串或超长均拒绝；不转整数、不去前导零、不按本科/研究生长度分流。64 是输入容量限制，不表示对学校学号规则的权威验证。

```text
associationToken32 = SHA256(Frame(UTF8(schemeVersion), UTF8(normalizedStudentNumber)))
```

版本字符串兼作用途前缀，是公开常量，不称为秘密盐。Auth 只接受该版本和恰好 32 字节 token；不能在服务器用学校接口或原始学号校验内容。真实性、明确提交和配额边界引用 BR-REG-004/005。

服务端加密、查找和密钥轮换的精确编码由 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008) 定义，客户端不参与这些密钥或内部存储格式。

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/auth-email-binding-v1.md`：邮箱设置与注册协议 v1

#### 范围与兼容性

本契约固定官方客户端、Auth、Gateway 对 [UC011](../use-cases/UC-AUTH-011-set-and-activate-email.md) 的签名和消息约定。业务规则属于该 UC；邮箱登录 UC012 和 Developer 申请 UC013 不因此接受或实现。

基础 Frame、UTF8、U64BE、UUID、严格 Base64url、设备公钥和 ECDSA 编码引用 [设备认证协议](../../platform/contracts/auth-device-session-v1.md)。新设备仍登记 `credentialProposal.protocol_version = "iwut-device-v1"`，设备凭据之后可用于原有 UC007。邮箱注册的待签消息使用独立版本 `iwut-email-registration-v1`，只放在返回的 registrationChallenge 中，不能把它写成设备凭据协议版本。

旧 REGISTER/LOGIN 字节格式、5 分钟期限及旧公开向量保持不变；本协议不向旧待签消息追加字段，不允许解析器通过忽略尾随字段兼容。

#### 邮箱注册签名字节

REGISTER 分支唯一的签名消息如下，共 11 个 Frame 字段：

```text
associationDigest32 = SHA256(Frame(UTF8(schemeVersion), associationToken32))

signingPayload = Frame(
  UTF8("iwut-email-registration-proof-v1"),
  UTF8("iwut-email-registration-v1"),
  UTF8("REGISTER_WITH_EMAIL"),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65,
  associationDigest32, UTF8(normalizedEmail)
)
```

- challenge32 为服务端生成的 32 随机字节；operationId 为服务端 UUIDv4。expiresAtUnixMs 是 Begin 服务端时间加 UC011 的 10 分钟，以 UTC Unix 毫秒精确保存；`now >= expiresAt` 拒绝。
- serviceId 使用既有 `AUTH_AUTHENTICATION_SERVICE_ID` 及其校验范围，applicationId 固定 `iwut-client`；客户端根据部署配置核对，不能仅信任服务端返回的任意上下文。
- publicKey65 是 Begin 中经过 P-256 曲线校验的完整 65 字节非压缩公钥，不是 PEM、SPKI 或指纹。associationDigest 的算法沿用原协议；邮箱按 UC011 BR-EML-002 规范化，未规范化的用户输入不能用于验签。
- 签名是对完整 payload 做一次 SHA-256 后的 ECDSA P-256，使用既有严格 DER 验证，接受合法 high-S/low-S。不允许双重哈希。服务端根据操作快照重建待签字节；Complete 只带 DER 签名，不能带可覆盖快照的邮箱、公钥、算法或关联声明。
- payload 最多 1024 字节，必须恰好解出 11 个字段；拒绝非法 UTF8、错误域标签/版本/用途、错误长度、尾随字节、额外字段。客户端核对本次操作的邮箱、公钥、关联摘要、随机挑战、operationId、期限和预配上下文后签名。
- 签名没有验证码字段；验证码由同一 operationId 的服务端记录另行校验，两种证明必须同时通过。BIND 分支没有注册签名挑战或设备证明，以该账号有效 Session 和绑定验证码授权。
- 含 associationDigest 的 signingPayload 只在受控内存及必要响应中构造，不进入持久化日志或操作明文；关联快照加密、操作清理和密钥迁移由 UC011/BR-REG-008 定义。

#### RPC 与 Session 鉴权

独立 API 目录 `auth_center/v1/email_binding/`，package `auth_center.v1.email_binding`，service `EmailBindingService`，Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/email_binding;email_binding`。

| full method | Auth 鉴权 |
| --- | --- |
| `/auth_center.v1.email_binding.EmailBindingService/BeginSetEmail` | 无 Session 只接受 registration；有效 Session 只接受 binding；任何已提供但无效的 Session 均拒绝。 |
| `/auth_center.v1.email_binding.EmailBindingService/CompleteSetEmail` | 先检查已提供的 Session；按操作固定模式，REGISTER 必须无 Session 且双证明有效，BIND 必须有同账号当前有效 Session。 |
| `/auth_center.v1.email_binding.EmailBindingService/GetOwnEmailBinding` | 必须有当前有效 ACTIVE USER Session，只读本人一致快照。 |

载体只使用 HTTP/gRPC 的 `x-iwut-session`。**缺失**表示 header/metadata 中根本不存在该键；存在但空、空白、重复、逗号合并或非法编码均为无效，不得当成缺失。提供了合法形状但已失效的 token 同样不得匿名降级。禁止从 cookie、query、Authorization 或 x-iwut-identity 回退恢复用户 Session。

Begin 的输入分支与载体不匹配返回 EMAIL_FLOW_MISMATCH；分支缺失、两个分支并存、未知枚举或结构非法返回 INVALID_EMAIL_REQUEST。Complete 中已提供的无效 Session 优先返回 SESSION_INVALID；有效 Session 用于 REGISTER 返回 EMAIL_FLOW_MISMATCH；缺失 Session 用于 BIND 返回 SESSION_INVALID；有效但属于他人的 Session 访问 BIND 操作统一 EMAIL_VERIFICATION_FAILED。未知 operationId 在已提供 Session 校验后统一 EMAIL_VERIFICATION_FAILED。

精确方法表不得把整个 email_binding package 当作匿名，不把 GetOwn 与 Begin/Complete 共用无条件匿名策略；也不将 Begin/Complete 套进必须有 Session 的 middleware。有效 Session 的主体、凭据及使用时间更新复用现有在线检查，业务提交点仍须在事务内再次确认授权。

#### 消息字段与 presence

以下为设计字段表，可执行 Proto 及生成物由独立 API 仓库交付。`Auth.*` 表示导入既有 `auth_center.v1.authentication` 消息。所有时间字段使用 int64 UTC Unix 毫秒，与既有 Authentication 消息一致；不另用 Timestamp。ProtoJSON int64 响应为字符串，bytes 遵守标准 ProtoJSON Base64。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `BeginSetEmailRequest` | `1: string request_id`；`2: string email`；`oneof intent { 3: BindEmailIntent binding; 4: RegisterEmailIntent registration; }` |
| `BindEmailIntent` | `1: optional int64 expected_revision`，presence 必需，允许显式 0 |
| `RegisterEmailIntent` | `1: Auth.CredentialRegistrationProposal credential_proposal`；`2: Auth.StudentAssociationDeclaration association`；两者必需 |
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

#### HTTP 与 Gateway

| HTTP | Auth 内部路径 | 方法 | 成功状态 |
| --- | --- | --- | --- |
| POST | `/v1/email-bindings` | BeginSetEmail | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | CompleteSetEmail | 200（两分支一致） |
| GET | `/v1/users/me/email-binding` | GetOwnEmailBinding | 200 |

POST 的 Proto annotation 使用 body `"*"`。Complete 的 operation_id 由路径绑定并覆盖体中同名值，body 包含 code 和 REGISTER 所需的 registrationProof，不沿用普通设备 Complete 的“只有 proof”。GET 无 body。禁止 query 作为输入；其余严格 JSON、重复字段/oneof 冲突拒绝、16 KiB 请求上限、不支持压缩、no-store 及错误映射遵守 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md)。

三个接口的 Gateway 策略都是 DIRECT；公共 HTTP 前缀 `/auth-center`，转发前剥离；原生 gRPC full method 不加该前缀，gRPC-Web 沿用既有终止方案。DIRECT 必须保留 Session 键是否出现及多值/非法值，不能清理坏 token 后转成匿名；禁止伪造 x-iwut-identity 代替 Session。不因模式为 REGISTER 就把整个服务对外公开，只开放表中三个精确方法。

HTTP 与 gRPC 的 reason/状态由 UC011 错误表拥有；未知枚举/字段等协议错误统一 INVALID_EMAIL_REQUEST。大小超限为 EMAIL_REQUEST_TOO_LARGE（HTTP 413 / gRPC RESOURCE_EXHAUSTED）。限流返回 EMAIL_RATE_LIMITED，附 `retryAfterSeconds`（metadata 字符串，正整数）及 HTTP Retry-After；网络/存储故障不伪装成输入错误。

#### 公开测试向量

文件 [auth-email-binding-v1.json](../../platform/contracts/test-vectors/auth-email-binding-v1.json)，由 `python3 tools/auth_email_protocol_vectors.py --write` 确定性生成，`--check` 校验漂移、正例和负例。其中私钥、验证码相关示例、挑战与 token 均为公开测试材料，不能进入运行配置。

后端和移动端共同验证邮箱规范化、精确 payload、ECDSA DER、前导零学生关联、用途/邮箱/公钥/关联/服务/应用/操作/期限篡改、旧 REGISTER 证明不能用于邮箱注册、双重哈希和边界时间拒绝。固定 DER 只为互操作样例，生产签名无需逐字相等；验签结果必须一致。原有 `tools/auth_protocol_vectors.py --check` 必须继续通过且原 fixture 不改。

#### 交付状态

契约接受不代表服务已启用。UC011 后端负责 API/生成代码、严格 HTTP/gRPC transport、邮件适配器、持久化与真实 Mongo/Wire 验收；客户端与 Gateway 路由是独立交付，不能仅凭后端通过就声称公网注册可用。

- 2026-09-25：按授权固定邮箱注册协议、消息字段、精确鉴权与 HTTP/Gateway 路由。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-011`（use-cases/UC-AUTH-011-set-and-activate-email.md）：实现约定/事务与存储、实现约定/邮件校验与幂等指纹、实现约定/限额与投递、变更记录
- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：目标与范围、认证与资格、API 与确认过程、主流程、首版运行与协议固定值、错误、限额与验收、实现依赖与联动、变更记录
- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、交付依赖与非目标、参考、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：目标与范围、参与者与前置条件、输入与输出、主流程、持久化候选、异常语义、测试与验收、交付依赖与验收边界、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：路由边界、治理工作包路由
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-011-set-and-activate-email.md` | 279 | `a96eacf40f23` |
| `use-cases/UC-AUTH-025-close-own-account.md` | 155 | `6b6f375f1aad` |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 144 | `b87f14177d5a` |
| `use-cases/UC-AUTH-007-login.md` | 252 | `3afbbd9047ae` |
| `use-cases/UC-AUTH-006-create-user.md` | 279 | `2b56bd4eb59d` |
| `platform/contracts/auth-center-api-routing.md` | 110 | `a2999614c568` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/auth-email-binding-v1.md` | 100 | `bbe1a81c1d9a` |
