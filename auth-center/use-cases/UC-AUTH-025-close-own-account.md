# UC-AUTH-025：本人注销账号

状态：`ACCEPTED`

## 目标与范围

用户明确确认后不可恢复地终止自己的平台账号，并通过可重试任务清理 Auth 的个人资料和认证数据。终止作用于已证明控制权的一个 authId，不包括同一 associationId 下的其他账号，也不宣称能够删除第三方已取得的数据。

首版不设注销冷静期或恢复窗口。分开表达“账号已终止”和“活动存储清理完成”；备份、必要墓碑及历史审计的保留范围单独披露。本文的保留时间是已接受的产品/运维方案，不作法律合规结论。

## 认证与资格

使用当前仍有效的已登记设备凭据，完成专用于注销的全新挑战签名；不能只凭已有 Session、学校账号声明、邮箱字符串或普通 LOGIN 证明注销。支持 ACTIVE 和 DISABLED USER，后者只能经此专用证明走注销流程，不签发普通 Session、不解除禁用。CLOSED、SYSTEM、未知/撤销凭据不能取得注销授权。

普通用户无需先绑定邮箱，无生物识别要求。ACTIVE 用户丢失全部设备私钥但有可用邮箱时，可先经 UC012 恢复本机凭据；DISABLED 用户若同时没有有效私钥，需另行受理控制权核验，不能把普通邮箱登录开放为解禁入口。该人工受理流程仍为产品上线依赖。

用户须先交接平台管理员资格并撤销全部管理权限；即使存在其他管理员也不能在注销操作里隐式撤销自身管理集合。最后管理员保护仍复用 UC021，不以注销绕过。

ACTIVE 且 APPROVED 的 Developer 须先完成 UC024 退出。DISABLED 账号不能使用 UC024，因此允许其在 App 确认零归属义务后直接终止 Developer 身份与账号，不要求先解禁。null、WITHDRAWN 可进入注销；PENDING/REJECTED/SUSPENDED 不要求管理员先恢复为 APPROVED，只要 App 确认没有归属义务即可终止账号，待处理申请一并终止，历史治理事实保留，不转成可重新申请的 null。这样既不允许借自助退出绕过暂停，也不把暂停者永久困在不能注销的状态。

## API 与确认过程

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

## 主流程

1. Begin 固定凭据归属、当前 accountRevision、凭据状态、policyVersion 和 5 分钟挑战；未知/不可用目标返回相同外形的不可完成占位操作，不能后来因记录变化而成为有效注销。
2. Prepare 验证专用签名，复核资格/当前状态，保存当时的 accountRevision、developerRevision、permissionRevision、凭据及生命周期操作引用，然后调用 App 归属退出协议。验证成功不终止账号。
3. App 确认零义务并设置屏障后，返回预览及用途隔离的令牌；其截止时间仍为原挑战的 5 分钟期限，不因查询或重试延长。
4. Confirm 在同一 Auth 事务内复核令牌、原凭据仍有效、所有版本及 policyVersion 未变、App receipt 就绪、管理交接完成且未过期，执行终止。
5. 将账号置为 CLOSED，递增 accountRevision，清空当前权限/Developer 能力投影，原子保存最小终止事实、COMMITTED 决定、清理任务和不可变注销审计；确认提交后账号已不可恢复；独立终止清单确认持久化前返回 TERMINATION_PENDING，确认后才返回 TERMINATED。
6. 后台工作按有界批次幂等清理，通知 App 永久 sealed 并等待回执；最终检查通过后返回 CLEANUP_COMPLETE。失败重试保持 CLOSED，永不自动恢复 ACTIVE。

## 业务规则

<a id="br-acc-009"></a>
### BR-ACC-009：明确终止与不可恢复

新增 accountStatus=CLOSED 终态，UC022 RESTORE 只能恢复 DISABLED，永不恢复 CLOSED。新认证、身份签发、邮箱恢复和历史结果重试对 CLOSED 一律拒绝；最小墓碑保证清理后仍不会把同 authId 当作可补建用户。CLOSED 墓碑是明确的合法存储形态，读取层先识别终态并拒绝认证，不再要求它具有普通 ACTIVE principal 的资料、权限或邮箱字段，也不能把它当作损坏的活动账号返回。

终止递增 accountRevision，使旧 Session、Auth audience JWS、code/token/family 和待完成操作失效，规则引用 UC022；每条实际消费仍检查 CLOSED，不因删除相应记录而放宽。Session、凭据和邮箱不再能授予普通操作，即使物理清理尚未执行。

