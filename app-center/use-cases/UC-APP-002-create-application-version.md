# UC-APP-002：创建应用版本

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，登记一个尚未提交审核的网页版本，并取得系统分配的版本 ID 和应用内序号。

本用例只创建 `DRAFT` ApplicationVersion，不提交审核、不批准、不发布，也不修改 stable/grey/test 槽位。

版本创建成功后不会出现在普通用户的应用目录中。

## 当前 ApplicationVersion

```text
versionId
applicationId
sequence
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
oauthRedirects
reviewStatus
createdBy
createdAt
revision
updatedBy
updatedAt
```

Application 的技术名称 name 不复制到版本中。公开 displayName、description 和 icon 属于独立的 ApplicationProfileRevision，也不复制到运行版本；release notes 等版本展示字段只有在对应真实用例出现时再加入。

## 旧实现观察

旧创建逻辑位于 `iwut-app-center/internal/biz/app_version.go` 的 `CreateAppVersion`。

### KEEP

- 只有应用管理员或有管理权限的人可以创建版本；当前还没有协作者用例，所以本轮仅允许 adminId。
- 系统为同一应用原子分配递增的内部版本序号。
- required 与 optional scopes 分开保存，并验证 scope 是否存在。
- 开发者版本标签最大长度为 50。
- 创建时校验入口 URL。
- createdAt 由系统生成。

### CHANGE

- 使用独立 UUIDv7 versionId，sequence 只负责应用内排序，不作为跨服务身份。
- `clientId` 改为 `applicationId`。
- 新版本初始状态是 `DRAFT`，而不是 `DEACTIVATE`。
- reviewStatus 只表达审核生命周期；`TEST/GREY/STABLE` 由后续 Publication 用例表达。
- 增加 RPC API major 兼容范围和 requiredCapabilities，不增加 platform/target。
- createdBy 保存创建时的 authId，即使以后管理员转让也不改变。
- 权限检查、版本序号分配和插入必须防止与管理员转让并发产生越权版本。

### DROP

- 在 Application 上保存 stable/grey/beta version 指针。
- 在 ApplicationVersion.status 中保存 `TEST/GREY/STABLE/DEACTIVATE`。
- 把 tester 数组嵌入版本记录。
- 本轮不继承 displayName、version description、icon、color 和 label。
- 创建版本时直接进入审核或发布流程。

### UNKNOWN

- RPC major 是否会长期并存；这不影响版本先声明兼容范围。

### 当前契约边界

- capability 名称的权威所有者是客户端 RPC 契约，不是 Auth 或 App Center。
- 当前阶段不建立在线 Capability Catalog；App Center 只执行 BR-VER-006 的本地格式、重复与排序规则，然后原样保存。
- Scope Catalog 仍由 Auth 唯一权威维护。核心用例只依赖 `ScopeCatalog` port；进程内 read-through cache adapter 实现该 port，单元测试使用可控 fake/mock。真实 Auth transport 属于后续独立工作包。

## 输入与身份

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
  oauthRedirects: []OAuthRedirectGroup
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

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 校验 versionLabel、launchUrl、RPC range、capabilities、scopes 和 oauthRedirects。
4. 通过 ScopeCatalog port 确认所有 scope 当前允许被新版本申请；生产组装最终使用 ADR-001 定义的带本地有界缓存 adapter，其快照源调用 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md)。
5. 生成 UUIDv7 versionId，并取得 UTC createdAt；初始化 revision 为 1、updatedBy 为 createdBy、updatedAt 为 createdAt。
6. Repository 在同一个原子操作中：
   - 确认 Application 存在且 adminId 仍等于调用者 authId。
   - 取得并增加该 Application 的 nextVersionSequence。
   - 确认 versionLabel 未被占用。
   - 插入 reviewStatus 为 `DRAFT` 的 ApplicationVersion。
7. 返回完整 ApplicationVersion。

## 异常流程

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
- oauthRedirects 的 type、数量、URL 或 hostname 规则不满足：`InvalidOAuthRedirectConfiguration`。
- Scope Catalog 无可用的新鲜快照：`ScopeCatalogUnavailable`，不创建版本。
- ID 或持久化失败：内部失败，不产生部分版本。

