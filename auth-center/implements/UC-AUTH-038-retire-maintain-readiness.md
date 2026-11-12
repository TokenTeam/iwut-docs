# UC038 脚本 maintain 权限退役交付记录

状态：`AUTH_BACKEND_VERIFIED / LOCAL`。

2026-11-11 用户确认脚本由具备资格的开发者本人上传。[UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 和 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md) 定义现行签发与治理契约。作者资格沿用 `developer_status`，App 负责校验本人归属与写入资格。

- Auth `995fd86753bb323aca777e1f393c54af9b1e22fe` 移除 `app.script.maintain` 的授撤、查询、本人发现与签发投影，同时退役旧专用 RPC 和 HTTP 路由。`be1fdea396178900ab87958621ee81b049cd73e8` 修正 OAuth 集成测试夹具。
- API 固定 `7192df37af4994b7cf198d64953190d92bea8f8e`。独立 Auth API 提交 `720fc8b7957dba248ad1324d8677d497bb883cc6` 的 Auth Proto 和 Go 生成物与该版本逐字节相同。
- 启用权限接口使用 `AUTH_USER_ENDPOINTS_ENABLED=true`、`AUTH_IDENTITY_ISSUANCE_ENABLED=true` 和 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED=true`。Gateway 与 Console 按各自工作包验收路由和权限消费。

## 验证

- Auth `make check`、`make test-race`、API Proto 生成检查及 Go 测试通过。
- 真实 Mongo/race 仓储包通过（782.000 秒）。历史 maintain 记录不出现在本人权限状态与新签 App JWS 中。该轮使用 Auth 代码一致的 `720fc8b`，与统一 API 的差异限于 Auth 未导入的 App 脚本包及生成清单。
- 使用统一 API `7192df3` 的完整生产 Wire/race 包通过（237.075 秒）。四项权限逐项授撤，同一 Session 的新签 App 身份和 HTTP/gRPC 状态一致。旧专用 RPC 返回 UNIMPLEMENTED，旧 HTTP 路由返回 404，退役枚举编号及名称均被拒绝。
- 首轮全仓真实回归的 OAuth 夹具漏传空 `scriptReferences`，并读取了已替换的策略字段。补齐空引用并改用绑定的 `reviewPolicy` 后，OAuth 专项和完整 Wire 复验通过。

## 已构建的本地验收镜像

- 标签 `iwut-auth-center:retire-maintain-7192df3-b7b00930da6c`
- 镜像 ID `sha256:fefbbecbfe247ad2128d36ef24ac499da9e3e68257078975104ad1019808e317`
- 构建输入为 Auth 父 HEAD `91a6568e6e5f64d52a9322a7890290b45d71808e` 加本轮改动。源码指纹为 `b7b00930da6c6b53eaa779b8bdaa35173c0a1718665bfb6bb36e32f84bb0a11d`，构建前后相等。镜像二进制包含本人读取入口和脚本权限开关。
