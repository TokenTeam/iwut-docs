<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-036 --spec tools/brief-specs/UC-AUTH-036.json -->
# Brief — UC-AUTH-036：管理 Scope 定义与生命周期

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-036` 管理 Scope 定义与生命周期 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCP-006`–`BR-SCP-015`（10 条） |
| 外部引用 BR | `BR-OAU-002`，`BR-SCP-001`，`BR-UPF-002`、`BR-UPF-012`（来自 `UC-AUTH-001`、`UC-AUTH-005`、`UC-AUTH-014`、`UC-AUTH-028`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

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

2026-10-26 用户接受简化方案并授权修订及实现：复用 UC021 完整平台管理员身份，提供 Auth 管理 API、目录版本检查、原子审计与操作结果查询。不建设独立发布身份、专用签名、双人审批、发布控制面或治理 UI；CLI 如将来需要，仅为正常管理 API 客户端，不获得 Mongo 写权限。

本 UC 统一拥有定义登记、同义文案修正、启停、新语义替代与退役，以及 BR-SCP-006–015。UC001 保持内部只读，不扩展 v1 投影。原文件路径保留，撤销编号不重分配。退役为长期 disabled，不引入不可逆 RETIRED 状态。目录 revision 不是 consent 版本，不改历史 G、不迁移旧凭据、不扩大 refresh ceiling。

UC014 同步接受待提交 consent 展示绑定修订；UC035 仍 DRAFT，宿主协议、Console UI、Gateway 路由部署与真实跨系统验收独立交付。本工作包不授权部署或迁移旧系统；commit/push 按用户后续明确授权单独执行，本批后续仅获本地 commit 授权，不含 push。

### 参与者与依赖

操作人为 ACTIVE USER，使用 audience=`iwut-auth-center` 的可信 USER JWS；每个读写及操作查询均在 Auth 一致性边界在线复核 UC021 完整管理员集合、accountRevision 和可信身份版本，复用 UC029 方式。不增加第五项权限，不将 auth.platform-admin.manage 拆成可单独授予的目录权限。拒绝 service/OAuth 身份、直接 Session、自报 actor 或仅有 Mongo 凭据。

依赖 UC001 持久目录、UC021/010 管理身份、UC014–019 授权交集及 UC028 提供方映射。基线 Auth `8b803db`、API `27c9743`、App `d3f510e` 已有目录/全局 Auth fence/管理员 gate，缺正式管理 API/CAS/回执/展示绑定。无新 App provider 依赖。

### 输入与输出

```text
GetManagedScopeCatalog {}
ManagedScopeCatalog { revision: Int64, generatedAt: Instant, digest: String, scopes: ScopeDefinition[] }
ScopeDefinition { name, label, description, kind, audience, profileField, profileValueType, enabled }
ChangeScopeCatalog {
  operationId: String       // canonical lowercase UUID v4，调用者生成
  expectedRevision: Int64   // 必填、正数
  expectedDigest: String    // Get 返回的完整目录 SHA-256，小写 hex
  reason: String           // trim 后 1..1024 UTF-8 bytes
  changes: ScopeChange[]   // 1..32 项，同一 name 不可重复
}
ScopeChange = REGISTER { definition: ScopeDefinition, contract: String, providerEvidence: String }
            | CORRECT_TEXT { name, label, description }
            | SET_ENABLED { name, enabled: Bool }
GetScopeCatalogOperation { operationId: String }
ScopeCatalogOperation {
  operationId, requestDigest, actorAuthId, reason,
  outcome: APPLIED | NO_CHANGE,
  baseRevision, resultRevision, resultGeneratedAt, resultDigest, occurredAt
}
```

REGISTER 不接受 profileValueType，它由真实 Profile 定义派生。contract 为 1..4096 UTF-8 bytes 不可变权限契约（动作、数据/资源范围、副作用），providerEvidence 为 1..1024 bytes 的设计/实现/测试引用，登记时持久保存；文案/启停不得改它。首批既有定义的原文案及稳定映射保存为系统初始基线，不伪造历史人工审核。

name 沿用既有语法；完整目录首版保持既有最多 32 项限制（含 disabled），不因永久占名偷偷解除。label/description 为 trim 后 1..256 / 1..4096 UTF-8 bytes。摘要显式编码全部内部稳定字段/文案/状态并按 name 排序，必须包含 json:"-" 的 profileValueType；revision/time 另作前置条件，不放入内容摘要。请求摘要包含可信 actor 与全部命令字段。

