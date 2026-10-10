# UC-APP-032：修改 Application 技术名称

状态：`SUPERSEDED`

> 撤回说明：评审确认技术名称改名的产品收益不足以覆盖独立 OCC、名称空间竞态、审计和多协议扩散成本。现行规则改为 Application 技术名称创建后不可修改；需要调整用户可见名称时修改 ApplicationProfileRevision.displayName。本提案未生成 brief、未进入实现。

## 目标与范围

> developerStatus 为 `APPROVED` 的当前 Application 管理员，以自己读取到的 nameRevision 为前提，修改仍处于 ACTIVE 生命周期的 Application 技术名称。

本用例只修改 `Application.name` 及其大小写不敏感唯一键。它同时交付：

- 独立于管理权、生命周期和平台可用状态的 `nameRevision`；
- 每次真实改名的不可变审计事件；
- 管理查询和创建响应读取当前 `nameRevision` 的最小协议扩展。

本用例不负责：

- 修改公开 `displayName`、`description` 或 `icon`；这些字段继续属于 ApplicationProfileRevision 及其审核生命周期。
- 修改 Application ID、当前管理员、创建时间、配额、生命周期或平台可用状态。
- 为旧名称建立 URL redirect、alias、保留期或公开搜索入口；所有资源定位继续使用稳定 Application ID。
- 归档、暂停、恢复、关闭或转让 Application。
- 提供名称变更历史查询 API；首版只保存审计事实并返回当前名称状态。

## 旧实现观察

旧服务在 `UpdateApplicationName` 中允许管理员修改 Application 技术名称。

### KEEP

- 只有当前管理员可以改名。
- 新名称继续满足创建 Application 时的技术名称规则。
- 同一管理员名下不能出现重复技术名称。

### CHANGE

