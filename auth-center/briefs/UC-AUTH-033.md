<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-033 --spec tools/brief-specs/UC-AUTH-033.json -->
# Brief — UC-AUTH-033：管理密码与恢复账号

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-033` 管理密码与恢复账号 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PWD-001`–`BR-PWD-008`（8 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-password-v1.md` |

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

用户正常修改平台密码，或在忘记密码时通过当前登录邮箱验证码重置，并原子收回旧认证材料的访问权。平台密码保护登录邮箱及危险动作，登录邮箱是最终恢复凭据。

2026-10-13 用户授权开始实现。已检查当前代码和认证事务依赖，工程默认及密码协议作为本工作包接受。实现分批推进，缺依赖的入口保持关闭。正式 blocklist 发布、目标机器压测和真实集成验收是启用门禁，不代表已完成交付。

密码注册初始化由 UC006/011 调用本 UC 的策略/存储规则；普通密码登录单列 [UC034](../use-cases/UC-AUTH-034-login-with-password.md)，邮箱码登录继续 UC012，设备自动登录继续 UC007。本 UC 不创建账号、改登录邮箱、管理应用权益、合并账号或提供密码之外的人工/扫码恢复。

### 参与者与依赖

- 正常改密：当前有效 ACTIVE USER Session，当前平台密码；调用者 owner/credentialId 来自 Auth，不能指定 authId。
- 忘记密码：无 Session 的匿名恢复入口，仅当前唯一登录邮箱码授权，不要求旧密码/旧私钥，不支持非登录/历史/仅用于校园认证的邮箱。
- 危险动作由所属 UC 完成业务授权，本 UC 只验证密码、固定用途/目标/版本；密码正确不授予管理员或应用归属权限。
- Auth 已有邮箱额度/SMTP、Mongo 认证事务栅栏、accountRevision、凭据归属、Session/LRU 和 OAuth 代际检查；没有密码存储、密码登录或恢复，详见[依赖检查](../implements/UC-AUTH-033-034-readiness.md)。

### 输入与输出

逻辑消息与载体见[密码协议草案](../../platform/contracts/auth-password-v1.md)。具体 Proto 字段号、入口和配置待接受时同步独立 API；不复用旧无密码注册路径。

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

### 主流程

#### 正常修改

1. 只读确认 Session/调用凭据、账号和当前密码记录；校验输入、额度、请求 ID，不提前修改状态。
2. 验证旧密码并校验新密码，计算新 Argon2id 认证材料；昂贵计算在有界执行器进行，不在可自动重试的事务内重复计算。
3. 在最终认证事务中复核原 Session、凭据、密码版本、账号版本和幂等状态。
4. 按 BR-PWD-004/006 更新密码与代际，保留且推进当前凭据，建立新的 Session，完成操作/审计；其他旧凭据/Session/OAuth 材料随代际失效。
5. 确认提交后一次性返回新 token，客户端替换旧 token。响应未知按 BR-PWD-007 恢复，不假定回滚、不重复返回秘密。

#### 忘记密码重置

1. Begin 检查地址、请求 ID 与共享邮件额度；固定目标当时的唯一登录邮箱/owner/角色版本、密码及账号版本，或不可恢复占位操作。
2. 真实可恢复目标收到独立重置验证码；匿名响应同形，不确认账号或角色是否存在，发送请求本身不使旧登录失效。
3. Complete 校验操作、码和新密码；在最终事务复核目标仍为当前登录邮箱、ACTIVE、全部原版本未漂移。
4. 更新密码/代际，清退所有旧设备与 Session，失效旧 OAuth 材料，原子消费操作并写审计。
5. 返回无秘密完成结果并通知登录邮箱；用户再走普通登录，客户端后台生成新密钥，不复活旧凭据。

### 验收与错误边界

- 策略：NFC/空格/15–128/字节边界、blocklist、无截断/明文、随机 salt、参数升级/异常/有界 hash。
- 改密：全部认证方法可用、保留唯一当前凭据、新 token 一次返回、旧 token/其他密钥/OAuth 在线失败，版本/审计/新 Session 失败整体回滚。
- 重置：仅登录邮箱码、独立用途、原邮箱/版本变化/占位始终拒绝；成功无 Session、全部旧钥永久退休；无效请求不踢人。
- 并发：改密/双重置/邮箱切换/登录/注销/禁用明确顺序；不能旧密码验证后晚提交；禁用恢复不复活密码退休钥。
- 恢复：未知提交、24 小时同键/异参、一次性 token 丢失经当前钥登录查询、完成结果只恢复原状态；通知不重复变更。
- 所有 Session/USER JWS/OAuth/LRU/列表/复用入口闭合版本和 credentialRevision；真实 HTTP/native gRPC/Wire/SMTP/Mongo race，App 短期离线窗口明确。

字段/reason/HMAC 与容量约定已写入密码契约/本 UC；2026-10-13 公开向量及 API 生成物已交付，正常改密核心分批验证，公开服务与注册/邮箱/重置依赖尚未交付，不假称已有可用入口。

### 交付依赖与变更记录

硬依赖/实施顺序见 readiness；正式实现必须同步 UC006/007/009/011/012/014–020/022/025/026/032、可信身份和密码协议。2026-10-13 授权开工，限额/字段/存储按上述约定实现，公开向量及压测属于启用验收。UC033 与 UC034、注册/邮箱改造先闭合，再开 UC032，避免用仅 UI 密码保护留下旧入口。

- 2026-10-12：建立密码管理/恢复 DRAFT；收录用户已接受产品建议，固定单一 accountRevision＋设备失效下界提案、正常保留当前设备/重置全部清退、目标密码验证、OAuth 失效及历史离线窗口；未实施。

## 业务规则（UC-AUTH-033 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-001 -->
### BR-PWD-001：密码来源、策略与初始化

平台密码独立于学校/邮箱口令和设备私钥。新注册在 UC006/011 同事务初始化密码；不允许无密码账号创建后再补齐，不从邮箱验证码、随机 Session 或客户端缓存派生密码。

首版：有效 UTF-8，统一 NFC 规范化后按 Unicode code point 计数 15..128，规范化后最多 512 字节，输入规范化前最多 1024 字节；不 trim、折叠大小写或截断，空格属于密码。所有设置/校验路径采用相同规范化版本，支持粘贴/密码管理器；拒绝常见、预期及已泄露密码的完整匹配，不强制大小写/数字/符号组合，不定期强制改密。新密码不得等于当前密码，失败不消费有效重置码或改动认证状态。

策略包含版本化本地 blocklist，部署明确装载、校验并在启用前压测；不能用测试 fixture、空列表或在线上送明文密码的接口代替。具体生产列表内容/发布流程列为启用门禁。

策略依据 [NIST 密码规则](https://pages.nist.gov/800-63-4/sp800-63b.html#passwords)；本平台的 128 上限/NFC/产品角色是已接受平台约束，不宣称满足 NIST 全部认证等级。

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-002 -->
### BR-PWD-002：安全存储与参数升级

按 authId 保存独立密码记录：Argon2id 的算法/格式/规范化版本、参数、每次设置生成的随机 salt、hash、正 passwordRevision、变更时间。首版 Argon2id v19，salt 16 随机字节、hash 32 字节，默认 m=19456 KiB/t=2/p=1；不得低于已审核成本，允许通过部署提升并在目标机器压测，存储参数本身也有上下界。未知版本、损坏记录或不可承受参数失败关闭，不退回 SHA-256/旧实现。

首版实现固定 formatVersion=1、normalizationVersion=`nfc-unicode-15.0.0`；存储/配置参数界限 m=19456..262144 KiB、t=2..6、p=1..4。参数升级不降低原 m/t，不能以“更高某一维度”为由降另一维度。本地 blocklist 使用版本/来源声明及内容 SHA-256 pin；文件每行一个规范密码的完整 SHA-256（64 位小写 hex＋LF），最多 1000000 个唯一条目/65000000 字节，拒绝空表/重复/损坏/摘要不符。该 SHA-256 仅为禁止列表匹配，不是长期密码 verifier；正式来源和发布审核仍是启用门禁，测试列表只供测试。

同一密码的工作因子升级只重哈希，不改变 passwordRevision/accountRevision，不踢设备；CAS 失败不得覆盖并发改密。真正设置不同密码才推进 passwordRevision。首版不引入 pepper/可逆密码加密；操作幂等用独立 HMAC 秘密，不把 HMAC 当长期密码存储。

明文密码不持久化、写日志/审计/trace/metrics、发邮件或加入可返回的签名 payload；客户端不预哈希为可重放“密码替身”。内存生命周期受控，但不声称 Go GC 可以证明秘密已经擦除。参考 [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。

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

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-005 -->
### BR-PWD-005：登录邮箱恢复与全部设备清退

恢复只由 Begin 时已归属 ACTIVE USER 的当前登录邮箱授权；非登录/历史地址、校园认证或普通 Session 不足以重置。占位操作在之后注册/换角色/恢复账号也永不可接受，须重新 Begin。

重置码与 authId、登录角色版本、密码版本、accountRevision、部署上下文和操作绑定；任何先完成的登录邮箱切换、改密/重置或账号治理都使旧操作失效。换邮箱再换回不复活旧码；登录、注册、绑定和重置码不互换。发起、过期或失败不得锁账号/撤销会话，避免匿名重置接口成为踢人入口。

成功重置推进 passwordRevision/accountRevision，提升 minimumCredentialRevision，不保留任何旧凭据/Session，不签发 Session。之后凭密码或当前登录邮箱码＋本机新密钥进入原 authId；旧公钥即使仍有私钥也不能复活/重新登记，客户端须生成新密钥。保留 profile、邮箱列表/登录角色、校园绑定、资格、grant 同意、authId/pairwise sub 和应用权益。

验证码复用邮件基线的 8 ASCII 数字、10 分钟、最多 5 次错误、60 秒冷却与共享发送额度，不复用用途/HMAC 密钥。通知在确认成功后发到变更当时的登录邮箱，不含新密码或登录 token。成功重置不自动登录，参考 [OWASP 恢复规则](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html#user-resets-password)。

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-006 -->
### BR-PWD-006：统一代际与不可复活的设备下界

继续使用 [UC022 的 accountRevision](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002)作为认证材料统一代际，不新增另一份 authenticationEpoch。密码修改/重置也原子推进它，accountStatus 不变；禁用/恢复仍只按 UC022 改状态/版本。

新增 principal.minimumCredentialRevision 正 int64，初始 1；密码变更将它提升到新的 accountRevision，永不下降。credential.credentialRevision 为登记时的 accountRevision；有效条件包含 `minimumCredentialRevision <= credentialRevision <= currentAccountRevision` 和原有未撤销/owner/协议条件。禁用/恢复不提升该下界，因此未被撤销且未退休的设备仍能恢复后新登录；密码重置则永久退休旧代设备。正常改密仅在该事务中推进原本有效的当前凭据，不允许一般登录/重试给低于下界的旧公钥补版本复活。

Session、登录/绑定/重置挑战、OAuth interaction/code/access/family/refresh、USER 身份签发和敏感动作都在最终边界检查 accountRevision；旧记录不可回填到新代。密码验证还比较 passwordRevision；工作因子升级不改变这些代际。版本缺失/非法/溢出失败关闭，不在请求中默认为 1。

改密事务的失效成本不随历史凭据/Session/token 数量增长，不无界 UpdateMany；退休由下界/代际立即决定，物理清理另做有界任务。保留公钥指纹永久归属。UC009 对本人已退休目标可按已失效事实幂等处理；列表/LRU/UC012 复用均须识别退休，不能只检查 revokedAt。

全部旧 OAuth code/access/refresh family 在 Auth 后续在线检查中失败，grant 历史同意/撤权 epoch 与 pairwise 映射保留，新授权按当前规则复用同意。Auth audience USER JWS 原有 account_revision 在线检查也拒绝旧版本；App audience、委托、app.close 及 OIDC 的已签短期离线证据与第三方自身 Cookie 仍可能存续到原期限，不能声称密码更新取消所有在途/离线业务。

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-007 -->
### BR-PWD-007：原子提交、幂等与秘密恢复

密码材料/版本、凭据下界/保留对象、新 Session（仅改密）、操作消费与不可变审计共用 Auth 事务栅栏。昂贵 hash 在事务外准备，提交/重试重新比较全部快照；不得接受旧密码校验后另一个密码版本已提交。任一失败回滚，未知提交不宣称失败回滚或发送成功通知。

改密幂等为 `(authId, requestId)`，操作至少保留 24 小时；同键输入指纹不同冲突。独立 operation HMAC tag 不存旧/新密码明文，新 token 只首次提交返回。响应丢失时当前私钥→UC007→GetOwnPasswordChange；若私钥不可用，可明确 UC012/034 登录，再查原 requestId。NOT_FOUND 只代表当前观察点未见完成，不证明在途请求不会提交，不据此换新 ID 自动再改密。

最终写入还尊重 UC024/025 既有退出/终止屏障，不用密码更新取消已提交注销、恢复 CLOSED 或绕过 App 归属退出义务；治理阻断按所属 UC 处理。

重置 Begin 按规范登录地址的受保护索引/requestId 幂等 24 小时，新真实操作可替代原本人未完成操作，检查额度/版本后才替代；同键不重发/延长，操作容量有界。首次 Complete 必须在 10 分钟内；完成记录保留窗口中只允许原码和同新密码输入、当前登录角色/密码/账号仍等于成功版本时恢复无秘密完成结果，不再次设置或推进版本。后来又换邮箱/改密码则旧完成结果不能成为新的授权，原操作失效。

审计记录 action、可信 owner/sourceSessionId 或邮箱恢复方式、操作 ID、版本、保留 credentialId（若有）、时间/结果；无密码/完整邮箱/码/hash/签名/token。通知用唯一事件 outbox，有界重试，不在事务中发信；投递失败不回滚已提交密码或重复产生变更。新密码、操作、通知、审计分类均纳入 UC025 终止清单与保留/备份恢复规则。

<!-- 权威位置: use-cases/UC-AUTH-033-manage-password-and-recovery.md#br-pwd-008 -->
### BR-PWD-008：限额、失败关闭与启用门禁

所有密码验证共用昂贵额度：默认单实例并发 4、队列 32/最长等待 2 秒，Argon 调用全局 120 单位/分钟、每来源 20、每 owner/地址 10；一次业务预留所需单位（校验＋新 hash 通常 2），事务重试不重扣。4096 细分桶、有限正配置、哈希前扣；取消请求不提前释放仍运行计算的执行槽。来源仅 socket，地址 HMAC；账户/地址失败额度用共用 Mongo，不因错密码永久禁用账号。

邮件重置共享既有发送额度，不能按用途翻倍。提案：有效 reset 每账号 1、password login 每 owner/匿名地址 5，全局合计 PENDING 10000；保留记录全局最多 1000000，达到容量拒绝新操作，不驱逐活跃/幂等记录。幂等键/状态/过期索引及共享认证栅栏原子保护容量，TTL 不代替业务计数；匿名占位同样占额。一般入口共享全局 600/来源 120/确认 owner 30 次每分钟及 4096 桶。通知 outbox 不占用户验证码额度，实施压测/索引和任务清理仍须验收。

错误密码/不存在账号/非登录邮箱等认证失败统一，依赖故障与限流可区分；不得响应裸数据库/crypto 信息。入口默认关闭，必须升级全部密码/下界/认证消费路径、准备正式 blocklist 与 hash 压测、完成公开向量/API/Wire/Mongo race/跨服务验证才可启用。系统未部署，不设计生产旧账号自动设密码/补代际；旧测试数据显式重建或隔离，不静默迁移/删除。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-password-v1.md`：平台密码与密码登录协议 v1 草案

