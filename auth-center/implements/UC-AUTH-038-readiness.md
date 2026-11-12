# UC-AUTH-038 脚本权限交付核对

本文记录 maintain 退役前的版本。现行四项权限及验证见[退役交付记录](UC-AUTH-038-retire-maintain-readiness.md)。

状态：`AUTH_BACKEND_VERIFIED / CONSUMER_INTEGRATION_PENDING`。

用户接受 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md) 与 [UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 的五项权限修订。更新共享契约并生成 [UC038 brief](../briefs/UC-AUTH-038.md) 和 UC010 brief 后实现。

- Auth/API 增加 `ScriptPermissionService`，提供 HTTP/JSON 与原生 gRPC。按目标一次查询五项，按固定枚举逐项授撤。旧 `ScriptMaintainerPermissionService` 保留原 RPC、路由、消息、错误与开关，固定操作 maintain。两组共享限流、目标快照、版本与原子审计。
- 查询和撤销覆盖 ACTIVE 与 DISABLED，授予才检查目标已验证邮箱及恢复就绪。只修改选中的权限。五项脚本权限仅向 App audience 按精确授权投影。撤销在新签发中生效，已签发身份仍遵循原有效期及验签容差。
- 新入口由 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED` 独立启用，默认关闭。部署新版签发器前按 UC038 只读检查可能的历史同名授权。

## 验证

- 生产 Wire 专项使用真实 Mongo、生成的 HTTP/gRPC 客户端和 App 实际验签器。对同一 Session 逐项正式授予再逐项撤销，查询和签发均核对全部权限，撤销一项时其他授权保持有效。新接口授予 maintain 后可用旧接口查询、撤销。验证 Auth audience 隔离、身份 jti 独立，以及脚本权限不能用于管理他人权限或取得 App Reviewer 权限。
- 真实 Mongo 专项覆盖跨权限共享版本竞争、DISABLED 且目标邮箱损坏时可查询和撤销、审计失败回滚、签发与撤销的提交顺序。
- Auth `make check`、普通全仓 race、两份 API `proto-check`、共享 API `go test ./...`、文档 brief/registry 和 30 项工具测试通过。
- 真实 Mongo 全仓 race 回归通过，完整生产 Wire 包 185.573 秒，完整 Mongo 仓储包 580.635 秒。随后补充的非法枚举和重复授予断言在同一真实环境专项复验通过。

## 待交付

2026-11-09 已完成五项 Auth/API 交付的提交与推送：Auth `8921b8354f3252a66f735e5e74489d6e62bfe749`，API 统一版本 `7651f96ceb85f11784660521b0f3c8a7c30d7d57`。Gateway 精确路由、Console 管理页面及 App UC044/045/046 的命令和查询鉴权按各自工作包验收。

2026-11-10 接受的本人脚本权限发现是后续增量，独立版本与验证见[本人读取交付记录](UC-AUTH-038-own-read-readiness.md)。
