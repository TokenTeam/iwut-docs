# UC-AUTH-012：使用邮箱登录

状态：`ACCEPTED`

## 目标与范围

> 用户通过已激活邮箱的验证码进入原平台账号，同时证明对本机设备私钥的控制权，由 Auth 登记或复用该设备凭据并建立 Session。

本用例闭合官方 App 在旧设备不可用时的登录路径。新手机自己生成新设备密钥，不继承旧私钥；用户只需输入邮箱和验证码，设备签名由客户端完成，不额外要求生物识别。后续可以使用 UC007 自动登录。

本用例不注册 USER，不要求重新提交 associationToken，不修改学校关联、邮箱绑定、资料或 Developer 状态。未知邮箱和登录失败均不能自动转成注册；明确创建新账号使用 UC011 的 REGISTER 分支。

首版选择邮件一次性验证码，不引入平台密码。只交付“邮箱验证并授权本机设备”的完整 App 登录流程；不提供缺少设备凭据的邮箱专用 Session，也不在普通 UC007 设备登录接口中开放新增公钥。

## 参与者与前置条件

- 用户已通过 [UC011](UC-AUTH-011-set-and-activate-email.md) 激活邮箱，目标账号为 ACTIVE USER；这两个事实由服务端确认。
- Begin/Complete 不要求已有 Session，身份只来自本次邮箱验证与设备证明。若携带 Session 载体，拒绝该请求，不读取它决定目标账号，也不撤销另一个已登录账号；客户端切换编排独立。
- 客户端持久保管本次设备私钥，可以提交新公钥，或提交本机已有公钥并证明持有对应私钥。客户端不能指定目标 authId。
- 邮箱登录入口、邮件适配器及所需配置已启用。UC011 的绑定能力单独可用不意味着本入口已经可用。

## 输入与输出

```text
BeginEmailLogin {
  requestId: UUID
  email: string
  credentialProposal: CredentialRegistrationProposal
}

EmailLoginChallenge {
  operationId: UUID
  challenge: Bytes
  signingPayload: Bytes
  protocolVersion: string
  expiresAt: Instant
  resendAfter: Instant
}

CompleteEmailLogin {
  operationId: UUID
  code: string
  proof: CredentialAuthenticationProof
}

EmailLoginResult {
  authId: AuthId
  credentialId: UUID
  session: SessionEstablished
}
```

