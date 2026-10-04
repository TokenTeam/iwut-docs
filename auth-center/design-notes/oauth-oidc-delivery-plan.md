# OAuth / OIDC 工作包与交付顺序

状态：`ACTIVE` — 2026-10-03；导航与实施顺序，不是业务规则的第二权威。

## 这轮确定的方向

采用 OIDC Authorization Code Flow。PUBLIC_PKCE 无 secret、强制 S256；CONFIDENTIAL_SECRET 使用后端 secret，也支持叠加 PKCE。两种方式最终取得独立的 ID Token 与 opaque access token。流程选择与代价见 [ADR-PLAT-003](../../platform/adr/ADR-PLAT-003-oidc-opaque-access-and-delegation.md)，完整端点与载体见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

用户提出的“在 Traefik 检查并注入”落实为：HTTP 请求在 Traefik ForwardAuth 阶段调用 Gateway→Auth，由 Auth 在线检查并签发内部委托 JWS，Traefik 只复制可信结果；原生 gRPC 和 gRPC-Web 延续专用前置代理。现有 SESSION→USER 身份继续使用原契约，OAuth 使用独立委托类型。

## 新用例

| UC | 工作包 | 主要前置 |
| --- | --- | --- |
| ApplicationVersion OAuth 扩展 | 在 UC-APP-002/003/004/005/007 中创建、编辑、审核并发布依附 Version 的 pkce/confidential 回调配置 | 已有 Version/Review/Publication |
| [UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) | 管理 Application＋channel 级稳定 client identity、独立 secret credential 和停用 | 已有 Application/Developer 管理门禁；不依赖 Publication |
| [UC-APP-019](../../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md) | Auth 读取配置、验证 secret、取得当前回调/scopes 和用户运行资格 | APP018、已交付 TEST/STABLE/GREY 运行资格与批准快照 |
| [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) | 官方登录/consent、用户 grant、一次性授权码 | APP019、平台 Session、生产 Catalog |
| [UC-AUTH-015](../use-cases/UC-AUTH-015-exchange-authorization-code.md) | 两种 client 兑换 code，签发 ID/access token | AUTH014、OIDC 签名/JWKS |
| [UC-AUTH-016](../use-cases/UC-AUTH-016-refresh-application-tokens.md) | 明确离线授权、refresh 旋转与重放处置 | AUTH015/018，可后置 |
| [UC-AUTH-017](../use-cases/UC-AUTH-017-get-oidc-user-info.md) | 标准 UserInfo，最小 sub/已授权邮箱 | AUTH015/018、激活邮箱事实 |
| [UC-AUTH-018](../use-cases/UC-AUTH-018-revoke-application-authorization.md) | 本人查看、部分/全部收回；应用 token 撤销 | grant/token 模型、平台 Session |
| [UC-AUTH-019](../use-cases/UC-AUTH-019-issue-delegation-context.md) | 在线 token 检查与可信委托签发 | AUTH015/018、APP019、资源策略 |
| [UC-GW-002](../../gateway/use-cases/UC-GW-002-authenticate-oauth-and-forward.md) | 标准 OIDC 路由、OAuth 入口与三协议转发 | AUTH019、资源服务委托验证器 |

2026-10-03：App019 及其 OAuth Version 前置扩展已交付；Auth014–019 已接受且 Auth 后端实现已交付，具体验收状态见 [implements/README](../implements/README.md)。Gateway 与资源工作包仍单独交付。接受工作包时必须把依赖的跨系统契约一同纳入，避免各自猜测消息与身份格式。

## App Center 需要交付的接口

[App 提供方契约](../../platform/contracts/app-oauth-client-v1.md) 分成两类：

- 当前应用管理员：RegisterOAuthClient、GetApplicationOAuthRegistration、SetOAuthClientStatus、GetOAuthClientCredentialMetadata、RotateOAuthClientSecret。每个 Application 每渠道每种 type 只有一个稳定 clientId；redirect URI 在 ApplicationVersion 中管理；secret 仅登记/轮换时返回一次，不存在读取旧 secret 的接口。
- Auth 内部：GetClientConfiguration、VerifyClientSecret、ResolveClientRuntimeConfiguration、ResolveAuthorizationContext、GetApplicationPublishedRedirects。运行配置以稳定 clientId 加 channel/rpcApiMajor 在登录前返回批准 Version 的回调/scopes；用户上下文再绑定当前渠道资格。客户端不能提交“申请哪些就批准哪些”。

App 不保存用户 consent，不自行定义 scope 含义；Auth 不直接读 App MongoDB，也不保有可独立变更的第二份 client 注册表。

