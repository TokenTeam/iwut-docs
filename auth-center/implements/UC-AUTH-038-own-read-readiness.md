# UC038 本人脚本权限发现交付核对

状态：`AUTH_BACKEND_VERIFIED / CONSUMER_INTEGRATION_PENDING`。

2026-11-10 用户明确接受本人读取修订。先将参与者、API、BR-SMP-004/005 合入 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md)，同步 registry 和路由契约，脚本生成 [brief](../briefs/UC-AUTH-038.md)，再实现 Auth/API。UC010 的五项独立 App 投影及旧 maintain 兼容延续原已接受定义。

## 实现与边界

- 新增空请求 `GetOwnScriptPermissions`，仅以可信 Auth USER 身份的 authId 和当前 accountRevision 定位本人；在既有认证事务栅栏内确认 ACTIVE、读取完整五项状态及共享正数 permissionRevision。
- 本人方法无需管理员 bundle、初始化标记、邮箱或恢复就绪。目标 Get/Manage 及旧 maintain 继续执行原管理员门禁。共用现有 actor 读限流和 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED`，默认关闭；仅旧 maintain 开关不会启用新方法。
- HTTP GET 无正文、无 query；原生 gRPC 空消息拒绝未知 wire 字段。五项状态和 false 值完整输出，成功与错误均 private, no-store。身份失效、停用、损坏或依赖失败不能变成五项 false 的成功结果。
- 无新增 grant、权限 ID、集合、索引或迁移；不改变 BrowserSession、App 业务鉴权及已签 JWS 剩余有效窗口。

## 发布版本（2026-11-11）

- GitHub 与 CNB 的 Auth `master` 都是 `91a6568e6e5f64d52a9322a7890290b45d71808e`。该提交固定 API `241d56de6f8a3f68ed91969a4239a8c9fe32baad`，共享 API GitHub `master` 和统一分支均可获取。
- [GitHub → CNB 同步](https://github.com/TokenTeam/iwut-auth-center/actions/runs/42953053443) 成功。已从 CNB 制品库核对提交标签 `91a6568e` 与 `latest` 的 manifest digest 均为 `sha256:8824836f46cdc81df000e0cd9b3a578d02af7998ac5ff47ae16c366c00a4fe69`；按 digest 拉取成功，镜像二进制包含 UC038 本人读取、UC027 本人读取和 UC039 搜索。未据此声明 Gateway/Console 联验或生产开关已启用。
- 三个接口共用 `AUTH_USER_ENDPOINTS_ENABLED=true`、`AUTH_IDENTITY_ISSUANCE_ENABLED=true`。分别启用 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED=true`、`AUTH_APPLICATION_OPERATIONS_PERMISSION_ENDPOINTS_ENABLED=true`、`AUTH_MANAGED_USER_SEARCH_ENDPOINTS_ENABLED=true`。旧 maintain 接口独立用 `AUTH_SCRIPT_MAINTAINER_PERMISSION_ENDPOINTS_ENABLED=true`。前两个本人查询不需要管理员或邮箱恢复，搜索及目标管理仍按对应 UC 复核完整管理员；授予恢复门槛不变。

## 实施时的本地镜像（历史）

API 自有分支 `auto/own-script-permissions-20261110`，从 `7651f96ceb85f11784660521b0f3c8a7c30d7d57` 新增本地提交 `241d56de6f8a3f68ed91969a4239a8c9fe32baad`，仅含 Auth Proto 与生成物。实施时该分支尚未推送；最终共享 API 见上方发布版本。

Auth 父 HEAD `8921b8354f3252a66f735e5e74489d6e62bfe749` 加本轮未提交改动。含非忽略未跟踪文件的 Auth 源码指纹 SHA-256 为 `ff994d372fff3c68d0bf031e4cd9bedf3df7dac7539a0b3678f2e60a849012db`，API 指纹单独记录在本机报告。构建前后相等，不能仅用父 HEAD 代指本轮代码。

本地镜像 `iwut-auth-center:own-script-241d56d-ff994d372fff`，ID `sha256:3908039e05223b0e739d47b2d3ff32335294230caaa82abd71da8599059f5fec`。构建与输入记录：`/tmp/iwut-auth-own-script-20261110-exa7ee17/report.json`；本记录保留身份信息，临时原始日志不承诺永久存在。

## 验证

Auth `make check`、`make test-race`，API `proto-check` 和 `go test ./...` 已通过。文档 86 份 brief、registry、30 项工具测试与差异检查通过。

新增真实 Mongo/race 专项通过（7.396 秒）：无管理员初始化且删除邮箱目录、恢复未就绪仍可读；未知主体、SYSTEM、停用、CLOSED 与失效代际拒绝；坏版本及重复权限失败；并发正式 grant 与读取只返回完整前/后快照，随后 revoke 立即可见，读取不增加授权审计。管理员目标 Get 查询本人仍拒绝非管理员。

完整生产 Wire 包回归通过（184.567 秒）。同一 Session 的正式五项逐个授予、逐个撤销中，生成的本人 HTTP/gRPC 客户端与管理员目标查询对照每个快照；旧 maintain 读写共享状态，新签 App 身份逐项变化。原始 HTTP 校验五项 false 均显式输出、共享版本为字符串、body/query 注入失败；原生 gRPC 拒绝未知字段、缺失身份和错误 audience。普通用户在管理员初始化前也能成功读取五项 false。

完整真实 Mongo/race 全仓回归通过，仓储包 634.300 秒，包含上述新增本人专项及原脚本共享 CAS、审计回滚、授撤与签发竞争测试。执行 `MONGODB_INTEGRATION_PORT=27069 ./scripts/test-mongo-integration.sh -race -timeout=20m -v`，最终退出码 0。App 实际验签器使用测试设施拉取的发布镜像 `docker.cnb.cool/tokenteam/iwut-app-center@sha256:18eacd03c1f0cd9b4841bd9b141b61c0d5dde89f6d0045f00322a056541b4027`，未修改 App 源码。

## Gateway 与 Console 交接

| 项目 | 精确要求 |
| --- | --- |
| full method | `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions` |
| Auth HTTP | `GET /v1/users/me/script-permissions` |
| Gateway HTTP | `GET /auth-center/v1/users/me/script-permissions` |
| 认证与 audience | SESSION → `iwut-auth-center` USER；请求为空，不接收 subjectAuthId |
| Console surface | ADMIN；该本人方法不要求管理或脚本 permission |
| 传输 | HTTP、原生 gRPC、gRPC-Web 按精确方法注册 typed adapter |
| 响应 | 现有 ScriptPermissions，严格消费五项完整 granted/effective 与十进制字符串版本；失败不折成零权限 |

Gateway 精确路由和 Console 消费由对应 owner 继续，本轮未改 Console 或部署生产。App 实际验签专项只证明身份与权限投影链，不替代脚本命令和查询的业务验收。
