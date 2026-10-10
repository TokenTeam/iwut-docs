<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-034 --spec tools/brief-specs/UC-APP-034.json -->
# Brief — UC-APP-034：查询我的 ApplicationVersion 列表与详情

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-034` 查询我的 ApplicationVersion 列表与详情 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-VER-019`–`BR-VER-025`（7 条） |
| 外部引用 BR | — |
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

> Application 当前管理员可以分页查询该 Application 下的全部 ApplicationVersion，并按稳定 versionId 读取任意审核状态 Version 的当前详情。这里的“任意”只表示当前所管理 Application 内的任意 Version 和任意审核状态，不表示跨 Application 查询，也不授予平台系统管理员或 Reviewer 通用读取权。

这个查询服务 Developer Console，是 [UC-APP-029](../use-cases/UC-APP-029-query-owned-application-management.md) 已明确留出的 Version 完整列表与详情能力，也是 [UC-APP-003](../use-cases/UC-APP-003-update-draft-application-version.md) 所述草稿编辑前读取 revision 的正式来源。

Reviewer 继续通过 [UC-APP-030](../use-cases/UC-APP-030-query-application-version-reviews.md) 读取一次审核的不可变 snapshot、当前审核策略和利益冲突提示。UC030 与本用例不能互相替代：本用例展示管理员拥有的 Version 当前状态，UC030 展示 Reviewer 作出或审计决定所需的审核事实。

如果未来平台支持人员需要跨 Application 排障，应建立带精确权限、强审计和最小披露的独立运维查询；不得把“平台管理员”解释为本用例的隐式超级读取者。

### 目标与范围

本用例交付两个只读查询：

- `ListApplicationVersions`：分页列出一个 Application 下的全部 Version，可选按一个 reviewStatus 过滤；
- `GetApplicationVersion`：读取一个 Version 的完整当前内容以及管理员继续编辑、提交或处理拒绝所需的最新审核摘要。

本用例负责：

- 使用 Application 当前保存的 `adminId` 授权，不要求调用者当前仍为 APPROVED Developer；
- 让 DRAFT、SUBMITTED、APPROVED、REJECTED Version 都可被当前管理员读取；
- 在 Application 为 ACTIVE、CLOSING、CLOSED，平台为 AVAILABLE/SUSPENDED，管理员状态为 UNARCHIVED/ARCHIVED 时保留管理历史可见性；
- 返回草稿更新、提交审核和拒绝恢复所需的当前 Version revision 与最新 reviewId；
- 对 Application、Version、OAuth 依附配置和最新 Review 使用一致读取，并在关系损坏时失败关闭；
- 提供稳定、私有且不能跨管理员复用的 keyset 分页。

本用例不负责：

- 读取其他管理员的 ApplicationVersion，或按 versionId 跨 Application 搜索；
- 赋予平台管理员、Reviewer、Tester、SYSTEM 或仅有运维权限的调用者通用版本读取权；
- 返回 Reviewer 当前 policy、confirmed checks、approval validation、利益冲突提示、Reviewer 身份或完整 Review snapshot；
- 返回一个 Version 的全部历史审核 attempts；详情只提供与当前 Version 状态相关的最新 attempt 摘要；
- 修改 Version、恢复拒绝、提交或决定审核、撤销批准资格、删除草稿或改变 Publication；
- 把 Version 当前详情当成已提交审核 snapshot、发布资格证明或后续写命令的授权证明；
- 返回 Publication、Tester、OAuth client secret/hash、用户资料或审计日志。

### 参与者与授权

- **查询者**：Gateway 验证后的可信 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **App Center**：从自己的 Application、ApplicationVersion、ApplicationVersionOAuthConfig 和 ApplicationReview 权威记录构造私有读取投影。

查询者不需要 developerStatus=`APPROVED`。Developer 资格下降不删除其既有 Application 管理关系，也不应阻止其读取和处置已有资产；创建、编辑、提交等写命令仍独立执行各自的 Developer 资格检查。

Application 的平台暂停、管理员归档、CLOSING 或 CLOSED 都不移除历史读取权。CLOSED 记录继续按 UC029 的语义向其保存的最后 `adminId` 可见，但这不恢复配额或 owner 义务，也不允许任何写命令。

