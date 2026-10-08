<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-028 --spec tools/brief-specs/UC-AUTH-028.json -->
# Brief — UC-AUTH-028：向第三方应用披露用户资料字段

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-028` 向第三方应用披露用户资料字段 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-UPF-012`–`BR-UPF-016`（5 条） |
| 外部引用 BR | `BR-SCP-004`（来自 `UC-AUTH-001`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-scope-catalog-v1.md`、`platform/contracts/oauth-oidc-v1.md` |

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

持有有效 OAuth access token 的第三方应用，通过既有 OIDC UserInfo 读取用户明确授权的、当前仍允许披露的 UC-AUTH-005 资料字段。每个可披露字段使用一个独立且稳定的 OAuth scope；新增字段不能借用旧 scope 扩大历史 consent。

本用例扩展 [UC-AUTH-017](../use-cases/UC-AUTH-017-get-oidc-user-info.md) 的 UserInfo 最小投影，不新增资料查询端点，不允许应用在请求中提交任意 field key，也不把本人资料接口、平台 Session、ID Token 或内部 authId 变成第三方资料凭据。邮箱继续由 UC011/017 的激活邮箱事实提供，不从资料 KV 投影。

字段值仍是用户主动提供、平台只校验格式的资料；第三方读取不把它变成学校或平台验证事实。ApplicationUserStorage、公开个人主页、管理员代查、资料搜索和历史快照不在本用例范围。

### 参与者与依赖

- 用户通过 UC014 对应用当前 Version 已审核声明的 scope 明确同意；grant、code、access/refresh token、撤销及三渠道资格继续由 UC014–018 定义。
- App Center 继续只消费 [Auth Scope Catalog v1](../../platform/contracts/auth-scope-catalog-v1.md) 的 `name/requestable` 投影，不读取资料字段目录，也不决定字段到 scope 的映射。
- Auth 同时拥有 UC005 的 ProfileFieldDefinition 目录、OAuth 权威 Scope Catalog、用户 profile、grant 与 access token；映射在 Auth 启动装载时闭合。
- 第三方应用只调用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md) 的 `GET/POST /userinfo`，并按现有规则核对 pairwise `sub`。

实现依赖已经闭合：UC005 提供有界、带类型的 profile 快照；UC001 提供持久 Scope Catalog；UC014–018 已提供审核、consent、有效权限交集、撤销和 UserInfo 在线读取。无需新增跨服务 RPC 或修改 Scope Catalog v1 线格式。

### 输入与输出

本用例没有新的公网请求字段。输入仍是唯一的 `Authorization: Bearer <access-token>`。

OAuth 部署目录中的可披露定义在既有 Scope 条目上增加 Auth 内部元数据：

```text
UserInfoProfileScope {
  name: "profile." + fieldKey
  label: non-empty consent label
  description: non-empty disclosure description
  kind: USERINFO_PROFILE
  audience: empty
  enabled: bool
  profileField: fieldKey
}
```

其中 `profileField` 必须精确引用当前已发布 ProfileFieldDefinition。`name` 由固定前缀和完整 field key 组成，例如字段 `education.school_name` 只能映射为 scope `profile.education.school_name`。

UserInfo 在既有 `sub`、可选 `email/email_verified` 之外，按需返回一个固定自定义 claim：

```json
{
  "sub": "<pairwise-subject>",
  "iwut_profile": {
    "education.enrollment_year": 2024,
    "education.school_name": "示例大学"
  }
}
```

`iwut_profile` 的 key 按 ASCII 字典序构造；JSON 对象顺序不构成客户端语义。STRING 与 DATE 输出 JSON string，INTEGER 输出 JSON number，BOOLEAN 输出 JSON boolean。响应不包含 profile revision、updatedAt、字段 label/description、未授权 key 或空值占位。

### 主流程

1. 按 UC017 在线验证 access token、family、grant、Application/渠道/Version 当前资格、Scope Catalog 和 UserInfo audience，并取得有效 scope 集合 E 与 pairwise sub。
2. 从当前权威目录选出 E 中 `kind=USERINFO_PROFILE` 的 scope；再次验证其名称、field key 和已装载类型元数据完整一致。
3. 若没有有效资料 scope，保持 UC017 的现有最小响应，不读取或返回 profile。
4. 在同一 Auth 一致性边界读取当前 ACTIVE USER 与完整 profile，拒绝缺失或损坏结构；只按选中定义查找对应 key。
5. 省略用户当前未填写的字段；把存在且类型匹配的值投影到 `iwut_profile`。任一目标值结构或类型不一致时整次读取失败关闭，不返回部分资料。
6. 返回 no-store 的标准 UserInfo JSON；不在日志、trace、metrics 或审计正文记录字段值。

### 验收场景

- 两个字段分别映射两个 scope；只同意其中一个时 `iwut_profile` 只含对应 key，应用请求体中的额外 field key 不存在也不能扩大结果。
- 新增第二个字段/scope 后，旧 grant 与旧 access token 不获得该字段；完成应用审核、用户新增 consent 并取得新 token 后才可读取。
- 用户未填写、之后填写、修改和删除字段时，既有有效授权分别表现为省略、出现、更新和再次省略；profile revision 不出现在响应。
- STRING、INTEGER、BOOLEAN、DATE 逐类保持 JSON 类型；零、false 与合法日期不被误判为缺失。
- email scope 与资料中相似 key 分离；只有当前激活邮箱产生 `email/email_verified=true`。
- scope disabled、Version 移除、grant 撤回、family/token 失效、三渠道资格丢失、账号禁用和 Application tombstone 均按当前 OAuth 规则拒绝或省略，恢复不越过原 token ceiling。
- ProfileFieldDefinition 不存在、同 scope 改绑 field、valueType 漂移、重复映射和非法 USERINFO_PROFILE audience 在启动时失败；持久目录损坏和目标 profile 类型损坏在读取时失败关闭。
- openid/email-only 行为保持与 UC017 一致；标准 OIDC 客户端仍能忽略未知 `iwut_profile` claim，并验证同一 sub。
- Scope Catalog v1 继续只输出 name/requestable；实际 App Center 可声明、审核并发布资料 scope，无需理解 field key 或新 Proto 字段。

### 实现依赖与交付边界

本工作包修改 Auth Center 服务与其配置/测试，不需要修改独立 API Proto：UserInfo 是标准 JSON 端点，Scope Catalog v1 的既有投影足以让 App Center 消费。实现应扩展持久 OAuth Scope 模型、启动交叉校验、当前 profile 解码、UserInfo/Discovery 投影，以及真实 Mongo/生产 Wire/实际 App 联合验收。

生产启用前必须由部署配置显式装载真实 ProfileFieldDefinition 和对应 USERINFO_PROFILE scope，并完成 consent 文案与 App 审核策略验收；仓库示例和测试字段不构成生产收集清单。官方门户必须逐项展示资料 scope 文案。Gateway 继续透传既有 `/userinfo`，无需解析 `iwut_profile`。

ApplicationUserStorage、字段目录在线管理、资料值真实性验证、敏感字段分级/强制二次确认、客户端资料编辑 UI 和第三方 SDK 类型封装分别后续设计。没有生产映射时功能保持关闭；不得把旧 Auth Center 的 `scope_keys`、任意字段过滤或 per-app storage 接口迁入本实现。

### 变更记录

- 2026-10-08：提出一字段一 scope、固定 `iwut_profile` claim 和 Auth 启动交叉校验方案；核对 UC005/001/014–018、共享契约及当前 Auth HEAD 后确认无需新跨服务 RPC 或 Proto，设计接受。

## 业务规则（UC-AUTH-028 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-012 -->
### BR-UPF-012：一字段一 Scope 的稳定映射

只有 Auth OAuth 目录中显式 `kind=USERINFO_PROFILE` 的条目可以披露 UC005 资料。每个条目精确映射一个 field key，scope 名固定为 `profile.<fieldKey>`，audience 必须为空；同一个 field key 和 scope 名均只能出现一次。

启动装载必须把每个映射与同一次完整 ProfileFieldDefinition 视图核对，并将其 valueType 固定进 Auth 持久 Scope Catalog。未知 field key、名称不匹配、重复映射、错误 kind/audience、缺少 consent 文案或类型不一致均拒绝启动。运行期不从 App 声明、用户资料内容、测试 fixture 或旧 Auth 实现推导映射。

已持久化 scope 的 kind、profileField 和 valueType 不得原地改变，字段 key 也不得改名或复用。新增可披露字段必须新增字段定义和新的 scope；不得给既有 scope 追加第二个字段。首版不提供在线删除或改绑命令；`enabled` 的变更仍遵循 BR-SCP-004。

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-013 -->
### BR-UPF-013：审核、同意与当前有效集合共同授权

资料 scope 与其它 OAuth scope 一样，必须先被 ApplicationVersion 声明并通过 App 审核，再由用户在 consent 中逐项同意。有效披露只取 access token scope、grant G、当前 Version 许可、Auth 当前 enabled 目录 C 的交集 E；字段存在、用户曾填写或 App 请求 field key 本身都不产生权限。

`/userinfo` 仍要求 `openid` 和 UserInfo audience。资料 scope 不能单独把不含 openid 的请求变成有效 OIDC 请求。新增资料 scope 对已有 grant 是新权限，遵循 UC014 的重新 consent；不会扩张旧 access token。Scope 停用或 Version 移除后立即停止投影，但不删除 G；恢复后仅在原凭据仍满足既有期限、撤销和 scope ceiling 时恢复。

用户在已授予某字段 scope 后新增或修改该字段，会使之后的 UserInfo 读取看到当前值；这是既有字段授权下的数据变化，不是新增 scope。资料编辑本身不创建 grant、不替应用同意 scope，也不恢复已撤销授权。

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-014 -->
### BR-UPF-014：固定 claim 与最小当前值投影

所有资料字段只进入顶层固定 claim `iwut_profile`，其值为 field key 到标量的 JSON object。field key 不提升为顶层 OIDC claim，不允许映射覆盖 `sub`、`email`、`email_verified` 或其它标准/平台 claim；应用不能请求返回任意 key 或全量 profile。

只返回 E 对应且用户当前实际保存的值。缺失字段被省略；全部缺失时省略整个 `iwut_profile`。不返回 null、默认值、历史值、目录中其它字段、profile revision 或更新时间。输出保留 UC005 的逻辑值；不 trim、不规范化、不把 DATE 转成带时区时间，也不从一个字段推导另一个字段。

应用必须把这些值视为用户自述数据，并按普通数据/文本安全处理；scope label、description 和字段目录文案不是 UserInfo 数据。资料中的 `email` 或相似 key 仍不能替代 UC011 的激活邮箱及 `email_verified`。

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-015 -->
### BR-UPF-015：在线当前读取与生命周期传播

UserInfo 每次读取当前 profile，不把资料复制进 grant、code、access/refresh token、ID Token 或 ApplicationUserStorage。字段修改或删除在后续成功读取中即时反映；删除不撤销 scope，scope 撤销也不删除用户资料。

账号禁用/CLOSED、Application 关闭、grant/family/token 撤销、渠道发布或资格丢失继续先按 UC017/022/025/026 拒绝整个 UserInfo。资料读取与这些 Auth 本地事实使用既有认证事务栅栏和一致检查点；撤销提交后开始的读取不能返回资料。跨 App 数据仍由 Application 级 pairwise sub 隔离，同一 Application 的既有 sub 稳定规则不变。

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-016 -->
### BR-UPF-016：损坏、依赖故障与隐私边界

只有实际需要资料 scope 时才要求 profile 和映射可读。目标 profile 缺失、revision/updatedAt/entries 损坏、重复 key、未知存储类型、目标值与固定 valueType 不符、目录映射损坏或数据库故障，均返回 UserInfo 依赖失败；不得降级为“字段未填写”、缓存值或部分成功。正常未填写不是错误。

响应使用 `Cache-Control: no-store`，并沿用 UC017 的 `invalid_token`、`insufficient_scope` 与 `temporarily_unavailable` 外部错误边界，不向应用区分用户是否填写某个未授权字段。常规日志、trace、metrics 标签和 OAuth 审计不得记录 profile field value；可记录 requestId、clientId、scope 名集合、结果类别和耗时，但不能记录 access token、authId 与字段值组合。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-001`

