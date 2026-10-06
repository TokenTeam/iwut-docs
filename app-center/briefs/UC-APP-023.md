<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-023 --spec tools/brief-specs/UC-APP-023.json -->
# Brief — UC-APP-023：解析 Application 的统一启动目标

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-023` 解析 Application 的统一启动目标 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-RUN-011`–`BR-RUN-020`（10 条） |
| 外部引用 BR | `BR-PUB-023`，`BR-RUN-005`（来自 `UC-APP-012`、`UC-APP-021`） |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

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

[UC-APP-012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) 保留为严格的 Test-only 授权查询：它要求 ACTIVE Tester，且 Test 不可用时不回退。UC023 是面向统一运行入口的新查询；它在高优先级候选因当前宿主能力不足时继续尝试低优先级候选。

### 已有依赖与扩展边界

- [UC-APP-012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) 已定义 Tester 授权、exact-major、Version 一致性、capabilities 和快照语义。
- [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) 已定义 Stable 是普通公开回退基线。
- [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md) 已定义可信 authId、`grey-bucket-v1`、Stable 基线和 Grey 最小披露。
- [UC-APP-022](../use-cases/UC-APP-022-manage-application-filter.md) 已确认 Filter 不参与服务端运行选择。

当前 Application 没有归档、禁用或 suspension 状态，因此 UC023 首版只验证 Application 存在。后续引入这些状态时，统一解析必须把它们加入共同资格检查；不能在多个 Catalog 查询中各自发明不同的停用语义。

### 输入与身份

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

`hostRpcApiMajor >= 1`。hostCapabilities 沿用 [BR-RUN-005](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005) 的名称和集合规范，入口去重并稳定排序。请求不能携带 channel、versionId、publicationRevision、membershipId、rolloutId、bucket、launchUrl 或 Filter 结果。

### 统一选择算法

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

### 回退与损坏状态

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

### 主流程

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

### 结果

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

### 异常流程

- 请求携带无效认证凭证：认证失败；不能降级为匿名。
- applicationId、hostRpcApiMajor 或 hostCapabilities 非法：稳定 INVALID_ARGUMENT。
- Application 不存在：`ApplicationNotFound`。
- exact-major Publication 不存在，或没有任何可运行候选：`ApplicationLaunchTargetUnavailable`。
- 所有实际可尝试的候选都因 hostCapabilities 不足而被跳过：仍返回 `ApplicationLaunchTargetUnavailable`，避免通过错误详情披露 Test/Grey 候选或 cohort。
- Publication、Grey、Version、Review 或 snapshot 不一致：`ApplicationRuntimeStateInconsistent`，对外 INTERNAL/不可用并记录不含规则正文、seed 或身份凭证的告警。
- 持久化读取失败：内部失败，不返回部分 Descriptor。

### 最小查询模型

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

### API 草图

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

### 验收场景

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

### 依赖与实现边界

- 数据依赖均已具备：UC012 Tester/Test、UC020 Stable、UC021 Grey 和共享 Publication/Version/Review 模型。
- 实现应抽取可批量复用的只读解析端口，避免未来列表对每个 Application 发起独立网络调用；是否使用 Mongo aggregation、snapshot transaction 或物化读模型属于实现选择，但必须满足一致性和无 N+1 外部调用。
- 不依赖 UC022 Filter 的存储即可完成目标选择；后续 Catalog 才把当前 FilterRevision 与本结果组合。
- Application disable/suspension 尚未建模，不阻塞当前 UC；该能力建立后必须在统一 resolver 的共同资格入口扩展。
- 本 UC 接受后再生成实现 brief、切换 App Center 工作包和实现 API/服务；普通列表/详情另建后续 UC。

## 业务规则（UC-APP-023 权威正文）

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-011 -->
### BR-RUN-011：可信可选身份与匿名语义

没有凭证的调用者按匿名用户处理，只能进入 Stable 路径。有效凭证提供的 authId 可以参与 Tester 和 Grey 判断；无效凭证不能降级。请求不得自报 authId、Tester、channel、bucket 或命中结果。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-012 -->
### BR-RUN-012：Exact-major 与统一快照

统一解析只读取 `(applicationId, hostRpcApiMajor)` 的 Publication，不扫描其他 major。Application、Membership、Publication、所需 Version/Review 和 Grey 配置来自同一逻辑一致快照；结果携带该 snapshot 的 publicationRevision。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-013 -->
### BR-RUN-013：兼容 Test 优先

