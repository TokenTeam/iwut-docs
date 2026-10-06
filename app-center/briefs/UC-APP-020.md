<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-020 --spec tools/brief-specs/UC-APP-020.json -->
# Brief — UC-APP-020：管理稳定发布槽位

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-020` 管理稳定发布槽位 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAC-012`，`BR-PUB-011`–`BR-PUB-019`（9 条） |
| 外部引用 BR | — |
| ADR | `ADR-001`、`ADR-002`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/app-oauth-client-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

> developerStatus 为 `APPROVED` 的 Application 当前管理员，在一个明确的 rpcApiMajor 分区中设置、替换或清空 stable 发布槽位，使普通用户后续能够通过统一运行解析取得一个经过审核的默认启动目标。

本用例负责：

- 为既有或新建的 `(applicationId, rpcApiMajor)` ApplicationPublication 设置或替换 `stableVersionId`。
- 清空 `stableVersionId`，并在所有槽位为空时保留 Publication 身份、revision 与历史。
- 复用 Publication 共享 revision，防止 test、未来 grey 与 stable 操作静默覆盖。
- 在真实设置前重新验证 Version、Review、当前公开资料、scope、launch URL 及 STABLE OAuth registration。
- 为每次真实变化追加不可变 ApplicationPublicationHistory。
- 激活 Application＋STABLE channel 的 PUBLIC/CONFIDENTIAL OAuth client 管理和 Auth provider 解析。

本用例不负责：

- 配置或调整 grey rollout。
- 统一执行 `test > grey > stable` 的用户运行目标解析。
- 返回普通用户目录或应用详情。
- 定义 FilterRule。
- 归档、禁用或平台紧急暂停整个 Application。
- 清空 test 槽位。
- 撤销 ApplicationVersion 的 APPROVED 资格。
- 自动把已批准 Version 从 test 或 grey 提升到 stable。

稳定发布不要求目标 Version 曾经进入 test 或 grey。Test、Grey、Stable 是三个独立槽位；常见的逐步发布顺序是产品操作路径，不是服务端强制状态机。

### 已确认的设计选择

