<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-021 --spec tools/brief-specs/UC-APP-021.json -->
# Brief — UC-APP-021：管理灰度发布

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-021` 管理灰度发布 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAC-013`，`BR-PUB-020`–`BR-PUB-030`（11 条） |
| 外部引用 BR | `BR-PUB-016`、`BR-PUB-017`（来自 `UC-APP-020`） |
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

### 已确认的设计选择

1. GreyRollout 按 `(applicationId, rpcApiMajor)` 保存于 ApplicationPublication，并与 Test、Stable 共用 Publication revision。
2. 暴露比例使用万分比 `exposureBasisPoints`，有效范围为 `1..10000`；停止灰度使用显式 Clear，不用比例 0 表达。
3. 只对可信的已登录 `authId` 分桶。相同 rollout、相同 authId 的结果在服务端实例、请求和设备之间一致。
4. 首次建立 rollout 时生成 32 字节 CSPRNG `cohortSeed` 和 UUIDv7 `rolloutId`。二者在比例调整和 Grey Version 替换时保持不变；Clear 后再次建立时重新生成。
5. 扩大暴露、首次建立和替换 Version 必须做完整发布复检；缩小暴露和 Clear 是风险收敛操作，不依赖外部 Scope/URL 服务。
6. Grey 可以暂时与 Stable 指向同一 Version。这允许先设置 Stable、再 Clear Grey 的两步提升，不建立隐式原子 Promote 行为。
7. GREY 使用独立于 TEST/STABLE 的 OAuth registration、credential 和 Auth grant；同一 Application 的 sector/sub 仍由 Auth 按 Application 管理。

### 输入与身份

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

### 建立、调整或替换主流程

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

### 清空主流程

1. 校验可信身份、路径和 expected revision。
2. 加载 Application 并确认调用者是当前 admin，再加载已有 Publication 并确认 revision 匹配。Publication 不存在时返回 NotFound。
3. 若 stableVersionId 为空且 GreyRollout 非空，返回内部不变量异常；若 stableVersionId 存在且 GreyRollout 已为空，返回当前 Publication、`changed=false`、`history=null`，不读取 Clock 或 IDGenerator。
4. 生成 historyId 和 changedAt，在同一事务中取得 Application 写栅栏，复查管理员、Publication revision、Stable/Grey 指针，然后：
   - 清空 GreyRollout。
   - 共享 revision 增加 1，更新 updatedBy/updatedAt。
   - 追加 `CLEAR_GREY_ROLLOUT` History。
5. 返回 `changed=true`。Stable 和 Test 均不改变；不调用 ScopeCatalog、URL 预检或 OAuth 外部依赖。

Clear 后旧 rolloutId/cohortSeed 不得复用。后续 Set 创建新的 rollout 和 cohort。

### 确定性分桶

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

### 异常流程

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

### 最小领域模型变化

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

### API 草图

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

### 验收场景

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

### 依赖与实现边界

- 依赖已完成的 UC-APP-007/020 Publication、共享 OCC/History、Application 写栅栏、Profile gate、ScopeCatalog 和 URL policy。
- 依赖 UC-APP-018/019 的 channel registration、credential 和 Auth-only provider；只扩展 GREY allowlist 与运行资格，不建立第二套 OAuth 模型。
- 需要 CSPRNG、HMAC-SHA-256、固定编码测试向量和 migration `0017_grey_rollout`。
- 需要同步独立 API 仓库与 App OAuth provider 跨服务契约，并以真实 MongoDB 和 App/Auth E2E 验证。
- 统一启动解析、Catalog、Filter、test clear、Application disable、Auth grant/code/token/sector/sub 和前端不属于本工作包。
- 实现必须使用生成 brief，并保持 API 子模块先提交、服务随后更新 gitlink 的交付顺序。

## 业务规则（UC-APP-021 权威正文）

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-oac-013 -->
### BR-OAC-013：GREY OAuth channel 与 cohort 资格