<!-- 权威位置: use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004 -->
### BR-SCP-004：ScopeDefinition 投影

Auth 内部的 ScopeDefinition 只使用 `enabled: bool` 表达启用状态，不引入独立的 requestable、runtimeEnabled 或“只允许旧应用使用”状态。enabled 必须显式存在；权威记录缺失该字段或格式错误属于目录不可用，不能默认启用。

首版跨服务投影仍只包含稳定 `name` 和 `requestable`：

- name 必须非空，在同一快照内唯一，并由 Auth 原样返回。
- requestable 固定由 enabled 投影，不能独立配置或写入；为 true 时允许新 ApplicationVersion 申请，为 false 时必须被新的申请拒绝。
- enabled=false 的 scope 不进入 Auth 新授权/签发的许可集合，也不进入已有凭据的实际有效权限集合；enabled=true 仍需通过用户同意、应用许可、token 范围等检查。OAuth 各阶段的处理分别由 UC014–019 定义。
- requestable 不表达用户 consent、token grant 或最终数据访问授权；消费方缓存不能替代 Auth 当前 enabled 的运行检查。
- 停用不删除 scope 定义或用户历史同意，也不等同于用户撤回；恢复必须保持同名 scope 原语义，不能复用旧名称扩大数据范围。Grant 与凭据恢复边界见 [BR-OAU-002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-002)。
- 其它展示、安全分类或数据投影元数据不在本 UC 中提前定义。

