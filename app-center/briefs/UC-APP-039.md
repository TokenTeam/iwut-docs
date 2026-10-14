<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-039 --spec tools/brief-specs/UC-APP-039.json -->
# Brief — UC-APP-039：查询我的 ApplicationProfileRevision 列表与详情

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-039` 查询我的 ApplicationProfileRevision 列表与详情 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PRF-047`–`BR-PRF-056`（10 条） |
| 外部引用 BR | `BR-PRF-003`、`BR-PRF-004`、`BR-PRF-005`、`BR-PRF-006`、`BR-PRF-007`、`BR-PRF-008`、`BR-PRF-018`、`BR-PRF-019`、`BR-PRF-020`、`BR-PRF-025`、`BR-PRF-026`、`BR-PRF-027`、`BR-PRF-028`、`BR-PRF-030`、`BR-PRF-031`、`BR-PRF-032`（来自 `UC-APP-013`、`UC-APP-014`、`UC-APP-015`、`UC-APP-016`） |
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

### 设计结论

1. 当前管理员可读取全部资料修订，包括暂停、归档、CLOSING/CLOSED Application 的保留历史；不要求当前 Developer 资格仍为 APPROVED。
2. 详情返回修订完整当前内容和可分页遍历的审核历史；REJECTED 内容按保存的原文返回，不恢复原修订。
3. 保留 createdBy 与必要时间；不披露 updatedBy、submittedBy、Reviewer 身份、confirmed checks、内部策略内容或不可变审核 snapshot 正文。
4. 查询采用同一 majority snapshot、绑定当前管理权的签名游标与 2 MiB 编码响应预算；超大单项明确报错，不截断正文或跳过记录。

管理员语义已接受并同步到 [Profile 管理查询契约](../query-contracts/profile-management.md)。Reviewer 部分继续由 [UC-APP-031](../use-cases/UC-APP-031-query-application-profile-reviews.md) 管理。

### 目标与范围

本用例为 Developer Console 交付两个私有读取能力：

- `ListApplicationProfileRevisions`：列出一个 Application 的资料修订，可按一个 reviewStatus 过滤。
- `GetApplicationProfileRevision`：读取一个资料修订的完整当前内容、当前工作/公开指针和审核历史的一页。

它补齐 UC-APP-029 的资料管理摘要之外的历史查询，也提供 UC-APP-014/015 写命令前读取当前 revision、以及 UC-APP-013 新建草稿前读取被拒绝内容的正式来源。命令仍在执行时重新校验身份、状态、revision 和指针；读取结果不替代写入授权。

不增加创建、提交、决定、恢复、复制、删除、资料回滚或放弃草稿命令，不提供 Reviewer 队列、平台跨 Application 查询、用户公开目录、Tester 管理、通知或受控 icon 资产。查询不调用 Auth、Scope Catalog、DNS 或 icon URL。

### 参与者与授权

调用者为已验证的可信 USER，authId 必须等于 snapshot 中 Application 当前保存的 adminId。Developer 资格、Reviewer 权限、Tester、SYSTEM 或平台运维权限均不替代当前管理关系。

Application 不存在、调用者不是当前管理员、目标修订不存在或不属于路径 Application，统一返回 `ApplicationProfileManagementNotFound`。非管理员不能通过此查询判断其他 Application 的资料是否存在。

ACTIVE/AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED、CLOSING/CLOSED 的保留记录均可由其保存的当前/最后管理员读取。CLOSED 读取不恢复 owner 义务、配额、在线资格或写权限。

### 查询输入与 API 草图

```text
ListApplicationProfileRevisionsQuery {
  applicationId
  reviewStatus?: DRAFT | SUBMITTED | APPROVED | REJECTED
  pageSize: 1..100 = 20
  pageToken?
}

GetApplicationProfileRevisionQuery {
  applicationId
  profileRevisionId
  reviewPageSize: 1..100 = 20
  reviewPageToken?
}
```

内部 HTTP：

```text
GET /v1/applications/{application_id}/profile-revisions
GET /v1/applications/{application_id}/profile-revisions/{profile_revision_id}
```

外部仅由 Gateway 增加 `/app-center` 前缀。拟在现有 `app_center.v1.application_profile_revision.ApplicationProfileRevision` 服务追加同名查询 RPC；不改变创建/编辑的现有字段号或行为。HTTP GET 不接受正文、身份/审计 query 或未知参数；列表只接受 reviewStatus/pageSize/pageToken，详情只接受 reviewPageSize/reviewPageToken。

