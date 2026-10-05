<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-025 --spec tools/brief-specs/UC-AUTH-025.json -->
# Brief — UC-AUTH-025：本人注销账号

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-025` 本人注销账号 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-ACC-009`–`BR-ACC-014`（6 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/account-owner-exit-v1.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

用户明确确认后不可恢复地终止自己的平台账号，并通过可重试任务清理 Auth 的个人资料和认证数据。终止作用于已证明控制权的一个 authId，不包括同一 associationId 下的其他账号，也不宣称能够删除第三方已取得的数据。

首版不设注销冷静期或恢复窗口。分开表达“账号已终止”和“活动存储清理完成”；备份、必要墓碑及历史审计的保留范围单独披露。本文的保留时间是已接受的产品/运维方案，不作法律合规结论。

### 认证与资格

使用当前仍有效的已登记设备凭据，完成专用于注销的全新挑战签名；不能只凭已有 Session、学校账号声明、邮箱字符串或普通 LOGIN 证明注销。支持 ACTIVE 和 DISABLED USER，后者只能经此专用证明走注销流程，不签发普通 Session、不解除禁用。CLOSED、SYSTEM、未知/撤销凭据不能取得注销授权。

普通用户无需先绑定邮箱，无生物识别要求。ACTIVE 用户丢失全部设备私钥但有可用邮箱时，可先经 UC012 恢复本机凭据；DISABLED 用户若同时没有有效私钥，需另行受理控制权核验，不能把普通邮箱登录开放为解禁入口。该人工受理流程仍为产品上线依赖。

用户须先交接平台管理员资格并撤销全部管理权限；即使存在其他管理员也不能在注销操作里隐式撤销自身管理集合。最后管理员保护仍复用 UC021，不以注销绕过。

ACTIVE 且 APPROVED 的 Developer 须先完成 UC024 退出。DISABLED 账号不能使用 UC024，因此允许其在 App 确认零归属义务后直接终止 Developer 身份与账号，不要求先解禁。null、WITHDRAWN 可进入注销；PENDING/REJECTED/SUSPENDED 不要求管理员先恢复为 APPROVED，只要 App 确认没有归属义务即可终止账号，待处理申请一并终止，历史治理事实保留，不转成可重新申请的 null。这样既不允许借自助退出绕过暂停，也不把暂停者永久困在不能注销的状态。

### API 与确认过程

独立 package `auth_center.v1.account_closure`，service `AccountClosureService`；Gateway DIRECT，HTTP 与原生 gRPC 同时交付，精确方法鉴权。以下均不接受 Session/JWS/OAuth token 混合认证；身份来自专用设备证明或用途受限的注销令牌，不扩大其他方法的匿名例外。

| 方法 | HTTP POST 路径 | 输入及输出 |
| --- | --- | --- |
| BeginAccountClosure | /v1/account-closures:begin | credentialLocator、requestId → operationId、challenge、signingPayload、expiresAt |
| PrepareAccountClosure | /v1/account-closures:prepare | operationId、signature → preview、confirmationToken、receiptToken |
| ConfirmAccountClosure | /v1/account-closures:confirm | operationId、confirmation=CLOSE_ACCOUNT、policyVersion；专用 confirmationToken → 状态 |
| CancelAccountClosure | /v1/account-closures:cancel | operationId；专用 confirmationToken → 状态 |
| GetAccountClosure | /v1/account-closures:get | operationId；专用 receiptToken → 最小状态 |

confirmationToken 仅放 `x-iwut-closure-confirmation`，receiptToken 仅放 `x-iwut-closure-receipt`；每次只允许对应方法唯一载体，不放 URL/query，不与通用 Authorization 混用。均为 CSPRNG 32 bytes 的规范无填充 Base64URL，服务端只保存带不同用途前缀的 SHA-256 摘要。receiptToken 不能确认、取消或登录，confirmationToken 不能作为 Session。

Prepare 仅在设备证明成立且没有 blocker、App 屏障就绪后返回两个秘密，其他结果不产生令牌。秘密只当次返回，不持久化明文；丢失响应可用新挑战重试，旧未决操作按取消协议收敛，不能自动撤掉已 COMMITTED 的操作。Get 不返回 authId、邮箱、handle、资料或原因，只返回 `PREPARING | READY | CANCELLED | TERMINATION_PENDING | TERMINATED | CLEANUP_COMPLETE`、terminatedAt、清理进度类别和备份最迟自然淘汰时间；故障不能伪报完成。

