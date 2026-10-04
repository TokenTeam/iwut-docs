# UC-APP-023：解析 Application 的统一启动目标

状态：`ACCEPTED`

## 目标与范围

> App Center 根据可信的可选用户身份、宿主实际 RPC API major 与 capabilities，在一个 Application 的 Test、Grey、Stable 运行配置中解析唯一启动目标；显式 Tester 优先使用兼容 Test，已登录用户随后按服务端 Grey cohort 选择，其他情况使用兼容 Stable。

本用例负责：

- 按 exact `(applicationId, hostRpcApiMajor)` 读取 ApplicationPublication。
- 使用可信可选 authId 判断 ACTIVE Tester Membership 和 Grey cohort；没有身份时按匿名用户处理。
- 依照 `TEST > GREY > STABLE` 选择一个与宿主 capabilities 兼容的当前发布 Version。
- 复核所选 Version 的 Application 归属、APPROVED 状态、RPC range 和批准快照一致性。
- 返回携带解析 channel 的统一 `LaunchTargetDescriptor`。
- 为后续普通 Catalog、“我参与的测试”列表和 Application 详情提供单一解析语义。

本用例不负责：

- 返回 Application 列表、详情、公开 Profile 或 Filter；这些由后续 Catalog 查询组合。
- 执行客户端 Filter，或读取、接收、保存用户资料字段。
- 改变 Test/Grey/Stable、Tester Membership、Version、Profile、OAuth 或任何 revision。
- 清空 test、归档或禁用 Application、紧急 suspension，或定义这些状态的管理流程。
- 允许客户端自选 channel、versionId、rolloutId、bucket、Tester 身份或回退目标。
- 在线调用 Auth Scope Catalog、Launch URL、OAuth provider 或其他外部复检依赖。
- 建立运行租约、启动 session、WebView、RPC bridge、OAuth consent 或 token。

[UC-APP-012](UC-APP-012-resolve-test-launch-target-for-tester.md) 保留为严格的 Test-only 授权查询：它要求 ACTIVE Tester，且 Test 不可用时不回退。UC023 是面向统一运行入口的新查询；它在高优先级候选因当前宿主能力不足时继续尝试低优先级候选。

## 已有依赖与扩展边界

- [UC-APP-012](UC-APP-012-resolve-test-launch-target-for-tester.md) 已定义 Tester 授权、exact-major、Version 一致性、capabilities 和快照语义。
- [UC-APP-020](UC-APP-020-manage-stable-publication-slot.md) 已定义 Stable 是普通公开回退基线。
- [UC-APP-021](UC-APP-021-manage-grey-rollout.md) 已定义可信 authId、`grey-bucket-v1`、Stable 基线和 Grey 最小披露。
- [UC-APP-022](UC-APP-022-manage-application-filter.md) 已确认 Filter 不参与服务端运行选择。

当前 Application 没有归档、禁用或 suspension 状态，因此 UC023 首版只验证 Application 存在。后续引入这些状态时，统一解析必须把它们加入共同资格检查；不能在多个 Catalog 查询中各自发明不同的停用语义。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

请求：

```text
ResolveLaunchTargetQuery {
  hostRpcApiMajor: int32
  hostCapabilities: []CapabilityName
}
```

可信上下文：

```text
OptionalAuthenticatedUserIdentity {
  authId?: string
}
```

- 没有认证凭证表示匿名用户，可以解析 Stable。
- 存在认证凭证时必须先由入口完成验证并得到 authId；无效、过期或歧义凭证必须返回认证错误，不能静默降级为匿名。
- authId 不得来自 path、query、body、cookie 内的自由字段或应用自己签发的声明。

`hostRpcApiMajor >= 1`。hostCapabilities 沿用 [BR-RUN-005](UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005) 的名称和集合规范，入口去重并稳定排序。请求不能携带 channel、versionId、publicationRevision、membershipId、rolloutId、bucket、launchUrl 或 Filter 结果。

## 统一选择算法

Repository 在一个逻辑一致快照中读取 Application、exact-major Publication、调用用户的 ACTIVE Membership（若有）以及选择所需的 Version/Review 事实。

```text
resolve(applicationId, hostRpcApiMajor, hostCapabilities, trustedAuthId?)

1. 若 trustedAuthId 存在、ACTIVE Tester Membership 存在，且 Test 候选可运行：
     return TEST
2. 若 trustedAuthId 存在、GreyRollout 存在、grey-bucket-v1 命中，且 Grey 候选可运行：
     return GREY
3. 若 Stable 候选可运行：
     return STABLE
4. return unavailable
```

