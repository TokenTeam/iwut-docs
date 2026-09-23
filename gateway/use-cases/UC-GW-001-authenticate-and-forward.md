# UC-GW-001：按路由认证并转发请求

状态：`PROPOSED`

## 目标与范围

> Gateway 根据已登记路由选择认证策略；对要求平台用户身份的请求先向 Auth 获取 Session 对应的 JWS，成功后由 Router 转发给固定目标服务。

首版一个通用 UC 覆盖所有相同转发行为；新增普通业务路由只增加配置和契约测试，不为每个接口复制一份 UC。不在 Gateway 重复实现 Developer、Reviewer、资料或应用业务授权。

这里的“内部访问”指终端访问平台自有服务。已有服务到服务 RPC 使用 service JWS，走自己的内部通道，不经本用例换用户 JWS，也不能被终端调用。

## 路由与策略

每个 Route 至少定义：稳定 routeId、外部匹配条件（HTTP method + path template，或原生 gRPC full method）、固定 targetService、目标操作/前缀映射、authMode、可保留的终端凭据载体。SESSION 另要求固定 audience。地址由 targetService 的部署表解析，客户端不能指定 upstream URL、audience 或 authMode。

| authMode | 行为 | 首版范围 |
| --- | --- | --- |
| `DIRECT` | 不先签发用户 JWS，完成头清理后交给目标接口自身认证/校验 | 启用，逐条登记自认证或确实公开的接口 |
| `SESSION` | 以本次 Session 调用 UC-AUTH-010，将取得的 JWS 写入本次请求再转发 | 启用，平台自有服务的用户入口 |
| `OAUTH2` | 使用应用获得的 OAuth2 access token，按委托授权契约处理 | 只保留策略名称，不启用任何路由 |

DIRECT 不等于整个服务匿名，也不等于跳过 Auth 本身的验证。例如 UC009 虽是 DIRECT，仍由 Auth 使用有效 Session 校验撤销权限。未来公开读取可显式采用 DIRECT，无需仅为“公开”增加第四套认证流程。

OAuth2 是授权体系，access token 不一定是 JWT。即使采用 JWT，也不能直接当作 trusted-identity-v1：必须另外定义 client、scope、resource audience、用户 consent、撤销以及是否需要内部委托身份转换。未定义前禁止配置已启用的 OAUTH2 路由，不能回退 SESSION/DIRECT 或依据 token 外形猜策略。

## 首批路由清单

以下是明确的策略分配，不宣称已生成 Gateway/HTTP 路由。Auth 首版只有原生 gRPC；HTTP 映射另由 API 契约声明，不能凭下表编造登录 URL。

| 目标服务与生成接口 | 策略 | 下游所需凭据 |
| --- | --- | --- |
| Auth AuthenticationService/BeginUserRegistration | DIRECT | 消息体中的凭据提案和关联声明 |
| Auth AuthenticationService/CompleteUserRegistration | DIRECT | 消息体中的挑战证明 |
| Auth AuthenticationService/BeginDeviceLogin | DIRECT | 消息体中的凭据定位 |
| Auth AuthenticationService/CompleteDeviceLogin | DIRECT | 消息体中的挑战证明 |
| Auth AuthenticationService/RevokeCurrentSession | DIRECT | 原始 `x-iwut-session`，允许已过期/未知的合法格式 token |
| Auth AuthenticationService/RevokeOwnCredential | DIRECT | 原始 `x-iwut-session`，由 Auth 校验当前有效性 |
| Auth UserProfileService/GetOwnProfile | SESSION | audience=`iwut-auth-center` 的 JWS |
| Auth UserProfileService/GetProfileEditingSchema | SESSION | audience=`iwut-auth-center` 的 JWS |
| Auth UserProfileService/EditOwnProfile | SESSION | audience=`iwut-auth-center` 的 JWS |
| App Application/CreateApplication | SESSION | audience=`iwut-app-center` 的 JWS |
| App ApplicationReview/DecideApplicationVersionReview | SESSION | audience=`iwut-app-center` 的 JWS |