#### 权威与兼容边界

业务规则唯一见 [UC033 密码管理/恢复](../use-cases/UC-AUTH-033-manage-password-and-recovery.md)、[UC034 密码登录](../use-cases/UC-AUTH-034-login-with-password.md)，邮箱角色见 UC011、密码注册见 UC006。本文只固定客户端/Auth/Gateway 的消息与安全载体提案，不是可执行 Proto，也未提供已验收的公开向量。

2026-10-13 用户授权开始实现，本文字段号、编码和默认参数随 UC033/034 接受。既有设备 LOGIN、邮箱码 LOGIN_WITH_EMAIL 和无密码邮箱注册 v2 字节不被改写；新密码字段/入口必须显式版本化，不通过向旧消息追加秘密、复用退役字段或自动降级实现。公开向量、可执行 API 和启用验证独立跟踪，接受不表示交付完成。

#### 秘密输入与载体

- 仅 TLS 传密码，密码为用户输入的 UTF-8 string；规范化/策略/存储唯一见 BR-PWD-001/002。不由客户端 SHA-256 后把摘要当认证密码，密码不进入 Frame/signingPayload、URL、日志、审计、错误或邮件。
- JSON 固定 lowerCamelCase、bytes 为标准 ProtoJSON Base64、时间为 int64 UTC Unix 毫秒（JSON string）、requestId/operationId 为小写 UUIDv4。body 最大 16 KiB，严格拒绝未知/重复/null/错误分支/query，响应 no-store。
- Session 唯一载体仍 `x-iwut-session`；不接受 Authorization/Cookie/JWS/OAuth token 替代。要求匿名的入口 Session 键必须不存在，已提供空/失效 token 不允许删除后重试匿名。
- Gateway DIRECT 只转发精确方法，不验证密码/owner、不签发“已验证密码”身份头；未知方法默认拒绝，正文与秘密不进入代理日志。

