<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-037 --spec tools/brief-specs/UC-APP-037.json -->
# Brief — UC-APP-037：查询 Application Tester 管理视图

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-037` 查询 Application Tester 管理视图 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-TST-037`–`BR-TST-043`（7 条） |
| 外部引用 BR | `BR-APP-010`、`BR-APP-015`、`BR-APP-039`，`BR-TST-003`、`BR-TST-004`、`BR-TST-005`、`BR-TST-012`、`BR-TST-014`、`BR-TST-016`、`BR-TST-023`、`BR-TST-031`（来自 `UC-APP-008`、`UC-APP-009`、`UC-APP-010`、`UC-APP-011`、`UC-APP-025`、`UC-APP-026`、`UC-APP-029`） |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

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

> Application 当前管理员可以读取 Tester 容量与当前加入链接摘要，分页查询 ACTIVE/REMOVED Membership episode 和 ACTIVE/REVOKED 加入链接历史。查询提供 UC008、UC010、UC011 所需的稳定目标 ID，不授予新的写权限。

只读权限沿用 [UC029](../use-cases/UC-APP-029-query-owned-application-management.md) 和 [UC034](../use-cases/UC-APP-034-query-owned-application-versions.md)：不要求 APPROVED Developer，暂停、归档或关闭后仍可读取保留历史。写命令继续验证各自的 Developer、管理员和 lifecycle 条件。

