<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-031 --spec tools/brief-specs/UC-APP-031.json -->
# Brief — UC-APP-031：查询 ApplicationProfileRevision 审核队列与审核详情

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-031` 查询 ApplicationProfileRevision 审核队列与审核详情 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PRF-041`–`BR-PRF-046`（6 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |
| 配套查询 | `app-center/query-contracts/profile-management.md` |

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

> 具备 `app.profile.review` 的 Reviewer 查询待处理公开资料审核队列，并读取一次资料审核的不可变详情。

本用例将 [资料管理与审核查询契约](../query-contracts/profile-management.md) 中的 Reviewer 查询交付为正式 API。管理员 ProfileRevision 列表/详情仍是独立管理查询范围；本用例不实现分配、锁单、SLA、通知、申诉或恢复被拒绝修订。

### 身份与精确权限

两个查询只接受可信 USER 身份和 `app.profile.review`。`app.version.review`、Application 管理员或 Developer 资格都不隐式授予权限。权限检查先于对象查找。

缺少身份返回 `ReviewerIdentityRequired`；缺少精确权限返回 `ApplicationProfileReviewPermissionRequired`。

### 待处理队列

```text
ListPendingApplicationProfileReviewsQuery {
  applicationId?
  pageSize: 1..100 = 20
  pageToken?
}
```

队列只包含 `ApplicationProfileReview.status=PENDING` 且所属 Application `lifecycleStatus=ACTIVE` 的记录。`SUSPENDED` 不阻止审核；`CLOSING/CLOSED` 按 UC027 排除。

按 `(submittedAt ASC, profileReviewId ASC)` 稳定 keyset 分页。队列项包含 Application ID/name、ProfileRevision ID/sequence/displayName、ProfileReview ID/attempt、submittedAt，以及查询时计算的：

```text
decisionEligibility {
  eligible
  conflicts: CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER []
}
```

冲突项不从队列隐藏。eligibility 是界面提示，UC016 的决定事务仍重新计算。

### 审核详情

详情路径中的 `applicationId/profileRevisionId/profileReviewId` 必须匹配。结果包含：

```text
ApplicationProfileReviewDetail {
  application { applicationId, name, adminId, lifecycleStatus, platformAvailabilityStatus }
  profileRevision { profileRevisionId, sequence, reviewStatus, revision, createdBy }
  review {
    profileReviewId, attempt, status, sourceRevision,
    snapshot { displayName, description, icon },
    submittedBy, submittedAt, decision?
  }
  currentPolicy { version, requiredCheckIds }
  decisionEligibility
  asOf
}
```

内容必须取不可变 Review snapshot。终态 Review 可按 ID 读取。当前 policy 第一版为 `app-profile-review-v1` 及其固定检查项，但查询结果不替代 UC016 在写入时对 expected policy 和 confirmed checks 的复查。

### 一致性与错误

单页和详情在 MongoDB majority snapshot 中构造。Application、ProfileRevision、Review 的引用、sourceRevision 或 snapshot 不一致时返回 `ApplicationProfileReviewStateInconsistent` / INTERNAL；不能省略坏项或回退到当前 ProfileRevision 内容。

不存在或路径不匹配返回 `ApplicationProfileReviewNotFound`。合法空队列成功返回空页。pageSize/pageToken 非法返回 INVALID_ARGUMENT。响应使用 `private, no-store`。

### 最小查询模型与索引

复用或补齐 `(status, submittedAt, profileReviewId)` 索引。read port 独立于决定 repository；队列通过批量 lookup 读取 Application 和 ProfileRevision，禁止 N+1。

### API 草图

```text
rpc ListPendingApplicationProfileReviews(...)
  POST /v1/reviews/application-profiles:search body=query

rpc GetApplicationProfileReview(...)
  GET /v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}
```

### 验收场景

1. 只有精确 `app.profile.review` 可读取；Version Reviewer 单独权限不足。
2. PENDING+ACTIVE 入队；CLOSING/CLOSED 排除；SUSPENDED 保留。
3. applicationId filter、升序 keyset、tie-break 与 token 绑定稳定。
4. 当前管理员、revision creator、submitter 冲突被完整提示而不隐藏队列项。
5. 详情返回 immutable snapshot 与当前固定 policy/checks。
6. 终态 Review 可查询但不进入 pending 队列。
7. 路径不匹配统一 NOT_FOUND；无权限先失败。
8. sourceRevision/snapshot/引用损坏返回 INTERNAL，不产生部分结果。
9. HTTP 与原生 gRPC 一致，真实 MongoDB 验证索引与 snapshot 行为。

### 实现依赖与交付边界

ProfileRevision、ProfileReview、固定 policy 和决定流程均已交付。现有查询契约提供读取语义；本工作包新增 API、read port/usecase、Mongo query、必要索引、transport/wiring 和验收，不改变 UC013–016 写模型。

## 业务规则（UC-APP-031 权威正文）

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-041 -->
### BR-PRF-041：Profile Reviewer 查询精确授权

资料审核队列与详情只接受具备 `app.profile.review` 的可信 Reviewer，权限检查先于对象查找。

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-042 -->
### BR-PRF-042：待处理资料队列资格

队列只包含 PENDING 且 Application 生命周期 ACTIVE 的资料 Review；SUSPENDED 保留，CLOSING/CLOSED 排除。

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-043 -->
### BR-PRF-043：资料审核快照权威

队列摘要和详情的内容来自提交时不可变 snapshot，不能用当前 ProfileRevision 替换。

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-044 -->
### BR-PRF-044：利益冲突提示不替代决定检查

查询计算的 eligibility 只用于 Reviewer 界面；UC016 在决定事务中重新计算全部冲突和前置条件。

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-045 -->
### BR-PRF-045：稳定资料队列分页

