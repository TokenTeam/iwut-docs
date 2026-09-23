<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-007 --spec tools/brief-specs/UC-APP-007.json -->
# Brief — UC-APP-007：将已批准应用版本放入测试发布槽位

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-007` 将已批准应用版本放入测试发布槽位 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PUB-001`–`BR-PUB-010`（10 条） |
| 外部引用 BR | `BR-REV-004`、`BR-REV-007`、`BR-REV-013`、`BR-REV-014`（来自 `UC-APP-004`、`UC-APP-005`） |
| ADR | `ADR-001`、`ADR-002`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/auth-scope-catalog-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

> developerStatus 为 `APPROVED` 的当前应用管理员，为一个明确的 rpcApiMajor 选择同一 Application 下、与该 major 兼容的 APPROVED ApplicationVersion，作为 test 发布槽位当前指向的版本。

本用例负责：

- 首次创建 `(applicationId, rpcApiMajor)` 对应的 ApplicationPublication，或更新其 testVersionId。
- 使用 Publication revision 防止并发槽位修改互相覆盖。
- 在实际改变槽位前重新验证批准状态、scopes 和公网 HTTPS URL。
- 为每次实际变化追加不可变 ApplicationPublicationHistory。

本用例不负责：

- 创建 Tester Membership、生成 Tester 加入链接或判断某个用户是否有测试资格。
- 向普通用户目录暴露 test Version。
- 清空 test 槽位。
- 设置 grey/stable 槽位、灰度比例或 rollout seed。
- 一次修改 Version range 中的多个 rpcApiMajor。
- 修改 ApplicationVersion 的内容、审核状态或 revision。
- 自动发布刚审核通过的 Version。

test 槽位可以在 tester 数量为 0 时存在；此时它只是管理员准备好的发布指针，不会因此对任何普通用户可见。

### 发布边界

ApplicationPublication 按 `(applicationId, rpcApiMajor)` 唯一，而不是按 platform/target 或客户端 build version 分区。详细理由见 [ADR-002](../adr/ADR-002-partition-publication-by-rpc-api-major.md)。

```text
Application A / RPC major 3
  testVersionId -> Version X

Application A / RPC major 4
  testVersionId -> Version X or Version Y
```

