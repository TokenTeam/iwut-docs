# 提交时固定审核策略：设计修订提案

状态：`ACCEPTED`。形成于 2026-11-03，2026-11-04 按用户“当前未上线，不做兼容设计”的要求简化。设计阶段只修改文档。2026-11-04 用户已接受并授权开始更新；当前进入 App 实施，其他模块依既有所有权边界交接，无部署或 push 授权。沿用原六个 UC，不新增用户目标。

## 规则与范围

周一按 A 成功提交，周二启用 B，周三仍按 A 审核；周四的新提交或拒绝后重新提交绑定 B。Version 与 Profile 政策各自独立。新政策不自动补审、不撤销批准、不增加整改期限或合规状态。

当前未上线，直接建立单一新模型和接口。删除上一稿的旧 PENDING 回填、旧终态只读、绑定来源分类、ID-only 定义分支、Profile v1 补充集合、新旧协议双读、弃用字段过渡和维护窗口。测试库、样例与夹具按新模型重新创建，本轮未执行重建。

新模型运行以后产生的 A 记录，在 B 生效后仍保留 A 的完整定义和决定事实。这是提交绑定的业务要求，不是兼容上线前旧模型。

本页只是审核导航，权威修订在下列 UC/BR。六份 UC 已为 ACCEPTED，原已接受/已交付工作的历史证据保留，不把本次修订说成已经实现。

| 用例 | 本次相关规则 | 修订位置 |
| --- | --- | --- |
| UC004 提交 Version | BR-REV-004/009 | [政策与内容一起绑定、提交/发布并发](../use-cases/UC-APP-004-submit-application-version-review.md#策略绑定与提交并发) |
| UC015 提交 Profile | BR-PRF-018/021 | [独立 Profile 绑定](../use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-018) |
| UC005 决定 Version | BR-REV-016/017/018/019 | [按绑定决定](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016)、[发布](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[初始化/实时门禁/验收](../use-cases/UC-APP-005-decide-application-version-review.md#新模型初始化与运行门禁) |
| UC016 决定 Profile | BR-PRF-028/029/031/032 | [完整政策定义及按绑定决定](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028) |
| UC030 查询 Version | BR-REV-031/034 | [reviewPolicy](../use-cases/UC-APP-030-query-application-version-reviews.md#审核详情)、[单一接口交付](../use-cases/UC-APP-030-query-application-version-reviews.md#策略接口与交付) |
| UC031 查询 Profile | BR-PRF-043/046 | [绑定定义与当前公开资料](../use-cases/UC-APP-031-query-application-profile-reviews.md#审核详情) |

## 与原设计的替代关系

| 原要求或上一稿安排 | 当前设计 |
| --- | --- |
| 决定采用最新 ACTIVE | 采用目标 attempt 提交时绑定的版本，退休不妨碍决定 |
| 页面读 A→发布 B→409→清确认换政策 | 已绑定 A 继续按 A；Scope、权限、公开指针等独立冲突仍按原契约恢复 |
| 决定与退休的政策写栅栏 | 将现有 coordinationRevision 真实写栅栏移到提交路径，保护提交与发布的归属，不新增 head |
| 旧记录回填、旧终态解释和定义补充 | 删除；从首次初始化起每份 Review 都有绑定，每份政策都有完整定义 |
| 新旧字段并行、兼容只读和切换窗口 | 删除；两类详情字段4直接定义为 reviewPolicy，配套生成单一新契约 |
| 原完整发布治理准备链 | 仅保留政策发布所需的原子切换、最小成功标识和未知结果恢复，不建设新的治理产品 |

旧[策略发布提案](2026-10-26-review-policy-change-proposal.md)与[Console交接记录](2026-10-26-console-review-acceptance-handoff.md)原文只保留历史，并有替代说明。Profile 单工作位、同 Review 一次性决定、公开指针 CAS、Scope 的 Auth 所有权与实时窗口不变。

## 现有实现差异（只读核对）

App `5b42ed7` / API `6fea3db` 当前没有提交政策绑定；决定仍检查 ACTIVE 并写政策 coordinationRevision；查询返回 currentPolicy。Version v3 已有完整正式定义，Profile v1 存储仍只有 ID。本次实施将直接使用新存储约束、完整定义和 reviewPolicy，不编写旧实验数据的升级路径。

只读定位包括 ApplicationReview、两类提交/决定 Repository 与 query Repository，以及 API 两份 review query proto。没有读取生产数据库或执行任何数据重建。UC007/020/021 发布和 UC012/019/023/024 运行查询仍按批准事实与独立门禁工作，不单因人工政策退休而失去资格。

## 已接受的技术方案

1. 提交与发布复用现有政策文档 coordinationRevision 条件写，保证每次成功提交归属明确；决定只读绑定，不再争抢全局选择器。
2. 两类政策从初始化起直接保存完整定义，Review 只新增 policyBinding.version，沿用 submittedAt 审计；详情统一返回 reviewPolicy，全体消费者按同一新契约生成、严格验证并联合验收。

未上线、不做旧模型兼容的方向已由用户确认，不再列为待选择事项。本节技术方案亦已接受，开始实施；具体进度与验证另见实施导航。

## API、Gateway 与 Console 交接

| 所有者 | 审核后必要工作 |
| --- | --- |
| App/API | 所有 Review 必有 policyBinding；两类完整政策及 validator 首次初始化；详情字段4改为 review_policy，直接删除 currentPolicy；错误绑定使用明确 PolicyMismatch 语义 |
| 生成客户端/BFF | 只接受新形状；缺绑定、缺定义或非法响应报错，没有旧协议只读兜底 |
| Gateway | 无新增路由/权限，核对新 descriptor、三协议和错误透传 |
| Console | 以 reviewPolicy 决定，逐项展示完整定义；A 下提交/B 后仍按 A 决定；保留权限、Scope、指针及未知结果恢复 |

Console/Gateway/Auth 的代码和 UC 未由本轮修改；Console UC006/007 对应验收由其所有者在本方案接受后更新。没有发送新的跨聊天消息。

## 验收边界

2026-11-04 实施已完成 App/API 后端及完整门禁，见[实施与验收记录](2026-11-04-submission-bound-review-policy-implementation.md)。以下“本轮未运行/未提交”为设计阶段历史，不能作为当前实施状态。

业务验收覆盖 A 提交→B 发布→仍按 A 批准/拒绝、B 新提交、拒绝后重提、提交/发布两个胜序、错误版本无法决定、历史不改写及独立实时门禁。只创建符合新模型的测试数据，不保留旧数据/旧客户端兼容用例。

本轮只进行文档生成器测试、brief freshness、registry 及链接/格式检查；没有运行新业务或联合链验收，没有 commit/push。resource-hub 工作保持原样。

文档验证（2026-11-04）：生成器测试 30 项通过，72 份 brief freshness 通过，registry 367 行/8 个退役编号通过，702 个 Markdown 引用无新增坏链，git diff --check 通过；resource-hub 两文件保持原样。未运行业务测试、未执行数据重建、未 commit/push。
