<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-011 --spec tools/brief-specs/UC-APP-011.json -->
# Brief — UC-APP-011：管理员显式撤销 Tester 加入链接

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-011` 管理员显式撤销 Tester 加入链接 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-TST-029`–`BR-TST-036`（8 条） |
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

> developerStatus 为 `APPROVED` 的当前应用管理员，显式撤销该 Application 的一个 Tester 加入链接，使它不能再创建新的 Tester Membership，同时不创建替代链接，也不影响现有 Tester。

本用例负责：

- 按 `(applicationId, joinLinkId)` 精确定位 TesterJoinLink。
- 把目标 ACTIVE 链接迁移为 `REVOKED`，记录 reason=`MANUAL`、revokedBy 和 revokedAt。
- 对同一个已经 REVOKED 的 joinLinkId 提供幂等结果。
- 确保撤销提交后，使用该链接的新加入请求不能成功。
- 与轮换、加入及管理员转让并发时保持明确顺序。

本用例不负责：

- 创建新的 Tester 加入链接。
- 把显式撤销伪装成一次没有替代链接的轮换。
- 移除现有 Tester Membership 或减少 activeTesterCount。
- 建立用户黑名单。
- 修改 test/grey/stable 发布槽位。
- 通知现有 Tester 或 Auth。
- 删除 TesterJoinLink 历史记录或 tokenHash。

撤销后，Application 可以处于“没有 ACTIVE TesterJoinLink，但仍有 ACTIVE Tester”的合法状态。管理员以后可以通过 UC-APP-008 使用 `expectedActiveJoinLinkId=null` 创建新链接。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
joinLinkId: ApplicationTesterJoinLinkId
```

Command 没有业务字段。status、revocationReason、revokedBy、revokedAt 和 replacedByJoinLinkId 都不能由请求正文指定。

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

按 joinLinkId 操作可以保护新链接：管理员基于旧页面撤销一个已经被轮换的链接时，只会得到旧链接的幂等终态，不会误撤销当前 ACTIVE 链接。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，applicationId 与 joinLinkId 是合法 UUIDv7。
3. Repository 加载撤销候选并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - joinLinkId 属于路径中的 Application。
4. 若目标链接已是 REVOKED，返回原链接和 revoked=false；不读取 Clock，不修改撤销原因，也不影响可能存在的其他 ACTIVE 链接。
5. 从 Clock 取得 revokedAt。
6. Repository 在同一事务或等价原子边界中重新确认当前 admin、链接归属和 ACTIVE 状态，然后写入：
   - status=`REVOKED`
   - revocationReason=`MANUAL`
   - revokedBy=当前 authId
   - revokedAt
   - replacedByJoinLinkId=null
7. 返回更新后的链接和 revoked=true。

本用例不需要读取 Tester Membership、activeTesterCount、ApplicationPublication 或 ApplicationVersion。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- joinLinkId 非法：`InvalidTesterJoinLinkId`。
- Application 不存在，或链接不存在/不属于该 Application：统一返回 `ApplicationTesterJoinLinkNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- ACTIVE 链接包含不应存在的撤销字段，或 REVOKED 链接字段组合非法：`ApplicationTesterJoinLinkStateInconsistent`。
- 时钟或持久化失败：内部失败，链接仍保持原状态。

路径关系不匹配按 NotFound 处理，不泄露其他 Application 的链接状态。

### 最小领域模型

UC-APP-011 扩展 UC-APP-008 已引入的 revocationReason：

```text
ApplicationTesterJoinLink {
  joinLinkId: ApplicationTesterJoinLinkId
  applicationId: ApplicationId
  tokenHash: TesterJoinTokenHash
  status: ACTIVE | REVOKED
  createdBy: AuthId
  createdAt: Instant
  revokedBy: optional AuthId
  revokedAt: optional Instant
  revocationReason: optional ROTATED | MANUAL
  replacedByJoinLinkId: optional ApplicationTesterJoinLinkId
}
```

合法状态组合：

```text
ACTIVE
  revokedBy=null
  revokedAt=null
  revocationReason=null
  replacedByJoinLinkId=null

REVOKED / ROTATED
  revokedBy!=null
  revokedAt!=null
  replacedByJoinLinkId!=null

REVOKED / MANUAL
  revokedBy!=null
  revokedAt!=null
  replacedByJoinLinkId=null
```

