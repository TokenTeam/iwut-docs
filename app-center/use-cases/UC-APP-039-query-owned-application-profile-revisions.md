# UC-APP-039：查询我的 ApplicationProfileRevision 列表与详情

状态：`ACCEPTED`

## 设计结论

1. 当前管理员可读取全部资料修订，包括暂停、归档、CLOSING/CLOSED Application 的保留历史；不要求当前 Developer 资格仍为 APPROVED。
2. 详情返回修订完整当前内容和可分页遍历的审核历史；REJECTED 内容按保存的原文返回，不恢复原修订。
3. 保留 createdBy 与必要时间；不披露 updatedBy、submittedBy、Reviewer 身份、confirmed checks、内部策略内容或不可变审核 snapshot 正文。
4. 查询采用同一 majority snapshot、绑定当前管理权的签名游标与 2 MiB 编码响应预算；超大单项明确报错，不截断正文或跳过记录。

管理员语义已接受并同步到 [Profile 管理查询契约](../query-contracts/profile-management.md)。Reviewer 部分继续由 [UC-APP-031](UC-APP-031-query-application-profile-reviews.md) 管理。

## 目标与范围

本用例为 Developer Console 交付两个私有读取能力：

- `ListApplicationProfileRevisions`：列出一个 Application 的资料修订，可按一个 reviewStatus 过滤。
- `GetApplicationProfileRevision`：读取一个资料修订的完整当前内容、当前工作/公开指针和审核历史的一页。

它补齐 UC-APP-029 的资料管理摘要之外的历史查询，也提供 UC-APP-014/015 写命令前读取当前 revision、以及 UC-APP-013 新建草稿前读取被拒绝内容的正式来源。命令仍在执行时重新校验身份、状态、revision 和指针；读取结果不替代写入授权。

不增加创建、提交、决定、恢复、复制、删除、资料回滚或放弃草稿命令，不提供 Reviewer 队列、平台跨 Application 查询、用户公开目录、Tester 管理、通知或受控 icon 资产。查询不调用 Auth、Scope Catalog、DNS 或 icon URL。

## 参与者与授权

调用者为已验证的可信 USER，authId 必须等于 snapshot 中 Application 当前保存的 adminId。Developer 资格、Reviewer 权限、Tester、SYSTEM 或平台运维权限均不替代当前管理关系。

Application 不存在、调用者不是当前管理员、目标修订不存在或不属于路径 Application，统一返回 `ApplicationProfileManagementNotFound`。非管理员不能通过此查询判断其他 Application 的资料是否存在。

ACTIVE/AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED、CLOSING/CLOSED 的保留记录均可由其保存的当前/最后管理员读取。CLOSED 读取不恢复 owner 义务、配额、在线资格或写权限。

## 查询输入与 API 草图

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

## 列表投影

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

## 详情与审核历史

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

## 一致性、游标与响应预算

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

## 隐私与错误

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

## 业务规则

<a id="br-prf-047"></a>
### BR-PRF-047：当前管理员私有资料读取

仅已验证 USER 且 authId 等于当前 Application.adminId 可读取；资格或其他权限不替代所有权，不存在与不可见使用统一 NotFound。

<a id="br-prf-048"></a>
### BR-PRF-048：全部修订状态与保留生命周期可见

当前/最后管理员可读取 DRAFT、SUBMITTED、APPROVED、REJECTED 及暂停、归档、CLOSING/CLOSED 下的保留资料；读取不恢复写入、owner 或在线资格。

<a id="br-prf-049"></a>
### BR-PRF-049：当前修订与历史审核投影分离

列表/详情显示当前 ProfileRevision 内容和一致的 Profile 指针；最新 Review 与分页历史来自对应审核事实，不能用当前内容替换 snapshot 或用历史页最后一项冒充 latestReview。

<a id="br-prf-050"></a>
### BR-PRF-050：签名且绑定管理权的资料分页

修订降序 keyset、审核历史升序 keyset。token 绑定 caller/Application/ownershipRevision/kind/filter/父修订/排序位置；篡改、跨上下文或管理权变化使 token 失效，合法长 authId 必须可分页。

<a id="br-prf-051"></a>
### BR-PRF-051：一致读取与管理权边界

每页/详情在单个 majority snapshot 构造，批量读取本页来源，转让和各资料写命令并发时不返回撕裂结果；后续写命令仍独立复核所有前置条件。

<a id="br-prf-052"></a>
### BR-PRF-052：必要资料关系损坏失败关闭

当次必要 Application/Profile/Revision/Review 或 lookahead 的结构、引用、唯一性、指针和既有审核不变量损坏，使整次查询 INTERNAL；不能跳过、降级或返回部分结果。

<a id="br-prf-053"></a>
### BR-PRF-053：拒绝修订原文读取与独立重建

REJECTED 继续保持终态及保存的原文，不以当前内容规则拒绝合法历史，不规范化或替换原文；新建 DRAFT 仍走 UC013，不提供恢复、复制或新关联。

<a id="br-prf-054"></a>
### BR-PRF-054：管理员查询最小披露

只返回正文、创建者/必要时间、指针及可公开给管理员的审核摘要/理由；不返回 updatedBy、submittedBy、Reviewer 身份、snapshot 正文、内部审核或当前 policy 数据。

<a id="br-prf-055"></a>
### BR-PRF-055：只读与私有缓存边界

查询不写状态、fence、审计、已读或投影，不调用 Auth/Scope/DNS/外部资产；所有响应 private, no-store，日志与指标遵循 ADR-007。

<a id="br-prf-056"></a>
### BR-PRF-056：完整有界响应与不跳项续页

每协议编码响应最多 2 MiB，成功字段完整、历史可遍历；预算提前结束时仅推进到实际返回位置，单个必要项过大明确 RESOURCE_EXHAUSTED，不裁剪、漏项或制造空页循环。

## 验收矩阵与交付边界

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

## 既有规则依赖

资料字段与审计复用 UC013 的 BR-PRF-003、BR-PRF-004、BR-PRF-005、BR-PRF-006、BR-PRF-007、BR-PRF-008；提交的不可变快照、attempt 和状态复用 UC015 的 BR-PRF-018、BR-PRF-019、BR-PRF-020；审核关系、状态同步、理由、历史策略和终态原文复用 UC016 的 BR-PRF-025、BR-PRF-026、BR-PRF-027、BR-PRF-028、BR-PRF-030、BR-PRF-031、BR-PRF-032。上述引用只定位既有规则，不重定义或改变其语义。
