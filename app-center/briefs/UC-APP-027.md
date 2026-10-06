<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-027 --spec tools/brief-specs/UC-APP-027.json -->
# Brief — UC-APP-027：关闭 Application

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-027` 关闭 Application |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-020`–`BR-APP-028`（9 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/account-owner-exit-v1.md`、`platform/contracts/application-close-reauth-proof-v1.md`、`platform/contracts/application-closure-v1.md`、`platform/contracts/auth-developer-status-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

> 当前管理员经过近期重新认证和明确确认后，把一个 Application 不可逆地从 `ACTIVE` 推进到 `CLOSING`；App Center 立即停止它的全部本地运行与管理能力，并通过持久协议让 Auth Center 建立永久授权撤销栅栏，最后收敛为 `CLOSED`。

本用例负责：

- 建立 `ACTIVE → CLOSING → CLOSED` 的 Application 生命周期；`CLOSING` 起不可取消、不可恢复。
- 在一个 App Center 本地事务内停止目录、运行解析、Tester 加入和 OAuth client 使用，释放管理员配额与账号归属义务。
- 终止待处理管理员转让，保留 Version、Profile、Review、Publication、Filter、Tester Membership 和审计记录。
- 通过可重试、幂等的 App→Auth 协议永久撤销该 Application 的 grant、authorization code、access token、refresh token family 和后续授权能力。
- 在 Auth 已持久应用关闭事实后，把 Application 从 `CLOSING` 收敛为 `CLOSED`。

本用例不负责：

- 可恢复的归档、临时停用、平台紧急 suspension 或恢复 Application。
- 物理删除 Application、历史版本、资料、审核、发布、Tester、OAuth registration、grant 或审计记录。
- 平台人员强制关闭、争议处理、批量关闭或账号关闭时自动代替管理员关闭 Application。
- 撤销第三方应用已经建立且不再访问 iWUT 平台的本地会话或其自行保存的数据。
- 释放 Application ID 或技术名称供其他 Application 复用。

归档是可恢复的整理动作，仍保留当前 owner 义务；关闭是不可逆终态，可以解除 owner 义务。两者不能共用一个布尔字段或一条命令。

### 参与者与前置依赖

- **当前管理员**：必须等于 `Application.adminId`，可信身份当前显示 accountStatus=`ACTIVE`、developerStatus=`APPROVED`。
- **Auth Center**：签发绑定本次高风险操作的近期重新认证证明，并依据 [Application Closure v1](../../platform/contracts/application-closure-v1.md) 保存永久 Application 授权撤销事实。
- **App Center**：拥有 Application 生命周期、当前管理员、配额、Publication、Tester、OAuth registration 和关闭过程。

两个接受依赖已经闭合：[UC-AUTH-026](../../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md) 定位 application closure tombstone 在授权、换码、token、refresh、UserInfo 与在线委托最终边界的检查；[Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md) 固定当前 Session 所属同一登记设备的新 challenge/signature 与 proof 格式。普通 App USER JWS 的 `iat` 仍只表示身份上下文签发时间，不能单独满足本用例。

### 输入、预览与身份

关闭前先读取：

```text
ApplicationClosurePreview {
  applicationId
  ownershipRevision
  lifecycleRevision
  lifecycleStatus: ACTIVE | CLOSING | CLOSED
  hasPendingAdminTransfer
  activePublicationChannelCount
  enabledOAuthClientCount
  activeTesterCount
  pendingReviewCount
}
```

预览用于让管理员看到影响范围和取得 OCC revision，不返回 Version 内容、Tester 身份、secret、credential 摘要或内部任务状态。

关闭命令：

```text
CloseApplicationCommand {
  applicationId: ApplicationId
  expectedOwnershipRevision: int64
  expectedLifecycleRevision: int64
  confirmation: "CLOSE_APPLICATION"
}
```

近期重新认证证明依据 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md)，通过专用 metadata/header `x-iwut-high-risk-proof` 传递，不放进 URL、命令正文、日志或审计 payload。证明至少绑定：

```text
iss, aud="iwut-app-center", sub=authId,
purpose="app.close", applicationId,
jti, auth_time, iat, nbf, exp
```

Auth 只在当前 Session 所属同一登记设备完成一次新的 challenge/signature 后签发；证明最大寿命和允许的 `auth_time` 年龄均为 5 分钟。App 验证签名、issuer、audience、typ/token_type、purpose、subject、applicationId 和时间，并把 jti 唯一绑定到首次创建的 ApplicationClosure。相同 jti 对同一关闭结果的网络重试返回既有资源；把它用于其他 Application、其他操作或不同 closure 则作为重放拒绝。失败、过期、跨 Application、跨用户或只提供普通 USER JWS 都不能关闭。

### 生命周期与可见行为

```text
ACTIVE ── START CLOSURE ──► CLOSING ── AUTH APPLIED ──► CLOSED
                                  │
                                  └── retry forever; no cancel/reopen
```

- `ACTIVE`：现有行为不变。
- `CLOSING`：不可逆关闭已经提交；所有运行、目录、OAuth 和管理路径按已关闭处理，后台继续收敛 Auth 撤销。
- `CLOSED`：Auth 永久撤销事实已有持久回执，关闭过程完成；仍只保留审计读取。

进入 `CLOSING` 是用户可见的关闭生效点。App Center 的 Catalog、统一启动目标、TEST descriptor、Tester 加入、管理员写入、审核决定以及 OAuth provider 查询都必须在最终读取/事务边界要求 Application=`ACTIVE`。因此 Auth 暂时不可用只延迟 `CLOSED` 回执，不让应用继续运行。

`CLOSING` 没有超时、取消或自动回滚。运维可以观察和重试收敛任务，但不能把它改回 `ACTIVE`。

### 发起关闭流程

