<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-026 --spec tools/brief-specs/UC-APP-026.json -->
# Brief — UC-APP-026：转让 Application 管理权

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-026` 转让 Application 管理权 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-012`–`BR-APP-019`（8 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/account-owner-exit-v1.md`、`platform/contracts/app-center-api-routing.md`、`platform/contracts/auth-developer-status-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

> 当前管理员向另一名符合资格的 Developer 发起转让；目标管理员显式接受后，App Center 在一个本地事务内改变当前管理权、移动配额占用、处理旧管理凭证，并立即使旧管理员失去后续写权限。

本用例负责：

- 保存独立于 Application 的管理权转让申请和完整终态审计。
- 支持当前管理员发起、取消，目标管理员接受、拒绝。
- 每个 Application 同时只允许一个 `PENDING` 申请，并让申请在固定期限后过期。
- 接受前向 Auth 批量取得源、目标账号和 Developer 的新鲜状态。
- 在同一事务中更新 `Application.adminId`、双方配额、转让终态和相关安全状态。
- 由目标管理员在接受时显式选择保留或轮换现有 CONFIDENTIAL client secret。
- 撤销当前 ACTIVE Tester 加入链接；保留既有 Tester Membership。
- 与 [UC-APP-025](../use-cases/UC-APP-025-coordinate-account-owner-exit.md) 的账号归属退出屏障互锁。

本用例不负责：

- 平台人员强制转让、绕过目标接受、争议仲裁或紧急接管。
- Application 改名、关闭、归档或恢复。
- 转移 Auth consent、grant、token、用户身份或服务器资产。
- 自动创建新的 Tester 加入链接。
- 可靠通知、消息已读状态或把消息系统作为转让事实来源。
- 通过分布式事务保证 Auth 状态在 App 提交瞬间仍完全不变。

### 参与者与依赖

- **源管理员**：发起时的 `Application.adminId`，可以在接受前取消。
- **目标管理员**：申请指定的 `toAdminId`，可以接受或拒绝。
- **Auth Center**：通过 [Auth Developer Status v1](../../platform/contracts/auth-developer-status-v1.md) 提供账号与 Developer 的权威当前状态。
- **App Center**：拥有当前管理员、名称占用、配额、转让生命周期、OAuth credential 和 Tester 链接事实。

转让只改变当前管理关系。Application ID、技术名称、创建时间、Version/Profile/Review/Publication/Filter/Tester Membership/OAuth clientId 及全部历史归因保持不变。历史 `createdBy`、`submittedBy`、`reviewer` 等字段不是当前权限来源，不能随转让改写。

### 输入与身份

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

### 生命周期

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

### 发起流程

1. 验证 applicationId、toAuthId 和正数 expectedOwnershipRevision；目标不能等于调用者。
2. 验证调用者是当前管理员，并且可信身份显示 accountStatus=`ACTIVE`、developerStatus=`APPROVED`。
3. 通过 Auth 的非缓存批量查询确认目标当前 accountStatus=`ACTIVE`、developerStatus=`APPROVED`；未知、缺项、错序、损坏或依赖失败均失败关闭。
4. 在本地事务中按 authId 字典序取得源、目标 `account_owner_exit_fences`，再取得 Application coordination fence。
5. 复查两个账号归属 fence 允许新增归属变化，Application.adminId、ownershipRevision 仍匹配，并收敛该 Application 已到期的旧申请。
6. 若相同目标已有未过期 PENDING，返回既有申请且不改变期限；若其他目标已有 PENDING，返回冲突。
7. 创建申请，保存源、目标、当前 ownershipRevision、requestedAt 和 expiresAt。

发起不预占目标配额，也不预留名称。接受时才以当前事实作最终决定。发起成功后目标账号的 owner-exit Prepare 必须因 `PENDING_OWNERSHIP_CHANGE` 被阻止。

### 接受流程

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

