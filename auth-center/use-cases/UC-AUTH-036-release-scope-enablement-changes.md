# UC-AUTH-036：管理 Scope 定义与生命周期

状态：`ACCEPTED`

## 目标与范围

2026-10-26 用户接受简化方案并授权修订及实现：复用 UC021 完整平台管理员身份，提供 Auth 管理 API、目录版本检查、原子审计与操作结果查询。不建设独立发布身份、专用签名、双人审批、发布控制面或治理 UI；CLI 如将来需要，仅为正常管理 API 客户端，不获得 Mongo 写权限。

本 UC 统一拥有定义登记、同义文案修正、启停、新语义替代与退役，以及 BR-SCP-006–015。UC001 保持内部只读，不扩展 v1 投影。原文件路径保留，撤销编号不重分配。退役为长期 disabled，不引入不可逆 RETIRED 状态。目录 revision 不是 consent 版本，不改历史 G、不迁移旧凭据、不扩大 refresh ceiling。

UC014 同步接受待提交 consent 展示绑定修订；UC035 仍 DRAFT，宿主协议、Console UI、Gateway 路由部署与真实跨系统验收独立交付。本工作包不授权部署或迁移旧系统；commit/push 按用户后续明确授权单独执行，本批后续仅获本地 commit 授权，不含 push。

## 参与者与依赖

操作人为 ACTIVE USER，使用 audience=`iwut-auth-center` 的可信 USER JWS；每个读写及操作查询均在 Auth 一致性边界在线复核 UC021 完整管理员集合、accountRevision 和可信身份版本，复用 UC029 方式。不增加第五项权限，不将 auth.platform-admin.manage 拆成可单独授予的目录权限。拒绝 service/OAuth 身份、直接 Session、自报 actor 或仅有 Mongo 凭据。

依赖 UC001 持久目录、UC021/010 管理身份、UC014–019 授权交集及 UC028 提供方映射。基线 Auth `8b803db`、API `27c9743`、App `d3f510e` 已有目录/全局 Auth fence/管理员 gate，缺正式管理 API/CAS/回执/展示绑定。无新 App provider 依赖。

## 输入与输出

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

## API 契约

独立 package `auth_center.v1.scope_management`，service `ScopeManagementService`，HTTP/JSON 与 native gRPC：

| 方法 | Auth 内部路径 | 响应 |
| --- | --- | --- |
| GetManagedScopeCatalog | POST `/v1/scope-catalog:get` | 200，完整管理目录 |
| ChangeScopeCatalog | POST `/v1/scope-catalog:change` | 200，终局回执 |
| GetScopeCatalogOperation | POST `/v1/scope-catalog/operations:get` | 200，原回执 |

均为 SESSION 路由，Gateway 前缀 `/auth-center`，Auth 仅接受可信 USER JWS。精确 full method 鉴权，无 package wildcard，不扩展 UC001 service read 权限。Gateway 实际清单另交付。128 KiB 正文、严格 ProtoJSON、禁止 query/压缩、拒绝未知/重复/null/非法 enum/oneof/presence；UTC Timestamp、int64 字符串、no-store。可信 actor 有界读写限额缺省每分钟 60/10。

`AUTH_SCOPE_MANAGEMENT_ENABLED` 缺省 false，开启要求用户端点、可信用户验证、完整管理员能力及持久 OAuth manifest 可用；不允许硬编码开发目录充当管理目录。

## 主流程

1. 验证身份并限额，在线复核完整管理员后才读目录或回执。
2. 修改在全局 Auth 事务内先查 operationId；同 actor/同完整摘要恢复原结果，异参/异 actor 拒绝。
3. 比较当前完整目录 revision/digest；陈旧请求即使目标碰巧相同仍冲突。
4. 应用严格类型化批次，验证全部生命周期、提供方与运行约束；任一失败全部拒绝。
5. 变化时目录 revision 增加一次，generatedAt 为服务端 UTC（Mongo 毫秒精度）；目录/审计/契约依据/回执同事务提交。no-op 保存一次 NO_CHANGE 回执及审计，不改目录版本/时间。
6. 确认提交才返回成功。提交未知返回不可用，使用原编号查询，不换编号自动重做；新动作先读取当前目录。

