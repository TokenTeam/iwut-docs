# Session 到可信用户身份签发 v1

状态：`ACTIVE`

## 范围与权威来源

本契约定义 Gateway 调用 Auth 的签发 RPC 和秘密转发边界。业务权威为 [UC-AUTH-010](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)，Gateway 编排为 [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md)，输出 JWS 继续使用 [trusted-identity-v1](trusted-identity-v1.md)。本契约不是 OAuth2 Token Exchange 协议，也不自动改变已启用的方法 allowlist。

## 内部 RPC

独立 API 路径 `auth_center/v1/identity/identity.proto`，package `auth_center.v1.identity`：

```text
/auth_center.v1.identity.UserIdentityService/IssueUserIdentityFromSession

IssueUserIdentityFromSessionRequest {
  string audience = 1;
}
IssuedUserIdentity {
  string identity_jws = 1;
  int64 expires_at_unix_seconds = 2;
}
```

以上为设计线格式，正式 Proto 及生成代码在实现时进入独立 API 仓库。首版仅 unary 原生 gRPC；不注册终端 HTTP、gRPC-Web 或网关公开路由。

- `authorization`：由 Gateway 自己生成的内部服务 Bearer JWS，严格遵循 [trusted-service-identity-v1](trusted-service-identity-v1.md)，不能使用客户端 Authorization。
- `x-iwut-session`：本次终端请求提供的唯一 token，采用 [auth-device-session-v1 的 Session 载体](auth-device-session-v1.md#session-载体)，消息体不重复承载。
- 不接收 `x-iwut-identity` 作为签发授权，也不通过 JWS 自身换取新 JWS。
- 目标 audience 精确匹配预登记值；无空白修剪、URL 解释或客户端动态指定。首批值为 `iwut-auth-center` 和 `iwut-app-center`。
- body、metadata、返回体均不得进入通用请求/响应日志；传输必须受保护。客户端 token 与服务 token 均不能透传给最终业务服务。

## 服务授权扩展

本工作包在 Auth 的固定 service permission 映射中仅增加上述完整方法，要求 `auth.identity.issue`。具有该 permission 的 caller 注册项增加必需 `identityAudiences`，一个非空、唯一、已知 audience 数组；没有该 permission 的已有 caller 可以省略该字段。未知 audience 或配置非法拒绝启动。兼容已有 caller 不等于默认授予签发能力。

示例是对 `AUTH_CENTER_SERVICE_CALLERS_B64` 解码后对象的一条扩展：

```json
{
  "iwut-gateway": {
    "status": "ACTIVE",
    "keys": {"gateway-k1": {"publicKeyPemB64": "<public PEM Base64>"}},
    "permissions": ["auth.identity.issue"],
    "systemPrincipalPurposes": [],
    "identityAudiences": ["iwut-auth-center", "iwut-app-center"]
  }
}
```

当前实现不识别此新增 permission/字段；在 UC010 实现前不能将示例作为可运行配置。Gateway 的服务身份签名私钥与 Auth 的用户身份签名私钥必须不同；服务身份的 audience 固定为提供方 `iwut-auth-center`，请求 body 中的 audience 是要签发给业务服务的用户身份 audience，两者含义不同。

## 应用审核权限投影

用户能力投影唯一遵循 [UC010 / BR-IDN-002](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002)：App audience 可携带用户实际拥有的 app.profile.review 与 app.version.review；管理权限不因此下发给 App。两项权限由 [UC004](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md) 独立授予/撤销，不增加 JWS claim 或新的签发 RPC。2026-10-03 扩展需更新 Auth 投影实现并进行真实 App 验签/审核回归，不能把已有 UC010 验收视为 profile 权限链路已交付。

## 签名与验签配置

签发入口使用显式开关 `AUTH_IDENTITY_ISSUANCE_ENABLED`（默认 false）。开启要求现有 `AUTH_USER_ENDPOINTS_ENABLED=true`，且下述 signer 配置完整有效；关闭时不注册签发 RPC，不要求私钥，也不影响已有服务和用户接口。不得因为开关开启而放宽原有鉴权。

新增 signer 配置：`AUTH_USER_IDENTITY_SIGNING_KID`、`AUTH_USER_IDENTITY_PRIVATE_KEY_PEM_B64`、`AUTH_USER_IDENTITY_TTL`（默认 `60s`，1–300 整秒）。issuer 沿用 `AUTH_USER_IDENTITY_ISSUER`；既有 `AUTH_USER_IDENTITY_MAX_TTL` 是 verifier 接受上限，不是 signer 默认 TTL。

私钥使用严格标准 Base64 包装的 PKCS#1/PKCS#8 RSA PEM，至少 2048 bit。Auth 自己作为 audience 时必须部署匹配的 verifier 公钥；其他服务先部署新公钥，再切 signer kid，旧验签公钥覆盖旧 token 的有效期、允许时钟偏差和在途请求后才移除。签发 key 只为此用途配置，不复用学生关联加密/查找密钥或服务身份 key。

输出 identity_jws 不为空，单个 compact JWS，最多 16 KiB；权限投影过大导致超限时不截断权限，按签发不可用拒绝。Gateway 只检查可信 Auth 响应的有界形状、三段格式及必要剩余时间，不解读 claims 进行授权或重签；最终服务仍必须验签。

## 请求与凭据流向

| 策略/调用 | 允许送给下一跳的凭据 |
| --- | --- |
| Gateway → Auth 签发 RPC | Gateway 服务 JWS + 原始 Session；无终端伪造身份头 |
| SESSION → 最终业务服务 | 只携带 Auth 签发的 `x-iwut-identity`；移除 Session、终端 Authorization 与内部服务 JWS |
| DIRECT → Auth 自认证方法 | 仅按该方法契约保留凭据，例如撤销接口的 Session；不附加 Gateway 服务身份 |
| OAUTH2 | 本轮禁用；未来独立委托凭证契约决定流向，不能套用普通 USER JWS |

Gateway 消费签发结果后不得把 identity_jws 暴露给终端或加入业务响应头。失败 reason 与 HTTP/gRPC 映射引用 UC010；Auth 签发失败不能继续 Router 转发。

## 与现有契约的衔接

- 终端不能经 Gateway 访问 ScopeCatalog、DeveloperStatusDirectory、SystemPrincipalDirectory 或签发 RPC；这些是服务到服务方法。不得仅凭 `/auth-center` 前缀自动开放。
- 本契约不改变 UC008 的幂等匿名 token 定向撤销例外，或 UC009 的有效 Session 授权；这两条 Gateway 路由均走 DIRECT，由 Auth 自己验证。
- Auth 用户资料及 UC004 新旧管理入口均走 SESSION，得到 audience=`iwut-auth-center` 的用户 JWS；不能因目标是 Auth 而递归触发签发。
- Gateway 只为外部用户请求编排身份。服务到服务调用继续使用独立 service JWS，不能借用某位用户的 Session。