“候选可运行”同时要求：

- 对应 pointer/rollout 存在。
- Version 属于同一 Application。
- Version 当前仍为 APPROVED，批准 Review/snapshot 与当前 Version 内容一致。
- Version RPC range 覆盖 hostRpcApiMajor。
- `requiredCapabilities ⊆ hostCapabilities`。

Test 可以在没有 Stable 时为 ACTIVE Tester 成功解析，因此 test-only Application 可以由后续“我参与的测试”入口复用本查询。Grey 继续要求 Stable 基线；匿名用户不执行 Grey 分桶，直接尝试 Stable。

## 回退与损坏状态

回退只用于用户资格或当前宿主能力：

- 不是 ACTIVE Tester、没有 test pointer，或 Test 缺少宿主 capabilities：继续 Grey/Stable。
- 匿名、没有 Grey、未命中 Grey，或 Grey 缺少宿主 capabilities：继续 Stable。
- Stable 缺少宿主 capabilities：没有统一启动目标。

以下情况不是正常回退，而是持久化不变量异常：

- pointer 指向不存在、跨 Application 或非 APPROVED Version。
- Version RPC range 不覆盖其所在的 exact-major Publication。
- 当前 Version 与批准 Review/snapshot 不一致。
- Grey 没有 Stable、rolloutId/seed/比例不完整，或 Publication 结构损坏。

只要解析路径读取到上述损坏状态，就必须失败关闭并告警，不能用低优先级 Version 掩盖损坏。未授权用户不会仅为检查 Test 细节而加载 Test Version；Test 私有状态不能改变普通用户的 Stable 结果或通过错误差异泄露。

## 主流程

1. 验证可选可信身份、applicationId、hostRpcApiMajor 和 hostCapabilities。
2. 在同一 snapshot 中确认 Application 存在，并加载 exact-major Publication；不存在时返回统一目标不可用，不扫描其他 major。
3. 若存在可信 authId，读取该 Application 的 ACTIVE Tester Membership：
   - 有 Membership 且 test pointer 存在时，复核 Test Version 一致性。
   - capabilities 满足则立即选择 TEST；仅 capabilities 不足时继续。
4. 若尚未选择、存在可信 authId 且 Publication 有 GreyRollout：
   - 验证 Grey/Stable 结构完整。
   - 使用持久化 cohortSeed 和可信 authId 执行 `grey-bucket-v1`。
   - 命中时复核 Grey Version；capabilities 满足则选择 GREY，仅 capabilities 不足时继续。
5. 若尚未选择且 stable pointer 存在，复核 Stable Version；capabilities 满足则选择 STABLE。
6. 没有候选成功时返回 `ApplicationLaunchTargetUnavailable`，不返回各槽位、bucket、missing capability 或 Version 细节。
7. 成功时组装 `LaunchTargetDescriptor`，携带 channel 和解析 snapshot 的 publicationRevision。

## 结果

```text
LaunchTargetDescriptor {
  applicationId
  publicationId
  publicationRevision
  channel: TEST | GREY | STABLE
  rpcApiMajor
  versionId
  versionLabel
  launchUrl
  rpcApiMinVersion
  rpcApiMaxVersionExclusive
  requiredCapabilities
  requiredScopes
  optionalScopes
}
```

`channel` 是已解析运行环境，也是客户端后续选择同渠道 OAuth 配置所需的事实。结果不包含 client secret、client credential、Tester Membership、rolloutId、cohortSeed、bucket、exposureBasisPoints、其他槽位、其他 Version、Filter、Profile 审核信息或管理员身份。

首版沿用 UC012 的启动字段，不在本用例增加 OAuth clientId 发现。OAuth clientId 由既有 Application＋channel 注册管理和客户端配置边界提供；Auth 继续通过 UC019 的 provider 接口独立复核 clientId、channel、major 和用户资格。

## 异常流程

- 请求携带无效认证凭证：认证失败；不能降级为匿名。
- applicationId、hostRpcApiMajor 或 hostCapabilities 非法：稳定 INVALID_ARGUMENT。
- Application 不存在：`ApplicationNotFound`。
- exact-major Publication 不存在，或没有任何可运行候选：`ApplicationLaunchTargetUnavailable`。
- 所有实际可尝试的候选都因 hostCapabilities 不足而被跳过：仍返回 `ApplicationLaunchTargetUnavailable`，避免通过错误详情披露 Test/Grey 候选或 cohort。
- Publication、Grey、Version、Review 或 snapshot 不一致：`ApplicationRuntimeStateInconsistent`，对外 INTERNAL/不可用并记录不含规则正文、seed 或身份凭证的告警。
- 持久化读取失败：内部失败，不返回部分 Descriptor。