若提交成功后的响应丢失，重复接受返回既有 ACCEPTED 结果，不再次披露 secret。目标管理员可查询 credential metadata，再通过 [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md) 独立执行新一轮轮换。

### 拒绝与取消

- 只有目标管理员可以拒绝 PENDING 申请。
- 只有仍为当前管理员的源管理员可以取消 PENDING 申请。
- 拒绝和取消均在账号 fence、Application fence 与转让状态的一致事务中完成。
- 操作发现已经到期时返回 EXPIRED 终态，不覆盖为 REJECTED 或 CANCELLED。
- 同一参与者重复请求相同终态返回既有结果；试图把其他终态改写为本终态返回冲突。
- REJECTED、CANCELLED、EXPIRED 立即不再构成目标账号的 pending owner-exit blocker。
- 当前管理员依据 UC-APP-027 把 Application 推进为 CLOSING 时，可以在同一本地事务把 PENDING 申请改为 CANCELLED，`resolutionCause=APPLICATION_CLOSURE`；这不是参与者主动取消，也没有恢复入口。

### 领域与数据模型

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

### API 草图

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

### 错误边界

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

### 并发验收场景

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

### 实现依赖与交付边界

现有设计已经提供所需基础：UC001 的名称/配额事务，UC008–011 的 Tester 链接，UC018 的 credential 轮换，UC025 的账号 fence，以及 Auth Developer Status 批量 provider。没有需要先新增的跨服务字段或协议。

实现需要一个纵切片同时更新：

- Domain/UseCase 和 Mongo migration 0021。
- Proto、HTTP/gRPC transport、可信身份与 composition root。
- UC025 Prepare 的入站 PENDING 查询和到期收敛。
- UC018 credential repository 的事务内批量轮换复用点。
- 真实 MongoDB 竞争测试与 Auth provider consumer 测试。

本文件已经接受。实现以生成的 UC-APP-026 brief 为工作包输入，并按本节边界交付 Domain、API、migration、跨能力事务和完整验收。

## 业务规则（UC-APP-026 权威正文）

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-012 -->
### BR-APP-012：转让身份与参与者

`Application.adminId` 是当前管理权的唯一权威结果；`ApplicationAdminTransfer` 保存过程和审计，不把 `pendingAdminId` 或 transferStatus 塞入 Application。源必须是发起时当前管理员，目标必须是不同的 Auth 用户；只有目标可以接受或拒绝，只有仍为当前管理员的源可以取消。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-013 -->
### BR-APP-013：单一待处理申请与固定过期

每个 Application 最多一个 PENDING 申请，有效期固定 7 天。ACCEPTED、REJECTED、CANCELLED、EXPIRED 均为不可变终态。所有相关命令和 owner-exit 检查都必须先收敛已到期记录，不能让物理上尚未被后台扫描的过期记录永久阻塞新申请或账号退出。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-014 -->
### BR-APP-014：新鲜 Auth 资格与有界竞态

发起时目标、接受时源与目标都必须由 Auth 权威批量查询确认为 ACTIVE＋APPROVED；接受查询不得使用进程缓存。Auth 不可用、响应不完整、顺序错误或状态非法时失败关闭。

本版不引入 Auth revision、资格 reservation 或跨服务事务。新鲜查询之后、App 事务提交之前发生的 SUSPENDED/DISABLED 具有现有 JWS 传播模型相同的有界窗口；WITHDRAWAL/CLOSURE 则由 BR-APP-017 的本地归属 fence 阻止进入终局。未来 Auth 响应即使追加 revision，也只能先用于审计，不能宣称形成原子 OCC。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-015 -->
### BR-APP-015：管理权 revision 与共享写栅栏

Application 持有正数 `ownershipRevision`，旧记录迁移为 1。发起时调用者提供 expectedOwnershipRevision，申请保存 sourceOwnershipRevision；只有接受成功使其增加 1。

