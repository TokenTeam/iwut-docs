# UC041 脚本资源实施与 API 交接

设计 `ACCEPTED`。App 资源维护与 [Auth UC038](../../auth-center/implements/UC-AUTH-038-readiness.md) 的正式授权及撤销已通过本地镜像联合验收。固定 API、镜像及后续全量回归见 [UC042 实施与镜像联验](UC-APP-042-script-version-implementation.md)。下文保留核心实现与初始 API 交接的历史记录。

## 本轮落地

- `internal/script` 实现独立 UUIDv7 脚本资源、名称/用途校验及创建和替换命令。仅消费可信 App USER 的精确 `app.script.maintain`，在解析目标和访问存储之前检查，不要求 Developer 状态，也不因其它角色自动放行。
- MongoDB 显式迁移 `0034_script_resource_metadata` 增加 `script_resources`、`script_resource_audits` 的 validator 和命名唯一索引。创建和实际替换同事务落业务审计；替换使用 revision 条件写，相同内容只在匹配 revision 时按 no-op 返回。响应、状态和审计的时间统一为 MongoDB 毫秒精度。资源操作不读取或修改版本、审核、发布或应用归属数据。
- 共享 API 的 App 命名空间已在 `iwut-app-center/api` 的独立 checkout 准备 Proto、生成物及 Makefile 条目，基线 `35a675c`。未改另一 checkout 中 Auth UC038 的待提交文件，也未更新 App Gitlink。此处的接口是待固定版本的 App 交接产物，运行服务尚未注册路由。

## App API 交接

服务：`app_center.v1.script_resource.ScriptResourceService`。

| RPC | 内部 HTTP | 请求 |
| --- | --- | --- |
| `CreateScriptResource` | `POST /v1/script-resources` | 正文 `name`、`purpose` |
| `ReplaceScriptResourceMetadata` | `PUT /v1/script-resources/{resource_id}/metadata` | 路径 resource ID；正文 `expectedRevision`、`name`、`purpose`（Proto 内为 `command`） |

两个 RPC 返回同一次原子操作的 `ScriptResource`（ID、名称、用途、revision、创建和更新时间）。不接受正文或 query 自报身份、权限、审计、目标 ID 或技术字段；元数据响应及错误使用 `private, no-store`。稳定错误 reason 见 `app_center/v1/script_resource/error_reason.proto`；身份错误为 401/Unauthenticated，无权限为 403/PermissionDenied，非法请求为 400/InvalidArgument，找不到为 404/NotFound，revision 冲突为 409/Aborted，其余失败为 500/Internal。Gateway 负责外部 ADMIN surface 和 `/app-center` 前缀；Console 接线由相应所有者处理。

共享 API 所有者可从 App 的 API checkout 取本轮 `app_center/v1/script_resource/`、对应 `gen/go/` 和 Makefile 新条目，或应用 App 忽略目录中的 `.artifacts/handoff/uc041-script-resource-api.patch`。合入仍需保留 Auth UC038 的独立修改；可在 API 主工作区检查应用，再统一执行 `make proto-check`。App 按 [ADR006](../adr/ADR-006-proto-v1-and-api-repository.md) 消费已提交且 CI 可获取的明确版本，不将临时本地生成物作为 Gitlink 依赖。

## 续行条件

固定 API 版本后，继续 UC041 的 transport、Wire、真实 MongoDB HTTP/gRPC 与真实 Auth 授予、撤销脚本写权限的联合验收。完整门禁以最终 App、API、Docs 和可验证 Auth 输入为准。UC041 闭合后才进入 UC042；当前未修改其他模块、未提交或推送，也未运行真实数据库的部署迁移。

## 本地验证

- Go 1.25.5：App 全仓单元与架构测试、格式、`go vet`、Wire 一致性检查通过；API `proto-check` 和全仓 Go 测试通过。API 补丁对当前共享 API 工作区执行 `git apply --check` 通过。
- 真实隔离 MongoDB `-race` 定向八个测试通过。UC041 覆盖同名资源使用不同 ID、ID 唯一索引、validator、匹配 revision 的 no-op、陈旧 revision、并发更新仅一项成功、数据库审计时间与状态一致、审计插入失败时创建与更新均回滚。其他专项覆盖迁移顺序与幂等、旧库升级、夹具隔离和启动就绪检查。
- App 完整 `check-full` 与真实 Auth/UC041 命令联验在固定依赖、完成接口接线后执行；当前专项不视为整条链路通过。
