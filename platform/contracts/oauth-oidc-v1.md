# OAuth 与 OIDC 接入协议 v1

状态：`PROPOSED` — 2026-09-27；设计输入，不代表服务已启用或已通过 OIDC 认证。

## 范围与职责

提供 Authorization Code Flow，用 OIDC ID Token 表达应用登录结果，用独立的 opaque access token 表达委托访问。Auth 拥有登录、consent、grant 和 token；App 拥有 client 身份/secret，以及 ApplicationVersion 中受审核的 redirect URI 和 scopes；Traefik/Gateway 执行入口鉴权，资源服务执行业务授权。

相关业务规则由 [UC-AUTH-014](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md) 至 [019](../../auth-center/use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) 至 [021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md) 拥有。跨服务 App 接口见 [App OAuth Client v1](app-oauth-client-v1.md)，入口和下游身份见 [OAuth 委托上下文 v1](oauth-delegation-v1.md)。

## 客户端配置

| 配置 | 使用场景 | token endpoint 认证 | PKCE |
| --- | --- | --- | --- |
| `PUBLIC_PKCE` | 原生客户端、浏览器应用，不能保守 secret | `none`，表单必须含 client_id | 必须 S256 |
| `CONFIDENTIAL_SECRET` | 能保守 secret 的应用后端 | `client_secret_basic` | 支持且建议叠加；一旦授权请求提交 challenge，兑换必须验证 |

两者都是授权码流程；client secret 认证应用后端，PKCE 绑定本次发起者与兑换者。不是 `client_credentials` 登录用户，也不支持 implicit/password grant。不支持 `client_secret_post`、`plain` PKCE、URL 中的 secret；多个认证来源或重复单值参数直接拒绝。Basic 按 RFC 6749 §2.3.1 编码。

PUBLIC client 不能提交 secret 冒充 confidential；CONFIDENTIAL client 不能省略 secret 降级为 public。无 PKCE 的 confidential OIDC 客户端必须依照下述 nonce 检查，在验证 ID Token 前不得建立应用会话或使用返回的 token。

每个 Application 每渠道（TEST/GREY/STABLE）分别登记稳定 PUBLIC/CONFIDENTIAL clientId 和 confidential secret；clientId 固定 channel，不绑定 RPC major、Version 或 hostname。不同渠道不得互用 client、grant、code、access/refresh token；App Center 已交付 TEST/STABLE，并由 UC-APP-021 接受 GREY 运行资格与接入语义。redirect URI 不保存在 client registration 中，而在当前批准并发布的 ApplicationVersion 中以 `pkceRedirectUris/confidentialRedirectUris` 表达。切换 Version 可以改变完整 URI，包括 hostname，而不重建 clientId。PUBLIC 与 CONFIDENTIAL 可以同时受支持，但使用两个 clientId，分别执行各自不可降级的安全规则。

## 公网端点与响应

部署固定 HTTPS issuer，例如 `https://auth.example.org/auth-center/oidc`。issuer、端点和签发内容都来自受信配置，不能从请求 Host/Forwarded 推导。

| 相对 issuer 的路径 | 方法 | 入口策略与用途 |
| --- | --- | --- |
| `/.well-known/openid-configuration` | GET | DIRECT；discovery |
| `/jwks` | GET | DIRECT；仅 OIDC 公钥 |
| `/authorize` | GET、POST | DIRECT；Auth 自行校验参数及官方登录门户会话 |
| `/token` | POST | DIRECT；Auth 自行校验 client/code/verifier 或 refresh token |
| `/userinfo` | GET、POST | DIRECT；Auth 自行在线校验 access token，不使用 Session |
| `/revoke` | POST | DIRECT；Auth 自行校验 client 与待撤销 token |

上述 DIRECT 不等于无鉴权，只是不经过 Session→用户 JWS 的转换。标准端点属于 `OIDC_HTTP`，显式加入 Gateway 路由 schema；不能假造 HTTP annotation 或套用 Kratos ProtoJSON envelope。POST authorize/token/revoke 使用 `application/x-www-form-urlencoded`；UserInfo 的 token 仅接受 `Authorization: Bearer …`。不支持 query/body 传 access token。Discovery/JWKS 可公开缓存，其余响应 `Cache-Control: no-store`、`Pragma: no-cache`。

成功兑换示例（示例值不是可用凭据）：

