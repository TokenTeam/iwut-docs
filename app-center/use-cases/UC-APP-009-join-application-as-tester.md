# UC-APP-009：通过有效链接加入 Application Tester 列表

状态：`ACCEPTED`

## 目标与范围

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

扫码、点击链接和深链跳转只是取得 joinLinkId 与 secret 的入口交互。前端扫码后使用当前用户的登录认证凭证发起本用例的加入请求；扫码与加入的职责边界见 [UC-APP-008](UC-APP-008-create-or-rotate-tester-join-link.md#前端扫码与加入边界)。真正的 Tester 资格只在本用例成功提交 Membership 后成立。

## 业务边界

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

## 输入与身份

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

## 主流程

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

## 异常流程

- 缺少身份或 authId：`AuthenticatedUserRequired`。
- joinLinkId 格式非法：`InvalidTesterJoinLinkId`。
- secret 编码或长度非法：`InvalidTesterJoinSecret`。
- 链接不存在、secret 不匹配、已撤销或所属 Application 不存在：统一返回 `TesterJoinLinkInvalid`。
- 当前 ACTIVE Tester 数量已达到上限：`ApplicationTesterLimitReached`。
- ID、时钟或持久化失败：内部失败，不创建部分 Membership，也不增加计数。

对外不区分链接不存在、secret 错误和链接已撤销，避免把 joinLinkId 是否存在或生命周期状态暴露给无权调用者。

## 业务规则

<a id="br-tst-010"></a>
### BR-TST-010：可信身份与自助加入

Tester 身份必须取自可信认证上下文中的 authId，请求不能替其他用户加入。

任何已认证用户都可以使用有效链接加入，不要求 developerStatus、reviewer 权限或管理员批准。当前 admin 不会被自动加入，但可以像普通用户一样自行加入。

<a id="br-tst-011"></a>
### BR-TST-011：链接凭证验证

加入必须同时满足：

- joinLinkId 指向一个存在的 TesterJoinLink。
- secret 解码后恰好 32 bytes。
- SHA-256(decoded 32-byte secret) 与 tokenHash 常量时间相等。
- 链接在最终提交时仍为 ACTIVE。
- 链接所属 Application 仍存在。

链接在初步校验后被轮换或撤销时，最终事务必须拒绝加入。REVOKED 链接永远不能恢复使用。

<a id="br-tst-012"></a>
### BR-TST-012：Application 级 Membership

Tester Membership 的业务键是 `(applicationId, testerAuthId)`，不包含 rpcApiMajor、Version 或 Publication。

更换 test 槽位或客户端升级不会自动移除 Membership。管理员转让是否同时轮换加入链接属于未来转让用例的安全策略，本用例不提前决定；无论如何，转让不能由一次 Tester 加入操作触发。

<a id="br-tst-013"></a>
### BR-TST-013：ACTIVE Membership 幂等

如果调用者已经是该 Application 的 ACTIVE Tester，使用当前有效链接重复加入时返回既有 Membership 和 joined=false：

- 不创建新 Membership。
- 不增加 activeTesterCount。
- 不改写 joinedAt 或 joinedViaJoinLinkId。
- 即使当前列表已经达到上限，也优先返回幂等成功。

仍然必须先验证本次链接有效；无效或已撤销的链接不能作为查询既有 Membership 的旁路。

<a id="br-tst-014"></a>
### BR-TST-014：Tester 数量上限

上限按 Application 计算，只统计 ACTIVE Membership episode。加入新用户时必须在同一原子边界确认：

```text
activeTesterCount < testerLimit
```

每个 Application 的 Tester 上限固定为 100。达到上限不会自动撤销加入链接，也不会移除现有 Tester；未来若需要调整上限，必须由新的明确业务规则和用例引入。

<a id="br-tst-015"></a>
### BR-TST-015：移除后可以重新加入

当前没有黑名单。曾被管理员移除的用户只要取得当前有效链接，并且 Application 仍有容量，就可以创建新的 ACTIVE Membership episode。

旧 Membership episode 和移除审计必须保留，新一次加入使用新的 membershipId 和 joinedAt，不把旧记录恢复为 ACTIVE。

<a id="br-tst-016"></a>
### BR-TST-016：Membership episode 与唯一性

- membershipId 是 UUIDv7，创建后不变。
- 每个 `(applicationId, testerAuthId)` 同时最多一个 ACTIVE episode。
- 同一用户可以在被移除后留下多个历史 episode，但只有最新加入且未移除的一条为 ACTIVE。
- joinedViaJoinLinkId 必须指向本次验证通过且属于同一 Application 的链接。
- joinedAt 由 App Center 时钟生成。

<a id="br-tst-017"></a>
### BR-TST-017：原子加入与容量竞争

以下检查与写入必须全部成功或全部失败：

- 链接 ACTIVE 状态与 tokenHash 复查。
- ACTIVE Membership 幂等检查。
- Application 存在性及 ACTIVE Tester 数量上限检查。
- Membership 插入和 activeTesterCount 更新。

多个用户竞争最后一个名额时最多一个成功。相同用户并发重复加入时最多创建一个 ACTIVE episode，其余请求返回既有 Membership 或并发冲突后安全重读，不能重复占用名额。

<a id="br-tst-018"></a>
### BR-TST-018：与发布和 Auth 分离

加入 Tester 列表不得：

- 创建或修改 ApplicationPublication。
- 要求当前存在 test Version。
- 修改 ApplicationVersion 或 ApplicationReview。
- 把 Tester 身份写入 Auth 权限或 developerStatus。
- 发送定向邀请或管理员通知。

App Center 是 Membership 的事实来源。Auth 只提供已经认证的 authId；未来通知只能是派生消息，不能成为 Membership 成功的前置条件。

<a id="br-tst-019"></a>
### BR-TST-019：凭证和隐私边界

App Center 只为 Membership 保存 opaque authId，不收集学生证明或额外个人资料。secret 和 tokenHash 都不得返回到 Membership API 响应、业务日志、指标标签、追踪属性或集成事件。

成功响应可以返回 joinLinkId 作为加入来源审计，但不能返回 secret、tokenHash 或其他 Tester 身份。

## 最小领域模型

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

## 用例端口

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

## 数据模型

### application_tester_memberships

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

### ACTIVE Tester 计数

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

## API 草图

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

## 测试与验收

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

## 实现依赖与交付边界

- UC-APP-008 已交付链接持久化、真实 token/hash、原子轮换与 URL 契约；本用例复用其 Application 写栅栏，具体事务方案见“ACTIVE Tester 计数”。
- 复用现有可信用户 JWS 校验、UUIDv7、Clock 与 MongoDB 副本集测试基础设施；入口仅投影 authId，不要求 Developer 资格。普通用户身份投影和本用例鉴权错误映射属于当前工作包。
- 不依赖 UC-APP-007 测试发布、Auth Scope Catalog、UC-APP-010 移除或 UC-APP-011 显式撤销先行实现。
- 前端扫码解析后的凭证保护与接入验证：从 joinUrl 取得 secret，放入加入请求正文，并按 BR-TST-019 避免进入统计或日志；不要求建设独立落地页。用户登录凭证到后端可信身份的生产链路仍按现有平台契约独立交付。

## 后续用例

```text
UC-APP-010：当前管理员移除 Application Tester
UC-APP-011：当前管理员显式撤销 Tester 加入链接
UC-APP-012：为 Tester 解析 Application 的 test 启动目标
```

UC-APP-010 已具体化为 [管理员移除 Application Tester](UC-APP-010-remove-application-tester.md)：删除的是当前 ACTIVE Membership episode。若仍有有效加入链接，管理界面只警告该用户可以再次加入，不撤销链接，也不创建黑名单。

## 变更记录

- 2026-09-16：建立 UC-APP-009；任何已认证用户可通过有效链接取得 Application 级 Tester Membership，重复加入幂等，容量原子受限，被移除后可重新加入。
- 2026-09-16：确认每个 Application 的 ACTIVE Tester 上限固定为 100，当前不引入可调整容量策略。
- 2026-09-16：由 UC-APP-010 确认 Membership 按 episode 移除、REMOVED 为终态且释放容量；移除不撤销加入链接或形成黑名单。

- 2026-09-22：明确由前端扫码后携带用户认证凭证发起加入请求，引用 UC-APP-008 的入口职责；请求正文仍只接受 secret，用户身份从认证上下文取得。

- 2026-09-22：状态改为 ACCEPTED；确认复用 UC-APP-008 Application 写栅栏，在同一事务复查链接、幂等检查、统计 ACTIVE Membership 与插入，固定事务重试及独立前端/Gateway 交付边界。
