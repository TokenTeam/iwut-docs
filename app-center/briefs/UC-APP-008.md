<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-008 --spec tools/brief-specs/UC-APP-008.json -->
# Brief — UC-APP-008：创建或轮换 Tester 加入链接

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-008` 创建或轮换 Tester 加入链接 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-TST-001`–`BR-TST-009`（9 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/tester-join-url-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

### 业务边界

加入链接是一项面向 Application 的可撤销凭证，不是对某个用户的邀请：

```text
Application
  ├─ current adminId
  ├─ at most one ACTIVE TesterJoinLink
  └─ future: bounded Tester Memberships
```

二维码只是 joinUrl 的展示形式。App Center 保存链接状态与 tokenHash，不保存图片，也不把明文 secret 写入数据库、日志、指标或事件。

当前版本不设置自动过期时间：链接保持有效，直到管理员轮换或在后续用例中显式撤销。为缩小泄露影响，每个 Application 同时最多只有一个 `ACTIVE` 链接。

### 前端扫码与加入边界

joinUrl 由前端扫码读取和解析，前端取得 joinLinkId 与 secret 后，携带当前用户的登录认证凭证调用 [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md#输入与身份)。App Center 根据该用例验证加入凭证并创建 Membership。

“携带用户信息”指通过认证链路建立可信用户身份；请求正文不接受前端自行指定的 authId 或用户资料作为身份依据。客户端到 Gateway 的登录认证与后端可信身份载体遵循现有 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，不因扫码另建一套身份协议。

本流程不要求 App Center 提供可直接访问的扫码落地 GET 接口，也不要求先建设独立 Web 落地页。扫码/解析本身不产生 Membership。URL builder 与前端共享 [Tester 加入 URL v1 契约](../../platform/contracts/tester-join-url-v1.md)；部署前缀不进入领域模型，凭证保护遵循 BR-TST-004、BR-TST-008。

### 配置与临时入口

- URL 前缀通过 `APP_CENTER_TESTER_JOIN_URL_PREFIX` 配置；未设置时默认 `https://app.example/tester/join`，作为无需真实页面的 mock 入口。
- URL 构造与前端解析遵循 [Tester 加入 URL v1 契约](../../platform/contracts/tester-join-url-v1.md#url-格式)，输出必须带齐 joinLinkId 和 secret。仅入口可以是 mock；随机 secret、哈希与存储不使用 mock。
- 环境变量仅由 config/composition boundary 读取；校验通过的前缀通过构造参数注入 URL builder。显式空值、首尾空白、非绝对 HTTP(S) URL、缺少 host、含 userinfo/query/fragment 或其它 URL 语法错误必须使启动失败，不静默使用默认值。
- HTTP 前缀允许本地开发入口；当前不检查 DNS、网络可达性或是否部署了页面。前缀变化只影响之后新生成的 joinUrl，不改写已有链接状态或哈希。
- 本工作包完成标准包含默认 mock 和 env 自定义前缀下的 URL 生成、前端可解析字段及敏感信息边界；真实前端扫码与 UC-APP-009 加入链路独立交付，不阻塞本 UC。

### 输入与身份

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

### 主流程

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

### 异常流程

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

### 最小领域模型

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

本用例只创建 `ACTIVE`，并在轮换时写 `REVOKED/ROTATED`。[UC-APP-011](../use-cases/UC-APP-011-revoke-tester-join-link.md) 另行引入 `REVOKED/MANUAL`，不改变本用例的轮换语义。

TesterJoinLink 与未来 Tester Membership 是不同实体。链接回答“当前是否允许持有此凭证的人申请加入”，Membership 回答“哪个 authId 当前拥有该 Application 的测试资格”。

### 用例端口

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

### 数据模型

#### application_tester_join_links

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

### API 草图

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
  "joinUrl": "https://app.example/tester/join#joinLinkId=new-join-link-uuid&secret=base64url-encoded-secret"
}
```

响应不得返回 tokenHash。`joinUrl` 只出现一次，入口日志和响应观测必须完成敏感字段脱敏。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application 不存在或预期链接不存在：`404 Not Found`。
- 链接存在性或 expectedActiveJoinLinkId 冲突：`409 Conflict`。
- applicationId 或 expectedActiveJoinLinkId 格式非法：`400 Bad Request`。

### 测试与验收

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
- 默认 mock URL 和 env 自定义前缀都按共享格式无损携带 joinLinkId/secret；URL 构造不依赖网络，非法显式配置阻止启动。

### 实现依赖与交付边界

- 复用既有 Application、可信 DeveloperIdentity、UUIDv7、Clock、Wire 和 MongoDB 事务基础；不依赖 Publication、Membership、Scope Catalog 或新的 Auth 查询。
- 开发和集成环境使用支持事务的 MongoDB replica set；已验证在唯一部分索引下，同一事务中撤销旧 ACTIVE 链接再插入新 ACTIVE 链接可行。正式实现仍须覆盖全部并发与回滚验收。
- 最终事务使用既有 Application adapter-only 写入栅栏或等价机制防止管理员转让竞争；不改变 Application 业务字段。
- URL 的临时入口、环境变量和编码已明确，本工作包可以开始；真实前端接入、生产登录到可信身份链路及 UC-APP-009 不纳入本次实现。

Tester 数量上限、重复加入语义和加入时的身份校验见 [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md)：任意已登录用户可自助加入，ACTIVE Membership 重复加入幂等，容量在加入事务中原子检查。

## 业务规则（UC-APP-008 权威正文）

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-001 -->
### BR-TST-001：管理权限

创建或轮换者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

创建链接不会自动把管理员加入 Tester 列表。管理员若要测试，必须和其他用户一样在后续加入用例中使用有效链接。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-002 -->
### BR-TST-002：Application 级凭证

Tester 加入链接只属于 Application，不绑定 rpcApiMajor、Version、Publication 或某个目标 authId。

通过链接取得的 Tester Membership 也属于整个 Application。更换 test 槽位不会使 Tester 失效；运行时兼容性由客户端实际 rpcApiVersion、capabilities 与 Publication/Version 决定。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-003 -->
### BR-TST-003：单一有效链接

每个 Application 同时最多存在一个 `ACTIVE` TesterJoinLink。已撤销记录可以有多个并永久保留。

当前模型不设置 expiresAt，也不因 Tester 列表已满自动撤销链接。是否允许加入由后续加入用例在提交 Membership 时判断。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004 -->
### BR-TST-004：Secret 与哈希

- secret 必须来自密码学安全随机源，长度为 32 bytes。
- 对外编码使用无填充 base64url。
- SHA-256 输入是编码前的 32 个原始 bytes；数据库只保存 tokenHash，不保存 secret 或完整 joinUrl。
- 校验 secret 时必须使用常量时间比较。
- secret、joinUrl 和 tokenHash 不得进入普通日志、指标标签、追踪属性或集成事件。
- joinUrl 仅在创建成功响应中返回一次；遗失后只能轮换，不能从数据库恢复。

tokenHash 可以使用 SHA-256，是因为输入是系统生成的 256-bit 随机 secret，而不是低熵用户密码。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-005 -->
### BR-TST-005：创建与轮换语义

- expectedActiveJoinLinkId 为 null 时，只能从“无有效链接”创建。
- expectedActiveJoinLinkId 有值时，只能轮换 ID 完全相同的当前有效链接。
- 每次成功调用都创建新的 joinLinkId 和 secret，不存在 no-op。
- 轮换成功后，旧链接立即失效，新链接成为唯一有效链接。
- 旧链接使用 reason=`ROTATED` 记录撤销，并指向 replacedByJoinLinkId。

以后“仅撤销而不替换”应由独立用例完成，不能伪造一次没有新链接的轮换。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-006 -->
### BR-TST-006：乐观并发

expectedActiveJoinLinkId 是当前链接状态的并发令牌。两个管理员页面基于同一链接同时轮换时最多一个成功；失败方必须重新读取当前状态，不能自动覆盖新链接。

首次创建的并发请求同样最多一个成功。数据库必须用 partial unique constraint 或等价机制保证每个 Application 只有一个 ACTIVE 链接。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-007 -->
### BR-TST-007：原子生命周期与审计

轮换时以下事实必须全部提交或全部回滚：

- 旧链接从 `ACTIVE` 变为 `REVOKED`。
- 旧链接记录 revokedBy、revokedAt、reason=`ROTATED` 和 replacedByJoinLinkId。
- 新链接以 `ACTIVE` 创建并记录 createdBy、createdAt。

链接记录不物理删除。后续管理界面中的“删除二维码”应映射为显式撤销，而不是清除审计记录。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008 -->
### BR-TST-008：二维码只是展示

App Center 返回 joinUrl；客户端或管理界面可以把它渲染成二维码、复制为链接或下载图片。二维码样式、图片格式和生成库不属于领域模型，也不保存到 App Center。

加入入口必须把 joinUrl 视为凭证，避免把 secret 暴露给第三方统计、Referer、崩溃报告或访问日志。

<!-- 权威位置: use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-009 -->
### BR-TST-009：不产生 Tester Membership

创建或轮换链接不得：

- 新增、移除或更新 Tester Membership。
- 检查或占用 Tester 名额。
- 修改 test、grey 或 stable 发布槽位。
- 通过 Auth 创建权限或定向邀请。
- 创建用户黑名单。

被移除的 Tester 在仍持有有效链接时可以重新加入；管理界面应在未来移除用例中提示这一点，但本用例不提供“移除并撤销链接”的组合行为。

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
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
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

- `UC-APP-008`（use-cases/UC-APP-008-create-or-rotate-tester-join-link.md）：数据模型/application_tester_join_links、后续用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-008-create-or-rotate-tester-join-link.md` | 414 | `9a39e6856efb` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/tester-join-url-v1.md` | 38 | `0edbb9f4f2d2` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
