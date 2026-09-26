# UC-APP-014：更新应用公开资料修订草稿

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 revision 为前提，完整替换一个 DRAFT ApplicationProfileRevision 的可编辑公开资料。

本用例只更新既有 DRAFT，不负责：

- 创建新的 ProfileRevision 或分配新的 sequence。
- 提交审核或改变 reviewStatus。
- 修改已提交、已批准或已拒绝的资料修订。
- 修改 Application.name、adminId 或 ApplicationVersion。
- 定义受控 icon 资产的上传、所有权或生命周期；当前 icon 只是资料中的不透明字符串。
- 改变 Application 的公开可见性或当前公开资料。
- 保存每次草稿编辑的完整内容历史。

读取单个资料草稿或资料修订列表是支持管理页面的 Query，不需要为此建立新的领域实体。

## 可编辑与不可编辑字段

完整替换以下字段：

```text
displayName
description
icon
```

系统在成功修改时更新：

```text
revision
updatedBy
updatedAt
```

以下字段不可由本用例修改：

```text
profileRevisionId
applicationId
sequence
reviewStatus
createdBy
createdAt
```

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
profileRevisionId: ApplicationProfileRevisionId
```

Command：

```text
UpdateDraftApplicationProfileRevisionCommand {
  expectedRevision: int64
  displayName: string
  description: string | null
  icon: string | null
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

HTTP adapter 从 `If-Match` 读取 expectedRevision；gRPC adapter 使用 command 字段表达相同语义。请求正文必须同时包含 displayName、description 和 icon；description 或 icon 为 `null` 表示明确清除该字段，字段缺失不表示保留旧值。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 确认 expectedRevision `>= 1`。
4. 依据 UC-APP-013 的相同规则校验并规范化 displayName、description 和 icon。
5. 从系统时钟取得 updatedAt。
6. Repository 原子确认并更新：
   - Application 存在且 adminId 仍等于调用者 authId。
   - ProfileRevision 存在且属于路径中的 Application。
   - reviewStatus 仍是 `DRAFT`。
   - revision 等于 expectedRevision。
   - 用新 displayName、description 和 icon 完整替换可编辑资料。
   - 发生真实变化时，revision 增加 1，updatedBy 设为 authId，updatedAt 设为系统时间。
7. 返回更新后的完整 ApplicationProfileRevision 和当前 revision。

如果规范化后的 displayName、description 和 icon 与持久化内容完全相同，则本次操作是 no-op：返回当前实体，不增加 revision，也不修改 updatedBy 或 updatedAt。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedRevision 缺失或 `< 1`：`ApplicationProfileExpectedRevisionRequired`。
- Application 或指定 ProfileRevision 不存在：`ApplicationProfileRevisionNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- ProfileRevision 不属于路径中的 Application：按 `ApplicationProfileRevisionNotFound` 处理。
- reviewStatus 不是 `DRAFT`：`ApplicationProfileRevisionNotDraft`。
- 当前 revision 不等于 expectedRevision：`ApplicationProfileRevisionConflict`。
- displayName 不符合规则：`InvalidApplicationDisplayName`。
- description 不符合规则：`InvalidApplicationDescription`。
- icon 不符合规则：`InvalidApplicationIcon`。
- 持久化失败：内部失败，不返回部分更新结果。

为避免泄露跨应用 profileRevisionId 的存在性，applicationId 与 profileRevisionId 不匹配时不返回真实所属应用。

## 业务规则

<a id="br-prf-008"></a>
### BR-PRF-008：仅草稿可编辑

只有 reviewStatus 为 `DRAFT` 的 ApplicationProfileRevision 可以被本用例更新。

`SUBMITTED/APPROVED/REJECTED` 等非 DRAFT 状态不能绕过各自生命周期用例直接修改。REJECTED 是终态；继续编辑旧内容时，由网页端预填后调用 UC-APP-013 创建新修订，服务端不提供恢复命令。

<a id="br-prf-009"></a>
### BR-PRF-009：完整替换

请求必须提供当前全部可编辑字段，服务端以新值整体替换旧值：

- displayName 缺失是非法请求，不回退到 Application.name 或旧 displayName。
- description 缺失是非法请求；`null` 表示明确清除简介。
- icon 缺失是非法请求；`null` 表示明确清除图标字符串。
- 本用例不提供单字段 Patch，也不使用字段 mask。

完整替换让一次资料快照始终可以独立理解，并避免“字段缺失”同时表示清除、继承和不修改。

<a id="br-prf-010"></a>
### BR-PRF-010：不可变身份与创建审计

profileRevisionId、applicationId、sequence、createdBy 和 createdAt 创建后不可修改。reviewStatus 只能由提交审核和审核决定用例改变。

管理员转让不会改写 createdBy；updatedBy 只记录最近一次真实修改的调用者。

<a id="br-prf-011"></a>
### BR-PRF-011：乐观并发与 no-op

- 创建 DRAFT 时 revision 为 1。
- 客户端更新时必须提交自己读取到的 expectedRevision。
- 只有 `currentRevision == expectedRevision` 才能更新或确认 no-op。
- 真实修改成功后 revision 原子增加 1。
- revision 不匹配时不自动合并，也不执行覆盖。

如果 expectedRevision 匹配，但规范化后的 displayName、description 和 icon 与当前内容完全相同，则返回当前 ProfileRevision，不修改 revision、updatedBy 或 updatedAt。

revision 属于整个 ApplicationProfileRevision。后续审核提交和其他生命周期迁移在成功改变状态时也应增加 revision，避免较早发出的草稿更新覆盖状态变化。

<a id="br-prf-012"></a>
### BR-PRF-012：字段规则复用与图标边界

displayName、description 和 icon 必须分别满足 [BR-PRF-003](UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](UC-APP-013-create-application-profile-revision.md#br-prf-005)。字段规则只有一个权威定义，UC-APP-014 不维护宽松副本。

本用例接受并保存 icon 字符串，但不解析其格式、不读取其指向内容，也不建立受控资产生命周期；它同样不修改 ApplicationVersion 字段。

<a id="br-prf-013"></a>
### BR-PRF-013：权限、状态与更新原子性

当前管理员身份、ProfileRevision 归属、DRAFT 状态、expectedRevision 和内容写入必须在同一事务或等价原子边界中确认。

这同时防止：

- 原 admin 在管理员转让完成后继续修改资料。
- ProfileRevision 提交审核后，较早发出的更新请求又把内容写回。
- 两个编辑页面静默覆盖彼此。
- 通过跨 Application ID 组合修改其他应用的资料修订。

<a id="br-prf-014"></a>
### BR-PRF-014：草稿修改审计粒度

当前只保存最近一次真实修改的 updatedBy、updatedAt 和 revision，不保存每次草稿编辑的完整内容历史。

未来提交审核时应保存不可变的资料快照。若出现撤销未提交编辑、比较草稿版本或多人协作编辑的真实需求，再引入 DraftRevision 或操作历史，不提前承担该复杂度。

## 最小领域行为

```text
ApplicationProfileRevision.ReplaceDraft(
  expectedRevision,
  replacement,
  updatedBy,
  updatedAt,
) -> ApplicationProfileRevision
```

单实体内部可以保护 DRAFT、revision、不可变字段和资料字段不变量；跨 Application 的当前 admin 检查由 Repository 的原子操作共同保护。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ApplicationProfileRevisionRepository interface {
    ReplaceDraft(
        ctx context.Context,
        applicationID ApplicationID,
        profileRevisionID ApplicationProfileRevisionID,
        expectedAdminID AuthID,
        expectedRevision int64,
        replacement DraftApplicationProfileReplacement,
        updatedAt time.Time,
    ) (*ApplicationProfileRevision, error)
}
```

Repository 必须区分：NotFound、NotAdmin、NotDraft、RevisionConflict 和基础设施失败。

## 数据模型变化

UC-APP-014 不新增 collection 或字段。它使用 UC-APP-013 已建立的：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `displayName` | 公开显示名称 | string | 复用 BR-PRF-003 | no | no |
| `description` | 公开纯文本简介 | string | 复用 BR-PRF-004 | no | yes |
| `icon` | 公开图标的不透明字符串 | string | 复用 BR-PRF-005 | no | yes |
| `reviewStatus` | 资料审核生命周期 | string enum | 本用例要求 `DRAFT` | partial `(applicationId)` where status in `DRAFT/SUBMITTED` | no |
| `revision` | 乐观并发版本 | int64 | `>= 1`；真实修改后递增 | no | no |
| `updatedBy` | 最近一次真实修改者 | string | opaque authId | no | no |
| `updatedAt` | 最近一次真实修改时间 | datetime | UTC / RFC 3339 | no | no |

条件更新至少包含 applicationId、profileRevisionId、reviewStatus=`DRAFT` 和 expectedRevision。管理员检查与更新必须和 Application.adminId 的读取处于同一原子边界。

## API 草图

```text
PUT /applications/{applicationId}/profile-revisions/{profileRevisionId}
Authorization: <authenticated identity>
If-Match: "3"
```

请求正文包含完整可编辑状态：

```json
{
  "displayName": "课程表与教学安排",
  "description": null,
  "icon": "course-table-v2"
}
```

成功：`200 OK`，响应完整 ApplicationProfileRevision，并返回：

```text
ETag: "4"
```

若规范化后内容没有变化，同样返回 `200 OK` 和当前完整 ApplicationProfileRevision，但 ETag 保持为请求匹配的 revision。

候选 HTTP 映射：

- 缺少或非法 If-Match：`428 Precondition Required` / `400 Bad Request`。
- revision 不匹配：`412 Precondition Failed`。
- 非 DRAFT：`409 Conflict`。
- 身份或当前管理员权限不足：`401 Unauthorized` / `403 Forbidden`。
- Application/ProfileRevision 不存在或不匹配：`404 Not Found`。

## 测试与验收

领域测试：

- DRAFT 且 revision 匹配时可以完整替换 displayName、description 和 icon。
- 非 DRAFT 或 revision 不匹配时不产生变化。
- ID、归属、sequence、状态和创建审计在更新后保持不变。
- description 可以从字符串改为 null，也可以从 null 改为合法字符串。
- icon 可以在合法字符串与 null 之间完整替换，但服务端不解析其内容。
- 相同规范化内容是 no-op，不增加 revision。
- 字段继续满足 UC-APP-013 的 NFC、长度、字符类别和纯文本规则。

UseCase 测试：

- 只有 developerStatus=`APPROVED` 的当前 admin 可以更新。
- updatedBy 只能来自可信 authId，updatedAt 只能来自 Clock。
- 字段校验失败时不调用 Repository。
- Repository 业务错误映射正确。

Repository 集成测试：

- 两个相同 expectedRevision 的并发真实更新最多一个成功。
- revision、updatedBy、updatedAt 与资料内容在同一原子写入中变化。
- 更新与管理员转让并发时，旧 admin 不能越权成功。
- 更新与提交审核并发时，不会修改已离开 DRAFT 的 ProfileRevision。
- applicationId/profileRevisionId 不匹配时返回 NotFound。
- no-op 不产生持久化审计变化。

API 测试：

- 使用 PUT 完整替换；displayName、description 或 icon 缺失是非法请求。
- description=`null` 和 icon=`null` 分别明确清除简介和图标字符串。
- If-Match 正确时返回新 ETag，过期时返回 412。
- no-op 返回当前 ETag，不伪造一次修改。
- 请求正文不能修改 ID、sequence、reviewStatus 或审计字段。
- ApplicationVersion 字段不会被接受。

## 后续用例

资料草稿创建和编辑已经闭合。下一项资料生命周期用例可以是：

```text
[UC-APP-015](UC-APP-015-submit-application-profile-revision-review.md)：提交 ApplicationProfileRevision 审核。
```

它应冻结本次资料内容并创建独立、不可变的审核快照，而不是继续扩展通用 Update。

## 迁移说明

服务从未上线，不迁移旧字段级资料更新 API。新入口直接使用完整替换和 revision；旧代码只作为需求证据。

## 变更记录

- 2026-09-16：建立 UC-APP-014，只允许当前管理员以 expectedRevision 完整替换 DRAFT ApplicationProfileRevision 的 displayName 和 description。
- 2026-09-17：将 icon 纳入完整替换内容；它当前为可空不透明字符串，不建立资产生命周期。

## 实现依赖与交付边界

本次交付为当前后端工作包：Domain、UseCase、MongoDB 原子 Repository、显式 migration、独立 API Proto 及生成物、可信身份 HTTP/原生 gRPC、Wire 和真实 MongoDB E2E。前端、生产 Gateway、资料管理查询和 UC-APP-016 审核决定分别交付，不阻塞当前命令实现。不得调用 Auth Scope Catalog、DNS、图标 URL 或资产服务。

沿用 Application `coordinationRevision` 技术写栅栏，在事务内保护当前管理员资格；资料生命周期、revision 和工作指针同时受最终条件检查保护。数据不变量异常使用 `ApplicationProfileStateInconsistent`，HTTP 500 / gRPC INTERNAL，并输出脱敏 ERROR 告警；不得伪装成客户端冲突或自动修复损坏状态。数据库驱动错误、完整资料文本和身份凭据不进入错误响应或普通日志。

验收必须运行 `make check-full`，覆盖所有 BR 的单元测试、真实副本集 validator/index、回滚、管理员转让竞争和 HTTP/gRPC E2E；冻结代码、API 和设计来源后运行，交付报告与本地 commit，禁止 push。

前置依赖是 UC-APP-013 已完成且通过 `make check-full`，复用其领域值对象、Proto 资料表达、工作指针与 schema。当前工作包不新增集合；如发现约束不能表达真实更新，先通过显式 migration 演进，禁止启动时静默修改 schema。

内部路由 `PUT /v1/applications/{application_id}/profile-revisions/{profile_revision_id}`，gRPC `app_center.v1.application_profile_revision.ApplicationProfileRevision/UpdateApplicationProfileRevision`。正文严格只接受三个完整可编辑字段，沿用 UC013 的显式 null 和绑定检查。HTTP expectedRevision 只来自一个强 ETag 的 If-Match（引号内十进制正整数，int64 范围），禁止弱 ETag、星号、多值和 query/body 覆盖；原生 gRPC 使用 expected_revision。缺少 If-Match 为428，格式错误400；stale 为412，原生 gRPC 为ABORTED；NotDraft 为409/ABORTED，其余沿用 UC013 的分类。

no-op 也必须在同一事务验证当前管理员、DRAFT、expectedRevision 和工作指针，然后返回当前记录，保持全部业务字段和审计不变。技术写栅栏允许变化。revision 溢出为内部失败，不能绕回。UC014 验证更新与状态迁移的底层竞争；UC015 完成后补充通过真实提交命令与编辑竞争的闭环测试。