## 业务规则

<a id="br-run-011"></a>
### BR-RUN-011：可信可选身份与匿名语义

没有凭证的调用者按匿名用户处理，只能进入 Stable 路径。有效凭证提供的 authId 可以参与 Tester 和 Grey 判断；无效凭证不能降级。请求不得自报 authId、Tester、channel、bucket 或命中结果。

<a id="br-run-012"></a>
### BR-RUN-012：Exact-major 与统一快照

统一解析只读取 `(applicationId, hostRpcApiMajor)` 的 Publication，不扫描其他 major。Application、Membership、Publication、所需 Version/Review 和 Grey 配置来自同一逻辑一致快照；结果携带该 snapshot 的 publicationRevision。

<a id="br-run-013"></a>
### BR-RUN-013：兼容 Test 优先

可信 authId 具有 ACTIVE ApplicationTesterMembership、test pointer 存在且候选可运行时选择 TEST。管理员、Developer 或 Reviewer 身份不隐式取得优先级。Test 不要求 Stable 基线；非 Tester 不读取或披露 Test Version 细节。

<a id="br-run-014"></a>
### BR-RUN-014：服务端 Grey 选择

只有可信已登录 authId 使用当前 GreyRollout 的 cohortSeed 执行 [BR-PUB-023](UC-APP-021-manage-grey-rollout.md#br-pub-023) `grey-bucket-v1`。命中且候选可运行时选择 GREY；客户端不能提交或覆盖 bucket。匿名和未命中用户继续 Stable。

<a id="br-run-015"></a>
### BR-RUN-015：Stable 公开回退

未选择 Test/Grey 时只尝试 exact-major Stable。Grey 不会在缺少 Stable 时单独成为公开入口；普通用户没有 Stable 即没有统一目标。解析不从 APPROVED Version 列表猜测最新版。

<a id="br-run-016"></a>
### BR-RUN-016：能力回退与不变量失败关闭

高优先级候选仅因 `requiredCapabilities` 不被当前宿主覆盖时可以继续低优先级候选。跨 Application、非 APPROVED、RPC range/Review snapshot 漂移、悬空 pointer 或损坏 Grey 是内部不变量异常，不允许回退掩盖。

<a id="br-run-017"></a>
### BR-RUN-017：唯一目标与最小披露

成功只返回一个带 TEST/GREY/STABLE channel 的 LaunchTargetDescriptor，不返回候选集合、其他槽位、Tester Membership、Grey 分桶材料或 Filter 命中。失败不通过错误详情披露用户是否处于 Grey cohort。

<a id="br-run-018"></a>
### BR-RUN-018：只读热路径

统一解析不写领域访问日志，不修改任何聚合，也不调用 Scope Catalog、URL、OAuth 或 Auth profile 服务同步复检。发布命令和 OAuth provider 各自继续负责其资格边界；技术日志不得包含 token、seed、完整身份声明或用户资料。

<a id="br-run-019"></a>
### BR-RUN-019：并发快照语义

Membership 移除、Publication 修改或 rollout 调整与解析并发时，结果必须等价于一个明确 snapshot：快照前可见的变化影响本次结果，快照后的变化由后续解析观察。本查询不创建长期运行租约，也不保证响应发出后目标不变。

<a id="br-run-020"></a>
### BR-RUN-020：Catalog 复用与边界

后续普通 Catalog、Application 详情和“我参与的测试”查询必须复用本用例的目标选择语义，不各自重写 `TEST > GREY > STABLE`。Catalog 另外负责公开 Profile、候选集合和 Filter 分发；客户端负责 Filter 求值与实际启动。

## 最小查询模型

本用例不新增持久化领域实体：

```text
Application
ApplicationTesterMembership(ACTIVE)?
ApplicationPublication(applicationId, rpcApiMajor)
  testVersionId?
  greyRollout?
  stableVersionId?
ApplicationVersion(APPROVED)
ApplicationReview(APPROVED snapshot)
```

`LaunchTargetDescriptor` 是一次读取结果，不持久化，不形成 session/token，也不复制为新的运行配置权威。

## API 草图

```text
POST /v1/applications/{applicationId}/launch-target:resolve
Content-Type: application/json
Cache-Control: private, no-store
```

请求：

```json
{
  "hostRpcApiMajor": 4,
  "hostCapabilities": ["camera.read.v1", "user.profile.v1"]
}
```

成功：`200 OK`

```json
{
  "applicationId": "application-uuid",
  "publicationId": "publication-uuid",
  "publicationRevision": 9,
  "channel": "GREY",
  "rpcApiMajor": 4,
  "versionId": "version-uuid",
  "versionLabel": "v2.0.0",
  "launchUrl": "https://example.edu/apps/course-table/v2/",
  "rpcApiMinVersion": 4,
  "rpcApiMaxVersionExclusive": 5,
  "requiredCapabilities": ["user.profile.v1"],
  "requiredScopes": ["profile.basic"],
  "optionalScopes": ["schedule.read"]
}
```

独立 API package 建议为 `app_center.v1.runtime_resolution`，service 为 `RuntimeResolutionService`，方法为 `ResolveLaunchTarget`。现有 `CatalogService.ResolveTestLaunchTarget` 保持兼容，不由本 UC 删除或改变语义。

所有响应使用 `private, no-store`，避免把依赖身份、Tester 或 cohort 的结果进入共享缓存。Gateway 外部前缀继续由既有路由规则提供，不写进 Proto annotation。

## 验收场景

- ACTIVE Tester＋兼容 Test 返回 TEST，即使没有 Stable；非 Tester 看不到 test-only 目标。
- Tester 的 Test 缺少宿主 capability 时，命中兼容 Grey 则返回 GREY，否则兼容 Stable 返回 STABLE。
- 没有身份时不查询 Tester、不做 Grey 分桶，兼容 Stable 返回 STABLE。
- 已登录非 Tester 命中固定 Grey 向量时返回 GREY；未命中返回 Stable；客户端自报 channel/bucket 无效。
- Grey 缺少宿主 capability 时回退兼容 Stable；没有兼容 Stable 时返回统一不可用且不披露 cohort。
- exact-major Publication 不存在时不扫描其他 major；Stable 缺失时普通用户不从 Version 列表猜测目标。
- 悬空/跨 Application/非 APPROVED pointer、RPC range 漂移、snapshot 漂移和 Grey-without-Stable 均失败关闭，不回退。
- Membership 移除、Test/Stable 替换、Grey 比例调整/Clear 与解析竞争符合 snapshot 先后语义。
- 响应只有一个 channel/Version，不包含 seed、bucket、rolloutId、exposure、Membership、其他槽位或 Filter。
- 查询不写数据库，不调用 Scope/URL/OAuth/Auth profile；日志不记录 token、seed 或完整请求身份。
- HTTP 与原生 gRPC 使用相同解析器；匿名、有身份和无效凭证三种入口语义一致。
- 后续 Catalog 契约可以批量复用解析端口，而不复制渠道选择规则。

## 依赖与实现边界

- 数据依赖均已具备：UC012 Tester/Test、UC020 Stable、UC021 Grey 和共享 Publication/Version/Review 模型。
- 实现应抽取可批量复用的只读解析端口，避免未来列表对每个 Application 发起独立网络调用；是否使用 Mongo aggregation、snapshot transaction 或物化读模型属于实现选择，但必须满足一致性和无 N+1 外部调用。
- 不依赖 UC022 Filter 的存储即可完成目标选择；后续 Catalog 才把当前 FilterRevision 与本结果组合。
- Application disable/suspension 尚未建模，不阻塞当前 UC；该能力建立后必须在统一 resolver 的共同资格入口扩展。
- 本 UC 接受后再生成实现 brief、切换 App Center 工作包和实现 API/服务；普通列表/详情另建后续 UC。

## 后续设计顺序

1. 普通 Application Catalog 列表与详情，组合当前公开 Profile、统一启动目标和当前 Filter Revision。
2. “我参与的测试”列表，允许 test-only Application 进入独立入口。
3. Application 归档/管理员停用与平台 suspension，统一影响 Catalog、resolver 和 OAuth provider。
4. test clear、原子 Grey promote 等管理操作按实际体验补充。

## 变更记录

- 2026-10-04：设计接受；进入 brief 生成与后端实现。
- 2026-10-04：建立 UC-APP-023 提案；统一 Test/Grey/Stable 单 Application 解析，并固定可选可信身份、能力回退、损坏状态失败关闭及 Catalog 复用边界。
