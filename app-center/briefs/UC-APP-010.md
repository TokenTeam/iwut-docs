<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-010 --spec tools/brief-specs/UC-APP-010.json -->
# Brief — UC-APP-010：管理员移除 Application Tester

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-010` 管理员移除 Application Tester |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-TST-020`–`BR-TST-028`（9 条） |
| 外部引用 BR | — |
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

> developerStatus 为 `APPROVED` 的当前应用管理员，按 membershipId 移除该 Application 中一个当前 ACTIVE Tester Membership episode，并原子释放一个 Tester 名额。

本用例负责：

- 验证调用者仍是 Application 当前 admin。
- 精确定位所属 Application 下的一次 Membership episode。
- 把 ACTIVE episode 迁移为 REMOVED，记录 removedBy 和 removedAt。
- 原子减少 activeTesterCount。
- 对同一个已经 REMOVED 的 membershipId 提供幂等结果。
- 返回移除完成时是否仍存在 ACTIVE TesterJoinLink，供管理界面显示重新加入警告。

本用例不负责：

- 撤销、轮换或删除 Tester 加入链接。
- 把用户加入黑名单或阻止未来重新加入。
- 删除 Membership 历史记录。
- 按 authId 批量移除所有历史 episode。
- 修改 test/grey/stable 槽位或 ApplicationVersion。
- 通过 Auth 撤销权限、developerStatus 或用户身份。
- 向被移除用户发送通知。
- 允许 Tester 主动退出；那是独立的未来用例。

如果仍存在有效加入链接，管理界面可以在执行前警告：“该用户仍可通过有效的测试加入链接再次加入。”这个提示不构成确认步骤，也不会把移除与链接撤销组合成一个命令。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
membershipId: ApplicationTesterMembershipId
```

Command 没有业务字段。目标用户、status、removedBy、removedAt 和 activeTesterCount 都不能由请求正文指定。

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

按 membershipId 操作而不是按 testerAuthId 操作，可以确保对旧 episode 的重复请求不会误删该用户后来重新加入所产生的新 ACTIVE episode。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，applicationId 和 membershipId 是合法 UUIDv7。
3. Repository 加载移除候选并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - membershipId 属于路径中的 Application。
4. 若目标 episode 已是 REMOVED，返回原 Membership、removed=false、当前 activeTesterCount 和当前是否存在 ACTIVE TesterJoinLink；不读取 Clock，不改变 Membership、审计或其他业务记录；允许维护 adapter-only 写栅栏。
5. 从 Clock 取得 removedAt。
6. Repository 在同一事务或等价原子边界中重新确认当前 admin、Membership 归属和状态，然后：
   - 把 status 从 ACTIVE 改为 REMOVED。
   - 写入 removedBy=当前 authId、removedAt。
   - 将 activeTesterCount 减少 1。
7. 返回更新后的 Membership、removed=true、结果 activeTesterCount，以及提交时是否存在 ACTIVE TesterJoinLink。

ACTIVE TesterJoinLink 的存在性只是提示快照，不是移除前置条件。链接在操作前后发生轮换或撤销，不影响 Membership 移除是否成功。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- membershipId 非法：`InvalidTesterMembershipId`。
- Application 不存在，或 Membership 不存在/不属于该 Application：统一返回 `ApplicationTesterMembershipNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- ACTIVE Membership 存在但 activeTesterCount 已为 0，或计数与状态无法一致提交：`ApplicationTesterStateInconsistent`。
- 时钟或持久化失败：内部失败，不改变 Membership 或计数。

路径关系不匹配按 NotFound 处理，不泄露其他 Application 的 Tester 信息。

### 最小领域模型

UC-APP-010 完成 UC-APP-009 已引入的 Membership 生命周期：

```text
ApplicationTesterMembership {
  membershipId: ApplicationTesterMembershipId
  applicationId: ApplicationId
  testerAuthId: AuthId
  status: ACTIVE | REMOVED
  joinedViaJoinLinkId: ApplicationTesterJoinLinkId
  joinedAt: Instant
  removedBy: optional AuthId
  removedAt: optional Instant
}
```

合法状态组合：

```text
ACTIVE  -> removedBy=null, removedAt=null
REMOVED -> removedBy!=null, removedAt!=null
```

REMOVED 是该 episode 的终态。当前模型不保存 removalReason，因为移除行为没有要求管理员填写理由。

