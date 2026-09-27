<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-004 --spec tools/brief-specs/UC-APP-004.json -->
# Brief — UC-APP-004：提交应用版本审核

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-004` 提交应用版本审核 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-REV-001`–`BR-REV-009`（9 条） |
| 外部引用 BR | `BR-VER-018`（来自 `UC-APP-002`） |
| ADR | `ADR-001`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/auth-scope-catalog-v1.md` |

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

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 revision 为前提，把一个满足提交条件的 DRAFT ApplicationVersion 提交为一次可审计的审核 attempt。

本用例完成两件不可分割的事：

- 复制当前受审核内容，创建状态为 `PENDING` 的 ApplicationReview。
- 将 ApplicationVersion.reviewStatus 从 `DRAFT` 改为 `SUBMITTED`。

本用例不负责：

- reviewer 批准或拒绝。
- 开发者撤回提交。
- 修改被拒绝的 Version，或把 `REJECTED` 恢复为 `DRAFT`。
- 把审核通过的 Version 放入 test/grey/stable 发布槽位。
- 抓取、托管或冻结开发者网页内容。
- 发送站内消息、邮件或 RabbitMQ 通知。

审核队列可以通过查询 `PENDING` ApplicationReview 构建，不需要在提交写路径提前引入消息系统。

### 提交结果

成功后产生以下状态：

```text
ApplicationVersion
  reviewStatus: DRAFT -> SUBMITTED
  revision: expectedRevision -> expectedRevision + 1
  updatedBy: submitter authId
  updatedAt: submittedAt

ApplicationReview
  status: PENDING
  decision: null
  draftRestoration: null
  sourceVersionRevision: expectedRevision
  snapshot: 提交瞬间的受审核字段
```

Version 内容字段本身不改变。后续 reviewer 只审核 ApplicationReview.snapshot，不重新把可变的 ApplicationVersion 当成审核输入。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
```

Command：

```text
SubmitApplicationVersionReviewCommand {
  expectedRevision: int64
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

HTTP 和 gRPC adapter 都在 command 中传递 expectedRevision。UC-APP-003 的 PUT 直接替换 Version，所以使用 `If-Match`；本用例的 POST 以 reviews collection 为目标且同时迁移 Version，把 Version ETag 放在 `If-Match` 会产生目标资源歧义，因此使用明确的 command 字段。

reviewId、attempt、status、snapshot、decision、draftRestoration、submittedBy 和 submittedAt 都不能由请求正文指定。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，expectedRevision `>= 1`。
3. Repository 读取候选 Version，并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - Version 属于路径中的 Application。
   - reviewStatus 是 `DRAFT`。
   - revision 等于 expectedRevision。
4. 通过 ScopeCatalog 重新确认 requiredScopes 和 optionalScopes 当前仍允许被新版本申请，并取得本次 Auth catalog revision。
5. 按 BR-VER-018 重新验证 oauthRedirects 的结构、规范 hostname 和安全限制。
6. 通过 LaunchURLSubmissionPolicy 确认 launchUrl 是当前可提交审核的公网 HTTPS URL。
7. 生成 UUIDv7 reviewId，并从 Clock 取得 submittedAt。
8. Repository 在同一事务或等价原子边界中重新确认步骤 3 的全部条件，然后：
   - 为该 Version 分配下一个 attempt，从 1 开始递增。
   - 复制候选 Version 的受审核字段形成不可变 snapshot。
   - 插入 status 为 `PENDING`、decision 和 draftRestoration 均为 null 的 ApplicationReview。
   - 将 Version.reviewStatus 改为 `SUBMITTED`。
   - 将 Version.revision 原子增加 1，并写入 updatedBy、updatedAt。
8. 返回新建的 ApplicationReview 和更新后的 Version 摘要。

外部检查与最终写入之间允许发生并发，但最终写入必须再次比较 revision。只要 Version 内容、状态或管理员已经变化，就不能保存基于旧候选内容生成的审核快照。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedRevision 缺失或 `< 1`：`ApplicationVersionRevisionRequired`。
- Application 或 Version 不存在，或二者不匹配：`ApplicationVersionNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 不是 `DRAFT`：`ApplicationVersionNotDraft`。
- 当前 revision 不等于 expectedRevision：`ApplicationVersionRevisionConflict`。
- launchUrl 不是公网 HTTPS URL：`ApplicationLaunchUrlNotReviewable`。
- launchUrl DNS 解析失败或检查依赖暂时不可用：`LaunchUrlInspectionUnavailable`。
- scope 已不存在、deprecated 或不再允许新申请：`InvalidApplicationScope`。
- oauthRedirects 不再满足 BR-VER-018：`InvalidOAuthRedirectConfiguration`。
- Scope Catalog 无可用的新鲜快照：`ScopeCatalogUnavailable`。
- reviewId 冲突或持久化失败：内部失败，不产生半完成提交。