## 业务规则

<a id="br-scp-006"></a>
### BR-SCP-006：管理员管理与最小权限

所有方法复用 UC021/UC029 当前完整管理员在线复核；撤权/禁用后的旧 JWS 不可继续读写。无独立发布身份、双人审批、权限扩容、App/Console service 写权或 OAuth 运维 scope。actor 只来自可信 context。

跨应用修改需 reason。管理员审核文案同义与提供方依据，机器不能证明自然语言同义或代码不越权。登记/文案/启停分型，同名不混用，不提供任意 patch。明确创建并启用可同批，但须同时通过两类门禁。

<a id="br-scp-007"></a>
### BR-SCP-007：目录 CAS、no-op 与原子提交

复用全局 Auth 事务 fence，先原回执再 CAS；两个基于同版本的不同操作即使改不同项也不自动合并。陈旧 no-op 冲突，revision 正 int64、检查溢出。非 no-op 仅增加一次版本，同值不改版本/时间。

目录、不可变审计、契约登记与回执同事务；审计失败回滚。重放不增 revision/审计；后续目录改变不影响原回执，但原结果不证明仍是当前状态。事务重试重新验证管理员及前置条件。

<a id="br-scp-008"></a>
### BR-SCP-008：可核验审计与未知写结果

独立 Auth-owned append-only 审计/回执保存 actorAuthId、operationId、请求摘要、reason、逐项前后定义、base/result revision、resultGeneratedAt/resultDigest、occurredAt；不含凭据/邮箱/用户资料。首版不自动清理，不建归档或永久墓碑；唯一索引占用 operationId，保留期间不可复用。未来清理需先定义恢复/重试期限，不擅加 TTL。

超时/未知提交返回不可用，不称成功或确定失败。结果读 NOT_FOUND 仅表示该检查点未见回执，不保证在途事务不会提交；保留原编号查询，不换编号盲重做。同原编号/请求可恢复，但仍检查当前管理员资格。冲突/非法请求不占用编号；仅 APPLIED/NO_CHANGE 是已提交终局结果。

<a id="br-scp-009"></a>
### BR-SCP-009：启动旁路关闭与前向补偿

manifest 改为已交付提供方清单，不能重启覆盖 live enabled/文案。全新系统仅在从未初始化时按审核 manifest 幂等 provision 基线，在同一全局事务写目录/系统基线审计/持久初始化标记。已有目录只读验证，绝不 SeedCatalog 更新；初始化后缺失/损坏拒绝启动，不静默重建，不迁移旧系统。

启动验证持久定义与本实例清单的 stable name/kind/audience/profile 映射/类型匹配；缺处理方则不 ready。数据库文案/启停为权威，不与初始值强行一致；清单新项不自动注册，持久目录允许是清单子集。首次 route/profile/storage/resource-ready 约束先纯验证，后 provision，避免先写库后启动失败。

REGISTER 只允许本实例真实已交付清单的精确定义，不接受任意 RESOURCE audience 自报；profile 来自真实字段目录。结果必须满足当前 UC030 storage.read/write 和所有 resource routes 约束；导致重启不一致的停用拒绝，解除依赖需独立组合交付。首次隔离验收可选 email，避开必需 storage/route scopes。

全部副本使用一致提供方清单，正式变更前撤除旧 SeedCatalog writer 是部署门禁，不声称本次已替运营者完成。恢复用最新 revision/新编号前向操作，不回滚数据库或 generatedAt；旧二进制回滚不获得目录写权。

<a id="br-scp-010"></a>
### BR-SCP-010：消费边界与既有授权规则引用