preview 向已证明身份的本人返回 authId、developerHandle（如有）、明确的清理/保留摘要、policyVersion、不可恢复提示及 expiresAt。客户端先展示，再由用户明确 Confirm；不得把 Prepare 自动接到 Confirm。本人 blocker 可含 ADMIN_HANDOVER_REQUIRED、DEVELOPER_WITHDRAWAL_REQUIRED、OWNED_APPLICATIONS、PENDING_OWNERSHIP_CHANGE、LIFECYCLE_OPERATION_PENDING。BLOCKED 不占用 App 屏障、无确认令牌；已建立的协调操作保存 CANCELLED 并释放未决占用。

严格 ProtoJSON、无 query/未知或重复字段、16 KiB 上限、UTC Timestamp、no-store。受限读取在注销后仍可用，令牌最长保留 30 天，不给已终止账号建立另一种登录态。

### 主流程

1. Begin 固定凭据归属、当前 accountRevision、凭据状态、policyVersion 和 5 分钟挑战；未知/不可用目标返回相同外形的不可完成占位操作，不能后来因记录变化而成为有效注销。
2. Prepare 验证专用签名，复核资格/当前状态，保存当时的 accountRevision、developerRevision、permissionRevision、凭据及生命周期操作引用，然后调用 App 归属退出协议。验证成功不终止账号。
3. App 确认零义务并设置屏障后，返回预览及用途隔离的令牌；其截止时间仍为原挑战的 5 分钟期限，不因查询或重试延长。
4. Confirm 在同一 Auth 事务内复核令牌、原凭据仍有效、所有版本及 policyVersion 未变、App receipt 就绪、管理交接完成且未过期，执行终止。
5. 将账号置为 CLOSED，递增 accountRevision，清空当前权限/Developer 能力投影，原子保存最小终止事实、COMMITTED 决定、清理任务和不可变注销审计；确认提交后账号已不可恢复；独立终止清单确认持久化前返回 TERMINATION_PENDING，确认后才返回 TERMINATED。
6. 后台工作按有界批次幂等清理，通知 App 永久 sealed 并等待回执；最终检查通过后返回 CLEANUP_COMPLETE。失败重试保持 CLOSED，永不自动恢复 ACTIVE。

### 首版运行与协议固定值

policyVersion 精确为 `account-closure-v1`。注销秘密摘要输入为 `Frame(UTF8("iwut-closure-confirmation-v1"), token32)` 或 `Frame(UTF8("iwut-closure-receipt-v1"), token32)` 后 SHA-256，禁止混用域。公开设备证明向量由 tools/auth_account_closure_vectors.py 生成并校验，随实现提交。

独立终止清单首版使用 `AUTH_TERMINATION_LEDGER_DIR` 指定的独立持久目录，禁止位于业务临时目录或包含在业务数据库回滚流程中。每 operationId 一个规范 JSON 记录，原子创建、文件与目录 fsync 后才确认；重复完全相同内容幂等，不匹配或损坏失败关闭。进程启动与显式 `auth-center reconcile-account-closures` 停服命令都须读取/核验清单，重放更高终止版本并调度清理，禁止将 CLOSED 恢复 ACTIVE。目录和恢复流程由运维独立备份，代码不能证明外部备份策略已经执行。

`AUTH_CLOSURE_DATA_POLICY_READY` 默认 false，是运维确认清理服务清单、备份/日志 30 天上限、终止清单隔离及无密钥人工受理均已具备的声明；启用公网注销要求 true。测试以隔离目录和真实服务验证，不修改真实部署声明。清理后台任务每批 500，周期初始 1 秒、失败指数退避至 60 秒，参数可配置但有正值/容量边界。当前实际平台个人存储为 Auth 与 App；以后增加资源服务须先加入清单与回执再启用，不允许空壳依赖假装全平台完成。

### 错误、限额与验收

Begin 不披露账号状态；Prepare 对未知目标、签名无效、凭据撤销或版本变化统一 `ACCOUNT_CLOSURE_PROOF_INVALID`（401）。已证明本人后才能返回正常 BLOCKED 明细。非法输入 400；未知/不匹配令牌或 operation 统一 401；过期/版本或终局冲突 409；依赖/存储/未知提交 503；限流 429。数据损坏不能伪装为无归属或已清理。

