<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-006 --spec tools/brief-specs/UC-AUTH-006.json -->
# Brief — UC-AUTH-006：创建用户

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-006` 创建用户 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-REG-001`–`BR-REG-008`（8 条） |
| 外部引用 BR | `BR-EML-006`、`BR-EML-009`，`BR-LGN-009`，`BR-PWD-001`，`BR-UPF-008`、`BR-UPF-010`（来自 `UC-AUTH-005`、`UC-AUTH-007`、`UC-AUTH-011`、`UC-AUTH-033`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-email-account-v3.md` |

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

> 用户明确选择邮箱注册，在 Auth 验证邮箱控制权、校验并建立平台密码及后台设备私钥持有证明后，原子建立正式 USER、空资料、首个已验证登录邮箱、初始设备凭据和首次 Session。

2026-10-12 按用户确认加入平台密码及邮箱列表模型，本次实质修订回到 DRAFT，等待完整密码/注册协议与依赖审核，不自动接受或开始实施。此前邮箱注册 v2/学号关联退役基线已交付；本次密码注册尚未实现，见[实现记录](../implements/README.md)。UC006 保留账号初始化、凭据归属、原子创建和结果恢复的权威规则；创建入口由 [UC011](../use-cases/UC-AUTH-011-set-and-activate-email.md) 的 REGISTER 分支提供。原无邮箱 BeginUserRegistration/CompleteUserRegistration 不恢复。

账号初始化、认证材料版本与 CLOSED 拒绝引用 [UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002)，终止与最小保留引用 [UC025](../use-cases/UC-AUTH-025-close-own-account.md#br-acc-009)。不得通过补默认值或历史成功结果复活账号。

后台保留 App 管理、系统安全存储保护的设备公私钥，供 UC007 记住登录、UC012 新设备登录及已接受的高风险证明使用；它不是标准 WebAuthn Passkey，不要求用户主动创建或管理“通行密钥”。学校账号及其本地功能不再是平台注册前提。

注册密码策略/材料及生命周期唯一见 [UC033 / BR-PWD-001/002](../use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-001)，默认密码登录 UC034，码登录 UC012 保留备用。本 UC 不另加修改/重置接口，不恢复/合并账号或上传学校关联，不管应用次数。校园成员认证按 UC031 当前绑定披露。

### 参与者与前置条件

- 用户明确选择“注册”，提交邮箱、设置 iWUT 密码并完成服务端邮件验证；普通邮箱可注册，客户端优先推荐 `@whut.edu.cn`，不以学校账号、本地学号或学校登录成功为前提。
- 邮箱登录、设备登录失败，打开 App 或本机密钥丢失均不得自动创建账号。
- 客户端在系统安全存储准备并保管新设备私钥，后台完成专用邮箱注册签名；不上传私钥、学校密码或学校登录 cookie。
- Auth 已有邮件验证、真实签名、主体初始化和 Session 基础；新增密码策略/安全存储/请求处理及 UC011 邮箱列表协议尚未闭合。未满足时不能以无密码注册宣称满足本次修订，不降级成无邮箱注册。
- 匿名注册不要求已有用户 JWS 或 Session；已提供但无效的 Session 不得视为匿名，按 UC011 精确分支鉴权。

### 输入与输出

注册输入、挑战、验证码、密码设置、完成证明与结果包裹由 [UC011 输入与输出](../use-cases/UC-AUTH-011-set-and-activate-email.md#输入与输出)定义。[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)仅是已经交付的不含密码基线，不能当作本次修订完整契约；密码请求字段/版本/证明绑定待设计，不向旧 v2 字节偷偷追加字段。

UC011 复用以下注册结果类型：

```text
UserRegistrationResult {
  authId: AuthId
  credentialId: OpaqueId
  session: SessionEstablished  // 引用 UC007
}
```

CredentialRegistrationProposal 与 proof 引用[设备公钥与签名](../../platform/contracts/auth-device-session-v1.md#公钥与签名)。设备协议仍是 `iwut-device-v1`；邮箱注册待签协议独立为 `iwut-email-registration-v2`，不能混用。

输入不接受客户端指定 authId、accountStatus、developerStatus、permissions、Session 寿命、服务端时间、原始学号、StudentAssociationDeclaration 或任何学校关联摘要。可选一卡通号是 UC005 的资料字段，不作为注册输入，不因退役学号关联而被顺带删除。

### 主流程

1. 用户明确选择邮箱注册并设置平台密码；客户端准备后台设备密钥，说明唯一登录邮箱用于进入/恢复原账号，不上传学校关联信息。
2. 按 UC011 发起 REGISTER，保存邮箱与公钥提案的不可变快照、挑战及邮件操作；Begin 不创建 USER。
3. 用户输入邮件验证码；客户端核对邮箱注册专用待签上下文后在后台签名。
4. Auth 按 UC011 验证邮箱/设备证明、密码策略与注册请求绑定、操作状态、邮箱归属及凭据唯一性。
5. 原子初始化 USER、空 profile、安全密码认证材料、首个邮箱绑定及唯一登录角色、首次凭据与首次 Session，并消费操作、写入最小审计；校园邮箱依据同事务按 UC031 建立。
6. 确认提交后返回结果；客户端保存 Session 与凭据定位信息。已完成或结果未知按 BR-REG-006 恢复，不转成新账号。

### 持久化候选

| 集合 | 作用与约束 |
| --- | --- |
| `auth_principals` | USER 与内嵌 profile，authId 唯一，初始化遵守 BR-REG-002。 |
| `auth_credentials` | 公钥、协议、authId 与状态；credentialId/规范指纹分别唯一，不保存私钥。 |
| `auth_authentication_operations` | 不可变认证快照与一次性消费；不保存学校关联字段或 Session 明文。 |
| `auth_sessions` | UC007 的 Session 权威状态。 |
| 邮箱绑定、操作与发送额度 | UC011 独立拥有，无学生组/成员写入。 |
| 密码认证材料/凭据下界 | UC033 DRAFT 定义 Argon2id/版本/初始化，当前未实现，不存明文或缺字段默认值。 |

TTL 只辅助清理，不能替代业务期限检查或释放公钥唯一占用。校园认证最小 schema 与注册同事务初始化按 UC031 引用，不在本 UC 重定义。

### 异常语义

创建入口统一使用 [UC011 错误语义](../use-cases/UC-AUTH-011-set-and-activate-email.md#错误语义)。无邮箱注册 HTTP 路径不注册、原 RPC 返回 UNIMPLEMENTED，不能重定向到隐式建号或接受旧 REGISTER 证明。旧字段号与名称保留，不复用于新语义。

### 测试与验收

1. 普通邮箱与校园邮箱均可显式注册；邮箱/设备证明及密码策略均满足后，原子建立 USER、密码认证材料、唯一登录邮箱、空资料、后台凭据和首次 Session。
2. Begin、取消、错误/过期验证码、无效签名、缺失/非法密码不创建 USER；不存在无邮箱/无密码旁路和自动注册。
3. 新签名不含关联摘要；旧注册协议/退役字段拒绝，不能通过省略或补零兼容。
4. 并发同操作、同公钥或同邮箱最多完成一个完整账号；审计/提交失败不留半账号。
5. 未知提交与响应丢失可恢复原 authId，不生成新身份；日志无秘密。
6. 未配置关联 ENV、存在旧 ENV 或开发数据库关联集合均不触发关联迁移/核验；新注册不写关联字段和组/成员。
7. 后台设备登录、邮箱登录/新设备登记、高风险证明及账号治理保持原有安全边界；不把无用户感设备密钥误称为删除凭据体系。
8. 邮件、Mongo 事务、真实 HTTP/gRPC、严格消息与向量验收独立进行；客户端和 Gateway 未交付不宣称公网可用。

### 交付依赖与验收边界

- 已交付[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)只证明无学号的邮箱/设备注册基线；本次密码字段、安全处理、版本与请求绑定、公开向量和邮箱列表还须设计/审核后实施，不以旧 v2 回归证明新模型可用。
- UC011 邮件验证及原子初始化、UC007 Session、UC012 邮箱恢复是既有基础；不等待具体应用次数方案才修订 Auth。
- Android/iOS 安全存储、邮箱注册/登录页面、签名前检查和本地清理独立验收。
- 移除关联配置、迁移/核验与写入；没有生产历史迁移任务，不自动删除开发数据。
- 校园认证按修订中的 UC031 当前学校邮箱依据与注册同事务初始化；新修订仍待审核，不在 Auth 发放或扣减权益。

## 业务规则（UC-AUTH-006 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-001 -->
### BR-REG-001：显式创建与平台账号独立

authId 为服务端生成的稳定 opaque 标识，引用 [UC002 数据模型](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#数据模型)；不由邮箱、学号或设备标识派生。注册与登录是明确分开的意图；注册占用邮箱冲突不自动登录旧账号，登录失败不自动注册。

新账号必须通过 UC011 邮箱验证并设置有效平台密码，不提供无邮箱/无密码创建旁路。切换登录邮箱不改变 authId、不重新创建账号；非登录邮箱不能用来找回或登录账号。UC012 的已交付验证码登录基线与未来邮箱＋密码登录的范围仍须明确，不能因为设置密码就悄悄改写普通设备登录证明。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-002 -->
### BR-REG-002：正式主体与最小初始化

创建时 USER/ACTIVE，统一 UTC 提交时间、developerStatus=null、permissions 空、permissionRevision=1；accountRevision=1 及生命周期按 UC022，minimumCredentialRevision=1、密码 passwordRevision=1、首个 credentialRevision=1 按 UC033 同事务初始化。不能等首次登录再补字段。资格/权限仍引用 UC002/004。

profile 初始化严格引用 [BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)及 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。不从学校数据、邮箱或客户端缓存推导资料值。安全密码认证材料、首个已验证邮箱及唯一登录角色、初始设备凭据和首次 Session 属于同一 authId；SYSTEM 不走此入口，注册不授予管理员、Developer 或 Reviewer 身份。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-003 -->
### BR-REG-003：设备凭据持有证明与唯一归属

Auth 使用受支持协议校验公钥和真实私钥持有证明，不能相信客户端 verified 标志。注册同时要求 UC011 邮箱验证码；公钥或设备签名本身不足以创建账号。本产品不额外要求生物识别或用户主动管理密钥；设备签名不证明学校身份、官方客户端或硬件可信等级。

首版一个规范公钥只属于一个 authId，禁止换编码、credentialId 或操作绕过唯一性。相同公钥已登记时，不创建第二账号，也不直接返回已有账号 Session；使用 UC007 的新设备登录证明确认原归属。撤销记录不立即释放公钥，注销占用与清理引用 UC025。

一个 authId 可有多条 credential。新设备生成新密钥，在 UC012 验证原邮箱并证明新私钥后登记；不复制或下载旧私钥。服务端不保存私钥。UC009 撤销凭据、UC008 撤销 Session；设备列表、命名及旧设备授权新增设备仍属后续用例。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-004 -->
### BR-REG-004：停止学号关联上传

注册、登录和恢复不提交或保存原始学号、学号散列、associationToken、associationDigest 或 StudentAssociationDeclaration。学校账号、密码和 cookie 仅供客户端自身功能，不是 Auth 的认证、权益领取或资料校验依据。

Auth 不建立学校账号客户端声明关系，不解析关联组，不把“同学号”当作找回、合并、删除或读取其他账号数据的证明。用户主动上传资料仍按 UC005 校验；一卡通号字段与已经退役的学号关联声明不同。

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-005 -->
### BR-REG-005：账号身份与应用权益边界

账号身份归于 authId，不再存在学生关联组或应用专属学生关联标识。内部服务仅按既有可信身份契约获取获授权的 authId；OAuth 第三方继续按 UC015 的 Application 级 pairwise sub 识别账号，不新增公开原始 authId 的能力。

应用自行维护权益领取、次数余额与消费流水。Auth 不保存或扣减这些次数，不以校园邮箱、学校关联或客户端 KV 作为次数账本。Auth 提供身份及经审核用例和用户授权披露的认证事实，不保证每自然人只能创建一个账号或领取一次权益。更换邮箱不改变原账号及其应用 subject；注销后注册是新账号，不继承旧数据或旧权益。

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

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-011`

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-006 -->
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认 BIND 按账号、REGISTER 按规范公钥指纹控制发送间隔至少 60 秒，两分支共用目标邮箱至少 60 秒的发送间隔；每账号/公钥指纹及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次。匿名注册还复用 BR-REG-007 的未完成挑战容量限制，不以可任意更换的公钥指纹作为唯一防滥用依据；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；独立邮件验证 HMAC 覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较，不与邮箱登录或 JWS 共用秘密。密钥由 ENV 注入；冷更新换钥可使未完成验证码失效，不为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功 BIND 以当前查询恢复状态；已完成 REGISTER 通过设备登录恢复。

