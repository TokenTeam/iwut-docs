<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-033 --spec tools/brief-specs/UC-APP-033.json -->
# Brief — UC-APP-033：归档与重新上线 Application

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-033` 归档与重新上线 Application |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-051`–`BR-APP-058`（8 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/app-oauth-client-v1.md`、`platform/contracts/oauth-delegation-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

### 设计结论

> Application 当前管理员可以把一个仍处于活动生命周期的 Application 归档，使它退出所有 Catalog、启动解析、Tester 新增加入和 OAuth 在线资格判断；之后可以取消归档。归档保留全部业务配置、当前管理员、配额与 owner 义务，取消归档只解除门禁，各消费路径必须按届时的当前事实重新判断是否可用。

这个能力只有在“归档”表示**管理员控制的整 Application 离线门禁**时才值得实现。

如果产品需求只是让 Application 从普通公开 Catalog 消失，则不应接受本用例：管理员清空各 RPC API major 的 Stable 槽位后，UC-APP-024 已不会返回该 Application；新增另一套只影响 Catalog 的隐藏状态会与 Publication 重复建模，并制造“已隐藏但 Stable 仍发布”之类的歧义。

本用例因此明确采用更强语义。归档统一阻止普通与未来 test-only Catalog、TEST/GREY/STABLE 启动解析、Tester 新增加入，以及 UC-APP-019 的全部 OAuth provider 在线资格；它不等价于清空任何发布槽位，也不等价于平台暂停或不可逆关闭。

### 目标与范围

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

### 参与者与授权

- **归档操作人**：可信身份为 `accountStatus=ACTIVE` 的 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **取消归档操作人**：条件相同；不允许旧管理员、Reviewer、Tester、SYSTEM 或仅持平台运维权限的人员代替当前管理员执行。
- **App Center**：唯一保存 Application 归档状态、revision 和业务审计；Auth Center 不复制 applicationId 级归档状态。

调用者不需要当前仍是 APPROVED Developer。Developer 资格下降不会自动终止其既有管理义务，也不能把 Application 永久困在 ARCHIVED。身份只来自 Gateway 验证后的、audience=`iwut-app-center` 的可信 USER JWS；OAuth access token、service JWS、请求正文自报 adminId 或历史查询结果都不能授权本用例。

未授权调用者在读取 Application 当前状态前失败；不存在与当前调用者不是管理员统一隐藏为 NOT_FOUND，不能借状态差异枚举 Application。

### 输入、输出与 API 草图

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

### 正交状态模型

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

### 归档流程

1. 严格校验可信 USER 身份、applicationId 和 expectedArchiveRevision。
2. 读取 Application；不存在与调用者不是当前管理员统一返回 NOT_FOUND。
3. 开启本地事务并取得 Application coordination fence。
4. 在事务内复查调用者仍是当前 `adminId`、lifecycleStatus=`ACTIVE`、archiveRevision 与 expected 值一致。
5. 若已为 ARCHIVED，则作为精确目标状态 no-op 返回当前资源，不增加 revision、不写事件。
6. 否则从 App Clock 取得 occurredAt，写入 ARCHIVED、严格增加一次 archiveRevision，并原子追加 `ApplicationArchiveEvent(action=ARCHIVE)`。
7. 提交成功后返回状态资源；提交结果未知时返回不可用，调用方通过 Get 读取权威状态，不用新 revision 盲目重放。

归档不遍历或改写依附记录。它在 Application 级统一门禁处阻止在线资格，避免取消归档时猜测哪些 Publication、client 或 Membership 是管理员原本主动禁用或清空的。

### 取消归档流程

1. 执行与归档相同的身份、当前管理员、ACTIVE lifecycle、expected revision 和共享写栅栏检查。
2. 若已为 UNARCHIVED，则作为精确目标状态 no-op 返回当前资源，不增加 revision、不写事件。
3. 否则写入 UNARCHIVED、严格增加一次 archiveRevision，并原子追加 `ApplicationArchiveEvent(action=UNARCHIVE)`。
4. 返回当前状态资源。之后的 Catalog、启动解析、Tester Join 和 OAuth provider 必须读取最新事实，并继续执行各自已有资格与不变量检查。

