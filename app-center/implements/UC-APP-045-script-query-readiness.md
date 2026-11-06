# UC045 脚本查询准备核对

UC045 设计为 `ACCEPTED`。用户已确认分段验收。资源、版本和待审查询已通过 App 直连、本地三镜像联验及分组回归。

## Auth 前置验证

UC-AUTH-038 和 UC-AUTH-010 的修订已接受。当前 Auth 工作树支持 `app.script.maintain`、`app.script.review`、`app.script.publish`、`app.script.suspend` 和 `app.script.restore` 的独立授撤，并向 `iwut-app-center` 签发有效权限列表。使用真实 MongoDB、生产 Wire 与 App Center `c2c2475` 的本地固定镜像重跑 `TestE2E_IdentityIssuance_ProductionWire`，确认同一 Session 新签发身份的授撤变化、单项撤销隔离及其他 audience 隔离。运行只对该 App 镜像名称用本地 SHA-256 校验替代拉取，其他 Docker 操作沿用原测试。

独立 Auth 专项日志在 App 仓库 `.artifacts/script-query-uc045/auth-identity.log`。三镜像联验使用已对齐的 API 和 Auth 本地工作树。详见 [Auth 交付记录](../../auth-center/implements/UC-AUTH-038-readiness.md)。

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

## 第一段实现与验证

App 镜像提交 `123e4cf18fa95f19a0530db756bd75344f36dc5f` 固定统一 API `71b6531f42be43cdcbcaccdbce839e2730652572`，包含脚本查询和五项权限管理的 Proto。Mongo migration `0037_script_query_indexes` 添加资源、版本和待审列表索引。版本详情与审核详情在快照事务中校验绑定关系。资源名称与用途在送审后仍按原快照展示。

真实 MongoDB race 专项验证同毫秒分页、游标签名、权限与过滤绑定、审核快照和摘要损坏时失败。App 直连专项验证五项权限的读取范围、审核冲突、非法参数、缓存头以及 1 MiB 正文的原生 gRPC 精确读取。Gateway `54763f5c97683fb951bb4c8e9f643ea20362dfcd` 的 `make check` 与 `make protocol-e2e` 通过。

三镜像专项 `TestE2E_UCAPP041_042_043_045_ScriptManagementLocalImages` 通过。测试使用真实注册与登录，同一 Session 经 Gateway 逐项授撤，验证 HTTP、原生 gRPC、gRPC-Web、Admin/Developer surface 和正文隔离。镜像 ID 在 App 仓库 `.artifacts/integration/run-PB4YSXt3/script-management-image-ids.txt`，日志在 `.artifacts/script-query-uc045/image-e2e.log`。Auth 镜像由 `e92b96c` 及本地 UC038 工作树构建，输入指纹和 API SHA 记录在 `.artifacts/script-query-uc045/auth-image-inputs.txt`。

首次 `make check-full` 前 23 项通过，最后一项的六个测试仍使用旧迁移数或旧索引集合。App 提交 `85f37cdb5bdd3a07276e9497e2334f6bcbc12976` 修复这些测试断言。最终提交的 `make check`、`make test-race` 均通过，MongoDB 和 HTTP/gRPC 阶段的 216 个顶层用例在六个独立实例重跑，210 通过，6 个按独立跨服务环境的前置条件跳过，其中脚本三镜像用例已单独通过。App 和 API 输入保持固定。首次报告位于 `.artifacts/verification/20261106T085340Z-bs9mpgke/report.json`，最终分组报告位于 `.artifacts/script-query-uc045/sharded-mongo-e2e/report.json`。

Gateway 会话沿用了上一轮已完成的推送指令，将统一 API `71b6531` 和 Gateway `54763f5` 推到了各自的远端 `master`。已核对远端引用。本轮 App 和 Auth 联验仍使用本地镜像。
