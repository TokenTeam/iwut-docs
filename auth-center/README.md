# Auth Center 设计

状态：`PROPOSED`

本目录保存 Auth Center bounded context 的权威业务设计。旧
`iwut-auth-center` 实现只作为历史证据，不自动成为新设计的规范或代码模板。

## 当前迭代

当前建立两个最小纵切片：

- `UC-AUTH-001`：授权的内部服务读取 Auth 权威的 Scope Catalog 完整快照。
- `UC-AUTH-002`：授权的内部服务按 Auth ID 批量读取当前 Developer 状态。

本轮不设计 Scope 管理后台、目录修改命令、Developer 状态修改命令、OAuth
consent、token 签发、用户资料投影、事件发布或整个 Auth Center 的重构。

## 权威边界

- Auth Center 拥有 Scope Catalog 的业务事实、快照与 revision 语义。
- [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 是提供方行为与 `BR-SCP-*` 的权威来源。
- [共享契约](../platform/contracts/auth-scope-catalog-v1.md) 是 Auth Center 与消费方共同遵守的线格式和 gRPC 边界。
- 可执行 Proto 进入独立 API 仓库的 `auth_center/v1/scope_catalog/`，不复制到本仓库。
- App Center 的 TTL、singleflight、revision 回退保护与 fail-closed 策略继续由 App Center 自己的 UC/ADR 拥有。
- Auth Center 拥有 `auth_principals` 中的主体类型与 Developer 状态；UC-AUTH-002
  只公开 App Center 批量暂停检查所需的最小投影。

## 文档入口

- [design-registry.md](design-registry.md)：Auth Center 已分配的 UC 与 BR。
- [open-questions.md](open-questions.md)：进入真实实现前仍需决定的问题。
- [implements/README.md](implements/README.md)：实现覆盖与交付缺口。
- [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)：读取 Scope Catalog 快照。
- [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md)：批量读取 Developer 状态。

## 状态

设计使用 `PROPOSED`、`ACCEPTED`、`DEPRECATED`、`SUPERSEDED`；实现覆盖使用
`NOT_STARTED`、`IN_PROGRESS`、`CORE_COMPLETE`、`COMPLETE`。设计状态和实现状态彼此独立。
