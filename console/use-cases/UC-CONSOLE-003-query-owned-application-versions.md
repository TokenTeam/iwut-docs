# UC-CONSOLE-003：只读管理 Application Version

状态：`PROPOSED`

## 用户目标与范围

当前管理员从 Application 管理概览进入 Version 列表，查看一个版本的当前声明和最新审核摘要，理解其状态以及是否已有相关发布。后端权威为 [UC-APP-034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md) BR-VER-019–025。前端共用 [UC-CONSOLE-002](UC-CONSOLE-002-query-owned-applications.md#前端业务规则) BR-CMG-001–004。

只读范围不包含创建/编辑、提交审核、恢复被拒绝版本、放弃草稿、发布槽位操作、完整审核历史或 Reviewer snapshot 查询。

## 页面与流程

1. 进入 `/applications/{applicationId}/versions` 的逻辑功能路由，调用 `ListApplicationVersions`：`POST /app-center/v1/applications/{application_id}/versions:search`。浏览器路由命名可由实现调整，API 路径不可改写业务含义。
2. 默认不额外限制审核状态；提供一个 DRAFT/SUBMITTED/APPROVED/REJECTED 筛选，不能扩展多状态、全文搜索或排序。按后端 sequence 降序显示版本名称、兼容范围、revision、状态及最小最新审核摘要。
3. 进入详情使用 `GetApplicationVersion`：`GET /app-center/v1/applications/{application_id}/versions/{version_id}`。展示返回的当前 Version 声明，包括 URL、RPC 范围、capabilities、required/optional scopes 和版本化 OAuth 回调；纯文本展示，不执行 URL 内容或回调。
4. 当前内容与 latestReview 明确分开：最新审核摘要不能作为完整提交 snapshot，也不能被当前可变字段替代。恢复后的 DRAFT 可以同时有最近 REJECTED 摘要，界面须能表达这两个事实。
5. 返回保持当前会话内筛选，重新确认权限；刷新不触发写命令。无记录、过滤无结果、无 latestReview、统一不可访问和依赖故障独立表达。

## 前端业务规则

<a id="br-cmg-005"></a>
### BR-CMG-005：当前 Version 与审核事实区分

当前内容、状态和最新审核摘要使用后端各自投影标签，不自行推导“审核通过即已上线”、自动生成发布状态或完整审核历史。APPROVED 仅按后端语义表述；发布摘要不存在不等于正在关闭应用。SUBMITTED 或终态页面不出现编辑/恢复等未接受操作。

<a id="br-cmg-006"></a>
### BR-CMG-006：版本筛选、敏感运行声明与可访问性

筛选变化重置分页；ID、revision、scope 和回调均为读取值，不构造写权限或 secret。int64 遵循生成客户端的 ProtoJSON 表达，不经 JavaScript 不安全整数转换。列表与详情的空态、刷新、分页、长文本和返回均适用 BR-CMG-002–004。运行声明不进入 URL 参数、遥测或持久缓存。

## 依赖与验收

依赖固定 Proto 生成客户端和两个 UC034 RPC 的 Gateway DEVELOPER surface；当前管理员读取不要求 Developer APPROVED，暂停、归档与关闭保留历史可读，按 UC034 验证。无新 App API 需求。

1. 四种状态、无审核摘要、恢复后 DRAFT/REJECTED 摘要均正确呈现；不冒充完整审核记录。
2. 非管理员和跨 Application versionId 统一隐藏，旧管理员缓存不能继续展示；管理员资格下降可读而无写按钮。
3. 单状态筛选、keyset、空页、无效 token、长 URL/scopes 和大 int64 有契约测试，深链接失败不闪现上一版本内容。
4. 真实 Session→Gateway→Auth/App 联合读取、no-store 和错误恢复通过；mock 不计真实 E2E。