入口默认关闭 `AUTH_ACCOUNT_CLOSURE_ENABLED`，依赖用户认证基础、App provider 和清理工作器配置；特殊 DISABLED 注销不绕过功能门禁。Begin 复用设备认证的有界 IP/locator 容量，证明后采用有界账号桶，初始写每分钟 10、收据读取每分钟 30；读写令牌摘要、签名和任何秘密不进入日志。

验收至少覆盖：ACTIVE/DISABLED 设备证明；无 Session、无邮箱普通用户；未知/撤销密钥与旧 LOGIN 签名；预览后权限/Developer/账号/凭据变化；SUSPENDED 无应用可终止而有应用阻止；最后管理员与并发交接；旧 JWS、token、邮箱 challenge/result 不复活；清理中断/重启/重复执行；邮箱释放后新注册不被旧任务删除；共享关联组并发注册；永久 handle/密钥占用；App 回执丢失；收据只读隔离；备份恢复重放终止清单。使用真实 Mongo 与双服务集成，不能只验证账号字段变成 CLOSED。

### 实现依赖与联动

硬依赖 UC021/022、UC023/024 的生命周期版本和取消规则、App 归属屏障/个人数据清理；上述尚未交付。还需全平台数据清单、备份/日志保留能力、终止清单恢复演练和禁用账号无密钥的人工受理流程。

实施时同步 UC002 的 CLOSED 主体查询及 App 历史审核处理、UC006–019/020–024 的 CLOSED 拒绝、UC013 handle 终止占用、UC015 pairwise 映射删除例外、所有审计保留规则、客户端引导、共享注销签名字节/公开向量及可执行 API。共享归属契约另与 App agent 对齐；不添加旧数据库迁移。本轮生成实施 brief 并交付后端；公网启用仍受恢复受理、数据清单和部署验收门禁约束。

## 业务规则（UC-AUTH-025 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-009 -->
### BR-ACC-009：明确终止与不可恢复

新增 accountStatus=CLOSED 终态，UC022 RESTORE 只能恢复 DISABLED，永不恢复 CLOSED。新认证、身份签发、邮箱恢复和历史结果重试对 CLOSED 一律拒绝；最小墓碑保证清理后仍不会把同 authId 当作可补建用户。CLOSED 墓碑是明确的合法存储形态，读取层先识别终态并拒绝认证，不再要求它具有普通 ACTIVE principal 的资料、权限或邮箱字段，也不能把它当作损坏的活动账号返回。

终止递增 accountRevision，使旧 Session、Auth audience JWS、code/token/family 和待完成操作失效，规则引用 UC022；每条实际消费仍检查 CLOSED，不因删除相应记录而放宽。Session、凭据和邮箱不再能授予普通操作，即使物理清理尚未执行。

删除不影响关联组其他账号。重新注册只能产生新 authId、新资料和新授权，不继承旧数据、pairwise sub 或 handle。学校关联不是自然人封禁证明；本用例不承诺阻止同一人创建另一账号。

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-010 -->
### BR-ACC-010：用途绑定的近期设备证明

注销证明使用设备协议的 P-256/SHA-256、规范 DER 和 Frame 基础编码，独立固定 payload：

```text
Frame(UTF8("iwut-account-closure-proof-v1"), UTF8("PREPARE_ACCOUNT_CLOSURE"),
      UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
      challenge32, U64BE(expiresAtUnixMs),
      UTF8(locatorKind), locatorValue, UTF8(policyVersion))
```

locatorKind/value 沿用设备登录的精确类型和编码；serviceId/applicationId 来自固定部署上下文。客户端签名前验证用途、自己选择的凭据、期限及政策版本；不接收任意服务端字节直接盲签。authId/账号版本由不可变服务端操作绑定，不泄露给未认证 Begin。禁止复用 LOGIN/REGISTER 签名或授权任意新公钥。

签名有效才可创建注销准备和展示本人信息；单有 Session 不能调用本方法替代证明。每操作最多 5 次失败验证。requestId 在 24 小时内只对同规范定位和提案去重，不延长期限；未知凭据 Begin 与 Complete 沿用认证入口的反枚举响应及有界容量。新的证明请求不能仅因 locator 相同就取消别人的准备，必须先验证真实签名。Prepare 的秘密结果只返回一次；新证明在原操作仍未提交时可原子取消原注销准备，等待 App 确认解除后重新准备。原操作已提交则禁止替换或取消；UC024 的未决退出仍须先单独完成或取消。

