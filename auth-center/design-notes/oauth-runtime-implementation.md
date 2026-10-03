# OAuth UC014–019 实施与运行说明

权威业务规则位于各 UC；线格式引用 [OAuth/OIDC](../../platform/contracts/oauth-oidc-v1.md)、[App provider](../../platform/contracts/app-oauth-client-v1.md)、[delegation](../../platform/contracts/oauth-delegation-v1.md) 和 [route policy](../../platform/contracts/oauth-route-policy-v1.md)。本文记录实现接入与部署边界，不另定义授权规则。

## 接入方式

Auth 服务设置 `AUTH_CENTER_OAUTH_CONFIG_FILE` 指向本地 JSON manifest，格式见代码仓库 `configs/oauth.example.json`。未设置时保持既有服务行为。必须启用 User endpoints；OAuth 模式启动时装载 Mongo 权威 Catalog，并由原 UC001 RPC 投影同一快照。

密钥通过独立 PEM 文件装载：OIDC、delegation、Auth→App service 以及已有 USER 签名用途不得复用 key/kid。OIDC 的旧公钥可经 `oldOidcPublicKeys` 明确保留，公开 JWKS 不含其它用途密钥。App 调用默认 TLS，`appPlaintextLoopback` 只允许测试/本机数字 loopback 地址，不接受远端明文 target。

App 注册服务调用方 `iwut-auth-center`，授权五项 provider 权限；Auth signer 的 audience 固定 `iwut-app-center`。调用方私钥不传给 App。所有配置/资格在每次决策时从 App019 读取，5 秒快照有效期不等于跨库锁；无 Redis/token 验证缓存。

## Catalog 与稳定身份

初始目录使用 `configs/oauth-scopes.example.json` 的 openid/email/offline_access 文案。RESOURCE scope 不自动启用：必须有实际资源实现和 audience 映射，并显式声明 `resourceScopesReady`。offline_access 还受 refreshEnabled 控制。

启动装载以完整文档在共享 Auth 事务内更新；同值幂等，变化递增 revision，generatedAt 与 revision 同存。停用项保留；既有名称不得删除后重建或改变 kind/audience。尚无在线目录编辑后台。未配置 OAuth manifest 的旧开发模式仍使用临时硬编码目录，不能当作生产 Catalog 交付。

Grant 使用 `(authId, applicationId, channel)` 复合唯一索引；用户列表按 applicationId/channel 排序。opaque 凭据仅保存用途隔离摘要。每个 family 最多一条未消费 refresh；重放记录保留至 family 最长期限之后，TTL 只负责清理，不替代运行到期检查。

sector/subject 与 grant 长期保留。每个已使用的 client/major 记录 Auth 静态 sector 注册元数据；回调 origin 仅作为 CORS 查询线索。实际 CORS 决策始终重新查询当前 App runtime，禁止以旧 origin 记录授权。首次 authorize 会登记查询线索，`publicClientContexts` 可选地提供尚未建立交互的 public client/major 引用；它不配置可信 origin。preflight 不授予 token 使用权，confidential client 不启用跨域 token/revoke。

sector host、Mongo 备份和已签发 OIDC 的旧公钥都需跨部署保留；不得把清理临时 token 记录扩展为删除稳定 pairwise 映射。

## 门户与本人授权管理

Auth 提供同源 Session→Secure/HttpOnly cookie 桥、最小服务端 consent 页面与确认动作。登录页由 `portalLoginURL` 指定的同源官方客户端交付，调用 UC007/012 完成认证后，用 `POST <issuer>/portal/session`、JSON `{}` 与 `x-iwut-session` 建立 cookie，再返回 interaction 页面。Session 不得放入 URL。

确认端点是 `POST <issuer>/portal/interactions/{interactionId}/confirm`。HTML 表单仅含 interaction、csrf、decision，以及每个所选 scope 的重复 `scope` 字段；重复 scope 值、重复其它字段均拒绝。OIDC 标准端点继续拒绝重复单值参数。这是官方门户表单编码，不改变 OAuth token endpoint 的空格分隔 scope 格式。

UC018 的生成 Proto 同时提供 HTTP/原生 gRPC。列表/撤销只接受单个 `x-iwut-session`；Authorization、cookie、USER JWS 或 access token 不能替代。路径与错误 reason 见 UC018。

## 上线边界

`publicEnabled` 默认 false；打开还需 portalReady、gatewayReady。这些是显式交付声明，不是自动 UI 健康探测，更不表示本轮已实现 Gateway。标准 OIDC/sector HTTP 入口在关闭状态下返回 404。

UC019 原生内部 gRPC 使用独立服务权限和 route/audience 注册表；未配置路由没有可签发的资源目标。非空路由还要求受信时钟监控文件，协议见 route policy。对外 OAUTH2/OIDC_HTTP 路由、真实 Traefik 三协议转发、资源服务的 delegation 验签与数据归属仍是 UC-GW-002/资源工作包。

测试通过只能证明所覆盖的 Auth/API 与真实 App provider 行为；不宣称 OpenID Certification，也不将官方登录前端、移动端 SSO、STABLE/GREY 接入、公开 introspection 或单点登出列为本轮交付。