1. stable 与 test 一样按 `(applicationId, rpcApiMajor)` 分区，并共享同一个 Publication revision。
2. 设置或替换 stable 使用已批准 Version；不要求存在 test/grey 历史。
3. 清空是管理员的日常停止公开分发手段。平台紧急处置和 Application 级禁用由后续独立用例定义。
4. 回退不建立新状态；管理员把 stable 重新设置为一个当前仍具资格的历史 Version，即构成一次可审计回退。
5. Publication 在全部槽位为空时仍保留，不删除身份、revision 或历史。
6. 未来只允许在已有 stable 基线时建立 grey；存在 grey rollout 时不能清空 stable。
7. STABLE 使用独立于 TEST/GREY 的 OAuth registration 和 credential，但同一 Application 的 sector/sub 仍只由 Auth 按 Application 管理。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
rpcApiMajor: int32
```

设置或替换命令：

```text
SetStablePublicationCommand {
  versionId: ApplicationVersionId
  expectedPublicationRevision: optional int64
}
```

清空命令：

```text
ClearStablePublicationCommand {
  expectedPublicationRevision: int64
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

设置命令中 `expectedPublicationRevision=null` 表示预期 Publication 尚不存在，只允许创建；正整数表示预期记录存在且 revision 精确匹配。清空只能操作已存在 Publication，因此 expected revision 必须为正整数。

请求不能指定 publicationId、historyId、审核引用、外部策略版本、审计字段、OAuth clientId 或结果 revision。

### 设置或替换主流程

1. 从可信身份取得 authId 和 developerStatus，校验 developerStatus=`APPROVED`、rpcApiMajor `>= 1`、versionId 为 UUIDv7，以及 expected revision 语义合法。
2. 加载候选并确认：
   - Application 存在，调用者是当前 admin。
   - 当前公开 Profile 指向同一 Application 的 APPROVED ProfileRevision，内容满足既有不变量。
   - Version 属于该 Application、状态为 APPROVED、RPC range 覆盖 rpcApiMajor。
   - 最新 ApplicationReview 具有完整 APPROVED decision，Version 内容、revision 与 snapshot 一致。
   - Publication 的存在性和 revision 符合请求预期。
3. 如果现有 stableVersionId 已等于目标 versionId，返回当前 Publication、changed=false、history=null；不执行外部复检，不读取 Clock 或 IDGenerator。
4. 针对批准 snapshot：
   - 通过 ScopeCatalog 确认 scopes 当前仍可申请并取得 catalog revision。
   - 通过 LaunchURLSubmissionPolicy 重新执行公网 HTTPS/DNS 预检并取得 policy version。
   - 读取 `(applicationId, STABLE)` OAuth registration；pkce redirect 非空要求 PUBLIC identity，confidential redirect 非空要求 CONFIDENTIAL identity 及 credential。空数组允许发布。
5. 为首次创建所需的 Publication 和本次 History 生成 UUIDv7，并取得 changedAt。
6. Repository 在同一事务中通过 Application、Version/Review、Profile、OAuth registration/credential 与 Publication 写入栅栏重新确认上述事实，然后：
   - Publication 不存在时创建 revision=1、stableVersionId=目标 Version、test/grey 为空的记录。
   - Publication 已存在时只替换 stableVersionId，并把共享 revision 增加 1。
   - 插入 `SET_STABLE_VERSION` History，记录旧/新 Version、批准 Review 和外部复检版本。
7. 返回 Publication、History 和 changed=true。

### 清空主流程

1. 校验可信 DeveloperIdentity、rpcApiMajor 和正的 expectedPublicationRevision。
2. 在一致读取中确认 Application 当前管理员、Publication 归属和 revision。
3. 若 stableVersionId 已为空且 greyRollout 也为空，返回当前 Publication、changed=false、history=null；不读取 Clock 或 IDGenerator。若 stable 为空但 grey 非空，属于持久化不变量损坏，返回 `ApplicationPublicationStateInconsistent`。
4. 若 stableVersionId 非空且 greyRollout 非空，返回 `StablePublicationRequiredByGrey`。清空不能制造只有 grey、没有 stable 的运行配置。
5. 生成 historyId 和 changedAt，在同一事务中重新取得 Application 写栅栏、复查管理员、Publication revision、stableVersionId 和 greyRollout，然后：
   - 把 stableVersionId 设为空。
   - shared revision 增加 1，更新审计。
   - 插入 `CLEAR_STABLE_VERSION` History，保存 previousVersionId；newVersionId、approvedReviewId 和外部策略版本为空。
6. 即使 test 和 grey 也为空，保留 Publication 记录，返回 changed=true。

清空不要求重新检查旧 Version、Review、Profile、scope、launch URL 或 OAuth registration，因为该操作只减少公开可用性。清空不删除 STABLE OAuth registration、clientId、credential、Auth grant 或审计事实；后续运行解析因没有 stable 指针而失败关闭，Auth 自行依据其 token/grant 规则处理既有凭据。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 APPROVED：`DeveloperApprovalRequired`。
- rpcApiMajor、versionId 或 expected revision 非法：对应稳定输入错误。
- Application、Version 或预期存在的 Publication 不存在：对应 NotFound；跨 Application 关系也按 NotFound 处理。
- 调用者不是当前管理员：`ApplicationAdminRequired`。
- Version/Review 未批准或失去资格：`ApplicationVersionNotApproved`。
- Review、Version 或 snapshot 关系损坏：`ApplicationReviewStateInconsistent`。
- 没有当前公开资料：`ApplicationProfileRequired`。
- 公开资料指针或内容损坏：`ApplicationProfileStateInconsistent`，映射 500/INTERNAL。
- Version 不覆盖 rpcApiMajor：`ApplicationVersionRpcApiIncompatible`。
- Publication 存在性或 revision 与预期不符：既有 Publication 冲突错误。
- scope、URL 或其依赖检查失败：复用 UC-APP-007 的对应错误。
- 非空 redirect 数组缺少 STABLE 对应 identity/credential：`OAuthClientRegistrationRequired`。
- grey 仍存在时清空 stable：`StablePublicationRequiredByGrey`。
- stable 为空但 grey 非空，或 Publication 字段组合违反 action/state 不变量：`ApplicationPublicationStateInconsistent`，映射 500/INTERNAL。
- revision 溢出、ID/Clock/存储失败或数据不变量损坏：内部失败；不得留下部分指针或 History。

### 最小领域模型变化

```text
ApplicationPublication {
  publicationId
  applicationId
  rpcApiMajor
  testVersionId?
  greyRollout?       // 后续 UC 定义；当前必须为空
  stableVersionId?
  revision
  createdBy / createdAt
  updatedBy / updatedAt
}
```

`testVersionId` 从存储层必填改为可空，因为 stable 可以首次创建 Publication，清空后也允许 EMPTY。该变化不改变 UC-APP-007 的设置语义：UC007 成功后 testVersionId 必然非空。

History action 扩展为 `SET_TEST_VERSION | SET_STABLE_VERSION | CLEAR_STABLE_VERSION`。previous/new/Review/外部策略字段的条件必填关系由 action 决定。

### API 草图

```text
PUT    /v1/applications/{applicationId}/publications/{rpcApiMajor}/stable-slot
DELETE /v1/applications/{applicationId}/publications/{rpcApiMajor}/stable-slot
```

PUT body：

```json
{
  "versionId": "version-uuid",
  "expectedPublicationRevision": 3
}
```

DELETE 使用 `If-Match` 或等价显式字段表达 expectedPublicationRevision；不得依赖客户端最后写入胜出。创建返回 201，替换、清空和 no-op 返回 200。响应返回 changed、当前完整 Publication 和可空 History。

独立 API 仓库继续使用 package `app_center.v1.application_publication` 和既有 `ApplicationPublication` service，新增：

```text
SetApprovedVersionInStableSlot
  PUT /v1/applications/{application_id}/publications/{rpc_api_major}/stable-slot
  body: command

ClearStableSlot
  DELETE /v1/applications/{application_id}/publications/{rpc_api_major}/stable-slot
  query: expected_publication_revision
```

`SetApprovedVersionInStableSlotRequest` 包含路径字段和 `SetApprovedVersionInStableSlotCommand { version_id, optional expected_publication_revision }`。`ClearStableSlotRequest` 直接包含路径字段和必填正整数 `expected_publication_revision`；HTTP 不接收 body，gRPC 使用同一字段。

两个响应复用 `{ changed, publication, history? }` 结构。为表达 stable-only 和 EMPTY：

- `ApplicationPublicationResource.test_version_id` 保持 field 4，但改为 `optional string`。
- 新增 `optional string stable_version_id = 10`。
- History 的 `new_version_id`、`approved_review_id`、`scope_catalog_revision`、`preflight_policy_version` 保持既有 field number 并改为 optional；SET action 必填，CLEAR action 为空。
- OAuth Provider 的 `AuthorizationContext.tester_membership_id` 保持 field 3 并改为 optional；TEST 必填，STABLE 为空。

新增 publication error reason：

```text
ERROR_REASON_STABLE_PUBLICATION_REQUIRED_BY_GREY = 23
ERROR_REASON_APPLICATION_PUBLICATION_STATE_INCONSISTENT = 24
```

前者映射 `FAILED_PRECONDITION / 422`；后者映射 `INTERNAL / 500`。其余错误继续复用 UC007 已有稳定 reason。HTTP 请求不能通过 query 覆盖 PUT command；DELETE 只允许三个已声明字段。

Mongo migration 固定为 `0016_stable_publication`：

- `application_publications` 增加可空 stableVersionId，并把 testVersionId 改为可空；允许 test-only、stable-only、二者同时存在和 EMPTY，当前不允许写 greyRollout。
- `application_publication_history` 接受三个 action，并按 action 校验条件必填字段；历史 SET_TEST 记录不重写。
- `application_oauth_registrations` channel validator 从仅 TEST 扩展为 TEST/STABLE；GREY 继续拒绝。
- migration ledger、fresh install、0015→0016 顺序升级、重复执行和回滚测试必须覆盖这些变化。

不得改变既有 UC007 test API 的命令语义；它只是开始返回带 presence 的完整 Publication/History 资源。

### 验收场景

- 可以用 APPROVED、exact-major 兼容且有当前公开资料的 Version 直接建立 stable，无需 test/grey 历史。
- stable-only Publication 可以首次创建；testVersionId 为空且 stableVersionId 非空。
- 替换 stable 增加共享 revision 并保留旧 Version/Review；设置相同 Version 为 no-op。
- 清空 stable 保留 Publication；所有槽位为空时形成 EMPTY 记录，后续 set 使用其正 revision。
- 存在 grey 时不能清空 stable；无 grey 时 test 不阻止清空。
- 把槽位设置回历史 Version 仍重新执行当前资格复检并写普通 SET History。
- 当前公开资料缺失时不能 set，但可以 clear；损坏资料指针 set 返回 INTERNAL。
- 非空 PKCE/confidential redirects 分别要求 STABLE PUBLIC/CONFIDENTIAL registration；TEST registration 不能代替。
- STABLE registration 与 TEST 完全隔离，clientId 稳定且 major/Version 变化不重建。
- STABLE provider 对普通有效用户不要求 Tester；TEST provider 行为不变。
- stable set/clear 与 test 修改共享 revision，两个相同 expected revision 的并发命令最多一个提交。
- clear stable 与 Auth 解析/授权并发时结果具有明确先后：旧 snapshot 先完成可以形成在途结果，clear 先提交则后续解析失败；App 不返回跨 revision 混合上下文。
- 管理员转让、Profile 切换、Version 资格变化和 registration 建立竞争均有明确先后结果。
- 事务回滚不留下孤立 History、部分指针或半创建 OAuth credential。
- Proto field presence 能区分 stable-only、test-only 和 EMPTY；DELETE 的 expected revision 缺失、零或 query 重复均拒绝。
- 0016 对 fresh、sequential 和重复 migration 产生相同 validator/index 结果；既有 SET_TEST History 保持可读。

### 依赖与实现边界

- 复用 UC-APP-007 的 Publication 聚合、History、批准事实复查、ScopeCatalog、LaunchURLSubmissionPolicy、Profile gate、Application 写栅栏和事务模型。
- 复用 UC-APP-018/019 的 registration/credential 与 Auth-only provider；实现时扩展渠道 allowlist，不建立第二套 OAuth 模型。
- 需要显式 migration 放宽历史 Publication 的 testVersionId 必填约束、增加 stableVersionId 与新的 History action/条件 validator；历史记录不重写。
- 需要同步修改独立 API 子模块和 [App OAuth provider 契约](../../platform/contracts/app-oauth-client-v1.md)，并做真实 App/Auth 跨服务验证。
- Catalog、统一启动解析、Application disable、Grey rollout 和 Filter 不属于本工作包；stable 指针可以先存在，但普通用户入口只有在后续查询契约完成后才形成产品闭环。

## 业务规则（UC-APP-020 权威正文）

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-oac-012 -->
### BR-OAC-012：STABLE OAuth channel 激活

UC-APP-020 被接受后，UC-APP-018 的五个管理员方法必须接受 channel=`STABLE`，并继续以 `(applicationId, channel)` 隔离 registration、clientId、status、authorizationEpoch 和 confidential credential。STABLE 与 TEST clientId 不共享，但都映射到同一 Application；Auth grant 继续以 `(authId, applicationId, channel)` 隔离。

UC-APP-019 的五个 Auth-only provider 方法必须支持 STABLE：

- runtime 使用 exact-major stableVersionId，不读取 test 或未来 grey。
- Auth 仍负责确认当前用户有效并提供可信 authId；App 的 authorization context 不要求 Tester Membership。共享契约中的 testerMembershipId 改为按渠道可空：TEST 必填，STABLE 为空。
- redirect/scopes/display 与 TEST 一样来自同一个批准 Version/Review/Profile snapshot。
- PublishedRedirectSnapshot 纳入已发布 STABLE major 的批准回调；仍忽略历史、草稿和未登记 type。
- 没有 stable、client channel 不匹配、Version/Profile 不一致或 client DISABLED 时失败关闭。

App 仍不保存 sector/sub，不签发 code/token。STABLE provider 扩展继续仅开放原生 gRPC，并复用现有五个方法级 service permission。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-011 -->
### BR-PUB-011：Stable 管理权限

设置、替换和清空 stable 的操作者必须具有可信 `APPROVED` Developer 身份，并在最终事务中仍是 Application 当前 admin。管理员转让先提交后，旧管理员不能改变 stable；发布操作先提交则形成一条完整审计事实。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-012 -->
### BR-PUB-012：Stable 发布资格与直接发布

stableVersionId 只能引用同一 Application、覆盖当前 rpcApiMajor 且当前仍具有完整 APPROVED Review/snapshot 一致性的 Version。设置时还必须存在当前已批准公开资料。

Version 不需要曾进入 test 或 grey。设置 stable 不修改 Version 审核状态，不修改 test/grey，也不自动形成目录响应。一个 APPROVED Version 可以同时被多个 major 和多个槽位引用。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-013 -->
### BR-PUB-013：公开默认目标边界

stable 是普通用户的默认发布目标，但本用例只保存权威指针。Application 进入公开候选目录还必须由后续 Catalog/Resolver 在同一查询语义中确认当前公开 Profile、Application 可用状态、exact-major Publication、Version 资格和 host capabilities。

没有 stable 的 Application 不进入普通公开候选集。TEST-only Application 后续只进入“我参与的测试”入口，不混入普通目录；Filter 只能影响客户端展示，不能代替 stable 资格或服务端授权。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-014 -->
### BR-PUB-014：共享乐观并发与 no-op

test、grey、stable 和 clear 操作共享 Publication revision。首次由 set stable 创建时 revision=1；每次真实变化增加 1；revision 不匹配时不自动覆盖。目标已生效或 stable 已为空时是 no-op，不增加 revision、不写 History、不改变审计时间。

首次 set 必须预期不存在；已有记录上的 set/clear 必须携带精确正 revision。空 Publication 仍是“已存在”，后续设置必须使用它的当前 revision，不能再次用 null 创建。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-015 -->
### BR-PUB-015：Stable PublicationHistory

每次真实设置/替换追加：

```text
SET_STABLE_VERSION {
  previousVersionId?
  newVersionId
  approvedReviewId
  scopeCatalogRevision
  preflightPolicyVersion
  changedBy
  changedAt
  publicationRevision
}
```

每次真实清空追加：

```text
CLEAR_STABLE_VERSION {
  previousVersionId
  newVersionId: null
  approvedReviewId: null
  scopeCatalogRevision: null
  preflightPolicyVersion: null
  changedBy
  changedAt
  publicationRevision
}
```

History 不可修改，是操作审计而非当前状态来源。把 stable 设置为一个历史 Version 就是回退；History 仍使用 `SET_STABLE_VERSION`，previous/new 指针足以表达结果，不增加 `ROLLBACK` 状态。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-016 -->
### BR-PUB-016：设置前复检与 STABLE OAuth

真实设置 stable 前，必须按照 UC-APP-007 相同强度重新检查当前公开资料、批准 snapshot、Scope Catalog、LaunchURLSubmissionPolicy 和非空 OAuth redirect 所需的 registration/credential。检查结果针对 STABLE channel，TEST/GREY registration 不能代替。

STABLE identity 可以在 Publication 之前登记。client 为 DISABLED 不阻止管理员保存 stable 指针，但 Auth 必须拒绝该 client 的授权；空 redirect 数组允许发布，并表示相应 client type 在该 Version 上没有可用 OAuth 回调。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017 -->
### BR-PUB-017：清空、空记录与 Grey 基线

清空 stable 只移除 stable 指针，不删除 Publication。test 可以继续存在；未来 grey 必须以 stable 为基线，因此 greyRollout 非空时拒绝清空 stable。管理员应先清空 grey，再清空 stable。

清空不删除 OAuth identity、credential、grant、Version、Review、Profile 或历史。全部槽位为空时 Publication 进入 EMPTY 形态并保留 revision，使后续并发和审计连续。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-018 -->
### BR-PUB-018：Stable 变化原子性

设置事务必须原子复查当前 admin、Version/Review/snapshot、Profile、STABLE registration/credential、Publication revision，并同时提交指针、revision、审计和 History。清空事务原子复查当前 admin、Publication revision、stable/grey 指针，并同时提交清空与 History。

与 test 修改、未来 grey 修改、管理员转让、审核资格撤销、Profile 切换或 OAuth registration 建立并发时，结果必须等价于某个明确先后顺序；失败不能留下部分状态。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-019 -->
### BR-PUB-019：不隐式扩散

Stable set/clear 不得修改其他 rpcApiMajor、test/grey、Version 状态、Profile、Tester Membership 或 FilterRule，也不触发批量发布。一个 range 覆盖多个 major 时仍需逐 major 操作。

## 架构决定（仅本次需要的章节）

### ADR-001：Scope Catalog 权威来源与缓存（`ACCEPTED`）

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

#### 多阶段校验

- 创建 DRAFT：使用上述有界缓存，尽早发现无效 scope。
- 提交审核：重新确认 scope 仍允许新版本申请。
- reviewer 批准：再次确认 snapshot 中的全部 scope，并把所用 catalog revision 写入 decision.approvalValidation；详见 UC-APP-005。
- 放入发布槽位：再次确认 approved snapshot 中的 scope，并把所用 catalog revision 写入 PublicationHistory；UC-APP-007 首先应用于 test 槽位。
- consent/token/用户数据读取：Auth 必须以自己的当前规则做最终授权，不能相信 App Center 过去的校验结果。

Scope 启用状态和兼容投影按 [UC-AUTH-001 / BR-SCP-004](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 执行：App 继续消费 requestable，Auth 自己在 OAuth 运行阶段检查当前 enabled。缓存仍可能在 TTL 内使管理操作按旧目录通过；这些结果不保证后续 OAuth 可用，也不阻止 Auth 排除已停用 scope。App 不新增独立 runtimeEnabled 状态或同步修改已批准 snapshot。

因此短暂缓存不构成实际用户授权依据。

### ADR-002：ApplicationPublication 按 RPC API major 分区（`ACCEPTED`）

#### 决定

ApplicationPublication 从第一次出现时就按以下业务键唯一：

```text
(applicationId, rpcApiMajor)
```

每条 Publication 只管理一个 RPC major 下的发布槽位和 revision。UC-APP-007 首先引入 testVersionId；grey/stable 字段只在对应真实用例出现时增加。

被放入槽位的 ApplicationVersion 必须满足：

```text
rpcApiMinVersion <= rpcApiMajor < rpcApiMaxVersionExclusive
```

requiredCapabilities 仍在客户端解析或握手时逐项判断，不成为新的 Publication 分区维度。

一个 Version 若兼容多个 major，可以由管理员分别放入多条 Publication。一次命令只改变一个 rpcApiMajor，不根据 Version range 隐式批量修改。

#### 适用边界

本决定只覆盖 App Center 的版本发布选择。Auth token、Expo build 升级策略和网页自己的 versionLabel 不使用这个分区键。

若未来证明系统永远只支持一个 RPC major，可以保留相同模型而只存在一条 Publication；无需把分区重新折叠进 Application。

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

### `platform/contracts/app-oauth-client-v1.md`：App OAuth Client 提供方契约 v1

#### 所有权与调用方

App Center 持有 Application＋channel 级稳定 client identity、confidential credential，以及依附 ApplicationVersion 的受审核 redirect URI 和 scopes。Auth 不保存另一份可独立修改的 client 注册表。管理规则见 [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md)，可信读取规则见 [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md)，STABLE/GREY 渠道扩展分别见 [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 与 [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md)，协议见 [OAuth OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

管理接口接受 SESSION 转换后的 [trusted identity](../../platform/contracts/trusted-identity-v1.md) USER 身份。内部接口只接受 Auth 的 [service identity](../../platform/contracts/trusted-service-identity-v1.md)，audience 固定为 `iwut-app-center`，权限来自 App Center 本地 caller registry；逐方法授权，不经过公网、HTTP 或 gRPC-Web，也不把 client secret 当服务间凭据。

#### 三种生命周期

`ApplicationOAuthRegistration` 以 `(applicationId, channel)` 唯一，字段为 applicationId、channel、publicClientId、publicStatus、publicAuthorizationEpoch、confidentialClientId、confidentialStatus、confidentialAuthorizationEpoch、registrationRevision、createdAt、updatedAt。两个 clientId 均为服务端 UUIDv4、全局唯一、永久不重用；type 由其所在 slot 确定，状态为 `ACTIVE/DISABLED`。client identity 固定归属一个 channel，不包含 rpcApiMajor、Version 或 hostname。

`OAuthClientCredential` 以 confidentialClientId 唯一，字段为 confidentialClientId、applicationId、secretDigest、credentialRevision、rotatedAt。channel 从 confidentialClientId 的 registration 确认，不能跨渠道使用。它只服务于以后 confidential client authentication；secret 轮换不改变 registrationRevision。

`ApplicationVersionOAuthConfig` 以 applicationVersionId 唯一，字段为 applicationVersionId、applicationId 和：

```text
oauthRedirects {
  pkceRedirectUris: []RedirectURI
  confidentialRedirectUris: []RedirectURI
}
```

它使用独立 collection 存储，但生命周期严格依附 ApplicationVersion：与 Version 同事务创建/编辑，使用同一个 Version revision 做 OCC，提交时深拷贝进 Review snapshot，提交后不可独立修改。两个数组均非 null、各 0–10 项、内部唯一且彼此不交叉。详细 URI 规则见 [BR-VER-018](../use-cases/UC-APP-002-create-application-version.md#br-ver-018)。

#### 管理接口

建议服务 `app_center.v1.oauth_client.OAuthClientService`。可执行 Proto、字段号与 HTTP annotation 在独立 API 仓库落地。

| 方法 | 输入 | 输出 |
| --- | --- | --- |
| RegisterOAuthClient | applicationId、channel、type、optional expectedRegistrationRevision | registration；仅 confidential 额外返回一次 clientSecret |
| GetApplicationOAuthRegistration | applicationId、channel | 当前管理员可见的 registration 元数据 |
| SetOAuthClientStatus | clientId、expectedRegistrationRevision、status | 新 registration；相同状态为 no-op |
| GetOAuthClientCredentialMetadata | clientId | credentialRevision、rotatedAt；不含 secret/摘要 |
| RotateOAuthClientSecret | clientId、expectedCredentialRevision | 新 credential 元数据及一次性 clientSecret |

每个 Application 每渠道每种 type 至多登记一次。registration 尚不存在时 expectedRegistrationRevision 必须为空，结果 revision=1；已存在且补登记另一 type 时必须提交当前 revision。登记不依赖 Version、Review 或 Publication；丢失登记响应时先查询，secret 丢失则轮换。禁用和重新启用使用 SetOAuthClientStatus，不删除 identity。

secret 为 32 随机字节的 base64url 无 padding 字符串。App 仅存 `SHA-256("iwut-oauth-client-secret-v1\0" || clientId || "\0" || secret)`，使用恒定时间比较；只保留当前摘要。创建/轮换成功响应使用 no-store；提交结果未知时不能返回可能未提交的 secret。

#### Auth 专用接口

服务 `app_center.v1.oauth_client.OAuthClientProviderService`：

| 完整方法后缀 | service permission | 输入 | 输出 |
| --- | --- | --- | --- |
| `/GetClientConfiguration` | `app.oauth.client.read` | clientId | identity 元数据（含固定 channel、registrationRevision、该 slot 的 authorizationEpoch）、tokenEndpointAuthMethod；CONFIDENTIAL 含 credentialRevision |
| `/VerifyClientSecret` | `app.oauth.client.verify` | clientId、clientSecret、expectedCredentialRevision | verified、credentialRevision；不返回摘要 |
| `/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` | clientId、channel、rpcApiMajor、expectedRegistrationRevision | 当前批准的运行配置 |
| `/ResolveAuthorizationContext` | `app.oauth.context.resolve` | clientId、authId、channel、rpcApiMajor、expectedRegistrationRevision、expectedRuntimeVersion | 当前用户授权上下文 |
| `/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` | applicationId | PublishedRedirectSnapshot |

完整 RPC 名由 `/app_center.v1.oauth_client.OAuthClientProviderService` 加表中后缀组成。permission 只授予指定 Auth 服务主体；SYSTEM、USER 和第三方 access token 均不能调用。Verify 对未知 client、错误 secret、PUBLIC、DISABLED 或 credential revision 不一致返回 `verified=false`。原 secret 只经 TLS 内网发送，拦截器和代理禁止记录 metadata/body。

`RuntimeConfiguration` 包含 clientId、applicationId、type、channel、rpcApiMajor、registrationRevision、authorizationEpoch、adminAuthId、versionId、publicationRevision、redirectUris、requiredScopes、optionalScopes、display、observedAt、validUntil。

`ApplicationDisplay` 包含 profileRevisionId、displayName、可空 description 和可空 icon。全部内容来自 `currentPublishedProfileRevisionId` 指向的同一 Application、APPROVED ProfileRevision；不提供 Application 技术名称 fallback，也不返回 HTML。运行 tuple 中的 profileRevisionId 即 `display.profileRevisionId`，不在 RuntimeConfiguration 顶层重复保存。

`AuthorizationContext` 包含完整 RuntimeConfiguration，加 authId 和可空 testerMembershipId。TEST 必须返回当前 ACTIVE Tester episode；STABLE/GREY 为空。`expectedRuntimeVersion` 为 `(versionId, publicationRevision, profileRevisionId, adminAuthId)`；expectedRegistrationRevision 独立传递。App 必须以一个 Mongo snapshot 同时比较预期 tuple、读取运行配置、当前公开资料和渠道用户资格。

redirectUris 来自批准 snapshot：PUBLIC 读取 pkceRedirectUris，CONFIDENTIAL 读取 confidentialRedirectUris；对应数组必须非空。requiredScopes/optionalScopes 来自同一 snapshot，不按 App 的 requestable 缓存过滤；Auth 根据 [Scope Catalog 契约](../../platform/contracts/auth-scope-catalog-v1.md) 对应的当前权威 enabled 和 OAuth UC 执行最终授权。前端不能指定 versionId、redirect URI、scope、adminAuthId 或“已审核”标记；channel 必须与 client 登记值完全相等，rpcApiMajor 只选择该渠道的权威 Publication；TEST/GREY/STABLE client 不能互相替代。

所有返回字段取自同一个 Mongo snapshot；observedAt 为建立 snapshot 的时刻，validUntil 不晚于 observedAt+5 秒。Auth 每个安全边界重新读取，不缓存延长。登录前后 registrationRevision 和 runtime tuple 必须一致；Profile 批准后当前公开指针发生变化也必须重新开始或重新展示。credentialRevision 只约束一次 secret 验证，不进入 runtime tuple。

Grant 按 [UC-AUTH-014 / BR-OAU-002](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 的 `(authId, applicationId, channel)` 业务主键保存，同应用同渠道的两类 client 及各 major 共享历史同意。App 提供可信的 client→applicationId/channel 归属，不管理 grant；Auth 不能从前端自报值推导共享范围。授权交互和 code 绑定精确 runtime tuple、redirect URI 和 scope；access/refresh 绑定不可变 channel/rpcApiMajor、authorizationEpoch、Tester episode。Version ID 只用于审计，后续在 token 原来的 major 上重新解析当前版本，不能由资源请求改选 major。Auth 保留历史同意集合，按当前有效交集决定权限；具体规则只由 UC-AUTH-014/016/018/019 定义。

#### Sector 的只读配置来源

Auth 唯一拥有 `applicationId → sector` 和 `(authId, sector) → sub`。App 的上述接口只提供可信 clientId/applicationId/channel/type 关系，不接受或返回客户端指定的 sector，不保有第二份 sector 映射。

`PublishedRedirectSnapshot` 包含 applicationId、entries、redirectUris、observedAt、validUntil。entries 按 `(channel,rpcApiMajor)` 排序，含 versionId/publicationRevision；redirectUris 是该应用当前已启用渠道、全部已发布 major 的批准 snapshot 中两类回调的去重排序并集。未发布 draft、历史已替换版本、没有对应 registration 的 type 不纳入；DISABLED client 不导致已有 sector 删除。无已发布回调时返回空集合；事实不一致或存储故障返回不可用，不伪造空成功。一次 snapshot 读完，期限同上；只读该应用，不能因它包含正式渠道就授予 TEST 用户正式权限。

Auth 用此快照提供标准 sector URI 的 JSON 清单。准备 OIDC 注册元数据时，对照同次 runtime 使用的 `(channel,major,versionId,publicationRevision)`；两份快照若不匹配就重新读取或失败关闭，不用跨版本拼接的清单完成注册验证。此查询不回调 Auth，不公开用户、secret、scope 或运行资格；标准清单的公开范围和协议见 OAuth/OIDC v1。

#### 资格变化与失败

client 不可用、对应回调数组为空、无 exact-major 渠道 Publication、无当前已批准公开资料或批准记录不一致均不可授权；TEST 还要求 ACTIVE Tester，GREY 还要求可信 authId 命中当前 rollout cohort。设计支持 channel=`TEST/GREY/STABLE`；GREY 随 UC-APP-021 工作包交付。正常缺少运行资格面向 Auth 返回统一 `FAILED_PRECONDITION`，受控诊断字段可区分内部原因；公开资料指针存在但目标缺失、跨应用、非 APPROVED 或内容损坏返回 `INTERNAL`。非法输入为 `INVALID_ARGUMENT`；服务身份失败为 `UNAUTHENTICATED/PERMISSION_DENIED`；存储或超时为 `UNAVAILABLE`。Auth 不用旧成功快照或 Application 技术名称兜底。

App 不回调 Auth；Auth 自行检查当前用户及 adminAuthId 的 Developer 状态。

#### STABLE 扩展

[UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 沿用同一组五个 provider 方法：STABLE runtime 精确读取 stableVersionId，用户上下文不要求 Tester Membership，testerMembershipId 按渠道为 TEST 必填/STABLE 为空，批准回调进入 sector 并集；管理面启用独立 `(applicationId, STABLE)` registration/credential。TEST 语义保持不变，STABLE client 不能代替 TEST client，Auth grant 继续按 `(authId, applicationId, channel)` 隔离。

#### 消费点与契约验收

Auth 在授权入口先解析 RuntimeConfiguration 并精确校验 redirect URI；登录后、用户确认和 code 兑换重新解析用户上下文。refresh、UserInfo 和每次委托签发按 OAuth/OIDC v1 的当前资格规则验证。confidential secret 只在 token/revoke 操作验证。

双方至少测试：每种 type 的 clientId 稳定；metadata 无 redirect/secret；一次 secret 返回；registration 与 credential revision 并发隔离；跨应用管理员；runtime tuple 混合；同 clientId 跨 Version/major 选择；伪造 Version/scopes/redirect；非法 redirect 不跳转；Tester 移除后重加；发布槽位变化；公开资料切换和损坏指针；hostname 迁移；快照过期；服务 permission；Auth→App 故障时零签发。

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

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center`，App Center 为 `iwut-app-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### App Center 固定授权映射

App Center 通过原生 gRPC 开放 OAuth provider 和账号归属退出 provider，不生成 HTTP annotation。完整方法与本地 caller registry permission 固定为：

| gRPC 方法 | 必需 permission |
| --- | --- |
| `OAuthClientProviderService/GetClientConfiguration` | `app.oauth.client.read` |
| `OAuthClientProviderService/VerifyClientSecret` | `app.oauth.client.verify` |
| `OAuthClientProviderService/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` |
| `OAuthClientProviderService/ResolveAuthorizationContext` | `app.oauth.context.resolve` |
| `OAuthClientProviderService/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` |

未知方法默认拒绝。普通 USER/SYSTEM trusted identity、第三方 access token、client secret 和网络位置都不能替代 Auth service identity。

#### ENV 配置

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_IDENTITY_ID` | `serviceId` |
| `APP_CENTER_SERVICE_IDENTITY_KID` | 当前签名 key ID |
| `APP_CENTER_SERVICE_IDENTITY_AUDIENCE` | 默认 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_PRIVATE_KEY_PEM_B64` | PKCS#1 或 PKCS#8 RSA private-key PEM 的 strict standard Base64 |
| `APP_CENTER_SERVICE_IDENTITY_TTL` | 正 Go duration；默认 `1m` |

Auth Center 必须提供 `AUTH_CENTER_SERVICE_CALLERS_B64`：以下 JSON UTF-8 bytes 的 strict standard Base64。

```json
{
  "iwut-app-center": {
    "status": "ACTIVE",
    "keys": {
      "app-center-2026-01": {
        "publicKeyPemB64": "<RSA public-key PEM 的 strict standard Base64>"
      }
    },
    "permissions": [
      "auth.scope-catalog.read",
      "auth.developer-status.read",
      "auth.system-principal.resolve",
      "auth.application-closure.apply",
      "auth.application-closure.read"
    ],
    "systemPrincipalPurposes": [
      "app-center.review-auto-rejection"
    ]
  }
}
```

外层 Base64 只解决环境变量传输与转义，不提供保密性。部署必须用 secret 管理 App 私钥；不得把值提交到仓库、镜像、日志或诊断输出。Auth 公钥注册表不含私钥，可以由 config 或 secret 注入。缺失、未知字段、重复权限、非法 key、未知 permission/purpose 或空注册表必须阻止启动。

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_CALLERS_B64` | 与 Auth caller registry 相同的 strict Base64 JSON schema；首版登记 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` | 接受的最大 token TTL，默认 `1m` |
| `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW` | claims 时钟偏差，默认 `30s` |

App Center registry 中 `iwut-auth-center` 允许上述五个 `app.oauth.*` permission，以及 account-owner-exit-v1 固定的三个 app.account-owner-exit.* 精确权限，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

#### 契约测试要求

至少验证合法调用、缺失/错误签名、未知 serviceId、未知 kid、错误 audience、过长 TTL、disabled caller、缺少 RPC permission 和未允许 purpose。生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor，不能只验证同接口 fake server。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-020`（use-cases/UC-APP-020-manage-stable-publication-slot.md）：后续设计顺序、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `ADR-002`（adr/ADR-002-partition-publication-by-rpc-api-major.md）：背景、为什么不使用 platform/target、考虑过的替代方案、结果、关联用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/app-oauth-client-v1.md`（docs 根级共享文档）：GREY 扩展
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：Auth Center 固定授权映射、账号归属退出方法、Application 关闭方法

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-020-manage-stable-publication-slot.md` | 353 | `ed0e74da0b64` |
| `adr/ADR-001-scope-catalog-cache.md` | 114 | `bfe9459ac5d6` |
| `adr/ADR-002-partition-publication-by-rpc-api-major.md` | 84 | `ce434a38d0d1` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
| `platform/contracts/trusted-service-identity-v1.md` | 124 | `4a64372bc9c0` |