1. 校验 applicationId、两个正 revision 和逐字匹配的 confirmation。
2. 验证普通可信用户身份、近期重新认证证明及其 jti 绑定；调用 Auth 的非缓存批量状态查询，确认当前管理员仍为 ACTIVE＋APPROVED。Auth 不可用、缺项或响应损坏时失败关闭。已经绑定同一 ApplicationClosure 的 jti 可以直接返回既有结果，不重复资格查询或副作用。
3. 读取 Application 与影响摘要。若已经 CLOSING/CLOSED，只有命令证明 jti 已绑定该 ApplicationClosure 时才按 Close 的幂等重试返回既有资源；其他调用应使用 Get，不能用新的关闭命令枚举终态。
4. 开始本地事务。先按原始 authId 字节序取得当前管理员以及待处理转让目标（如有）的 `account_owner_exit_fences`，再取得 Application coordination fence。
5. 在事务内复查 adminId、ownershipRevision、lifecycleRevision、lifecycleStatus=`ACTIVE`、证明绑定和 jti 尚未绑定其他操作。任何漂移都拒绝整个命令。
6. 从 App Clock 取得一个 `closingStartedAt`，创建 ApplicationClosure 和持久收敛任务，并原子执行“本地关闭事务”中的全部变化。
7. 提交成功返回 `CLOSING`。后台在事务外调用 Auth；只有取得匹配的 APPLIED 回执后，才在 App 事务中保存回执并把生命周期推进为 CLOSED。

新鲜 Auth 状态查询与本地提交之间仍存在与 UC026 一致的有界跨服务窗口；本地 ownership/lifecycle OCC 和账号退出 fence 负责 App 内线性化，不能把 Auth 查询描述成跨服务原子锁。

### 本地关闭事务

进入 CLOSING 的事务必须全部成功或全部回滚：

1. `Application.lifecycleStatus = CLOSING`，`lifecycleRevision + 1`；adminId 作为历史当前管理员保留，ownershipRevision 不变。
2. 当前管理员的 `DeveloperApplicationQuota.usedCount - 1`，只执行一次。缺失配额、usedCount=0 或绑定漂移属于内部数据不变量异常。
3. 若存在 PENDING ApplicationAdminTransfer，把它改为 CANCELLED，`resolutionCause=APPLICATION_CLOSURE`、`resolvedBy=adminId`、`resolvedAt=closingStartedAt`。不创建新申请，不改变历史终态。
4. 若存在 ACTIVE TesterJoinLink，把它改为 REVOKED，`revocationReason=APPLICATION_CLOSURE`、`revokedBy=adminId`、`revokedAt=closingStartedAt`、`replacedByJoinLinkId=null`。已有 Tester Membership 原样保留作审计，不做最多 100 条的批量终态改写。
5. 遍历 TEST、GREY、STABLE registration 的已存在 client slot：ACTIVE 改为 DISABLED，并增加该 slot 的 authorizationEpoch；一个 registration 中至少一个 slot真实变化时，registrationRevision 只增加一次。已经 DISABLED 的 slot不变。不轮换或删除 confidential secret。
6. 创建唯一 ApplicationClosure、消费高风险证明 jti，并写入 durable outbox/task。

Version、ProfileRevision、Review、Publication、PublicationHistory、Filter 和 Tester Membership 均不改写。SUBMITTED/PENDING 审核保留原状态与证据，但 reviewer queue 必须排除非 ACTIVE Application，决定命令也必须失败。Publication 指针保留历史形状，不过运行解析因 Application 生命周期 gate 返回不可运行。

### Auth 持久撤销与最终收敛

App 不在数据库事务内调用 Auth。事务提交后，durable worker 根据 [Application Closure v1](../../platform/contracts/application-closure-v1.md) 调用 `ApplyApplicationClosure(applicationId, closureId, closingStartedAt)`：

- 初始退避 1 秒，指数增长，最大 60 秒；单次 RPC deadline 5 秒。
- 相同 applicationId＋closureId 必须幂等返回同一 APPLIED receipt。
- 超时或响应丢失后先调用 Get；不能把未知结果当作失败并创建新 closureId。
- Auth 持久事实以 applicationId 唯一；同 applicationId 的不同 closureId 是冲突和运维告警。
- 进程重启、重复投递和长期依赖故障都不能丢失任务或改变 `CLOSING` 的本地封禁。

Auth 的 application closure tombstone 是永久授权栅栏。在相关 Auth UC 的最终事务边界中，它阻止或失效：

- 新建/扩大 consent grant；
- 签发或消费 authorization code；
- 签发 access token、ID token 和 refresh token；
- 使用既有 refresh token family；
- 在线 token introspection/delegation 对该 Application 返回可用。

Auth 可以保留 grant、token family、sector 与 pairwise sub 映射作审计；无需扫描并改写所有记录。tombstone 才是权威撤销事实，applicationId、sector 和既有 sub 不得复用。

App 收到匹配的 APPLIED receipt 后，在本地事务中锁定 Application coordination fence，复查 Application 和 closure 仍绑定且处于 CLOSING，保存 receiptId/appliedAt，把 Application 与 closure 置为 CLOSED，并增加 lifecycleRevision。重复回执不再增加 revision。

### 领域与数据模型

```text
Application {
  id
  name
  adminId
  ownershipRevision
  lifecycleStatus: ACTIVE | CLOSING | CLOSED
  lifecycleRevision
  createdAt
}

ApplicationClosure {
  closureId
  applicationId
  initiatedBy
  sourceOwnershipRevision
  sourceLifecycleRevision
  status: CLOSING | CLOSED
  highRiskProofJti
  closingStartedAt
  authRevocationState: PENDING | APPLIED
  authReceiptId?
  authAppliedAt?
  closedAt?
}
```

