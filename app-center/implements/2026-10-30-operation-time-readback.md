# UC028 运维操作回执与持久化时间一致性

状态：`COMPLETE`（本地后端修复，两轮完整门禁通过；未发布），更新于 2026-11-01。App 本地提交 `5b42ed7c0ae2a79a2df701211cadb40981d17db8`。用户通过 Console 联调明确要求后端统一时间；本包只修复 Suspend/Restore 操作的持久化表示，依据 [UC028 / BR-APP-036](../use-cases/UC-APP-028-suspend-and-restore-application.md#br-app-036)，保留权限、OCC、事务及提交结果未知时的恢复语义。

## 根因与修复

[Console 实链记录](../../console/implements/2026-10-30-app-operation-time-readback-gap.md)确认：同一事件和 revision 下，暂停回执与 Get 仅 suspendedAt 的 nanos 不同，换算到毫秒相同。App 源码基线 `4f62bad` 在 Mongo Repository 的 Set 中将原始 Clock 时间写入 Application、事件及 outbox，再以内存原始值返回回执；BSON Date 存储为毫秒，后续读回丢失亚毫秒部分。

`internal/adapter/mongo/application_operations_repository.go` 在进入事务前一次将操作时间转换为 UTC 毫秒时刻。所有状态写入、事件 occurredAt、outbox createdAt 及回执复用同一值；事务重试不重新取时，也不在提交后通过无版本查询拼装回执。Suspend 和 Restore 共享此路径，Restore 保留已持久化的上次 suspendedAt。没有修改系统 Clock、其他业务时间或前端比较容差。

UC028 已按本次用户授权明确该精度与完全一致的读回要求，文档提交 `f8576ea`，并重新生成 UC028 brief 与受来源摘要影响的 UC038 brief。API 字段、路由、身份、权限和 schema 均未改变，不需要迁移历史数据；已持久化的 BSON Date 本身已经是毫秒精度。

## 回归与证据

新增 `cmd/app-center/application_operations_time_integration_test.go`，使用真实事务型 Mongo、正式 Application 创建 Repository 和注入 Clock 的运维 UseCase handlers，不用 fake Repository 证明持久化行为。

- 两次 Clock 均含非零亚毫秒，分别执行 Suspend 和 Restore；比较完整命令结果与同 event/revision 的 Get，不能只比较毫秒换算值。
- 根据 applicationId/eventId 读取对应事件与 outbox，核对操作时间和事件 revision；验证 Restore 保留上次暂停时间。
- Clock 推进后以旧 revision 重放命令，验证冲突、不改变状态且不新增事件/outbox。
- 修复前同一新增回归的 suspend/restore 两项均失败；修复后与既有事务状态/outbox 专项一起通过。

专项命令：

```bash
GOTOOLCHAIN=go1.25.5 bash scripts/test-mongo-integration.sh \
  -run 'TestIntegration_UCAPP028_BR_APP_036_OperationTimeReadback|TestApplicationOperationsRepositoryIntegration' -v
```

本地诊断（不提交、不转发真实凭据或私有响应）：`iwut-app-center/.artifacts/integration/run-EoZvfvaF` 为修复前，`run-bo4RhGIX` 为修复后。

2026-10-30 完整 `make check-full` **24/24 PASS**，`changed_sources=[]`，报告：`iwut-app-center/.artifacts/verification/20261030T095408Z-5myrng3a/report.json`。该轮在北京时间 18:18 完成；聊天中断没有终止后台门禁，原先待补齐的是回报和记录。最后的真实 Mongo/HTTP/gRPC race 项耗时 1434.304 秒。

2026-11-01 用户要求重新测试。核查无残留测试进程或容器后启动新的完整 `make check-full`，再次 **24/24 PASS**，`changed_sources=[]`，报告：`iwut-app-center/.artifacts/verification/20261031T175237Z-_pjkgvxf/report.json`（目录时间为 UTC）。本轮于北京时间 01:52 开始、02:14 完成，最后的真实 Mongo/HTTP/gRPC race 项耗时 1269.406 秒。运行期间隔离 Mongo 的查询和写入计数持续增加，实际用例在推进；不是仅有等待进程。

两轮固定 Go `1.25.5`、App 基线 `4f62bad` 加本包改动、API `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6` 及已提交文档 `f8576eadb7b3c1038d16bfa51ef0cbafe061a51d`；新一轮起始指纹与上轮三项均一致：

| 输入 | 内容指纹 sha256 |
| --- | --- |
| App（提交前） | `c88a23222bbd218cb11afaa035426c8bb5874ee6118ff0c81d34faaecd81ee85` |
| API | `b9f1e26ee3b52ab7547d6ff415155d6a9462291fdfac5888dd657c42c3df4dff` |
| Docs | `0ae1babb62f2d84a7c3264d5174d7a60bc31ac0d5f8bc7a546f4e009f5ecacf0` |

最终再次核对完整报告、三项起止指纹与当前 App 输入后，本地提交为 `5b42ed7`；提交前后本包三个文件的 sha256 一致，验证后未修改源码，App 工作区干净。验收记录和实现导航在本轮结果结束后补齐，不改权威设计或冻结验证输入。

## 发布边界

本轮保持既有本地修复和提交范围，未 push、发布镜像或部署。没有修改 Auth、Gateway、Console 或 API 源码，也没有运行本轮真实 Auth/Gateway/Console 联合链；完整后端门禁不能替代已发布镜像验收。发布包含修复的新 App 镜像后，Console 仍须保留原严格断言、拉取新输入，先复验治理场景中的暂停与恢复，再执行其完整门禁。