applicationId 与 versionId 不匹配时不返回 Version 的真实所属应用。所有失败都必须保持 Version 为原状态且不创建 review。

### 最小领域模型

```text
ApplicationReview {
  reviewId: ApplicationReviewId
  applicationId: ApplicationId
  versionId: ApplicationVersionId
  attempt: ReviewAttempt
  sourceVersionRevision: int64
  status: PENDING
  decision: null
  draftRestoration: null
  snapshot: ApplicationVersionReviewSnapshot
  scopeCatalogRevision: int64
  preflightPolicyVersion: string
  submittedBy: AuthId
  submittedAt: Instant
}

ApplicationVersionReviewSnapshot {
  versionLabel: VersionLabel
  launchUrl: LaunchURL
  rpcApiRange: RpcApiRange
  requiredCapabilities: []CapabilityName
  requiredScopes: []ScopeName
  optionalScopes: []ScopeName
  oauthRedirects: []OAuthRedirectGroup
}
```

ApplicationReview 是一次审核 attempt。它引用 Version，但拥有自己的受审核快照；不能用当前 Version 内容替代 snapshot。

### 用例端口

```go
type ApplicationReviewIDGenerator interface {
    NewUUIDv7() (ApplicationReviewID, error)
}

type Clock interface {
    Now() time.Time
}

type ScopeCatalog interface {
    EnsureAllRequestable(
        ctx context.Context,
        scopes []ScopeName,
    ) (ScopeCatalogRevision, error)
}

type LaunchURLSubmissionPolicy interface {
    Inspect(
        ctx context.Context,
        launchURL LaunchURL,
    ) (PreflightPolicyVersion, error)
}

type ApplicationReviewRepository interface {
    LoadSubmissionCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        expectedAdminID AuthID,
        expectedRevision int64,
    ) (*ApplicationVersion, error)

    Submit(
        ctx context.Context,
        candidate ApplicationVersion,
        reviewID ApplicationReviewID,
        expectedAdminID AuthID,
        scopeCatalogRevision ScopeCatalogRevision,
        preflightPolicyVersion PreflightPolicyVersion,
        submittedAt time.Time,
    ) (*ReviewSubmissionResult, error)
}
```

`Submit` 必须重新比较 applicationId、versionId、adminId、reviewStatus 和 revision，不能相信较早读取的 candidate 仍是当前状态。

### 数据模型