地址规范化引用 [BR-EML-002](UC-AUTH-011-set-and-activate-email.md#br-eml-002)。已有公钥和签名编码引用 [App 设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)；本用例的独立签名上下文、消息字段和 RPC/HTTP 由 [邮箱登录协议 v1](../../platform/contracts/auth-email-login-v1.md) 固定，不能用 REGISTER、REGISTER_WITH_EMAIL 或普通 LOGIN 证明代替。成功结果不附带邮箱、学生资料、权限或关联组信息。

## 主流程

1. 用户明确选择邮箱登录，客户端准备并保存本机设备私钥，提交邮箱和公钥提案。
2. Auth 检查输入、发送限额与容量，生成不可变操作，固定该邮箱此时的账号归属和绑定 revision，或固定为不可登录的占位操作；Begin 不登记公钥。
3. 向格式有效的目标邮箱发送本操作的登录验证码，返回相同形状的挑战。邮件仅说明本次登录验证，不宣称账号存在。
4. 客户端检查签名上下文与自己发起的操作一致，在用户提交验证码时，以本机私钥签署挑战，提交 Complete。
5. Auth 检查验证码、签名、用途、期限和次数，复核目标账号、当前邮箱归属/revision 以及公钥归属与状态。
6. 在同一 Mongo 事务内确认认证事实、登记或复用设备凭据、消费操作、按 UC007 淘汰必要的 LRU Session、创建新 Session 并写入审计。
7. 提交确定成功后返回登录结果；客户端保存 credentialId 和 Session，加载该 authId 的本地数据。

## 业务规则

<a id="br-lgn-013"></a>
### BR-LGN-013：邮箱登录定位与用途隔离

账号归属只能来自 Auth 当前激活邮箱记录。Begin 固定内部 authId、邮箱绑定 revision、是否可登录、公钥提案和服务/应用上下文；不把这些内部账号信息返回给未认证调用者。Begin 时未知、未激活、禁用或非 USER 的目标，在该操作内始终不可登录，即使稍后注册或恢复状态也必须重新 Begin。

Complete 必须确认激活邮箱仍属于原 authId，且 revision 与 Begin 一致。更换邮箱后再换回同一地址也不能复活旧登录操作；地址后来被另一账号绑定时，旧操作不得进入新账号。学生关联、邮箱字符串、本机账号标签和客户端 verified 标志均不是控制权证明。

操作 purpose 固定为 `LOGIN_WITH_EMAIL`，验证码与设备证明绑定同一 operationId。签名覆盖用途、随机挑战、期限、部署/应用上下文、规范化邮箱和规范公钥。验证之前客户端应核对自己的发起意图；Complete 不能更换邮箱、公钥或协议。签名内容不包含未认证调用者不应获知的 authId 或绑定 revision，这些由不可变操作在服务端固定。

<a id="br-lgn-014"></a>
### BR-LGN-014：邮箱验证码与有界投递

验证码采用均匀的 8 位十进制随机字符串，保留前导零；验证码和设备挑战均在 10 分钟后到期，最多累计 5 次错误验证码或设备证明尝试。并发错误计数、次数耗尽和成功消费原子确认。邮箱绑定、注册、登录验证码不可跨用途替代。

校验值使用独立的 `AUTH_EMAIL_LOGIN_CODE_KEY`（标准 Base64 编码的 32 字节随机密钥，ENV 注入）计算 HMAC-SHA-256，输入以 Frame 编码绑定用途、操作、目标邮箱、提案公钥、期限、服务/应用及验证码；不与邮箱绑定验证、学生关联或 JWS 的秘密共用。验证码明文仅用于当次投递，不落库、不进入普通日志，校验采用恒定时间比较。冷更新换钥可以关闭未完成操作，不影响既有设备凭据或 Session；缺失/非法配置拒绝启用邮箱登录。

与 UC011 共用“每目标邮箱”的发送冷却和小时总额度，不能通过切换注册、绑定、登录入口绕过：默认至少间隔 60 秒、每小时最多 5 次。另按公钥指纹每小时最多 5 次、可信来源 IP 每小时最多 20 次；发送失败也计额度，相同幂等请求不重复计数。全局请求和未完成操作容量沿用 [BR-LGN-009](UC-AUTH-007-login.md#br-lgn-009)，细分桶有界；邮件额度用 Mongo 原子持久化，不引入 Redis。

先提交操作，再在事务外投递，不在事务重试中发送。进程在提交后发送前中断可能丢失此次投递，用户冷却后用新 requestId 重发；不承诺可靠异步投递或收件箱送达。格式有效的未知和已存在邮箱均走相同投递流程，因此投递失败不应泄露账号存在性。不得在 Begin 暗示“邮件只在账号存在时才发送”或返回占用信息。

<a id="br-lgn-015"></a>
### BR-LGN-015：邮箱授权下的设备凭据登记

正确邮箱验证码授权将本次已证明私钥持有的设备公钥加入该账号，设备签名证明公钥可用。两者缺一不可；不能先获得普通 Session，再仅靠提交公钥新增凭据。

公钥尚未登记时，在登录事务内生成 credentialId 并绑定原 authId；同一账号下已经有效的规范公钥可复用同一 credentialId，不重复新增。属于其它账号或已经撤销的公钥均不可接受，不能改绑或复活；即使撤销后仍持有私钥，也应生成新密钥重新发起邮箱登录。唯一归属沿用 [BR-REG-003](UC-AUTH-006-create-user.md#br-reg-003)。只有邮箱和设备证明通过后才披露受控的凭据冲突错误，不返回原公钥所属账号。

Begin 时公钥已被撤销或属于其它账号，不能在该操作中转为可接受；Begin 时未登记的公钥若后来由同一账号成功登记，可以复用，但若被撤销或绑定其它账号则失败。并发邮箱登录、一键注册和邮箱注册依靠同一全局公钥唯一约束协调。

新增设备必须经过本用例的邮件额度、一次性验证码和设备证明，不自动淘汰旧设备凭据。UC007 的 10 条上限只统计有效 Session，不解释成设备数量上限；完整设备列表、数量策略和批量清理另立管理用例。

<a id="br-lgn-016"></a>
### BR-LGN-016：邮箱登录 Session 与邮箱更换边界

本次 Session 的 authenticationMethod 明确为 `EMAIL_CODE_AND_DEVICE`，credentialId 必填，并记录登录时邮箱绑定 revision 作为认证来源证据，不保存邮箱明文或验证码。既有 `DEVICE_CREDENTIAL` Session 语义不变。Session token、固定时长、在线检查、10 条上限和 LRU 复用 UC007 的 BR-LGN-003、BR-LGN-004 和 BR-LGN-010；撤销复用 UC008/009。

邮箱登录成功即已授权本机设备，后续 Session 有效性依赖当前主体、Session 与所引用的设备凭据。**后来更换邮箱不撤销已授权设备及其 Session**，认证来源 revision 不是每次在线检查的额外相等条件。更换邮箱只使旧绑定的未完成邮箱登录操作失败；收回已授权设备访问需 UC009 撤销凭据，只退出会话用 UC008。这与普通设备登录保持一致，不能把改邮箱宣称为退出全部设备。

本机后续通过 UC007 自动登录得到 `DEVICE_CREDENTIAL` Session；它与最初邮箱登录 Session 共享同一凭据撤销边界。UC007 的检查器、UC008/009、UC010 签发与所有有效 Session 入口必须明确支持新认证方法并检查 credentialId，未知方法仍拒绝；不能仅改数据库 method 字符串就开放入口。

<a id="br-lgn-017"></a>
### BR-LGN-017：原子登录与结果恢复

成功确认必须与邮箱替换、主体禁用、设备撤销以及其它 Session 创建/淘汰有明确事务顺序，复用 [BR-LGN-007](UC-AUTH-007-login.md#br-lgn-007) 和 [BR-IDN-004](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 的认证一致性边界。先提交更换/撤销时旧操作失败；登录先提交时按 BR-LGN-016 处理既有设备及 Session。只读事务快照不够，必须对邮箱绑定与主体/凭据采用共同事务栅栏或条件写确认。

设备登记、操作消费、Session 淘汰/创建和最小审计一次提交，失败不能留下已登记但没有成功认证结果的半流程。事务自动重试保持候选标识与 Session token 稳定，只有提交确认后才返回秘密。

Begin 幂等键为 `(规范公钥指纹, requestId)`，至少保留 24 小时；邮箱/公钥/协议完全一致才可返回同操作元数据，不重发邮件、不延时。不同参数冲突。重发使用新 requestId，同一规范邮箱与公钥组合最多一个可验证登录操作，新操作作废该组合旧操作，不作废其它设备的挑战。邮箱更换仍可使该账号旧 revision 的全部登录操作失效。

同一成功操作最多创建一个 Session。Complete 重放返回 `LOGIN_ALREADY_COMPLETED`，不再次返回 token 或创建凭据。提交结果未知/响应丢失时保留原私钥，优先通过 UC007 以公钥定位发起设备登录；若设备尚未登记且原操作仍有效，可重试 Complete，否则重新邮箱登录。不自动生成新密钥或创建新账号。完成标记至少保留至操作期限及 24 小时幂等窗口结束；过期或清理后的操作始终失败。

<a id="br-lgn-018"></a>
### BR-LGN-018：邮箱登录隐私与失败关闭

Begin 对未知、已知、禁用邮箱返回相同形状挑战并使用相同邮件模板；不返回 authId、credentialId、Developer 状态、是否已有账号或绑定 revision。Complete 对未知目标、错误证明、过期/失效操作及禁用账号统一认证失败，不提示自动注册。

仅成功认证后输出原账号最小登录结果；真实仓储、密钥或投递故障与普通认证失败区分，以便有界重试。日志和不可变审计仅记录 operationId、认证方法、结果、已确认的 authId/credentialId/sessionId 及服务端时间，不含邮箱、验证码、证明正文、私钥或 Session token。未完成和终态操作在必要保留期后清理。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 请求超过有界大小 | `EMAIL_LOGIN_REQUEST_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 输入、提案、验证码形状非法，或携带不支持的 Session 载体 | `INVALID_EMAIL_LOGIN_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不可登录、验证码/设备证明错误、操作无效 | `EMAIL_LOGIN_FAILED` | 401 / UNAUTHENTICATED |
| 两项证明有效但公钥归属或撤销状态不可接受 | `EMAIL_LOGIN_CREDENTIAL_UNAVAILABLE` | 409 / ALREADY_EXISTS |
| 同一 requestId 的参数不同 | `EMAIL_LOGIN_REQUEST_CONFLICT` | 409 / ALREADY_EXISTS |
| 操作已成功 | `LOGIN_ALREADY_COMPLETED` | 409 / ALREADY_EXISTS |
| 限流或容量耗尽 | `EMAIL_LOGIN_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 邮件投递失败或结果不确定 | `EMAIL_DELIVERY_UNAVAILABLE` | 503 / UNAVAILABLE |
| 配置/仓储不可用或提交结果未知 | `EMAIL_LOGIN_UNAVAILABLE` | 503 / UNAVAILABLE |

## 测试与验收

1. 没有旧设备、没有 Session，仅凭已激活邮箱及本机新设备证明进入原 authId；原资料和关联不变，新设备可通过 UC007 再次登录。
2. 未知/未激活/禁用目标得到同形状 Begin；后来激活不能让旧占位操作有效；失败不创建 USER。
3. 邮箱更换、换回、被其它账号重新绑定均不能让旧挑战进入错误账号；更换与登录并发符合提交顺序。
4. 验证码及设备证明跨操作/用途/邮箱/公钥重放失败；验证码次数和冷却可并发验证且跨重启有效。
5. 同账号公钥复用；其它账号及已撤销公钥拒绝；并发注册和邮箱登录最多一个公钥归属。
6. 设备新增、审计、消费和 Session 创建/淘汰任一步失败全部回滚；并发登录不突破 10 条有效 Session。
7. 成功响应丢失后，用原私钥恢复到同一 authId；Complete 重放不重复发 token，不明文存储 token。
8. EMAIL_CODE_AND_DEVICE 在有效 Session 查询、绑定、更换、UC008/009/010 中均可使用；未知方法拒绝。撤销凭据使相关 Session 失效，改邮箱不隐式撤销既有设备。
9. 发送失败/进程中断可重发，Begin 重试不重复发送；未知和已知地址采用相同对外投递语义，认证正文和邮箱不进日志。

## 实现约定

### 前置基线与复用边界

UC011 必须提供权威邮箱绑定的 authId/activeEmail/revision 查询、现有认证事务中的条件确认、统一邮件发送与持久化额度。本工作包不得复制一个邮箱目录、绕过 UC011 写入或用 fixture 冒充依赖。UC011 未提交稳定基线时，可在独立 worktree 推进协议验证器、API 与领域/端口；Mongo 集成、完整 Wire 验收和最终合入等待其可用提交。

复用 UC011 的邮箱规范化、SMTP 适配器及配置校验，引用 BR-EML-002 和 UC011 的“实现约定”；SMTP 模板追加 LOGIN_WITH_EMAIL 用途，不改变注册/绑定模板。目标邮箱发送冷却、过去 60 分钟滑动额度以及可信来源额度与 UC011 使用同一存储键和事务扣额，不能按 RPC 或用途另开一套使额度翻倍。两边的 requestId 幂等记录分别按用途隔离，不能互相命中。

邮箱登录操作可使用专用 collection，但只能引用同一设备凭据、主体、绑定目录及 Session 仓储。Begin 的可登录性、目标 authId/revision 与凭据归属快照取自一致读取；Complete 加入认证事务栅栏后重新检查，操作消费、设备新增/复用、Session LRU 和审计一次提交。设备协议保存 iwut-device-v1，不能误存为邮箱待签协议。

新增 Session 字段 emailBindingRevision（正 int64）只记录认证来源；EMAIL_CODE_AND_DEVICE 缺少该字段/有效 credentialId 或记录损坏时失败关闭。旧 DEVICE_CREDENTIAL 记录无需迁移；未知方法拒绝。更新所有消费路径及有效 Session/LRU 统计条件，不允许部分入口可用、其它入口报登录失效。当前邮箱 revision 后来变化不使既有设备 Session 失效，遵守 BR-LGN-016。

### 邮件密钥与操作指纹

K_login 由 AUTH_EMAIL_LOGIN_CODE_KEY 注入，独立于 UC011 邮件 HMAC、关联加密/查找和其它用途；共享 SMTP 不共享校验密钥。定义：

```text
requestMac = HMAC-SHA256(K_login, Frame(
  UTF8("iwut-email-login-request-v1"), UTF8(requestId), UTF8(normalizedEmail),
  UTF8(serviceId), UTF8("iwut-client"), UTF8(credentialProtocolVersion), publicKey65))
codeMac = HMAC-SHA256(K_login, Frame(
  UTF8("iwut-email-login-code-v1"), UTF8("LOGIN_WITH_EMAIL"), UTF8(operationId),
  U64BE(expiresAtUnixMs), requestMac, UTF8(code8)))
keyId = SHA256(Frame(UTF8("iwut-email-login-key-id-v1"), K_login))
```

保存 requestMac/codeMac/keyId，不保存明文验证码。操作快照内的邮箱、authId/revision/可登录性仅供 Auth 使用，不投影到 Begin 响应或日志。同键 Begin 先比较请求指纹；参数不符冲突，完成操作返回 LOGIN_ALREADY_COMPLETED，仍有效操作返回原挑战，不重发信。失效/过期/被替代操作返回 EMAIL_LOGIN_FAILED，不重新复活或延长时限。

冷更新 keyId 变化使旧 keyId 未完成操作关闭；完成标记保留至其去重窗口结束，不返回已建立 Session 秘密。已完成操作可返回 LOGIN_ALREADY_COMPLETED，其它旧 keyId 操作统一失败，不因无法比较旧请求 HMAC 就创建同键新操作。无需保存旧 K_login；同密钥日常重启保留未过期操作。邮箱登录不保存学号关联快照，也不受关联密钥轮换而额外作废，除非其邮箱或设备事实已失效。

### 启用与故障

AUTH_EMAIL_LOGIN_ENABLED 默认 false，独立于 AUTH_EMAIL_BINDING_ENABLED。启用要求 AUTH_USER_ENDPOINTS_ENABLED=true、K_login 与共用 SMTP 配置合法、UC011 的目录/额度 schema 可用；SMTP 参数、TLS 模式及超时沿用 UC011，不重复新增一套连接配置。只启用邮箱登录时无需启用绑定路由或加载绑定 HMAC，组合根应按启用功能装配共用能力。关闭时不注册两个 HTTP 路由，两个 gRPC 方法返回 UNIMPLEMENTED，不落入其它鉴权分支。

启动检查参数和 schema，不向真实邮箱发健康检查信。未知、已知和禁用目标都走同样的固定登录邮件投递路径、限额和错误；Begin 的成功只代表请求已接受/发信调用已完成，不证明送达。投递失败计发送额度，幂等重试不重发；用户冷却后用新 requestId 重发。仓储故障与账号不存在必须区分，不能在读取异常时创建“未知用户”占位操作掩盖故障。

对错误证明使用同一尝试计数；所有失败分支仍受全局/来源请求限流。实际 SMTP、日志与错误清洗沿用 UC011；审计与登录提交失败均不得返回候选 token。测试仅使用隔离 TLS SMTP 接收端，不向真实用户发信。

## 交付依赖

- 依赖 UC011 激活邮箱及 revision/唯一归属、UC006 凭据存储和 UC007 Session；UC011 与本 UC 均已接受；后端基线、合入与测试进度见 [实现记录](../implements/README.md)，设计接受不等于生产启用。
- [邮箱登录协议 v1](../../platform/contracts/auth-email-login-v1.md) 已固定 LOGIN_WITH_EMAIL 编码、字段、RPC/HTTP 和载体；公开向量由 tools/auth_email_login_vectors.py 生成/校验。
- 交付新认证方法的 Session 读取/检查/撤销/JWS 签发兼容、邮箱绑定事务栅栏、真实 Mongo 和真实 transport 验收，以及邮件适配器与客户端新设备流程。
- Gateway 的 Begin/Complete 走 DIRECT 匿名认证入口，仅开放明确方法；不要求已有 Session，也不使用 SESSION-to-JWS 作为前置。
- 这次由邮箱验证码明确授权新增本机设备；其它方式的设备管理、旧设备迁移和单独的纯邮箱 Session 不在范围内。

## 变更记录

- 2026-09-24：提出邮箱验证码登录草案，同时授权登记/复用本机设备凭据，闭合无旧设备恢复、Session 兼容及邮箱更换边界。

- 2026-09-25：闭合签名字节、公开正反向量、API/路由及 Session 兼容，接受设计并生成 brief；UC011 稳定实现仍为集成前置，允许隔离推进独立工作。
