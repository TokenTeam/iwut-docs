# UC-AUTH-028：向第三方应用披露用户资料字段

状态：`ACCEPTED`

## 目标与范围

持有有效 OAuth access token 的第三方应用，通过既有 OIDC UserInfo 读取用户明确授权的、当前仍允许披露的 UC-AUTH-005 资料字段。每个可披露字段使用一个独立且稳定的 OAuth scope；新增字段不能借用旧 scope 扩大历史 consent。

本用例扩展 [UC-AUTH-017](UC-AUTH-017-get-oidc-user-info.md) 的 UserInfo 最小投影，不新增资料查询端点，不允许应用在请求中提交任意 field key，也不把本人资料接口、平台 Session、ID Token 或内部 authId 变成第三方资料凭据。邮箱继续由 UC011/017 的激活邮箱事实提供，不从资料 KV 投影。

字段值仍是用户主动提供、平台只校验格式的资料；第三方读取不把它变成学校或平台验证事实。ApplicationUserStorage、公开个人主页、管理员代查、资料搜索和历史快照不在本用例范围。

## 参与者与依赖

- 用户通过 UC014 对应用当前 Version 已审核声明的 scope 明确同意；grant、code、access/refresh token、撤销及三渠道资格继续由 UC014–018 定义。
- App Center 继续只消费 [Auth Scope Catalog v1](../../platform/contracts/auth-scope-catalog-v1.md) 的 `name/requestable` 投影，不读取资料字段目录，也不决定字段到 scope 的映射。
- Auth 同时拥有 UC005 的 ProfileFieldDefinition 目录、OAuth 权威 Scope Catalog、用户 profile、grant 与 access token；映射在 Auth 启动装载时闭合。
- 第三方应用只调用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md) 的 `GET/POST /userinfo`，并按现有规则核对 pairwise `sub`。

实现依赖已经闭合：UC005 提供有界、带类型的 profile 快照；UC001 提供持久 Scope Catalog；UC014–018 已提供审核、consent、有效权限交集、撤销和 UserInfo 在线读取。无需新增跨服务 RPC 或修改 Scope Catalog v1 线格式。

## 输入与输出

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

## 主流程

1. 按 UC017 在线验证 access token、family、grant、Application/渠道/Version 当前资格、Scope Catalog 和 UserInfo audience，并取得有效 scope 集合 E 与 pairwise sub。
2. 从当前权威目录选出 E 中 `kind=USERINFO_PROFILE` 的 scope；再次验证其名称、field key 和已装载类型元数据完整一致。
3. 若没有有效资料 scope，保持 UC017 的现有最小响应，不读取或返回 profile。
4. 在同一 Auth 一致性边界读取当前 ACTIVE USER 与完整 profile，拒绝缺失或损坏结构；只按选中定义查找对应 key。
5. 省略用户当前未填写的字段；把存在且类型匹配的值投影到 `iwut_profile`。任一目标值结构或类型不一致时整次读取失败关闭，不返回部分资料。
6. 返回 no-store 的标准 UserInfo JSON；不在日志、trace、metrics 或审计正文记录字段值。

## 业务规则

<a id="br-upf-012"></a>
### BR-UPF-012：一字段一 Scope 的稳定映射

只有 Auth OAuth 目录中显式 `kind=USERINFO_PROFILE` 的条目可以披露 UC005 资料。每个条目精确映射一个 field key，scope 名固定为 `profile.<fieldKey>`，audience 必须为空；同一个 field key 和 scope 名均只能出现一次。

启动装载必须把每个映射与同一次完整 ProfileFieldDefinition 视图核对，并将其 valueType 固定进 Auth 持久 Scope Catalog。未知 field key、名称不匹配、重复映射、错误 kind/audience、缺少 consent 文案或类型不一致均拒绝启动。运行期不从 App 声明、用户资料内容、测试 fixture 或旧 Auth 实现推导映射。

已持久化 scope 的 kind、profileField 和 valueType 不得原地改变，字段 key 也不得改名或复用。新增可披露字段必须新增字段定义和新的 scope；不得给既有 scope 追加第二个字段。首版不提供在线删除或改绑命令；`enabled` 的变更仍遵循 BR-SCP-004。

<a id="br-upf-013"></a>
### BR-UPF-013：审核、同意与当前有效集合共同授权

资料 scope 与其它 OAuth scope 一样，必须先被 ApplicationVersion 声明并通过 App 审核，再由用户在 consent 中逐项同意。有效披露只取 access token scope、grant G、当前 Version 许可、Auth 当前 enabled 目录 C 的交集 E；字段存在、用户曾填写或 App 请求 field key 本身都不产生权限。

`/userinfo` 仍要求 `openid` 和 UserInfo audience。资料 scope 不能单独把不含 openid 的请求变成有效 OIDC 请求。新增资料 scope 对已有 grant 是新权限，遵循 UC014 的重新 consent；不会扩张旧 access token。Scope 停用或 Version 移除后立即停止投影，但不删除 G；恢复后仅在原凭据仍满足既有期限、撤销和 scope ceiling 时恢复。

用户在已授予某字段 scope 后新增或修改该字段，会使之后的 UserInfo 读取看到当前值；这是既有字段授权下的数据变化，不是新增 scope。资料编辑本身不创建 grant、不替应用同意 scope，也不恢复已撤销授权。

<a id="br-upf-014"></a>
### BR-UPF-014：固定 claim 与最小当前值投影