#### 方法与逻辑消息

package `auth_center.v1.password_management` / `PasswordManagementService`：

| 方法 | 内部 HTTP 提案 | 载体/成功 |
| --- | --- | --- |
| ChangeOwnPassword | POST `/v1/users/me/password:change` | 有效 Session；PasswordChanged，含一次性新 Session |
| GetOwnPasswordChange | POST `/v1/users/me/password-changes:get` | 有效 Session；本人 requestId 的无秘密状态 |
| BeginPasswordReset | POST `/v1/password-resets` | 明确匿名；PasswordResetStarted |
| CompletePasswordReset | POST `/v1/password-resets:complete` | 明确匿名；PasswordResetCompleted，无 Session |

package `auth_center.v1.password_login` / `PasswordLoginService`：

| 方法 | 内部 HTTP 提案 | 载体/成功 |
| --- | --- | --- |
| BeginPasswordLogin | POST `/v1/password-logins` | 明确匿名；PasswordLoginStarted |
| CompletePasswordLogin | POST `/v1/password-logins:complete` | 明确匿名；PasswordLoginResult，一次性 Session |

完整 RPC 为 `/<package>.<service>/<method>`，六个 exact 方法分别登记，原生 gRPC/HTTP 同语义。以下字段号已接受，独立 API 按本契约实施；表中路径不是现有生产清单。

