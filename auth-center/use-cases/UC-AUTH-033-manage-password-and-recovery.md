# UC-AUTH-033：管理密码与恢复账号

状态：`ACCEPTED`

## 目标与范围

用户正常修改平台密码，或在忘记密码时通过当前登录邮箱验证码重置，并原子收回旧认证材料的访问权。平台密码保护登录邮箱及危险动作，登录邮箱是最终恢复凭据。

2026-10-13 用户授权开始实现。已检查当前代码和认证事务依赖，工程默认及密码协议作为本工作包接受。实现分批推进，缺依赖的入口保持关闭。正式 blocklist 发布、目标机器压测和真实集成验收是启用门禁，不代表已完成交付。

密码注册初始化由 UC006/011 调用本 UC 的策略/存储规则；普通密码登录单列 [UC034](UC-AUTH-034-login-with-password.md)，邮箱码登录继续 UC012，设备自动登录继续 UC007。本 UC 不创建账号、改登录邮箱、管理应用权益、合并账号或提供密码之外的人工/扫码恢复。

## 参与者与依赖

- 正常改密：当前有效 ACTIVE USER Session，当前平台密码；调用者 owner/credentialId 来自 Auth，不能指定 authId。
- 忘记密码：无 Session 的匿名恢复入口，仅当前唯一登录邮箱码授权，不要求旧密码/旧私钥，不支持非登录/历史/仅用于校园认证的邮箱。
- 危险动作由所属 UC 完成业务授权，本 UC 只验证密码、固定用途/目标/版本；密码正确不授予管理员或应用归属权限。
- Auth 已有邮箱目录/额度/SMTP、共享密码策略/存储/计算、Mongo 认证事务栅栏、accountRevision/凭据下界、Session/LRU 和 OAuth 代际检查；公开改密/重置/通知的续作现状见[依赖检查](../implements/UC-AUTH-033-034-readiness.md)。普通密码登录仍由 UC034 独立交付。

## 输入与输出

逻辑消息与载体见[已接受的密码协议](../../platform/contracts/auth-password-v1.md)。Proto 字段号与入口已同步独立 API；公开管理入口由默认关闭的 AUTH_PASSWORD_MANAGEMENT_ENABLED 独立控制，不复用旧无密码注册路径。

```text
ChangeOwnPassword { requestId, currentPassword, newPassword }
PasswordChanged { operationId, session: SessionEstablished }
GetOwnPasswordChange { requestId }
OwnPasswordChange { status: NOT_FOUND | COMPLETED, operationId? }

BeginPasswordReset { requestId, loginEmail }
PasswordResetStarted { operationId, expiresAt, resendAfter }
CompletePasswordReset { operationId, code, newPassword }
PasswordResetCompleted { operationId }
```

Change 和 Get 要求唯一有效 `x-iwut-session`；Reset 两入口要求 Session 键完全不存在，不以它确定目标账号，携带无效 token 不匿名降级。所有请求 no-store、严格 JSON/有界 body，密码/码只经 TLS 传输、不进入 URL。重置响应没有 Session 或设备授权。

## 主流程

### 正常修改

1. 只读确认 Session/调用凭据、账号和当前密码记录；校验输入、额度、请求 ID，不提前修改状态。
2. 验证旧密码并校验新密码，计算新 Argon2id 认证材料；昂贵计算在有界执行器进行，不在可自动重试的事务内重复计算。
3. 在最终认证事务中复核原 Session、凭据、密码版本、账号版本和幂等状态。
4. 按 BR-PWD-004/006 更新密码与代际，保留且推进当前凭据，建立新的 Session，完成操作/审计；其他旧凭据/Session/OAuth 材料随代际失效。
5. 确认提交后一次性返回新 token，客户端替换旧 token。响应未知按 BR-PWD-007 恢复，不假定回滚、不重复返回秘密。

### 忘记密码重置

1. Begin 检查地址、请求 ID 与共享邮件额度；固定目标当时的唯一登录邮箱/owner/角色版本、密码及账号版本，或不可恢复占位操作。
2. 真实可恢复目标收到独立重置验证码；匿名响应同形，不确认账号或角色是否存在，发送请求本身不使旧登录失效。
3. Complete 校验操作、码和新密码；在最终事务复核目标仍为当前登录邮箱、ACTIVE、全部原版本未漂移。
4. 更新密码/代际，清退所有旧设备与 Session，失效旧 OAuth 材料，原子消费操作并写审计。
5. 返回无秘密完成结果并通知登录邮箱；用户再走普通登录，客户端后台生成新密钥，不复活旧凭据。