所有资料字段只进入顶层固定 claim `iwut_profile`，其值为 field key 到标量的 JSON object。field key 不提升为顶层 OIDC claim，不允许映射覆盖 `sub`、`email`、`email_verified` 或其它标准/平台 claim；应用不能请求返回任意 key 或全量 profile。

只返回 E 对应且用户当前实际保存的值。缺失字段被省略；全部缺失时省略整个 `iwut_profile`。不返回 null、默认值、历史值、目录中其它字段、profile revision 或更新时间。输出保留 UC005 的逻辑值；不 trim、不规范化、不把 DATE 转成带时区时间，也不从一个字段推导另一个字段。

应用必须把这些值视为用户自述数据，并按普通数据/文本安全处理；scope label、description 和字段目录文案不是 UserInfo 数据。资料中的 `email` 或相似 key 仍不能替代 UC011 的激活邮箱及 `email_verified`。

<a id="br-upf-015"></a>
### BR-UPF-015：在线当前读取与生命周期传播

UserInfo 每次读取当前 profile，不把资料复制进 grant、code、access/refresh token、ID Token 或 ApplicationUserStorage。字段修改或删除在后续成功读取中即时反映；删除不撤销 scope，scope 撤销也不删除用户资料。

账号禁用/CLOSED、Application 关闭、grant/family/token 撤销、渠道发布或资格丢失继续先按 UC017/022/025/026 拒绝整个 UserInfo。资料读取与这些 Auth 本地事实使用既有认证事务栅栏和一致检查点；撤销提交后开始的读取不能返回资料。跨 App 数据仍由 Application 级 pairwise sub 隔离，同一 Application 的既有 sub 稳定规则不变。

<a id="br-upf-016"></a>
### BR-UPF-016：损坏、依赖故障与隐私边界

只有实际需要资料 scope 时才要求 profile 和映射可读。目标 profile 缺失、revision/updatedAt/entries 损坏、重复 key、未知存储类型、目标值与固定 valueType 不符、目录映射损坏或数据库故障，均返回 UserInfo 依赖失败；不得降级为“字段未填写”、缓存值或部分成功。正常未填写不是错误。

响应使用 `Cache-Control: no-store`，并沿用 UC017 的 `invalid_token`、`insufficient_scope` 与 `temporarily_unavailable` 外部错误边界，不向应用区分用户是否填写某个未授权字段。常规日志、trace、metrics 标签和 OAuth 审计不得记录 profile field value；可记录 requestId、clientId、scope 名集合、结果类别和耗时，但不能记录 access token、authId 与字段值组合。

## 验收场景

- 两个字段分别映射两个 scope；只同意其中一个时 `iwut_profile` 只含对应 key，应用请求体中的额外 field key 不存在也不能扩大结果。
- 新增第二个字段/scope 后，旧 grant 与旧 access token 不获得该字段；完成应用审核、用户新增 consent 并取得新 token 后才可读取。
- 用户未填写、之后填写、修改和删除字段时，既有有效授权分别表现为省略、出现、更新和再次省略；profile revision 不出现在响应。
- STRING、INTEGER、BOOLEAN、DATE 逐类保持 JSON 类型；零、false 与合法日期不被误判为缺失。
- email scope 与资料中相似 key 分离；只有当前激活邮箱产生 `email/email_verified=true`。
- scope disabled、Version 移除、grant 撤回、family/token 失效、三渠道资格丢失、账号禁用和 Application tombstone 均按当前 OAuth 规则拒绝或省略，恢复不越过原 token ceiling。
- ProfileFieldDefinition 不存在、同 scope 改绑 field、valueType 漂移、重复映射和非法 USERINFO_PROFILE audience 在启动时失败；持久目录损坏和目标 profile 类型损坏在读取时失败关闭。
- openid/email-only 行为保持与 UC017 一致；标准 OIDC 客户端仍能忽略未知 `iwut_profile` claim，并验证同一 sub。
- Scope Catalog v1 继续只输出 name/requestable；实际 App Center 可声明、审核并发布资料 scope，无需理解 field key 或新 Proto 字段。

## 实现依赖与交付边界

本工作包修改 Auth Center 服务与其配置/测试，不需要修改独立 API Proto：UserInfo 是标准 JSON 端点，Scope Catalog v1 的既有投影足以让 App Center 消费。实现应扩展持久 OAuth Scope 模型、启动交叉校验、当前 profile 解码、UserInfo/Discovery 投影，以及真实 Mongo/生产 Wire/实际 App 联合验收。

生产启用前必须由部署配置显式装载真实 ProfileFieldDefinition 和对应 USERINFO_PROFILE scope，并完成 consent 文案与 App 审核策略验收；仓库示例和测试字段不构成生产收集清单。官方门户必须逐项展示资料 scope 文案。Gateway 继续透传既有 `/userinfo`，无需解析 `iwut_profile`。

ApplicationUserStorage、字段目录在线管理、资料值真实性验证、敏感字段分级/强制二次确认、客户端资料编辑 UI 和第三方 SDK 类型封装分别后续设计。没有生产映射时功能保持关闭；不得把旧 Auth Center 的 `scope_keys`、任意字段过滤或 per-app storage 接口迁入本实现。

## 变更记录

- 2026-10-08：提出一字段一 scope、固定 `iwut_profile` claim 和 Auth 启动交叉校验方案；核对 UC005/001/014–018、共享契约及当前 Auth HEAD 后确认无需新跨服务 RPC 或 Proto，设计接受。
