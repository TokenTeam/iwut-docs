# UC-APP-033：归档与重新上线 Application

状态：`ACCEPTED`

## 设计结论

> Application 当前管理员可以把一个仍处于活动生命周期的 Application 归档，使它退出所有 Catalog、启动解析、Tester 新增加入和 OAuth 在线资格判断；之后可以取消归档。归档保留全部业务配置、当前管理员、配额与 owner 义务，取消归档只解除门禁，各消费路径必须按届时的当前事实重新判断是否可用。

这个能力只有在“归档”表示**管理员控制的整 Application 离线门禁**时才值得实现。

如果产品需求只是让 Application 从普通公开 Catalog 消失，则不应接受本用例：管理员清空各 RPC API major 的 Stable 槽位后，UC-APP-024 已不会返回该 Application；新增另一套只影响 Catalog 的隐藏状态会与 Publication 重复建模，并制造“已隐藏但 Stable 仍发布”之类的歧义。

本用例因此明确采用更强语义。归档统一阻止普通与未来 test-only Catalog、TEST/GREY/STABLE 启动解析、Tester 新增加入，以及 UC-APP-019 的全部 OAuth provider 在线资格；它不等价于清空任何发布槽位，也不等价于平台暂停或不可逆关闭。

## 目标与范围

本用例负责：

- 为 Application 增加与关闭生命周期、平台可用性正交的 `archiveStatus=UNARCHIVED | ARCHIVED` 及独立 revision。
- 允许当前管理员归档和取消归档自己的 ACTIVE Application，不要求平台运维权限或近期认证。
- 在 App Center 本地事务内原子改变归档状态并保存不可变业务审计。
- 让 Catalog、统一启动解析、TEST descriptor、Tester Join 和五个 OAuth provider 方法消费同一个管理员归档门禁。
- 保证归档 Application 始终保留在管理员私有查询中，并可继续修复 Version、Profile、Publication、Filter、Tester 与 OAuth 配置。
- 明确归档与平台暂停、管理权转让、关闭及既有 OAuth snapshot/凭据的组合语义。

本用例不负责：

- 只隐藏某一个 Catalog 条目、清空 Test/Stable/Grey 槽位、调整 Grey rollout 或撤销已批准 Version。
- 平台紧急处置；平台操作人继续使用 UC-APP-028 的独立 suspend/restore 权限与审计。
- 修改、删除或回滚 Profile、Version、Review、Publication、Filter、Tester Membership/JoinLink、OAuth registration/credential、grant 或 token。
- 因归档释放配额、技术名称或 owner-exit blocker；归档不能帮助 Developer 退出或注销账号。
- 自动归档、定时恢复、批量操作、归档目录、回收站、可靠通知或从第三方设备撤回已返回的数据与本地会话。
- 为管理员隐藏 Application；“归档”是对外离线，不是从 Developer Console 中消失。

## 参与者与授权

- **归档操作人**：可信身份为 `accountStatus=ACTIVE` 的 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **取消归档操作人**：条件相同；不允许旧管理员、Reviewer、Tester、SYSTEM 或仅持平台运维权限的人员代替当前管理员执行。
- **App Center**：唯一保存 Application 归档状态、revision 和业务审计；Auth Center 不复制 applicationId 级归档状态。

调用者不需要当前仍是 APPROVED Developer。Developer 资格下降不会自动终止其既有管理义务，也不能把 Application 永久困在 ARCHIVED。身份只来自 Gateway 验证后的、audience=`iwut-app-center` 的可信 USER JWS；OAuth access token、service JWS、请求正文自报 adminId 或历史查询结果都不能授权本用例。

未授权调用者在读取 Application 当前状态前失败；不存在与当前调用者不是管理员统一隐藏为 NOT_FOUND，不能借状态差异枚举 Application。

## 输入、输出与 API 草图

读取资源：

```text
ApplicationArchiveState {
  applicationId
  lifecycleStatus: ACTIVE | CLOSING | CLOSED
  platformAvailabilityStatus: AVAILABLE | SUSPENDED
  archiveStatus: UNARCHIVED | ARCHIVED
  archiveRevision: int64
}
```

普通管理员状态读取不返回历史管理员、平台暂停原因、审计 actor 或依附配置正文。完整事件历史属于未来受控审计查询。

写命令：

```text
ArchiveApplicationCommand {
  applicationId: ApplicationId
  expectedArchiveRevision: int64
}

UnarchiveApplicationCommand {
  applicationId: ApplicationId
  expectedArchiveRevision: int64
}
```

