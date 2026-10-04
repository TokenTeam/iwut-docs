# UC-APP-024：查询普通 Application Catalog 列表与详情

状态：`PROPOSED`

## 目标与范围

> 官方客户端使用实际宿主 RPC API major、capabilities 和可选可信用户身份，查询由 Stable 支撑的普通公开 Application 列表或单项详情；App Center 为每个结果组合当前公开 Profile、UC-APP-023 解析的唯一启动目标和当前 Application Filter，客户端随后使用本地用户信息执行 Filter。

本用例负责：

- 定义普通公开 Catalog 的候选资格。
- 分页返回候选 Application 的最小公开资料、唯一启动目标和 Filter 投影。
- 按 applicationId 返回与列表项相同语义的普通公开详情。
- 复用 [UC-APP-023](UC-APP-023-resolve-unified-launch-target.md) 的 exact-major `TEST > GREY > STABLE` 选择，不建立第二套运行解析规则。
- 以可选可信身份参与 Tester 与 Grey 判断；匿名用户只得到 Stable 目标。
- 在一个查询快照内组合 Profile、Publication、Version/Review、Membership 和 Filter 当前事实。

本用例不负责：

- 在服务端执行 Filter、接收用户资料字段或保存用户级命中结果。
- 把 test-only Application 混入普通公开目录；它们进入后续“我参与的测试”查询。
- 返回管理资料、技术名称、adminId、Reviewer、审核意见、Filter 发布者或其他槽位。
- 搜索、分类、推荐、人工排序、热度、置顶、总数统计或个性化排名。
- 修改 Profile、Publication、Version、Membership、Filter 或任何 revision。
- 发现 OAuth clientId、签发 token、建立运行 session 或启动 WebView。
- 定义 Application 归档、管理员停用或平台 suspension；这些状态建立后必须加入共同候选资格。

## 已有依赖与组合边界

- [UC-APP-016](UC-APP-016-decide-application-profile-revision-review.md) 提供当前已批准并公开的 Profile pointer。
- [UC-APP-020](UC-APP-020-manage-stable-publication-slot.md) 定义 Stable 是普通公开 Catalog 的发布基线。
- [UC-APP-021](UC-APP-021-manage-grey-rollout.md) 定义已登录用户的确定性 Grey cohort。
- [UC-APP-022](UC-APP-022-manage-application-filter.md) 定义 Application 级当前 Filter、默认 `ALLOW_ALL` 和客户端求值边界。
- [UC-APP-023](UC-APP-023-resolve-unified-launch-target.md) 定义单 Application 的可信可选身份、exact-major、capability 回退、唯一目标和不变量失败关闭语义。

Catalog 是只读组合能力，不成为上述事实的新权威来源，也不保存物化的“当前可见应用列表”。普通候选资格由 Stable 建立；Tester 或 Grey 只改变候选 Application 的启动目标，不让缺少 Stable 的 Application 进入本查询。

## 输入与身份

共享运行输入：

```text
CatalogRuntimeQuery {
  hostRpcApiMajor: int32
  hostCapabilities: []CapabilityName
}
```

列表输入：

```text
ListPublicApplicationsQuery {
  runtime: CatalogRuntimeQuery
  pageSize?: int32
  pageToken?: string
}
```

详情输入：

```text
GetPublicApplicationQuery {
  applicationId: ApplicationId
  runtime: CatalogRuntimeQuery
}
```

可信上下文：

```text
OptionalAuthenticatedUserIdentity {
  authId?: string
}
```

- 没有认证凭证表示匿名调用。
- 已提供的凭证必须完整验证；无效、过期、空白、多值或歧义凭证不能降级为匿名。
- authId 不得来自 path、query、body、cookie 内的自由字段。
- `hostRpcApiMajor` 和 `hostCapabilities` 完全沿用 UC023 的校验与规范化语义。
- 请求不能指定 channel、versionId、profileRevisionId、filterRevisionId、Tester、bucket 或 Filter 命中结果。

