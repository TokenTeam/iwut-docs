# Auth Center 实现入口

状态：`ACTIVE`

## 当前实现覆盖

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | `ACCEPTED` | `IN_PROGRESS` | 独立 API Proto 与生成代码、Domain/Port/UseCase、临时硬编码 catalog adapter、Kratos 原生 gRPC transport、goforj/wire Composition Root、service JWS/固定 allowlist、未认证 provider E2E、真实 App+Auth 双服务 E2E | MongoDB 权威目录 |
| [UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | `ACCEPTED` | `COMPLETE` | 权威设计、共享契约、独立 API Proto 与生成代码、Domain/Port/UseCase、MongoDB Repository 与唯一索引、Kratos 原生 gRPC Transport、service JWS/固定 allowlist、真实 MongoDB provider E2E、App Center consumer adapter、真实 App+Auth 双服务 E2E | — |
| [UC-AUTH-003](../use-cases/UC-AUTH-003-resolve-system-principal.md) | `ACCEPTED` | `COMPLETE` | 独立 API Proto、启动时幂等 Mongo provision、purpose partial unique index、Domain/Port/UseCase、受 service identity 与 purpose allowlist 保护的原生 gRPC、App Center 延迟解析与成功缓存、provider E2E | — |
| [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) | `ACCEPTED` | `NOT_STARTED` | 权威生命周期、PLATFORM_ADMIN 与一次性 bootstrap 边界、撤销传播上界 | 管理 Proto/路由、Domain/Mongo/Transport 实现（普通 USER 和内部身份签发已具备） |
| [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) | `ACCEPTED` | `CORE_COMPLETE` | 独立 Proto、配置字段目录、Domain/Port/UseCase、Mongo 内嵌资料 CAS、严格 oneof 解码、可信用户 JWS、HTTP/JSON 与原生 gRPC、生产 Wire 与真实 Mongo E2E；注册初始化空资料 | 生产实际字段清单、既有 USER 数据迁移、Gateway 接入与客户端确认交互 |
| [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实 P-256 验证、必填关联声明、独立 Proto、原子注册、关联认证加密/HMAC、启动前离线轮换与幂等重跑、全量核验、限额、生产 Wire/Mongo/HTTP/gRPC E2E | 正式事务部署上的维护窗口验收；客户端、Gateway 独立交付 |
| [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实设备登录、严格编码、Session 在线检查、固定寿命配置、10 会话精确 LRU、有界限流、事务栅栏、HTTP/gRPC/生产 Wire/Mongo 并发与故障测试 | Gateway 的 Session-to-JWS 编排与客户端接入；物理清理暂以保留记录处理 |
| [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) | `ACCEPTED` | `COMPLETE` | token 定向幂等撤销、专用载体、精确鉴权例外、首次 revokedAt、保守保留记录、真实 Mongo 故障/未知提交测试与生产 HTTP/gRPC E2E | —（Gateway 与客户端退出编排独立交付） |
| [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) | `ACCEPTED` | `COMPLETE` | 有效 Session 授权及事务内复核、本人目标隔离、首次撤销记录、公钥归属保留、引用 Session 即时拒绝、并发登录/撤销及生产 HTTP/gRPC E2E | —（客户端编排独立交付） |
| [UC-AUTH-010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) | `ACCEPTED` | `CORE_COMPLETE` | 固定 identity RPC、双重认证、独立 RSA signer、audience 能力投影、Mongo 当前状态事务确认及无缓存、caller audience 配置、生产 Wire/gRPC/Mongo 测试、实际 App verifier 兼容验证 | Gateway 联合入口验收（UC-GW-001 独立交付） |

## 实现边界

- 不在旧 Auth Center 代码中直接追加一个临时 JSON 接口。
- 不把 App Center 测试 fixture、cache 或硬编码 Scope 列表提升为 Auth 权威数据。
- 当前 `internal/adapter/catalog` 硬编码实现只用于启动纵切和 E2E；它不是 BR-SCP-001 所指的生产权威目录，必须由 Auth 自有 MongoDB adapter 替换。
- Provider E2E 使用生产 Composition Root、真实 Kratos gRPC listener 和生成 client，不使用进程内假 Server。
- UC-AUTH-002 使用 Auth 自有 MongoDB `auth_principals` repository；测试 fixture 只能
  建立输入记录，不能替代生产 repository。
- 内部服务调用 transport 统一使用 trusted-service-identity-v1；未知 RPC、permission 或 purpose 默认拒绝。UC-AUTH-004/005 的用户入口按各自用例使用 trusted-identity-v1。
- UC-AUTH-006/007 的 Begin/Complete 是有界匿名认证入口，使用挑战证明，不以已有用户 JWS 作为前提；UC-AUTH-008 只有 token 定向撤销可以不经过普通有效 Session middleware，UC-AUTH-009 必须使用有效用户 Session。仅允许显式登记的方法，不扩大其他用户能力的匿名访问面。

## 2026-09-22 后端集成记录

- 五个工作包在独立 worktree 实现，按完成顺序 `005 → 007 → 006 → 008 → 009`
  rebase 后快进合入 `worktrees/iwut-auth-center-ddd` 的 `auth-center/v1`，没有 push。
- 独立 API 分支 `auth-scope-catalog/v1` 包含 authentication 与 user_profile 的 Proto
  和生成代码；Auth 集成提交 `565c58d` 固定 API 提交 `439942a`。协议与公开测试向量见
  [设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)。
- 生产 Wire 统一注册按完整方法名分派的鉴权：设备证明、token 定向撤销、有效 Session、
  trusted-user JWS、内部 service JWS。新增用户入口默认关闭，显式设置
  `AUTH_USER_ENDPOINTS_ENABLED=true` 并满足部署配置才启用。启动前完成事务探测、
  索引和关联密文核验/迁移；失败不监听。具体环境变量见实现仓库 README。
- 验证包括 `make check`、真实 MongoDB 单成员副本集上的全包 `-race`，以及生产 Wire
  端到端注册、资料编辑、登录、两类撤销、停机轮换和仅当前密钥重启后的关联复用。
  本地运行不代替正式服务器的停机维护窗口验收。
- `COMPLETE` 指对应后端工作包，不表示外部客户端已经可用。已有 USER fixture/历史记录
  没有被静默补全资料；生产资料字段清单未自行确定。撤销和完成记录暂时保守保留，
  后续物理清理必须另行确定审计窗口且不能释放凭据公钥唯一归属。

## 2026-09-23 HTTP 接入

UC005–009 的九个用户方法增加 Proto HTTP annotation 与生成客户端；生产 Wire 同时启动
HTTP/gRPC，复用相同服务与鉴权分派。HTTP 额外验证标准 ProtoJSON、请求体上限及错误状态映射，
Session 撤销与来源限流支持 HTTP transport。路由绑定见 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md)。
内部服务查询及 UC010 签发仍仅通过 gRPC 提供，Gateway 路由独立交付。

UC010 后端实现提交为 `592eca6`，接口命名修正为 `834a801`，对应 API `fb68445`。
实际 App verifier 在有效时间内接受普通/有能力的 App audience token，并拒绝 Auth audience；
此前临时 fixture 的失败由过期引起，未修改生产验签逻辑。HTTP 接入不改变其内部 gRPC 边界。

HTTP 集成提交：Auth `afe227a`，API `5a6d439`。`make check`、`make test-race`、
`make test-mongo` 及真实 MongoDB 上的全包 `-race` 均通过；测试容器已清理，提交未 push。
