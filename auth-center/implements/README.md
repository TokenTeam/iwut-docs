# Auth Center 实现入口

状态：`ACTIVE`

## 当前实现覆盖

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | `ACCEPTED` | `IN_PROGRESS` | 独立 API Proto 与生成代码、Domain/Port/UseCase、临时硬编码 catalog adapter、Kratos 原生 gRPC transport、goforj/wire Composition Root、service JWS/固定 allowlist、未认证 provider E2E、真实 App+Auth 双服务 E2E | MongoDB 权威目录 |
| [UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | `ACCEPTED` | `COMPLETE` | 权威设计、共享契约、独立 API Proto 与生成代码、Domain/Port/UseCase、MongoDB Repository 与唯一索引、Kratos 原生 gRPC Transport、service JWS/固定 allowlist、真实 MongoDB provider E2E、App Center consumer adapter、真实 App+Auth 双服务 E2E | — |
| [UC-AUTH-003](../use-cases/UC-AUTH-003-resolve-system-principal.md) | `ACCEPTED` | `COMPLETE` | 独立 API Proto、启动时幂等 Mongo provision、purpose partial unique index、Domain/Port/UseCase、受 service identity 与 purpose allowlist 保护的原生 gRPC、App Center 延迟解析与成功缓存、provider E2E | — |
| [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) | `ACCEPTED` | `NOT_STARTED` | 权威生命周期、PLATFORM_ADMIN 与一次性 bootstrap 边界、撤销传播上界 | 普通 USER provision、Auth 用户身份签发、管理 Proto/路由、Domain/Mongo/Transport 实现 |
| [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) | `ACCEPTED` | `NOT_STARTED` | 编辑 UC/BR、本人资料与字段 schema 查询契约、主体内嵌资料及脚本生成 brief | 实际字段目录、USER 初始化/迁移、用户认证/Gateway 入口、Proto、Domain/Mongo/Transport、客户端确认交互与 E2E |
| [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md) | `ACCEPTED` | `NOT_STARTED` | 创建 USER、设备证明、必填学生关联、原子注册及已接受共享协议及[brief](../briefs/UC-AUTH-006.md) | 真实验证器、Proto、运行限额、Mongo 事务/离线迁移、原生 gRPC 与 E2E；客户端和 Gateway 独立交付 |
| [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) | `ACCEPTED` | `NOT_STARTED` | 设备登录、Session 检查、10 会话 LRU、Session 配置及共享协议及[brief](../briefs/UC-AUTH-007.md) | 验证器、并发栅栏、Proto、Mongo/Transport 与 E2E；客户端及 Gateway 身份签发独立交付 |
| [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) | `ACCEPTED` | `NOT_STARTED` | token 定向幂等撤销、载体及精确鉴权例外及[brief](../briefs/UC-AUTH-008.md) | Mongo 条件更新、Proto/Transport、保留策略与 E2E |
| [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) | `ACCEPTED` | `NOT_STARTED` | 本人凭据撤销、有效 Session 授权及失效传播及[brief](../briefs/UC-AUTH-009.md) | 凭据状态/审计存储、Proto/Transport 与 E2E；客户端编排独立交付 |

## 实现边界

- 不在旧 Auth Center 代码中直接追加一个临时 JSON 接口。
- 不把 App Center 测试 fixture、cache 或硬编码 Scope 列表提升为 Auth 权威数据。
- 当前 `internal/adapter/catalog` 硬编码实现只用于启动纵切和 E2E；它不是 BR-SCP-001 所指的生产权威目录，必须由 Auth 自有 MongoDB adapter 替换。
- Provider E2E 使用生产 Composition Root、真实 Kratos gRPC listener 和生成 client，不使用进程内假 Server。
- UC-AUTH-002 使用 Auth 自有 MongoDB `auth_principals` repository；测试 fixture 只能
  建立输入记录，不能替代生产 repository。
- 内部服务调用 transport 统一使用 trusted-service-identity-v1；未知 RPC、permission 或 purpose 默认拒绝。UC-AUTH-004/005 的用户入口按各自用例使用 trusted-identity-v1。
- UC-AUTH-006/007 的 Begin/Complete 是有界匿名认证入口，使用挑战证明，不以已有用户 JWS 作为前提；UC-AUTH-008 只有 token 定向撤销可以不经过普通有效 Session middleware，UC-AUTH-009 必须使用有效用户 Session。仅允许显式登记的方法，不扩大其他用户能力的匿名访问面。
