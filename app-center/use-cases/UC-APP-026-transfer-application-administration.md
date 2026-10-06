# UC-APP-026：转让 Application 管理权

状态：`ACCEPTED`

## 目标与范围

> 当前管理员向另一名符合资格的 Developer 发起转让；目标管理员显式接受后，App Center 在一个本地事务内改变当前管理权、移动配额占用、处理旧管理凭证，并立即使旧管理员失去后续写权限。

本用例负责：

- 保存独立于 Application 的管理权转让申请和完整终态审计。
- 支持当前管理员发起、取消，目标管理员接受、拒绝。
- 每个 Application 同时只允许一个 `PENDING` 申请，并让申请在固定期限后过期。
- 接受前向 Auth 批量取得源、目标账号和 Developer 的新鲜状态。
- 在同一事务中更新 `Application.adminId`、双方配额、转让终态和相关安全状态。
- 由目标管理员在接受时显式选择保留或轮换现有 CONFIDENTIAL client secret。
- 撤销当前 ACTIVE Tester 加入链接；保留既有 Tester Membership。
- 与 [UC-APP-025](UC-APP-025-coordinate-account-owner-exit.md) 的账号归属退出屏障互锁。

本用例不负责：

- 平台人员强制转让、绕过目标接受、争议仲裁或紧急接管。
- Application 改名、关闭、归档或恢复。
- 转移 Auth consent、grant、token、用户身份或服务器资产。
- 自动创建新的 Tester 加入链接。
- 可靠通知、消息已读状态或把消息系统作为转让事实来源。
- 通过分布式事务保证 Auth 状态在 App 提交瞬间仍完全不变。

## 参与者与依赖

- **源管理员**：发起时的 `Application.adminId`，可以在接受前取消。
- **目标管理员**：申请指定的 `toAdminId`，可以接受或拒绝。
- **Auth Center**：通过 [Auth Developer Status v1](../../platform/contracts/auth-developer-status-v1.md) 提供账号与 Developer 的权威当前状态。
- **App Center**：拥有当前管理员、名称占用、配额、转让生命周期、OAuth credential 和 Tester 链接事实。

转让只改变当前管理关系。Application ID、技术名称、创建时间、Version/Profile/Review/Publication/Filter/Tester Membership/OAuth clientId 及全部历史归因保持不变。历史 `createdBy`、`submittedBy`、`reviewer` 等字段不是当前权限来源，不能随转让改写。

## 输入与身份

发起：

```text
InitiateApplicationAdminTransferCommand {
  applicationId: ApplicationId
  toAuthId: AuthId
  expectedOwnershipRevision: int64
}
```

当前管理员先通过 `GetApplicationOwnership` 取得：

```text
ApplicationOwnershipResource {
  applicationId
  ownershipRevision
  pendingTransferId?
  pendingExpiresAt?
}
```

该资源不返回 adminId、配额或目标用户资料；存在已到期 PENDING 时先收敛为 EXPIRED。它为发起命令提供 expectedOwnershipRevision，不替代未来完整的 Application 管理查询。

接受：

```text
AcceptApplicationAdminTransferCommand {
  transferId: ApplicationAdminTransferId
  confidentialCredentialHandling: KEEP | ROTATE
}
```

拒绝、取消和读取只携带 `transferId`。所有调用者身份来自可信用户身份上下文；请求不能自报 `fromAdminId`、接受者、Developer 状态、配额或转让终态。

`confidentialCredentialHandling` 必须显式提供：

- `KEEP`：服务器和运营主体只发生交接时，保留全部现有 CONFIDENTIAL secret。
- `ROTATE`：轮换该 Application 在 TEST、GREY、STABLE 中所有已经存在的 CONFIDENTIAL secret。

平台强制转让若未来建立独立用例，不得默认使用 `KEEP`。

## 生命周期

