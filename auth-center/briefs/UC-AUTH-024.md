<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-024 --spec tools/brief-specs/UC-AUTH-024.json -->
# Brief — UC-AUTH-024：本人退出 Developer 资格

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-024` 本人退出 Developer 资格 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-DEV-018`–`BR-DEV-022`（5 条） |
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

用户主动终止自己的 Developer 资格，先处理所有名下应用及未决归属义务，再进入 WITHDRAWN。保留普通账号、Session、邮箱、用户资料和 developerHandle 的永久占用。

首版退出后不支持重新开通，不把 WITHDRAWN 当作 null 或 SUSPENDED。后续若需要重新开通，须新设计审核/门禁及 App 屏障解除协议，且只能沿用原 handle；当前 UC013 和 UC023 都不能重新激活。客户端在确认前必须明确展示此结果。

### 参与者与接口

只有当前有效 Session 对应的 ACTIVE USER 可以操作本人，不接收 subjectAuthId。要求 developerStatus=APPROVED、有合法永久 handle 占用，并使用 UC023 的 developerRevision；无需管理员同意或额外绑定邮箱。SUSPENDED、PENDING、REJECTED 不走自助退出，避免将治理状态转换成可以重新申请的空状态。

独立 package `auth_center.v1.developer_withdrawal`，service `DeveloperWithdrawalService`。四个方法均为直接有效 Session 鉴权，Gateway DIRECT 精确转发（不代表匿名），不先换 USER JWS；HTTP/原生 gRPC 同时交付：

| 方法 | HTTP POST 路径 | 输入/结果 |
| --- | --- | --- |
| PrepareDeveloperWithdrawal | /v1/users/me/developer-withdrawal:prepare | requestId(UUIDv4)、expectedDeveloperRevision → operation |
| ConfirmDeveloperWithdrawal | /v1/users/me/developer-withdrawal:confirm | operationId、confirmation=WITHDRAW_DEVELOPER → operation |
| CancelDeveloperWithdrawal | /v1/users/me/developer-withdrawal:cancel | operationId → operation |
| GetDeveloperWithdrawal | /v1/users/me/developer-withdrawal:get | operationId → operation |

operation 仅返回本人的 operationId、state=`PREPARING | READY | BLOCKED | COMPLETED | CANCELLED`、expiresAt、developerStatus/revision、blocker 和 completedAt；不返回 App receipt、其他应用所有者或邮箱。BLOCKED 原因可为 OWNED_APPLICATIONS/PENDING_OWNERSHIP_CHANGE；客户端引导到 App 处理，不由 Auth 代办转让。

请求采用严格 ProtoJSON、UTC Timestamp、16 KiB 上限、无 query/未知重复字段；Session 唯一载体沿用设备协议。读写都复核 Session/accountRevision，不增加新登录方法。只读查询不 touch lastUsedAt；成功变更按既有有效 Session 操作规则处理。

### 主流程

1. Prepare 在 Auth 事务中复核资格、目标版本，保存本人 PENDING 操作、当前 Session ID、accountRevision、developerRevision 和固定 10 分钟期限；不先修改 Developer 状态。
2. 调用 [App 归属退出协调](../../platform/contracts/account-owner-exit-v1.md) 的 Prepare。存在名下应用或未决归属时返回 BLOCKED；零义务并建立屏障后为 READY。当前 session/版本条件变化则取消，不能把新状态重新绑定到旧操作。
3. 客户端展示资格退出、handle 保留和首版不可重新开通，由用户明确 Confirm；确认不是 Prepare 的隐式后续。
4. 同一 Auth 事务重新确认原 Session 仍有效、账号/Developer 版本未变、APPROVED、receipt 匹配且未过期，设置 WITHDRAWN、增加 developerRevision、写生命周期审计和 COMMITTED 决定。
5. 持久通知 App 将屏障 sealed；通知失败重试，不把已退出的资格恢复。返回 COMPLETED 后普通用户功能继续可用。

### 错误与验收

Session 无效为 401；请求非法为 400；operation 不属于本人为统一 404；版本/状态冲突或过期确认为 409；依赖/存储/未知提交为 503；限流为 429。Prepare 的应用义务为正常 BLOCKED 结果，不以 500 表示。默认关闭 `AUTH_DEVELOPER_WITHDRAWAL_ENABLED`，开启要求用户入口及 App provider 配置齐备；有界账号读/写桶默认每分钟 60/10。

必须测试：草稿/未发布/已发布均阻止；并发创建、转入与退出；旧 JWS；Prepare 后取消/过期/暂停/禁用；提交丢响应和 App 不可用；永久 handle 占用；新 Apply/管理 RESTORE 拒绝 WITHDRAWN；普通登录与独立权限保留；已退出后再注销并取消不解除既有 sealed。覆盖真实双服务、Mongo 事务与 HTTP/gRPC。

### 实现依赖与联动

