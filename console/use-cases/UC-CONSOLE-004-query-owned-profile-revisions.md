# UC-CONSOLE-004：只读管理 Application 资料修订

状态：`PROPOSED`

## 用户目标与范围

当前管理员查看资料修订列表、一个修订的完整原文和有界审核历史，辨别当前工作修订、当前公开修订及审核结果。权威引用 [UC-APP-039](../../app-center/use-cases/UC-APP-039-query-owned-application-profile-revisions.md) BR-PRF-047–056 与 [资料查询契约](../../app-center/query-contracts/profile-management.md)，前端复用 BR-CMG-001–004。

不提供新建、编辑、复制、恢复、再次提交、重新公开或回滚；被拒绝原文可读不意味着原修订可编辑。Reviewer 完整 snapshot 由独立审核流程授权，本页面不补查。

## 页面与流程

1. 从管理概览进入资料列表，调用 `ListApplicationProfileRevisions`，`GET /app-center/v1/applications/{application_id}/profile-revisions`。默认全状态，提供单个 reviewStatus 筛选及后端支持的分页参数；不发送未知 query 或正文。
2. 列表按后端顺序展示 sequence、displayName、审核状态、revision、当前工作/公开标记与最小 latestReview。页级 profileState 单独展示；当前指针不在筛选结果中时不能显示“没有公开资料”。
3. 进入详情调用 `GetApplicationProfileRevision`，同路径加 `/{profile_revision_id}`。按后端原文展示名称、description、icon 字符串及允许披露的必要审计信息；不得 trim、规范化或按当前新建限制裁剪 REJECTED 原文。
4. 完整当前内容与审核摘要分区；reviews 逐页读取，保留 attempt 升序，latestReview 独立展示。nextReviewPageToken 不与列表 token 混用。刷新详情或切换修订时从该修订审核历史首批读取。
5. 长内容纯文本呈现，不执行 HTML/Markdown，不主动探测或自动打开 URL；图标字符串以安全文本为基线，不新增受控资产或外链代理。无资料、无审核记录、指针不在列表、超预算错误、统一不可访问各有语义状态。

## 前端业务规则

<a id="br-cmg-007"></a>
### BR-CMG-007：原文、指针与审核摘要忠实表达

原文来自当前 ProfileRevision；审核历史来自对应摘要，不把当前内容称为提交时 snapshot。当前工作和公开指针按页级/详情事实显示，不能由当前筛选页推断。隐藏字段不补查，REJECTED 不生成恢复或重新提交旧修订入口。

<a id="br-cmg-008"></a>
### BR-CMG-008：资料与审核历史独立分页

列表与详情历史拥有各自上下文和不透明 token；切换修订、身份或筛选时仅保留仍合法的页面状态。详情历史翻页不覆盖 latestReview。超预算按正式错误显示，不截断原文伪装成功、不跳过条目、不拆成未经授权的临时接口。no-store、恢复和可访问性遵循 BR-CMG-002–004。

## 依赖与验收

两个 UC039 RPC、固定 API 和 Gateway DEVELOPER surface 已具备后端契约；实际路由/客户端和真实 E2E 仍需对应工作包交付，无新 API 需求。

1. 四状态、空资料状态、当前工作/公开同或不同、筛选排除当前项、REJECTED 合法原文均忠实呈现。
2. 多页审核历史、latestReview 与历史重复、历史为空及独立 token 错用均验证；详情内容不是 Reviewer snapshot。
3. 非管理员、旧管理员、跨 Application 修订统一隐藏，资格下降与保留生命周期历史仍可读。
4. 预算错误、5xx/网络失败、SESSION_INVALID、迟到响应与键盘长文阅读覆盖；真正后台链路、no-store 和私有资料不持久化通过验收。