完整 gRPC method 使用各独立 Proto 的生成常量，Auth 身份类型参考 [设备认证契约](../../platform/contracts/auth-device-session-v1.md#rpc-鉴权表)，Auth HTTP 路径引用 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md)，App HTTP 路径引用 [App API 路由](../../platform/contracts/app-center-api-routing.md)。原生 gRPC 不凭 package 前缀批量开放。其它已实现 App 用户接口逐条登记后才开放。

重设密码、邮箱登录和 UC004 Reviewer 管理入口目前尚未交付：前两类将由各自 UC 决定 DIRECT 载体，UC004 采用 SESSION；不得因为例子里提及就创建通配路由或视为可用。Auth 签发 RPC、内部状态查询、provision/管理运维接口均不在终端路由表。

## 主流程

1. Edge 接收请求，按部署路由表匹配唯一 Route；确认协议、HTTP method/路径或 gRPC method 一致。路由选择先发生，业务 upstream 尚未接到请求。
2. 删除终端伪造的身份及内部控制头，根据该 Route 提取允许的认证输入；选中的 Route 在整个请求内保持不变。
3. DIRECT 不调用签发接口。SESSION 使用 Route 的 audience、终端唯一 Session 和 Gateway 自己的服务身份调用 UC-AUTH-010；绝不携带业务请求体到签发 RPC。
4. SESSION 只有取得可信 Auth 返回的合格 JWS 才继续；写入唯一 `x-iwut-identity`，移除原始 Session 和终端 Authorization。失败则结束请求，Router 不向业务 upstream 发送请求。
5. Router 按同一 Route 转发，遵守已有前缀/Proto 映射，保留业务请求语义。下游自己验签及授权。
6. 将下游结果返回；不得泄露用于内部转发的身份凭证。

## 业务规则

<a id="br-gwr-001"></a>
### BR-GWR-001：单一路由决定认证与转发

认证模式、目标 audience、目标服务必须来自同一份已验证路由配置。首版启动装载、重启发布，不设计数据库路由管理、热更新或每路由 UC。未知路由、重叠/歧义路由、非法策略配置拒绝；不设置“剩下的都直通”兜底，不按请求是否带 Session/Authorization 猜模式。

必须用同一份解析后的 path/method 作匹配与转发，拒绝路径正规化差异、编码斜杠/反斜杠、点段等可能改变目标的歧义输入，避免认证按一个接口而 Router 命中另一个。HTTP query/body 可以传业务字段，但不能决定认证模式和 upstream。服务前缀只按共享契约剥离，不能任意重写业务路径。

<a id="br-gwr-002"></a>
### BR-GWR-002：Session 认证先于业务转发

SESSION 逐请求调用 [UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)，不缓存认证成功或 JWS。签发操作只通往配置的 Auth 内部原生 gRPC 地址，不经过公开 Router，从而不会递归要求再签发。

网关只处理认证编排；既不自行签发用户身份，也不根据 claims 判断 Reviewer/Developer 或代替后端授权。Auth 不可用时失败关闭，禁止使用上次成功的 JWS 或直接放行业务请求。首版不引入 Redis；服务连接池和配置缓存不等于认证结果缓存。

<a id="br-gwr-003"></a>
### BR-GWR-003：头部清理与凭据最小转发

所有策略都先删除客户端提供的 `x-iwut-identity`、旧 `X-Auth-*-Claim`/`X-Auth-Jwt-Type`，以及任何用于内部路由/策略/鉴权回调的控制头。禁止信任终端伪造的 X-Forwarded-* 来决定 target、audience 或 DIRECT 例外。Forwarded 元数据由受信 Edge 重新生成；认证回调仅受信 Router 可达。

Session 严格使用 [设备认证契约的载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，重复值或逗号合并值拒绝，不能从 Cookie、query、body 或 Authorization 兜底读取。SESSION 路由不接受 OAuth2/服务 Bearer 作为替代；同时提交终端 Authorization 与 Session 时按凭据歧义拒绝。客户端伪造身份头会被删除，不覆盖新签 JWS。

服务身份由 Gateway 内部 Auth client 独立生成，只发送给签发 RPC。各跳允许凭据见[签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md#请求与凭据流向)。DIRECT 仅保留目标端点明确需要的原始凭据，例如两项撤销保留 Session，其它未允许认证头删除。Gateway 不替 DIRECT 的 Auth 接口判断 token 是否已撤销，以免破坏 UC008 幂等语义。

签发成功却返回空、多值、过大、形状非法或已无剩余寿命的身份，视为上游协议故障，不以成功状态码单独放行。网关不把签发 JWS 放入终端响应头/响应体。Auth 登录原本应返回给用户的 Session 是业务响应，不得误删或记录。

<a id="br-gwr-004"></a>
### BR-GWR-004：协议与转发责任

Traefik 继续承担 Edge、Router、TLS 和 gRPC-Web 终止；Gateway 认证编排作为薄适配组件调用 Auth，Router 负责最终反向代理。架构采用 Domain/UseCase/Port/Adapter 分离，不增加用户数据库、事件总线或通用策略语言。外部 gRPC-Web 转换后的原生 gRPC 同样必须经过认证策略，不存在转换后直达业务服务的绕路。

可用 Traefik ForwardAuth 连接认证组件，但这只是适配方式，不把其默认行为当作业务契约：成功回调必须已有完整 JWS，失败不能返回会让 Router 继续请求的 2xx。由已匹配路由绑定认证组件的 policy/routeId，不采信客户端同名头；Router 与组件配置必须由同一目录生成或用契约测试验证一致。

HTTP、原生 gRPC 与 gRPC-Web 都须实测失败不会到达业务 upstream，终端能得到相应协议的认证/不可用错误；不能只测一个 HTTP 200 回调便宣称 gRPC 已交付。Auth 的原生 gRPC 不提供 HTTP JSON 转码，Traefik gRPC-Web 转换也不等于 JSON 转码；未声明 HTTP 接口的能力暂不开放 JSON 路由。

<a id="br-gwr-005"></a>
### BR-GWR-005：有界失败与不重放业务

签发 RPC 首版 timeout 默认 2 秒，可配置有限正值，并不超过剩余请求 deadline；不自动重试签发，不自动重放业务写请求，不跟随认证/业务 upstream 重定向去获取身份。客户端重试是新请求；不能把业务结果未知说成已失败且可安全重复。

路由不匹配返回 404；终端 Session 缺失/非法/失效返回 401；歧义凭据返回 400；签发依赖/网关服务身份配置故障返回 503；签发 deadline 返回 504；成功签发后的业务拒绝保留下游权限错误。细分错误使用 UC010 的 reason，不能把 Gateway 服务 JWS 错误误报为用户 Session 失效。原生 gRPC/转换链路提供相应标准状态，不泄露认证服务响应中的内部细节。

经 Gateway 转发后，现有 Auth 的来源限流看到的是 Gateway 网络对端，多个用户会共享该来源桶。首版按聚合流量显式配置 Auth 的来源限额，并保留全局限额；不能为绕过默认每来源阈值而直接相信客户端 X-Forwarded-For。逐终端来源限流及受信来源传递另行接入，不以 Redis 作为本 UC 前置依赖。

日志只记录 routeId、requestId、目标服务、结果与耗时；不记录认证头、JWS、Session、OAuth2 token、私钥或注册/登录的秘密内容。签发失败后可对客户端返回稳定 reason，不透传任意 Auth 响应头。

## 测试与验收

- route table 驱动测试覆盖首批接口，默认拒绝未知方法；不能因路径包含 login、auth 或接口新增便自动 DIRECT。
- 无 Session 的注册/登录能转发；DIRECT 撤销保留 token，已失效 token 的 UC008 仍能幂等完成；UC009 无有效 Session 被 Auth 拒绝。
- SESSION 请求恰好调用一次 Auth，拿到正确 audience JWS 后业务 upstream 才收到一次请求；跨 audience 请求被目标 verifier 拒绝。
- 伪造身份头/控制头、重复 Session、终端 Bearer 混用、路径编码歧义、错误服务前缀均无法改变路由策略。
- Auth 401/403/503、timeout、空成功响应、错误 JWS 形状均阻止业务请求；服务身份失败不能诱导用户重新登录。
- SESSION 最终 upstream 看不到 Session、OAuth2 token 或 Gateway 服务 JWS；日志及终端响应不泄露签发身份。
- 真实 Traefik + 认证组件 + Auth signer/Mongo + 后端 verifier 端到端验证，包括原生 gRPC 和 gRPC-Web 的失败路径、调用次数与路由映射。
- OAUTH2 路由启用配置被拒绝；内部服务 RPC 不可经公开路由调用；新增普通路由不新增用例代码分支。

## 交付边界

本轮仅设计并建立 `iwut-gateway-ddd` 孤儿 worktree，不将旧 Gateway 或旧 auth-forward 的实现视为模板。首个实现工作包需选定并锁定 Traefik 版本、交付薄认证适配组件和路由生成/验证、协议错误适配及真实 E2E；不是只提交一份未经运行验证的 YAML。

配置通过部署注入，不做管理后台。OAuth2 委托协议另立 UC，公开资源策略可通过明确 DIRECT 路由扩展；不会因本 UC 已有枚举而隐式开放。Auth 原生 RPC 的实现依赖为 UC-AUTH-010，业务接口按各自实现状态启用。

## 参考

- [Traefik ForwardAuth](https://doc.traefik.io/traefik/reference/routing-configuration/http/middlewares/forwardauth/)：认证回调与 Router 转发的适配机制；具体版本参数须在实现时验证。
- [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html)：OAuth2 access token 的 JWT profile；OAuth2 本身并不强制 token 是 JWT。

## 变更记录

- 2026-09-23：提出单一路由驱动的 DIRECT/SESSION 策略，OAuth2 暂不启用；复用 Auth 签发与下游本地验签，不引入 Redis。
