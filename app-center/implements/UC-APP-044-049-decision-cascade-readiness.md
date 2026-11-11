# UC044 与 UC049 实施与验收

2026-11-07。UC044 和 UC049 的设计为 `ACCEPTED`，App/API 实现与 Gateway 接入已完成，固定输入的完整 `check-full` 24/24 通过。用户要求遇到阻碍或依赖时暂停并说明方案。用户已于 2026-11-07 接受方案 A，权威 UC027/045/049 已修订并重新生成 brief，工作包已据此完成。下表保留发现冲突时的分析。

## 准备过程

- 已生成两个工作包的 spec 和 brief。
- Auth 所有者已确认现有 `APP_CENTER_REVIEW_AUTO_REJECTION` 覆盖 `SCRIPT_VERSION_REJECTED`，已补充 UC-AUTH-003、共享契约和 UC049 的确认说明，并重新生成相关 brief。无需新增 Auth purpose、接口、权限或数据库迁移。
- 已在本地工作树起草脚本决定事务、持久任务和处理器、结构化拒绝原因、查询终态及 HTTP/gRPC 接线。发现冲突时，代码和 App 相关 Proto/生成物仍为本地草稿；后续已完成并固定为下文提交。
- 发现规则冲突时仅完成相关 Go package 的编译及过滤测试检查。该次入口未提供 MongoDB URI，不能作为业务验收。接受关闭豁免后的最新验证见下文。
- UC048 旧记录中的“全量回归运行中”已更新为固定输入的分阶段、分组及补跑结果。该证据对应 App `bdabcf5` 和 API `d2900b3`，不覆盖后续 UC044/049 改动，后者使用下文完整门禁结果。

## 已解决的生命周期冲突

| 项 | 内容 |
| --- | --- |
| blocked | false，方案 A 已接受 |
| authority | UC027 的“本地关闭事务”、BR-APP-022/024，与 UC049 的 BR-SDP-006/009 |
| conflict | UC027 要求非 ACTIVE 应用保留 SUBMITTED/PENDING 历史状态并禁止审核决定。UC049 要求所有精确关联的 PENDING AppReview 自动拒绝，且 COMPLETE 时不存在仍待审的精确依赖。一个依赖应用在级联前关闭即可让两项要求无法同时成立。 |
| evidence | 现有应用决定事务通过 Application coordination fence 串行化，并在读和锁定管理员时都要求 lifecycleStatus=ACTIVE。关闭不会把待审 Review 改成其他终态。直接复用该入口会持续失败，忽略该失败又不能证明任务 COMPLETE。 |
| options | 方案 A，对 CLOSING/CLOSED 目标记录明确的关闭豁免，保留历史状态，完成判据覆盖“已决定或已验证关闭”。方案 B，为内部脚本依赖拒绝定义非 ACTIVE 应用的专用例外，允许关闭后改写审核和 Version。 |
| suggested | 方案 A，延续 UC027 的历史保留规则。在同一事务取得现有 Application fence 后确认生命周期。ACTIVE 目标沿用现行一次决定事务，CLOSING/CLOSED 目标保存幂等结果 APPLICATION_CLOSED 并关联已有关闭事实。最终复核每条精确依赖均已决定或有可验证关闭豁免。 |

方案 A 需要先修订 UC049 的精确目标与完成判据，并在 UC027 明确“记录级联豁免不属于改写审核历史”。UC044/045 的进度投影应能区分实际拒绝、既有终态和关闭豁免。用户已接受上述范围，已修改权威 UC/BR 并重新生成 brief，继续实现。

## 验收范围

已先串行运行 UC044 决定专项与 UC049 级联专项，覆盖脚本终态、任务保存失败回滚、SYSTEM 失败重试、lease 恢复、重复处理、多源竞争、两种送审胜序、恢复草稿后的新审核，以及关闭与级联两个提交胜序。专项通过后冻结最终输入，完整门禁已通过。App/API 提交、API 对齐及 Gateway 接入沿用用户确认的流程。

权威来源见 [UC027](../use-cases/UC-APP-027-close-application.md)、[UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 和 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)。Auth 确认见 [UC-AUTH-003](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md) 与 [SYSTEM 契约](../../platform/contracts/auth-system-principal-v1.md)。

## 当前实施形态

脚本决定入口为 `ScriptReviewService.DecideScriptVersionReview`，HTTP 使用 `POST /v1/script-resources/{resource_id}/versions/{version_id}/reviews/{review_id}/decision`，仅 Admin Console surface 消费。请求 command 为 expectedVersionRevision、policyVersion、decision（APPROVE/REJECT）、confirmedCheckIds、reason。服务器复核独立脚本审核权、贡献者/提交者利益冲突和固定审核快照。批准返回唯一决定，拒绝另返回持久 cascade 的 PENDING 回执。