转让与 Version、Profile、Publication、Tester、OAuth、Filter 及其他管理员写操作共用 Application `coordinationRevision` 写栅栏，并在最终事务中复查当前 admin。旧管理员持有的尚未过期 JWS 无需全局撤销：接受先提交时其后续写入因 adminId 不匹配而失败；旧管理员写入先提交时，其操作先线性化，接受再基于更新后的完整 Application 事实提交或失败。

`ownershipRevision` 是管理权 API 的业务 OCC，不替代 adapter-only coordinationRevision，也不因普通下级写入增加。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-016 -->
### BR-APP-016：所有权、配额与名称原子转移

接受必须在一个本地事务中同时移动 `adminId`、双方 quota usedCount、ownershipRevision 和申请终态。目标容量不足或存在 `(toAdminId, nameKey)` 冲突时拒绝接受，不自动改名、不临时超额，也不产生部分配额移动。

源配额记录缺失、usedCount 为零、目标配额损坏、Application 归属漂移或申请绑定不一致属于内部数据不变量异常。目标配额记录不存在时，以 UC001 相同的配置上限在接受事务内惰性建立，再检查容量。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-017 -->
### BR-APP-017：账号退出屏障与确定锁序

PENDING 的入站转让是目标账号 [UC-APP-025](../use-cases/UC-APP-025-coordinate-account-owner-exit.md) Prepare 的 `PENDING_OWNERSHIP_CHANGE` blocker；源账号在接受前仍因 OWNED_APPLICATIONS 被阻止。发起、接受、拒绝、取消、过期收敛和 owner-exit Prepare 使用同一 `account_owner_exit_fences` 协调点。

涉及两个账号和 Application 时，先按 authId 原始字节字典序取得全部账号 fence，再取得 Application coordination fence。接受完成后，源立即不再拥有该 Application；App 不自动替源发起 Developer withdrawal 或账号关闭，源需重试 Auth 流程。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-018 -->
### BR-APP-018：Credential 与 Tester 链接处理

接受者必须显式选择 KEEP 或 ROTATE。KEEP 保留所有 clientId、secret 摘要、credentialRevision、registrationRevision、authorizationEpoch、状态、grant 和 token。ROTATE 保留 clientId、registrationRevision、authorizationEpoch、状态、grant 和 token，只对全部现有 CONFIDENTIAL credential 使用 UC018 语义替换摘要并各自增加 credentialRevision；PUBLIC client 不受影响。

ROTATE 的明文 secret 只在首次确定提交后的响应中披露一次，日志、审计、trace 和重试结果不得记录或重放。没有 CONFIDENTIAL client 时 ROTATE 仍可成功并返回空 credential 列表。

接受同时把当前 ACTIVE TesterJoinLink 撤销为 `ADMIN_TRANSFER`，`revokedBy=toAdminId`、`revokedAt=resolvedAt`、`replacedByJoinLinkId=null`。已有 Tester Membership 和人数计数保持不变；新管理员需要邀请时显式调用 UC008 创建新链接。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-019 -->
### BR-APP-019：终态审计、幂等与最小披露

转让终态永久保存参与者、Application、源 ownershipRevision、时间、操作者和 credential handling。读取只允许 from/to 参与者，不提供公开枚举，也不返回技术配额、secret 摘要或其他管理员资料。

同一发起者对相同目标重复发起返回现有 PENDING；目标不同则冲突。终态命令的安全重试返回既有终态，但一次性 secret 永不重放。消息、邮件或 Console deep link 只携带 transferId 等最小定位信息，投递失败不改变转让事实。

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

#### 固定线格式与方法授权

App package `app_center.v1.account_owner_exit`、service `AccountOwnerExitService`，PrepareAccountOwnerExit / FinishAccountOwnerExit / GetAccountOwnerExitStatus 分别要求 `app.account-owner-exit.prepare` / `app.account-owner-exit.finish` / `app.account-owner-exit.read`，仅授权 Auth caller。Auth package `auth_center.v1.account_owner_exit`、service `AccountOwnerExitDecisionService/GetAccountOwnerExitDecision` 要求 `auth.account-owner-exit.read`，仅 App caller。均无 HTTP annotation 或终端路由。