`expectedArchiveRevision` 必须为正数。请求不能携带 actorAuthId、adminId、目标状态、lifecycle 或 platform availability；这些值均由服务端权威读取。

建议独立 package `app_center.v1.application_archival`，service 为 `ApplicationArchivalService`：

| 方法 | HTTP | 成功响应 |
| --- | --- | --- |
| `GetApplicationArchiveState` | `GET /v1/applications/{application_id}/archive-state` | 当前归档状态资源 |
| `ArchiveApplication` | `POST /v1/applications/{application_id}:archive` | 变化后或已处于目标状态的当前资源 |
| `UnarchiveApplication` | `POST /v1/applications/{application_id}:unarchive` | 变化后或已处于目标状态的当前资源 |

三种方法同时提供 HTTP/JSON 与原生 gRPC，响应使用 `Cache-Control: private, no-store`。命令不要求用户输入 reason；审计记录操作人、动作、前后状态/revision 和服务端时间，避免把可能含隐私或敏感内容的自由文本引入核心状态。

## 正交状态模型

```text
Application lifecycle                Owner archive state

ACTIVE ── close ──► CLOSING ─► CLOSED   UNARCHIVED ◄── unarchive ── ARCHIVED
   │                                         │                       ▲
   └─ archive/unarchive only here            └────── archive ────────┘

Platform availability

AVAILABLE ◄── restore ── SUSPENDED
```

- `lifecycleStatus` 继续只表达 `ACTIVE/CLOSING/CLOSED`，由 UC-APP-027 拥有。
- `platformAvailabilityStatus` 继续只表达平台运维门禁，由 UC-APP-028 拥有。
- `archiveStatus` 只表达当前管理员选择的整 Application 对外在线门禁。新建和既有 Application 均为 `UNARCHIVED`、revision 1。
- 只有 lifecycle=`ACTIVE` 时可以 archive 或 unarchive。CLOSING/CLOSED 即使保存历史 ARCHIVED 值也没有恢复入口。
- 平台暂停与管理员归档互不改写。平台 restore 不会取消归档；管理员 unarchive 也不能越过 SUSPENDED。
- 关闭可以从任意 archive/platform availability 组合发起；进入 CLOSING 后关闭规则优先，归档状态只作为历史事实保留。

一个 Application 参与在线分发和授权判断的共同前提是：

```text
lifecycleStatus == ACTIVE
&& archiveStatus == UNARCHIVED
&& platformAvailabilityStatus == AVAILABLE
```

满足共同前提只表示可以继续执行下级资格检查，不保证存在可运行 Version、已发布 Profile、Publication、Tester 资格或启用的 OAuth client。

## 归档流程

1. 严格校验可信 USER 身份、applicationId 和 expectedArchiveRevision。
2. 读取 Application；不存在与调用者不是当前管理员统一返回 NOT_FOUND。
3. 开启本地事务并取得 Application coordination fence。
4. 在事务内复查调用者仍是当前 `adminId`、lifecycleStatus=`ACTIVE`、archiveRevision 与 expected 值一致。
5. 若已为 ARCHIVED，则作为精确目标状态 no-op 返回当前资源，不增加 revision、不写事件。
6. 否则从 App Clock 取得 occurredAt，写入 ARCHIVED、严格增加一次 archiveRevision，并原子追加 `ApplicationArchiveEvent(action=ARCHIVE)`。
7. 提交成功后返回状态资源；提交结果未知时返回不可用，调用方通过 Get 读取权威状态，不用新 revision 盲目重放。

归档不遍历或改写依附记录。它在 Application 级统一门禁处阻止在线资格，避免取消归档时猜测哪些 Publication、client 或 Membership 是管理员原本主动禁用或清空的。

## 取消归档流程

1. 执行与归档相同的身份、当前管理员、ACTIVE lifecycle、expected revision 和共享写栅栏检查。
2. 若已为 UNARCHIVED，则作为精确目标状态 no-op 返回当前资源，不增加 revision、不写事件。
3. 否则写入 UNARCHIVED、严格增加一次 archiveRevision，并原子追加 `ApplicationArchiveEvent(action=UNARCHIVE)`。
4. 返回当前状态资源。之后的 Catalog、启动解析、Tester Join 和 OAuth provider 必须读取最新事实，并继续执行各自已有资格与不变量检查。

