<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-014 --spec tools/brief-specs/UC-APP-014.json -->
# Brief — UC-APP-014：更新应用公开资料修订草稿

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-014` 更新应用公开资料修订草稿 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PRF-008`–`BR-PRF-014`（7 条） |
| 外部引用 BR | `BR-PRF-003`–`BR-PRF-005`（3 条）（来自 `UC-APP-013`） |
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

### 可编辑与不可编辑字段

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

### 输入与身份

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

### 主流程

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

### 异常流程

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

### 最小领域行为

```text
ApplicationProfileRevision.ReplaceDraft(
  expectedRevision,
  replacement,
  updatedBy,
  updatedAt,
) -> ApplicationProfileRevision
```

单实体内部可以保护 DRAFT、revision、不可变字段和资料字段不变量；跨 Application 的当前 admin 检查由 Repository 的原子操作共同保护。

### 用例端口

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

### 数据模型变化

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

### API 草图

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

### 测试与验收

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

### 实现依赖与交付边界

本次交付为当前后端工作包：Domain、UseCase、MongoDB 原子 Repository、显式 migration、独立 API Proto 及生成物、可信身份 HTTP/原生 gRPC、Wire 和真实 MongoDB E2E。前端、生产 Gateway、资料管理查询和 UC-APP-016 审核决定分别交付，不阻塞当前命令实现。不得调用 Auth Scope Catalog、DNS、图标 URL 或资产服务。

沿用 Application `coordinationRevision` 技术写栅栏，在事务内保护当前管理员资格；资料生命周期、revision 和工作指针同时受最终条件检查保护。数据不变量异常使用 `ApplicationProfileStateInconsistent`，HTTP 500 / gRPC INTERNAL，并输出脱敏 ERROR 告警；不得伪装成客户端冲突或自动修复损坏状态。数据库驱动错误、完整资料文本和身份凭据不进入错误响应或普通日志。

验收必须运行 `make check-full`，覆盖所有 BR 的单元测试、真实副本集 validator/index、回滚、管理员转让竞争和 HTTP/gRPC E2E；冻结代码、API 和设计来源后运行，交付报告与本地 commit，禁止 push。

前置依赖是 UC-APP-013 已完成且通过 `make check-full`，复用其领域值对象、Proto 资料表达、工作指针与 schema。当前工作包不新增集合；如发现约束不能表达真实更新，先通过显式 migration 演进，禁止启动时静默修改 schema。

内部路由 `PUT /v1/applications/{application_id}/profile-revisions/{profile_revision_id}`，gRPC `app_center.v1.application_profile_revision.ApplicationProfileRevision/UpdateApplicationProfileRevision`。正文严格只接受三个完整可编辑字段，沿用 UC013 的显式 null 和绑定检查。HTTP expectedRevision 只来自一个强 ETag 的 If-Match（引号内十进制正整数，int64 范围），禁止弱 ETag、星号、多值和 query/body 覆盖；原生 gRPC 使用 expected_revision。缺少 If-Match 为428，格式错误400；stale 为412，原生 gRPC 为ABORTED；NotDraft 为409/ABORTED，其余沿用 UC013 的分类。

no-op 也必须在同一事务验证当前管理员、DRAFT、expectedRevision 和工作指针，然后返回当前记录，保持全部业务字段和审计不变。技术写栅栏允许变化。revision 溢出为内部失败，不能绕回。UC014 验证更新与状态迁移的底层竞争；UC015 完成后补充通过真实提交命令与编辑竞争的闭环测试。

## 业务规则（UC-APP-014 权威正文）

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-008 -->
### BR-PRF-008：仅草稿可编辑

只有 reviewStatus 为 `DRAFT` 的 ApplicationProfileRevision 可以被本用例更新。

`SUBMITTED/APPROVED/REJECTED` 等非 DRAFT 状态不能绕过各自生命周期用例直接修改。REJECTED 是终态；继续编辑旧内容时，由网页端预填后调用 UC-APP-013 创建新修订，服务端不提供恢复命令。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-009 -->
### BR-PRF-009：完整替换

请求必须提供当前全部可编辑字段，服务端以新值整体替换旧值：

- displayName 缺失是非法请求，不回退到 Application.name 或旧 displayName。
- description 缺失是非法请求；`null` 表示明确清除简介。
- icon 缺失是非法请求；`null` 表示明确清除图标字符串。
- 本用例不提供单字段 Patch，也不使用字段 mask。

完整替换让一次资料快照始终可以独立理解，并避免“字段缺失”同时表示清除、继承和不修改。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-010 -->
### BR-PRF-010：不可变身份与创建审计

profileRevisionId、applicationId、sequence、createdBy 和 createdAt 创建后不可修改。reviewStatus 只能由提交审核和审核决定用例改变。

管理员转让不会改写 createdBy；updatedBy 只记录最近一次真实修改的调用者。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-011 -->
### BR-PRF-011：乐观并发与 no-op

- 创建 DRAFT 时 revision 为 1。
- 客户端更新时必须提交自己读取到的 expectedRevision。
- 只有 `currentRevision == expectedRevision` 才能更新或确认 no-op。
- 真实修改成功后 revision 原子增加 1。
- revision 不匹配时不自动合并，也不执行覆盖。

如果 expectedRevision 匹配，但规范化后的 displayName、description 和 icon 与当前内容完全相同，则返回当前 ProfileRevision，不修改 revision、updatedBy 或 updatedAt。

revision 属于整个 ApplicationProfileRevision。后续审核提交和其他生命周期迁移在成功改变状态时也应增加 revision，避免较早发出的草稿更新覆盖状态变化。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-012 -->
### BR-PRF-012：字段规则复用与图标边界

displayName、description 和 icon 必须分别满足 [BR-PRF-003](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005)。字段规则只有一个权威定义，UC-APP-014 不维护宽松副本。

本用例接受并保存 icon 字符串，但不解析其格式、不读取其指向内容，也不建立受控资产生命周期；它同样不修改 ApplicationVersion 字段。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-013 -->
### BR-PRF-013：权限、状态与更新原子性

当前管理员身份、ProfileRevision 归属、DRAFT 状态、expectedRevision 和内容写入必须在同一事务或等价原子边界中确认。

这同时防止：

- 原 admin 在管理员转让完成后继续修改资料。
- ProfileRevision 提交审核后，较早发出的更新请求又把内容写回。
- 两个编辑页面静默覆盖彼此。
- 通过跨 Application ID 组合修改其他应用的资料修订。

<!-- 权威位置: use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-014 -->
### BR-PRF-014：草稿修改审计粒度

当前只保存最近一次真实修改的 updatedBy、updatedAt 和 revision，不保存每次草稿编辑的完整内容历史。

未来提交审核时应保存不可变的资料快照。若出现撤销未提交编辑、比较草稿版本或多人协作编辑的真实需求，再引入 DraftRevision 或操作历史，不提前承担该复杂度。

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
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-014`（use-cases/UC-APP-014-update-draft-application-profile-revision.md）：后续用例、迁移说明、变更记录
- `UC-APP-013`（use-cases/UC-APP-013-create-application-profile-revision.md）：目标与范围、业务边界、输入与身份、网页端重新编辑被拒绝资料、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、尚未决定但不阻塞文档、后续用例、迁移说明、变更记录、实现依赖与交付边界
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-014-update-draft-application-profile-revision.md` | 336 | `fde28528679f` |
| `use-cases/UC-APP-013-create-application-profile-revision.md` | 404 | `42ec2452522f` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
