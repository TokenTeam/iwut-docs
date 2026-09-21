# UC-APP-001：开发者新建应用

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的调用者，在其创建配额内建立一个应用，并成为当前管理员。

Application 当前只有四个业务字段：

```text
id
name
adminId
createdAt
```

本用例只负责创建 Application。版本由独立的 ApplicationVersion 用例创建，不在 Application 中保留临时 version 字段。

面向用户公开的 displayName、description 和 icon 属于独立的 ApplicationProfileRevision，需要单独编辑和审核，不在本用例中提前写入 Application。

本轮不处理查询、更新、删除、管理员转让、协作者、审核、发布、OAuth、RPC 兼容或 Resource Hub。

## 旧实现观察

旧用例位于 `iwut-app-center/internal/biz/app.go` 的 `CreateApplication`。

### KEEP

- 调用者身份来自可信上下文，不能由请求正文指定。
- ID 由系统生成。
- name 长度为 1–50，只允许英文字母、数字、`-`、`_`。
- 同一管理员名下不能创建同名应用。

### CHANGE

- `adminId` 是当前管理员的 Auth `authId`，不是永久创建者 ID，未来允许转让。
- 名称按大小写不敏感的方式比较，同时保留用户输入的显示形式。
- 增加 createdAt、开发者资格和创建配额。
- ID 改为 UUIDv7。

### DROP

- client ID、client secret。
- Application 上的 version 及 stable/grey/beta 指针。
- 灰度比例、shuffle code、status、collaborators、redirect URI 和 rule 默认值。
- 未经审核的 displayName、description、icon 等公开目录资料。
- 为后续能力预先写入的业务字段。

## 输入与身份

```text
CreateApplicationCommand {
  name: string
}

DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

约束：

- `adminId` 取自 `DeveloperIdentity.authId`，不属于 Command。
- 只有 `APPROVED` 可以创建应用。
- App Center 信任 Auth 给出的资格结果，不重新执行师生验证。
- 弱师生验证在客户端申请时进行；不向 App Center 传递或保存学生证明材料。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 校验 name。
4. 生成 UUIDv7 Application ID，并从系统时钟取得 UTC createdAt。
5. 以 authId 作为 adminId 构造 Application，并把持久化技术字段 nextVersionSequence 和 nextProfileRevisionSequence 初始化为 1。
6. 原子地检查名称未占用、配额尚有余额，保存 Application 并增加配额用量。若该 adminId 尚无配额记录，在同一原子边界内以进程启动配置给出的初始上限惰性建立；未配置时默认为 10。
7. 返回创建后的 Application。

## 异常流程

- 缺少 authId：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- name 不符合规则：`InvalidApplicationName`。
- 同一 adminId 下存在大小写等价的 name：`ApplicationNameAlreadyExists`。
- 当前应用数量达到创建配额：`ApplicationQuotaExceeded`。
- ID 生成或持久化失败：内部失败，不产生部分结果。

## 业务规则

<a id="br-app-001"></a>
### BR-APP-001：Application ID

ID 由系统生成，必须是 UUIDv7、全局唯一且创建后不可修改。UUIDv7 的时间排序只用于改善索引局部性，业务排序和审计仍以 createdAt 为准；调用者不能依赖 ID 内部时间。

参考：[RFC 9562, UUID Version 7](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.7)。

<a id="br-app-002"></a>
### BR-APP-002：开发者资格与管理员

只有 developerStatus 为 `APPROVED` 的 Auth 用户可以创建 Application。创建时 `adminId = authId`，请求正文不能覆盖它。

adminId 表示当前管理关系。管理员转让成功后它可以改变，但转让过程不属于本用例。

<a id="br-app-003"></a>
### BR-APP-003：名称

- 长度为 1–50。
- 只允许 ASCII 英文字母、数字、`-`、`_`：`^[A-Za-z0-9_-]{1,50}$`。
- 保留输入的大小写用于管理界面和开发者识别，不自动 trim 或改写。
- 唯一性比较使用 ASCII lowercase key；例如 `Course_App` 与 `course_app` 是同名。
- 同名限制范围是同一 adminId；不同管理员可以使用同名应用。

这与 GitHub 仓库路由的大小写不敏感语义相近；GitHub REST API 也明确说明 owner 和 repository path name 不区分大小写。这里不是对 GitHub 全部命名规则的逐项复制。

参考：[GitHub REST API endpoints for repositories](https://docs.github.com/en/rest/repos/repos)。

<a id="br-app-004"></a>
### BR-APP-004：公开资料不属于 Application

- Application 不保存面向用户目录的 displayName、description 或 icon。
- `name` 是技术名称/slug，不替代未来的公开 displayName。
- 公开资料由独立的 ApplicationProfileRevision 表达，并具有自己的草稿、审核和发布生命周期。
- CreateApplicationCommand 不接受公开资料字段，避免在资料审核用例出现前形成未经审核的目录内容。

<a id="br-app-005"></a>
### BR-APP-005：创建配额

每个 adminId 有独立、可调整的 Application Creation Quota。持久化的配额记录是当前上限与占用量的唯一权威来源。

配额记录不存在时，首次创建 Application 必须以进程启动时加载的初始上限惰性建立它。该值由 `APP_CENTER_INITIAL_APPLICATION_QUOTA` 配置，格式为 `>= 0` 的十进制 int32，未设置时默认 10；显式设置为空、非数字、负数或溢出时服务必须启动失败，不得静默回退。

记录已存在时，创建 Application 不得用当前进程的初始值覆盖其 `limit`。改变环境变量只影响之后首次建立的配额记录；未来已有记录只能由独立的配额调整用例修改 `limit`，配额增长规则另行设计。

在删除、归档和转让用例出现前，所有成功创建的 Application 都计入当前管理员配额。

<a id="br-app-006"></a>
### BR-APP-006：并发原子性

名称占用检查、配额检查、Application 写入和配额用量增加必须是一个原子操作。并发请求不能创建大小写等价的同名应用，也不能突破配额。

<a id="br-app-007"></a>
### BR-APP-007：创建时间

createdAt 由 App Center 时钟生成，使用 UTC，创建后不可修改，也不能由请求正文指定。

## 最小领域模型

```text
Application {
  id: ApplicationId
  name: ApplicationName
  adminId: AuthId
  createdAt: Instant
}
```

- ApplicationName 同时持有显示值和用于唯一性比较的 lowercase key。
- 公开 displayName、description 和 icon 不属于当前 Application 模型。
- Developer 资格和创建配额是创建约束，不是 Application 字段。
- ApplicationVersion 是后续独立实体，不属于当前聚合。

## 用例端口

```go
type ApplicationIDGenerator interface {
    NewUUIDv7() (ApplicationID, error)
}

