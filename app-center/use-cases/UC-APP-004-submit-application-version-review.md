# UC-APP-004：提交应用版本审核

状态：`ACCEPTED`

## 修订范围与审核状态

2026-11-04 用户已接受本次修订并要求开始更新。提交时固定政策、未上线不做旧模型/数据/接口兼容，均为当前实施依据；旧已交付基线和历史记录保留，本次接受不表示新增实现已完成。实施范围与依赖见[已接受提案](../implements/2026-11-03-submission-bound-review-policy-proposal.md)。

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 revision 为前提，把一个满足提交条件的 DRAFT ApplicationVersion 提交为一次可审计的审核 attempt。

本用例完成两件不可分割的事：

- 复制当前受审核内容，并绑定本次提交事务中生效的审核策略，创建状态为 `PENDING` 的 ApplicationReview。
- 将 ApplicationVersion.reviewStatus 从 `DRAFT` 改为 `SUBMITTED`。

本用例不负责：

- reviewer 批准或拒绝。
- 开发者撤回提交。
- 修改被拒绝的 Version，或把 `REJECTED` 恢复为 `DRAFT`。
- 把审核通过的 Version 放入 test/grey/stable 发布槽位。
- 抓取、托管或冻结开发者网页内容。
- 发送站内消息、邮件或 RabbitMQ 通知。

审核队列可以通过查询 `PENDING` ApplicationReview 构建，不需要在提交写路径提前引入消息系统。

## 提交结果

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
  policyBinding: { version }
