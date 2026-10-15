# UC-AUTH-011：设置并激活邮箱

状态：`ACCEPTED`

2026-10-13：用户审核并接受邮箱账号 v3 契约，授权本 UC 修订开始实现；密码初始化、目录/角色版本、校园当前依据和旧入口退役按 [v3 契约](../../platform/contracts/auth-email-account-v3.md)交付。下文此前待审核/单邮箱 v2 工程描述保留为历史基线，不作为新实现输入；新契约与本段优先。已完成依赖检查，公开启用仍需完整链路验收。

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

> 用户注册时验证邮箱并设置平台密码；已有账号管理已验证邮箱列表，其中始终恰好一个地址承担登录/密码恢复角色，切换该角色必须验证当前密码。

2026-10-12 密码、邮箱列表/唯一登录角色及校园解绑是实质修订，本 UC 回到 DRAFT 待重新审核，不能因旧版本 ACCEPTED 自动开工。[UC006](UC-AUTH-006-create-user.md)拥有初始化，原“一键注册”/无邮箱入口不恢复。客户端优先推荐 `@whut.edu.cn`，普通邮箱同样可注册；学校账号不是前提。

邮箱注册需要邮箱、平台密码设置及后台设备证明，不上传学号、学号散列或 associationToken。验证成功后原子创建账号、密码认证材料、初始设备凭据、首次 Session、首个邮箱及唯一登录角色。设备密钥仍是后台设施，不要求用户主动管理 Passkey，也不等于提前创建平台账号。

本 UC 不另定义密码接口；策略/存储、正常改密及登录邮箱恢复归 UC033，UC034 默认密码登录，UC012 码登录保留备用。三种登录均不替代切换角色的密码要求，校园认证仍按 UC031，不自动授予权限或管理次数。新密码 UC/协议为 DRAFT，未实现。

已交付的邮箱注册 v2/单邮箱 BIND 只作为工程基线，未实现本次密码/列表/角色切换；旧消息与实现约定在下文显式标为基线，不可继续把 Session＋新邮箱码当作切换登录邮箱的完整授权。

## 参与者与前置条件

- 注册明确不携带 Session，须邮箱验证码、新设备证明及密码设置；已有账号的添加/解绑/角色切换要求有效 ACTIVE USER Session。无效、空或撤销 Session 不降级注册。
- 各操作意图在发起时固定，途中登录/退出/切换账号不能改变 owner 或用途。已有账号 authId 只来自 Auth Session；普通添加不隐式替换登录角色。
- 切换到已绑定邮箱与切换到新邮箱同样要求当前密码；新邮箱还必须先验证。添加/解绑非登录地址不要求密码，但不能据此取得登录/密码恢复权。
- 当前登录邮箱不能直接解绑；须先原子切换到另一个已验证地址，再移除旧地址。始终恰好一个登录角色，待验证地址不算保底邮箱。
- 用户明确提交目标邮箱。客户端不得从学校数据、资料字段或本机缓存自动发起注册或绑定。Auth 配有邮件发送适配器，邮件系统不决定账号归属。

## 输入与输出

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

## 主流程

1. 固定注册/添加/切换/解绑意图及 owner，校验 Session 缺失/有效/无效，不自动建号。
2. 需要验证新邮箱的操作保存不可变地址/角色版本快照，消耗有界发送额度，再在事务外投递；未验证前不改变登录邮箱。
3. 注册验证邮箱/设备证明及密码策略，按 BR-EML-009 原子建立完整账号。
4. 普通添加验证邮箱后只建立非登录绑定；学校地址按 UC031 成为认证依据，不改变登录角色。
5. 切换通过当前密码和目标邮箱验证，在最终一致检查点比较版本并原子改变唯一登录角色；旧地址可以保留为非登录绑定，不隐式删除。
6. 解绑在最终事务确认目标不是当前登录邮箱，再删除绑定并按 UC031 收敛校园认证；失败/并发冲突不产生半变更。
7. 确认提交后返回结果；未知提交按固定操作恢复，不能自动扩大目标或把注册、添加和角色切换混为同一重试。

## 业务规则

<a id="br-eml-001"></a>
### BR-EML-001：邮箱凭据与资料、身份分离

邮箱绑定由 Auth 独立管理，不写入用户资料 KV；资料中的邮箱即使文字相同，也不成为已验证凭据，二者不自动同步。邮箱验证只证明本次操作期间的邮箱控制权，不证明学生身份、真实姓名或永久所有权。

