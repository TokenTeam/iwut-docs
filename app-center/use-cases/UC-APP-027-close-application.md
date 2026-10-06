# UC-APP-027：关闭 Application

状态：`PROPOSED`

## 目标与范围

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

## 参与者与前置依赖

- **当前管理员**：必须等于 `Application.adminId`，可信身份当前显示 accountStatus=`ACTIVE`、developerStatus=`APPROVED`。
- **Auth Center**：签发绑定本次高风险操作的近期重新认证证明，并依据 [Application Closure v1](../../platform/contracts/application-closure-v1.md) 保存永久 Application 授权撤销事实。
- **App Center**：拥有 Application 生命周期、当前管理员、配额、Publication、Tester、OAuth registration 和关闭过程。

本提案进入 `ACCEPTED` 前必须补齐两个依赖：

1. Auth Center 的关闭消费方 UC，明确 application closure tombstone 在授权、换码、发 token、refresh 和在线校验最终事务边界的执行位置。
2. Auth 与 App 共用的近期重新认证证明契约。普通 App USER JWS 的 `iat` 只表示该身份上下文何时签发，不能证明用户刚完成密码、Passkey 或其他新认证，不能单独满足本用例。

## 输入、预览与身份

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

近期重新认证证明通过专用 metadata/header `x-iwut-high-risk-proof` 传递，不放进 URL、命令正文、日志或审计 payload。证明至少绑定：

```text
iss, aud="iwut-app-center", sub=authId,
purpose="app.close", applicationId,
jti, auth_time, iat, nbf, exp
```

Auth 只在一次新的认证事件后签发；证明最大寿命和允许的 `auth_time` 年龄均为 5 分钟。App 验证签名、issuer、audience、purpose、subject、applicationId 和时间，并把 jti 唯一绑定到首次创建的 ApplicationClosure。相同 jti 对同一关闭结果的网络重试返回既有资源；把它用于其他 Application、其他操作或不同 closure 则作为重放拒绝。失败、过期、跨 Application、跨用户或只提供普通 USER JWS 都不能关闭。

## 生命周期与可见行为

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

## 发起关闭流程

1. 校验 applicationId、两个正 revision 和逐字匹配的 confirmation。
2. 验证普通可信用户身份、近期重新认证证明及其 jti 绑定；调用 Auth 的非缓存批量状态查询，确认当前管理员仍为 ACTIVE＋APPROVED。Auth 不可用、缺项或响应损坏时失败关闭。已经绑定同一 ApplicationClosure 的 jti 可以直接返回既有结果，不重复资格查询或副作用。
3. 读取 Application 与影响摘要。若已经 CLOSING/CLOSED，只有命令证明 jti 已绑定该 ApplicationClosure 时才按 Close 的幂等重试返回既有资源；其他调用应使用 Get，不能用新的关闭命令枚举终态。
4. 开始本地事务。先按原始 authId 字节序取得当前管理员以及待处理转让目标（如有）的 `account_owner_exit_fences`，再取得 Application coordination fence。
5. 在事务内复查 adminId、ownershipRevision、lifecycleRevision、lifecycleStatus=`ACTIVE`、证明绑定和 jti 尚未绑定其他操作。任何漂移都拒绝整个命令。
6. 从 App Clock 取得一个 `closingStartedAt`，创建 ApplicationClosure 和持久收敛任务，并原子执行“本地关闭事务”中的全部变化。
7. 提交成功返回 `CLOSING`。后台在事务外调用 Auth；只有取得匹配的 APPLIED 回执后，才在 App 事务中保存回执并把生命周期推进为 CLOSED。

新鲜 Auth 状态查询与本地提交之间仍存在与 UC026 一致的有界跨服务窗口；本地 ownership/lifecycle OCC 和账号退出 fence 负责 App 内线性化，不能把 Auth 查询描述成跨服务原子锁。

## 本地关闭事务

进入 CLOSING 的事务必须全部成功或全部回滚：

1. `Application.lifecycleStatus = CLOSING`，`lifecycleRevision + 1`；adminId 作为历史当前管理员保留，ownershipRevision 不变。
2. 当前管理员的 `DeveloperApplicationQuota.usedCount - 1`，只执行一次。缺失配额、usedCount=0 或绑定漂移属于内部数据不变量异常。
3. 若存在 PENDING ApplicationAdminTransfer，把它改为 CANCELLED，`resolutionCause=APPLICATION_CLOSURE`、`resolvedBy=adminId`、`resolvedAt=closingStartedAt`。不创建新申请，不改变历史终态。
4. 若存在 ACTIVE TesterJoinLink，把它改为 REVOKED，`revocationReason=APPLICATION_CLOSURE`、`revokedBy=adminId`、`revokedAt=closingStartedAt`、`replacedByJoinLinkId=null`。已有 Tester Membership 原样保留作审计，不做最多 100 条的批量终态改写。
5. 遍历 TEST、GREY、STABLE registration 的已存在 client slot：ACTIVE 改为 DISABLED，并增加该 slot 的 authorizationEpoch；一个 registration 中至少一个 slot真实变化时，registrationRevision 只增加一次。已经 DISABLED 的 slot不变。不轮换或删除 confidential secret。
6. 创建唯一 ApplicationClosure、消费高风险证明 jti，并写入 durable outbox/task。

