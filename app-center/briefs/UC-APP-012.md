<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-012 --spec tools/brief-specs/UC-APP-012.json -->
# Brief — UC-APP-012：为 Tester 解析 Application 的 test 启动目标

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-012` 为 Tester 解析 Application 的 test 启动目标 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-RUN-001`–`BR-RUN-010`（10 条） |
| 外部引用 BR | `BR-PUB-003`、`BR-PUB-007`，`BR-REV-004`、`BR-REV-013`、`BR-REV-014`，`BR-VER-006`（来自 `UC-APP-002`、`UC-APP-004`、`UC-APP-005`、`UC-APP-007`） |
| ADR | `ADR-006` |
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

> App Center 根据已认证用户的 ACTIVE Tester Membership、宿主实际 RPC API major 与 capabilities，为一个 Application 返回当前可运行的 test ApplicationVersion 启动描述。

本用例是服务端授权查询，不是客户端实现。它负责：

- 使用可信身份中的 authId 检查 Application 级 ACTIVE Tester Membership。
- 按 `(applicationId, hostRpcApiMajor)` 精确读取 ApplicationPublication。
- 取得该 Publication 当前 testVersionId。
- 复核 Version 仍属于同一 Application、保持 APPROVED，并兼容该 RPC major。
- 确认宿主 capabilities 覆盖 Version.requiredCapabilities。
- 返回一个内部一致的 TestLaunchDescriptor。

本用例不负责：

- 扫码、二维码页面或 Tester 加入流程。
- WebView 创建、页面导航、加载失败重试或前端缓存。
- Expo Host RPC bridge 的实现与握手细节。
- 客户端升级、应用商店发布或强制更新流程。
- Auth consent、token 签发或 scope 授权执行。
- 在没有 exact Publication 时搜索其他 RPC major 或猜测回退版本。
- 回退到 grey/stable，或改变任何发布槽位。
- 同步请求 launchUrl、重新抓取网页内容或重新运行 Scope Catalog/URL 预检。
- 创建领域访问日志或修改 Tester、Publication、Version。

调用方可以是官方客户端、Gateway 或其他受信入口适配器；“Tester”描述业务身份，“宿主运行上下文”描述兼容性输入，两者不意味着 App Center 负责客户端代码。

### 业务边界

解析链路是：

```text
authenticated authId
  + applicationId
  + hostRpcApiMajor
  + hostCapabilities
        │
        ▼
ACTIVE Tester Membership
        │
        ▼
ApplicationPublication(applicationId, hostRpcApiMajor)
        │ testVersionId
        ▼
compatible APPROVED ApplicationVersion
        │
        ▼
TestLaunchDescriptor
```

Tester 资格是 Application 级，RPC major 只参与 Publication/Version 解析。Membership 不会因为不同 major 而复制。

rpcApiMajor 和 capabilities 是运行兼容性声明，不单独构成授权。即使调用方伪造它们，也不能绕过 ACTIVE Membership；错误声明最多得到一个实际宿主无法运行的版本，因此官方入口仍应从宿主运行时而不是用户表单构造这些值。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

Query：

```text
ResolveTestLaunchTargetQuery {
  hostRpcApiMajor: int32
  hostCapabilities: []CapabilityName
}
```

可信身份：

```text
AuthenticatedUserIdentity {
  authId: string
}
```

authId 只能来自已认证上下文。请求不能指定 testerAuthId、membershipId、publicationId、versionId 或 launchUrl。