pageToken/reviewPageToken 为最多 4096 字节的不透明字符串。省略和空字符串表示首批查询。HTTP 省略 pageSize/reviewPageSize 使用 20，显式给出的值须在 1..100；原生 gRPC 两个 size 字段的默认 0 使用 20。时间按 UTC RFC3339 返回，int64 使用 ProtoJSON 字符串表示。

### 列表投影

列表按 `(sequence DESC, profileRevisionId DESC)` keyset 排序；sequence 在 Application 内仍须唯一。结果包含 items、nextPageToken（可空）、asOf 和一次页级 profileState：

```text
profileState {
  workingProfileRevisionId: UUIDv7 | null
  currentPublishedProfileRevisionId: UUIDv7 | null
}

AdminProfileRevisionSummary {
  profileRevisionId, sequence, reviewStatus, revision
  displayName, description: string | null, icon: string | null
  createdAt, updatedAt
  isCurrentWorkingRevision, isCurrentPublished
  latestReview: {
    profileReviewId, attempt, status, submittedAt
    decidedAt?, outcome?
  } | null
}
```

description 不在服务端截成摘要。空列表仍返回合法 profileState/asOf 和空 items。过滤后当前指针可能不在 items 中，不能把“当前项未返回”解释为指针为空。

尚未创建任何资料的 Application 可以返回空资料状态；已经存在修订或 Review 却缺失其必需 Profile 根记录，属于关系损坏。

### 详情与审核历史

```text
AdminProfileRevisionDetail {
  applicationId, profileRevisionId, sequence, reviewStatus, revision
  content { displayName, description: string | null, icon: string | null }
  createdBy, createdAt, updatedAt
  profileState
  isCurrentWorkingRevision, isCurrentPublished
  latestReview: AdminProfileReviewSummary | null
  reviews: AdminProfileReviewSummary[]
  nextReviewPageToken: string | null
  asOf
}

AdminProfileReviewSummary {
  profileReviewId, attempt, status, sourceRevision, submittedAt
  decision: {
    outcome, reason: string | null, policyVersion, decidedAt
  } | null
}
```

reviews 按 `(attempt ASC, profileReviewId ASC)` 排序，连续分页能遍历该修订的全部保留历史。latestReview 独立表示当前最高 attempt，不因为历史页停在早期记录而变化；当它也在 reviews 中出现时，两份投影必须一致。

这是对旧候选契约“一个详情响应返回完整 reviews 数组”的有界替代，不新增独立历史写入或复制关系。当前正常新修订首次审核 attempt=1、没有恢复入口；分页不引入新 attempt 或暗示 REJECTED 可重新提交。

展示当前内容用 ProfileRevision；审核摘要取不可变 Review 的状态和 decision。管理员详情不返回 Review snapshot 正文，不把当前修订内容冒充提交时 snapshot。审核人需要完整 snapshot 时仍使用 UC031 的独立授权查询。

REJECTED 内容遵循 UC016 的原文保留规则。合法保存但不符合当前资料内容限制的拒绝记录仍可读；不执行 NFC 规范化、trim、当前长度复检或 icon 外部验证。非法 BSON/UTF-8、引用、状态或审计结构仍失败关闭，不能把结构损坏解释为“允许坏内容”。前端预填后调用普通创建命令，继续由 UC013 校验新 DRAFT。

### 一致性、游标与响应预算

单个列表页或详情在一个 MongoDB majority read-only snapshot 中确认当前 admin、管理权 revision、Profile 指针、目标修订及所需 Review。列表批量读取，不能逐项建立 RPC/transaction；不保存投影或可用性，不写 Application fence。

转让、编辑、提交、决定和关闭与读取并发时，结果必须完整落在提交前或提交后，不能拼接两个时点。各次分页是独立 snapshot，asOf 不承诺跨请求冻结整个数据集；已经返回的旧管理员响应无法撤回。

游标使用独立 domain 的 HMAC-SHA-256 签名，绑定版本、查询 kind、调用者、规范化 Application ID、当前 ownershipRevision、过滤条件、排序键，以及详情历史的 profileRevisionId。列表与审核历史 token 不能互换。复用已验证 Service Identity key material 的独立派生 key；不把 JWT 或 OAuth credential 作为游标。