学生关联配置、快照和启动离线迁移按 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008) 退役；邮件 HMAC 冷更新仍按本 UC 执行，不能借退役关联而取消邮件操作失效处理。

邮箱明文仅在 Auth 绑定、短期操作及邮件投递中使用；密码不以明文持久化/投递，不进入日志/审计/签名 payload。列表不自动加入 JWS、资料或 Developer 投影。审计仅必要标识/版本/时间/结果，不含邮箱、密码、验证码或 token；操作在窗口后清理。

<!-- 权威位置: use-cases/UC-AUTH-011-set-and-activate-email.md#br-eml-009 -->
### BR-EML-009：邮箱注册的原子创建

REGISTER 复用 UC006 主体初始化/凭据归属，首次 Session 复用 UC007。邮箱与设备证明、密码策略/安全认证材料均满足前，不创建临时 USER、不建立设备归属、不占用登录邮箱。

一次 Mongo 事务提交 USER、安全密码认证材料、初始设备凭据/Session、首个已验证邮箱及唯一登录角色、必要归属/版本、操作消费/审计；不写关联组。任何失败回滚，不顺序建号再补密码/邮箱。邮件在事务外，初始令牌仅确认提交后返回；学校邮箱依据与当前认证投影按 UC031 同事务闭合，认证/审计失败回滚注册。