新逻辑 collection：`application_reviews`。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `reviewId` | 审核 attempt 稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | no | no |
| `versionId` | 被审核的 ApplicationVersion | string | UUIDv7 | `(versionId, attempt)` | no |
| `attempt` | Version 内审核次数 | int32 | `>= 1`，从 1 递增 | `(versionId, attempt)` | no |
| `sourceVersionRevision` | 生成快照时的 Version revision | int64 | `>= 1` | `(versionId, sourceVersionRevision)` | no |
| `status` | attempt 当前状态 | string enum | `PENDING/APPROVED/REJECTED`；本用例只写 PENDING | partial: one PENDING per versionId | no |
| `decision` | reviewer 的一次性决定 | object | UC-APP-005 定义；本用例固定为 null | no | yes |
| `draftRestoration` | 被拒绝后的草稿恢复审计 | object | UC-APP-006 定义；本用例固定为 null | no | yes |
| `snapshot.versionLabel` | 提交时版本标签 | string | 与 UC-APP-002 相同 | no | no |
| `snapshot.launchUrl` | 提交时入口 URL | string | public absolute HTTPS URI；最多 2048 UTF-8 bytes | no | no |
| `snapshot.rpcApiMinVersion` | 提交时最小 RPC major | int32 | `>= 1` | no | no |
| `snapshot.rpcApiMaxVersionExclusive` | 提交时首个不兼容 RPC major | int32 | `> min` | no | no |
| `snapshot.requiredCapabilities` | 提交时必需宿主能力 | array&lt;string&gt; | 已排序；元素唯一 | no | no |
| `snapshot.requiredScopes` | 提交时必需 scopes | array&lt;string&gt; | 已排序；元素唯一 | no | no |
| `snapshot.optionalScopes` | 提交时可选 scopes | array&lt;string&gt; | 已排序；元素唯一且不与 required 交叉 | no | no |
| `snapshot.oauthRedirects` | 提交时 OAuth 回调 | array&lt;object&gt; | BR-VER-018；已规范排序 | no | no |
| `scopeCatalogRevision` | scope 校验使用的 Auth catalog revision | int64 | Auth 单调递增版本 | no | no |
| `preflightPolicyVersion` | URL 提交预检规则版本 | string | 稳定策略标识，1–50 ASCII `[A-Za-z0-9._-]` | no | no |
| `submittedBy` | 实际提交者 | string | opaque authId | no | no |
| `submittedAt` | 提交时间 | datetime | UTC / RFC 3339 | no | no |

索引与 validator：

- reviewId 唯一索引。
- `(versionId, attempt)` 复合唯一索引。
- `(versionId, sourceVersionRevision)` 复合唯一索引。
- 对 `status = PENDING` 建立 versionId 部分唯一索引。
- `(status, submittedAt, reviewId)` 索引支持稳定审核队列分页。
- snapshot、提交身份和提交时间创建后不可修改。
- 本用例只允许插入 status=`PENDING` 且 decision/draftRestoration 均为 null。

`application_versions` 不增加字段，但 reviewStatus、revision、updatedBy 和 updatedAt 在本用例中一同变化。

### API 草图

```text
POST /applications/{applicationId}/versions/{versionId}/reviews
Authorization: <authenticated identity>
```

请求：

```json
{
  "expectedRevision": 3
}
```

响应：`201 Created`

```text
Location: /applications/{applicationId}/versions/{versionId}/reviews/{reviewId}
```

```json
{
  "review": {
    "reviewId": "review-uuid",
    "applicationId": "application-uuid",
    "versionId": "version-uuid",
    "attempt": 1,
    "sourceVersionRevision": 3,
    "status": "PENDING",
    "decision": null,
    "draftRestoration": null,
    "snapshot": {
      "versionLabel": "v1.0.0",
      "launchUrl": "https://example.edu/apps/course-table/v1/",
      "rpcApiMinVersion": 3,
      "rpcApiMaxVersionExclusive": 5,
      "requiredCapabilities": ["user.profile.v1"],
      "requiredScopes": ["profile.basic"],
      "optionalScopes": ["schedule.read"],
      "oauthRedirects": [{
        "clientType": "PUBLIC_PKCE",
        "redirectUris": ["https://example.edu/oauth/callback"]
      }]
    },
    "scopeCatalogRevision": 17,
    "preflightPolicyVersion": "submit-v1",
    "submittedBy": "auth-id-from-identity",
    "submittedAt": "2026-09-15T12:00:00Z"
  },
  "version": {
    "versionId": "version-uuid",
    "reviewStatus": "SUBMITTED",
    "revision": 4,
    "updatedBy": "auth-id-from-identity",
    "updatedAt": "2026-09-15T12:00:00Z"
  }
}
```