绑定上下文可以使用固定长度摘要，必须支持合法长 opaque authId。先验证当前管理员，再判断 token；旧管理员统一 NOT_FOUND。转让后同一用户再次取得管理权，其旧 ownership-bound token 仍失效。修改 pageSize 可以继续翻页；换调用者、Application、修订、状态过滤、kind 或签名 key 的旧 token 返回 `InvalidApplicationProfileManagementPageToken`。

同一响应在 HTTP JSON 和原生 gRPC 的编码大小均不得超过 2 MiB。预算检查涵盖所有投影、metadata、游标、latestReview 和重复字段：

- 列表或审核历史页允许因预算提前结束，但 token 只推进到最后实际返回的记录，不跳过已加载但未返回的记录。
- 每条成功返回的正文和 reason 完整保留；不得裁剪字段、替换内容、省略损坏关系或返回部分详情。
- 单个必须返回的修订/最新审核/历史项即超过预算时，明确返回 `ApplicationProfileManagementResponseTooLarge`（HTTP 413 / gRPC RESOURCE_EXHAUSTED），不伪装为损坏或生成不能前进的空页 token。

必要来源包括当前 Profile 指针的被引用修订、当次项目及 lookahead、最新 Review 和返回的历史页。至少校验跨 Application 引用、悬空指针、工作/公开状态、重复 ID/sequence/attempt、时间与正 revision、PENDING/decision/sourceRevision/snapshot 的既有 UC015/016 不变量。历史 APPROVED 不是当前公开修订是正常情况；合法过去策略退休不使历史决定不可读。

不要求在每页穷尽扫描全部 Application 历史；必要来源损坏则整次查询 INTERNAL，不跳项、不回退到当前公开资料、不返回部分结果。

### 隐私与错误

成功、空结果及所有错误均为 `private, no-store`。响应只返回上述管理投影，不返回 updatedBy、submittedBy、decidedBy、Reviewer 身份、confirmedCheckIds、approvalValidation、内部检查项/策略正文、利益冲突提示、当前 policy 或其他业务数据。policyVersion 只表示历史 decision 的策略标识，不从当前策略重新解释旧决定。

查询不产生领域审计、已读记录或 side effect。技术日志/trace 遵循 ADR-007，不记录资料正文、reason、token 或自由输入；metric 使用固定 operation，不含用户/资源 ID。

| 情况 | 稳定错误 | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信 USER | 复用现有身份错误 | 401 / UNAUTHENTICATED |
| Application/修订不可见 | `ApplicationProfileManagementNotFound` | 404 / NOT_FOUND |
| 非法 Application ID、过滤或分页参数 | `InvalidApplicationProfileManagementQuery` | 400 / INVALID_ARGUMENT |
| 非法、篡改或上下文不匹配 token | `InvalidApplicationProfileManagementPageToken` | 400 / INVALID_ARGUMENT |
| 必需来源结构或关系损坏 | `ApplicationProfileManagementStateInconsistent` | 500 / INTERNAL |
| 当前存储不可用 | `ApplicationProfileManagementUnavailable` | 503 / UNAVAILABLE |
| 单个必要结果超过响应预算 | `ApplicationProfileManagementResponseTooLarge` | 413 / RESOURCE_EXHAUSTED |

合法但不存在、属于其他 Application 或格式非法的 profileRevisionId 按同一修订 NotFound 隐藏。超时和存储错误不转换为成功空页，不披露数据库错误或原始内容。

### 验收矩阵与交付边界

1. 当前管理员及资格已下降的管理员成功读取四种状态；非管理员、仅 Reviewer/Tester/运维权限和路径伪造统一拒绝；全部保留生命周期组合可读。
2. 从未创建资料返回空页；当前工作/公开指针在页外仍正确，历史批准不是当前公开正常；REJECTED 原文、null/空串语义和合法坏内容保持逐字段一致。
3. 列表状态过滤、默认/上下界 pageSize、稳定 keyset、历史分页/latestReview 一致、所有历史可遍历；长 opaque authId 可正常继续。
4. token 篡改、跨 caller/Application/父修订/kind/filter、转让后旧管理员及转出再转入均按约定拒绝；改 pageSize 可继续。
5. sourceRevision、状态/decision、snapshot、指针、BSON duplicate key、时间、唯一 ID/sequence/attempt 和 lookahead 损坏失败关闭，无部分结果或自动修复。
6. 创建/编辑/提交/批准/拒绝、管理员转让、归档/暂停/关闭并发的提交前后 snapshot 可证明；读取不写 fence/审计或调用外部依赖。
7. 两协议预算、实际生成 HTTP client、提前结束不跳项、超大单项、所有错误与 no-store、响应隐私字段白名单通过自动化验证。
8. 现有 UC013–016/029/031/034、目录与运行消费行为保持原有验收通过，不加入任何新写能力。

