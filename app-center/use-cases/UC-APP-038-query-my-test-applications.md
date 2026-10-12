# UC-APP-038：查询我参与的测试 Application

状态：`ACCEPTED`

## 设计结论

> 已认证用户可以分页查询自己拥有 ACTIVE Tester Membership 的在线 Application，并读取其中一个的测试详情。结果展示当前已批准公开资料和 Test 可用性；有兼容 Test 时只返回 Test 启动目标，暂时无目标时保留参与卡片并说明原因。

候选来自当前用户的 Membership，不要求 Stable。已有 Stable 的 Application 也可出现在此入口；它与 [UC024 普通 Catalog](UC-APP-024-query-public-application-catalog.md) 独立，两个入口的候选资格和使用目的不同。

保留“已经参与、暂时不可启动”的卡片，因为 [UC009](UC-APP-009-join-application-as-tester.md) 允许先加入、后设置 Test，[UC036](UC-APP-036-clear-test-publication-slot.md) 清空时保留 Membership。用户应能区分失去资格与等待开发者发布。资料尚未公开时不使用技术名称或未审核资料作为替代。

暂停、归档、CLOSING/CLOSED 仍遵守既有在线门禁：列表隐藏、详情统一 NOT_FOUND，不返回占位卡片或目标。ACTIVE Membership 保留不意味着绕过这些门禁。产品已审核接受本设计。

## 目标与范围

交付 ListMyTestApplications 与 GetMyTestApplication，负责本人资格、运行输入、私有分页、当前公开 Profile、纯 Test 解析和不可用状态投影。

不负责主动退出、加入或移除 Tester、历史参与记录、其他用户/管理员查询、Stable/Grey 启动回退、服务端或客户端 Filter、邀请凭证、Auth 资料、WebView/session/token、搜索排序推荐或通知。管理员未显式加入不会自动出现在列表。

这是独立测试参与查询，不把 test-only 应用混入普通 Catalog，不保存物化可见列表。UC037 管理查询的权限与历史可见性不授予本用例。

## 身份、候选与门禁

身份必须为可信 USER，authId 只从认证上下文取得；developerStatus、Reviewer 或平台权限不参与授权。匿名和无效凭证返回认证失败，不能降级到公开查询。

候选满足：

1. 当前用户在该 Application 下存在唯一 ACTIVE Membership。
2. Application 存在，lifecycleStatus=ACTIVE。
3. platformAvailabilityStatus=AVAILABLE，archiveStatus=UNARCHIVED。

使用 [UC028](UC-APP-028-suspend-and-restore-application.md) 和 [UC033](UC-APP-033-archive-and-unarchive-application.md) 的共同在线门禁。不存在、没有 ACTIVE episode、REMOVED、暂停、归档或关闭等正常不合格项在列表跳过，详情统一 MyTestApplicationNotFound；不能通过详情区分他人应用、移除和管理门禁。

