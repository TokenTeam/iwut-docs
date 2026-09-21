# UC-APP-008：创建或轮换 Tester 加入链接

状态：`PROPOSED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，为整个 Application 创建一个 Tester 加入链接；若已有有效链接，则在明确匹配当前链接后原子撤销旧链接并生成新链接。

本用例负责：

- 为 Application 创建第一个有效 Tester 加入链接。
- 通过 expectedActiveJoinLinkId 防止并发管理操作静默覆盖。
- 轮换时原子撤销旧链接并创建新链接。
- 生成不可猜测的加入 secret，只持久化其哈希。
- 返回一次可生成二维码的完整 joinUrl。
- 保留已撤销链接的最小审计事实。

本用例不负责：

- 把任何用户加入 Tester 列表。
- 指定被邀请的 authId 或通过 Auth 发送定向邀请。
- 保存二维码图片。
- 检查 Tester 数量上限；该限制在用户真正加入时原子检查。
- 移除 Tester、撤销链接但不创建替代链接，或解析 test Version。
- 创建黑名单或阻止被移除的 Tester 再次通过有效链接加入。
- 绑定 rpcApiMajor、ApplicationVersion 或 ApplicationPublication。

创建链接不会使当前 admin 自动成为 Tester。Tester Membership 属于整个 Application；运行时使用客户端实际 rpcApiVersion 解析兼容的 Publication/Version。

## 业务边界

加入链接是一项面向 Application 的可撤销凭证，不是对某个用户的邀请：

```text
Application
  ├─ current adminId
  ├─ at most one ACTIVE TesterJoinLink
  └─ future: bounded Tester Memberships