删除不影响关联组其他账号。重新注册只能产生新 authId、新资料和新授权，不继承旧数据、pairwise sub 或 handle。学校关联不是自然人封禁证明；本用例不承诺阻止同一人创建另一账号。

<a id="br-acc-010"></a>
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

<a id="br-acc-011"></a>
### BR-ACC-011：归属、治理与竞争

所有账号都通过 [App 归属退出协议](../../platform/contracts/account-owner-exit-v1.md) 验证，不以 Developer 状态为空推断从未拥有应用。已 WITHDRAWN 的永久屏障可作为基础，但仍为本次注销建立绑定 receipt。不存在归属处置及屏障能力时，不启用注销。

原子终止与 UC021–024、UC013 开通、邮箱/凭据变更、用户权限及身份签发共用 Auth 认证协调边界；确认比较全部绑定版本与当前凭据。任何相关变更先提交，旧预览均不能继续执行，准备转 CANCELLED 后重新发起；终止先提交则后续业务命令拒绝。PENDING 申请后续审批也必须检查 CLOSED，不允许迟到的批准复活主体。

持有任何管理员管理权限时阻止注销，由 UC021 明确交接/撤销；独立 reviewer 权限可随终止清除，不删除其历史审核决定。SUSPENDED 账号无应用义务时可终止，其历史处罚不被改写成撤销处罚。禁用账号的专用注销授权仅用于本流程，不能用于退出 SUSPENDED Developer 或普通业务。

<a id="br-acc-012"></a>
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

现有审计的 append-only 表示保留期内不可更新/删除；接受本 UC 时需要明确增加受控保留期清理例外，不能由普通业务账号任意删除审计。永久墓碑的字段就是允许保留的完整集合，不能附加整份 principal 或自由文本快照。

<a id="br-acc-013"></a>
### BR-ACC-013：清理任务与备份恢复

终止事务创建持久任务，按 collection/步骤以有界批次（初始 500 条）执行幂等清理；步骤完成事实和重试可跨进程重启恢复。大批历史数据不放入一个长 Mongo 事务。逻辑终止与 cleanup 状态分离，任务失败不恢复账号、不释放未确认安全的跨服务屏障。

对邮箱归属、设备占用墓碑和学生共享组使用专门事务与唯一约束，不做无归属条件的批量删除。清理始终使用原 authId，不能按已释放且可能被新账号使用的邮箱或学号散列删除数据。

保留独立于旧业务备份的最小终止清单（authId、最终 accountRevision、terminatedAt、operationId），与墓碑同等保护并持续备份。Auth 终止事务写持久待投递记录，以 operationId 幂等写入不会随业务备份回滚的清单；收到持久化确认前只展示 TERMINATION_PENDING，本地 CLOSED 不可取消或回滚，投递故障必须告警并重试。恢复历史备份后先隔离服务，重放此清单、重新执行清理并核验，再接流量，防止旧备份复活账号。清单不可用、可能不完整或未能核验最新终止事实时保持停服，不直接以旧备份接流量。清单同步和恢复演练是上线门禁；未完成前不能承诺已终止账号不会因灾备回滚复活。

清理不删除 App 的历史应用/审核事实。App 还需清理该账号的 Tester membership、个人过滤偏好等个人状态，并确认终局 sealed；其幂等清理及有界完成回执属于 App 新 UC 的交付范围。其它平台资源服务若另存用户数据，必须进入数据清单和清理协调验收，不能以 Auth 数据已清理宣称全平台清理完成。

<a id="br-acc-014"></a>
### BR-ACC-014：结果、审计与第三方边界

终止状态、最小审计、清理任务和归属协议 COMMITTED 决定同一事务提交。审计只记录 operationId、subjectAuthId、认证方式/凭据引用、policyVersion、终止时间及版本；认证来源为 DEVICE_PROOF，不伪造有效 Session 操作，不记录退出自由文本理由或完整签名。

TERMINATION_PENDING 已终止本地账号、正在确认独立终止清单，仍不可恢复；TERMINATED 表示终止清单亦已确认，账号不可再登录；CLEANUP_COMPLETE 只在 Auth 活动数据清理、App 个人状态清理和必须的其他平台服务回执都完成后返回，同时列明永久保留项及备份到期边界。收据丢失后不能通过原邮箱、旧 Session 或匿名 authId 查询终止详情；必要的用户支持由独立核验流程处理。