- 复用 [BR-APP-003](../use-cases/UC-APP-001-create-application.md#br-app-003) 的 ASCII 字段和大小写不敏感唯一性语义。
- 使用独立 `nameRevision` 做乐观并发控制，拒绝静默覆盖。
- 当前管理员、ACTIVE 生命周期、revision、名称唯一性、Application 更新和审计事件在同一本地原子边界内复查并提交。
- 与管理员转让、关闭及其他管理员写操作共用 Application coordination fence。
- 精确相同名称是 no-op；只改变大小写是可见的真实改名。

### DROP

- 无条件 last-write-wins 更新。
- 依赖旧名称作为路由、资源身份或 OAuth client 身份。
- 改名时隐式修改公开资料、发布槽位、Version、Tester、Filter 或 OAuth 配置。

## 输入、身份与读取来源

路径参数：

```text
applicationId: ApplicationId
```

Command：

```text
RenameApplicationCommand {
  expectedNameRevision: int64
  name: string
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

`expectedNameRevision` 来自 `CreateApplication` 响应或 [UC-APP-029](../use-cases/UC-APP-029-query-owned-application-management.md) 的 `OwnedApplicationCore.nameRevision`。HTTP adapter 从 `If-Match` 读取它；原生 gRPC request 字段表达同一语义。请求正文不能指定 adminId、revision 或审计字段。

只有 developerStatus=`APPROVED` 且 `authId` 等于当前 `Application.adminId` 的调用者可以改名。Application 必须仍为 `ACTIVE`；`CLOSING/CLOSED` 不可修改。`platformAvailabilityStatus=SUSPENDED` 不阻止改名，因为平台 suspension 保留管理员修复和整理配置的能力。

## 命令语义与并发

`nameRevision` 是技术名称自己的业务 OCC，从 1 开始：

- 创建 Application 时初始化为 1；既有记录由迁移回填为 1。
- 客户端必须提交自己读取到的正数 expectedNameRevision。
- expectedNameRevision 不匹配时，即使请求名称恰好等于当前名称，也返回冲突。
- revision 匹配且新名称与当前 `name` 逐字节完全相同时是 no-op：返回 `changed=false`，不生成 ID、时间或审计事件，也不推进任何 revision。
- 大小写变化属于真实改名。例如 `Course_App` 改为 `course_app` 时，虽然 `nameKey` 不变，仍推进 nameRevision 并记录事件。
- 其他真实变化成功时，nameRevision 精确增加 1；溢出失败关闭。

名称比较只使用 BR-APP-003 已定义的 ASCII 规则。服务端不 trim、不做 Unicode 规范化，也不把 lowercase key 当作返回名称。

## 主流程

1. 从可信身份取得 authId 和 developerStatus，确认 developerStatus=`APPROVED`。
2. 校验 applicationId、正数 expectedNameRevision，并按 BR-APP-003 校验新 name，计算 ASCII lowercase `nameKey`。
3. 读取当前 Application，确认存在、adminId 等于 authId、lifecycleStatus=`ACTIVE`，并精确匹配 nameRevision。
4. 若新 name 与当前 name 逐字节相同，返回当前名称资源和 `changed=false`；本次命令在线性化读取点成立，不产生写入。
5. 为真实变化生成 UUIDv7 nameChangeEventId，并从 App Center 时钟取得 UTC changedAt。
6. 在一个 MongoDB 事务中取得 Application coordination fence，并重新检查：
   - Application 仍存在且 lifecycleStatus=`ACTIVE`；
   - adminId 仍等于调用者 authId；
   - nameRevision 仍等于 expectedNameRevision；
   - `(adminId, newNameKey)` 没有被另一 Application 占用。
7. 在同一事务中：
   - 更新 Application.name 与 nameKey；
   - nameRevision 增加 1；
   - 插入不可变 ApplicationNameChangeEvent，记录前后名称/revision、操作者和时间。
8. 提交确定后返回 `changed=true`、当前 name、递增后的 nameRevision，并以新 revision 作为 HTTP ETag。

本流程不调用 Auth、Profile、Publication、Scope Catalog、URL preflight、OAuth 或通知服务。Developer 资格来自当前可信身份；与管理员转让或关闭的最终权限竞态由本地 Application 事务复查和共享写栅栏处理。

## 异常流程

- 缺少或损坏的可信身份：沿用 `DeveloperIdentityRequired` / `InvalidDeveloperIdentity`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- name 不符合 BR-APP-003：`InvalidApplicationName`。
- expectedNameRevision 缺失、非正数或 HTTP `If-Match` 非法：`ApplicationNameRevisionRequired`。
- Application 不存在：`ApplicationNotFound`。
- 调用者不是当前管理员：`ApplicationAdminRequired`。
- Application 为 `CLOSING/CLOSED`：`ApplicationNotActive`。
- 当前 nameRevision 不等于 expectedNameRevision：`ApplicationNameRevisionConflict`。
- 同一当前管理员名下已有大小写等价名称：沿用 `ApplicationNameAlreadyExists`。
- nameRevision 溢出、ID/Clock、事务、存储或持久状态损坏：内部失败，不返回部分结果。

所有失败都不得改变 name/nameKey/nameRevision、写入孤立审计事件或影响任何依附能力。

## 业务规则

<a id="br-app-044"></a>
### BR-APP-044：技术名称与稳定身份分离

Application.name 继续遵守 BR-APP-003，是供开发者管理和识别的技术名称，不是公开 displayName。改名不改变稳定 Application ID；API 路径、Version/Profile/Publication/Tester/OAuth/Filter 归属均继续使用 applicationId，旧名称不形成 alias 或重定向。

<a id="br-app-045"></a>
### BR-APP-045：改名权限与生命周期

只有 developerStatus=`APPROVED` 的当前 Application admin 可以改名。Application 必须为 `ACTIVE`；CLOSING/CLOSED 禁止管理写入。平台 `SUSPENDED` 与技术名称编辑正交，不阻止当前管理员改名，也不会因改名自动恢复平台可用性。

<a id="br-app-046"></a>
### BR-APP-046：独立 nameRevision 与 no-op

nameRevision 是正数且只跟踪技术名称真实变化，不复用 ownershipRevision、lifecycleRevision、platformAvailabilityRevision 或 adapter-only coordinationRevision。创建与历史回填值为 1；每次真实改名增加 1。命令必须先匹配 expectedNameRevision；精确同名是无副作用 no-op，大小写变化是真实改名。

<a id="br-app-047"></a>
### BR-APP-047：当前管理员名称空间唯一性

真实改名后，`(adminId, ASCII-lowercase(name))` 必须唯一。名称占用以事务提交时的当前 adminId 为准，不预留旧名称或新名称，也不跨管理员建立全局唯一性。改名成功后旧 nameKey 立即可被同一管理员的其他 ACTIVE Application 使用；CLOSED Application 的名称仍按 [BR-APP-025](../use-cases/UC-APP-027-close-application.md#br-app-025) 永久保留，不因本用例释放。

<a id="br-app-048"></a>
### BR-APP-048：共享写栅栏与原子改名

真实改名必须在一个本地事务中取得 Application coordination fence，复查 admin/lifecycle/nameRevision/名称唯一性，并原子更新 Application 与插入审计事件。它与管理员转让、关闭及其他管理员写操作的并发结果必须等价于明确先后顺序：转让先提交则旧管理员失败；改名先提交则转让按新 nameKey 检查目标名称空间；关闭先提交则改名失败。

<a id="br-app-049"></a>
### BR-APP-049：不可变名称变更审计

每次真实改名创建一个不可变 ApplicationNameChangeEvent，保存 applicationId、previousName/newName、previousNameRevision/nameRevision、changedBy 和 changedAt。事件不作为当前名称的读取权威，不允许覆盖或删除；no-op 不创建事件。普通日志、错误和 trace 不记录前后名称，避免高基数输入扩散，审计查询 API 留待后续设计。

<a id="br-app-050"></a>
### BR-APP-050：影响边界与管理读取

改名只改变 Application.name/nameKey/nameRevision 和名称审计；不得修改 Profile displayName、Version/Profile/Review、Publication、Filter、Tester、OAuth、配额、管理员、生命周期或平台可用状态。CreateApplication 成功结果和 UC-APP-029 的 OwnedApplicationCore 必须返回当前 nameRevision；管理响应继续使用 `private, no-store`，但不返回名称历史。

## 最小领域与数据模型变化

```text
Application {
  id
  name
  nameRevision
  adminId
  ownershipRevision
  lifecycleStatus
  lifecycleRevision
  platformAvailabilityStatus
  platformAvailabilityRevision
  createdAt
}

ApplicationNameChangeEvent {
  nameChangeEventId
  applicationId
  previousName
  newName
  previousNameRevision
  nameRevision
  changedBy
  changedAt
}
```

`nameKey` 和 `coordinationRevision` 仍是 Mongo adapter 技术字段，不进入 Domain 或 API。ApplicationNameChangeEvent 是追加式业务审计，不是独立可变聚合。

### applications 变化

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `nameRevision` | 技术名称 OCC | int64 | `>= 1`，创建/回填为 1 | no | no |

现有 `(adminId, nameKey)` 唯一索引继续承担最终名称冲突保护。真实改名对 Application 文档同时设置 name/nameKey，并原子增加 nameRevision 与 coordinationRevision。

### application_name_change_events

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `nameChangeEventId` | 名称变更事件 ID | string | UUIDv7 | yes | no |
| `applicationId` | Application ID | string | UUIDv7 | `(applicationId, nameRevision)` | no |
| `previousName` | 变更前技术名称 | string | BR-APP-003 | no | no |
| `newName` | 变更后技术名称 | string | BR-APP-003 | no | no |
| `previousNameRevision` | 变更前 revision | int64 | `>= 1` | no | no |
| `nameRevision` | 变更后 revision | int64 | `previousNameRevision + 1` | `(applicationId, nameRevision)` | no |
| `changedBy` | 执行改名的 authId | string | opaque authId | no | no |
| `changedAt` | 提交使用的业务时间 | datetime | UTC / RFC 3339 | no | no |

唯一索引包括 nameChangeEventId 和 `(applicationId, nameRevision)`。Mongo validator 固定字段完整性、正数 revision 和名称格式；Domain/Repository 负责校验 `nameRevision = previousNameRevision + 1`，事件唯一索引和同事务写入负责阻止重复 revision 审计。

## 用例端口草图

```go
type ApplicationNameChangeIDGenerator interface {
    NewUUIDv7() (ApplicationNameChangeEventID, error)
}

type Clock interface {
    Now() time.Time
}

type ApplicationNameRepository interface {
    LoadRenameCandidate(
        context.Context,
        ApplicationID,
        AuthID,
    ) (*ApplicationNameCandidate, error)

    Rename(
        context.Context,
        ApplicationNameCandidate,
        ApplicationName,
        int64,
        ApplicationNameChangeEventID,
        time.Time,
    ) (*RenameApplicationResult, error)
}
```

`LoadRenameCandidate` 支持在生成 ID/时间前识别有效 no-op；`Rename` 不能信任旧 candidate 的授权结论，必须在事务内重新检查全部提交条件。实现可以收窄具体签名，但不得把 Mongo/Proto 类型带入 Domain/UseCase，也不得为 no-op 生成审计材料。

## API 草图

在现有 `app_center.v1.application.Application` service 增加：

```text
rpc RenameApplication(RenameApplicationRequest)
  PUT /v1/applications/{application_id}/name body=replacement

RenameApplicationRequest {
  application_id
  expected_name_revision
  replacement: ApplicationNameReplacement { name }
}
```

HTTP：

```text
PUT /v1/applications/{applicationId}/name
If-Match: "3"
Content-Type: application/json

{
  "name": "Course_Table_V2"
}
```

Native gRPC 的 `RenameApplicationRequest.expected_name_revision` 表达同一 OCC；HTTP 请求正文只绑定 `command`，不能覆盖 header revision。成功返回 `200 OK`：

```json
{
  "changed": true,
  "applicationId": "application-uuid",
  "name": "Course_Table_V2",
  "nameRevision": "4"
}
```

HTTP 同时返回 `ETag: "4"`。no-op 返回 `changed=false` 和未变化的 ETag。

协议还以向后兼容的新字段扩展：

- `CreateApplicationResponse.name_revision`，创建成功固定为 1；
- `OwnedApplicationCore.name_revision`，供 UC-APP-029 列表和详情取得当前改名 OCC。

建议错误映射：

| 情况 | HTTP / gRPC | 稳定 reason |
| --- | --- | --- |
| ID/name 非法 | 400 / INVALID_ARGUMENT | `INVALID_APPLICATION_ID`、`INVALID_APPLICATION_NAME` |
| HTTP 缺少 If-Match | 428 / INVALID_ARGUMENT | `APPLICATION_NAME_REVISION_REQUIRED` |
| 非法 If-Match 或 gRPC expected revision | 400 / INVALID_ARGUMENT | `APPLICATION_NAME_REVISION_REQUIRED` |
| 身份缺失或损坏 | 401 / UNAUTHENTICATED | 复用现有 identity reason |
| Developer 未批准 | 403 / PERMISSION_DENIED | `DEVELOPER_APPROVAL_REQUIRED` |
| Application 不存在 | 404 / NOT_FOUND | `APPLICATION_NOT_FOUND` |
| 非当前管理员 | 403 / PERMISSION_DENIED | `APPLICATION_ADMIN_REQUIRED` |
| CLOSING/CLOSED | 409 / FAILED_PRECONDITION | `APPLICATION_NOT_ACTIVE` |
| 名称已占用 | 409 / ALREADY_EXISTS | `APPLICATION_NAME_ALREADY_EXISTS` |
| nameRevision 漂移 | 412 / ABORTED | `APPLICATION_NAME_REVISION_CONFLICT` |
| 数据损坏或基础设施失败 | 500 / INTERNAL | `INTERNAL` |

错误 body、日志和 trace 不回显冲突 Application、旧名称或候选名称。

## 验收场景

### Domain / UseCase

1. name 完整复用 BR-APP-003 的长度、字符、大小写保留与 lowercase key 规则。
2. 只有 APPROVED 当前 admin 可以改名；普通认证用户、旧管理员和非 APPROVED Developer 被拒绝。
3. ACTIVE＋AVAILABLE 与 ACTIVE＋SUSPENDED 都允许改名；CLOSING/CLOSED 均拒绝。
4. expectedNameRevision 必须先匹配；过期请求即使名称与当前值相同也冲突。
5. 精确同名返回无 ID/Clock/Repository commit 的 no-op；case-only 变化是真实修改。
6. 真实变化增加 nameRevision 并产生完整审计；其他业务 revision 不变。

### MongoDB integration

7. 同一 adminId 下大小写等价名称只有一个 Application 可以提交；不同管理员仍可同名。
8. 名称冲突、审计插入失败或事务失败时 Application 和事件均不留下部分结果。
9. 两个携带相同 expected revision 的并发真实改名最多一个成功。
10. 改名与管理员转让竞争满足 BR-APP-048：目标名称检查使用线性化后的 nameKey，旧管理员不能越权提交。
11. 改名与关闭竞争最多按一种明确顺序生效；CLOSING 后不再接受改名。
12. case-only 改名保持 nameKey 但增加 revision；改为其他 key 后旧 key 可由同管理员另一 ACTIVE Application 使用。
13. migration 为既有 Application 回填 nameRevision=1，fresh/sequential/idempotent 一致，validator/index 拒绝损坏事件。

### API / E2E

14. Create 与 UC029 管理查询返回 nameRevision；rename 成功和 no-op 返回正确 ETag。
15. HTTP If-Match 与 native gRPC expected_name_revision 具有相同错误和 OCC 语义；body 不能覆盖 revision、admin 或审计字段。
16. 响应和错误使用 `Cache-Control: private, no-store`；遥测不记录名称。
17. 改名后 UC029 立即返回新名称；公开 Catalog 仍返回 Profile displayName，运行解析结果不发生变化。
18. `make check-full` 在冻结的最终服务/API 输入上通过；本 UC 不需要新的 Auth 接口，除非实现实际改变共享 Auth 契约。

## 实现依赖与交付边界

依赖已经接受的 UC-APP-001 名称规则、UC-APP-026 ownership/shared fence、UC-APP-027 lifecycle、UC-APP-028 platform availability 和 UC-APP-029 管理读取。不新增 ADR 或跨服务契约。

实现工作包预计包含：

- Application Domain/UseCase/Port 的 nameRevision 与 rename 行为；
- API Proto、HTTP/gRPC transport、稳定错误 reason 和 ETag/If-Match；
- Mongo migration `0026_application_name_rename`、事件 collection、validator/index 与事务 repository；
- Create/management query 的 nameRevision 投影扩展；
- Wire、单元测试、Mongo integration 和真实 HTTP/gRPC E2E。

实现不得顺带加入 archive/unarchive、版本查询、草稿放弃、Test clear、Tester 列表或名称历史查询。设计接受后才能创建 brief spec、生成 brief 并开始实现。

## 审核要点

- 是否接受独立 `nameRevision`，而不是复用 ownershipRevision 或建立笼统 Application revision。
- 是否接受精确同名 no-op、case-only 真实改名。
- 是否接受 ACTIVE＋SUSPENDED 仍可改名，CLOSING/CLOSED 禁止。
- 是否需要首版保存不可变名称变更事件；本提案保存事实但不开放历史查询。
- 是否接受旧名称立即释放且不建立 alias/保留期；CLOSED Application 名称仍永久保留。

## 变更记录

- 2026-10-10：建立 UC-APP-032 提案；采用独立 nameRevision、共享 Application 写栅栏、大小写敏感 no-op 判断和追加式改名审计。
- 2026-10-10：产品评审撤回改名能力；技术名称由 BR-APP-003 明确为创建后不可修改，UC-APP-032 归档且未实现。