Reviewer 的 `app.version.review`、平台运维的 suspend/restore 权限、SYSTEM service identity 和其他平台角色都不隐式满足本用例。当前管理员若同时拥有 Reviewer 权限，仍以当前管理员身份使用本查询；其 Reviewer 查询继续遵守 UC030 的独立授权和利益冲突规则。

可信身份必须先完成验证。随后 Application 不存在、调用者不是当前管理员、Version 不存在或 Version 不属于路径 Application，统一返回 `ApplicationVersionManagementNotFound`，不能通过错误差异枚举 Application 或跨 Application versionId。

### 查询输入与 API 草图

列表输入：

```text
ListApplicationVersionsQuery {
  reviewStatus?: DRAFT | SUBMITTED | APPROVED | REJECTED
  pageSize: 1..100 = 20
  pageToken?
}
```

详情输入：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
```

查询不接受 adminId、authId、createdBy、updatedBy 或其他身份字段。可选 reviewStatus 只接受一个明确值；首版不提供多状态组合、versionLabel 搜索、全文搜索、Publication 反向筛选或 offset。

沿用现有 `app_center.v1.application_version.ApplicationVersion` service，新增：

```text
rpc ListApplicationVersions(ListApplicationVersionsRequest)
  POST /v1/applications/{application_id}/versions:search body=query

rpc GetApplicationVersion(GetApplicationVersionRequest)
  GET /v1/applications/{application_id}/versions/{version_id}
```

两种 transport 共享相同身份、存在性隐藏、分页、错误和结果语义。所有成功及领域错误响应都使用 `Cache-Control: private, no-store`；网关和共享代理不得缓存管理员版本内容。

### 列表结果

列表按 `(sequence DESC, versionId DESC)` 排序。sequence 在单个 Application 内唯一且严格递增，versionId 作为游标完整性和未来兼容的稳定次键保留。

```text
OwnedApplicationVersionSummary {
  versionId
  applicationId
  sequence
  versionLabel
  rpcApiMinVersion
  rpcApiMaxVersionExclusive
  reviewStatus
  revision
  createdBy
  createdAt
  updatedAt
  latestReview?: {
    reviewId
    attempt
    status
    submittedAt
    decidedAt?
    restoredAt?
  }
}