`application_closures` 至少具有 closureId 唯一索引、applicationId 唯一索引、`(authRevocationState, nextAttemptAt, closureId)` worker 索引和严格 validator。ApplicationClosure 不是可删除 job；任务元数据可以归档，关闭事实永久保留。

App migration 0022：

- 为既有 Application 回填 `lifecycleStatus=ACTIVE`、`lifecycleRevision=1`。
- 创建 `application_closures` 及 durable task/index/validator。
- 为 high-risk proof jti 建全局唯一绑定约束；同一关闭结果允许安全重试，其他用途拒绝重放。
- 把 ApplicationAdminTransfer CANCELLED 的 `resolutionCause` 扩展为 `EXPLICIT | APPLICATION_CLOSURE`。
- 把 TesterJoinLink `revocationReason` 扩展为 `ROTATED | MANUAL | ADMIN_TRANSFER | APPLICATION_CLOSURE`。

### API 草图

独立 package：`app_center.v1.application_closure`；service：`ApplicationClosureService`。

| RPC | HTTP | 语义 |
| --- | --- | --- |
| `GetApplicationClosurePreview` | `GET /v1/applications/{application_id}/closure-preview` | 当前管理员读取影响摘要和 revision |
| `CloseApplication` | `POST /v1/applications/{application_id}:close` | 提交不可逆关闭，成功返回 CLOSING |
| `GetApplicationClosure` | `GET /v1/applications/{application_id}/closure` | 发起时管理员读取收敛状态 |

Close 成功使用 HTTP 202；重复请求返回现有 CLOSING/CLOSED，不重复副作用。所有响应使用 `Cache-Control: no-store`。内部 task、重试次数和依赖错误正文不向用户暴露。

稳定错误映射：

- 参数、confirmation 非法：HTTP 400 / gRPC INVALID_ARGUMENT。
- USER 身份或 high-risk proof 缺失、无效、过期、跨操作重放：HTTP 401 / gRPC UNAUTHENTICATED；同一 jti 对已绑定关闭的重试返回既有结果。
- 非当前管理员、账号或 Developer 不合格：HTTP 403 / gRPC PERMISSION_DENIED。
- Application 不存在或调用者不可见：HTTP 404 / gRPC NOT_FOUND。
- expected revision 漂移、生命周期或并发状态冲突：HTTP 409 / gRPC ABORTED。
- 关闭前 Auth 新鲜资格检查不可用：HTTP 503 / gRPC UNAVAILABLE；已经 CLOSING 后的后台故障只保留 CLOSING。
- 持久事实损坏、配额下溢、closure/Application 绑定漂移：HTTP 500 / gRPC INTERNAL。

### 并发与验收场景

至少覆盖：

1. 关闭与 UC026 接受、取消、过期收敛的两个确定性胜序；不能出现转让完成后仍由旧 owner 关闭，也不能遗留 PENDING 转让。
2. 关闭与 owner-exit Prepare 的两个胜序，以及 BLOCKED 后关闭再重试。
3. 关闭与创建 Version/Profile、提交/决定审核、设置 TEST/GREY/STABLE、修改 Filter、Tester 加入/移除、创建/启停/轮换 OAuth client 的竞争；后提交者必须看见 lifecycle gate。
4. 关闭与同一 owner 创建新 Application、最后一个配额名额竞争；usedCount 不短暂重复、不丢失、不下溢。
5. 本地事务任一步失败时 Application、配额、转让、链接、OAuth slot、proof jti 和 task 全部回滚。
6. 多 channel、PUBLIC/CONFIDENTIAL 混合 ACTIVE/DISABLED 时 authorizationEpoch 与 registrationRevision 的精确变化。
7. CLOSING 提交后 Catalog、详情、统一解析、TEST descriptor 和 OAuth provider 立即失败；旧缓存不能继续服务。
8. Auth tombstone 前后既有 authorization code、access token、refresh token family、grant 扩大和在线 delegation 的行为。
9. Auth 长期不可用、Apply 成功但回包丢失、Get 丢失、双边重启和重复 worker；最终只有一个 receipt，并从 CLOSING 收敛 CLOSED。
10. high-risk proof 的重放、跨用户、跨 Application、错误 purpose/audience、过期、未来时间，以及只提交普通 USER JWS。
11. 待审核记录保留原状态但队列不可见、决定失败；Membership 和 Publication 历史无批量改写。
12. CLOSED 无恢复入口，ApplicationId 与原命名空间技术名称不能复用；管理读取不泄露 secret、token、Tester 身份或内部错误。

### 实现前决策结论

本提案已经确定：关闭不可逆；CLOSING 即释放配额和 owner 义务；技术名称首版不释放；不删除历史、不批量改写 Membership/Review；不轮换 secret；本地禁用与 Auth application tombstone 双层生效；只有 Auth 回执推进 CLOSED。

产品语义与跨服务依赖均已固定，可以生成 brief 并进入 App/API 后端实现。Auth/API 的 tombstone、OAuth 最终 gate 与 proof 签发是并行工作包；App 完整验收仍须使用真实 Auth 完成 Apply/Get 和 proof 消费联调，不能用永久 fake 替代。

## 业务规则（UC-APP-027 权威正文）

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-020 -->
### BR-APP-020：不可逆生命周期与稳定身份

Application lifecycle 只有 `ACTIVE → CLOSING → CLOSED`。CLOSING 和 CLOSED 都不能恢复、取消或被普通管理员改写。ApplicationId 永不复用；技术名称在原管理员既有 `(adminId, nameKey)` 命名空间内永久占用，首版不提供释放或跨 owner 的墓碑复用规则。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-021 -->
### BR-APP-021：关闭权限、明确确认与近期认证