```text
                         ACCEPT
                    ┌────────────► ACCEPTED
                    │
                    ├── REJECT ──► REJECTED
CREATE ──► PENDING ─┤
                    ├── CANCEL ──► CANCELLED
                    │
                    └── EXPIRE ──► EXPIRED
```

终态不可恢复为 `PENDING`，也不能改写为其他终态。申请有效期固定为 7 天：`expiresAt = requestedAt + 7 days`。任何命令或 Get 发现 `PENDING` 且 `now >= expiresAt` 时，必须先在事务中收敛为 `EXPIRED`；后台扫描器负责让长期无人访问的记录最终收敛，但正确性不能依赖扫描时机。

同一 Application 同时最多一个 `PENDING` 申请。同一用户可以同时是多个不同 Application 申请的源或目标。

## 发起流程

1. 验证 applicationId、toAuthId 和正数 expectedOwnershipRevision；目标不能等于调用者。
2. 验证调用者是当前管理员，并且可信身份显示 accountStatus=`ACTIVE`、developerStatus=`APPROVED`。
3. 通过 Auth 的非缓存批量查询确认目标当前 accountStatus=`ACTIVE`、developerStatus=`APPROVED`；未知、缺项、错序、损坏或依赖失败均失败关闭。
4. 在本地事务中按 authId 字典序取得源、目标 `account_owner_exit_fences`，再取得 Application coordination fence。
5. 复查两个账号归属 fence 允许新增归属变化，Application.adminId、ownershipRevision 仍匹配，并收敛该 Application 已到期的旧申请。
6. 若相同目标已有未过期 PENDING，返回既有申请且不改变期限；若其他目标已有 PENDING，返回冲突。
7. 创建申请，保存源、目标、当前 ownershipRevision、requestedAt 和 expiresAt。

发起不预占目标配额，也不预留名称。接受时才以当前事实作最终决定。发起成功后目标账号的 owner-exit Prepare 必须因 `PENDING_OWNERSHIP_CHANGE` 被阻止。

## 接受流程

1. 验证 transferId、接受者身份和显式 credential handling，读取 PENDING 申请。
2. 调用 Auth `BatchGetDeveloperStatuses(fromAdminId, toAdminId)`，不使用 App 进程缓存；两人都必须是 accountStatus=`ACTIVE` 且 developerStatus=`APPROVED`。
3. 在本地事务中按 authId 字典序取得源、目标账号归属 fence，再取得 Application coordination fence。
4. 重新读取申请并处理到期；复查调用者等于 toAdminId、申请仍为 PENDING、两个 fence 均允许提交、Application.adminId 等于 fromAdminId，且 ownershipRevision 等于 sourceOwnershipRevision。
5. 复查目标配额存在容量，且目标名下不存在与 Application.nameKey 大小写等价的名称。
6. 从 App Clock 取得一个 resolvedAt。如选择 `ROTATE`，为所有现有 CONFIDENTIAL client 生成新 secret，并在事务中替换摘要、增加各自 credentialRevision，以 toAdminId/resolvedAt 记录轮换审计；如选择 `KEEP`，不修改任何 OAuth registration 或 credential 字段。
7. 如存在 ACTIVE TesterJoinLink，将其改为 REVOKED，reason=`ADMIN_TRANSFER`、revokedBy=toAdminId、revokedAt=resolvedAt，不创建替代链接。
8. 在同一事务中：
   - 源配额 `usedCount - 1`；
   - 目标配额 `usedCount + 1`；
   - `Application.adminId = toAdminId`；
   - `Application.ownershipRevision + 1`；
   - 转让状态改为 ACCEPTED，保存 resolvedAt、resolvedBy 和 credential handling；
   - 保存 OAuth credential 与链接变化的审计。
9. 提交确定后返回转让资源。`ROTATE` 的新 secret 只在首次成功响应披露一次。

若提交成功后的响应丢失，重复接受返回既有 ACCEPTED 结果，不再次披露 secret。目标管理员可查询 credential metadata，再通过 [UC-APP-018](UC-APP-018-manage-oauth-client.md) 独立执行新一轮轮换。

