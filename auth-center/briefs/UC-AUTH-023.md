<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-023 --spec tools/brief-specs/UC-AUTH-023.json -->
# Brief — UC-AUTH-023：暂停与恢复 Developer 资格

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-023` 暂停与恢复 Developer 资格 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-DEV-013`–`BR-DEV-017`（5 条） |
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

管理员暂停或恢复指定 authId 的 Developer 资格，保留普通账号使用能力、developerHandle 和应用归属。暂停限制开发者行为，不等同于禁用账号、注销、应用下架、撤销 reviewer 权限或撤销所有应用用户的 OAuth 授权。

本用例只支持 APPROVED 与 SUSPENDED 之间的转换，不批准 PENDING、不恢复 REJECTED，不重新开通 UC024 的 WITHDRAWN。没有定时自动恢复。

### 参与者与 API

操作人使用 Gateway SESSION 换取面向 Auth 的 USER JWS，必须是当前 ACTIVE、账号版本匹配且具备 UC021 完整管理员集合和 `auth.developer.manage` 的 USER。目标可以是 ACTIVE 或 DISABLED USER；改变其 Developer 资格不会改变账号状态。

```text
ManageDeveloperStatus {
  subjectAuthId: AuthId
  action: SUSPEND | RESTORE
  expectedDeveloperRevision: Int64  // 必填，正数
  reason: String                    // trim 后 1..1024 UTF-8 bytes
}
GetManagedDeveloperStatus { subjectAuthId: AuthId }
ManagedDeveloperStatus {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED | WITHDRAWN
  developerRevision: Int64
  statusChangedAt: Instant?
}
```

独立 package `auth_center.v1.developer_management`，service `DeveloperManagementService`：

| 方法 | Auth HTTP 路径 | 结果 |
| --- | --- | --- |
| ManageDeveloperStatus | POST /v1/developers:manage-status | 200，ManagedDeveloperStatus |
| GetManagedDeveloperStatus | POST /v1/developers:get-managed-status | 200，ManagedDeveloperStatus |

HTTP 与原生 gRPC 同时交付，Gateway 外部前缀 `/auth-center`，精确登记方法；只接受 trusted USER JWS，不以 service/OAuth token 或直接 Session 替代。ProtoJSON、optional revision、UTC Timestamp、16 KiB 上限、无 query、拒绝未知/重复字段；no-store。查询不返回邮箱、学生关联、审核理由或应用清单。

### 主流程

1. 验证输入与操作人身份，在 Auth 全局认证事务协调边界内在线复核其当前管理资格。
2. 读取目标合法 Developer 状态及 developerRevision，校验 expectedDeveloperRevision。
3. SUSPEND 要求 APPROVED；RESTORE 要求 SUSPENDED。恢复还需当前激活邮箱和 UC013 的邮箱恢复部署就绪条件。
4. 若存在未提交的 Developer 退出/账号注销操作，按 BR-DEV-015 处理，不能与终止资格竞争提交。
5. 原子更新状态、developerRevision、归因/时间并追加独立生命周期审计，确认提交后返回。

### 错误与运行约束

身份失效为 401/UNAUTHENTICATED，缺当前管理资格为 403/PERMISSION_DENIED；不存在、SYSTEM、非 Developer 或已注销目标统一 `DEVELOPER_SUBJECT_UNAVAILABLE`（404/NOT_FOUND）。输入非法为 400/INVALID_ARGUMENT；revision/重复或非法状态转换为 `DEVELOPER_STATUS_CONFLICT`（409/ABORTED）；恢复邮箱门禁为 `DEVELOPER_RESTORE_BLOCKED`（409/FAILED_PRECONDITION）；版本耗尽拒绝。损坏数据、依赖故障或未知提交为 503/UNAVAILABLE，限流为 429/RESOURCE_EXHAUSTED。