只有当前 ACTIVE＋APPROVED 管理员可以关闭。请求必须同时携带 expectedOwnershipRevision、expectedLifecycleRevision、逐字确认和绑定 applicationId 的一次性近期重新认证证明。普通 USER JWS、旧 Session 活跃、前端二次弹窗或命令 confirmation 都不能代替 Auth 证明的新认证事件。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-022 -->
### BR-APP-022：CLOSING 即时本地隔离

CLOSING 是关闭生效点。所有目录、启动、Tester、审核、Publication、Filter、Version/Profile 管理和 OAuth provider 路径必须在最终边界要求 Application ACTIVE；缓存不能把旧 ACTIVE 结果延长到关闭事务之后。CLOSED 只表示跨服务撤销已经确认，不是首次停止服务的时刻。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-023 -->
### BR-APP-023：OAuth 本地禁用与 Auth 永久撤销

本地事务禁用所有现有 channel/client type slot，并按真实状态变化增加 authorizationEpoch 和 registrationRevision；不删除 clientId、不轮换 secret、不改写 grant/token。Auth tombstone 独立永久阻止该 applicationId 的授权与 token 使用。两个边界缺一不可：本地 gate 提供即时效果，Auth tombstone 覆盖已经签发的 Auth 状态。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-024 -->
### BR-APP-024：依附状态保留与待处理操作终止

关闭保留 Version、Profile、Review、Publication、Filter、Tester Membership、OAuth registration/credential 和全部历史。PENDING 管理员转让与 ACTIVE 加入链接在本地事务中终止；待审核记录不改写，但从队列排除且不能再决定。避免为每个依附模型伪造 CLOSED/CANCELLED 状态，也避免一次关闭产生无界批量写入。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-025 -->
### BR-APP-025：配额、名称与 owner 义务

进入不可逆 CLOSING 时立即且只一次释放当前管理员一个配额占用，并不再构成 OWNED_APPLICATIONS 义务；adminId 留作历史归因。关闭与 owner-exit Prepare 使用同一账号 fence：Prepare 先线性化时看见 ACTIVE Application 并返回 BLOCKED，关闭先线性化时 Prepare 可在其余义务为零时成功。BLOCKED 的 Auth 操作由用户在关闭后重试。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-026 -->
### BR-APP-026：持久收敛、幂等与未知结果

ApplicationClosure 和 durable task 必须与 CLOSING 同事务创建。App→Auth 调用在事务外至少一次投递，使用稳定 closureId；超时、断连、响应丢失和重启都通过 Get 与相同 Apply 收敛。CLOSING 不因任务年龄回滚，只有匹配的 Auth APPLIED receipt 能推进 CLOSED。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-027 -->
### BR-APP-027：共享写栅栏与竞态

关闭与创建/接受/取消管理员转让、账号归属退出、Version/Profile/Review/Publication/Filter/Tester/OAuth 写操作共用 Application coordination fence；涉及账号时先按 authId 原始字节序锁全部 account_owner_exit_fences，再锁 Application。所有写入口必须在最终事务内复查 lifecycleStatus=ACTIVE，不能只依赖 handler 预读。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-028 -->
### BR-APP-028：终态审计、隐私与错误边界

关闭永久保存 applicationId、closureId、发起者、源 ownership/lifecycle revision、开始/完成时间、证明 jti、Auth receipt 和状态；不保存证明原文、secret、token 或用户资料。公开读取仍按未找到处理，管理读取只向发起时管理员披露最小状态。数据不变量损坏返回 INTERNAL，不伪装成业务冲突。

## 架构决定（仅本次需要的章节）

### ADR-003：Go package 与依赖边界（`ACCEPTED`）

#### 决定

代码首先按业务能力组织，每项能力内部再分 Domain、UseCase 与 Port：

```text
internal/application/domain
internal/application/usecase
internal/application/port
internal/version/domain
internal/version/usecase
internal/version/port
internal/profile/domain
internal/profile/usecase
internal/profile/port
internal/publication/...
internal/tester/...
internal/catalog/...
```

跨能力稳定且确实共享的类型放入小型 `internal/shared` package。只有在至少两个已实现能力出现相同语义时才提升为共享类型，不提前建立通用工具箱。

基础设施放在能力之外：

```text
internal/adapter/mongo
internal/adapter/auth
internal/adapter/transport
cmd/app-center
```

主要依赖方向为：

```text
transport -> usecase -> domain
adapter -> capability port + required domain types
composition root -> concrete implementations
```

Domain 不依赖 Kratos、MongoDB driver、Proto 生成包、HTTP、配置或具体日志实现。UseCase 只依赖 Domain 与当前能力声明的 ports。Adapter 实现 ports，composition root 负责组装。

能力间协作通过显式应用服务、port 或只读 Query 接口完成。一个能力不得直接导入另一个能力的 MongoDB document 或未导出的聚合内部结构。

当前代码树只使用表达业务职责的目录名，不以迁移阶段或实现世代划分代码。

#### Port 所有权

Port 由使用它的能力拥有，而不是由提供方或某个全局 infrastructure package 拥有。例如 Application 创建用例需要的原子持久化接口位于 `internal/application/port`，MongoDB adapter 在外部实现它。

Port 方法使用业务语言并表达所需原子边界，不先建立 `Save/Get/Delete` 式通用 Repository。只有多个实际用例证明通用操作具有相同语义时才抽取。

#### 自动化约束

代码仓库根目录的 `architecture_test.go` 作为 ADR 的可执行护栏，并由 `go test ./...` 自动运行。它至少强制以下规则：

