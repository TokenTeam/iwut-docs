# UC-APP-021：管理灰度发布

状态：`PROPOSED`

## 目标与范围

> developerStatus 为 `APPROVED` 的 Application 当前管理员，在一个已有 stable 基线的 rpcApiMajor 分区中建立、调整、替换或清空 Grey rollout，使已登录用户能够被服务端稳定地分入 Grey 或 Stable。

本用例负责：

- 在既有 `(applicationId, rpcApiMajor)` ApplicationPublication 中建立 GreyRollout。
- 用一个命令调整暴露比例或替换 Grey Version。
- 在连续 rollout 内保持稳定 cohort，避免比例或补丁版本变化造成用户无意义洗牌。
- 清空 GreyRollout，并保留 Stable、Publication revision 和追加式 History。
- 定义跨实现一致的已登录用户确定性分桶算法。
- 复用 Publication 共享 revision、批准事实、当前公开资料、Scope、URL 和 OAuth 检查。
- 激活 Application＋GREY channel 的 OAuth client 管理及 Auth provider 资格验证。

本用例不负责：

- 实现普通目录、应用详情或统一 `test > grey > stable` 启动解析接口。
- 为匿名用户执行 Grey 分桶；匿名用户只能使用 Stable。
- 清空 test 或 stable 槽位。
- 自动把 Grey Version 提升到 Stable，或在提升后自动清空 Grey。
- 定义 Application 归档、平台 suspension、FilterRule 或 Version 资格撤销。
- 收集实验指标、转化率或客户端遥测。
- 允许客户端自报 Grey 命中结果。

Grey 是服务端运行目标选择，不是新的 ApplicationVersion 状态，也不是访问权限或客户端 Filter。Grey 必须以同一分区的 Stable 为回退基线，但 Grey Version 不要求曾经进入 Test。

## 已确认的设计选择

