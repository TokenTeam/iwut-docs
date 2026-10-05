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
| 外部引用 BR | `BR-ACC-012`，`BR-DEV-004`，`BR-LGN-002`、`BR-LGN-003`、`BR-LGN-009`、`BR-LGN-011`，`BR-UPF-008`、`BR-UPF-010`（来自 `UC-AUTH-002`、`UC-AUTH-005`、`UC-AUTH-007`、`UC-AUTH-025`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md` |

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

> 已在客户端本地保存学校账号密码的用户，明确选择创建平台账号，提交学校账号关联声明并通过新设备凭据的持有证明，建立正式 USER 主体并获得首次登录会话；邮箱和学生资料不作为注册前提。

本文件是创建行为与 `BR-REG-*` 的唯一规则正文。凭据证明、关联声明和认证载体遵守已接受的 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)；设计接受不表示后端、客户端或 Gateway 已交付。

首版设备凭据确定为 App 管理生命周期、由操作系统安全存储保护的设备公私钥，不采用标准 WebAuthn Passkey，也不依赖系统账号或密码管理器同步。私钥应由系统密钥设施生成并尽可能不可导出；“App 管理”是指 App 决定创建、使用和删除，不表示把明文私钥写入普通文件、偏好设置或业务数据库。算法和签名协议引用[公钥与签名契约](../../platform/contracts/auth-device-session-v1.md#公钥与签名)，客户端安全存储独立验收。

本用例不绑定邮箱、不设置平台密码、不恢复或合并旧账号、不认证学生真实性，不开放第三方资料读取，不签发服务间身份 JWS。Session 的共享规则由 [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) 定义。

### 参与者与前置条件

- 客户端已上线并提供无需平台后端的功能；用户进入平台注册页面前，已在本地完成学校账号密码的保存。平台注册是后续独立动作，不是使用这些既有本地功能的前提。
- 用户在客户端看见独立的“创建平台账号”动作并明确确认；不能仅因打开 App、学校登录成功或平台登录失败而自动注册。
- 客户端能根据本次选择的本地学校账号生成关联声明，注册必须提交；具体规则见 [BR-REG-004](../use-cases/UC-AUTH-006-create-user.md#br-reg-004) 和 [BR-REG-005](../use-cases/UC-AUTH-006-create-user.md#br-reg-005)。本地保存状态是客户端流程前提，不作为服务器已验证学校身份的证据。
- 客户端能在系统安全存储中创建并持久保管本次新设备凭据，能够完成已发布认证协议的签名证明及不可逆删除本机私钥。学校账号密码、学校登录 cookie 不发给 Auth。
- Auth 已配置支持的凭据协议、挑战策略和 Session 策略；缺少配置时相应入口不接流量。
- 创建入口允许尚无平台 Session 的用户访问；通过注册挑战和持有证明建立身份，不要求预先提供 trusted-identity-v1，也不依赖“来自官方 App”的声明放行。

### 输入与输出

以下是逻辑消息，不是已发布的 Proto 或 HTTP 线格式。

```text
BeginUserRegistration {
  credentialProposal: CredentialRegistrationProposal
  association: StudentAssociationDeclaration  // 必填，见 BR-REG-005
}

RegistrationChallenge {
  operationId: OpaqueId
  challenge: Bytes
  signingPayload: Bytes
  protocolVersion: string
  expiresAt: Instant
}

CompleteUserRegistration {
  operationId: OpaqueId
  proof: CredentialRegistrationProof
}

UserRegistrationResult {
  authId: AuthId
  credentialId: OpaqueId
  session: SessionEstablished  // 引用 UC-AUTH-007，不另定义令牌格式
}