| 消息 | 字段号/类型 |
| --- | --- |
| ChangeOwnPasswordRequest | 1 string request_id；2 string current_password；3 string new_password |
| PasswordChanged | 1 string operation_id；2 Auth.SessionEstablished session |
| GetOwnPasswordChangeRequest | 1 string request_id |
| OwnPasswordChange | 1 PasswordChangeStatus status；2 optional string operation_id；3 int64 observed_at_unix_ms |
| BeginPasswordResetRequest | 1 string request_id；2 string login_email |
| PasswordResetStarted | 1 string operation_id；2 int64 expires_at_unix_ms；3 int64 resend_after_unix_ms |
| CompletePasswordResetRequest | 1 string operation_id；2 string code；3 string new_password |
| PasswordResetCompleted | 1 string operation_id |
| BeginPasswordLoginRequest | 1 string request_id；2 string login_email；3 Auth.CredentialRegistrationProposal credential_proposal |
| PasswordLoginStarted | 1 string operation_id；2 bytes challenge；3 bytes signing_payload；4 string protocol_version；5 int64 expires_at_unix_ms |
| CompletePasswordLoginRequest | 1 string operation_id；2 string password；3 Auth.CredentialProof proof |
| PasswordLoginResult | 1 string auth_id；2 string credential_id；3 Auth.SessionEstablished session |