1. GreyRollout 按 `(applicationId, rpcApiMajor)` 保存于 ApplicationPublication，并与 Test、Stable 共用 Publication revision。
2. 暴露比例使用万分比 `exposureBasisPoints`，有效范围为 `1..10000`；停止灰度使用显式 Clear，不用比例 0 表达。
3. 只对可信的已登录 `authId` 分桶。相同 rollout、相同 authId 的结果在服务端实例、请求和设备之间一致。
4. 首次建立 rollout 时生成 32 字节 CSPRNG `cohortSeed` 和 UUIDv7 `rolloutId`。二者在比例调整和 Grey Version 替换时保持不变；Clear 后再次建立时重新生成。
5. 扩大暴露、首次建立和替换 Version 必须做完整发布复检；缩小暴露和 Clear 是风险收敛操作，不依赖外部 Scope/URL 服务。
6. Grey 可以暂时与 Stable 指向同一 Version。这允许先设置 Stable、再 Clear Grey 的两步提升，不建立隐式原子 Promote 行为。
7. GREY 使用独立于 TEST/STABLE 的 OAuth registration、credential 和 Auth grant；同一 Application 的 sector/sub 仍由 Auth 按 Application 管理。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
rpcApiMajor: int32
```

建立、调整或替换命令：

```text
SetGreyRolloutCommand {
  versionId: ApplicationVersionId
  exposureBasisPoints: int32  // 1..10000
  expectedPublicationRevision: int64
}
```

清空命令：

```text
ClearGreyRolloutCommand {
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

Grey 必须依附已有 Stable，因此两个命令的 expected revision 均为必填正整数。请求不能指定 publicationId、rolloutId、cohortSeed、historyId、审核引用、外部策略版本、审计字段、OAuth clientId 或结果 revision。

## 建立、调整或替换主流程

1. 从可信身份取得 authId 和 developerStatus，校验 developerStatus=`APPROVED`、rpcApiMajor `>= 1`、versionId 为 UUIDv7、exposureBasisPoints 在 `1..10000`，expected revision 为正整数。
2. 加载 Application，确认调用者是当前 admin；再加载 ApplicationPublication，确认它属于目标 Application/major、revision 精确匹配且 stableVersionId 非空。记录损坏的 Grey-without-Stable 状态属于内部不变量异常。
3. 若当前 GreyRollout 的 versionId 和 exposureBasisPoints 已与命令相同，返回当前 Publication、`changed=false`、`history=null`；不调用外部服务，不读取 Clock、IDGenerator 或随机源。
4. 把真实变化分类为：
   - `START`：当前没有 GreyRollout。
   - `INCREASE`：Version 相同，新比例更大。
   - `DECREASE`：Version 相同，新比例更小。
   - `REPLACE`：Version 改变；比例可以同时改变。
5. `START`、`INCREASE` 和 `REPLACE` 完整验证：
   - Application 仍存在且管理关系未改变。
   - 当前公开 Profile 指向同一 Application 的有效 APPROVED ProfileRevision。
   - 目标 Version 属于该 Application、覆盖 rpcApiMajor，并保持完整 APPROVED Review/snapshot 一致性。
   - 按 Review snapshot 重新执行 ScopeCatalog 与 LaunchURLSubmissionPolicy。
   - Version 的 PKCE/confidential redirects 非空时，分别存在 GREY PUBLIC/CONFIDENTIAL registration；CONFIDENTIAL 还存在 credential。
6. `DECREASE` 只读取本地权威数据并验证当前管理员、Publication revision、Stable/Grey 状态，不调用 ScopeCatalog、URL 预检或 OAuth 外部依赖。
7. `START` 生成 rolloutId、32 字节 cohortSeed、historyId 和 changedAt。其他变化保留当前 rolloutId/cohortSeed，只生成 historyId 和 changedAt。
8. 在同一事务中取得 Application 写栅栏并重复相应检查，然后：
   - 写入新的 GreyRollout。
   - 共享 Publication revision 增加 1，更新 updatedBy/updatedAt。
   - 按变化类型追加一条不可变 History。
9. 返回 `changed=true`、完整 Publication 和本次 History。cohortSeed 不进入响应、日志、错误或普通追踪属性。

`REPLACE` 即使同时降低比例，仍按引入新运行内容处理，必须完成全部复检。目标 Version 与 Stable 相同时不报错，也不隐式 Clear Grey。

## 清空主流程

1. 校验可信身份、路径和 expected revision。
2. 加载 Application 并确认调用者是当前 admin，再加载已有 Publication 并确认 revision 匹配。Publication 不存在时返回 NotFound。
3. 若 stableVersionId 为空且 GreyRollout 非空，返回内部不变量异常；若 stableVersionId 存在且 GreyRollout 已为空，返回当前 Publication、`changed=false`、`history=null`，不读取 Clock 或 IDGenerator。
4. 生成 historyId 和 changedAt，在同一事务中取得 Application 写栅栏，复查管理员、Publication revision、Stable/Grey 指针，然后：
   - 清空 GreyRollout。
   - 共享 revision 增加 1，更新 updatedBy/updatedAt。
   - 追加 `CLEAR_GREY_ROLLOUT` History。
5. 返回 `changed=true`。Stable 和 Test 均不改变；不调用 ScopeCatalog、URL 预检或 OAuth 外部依赖。

Clear 后旧 rolloutId/cohortSeed 不得复用。后续 Set 创建新的 rollout 和 cohort。

## 确定性分桶

分桶输入只能使用服务端取得的可信 authId，不能使用请求正文、设备 ID、IP、cookie、clientId、Tester Membership 或可由应用选择的字段。

规范算法 `grey-bucket-v1`：

```text
auth = exact UTF-8 bytes of trusted authId
message = ASCII("iwut-grey-v1") || 0x00 || uint32be(len(auth)) || auth
digest = HMAC-SHA-256(key=cohortSeed, message=message)
bucket = uint64be(digest[0:8]) mod 10000
matched = bucket < exposureBasisPoints
```

authId 长度按 UTF-8 byte count 编码，不做大小写转换或 Unicode normalization。实现必须使用相同的无符号大端解释和取模方式，并提供跨实现固定测试向量。

在同一 rollout 内提高比例具有单调性：已经命中的用户不会因为比例增加而退出；降低比例只移除 bucket 较高的用户。替换 Grey Version 不改变 cohort。Clear 后新 rollout 使用新 seed，不承诺与旧 cohort 的关系。

cohortSeed 是内部随机材料，不是用户凭证，但不得通过管理员 API、Auth provider、日志、指标 label 或客户端响应披露。它保存在当前 GreyRollout，并在首次 SET History 的内部持久化事实中保留，以支持历史资格审计；普通 History API 不返回该字段。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 APPROVED：`DeveloperApprovalRequired`。
- rpcApiMajor、versionId、exposureBasisPoints 或 expected revision 非法：对应稳定输入错误。
- Application、Version 或 Publication 不存在：对应 NotFound；跨 Application 关系也按 NotFound 处理。
- 调用者不是当前管理员：`ApplicationAdminRequired`。
- 没有 stable 基线：`GreyStableBaselineRequired`，映射 HTTP 422 / gRPC FAILED_PRECONDITION。
- Version/Review 未批准、snapshot 损坏、Profile 缺失/损坏、RPC major 不兼容：复用 UC007/020 的对应错误。
- START、INCREASE 或 REPLACE 的 Scope、URL 或 OAuth 复检失败：复用既有错误；GREY registration 不能由 TEST/STABLE 替代。
- Publication revision 不匹配：既有 Publication conflict。
- Grey-without-Stable、rolloutId/seed/比例字段组合损坏：`ApplicationPublicationStateInconsistent`，映射 HTTP 500 / gRPC INTERNAL。
- 随机源、HMAC、ID、Clock、存储、revision 溢出或事务失败：内部失败；不得留下部分 Rollout、History 或 revision。

## 业务规则

<a id="br-pub-020"></a>
### BR-PUB-020：Grey 管理权限与 Stable 基线

只有 developerStatus=`APPROVED` 的当前 Application admin 可以管理 GreyRollout。Set 和 Clear 都要求目标 exact-major Publication 已存在且 stableVersionId 非空；Grey 不能单独形成普通公开入口。存在 Grey 时 [BR-PUB-017](UC-APP-020-manage-stable-publication-slot.md#br-pub-017) 继续禁止清空 Stable。

<a id="br-pub-021"></a>
### BR-PUB-021：Grey rollout 身份与比例

一个 ApplicationPublication 同时至多有一个 GreyRollout：

```text
GreyRollout {
  rolloutId: UUIDv7
  versionId: ApplicationVersionId
  exposureBasisPoints: 1..10000
  cohortSeed: 32 random bytes
}
```

比例 0 不表示对象状态；停止分流必须执行 Clear。10000 表示所有参与 Grey 分桶的已登录用户都命中，但 Stable 仍必须存在作为持久化基线和非 Grey/匿名回退目标。

<a id="br-pub-022"></a>
### BR-PUB-022：Grey Version 发布资格

Grey Version 必须属于同一 Application、覆盖当前 rpcApiMajor，并保持完整 APPROVED Review/snapshot 一致性；Application 必须存在当前有效的 APPROVED ProfileRevision。Version 不要求曾进入 Test，也可以与 Stable 指向同一 Version。设置 Grey 不改变 Version 状态、Stable 或 Test。

<a id="br-pub-023"></a>
### BR-PUB-023：确定性已登录用户分桶

Grey 只对可信已登录 authId 使用 `grey-bucket-v1` 计算。客户端不得自报 bucket、seed 或命中结果。相同 rollout/authId 的结果必须稳定；比例提高保持 cohort 单调扩张。匿名用户不参与分桶，由后续统一解析直接使用 Stable。

<a id="br-pub-024"></a>
### BR-PUB-024：cohort 生命周期与最小披露

START 创建新的 rolloutId/cohortSeed；INCREASE、DECREASE 和 REPLACE 保留二者；Clear 结束该 rollout，后续 START 不得复用。cohortSeed 只能存在于内部当前状态和首次 SET 的内部审计事实，不通过任何外部资源、日志或指标披露。

<a id="br-pub-025"></a>
### BR-PUB-025：共享 OCC、变化分类与 no-op

Grey 与 Test/Stable 共用 Publication revision。所有 Grey 命令要求正 expected revision 精确匹配；真实变化只增加一次 revision。相同 Version 和比例是 no-op。Set 必须分类为 START、INCREASE、DECREASE 或 REPLACE，以决定 seed 生命周期、History action 和外部复检强度。

<a id="br-pub-026"></a>
### BR-PUB-026：Grey PublicationHistory

真实变化追加一个不可变 History，action 为：

```text
SET_GREY_ROLLOUT
INCREASE_GREY_EXPOSURE
DECREASE_GREY_EXPOSURE
REPLACE_GREY_VERSION
CLEAR_GREY_ROLLOUT
```

History 保存 rolloutId、previous/new Version、previous/new exposure、changedBy/changedAt 和提交后的 publicationRevision。START、INCREASE 和 REPLACE 还保存 approvedReviewId、scopeCatalogRevision、preflightPolicyVersion；DECREASE/CLEAR 不伪造外部复检事实。使用独立的 INCREASE/DECREASE action，使持久化 validator 不需要比较两个数值才能判断外部事实是否必填。首次 SET 的内部持久化事实保存 cohortSeed，普通 API 永不返回。no-op 不写 History。

<a id="br-pub-027"></a>
### BR-PUB-027：按风险方向复检

START、INCREASE、REPLACE 会新增用户或运行内容，必须按 [BR-PUB-016](UC-APP-020-manage-stable-publication-slot.md#br-pub-016) 同等强度复查 Profile、Version/Review/snapshot、Scope、URL 和 GREY OAuth registration/credential。DECREASE 与 Clear 只收敛风险，不依赖外部检查；外部依赖故障不能阻止管理员降低或停止 Grey。

<a id="br-pub-028"></a>
### BR-PUB-028：清空与损坏状态

Clear 只移除 GreyRollout，保留 Stable、Test、Publication 和历史。Publication 存在且 Grey 已空是 no-op；Publication 不存在是 NotFound。任何 Grey-without-Stable 或不完整 rollout 字段组合都是内部不变量异常，不以自动修复掩盖数据损坏。

<a id="br-pub-029"></a>
### BR-PUB-029：Grey 变化原子性

最终事务必须取得 Application 写栅栏，复查当前管理员、Publication revision、Stable/Grey 状态，并按变化类型复查资格来源；Rollout、revision、审计和 History 必须一起提交。与 Test/Stable 修改、管理员转让、Profile 切换、Version 资格变化或 OAuth registration 建立并发时，结果必须等价于某个明确先后顺序。

<a id="br-pub-030"></a>
### BR-PUB-030：不隐式提升或扩散

Grey Set/Clear 不修改其他 rpcApiMajor、Test、Stable、Version 状态、Tester Membership 或 FilterRule。设置 Stable 为当前 Grey Version 不自动 Clear Grey；管理员随后显式 Clear 即完成两步提升。批量发布和原子 Promote 需要独立设计。

<a id="br-oac-013"></a>
### BR-OAC-013：GREY OAuth channel 与 cohort 资格

UC-APP-021 被接受后，UC-APP-018 的五个管理员方法接受 channel=`GREY`，继续以 `(applicationId, channel)` 隔离 registration、clientId、status、authorizationEpoch 和 confidential credential。GREY client 不能由 TEST/STABLE client 代替。

UC-APP-019 的五个 Auth-only provider 方法支持 GREY：

- runtime 精确读取请求 rpcApiMajor 的 GreyRollout Version，不读取 Test/Stable 作为替代。
- user authorization context 使用可信 authId 重新执行 `grey-bucket-v1`；未命中当前 cohort 时返回统一 runtime unavailable，不暴露 bucket/seed。
- GREY 与 STABLE 一样不要求 Tester Membership，testerMembershipId 为空。
- redirect/scopes/display 来自当前 Grey Version 的批准 Review/Profile snapshot；PublishedRedirectSnapshot 纳入当前已发布 Grey Version 的批准回调。
- runtime tuple 继续绑定 Publication revision；比例、目标或 Clear 改变后，旧 tuple 不能生成新授权上下文。

App 不生成 sector/sub，不签发 code/token。默认的 `test > grey > stable` 路由由后续统一解析契约负责；provider 只验证调用方明确请求的 GREY client 在当前用户和 runtime tuple 下是否有资格。

## 最小领域模型变化

```text
ApplicationPublication {
  publicationId
  applicationId
  rpcApiMajor
  testVersionId?
  greyRollout? {
    rolloutId
    versionId
    exposureBasisPoints
    cohortSeed       // internal only
  }
  stableVersionId?
  revision
  createdBy / createdAt
  updatedBy / updatedAt
}
```

不建立独立 GreyRollout 聚合或按用户保存分桶结果。当前 Publication 是运行配置权威；History 用于审计，不作为事件溯源状态。

## API 草图

```text
PUT    /v1/applications/{applicationId}/publications/{rpcApiMajor}/grey-rollout
DELETE /v1/applications/{applicationId}/publications/{rpcApiMajor}/grey-rollout
```

PUT body：

```json
{
  "versionId": "version-uuid",
  "exposureBasisPoints": 500,
  "expectedPublicationRevision": 7
}
```

DELETE 只通过 query 传递 `expected_publication_revision`，不接收 body。两个响应复用 `{ changed, publication, history? }`。

独立 API 仓库继续使用 `app_center.v1.application_publication.ApplicationPublicationService`，新增：

```text
SetGreyRollout
ClearGreyRollout
```

`ApplicationPublicationResource` 新增可空 `GreyRolloutResource grey_rollout`；资源只返回 rolloutId、versionId 和 exposureBasisPoints，不返回 cohortSeed。History 资源增加 Grey action 及可空 previous/new exposure、rolloutId 字段；内部 seed 不进入 Proto。

Application Publication error reason 追加：

```text
ERROR_REASON_GREY_STABLE_BASELINE_REQUIRED = 25
```

非法比例复用稳定 INVALID_ARGUMENT reason；Grey user 未命中在 OAuth provider 面复用 `ERROR_REASON_OAUTH_CLIENT_RUNTIME_UNAVAILABLE`，不建立可用于探测 bucket 的公开 reason。

Mongo migration 预留为 `0017_grey_rollout`：

- `application_publications` 接受完整 GreyRollout，并强制 `greyRollout => stableVersionId`。
- `application_publication_history` 接受五个 Grey action 及条件字段；既有 Test/Stable History 不重写。
- `application_oauth_registrations` channel validator 从 TEST/STABLE 扩展为 TEST/GREY/STABLE。
- migration ledger、fresh、0016→0017、重复执行、回滚和非法部分 rollout 均须验证。

## 验收场景

- 没有 Stable 或 Publication 不存在时不能建立 Grey。
- 可以对 APPROVED、exact-major Version 建立 1、500 或 10000 basis points 的 Grey；比例 0 和 10001 被拒绝。
- 首次 Set 生成 rolloutId/seed；响应和日志不含 seed。
- 相同 Version/比例是无外部调用、无 Clock/随机源的 no-op。
- 5%→20% 保留 rolloutId/seed，原 5% 用户仍命中；20%→5% 只移除高 bucket 用户。
- 替换 Grey Version 保留 cohort；即使同时降低比例也执行完整复检。
- 降低比例和 Clear 在 Scope/URL/OAuth 外部依赖不可用时仍可成功。
- Clear 保留 Stable、Test、Publication 与历史；再次 Set 生成新 rolloutId/seed。
- 相同 authId 在不同实例和设备上命中一致；固定跨实现向量验证 UTF-8、长度前缀、大端和取模。
- 匿名请求不做 Grey 分桶；客户端自报 bucket 或 channel 不能改变服务端结果。
- GREY registration/clientId/credential 与 TEST/STABLE 隔离，major 和 Version 变化不重建 clientId。
- 非 Grey 用户直接使用 GREY client 时，Auth provider 返回统一 runtime unavailable；Grey 用户可取得无 Tester Membership 的上下文。
- PublishedRedirectSnapshot 纳入当前 Grey Version，Clear 后不再纳入；DISABLED identity 仍按既有 sector 规则保留已发布回调事实。
- Grey 与 Test/Stable 命令使用相同 expected revision，并发命令最多一个提交。
- 设置 Stable 为 Grey Version 不自动 Clear Grey；显式 Clear 后所有用户使用 Stable channel。
- 管理员转让、Profile 切换、Version 资格变化、registration 建立和 Auth 解析竞争都有明确先后结果。
- 事务回滚不留下部分 rollout、孤立 History 或错误 revision。
- 0017 migration 对 fresh、sequential 和重复运行产生相同 validator/index 结果。

## 依赖与实现边界

- 依赖已完成的 UC-APP-007/020 Publication、共享 OCC/History、Application 写栅栏、Profile gate、ScopeCatalog 和 URL policy。
- 依赖 UC-APP-018/019 的 channel registration、credential 和 Auth-only provider；只扩展 GREY allowlist 与运行资格，不建立第二套 OAuth 模型。
- 需要 CSPRNG、HMAC-SHA-256、固定编码测试向量和 migration `0017_grey_rollout`。
- 需要同步独立 API 仓库与 App OAuth provider 跨服务契约，并以真实 MongoDB 和 App/Auth E2E 验证。
- 统一启动解析、Catalog、Filter、test clear、Application disable、Auth grant/code/token/sector/sub 和前端不属于本工作包。
- UC 进入 `ACCEPTED` 并生成 brief 前不得开始实现。

## 后续设计顺序

1. 统一运行目标解析 Query Contract，按有效 Tester Test、命中 Grey、Stable 返回唯一目标。
2. Application 归档、管理员停用与平台紧急 suspension，统一影响目录、运行解析和 OAuth provider。
3. 独立 ApplicationFilterRevision 的规则、审核和客户端求值契约。
4. 普通目录与“我参与的测试”两个查询入口。
5. test clear、原子 Grey promote 等后续操作按实际管理体验补充。

## 变更记录

- 2026-10-04：建立 UC-APP-021 提案；定义 Stable 基线、万分比分流、连续 rollout cohort、按风险方向复检和 GREY OAuth 扩展。
