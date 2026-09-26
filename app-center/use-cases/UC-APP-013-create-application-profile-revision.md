# UC-APP-013：创建应用公开资料修订草稿

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，为 Application 创建一份完整但尚未提交审核的公开资料草稿。

本用例首次建立独立的 `ApplicationProfileRevision`。它把面向用户的目录资料与以下概念分离：

- Application 的稳定身份、技术名称和当前管理员。
- ApplicationVersion 的网页运行内容、RPC 兼容声明和 scopes。
- ApplicationPublication 的 test/grey/stable 运行版本槽位。

本用例只创建 `DRAFT` ApplicationProfileRevision，不编辑既有草稿、不提交审核、不批准、不发布，也不改变应用对普通用户的可见性。

第一版草稿包含：

```text
displayName
description
icon
```

`icon` 当前只是可空、不透明字符串。App Center 不在本轮解释它是 URL、资产 ID 还是其他引用，也不读取它指向的内容。未来确定受控资产生命周期时，再通过新用例和迁移规则收紧其语义。

## 业务边界

```text
Application
  id / name / adminId / createdAt

ApplicationProfileRevision
  一版完整的公开目录资料草稿

ApplicationVersion
  一版可运行网页及其权限、兼容声明
```

修改公开资料不会创建虚假的 ApplicationVersion；创建运行版本也不会复制公开资料。

ApplicationProfileRevision 的批准不等于运行版本已经 stable，运行版本 stable 也不等于存在可公开展示的资料。首版目标是在资料审核批准时自动把该 Revision 设为当前公开资料；普通用户目录如何组合当前公开资料与 stable 运行版本，由后续资料审核和目录查询用例定义。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

Command：

```text
CreateApplicationProfileRevisionCommand {
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

applicationId、profileRevisionId、sequence、reviewStatus、createdBy、createdAt、revision、updatedBy 和 updatedAt 不属于请求正文。

请求提供的是完整资料快照，不从 Application.name 或既有 ProfileRevision 隐式继承缺失字段。没有简介或图标字符串时分别显式使用 `null`。

## 网页端重新编辑被拒绝资料

当管理员希望继续修改一份 REJECTED ProfileRevision 时，网页端可以从 [GetApplicationProfileRevisionForAdmin](../query-contracts/profile-management.md#getapplicationprofilerevisionforadmin) 的结果读取其 displayName、description 和 icon，预填到创建页面，再提交一次普通的 `CreateApplicationProfileRevisionCommand`。这条途径不增加专用读取接口。

对 App Center 而言，这始终是一次新建：系统分配新的 profileRevisionId、sequence 和创建审计，Command 不包含源 Revision ID。App Center 不提供复制或恢复 REJECTED ProfileRevision 的额外命令或接口；REJECTED 的终态语义以 [BR-PRF-031](UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) 为准。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 校验并规范化 displayName、description 和 icon。
4. 生成 UUIDv7 profileRevisionId，并取得 UTC createdAt。
5. 初始化 reviewStatus=`DRAFT`、revision=1、createdBy=updatedBy=authId、updatedAt=createdAt。
6. Repository 在同一个原子操作中：
   - 确认 Application 存在且 adminId 仍等于调用者 authId。
   - 确认该 Application 当前没有 DRAFT 或 SUBMITTED ProfileRevision。
   - 取得并增加 Application.nextProfileRevisionSequence。
   - 插入新的 ApplicationProfileRevision。
7. 返回完整的 ApplicationProfileRevision，并用 ETag 暴露 revision。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- Application 不存在：`ApplicationNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- displayName 不符合规则：`InvalidApplicationDisplayName`。
- description 不符合规则：`InvalidApplicationDescription`。
- icon 不符合规则：`InvalidApplicationIcon`。
- Application 已存在 DRAFT 或 SUBMITTED ProfileRevision：`ApplicationProfileWorkRevisionAlreadyExists`。DRAFT 由 [UC-APP-014](UC-APP-014-update-draft-application-profile-revision.md) 编辑；SUBMITTED 则等待审核决定，不创建并行草稿。
- ID 生成、时钟或持久化失败：内部失败，不产生部分 ProfileRevision，也不消耗 sequence。

