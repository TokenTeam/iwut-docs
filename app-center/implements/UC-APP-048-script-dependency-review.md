# UC048 既有应用接口修订

用户已接受 UC048、ADR-008 及以下既有用例修订。

| 既有用例 | 修订范围 |
| --- | --- |
| UC002/003 | 创建和完整替换草稿都显式提交 `scriptReferences`。Proto 用有 presence 的消息承载列表，空列表表示不使用脚本。引用内容随现有 Version revision 和 OCC 一起更新。 |
| UC004 | AppReview 快照保存规范化后的精确版本、格式、摘要和脚本审核 ID。沿用既有送审事务，加入真实条件写栅栏与反向依赖登记。 |
| UC005 | App 批准时核对全部固定脚本的批准事实，记录实际使用的决定 ID、版本 ID 和摘要。待审和拒绝使用各自的稳定错误。 |
| UC006/035 | 恢复草稿保留引用，放弃草稿按原边界清理。已提交的快照和历史反向依赖仍可追溯。 |
| UC029/030/034 | 应用管理和审核详情返回精确引用、当前阻塞状态及快照摘要。应用管理员在有权限的应用上下文中查候选；App Reviewer 可按本次审核里的固定引用逐条读取正文和政策。 |

App 审核详情列出引用和状态，正文走单条引用详情。一个应用最多引用 16 个脚本，单个脚本最大 1 MiB。逐条读取能沿用 Gateway 现有的消息上限，也能在每次读取时确认调用者对该 AppReview 有权且目标在固定快照中。候选和私有版本历史的响应只包含授权范围内的元数据。

UC048 先以真实 MongoDB 验证草稿和待审提交、引用权限、OCC、事务回滚及待审时拒绝批准。真实脚本决定产生后的继续批准，以及拒绝与送审的两个胜序，随 UC044/049 关闭联合验收。工程入口见 [UC048 brief](../briefs/UC-APP-048.md)，权威规则见 [UC048](../use-cases/UC-APP-048-manage-application-script-dependencies.md) 和 [ADR-008](../adr/ADR-008-script-dependency-transactions-and-cascade.md)。

App 实施提交 `d14a82a`，试用读取回归修复 `bdabcf5`，固定本地 API `d2900b3`。迁移 `0038_application_script_dependencies` 添加反向依赖集合、唯一索引、级联查询索引及脚本版本写栅栏。反向依赖与审核快照均保存精确版本、格式、摘要和脚本审核 ID。应用批准保存对应脚本决定 ID。恢复草稿保留引用，更换引用并重新送审后旧尝试仍保留原记录。

已有创建和完整替换入口要求有 presence 的 `ScriptReferences`，无依赖时 HTTP 使用 `{"scriptReferences":{"items":[]}}`，原生 gRPC 传空消息。新查询接口如下。

| 方法 | HTTP 路径 | 读取权限 |
| --- | --- | --- |
| `ApplicationVersion.ListApplicationScriptCandidates` | `GET /v1/applications/{application_id}/script-candidates` | Developer Console 中具备 Developer 资格的当前应用管理员 |
| `ApplicationReviewQueryService.GetApplicationReviewScript` | `GET /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/scripts/{script_version_id}` | Admin Console 中对该 AppReview 有读取权限的 Reviewer |

真实 MongoDB 专项验证反向登记失败后的事务回滚、提交栅栏、OCC、拒绝后恢复及历史保留。待审脚本阻止批准，测试以持久化终态夹具验证拒绝阻断和批准证据落库。App 直连 HTTP/gRPC 专项验证字段 presence、候选与正文隔离、无关引用隐藏、版本详情与审核快照读取。固定 App `bdabcf5` 与 API `d2900b3` 的 `make check` 和 `make test-race` 已通过。MongoDB 与 HTTP/gRPC 的 218 个顶层用例分组运行，中断后的 7 项已补跑通过，合计 212 通过、6 项按跨服务环境前置条件跳过、0 失败，输入保持不变。合并报告位于 App 仓库 `.artifacts/script-dependency-uc048/resume-szqk9r2y/report.json`。这是分阶段与分组补跑证据，原 `check-full` 报告仍保留原失败状态。该首轮证据尚未包括 Gateway 新路由，后续接入和联合验证见下文。

App 镜像 `iwut-app-center:script-dependency-bdabcf5` 在本机构建，ID 为 `sha256:71c60e49a1c7b044e7e636f109b837622aa0d9619fe29805a91c70f2b2368401`。使用该镜像与 Gateway `54763f5`、Auth 的 `script-query-71b6531` 镜像，既有 UC041–045 联验通过。UC048 首轮时两条精确路由尚待 Gateway 接入，现已随 `5bd9c9c` 交付。Developer Console 的草稿请求组装、Auth 的 OAuth 端到端测试夹具仍需传递显式空引用或所选引用。

2026-11-07，Auth 所有者已确认现有 `APP_CENTER_REVIEW_AUTO_REJECTION` SYSTEM purpose 可记录脚本依赖拒绝，并更新共享契约与 UC049。UC044/049 已实现用户接受的关闭豁免方案，App `207e3f2` / API `015f172` 的完整 `check-full` 24/24 通过。真实脚本批准后 App 批准、脚本拒绝后的自动拒绝、关闭与级联、送审与拒绝的两个并发胜序已通过。Gateway `5bd9c9c` 已接入两条 UC048 查询和脚本决定，协议联验通过。详见 [联合实施与最终验收](UC-APP-044-049-decision-cascade-readiness.md)。