每个规范公钥指纹只允许一个当前待验证 REGISTER 提案；同密钥重发使旧提案失效，不影响其它密钥，不按收件地址作废他人挑战。已登记公钥不能给旧账号补绑邮箱或创建第二账号。并发邮箱注册依靠凭据/邮箱唯一性确保唯一归属；失败方先通过 UC007 登录确认结果，再以 Session 发起 BIND，不能把注册码用于旧账号绑定。无邮箱注册接口不可用。

被占用邮箱或公钥冲突不留下半创建账号；“有 Session 绑定、无 Session 显式注册”的选择只在 Begin 固定，后续不能重新推断目标。不接收学校声明定位旧账号或授予权益。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-009 -->
### BR-LGN-009：认证入口的失败与披露边界

Begin/Complete 需要请求大小、挑战尝试次数、创建速率和未完成操作容量限制；按来源/操作/凭据等维度组合，不信任客户端设备 ID。初始参数如下，必须在上线前配置校验，不由学生关联分组代替。

认证入口工程默认值：解压后消息上限 16 KiB、单挑战最多 5 次失败、全局 Begin 每分钟 600 次、全局 Complete 每分钟 1200 次、同来源 Begin 每分钟 30 次、同定位 Complete 每分钟 60 次、未完成挑战最多 10000 条。参数可配置但必须有限且为正，非法配置拒绝启动；总体容量和全局限速即使来源不可确认也必须生效。未知 operationId 的 Complete 同样计入全局 Complete 限流，不能通过制造新定位或未知操作绕过总量保护。来源默认使用受信网络对端，不信任终端自填 forwarded header；Gateway 精细来源限流以后通过受信转发契约接入。挑战次数和未完成容量在 Auth 持久化层原子确认；单进程速率桶允许重启清空，不称为跨重启风控。每来源及每定位桶的存储必须有有限容量、过期淘汰和容量耗尽策略，不能因任意客户端定位形成无限内存增长；即使无法新增细分桶，全局限流仍须生效。

