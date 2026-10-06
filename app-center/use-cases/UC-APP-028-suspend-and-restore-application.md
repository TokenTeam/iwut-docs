# UC-APP-028：暂停与恢复 Application

状态：`ACCEPTED`

## 目标与范围

> 获得精确平台运维权限的人员可以临时暂停一个仍处于活动生命周期的 Application，使它立即退出 App Center 的目录、启动解析、Tester 新增加入和 OAuth 在线资格判断；问题处理完成后，另一项独立权限可以解除平台门禁，而各运行路径仍按当前 Version、Profile、Publication、Tester 和 OAuth 事实重新判断是否可用。

本用例负责：

- 为 Application 增加与关闭生命周期正交的 `platformAvailabilityStatus=AVAILABLE | SUSPENDED` 及独立 revision。
- 分别使用 `app.application.suspend` 与 `app.application.restore`，不复用审核、管理员或平台管理员身份。
- 在 App Center 本地事务内原子改变平台可用状态并保存不可变运维审计。
- 让 Catalog、统一启动解析、TEST descriptor、Tester Join 和五个 OAuth provider 方法消费同一个平台可用门禁。
- 明确 Auth 在线 OAuth 检查、App 快照、短期委托 JWS 和第三方本地会话的残余窗口。
- 恢复时保持现有配置原样，并保证恢复命令本身不能把已经失效或损坏的下级配置声明为可运行。

本用例不负责：

- Application 管理员的日常归档、单渠道 clear、不可逆关闭或平台强制转让。
- 修改、回滚、清空或重新审核 Profile、Version、Publication、Filter、Tester Membership、OAuth registration、grant 或 token。
- 因暂停释放 owner 义务、配额或技术名称；暂停不能帮助 Developer 退出或账号注销。
- 可靠通知、值班编排、自动恢复、定时暂停、批量操作或基于内容扫描自动暂停。
- 从第三方设备内存收回已返回的页面、ID Token、短期委托 JWS、应用自建 Session 或已经下载的数据。

暂停是平台对分发和在线授权资格的可恢复门禁。关闭是不可逆的 Application 生命周期终止；归档是未来管理员日常整理能力。三者不能共用字段或命令。

## 参与者与依赖