## 业务规则

<a id="br-ver-001"></a>
### BR-VER-001：版本身份与序号

- versionId 是系统生成的全局唯一 UUIDv7，创建后不可修改。
- sequence 由 Application 内部计数器分配，从 1 开始并严格递增。
- `(applicationId, sequence)` 唯一。
- sequence 只用于稳定排序和审计，不参与版本兼容判断。

<a id="br-ver-002"></a>
### BR-VER-002：创建权限

创建者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在真正写入时仍是 Application.adminId。

createdBy 记录创建时的 authId，之后管理员转让不会改写它。

<a id="br-ver-003"></a>
### BR-VER-003：versionLabel

- 1–50 个 Unicode code point。
- 首尾不允许 Unicode whitespace，并禁止 Unicode `Cc` 控制字符。
- 通过校验后原样保存，不解析、不排序、不强制 SemVer。
- 同一 Application 下唯一，按大小写敏感的原始字符串比较；`v1.0.0` 与 `V1.0.0` 是两个标签。

<a id="br-ver-004"></a>
### BR-VER-004：launchUrl

launchUrl 保存后的 UTF-8 表示最多 2048 bytes，必须是绝对 URL 且不允许 userinfo。[RFC 3986](https://www.rfc-editor.org/rfc/rfc3986.html) 没有规定通用 URI 最大长度，2048 是本产品为了数据库、网关、日志和客户端互操作性设置的明确上限，不是协议要求。

允许两类 URL：

- 生产 URL：`https`，可进入后续提交审核流程。
- 开发 URL：可以使用 `http`，但 host 必须是 localhost/`.localhost`、`.local`、loopback、RFC 1918 私网 IPv4、IPv6 ULA 或 link-local 地址。它只能停留在 DRAFT；提交审核前必须改为公开可访问的 HTTPS URL。

不允许 `file:`、`data:`、`javascript:` 等其他 scheme。创建 DRAFT 时只做语法和地址类别校验，不由服务端抓取 URL；提交审核时再进行 DNS 解析、公网地址与安全检查。

URL 只表示登记的入口。对于自托管网页，App Center 不能因为 URL 不变就证明远端内容没有变化。

<a id="br-ver-005"></a>
### BR-VER-005：RPC 兼容范围

- rpcApiMinVersion 必须 `>= 1`。
- rpcApiMaxVersionExclusive 必须 `> rpcApiMinVersion`。
- 只支持一个 major 时使用 `[major, major + 1)`。

宿主 RPC 兼容性由整数 major 范围与 requiredCapabilities 共同表达，不使用 platform/target。maxExclusive 不允许为空，因为尚未发布的未来 major 不能被默认视为兼容。

<a id="br-ver-006"></a>
### BR-VER-006：requiredCapabilities

- capability 名称由客户端 RPC 契约定义并负责演进。当前格式是小写 ASCII 点分名称：版本后缀之前至少有一个名称段，每个名称段匹配 `[a-z][a-z0-9]*`，并以 `.v<正整数>` 结尾；正整数使用 `[1-9][0-9]*` 表示。例如 `camera.read.v1`。
- App Center 当前不查询中央 Capability Catalog，也不判断客户端实际是否提供该 capability；它只校验上述格式。
- 数组不得包含重复项；无额外要求时保存空数组，不保存 null。
- 校验通过后按 Unicode code point 字典序排序再保存；输入顺序不表达业务含义。

<a id="br-ver-007"></a>
### BR-VER-007：scopes

- requiredScopes 和 optionalScopes 内部不得重复，二者之间也不得交叉。
- 每个 scope 必须存在于 Auth Scope Catalog。
- 没有 scope 时保存空数组，不保存 null。
- 校验通过后两个数组分别按 Unicode code point 字典序排序再保存；输入顺序不表达业务含义。
- scope 改变属于受审核内容；其编辑与重新审核规则由后续用例定义。

Scope Catalog 的权威来源是 Auth。UC-APP-002 使用 App Center 进程内的 read-through cache；TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 配置，使用 Go duration 文本，未设置时默认 `5m`。显式配置为空、无法解析、为零或负数时服务启动失败。缓存过期时同步读取 Auth，读取失败则 fail closed。当前不为这一份低频小目录单独引入 RabbitMQ 或 Redis。详细一致性方案见 [ADR-001](../adr/ADR-001-scope-catalog-cache.md)。

Domain/UseCase 核心只声明 `ScopeCatalog` port，不依赖 Auth 的 HTTP/gRPC 形状。Cache adapter 通过构造参数接收 TTL、Clock 与窄的 Auth snapshot source；只有测试使用 fake/mock，生产代码不得提供硬编码 Scope 目录。真实 Auth transport 实现根级 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md)，提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 拥有。