- 业务能力的 Go 文件只能位于该能力的 `domain`、`usecase` 或 `port` package。
- Domain 的项目内依赖只能指向 `internal/shared`，并禁止 MongoDB、HTTP、Proto、配置、JSON 和具体日志依赖及 `bson/json/protobuf` struct tag。
- Port 只能依赖同能力 Domain 与 `internal/shared`。
- UseCase 只能依赖同能力 Domain、Port 与 `internal/shared`。
- `internal/shared` 不得反向依赖任何业务能力。
- Domain、UseCase、Port 与 `internal/shared` 默认不得新增第三方依赖；确需窄依赖时先接受相应架构变更并显式调整测试。
- 已接受的窄例外（2026-09-27，UC-APP-013）：仅 `internal/profile/domain` 可直接导入 `golang.org/x/text/unicode/norm`，用于 BR-PRF-003–005 的纯 NFC 规范化。它无网络、时钟或存储副作用；不扩大到 x/text 其他包、其他能力、UseCase、Port 或 shared。架构测试必须同时覆盖允许位置及这些拒绝位置。
- 具体 adapter package 之间不得互相导入；只有 transport adapter 可以导入 UseCase，MongoDB/Auth 等 provider adapter 只面向能力 Port 与必要的 Domain 类型。
- Adapter 不得读取 `internal/config`；只有 composition root 可以同时依赖配置与具体 adapter。
- 禁止全局 `internal/biz`、`internal/data`、`internal/domain`、`internal/service` 和 `internal/util` package。
- composition root 只位于 `cmd/app-center`。

自动化检查只维护依赖和物理结构，不推断业务语义，也不取代 BR 测试和评审。确有新依赖方向需求时，必须先修改本 ADR，再在同一变更中调整架构测试；不得通过删除、跳过或弱化测试绕过边界。

### ADR-004：MongoDB 事务与 Schema 管理（`ACCEPTED`）

#### 决定

App Center 的权威写模型使用支持多文档事务的 MongoDB 部署拓扑。开发、测试和生产至少运行 replica set 或其他被当前 MongoDB 版本明确支持事务的拓扑；不支持事务的 standalone 部署不属于受支持环境。

跨文档 BR 使用 MongoDB transaction 实现，并遵循：

- 事务内只执行本地 MongoDB 读写，不调用 Auth、HTTP、消息系统或其他远程服务。
- 外部校验在事务前完成；BR 要求最终复检的本地事实在事务内重新读取或通过条件写保护。
- transient transaction error 或 unknown commit result 按 MongoDB 官方语义重试完整事务/提交，不单独重试其中一次写入。
- 事务重试使用同一组命令输入、ID 与审计时间，避免一次逻辑操作产生多个身份或时间。
- 唯一索引、条件更新和事务共同保护并发不变量；应用层的预检查只用于改善错误体验。
- Adapter 把 duplicate key、write conflict 和事务失败映射为当前 port 能表达的稳定结果。

Repository port 优先暴露一个完整业务原子行为，例如 `CreateWithinQuota`。当一个 UseCase 必须协调多个独立聚合 Repository 时，可以引入窄的 Transaction Manager，但不能让 Domain 感知 MongoDB session。

#### 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

### ADR-005：领域错误与 Transport 映射（`ACCEPTED`）

#### 决定

Domain 与 UseCase 使用协议无关的稳定错误分类。每个可预期业务失败具有：

```text
stable code
human-readable internal message
optional safe details
optional wrapped cause
```

稳定 code 使用设计文档中的业务失败名称。调用者通过错误类型、code 或 `errors.Is` 判断，不解析 message。

错误分为：

- Validation：输入无法形成合法值对象。
- Authentication：缺少或无效可信身份。
- Authorization：身份存在但没有执行权限。
- NotFound：目标不存在，或按隐私规则必须隐藏归属不匹配。
- Conflict：状态、唯一性、revision、容量或并发前置条件冲突。
- DependencyUnavailable：完成当前行为所需的外部事实暂不可用。
- Internal：未预期的实现或基础设施失败。

MongoDB/Auth 等 adapter 负责把技术错误转换为 port 定义的稳定结果，同时保留 cause。UseCase 再按业务上下文确定最终领域错误。例如 duplicate key 不能直接泄露索引名。

Transport adapter 在一个集中映射表中把领域错误转换为：

- 稳定 Proto error reason；
- canonical gRPC status；
- 对应 HTTP status；
- 可以安全返回的 message/details。

新 API 不采用“所有 HTTP 响应都返回 200，再在 JSON body 中表达错误”的形式。HTTP 与 gRPC 使用各自标准状态语义，稳定业务 code 供客户端做细分处理。

未知错误统一映射为 Internal，不向客户端返回 cause、数据库字段、索引名、远程地址、token、secret 或 stack trace。日志和 trace 在服务端保留原 cause，并使用同一 trace ID 关联。

#### 隐私与存在性隐藏

当 UC 规定跨 Application 的资源归属不匹配按 NotFound 处理时，Transport 不得把内部的“存在但不属于调用者”转换成 Forbidden。存在性隐藏属于业务契约，而不是展示文案。

错误 details 采用明确 allowlist。字段校验可以返回安全字段名和约束类别，但不能回显任意用户内容或凭证。

### ADR-006：Proto v1 与独立 API 仓库协作（`ACCEPTED`）

#### 决定

新协议在 API 仓库使用独立命名空间和目录：

```text
app_center/v1/...
package app_center.v1.<capability>
```

`v1` 只表示共享协议命名空间，不进入 App Center 的领域 package、collection 名或业务身份。Schema revision 由 migration ledger 中的 `0001`、`0002` 等迁移 ID 管理，collection 名保持无版本的业务命名。

Proto 源文件继续由独立 API 仓库拥有。App Center 服务仓库固定引用一个明确的 API repository revision；不得依赖浮动分支或在服务仓库手工维护生成代码的私有修改。

协作顺序为：

1. Domain 与 UseCase 通过自己的 Command/Result 类型稳定业务行为。
2. 在 API 仓库增加或修改 v1 Proto、error reason 和生成配置。
3. 生成代码并在 API 仓库通过检查后提交。
4. App Center 更新固定 revision。
5. Transport adapter 显式完成 Proto 与 UseCase 类型转换。
6. 两个仓库分别使用各自可审查的 commit。

