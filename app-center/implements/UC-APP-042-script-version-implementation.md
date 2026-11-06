# UC042 脚本版本草稿实施记录

设计 `ACCEPTED`。App 核心状态 `CORE_COMPLETE`。工作包使用 [UC042 brief](../briefs/UC-APP-042.md)。

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

远端 `master` 查询结果为 `35a675c`。当前远端分支尚无这两项 App API。依照 [ADR006](../adr/ADR-006-proto-v1-and-api-repository.md#子模块与构建)，App 正式接线需要 CI 可获取的 API 提交。待 API 负责人合入或获得独立分支发布授权后，固定该提交，再完成 UC042 transport、Wire 和联合验收。UC043–049 依已接受的串行清单随后开展。
