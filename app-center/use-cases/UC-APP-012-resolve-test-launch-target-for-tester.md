# UC-APP-012：为 Tester 解析 Application 的 test 启动目标

状态：`PROPOSED`

## 目标与范围

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

## 业务边界

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

## 输入与身份

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

hostRpcApiMajor 必须 `>= 1`。hostCapabilities 使用集合语义，名称复用 [BR-VER-006](UC-APP-002-create-application-version.md#br-ver-006) 的规范；重复项在入口规范化后去重并按稳定字典序处理。

## 主流程

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

## 异常流程

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

## 业务规则

<a id="br-run-001"></a>
### BR-RUN-001：Tester 授权

解析者必须是该 Application 的 ACTIVE Tester：

```text
membership.applicationId = applicationId
membership.testerAuthId = authenticated authId
membership.status = ACTIVE
```

Developer、admin 或 Reviewer 身份都不会隐式授予测试启动资格。admin 只有显式加入 Tester 列表后才能解析。

<a id="br-run-002"></a>
### BR-RUN-002：按 exact RPC major 解析

只读取业务键恰好为 `(applicationId, hostRpcApiMajor)` 的 Publication。不存在时返回不可用：

- 不扫描其他 major。
- 不根据 Version range 猜测某个 Publication。
- 不使用 clientBuildVersion、platform、target 或 versionLabel 作为分区键。

客户端强制升级策略属于客户端发布边界；App Center 只对调用时实际 major 作出解析。

<a id="br-run-003"></a>
### BR-RUN-003：test 槽位优先且不回退

本用例只返回 Publication.testVersionId：

- 不读取或回退到 grey/stable。
- 不从全部 APPROVED Version 中自动挑选最新 sequence。
- 不因为调用者是 Tester 就改变 Publication。

如果 testVersionId 不存在或失去资格，本次 test 解析失败。未来统一启动解析可以定义 test/grey/stable 优先级，但不能隐式改变本用例。

<a id="br-run-004"></a>
### BR-RUN-004：Version 一致性与发布资格

被解析 Version 必须：

- 属于同一 Application。
- 当前 reviewStatus=`APPROVED`。
- RPC range 覆盖 hostRpcApiMajor。
- 受审核内容与发布槽位设置时的批准事实保持一致。

发现悬空 testVersionId、跨 Application 引用、失去批准资格或内容漂移时不得返回 launchUrl，并必须产生内部一致性告警。

<a id="br-run-005"></a>
### BR-RUN-005：Capabilities 覆盖

宿主能力必须满足集合包含关系：

```text
Version.requiredCapabilities ⊆ hostCapabilities
```

宿主可以声明额外能力。缺少能力时返回稳定排序的 missingCapabilities；optional/required scopes 不属于宿主 capabilities，不参与该集合判断。

<a id="br-run-006"></a>
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

<a id="br-run-007"></a>
### BR-RUN-007：一致快照与并发

Membership、Publication 和 Version 必须来自一个逻辑一致的解析快照：

- 移除先于解析快照可见：解析失败。
- 解析快照先于移除：本次可以成功，后续解析失败。
- Publication 替换先于快照：返回新 testVersionId 和对应 revision。
- 快照先于替换：返回旧 testVersionId 和旧 revision，本次结果仍有效。

本用例不承诺响应发出后目标永远不变，也不创建运行租约。

<a id="br-run-008"></a>
### BR-RUN-008：只读且不做同步外部复检

解析不得修改 Membership、Publication、Version、Review 或 History，也不写领域“访问次数”。技术观测日志不属于领域事实。

解析不调用 Auth Scope Catalog、不请求 launchUrl、不执行 DNS/公网 HTTPS 预检。发布时复检和未来持续监控负责这些保证，避免把外部依赖加入启动热路径。

<a id="br-run-009"></a>
### BR-RUN-009：敏感信息与缓存

响应只对通过 Tester 授权的当前用户返回。HTTP 响应默认使用：

```text
Cache-Control: private, no-store
```

共享缓存不得按 applicationId 单独缓存授权结果。日志和 trace 可以记录 applicationId、versionId、publicationRevision 和错误类别，但不得记录 Auth token、TesterJoinLink secret 或用户 scopes 的授权 token。

<a id="br-run-010"></a>
### BR-RUN-010：客户端与相邻上下文边界

App Center 的职责在返回 Descriptor 时结束。以下行为由其他组件负责：

- 客户端/WebView 使用 launchUrl 启动页面。
- Expo Host 提供 RPC bridge 和 capability 实现。
- Auth 根据 required/optional scopes 完成 consent 与 token 签发。
- 客户端升级系统处理过旧 rpcApiMajor。
- Gateway 决定如何把可信身份和宿主上下文传入本查询。

上述行为失败不会反向修改 Publication 或 Tester Membership。

## 最小查询模型

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

## 用例端口

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

## API 草图

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

## 测试与验收

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

## 实现前需要确认

- 官方客户端或 Gateway 如何提供规范化的 hostRpcApiMajor 与 hostCapabilities；这些输入不作为 Tester 授权来源。
- MongoDB 使用 aggregation 还是只读事务提供 Membership/Publication/Version 的逻辑一致快照。

## 后续用例

test 闭环到此完成。后续发布设计可以进入：

```text
为一个 RPC major 设置 grey 发布槽位与初始 rollout
调整 grey rollout 比例
提升为 stable
通过 PublicationHistory 回滚发布槽位
```

具体顺序和编号仍应由下一阶段业务目标及注册表的 Next ID 决定；本候选列表不预分配 ID。

## 变更记录

- 2026-09-16：建立 UC-APP-012；将原“客户端解析”重命名为 App Center 服务端查询“为 Tester 解析 test 启动目标”，明确客户端实现与 Auth consent 均在边界外。
