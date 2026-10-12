# UC-APP-036：清空测试发布槽位

状态：`ACCEPTED`

## 设计结论

> 具有 APPROVED Developer 身份的 Application 当前管理员，可以清空一个明确 RPC API major 的 Test 槽位。命令只移除 testVersionId，保留 Publication、其他槽位、Tester Membership、加入链接和 OAuth client。

本提案沿用 [UC020 Stable clear](UC-APP-020-manage-stable-publication-slot.md#清空主流程) 与 [UC021 Grey clear](UC-APP-021-manage-grey-rollout.md) 的共享 revision 和不可变 History。存在 ACTIVE Tester 不阻止清空，也不要求服务端额外确认；管理员可以在界面确认其操作，但人数不能成为新的领域前置条件。再设置 Test 后，既有 ACTIVE Tester 继续具有测试资格。

产品已审核接受本设计，可生成 brief 并开始实现。

## 目标与范围

负责 exact `(applicationId, rpcApiMajor)` 的 Test 清空、OCC、no-op、审计与运行读取兼容。它补齐 [UC007](UC-APP-007-place-approved-version-in-test-slot.md) 的 set/replace 路径。

不负责移除 Tester、撤销链接、删除 Version/Review、清空 Stable/Grey、归档 Application、取消 Auth grant、恢复旧 Test 或批量操作多个 major。清空后重新发布仍调用 UC007 并执行当时的完整发布资格复检。

## 参与者与授权

调用者来自可信 DeveloperIdentity，developerStatus 必须为 APPROVED，且在最终事务中仍是 Application.adminId。这是与 [BR-PUB-001](UC-APP-007-place-approved-version-in-test-slot.md#br-pub-001)、[BR-PUB-011](UC-APP-020-manage-stable-publication-slot.md#br-pub-011) 相同的发布命令权限；本提案不放宽现有其他 clear 命令。

Application lifecycle 必须为 ACTIVE。平台 SUSPENDED 或管理员 ARCHIVED 时可清空配置；CLOSING/CLOSED 拒绝，包括空槽位 no-op。Reviewer、普通 Tester、SYSTEM 或平台运维权限都不隐式授权。

## 输入与 API 草图

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

## 主流程与 no-op

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

## 清空前检查的边界

命令检查 Application、Publication 自身结构和共享 revision。Grey-without-Stable、非法槽位 ID、错误归属、无效 revision 或非法 Grey 结构属于 StateInconsistent，不能通过清空 Test 自动修复。

清空不重新验证旧目标的 Version、Review、Profile、OAuth config、Scope Catalog 或 launch URL。有效结构中即使旧 Test 目标已经悬空或失去运行资格，也允许移除这个指针，以便管理员停止分发；History 保存旧指针但不宣称其仍合格。这与 UC020 的减少可用性操作一致。

不读取 Tester 人数，不要求有或没有 ACTIVE 加入链接；Membership 数量和清空权限没有依赖关系。存储写入、revision/fence 溢出、删除或改写错误均整事务失败。

## PublicationHistory 与迁移

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

## 在线效果与 OAuth 边界

- [UC012](UC-APP-012-resolve-test-launch-target-for-tester.md) 的纯 Test 解析在 clear 后返回 TestTargetUnavailable。
- [UC023](UC-APP-023-resolve-unified-launch-target.md) 在同一 snapshot 中按现有规则继续检查 Grey/Stable；不存在可兼容目标则 unavailable。
- [UC024](UC-APP-024-query-public-application-catalog.md) 的普通候选资格仍由 Stable 建立，清空 Test 不撤回 Stable-backed Catalog。
- [UC019](UC-APP-019-resolve-oauth-authorization-context.md) 的 exact-major TEST runtime/context 后续读取失败；STABLE/GREY、其他 major 和 client metadata/credential 管理继续遵守各自语义。
- PublishedRedirectSnapshot 重新计算当前已发布指针并集；只移除不再由任何当前有效槽位贡献的回调。不得全量清空一个跨 major 共用 client 的回调事实。

清空不推进 OAuth authorizationEpoch，不删除 client/credential，也不直接调用 Auth。Auth 在 authorize、code exchange、refresh、UserInfo 和在线 delegation 的当前运行上下文检查中消费这一变化；已经返回的短期快照与在途委托遵守 [App OAuth 契约](../../platform/contracts/app-oauth-client-v1.md) 的既有有效期，不能声称收回已交付响应或立即终止运行中的 WebView。

## 并发与错误

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

## 业务规则

<a id="br-pub-031"></a>
### BR-PUB-031：Test 清空权限与生命周期

清空者须为可信 APPROVED Developer 且在最终事务中为当前管理员，Application 须 ACTIVE；SUSPENDED/ARCHIVED 不阻止清空，CLOSING/CLOSED 拒绝。ACTIVE Tester 数量不构成额外前置或服务端确认。

<a id="br-pub-032"></a>
### BR-PUB-032：精确清空与依附状态保留

清空只修改指定 major 的 testVersionId。保留同一 Publication 和其他槽位，以及 Version、Review、Profile、Membership、链接和 OAuth client；全空时保留 EMPTY。清空不撤销 Tester 资格，重设 Test 继续使用现有 ACTIVE Membership。

<a id="br-pub-033"></a>
### BR-PUB-033：共享 OCC 与空槽位 no-op

Publication 必须已存在且正 expected revision 精确匹配，检查 revision 先于 no-op。已空返回 changed=false 和空 History，不推进 ID、Clock、fence、revision 或审计；旧 revision 重试仍冲突。

<a id="br-pub-034"></a>
### BR-PUB-034：Test 清空原子审计

真实清空、revision/audit 更新与 CLEAR_TEST_VERSION History 同事务提交或回滚。History 保存旧 Test 指针，new/Review/外部校验/Grey 字段为空，事实不可修改，事务重试复用同一审计身份和时间。

<a id="br-pub-035"></a>
### BR-PUB-035：减少分发不依赖目标复检

清空校验 Application 和 Publication 自身不变量；不依赖旧 Version/Review/Profile/OAuth 资格、Tester 人数或外部服务。Publication 自身损坏须失败关闭；可移除合法指针字段中已经不可运行的旧目标。

<a id="br-pub-036"></a>
### BR-PUB-036：清空后的解析与并发顺序

clear 提交后的新权威读取不再取得该 major 的 Test 目标，纯 Test 失败，统一解析按既有 Grey/Stable 规则继续。变更与所有槽位写入、转让和关闭具有明确先后顺序；不得从旧 History 恢复 Test，或破坏其他槽位的 History 校验。

## 引用规则与实现输入

实现沿用 [BR-PUB-014](UC-APP-020-manage-stable-publication-slot.md#br-pub-014)、[BR-PUB-017](UC-APP-020-manage-stable-publication-slot.md#br-pub-017)、[BR-PUB-018](UC-APP-020-manage-stable-publication-slot.md#br-pub-018) 的共享 OCC、EMPTY 与原子性；转让/关闭依据 [BR-APP-015](UC-APP-026-transfer-application-administration.md#br-app-015)、[BR-APP-022](UC-APP-027-close-application.md#br-app-022)、[BR-APP-027](UC-APP-027-close-application.md#br-app-027)；在线读取分别遵守 [BR-RUN-003](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003)、[BR-RUN-016](UC-APP-023-resolve-unified-launch-target.md#br-run-016) 和 [BR-CAT-001](UC-APP-024-query-public-application-catalog.md#br-cat-001)。这些引用只导航既有规则，不扩大本命令范围。

## 验收与交付边界

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

## 变更记录

- 2026-10-12：建立提案；建议允许有 ACTIVE Tester 时清空、保留全部 Membership，并沿用 Publication clear 的权限、query OCC 与审计。
- 2026-10-12：产品审核通过，状态转为 ACCEPTED；按 UC036 → UC037 → UC038 串行实现与验收。
- 2026-10-12：实施契约澄清：为已经接受的非法 Application ID 返回 400 语义追加 INVALID_APPLICATION_ID reason，限定 UC036，保留旧命令分类。