- **暂停操作人**：可信身份必须是 `accountStatus=ACTIVE` 的 USER，并精确包含 `app.application.suspend`。
- **恢复操作人**：可信身份必须是 `accountStatus=ACTIVE` 的 USER，并精确包含 `app.application.restore`。
- **Auth Center**：依据 [UC-AUTH-027](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 保存两项独立人员权限，并通过 audience=`iwut-app-center` 的短期 USER JWS 投影。
- **App Center**：唯一保存 Application 平台可用状态、revision 和业务审计；Auth 不复制 applicationId 级 suspension 状态。

两项权限不在平台管理员固定 bundle 中，必须独立授予；Reviewer、Developer、Application 当前管理员、SYSTEM 或完整平台管理员均不自动获得。App Center 只信任正确 audience、签名、issuer、typ、时间和 accountStatus 的 USER JWS，并要求精确 permission；OAuth access token、service JWS、请求正文自报角色和权限通配符都不能操作本用例。

Auth 权限撤销后，已签发 App audience USER JWS 的残余窗口沿用 UC-AUTH-027：默认 TTL 最长 60 秒、可配置 1–300 秒，并受既有 clock skew 约束。本用例首版不为操作人权限增加逐请求 Auth introspection 或 denylist。

## 输入、输出与 API 草图

读取：

```text
ApplicationPlatformAvailability {
  applicationId
  lifecycleStatus: ACTIVE | CLOSING | CLOSED
  lifecycleRevision: int64
  platformAvailabilityStatus: AVAILABLE | SUSPENDED
  platformAvailabilityRevision: int64
  lastOperationEventId?
  suspendedAt?
  restoredAt?
}
```

读取结果不返回 Application 管理员、操作人 authId、reason、OAuth client、Tester、发布或审核详情。运维审计通过受控审计查询能力读取，不混入普通状态响应。

暂停命令：

```text
SuspendApplicationCommand {
  applicationId: ApplicationId
  expectedLifecycleRevision: int64
  expectedPlatformAvailabilityRevision: int64
  reason: string
}
```

恢复命令字段相同，命名为 `RestoreApplicationCommand`。两个 revision 都必须为正数；reason 去除两端空白后为 1..1024 UTF-8 bytes。调用者身份和权限只来自可信 USER JWS，请求不能携带 actorAuthId、状态或 permission。

建议独立 package `app_center.v1.application_operations`，service 为 `ApplicationOperationsService`：

| 方法 | HTTP | 成功响应 |
| --- | --- | --- |
| `GetApplicationPlatformAvailability` | `GET /v1/applications/{application_id}/platform-availability` | 当前状态资源 |
| `SuspendApplication` | `POST /v1/applications/{application_id}:suspend` | 变化后的状态资源 |
| `RestoreApplication` | `POST /v1/applications/{application_id}:restore` | 变化后的状态资源 |

三种方法同时提供 HTTP/JSON 与原生 gRPC，响应使用 `Cache-Control: private, no-store`。Get 允许持有任一运维权限的 ACTIVE USER 调用；未授权者先失败，不能借 applicationId 或状态差异枚举 Application。

## 正交状态模型

```text
Application lifecycle                    Platform availability

ACTIVE ── close ──► CLOSING ──► CLOSED   AVAILABLE ◄── restore ── SUSPENDED
   │                                         │                     ▲
   └─ suspend/restore only here              └────── suspend ──────┘
```

- `lifecycleStatus` 继续只表达 `ACTIVE/CLOSING/CLOSED`，由 UC-APP-027 拥有。
- `platformAvailabilityStatus` 只表达平台临时运行门禁。既有 Application 迁移为 `AVAILABLE`、revision 1。
- 只有 lifecycle=`ACTIVE` 时可以 suspend 或 restore。CLOSING/CLOSED 即使保留历史 SUSPENDED 值也没有恢复入口。
- 关闭可以从 AVAILABLE 或 SUSPENDED 的 ACTIVE Application 发起；进入 CLOSING 后关闭规则优先，平台状态只作为历史事实保留。
- 暂停和恢复不改变 lifecycleRevision、ownershipRevision、adminId、配额或账号归属 blocker；关闭、转让和普通管理命令也不隐式改变平台可用状态。

## 暂停流程

1. 严格校验身份、`app.application.suspend`、applicationId、两个 expected revision 和 reason。
2. 读取 Application 当前状态；未授权身份在存在性读取前拒绝。
3. 开启本地事务并取得 Application coordination fence。
4. 在事务内复查 lifecycleStatus=`ACTIVE`、expectedLifecycleRevision、platformAvailabilityStatus=`AVAILABLE` 和 expectedPlatformAvailabilityRevision。
5. 从 App Clock 取得 occurredAt，写入 `SUSPENDED`、严格增加一次 platformAvailabilityRevision，并追加一条 `ApplicationPlatformOperationEvent(action=SUSPEND)`。
6. 状态、revision、审计和用于告警投递的 durable outbox 在同一事务提交；提交成功后返回该状态资源。

已经 SUSPENDED、stale revision 或与关闭并发失败时返回冲突，不追加第二条事件。提交结果未知时返回不可用，调用方通过 Get 读取权威状态，不用新 revision 盲目重放。

暂停不改写下级配置，也不禁用 OAuth slot 或增加 authorizationEpoch。它在 Application 级门禁处阻止整个应用的在线资格；这样恢复不需要恢复一批由暂停制造的派生状态，也不会把管理员原本主动 DISABLED 的 client 误启用。

## 恢复流程

1. 严格校验身份、`app.application.restore`、applicationId、两个 expected revision 和 reason。
2. 开启本地事务并取得同一个 Application coordination fence。
3. 在事务内复查 lifecycleStatus=`ACTIVE`、expectedLifecycleRevision、platformAvailabilityStatus=`SUSPENDED` 和 expectedPlatformAvailabilityRevision。
4. 验证 Application 当前状态结构完整；不把“存在 Stable”“存在公开 Profile”或“所有 OAuth client 均启用”作为恢复命令的前提，因为没有发布或主动禁用 client 都是合法业务状态。
5. 写入 `AVAILABLE`、严格增加一次 platformAvailabilityRevision，并原子追加 `ApplicationPlatformOperationEvent(action=RESTORE)` 与告警 outbox。
6. 返回平台状态资源。Catalog、启动解析、Tester 和 OAuth provider 在之后的每次请求中读取当前事实，并继续执行各自已有资格与不变量检查。

恢复只解除平台门禁，不产生“Application 已可运行”的保证。若当前没有兼容 Stable、Profile 已缺失、Version/Review snapshot 损坏、Tester 资格不足、client 已 DISABLED、回调为空或 OAuth 配置不一致，对应路径仍按原 UC 返回不可用或内部不变量异常；恢复不得写默认值、回退历史版本、自动启用 client 或跳过检查。

## 暂停期间的行为

| 能力 | SUSPENDED 行为 |
| --- | --- |
| UC024 Catalog 列表/详情 | 列表排除；详情沿用普通候选统一 NOT_FOUND，不暴露暂停事实 |
| UC023 统一启动解析 | 不返回任何 TEST/GREY/STABLE 目标；沿用统一目标不可用语义 |
| UC012 TEST descriptor | 不返回启动目标 |
| UC009 Tester Join | 不创建新 Membership；现有 Membership、计数和链接原样保留 |
| UC019 五个 Auth provider 方法 | 全部失败关闭，不返回可继续使用的 client/runtime/secret 验证/redirect snapshot |
| Profile、Version、Review、Publication、Filter、Tester 管理、OAuth registration/credential 管理 | 继续按原有管理员、Reviewer、revision 和 lifecycle 规则工作，使管理员可以修复问题 |
| 管理权转让 | 可以继续；暂停状态不变，新管理员不能自行恢复，除非另有 restore 权限 |
| 不可逆关闭 | 可以继续；进入 CLOSING 后 UC027 规则优先且不能恢复 |
| owner-exit / quota | 仍视为当前管理员拥有 Application；不释放配额或 blocker |

“立即失效”指暂停事务提交后开始的 App Center 权威读取不得产生新的目录项、启动描述、Tester Membership 或 OAuth provider 成功结果。事务提交前已经返回给客户端的数据无法撤回；Catalog 响应继续使用 `private, no-store`，启动解析不得建立长期租约或服务端资格缓存。

## OAuth 在线检查与残余窗口

UC019 的 `GetClientConfiguration`、`VerifyClientSecret`、`ResolveClientRuntimeConfiguration`、`ResolveAuthorizationContext` 和 `GetApplicationPublishedRedirects` 都必须在其一致 snapshot 中要求 lifecycle=`ACTIVE` 且 platformAvailabilityStatus=`AVAILABLE`。SUSPENDED 是正常业务门禁，不改写 registration/client 状态；provider 对 Auth 使用统一应用不可用分类，不能把暂停原因、操作人或 reason 返回给 OAuth 客户端。

由此得到以下边界：

- 新 authorize/consent、authorization code exchange、refresh、UserInfo 和 opaque access token 的在线 delegation 都会在各自已有 App provider 复查点失败；Auth 不得因旧 runtime tuple 或 provider 故障降级成功。
- App provider 在暂停前已经返回的 snapshot 最长仍可使用到既有 `validUntil`，当前契约不超过 observedAt＋5 秒。Auth 不能缓存延长，也不能把旧 snapshot 用于下一个安全边界。
- 资源访问依赖 UC-AUTH-019 在线签发短期委托 JWS。暂停后不再签发新的委托；暂停前已经签发的 JWS 最长 5 秒并允许 1 秒时钟差。结合最长 5 秒 App snapshot，既有契约给出的配置变化到最后一个旧委托可接受上界约为 11 秒。
- opaque access token 与 refresh token 可以继续作为历史凭据记录存在，但暂停期间不能通过在线边界获得新能力。恢复后，只要它们自身仍未过期、未撤销且所有当前 grant/client/channel/version/scope 条件重新满足，既有凭据可以再次通过在线检查；暂停本身不永久推进 grant、family 或 authorizationEpoch。
- 已经交付的 ID Token、第三方本地会话、页面和数据不受 App Center 控制；恢复或暂停都不应声称收回它们。要求永久撤销时使用 UC-APP-027 关闭流程，而不是 suspension。

## 业务规则

<a id="br-app-029"></a>
### BR-APP-029：关闭生命周期与平台可用性正交

Application 的 `lifecycleStatus` 与 `platformAvailabilityStatus` 是两个不同维度。只有 lifecycle ACTIVE 可在 AVAILABLE 与 SUSPENDED 之间迁移；CLOSING/CLOSED 不可恢复。暂停不释放身份、配额或 owner 义务，关闭可以终止一个已暂停 Application。

<a id="br-app-030"></a>
### BR-APP-030：精确且独立的运维权限

Suspend 只接受 `app.application.suspend`，Restore 只接受 `app.application.restore`。两项权限互不蕴含，不由 Reviewer、Developer、Application 管理员、SYSTEM 或平台管理员身份自动取得，也不接受 permission 通配符、OAuth scope 或请求正文自报授权。

<a id="br-app-031"></a>
### BR-APP-031：权威读取的即时平台门禁

暂停提交后开始的 Catalog、启动解析、TEST descriptor、Tester Join 和 OAuth provider 权威读取必须观察 SUSPENDED 并失败，不得用进程缓存或旧查询投影延长成功。提交前已返回结果受各自 no-store、snapshot 和凭据时限约束，不能被描述为已经从客户端撤回。

<a id="br-app-032"></a>
### BR-APP-032：依附配置和 owner 义务保持不变

暂停/恢复不修改 Profile、Version、Review、Publication、Filter、Tester Membership/JoinLink、OAuth registration/credential、grant/token、adminId、ownershipRevision、lifecycleRevision、配额或 owner-exit blocker。暂停期间现有管理与审核写入口继续按原 UC 工作；Tester Join 作为新增运行资格被阻止。

<a id="br-app-033"></a>
### BR-APP-033：恢复不等于运行资格

Restore 只把平台门禁改回 AVAILABLE。恢复后所有读路径必须从当前事实重新执行既有 Profile、Version、Review、Publication、Tester、client、redirect、scope 和不变量检查；不得自动启用 client、回退历史配置、补默认值或把无有效配置伪装成可运行。

<a id="br-app-034"></a>
### BR-APP-034：OAuth 在线失效与有界残余

SUSPENDED 时 UC019 的五个 provider 方法全部失败关闭，使 authorize、code exchange、refresh、UserInfo 和 delegation 无法通过下一次在线检查。既有 App snapshot 与委托 JWS 只在既有最长约 11 秒上界内残余；已交付 ID Token、第三方 Session 或数据无法远程收回。暂停不建立 Auth 永久 tombstone，恢复后仍有效的历史 grant/token 可以重新通过当前资格检查。

<a id="br-app-035"></a>
### BR-APP-035：独立 OCC 与共享写栅栏

Application 使用正数 `platformAvailabilityRevision` 保护 suspend/restore OCC；真实变化严格增加一次。两种命令与关闭、转让及其他 Application 写操作共用 coordination fence，并在最终事务内复查 lifecycle 和两个 expected revision。普通下级配置写入可以与暂停串行提交，但不改变 availability revision；无论谁先提交，暂停后的运行读取都受门禁约束。

<a id="br-app-036"></a>
### BR-APP-036：原子审计、告警和隐私

每次真实 suspend/restore 与 append-only `ApplicationPlatformOperationEvent`、durable alert outbox 同事务提交。事件保存 eventId、applicationId、action、actorAuthId、reason、before/after status、before/after revision 和 occurredAt；不保存 USER JWS、token、secret、Tester 身份或配置正文。状态查询与 OAuth 错误不披露 actor 或 reason。

成功暂停产生一条可去重的高信号 `WARNING` 运维事件，恢复产生关联该 Application 与新 revision 的 `INFO` 事件；通知系统是否分页由外部值班策略决定。被暂停应用的普通访问只计有界 metric，不逐请求分页或打印 reason；状态损坏、revision 回退、审计缺失或门禁绕过检测属于 `ERROR/CRITICAL` 安全告警。

<a id="br-app-037"></a>
### BR-APP-037：无自动恢复与失败关闭

暂停没有 TTL，也不因进程重启、权限撤销、管理员转让、配置修复或时间流逝自动恢复。只有成功提交、持有精确 restore 权限的命令能恢复。存储故障、状态损坏、提交结果未知或不明确的身份一律失败关闭，不返回猜测状态。

## 领域与数据模型

Application 增加：

```text
platformAvailabilityStatus: AVAILABLE | SUSPENDED
platformAvailabilityRevision: int64 >= 1
lastPlatformOperationEventId?: UUIDv7
```

`ApplicationPlatformOperationEvent` 是 append-only 审计实体：

```text
eventId, applicationId,
action: SUSPEND | RESTORE,
actorAuthId, reason,
beforeStatus, afterStatus,
beforeRevision, afterRevision,
occurredAt
```

迁移为所有既有 Application 回填 AVAILABLE/revision 1，并建立 eventId 唯一、`(applicationId, occurredAt, eventId)` 审计索引。validator 要求状态与 revision 成对存在；未知枚举、缺 revision、revision 非正数、最新 event 与 Application 指针不一致均按内部不变量异常处理，不惰性补默认值。

durable alert outbox 可以复用现有 outbox 基础设施，但其投递状态不是 Application 可用性的事实来源。即使通知暂时失败，已提交的 SUSPENDED 仍立即生效；worker 重试不能重复业务事件。

## 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效 USER JWS | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 缺精确 suspend/restore 权限 | `APPLICATION_OPERATION_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 参数、revision 或 reason 非法 | `INVALID_APPLICATION_OPERATION_REQUEST` | 400 / INVALID_ARGUMENT |
| 已授权 Get/命令查不到 Application | `APPLICATION_NOT_FOUND` | 404 / NOT_FOUND |
| 状态已相同、stale revision 或并发变化 | `APPLICATION_AVAILABILITY_CONFLICT` | 409 / ABORTED |
| lifecycle 为 CLOSING/CLOSED | `APPLICATION_NOT_ACTIVE` | 409 / FAILED_PRECONDITION |
| 状态、revision、审计绑定或 schema 损坏 | `APPLICATION_OPERATION_STATE_INCONSISTENT` | 500 / INTERNAL |
| 存储故障或提交结果未知 | `APPLICATION_OPERATION_UNAVAILABLE` | 503 / UNAVAILABLE |

Catalog、runtime 和 OAuth 公网错误继续沿用各自 UC 的存在性隐藏与协议错误，不新增 `APPLICATION_SUSPENDED` 公共枚举。内部监控可按 applicationId 和 platformAvailabilityRevision 关联事件，但不能记录 reason 到高基数 metrics。

## 并发与验收场景

1. 只持有 suspend、只持有 restore、同时持有两项和均未持有的精确授权矩阵；Reviewer、管理员和未显式授权的平台管理员均不能越权。
2. AVAILABLE→SUSPENDED→AVAILABLE 正常迁移；重复命令、stale availability revision、stale lifecycle revision、提交结果未知和审计失败。
3. suspend 与 Catalog 列表/详情、UC012、UC023、Tester Join 及五个 OAuth provider 方法并发的两个胜序；事务提交后开始的新读取全部受门禁约束。
4. 暂停保留全部 Profile/Version/Publication/Filter/Tester/OAuth 数据、配额和 owner blocker；暂停期间管理员修复配置，恢复后按修复后的当前事实运行。
5. restore 后无 Stable、无公开 Profile、client DISABLED、回调为空、Tester episode 已结束、Version snapshot 损坏分别沿原 UC 得到正常不可用或 INTERNAL，不能因 AVAILABLE 绕过。
6. suspend 与转让并发；转让可完成且状态保持 SUSPENDED，新管理员没有 restore 权限时不能恢复。
7. suspend 与关闭并发；先暂停后仍可关闭，先进入 CLOSING 后 suspend/restore 均拒绝，CLOSED 永不恢复。
8. Auth authorize、exchange、refresh、UserInfo 和 delegation 在暂停前后边界的联合验收；不使用 fake provider 代替实际 App consumer。
9. provider 旧 snapshot、5 秒委托 JWS 与 1 秒 clock skew 的边界测试；超过既有约 11 秒上界后不能再凭暂停前 App 资格访问资源。
10. 成功操作只产生一条审计和一条可去重 outbox；普通暂停访问不触发告警风暴，损坏状态和门禁绕过触发安全告警。
11. 服务重启不自动恢复；权限随后被撤销、Application 管理员变化或时间流逝都不改变 SUSPENDED。
12. migration 对既有 ACTIVE/CLOSING/CLOSED Application 回填一致；未知/缺失状态拒绝启动或读写，不在请求路径修复。

## 实现依赖与启用边界

Auth 侧 [UC-AUTH-027](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 已接受并完成后端，提供两项独立权限和 App audience 投影。App 实现还需要：

- API 仓库新增 application operations package；
- Application schema migration、repository OCC、审计/outbox；
- USER JWS permission allowlist 增加两项精确值；
- UC012/019/023/024 和 UC009 Join 的共同 availability gate；
- UC-AUTH-014 至 019 的真实跨服务回归，尤其是 refresh、UserInfo 和 delegation；
- 部署显式启用的 `APP_CENTER_APPLICATION_OPERATIONS_ENABLED`，默认 false。关闭端点开关不得让已保存 SUSPENDED 记录失效；只要数据库存在 SUSPENDED，所有读路径和 worker 仍必须执行门禁。

本用例已接受为 App/API 后端工作包。实现应固定 API 字段号与路由，复用或建立 durable alert outbox，并以真实 Auth/App 联合测试验证 OAuth 在线门禁；业务状态、权限和残余窗口不再依赖新的产品决策。

## 变更记录

- 2026-10-06：建立首版提案；采用独立平台可用状态和 revision、精确 suspend/restore 权限、暂停期间保留配置并允许修复、恢复后重新执行现有资格、OAuth 在线失败和约 11 秒委托残余边界。
- 2026-10-06：接受 App/API 后端工作包并开始实现；保持端点默认关闭，要求真实 Mongo 和 Auth/App 联合验收。
