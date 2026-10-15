# UC-CONSOLE-004：只读管理 Application 资料修订

状态：`ACCEPTED`

接受日期：2026-10-15

## 用户目标与范围

当前管理员查看资料修订列表、一个修订的完整原文和有界审核历史，辨别当前工作修订、当前公开修订及审核结果。权威引用 [UC-APP-039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md) BR-PRF-047–056 与 [资料查询契约](../../app-center/query-contracts/profile-management.md)，前端复用 BR-CMG-001–004。

不提供新建、编辑、复制、恢复、再次提交、重新公开或回滚；被拒绝原文可读不意味着原修订可编辑。Reviewer 完整 snapshot 由独立审核流程授权，本页面不补查。

## 页面与流程

1. 从管理概览进入资料列表，调用 `ListApplicationProfileRevisions`，`GET /app-center/v1/applications/{application_id}/profile-revisions`。Query 仅允许 camelCase 单值 `reviewStatus?`、`pageSize?`、`pageToken?`，默认全状态；GET 不发送正文，path ID 不重复进入 query。
2. 列表按后端顺序展示 sequence、displayName、审核状态、revision、当前工作/公开标记与最小 latestReview。页级 profileState 单独展示；当前指针不在筛选结果中时不能显示“没有公开资料”。
3. 进入详情调用 `GetApplicationProfileRevision`，同路径加 `/{profile_revision_id}`。按后端原文展示名称、description、icon 字符串；审计字段白名单仅为 createdBy、createdAt、updatedAt。不得显示 updatedBy、submittedBy、decidedBy、Reviewer 身份、confirmed checks、current policy 或 snapshot 正文，也不得 trim、规范化或按当前新建限制裁剪 REJECTED 原文。
4. 详情与审核历史均复用 `GET /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}`；Query 仅允许 `reviewPageSize?`、`reviewPageToken?`，没有独立 reviews endpoint。完整当前内容与审核摘要分区；reviews 逐页读取，保留 attempt 升序，latestReview 独立展示。nextReviewPageToken 不与列表 token 混用。刷新详情或切换修订时从该修订审核历史首批读取。
5. 长内容纯文本呈现，不执行 HTML/Markdown，不主动探测或自动打开 URL；图标字符串以安全文本为基线，不新增受控资产或外链代理。description、icon 和审核 reason 必须保留 `null` 与空字符串的差异，并保持空白原文，不得 trim/normalize。无资料、无审核记录、指针不在列表、超预算错误、统一不可访问各有语义状态。

## 前端业务规则

<a id="br-cmg-007"></a>
### BR-CMG-007：原文、指针与审核摘要忠实表达

原文来自当前 ProfileRevision；审核历史来自对应摘要，不把当前内容称为提交时 snapshot。当前工作和公开指针按页级/详情事实显示，不能由当前筛选页推断。隐藏字段不补查，REJECTED 不生成恢复或重新提交旧修订入口。

<a id="br-cmg-008"></a>
### BR-CMG-008：资料与审核历史独立分页

列表与详情历史拥有各自上下文和不透明 token；`pageSize` / `reviewPageSize` 范围为 1..100，省略时后端默认 20，显式 0 非法，token 上限 4096 字节，空串或省略表示首批。只能根据 next token 为 `null` 判断结束；响应可能因 2 MiB 预算提前分页。切换修订、身份或筛选时清空对应 token 栈。详情历史翻页返回新的完整详情，content、profileState、latestReview 与 reviews 必须来自同一响应；不得把旧详情和新 reviews 拼成同一 snapshot。列表页和详情历史各页 `asOf` 独立，不宣称跨页冻结。超预算按正式错误显示，不截断原文伪装成功、不跳过条目、不拆成未经授权的临时接口。no-store、恢复和可访问性遵循 BR-CMG-002–004。

## 依赖与验收

两个 UC039 RPC、固定 API 和 Gateway DEVELOPER surface 已具备后端契约；实际路由/客户端和真实 E2E 仍需对应工作包交付，无新 API 需求。

