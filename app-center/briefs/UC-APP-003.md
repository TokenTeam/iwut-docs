<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-003 --spec tools/brief-specs/UC-APP-003.json -->
# Brief — UC-APP-003：更新草稿应用版本

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-003` 更新草稿应用版本 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-VER-010`–`BR-VER-017`（8 条） |
| 外部引用 BR | `BR-VER-003`–`BR-VER-007`（5 条）（来自 `UC-APP-002`） |
| ADR | `ADR-001` |

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

> developerStatus 为 `APPROVED` 的当前应用管理员，以自己读取到的 revision 为前提，完整替换一个 DRAFT ApplicationVersion 的可编辑内容。

本用例只更新 DRAFT，不负责：

- 提交审核或改变 reviewStatus。
- 修改已提交、已批准、已拒绝或已撤销版本。
- 修改 Application.name 或独立的 ApplicationProfileRevision。
- 修改 stable/grey/test 发布槽位。
- 保存每次草稿编辑的完整历史。

读取单个版本或版本列表是支持管理页面的 Query，不需要为此建立新的领域实体。

### 可编辑与不可编辑字段

完整替换以下字段：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
```

系统在成功修改时更新：

```text
revision
updatedBy
updatedAt
```

以下字段不可由本用例修改：

```text
versionId
applicationId
sequence
reviewStatus
createdBy
createdAt
```

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
versionId: ApplicationVersionId
```

Command：

```text
UpdateDraftApplicationVersionCommand {
  expectedRevision: int64
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

HTTP adapter 从 `If-Match` 读取 expectedRevision；gRPC adapter 使用 command 字段表达相同语义。

### 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`。
3. 确认 expectedRevision `>= 1`。
4. 使用 UC-APP-002 的相同规则校验所有可编辑字段。
5. 通过 ScopeCatalog adapter 确认 requiredScopes 和 optionalScopes 当前允许被新版本申请。
6. 将 capabilities 和 scopes 分别按字典序规范化为稳定集合表示。
7. 从系统时钟取得 updatedAt。
8. Repository 原子确认并更新：
   - Application 存在且 adminId 仍等于调用者 authId。
   - ApplicationVersion 属于路径中的 Application。
   - reviewStatus 仍是 `DRAFT`。
   - revision 等于 expectedRevision。
   - 新 versionLabel 未与同一 Application 的其他版本冲突。
   - 完整替换可编辑字段。
   - revision 增加 1，updatedBy 设为 authId，updatedAt 设为系统时间。