PasswordChangeStatus：UNSPECIFIED=0（不允许成功）、NOT_FOUND=1、COMPLETED=2；NOT_FOUND 没有 operationId，COMPLETED 必须有。所有 string 请求字段非空且必需，proof/proposal/session presence 必需，当前旧 Session 无效不得返回完成秘密。密码校验输入不套用新设置的 blocklist/最短门限，验证已有 hash；所有路径按其规范化版本处理且有原始长度上限，新设置必须满足 UC033 策略。

注册还需单独受版本保护的“邮箱验证＋密码设置＋设备证明”完成请求（UC011），不能让旧无密码 REGISTER 绕过新模型。添加非登录邮箱与切换登录角色须区分：Session＋新邮箱码不足以切换。危险动作采用所属 UC 的 Complete 带当前密码，在 Auth 最终提交边界复核；不签发通用解锁 token。

2026-10-13 六个消息/RPC 已进入独立 API Proto 并生成 Go/gRPC/HTTP 客户端；Auth 公开服务仍未注册。新注册/邮箱目录方案见[已接受的邮箱账号 v3 契约](../../platform/contracts/auth-email-account-v3.md)，已实施邮箱核心，但不属于已交付的普通密码登录/重置 API。

#### 密码验证与幂等记录

新操作 HMAC 秘密独立于邮箱/JWS/设备算法；提案使用 `AUTH_PASSWORD_OPERATION_HMAC_KEY`，严格标准 Base64 随机 32 字节，keyId 用设备 Frame 标签隔离后 SHA-256 派生。该 key 不是密码 salt，不代替 Argon2id。