StudentAssociationDeclaration {
  schemeVersion: string
  associationToken: Bytes
}
```

credentialProposal/proof 的具体字段、公钥编码和算法引用[公钥与签名](../../platform/contracts/auth-device-session-v1.md#公钥与签名)，signingPayload 引用[挑战与待签消息](../../platform/contracts/auth-device-session-v1.md#挑战与待签消息)，不得把此处的抽象类型实现成“接收任意 JSON 并信任客户端 verified=true”。Begin 的公钥提案、关联声明及其显式提交意图在 Auth 侧形成不可变操作快照；Complete 不能替换这些内容。

不接受客户端指定 authId、accountStatus、developerStatus、permissions、associationId、Session 寿命或服务器时间。关联声明不能带学校密码或原始学号；主动上传资料走 UC-AUTH-005，不能借注册混入 profile。

### 主流程

1. 用户从已保存学校账号的客户端进入注册页，选择创建新平台账号；客户端持久准备平台设备凭据，生成对应学校账号的关联声明，并说明账号恢复能力及关联信息的用途。
2. Begin 校验提案、关联声明和入口限额，创建 purpose 为 REGISTER 的操作快照与挑战；挑战规则引用 [BR-LGN-002](../use-cases/UC-AUTH-007-login.md#br-lgn-002)。此时不创建 USER。
3. 客户端完成明确的注册确认，使用新私钥生成注册证明；本产品不要求额外生物识别，所选系统 API 必需的交互仍须遵从。
4. Complete 验证挑战、绑定内容和私钥持有证明，按 BR-REG-003 检查凭据唯一性；仅收到公钥不能注册成功。
5. Auth 生成新的 authId，初始化主体与空资料；按 BR-REG-004/005 解析或建立关联组，准备本次账号的关联绑定。
6. 依照 BR-REG-006，在一次原子提交中消费挑战，创建 USER、首个凭据、首次 Session、必需的账号关联绑定、必要的新关联组和操作完成记录。
7. 返回成功结果；客户端安全保存 Session 令牌，进入普通用户功能。Session 规则引用 [BR-LGN-003](../use-cases/UC-AUTH-007-login.md#br-lgn-003)。

无邮箱不使账号成为临时主体。普通用户可以立即调用仅要求有效 USER 身份的功能；需要 Developer 资格、人员权限、应用授权或特定配额条件的能力仍分别检查，注册不隐式授予它们。

### 持久化候选

| 集合 | 作用与约束 |
| --- | --- |
| `auth_principals` | 原有主体与内嵌 profile；authId 唯一。 |
| `auth_credentials` | 设备公钥、协议版本、authId、状态、创建/撤销时间；credentialId 与规范公钥指纹分别唯一；私钥不入库。 |
| `auth_authentication_operations` | BR-LGN-002 的不可变绑定、期限、尝试/消费状态与完成引用；REGISTER 快照的 token 密文及清理见 BR-REG-008，不持久化明文 associationToken 或 Session 令牌。 |
| `auth_sessions` | 结构和令牌规则由 UC-AUTH-007 拥有。 |
| `auth_student_associations` | associationId 唯一；每组一份版本化 lookupKey 与 token 认证加密密文，字段及唯一索引见 BR-REG-008；不维护在线轮换别名。 |
| `auth_student_association_members` | authId 到 associationId 的绑定和 CLIENT_ASSERTED 信任等级；authId 唯一。 |

这些集合是初版物理候选。短期挑战清理由 TTL 等机制辅助，但不能用异步删除代替服务端期限检查。注册提交后删除/过期操作记录也不能释放凭据唯一性，避免迟到重试创建第二账号。

### 异常语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 提案不合法，或关联声明缺失/null/为空/结构不合法 | `INVALID_REGISTRATION_INPUT` | 400 / INVALID_ARGUMENT |
| 凭据协议或关联方案未支持 | `REGISTRATION_SCHEME_UNSUPPORTED` | 400 / INVALID_ARGUMENT |
| 挑战无效、过期、绑定不符、证明无效 | `REGISTRATION_PROOF_INVALID` | 401 / UNAUTHENTICATED |
| 相同操作已经完成 | `REGISTRATION_ALREADY_COMPLETED` | 409 / ALREADY_EXISTS |
| 公钥已绑定账号 | `CREDENTIAL_ALREADY_REGISTERED` | 409 / ALREADY_EXISTS |
| 入口限额耗尽 | `REGISTRATION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 解压后消息/证明超出限制 | `REGISTRATION_INPUT_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 持久化/认证配置暂不可用或提交结果未知 | `REGISTRATION_UNAVAILABLE` | 503 / UNAVAILABLE |

客户端不靠 message 文本判断下一步；底层畸形消息至少使用对应标准状态。公钥重复结果不返回既有账号资料或登录令牌。不可用不等于确定回滚，按 BR-REG-006 恢复。

### 测试与验收

1. 已有本地学校账号、提供有效关联声明但无邮箱/资料的明确注册，建立 ACTIVE USER、空资料、一个凭据、一个关联组绑定和首次 Session；不授予任何特权。
2. Begin、用户取消、挑战过期和无效签名均不创建 USER；学校登录不触发静默注册。
3. 替换公钥、关联绑定、operation purpose、协议版本或挑战时证明失败；客户端 verified 标志无效。
4. 相同 operation 并发最多一个完整提交；不同 operation 使用同一公钥不产生第二账号。
5. 各阶段失败注入验证多文档全部提交或回滚；未知提交/丢失成功响应后保留私钥，能通过新登录恢复同一 authId。
6. 同声明不同公钥产生不同 authId、同一关联组；不同声明分组不同；请求不接受客户端选择学校；并发首次关联只有一个组。
7. association 缺失/null、必需字段缺失/为空/非法在 Begin 创建挑战前失败；关联存储失败不留下无关联 USER，Complete 不能更换声明。关联不修改 profile、不授予所有权，不返回其他账号或对外关联 ID。
8. 未支持的协议、超大输入、限流、耗尽的挑战尝试和损坏配置均失败关闭；日志检查无秘密泄漏。
9. 后端使用真实 Mongo 事务、真实 transport、真实验证器及共享协议向量验证；客户端安全存储独立验收，不能只用 fake verifier 证明生产认证可用。
10. 客户端进入注册页前已有本地学校账号，只有明确注册才提交派生关联信息；取消或失败不删除学校凭据、不影响既有本地功能，也不上传学校密码或原始学号。
11. 轮换在旧进程停服并排空写入后、由新进程接收业务请求前执行；迁移/核验未完成不得报告 ready，失败则退出。迁移前创建但未完成的 REGISTER 操作不能在恢复后继续完成，已完成操作仍不能重放创建账号；仅当前 ENV 的日常启动保留有效的当前版本挑战。
12. 每批最多 500 条 ordered bulkWrite，覆盖末批不足 500 条、批次部分成功、更新数量不符、任意记录更新前后中断或响应丢失。使用同一源/目标配置重新启动后分组与成员保持不变；已到目标版本的记录不重复更新，两次连续完整轮换后不依赖第一代运行密钥。
13. 错误密钥、篡改密文/标签/nonce/AAD、未知版本或 lookupKey 不符时失败关闭，原记录不被覆盖；半迁移状态不能恢复正常服务。验证移除旧 ENV 后目标版本数据仍可注册关联到原组。
14. 在接近生产的 MongoDB 上测量完整迁移与核验耗时；覆盖旧备份恢复后的版本检查，不以纯密码运算基准代替维护窗口验收。

### 交付依赖与验收边界

- 后端按[共享协议](../../platform/contracts/auth-device-session-v1.md)交付真实验证器、生成 Proto、原生 gRPC 与测试向量；算法、公钥规范化和签名报文不由各工作包自行定义。
- Android/iOS 安全存储、最低兼容版本、签名前检查、关联声明披露及可靠删除由客户端独立验收；后端测试不替代移动端验收。
- Mongo 原子注册、启动前离线密钥迁移及故障测试由本工作包交付。编码遵循 BR-REG-008，正式环境维护窗口仍须部署验收。
- 挑战与入口限额引用 UC-AUTH-007；Session 寿命由有效的 AUTH_SESSION_TTL 部署配置决定。
- API 包为 `auth_center/v1/authentication/`，方法与 middleware 遵守共享契约的 RPC 鉴权表；TLS 部署、Gateway 路由和身份签发另行交付。

## 业务规则（UC-AUTH-006 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-001 -->
### BR-REG-001：显式创建与平台账号独立

一次明确创建意图对应一个新 USER 主体。authId 是服务端生成的稳定 opaque 标识，沿用 [UC-AUTH-002 数据模型](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#数据模型)；不使用邮箱、学号、关联组或设备标识作为 authId。

学校账号、本机平台账号、平台认证凭据三者独立。相同学校声明可对应多个 authId，不据此复用、合并、覆盖或删除旧账号。已有账号登录入口认证失败时不得静默转成创建流程。

客户端首次注册即说明本机凭据丢失后的恢复限制，并提供以后绑定恢复方式的入口；不能等到主动退出时才告知。实际邮箱绑定和恢复另立用例，未交付前不能展示为已可用。

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

### 来自 `UC-AUTH-002`

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004 -->
### BR-DEV-004：状态语义

公开 `PENDING/APPROVED/REJECTED/SUSPENDED/WITHDRAWN`。UC-APP-005 只把
`SUSPENDED` 判断为暂停，但 Auth 返回完整枚举，让消费方不需要用 bool 掩盖未知状态。

CLOSED 墓碑作为明确终止状态返回是本规则的例外，不将其伪装成 PENDING 或 WITHDRAWN。

普通 USER 可以不是 Developer，此时 `developerStatus = null`；SYSTEM principal 也不具有
Developer 状态。两者都不能作为本查询的成功结果，且不得被伪装成 `PENDING`。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-002 -->
### BR-LGN-002：挑战绑定与一次性证明

注册和登录均使用 Auth 生成的密码学随机挑战及不可变操作记录。首版挑战具有 256 bit 随机性，寿命固定为 5 分钟；编码和上下文遵守共享契约。服务端以自己的时间检查过期，不依赖 TTL 清理是否已发生。

挑战记录绑定 purpose（REGISTER/LOGIN）、operationId、协议版本、服务标识、允许的应用/来源上下文，以及完整的注册提案快照或登录凭据定位。注册关联声明以受控摘要绑定，存储边界引用 BR-REG-004。签名/协议证明须覆盖挑战及规定上下文，不能跨用途、账号、凭据或服务重放；客户端不能在 Complete 改写 Begin 的输入。

每个 operation 的成功消费与业务提交原子发生。失败尝试需要有界计数及最终关闭状态，随机 operationId 本身不是认证凭证。并发提交不能多次消费，超时或网络重试不能延长挑战寿命；无效证明不修改账号、凭据或建立会话。

未知凭据的 Begin 应返回与已知凭据兼容的普通挑战或统一响应，不提供账号存在性和状态查询；Complete 统一失败。单凭持有挑战/定位摘要不能登录。挑战签名成功仅证明密钥控制权，不自动证明客户端未被篡改、硬件安全等级或生物识别已执行；相关声明须由所选协议的可验证证据支持。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-003 -->
### BR-LGN-003：会话权威与秘密令牌

Auth 保存 Session 权威状态，每个 Session 只对应一个 authId。sessionId 是非秘密的记录标识，sessionToken 是 CSPRNG 生成、至少 256 bit 随机性的 bearer secret；二者不得互相替代。令牌不编码学号、邮箱、权限或用户资料，不要求 JWT。

token 线格式、摘要输入和认证载体引用[Session 载体契约](../../platform/contracts/auth-device-session-v1.md#session-载体)。服务端持久化 token 的 SHA-256 摘要并建立唯一索引，不保存明文令牌；高熵随机令牌不同于低熵密码，不从密码/学号派生。客户端通过 TLS 传输并安全存储令牌，不在 URL、普通日志、分析事件或崩溃报告中包含它。拥有有效 bearer token 即可使用会话，本规则不宣称自动具有设备持有证明或防重放能力。

每条 Session 记录本次认证方法、凭据引用（设备认证时必填）、authenticatedAt、createdAt、lastUsedAt、expiresAt、撤销状态与时间。lastUsedAt 的使用与更新规则见 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010)。Session 不包含私钥，不被 profile、学生关联或客户端设备名称决定归属。以后添加邮箱方法时必须扩展明确的认证记录语义。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-009 -->
### BR-LGN-009：认证入口的失败与披露边界

Begin/Complete 需要请求大小、挑战尝试次数、创建速率和未完成操作容量限制；按来源/操作/凭据等维度组合，不信任客户端设备 ID。初始参数如下，必须在上线前配置校验，不由学生关联分组代替。

认证入口工程默认值：解压后消息上限 16 KiB、单挑战最多 5 次失败、全局 Begin 每分钟 600 次、全局 Complete 每分钟 1200 次、同来源 Begin 每分钟 30 次、同定位 Complete 每分钟 60 次、未完成挑战最多 10000 条。参数可配置但必须有限且为正，非法配置拒绝启动；总体容量和全局限速即使来源不可确认也必须生效。未知 operationId 的 Complete 同样计入全局 Complete 限流，不能通过制造新定位或未知操作绕过总量保护。来源默认使用受信网络对端，不信任终端自填 forwarded header；Gateway 精细来源限流以后通过受信转发契约接入。挑战次数和未完成容量在 Auth 持久化层原子确认；单进程速率桶允许重启清空，不称为跨重启风控。每来源及每定位桶的存储必须有有限容量、过期淘汰和容量耗尽策略，不能因任意客户端定位形成无限内存增长；即使无法新增细分桶，全局限流仍须生效。

错误不区分未知账号、已撤销凭据、错误签名与账号禁用的具体身份事实。依赖不可用与错误凭据区分，便于客户端重试而不是误创建账号。对外不返回账号是否绑定邮箱、关联组成员、内部验签细节或堆栈。

认证请求/响应正文不进入常规日志；禁止记录 token、完整挑战/证明或任何私钥。操作元数据可以记录 operationId、sessionId、结果和时间，已确认身份后才记录可信 authId。Session 不含用户资料，认证事件不广播敏感声明。

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-011 -->
### BR-LGN-011：登录触发与客户端边界

Auth 不区分本次登录由用户点击、应用启动、Session 到期还是业务请求恢复触发；所有调用都必须执行相同的挑战、私钥持有证明、账号/凭据复核、限流和 Session 创建规则。客户端的 `automatic=true`、`userConfirmed=true` 或类似声明不构成认证证据，也不改变服务端权限。

首版 App 管理设备密钥的服务端协议不要求生物识别、设备 PIN 或额外点击的证明；它只证明对应私钥控制权。操作系统安全存储若要求本地交互，客户端必须遵从，但 Auth 不接收无法验证的布尔声明。客户端何时自动调用、如何合并并发登录、退出后是否继续尝试及如何删除本地秘密不属于本 UC 的服务端后置条件。

每次成功调用都创建一条新 Session，并受 BR-LGN-010 的 10 条上限和 LRU 约束；不得用自动触发名义绕过限流或无限创建 Session。Session 建立不授权客户端自动重放结果未知的业务写命令，业务重试遵守对应命令的幂等规则。

### 来自 `UC-AUTH-005`

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008 -->
### BR-UPF-008：资料初始化与乐观并发

普通 USER 创建时初始化逻辑空资料，values 为空，revision 为 1，profile.updatedAt 等于主体 createdAt；本编辑用例只处理已经完成初始化的主体。

expectedRevision 必填且为正 int64。当前版本不匹配则冲突，即使目标值与现有值相同。每次真实变化将 revision 精确增加 1，并将 profile.updatedAt 设为服务端本次提交使用的 UTC 时间；时间戳不承担并发比较，也不保证因时钟调整严格递增。

revision 属于整份资料，与权限版本、目录版本和认证版本相互独立。任何写 profile 的生产路径都遵循本规则，不能绕过版本更新。revision 达到 int64 最大值时拒绝真实变更并报告耗尽，不回绕；合法 no-op 仍可返回原版本。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010 -->
### BR-UPF-010：主体内嵌资料与单文档原子提交

基础资料内嵌在 Auth 自有 `auth_principals.profile` 中。USER 的账号状态和资料版本处于同一 document；字段目录独立共享，Session、consent、应用存储和追加式审计不作为此 profile 的组成部分。

仓储把逻辑 KV 保存为有界 `entries` 数组，每项为 `{key, valueType, value}`，按 key 的 ASCII 字典序存放且 key 唯一。key 是数据值，不作为 Mongo 更新路径；带点的名称不会被解释成嵌套字段。STRING/DATE 保存为 BSON string、INTEGER 为 BSON int32、BOOLEAN 为 BSON bool；DATE 由 valueType 区分。仓储读取时拒绝重复 key、未知存储类型或损坏的 profile 元数据，不静默合并或丢弃。

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

#### RPC 鉴权表

Auth 原生 gRPC 新接口固定为以下 full method；可执行 Proto 在独立 API 仓库。middleware 按精确方法表分派，未知方法默认拒绝，不能把整个 package 标成匿名。

| full method | 认证与授权 |
| --- | --- |
| `/auth_center.v1.authentication.AuthenticationService/BeginUserRegistration` | 有界匿名；校验输入与容量，创建 REGISTER 挑战。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteUserRegistration` | 有界匿名；仅挑战与私钥证明可完成注册。 |
| `/auth_center.v1.authentication.AuthenticationService/BeginDeviceLogin` | 有界匿名；创建 LOGIN 挑战。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteDeviceLogin` | 有界匿名；仅挑战与私钥证明可建立 Session。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeCurrentSession` | 仅 token 定向撤销；必须绕过普通“当前 Session 有效”前置检查，按 UC008 幂等处理。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeOwnCredential` | 有效 Session，ACTIVE USER；以可信 authId 检查目标凭据归属，执行 UC009。 |
| `/auth_center.v1.user_profile.UserProfileService/EditOwnProfile` | trusted-identity-v1 用户 JWS，audience 为 `iwut-auth-center`；按 UC005 再查当前主体。 |
| `/auth_center.v1.user_profile.UserProfileService/GetOwnProfile` | 同上。 |
| `/auth_center.v1.user_profile.UserProfileService/GetProfileEditingSchema` | 同上。 |
| 既有 Scope/Developer/SystemPrincipal 方法 | 保持 trusted-service-identity-v1 与各自固定 permission/purpose allowlist。 |

同一调用只依据该方法规定的认证类型授权，不接受其它类型替代。会话撤销请求不因携带一个失效用户 JWS 而失去幂等性；匿名证明接口也不因附带身份获得额外权限。所有认证材料均需脱敏。客户端请求中声明的 authId、角色、设备名称或 applicationId 不生成可信 context。

UC009 撤销当前认证凭据后，再用原 Session 重试会得到 SESSION_INVALID；“幂等撤销已撤销凭据成功”以前置有效 Session 为限。其它仍有效 Session 可重复撤销同一目标。认证检查成功后的在途撤销请求按 UC007 的检查时间边界处理。

#### 实现配置与验收边界

Session 寿命、认证限额、MongoDB 并发实现与保留策略由 [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) 拥有；本契约只固定相互通信所需的格式和认证方法。并行工作包共用同一套端口和持久化约定。

本轮后端验收包括真实协议验证器、正反测试向量、生成 Proto、原生 gRPC、生产组合根与真实 Mongo 副本集上的事务/撤销测试。Android/iOS 私钥安全存储、客户端界面与恢复体验由客户端独立验收；Gateway 路由、在线 Session 到身份 JWS 签发仍为后续工作。不得用测试签名密钥或 fake verifier 代替生产认证，不把后端测试通过描述为移动端及公网调用已贯通。

#### 测试向量

确定性编码、关联 token、公钥指纹、REGISTER/LOGIN 签名验证、Session 摘要和关联认证加密样例见 [auth-device-session-v1.json](../../platform/contracts/test-vectors/auth-device-session-v1.json)。签名可以使用随机 nonce，因此验签结果固定，不要求生产端每次产生与样例相同的 DER 字节。负例必须覆盖错误 purpose/serviceId/locator、双重哈希、错误 DER、公钥编码、token 别名和前导零丢失。

生成与验证脚本位于 [tools/auth_protocol_vectors.py](../../tools/auth_protocol_vectors.py)。脚本中的私钥和服务端密钥是公开测试数据，只能用于向量；不得作为生产默认配置。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：变更记录
- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：目标与范围、认证与资格、API 与确认过程、主流程、首版运行与协议固定值、错误、限额与验收、实现依赖与联动、变更记录
- `UC-AUTH-002`（use-cases/UC-AUTH-002-batch-get-developer-statuses.md）：目标与范围、调用者与输入、输出、主流程、异常流程、数据模型、API 契约、测试与验收、非目标、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `UC-AUTH-005`（use-cases/UC-AUTH-005-edit-own-user-profile.md）：目标与范围、参与者与前置条件、输入、输出、主流程、持久化与返回说明、异常与 transport 映射、API 与交付依赖、测试与验收、非目标、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-006-create-user.md` | 279 | `2b56bd4eb59d` |
| `use-cases/UC-AUTH-025-close-own-account.md` | 161 | `4a8ab75ce6d1` |
| `use-cases/UC-AUTH-002-batch-get-developer-statuses.md` | 156 | `220a639a2f73` |
| `use-cases/UC-AUTH-007-login.md` | 252 | `3afbbd9047ae` |
| `use-cases/UC-AUTH-005-edit-own-user-profile.md` | 287 | `60af229c87c6` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