Proto 不直接复用 Domain struct，也不把生成 message 传入 Domain。字段 presence、oneof、timestamp、enum unknown value 和 transport validation 在 adapter 边界处理。

#### 协议演进

即使系统尚未上线，已提交到共享 API 仓库的 v1 字段编号也保持稳定：

- 不重用删除字段的编号或名称，使用 `reserved`。
- enum 保留明确的 `UNSPECIFIED = 0`，业务上不接受时由 adapter 拒绝。
- 不把数据库内部字段、comparison key、技术计数器或 secret 暴露为公共字段。
- 写请求不接受可信身份、服务端状态和审计字段。
- 分页 cursor 是不透明 bytes/string，不承诺内部编码。
- Error reason 与 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 的稳定业务 code 对齐。

HTTP annotation 和 gRPC service 共享同一 Proto 语义。HTTP API 使用 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 定义的标准状态映射。

#### 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/account-owner-exit-v1.md`：账号退出时的 App 归属协调 v1

#### 范围与事实来源

本契约是 [UC024](../../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md) 和 [UC025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md) 所需的 Auth/App 实现契约，App 工作包见 UC-APP-025。Auth 决定资格退出或账号终止；App 决定哪些应用及归属操作仍需该账号承担责任，并阻止并发新增归属。不能用一次无保护的查询代替本协议。

首版 App 中所有 `adminId=authId` 的 Application（包括草稿、审核中、未发布、已发布）都阻止退出。仅清空发布槽不算处置；转让、关闭如何移除归属义务由后续 App UC 明确，在其交付前拥有应用的用户无法完成此流程。历史 creator/reviewer 引用不等于当前所有权，但存在仍需该账号负责的待处理归属操作也阻止退出。

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

### `platform/contracts/application-close-reauth-proof-v1.md`：Application 关闭近期认证证明 v1

#### 目的与边界

本契约定义用户在关闭一个 Application 前，如何用当前 Session 所属的同一登记设备完成一次新的 challenge/signature，并由 Auth Center 签发只能交给 App Center、只能用于该 Application 关闭的短期 JWS。

普通 USER JWS 的 `iat` 表示可信身份何时签发，不表示用户刚刚重新证明设备私钥控制权。前端确认框、Session 最近使用时间、密码输入字符串和已有 OAuth token 也不能代替本文证明。

Auth Center 拥有 Session、设备凭据、新挑战、签发密钥和 proof claims；App Center 验证 proof，并把 `jti` 唯一绑定到 ApplicationClosure。本契约不授予 Application 管理权；App 仍须依据 UC-APP-027 复查当前管理员、Developer 状态和 revision。

#### Proof JWS

成功 Complete 返回 compact JWS。JOSE header：

```json
{
  "alg": "RS256",
  "kid": "<auth-key-id>",
  "typ": "iwut-app-close-reauth+jwt"
}
```

payload 必须包含：

```json
{
  "iss": "<configured-auth-issuer>",
  "aud": "iwut-app-center",
  "sub": "<authId>",
  "token_type": "APP_CLOSE_REAUTH",
  "purpose": "app.close",
  "application_id": "<applicationId>",
  "jti": "<UUIDv7>",
  "auth_time": 0,
  "iat": 0,
  "nbf": 0,
  "exp": 0
}
```

`auth_time` 是 Auth 成功验证本次新设备签名的时间，不得取 Session 创建/使用时间；`iat` 与 `auth_time` 相同。`nbf = iat - 30s`，`exp = iat + 5m`。签发后不允许刷新或换取新 proof；过期后必须重新 Begin/Complete。

签名密钥可以与 Auth 的可信用户身份签发共用轮换设施，但 verifier 必须按精确 `typ`、`token_type`、audience 和 purpose 分派，不能把该 proof 当 USER identity，反向也不能把 USER identity 当 proof。

#### 幂等、重放与消费

首次成功 Complete 在同一 Auth 事务中把 operation 置为 COMPLETED，并固定 `jti/auth_time/iat/nbf/exp`。完全相同 operation、applicationId、Session 和签名的重试返回同一 claims 和逐字节相同 JWS；不得签发第二个 jti 或延长期限。实现可持久化固定 claims 并按规范编码重签，不需要保存 proof 明文。

已完成 operation 的不同签名、不同 Session 或不同 applicationId 均拒绝。未完成 operation 的签名失败只递增有界失败计数，不生成 proof。

App 验证签名、issuer、固定 audience、typ、token_type、purpose、applicationId、subject、时间和 `jti`。允许最大 30 秒时钟偏差，但 proof 的总寿命仍固定 5 分钟；App 接受时还要求 `now - auth_time <= 5m`。

App 在 UC-APP-027 的本地关闭事务中唯一消费 `jti`：

- 首次消费只能绑定一个 applicationId、subject 和 closureId；
- 同一 `jti` 对同一 ApplicationClosure 的网络重试返回既有 CLOSING/CLOSED 结果；
- 跨 Application、跨 subject、跨 purpose 或绑定另一个 closureId 一律按重放拒绝；
- 只在关闭事务成功时提交消费记录，事务回滚不能永久烧掉 proof。

Auth 不回调 App 查询 `jti` 是否消费；App 不向 Auth 声称 proof 已使用。短寿命、App 唯一约束和业务绑定共同提供重放边界。

#### 错误、限额与隐私

- 非法字段、UUID、长度或 DER：HTTP 400 / INVALID_ARGUMENT。
- Session、operation、签名或绑定无效以及过期：统一 HTTP 401 / UNAUTHENTICATED；未经证明不能区分账号、凭据或 operation 状态。
- 账号级限额：HTTP 429 / RESOURCE_EXHAUSTED，并提供有界 Retry-After。
- 持久化或签名服务暂不可用：HTTP 503 / UNAVAILABLE；不能返回未持久化的 proof。
- 记录损坏、已完成 claims 不一致：HTTP 500 / INTERNAL。