依赖 UC021–023 的治理、账号/资格版本和取消边界；App 归属屏障由已交付的 UC-APP-025 满足。实施时扩展 UC002、UC013、UC010、JWS/内部状态 Proto 和所有 App 状态消费者，明确 App 归属处置与历史审核政策；同步 brief。首版不增加重新申请、资格审批或旧数据迁移。本 UC 已 ACCEPTED，设计接受不等于依赖已实现。

## 业务规则（UC-AUTH-024 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-018 -->
### BR-DEV-018：明确本人退出与稳定身份

只修改当前 authId 的 Developer 资格。保留 handle 原归属、claimedAt、原始开通事实和历史应用/审核引用；不释放名称、不重置配额或创建第二身份。不改 accountRevision、permissionRevision，不回收本人 Session、独立 reviewer/管理员权限或作为应用用户的 grant。

转换固定为 APPROVED→WITHDRAWN，版本只递增一次；同 operationId 的已确认操作重复 Confirm 返回原完成结果，不能生成第二事件。对 WITHDRAWN 新建退出操作返回 ALREADY_WITHDRAWN，不重走 App 或增加版本。

<!-- 权威位置: use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-019 -->
### BR-DEV-019：先处置应用再退出

App 是当前应用归属义务的唯一权威。所有名下 Application 均计入，包括未发布草稿；没有公开发布不等于没有义务。先通过 App 正式用例转出或关闭，Auth 不帮用户删除 App 数据，也不将应用自动移交平台。

共享协议的 PREPARED 屏障是提交前置条件；普通读 API、缓存名单或用户声明不可替代。即使旧 APPROVED JWS 尚未过期，并发创建/转入也不能在 READY 之后成功，COMPLETED 后永久拒绝新增归属。

App 当前缺少完整转让/关闭及该屏障能力。其交付前入口保持关闭；仅向无应用用户开放也仍需屏障，不能以“没有查询到”提前完成。

<!-- 权威位置: use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-020 -->
### BR-DEV-020：可取消准备与不可逆提交

Prepare/READY 不改变资格，但 App 可暂时阻止增加归属。用户可在提交前 Cancel；过期、账号版本变化、Session 失效或管理员暂停导致 Auth 终局 CANCELLED，按共享协议解除本次临时屏障。UC023 暂停可以取消退出，退出不得占锁阻止治理。

一个 authId 最多一个未决生命周期退出操作，UC025 注销准备不能并行另开。requestId 在 24 小时内按 `(authId, requestId)` 去重；相同请求返回已有 operation，不延长期限，同键不同 revision 冲突。已取消/阻塞结果不复活，重新尝试使用新 requestId。BLOCKED 是对本次失败准备的展示状态，对协调协议保存终局 CANCELLED；释放未决操作占用并发送必要的取消通知，不让用户无谓等待 10 分钟。

COMPLETED 不可 Cancel，也不因 App 回执丢失恢复 APPROVED。未知提交先读取终局，不能推测取消。操作决定及重试任务持久化，跨服务故障处理严格引用共享协议。

<!-- 权威位置: use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-021 -->
### BR-DEV-021：状态消费与历史审核

WITHDRAWN 是 Developer 生命周期终态，不是违规暂停。UC002 返回这一明确状态；UC010 可携带 WITHDRAWN，所有 APPROVED-only 开发入口及 Auth OAuth owner 检查均拒绝其行使开发者资格。不得将未知枚举默认为 APPROVED、null 或 SUSPENDED。

App 对历史 submitter、creator 或 reviewer 的处理不能只使用“不是 SUSPENDED 就允许”：WITHDRAWN/已终止账号在具体审核批准门禁中的含义必须由 App 同步明确。退出不撤销已作出的审核决定，不抹去审计归因；作为 reviewer 的权限仍由 UC004 独立控制。当前管理员必须具备有效资格，历史提交者是否阻止新决定由 App 用例逐项固定，未对齐前不可启用退出。

<!-- 权威位置: use-cases/UC-AUTH-024-withdraw-developer.md#br-dev-022 -->
### BR-DEV-022：原子性、查询与审计

复用 UC023 生命周期审计，operation=WITHDRAW、actorAuthId=subjectAuthId，记录 before/after 状态及版本和 operationId，不强制用户填写退出理由。资格、审计、协调终局及通知任务同一 Auth 事务提交，与申请、暂停、恢复、账号禁用/注销和身份签发共用认证栅栏。

属于其他账号或不存在的 operation 统一不可用；只对本人披露 blocker。普通数据损坏、App 故障或状态未知均返回不可用/处理中，不伪装为“名下没有应用”。App 未收终局回执前，不清理所需操作决定。

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

- `UC-AUTH-024`（use-cases/UC-AUTH-024-withdraw-developer.md）：变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-024-withdraw-developer.md` | 91 | `fd28fc8a43cb` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `70d736bfa904` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