本规则固定状态及其读投影，不增加目录写接口；生产持久化/部署装载另行交付，在线目录管理仍不在本用例范围内。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-scope-catalog-v1.md`：Auth Scope Catalog v1 跨服务契约

#### 目的与所有权

本契约定义读取 Auth 权威 Scope Catalog 完整快照的线格式和原生 gRPC 边界。业务行为由 [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 及其 `BR-SCP-*` 拥有；本文件不复制 Auth 的内部持久化或目录管理规则。

Auth Center 是提供方，App Center 是首个消费方。可执行 Proto 由独立 API 仓库拥有，目标目录为 `auth_center/v1/scope_catalog/`。

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

- `revision` 必须大于零，并遵循 [BR-SCP-003](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- `requestable` 固定投影 Auth 当前 `enabled`，状态定义唯一引用 [BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。停用项仍返回，值为 false；不增加独立 runtimeEnabled 字段。
- PROTOCOL、RESOURCE 与 UC028 的 USERINFO_PROFILE 都使用同一 `name/requestable` 投影；kind、resource audience、profile field 和 UserInfo claim 映射均为 Auth 内部元数据，不进入 v1。App 不能从 scope 名之外猜测或重建这些字段。
- App 消费方继续把 `requestable = true` 的 name 用于版本申请、审核和发布规则的目录检查；它不是最终用户授权结果。Auth OAuth 路径直接检查自己的当前权威状态，不以 App 缓存或历史批准快照代替。
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
8. Provider 的 enabled 状态与 requestable 投影一致，启停递增 revision；完整快照保留停用项，App 的既有布尔校验无需新增状态分支。

#### 兼容性

- 本次 enabled 单状态决定保留 `bool requestable = 2`、消息名和 full method，不要求 App 修改 Proto 或 UC-APP-018 client 管理逻辑；App 无需持久化第二份 enabled。现有“true 可申请、false 不可申请”的消费方式保持兼容，新增约束是 Auth 从唯一状态生成该投影。
- v1 可以追加 optional 字段或新增错误 reason，但不得改变现有字段号、字段类型或 full method。
- 删除字段时保留其 field number 和 name 为 `reserved`。
- 改变完整快照、revision 或 requestable 的语义需要新的平台契约评审；不能只修改某一方实现。

### `platform/contracts/oauth-oidc-v1.md`：OAuth 与 OIDC 接入协议 v1

#### 范围与职责

提供 Authorization Code Flow，用 OIDC ID Token 表达应用登录结果，用独立的 opaque access token 表达委托访问。Auth 拥有登录、consent、grant 和 token；App 拥有 client 身份/secret，以及 ApplicationVersion 中受审核的 redirect URI 和 scopes；Traefik/Gateway 执行入口鉴权，资源服务执行业务授权。

相关业务规则由 [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) 至 [019](../use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-AUTH-028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md)、[UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) 至 [021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md) 拥有。跨服务 App 接口见 [App OAuth Client v1](../../platform/contracts/app-oauth-client-v1.md)，入口和下游身份见 [OAuth 委托上下文 v1](../../platform/contracts/oauth-delegation-v1.md)。

#### 公网端点与响应

部署固定 HTTPS issuer，例如 `https://auth.example.org/auth-center/oidc`。issuer、端点和签发内容都来自受信配置，不能从请求 Host/Forwarded 推导。