type Clock interface {
    Now() time.Time
}

type ApplicationRepository interface {
    CreateWithinQuota(
        ctx context.Context,
        application *Application,
        initialLimit int32,
    ) error
}
```

`initialLimit` 只能用于惰性创建尚不存在的配额记录，不是本次创建的当前配额决策，也不得覆盖已存在记录的 `limit`。`CreateWithinQuota` 必须使用配额记录自身的 `usedCount < limit` 判定容量，并能区分名称冲突、配额耗尽和基础设施失败。初始值由进程配置在 composition boundary 加载并显式注入 UseCase；Domain、UseCase 和 MongoDB adapter 均不得读取环境变量或自行隐藏默认值。

当前不需要通用 CRUD Repository、事件发布器、每次创建都重新决定配额的 Policy，或在用例内部同步调用 Auth Center。

## 数据模型

### applications

`nameKey`、`nextVersionSequence` 和 `nextProfileRevisionSequence` 是持久化技术字段，不增加 Application 的业务字段数量。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `id` | Application ID | string | UUIDv7 | yes | no |
| `name` | 保留原始大小写的应用名称 | string | `^[A-Za-z0-9_-]{1,50}$` | no | no |
| `nameKey` | name 的 ASCII lowercase 形式 | string | `^[a-z0-9_-]{1,50}$` | `(adminId, nameKey)` | no |
| `adminId` | 当前管理员的 Auth authId | string | opaque authId | `(adminId, nameKey)` | no |
| `createdAt` | 创建时间 | datetime | UTC / RFC 3339 | no | no |
| `nextVersionSequence` | 下一个可分配的版本序号 | int32 | `>= 1`；创建时为 1 | no | no |
| `nextProfileRevisionSequence` | 下一个可分配的资料修订序号 | int32 | `>= 1`；创建时为 1 | no | no |

数据库约束：

- `id` 唯一索引。
- `(adminId, nameKey)` 复合唯一索引。
- 所有字段必须存在。
- nextVersionSequence 只能由 UC-APP-002 的原子版本创建操作增加；nextProfileRevisionSequence 只能由 [UC-APP-013](UC-APP-013-create-application-profile-revision.md) 的原子资料草稿创建操作增加。外部 API 不返回这两个字段。

### application_creation_quotas

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `adminId` | 配额所属 Auth 用户 | string | opaque authId | yes | no |
| `limit` | 当前创建上限，配额的唯一权威值 | int32 | `>= 0`；首次建档使用配置值，默认 10 | no | no |
| `usedCount` | 当前已占用数量 | int32 | `0 <= usedCount <= limit` | no | no |
| `revision` | 并发控制版本 | int64 | 单调递增 | no | no |
| `updatedAt` | 最后变更时间 | datetime | UTC / RFC 3339 | no | no |

首次创建时惰性建立配额记录。创建 Application 的路径对已存在记录只可读取 `limit`，成功时只增加 `usedCount` 和 `revision` 并更新 `updatedAt`，不得改写 `limit`。插入 Application 失败时不能留下配额占用。

## API 草图

```text
POST /applications
Authorization: <authenticated identity>
```

请求：

```json
{
  "name": "Course_Table"
}
```

响应：`201 Created`

```json
{
  "id": "application-uuid",
  "name": "Course_Table",
  "adminId": "auth-id-from-identity",
  "createdAt": "2026-08-23T10:00:00Z"
}
```

API 不接受或返回内部技术字段 `nameKey`。API 路径和错误编码尚未形成兼容承诺。

## 测试与验收

领域测试：

- name 长度 1 和 50 可用，0 和 51 被拒绝。
- name 只接受规定的 ASCII 字符。
- `Course_App` 与 `course_app` 产生相同 nameKey，同时保留各自输入形式。
- id、adminId、createdAt 创建后不可由公开行为修改。
- Application 和 CreateApplicationCommand 都不包含 displayName、description 或 icon。

UseCase 测试：

- 只有 `APPROVED` 可以创建；`PENDING/REJECTED/SUSPENDED` 均被拒绝。
- adminId 只能来自 DeveloperIdentity.authId。
- IDGenerator、Clock 和 Repository 按主流程调用；Repository 只接收进程组装时显式注入的初始上限，默认配置为 10。
- 配置为非默认初始上限时，Repository 收到该配置值；负数等非法启动配置不得进入 UseCase。
- 名称冲突和配额耗尽映射为对应业务错误。
- 任一依赖失败时不返回成功结果。

Repository 集成测试：

- 同一 adminId 下大小写等价名称只有一次成功；不同 adminId 可以同名。
- 初始配额为 10 时前 10 次成功，第 11 次失败。
- 通过显式持久化更新调高 limit 后可以继续创建，且创建路径传入的任何初始配置值都不会覆盖已调整的值。
- 新建 Application 的 nextVersionSequence 和 nextProfileRevisionSequence 都初始化为 1。
- 并发创建不会突破名称唯一性或配额。
- Application 插入失败不会消耗配额。
- document validator 拒绝缺失或非法字段。

API 测试：

- 请求正文不能覆盖 adminId、createdAt、developerStatus、nameKey、nextVersionSequence 或 nextProfileRevisionSequence。
- 成功响应包含四个业务字段，不包含 version 或公开资料。
- 身份、资格、字段、名称冲突和配额错误映射正确。

## 尚未决定但不阻塞文档

- developerStatus 为 `SUSPENDED` 时，已有应用的读取和运行行为。
- 管理员转让后配额如何转移。

## 迁移说明

服务从未上线，不迁移旧 application 数据，也不维护旧 API 或 MongoDB 文档兼容。旧代码只作为需求证据。

## 变更记录

- 2026-08-22：建立 UC-APP-001。
- 2026-08-23：引入 adminId、开发者资格、名称唯一性、创建配额、createdAt 和 UUID。
- 2026-08-23：当时确认 developerStatus 四状态、名称大小写不敏感，并把 description 作为可空字段；description 的决定已由 2026-09-16 的资料边界取代。version 从 Application 移出，交由独立版本用例。
- 2026-08-23：UC-APP-002 引入持久化技术字段 nextVersionSequence，创建 Application 时初始化为 1；当时的五字段模型已于 2026-09-16 收敛为四字段。
- 2026-09-15：Application ID 确认为 UUIDv7。
- 2026-09-16：Application 收敛为 id、name、adminId、createdAt 四个业务字段；公开 displayName、description、icon 移交后续独立且需审核的 ApplicationProfileRevision。
- 2026-09-16：UC-APP-013 建立 ApplicationProfileRevision，并引入持久化技术字段 nextProfileRevisionSequence；Application 四个业务字段不变。
- 2026-09-19：确认持久化配额记录为唯一权威来源，初始上限为 10；创建路径只在记录不存在时初始化它，不改写已有 limit。
- 2026-09-20：初始配额允许通过 `APP_CENTER_INITIAL_APPLICATION_QUOTA` 配置，默认 10；配置只影响首次建档，已有配额仍是唯一权威。
- 2026-09-20：设计进入 `ACCEPTED`；Domain、UseCase、MongoDB 持久化及事务集成测试达到 `CORE_COMPLETE`，Transport、Composition Root 与端到端验证单独跟踪。
