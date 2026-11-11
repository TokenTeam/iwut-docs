# UC046 独立脚本发布实施记录

2026-11-07 实施，2026-11-08 完成验证。UC046 与 ADR008 已接受，App 实现、专项、Gateway 接入、固定三镜像业务联验和完整后端门禁均通过。本记录只覆盖 UC046 与 UC045 的发布管理查询段，运行内容获取及既有应用发布/启动门禁属于 UC047。

## 实现范围

资源创建事务同时初始化推荐 head=null、publicationRevision=1，以及 AVAILABLE、availabilityRevision=1。`script_publications` 保存 head，`script_distribution_availability` 保存独立门禁及 adapter-only coordinationRevision，`script_published_versions` 保存永久精确版本资格，`script_publication_events` 保存不可变事件。迁移为 `0040_script_publication_and_availability`。新资源初始化失败时资源、head、gate 和创建审计整体回滚。

发布核对完整匹配的 ScriptReview APPROVED 事实，事务内固定精确文本摘要、格式、字节数和审核决定。首次发布资格、head 与事件同事务提交。回退到曾发布版本和 ClearHead 都保留原资格、首次事件及已批准应用的固定引用。已有资格缺失或来源事件不匹配时失败关闭，不凭重新点击发布修复损坏数据。

实际发布、清空、暂停与恢复都对同一个资源门禁文档做真实条件递增，Publish/Suspend 的两个提交胜序已由真实 MongoDB 专项验证。publicationRevision 和 availabilityRevision 独立变化。匹配 revision 的同 head、空 head 和重复目标门禁为 no-op，保留原审计时间且不写业务事件。暂停期间同 head 的匹配 no-op 不新增发布资格，实际新发布仍失败。旧 revision 先按所属计数器返回冲突。门禁不承担脚本审核结果，不因暂停改写既有批准。

命令分别要求可信 USER 的 `app.script.publish`、`app.script.suspend`、`app.script.restore`，没有隐式授予。Suspend/Restore 的理由按 trim 后 1..2048 UTF-8 bytes 校验。操作者、时间与事件 ID 由可信身份和服务 ports 提供。

## API 接线

下列入口均供 Admin Console 使用，沿用 App audience 和 Session 身份签发。

| 方法 | HTTP 路径 | 精确权限 |
| --- | --- | --- |
| ScriptPublicationService.PublishScriptVersion | POST `/v1/script-resources/{resource_id}/versions/{version_id}/publication` | publish |
| ScriptPublicationService.ClearScriptHead | POST `/v1/script-resources/{resource_id}/publication/head/clear` | publish |
| ScriptPublicationService.SuspendScriptDistribution | POST `/v1/script-resources/{resource_id}/distribution/suspend` | suspend |
| ScriptPublicationService.RestoreScriptDistribution | POST `/v1/script-resources/{resource_id}/distribution/restore` | restore |
| ScriptQueryService.GetScriptPublication | GET `/v1/script-resources/{resource_id}/publication` | 任一脚本管理权限 |
| ScriptQueryService.ListScriptPublicationHistory | GET `/v1/script-resources/{resource_id}/publication/history` | publish |

Publish/Clear 的 command 为 expectedPublicationRevision；Suspend/Restore 为 expectedAvailabilityRevision 与 reason。写回执返回 state、changed，以及实际变化时的 eventId/eventAt。no-op 的 eventId 为空、eventAt 无值，state 保留真实更新时间。

查询状态返回 head 精确版本描述、两个 revision、availability 和各自更新时间。发布历史按 at/eventId 稳定倒序，使用 limit/cursor；默认20，最大100，游标签名绑定调用者有效权限与资源。历史只返回发布与 ClearHead 事件摘要，不返回运维理由、人员审计或正文。所有写入与查询的 HTTP 成功/失败响应 private, no-store，先鉴权再定位。

## 规则与验证

| 规则 | 验证 |
| --- | --- |
| BR-SCR-002 | 三项精确命令权限互不替代，非法目标前鉴权；普通维护/审核/应用审核/平台管理权限不隐式授予发布权 |
| BR-SCR-015 | DRAFT/PENDING/REJECTED 禁止发布，资源/版本关系隔离，完整批准事实，资源初始化与首次发布事务回滚 |
| BR-SCR-016 | 发布 A、发布 B、回退 A、清空 head 后两条永久资格仍在，首次事实不覆盖；损坏历史资格失败关闭 |
| BR-SCR-017 | 发布/暂停真实写栅栏的两个并发提交胜序，暂停阻断实际发布，恢复保留 head 与历史资格 |
| BR-SCR-018 | 两个发布竞争只消费一次 revision，迟到旧 revision 冲突，匹配 no-op、原始时间精度读回、字节级理由长度、审计插入失败整体回滚 |
| UC045 发布查询段 | 同毫秒事件分页、权限和 cursor 绑定、门禁事件/理由隔离、HTTP/gRPC 正式入口与无权限错误边界 |