### API 契约

独立 package `auth_center.v1.scope_management`，service `ScopeManagementService`，HTTP/JSON 与 native gRPC：

| 方法 | Auth 内部路径 | 响应 |
| --- | --- | --- |
| GetManagedScopeCatalog | POST `/v1/scope-catalog:get` | 200，完整管理目录 |
| ChangeScopeCatalog | POST `/v1/scope-catalog:change` | 200，终局回执 |
| GetScopeCatalogOperation | POST `/v1/scope-catalog/operations:get` | 200，原回执 |

均为 SESSION 路由，Gateway 前缀 `/auth-center`，Auth 仅接受可信 USER JWS。精确 full method 鉴权，无 package wildcard，不扩展 UC001 service read 权限。Gateway 实际清单另交付。128 KiB 正文、严格 ProtoJSON、禁止 query/压缩、拒绝未知/重复/null/非法 enum/oneof/presence；UTC Timestamp、int64 字符串、no-store。可信 actor 有界读写限额缺省每分钟 60/10。

`AUTH_SCOPE_MANAGEMENT_ENABLED` 缺省 false，开启要求用户端点、可信用户验证、完整管理员能力及持久 OAuth manifest 可用；不允许硬编码开发目录充当管理目录。

### 主流程

1. 验证身份并限额，在线复核完整管理员后才读目录或回执。
2. 修改在全局 Auth 事务内先查 operationId；同 actor/同完整摘要恢复原结果，异参/异 actor 拒绝。
3. 比较当前完整目录 revision/digest；陈旧请求即使目标碰巧相同仍冲突。
4. 应用严格类型化批次，验证全部生命周期、提供方与运行约束；任一失败全部拒绝。
5. 变化时目录 revision 增加一次，generatedAt 为服务端 UTC（Mongo 毫秒精度）；目录/审计/契约依据/回执同事务提交。no-op 保存一次 NO_CHANGE 回执及审计，不改目录版本/时间。
6. 确认提交才返回成功。提交未知返回不可用，使用原编号查询，不换编号自动重做；新动作先读取当前目录。

### 错误语义与运行约束

身份错误沿用 trusted-identity-v1。当前无完整管理资格 SCOPE_MANAGEMENT_FORBIDDEN（403/PERMISSION_DENIED）；非法输入 INVALID_SCOPE_MANAGEMENT_REQUEST（400/INVALID_ARGUMENT）；前置条件过期 SCOPE_CATALOG_CONFLICT（409/ABORTED）；ID 异参 SCOPE_OPERATION_CONFLICT（409/ABORTED）；回执不存在 SCOPE_OPERATION_NOT_FOUND（404/NOT_FOUND）；生命周期/提供方/依赖门禁 SCOPE_CHANGE_BLOCKED（409/FAILED_PRECONDITION）；版本耗尽 SCOPE_CATALOG_REVISION_EXHAUSTED（409/FAILED_PRECONDITION）；限流 SCOPE_MANAGEMENT_RATE_LIMITED（429/RESOURCE_EXHAUSTED）；数据损坏/存储故障/提交未知 SCOPE_MANAGEMENT_UNAVAILABLE（503/UNAVAILABLE）。不回显凭据或底层错误；开关关闭不恢复旧旁路。

### 验收与交付边界

1. 真实 USER JWS/full admin 读写/查询，普通/部分 bundle/Reviewer/Developer/service/OAuth/错误 audience/撤权旧 JWS/禁用均拒绝；撤权与变更 fence 竞争。
2. 类型限字段、未知/重复/删名/改义/改映射、未交付 provider、profile 别名/类型、保留名与容量边界；登记不自动提供能力。
3. 并发 CAS、陈旧 no-op、同值 no-op、同 ID重放/异参/异 actor、溢出、审计失败回滚、未知结果查询。完整目录/审计/回执原子，不靠退出码推断。
4. 首次基线唯一；重启不改文案/启停，清单新增不自动登记；目录丢失损坏失败关闭；写前 route/storage 验证，依赖项停用拒绝。生产不得保留旧更新旁路。
5. 真实 Mongo/生产 Wire/生成 HTTP+gRPC client 覆盖 UC001 与 OAuth 启停恢复；G/epoch/sub 不变，新名不扩旧 token/refresh。
6. consent 相关/无关文案变更、两标签页、无 presentation、grant/撤销竞争、明确同意/复用审计、回滚。
7. make check/race/真实 Mongo，独立 API 生成一致、brief/registry 静态检查。Gateway/Console 真正跨系统验收另跟踪，不将低层测试冒充真实 UI 证据。