错误不区分未知账号、已撤销凭据、错误签名与账号禁用的具体身份事实。依赖不可用与错误凭据区分，便于客户端重试而不是误创建账号。对外不返回账号是否绑定邮箱、关联组成员、内部验签细节或堆栈。

认证请求/响应正文不进入常规日志；禁止记录 token、完整挑战/证明或任何私钥。操作元数据可以记录 operationId、sessionId、结果和时间，已确认身份后才记录可信 authId。Session 不含用户资料，认证事件不广播敏感声明。

### 来自 `UC-AUTH-033`

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-001 -->
### BR-PWD-001：密码来源、策略与初始化

平台密码独立于学校/邮箱口令和设备私钥。新注册在 UC006/011 同事务初始化密码；不允许无密码账号创建后再补齐，不从邮箱验证码、随机 Session 或客户端缓存派生密码。

首版：有效 UTF-8，统一 NFC 规范化后按 Unicode code point 计数 15..128，规范化后最多 512 字节，输入规范化前最多 1024 字节；不 trim、折叠大小写或截断，空格属于密码。所有设置/校验路径采用相同规范化版本，支持粘贴/密码管理器；拒绝常见、预期及已泄露密码的完整匹配，不强制大小写/数字/符号组合，不定期强制改密。新密码不得等于当前密码，失败不消费有效重置码或改动认证状态。