候选 HTTP 映射：

- expectedRevision 缺少或非法：`400 Bad Request`。
- revision 不匹配、非 DRAFT 或已有 PENDING review：`409 Conflict`，使用领域错误码区分原因。
- scope 或 URL 不满足提交条件：`422 Unprocessable Content`。
- Scope Catalog 或 URL 检查依赖不可用：`503 Service Unavailable`。

### 测试与验收

领域测试：

- 只有 DRAFT 可以进入 SUBMITTED。
- 提交产生与候选内容完全一致、集合顺序稳定且包含 oauthRedirects 的 snapshot。
- 提交增加 Version revision，并更新最近修改审计。
- snapshot 与提交审计创建后不可修改。
- 新 Review 的 decision 固定为 null。
- 新 Review 的 draftRestoration 固定为 null。
- attempt 在同一 Version 内递增，不参与 Version 身份或排序。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以提交。
- 使用 expectedRevision 加载候选，并在写入时再次校验。
- scopes 在提交时重新验证，并保存 catalog revision。
- oauthRedirects 在提交时按 BR-VER-018 重新验证并冻结进 snapshot。
- 开发 HTTP/私网 URL 不能提交；合规公网 HTTPS URL 可以提交。
- 外部检查失败时不调用最终 Submit。
- reviewId 和 submittedAt 只能来自系统端口。

Repository 集成测试：

- review 插入与 Version 状态/revision/审计更新全部提交或全部回滚。
- 两个相同 expectedRevision 的并发提交最多一个成功。
- 提交与草稿更新并发时不会审核旧内容。
- 提交与管理员转让并发时旧 admin 不能成功。
- `(versionId, attempt)`、`(versionId, sourceVersionRevision)` 和单 PENDING 唯一约束生效。
- 第二次合法提交取得递增 attempt，且不覆盖第一次 snapshot。
- applicationId/versionId 不匹配时返回 NotFound。

API 测试：

- 正确 expectedRevision 返回 201、Location 及 review/version 结果。
- 请求不能指定 reviewId、attempt、status、snapshot、decision、draftRestoration 或审计字段。
- 过期 expectedRevision 或非 DRAFT 返回 409，并保留可区分的领域错误码。
- 提交条件失败与依赖不可用的错误映射正确。

## 业务规则（UC-APP-004 权威正文）

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-001 -->
### BR-REV-001：提交权限

提交者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终原子写入时仍是 Application.adminId。

createdBy 只记录 Version 最初创建者；submittedBy 记录本次实际提交者。管理员转让后，新管理员可以提交旧管理员创建的 DRAFT。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-002 -->
### BR-REV-002：提交前状态

只有 `DRAFT` 可以提交。`SUBMITTED/APPROVED/REJECTED/REVOKED` 不能进入本用例。

同一 Version 同时最多有一个 `PENDING` review。对已提交请求进行普通重试不会创建第二条记录；如果客户端没有收到成功响应，应查询 Version 和最近一次 review，而不是移除并重建审核记录。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-003 -->
### BR-REV-003：乐观并发与 Version revision

- expectedRevision 必须等于读取候选和最终写入时的 Version.revision。
- 提交成功后 Version.revision 增加 1。
- updatedBy 设为 submittedBy，updatedAt 设为 submittedAt。
- ApplicationReview.sourceVersionRevision 保存状态迁移前的 expectedRevision。

revision 是整个 ApplicationVersion 的并发版本，不只统计草稿内容编辑。任何会改变 Version 内容或生命周期状态的行为都必须增加它。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004 -->
### BR-REV-004：审核快照

