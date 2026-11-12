# UC-APP-045：查询脚本管理与审核视图

状态：`ACCEPTED`

## 目标与查询

作者读取本人的脚本、版本和审核结果。平台 Reviewer、发布人员和分发运维人员使用各自的管理视图。客户端独立分发与应用关联读取见 [UC047](UC-APP-047-resolve-application-script-content.md)，应用选取与 App Reviewer 的关联视图见 [UC048](UC-APP-048-manage-application-script-dependencies.md)。

| `ScriptAuthoringService` 本人查询 | App 内部 HTTP |
| --- | --- |
| `ListOwnScriptResources` | `GET /v1/users/me/script-resources` |
| `GetOwnScriptResource` | `GET /v1/users/me/script-resources/{resource_id}` |
| `ListOwnScriptVersions` | `GET /v1/users/me/script-resources/{resource_id}/versions` |
| `GetOwnScriptVersion` | `GET /v1/users/me/script-resources/{resource_id}/versions/{version_id}` |
| `GetOwnScriptReviewResult` | `GET /v1/users/me/script-resources/{resource_id}/versions/{version_id}/reviews/{review_id}` |

## 业务规则

<a id="br-scr-013"></a>
### BR-SCR-013：按职责限定查询披露

本人视图要求有效可信 USER 且 `ownerAuthId` 为调用者。Developer 资格失效后，仍可登录的作者可以读取本人历史、草稿和审核结果。本人入口从可信身份确定范围，平台权限不会扩大该范围。未送审的 DRAFT 仅向本人披露，治理视图不列出 DRAFT 或仅有 DRAFT 的资源。

本人资源列表及详情返回 resourceId、名称、用途、revision、时间和最近创建版本的最小摘要。无版本时摘要为空，最近版本按 createdAt 和 versionId 判定。本人版本列表返回 resourceId、versionId、标签、状态、format、digest、revision、时间和已有 reviewId，详情另返回原文。作者审核结果返回 resourceId、versionId、reviewId、审核状态、提交时间、提交时的名称/用途、资源 revision、源版本 revision、format、digest 和 policyVersion。终态另返回决定 ID、结果、决定时间和已保存理由。该投影省略审核人员身份、平台内部审计和跨应用级联信息。

`app.script.review` 可读取脚本队列、受审原文和检查定义、相关资源与已送审版本、决定与级联详情。利益冲突仍可读，详情显示 `canDecide=false` 及冲突类别，决定入口独立校验。`app.script.publish` 可读已送审资源与版本摘要、批准事实和发布历史。`app.script.suspend` 和 `app.script.restore` 可读分发门禁和发布摘要。发布和运维按职责只披露相应摘要与状态。治理查询无权读取作者的私有草稿，也不授予本人写操作。

<a id="br-scr-014"></a>
### BR-SCR-014：一致详情与有界列表

详情在同一次一致读取中校验资源归属、resourceId/versionId/reviewId 关联、状态、原文/digest、绑定政策和唯一决定，并按职责投影。PENDING 队列仅包含待审。Reviewer 的级联详情返回 taskId、状态、进度观测时间、已处理数量、实际拒绝/既有终态/关闭豁免的分别计数及受控失败分类。完成以 [UC049](UC-APP-049-cascade-script-rejection.md) 的判据为准。

limit 默认 20、最大 100，按 createdAt 和唯一 ID 稳定倒序。本人的版本列表可按状态过滤。先按所有者或平台职责过滤，再做有界分页。opaque cursor 绑定调用者、查询范围、父资源、过滤与排序。非法或不匹配 cursor 报错。正文只在详情返回，决定前重读详情。

所有视图为 `private, no-store`。先鉴权再定位目标。本人查询的未知、非本人或路径关联不匹配统一 NotFound。必要事实损坏时明确失败。

## 验收

- 作者可在资格失效后读取本人草稿和原拒绝原因。其他账号猜测 ID、替换父 ID 或重放游标均不能取得本人视图。
- 审核、发布和分发运维入口隐藏未送审草稿，角色组合也不得扩大到他人的草稿。
- Reviewer 获得完整政策文本和精确受审字节，可看到自身冲突但不能绕过决定门禁。
- 终态记录退出 PENDING 队列、历史仍可查询；同时间分页与过滤变更 cursor 有明确行为。