```json
{
  "token_type": "Bearer",
  "access_token": "<opaque random token>",
  "expires_in": 900,
  "id_token": "<signed JWT, different from access_token>",
  "scope": "openid email"
}
```

只有按 UC-AUTH-016 获得离线授权时才增加 `refresh_token`。刷新响应保留 access_token/token_type/expires_in/scope/refresh_token，首版不重新签发 ID Token。

Discovery 必须准确声明 issuer、authorization_endpoint、token_endpoint、userinfo_endpoint、jwks_uri、revocation_endpoint；`response_types_supported=[code]`、`grant_types_supported=[authorization_code,refresh_token]`、`subject_types_supported=[pairwise]`、`id_token_signing_alg_values_supported=[RS256]`、`token_endpoint_auth_methods_supported=[none,client_secret_basic]`、`code_challenge_methods_supported=[S256]`。`response_modes_supported=[query]`、`authorization_response_iss_parameter_supported=true`；revocation 同样支持 none/basic。scopes_supported 仅列出实际装载、enabled=true 且已实现的 scope；不宣称动态注册、logout、introspection 或 JWT access token profile 已实现。

## Scope 启用与兼容投影

Scope 单一启用状态与 requestable 投影唯一由 [UC-AUTH-001 / BR-SCP-004](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 定义；OAuth 当前目录许可集合 C 及授权/恢复边界见 [UC-AUTH-014 / BR-OAU-001、002](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md#br-oau-001)。本协议不增加 requestable 与 runtimeEnabled 两个独立开关。

App 继续使用已有 requestable 字段进行版本管理检查；Auth 的 authorize、code 兑换、refresh、UserInfo 和委托签发分别遵循 UC014–019 的当前目录检查。停用不会调用用户撤销用例或抹掉历史同意。目录故障使用依赖错误，Discovery 缓存或 App 旧快照不改变运行判断。

## 授权请求与登录门户

必填 `response_type=code`、client_id、精确 redirect_uri、含 `openid` 的 scope、state、nonce，以及产品扩展参数 `iwut_channel=TEST|GREY|STABLE`、正整数 `iwut_rpc_api_major`；PUBLIC 额外必填 code_challenge/code_challenge_method。channel 必须精确等于 client 登记渠道；major 只选择该渠道 App Center 的权威 Publication，不能覆盖 Version、回调或 scope。两者绑定到 code/token/family，后续资源请求、UserInfo 或 refresh 不接受改选。客户端每次新建至少 32 随机字节的 state、nonce；服务端接受 43–128 字符的 base64url 值，不把 nonce 当用户身份。PKCE verifier 为 RFC 7636 规定的 43–128 个 unreserved ASCII 字符；challenge 为 SHA-256 后无 padding 的 base64url，固定 43 字符。

Auth 在建立登录 interaction 前以 clientId、iwut_channel 和 iwut_rpc_api_major 调用 App 的 `ResolveClientRuntimeConfiguration`，从 exact-major 当前渠道 Publication 的批准 Version snapshot 取得 effective redirect URIs 和 scopes，并从当前已批准 ProfileRevision 取得展示资料，再先精确匹配 redirect_uri。runtime tuple 包含 versionId、publicationRevision、profileRevisionId 和 adminAuthId；用户登录后以该 tuple 调用 `ResolveAuthorizationContext`，确认和 code 兑换时继续重查。任何 tuple 变化都不能把旧回调或展示资料与新 scopes、Profile、Tester 或 Grey cohort 资格拼接。

Grant 业务主键为 `(authId, applicationId, channel)`，具体约束由 [BR-OAU-002](../../auth-center/use-cases/UC-AUTH-014-authorize-application.md#br-oau-002) 定义。同应用同渠道的 PUBLIC/CONFIDENTIAL client 及各 major 共享历史同意；grantId 是稳定引用 ID，不以 client 或 Version 为授权身份。code、access/refresh token 和 family 仍各自绑定 client，不能跨 client 兑换、刷新或撤销；共享同意不省略各自的 client authentication/PKCE、当前版本资格或 offline_access 确认。历史同意集合 G 不因当前版本 scope 减少而删减；只有本次请求超出 G 的部分需要新增同意。实际访问使用 token、G、当前批准版本及 Auth 当前目录许可集合 C 的交集，UC014/016/018/019 定义唯一业务规则。revision 用于 OCC/审计，用户撤回递增共享 grant 的独立 revocationEpoch，对同应用同渠道所有 client 的旧凭据生效；新增同意不使旧 token 失效，也不自动扩大旧 token。授权交互和 code 始终绑定其创建时的精确 runtime tuple 与 redirect URI；旧 code 不能因 grant 可延续而兑换到新 Version 的回调。secret 轮换只影响之后的 confidential client authentication，不单独撤销 grant、access token 或 refresh family。

支持 `prompt=none|login|consent`（首版单值）、非负整数 max_age。申请 offline_access 必须 prompt=consent 并实际确认，缺失时返回 invalid_request，不静默授予离线访问。无 prompt 时可复用尚有效的平台登录与既有 grant；none 不允许显示 UI，缺登录/新权限分别返回 login_required/consent_required。login/max_age 要求重新走 UC007/012 的认证，不能靠刷新门户 cookie 伪造 auth_time。nonce 写入最终 ID Token，state 原样返回。重新认证不得复用进入 prompt=login 前的同一 Session；auth_time 取 Auth 记录的实际认证时间，不接受浏览器上报。

官方 Auth 登录/consent 门户是交付的一部分；下述 /portal 路径也相对 issuer，不是站点根目录。浏览器先走既有注册/登录能力，取得平台 Session 后，在同源 `POST /portal/session` 用 `x-iwut-session` 建立 `__Host-iwut-portal` cookie：值为原 Session，Secure、HttpOnly、Path=/、SameSite=Lax，寿命不长于 Session；Auth 仍逐次在线验证。该桥接只接受配置的官方 Origin、JSON 和自定义 header，禁止跨域 CORS。cookie 只在 Auth 专用主机使用，代理不能传给应用。

门户确认使用同源 `POST /portal/interactions/{interactionId}/confirm`，含绑定 Session/interaction 的服务端随机 CSRF token、用户选择的 optional scopes 与同意/拒绝决定。Auth 重新检查 Session 归属及 interaction；请求体不接受可覆盖的 authId/client/redirect/scope 定义。禁止第三方 iframe 嵌入（CSP frame-ancestors 'none'），页面 Referrer-Policy 为 no-referrer，不加载第三方统计脚本。交互标识本身不是用户授权凭据。

原生应用使用系统浏览器和已登记的 HTTPS app/universal link 回调；前端 verifier/state/nonce 只保存在发起端。首版不设计 custom scheme、loopback 回调或把原生平台 Session 放入浏览器 URL 的 SSO 桥。官方宿主已有 Session 的无感浏览器迁移另行交付；允许在门户重新认证。

成功通过 303 跳回精确登记的 redirect_uri，仅附加 code、state、iss；客户端核对 iss 与发起时保存的 issuer。错误只有在 client 与 redirect_uri 已通过校验后才允许回跳；恶意/未知回调留在 Auth 本地报错。回调登记禁止占用 code/state/iss/error 等响应参数。应用处理一次回调后清除 URL 中的 code，不在日志或 Referer 中传播。

## 凭据与身份格式

授权码、access token、refresh token 分别由 CSPRNG 产生 32 字节，base64url 无 padding；用途隔离的 SHA-256 摘要建索引，原值只在成功响应中出现。Session、三类 OAuth 凭据即使形状相同也只能查各自的存储，禁止自动回退。数据库 TTL 清理不代替 expiresAt 检查。

| 对象 | 首版有效期 | 消费方 |
| --- | --- | --- |
| 授权交互 | 10 分钟 | 官方门户 |
| 授权码 | 90 秒，一次性 | token endpoint |
| access token | 15 分钟，仍逐次在线查授权 | UserInfo / Gateway |
| ID Token | 5 分钟 | 该 client 的登录处理 |
| refresh family | 30 天未成功刷新失效；自首次签发起最长 180 天 | token endpoint；滑动闲置期限＋固定绝对上限 |

上述天数按 24 小时计算。refresh 的滑动更新、到期边界和 access token 剩余寿命截断规则唯一由 [UC-AUTH-016 / BR-OAU-010](../../auth-center/use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-010) 定义；轮换改变 token 值，续期只移动闲置截止时间，不重置整条链的绝对上限。

ID Token 使用独立 OIDC RSA 签名密钥与 JWKS（RS256，RSA 至少 2048 bit）。header 为 `alg=RS256,typ=JWT,kid=<configured key>`；claims 为 iss、sub、单值 aud=client_id、iat、exp、auth_time、nonce、at_hash。at_hash 按 OIDC RS256 的 SHA-256 左半摘要规则，从实际 access token 计算。不包含平台 Session、内部 authId、学生关联值、developer/reviewer 权限或全量资料。

client 必须用预先信任 issuer 的 discovery/JWKS 验签，检查算法、iss、aud、exp、nonce、at_hash；ID Token 的时钟容差最多 30 秒，max_age 请求还须检查 auth_time；未知 kid 只允许对固定 JWKS 地址进行有界刷新，不访问 JWT 提供的 URL。ID Token 不作为 API Bearer token；取得后 client 可自行建立应用会话，其寿命由应用管理。OIDC 签名密钥退役前保留公钥至少覆盖已签 token 的有效期、容许时钟差和 JWKS 缓存期限。

pairwise sub 的业务所有权和持久化由 [BR-OAU-021](../../auth-center/use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021) 定义：一个 Application 一个稳定 sector，所有 channel/type/major/Version 共用。Auth 从 App 验证 clientId→applicationId 后创建映射；App 不保存 sector/sub，用户和开发者不能自选其他应用的 sector。同一 sector 下 PUBLIC/CONFIDENTIAL 的 sub 相同，但 ID Token 的 aud 仍分别为各自 clientId，不能跨 client 使用 ID Token 登录。

## 标准 sector 注册与回调清单

Auth 配置专用稳定 HTTPS 域名后缀 `sectors.<platform-domain>`，为每个应用生成随机 UUID sectorId，并保存完整 URI，例如 `https://<sectorId>.sectors.example.org/redirect-uris.json`。**URI 的 hostname 才是标准 Sector Identifier**；不同 Application 必须不同 hostname，不能只靠同一 host 下不同路径实现隔离。所有该应用的 client 注册元数据使用同一个 sector_identifier_uri，按 `(authId, sectorId)` 的持久映射生成 sub。已分配的 host/URI 不随版本或环境密钥变化；需要稳定 DNS、TLS 和备份，不能临时重建。

这是服务端受控的静态注册，不要求公开动态 client 注册接口。sector_identifier_uri 为 Auth 生成的只读元数据，客户端不需要获取 sector 才能登录；App 只提供 applicationId/client 归属和 [GetApplicationPublishedRedirects](app-oauth-client-v1.md#sector-的只读配置来源) 的批准回调事实，不保存或更新 sector。

标准 URI 仅 GET，成功直接返回 `application/json` 的字符串数组，不加 envelope。数组为该 Application 当前已启用渠道、已发布 major、两种 type 的批准回调去重排序并集；它是注册描述，不是实际授权回调白名单。每次 authorize/code 兑换仍只允许选中 client/channel/major 的精确回调，不允许因 URI 清单含有别的渠道就跨渠道跳转。

Auth 为运行配置准备/更新静态 OIDC 注册元数据时，确认本 client 生效的所有 redirect_uris 均包含在同一有效快照的 JSON 清单中；hostname 迁移或新增 major 回调时重新确认。App 仍是唯一配置权威，Auth 不维护可独立修改的回调副本。验证可直接消费生成 JSON 的同一受信快照，不要求 Auth 经公网请求自己；对外端点必须与该 JSON 语义一致。版本并发变化按 provider 的 entries/version 对照规则重读或失败关闭，不使用陈旧白名单。

清单公开仅包含回调 URI，不含 scopes、client secret、用户、学校关联或 token；URI 的 query 本就不得嵌入秘密。已分配 sector 暂无发布回调可返回空数组；未知 sector 404，App 故障或快照过期 503，不能返回旧值或假空数组。响应 no-store。清单读取不创建新 sector，不接受任意外部 URL，也不能用于 SSRF 代理。

跨域回调使用同一个稳定 sector URI，其清单只随批准发布事实更新，用户 sub 不变。认证套件用于验证此已明确的 sector/注册契约，不再把是否补 sector 元数据留作实现时决定。标准依据见 [OIDC Core §8.1](https://openid.net/specs/openid-connect-core-1_0.html#PairwiseAlg) 和 [Registration §5](https://openid.net/specs/openid-connect-registration-1_0.html#SectorIdentifierValidation)。

## 错误、CORS 与限额

协议端点返回 OAuth/OIDC JSON error，不包装业务 envelope。无效 client 统一 invalid_client（Basic 失败 HTTP 401 并带 WWW-Authenticate）；失效 code/verifier/refresh 统一 invalid_grant（400）；非法参数 invalid_request，越界 scope invalid_scope。不要向攻击者区分 secret、用户、grant 是否存在。依赖故障返回 503 与 temporarily_unavailable，不当成用户拒绝或已撤销。

UserInfo 无效 token 返回 401 Bearer invalid_token；scope 不够返回 403 insufficient_scope。API 不返回登录 302。revocation 已失效/未知/不属于调用 client 的 token 统一 200；不支持的 token 类型用 unsupported_token_type。

PUBLIC token/UserInfo/revoke 的浏览器 CORS 只允许当前批准并发布 Version 中 PUBLIC_PKCE effective callbacks 对应的 HTTPS origin（无 cookie credentials），缺 Origin 的原生调用仍按协议认证；preflight 无 token 时仅根据当前 effective public origins 联集返回允许的方法/headers，实际请求仍按认证后的 client 再匹配 Origin；验证 preflight 不授予访问权限。CONFIDENTIAL token/revoke 不启用跨域浏览器访问。授权端点仅允许顶层导航，不提供跨域 fetch 登录。

请求体最大 16 KiB、scope 最多 32 项、单项最多 128 ASCII 字符；单值参数重复、未知 grant/response_type 均拒绝。默认每 IP 120 次/分钟、每 client 300 次/分钟、每登录用户 30 次授权确认/分钟，可部署调小；429 携 Retry-After。code、token、secret、verifier、cookie、签名上下文、邮件及用户资料不得进入访问日志、trace、metrics 标签或审计原文。

## 交付依赖与验收

1. App 先扩展 UC-APP-002/003/004/005 的 Version 依附 oauthRedirects 创建、编辑、审核与策略，再由 UC-APP-018 提供 Application＋channel 级稳定 identity/credential，UC-APP-007/019 负责发布检查与运行资格快照。
2. Auth 实现 UC-AUTH-014/015/017/018/019，门户与 Gateway 同步交付；UC-AUTH-016 是独立离线授权工作包，未启用时 discovery 必须去掉 refresh_token，拒绝 offline_access，不能部分宣称支持。
3. 初版最小生产 scope 装载 `openid`、`email`、`offline_access`：Auth 维护稳定语义/用户可读说明/映射；App 版本仍须声明并通过原有审核。其他业务 scope 必须有已交付资源服务、scope→audience→route 映射；不接受开发 fixture。生产 Catalog 装载能力是实现依赖，不需要先做在线 Catalog 管理 UC。
4. Gateway OAUTH2、OIDC_HTTP 与资源服务委托验证通过真实三方联合测试后显式启用。当前 ACTIVE 契约继续有效，本文不使旧实现自动具备新能力。

验收至少覆盖两种 client、confidential+PKCE、code/refresh 重放、nonce/state 错配、同一 clientId 的 Version/hostname/major 回调切换与未登记回调、登录前后 runtime tuple 变化、scope 越权、跨 major 历史授权保留、渠道授权隔离、仅新增 scope 重新 consent、同应用所有渠道/type 的 sub 一致及不同应用隔离、secret 轮换不撤销 grant/既有 token、App 停用、UserInfo 最小披露、HTTP/原生 gRPC/gRPC-Web，以及依赖故障时不转发。启用前还需实际 OIDC 客户端库互通测试；未通过认证不得宣称通过 OpenID Certification。

## 标准依据

[OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html) 定义认证结果、ID Token 校验与 pairwise sector；[OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html) 定义元数据。[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.1.1) 要求 public client 使用 PKCE，建议 confidential client 也使用；[RFC 7636](https://www.rfc-editor.org/rfc/rfc7636.html) 固定 verifier/challenge 编码。[RFC 9207](https://www.rfc-editor.org/rfc/rfc9207.html) 定义授权响应中的 issuer 标识。[RFC 6749](https://www.rfc-editor.org/rfc/rfc6749.html)、[RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html) 分别约束 client 认证与撤销端点。本文的期限、权限集合和发布资格是 iWUT 的产品决定。
