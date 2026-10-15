# Version 审核决定接入准备

状态：`OPEN`

核对日期：2026-10-16。关联 [UC-CONSOLE-006](../use-cases/UC-CONSOLE-006-review-application-versions.md)、[BR-CRV-001](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-001)、[BR-CRV-002](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-002) 与 [BR-CRV-003](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-003)。

本页是 Console 消费已有后端能力的依赖跟踪记录，不新增或替代 App/Gateway 业务规则。审核查询和决定已经存在，UC006 可以继续接受和实施；完整决定流程需要补齐下面两个具体接入项。队列、详情、权限恢复、表单和结果未知状态机可以并行推进，不能用只读完成状态替代整个审核用例的完成证据。

## 固定核对输入与权威位置

| 输入 | 核对版本 | 依据 |
| --- | --- | --- |
| API | `a5d504c058c62cd91be451074d21608d69789918` | [查询 Proto](https://github.com/TokenTeam/iwut-api-proto/blob/a5d504c058c62cd91be451074d21608d69789918/app_center/v1/application_review_query/application_review_query.proto)、[决定 Proto](https://github.com/TokenTeam/iwut-api-proto/blob/a5d504c058c62cd91be451074d21608d69789918/app_center/v1/application_review/application_review.proto) |
| App | `c6332708ed9a89accb229f569ee44f98fd7487b2` | [查询 transport](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/internal/adapter/transport/application_review_query_service.go)、[决定 transport](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/internal/adapter/transport/application_review_service.go) |
| Gateway | `f4d5e5e935ccabfd718cfc493bf51a398776c8ae` | [路由目录](https://cnb.cool/TokenTeam/iwut-gateway/-/blob/f4d5e5e935ccabfd718cfc493bf51a398776c8ae/config/routes.v3.yaml)、[生成的 Traefik 配置](https://cnb.cool/TokenTeam/iwut-gateway/-/blob/f4d5e5e935ccabfd718cfc493bf51a398776c8ae/deploy/traefik/dynamic.generated.yaml) |

查询授权、队列资格、snapshot 与一致性由 [UC-APP-030](../../app-center/use-cases/UC-APP-030-query-application-version-reviews.md) 拥有；决定、正式策略、检查确认与并发写入由 [UC-APP-005](../../app-center/use-cases/UC-APP-005-decide-application-version-review.md) 拥有。普通已登录请求的流量边界继续遵循 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)。这些固定源码版本用于说明核对事实，不把历史提交当作测试运行时镜像选择；联合测试继续拉取已发布 `latest` 并记录实际 digest。

## 已有 wire 与 Console 消费约束

下表描述固定 Proto 的 HTTP binding，不定义第二份业务模型。`/app-center` 是 Gateway 前缀；App 服务内路径从 `/v1` 开始。

| 能力 | Browser 同源 HTTP | HTTP 正文 |
| --- | --- | --- |
| `ListPendingApplicationVersionReviews` | `POST /app-center/v1/reviews/application-versions:search` | 直接 Query：`applicationId?`、`pageSize`、`pageToken`；不包 `query` |
| `GetApplicationVersionReview` | `GET /app-center/v1/applications/{applicationId}/versions/{versionId}/reviews/{reviewId}` | 无正文、无查询参数 |
| `DecideApplicationVersionReview` | `POST /app-center/v1/applications/{applicationId}/versions/{versionId}/reviews/{reviewId}/decision` | 直接 Command：`outcome`、`expectedPolicyVersion`、`confirmedCheckIds`、`reason?`；不包 `command` |

App API transport 显式发送 `Accept: application/json`，有正文时发送 `Content-Type: application/json`；正文和响应按 ProtoJSON 语义处理 camelCase、字符串 enum 和 RFC3339 Timestamp。App 当前 [go.mod](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/go.mod) 使用 Kratos v2.9.2，其 [json codec](https://github.com/go-kratos/kratos/blob/v2.9.2/encoding/json/json.go) 对 `proto.Message` 已调用 ProtoJSON；不能据其它已缓存 Kratos 版本推断为 `application/protojson` 媒体类型。路径 ID 分别编码；不把 Session、USER identity 或客户端审核人字段放进业务正文。

队列使用后端默认全部待审及可选精确 applicationId filter，分页输入与 token 语义引用 UC-APP-030。前端不添加服务端未定义的状态过滤。决定的 enum wire 值为 `APPROVE` / `REJECT`；实际终态来自响应的 `review.status` 与 `review.decision.outcome`，不能从请求方向推断。

详情已提供 `currentPolicy.version/requiredCheckIds`、`decisionEligibility` 与 `asOf`，不是缺失 API。审核主体取 `review.snapshot`；当前 Application/Version 上下文、提交时验证版本和当前策略分别显示。`CURRENT_ADMIN`、`VERSION_CREATOR`、`REVIEW_SUBMITTER` 是已有冲突 enum，不授予或代替后端写权限。

决定正文没有 `expectedVersionRevision`、客户端 reviewerId 或决定时间；不发明 `If-Match` 或幂等 key。并发保护由既有后端一次性决定事务负责。客户端收到 already-decided、状态或 policy conflict 后重读相同三元路径；结果未知时仍按 BR-CRV-003 恢复，不自动重发。

稳定错误字段使用完整 `ERROR_REASON_*`，来源为 [查询错误 Proto](https://github.com/TokenTeam/iwut-api-proto/blob/a5d504c058c62cd91be451074d21608d69789918/app_center/v1/application_review_query/error_reason.proto) 与 [决定错误 Proto](https://github.com/TokenTeam/iwut-api-proto/blob/a5d504c058c62cd91be451074d21608d69789918/app_center/v1/application_review/error_reason.proto)。权限不足 `ERROR_REASON_APPLICATION_REVIEW_PERMISSION_REQUIRED` 与利益冲突 `ERROR_REASON_APPLICATION_REVIEW_CONFLICT_OF_INTEREST` 必须区分：前者回收该功能的私有审核内容，后者保留可读详情并刷新 eligibility。两者均不等同于 `SESSION_INVALID`。

## 接入项一：正式检查定义的可消费来源

状态：`OPEN`。影响：完整 APPROVE/REJECT 表单的正式政策解释与验收，不影响真实查询能力。

当前正式 ACTIVE 版本及其 required IDs 已由 UC-APP-005 定义，并由 [App OAuth migration](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/internal/adapter/mongo/version_oauth_migration.go) 写入：

```text
app-version-review-v2
  content-policy-reviewed
  launch-url-content-reviewed
  requested-access-reviewed
  oauth-redirects-reviewed
```

历史 `app-version-review-v1` 已退休，其前三项用于解释既有决定。这里记录现状，不把该版本硬编码为客户端认定的“当前策略”。当前版本必须每次从正式详情取得。

四项正式定义的完整可消费来源尚未齐备：公开详情只返回 IDs；[App domain 的 ReviewCheckDefinition](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/internal/review/domain/decision.go) 仅保存 ID；[Mongo policy document](https://github.com/TokenTeam/iwut-app-center/blob/c6332708ed9a89accb229f569ee44f98fd7487b2/internal/adapter/mongo/version_review_policy_repository.go) 只有 version、status 和 requiredChecks 字符串。UC-APP-005 已说明 `oauth-redirects-reviewed` 的双 client type 回调确认含义，但其它三项没有可直接消费的正式定义文本，尚不足以构成完整定义包。不能通过英文 ID 猜测文案，也不能移植 Profile policy 的同名检查定义。

接入选择采用 UC006 已列出的不可变版本定义包方案：由 App 权威来源核验各检查定义，提供严格绑定 policy version 与完整 check ID 集合的只读定义包；Console 只消费该包解释详情返回的版本。该方案无需新增 App 决定 API，客户端定义包不拥有当前策略选择权。后续若由 App 提供正式定义投影，可以在保持同一权威语义的前提下替换交付渠道。

解除证据：

1. 可追溯的 App 权威位置覆盖四项检查的正式含义，记录适用 policy version、完整 ID 集合与核验版本；不能仅以 Console 翻译或 fixture 作为定义来源。
2. Console 定义包由上述固定来源生成或逐项核对，测试证明未知版本、未知/缺少/重复 ID 和不完整详情关闭决定表单。
3. `currentPolicy` 仍来自真实详情；确认绑定 `(reviewId, policyVersion, requiredCheckIds)`，版本或集合改变即清空确认。
4. 真实 v2 详情可以解释全部检查，Reviewer 主动逐项确认后发送原版本与原 IDs；历史终态不会被当前策略重新解释成待决定状态。

下一步是补齐并核验正式定义来源及对应只读包，同时实施消费与失败关闭逻辑。本页不修改 App 业务权威正文，也不自行给现有 check ID 追加政策含义。

## 接入项二：Gateway ADMIN 决定 surface

状态：`OPEN`。影响：Browser 同源决定请求进入约定混合链路。

固定 Gateway 路由目录已为两个查询登记 `consoleSurfaces: [ADMIN]`，生成配置包含：

```text
admin-console-app-list-pending-application-version-reviews-http
admin-console-app-get-application-version-review-http
```

`app.decide-application-version-review` 已有普通 HTTP、gRPC、gRPC-Web 与 BFF internal 路由，但尚未登记 ADMIN surface，因而缺少：

```text
admin-console-app-decide-application-version-review-http
```

最小接入改动是在既有决定路由登记 ADMIN，重新生成路由配置与对应测试；保留已有 Session→USER 身份交换、Cookie 清理和 App 精确权限检查，不需要改 Proto。不得用 Console 通用代理或其它 surface 代替这条路由。

解除证据：

1. Gateway route catalog 与生成配置都出现该 ADMIN 决定路由，Developer surface 不因此获得此入口。
2. 中间件链为 `scrub-untrusted-console-headers → admin-console-session-forward-auth → remove-console-cookie → app-decide-application-version-review-forward-auth → app-decide-application-version-review-post-auth-scrub → strip-app-center-prefix`。
3. 已发布 Gateway `latest` 包含该配置，Console 镜像测试记录实际 digest；缺 Cookie、伪造 header、BFF 不可用和 Session 失效均按既有契约失败关闭。
4. 真实 Browser→Admin Session→Gateway→Auth→App 的 PENDING 决定成功；利益冲突、权限撤销和并发决定由真实 App 拒绝，既有其它 surface 和公共协议路由仍通过验证。

## 推进与关闭标准

可立即推进生成查询/决定客户端、Admin 私有缓存与 Session 隔离、真实待审队列及详情、分页过滤、终态展示、确认绑定、结果未知与冲突恢复。定义消费和路由验收与这部分并行实施，所有决定入口遵循 BR-CRV-002 的可解释性门禁。

两个接入项的解除证据齐全后，继续完成 UC006 的真实授权、逐项确认、并发、策略变化、依赖失败及响应丢失浏览器验收，再关闭本记录。`OPEN` 只表示上述依赖证据尚未收齐，不表示当前审核功能不可实施，也不把协议 fixture 或只读完成当作完整决定能力交付。
