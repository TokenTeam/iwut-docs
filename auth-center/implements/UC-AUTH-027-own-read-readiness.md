# UC-AUTH-027 本人运维权限读取：实现与交接

状态：`AUTH_BACKEND_PUBLISHED / CONSUMER_INTEGRATION_PENDING`。

用户明确接受 UC027/UC-CONSOLE-015 本次修订并授权实施，先更新 ACCEPTED 并脚本生成 brief，再开始 API/Auth。旧目标 Get/Manage、App 写授权和 BrowserSession 结构保持；不开生产开关，不自动 commit/push，resource-hub 保留。

## 2026-11-04 输入与变更（历史）

- Auth 基于 `bddd98f`，工作区新增本人 Domain 投影、Port/UseCase、独立 Mongo 普通 USER 在线确认和同次权限/版本读取、精确 middleware/handler/严格空请求校验、专用 JSON 显式空数组和 private/no-store。
- API 基于 App/Console 当前使用的 `2dc002e`（包含此前 `6fea3db`），本地已快进共享 API/Auth API checkout 到该既有提交，保留提交绑定审核契约；新增本人 RPC/三字段资源与官方 Go HTTP/gRPC 生成物。**新方法仍是未提交变更，不存在可消费的新固定 API revision。**
- 管理 Get/Manage 仍经过完整管理员权限与在线复核，本人只读不查邮箱/恢复配置、不调用 RequireAdministratorTx。权限数据完整校验后只公开两项 ID，不透传全量 permissions；同次 Auth 栅栏确认 accountRevision、权限集合和共享 permissionRevision。读取不写授权审计或推进权限版本。
- 本人 Get 与原管理 Get 共用已认证 actor 的有界读预算，复用原默认关闭开关；native gRPC 未知字段、HTTP body/query/替代目标拒绝。失败不返回空集合，旧 Auth audience allowlist 和 App 命令字段不变。

## 验证记录

- `make check`、`make test-race` 通过；API 两份 Go 生成物的 `proto-check` 通过。
- 新 Domain 四组合/完整管理员无隐含授权、未公开坏权限导致全读失败、正数大 int64、共享读限流、HTTP 本人主体/显式空数组/最小三字段/401/400/403/429/503/private-no-store、精确方法和空 wire 校验通过。
- 真实 Mongo 副本集专项 `TestApplicationOperationsOwnMongo*` 的最终三项 race 通过（10.162s）：无管理员初始化/邮箱/恢复前置、四组合、代际/禁用/损坏拒绝，正式管理入口授撤后的同身份新读取、与授予并发的完整快照、审计仅随四次真实变化增加。
- 首次完整真实 Wire 包 race 通过（193.423s），新增覆盖管理员初始化前普通 USER 本人读取、原 Get 查本人仍拒绝、同一已签 Auth identity 观察新 App grant、账号禁用后旧本人身份拒绝。
- 最终独立 runner 全仓真实 Mongo/race **完整通过，exit 0**：Wire 包 261.105s、Mongo 包 760.103s；输入包含已纠正断言及正式授撤/并发新增用例。不是把不同版本专项拼成全仓成功。日志 `/tmp/uc027-auth-mongo-final.log`；临时副本集容器和所有测试进程已清理。
- 最终版本再次通过 `make check`、`make test-race`、两份 API 生成物逐字节一致性与 `git diff --check`；docs 72 briefs、registry 与 30 工具测试通过。无生产启用或联合链验收声明。

首次回归启动后发现新增 repository 测试对旧无初始化管理读的预期写错：旧 repository 缺 bootstrap marker 返回 UNAVAILABLE，而非 transport 对普通 USER 的 403。本轮只纠正此测试断言，未放宽旧入口；修订后的真实 Mongo 专项已通过。该首次完整回归使用启动时的旧测试二进制，Mongo 664.057s、仅此测试失败，exit 1，日志 `/tmp/uc027-auth-mongo.log` 保留；最终独立 runner 的全仓通过不抹去这次失败。曾启动一轮复用同一临时 Mongo 的额外包复验，发现会越过原 runner 容器生命周期后即停止（143），不计入成功证据；最终轮使用独立端口/容器并自行清理。

## 当前交接（2026-11-11）

固定版本已发布：Auth `91a6568e6e5f64d52a9322a7890290b45d71808e` / API `241d56de6f8a3f68ed91969a4239a8c9fe32baad`。UC039/UC027 的后续扩展已将本人公开范围增加到三项 `restore/search/suspend`；上面实施与验证保留初版两项的历史。发布镜像、开关和通用身份依赖见[发布记录](UC-AUTH-038-own-read-readiness.md#发布版本2026-11-11)。Gateway 与 Console 依对应仓库的精确路由和联验证据记录交付，不通过旧目标 Get 探测本人权限。