`GetScriptReview` 增加决定与级联进度，含 processed/total、rejected/alreadyTerminal/applicationClosed、observedAt 与受控 lastFailure。`GetScriptVersion` 返回关联 decisionId，发布角色通过该入口读取决定定位，不获得审核私有理由或人员详情。UC045 的发布历史和分发门禁仍随 UC046 验收。

迁移 `0039_script_decisions_and_cascade` 创建脚本决定与级联 schema、任务源决定唯一索引和目标幂等唯一索引。worker 每次最多处理 32 步，每个目标连同进度在独立事务提交。lease 为 30 秒，单轮有界 deadline 为 20 秒，失败 5 秒后重新尝试，持续失败保留任务。Application coordination fence 下核对真实关闭记录，再保存 APPLICATION_CLOSED 豁免。处理完反向依赖后逐条重扫 Review 快照，缺失登记或未解决的待审目标阻止 COMPLETE。

首轮 UC044 与 UC049 的真实 MongoDB race 专项通过，HTTP/gRPC 正常生产组装链也已通过。后者验证真实脚本批准后应用批准并保存依据、脚本拒绝后生产 worker 使用解析出的 SYSTEM ID 自动拒绝应用，以及私有脚本理由不传播给应用。SYSTEM 失败重试和送审/拒绝两个并发提交胜序通过专项。最终输入回归、完整门禁及 Gateway 联验均已通过，结果见下文。


## 固定输入与联合验证

App 本地提交 `207e3f2be27e988e9e8391ed24f28e54b4425b92`，API `015f172611ea35f9386438ac7464eccb52bb9a8c`。API 对齐会话已将 App、Auth 和独立 Proto 对齐到此 API，App/API 工作树干净。

Gateway 本地提交 `5bd9c9cf088e55616b0328e87f6858381bbd418f`，同一 API，已接入脚本决定 ADMIN、应用脚本候选 DEVELOPER、应用审核关联正文 ADMIN 三条精确入口。Gateway `make check` 和 `make protocol-e2e` 通过，涵盖新入口的 HTTP/JSON、原生 gRPC、gRPC-Web、Session 与 Console surface 边界。

使用固定本地 App、Auth、Gateway 镜像的既有脚本三镜像回归已通过。该回归验证 UC041/042/043/045 的真实注册登录、权限授撤及读写路径；新脚本决定、关联应用批准及自动拒绝由 App 正式组装 HTTP/gRPC 专项验证，Gateway 新路由另由其协议专项验证。证据范围分别记录，不把既有三镜像用例记成全部新业务场景。

Auth 镜像来自 `e92b96c` 与 Auth 负责人保留的现有工作树，API 为 `015f172`，源码指纹为 `22298e2e70f8306d616e13199ba3dd9b66bd079aa49f03bff6a4539072d3c6a9`，构建前后未变化。App 和 Gateway 镜像来自各自固定提交。

| 镜像 | ID |
| --- | --- |
| App `iwut-app-center:script-review-207e3f2` | `sha256:8a5be07e6fa19ad2625f169a6e020507722d04885332c7b8b684b6d46eb7f954` |
| Auth `iwut-auth-center:script-local-uc044-049-015f172-22298e2e70f8` | `sha256:1c36dce26f75e3c9d9bbbf11031df6bf8e9eafd46ec49babb967f9f919e9a587` |
| Gateway `iwut-gateway:script-local-uc044-049-5bd9c9c` | `sha256:63cb28419da5a00d92a6e9500b16da1f83d83c728f7b493358ea06e723c11d90` |

App 完整 `check-full` 使用本地已提交文档快照 `bcbd0e79c41e0e90e509fe4be2be41f9f1bccc95`，24 项全部通过，`status=passed` 且 `changed_sources=[]`。最后的全量 MongoDB/HTTP/gRPC race 阶段也已通过，Mongo 包耗时约 2002 秒，HTTP/gRPC 包约 208 秒。报告位于 App 仓库 `.artifacts/verification/20261107T104258Z-o166d3ew/report.json`。源码与生成物冻结，三镜像和专项日志保存在 `.artifacts/script-review-uc044049/`。该目录下 `integration-inputs.json` 汇总固定输入。


UC044/049 当前后端范围关闭。UC045 的唯一决定、终态详情和级联进度已完成本段验收，发布历史与分发门禁仍随 UC046 验收。UC048 的真实脚本批准前置、脚本拒绝阻断及两种送审胜序均已覆盖。后续UC046发布/暂停/恢复及UC047后端分发/精确内容已于2026-11-08完成，完整backend与固定三镜像通过；见[UC046](UC-APP-046-script-publication-implementation.md)、[UC047最终记录](UC-APP-047-script-distribution-implementation.md)。所有代码提交和镜像均为本地结果。