后续 App/Console 联合验收保持：隔离环境通过正式 API 创建含实际 email 等 Scope 的待审 Version，真实审核详情加载后管理 API 停用，取回执/UC001 新快照，等待真实 App TTL/刷新证据，APPROVE 应 InvalidApplicationScope 且 Review PENDING。新编号/revision 恢复，显式重读确认再 APPROVE；独立 Review 验证停用期间人工 REJECT。不直改库/伪造快照/假定一次 sleep 证明全副本刷新；目录不可用、owner 失格、策略错误分别验证。Console 专用工作树本轮不改。

## 业务规则（UC-AUTH-036 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-006 -->
### BR-SCP-006：管理员管理与最小权限

所有方法复用 UC021/UC029 当前完整管理员在线复核；撤权/禁用后的旧 JWS 不可继续读写。无独立发布身份、双人审批、权限扩容、App/Console service 写权或 OAuth 运维 scope。actor 只来自可信 context。

跨应用修改需 reason。管理员审核文案同义与提供方依据，机器不能证明自然语言同义或代码不越权。登记/文案/启停分型，同名不混用，不提供任意 patch。明确创建并启用可同批，但须同时通过两类门禁。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-007 -->
### BR-SCP-007：目录 CAS、no-op 与原子提交

复用全局 Auth 事务 fence，先原回执再 CAS；两个基于同版本的不同操作即使改不同项也不自动合并。陈旧 no-op 冲突，revision 正 int64、检查溢出。非 no-op 仅增加一次版本，同值不改版本/时间。

目录、不可变审计、契约登记与回执同事务；审计失败回滚。重放不增 revision/审计；后续目录改变不影响原回执，但原结果不证明仍是当前状态。事务重试重新验证管理员及前置条件。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-008 -->
### BR-SCP-008：可核验审计与未知写结果

独立 Auth-owned append-only 审计/回执保存 actorAuthId、operationId、请求摘要、reason、逐项前后定义、base/result revision、resultGeneratedAt/resultDigest、occurredAt；不含凭据/邮箱/用户资料。首版不自动清理，不建归档或永久墓碑；唯一索引占用 operationId，保留期间不可复用。未来清理需先定义恢复/重试期限，不擅加 TTL。

超时/未知提交返回不可用，不称成功或确定失败。结果读 NOT_FOUND 仅表示该检查点未见回执，不保证在途事务不会提交；保留原编号查询，不换编号盲重做。同原编号/请求可恢复，但仍检查当前管理员资格。冲突/非法请求不占用编号；仅 APPLIED/NO_CHANGE 是已提交终局结果。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-009 -->
### BR-SCP-009：启动旁路关闭与前向补偿

manifest 改为已交付提供方清单，不能重启覆盖 live enabled/文案。全新系统仅在从未初始化时按审核 manifest 幂等 provision 基线，在同一全局事务写目录/系统基线审计/持久初始化标记。已有目录只读验证，绝不 SeedCatalog 更新；初始化后缺失/损坏拒绝启动，不静默重建，不迁移旧系统。

启动验证持久定义与本实例清单的 stable name/kind/audience/profile 映射/类型匹配；缺处理方则不 ready。数据库文案/启停为权威，不与初始值强行一致；清单新项不自动注册，持久目录允许是清单子集。首次 route/profile/storage/resource-ready 约束先纯验证，后 provision，避免先写库后启动失败。

REGISTER 只允许本实例真实已交付清单的精确定义，不接受任意 RESOURCE audience 自报；profile 来自真实字段目录。结果必须满足当前 UC030 storage.read/write 和所有 resource routes 约束；导致重启不一致的停用拒绝，解除依赖需独立组合交付。首次隔离验收可选 email，避开必需 storage/route scopes。

全部副本使用一致提供方清单，正式变更前撤除旧 SeedCatalog writer 是部署门禁，不声称本次已替运营者完成。恢复用最新 revision/新编号前向操作，不回滚数据库或 generatedAt；旧二进制回滚不获得目录写权。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-010 -->
### BR-SCP-010：消费边界与既有授权规则引用