## 拒绝与取消

- 只有目标管理员可以拒绝 PENDING 申请。
- 只有仍为当前管理员的源管理员可以取消 PENDING 申请。
- 拒绝和取消均在账号 fence、Application fence 与转让状态的一致事务中完成。
- 操作发现已经到期时返回 EXPIRED 终态，不覆盖为 REJECTED 或 CANCELLED。
- 同一参与者重复请求相同终态返回既有结果；试图把其他终态改写为本终态返回冲突。
- REJECTED、CANCELLED、EXPIRED 立即不再构成目标账号的 pending owner-exit blocker。
- 当前管理员依据 UC-APP-027 把 Application 推进为 CLOSING 时，可以在同一本地事务把 PENDING 申请改为 CANCELLED，`resolutionCause=APPLICATION_CLOSURE`；这不是参与者主动取消，也没有恢复入口。

## 业务规则

<a id="br-app-012"></a>
### BR-APP-012：转让身份与参与者

`Application.adminId` 是当前管理权的唯一权威结果；`ApplicationAdminTransfer` 保存过程和审计，不把 `pendingAdminId` 或 transferStatus 塞入 Application。源必须是发起时当前管理员，目标必须是不同的 Auth 用户；只有目标可以接受或拒绝，只有仍为当前管理员的源可以取消。

<a id="br-app-013"></a>
### BR-APP-013：单一待处理申请与固定过期

每个 Application 最多一个 PENDING 申请，有效期固定 7 天。ACCEPTED、REJECTED、CANCELLED、EXPIRED 均为不可变终态。所有相关命令和 owner-exit 检查都必须先收敛已到期记录，不能让物理上尚未被后台扫描的过期记录永久阻塞新申请或账号退出。

<a id="br-app-014"></a>
### BR-APP-014：新鲜 Auth 资格与有界竞态

发起时目标、接受时源与目标都必须由 Auth 权威批量查询确认为 ACTIVE＋APPROVED；接受查询不得使用进程缓存。Auth 不可用、响应不完整、顺序错误或状态非法时失败关闭。

本版不引入 Auth revision、资格 reservation 或跨服务事务。新鲜查询之后、App 事务提交之前发生的 SUSPENDED/DISABLED 具有现有 JWS 传播模型相同的有界窗口；WITHDRAWAL/CLOSURE 则由 BR-APP-017 的本地归属 fence 阻止进入终局。未来 Auth 响应即使追加 revision，也只能先用于审计，不能宣称形成原子 OCC。

<a id="br-app-015"></a>
### BR-APP-015：管理权 revision 与共享写栅栏

Application 持有正数 `ownershipRevision`，旧记录迁移为 1。发起时调用者提供 expectedOwnershipRevision，申请保存 sourceOwnershipRevision；只有接受成功使其增加 1。

转让与 Version、Profile、Publication、Tester、OAuth、Filter 及其他管理员写操作共用 Application `coordinationRevision` 写栅栏，并在最终事务中复查当前 admin。旧管理员持有的尚未过期 JWS 无需全局撤销：接受先提交时其后续写入因 adminId 不匹配而失败；旧管理员写入先提交时，其操作先线性化，接受再基于更新后的完整 Application 事实提交或失败。

`ownershipRevision` 是管理权 API 的业务 OCC，不替代 adapter-only coordinationRevision，也不因普通下级写入增加。

<a id="br-app-016"></a>
### BR-APP-016：所有权、配额与名称原子转移

接受必须在一个本地事务中同时移动 `adminId`、双方 quota usedCount、ownershipRevision 和申请终态。目标容量不足或存在 `(toAdminId, nameKey)` 冲突时拒绝接受，不自动改名、不临时超额，也不产生部分配额移动。