## 业务规则

<a id="br-pwd-001"></a>
### BR-PWD-001：密码来源、策略与初始化

平台密码独立于学校/邮箱口令和设备私钥。新注册在 UC006/011 同事务初始化密码；不允许无密码账号创建后再补齐，不从邮箱验证码、随机 Session 或客户端缓存派生密码。

首版：有效 UTF-8，统一 NFC 规范化后按 Unicode code point 计数 15..128，规范化后最多 512 字节，输入规范化前最多 1024 字节；不 trim、折叠大小写或截断，空格属于密码。所有设置/校验路径采用相同规范化版本，支持粘贴/密码管理器；拒绝常见、预期及已泄露密码的完整匹配，不强制大小写/数字/符号组合，不定期强制改密。新密码不得等于当前密码，失败不消费有效重置码或改动认证状态。

策略包含版本化本地 blocklist，部署明确装载、校验并在启用前压测；不能用测试 fixture、空列表或在线上送明文密码的接口代替。具体生产列表内容/发布流程列为启用门禁。

策略依据 [NIST 密码规则](https://pages.nist.gov/800-63-4/sp800-63b.html#passwords)；本平台的 128 上限/NFC/产品角色是已接受平台约束，不宣称满足 NIST 全部认证等级。

<a id="br-pwd-002"></a>
### BR-PWD-002：安全存储与参数升级

按 authId 保存独立密码记录：Argon2id 的算法/格式/规范化版本、参数、每次设置生成的随机 salt、hash、正 passwordRevision、变更时间。首版 Argon2id v19，salt 16 随机字节、hash 32 字节，默认 m=19456 KiB/t=2/p=1；不得低于已审核成本，允许通过部署提升并在目标机器压测，存储参数本身也有上下界。未知版本、损坏记录或不可承受参数失败关闭，不退回 SHA-256/旧实现。

首版实现固定 formatVersion=1、normalizationVersion=`nfc-unicode-15.0.0`；存储/配置参数界限 m=19456..262144 KiB、t=2..6、p=1..4。参数升级不降低原 m/t，不能以“更高某一维度”为由降另一维度。本地 blocklist 使用版本/来源声明及内容 SHA-256 pin；文件每行一个规范密码的完整 SHA-256（64 位小写 hex＋LF），最多 1000000 个唯一条目/65000000 字节，拒绝空表/重复/损坏/摘要不符。该 SHA-256 仅为禁止列表匹配，不是长期密码 verifier；正式来源和发布审核仍是启用门禁，测试列表只供测试。

同一密码的工作因子升级只重哈希，不改变 passwordRevision/accountRevision，不踢设备；CAS 失败不得覆盖并发改密。真正设置不同密码才推进 passwordRevision。首版不引入 pepper/可逆密码加密；操作幂等用独立 HMAC 秘密，不把 HMAC 当长期密码存储。

明文密码不持久化、写日志/审计/trace/metrics、发邮件或加入可返回的签名 payload；客户端不预哈希为可重放“密码替身”。内存生命周期受控，但不声称 Go GC 可以证明秘密已经擦除。参考 [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。

<a id="br-pwd-003"></a>
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

<a id="br-pwd-004"></a>
### BR-PWD-004：正常改密保留当前设备

当前 Session 与所引用凭据必须在最终事务仍有效，旧密码校验快照版本未变化，新密码满足策略。正常改密将 passwordRevision/accountRevision 各加一，并将 minimumCredentialRevision 提升到新 accountRevision；唯一保留的当前有效凭据推进 credentialRevision 到该值，不更改公钥/指纹/createdAt/credentialId。已经撤销或低于旧下界的凭据不可成为保留对象。

旧 Session 全部失效，包括调用 token；新建不同 sessionId/token 的 Session，只在确认首次提交后返回。新记录方法为 `PASSWORD_AND_SESSION`，表示旧 Session＋密码重新认证，不伪称完成新的私钥签名；必需当前 credentialId、来源 sessionId、passwordRevision 和新 accountRevision。来源 sessionId 是不可变认证快照，不要求旧来源 Session 继续有效，也不由用户指定。

新 Session 按 UC007 新会话固定寿命与容量规则建立，authenticatedAt/createdAt 为本次密码验证提交时间；不更新旧 Session 的代际或延长旧会话。其他凭据永久退休，重新登录生成新密钥；用户界面提前说明“当前设备保留，其他设备需重新登录”。

<a id="br-pwd-005"></a>
### BR-PWD-005：登录邮箱恢复与全部设备清退

恢复只由 Begin 时已归属 ACTIVE USER 的当前登录邮箱授权；非登录/历史地址、校园认证或普通 Session 不足以重置。占位操作在之后注册/换角色/恢复账号也永不可接受，须重新 Begin。

重置码与 authId、登录角色版本、密码版本、accountRevision、部署上下文和操作绑定；任何先完成的登录邮箱切换、改密/重置或账号治理都使旧操作失效。换邮箱再换回不复活旧码；登录、注册、绑定和重置码不互换。发起、过期或失败不得锁账号/撤销会话，避免匿名重置接口成为踢人入口。

成功重置推进 passwordRevision/accountRevision，提升 minimumCredentialRevision，不保留任何旧凭据/Session，不签发 Session。之后凭密码或当前登录邮箱码＋本机新密钥进入原 authId；旧公钥即使仍有私钥也不能复活/重新登记，客户端须生成新密钥。保留 profile、邮箱列表/登录角色、校园绑定、资格、grant 同意、authId/pairwise sub 和应用权益。

验证码复用邮件基线的 8 ASCII 数字、10 分钟、最多 5 次错误、60 秒冷却与共享发送额度，不复用用途/HMAC 密钥。通知在确认成功后发到变更当时的登录邮箱，不含新密码或登录 token。成功重置不自动登录，参考 [OWASP 恢复规则](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html#user-resets-password)。

<a id="br-pwd-006"></a>
### BR-PWD-006：统一代际与不可复活的设备下界

继续使用 [UC022 的 accountRevision](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002)作为认证材料统一代际，不新增另一份 authenticationEpoch。密码修改/重置也原子推进它，accountStatus 不变；禁用/恢复仍只按 UC022 改状态/版本。

新增 principal.minimumCredentialRevision 正 int64，初始 1；密码变更将它提升到新的 accountRevision，永不下降。credential.credentialRevision 为登记时的 accountRevision；有效条件包含 `minimumCredentialRevision <= credentialRevision <= currentAccountRevision` 和原有未撤销/owner/协议条件。禁用/恢复不提升该下界，因此未被撤销且未退休的设备仍能恢复后新登录；密码重置则永久退休旧代设备。正常改密仅在该事务中推进原本有效的当前凭据，不允许一般登录/重试给低于下界的旧公钥补版本复活。

Session、登录/绑定/重置挑战、OAuth interaction/code/access/family/refresh、USER 身份签发和敏感动作都在最终边界检查 accountRevision；旧记录不可回填到新代。密码验证还比较 passwordRevision；工作因子升级不改变这些代际。版本缺失/非法/溢出失败关闭，不在请求中默认为 1。

改密事务的失效成本不随历史凭据/Session/token 数量增长，不无界 UpdateMany；退休由下界/代际立即决定，物理清理另做有界任务。保留公钥指纹永久归属。UC009 对本人已退休目标可按已失效事实幂等处理；列表/LRU/UC012 复用均须识别退休，不能只检查 revokedAt。

全部旧 OAuth code/access/refresh family 在 Auth 后续在线检查中失败，grant 历史同意/撤权 epoch 与 pairwise 映射保留，新授权按当前规则复用同意。Auth audience USER JWS 原有 account_revision 在线检查也拒绝旧版本；App audience、委托、app.close 及 OIDC 的已签短期离线证据与第三方自身 Cookie 仍可能存续到原期限，不能声称密码更新取消所有在途/离线业务。

<a id="br-pwd-007"></a>
### BR-PWD-007：原子提交、幂等与秘密恢复

密码材料/版本、凭据下界/保留对象、新 Session（仅改密）、操作消费与不可变审计共用 Auth 事务栅栏。昂贵 hash 在事务外准备，提交/重试重新比较全部快照；不得接受旧密码校验后另一个密码版本已提交。任一失败回滚，未知提交不宣称失败回滚或发送成功通知。

改密幂等为 `(authId, requestId)`，操作至少保留 24 小时；同键输入指纹不同冲突。独立 operation HMAC tag 不存旧/新密码明文，新 token 只首次提交返回。响应丢失时当前私钥→UC007→GetOwnPasswordChange；若私钥不可用，可明确 UC012/034 登录，再查原 requestId。NOT_FOUND 只代表当前观察点未见完成，不证明在途请求不会提交，不据此换新 ID 自动再改密。

最终写入还尊重 UC024/025 既有退出/终止屏障，不用密码更新取消已提交注销、恢复 CLOSED 或绕过 App 归属退出义务；治理阻断按所属 UC 处理。

重置 Begin 按规范登录地址的受保护索引/requestId 幂等 24 小时，新真实操作可替代原本人未完成操作，检查额度/版本后才替代；同键不重发/延长，操作容量有界。首次 Complete 必须在 10 分钟内；完成记录保留窗口中只允许原码和同新密码输入、当前登录角色/密码/账号仍等于成功版本时恢复无秘密完成结果，不再次设置或推进版本。后来又换邮箱/改密码则旧完成结果不能成为新的授权，原操作失效。

审计记录 action、可信 owner/sourceSessionId 或邮箱恢复方式、操作 ID、版本、保留 credentialId（若有）、时间/结果；无密码/完整邮箱/码/hash/签名/token。通知用唯一事件 outbox，有界重试，不在事务中发信；投递失败不回滚已提交密码或重复产生变更。新密码、操作、通知、审计分类均纳入 UC025 终止清单与保留/备份恢复规则。

<a id="br-pwd-008"></a>
### BR-PWD-008：限额、失败关闭与启用门禁

所有密码验证共用昂贵额度：默认单实例并发 4、队列 32/最长等待 2 秒，Argon 调用全局 120 单位/分钟、每来源 20、每 owner/地址 10；一次业务预留所需单位（校验＋新 hash 通常 2），事务重试不重扣。4096 细分桶、有限正配置、哈希前扣；取消请求不提前释放仍运行计算的执行槽。来源仅 socket，地址 HMAC；账户/地址失败额度用共用 Mongo，不因错密码永久禁用账号。

邮件重置共享既有发送额度，不能按用途翻倍。提案：有效 reset 每账号 1、password login 每 owner/匿名地址 5，全局合计 PENDING 10000；保留记录全局最多 1000000，达到容量拒绝新操作，不驱逐活跃/幂等记录。幂等键/状态/过期索引及共享认证栅栏原子保护容量，TTL 不代替业务计数；匿名占位同样占额。一般入口共享全局 600/来源 120/确认 owner 30 次每分钟及 4096 桶。通知 outbox 不占用户验证码额度，实施压测/索引和任务清理仍须验收。

错误密码/不存在账号/非登录邮箱等认证失败统一，依赖故障与限流可区分；不得响应裸数据库/crypto 信息。入口默认关闭，必须升级全部密码/下界/认证消费路径、准备正式 blocklist 与 hash 压测、完成公开向量/API/Wire/Mongo race/跨服务验证才可启用。系统未部署，不设计生产旧账号自动设密码/补代际；旧测试数据显式重建或隔离，不静默迁移/删除。

## 验收与错误边界

- 策略：NFC/空格/15–128/字节边界、blocklist、无截断/明文、随机 salt、参数升级/异常/有界 hash。
- 改密：全部认证方法可用、保留唯一当前凭据、新 token 一次返回、旧 token/其他密钥/OAuth 在线失败，版本/审计/新 Session 失败整体回滚。
- 重置：仅登录邮箱码、独立用途、原邮箱/版本变化/占位始终拒绝；成功无 Session、全部旧钥永久退休；无效请求不踢人。
- 并发：改密/双重置/邮箱切换/登录/注销/禁用明确顺序；不能旧密码验证后晚提交；禁用恢复不复活密码退休钥。
- 恢复：未知提交、24 小时同键/异参、一次性 token 丢失经当前钥登录查询、完成结果只恢复原状态；通知不重复变更。
- 所有 Session/USER JWS/OAuth/LRU/列表/复用入口闭合版本和 credentialRevision；真实 HTTP/native gRPC/Wire/SMTP/Mongo race，App 短期离线窗口明确。

字段/reason/HMAC 与容量约定已写入密码契约/本 UC；公开向量及 API 已交付，注册/邮箱与全部认证消费者的直接依赖已具备。2026-10-15 串行续作补公开改密/重置及通知；代码、真实验收和启用状态分别见 readiness，不以协议存在代替上线验证。

## 交付依赖与变更记录

硬依赖/实施顺序见 readiness；正式实现必须同步 UC006/007/009/011/012/014–020/022/025/026/032、可信身份和密码协议。2026-10-13 授权开工，限额/字段/存储按上述约定实现，公开向量及压测属于启用验收。最新直接依赖及 UC032 已交付；本轮按用户要求先完成 UC033 验收，再实现 UC034，保持全部旧入口无旁路。

- 2026-10-12：建立密码管理/恢复 DRAFT；收录用户已接受产品建议，固定单一 accountRevision＋设备失效下界提案、正常保留当前设备/重置全部清退、目标密码验证、OAuth 失效及历史离线窗口；未实施。
