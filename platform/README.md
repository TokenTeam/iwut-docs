# 平台共享设计文档

状态：**权威** — 本目录保存跨 bounded context 的设计契约，只有真正跨系统的内容才放这里。

## 放什么、不放什么

| 内容 | 权威位置 | 说明 |
| --- | --- | --- |
| App Center 的业务语义（UC、BR、领域模型、能力内 ADR） | `app-center/` | 仍由 App Center 的正文与 `app-center/design-registry.md` 管理 |
| Auth Center 的业务语义（UC、BR、目录所有权） | `auth-center/` | 仍由 Auth Center 的正文与 `auth-center/design-registry.md` 管理 |
| Gateway 的路由策略、认证编排和转发行为 | `gateway/` | UC-GW-001 拥有规则，Gateway registry 独立维护 |
| 可执行 Proto / API 定义 | 独立 API 仓库 | 本仓库不放可执行契约，只放设计契约 |
| 跨系统决定（例如身份信任模型、gRPC-Web 终止位置） | `platform/adr/` | 记录为什么选择某种跨系统方案及其后果 |
| 稳定的身份、消息、路由格式 | `platform/contracts/` | 记录多方必须共同遵守、可做契约测试的格式与语义 |
| 某个能力的实现细节、单系统决策 | 对应能力目录 | 不要为了“看起来集中”而提升到平台层 |

判断标准：**如果一条规则只对一个 bounded context 成立，它就不属于 `platform/`。** 平台文档记录的是系统之间的约定，例如“可信身份 JWS 由谁签发、入口如何路由”，而不是某个服务内部如何实现。

## 权威边界

- 同一内容只能有一个权威定义。`platform/` 的文档**不复制** `app-center/`、`auth-center/` 或 Gateway 已有的正文；需要引用时链接原 ID 与锚点。
- `platform/` 文档**不登记进 `app-center/design-registry.md`**。那份注册表是 App Center 的索引，不是跨系统登记表。
- `platform/` 文档可以定义自己的跨系统决定或契约 ID；本仓库当前不为它生成注册表。
- 例如，采用“Auth Center 签发短期、指定 audience 的 JWS，Gateway 转发，App Center 本地验签”属于 `platform/adr/`；JWS header/claims、audience、有效期约束和转发载体属于 `platform/contracts/`。App Center 如何把已验证身份用于某个 UC，仍属于 `app-center/`。
- `platform/` 下的文档是权威设计正文，但**不自动进入任何 brief**。

当前 App Center 与前端扫描器共享的 Tester 凭证 URL 格式见 [Tester 加入 URL v1](contracts/tester-join-url-v1.md)；mock 入口和可配置前缀不改变加入用例的身份与凭证验证要求。

## 与 brief 生成的关系

当前 App 设备认证与 Session 的跨端格式见 [auth-device-session-v1](contracts/auth-device-session-v1.md)，包括公钥、签名输入、学号关联声明、Session 载体、RPC 鉴权表及公开测试向量。Auth 自有业务和存储规则仍由对应 UC 拥有。

平台共享文档默认**不进入 engineering baseline**。只有某个 per-UC spec 在 `shared_sections` 里显式选择时，才会被抽取进那一份 brief：

```json
{
  "uc": "UC-APP-003",
  "shared_sections": {
    "platform/contracts/trusted-identity-v1.md": ["JWS Claims", "校验顺序"]
  }
}
```

规则：

- 键是**相对 docs 仓库根**的 POSIX 路径（`platform/…`），不是相对 `app-center/` 的路径，也不需要登记进 registry。
- 值是章节路径列表，语法与 `adr_sections` / `uc_sections` 相同，支持 `父节/子节`。
- 渲染顺序稳定：文件按路径字典序，章节按 spec 中的顺序。
- 选中的共享章节会出现在 brief 正文、未纳入小节索引、溯源表（含 sha256）与源体积统计中。
- 从 `app-center/briefs/` 输出位置看，平台文档里的相对链接会被重写为仍然正确的路径（例如 `../../platform/…`）。

