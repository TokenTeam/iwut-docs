<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-012 --spec tools/brief-specs/UC-AUTH-012.json -->
# Brief — UC-AUTH-012：使用邮箱登录

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-012` 使用邮箱登录 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-LGN-013`–`BR-LGN-018`（6 条） |
| 外部引用 BR | `BR-ACC-012`，`BR-EML-002`，`BR-IDN-004`，`BR-LGN-003`、`BR-LGN-004`、`BR-LGN-007`、`BR-LGN-009`、`BR-LGN-010`，`BR-REG-003`（来自 `UC-AUTH-006`、`UC-AUTH-007`、`UC-AUTH-010`、`UC-AUTH-011`、`UC-AUTH-025`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-email-login-v1.md` |

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

> 用户通过已激活邮箱的验证码进入原平台账号，同时证明对本机设备私钥的控制权，由 Auth 登记或复用该设备凭据并建立 Session。

本用例闭合官方 App 在旧设备不可用时的登录路径。新手机自己生成新设备密钥，不继承旧私钥；用户只需输入邮箱和验证码，设备签名由客户端完成，不额外要求生物识别。后续可以使用 UC007 自动登录。

本用例不注册 USER，不要求重新提交 associationToken，不修改学校关联、邮箱绑定、资料或 Developer 状态。未知邮箱和登录失败均不能自动转成注册；明确创建新账号使用 UC011 的 REGISTER 分支。

首版选择邮件一次性验证码，不引入平台密码。只交付“邮箱验证并授权本机设备”的完整 App 登录流程；不提供缺少设备凭据的邮箱专用 Session，也不在普通 UC007 设备登录接口中开放新增公钥。

### 参与者与前置条件

- 用户已通过 [UC011](../use-cases/UC-AUTH-011-set-and-activate-email.md) 激活邮箱，目标账号为 ACTIVE USER；这两个事实由服务端确认。
- Begin/Complete 不要求已有 Session，身份只来自本次邮箱验证与设备证明。若携带 Session 载体，拒绝该请求，不读取它决定目标账号，也不撤销另一个已登录账号；客户端切换编排独立。
- 客户端持久保管本次设备私钥，可以提交新公钥，或提交本机已有公钥并证明持有对应私钥。客户端不能指定目标 authId。
- 邮箱登录入口、邮件适配器及所需配置已启用。UC011 的绑定能力单独可用不意味着本入口已经可用。

### 输入与输出

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

地址规范化引用 [BR-EML-002](../use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-002)。已有公钥和签名编码引用 [App 设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)；本用例的独立签名上下文、消息字段和 RPC/HTTP 由 [邮箱登录协议 v1](../../platform/contracts/auth-email-login-v1.md) 固定，不能用 REGISTER、REGISTER_WITH_EMAIL 或普通 LOGIN 证明代替。成功结果不附带邮箱、学生资料、权限或关联组信息。

### 主流程

1. 用户明确选择邮箱登录，客户端准备并保存本机设备私钥，提交邮箱和公钥提案。
2. Auth 检查输入、发送限额与容量，生成不可变操作，固定该邮箱此时的账号归属和绑定 revision，或固定为不可登录的占位操作；Begin 不登记公钥。
3. 向格式有效的目标邮箱发送本操作的登录验证码，返回相同形状的挑战。邮件仅说明本次登录验证，不宣称账号存在。
4. 客户端检查签名上下文与自己发起的操作一致，在用户提交验证码时，以本机私钥签署挑战，提交 Complete。
5. Auth 检查验证码、签名、用途、期限和次数，复核目标账号、当前邮箱归属/revision 以及公钥归属与状态。
6. 在同一 Mongo 事务内确认认证事实、登记或复用设备凭据、消费操作、按 UC007 淘汰必要的 LRU Session、创建新 Session 并写入审计。
7. 提交确定成功后返回登录结果；客户端保存 credentialId 和 Session，加载该 authId 的本地数据。

### 错误语义

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

### 测试与验收

1. 没有旧设备、没有 Session，仅凭已激活邮箱及本机新设备证明进入原 authId；原资料和关联不变，新设备可通过 UC007 再次登录。
2. 未知/未激活/禁用目标得到同形状 Begin；后来激活不能让旧占位操作有效；失败不创建 USER。
3. 邮箱更换、换回、被其它账号重新绑定均不能让旧挑战进入错误账号；更换与登录并发符合提交顺序。
4. 验证码及设备证明跨操作/用途/邮箱/公钥重放失败；验证码次数和冷却可并发验证且跨重启有效。
5. 同账号公钥复用；其它账号及已撤销公钥拒绝；并发注册和邮箱登录最多一个公钥归属。
6. 设备新增、审计、消费和 Session 创建/淘汰任一步失败全部回滚；并发登录不突破 10 条有效 Session。
7. 成功响应丢失后，用原私钥恢复到同一 authId；Complete 重放不重复发 token，不明文存储 token。
8. EMAIL_CODE_AND_DEVICE 在有效 Session 查询、绑定、更换、UC008/009/010 中均可使用；未知方法拒绝。撤销凭据使相关 Session 失效，改邮箱不隐式撤销既有设备。
9. 发送失败/进程中断可重发，Begin 重试不重复发送；未知和已知地址采用相同对外投递语义，认证正文和邮箱不进日志。

### 实现约定

#### 前置基线与复用边界

UC011 必须提供权威邮箱绑定的 authId/activeEmail/revision 查询、现有认证事务中的条件确认、统一邮件发送与持久化额度。本工作包不得复制一个邮箱目录、绕过 UC011 写入或用 fixture 冒充依赖。UC011 未提交稳定基线时，可在独立 worktree 推进协议验证器、API 与领域/端口；Mongo 集成、完整 Wire 验收和最终合入等待其可用提交。

复用 UC011 的邮箱规范化、SMTP 适配器及配置校验，引用 BR-EML-002 和 UC011 的“实现约定”；SMTP 模板追加 LOGIN_WITH_EMAIL 用途，不改变注册/绑定模板。目标邮箱发送冷却、过去 60 分钟滑动额度以及可信来源额度与 UC011 使用同一存储键和事务扣额，不能按 RPC 或用途另开一套使额度翻倍。两边的 requestId 幂等记录分别按用途隔离，不能互相命中。

邮箱登录操作可使用专用 collection，但只能引用同一设备凭据、主体、绑定目录及 Session 仓储。Begin 的可登录性、目标 authId/revision 与凭据归属快照取自一致读取；Complete 加入认证事务栅栏后重新检查，操作消费、设备新增/复用、Session LRU 和审计一次提交。设备协议保存 iwut-device-v1，不能误存为邮箱待签协议。

新增 Session 字段 emailBindingRevision（正 int64）只记录认证来源；EMAIL_CODE_AND_DEVICE 缺少该字段/有效 credentialId 或记录损坏时失败关闭。旧 DEVICE_CREDENTIAL 记录无需迁移；未知方法拒绝。更新所有消费路径及有效 Session/LRU 统计条件，不允许部分入口可用、其它入口报登录失效。当前邮箱 revision 后来变化不使既有设备 Session 失效，遵守 BR-LGN-016。

#### 邮件密钥与操作指纹

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

#### 启用与故障

AUTH_EMAIL_LOGIN_ENABLED 默认 false，独立于 AUTH_EMAIL_BINDING_ENABLED。启用要求 AUTH_USER_ENDPOINTS_ENABLED=true、K_login 与共用 SMTP 配置合法、UC011 的目录/额度 schema 可用；SMTP 参数、TLS 模式及超时沿用 UC011，不重复新增一套连接配置。只启用邮箱登录时无需启用绑定路由或加载绑定 HMAC，组合根应按启用功能装配共用能力。关闭时不注册两个 HTTP 路由，两个 gRPC 方法返回 UNIMPLEMENTED，不落入其它鉴权分支。

启动检查参数和 schema，不向真实邮箱发健康检查信。未知、已知和禁用目标都走同样的固定登录邮件投递路径、限额和错误；Begin 的成功只代表请求已接受/发信调用已完成，不证明送达。投递失败计发送额度，幂等重试不重发；用户冷却后用新 requestId 重发。仓储故障与账号不存在必须区分，不能在读取异常时创建“未知用户”占位操作掩盖故障。

对错误证明使用同一尝试计数；所有失败分支仍受全局/来源请求限流。实际 SMTP、日志与错误清洗沿用 UC011；审计与登录提交失败均不得返回候选 token。测试仅使用隔离 TLS SMTP 接收端，不向真实用户发信。

### 交付依赖

- 依赖 UC011 激活邮箱及 revision/唯一归属、UC006 凭据存储和 UC007 Session；UC011 与本 UC 均已接受；后端基线、合入与测试进度见 [实现记录](../implements/README.md)，设计接受不等于生产启用。
- [邮箱登录协议 v1](../../platform/contracts/auth-email-login-v1.md) 已固定 LOGIN_WITH_EMAIL 编码、字段、RPC/HTTP 和载体；公开向量由 tools/auth_email_login_vectors.py 生成/校验。
- 交付新认证方法的 Session 读取/检查/撤销/JWS 签发兼容、邮箱绑定事务栅栏、真实 Mongo 和真实 transport 验收，以及邮件适配器与客户端新设备流程。
- Gateway 的 Begin/Complete 走 DIRECT 匿名认证入口，仅开放明确方法；不要求已有 Session，也不使用 SESSION-to-JWS 作为前置。
- 这次由邮箱验证码明确授权新增本机设备；其它方式的设备管理、旧设备迁移和单独的纯邮箱 Session 不在范围内。

## 业务规则（UC-AUTH-012 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-013 -->
### BR-LGN-013：邮箱登录定位与用途隔离

账号归属只能来自 Auth 当前激活邮箱记录。Begin 固定内部 authId、邮箱绑定 revision、是否可登录、公钥提案和服务/应用上下文；不把这些内部账号信息返回给未认证调用者。Begin 时未知、未激活、禁用或非 USER 的目标，在该操作内始终不可登录，即使稍后注册或恢复状态也必须重新 Begin。

Complete 必须确认激活邮箱仍属于原 authId，且 revision 与 Begin 一致。更换邮箱后再换回同一地址也不能复活旧登录操作；地址后来被另一账号绑定时，旧操作不得进入新账号。学生关联、邮箱字符串、本机账号标签和客户端 verified 标志均不是控制权证明。

操作 purpose 固定为 `LOGIN_WITH_EMAIL`，验证码与设备证明绑定同一 operationId。签名覆盖用途、随机挑战、期限、部署/应用上下文、规范化邮箱和规范公钥。验证之前客户端应核对自己的发起意图；Complete 不能更换邮箱、公钥或协议。签名内容不包含未认证调用者不应获知的 authId 或绑定 revision，这些由不可变操作在服务端固定。

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-014 -->
### BR-LGN-014：邮箱验证码与有界投递

验证码采用均匀的 8 位十进制随机字符串，保留前导零；验证码和设备挑战均在 10 分钟后到期，最多累计 5 次错误验证码或设备证明尝试。并发错误计数、次数耗尽和成功消费原子确认。邮箱绑定、注册、登录验证码不可跨用途替代。

校验值使用独立的 `AUTH_EMAIL_LOGIN_CODE_KEY`（标准 Base64 编码的 32 字节随机密钥，ENV 注入）计算 HMAC-SHA-256，输入以 Frame 编码绑定用途、操作、目标邮箱、提案公钥、期限、服务/应用及验证码；不与邮箱绑定验证、学生关联或 JWS 的秘密共用。验证码明文仅用于当次投递，不落库、不进入普通日志，校验采用恒定时间比较。冷更新换钥可以关闭未完成操作，不影响既有设备凭据或 Session；缺失/非法配置拒绝启用邮箱登录。

与 UC011 共用“每目标邮箱”的发送冷却和小时总额度，不能通过切换注册、绑定、登录入口绕过：默认至少间隔 60 秒、每小时最多 5 次。另按公钥指纹每小时最多 5 次、可信来源 IP 每小时最多 20 次；发送失败也计额度，相同幂等请求不重复计数。全局请求和未完成操作容量沿用 [BR-LGN-009](../use-cases/UC-AUTH-007-login.md#br-lgn-009)，细分桶有界；邮件额度用 Mongo 原子持久化，不引入 Redis。

先提交操作，再在事务外投递，不在事务重试中发送。进程在提交后发送前中断可能丢失此次投递，用户冷却后用新 requestId 重发；不承诺可靠异步投递或收件箱送达。格式有效的未知和已存在邮箱均走相同投递流程，因此投递失败不应泄露账号存在性。不得在 Begin 暗示“邮件只在账号存在时才发送”或返回占用信息。

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-015 -->
### BR-LGN-015：邮箱授权下的设备凭据登记

正确邮箱验证码授权将本次已证明私钥持有的设备公钥加入该账号，设备签名证明公钥可用。两者缺一不可；不能先获得普通 Session，再仅靠提交公钥新增凭据。

公钥尚未登记时，在登录事务内生成 credentialId 并绑定原 authId；同一账号下已经有效的规范公钥可复用同一 credentialId，不重复新增。属于其它账号或已经撤销的公钥均不可接受，不能改绑或复活；即使撤销后仍持有私钥，也应生成新密钥重新发起邮箱登录。唯一归属沿用 [BR-REG-003](../use-cases/UC-AUTH-006-create-user.md#br-reg-003)。只有邮箱和设备证明通过后才披露受控的凭据冲突错误，不返回原公钥所属账号。

Begin 时公钥已被撤销或属于其它账号，不能在该操作中转为可接受；Begin 时未登记的公钥若后来由同一账号成功登记，可以复用，但若被撤销或绑定其它账号则失败。并发邮箱登录、一键注册和邮箱注册依靠同一全局公钥唯一约束协调。

新增设备必须经过本用例的邮件额度、一次性验证码和设备证明，不自动淘汰旧设备凭据。UC007 的 10 条上限只统计有效 Session，不解释成设备数量上限；完整设备列表、数量策略和批量清理另立管理用例。

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-016 -->
### BR-LGN-016：邮箱登录 Session 与邮箱更换边界

本次 Session 的 authenticationMethod 明确为 `EMAIL_CODE_AND_DEVICE`，credentialId 必填，并记录登录时邮箱绑定 revision 作为认证来源证据，不保存邮箱明文或验证码。既有 `DEVICE_CREDENTIAL` Session 语义不变。Session token、固定时长、在线检查、10 条上限和 LRU 复用 UC007 的 BR-LGN-003、BR-LGN-004 和 BR-LGN-010；撤销复用 UC008/009。

邮箱登录成功即已授权本机设备，后续 Session 有效性依赖当前主体、Session 与所引用的设备凭据。**后来更换邮箱不撤销已授权设备及其 Session**，认证来源 revision 不是每次在线检查的额外相等条件。更换邮箱只使旧绑定的未完成邮箱登录操作失败；收回已授权设备访问需 UC009 撤销凭据，只退出会话用 UC008。这与普通设备登录保持一致，不能把改邮箱宣称为退出全部设备。

本机后续通过 UC007 自动登录得到 `DEVICE_CREDENTIAL` Session；它与最初邮箱登录 Session 共享同一凭据撤销边界。UC007 的检查器、UC008/009、UC010 签发与所有有效 Session 入口必须明确支持新认证方法并检查 credentialId，未知方法仍拒绝；不能仅改数据库 method 字符串就开放入口。

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-017 -->
### BR-LGN-017：原子登录与结果恢复

成功确认必须与邮箱替换、主体禁用、设备撤销以及其它 Session 创建/淘汰有明确事务顺序，复用 [BR-LGN-007](../use-cases/UC-AUTH-007-login.md#br-lgn-007) 和 [BR-IDN-004](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004) 的认证一致性边界。先提交更换/撤销时旧操作失败；登录先提交时按 BR-LGN-016 处理既有设备及 Session。只读事务快照不够，必须对邮箱绑定与主体/凭据采用共同事务栅栏或条件写确认。

设备登记、操作消费、Session 淘汰/创建和最小审计一次提交，失败不能留下已登记但没有成功认证结果的半流程。事务自动重试保持候选标识与 Session token 稳定，只有提交确认后才返回秘密。

Begin 幂等键为 `(规范公钥指纹, requestId)`，至少保留 24 小时；邮箱/公钥/协议完全一致才可返回同操作元数据，不重发邮件、不延时。不同参数冲突。重发使用新 requestId，同一规范邮箱与公钥组合最多一个可验证登录操作，新操作作废该组合旧操作，不作废其它设备的挑战。邮箱更换仍可使该账号旧 revision 的全部登录操作失效。

同一成功操作最多创建一个 Session。Complete 重放返回 `LOGIN_ALREADY_COMPLETED`，不再次返回 token 或创建凭据。提交结果未知/响应丢失时保留原私钥，优先通过 UC007 以公钥定位发起设备登录；若设备尚未登记且原操作仍有效，可重试 Complete，否则重新邮箱登录。不自动生成新密钥或创建新账号。完成标记至少保留至操作期限及 24 小时幂等窗口结束；过期或清理后的操作始终失败。

<!-- 权威位置: use-cases/UC-AUTH-012-login-with-email.md#br-lgn-018 -->
### BR-LGN-018：邮箱登录隐私与失败关闭

Begin 对未知、已知、禁用邮箱返回相同形状挑战并使用相同邮件模板；不返回 authId、credentialId、Developer 状态、是否已有账号或绑定 revision。Complete 对未知目标、错误证明、过期/失效操作及禁用账号统一认证失败，不提示自动注册。

仅成功认证后输出原账号最小登录结果；真实仓储、密钥或投递故障与普通认证失败区分，以便有界重试。日志和不可变审计仅记录 operationId、认证方法、结果、已确认的 authId/credentialId/sessionId 及服务端时间，不含邮箱、验证码、证明正文、私钥或 Session token。未完成和终态操作在必要保留期后清理。

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

首次管理员的全局 bootstrap 消费事实永久保留；其原事件到期删除时按 [管理员初始化规则](../use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-005) 在同一认证事务写 auditRetiredAt 收据，防止清理后所有管理员操作因审计缺失被拒绝。此全局控制记录不属于账号资料墓碑。

现有审计的 append-only 表示保留期内不可更新/删除；接受本 UC 时需要明确增加受控保留期清理例外，不能由普通业务账号任意删除审计。永久墓碑的字段就是允许保留的完整集合，不能附加整份 principal 或自由文本快照。

### 来自 `UC-AUTH-011`

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-002 -->
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

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

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-007 -->
### BR-LGN-007：原子登录与重试

消费挑战、最后复核账号/凭据状态、必要的 LRU 淘汰和创建 Session 必须作为一个原子业务提交，不能先消费挑战或撤销旧会话，再在非原子步骤中写新会话。Mongo 实现使用事务；只有读取快照不足以排除并发禁用/撤销的写偏差，必须对参与认证的主体与凭据做条件更新/版本栅栏等可串行化确认，并保证同一账号并发创建不会突破 BR-LGN-010 的容量约束。实现工作包需给出具体字段、锁定顺序和真实并发测试，不能只在代码注释声称原子。

当禁用/凭据撤销先完成时登录失败；登录先完成则可以建立会话，后续检查仍受 BR-LGN-004 控制。事务回滚不留下已消费成功状态或可用 Session；服务端事务自动重试使用固定的候选 sessionId/token。

成功证明不可重放领取更多 Session。相同操作已成功时返回 LOGIN_ALREADY_COMPLETED，不重发原 token、不生成第二个 token。响应丢失时客户端保留原凭据，重新发起挑战建立新 Session；可能遗留的未取得令牌会话按寿命/限额规则处理。不能把“已完成”当作客户端已经登录，也不能明文保存 token 以支持重放。

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

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-003 -->
### BR-REG-003：设备凭据持有证明与唯一归属

Auth 只接受已发布、受支持协议的注册证明，校验公钥/算法及证明的绑定关系，并确认调用者持有对应私钥。协议级挑战约束见 BR-LGN-002。客户端“设备验证成功”布尔值不是服务器认证证据；本轮不声称已证明设备未被修改或完成学生真实性验证。

首次注册保留显式创建平台账号和提交关联声明的确认，不要求额外的生物识别或每次签名确认；后续设备登录的服务端证明与触发边界引用 [BR-LGN-011](../use-cases/UC-AUTH-007-login.md#br-lgn-011)，客户端自动登录和本地清理建议见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。具体凭据协议须满足该产品目标，不能把 App 自管设备密钥称作或实现成标准 Passkey。

凭据的稳定标识与归一化公钥指纹由服务端/受信协议适配器确定。首版一个凭据只属于一个 authId，禁止将已有凭据改绑另一个账号；客户端不能通过不同编码、换 credentialId 或新注册 operation 绕过公钥唯一性。具体规范化由凭据协议规定。

同一公钥已注册时，不创建第二个主体，也不直接发放已有主体的 Session；引导使用 UC-AUTH-007 完成新的登录证明。不能复用已消费的注册证明作为登录证明。撤销记录不立即释放公钥唯一归属，注销后的保留/清理另行设计。

一个 authId 可以拥有多条独立 credential 记录，每条保存 credentialId、公钥、协议及状态；服务端不保存私钥。首版每台新设备或每次失去原安全存储后的独立安装都生成新密钥，并在邮箱登录、旧设备授权或其他恢复方式确认同一 authId 后新增一条 credential；不复制、导出或下载旧私钥。服务端凭据撤销由 [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 定义，本机私钥删除与退出编排见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)；只撤销当前 Session 是 [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) 的独立能力。新增凭据和凭据列表仍由后续管理用例授权，当前匿名注册入口不能向既有 authId 添加凭据。

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

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/auth-email-login-v1.md`：邮箱登录协议 v1

