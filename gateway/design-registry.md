# Gateway 设计标识符注册表

状态：`ACTIVE`

索引不是规则的第二权威。当前手工维护，`tools/registry.py` 仍只检查 App Center。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Gateway | `UC-GW-007` |
| Business Rule / Gateway Routing | `BR-GWR-026` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 备注 |
| --- | --- | --- | --- | --- |
| `UC-GW-001` | 按路由认证并转发请求 | `ACCEPTED` | [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md) | DIRECT/SESSION 编排；OAUTH2 仅预留。首个实现工作包已 `COMPLETE`。 |
| `UC-GW-002` | 应用委托请求鉴权与转发 | `PROPOSED` | [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md) | OAuth/OIDC 新设计，未实现。 |
| `UC-GW-003` | 为公开读取附加可选用户身份 | `ACCEPTED` | [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md) | 匿名或有效 Session→USER JWS；无效凭据不降级。本地实现已验证。 |
| `UC-GW-004` | 向 Auth 自认证入口保留可选 Session | `PROPOSED` | [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md) | 邮箱注册/绑定双模式 route；可选 Session 原样下传，不换 USER JWS。 |
| `UC-GW-005` | 转发账号注销用途隔离凭据 | `PROPOSED` | [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md) | 五条注销 route；confirmation/receipt 精确隔离，禁止通用凭据。 |
| `UC-GW-006` | 携带用户身份与应用关闭高风险证明转发 | `PROPOSED` | [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md) | Close route 同时下传 App USER JWS 与唯一 high-risk proof。 |

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
| `BR-GWR-010` | 匿名与已认证分支只由载体是否缺失决定 | Authentication / Routing | [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md#br-gwr-010) |
| `BR-GWR-011` | 已提供凭据必须失败关闭 | Authentication / Failure | [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md#br-gwr-011) |
| `BR-GWR-012` | 成功交换才允许携带可信身份转发 | Identity / Boundary | [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md#br-gwr-012) |
| `BR-GWR-013` | 三协议一致与私有响应边界 | Transport / Privacy | [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md#br-gwr-013) |
| `BR-GWR-014` | 可选 DIRECT 只由精确 Route 声明 | Routing / Boundary | [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md#br-gwr-014) |
| `BR-GWR-015` | 出现 Session 后不得匿名降级 | Authentication / Failure | [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md#br-gwr-015) |
| `BR-GWR-016` | 可选保留不产生内部身份 | Identity / Boundary | [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md#br-gwr-016) |
| `BR-GWR-017` | 三协议同一分支与单次转发 | Transport / Ordering | [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md#br-gwr-017) |
| `BR-GWR-018` | 账号注销使用封闭的精确路由集合 | Routing / Boundary | [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md#br-gwr-018) |
| `BR-GWR-019` | confirmation 与 receipt 按方法强制用途隔离 | Authentication / Boundary | [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md#br-gwr-019) |
| `BR-GWR-020` | Gateway 只校验载体，Auth 校验秘密语义 | Authentication / Boundary | [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md#br-gwr-020) |
| `BR-GWR-021` | 最小下传、三协议一致与秘密不回流 | Transport / Privacy | [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md#br-gwr-021) |
| `BR-GWR-022` | 双凭据组合只属于 Close 精确 Route | Routing / Boundary | [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md#br-gwr-022) |
| `BR-GWR-023` | 身份交换成功先于 proof 下传 | Identity / Ordering | [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md#br-gwr-023) |
| `BR-GWR-024` | proof 对 Gateway 不透明且按 Route 最小转发 | Security / Boundary | [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md#br-gwr-024) |
| `BR-GWR-025` | 高风险载体的三协议与隐私边界 | Transport / Privacy | [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md#br-gwr-025) |

## Architecture Decisions

| ID | 标题 | 状态 | 权威位置 |
| --- | --- | --- | --- |
| `ADR-GW-001` | Gateway 运行时、路由目录与协议适配 | `ACCEPTED` | [ADR-GW-001](adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) |
| `ADR-GW-002` | 路由凭据载体与条件身份交换策略 | `ACCEPTED` | [ADR-GW-002](adr/ADR-GW-002-route-credential-and-identity-policy.md) |
