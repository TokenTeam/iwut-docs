# Gateway 设计标识符注册表

状态：`ACTIVE`

索引不是规则的第二权威。当前手工维护，`tools/registry.py` 仍只检查 App Center。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Gateway | `UC-GW-003` |
| Business Rule / Gateway Routing | `BR-GWR-010` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `UC-GW-001` | 按路由认证并转发请求 | `ACCEPTED` | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md) | DIRECT/SESSION 编排；OAUTH2 仅预留。首个实现工作包已 `COMPLETE`。 |
| `UC-GW-002` | 应用委托请求鉴权与转发 | `PROPOSED` | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md) | OAuth/OIDC 新设计，未实现。 |

## Business Rules

| ID | 标题 | 类型 | 权威位置 |
| --- | --- | --- | --- |
| `BR-GWR-001` | 单一路由决定认证与转发 | Routing / Boundary | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md#br-gwr-001) |
| `BR-GWR-002` | Session 认证先于业务转发 | Authentication / Ordering | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md#br-gwr-002) |
| `BR-GWR-003` | 头部清理与凭据最小转发 | Security / Boundary | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md#br-gwr-003) |
| `BR-GWR-004` | 协议与转发责任 | Architecture / Transport | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md#br-gwr-004) |
| `BR-GWR-005` | 有界失败与不重放业务 | Failure / Privacy | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md#br-gwr-005) |
| `BR-GWR-006` | 显式启用与唯一认证策略 | Authorization / Boundary | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md#br-gwr-006) |
| `BR-GWR-007` | 在线委托签发先于转发 | Authorization / Boundary | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md#br-gwr-007) |
| `BR-GWR-008` | 外来身份清理和最小转发 | Authorization / Boundary | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md#br-gwr-008) |
| `BR-GWR-009` | 协议失败与可观测性 | Authorization / Boundary | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md#br-gwr-009) |

## Architecture Decisions

| ID | 标题 | 状态 | 权威位置 |
| --- | --- | --- | --- |
| `ADR-GW-001` | Gateway 运行时、路由目录与协议适配 | `ACCEPTED` | [ADR-GW-001](adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) |