取消归档只解除管理员门禁，不产生“Application 已重新上线”的强保证。若平台仍为 SUSPENDED、没有兼容 Stable/Test/Grey、公开 Profile 缺失、Version snapshot 损坏、Tester 资格不足、client 已 DISABLED、redirect 为空或 OAuth 状态不一致，对应路径仍按原 UC 返回不可用或内部不变量异常；取消归档不得写默认值、回退历史版本、自动启用 client 或绕过审核。

“重新上线”表示原有且当前仍有效的配置重新取得被求值的机会，不表示恢复成归档瞬间的历史快照。

## ARCHIVED 期间的行为

| 能力 | ARCHIVED 行为 |
| --- | --- |
| UC024 普通 Catalog 列表/详情 | 列表排除；详情沿用普通候选统一 NOT_FOUND，不披露归档事实 |
| 未来 test-only Catalog | 列表排除；不能借 Tester 身份发现归档 Application |
| UC023 统一启动解析 | 不返回 TEST/GREY/STABLE 目标；沿用统一目标不可用语义 |
| UC012 TEST descriptor | 不返回启动目标 |
| UC009 Tester Join | 不创建新 Membership；现有 Membership、容量计数和链接原样保留 |
| UC019 五个 Auth provider 方法 | 全部失败关闭，不返回可继续使用的 client/runtime/secret 验证/redirect snapshot |
| Profile、Version、Review、Publication、Filter、Tester 管理、OAuth registration/credential 管理 | 继续按原管理员、Reviewer、revision 和 ACTIVE lifecycle 规则工作，使管理员可以修复再上线 |
| UC029 管理列表与详情 | 始终可见并明确返回 archiveStatus/archiveRevision；默认列表不能因 ARCHIVED 排除 |
| 管理权转让 | 可以继续；归档状态不变，接受转让后的新管理员取得取消归档权限 |
| 平台暂停/恢复 | 可以继续；两种门禁独立，只有二者均解除才可继续在线资格检查 |
| 不可逆关闭 | 可以继续；进入 CLOSING 后 UC027 规则优先且不能取消归档 |
| owner-exit / quota / 技术名称 | 仍视为当前管理员拥有 Application；不释放配额、名称或 blocker |

归档事务提交后开始的 App Center 权威读取不得产生新的目录项、启动描述、Tester Membership 或 OAuth provider 成功结果。事务提交前已经返回的数据无法撤回；Catalog 响应继续 `private, no-store`，启动解析不得建立长期租约或服务端资格缓存。

## OAuth 在线检查与残余窗口

UC-APP-019 的 `GetClientConfiguration`、`VerifyClientSecret`、`ResolveClientRuntimeConfiguration`、`ResolveAuthorizationContext` 和 `GetApplicationPublishedRedirects` 都必须在一致 snapshot 中要求 archiveStatus=`UNARCHIVED`。ARCHIVED 是正常业务门禁，不改写 registration/client 状态；provider 对 Auth 使用统一应用不可用分类，不能向 OAuth 客户端披露归档状态、管理员或事件信息。

归档沿用 UC-APP-028 已定义的在线失效边界：

- 新 authorize/consent、authorization code exchange、refresh、UserInfo 和 opaque access token 在线 delegation 在各自下一次 App provider 复查点失败；Auth 不得用旧 runtime tuple 或 provider 故障降级成功。
- 归档前已经返回的 App snapshot 只可使用到既有 `validUntil`，当前最长为 observedAt＋5 秒；Auth 不能延长。
- 归档后不再签发新的短期委托 JWS；归档前已签发 JWS 最长 5 秒并允许 1 秒时钟差。结合 snapshot，既有契约给出的配置变化到最后一个旧委托可接受上界约为 11 秒。
- opaque access token 与 refresh token 可以继续作为历史记录存在。取消归档后，只有仍未过期、未撤销且满足当前 grant/client/channel/version/scope 条件的凭据才可重新通过在线检查。
- 已交付 ID Token、第三方 Session、页面或数据无法由 App Center 远程收回。需要永久撤销时使用 UC-APP-027，而不是归档。

## 业务规则

<a id="br-app-051"></a>
### BR-APP-051：归档、平台暂停与关闭分离

`archiveStatus`、`platformAvailabilityStatus` 与 `lifecycleStatus` 是三个不同维度。归档由当前管理员控制且可恢复，平台暂停由独立运维权限控制且可恢复，关闭是不可逆终止。三者不得共用字段、权限或命令，也不得互相隐式解除。

<a id="br-app-052"></a>
### BR-APP-052：当前管理员与 ACTIVE 前置

