# UC042 脚本版本草稿实施记录

设计 `ACCEPTED`。本地实现 `COMPLETE`。App 核心、接口接线、三镜像专项及全量回归 24/24 均通过。工作包使用 [UC042 brief](../briefs/UC-APP-042.md)。

UC042 实现资源下独立 UUIDv7 草稿和整份正文替换。`app.script.maintain` 在解析输入和访问存储前检查。创建以资源和区分大小写的标签唯一索引阻止重用。正文经过 UTF-8、空白、NUL 和 1 MiB 字节上限校验，按接收字节存储并计算 SHA-256。替换同时检查资源、版本、DRAFT 状态和 revision。正文、摘要、贡献者和审计以同一次事务写入，匹配 revision 的相同正文保持原状态。

迁移 `0035_script_version_drafts` 为 `script_versions` 和 `script_version_audits` 建立 validator 和唯一索引。真实 MongoDB 的七个定向测试在启用 Go race 检测的隔离副本集上通过。覆盖 BOM、换行和 JSON 键顺序的正文往返、标签创建竞争、同 revision 编辑竞争、非 DRAFT 冻结和审计失败回滚。回归覆盖 UC041、迁移 ledger、幂等性、旧库升级、新库与逐步升级一致性及启动就绪。App 格式、全仓 Go 测试、静态分析和 Wire 一致性检查通过。

## 共享 API 交接

App API 工作区已生成 `app_center.v1.script_version.ScriptVersionService` 的 Proto、稳定错误枚举和 Go 产物。

| 方法 | App 内部 HTTP | 正文 |
| --- | --- | --- |
| `CreateScriptVersionDraft` | `POST /v1/script-resources/{resource_id}/versions` | `versionLabel`、`contentFormat`、`contentText` |
| `ReplaceScriptVersionDraft` | `PUT /v1/script-resources/{resource_id}/versions/{version_id}/draft` | `expectedRevision`、`contentFormat`、`contentText` |

两个方法返回资源与版本 ID、标签、原文、格式、摘要、状态、revision 和时间。接线验收应覆盖 `private, no-store`、JSON 转义下原文保真、路径和正文边界、权限隔离、稳定错误和真实 HTTP/gRPC 调用。与送审的并发胜序由下一工作包 UC043 的事务测试联合验证。

联合补丁 `iwut-app-center/.artifacts/handoff/uc041-042-script-management-api.patch` 包含 UC041、UC042 的 App Proto、生成物和 Makefile 条目。API `proto-check` 和全仓 Go 测试通过。补丁在当前共享 API 工作区执行 `git apply --check` 通过。

## 本地镜像联验

按用户提供的本地流程，App 核心与 App Proto 先分别提交。`对齐 iwut-api-proto` 将独立 Proto、App 与 Auth 的 API checkout 固定到同一提交，随后 `gateway` 使用这一提交接入 App 和 Auth 的六个管理入口。完整 CI 流程在同一对齐与接入步骤后按 API、Gateway、Auth 顺序推送，并使用构建产出的镜像执行联验。

| 输入 | 本地版本 |
| --- | --- |
| App 核心 | `10db7483f3863fd98fe1a6342eed4b032223e8c2` |
| App 接线和测试 | `880e5b8fbd3cfbca36676b5d72daaed91b6a7b23` |
| App Proto 原始提交 | `91ef6240f4251226fd3acdb841a1097e8e221058` |
| 统一 API | `1cb48a97097b96395013e7e3c71e4d68ab510db1` |
| Gateway | `ef984fa5022908188c619b73066014117873e176` |
| Auth 构建输入 | `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f` 加本地 UC038 工作树，构建前后 SHA-256 `706e69336467ef959e329f987bc620ae25fddaaeb514e4134c94a89820e4b501` |

App 直连 MongoDB、HTTP、原生 gRPC 的生产 Wire 专项通过，覆盖 1 MiB 正文、JSON 转义膨胀、原字节、摘要、冲突、权限和缓存头。三镜像专项 `TestE2E_UCAPP041_042_ScriptManagementLocalImages` 通过。正式注册与设备登录得到两个 Session，Auth 通过真实管理接口授权和撤销。Admin HTTP、原生 gRPC 与 gRPC-Web 调用实际 App 脚本写入，Developer Console 返回 404。撤销后同一 Session 的后续写入被拒绝，数据库中只保留两次资源审计和两次草稿审计。Admin 会话转发使用测试 fixture，Gateway 继续调用真实 Auth 签发 JWS。

本地镜像 ID 记录于 `iwut-app-center/.artifacts/integration/run-h0KazIu0/script-management-image-ids.txt`，专项日志位于 `.artifacts/script-local/image-e2e.log`。App `check-full` 24/24 通过，测试前后输入未变。使用 Docs 核对快照 `3036e0a052a6215e6b675fff4c0276247a9770d5`，报告位于 `.artifacts/verification/20261106T063947Z-xbq4x7gf/report.json`。UC043–049 依已接受的串行清单随后开展。