消息字段号固定：PrepareRequest auth_id=1, operation_id=2, purpose=3；FinishRequest auth_id=1, operation_id=2, receipt_id=3, decision=4, purpose=5；GetStatusRequest 与 GetDecisionRequest 均 auth_id=1, operation_id=2。Purpose 枚举 0=UNSPECIFIED(拒绝),1=DEVELOPER_WITHDRAWAL,2=ACCOUNT_CLOSURE；Decision 0=UNSPECIFIED,1=PENDING,2=COMMITTED,3=CANCELLED，Finish 不允许 PENDING。

PrepareResponse outcome=1（0非法,1=PREPARED,2=BLOCKED）,receipt_id=2,blocker=3（0=NONE,1=OWNED_APPLICATIONS,2=PENDING_OWNERSHIP_CHANGE）。App 状态/Finish 响应统一 auth_id=1,operation_id=2,purpose=3,decision=4,receipt_id=5,cleanup_state=6（0非法,1=NOT_REQUIRED,2=PENDING,3=COMPLETE）。GetDecisionResponse decision=1,purpose=2,receipt_id=3。状态查询对未知 operation 返回 NOT_FOUND，不暗示取消。

App 的 ACCOUNT_CLOSURE COMMITTED 持久创建个人清理任务，GetStatus 的 cleanup_state=COMPLETE 才表示个人数据清理回执；WITHDRAWAL 为 NOT_REQUIRED。Auth 先调用 Finish 再轮询持久状态确认 App 回执，不把 Finish 网络成功误认为全部清理完成。App 也可回查 Auth 终局用于收敛。

AuthId 沿用现有 1..200 bytes opaque ID；operationId 为 Auth UUIDv4，receiptId 为 App 生成 UUIDv7，不作秘密；所有比较原样精确。双边后台重试初始 1 秒、指数退避最大 60 秒，每批最多 100，RPC deadline 5 秒，含有界抖动。部署参数可调整但不得把到期当作自动解除屏障。每个操作的终局摘要永久保留至关联墓碑被明确政策替代，避免任意迟到 Prepare 越过已清理的取消记录；大体量诊断材料在回执后 30 天内清理。

#### 交付门禁

提供方权威用例为 UC-APP-025，支持零归属用户。转让/关闭已有应用不在本轮，有应用者持续 BLOCKED。必须更新实际创建入口和 ACCOUNT_CLOSURE 下 Tester 加入入口，防止旧 JWS 重建个人状态；未来增加归属写入口必须复用此屏障。

验收覆盖 Prepare 与创建竞争、取消先于 Prepare、Auth 提交后丢响应、双边重启、长时间故障、过期准备、重复 Finish、目标/receipt/purpose 错配、WITHDRAWN 后注销取消不解除原 sealed、注销清理与 Tester 加入竞争。联调前退出/注销公网开关保持关闭。

### `platform/contracts/app-center-api-routing.md`：App Center API 路由 v1 契约

#### 路由映射

App Center 的每个 HTTP 资源在 Proto 内部使用的路径**不含服务前缀**。Gateway 为外部请求增加且只增加一个服务前缀 `/app-center`。

首个正式资源 CreateApplication 的映射是：