在 `internal/profile/domain/usecase/port`、Mongo/transport adapter 与 composition root 实施。复用既有模型、严格重建和 query snapshot 设施，按需要新增显式 `0032` 查询索引 migration/readiness；不改变既有审核状态、事实或内容保留规则，不在启动时隐式迁移。

生成对应 spec/brief、声明工作包后才开始实现。最终要求 Go 1.25.5、API/Wire 一致性和完整 `make check-full`；若实际工作改变 Auth 契约，则按用户要求暂停并交接其他 agent，不扩大本任务代码范围。所有修改保持本地，生产部署另审。

本用例于 2026-10-14 经用户审核接受。Query Contract 管理员部分、Capability Map、implements 覆盖与 registry 同步，保留 Reviewer UC031 已接受语义。

### 既有规则依赖

资料字段与审计复用 UC013 的 BR-PRF-003、BR-PRF-004、BR-PRF-005、BR-PRF-006、BR-PRF-007、BR-PRF-008；提交的不可变快照、attempt 和状态复用 UC015 的 BR-PRF-018、BR-PRF-019、BR-PRF-020；审核关系、状态同步、理由、历史策略和终态原文复用 UC016 的 BR-PRF-025、BR-PRF-026、BR-PRF-027、BR-PRF-028、BR-PRF-030、BR-PRF-031、BR-PRF-032。上述引用只定位既有规则，不重定义或改变其语义。

## 业务规则（UC-APP-039 权威正文）

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-047 -->
### BR-PRF-047：当前管理员私有资料读取

仅已验证 USER 且 authId 等于当前 Application.adminId 可读取；资格或其他权限不替代所有权，不存在与不可见使用统一 NotFound。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-048 -->
### BR-PRF-048：全部修订状态与保留生命周期可见

当前/最后管理员可读取 DRAFT、SUBMITTED、APPROVED、REJECTED 及暂停、归档、CLOSING/CLOSED 下的保留资料；读取不恢复写入、owner 或在线资格。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-049 -->
### BR-PRF-049：当前修订与历史审核投影分离

列表/详情显示当前 ProfileRevision 内容和一致的 Profile 指针；最新 Review 与分页历史来自对应审核事实，不能用当前内容替换 snapshot 或用历史页最后一项冒充 latestReview。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-050 -->
### BR-PRF-050：签名且绑定管理权的资料分页

修订降序 keyset、审核历史升序 keyset。token 绑定 caller/Application/ownershipRevision/kind/filter/父修订/排序位置；篡改、跨上下文或管理权变化使 token 失效，合法长 authId 必须可分页。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-051 -->
### BR-PRF-051：一致读取与管理权边界

每页/详情在单个 majority snapshot 构造，批量读取本页来源，转让和各资料写命令并发时不返回撕裂结果；后续写命令仍独立复核所有前置条件。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-052 -->
### BR-PRF-052：必要资料关系损坏失败关闭

当次必要 Application/Profile/Revision/Review 或 lookahead 的结构、引用、唯一性、指针和既有审核不变量损坏，使整次查询 INTERNAL；不能跳过、降级或返回部分结果。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-053 -->
### BR-PRF-053：拒绝修订原文读取与独立重建

REJECTED 继续保持终态及保存的原文，不以当前内容规则拒绝合法历史，不规范化或替换原文；新建 DRAFT 仍走 UC013，不提供恢复、复制或新关联。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-054 -->
### BR-PRF-054：管理员查询最小披露

只返回正文、创建者/必要时间、指针及可公开给管理员的审核摘要/理由；不返回 updatedBy、submittedBy、Reviewer 身份、snapshot 正文、内部审核或当前 policy 数据。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-055 -->
### BR-PRF-055：只读与私有缓存边界