UC-APP-021 被接受后，UC-APP-018 的五个管理员方法接受 channel=`GREY`，继续以 `(applicationId, channel)` 隔离 registration、clientId、status、authorizationEpoch 和 confidential credential。GREY client 不能由 TEST/STABLE client 代替。

UC-APP-019 的五个 Auth-only provider 方法支持 GREY：

- runtime 精确读取请求 rpcApiMajor 的 GreyRollout Version，不读取 Test/Stable 作为替代。
- user authorization context 使用可信 authId 重新执行 `grey-bucket-v1`；未命中当前 cohort 时返回统一 runtime unavailable，不暴露 bucket/seed。
- GREY 与 STABLE 一样不要求 Tester Membership，testerMembershipId 为空。
- redirect/scopes/display 来自当前 Grey Version 的批准 Review/Profile snapshot；PublishedRedirectSnapshot 纳入当前已发布 Grey Version 的批准回调。
- runtime tuple 继续绑定 Publication revision；比例、目标或 Clear 改变后，旧 tuple 不能生成新授权上下文。

App 不生成 sector/sub，不签发 code/token。默认的 `test > grey > stable` 路由由后续统一解析契约负责；provider 只验证调用方明确请求的 GREY client 在当前用户和 runtime tuple 下是否有资格。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-020 -->
### BR-PUB-020：Grey 管理权限与 Stable 基线

只有 developerStatus=`APPROVED` 的当前 Application admin 可以管理 GreyRollout。Set 和 Clear 都要求目标 exact-major Publication 已存在且 stableVersionId 非空；Grey 不能单独形成普通公开入口。存在 Grey 时 [BR-PUB-017](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017) 继续禁止清空 Stable。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-021 -->
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

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-022 -->
### BR-PUB-022：Grey Version 发布资格

Grey Version 必须属于同一 Application、覆盖当前 rpcApiMajor，并保持完整 APPROVED Review/snapshot 一致性；Application 必须存在当前有效的 APPROVED ProfileRevision。Version 不要求曾进入 Test，也可以与 Stable 指向同一 Version。设置 Grey 不改变 Version 状态、Stable 或 Test。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-023 -->
### BR-PUB-023：确定性已登录用户分桶

Grey 只对可信已登录 authId 使用 `grey-bucket-v1` 计算。客户端不得自报 bucket、seed 或命中结果。相同 rollout/authId 的结果必须稳定；比例提高保持 cohort 单调扩张。匿名用户不参与分桶，由后续统一解析直接使用 Stable。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-024 -->
### BR-PUB-024：cohort 生命周期与最小披露

START 创建新的 rolloutId/cohortSeed；INCREASE、DECREASE 和 REPLACE 保留二者；Clear 结束该 rollout，后续 START 不得复用。cohortSeed 只能存在于内部当前状态和首次 SET 的内部审计事实，不通过任何外部资源、日志或指标披露。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-025 -->
### BR-PUB-025：共享 OCC、变化分类与 no-op

Grey 与 Test/Stable 共用 Publication revision。所有 Grey 命令要求正 expected revision 精确匹配；真实变化只增加一次 revision。相同 Version 和比例是 no-op。Set 必须分类为 START、INCREASE、DECREASE 或 REPLACE，以决定 seed 生命周期、History action 和外部复检强度。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-026 -->
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

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-027 -->
### BR-PUB-027：按风险方向复检

START、INCREASE、REPLACE 会新增用户或运行内容，必须按 [BR-PUB-016](../use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-016) 同等强度复查 Profile、Version/Review/snapshot、Scope、URL 和 GREY OAuth registration/credential。DECREASE 与 Clear 只收敛风险，不依赖外部检查；外部依赖故障不能阻止管理员降低或停止 Grey。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-028 -->
### BR-PUB-028：清空与损坏状态

Clear 只移除 GreyRollout，保留 Stable、Test、Publication 和历史。Publication 存在且 Grey 已空是 no-op；Publication 不存在是 NotFound。任何 Grey-without-Stable 或不完整 rollout 字段组合都是内部不变量异常，不以自动修复掩盖数据损坏。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-029 -->
### BR-PUB-029：Grey 变化原子性