可信 authId 具有 ACTIVE ApplicationTesterMembership、test pointer 存在且候选可运行时选择 TEST。管理员、Developer 或 Reviewer 身份不隐式取得优先级。Test 不要求 Stable 基线；非 Tester 不读取或披露 Test Version 细节。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-014 -->
### BR-RUN-014：服务端 Grey 选择

只有可信已登录 authId 使用当前 GreyRollout 的 cohortSeed 执行 [BR-PUB-023](../use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-023) `grey-bucket-v1`。命中且候选可运行时选择 GREY；客户端不能提交或覆盖 bucket。匿名和未命中用户继续 Stable。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-015 -->
### BR-RUN-015：Stable 公开回退

未选择 Test/Grey 时只尝试 exact-major Stable。Grey 不会在缺少 Stable 时单独成为公开入口；普通用户没有 Stable 即没有统一目标。解析不从 APPROVED Version 列表猜测最新版。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-016 -->
### BR-RUN-016：能力回退与不变量失败关闭

高优先级候选仅因 `requiredCapabilities` 不被当前宿主覆盖时可以继续低优先级候选。跨 Application、非 APPROVED、RPC range/Review snapshot 漂移、悬空 pointer 或损坏 Grey 是内部不变量异常，不允许回退掩盖。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-017 -->
### BR-RUN-017：唯一目标与最小披露

成功只返回一个带 TEST/GREY/STABLE channel 的 LaunchTargetDescriptor，不返回候选集合、其他槽位、Tester Membership、Grey 分桶材料或 Filter 命中。失败不通过错误详情披露用户是否处于 Grey cohort。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-018 -->
### BR-RUN-018：只读热路径

统一解析不写领域访问日志，不修改任何聚合，也不调用 Scope Catalog、URL、OAuth 或 Auth profile 服务同步复检。发布命令和 OAuth provider 各自继续负责其资格边界；技术日志不得包含 token、seed、完整身份声明或用户资料。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-019 -->
### BR-RUN-019：并发快照语义

Membership 移除、Publication 修改或 rollout 调整与解析并发时，结果必须等价于一个明确 snapshot：快照前可见的变化影响本次结果，快照后的变化由后续解析观察。本查询不创建长期运行租约，也不保证响应发出后目标不变。

<!-- 权威位置: use-cases/UC-APP-023-resolve-unified-launch-target.md#br-run-020 -->
### BR-RUN-020：Catalog 复用与边界

后续普通 Catalog、Application 详情和“我参与的测试”查询必须复用本用例的目标选择语义，不各自重写 `TEST > GREY > STABLE`。Catalog 另外负责公开 Profile、候选集合和 Filter 分发；客户端负责 Filter 求值与实际启动。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-021`

<!-- 权威位置: use-cases/UC-APP-021-manage-grey-rollout.md#br-pub-023 -->
### BR-PUB-023：确定性已登录用户分桶

Grey 只对可信已登录 authId 使用 `grey-bucket-v1` 计算。客户端不得自报 bucket、seed 或命中结果。相同 rollout/authId 的结果必须稳定；比例提高保持 cohort 单调扩张。匿名用户不参与分桶，由后续统一解析直接使用 Stable。

### 来自 `UC-APP-012`

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005 -->
### BR-RUN-005：Capabilities 覆盖

宿主能力必须满足集合包含关系：

```text
Version.requiredCapabilities ⊆ hostCapabilities
```

宿主可以声明额外能力。缺少能力时返回稳定排序的 missingCapabilities；optional/required scopes 不属于宿主 capabilities，不参与该集合判断。

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

- `UC-APP-023`（use-cases/UC-APP-023-resolve-unified-launch-target.md）：后续设计顺序、变更记录
- `UC-APP-021`（use-cases/UC-APP-021-manage-grey-rollout.md）：目标与范围、已确认的设计选择、输入与身份、建立、调整或替换主流程、清空主流程、确定性分桶、异常流程、最小领域模型变化、API 草图、验收场景、依赖与实现边界、后续设计顺序、变更记录
- `UC-APP-012`（use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md）：目标与范围、业务边界、输入与身份、主流程、异常流程、最小查询模型、用例端口、API 草图、测试与验收、实现依赖与交付边界、后续用例、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-023-resolve-unified-launch-target.md` | 305 | `30ae34bdccb2` |
| `use-cases/UC-APP-021-manage-grey-rollout.md` | 352 | `5d63fc0c10b4` |
| `use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md` | 403 | `6db4e23c15a2` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