confirmationToken 一次消费，绑定 operation、本人 authId、上述版本、policyVersion 及 App receipt；只授权 CLOSE_ACCOUNT/提交前取消。重复 Confirm 若摘要匹配且已提交，只返回原最小状态，不再写数据。提交后再 Cancel 必须拒绝，不能重跑 bootstrap 或复用 receipt 恢复。

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-011 -->
### BR-ACC-011：归属、治理与竞争

所有账号都通过 [App 归属退出协议](../../platform/contracts/account-owner-exit-v1.md) 验证，不以 Developer 状态为空推断从未拥有应用。已 WITHDRAWN 的永久屏障可作为基础，但仍为本次注销建立绑定 receipt。不存在归属处置及屏障能力时，不启用注销。

原子终止与 UC021–024、UC013 开通、邮箱/凭据变更、用户权限及身份签发共用 Auth 认证协调边界；确认比较全部绑定版本与当前凭据。任何相关变更先提交，旧预览均不能继续执行，准备转 CANCELLED 后重新发起；终止先提交则后续业务命令拒绝。PENDING 申请后续审批也必须检查 CLOSED，不允许迟到的批准复活主体。

持有任何管理员管理权限时阻止注销，由 UC021 明确交接/撤销；独立 reviewer 权限可随终止清除，不删除其历史审核决定。SUSPENDED 账号无应用义务时可终止，其历史处罚不被改写成撤销处罚。禁用账号的专用注销授权仅用于本流程，不能用于退出 SUSPENDED Developer 或普通业务。

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

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-013 -->
### BR-ACC-013：清理任务与备份恢复

终止事务创建持久任务，按 collection/步骤以有界批次（初始 500 条）执行幂等清理；步骤完成事实和重试可跨进程重启恢复。大批历史数据不放入一个长 Mongo 事务。逻辑终止与 cleanup 状态分离，任务失败不恢复账号、不释放未确认安全的跨服务屏障。

对邮箱归属、设备占用墓碑和学生共享组使用专门事务与唯一约束，不做无归属条件的批量删除。清理始终使用原 authId，不能按已释放且可能被新账号使用的邮箱或学号散列删除数据。

保留独立于旧业务备份的最小终止清单（authId、最终 accountRevision、terminatedAt、operationId），与墓碑同等保护并持续备份。Auth 终止事务写持久待投递记录，以 operationId 幂等写入不会随业务备份回滚的清单；收到持久化确认前只展示 TERMINATION_PENDING，本地 CLOSED 不可取消或回滚，投递故障必须告警并重试。恢复历史备份后先隔离服务，重放此清单、重新执行清理并核验，再接流量，防止旧备份复活账号。清单不可用、可能不完整或未能核验最新终止事实时保持停服，不直接以旧备份接流量。清单同步和恢复演练是上线门禁；未完成前不能承诺已终止账号不会因灾备回滚复活。

清理不删除 App 的历史应用/审核事实。App 还需清理该账号的 Tester membership、个人过滤偏好等个人状态，并确认终局 sealed；其幂等清理及有界完成回执属于 App 新 UC 的交付范围。其它平台资源服务若另存用户数据，必须进入数据清单和清理协调验收，不能以 Auth 数据已清理宣称全平台清理完成。

<!-- 权威位置: use-cases/UC-AUTH-025-close-own-account.md#br-acc-014 -->
### BR-ACC-014：结果、审计与第三方边界

终止状态、最小审计、清理任务和归属协议 COMMITTED 决定同一事务提交。审计只记录 operationId、subjectAuthId、认证方式/凭据引用、policyVersion、终止时间及版本；认证来源为 DEVICE_PROOF，不伪造有效 Session 操作，不记录退出自由文本理由或完整签名。

TERMINATION_PENDING 已终止本地账号、正在确认独立终止清单，仍不可恢复；TERMINATED 表示终止清单亦已确认，账号不可再登录；CLEANUP_COMPLETE 只在 Auth 活动数据清理、App 个人状态清理和必须的其他平台服务回执都完成后返回，同时列明永久保留项及备份到期边界。收据丢失后不能通过原邮箱、旧 Session 或匿名 authId 查询终止详情；必要的用户支持由独立核验流程处理。

