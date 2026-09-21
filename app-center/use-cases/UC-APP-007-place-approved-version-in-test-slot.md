# UC-APP-007：将已批准应用版本放入测试发布槽位

状态：`PROPOSED`

## 目标与范围

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

## 发布边界

ApplicationPublication 按 `(applicationId, rpcApiMajor)` 唯一，而不是按 platform/target 或客户端 build version 分区。详细理由见 [ADR-002](../adr/ADR-002-partition-publication-by-rpc-api-major.md)。

```text
Application A / RPC major 3
  testVersionId -> Version X

Application A / RPC major 4
  testVersionId -> Version X or Version Y
```

Version X 即使声明兼容 `[3, 5)`，也必须通过两个独立命令分别设置 major 3 和 major 4；不存在隐式批量发布。

## 旧实现观察

旧 Application 直接保存 `beta_version`，ApplicationVersion.status 同时使用 `TEST/GREY/STABLE/DEACTIVATE`，tester 数组又嵌入 Version。切换槽位时先更新 Version status、再更新 Application 指针、最后停用旧 Version，多步失败可能产生互相矛盾的状态。

### KEEP

- Application 需要一个当前测试版本指针。
- 开发者拥有主动选择测试版本的能力。
- 测试版本优先于普通 stable/grey 解析，但只能对有资格的 tester 生效；解析规则由后续用例完成。

### CHANGE

- `beta` 统一命名为 `test`。
- 槽位移入独立 ApplicationPublication，不再扩充 Application。
- Publication 按 rpcApiMajor 分区。
- Version 保持 `APPROVED`，不再用 Version.status=`TEST` 表示引用关系。
- 替换 test 指针不修改或停用旧 Version。
- 每次真实变化写入 PublicationHistory，并和当前指针原子提交。
- 使用 expectedPublicationRevision 拒绝静默覆盖。

### DROP

- Application.betaVersion 字段和 `-1` 空值哨兵。
- ApplicationVersion.status=`TEST`。
- 把 tester ID 数组嵌入 ApplicationVersion。
- 先改 Version、再改 Application、再停用旧 Version 的过程式多次写入。
- 根据 Version range 自动批量设置多个 major。

### UNKNOWN

- test 槽位的清空权限和审计语义。

## 输入与身份

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

## 主流程

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

## 异常流程

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

## 业务规则

<a id="br-pub-001"></a>
### BR-PUB-001：设置权限

设置者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

reviewer 批准 Version 不会替开发者作出发布选择。管理员转让后，新的当前 admin 可以修改已有 Publication。

<a id="br-pub-002"></a>
### BR-PUB-002：按 RPC major 分区

- `(applicationId, rpcApiMajor)` 唯一。
- rpcApiMajor 是 `>= 1` 的整数。
- 一次命令只操作一个分区。
- Version 必须满足 `min <= rpcApiMajor < maxExclusive`。
- requiredCapabilities 不成为分区键；客户端解析时仍需逐项匹配。

不使用 platform/target，也不把 clientBuildVersion 或 versionLabel 当作发布维度。

<a id="br-pub-003"></a>
### BR-PUB-003：Version 发布资格

testVersionId 只能引用同一 Application 的 APPROVED Version。其最新 Review 必须是完整 APPROVED decision，Version 内容必须仍等于 snapshot，且 revision 关系必须一致。

`DRAFT/SUBMITTED/REJECTED/REVOKED` 都不能进入 test 槽位。历史上曾经 APPROVED 但当前已失去资格的 Version 也不能重新设置。

<a id="br-pub-004"></a>
### BR-PUB-004：测试槽位不是审核状态

设置 testVersionId 不改变 ApplicationVersion.reviewStatus 或 revision。替换槽位时，旧 Version 仍保持原审核状态，也不会被删除或停用。

同一个 APPROVED Version 可以同时被不同 rpcApiMajor 的 test 槽位引用，也可以在后续规则允许时同时被 test/grey/stable 引用。

<a id="br-pub-005"></a>
### BR-PUB-005：测试可见性

test 槽位永远不因存在而向普通用户公开。未来解析用例至少需要同时满足：

