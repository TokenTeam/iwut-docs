# UC-GW-005：转发账号注销用途隔离凭据

状态：`PROPOSED`

## 目标与范围

> Gateway 为 Auth 账号注销的五个精确入口提供一条闭合的终端路由链：禁止通用 Session/JWS/OAuth 身份，只在对应方法上接收并保留设备证明正文或一种用途隔离 header，避免 confirmation token、receipt token 和其它认证材料跨用途、跨方法或混合转发。

本用例只定义 Gateway 的载体选择、清理和转发。账号注销资格、设备签名、operation 状态、App owner-exit 屏障、token 摘要、终止与清理语义全部属于 [UC-AUTH-025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md)。Gateway 不校验设备签名，不解析注销 token 的业务含义，不读取 Auth 数据库，也不把用途隔离 token 换成 USER JWS。

五条路由作为一个安全工作包交付，不能只开放 Confirm/Get 而没有对应 Begin/Prepare，或把其中任一路由退化为通用匿名/Auth 透传器。

## 路由策略

| RPC | 外部 HTTP | 必需终端载体 | 明确禁止 |
| --- | --- | --- | --- |
| `BeginAccountClosure` | `POST /auth-center/v1/account-closures:begin` | 设备定位与 requestId 在 Proto body | Session、Authorization、Cookie、注销 header |
| `PrepareAccountClosure` | `POST /auth-center/v1/account-closures:prepare` | operationId 与设备签名在 Proto body | Session、Authorization、Cookie、注销 header |
| `ConfirmAccountClosure` | `POST /auth-center/v1/account-closures:confirm` | 唯一 `x-iwut-closure-confirmation` | receipt header 与全部通用凭据 |
| `CancelAccountClosure` | `POST /auth-center/v1/account-closures:cancel` | 唯一 `x-iwut-closure-confirmation` | receipt header 与全部通用凭据 |
| `GetAccountClosure` | `POST /auth-center/v1/account-closures:get` | 唯一 `x-iwut-closure-receipt` | confirmation header 与全部通用凭据 |

所有方法的 USER 交换与 OAuth 委托交换均为 `NEVER`。普通 Proto body 按 API annotation 转发；专用 header 同时适用于 HTTP header 和 gRPC metadata。五条 route 目标支持 HTTP/JSON、原生 gRPC 与 gRPC-Web。

## 主流程

1. 以规范化 method/path 或 exact gRPC full method 唯一匹配五条 Route 之一，固定 Auth upstream，并清除外来内部身份和控制头。
2. 在转发前收集 Session、Authorization、Cookie、confirmation/receipt header 及其重复值；任何不符合该 Route 矩阵的组合都失败，Auth 业务 handler 零调用。
3. Begin/Prepare 要求两个注销 header 完全缺失；其设备定位、challenge 签名等业务字段只留在 Proto body，由 Auth 校验。
4. Confirm/Cancel 要求唯一 confirmation header 且 receipt header 缺失；Get 要求唯一 receipt header 且 confirmation header 缺失。
5. Gateway 只检查专用 token 的单值、规范无填充 Base64URL 载体形状、长度与控制字符，不计算摘要、不判断 operation 归属/期限/用途。
6. 清除所有未声明凭据，只把该 Route 允许的一种专用 header 和业务消息转发一次给 Auth。Auth 根据 UC-AUTH-025 完成权威验证。
7. 返回 Auth 响应，删除任何不应暴露的内部认证辅助 header；不缓存、不重放、不记录注销凭据。

## 业务规则

<a id="br-gwr-018"></a>
### BR-GWR-018：账号注销使用封闭的精确路由集合

账号注销只开放表中的五个 exact RPC/method/path，不允许 `/account-closures` 前缀通配、Auth package 通配或未知方法 DIRECT。每条 Route 在静态目录中声明允许的 terminal credential；同一 header 名不能由请求参数、Auth 响应或客户端 routeId 动态选择。

Begin/Prepare 的“无通用凭据”不是跳过认证：身份由 Auth 对正文中的定向设备证明建立。Confirm/Cancel/Get 的专用 token 也不是 Session、Bearer、Cookie 或 USER identity，不能被其它 Gateway 策略消费或换签。

<a id="br-gwr-019"></a>
### BR-GWR-019：confirmation 与 receipt 按方法强制用途隔离

Confirm/Cancel 只允许 `x-iwut-closure-confirmation`，Get 只允许 `x-iwut-closure-receipt`。必需 header 缺失、两种同时出现、出现在错误方法、重复、多值、逗号合并或使用 Authorization 代装都必须失败；Gateway 不按 token 外形猜用途，也不把一个 header 改名为另一个。

