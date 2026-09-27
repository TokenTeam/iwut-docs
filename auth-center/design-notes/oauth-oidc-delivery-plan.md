# OAuth / OIDC 工作包与交付顺序

状态：`PROPOSED` — 2026-09-27；导航与实施顺序，不是业务规则的第二权威。

## 这轮确定的方向

采用 OIDC Authorization Code Flow。PUBLIC_PKCE 无 secret、强制 S256；CONFIDENTIAL_SECRET 使用后端 secret，也支持叠加 PKCE。两种方式最终取得独立的 ID Token 与 opaque access token。流程选择与代价见 [ADR-PLAT-003](../../platform/adr/ADR-PLAT-003-oidc-opaque-access-and-delegation.md)，完整端点与载体见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

用户提出的“在 Traefik 检查并注入”落实为：HTTP 请求在 Traefik ForwardAuth 阶段调用 Gateway→Auth，由 Auth 在线检查并签发内部委托 JWS，Traefik 只复制可信结果；原生 gRPC 和 gRPC-Web 延续专用前置代理。现有 SESSION→USER 身份继续使用原契约，OAuth 使用独立委托类型。

## 新用例

| UC | 工作包 | 主要前置 |
| --- | --- | --- |
| ApplicationVersion OAuth 扩展 | 在 UC-APP-002/003/004/005/007 中创建、编辑、审核并发布按 client type 分组的回调 | 已有 Version/Review/Publication |
| [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) | 管理应用 client 身份、类型、secret 轮换和停用 | Version OAuth 扩展、已有 Application/Developer 管理门禁 |
| [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md) | Auth 读取配置、验证 secret、取得当前回调/scopes 和用户运行资格 | APP018、已有 TEST/Tester/批准快照 |
| [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) | 官方登录/consent、用户 grant、一次性授权码 | APP019、平台 Session、生产 Catalog |
| [UC-AUTH-015](../use-cases/UC-AUTH-015-exchange-authorization-code.md) | 两种 client 兑换 code，签发 ID/access token | AUTH014、OIDC 签名/JWKS |
| [UC-AUTH-016](../use-cases/UC-AUTH-016-refresh-application-tokens.md) | 明确离线授权、refresh 旋转与重放处置 | AUTH015/018，可后置 |
| [UC-AUTH-017](../use-cases/UC-AUTH-017-get-oidc-user-info.md) | 标准 UserInfo，最小 sub/已授权邮箱 | AUTH015/018、激活邮箱事实 |
| [UC-AUTH-018](../use-cases/UC-AUTH-018-revoke-application-authorization.md) | 本人查看、部分/全部收回；应用 token 撤销 | grant/token 模型、平台 Session |
| [UC-AUTH-019](../use-cases/UC-AUTH-019-issue-delegation-context.md) | 在线 token 检查与可信委托签发 | AUTH015/018、APP019、资源策略 |
| [UC-GW-002](../../gateway/use-cases/UC-GW-002-authenticate-oauth-and-forward.md) | 标准 OIDC 路由、OAuth 入口与三协议转发 | AUTH019、资源服务委托验证器 |

新列出的 OAuth/OIDC UC 均为 PROPOSED / NOT_STARTED；ApplicationVersion OAuth 扩展修改了既有 ACCEPTED UC 的设计，但实现同样尚未开始。既有完成记录不覆盖这些扩展。接受工作包时必须把依赖的跨系统契约一同纳入，避免各自猜测消息与身份格式。

## App Center 需要交付的接口

[App 提供方契约](../../platform/contracts/app-oauth-client-v1.md) 分成两类：

- 当前应用管理员：Create/Get/List、SetOAuthClientStatus、RotateOAuthClientSecret。redirect URI 在 ApplicationVersion 中管理；secret 仅创建/轮换时返回一次，不存在读取旧 secret 的接口。
- Auth 内部：GetClientConfiguration、VerifyClientSecret、ResolveClientRuntimeConfiguration、ResolveAuthorizationContext。运行配置方法在登录前返回批准 Version 的回调/scopes；最后一项再绑定当前 TEST/Tester 资格。客户端不能提交“申请哪些就批准哪些”。

App 不保存用户 consent，不自行定义 scope 含义；Auth 不直接读 App MongoDB，也不保有可独立变更的第二份 client 注册表。

## 交付顺序

1. **配置和事实来源**：先扩展 APP002/003/004/005/007 的版本化回调，再按 APP018→APP019 交付 client 与提供方；同时落实 Auth 生产 scope 初始装载、最小授权文案和路由映射。无需先建立在线 Catalog 管理后台。
2. **可登录、可退出授权的最小闭环**：AUTH014/015/017/018 与门户一起验收。AUTH018 的 grant/family 栅栏是共享基础，应在首批 token 发放前完成，不能先上线不可撤回凭据。
3. **访问资源**：AUTH019→GW002，并交付目标服务的专用委托验签与数据授权。可先用 UserInfo 做 OIDC 互通，但通过 UserInfo 不代表业务资源已可调用。
4. **离线访问**：AUTH016 可后置；未交付时拒绝 offline_access，discovery 不宣称 refresh grant。

接口 Proto 与 HTTP annotation 是独立 API 仓库的实现产物；实施前需固定字段号、错误 reason、全部 public management 路由及生成器输入。本文已有消息语义和内部完整方法名，未把“文档设计完成”称为“立即可并行实现所有适配器”。

## 需要明确接受的取舍

- 当前 App 只有 TEST/Tester 的运行规则，因此首版 OAuth 只绑定该渠道；面向所有用户的 STABLE 接入需先设计正式发布/运行资格。
- secret 轮换、client 配置、发布或 Tester episode 变化会使旧凭据失效；以重新授权换取首版简单一致的规则。
- refresh 严格旋转，无重试宽限；客户端须串行刷新，丢响应可能需要重新授权。
- pairwise subject 按 OIDC 回调 hostname sector，同域不同 client 会相同；它不是学号分组，也不是全局 authId。
- 标准门户先支持浏览器重新登录。原生已有 Session 的无感 SSO 桥、更多回调类型、更多动态资料 scopes、公开 introspection、单点登出均不在本轮。
- [Traefik 契约](../../platform/contracts/oauth-delegation-v1.md)明确已有短期上下文及在途请求的撤销传播窗口；不承诺第三方应用会话/已取得数据同步删除。

这些是本轮具体建议，不是用户已经逐条接受的决定。后续可以调整 PROPOSED 文档后再生成 brief；已有 SESSION/身份契约保持其原有权威性。