- 请求宿主的 rpcApiMajor 与 Publication 相同。
- 宿主 capabilities 覆盖 Version.requiredCapabilities。
- 当前用户具有整个 Application 下的有效 Tester Membership。

本用例允许没有 Tester 的 test 槽位。当前 admin 不隐式拥有测试资格，必须和其他用户一样通过有效加入链接取得 Membership。本用例不返回可直接绕过资格检查的公开入口。

<a id="br-pub-006"></a>
### BR-PUB-006：Publication 乐观并发

- 首次创建时 expectedPublicationRevision 必须为 null，结果 revision 为 1。
- 已存在时 expectedPublicationRevision 必须与当前 revision 相同。
- 每次真实槽位变化 revision 增加 1。
- revision 不匹配时不自动重试或覆盖。
- 若 expected revision 匹配且目标 versionId 已在 test 槽位，返回 no-op，不改变 revision 或审计。

Publication revision 对该 `(applicationId, rpcApiMajor)` 下未来所有槽位共享。test、grey、stable 的并发修改因此会相互检测，而不是分别静默覆盖。

<a id="br-pub-007"></a>
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

<a id="br-pub-008"></a>
### BR-PUB-008：发布前复检

真实改变 test 槽位前，必须针对 approved Review.snapshot 重新执行 ScopeCatalog 和 LaunchURLSubmissionPolicy 检查，并把所用版本写入 History。

这仍然不能冻结自托管网页内容。重复设置同一 Version 的 no-op 不代表一次新的发布或复检；若需要主动重新验证已在槽位中的版本，应设计独立检查行为。

<a id="br-pub-009"></a>
### BR-PUB-009：原子写入

以下操作必须全部成功或全部失败：

- 当前 admin 和 Version/Review 发布资格复查。
- Publication 存在性和 expected revision 检查。
- Publication 创建或 testVersionId/revision/审计更新。
- PublicationHistory 插入。

替换、管理员转让、审核撤销或其他槽位操作并发时，旧条件不能成功覆盖新状态。

<a id="br-pub-010"></a>
### BR-PUB-010：不自动扩散

设置 test 槽位不得：

- 修改同一 Version range 内其他 rpcApiMajor 的 Publication。
- 创建 tester 资格。
- 修改 grey/stable 槽位。
- 修改 Application 或 ApplicationVersion。
- 触发自动逐步灰度或稳定发布。

未来批量操作必须由多个单分区命令组合，并明确部分失败与补偿语义。

## 最小领域模型

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

## 用例端口

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

## 数据模型

### application_publications

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

### application_publication_history

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

## API 草图

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

## 测试与验收

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

## 实现前需要确认

- MongoDB 部署是否支持跨 Application、Version、Review、Publication、History 的事务边界。

## 后续用例

UC-APP-007 只建立测试发布指针。Tester 资格随后确定为 Application 级，加入凭证不绑定 rpcApiMajor：

```text
UC-APP-008：创建或轮换 Application Tester 加入链接
UC-APP-009：通过有效链接加入 Application Tester 列表
UC-APP-010：当前管理员移除 Application Tester
UC-APP-011：当前管理员显式撤销 Tester 加入链接
UC-APP-012：为 Tester 解析 Application 的 test 启动目标
```

## 迁移说明

服务从未上线，不迁移 Application.betaVersion、Version.status=TEST 或内嵌 tester 数组。新模型直接创建按 rpcApiMajor 分区的 Publication 和追加式 History。

## 变更记录

- 2026-09-15：建立 UC-APP-007；当前 admin 可把兼容的 APPROVED Version 放入单个 rpcApiMajor 的 test 槽位，并原子追加 PublicationHistory。
- 2026-09-16：由 UC-APP-008 确认 Tester Membership 属于 Application、admin 不隐式成为 Tester，加入链接不绑定 rpcApiMajor。
- 2026-09-16：由 UC-APP-012 确认 App Center 使用 exact rpcApiMajor Publication 和 capabilities 为 ACTIVE Tester 返回 TestLaunchDescriptor，不把选择规则下放给客户端。
