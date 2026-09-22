<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-002 --spec tools/brief-specs/UC-APP-002.json -->
# Brief — UC-APP-002：创建应用版本

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-002` 创建应用版本 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-VER-001`–`BR-VER-009`（9 条） |
| 外部引用 BR | — |
| ADR | `ADR-001` |
| 平台共享 | `platform/contracts/auth-scope-catalog-v1.md` |

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

> developerStatus 为 `APPROVED` 的当前应用管理员，登记一个尚未提交审核的网页版本，并取得系统分配的版本 ID 和应用内序号。

本用例只创建 `DRAFT` ApplicationVersion，不提交审核、不批准、不发布，也不修改 stable/grey/test 槽位。

版本创建成功后不会出现在普通用户的应用目录中。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

Command：

```text
CreateApplicationVersionCommand {
  versionLabel: string
  launchUrl: string
  rpcApiMinVersion: int32
  rpcApiMaxVersionExclusive: int32
  requiredCapabilities: []string
  requiredScopes: []string
  optionalScopes: []string
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

applicationId、reviewStatus、sequence、versionId、createdBy、createdAt、revision、updatedBy 和 updatedAt 不能由请求正文指定。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 校验 versionLabel、launchUrl、RPC range、capabilities 和 scopes。
4. 通过 ScopeCatalog port 确认所有 scope 当前允许被新版本申请；生产组装最终使用 ADR-001 定义的带本地有界缓存 adapter，其快照源调用 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md)。
5. 生成 UUIDv7 versionId，并取得 UTC createdAt；初始化 revision 为 1、updatedBy 为 createdBy、updatedAt 为 createdAt。
6. Repository 在同一个原子操作中：
   - 确认 Application 存在且 adminId 仍等于调用者 authId。
   - 取得并增加该 Application 的 nextVersionSequence。
   - 确认 versionLabel 未被占用。
   - 插入 reviewStatus 为 `DRAFT` 的 ApplicationVersion。
7. 返回完整 ApplicationVersion。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- Application 不存在：`ApplicationNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- versionLabel 缺失、过长、首尾含空白或含控制字符：`InvalidVersionLabel`。
- 同一 Application 已存在相同 versionLabel：`ApplicationVersionLabelAlreadyExists`。
- launchUrl 超过 2048 UTF-8 bytes，或不是允许的生产/开发 URL：`InvalidApplicationLaunchUrl`。
- RPC range 非法：`InvalidRpcApiRange`。
- capability 名称非法或重复：`InvalidRequiredCapability`。
- requiredScopes 或 optionalScopes 包含未知、重复或交叉项：`InvalidApplicationScope`。
- Scope Catalog 无可用的新鲜快照：`ScopeCatalogUnavailable`，不创建版本。
- ID 或持久化失败：内部失败，不产生部分版本。

### API 草图

```text
POST /applications/{applicationId}/versions
Authorization: <authenticated identity>
```

请求：

```json
{
  "versionLabel": "v1.0.0",
  "launchUrl": "https://example.edu/apps/course-table/v1/",
  "rpcApiMinVersion": 3,
  "rpcApiMaxVersionExclusive": 5,
  "requiredCapabilities": ["user.profile.v1"],
  "requiredScopes": ["profile.basic"],
  "optionalScopes": ["schedule.read"]
}
```

响应：`201 Created`，并返回：

```text
ETag: "1"
```

```json
{
  "versionId": "version-uuid",
  "applicationId": "application-uuid",
  "sequence": 1,
  "versionLabel": "v1.0.0",
  "launchUrl": "https://example.edu/apps/course-table/v1/",
  "rpcApiMinVersion": 3,
  "rpcApiMaxVersionExclusive": 5,
  "requiredCapabilities": ["user.profile.v1"],
  "requiredScopes": ["profile.basic"],
  "optionalScopes": ["schedule.read"],
  "reviewStatus": "DRAFT",
  "createdBy": "auth-id-from-identity",
  "createdAt": "2026-08-23T12:00:00Z",
  "revision": 1,
  "updatedBy": "auth-id-from-identity",
  "updatedAt": "2026-08-23T12:00:00Z"
}
```

### 测试与验收

领域测试：

