# UC-APP-003：更新草稿应用版本

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 revision 为前提，完整替换一个 DRAFT ApplicationVersion 的可编辑内容。

本用例只更新 DRAFT，不负责：

- 提交审核或改变 reviewStatus。
- 修改已提交、已批准、已拒绝或已撤销版本。
- 修改 Application.name 或独立的 ApplicationProfileRevision。
- 修改 stable/grey/test 发布槽位。
- 保存每次草稿编辑的完整历史。

读取单个版本或版本列表是支持管理页面的 Query，不需要为此建立新的领域实体。

## 可编辑与不可编辑字段

完整替换以下字段：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
```

系统在成功修改时更新：

```text
revision
updatedBy
updatedAt
```

以下字段不可由本用例修改：

```text
versionId
applicationId
sequence
reviewStatus
createdBy
createdAt
```

## 旧实现观察

旧 API 分别提供 `update-version-display-name`、`update-version-description`、`update-version-url`、`update-version-icon`、`update-version-version` 等字段级入口。

### KEEP

- 修改前确认调用者拥有应用管理权限。
- versionLabel 和 launchUrl 修改后仍需满足创建时的字段规则。
- 修改 scopes 时仍需验证 Scope Catalog。

### CHANGE

- 由一个完整替换草稿内容的 UseCase 取代多个字段级接口。
- 只允许修改 DRAFT；reviewStatus 由独立状态迁移用例管理。
- 使用 expectedRevision 做乐观并发控制，拒绝静默覆盖。
- 当前管理员检查、状态检查、revision 检查和写入形成一个原子操作。
- 更新时记录 updatedBy、updatedAt，并增加 revision。
- capabilities 和 scopes 作为集合处理，持久化前按字典序排序。

### DROP

- 每个字段一个 RPC/HTTP 入口。
- 不校验当前状态就直接修改版本。
- 仅凭 applicationId + sequence 更新，不验证稳定 versionId。
- 让请求正文修改 status、createdAt 或其他系统字段。
- last-write-wins 式无条件覆盖。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
```

Command：

```text
UpdateDraftApplicationVersionCommand {
  expectedRevision: int64
  versionLabel: string
  launchUrl: string
  rpcApiMinVersion: int32
  rpcApiMaxVersionExclusive: int32
  requiredCapabilities: []string
  requiredScopes: []string
  optionalScopes: []string
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

HTTP adapter 从 `If-Match` 读取 expectedRevision；gRPC adapter 使用 command 字段表达相同语义。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 确认 expectedRevision `>= 1`。
4. 使用 UC-APP-002 的相同规则校验所有可编辑字段。
5. 通过 ScopeCatalog adapter 确认 requiredScopes 和 optionalScopes 当前允许被新版本申请。
6. 将 capabilities 和 scopes 分别按字典序规范化为稳定集合表示。
7. 从系统时钟取得 updatedAt。
8. Repository 原子确认并更新：
   - Application 存在且 adminId 仍等于调用者 authId。
   - ApplicationVersion 属于路径中的 Application。
   - reviewStatus 仍是 `DRAFT`。
   - revision 等于 expectedRevision。
   - 新 versionLabel 未与同一 Application 的其他版本冲突。
   - 完整替换可编辑字段。
   - revision 增加 1，updatedBy 设为 authId，updatedAt 设为系统时间。
9. 返回更新后的完整 ApplicationVersion 和新 revision。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedRevision 缺失或 `< 1`：`ApplicationVersionRevisionRequired`。
- Application 或指定 Version 不存在：`ApplicationVersionNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 不属于路径中的 Application：按 `ApplicationVersionNotFound` 处理。
- reviewStatus 不是 `DRAFT`：`ApplicationVersionNotDraft`。
- 当前 revision 不等于 expectedRevision：`ApplicationVersionRevisionConflict`。
- versionLabel 与其他 Version 冲突：`ApplicationVersionLabelAlreadyExists`。
- 字段、URL、RPC range、capabilities 或 scopes 非法：沿用 UC-APP-002 对应错误。
- Scope Catalog 无新鲜快照：`ScopeCatalogUnavailable`。
- 持久化失败：内部失败，不返回部分更新结果。

为避免泄露跨应用 versionId 的存在性，applicationId 与 versionId 不匹配时不返回真实所属应用。

## 业务规则

<a id="br-ver-010"></a>
### BR-VER-010：仅草稿可编辑