最终事务必须取得 Application 写栅栏，复查当前管理员、Publication revision、Stable/Grey 状态，并按变化类型复查资格来源；Rollout、revision、审计和 History 必须一起提交。与 Test/Stable 修改、管理员转让、Profile 切换、Version 资格变化或 OAuth registration 建立并发时，结果必须等价于某个明确先后顺序。

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-030 -->
### BR-PUB-030：不隐式提升或扩散

Grey Set/Clear 不修改其他 rpcApiMajor、Test、Stable、Version 状态、Tester Membership 或 FilterRule。设置 Stable 为当前 Grey Version 不自动 Clear Grey；管理员随后显式 Clear 即完成两步提升。批量发布和原子 Promote 需要独立设计。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-020`

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-016 -->
### BR-PUB-016：设置前复检与 STABLE OAuth

真实设置 stable 前，必须按照 UC-APP-007 相同强度重新检查当前公开资料、批准 snapshot、Scope Catalog、LaunchURLSubmissionPolicy 和非空 OAuth redirect 所需的 registration/credential。检查结果针对 STABLE channel，TEST/GREY registration 不能代替。

STABLE identity 可以在 Publication 之前登记。client 为 DISABLED 不阻止管理员保存 stable 指针，但 Auth 必须拒绝该 client 的授权；空 redirect 数组允许发布，并表示相应 client type 在该 Version 上没有可用 OAuth 回调。

<!-- 权威位置: use-cases/UC-APP-020-manage-stable-publication-slot.md#br-pub-017 -->
### BR-PUB-017：清空、空记录与 Grey 基线

清空 stable 只移除 stable 指针，不删除 Publication。test 可以继续存在；未来 grey 必须以 stable 为基线，因此 greyRollout 非空时拒绝清空 stable。管理员应先清空 grey，再清空 stable。

清空不删除 OAuth identity、credential、grant、Version、Review、Profile 或历史。全部槽位为空时 Publication 进入 EMPTY 形态并保留 revision，使后续并发和审计连续。

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
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一；普通用户省略 |
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

App Center 首版只开放原生 gRPC 的 OAuth provider，不生成 HTTP annotation。完整方法与本地 caller registry permission 固定为：

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
      "auth.system-principal.resolve"
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

App Center registry 中 `iwut-auth-center` 只允许上述五个 `app.oauth.*` permission，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

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

- `UC-APP-021`（use-cases/UC-APP-021-manage-grey-rollout.md）：后续设计顺序、变更记录
- `UC-APP-020`（use-cases/UC-APP-020-manage-stable-publication-slot.md）：目标与范围、已确认的设计选择、输入与身份、设置或替换主流程、清空主流程、异常流程、最小领域模型变化、API 草图、验收场景、依赖与实现边界、后续设计顺序、变更记录
- `ADR-001`（adr/ADR-001-scope-catalog-cache.md）：背景、决定、为什么现在不上 RabbitMQ、未来何时引入事件、结果、参考
- `ADR-002`（adr/ADR-002-partition-publication-by-rpc-api-major.md）：背景、为什么不使用 platform/target、考虑过的替代方案、结果、关联用例、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：Auth Center 固定授权映射

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-021-manage-grey-rollout.md` | 352 | `e8650715ef24` |
| `use-cases/UC-APP-020-manage-stable-publication-slot.md` | 353 | `ed0e74da0b64` |
| `adr/ADR-001-scope-catalog-cache.md` | 114 | `bfe9459ac5d6` |
| `adr/ADR-002-partition-publication-by-rpc-api-major.md` | 84 | `ce434a38d0d1` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/app-oauth-client-v1.md` | 98 | `38d735de91e1` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `cfaa02fcbb8c` |
| `platform/contracts/trusted-service-identity-v1.md` | 112 | `696ad25845e5` |