独立 `AUTH_DEVELOPER_MANAGEMENT_ENDPOINTS_ENABLED` 默认 false，开启要求用户入口启用。按已认证 actor 的有界读/写桶默认每分钟 60/10，可部署调节；失败日志不含 JWS 或邮箱。

### 验收与依赖

- 同一用户的普通登录、资料和独立审核/管理权限在 Developer 暂停后仍可用；DISABLED 账号即使恢复 Developer 也不能登录。
- 版本冲突、重复转换、无邮箱恢复、PENDING/REJECTED/WITHDRAWN 非法恢复、数据损坏均不改变状态。
- 暂停与退出/注销确认竞争只有一个合法先后；取消决定持久化后 App 故障可重试，不永久阻塞治理。
- 真实 App 消费新的身份及 UC002 状态，验证暂停窗口与恢复；OAuth 不误撤销其他用户 grant，也不复活已有撤销 token。
- 使用真实 Mongo、签名、生产 HTTP/gRPC、并发和未知提交测试。

硬依赖 UC021 管理权限及 UC022 的 Auth 身份账号版本复核，两者尚未实现。UC024/025 未启用时无需提前存在退出操作，但启用它们前必须接入取消协调。实施时同步 UC013 的 developerRevision 初始化、UC002/UC010 状态消费说明、存储校验、API/路由和 brief；WITHDRAWN 的完整扩展由 UC024 负责。

## 业务规则（UC-AUTH-023 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-013 -->
### BR-DEV-013：独立资格与单调版本

普通 USER 的 developerRevision 初始为 0，首次 UC013 开通时变为 1；已有非 null Developer 状态必须有正 int64 revision。后续暂停、恢复和 UC024 退出每次成功严格递增，版本耗尽拒绝。不是 permissionRevision、accountRevision 或 developerHandle 版本。

SUSPEND/RESTORE 是显式状态转换，重复操作和过期 revision 均冲突，不产生重复事件。恢复要求已有激活邮箱及恢复能力就绪，暂停不依赖邮件配置。null 不是待批准 Developer；PENDING、REJECTED、WITHDRAWN 不通过此入口转为 APPROVED。首版无历史数据补齐迁移。

<!-- 权威位置: use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-014 -->
### BR-DEV-014：保留普通功能与传播边界

不递增 accountRevision，不撤销 Session、邮箱或设备密钥，不改变普通用户的资料、作为应用用户的历史 grant 或独立 reviewer/管理员权限。管理员即使暂停自身 Developer 资格也仍可管理平台，权限由对应 UC 判断。

新的 UC010 App audience 身份携带当前 Developer 状态；Auth OAuth 所有者检查读到 SUSPENDED 时拒绝该所有者应用的相关签发/使用。普通用户功能不要求 Developer APPROVED。

App 只允许 APPROVED 的开发写入口在新身份下拒绝；已有离线验签的短期 Developer JWS 存在原 TTL/leeway 窗口，暂停不提供跨库即时撤销。已有 UC002 当前状态检查仍按其消费用例生效，但不能宣称所有 App 方法已经在线查询。实施时必须列出并验收受影响入口。

暂停不清空 TEST/GREY/STABLE、不撤销审核结论、不隐藏 Catalog，也不删除应用 URL。若需立即停止应用服务，应另行执行 App 应用治理；不得让 Auth 直接修改 App 数据库。

<!-- 权威位置: use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-015 -->
### BR-DEV-015：暂停优先与退出竞争

与 UC024/025 共享 Auth 认证事务栅栏。暂停先提交时，未完成的 Developer 退出操作被原子标为 CANCELLED，交由共享归属屏障协议解除本次临时屏障；不得阻止管理员因网络挂起的退出请求执行暂停。退出先提交为 WITHDRAWN 时，暂停请求冲突，不把已退出者改成 SUSPENDED。

若本账号已有未提交的注销准备，任何 Developer 状态变化都令该准备失效并取消，用户需重新取得注销预览及确认。注销先提交后目标已终止，本用例拒绝。恢复与账号禁用可分别提交，但恢复 Developer 不恢复 DISABLED 账号。

