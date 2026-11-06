# UC045 脚本查询准备核对

UC045 设计为 `ACCEPTED`。用户已确认分段验收。Auth 权限后端已复验，本轮实施资源、版本和待审查询。

## Auth 前置验证

UC-AUTH-038 和 UC-AUTH-010 的修订已接受。当前 Auth 工作树支持 `app.script.maintain`、`app.script.review`、`app.script.publish`、`app.script.suspend` 和 `app.script.restore` 的独立授撤，并向 `iwut-app-center` 签发有效权限列表。使用真实 MongoDB、生产 Wire 与 App Center `c2c2475` 的本地固定镜像重跑 `TestE2E_IdentityIssuance_ProductionWire`，确认同一 Session 新签发身份的授撤变化、单项撤销隔离及其他 audience 隔离。运行只对该 App 镜像名称用本地 SHA-256 校验替代拉取，其他 Docker 操作沿用原测试。

专项日志在 App 仓库 `.artifacts/script-query-uc045/auth-identity.log`。本轮用的是 Auth 本地源码及其 API 工作树。共享 API 仍需固定提交，新 `ScriptPermissionService` 的 Gateway 路由待接入。详见 [Auth 交付记录](../../auth-center/implements/UC-AUTH-038-readiness.md)。

## 串行顺序与真实读回

- `authority`：[UC045 BR-SCR-013/014](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013)、[UC044 拒绝与级联义务](../use-cases/UC-APP-044-decide-script-version-review.md#br-scr-012)、[UC049 完成判据](../use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-009)、[UC046 发布事实](../use-cases/UC-APP-046-manage-script-publication.md#br-scr-015)。
- `conflict`：现有顺序要求先完成 UC045，但 App 当前 Mongo schema 只写脚本资源、版本和 PENDING 审核。审核终态和级联任务由 UC044/049 写入，发布历史、head 和分发门禁由 UC046 写入。UC045 在这些写入前无法按正式链路证明其读回正确。无数据不能用来证明任务完成、批准存在或分发可用。
- `options`：先实现可由现有写入验收的查询，随各权威写入补齐读回，或把整个 UC045 移到 UC046 后。整体后移会推迟 UC044 人工决定前所需的审核详情。
- `accepted`：保留实现顺序，把 UC045 的交付拆为三段。先做资源与版本查询、PENDING 队列及详情，验证角色隔离、正文/政策、利益冲突、游标与缓存头。UC044/049 同一工作包补齐并验收唯一决定、终态历史与级联进度。UC046 补齐并验收批准事实、发布历史和分发门禁后，关闭 UC045 的完整验收。

本次已生成并核对 [UC045 brief](../briefs/UC-APP-045.md)。

## 第一段 API

`app_center.v1.script_query.ScriptQueryService` 暴露六个 Admin Console GET 与对应的原生 gRPC 方法。

| 方法 | App HTTP 路径 | 读取权限 |
| --- | --- | --- |
| `ListScriptResources` | `/v1/script-resources` | 五项脚本权限任一 |
| `GetScriptResource` | `/v1/script-resources/{resource_id}` | 五项脚本权限任一 |
| `ListScriptVersions` | `/v1/script-resources/{resource_id}/versions` | maintain、review、publish |
| `GetScriptVersion` | `/v1/script-resources/{resource_id}/versions/{version_id}` | maintain、review、publish |
| `ListPendingScriptReviews` | `/v1/script-reviews/pending` | review |
| `GetScriptReview` | `/v1/script-resources/{resource_id}/versions/{version_id}/reviews/{review_id}` | maintain、review |

版本列表可按 `state` 筛选，待审列表可按 `resourceId` 筛选。三类列表以 `limit`、`cursor` 分页，游标签名绑定用户、有效脚本权限、列表和过滤条件。资源、版本使用 `createdAt` 加 ID，审核使用记录创建时的 `submittedAt` 加 ID，均倒序。审核角色通过版本查询仅可读取进入审核的版本。发布角色读取版本摘要，正文只随维护或相应审核权限的详情返回。审核详情返回提交快照、正式检查定义、版本 revision 和调用者的决定资格及冲突类别。

App 对权限不足返回 403、合法未知 ID 返回 404、非法请求或游标返回 400、关联事实损坏返回 500、存储不可用返回 503。HTTP 成功与失败都使用 `Cache-Control: private, no-store`。Gateway 按精确方法与路径绑定 Admin Console surface，并使用既有 Session 换 App USER 身份的流程。