已有 App audience/委托短期 JWS 仍存在 UC022 定义的离线有效期窗口，第三方自建登录态或已导出的数据不能被本用例删除。客户端应在确认终止后删除本地 Session 和设备私钥；失败或结果不确定时先保留收据查询，不能通过本地删除声称服务端已经注销。

## 首版运行与协议固定值

policyVersion 精确为 `account-closure-v1`。注销秘密摘要输入为 `Frame(UTF8("iwut-closure-confirmation-v1"), token32)` 或 `Frame(UTF8("iwut-closure-receipt-v1"), token32)` 后 SHA-256，禁止混用域。公开设备证明向量由 tools/auth_account_closure_vectors.py 生成并校验，随实现提交。

独立终止清单首版使用 `AUTH_TERMINATION_LEDGER_DIR` 指定的独立持久目录，禁止位于业务临时目录或包含在业务数据库回滚流程中。每 operationId 一个规范 JSON 记录，原子创建、文件与目录 fsync 后才确认；重复完全相同内容幂等，不匹配或损坏失败关闭。进程启动与显式 `auth-center reconcile-account-closures` 停服命令都须读取/核验清单，重放更高终止版本并调度清理，禁止将 CLOSED 恢复 ACTIVE。目录和恢复流程由运维独立备份，代码不能证明外部备份策略已经执行。

`AUTH_CLOSURE_DATA_POLICY_READY` 默认 false，是运维确认清理服务清单、备份/日志 30 天上限、终止清单隔离及无密钥人工受理均已具备的声明；启用公网注销要求 true。测试以隔离目录和真实服务验证，不修改真实部署声明。清理后台任务每批 500，周期初始 1 秒、失败指数退避至 60 秒，参数可配置但有正值/容量边界。当前实际平台个人存储为 Auth 与 App；以后增加资源服务须先加入清单与回执再启用，不允许空壳依赖假装全平台完成。

## 错误、限额与验收

Begin 不披露账号状态；Prepare 对未知目标、签名无效、凭据撤销或版本变化统一 `ACCOUNT_CLOSURE_PROOF_INVALID`（401）。已证明本人后才能返回正常 BLOCKED 明细。非法输入 400；未知/不匹配令牌或 operation 统一 401；过期/版本或终局冲突 409；依赖/存储/未知提交 503；限流 429。数据损坏不能伪装为无归属或已清理。

入口默认关闭 `AUTH_ACCOUNT_CLOSURE_ENABLED`，依赖用户认证基础、App provider 和清理工作器配置；特殊 DISABLED 注销不绕过功能门禁。Begin 复用设备认证的有界 IP/locator 容量，证明后采用有界账号桶，初始写每分钟 10、收据读取每分钟 30；读写令牌摘要、签名和任何秘密不进入日志。

验收至少覆盖：ACTIVE/DISABLED 设备证明；无 Session、无邮箱普通用户；未知/撤销密钥与旧 LOGIN 签名；预览后权限/Developer/账号/凭据变化；SUSPENDED 无应用可终止而有应用阻止；最后管理员与并发交接；旧 JWS、token、邮箱 challenge/result 不复活；清理中断/重启/重复执行；邮箱释放后新注册不被旧任务删除；共享关联组并发注册；永久 handle/密钥占用；App 回执丢失；收据只读隔离；备份恢复重放终止清单。使用真实 Mongo 与双服务集成，不能只验证账号字段变成 CLOSED。

## 实现依赖与联动

硬依赖 UC021/022、UC023/024 的生命周期版本和取消规则、App 归属屏障/个人数据清理；上述尚未交付。还需全平台数据清单、备份/日志保留能力、终止清单恢复演练和禁用账号无密钥的人工受理流程。

实施时同步 UC002 的 CLOSED 主体查询及 App 历史审核处理、UC006–019/020–024 的 CLOSED 拒绝、UC013 handle 终止占用、UC015 pairwise 映射删除例外、所有审计保留规则、客户端引导、共享注销签名字节/公开向量及可执行 API。共享归属契约另与 App agent 对齐；不添加旧数据库迁移。本轮生成实施 brief 并交付后端；公网启用仍受恢复受理、数据清单和部署验收门禁约束。

## 变更记录

- 2026-10-05：提出本人不可恢复注销；独立设备证明、禁用账号专用途径、应用归属门禁、CLOSED 与异步清理、最小永久保留及备份恢复防复活。

- 2026-10-05：按用户决定接受，生成 brief 并启动独立工作包；依赖顺序与生产启用门禁继续有效，不把设计接受记为实现完成。