每个正常账号最多有 10 个已验证邮箱，其中始终恰好一个登录邮箱；其余地址不具有登录、授权新设备或重置密码权限。所有规范地址（包括非登录校园邮箱）跨账号全局唯一，每个绑定有不可复用 UUIDv4 bindingId。登录邮箱可以同时是学校邮箱，但登录角色与校园认证用途相互独立。未验证提案不占用邮箱归属，不自动创建/合并账号或转移他人邮箱；正确邮件码本身不授予原账号控制权。2026-10-13 用户确认容量与全局唯一策略。

<a id="br-eml-002"></a>
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

<a id="br-eml-003"></a>
### BR-EML-003：分支授权与验证码隔离

REGISTER 要求邮箱码、设备证明及 UC033 密码设置；非登录邮箱添加要求有效 Session＋目标码，非登录解绑只需有效 Session，不要求密码。切换唯一登录角色（已有/新增目标均同）必须 UC033/BR-PWD-003 当前密码目标绑定验证＋有效 Session，最终复核角色/密码/账号版本；新地址仍需验证码。普通添加/解绑不产生登录权，不可组合成 Session-only/扫码绕过；列表须有效 Session，不匿名降级。

邮件验证码继续采用基线的均匀 8 位 ASCII 数字、10 分钟、最多 5 次失败，等于 expiresAt 即过期。新增注册、添加绑定、登录和密码重置各自用途隔离；新增登录角色切换须绑定 owner/旧新目标/角色版本/密码版本/操作/期限，密码验证与目标切换不可拼接或任意复用。新增用途标签和协议版本待审核，不能把旧 `BIND_EMAIL` 证明解释为已经满足当前密码保护。

既有 v2 设备签名覆盖独立用途/操作/挑战/期限/部署/地址/公钥，但没有密码设置，本次须闭合密码注册请求绑定及版本。邮箱码与设备证明对应同一操作，不能拼接；密码不进入可返回/记录的签名 payload。注册挑战基线 10 分钟，不改变设备登录 5 分钟；Complete 不允许覆盖固定输入，证明不跨版本/用途。

仅有新邮箱验证码、Session 或 operationId 不能切换原账号登录邮箱；注册也不能缺密码设置。忘记密码的唯一邮箱恢复来源是当前登录角色，不是任意绑定/历史邮箱，重置用途与登录/绑定码严格隔离；正常改密码仍需旧密码，新密码生命周期接口待独立设计。邮件失败尝试计数与关闭操作原子更新，过期使用服务端时间，不依赖 TTL。

<a id="br-eml-004"></a>
### BR-EML-004：更换与原子激活

本规则区分添加绑定与切换登录角色。添加先验证目标，成功只增加非登录地址，不删除原邮箱或改变角色；切换始终须当前密码、合法目标及一致版本。邮件重发不能延长旧操作、晚到码不能完成被替代操作；多个添加提案的容量/替代规则和幂等键需随邮箱列表协议闭合，不沿用“每账号单个 BIND 就替换登录邮箱”的隐式行为。

邮箱集合/登录角色的版本独立于资料、账号代际和密码版本。最终提交复核目标仍绑定且已验证、当前密码验证未被改密/重置废止、期望角色版本未变化；冲突不自动覆盖。最终存储版本划分与 Proto presence 待审核，不能用旧 activeEmail 单字段掩盖多个地址和角色竞争。

角色切换与密码验证消费、版本推进、操作结果、审计同事务提交；提交前旧登录邮箱始终有效，任何失败都不留下零个或多个登录角色。旧登录邮箱可以保留为非登录绑定，不隐式释放其地址或删除校园依据；只有明确解绑才移除。当前登录邮箱不得直接解绑，解绑事务必须重新确认其非登录状态，并与角色切换串行协调，不能靠客户端提示保护最后入口。

邮箱增删/角色切换不改变 authId/Developer/sub，校园认证按 UC031。2026-10-13 用户确认切换登录邮箱不清退已有设备和 Session、不推进 accountRevision；推进 loginRoleRevision 使旧邮箱登录/恢复提案失效，切回也不复活旧提案。密码修改/恢复的收回策略唯一见 UC033/BR-PWD-004–006。

<a id="br-eml-005"></a>
### BR-EML-005：重试与提交结果不确定

基线的 24 小时幂等窗口、同键异参冲突、不重复发信/延长挑战继续适用；新增添加/角色切换/解绑须固定 actor、用途、目标与角色/密码版本，网络重试不得把只添加升级为登录切换或扩大解绑目标。密码设置的请求一致性如何比较及保护待密码协议确定，不把明文密码放入幂等记录/HMAC 输入日志或签名 payload。REGISTER 已完成不再披露初始 Session；过期/废止操作不复活。