1. 四状态、空资料状态、当前工作/公开同或不同、筛选排除当前项、REJECTED 合法原文均忠实呈现。
2. 多页审核历史、latestReview 与历史重复、历史为空及独立 token 错用均验证；详情内容不是 Reviewer snapshot。
3. 非管理员、旧管理员、跨 Application 修订统一隐藏，资格下降与保留生命周期历史仍可读。
4. 预算错误、5xx/网络失败、SESSION_INVALID、迟到响应与键盘长文阅读覆盖；真正后台链路、no-store 和私有资料不持久化通过验收。

## 首个实现决定

本 UC 自 2026-10-15 起接受，并按以下边界交付首个实现工作包：

- 继续使用固定统一 API 输入 `a5d504c058c62cd91be451074d21608d69789918`，生成 `app_center/v1/application_profile_revision` 类型并实现严格同源 GET client；仅发送契约允许的 query 参数。
- Developer Console 使用 `/applications/{applicationId}/profile-revisions` 与 `/applications/{applicationId}/profile-revisions/{profileRevisionId}`；单状态筛选使用 URL search `review`，两类 page token 均只留内存。
- 修订列表与详情审核历史使用独立显式页状态和内存 token 栈；query key 分别绑定 authId、applicationId、筛选、profileRevisionId 和当前 token。换身份、目标或筛选丢弃对应旧页；各页 `asOf` 独立，不宣称跨页冻结。
- 详情正文、icon 与 reason 用 `white-space: pre-wrap` 的惰性纯文本表达，显式区分 `null`、空字符串和值；不渲染 HTML/Markdown、图片、链接、预览或外部探测。
- UC002 详情中的资料修订入口随本包启用；创建、编辑、复制、恢复、提交、公开、回滚、Reviewer snapshot/queue/decision 和 Admin Console 均不在本包范围。
- 组件/浏览器 fixture、Gateway `latest` route test 与真实 Auth/App 协议链分开登记；最终仍需真实浏览器联合验收。

## 2026-10-16 实现结果

- `@iwut/api-client` 已生成 Application ProfileRevision 类型；两个请求都是无正文 GET，只映射白名单 query，path ID 独立编码，ProtoJSON 未知字段拒绝，`int64` 保持 `bigint`。解码前额外验证必需 `profileState/asOf/content` 以及所有公开 `google.protobuf.Value` 的 `null | string` 形态，畸形成功响应失败关闭。
- Developer Console 已交付资料修订列表/详情路由、单状态 URL 筛选、显式前后翻页、页级工作/公开指针、独立 latestReview 与审核历史分页。审核翻页以新响应整体替换当前详情，不合并不同时点的正文或历史。
- description、icon、reason 均以 `white-space: pre-wrap` 的 React 文本节点呈现，显式区分 `null`、空字符串和值；icon 即使形似 URL 也不会创建链接、图片、预取或外部探测。只展示 createdBy、createdAt、updatedAt 和允许的 decision 字段，不补查 Auth 用户资料。
- 400 坏 token 提供从头刷新，404 统一隐藏，413 使用专门且不可截断的错误状态；网络和 5xx 不清 Session，`SESSION_INVALID` 清除 Developer 私有 Query/Session 并返回登录入口。
- Vitest 覆盖精确 GET/query、无正文、严格解码、大整数、筛选重置、指针目标在筛选外、null/空串/空白原文、惰性 URL、latestReview 与历史分离以及完整详情翻页。Playwright 在真实浏览器 origin 上覆盖同源 list/detail 与审核翻页，但业务响应仍为类型化 fixture。
- Console `edge:e2e` 已确认 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` 包含两个 ProfileRevision DEVELOPER surface route，并验证 BFF 不可用时均失败关闭。同 digest 的 Gateway 协议 E2E 已通过真实 Auth/App/Mongo 和 BFF Cookie 身份交换。

剩余验收是让浏览器页面直接连接同一套真实 Gateway/Auth/App 环境，覆盖真实管理员、四种修订状态、三种 Review 状态、管理权变化、生命周期组合、跨上下文 token、413 和迟到响应；完成前不得把 fixture 浏览器测试表述为完整业务 E2E。