只有 reviewStatus 为 `DRAFT` 的 ApplicationVersion 可以被本用例更新。

`SUBMITTED/APPROVED/REJECTED/REVOKED` 都不能绕过状态用例直接修改。被拒绝 Version 必须先通过 [UC-APP-006](UC-APP-006-restore-rejected-version-to-draft.md) 显式恢复为 DRAFT。

<a id="br-ver-011"></a>
### BR-VER-011：完整替换

请求必须提供全部可编辑字段，服务端以新值整体替换旧值。空数组表示明确清空该集合，不表示“不修改”。

本用例不提供单字段 Patch，也不使用字段 mask。这样 URL、RPC range、capabilities 和 scopes 可以在同一组校验和一次原子写入中保持一致。

<a id="br-ver-012"></a>
### BR-VER-012：不可变身份与创建审计

versionId、applicationId、sequence、createdBy 和 createdAt 创建后不可修改。reviewStatus 只能由提交审核、审核决定和撤销等独立用例改变。

管理员转让不会改写 createdBy；updatedBy 记录本次实际修改者。

<a id="br-ver-013"></a>
### BR-VER-013：乐观并发

- 创建 DRAFT 时 revision 为 1。
- 客户端更新时必须提交自己读取到的 expectedRevision。
- 只有 `currentRevision == expectedRevision` 才能写入。
- 成功修改后 revision 原子增加 1。
- revision 不匹配时不自动合并，也不执行覆盖。

若 expectedRevision 正确但规范化后的可编辑内容与当前内容完全相同，返回当前 Version，不修改 revision、updatedBy 或 updatedAt。

revision 属于整个 ApplicationVersion，而不是只属于草稿内容；UC-APP-004 及后续生命周期迁移也必须在成功改变状态时增加 revision。

<a id="br-ver-014"></a>
### BR-VER-014：集合规范化

requiredCapabilities、requiredScopes 和 optionalScopes 在业务上都是集合：

- 输入包含重复项时仍然拒绝，而不是静默去重。
- requiredScopes 与 optionalScopes 不能交叉。
- 校验通过后分别按 Unicode code point 字典序排序再保存。
- 集合顺序变化不构成业务修改。

<a id="br-ver-015"></a>
### BR-VER-015：字段规则复用

versionLabel、launchUrl、RPC range、capabilities 和 scopes 必须满足 UC-APP-002 的 BR-VER-003 至 BR-VER-007。规则只有一个定义来源，UC-APP-003 不维护宽松副本。

尤其是：HTTP 开发 URL 仍只能用于 DRAFT；改为公开 HTTPS 后才能进入未来提交审核用例。

<a id="br-ver-016"></a>
### BR-VER-016：权限与更新原子性

管理员身份、DRAFT 状态、expectedRevision、versionLabel 唯一性和写入必须在同一事务或等价原子边界中确认。

这同时防止：

- 原 admin 在管理员转让完成后继续修改。
- Version 提交审核后，较早发出的更新请求又把内容写回。
- 两个编辑页面静默覆盖彼此。

<a id="br-ver-017"></a>
### BR-VER-017：草稿审计粒度

当前只保存最近一次修改者、时间和 revision，不保存每次草稿编辑的完整内容历史。提交审核时由 ApplicationReview 保存不可变快照；若以后确有恢复草稿历史的需求，再引入 DraftRevision，不提前承担该成本。

## 最小领域行为

```text
ApplicationVersion.ReplaceDraft(
  expectedRevision,
  replacement,
  updatedBy,
  updatedAt,
) -> ApplicationVersion
```

单实体内部可以保护 DRAFT、revision 和字段不变量；跨 Application 的当前 admin 检查以及 versionLabel 唯一性由 Repository 的原子操作共同保护。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ScopeCatalog interface {
    EnsureAllRequestable(
        ctx context.Context,
        scopes []ScopeName,
    ) (ScopeCatalogRevision, error)
}