ApplicationReview.snapshot 必须复制以下规范化字段：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
oauthRedirects
```

snapshot 创建后不可修改。Application.name 和独立的 ApplicationProfileRevision 不进入本次版本审核快照；公开目录资料由其自身的 revision 审核流程负责。

审核记录的 status 和后续决策审计可以发生一次受控状态迁移，但这不允许改写 snapshot、sourceVersionRevision、submittedBy 或 submittedAt。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-005 -->
### BR-REV-005：审核 attempt

- reviewId 是系统生成的全局唯一 UUIDv7。
- attempt 在单个 versionId 内从 1 开始严格递增。
- `(versionId, attempt)` 唯一。
- `(versionId, sourceVersionRevision)` 唯一，防止同一个 Version 状态被提交两次。

Version 被拒绝后的编辑和重新提交需要后续用例先明确 `REJECTED -> DRAFT` 行为。每次重新提交都必须创建新的 attempt，旧记录永不覆盖。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-006 -->
### BR-REV-006：Scope 重新验证

提交时必须重新验证全部 requiredScopes 和 optionalScopes。DRAFT 创建或修改时合法，不代表提交时仍合法。

ApplicationReview 保存校验所依据的 scopeCatalogRevision。它用于审计“提交时使用了哪一版目录”，但不把 App Center 变成 Scope Catalog 的权威来源。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-007 -->
### BR-REV-007：公网 HTTPS 预检

可提交的 launchUrl 必须：

- 使用 `https`，且不含 userinfo。
- host 不是字面 IPv4/IPv6 地址。域名先按 non-transitional UTS #46 Lookup
  processing 转为 ASCII A-label；转换失败、空 label、或移除一个表示 DNS root
  的末尾 `.` 后仍含末尾 `.` 时不可提交。
- 规范化后的域名不是 IANA Special-Use Domain Names registry
  `2026-05-22` 快照中的名称或其子域。该快照包含 `localhost`、`.local`、
  `example`、`invalid`、`test`、`onion`、`alt`、`home.arpa` 及 registry
  中列出的其它专用名称。
- DNS 至少解析出一个地址，且所有 A/AAAA 结果都是允许访问的公网地址。
- 不解析到 IANA IPv4/IPv6 Special-Purpose Address registries `2025-10-09`
  快照中的任何前缀，也不解析到 private、loopback、link-local、unspecified、
  multicast、documentation、benchmark、CGNAT 或其它非 global-unicast 地址。
- IPv6 结果还必须位于 IANA 当前分配为 Global Unicast 的 `2000::/3`；其它
  IETF reserved IPv6 space 即使通用语言库把它分类为 unicast，也不能视为公网入口。

以上 registry 日期是 `submit-v1` 的冻结输入，不在运行时读取。IANA registry
变化时，必须显式更新 denylist 与测试，并分配新的 preflightPolicyVersion；不能在
相同 policy version 下静默改变已记录审核的解释。即使 registry 把某个
special-purpose 地址标为 globally reachable，本策略仍拒绝它，因为它不是普通公网
Application 入口地址。

本用例只做地址策略和 DNS 预检，不向目标发送 HTTP 请求，也不跟随重定向。未来若加入自动抓取或扫描，必须在每次连接及每次重定向前重新解析和校验地址，不能把本次预检当作永久 SSRF 保证。

ApplicationReview 保存 preflightPolicyVersion，便于以后解释提交时使用的规则版本。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-008 -->
### BR-REV-008：自托管内容的弱保证

snapshot 冻结的是登记信息，不是 launchUrl 指向的网页字节。开发者可能在 URL 不变时替换远端内容，因此审核通过也只能说明“审核时观察到的内容与登记信息被接受”。

在制品摘要、不可变托管或持续监控用例建立以前，API 和管理界面都不能宣称 App Center 已冻结或验证实际网页制品。

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-009 -->
### BR-REV-009：原子提交

以下操作必须全部成功或全部失败：

- 最终管理员检查。
- Version 所属、DRAFT 状态和 expectedRevision 检查。
- attempt 分配和唯一性检查。
- ApplicationReview 插入。
- Version 状态、revision 和更新审计变更。

MongoDB 实现应使用同一事务覆盖 Application、ApplicationVersion 和 ApplicationReview，或提供能证明相同语义的原子方案。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-002`

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-018 -->
### BR-VER-018：版本化 OAuth 回调