## 交付顺序

1. **配置和事实来源**：扩展 APP002/003/004/005 的 Version 依附回调；APP018 可并行建立稳定 registration/credential，随后 APP007 加入非空回调所需 identity 检查，再由 APP019 组合运行配置；同时落实 Auth 生产 scope 初始装载、最小授权文案和路由映射。无需先建立在线 Catalog 管理后台。
2. **可登录、可退出授权的最小闭环**：AUTH014/015/017/018 与门户一起验收。AUTH018 的 grant/family 栅栏是共享基础，应在首批 token 发放前完成，不能先上线不可撤回凭据。
3. **访问资源**：AUTH019→GW002，并交付目标服务的专用委托验签与数据授权。可先用 UserInfo 做 OIDC 互通，但通过 UserInfo 不代表业务资源已可调用。
4. **离线访问**：AUTH016 可后置；未交付时拒绝 offline_access，discovery 不宣称 refresh grant。

接口 Proto 与 HTTP annotation 是独立 API 仓库的实现产物；实施前需固定字段号、错误 reason、全部 public management 路由及生成器输入。本文已有消息语义和内部完整方法名，未把“文档设计完成”称为“立即可并行实现所有适配器”。

## 需要明确接受的取舍

- App 的 TEST/STABLE/GREY provider 已交付；Auth 多渠道适配沿用既有 UC014–019，按 TEST Tester、STABLE 正式发布、GREY 当前 cohort 分别校验，不重建 OAuth 模型。
- client authorizationEpoch、Tester episode 或 grant revocationEpoch 变化使旧代失效；grant revision 仅用于 OCC/审计。Version 或 major 切换保留历史同意，资源使用当前交集，新增 scopes 才重新 consent。secret 轮换只影响后续 confidential client authentication，不撤销既有 grant/token/family。
- 后台访问沿用 offline_access 和既有刷新端点，不增加独立授权开关或任意领取 token 的接口。refresh 采用滑动闲置期限＋固定绝对上限，规则见 UC016、时长见 OAuth/OIDC v1；仍严格旋转、无重试宽限，客户端须串行刷新，丢响应可能需要重新授权。
- sector 与 pairwise subject 由 Auth 管理，按 Application 隔离，所有渠道/type/major/hostname 共用；不同应用不因开发者相同而合并。标准 sector URI 使用 Auth 管理的每应用独立 hostname 和批准回调清单；App 不保存映射。
- 标准门户先支持浏览器重新登录。原生已有 Session 的无感 SSO 桥、更多回调类型、更多动态资料 scopes、公开 introspection、单点登出均不在本轮。
- [Traefik 契约](../../platform/contracts/oauth-delegation-v1.md)明确已有短期上下文及在途请求的撤销传播窗口；不承诺第三方应用会话/已取得数据同步删除。

Auth014–019 的设计取舍已随实施请求接受并生成 brief；已有 SESSION/身份契约保持其原有权威性。

## Scope 启用决定（2026-09-28）

采用 UC001/BR-SCP-004 的 enabled 单状态和 requestable 兼容投影；App 既有接口及 UC-APP-018 管理模型保持兼容。该决定已明确，不属于待选择的双开关方案。Auth OAuth manifest 路径现已实现 Mongo 单状态持久化/装载与一致快照，并在 UC014–019 执行当前目录检查；无 manifest 的开发模式仍保留旧硬编码 provider。目录停用/恢复的验收见实现记录。

## 本轮确认的分离边界

| 对象 | 归属与稳定范围 |
| --- | --- |
| sector / OIDC sub | Auth；每 Application 一个，所有渠道/type/major 共享 |
| registration / clientId / secret | App；按 Application＋channel 登记 PUBLIC/CONFIDENTIAL，各 major 复用 |
| grant / 历史同意 | Auth；按 authId＋applicationId＋channel 保存，同渠道两类 client 及各 major 共享；不因版本许可减少而删除 |
| 本次有效权限 | Auth；token、历史同意、当前批准版本和可用目录的交集 |
| code / token / refresh 运行选择 | channel 固定于 client，major 固定于本次凭据；Version 可在校验时重读当前值 |

UC015 包含 sector 首次原子建立和稳定 sub；APP019 增加批准回调并集查询；Gateway 增加受控 sector URI 的只读路由。Auth TEST 后端已交付；STABLE/GREY 消费扩展以实现记录为准，共享契约的 Gateway/资源落地仍独立验收。

实施接入与默认关闭门禁见 [OAuth runtime](oauth-runtime-implementation.md)。