proof、challenge 和 signature 不进入业务审计。Auth 审计只记录 operationId、authId、credentialId、applicationId、结果类别、jti（成功时）和时间；App 审计只保存 proof jti，不保存 proof 原文。短期 operation 在过期后按既有认证挑战清理机制删除；已消费 jti 的永久/长期保留由 ApplicationClosure 审计拥有。

#### 兼容与验收

v1 允许追加可选响应字段；改变 domain/action、Frame 顺序、签名算法、固定 audience/purpose、5 分钟上限或消费键需要新版本。

双方至少覆盖：

1. 同一登记设备的新签名成功，只有 Session、USER JWS、旧登录签名或另一设备签名失败。
2. Begin 后账号禁用、Session/credential 撤销、revision 变化或 applicationId 改写时 Complete 失败。
3. Complete 提交后响应丢失，重试返回同一 jti、时间和 JWS；不延长 exp。
4. 错误 issuer/audience/typ/token_type/purpose/sub/applicationId、未来 auth_time、过期和超过允许时钟差均被 App 拒绝。
5. App 关闭事务失败后 proof 可在原期限内重试；事务成功后的同 closure 重试幂等，跨 closure/application/subject 重放失败。
6. challenge/签名/proof 不进 URL、普通日志、审计或缓存；限额与失败计数有界。

### `platform/contracts/application-closure-v1.md`：Application 关闭协调 v1

#### 目的与边界

本契约定义 App Center 在 Application 进入不可逆 `CLOSING` 后，如何要求 Auth Center 建立永久的 applicationId 级授权撤销事实，并在未知结果、重试和进程重启后收敛。

App Center 是 Application 生命周期、Publication、OAuth registration 和关闭流程的权威；Auth Center 是 consent grant、authorization code、token family、sector、pairwise sub 及授权执行的权威。双方不共享数据库，也不把远程调用放进本地事务。

本契约不定义用户发起关闭的公网 API、账号关闭或平台强制关闭。近期重新认证格式见 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md)。

#### 先决条件与生效点

App 必须先在一个本地事务中：

- 把 Application 从 ACTIVE 改为 CLOSING；
- 安装所有本地运行与写入 gate；
- 禁用既有 OAuth client slot；
- 创建稳定 closureId 和 durable delivery task。

该事务提交是 App 侧停止服务的生效点。Auth 调用失败不能恢复 ACTIVE。App 只有取得 Auth 的 APPLIED receipt 后才能把 Application 改为 CLOSED。

#### 服务身份

仅提供原生 gRPC，不提供 HTTP annotation、gRPC-Web 或终端路由。

```text
package auth_center.v1.application_closure
service ApplicationClosureService
```

App→Auth 使用 [Trusted Service Identity v1](../../platform/contracts/trusted-service-identity-v1.md)、固定 audience `iwut-auth-center` 和 Auth 本地 App caller allowlist：

| 方法 | permission |
| --- | --- |
| `ApplyApplicationClosure` | `auth.application-closure.apply` |
| `GetApplicationClosureStatus` | `auth.application-closure.read` |

USER identity、未知 key、错误 audience、禁用 caller、缺少精确 permission 或过期 service JWS 一律失败关闭。Auth 不能接受终端自报的 applicationId/closureId。

#### RPC 草图

```proto
message ApplyApplicationClosureRequest {
  string application_id = 1;
  string closure_id = 2;
  google.protobuf.Timestamp closing_started_at = 3;
}

message GetApplicationClosureStatusRequest {
  string application_id = 1;
  string closure_id = 2;
}

enum ApplicationClosureState {
  APPLICATION_CLOSURE_STATE_UNSPECIFIED = 0;
  APPLICATION_CLOSURE_STATE_APPLIED = 1;
}

message ApplicationClosureStatus {
  string application_id = 1;
  string closure_id = 2;
  ApplicationClosureState state = 3;
  string receipt_id = 4;
  google.protobuf.Timestamp applied_at = 5;
}
```

`ApplyApplicationClosure` 成功只返回 APPLIED，不暴露内部扫描、grant 数量、用户数量或 token 数量。`GetApplicationClosureStatus` 返回相同资源。

#### 投递、查询与收敛

- App 使用同一个 closureId 至少一次投递 Apply。
- 建议初始退避 1 秒、指数增长、最大 60 秒；单次 RPC deadline 5 秒。
- Apply 超时、断连或响应丢失时，App 使用相同 applicationId＋closureId 查询 Get；Get NOT_FOUND 后才能重试相同 Apply。
- App 不能因未知结果生成新 closureId，也不能把超时当成 APPLIED。
- Auth 返回 APPLIED 后，App 验证 applicationId、closureId、receiptId、appliedAt 完整且匹配，再持久保存回执并推进 CLOSED。
- App 的 CLOSING 没有协议超时。长期故障触发运维告警，但不回滚关闭或恢复运行。

#### 错误与兼容

- 参数格式错误：INVALID_ARGUMENT。
- service identity 无效：UNAUTHENTICATED。
- caller 或 permission 不允许：PERMISSION_DENIED。
- Get 无匹配记录：NOT_FOUND。
- 既有 applicationId/closureId/时间绑定冲突：ALREADY_EXISTS 或 FAILED_PRECONDITION；实现必须固定一种 reason 供契约测试。
- Auth 暂时无法提交持久事实：UNAVAILABLE。
- tombstone 或 receipt 数据不变量损坏：INTERNAL。

v1 只允许追加可选字段和新的只读方法。改变幂等键、允许取消、缩短永久保留、把 APPLIED 拆成可回退状态或削弱最终 tombstone 检查都需要新版本。