改密请求指纹编码提案：

```text
HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-change-request-v1"), UTF8(authId), UTF8(requestId),
  UTF8(originalSessionId), U64BE(originalAccountRevision), U64BE(originalPasswordRevision),
  UTF8(normalizedCurrentPassword), UTF8(normalizedNewPassword)
))
```

只持久化 tag/keyId 与必要版本/标识，不保存上述含密码明文的 Frame；24 小时窗口后删除。完成重试使用记录原 sourceSessionId/版本重建 tag，不以新 Session 改写原操作；不重返秘密。重置用途为 RESET_PASSWORD，提案编码如下（U64BE 整数均服务端生成、非负，角色版本属于唯一登录角色）：

```text
resetRequestMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-request-v1"), UTF8(requestId), UTF8(normalizedLoginEmail),
  UTF8(serviceId), UTF8("iwut-client")))
resetCodeMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-code-v1"), UTF8("RESET_PASSWORD"), UTF8(operationId),
  UTF8(authId), U64BE(loginRoleRevision), U64BE(passwordRevision), U64BE(accountRevision),
  U64BE(expiresAtUnixMs), resetRequestMac, UTF8(code8)))
resetCompletionMac = HMAC-SHA256(K_operation, Frame(
  UTF8("iwut-password-reset-completion-v1"), UTF8(operationId), resetCodeMac,
  UTF8(normalizedNewPassword)))
keyId = SHA256(Frame(UTF8("iwut-password-operation-key-id-v1"), K_operation))
```

