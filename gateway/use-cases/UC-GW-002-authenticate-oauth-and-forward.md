# UC-GW-002：应用委托请求鉴权与转发

状态：`PROPOSED`

## 目标与范围

扩展 UC-GW-001 的 OAUTH2 分支，在转发前由 Auth 检查应用 access token 并注入专用委托上下文。标准 OIDC HTTP 端点采用显式 DIRECT 适配，不为每个业务路径建立独立 UC。

## 输入与输出

输入为静态目录匹配到的 HTTP/native gRPC/gRPC-Web 请求和单个 Bearer access token；输出为上游业务响应或本协议拒绝。路由清单、内部 RPC、header 与协议约束见 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md)；标准端点见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

## 主流程

1. 根据受信目录唯一匹配请求，清理伪造身份头，禁止从客户端信息选择策略或上游。
2. HTTP 在 Traefik ForwardAuth 调用 Gateway；gRPC/gRPC-Web 走现有 unary 前置代理。
3. Gateway 以自身 service 身份及 access token 调用 Auth 专用委托签发，核对响应期限和形状。
4. 仅成功时将单一委托 JWS 交给固定上游；清除原始 token/Session 等凭据。资源服务独立验签与授权。
5. 失败按协议返回，不能降级策略、重放业务 mutation 或返回登录跳转。

## 业务规则

<a id="br-gwr-006"></a>
### BR-GWR-006：显式启用与唯一认证策略

OAUTH2 只能用于路由目录明确登记并已交付委托验证器的资源方法；不能按 token 是否含句点猜 SESSION/OAUTH2。现有 SESSION/DIRECT 不变，未知路由继续拒绝。

新增 OIDC_HTTP 类型仅用于标准协议端点和官方门户明确方法；它是现有 HTTP annotation 检查的窄例外，不能给任意业务路由绕过 Proto 绑定。配置生成器必须验证精确白名单、认证模式及凭据转发策略；功能未联合验收时默认关闭。

<a id="br-gwr-007"></a>
### BR-GWR-007：在线委托签发先于转发

必须先成功调用 UC-AUTH-019，才能发送业务请求。Auth 拒绝、超时或 App 依赖故障都零业务转发；不缓存 access token 的认证结果或 JWS。路由所需 scope/audience 及双凭据传输引用 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md)，不得复用 UC010 的 USER JWS 代替。

<a id="br-gwr-008"></a>
### BR-GWR-008：外来身份清理和最小转发

清理、允许复制的认证响应头及原始凭据剥离按 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md) 的 Traefik 顺序执行。外部即使提交有效形状的 x-iwut-delegation 也必须先删除；只有本次 Auth 签发的值可进入上游。不向客户端响应内部上下文，不把 Basic secret 或平台 Session 送往资源服务。

路由固定后其 audience/upstream/method/path 不能被认证响应或用户 header 重写。资源服务只把专用委托用于明确启用的 OAuth 方法。

<a id="br-gwr-009"></a>
### BR-GWR-009：协议失败与可观测性

HTTP 采用 ForwardAuth，native gRPC 与转换后的 gRPC-Web 保留合法 status/trailer；不得因 HTTP 鉴权中间件返回 401 而破坏 gRPC 错误语义。401/403/429/503 的映射与时钟/撤销窗口见共享契约。

业务请求不自动重放；签发请求也只在本次总 deadline 内处理，首版不重试。日志只记录 routeId、内部 requestId、错误类别和耗时，不记录 Authorization/Session/cookie/JWS/secret 或用户资料。

## 验收场景

- PUBLIC/CONFIDENTIAL 签出的 access token 均可走对应已批准 scope 路由，正确传入专用上下文。
- 外来身份头、重复/别名 Authorization、错误 issuer/aud/typ、错路由/路径、ID Token 冒充全部拒绝。
- 401/403/429/503 在 HTTP/gRPC/gRPC-Web 中语义一致，所有鉴权失败均零上游调用。
- OIDC 标准表单/JSON 与 discovery 正常，不误用 Session 身份；secret 只去 Auth 标准端点。
- route policy digest 不一致、后端未安装委托验证器、未知 OAUTH2 scope 时配置不能启用。
- 真正 Traefik+Gateway+Auth+App+Mongo+资源验证器联合测试覆盖撤销传播和 header 剥离。

## 依赖与实现边界

依赖 UC-AUTH-019、UC-APP-018/019、目标资源的委托验证与业务权限；标准端点还依赖 UC014–018 和官方门户。沿用 ADR-GW-001 的 Traefik 版本与协议适配，不在本文升级版本或引入 Redis。新契约接受及实现验收前 UC-GW-001 的 OAUTH2 仍保持未启用。
