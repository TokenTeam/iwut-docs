# UC-APP-034：查询我的 ApplicationVersion 列表与详情

状态：`ACCEPTED`

## 设计结论

> Application 当前管理员可以分页查询该 Application 下的全部 ApplicationVersion，并按稳定 versionId 读取任意审核状态 Version 的当前详情。这里的“任意”只表示当前所管理 Application 内的任意 Version 和任意审核状态，不表示跨 Application 查询，也不授予平台系统管理员或 Reviewer 通用读取权。

这个查询服务 Developer Console，是 [UC-APP-029](UC-APP-029-query-owned-application-management.md) 已明确留出的 Version 完整列表与详情能力，也是 [UC-APP-003](UC-APP-003-update-draft-application-version.md) 所述草稿编辑前读取 revision 的正式来源。

Reviewer 继续通过 [UC-APP-030](UC-APP-030-query-application-version-reviews.md) 读取一次审核的不可变 snapshot、当前审核策略和利益冲突提示。UC030 与本用例不能互相替代：本用例展示管理员拥有的 Version 当前状态，UC030 展示 Reviewer 作出或审计决定所需的审核事实。

如果未来平台支持人员需要跨 Application 排障，应建立带精确权限、强审计和最小披露的独立运维查询；不得把“平台管理员”解释为本用例的隐式超级读取者。

## 目标与范围

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

## 参与者与授权

- **查询者**：Gateway 验证后的可信 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **App Center**：从自己的 Application、ApplicationVersion、ApplicationVersionOAuthConfig 和 ApplicationReview 权威记录构造私有读取投影。

查询者不需要 developerStatus=`APPROVED`。Developer 资格下降不删除其既有 Application 管理关系，也不应阻止其读取和处置已有资产；创建、编辑、提交等写命令仍独立执行各自的 Developer 资格检查。

Application 的平台暂停、管理员归档、CLOSING 或 CLOSED 都不移除历史读取权。CLOSED 记录继续按 UC029 的语义向其保存的最后 `adminId` 可见，但这不恢复配额或 owner 义务，也不允许任何写命令。

Reviewer 的 `app.version.review`、平台运维的 suspend/restore 权限、SYSTEM service identity 和其他平台角色都不隐式满足本用例。当前管理员若同时拥有 Reviewer 权限，仍以当前管理员身份使用本查询；其 Reviewer 查询继续遵守 UC030 的独立授权和利益冲突规则。

可信身份必须先完成验证。随后 Application 不存在、调用者不是当前管理员、Version 不存在或 Version 不属于路径 Application，统一返回 `ApplicationVersionManagementNotFound`，不能通过错误差异枚举 Application 或跨 Application versionId。

## 查询输入与 API 草图

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

## 列表结果

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

## Version 详情

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

## 当前内容、审核快照与写命令边界

- DRAFT Version 的详情是 UC003 编辑输入来源；调用者在写入时仍必须提交读取到的 expectedRevision。
- SUBMITTED/APPROVED/REJECTED Version 的当前内容应与最新审核 snapshot 的受审核字段一致，但本查询不以 snapshot 替换 Version 当前资源。
- UC004 提交、UC005 决定、UC006 恢复和 UC003 编辑都必须在自己的最终事务中重新检查当前管理员、Developer 资格、状态、revision 和 Review 关系。
- 查询返回的 reviewStatus、revision、latestReview 或 asOf 都不是锁、租约、授权票据或决定资格证明。
- Publication 是否引用该 Version 继续从 UC029 的 publications 投影读取；本详情不跨能力拼接 TEST/GREY/STABLE 使用位置。

## 生命周期与管理权变化

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

## 一致性与损坏状态

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

