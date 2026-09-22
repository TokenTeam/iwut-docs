# Auth Center 实现入口

状态：`ACTIVE`

## 当前实现覆盖

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | `PROPOSED` | `IN_PROGRESS` | 独立 API Proto 与生成代码、Domain/Port/UseCase、临时硬编码 catalog adapter、Kratos 原生 gRPC transport、goforj/wire Composition Root、真实监听器 provider E2E | 服务身份与 allowlist、MongoDB 权威目录、未认证/未授权 E2E、App Center consumer 跨服务 E2E |
| [UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | `PROPOSED` | `IN_PROGRESS` | 权威设计、共享契约、独立 API Proto 与生成代码、Domain/Port/UseCase、MongoDB Repository 与唯一索引、Kratos 原生 gRPC Transport、goforj/wire Composition Root、真实 MongoDB provider E2E | 服务身份与 allowlist、未认证/未授权 E2E、App Center consumer adapter 与跨服务 E2E |

## 实现边界

- 不在旧 Auth Center 代码中直接追加一个临时 JSON 接口。
- 不把 App Center 测试 fixture、cache 或硬编码 Scope 列表提升为 Auth 权威数据。
- 当前 `internal/adapter/catalog` 硬编码实现只用于启动纵切和 E2E；它不是 BR-SCP-001 所指的生产权威目录，必须由 Auth 自有 MongoDB adapter 替换。
- Provider E2E 使用生产 Composition Root、真实 Kratos gRPC listener 和生成 client，不使用进程内假 Server。
- UC-AUTH-002 使用 Auth 自有 MongoDB `auth_principals` repository；测试 fixture 只能
  建立输入记录，不能替代生产 repository。
- 在内部服务身份、allowlist 与权威目录闭合前，可以验证消息和 provider 链路，但不能把 UC 或真实 Auth transport 标记为完成，也不能部署暴露该端点。