已有 App audience/委托短期 JWS 仍存在 UC022 定义的离线有效期窗口，第三方自建登录态或已导出的数据不能被本用例删除。客户端应在确认终止后删除本地 Session 和设备私钥；失败或结果不确定时先保留收据查询，不能通过本地删除声称服务端已经注销。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/account-owner-exit-v1.md`：账号退出时的 App 归属协调 v1

#### 范围与事实来源

本契约是 [UC024](../use-cases/UC-AUTH-024-withdraw-developer.md) 和 [UC025](../use-cases/UC-AUTH-025-close-own-account.md) 所需的 Auth/App 实现契约，App 工作包见 UC-APP-025。Auth 决定资格退出或账号终止；App 决定哪些应用及归属操作仍需该账号承担责任，并阻止并发新增归属。不能用一次无保护的查询代替本协议。

首版 App 中所有 `adminId=authId` 的 Application（包括草稿、审核中、未发布、已发布）都阻止退出。仅清空发布槽不算处置；转让、关闭如何移除归属义务由后续 App UC 明确，在其交付前拥有应用的用户无法完成此流程。历史 creator/reviewer 引用不等于当前所有权，但存在仍需该账号负责的待处理归属操作也阻止退出。

#### 内部接口

均为原生 gRPC、独立 trusted-service-identity 方法权限和调用方 allowlist，Auth→App，Finish 的决定必须与 Auth 持久状态一致；不通过用户 Gateway，不信任终端声称“没有应用”。

```text
PrepareAccountOwnerExit {
  authId, operationId: opaque ID
  purpose: DEVELOPER_WITHDRAWAL | ACCOUNT_CLOSURE
}
OwnerExitPreparation {
  outcome: PREPARED | BLOCKED
  receiptId: opaque ID?  // 只有 PREPARED 返回
  blocker: OWNED_APPLICATIONS | PENDING_OWNERSHIP_CHANGE | NONE
}
FinishAccountOwnerExit {
  authId, operationId, receiptId?: opaque ID
  decision: COMMITTED | CANCELLED
  purpose: DEVELOPER_WITHDRAWAL | ACCOUNT_CLOSURE
}
```

另由 Auth 向获授权 App 提供 `GetAccountOwnerExitDecision(authId, operationId)`，返回 `PENDING | COMMITTED | CANCELLED`；未知操作返回 NOT_FOUND，不能解释为已取消。Auth 保存的 purpose 和归属目标必须与 App 一致；已获得的非空 receipt 必须精确一致。消息中的 authId 只是被治理对象，不是伪造的终端操作人身份。

#### App 原子屏障

App 的 Prepare 在同一账号归属事务栅栏下检查义务并安装屏障。所有创建应用、转入所有权、撤销转出、恢复已关闭应用以及将来可能增加归属义务的写操作必须参与同一栅栏；包括持有旧 APPROVED JWS 的请求。不能只在 HTTP handler 做预检查。

存在义务时返回 BLOCKED，不安装屏障，不自动转让、关闭或删除应用；用户处理后用新操作重试。零义务时返回 PREPARED，保存不可变 `(authId, operationId, purpose, receiptId)`，阻止该账号新增归属，直到收到终局决定。重复相同请求返回同一结果；同 operationId 换 authId/purpose 或不匹配 receipt 拒绝。

COMMITTED 将本次屏障变为永久 sealed，不允许未来凭旧 JWS 创建或转入应用。首版 Developer 退出不支持重新开通，因此无需解封接口。已因 Developer 退出 sealed 的账号之后申请注销时，仍重新核验无义务，为注销 operation 生成独立 receipt；取消注销不会解除之前的永久 sealed 状态。

COMMITTED 必须携带与 App 完全匹配的非空 receiptId。CANCELLED 允许 receiptId 为空，以覆盖 Prepare 已建立屏障但回包丢失的情况；只对可信 Auth 调用且 authId/operationId/purpose 全部匹配生效，传入非空 receiptId 时仍必须精确匹配。CANCELLED 仅解除该 operation 创建的临时屏障，不能解除其他操作或既有永久 sealed。即使 Prepare 尚未到达，Finish(CANCELLED) 也保存该 operation 的终局记录，拒绝后来延迟到达的 Prepare；不能出现“先取消，再被迟到的准备永久锁住”。一个 authId 同时最多一个未决归属退出操作。

#### Auth 协调与故障

Auth 先保存 PENDING 操作，再调用 Prepare；准备操作寿命最多 10 分钟。随后在 Auth 事务中复核 Session/专用注销证明、accountRevision、developerRevision、权限和业务条件，只有 PREPARED receipt 对应原操作且仍在期限内才可提交资格退出/账号终止，同时写 COMMITTED 决定与待投递通知。

用户取消、条件变化或准备超时由 Auth CAS 为 CANCELLED，不能取消已提交操作。事务提交结果未知时先读取权威决定，不发送推测的 CANCELLED。账号终止后的清理任务不能删除尚未被 App 确认的协调决定。

App 屏障不按租约或本地 TTL 自动解除：Auth 可能已经提交而通知丢失。双方使用持久化、幂等重试收敛，App 可向 Auth 查询终局；Auth 不可用时保持屏障并返回依赖故障。孤立 PENDING 由 Auth 到期任务确认取消再通知，不以“找不到”当取消。故障期间用户可见“处理中/尚未完成”，不能声称数据或资格已经删除。

App 收到终局后回执；Auth 在回执前保留决定。只有协调已终结且超过外部调用最大重试窗口后才允许压缩操作明细；永久 sealed 的最小 authId/purpose/终止操作引用保留。终局不得回退。此为两个本地事务与持久补偿，不假设分布式事务、消息必达或 Redis。

#### 固定线格式与方法授权

App package `app_center.v1.account_owner_exit`、service `AccountOwnerExitService`，PrepareAccountOwnerExit / FinishAccountOwnerExit / GetAccountOwnerExitStatus 分别要求 `app.account-owner-exit.prepare` / `app.account-owner-exit.finish` / `app.account-owner-exit.read`，仅授权 Auth caller。Auth package `auth_center.v1.account_owner_exit`、service `AccountOwnerExitDecisionService/GetAccountOwnerExitDecision` 要求 `auth.account-owner-exit.read`，仅 App caller。均无 HTTP annotation 或终端路由。

消息字段号固定：PrepareRequest auth_id=1, operation_id=2, purpose=3；FinishRequest auth_id=1, operation_id=2, receipt_id=3, decision=4, purpose=5；GetStatusRequest 与 GetDecisionRequest 均 auth_id=1, operation_id=2。Purpose 枚举 0=UNSPECIFIED(拒绝),1=DEVELOPER_WITHDRAWAL,2=ACCOUNT_CLOSURE；Decision 0=UNSPECIFIED,1=PENDING,2=COMMITTED,3=CANCELLED，Finish 不允许 PENDING。

PrepareResponse outcome=1（0非法,1=PREPARED,2=BLOCKED）,receipt_id=2,blocker=3（0=NONE,1=OWNED_APPLICATIONS,2=PENDING_OWNERSHIP_CHANGE）。App 状态/Finish 响应统一 auth_id=1,operation_id=2,purpose=3,decision=4,receipt_id=5,cleanup_state=6（0非法,1=NOT_REQUIRED,2=PENDING,3=COMPLETE）。GetDecisionResponse decision=1,purpose=2,receipt_id=3。状态查询对未知 operation 返回 NOT_FOUND，不暗示取消。

App 的 ACCOUNT_CLOSURE COMMITTED 持久创建个人清理任务，GetStatus 的 cleanup_state=COMPLETE 才表示个人数据清理回执；WITHDRAWAL 为 NOT_REQUIRED。Auth 先调用 Finish 再轮询持久状态确认 App 回执，不把 Finish 网络成功误认为全部清理完成。App 也可回查 Auth 终局用于收敛。

AuthId 沿用现有 1..200 bytes opaque ID；operationId 为 Auth UUIDv4，receiptId 为 App 生成 UUIDv7，不作秘密；所有比较原样精确。双边后台重试初始 1 秒、指数退避最大 60 秒，每批最多 100，RPC deadline 5 秒，含有界抖动。部署参数可调整但不得把到期当作自动解除屏障。每个操作的终局摘要永久保留至关联墓碑被明确政策替代，避免任意迟到 Prepare 越过已清理的取消记录；大体量诊断材料在回执后 30 天内清理。

#### 交付门禁

提供方权威用例为 UC-APP-025，支持零归属用户。转让/关闭已有应用不在本轮，有应用者持续 BLOCKED。必须更新实际创建入口和 ACCOUNT_CLOSURE 下 Tester 加入入口，防止旧 JWS 重建个人状态；未来增加归属写入口必须复用此屏障。

验收覆盖 Prepare 与创建竞争、取消先于 Prepare、Auth 提交后丢响应、双边重启、长时间故障、过期准备、重复 Finish、目标/receipt/purpose 错配、WITHDRAWN 后注销取消不解除原 sealed、注销清理与 Tester 加入竞争。联调前退出/注销公网开关保持关闭。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-025`（use-cases/UC-AUTH-025-close-own-account.md）：变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-025-close-own-account.md` | 157 | `ca8b8577d101` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `70d736bfa904` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