`oauthRedirects` 是受审核的版本内容，不属于 OAuthClient，也不从 launchUrl 推导。它是 0–2 个回调组组成的非 null 数组：

```text
OAuthRedirectGroup {
  clientType: PUBLIC_PKCE | CONFIDENTIAL_SECRET
  redirectUris: []RedirectURI
}
```

- 每种 clientType 至多一组；每组包含 1–10 个不重复 URI。空数组表示该 Version 不提供 OAuth/OIDC 回调。
- URI 必须是绝对 HTTPS URL，最多 2048 UTF-8 bytes；禁止 userinfo、fragment、wildcard、IP literal、localhost，以及 [BR-REV-007](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-007) 固定的 IANA `2026-05-22` special-use 域名或其子域。
- 禁止预占 OAuth/OIDC 响应参数 `code/state/iss/error/error_description/error_uri`。
- 同一组的所有 URI 必须使用同一个规范 DNS hostname。hostname 使用 non-transitional UTS #46 Lookup 转为小写 ASCII A-label；输入必须已经是规范表示，不静默改写。其余 URL 部分保存后按完整字符串精确匹配。
- callback path、query 和 port 可以不同；运行时不做前缀匹配。客户端必须控制回调处理，App Center 不向回调地址发起探测请求。
- 回调组按 clientType 固定顺序保存，组内 URI 按 Unicode code point 排序。输入顺序不表达业务含义。

OAuthClient 创建时从当前批准并发布的回调组派生不可变 sector。存在该运行上下文的 client 后，后续发布由 UC-APP-007 检查同 type 回调组的 hostname；改变 hostname 需要新的 clientId。Version 草稿本身可以在 client 创建前存在，因此创建/编辑阶段不依赖 OAuthClient。

## 架构决定（仅本次需要的章节）

### ADR-001：Scope Catalog 权威来源与缓存（`PROPOSED`）

#### 权威来源

Auth 是 Scope Catalog 唯一权威来源。Auth 提供可读取完整快照的内部接口：

```text
ScopeCatalogSnapshot {
  revision: int64
  scopes: []ScopeDefinition
  generatedAt: Instant
}
```

revision 必须在 Auth 内单调递增。提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 定义；跨服务 `ScopeDefinition` 首版投影和 gRPC 方法由 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md) 定义。

ScopeCatalog adapter 在完成校验时一并返回所使用的 snapshot revision。创建和修改草稿可以忽略它；UC-APP-004 将它写入 ApplicationReview，用于说明提交时依据的 Auth 目录版本。

#### 第一阶段缓存

App Center 的 ScopeCatalog adapter 使用每进程 read-through cache：

- TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 使用 Go duration 文本配置，未设置时默认 `5m`；显式值为空、无法解析、为零或负数时进程组装失败，不静默回退。
- 进程启动或 cache miss 时同步读取 Auth 快照。
- TTL 内直接使用缓存快照。
- TTL 到期时同步刷新；使用 singleflight 合并同一时刻的刷新请求。
- 刷新失败时不使用过期快照创建版本，返回 `ScopeCatalogUnavailable`。
- Auth revision 发生回退时视为不可用并 fail closed，避免用较旧快照覆盖进程已经观察到的较新事实。
- 不为此单独引入 Redis。

这是有界缓存，不是 App Center 自己的 Scope Catalog。缓存内容不能被 App Center 管理接口修改。