### 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ApplicationTesterJoinLinkRepository interface {
    LoadRevocationCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        joinLinkID ApplicationTesterJoinLinkID,
        expectedAdminID AuthID,
    ) (*TesterJoinLinkRevocationCandidate, error)

    Revoke(
        ctx context.Context,
        applicationID ApplicationID,
        joinLinkID ApplicationTesterJoinLinkID,
        expectedAdminID AuthID,
        revokedAt time.Time,
    ) (*RevokeTesterJoinLinkResult, error)
}
```

`Revoke` 必须重新比较 Application.adminId、TesterJoinLink.applicationId/status，并只对目标 ACTIVE joinLinkId 写入 MANUAL 撤销字段。

### 数据模型

UC-APP-011 不新增 collection，复用 `application_tester_join_links`：

| Key | 本用例行为 |
| --- | --- |
| `status` | 从 `ACTIVE` 单向变为 `REVOKED` |
| `revokedBy` | 成功撤销时写当前 admin authId；之后不可修改 |
| `revokedAt` | 成功撤销时写 App Center UTC 时间；之后不可修改 |
| `revocationReason` | 本用例写 `MANUAL` |
| `replacedByJoinLinkId` | MANUAL 时固定为空 |
| `tokenHash` | 保持不变，不对外返回 |

索引与 validator：

- ACTIVE 的四个撤销字段必须全部为空。
- REVOKED 必须具有 revokedBy、revokedAt 和 revocationReason。
- ROTATED 必须具有 replacedByJoinLinkId。
- MANUAL 的 replacedByJoinLinkId 必须为空。
- REVOKED 不能恢复为 ACTIVE，撤销字段不能二次改写。
- partial unique ACTIVE 索引在撤销提交后允许同一 Application 创建新链接。

### API 草图

```text
DELETE /applications/{applicationId}/tester-join-links/{joinLinkId}
Authorization: <authenticated developer identity>
```

首次撤销和幂等重复均返回 `200 OK`：

```json
{
  "revoked": true,
  "joinLink": {
    "joinLinkId": "join-link-uuid",
    "applicationId": "application-uuid",
    "status": "REVOKED",
    "createdBy": "admin-auth-id",
    "createdAt": "2026-09-16T12:00:00Z",
    "revokedBy": "admin-auth-id",
    "revokedAt": "2026-09-16T15:00:00Z",
    "revocationReason": "MANUAL",
    "replacedByJoinLinkId": null
  }
}
```

API 不接受 `createReplacement`、`removeTesters` 或目标状态字段。需要新链接时，管理员随后独立调用 UC-APP-008。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application/TesterJoinLink 不存在或归属不匹配：`404 Not Found`。
- applicationId 或 joinLinkId 格式非法：`400 Bad Request`。
- 链接状态字段不一致：HTTP `500 Internal Server Error` / gRPC `INTERNAL`，稳定 reason 为 `ERROR_REASON_APPLICATION_TESTER_JOIN_LINK_STATE_INCONSISTENT`。沿用已确认的内部数据不变量异常分类，触发不含凭证的服务端告警，不暴露底层存储细节。

### 测试与验收

领域测试：

- ACTIVE 可以迁移为 REVOKED/MANUAL，replacedByJoinLinkId 必须为空。
- REVOKED/ROTATED 的替代关系保持不变，不能改写为 MANUAL。
- REVOKED 不能恢复为 ACTIVE。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以撤销。
- 首次撤销返回 revoked=true；重复撤销返回 revoked=false 且不读取 Clock。
- 对已 ROTATED 旧链接撤销不影响替代链接。
- 撤销不读取或修改 Membership、activeTesterCount 和 Publication。
- 请求不能要求创建替代链接或移除 Tester。

Repository 集成测试：

- 两个并发撤销最多一个写入审计字段。
- 撤销与加入的提交顺序决定加入成功或失败。
- 撤销与轮换同一 ACTIVE 链接时最多一个状态迁移成功。
- 管理员转让与撤销并发时旧 admin 不能成功。
- partial unique ACTIVE 索引在撤销后允许创建新链接。

API 与安全测试：

- 首次与重复撤销都返回 200，并正确区分 revoked。
- 请求不能指定 status、reason、revokedBy、revokedAt 或 replacedByJoinLinkId。
- 响应、日志、trace 和错误详情不包含 secret 或 tokenHash。
- 不存在与归属不匹配使用统一外部错误。

### 实现依赖与交付边界

- UC-APP-008 已交付链接、哈希、历史审计、ACTIVE partial unique index，现有 0009 schema 和领域恢复逻辑已支持 MANUAL；当前不要求新增 collection 或 migration。如确需改变存储约束，新增显式迁移，不修改已交付迁移。
- 复用 UC008/009/010 的 Application `coordinationRevision` 写栅栏。事务内先取得该 Application 的真实写栅栏，再校验当前 admin 和精确目标链接的归属及状态；仅把该 ACTIVE joinLinkId 改为 REVOKED/MANUAL，不读取或改写 Membership 或人数。
- `LoadRevocationCandidate` 的 REVOKED 幂等快捷结果也必须在上述栅栏与一致快照中校验当前 admin；不读取 Clock，不修改业务记录或原审计，仅允许维护 adapter-only 写栅栏。ACTIVE 候选是预检查，最终 `Revoke` 必须重新取得栅栏并复查；若并发轮换/撤销已完成，则返回原终态并丢弃预取时间。
- 使用 snapshot read concern 与 majority write concern，沿用 [UC-APP-009 事务重试协议](../use-cases/UC-APP-009-join-application-as-tester.md#active-tester-计数)。事务重试始终针对原 `(applicationId, joinLinkId)`，不得自动跟随替代关系或选择当前其他 ACTIVE 链接。
- UC-APP-009 已在取得同一写栅栏后最终验证链接，必须通过真实 MongoDB 测试证明撤销/加入和撤销/轮换的双向提交顺序。撤销后现有 Membership 完整保留，UC008 可独立创建新链接。
- 复用可信 DeveloperIdentity、APPROVED 校验、Clock、Proto/Wire 与真实 MongoDB 副本集设施；前端和生产 Gateway 身份签发链路独立交付。
- 不依赖测试发布、Auth Scope Catalog、UC-APP-012 解析，也不实现 Tester 移除、黑名单、替代链接生成或通知。

## 业务规则（UC-APP-011 权威正文）

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-029 -->
### BR-TST-029：撤销权限

撤销者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

普通 Tester、Reviewer 或链接持有人都不能仅凭自身身份撤销链接。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-030 -->
### BR-TST-030：按链接身份定位

撤销目标由 `(applicationId, joinLinkId)` 唯一确定。请求不能表达“撤销当前任意有效链接”，也不能省略 joinLinkId。

旧链接被轮换后会保留原 joinLinkId。对旧 ID 的迟到请求不得作用于 replacedByJoinLinkId 或当前其他 ACTIVE 链接。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-031 -->
### BR-TST-031：MANUAL 撤销终态

ACTIVE 链接成功显式撤销后必须满足：

```text
status = REVOKED
revocationReason = MANUAL
revokedBy = current admin authId
revokedAt = App Center Clock
replacedByJoinLinkId = null
```

MANUAL 表示没有由本操作创建的替代链接。REVOKED 是终态，链接不能恢复为 ACTIVE。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-032 -->
### BR-TST-032：幂等撤销

- ACTIVE 链接首次显式撤销返回 revoked=true。
- 目标链接已经 REVOKED 时返回既有终态和 revoked=false。
- 幂等结果不修改 `ROTATED/MANUAL` 原因、撤销审计或替代关系。
- 幂等返回前仍要确认当前调用者是 Application admin。

因此，对已经 ROTATED 的旧链接调用本用例不会把 reason 改成 MANUAL，也不会撤销其替代链接。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-033 -->
### BR-TST-033：凭证立即失效

撤销事务提交后，目标 joinLinkId 与 secret 的组合不能再创建 Membership。只在事务开始前做缓存校验不够；UC-APP-009 必须在最终加入事务中复查 status=`ACTIVE`。

撤销不要求删除 tokenHash。保留哈希用于验证历史一致性和统一拒绝旧凭证，但不得记录或恢复明文 secret。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-034 -->
### BR-TST-034：并发线性化

- 撤销先提交、加入后提交：加入必须因链接已 REVOKED 而失败。
- 加入先提交、撤销后提交：已创建的 Membership 保留，撤销只阻止后续加入。
- 轮换先提交：旧链接已 ROTATED，本次撤销幂等返回旧终态，新链接保持 ACTIVE。
- 撤销先提交：基于旧 ACTIVE 链接执行的轮换因 expectedActiveJoinLinkId 不再匹配而失败。
- 管理员转让先提交：旧 admin 的撤销失败。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-035 -->
### BR-TST-035：与 Tester Membership 独立

显式撤销链接不得：

- 移除或修改任何 ACTIVE/REMOVED Membership。
- 改变 activeTesterCount。
- 阻止管理员以后创建新链接。
- 为任何 authId 建立黑名单。

现有 Tester 在链接撤销后继续拥有测试资格，直到被 UC-APP-010 单独移除。

<!-- 权威位置: use-cases/UC-APP-011-revoke-tester-join-link.md#br-tst-036 -->
### BR-TST-036：边界、审计与隐私

链接记录不物理删除，createdBy/createdAt/tokenHash 保持不变，撤销字段写入后不可修改。

撤销不得修改 ApplicationPublication、ApplicationVersion、ApplicationReview、Auth 用户或权限，也不自动发送通知。API 响应和日志不能返回 secret 或 tokenHash。

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
8. 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-011`（use-cases/UC-APP-011-revoke-tester-join-link.md）：后续用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-011-revoke-tester-join-link.md` | 339 | `e55e4f0feaf1` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `2595342af7cd` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `4bb4d40a23c8` |