## 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信 USER 身份 | 沿用 `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| Application/Version 不存在、非当前管理员或路径归属不匹配 | `APPLICATION_VERSION_MANAGEMENT_NOT_FOUND` | 404 / NOT_FOUND |
| applicationId、versionId、pageSize 或 reviewStatus 非法 | `INVALID_APPLICATION_VERSION_QUERY` | 400 / INVALID_ARGUMENT |
| pageToken 损坏或上下文不匹配 | `INVALID_APPLICATION_VERSION_PAGE_TOKEN` | 400 / INVALID_ARGUMENT |
| Version、OAuth 配置或 Review 关系损坏 | `APPLICATION_VERSION_MANAGEMENT_STATE_INCONSISTENT` | 500 / INTERNAL |
| snapshot、存储或查询依赖不可用 | `APPLICATION_VERSION_MANAGEMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

不存在独立的“系统管理员可以读取”错误分支。Reviewer、平台运维人员和其他非当前管理员与任意普通非管理员一样得到统一 NOT_FOUND。

## 业务规则

<a id="br-ver-019"></a>
### BR-VER-019：当前管理员私有版本读取

ApplicationVersion 管理列表与详情只向 Application 当前保存的 adminId 对应可信 USER 返回。Developer 资格不作为只读前置；Reviewer、平台管理员、Tester、SYSTEM 和运维权限均不隐式授权。Application/Version 不存在、非当前管理员和跨 Application versionId 必须统一隐藏。

<a id="br-ver-020"></a>
### BR-VER-020：全部状态与历史生命周期可见

当前管理员可以读取其 Application 下 DRAFT、SUBMITTED、APPROVED、REJECTED 的全部 Version。平台 SUSPENDED、管理员 ARCHIVED、Application CLOSING/CLOSED 不删除管理历史可见性；CLOSED 读取不恢复 owner 义务或写权限。

<a id="br-ver-021"></a>
### BR-VER-021：当前 Version 与最新 Review 投影分离

详情的 Version 字段来自当前 ApplicationVersion 及其一对一 OAuth 配置；latestReview 只提供管理员继续管理所需的最新 attempt、决定理由和恢复时间摘要。它不得以 Review snapshot 替换当前 Version，也不得披露 ApplicationVersion.updatedBy、Reviewer 身份、内部策略、检查项、approval validation、利益冲突或完整历史 attempts。

<a id="br-ver-022"></a>
### BR-VER-022：稳定且绑定授权上下文的分页

列表按 `(sequence, versionId)` 降序 keyset 分页。token 必须绑定调用者、Application、reviewStatus filter 和最后排序键，不承载授权结论，不能跨身份、Application 或过滤条件复用；列表不得使用 offset 或无界 N+1 查询。

<a id="br-ver-023"></a>
### BR-VER-023：一致快照与管理权边界

每个列表页和详情必须在一个一致 snapshot 中确认当前 adminId 并读取所需 Version、OAuth 配置和最新 Review。与管理权转让并发时结果等价于明确先后顺序；转让后的旧管理员不能开始新的成功查询。

<a id="br-ver-024"></a>
### BR-VER-024：关系损坏失败关闭

Version、OAuth 配置和最新 Review 的归属、状态、revision、attempt 或 decision/restoration 关系损坏时，整页或详情返回 INTERNAL。查询不能跳项、返回部分详情、补默认值或修改权威数据。

<a id="br-ver-025"></a>
### BR-VER-025：查询最小披露且不构成写依据

列表只返回导航与状态字段，详情返回当前管理员管理 Version 所需的完整运行声明和最小最新审核摘要；不得返回 secret/hash、ApplicationVersion.updatedBy、Reviewer 内部事实、用户资料或完整审核历史。响应必须 `private, no-store`，且任何字段都不能替代写命令自己的最终授权、状态和 OCC 检查。

## 最小查询模型与索引

本用例增加独立 read port 和 read model，不把分页、最新 Review 投影或身份授权放入 ApplicationVersion 聚合。

无过滤列表复用既有 `(applicationId, sequence)` 唯一索引并反向扫描。若实现保留单 reviewStatus 过滤，应通过显式 migration 增加：

```text
(applicationId ASC, reviewStatus ASC, sequence DESC, versionId DESC)
```

详情复用 applicationId/versionId、versionId OAuth 配置和 `(versionId, attempt)` 既有唯一索引。Repository 必须批量取得一页 Version 的最大 attempt，不能对每个列表项分别往返数据库。

本用例不新增业务集合、不写审计事件，也不修改 Application、Version、OAuth config 或 Review。page token 的签名/编码 key 属于 adapter 配置，不进入 Domain。

## 验收场景

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

## 实现依赖与交付边界

若本提案被接受，实现至少需要：

- `iwut-app-center-api`：在既有 `app_center.v1.application_version` service 增加列表/详情 RPC、read model 与稳定 error reasons；
- `iwut-app-center`：独立 query usecase/port、Mongo majority snapshot adapter、批量 latest Review 查询、私有 HTTP/gRPC transport 和 composition wiring；
- MongoDB：复用现有唯一索引，并以显式 migration 增加单 reviewStatus 分页索引；
- 测试：身份与存在性隐藏、四状态和恢复后 DRAFT、分页/token 绑定、转让并发、生命周期/平台/归档可见性、关系损坏、HTTP/gRPC header 与真实 MongoDB snapshot 验收；
- 最终门禁：`make check-full`。本查询不需要 Auth schema/API 变化或真实 OAuth 流程，因此不以 `make check-auth-app` 作为最低验收层级。

本用例不生成新的领域状态，不需要跨服务写协调。若实现发现必须调用 Auth 才能判断读取权，说明授权边界偏离 UC029 的当前管理员模型，应先返回设计层修正，不能在 adapter 中隐式扩权。

## 变更记录

- 2026-10-10：建立当前 Application 管理员的 Version 列表与详情提案；明确 Reviewer 使用 UC030，平台跨 Application 运维读取不属于本用例。
- 2026-10-10：产品确认权限与查询边界；接受当前管理员私有列表、当前详情、最小最新审核摘要和历史生命周期可见性，进入 brief 与实现。
- 2026-10-10：实现审查确认 UC005 会把 Reviewer/SYSTEM authId 写入 Version.updatedBy；为落实 Reviewer 身份最小披露，UC034 列表与详情明确不返回 updatedBy。