源配额记录缺失、usedCount 为零、目标配额损坏、Application 归属漂移或申请绑定不一致属于内部数据不变量异常。目标配额记录不存在时，以 UC001 相同的配置上限在接受事务内惰性建立，再检查容量。

<a id="br-app-017"></a>
### BR-APP-017：账号退出屏障与确定锁序

PENDING 的入站转让是目标账号 [UC-APP-025](UC-APP-025-coordinate-account-owner-exit.md) Prepare 的 `PENDING_OWNERSHIP_CHANGE` blocker；源账号在接受前仍因 OWNED_APPLICATIONS 被阻止。发起、接受、拒绝、取消、过期收敛和 owner-exit Prepare 使用同一 `account_owner_exit_fences` 协调点。

涉及两个账号和 Application 时，先按 authId 原始字节字典序取得全部账号 fence，再取得 Application coordination fence。接受完成后，源立即不再拥有该 Application；App 不自动替源发起 Developer withdrawal 或账号关闭，源需重试 Auth 流程。

<a id="br-app-018"></a>
### BR-APP-018：Credential 与 Tester 链接处理

接受者必须显式选择 KEEP 或 ROTATE。KEEP 保留所有 clientId、secret 摘要、credentialRevision、registrationRevision、authorizationEpoch、状态、grant 和 token。ROTATE 保留 clientId、registrationRevision、authorizationEpoch、状态、grant 和 token，只对全部现有 CONFIDENTIAL credential 使用 UC018 语义替换摘要并各自增加 credentialRevision；PUBLIC client 不受影响。

ROTATE 的明文 secret 只在首次确定提交后的响应中披露一次，日志、审计、trace 和重试结果不得记录或重放。没有 CONFIDENTIAL client 时 ROTATE 仍可成功并返回空 credential 列表。

接受同时把当前 ACTIVE TesterJoinLink 撤销为 `ADMIN_TRANSFER`，`revokedBy=toAdminId`、`revokedAt=resolvedAt`、`replacedByJoinLinkId=null`。已有 Tester Membership 和人数计数保持不变；新管理员需要邀请时显式调用 UC008 创建新链接。

<a id="br-app-019"></a>
### BR-APP-019：终态审计、幂等与最小披露

转让终态永久保存参与者、Application、源 ownershipRevision、时间、操作者和 credential handling。读取只允许 from/to 参与者，不提供公开枚举，也不返回技术配额、secret 摘要或其他管理员资料。

同一发起者对相同目标重复发起返回现有 PENDING；目标不同则冲突。终态命令的安全重试返回既有终态，但一次性 secret 永不重放。消息、邮件或 Console deep link 只携带 transferId 等最小定位信息，投递失败不改变转让事实。

## 领域与数据模型

```text
Application {
  id
  name
  adminId
  ownershipRevision
  createdAt
}

ApplicationAdminTransfer {
  transferId
  applicationId
  fromAdminId
  toAdminId
  sourceOwnershipRevision
  status: PENDING | ACCEPTED | REJECTED | CANCELLED | EXPIRED
  requestedAt
  expiresAt
  resolvedAt?
  resolvedBy?
  resolutionCause?: EXPLICIT | APPLICATION_CLOSURE
  confidentialCredentialHandling?
}
```

`application_admin_transfers` 至少具有：

- transferId 唯一索引。
- applicationId 在 status=PENDING 条件下的 partial unique index。
- `(toAdminId, status, expiresAt)` 索引，供 owner-exit blocker 与过期收敛查询。
- `(fromAdminId, requestedAt, transferId)` 与 `(applicationId, requestedAt, transferId)` 审计索引。
- validator 固定参与者非空且不同、正 sourceOwnershipRevision、状态与 resolved 字段组合、`requestedAt < expiresAt`。