```

Version 内容字段本身不改变。后续 reviewer 只审核 ApplicationReview.snapshot，不重新把可变的 ApplicationVersion 当成审核输入。

## 旧实现观察

旧实现只有 Application 级 `DEVELOPING/AUDITING/PUBLISHED/...` 状态和可直接修改的 Version 发布状态，没有独立的版本审核记录、提交快照或 reviewer 决策模型。

### KEEP

- 开发者必须拥有应用管理权限才能发起审核。
- 审核中状态需要能被查询，以支持后台审核队列。
- 进入审核前需要检查版本入口和申请权限。

### CHANGE

- 审核对象从整个 Application 改为一次明确的 ApplicationVersion 内容快照。
- `SUBMITTED` 只表达 Version 正在等待审核，不表达已发布。
- 每次提交创建独立 ApplicationReview attempt，而不是覆盖上一次审核结果。
- 提交使用 expectedRevision，防止开发者提交自己没有看到的草稿内容。
- 重新验证 Scope Catalog 和公网 HTTPS 条件，不只依赖创建 DRAFT 时的旧结果。
- Version 状态变化也增加 revision 并更新 updatedBy/updatedAt。

### DROP

- 由调用者任意把 Application.status 设置为 `AUDITING`。
- 把审核、批准与 stable/grey/test 发布位置混在一个 status 字段中。
- reviewer 直接读取可能变化的草稿作为审核依据。
- 提交审核时顺便批准、发布或创建 OAuth client。

### UNKNOWN

- 审核人角色、分配机制、检查清单和 SLA；由审核决定用例设计。
- 自托管内容最终采用版本化 URL、构建摘要、平台托管还是持续监控。
- 是否需要开发者主动撤回已提交审核。

## 输入与身份

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

reviewId、attempt、status、snapshot、policyBinding、decision、draftRestoration、submittedBy 和 submittedAt 都不能由请求正文指定。客户端不选择提交政策。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，expectedRevision `>= 1`。
3. Repository 读取候选 Version，并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - Version 属于路径中的 Application。
   - reviewStatus 是 `DRAFT`。
   - revision 等于 expectedRevision。
4. 通过 ScopeCatalog 重新确认 requiredScopes 和 optionalScopes 当前仍允许被新版本申请，并取得本次 Auth catalog revision。
5. 按 BR-VER-018 重新验证 oauthRedirects 的双数组结构、规范 URL 和安全限制。
6. 通过 LaunchURLSubmissionPolicy 确认 launchUrl 是当前可提交审核的公网 HTTPS URL。
7. 生成 UUIDv7 reviewId，并从 Clock 取得 submittedAt。
8. Repository 在同一事务或等价原子边界中重新确认步骤 3 的全部条件，然后：
   - 为该 Version 分配下一个 attempt，从 1 开始递增。
   - 复制候选 Version 的受审核字段形成不可变 snapshot。
   - 按下节在同一事务读取并保护当前 Version 策略选择，将 policyBinding 与 snapshot 一同写入。
   - 插入 status 为 `PENDING`、decision 和 draftRestoration 均为 null 的 ApplicationReview。
   - 将 Version.reviewStatus 改为 `SUBMITTED`。
   - 将 Version.revision 原子增加 1，并写入 updatedBy、updatedAt。
9. 返回新建的 ApplicationReview 和更新后的 Version 摘要。

外部检查与最终写入之间允许发生并发，但最终写入必须再次比较 revision。只要 Version 内容、状态或管理员已经变化，就不能保存基于旧候选内容生成的审核快照。

## 异常流程

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
- 当前策略缺失、多 ACTIVE、选择与定义不一致或正式定义不完整：内部一致性失败，不创建 Review、不迁移 Version。存储故障按依赖不可用处理。
- reviewId 冲突或持久化失败：内部失败，不产生半完成提交。

applicationId 与 versionId 不匹配时不返回 Version 的真实所属应用。所有失败都必须保持 Version 为原状态且不创建 review。

## 业务规则

<a id="br-rev-001"></a>
### BR-REV-001：提交权限

提交者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终原子写入时仍是 Application.adminId。

createdBy 只记录 Version 最初创建者；submittedBy 记录本次实际提交者。管理员转让后，新管理员可以提交旧管理员创建的 DRAFT。

<a id="br-rev-002"></a>
### BR-REV-002：提交前状态

只有 `DRAFT` 可以提交。`SUBMITTED/APPROVED/REJECTED/REVOKED` 不能进入本用例。

同一 Version 同时最多有一个 `PENDING` review。对已提交请求进行普通重试不会创建第二条记录；如果客户端没有收到成功响应，应查询 Version 和最近一次 review，而不是移除并重建审核记录。

<a id="br-rev-003"></a>
### BR-REV-003：乐观并发与 Version revision

- expectedRevision 必须等于读取候选和最终写入时的 Version.revision。
- 提交成功后 Version.revision 增加 1。
- updatedBy 设为 submittedBy，updatedAt 设为 submittedAt。
- ApplicationReview.sourceVersionRevision 保存状态迁移前的 expectedRevision。

revision 是整个 ApplicationVersion 的并发版本，不只统计草稿内容编辑。任何会改变 Version 内容或生命周期状态的行为都必须增加它。

<a id="br-rev-004"></a>
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

审核记录的 status 和后续决策审计可以发生一次受控状态迁移，但这不允许改写 snapshot、policyBinding、sourceVersionRevision、submittedBy 或 submittedAt。policyBinding.version 指向本次提交绑定的不可变正式检查定义；与内容 snapshot 一起冻结。

<a id="br-rev-005"></a>
### BR-REV-005：审核 attempt

- reviewId 是系统生成的全局唯一 UUIDv7。
- attempt 在单个 versionId 内从 1 开始严格递增。
- `(versionId, attempt)` 唯一。
- `(versionId, sourceVersionRevision)` 唯一，防止同一个 Version 状态被提交两次。

Version 被拒绝后的编辑和重新提交需要后续用例先明确 `REJECTED -> DRAFT` 行为。每次重新提交都必须创建新的 attempt，旧记录永不覆盖。

<a id="br-rev-006"></a>
### BR-REV-006：Scope 重新验证

提交时必须重新验证全部 requiredScopes 和 optionalScopes。DRAFT 创建或修改时合法，不代表提交时仍合法。

ApplicationReview 保存校验所依据的 scopeCatalogRevision。它用于审计“提交时使用了哪一版目录”，但不把 App Center 变成 Scope Catalog 的权威来源。

<a id="br-rev-007"></a>
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

<a id="br-rev-008"></a>
### BR-REV-008：自托管内容的弱保证

snapshot 冻结的是登记信息，不是 launchUrl 指向的网页字节。开发者可能在 URL 不变时替换远端内容，因此审核通过也只能说明“审核时观察到的内容与登记信息被接受”。

在制品摘要、不可变托管或持续监控用例建立以前，API 和管理界面都不能宣称 App Center 已冻结或验证实际网页制品。

<a id="br-rev-009"></a>
### BR-REV-009：原子提交

以下操作必须全部成功或全部失败：

- 最终管理员检查。
- Version 所属、DRAFT 状态和 expectedRevision 检查。
- attempt 分配和唯一性检查。
- 当前有效审核策略的选择、真实并发栅栏及完整 policyBinding 写入。
- ApplicationReview 插入。
- Version 状态、revision 和更新审计变更。

MongoDB 实现应使用同一事务覆盖 Application、ApplicationVersion 和 ApplicationReview，或提供能证明相同语义的原子方案。

## 策略绑定与提交并发

本节落实 BR-REV-004/009。Version 与 Profile 分别选择自己集合中的政策，Profile 提交由 UC015 BR-PRF-018/021 引用同一协议，不共享政策正文或新增政策服务。

每次提交保存 `policyBinding { version }`。version 为 1–50 ASCII `[A-Za-z0-9._-]`；绑定与内容在同一次提交完成，沿用 submittedAt 审计，不新增来源分支或重复时间字段。完整定义按 `(kind, version)` 从对应不可变政策仓库稳定读取。新提交只有完整可解释的定义才能成功；不以 preflightPolicyVersion 或 scopeCatalogRevision 代替审核政策，不复制另一个可修改副本。

复用现有 policy 文档的 coordinationRevision：提交事务严格确认本类恰好一个 ACTIVE，读取其完整定义，再按读取的 version、status=ACTIVE、coordinationRevision 作真实条件写（增加技术计数），把 policyBinding、内容 snapshot、attempt 和 SUBMITTED 状态同事务提交。发布退休 A 时也写同一 A 文档；原来位于决定路径的退休写栅栏移到提交路径，不新增 head/全局指针对象。仅 snapshot 读后插入 Review 不足以排除旧读。

归属以提交事务与发布事务的串行提交顺序确定：提交先成功则绑定 A；A→B 发布先成功则旧 A 上的提交不能按旧快照成功，事务重试读取 B 后才绑定 B。重试复用命令、reviewId 和审计时间，但重新选择事务内有效政策；失败不留下绑定或 Review。每个成功提交恰有一份当时有效的规则，不按页面打开时间、事务外缓存或 submittedAt 猜测。技术计数会被提交增加，发布人员不持有它作长期业务前置。

版本唯一索引、逐事务唯一 ACTIVE 复查及对原 ACTIVE 的共享真实条件写共同保护选择/切换；并发发布只能有一个基于 A 成功，不需要另建选择状态。零/多 ACTIVE 或坏定义时新提交/发布失败关闭，不任取一条。绑定后查询/决定只读自身引用与不可变定义，不要求仍 ACTIVE，也不为退休写政策栅栏。

拒绝后 Version 经 UC006 恢复/编辑/重提形成新 attempt，Profile 经 UC013 新建修订再提交，两者均重新选择当时有效政策。旧 attempt 保留原绑定与终态。验收覆盖两种提交胜序、重试、发布回滚、重复 source revision 与无部分绑定；以上方案已接受；实现与验证状态以实施导航为准。

## 最小领域模型

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
  policyBinding: { version }
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
  oauthRedirects: OAuthRedirectConfiguration
}
```

