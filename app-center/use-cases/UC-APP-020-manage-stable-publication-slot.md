# UC-APP-020：管理稳定发布槽位

状态：`PROPOSED`

## 目标与范围

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

## 已确认的设计选择

1. stable 与 test 一样按 `(applicationId, rpcApiMajor)` 分区，并共享同一个 Publication revision。
2. 设置或替换 stable 使用已批准 Version；不要求存在 test/grey 历史。
3. 清空是管理员的日常停止公开分发手段。平台紧急处置和 Application 级禁用由后续独立用例定义。
4. 回退不建立新状态；管理员把 stable 重新设置为一个当前仍具资格的历史 Version，即构成一次可审计回退。
5. Publication 在全部槽位为空时仍保留，不删除身份、revision 或历史。
6. 未来只允许在已有 stable 基线时建立 grey；存在 grey rollout 时不能清空 stable。
7. STABLE 使用独立于 TEST/GREY 的 OAuth registration 和 credential，但同一 Application 的 sector/sub 仍只由 Auth 按 Application 管理。

## 输入与身份

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

## 设置或替换主流程

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

## 清空主流程

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

## 异常流程

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

## 业务规则

<a id="br-pub-011"></a>
### BR-PUB-011：Stable 管理权限

设置、替换和清空 stable 的操作者必须具有可信 `APPROVED` Developer 身份，并在最终事务中仍是 Application 当前 admin。管理员转让先提交后，旧管理员不能改变 stable；发布操作先提交则形成一条完整审计事实。

<a id="br-pub-012"></a>
### BR-PUB-012：Stable 发布资格与直接发布

stableVersionId 只能引用同一 Application、覆盖当前 rpcApiMajor 且当前仍具有完整 APPROVED Review/snapshot 一致性的 Version。设置时还必须存在当前已批准公开资料。

Version 不需要曾进入 test 或 grey。设置 stable 不修改 Version 审核状态，不修改 test/grey，也不自动形成目录响应。一个 APPROVED Version 可以同时被多个 major 和多个槽位引用。

<a id="br-pub-013"></a>
### BR-PUB-013：公开默认目标边界

stable 是普通用户的默认发布目标，但本用例只保存权威指针。Application 进入公开候选目录还必须由后续 Catalog/Resolver 在同一查询语义中确认当前公开 Profile、Application 可用状态、exact-major Publication、Version 资格和 host capabilities。

没有 stable 的 Application 不进入普通公开候选集。TEST-only Application 后续只进入“我参与的测试”入口，不混入普通目录；Filter 只能影响客户端展示，不能代替 stable 资格或服务端授权。

<a id="br-pub-014"></a>
### BR-PUB-014：共享乐观并发与 no-op

test、grey、stable 和 clear 操作共享 Publication revision。首次由 set stable 创建时 revision=1；每次真实变化增加 1；revision 不匹配时不自动覆盖。目标已生效或 stable 已为空时是 no-op，不增加 revision、不写 History、不改变审计时间。

首次 set 必须预期不存在；已有记录上的 set/clear 必须携带精确正 revision。空 Publication 仍是“已存在”，后续设置必须使用它的当前 revision，不能再次用 null 创建。

<a id="br-pub-015"></a>
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

<a id="br-pub-016"></a>
### BR-PUB-016：设置前复检与 STABLE OAuth

真实设置 stable 前，必须按照 UC-APP-007 相同强度重新检查当前公开资料、批准 snapshot、Scope Catalog、LaunchURLSubmissionPolicy 和非空 OAuth redirect 所需的 registration/credential。检查结果针对 STABLE channel，TEST/GREY registration 不能代替。

STABLE identity 可以在 Publication 之前登记。client 为 DISABLED 不阻止管理员保存 stable 指针，但 Auth 必须拒绝该 client 的授权；空 redirect 数组允许发布，并表示相应 client type 在该 Version 上没有可用 OAuth 回调。

<a id="br-pub-017"></a>
### BR-PUB-017：清空、空记录与 Grey 基线

清空 stable 只移除 stable 指针，不删除 Publication。test 可以继续存在；未来 grey 必须以 stable 为基线，因此 greyRollout 非空时拒绝清空 stable。管理员应先清空 grey，再清空 stable。

