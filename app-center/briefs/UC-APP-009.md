<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-009 --spec tools/brief-specs/UC-APP-009.json -->
# Brief — UC-APP-009：通过有效链接加入 Application Tester 列表

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-009` 通过有效链接加入 Application Tester 列表 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-TST-010`–`BR-TST-019`（10 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/tester-join-url-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

> 一个已登录用户使用仍然有效的 Tester 加入链接，自助取得整个 Application 的 Tester Membership；加入时不要求 Developer 资格，并受到 Application 级 Tester 数量上限约束。

本用例负责：

- 使用可信身份中的 authId 作为 Tester 身份。
- 验证 joinLinkId、secret、链接状态及其所属 Application。
- 在 Application Tester 上限内创建一个 ACTIVE Membership。
- 对已经是 ACTIVE Tester 的相同用户提供幂等结果。
- 允许曾被移除的用户持有效链接重新加入，并创建新的 Membership episode。
- 在链接轮换、并发加入和容量竞争下保持链接、唯一性及上限一致。

本用例不负责：

- 要求或检查 developerStatus。
- 由 admin 指定目标用户或审批加入申请。
- 发送 Auth 消息或保存 Auth 权限。
- 创建、轮换或撤销 Tester 加入链接。
- 移除 Tester 或建立黑名单。
- 自动把 Application admin 加入 Tester 列表。
- 选择 test Version、检查 rpcApiVersion/capabilities 或改变发布槽位。
- 要求 Application 已经存在 test 槽位。