只有可信 USER 的 authId 等于 Application 最终事务内的当前 adminId，且 lifecycle 为 ACTIVE 时，才可归档或取消归档。Developer 资格下降不撤销既有管理员的处置能力；不存在与非管理员统一隐藏。

<a id="br-app-053"></a>
### BR-APP-053：整 Application 在线门禁

ARCHIVED 提交后开始的普通与 test-only Catalog、启动解析、TEST descriptor、Tester Join 和 UC019 五个 OAuth provider 权威读取必须失败关闭。共同在线前提还要求 lifecycle ACTIVE 且平台 AVAILABLE；任何一个门禁关闭都不能被另一个操作越过。

<a id="br-app-054"></a>
### BR-APP-054：配置、配额与 owner 义务保留

归档/取消归档不修改 Profile、Version、Review、Publication、Filter、Tester Membership/JoinLink、OAuth registration/credential、grant/token、adminId、ownershipRevision、lifecycleRevision、platformAvailabilityRevision、技术名称、配额或 owner-exit blocker。归档期间管理与审核入口继续按原 UC 工作，Tester Join 作为新增运行资格被阻止。

<a id="br-app-055"></a>
### BR-APP-055：重新上线必须重新求值

Unarchive 只把管理员门禁改回 UNARCHIVED。之后所有读路径必须从当前事实重新执行既有 Profile、Version、Review、Publication、Tester、platform availability、client、redirect、scope 和不变量检查；不得恢复历史快照、自动启用 client、补默认值或把无有效配置伪装成可运行。

<a id="br-app-056"></a>
### BR-APP-056：独立 OCC、no-op 与共享写栅栏

Application 使用正数 `archiveRevision` 保护 archive/unarchive OCC；真实变化严格增加一次，expected revision 匹配且已是目标状态时为不写事件的 no-op。两种命令与关闭、转让、平台暂停及其他 Application 写操作共用 coordination fence，并在最终事务内复查 adminId、lifecycle 和 expected revision。

<a id="br-app-057"></a>
### BR-APP-057：原子审计与有界残余

每次真实 archive/unarchive 与 append-only `ApplicationArchiveEvent` 同事务提交。事件只保存 eventId、applicationId、action、actorAuthId、before/after status、before/after revision 和 occurredAt。归档后的权威读取立即失败；归档前已返回 App snapshot 与短期委托只在 UC028 已定义的最长约 11 秒边界内残余，已交付第三方会话或数据不在可撤回范围。

<a id="br-app-058"></a>
### BR-APP-058：管理可见性与最小披露

ARCHIVED Application 不得从当前管理员的 UC029 默认列表或详情消失，且管理读取必须返回 archiveStatus/archiveRevision 供后续命令 OCC 使用。公开和 OAuth 错误不披露归档事实，管理响应不混入审计 actor、历史事件、OAuth secret/hash 或 Tester 身份。

## 领域与数据模型

Application 增加：

```text
archiveStatus: UNARCHIVED | ARCHIVED
archiveRevision: int64 >= 1
lastArchiveEventId?: UUIDv7
```

`ApplicationArchiveEvent` 是 append-only 审计实体：

```text
eventId, applicationId,
action: ARCHIVE | UNARCHIVE,
actorAuthId,
beforeStatus, afterStatus,
beforeRevision, afterRevision,
occurredAt
```

迁移为所有既有 Application 回填 UNARCHIVED/revision 1，并建立 eventId 唯一、`(applicationId, occurredAt, eventId)` 审计索引。validator 要求状态与 revision 成对存在；未知枚举、缺 revision、revision 非正数或最新事件指针不一致均按内部不变量异常处理，不惰性补默认值。

UC029 的列表筛选增加可选 `archiveStatuses?: UNARCHIVED | ARCHIVED []`，空值不限制归档状态；默认 ACTIVE/CLOSING 列表必须同时包含两种 archiveStatus。`OwnedApplicationCore` 和详情中的 Application 核心状态增加 archiveStatus/archiveRevision，不返回 lastArchiveEventId。

