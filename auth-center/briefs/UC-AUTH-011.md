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
| 外部引用 BR | `BR-ACC-012`，`BR-IDN-004`，`BR-LGN-003`、`BR-LGN-009`，`BR-PWD-003`、`BR-PWD-004`，`BR-REG-006`–`BR-REG-008`（3 条）（来自 `UC-AUTH-006`、`UC-AUTH-007`、`UC-AUTH-010`、`UC-AUTH-025`、`UC-AUTH-033`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-email-account-v3.md` |

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

> 用户注册时验证邮箱并设置平台密码；已有账号管理已验证邮箱列表，其中始终恰好一个地址承担登录/密码恢复角色，切换该角色必须验证当前密码。

2026-10-12 密码、邮箱列表/唯一登录角色及校园解绑是实质修订，本 UC 回到 DRAFT 待重新审核，不能因旧版本 ACCEPTED 自动开工。[UC006](../use-cases/UC-AUTH-006-create-user.md)拥有初始化，原“一键注册”/无邮箱入口不恢复。客户端优先推荐 `@whut.edu.cn`，普通邮箱同样可注册；学校账号不是前提。

邮箱注册需要邮箱、平台密码设置及后台设备证明，不上传学号、学号散列或 associationToken。验证成功后原子创建账号、密码认证材料、初始设备凭据、首次 Session、首个邮箱及唯一登录角色。设备密钥仍是后台设施，不要求用户主动管理 Passkey，也不等于提前创建平台账号。

本 UC 不另定义密码接口；策略/存储、正常改密及登录邮箱恢复归 UC033，UC034 默认密码登录，UC012 码登录保留备用。三种登录均不替代切换角色的密码要求，校园认证仍按 UC031，不自动授予权限或管理次数。新密码 UC/协议为 DRAFT，未实现。

已交付的邮箱注册 v2/单邮箱 BIND 只作为工程基线，未实现本次密码/列表/角色切换；旧消息与实现约定在下文显式标为基线，不可继续把 Session＋新邮箱码当作切换登录邮箱的完整授权。

### 参与者与前置条件

- 注册明确不携带 Session，须邮箱验证码、新设备证明及密码设置；已有账号的添加/解绑/角色切换要求有效 ACTIVE USER Session。无效、空或撤销 Session 不降级注册。
- 各操作意图在发起时固定，途中登录/退出/切换账号不能改变 owner 或用途。已有账号 authId 只来自 Auth Session；普通添加不隐式替换登录角色。
- 切换到已绑定邮箱与切换到新邮箱同样要求当前密码；新邮箱还必须先验证。添加/解绑非登录地址不要求密码，但不能据此取得登录/密码恢复权。
- 当前登录邮箱不能直接解绑；须先原子切换到另一个已验证地址，再移除旧地址。始终恰好一个登录角色，待验证地址不算保底邮箱。
- 用户明确提交目标邮箱。客户端不得从学校数据、资料字段或本机缓存自动发起注册或绑定。Auth 配有邮件发送适配器，邮件系统不决定账号归属。

### 输入与输出

新增逻辑能力：注册提交密码设置；本人查询返回邮箱列表及唯一登录角色；添加验证只增加非登录绑定；切换提交目标 bindingId、当前密码验证与邮箱角色期望版本；解绑提交本人非登录 bindingId 和期望版本。2026-10-13 新增[邮箱账号 v3 契约草案](../../platform/contracts/auth-email-account-v3.md)，固定独立入口/字段号、新注册签名、目录/角色版本及防旁路提案，待用户审核；不直接向已交付 v2 消息追加秘密。

以下消息仅记录已实现的无密码 REGISTER/单邮箱 BIND 基线，不是本次修订的完整输入输出：

```text
BeginSetEmail {
  requestId: UUID
  email: string
  // 以下两组互斥，且必须与 Session 是否提供一致：
  binding: { expectedRevision: int64 } | null
  registration: {
    credentialProposal: CredentialRegistrationProposal
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

以上是已交付基线的逻辑消息。UUID、时间、公钥/签名编码引用设备契约，v2 十字段签名和消息保持历史互操作证据；它没有平台密码或邮箱列表，不能证明新模型已交付。旧无邮箱 REGISTER 和 v1 仍退役；新增模型的协议须另行审核。

BIND 的 expectedRevision 必填，首次绑定为 0；REGISTER 不能提交已有账号的 revision。Complete 的 REGISTER 分支必须提交设备证明，BIND 分支不接受该字段。客户端不能提交 authId、verified、emailLoginEnabled、角色或服务器时间。

重发使用新 requestId 再次 Begin，并保留原模式和设备提案；REGISTER 不因发信失败重建密钥。本人查询不向匿名用户开放，pending 只表示本人仍可验证的 BIND 提案；匿名注册依靠 Begin 幂等响应恢复操作元数据。

### 主流程

1. 固定注册/添加/切换/解绑意图及 owner，校验 Session 缺失/有效/无效，不自动建号。
2. 需要验证新邮箱的操作保存不可变地址/角色版本快照，消耗有界发送额度，再在事务外投递；未验证前不改变登录邮箱。
3. 注册验证邮箱/设备证明及密码策略，按 BR-EML-009 原子建立完整账号。
4. 普通添加验证邮箱后只建立非登录绑定；学校地址按 UC031 成为认证依据，不改变登录角色。
5. 切换通过当前密码和目标邮箱验证，在最终一致检查点比较版本并原子改变唯一登录角色；旧地址可以保留为非登录绑定，不隐式删除。
6. 解绑在最终事务确认目标不是当前登录邮箱，再删除绑定并按 UC031 收敛校园认证；失败/并发冲突不产生半变更。
7. 确认提交后返回结果；未知提交按固定操作恢复，不能自动扩大目标或把注册、添加和角色切换混为同一重试。

### 错误语义

下表为已交付 v2/单邮箱基线错误，新注册缺密码、密码验证失败、当前登录邮箱禁止解绑和角色/绑定版本冲突等完整 reason/映射待新协议审核；不能用原表证明新安全门禁已实现。

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

本次新增验收：注册缺密码拒绝且无半账号；列表有多地址但恰好一个登录角色；添加/解绑非登录地址不要求密码但不能获得恢复权限；切换到已有/新增目标均需密码；并发切换/解绑不能移除当前角色；学校最后依据解绑使 UC031/UserInfo 收敛；只用当前登录邮箱授权密码恢复。字段/版本/幂等/密码错误及旧入口防旁路必须补真实回归。

下列为既有 v2/单邮箱基线验收，保留作回归证据，不代表新增需求已满足：

1. 无 Session 的邮箱注册在验证码与设备证明通过后，原子创建正式 USER、设备凭据、已激活邮箱及首次 Session，不上传关联声明或写关联组；Begin、取消或失败不留账号。
2. 有效 Session 的首次绑定/更换只操作当前账号，不另建 USER 或 Session；缺失公钥或任一注册证明不能注册成功；普通邮箱与校园邮箱都可注册。
3. 空值、错误、过期、撤销 Session 均不降级成注册；BIND 中途掉线、REGISTER 中途登录、跨账号切换均不改变固定模式。
4. 格式边界、大小写规范化、前导零验证码、`+tag` 和点号不合并；HTTP/gRPC 共用校验。
5. 更换验证前旧邮箱有效；投递失败、错误、过期、冲突不改变旧绑定；成功原子切换并增加一次 revision。
6. REGISTER/REGISTER、REGISTER/BIND 和 BIND/BIND 并发争用同一邮箱最多一个成功；不能凭验证码抢占已有绑定或自动登录旧账号。
7. 同公钥/邮箱并发注册最多一个账号；无邮箱注册路径不可用，失败不隐式绑定到胜出账号。
8. 重发使同账号 BIND 或同公钥 REGISTER 的旧操作失效，不作废其它公钥的邮箱注册提案；并发失败计数、限额及验证码消费有界且跨重启有效。
9. 设备签名篡改邮箱、公钥、用途、期限或操作标识失败；旧 v1 注册签名和已退役关联字段拒绝，不能省略/补零兼容为 v2 或跨操作组合证明。
10. Begin 幂等不重复发信；BIND Complete 幂等不重复变更。REGISTER 完成重放不泄露 Session token，丢失首次响应可用原设备密钥登录同一账号。
11. Mongo 回滚、唯一冲突、提交未知和投递前后中断不产生半创建账号或误报成功；禁用/撤销与 BIND 激活遵守现有认证事务确认边界。
12. 本人查询拒绝匿名和他人访问；邮箱/秘密不出现在普通 JWS、日志或审计；邮件 HMAC 冷更新仍关闭对应未完成操作，但没有关联轮换依赖。
13. 两分支均不授予 Developer 或恢复旧账号，不改变 UC008/009 撤销语义。

### 实现约定

以下仅记录已交付 v2/单邮箱基线，用于理解当前代码和保留回归；其 activeEmail 单字段、BIND 替换及无密码消息不是本次修订实现约定。邮箱列表/唯一角色、密码安全处理和请求/版本绑定须先单独设计并审核，不照抄旧 schema 接口开工。

#### 事务与存储

- 复用既有 Mongo 副本集与认证事务栅栏，原子写入范围按 BR-EML-009；不得顺序建号再补绑定。内部事务方法保持 DDD 依赖方向，旧无邮箱创建 API 不再兼容。
- 邮箱绑定独立 collection，authId 与规范邮箱分别唯一；每账号一个文档维护 activeEmail/revision 与当前 BIND 操作引用。普通旧 USER 没有该文档视为未绑定、revision 0，首次 Begin 可以建立邮箱能力记录，但不修改主体资料或伪造已激活邮箱。未激活邮箱不占全局唯一键，可用 partial unique index。
- 操作保存不可变模式、身份/公钥定位、规范邮箱、requestId、期限、邮件校验值、请求指纹、状态及失败次数，不保存关联快照。邮件冷更新与过期清理须覆盖全部邮箱操作。
- 本人查询返回同一一致快照中的 revision、activeEmail 和当前有效 pending；主动关闭、被替代、过期或耗尽尝试的操作不返回 pending。BIND 成功与操作结果、绑定变更及审计同事务；邮箱替换、禁用、凭据撤销与注册/绑定都参加现有认证栅栏。
- 邮箱 revision 使用非负 int64；到最大值时拒绝再激活并返回 EMAIL_REVISION_CONFLICT，不溢出或重置。审计写入失败则业务回滚。
- REGISTER 完成标记及请求 HMAC 保留至至少 24 小时幂等窗口结束；BIND 历史结果保留至少 24 小时。过期个人操作数据按所需窗口清理，TTL 仅做物理删除，校验使用期限/状态。

#### 邮件校验与幂等指纹

`K_email` 是 `AUTH_EMAIL_BINDING_HMAC_KEY` 提供的独立 32 字节随机密钥，使用标准 Base64 编码。校验 HMAC 与请求 HMAC 通过不同用途标签隔离，不与其它认证能力共用；基础编码引用共享协议。

```text
REGISTER requestBytes = Frame(
  UTF8("iwut-email-request-v2"), UTF8("REGISTER"), UTF8(requestId),
  UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8(credentialProtocolVersion), publicKey65)
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

purpose 分别为 BIND_EMAIL / REGISTER_WITH_EMAIL。REGISTER 使用新请求域 v2，BIND 的请求域/编码与 codeMac、keyId 不变；不把旧注册请求 HMAC 当作新请求。保存 requestMac/codeMac，不保存请求明文编码、验证码或 signingPayload。keyId 仅内部识别校验密钥变化。

冷更新识别 keyId 变化时关闭旧 keyId 的未完成操作；完成标记保持，不重新披露 token。旧 BIND 验证码不可重放，以本人查询确认当前状态。窗口内旧操作仍占原幂等键，换钥不创建同键新操作；其它旧/失效操作重试返回 EMAIL_VERIFICATION_FAILED。无需旧邮件密钥继续驻留。同密钥日常重启保留有效操作；旧 v1 注册操作不进入 v2 完成路径，不对未部署系统设计生产迁移。

#### 限额与投递

- 发送采用过去 60 分钟滑动窗口；默认额度引用 BR-EML-006，最近一次发送与 now 间隔不足 60 秒时冷却拒绝。账号/公钥、目标邮箱及可信来源的额度在同一事务中扣除，重试同一 requestId 不重复扣除或投递。限额存储有 TTL、总容量和失效清理，容量耗尽时拒绝新操作，不能丢弃活跃桶以绕过额度。
- SMTP 是首版具体适配器。配置启用开关 `AUTH_EMAIL_BINDING_ENABLED`，默认 false；为 true 时要求已有 `AUTH_USER_ENDPOINTS_ENABLED=true`，HMAC 和 SMTP 配置完整。关闭时不注册三个 HTTP 路由，三个 gRPC 方法返回 UNIMPLEMENTED，不回退为其它认证方法。
- 必需邮件配置：`AUTH_SMTP_ADDR`（host:port）、`AUTH_SMTP_FROM`（平台控制的单个发件地址）、`AUTH_SMTP_TLS_MODE`（仅 `implicit_tls` 或 `starttls`）。`AUTH_SMTP_USERNAME`/`AUTH_SMTP_PASSWORD` 同时配置或同时为空；TLS 必须验证证书及目标主机名，不允许明文降级。可选 `AUTH_SMTP_CA_FILE` 提供受信 CA，包括隔离测试环境的测试 CA；超时 `AUTH_SMTP_TIMEOUT` 默认 10s，必须为正。
- 启动时校验参数、密钥格式和 CA，不给真实邮箱发探测邮件；网络不可用由实际投递返回 EMAIL_DELIVERY_UNAVAILABLE。SMTP 适配器只在事务确认之后调用一次；Begin 幂等重放无论上次投递成功、失败或未知都不再次发送，用户以新 requestId 重发。
- 邮件是固定用途模板，说明本次请求、验证码及期限，不包含学号、关联信息、authId、完整设备公钥或登录链接；目标是否被占用不改变模板。头部地址经过校验，不能拼接用户输入注入任意邮件头。验证码/地址及 SMTP 凭据不记录到日志；发送失败不返回 SMTP 原始正文。
- 用可控 TLS SMTP 接收端验收实际生产适配器，包括超时、拒绝及事务已提交而响应丢失；不把仅 fake sender 的测试当作生产投递已实现，不向真实用户发信。

### 交付依赖与边界

本次硬依赖：密码生命周期与安全存储/策略/再认证、邮箱列表/容量/归属/版本/新接口、UC031 当前绑定事实与撤回、UC012/013/017 消费唯一登录角色及 UC025 清理。已有实现项列在下面只表示可复用基础；新修订 DRAFT，不按旧 brief 自动实施，不对未部署系统新增旧用户生产迁移。

- 复用 UC006/007 主体初始化、凭据唯一性、首次 Session 与事务设施；秘密/寿命/容量遵守 BR-LGN-003/004/010，限额遵守 BR-LGN-009，最终栅栏遵守 BR-IDN-004，不恢复关联存储或顺序建号再绑定。
- [邮箱设置与注册协议 v2](../../platform/contracts/auth-email-binding-v2.md) 固定新签名、退役字段与入口；新的公开向量和 Go 验证器已交付，客户端/Gateway 继续独立验收，历史 v1 fixture 不能作为新版注册验收。UC007 设备登录和 UC012 邮箱登录签名字节不变。
- 补齐 EmailBinding 服务 Proto、HTTP annotation 和精确方法鉴权：Begin 允许无 Session 注册或有效 Session 绑定，但拒绝无效 Session；Complete 按持久化模式验证；GetOwnEmailBinding 始终要求有效 Session。Gateway 走 DIRECT，由 Auth 检查原始 Session 载体及证明，不统一套用必需 Session middleware，也不把带错 token 的请求转成匿名。
- 邮箱唯一性、revision、幂等/操作、持久限额、原子审计与真实邮件适配器保持；删除关联配置与迁移装配，保留独立邮件冷更新。生产配置不入仓库。
- 后端真实 Mongo 与隔离邮件接收端验收；客户端邮箱注册/登录界面、Gateway 与公网投递独立交付，不向真实用户发测试邮件。
- UC012/013 已接受，历史交付见实现记录；本次注册 v2 与用户已接受的 UC031 同步实施、实际验证后记录状态。具体应用次数设计不是 Auth 注册的实施依赖。

## 业务规则（UC-AUTH-011 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-001 -->
### BR-EML-001：邮箱凭据与资料、身份分离

邮箱绑定由 Auth 独立管理，不写入用户资料 KV；资料中的邮箱即使文字相同，也不成为已验证凭据，二者不自动同步。邮箱验证只证明本次操作期间的邮箱控制权，不证明学生身份、真实姓名或永久所有权。

每个正常账号最多有 10 个已验证邮箱，其中始终恰好一个登录邮箱；其余地址不具有登录、授权新设备或重置密码权限。所有规范地址（包括非登录校园邮箱）跨账号全局唯一，每个绑定有不可复用 UUIDv4 bindingId。登录邮箱可以同时是学校邮箱，但登录角色与校园认证用途相互独立。未验证提案不占用邮箱归属，不自动创建/合并账号或转移他人邮箱；正确邮件码本身不授予原账号控制权。2026-10-13 用户确认容量与全局唯一策略。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-002 -->
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-003 -->
### BR-EML-003：分支授权与验证码隔离

REGISTER 要求邮箱码、设备证明及 UC033 密码设置；非登录邮箱添加要求有效 Session＋目标码，非登录解绑只需有效 Session，不要求密码。切换唯一登录角色（已有/新增目标均同）必须 UC033/BR-PWD-003 当前密码目标绑定验证＋有效 Session，最终复核角色/密码/账号版本；新地址仍需验证码。普通添加/解绑不产生登录权，不可组合成 Session-only/扫码绕过；列表须有效 Session，不匿名降级。

邮件验证码继续采用基线的均匀 8 位 ASCII 数字、10 分钟、最多 5 次失败，等于 expiresAt 即过期。新增注册、添加绑定、登录和密码重置各自用途隔离；新增登录角色切换须绑定 owner/旧新目标/角色版本/密码版本/操作/期限，密码验证与目标切换不可拼接或任意复用。新增用途标签和协议版本待审核，不能把旧 `BIND_EMAIL` 证明解释为已经满足当前密码保护。

既有 v2 设备签名覆盖独立用途/操作/挑战/期限/部署/地址/公钥，但没有密码设置，本次须闭合密码注册请求绑定及版本。邮箱码与设备证明对应同一操作，不能拼接；密码不进入可返回/记录的签名 payload。注册挑战基线 10 分钟，不改变设备登录 5 分钟；Complete 不允许覆盖固定输入，证明不跨版本/用途。

仅有新邮箱验证码、Session 或 operationId 不能切换原账号登录邮箱；注册也不能缺密码设置。忘记密码的唯一邮箱恢复来源是当前登录角色，不是任意绑定/历史邮箱，重置用途与登录/绑定码严格隔离；正常改密码仍需旧密码，新密码生命周期接口待独立设计。邮件失败尝试计数与关闭操作原子更新，过期使用服务端时间，不依赖 TTL。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-004 -->
### BR-EML-004：更换与原子激活

本规则区分添加绑定与切换登录角色。添加先验证目标，成功只增加非登录地址，不删除原邮箱或改变角色；切换始终须当前密码、合法目标及一致版本。邮件重发不能延长旧操作、晚到码不能完成被替代操作；多个添加提案的容量/替代规则和幂等键需随邮箱列表协议闭合，不沿用“每账号单个 BIND 就替换登录邮箱”的隐式行为。

邮箱集合/登录角色的版本独立于资料、账号代际和密码版本。最终提交复核目标仍绑定且已验证、当前密码验证未被改密/重置废止、期望角色版本未变化；冲突不自动覆盖。最终存储版本划分与 Proto presence 待审核，不能用旧 activeEmail 单字段掩盖多个地址和角色竞争。

角色切换与密码验证消费、版本推进、操作结果、审计同事务提交；提交前旧登录邮箱始终有效，任何失败都不留下零个或多个登录角色。旧登录邮箱可以保留为非登录绑定，不隐式释放其地址或删除校园依据；只有明确解绑才移除。当前登录邮箱不得直接解绑，解绑事务必须重新确认其非登录状态，并与角色切换串行协调，不能靠客户端提示保护最后入口。

邮箱增删/角色切换不改变 authId/Developer/sub，校园认证按 UC031。2026-10-13 用户确认切换登录邮箱不清退已有设备和 Session、不推进 accountRevision；推进 loginRoleRevision 使旧邮箱登录/恢复提案失效，切回也不复活旧提案。密码修改/恢复的收回策略唯一见 UC033/BR-PWD-004–006。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-005 -->
### BR-EML-005：重试与提交结果不确定

基线的 24 小时幂等窗口、同键异参冲突、不重复发信/延长挑战继续适用；新增添加/角色切换/解绑须固定 actor、用途、目标与角色/密码版本，网络重试不得把只添加升级为登录切换或扩大解绑目标。密码设置的请求一致性如何比较及保护待密码协议确定，不把明文密码放入幂等记录/HMAC 输入日志或签名 payload。REGISTER 已完成不再披露初始 Session；过期/废止操作不复活。

既有账号变更的完成记录至少保留 24 小时；重试只恢复同一已确认操作，不再次变更或恢复旧登录角色/被删除学校依据。恢复历史结果仍需当前合法身份，不能仅凭历史码绕过密码再认证或当前版本条件。密码修改/恢复与变更证明的废止、完成重试规则须在独立协议闭合；当前状态以本人邮箱列表为准。

REGISTER 遵守 [BR-REG-006](../use-cases/UC-AUTH-006-create-user.md#br-reg-006) 的一次性注册结果语义：同操作最多创建一个账号及首次 Session，成功重放只返回 `REGISTRATION_ALREADY_COMPLETED`，不再次披露 Session token 或账号资料。完成标记的保留不得短于 Begin 幂等窗口；即使操作记录后来清理，公钥唯一归属也不释放。客户端在响应丢失、提交未知或已完成时保留原私钥，通过 UC007 发起新的设备登录恢复同一账号，不能换密钥重建账号。

Begin 和 Complete 提交结果未知时返回不可用，不声称已回滚。Begin 使用原 requestId 重试取回操作元数据；未完成且无法投递时，冷却后显式重发。REGISTER 重试不依赖原本不存在的 Session；BIND 重试不得因丢失 Session 而变成 REGISTER。服务端也不能因为 Complete 恰好携带了一个 Session 就更改匿名操作的模式。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-006 -->
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认 BIND 按账号、REGISTER 按规范公钥指纹控制发送间隔至少 60 秒，两分支共用目标邮箱至少 60 秒的发送间隔；每账号/公钥指纹及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次。匿名注册还复用 BR-REG-007 的未完成挑战容量限制，不以可任意更换的公钥指纹作为唯一防滥用依据；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；独立邮件验证 HMAC 覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较，不与邮箱登录或 JWS 共用秘密。密钥由 ENV 注入；冷更新换钥可使未完成验证码失效，不为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功 BIND 以当前查询恢复状态；已完成 REGISTER 通过设备登录恢复。

学生关联配置、快照和启动离线迁移按 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008) 退役；邮件 HMAC 冷更新仍按本 UC 执行，不能借退役关联而取消邮件操作失效处理。

邮箱明文仅在 Auth 绑定、短期操作及邮件投递中使用；密码不以明文持久化/投递，不进入日志/审计/签名 payload。列表不自动加入 JWS、资料或 Developer 投影。审计仅必要标识/版本/时间/结果，不含邮箱、密码、验证码或 token；操作在窗口后清理。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-007 -->
### BR-EML-007：查询与占用披露边界

本人查询使用有效 Session，返回已验证邮箱列表、唯一登录角色及有界待验证提案的一致快照；不接受按任意邮箱/他人 authId 查询。规范地址对应绑定身份，角色/校园属性由 Auth 得出，非客户端可写标志。匿名注册/登录/重置不返回列表，不提供邮箱预查存在接口；必要依赖损坏失败关闭，不伪装成没有登录邮箱。

只有已通过当前操作邮箱验证码验证后，Complete 才可返回 `EMAIL_UNAVAILABLE` 表示地址不可用于本账号，不返回占用者 authId、资料或 Developer 状态。占用判断必须在提交点重新确认，不能把 Begin 时查重当成承诺。REGISTER 冲突时不创建新账号，也不自动切换为邮箱登录；客户端提示使用已有账号登录入口，该入口未交付时不能伪装成可用恢复方式。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-008 -->
### BR-EML-008：恢复与 Developer 开通边界

邮箱添加/解绑/角色切换不签发 Session、不添加设备公钥；注册只建立新账号的初始凭据/Session。不自动开通 Developer。UC012 的已交付验证码登录只认可当前唯一登录邮箱，不接受非登录校园地址或资料 KV；新增密码普通登录待确定，不继承旧私钥或学校声明。

Developer 开通引用 UC013；其邮箱前置条件必须是当前唯一已验证登录邮箱，额外认证邮箱不能代替。校园地址解绑的影响由 UC031 定义，Auth 不自动撤销/补发应用次数。密码忘记恢复只能用当前登录邮箱；具体重置 API/协议另行设计，不能把本 UC 邮箱添加码当作重置码。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-009 -->
### BR-EML-009：邮箱注册的原子创建

REGISTER 复用 UC006 主体初始化/凭据归属，首次 Session 复用 UC007。邮箱与设备证明、密码策略/安全认证材料均满足前，不创建临时 USER、不建立设备归属、不占用登录邮箱。

一次 Mongo 事务提交 USER、安全密码认证材料、初始设备凭据/Session、首个已验证邮箱及唯一登录角色、必要归属/版本、操作消费/审计；不写关联组。任何失败回滚，不顺序建号再补密码/邮箱。邮件在事务外，初始令牌仅确认提交后返回；学校邮箱依据与当前认证投影按 UC031 同事务闭合，认证/审计失败回滚注册。

每个规范公钥指纹只允许一个当前待验证 REGISTER 提案；同密钥重发使旧提案失效，不影响其它密钥，不按收件地址作废他人挑战。已登记公钥不能给旧账号补绑邮箱或创建第二账号。并发邮箱注册依靠凭据/邮箱唯一性确保唯一归属；失败方先通过 UC007 登录确认结果，再以 Session 发起 BIND，不能把注册码用于旧账号绑定。无邮箱注册接口不可用。

被占用邮箱或公钥冲突不留下半创建账号；“有 Session 绑定、无 Session 显式注册”的选择只在 Begin 固定，后续不能重新推断目标。不接收学校声明定位旧账号或授予权益。

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
| 校园认证与操作 | 按修订 UC031 清除认证依据/投影、验证地址/MAC/操作及受控审计；新邮箱列表/密码材料须纳入终止清单，不按邮箱跨账号清理，不保留已消费库，备份恢复执行终止门禁 |
| 已退役学生关联 | 新设计没有组/成员或关联密文。移除关联装配时同步退役清理步骤；当前代码历史清理仍存在，不能以文档修订冒称已移除。旧开发数据独立显式处置，不增加生产迁移 |
| developerHandle | 永久保留规范 handle、原 authId、claimedAt 和终止占用标记；不转让、不释放、不连同邮箱/资料保留。该最小公开命名空间墓碑明确向本人披露 |
| Auth 审计 | 只读期内保留最小事件归因，不保留 token/邮箱/资料副本；账号相关普通事件上限为事件发生后 180 天，已超期的随本次任务清理。注销事件保留 180 天；期满按专用保留任务删除，不由业务更新覆盖 |
| 协调决定、清理进度及查询令牌 | App 确认终局前保留必要决定；查询摘要最多 30 天，详细清理任务在全部步骤完成且终局回执后清理，永久终止事实由最小墓碑承担 |

默认活动存储清理目标为终止后 24 小时，超时告警并保留失败进度，绝不伪报完成。普通日志不应保存上述秘密，已经存在的可识别普通日志轮转上限 30 天；备份自然淘汰上限 30 天。部署未落实这些期限时不得展示该承诺或启用入口。

首次管理员的全局 bootstrap 消费事实永久保留；其原事件到期删除时按 [管理员初始化规则](../use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-005) 在同一认证事务写 auditRetiredAt 收据，防止清理后所有管理员操作因审计缺失被拒绝。此全局控制记录不属于账号资料墓碑。

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

每条 Session 记录认证方法、credentialId、认证/创建/使用/到期时间及撤销状态。EMAIL_CODE_AND_DEVICE 来源见 UC012；新增 PASSWORD_AND_DEVICE 见 UC034、PASSWORD_AND_SESSION 见 UC033/密码契约，分别必须 passwordRevision 以及后者的 sourceSessionId。sourceSessionId 是历史证明来源，不要求旧来源仍有效。统一验证 owner/当前代际/凭据下界和必需来源字段，不能当未知方法忽略。新方法未实施，不改变 lastUsedAt/LRU 或宣称已有密码会话。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-009 -->
### BR-LGN-009：认证入口的失败与披露边界

Begin/Complete 需要请求大小、挑战尝试次数、创建速率和未完成操作容量限制；按来源/操作/凭据等维度组合，不信任客户端设备 ID。初始参数如下，必须在上线前配置校验，不由学生关联分组代替。

认证入口工程默认值：解压后消息上限 16 KiB、单挑战最多 5 次失败、全局 Begin 每分钟 600 次、全局 Complete 每分钟 1200 次、同来源 Begin 每分钟 30 次、同定位 Complete 每分钟 60 次、未完成挑战最多 10000 条。参数可配置但必须有限且为正，非法配置拒绝启动；总体容量和全局限速即使来源不可确认也必须生效。未知 operationId 的 Complete 同样计入全局 Complete 限流，不能通过制造新定位或未知操作绕过总量保护。来源默认使用受信网络对端，不信任终端自填 forwarded header；Gateway 精细来源限流以后通过受信转发契约接入。挑战次数和未完成容量在 Auth 持久化层原子确认；单进程速率桶允许重启清空，不称为跨重启风控。每来源及每定位桶的存储必须有有限容量、过期淘汰和容量耗尽策略，不能因任意客户端定位形成无限内存增长；即使无法新增细分桶，全局限流仍须生效。

错误不区分未知账号、已撤销凭据、错误签名与账号禁用的具体身份事实。依赖不可用与错误凭据区分，便于客户端重试而不是误创建账号。对外不返回账号是否绑定邮箱、关联组成员、内部验签细节或堆栈。

认证请求/响应正文不进入常规日志；禁止记录 token、完整挑战/证明或任何私钥。操作元数据可以记录 operationId、sessionId、结果和时间，已确认身份后才记录可信 authId。Session 不含用户资料，认证事件不广播敏感声明。

### 来自 `UC-AUTH-033`

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-003 -->
### BR-PWD-003：危险动作的目标绑定验证

首版密码要求矩阵如下，业务权限/原有设备证明仍由各 UC 校验，不因密码正确被替代：

| 动作 | 密码要求 | 原有额外条件 |
| --- | --- | --- |
| UC011 切换唯一登录邮箱 | 当前密码 | 有效 Session、目标已验证、角色版本 |
| UC032 移除其他凭据 | 当前密码 | 原 Session 所引用设备的新签名、明确单目标 |
| UC025 注销本人账号 | 当前密码 | 原专用设备证明、确认及应用/管理员退出门禁 |
| UC026 签发 app.close 近期证明 | 当前密码 | 同 Session/设备新签名；App 独立归属门禁 |
| 正常改密码 | 旧密码 | 有效 Session、新密码策略 |
| 忘记密码重置 | 不要求旧密码 | 仅当前登录邮箱独立重置码 |
| 非登录邮箱添加/解绑、Session 回收、本机凭据退出 | 不新增密码要求 | 原有效 Session/邮件控制权/owner 条件 |

密码由 Auth 在业务提交时核验，验证结果内部绑定 authId、passwordRevision、accountRevision、操作 ID、purpose、精确目标/版本及期限；事务重试重新复核，不能接受客户端 passwordVerified 或通用 5 分钟解锁标志。优先直接携带密码在原业务 Complete 中验证，不额外签发通用高权限 token。

UC025 的 DISABLED 本人专用途径仍可用：在该专用设备操作解析出的本人范围内检查密码，不要求普通有效 Session，也不恢复账号；其它密码操作仍只允许 ACTIVE。遗忘密码且账号禁用时不能绕过账号 gate 自动恢复，受理/治理另按既有边界。

已签发 app.close/USER/委托短期 JWS 的离线残余窗口见 BR-PWD-006；密码规则需同步其签发入口，不能仅改 UI，而旧 Complete 仍无密码成功。其他未列平台管理动作不自动新增/取消原权限规则，后续扩展矩阵需独立审核。

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-004 -->
### BR-PWD-004：正常改密保留当前设备

当前 Session 与所引用凭据必须在最终事务仍有效，旧密码校验快照版本未变化，新密码满足策略。正常改密将 passwordRevision/accountRevision 各加一，并将 minimumCredentialRevision 提升到新 accountRevision；唯一保留的当前有效凭据推进 credentialRevision 到该值，不更改公钥/指纹/createdAt/credentialId。已经撤销或低于旧下界的凭据不可成为保留对象。

旧 Session 全部失效，包括调用 token；新建不同 sessionId/token 的 Session，只在确认首次提交后返回。新记录方法为 `PASSWORD_AND_SESSION`，表示旧 Session＋密码重新认证，不伪称完成新的私钥签名；必需当前 credentialId、来源 sessionId、passwordRevision 和新 accountRevision。来源 sessionId 是不可变认证快照，不要求旧来源 Session 继续有效，也不由用户指定。

新 Session 按 UC007 新会话固定寿命与容量规则建立，authenticatedAt/createdAt 为本次密码验证提交时间；不更新旧 Session 的代际或延长旧会话。其他凭据永久退休，重新登录生成新密钥；用户界面提前说明“当前设备保留，其他设备需重新登录”。

### 来自 `UC-AUTH-006`

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-006 -->
### BR-REG-006：原子创建与结果不确定的恢复

新 USER、安全密码认证材料、初始凭据、首次 Session、首个已验证邮箱/唯一登录角色、注册操作消费和最小审计一次 Mongo 多文档事务提交；邮箱细则由 [BR-EML-009](../use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-009)定义。任一失败全部回滚，不允许顺序建号再补邮箱或密码。事务自动重试期间生成标识、Session 秘密和候选内容保持一致；未确认提交不返回秘密。

同一操作最多创建一个 USER 和一个首次 Session。完成重放返回 REGISTRATION_ALREADY_COMPLETED，不重新创建或再次披露 Session；不同操作同公钥/同邮箱由唯一约束协调。

响应丢失或提交未知时保留原私钥和操作，按 UC011 重试确认，再使用 UC007 新挑战恢复原账号；失去该私钥时可由 UC012 邮箱登录原账号。未知结果不能自动换密钥或邮箱再注册。不得明文持久化 Session 或把已消费注册证明变成长期恢复凭据。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-007 -->
### BR-REG-007：注册入口的限额与秘密最小暴露

注册请求有界，邮件发送与验证码额度遵守 [BR-EML-006](../use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-006)，一般挑战容量和来源限流遵守 [BR-LGN-009](../use-cases/UC-AUTH-007-login.md#br-lgn-009)。不能只依赖可伪造设备标识或任意换公钥防滥用。

秘密保护/Argon2id/策略引用 UC033，密码不进入签名 payload、KV/日志/邮件，不继承旧 SHA-256。审计仅必要 ID/结果/时间，占用披露按 UC011，不返回占用者。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-008 -->
### BR-REG-008：关联配置与离线迁移退役

学生关联密文、查找 HMAC、组/成员 schema、全量核验及启动前密钥轮换不再是新 Auth 的创建、登录或启动依赖。退役以下配置：AUTH_ASSOC_KEY_VERSION、AUTH_ASSOC_ENCRYPT_KEY、AUTH_ASSOC_LOOKUP_KEY、AUTH_ASSOC_PREVIOUS_KEY_VERSION、AUTH_ASSOC_PREVIOUS_ENCRYPT_KEY、AUTH_ASSOC_PREVIOUS_LOOKUP_KEY。新运行时不读取这些变量；环境残留不构成启动失败，不要求注入旧密钥才能启用邮箱注册或设备登录。

系统尚未部署，本轮不设计生产学生组迁移，不把旧组兑换成新校园认证、新身份或应用权益。实现删除关联装配、迁移调用、快照、创建写入及相关测试前置；保留现有账号、设备、Session 和邮箱模型的独立安全校验。旧开发数据库如需保留或清理，另行显式处置，不在普通启动中自动删除用户数据。

邮件 HMAC 冷更新、Session/JWS 密钥和 UC025 终止清单恢复仍遵守各自用例；退役关联迁移不能被解释成取消全部认证密钥轮换或恢复门禁。旧关联性能记录仅是历史证据，不是新版本维护窗口或上线验收项。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。学年时间表 PUT 只接受 nextRolloverAt、expectedRevision 和 reason，不接受客户端提交 currentAcademicYear。
- 设备登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 和应用存储清除的 `application_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB，应用用户存储固定 16 KiB。
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

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖修订后的资料/认证方法及退役无邮箱路径拒绝、Reviewer/应用运维权限方法、两个学年时间表管理方法及应用用户存储 HTTP/本人清除方法、
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

设备登录返回 `signingPayload: bytes`。服务器保存不可变快照，返回精确字节并在 Complete 重建验证。客户端核对协议、LOGIN purpose、operationId、challenge、expiresAt、预配 serviceId/applicationId 及刚提交的定位信息，不签署任意服务端字节。末字段是固定空字节串的保留槽，保留它仅为不改变既有 LOGIN 字节，不再代表学校关联。

```text
signingPayload = Frame(
  UTF8("iwut-device-proof-v1"), UTF8(protocolVersion), UTF8(purpose),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs),
  UTF8(locatorKind), locatorValue, emptyReservedSlot
)
```

- 当前 `purpose` 只接受 `LOGIN`；REGISTER 已退役。challenge 为 CSPRNG 32 字节，寿命固定 5 分钟，无客户端时钟容差。
- `serviceId` 为服务端部署必填的 `AUTH_AUTHENTICATION_SERVICE_ID`，1–128 个 ASCII 字符，允许字母、数字、`.`、`_`、`:`、`-`。示例 `iwut-auth-center:prod` 与 `iwut-auth-center:test` 必须不同。官方客户端为其目标环境预配置相同值，不能只相信响应。首版 applicationId 固定为 `iwut-client`；不提供动态选择应用参数。
- LOGIN 的 locatorKind 为 `CREDENTIAL_ID` 或 `PUBLIC_KEY_FINGERPRINT`，locatorValue 分别为提交的 UUID 文本 UTF-8 或原始 32 字节指纹；emptyReservedSlot 必须为零长度字节串，不接受 token、散列或 32 字节全零。BeginDeviceLogin oneof 必须恰好一个定位值。
- 登录的 payload 保留请求定位方式，不将指纹静默转换为 credentialId。对于未知、禁用、已撤销凭据，Begin 仍返回同形状的 v1 挑战，不返回 authId、credentialId、账号状态或恢复方式；Complete 统一认证失败。依赖故障与限流可以分别返回不可用和限流错误。
- LOGIN 操作保存 Begin 时的内部凭据解析结果；当时不可接受的目标在本操作中始终不可接受。后来注册同公钥或重新启用账号不会让这个旧挑战变成有效登录操作；需重新 Begin。Begin 时有效也不免除 Complete 的当前状态复核。
- 客户端签名输入上限 1024 字节。未知版本、枚举变体、字段错位及额外字段均拒绝；不协商降级到其它算法。
- 成功设备登录结果补充 `credentialId`，使注册响应丢失后通过指纹登录的客户端能恢复非秘密定位信息。它来自成功认证后的服务端凭据，不能成为客户端选择 authId 的输入。

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。UC020 独立入口的缺失/畸形或混用载体为 INVALID_SESSION_TOKEN（400），载体合法但当前资格失效为 SESSION_INVALID（401），不得沿用 UC008 的免有效性检查。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 新注册/目录使用 [已接受的邮箱账号 v3](../../platform/contracts/auth-email-account-v3.md) 的精确载体；旧可选 Session REGISTER/BIND 已退役，其它接口的必需载体不变。

### `platform/contracts/auth-email-account-v3.md`：邮箱账号、密码注册与登录角色协议 v3 草案

#### 范围与审核边界

UC006/011 拥有注册及邮箱集合规则，UC031 拥有当前校园依据，UC033 拥有密码策略/安全验证。本契约补齐原草案未固定的接口、集合版本及注册字节，2026-10-13 新增并经用户明确审核接受，授权 UC006/011/031 修订生成 brief 后实现；公开启用仍须完整验收。

用户已明确确认：最多 10 个已验证地址、所有地址跨账号全局唯一；切换唯一登录邮箱不清退现有设备/Session，但旧邮箱登录/恢复操作失效。本文不重新讨论这些规则。没有旧账号生产迁移；现有开发数据库不自动删除、补密码或补版本。

#### 精确入口与载体

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

#### 消息字段提案

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

#### 注册签名字节

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

#### 邮箱目录与独立版本

新目录 `auth_email_directories` 每 authId 唯一：`revision`、`loginRoleRevision`、`loginBindingId`、`verifiedCount` 均在服务端管理；revision/role 为正 int64，verifiedCount 为 1..10。

`auth_email_bindings` 每 bindingId 一条：authId、规范 email、verifiedAt；bindingId 与规范 email 各全局唯一，authId 不是唯一键。一次查询最多读 11 个绑定并验证 count/角色/owner 一致；第 11 个或多个/缺失登录角色失败关闭。删除后的 bindingId 不复用；重新验证原地址得到新 ID。

新增/解绑推进 directoryRevision，不改变 loginRoleRevision。切换登录角色推进两者；同目标为验证密码后的幂等 no-op，不增加版本。登录提案和密码恢复绑定 loginRoleRevision，不因添加/移除无关非登录地址而失效；角色 A→B→A 后原提案仍不能使用。目录版本溢出拒绝变更，不重置版本。

添加 Begin 固定 owner、accountRevision、目标和 expectedDirectoryRevision；首次/重复提交均需同 owner 当前有效 Session。Complete 最终比较快照、目录 CAS 和地址全局归属，成功只添加非登录绑定；并发目录变更为冲突，不自动改角色或复用旧验证另做动作。切换新地址先 ADD 验证，再 SWITCH，不能把新邮箱码当作原账号密码。

Remove 最终确认目标不是登录绑定；始终保留当前登录地址。解绑最后学校依据时客户端提前提示失去认证，但不额外要求密码；服务端不信任客户端校园标志。切换登录邮箱不修改账号代际、设备或 Session，不隐式删旧地址；Auth 消费方读取新主角色，旧邮箱码/恢复的角色版本复核失败。

#### 用途、HMAC 与重试

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

#### 校园依据与旧入口退役

校园 true 只从当前 verified WHUT 绑定集合导出，不另写永久 true 记录。OwnCampusCertification 的 certifiedAt 定义为**当前有效 WHUT 依据中最早 verifiedAt**；删除最早依据可能改变此时间，删除最后依据为 false 且无时间，重新绑定产生新验证时间。它不是首次领取/自然人身份，不得用其重置权益活动。

独立旧校园 Begin/Complete 作为受同一目录/容量/额度约束的 ADD 验证别名，使用新 ADD 用途；不再写旧永久集合，不因已经认证拒绝添加第二个学校地址。Get 与 UserInfo 在同一当前授权事务读取目录/绑定；最后依据移除提交后即不披露认证。坏目录整次拒绝。

旧 v1 EmailBindingService 的 BeginSetEmail/CompleteSetEmail（无密码 REGISTER、隐式更换主邮箱 BIND）退役，不允许通过开关恢复；旧只读 Get 可投影当前主邮箱及 loginRoleRevision，不提供旧 pending。历史 v2 向量保留，不改其字节或作为 v3 输入。Campus 旧永久文档不作为认证依据，无自动迁移。

#### 错误、依赖与启用

沿用邮箱规范错误，并增加 EMAIL_DIRECTORY_CONFLICT（409）、EMAIL_LOGIN_ROLE_CONFLICT（409）、EMAIL_BINDING_LIMIT_REACHED（409）、LOGIN_EMAIL_REMOVAL_FORBIDDEN（409）、EMAIL_BINDING_NOT_FOUND（404）。密码错误/成本额度/依赖按 UC033，不披露另一账号 owner。匿名注册的地址冲突只在证明该地址和新私钥控制后给出受控冲突，不提供存在性预查询。

硬依赖：本契约审核与公开 v3 正反向量、独立 API、密码初始化、目录角色读取和 UC012/013/017/033/034 的角色版本复核、共享邮件/昂贵额度、校园目录投影、UC025 清理/终止清单及旧入口防旁路。首版配置启用必须覆盖完整链路；不能先开密码 API 而保留旧无密码创建/换主入口。

2026-10-13 用户明确接受并授权实现；同步 UC006/011/031 ACCEPTED、脚本生成 brief 后开工。实现覆盖和启用门禁独立记录，不以接受代替验收。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-011`（use-cases/UC-AUTH-011-set-and-activate-email.md）：实现约定/事务与存储、实现约定/邮件校验与幂等指纹、实现约定/限额与投递、变更记录
- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：目标与范围、认证与资格、API 与确认过程、主流程、首版运行与协议固定值、错误、限额与验收、实现依赖与联动、变更记录
- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、交付依赖与非目标、参考、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-033`（use-cases/UC-AUTH-033-manage-password-and-recovery.md）：目标与范围、参与者与依赖、输入与输出、主流程、验收与错误边界、交付依赖与变更记录
- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：目标与范围、参与者与前置条件、输入与输出、主流程、持久化候选、异常语义、测试与验收、交付依赖与验收边界、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：路由边界、校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/auth-email-account-v3.md`（docs 根级共享文档）：实施证据与公开向量（2026-10-13）

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-011-set-and-activate-email.md` | 299 | `39d8427ba29e` |
| `use-cases/UC-AUTH-025-close-own-account.md` | 167 | `270401ed1609` |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 145 | `c64b0cd24844` |
| `use-cases/UC-AUTH-007-login.md` | 256 | `37041f11441d` |
| `use-cases/UC-AUTH-033-manage-password-and-recovery.md` | 171 | `a9f8309c49b6` |
| `use-cases/UC-AUTH-006-create-user.md` | 171 | `e30e98fe13c9` |
| `platform/contracts/auth-center-api-routing.md` | 142 | `c300b311eaac` |
| `platform/contracts/auth-device-session-v1.md` | 118 | `ec97f26c28b8` |
| `platform/contracts/auth-email-account-v3.md` | 126 | `b13b360d803f` |