取消归档只解除管理员门禁，不产生“Application 已重新上线”的强保证。若平台仍为 SUSPENDED、没有兼容 Stable/Test/Grey、公开 Profile 缺失、Version snapshot 损坏、Tester 资格不足、client 已 DISABLED、redirect 为空或 OAuth 状态不一致，对应路径仍按原 UC 返回不可用或内部不变量异常；取消归档不得写默认值、回退历史版本、自动启用 client 或绕过审核。

“重新上线”表示原有且当前仍有效的配置重新取得被求值的机会，不表示恢复成归档瞬间的历史快照。

### ARCHIVED 期间的行为

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

### OAuth 在线检查与残余窗口

UC-APP-019 的 `GetClientConfiguration`、`VerifyClientSecret`、`ResolveClientRuntimeConfiguration`、`ResolveAuthorizationContext` 和 `GetApplicationPublishedRedirects` 都必须在一致 snapshot 中要求 archiveStatus=`UNARCHIVED`。ARCHIVED 是正常业务门禁，不改写 registration/client 状态；provider 对 Auth 使用统一应用不可用分类，不能向 OAuth 客户端披露归档状态、管理员或事件信息。

归档沿用 UC-APP-028 已定义的在线失效边界：

- 新 authorize/consent、authorization code exchange、refresh、UserInfo 和 opaque access token 在线 delegation 在各自下一次 App provider 复查点失败；Auth 不得用旧 runtime tuple 或 provider 故障降级成功。
- 归档前已经返回的 App snapshot 只可使用到既有 `validUntil`，当前最长为 observedAt＋5 秒；Auth 不能延长。
- 归档后不再签发新的短期委托 JWS；归档前已签发 JWS 最长 5 秒并允许 1 秒时钟差。结合 snapshot，既有契约给出的配置变化到最后一个旧委托可接受上界约为 11 秒。
- opaque access token 与 refresh token 可以继续作为历史记录存在。取消归档后，只有仍未过期、未撤销且满足当前 grant/client/channel/version/scope 条件的凭据才可重新通过在线检查。
- 已交付 ID Token、第三方 Session、页面或数据无法由 App Center 远程收回。需要永久撤销时使用 UC-APP-027，而不是归档。

### 领域与数据模型

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

### 错误语义

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

### 并发与验收场景

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

### 实现依赖与交付边界

若本提案被接受，实现至少需要：

- `iwut-app-center`：Application 领域字段、ApplicationArchiveEvent、共享 coordination fence、UseCase、Mongo repository/事务/validator、迁移 `0026_application_archival`、HTTP/gRPC transport 和 composition wiring。
- `iwut-app-center-api`：新增独立 `app_center.v1.application_archival` package 和生成代码，不把写命令塞入既有创建或管理查询 service。
- 既有消费者：UC012/023/024、Tester Join、未来 test-only Catalog 与 UC019 五个 provider 在一致 snapshot 中统一消费 archive gate；UC029 增加私有状态和筛选。
- 测试：domain/usecase、race、真实 MongoDB replica-set transaction、transport contract、consumer 回归与 App↔Auth 联合 OAuth 验收；运行 `make check` 与 `make check-auth-app`。

本用例不要求 Auth Center 新增归档 API、application tombstone 或持久复制字段。若实现发现五个 provider 或 Catalog/Resolver 各自拼接门禁，应该先抽取共享的 Application 在线资格判定，避免 archive 与 suspension 在消费者间漂移。

## 业务规则（UC-APP-033 权威正文）

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-051 -->
### BR-APP-051：归档、平台暂停与关闭分离

`archiveStatus`、`platformAvailabilityStatus` 与 `lifecycleStatus` 是三个不同维度。归档由当前管理员控制且可恢复，平台暂停由独立运维权限控制且可恢复，关闭是不可逆终止。三者不得共用字段、权限或命令，也不得互相隐式解除。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-052 -->
### BR-APP-052：当前管理员与 ACTIVE 前置