## 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效 USER JWS | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| Application 不存在或调用者不是当前管理员 | `APPLICATION_ARCHIVE_NOT_FOUND` | 404 / NOT_FOUND |
| applicationId 或 expected revision 非法 | `INVALID_APPLICATION_ARCHIVE_REQUEST` | 400 / INVALID_ARGUMENT |
| stale revision 或并发变化 | `APPLICATION_ARCHIVE_CONFLICT` | 409 / ABORTED |
| lifecycle 为 CLOSING/CLOSED | `APPLICATION_NOT_ACTIVE` | 409 / FAILED_PRECONDITION |
| 状态、revision、事件绑定或 schema 损坏 | `APPLICATION_ARCHIVE_STATE_INCONSISTENT` | 500 / INTERNAL |
| 存储故障或提交结果未知 | `APPLICATION_ARCHIVE_UNAVAILABLE` | 503 / UNAVAILABLE |

精确目标状态且 expected revision 等于当前值是成功 no-op，不属于冲突。公开 Catalog、runtime 和 OAuth 错误继续沿用各自 UC 的存在性隐藏与协议错误，不新增 `APPLICATION_ARCHIVED` 公共枚举。

## 并发与验收场景

1. 当前管理员执行 UNARCHIVED→ARCHIVED→UNARCHIVED；每次真实变化 revision 只增加一次并产生一条匹配事件。
2. 相同 expected revision 的目标状态 no-op 不写事件；stale revision、提交结果未知和重读后安全恢复路径正确。
3. 非管理员、不存在 Application、旧管理员、Reviewer、Tester、SYSTEM 与只有平台运维权限的人员均不能操作；Developer 资格下降的当前管理员仍能处置。
4. archive 与 UC024 列表/详情、未来 test-only Catalog、UC012、UC023、Tester Join 及五个 OAuth provider 并发的两个胜序；提交后开始的新读取全部受门禁约束。
5. 归档保留全部 Profile/Version/Review/Publication/Filter/Tester/OAuth 数据、技术名称、配额和 owner blocker；归档期间管理员能修复配置。
6. unarchive 后无 Stable、无公开 Profile、client DISABLED、回调为空、Tester episode 已结束、Version snapshot 损坏分别沿原 UC 得到正常不可用或 INTERNAL，不能因 UNARCHIVED 绕过。
7. archive 与 platform suspend/restore 的所有组合；任一门禁关闭都不可在线，restore 不 unarchive，unarchive 不 restore。
8. archive 与转让并发；先转让则旧管理员失败，先归档后仍可转让，状态保持 ARCHIVED 且新管理员可以取消归档。
9. archive 与关闭并发；先归档后仍可关闭，先进入 CLOSING 后 archive/unarchive 均拒绝，CLOSED 永不重新上线。
10. UC029 默认列表始终包含 ARCHIVED，archive filter 和 cursor 条件绑定稳定；详情返回 archive revision 且不泄露事件 actor。
11. Auth authorize、exchange、refresh、UserInfo 和 delegation 在归档前后边界的联合验收；超过既有约 11 秒上界后不能再凭归档前 App 资格访问在线能力。
12. validator 拒绝缺字段、未知枚举、非正 revision、最新事件指针错误和审计原子性失败；损坏状态不能被 unarchive 修复或覆盖。
13. HTTP 与原生 gRPC 共享相同身份、OCC、no-op、错误和隐私语义；管理响应均为 private/no-store。

## 实现依赖与交付边界

若本提案被接受，实现至少需要：

- `iwut-app-center`：Application 领域字段、ApplicationArchiveEvent、共享 coordination fence、UseCase、Mongo repository/事务/validator、迁移 `0026_application_archival`、HTTP/gRPC transport 和 composition wiring。
- `iwut-app-center-api`：新增独立 `app_center.v1.application_archival` package 和生成代码，不把写命令塞入既有创建或管理查询 service。
- 既有消费者：UC012/023/024、Tester Join、未来 test-only Catalog 与 UC019 五个 provider 在一致 snapshot 中统一消费 archive gate；UC029 增加私有状态和筛选。
- 测试：domain/usecase、race、真实 MongoDB replica-set transaction、transport contract、consumer 回归与 App↔Auth 联合 OAuth 验收；运行 `make check` 与 `make check-auth-app`。

本用例不要求 Auth Center 新增归档 API、application tombstone 或持久复制字段。若实现发现五个 provider 或 Catalog/Resolver 各自拼接门禁，应该先抽取共享的 Application 在线资格判定，避免 archive 与 suspension 在消费者间漂移。

## 变更记录

- 2026-10-10：建立管理员可恢复的整 Application 离线门禁提案；明确若需求仅为 Catalog 隐藏则应否决本用例并使用 Stable clear。
- 2026-10-10：产品确认需要管理员一键让整个 Application 离线并可恢复；接受整应用门禁、配置保留和重新求值语义，进入 brief 与实现。