队列按 `(submittedAt, profileReviewId)` 升序 keyset 分页，token 绑定 Reviewer 与 filter。

<!-- 权威位置: use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-046 -->
### BR-PRF-046：资料审核查询失败关闭

引用、sourceRevision 或 snapshot 损坏导致整次查询 INTERNAL；不能跳项、降级或返回部分详情。

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

## 配套查询契约（按 spec 显式抽取）

> 这些是当前 bounded context 的查询契约；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `app-center/query-contracts/profile-management.md`：Application Profile 管理与审核查询契约

#### 共享约定

##### 可信身份

管理员查询使用：

```text
AuthenticatedIdentity {
  authId
}
```

管理员读取权来自 Application 当前 `adminId`。查询不使用 developerStatus 代替所有权检查；Developer 资格影响写命令，不改写已有 Application 的当前管理关系。

Reviewer 查询使用：

```text
ReviewerIdentity {
  authId
  permissions
}
```

Reviewer 查询只接受包含 `app.profile.review` 的可信身份。`app.version.review` 不隐式授予资料审核读取权，与 [BR-PRF-023](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-023) 保持一致。

##### 身份隐藏

管理员查询中，Application 不存在、ProfileRevision 不属于 Application，或调用者不是当前 admin，都返回同一类 `ApplicationProfileNotFound` 结果，避免向非管理员暴露资料是否存在。

Reviewer 查询先检查可信身份和 `app.profile.review`，再读取审核事实。缺少权限返回 `ApplicationProfileReviewPermissionRequired`；Review 不存在或引用路径不一致返回 `ApplicationProfileReviewNotFound`。

##### 分页

列表查询使用不透明 cursor，不使用可受并发插入影响的页码偏移。

```text
PageRequest {
  cursor?
  limit: 1..100 = 20
}

Page<T> {
  items: T[]
  nextCursor?
  asOf
}
```

`asOf` 表示该页结果所依据的读取时点，不是业务审计时间。cursor 的编码不对调用者承诺。

##### 一致性

- 尚未交付的管理员列表可来自读投影，允许短暂滞后，并返回 `asOf`。
- UC-APP-031 的 Reviewer 单页和详情在同一个 MongoDB snapshot 中构造，不允许以投影滞后隐藏不变量损坏。
- 详情查询从 App Center 权威事实构造单个内部一致的快照。
- 查询结果不是写入授权。UC-APP-014、015 和 016 在执行时继续校验当前 admin、状态、revision、利益冲突和公开指针前置值。

#### Reviewer 查询

##### ListPendingApplicationProfileReviews

用途：为资料 Reviewer 提供 PENDING 审核队列。

输入：

```text
ListPendingApplicationProfileReviews {
  applicationId?
  page: PageRequest
}
```

结果只包含 status=`PENDING` 且所属 Application 生命周期为 ACTIVE 的 ApplicationProfileReview；平台 SUSPENDED 不排除审核，CLOSING/CLOSED 排除。结果按 `submittedAt ASC, profileReviewId ASC` 排序，使较早提交稳定地排在前面。

```text
PendingProfileReviewSummary {
  applicationId
  applicationName
  profileRevisionId
  sequence
  profileReviewId
  attempt
  displayName
  submittedAt
  decisionEligibility: {
    eligible
    conflicts: (CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER)[]
  }
}
```

队列不隐藏利益冲突项，而是返回根据查询时当前事实计算的 `decisionEligibility`，使 Reviewer 能够理解为何无法处理某项。该字段只是界面提示；[UC-APP-016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md) 在写入 decision 时重新计算利益冲突。

##### GetApplicationProfileReviewForReviewer

用途：返回 Reviewer 完成一次审核所需的快照、当前状态和策略输入，或查看已作出的决定。

输入：

```text
GetApplicationProfileReviewForReviewer {
  applicationId
  profileRevisionId
  profileReviewId
}
```

返回：

```text
ReviewerProfileReviewDetail {
  application: {
    applicationId
    name
    adminId
    lifecycleStatus
    platformAvailabilityStatus
  }
  profileRevision: {
    profileRevisionId
    sequence
    reviewStatus
    revision
    createdBy
  }
  review: {
    profileReviewId
    attempt
    status
    sourceRevision
    snapshot: {
      displayName
      description
      icon
    }
    submittedBy
    submittedAt
    decision?
  }
  decisionEligibility: {
    eligible
    conflicts: (CURRENT_ADMIN | REVISION_CREATOR | REVIEW_SUBMITTER)[]
  }
  currentPolicy: {
    version
    requiredCheckIds
  }
  asOf
}
```

`currentPolicy` 来自查询时唯一 ACTIVE 的不可变 ProfileReviewPolicy。Reviewer 将实际阅读的 version 作为 `expectedPolicyVersion` 传给 UC-APP-016。如果在查询后发生策略、Revision、管理员或当前公开指针变化，UC-APP-016 通过自己的前置条件拒绝过期决定。

已决定 Review 保留 decision 供审计查看。查询本身不领取、锁定、分配或标记审核任务。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-031`（use-cases/UC-APP-031-query-application-profile-reviews.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出
- `app-center/query-contracts/profile-management.md`（配套查询契约）：定位、共享约定/可信身份、共享约定/身份隐藏、共享约定/分页、共享约定/一致性、管理员查询、Reviewer 查询/ListPendingApplicationProfileReviews、Reviewer 查询/GetApplicationProfileReviewForReviewer、明确不提供的查询行为、验收要点

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-031-query-application-profile-reviews.md` | 131 | `8e19b6a2f239` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `app-center/query-contracts/profile-management.md` | 297 | `47b372725ffa` |