环境变量只由 config/composition boundary 读取；Cache adapter 通过构造参数接收已经校验的 TTL、Clock 与 snapshot source，不直接读取进程环境。真实 Auth transport 必须实现共享 gRPC 契约；测试可以使用实现同一生成接口的 Auth Server 或 port fake，不得在生产代码中硬编码目录。

#### 多阶段校验

- 创建 DRAFT：使用上述有界缓存，尽早发现无效 scope。
- 提交审核：重新确认 scope 仍允许新版本申请。
- reviewer 批准：再次确认 snapshot 中的全部 scope，并把所用 catalog revision 写入 decision.approvalValidation；详见 UC-APP-005。
- 放入发布槽位：再次确认 approved snapshot 中的 scope，并把所用 catalog revision 写入 PublicationHistory；UC-APP-007 首先应用于 test 槽位。
- consent/token/用户数据读取：Auth 必须以自己的当前规则做最终授权，不能相信 App Center 过去的校验结果。

因此短暂缓存只影响开发体验，不会成为实际授权边界。

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

### `platform/contracts/auth-scope-catalog-v1.md`：Auth Scope Catalog v1 跨服务契约

#### gRPC 方法

首版只提供内部原生 gRPC：

```text
/auth_center.v1.scope_catalog.ScopeCatalog/GetScopeCatalogSnapshot
```

Proto 结构：

```proto
service ScopeCatalog {
  rpc GetScopeCatalogSnapshot(GetScopeCatalogSnapshotRequest)
      returns (GetScopeCatalogSnapshotResponse);
}

message GetScopeCatalogSnapshotRequest {}

message GetScopeCatalogSnapshotResponse {
  int64 revision = 1;
  google.protobuf.Timestamp generated_at = 2;
  repeated ScopeDefinition scopes = 3;
}

message ScopeDefinition {
  string name = 1;
  bool requestable = 2;
}
```

不声明 `google.api.http` annotation，不经 Gateway 暴露，不提供浏览器或 gRPC-Web 入口。

#### 快照语义

- `revision` 必须大于零，并遵循 [BR-SCP-003](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- 消费方只把 `requestable = true` 的 name 用于新申请校验；它不是最终授权结果。
- 消费方遇到未知追加字段时必须忽略，以保持向后兼容。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证内部服务身份。Auth Center 在验签后按固定 full method → `auth.scope-catalog.read` 映射检查 caller 注册表；认证成功不自动产生读取权限。

测试 Auth Server 可以验证 consumer 行为，但生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_SCOPE_CATALOG_READ_FORBIDDEN` |
| 权威目录暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含凭证、存储查询、连接地址、Scope 私有元数据或堆栈。调用方不得把失败时持有的过期快照包装成本次成功响应。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. gRPC full method 与 package/service/rpc 名称准确。
2. request message 没有业务字段或用户身份字段。
3. response 字段号和类型与本契约一致。
4. 空目录编码为空列表，不是错误或伪造占位 Scope。
5. duplicate/empty name、非正 revision、无效 generatedAt 或非稳定排序不能作为成功快照。
6. `UNAUTHENTICATED`、`PERMISSION_DENIED`、`UNAVAILABLE` 与稳定 reason 映射一致。
7. App Center E2E 的测试 Auth Server 实现同一生成接口，不维护另一份手写 wire model。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-004`（use-cases/UC-APP-004-submit-application-version-review.md）：旧实现观察、后续用例、迁移说明、变更记录
- `UC-APP-002`（use-cases/UC-APP-002-create-application-version.md）：目标与范围、当前 ApplicationVersion、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、后续接口工作、迁移说明、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/auth-scope-catalog-v1.md`（docs 根级共享文档）：目的与所有权、兼容性、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-004-submit-application-version-review.md` | 509 | `f68b6f1eadb6` |
| `use-cases/UC-APP-002-create-application-version.md` | 463 | `aed995d52573` |
| `adr/ADR-001-scope-catalog-cache.md` | 112 | `a5fe7365b96f` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/auth-scope-catalog-v1.md` | 91 | `cab448326f29` |
