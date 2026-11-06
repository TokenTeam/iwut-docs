# UC043 脚本送审实施记录

设计 `ACCEPTED`。送审核心、App HTTP、原生 gRPC 及三镜像专项已通过。App 全量门禁前 23 项通过，最后的 MongoDB 和传输回归分四组重跑通过。业务规则见 [UC043 brief](../briefs/UC-APP-043.md)。

`app.script.maintain` 持有人按预期 revision 提交草稿。`0036_script_review_submission` 初始化正式政策 `crawler-script-manual-v1`。MongoDB 在一次事务中比较 DRAFT revision，锁定 ACTIVE 政策版本，保存四项正式检查的定义、原文、摘要、贡献者、资源元数据及其 revision，并写入 PENDING 审核、SUBMITTED 版本和审计。版本的唯一审核索引防止生成第二次提交。调用方只提交版本定位和预期 revision。

| 输入 | 本地版本 |
| --- | --- |
| App 核心 | `51a1a10c00946e8086cabc8d0b4e3f811de67aa7` |
| App 接线和测试 | `c2c2475d69a660454a06646914428ce262ea610b` |
| 独立 Proto、App API、Gateway API、Auth API checkout | `15fc2b9b2355ccccd7a17bbfd108dedfd77e3a58` |
| Gateway | `e109b856d0010f2e1257ef8e12fc29f4a5c1f35d` |
| Auth 构建输入 | `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f` 加本地 UC038 工作树，构建前后 SHA-256 `706e69336467ef959e329f987bc620ae25fddaaeb514e4134c94a89820e4b501` |

采用本地镜像接入流程。App、独立 Proto 和 Gateway 已分别提交。Auth 父仓库的 UC038 源码和 API 指针仍是本地改动，Auth 镜像由该工作树构建。

`ScriptVersionService.SubmitScriptVersionReview` 使用 `POST /v1/script-resources/{resource_id}/versions/{version_id}/reviews`。正文为 `expectedRevision`。成功回执包含 `reviewId`、`SUBMITTED`、新 revision、提交时间和政策版本。无有效政策返回 503，过期 revision 或已经送审返回 409。

真实 MongoDB 验证了编辑和送审竞争、政策切换的两种提交胜序、审核快照不随资源元数据变更，以及写入审计失败后的原子回滚。HTTP 和原生 gRPC 覆盖权限隔离、拒绝调用方指定政策、重复提交冲突和送审后的编辑冻结。

Gateway `make check` 和 `make protocol-e2e` 通过，七条脚本管理入口在 Admin Console 可达，Developer Console 拒绝访问。三镜像专项 `TestE2E_UCAPP041_042_043_ScriptManagementLocalImages` 通过，覆盖正式注册与设备登录、真实 Auth 权限授予和撤销、Admin HTTP 送审、重复提交冲突、送审后冻结及同一 Session 撤权后拒绝。Console 会话转发由测试 fixture 提供，Gateway 到 Auth 的身份签发和 App 的业务写入使用真实镜像。

镜像 ID 记录于 `iwut-app-center/.artifacts/integration/run-H4emTAX8/script-management-image-ids.txt`，专项日志位于 `.artifacts/script-local-uc043/image-e2e.log`。

App `make check-full` 使用 Docs 核对快照 `49bc3aac0e5f46b97a100922d1ecfa97114cd082`，报告位于 `.artifacts/verification/20261106T071929Z-pty6o00t/report.json`。最后一项收到 SIGTERM。使用相同 App 和 API 提交，将该项的 215 个顶层用例分四组，在独立 MongoDB 实例上以 `-race` 重跑。209 项通过，6 项按独立跨服务夹具的前置条件跳过，其中脚本三镜像用例已通过上述专项。四组均返回成功，App 和 API 源码指纹一致。分组报告位于 `.artifacts/script-local-uc043/sharded-mongo-e2e/report.json`。

## 下一项权限依赖

本节记录 UC043 完成时的依赖。Auth 后续已补齐四项权限，本地签发复验见 [UC045 准备核对](UC-APP-045-script-query-readiness.md)。

已接受清单在 UC043 后进入 UC045。`BR-SCR-013` 分别以 `app.script.maintain`、`app.script.review`、`app.script.publish`、`app.script.suspend` 和 `app.script.restore` 控制正文、队列、发布历史和运维视图的披露。

Auth 当前的 UC038 与 App audience 签发清单只支持 `app.script.maintain`。UC045 的其他职责无法通过真实 Auth 签发和联合验收。由 Auth 负责人补齐四项精确权限的独立授予、撤销和 `iwut-app-center` audience 签发，并验证无隐式授予、撤销后的新身份和其他 audience 隔离。UC044/049 的自动拒绝需随后确认现有 SYSTEM purpose 是否可以复用。App 保持已接受的职责边界。参见 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013) 和 [Auth UC038](../../auth-center/use-cases/UC-AUTH-038-manage-script-maintainer-permission.md)。
