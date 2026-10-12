<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-038 --spec tools/brief-specs/UC-APP-038.json -->
# Brief — UC-APP-038：查询我参与的测试 Application

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-038` 查询我参与的测试 Application |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-CAT-011`–`BR-CAT-017`（7 条） |
| 外部引用 BR | `BR-APP-010`、`BR-APP-031`、`BR-APP-053`，`BR-CAT-004`，`BR-PRF-030`，`BR-PUB-036`，`BR-RUN-001`–`BR-RUN-008`（8 条）（来自 `UC-APP-012`、`UC-APP-016`、`UC-APP-024`、`UC-APP-025`、`UC-APP-028`、`UC-APP-033`、`UC-APP-036`） |
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

> 已认证用户可以分页查询自己拥有 ACTIVE Tester Membership 的在线 Application，并读取其中一个的测试详情。结果展示当前已批准公开资料和 Test 可用性；有兼容 Test 时只返回 Test 启动目标，暂时无目标时保留参与卡片并说明原因。

候选来自当前用户的 Membership，不要求 Stable。已有 Stable 的 Application 也可出现在此入口；它与 [UC024 普通 Catalog](../use-cases/UC-APP-024-query-public-application-catalog.md) 独立，两个入口的候选资格和使用目的不同。

保留“已经参与、暂时不可启动”的卡片，因为 [UC009](../use-cases/UC-APP-009-join-application-as-tester.md) 允许先加入、后设置 Test，[UC036](../use-cases/UC-APP-036-clear-test-publication-slot.md) 清空时保留 Membership。用户应能区分失去资格与等待开发者发布。资料尚未公开时不使用技术名称或未审核资料作为替代。

暂停、归档、CLOSING/CLOSED 仍遵守既有在线门禁：列表隐藏、详情统一 NOT_FOUND，不返回占位卡片或目标。ACTIVE Membership 保留不意味着绕过这些门禁。产品已审核接受本设计。

### 目标与范围

交付 ListMyTestApplications 与 GetMyTestApplication，负责本人资格、运行输入、私有分页、当前公开 Profile、纯 Test 解析和不可用状态投影。

不负责主动退出、加入或移除 Tester、历史参与记录、其他用户/管理员查询、Stable/Grey 启动回退、服务端或客户端 Filter、邀请凭证、Auth 资料、WebView/session/token、搜索排序推荐或通知。管理员未显式加入不会自动出现在列表。

这是独立测试参与查询，不把 test-only 应用混入普通 Catalog，不保存物化可见列表。UC037 管理查询的权限与历史可见性不授予本用例。

### 身份、候选与门禁

身份必须为可信 USER，authId 只从认证上下文取得；developerStatus、Reviewer 或平台权限不参与授权。匿名和无效凭证返回认证失败，不能降级到公开查询。

候选满足：

1. 当前用户在该 Application 下存在唯一 ACTIVE Membership。
2. Application 存在，lifecycleStatus=ACTIVE。
3. platformAvailabilityStatus=AVAILABLE，archiveStatus=UNARCHIVED。

使用 [UC028](../use-cases/UC-APP-028-suspend-and-restore-application.md) 和 [UC033](../use-cases/UC-APP-033-archive-and-unarchive-application.md) 的共同在线门禁。不存在、没有 ACTIVE episode、REMOVED、暂停、归档或关闭等正常不合格项在列表跳过，详情统一 MyTestApplicationNotFound；不能通过详情区分他人应用、移除和管理门禁。

Membership 缺失 Application 属于内部悬空关系，列表已扫描到这种关系整页失败；直接详情首先按正常不存在/无资格统一隐藏。对通过 gate 的候选须批量验证 Membership 形状和加入来源链接的同 Application 归属；来源链接后来被撤销仍合法。已读重复 ACTIVE episode、缺失或跨应用来源等关系损坏失败关闭。账号个人状态清理依 [BR-APP-010](../use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010)，已清理记录不恢复。

### 输入与 API 草图

新增独立 `app_center.v1.test_application_catalog.TestApplicationCatalogService`：