`pageSize` 默认 20，范围 1–100。`pageToken` 是服务端产生的 opaque keyset cursor，至少携带格式版本、上一扫描位置和规范化后的 RPC major/capabilities 指纹。格式、版本或查询指纹不匹配时返回 INVALID_ARGUMENT。cursor 不携带 authId，也不授予任何读取权限；每一页都使用本次请求的可信身份重新解析目标。客户端即使改变扫描位置也只能跳过普通公开候选，不能借 cursor 取得私有事实。

## 普通公开候选资格

一个 Application 进入本查询的候选集合，必须在同一查询快照中满足：

1. Application 存在。
2. `currentPublishedProfileRevisionId` 指向同一 Application 的有效 APPROVED ProfileRevision，且其批准事实一致。
3. exact `(applicationId, hostRpcApiMajor)` Publication 存在有效 stable pointer。
4. Stable Version 属于同一 Application、保持 APPROVED、批准 snapshot 一致、RPC range 覆盖请求 major，并且 `requiredCapabilities ⊆ hostCapabilities`。
5. 当前不存在已建模的归档、停止分发或 suspension 状态。首版尚无这些字段，因此本条暂时只保留扩展位置。

缺少公开 Profile、缺少 exact-major Publication、没有 Stable 或 Stable 正常但不兼容当前宿主，都是“不进入普通候选集”，不是错误。存在 pointer 但指向损坏、跨 Application、非 APPROVED 或 snapshot 漂移的事实属于内部不变量异常。

Grey 不单独建立公开资格。ACTIVE Tester 即使拥有兼容 Test，也不能通过本查询看到一个没有合格 Stable 基线的 test-only Application。

## 目标解析与 Filter 组合

候选资格成立后，Catalog 使用同一可信身份和运行输入复用 UC023：

```text
eligible stable-backed Application
  -> UC023 resolve(TEST > GREY > STABLE)
  -> one LaunchTargetDescriptor
```

因此：

- ACTIVE Tester 可以在普通 Catalog 项中得到 TEST 启动目标。
- 非 Tester 的已登录用户命中 Grey 时得到 GREY，否则得到 STABLE。
- 匿名用户得到 STABLE。
- 高优先级目标仅因 capability 不足时按 UC023 回退。
- 任何实际读取到的运行不变量损坏按 UC023 失败关闭。

普通 Catalog 的可见性仍由 Stable-backed 候选资格建立。即使 Tester 的最终启动目标是 TEST，这一项仍属于普通公开 Catalog，因此返回并执行当前 Filter。后续独立的 test-only“我参与的测试”入口不执行 Filter；两者不能用 selected channel 判断是否分发规则。

Filter 组合规则：

- ApplicationFilter 不存在时返回合成的 revision 0、`ALLOW_ALL`，不写数据库。
- 当前 Revision 为 `ALLOW_ALL` 时不返回 rule。
- 当前 Revision 为 `RULE` 时原样返回 `profile-filter-v1` 规则树。
- 不返回 publishedBy、publishedAt、历史 Revision 或管理 OCC 输入。
- current pointer、Revision、schemaVersion、mode 或规则内容损坏时返回内部不变量异常，不能静默改成 `ALLOW_ALL`。