| 层 | 方法与路径 | 说明 |
| --- | --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications` | 客户端唯一可见的地址；`app-center` 是服务前缀 |
| Gateway | 剥离前缀 `/app-center` | 只做前缀剥离，不重写其余路径 |
| 内部（Gateway → App Center） | `POST /v1/applications` | Proto `google.api.http` annotation 声明的路径；请求体 `body: "*"` |
| gRPC | `/app_center.v1.application.Application/CreateApplication` | proto package `app_center.v1.application`，service `Application`，rpc `CreateApplication` |

UC-APP-005 审核决定命令遵循同一映射规则：

| 层 | 方法与路径 |
| --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| Gateway | 只剥离前缀 `/app-center` |
| 内部（Gateway → App Center） | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| gRPC | `/app_center.v1.application_review.ApplicationReview/DecideApplicationVersionReview` |

规则：

- Gateway 必须按**服务名到前缀**的映射表工作，不得把 `/app-center` 硬编码进业务路径，也不得同时改写内部资源路径。
- 前缀剥离后必须保留查询串与请求体。
- 内部路径与 gRPC full method 由 Proto 定义，App Center 的 HTTP 路由注册必须与 Proto annotation 一致；两者不得各写一份。
- 写请求只通过请求体传递资源字段；可信身份只通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 定义的 `x-iwut-identity` 传递，路径或 query 不承载身份。
- 未匹配的服务前缀或缺少前缀的外部请求由 Gateway 拒绝，不转发给 App Center。

#### gRPC-Web 终止

- gRPC-Web 在 **Traefik** 终止，不进入 App Center 进程。
- App Center 后端只暴露**原生 gRPC**；不嵌入 `grpc-web` wrapper，也不注册 gRPC-Web 专用的 HTTP handler。
- 浏览器流量由 Traefik 完成 gRPC-Web ⇄ gRPC 转换后，以原生 gRPC 到达 App Center；身份键仍为 metadata `x-iwut-identity`。
- 因此 App Center 不为 gRPC-Web 增加 CORS、content-type 或协议转换配置；这些属于 Traefik。

#### 契约测试要求

外部到内部的映射必须由**自动化契约测试**机械验证，不能只靠文档。测试至少断言：

1. Proto HTTP annotation 的内部路径等于 `POST /v1/applications`。
2. 外部路径等于服务前缀 `/app-center` 加内部路径，即 `POST /app-center/v1/applications`。
3. 前缀映射只剥离 `/app-center`，得到的内部路径与第 1 项一致。
4. gRPC full method 等于 `/app_center.v1.application.Application/CreateApplication`。
5. 写请求 message 只包含 `name`，不包含身份字段（`authId`、`developer_status`）、服务端字段（`id`、`adminId`、`createdAt`）或持久化技术字段。
6. 响应 message 不包含 `nameKey`、`nextVersionSequence`、`nextProfileRevisionSequence` 或其它内部技术字段。
7. 审核决定的外部/内部路径与上述 UC-APP-005 映射精确一致，gRPC full method 使用同一生成 service。
8. UC-APP-005 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

外部路径可以作为 contract constant / fixture 存在于测试中，但它必须与内部路径、前缀和 gRPC method 在同一测试里被自动验证，任何一侧漂移都必须让测试失败。

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

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证
内部服务身份。Auth Center 在验签后按固定 full method → `auth.developer-status.read`
映射检查 caller 注册表；测试 server 不能被当作生产无认证入口。

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

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. package/service/rpc 的 full method 精确一致。
2. request 只有 `auth_ids = 1`，没有用户或服务身份字段。
3. response 和 enum 字段号保持稳定。
4. entries 与请求一一对应并保持顺序。
5. ACTIVE/DISABLED 的 UNSPECIFIED、未知 account_status、缺项、额外项、重复项或错序均拒绝；CLOSED+UNSPECIFIED 为合法终止结果。
6. INVALID_ARGUMENT、NOT_FOUND、UNAVAILABLE 和稳定 reason 映射一致。
7. App Center 测试 Auth Server 实现同一生成接口，不维护手写 wire model。

#### 兼容性

- v1 可以追加 optional 字段或错误 reason，但不得改变现有字段号、类型、枚举值或 full method。
- 删除字段或枚举时必须 reserve 原 name 与 number。
- 改变完整批量和 fail-closed 语义需要新的平台契约评审。

2026-10-05：治理工作包共同接受 CLOSED 终止投影与 WITHDRAWN 枚举扩展，保持完整批量和失败关闭规则；未上线系统的测试 fixture 同步升级，不接受缺 account_status 的旧响应。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
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

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### App Center 固定授权映射

App Center 通过原生 gRPC 开放 OAuth provider 和账号归属退出 provider，不生成 HTTP annotation。完整方法与本地 caller registry permission 固定为：

| gRPC 方法 | 必需 permission |
| --- | --- |
| `OAuthClientProviderService/GetClientConfiguration` | `app.oauth.client.read` |
| `OAuthClientProviderService/VerifyClientSecret` | `app.oauth.client.verify` |
| `OAuthClientProviderService/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` |
| `OAuthClientProviderService/ResolveAuthorizationContext` | `app.oauth.context.resolve` |
| `OAuthClientProviderService/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` |

未知方法默认拒绝。普通 USER/SYSTEM trusted identity、第三方 access token、client secret 和网络位置都不能替代 Auth service identity。

#### ENV 配置

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_IDENTITY_ID` | `serviceId` |
| `APP_CENTER_SERVICE_IDENTITY_KID` | 当前签名 key ID |
| `APP_CENTER_SERVICE_IDENTITY_AUDIENCE` | 默认 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_PRIVATE_KEY_PEM_B64` | PKCS#1 或 PKCS#8 RSA private-key PEM 的 strict standard Base64 |
| `APP_CENTER_SERVICE_IDENTITY_TTL` | 正 Go duration；默认 `1m` |

Auth Center 必须提供 `AUTH_CENTER_SERVICE_CALLERS_B64`：以下 JSON UTF-8 bytes 的 strict standard Base64。

```json
{
  "iwut-app-center": {
    "status": "ACTIVE",
    "keys": {
      "app-center-2026-01": {
        "publicKeyPemB64": "<RSA public-key PEM 的 strict standard Base64>"
      }
    },
    "permissions": [
      "auth.scope-catalog.read",
      "auth.developer-status.read",
      "auth.system-principal.resolve"
    ],
    "systemPrincipalPurposes": [
      "app-center.review-auto-rejection"
    ]
  }
}
```

外层 Base64 只解决环境变量传输与转义，不提供保密性。部署必须用 secret 管理 App 私钥；不得把值提交到仓库、镜像、日志或诊断输出。Auth 公钥注册表不含私钥，可以由 config 或 secret 注入。缺失、未知字段、重复权限、非法 key、未知 permission/purpose 或空注册表必须阻止启动。

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_CALLERS_B64` | 与 Auth caller registry 相同的 strict Base64 JSON schema；首版登记 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` | 接受的最大 token TTL，默认 `1m` |
| `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW` | claims 时钟偏差，默认 `30s` |

App Center registry 中 `iwut-auth-center` 允许上述五个 `app.oauth.*` permission，以及 account-owner-exit-v1 固定的三个 app.account-owner-exit.* 精确权限，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

#### 契约测试要求

至少验证合法调用、缺失/错误签名、未知 serviceId、未知 kid、错误 audience、过长 TTL、disabled caller、缺少 RPC permission 和未允许 purpose。生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor，不能只验证同接口 fake server。

#### 账号归属退出方法

精确 full method、调用方向及权限以 [account-owner-exit-v1](../../platform/contracts/account-owner-exit-v1.md#固定线格式与方法授权) 为准。Auth 接受 App 的 auth.account-owner-exit.read；App 接受 Auth 的 prepare/finish/read。它们不授予其他服务权限、不开放 HTTP 或通用 wildcard。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-026`（use-cases/UC-APP-026-transfer-application-administration.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/account-owner-exit-v1.md`（docs 根级共享文档）：Auth 协调与故障
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-026-transfer-application-administration.md` | 324 | `7e93553d9cdd` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `70d736bfa904` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/auth-developer-status-v1.md` | 97 | `65d986d93af1` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
| `platform/contracts/trusted-service-identity-v1.md` | 116 | `b33b72ad4752` |