HTTP header 名大小写按协议视为同一逻辑键，合并后仍必须恰好一个值；gRPC metadata 同样按逻辑键统计全部值。禁止把专用凭据放入 path、query、body、Cookie 或日志作为替代载体。

<a id="br-gwr-020"></a>
### BR-GWR-020：Gateway 只校验载体，Auth 校验秘密语义

confirmation/receipt token 是 32-byte CSPRNG 值的规范无填充 Base64URL，线上载体固定 43 个 ASCII 字符。Gateway 可以在分配/转发前执行该固定形状和有界检查，以拒绝模糊或畸形输入；token 摘要、operation 绑定、期限、状态、用途与账号归属仍只能由 Auth 判断。

形状合格不代表认证成功。Gateway 不缓存 Auth 的 token 判定、不读取响应推断 token 类型、不把 Auth 的失败改成另一方法重试，也不在错误中区分未知、过期、错误用途或已消费 token。

<a id="br-gwr-021"></a>
### BR-GWR-021：最小下传、三协议一致与秘密不回流

所有五条路由都禁止 Session、Authorization、Cookie、`x-iwut-identity`、`x-iwut-delegation`、Gateway service JWS 和其它 terminal header 到达 Auth handler。Confirm/Cancel/Get 只下传各自唯一专用 header；Begin/Prepare 不下传任何认证 header。

HTTP ForwardAuth、原生 gRPC 与转换后的 gRPC-Web 对载体矩阵、错误类别和 Auth 调用次数必须一致。专用 token 不进入日志、trace、metrics、审计 payload、终端响应或认证错误；ForwardAuth 的成功响应 header 白名单不能把它回显给客户端或复制到错误响应。

## 错误语义

- 必需专用 header 缺失或载体形状非法：HTTP 401 / gRPC UNAUTHENTICATED；
- 重复/合并值、两种注销 header 混用、错误方法使用或与 Session/Authorization/Cookie 混用：HTTP 400 / gRPC INVALID_ARGUMENT；
- Auth 对设备证明或专用 token 的语义拒绝：保留 UC-AUTH-025 的稳定认证/业务错误，不披露内部原因；
- 未登记 route：HTTP 404 / gRPC UNIMPLEMENTED 对应边界；
- Auth 不可用或 deadline/cancel：保留下游/协议语义，不自动重放业务命令。

## 验收场景

- Begin/Prepare 在三协议中只转发业务消息，Session、Authorization、Cookie 或任一注销 header 都使 Auth handler 零调用。
- Confirm/Cancel 的唯一规范 confirmation token 逐字节到达 Auth；receipt token 缺失。Get 的行为反向成立。
- 缺失、空白、非 43 字符、非 Base64URL、有 padding、重复、逗号合并、双 header、错误方法 header 和 Authorization 代装全部失败关闭。
- 规范形状但未知、过期、错误 operation、错误用途或已消费 token 由真实 Auth 拒绝；Gateway 不尝试另一用途或重放。
- 客户端伪造 USER/委托身份、内部 routeId/audience、Forwarded 或 ForwardAuth 控制头不能改变 Route 或获得下传。
- 成功与失败响应、Gateway/Auth 日志、trace 和 metrics 不包含 confirmation/receipt token、设备签名或 Gateway service credential。
- 使用真实 Traefik、Gateway、Auth production composition/Mongo，对五个方法完成 HTTP/JSON、原生 gRPC、gRPC-Web 联合测试，并断言每次最多一个 Auth 业务调用。

## 依赖与实施边界

依赖 [ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md)、[UC-AUTH-025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md)、[账号归属退出协议](../../platform/contracts/account-owner-exit-v1.md) 与统一 API 的 account-closure Proto。实现需要让 v2 route schema 表达 terminal credential 的 `FORBIDDEN/REQUIRED`、精确名称、载体形状和下游保留，不得启用任意 header passthrough。

本用例接受和真实联合验收前，五条 route 保持未启用。Auth 的功能开关、HTTP listener 或后端实现完成不等于 Gateway 已提供公网注销入口；生产发布还须确认 Edge 不记录这些 header，且反向代理大小/重复值处理与 Gateway 契约一致。

## 变更记录

- 2026-10-07：建立提案；把账号注销五条终端入口作为单一安全工作包，固定 confirmation/receipt 用途隔离、通用凭据禁止、载体与语义分层及三协议秘密边界。