```

二维码只是 joinUrl 的展示形式。App Center 保存链接状态与 tokenHash，不保存图片，也不把明文 secret 写入数据库、日志、指标或事件。

当前版本不设置自动过期时间：链接保持有效，直到管理员轮换或在后续用例中显式撤销。为缩小泄露影响，每个 Application 同时最多只有一个 `ACTIVE` 链接。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

Command：

```text
CreateOrRotateTesterJoinLinkCommand {
  expectedActiveJoinLinkId: optional ApplicationTesterJoinLinkId
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

expectedActiveJoinLinkId 的语义：

- null：调用者预期当前没有有效链接，本次只允许首次创建。
- UUIDv7：调用者预期该 ID 正是当前有效链接，本次只允许轮换它。

joinLinkId、secret、tokenHash、状态和全部审计字段都由系统生成，不能由请求正文指定。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，applicationId 和可选 expectedActiveJoinLinkId 是合法 UUIDv7。
3. Repository 加载当前状态并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - 当前有效链接的存在性和 ID 符合 expectedActiveJoinLinkId。
4. 使用密码学安全随机源生成 32-byte secret，对这 32 个原始 bytes 计算 SHA-256 tokenHash，并将 secret 编码为无填充 base64url 供 joinUrl 使用。
5. 为新链接生成 UUIDv7 joinLinkId，并从 Clock 取得 createdAt。
6. 使用 TesterJoinURLBuilder 构造包含 joinLinkId 与原始 secret 的 joinUrl。joinUrl 是敏感响应值，不进入持久化模型。
7. Repository 在同一事务或等价原子边界中重新确认当前 admin 与 expectedActiveJoinLinkId，然后：
   - 当前不存在有效链接时，创建新的 `ACTIVE` 链接。
   - 当前存在预期链接时，将旧链接改为 `REVOKED`，记录 reason=`ROTATED`、revokedBy、revokedAt 和 replacedByJoinLinkId；随后创建新的 `ACTIVE` 链接。
8. 返回新链接的公开元数据、replacedJoinLinkId 和只显示一次的 joinUrl。

生成 token、ID 或 URL 后如果最终事务因并发检查失败，生成结果必须丢弃，不能返回，也不能留下部分记录。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- expectedActiveJoinLinkId 非法：`InvalidTesterJoinLinkId`。
- Application 不存在：`ApplicationNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- 预期没有有效链接但实际存在：`ApplicationTesterJoinLinkAlreadyExists`。
- 预期存在有效链接但实际不存在：`ApplicationTesterJoinLinkNotFound`。
- 当前有效链接不是 expectedActiveJoinLinkId：`ApplicationTesterJoinLinkChanged`。
- 安全随机数、ID、URL 构造或持久化失败：内部失败，不撤销旧链接，也不创建新链接。

所有失败都不得改变当前有效链接。管理员关系或链接状态在加载与写入之间变化时，以最终原子检查为准。

## 业务规则

<a id="br-tst-001"></a>
### BR-TST-001：管理权限

创建或轮换者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

创建链接不会自动把管理员加入 Tester 列表。管理员若要测试，必须和其他用户一样在后续加入用例中使用有效链接。

<a id="br-tst-002"></a>
### BR-TST-002：Application 级凭证

Tester 加入链接只属于 Application，不绑定 rpcApiMajor、Version、Publication 或某个目标 authId。

通过链接取得的 Tester Membership 也属于整个 Application。更换 test 槽位不会使 Tester 失效；运行时兼容性由客户端实际 rpcApiVersion、capabilities 与 Publication/Version 决定。

<a id="br-tst-003"></a>
### BR-TST-003：单一有效链接

每个 Application 同时最多存在一个 `ACTIVE` TesterJoinLink。已撤销记录可以有多个并永久保留。

当前模型不设置 expiresAt，也不因 Tester 列表已满自动撤销链接。是否允许加入由后续加入用例在提交 Membership 时判断。

<a id="br-tst-004"></a>
### BR-TST-004：Secret 与哈希

- secret 必须来自密码学安全随机源，长度为 32 bytes。
- 对外编码使用无填充 base64url。
- SHA-256 输入是编码前的 32 个原始 bytes；数据库只保存 tokenHash，不保存 secret 或完整 joinUrl。
- 校验 secret 时必须使用常量时间比较。
- secret、joinUrl 和 tokenHash 不得进入普通日志、指标标签、追踪属性或集成事件。
- joinUrl 仅在创建成功响应中返回一次；遗失后只能轮换，不能从数据库恢复。

tokenHash 可以使用 SHA-256，是因为输入是系统生成的 256-bit 随机 secret，而不是低熵用户密码。

<a id="br-tst-005"></a>
### BR-TST-005：创建与轮换语义

- expectedActiveJoinLinkId 为 null 时，只能从“无有效链接”创建。
- expectedActiveJoinLinkId 有值时，只能轮换 ID 完全相同的当前有效链接。
- 每次成功调用都创建新的 joinLinkId 和 secret，不存在 no-op。
- 轮换成功后，旧链接立即失效，新链接成为唯一有效链接。
- 旧链接使用 reason=`ROTATED` 记录撤销，并指向 replacedByJoinLinkId。

以后“仅撤销而不替换”应由独立用例完成，不能伪造一次没有新链接的轮换。

<a id="br-tst-006"></a>
### BR-TST-006：乐观并发

expectedActiveJoinLinkId 是当前链接状态的并发令牌。两个管理员页面基于同一链接同时轮换时最多一个成功；失败方必须重新读取当前状态，不能自动覆盖新链接。

首次创建的并发请求同样最多一个成功。数据库必须用 partial unique constraint 或等价机制保证每个 Application 只有一个 ACTIVE 链接。

<a id="br-tst-007"></a>
### BR-TST-007：原子生命周期与审计

轮换时以下事实必须全部提交或全部回滚：

- 旧链接从 `ACTIVE` 变为 `REVOKED`。
- 旧链接记录 revokedBy、revokedAt、reason=`ROTATED` 和 replacedByJoinLinkId。
- 新链接以 `ACTIVE` 创建并记录 createdBy、createdAt。

链接记录不物理删除。后续管理界面中的“删除二维码”应映射为显式撤销，而不是清除审计记录。

<a id="br-tst-008"></a>
### BR-TST-008：二维码只是展示

App Center 返回 joinUrl；客户端或管理界面可以把它渲染成二维码、复制为链接或下载图片。二维码样式、图片格式和生成库不属于领域模型，也不保存到 App Center。

加入入口必须把 joinUrl 视为凭证，避免把 secret 暴露给第三方统计、Referer、崩溃报告或访问日志。

<a id="br-tst-009"></a>
### BR-TST-009：不产生 Tester Membership

创建或轮换链接不得：

- 新增、移除或更新 Tester Membership。
- 检查或占用 Tester 名额。
- 修改 test、grey 或 stable 发布槽位。
- 通过 Auth 创建权限或定向邀请。
- 创建用户黑名单。

被移除的 Tester 在仍持有有效链接时可以重新加入；管理界面应在未来移除用例中提示这一点，但本用例不提供“移除并撤销链接”的组合行为。

## 最小领域模型

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

本用例只创建 `ACTIVE`，并在轮换时写 `REVOKED/ROTATED`。[UC-APP-011](UC-APP-011-revoke-tester-join-link.md) 另行引入 `REVOKED/MANUAL`，不改变本用例的轮换语义。

TesterJoinLink 与未来 Tester Membership 是不同实体。链接回答“当前是否允许持有此凭证的人申请加入”，Membership 回答“哪个 authId 当前拥有该 Application 的测试资格”。

## 用例端口

```go
type UUIDv7Generator interface {
    NewUUIDv7() (string, error)
}

type Clock interface {
    Now() time.Time
}

type SecureTesterJoinTokenFactory interface {
    NewToken() (rawToken string, tokenHash [32]byte, err error)
}

type TesterJoinURLBuilder interface {
    Build(joinLinkID ApplicationTesterJoinLinkID, rawToken string) (string, error)
}

type ApplicationTesterJoinLinkRepository interface {
    LoadCurrent(
        ctx context.Context,
        applicationID ApplicationID,
        expectedAdminID AuthID,
    ) (*TesterJoinLinkCandidate, error)

    CreateOrRotate(
        ctx context.Context,
        applicationID ApplicationID,
        expectedAdminID AuthID,
        expectedActiveJoinLinkID *ApplicationTesterJoinLinkID,
        newLink ApplicationTesterJoinLink,
    ) (*CreateOrRotateTesterJoinLinkResult, error)
}
```

`CreateOrRotate` 必须重新比较 Application.adminId 和当前 ACTIVE joinLinkId，并在同一原子边界完成旧链接撤销与新链接插入。Repository 不接收或保存 rawToken、joinUrl。

## 数据模型

### application_tester_join_links

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `joinLinkId` | 加入链接稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | `partial: one ACTIVE per applicationId` | no |
| `tokenHash` | 加入 secret 的哈希 | binary | SHA-256，32 bytes | yes | no |
| `status` | 链接生命周期 | string enum | `ACTIVE/REVOKED` | no | no |
| `createdBy` | 创建时的当前 admin | string | opaque authId | no | no |
| `createdAt` | 创建时间 | datetime | UTC / RFC 3339 | no | no |
| `revokedBy` | 撤销操作者 | string | opaque authId；ACTIVE 时为空 | no | yes |
| `revokedAt` | 撤销时间 | datetime | UTC / RFC 3339；ACTIVE 时为空 | no | yes |
| `revocationReason` | 撤销原因 | string enum | `ROTATED/MANUAL`；本用例只写 ROTATED；ACTIVE 时为空 | no | yes |
| `replacedByJoinLinkId` | 轮换后的新链接 | string | UUIDv7；ROTATED 时必填 | no | yes |

索引与 validator：

- joinLinkId 唯一索引。
- tokenHash 唯一索引。
- applicationId 在 `status=ACTIVE` 条件下建立 partial unique index。
- `(applicationId, createdAt, joinLinkId)` 索引支持稳定审计分页。
- ACTIVE 记录的四个撤销字段必须全部为空。
- REVOKED 记录必须有 revokedBy、revokedAt 和 revocationReason。
- reason=`ROTATED` 时 replacedByJoinLinkId 必填；reason=`MANUAL` 时必须为空。
- tokenHash 创建后不可修改；REVOKED 不能恢复为 ACTIVE。

## API 草图

```text
POST /applications/{applicationId}/tester-join-links
Authorization: <authenticated developer identity>
Cache-Control: no-store
```

首次创建请求：

```json
{
  "expectedActiveJoinLinkId": null
}
```

轮换请求：

```json
{
  "expectedActiveJoinLinkId": "current-join-link-uuid"
}
```

首次创建与轮换都会产生新的链接资源，成功均返回 `201 Created`。

```json
{
  "joinLink": {
    "joinLinkId": "new-join-link-uuid",
    "applicationId": "application-uuid",
    "status": "ACTIVE",
    "createdBy": "admin-auth-id",
    "createdAt": "2026-09-16T12:00:00Z"
  },
  "replacedJoinLinkId": "old-join-link-uuid-or-null",
  "joinUrl": "https://app.example/tester/join/<opaque-credential>"
}
```

响应不得返回 tokenHash。`joinUrl` 只出现一次，入口日志和响应观测必须完成敏感字段脱敏。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application 不存在或预期链接不存在：`404 Not Found`。
- 链接存在性或 expectedActiveJoinLinkId 冲突：`409 Conflict`。
- applicationId 或 expectedActiveJoinLinkId 格式非法：`400 Bad Request`。

## 测试与验收

领域测试：

- TesterJoinLink 只属于 Application，不接受 RPC、Version、Publication 或目标用户字段。
- ACTIVE 与 REVOKED 字段组合满足不变量。
- ROTATED 必须指向替代链接。
- tokenHash、身份和审计字段不受请求控制。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以创建或轮换。
- 无有效链接且 expected 为 null 时创建成功。
- 有有效链接且 expected 匹配时轮换成功。
- expected 与当前状态不匹配时，不调用最终持久化。
- 安全随机源产生 32-byte secret；响应 joinUrl 包含凭证但持久化对象不包含明文。
- 创建链接不读取 Tester 数量、不创建 Membership，也不修改 Publication。
- ID、token 或 URL 构造失败时不改变旧链接。

Repository 集成测试：

- 同一 Application 的两个并发首次创建最多一个成功。
- 两个基于同一 expectedActiveJoinLinkId 的并发轮换最多一个成功。
- 管理员转让与轮换并发时，旧 admin 不能成功写入。
- 旧链接撤销与新链接创建全部提交或全部回滚。
- partial unique index 阻止两个 ACTIVE 链接。
- REVOKED 不能恢复，tokenHash 不能修改，validator 字段组合生效。

API 与安全测试：

- 首次创建与轮换都返回 201，并设置 `Cache-Control: no-store`。
- 请求不能指定 joinLinkId、token、tokenHash、status 或审计字段。
- 响应、访问日志、trace 和错误信息不暴露 tokenHash；除成功响应外不暴露 joinUrl。
- 旧 joinUrl 在轮换提交后不能再通过未来加入入口取得资格。
- QR 由客户端根据 joinUrl 生成，服务端不产生或保存图片。

## 实现前需要确认

- MongoDB 部署是否支持旧链接撤销与新链接插入所需的事务；如果不支持，需要能证明等价原子性的存储设计。
- 正式 tester join base URL/deep-link 归属及所有入口层的凭证脱敏策略。

Tester 数量上限、重复加入语义和加入时的身份校验见 [UC-APP-009](UC-APP-009-join-application-as-tester.md)：任意已登录用户可自助加入，ACTIVE Membership 重复加入幂等，容量在加入事务中原子检查。

## 后续用例

```text
UC-APP-009：已登录用户通过有效链接加入 Application Tester 列表
UC-APP-010：当前管理员移除 Application Tester
UC-APP-011：当前管理员显式撤销 Tester 加入链接
UC-APP-012：为 Tester 解析 Application 的 test 启动目标
```

移除 Tester 与撤销加入链接保持独立。若移除时仍有 ACTIVE 链接，管理界面只提示该用户仍可能再次加入，不提供组合命令。

## 变更记录

- 2026-09-16：建立 UC-APP-008；Tester 资格与加入链接均属于 Application，不绑定 RPC major；采用一个 ACTIVE 链接、哈希存储、显式轮换且不自动创建 Membership。
- 2026-09-16：由 UC-APP-009 确认任意已登录用户可自助加入、重复加入幂等、容量原子受限，链接创建本身仍不检查或占用名额。
- 2026-09-16：由 UC-APP-011 增加 REVOKED/MANUAL 终态；显式撤销不创建替代链接，也不改变 ROTATED 轮换语义。