ApplicationReview 是一次审核 attempt。它引用 Version，但拥有自己的受审核快照；不能用当前 Version 内容替代 snapshot。

## 用例端口

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

## 数据模型

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
| `snapshot.oauthRedirects` | 提交时 OAuth 回调 | object | `pkceRedirectUris/confidentialRedirectUris`；BR-VER-018；已规范排序 | no | no |
| `policyBinding` | 本次提交的不可变审核策略引用 | object | 仅 version；定义见本 UC 策略绑定章节 | no | no |
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
- snapshot、policyBinding、提交身份和提交时间创建后不可修改；所有 Review 从新模型创建起就具有绑定；测试夹具按 UC005 初始化章节重建。
- 本用例只允许插入 status=`PENDING` 且 decision/draftRestoration 均为 null。

`application_versions` 不增加字段，但 reviewStatus、revision、updatedBy 和 updatedAt 在本用例中一同变化。

## API 草图

policyBinding 是 Review 的内部持久化事实，不增加开发者提交输入或响应字段；Reviewer 投影见 UC030，管理员历史查询的最小披露白名单不扩展。

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
      "oauthRedirects": {
        "pkceRedirectUris": ["https://example.edu/oauth/callback"],
        "confidentialRedirectUris": []
      }
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

## 测试与验收

领域测试：

- 只有 DRAFT 可以进入 SUBMITTED。
- 提交产生与候选内容完全一致、集合顺序稳定且包含 oauthRedirects 的 snapshot。
- 提交增加 Version revision，并更新最近修改审计。
- snapshot、policyBinding 与提交审计创建后不可修改。
- A 下成功提交后切换 B，原 attempt 保持 A；新提交和 UC006 恢复后的重提绑定 B；并发顺序、缺策略和事务回滚见下节。
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

## 后续用例

UC-APP-004 之后的 reviewer 用例是：

```text
UC-APP-005：审核 ApplicationVersion
```

它负责 reviewer 身份、检查结果、批准/拒绝理由，以及 ApplicationReview 与 ApplicationVersion 的一致状态迁移。详见 [UC-APP-005](UC-APP-005-decide-application-version-review.md)。被拒绝版本将由后续独立用例恢复为 DRAFT。

## 迁移说明

既有实现需要 migration 为历史 Review snapshot 回填 `oauthRedirects: {pkceRedirectUris: [], confidentialRedirectUris: []}`，并同步 Version 依附配置读取、snapshot 深拷贝、schema、API 与测试；完成前不覆盖 OAuth 扩展。旧 Application 的 `AUDITING` 状态和直接改审核状态 API 不保留。

## 变更记录

- 2026-11-04：用户接受无旧模型兼容的提交政策绑定方案，开始实施；接受不代表交付完成。

- 2026-11-04：按用户确认的未上线前提，删除旧模型、旧数据和旧接口兼容，改为统一新模型初始化及单一契约交付。

- 2026-09-15：建立 UC-APP-004；提交时创建独立审核快照，把 Version 原子迁移为 SUBMITTED，并重新验证 Scope Catalog 与公网 HTTPS 入口。
- 2026-09-15：UC-APP-005 引入一次性 decision；UC-APP-004 创建 PENDING Review 时将其初始化为 null。
- 2026-09-15：UC-APP-006 引入拒绝后的 draftRestoration；UC-APP-004 创建 Review 时将其初始化为 null。
- 2026-09-27：审核 snapshot 增加 oauthRedirects，并在提交时复查 BR-VER-018。
- 2026-09-27：审核 snapshot 改为冻结 Version 依附的 pkce/confidential 双数组配置。
