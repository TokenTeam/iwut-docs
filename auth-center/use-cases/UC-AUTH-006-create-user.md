# UC-AUTH-006：创建用户

状态：`ACCEPTED`

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

> 已在客户端本地保存学校账号密码的用户，明确选择创建平台账号，提交学校账号关联声明并通过新设备凭据的持有证明，建立正式 USER 主体并获得首次登录会话；邮箱和学生资料不作为注册前提。

本文件是创建行为与 `BR-REG-*` 的唯一规则正文。凭据证明、关联声明和认证载体遵守已接受的 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)；设计接受不表示后端、客户端或 Gateway 已交付。

首版设备凭据确定为 App 管理生命周期、由操作系统安全存储保护的设备公私钥，不采用标准 WebAuthn Passkey，也不依赖系统账号或密码管理器同步。私钥应由系统密钥设施生成并尽可能不可导出；“App 管理”是指 App 决定创建、使用和删除，不表示把明文私钥写入普通文件、偏好设置或业务数据库。算法和签名协议引用[公钥与签名契约](../../platform/contracts/auth-device-session-v1.md#公钥与签名)，客户端安全存储独立验收。

本用例不绑定邮箱、不设置平台密码、不恢复或合并旧账号、不认证学生真实性，不开放第三方资料读取，不签发服务间身份 JWS。Session 的共享规则由 [UC-AUTH-007](UC-AUTH-007-login.md) 定义。

## 参与者与前置条件

- 客户端已上线并提供无需平台后端的功能；用户进入平台注册页面前，已在本地完成学校账号密码的保存。平台注册是后续独立动作，不是使用这些既有本地功能的前提。
- 用户在客户端看见独立的“创建平台账号”动作并明确确认；不能仅因打开 App、学校登录成功或平台登录失败而自动注册。
- 客户端能根据本次选择的本地学校账号生成关联声明，注册必须提交；具体规则见 [BR-REG-004](#br-reg-004) 和 [BR-REG-005](#br-reg-005)。本地保存状态是客户端流程前提，不作为服务器已验证学校身份的证据。
- 客户端能在系统安全存储中创建并持久保管本次新设备凭据，能够完成已发布认证协议的签名证明及不可逆删除本机私钥。学校账号密码、学校登录 cookie 不发给 Auth。
- Auth 已配置支持的凭据协议、挑战策略和 Session 策略；缺少配置时相应入口不接流量。
- 创建入口允许尚无平台 Session 的用户访问；通过注册挑战和持有证明建立身份，不要求预先提供 trusted-identity-v1，也不依赖“来自官方 App”的声明放行。

## 输入与输出

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

## 主流程

1. 用户从已保存学校账号的客户端进入注册页，选择创建新平台账号；客户端持久准备平台设备凭据，生成对应学校账号的关联声明，并说明账号恢复能力及关联信息的用途。
2. Begin 校验提案、关联声明和入口限额，创建 purpose 为 REGISTER 的操作快照与挑战；挑战规则引用 [BR-LGN-002](UC-AUTH-007-login.md#br-lgn-002)。此时不创建 USER。
3. 客户端完成明确的注册确认，使用新私钥生成注册证明；本产品不要求额外生物识别，所选系统 API 必需的交互仍须遵从。
4. Complete 验证挑战、绑定内容和私钥持有证明，按 BR-REG-003 检查凭据唯一性；仅收到公钥不能注册成功。
5. Auth 生成新的 authId，初始化主体与空资料；按 BR-REG-004/005 解析或建立关联组，准备本次账号的关联绑定。
6. 依照 BR-REG-006，在一次原子提交中消费挑战，创建 USER、首个凭据、首次 Session、必需的账号关联绑定、必要的新关联组和操作完成记录。
7. 返回成功结果；客户端安全保存 Session 令牌，进入普通用户功能。Session 规则引用 [BR-LGN-003](UC-AUTH-007-login.md#br-lgn-003)。

无邮箱不使账号成为临时主体。普通用户可以立即调用仅要求有效 USER 身份的功能；需要 Developer 资格、人员权限、应用授权或特定配额条件的能力仍分别检查，注册不隐式授予它们。

## 业务规则

<a id="br-reg-001"></a>
### BR-REG-001：显式创建与平台账号独立

一次明确创建意图对应一个新 USER 主体。authId 是服务端生成的稳定 opaque 标识，沿用 [UC-AUTH-002 数据模型](UC-AUTH-002-batch-get-developer-statuses.md#数据模型)；不使用邮箱、学号、关联组或设备标识作为 authId。

学校账号、本机平台账号、平台认证凭据三者独立。相同学校声明可对应多个 authId，不据此复用、合并、覆盖或删除旧账号。已有账号登录入口认证失败时不得静默转成创建流程。

客户端首次注册即说明本机凭据丢失后的恢复限制，并提供以后绑定恢复方式的入口；不能等到主动退出时才告知。实际邮箱绑定和恢复另立用例，未交付前不能展示为已可用。

<a id="br-reg-002"></a>
### BR-REG-002：正式主体与最小初始化

创建时 principalType 为 USER、accountStatus 为 ACTIVE，createdAt/updatedAt 使用同一服务端 UTC 提交时间；developerStatus 为 null，permissions 为空，permissionRevision 从正整数 1 开始。资格与权限含义引用 [BR-DEV-004](UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) 和 [UC-AUTH-004](UC-AUTH-004-manage-reviewer-permission.md#数据模型)。

profile 初始化严格引用 [BR-UPF-008](UC-AUTH-005-edit-own-user-profile.md#br-upf-008)，物理结构引用 [BR-UPF-010](UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。不自动从学校系统、客户端缓存或关联声明推导任何资料值。

首个凭据和首次 Session 必须归属于本次 authId。SYSTEM 不走此入口；不接受客户端声明管理员、Developer 或 Reviewer 身份。

<a id="br-reg-003"></a>
### BR-REG-003：设备凭据持有证明与唯一归属

Auth 只接受已发布、受支持协议的注册证明，校验公钥/算法及证明的绑定关系，并确认调用者持有对应私钥。协议级挑战约束见 BR-LGN-002。客户端“设备验证成功”布尔值不是服务器认证证据；本轮不声称已证明设备未被修改或完成学生真实性验证。

首次注册保留显式创建平台账号和提交关联声明的确认，不要求额外的生物识别或每次签名确认；后续设备登录的服务端证明与触发边界引用 [BR-LGN-011](UC-AUTH-007-login.md#br-lgn-011)，客户端自动登录和本地清理建议见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。具体凭据协议须满足该产品目标，不能把 App 自管设备密钥称作或实现成标准 Passkey。

凭据的稳定标识与归一化公钥指纹由服务端/受信协议适配器确定。首版一个凭据只属于一个 authId，禁止将已有凭据改绑另一个账号；客户端不能通过不同编码、换 credentialId 或新注册 operation 绕过公钥唯一性。具体规范化由凭据协议规定。

同一公钥已注册时，不创建第二个主体，也不直接发放已有主体的 Session；引导使用 UC-AUTH-007 完成新的登录证明。不能复用已消费的注册证明作为登录证明。撤销记录不立即释放公钥唯一归属，注销后的保留/清理另行设计。

一个 authId 可以拥有多条独立 credential 记录，每条保存 credentialId、公钥、协议及状态；服务端不保存私钥。首版每台新设备或每次失去原安全存储后的独立安装都生成新密钥，并在邮箱登录、旧设备授权或其他恢复方式确认同一 authId 后新增一条 credential；不复制、导出或下载旧私钥。服务端凭据撤销由 [UC-AUTH-009](UC-AUTH-009-revoke-own-credential.md) 定义，本机私钥删除与退出编排见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)；只撤销当前 Session 是 [UC-AUTH-008](UC-AUTH-008-revoke-own-session.md) 的独立能力。新增凭据和凭据列表仍由后续管理用例授权，当前匿名注册入口不能向既有 authId 添加凭据。

<a id="br-reg-004"></a>
### BR-REG-004：学号关联的声明与隐私边界

关联声明只表示客户端提供了相同的学校账号关联输入，可信度固定为 CLIENT_ASSERTED，不是已验证自然人或已认证学生身份。相同组成员仍是独立账号；关联不得用于认证、找回、账号删除、读取其他成员数据或继承权限。

客户端通过明确版本的规范化与确定性散列生成 associationToken，首版仅面向武汉理工大学，输入为本地保存的该校学号，不增加学校 namespace 或可选学校字段；固定盐或用途字符串按公开信息对待。学号规范化不得丢失前导零或擅自把不同账号折叠。算法、规范化规则和测试向量引用[学号关联声明契约](../../platform/contracts/auth-device-session-v1.md#学号关联声明)，客户端不能自行换版本。

Auth 不通过学校接口验证，也不接收原始学号或学校凭据。注册页说明会提交用于关联的派生信息及其用途，用户明确选择创建平台账号即确认本次提交，不因本地已保存学校账号密码而提前上传。它不是“未上传任何学校相关信息”，固定盐散列也不保证学号无法被枚举。只校验声明形状/版本不能发现伪造：攻击者可能改值领取多份配额，也可能提交他人对应值消耗其配额。

Auth 用专用于关联查找的服务端密钥对规范编码的版本和 token 做 HMAC，持久化 lookupKey；为支持不依赖客户端再次上线的密钥轮换，另保存 associationToken 的认证加密密文。明文只在请求处理或迁移内存中短暂存在，不进入日志或明文持久化快照。挑战快照绑定 lookupKey，并暂存完成注册所需的 token 密文。存储、密钥隔离与轮换规则见 [BR-REG-008](#br-reg-008)。此措施仅降低单独数据库泄漏的风险，不承诺服务器本身无法枚举学号；密文属于服务器可恢复的派生关联信息，不等于完全不保留该信息。

<a id="br-reg-005"></a>
### BR-REG-005：关联组独立与应用隔离

同一规范化声明的 lookupKey 映射到稳定、服务端随机生成的 associationId；并发首次创建也只产生一个组。多个 authId 可关联同组。经本用例成功创建的每个新账号恰好绑定一个组，修改、解绑、关联方案升级不由注册接口提供。

关联声明是平台注册的必填输入：association 缺失/null，或 schemeVersion、associationToken 缺失/为空/格式不合法时，Begin 在创建挑战前拒绝；未知方案版本按未支持处理。Complete 只能使用已绑定的有效声明，不能省略或替换关联。关联存储不可用时不得降级创建无关联账号，失败的平台注册不删除客户端学校凭据，也不阻断既有无需平台后端的功能。

该要求只保证新建账号具有一份结构有效的客户端声明，不提升其真实性等级、不限制同组只能有一个账号，也不赋予学生关联账号控制权。历史账号如何补充关联不在本用例中隐式迁移；不得把新注册的必填规则直接变成既有登录的额外认证证明。

未来对外仅提供应用范围内的关联标识，建议保存唯一 `(appId, associationId)` 到随机 applicationAssociationId 的映射；不向应用披露 lookupKey、内部 associationId、原始 token 或其他成员账号。appId 来自服务端确认的应用上下文，不由终端任意选择。该映射不需要派生密钥，也不替换对外账号身份标识。

未来若扩展其他学校，必须先设计关联方案版本与既有分组迁移，不通过新增一个默认学校字段静默重算武汉理工大学的既有标识。

本 UC 只建立内部关系，不提供对外映射查询/签发接口。应用授权、缺失值、删除/重新创建后的配额连续性及关联保留期限，由后续对外能力用例定义；不能因一个成员退出登录或注销就隐式重建整个组。

<a id="br-reg-006"></a>
### BR-REG-006：原子创建与结果不确定的恢复

首版采用 Mongo 多文档事务，一次提交 USER、凭据、Session、必需的账号关联绑定、必要的新关联组、操作完成标记和 REGISTER 挑战的消费；任一失败全部回滚。必须在支持事务的部署上交付；不能用顺序写入加“后续修复”冒充原子性。生成标识、Session 秘密和提交候选在事务自动重试期间保持一致，未确认提交不得把 Session 秘密返回客户端。

operationId 只标识一次注册操作，不是登录凭证。相同 operation 最多创建一个 USER 和一个首次 Session；并发 Complete 只有一个消费成功。已消费操作的重放返回 REGISTRATION_ALREADY_COMPLETED，不重新创建、不再次披露 Session 令牌。不同 operation 的同一公钥由唯一索引阻止重复账号。

响应丢失或提交结果未知时，客户端保留原私钥，可先重试同一操作确认，再通过 UC-AUTH-007 发起全新登录。只返回“已完成”不代表已取得可用 Session；不得因为未知结果而自动生成新私钥创建新账号。新挑战的登录成功证明了原账号可用；暂时不可用时继续保留凭据并提示重试。

首次响应遗失可能留下一条客户端未取得令牌的 Session，它不产生额外账号；按会话有效期失效。不得为了重发响应而明文持久化 Session 令牌或无限保留可兑换的注册证明。

<a id="br-reg-007"></a>
### BR-REG-007：注册入口的限额与秘密最小暴露

Begin/Complete 都是有界入口，需要独立限流、挑战有效期、尝试次数和未完成挑战容量限制。限流不能只依赖可伪造的设备 ID 或关联声明；不把“一组只准一个账号”用作去重或滥用防护。入口阈值和输入容量引用 [BR-LGN-009](UC-AUTH-007-login.md#br-lgn-009)，不以无限制默认值上线；客户端兼容矩阵独立验收。

不记录私钥、Session 令牌、完整挑战/证明、学校密码、邮箱恢复秘密或 associationToken。允许记录 operationId、结果、已建立的 authId/credentialId 和时间等受控操作元数据；不得通过失败响应返回匹配关联组、其他成员、已绑定邮箱或数据库内部信息。

<a id="br-reg-008"></a>
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

## 持久化候选

| 集合 | 作用与约束 |
| --- | --- |
| `auth_principals` | 原有主体与内嵌 profile；authId 唯一。 |
| `auth_credentials` | 设备公钥、协议版本、authId、状态、创建/撤销时间；credentialId 与规范公钥指纹分别唯一；私钥不入库。 |
| `auth_authentication_operations` | BR-LGN-002 的不可变绑定、期限、尝试/消费状态与完成引用；REGISTER 快照的 token 密文及清理见 BR-REG-008，不持久化明文 associationToken 或 Session 令牌。 |
| `auth_sessions` | 结构和令牌规则由 UC-AUTH-007 拥有。 |
| `auth_student_associations` | associationId 唯一；每组一份版本化 lookupKey 与 token 认证加密密文，字段及唯一索引见 BR-REG-008；不维护在线轮换别名。 |
| `auth_student_association_members` | authId 到 associationId 的绑定和 CLIENT_ASSERTED 信任等级；authId 唯一。 |

这些集合是初版物理候选。短期挑战清理由 TTL 等机制辅助，但不能用异步删除代替服务端期限检查。注册提交后删除/过期操作记录也不能释放凭据唯一性，避免迟到重试创建第二账号。

## 异常语义

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

## 测试与验收

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

## 交付依赖与验收边界

- 后端按[共享协议](../../platform/contracts/auth-device-session-v1.md)交付真实验证器、生成 Proto、原生 gRPC 与测试向量；算法、公钥规范化和签名报文不由各工作包自行定义。
- Android/iOS 安全存储、最低兼容版本、签名前检查、关联声明披露及可靠删除由客户端独立验收；后端测试不替代移动端验收。
- Mongo 原子注册、启动前离线密钥迁移及故障测试由本工作包交付。编码遵循 BR-REG-008，正式环境维护窗口仍须部署验收。
- 挑战与入口限额引用 UC-AUTH-007；Session 寿命由有效的 AUTH_SESSION_TTL 部署配置决定。
- API 包为 `auth_center/v1/authentication/`，方法与 middleware 遵守共享契约的 RPC 鉴权表；TLS 部署、Gateway 路由和身份签发另行交付。

## 变更记录

- 2026-09-22：接受本用例，设备证明、关联声明、Session 载体与 RPC 鉴权引用 auth-device-session-v1；后端、客户端和 Gateway 分别验收。

- 2026-09-22：建立设备凭据创建正式账号草案，包含首次 Session、学号关联、原子创建及未知结果恢复；保留凭据协议等交付阻塞项。
- 2026-09-22：确认注册前客户端已保存学校账号密码，学校账号关联声明为必填；更新输入、拒绝语义和验收，保留客户端声明的真实性边界及既有本地功能。
- 2026-09-22：确认首版仅服务武汉理工大学，移除学校 namespace；验收检查发现设备证明协议和关联 token 算法尚未闭合，保留 PROPOSED。
- 2026-09-22：确认关联 token 认证加密保存、查找/加密密钥分离，采用 ENV 注入当前/上一密钥组、单实例停服迁移与按记录版本幂等重跑；不设计进度检查点或多实例在线轮换。
- 2026-09-22：根据远端 10 万条记录基准，确定 Auth 启动前每批 500 条迁移、全量核验后同进程开放服务；失败退出并幂等重启，保留正式部署与故障路径验收项。
- 2026-09-22：明确注册不要求额外生物识别，保留显式注册与关联信息提交确认；凭据接入需支持 UC-AUTH-007 的自动登录目标。
- 2026-09-22：明确一个账号可拥有多条凭据；同步型 Passkey 可由多设备共用一条服务端凭据，恢复后在新设备新建的密钥则新增凭据记录，不复制旧私钥。
- 2026-09-22：首版收敛为 App 管理、系统安全存储保护且不参与系统同步的设备密钥；退出删除本机私钥并撤销服务端凭据，标准 Passkey 不进入首版。
- 2026-09-22：将设备登录、Session 撤销和凭据撤销分别引用 UC-AUTH-007/008/009；注册用例不再定义客户端退出编排。
