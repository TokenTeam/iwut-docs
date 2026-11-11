# UC039 与 Application search 权限交付核对

状态：`AUTH_BACKEND_PUBLISHED / CONSUMER_INTEGRATION_PENDING`。

2026-11-08 用户接受 [UC039](../use-cases/UC-AUTH-039-search-users-for-administration.md) 与 UC027/010 的搜索扩展。已合入 ACCEPTED 正文、同步 registry，并在实施前生成三个 brief。

## 实现与验证

- UC039 提供受保护的原生 gRPC 和 HTTP/JSON。完整管理员在最终 Auth 事务在线复核后，按原值 Auth ID 或规范化当前已验证邮箱精确定位。绑定与目录一致性、账号与 Developer 状态校验共用该事务。查询最多返回一项最小摘要，未知/SYSTEM/CLOSED 返回空集合，损坏数据及存储失败关闭。
- UC027 的管理和本人公开 allowlist 扩为 restore/search/suspend 三项，目标状态按精确 ID 排序。三项独立授权，与其他人员权限共用 revision 和原子审计。UC010 仅向 App audience 投影当前显式 search grant。
- 真实 Mongo 专项通过，包含非登录邮箱、已解绑地址、全部合法 Developer 状态、DISABLED/CLOSED、目录损坏、正式管理员撤权后查询拒绝，以及 search 授撤和审计失败回滚。
- 生产 Wire 专项通过，正式 HTTP/gRPC 查询、严格字段/oneof、private/no-store、未知目标完整空数组，以及同一 Session 的本人集合和新签 App 身份无→有→无。App 实际验签器接收新签身份，且 search 不授予 App Reviewer 权限。
- ProtoJSON 会忽略 oneof 的 null 值，已增加显式形状检查及回归断言，拒绝空 selector 和附带 null 的第二 selector。最终代码通过 Auth make check、普通全仓 race。
- 真实 Mongo 全仓 race 回归通过，完整仓储包 743.916 秒、首轮完整 Wire 包 181.538 秒；最终严格 JSON 输入代码的完整 Wire 包独立复验通过（295.887 秒）。文档 85 份 brief、registry、30 项工具测试和差异检查通过。

## 版本与交接

实施时 Auth 父 HEAD 为 `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f`，保留既有和本轮未提交工作。Auth API 自有分支 `auto/auth-user-search-20261108` 从 `01f2ecb633120662d9a74d0263d9aebda37b6e16` 增量提交 `bf0f17d4943b13cddf57d570c7003596be14ebd7`，仅包含 Auth Proto/生成物和 Makefile。API proto-check 及 Go 全包测试通过。

API 已与 App 增量统一至 `241d56de6f8a3f68ed91969a4239a8c9fe32baad`，Auth `91a6568e6e5f64d52a9322a7890290b45d71808e` 固定该引用。镜像及启用条件见[发布记录](UC-AUTH-038-own-read-readiness.md#发布版本2026-11-11)。Gateway 的精确 Admin 路由、Console 和 App UC051 实际目录/摘要联验由对应工作包继续；本次 Auth 验签专项不替代 App 目录业务验收。管理入口默认关闭，UC039 的独立开关为 `AUTH_MANAGED_USER_SEARCH_ENDPOINTS_ENABLED`。

实施时的本地镜像 `iwut-auth-center:search-local-uc039-bf0f17d-6e680a1e5700`，ID `sha256:78f714f26304bf5b65042b2e184b5aaa23e6f50d3a812419e48d54d86b20c9bc`。Auth 脏源码 SHA-256 为 `6e680a1e57005d31ecf4e192b19df864fc420d53a8df4346ee3ff01d15dacf7f`，与 API 分开记录；构建前后及最终验证的指纹相等。原始构建/验证记录位于本机 `/tmp/iwut-auth-uc039-search-20261108-kkxf0obj/report.json`。