真实 MongoDB race 专项与 App 正常 Wire 组装 HTTP/gRPC 专项已通过。三镜像用例已扩展为 `TestE2E_UCAPP041_042_043_044_045_046_ScriptManagementLocalImages`，使用正式注册的独立 Reviewer、真实 Auth 授权/撤权和 Gateway 三协议验证，最终通过，耗时36.82秒。首次在第11次 Auth 权限写入触发每操作者每分钟10次的正常限流；测试仅对该接口精确的 SCRIPT_PERMISSION_RATE_LIMITED 429 有界等待，使用原 payload/OCC 重试，权限政策与业务代码不变。首次失败、修复和通过日志均保留。

## 固定输入与本地接入

| 输入 | 固定值 |
| --- | --- |
| App 业务实现 | `10a08e2a78d6f433aac21e06c6745a09de9fb866` |
| App 测试限流适配 | `1b28d50`，只修改三镜像测试 helper，生产代码及 API 不变 |
| App/API、Auth/API、Gateway/API、独立 API | `40cad37e41e25a14d4e6b044096f2784110ea9e4`，API 对齐会话核验通过 |
| Gateway | `f0d2a224dfb5c6a6b73b74456e19d2ea59e101b8`，6条新增 ADMIN 路由，目录155条 |
| Auth | HEAD `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f` 加现有未提交权限实现，源码指纹 `22298e2e70f8306d616e13199ba3dd9b66bd079aa49f03bff6a4539072d3c6a9`；构建前后保持 |
| 后端门禁 docs 快照 | `33e0baca40b465730d530e118f3971453cd672f6`，从权威工作树复制到忽略的验收目录后提交，不占用 docs main worktree，不修改权威设计 |

| 本地镜像 | 固定 image ID |
| --- | --- |
| `iwut-app-center:script-publication-10a08e2` | `sha256:e954066f257c35face7b09b819570ab12ab5739a31efc0751d6e642f13a54306` |
| `iwut-gateway:script-publication-f0d2a22` | `sha256:0cbe3de6775a29651625d834a763339c6d77697d29ef03e3c05af0ca1fff70ee` |
| `iwut-auth-center:script-local-uc046-40cad37-22298e2e70f8` | `sha256:2335154e4abd28e3d4e6b1d8b9d6bec1f7d618297f1e69ab4b6d2bc35f32c1da` |

Gateway `make check` 与完整 `make protocol-e2e` 通过，27条 App 管理/查询/决定路由完成真实三协议验证，并通过 Admin Cookie/BFF、CSRF、身份头清洗及 Developer surface 隔离。App 固定三镜像业务联验使用上述同一镜像；测试限流修订没有改变 App 镜像中的生产代码。本轮没有 push 或远程部署。

App 证据在服务仓库 `.artifacts/script-publication-uc046/`：`targeted-final.log`、`app-image.log`、`three-image-e2e.log`（首次限流失败）、`three-image-e2e-paced.log`（最终通过），镜像 ID 及服务诊断见 `image-diagnostics-paced/`。Auth 构建记录 `/tmp/iwut-auth-uc046-image-20261107-m44ufupe/report.json` 保存构建前后工作树/API 指纹，Gateway 交付记录在其 `docs/verification/2026-11-06-script-management-routing.md`。

完整门禁的第一次执行在前23项通过、最后一项仍运行时主动中断，以纳入测试夹具修订，不计为最终通过。报告 `.artifacts/verification/20261107T151732Z-443lfum5/report.json` 的状态为 interrupted。最终固定输入执行为 `.artifacts/verification/20261107T153242Z-a_bae9ap/report.json`，24/24 全部通过，`changed_sources=[]`。执行时间为 UTC 2026-11-07 15:32:42–16:05:37；最后一项耗时1963.406秒，Mongo race 包1957.132秒，HTTP/gRPC E2E 包231.763秒。App 与 API 工作树保持干净，验收容器已清理。UC046 与 UC045 发布管理查询段完成。

UC047 的[具体接口与既有 UC 修订方案](../design-notes/2026-11-07-uc047-runtime-script-contract-proposal.md)已于2026-11-07由用户接受。UC046完整门禁通过后，UC047已串行完成权威用例、读契约、brief及实现，完整backend 24/24和固定三镜像均通过；见[UC047最终实施记录](UC-APP-047-script-distribution-implementation.md)。