<a id="br-ver-018"></a>
### BR-VER-018：版本化 OAuth 回调

`oauthRedirects` 是受审核的版本内容，不属于 OAuthClient，也不从 launchUrl 推导。它是 0–2 个回调组组成的非 null 数组：

```text
OAuthRedirectGroup {
  clientType: PUBLIC_PKCE | CONFIDENTIAL_SECRET
  redirectUris: []RedirectURI
}
```

- 每种 clientType 至多一组；每组包含 1–10 个不重复 URI。空数组表示该 Version 不提供 OAuth/OIDC 回调。
- URI 必须是绝对 HTTPS URL，最多 2048 UTF-8 bytes；禁止 userinfo、fragment、wildcard、IP literal、localhost，以及 [BR-REV-007](UC-APP-004-submit-application-version-review.md#br-rev-007) 固定的 IANA `2026-05-22` special-use 域名或其子域。
- 禁止预占 OAuth/OIDC 响应参数 `code/state/iss/error/error_description/error_uri`。
- 同一组的所有 URI 必须使用同一个规范 DNS hostname。hostname 使用 non-transitional UTS #46 Lookup 转为小写 ASCII A-label；输入必须已经是规范表示，不静默改写。其余 URL 部分保存后按完整字符串精确匹配。
- callback path、query 和 port 可以不同；运行时不做前缀匹配。客户端必须控制回调处理，App Center 不向回调地址发起探测请求。
- 回调组按 clientType 固定顺序保存，组内 URI 按 Unicode code point 排序。输入顺序不表达业务含义。

OAuthClient 创建时从当前批准并发布的回调组派生不可变 sector。存在该运行上下文的 client 后，后续发布由 UC-APP-007 检查同 type 回调组的 hostname；改变 hostname 需要新的 clientId。Version 草稿本身可以在 client 创建前存在，因此创建/编辑阶段不依赖 OAuthClient。

<a id="br-ver-008"></a>
### BR-VER-008：初始生命周期

新版本的 reviewStatus 固定为 `DRAFT`。创建者不能在请求中把它设为 `SUBMITTED/APPROVED/REJECTED/REVOKED`。

DRAFT 不可进入普通目录解析，也不能成为 stable 或 grey 版本。

<a id="br-ver-009"></a>
### BR-VER-009：原子创建

当前管理员检查、sequence 分配、versionLabel 唯一检查和版本插入必须处于同一事务或等价原子边界。管理员转让与版本创建并发时，旧管理员不能在转让完成后插入版本。

创建时 revision 固定为 1，updatedBy 等于 createdBy，updatedAt 等于 createdAt。这三个字段由 UC-APP-003 的并发控制与最近修改审计要求反向引入。

## 最小领域模型

```text
ApplicationVersion {
  versionId: ApplicationVersionId
  applicationId: ApplicationId
  sequence: VersionSequence
  versionLabel: VersionLabel
  launchUrl: LaunchURL
  rpcApiRange: RpcApiRange
  requiredCapabilities: []CapabilityName
  requiredScopes: []ScopeName
  optionalScopes: []ScopeName
  oauthRedirects: []OAuthRedirectGroup
  reviewStatus: DRAFT
  createdBy: AuthId
  createdAt: Instant
  revision: 1
  updatedBy: AuthId
  updatedAt: Instant
}
```

ApplicationVersion 是独立实体。Application 仍是应用身份和当前管理员的事实来源；Application 上的 nextVersionSequence 是序号分配技术状态。

## 用例端口

```go
type ApplicationVersionIDGenerator interface {
    NewUUIDv7() (ApplicationVersionID, error)
}

type Clock interface {
    Now() time.Time
}

type ScopeCatalog interface {
    EnsureAllRequestable(
        ctx context.Context,
        scopes []ScopeName,
    ) (ScopeCatalogRevision, error)
}

type ApplicationVersionRepository interface {
    // CreateDraft 原子地检查当前 admin、分配 sequence 并插入版本。
    CreateDraft(
        ctx context.Context,
        expectedAdminID AuthID,
        draft DraftApplicationVersion,
    ) (*ApplicationVersion, error)
}
```

Repository 需要区分 Application 不存在、管理员不匹配、版本标签冲突和基础设施失败。

## 数据模型

逻辑 collection：`application_versions`。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `versionId` | 版本稳定 ID | string | UUIDv7 | yes | no |
| `applicationId` | 所属 Application | string | UUIDv7 | `(applicationId, sequence)` | no |
| `sequence` | 应用内系统序号 | int32 | `>= 1` | `(applicationId, sequence)` | no |
| `versionLabel` | 开发者版本标签 | string | UTF-8，1–50 code points；大小写敏感；首尾无 whitespace；禁止 `Cc` | `(applicationId, versionLabel)` | no |
| `launchUrl` | WebView 入口 | string | absolute HTTP(S) URI；最多 2048 UTF-8 bytes；无 userinfo；HTTP 仅限开发地址 | no | no |
| `rpcApiMinVersion` | 最小兼容 RPC major | int32 | `>= 1` | no | no |
| `rpcApiMaxVersionExclusive` | 首个不兼容 RPC major | int32 | `> min` | no | no |
| `requiredCapabilities` | 必需宿主能力 | array&lt;string&gt; | capability name；元素唯一 | no | no |
| `requiredScopes` | 必需用户数据 scopes | array&lt;string&gt; | Auth scope name；元素唯一 | no | no |
| `optionalScopes` | 可选用户数据 scopes | array&lt;string&gt; | Auth scope name；元素唯一 | no | no |
| `oauthRedirects` | 按 client type 分组的 OAuth 回调 | array&lt;object&gt; | BR-VER-018；0–2 组 | no | no |
| `reviewStatus` | 当前审核生命周期 | string enum | `DRAFT/SUBMITTED/APPROVED/REJECTED/REVOKED`；本用例只写 DRAFT | no | no |
| `createdBy` | 创建者 Auth ID | string | opaque authId | no | no |
| `createdAt` | 创建时间 | datetime | UTC / RFC 3339 | no | no |
| `revision` | 乐观并发版本 | int64 | `>= 1`；本用例固定写 1 | no | no |
| `updatedBy` | 最近一次修改者 | string | opaque authId；本用例等于 createdBy | no | no |
| `updatedAt` | 最近一次修改时间 | datetime | UTC / RFC 3339；本用例等于 createdAt | no | no |

索引与 validator：

- versionId 唯一索引。
- `(applicationId, sequence)` 复合唯一索引。
- `(applicationId, versionLabel)` 使用 binary/simple collation 的大小写敏感复合唯一索引。
- requiredCapabilities、requiredScopes、optionalScopes 和 oauthRedirects 必须存在，空值使用 `[]`。
- reviewStatus 在本用例只能写入 `DRAFT`。
- revision、updatedBy 和 updatedAt 必须存在；创建时分别为 1、createdBy 和 createdAt。

## 对 Application 持久化模型的影响

`applications` 增加以下技术字段，Application 的四个业务字段不变：

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `nextVersionSequence` | 下一个可分配的版本序号 | int32 | `>= 1`，创建 Application 时初始化为 1 | no | no |

只有版本创建 Repository 可以原子增加这个字段；外部 API 不返回它。

## API 草图

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
  "optionalScopes": ["schedule.read"],
  "oauthRedirects": [{
    "clientType": "PUBLIC_PKCE",
    "redirectUris": ["https://example.edu/oauth/callback"]
  }]
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
  "oauthRedirects": [{
    "clientType": "PUBLIC_PKCE",
    "redirectUris": ["https://example.edu/oauth/callback"]
  }],
  "reviewStatus": "DRAFT",
  "createdBy": "auth-id-from-identity",
  "createdAt": "2026-08-23T12:00:00Z",
  "revision": 1,
  "updatedBy": "auth-id-from-identity",
  "updatedAt": "2026-08-23T12:00:00Z"
}
```

## 测试与验收

领域测试：

- versionLabel、URL、RPC range、capabilities、scope 集合和 OAuth 回调的不变量成立。
- versionLabel 大小写敏感，`v1.0.0` 与 `V1.0.0` 可以分别创建。
- 2048-byte URL 边界可接受，2049 bytes 被拒绝。
- DRAFT 接受符合范围的 HTTP 私网开发 URL，不接受公网 HTTP 或非 HTTP(S) scheme。
- 单 major 范围和多 major 范围均可表达，无上界范围被拒绝。
- requiredScopes 与 optionalScopes 的重复或交叉项被拒绝。
- capabilities 和 scopes 校验后以稳定字典序保存。
- OAuth 回调拒绝多 hostname、wildcard、响应参数预占和非规范 host，并按 type/URI 稳定排序；空数组合法。
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

## 后续接口工作

Auth Scope Catalog 快照读取已经建立提供方 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)、根级 [v1 共享契约](../../platform/contracts/auth-scope-catalog-v1.md)、可执行 Proto，以及使用临时硬编码目录的真实 Kratos gRPC provider 纵切。当前仍未闭合内部服务身份与 allowlist、MongoDB 权威目录及 App Center consumer 跨服务 E2E；在这些工作完成前，测试可以调用该 provider 验证生成接口，但生产组装不得把硬编码目录当作 Auth 权威来源。

## 迁移说明

既有 UC-APP-002 实现需要新 migration 为历史 `application_versions` 回填 `oauthRedirects: []`，并同步 API、Domain、Repository 和 validator 后才能声明覆盖本扩展。服务不保留旧 `/app/create-version` 契约。

当前 `iwut-app-center` 已依赖 `github.com/google/uuid v1.6.0`，该版本提供 `uuid.NewV7()`，实现 UUIDv7 不需要新增 UUID 库。

## 变更记录

- 2026-08-23：建立 UC-APP-002，只创建 DRAFT ApplicationVersion；拆分审核生命周期与发布槽位，引入 RPC range、capabilities 和独立 versionId。
- 2026-09-15：确认 versionLabel 为 1–50 code points 的大小写敏感字符串；launchUrl 上限为 2048 bytes，并允许仅限 DRAFT 的本地/私网 HTTP 开发地址；统一使用 UUIDv7；Scope Catalog 采用 Auth 权威读取与 5 分钟进程内缓存，暂不引入 RabbitMQ。
- 2026-09-15：为 UC-APP-003 的并发控制和最近修改审计增加 revision、updatedBy、updatedAt，并统一集合的稳定排序规则。
- 2026-09-15：ScopeCatalog 返回所使用的 catalog revision，供 UC-APP-004 在提交快照中记录；创建 DRAFT 时可以忽略该返回值。
- 2026-09-19：确认 capability 由客户端 RPC 契约负责，采用小写 ASCII 点分名称和 `.v<正整数>` 后缀；当前无在线 Capability Catalog。Scope Catalog 核心仅定义 port，Auth transport 与 5 分钟 cache adapter 拆为后续工作包。
- 2026-09-20：Scope Catalog cache TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 配置，默认 `5m`；cache adapter 保持独立于真实 Auth transport。
- 2026-09-20：设计进入 `ACCEPTED`；Domain、UseCase、MongoDB 持久化、Scope Catalog cache 及事务集成测试达到 `CORE_COMPLETE`，真实 Auth transport、API Transport、Composition Root 与端到端验证单独跟踪。
- 2026-09-21：建立提供方 UC-AUTH-001 与根级 Auth Scope Catalog v1 共享契约；内部服务身份、Proto 与真实 provider 继续单独闭合。
- 2026-09-27：增加受审核的 oauthRedirects；按 client type 分组，OAuthClient 只引用当前发布版本的回调。