既有账号变更的完成记录至少保留 24 小时；重试只恢复同一已确认操作，不再次变更或恢复旧登录角色/被删除学校依据。恢复历史结果仍需当前合法身份，不能仅凭历史码绕过密码再认证或当前版本条件。密码修改/恢复与变更证明的废止、完成重试规则须在独立协议闭合；当前状态以本人邮箱列表为准。

REGISTER 遵守 [BR-REG-006](UC-AUTH-006-create-user.md#br-reg-006) 的一次性注册结果语义：同操作最多创建一个账号及首次 Session，成功重放只返回 `REGISTRATION_ALREADY_COMPLETED`，不再次披露 Session token 或账号资料。完成标记的保留不得短于 Begin 幂等窗口；即使操作记录后来清理，公钥唯一归属也不释放。客户端在响应丢失、提交未知或已完成时保留原私钥，通过 UC007 发起新的设备登录恢复同一账号，不能换密钥重建账号。

Begin 和 Complete 提交结果未知时返回不可用，不声称已回滚。Begin 使用原 requestId 重试取回操作元数据；未完成且无法投递时，冷却后显式重发。REGISTER 重试不依赖原本不存在的 Session；BIND 重试不得因丢失 Session 而变成 REGISTER。服务端也不能因为 Complete 恰好携带了一个 Session 就更改匿名操作的模式。

<a id="br-eml-006"></a>
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认 BIND 按账号、REGISTER 按规范公钥指纹控制发送间隔至少 60 秒，两分支共用目标邮箱至少 60 秒的发送间隔；每账号/公钥指纹及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次。匿名注册还复用 BR-REG-007 的未完成挑战容量限制，不以可任意更换的公钥指纹作为唯一防滥用依据；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；独立邮件验证 HMAC 覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较，不与邮箱登录或 JWS 共用秘密。密钥由 ENV 注入；冷更新换钥可使未完成验证码失效，不为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功 BIND 以当前查询恢复状态；已完成 REGISTER 通过设备登录恢复。

学生关联配置、快照和启动离线迁移按 [BR-REG-008](UC-AUTH-006-create-user.md#br-reg-008) 退役；邮件 HMAC 冷更新仍按本 UC 执行，不能借退役关联而取消邮件操作失效处理。

邮箱明文仅在 Auth 绑定、短期操作及邮件投递中使用；密码不以明文持久化/投递，不进入日志/审计/签名 payload。列表不自动加入 JWS、资料或 Developer 投影。审计仅必要标识/版本/时间/结果，不含邮箱、密码、验证码或 token；操作在窗口后清理。

<a id="br-eml-007"></a>
### BR-EML-007：查询与占用披露边界

本人查询使用有效 Session，返回已验证邮箱列表、唯一登录角色及有界待验证提案的一致快照；不接受按任意邮箱/他人 authId 查询。规范地址对应绑定身份，角色/校园属性由 Auth 得出，非客户端可写标志。匿名注册/登录/重置不返回列表，不提供邮箱预查存在接口；必要依赖损坏失败关闭，不伪装成没有登录邮箱。

只有已通过当前操作邮箱验证码验证后，Complete 才可返回 `EMAIL_UNAVAILABLE` 表示地址不可用于本账号，不返回占用者 authId、资料或 Developer 状态。占用判断必须在提交点重新确认，不能把 Begin 时查重当成承诺。REGISTER 冲突时不创建新账号，也不自动切换为邮箱登录；客户端提示使用已有账号登录入口，该入口未交付时不能伪装成可用恢复方式。

<a id="br-eml-008"></a>
### BR-EML-008：恢复与 Developer 开通边界

邮箱添加/解绑/角色切换不签发 Session、不添加设备公钥；注册只建立新账号的初始凭据/Session。不自动开通 Developer。UC012 的已交付验证码登录只认可当前唯一登录邮箱，不接受非登录校园地址或资料 KV；新增密码普通登录待确定，不继承旧私钥或学校声明。

Developer 开通引用 UC013；其邮箱前置条件必须是当前唯一已验证登录邮箱，额外认证邮箱不能代替。校园地址解绑的影响由 UC031 定义，Auth 不自动撤销/补发应用次数。密码忘记恢复只能用当前登录邮箱；具体重置 API/协议另行设计，不能把本 UC 邮箱添加码当作重置码。

<a id="br-eml-009"></a>
### BR-EML-009：邮箱注册的原子创建

REGISTER 复用 UC006 主体初始化/凭据归属，首次 Session 复用 UC007。邮箱与设备证明、密码策略/安全认证材料均满足前，不创建临时 USER、不建立设备归属、不占用登录邮箱。

一次 Mongo 事务提交 USER、安全密码认证材料、初始设备凭据/Session、首个已验证邮箱及唯一登录角色、必要归属/版本、操作消费/审计；不写关联组。任何失败回滚，不顺序建号再补密码/邮箱。邮件在事务外，初始令牌仅确认提交后返回；学校邮箱依据与当前认证投影按 UC031 同事务闭合，认证/审计失败回滚注册。

每个规范公钥指纹只允许一个当前待验证 REGISTER 提案；同密钥重发使旧提案失效，不影响其它密钥，不按收件地址作废他人挑战。已登记公钥不能给旧账号补绑邮箱或创建第二账号。并发邮箱注册依靠凭据/邮箱唯一性确保唯一归属；失败方先通过 UC007 登录确认结果，再以 Session 发起 BIND，不能把注册码用于旧账号绑定。无邮箱注册接口不可用。

被占用邮箱或公钥冲突不留下半创建账号；“有 Session 绑定、无 Session 显式注册”的选择只在 Begin 固定，后续不能重新推断目标。不接收学校声明定位旧账号或授予权益。

## 错误语义

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

## 测试与验收

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

## 实现约定

以下仅记录已交付 v2/单邮箱基线，用于理解当前代码和保留回归；其 activeEmail 单字段、BIND 替换及无密码消息不是本次修订实现约定。邮箱列表/唯一角色、密码安全处理和请求/版本绑定须先单独设计并审核，不照抄旧 schema 接口开工。

### 事务与存储

- 复用既有 Mongo 副本集与认证事务栅栏，原子写入范围按 BR-EML-009；不得顺序建号再补绑定。内部事务方法保持 DDD 依赖方向，旧无邮箱创建 API 不再兼容。
- 邮箱绑定独立 collection，authId 与规范邮箱分别唯一；每账号一个文档维护 activeEmail/revision 与当前 BIND 操作引用。普通旧 USER 没有该文档视为未绑定、revision 0，首次 Begin 可以建立邮箱能力记录，但不修改主体资料或伪造已激活邮箱。未激活邮箱不占全局唯一键，可用 partial unique index。
- 操作保存不可变模式、身份/公钥定位、规范邮箱、requestId、期限、邮件校验值、请求指纹、状态及失败次数，不保存关联快照。邮件冷更新与过期清理须覆盖全部邮箱操作。
- 本人查询返回同一一致快照中的 revision、activeEmail 和当前有效 pending；主动关闭、被替代、过期或耗尽尝试的操作不返回 pending。BIND 成功与操作结果、绑定变更及审计同事务；邮箱替换、禁用、凭据撤销与注册/绑定都参加现有认证栅栏。
- 邮箱 revision 使用非负 int64；到最大值时拒绝再激活并返回 EMAIL_REVISION_CONFLICT，不溢出或重置。审计写入失败则业务回滚。
- REGISTER 完成标记及请求 HMAC 保留至至少 24 小时幂等窗口结束；BIND 历史结果保留至少 24 小时。过期个人操作数据按所需窗口清理，TTL 仅做物理删除，校验使用期限/状态。

### 邮件校验与幂等指纹

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

### 限额与投递

- 发送采用过去 60 分钟滑动窗口；默认额度引用 BR-EML-006，最近一次发送与 now 间隔不足 60 秒时冷却拒绝。账号/公钥、目标邮箱及可信来源的额度在同一事务中扣除，重试同一 requestId 不重复扣除或投递。限额存储有 TTL、总容量和失效清理，容量耗尽时拒绝新操作，不能丢弃活跃桶以绕过额度。
- SMTP 是首版具体适配器。配置启用开关 `AUTH_EMAIL_BINDING_ENABLED`，默认 false；为 true 时要求已有 `AUTH_USER_ENDPOINTS_ENABLED=true`，HMAC 和 SMTP 配置完整。关闭时不注册三个 HTTP 路由，三个 gRPC 方法返回 UNIMPLEMENTED，不回退为其它认证方法。
- 必需邮件配置：`AUTH_SMTP_ADDR`（host:port）、`AUTH_SMTP_FROM`（平台控制的单个发件地址）、`AUTH_SMTP_TLS_MODE`（仅 `implicit_tls` 或 `starttls`）。`AUTH_SMTP_USERNAME`/`AUTH_SMTP_PASSWORD` 同时配置或同时为空；TLS 必须验证证书及目标主机名，不允许明文降级。可选 `AUTH_SMTP_CA_FILE` 提供受信 CA，包括隔离测试环境的测试 CA；超时 `AUTH_SMTP_TIMEOUT` 默认 10s，必须为正。
- 启动时校验参数、密钥格式和 CA，不给真实邮箱发探测邮件；网络不可用由实际投递返回 EMAIL_DELIVERY_UNAVAILABLE。SMTP 适配器只在事务确认之后调用一次；Begin 幂等重放无论上次投递成功、失败或未知都不再次发送，用户以新 requestId 重发。
- 邮件是固定用途模板，说明本次请求、验证码及期限，不包含学号、关联信息、authId、完整设备公钥或登录链接；目标是否被占用不改变模板。头部地址经过校验，不能拼接用户输入注入任意邮件头。验证码/地址及 SMTP 凭据不记录到日志；发送失败不返回 SMTP 原始正文。
- 用可控 TLS SMTP 接收端验收实际生产适配器，包括超时、拒绝及事务已提交而响应丢失；不把仅 fake sender 的测试当作生产投递已实现，不向真实用户发信。

## 交付依赖与边界

本次硬依赖：密码生命周期与安全存储/策略/再认证、邮箱列表/容量/归属/版本/新接口、UC031 当前绑定事实与撤回、UC012/013/017 消费唯一登录角色及 UC025 清理。已有实现项列在下面只表示可复用基础；新修订 DRAFT，不按旧 brief 自动实施，不对未部署系统新增旧用户生产迁移。

- 复用 UC006/007 主体初始化、凭据唯一性、首次 Session 与事务设施；秘密/寿命/容量遵守 BR-LGN-003/004/010，限额遵守 BR-LGN-009，最终栅栏遵守 BR-IDN-004，不恢复关联存储或顺序建号再绑定。
- [邮箱设置与注册协议 v2](../../platform/contracts/auth-email-binding-v2.md) 固定新签名、退役字段与入口；新的公开向量和 Go 验证器已交付，客户端/Gateway 继续独立验收，历史 v1 fixture 不能作为新版注册验收。UC007 设备登录和 UC012 邮箱登录签名字节不变。
- 补齐 EmailBinding 服务 Proto、HTTP annotation 和精确方法鉴权：Begin 允许无 Session 注册或有效 Session 绑定，但拒绝无效 Session；Complete 按持久化模式验证；GetOwnEmailBinding 始终要求有效 Session。Gateway 走 DIRECT，由 Auth 检查原始 Session 载体及证明，不统一套用必需 Session middleware，也不把带错 token 的请求转成匿名。
- 邮箱唯一性、revision、幂等/操作、持久限额、原子审计与真实邮件适配器保持；删除关联配置与迁移装配，保留独立邮件冷更新。生产配置不入仓库。
- 后端真实 Mongo 与隔离邮件接收端验收；客户端邮箱注册/登录界面、Gateway 与公网投递独立交付，不向真实用户发测试邮件。
- UC012/013 已接受，历史交付见实现记录；本次注册 v2 与用户已接受的 UC031 同步实施、实际验证后记录状态。具体应用次数设计不是 Auth 注册的实施依赖。

## 变更记录

- 2026-10-12：密码注册、已验证邮箱列表/唯一登录角色、角色切换密码保护及非登录绑定增删纳入 DRAFT 修订；旧字段/API/工程默认标为已交付基线，新密码协议仍待审核。
- 2026-10-12：UC031 接受/生成 brief 后完成注册 v2 和同事务校园认证，真实 Mongo/Wire/race 通过；下方同日待实施记录保留为历史阶段。

- 2026-10-12：按用户确认只保留邮箱显式注册，移除学生关联字段/快照/原子写入与离线迁移依赖，改为独立 v2 注册签名；普通邮箱可用、后台设备密钥保留。文档已修订，代码与新版向量尚未实施。

- 2026-09-24：提出设置并激活邮箱草案，定义验证码激活、先验证后更换、唯一归属、重试与邮箱登录/Developer 开通边界。
- 2026-09-24：按注册页两种选择修订：Begin 无 Session 走邮箱注册，有效 Session 走已有账号绑定；固定操作模式，拒绝失效 Session 降级，邮箱注册原子创建账号与首次 Session。仍为 PROPOSED，尚未实现。

- 2026-09-25：固定独立邮箱注册协议、公开正反向量、消息字段、精确 RPC/HTTP 与可选 Session 鉴权；明确 SMTP、HMAC/换钥、滑动发送额度与原子存储，基础依赖已具备，接受 UC011 后端工作包。
