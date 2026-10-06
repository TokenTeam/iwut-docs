# ADR-GW-002：路由凭据载体与条件身份交换策略

状态：`ACCEPTED`

日期：2026-10-06

## 背景

[ADR-GW-001](ADR-GW-001-runtime-routing-and-protocol-adapters.md) 的首版路由 schema 用 `DIRECT | SESSION | OAUTH2` 和 `directCredential: NONE | SESSION` 表达认证。它足以覆盖首批公开/自认证接口、必须登录的用户接口和两个 Session 撤销接口，但不能无歧义表达后续已经出现的入口：

- [UC-APP-023](../../app-center/use-cases/UC-APP-023-resolve-unified-launch-target.md) 与 [UC-APP-024](../../app-center/use-cases/UC-APP-024-query-public-application-catalog.md) 允许完全匿名，也允许把已提供且有效的 Session 换成可信用户身份；
- [UC-GW-002](../use-cases/UC-GW-002-authenticate-oauth-and-forward.md) 同时需要 OAuth Bearer 在线交换、OIDC `/token`/`/revoke` 的 Basic、`/userinfo` 的 Bearer，以及门户的限定 Cookie/Session；
- 某些 Auth 接口由下游自行验证原始 Session，不能因为看见 Session 就先执行 UC-AUTH-010；
- 同一个 `DIRECT` 名称无法说明 Authorization、Cookie、专用 header 和内部身份头究竟应保留、交换还是删除。

若继续为每种组合增加 authMode，路由目录会变成不断扩张的模式枚举；若根据请求实际携带的 header 猜测策略，又会破坏 BR-GWR-001 的单一路由决定原则。

## 决定

后续路由目录把“终端可以提供什么”“Gateway 是否执行身份交换”“最终向下游注入或保留什么”拆成正交但受约束的策略。具体 YAML 字段名在实现工作包中定稿，语义必须至少覆盖下列矩阵：

| 维度 | 允许值 | 含义 |
| --- | --- | --- |
| Session 载体 | `FORBIDDEN` / `OPTIONAL` / `REQUIRED` | 是否允许或要求唯一 `x-iwut-session`；`OPTIONAL` 只放宽缺失，不放宽非法值 |
| Authorization 载体 | `FORBIDDEN` / `OIDC_BASIC` / `OAUTH_BEARER` | 只允许该路由声明的单一 scheme；不提供任意透传值 |
| Portal Cookie | `FORBIDDEN` / 精确 cookie 名白名单 | 只供明确 OIDC portal 路由，禁止把整包 Cookie 转发到应用服务 |
| 专用终端 header | 空集或精确名称白名单 | 只保留对应协议明确定义的有限字段；未知、别名和内部控制头删除或拒绝 |
| USER 身份交换 | `NEVER` / `WHEN_SESSION_PRESENT` / `REQUIRED` | 是否调用 UC-AUTH-010 并注入唯一 `x-iwut-identity` |
| OAuth 委托交换 | `NEVER` / `REQUIRED` | 是否调用 UC-AUTH-019 并注入唯一 `x-iwut-delegation` |
| 原始凭据下游去向 | `DROP` / 精确载体白名单 | 交换后默认删除；只有下游自己认证的明确路由可以保留声明载体 |

路由类别仍由静态目录决定。Proto RPC 路由继续从固定 descriptor 推导 method/path；OIDC 标准端点使用有限的 `OIDC_HTTP` 类别和精确 method/path 清单，不能成为任意无 annotation HTTP 代理。

### 合法组合

配置装载器使用有限组合校验，而不是实现通用策略语言。至少允许：

- 必须登录的平台用户路由：Session `REQUIRED`，USER 交换 `REQUIRED`，原始 Session/Authorization `DROP`；
- 可选身份公开读取：Session `OPTIONAL`，USER 交换 `WHEN_SESSION_PRESENT`，原始凭据 `DROP`；
- 下游自行验证 Session 的撤销/桥接路由：Session 按契约 `REQUIRED`，USER 交换 `NEVER`，只保留 Session；
- OAuth 资源路由：Authorization `OAUTH_BEARER`，委托交换 `REQUIRED`，原始 Bearer `DROP`；
- OIDC 标准/门户路由：只按精确端点保留 Basic、Bearer、指定 Session 或指定 Cookie，两个身份交换均为 `NEVER`；
- 真正匿名且无凭据的公开路由：所有终端凭据 `FORBIDDEN`，两个交换均为 `NEVER`。

