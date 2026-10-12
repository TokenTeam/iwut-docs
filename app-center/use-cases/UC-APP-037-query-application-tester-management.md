# UC-APP-037：查询 Application Tester 管理视图

状态：`ACCEPTED`

## 设计结论

> Application 当前管理员可以读取 Tester 容量与当前加入链接摘要，分页查询 ACTIVE/REMOVED Membership episode 和 ACTIVE/REVOKED 加入链接历史。查询提供 UC008、UC010、UC011 所需的稳定目标 ID，不授予新的写权限。

只读权限沿用 [UC029](UC-APP-029-query-owned-application-management.md) 和 [UC034](UC-APP-034-query-owned-application-versions.md)：不要求 APPROVED Developer，暂停、归档或关闭后仍可读取保留历史。写命令继续验证各自的 Developer、管理员和 lifecycle 条件。

Tester 标识返回 opaque testerAuthId，不查询姓名、邮箱、学号或其他 Auth 用户资料。加入 secret/hash/joinUrl 均不返回，遗失的链接依 [BR-TST-004](UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 只能轮换。产品已审核接受本设计。

## 目标与范围

交付三个只读查询：

1. GetApplicationTesterManagement：容量与当前 ACTIVE 加入链接元数据。
2. ListApplicationTesterMemberships：默认 ACTIVE，可切换 REMOVED 或 ALL 的 episode 分页。
3. ListApplicationTesterJoinLinks：默认 ALL，可过滤 ACTIVE 或 REVOKED 的链接历史分页。

一条列表项已含全部本 UC 可披露字段，首版不另设详情 RPC。管理员通过 membershipId 精确移除一个 episode，通过 joinLinkId 撤销或 expectedActiveJoinLinkId 轮换；这些动作仍分别由 UC010/011/008 实现。

REMOVED/ALL 分页保留为后端能力。首版界面以 ACTIVE 管理为主，不要求提供 REMOVED 历史入口；前端是否展示不改变后端分页和权限契约。

不负责主动退出、黑名单、邀请有效期、恢复旧 episode、链接 credential 恢复、用户搜索、Auth 资料批量披露、通知或平台跨 Application 查询。查询不检查 Test 槽位和宿主兼容性，Tester 资格属于 Application 而不是 Version/major。

## 授权与生命周期

调用者须为可信 USER，authId 等于 snapshot 中 Application.adminId。非当前管理员、无 Application 与跨 Application 路径统一 TesterManagementNotFound；先验证身份，再确认管理员，然后读取 Tester 私有事实。

Reviewer、SYSTEM、Tester、平台运维权限没有隐式读取权。管理员即使本身是 Tester，也必须通过当前管理关系获权。

ACTIVE/CLOSING/CLOSED、AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED 不过滤管理员历史。CLOSED 由保存的最后 adminId 获读权，不能据此恢复写能力或 owner 义务。转让后只有新管理员可开始成功查询，旧管理员已经收到的内容无法收回。

查询遵守 [UC025 / BR-APP-010](UC-APP-025-coordinate-account-owner-exit.md#br-app-010) 的个人状态清理：被账号关闭清理的 episode 不再返回，不从审计、缓存或 Auth 重新构造历史。

## API 与输入草图

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

## 返回投影

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

## 分页与一致读取

Membership 按 `(joinedAt DESC, membershipId DESC)`，JoinLink 按 `(createdAt DESC, joinLinkId DESC)` keyset 分页，时间使用存储精度，UUID 按稳定二进制顺序。相同时间通过 ID 定位，ALL 不按状态分段。

token 至少绑定格式版本、可信调用者、Application、当前 ownershipRevision、查询种类、规范化 status filter、最后排序键，且以服务端密钥签名或等效机制防篡改；不能只用可重算 fingerprint。实现可复用 UC034 的域隔离 HMAC 方案，但必须为本查询种类建立独立 domain。canonical 编码、有界 token 长度和验签失败统一 InvalidTesterManagementPageToken。

每页重新验证可信身份与当前管理员；token 不携带授权结论。换调用者/Application/filter/查询类型、修改位置、或转让后复用旧 ownershipRevision 都拒绝。改变 pageSize 允许继续翻页。每页内部 snapshot 一致，跨页不冻结状态；新加入、移除、轮换、账号清理可能影响后续页，旧页不能作为同步日志。

overview 和每个列表页分别在一个 MongoDB majority read-only snapshot 中读取 Application、所需 episode/link 与批量来源关系。禁止新增 coordination fence、updatedAt、访问审计或远程 Auth 调用，禁止逐 item 开启事务。

overview 统计并校验全部 ACTIVE Membership（上限 100）与其加入来源，同一 authId 多个 ACTIVE episode、容量超过 100 或重复 ACTIVE link 均失败关闭。Membership 页批量校验页内 episode 的来源链接存在且属于同一 Application；来源已 REVOKED 合法，不能要求仍 ACTIVE。JoinLink 页批量校验 ROTATED 的 replacement 存在、属于同一 Application 且不是自身；replacement 后来被撤销也合法。

至少下列已读取关系属于 StateInconsistent：非法状态或 ID/时间、ACTIVE 携带 removal/revocation 字段、REMOVED 缺终态字段、非法原因与 replacement 组合、跨 Application 来源/替代链接、缺必要来源。合法记录的隐藏操作人审计字段仍须符合所属领域不变量，不能因为不披露就跳过结构校验。查询实际发现损坏整次 INTERNAL，不返回部分页、不修复。它不承诺在每次查询全量检查所有历史 episode。

## 主流程与错误

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

## 业务规则

<a id="br-tst-037"></a>
### BR-TST-037：当前管理员私有 Tester 读取

Tester 管理只读查询仅授予 snapshot 中当前 adminId 对应可信 USER，不要求 APPROVED Developer。不存在和非管理员统一隐藏；其他角色不隐式授权。保留的所有生命周期历史可读，不恢复写能力。

<a id="br-tst-038"></a>
### BR-TST-038：容量与当前链接来自权威快照

overview 的 ACTIVE count、固定 100 上限与唯一 ACTIVE link 来自一个 snapshot。无 ACTIVE link 可与 ACTIVE Membership 并存，链接存在不保证可加入；查询不建立计数、凭证或新的审计事实。

<a id="br-tst-039"></a>
### BR-TST-039：Membership episode 历史查询

分页读取仍保留的 ACTIVE/REMOVED episode，默认 ACTIVE，按稳定 membershipId 提供移除目标。同用户重新加入为新 episode；账号关闭已清理记录不返回或重建。来源链接被撤销不撤销 episode。

<a id="br-tst-040"></a>
### BR-TST-040：链接历史与凭证最小披露

链接查询返回 ACTIVE/REVOKED 元数据、合法撤销原因和 replacement 身份，绝不返回 secret/hash/joinUrl，不能恢复旧凭证。管理读取不返回历史操作人或 Auth 用户资料，只向管理员披露 Membership 的必要 opaque testerAuthId。

<a id="br-tst-041"></a>
### BR-TST-041：私有分页绑定管理权

两种列表分别按时间与 ID 降序 keyset，token 必须防篡改并绑定可信身份、Application、ownershipRevision、查询种类和 status。每页重新授权，不返回 totalCount；跨页不保证同一 snapshot。

<a id="br-tst-042"></a>
### BR-TST-042：只读一致性与关系损坏失败关闭

每次 overview/页面内授权、Tester 事实和必要关系来自同一只读 snapshot，批量加载。已读来源、替代、状态、容量或唯一性损坏整次失败，不跳项、不修复，不创建写栅栏、不调用 Auth。

<a id="br-tst-043"></a>
### BR-TST-043：查询不替代命令检查

响应 ID、asOf、人数、链接状态或 token 不是写权限/锁。轮换、撤销、移除在其最终事务继续检查当前管理员、Developer、lifecycle 和各自 OCC/episode 条件；敏感查询响应与领域错误均 private, no-store。

## 索引与实现依赖

新增独立 query usecase/port，不把列表投影、分页或用户资料放入 Tester 聚合。现有唯一 ACTIVE episode/link 索引用于权威判断；通过显式 migration 增加：

```text
Membership: (applicationId, joinedAt DESC, membershipId DESC)
Membership: (applicationId, status, joinedAt DESC, membershipId DESC)
JoinLink:   (applicationId, createdAt DESC, joinLinkId DESC)
JoinLink:   (applicationId, status, createdAt DESC, joinLinkId DESC)
```

接受后按当时 migration ledger 分配编号并升级 readiness，不新增业务集合。签名 key 只在配置/adapter 边界，查询不得持有明文加入凭证。UC036 的 Test clear 不影响本管理查询，两个用例只在实现顺序上相邻。

## 引用规则与实现输入

Membership 形状和来源依据 [BR-TST-012](UC-APP-009-join-application-as-tester.md#br-tst-012)、[BR-TST-014](UC-APP-009-join-application-as-tester.md#br-tst-014)、[BR-TST-016](UC-APP-009-join-application-as-tester.md#br-tst-016)、[BR-TST-023](UC-APP-010-remove-application-tester.md#br-tst-023)；链接形状依据 [BR-TST-003](UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-003)、[BR-TST-005](UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-005)、[BR-TST-031](UC-APP-011-revoke-tester-join-link.md#br-tst-031)。私有历史与转让沿用 [BR-APP-039](UC-APP-029-query-owned-application-management.md#br-app-039) 和 [BR-APP-015](UC-APP-026-transfer-application-administration.md#br-app-015)。

## 验收与交付边界

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

## 变更记录

- 2026-10-12：在 UC036 提案完成后建立 Tester 管理查询提案；建议容量概览、episode/链接历史分页和不可恢复凭证的最小披露边界。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；REMOVED/ALL 分页保留后端契约，首版界面不要求展示历史入口。