目录权威/完整投影/enabled/requestable/稳定名引用 [BR-SCP-001–005](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#业务规则)。实际权限仍按 [UC014/BR-OAU-002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-002)、UC015–019 与 UC028 的 token.scopes∩G∩D∩C；本 UC 不改 G/revocationEpoch，不恢复过期/撤销材料。

App 只消费 UC001 name/requestable/revision/generatedAt；缓存窗口由 [App ADR001](../../app-center/adr/ADR-001-scope-catalog-cache.md#第一阶段缓存) 拥有（当前缺省 5m），无广播或跨库原子承诺。Auth 当前检查不等待 App TTL。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-011 -->
### BR-SCP-011：已登记 Scope 的稳定权限契约

首次登记永久占名，动作/数据与资源边界/kind/audience/字段映射类型/副作用固定。扩大或缩小契约、更换意义须新 name，不借 description/handler 重构/返回更多字段绕过。内部重构、修复越契约披露保持原契约；用户资料值变化或既有年级计算不是定义变化。

REGISTER 的 contract/providerEvidence 不可变；系统基线保留原定义来源，不补造人工审核。机器固定 stable metadata 与登记依据，管理员按设计/测试判断同义与真实实现匹配，摘要不证明行为正确。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-012 -->
### BR-SCP-012：定义登记与启用门禁

新项需名称未占用、契约完整、真实提供方及越权拒绝依据；disabled 也不跳过。name 不生成能力。openid/email/offline_access/campus.whut 保留名遵守原协议/校园用例，不允许通用重新定义。

资料一字段一 Scope、精确 profile.<fieldKey>，固定真实类型，引用 [UC028/BR-UPF-012](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-012) 与 [UC005/BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。不得 .v2 别名映射旧字段。RESOURCE 须有本部署清单和资源约束，不靠 readiness 布尔或示例路由造能力。

同名 REGISTER 即使同值也拒绝。CORRECT_TEXT 仅 label/description，SET_ENABLED 仅 enabled，未知名拒绝。删除、重命名、kind/audience/field/type/contract 修改与独立 requestable 写入无入口。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-013 -->
### BR-SCP-013：文案修正与同意展示一致性

同义文案修正保存前后值/原因，不改 G/grant revision/epoch/token，不让所有用户重同意，不把不可解释旧文案修成更广权限。

待提交 consent 绑定实际请求 R 的定义/文案摘要及展示凭证。View 生成新不可猜 presentation 标识并保存证据；Confirm 提交页面标识，最终事务同时校验保存标识、当前 R 定义摘要、Session/CSRF/App/grant。相关变化返回既有 interaction_changed，显式重读后确认；无关 Scope 变化不冲突。另一标签页 View 后旧表单不能借最新服务器快照通过。

审计保存实际展示证据及明确确认/复用历史同意来源，不含资料值，不给旧 grant 批量补历史快照。UC014 同步接受；UC035 引用共享规则但仍 DRAFT、不实现宿主协议。旧无证据交互须重新 View；静默复用 G 仍按原 prompt 规则，不凭空新增权限。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-014 -->
### BR-SCP-014：新语义替代与重新授权

新语义新 name，替代关系仅说明，不参与授权匹配，禁 alias/前缀/superset/old→new 推导。App 新 Version 明确声明审核，用户 UC014 同意新项。旧 G/code/token/family 不获得新项；后来同意也不扩大旧 family ceiling。

兼容期可同启旧新定义，各自提供原契约；期限由实际提供方决定，无默认自动迁移。不改账号/pairwise sub/渠道边界。

<!-- 权威位置: use-cases/UC-AUTH-036-release-scope-enablement-changes.md#br-scp-015 -->
### BR-SCP-015：停用、退役与删除边界

暂停/退役均 enabled=false，完整投影保留旧定义/name，requestable=false；无不可逆状态或仅旧应用的第二开关。风险阻断无需等全部 App 迁移。停用不删 G/审计/资料/KV，不追回已披露数据。

恢复仅同契约，经新 revision 操作，不复活过期/撤销材料。未来若要不可恢复退役，另审写约束，不偷偷增加第二授权状态。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-014`

<!-- 权威位置: use-cases/UC-AUTH-014-authorize-application.md#br-oau-002 -->
### BR-OAU-002：显式同意与最小授权

令 D=当前批准版本 requiredScopes∪optionalScopes，R=本次请求 scopes，S=用户本次选择；必须 requiredScopes⊆R⊆D∩C，S 包含 requiredScopes 且 S⊆R。登录必需 openid；不允许用“不选 optional”偷增其他权限。无法接受必需权限时用户仍可拒绝全部。

Grant 的业务主键为 `(authId, applicationId, channel)`，Mongo 必须以这三个字段建立复合唯一约束；grantId 仅为稳定、不透明的引用 ID，供 token 和本人管理接口引用。authId 来自当前 Session，applicationId/channel 来自 App 确认的 client 归属，不接受客户端自行指定授权归属。同一 Application 同一 channel 的 PUBLIC/CONFIDENTIAL client 及各 RPC major 共享一个 grant；TEST/GREY/STABLE 分别保存，不因跨渠道 sub 相同而共享授权。clientId、major、Version 均不进入 grant 唯一键。保存历史同意集合 G=grantedScopes、revision、revocationEpoch（初始 1）和 status；发起 clientId 与运行 tuple 记录在交互及审计中。

授权页明确展示应用和渠道，并说明本次同意可由该渠道的两类 client 复用。共享的是用户同意；每个 client 仍须分别满足自己的当前批准版本、运行资格和凭据证明，code/token/family 不跨 client 使用。

首次同意保存 S；以后只展示本次尚未同意的 `S−G`，明确同意后更新为 `G∪S`。若本次 R 已包含于 G 且满足当前 D∩C，可按 prompt 规则静默取得本次需要的 S。prompt=consent 仍展示确认，offline_access 的专用规则保持有效。不能把历史 G 全部签入 token；S 必须是当前请求与当前允许集合的子集。

Version、major 或 Publication 变化不删除 G，不因当前 D 变小写回 `G∩D`，也不改变 grant 的 revision/epoch。某个 scope 未来再次由批准版本声明，只要用户未主动撤回，仍可复用原同意。Catalog enabled=false 同样不删除 G 或推进 grant revision/revocationEpoch；恢复后只可在仍有效的凭据原范围、G 与当前 D 内继续使用，不能复活已过期或被用户撤销的凭据，不能自动扩大停用期间新发 token 的范围。恢复同名含义必须保持 Catalog 的稳定语义。所有资源实际权限为 `token.scopes ∩ G ∩ D ∩ C`，不满足本次路由的权限时拒绝该操作，而非因为 token 另含一个暂不可用 scope 就拒绝全部操作。

新增同意递增 revision（OCC/审计），不递增 revocationEpoch，不使已签发凭据失效；旧 token 不会因此自动获得新 scope。用户显式撤回按 UC018 改变 G/status 并递增两者，旧 code/token/family 通过 epoch 失效。重新同意也不能复活已撤销代的凭据。交互提交仍比较展示时 revision，竞争时要求刷新页面，不能覆盖用户后来决定。

### 来自 `UC-AUTH-001`

<!-- 权威位置: use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001 -->
### BR-SCP-001：Auth 权威所有权

Auth Center 是 Scope Catalog、ScopeDefinition 和 catalog revision 的唯一权威来源。消费方 cache、测试 fixture、配置文件副本或历史快照都不能独立修改或替代该权威目录。

### 来自 `UC-AUTH-005`

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002 -->
### BR-UPF-002：平台字段定义与稳定标识

Auth 拥有共享 ProfileFieldDefinition：`key`、`label`、`description`、`valueType`、`constraints` 五项均存在；label 和 description 是非空有效 UTF-8 文本。字段定义不包含某位用户的值，不要求每位用户填写，也不隐含应用读取授权。

key 在目录中唯一，长度为 1–128 ASCII bytes，符合 `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$`。按完整原始字符串比较；点只用于名称组织，不表示对象路径或权限继承。

已发布 key、业务含义、valueType 和 constraints 在首版保持不变，key 不更名、不复用。展示文案可以修正但不改变含义。首版允许新增定义，不提供在线停用、删除或修改已发布校验规则的管理命令；这些变化由后续用例定义兼容和数据清理规则。

首版定义可由 Auth 自有、纳入版本管理的部署配置显式装载；启动时验证整个目录的唯一性、语法和类型约束，无效配置阻止该服务实例接流量。发布流程保留全部既有定义及其校验含义，不用客户端提交的 schema、测试 fixture 或 Scope 列表代替字段目录。一次 set 校验使用一个完整一致的定义视图，定义不完整或损坏时失败关闭。

### 来自 `UC-AUTH-028`

<!-- 权威位置: use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-012 -->
### BR-UPF-012：一字段一 Scope 的稳定映射

只有 Auth OAuth 目录中显式 `kind=USERINFO_PROFILE` 的条目可以披露 UC005 资料。每个条目精确映射一个 field key，scope 名固定为 `profile.<fieldKey>`，audience 必须为空；同一个 field key 和 scope 名均只能出现一次。

启动装载必须把每个映射与同一次完整 ProfileFieldDefinition 视图核对，并将其 valueType 固定进 Auth 持久 Scope Catalog。未知 field key、名称不匹配、重复映射、错误 kind/audience、缺少 consent 文案或类型不一致均拒绝启动。运行期不从 App 声明、用户资料内容、测试 fixture 或旧 Auth 实现推导映射。

已持久化 scope 的 kind、profileField 和 valueType 不得原地改变，字段 key 也不得改名或复用。新增可披露字段必须新增字段定义和新的 scope；不得给既有 scope 追加第二个字段。首版不提供在线删除或改绑命令；`enabled` 的变更仍遵循 BR-SCP-004。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

UC038 新增已接受的本人读取 `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions`，GET `/v1/users/me/script-permissions`，空请求返回本人四项状态和共享版本。Gateway 采用 SESSION → Auth audience、ADMIN Console surface，原生 gRPC/HTTP/gRPC-Web 按精确方法接入。该本人方法不要求管理或脚本 permission，目标管理方法沿原规则鉴权。开关、无权限与失败区分唯一见 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-004)。


UC039 的 `ManagedUserSearchService/SearchUsers` 使用 `POST /v1/managed-users:search` 和原生 gRPC，业务及最小披露见 [UC039](../use-cases/UC-AUTH-039-search-users-for-administration.md)。Gateway 接入时使用 SESSION → Auth audience，限定 Admin surface。UC027 的固定管理和本人公开范围已接受增加精确 `app.application.search`，沿用现有方法及线格式。


UC038 的目标脚本权限查询和授撤方法按 [UC038 API 契约](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#api-契约) 固定 HTTP 和原生 gRPC。Gateway 按精确 RPC 接入 Admin 管理路由，采用 SESSION → Auth audience USER JWS，管理权限由 Auth 复核。旧 `ScriptMaintainerPermissionService` 及其两条 HTTP 路由退役。

2026-10-12 下表仅已交付基线。密码管理/恢复、默认密码登录已展开 UC033/034 DRAFT 和 auth-password-v1 草案，未注册真实入口；旧 REGISTER/BIND/凭据撤销、注销 Prepare/app.close Complete 须同步密码与防旁路门禁，新修订未实施，不提前启用或登记虚构公网清单。

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/device-logins` | AuthenticationService/BeginDeviceLogin | DIRECT | 200 |
| POST | `/v1/device-logins/{operation_id}/completion` | AuthenticationService/CompleteDeviceLogin | DIRECT | 201 |
| DELETE | `/v1/sessions/current` | AuthenticationService/RevokeCurrentSession | DIRECT | 200 |
| DELETE | `/v1/users/me/credentials/{credential_id}` | AuthenticationService/RevokeOwnCredential | DIRECT | 200 |
| GET | `/v1/users/me/profile` | UserProfileService/GetOwnProfile | SESSION | 200 |
| PATCH | `/v1/users/me/profile` | UserProfileService/EditOwnProfile | SESSION | 200 |
| GET | `/v1/user-profile-schema` | UserProfileService/GetProfileEditingSchema | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/ManageReviewerPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/GetReviewerPermission | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | ReviewerPermissionService/ManageApplicationReviewPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-review-permissions` | ReviewerPermissionService/GetApplicationReviewPermissions | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | ApplicationOperationsPermissionService/ManageApplicationOperationsPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-operation-permissions` | ApplicationOperationsPermissionService/GetApplicationOperationsPermissions | SESSION | 200 |
| GET | `/v1/academic-year-policy/schedule` | AcademicYearPolicyService/GetAcademicYearSchedule | SESSION | 200 |
| PUT | `/v1/academic-year-policy/schedule/next-rollover` | AcademicYearPolicyService/UpdateNextAcademicYearRollover | SESSION | 200 |
| DELETE | `/v1/users/me/application-user-storage/{application_id}` | ApplicationUserStorageService/ClearOwnApplicationUserStorage | SESSION | 200 |

原 `/v1/registrations` 和 completion 路径不注册，旧 BeginUserRegistration/CompleteUserRegistration RPC 返回 UNIMPLEMENTED；不重定向、不代为发起注册，也不因启用用户入口恢复旧方法。

UC011 是唯一注册入口，三个 DIRECT 路由的字段及 Session 例外见[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](../../platform/contracts/auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AcademicYearPolicyService package 为 `auth_center.v1.academic_year_policy`，两个方法由 Auth 在线复核当前完整平台管理员资格；精确时间、递推、并发和审计语义唯一见 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md)。管理入口由独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED` 控制且默认关闭；关闭管理入口不影响 Auth 内部消费已 provision 的时间表。

ApplicationUserStorageService package 为 `auth_center.v1.application_user_storage`。本人清除使用 SESSION 身份，`application_id` 仅由路径绑定，一次删除该用户与 Application 的 TEST/GREY/STABLE 数据，不返回应用 key/value。第三方读写另使用 `POST /v1/application-user-storage:batchGet` 与 `POST /v1/application-user-storage:mutate`；两者是 Auth 直接验证 opaque OAuth Bearer token 的 HTTP-only 资源端点，不经 SESSION 转换、不生成原生 gRPC 第三方方法。三个入口均由 `AUTH_APPLICATION_USER_STORAGE_ENABLED` 控制且默认关闭，精确语义见 [UC030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

UC036 的 `auth_center.v1.scope_management.ScopeManagementService` 提供三个 SESSION 管理方法：POST `/v1/scope-catalog:get`、POST `/v1/scope-catalog:change`、POST `/v1/scope-catalog/operations:get`，分别为 GetManagedScopeCatalog、ChangeScopeCatalog、GetScopeCatalogOperation。独立 `AUTH_SCOPE_MANAGEMENT_ENABLED` 缺省关闭，在线复核当前完整平台管理员，不增加权限或 service 写权。正文上限 128 KiB；严格解码/no-store/原生 gRPC；精确语义唯一引用 [UC036](../use-cases/UC-AUTH-036-release-scope-enablement-changes.md#api-契约)。UC001 内部 ScopeCatalog 只读方法不变，Gateway 实际路由清单另行交付，不因本文登记自动开放。

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。学年时间表 PUT 只接受 nextRolloverAt、expectedRevision 和 reason，不接受客户端提交 currentAcademicYear。
- 设备登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 和应用存储清除的 `application_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB，应用用户存储固定 16 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

#### 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖修订后的资料/认证方法及退役无邮箱路径拒绝、Reviewer/应用运维权限方法、两个学年时间表管理方法及应用用户存储 HTTP/本人清除方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

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

- `UC-AUTH-036`（use-cases/UC-AUTH-036-release-scope-enablement-changes.md）：变更记录
- `UC-AUTH-014`（use-cases/UC-AUTH-014-authorize-application.md）：目标与范围、输入与输出、主流程、验收场景、依赖与实现边界、变更记录
- `UC-AUTH-001`（use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md）：目标与范围、调用者与输入、输出、主流程、异常流程、API 契约、测试与验收、非目标、变更记录
- `UC-AUTH-005`（use-cases/UC-AUTH-005-edit-own-user-profile.md）：目标与范围、参与者与前置条件、输入、输出、主流程、持久化与返回说明、异常与 transport 映射、API 与交付依赖、测试与验收、非目标、变更记录
- `UC-AUTH-028`（use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md）：目标与范围、参与者与依赖、输入与输出、主流程、验收场景、实现依赖与交付边界、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC027 本人运维权限读取、UC020 同账号 Session 管理
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-036-release-scope-enablement-changes.md` | 169 | `832ac0def1ba` |
| `use-cases/UC-AUTH-014-authorize-application.md` | 89 | `b854c65e519a` |
| `use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md` | 126 | `7d34b0245dd1` |
| `use-cases/UC-AUTH-005-edit-own-user-profile.md` | 340 | `a2e87a33efad` |
| `use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md` | 147 | `b50a252bf8ae` |
| `platform/contracts/auth-center-api-routing.md` | 171 | `ec86209bbd44` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