## 业务规则

<a id="br-prf-001"></a>
### BR-PRF-001：资料修订身份与序号

- profileRevisionId 是系统生成的全局唯一 UUIDv7，创建后不可修改。
- sequence 由单个 Application 内部计数器分配，从 1 开始并严格递增。
- `(applicationId, sequence)` 唯一。
- sequence 只用于稳定排序、审计和人类识别，不代表审核状态，也不代替乐观并发 revision。

<a id="br-prf-002"></a>
### BR-PRF-002：创建权限

创建者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在真正写入时仍是 Application.adminId。

createdBy 记录本次 ProfileRevision 的创建者。后续管理员转让不会改写历史 createdBy。

<a id="br-prf-003"></a>
### BR-PRF-003：displayName

- 是面向普通用户的公开显示名称，不承担路由、唯一键或授权职责。
- 输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–80 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 不要求全局唯一，也不要求在同一管理员或 Application 范围内唯一。
- Application.name 不作为 displayName 的默认值；调用者必须明确提供。

公开展示时仍必须按普通文本转义。displayName 不是 HTML、Markdown 或富文本。

<a id="br-prf-004"></a>
### BR-PRF-004：description

- description 是可空的公开应用简介；没有简介时保存 `null`，不保存空字符串。
- 非空输入按 Unicode NFC 规范化后保存。
- 规范化后长度为 1–1000 个 Unicode code point。
- 首尾不允许 Unicode whitespace。
- 不允许 Unicode General Category `Cc`、`Cf`、`Cs` 字符或 `Zl/Zp` 行、段分隔符。
- 当前只保存纯文本，不解释 HTML、Markdown、链接或富文本语法。

公开展示时必须按普通文本转义。若未来需要多段或富文本简介，应通过新用例和明确的内容安全规则扩展，而不是放宽当前字段的隐式解释。

<a id="br-prf-005"></a>
### BR-PRF-005：完整资料快照与图标边界

- 一条 ApplicationProfileRevision 表示一版完整资料，而不是字段 patch。
- 本用例的完整快照由 displayName、description 和 icon 构成；缺失 displayName 不会回退到 Application.name。
- ProfileRevision 不复制 ApplicationVersion 的 versionLabel、launchUrl、RPC 声明、capabilities、scopes 或发布状态。
- icon 可为 `null`；非空值按 Unicode NFC 规范化，长度为 1–512 个 Unicode code point，首尾不允许 Unicode whitespace，不允许 `Cc/Cf/Cs/Zl/Zp`。
- icon 是不透明纯字符串；App Center 不解析 scheme、不验证资产存在性、不请求指向内容，也不把它宣称为受控或不可变资产。
- 未来把 icon 收紧为受控资产引用时，通过新用例、新字段语义和显式迁移完成，不在当前字符串上隐式增加强保证。

<a id="br-prf-006"></a>
### BR-PRF-006：初始生命周期与单一工作修订

- 新 ProfileRevision 的 reviewStatus 固定为 `DRAFT`；调用者不能指定其他状态。
- 每个 Application 同时最多存在一条 reviewStatus 为 DRAFT 或 SUBMITTED 的工作修订。
- DRAFT 不属于公开目录，不改变已发布资料，也不会让 Application 自动公开。
- DRAFT 迁移为 SUBMITTED 后继续占用该工作位；在 PENDING ProfileReview 得到 APPROVED 或 REJECTED 决定前，不创建下一份 DRAFT。
- APPROVED 或 REJECTED 决定产生后释放工作位；它们不阻止后续创建新 DRAFT。

<a id="br-prf-007"></a>
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

## 最小领域模型

```text
ApplicationProfileRevision {
  profileRevisionId: ApplicationProfileRevisionId
  applicationId: ApplicationId
  sequence: ProfileSequence
  displayName: ApplicationDisplayName
  description: ApplicationDescription?
  icon: ApplicationIcon?
  reviewStatus: DRAFT
  createdBy: AuthId
  createdAt: Instant
  revision: 1
  updatedBy: AuthId
  updatedAt: Instant
}

ApplicationProfile {
  applicationId: ApplicationId
  workingProfileRevisionId: ApplicationProfileRevisionId
}
```