ACCEPTED、REJECTED、CANCELLED 都要求 resolvedAt 与 resolvedBy；EXPIRED 要求 resolvedAt 且 resolvedBy 为空。只有 ACCEPTED 保存 confidentialCredentialHandling，其他状态必须为空。CANCELLED 保存 resolutionCause：普通源管理员取消为 EXPLICIT；UC027 的关闭事务为 APPLICATION_CLOSURE。其他终态不保存该字段。

App migration 0021 为既有 Application 回填 `ownershipRevision=1`，创建转让集合及索引，并把 TesterJoinLink `revocationReason` 扩展为 `ROTATED | MANUAL | ADMIN_TRANSFER`。ADMIN_TRANSFER 与 MANUAL 一样要求 `replacedByJoinLinkId=null`。

## API 草图

独立 package：`app_center.v1.application_admin_transfer`；service：`ApplicationAdminTransferService`。

| RPC | HTTP | 访问者 |
| --- | --- | --- |
| `GetApplicationOwnership` | `GET /v1/applications/{application_id}/ownership` | 当前源管理员 |
| `InitiateApplicationAdminTransfer` | `POST /v1/applications/{application_id}/admin-transfers` | 当前源管理员 |
| `GetApplicationAdminTransfer` | `GET /v1/application-admin-transfers/{transfer_id}` | 源或目标参与者 |
| `AcceptApplicationAdminTransfer` | `POST /v1/application-admin-transfers/{transfer_id}:accept` | 目标管理员 |
| `RejectApplicationAdminTransfer` | `POST /v1/application-admin-transfers/{transfer_id}:reject` | 目标管理员 |
| `CancelApplicationAdminTransfer` | `POST /v1/application-admin-transfers/{transfer_id}:cancel` | 当前源管理员 |

稳定枚举：

```text
ApplicationAdminTransferStatus:
  UNSPECIFIED=0 PENDING=1 ACCEPTED=2 REJECTED=3 CANCELLED=4 EXPIRED=5

ConfidentialCredentialHandling:
  UNSPECIFIED=0 KEEP=1 ROTATE=2
```

接受响应包含转让资源，以及仅在首次 ROTATE 成功时出现的：

```text
rotatedCredentials[] {
  channel
  clientId
  credentialRevision
  clientSecret
}
secretsDisclosed: bool
```

数组按 `TEST < GREY < STABLE` 的固定渠道顺序返回；同一渠道至多一个 CONFIDENTIAL client。幂等重试固定返回空数组和 `secretsDisclosed=false`。

所有响应使用 `Cache-Control: no-store`。不提供列表接口；管理界面通过已知 transferId 打开详情，通知能力留给后续 outbox 工作包。

## 错误边界

| 情况 | HTTP / gRPC | 稳定 reason 示例 |
| --- | --- | --- |
| ID、revision、handling 非法 | 400 / INVALID_ARGUMENT | `INVALID_APPLICATION_ID`、`INVALID_TRANSFER_ID`、`INVALID_TARGET_AUTH_ID`、`INVALID_OWNERSHIP_REVISION`、`INVALID_CONFIDENTIAL_CREDENTIAL_HANDLING` |
| Application 或 transfer 不存在 | 404 / NOT_FOUND | `APPLICATION_NOT_FOUND`、`APPLICATION_ADMIN_TRANSFER_NOT_FOUND` |
| 调用者不是要求的参与者 | 403 / PERMISSION_DENIED | `APPLICATION_ADMIN_REQUIRED`、`APPLICATION_ADMIN_TRANSFER_PARTICIPANT_REQUIRED` |
| 已有其他 PENDING、名称冲突 | 409 / ALREADY_EXISTS | `APPLICATION_ADMIN_TRANSFER_ALREADY_PENDING`、`APPLICATION_NAME_CONFLICT` |
| 配额不足、已过期或终态不允许操作 | 409 / FAILED_PRECONDITION | `APPLICATION_QUOTA_EXCEEDED`、`APPLICATION_ADMIN_TRANSFER_EXPIRED`、`APPLICATION_ADMIN_TRANSFER_NOT_PENDING` |
| ownership revision 或当前归属变化 | 409 / ABORTED | `APPLICATION_OWNERSHIP_CHANGED` |
| 账号归属退出屏障阻止写入 | 409 / FAILED_PRECONDITION | `ACCOUNT_OWNER_EXIT_IN_PROGRESS` |
| Auth 状态不符合资格 | 422 / FAILED_PRECONDITION | `SOURCE_DEVELOPER_INELIGIBLE`、`TARGET_DEVELOPER_INELIGIBLE` |
| Auth 不可用或响应非法 | 503 / UNAVAILABLE | `DEVELOPER_STATUS_UNAVAILABLE` |
| 本地绑定、配额或关联状态损坏 | 500 / INTERNAL | `APPLICATION_ADMIN_TRANSFER_STATE_INCONSISTENT`、`INTERNAL` |

