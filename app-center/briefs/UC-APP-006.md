<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-006 --spec tools/brief-specs/UC-APP-006.json -->
# Brief — UC-APP-006：将被拒绝的应用版本恢复为草稿

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-006` 将被拒绝的应用版本恢复为草稿 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-REV-021`–`BR-REV-028`（8 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
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

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 Version revision 为前提，把最新一次被拒绝的 ApplicationVersion 显式恢复为可编辑 DRAFT，并留下不可覆盖的恢复审计。

本用例负责：

- 确认目标是该 Version 最新且尚未处理的 `REJECTED` ApplicationReview。
- 在该 Review 上写入一次性 draftRestoration 审计。
- 将 ApplicationVersion.reviewStatus 从 `REJECTED` 改为 `DRAFT`。
- 增加 Version revision 并更新最近修改审计。

本用例不负责：

- 修改 Version 内容；恢复后使用 UC-APP-003。
- 自动重新提交审核；重新提交使用 UC-APP-004，并创建新的 attempt。
- 修改、删除或推翻原拒绝 decision。
- 重新检查 Scope Catalog、launchUrl 或审核策略。
- 撤回 SUBMITTED、撤销 APPROVED 或处理申诉。
- 发送审核通知。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
reviewId: ApplicationReviewId
```

Command：

```text
RestoreRejectedApplicationVersionCommand {
  expectedVersionRevision: int64
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

restoredBy、restoredAt、resultVersionRevision 和最终 reviewStatus 不能由请求正文指定。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，expectedVersionRevision `>= 1`。
3. 从 Clock 取得 restoredAt。
4. Repository 在同一事务或等价原子边界中确认并更新：
   - Application 存在且 adminId 等于调用者 authId。
   - Version 属于路径中的 Application。
   - Version.reviewStatus 是 `REJECTED`。
   - Version.revision 等于 expectedVersionRevision。
   - Review 属于该 Application 和 Version。
   - Review 是该 Version attempt 最大的最新审核。
   - Review.status 和 decision.outcome 都是 `REJECTED`。
   - Review.draftRestoration 是 null。
   - Version.revision 等于 `Review.sourceVersionRevision + 2`。
   - 写入 Review.draftRestoration，包括 restoredBy、restoredAt 和 resultVersionRevision。
   - 将 Version.reviewStatus 改为 `DRAFT`。
   - 将 Version.revision 增加 1。
   - 将 Version.updatedBy 设为 authId，updatedAt 设为 restoredAt。
5. 返回带 draftRestoration 的 Review 摘要和更新后的 DRAFT Version 摘要。

步骤 4 的全部检查与写入必须处于同一个条件更新边界，不能先检查后无条件写入。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedVersionRevision 缺失或 `< 1`：`ApplicationVersionRevisionRequired`。
- Application、Version 或 Review 不存在，或路径关系不匹配：`ApplicationReviewNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 不是 `REJECTED`：`ApplicationVersionNotRejected`。
- Version revision 不匹配：`ApplicationVersionRevisionConflict`。
- Review 不是最新 attempt：`ApplicationReviewNotLatest`。
- Review 不是有效 REJECTED decision，或与 Version 状态/revision 不一致：`ApplicationReviewStateInconsistent`。
- draftRestoration 已存在：`ApplicationReviewAlreadyRestored`。
- 持久化失败：内部失败，不产生部分恢复。

路径关系不匹配统一返回 NotFound，不泄露其他应用或版本的审核记录。所有失败都保持 Review 和 Version 不变。

多个条件同时不满足时，为保证错误 reason 和契约测试稳定，Repository 按以下优先级
分类：`NotFound` → `NotAdmin` → `NotLatest` → `AlreadyRestored` →
`NotRejected` → `RevisionConflict` → `StateInconsistent`。因此对最新且已经恢复的
Review 重试，即使 Version 已经是 DRAFT 或旧 expectedVersionRevision 已经过期，也返回
`ApplicationReviewAlreadyRestored`；历史 attempt 始终先返回
`ApplicationReviewNotLatest`。

### 最小领域行为

```text
ApplicationVersion.RestoreDraft(
  expectedRevision,
  restoredBy,
  restoredAt,
) -> ApplicationVersion

ApplicationReview.RecordDraftRestoration(
  restoredBy,
  restoredAt,
  resultVersionRevision,
) -> ApplicationReviewDraftRestoration
```

实体分别保护状态和一次性字段；跨 Application、Version、Review 的当前管理员、最新 attempt 和 revision 关系由 Repository 原子操作共同保护。

### 用例端口

```go
type Clock interface {
    Now() time.Time
}

type RejectedApplicationVersionRepository interface {
    RestoreDraft(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        reviewID ApplicationReviewID,
        expectedAdminID AuthID,
        expectedVersionRevision int64,
        restoredAt time.Time,
    ) (*RestoreRejectedVersionResult, error)
}
```

Repository 必须区分 NotFound、NotAdmin、NotRejected、RevisionConflict、NotLatest、AlreadyRestored、StateInconsistent 和基础设施失败。

### 数据模型变化

UC-APP-006 不增加 collection。`application_reviews` 增加一次性、可空的 draftRestoration：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `draftRestoration` | 对拒绝结果的草稿恢复审计 | object | 仅 REJECTED Review 可从 null 写入一次 | no | yes |
| `draftRestoration.restoredBy` | 执行恢复的当前 admin | string | opaque authId | no | no when draftRestoration exists |
| `draftRestoration.restoredAt` | 恢复时间 | datetime | UTC / RFC 3339 | no | no when draftRestoration exists |
| `draftRestoration.resultVersionRevision` | 恢复后的 Version revision | int64 | `>= 1`；等于恢复前 revision + 1 | no | no when draftRestoration exists |

schema validator 必须保证：

- draftRestoration 为 null，或三个子字段完整存在。
- 只有 status=`REJECTED` 且 decision.outcome=`REJECTED` 的 Review 可以拥有 draftRestoration。

MongoDB schema validator 不能比较更新前后的 document，因此“一旦创建不可修改”由
Repository 的 `draftRestoration=null` 条件更新、同一事务中的完整复检以及该 collection
的单一写入口共同保证；不得提供覆盖或清空 draftRestoration 的通用 Repository 方法。

`application_versions` 不增加字段。本用例更新 reviewStatus、revision、updatedBy 和 updatedAt。

### API 草图

```text
POST /applications/{applicationId}/versions/{versionId}/reviews/{reviewId}/draft-restoration
Authorization: <authenticated developer identity>
```

请求：

```json
{
  "expectedVersionRevision": 5
}
```

成功：`200 OK`

```json
{
  "review": {
    "reviewId": "review-uuid",
    "status": "REJECTED",
    "draftRestoration": {
      "restoredBy": "current-admin-auth-id",
      "restoredAt": "2026-09-15T16:00:00Z",
      "resultVersionRevision": 6
    }
  },
  "version": {
    "versionId": "version-uuid",
    "reviewStatus": "DRAFT",
    "revision": 6,
    "updatedBy": "current-admin-auth-id",
    "updatedAt": "2026-09-15T16:00:00Z"
  }
}
```

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- 路径关系不存在：`404 Not Found`。
- revision 不匹配、非 REJECTED、非最新 attempt、已恢复或状态不一致：`409 Conflict`，使用领域错误码区分。
- expectedVersionRevision 格式非法：`400 Bad Request`。

### 测试与验收

领域测试：

- REJECTED Version 可以恢复为 DRAFT，并增加 revision。
- 其他 Version 状态不能使用恢复行为。
- draftRestoration 只能设置一次且创建后不可修改。
- 恢复不修改 Version 内容或原 Review decision。
- resultVersionRevision 与 Version 新 revision 一致。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以恢复。
- 新 admin 可以恢复前任创建和提交的 Version。
- expectedVersionRevision、restoredBy 和 restoredAt 来源正确。
- 本用例不调用 ScopeCatalog、LaunchURLSubmissionPolicy 或 ReviewPolicyProvider。
- Repository 业务错误映射正确。

Repository 集成测试：

- draftRestoration 与 Version 状态/revision/审计全部提交或全部回滚。
- 两个并发恢复最多一个成功。
- 管理员转让与恢复并发时旧 admin 不会成功。
- 历史 rejected reviewId 不能恢复当前 Version。
- Review/Version 状态或 revision 关系损坏时拒绝并告警。
- 恢复后可以由 UC-APP-003 更新，或由 UC-APP-004 直接创建递增的新 attempt。

API 测试：

- 正确请求返回 REJECTED Review 的恢复审计和 DRAFT Version 摘要。
- 请求不能指定 restoredBy、restoredAt、resultVersionRevision 或最终状态。
- 路径、身份、状态、revision 和重复恢复错误映射正确。

### 迁移说明

服务从未上线，不迁移旧通用 Version status 更新入口。新的恢复行为必须同时写入 draftRestoration 和 Version 状态，不能通过数据库脚本只改一边。

## 业务规则（UC-APP-006 权威正文）

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-021 -->
### BR-REV-021：恢复权限

恢复者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终写入时仍是 Application 当前 adminId。

恢复者不必是 Version.createdBy 或 Review.submittedBy。管理员转让后，新管理员可以继续处理旧管理员留下的拒绝版本。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-022 -->
### BR-REV-022：只恢复最新拒绝

目标 Review 必须：

- 属于路径中的 Application 和 Version。
- 是该 Version attempt 最大的记录。
- status=`REJECTED` 且 decision.outcome=`REJECTED`。
- draftRestoration=null。

不能针对历史拒绝 attempt 改变当前 Version，也不能恢复 PENDING 或 APPROVED Review。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-023 -->
### BR-REV-023：状态与 revision

合法迁移只有：

```text
ApplicationVersion: REJECTED -> DRAFT
```

恢复前 Version.revision 必须等于 Review.sourceVersionRevision + 2：一次提交和一次拒绝决定分别增加过一次 revision。恢复成功后 revision 再增加 1，resultVersionRevision 保存增加后的值。

若这些关系不成立，说明存在绕过用例的写入或数据损坏；系统必须中止并告警，不能猜测应恢复哪条记录。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-024 -->
### BR-REV-024：恢复不修改内容

恢复只改变 lifecycle、revision 和审计字段。以下内容保持不变：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
```

恢复后的内容仍应与被拒绝 Review.snapshot 相同，直到 UC-APP-003 发生一次实际编辑。

允许恢复后不修改内容就再次提交。系统不能仅凭数据库字段判断远端自托管网页是否已改变，也可能出现策略更新或原审核误判。反复提交的滥用限制应作为独立规则设计。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-025 -->
### BR-REV-025：拒绝事实不可变

恢复不得修改：

- Review.status=`REJECTED`。
- Review.snapshot 和 sourceVersionRevision。
- Review.decision 的 outcome、reason、policy、checks、decidedBy、decidedAt 或 approvalValidation。
- Review.submittedBy 和 submittedAt。

Version 回到 DRAFT 不表示拒绝被撤销，只表示管理员开始处理这次拒绝。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-026 -->
### BR-REV-026：一次性恢复审计

draftRestoration 从 null 只能设置一次：

```text
ApplicationReviewDraftRestoration {
  restoredBy: AuthId
  restoredAt: Instant
  resultVersionRevision: int64
}
```

它创建后不可修改。新的审核 attempt 若再次被拒绝，会在新的 ApplicationReview 上产生自己的 draftRestoration，不覆盖旧记录。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-027 -->
### BR-REV-027：原子恢复

以下操作必须全部成功或全部失败：

- 当前 admin、Version 状态和 expectedVersionRevision 检查。
- Review 所属、最新 attempt、拒绝 decision 和未恢复检查。
- draftRestoration 写入。
- Version 的 `REJECTED -> DRAFT`、revision 和更新审计变更。

管理员转让与恢复并发时，旧 admin 不能在转让完成后恢复。两个恢复请求并发时最多一个成功。

<!-- 权威位置: use-cases/UC-APP-006-restore-rejected-version-to-draft.md#br-rev-028 -->
### BR-REV-028：不提前重新验证

恢复 DRAFT 不调用 ScopeCatalog、LaunchURLSubmissionPolicy 或 ReviewPolicyProvider。DRAFT 可以暂时包含已经过期的 scope 或不再可提交的 URL；开发者必须能先进入草稿状态，才能通过 UC-APP-003 修正它们。

UC-APP-004 在下一次提交时重新执行提交校验，因此跳过恢复时的外部检查不会降低审核入口约束。

## 架构决定（仅本次需要的章节）

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
8. 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

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
| `developer_status` | string | 条件必需 | Developer 用例必需；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 当前只消费精确值 `app.version.review`。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时按身份不满足该入口要求拒绝，不能把缺失解释为任一状态。
- Reviewer 决定入口缺少 `permissions` 或不含 `app.version.review` 时按权限不足拒绝；Reviewer 不需要 `developer_status`。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 本身合法但不是 `APPROVED`，或可信 Reviewer 身份不含目标权限，属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-006`（use-cases/UC-APP-006-restore-rejected-version-to-draft.md）：为什么需要显式恢复、旧实现观察、后续方向、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-006-restore-rejected-version-to-draft.md` | 416 | `82ee4c6d47dc` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `2595342af7cd` |
| `platform/contracts/trusted-identity-v1.md` | 130 | `d77952c6191c` |