- versionLabel、URL、RPC range、capabilities 和 scope 集合的不变量成立。
- versionLabel 大小写敏感，`v1.0.0` 与 `V1.0.0` 可以分别创建。
- 2048-byte URL 边界可接受，2049 bytes 被拒绝。
- DRAFT 接受符合范围的 HTTP 私网开发 URL，不接受公网 HTTP 或非 HTTP(S) scheme。
- 单 major 范围和多 major 范围均可表达，无上界范围被拒绝。
- requiredScopes 与 optionalScopes 的重复或交叉项被拒绝。
- capabilities 和 scopes 校验后以稳定字典序保存。
- 新版本状态只能是 DRAFT。

UseCase 测试：

- 只有 APPROVED 的当前 admin 可以创建。
- versionId、createdBy、createdAt、reviewStatus、revision、updatedBy 和 updatedAt 不受请求正文控制。
- 创建结果中 revision 为 1，updatedBy 等于 createdBy，updatedAt 等于 createdAt。
- 未知 scope 在调用 Repository 前被拒绝。
- Scope Catalog 缓存过期且 Auth 不可用时 fail closed。
- Scope Catalog TTL 内复用快照；并发 cache miss/过期刷新合并为一次 Auth snapshot 读取；TTL 配置非法时不能完成进程组装。
- Repository 业务错误映射正确。

Repository 集成测试：

- 同一应用并发创建取得不同且递增的 sequence。
- 同一应用重复 versionLabel 被唯一索引拒绝；不同应用可以使用相同标签。
- 管理员转让与创建版本并发时不会让旧 admin 越权写入。
- 原子操作失败时既不插入版本，也不增加 nextVersionSequence。
- 数组空值、nullable 字段和 validator 行为符合表定义。
- revision 和创建/更新审计字段与版本记录在同一操作中持久化。

API 测试：

- applicationId 只取路径参数。
- 请求不能指定 sequence、status、createdBy、createdAt、revision、updatedBy 或 updatedAt。
- 创建成功返回 201、`ETag: "1"` 和完整 DRAFT 版本。
- 各类身份、字段、冲突和依赖错误映射正确。

### 后续接口工作

Auth Scope Catalog 快照读取已经建立提供方 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)、根级 [v1 共享契约](../../platform/contracts/auth-scope-catalog-v1.md)、可执行 Proto，以及使用临时硬编码目录的真实 Kratos gRPC provider 纵切。当前仍未闭合内部服务身份与 allowlist、MongoDB 权威目录及 App Center consumer 跨服务 E2E；在这些工作完成前，测试可以调用该 provider 验证生成接口，但生产组装不得把硬编码目录当作 Auth 权威来源。

## 业务规则（UC-APP-002 权威正文）

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-001 -->
### BR-VER-001：版本身份与序号

- versionId 是系统生成的全局唯一 UUIDv7，创建后不可修改。
- sequence 由 Application 内部计数器分配，从 1 开始并严格递增。
- `(applicationId, sequence)` 唯一。
- sequence 只用于稳定排序和审计，不参与版本兼容判断。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-002 -->
### BR-VER-002：创建权限

创建者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在真正写入时仍是 Application.adminId。

createdBy 记录创建时的 authId，之后管理员转让不会改写它。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-003 -->
### BR-VER-003：versionLabel

- 1–50 个 Unicode code point。
- 首尾不允许 Unicode whitespace，并禁止 Unicode `Cc` 控制字符。
- 通过校验后原样保存，不解析、不排序、不强制 SemVer。
- 同一 Application 下唯一，按大小写敏感的原始字符串比较；`v1.0.0` 与 `V1.0.0` 是两个标签。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-004 -->
### BR-VER-004：launchUrl

launchUrl 保存后的 UTF-8 表示最多 2048 bytes，必须是绝对 URL 且不允许 userinfo。[RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html) 没有规定通用 URI 最大长度，2048 是本产品为了数据库、网关、日志和客户端互操作性设置的明确上限，不是协议要求。

允许两类 URL：

- 生产 URL：`https`，可进入后续提交审核流程。
- 开发 URL：可以使用 `http`，但 host 必须是 localhost/`.localhost`、`.local`、loopback、RFC 1918 私网 IPv4、IPv6 ULA 或 link-local 地址。它只能停留在 DRAFT；提交审核前必须改为公开可访问的 HTTPS URL。