目录权威/完整投影/enabled/requestable/稳定名引用 [BR-SCP-001–005](UC-AUTH-001-get-scope-catalog-snapshot.md#业务规则)。实际权限仍按 [UC014/BR-OAU-002](UC-AUTH-014-authorize-application.md#br-oau-002)、UC015–019 与 UC028 的 token.scopes∩G∩D∩C；本 UC 不改 G/revocationEpoch，不恢复过期/撤销材料。

App 只消费 UC001 name/requestable/revision/generatedAt；缓存窗口由 [App ADR001](../../app-center/adr/ADR-001-scope-catalog-cache.md#第一阶段缓存) 拥有（当前缺省 5m），无广播或跨库原子承诺。Auth 当前检查不等待 App TTL。

<a id="br-scp-011"></a>
### BR-SCP-011：已登记 Scope 的稳定权限契约

首次登记永久占名，动作/数据与资源边界/kind/audience/字段映射类型/副作用固定。扩大或缩小契约、更换意义须新 name，不借 description/handler 重构/返回更多字段绕过。内部重构、修复越契约披露保持原契约；用户资料值变化或既有年级计算不是定义变化。

REGISTER 的 contract/providerEvidence 不可变；系统基线保留原定义来源，不补造人工审核。机器固定 stable metadata 与登记依据，管理员按设计/测试判断同义与真实实现匹配，摘要不证明行为正确。

<a id="br-scp-012"></a>
### BR-SCP-012：定义登记与启用门禁

新项需名称未占用、契约完整、真实提供方及越权拒绝依据；disabled 也不跳过。name 不生成能力。openid/email/offline_access/campus.whut 保留名遵守原协议/校园用例，不允许通用重新定义。

资料一字段一 Scope、精确 profile.<fieldKey>，固定真实类型，引用 [UC028/BR-UPF-012](UC-AUTH-028-disclose-user-profile-to-applications.md#br-upf-012) 与 [UC005/BR-UPF-002](UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。不得 .v2 别名映射旧字段。RESOURCE 须有本部署清单和资源约束，不靠 readiness 布尔或示例路由造能力。

同名 REGISTER 即使同值也拒绝。CORRECT_TEXT 仅 label/description，SET_ENABLED 仅 enabled，未知名拒绝。删除、重命名、kind/audience/field/type/contract 修改与独立 requestable 写入无入口。

<a id="br-scp-013"></a>
### BR-SCP-013：文案修正与同意展示一致性

同义文案修正保存前后值/原因，不改 G/grant revision/epoch/token，不让所有用户重同意，不把不可解释旧文案修成更广权限。

待提交 consent 绑定实际请求 R 的定义/文案摘要及展示凭证。View 生成新不可猜 presentation 标识并保存证据；Confirm 提交页面标识，最终事务同时校验保存标识、当前 R 定义摘要、Session/CSRF/App/grant。相关变化返回既有 interaction_changed，显式重读后确认；无关 Scope 变化不冲突。另一标签页 View 后旧表单不能借最新服务器快照通过。

审计保存实际展示证据及明确确认/复用历史同意来源，不含资料值，不给旧 grant 批量补历史快照。UC014 同步接受；UC035 引用共享规则但仍 DRAFT、不实现宿主协议。旧无证据交互须重新 View；静默复用 G 仍按原 prompt 规则，不凭空新增权限。

<a id="br-scp-014"></a>
### BR-SCP-014：新语义替代与重新授权

新语义新 name，替代关系仅说明，不参与授权匹配，禁 alias/前缀/superset/old→new 推导。App 新 Version 明确声明审核，用户 UC014 同意新项。旧 G/code/token/family 不获得新项；后来同意也不扩大旧 family ceiling。

兼容期可同启旧新定义，各自提供原契约；期限由实际提供方决定，无默认自动迁移。不改账号/pairwise sub/渠道边界。

<a id="br-scp-015"></a>
### BR-SCP-015：停用、退役与删除边界

暂停/退役均 enabled=false，完整投影保留旧定义/name，requestable=false；无不可逆状态或仅旧应用的第二开关。风险阻断无需等全部 App 迁移。停用不删 G/审计/资料/KV，不追回已披露数据。

恢复仅同契约，经新 revision 操作，不复活过期/撤销材料。未来若要不可恢复退役，另审写约束，不偷偷增加第二授权状态。

## 错误语义与运行约束

身份错误沿用 trusted-identity-v1。当前无完整管理资格 SCOPE_MANAGEMENT_FORBIDDEN（403/PERMISSION_DENIED）；非法输入 INVALID_SCOPE_MANAGEMENT_REQUEST（400/INVALID_ARGUMENT）；前置条件过期 SCOPE_CATALOG_CONFLICT（409/ABORTED）；ID 异参 SCOPE_OPERATION_CONFLICT（409/ABORTED）；回执不存在 SCOPE_OPERATION_NOT_FOUND（404/NOT_FOUND）；生命周期/提供方/依赖门禁 SCOPE_CHANGE_BLOCKED（409/FAILED_PRECONDITION）；版本耗尽 SCOPE_CATALOG_REVISION_EXHAUSTED（409/FAILED_PRECONDITION）；限流 SCOPE_MANAGEMENT_RATE_LIMITED（429/RESOURCE_EXHAUSTED）；数据损坏/存储故障/提交未知 SCOPE_MANAGEMENT_UNAVAILABLE（503/UNAVAILABLE）。不回显凭据或底层错误；开关关闭不恢复旧旁路。

## 验收与交付边界

1. 真实 USER JWS/full admin 读写/查询，普通/部分 bundle/Reviewer/Developer/service/OAuth/错误 audience/撤权旧 JWS/禁用均拒绝；撤权与变更 fence 竞争。
2. 类型限字段、未知/重复/删名/改义/改映射、未交付 provider、profile 别名/类型、保留名与容量边界；登记不自动提供能力。
3. 并发 CAS、陈旧 no-op、同值 no-op、同 ID重放/异参/异 actor、溢出、审计失败回滚、未知结果查询。完整目录/审计/回执原子，不靠退出码推断。
4. 首次基线唯一；重启不改文案/启停，清单新增不自动登记；目录丢失损坏失败关闭；写前 route/storage 验证，依赖项停用拒绝。生产不得保留旧更新旁路。
5. 真实 Mongo/生产 Wire/生成 HTTP+gRPC client 覆盖 UC001 与 OAuth 启停恢复；G/epoch/sub 不变，新名不扩旧 token/refresh。
6. consent 相关/无关文案变更、两标签页、无 presentation、grant/撤销竞争、明确同意/复用审计、回滚。
7. make check/race/真实 Mongo，独立 API 生成一致、brief/registry 静态检查。Gateway/Console 真正跨系统验收另跟踪，不将低层测试冒充真实 UI 证据。

后续 App/Console 联合验收保持：隔离环境通过正式 API 创建含实际 email 等 Scope 的待审 Version，真实审核详情加载后管理 API 停用，取回执/UC001 新快照，等待真实 App TTL/刷新证据，APPROVE 应 InvalidApplicationScope 且 Review PENDING。新编号/revision 恢复，显式重读确认再 APPROVE；独立 Review 验证停用期间人工 REJECT。不直改库/伪造快照/假定一次 sleep 证明全副本刷新；目录不可用、owner 失格、策略错误分别验证。Console 专用工作树本轮不改。

## 变更记录

- 2026-10-26：合并生命周期与启停，保留 BR-SCP-006–015，撤销重复用例编号。
- 2026-10-26：用户接受管理员 API 简化并授权设计及实现；ACCEPTED，脚本 brief 后实施。设计接受不等于后端完成或生产启用。