#### 验收矩阵

双方契约测试至少覆盖：

1. 首次 Apply、相同请求重复 Apply 和 Get 返回完全相同 receipt。
2. 相同 applicationId 使用不同 closureId、相同 closureId 使用不同时间的冲突。
3. Apply 已提交但响应丢失、Get 已提交但响应丢失、App/Auth 任一侧重启。
4. USER JWS、错误 audience、未知/禁用 caller、错误 permission 和过期 service JWS。
5. tombstone 前取得的 code、access token、refresh family 在 tombstone 后全部按对应入口失败。
6. tombstone 后并发 authorize/exchange/refresh/delegation 的最终事务复查，不能产生晚到的有效凭证。
7. provider 暂时不可用不创建 tombstone；已有 tombstone 时 provider 恢复也不能重新授权。
8. 历史 sector/sub/grant 保留但 applicationId 永不复用。

### `platform/contracts/auth-developer-status-v1.md`：Auth Developer Status v1 跨服务契约

#### 目的与所有权

Auth Center 是 Developer 状态的唯一权威。提供方行为由
[UC-AUTH-002](../../auth-center/use-cases/UC-AUTH-002-batch-get-developer-statuses.md)
及其 `BR-DEV-*` 拥有；本文件只定义跨服务线格式和错误边界。

#### gRPC 方法

```text
/auth_center.v1.developer_status.DeveloperStatusDirectory/BatchGetDeveloperStatuses
```

```proto
service DeveloperStatusDirectory {
  rpc BatchGetDeveloperStatuses(BatchGetDeveloperStatusesRequest)
      returns (BatchGetDeveloperStatusesResponse);
}

message BatchGetDeveloperStatusesRequest {
  repeated string auth_ids = 1;
}

message BatchGetDeveloperStatusesResponse {
  repeated DeveloperStatusEntry entries = 1;
}

message DeveloperStatusEntry {
  string auth_id = 1;
  DeveloperStatus developer_status = 2;
  AccountStatus account_status = 3;
}

enum DeveloperStatus {
  DEVELOPER_STATUS_UNSPECIFIED = 0;
  DEVELOPER_STATUS_PENDING = 1;
  DEVELOPER_STATUS_APPROVED = 2;
  DEVELOPER_STATUS_REJECTED = 3;
  DEVELOPER_STATUS_SUSPENDED = 4;
  DEVELOPER_STATUS_WITHDRAWN = 5;
}
```

AccountStatus 固定 0=UNSPECIFIED（成功非法）,1=ACTIVE,2=DISABLED,3=CLOSED。CLOSED 是合法 USER 墓碑，仅此状态下 developer_status 必须 UNSPECIFIED；ACTIVE/DISABLED 仍要求明确 Developer 枚举，普通 null Developer 保持 NOT_FOUND。

该方法没有 `google.api.http` annotation，不经 Gateway 暴露，也不提供 gRPC-Web。

#### 完整批量语义

- 请求包含 `1..100` 个唯一 Auth ID。
- 成功响应 entries 数量与请求相同，顺序一致，auth_id 逐项相等。
- `DEVELOPER_STATUS_UNSPECIFIED` 仅在 account_status=CLOSED 的合法终止墓碑响应中允许。
- 任一主体未知或状态无法读取时整个 RPC 失败，不返回部分 entries。
- 请求和响应只包含 opaque authId、账号状态与 Developer 状态，不投影用户资料。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_DEVELOPER_STATUS_READ_FORBIDDEN` |
| 批量输入非法 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_DEVELOPER_STATUS_QUERY` |
| 任一主体未知或不适用 | `NOT_FOUND` | `ERROR_REASON_DEVELOPER_STATUS_NOT_FOUND` |
| 权威状态暂不可读取或记录损坏 | `UNAVAILABLE` | `ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含 MongoDB 查询、用户资料、服务凭证或堆栈。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center`，App Center 为 `iwut-app-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### Auth Center 固定授权映射

| gRPC 方法 | 必需 permission |
| --- | --- |
| `ScopeCatalog/GetScopeCatalogSnapshot` | `auth.scope-catalog.read` |
| `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | `auth.developer-status.read` |
| `SystemPrincipalDirectory/ResolveSystemPrincipal` | `auth.system-principal.resolve` |
| `UserIdentityService/IssueUserIdentityFromSession` | `auth.identity.issue` |
| `ApplicationClosureService/ApplyApplicationClosure` | `auth.application-closure.apply` |
| `ApplicationClosureService/GetApplicationClosureStatus` | `auth.application-closure.read` |

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-027`（use-cases/UC-APP-027-close-application.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/account-owner-exit-v1.md`（docs 根级共享文档）：内部接口、固定线格式与方法授权、交付门禁
- `platform/contracts/application-close-reauth-proof-v1.md`（docs 根级共享文档）：签发入口、新挑战和设备签名、权威用例
- `platform/contracts/application-closure-v1.md`（docs 根级共享文档）：Auth 持久事实、Auth 执行语义、权威用例
- `platform/contracts/auth-developer-status-v1.md`（docs 根级共享文档）：调用方身份、契约测试要求、兼容性
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：App Center 固定授权映射、ENV 配置、契约测试要求、账号归属退出方法、Application 关闭方法

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-027-close-application.md` | 273 | `d2761c77847f` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `70d736bfa904` |
| `platform/contracts/application-close-reauth-proof-v1.md` | 152 | `1e16aa4fe484` |
| `platform/contracts/application-closure-v1.md` | 135 | `05e04ba6d669` |
| `platform/contracts/auth-developer-status-v1.md` | 97 | `65d986d93af1` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `platform/contracts/trusted-service-identity-v1.md` | 124 | `4a64372bc9c0` |