查询不写状态、fence、审计、已读或投影，不调用 Auth/Scope/DNS/外部资产；所有响应 private, no-store，日志与指标遵循 ADR-007。

<!-- 权威位置: use-cases/UC-APP-039-query-owned-application-profile-revisions.md#br-prf-056 -->
### BR-PRF-056：完整有界响应与不跳项续页

每协议编码响应最多 2 MiB，成功字段完整、历史可遍历；预算提前结束时仅推进到实际返回位置，单个必要项过大明确 RESOURCE_EXHAUSTED，不裁剪、漏项或制造空页循环。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-013`

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003 -->
### BR-PRF-003：displayName

- 是面向普通用户的公开显示名称，不承担路由、唯一键或授权职责。
- 输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–80 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 不要求全局唯一，也不要求在同一管理员或 Application 范围内唯一。
- Application.name 不作为 displayName 的默认值；调用者必须明确提供。

公开展示时仍必须按普通文本转义。displayName 不是 HTML、Markdown 或富文本。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004 -->
### BR-PRF-004：description

- description 是可空的公开应用简介；没有简介时保存 `null`，不保存空字符串。
- 非空输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–1000 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 当前只保存纯文本，不解释 HTML、Markdown、链接或富文本语法。

公开展示时必须按普通文本转义。若未来需要多段或富文本简介，应通过新用例和明确的内容安全规则扩展，而不是放宽当前字段的隐式解释。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005 -->
### BR-PRF-005：完整资料快照与图标边界

- 一条 ApplicationProfileRevision 表示一版完整资料，而不是字段 patch。
- 本用例的完整快照由 displayName、description 和 icon 构成；缺失 displayName 不会回退到 Application.name。
- ProfileRevision 不复制 ApplicationVersion 的 versionLabel、launchUrl、RPC 声明、capabilities、scopes 或发布状态。
- icon 可为 `null`；非空值按 Unicode NFC 规范化，长度为 1–512 个 Unicode code point，首尾不允许 Unicode whitespace，不允许 `Cc/Cf/Cs/Zl/Zp`。
- icon 是不透明纯字符串；App Center 不解析 scheme、不验证资产存在性、不请求指向内容，也不把它宣称为受控或不可变资产。
- 未来把 icon 收紧为受控资产引用时，通过新用例、新字段语义和显式迁移完成，不在当前字符串上隐式增加强保证。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006 -->
### BR-PRF-006：初始生命周期与单一工作修订

- 新 ProfileRevision 的 reviewStatus 固定为 `DRAFT`；调用者不能指定其他状态。
- 每个 Application 同时最多存在一条 reviewStatus 为 DRAFT 或 SUBMITTED 的工作修订。
- DRAFT 不属于公开目录，不改变已发布资料，也不会让 Application 自动公开。
- DRAFT 迁移为 SUBMITTED 后继续占用该工作位；在 PENDING ProfileReview 得到 APPROVED 或 REJECTED 决定前，不创建下一份 DRAFT。
- APPROVED 或 REJECTED 决定产生后释放工作位；它们不阻止后续创建新 DRAFT。

<!-- 权威位置: use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-007 -->
### BR-PRF-007：原子创建与初始审计

当前管理员检查、DRAFT/SUBMITTED 工作修订唯一检查、sequence 分配、ProfileRevision 插入、Application 计数器增加和 `ApplicationProfile.workingProfileRevisionId` 设置必须处于同一事务或等价原子边界。

管理员转让与创建并发时，旧管理员不能在转让完成后插入草稿。两个并发创建请求最多一个成功；失败请求不消耗 sequence。

创建时：

```text
revision = 1
createdBy = updatedBy = authenticated authId
createdAt = updatedAt = Clock.Now() in UTC
```

这些字段不能由请求正文覆盖。

### 来自 `UC-APP-014`

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-008 -->
### BR-PRF-008：仅草稿可编辑

只有 reviewStatus 为 `DRAFT` 的 ApplicationProfileRevision 可以被本用例更新。

`SUBMITTED/APPROVED/REJECTED` 等非 DRAFT 状态不能绕过各自生命周期用例直接修改。REJECTED 是终态；继续编辑旧内容时，由网页端预填后调用 UC-APP-013 创建新修订，服务端不提供恢复命令。

### 来自 `UC-APP-015`

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-018 -->
### BR-PRF-018：不可变审核快照

ApplicationProfileReview.snapshot 复制提交时已经规范化的完整资料：

```text
ApplicationProfileReviewSnapshot {
  displayName
  description
  icon
}
```

snapshot、sourceRevision、submittedBy 和 submittedAt 创建后不可修改。后续 Reviewer 读取 snapshot，不使用可能已经存在的其他草稿或当前公开资料拼装审核输入。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-019 -->
### BR-PRF-019：审核 attempt 身份

- profileReviewId 是系统生成的全局唯一 UUIDv7。
- attempt 在单个 profileRevisionId 内从 1 开始严格递增。
- `(profileRevisionId, attempt)` 唯一。
- `(profileRevisionId, sourceRevision)` 唯一，防止同一 ProfileRevision 状态被重复提交。
- 同一 ProfileRevision 同时最多有一个 PENDING Review。

一个 ProfileRevision 不从 REJECTED 恢复。网页端可以预填其内容并通过 UC-APP-013 创建拥有新身份的新修订；新修订的 attempt 从 1 开始，不覆盖旧 Review。

<!-- 权威位置: use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-020 -->
### BR-PRF-020：ProfileRevision 状态与审计

提交只执行以下生命周期变化：

```text
ApplicationProfileRevision: DRAFT -> SUBMITTED
revision: expectedRevision -> expectedRevision + 1
updatedBy: submittedBy
updatedAt: submittedAt
```

profileRevisionId、applicationId、sequence、createdBy、createdAt、displayName、description 和 icon 保持不变。ApplicationProfileReview.sourceRevision 保存迁移前的 expectedRevision。

### 来自 `UC-APP-016`

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-025 -->
### BR-PRF-025：Review、Revision 与 snapshot 一致性

作出决定前必须满足：

- Review、ProfileRevision 与 Application 属于同一路径；
- ProfileRevision 当前 displayName/description/icon 等于 Review.snapshot；
- `ProfileRevision.revision = Review.sourceRevision + 1`；
- Review 是该 ProfileRevision 当前 PENDING attempt。

发现内容漂移、悬空引用或 revision 关系异常时中止并告警，不自动修复。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-026 -->
### BR-PRF-026：状态同步

合法决定迁移只有：

```text
ApplicationProfileReview: PENDING -> APPROVED
ApplicationProfileRevision: SUBMITTED -> APPROVED

