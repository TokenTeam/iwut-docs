# UC-AUTH-010：由 Session 签发可信用户身份

状态：`ACCEPTED`

## 目标与范围

> 已获授权的 Gateway 提交当前请求携带的 Session 和目标服务 audience，Auth 验证当前登录状态，从自己的权威数据取得用户能力，签发一枚供目标服务本地验签的短期 JWS。

本用例补上 UC004/005 和 App Center 用户入口的身份签发依赖。它不创建 Session、延长 Session、决定具体业务权限，也不实现 OAuth2、Redis 缓存或 Gateway 路由。JWS 格式引用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，跨服务请求格式见[签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)。

## 参与者与前置条件

- 调用者是预登记且 ACTIVE 的内部 Gateway 服务，必须具有 `auth.identity.issue`，并获准为本次目标 audience 申请用户身份。
- 最终用户拥有 UC007 建立的有效 Session。服务身份与用户 Session 两者都必须成立，不能相互替代。
- 签发器、可接受 audience 及能力投影策略在启动前配置并校验。签名私钥只由 Auth 持有，独立于内部服务身份密钥、设备密钥、学生关联查找及加密密钥。
- 依赖 UC007 的在线检查与事务一致性、UC006 的 USER 初始化；现有检查只返回 Session，需要本工作包增加同一一致性边界内的用户能力快照读取，不能在 Gateway 中直读数据库。

## 输入与输出

```text
IssueUserIdentityFromSessionRequest {
  audience: string
  // 服务身份来自 authorization；用户 token 来自 x-iwut-session。
}

IssuedUserIdentity {
  identityJws: string
  expiresAtUnixSeconds: int64
}
```

不接受客户端声明的 authId、permissions、developerStatus、issuer、TTL 或签名 key。audience 来自 Gateway 已匹配的固定路由；Auth 仍独立检查调用服务的 audience allowlist。输出只回给 Gateway，不作为响应头、Cookie 或业务响应交给终端。

## 主流程

1. 验证调用服务身份、方法 permission、请求结构与 audience 授权。
2. 校验专用载体中的唯一 Session token，并计算摘要；不记录原文。
3. 在与 UC007/008/009 共用的一致性边界内，确认 Session 未过期/撤销，认证凭据仍有效，主体是 ACTIVE USER；读取同一主体的 permissions、permissionRevision 及可选 developerStatus。
4. 根据服务端 audience 策略生成最小能力投影，按 BR-IDN-003 计算时间字段，并在内存中签名。
5. 与成功检查原子提交单调 lastUsedAt 更新；只有签名成功且事务提交确认后，才向 Gateway 返回 JWS。
6. Gateway 将该 JWS 附加到本次业务请求；业务服务自行验签并决定授权。

## 业务规则

<a id="br-idn-001"></a>
### BR-IDN-001：双重认证与受限签发