不允许 `file:`、`data:`、`javascript:` 等其他 scheme。创建 DRAFT 时只做语法和地址类别校验，不由服务端抓取 URL；提交审核时再进行 DNS 解析、公网地址与安全检查。

URL 只表示登记的入口。对于自托管网页，App Center 不能因为 URL 不变就证明远端内容没有变化。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-005 -->
### BR-VER-005：RPC 兼容范围

- rpcApiMinVersion 必须 `>= 1`。
- rpcApiMaxVersionExclusive 必须 `> rpcApiMinVersion`。
- 只支持一个 major 时使用 `[major, major + 1)`。

宿主 RPC 兼容性由整数 major 范围与 requiredCapabilities 共同表达，不使用 platform/target。maxExclusive 不允许为空，因为尚未发布的未来 major 不能被默认视为兼容。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-006 -->
### BR-VER-006：requiredCapabilities

- capability 名称由客户端 RPC 契约定义并负责演进。当前格式是小写 ASCII 点分名称：版本后缀之前至少有一个名称段，每个名称段匹配 `[a-z][a-z0-9]*`，并以 `.v<正整数>` 结尾；正整数使用 `[1-9][0-9]*` 表示。例如 `camera.read.v1`。
- App Center 当前不查询中央 Capability Catalog，也不判断客户端实际是否提供该 capability；它只校验上述格式。
- 数组不得包含重复项；无额外要求时保存空数组，不保存 null。
- 校验通过后按 Unicode code point 字典序排序再保存；输入顺序不表达业务含义。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-007 -->
### BR-VER-007：scopes

- requiredScopes 和 optionalScopes 内部不得重复，二者之间也不得交叉。
- 每个 scope 必须存在于 Auth Scope Catalog。
- 没有 scope 时保存空数组，不保存 null。
- 校验通过后两个数组分别按 Unicode code point 字典序排序再保存；输入顺序不表达业务含义。
- scope 改变属于受审核内容；其编辑与重新审核规则由后续用例定义。

Scope Catalog 的权威来源是 Auth。UC-APP-002 使用 App Center 进程内的 read-through cache；TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 配置，使用 Go duration 文本，未设置时默认 `5m`。显式配置为空、无法解析、为零或负数时服务启动失败。缓存过期时同步读取 Auth，读取失败则 fail closed。当前不为这一份低频小目录单独引入 RabbitMQ 或 Redis。详细一致性方案见 [ADR-001](../adr/ADR-001-scope-catalog-cache.md)。

Domain/UseCase 核心只声明 `ScopeCatalog` port，不依赖 Auth 的 HTTP/gRPC 形状。Cache adapter 通过构造参数接收 TTL、Clock 与窄的 Auth snapshot source；只有测试使用 fake/mock，生产代码不得提供硬编码 Scope 目录。真实 Auth transport 实现根级 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md)，提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 拥有。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-008 -->
### BR-VER-008：初始生命周期

新版本的 reviewStatus 固定为 `DRAFT`。创建者不能在请求中把它设为 `SUBMITTED/APPROVED/REJECTED/REVOKED`。

DRAFT 不可进入普通目录解析，也不能成为 stable 或 grey 版本。

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-009 -->
### BR-VER-009：原子创建

当前管理员检查、sequence 分配、versionLabel 唯一检查和版本插入必须处于同一事务或等价原子边界。管理员转让与版本创建并发时，旧管理员不能在转让完成后插入版本。

创建时 revision 固定为 1，updatedBy 等于 createdBy，updatedAt 等于 createdAt。这三个字段由 UC-APP-003 的并发控制与最近修改审计要求反向引入。

## 架构决定（仅本次需要的章节）

### ADR-001：Scope Catalog 权威来源与缓存（`PROPOSED`）

#### 权威来源

Auth 是 Scope Catalog 唯一权威来源。Auth 提供可读取完整快照的内部接口：

```text
ScopeCatalogSnapshot {
  revision: int64
  scopes: []ScopeDefinition
  generatedAt: Instant
}
```

revision 必须在 Auth 内单调递增。提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 定义；跨服务 `ScopeDefinition` 首版投影和 gRPC 方法由 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md) 定义。