Version X 即使声明兼容 `[3, 5)`，也必须通过两个独立命令分别设置 major 3 和 major 4；不存在隐式批量发布。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
rpcApiMajor: int32
```

Command：

```text
PlaceApprovedVersionInTestSlotCommand {
  versionId: ApplicationVersionId
  expectedPublicationRevision: optional int64
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

expectedPublicationRevision 的语义：

- null：调用者预期 Publication 尚不存在，本次只允许创建。
- `>= 1`：调用者预期 Publication 已存在且 revision 与该值相同，本次只允许更新或 no-op。

publicationId、historyId、revision、审核引用、验证版本和审计字段都不能由请求正文指定。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，rpcApiMajor `>= 1`，versionId 为 UUIDv7，expectedPublicationRevision 为空或 `>= 1`。
3. Repository 加载放置候选并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - Version 属于该 Application，reviewStatus=`APPROVED`。
   - 最新 ApplicationReview 属于该 Version，status 和 decision.outcome 都为 `APPROVED`。
   - Version 的受审核内容等于 Review.snapshot。
   - Version.revision 等于 `Review.sourceVersionRevision + 2`。
   - Version 的 RPC range 覆盖 rpcApiMajor。
   - Publication 的存在性和 revision 符合 expectedPublicationRevision。
4. 若已存在 Publication、revision 匹配且 testVersionId 已等于 versionId，返回当前 Publication，changed=false，不执行外部检查、不增加 revision、不写 History。
5. 针对 approved Review.snapshot：
   - 通过 ScopeCatalog 确认 scopes 当前仍允许新版本使用，并取得 scopeCatalogRevision。
   - 通过 LaunchURLSubmissionPolicy 重新检查公网 HTTPS URL，并取得 preflightPolicyVersion。
6. 为新 Publication（若需要）和本次 History 分别生成 UUIDv7，并从 Clock 取得 changedAt。
7. Repository 在同一事务或等价原子边界中重新确认步骤 3 的全部条件，然后：
   - Publication 不存在时创建 revision=1、testVersionId=versionId 的记录。
   - Publication 已存在时把 testVersionId 替换为 versionId，并将 revision 增加 1。
   - 设置 createdBy/createdAt 或 updatedBy/updatedAt。
   - 插入一条与结果 publicationRevision 对应的 SET_TEST_VERSION History。
8. 返回 Publication、History 和 changed=true。

外部检查与最终写入之间可能发生审核撤销、管理员转让或其他槽位修改，因此最终事务必须重新检查 Version/Review 资格、当前 admin 和 Publication revision。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- rpcApiMajor `< 1`：`InvalidRpcApiMajor`。
- versionId 格式非法：`InvalidApplicationVersionId`。
- Application 或 Version 不存在，或 Version 不属于 Application：`ApplicationVersionNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 或最新 Review 不是 APPROVED：`ApplicationVersionNotApproved`。
- Review/Version 的内容、状态或 revision 关系不一致：`ApplicationReviewStateInconsistent`。
- Version RPC range 不覆盖 rpcApiMajor：`ApplicationVersionRpcApiIncompatible`。
- 预期不存在但 Publication 已存在：`ApplicationPublicationAlreadyExists`。
- 预期存在但 Publication 不存在：`ApplicationPublicationNotFound`。
- Publication revision 不匹配：`ApplicationPublicationRevisionConflict`。
- scope 不再允许新版本使用：`InvalidApplicationScope`。
- Scope Catalog 不可用：`ScopeCatalogUnavailable`。
- URL 不再满足公网 HTTPS 策略：`ApplicationLaunchUrlNotReviewable`。
- URL 检查依赖不可用：`LaunchUrlInspectionUnavailable`。
- ID 生成或持久化失败：内部失败，不产生部分 Publication 或 History。

路径关系不匹配统一按 NotFound 处理，不泄露其他应用的 Version。所有失败都不能改变当前槽位。

### 最小领域模型

```text
ApplicationPublication {
  publicationId: ApplicationPublicationId
  applicationId: ApplicationId
  rpcApiMajor: int32
  testVersionId: ApplicationVersionId
  revision: int64
  createdBy: AuthId
  createdAt: Instant
  updatedBy: AuthId
  updatedAt: Instant
}

ApplicationPublicationHistory {
  historyId: ApplicationPublicationHistoryId
  publicationId: ApplicationPublicationId
  applicationId: ApplicationId
  rpcApiMajor: int32
  publicationRevision: int64
  action: SET_TEST_VERSION
  previousVersionId: optional ApplicationVersionId
  newVersionId: ApplicationVersionId
  approvedReviewId: ApplicationReviewId
  scopeCatalogRevision: int64
  preflightPolicyVersion: string
  changedBy: AuthId
  changedAt: Instant
}
```

ApplicationPublication 是一个 RPC major 的当前发布状态；History 是追加式审计记录。ApplicationVersion 和 ApplicationReview 只作为发布资格来源，不归入 Publication 聚合。

### 用例端口

```go
type UUIDv7Generator interface {
    NewUUIDv7() (string, error)
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

type ApplicationPublicationRepository interface {
    LoadTestPlacementCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        rpcAPIMajor int32,
        versionID ApplicationVersionID,
        expectedAdminID AuthID,
        expectedPublicationRevision *int64,
    ) (*TestPlacementCandidate, error)

    PlaceInTest(
        ctx context.Context,
        candidate TestPlacementCandidate,
        publicationID *ApplicationPublicationID,
        historyID ApplicationPublicationHistoryID,
        expectedAdminID AuthID,
        validation PublicationValidation,
        changedAt time.Time,
    ) (*PlaceInTestResult, error)
}
```

`PlaceInTest` 必须重新比较 Application.adminId、Version/Review 资格、Publication 存在性/revision 和当前 testVersionId。publicationID 只在创建候选时提供，更新时必须为空。

### 数据模型

#### application_publications

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `publicationId` | Publication 稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | `(applicationId, rpcApiMajor)` | no |
| `rpcApiMajor` | 宿主 RPC 合约 major | int32 | `>= 1` | `(applicationId, rpcApiMajor)` | no |
| `testVersionId` | 当前 test 槽位 | string | 同一 Application 的 APPROVED Version UUIDv7 | no | no |
| `revision` | Publication 并发版本 | int64 | `>= 1`；创建为 1，真实变化递增 | no | no |
| `createdBy` | 首次创建者 | string | opaque authId | no | no |
| `createdAt` | 首次创建时间 | datetime | UTC / RFC 3339 | no | no |
| `updatedBy` | 最近槽位修改者 | string | opaque authId；创建时等于 createdBy | no | no |
| `updatedAt` | 最近槽位修改时间 | datetime | UTC / RFC 3339；创建时等于 createdAt | no | no |

索引与 validator：

- publicationId 唯一索引。
- `(applicationId, rpcApiMajor)` 复合唯一索引。
- testVersionId 必须存在且不能使用空字符串或 `-1` 哨兵。
- revision 和全部审计字段必须存在。

#### application_publication_history

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `historyId` | History 稳定 ID | string | UUIDv7 | yes | no |
| `publicationId` | 对应 Publication | string | UUIDv7 | `(publicationId, publicationRevision)` | no |
| `applicationId` | 冗余所属 Application，支持审计查询 | string | UUIDv7 | no | no |
| `rpcApiMajor` | 变更的 RPC major | int32 | `>= 1` | no | no |
| `publicationRevision` | 变更后的 Publication revision | int64 | `>= 1` | `(publicationId, publicationRevision)` | no |
| `action` | 槽位行为 | string enum | `SET_TEST_VERSION` | no | no |
| `previousVersionId` | 变更前 test Version | string | UUIDv7；首次设置为空 | no | yes |
| `newVersionId` | 变更后 test Version | string | UUIDv7 | no | no |
| `approvedReviewId` | 证明发布资格的 Review | string | UUIDv7；status=APPROVED | no | no |
| `scopeCatalogRevision` | 发布复检使用的 Auth catalog revision | int64 | Auth 单调递增版本 | no | no |
| `preflightPolicyVersion` | 发布复检使用的 URL 策略 | string | 1–50 ASCII `[A-Za-z0-9._-]` | no | no |
| `changedBy` | 执行设置的当前 admin | string | opaque authId | no | no |
| `changedAt` | 槽位变化时间 | datetime | UTC / RFC 3339 | no | no |

索引与 validator：

- historyId 唯一索引。
- `(publicationId, publicationRevision)` 复合唯一索引。
- `(applicationId, changedAt, historyId)` 索引支持稳定审计分页。
- action 在本用例只能是 `SET_TEST_VERSION`。
- History 插入后不可修改或删除。

### API 草图

```text
PUT /applications/{applicationId}/publications/{rpcApiMajor}/test-slot
Authorization: <authenticated developer identity>
```

首次创建请求：

```json
{
  "versionId": "version-uuid",
  "expectedPublicationRevision": null
}
```

替换请求：

```json
{
  "versionId": "new-version-uuid",
  "expectedPublicationRevision": 3
}
```

首次创建成功：`201 Created`；替换或 no-op 成功：`200 OK`。

```json
{
  "changed": true,
  "publication": {
    "publicationId": "publication-uuid",
    "applicationId": "application-uuid",
    "rpcApiMajor": 3,
    "testVersionId": "version-uuid",
    "revision": 1,
    "createdBy": "admin-auth-id",
    "createdAt": "2026-09-15T18:00:00Z",
    "updatedBy": "admin-auth-id",
    "updatedAt": "2026-09-15T18:00:00Z"
  },
  "history": {
    "historyId": "history-uuid",
    "publicationRevision": 1,
    "action": "SET_TEST_VERSION",
    "previousVersionId": null,
    "newVersionId": "version-uuid",
    "approvedReviewId": "review-uuid",
    "scopeCatalogRevision": 19,
    "preflightPolicyVersion": "submit-v1",
    "changedBy": "admin-auth-id",
    "changedAt": "2026-09-15T18:00:00Z"
  }
}
```

no-op 响应中 changed=false、history=null，并返回未改变的 Publication。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application、Version 或预期存在的 Publication 不存在：`404 Not Found`。
- Publication 已存在但调用者预期不存在，或 revision 冲突：`409 Conflict`。
- major、versionId 或 expected revision 格式非法：`400 Bad Request`。
- Version 未批准、RPC major 不兼容或 scope/URL 不满足条件：`422 Unprocessable Content`。
- Scope Catalog 或 URL 检查依赖不可用：`503 Service Unavailable`。

### 测试与验收

领域测试：

- Publication 以 `(applicationId, rpcApiMajor)` 唯一。
- 只有 range 覆盖指定 major 的 APPROVED Version 可以进入 test。
- 首次创建 revision=1，替换真实变化时递增。
- 相同 versionId 是 no-op，不产生 History。
- 设置槽位不改变新旧 ApplicationVersion。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以设置。
- null expected revision 只创建，数值 expected revision 只更新或 no-op。
- 实际变化时针对 approved snapshot 复检 scope 和 URL。
- no-op 不调用外部复检、IDGenerator 或 Clock。
- 一次命令不会修改其他 rpcApiMajor。
- 外部检查失败时不调用最终 PlaceInTest。

Repository 集成测试：

- Publication 和 History 全部提交或全部回滚。
- 同一 major 的两个并发创建只有一个成功。
- 两个相同 expected revision 的并发替换最多一个成功。
- 管理员转让、Version revoke 与设置并发时旧条件不能成功。
- approved Review、snapshot、Version status/revision 的一致性检查生效。
- `(applicationId, rpcApiMajor)` 和 `(publicationId, publicationRevision)` 唯一约束生效。
- 替换后旧 Version 保持 APPROVED，历史指针仍可审计。

API 测试：

- 创建、替换和 no-op 返回正确状态码与 changed/history 组合。
- 请求不能指定 publicationId、historyId、审计、验证版本或结果 revision。
- 身份、路径、发布资格、RPC 兼容和并发错误映射正确。

### 实现依赖与交付边界

- Application、ApplicationVersion 与 ApplicationReview 的前置行为已由 UC-APP-001 至 UC-APP-006 实现；发布从完整 APPROVED decision 和 snapshot 读取资格，不依赖 Tester、公开资料或后续发布能力。
- 复用现有可信 DeveloperIdentity、Auth Scope Catalog gRPC consumer/有界缓存、DNS-only URL 预检、UUIDv7/Clock 与 Wire；新能力通过自己的 ports 适配，遵守 ADR-003 的能力边界。
- MongoDB 使用 ADR-004 要求的事务拓扑；现有隔离 replica-set 测试脚本可验证跨 Application、Version、Review、Publication、History 的事务、回滚和并发。最终事务必须以真实写入栅栏或等价机制防止读快照下的管理员转让/审核撤销竞争；不得改变 Application/Version 的业务字段或业务 revision。
- Auth 的 MongoDB 权威 Scope Catalog 尚未交付，不阻止 App Center consumer 实现及隔离 E2E，但在权威目录和完整双服务验证闭合前，不将本 UC 标为生产依赖全部闭合的 COMPLETE。
- 新增 Publication/History schema、API 和 consumer adapters 属于本工作包交付内容，不是要求预先实现的依赖。

### 迁移说明

服务从未上线，不迁移 Application.betaVersion、Version.status=TEST 或内嵌 tester 数组。新模型直接创建按 rpcApiMajor 分区的 Publication 和追加式 History。

## 业务规则（UC-APP-007 权威正文）

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-001 -->
### BR-PUB-001：设置权限

设置者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

reviewer 批准 Version 不会替开发者作出发布选择。管理员转让后，新的当前 admin 可以修改已有 Publication。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-002 -->
### BR-PUB-002：按 RPC major 分区

- `(applicationId, rpcApiMajor)` 唯一。
- rpcApiMajor 是 `>= 1` 的整数。
- 一次命令只操作一个分区。
- Version 必须满足 `min <= rpcApiMajor < maxExclusive`。
- requiredCapabilities 不成为分区键；客户端解析时仍需逐项匹配。

不使用 platform/target，也不把 clientBuildVersion 或 versionLabel 当作发布维度。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003 -->
### BR-PUB-003：Version 发布资格

testVersionId 只能引用同一 Application 的 APPROVED Version。其最新 Review 必须是完整 APPROVED decision，Version 内容必须仍等于 snapshot，且 revision 关系必须一致。

审核状态一致性和 revision 的既有约束分别见 [BR-REV-013](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) 与 [BR-REV-014](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014)；受审核快照字段见 [BR-REV-004](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004)。

`DRAFT/SUBMITTED/REJECTED/REVOKED` 都不能进入 test 槽位。历史上曾经 APPROVED 但当前已失去资格的 Version 也不能重新设置。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-004 -->
### BR-PUB-004：测试槽位不是审核状态

设置 testVersionId 不改变 ApplicationVersion.reviewStatus 或 revision。替换槽位时，旧 Version 仍保持原审核状态，也不会被删除或停用。

同一个 APPROVED Version 可以同时被不同 rpcApiMajor 的 test 槽位引用，也可以在后续规则允许时同时被 test/grey/stable 引用。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-005 -->
### BR-PUB-005：测试可见性

test 槽位永远不因存在而向普通用户公开。未来解析用例至少需要同时满足：

- 请求宿主的 rpcApiMajor 与 Publication 相同。
- 宿主 capabilities 覆盖 Version.requiredCapabilities。
- 当前用户具有整个 Application 下的有效 Tester Membership。

本用例允许没有 Tester 的 test 槽位。当前 admin 不隐式拥有测试资格，必须和其他用户一样通过有效加入链接取得 Membership。本用例不返回可直接绕过资格检查的公开入口。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-006 -->
### BR-PUB-006：Publication 乐观并发

- 首次创建时 expectedPublicationRevision 必须为 null，结果 revision 为 1。
- 已存在时 expectedPublicationRevision 必须与当前 revision 相同。
- 每次真实槽位变化 revision 增加 1。
- revision 不匹配时不自动重试或覆盖。
- 若 expected revision 匹配且目标 versionId 已在 test 槽位，返回 no-op，不改变 revision 或审计。

Publication revision 对该 `(applicationId, rpcApiMajor)` 下未来所有槽位共享。test、grey、stable 的并发修改因此会相互检测，而不是分别静默覆盖。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007 -->
### BR-PUB-007：PublicationHistory

每次真实变化必须追加一条不可修改的 History：

```text
SET_TEST_VERSION {
  previousVersionId
  newVersionId
  approvedReviewId
  scopeCatalogRevision
  preflightPolicyVersion
  changedBy
  changedAt
  publicationRevision
}
```

首次设置 previousVersionId 为 null。替换时保留旧指针，不修改过去记录。no-op 不写 History。

History 是操作审计，不是 event sourcing 的权威状态；当前 Publication 才是槽位读取来源。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-008 -->
### BR-PUB-008：发布前复检

真实改变 test 槽位前，必须针对 approved Review.snapshot 重新执行 ScopeCatalog 和 LaunchURLSubmissionPolicy 检查，并把所用版本写入 History。

ScopeCatalog 使用 [ADR-001](../adr/ADR-001-scope-catalog-cache.md) 的有界缓存和失败关闭语义；LaunchURLSubmissionPolicy 复用 [BR-REV-007](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-007) 的公网 HTTPS/DNS 预检，不新增内容抓取。

这仍然不能冻结自托管网页内容。重复设置同一 Version 的 no-op 不代表一次新的发布或复检；若需要主动重新验证已在槽位中的版本，应设计独立检查行为。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-009 -->
### BR-PUB-009：原子写入

以下操作必须全部成功或全部失败：

- 当前 admin 和 Version/Review 发布资格复查。
- Publication 存在性和 expected revision 检查。
- Publication 创建或 testVersionId/revision/审计更新。
- PublicationHistory 插入。

替换、管理员转让、审核撤销或其他槽位操作并发时，旧条件不能成功覆盖新状态。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-010 -->
### BR-PUB-010：不自动扩散

设置 test 槽位不得：

- 修改同一 Version range 内其他 rpcApiMajor 的 Publication。
- 创建 tester 资格。
- 修改 grey/stable 槽位。
- 修改 Application 或 ApplicationVersion。
- 触发自动逐步灰度或稳定发布。

未来批量操作必须由多个单分区命令组合，并明确部分失败与补偿语义。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-004`

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
```

snapshot 创建后不可修改。Application.name 和独立的 ApplicationProfileRevision 不进入本次版本审核快照；公开目录资料由其自身的 revision 审核流程负责。

审核记录的 status 和后续决策审计可以发生一次受控状态迁移，但这不允许改写 snapshot、sourceVersionRevision、submittedBy 或 submittedAt。

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

### 来自 `UC-APP-005`

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013 -->
### BR-REV-013：状态一致性

合法迁移只有：

```text
ApplicationReview: PENDING -> APPROVED
ApplicationVersion: SUBMITTED -> APPROVED

ApplicationReview: PENDING -> REJECTED
ApplicationVersion: SUBMITTED -> REJECTED
```

Review 和 Version 的结果必须相同。Version 内容必须等于 snapshot，且决定前 Version.revision 必须为 `sourceVersionRevision + 1`。不满足表示出现绕过用例的写入或数据损坏，应中止并告警，不能尝试自动修复。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014 -->
### BR-REV-014：Version revision 与审计

决定成功后 Version.revision 原子增加 1，updatedBy 记录 decision.decidedBy，updatedAt 等于 decision.decidedAt。人工决定的 decidedBy 是 reviewer authId；暂停触发的自动拒绝使用注入的 System Auth ID。

createdBy、createdAt、submittedBy 和 submittedAt 都不因审核决定改变。审核人和审核时间属于 ApplicationReview.decision。

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

### ADR-002：ApplicationPublication 按 RPC API major 分区（`PROPOSED`）

#### 决定

ApplicationPublication 从第一次出现时就按以下业务键唯一：

```text
(applicationId, rpcApiMajor)
```

每条 Publication 只管理一个 RPC major 下的发布槽位和 revision。UC-APP-007 首先引入 testVersionId；grey/stable 字段只在对应真实用例出现时增加。

被放入槽位的 ApplicationVersion 必须满足：

```text
rpcApiMinVersion <= rpcApiMajor < rpcApiMaxVersionExclusive
```

requiredCapabilities 仍在客户端解析或握手时逐项判断，不成为新的 Publication 分区维度。

一个 Version 若兼容多个 major，可以由管理员分别放入多条 Publication。一次命令只改变一个 rpcApiMajor，不根据 Version range 隐式批量修改。

#### 适用边界

本决定只覆盖 App Center 的版本发布选择。Auth token、Expo build 升级策略和网页自己的 versionLabel 不使用这个分区键。

若未来证明系统永远只支持一个 RPC major，可以保留相同模型而只存在一条 Publication；无需把分区重新折叠进 Application。

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
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 当前只消费精确值 `app.version.review`。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含 `app.version.review` 时按权限不足拒绝；Reviewer 不需要 `developer_status`。
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

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### Auth Center 固定授权映射

| gRPC 方法 | 必需 permission |
| --- | --- |
| `ScopeCatalog/GetScopeCatalogSnapshot` | `auth.scope-catalog.read` |
| `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | `auth.developer-status.read` |
| `SystemPrincipalDirectory/ResolveSystemPrincipal` | `auth.system-principal.resolve` |
| `UserIdentityService/IssueUserIdentityFromSession` | `auth.identity.issue` |

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-007`（use-cases/UC-APP-007-place-approved-version-in-test-slot.md）：旧实现观察、数据模型/application_publications、数据模型/application_publication_history、后续用例、变更记录
- `UC-APP-004`（use-cases/UC-APP-004-submit-application-version-review.md）：目标与范围、提交结果、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、后续用例、迁移说明、变更记录
- `UC-APP-005`（use-cases/UC-APP-005-decide-application-version-review.md）：目标与范围、参与者、决定结果、旧实现观察、输入、主流程、异常流程、最小领域行为、用例端口、数据模型变化、API 草图、测试与验收、已确认的实现边界、后续用例、迁移说明、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `ADR-002`（adr/ADR-002-partition-publication-by-rpc-api-major.md）：背景、为什么不使用 platform/target、考虑过的替代方案、结果、关联用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/auth-scope-catalog-v1.md`（docs 根级共享文档）：目的与所有权、兼容性、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：ENV 配置、契约测试要求

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-007-place-approved-version-in-test-slot.md` | 538 | `b3cad71e1237` |
| `use-cases/UC-APP-004-submit-application-version-review.md` | 498 | `5db0577b6aed` |
| `use-cases/UC-APP-005-decide-application-version-review.md` | 608 | `ff0f43b11bd2` |
| `adr/ADR-001-scope-catalog-cache.md` | 112 | `a5fe7365b96f` |
| `adr/ADR-002-partition-publication-by-rpc-api-major.md` | 84 | `0a1f73af1ac8` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `2595342af7cd` |
| `platform/contracts/auth-scope-catalog-v1.md` | 91 | `cab448326f29` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `4bb4d40a23c8` |
| `platform/contracts/trusted-service-identity-v1.md` | 88 | `3c091a708b32` |