不存在和非参与者的读取不得泄漏目标账号资料；Transport 可以统一外部 message，但稳定 reason 仍按可信调用边界记录。错误、日志和 metrics 不得包含 secret、secret 摘要、完整 Auth 响应或数据库内部结构。

## 并发验收场景

- 发起与目标 owner-exit Prepare 并发：只能形成 PENDING blocker 或先完成退出屏障后拒绝发起，不能两者同时越过。
- 接受与源/目标 owner-exit 并发：按账号 fence 线性化，不能把 Application 转给 WITHDRAWN/CLOSED 目标，也不能让源仍被错误计为 owner。
- 两次发起竞争：同 Application 最多一个 PENDING；相同目标幂等，目标不同冲突。
- 接受与取消、拒绝、过期竞争：只能提交一个终态。
- 接受与任意管理员写入竞争：共享 Application fence 决定先后；接受后旧管理员写入失败。
- 接受与 OAuth secret 轮换、client 状态修改竞争：不得丢失 credential revision、registration revision 或 epoch 变化。
- 接受与 Tester 链接创建/轮换/加入竞争：接受后旧 ACTIVE 链接不可继续加入；此前已提交 Membership 保留。
- 目标配额最后一个名额、同名创建与接受竞争：唯一索引和配额事务不能超额或产生重名。
- ROTATE 覆盖零个、一个及多个渠道的 CONFIDENTIAL client；任一写入失败则管理权、配额、链接和全部 credential 一起回滚。
- 成功 ROTATE 后响应丢失：重试不重放 secret，UC018 后续轮换仍可恢复运营。
- Auth 查询后目标被临时 DISABLED：记录并接受有界窗口，不虚构跨服务原子保证；后续管理写仍按其入口的新鲜身份门禁失败。

## 实现依赖与交付边界

现有设计已经提供所需基础：UC001 的名称/配额事务，UC008–011 的 Tester 链接，UC018 的 credential 轮换，UC025 的账号 fence，以及 Auth Developer Status 批量 provider。没有需要先新增的跨服务字段或协议。

实现需要一个纵切片同时更新：

- Domain/UseCase 和 Mongo migration 0021。
- Proto、HTTP/gRPC transport、可信身份与 composition root。
- UC025 Prepare 的入站 PENDING 查询和到期收敛。
- UC018 credential repository 的事务内批量轮换复用点。
- 真实 MongoDB 竞争测试与 Auth provider consumer 测试。

本文件已经接受。实现以生成的 UC-APP-026 brief 为工作包输入，并按本节边界交付 Domain、API、migration、跨能力事务和完整验收。

## 变更记录

- 2026-10-06：建立 UC-APP-026 提案；采用发起—接受模型、新鲜 Auth 检查、本地 ownershipRevision 与共享写栅栏；接受者显式选择 KEEP/ROTATE，转让时撤销 Tester 加入链接。
- 2026-10-06：接受 UC-APP-026；依赖检查确认 UC001、UC008–011、UC018、UC025 和 Auth Developer Status provider 已交付，生成实现 brief 并启动纵切片。