占位 resetCodeMac 用随机 dummy owner/版本，只用于 acceptable=false，不给真实账号补默认。真实码/完成 tag 最终复核固定版本，不赋新授权。短期重置记录可在 Auth 保护的存储保存规范地址，幂等唯一键 `(normalizedLoginEmail,requestId)` 不依赖可冷换 operation key，因此换钥不能绕过原幂等窗口；邮箱不进日志/审计。匿名地址限流桶采用既有邮件额度的受保护地址键，operation key 不为它派生新预算。

冷换操作 key 应使未完成操作不可消费，不影响长期 Argon2id 密码；完成记录只能按 UC033 只读恢复，不能借旧 HMAC 制造新变更。密码变更与账号治理/登录角色切换的版本复核优先于历史幂等成功。

#### Session 与安全代际

- UC034 新登录方法 `PASSWORD_AND_DEVICE`：credentialId、passwordRevision>0，新的 accountRevision/认证时间；必须有本次新签名。
- UC033 正常改密换发方法 `PASSWORD_AND_SESSION`：credentialId、sourceSessionId、passwordRevision>0、新 accountRevision/认证时间；来源是旧 Session＋当前密码，不伪造 device 签名。token/sessionId 新建，旧来源 Session 不继续有效。
- 保留既有 DEVICE_CREDENTIAL、EMAIL_CODE_AND_DEVICE；所有方法都要求合法当前凭据、owner、UC033 凭据下界和 UC022 账号代际，并在 LRU/列表/身份签发/OAuth 绑定/退出等消费路径完整分派；未知/缺字段失败关闭。

设备凭据新字段 credentialRevision 与 principal.minimumCredentialRevision 只在服务端持久化/检查，不添加到既有 LOGIN 字节。正常改密/重置推进 accountRevision，旧 Auth audience identity 与 opaque OAuth 材料拒绝；App 离线 JWS/第三方自有登录态的旧残余窗口不由新 Session 格式收回。

#### 接受与交付门禁

统一 reason：400 INVALID_PASSWORD_REQUEST/PASSWORD_POLICY_REJECTED/PASSWORD_UNCHANGED；401 SESSION_INVALID/PASSWORD_AUTHENTICATION_FAILED/PASSWORD_RESET_FAILED；409 PASSWORD_REVISION_CONFLICT/PASSWORD_REQUEST_CONFLICT/PASSWORD_CHANGE_ALREADY_COMPLETED/PASSWORD_LOGIN_ALREADY_COMPLETED；429 PASSWORD_RATE_LIMITED；503 PASSWORD_UNAVAILABLE。正文过大为 413 PASSWORD_REQUEST_TOO_LARGE；邮件明确投递故障沿用 EMAIL_DELIVERY_UNAVAILABLE。密码登录除语法/限流/依赖外统一 PASSWORD_AUTHENTICATION_FAILED，包含密码、owner、角色、签名、操作无效，不区分不存在账号。

字段/HMAC 已接受；须补公开 Frame/hash/MAC/NFC 正反向量、验证注册版本及敏感动作无旁路；算法参数压测、blocklist 正式来源和容量实际测试为启用门禁。脚本开工 brief 已配置，可执行 API 独立交付，不改变历史向量。

公开测试向量：[auth-password-v1.json](../../platform/contracts/test-vectors/auth-password-v1.json)；生成/校验脚本 `tools/auth_password_protocol_vectors.py --write/--check`，需 cryptography 和 argon2-cffi（独立 libargon2）。Go 使用 x/crypto 校验同一 hash/Frame/MAC/NFC 与 DER 正反向量；所有固定密码/salt/key/码仅供公开测试，绝不能作为运行默认。原设备/邮箱 v1/v2 文件未改写。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-033`（use-cases/UC-AUTH-033-manage-password-and-recovery.md）：主流程/正常修改、主流程/忘记密码重置
- `platform/contracts/auth-password-v1.md`（docs 根级共享文档）：密码登录签名字节

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-033-manage-password-and-recovery.md` | 171 | `12caeedc7b93` |
| `platform/contracts/auth-password-v1.md` | 124 | `0ac9cd7021d3` |
