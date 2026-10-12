<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-036 --spec tools/brief-specs/UC-APP-036.json -->
# Brief — UC-APP-036：清空测试发布槽位

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-036` 清空测试发布槽位 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-PUB-031`–`BR-PUB-036`（6 条） |
| 外部引用 BR | `BR-APP-015`、`BR-APP-022`、`BR-APP-027`，`BR-CAT-001`，`BR-PUB-001`、`BR-PUB-011`、`BR-PUB-014`、`BR-PUB-017`、`BR-PUB-018`，`BR-RUN-003`、`BR-RUN-016`（来自 `UC-APP-007`、`UC-APP-012`、`UC-APP-020`、`UC-APP-023`、`UC-APP-024`、`UC-APP-026`、`UC-APP-027`） |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/app-oauth-client-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

### 设计结论

> 具有 APPROVED Developer 身份的 Application 当前管理员，可以清空一个明确 RPC API major 的 Test 槽位。命令只移除 testVersionId，保留 Publication、其他槽位、Tester Membership、加入链接和 OAuth client。

本提案沿用 [UC020 Stable clear](../use-cases/UC-APP-020-manage-stable-publication-slot.md#清空主流程) 与 [UC021 Grey clear](../use-cases/UC-APP-021-manage-grey-rollout.md) 的共享 revision 和不可变 History。存在 ACTIVE Tester 不阻止清空，也不要求服务端额外确认；管理员可以在界面确认其操作，但人数不能成为新的领域前置条件。再设置 Test 后，既有 ACTIVE Tester 继续具有测试资格。

产品已审核接受本设计，可生成 brief 并开始实现。

### 目标与范围

负责 exact `(applicationId, rpcApiMajor)` 的 Test 清空、OCC、no-op、审计与运行读取兼容。它补齐 [UC007](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md) 的 set/replace 路径。

不负责移除 Tester、撤销链接、删除 Version/Review、清空 Stable/Grey、归档 Application、取消 Auth grant、恢复旧 Test 或批量操作多个 major。清空后重新发布仍调用 UC007 并执行当时的完整发布资格复检。

### 参与者与授权

调用者来自可信 DeveloperIdentity，developerStatus 必须为 APPROVED，且在最终事务中仍是 Application.adminId。这是与 [BR-PUB-001](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-001)、[BR-PUB-011](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-011) 相同的发布命令权限；本提案不放宽现有其他 clear 命令。

Application lifecycle 必须为 ACTIVE。平台 SUSPENDED 或管理员 ARCHIVED 时可清空配置；CLOSING/CLOSED 拒绝，包括空槽位 no-op。Reviewer、普通 Tester、SYSTEM 或平台运维权限都不隐式授权。

### 输入与 API 草图

在既有 `app_center.v1.application_publication.ApplicationPublication` service 新增：

```text
rpc ClearTestSlot(ClearTestSlotRequest) returns (ClearTestSlotResponse)
  DELETE /v1/applications/{application_id}/publications/{rpc_api_major}/test-slot

ClearTestSlotRequest {
  application_id
  rpc_api_major
  expected_publication_revision
}

ClearTestSlotResponse {
  changed
  publication: ApplicationPublicationResource
  history?: ApplicationPublicationHistoryResource
}
```

applicationId 为 UUIDv7，rpcApiMajor 为正 int32，expectedPublicationRevision 为正 int64。HTTP 沿用现有 ClearStableSlot/ClearGreyRollout 的唯一 query 参数 `expected_publication_revision`，不接收 body；重复参数、未知参数、路径覆盖参数和缺失/非规范正整数拒绝。gRPC 使用同一 request 字段。此 UC 不引入另一套 If-Match 约定。

成功和 no-op 均为 HTTP 200。HTTP 与原生 gRPC 的成功、no-op 和领域错误均设置 `Cache-Control: private, no-store`。响应复用既有 Publication/History 最小资源，不能包含 Grey seed、加入凭证、OAuth secret/hash 或额外 Tester 信息。

### 主流程与 no-op

1. 验证可信身份、Developer 资格、路径与正 expected revision。
2. 在同一 MongoDB majority transaction 中读取 Application，验证当前管理员和 ACTIVE lifecycle。
3. 读取 exact-major Publication，校验其身份、槽位组合、revision 与持久化字段；不存在时返回 not found，不能创建 EMPTY 占位。
4. 先检查 revision 精确匹配。过期 revision 即使 Test 已为空也必须冲突。
5. 若 testVersionId 已为空，返回当前 Publication、changed=false、history=null；不读取 Clock/IDGenerator、不更新 updatedAt/revision、coordinationRevision 或审计。
6. 若非空，取得 Application 共享 coordination fence，并在事务重试后重新复查管理权、lifecycle、Publication revision 与旧 Test 指针。
7. 为本次实际变化取得一次 historyId（UUIDv7）和 changedAt；事务重试复用同一 ID/时间。
8. 只把 testVersionId 置空，Publication revision 增加 1，更新 updatedBy/updatedAt，并原子追加 CLEAR_TEST_VERSION History。
9. 返回 changed=true、更新后的完整 Publication 和本次 History。失败全部回滚。

其他槽位保持原值。若所有槽位均为空，保留同一 publicationId 与新的正 revision；以后 UC007 set 必须携带该正 revision，不能再次表达“预期不存在”。

相同旧 expected revision 的网络重试会冲突；客户端重新读到清空后的 revision 再 clear 才返回 no-op。这里沿用共享 Publication OCC，不提供基于旧 revision 的命令结果重放。

### 清空前检查的边界

命令检查 Application、Publication 自身结构和共享 revision。Grey-without-Stable、非法槽位 ID、错误归属、无效 revision 或非法 Grey 结构属于 StateInconsistent，不能通过清空 Test 自动修复。

清空不重新验证旧目标的 Version、Review、Profile、OAuth config、Scope Catalog 或 launch URL。有效结构中即使旧 Test 目标已经悬空或失去运行资格，也允许移除这个指针，以便管理员停止分发；History 保存旧指针但不宣称其仍合格。这与 UC020 的减少可用性操作一致。

不读取 Tester 人数，不要求有或没有 ACTIVE 加入链接；Membership 数量和清空权限没有依赖关系。存储写入、revision/fence 溢出、删除或改写错误均整事务失败。

### PublicationHistory 与迁移

追加新 action，保留既有 SET_TEST 与所有 Stable/Grey 历史：

```text
CLEAR_TEST_VERSION {
  historyId, publicationId, applicationId, rpcApiMajor
  publicationRevision: new revision
  previousVersionId: previous testVersionId
  newVersionId: null
  approvedReviewId: null
  scopeCatalogRevision: null
  preflightPolicyVersion: null
  greyRolloutId: null
  previousExposureBasisPoints: null
  newExposureBasisPoints: null
  changedBy, changedAt
}
```

建议新增显式 migration `0029_test_publication_clear`，扩展 History validator 的 action 与条件字段组合，并提升 readiness；ApplicationPublication 已允许 Test 为空，无需新增业务字段或集合。fresh、顺序升级、重复运行与历史可读性必须一致。API 不重编号既有字段。

运行 adapter 中的 History action allowlist 与各槽位“最后一次相关 action”检查必须纳入 CLEAR_TEST_VERSION：Test 为空与 clear 事实一致；仍存在的 Stable/Grey 按自己的最近有效 History 校验，不能把最新 clear-test 当作它们失去批准依据。不能在 clear 之后从旧 SET_TEST 历史重新取回目标。

### 在线效果与 OAuth 边界

- [UC012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) 的纯 Test 解析在 clear 后返回 TestTargetUnavailable。
- [UC023](../use-cases/UC-APP-023-resolve-unified-launch-target.md) 在同一 snapshot 中按现有规则继续检查 Grey/Stable；不存在可兼容目标则 unavailable。
- [UC024](../use-cases/UC-APP-024-query-public-application-catalog.md) 的普通候选资格仍由 Stable 建立，清空 Test 不撤回 Stable-backed Catalog。
- [UC019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md) 的 exact-major TEST runtime/context 后续读取失败；STABLE/GREY、其他 major 和 client metadata/credential 管理继续遵守各自语义。
- PublishedRedirectSnapshot 重新计算当前已发布指针并集；只移除不再由任何当前有效槽位贡献的回调。不得全量清空一个跨 major 共用 client 的回调事实。

清空不推进 OAuth authorizationEpoch，不删除 client/credential，也不直接调用 Auth。Auth 在 authorize、code exchange、refresh、UserInfo 和在线 delegation 的当前运行上下文检查中消费这一变化；已经返回的短期快照与在途委托遵守 [App OAuth 契约](../../platform/contracts/app-oauth-client-v1.md) 的既有有效期，不能声称收回已交付响应或立即终止运行中的 WebView。

### 并发与错误

共享 revision 令 Test set/clear、Stable set/clear 和 Grey set/adjust/clear 的两个同 revision 实际变更最多一个提交。转让先提交后旧管理员不能清空；关闭先提交后不能清空；清空先提交则变更完整保留。查询可看到 clear 前或后的完整 snapshot，不能看到新 revision 配旧 Test 指针。

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/非法 Developer 身份 | 既有 DeveloperIdentity 错误 | 401 / UNAUTHENTICATED |
| Developer 非 APPROVED，或非当前管理员 | DEVELOPER_APPROVAL_REQUIRED / APPLICATION_ADMIN_REQUIRED | 403 / PERMISSION_DENIED |
| 非法 applicationId | INVALID_APPLICATION_ID（Publication namespace 新增） | 400 / INVALID_ARGUMENT |
| 非法 major、revision 或 HTTP 输入 | 既有 major/revision 输入错误 | 400 / INVALID_ARGUMENT |
| Application 或 exact Publication 不存在 | APPLICATION_PUBLICATION_NOT_FOUND | 404 / NOT_FOUND |
| revision 不匹配 | APPLICATION_PUBLICATION_REVISION_CONFLICT | 409 / ABORTED |
| CLOSING/CLOSED | APPLICATION_PUBLICATION_NOT_ALLOWED（新增） | 422 / FAILED_PRECONDITION |
| Publication 自身结构损坏 | APPLICATION_PUBLICATION_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储、ID、Clock 或技术字段溢出 | 既有 INTERNAL | 500 / INTERNAL |

UC036 的 path 校验独立于旧 Publication 命令的兼容错误分类；不把非法 Application ID 映射为 VersionNotFound，不改变既有 set/Stable/Grey clear 的错误行为。新增稳定 reason 与既有 enum 字段号兼容追加。

### 引用规则与实现输入

实现沿用 [BR-PUB-014](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-014)、[BR-PUB-017](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017)、[BR-PUB-018](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-018) 的共享 OCC、EMPTY 与原子性；转让/关闭依据 [BR-APP-015](../use-cases/UC-APP-026-transfer-application-administration.md#br-app-015)、[BR-APP-022](../use-cases/UC-APP-027-close-application.md#br-app-022)、[BR-APP-027](../use-cases/UC-APP-027-close-application.md#br-app-027)；在线读取分别遵守 [BR-RUN-003](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003)、[BR-RUN-016](../use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-016) 和 [BR-CAT-001](../use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-001)。这些引用只导航既有规则，不扩大本命令范围。

### 验收与交付边界

1. 清空 test-only、Test+Stable、Test+Grey+Stable 仅影响指定 Test；全空保留身份/revision，其他 major 不变。
2. 0、100 个 ACTIVE Tester、无链接或有效链接各组合都能清空；既有 episode 保留，重新 set 后仍可 Test 解析。
3. 匹配 revision 的空槽位 no-op 无 ID/Clock/fence/audit；不存在 Publication、缺失 revision、过期 revision 各自拒绝。
4. APPROVED/当前管理员/ACTIVE 校验在首次与 no-op 都成立；转让、关闭并发至少覆盖两个确定性胜序。
5. clear 与 Test/Stable/Grey 实际变更共用 revision，双 clear 至多一次新增 History；事务失败和溢出完整回滚。
6. 缺 Profile/旧目标悬空/外部依赖不可用不阻止清空；Publication 结构损坏失败，不能顺手修复。
7. 迁移接受新 History 合法形状并拒绝多余批准/Grey 字段，旧 SET/Stable/Grey 历史仍可读；所有运行读取处理新 action。
8. HTTP/gRPC 输入、成功/no-op/错误/no-store 与生成客户端均验证。
9. 真实 Mongo + App/Auth E2E 覆盖 clear 前后 TEST authorize、待兑换 code、refresh、UserInfo/delegation 的当前门禁；其他 major、STABLE/GREY 正常；重新 set 按当前资格恢复。

生成 brief 后由实现工作包交付 API、Domain/UseCase/Port、Mongo 事务/迁移、所有受影响读取与双服务验收。最终门禁为 `make check-auth-app`，因为此命令改变 Auth 消费的运行资格。

### 变更记录

- 2026-10-12：建立提案；建议允许有 ACTIVE Tester 时清空、保留全部 Membership，并沿用 Publication clear 的权限、query OCC 与审计。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；按 UC036 → UC037 → UC038 串行实现与验收。
- 2026-10-12：实施契约澄清：为已经接受的非法 Application ID 返回 400 语义追加 INVALID_APPLICATION_ID reason，限定 UC036，保留旧命令分类。

## 业务规则（UC-APP-036 权威正文）

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-031 -->
### BR-PUB-031：Test 清空权限与生命周期

清空者须为可信 APPROVED Developer 且在最终事务中为当前管理员，Application 须 ACTIVE；SUSPENDED/ARCHIVED 不阻止清空，CLOSING/CLOSED 拒绝。ACTIVE Tester 数量不构成额外前置或服务端确认。

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-032 -->
### BR-PUB-032：精确清空与依附状态保留

清空只修改指定 major 的 testVersionId。保留同一 Publication 和其他槽位，以及 Version、Review、Profile、Membership、链接和 OAuth client；全空时保留 EMPTY。清空不撤销 Tester 资格，重设 Test 继续使用现有 ACTIVE Membership。

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-033 -->
### BR-PUB-033：共享 OCC 与空槽位 no-op

Publication 必须已存在且正 expected revision 精确匹配，检查 revision 先于 no-op。已空返回 changed=false 和空 History，不推进 ID、Clock、fence、revision 或审计；旧 revision 重试仍冲突。

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-034 -->
### BR-PUB-034：Test 清空原子审计

真实清空、revision/audit 更新与 CLEAR_TEST_VERSION History 同事务提交或回滚。History 保存旧 Test 指针，new/Review/外部校验/Grey 字段为空，事实不可修改，事务重试复用同一审计身份和时间。

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-035 -->
### BR-PUB-035：减少分发不依赖目标复检

清空校验 Application 和 Publication 自身不变量；不依赖旧 Version/Review/Profile/OAuth 资格、Tester 人数或外部服务。Publication 自身损坏须失败关闭；可移除合法指针字段中已经不可运行的旧目标。

<!-- 权威位置: use-cases/UC-APP-036-clear-test-publication-slot.md#br-pub-036 -->
### BR-PUB-036：清空后的解析与并发顺序

clear 提交后的新权威读取不再取得该 major 的 Test 目标，纯 Test 失败，统一解析按既有 Grey/Stable 规则继续。变更与所有槽位写入、转让和关闭具有明确先后顺序；不得从旧 History 恢复 Test，或破坏其他槽位的 History 校验。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-026`

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-015 -->
### BR-APP-015：管理权 revision 与共享写栅栏

Application 持有正数 `ownershipRevision`，旧记录迁移为 1。发起时调用者提供 expectedOwnershipRevision，申请保存 sourceOwnershipRevision；只有接受成功使其增加 1。

转让与 Version、Profile、Publication、Tester、OAuth、Filter 及其他管理员写操作共用 Application `coordinationRevision` 写栅栏，并在最终事务中复查当前 admin。旧管理员持有的尚未过期 JWS 无需全局撤销：接受先提交时其后续写入因 adminId 不匹配而失败；旧管理员写入先提交时，其操作先线性化，接受再基于更新后的完整 Application 事实提交或失败。

`ownershipRevision` 是管理权 API 的业务 OCC，不替代 adapter-only coordinationRevision，也不因普通下级写入增加。

### 来自 `UC-APP-027`

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-022 -->
### BR-APP-022：CLOSING 即时本地隔离

CLOSING 是关闭生效点。所有目录、启动、Tester、审核、Publication、Filter、Version/Profile 管理和 OAuth provider 路径必须在最终边界要求 Application ACTIVE；缓存不能把旧 ACTIVE 结果延长到关闭事务之后。CLOSED 只表示跨服务撤销已经确认，不是首次停止服务的时刻。

<!-- 权威位置: use-cases/UC-APP-027-close-application.md#br-app-027 -->
### BR-APP-027：共享写栅栏与竞态

关闭与创建/接受/取消管理员转让、账号归属退出、Version/Profile/Review/Publication/Filter/Tester/OAuth 写操作共用 Application coordination fence；涉及账号时先按 authId 原始字节序锁全部 account_owner_exit_fences，再锁 Application。所有写入口必须在最终事务内复查 lifecycleStatus=ACTIVE，不能只依赖 handler 预读。

### 来自 `UC-APP-024`

<!-- 权威位置: use-cases/UC-APP-024-query-public-application-catalog.md#br-cat-001 -->
### BR-CAT-001：Stable 支撑的普通公开候选

普通 Catalog 只包含具有有效当前公开 Profile 和兼容 exact-major Stable 基线的 Application。Grey、Tester 或 APPROVED Version 本身不能建立普通公开资格；test-only Application 进入独立查询。

### 来自 `UC-APP-007`

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-001 -->
### BR-PUB-001：设置权限

设置者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

reviewer 批准 Version 不会替开发者作出发布选择。管理员转让后，新的当前 admin 可以修改已有 Publication。

### 来自 `UC-APP-020`

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-011 -->
### BR-PUB-011：Stable 管理权限

设置、替换和清空 stable 的操作者必须具有可信 `APPROVED` Developer 身份，并在最终事务中仍是 Application 当前 admin。管理员转让先提交后，旧管理员不能改变 stable；发布操作先提交则形成一条完整审计事实。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-014 -->
### BR-PUB-014：共享乐观并发与 no-op

test、grey、stable 和 clear 操作共享 Publication revision。首次由 set stable 创建时 revision=1；每次真实变化增加 1；revision 不匹配时不自动覆盖。目标已生效或 stable 已为空时是 no-op，不增加 revision、不写 History、不改变审计时间。

首次 set 必须预期不存在；已有记录上的 set/clear 必须携带精确正 revision。空 Publication 仍是“已存在”，后续设置必须使用它的当前 revision，不能再次用 null 创建。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017 -->
### BR-PUB-017：清空、空记录与 Grey 基线

清空 stable 只移除 stable 指针，不删除 Publication。test 可以继续存在；未来 grey 必须以 stable 为基线，因此 greyRollout 非空时拒绝清空 stable。管理员应先清空 grey，再清空 stable。

清空不删除 OAuth identity、credential、grant、Version、Review、Profile 或历史。全部槽位为空时 Publication 进入 EMPTY 形态并保留 revision，使后续并发和审计连续。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-018 -->
### BR-PUB-018：Stable 变化原子性

设置事务必须原子复查当前 admin、Version/Review/snapshot、Profile、STABLE registration/credential、Publication revision，并同时提交指针、revision、审计和 History。清空事务原子复查当前 admin、Publication revision、stable/grey 指针，并同时提交清空与 History。

与 test 修改、未来 grey 修改、管理员转让、审核资格撤销、Profile 切换或 OAuth registration 建立并发时，结果必须等价于某个明确先后顺序；失败不能留下部分状态。

### 来自 `UC-APP-012`

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003 -->
### BR-RUN-003：test 槽位优先且不回退

本用例只返回 Publication.testVersionId：

- 不读取或回退到 grey/stable。
- 不从全部 APPROVED Version 中自动挑选最新 sequence。
- 不因为调用者是 Tester 就改变 Publication。

如果 testVersionId 不存在或失去资格，本次 test 解析失败。未来统一启动解析可以定义 test/grey/stable 优先级，但不能隐式改变本用例。

### 来自 `UC-APP-023`

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-016 -->
### BR-RUN-016：能力回退与不变量失败关闭

高优先级候选仅因 `requiredCapabilities` 不被当前宿主覆盖时可以继续低优先级候选。跨 Application、非 APPROVED、RPC range/Review snapshot 漂移、悬空 pointer 或损坏 Grey 是内部不变量异常，不允许回退掩盖。

## 架构决定（仅本次需要的章节）

### ADR-003：Go package 与依赖边界（`ACCEPTED`）

#### 决定

代码首先按业务能力组织，每项能力内部再分 Domain、UseCase 与 Port：

```text
internal/application/domain
internal/application/usecase
internal/application/port
internal/version/domain
internal/version/usecase
internal/version/port
internal/profile/domain
internal/profile/usecase
internal/profile/port
internal/publication/...
internal/tester/...
internal/catalog/...
```

跨能力稳定且确实共享的类型放入小型 `internal/shared` package。只有在至少两个已实现能力出现相同语义时才提升为共享类型，不提前建立通用工具箱。

基础设施放在能力之外：

```text
internal/adapter/mongo
internal/adapter/auth
internal/adapter/transport
cmd/app-center
```

主要依赖方向为：

```text
transport -> usecase -> domain
adapter -> capability port + required domain types
composition root -> concrete implementations
```

Domain 不依赖 Kratos、MongoDB driver、Proto 生成包、HTTP、配置或具体日志实现。UseCase 只依赖 Domain 与当前能力声明的 ports。Adapter 实现 ports，composition root 负责组装。

能力间协作通过显式应用服务、port 或只读 Query 接口完成。一个能力不得直接导入另一个能力的 MongoDB document 或未导出的聚合内部结构。

当前代码树只使用表达业务职责的目录名，不以迁移阶段或实现世代划分代码。

#### Port 所有权

Port 由使用它的能力拥有，而不是由提供方或某个全局 infrastructure package 拥有。例如 Application 创建用例需要的原子持久化接口位于 `internal/application/port`，MongoDB adapter 在外部实现它。

Port 方法使用业务语言并表达所需原子边界，不先建立 `Save/Get/Delete` 式通用 Repository。只有多个实际用例证明通用操作具有相同语义时才抽取。

#### 自动化约束

代码仓库根目录的 `architecture_test.go` 作为 ADR 的可执行护栏，并由 `go test ./...` 自动运行。它至少强制以下规则：

- 业务能力的 Go 文件只能位于该能力的 `domain`、`usecase` 或 `port` package。
- Domain 的项目内依赖只能指向 `internal/shared`，并禁止 MongoDB、HTTP、Proto、配置、JSON 和具体日志依赖及 `bson/json/protobuf` struct tag。
- Port 只能依赖同能力 Domain 与 `internal/shared`。
- UseCase 只能依赖同能力 Domain、Port 与 `internal/shared`。
- `internal/shared` 不得反向依赖任何业务能力。
- Domain、UseCase、Port 与 `internal/shared` 默认不得新增第三方依赖；确需窄依赖时先接受相应架构变更并显式调整测试。
- 已接受的窄例外（2026-09-27，UC-APP-013）：仅 `internal/profile/domain` 可直接导入 `golang.org/x/text/unicode/norm`，用于 BR-PRF-003–005 的纯 NFC 规范化。它无网络、时钟或存储副作用；不扩大到 x/text 其他包、其他能力、UseCase、Port 或 shared。架构测试必须同时覆盖允许位置及这些拒绝位置。
- 具体 adapter package 之间不得互相导入；只有 transport adapter 可以导入 UseCase，MongoDB/Auth 等 provider adapter 只面向能力 Port 与必要的 Domain 类型。
- Adapter 不得读取 `internal/config`；只有 composition root 可以同时依赖配置与具体 adapter。
- 禁止全局 `internal/biz`、`internal/data`、`internal/domain`、`internal/service` 和 `internal/util` package。
- composition root 只位于 `cmd/app-center`。

自动化检查只维护依赖和物理结构，不推断业务语义，也不取代 BR 测试和评审。确有新依赖方向需求时，必须先修改本 ADR，再在同一变更中调整架构测试；不得通过删除、跳过或弱化测试绕过边界。

### ADR-004：MongoDB 事务与 Schema 管理（`ACCEPTED`）

#### 决定

App Center 的权威写模型使用支持多文档事务的 MongoDB 部署拓扑。开发、测试和生产至少运行 replica set 或其他被当前 MongoDB 版本明确支持事务的拓扑；不支持事务的 standalone 部署不属于受支持环境。

跨文档 BR 使用 MongoDB transaction 实现，并遵循：

- 事务内只执行本地 MongoDB 读写，不调用 Auth、HTTP、消息系统或其他远程服务。
- 外部校验在事务前完成；BR 要求最终复检的本地事实在事务内重新读取或通过条件写保护。
- transient transaction error 或 unknown commit result 按 MongoDB 官方语义重试完整事务/提交，不单独重试其中一次写入。
- 事务重试使用同一组命令输入、ID 与审计时间，避免一次逻辑操作产生多个身份或时间。
- 唯一索引、条件更新和事务共同保护并发不变量；应用层的预检查只用于改善错误体验。
- Adapter 把 duplicate key、write conflict 和事务失败映射为当前 port 能表达的稳定结果。

Repository port 优先暴露一个完整业务原子行为，例如 `CreateWithinQuota`。当一个 UseCase 必须协调多个独立聚合 Repository 时，可以引入窄的 Transaction Manager，但不能让 Domain 感知 MongoDB session。

#### Schema 与索引

collection、validator、索引和 schema revision 通过显式、版本化、可重复执行的迁移管理：

- 普通服务启动不创建、删除或修改生产索引与 validator。
- 迁移在部署前单独执行，并记录成功的 migration ID。
- 重复执行已成功迁移是安全的。
- 破坏性变更必须先有对应设计决定和恢复方案。
- 新集合从首次创建起使用明确的 validator 与命名索引。
- 集成测试验证实际索引、validator 和事务行为，而不仅测试 mapper。

具体 collection 名由对应 UC 的数据模型和实现工作包确定，不在本 ADR 中建立跨能力的统一 document 形状。

#### 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

### ADR-005：领域错误与 Transport 映射（`ACCEPTED`）

#### 决定

Domain 与 UseCase 使用协议无关的稳定错误分类。每个可预期业务失败具有：

```text
stable code
human-readable internal message
optional safe details
optional wrapped cause
```

稳定 code 使用设计文档中的业务失败名称。调用者通过错误类型、code 或 `errors.Is` 判断，不解析 message。

错误分为：

- Validation：输入无法形成合法值对象。
- Authentication：缺少或无效可信身份。
- Authorization：身份存在但没有执行权限。
- NotFound：目标不存在，或按隐私规则必须隐藏归属不匹配。
- Conflict：状态、唯一性、revision、容量或并发前置条件冲突。
- DependencyUnavailable：完成当前行为所需的外部事实暂不可用。
- Internal：未预期的实现或基础设施失败。

MongoDB/Auth 等 adapter 负责把技术错误转换为 port 定义的稳定结果，同时保留 cause。UseCase 再按业务上下文确定最终领域错误。例如 duplicate key 不能直接泄露索引名。

Transport adapter 在一个集中映射表中把领域错误转换为：

- 稳定 Proto error reason；
- canonical gRPC status；
- 对应 HTTP status；
- 可以安全返回的 message/details。

新 API 不采用“所有 HTTP 响应都返回 200，再在 JSON body 中表达错误”的形式。HTTP 与 gRPC 使用各自标准状态语义，稳定业务 code 供客户端做细分处理。

未知错误统一映射为 Internal，不向客户端返回 cause、数据库字段、索引名、远程地址、token、secret 或 stack trace。日志和 trace 在服务端保留原 cause，并使用同一 trace ID 关联。

#### 隐私与存在性隐藏

当 UC 规定跨 Application 的资源归属不匹配按 NotFound 处理时，Transport 不得把内部的“存在但不属于调用者”转换成 Forbidden。存在性隐藏属于业务契约，而不是展示文案。

错误 details 采用明确 allowlist。字段校验可以返回安全字段名和约束类别，但不能回显任意用户内容或凭证。

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

#### GREY 扩展

[UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md) 沿用同一组五个 provider 方法：GREY runtime 精确读取 exact-major GreyRollout 的 versionId；用户上下文使用 Publication 内部 cohortSeed 对可信 authId 重算 `grey-bucket-v1`，未命中时返回统一 runtime unavailable，不能披露 bucket 或 seed。GREY 不要求 Tester Membership，testerMembershipId 为空；批准回调进入 sector 并集。管理面启用独立 `(applicationId, GREY)` registration/credential，Auth grant 继续按 `(authId, applicationId, channel)` 隔离。

比例、目标 Version 或 Clear 都改变共享 publicationRevision，因此登录前 runtime tuple 不能跨 rollout 变化继续使用。Provider 不负责 `test > grey > stable` 默认路由；后续统一解析先选择 channel，Provider 再验证明确的 GREY client 和用户 cohort。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
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

- `UC-APP-026`（use-cases/UC-APP-026-transfer-application-administration.md）：目标与范围、参与者与依赖、输入与身份、生命周期、发起流程、接受流程、拒绝与取消、领域与数据模型、API 草图、错误边界、并发验收场景、实现依赖与交付边界、变更记录
- `UC-APP-027`（use-cases/UC-APP-027-close-application.md）：目标与范围、参与者与前置依赖、输入、预览与身份、生命周期与可见行为、发起关闭流程、本地关闭事务、Auth 持久撤销与最终收敛、领域与数据模型、API 草图、并发与验收场景、实现前决策结论、变更记录
- `UC-APP-024`（use-cases/UC-APP-024-query-public-application-catalog.md）：目标与范围、已有依赖与组合边界、输入与身份、普通公开候选资格、目标解析与 Filter 组合、公开结果模型、列表、排序与分页、列表主流程、详情主流程、错误与部分结果、最小查询模型与持久化影响、API 草图、验收场景、依赖检查与待确认设计选择、后续设计顺序、变更记录
- `UC-APP-007`（use-cases/UC-APP-007-place-approved-version-in-test-slot.md）：目标与范围、发布边界、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、迁移说明、变更记录
- `UC-APP-020`（use-cases/UC-APP-020-manage-stable-publication-slot.md）：目标与范围、已确认的设计选择、输入与身份、设置或替换主流程、清空主流程、异常流程、最小领域模型变化、API 草图、验收场景、依赖与实现边界、后续设计顺序、变更记录
- `UC-APP-012`（use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md）：目标与范围、业务边界、输入与身份、主流程、异常流程、最小查询模型、用例端口、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `UC-APP-023`（use-cases/UC-APP-023-resolve-unified-launch-target.md）：目标与范围、已有依赖与扩展边界、输入与身份、统一选择算法、回退与损坏状态、主流程、结果、异常流程、最小查询模型、API 草图、验收场景、依赖与实现边界、后续设计顺序、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/app-oauth-client-v1.md`（docs 根级共享文档）：三种生命周期、管理接口
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-036-clear-test-publication-slot.md` | 180 | `e0aa209d3e5f` |
| `use-cases/UC-APP-026-transfer-application-administration.md` | 324 | `7e93553d9cdd` |
| `use-cases/UC-APP-027-close-application.md` | 273 | `d2761c77847f` |
| `use-cases/UC-APP-024-query-public-application-catalog.md` | 338 | `88484d65cdb4` |
| `use-cases/UC-APP-007-place-approved-version-in-test-slot.md` | 567 | `d246090acbc7` |
| `use-cases/UC-APP-020-manage-stable-publication-slot.md` | 353 | `ed0e74da0b64` |
| `use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md` | 403 | `6db4e23c15a2` |
| `use-cases/UC-APP-023-resolve-unified-launch-target.md` | 305 | `30ae34bdccb2` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
