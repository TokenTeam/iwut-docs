<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-024 --spec tools/brief-specs/UC-APP-024.json -->
# Brief — UC-APP-024：查询普通 Application Catalog 列表与详情

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-024` 查询普通 Application Catalog 列表与详情 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-CAT-001`–`BR-CAT-010`（10 条） |
| 外部引用 BR | `BR-FLT-006`（来自 `UC-APP-022`） |
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

### 目标与范围

> 官方客户端使用实际宿主 RPC API major、capabilities 和可选可信用户身份，查询由 Stable 支撑的普通公开 Application 列表或单项详情；App Center 为每个结果组合当前公开 Profile、UC-APP-023 解析的唯一启动目标和当前 Application Filter，客户端随后使用本地用户信息执行 Filter。

本用例负责：

- 定义普通公开 Catalog 的候选资格。
- 分页返回候选 Application 的最小公开资料、唯一启动目标和 Filter 投影。
- 按 applicationId 返回与列表项相同语义的普通公开详情。
- 复用 [UC-APP-023](../use-cases/UC-APP-023-resolve-unified-launch-target.md) 的 exact-major `TEST > GREY > STABLE` 选择，不建立第二套运行解析规则。
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

### 已有依赖与组合边界

- [UC-APP-016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md) 提供当前已批准并公开的 Profile pointer。
- [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 定义 Stable 是普通公开 Catalog 的发布基线。
- [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md) 定义已登录用户的确定性 Grey cohort。
- [UC-APP-022](../use-cases/UC-APP-022-manage-application-filter.md) 定义 Application 级当前 Filter、默认 `ALLOW_ALL` 和客户端求值边界。
- [UC-APP-023](../use-cases/UC-APP-023-resolve-unified-launch-target.md) 定义单 Application 的可信可选身份、exact-major、capability 回退、唯一目标和不变量失败关闭语义。

Catalog 是只读组合能力，不成为上述事实的新权威来源，也不保存物化的“当前可见应用列表”。普通候选资格由 Stable 建立；Tester 或 Grey 只改变候选 Application 的启动目标，不让缺少 Stable 的 Application 进入本查询。

### 输入与身份

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

### 普通公开候选资格

一个 Application 进入本查询的候选集合，必须在同一查询快照中满足：

1. Application 存在。
2. `currentPublishedProfileRevisionId` 指向同一 Application 的有效 APPROVED ProfileRevision，且其批准事实一致。
3. exact `(applicationId, hostRpcApiMajor)` Publication 存在有效 stable pointer。
4. Stable Version 属于同一 Application、保持 APPROVED、批准 snapshot 一致、RPC range 覆盖请求 major，并且 `requiredCapabilities ⊆ hostCapabilities`。
5. 当前不存在已建模的归档、停止分发或 suspension 状态。首版尚无这些字段，因此本条暂时只保留扩展位置。

缺少公开 Profile、缺少 exact-major Publication、没有 Stable 或 Stable 正常但不兼容当前宿主，都是“不进入普通候选集”，不是错误。存在 pointer 但指向损坏、跨 Application、非 APPROVED 或 snapshot 漂移的事实属于内部不变量异常。

Grey 不单独建立公开资格。ACTIVE Tester 即使拥有兼容 Test，也不能通过本查询看到一个没有合格 Stable 基线的 test-only Application。

### 目标解析与 Filter 组合

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

App Center 不执行规则。官方客户端按 [BR-FLT-006](../use-cases/UC-APP-022-manage-application-filter.md#br-flt-006) 求值；未知 schema 或节点 fail closed，只影响客户端展示，不授予或撤销服务端运行权限。

### 公开结果模型

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

### 列表、排序与分页

- 服务端按 ApplicationId 的稳定二进制升序扫描 ordinary candidate，不能按 displayName、channel、Version label 或 Filter 内容排序。
- cursor 表示已扫描位置，而不是数组 offset；候选在并发变化时不保证跨页冻结快照。
- 每一页内部来自一个逻辑一致快照。跨页期间新发布、撤回、Profile/Filter 切换或 rollout 调整可在后续页或下一轮查询体现。
- 客户端不能假设跨页 total snapshot，也不能把 pageToken 用作长期同步位置。
- 服务端可以为避免无界扫描而在达到内部扫描预算后返回少于 pageSize、甚至空的 applications，同时给出 nextPageToken；客户端应继续请求直到 token 为空。
- 为控制最坏 Filter 体积，服务端还应在序列化前使用固定响应预算截断页面，并从最后已返回或已扫描位置继续。首版建议预算 3 MiB；单个按 UC022 约束合法的 item 必须能够单独返回。

pageSize 只限制 item 数量，不保证响应一定达到请求数量。扫描预算和字节预算属于稳定服务限制，不能因不同用户资料或 Filter 求值结果变化；服务端本身不掌握这些结果。

### 列表主流程

1. 验证可选可信身份、运行输入和分页输入；规范化 capabilities。
2. 从 exact-major 且有 stable pointer 的 Publication 集合按 ApplicationId keyset 扫描候选键。
3. 在一个页面快照中批量加载 Application、当前公开 Profile、Stable Version/Review、可选 Membership、Grey/Test 解析所需事实和当前 Filter。
4. 对每个扫描项检查普通公开候选资格；正常不合格项跳过。
5. 对合格项复用 UC023 目标选择语义并组合公开 Profile 与 Filter 投影。
6. 达到 pageSize、响应预算、扫描预算或数据末尾时停止，返回 items 和必要的 nextPageToken。
7. 不写访问日志领域事实，不调用 Auth Scope Catalog、目标 URL、OAuth provider 或用户资料服务。

### 详情主流程

1. 验证可选可信身份、applicationId 和运行输入。
2. 在一个逻辑一致快照中加载该 Application 的候选资格事实。
3. 不存在或正常不满足普通公开候选资格时，返回统一 `PublicApplicationNotFound`。
4. 资格成立后复用 UC023 解析唯一目标，并组合与列表项相同的 Profile 和 Filter 投影。
5. 任何 pointer、批准 snapshot 或当前 Filter 损坏时返回内部不变量异常。

详情不因为调用者知道 applicationId 就暴露 DRAFT/SUBMITTED/REJECTED Profile、test-only Publication、管理员、审核或 Filter 历史。

### 错误与部分结果

- 非法运行输入、pageSize、pageToken 或 applicationId：INVALID_ARGUMENT。
- 无效认证凭证：认证失败，不能降级为匿名。
- 列表没有候选：成功返回空数组。
- 详情不存在或不满足普通公开资格：`PublicApplicationNotFound`，HTTP 404 / gRPC NOT_FOUND。
- Profile、Publication、Version/Review 或 Filter 当前事实损坏：`ApplicationCatalogStateInconsistent`，HTTP 500 / gRPC INTERNAL。
- 存储或 snapshot 失败：内部失败。

首版不返回带 per-item errors 的部分成功。查询实际读取到内部不变量异常时，整页失败并产生不含身份、Filter 正文、seed 或私有槽位的安全告警；不能把损坏项静默隐藏成普通不合格。详情使用相同错误边界。

### 最小查询模型与持久化影响

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

### API 草图

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

### 验收场景

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

### 依赖检查与待确认设计选择

已有数据依赖足够开始实现；UC016、UC020、UC021、UC022 和 UC023 均已完成当前后端范围。本用例不依赖 Auth 新增 API，也不依赖尚未设计的 Application disable/suspension。

接受前需要确认以下首版选择：

1. 普通目录严格要求兼容 Stable；test-only Application 只进入后续“我参与的测试”入口。
2. Stable-backed 普通项即使为 Tester 解析出 TEST，仍携带并执行普通 Catalog Filter。
3. 列表按 ApplicationId keyset 排序，无搜索、推荐、分类和 totalCount。
4. 读取到任一内部不变量异常时整页 500/INTERNAL，不返回部分结果。
5. pageSize 默认 20、最大 100，并使用建议 3 MiB 响应预算及内部扫描预算允许短页。

## 业务规则（UC-APP-024 权威正文）

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-001 -->
### BR-CAT-001：Stable 支撑的普通公开候选

普通 Catalog 只包含具有有效当前公开 Profile 和兼容 exact-major Stable 基线的 Application。Grey、Tester 或 APPROVED Version 本身不能建立普通公开资格；test-only Application 进入独立查询。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-002 -->
### BR-CAT-002：可信可选身份

匿名调用只得到 Stable 目标；有效 authId 可以参与 Tester 和 Grey 判断。无效凭证不能降级，请求不能自报 authId、Tester、channel、cohort 或 Filter 命中。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-003 -->
### BR-CAT-003：复用唯一运行解析

每个候选 Application 必须复用 UC023 的 exact-major `TEST > GREY > STABLE` 选择、capability 回退与不变量边界。列表和详情不得复制、简化或改写该优先级。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-004 -->
### BR-CAT-004：最小公开 Profile

Catalog 只返回当前已发布 Profile 的 revision 身份和 displayName、description、icon；不返回技术名称、管理员、作者、Reviewer、审核、策略或历史资料。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-005 -->
### BR-CAT-005：Filter 分发与客户端求值

每个普通 Catalog item 返回当前 Application Filter；不存在时合成 revision 0 `ALLOW_ALL`。即使启动目标因 Tester 资格解析为 TEST，该 item 仍按普通公开 Catalog 执行 Filter。App Center 不读取用户资料或执行规则。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-006 -->
### BR-CAT-006：列表与详情同一投影

列表项和详情使用同一 PublicApplicationCatalogItem。详情不能通过 applicationId 绕过普通候选资格，列表也不使用缺字段的另一套运行或 Filter 语义。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-007 -->
### BR-CAT-007：稳定 keyset 分页

列表按 ApplicationId 稳定升序并使用绑定查询边界的 opaque keyset cursor。每页内部一致，跨页不冻结全局 snapshot，不返回 totalCount；pageSize、扫描预算或响应字节预算均可使页面提前结束。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-008 -->
### BR-CAT-008：一致快照与失败关闭

每个页面或详情内组合的 Application、Profile、Publication、Membership、Version/Review 和 Filter 来自一个逻辑一致快照。正常不合格项被排除；实际读取到的悬空、跨 Application、非批准或 snapshot/规则损坏返回 INTERNAL，不提供部分成功。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-009 -->
### BR-CAT-009：批量只读热路径

列表不得为每个 item 发起外部网络调用或逐项开启独立数据库事务。实现应批量扫描和加载候选，并复用 UC023 的批量解析核心；查询不写领域访问事实。

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-010 -->
### BR-CAT-010：最小披露与私有缓存

响应不披露未选槽位、Tester Membership、Grey bucket/seed、Filter 发布者或审核事实。列表和详情均使用 `Cache-Control: private, no-store`，避免依赖身份的目标进入共享缓存。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-022`

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-006 -->
### BR-FLT-006：客户端确定性求值

官方客户端必须实现本用例的相同布尔、类型、比较和缺失字段语义。未知 schemaVersion 或节点 fail closed。App Center 不接收原始用户字段，不执行或保存用户级求值结果。

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

- `UC-APP-024`（use-cases/UC-APP-024-query-public-application-catalog.md）：后续设计顺序、变更记录
- `UC-APP-022`（use-cases/UC-APP-022-manage-application-filter.md）：目标与范围、已确认的设计选择、输入与身份、规则结构、客户端求值契约、设置主流程、清空主流程、读取主流程、异常流程、最小领域模型变化、API 草图、验收场景、依赖与实现边界、后续设计顺序、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-024-query-public-application-catalog.md` | 338 | `693af4a87c06` |
| `use-cases/UC-APP-022-manage-application-filter.md` | 314 | `385fb67364de` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