ApplicationProfileRevision 是独立实体，不嵌入 Application 或 ApplicationVersion。ApplicationProfile 的 workingProfileRevisionId 指向唯一的 DRAFT 或 SUBMITTED 工作修订；Application 上的 nextProfileRevisionSequence 只是序号分配所需的持久化技术状态。

## 用例端口

```go
type ApplicationProfileRevisionIDGenerator interface {
    NewUUIDv7() (ApplicationProfileRevisionID, error)
}

type Clock interface {
    Now() time.Time
}

type ApplicationProfileRevisionRepository interface {
    // CreateDraft 原子地检查当前 admin、工作修订唯一性，分配 sequence，
    // 插入草稿并设置 ApplicationProfile.workingProfileRevisionId。
    CreateDraft(
        ctx context.Context,
        expectedAdminID AuthID,
        draft DraftApplicationProfileRevision,
    ) (*ApplicationProfileRevision, error)
}
```

Repository 需要区分 Application 不存在、管理员不匹配、DRAFT/SUBMITTED 工作修订已存在和基础设施失败。

## 数据模型

逻辑 collection：`application_profile_revisions`。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `profileRevisionId` | 资料修订稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | `(applicationId, sequence)` | no |
| `sequence` | 应用内资料修订序号 | int32 | `>= 1` | `(applicationId, sequence)` | no |
| `displayName` | 公开显示名称 | string | NFC；1–80 code points；首尾无 whitespace；禁止 `Cc/Cf/Cs/Zl/Zp` | no | no |
| `description` | 公开纯文本简介 | string | NFC；1–1000 code points；首尾无 whitespace；禁止 `Cc/Cf/Cs/Zl/Zp` | no | yes |
| `icon` | 公开图标的不透明字符串 | string | NFC；1–512 code points；首尾无 whitespace；禁止 `Cc/Cf/Cs/Zl/Zp`；不解释内容 | no | yes |
| `reviewStatus` | 资料审核生命周期 | string enum | 本用例只允许 `DRAFT` | partial `(applicationId)` where status in `DRAFT/SUBMITTED` | no |
| `createdBy` | 创建者 Auth ID | string | opaque authId | no | no |
| `createdAt` | 创建时间 | datetime | UTC / RFC 3339 | no | no |
| `revision` | 乐观并发版本 | int64 | 本用例固定为 1 | no | no |
| `updatedBy` | 最近修改者 | string | opaque authId；本用例等于 createdBy | no | no |
| `updatedAt` | 最近修改时间 | datetime | UTC / RFC 3339；本用例等于 createdAt | no | no |

索引与 validator：