Tester 标识返回 opaque testerAuthId，不查询姓名、邮箱、学号或其他 Auth 用户资料。加入 secret/hash/joinUrl 均不返回，遗失的链接依 [BR-TST-004](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 只能轮换。产品已审核接受本设计。

### 目标与范围

交付三个只读查询：

1. GetApplicationTesterManagement：容量与当前 ACTIVE 加入链接元数据。
2. ListApplicationTesterMemberships：默认 ACTIVE，可切换 REMOVED 或 ALL 的 episode 分页。
3. ListApplicationTesterJoinLinks：默认 ALL，可过滤 ACTIVE 或 REVOKED 的链接历史分页。

一条列表项已含全部本 UC 可披露字段，首版不另设详情 RPC。管理员通过 membershipId 精确移除一个 episode，通过 joinLinkId 撤销或 expectedActiveJoinLinkId 轮换；这些动作仍分别由 UC010/011/008 实现。

REMOVED/ALL 分页保留为后端能力。首版界面以 ACTIVE 管理为主，不要求提供 REMOVED 历史入口；前端是否展示不改变后端分页和权限契约。

不负责主动退出、黑名单、邀请有效期、恢复旧 episode、链接 credential 恢复、用户搜索、Auth 资料批量披露、通知或平台跨 Application 查询。查询不检查 Test 槽位和宿主兼容性，Tester 资格属于 Application 而不是 Version/major。

### 授权与生命周期

调用者须为可信 USER，authId 等于 snapshot 中 Application.adminId。非当前管理员、无 Application 与跨 Application 路径统一 TesterManagementNotFound；先验证身份，再确认管理员，然后读取 Tester 私有事实。

Reviewer、SYSTEM、Tester、平台运维权限没有隐式读取权。管理员即使本身是 Tester，也必须通过当前管理关系获权。

ACTIVE/CLOSING/CLOSED、AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED 不过滤管理员历史。CLOSED 由保存的最后 adminId 获读权，不能据此恢复写能力或 owner 义务。转让后只有新管理员可开始成功查询，旧管理员已经收到的内容无法收回。

查询遵守 [UC025 / BR-APP-010](../use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010) 的个人状态清理：被账号关闭清理的 episode 不再返回，不从审计、缓存或 Auth 重新构造历史。

### API 与输入草图

新增独立 `app_center.v1.tester_management.ApplicationTesterManagementService`：

```text
GetApplicationTesterManagement
  GET /v1/applications/{application_id}/tester-management

ListApplicationTesterMemberships
  POST /v1/applications/{application_id}/tester-memberships:search
  body: query

ListApplicationTesterJoinLinks
  POST /v1/applications/{application_id}/tester-join-links:search
  body: query
```

path applicationId 为 UUIDv7。两个 search 的 query 分别为：

```text
MembershipQuery {
  status: ACTIVE | REMOVED | ALL = ACTIVE
  pageSize: 1..100 = 20
  pageToken?
}

JoinLinkQuery {
  status: ACTIVE | REVOKED | ALL = ALL
  pageSize: 1..100 = 20
  pageToken?
}
```

省略或 proto unspecified 映射默认值，未知 enum 拒绝。HTTP search 不接收 query-string 覆盖正文；GET 不接收 body/query。不接受 testerAuthId/adminId/source-link filter、全文搜索、offset、时间范围或客户端排序。

### 返回投影

```text
ApplicationTesterManagement {
  applicationId
  capacity: { activeTesterCount, testerLimit: 100 }
  activeJoinLink?: ManagedTesterJoinLink
  asOf
}

ManagedTesterMembership {
  membershipId
  applicationId
  testerAuthId
  status: ACTIVE | REMOVED
  joinedViaJoinLinkId
  joinedAt
  removedAt?
}

ManagedTesterJoinLink {
  joinLinkId
  applicationId
  status: ACTIVE | REVOKED
  createdAt
  revokedAt?
  revocationReason?: ROTATED | MANUAL | ADMIN_TRANSFER | APPLICATION_CLOSURE
  replacedByJoinLinkId?
}

MembershipPage { items[], nextPageToken?, asOf }
JoinLinkPage { items[], nextPageToken?, asOf }
```

这些是独立管理 read model，不直接复用既有命令响应资源。Membership 列表不返回 removedBy，链接投影不返回 createdBy/revokedBy，避免把历史管理员身份当作日常管理信息；本 UC 不提供操作人审计查询。revocationReason 的合法形状以引入该原因的 UC008/011/026/027 为准，不自行新增原因。

capacity 是 snapshot 中 ACTIVE Membership 的权威统计，不存储第二份计数。无 ACTIVE 链接与仍有 ACTIVE Tester 可以同时成立；空链接时 activeJoinLink=null，不能合成新链接。链接为 ACTIVE 只表示尚未撤销，不能保证当前 Application 在线、容量未满或加入写命令可成功。

overview 的容量不随分页变化；列表页不返回 totalCount，也不复制整份 summary。跨 RPC 的 asOf 可能不同，界面不能把它们解释为一个冻结事务。若 overview 显示 10 人但随后页面变化，刷新即可，不以人数不等判断关系损坏。

### 分页与一致读取

Membership 按 `(joinedAt DESC, membershipId DESC)`，JoinLink 按 `(createdAt DESC, joinLinkId DESC)` keyset 分页，时间使用存储精度，UUID 按稳定二进制顺序。相同时间通过 ID 定位，ALL 不按状态分段。

token 至少绑定格式版本、可信调用者、Application、当前 ownershipRevision、查询种类、规范化 status filter、最后排序键，且以服务端密钥签名或等效机制防篡改；不能只用可重算 fingerprint。实现可复用 UC034 的域隔离 HMAC 方案，但必须为本查询种类建立独立 domain。canonical 编码、有界 token 长度和验签失败统一 InvalidTesterManagementPageToken。

每页重新验证可信身份与当前管理员；token 不携带授权结论。换调用者/Application/filter/查询类型、修改位置、或转让后复用旧 ownershipRevision 都拒绝。改变 pageSize 允许继续翻页。每页内部 snapshot 一致，跨页不冻结状态；新加入、移除、轮换、账号清理可能影响后续页，旧页不能作为同步日志。

overview 和每个列表页分别在一个 MongoDB majority read-only snapshot 中读取 Application、所需 episode/link 与批量来源关系。禁止新增 coordination fence、updatedAt、访问审计或远程 Auth 调用，禁止逐 item 开启事务。

overview 统计并校验全部 ACTIVE Membership（上限 100）与其加入来源，同一 authId 多个 ACTIVE episode、容量超过 100 或重复 ACTIVE link 均失败关闭。Membership 页批量校验页内 episode 的来源链接存在且属于同一 Application；来源已 REVOKED 合法，不能要求仍 ACTIVE。JoinLink 页批量校验 ROTATED 的 replacement 存在、属于同一 Application 且不是自身；replacement 后来被撤销也合法。

至少下列已读取关系属于 StateInconsistent：非法状态或 ID/时间、ACTIVE 携带 removal/revocation 字段、REMOVED 缺终态字段、非法原因与 replacement 组合、跨 Application 来源/替代链接、缺必要来源。合法记录的隐藏操作人审计字段仍须符合所属领域不变量，不能因为不披露就跳过结构校验。查询实际发现损坏整次 INTERNAL，不返回部分页、不修复。它不承诺在每次查询全量检查所有历史 episode。

### 主流程与错误

1. 验证 USER、path/query，并规范化 filter。
2. 在只读 snapshot 内确认 Application 当前管理员、ownershipRevision；token 在此上下文验签/绑定校验。
3. overview 取得 ACTIVE count 和唯一 ACTIVE link；列表按 keyset 读取 pageSize+1 记录，批量校验所需关系。
4. 返回最小 read model、snapshot asOf 和必要的下一页 token；无数据成功为空。

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效 USER 身份 | 既有 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY | 401 / UNAUTHENTICATED |
| 非管理员或 Application 不存在 | APPLICATION_TESTER_MANAGEMENT_NOT_FOUND | 404 / NOT_FOUND |
| 非法 path/status/pageSize/HTTP 输入 | INVALID_APPLICATION_TESTER_MANAGEMENT_QUERY | 400 / INVALID_ARGUMENT |
| token 非法、篡改或绑定不匹配 | INVALID_APPLICATION_TESTER_MANAGEMENT_PAGE_TOKEN | 400 / INVALID_ARGUMENT |
| 已读取 Tester 事实损坏 | APPLICATION_TESTER_MANAGEMENT_STATE_INCONSISTENT | 500 / INTERNAL |
| snapshot 或存储不可用 | APPLICATION_TESTER_MANAGEMENT_UNAVAILABLE | 503 / UNAVAILABLE |

所有成功、空页和领域错误在 HTTP 与 gRPC 均使用 `private, no-store`。普通日志/trace 不记录 testerAuthId、历史操作人、token、joinUrl/secret/hash、用户资料或请求正文，只记录稳定错误类别和必要资源 ID。

### 索引与实现依赖

新增独立 query usecase/port，不把列表投影、分页或用户资料放入 Tester 聚合。现有唯一 ACTIVE episode/link 索引用于权威判断；通过显式 migration 增加：

```text
Membership: (applicationId, joinedAt DESC, membershipId DESC)
Membership: (applicationId, status, joinedAt DESC, membershipId DESC)
JoinLink:   (applicationId, createdAt DESC, joinLinkId DESC)
JoinLink:   (applicationId, status, createdAt DESC, joinLinkId DESC)
```

接受后按当时 migration ledger 分配编号并升级 readiness，不新增业务集合。签名 key 只在配置/adapter 边界，查询不得持有明文加入凭证。UC036 的 Test clear 不影响本管理查询，两个用例只在实现顺序上相邻。

### 引用规则与实现输入

Membership 形状和来源依据 [BR-TST-012](../use-cases/UC-APP-009-join-application-as-tester.md#br-tst-012)、[BR-TST-014](../use-cases/UC-APP-009-join-application-as-tester.md#br-tst-014)、[BR-TST-016](../use-cases/UC-APP-009-join-application-as-tester.md#br-tst-016)、[BR-TST-023](../use-cases/UC-APP-010-remove-application-tester.md#br-tst-023)；链接形状依据 [BR-TST-003](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-003)、[BR-TST-005](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-005)、[BR-TST-031](../use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-031)。私有历史与转让沿用 [BR-APP-039](../use-cases/UC-APP-029-query-owned-application-management.md#br-app-039) 和 [BR-APP-015](../use-cases/UC-APP-026-transfer-application-administration.md#br-app-015)。

### 验收与交付边界

1. 当前管理员无需 APPROVED 可读；其他角色、旧管理员及不存在 Application 的错误不泄漏资源。
2. 各 lifecycle/platform/archive 组合可读保留历史；查询不解除在线门禁或开启写命令。
3. 容量 0/100、无链接有 Tester、有链接无 Tester、链接已轮换都映射真实 snapshot。
4. 默认/所有 status、空页、同时间多 ID、边界 pageSize、token 换身份/应用/过滤/种类/ownershipRevision/篡改各有覆盖。
5. 移除与重新加入保留旧 REMOVED、新 ACTIVE episode，分页精确定位旧 ID；账号清理后无历史重建。
6. 返回可用于 UC008/010/011 的 ID，但并发变化后旧输入按命令既有规则处理。
7. 缺来源链接、非法 replacement、跨应用、重复 ACTIVE、超容量和终态结构损坏整次 INTERNAL。
8. 与加入、移除、轮换、撤销、转让、关闭和个人状态清理并发时，每次查询来自明确先后 snapshot。
9. 响应与 telemetry 不含 credential/hash、Auth 资料、历史操作人；HTTP/gRPC/no-store 与生成客户端同义。
10. 真实 Mongo 证明只读，无 fence/revision/audit 漂移，无外部业务网络调用或逐 item 事务。

接受后生成 brief、实现独立 API/read port/Mongo snapshot/索引/transport，并运行 `make check-full`。本 UC 不需要新增 Auth API 或用户资料协议，生产前端展示与资料解析由相邻工作包负责。

### 变更记录

- 2026-10-12：在 UC036 提案完成后建立 Tester 管理查询提案；建议容量概览、episode/链接历史分页和不可恢复凭证的最小披露边界。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；REMOVED/ALL 分页保留后端契约，首版界面不要求展示历史入口。

## 业务规则（UC-APP-037 权威正文）

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-037 -->
### BR-TST-037：当前管理员私有 Tester 读取

Tester 管理只读查询仅授予 snapshot 中当前 adminId 对应可信 USER，不要求 APPROVED Developer。不存在和非管理员统一隐藏；其他角色不隐式授权。保留的所有生命周期历史可读，不恢复写能力。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-038 -->
### BR-TST-038：容量与当前链接来自权威快照

overview 的 ACTIVE count、固定 100 上限与唯一 ACTIVE link 来自一个 snapshot。无 ACTIVE link 可与 ACTIVE Membership 并存，链接存在不保证可加入；查询不建立计数、凭证或新的审计事实。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-039 -->
### BR-TST-039：Membership episode 历史查询

分页读取仍保留的 ACTIVE/REMOVED episode，默认 ACTIVE，按稳定 membershipId 提供移除目标。同用户重新加入为新 episode；账号关闭已清理记录不返回或重建。来源链接被撤销不撤销 episode。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-040 -->
### BR-TST-040：链接历史与凭证最小披露

链接查询返回 ACTIVE/REVOKED 元数据、合法撤销原因和 replacement 身份，绝不返回 secret/hash/joinUrl，不能恢复旧凭证。管理读取不返回历史操作人或 Auth 用户资料，只向管理员披露 Membership 的必要 opaque testerAuthId。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-041 -->
### BR-TST-041：私有分页绑定管理权

两种列表分别按时间与 ID 降序 keyset，token 必须防篡改并绑定可信身份、Application、ownershipRevision、查询种类和 status。每页重新授权，不返回 totalCount；跨页不保证同一 snapshot。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-042 -->
### BR-TST-042：只读一致性与关系损坏失败关闭

每次 overview/页面内授权、Tester 事实和必要关系来自同一只读 snapshot，批量加载。已读来源、替代、状态、容量或唯一性损坏整次失败，不跳项、不修复，不创建写栅栏、不调用 Auth。

<!-- 权威位置: use-cases/UC-APP-037-query-application-tester-management.md#br-tst-043 -->
### BR-TST-043：查询不替代命令检查

响应 ID、asOf、人数、链接状态或 token 不是写权限/锁。轮换、撤销、移除在其最终事务继续检查当前管理员、Developer、lifecycle 和各自 OCC/episode 条件；敏感查询响应与领域错误均 private, no-store。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-025`

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010 -->
### BR-APP-010：注销个人状态清理

ACCOUNT_CLOSURE 的准备及永久 sealed 同时阻止 Tester Join 新增个人状态；DEVELOPER_WITHDRAWAL 仍允许普通 Tester 加入。创建/Join 与 Prepare 共用账号栅栏，涉及 Application coordination fence 时统一顺序 account→Application。

COMMITTED ACCOUNT_CLOSURE 后以有界批次清理该 testerAuthId 的全部 ACTIVE/REMOVED membership episode，并在各 Application coordination fence 内处理，保证人数计数及并发移除一致；其他用户不受影响。零应用账号的 creation quota 可以删除。仅在扫描为空并确认不可重建时标为 COMPLETE。

application_filters/filter_revisions 是应用公开 Filter，不是用户偏好，不能删除。保留 Application、Version、Review、Publication 及历史 createdBy/submittedBy/reviewer 等归因；当前没有独立个人偏好 collection，禁止凭名称猜测清理表。未来新增个人数据需显式纳入清单。

### 来自 `UC-APP-026`

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-015 -->
### BR-APP-015：管理权 revision 与共享写栅栏

Application 持有正数 `ownershipRevision`，旧记录迁移为 1。发起时调用者提供 expectedOwnershipRevision，申请保存 sourceOwnershipRevision；只有接受成功使其增加 1。

转让与 Version、Profile、Publication、Tester、OAuth、Filter 及其他管理员写操作共用 Application `coordinationRevision` 写栅栏，并在最终事务中复查当前 admin。旧管理员持有的尚未过期 JWS 无需全局撤销：接受先提交时其后续写入因 adminId 不匹配而失败；旧管理员写入先提交时，其操作先线性化，接受再基于更新后的完整 Application 事实提交或失败。

`ownershipRevision` 是管理权 API 的业务 OCC，不替代 adapter-only coordinationRevision，也不因普通下级写入增加。

### 来自 `UC-APP-029`

<!-- 权威位置: use-cases/UC-APP-029-query-owned-application-management.md#br-app-039 -->
### BR-APP-039：生命周期可见性

SUSPENDED Application 始终保留管理可见性；CLOSED 只在显式筛选或直接详情中作为历史可见，不恢复 owner 义务。

### 来自 `UC-APP-008`

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-003 -->
### BR-TST-003：单一有效链接

每个 Application 同时最多存在一个 `ACTIVE` TesterJoinLink。已撤销记录可以有多个并永久保留。

当前模型不设置 expiresAt，也不因 Tester 列表已满自动撤销链接。是否允许加入由后续加入用例在提交 Membership 时判断。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004 -->
### BR-TST-004：Secret 与哈希

- secret 必须来自密码学安全随机源，长度为 32 bytes。
- 对外编码使用无填充 base64url。
- SHA-256 输入是编码前的 32 个原始 bytes；数据库只保存 tokenHash，不保存 secret 或完整 joinUrl。
- 校验 secret 时必须使用常量时间比较。
- secret、joinUrl 和 tokenHash 不得进入普通日志、指标标签、追踪属性或集成事件。
- joinUrl 仅在创建成功响应中返回一次；遗失后只能轮换，不能从数据库恢复。

tokenHash 可以使用 SHA-256，是因为输入是系统生成的 256-bit 随机 secret，而不是低熵用户密码。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-005 -->
### BR-TST-005：创建与轮换语义

- expectedActiveJoinLinkId 为 null 时，只能从“无有效链接”创建。
- expectedActiveJoinLinkId 有值时，只能轮换 ID 完全相同的当前有效链接。
- 每次成功调用都创建新的 joinLinkId 和 secret，不存在 no-op。
- 轮换成功后，旧链接立即失效，新链接成为唯一有效链接。
- 旧链接使用 reason=`ROTATED` 记录撤销，并指向 replacedByJoinLinkId。

以后“仅撤销而不替换”应由独立用例完成，不能伪造一次没有新链接的轮换。

### 来自 `UC-APP-009`

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-012 -->
### BR-TST-012：Application 级 Membership

Tester Membership 的业务键是 `(applicationId, testerAuthId)`，不包含 rpcApiMajor、Version 或 Publication。

更换 test 槽位或客户端升级不会自动移除 Membership。管理员转让是否同时轮换加入链接属于未来转让用例的安全策略，本用例不提前决定；无论如何，转让不能由一次 Tester 加入操作触发。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-014 -->
### BR-TST-014：Tester 数量上限

上限按 Application 计算，只统计 ACTIVE Membership episode。加入新用户时必须在同一原子边界确认：

```text
activeTesterCount < testerLimit
```

每个 Application 的 Tester 上限固定为 100。达到上限不会自动撤销加入链接，也不会移除现有 Tester；未来若需要调整上限，必须由新的明确业务规则和用例引入。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-016 -->
### BR-TST-016：Membership episode 与唯一性

- membershipId 是 UUIDv7，创建后不变。
- 每个 `(applicationId, testerAuthId)` 同时最多一个 ACTIVE episode。
- 同一用户可以在被移除后留下多个历史 episode，但只有最新加入且未移除的一条为 ACTIVE。
- joinedViaJoinLinkId 必须指向本次验证通过且属于同一 Application 的链接。
- joinedAt 由 App Center 时钟生成。

### 来自 `UC-APP-010`

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-023 -->
### BR-TST-023：REMOVED 终态与审计

成功移除必须记录：

```text
status = REMOVED
removedBy = current admin authId
removedAt = App Center Clock
```

joinedViaJoinLinkId 和 joinedAt 保持不变。REMOVED episode 不恢复为 ACTIVE、不物理删除；用户再次加入时创建新的 episode。

### 来自 `UC-APP-011`

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-031 -->
### BR-TST-031：MANUAL 撤销终态

ACTIVE 链接成功显式撤销后必须满足：

```text
status = REVOKED
revocationReason = MANUAL
revokedBy = current admin authId
revokedAt = App Center Clock
replacedByJoinLinkId = null
```

MANUAL 表示没有由本操作创建的替代链接。REVOKED 是终态，链接不能恢复为 ACTIVE。

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-025`（use-cases/UC-APP-025-coordinate-account-owner-exit.md）：目标与范围、主流程与 API、数据与验收、交付依赖
- `UC-APP-026`（use-cases/UC-APP-026-transfer-application-administration.md）：目标与范围、参与者与依赖、输入与身份、生命周期、发起流程、接受流程、拒绝与取消、领域与数据模型、API 草图、错误边界、并发验收场景、实现依赖与交付边界、变更记录
- `UC-APP-029`（use-cases/UC-APP-029-query-owned-application-management.md）：目标与范围、身份、授权与存在性隐藏、列表语义、管理详情、一致性与损坏状态、最小查询模型与索引、API 草图、验收场景、实现依赖与交付边界、变更记录
- `UC-APP-008`（use-cases/UC-APP-008-create-or-rotate-tester-join-link.md）：目标与范围、业务边界、前端扫码与加入边界、配置与临时入口、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `UC-APP-009`（use-cases/UC-APP-009-join-application-as-tester.md）：目标与范围、业务边界、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `UC-APP-010`（use-cases/UC-APP-010-remove-application-tester.md）：目标与范围、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `UC-APP-011`（use-cases/UC-APP-011-revoke-tester-join-link.md）：目标与范围、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-037-query-application-tester-management.md` | 216 | `f2d2bac6c26d` |
| `use-cases/UC-APP-025-coordinate-account-owner-exit.md` | 65 | `730a0ecc6a28` |
| `use-cases/UC-APP-026-transfer-application-administration.md` | 324 | `7e93553d9cdd` |
| `use-cases/UC-APP-029-query-owned-application-management.md` | 151 | `bf56cdb407d2` |
| `use-cases/UC-APP-008-create-or-rotate-tester-join-link.md` | 414 | `9a39e6856efb` |
| `use-cases/UC-APP-009-join-application-as-tester.md` | 413 | `71b19b545669` |
| `use-cases/UC-APP-010-remove-application-tester.md` | 337 | `4804d0a44f36` |
| `use-cases/UC-APP-011-revoke-tester-join-link.md` | 339 | `e55e4f0feaf1` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