同时启用 USER 与 OAuth 委托交换、把 SESSION 当 Bearer 备用、允许任意 Authorization scheme、把终端提供的内部 JWS 直接转发，或在未声明时保留 Cookie/header，均为非法配置并阻止启动。

### 可选不等于宽松

`OPTIONAL` 的唯一含义是“载体完全缺失时继续匿名流程”。一旦出现空白、多值、逗号合并、别名、非法形状、过期、撤销或 Auth 拒绝，Gateway 必须返回认证错误，业务 upstream 零调用；不能删除坏凭据后按匿名继续。Session 与 Authorization/Cookie 等该路由禁止的凭据同时出现时，按歧义或禁止凭据拒绝，不通过优先级猜测用户意图。

Gateway 仍不解析 USER/委托 JWS 做业务授权。它只校验签发响应的单值、大小、形状和剩余寿命并按路由写入固定内部 header；下游继续验签并执行业务规则。

### Schema 演进

现有 `routes.v1.yaml` 的语义不能在原字段下静默改变。实现本决定时应引入可机械迁移的新 schema 版本，或在严格互斥的新字段组下完成一次性迁移；同一路由不能同时使用旧 `auth.mode/directCredential` 和新矩阵。生成器、运行时与已提交 Traefik 配置必须由同一解析模型产生并做 digest/漂移检查。

HTTP ForwardAuth、原生 gRPC 和 gRPC-Web 继续共享同一已验证策略。任何组合若只能在其中一种协议正确执行，必须限制 route protocols 或在启用前补齐适配，不能声称三协议等价。

## 不采用的方案

### 增加 OPTIONAL_SESSION 等更多 authMode

模式枚举会把凭据输入、交换行为和下游保留策略绑死；OIDC 标准端点仍会需要大量特殊分支，因此不采用。

### 根据请求实际携带的凭据自动选择流程

这会让相同 method/path 因 header 不同命中不同信任路径，并产生坏凭据降级为匿名的风险，因此禁止。

### 所有 DIRECT 路由透传全部认证头

DIRECT 只表示 Gateway 不执行某类交换，不表示凭据可以无界透传。默认仍是删除，例外必须逐路由声明。

### 把可选身份校验交给 App Center

App Center 只接受可信 USER JWS，不应接触平台 Session 或每请求回调 Auth。身份交换继续位于 Gateway/Auth 边界。

## 结果

优点：

- 可以同时表达匿名、可选登录、必须登录、下游自认证和 OAuth/OIDC，而不按 header 猜模式；
- 载体保留和内部身份注入都可由配置生成器静态审计；
- UC-GW-001、UC-GW-002 与 UC-GW-003 可以共用一个路由执行模型；
- 新增协议载体时必须显式扩展有限枚举和组合测试。

代价：

- 需要升级严格路由 schema、生成器、两个 transport adapter 与测试矩阵；
- 配置校验比首版二元模式更复杂；
- OIDC_HTTP 仍需小范围专用适配，不能完全由 Proto descriptor 推导。

## 实施记录

2026-10-07，Gateway `0009947` 用 `iwut.gateway.routes/v2` 一次性替换 v1 schema，落实 Session、Authorization、USER 交换、OAuth 委托交换和原始凭据保留矩阵。HTTP 每条路由都经过 route-specific ForwardAuth；原生 gRPC 与 gRPC-Web 共用同一认证用例。禁止凭据、可选 Session、无效 Session 不降级、原始凭据清理及下游自认证 Session 例外均有单元测试和协议 E2E。

本工作包只启用 `Authorization: FORBIDDEN` 与 `oauthDelegation: NEVER` 的合法组合；配置若声明 Basic、Bearer、OAuth 委托、Portal Cookie 或专用终端 header，会在启动时失败关闭。UC-GW-002 仍为独立的 `PROPOSED / NOT_STARTED` 工作包，不能从本 ADR 已接受推导为 OAuth/OIDC 已开放。

## 关联文档

- [UC-GW-001：按路由认证并转发请求](../use-cases/UC-GW-001-authenticate-and-forward.md)
- [UC-GW-002：应用委托请求鉴权与转发](../use-cases/UC-GW-002-authenticate-oauth-and-forward.md)
- [UC-GW-003：为公开读取附加可选用户身份](../use-cases/UC-GW-003-attach-optional-user-identity.md)
- [ADR-PLAT-004：跨服务交付使用统一 API 集成基线](../../platform/adr/ADR-PLAT-004-unified-api-integration-baseline.md)
