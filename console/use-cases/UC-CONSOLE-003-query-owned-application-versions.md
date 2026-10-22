# UC-CONSOLE-003：只读管理 Application Version

状态：`ACCEPTED`

接受日期：2026-10-15

## 用户目标与范围

当前管理员从 Application 管理概览进入 Version 列表，查看一个版本的当前声明和最新审核摘要，并理解其审核状态。后端权威为 [UC-APP-034](../../app-center/use-cases/UC-APP-034-query-owned-application-versions.md) BR-VER-019–025。前端共用已接受的 [UC-CONSOLE-002](UC-CONSOLE-002-query-owned-applications.md#前端业务规则) BR-CMG-001–004。

本 UC 不读取、推导或拼接 Version 的发布位置。Publication 摘要属于 UC002 的独立 Application 管理投影，具有自己的 `asOf`；UC034 又明确要求不能把当前 Version 与 Publication 跨能力拼成一个快照。因此页面只提供返回 Application 概览的导航，不宣称某个 Version 已发布。

只读范围不包含创建/编辑、提交审核、恢复被拒绝版本、放弃草稿、发布槽位操作、完整审核历史或 Reviewer snapshot 查询。

## 页面与流程

1. 进入 `/applications/{applicationId}/versions` 的逻辑功能路由，调用 `ListApplicationVersions`：`POST /app-center/v1/applications/{application_id}/versions:search`。正文是 `ListApplicationVersionsQuery` 的直接 ProtoJSON（`reviewStatus`、`pageSize`、`pageToken`），不是 `{query:{...}}`。浏览器路由命名可由实现调整，API 路径不可改写业务含义。
2. 默认不额外限制审核状态；提供一个 DRAFT/SUBMITTED/APPROVED/REJECTED 筛选，不能扩展多状态、全文搜索或排序。按后端 sequence 降序显示版本名称、兼容范围、revision、状态及最小最新审核摘要。
3. 进入详情使用 `GetApplicationVersion`：`GET /app-center/v1/applications/{application_id}/versions/{version_id}`。展示返回的当前 Version 声明，包括 URL、RPC 范围、capabilities、required/optional scopes 和版本化 OAuth 回调；纯文本展示，不执行 URL 内容或回调。
4. 当前内容与 latestReview 明确分开：最新审核摘要不能作为完整提交 snapshot，也不能被当前可变字段替代。恢复后的 DRAFT 可以同时有最近 REJECTED 摘要，界面须能表达这两个事实。
5. 返回保持当前会话内筛选，重新确认权限；刷新不触发写命令。无记录、过滤无结果、无 latestReview、统一不可访问和依赖故障独立表达。

## 前端业务规则

<a id="br-cmg-005"></a>
### BR-CMG-005：当前 Version 与审核事实区分

当前内容、状态和最新审核摘要使用后端各自投影标签，不自行推导“审核通过即已上线”、自动生成发布状态或完整审核历史。APPROVED 仅按后端语义表述；页面不从 UC002 Publication 摘要反推当前 Version 的发布事实。DRAFT、SUBMITTED 和终态页面一律不出现创建、编辑、提交、恢复、放弃或发布操作。

<a id="br-cmg-006"></a>
### BR-CMG-006：版本筛选、敏感运行声明与可访问性

筛选变化重置分页；ID、revision、scope 和回调均为读取值，不构造写权限或 secret。int64 遵循生成客户端的 ProtoJSON 表达，不经 JavaScript 不安全整数转换。列表与详情的空态、刷新、分页、长文本和返回均适用 BR-CMG-002–004。运行声明不进入 URL 参数、遥测或持久缓存。

## 依赖与验收

依赖固定 Proto 生成客户端和两个 UC034 RPC 的 Gateway DEVELOPER surface；当前管理员读取不要求 Developer APPROVED，暂停、归档与关闭保留历史可读，按 UC034 验证。无新 App API 需求。

1. 四种状态、无审核摘要、恢复后 DRAFT/REJECTED 摘要均正确呈现；不冒充完整审核记录。
2. 非管理员和跨 Application versionId 统一隐藏，旧管理员缓存不能继续展示；管理员资格下降可读而无写按钮。
3. 单状态筛选、keyset、空页、无效 token、长 URL/scopes 和大 int64 有契约测试，深链接失败不闪现上一版本内容。
4. 真实 Session→Gateway→Auth/App 联合读取、no-store 和错误恢复通过；mock 不计真实 E2E。

## 首个实现决定

本 UC 自 2026-10-15 起接受，并按以下边界启动首个实现工作包：

- 继续使用固定统一 API 输入 `a5d504c058c62cd91be451074d21608d69789918`，只新增 `app_center/v1/application_version` 生成类型和严格同源 client；不手写第二套 Version DTO。
- Developer Console 使用 `/applications/{applicationId}/versions` 作为列表入口，使用 `/applications/{applicationId}/versions/{versionId}` 作为只读详情入口；单状态筛选使用 URL search `review`，详情与返回列表保留该值。
- 首包只实现四种 review status 的单选筛选、不透明 token 逐页加载、显式刷新、当前 Version 内容与 latestReview 分区展示、统一不可访问和 Session 失效回收。
- “全部状态”省略 `reviewStatus`；pageSize 固定为 20。token 只留在内存并绑定当前 authId、applicationId 与筛选；筛选、身份或目标变化时丢弃全部旧页。累计页面各自保留独立 `asOf`，界面不得宣称多页来自同一快照。
- `launchUrl`、capability、scope 与 OAuth redirect 只按服务端字符串显示，不生成可执行链接、不预取目标、不写入 URL search、日志或持久存储；所有 int64 继续保持生成类型的 `bigint`。
- UC002 详情中的 Version 入口随本包启用；资料修订与 Tester 入口继续保持未交付表达。创建、编辑、提交、恢复、放弃草稿、发布和完整审核历史均不在本包范围。
- 组件和浏览器 fixture 只证明页面分支；Gateway `latest` route test 与真实 Auth/App 协议链分别记录，最终仍需真实浏览器联合验收。

## 实现登记

2026-10-15 首个实现工作包已交付：固定类型与同源 client、列表/详情路由、单状态 URL 筛选、显式游标翻页、当前 Version/latestReview 分区、无效 token 回收、`SESSION_INVALID` 回登录和运行声明惰性纯文本均已落地。浏览器 fixture 用例、Gateway `latest` 路由组成测试及真实 Auth/App/Mongo 协议 E2E 已通过。

本登记不宣称真实浏览器联合验收已完成：仍需让页面连接同一套真实服务环境，使用真实管理员及四种状态/恢复后 DRAFT 数据覆盖管理权变化、生命周期组合、no-store 与迟到响应。证据和固定镜像 digest 记录在 [Console 实现状态](../implements/README.md)。