ApplicationProfileReview: PENDING -> REJECTED
ApplicationProfileRevision: SUBMITTED -> REJECTED
```

Review 与 ProfileRevision 的结果必须相同。决定不修改 snapshot、sourceRevision、submittedBy 或 submittedAt。
无论批准还是拒绝，决定同时清空指向目标修订的 `ApplicationProfile.workingProfileRevisionId`，释放下一份 DRAFT 的工作位。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-027 -->
### BR-PRF-027：决定理由

- REJECT 必须提供 reason；APPROVE 可以省略。
- 非空 reason 为 1–2000 个 Unicode code point。
- 首尾不允许 Unicode whitespace，不允许 Unicode `Cc` 控制字符，也不接受纯 whitespace。
- reason 是纯文本，不解释 HTML 或 Markdown。

校验后原样保存。Reviewer 不应在 reason 中写入敏感学生资料或无需向开发者公开的安全细节。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028 -->
### BR-PRF-028：版本化资料审核策略

Reviewer 提交自己实际阅读的 expectedPolicyVersion。App Center 拥有不可变、可按版本读取的 ProfileReviewPolicy：

```text
ProfileReviewPolicy {
  version
  requiredChecks
  status: ACTIVE | RETIRED
}
```

APPROVE 时 confirmedCheckIds 使用集合语义，并完整覆盖策略对 snapshot 要求的检查；REJECT 时 confirmedCheckIds 为空。历史 policy 保留用于解释既有 decision，RETIRED policy 不用于新决定。

首版策略由 App Center migration 写入：version=`app-profile-review-v1`、status=`ACTIVE`，固定要求以下两项：

- `content-policy-reviewed`：Reviewer 已检查名称、描述符合内容规范。
- `icon-content-reviewed`：Reviewer 已检查图标内容合规；icon 为空时明确确认不适用，仍提交该检查项。

策略内容不可原地修改；变更检查项使用新 version，历史定义保留。同版本已有不同定义时 migration 失败，不覆盖。首版不提供策略管理或查询接口。confirmedCheckIds 不接受重复、未知或缺失项，持久化按 ID 排序；REJECT 必须为空。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030 -->
### BR-PRF-030：批准后自动公开

APPROVE 必须提供 Reviewer 作出决定时观察到的 `expectedCurrentPublishedProfileRevisionId`，其值是某个 ProfileRevision ID 或明确的 `NONE`。它必须与当前指针匹配，再与以下变化处于同一原子边界：

```text
ProfileRevision.reviewStatus = APPROVED
ApplicationProfile.currentPublishedProfileRevisionId = profileRevisionId
```

管理员不需要第二次 Publish 操作。指针前置值使两个针对不同 ProfileRevision 的并发批准不会静默相互覆盖；后一个 Reviewer 必须重新读取已改变的公开资料后再决定。旧的当前公开 Revision 保留 APPROVED 状态和审核历史，但首版不提供重新选择它或回滚资料的命令。

资料自动公开不创建 stable Version。没有兼容 stable 槽位时，Application 仍不进入普通用户候选目录。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031 -->
### BR-PRF-031：拒绝终止修订且不改变当前公开资料

REJECT 只把目标 Review/Revision 迁移为 REJECTED，并记录理由。`currentPublishedProfileRevisionId` 保持不变；没有既有公开资料时继续为空。

REJECTED 是该 ProfileRevision 的终态：服务端不提供 `REJECTED -> DRAFT`、复制或恢复命令，也不修改 ApplicationVersion 或发送通知。Review snapshot、decision、Revision 内容和审计事实保持不变。

重新编辑是网页端便利行为：网页端读取被拒绝资料并预填创建表单，然后调用 [UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md) 创建一份新 DRAFT。新草稿获得独立的 profileRevisionId、sequence 和创建审计；App Center 不记录它与被拒绝 Revision 的复制关系。

<!-- 权威位置: use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-032 -->
### BR-PRF-032：Revision、审计与原子决定

决定成功后 ProfileRevision.revision 增加 1，updatedBy 记录 Reviewer authId，updatedAt 等于 decidedAt。createdBy、createdAt、submittedBy 和 submittedAt 保持不变。

以下事实全部成功或全部失败：

- 可信 ReviewerIdentity 权限、利益冲突、Review/Revision 状态与 revision 的最终检查；
- policy 与 confirmedCheckIds 校验；
- decision 写入和 Review 状态迁移；
- ProfileRevision 状态、revision 与更新审计变化；
- ApplicationProfile.workingProfileRevisionId 的匹配检查与清空；
- APPROVE 时当前公开资料指针前置值检查与替换。

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

- `UC-APP-013`（use-cases/UC-APP-013-create-application-profile-revision.md）：目标与范围、业务边界、输入与身份、网页端重新编辑被拒绝资料、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、尚未决定但不阻塞文档、后续用例、迁移说明、变更记录、实现依赖与交付边界
- `UC-APP-014`（use-cases/UC-APP-014-update-draft-application-profile-revision.md）：目标与范围、可编辑与不可编辑字段、输入与身份、主流程、异常流程、最小领域行为、用例端口、数据模型变化、API 草图、测试与验收、后续用例、迁移说明、变更记录、实现依赖与交付边界
- `UC-APP-015`（use-cases/UC-APP-015-submit-application-profile-revision-review.md）：目标与边界、参与者与输入、成功结果、主流程、失败结果、领域模型影响、验收场景、后续方向、实现依赖与交付边界、API 实现契约
- `UC-APP-016`（use-cases/UC-APP-016-decide-application-profile-revision-review.md）：目标与边界、参与者与输入、成功结果、主流程、失败结果、领域模型影响、验收场景、后续方向、实现依赖与交付边界、API 实现契约
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、Claims、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-039-query-owned-application-profile-revisions.md` | 228 | `114ea58a96cd` |
| `use-cases/UC-APP-013-create-application-profile-revision.md` | 404 | `42ec2452522f` |
| `use-cases/UC-APP-014-update-draft-application-profile-revision.md` | 336 | `fde28528679f` |
| `use-cases/UC-APP-015-submit-application-profile-revision-review.md` | 254 | `726a36ab708e` |
| `use-cases/UC-APP-016-decide-application-profile-revision-review.md` | 312 | `32bcd54ca110` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