策略包含版本化本地 blocklist，部署明确装载、校验并在启用前压测；不能用测试 fixture、空列表或在线上送明文密码的接口代替。具体生产列表内容/发布流程列为启用门禁。

策略依据 [NIST 密码规则](https://pages.nist.gov/800-63-4/sp800-63b.html#passwords)；本平台的 128 上限/NFC/产品角色是已接受平台约束，不宣称满足 NIST 全部认证等级。

### 来自 `UC-AUTH-005`

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008 -->
### BR-UPF-008：资料初始化与乐观并发

普通 USER 创建时初始化逻辑空资料，values 为空，revision 为 1，profile.updatedAt 等于主体 createdAt；本编辑用例只处理已经完成初始化的主体。

expectedRevision 必填且为正 int64。当前版本不匹配则冲突，即使目标值与现有值相同。每次真实变化将 revision 精确增加 1，并将 profile.updatedAt 设为服务端本次提交使用的 UTC 时间；时间戳不承担并发比较，也不保证因时钟调整严格递增。

revision 属于整份资料，与权限版本、目录版本和认证版本相互独立。任何写 profile 的生产路径都遵循本规则，不能绕过版本更新。revision 达到 int64 最大值时拒绝真实变更并报告耗尽，不回绕；合法 no-op 仍可返回原版本。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010 -->
### BR-UPF-010：主体内嵌资料与单文档原子提交

基础资料内嵌在 Auth 自有 `auth_principals.profile` 中。USER 的账号状态和资料版本处于同一 document；字段目录独立共享，Session、consent、应用存储和追加式审计不作为此 profile 的组成部分。

仓储把逻辑 KV 保存为有界 `entries` 数组，每项为 `{key, valueType, value}`，按 key 的 ASCII 字典序存放且 key 唯一。key 是数据值，不作为 Mongo 更新路径；带点的名称不会被解释成嵌套字段。STRING/DATE 保存为 BSON string、INTEGER 为 BSON int32、BOOLEAN 为 BSON bool，STRING_SET 保存为规范排序的 BSON string array，ACADEMIC_GRADE 保存为带 stage/year/finalYear/academicYear/confirmedAt 的封闭 object；DATE 由 valueType 区分。仓储读取时拒绝重复 key、未知存储类型、非规范集合或损坏的 profile 元数据，不静默合并或丢弃。

profile.revision 使用 BSON int64，profile.updatedAt 使用 BSON datetime。存储类型、key 语法、标量基本格式和元数据有效性属于结构校验；对未修改的历史值不重复应用当前字段目录的业务约束。内嵌 profile 不重复保存 authId，其归属由外层主体确定。

真实变更使用一次条件更新匹配 `authId + principalType=USER + accountStatus=ACTIVE + profile.revision=expectedRevision`，在同一次操作中写入候选 entries、新 revision 和 profile.updatedAt。禁止 upsert、整份主体替换、由客户端 key 拼接 `$set` 路径，或把部分条目分别提交。

该操作只改变 profile，不覆盖权限、Developer 状态、主体顶层 updatedAt 等其他事实。profile 的变化不能因为权限更新而被丢失，权限更新也不能用旧主体快照覆盖 profile。底层单文档原子性依据见 [MongoDB Atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/)。

若条件更新匹配数为 0，不报告成功，也不自动换版本重试；可通过新的权威读取区分主体不存在、非 USER、DISABLED 和版本冲突。若此时状态已再次变化而无法精确归因，返回并发冲突让客户端重读，不猜测成功。数据库异常返回不可用，未知提交结果按 BR-UPF-009 处理。

禁用先于本次条件更新生效时，本次写入失败；资料更新先完成则可以成功，之后的禁用不撤销已经提交的资料。这是本用例的并发边界，不提供跨所有会话的即时失效承诺。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### 范围与权威来源

本契约固定官方客户端、Auth Center 与未来 Gateway 接入共同使用的字节格式。业务规则由 [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md)、[UC-AUTH-007](../use-cases/UC-AUTH-007-login.md)、[UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md)、[UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 拥有；本文件不引入邮箱恢复、设备迁移或新的身份签发能力。

2026-10-12：无邮箱 REGISTER/学号关联已退役，邮箱 v2 基线已交付，本文件继续规范后台设备 LOGIN/Session/撤销。UC006/011 邮箱 v3 已接受并实施，UC009 防旁路修订已接受；不改变 LOGIN 字节，不据旧向量开放注册或宣称密码注册已经完成。v2 不含密码，不是完整新注册契约。

首版选择是 App 管理设备密钥。协议只证明私钥控制权，不声称验证官方客户端、学校身份、硬件等级或生物识别。签名中的 applicationId 用于隔离上下文，不是 App attestation。

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

#### RPC 鉴权表

Auth 原生 gRPC 新接口固定为以下 full method；可执行 Proto 在独立 API 仓库。middleware 按精确方法表分派，未知方法默认拒绝，不能把整个 package 标成匿名。

| full method | 认证与授权 |
| --- | --- |
| `/auth_center.v1.authentication.AuthenticationService/BeginUserRegistration` | 退役；UNIMPLEMENTED，不创建挑战或账号。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteUserRegistration` | 退役；UNIMPLEMENTED，不消费旧证明创建账号。 |
| `/auth_center.v1.authentication.AuthenticationService/BeginDeviceLogin` | 有界匿名；创建 LOGIN 挑战。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteDeviceLogin` | 有界匿名；仅挑战与私钥证明可建立 Session。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeCurrentSession` | 仅 token 定向撤销；必须绕过普通“当前 Session 有效”前置检查，按 UC008 幂等处理。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeOwnCredential` | UC009 已交付：有效 Session/ACTIVE，仅当前凭据；其他目标 403 CREDENTIAL_REAUTH_REQUIRED，由 UC032 当前密码＋当前钥证明处理。 |
| `/auth_center.v1.user_profile.UserProfileService/EditOwnProfile` | trusted-identity-v1 用户 JWS，audience 为 `iwut-auth-center`；按 UC005 再查当前主体。 |
| `/auth_center.v1.user_profile.UserProfileService/GetOwnProfile` | 同上。 |
| `/auth_center.v1.user_profile.UserProfileService/GetProfileEditingSchema` | 同上。 |
| `/auth_center.v1.session_management.SessionManagementService/ListOwnSessions` | 有效 Session，ACTIVE USER；UC020 只读管理检查不 touch LRU，同 authId 有界分页。 |
| `/auth_center.v1.session_management.SessionManagementService/RevokeOwnSessions` | 有效 Session，ACTIVE USER；UC020 最终事务复核、原子回收明确 ID 集合，禁止包含当前 Session。 |
| 既有 Scope/Developer/SystemPrincipal 方法 | 保持 trusted-service-identity-v1 与各自固定 permission/purpose allowlist。 |

同一调用只依据该方法规定的认证类型授权，不接受其它类型替代。会话撤销请求不因携带一个失效用户 JWS 而失去幂等性；匿名证明接口也不因附带身份获得额外权限。所有认证材料均需脱敏。客户端请求中声明的 authId、角色、设备名称或 applicationId 不生成可信 context。

UC009 当前凭据撤销后旧 Session 重试 SESSION_INVALID；其他有效 Session 只能经 UC032 密码＋签名流程确认该其他目标，不能直接用旧入口。目标状态幂等与在途边界仍引用 UC009；新收紧逻辑未实施，不以本文修订冒称已修复。

#### 实现配置与验收边界

Session 寿命、认证限额、MongoDB 并发实现与保留策略由 [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) 拥有；本契约只固定相互通信所需的格式和认证方法。并行工作包共用同一套端口和持久化约定。

本轮后端验收包括真实协议验证器、正反测试向量、生成 Proto、原生 gRPC、生产组合根与真实 Mongo 副本集上的事务/撤销测试。Android/iOS 私钥安全存储、客户端界面与恢复体验由客户端独立验收；Gateway 路由、在线 Session 到身份 JWS 签发仍为后续工作。不得用测试签名密钥或 fake verifier 代替生产认证，不把后端测试通过描述为移动端及公网调用已贯通。

#### 测试向量

确定性编码、关联 token、公钥指纹、REGISTER/LOGIN 签名验证、Session 摘要和关联认证加密样例见 [auth-device-session-v1.json](../../platform/contracts/test-vectors/auth-device-session-v1.json)。签名可以使用随机 nonce，因此验签结果固定，不要求生产端每次产生与样例相同的 DER 字节。负例必须覆盖错误 purpose/serviceId/locator、双重哈希、错误 DER、公钥编码、token 别名和前导零丢失。

此文件是既有互操作历史向量；新实现仅复用其中仍有效的 LOGIN/公钥/Session 用例，REGISTER 与关联正例不代表当前业务可用。必须另验收旧注册 RPC/路径拒绝和 LOGIN 空保留槽严格校验，不重写历史向量为新注册协议。

生成与验证脚本位于 [tools/auth_protocol_vectors.py](../../tools/auth_protocol_vectors.py)。脚本中的私钥和服务端密钥是公开测试数据，只能用于向量；不得作为生产默认配置。

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

- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：变更记录
- `UC-AUTH-011`（use-cases/UC-AUTH-011-set-and-activate-email.md）：目标与范围、参与者与前置条件、输入与输出、主流程、错误语义、测试与验收、实现约定、交付依赖与边界、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-033`（use-cases/UC-AUTH-033-manage-password-and-recovery.md）：目标与范围、参与者与依赖、输入与输出、主流程、验收与错误边界、交付依赖与变更记录
- `UC-AUTH-005`（use-cases/UC-AUTH-005-edit-own-user-profile.md）：目标与范围、参与者与前置条件、输入、输出、主流程、持久化与返回说明、异常与 transport 映射、API 与交付依赖、测试与验收、非目标、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：学号关联声明、变更记录
- `platform/contracts/auth-email-account-v3.md`（docs 根级共享文档）：实施证据与公开向量（2026-10-13）

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-006-create-user.md` | 171 | `e30e98fe13c9` |
| `use-cases/UC-AUTH-011-set-and-activate-email.md` | 299 | `39d8427ba29e` |
| `use-cases/UC-AUTH-007-login.md` | 256 | `37041f11441d` |
| `use-cases/UC-AUTH-033-manage-password-and-recovery.md` | 171 | `12caeedc7b93` |
| `use-cases/UC-AUTH-005-edit-own-user-profile.md` | 340 | `a2e87a33efad` |
| `platform/contracts/auth-device-session-v1.md` | 118 | `ec97f26c28b8` |
| `platform/contracts/auth-email-account-v3.md` | 126 | `b13b360d803f` |