ScopeCatalog adapter 在完成校验时一并返回所使用的 snapshot revision。创建和修改草稿可以忽略它；UC-APP-004 将它写入 ApplicationReview，用于说明提交时依据的 Auth 目录版本。

#### 第一阶段缓存

App Center 的 ScopeCatalog adapter 使用每进程 read-through cache：

- TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 使用 Go duration 文本配置，未设置时默认 `5m`；显式值为空、无法解析、为零或负数时进程组装失败，不静默回退。
- 进程启动或 cache miss 时同步读取 Auth 快照。
- TTL 内直接使用缓存快照。
- TTL 到期时同步刷新；使用 singleflight 合并同一时刻的刷新请求。
- 刷新失败时不使用过期快照创建版本，返回 `ScopeCatalogUnavailable`。
- Auth revision 发生回退时视为不可用并 fail closed，避免用较旧快照覆盖进程已经观察到的较新事实。
- 不为此单独引入 Redis。

这是有界缓存，不是 App Center 自己的 Scope Catalog。缓存内容不能被 App Center 管理接口修改。

环境变量只由 config/composition boundary 读取；Cache adapter 通过构造参数接收已经校验的 TTL、Clock 与 snapshot source，不直接读取进程环境。真实 Auth transport 必须实现共享 gRPC 契约；测试可以使用实现同一生成接口的 Auth Server 或 port fake，不得在生产代码中硬编码目录。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-scope-catalog-v1.md`：Auth Scope Catalog v1 跨服务契约

#### gRPC 方法

首版只提供内部原生 gRPC：

```text
/auth_center.v1.scope_catalog.ScopeCatalog/GetScopeCatalogSnapshot
```

Proto 结构：

```proto
service ScopeCatalog {
  rpc GetScopeCatalogSnapshot(GetScopeCatalogSnapshotRequest)
      returns (GetScopeCatalogSnapshotResponse);
}

message GetScopeCatalogSnapshotRequest {}

message GetScopeCatalogSnapshotResponse {
  int64 revision = 1;
  google.protobuf.Timestamp generated_at = 2;
  repeated ScopeDefinition scopes = 3;
}

message ScopeDefinition {
  string name = 1;
  bool requestable = 2;
}
```

不声明 `google.api.http` annotation，不经 Gateway 暴露，不提供浏览器或 gRPC-Web 入口。

#### 快照语义

- `revision` 必须大于零，并遵循 [BR-SCP-003](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- 消费方只把 `requestable = true` 的 name 用于新申请校验；它不是最终授权结果。
- 消费方遇到未知追加字段时必须忽略，以保持向后兼容。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证内部服务身份。Auth Center 在验签后按固定 full method → `auth.scope-catalog.read` 映射检查 caller 注册表；认证成功不自动产生读取权限。

测试 Auth Server 可以验证 consumer 行为，但生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_SCOPE_CATALOG_READ_FORBIDDEN` |
| 权威目录暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含凭证、存储查询、连接地址、Scope 私有元数据或堆栈。调用方不得把失败时持有的过期快照包装成本次成功响应。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. gRPC full method 与 package/service/rpc 名称准确。
2. request message 没有业务字段或用户身份字段。
3. response 字段号和类型与本契约一致。
4. 空目录编码为空列表，不是错误或伪造占位 Scope。
5. duplicate/empty name、非正 revision、无效 generatedAt 或非稳定排序不能作为成功快照。
6. `UNAUTHENTICATED`、`PERMISSION_DENIED`、`UNAVAILABLE` 与稳定 reason 映射一致。
7. App Center E2E 的测试 Auth Server 实现同一生成接口，不维护另一份手写 wire model。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-002`（use-cases/UC-APP-002-create-application-version.md）：当前 ApplicationVersion、旧实现观察、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、迁移说明、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `platform/contracts/auth-scope-catalog-v1.md`（docs 根级共享文档）：目的与所有权、兼容性、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-002-create-application-version.md` | 427 | `8e8bb5e13166` |
| `adr/ADR-001-scope-catalog-cache.md` | 112 | `a5fe7365b96f` |
| `platform/contracts/auth-scope-catalog-v1.md` | 91 | `cab448326f29` |