hostRpcApiMajor 必须 `>= 1`。hostCapabilities 使用集合语义，名称复用 [BR-VER-006](../use-cases/UC-APP-002-create-application-version.md#br-ver-006) 的规范；重复项在入口规范化后去重并按稳定字典序处理。

### 主流程

1. 从可信身份上下文取得 authId。
2. 校验 applicationId、hostRpcApiMajor 和 hostCapabilities 的格式。
3. Repository 使用同一一致性快照或等价查询边界加载：
   - Application 存在。
   - `(applicationId, authId)` 存在 ACTIVE Tester Membership。
   - `(applicationId, hostRpcApiMajor)` 存在 ApplicationPublication，且 testVersionId 非空。
   - testVersionId 指向同一 Application 的 ApplicationVersion。
4. 确认 Version：
   - reviewStatus=`APPROVED`。
   - `rpcApiMinVersion <= hostRpcApiMajor < rpcApiMaxVersionExclusive`。
   - 当前内容仍与批准并发布时的受审核内容一致。
5. 计算 `missingCapabilities = requiredCapabilities - hostCapabilities`；必须为空。
6. 组装并返回 TestLaunchDescriptor，同时携带 publicationRevision，供调用方诊断一次解析使用的发布快照。

本用例不锁定一个长期运行租约。解析成功后 Publication 可能立即改变；当前响应仍代表解析时一致快照，后续启动或刷新可以重新解析。

### 异常流程

- 缺少身份或 authId：`AuthenticatedUserRequired`。
- applicationId 非法：`InvalidApplicationId`。
- hostRpcApiMajor `< 1`：`InvalidHostRpcApiMajor`。
- capability 名称、数量或规范化结果非法：`InvalidHostCapabilities`。
- Application 不存在：`ApplicationNotFound`。
- 当前用户没有 ACTIVE Tester Membership：`ApplicationTesterRequired`。
- 指定 major 没有 Publication 或 testVersionId：`ApplicationTestTargetUnavailable`。
- hostCapabilities 缺少必需能力：`HostCapabilitiesInsufficient`，可以返回 missingCapabilities。
- Publication、Version、Review 或兼容关系不一致：`ApplicationTestPublicationInconsistent`，对外按暂不可用处理并触发内部告警。
- 持久化读取失败：内部失败，不返回部分 Descriptor。

必须先确认 Tester Membership，再向调用方暴露 test Publication/Version 细节。非 Tester 不应通过错误差异枚举测试版本。

### 最小查询模型

本用例不新增领域实体，只组合已有事实：

```text
ApplicationTesterMembership(ACTIVE)
ApplicationPublication(applicationId, rpcApiMajor, testVersionId, revision)
ApplicationVersion(APPROVED, rpcApiRange, requiredCapabilities, launch fields)
```

返回值：

```text
TestLaunchDescriptor {
  applicationId: ApplicationId
  publicationId: ApplicationPublicationId
  publicationRevision: int64
  rpcApiMajor: int32
  versionId: ApplicationVersionId
  versionLabel: VersionLabel
  launchUrl: LaunchURL
  rpcApiMinVersion: int32
  rpcApiMaxVersionExclusive: int32
  requiredCapabilities: []CapabilityName
  requiredScopes: []ScopeName
  optionalScopes: []ScopeName
}
```

Descriptor 是一次查询结果，不持久化为新 collection，也不是长期有效的 session/token。

### 用例端口

```go
type TestLaunchResolver interface {
    ResolveForTester(
        ctx context.Context,
        applicationID ApplicationID,
        testerAuthID AuthID,
        hostRpcAPIMajor int32,
        hostCapabilities []CapabilityName,
    ) (*TestLaunchDescriptor, error)
}
```

实现可以使用单个 MongoDB aggregation、只读事务或其他能提供逻辑一致快照的 Repository。端口必须区分身份不足、无 test target、capability 不足和内部状态不一致。

### API 草图

```text
POST /applications/{applicationId}/test-launch:resolve
Authorization: <authenticated user identity>
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
  "publicationRevision": 3,
  "rpcApiMajor": 4,
  "versionId": "version-uuid",
  "versionLabel": "v1.2.0-beta",
  "launchUrl": "https://example.edu/apps/course-table/v1.2/",
  "rpcApiMinVersion": 4,
  "rpcApiMaxVersionExclusive": 5,
  "requiredCapabilities": ["user.profile.v1"],
  "requiredScopes": ["profile.basic"],
  "optionalScopes": ["schedule.read"]
}
```

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- 不是 ACTIVE Tester：`403 Forbidden`。
- Application 不存在：`404 Not Found`。
- 当前 major 没有 test target：`404 Not Found`，错误码 `APPLICATION_TEST_TARGET_UNAVAILABLE`。
- 输入非法：`400 Bad Request`。
- 缺少 requiredCapabilities：`422 Unprocessable Content`。
- Publication/Version 内部不一致：对外 `503 Service Unavailable`，内部告警。

### 测试与验收

领域测试：

- exact rpcApiMajor、range 和 capability 子集判断正确。
- capabilities 输入按集合处理，重复和顺序不影响结果。
- Descriptor 不包含非 test 槽位、其他版本或 Tester 数据。

UseCase 测试：

- 只有 ACTIVE Tester 可以解析；Developer/admin 不具有隐式权限。
- REMOVED Membership 被拒绝。
- exact Publication 不存在时不搜索其他 major。
- testVersionId 不存在时不回退 grey/stable 或最新 APPROVED Version。
- requiredCapabilities 缺失时返回稳定 missingCapabilities。
- 成功返回 Publication revision 与完整启动必要字段。
- 查询不调用 ScopeCatalog、LaunchURLSubmissionPolicy 或任何写端口。

Repository 集成测试：

- Membership、Publication 和 Version 从一致快照组合。
- 跨 Application testVersionId、悬空 Version 和非 APPROVED Version 被拒绝并告警。
- Version range 不覆盖 Publication major 时被拒绝。
- Membership 移除、Publication 替换与解析并发符合快照语义。

API 与安全测试：

- authId、membershipId、publicationId、versionId 和 launchUrl 不能由请求指定。
- 非 Tester 不能通过错误响应枚举 test Version 细节。
- 响应设置 `Cache-Control: private, no-store`。
- 缺失 capabilities 只返回当前 Version 要求但宿主缺少的能力名。

### 实现依赖与交付边界

- UC-APP-007 已实现 Publication/History 与批准 Review 快照；UC-APP-009/010 已实现 ACTIVE/REMOVED Membership；可信普通用户身份、Version、MongoDB 副本集和 HTTP/gRPC/Wire 基础设施均可复用。UC007 尚未闭合的 Auth 权威 Scope Catalog 交付不阻塞本只读查询，因为 BR-RUN-008 禁止同步外部复检。
- 当前采用 MongoDB 只读 snapshot 事务，按 Application → 当前用户 ACTIVE Membership → exact-major Publication → 对应发布 History、Version 和批准 Review 的顺序组合事实。不得增加 coordinationRevision 写栅栏、访问计数、持久化 Descriptor 或查询外部服务；失败不返回部分结果。
- 按当前 Publication 的 publicationId/revision 精确取得 [BR-PUB-007](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007) 定义的发布 History，核对 applicationId、rpcApiMajor、newVersionId 与当前指针一致，并用其 approvedReviewId 定位本次发布的批准依据。依照 [BR-PUB-003](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003)、[BR-REV-013](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013)、[BR-REV-014](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014) 和 [BR-REV-004](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004) 检查当前批准状态、最新审核关系、revision 及受审核内容；缺失、悬空或漂移按 BR-RUN-004 处理，不只信任 APPROVED 字符串。
- 宿主上下文使用本 UC 已定义的请求正文。官方客户端/Gateway 从实际宿主运行时构造 major 与 capabilities；App Center 校验格式、按集合去重排序，并独立用可信 authId 检查 Tester 资格。不引入 capability 在线目录、宿主证明或额外授权机制，实际客户端接入独立交付。
- capability 名称仅复用 BR-VER-006 格式；hostCapabilities 的重复项按本 UC 去重，不沿用 requiredCapabilities 的重复拒绝规则，也不自行增加未定义的业务数量上限。
- 按 ADR-003 在 `internal/catalog/{domain,usecase,port}` 实现 Catalog & Resolution 查询能力，Mongo adapter 组合现有文档；领域/用例不直接导入其他能力的内部类型。现有 schema 可供读取，不预设新增 migration。
- 保持本 UC 的错误语义：缺少能力返回 HTTP422，内部 Publication/Version/Review 不一致返回 HTTP503/gRPC UNAVAILABLE 与安全告警；不套用 UC010/011 写命令的一致性异常 HTTP500 分类。成功及敏感错误响应遵守 private, no-store，不在授权前泄露版本细节。
- 前端/WebView、RPC bridge、Auth consent/token、Gateway 生产登录链路及后续公开资料用例均独立交付，不阻塞当前后端工作包。

## 业务规则（UC-APP-012 权威正文）

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-001 -->
### BR-RUN-001：Tester 授权

解析者必须是该 Application 的 ACTIVE Tester：

```text
membership.applicationId = applicationId
membership.testerAuthId = authenticated authId
membership.status = ACTIVE
```

Developer、admin 或 Reviewer 身份都不会隐式授予测试启动资格。admin 只有显式加入 Tester 列表后才能解析。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-002 -->
### BR-RUN-002：按 exact RPC major 解析

只读取业务键恰好为 `(applicationId, hostRpcApiMajor)` 的 Publication。不存在时返回不可用：

- 不扫描其他 major。
- 不根据 Version range 猜测某个 Publication。
- 不使用 clientBuildVersion、platform、target 或 versionLabel 作为分区键。

客户端强制升级策略属于客户端发布边界；App Center 只对调用时实际 major 作出解析。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-003 -->
### BR-RUN-003：test 槽位优先且不回退

本用例只返回 Publication.testVersionId：

- 不读取或回退到 grey/stable。
- 不从全部 APPROVED Version 中自动挑选最新 sequence。
- 不因为调用者是 Tester 就改变 Publication。

如果 testVersionId 不存在或失去资格，本次 test 解析失败。未来统一启动解析可以定义 test/grey/stable 优先级，但不能隐式改变本用例。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-004 -->
### BR-RUN-004：Version 一致性与发布资格

被解析 Version 必须：

- 属于同一 Application。
- 当前 reviewStatus=`APPROVED`。
- RPC range 覆盖 hostRpcApiMajor。
- 受审核内容与发布槽位设置时的批准事实保持一致。

发现悬空 testVersionId、跨 Application 引用、失去批准资格或内容漂移时不得返回 launchUrl，并必须产生内部一致性告警。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-005 -->
### BR-RUN-005：Capabilities 覆盖

宿主能力必须满足集合包含关系：

```text
Version.requiredCapabilities ⊆ hostCapabilities
```

宿主可以声明额外能力。缺少能力时返回稳定排序的 missingCapabilities；optional/required scopes 不属于宿主 capabilities，不参与该集合判断。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-006 -->
### BR-RUN-006：启动描述

成功结果只包含启动当前 test Version 所需的事实：

```text
TestLaunchDescriptor {
  applicationId
  publicationId
  publicationRevision
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

Descriptor 不包含 client secret、Tester 列表、审核备注、其他 Version 或其他 RPC major 的 Publication。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-007 -->
### BR-RUN-007：一致快照与并发

Membership、Publication 和 Version 必须来自一个逻辑一致的解析快照：

- 移除先于解析快照可见：解析失败。
- 解析快照先于移除：本次可以成功，后续解析失败。
- Publication 替换先于快照：返回新 testVersionId 和对应 revision。
- 快照先于替换：返回旧 testVersionId 和旧 revision，本次结果仍有效。

本用例不承诺响应发出后目标永远不变，也不创建运行租约。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-008 -->
### BR-RUN-008：只读且不做同步外部复检

解析不得修改 Membership、Publication、Version、Review 或 History，也不写领域“访问次数”。技术观测日志不属于领域事实。

解析不调用 Auth Scope Catalog、不请求 launchUrl、不执行 DNS/公网 HTTPS 预检。发布时复检和未来持续监控负责这些保证，避免把外部依赖加入启动热路径。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-009 -->
### BR-RUN-009：敏感信息与缓存

响应只对通过 Tester 授权的当前用户返回。HTTP 响应默认使用：

```text
Cache-Control: private, no-store
```

共享缓存不得按 applicationId 单独缓存授权结果。日志和 trace 可以记录 applicationId、versionId、publicationRevision 和错误类别，但不得记录 Auth token、TesterJoinLink secret 或用户 scopes 的授权 token。

<!-- 权威位置: use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md#br-run-010 -->
### BR-RUN-010：客户端与相邻上下文边界

App Center 的职责在返回 Descriptor 时结束。以下行为由其他组件负责：

- 客户端/WebView 使用 launchUrl 启动页面。
- Expo Host 提供 RPC bridge 和 capability 实现。
- Auth 根据 required/optional scopes 完成 consent 与 token 签发。
- 客户端升级系统处理过旧 rpcApiMajor。
- Gateway 决定如何把可信身份和宿主上下文传入本查询。

上述行为失败不会反向修改 Publication 或 Tester Membership。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-007`

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-003 -->
### BR-PUB-003：Version 发布资格

testVersionId 只能引用同一 Application 的 APPROVED Version。其最新 Review 必须是完整 APPROVED decision，Version 内容必须仍等于 snapshot，且 revision 关系必须一致。

审核状态一致性和 revision 的既有约束分别见 [BR-REV-013](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013) 与 [BR-REV-014](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014)；受审核快照字段见 [BR-REV-004](../use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004)。

`DRAFT/SUBMITTED/REJECTED/REVOKED` 都不能进入 test 槽位。历史上曾经 APPROVED 但当前已失去资格的 Version 也不能重新设置。

如果该运行上下文已经登记 OAuthClient，snapshot 中同 type 回调组的规范 hostname 必须等于 client.sector；改变 hostname 必须新建 clientId。snapshot 可以省略该 type，明确让当前 test 发布不提供 OAuth 回调；运行解析必须失败关闭，不能回退旧 Version。

<!-- 权威位置: use-cases/UC-APP-007-place-approved-version-in-test-slot.md#br-pub-007 -->
### BR-PUB-007：PublicationHistory

每次真实变化必须追加一条不可修改的 History：

```text
SET_TEST_VERSION {
  previousVersionId
  newVersionId
  approvedReviewId
  scopeCatalogRevision
  preflightPolicyVersion
  changedBy
  changedAt
  publicationRevision
}
```

首次设置 previousVersionId 为 null。替换时保留旧指针，不修改过去记录。no-op 不写 History。

History 是操作审计，不是 event sourcing 的权威状态；当前 Publication 才是槽位读取来源。

### 来自 `UC-APP-004`

<!-- 权威位置: use-cases/UC-APP-004-submit-application-version-review.md#br-rev-004 -->
### BR-REV-004：审核快照

ApplicationReview.snapshot 必须复制以下规范化字段：

```text
versionLabel
launchUrl
rpcApiMinVersion
rpcApiMaxVersionExclusive
requiredCapabilities
requiredScopes
optionalScopes
oauthRedirects
```

snapshot 创建后不可修改。Application.name 和独立的 ApplicationProfileRevision 不进入本次版本审核快照；公开目录资料由其自身的 revision 审核流程负责。

审核记录的 status 和后续决策审计可以发生一次受控状态迁移，但这不允许改写 snapshot、sourceVersionRevision、submittedBy 或 submittedAt。

### 来自 `UC-APP-005`

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-013 -->
### BR-REV-013：状态一致性

合法迁移只有：

```text
ApplicationReview: PENDING -> APPROVED
ApplicationVersion: SUBMITTED -> APPROVED

ApplicationReview: PENDING -> REJECTED
ApplicationVersion: SUBMITTED -> REJECTED
```

Review 和 Version 的结果必须相同。Version 内容必须等于 snapshot，且决定前 Version.revision 必须为 `sourceVersionRevision + 1`。不满足表示出现绕过用例的写入或数据损坏，应中止并告警，不能尝试自动修复。

<!-- 权威位置: use-cases/UC-APP-005-decide-application-version-review.md#br-rev-014 -->
### BR-REV-014：Version revision 与审计

决定成功后 Version.revision 原子增加 1，updatedBy 记录 decision.decidedBy，updatedAt 等于 decision.decidedAt。人工决定的 decidedBy 是 reviewer authId；暂停触发的自动拒绝使用注入的 System Auth ID。

createdBy、createdAt、submittedBy 和 submittedAt 都不因审核决定改变。审核人和审核时间属于 ApplicationReview.decision。

### 来自 `UC-APP-002`

<!-- 权威位置: use-cases/UC-APP-002-create-application-version.md#br-ver-006 -->
### BR-VER-006：requiredCapabilities

- capability 名称由客户端 RPC 契约定义并负责演进。当前格式是小写 ASCII 点分名称：版本后缀之前至少有一个名称段，每个名称段匹配 `[a-z][a-z0-9]*`，并以 `.v<正整数>` 结尾；正整数使用 `[1-9][0-9]*` 表示。例如 `camera.read.v1`。
- App Center 当前不查询中央 Capability Catalog，也不判断客户端实际是否提供该 capability；它只校验上述格式。
- 数组不得包含重复项；无额外要求时保存空数组，不保存 null。
- 校验通过后按 Unicode code point 字典序排序再保存；输入顺序不表达业务含义。

## 架构决定（仅本次需要的章节）

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

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-012`（use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md）：后续用例、变更记录
- `UC-APP-007`（use-cases/UC-APP-007-place-approved-version-in-test-slot.md）：目标与范围、发布边界、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、实现依赖与交付边界、后续用例、迁移说明、变更记录
- `UC-APP-004`（use-cases/UC-APP-004-submit-application-version-review.md）：目标与范围、提交结果、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、API 草图、测试与验收、后续用例、迁移说明、变更记录
- `UC-APP-005`（use-cases/UC-APP-005-decide-application-version-review.md）：目标与范围、参与者、决定结果、旧实现观察、输入、主流程、异常流程、最小领域行为、用例端口、数据模型变化、API 草图、测试与验收、已确认的实现边界、后续用例、迁移说明、变更记录
- `UC-APP-002`（use-cases/UC-APP-002-create-application-version.md）：目标与范围、当前 ApplicationVersion、旧实现观察、输入与身份、主流程、异常流程、最小领域模型、用例端口、数据模型、对 Application 持久化模型的影响、API 草图、测试与验收、后续接口工作、迁移说明、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md` | 403 | `6db4e23c15a2` |
| `use-cases/UC-APP-007-place-approved-version-in-test-slot.md` | 544 | `3e7d25287f64` |
| `use-cases/UC-APP-004-submit-application-version-review.md` | 509 | `f68b6f1eadb6` |
| `use-cases/UC-APP-005-decide-application-version-review.md` | 618 | `b213564fd3ae` |
| `use-cases/UC-APP-002-create-application-version.md` | 463 | `aed995d52573` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `cfaa02fcbb8c` |
