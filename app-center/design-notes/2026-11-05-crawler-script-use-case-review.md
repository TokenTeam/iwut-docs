# 平台爬虫脚本：Use Case 审核与串行工作清单

状态：`ACCEPTED`

2026-11-06 用户接受 UC-APP-041–049 与 ADR-008，并要求按下表串行执行。业务规则与事务设计以对应 UC、BR、ADR 为准。UC041 和 UC042 的本地三镜像专项已通过，App 全量回归通过 24/24。当前状态见 [UC042 实施与镜像联验](../implements/UC-APP-042-script-version-implementation.md)。

## 已确认的产品边界

平台维护文本脚本，在用户客户端执行；独立资源、版本、审核及发布，正式属于 App Center 同服务同库。当前 JSON，未来可扩展 Lua，服务端不过度解析。应用可引用待审脚本，应用批准依赖脚本获批；脚本拒绝自动拒绝所有精确引用它的待审应用。不设计旧数据/接口兼容，不实现客户端 Runner 或机器检查引擎。讨论来源与演进见[前期背景](2026-11-05-crawler-script-management-proposal.md)。

## 用例与串行工作顺序

每项遇到依赖阻塞即停下说明方案，不越过当前工作包。

| 顺序 | 用例 | 本次设计重点 |
| --- | --- | --- |
| 1 | [UC041 管理脚本资源](../use-cases/UC-APP-041-manage-script-resource.md) | 独立身份、平台精确权限、元数据和 OCC |
| 2 | [UC042 创建与编辑脚本版本草稿](../use-cases/UC-APP-042-manage-script-version-draft.md) | 原文/摘要、DRAFT 替换、提交后不可变 |
| 3 | [UC043 提交脚本版本审核](../use-cases/UC-APP-043-submit-script-version-review.md) | 固定文本、完整人工检查定义、提交绑定政策 |
| 4 | [UC045 查询脚本管理与审核视图](../use-cases/UC-APP-045-query-script-management-and-reviews.md) | 维护/审核/发布/运维读取隔离 |
| 5 | [UC048 管理应用脚本审核依赖](../use-cases/UC-APP-048-manage-application-script-dependencies.md) | pending 引用、提交冻结/登记、批准前置、受限关联正文 |
| 6 | [UC044 审核脚本版本](../use-cases/UC-APP-044-decide-script-version-review.md) + [UC049 自动拒绝关联应用](../use-cases/UC-APP-049-cascade-script-rejection.md) | 同一工作包闭合决定与级联义务，禁止只交付拒绝接口遗漏处理器 |
| 7 | [UC046 独立发布与分发门禁](../use-cases/UC-APP-046-manage-script-publication.md) | head、历史精确版本、暂停/恢复 |
| 8 | [UC047 独立分发与应用精确内容获取](../use-cases/UC-APP-047-resolve-application-script-content.md) | 无应用关联也可独立分发，应用固定依赖与原文字节一致 |

并发/可靠性方案统一在 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)：同库真实条件写消除送审与拒绝写偏斜，持久任务有界处理、幂等恢复。每个工作包先验证适用依赖：首项核对 maintain 权限，UC044/049 核对审核权限和 SYSTEM purpose；UC048 完成后、UC044/049 闭合前的中间版本不发布为完整能力。

## 已接受的设计决定

以下是 2026-11-06 用户接受的设计摘要。

| 决策 | 接受内容 | 权威位置 |
| --- | --- | --- |
| 谁维护/审核/发布 | 五项精确权限，互不自动授予；创建/修改/提交该脚本版本的人不能决定其审核 | [BR-SCR-002](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002)、[BR-SCR-010](../use-cases/UC-APP-044-decide-script-version-review.md#br-scr-010) |
| 文本/数量边界 | JSON 显式格式、最多1 MiB、保留原字节；应用最多16个脚本资源，各引用一个精确版本 | [BR-SCR-005](../use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-005)、[BR-SDP-001](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-001) |
| 拒绝后的修复 | 脚本版本不恢复草稿，创建新版本/标签；应用现行拒绝恢复机制保留 | [BR-SCR-004](../use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-004)、[BR-SDP-005](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-005) |
| 人工检查内容 | 用途、客户端可执行性、数据/凭据边界、网络/资源使用四项正式文本 | [BR-SCR-008](../use-cases/UC-APP-043-submit-script-version-review.md#br-scr-008) |
| 拒绝何时算完成 | 脚本决定和级联任务先落盘再 ACK；应用批准立即禁止，关联应用自动拒绝有界收敛并可查进度 | [BR-SCR-012](../use-cases/UC-APP-044-decide-script-version-review.md#br-scr-012)、[BR-SDP-009](../use-cases/UC-APP-049-cascade-script-rejection.md#br-sdp-009) |
| 发布机制 | 一个 release head，曾发布历史版本继续分发，head 变动不换应用精确依赖 | [BR-SCR-015](../use-cases/UC-APP-046-manage-script-publication.md#br-scr-015)、[BR-SCR-016](../use-cases/UC-APP-046-manage-script-publication.md#br-scr-016) |
| 停止分发粒度 | 首期资源级暂停/恢复；影响该资源全部版本，不含单版本撤销 | [BR-SCR-017](../use-cases/UC-APP-046-manage-script-publication.md#br-scr-017) |
| 应用批准与运行 | 脚本获批即可支持应用审核；应用发布/运行还要求该版本曾发布且当前可分发 | [BR-SDP-004](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-004)、[BR-SCR-020](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-020) |
| 独立分发可见性 | 已批准且已发布的可用脚本向所有 ACTIVE 登录用户开放，不要求关联应用；不能据此获得应用资格 | [BR-SCR-022](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-022) |
| 未获批正文可见性 | 应用维护人只见候选元数据；有权的 App Reviewer 可读固定关联正文但不自动获脚本决定权 | [BR-SDP-002](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-002) |

## 接受后的修订与分工

App 内部模型、事务、脚本接口和联合门禁归本 agent。在各对应串行工作包按 UC048 的修订矩阵更新既有 App UC/BR 与对应生成 brief。API 方法、字段、错误映射及读契约在其工作包实施前固定。首项使用 [UC041 brief](../briefs/UC-APP-041.md)，后续 brief 随各自工作包准备。

Auth 所有者需确认新精确权限及既有 SYSTEM purpose 是否可覆盖脚本依赖自动拒绝；Gateway 所有者负责路由/ADMIN surface；Console 所有者负责维护/审核/发布和先审脚本再审应用的编排。客户端 Runner 由客户端负责。相邻模块的设计与实现由各自所有者负责，交接由用户分派。

验收以各 UC 的具体案例为准，重点包含真实 MongoDB 两种提交胜序、拒绝/批准互斥、多依赖级联、崩溃重试、与既有自动拒绝竞争及精确正文分发。文档检查通过不等于这些业务验收已执行。