App Center 不执行规则。官方客户端按 [BR-FLT-006](UC-APP-022-manage-application-filter.md#br-flt-006) 求值；未知 schema 或节点 fail closed，只影响客户端展示，不授予或撤销服务端运行权限。

## 公开结果模型

列表项和详情共用同一个投影：

```text
PublicApplicationCatalogItem {
  applicationId
  profile: {
    profileRevisionId
    displayName
    description?
    icon?
  }
  launchTarget: LaunchTargetDescriptor
  filter: {
    revision
    filterRevisionId?
    schemaVersion: "profile-filter-v1"
    mode: RULE | ALLOW_ALL
    rule?
  }
}
```

Profile 不包含 application 技术名称、adminId、createdBy、Review、policy、checks 或 decision。LaunchTargetDescriptor 沿用 UC023，不扩展为候选槽位集合。Filter 不包含发布者和历史。

列表结果：

```text
PublicApplicationCatalogPage {
  applications: []PublicApplicationCatalogItem
  nextPageToken?
}
```

不返回 totalCount。详情返回单个 `PublicApplicationCatalogItem`；它不是不同于列表项的第二种公开资料模型。

## 列表、排序与分页

- 服务端按 ApplicationId 的稳定二进制升序扫描 ordinary candidate，不能按 displayName、channel、Version label 或 Filter 内容排序。
- cursor 表示已扫描位置，而不是数组 offset；候选在并发变化时不保证跨页冻结快照。
- 每一页内部来自一个逻辑一致快照。跨页期间新发布、撤回、Profile/Filter 切换或 rollout 调整可在后续页或下一轮查询体现。
- 客户端不能假设跨页 total snapshot，也不能把 pageToken 用作长期同步位置。
- 服务端可以为避免无界扫描而在达到内部扫描预算后返回少于 pageSize、甚至空的 applications，同时给出 nextPageToken；客户端应继续请求直到 token 为空。
- 为控制最坏 Filter 体积，服务端还应在序列化前使用固定响应预算截断页面，并从最后已返回或已扫描位置继续。首版建议预算 3 MiB；单个按 UC022 约束合法的 item 必须能够单独返回。

pageSize 只限制 item 数量，不保证响应一定达到请求数量。扫描预算和字节预算属于稳定服务限制，不能因不同用户资料或 Filter 求值结果变化；服务端本身不掌握这些结果。

## 列表主流程

1. 验证可选可信身份、运行输入和分页输入；规范化 capabilities。
2. 从 exact-major 且有 stable pointer 的 Publication 集合按 ApplicationId keyset 扫描候选键。
3. 在一个页面快照中批量加载 Application、当前公开 Profile、Stable Version/Review、可选 Membership、Grey/Test 解析所需事实和当前 Filter。
4. 对每个扫描项检查普通公开候选资格；正常不合格项跳过。
5. 对合格项复用 UC023 目标选择语义并组合公开 Profile 与 Filter 投影。
6. 达到 pageSize、响应预算、扫描预算或数据末尾时停止，返回 items 和必要的 nextPageToken。
7. 不写访问日志领域事实，不调用 Auth Scope Catalog、目标 URL、OAuth provider 或用户资料服务。

## 详情主流程

1. 验证可选可信身份、applicationId 和运行输入。
2. 在一个逻辑一致快照中加载该 Application 的候选资格事实。
3. 不存在或正常不满足普通公开候选资格时，返回统一 `PublicApplicationNotFound`。
4. 资格成立后复用 UC023 解析唯一目标，并组合与列表项相同的 Profile 和 Filter 投影。
5. 任何 pointer、批准 snapshot 或当前 Filter 损坏时返回内部不变量异常。

详情不因为调用者知道 applicationId 就暴露 DRAFT/SUBMITTED/REJECTED Profile、test-only Publication、管理员、审核或 Filter 历史。

## 错误与部分结果

- 非法运行输入、pageSize、pageToken 或 applicationId：INVALID_ARGUMENT。
- 无效认证凭证：认证失败，不能降级为匿名。
- 列表没有候选：成功返回空数组。
- 详情不存在或不满足普通公开资格：`PublicApplicationNotFound`，HTTP 404 / gRPC NOT_FOUND。
- Profile、Publication、Version/Review 或 Filter 当前事实损坏：`ApplicationCatalogStateInconsistent`，HTTP 500 / gRPC INTERNAL。
- 存储或 snapshot 失败：内部失败。

首版不返回带 per-item errors 的部分成功。查询实际读取到内部不变量异常时，整页失败并产生不含身份、Filter 正文、seed 或私有槽位的安全告警；不能把损坏项静默隐藏成普通不合格。详情使用相同错误边界。

## 业务规则

<a id="br-cat-001"></a>
### BR-CAT-001：Stable 支撑的普通公开候选

普通 Catalog 只包含具有有效当前公开 Profile 和兼容 exact-major Stable 基线的 Application。Grey、Tester 或 APPROVED Version 本身不能建立普通公开资格；test-only Application 进入独立查询。

<a id="br-cat-002"></a>
### BR-CAT-002：可信可选身份

匿名调用只得到 Stable 目标；有效 authId 可以参与 Tester 和 Grey 判断。无效凭证不能降级，请求不能自报 authId、Tester、channel、cohort 或 Filter 命中。

<a id="br-cat-003"></a>
### BR-CAT-003：复用唯一运行解析

每个候选 Application 必须复用 UC023 的 exact-major `TEST > GREY > STABLE` 选择、capability 回退与不变量边界。列表和详情不得复制、简化或改写该优先级。

<a id="br-cat-004"></a>
### BR-CAT-004：最小公开 Profile

Catalog 只返回当前已发布 Profile 的 revision 身份和 displayName、description、icon；不返回技术名称、管理员、作者、Reviewer、审核、策略或历史资料。

<a id="br-cat-005"></a>
### BR-CAT-005：Filter 分发与客户端求值

每个普通 Catalog item 返回当前 Application Filter；不存在时合成 revision 0 `ALLOW_ALL`。即使启动目标因 Tester 资格解析为 TEST，该 item 仍按普通公开 Catalog 执行 Filter。App Center 不读取用户资料或执行规则。

<a id="br-cat-006"></a>
### BR-CAT-006：列表与详情同一投影

列表项和详情使用同一 PublicApplicationCatalogItem。详情不能通过 applicationId 绕过普通候选资格，列表也不使用缺字段的另一套运行或 Filter 语义。

<a id="br-cat-007"></a>
### BR-CAT-007：稳定 keyset 分页

列表按 ApplicationId 稳定升序并使用绑定查询边界的 opaque keyset cursor。每页内部一致，跨页不冻结全局 snapshot，不返回 totalCount；pageSize、扫描预算或响应字节预算均可使页面提前结束。

<a id="br-cat-008"></a>
### BR-CAT-008：一致快照与失败关闭

每个页面或详情内组合的 Application、Profile、Publication、Membership、Version/Review 和 Filter 来自一个逻辑一致快照。正常不合格项被排除；实际读取到的悬空、跨 Application、非批准或 snapshot/规则损坏返回 INTERNAL，不提供部分成功。

<a id="br-cat-009"></a>
### BR-CAT-009：批量只读热路径

列表不得为每个 item 发起外部网络调用或逐项开启独立数据库事务。实现应批量扫描和加载候选，并复用 UC023 的批量解析核心；查询不写领域访问事实。

<a id="br-cat-010"></a>
### BR-CAT-010：最小披露与私有缓存

响应不披露未选槽位、Tester Membership、Grey bucket/seed、Filter 发布者或审核事实。列表和详情均使用 `Cache-Control: private, no-store`，避免依赖身份的目标进入共享缓存。

## 最小查询模型与持久化影响

本用例不新增领域聚合或物化 Catalog 文档：

```text
Application
ApplicationProfileRevision(current APPROVED)
ApplicationPublication(exact major, stable-backed)
ApplicationTesterMembership(ACTIVE)?
ApplicationVersion + approved Review snapshot
ApplicationFilter + current ApplicationFilterRevision?
```

`PublicApplicationCatalogItem` 和 page token 都是读取结果，不持久化为业务事实。

实现需要为全局 exact-major Stable 候选扫描提供索引。建议预留 migration `0019_application_catalog_indexes`，只增加与 `(rpcApiMajor, applicationId)` keyset 扫描及 stable pointer 存在性匹配相符的索引，不改变现有 document schema。最终索引形状应由 explain 验证，禁止普通列表退化为对每个 Application 的 N+1 查询。

## API 草图

独立 API package 建议为 `app_center.v1.application_catalog`，service 为 `ApplicationCatalogService`：

```text
rpc ListPublicApplications(ListPublicApplicationsRequest)
rpc GetPublicApplication(GetPublicApplicationRequest)
```

HTTP：

```text
POST /v1/catalog/applications:search
POST /v1/catalog/applications/{applicationId}:get
```

使用 POST 是因为运行输入包含有界 capability 集合和 opaque cursor，不把身份或复杂数组编码进 URL。请求 body 只允许对应 query；未知字段和自报身份/目标字段拒绝。

列表成功返回 `200 OK` 和 page；详情成功返回 `200 OK` 和 item。所有响应设置：

```text
Cache-Control: private, no-store
```

Proto 可以复用 `app_center.v1.runtime_resolution.LaunchTargetDescriptor` 和 Application Filter 的 rule message，不能复制出语义相同但独立演进的结构。公开 Filter projection 需要独立 message，以排除管理资源中的 publishedBy/publishedAt。

## 验收场景

- 匿名列表只返回具有公开 Profile 和兼容 Stable 的 Application，并为每项返回 STABLE、Profile 和当前 Filter。
- 已登录用户命中 Grey 时得到 GREY；ACTIVE Tester 在同一个 Stable-backed Application 上得到 TEST；两者仍携带 Filter。
- test-only Application、没有公开 Profile、没有 exact-major Stable 或 Stable 缺少宿主 capability 时不进入普通列表，详情统一 404。
- Filter 不存在返回 revision 0 `ALLOW_ALL`；RULE 原样分发；客户端用户资料和求值结果不进入请求、日志或存储。
- current Profile、Stable pointer、批准 snapshot 或 Filter pointer 损坏时整页/详情返回 INTERNAL，不静默跳过或回退到旧事实。
- 分页按 ApplicationId 稳定；token 不能跨 major 或 capability 集合复用，身份资格在每页重新验证；无 totalCount。
- 并发切换 Profile、Stable/Grey/Test、Membership 或 Filter 时，每页/详情等价于一个明确 snapshot；跨页允许观察后续变化。
- pageSize、扫描预算和 3 MiB 响应预算均可提前截断页面，并提供不会丢失已扫描位置的 nextPageToken。
- 列表使用批量数据库读取，无逐 item 外部调用、无 N+1 transaction；真实 explain 使用预期索引。
- HTTP 与原生 gRPC 返回相同投影、排序、错误和可选身份语义。
- 响应不包含 adminId、技术名称、审核、Filter 发布者、其他槽位、Membership、seed、bucket 或 client secret。

## 依赖检查与待确认设计选择

已有数据依赖足够开始实现；UC016、UC020、UC021、UC022 和 UC023 均已完成当前后端范围。本用例不依赖 Auth 新增 API，也不依赖尚未设计的 Application disable/suspension。

接受前需要确认以下首版选择：

1. 普通目录严格要求兼容 Stable；test-only Application 只进入后续“我参与的测试”入口。
2. Stable-backed 普通项即使为 Tester 解析出 TEST，仍携带并执行普通 Catalog Filter。
3. 列表按 ApplicationId keyset 排序，无搜索、推荐、分类和 totalCount。
4. 读取到任一内部不变量异常时整页 500/INTERNAL，不返回部分结果。
5. pageSize 默认 20、最大 100，并使用建议 3 MiB 响应预算及内部扫描预算允许短页。

## 后续设计顺序

1. “我参与的测试”列表，允许没有 Stable 的 test-only Application，且不执行 Filter。
2. Application 管理查询与受控改名。
3. Application 归档、管理员停止分发和平台 suspension，统一进入 Catalog、UC023 和 OAuth provider 资格。
4. 搜索、分类、推荐或排名只在出现真实产品需求后建立独立模型。

## 变更记录

- 2026-10-04：建立 UC-APP-024 提案；定义 Stable-backed 普通列表/详情、公开 Profile、UC023 唯一目标、Filter 分发、keyset 分页与批量快照边界。