type ApplicationVersionRepository interface {
    ReplaceDraft(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        expectedAdminID AuthID,
        expectedRevision int64,
        replacement DraftApplicationVersionReplacement,
        updatedAt time.Time,
    ) (*ApplicationVersion, error)
}
```

Repository 必须区分：NotFound、NotAdmin、NotDraft、RevisionConflict、VersionLabelConflict 和基础设施失败。

## 数据模型变化

UC-APP-003 不增加 collection。`application_versions` 增加三个非空字段；UC-APP-002 创建时同时初始化。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `revision` | ApplicationVersion 并发版本 | int64 | `>= 1`；创建时为 1；成功修改或状态迁移后递增 | no | no |
| `updatedBy` | 最近一次修改者 | string | opaque authId；创建时等于 createdBy | no | no |
| `updatedAt` | 最近一次修改时间 | datetime | UTC / RFC 3339；创建时等于 createdAt | no | no |

既有索引继续生效：

- versionId 全局唯一。
- `(applicationId, sequence)` 唯一。
- `(applicationId, versionLabel)` 大小写敏感唯一。

条件更新至少包含 versionId、applicationId、reviewStatus=`DRAFT` 和 expectedRevision。管理员检查与更新必须和 Application.adminId 的读取处于同一原子边界。

## API 草图

```text
PUT /applications/{applicationId}/versions/{versionId}
Authorization: <authenticated identity>
If-Match: "3"
```

请求正文必须包含完整可编辑状态：

```json
{
  "versionLabel": "v1.1.0-beta",
  "launchUrl": "http://192.168.1.20:8081/",
  "rpcApiMinVersion": 3,
  "rpcApiMaxVersionExclusive": 5,
  "requiredCapabilities": ["user.profile.v1"],
  "requiredScopes": ["profile.basic"],
  "optionalScopes": ["schedule.read"]
}
```

成功：`200 OK`，响应完整 ApplicationVersion，并返回：

```text
ETag: "4"
```

若内容规范化后没有变化，同样返回 `200 OK` 和当前完整 ApplicationVersion，但 ETag 保持为请求匹配的 revision。

候选 HTTP 映射：

- 缺少或非法 If-Match：`428 Precondition Required` / `400 Bad Request`。
- revision 不匹配：`412 Precondition Failed`。
- 非 DRAFT、标签冲突：`409 Conflict`。
- Scope Catalog 不可用：`503 Service Unavailable`。

## 测试与验收

领域测试：

- DRAFT 且 revision 匹配时可以完整替换可编辑字段。
- 非 DRAFT 或 revision 不匹配时不产生变化。
- 不可变字段在更新后保持不变。
- 相同规范化内容是 no-op，不增加 revision。
- 集合乱序输入规范化后得到稳定顺序；重复和 scope 交叉仍被拒绝。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以更新。
- 使用与 UC-APP-002 相同的字段和 Scope Catalog 规则。
- updatedBy 只能来自可信 authId，updatedAt 只能来自 Clock。
- Scope Catalog 失败时不调用 Repository。
- Repository 业务错误映射正确。

Repository 集成测试：

- 两个相同 expectedRevision 的并发更新最多一个成功。
- revision、updatedBy、updatedAt 与内容在同一原子写入中变化。
- 修改为同一 Application 中已存在的 versionLabel 被唯一索引拒绝。
- 更新与管理员转让并发时，旧 admin 不能越权成功。
- 更新与提交审核并发时，不会修改已离开 DRAFT 的 Version。
- applicationId/versionId 不匹配时返回 NotFound。

API 测试：

- 使用 PUT 完整替换，缺失字段不是“保持旧值”。
- If-Match 正确时返回新 ETag；过期时返回 412。
- 无内容变化时返回当前 ETag，不伪造一次修改。
- 请求正文不能修改 ID、sequence、状态和审计字段。
- HTTP 开发 URL 可以保存为 DRAFT。

## 后续用例

UC-APP-003 之后的状态变化用例是：

```text
UC-APP-004：提交 ApplicationVersion 审核
```

它负责把 DRAFT 内容锁定成一次不可变审核快照，而不是继续扩展通用 Update。详见 [UC-APP-004](UC-APP-004-submit-application-version-review.md)。

## 迁移说明

服务从未上线，不迁移旧字段级更新 API。新入口直接使用完整替换和 revision；旧代码只作为需求证据。

## 变更记录

- 2026-09-15：建立 UC-APP-003，只允许当前管理员以 expectedRevision 完整替换 DRAFT 内容，并引入 revision、updatedBy、updatedAt。
- 2026-09-15：UC-APP-004 明确 Version 生命周期迁移也增加 revision；ScopeCatalog 端口返回提交审计所需的 catalog revision。
- 2026-09-15：UC-APP-006 明确 REJECTED 不能直接编辑，必须先显式恢复为 DRAFT。