OwnedApplicationVersionPage {
  items[]
  nextPageToken?
  asOf
}
```

列表不返回 launchUrl、capabilities、scopes、OAuth redirects、审核理由或 Review snapshot，以控制页面大小和披露面。调用者需要这些字段时读取详情。

page token 必须至少绑定调用者 authId、applicationId、可选 reviewStatus、最后一个 `(sequence, versionId)` 和 token 版本。token 编码损坏、换调用者、换 Application 或换过滤条件均返回 `InvalidApplicationVersionPageToken`，不能降级为首页或接受 token 内的授权结论。

一次列表读取必须批量取得本页 Version 的最新 Review 指针并验证状态关系，不能逐项执行无界 N+1 查询。合法空结果返回空 items 和空 nextPageToken。

### Version 详情

详情返回 ApplicationVersion 当前权威内容，而不是某次审核 snapshot：

```text
OwnedApplicationVersionDetail {
  version {
    versionId
    applicationId
    sequence
    versionLabel
    launchUrl
    rpcApiMinVersion
    rpcApiMaxVersionExclusive
    requiredCapabilities[]
    requiredScopes[]
    optionalScopes[]
    oauthRedirects {
      pkceRedirectUris[]
      confidentialRedirectUris[]
    }
    reviewStatus
    revision
    createdBy
    createdAt
    updatedAt
  }
  latestReview?: {
    reviewId
    attempt
    status
    submittedBy
    submittedAt
    decision?: {
      outcome
      reason?
      decidedAt
    }
    draftRestoration?: {
      restoredAt
    }
  }
  asOf
}
```

`oauthRedirects` 是 Version 受审核内容的一部分，可以向当前管理员返回；它不包含 OAuth client secret、credential hash、grant 或 token。capabilities 与 scopes 返回 Version 保存的规范化值，本查询不调用 Auth Scope Catalog，也不声明这些 scope 在查询时仍允许被新版本申请。

`latestReview` 取该 Version attempt 最大的 ApplicationReview。管理员需要 reviewId 才能针对最新拒绝执行 UC006，需要拒绝 reason 才能修改草稿后重新提交，因此这两项属于必要管理信息。管理员投影不返回 `decision.decidedBy`、review policy、confirmed checks、approval validation、完整 snapshot 或 Reviewer eligibility；这些事实继续属于 UC030 的受控 Reviewer 查询。

管理员投影也不返回 ApplicationVersion.updatedBy。UC005 在审核决定后会把人工 Reviewer 或 SYSTEM principal 的 authId 写入该字段；将它放入列表或详情会绕过上述 Reviewer 身份最小披露。查询仍返回 revision 与 updatedAt，足以支持 OCC 和界面更新时间展示；createdBy 继续返回，因为它记录 Version 创建者而不是审核决定者。

本用例不提供历史 attempts 数组。若未来需要管理员浏览完整审核时间线，应建立独立分页查询并明确 Reviewer 身份、内部策略和历史理由的披露边界，不能无界嵌入 Version 详情。

### 当前内容、审核快照与写命令边界

- DRAFT Version 的详情是 UC003 编辑输入来源；调用者在写入时仍必须提交读取到的 expectedRevision。
- SUBMITTED/APPROVED/REJECTED Version 的当前内容应与最新审核 snapshot 的受审核字段一致，但本查询不以 snapshot 替换 Version 当前资源。
- UC004 提交、UC005 决定、UC006 恢复和 UC003 编辑都必须在自己的最终事务中重新检查当前管理员、Developer 资格、状态、revision 和 Review 关系。
- 查询返回的 reviewStatus、revision、latestReview 或 asOf 都不是锁、租约、授权票据或决定资格证明。
- Publication 是否引用该 Version 继续从 UC029 的 publications 投影读取；本详情不跨能力拼接 TEST/GREY/STABLE 使用位置。

### 生命周期与管理权变化

查询只读，不受在线门禁限制：

| Application 状态 | 查询行为 |
| --- | --- |
| ACTIVE + AVAILABLE + UNARCHIVED | 当前管理员可读 |
| ACTIVE + SUSPENDED | 当前管理员可读 |
| ACTIVE + ARCHIVED | 当前管理员可读 |
| CLOSING | 保存的当前管理员可读历史，不能据此继续写入 |
| CLOSED | 保存的最后管理员可读历史，不恢复 owner 义务 |

管理权转让提交后，新管理员立即成为唯一可开始新查询的身份，旧管理员的新查询统一 NOT_FOUND。转让提交前已经完成并返回给旧管理员的响应无法撤回；`private, no-store` 禁止共享缓存，但不承诺从调用者设备收回已显示数据。

列表页和详情都在单个 MongoDB majority snapshot 中确认 Application.adminId 与 Version/Review 事实。若转让与查询并发，结果必须等价于查询快照发生在转让提交之前或之后，不能返回新管理员授权与旧快照、或旧管理员授权与转让后事实拼接的撕裂结果。

### 一致性与损坏状态

ApplicationVersion 与其 OAuth 配置共用 revision 和审核生命周期。详情必须在一个 snapshot 中读取 Application、Version、OAuth 配置及最新 Review；列表页必须在一个 snapshot 中读取 Application、本页 Version 和批量最新 Review 指针。

至少以下状态属于 `ApplicationVersionManagementStateInconsistent`：

- Version.applicationId 与路径 Application 不一致；
- Version 缺少一对一 OAuth 配置、配置指向其他 Version/Application，或配置内容不满足已迁移 schema；
- 同一 Application 的 sequence 重复、非正数或列表排序键损坏；
- SUBMITTED Version 没有最新 PENDING Review，或 Review 的 versionId/applicationId 不匹配；
- APPROVED Version 的最新 Review 不是匹配的 APPROVED decision；
- REJECTED Version 的最新 Review 不是未恢复的匹配 REJECTED decision；
- DRAFT Version 存在最新 Review 时，该 Review 不是已经记录 draftRestoration 的 REJECTED attempt；
- Review.status、decision.outcome、draftRestoration、attempt 或 sourceVersionRevision 关系违反 UC004–006 的不变量。

损坏状态导致整页或整个详情失败为 INTERNAL，不能跳过坏 Version、隐去 latestReview、用空 OAuth 配置兜底或从 Review snapshot 自动修复 Version。普通日志、错误和 trace 不记录 launchUrl、OAuth redirects、scopes、审核 reason 或身份凭据。

### 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信 USER 身份 | 沿用 `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| Application/Version 不存在、非当前管理员或路径归属不匹配 | `APPLICATION_VERSION_MANAGEMENT_NOT_FOUND` | 404 / NOT_FOUND |
| applicationId、versionId、pageSize 或 reviewStatus 非法 | `INVALID_APPLICATION_VERSION_QUERY` | 400 / INVALID_ARGUMENT |
| pageToken 损坏或上下文不匹配 | `INVALID_APPLICATION_VERSION_PAGE_TOKEN` | 400 / INVALID_ARGUMENT |
| Version、OAuth 配置或 Review 关系损坏 | `APPLICATION_VERSION_MANAGEMENT_STATE_INCONSISTENT` | 500 / INTERNAL |
| snapshot、存储或查询依赖不可用 | `APPLICATION_VERSION_MANAGEMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

不存在独立的“系统管理员可以读取”错误分支。Reviewer、平台运维人员和其他非当前管理员与任意普通非管理员一样得到统一 NOT_FOUND。

### 最小查询模型与索引

本用例增加独立 read port 和 read model，不把分页、最新 Review 投影或身份授权放入 ApplicationVersion 聚合。

无过滤列表复用既有 `(applicationId, sequence)` 唯一索引并反向扫描。若实现保留单 reviewStatus 过滤，应通过显式 migration 增加：

```text
(applicationId ASC, reviewStatus ASC, sequence DESC, versionId DESC)
```

详情复用 applicationId/versionId、versionId OAuth 配置和 `(versionId, attempt)` 既有唯一索引。Repository 必须批量取得一页 Version 的最大 attempt，不能对每个列表项分别往返数据库。

本用例不新增业务集合、不写审计事件，也不修改 Application、Version、OAuth config 或 Review。page token 的签名/编码 key 属于 adapter 配置，不进入 Domain。

### 验收场景

1. 当前管理员可以分页读取同一 Application 下四种 reviewStatus 的 Version，并读取任一 Version 详情。
2. 查询不要求 APPROVED Developer；Developer 资格下降的当前管理员仍可读，但既有写 UC 继续按自己的规则拒绝不合格调用者。
3. 非管理员、旧管理员、Reviewer、Tester、SYSTEM、平台运维人员和不存在 Application/Version 均不能据错误区分资源是否存在。
4. 管理权转让前后只有 snapshot 对应的管理员成功；旧 page token 不能被新管理员使用，新管理员也不能使用旧管理员 token。
5. AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED、ACTIVE/CLOSING/CLOSED 组合不删除历史读取权；这些状态不因查询而改变。
6. 默认列表 sequence 降序、单状态过滤、pageSize 边界、稳定翻页、非法 token、换身份/换 Application/换 filter 均按契约工作。
7. 列表保持轻量，详情返回完整 launchUrl、capabilities、scopes、OAuth redirects、revision、createdBy 与时间字段；两者均不返回 updatedBy、secret/hash 或 Reviewer 身份。
8. 初始 DRAFT 无 latestReview；SUBMITTED 映射最新 PENDING；APPROVED/REJECTED 映射匹配 decision；恢复后的 DRAFT 返回带 draftRestoration 的最新 REJECTED 摘要。
9. REJECTED 详情返回最新 reviewId 和 reason，可作为用户发起 UC006 的输入来源，但 UC006 仍独立复查 latest attempt、状态和 revision。
10. 修改或提交与查询并发时，单次结果来自一个一致 snapshot，不出现 Version 新 revision 配旧 OAuth 配置或旧 Review 指针。
11. 缺 OAuth config、跨 Application 引用、重复 sequence、Review/Version 状态不一致和 restoration 损坏使整页或详情 INTERNAL，不返回部分结果。
12. HTTP 与原生 gRPC 共享身份、NOT_FOUND 隐藏、分页和错误语义，并对成功及领域错误设置 `private, no-store`。
13. 查询不调用 Scope Catalog、URL preflight 或 Auth 业务接口，不改变任何 revision、状态、审计或 updatedAt。

### 实现依赖与交付边界

若本提案被接受，实现至少需要：

- `iwut-app-center-api`：在既有 `app_center.v1.application_version` service 增加列表/详情 RPC、read model 与稳定 error reasons；
- `iwut-app-center`：独立 query usecase/port、Mongo majority snapshot adapter、批量 latest Review 查询、私有 HTTP/gRPC transport 和 composition wiring；
- MongoDB：复用现有唯一索引，并以显式 migration 增加单 reviewStatus 分页索引；
- 测试：身份与存在性隐藏、四状态和恢复后 DRAFT、分页/token 绑定、转让并发、生命周期/平台/归档可见性、关系损坏、HTTP/gRPC header 与真实 MongoDB snapshot 验收；
- 最终门禁：`make check-full`。本查询不需要 Auth schema/API 变化或真实 OAuth 流程，因此不以 `make check-auth-app` 作为最低验收层级。

本用例不生成新的领域状态，不需要跨服务写协调。若实现发现必须调用 Auth 才能判断读取权，说明授权边界偏离 UC029 的当前管理员模型，应先返回设计层修正，不能在 adapter 中隐式扩权。

## 业务规则（UC-APP-034 权威正文）

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-019 -->
### BR-VER-019：当前管理员私有版本读取

ApplicationVersion 管理列表与详情只向 Application 当前保存的 adminId 对应可信 USER 返回。Developer 资格不作为只读前置；Reviewer、平台管理员、Tester、SYSTEM 和运维权限均不隐式授权。Application/Version 不存在、非当前管理员和跨 Application versionId 必须统一隐藏。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-020 -->
### BR-VER-020：全部状态与历史生命周期可见

当前管理员可以读取其 Application 下 DRAFT、SUBMITTED、APPROVED、REJECTED 的全部 Version。平台 SUSPENDED、管理员 ARCHIVED、Application CLOSING/CLOSED 不删除管理历史可见性；CLOSED 读取不恢复 owner 义务或写权限。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-021 -->
### BR-VER-021：当前 Version 与最新 Review 投影分离

详情的 Version 字段来自当前 ApplicationVersion 及其一对一 OAuth 配置；latestReview 只提供管理员继续管理所需的最新 attempt、决定理由和恢复时间摘要。它不得以 Review snapshot 替换当前 Version，也不得披露 ApplicationVersion.updatedBy、Reviewer 身份、内部策略、检查项、approval validation、利益冲突或完整历史 attempts。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-022 -->
### BR-VER-022：稳定且绑定授权上下文的分页

列表按 `(sequence, versionId)` 降序 keyset 分页。token 必须绑定调用者、Application、reviewStatus filter 和最后排序键，不承载授权结论，不能跨身份、Application 或过滤条件复用；列表不得使用 offset 或无界 N+1 查询。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-023 -->
### BR-VER-023：一致快照与管理权边界

每个列表页和详情必须在一个一致 snapshot 中确认当前 adminId 并读取所需 Version、OAuth 配置和最新 Review。与管理权转让并发时结果等价于明确先后顺序；转让后的旧管理员不能开始新的成功查询。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-024 -->
### BR-VER-024：关系损坏失败关闭

Version、OAuth 配置和最新 Review 的归属、状态、revision、attempt 或 decision/restoration 关系损坏时，整页或详情返回 INTERNAL。查询不能跳项、返回部分详情、补默认值或修改权威数据。

<!-- 权威位置: use-cases/UC-APP-034-query-owned-application-versions.md#br-ver-025 -->
### BR-VER-025：查询最小披露且不构成写依据

列表只返回导航与状态字段，详情返回当前管理员管理 Version 所需的完整运行声明和最小最新审核摘要；不得返回 secret/hash、ApplicationVersion.updatedBy、Reviewer 内部事实、用户资料或完整审核历史。响应必须 `private, no-store`，且任何字段都不能替代写命令自己的最终授权、状态和 OCC 检查。

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

- `UC-APP-034`（use-cases/UC-APP-034-query-owned-application-versions.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-034-query-owned-application-versions.md` | 318 | `d580af070c83` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