```text
ListMyTestApplications
  POST /v1/test-applications:search
  body: query

GetMyTestApplication
  POST /v1/test-applications/{application_id}:resolve
  body: runtime

RuntimeQuery {
  hostRpcApiMajor
  hostCapabilities[]
}

ListQuery {
  runtime: RuntimeQuery
  pageSize: 1..100 = 20
  pageToken?
}
```

path applicationId 为 UUIDv7；运行字段沿用 [UC012 输入](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#输入与身份) 的 major 正整数、capability 格式和集合去重排序。列表必须携带 runtime。HTTP 不接受 query-string 覆盖正文，身份、membershipId、channel、versionId、Filter 结果不能由请求指定。

详情 POST 因为也需宿主运行上下文；查询保持只读。两种 transport 共享结果与错误，所有成功、不可用卡片、空页与领域错误均使用 `Cache-Control: private, no-store`。

### 参与卡片与可用性

```text
MyTestApplicationItem {
  applicationId
  membership: { membershipId, joinedAt }
  profile?: {
    profileRevisionId, displayName, description?, icon?
  }
  availability: READY | PROFILE_REQUIRED | TEST_TARGET_UNAVAILABLE
                | HOST_CAPABILITIES_INSUFFICIENT
  launchTarget?: TestLaunchDescriptor
  missingCapabilities[]
}

MyTestApplicationPage { items[], nextPageToken?, asOf }
MyTestApplicationDetail { item: MyTestApplicationItem, asOf }
```

列表项与详情使用同一投影。membership 仅返回调用者自己的 episode 身份和时间，不返回 testerAuthId、加入来源链接、操作人或其他 Tester。profile 仅来自当前公开指针，批准事实与投影沿用 [BR-CAT-004](../use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-004)；不返回技术名称、管理员、作者、未公开资料或审核内容。

在已通过资格和在线门禁的 snapshot 内，按以下顺序投影：

| 当前事实 | availability | profile | launchTarget | missingCapabilities |
| --- | --- | --- | --- | --- |
| 没有 currentPublishedProfileRevisionId | PROFILE_REQUIRED | 无 | 无 | 空 |
| 有有效公开资料，但 exact-major Publication 或 Test 指针不存在 | TEST_TARGET_UNAVAILABLE | 有 | 无 | 空 |
| 有有效公开资料/批准 Test，但宿主缺少必需 capabilities | HOST_CAPABILITIES_INSUFFICIENT | 有 | 无 | 稳定排序的缺少能力 |
| 有有效公开资料、批准兼容 Test 且能力满足 | READY | 有 | 有 | 空 |

availability 是当次查询投影，不是新的持久化业务状态。PROFILE_REQUIRED 可出现在加入先于首次公开资料的合法阶段；客户端可使用本地通用文案表示等待就绪，服务端不能回退技术名称或未审核 displayName。测试应用当前不支持请求 major 时等价于没有 exact-major Test；不扫描其他 major。

有非空 Profile/Test 指针而目标缺失、跨 Application、非 APPROVED、snapshot 漂移或 range 不覆盖该 Publication major，属于损坏，不能映射为正常不可用卡片。各阶段只需读取当前阶段相关事实；不要求为一个已被门禁排除的候选继续读取私有运行内容，也不全量检查所有未选槽位。

READY 的 launchTarget 复用 [UC012 / TestLaunchDescriptor](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#最小查询模型)，包含当前 exact-major Test 的身份、revision、launch URL、兼容范围和 scopes 声明。不存在 Stable/Grey 回退：即使同一应用在普通 Catalog 可运行，测试入口的空/不兼容 Test 仍返回上述不可用状态。

不会读取或分发 Filter。该行为由入口语义决定，不能因为 Application 已有 Stable 就改成普通 Catalog Filter；READY 仅意味着可按当前 Test 事实启动，不代表已取得 Auth consent/token 或运行租约。

### 解析复用与查询快照

运行校验复用 UC012 的 ACTIVE Membership、exact-major Test、最近相关 Test History、批准 Version/Review/OAuth 配置一致性及 capability 子集语义。当前公开 Profile 的有效性沿用已接受的 Profile/Review 规则。查询不调用公开 UC012 RPC 再逐项拼接结果；应抽取或复用同一批量解析核心，在一个页面 snapshot 内加载和组合。

UC012 自身保留现有“无 Test/缺能力则错误”的单目标 RPC；本用例显式把这两种正常结果映射为 unavailable card，不修改其 RPC。损坏关系在本入口统一 MyTestApplicationStateInconsistent（500/INTERNAL）；不能把 UC012 的内部不一致 UNAVAILABLE 错误误当作普通无目标。

UC036 被接受并实现后，最近 CLEAR_TEST_VERSION 与空 Test 必须一致；不能从旧 SET_TEST 历史取得运行目标。Stable/Grey 变化后的共享 Publication revision 不表示 Test 批准依据丢失，校验最近相关 Test action。若 UC036 未接受，本查询也可以对既有 stable-only/EMPTY Publication 返回 TEST_TARGET_UNAVAILABLE。

每个列表页或详情用一个 MongoDB majority read-only snapshot，同时确认 Membership、Application 在线门禁和所需 Profile、Publication/History、Version/Review/OAuth。与 Test clear/replace、Profile 批准、Membership 移除/加入、暂停/归档、关闭和账号清理并发时，必须返回提交前或后的完整事实组合。

只读查询不写 coordinationRevision、访问历史、asOf 记录、计数或持久化可用性；不调用 Scope Catalog、DNS preflight、Auth 用户资料或 OAuth provider。技术观测不记录可信 authId、pageToken、完整 URL/scopes、凭证或返回正文。

### 排序、分页与预算

按 ApplicationId 二进制升序扫描当前 authId 的 ACTIVE Membership，确保同一 Application 最多一项。pageToken 表示最后已消费的 ApplicationId，不使用 offset 或最近使用/名称/可用性排序。

token 必须签名或等效防篡改，并绑定版本、可信 authId、规范化 major/capabilities 指纹、查询种类和最后扫描位置；建立独立于 UC037/UC034 的签名 domain。换用户、换 major、改变 capability 集合、篡改位置或非法 canonical 编码拒绝；重复/重排 capabilities 规范化后可继续，pageSize 可改变。token 不承载资格，每页重新读取 ACTIVE Membership 和在线门禁。

pageSize 默认20、范围1–100。不返回 totalCount。首版每页最多扫描500个 ACTIVE candidate，响应预算建议3 MiB：到扫描上限可返回少于 pageSize 甚至空页并提供 nextPageToken；到字节预算时 token 停在最后已消费项之前或之处，不能越过尚未返回的合法 item。单个合法 item 必须能单独返回。

被移除或 gate 隐藏项仍占扫描位置；PROFILE_REQUIRED/TEST_TARGET_UNAVAILABLE/能力不足属于返回 item，占 pageSize。新加入到已扫描位置之前的 Application 只能在下一轮刷新出现；跨页不冻结 snapshot，重新加入得到新的 membershipId，不保证该轮分页再次展示同一 Application。

### 主流程与错误

列表：验证 USER/runtime/page → 开启只读 snapshot → 按 authId 和 ACTIVE keyset 批量扫描 Membership → 加载 Application 并应用 gate → 批量加载候选当前 Profile 和 Test 运行事实 → 映射卡片与预算 → 返回 asOf/token。

详情：验证 USER/runtime/path → 同一 snapshot 先确认 ACTIVE Membership 与 Application gate → 不合格统一404 → 执行相同投影 → 返回 item/asOf。无 Test 或能力不足对合格参与者为200卡片，不为404。

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效 USER 身份 | 既有 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY | 401 / UNAUTHENTICATED |
| 非法 runtime/path/pageSize/HTTP 输入 | INVALID_MY_TEST_APPLICATION_QUERY | 400 / INVALID_ARGUMENT |
| token 损坏、篡改或绑定不匹配 | INVALID_MY_TEST_APPLICATION_PAGE_TOKEN | 400 / INVALID_ARGUMENT |
| 详情不存在、无 ACTIVE Membership 或被 gate 隐藏 | MY_TEST_APPLICATION_NOT_FOUND | 404 / NOT_FOUND |
| 已读必要关系损坏 | MY_TEST_APPLICATION_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储/snapshot 不可用 | MY_TEST_APPLICATION_UNAVAILABLE | 503 / UNAVAILABLE |

列表无候选成功空数组。损坏整页/详情失败，不返回 per-item error 或部分成功，不静默略过坏 Profile/Test，也不自动修复。无目标、缺资料和能力不足是有明确合法事实的投影，与存储失败不同。

### 索引与交付边界

通过显式 migration 增加本人 ACTIVE 扫描索引：

```text
application_tester_memberships:
  (testerAuthId ASC, status ASC, applicationId ASC, membershipId ASC)
```

保留既有 `(applicationId, testerAuthId)` ACTIVE 唯一约束。其他事实复用当前 pointer/ID/review/history 索引；不新增领域实体或集合，不把参与列表保存到 Auth。migration 编号在接受/开工时对齐实际 ledger。

接受后生成 brief，交付独立 API、Catalog query port/read model、批量 snapshot adapter、索引、HTTP/gRPC 和真实 Mongo E2E；最低门禁 `make check-full`。查询不改变 Auth runtime provider 或签发规则，不需新增 Auth API。UC036/037 与本 UC 按请求顺序设计；实现可复用 036 的新 History 支持，037 的管理员读权不能替代本人资格。

### 引用规则与实现输入

批量纯 Test 解析复用 [BR-RUN-001](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001)、[BR-RUN-002](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-002)、[BR-RUN-003](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003)、[BR-RUN-004](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-004)、[BR-RUN-005](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005)、[BR-RUN-006](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-006)、[BR-RUN-007](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-007)、[BR-RUN-008](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-008)；公开资料批准一致性依据 [BR-PRF-030](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)。在线门禁复用 [BR-APP-031](../use-cases/UC-APP-028-suspend-and-restore-application.md#br-app-031)、[BR-APP-053](../use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-053)，Test clear 复用 [BR-PUB-036](../use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-036)。

### 验收场景

1. 普通 USER 显式加入 test-only 或 stable-backed Application 后可在此入口看到；无 Membership 的管理员/Reviewer、匿名和其他用户不能取得卡片。
2. 无 Stable 的合法 Test READY；仅有 Stable、只有其他 major Test、空 Publication 都为 TEST_TARGET_UNAVAILABLE，无隐式回退。
3. 缺公开 pointer 得到 PROFILE_REQUIRED 且无技术名称/未审核资料；有效 Profile 返回公开投影；坏 pointer 非 APPROVED/snapshot 漂移整页 INTERNAL。
4. 能力不足返回稳定 missingCapabilities、无 launch URL/scopes/target；能力满足才 READY，输入重复排序按集合规范化。
5. Test clear 前READY、后保留 unavailable card；重新 set 恢复当前兼容 Test，Membership 身份与 joinedAt 不变。
6. REMOVED 后列表不见、详情404；再加入返回新 membershipId；账号清理后不恢复历史。
7. 暂停/归档/关闭列表隐藏、详情统一404；恢复/取消归档按当前 Test/Profile/Membership 重评，关闭不恢复。
8. 有 Stable 的测试项仍只解析 Test 且不读 Filter；普通 Catalog 仍按 UC024 运行，不改变其候选与 Filter。
9. 分页边界、同 Application 唯一、身份/runtime 绑定及签名篡改、空页 nextToken、500 扫描和字节预算续页、并发重新加入各有验证。
10. 来源悬空、重复 ACTIVE、跨应用 Profile/Test、旧 History 回取、OAuth 配置/Review 漂移整次失败；与替换、clear、Profile 批准、移除、门禁和清理并发只返回一致快照。
11. HTTP/gRPC/生成客户端正确返回可用与不可用卡片并设置 no-store；查询无外部调用、领域写入或敏感 telemetry。

### 变更记录

- 2026-10-12：在 UC036/037 提案完成后建立本人测试参与查询提案；建议在线 ACTIVE Membership 保留暂不可用卡片，门禁隐藏、纯 Test 目标和无 Filter。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；按本人资格、正常不可用卡片、在线门禁隐藏和纯 Test 解析边界交付。

## 业务规则（UC-APP-038 权威正文）

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-011 -->
### BR-CAT-011：本人 ACTIVE Membership 候选

测试参与查询仅由可信 USER 的 ACTIVE Membership 建立候选，不要求 Stable，不因管理员/Reviewer/Developer 身份隐式参与。ACTIVE/AVAILABLE/UNARCHIVED gate 必须成立，列表隐藏正常不合格项，详情统一 NOT_FOUND。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-012 -->
### BR-CAT-012：参与记录与可运行状态分离

通过资格和 gate 的候选，即使无公开资料、无 exact-major Test 或宿主缺能力，也保留参与卡片并返回确定的 availability。正常缺资料优先于无 Test、缺能力；有损坏指针时 INTERNAL。availability 不持久化、不新增 Membership 状态。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-013 -->
### BR-CAT-013：纯 Test 目标且不执行 Filter

READY 只来自符合 UC012 语义的 Test 目标，不回退其他 major/Grey/Stable。该入口不读取、分发或执行 Filter，即使 Application 也具有 Stable；普通 Catalog 继续遵守 UC024。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-014 -->
### BR-CAT-014：最小参与投影

列表和详情返回同一 item，仅含本人 episode 身份/加入时间、当前批准公开 Profile、可用性与必要 Test descriptor。不可用时不返回 launchTarget；不公开技术名称、未审核资料、管理员、其他 Tester、链接、OAuth credential 或审核事实。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-015 -->
### BR-CAT-015：身份与宿主绑定的分页

列表按 ApplicationId 升序 keyset，token 防篡改并绑定身份、规范化宿主上下文、查询种类和扫描位置；每页重新检查资格，不返回总数、不冻结跨页 snapshot。预算终止不得跳过未返回的合法项。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-016 -->
### BR-CAT-016：测试查询只读快照与失败关闭

每页/详情内资格、在线门禁、公开资料与 Test 运行事实来自同一只读 snapshot；复用批量解析而非逐 item RPC/事务。已读损坏整次 INTERNAL，不降级为正常 unavailable；不修复、不写栅栏、不调用外部业务依赖。

<!-- 权威位置: use-cases/UC-APP-038-query-my-test-applications.md#br-cat-017 -->
### BR-CAT-017：清空、移除和门禁后的可见性

Test clear 保留在线 ACTIVE Tester 的 unavailable card，Test 重设后按当前事实变为 READY；移除令旧 episode 不可查询，再加入使用新 episode。暂停/归档/关闭隐藏整个 item，解除可恢复 gate 后重新检查当前事实。既有已返回数据不形成租约，响应与错误均 private, no-store。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-025`

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010 -->
### BR-APP-010：注销个人状态清理

ACCOUNT_CLOSURE 的准备及永久 sealed 同时阻止 Tester Join 新增个人状态；DEVELOPER_WITHDRAWAL 仍允许普通 Tester 加入。创建/Join 与 Prepare 共用账号栅栏，涉及 Application coordination fence 时统一顺序 account→Application。

COMMITTED ACCOUNT_CLOSURE 后以有界批次清理该 testerAuthId 的全部 ACTIVE/REMOVED membership episode，并在各 Application coordination fence 内处理，保证人数计数及并发移除一致；其他用户不受影响。零应用账号的 creation quota 可以删除。仅在扫描为空并确认不可重建时标为 COMPLETE。

application_filters/filter_revisions 是应用公开 Filter，不是用户偏好，不能删除。保留 Application、Version、Review、Publication 及历史 createdBy/submittedBy/reviewer 等归因；当前没有独立个人偏好 collection，禁止凭名称猜测清理表。未来新增个人数据需显式纳入清单。

### 来自 `UC-APP-028`

<!-- 权威位置: use-cases/UC-APP-028-suspend-and-restore-application.md#br-app-031 -->
### BR-APP-031：权威读取的即时平台门禁

暂停提交后开始的 Catalog、启动解析、TEST descriptor、Tester Join 和 OAuth provider 权威读取必须观察 SUSPENDED 并失败，不得用进程缓存或旧查询投影延长成功。提交前已返回结果受各自 no-store、snapshot 和凭据时限约束，不能被描述为已经从客户端撤回。

### 来自 `UC-APP-033`

<!-- 权威位置: use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-053 -->
### BR-APP-053：整 Application 在线门禁

ARCHIVED 提交后开始的普通与 test-only Catalog、启动解析、TEST descriptor、Tester Join 和 UC019 五个 OAuth provider 权威读取必须失败关闭。共同在线前提还要求 lifecycle ACTIVE 且平台 AVAILABLE；任何一个门禁关闭都不能被另一个操作越过。

### 来自 `UC-APP-024`

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-004 -->
### BR-CAT-004：最小公开 Profile

Catalog 只返回当前已发布 Profile 的 revision 身份和 displayName、description、icon；不返回技术名称、管理员、作者、Reviewer、审核、策略或历史资料。

### 来自 `UC-APP-016`

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030 -->
### BR-PRF-030：批准后自动公开

APPROVE 必须提供 Reviewer 作出决定时观察到的 `expectedCurrentPublishedProfileRevisionId`，其值是某个 ProfileRevision ID 或明确的 `NONE`。它必须与当前指针匹配，再与以下变化处于同一原子边界：

```text
ProfileRevision.reviewStatus = APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = profileRevisionId
```

管理员不需要第二次 Publish 操作。指针前置值使两个针对不同 ProfileRevision 的并发批准不会静默相互覆盖；后一个 Reviewer 必须重新读取已改变的公开资料后再决定。旧的当前公开 Revision 保留 APPROVED 状态和审核历史，但首版不提供重新选择它或回滚资料的命令。

资料自动公开不创建 stable Version。没有兼容 stable 槽位时，Application 仍不进入普通用户候选目录。

### 来自 `UC-APP-036`

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-036 -->
### BR-PUB-036：清空后的解析与并发顺序

clear 提交后的新权威读取不再取得该 major 的 Test 目标，纯 Test 失败，统一解析按既有 Grey/Stable 规则继续。变更与所有槽位写入、转让和关闭具有明确先后顺序；不得从旧 History 恢复 Test，或破坏其他槽位的 History 校验。

### 来自 `UC-APP-012`

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001 -->
### BR-RUN-001：Tester 授权

解析者必须是该 Application 的 ACTIVE Tester：

```text
membership.applicationId = applicationId
membership.testerAuthId = authenticated authId
membership.status = ACTIVE
```

Developer、admin 或 Reviewer 身份都不会隐式授予测试启动资格。admin 只有显式加入 Tester 列表后才能解析。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-002 -->
### BR-RUN-002：按 exact RPC major 解析

只读取业务键恰好为 `(applicationId, hostRpcApiMajor)` 的 Publication。不存在时返回不可用：

- 不扫描其他 major。
- 不根据 Version range 猜测某个 Publication。
- 不使用 clientBuildVersion、platform、target 或 versionLabel 作为分区键。

客户端强制升级策略属于客户端发布边界；App Center 只对调用时实际 major 作出解析。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003 -->
### BR-RUN-003：test 槽位优先且不回退

本用例只返回 Publication.testVersionId：

- 不读取或回退到 grey/stable。
- 不从全部 APPROVED Version 中自动挑选最新 sequence。
- 不因为调用者是 Tester 就改变 Publication。

如果 testVersionId 不存在或失去资格，本次 test 解析失败。未来统一启动解析可以定义 test/grey/stable 优先级，但不能隐式改变本用例。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-004 -->
### BR-RUN-004：Version 一致性与发布资格

被解析 Version 必须：

- 属于同一 Application。
- 当前 reviewStatus=`APPROVED`。
- RPC range 覆盖 hostRpcApiMajor。
- 受审核内容与发布槽位设置时的批准事实保持一致。

发现悬空 testVersionId、跨 Application 引用、失去批准资格或内容漂移时不得返回 launchUrl，并必须产生内部一致性告警。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005 -->
### BR-RUN-005：Capabilities 覆盖

宿主能力必须满足集合包含关系：

```text
Version.requiredCapabilities ⊆ hostCapabilities
```

宿主可以声明额外能力。缺少能力时返回稳定排序的 missingCapabilities；optional/required scopes 不属于宿主 capabilities，不参与该集合判断。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-006 -->
### BR-RUN-006：启动描述

成功结果只包含启动当前 test Version 所需的事实：

```text
TestLaunchDescriptor {
  applicationId
  publicationId
  publicationRevision
  rpcApiMajor
  versionId
  versionLabel
  launchUrl
  rpcApiMinVersion
  rpcApiMaxVersionExclusive
  requiredCapabilities
  requiredScopes
  optionalScopes
}
```

Descriptor 不包含 client secret、Tester 列表、审核备注、其他 Version 或其他 RPC major 的 Publication。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-007 -->
### BR-RUN-007：一致快照与并发

Membership、Publication 和 Version 必须来自一个逻辑一致的解析快照：

- 移除先于解析快照可见：解析失败。
- 解析快照先于移除：本次可以成功，后续解析失败。
- Publication 替换先于快照：返回新 testVersionId 和对应 revision。
- 快照先于替换：返回旧 testVersionId 和旧 revision，本次结果仍有效。

本用例不承诺响应发出后目标永远不变，也不创建运行租约。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-008 -->
### BR-RUN-008：只读且不做同步外部复检

解析不得修改 Membership、Publication、Version、Review 或 History，也不写领域“访问次数”。技术观测日志不属于领域事实。

解析不调用 Auth Scope Catalog、不请求 launchUrl、不执行 DNS/公网 HTTPS 预检。发布时复检和未来持续监控负责这些保证，避免把外部依赖加入启动热路径。

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
- `UC-APP-028`（use-cases/UC-APP-028-suspend-and-restore-application.md）：目标与范围、参与者与依赖、输入、输出与 API 草图、正交状态模型、暂停流程、恢复流程、暂停期间的行为、OAuth 在线检查与残余窗口、领域与数据模型、错误语义、并发与验收场景、实现依赖与启用边界、变更记录
- `UC-APP-033`（use-cases/UC-APP-033-archive-and-unarchive-application.md）：设计结论、目标与范围、参与者与授权、输入、输出与 API 草图、正交状态模型、归档流程、取消归档流程、ARCHIVED 期间的行为、OAuth 在线检查与残余窗口、领域与数据模型、错误语义、并发与验收场景、实现依赖与交付边界、变更记录
- `UC-APP-024`（use-cases/UC-APP-024-query-public-application-catalog.md）：目标与范围、已有依赖与组合边界、输入与身份、普通公开候选资格、目标解析与 Filter 组合、公开结果模型、列表、排序与分页、列表主流程、详情主流程、错误与部分结果、最小查询模型与持久化影响、API 草图、验收场景、依赖检查与待确认设计选择、后续设计顺序、变更记录
- `UC-APP-016`（use-cases/UC-APP-016-decide-application-profile-revision-review.md）：目标与边界、参与者与输入、成功结果、主流程、失败结果、领域模型影响、验收场景、后续方向、实现依赖与交付边界、API 实现契约
- `UC-APP-036`（use-cases/UC-APP-036-clear-test-publication-slot.md）：设计结论、目标与范围、参与者与授权、输入与 API 草图、主流程与 no-op、清空前检查的边界、PublicationHistory 与迁移、在线效果与 OAuth 边界、并发与错误、引用规则与实现输入、验收与交付边界、变更记录
- `UC-APP-012`（use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md）：目标与范围、业务边界、输入与身份、主流程、异常流程、最小查询模型、用例端口、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-038-query-my-test-applications.md` | 214 | `a67eafb9221d` |
| `use-cases/UC-APP-025-coordinate-account-owner-exit.md` | 65 | `730a0ecc6a28` |
| `use-cases/UC-APP-028-suspend-and-restore-application.md` | 269 | `155e654469e7` |
| `use-cases/UC-APP-033-archive-and-unarchive-application.md` | 283 | `e9e406a93d2d` |
| `use-cases/UC-APP-024-query-public-application-catalog.md` | 338 | `88484d65cdb4` |
| `use-cases/UC-APP-016-decide-application-profile-revision-review.md` | 312 | `32bcd54ca110` |
| `use-cases/UC-APP-036-clear-test-publication-slot.md` | 176 | `ee3e0a6ce93b` |
| `use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md` | 403 | `6db4e23c15a2` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