Membership 缺失 Application 属于内部悬空关系，列表已扫描到这种关系整页失败；直接详情首先按正常不存在/无资格统一隐藏。对通过 gate 的候选须批量验证 Membership 形状和加入来源链接的同 Application 归属；来源链接后来被撤销仍合法。已读重复 ACTIVE episode、缺失或跨应用来源等关系损坏失败关闭。账号个人状态清理依 [BR-APP-010](UC-APP-025-coordinate-account-owner-exit.md#br-app-010)，已清理记录不恢复。

## 输入与 API 草图

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

path applicationId 为 UUIDv7；运行字段沿用 [UC012 输入](UC-APP-012-resolve-test-launch-target-for-tester.md#输入与身份) 的 major 正整数、capability 格式和集合去重排序。列表必须携带 runtime。HTTP 不接受 query-string 覆盖正文，身份、membershipId、channel、versionId、Filter 结果不能由请求指定。

详情 POST 因为也需宿主运行上下文；查询保持只读。两种 transport 共享结果与错误，所有成功、不可用卡片、空页与领域错误均使用 `Cache-Control: private, no-store`。

## 参与卡片与可用性

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

列表项与详情使用同一投影。membership 仅返回调用者自己的 episode 身份和时间，不返回 testerAuthId、加入来源链接、操作人或其他 Tester。profile 仅来自当前公开指针，批准事实与投影沿用 [BR-CAT-004](UC-APP-024-query-public-application-catalog.md#br-cat-004)；不返回技术名称、管理员、作者、未公开资料或审核内容。

在已通过资格和在线门禁的 snapshot 内，按以下顺序投影：

| 当前事实 | availability | profile | launchTarget | missingCapabilities |
| --- | --- | --- | --- | --- |
| 没有 currentPublishedProfileRevisionId | PROFILE_REQUIRED | 无 | 无 | 空 |
| 有有效公开资料，但 exact-major Publication 或 Test 指针不存在 | TEST_TARGET_UNAVAILABLE | 有 | 无 | 空 |
| 有有效公开资料/批准 Test，但宿主缺少必需 capabilities | HOST_CAPABILITIES_INSUFFICIENT | 有 | 无 | 稳定排序的缺少能力 |
| 有有效公开资料、批准兼容 Test 且能力满足 | READY | 有 | 有 | 空 |

availability 是当次查询投影，不是新的持久化业务状态。PROFILE_REQUIRED 可出现在加入先于首次公开资料的合法阶段；客户端可使用本地通用文案表示等待就绪，服务端不能回退技术名称或未审核 displayName。测试应用当前不支持请求 major 时等价于没有 exact-major Test；不扫描其他 major。

有非空 Profile/Test 指针而目标缺失、跨 Application、非 APPROVED、snapshot 漂移或 range 不覆盖该 Publication major，属于损坏，不能映射为正常不可用卡片。各阶段只需读取当前阶段相关事实；不要求为一个已被门禁排除的候选继续读取私有运行内容，也不全量检查所有未选槽位。

READY 的 launchTarget 复用 [UC012 / TestLaunchDescriptor](UC-APP-012-resolve-test-launch-target-for-tester.md#最小查询模型)，包含当前 exact-major Test 的身份、revision、launch URL、兼容范围和 scopes 声明。不存在 Stable/Grey 回退：即使同一应用在普通 Catalog 可运行，测试入口的空/不兼容 Test 仍返回上述不可用状态。

不会读取或分发 Filter。该行为由入口语义决定，不能因为 Application 已有 Stable 就改成普通 Catalog Filter；READY 仅意味着可按当前 Test 事实启动，不代表已取得 Auth consent/token 或运行租约。

## 解析复用与查询快照

运行校验复用 UC012 的 ACTIVE Membership、exact-major Test、最近相关 Test History、批准 Version/Review/OAuth 配置一致性及 capability 子集语义。当前公开 Profile 的有效性沿用已接受的 Profile/Review 规则。查询不调用公开 UC012 RPC 再逐项拼接结果；应抽取或复用同一批量解析核心，在一个页面 snapshot 内加载和组合。

UC012 自身保留现有“无 Test/缺能力则错误”的单目标 RPC；本用例显式把这两种正常结果映射为 unavailable card，不修改其 RPC。损坏关系在本入口统一 MyTestApplicationStateInconsistent（500/INTERNAL）；不能把 UC012 的内部不一致 UNAVAILABLE 错误误当作普通无目标。

UC036 被接受并实现后，最近 CLEAR_TEST_VERSION 与空 Test 必须一致；不能从旧 SET_TEST 历史取得运行目标。Stable/Grey 变化后的共享 Publication revision 不表示 Test 批准依据丢失，校验最近相关 Test action。若 UC036 未接受，本查询也可以对既有 stable-only/EMPTY Publication 返回 TEST_TARGET_UNAVAILABLE。

每个列表页或详情用一个 MongoDB majority read-only snapshot，同时确认 Membership、Application 在线门禁和所需 Profile、Publication/History、Version/Review/OAuth。与 Test clear/replace、Profile 批准、Membership 移除/加入、暂停/归档、关闭和账号清理并发时，必须返回提交前或后的完整事实组合。

只读查询不写 coordinationRevision、访问历史、asOf 记录、计数或持久化可用性；不调用 Scope Catalog、DNS preflight、Auth 用户资料或 OAuth provider。技术观测不记录可信 authId、pageToken、完整 URL/scopes、凭证或返回正文。

## 排序、分页与预算

按 ApplicationId 二进制升序扫描当前 authId 的 ACTIVE Membership，确保同一 Application 最多一项。pageToken 表示最后已消费的 ApplicationId，不使用 offset 或最近使用/名称/可用性排序。

本查询读取的持久化 UUID ID 使用现有正常写入生成的规范小写 UUIDv7 字符串；固定格式的 simple 字符串顺序等价于 UUID 二进制顺序。已读非规范表示按 StateInconsistent 失败，不规范化、重排或修复历史记录；API path UUID 的既有解析与规范化行为不变。

token 必须签名或等效防篡改，并绑定版本、可信 authId、规范化 major/capabilities 指纹、查询种类和最后扫描位置；建立独立于 UC037/UC034 的签名 domain。换用户、换 major、改变 capability 集合、篡改位置或非法 canonical 编码拒绝；重复/重排 capabilities 规范化后可继续，pageSize 可改变。token 不承载资格，每页重新读取 ACTIVE Membership 和在线门禁。

pageSize 默认20、范围1–100。不返回 totalCount。首版每页最多扫描500个 ACTIVE candidate，响应预算建议3 MiB：到扫描上限可返回少于 pageSize 甚至空页并提供 nextPageToken；到字节预算时 token 停在最后已消费项之前或之处，不能越过尚未返回的合法 item。单个合法 item 必须能单独返回。

被移除或 gate 隐藏项仍占扫描位置；PROFILE_REQUIRED/TEST_TARGET_UNAVAILABLE/能力不足属于返回 item，占 pageSize。新加入到已扫描位置之前的 Application 只能在下一轮刷新出现；跨页不冻结 snapshot，重新加入得到新的 membershipId，不保证该轮分页再次展示同一 Application。

## 主流程与错误

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

## 业务规则

<a id="br-cat-011"></a>
### BR-CAT-011：本人 ACTIVE Membership 候选

测试参与查询仅由可信 USER 的 ACTIVE Membership 建立候选，不要求 Stable，不因管理员/Reviewer/Developer 身份隐式参与。ACTIVE/AVAILABLE/UNARCHIVED gate 必须成立，列表隐藏正常不合格项，详情统一 NOT_FOUND。

<a id="br-cat-012"></a>
### BR-CAT-012：参与记录与可运行状态分离

通过资格和 gate 的候选，即使无公开资料、无 exact-major Test 或宿主缺能力，也保留参与卡片并返回确定的 availability。正常缺资料优先于无 Test、缺能力；有损坏指针时 INTERNAL。availability 不持久化、不新增 Membership 状态。

<a id="br-cat-013"></a>
### BR-CAT-013：纯 Test 目标且不执行 Filter

READY 只来自符合 UC012 语义的 Test 目标，不回退其他 major/Grey/Stable。该入口不读取、分发或执行 Filter，即使 Application 也具有 Stable；普通 Catalog 继续遵守 UC024。

<a id="br-cat-014"></a>
### BR-CAT-014：最小参与投影

列表和详情返回同一 item，仅含本人 episode 身份/加入时间、当前批准公开 Profile、可用性与必要 Test descriptor。不可用时不返回 launchTarget；不公开技术名称、未审核资料、管理员、其他 Tester、链接、OAuth credential 或审核事实。

<a id="br-cat-015"></a>
### BR-CAT-015：身份与宿主绑定的分页

列表按 ApplicationId 升序 keyset，token 防篡改并绑定身份、规范化宿主上下文、查询种类和扫描位置；每页重新检查资格，不返回总数、不冻结跨页 snapshot。预算终止不得跳过未返回的合法项。

<a id="br-cat-016"></a>
### BR-CAT-016：测试查询只读快照与失败关闭

每页/详情内资格、在线门禁、公开资料与 Test 运行事实来自同一只读 snapshot；复用批量解析而非逐 item RPC/事务。已读损坏整次 INTERNAL，不降级为正常 unavailable；不修复、不写栅栏、不调用外部业务依赖。

<a id="br-cat-017"></a>
### BR-CAT-017：清空、移除和门禁后的可见性

Test clear 保留在线 ACTIVE Tester 的 unavailable card，Test 重设后按当前事实变为 READY；移除令旧 episode 不可查询，再加入使用新 episode。暂停/归档/关闭隐藏整个 item，解除可恢复 gate 后重新检查当前事实。既有已返回数据不形成租约，响应与错误均 private, no-store。

## 索引与交付边界

通过显式 migration 增加本人 ACTIVE 扫描索引：

```text
application_tester_memberships:
  (testerAuthId ASC, status ASC, applicationId ASC, membershipId ASC)
```

保留既有 `(applicationId, testerAuthId)` ACTIVE 唯一约束。其他事实复用当前 pointer/ID/review/history 索引；不新增领域实体或集合，不把参与列表保存到 Auth。migration 编号在接受/开工时对齐实际 ledger。

接受后生成 brief，交付独立 API、Catalog query port/read model、批量 snapshot adapter、索引、HTTP/gRPC 和真实 Mongo E2E；最低门禁 `make check-full`。查询不改变 Auth runtime provider 或签发规则，不需新增 Auth API。UC036/037 与本 UC 按请求顺序设计；实现可复用 036 的新 History 支持，037 的管理员读权不能替代本人资格。

## 引用规则与实现输入

批量纯 Test 解析复用 [BR-RUN-001](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001)、[BR-RUN-002](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-002)、[BR-RUN-003](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003)、[BR-RUN-004](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-004)、[BR-RUN-005](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005)、[BR-RUN-006](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-006)、[BR-RUN-007](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-007)、[BR-RUN-008](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-008)；公开资料批准一致性依据 [BR-PRF-030](UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)。在线门禁复用 [BR-APP-031](UC-APP-028-suspend-and-restore-application.md#br-app-031)、[BR-APP-053](UC-APP-033-archive-and-unarchive-application.md#br-app-053)，Test clear 复用 [BR-PUB-036](UC-APP-036-clear-test-publication-slot.md#br-pub-036)。

## 验收场景

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

## 变更记录

- 2026-10-12：在 UC036/037 提案完成后建立本人测试参与查询提案；建议在线 ACTIVE Membership 保留暂不可用卡片，门禁隐藏、纯 Test 目标和无 Filter。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；按本人资格、正常不可用卡片、在线门禁隐藏和纯 Test 解析边界交付。
- 2026-10-12：开工复核明确规范小写持久化 UUID 的读取边界，保持索引 keyset 与 UUID 二进制顺序一致，不改变 API UUID 解析行为。