生成是 **fail closed** 的：绝对路径、`..`、解析后经 symlink 逃逸 docs 仓库的路径、缺失文件、非普通 Markdown 文件、缺失章节都会被收集为问题并让生成失败，不会产出残缺 brief。

## 新增平台文档时

1. 先确认这条规则确实跨系统，且不能在原能力权威文档里定义。
2. 跨系统选择写入 `platform/adr/`，稳定格式写入 `platform/contracts/`；用 `#` 标题与 `##` / `###` 章节组织，便于 `shared_sections` 选择。
3. 需要被工作包使用时，在对应 `tools/brief-specs/<UC>.json` 里添加 `shared_sections`，不要复制正文到 `app-center/`。

## Session 签发与 Gateway

[Session 到可信用户身份签发 v1](contracts/auth-session-identity-issuance-v1.md) 已 ACTIVE，定义 Gateway 对 Auth 的内部签发 RPC、双重凭据和 audience 授权。业务规则分别由 [UC-AUTH-010](../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 与 [UC-GW-001](../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 拥有。两项 UC 均已接受；Auth 后端为 CORE_COMPLETE，Gateway 首个后端/本地部署工作包为 COMPLETE，并已通过真实 Auth/Mongo 与三协议联合验收。生产 RPC 仍须按部署开关显式启用；实现完成不等于已执行生产公网发布。

Auth HTTP/JSON 的路径、ProtoJSON 与部署边界见 [Auth API 路由](contracts/auth-center-api-routing.md)。

邮箱注册的独立签名、消息字段与可选 Session 鉴权见 [邮箱设置与注册协议 v1](contracts/auth-email-binding-v1.md)；公开测试向量通过 `tools/auth_email_protocol_vectors.py --check` 校验，旧设备协议保持兼容。

邮箱登录与本机设备授权的独立协议见 [邮箱登录 v1](contracts/auth-email-login-v1.md)，向量校验命令为 `tools/auth_email_login_vectors.py --check`；与邮箱注册保持用途隔离。

Developer 自助申请的有效 Session 接口、nullable 状态及 HTTP 路由见 [Developer 自助申请协议 v1](contracts/auth-developer-application-v1.md)；不改变 UC002 内部目录或既有 JWS 格式。

## OAuth / OIDC 新设计

以下契约均为 PROPOSED，当前实现尚未启用：

- [OAuth/OIDC 接入协议 v1](contracts/oauth-oidc-v1.md)：两种 client 配置、标准端点、门户、token 与 subject。
- [App OAuth Client 提供方契约 v1](contracts/app-oauth-client-v1.md)：应用管理员管理接口、Auth 内部配置/secret 验证/授权上下文接口。
- [OAuth 委托上下文与 Traefik v1](contracts/oauth-delegation-v1.md)：opaque access token 在线校验、专用 JWS、路由与三协议入口。
- [工作包与依赖总览](../auth-center/design-notes/oauth-oidc-delivery-plan.md)：Auth 014–019、App 018–019、Gateway 002；不覆盖已接受的 Session/USER 契约。

## 账号与 Developer 退出协调草案

[账号退出时的 App 归属协调 v1](contracts/account-owner-exit-v1.md)（ACCEPTED）供 Auth UC024/025 使用，定义归属准备屏障、持久终局和失败重试；App UC025 已接受并进入实现，提供方扩展与 Auth 同批交付。

## Application 关闭协调提案

[Application 关闭协调 v1](contracts/application-closure-v1.md)（PROPOSED）定义 App UC027 在本地不可逆关闭后，如何让 Auth 持久建立 applicationId 级授权撤销栅栏并通过幂等回执收敛。Auth 消费方 UC 与近期重新认证证明契约尚待建立，因此当前不能进入实现。