Version、ProfileRevision、Review、Publication、PublicationHistory、Filter 和 Tester Membership 均不改写。SUBMITTED/PENDING 审核保留原状态与证据，但 reviewer queue 必须排除非 ACTIVE Application，决定命令也必须失败。Publication 指针保留历史形状，不过运行解析因 Application 生命周期 gate 返回不可运行。

## Auth 持久撤销与最终收敛

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

## 业务规则

<a id="br-app-020"></a>
### BR-APP-020：不可逆生命周期与稳定身份

Application lifecycle 只有 `ACTIVE → CLOSING → CLOSED`。CLOSING 和 CLOSED 都不能恢复、取消或被普通管理员改写。ApplicationId 永不复用；技术名称在原管理员既有 `(adminId, nameKey)` 命名空间内永久占用，首版不提供释放或跨 owner 的墓碑复用规则。

<a id="br-app-021"></a>
### BR-APP-021：关闭权限、明确确认与近期认证

只有当前 ACTIVE＋APPROVED 管理员可以关闭。请求必须同时携带 expectedOwnershipRevision、expectedLifecycleRevision、逐字确认和绑定 applicationId 的一次性近期重新认证证明。普通 USER JWS、旧 Session 活跃、前端二次弹窗或命令 confirmation 都不能代替 Auth 证明的新认证事件。

<a id="br-app-022"></a>
### BR-APP-022：CLOSING 即时本地隔离

CLOSING 是关闭生效点。所有目录、启动、Tester、审核、Publication、Filter、Version/Profile 管理和 OAuth provider 路径必须在最终边界要求 Application ACTIVE；缓存不能把旧 ACTIVE 结果延长到关闭事务之后。CLOSED 只表示跨服务撤销已经确认，不是首次停止服务的时刻。

<a id="br-app-023"></a>
### BR-APP-023：OAuth 本地禁用与 Auth 永久撤销

本地事务禁用所有现有 channel/client type slot，并按真实状态变化增加 authorizationEpoch 和 registrationRevision；不删除 clientId、不轮换 secret、不改写 grant/token。Auth tombstone 独立永久阻止该 applicationId 的授权与 token 使用。两个边界缺一不可：本地 gate 提供即时效果，Auth tombstone 覆盖已经签发的 Auth 状态。

<a id="br-app-024"></a>
### BR-APP-024：依附状态保留与待处理操作终止

关闭保留 Version、Profile、Review、Publication、Filter、Tester Membership、OAuth registration/credential 和全部历史。PENDING 管理员转让与 ACTIVE 加入链接在本地事务中终止；待审核记录不改写，但从队列排除且不能再决定。避免为每个依附模型伪造 CLOSED/CANCELLED 状态，也避免一次关闭产生无界批量写入。

<a id="br-app-025"></a>
### BR-APP-025：配额、名称与 owner 义务

进入不可逆 CLOSING 时立即且只一次释放当前管理员一个配额占用，并不再构成 OWNED_APPLICATIONS 义务；adminId 留作历史归因。关闭与 owner-exit Prepare 使用同一账号 fence：Prepare 先线性化时看见 ACTIVE Application 并返回 BLOCKED，关闭先线性化时 Prepare 可在其余义务为零时成功。BLOCKED 的 Auth 操作由用户在关闭后重试。

<a id="br-app-026"></a>
### BR-APP-026：持久收敛、幂等与未知结果

ApplicationClosure 和 durable task 必须与 CLOSING 同事务创建。App→Auth 调用在事务外至少一次投递，使用稳定 closureId；超时、断连、响应丢失和重启都通过 Get 与相同 Apply 收敛。CLOSING 不因任务年龄回滚，只有匹配的 Auth APPLIED receipt 能推进 CLOSED。

<a id="br-app-027"></a>
### BR-APP-027：共享写栅栏与竞态

关闭与创建/接受/取消管理员转让、账号归属退出、Version/Profile/Review/Publication/Filter/Tester/OAuth 写操作共用 Application coordination fence；涉及账号时先按 authId 原始字节序锁全部 account_owner_exit_fences，再锁 Application。所有写入口必须在最终事务内复查 lifecycleStatus=ACTIVE，不能只依赖 handler 预读。

<a id="br-app-028"></a>
### BR-APP-028：终态审计、隐私与错误边界

关闭永久保存 applicationId、closureId、发起者、源 ownership/lifecycle revision、开始/完成时间、证明 jti、Auth receipt 和状态；不保存证明原文、secret、token 或用户资料。公开读取仍按未找到处理，管理读取只向发起时管理员披露最小状态。数据不变量损坏返回 INTERNAL，不伪装成业务冲突。

## 领域与数据模型

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

## API 草图

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

## 并发与验收场景

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

## 实现前决策结论

本提案已经确定：关闭不可逆；CLOSING 即释放配额和 owner 义务；技术名称首版不释放；不删除历史、不批量改写 Membership/Review；不轮换 secret；本地禁用与 Auth application tombstone 双层生效；只有 Auth 回执推进 CLOSED。

尚未满足的不是产品语义选择，而是跨服务可执行依赖：Auth 消费方 UC 与近期重新认证证明契约。两者完成并通过双方评审后，UC027 才能改为 ACCEPTED、生成 brief 和进入代码工作包。

## 变更记录

- 2026-10-06：建立 UC-APP-027 提案；采用不可逆 CLOSING/CLOSED、本地即时隔离、配额与 owner 义务在 CLOSING 释放、历史保留、OAuth slot 禁用和 Auth application tombstone 持久收敛；明确近期重新认证证明与 Auth 消费方 UC 是接受前依赖。