- profileRevisionId 唯一索引。
- `(applicationId, sequence)` 复合唯一索引。
- 对 reviewStatus 属于 `DRAFT/SUBMITTED` 的文档建立以 applicationId 为键的 partial unique index，保证每个 Application 至多一份工作修订。
- description 字段必须存在；无简介时值为 null。
- icon 字段必须存在；无图标字符串时值为 null，非空值遵守 [BR-PRF-005](#br-prf-005)。
- reviewStatus 在本用例只能写入 DRAFT。
- revision、updatedBy 和 updatedAt 必须存在，创建时分别为 1、createdBy 和 createdAt。

## 对 Application 持久化模型的影响

`applications` 增加一个技术计数器，不增加 Application 业务字段：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `nextProfileRevisionSequence` | 下一个可分配的资料修订序号 | int32 | `>= 1`；创建 Application 时初始化为 1 | no | no |

只有 ProfileRevision 创建 Repository 可以原子增加该字段；外部 API 不返回它。

ApplicationProfile 投影同时把 `workingProfileRevisionId` 设置为新建的 profileRevisionId。该指针在提交审核后保持不变，直到 [UC-APP-016](UC-APP-016-decide-application-profile-revision-review.md) 产生批准或拒绝决定时才清空。

## API 草图

```text
POST /applications/{applicationId}/profile-revisions
Authorization: <authenticated identity>
```

请求：

```json
{
  "displayName": "课程表",
  "description": "查看个人课表与教学安排。",
  "icon": "course-table"
}
```

没有简介时：

```json
{
  "displayName": "课程表",
  "description": null,
  "icon": null
}
```

响应：`201 Created`

```text
ETag: "1"
```

```json
{
  "profileRevisionId": "profile-revision-uuid",
  "applicationId": "application-uuid",
  "sequence": 1,
  "displayName": "课程表",
  "description": "查看个人课表与教学安排。",
  "icon": "course-table",
  "reviewStatus": "DRAFT",
  "createdBy": "auth-id-from-identity",
  "createdAt": "2026-09-16T10:00:00Z",
  "revision": 1,
  "updatedBy": "auth-id-from-identity",
  "updatedAt": "2026-09-16T10:00:00Z"
}
```

API 路径、错误编码和响应字段尚未形成兼容承诺。

## 测试与验收

领域测试：

- displayName 在 NFC 后按 code point 计数，1 和 80 可接受，0 和 81 被拒绝。
- displayName 首尾 whitespace、控制/格式/代理字符和行段分隔符被拒绝。
- 不同 Application 或同一 Application 的不同历史 revision 可以使用相同 displayName；它不是唯一键。
- description 为 null 可接受；空字符串、首尾 whitespace、超过 1000 code points 或包含禁用字符时被拒绝。
- icon 为 null 可接受；非空字符串按 [BR-PRF-005](#br-prf-005) 规范化和校验，但不解析其内容。
- 输入按 NFC 保存；显示内容始终是纯文本。
- 新资料修订只能处于 DRAFT。
- Command 不接受 ApplicationVersion 字段或系统生成字段。

UseCase 测试：

- 只有 developerStatus=`APPROVED` 的当前 admin 可以创建。
- profileRevisionId、sequence、状态和审计字段不受请求正文控制。
- Repository 返回 DRAFT 或 SUBMITTED 工作修订已存在时映射为 `ApplicationProfileWorkRevisionAlreadyExists`。
- 创建结果的 revision 为 1，createdBy=updatedBy，createdAt=updatedAt。
- 任一依赖失败时不返回成功结果。

Repository 集成测试：

- 同一 Application 的两个并发创建请求最多一个成功。
- 不同 Application 可以各自拥有一份 DRAFT；同一 Application 在 SUBMITTED 期间不能创建下一份 DRAFT。
- 管理员转让与创建并发时不会让旧管理员越权写入。
- 原子操作失败时不插入 ProfileRevision，也不增加 nextProfileRevisionSequence。
- description=null 与 icon=null 可以持久化，缺失任一字段都被 validator 拒绝。
- partial unique index 与 document validator 符合表定义。

API 测试：

- 请求正文不能覆盖 applicationId、profileRevisionId、sequence、reviewStatus 或审计字段。
- description 缺失与空字符串均被拒绝；无简介使用显式 null。
- 成功响应包含完整 ProfileRevision，并返回 `ETag: "1"`。
- 身份、资格、管理员、字段和工作修订冲突错误映射正确。

## 尚未决定但不阻塞文档

- 尚未存在公开资料时，管理页面是否用 Application.name 作为非公开占位显示；普通用户目录不得把该占位当作已审核 displayName。

## 后续用例

[UC-APP-014](UC-APP-014-update-draft-application-profile-revision.md) 使用 expectedRevision 完整替换 DRAFT 的 displayName、description 和 icon，不创建新的 ProfileRevision。

## 迁移说明

服务从未上线，不迁移旧 Application 或 ApplicationVersion 上的 displayName、description、icon 数据，也不维护旧 API 或 MongoDB 文档兼容。

## 变更记录

- 2026-09-16：建立 UC-APP-013，创建只含 displayName 与可空 description 的 DRAFT ApplicationProfileRevision；图标等待受控资产用例。
- 2026-09-16：UC-APP-014 建立 DRAFT 的完整替换编辑和乐观并发语义。
- 2026-09-17：将可空 icon 定义为不透明字符串；将单一草稿收紧为单一 DRAFT/SUBMITTED 工作修订，PENDING 审核期间不得创建下一份 DRAFT。

## 实现依赖与交付边界

本次交付为当前后端工作包：Domain、UseCase、MongoDB 原子 Repository、显式 migration、独立 API Proto 及生成物、可信身份 HTTP/原生 gRPC、Wire 和真实 MongoDB E2E。前端、生产 Gateway、资料管理查询和 UC-APP-016 审核决定分别交付，不阻塞当前命令实现。不得调用 Auth Scope Catalog、DNS、图标 URL 或资产服务。

沿用 Application `coordinationRevision` 技术写栅栏，在事务内保护当前管理员资格；资料生命周期、revision 和工作指针同时受最终条件检查保护。数据不变量异常使用 `ApplicationProfileStateInconsistent`，HTTP 500 / gRPC INTERNAL，并输出脱敏 ERROR 告警；不得伪装成客户端冲突或自动修复损坏状态。数据库驱动错误、完整资料文本和身份凭据不进入错误响应或普通日志。

验收必须运行 `make check-full`，覆盖所有 BR 的单元测试、真实副本集 validator/index、回滚、管理员转让竞争和 HTTP/gRPC E2E；冻结代码、API 和设计来源后运行，交付报告与本地 commit，禁止 push。

UC-APP-001 已提供 Application、`nextProfileRevisionSequence=1`、计数器 validator 和可信 Developer 身份；无需重建计数器。UC-APP-013 新增 `application_profile_revisions` 与 `application_profiles` 的显式 migration，并纳入启动 readiness。

`application_profiles` 以 applicationId 唯一：workingProfileRevisionId 和 currentPublishedProfileRevisionId 均为必须存在的可空 UUIDv7。首次创建 Profile 时公开指针为 null；再次创建仅设置工作指针，保留已有公开指针。Revision schema 表达 DRAFT/SUBMITTED/APPROVED/REJECTED 已定义生命周期，但当前入口只写 DRAFT。工作指针和实际 DRAFT/SUBMITTED 唯一记录必须相符；有正常工作修订返回 AlreadyExists，损坏或悬空指针返回内部一致性失败。sequence 分配须检查 int32 溢出，失败不消费序号。

NFC 在 `internal/profile/domain` 的值对象构造中执行，严格拒绝非法 UTF-8，依照 ADR-003 接受的窄依赖使用 `golang.org/x/text/unicode/norm`。领域重建持久化数据时验证已为规范形式，不悄悄修复数据库。

内部 HTTP 路径为 `POST /v1/applications/{application_id}/profile-revisions`，外部路径只加 `/app-center`；gRPC 使用 `app_center.v1.application_profile_revision.ApplicationProfileRevision/CreateApplicationProfileRevision`。HTTP body 仅包含 displayName、description、icon；路径/query 不能覆盖正文、归属或系统字段。未知、重复、缺失字段和非预期 JSON 类型均拒绝；不得依赖 Proto 的忽略未知字段默认行为。

Proto 的 description/icon 使用 `google.protobuf.Value`，只接受 string_value 或 null_value，缺失 Value 和其他 kind 均非法；保持 HTTP 的 string/null 形状，同时让原生 gRPC 区分缺失与显式 null。响应使用相同 string/null 表示，不省略空值。Domain/UseCase 使用本地类型，不依赖 Proto。

错误映射：身份缺失401/UNAUTHENTICATED，资格或管理员不足403/PERMISSION_DENIED，Application 不存在404/NOT_FOUND，非法 applicationId/字段或请求400/INVALID_ARGUMENT，正常工作位冲突409/ABORTED，内部失败500/INTERNAL。沿用稳定 ErrorReason，不以 message 文本判断错误。成功201并携带 ETag。完整创建、空值和非法输入必须双协议验收。