只有可信 USER 的 authId 等于 Application 最终事务内的当前 adminId，且 lifecycle 为 ACTIVE 时，才可归档或取消归档。Developer 资格下降不撤销既有管理员的处置能力；不存在与非管理员统一隐藏。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-053 -->
### BR-APP-053：整 Application 在线门禁

ARCHIVED 提交后开始的普通与 test-only Catalog、启动解析、TEST descriptor、Tester Join 和 UC019 五个 OAuth provider 权威读取必须失败关闭。共同在线前提还要求 lifecycle ACTIVE 且平台 AVAILABLE；任何一个门禁关闭都不能被另一个操作越过。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-054 -->
### BR-APP-054：配置、配额与 owner 义务保留

归档/取消归档不修改 Profile、Version、Review、Publication、Filter、Tester Membership/JoinLink、OAuth registration/credential、grant/token、adminId、ownershipRevision、lifecycleRevision、platformAvailabilityRevision、技术名称、配额或 owner-exit blocker。归档期间管理与审核入口继续按原 UC 工作，Tester Join 作为新增运行资格被阻止。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-055 -->
### BR-APP-055：重新上线必须重新求值

Unarchive 只把管理员门禁改回 UNARCHIVED。之后所有读路径必须从当前事实重新执行既有 Profile、Version、Review、Publication、Tester、platform availability、client、redirect、scope 和不变量检查；不得恢复历史快照、自动启用 client、补默认值或把无有效配置伪装成可运行。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-056 -->
### BR-APP-056：独立 OCC、no-op 与共享写栅栏

Application 使用正数 `archiveRevision` 保护 archive/unarchive OCC；真实变化严格增加一次，expected revision 匹配且已是目标状态时为不写事件的 no-op。两种命令与关闭、转让、平台暂停及其他 Application 写操作共用 coordination fence，并在最终事务内复查 adminId、lifecycle 和 expected revision。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-057 -->
### BR-APP-057：原子审计与有界残余

每次真实 archive/unarchive 与 append-only `ApplicationArchiveEvent` 同事务提交。事件只保存 eventId、applicationId、action、actorAuthId、before/after status、before/after revision 和 occurredAt。归档后的权威读取立即失败；归档前已返回 App snapshot 与短期委托只在 UC028 已定义的最长约 11 秒边界内残余，已交付第三方会话或数据不在可撤回范围。

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-058 -->
### BR-APP-058：管理可见性与最小披露

ARCHIVED Application 不得从当前管理员的 UC029 默认列表或详情消失，且管理读取必须返回 archiveStatus/archiveRevision 供后续命令 OCC 使用。公开和 OAuth 错误不披露归档事实，管理响应不混入审计 actor、历史事件、OAuth secret/hash 或 Tester 身份。

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

#### Schema 与索引

collection、validator、索引和 schema revision 通过显式、版本化、可重复执行的迁移管理：

- 普通服务启动不创建、删除或修改生产索引与 validator。
- 迁移在部署前单独执行，并记录成功的 migration ID。
- 重复执行已成功迁移是安全的。
- 破坏性变更必须先有对应设计决定和恢复方案。
- 新集合从首次创建起使用明确的 validator 与命名索引。
- 集成测试验证实际索引、validator 和事务行为，而不仅测试 mapper。

具体 collection 名由对应 UC 的数据模型和实现工作包确定，不在本 ADR 中建立跨能力的统一 document 形状。

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

### `platform/contracts/app-oauth-client-v1.md`：App OAuth Client 提供方契约 v1

#### 所有权与调用方