只有获得方法 permission 与 audience allowlist 的服务可调用。用户 Session 不能作为服务身份，服务 JWS 不能作为用户身份；端点不通过终端路由暴露。Auth 只为现存有效 Session 的 ACTIVE USER 签发，不为 SYSTEM、未知主体或损坏身份记录签发。Session 判断复用 [BR-LGN-004](UC-AUTH-007-login.md#br-lgn-004)。

<a id="br-idn-002"></a>
### BR-IDN-002：权威能力与 audience 投影

Auth 从 `auth_principals` 读取当前能力，不能信任 Session 创建时的能力副本、Gateway 传入的 claims 或客户端标签。`permissions` 必须是唯一字符串集合，permissionRevision 为正 int64；不合法的权威记录按不可用拒绝，不静默修复或忽略损坏权限。

每个 audience 配置可披露的 permission 集合及是否披露 developerStatus；签发权限为当前集合与 audience 集合的交集，稳定排序。首批最小策略：

| audience | 可披露权限 | Developer 状态 |
| --- | --- | --- |
| `iwut-app-center` | `app.version.review` | 有合法非 null 状态时携带 |
| `iwut-auth-center` | `auth.reviewer.manage` | 不携带 |

普通 USER 的 developerStatus 为 null 时省略该 claim，仍可签发合法用户身份；当前支持的非 null 状态见 [BR-DEV-004](UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004)。permissions 始终输出数组，允许为空，不自动推导管理员或 Reviewer 权限。

这只是允许 token 携带哪些能力，不表示调用者已获准执行目标业务。UC004 等后端继续检查其必需权限。新业务权限可扩充明确的服务端投影目录，不开放客户端自选权限，也不自动透传未知权限。不携带学生资料、关联 token、关联组、Session token 或私钥。首版不增加 role claim。

<a id="br-idn-003"></a>
### BR-IDN-003：短期签名与 Session 边界

格式、算法、JOSE、claims 和消费方校验规则引用 trusted-identity-v1。首版 TTL 部署默认 60 秒，可配置为 1–300 整秒，并不得超过任何目标消费方允许的 maxTTL；部署契约测试校验两侧匹配。aud 只包含本次目标 audience；jti 为每次 RPC 调用独立生成的随机 UUIDv4。签名 key 必须是有效 RSA 私钥、至少 2048 bit，有明确 kid 和 issuer。

每次事务尝试重新取服务端时间：iat/nbf 为当前 Unix 整秒，exp 为 `min(iat + TTL, floor(session.expiresAt))`。若 exp 不大于 iat，按 Session 无法继续授权拒绝，不签发零寿命 token。不延长 Session 的 expiresAt，不生成新 Session。响应中的 expiresAtUnixSeconds 与签名 exp 相等。

事务内完成签名、成功会话检查和使用时间更新，确认提交后才能释放结果。失败或提交结果未知不返回候选 JWS；重试是一轮新在线检查，可生成新的 jti，不持久化可重发的 JWS。事务内部重试可重新生成时间/签名，但不能重复产生对外响应。

消费方仍按自身 clockSkew 验签，因此绝对时间上的接受窗口包含允许的时钟容差；不能把 exp 不超过 Session expiresAt 宣称为到期瞬间的全系统强制中止。

<a id="br-idn-004"></a>
### BR-IDN-004：签发与撤销的一致性

签发授权确认点为步骤 5 的成功事务提交。与 Session/凭据撤销、账号禁用、权限及 Developer 状态修改有明确提交顺序：修改先提交时，后续确认不得使用旧状态；签发先提交的 JWS 是已授权的在途结果，随后撤销不追回它，最迟按 exp 与消费方容差停止接受。

Mongo 首版复用认证事务栅栏，并对参与确认的 Session、主体与认证凭据采用条件写以排除快照写偏差。后续 UC004 和 Developer 修改命令必须满足该一致性约定；不能先检查 Session，离开事务，再独立读取权限签发。

签发失败不提交 lastUsedAt；签发成功后，即使 Gateway 转发失败或后端拒绝业务，成功检查产生的 lastUsedAt 不回滚。不以权限不足为理由把一个仍有效的 Session 改为无效。

<a id="br-idn-005"></a>
### BR-IDN-005：首版不缓存认证结果

每个需要用户身份的 Gateway 请求均执行本用例；Auth 与 Gateway 不缓存 Session 有效结果、权限快照或签发的用户 JWS，不使用 Redis 作为第二份 Session 权威。允许启动配置、公钥和到 Auth 的连接复用，不复用先前请求的认证结论。

当前单机 Mongo 已是会话权威，先测量签发耗时、数据库事务/锁等待、吞吐和错误率，再考虑存储或缓存变化。Redis 若用于跨实例限流等非授权用途，可单独设计；若缓存身份，必须另行明确撤销传播、失效竞态、故障降级和 LRU 更新语义，不能仅通过加一个 TTL 改变本用例。

<a id="br-idn-006"></a>
### BR-IDN-006：失败关闭与秘密边界

调用鉴权、在线检查、存储或签名任一步失败均不得返回身份。存储故障不是用户未登录；错误分类见下表。只记录 requestId、调用服务、目标 audience、结果类别和必要的耗时，不记录 Session、JWS、私钥或完整认证 metadata。Gateway 与 Auth 通道必须具备部署级机密性保护；JWS 的签名不提供 Session 传输加密。

## 错误语义

| 原因 | reason | gRPC / Gateway HTTP |
| --- | --- | --- |
| 缺失/无效服务身份 | 沿用 trusted-service-identity-v1 | UNAUTHENTICATED；Gateway 对终端返回 503，属内部配置故障 |
| 服务缺少签发 permission / audience 授权 | `IDENTITY_ISSUANCE_FORBIDDEN` | PERMISSION_DENIED；Gateway 对终端返回 503 |
| 请求或 audience 结构非法 | `INVALID_IDENTITY_ISSUANCE_REQUEST` | INVALID_ARGUMENT；Gateway 对终端返回 503，路由生成输入不应非法 |
| Session 缺失/畸形/过期/撤销，凭据失效或主体不可登录 | `SESSION_INVALID` | UNAUTHENTICATED / 401 |
| 权威记录损坏、Mongo 或 signer 不可用、提交结果未知 | `IDENTITY_ISSUANCE_UNAVAILABLE` | UNAVAILABLE / 503 |
| 调用 deadline 到期 | `IDENTITY_ISSUANCE_TIMEOUT` | DEADLINE_EXCEEDED / 504 |

不要仅按 gRPC 的 UNAUTHENTICATED 推断用户要重新登录；服务身份与用户会话的 reason 必须区分。所有失败都禁止业务请求继续转发。

## 测试与验收

- Auth 后端验收使用扮演 Gateway 的测试调用方执行真实服务身份 RSA 签名，连接生产 Wire、原生 gRPC、真实 Mongo 和用户 signer，并使用实际目标 verifier 验签；不能用 fake verifier 替代。Gateway/Traefik 的真实转发调用链在 UC-GW-001 联合验收，不阻塞本工作包。
- Session 与服务身份任一缺失/伪造都拒绝；未授权 audience、SYSTEM/disabled USER、错误 key 和畸形记录拒绝。
- 普通 USER 无 Developer 状态仍成功；不同 audience 的权限交集正确，客户端无法覆盖 claims。
- 与 UC008/009、权限/Developer 修改并发时满足 BR-IDN-004；修改提交后开始的新签发不会读取旧能力。
- 签名失败和事务失败不提交 lastUsedAt、不返回候选身份；未知提交结果不声称成功，重试重新检查。
- Session 近到期截断 exp；签发后撤销不宣称已签 token 即时消失；签名公钥轮换覆盖有效 token 窗口及容差。
- 连续两次请求均访问权威检查，不能靠缓存通过第二次；下游拒绝不回滚已成功检查的 LRU 更新。
- 记录单机真实 Mongo 条件下的签发/RSA/事务开销，避免先把 Redis 当作必需组件。

## 交付依赖与非目标

UC006–009 后端已具备基础；本用例补充组合端口、能力快照、signer、内部 Proto、精确方法授权、caller audience 配置和 E2E。不依赖 Gateway 实现完成才可交付 Auth 原生 gRPC，但完整客户端链路须与 [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 联合验收。

UC004 的授权命令与 bootstrap、Developer 状态修改、OAuth2 委托权限、终端保存 JWS、Redis 和业务服务之间的内部调用不在本工作包中。独立 API 仓库中现有服务 allowlist 不会因本文自动启用签发 RPC。

## 参考

[Redis cache-aside 文档](https://redis.io/docs/latest/develop/use-cases/cache-aside/) 将 TTL 与显式失效作为控制缓存陈旧窗口的机制。本用例不接受通过认证缓存引入新的撤销窗口，暂不引入该组件；这是当前项目选择，而不是 Redis 无法保存 Session。

## 变更记录

- 2026-09-23：依赖核验通过，接受 Auth 后端工作包；UC006–009 和 service JWS 基础已具备，Gateway 联合验收独立推进；确认首版不使用 Redis。

- 2026-09-23：提出 Session 到可信身份签发用例；服务双重认证、最小 audience 投影、每请求在线确认，首版不引入 Redis。