扫码、点击链接和深链跳转只是取得 joinLinkId 与 secret 的入口交互。前端扫码后使用当前用户的登录认证凭证发起本用例的加入请求；扫码与加入的职责边界见 [UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#前端扫码与加入边界)。真正的 Tester 资格只在本用例成功提交 Membership 后成立。

### 业务边界

Tester Membership 属于整个 Application：

```text
Application
  ├─ one ACTIVE TesterJoinLink
  └─ bounded ACTIVE Tester Memberships
       ├─ authId A
       ├─ authId B
       └─ authId C
```

Membership 不记录 rpcApiMajor、Version 或 Publication。用户运行应用时，后续解析用例根据其客户端实际 rpcApiVersion、capabilities 和当前 Publication 选择 test Version。

加入链接是 bearer credential：任何已登录用户取得有效 secret 后都可以申请加入。当前模型没有定向邀请、审批或黑名单，因此不能把二维码的实际持有人视为管理员预先指定的人。

### 输入与身份

路径参数：

```text
joinLinkId: ApplicationTesterJoinLinkId
```

Command：

```text
JoinApplicationAsTesterCommand {
  secret: string
}
```

可信身份：

```text
AuthenticatedUserIdentity {
  authId: string
}
```

authId 只能来自已认证上下文，不能由路径、二维码或请求正文指定。调用者不需要是 Developer，也不需要是 Application admin；admin 若希望测试，同样以自己的 authId 执行本用例。

secret 必须是由 UC-APP-008 生成的 32-byte 无填充 base64url 值。入口层必须把它视为敏感字段并禁止日志记录。

### 主流程

1. 从可信身份上下文取得 authId。
2. 校验 joinLinkId 为 UUIDv7，secret 是可以解码为恰好 32 bytes 的无填充 base64url。
3. 解码 secret，对得到的 32 个原始 bytes 计算 SHA-256 tokenHash；原始 secret 不再进入领域对象或 Repository 参数。
4. Repository 初步验证 joinLinkId、tokenHash 和 ACTIVE 状态，取得 applicationId；该结果只是候选，不能替代最终事务复查。
5. 使用固定的 Application Tester 上限 100。
6. 为可能的新 Membership 生成 UUIDv7 membershipId，并从 Clock 取得 joinedAt。
7. Repository 在一个事务或等价原子边界中：
   - 按 joinLinkId 加载链接，使用常量时间比较 tokenHash。
   - 确认链接仍为 ACTIVE，并取得 applicationId。
   - 确认 Application 仍存在。
   - 若 `(applicationId, authId)` 已有 ACTIVE Membership，返回该记录和 joined=false，不占用新名额，也不写新记录。
   - 否则计算当前 ACTIVE Tester 数量，并确认小于上限。
   - 创建新的 ACTIVE Membership episode，记录 joinedViaJoinLinkId 和 joinedAt。
8. 返回 Membership、joined 标记及成功后的 activeTesterCount/limit。

如果结果 joined=false，步骤 6 预生成的 ID 和时间必须丢弃。实现可以在确认不是幂等结果后再生成，但最终事务仍必须重新验证链接和容量。

### 异常流程

- 缺少身份或 authId：`AuthenticatedUserRequired`。
- joinLinkId 格式非法：`InvalidTesterJoinLinkId`。
- secret 编码或长度非法：`InvalidTesterJoinSecret`。
- 链接不存在、secret 不匹配、已撤销或所属 Application 不存在：统一返回 `TesterJoinLinkInvalid`。
- 当前 ACTIVE Tester 数量已达到上限：`ApplicationTesterLimitReached`。
- ID、时钟或持久化失败：内部失败，不创建部分 Membership，也不增加计数。

对外不区分链接不存在、secret 错误和链接已撤销，避免把 joinLinkId 是否存在或生命周期状态暴露给无权调用者。

### 最小领域模型

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

本用例只创建 `ACTIVE`，removedBy 和 removedAt 必须为空。`REMOVED` 以及移除字段由 UC-APP-010 使用；旧 episode 不恢复为 ACTIVE，再次加入会创建新的 membershipId。

ApplicationTesterMembership 是一次成员资格 episode，不是 Auth role。ApplicationTesterJoinLink 只是取得 Membership 的凭证，两者生命周期独立。

### 用例端口

```go
type UUIDv7Generator interface {
    NewUUIDv7() (string, error)
}

type Clock interface {
    Now() time.Time
}

type TesterJoinTokenHasher interface {
    Hash(secretBytes [32]byte) [32]byte
}

type ApplicationTesterMembershipRepository interface {
    ResolveJoinCandidate(
        ctx context.Context,
        joinLinkID ApplicationTesterJoinLinkID,
        tokenHash [32]byte,
    ) (*TesterJoinCandidate, error)

    Join(
        ctx context.Context,
        joinLinkID ApplicationTesterJoinLinkID,
        tokenHash [32]byte,
        testerAuthID AuthID,
        candidateMembership ApplicationTesterMembership,
        testerLimit int32,
    ) (*JoinApplicationAsTesterResult, error)
}
```

`ResolveJoinCandidate` 只返回验证通过后的 applicationId，并把不存在、hash 不匹配、REVOKED 和 Application 不存在统一映射为无效链接。`Join` 必须再次使用常量时间比较 tokenHash，并在同一原子边界复查链接、已有 ACTIVE Membership、容量和插入结果。Repository 不接收 rawToken。

当前领域常量 `ApplicationTesterLimit = 100`。未来若需要全局或按 Application 调整，再引入独立容量策略或管理用例，不提前把 testerLimit 加入 Application 业务字段。

### 数据模型

#### application_tester_memberships

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `membershipId` | Membership episode 稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | `partial: one ACTIVE per (applicationId, testerAuthId)` | no |
| `testerAuthId` | Tester 的 Auth ID | string | opaque authId | `partial: one ACTIVE per (applicationId, testerAuthId)` | no |
| `status` | 当前 episode 状态 | string enum | `ACTIVE/REMOVED`；本用例只写 ACTIVE | no | no |
| `joinedViaJoinLinkId` | 本次加入使用的链接 | string | 同一 Application 的 TesterJoinLink UUIDv7 | no | no |
| `joinedAt` | 加入时间 | datetime | UTC / RFC 3339 | no | no |
| `removedBy` | 移除操作者 | string | opaque authId；ACTIVE 时为空 | no | yes |
| `removedAt` | 移除时间 | datetime | UTC / RFC 3339；ACTIVE 时为空 | no | yes |

索引与 validator：

- membershipId 唯一索引。
- `(applicationId, testerAuthId)` 在 `status=ACTIVE` 条件下建立 partial unique index。
- `(applicationId, status, joinedAt, membershipId)` 索引支持稳定的当前列表和历史分页。
- `(testerAuthId, status, joinedAt, membershipId)` 索引支持用户查询自己可测试的 Application。
- ACTIVE 的 removedBy/removedAt 必须同时为空；REMOVED 必须同时存在，且不能恢复为 ACTIVE。
- joinedViaJoinLinkId 与 applicationId 的归属关系由 Repository 在加入事务中保证。

#### ACTIVE Tester 计数

存储实现必须为每个 Application 提供可原子竞争的 activeTesterCount，或使用能证明等价正确性的串行化机制。该计数是 Membership 投影，不是 Application 的新业务字段：

- 新建 ACTIVE episode 时增加 1。
- 幂等加入不改变。
- UC-APP-010 成功移除时减少 1。
- 计数不得小于 0，也不得大于本次提交使用的 testerLimit。

当前 MongoDB 实现复用 UC-APP-008 的 Application `coordinationRevision` 写栅栏：

1. `ResolveJoinCandidate` 只取得候选 applicationId，不提供最终有效性保证。
2. `Join` 在事务内先对候选 Application 的 `coordinationRevision` 执行真实递增写入，再重新读取链接并验证归属、ACTIVE 状态和 tokenHash。不得仅依赖事务外或取得栅栏之前的读取结果。
3. 同一事务内检查已有 ACTIVE Membership，统计该 Application 的 ACTIVE episode；已有成员优先幂等返回，否则在数量小于 100 时插入新 episode，并返回插入后的数量。
4. activeTesterCount 由事务内的 ACTIVE Membership 统计得到，不另建持久化计数器；Membership 插入本身改变该投影。Application 不增加业务字段。
5. 与 UC-APP-008 轮换共享同一 Application 写栅栏，使并发写冲突触发事务重试。事务使用 snapshot read concern 与 majority write concern；可重试事务错误重跑完整事务，未知提交结果仅重试提交，遵循 MongoDB driver 事务协议并受请求上下文限制，不把任意持久化失败转换为成功。
6. `(applicationId, testerAuthId)` 的 ACTIVE partial unique index 作为最终唯一性约束。重复键不能未经重新验证链接和读取已提交 Membership 就当作幂等成功。

后续 UC-APP-010 移除与 UC-APP-011 显式撤销在接入时必须遵守同一写栅栏协议；本工作包不实现这两个用例。真实 MongoDB 并发测试必须证明最后一个名额、同一用户加入和链接轮换竞争的正确性。

### API 草图

```text
POST /tester-join-links/{joinLinkId}/memberships
Authorization: <authenticated user identity>
Content-Type: application/json
Cache-Control: no-store
```

请求：

```json
{
  "secret": "base64url-encoded-32-byte-secret"
}
```

首次加入成功：`201 Created`；已经是 ACTIVE Tester：`200 OK`。

```json
{
  "joined": true,
  "membership": {
    "membershipId": "membership-uuid",
    "applicationId": "application-uuid",
    "testerAuthId": "auth-id-from-identity",
    "status": "ACTIVE",
    "joinedViaJoinLinkId": "join-link-uuid",
    "joinedAt": "2026-09-16T13:00:00Z"
  },
  "capacity": {
    "activeTesterCount": 17,
    "testerLimit": 100
  }
}
```

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- joinLinkId 或 secret 格式非法：`400 Bad Request`。
- 链接不存在、secret 错误、已撤销或 Application 不存在：统一 `404 Not Found`。
- Tester 列表已满：`409 Conflict`。

### 测试与验收

领域测试：

- Membership 只属于 Application，不包含 RPC、Version 或 Publication 字段。
- authId、membershipId、joinedViaJoinLinkId 和 joinedAt 不能为空。
- ACTIVE 与 REMOVED 字段组合满足不变量。
- REMOVED episode 不能恢复为 ACTIVE。

UseCase 测试：

- 任意已认证用户均可加入，不读取 developerStatus。
- authId 只取可信身份，不能由请求覆盖。
- secret 必须是无填充 base64url 且解码后恰好 32 bytes。
- ACTIVE 用户重复加入返回 joined=false，不生成新记录、不占用名额。
- 被移除用户持有效链接可以创建新 episode。
- 无 test 槽位时仍可加入。
- 链接无效或列表已满时不创建 Membership。

Repository 集成测试：

- 链接轮换与加入并发时，旧链接不能在轮换提交后成功加入。
- 两个用户竞争最后一个名额时最多一个成功。
- 同一用户并发加入最多创建一个 ACTIVE episode并只增加一次计数。
- partial unique index 阻止同一用户出现两个 ACTIVE episode。
- Membership 插入与 activeTesterCount 增加全部提交或全部回滚。
- 幂等加入在列表已满时仍返回既有 Membership。
- joinedViaJoinLinkId 必须与 Application 匹配。

API 与安全测试：

- 新加入返回 201，幂等加入返回 200，响应设置 `Cache-Control: no-store`。
- 请求不能指定 authId、applicationId、membershipId、status 或审计字段。
- 不存在、错误 secret、REVOKED 和 Application 不存在使用统一外部错误。
- secret 与 tokenHash 不出现在响应、访问日志、trace、指标或错误详情中。

### 实现依赖与交付边界

- UC-APP-008 已交付链接持久化、真实 token/hash、原子轮换与 URL 契约；本用例复用其 Application 写栅栏，具体事务方案见“ACTIVE Tester 计数”。
- 复用现有可信用户 JWS 校验、UUIDv7、Clock 与 MongoDB 副本集测试基础设施；入口仅投影 authId，不要求 Developer 资格。普通用户身份投影和本用例鉴权错误映射属于当前工作包。
- 不依赖 UC-APP-007 测试发布、Auth Scope Catalog、UC-APP-010 移除或 UC-APP-011 显式撤销先行实现。
- 前端扫码解析后的凭证保护与接入验证：从 joinUrl 取得 secret，放入加入请求正文，并按 BR-TST-019 避免进入统计或日志；不要求建设独立落地页。用户登录凭证到后端可信身份的生产链路仍按现有平台契约独立交付。

## 业务规则（UC-APP-009 权威正文）

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-010 -->
### BR-TST-010：可信身份与自助加入

Tester 身份必须取自可信认证上下文中的 authId，请求不能替其他用户加入。

任何已认证用户都可以使用有效链接加入，不要求 developerStatus、reviewer 权限或管理员批准。当前 admin 不会被自动加入，但可以像普通用户一样自行加入。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-011 -->
### BR-TST-011：链接凭证验证

加入必须同时满足：

- joinLinkId 指向一个存在的 TesterJoinLink。
- secret 解码后恰好 32 bytes。
- SHA-256(decoded 32-byte secret) 与 tokenHash 常量时间相等。
- 链接在最终提交时仍为 ACTIVE。
- 链接所属 Application 仍存在。

链接在初步校验后被轮换或撤销时，最终事务必须拒绝加入。REVOKED 链接永远不能恢复使用。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-012 -->
### BR-TST-012：Application 级 Membership

Tester Membership 的业务键是 `(applicationId, testerAuthId)`，不包含 rpcApiMajor、Version 或 Publication。

更换 test 槽位或客户端升级不会自动移除 Membership。管理员转让是否同时轮换加入链接属于未来转让用例的安全策略，本用例不提前决定；无论如何，转让不能由一次 Tester 加入操作触发。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-013 -->
### BR-TST-013：ACTIVE Membership 幂等

如果调用者已经是该 Application 的 ACTIVE Tester，使用当前有效链接重复加入时返回既有 Membership 和 joined=false：

- 不创建新 Membership。
- 不增加 activeTesterCount。
- 不改写 joinedAt 或 joinedViaJoinLinkId。
- 即使当前列表已经达到上限，也优先返回幂等成功。

仍然必须先验证本次链接有效；无效或已撤销的链接不能作为查询既有 Membership 的旁路。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-014 -->
### BR-TST-014：Tester 数量上限

上限按 Application 计算，只统计 ACTIVE Membership episode。加入新用户时必须在同一原子边界确认：

```text
activeTesterCount < testerLimit
```

每个 Application 的 Tester 上限固定为 100。达到上限不会自动撤销加入链接，也不会移除现有 Tester；未来若需要调整上限，必须由新的明确业务规则和用例引入。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-015 -->
### BR-TST-015：移除后可以重新加入

当前没有黑名单。曾被管理员移除的用户只要取得当前有效链接，并且 Application 仍有容量，就可以创建新的 ACTIVE Membership episode。

旧 Membership episode 和移除审计必须保留，新一次加入使用新的 membershipId 和 joinedAt，不把旧记录恢复为 ACTIVE。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-016 -->
### BR-TST-016：Membership episode 与唯一性

- membershipId 是 UUIDv7，创建后不变。
- 每个 `(applicationId, testerAuthId)` 同时最多一个 ACTIVE episode。
- 同一用户可以在被移除后留下多个历史 episode，但只有最新加入且未移除的一条为 ACTIVE。
- joinedViaJoinLinkId 必须指向本次验证通过且属于同一 Application 的链接。
- joinedAt 由 App Center 时钟生成。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-017 -->
### BR-TST-017：原子加入与容量竞争

以下检查与写入必须全部成功或全部失败：

- 链接 ACTIVE 状态与 tokenHash 复查。
- ACTIVE Membership 幂等检查。
- Application 存在性及 ACTIVE Tester 数量上限检查。
- Membership 插入和 activeTesterCount 更新。

多个用户竞争最后一个名额时最多一个成功。相同用户并发重复加入时最多创建一个 ACTIVE episode，其余请求返回既有 Membership 或并发冲突后安全重读，不能重复占用名额。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-018 -->
### BR-TST-018：与发布和 Auth 分离

加入 Tester 列表不得：

- 创建或修改 ApplicationPublication。
- 要求当前存在 test Version。
- 修改 ApplicationVersion 或 ApplicationReview。
- 把 Tester 身份写入 Auth 权限或 developerStatus。
- 发送定向邀请或管理员通知。

App Center 是 Membership 的事实来源。Auth 只提供已经认证的 authId；未来通知只能是派生消息，不能成为 Membership 成功的前置条件。

<!-- 权威位置: use-cases/UC-APP-009-join-application-as-tester.md#br-tst-019 -->
### BR-TST-019：凭证和隐私边界

App Center 只为 Membership 保存 opaque authId，不收集学生证明或额外个人资料。secret 和 tokenHash 都不得返回到 Membership API 响应、业务日志、指标标签、追踪属性或集成事件。

成功响应可以返回 joinLinkId 作为加入来源审计，但不能返回 secret、tokenHash 或其他 Tester 身份。

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

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

#### 实现配置与验收边界

Session 寿命、认证限额、MongoDB 并发实现与保留策略由 [UC-AUTH-007](../../auth-center/use-cases/UC-AUTH-007-login.md) 拥有；本契约只固定相互通信所需的格式和认证方法。并行工作包共用同一套端口和持久化约定。

本轮后端验收包括真实协议验证器、正反测试向量、生成 Proto、原生 gRPC、生产组合根与真实 Mongo 副本集上的事务/撤销测试。Android/iOS 私钥安全存储、客户端界面与恢复体验由客户端独立验收；Gateway 路由、在线 Session 到身份 JWS 签发仍为后续工作。不得用测试签名密钥或 fake verifier 代替生产认证，不把后端测试通过描述为移动端及公网调用已贯通。

### `platform/contracts/tester-join-url-v1.md`：Tester 加入 URL v1 契约

#### 目的与范围

本契约定义 App Center URL builder 与前端扫描器共同使用的加入凭证格式。链接生成与轮换规则属于 [UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)，加入行为与用户身份属于 [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md)。

当前允许使用 mock URL 入口，不要求目标页面真实存在。App Center 不访问、解析 DNS 或验证该入口可达性；mock 只指入口地址，链接 ID、secret、持久化和生命周期仍使用真实实现。

#### URL 格式

```text
{prefix}#joinLinkId={joinLinkId}&secret={secret}
```

- prefix 是绝对 HTTP 或 HTTPS URL，具有非空 host，可包含路径；不包含 userinfo、query 或 fragment。保留合法前缀的路径和末尾斜杠，不额外拼接路径。
- fragment 使用 URL query 参数编码，生成顺序固定为 `joinLinkId`、`secret`，每个键出现一次。
- joinLinkId 是服务端生成的小写规范 UUIDv7；secret 使用 [BR-TST-004](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 的无填充 base64url 编码。
- 不在 URL 中加入用户身份、applicationId、RPC major 或 Version；后端按 joinLinkId 解析所属 Application，按认证上下文确定当前用户。
- secret 只放在 fragment，不放入 URL 路径或 query。完整 joinUrl 仍是敏感值，遵循 [BR-TST-004](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 和 [BR-TST-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008)。

#### 前端解析与请求

前端扫码后解析 fragment，取得唯一的 joinLinkId 和 secret，并携带当前用户的登录认证凭证调用 UC-APP-009。joinLinkId 放在该用例定义的路径，secret 放在请求正文；用户身份遵循既有 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，不信任二维码或请求正文中自行声明的 authId。

扫码不等于加入，生成或轮换链接也不创建 Membership。前端应拒绝缺少或重复的凭证键、非法 UUIDv7 或不符合 BR-TST-004 编码的 secret，不把凭证送入日志或第三方统计。本轮后端不实现前端页面、扫码组件或 UC-APP-009。

#### 契约测试要求

- URL builder 在默认 mock 前缀和自定义 HTTP/HTTPS 前缀下都能生成可解析的 URL，正确保留路径。
- fragment 恰好包含 joinLinkId 和 secret，能无损还原服务端生成值；路径和 query 不含 secret。
- 明确无效的前缀、ID 或 secret 不能生成部分有效结果；不执行 DNS/HTTP 调用。
- 持久化只保存 BR-TST-004 定义的哈希；成功响应可返回 joinUrl，失败响应、日志和 trace 不得返回它。

#### 配置所有权

App Center 的环境变量名、默认 mock 前缀和启动失败规则见 [UC-APP-008 配置与临时入口](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#配置与临时入口)。以后只替换部署前缀时，fragment 契约保持不变。

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

- `UC-APP-009`（use-cases/UC-APP-009-join-application-as-tester.md）：数据模型/application_tester_memberships、数据模型/ACTIVE Tester 计数、后续用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-009-join-application-as-tester.md` | 411 | `556bdc015bae` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `2595342af7cd` |
| `platform/contracts/auth-device-session-v1.md` | 119 | `524cf6d814b0` |
| `platform/contracts/tester-join-url-v1.md` | 38 | `0edbb9f4f2d2` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `4bb4d40a23c8` |