App Center 持有 Application＋channel 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，STABLE/GREY 渠道扩展分别见 [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 与 [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md)，协议见 [OAuth OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

管理接口接受 SESSION 转换后的 [trusted identity](../../platform/contracts/trusted-identity-v1.md) USER 身份。内部接口只接受 Auth 的 [service identity](../../platform/contracts/trusted-service-identity-v1.md)，audience 固定为 `iwut-app-center`，权限来自 App Center 本地 caller registry；逐方法授权，不经过公网、HTTP 或 gRPC-Web，也不把 client secret 当服务间凭据。

#### 三种生命周期

`ApplicationOAuthRegistration` 以 `(applicationId, channel)` 唯一，字段为 applicationId、channel、publicClientId、publicStatus、publicAuthorizationEpoch、confidentialClientId、confidentialStatus、confidentialAuthorizationEpoch、registrationRevision、createdAt、updatedAt。两个 clientId 均为服务端 UUIDv4、全局唯一、永久不重用；type 由其所在 slot 确定，状态为 `ACTIVE/DISABLED`。client identity 固定归属一个 channel，不包含 rpcApiMajor、Version 或 hostname。

`OAuthClientCredential` 以 confidentialClientId 唯一，字段为 confidentialClientId、applicationId、secretDigest、credentialRevision、rotatedAt。channel 从 confidentialClientId 的 registration 确认，不能跨渠道使用。它只服务于以后 confidential client authentication；secret 轮换不改变 registrationRevision。

`ApplicationVersionOAuthConfig` 以 applicationVersionId 唯一，字段为 applicationVersionId、applicationId 和：

```text
oauthRedirects {
  pkceRedirectUris: []RedirectURI
  confidentialRedirectUris: []RedirectURI
}
```

它使用独立 collection 存储，但生命周期严格依附 ApplicationVersion：与 Version 同事务创建/编辑，使用同一个 Version revision 做 OCC，提交时深拷贝进 Review snapshot，提交后不可独立修改。两个数组均非 null、各 0–10 项、内部唯一且彼此不交叉。详细 URI 规则见 [BR-VER-018](../use-cases/UC-APP-002-create-application-version.md#br-ver-018)。

#### Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | identity 元数据（含固定 channel、registrationRevision、该 slot 的 authorizationEpoch）、tokenEndpointAuthMethod；CONFIDENTIAL 含 credentialRevision |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedCredentialRevision | verified、credentialRevision；不返回摘要 |
| `/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` | clientId、channel、rpcApiMajor、expectedRegistrationRevision | 当前批准的运行配置 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、channel、rpcApiMajor、expectedRegistrationRevision、expectedRuntimeVersion | 当前用户授权上下文 |
| `/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` | applicationId | PublishedRedirectSnapshot |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。permission 只授予指定 Auth 服务主体；SYSTEM、USER 和第三方 access token 均不能调用。Verify 对未知 client、错误 secret、PUBLIC、DISABLED 或 credential revision 不一致返回 `verified=false`。原 secret 只经 TLS 内网发送，拦截器和代理禁止记录 metadata/body。

`RuntimeConfiguration` 包含 clientId、applicationId、type、channel、rpcApiMajor、registrationRevision、authorizationEpoch、adminAuthId、versionId、publicationRevision、redirectUris、requiredScopes、optionalScopes、display、observedAt、validUntil。

`ApplicationDisplay` 包含 profileRevisionId、displayName、可空 description 和可空 icon。全部内容来自 `currentPublishedProfileRevisionId` 指向的同一 Application、APPROVED ProfileRevision；不提供 Application 技术名称 fallback，也不返回 HTML。运行 tuple 中的 profileRevisionId 即 `display.profileRevisionId`，不在 RuntimeConfiguration 顶层重复保存。

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和可空 testerMembershipId。TEST 必须返回当前 ACTIVE Tester episode；STABLE/GREY 为空。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, profileRevisionId, adminAuthId)`；expectedRegistrationRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置、当前公开资料和渠道用户资格。

redirectUris 来自批准 snapshot：PUBLIC 读取 pkceRedirectUris，CONFIDENTIAL 读取 confidentialRedirectUris；对应数组必须非空。requiredScopes/optionalScopes 来自同一 snapshot，不按 App 的 requestable 缓存过滤；Auth 根据 [Scope Catalog 契约](../../platform/contracts/auth-scope-catalog-v1.md) 对应的当前权威 enabled 和 OAuth UC 执行最终授权。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记；channel 必须与 client 登记值完全相等，rpcApiMajor 只选择该渠道的权威 Publication；TEST/GREY/STABLE client 不能互相替代。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。登录前后 registrationRevision 和 runtime tuple 必须一致；Profile 批准后当前公开指针发生变化也必须重新开始或重新展示。credentialRevision 只约束一次 secret 验证，不进入 runtime tuple。

Grant 按 [UC-AUTH-014 / BR-OAU-002](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 的 `(authId, applicationId, channel)` 业务主键保存，同应用同渠道的两类 client 及各 major 共享历史同意。App 提供可信的 client→applicationId/channel 归属，不管理 grant；Auth 不能从前端自报值推导共享范围。授权交互和 code 绑定精确 runtime tuple、redirect URI 和 scope；access/refresh 绑定不可变 channel/rpcApiMajor、authorizationEpoch、Tester episode。Version ID 只用于审计，后续在 token 原来的 major 上重新解析当前版本，不能由资源请求改选 major。Auth 保留历史同意集合，按当前有效交集决定权限；具体规则只由 UC-AUTH-014/016/018/019 定义。

#### 资格变化与失败

client 不可用、对应回调数组为空、无 exact-major 渠道 Publication、无当前已批准公开资料或批准记录不一致均不可授权；TEST 还要求 ACTIVE Tester，GREY 还要求可信 authId 命中当前 rollout cohort。设计支持 channel=`TEST/GREY/STABLE`；GREY 随 UC-APP-021 工作包交付。正常缺少运行资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因；公开资料指针存在但目标缺失、跨应用、非 APPROVED 或内容损坏返回 `INTERNAL`。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照或 Application 技术名称兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。

#### 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认和 code 兑换重新解析用户上下文。refresh、UserInfo 和每次委托签发按 OAuth/OIDC v1 的当前资格规则验证。confidential secret 只在 token/revoke 操作验证。

双方至少测试：每种 type 的 clientId 稳定；metadata 无 redirect/secret；一次 secret 返回；registration 与 credential revision 并发隔离；跨应用管理员；runtime tuple 混合；同 clientId 跨 Version/major 选择；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；公开资料切换和损坏指针；hostname 迁移；快照过期；服务 permission；Auth→App 故障时零签发。

### `platform/contracts/oauth-delegation-v1.md`：OAuth 委托上下文与 Traefik 契约 v1

#### 链路与身份隔离

```text
应用 ─ Bearer access token → Traefik
  HTTP：ForwardAuth → Gateway → Auth 在线校验 + 签发委托 JWS
        Traefik 复制委托 JWS → 固定 Router → 资源服务验签与业务授权
  gRPC：Traefik → Gateway 精确 unary 代理 → Auth → 资源服务
  gRPC-Web：Traefik 协议转换 → 同一 unary 代理
```

Traefik 阶段完成入口检查，但 token 真伪、grant、scope 的权威判断仍由 Auth 完成。随机 access token 不可本地验签；Traefik 不持有 Auth 私钥，也不查询 Mongo。不开 Redis，不缓存 token 校验结果或签发结果。

委托上下文使用 `x-iwut-delegation`，与 SESSION 的 [x-iwut-identity](../../platform/contracts/trusted-identity-v1.md) 分离。ID Token、平台 Session、service JWS 不可作为 OAuth Bearer token。第三方应用不能通过 OAuth scope 获得原有 developer/reviewer/管理员 USER 身份；管理端原有 SESSION 路由继续只接受平台 Session。

规则归属：[UC-AUTH-019](../../auth-center/use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-GW-002](../../gateway/use-cases/UC-GW-002-authenticate-oauth-and-forward.md)。本契约与 [ADR-GW-001](../../gateway/adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) 配合，保留其固定 Traefik 版本和三协议适配方式。

#### 委托 JWS

单个 compact JWS、不带 Bearer，大小至多 8 KiB。RS256、独立用途的签名 key/kid；header `typ=iwut-delegation+jwt`，不与公开 OIDC JWKS 或 USER/service 验证器共享可接受密钥集。

| claim | 语义 |
| --- | --- |
| iss、aud | 配置的 Auth issuer、单个目标资源 audience |
| sub | 内部 authId，只在平台内网下游使用，不向应用返回 |
| client_id、application_id | 已认证 token 所属 client 和应用 |
| grant_id、grant_revision、grant_revocation_epoch | 按用户、应用及渠道共享的授权引用、审计 revision 与撤销 epoch；同渠道不同 client 可携带相同 grant_id |
| channel、rpc_api_major、client_authorization_epoch | token 固定运行上下文及 client 状态 epoch |
| scopes | UC-AUTH-019 计算的有效交集 E；不包含当前版本未允许的历史同意或 token 外的新增 scope |
| route_id、policy_digest、protocol、method | 绑定本次路由/策略/协议/操作 |
| target_path | HTTP 重写后的 escaped path；gRPC 不出现 |
| iat、nbf、exp、jti | 签发时间、当前有效、最长 5 秒、独立随机 ID |

exp 不晚于 access token 到期时间。无 permissions、developer_status、email、学校关联值、平台 Session 或 token 原文。Auth 检查 token 对本 audience 的许可；token 的 audience 集合由已授予 scope 的受信映射产生，客户端不能自报。

client_id 始终为本次 access token 所属 client，不因 grant 共享而替换；Auth 按 [BR-OAU-018](../../auth-center/use-cases/UC-AUTH-019-issue-delegation-context.md#br-oau-018) 验证 token、grant 和 App client 归属一致。

资源服务必须验证签名、固定算法/typ/kid/issuer/audience、时限和本次 method/route/policy/target_path，再以 sub 做数据归属检查，以 client_id/application_id/channel 做应用环境约束。route policy 显式配置非空 allowedChannels，允许 TEST/GREY/STABLE 的唯一子集；未知或重复项拒绝。仅限正式渠道的路由拒绝 TEST token；允许多个渠道的共享资源仍分别检查各自 grant/E，不能因为 OIDC sub 相同绕过渠道许可。可验证委托 JWS 不等于全部业务许可。不得把委托转换成通用 USER 管理身份。只在配置明确启用的 OAuth 方法接受该 header，未知入口拒绝。

HTTP path 必须经过路由生成器规定的单次解析和固定重写；拒绝非法 percent encoding、编码斜线/反斜线、dot segment 和无法唯一匹配的路径。Gateway 签发请求与后端收到的 escaped path 必须字节相等；查询参数不作为路径签名的一部分，业务仍验证其中的资源 ID/过滤条件，不能把 query 当授权范围来源。

#### 撤销与时钟边界

Auth 本地 grant/token 撤销与最终签发共用原子栅栏：撤销提交后开始的新检查不得再成功。已签发的委托 JWS 最长 5 秒，资源服务只允许 1 秒时钟容差；部署必须监测时钟偏移，超界停止签发。

App 使用最长 5 秒的单次快照，Auth 只在快照未过期时完成本次决策；它不是跨库锁或永久租约。故 App 配置/资格变化到最后一个旧委托可被接受的上界为约 11 秒（快照 5 秒 + JWS 5 秒 + 时钟差 1 秒）。Auth 本地撤回的上界为约 6 秒。已开始的业务操作不回滚，长任务/流式 RPC 不在首版范围，不能声称全链路即时撤回。

token 校验不依赖原登录 Session 继续存在；用户退出平台 Session 不隐式撤回第三方 grant。账号不可用、grant/refresh family 撤销、client/config/资格变化按相关 UC 拒绝；第三方自己的登录会话、已下载数据不由此自动删除。

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

- `UC-APP-033`（use-cases/UC-APP-033-archive-and-unarchive-application.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/app-oauth-client-v1.md`（docs 根级共享文档）：管理接口、Sector 的只读配置来源、STABLE 扩展、GREY 扩展
- `platform/contracts/oauth-delegation-v1.md`（docs 根级共享文档）：Auth 签发 RPC、Traefik HTTP 契约、错误与协议适配、验收与启用门禁
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-033-archive-and-unarchive-application.md` | 283 | `e9e406a93d2d` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/oauth-delegation-v1.md` | 97 | `1f431b468864` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