| 相对 issuer 的路径 | 方法 | 入口策略与用途 |
| --- | --- | --- |
| `/.well-known/openid-configuration` | GET | DIRECT；discovery |
| `/jwks` | GET | DIRECT；仅 OIDC 公钥 |
| `/authorize` | GET、POST | DIRECT；Auth 自行校验参数及官方登录门户会话 |
| `/token` | POST | DIRECT；Auth 自行校验 client/code/verifier 或 refresh token |
| `/userinfo` | GET、POST | DIRECT；Auth 自行在线校验 access token，不使用 Session |
| `/revoke` | POST | DIRECT；Auth 自行校验 client 与待撤销 token |

上述 DIRECT 不等于无鉴权，只是不经过 Session→用户 JWS 的转换。标准端点属于 `OIDC_HTTP`，显式加入 Gateway 路由 schema；不能假造 HTTP annotation 或套用 Kratos ProtoJSON envelope。POST authorize/token/revoke 使用 `application/x-www-form-urlencoded`；UserInfo 的 token 仅接受 `Authorization: Bearer …`。不支持 query/body 传 access token。Discovery/JWKS 可公开缓存，其余响应 `Cache-Control: no-store`、`Pragma: no-cache`。

成功兑换示例（示例值不是可用凭据）：

```json
{
  "token_type": "Bearer",
  "access_token": "<opaque random token>",
  "expires_in": 900,
  "id_token": "<signed JWT, different from access_token>",
  "scope": "openid email"
}
```