9. 返回更新后的完整 ApplicationVersion 和新 revision。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- expectedRevision 缺失或 `< 1`：`ApplicationVersionRevisionRequired`。
- Application 或指定 Version 不存在：`ApplicationVersionNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- Version 不属于路径中的 Application：按 `ApplicationVersionNotFound` 处理。
- reviewStatus 不是 `DRAFT`：`ApplicationVersionNotDraft`。
- 当前 revision 不等于 expectedRevision：`ApplicationVersionRevisionConflict`。
- versionLabel 与其他 Version 冲突：`ApplicationVersionLabelAlreadyExists`。
- 字段、URL、RPC range、capabilities 或 scopes 非法：沿用 UC-APP-002 对应错误。
- Scope Catalog 无新鲜快照：`ScopeCatalogUnavailable`。
- 持久化失败：内部失败，不返回部分更新结果。

为避免泄露跨应用 versionId 的存在性，applicationId 与 versionId 不匹配时不返回真实所属应用。

### 最小领域行为

```text
ApplicationVersion.ReplaceDraft(
  expectedRevision,
  replacement,
  updatedBy,
  updatedAt,
) -> ApplicationVersion
```

单实体内部可以保护 DRAFT、revision 和字段不变量；跨 Application 的当前 admin 检查以及 versionLabel 唯一性由 Repository 的原子操作共同保护。

### 用例端口

```go
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
    ReplaceDraft(
        ctx context.Context,
        applicationID ApplicationID,
        versionID ApplicationVersionID,
        expectedAdminID AuthID,
        expectedRevision int64,
        replacement DraftApplicationVersionReplacement,
        updatedAt time.Time,
    ) (*ApplicationVersion, error)
}
```

Repository 必须区分：NotFound、NotAdmin、NotDraft、RevisionConflict、VersionLabelConflict 和基础设施失败。

### 数据模型变化

UC-APP-003 不增加 collection。`application_versions` 增加三个非空字段；UC-APP-002 创建时同时初始化。

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `revision` | ApplicationVersion 并发版本 | int64 | `>= 1`；创建时为 1；成功修改或状态迁移后递增 | no | no |
| `updatedBy` | 最近一次修改者 | string | opaque authId；创建时等于 createdBy | no | no |
| `updatedAt` | 最近一次修改时间 | datetime | UTC / RFC 3339；创建时等于 createdAt | no | no |

既有索引继续生效：

- versionId 全局唯一。
- `(applicationId, sequence)` 唯一。
- `(applicationId, versionLabel)` 大小写敏感唯一。

条件更新至少包含 versionId、applicationId、reviewStatus=`DRAFT` 和 expectedRevision。管理员检查与更新必须和 Application.adminId 的读取处于同一原子边界。

### 测试与验收

领域测试：

- DRAFT 且 revision 匹配时可以完整替换可编辑字段。
- 非 DRAFT 或 revision 不匹配时不产生变化。
- 不可变字段在更新后保持不变。
- 相同规范化内容是 no-op，不增加 revision。
- 集合乱序输入规范化后得到稳定顺序；重复和 scope 交叉仍被拒绝。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以更新。
- 使用与 UC-APP-002 相同的字段和 Scope Catalog 规则。
- updatedBy 只能来自可信 authId，updatedAt 只能来自 Clock。
- Scope Catalog 失败时不调用 Repository。
- Repository 业务错误映射正确。

Repository 集成测试：

- 两个相同 expectedRevision 的并发更新最多一个成功。
- revision、updatedBy、updatedAt 与内容在同一原子写入中变化。
- 修改为同一 Application 中已存在的 versionLabel 被唯一索引拒绝。
- 更新与管理员转让并发时，旧 admin 不能越权成功。
- 更新与提交审核并发时，不会修改已离开 DRAFT 的 Version。
- applicationId/versionId 不匹配时返回 NotFound。

API 测试：

- 使用 PUT 完整替换，缺失字段不是“保持旧值”。
- If-Match 正确时返回新 ETag；过期时返回 412。
- 无内容变化时返回当前 ETag，不伪造一次修改。
- 请求正文不能修改 ID、sequence、状态和审计字段。
- HTTP 开发 URL 可以保存为 DRAFT。

## 业务规则（UC-APP-003 权威正文）

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-010 -->
### BR-VER-010：仅草稿可编辑

只有 reviewStatus 为 `DRAFT` 的 ApplicationVersion 可以被本用例更新。

`SUBMITTED/APPROVED/REJECTED/REVOKED` 都不能绕过状态用例直接修改。被拒绝 Version 必须先通过 [UC-APP-006](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md) 显式恢复为 DRAFT。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-011 -->
### BR-VER-011：完整替换

请求必须提供全部可编辑字段，服务端以新值整体替换旧值。空数组表示明确清空该集合，不表示“不修改”。

本用例不提供单字段 Patch，也不使用字段 mask。这样 URL、RPC range、capabilities 和 scopes 可以在同一组校验和一次原子写入中保持一致。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-012 -->
### BR-VER-012：不可变身份与创建审计

versionId、applicationId、sequence、createdBy 和 createdAt 创建后不可修改。reviewStatus 只能由提交审核、审核决定和撤销等独立用例改变。

管理员转让不会改写 createdBy；updatedBy 记录本次实际修改者。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-013 -->
### BR-VER-013：乐观并发

- 创建 DRAFT 时 revision 为 1。
- 客户端更新时必须提交自己读取到的 expectedRevision。
- 只有 `currentRevision == expectedRevision` 才能写入。
- 成功修改后 revision 原子增加 1。
- revision 不匹配时不自动合并，也不执行覆盖。

若 expectedRevision 正确但规范化后的可编辑内容与当前内容完全相同，返回当前 Version，不修改 revision、updatedBy 或 updatedAt。

revision 属于整个 ApplicationVersion，而不是只属于草稿内容；UC-APP-004 及后续生命周期迁移也必须在成功改变状态时增加 revision。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-014 -->
### BR-VER-014：集合规范化

requiredCapabilities、requiredScopes 和 optionalScopes 在业务上都是集合：

- 输入包含重复项时仍然拒绝，而不是静默去重。
- requiredScopes 与 optionalScopes 不能交叉。
- 校验通过后分别按 Unicode code point 字典序排序再保存。
- 集合顺序变化不构成业务修改。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-015 -->
### BR-VER-015：字段规则复用

versionLabel、launchUrl、RPC range、capabilities 和 scopes 必须满足 UC-APP-002 的 BR-VER-003 至 BR-VER-007。规则只有一个定义来源，UC-APP-003 不维护宽松副本。

尤其是：HTTP 开发 URL 仍只能用于 DRAFT；改为公开 HTTPS 后才能进入未来提交审核用例。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-016 -->
### BR-VER-016：权限与更新原子性

管理员身份、DRAFT 状态、expectedRevision、versionLabel 唯一性和写入必须在同一事务或等价原子边界中确认。

这同时防止：

- 原 admin 在管理员转让完成后继续修改。
- Version 提交审核后，较早发出的更新请求又把内容写回。
- 两个编辑页面静默覆盖彼此。

<!-- 权威位置: use-cases/UC-APP-003-update-draft-application-version.md#br-ver-017 -->
### BR-VER-017：草稿审计粒度

当前只保存最近一次修改者、时间和 revision，不保存每次草稿编辑的完整内容历史。提交审核时由 ApplicationReview 保存不可变快照；若以后确有恢复草稿历史的需求，再引入 DraftRevision，不提前承担该成本。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-002`

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

Domain/UseCase 核心只声明 `ScopeCatalog` port，不依赖 Auth 的 HTTP/gRPC 形状。Cache adapter 通过构造参数接收 TTL、Clock 与窄的 Auth snapshot source；只有测试使用 fake/mock，生产代码不得提供硬编码 Scope 目录。真实 Auth transport 在 Auth 接口确定后实现。

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

revision 必须在 Auth 内单调递增。UC-APP-002 至少需要知道哪些 scope 当前允许被新 ApplicationVersion 申请；完整 ScopeDefinition 在设计 Auth 用例时确定。

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

环境变量只由 config/composition boundary 读取；Cache adapter 通过构造参数接收已经校验的 TTL、Clock 与 snapshot source，不直接读取进程环境。真实 Auth transport 尚未确定时，测试使用 fake source，不得在生产代码中硬编码目录。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-003`（use-cases/UC-APP-003-update-draft-application-version.md）：旧实现观察、API 草图、后续用例、迁移说明、变更记录
- `UC-APP-002`（use-cases/UC-APP-002-create-application-version.md）：目标与范围、当前 ApplicationVersion、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、后续接口工作、迁移说明、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-003-update-draft-application-version.md` | 369 | `db3d6fac8074` |
| `use-cases/UC-APP-002-create-application-version.md` | 426 | `ba31f8a63776` |
| `adr/ADR-001-scope-catalog-cache.md` | 112 | `88161ee9c7ee` |
