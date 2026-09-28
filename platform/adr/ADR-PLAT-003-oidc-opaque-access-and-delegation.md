# ADR-PLAT-003：OIDC、在线访问凭据与专用委托上下文

状态：`PROPOSED` — 2026-09-27。

## 背景

平台已有服务端 Session、可信 USER JWS、应用版本 scope 声明与 TEST 发布。现在需要第三方标准登录、用户 scope 授权/收回，并在 Traefik 转发前建立可信调用上下文。用户要求支持 public PKCE 与后端 client secret，暂不引入 Redis，也不把低频 Catalog 管理后台作为首项工作。

## 决定

建议用 OIDC code flow 表达登录：ID Token 面向应用，opaque access token 面向资源，两者分离。public client 强制 PKCE，confidential client 强制 secret 并可叠加 PKCE。具体格式与期限唯一由 [OAuth/OIDC v1](../contracts/oauth-oidc-v1.md) 定义。

OAuth client 配置及 secret 属于 App，按 Application＋channel/type 隔离；用户 grant 和 token 属于 Auth；grant 按 `(authId, applicationId, channel)` 共享历史同意，覆盖同渠道两类 client 及各 major，token 仍各自绑定 client。sector 和 sub 同样由 Auth 唯一管理，一个 Application 一个 sector，所有渠道/type 共享身份分组，但不共享 token 权限。Auth 经受授权内部接口获取 App 当前批准范围/运行资格，并验证 secret；不复制 App 注册表，不跨库直读。Provider 线格式见 [App OAuth Client v1](../contracts/app-oauth-client-v1.md)。

HTTP 使用 Traefik ForwardAuth→Gateway→Auth 在线验证，再由 Auth 签发专用、短期、指定 audience 的内部委托 JWS。下游资源独立验签并执行业务授权。native gRPC 保留现有前置代理，不让 HTTP 错误破坏 gRPC 状态。专用类型、header 和传播边界见 [委托上下文 v1](../contracts/oauth-delegation-v1.md)。

## 理由与代价

随机 access token 让当前 scope 交集、grant 撤回和 family 撤销统一读取服务端当前状态；版本变化不删除历史同意，不额外引入 JWT 黑名单。但每次资源访问增加 Auth/App 查询，故障时拒绝服务；这是单实例、可接受停机条件下的明确取舍，不以缓存绕过。

专用委托上下文保留现有下游本地验签模式，同时避免第三方 token 被误解释为拥有用户全部平台权限。它增加资源服务验证器及路由清单的交付工作，不能仅靠 Traefik 加一个 middleware 就完成。

secret 放 App 可以让归属、配置、禁用/轮换在一个服务内原子管理；代价是 Auth 的 confidential 兑换依赖内部 secret 验证调用。接口仅作验证，不允许其他服务读取 stored secret。

App/Auth 之间采用有界只读快照，不引入跨库事务或分布式锁。已有在途快照和委托 JWS 带来有限撤销窗口，资源请求已开始执行后不追溯回滚。

## 未采用的方案

- ID Token 和 access token 复用：登录证据与资源授权的 audience/用途不同，容易令资源接受错误凭据。
- 直接对外签通用 USER JWS：会混淆平台角色与应用受托权限。
- Traefik 独立验证长寿命 JWT 并永久放行：不满足本轮在线收回授权的目标。
- 为 client 配置新建独立服务、Redis 缓存或消息同步双写：当前交付规模下增加一致性与部署成本。

## 接受与兼容性

工作包见 [交付总览](../../auth-center/design-notes/oauth-oidc-delivery-plan.md)。本 ADR 未接受，不更改既有 ACTIVE 的 USER/service JWS、Session 签发或 Gateway 默认关闭的 OAUTH2。上线需协议互通、三方真实联测与资源授权验收。