外部屏障解除不能在 Auth 事务中调用 App；先持久化取消决定，再按 [归属退出协调草案](../../platform/contracts/account-owner-exit-v1.md) 重试通知。App 故障可延迟解除临时限制，不能回滚已完成暂停。

<!-- 权威位置: use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-016 -->
### BR-DEV-016：OAuth 恢复及 handle 连续性

developerHandle 及其永久唯一占用不变化。原应用归属、审核历史和发布事实保留；恢复不创建新的 Developer 身份或释放配额。

暂停本身不推进其他用户 grant/client epoch，也不逐条撤销其 token family。所有者恢复后，仍未过期、未撤销并满足当前全部条件的凭据可以再次使用；到期、重放撤销、用户撤回和账号禁用引起的失效不能恢复。永久停止应用凭据必须使用单独的应用/client 治理行为。

<!-- 权威位置: use-cases/UC-AUTH-023-suspend-and-restore-developer.md#br-dev-017 -->
### BR-DEV-017：审计与并发一致性

新建 append-only `auth_developer_lifecycle_audit_events`，记录 eventId、actorType=USER、actorAuthId、subjectAuthId、action、reason、before/after 状态及 revision、occurredAt；UC024 复用该生命周期审计。eventId 唯一，按 subjectAuthId/occurredAt/eventId 查询，不复用 UC013 一次性 ACTIVATE/CLAIM 审计唯一约束，不改写历史开通记录。

状态、版本、取消决定和审计同一事务提交；与 UC010/019 签发和 OAuth 所有者读取协调。提交前重查当前权限，审计失败回滚，未知提交返回不可用。客户端通过查询确认结果，不能以旧版本覆盖新决定。

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

另由 Auth 向获授权 App 提供 `GetAccountOwnerExitDecision(authId, operationId)`，返回 `PENDING | COMMITTED | CANCELLED`；未知操作返回 NOT_FOUND，不能解释为已取消。Auth 保存的 receipt/purpose 和归属目标必须与 App 一致。消息中的 authId 只是被治理对象，不是伪造的终端操作人身份。

#### App 原子屏障

App 的 Prepare 在同一账号归属事务栅栏下检查义务并安装屏障。所有创建应用、转入所有权、撤销转出、恢复已关闭应用以及将来可能增加归属义务的写操作必须参与同一栅栏；包括持有旧 APPROVED JWS 的请求。不能只在 HTTP handler 做预检查。

存在义务时返回 BLOCKED，不安装屏障，不自动转让、关闭或删除应用；用户处理后用新操作重试。零义务时返回 PREPARED，保存不可变 `(authId, operationId, purpose, receiptId)`，阻止该账号新增归属，直到收到终局决定。重复相同请求返回同一结果；同 operationId 换 authId/purpose 或不匹配 receipt 拒绝。

COMMITTED 将本次屏障变为永久 sealed，不允许未来凭旧 JWS 创建或转入应用。首版 Developer 退出不支持重新开通，因此无需解封接口。已因 Developer 退出 sealed 的账号之后申请注销时，仍重新核验无义务，为注销 operation 生成独立 receipt；取消注销不会解除之前的永久 sealed 状态。

CANCELLED 仅解除该 operation 创建的临时屏障，不能解除其他操作或既有永久 sealed。即使 Prepare 尚未到达，Finish(CANCELLED) 也保存该 operation 的终局记录，拒绝后来延迟到达的 Prepare；不能出现“先取消，再被迟到的准备永久锁住”。一个 authId 同时最多一个未决归属退出操作。

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

- `UC-AUTH-023`（use-cases/UC-AUTH-023-suspend-and-restore-developer.md）：变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-023-suspend-and-restore-developer.md` | 112 | `bff16548144e` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `3d5371d4e48b` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