只有按 UC-AUTH-016 获得离线授权时才增加 `refresh_token`。刷新响应保留 access_token/token_type/expires_in/scope/refresh_token，首版不重新签发 ID Token。

Discovery 必须准确声明 issuer、authorization_endpoint、token_endpoint、userinfo_endpoint、jwks_uri、revocation_endpoint；`response_types_supported=[code]`、`grant_types_supported=[authorization_code,refresh_token]`、`subject_types_supported=[pairwise]`、`id_token_signing_alg_values_supported=[RS256]`、`token_endpoint_auth_methods_supported=[none,client_secret_basic]`、`code_challenge_methods_supported=[S256]`。`response_modes_supported=[query]`、`authorization_response_iss_parameter_supported=true`；revocation 同样支持 none/basic。scopes_supported 仅列出实际装载、enabled=true 且已实现的 scope；不宣称动态注册、logout、introspection 或 JWT access token profile 已实现。

#### Scope 启用与兼容投影

Scope 单一启用状态与 requestable 投影唯一由 [UC-AUTH-001 / BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 定义；OAuth 当前目录许可集合 C 及授权/恢复边界见 [UC-AUTH-014 / BR-OAU-001、002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-001)。本协议不增加 requestable 与 runtimeEnabled 两个独立开关。

App 继续使用已有 requestable 字段进行版本管理检查；Auth 的 authorize、code 兑换、refresh、UserInfo 和委托签发分别遵循 UC014–019 的当前目录检查。停用不会调用用户撤销用例或抹掉历史同意。目录故障使用依赖错误，Discovery 缓存或 App 旧快照不改变运行判断。

`kind=USERINFO_PROFILE` 是 Auth 内部 Scope Catalog 元数据，不扩展跨服务 `ScopeDefinition` 线格式。其名称固定为 `profile.<fieldKey>`，audience 为空，并按 UC028 一对一映射 UC005 字段；App 仍只看到 name/requestable。该类 scope 与 PROTOCOL/RESOURCE 一起进入实际 enabled 集合，但只用于 UserInfo，不产生 Gateway 资源 audience 或委托路由。

#### 授权请求与登录门户

必填 `response_type=code`、client_id、精确 redirect_uri、含 `openid` 的 scope、state、nonce，以及产品扩展参数 `iwut_channel=TEST|GREY|STABLE`、正整数 `iwut_rpc_api_major`；PUBLIC 额外必填 code_challenge/code_challenge_method。channel 必须精确等于 client 登记渠道；major 只选择该渠道 App Center 的权威 Publication，不能覆盖 Version、回调或 scope。两者绑定到 code/token/family，后续资源请求、UserInfo 或 refresh 不接受改选。客户端每次新建至少 32 随机字节的 state、nonce；服务端接受 43–128 字符的 base64url 值，不把 nonce 当用户身份。PKCE verifier 为 RFC 7636 规定的 43–128 个 unreserved ASCII 字符；challenge 为 SHA-256 后无 padding 的 base64url，固定 43 字符。

Auth 在建立登录 interaction 前以 clientId、iwut_channel 和 iwut_rpc_api_major 调用 App 的 `ResolveClientRuntimeConfiguration`，从 exact-major 当前渠道 Publication 的批准 Version snapshot 取得 effective redirect URIs 和 scopes，并从当前已批准 ProfileRevision 取得展示资料，再先精确匹配 redirect_uri。runtime tuple 包含 versionId、publicationRevision、profileRevisionId 和 adminAuthId；用户登录后以该 tuple 调用 `ResolveAuthorizationContext`，确认和 code 兑换时继续重查。任何 tuple 变化都不能把旧回调或展示资料与新 scopes、Profile、Tester 或 Grey cohort 资格拼接。

Grant 业务主键为 `(authId, applicationId, channel)`，具体约束由 [BR-OAU-002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 定义。同应用同渠道的 PUBLIC/CONFIDENTIAL client 及各 major 共享历史同意；grantId 是稳定引用 ID，不以 client 或 Version 为授权身份。code、access/refresh token 和 family 仍各自绑定 client，不能跨 client 兑换、刷新或撤销；共享同意不省略各自的 client authentication/PKCE、当前版本资格或 offline_access 确认。历史同意集合 G 不因当前版本 scope 减少而删减；只有本次请求超出 G 的部分需要新增同意。实际访问使用 token、G、当前批准版本及 Auth 当前目录许可集合 C 的交集，UC014/016/018/019 定义唯一业务规则。revision 用于 OCC/审计，用户撤回递增共享 grant 的独立 revocationEpoch，对同应用同渠道所有 client 的旧凭据生效；新增同意不使旧 token 失效，也不自动扩大旧 token。授权交互和 code 始终绑定其创建时的精确 runtime tuple 与 redirect URI；旧 code 不能因 grant 可延续而兑换到新 Version 的回调。secret 轮换只影响之后的 confidential client authentication，不单独撤销 grant、access token 或 refresh family。

支持 `prompt=none|login|consent`（首版单值）、非负整数 max_age。申请 offline_access 必须 prompt=consent 并实际确认，缺失时返回 invalid_request，不静默授予离线访问。无 prompt 时可复用尚有效的平台登录与既有 grant；none 不允许显示 UI，缺登录/新权限分别返回 login_required/consent_required。login/max_age 要求重新走 UC007/012 的认证，不能靠刷新门户 cookie 伪造 auth_time。nonce 写入最终 ID Token，state 原样返回。重新认证不得复用进入 prompt=login 前的同一 Session；auth_time 取 Auth 记录的实际认证时间，不接受浏览器上报。

官方 Auth 登录/consent 门户是交付的一部分；下述 /portal 路径也相对 issuer，不是站点根目录。浏览器先走既有注册/登录能力，取得平台 Session 后，在同源 `POST /portal/session` 用 `x-iwut-session` 建立 `__Host-iwut-portal` cookie：值为原 Session，Secure、HttpOnly、Path=/、SameSite=Lax，寿命不长于 Session；Auth 仍逐次在线验证。该桥接只接受配置的官方 Origin、JSON 和自定义 header，禁止跨域 CORS。cookie 只在 Auth 专用主机使用，代理不能传给应用。

门户确认使用同源 `POST /portal/interactions/{interactionId}/confirm`，含绑定 Session/interaction 的服务端随机 CSRF token、用户选择的 optional scopes 与同意/拒绝决定。Auth 重新检查 Session 归属及 interaction；请求体不接受可覆盖的 authId/client/redirect/scope 定义。禁止第三方 iframe 嵌入（CSP frame-ancestors 'none'），页面 Referrer-Policy 为 no-referrer，不加载第三方统计脚本。交互标识本身不是用户授权凭据。

原生应用使用系统浏览器和已登记的 HTTPS app/universal link 回调；前端 verifier/state/nonce 只保存在发起端。首版不设计 custom scheme、loopback 回调或把原生平台 Session 放入浏览器 URL 的 SSO 桥。官方宿主已有 Session 的无感浏览器迁移另行交付；允许在门户重新认证。

成功通过 303 跳回精确登记的 redirect_uri，仅附加 code、state、iss；客户端核对 iss 与发起时保存的 issuer。错误只有在 client 与 redirect_uri 已通过校验后才允许回跳；恶意/未知回调留在 Auth 本地报错。回调登记禁止占用 code/state/iss/error 等响应参数。应用处理一次回调后清除 URL 中的 code，不在日志或 Referer 中传播。

#### 凭据与身份格式

授权码、access token、refresh token 分别由 CSPRNG 产生 32 字节，base64url 无 padding；用途隔离的 SHA-256 摘要建索引，原值只在成功响应中出现。Session、三类 OAuth 凭据即使形状相同也只能查各自的存储，禁止自动回退。数据库 TTL 清理不代替 expiresAt 检查。

| 对象 | 首版有效期 | 消费方 |
| --- | --- | --- |
| 授权交互 | 10 分钟 | 官方门户 |
| 授权码 | 90 秒，一次性 | token endpoint |
| access token | 15 分钟，仍逐次在线查授权 | UserInfo / Gateway |
| ID Token | 5 分钟 | 该 client 的登录处理 |
| refresh family | 30 天未成功刷新失效；自首次签发起最长 180 天 | token endpoint；滑动闲置期限＋固定绝对上限 |

上述天数按 24 小时计算。refresh 的滑动更新、到期边界和 access token 剩余寿命截断规则唯一由 [UC-AUTH-016 / BR-OAU-010](../use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-010) 定义；轮换改变 token 值，续期只移动闲置截止时间，不重置整条链的绝对上限。

ID Token 使用独立 OIDC RSA 签名密钥与 JWKS（RS256，RSA 至少 2048 bit）。header 为 `alg=RS256,typ=JWT,kid=<configured key>`；claims 为 iss、sub、单值 aud=client_id、iat、exp、auth_time、nonce、at_hash。at_hash 按 OIDC RS256 的 SHA-256 左半摘要规则，从实际 access token 计算。不包含平台 Session、内部 authId、学生关联值、developer/reviewer 权限或全量资料。

client 必须用预先信任 issuer 的 discovery/JWKS 验签，检查算法、iss、aud、exp、nonce、at_hash；ID Token 的时钟容差最多 30 秒，max_age 请求还须检查 auth_time；未知 kid 只允许对固定 JWKS 地址进行有界刷新，不访问 JWT 提供的 URL。ID Token 不作为 API Bearer token；取得后 client 可自行建立应用会话，其寿命由应用管理。OIDC 签名密钥退役前保留公钥至少覆盖已签 token 的有效期、容许时钟差和 JWKS 缓存期限。

pairwise sub 的业务所有权和持久化由 [BR-OAU-021](../use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021) 定义：一个 Application 一个稳定 sector，所有 channel/type/major/Version 共用。Auth 从 App 验证 clientId→applicationId 后创建映射；App 不保存 sector/sub，用户和开发者不能自选其他应用的 sector。同一 sector 下 PUBLIC/CONFIDENTIAL 的 sub 相同，但 ID Token 的 aud 仍分别为各自 clientId，不能跨 client 使用 ID Token 登录。

UserInfo 的资料扩展使用固定顶层自定义 claim `iwut_profile`，其值是完整 field key 到 JSON 标量的 object；每次只包含当前有效 `profile.<fieldKey>` scope 对应且用户当前已填写的字段。STRING/DATE 为 string、INTEGER 为 number、BOOLEAN 为 boolean；没有值时省略该 key，全部为空时省略 `iwut_profile`。该 claim 不进入 ID Token，不包含 revision/updatedAt，也不能覆盖 sub/email/email_verified。精确授权、故障与生命周期规则见 [UC-AUTH-028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md)。Discovery 的 `claims_supported` 在交付后增加 `iwut_profile`，`scopes_supported` 只列实际 enabled 的资料 scope。

#### 错误、CORS 与限额

协议端点返回 OAuth/OIDC JSON error，不包装业务 envelope。无效 client 统一 invalid_client（Basic 失败 HTTP 401 并带 WWW-Authenticate）；失效 code/verifier/refresh 统一 invalid_grant（400）；非法参数 invalid_request，越界 scope invalid_scope。不要向攻击者区分 secret、用户、grant 是否存在。依赖故障返回 503 与 temporarily_unavailable，不当成用户拒绝或已撤销。

UserInfo 无效 token 返回 401 Bearer invalid_token；scope 不够返回 403 insufficient_scope。API 不返回登录 302。revocation 已失效/未知/不属于调用 client 的 token 统一 200；不支持的 token 类型用 unsupported_token_type。

PUBLIC token/UserInfo/revoke 的浏览器 CORS 只允许当前批准并发布 Version 中 PUBLIC_PKCE effective callbacks 对应的 HTTPS origin（无 cookie credentials），缺 Origin 的原生调用仍按协议认证；preflight 无 token 时仅根据当前 effective public origins 联集返回允许的方法/headers，实际请求仍按认证后的 client 再匹配 Origin；验证 preflight 不授予访问权限。CONFIDENTIAL token/revoke 不启用跨域浏览器访问。授权端点仅允许顶层导航，不提供跨域 fetch 登录。

请求体最大 16 KiB、scope 最多 32 项、单项最多 128 ASCII 字符；单值参数重复、未知 grant/response_type 均拒绝。默认每 IP 120 次/分钟、每 client 300 次/分钟、每登录用户 30 次授权确认/分钟，可部署调小；429 携 Retry-After。code、token、secret、verifier、cookie、签名上下文、邮件及用户资料不得进入访问日志、trace、metrics 标签或审计原文。

#### 交付依赖与验收

1. App 先扩展 UC-APP-002/003/004/005 的 Version 依附 oauthRedirects 创建、编辑、审核与策略，再由 UC-APP-018 提供 Application＋channel 级稳定 identity/credential，UC-APP-007/019 负责发布检查与运行资格快照。
2. Auth 实现 UC-AUTH-014/015/017/018/019，门户与 Gateway 同步交付；UC-AUTH-016 是独立离线授权工作包，未启用时 discovery 必须去掉 refresh_token，拒绝 offline_access，不能部分宣称支持。
3. 初版最小生产 scope 装载 `openid`、`email`、`offline_access`：Auth 维护稳定语义/用户可读说明/映射；App 版本仍须声明并通过原有审核。资源 scope 必须有已交付资源服务、scope→audience→route 映射；USERINFO_PROFILE scope 必须有 UC028 已验证的一字段一 scope 映射和真实资料字段定义。不接受开发 fixture。生产 Catalog 装载能力是实现依赖，不需要先做在线 Catalog 管理 UC。
4. Gateway OAUTH2、OIDC_HTTP 与资源服务委托验证通过真实三方联合测试后显式启用。当前 ACTIVE 契约继续有效，本文不使旧实现自动具备新能力。

验收至少覆盖两种 client、confidential+PKCE、code/refresh 重放、nonce/state 错配、同一 clientId 的 Version/hostname/major 回调切换与未登记回调、登录前后 runtime tuple 变化、scope 越权、跨 major 历史授权保留、渠道授权隔离、仅新增 scope 重新 consent、同应用所有渠道/type 的 sub 一致及不同应用隔离、secret 轮换不撤销 grant/既有 token、App 停用、UserInfo 最小披露、HTTP/原生 gRPC/gRPC-Web，以及依赖故障时不转发。启用前还需实际 OIDC 客户端库互通测试；未通过认证不得宣称通过 OpenID Certification。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-001`（use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md）：目标与范围、调用者与输入、输出、主流程、异常流程、API 契约、测试与验收、非目标、变更记录
- `platform/contracts/auth-scope-catalog-v1.md`（docs 根级共享文档）：关联文档
- `platform/contracts/oauth-oidc-v1.md`（docs 根级共享文档）：客户端配置、标准 sector 注册与回调清单、标准依据

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md` | 130 | `ba199194713d` |
| `use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md` | 125 | `ba56267a4891` |
| `platform/contracts/auth-scope-catalog-v1.md` | 95 | `d7e2b937c86e` |
| `platform/contracts/oauth-oidc-v1.md` | 138 | `9c0b396eab0a` |