清空不删除 OAuth identity、credential、grant、Version、Review、Profile 或历史。全部槽位为空时 Publication 进入 EMPTY 形态并保留 revision，使后续并发和审计连续。

<a id="br-pub-018"></a>
### BR-PUB-018：Stable 变化原子性

设置事务必须原子复查当前 admin、Version/Review/snapshot、Profile、STABLE registration/credential、Publication revision，并同时提交指针、revision、审计和 History。清空事务原子复查当前 admin、Publication revision、stable/grey 指针，并同时提交清空与 History。

与 test 修改、未来 grey 修改、管理员转让、审核资格撤销、Profile 切换或 OAuth registration 建立并发时，结果必须等价于某个明确先后顺序；失败不能留下部分状态。

<a id="br-pub-019"></a>
### BR-PUB-019：不隐式扩散

Stable set/clear 不得修改其他 rpcApiMajor、test/grey、Version 状态、Profile、Tester Membership 或 FilterRule，也不触发批量发布。一个 range 覆盖多个 major 时仍需逐 major 操作。

<a id="br-oac-012"></a>
### BR-OAC-012：STABLE OAuth channel 激活

UC-APP-020 被接受后，UC-APP-018 的五个管理员方法必须接受 channel=`STABLE`，并继续以 `(applicationId, channel)` 隔离 registration、clientId、status、authorizationEpoch 和 confidential credential。STABLE 与 TEST clientId 不共享，但都映射到同一 Application；Auth grant 继续以 `(authId, applicationId, channel)` 隔离。

UC-APP-019 的五个 Auth-only provider 方法必须支持 STABLE：

- runtime 使用 exact-major stableVersionId，不读取 test 或未来 grey。
- Auth 仍负责确认当前用户有效并提供可信 authId；App 的 authorization context 不要求 Tester Membership。共享契约中的 testerMembershipId 改为按渠道可空：TEST 必填，STABLE 为空。
- redirect/scopes/display 与 TEST 一样来自同一个批准 Version/Review/Profile snapshot。
- PublishedRedirectSnapshot 纳入已发布 STABLE major 的批准回调；仍忽略历史、草稿和未登记 type。
- 没有 stable、client channel 不匹配、Version/Profile 不一致或 client DISABLED 时失败关闭。

App 仍不保存 sector/sub，不签发 code/token。STABLE provider 扩展继续仅开放原生 gRPC，并复用现有五个方法级 service permission。

## 最小领域模型变化

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

## API 草图

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

具体 Proto package、HTTP annotation、错误 reason 和 Mongo migration 在进入 `ACCEPTED` 前补齐；不得改变既有 UC007 API 的 test 语义。

## 验收场景

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

## 依赖与实现边界

- 复用 UC-APP-007 的 Publication 聚合、History、批准事实复查、ScopeCatalog、LaunchURLSubmissionPolicy、Profile gate、Application 写栅栏和事务模型。
- 复用 UC-APP-018/019 的 registration/credential 与 Auth-only provider；实现时扩展渠道 allowlist，不建立第二套 OAuth 模型。
- 需要显式 migration 放宽历史 Publication 的 testVersionId 必填约束、增加 stableVersionId 与新的 History action/条件 validator；历史记录不重写。
- 需要同步修改独立 API 子模块和 [App OAuth provider 契约](../../platform/contracts/app-oauth-client-v1.md)，并做真实 App/Auth 跨服务验证。
- Catalog、统一启动解析、Application disable、Grey rollout 和 Filter 不属于本工作包；stable 指针可以先存在，但普通用户入口只有在后续查询契约完成后才形成产品闭环。

## 后续设计顺序

1. UC-APP-021：管理 Grey rollout，要求 stable 基线并定义已登录用户的确定性分桶。
2. Application 归档、管理员停用与平台紧急 suspension，统一影响目录、运行解析和 OAuth provider。
3. 统一运行目标解析 Query Contract，按 Tester test、命中 grey、stable 的顺序返回唯一目标。
4. 独立 ApplicationFilterRevision 的规则、审核和客户端求值契约。
5. 普通目录与“我参与的测试”两个查询入口。

## 变更记录

- 2026-10-04：建立 UC-APP-020 提案；定义 stable set/replace/clear、EMPTY Publication、直接稳定发布和 STABLE OAuth channel 激活方向。