### 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ApplicationTesterMembershipRepository interface {
    LoadRemovalCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        membershipID ApplicationTesterMembershipID,
        expectedAdminID AuthID,
    ) (*TesterRemovalCandidate, error)

    Remove(
        ctx context.Context,
        applicationID ApplicationID,
        membershipID ApplicationTesterMembershipID,
        expectedAdminID AuthID,
        removedAt time.Time,
    ) (*RemoveApplicationTesterResult, error)
}
```

`Remove` 必须重新比较 Application.adminId、Membership.applicationId/status 和 activeTesterCount，并在同一原子边界写 REMOVED 与计数。结果中的 activeJoinLinkExists 是提交时的提示快照，不参与事务成败判断。

### 数据模型

UC-APP-010 不新增 collection，复用 `application_tester_memberships`：

| Key | 本用例行为 |
| --- | --- |
| `status` | 从 `ACTIVE` 单向变为 `REMOVED` |
| `removedBy` | 成功移除时写当前 admin authId；之后不可修改 |
| `removedAt` | 成功移除时写 App Center UTC 时间；之后不可修改 |
| `joinedViaJoinLinkId` | 保持不变 |
| `joinedAt` | 保持不变 |

存储约束：

- REMOVED 必须同时具有 removedBy 和 removedAt。
- REMOVED 不能恢复为 ACTIVE。
- partial unique ACTIVE 索引在状态迁移后释放 `(applicationId, testerAuthId)`，允许重新加入创建新 episode。
- Membership 状态迁移与 activeTesterCount 减少必须原子提交。
- 历史查询索引继续保留 REMOVED episode。

### API 草图

```text
DELETE /applications/{applicationId}/tester-memberships/{membershipId}
Authorization: <authenticated developer identity>
```

首次移除和幂等重复均返回 `200 OK`：

```json
{
  "removed": true,
  "membership": {
    "membershipId": "membership-uuid",
    "applicationId": "application-uuid",
    "testerAuthId": "tester-auth-id",
    "status": "REMOVED",
    "joinedViaJoinLinkId": "join-link-uuid",
    "joinedAt": "2026-09-16T13:00:00Z",
    "removedBy": "admin-auth-id",
    "removedAt": "2026-09-16T14:00:00Z"
  },
  "capacity": {
    "activeTesterCount": 16,
    "testerLimit": 100
  },
  "activeJoinLinkExists": true
}
```

当 activeJoinLinkExists=true 时，管理界面显示重新加入警告。API 不要求 `confirm` 或 `revokeJoinLink` 参数。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application/Membership 不存在或归属不匹配：`404 Not Found`。
- applicationId 或 membershipId 格式非法：`400 Bad Request`。
- Membership 与计数状态不一致：HTTP `500 Internal Server Error` / gRPC `INTERNAL`，稳定 reason 为 `ERROR_REASON_APPLICATION_TESTER_STATE_INCONSISTENT`；该错误属于内部数据不变量异常，并触发服务端告警，不向客户端暴露底层数据或存储细节。

### 测试与验收

领域测试：

- ACTIVE 可以迁移为 REMOVED，并写入 removedBy/removedAt。
- REMOVED 不能恢复为 ACTIVE，加入字段保持不变。
- 没有 removalReason，也没有 blacklist 状态。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以移除。
- admin 可以移除自己的 Tester Membership。
- 首次移除返回 removed=true；重复移除返回 removed=false 且不读取 Clock。
- membershipId 归属不匹配按 NotFound 处理。
- activeJoinLinkExists 只影响响应提示，不影响移除结果。
- 请求不能要求同时撤销链接。

Repository 集成测试：

- Membership 状态与 activeTesterCount 原子更新。
- 同一 Membership 并发移除只减少一次计数。
- 对旧 REMOVED episode 的重复删除不影响后来重新加入的新 episode。
- 移除与重新加入并发结果满足明确线性化顺序。
- 管理员转让与移除并发时旧 admin 不能成功。
- activeTesterCount 为 0 但 Membership 为 ACTIVE 时拒绝提交并报告不一致。

API 测试：

- 首次和重复移除都返回 200，并正确区分 removed。
- 请求不能指定 testerAuthId、status、removedBy、removedAt 或计数。
- 响应在存在 ACTIVE 加入链接时返回 activeJoinLinkExists=true。
- API 不接受组合撤销链接参数。

### 实现依赖与交付边界

- UC-APP-009 已交付 Membership episode、ACTIVE/REMOVED schema、0010 migration、partial unique index 与事务内人数统计；复用现有可信 DeveloperIdentity、Clock、Proto/Wire 和 MongoDB 副本集设施。
- activeTesterCount 继续由同一事务内的 ACTIVE Membership 统计得到，不另建持久化计数器；ACTIVE → REMOVED 的提交本身令统计结果减少 1。事务重试协议沿用 [UC-APP-009 ACTIVE Tester 计数](../use-cases/UC-APP-009-join-application-as-tester.md#active-tester-计数)。
- 复用 UC-APP-008/009 的 Application `coordinationRevision` 写栅栏：先取得栅栏，再校验当前管理员、Membership 归属/状态并读取人数与 ACTIVE 链接存在性；首次移除在同一 snapshot/majority 事务内更新状态和审计，返回更新后的统计结果。
- `LoadRemovalCandidate` 若直接产生 REMOVED 幂等结果，也在上述栅栏和一致快照中验证当前管理员、读取 count 与 activeJoinLinkExists；该分支不读取 Clock，不改写业务记录。ACTIVE 候选只供预检查，最终 `Remove` 必须重新取得栅栏并复查；并发移除已完成时返回原终态并丢弃预取时间。
- activeJoinLinkExists 的真假不影响移除资格，也不导致链接写入；共享栅栏只提供串行化及提示快照，不把移除与链接轮换/撤销组合成一个业务命令。
- `ApplicationTesterStateInconsistent` 固定为内部错误；保留人数范围及 ACTIVE episode 对应正数人数的防御校验。真实存储从同一快照统计时不另造计数漂移；无法通过合法存储构造的矛盾输入在领域/端口异常测试验证，MongoDB 测试验证真实统计、回滚及并发线性化。
- 当前 schema 已能承载移除，不要求为了 UC 编号新增 migration；如实现发现必须改变 schema，则新增显式 migration，不修改已交付迁移。
- Tester 管理查询字段/分页、前端警告及生产 Gateway 身份签发链路独立交付，不阻塞本用例命令；当前不实现列表查询、黑名单、主动退出、UC-APP-011 撤销或 UC-APP-012 解析。

## 业务规则（UC-APP-010 权威正文）

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-020 -->
### BR-TST-020：移除权限

移除者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

管理员可以移除自己的 Tester Membership；管理员身份与 Tester 资格相互独立。Reviewer 或普通 Tester 不因其他身份获得移除权限。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-021 -->
### BR-TST-021：按 Membership episode 定位

移除目标由 `(applicationId, membershipId)` 唯一确定。membershipId 必须属于该 Application；请求不能用 testerAuthId 代替。

同一用户重新加入会取得新的 membershipId。对旧 REMOVED membershipId 的迟到或重复请求不得影响新的 ACTIVE episode。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-022 -->
### BR-TST-022：幂等移除

- ACTIVE episode 首次成功移除时返回 removed=true。
- 同一 membershipId 已经 REMOVED 时返回原终态和 removed=false。
- 幂等结果不改写 removedBy/removedAt，不再次减少计数，也不创建新的审计记录。
- 幂等返回前仍要确认当前调用者是 Application admin，不能把旧 Membership 当作公开查询入口。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-023 -->
### BR-TST-023：REMOVED 终态与审计

成功移除必须记录：

```text
status = REMOVED
removedBy = current admin authId
removedAt = App Center Clock
```

joinedViaJoinLinkId 和 joinedAt 保持不变。REMOVED episode 不恢复为 ACTIVE、不物理删除；用户再次加入时创建新的 episode。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-024 -->
### BR-TST-024：原子释放容量

Membership 的 `ACTIVE -> REMOVED` 与 activeTesterCount `-1` 必须全部成功或全部失败。

- activeTesterCount 不能小于 0。
- 幂等移除不改变计数。
- 成功释放的名额可以被后续有效加入使用。
- 每个 Application 的 ACTIVE Tester 上限仍固定为 100。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-025 -->
### BR-TST-025：不建立黑名单

移除只终止当前 Membership episode，不表示封禁 authId。被移除用户只要取得当前有效加入链接，且 ACTIVE Tester 数量小于 100，就可以重新加入。

若未来需要禁止特定用户再次加入，必须引入明确的封禁/黑名单用例、权限、期限和申诉规则，不能改变本用例语义。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-026 -->
### BR-TST-026：加入链接独立

移除 Membership 不得撤销、轮换或删除任何 TesterJoinLink。链接是否 ACTIVE 不影响移除能否执行。

Repository 返回的 activeJoinLinkExists 只用于界面提示。提示不要求管理员确认，也不能把两个动作包装为一个领域命令。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-027 -->
### BR-TST-027：并发线性化

- 两个并发移除请求最多一个执行状态迁移和计数减少；另一个安全返回幂等结果或在冲突后重读。
- 移除与同一用户重新加入并发时，结果必须等价于某个明确顺序：加入先发生则本次移除该 ACTIVE episode；移除先发生则持有效链接的用户可以创建新的 episode。
- 管理员转让与移除并发时，旧 admin 不能在转让提交后成功移除。
- 链接轮换/撤销与移除相互独立，不需要跨两个生命周期建立联合事务。

<!-- 权威位置: use-cases/UC-APP-010-remove-application-tester.md#br-tst-028 -->
### BR-TST-028：边界与隐私

移除 Tester 不得：

- 修改 ApplicationPublication、ApplicationVersion 或 ApplicationReview。
- 修改 Auth 用户、Developer 状态或权限。
- 返回其他 Tester 的列表或个人资料。
- 删除加入来源、加入时间或其他 Membership 审计事实。
- 自动发送通知。

App Center 只保存和返回完成本操作所需的 opaque authId 与 Membership 审计字段。

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
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
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

- `UC-APP-010`（use-cases/UC-APP-010-remove-application-tester.md）：后续用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-010-remove-application-tester.md` | 337 | `4804d0a44f36` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `cfaa02fcbb8c` |