#### 范围与兼容性

本契约固定 [UC012](../use-cases/UC-AUTH-012-login-with-email.md) 的客户端、Auth 和 Gateway 协议。它授权邮箱持有人登录原账号并登记/复用本机设备，不是注册协议，也不增加邮箱字符串到 JWS 的投影。

Frame、UTF8、U64BE、规范 UUID、公钥及 DER 签名编码引用 [设备协议](../../platform/contracts/auth-device-session-v1.md)。credentialProposal.protocol_version 仍为 `iwut-device-v1`，供后续 UC007 使用；本次 challenge.protocol_version 独立为 `iwut-email-login-v1`。旧 REGISTER/LOGIN 和 [邮箱注册协议](../../platform/contracts/auth-email-binding-v1.md) 的格式与向量均不变。

#### 邮箱登录签名字节

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

#### RPC 与认证载体

API 目录 `auth_center/v1/email_login/`；package `auth_center.v1.email_login`；service `EmailLoginService`；Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/email_login;email_login`。

| full method | 认证 |
| --- | --- |
| `/auth_center.v1.email_login.EmailLoginService/BeginEmailLogin` | 有界匿名；无 Session，仅创建不可变邮箱/设备提案和验证码挑战。 |
| `/auth_center.v1.email_login.EmailLoginService/CompleteEmailLogin` | 有界匿名；验证同一操作的邮箱验证码及设备签名，再确认当前账号/邮箱/凭据。 |

这两个方法要求 `x-iwut-session` 键完全缺失；只要键存在，无论有效、过期、空值或多值，均返回 INVALID_EMAIL_LOGIN_REQUEST，不检查它选择目标账号，也不删除旧账号 Session。不得由 Gateway 清理后转成合法匿名调用。Authorization、cookie 或 x-iwut-identity 不作为替代身份来源；精确方法表只开放上述方法，未知方法仍默认拒绝。

#### 消息字段

`Auth.*` 复用 `auth_center.v1.authentication` 消息。以下为设计字段表，不是本仓库的可执行 Proto；独立 API 仓库生成实现。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `BeginEmailLoginRequest` | `1: string request_id`；`2: string email`；`3: Auth.CredentialRegistrationProposal credential_proposal` |
| `EmailLoginChallenge` | `1: string operation_id`；`2: bytes challenge`；`3: bytes signing_payload`；`4: string protocol_version`；`5: int64 expires_at_unix_ms`；`6: int64 resend_after_unix_ms` |
| `CompleteEmailLoginRequest` | `1: string operation_id`；`2: string code`；`3: Auth.CredentialProof proof` |
| `EmailLoginResult` | `1: string auth_id`；`2: string credential_id`；`3: Auth.SessionEstablished session` |

requestId/operationId 使用小写规范 UUIDv4；code 恰好 8 个 ASCII 数字，保留前导零，不 trim。credentialProposal 和 proof presence 必需，JSON null 不满足必需项；未知/重复字段和畸形公钥/签名编码拒绝。请求不含 authId、revision、角色、关联声明或可信校验标志。时间为 int64 UTC Unix 毫秒；ProtoJSON int64 响应为字符串，bytes 遵守标准 Base64。

成功时 auth_id、credential_id 与内嵌 Session 必须一致；认证方法及邮箱绑定 revision 是服务端内部事实，不新增客户端可以指定的 Session 字段。错误不返回部分成功结果或候选 token。

#### HTTP 与 Gateway

| HTTP | Auth 内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

Proto annotation 的 body 为 `"*"`。Complete 路径 operation_id 覆盖消息体同名值，body 提交 code 和 proof。公共 HTTP 前缀 `/auth-center` 转发前剥离；原生 gRPC full method 不加前缀，gRPC-Web 沿用既有终止方案。

禁止 query 作为消息输入；继承 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md) 的严格 JSON、默认 16 KiB 请求上限、415 压缩/内容类型拒绝和 Cache-Control: no-store。DIRECT 不是跳过证明验证；不执行 SESSION-to-JWS，也不清除非法 Session 载体以绕过拒绝。

reason/HTTP/gRPC 状态遵守 UC012。超大消息使用 EMAIL_LOGIN_REQUEST_TOO_LARGE（413 / RESOURCE_EXHAUSTED）；限流带正整数秒的 retryAfterSeconds 错误 metadata 和 HTTP Retry-After。已完成操作返回 LOGIN_ALREADY_COMPLETED，不重发 Session token。

#### Session 兼容边界

邮箱登录产生的 Session authenticationMethod 为 EMAIL_CODE_AND_DEVICE，credentialId 必填，保存正整数 emailBindingRevision 作为认证来源记录。UC007 的 DEVICE_CREDENTIAL Session 保持原状；EMAIL_CODE_AND_DEVICE 的在线有效性依旧检查当前主体、设备凭据和 Session，不要求来源 revision 等于当前邮箱 revision。

部署必须在开放邮箱登录前完成所有 Session 使用入口对该方法的兼容，包括 UC008/009/010、UC011 BIND/查询和后续需要有效 Session 的命令；未知 authenticationMethod 一律拒绝。不增加下游服务需要识别的 JWS claim，Gateway 与 App Center 仍接收原来的可信用户身份。

#### 公开测试向量

[auth-email-login-v1.json](../../platform/contracts/test-vectors/auth-email-login-v1.json) 由 `python3 tools/auth_email_login_vectors.py --write` 生成，`--check` 校验。全部密钥、地址、挑战为公开测试数据；生产不得使用。

向量覆盖精确字节、邮箱规范化、公钥/用途/邮箱/服务/应用/操作/期限篡改、Frame 和 DER 拒绝、双重哈希、旧 LOGIN 与邮箱 REGISTER_WITH_EMAIL 的双向证明隔离，以及 now == expiresAt 的拒绝。固定签名字节不要求生产逐字复现，只要求相同输入验证通过。

旧 `tools/auth_protocol_vectors.py --check` 及 `tools/auth_email_protocol_vectors.py --check` 必须继续通过；本用例不修改旧 fixture。服务端存储 HMAC、事务和审计约定由 UC012 自身定义。

#### 交付依赖

协议接受不等于 UC011 实现已完成。UC012 依赖其激活邮箱目录、统一邮件额度、真实邮件适配器及认证事务设施；缺少稳定 UC011 基线时，可在隔离 worktree 实现协议/领域层，但不能用 fixture 或另一个邮箱目录代替该依赖，也不能标记整项实现完成。

- 2026-09-25：固定邮箱登录签名、字段、精确 RPC/HTTP 与 Session 兼容契约；保持其它认证协议兼容。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-012`（use-cases/UC-AUTH-012-login-with-email.md）：实现约定/前置基线与复用边界、实现约定/邮件密钥与操作指纹、实现约定/启用与故障、变更记录
- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：目标与范围、认证与资格、API 与确认过程、主流程、首版运行与协议固定值、错误、限额与验收、实现依赖与联动、变更记录
- `UC-AUTH-011`（use-cases/UC-AUTH-011-set-and-activate-email.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、实现约定、交付依赖与边界、变更记录
- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、交付依赖与非目标、参考、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：目标与范围、参与者与前置条件、输入与输出、主流程、持久化候选、异常语义、测试与验收、交付依赖与验收边界、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：路由边界、治理工作包路由
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-012-login-with-email.md` | 203 | `59f3bf32fa60` |
| `use-cases/UC-AUTH-025-close-own-account.md` | 157 | `2812fce31705` |
| `use-cases/UC-AUTH-011-set-and-activate-email.md` | 279 | `a96eacf40f23` |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 144 | `b87f14177d5a` |
| `use-cases/UC-AUTH-007-login.md` | 252 | `3afbbd9047ae` |
| `use-cases/UC-AUTH-006-create-user.md` | 279 | `2b56bd4eb59d` |
| `platform/contracts/auth-center-api-routing.md` | 110 | `a2999614c568` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/auth-email-login-v1.md` | 88 | `ef2417d3b9e4` |
