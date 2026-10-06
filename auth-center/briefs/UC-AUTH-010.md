<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-010 --spec tools/brief-specs/UC-AUTH-010.json -->
# Brief — UC-AUTH-010：由 Session 签发可信用户身份

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-010` 由 Session 签发可信用户身份 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-IDN-001`–`BR-IDN-006`（6 条） |
| 外部引用 BR | `BR-ACC-004`，`BR-ADM-001`，`BR-DEV-004`，`BR-LGN-004`（来自 `UC-AUTH-002`、`UC-AUTH-007`、`UC-AUTH-021`、`UC-AUTH-022`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-session-identity-issuance-v1.md`、`platform/contracts/trusted-identity-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

> 已获授权的 Gateway 提交当前请求携带的 Session 和目标服务 audience，Auth 验证当前登录状态，从自己的权威数据取得用户能力，签发一枚供目标服务本地验签的短期 JWS。

本用例补上 UC004/005 和 App Center 用户入口的身份签发依赖。它不创建 Session、延长 Session、决定具体业务权限，也不实现 OAuth2、Redis 缓存或 Gateway 路由。JWS 格式引用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，跨服务请求格式见[签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)。

### 参与者与前置条件

- 调用者是预登记且 ACTIVE 的内部 Gateway 服务，必须具有 `auth.identity.issue`，并获准为本次目标 audience 申请用户身份。
- 最终用户拥有 UC007 建立的有效 Session。服务身份与用户 Session 两者都必须成立，不能相互替代。
- 签发器、可接受 audience 及能力投影策略在启动前配置并校验。签名私钥只由 Auth 持有，独立于内部服务身份密钥、设备密钥、学生关联查找及加密密钥。
- 依赖 UC007 的在线检查与事务一致性、UC006 的 USER 初始化；现有检查只返回 Session，需要本工作包增加同一一致性边界内的用户能力快照读取，不能在 Gateway 中直读数据库。

### 输入与输出

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

Auth audience 的 `account_revision` 条件必需投影及在线消费规则引用 [UC022/BR-ACC-004](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-004)；App audience 不增加该 claim。所有 Session 校验同时满足 UC022 的 accountRevision，CLOSED 永不签发。

### 主流程

1. 验证调用服务身份、方法 permission、请求结构与 audience 授权。
2. 校验专用载体中的唯一 Session token，并计算摘要；不记录原文。
3. 在与 UC007/008/009 共用的一致性边界内，确认 Session 未过期/撤销，认证凭据仍有效，主体是 ACTIVE USER；读取同一主体的 permissions、permissionRevision 及可选 developerStatus。
4. 根据服务端 audience 策略生成最小能力投影，按 BR-IDN-003 计算时间字段，并在内存中签名。
5. 与成功检查原子提交单调 lastUsedAt 更新；只有签名成功且事务提交确认后，才向 Gateway 返回 JWS。
6. Gateway 将该 JWS 附加到本次业务请求；业务服务自行验签并决定授权。

### 错误语义

| 原因 | reason | gRPC / Gateway HTTP |
| --- | --- | --- |
| 缺失/无效服务身份 | 沿用 trusted-service-identity-v1 | UNAUTHENTICATED；Gateway 对终端返回 503，属内部配置故障 |
| 服务缺少签发 permission / audience 授权 | `IDENTITY_ISSUANCE_FORBIDDEN` | PERMISSION_DENIED；Gateway 对终端返回 503 |
| 请求或 audience 结构非法 | `INVALID_IDENTITY_ISSUANCE_REQUEST` | INVALID_ARGUMENT；Gateway 对终端返回 503，路由生成输入不应非法 |
| Session 缺失/畸形/过期/撤销，凭据失效或主体不可登录 | `SESSION_INVALID` | UNAUTHENTICATED / 401 |
| 权威记录损坏、Mongo 或 signer 不可用、提交结果未知 | `IDENTITY_ISSUANCE_UNAVAILABLE` | UNAVAILABLE / 503 |
| 调用 deadline 到期 | `IDENTITY_ISSUANCE_TIMEOUT` | DEADLINE_EXCEEDED / 504 |

不要仅按 gRPC 的 UNAUTHENTICATED 推断用户要重新登录；服务身份与用户会话的 reason 必须区分。所有失败都禁止业务请求继续转发。

### 测试与验收

- Auth 后端验收使用扮演 Gateway 的测试调用方执行真实服务身份 RSA 签名，连接生产 Wire、原生 gRPC、真实 Mongo 和用户 signer，并使用实际目标 verifier 验签；不能用 fake verifier 替代。Gateway/Traefik 的真实转发调用链在 UC-GW-001 联合验收，不阻塞本工作包。
- Session 与服务身份任一缺失/伪造都拒绝；未授权 audience、SYSTEM/disabled USER、错误 key 和畸形记录拒绝。
- 普通 USER 无 Developer 状态仍成功；不同 audience 的权限交集正确，客户端无法覆盖 claims。
- 两项应用审核权限的零项/profile-only/version-only/两项组合均用真实签发和 App verifier 验证；向 Auth audience 不泄露它们，向 App 不泄露管理权限。
- 分别与 UC004 两项权限的授予/撤销竞争，撤销先提交后新签发不能包含该项；另一项独立保留，不能只对旧 version 权限执行过滤或撤销协调。
- 与 UC008/009、权限/Developer 修改并发时满足 BR-IDN-004；修改提交后开始的新签发不会读取旧能力。
- 签名失败和事务失败不提交 lastUsedAt、不返回候选身份；未知提交结果不声称成功，重试重新检查。
- Session 近到期截断 exp；签发后撤销不宣称已签 token 即时消失；签名公钥轮换覆盖有效 token 窗口及容差。
- 连续两次请求均访问权威检查，不能靠缓存通过第二次；下游拒绝不回滚已成功检查的 LRU 更新。
- 记录单机真实 Mongo 条件下的签发/RSA/事务开销，避免先把 Redis 当作必需组件。

### 交付依赖与非目标

UC006–009 后端已具备基础；本用例补充组合端口、能力快照、signer、内部 Proto、精确方法授权、caller audience 配置和 E2E。不依赖 Gateway 实现完成才可交付 Auth 原生 gRPC，但完整客户端链路须与 [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 联合验收。

UC004 的授权命令与 bootstrap、Developer 状态修改、OAuth2 委托权限、终端保存 JWS、Redis 和业务服务之间的内部调用不在本工作包中。独立 API 仓库中现有服务 allowlist 不会因本文自动启用签发 RPC。

## 业务规则（UC-AUTH-010 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-001 -->
### BR-IDN-001：双重认证与受限签发

只有获得方法 permission 与 audience allowlist 的服务可调用。用户 Session 不能作为服务身份，服务 JWS 不能作为用户身份；端点不通过终端路由暴露。Auth 只为现存有效 Session 的 ACTIVE USER 签发，不为 SYSTEM、未知主体或损坏身份记录签发。Session 判断复用 [BR-LGN-004](../use-cases/UC-AUTH-007-login.md#br-lgn-004)。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002 -->
### BR-IDN-002：权威能力与 audience 投影

Auth 从 `auth_principals` 读取当前能力，不能信任 Session 创建时的能力副本、Gateway 传入的 claims 或客户端标签。`permissions` 必须是唯一字符串集合，permissionRevision 为正 int64；不合法的权威记录按不可用拒绝，不静默修复或忽略损坏权限。

每个 audience 配置可披露的 permission 集合及是否披露 developerStatus；签发权限为当前集合与 audience 集合的交集，稳定排序。首批最小策略：

| audience | 可披露权限 | Developer 状态 |
| --- | --- | --- |
| `iwut-app-center` | `app.application.restore`、`app.application.suspend`、`app.profile.review`、`app.version.review` | 有合法非 null 状态时携带 |
| `iwut-auth-center` | UC021/BR-ADM-001 固定四项管理权限 | 不携带 |

普通 USER 的 developerStatus 为 null 时省略该 claim，仍可签发合法用户身份；当前支持的非 null 状态见 [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004)。permissions 始终输出数组，允许为空，不自动推导管理员或 Reviewer 权限。

两项应用审核权限均来自 UC004 的独立显式 grant；不能从管理权限、Developer 状态或另一项审核权限推导。向 App 签发时保留精确值并稳定排序，只拥有其中一项时只签该项；不向 App 披露任何管理权限，不向 Auth audience 披露应用审核权限。

这只是允许 token 携带哪些能力，不表示调用者已获准执行目标业务。UC004 等后端继续检查其必需权限。新业务权限可扩充明确的服务端投影目录，不开放客户端自选权限，也不自动透传未知权限。不携带学生资料、关联 token、关联组、Session token 或私钥。首版不增加 role claim。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-003 -->
### BR-IDN-003：短期签名与 Session 边界

格式、算法、JOSE、claims 和消费方校验规则引用 trusted-identity-v1。首版 TTL 部署默认 60 秒，可配置为 1–300 整秒，并不得超过任何目标消费方允许的 maxTTL；部署契约测试校验两侧匹配。aud 只包含本次目标 audience；jti 为每次 RPC 调用独立生成的随机 UUIDv4。签名 key 必须是有效 RSA 私钥、至少 2048 bit，有明确 kid 和 issuer。

每次事务尝试重新取服务端时间：iat/nbf 为当前 Unix 整秒，exp 为 `min(iat + TTL, floor(session.expiresAt))`。若 exp 不大于 iat，按 Session 无法继续授权拒绝，不签发零寿命 token。不延长 Session 的 expiresAt，不生成新 Session。响应中的 expiresAtUnixSeconds 与签名 exp 相等。

事务内完成签名、成功会话检查和使用时间更新，确认提交后才能释放结果。失败或提交结果未知不返回候选 JWS；重试是一轮新在线检查，可生成新的 jti，不持久化可重发的 JWS。事务内部重试可重新生成时间/签名，但不能重复产生对外响应。

消费方仍按自身 clockSkew 验签，因此绝对时间上的接受窗口包含允许的时钟容差；不能把 exp 不超过 Session expiresAt 宣称为到期瞬间的全系统强制中止。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004 -->
### BR-IDN-004：签发与撤销的一致性

签发授权确认点为步骤 5 的成功事务提交。与 Session/凭据撤销、账号禁用、权限及 Developer 状态修改有明确提交顺序：修改先提交时，后续确认不得使用旧状态；签发先提交的 JWS 是已授权的在途结果，随后撤销不追回它，最迟按 exp 与消费方容差停止接受。

Mongo 首版复用认证事务栅栏，并对参与确认的 Session、主体与认证凭据采用条件写以排除快照写偏差。后续 UC004 和 Developer 修改命令必须满足该一致性约定；不能先检查 Session，离开事务，再独立读取权限签发。

签发失败不提交 lastUsedAt；签发成功后，即使 Gateway 转发失败或后端拒绝业务，成功检查产生的 lastUsedAt 不回滚。不以权限不足为理由把一个仍有效的 Session 改为无效。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-005 -->
### BR-IDN-005：首版不缓存认证结果

每个需要用户身份的 Gateway 请求均执行本用例；Auth 与 Gateway 不缓存 Session 有效结果、权限快照或签发的用户 JWS，不使用 Redis 作为第二份 Session 权威。允许启动配置、公钥和到 Auth 的连接复用，不复用先前请求的认证结论。

当前单机 Mongo 已是会话权威，先测量签发耗时、数据库事务/锁等待、吞吐和错误率，再考虑存储或缓存变化。Redis 若用于跨实例限流等非授权用途，可单独设计；若缓存身份，必须另行明确撤销传播、失效竞态、故障降级和 LRU 更新语义，不能仅通过加一个 TTL 改变本用例。

<!-- 权威位置: use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-006 -->
### BR-IDN-006：失败关闭与秘密边界

调用鉴权、在线检查、存储或签名任一步失败均不得返回身份。存储故障不是用户未登录；错误分类见下表。只记录 requestId、调用服务、目标 audience、结果类别和必要的耗时，不记录 Session、JWS、私钥或完整认证 metadata。Gateway 与 Auth 通道必须具备部署级机密性保护；JWS 的签名不提供 Session 传输加密。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-022`

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-004 -->
### BR-ACC-004：可信身份与下游生效边界

Auth 自身消费的 USER JWS 也必须防止恢复后重放。UC010 为 `iwut-auth-center` 签发时增加 `account_revision` claim，值为当前 accountRevision 的规范十进制字符串（正 int64，无前导零），来自与 Session 检查相同的快照。Auth 的所有 USER JWS 入口统一在线比较该 claim 与当前 ACTIVE 账号版本；缺失或不一致拒绝，不只在本用例管理入口校验。实施时同步 trusted-identity-v1 的条件必需字段与实现。

该字段首版只向 Auth audience 投影；不加入 OIDC ID Token、用户资料或第三方身份，不为 App 引入新的在线 introspection 要求。App audience USER JWS 及 UC019 委托 JWS 仍按既有短 TTL/leeway 离线校验。禁用确认后，Auth 不再为目标账号签发新身份；在此之前已签发的短期 JWS 可能继续被下游接受直到到期，不能承诺瞬间阻断已转发请求。

OIDC ID Token 是一次认证的证据，第三方自己建立的 Cookie/Session 不由本用例远程销毁。旧 opaque access/refresh token 在 Auth 在线检查时永久失败；第三方继续访问平台资源必须经过这些检查。要求应用立即登出需另行设计 OIDC logout/通知协议，不由本 UC 暗中增加。

### 来自 `UC-AUTH-021`

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001 -->
### BR-ADM-001：固定管理权限集合

管理员集合 v1 固定为以下四项：

| permission | 能力边界 |
| --- | --- |
| `auth.platform-admin.manage` | 本用例的管理员资格管理与查询 |
| `auth.reviewer.manage` | UC004 的两项审核权限管理 |
| `auth.account.manage` | 后续账号禁用与恢复用例 |
| `auth.developer.manage` | 后续 Developer 暂停与恢复用例 |

不新增 principalType，不存第二份可独立修改的 role/granted 布尔值，不从 Developer 身份推导资格。四项全部存在为 GRANTED，四项均不存在为 NONE。

只包含部分管理权限（包括仅有 auth.reviewer.manage）的集合不符合本用例数据约束，失败关闭，不能视为普通用户或由 GRANT 静默补齐。与四项无关的权限不参与该分类。

GRANT 将 NONE 转为 GRANTED；REVOKE 将 GRANTED 转为 NONE，删除整个管理集合。管理权限不记录多个叠加授予来源。审核权限本身、Developer 状态、设备凭据和 Session 均保留。不得通过 UC004 修改集合中的任何一项。

### 来自 `UC-AUTH-002`

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004 -->
### BR-DEV-004：状态语义

公开 `PENDING/APPROVED/REJECTED/SUSPENDED/WITHDRAWN`。UC-APP-005 只把
`SUSPENDED` 判断为暂停，但 Auth 返回完整枚举，让消费方不需要用 bool 掩盖未知状态。

CLOSED 墓碑作为明确终止状态返回是本规则的例外，不将其伪装成 PENDING 或 WITHDRAWN。

普通 USER 可以不是 Developer，此时 `developerStatus = null`；SYSTEM principal 也不具有
Developer 状态。两者都不能作为本查询的成功结果，且不得被伪装成 `PENDING`。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-004 -->
### BR-LGN-004：有效期与在线检查

首版采用固定绝对有效期：T_session 通过 AUTH_SESSION_TTL 配置，为部署必填的正时长，创建时固定 expiresAt；缺失/非法配置拒绝接流量。配置采用 Go duration 格式，示例部署值为 `720h`（30 天）；该示例不是隐式默认值。本轮不自动滑动续期、不签发 refresh token，也不因请求活跃无限延长会话。到期后必须重新完成本用例的设备认证并建立新 Session，不延长旧会话的 expiresAt。后续若增加续期，另行设计轮换与并发语义。

一次成功会话检查必须得到一致、当前的事实：token 摘要匹配，Session 未撤销且 `now < expiresAt`，所属主体为 ACTIVE USER，作为会话认证依据的设备凭据仍有效且归属一致。缺失、损坏、超时或无法读取均失败关闭，不能回退到客户端缓存或只凭旧 JWT 放行。

首版不缓存正向会话授权结果，权威读取不得使用可能落后的副本。建议使用一致快照读取主体、凭据和 Session；检查与撤销/禁用存在并发时，以明确的检查快照为边界。变更提交后才开始的新检查必须看到变更；先已通过的请求可能继续执行，不承诺取消在途业务。

成功检查还须完成 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010) 的使用时间更新；不能先返回检查成功，再异步记录使用时间。此更新不改变固定 expiresAt。

清理过期会话只是存储维护；即使记录未被删除也不能再通过检查。更改配置不追溯改变已有 expiresAt；紧急失效使用显式撤销，不通过重解释时间或静默换令牌完成。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。UC020 独立入口的缺失/畸形或混用载体为 INVALID_SESSION_TOKEN（400），载体合法但当前资格失效为 SESSION_INVALID（401），不得沿用 UC008 的免有效性检查。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/auth-session-identity-issuance-v1.md`：Session 到可信用户身份签发 v1

#### 范围与权威来源

本契约定义 Gateway 调用 Auth 的签发 RPC 和秘密转发边界。业务权威为 [UC-AUTH-010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md)，Gateway 编排为 [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md)，输出 JWS 继续使用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。本契约不是 OAuth2 Token Exchange 协议，也不自动改变已启用的方法 allowlist。

#### 内部 RPC

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

- `authorization`：由 Gateway 自己生成的内部服务 Bearer JWS，严格遵循 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，不能使用客户端 Authorization。
- `x-iwut-session`：本次终端请求提供的唯一 token，采用 [auth-device-session-v1 的 Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，消息体不重复承载。
- 不接收 `x-iwut-identity` 作为签发授权，也不通过 JWS 自身换取新 JWS。
- 目标 audience 精确匹配预登记值；无空白修剪、URL 解释或客户端动态指定。首批值为 `iwut-auth-center` 和 `iwut-app-center`。
- body、metadata、返回体均不得进入通用请求/响应日志；传输必须受保护。客户端 token 与服务 token 均不能透传给最终业务服务。

#### 服务授权扩展

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

#### 签名与验签配置

签发入口使用显式开关 `AUTH_IDENTITY_ISSUANCE_ENABLED`（默认 false）。开启要求现有 `AUTH_USER_ENDPOINTS_ENABLED=true`，且下述 signer 配置完整有效；关闭时不注册签发 RPC，不要求私钥，也不影响已有服务和用户接口。不得因为开关开启而放宽原有鉴权。

新增 signer 配置：`AUTH_USER_IDENTITY_SIGNING_KID`、`AUTH_USER_IDENTITY_PRIVATE_KEY_PEM_B64`、`AUTH_USER_IDENTITY_TTL`（默认 `60s`，1–300 整秒）。issuer 沿用 `AUTH_USER_IDENTITY_ISSUER`；既有 `AUTH_USER_IDENTITY_MAX_TTL` 是 verifier 接受上限，不是 signer 默认 TTL。

私钥使用严格标准 Base64 包装的 PKCS#1/PKCS#8 RSA PEM，至少 2048 bit。Auth 自己作为 audience 时必须部署匹配的 verifier 公钥；其他服务先部署新公钥，再切 signer kid，旧验签公钥覆盖旧 token 的有效期、允许时钟偏差和在途请求后才移除。签发 key 只为此用途配置，不复用学生关联加密/查找密钥或服务身份 key。

输出 identity_jws 不为空，单个 compact JWS，最多 16 KiB；权限投影过大导致超限时不截断权限，按签发不可用拒绝。Gateway 只检查可信 Auth 响应的有界形状、三段格式及必要剩余时间，不解读 claims 进行授权或重签；最终服务仍必须验签。

#### 请求与凭据流向

| 策略/调用 | 允许送给下一跳的凭据 |
| --- | --- |
| Gateway → Auth 签发 RPC | Gateway 服务 JWS + 原始 Session；无终端伪造身份头 |
| SESSION → 最终业务服务 | 只携带 Auth 签发的 `x-iwut-identity`；移除 Session、终端 Authorization 与内部服务 JWS |
| DIRECT → Auth 自认证方法 | 仅按该方法契约保留凭据，例如撤销接口的 Session；不附加 Gateway 服务身份 |
| OAUTH2 | 本轮禁用；未来独立委托凭证契约决定流向，不能套用普通 USER JWS |

Gateway 消费签发结果后不得把 identity_jws 暴露给终端或加入业务响应头。失败 reason 与 HTTP/gRPC 映射引用 UC010；Auth 签发失败不能继续 Router 转发。

#### 与现有契约的衔接

- 终端不能经 Gateway 访问 ScopeCatalog、DeveloperStatusDirectory、SystemPrincipalDirectory 或签发 RPC；这些是服务到服务方法。不得仅凭 `/auth-center` 前缀自动开放。
- 本契约不改变 UC008 的幂等匿名 token 定向撤销例外，或 UC009 的有效 Session 授权；这两条 Gateway 路由均走 DIRECT，由 Auth 自己验证。
- Auth 用户资料及 UC004 新旧管理入口均走 SESSION，得到 audience=`iwut-auth-center` 的用户 JWS；不能因目标是 Auth 而递归触发签发。
- Gateway 只为外部用户请求编排身份。服务到服务调用继续使用独立 service JWS，不能借用某位用户的 Session。

#### 应用审核权限投影

用户能力投影唯一遵循 [UC010 / BR-IDN-002](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002)：App audience 可携带用户实际拥有的 `app.profile.review`、`app.version.review`、`app.application.suspend` 与 `app.application.restore`；Auth 管理权限不因此下发给 App。审核权限由 [UC004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) 管理，运维权限由 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 管理；均复用现有 `permissions` claim 和签发 RPC。平台管理员不会被自动投影为 Reviewer 或 Application 运维人员。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### JOSE Header

JOSE header 是 JSON 对象，至少包含：

| 字段 | 必需 | 约束 |
| --- | --- | --- |
| `typ` | 是 | 必须**精确**等于 `JWT`（区分大小写；`jwt`、`JWS` 等变体一律拒绝） |
| `alg` | 是 | 必须等于 `RS256` |
| `kid` | 是 | 非空字符串；必须能解析到本地启动配置中的一把 RSA 公钥 |

`alg` 为 `none`、`HS*` 或任何非 `RS256` 值都必须拒绝。禁止根据 token 自带的 `jwk`/`x5u` 等字段在运行时拉取密钥。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

#### 密钥与轮换

- 消费方启动时加载一组 `kid → RSA 公钥` 映射；公钥以来自身份配置的 PEM 文件或等价明确配置提供。
- 至少配置一把公钥；`kid` 为空、重复或公钥无法解析时必须**阻止启动**，不得跳过或降级。
- 每把 RSA 公钥的模数至少 **2048 bit**；小于 2048 bit 的密钥必须**阻止启动**，不得降级接受。
- 轮换采用双密钥重叠：先发布新 kid 的公钥并让签发方开始使用新 kid，旧 kid 公钥保留到持有旧 token 的最长寿命（不超过 `maxTTL`）之后才移除。
- 未知 `kid` 一律认证失败，禁止回退到「唯一的公钥」或首次见到的密钥。
- 不在请求路径上拉取或刷新密钥。密钥分发是部署配置问题，不是每请求行为。

#### Gateway 义务

Gateway 是身份的**透传者**，不是信任的终点。对每个将会到达受保护后端的请求，Gateway 必须：

1. 剥离客户端传入的 `x-iwut-identity`，无论其内容是否看起来合法。
2. 剥离旧头 `X-Auth-Jwt-Type`、`X-Auth-Base-Claim`、`X-Auth-Oauth-Claim`、`X-Auth-Service-Claim`，不让它们到达后端。
3. 写入由 Auth Center 取得的、绑定目标服务 audience 的 JWS 到 `x-iwut-identity`。
4. HTTP 与 gRPC 转发都使用同一键；gRPC metadata 键为小写。
5. 仅剥离 `/app-center` 服务前缀，不重写内部路径（路由见 [App Center API 路由 v1](../../platform/contracts/app-center-api-routing.md)）。
6. 不因为某个后端「也校验日志」或「内网可信」而省略上述步骤。

Gateway 不要求验签，也不得把验签结果以明文身份字段转写后丢弃签名。

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center`，App Center 为 `iwut-app-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### Auth Center 固定授权映射

| gRPC 方法 | 必需 permission |
| --- | --- |
| `ScopeCatalog/GetScopeCatalogSnapshot` | `auth.scope-catalog.read` |
| `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | `auth.developer-status.read` |
| `SystemPrincipalDirectory/ResolveSystemPrincipal` | `auth.system-principal.resolve` |
| `UserIdentityService/IssueUserIdentityFromSession` | `auth.identity.issue` |
| `ApplicationClosureService/ApplyApplicationClosure` | `auth.application-closure.apply` |
| `ApplicationClosureService/GetApplicationClosureStatus` | `auth.application-closure.read` |

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### ENV 配置

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_IDENTITY_ID` | `serviceId` |
| `APP_CENTER_SERVICE_IDENTITY_KID` | 当前签名 key ID |
| `APP_CENTER_SERVICE_IDENTITY_AUDIENCE` | 默认 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_PRIVATE_KEY_PEM_B64` | PKCS#1 或 PKCS#8 RSA private-key PEM 的 strict standard Base64 |
| `APP_CENTER_SERVICE_IDENTITY_TTL` | 正 Go duration；默认 `1m` |

Auth Center 必须提供 `AUTH_CENTER_SERVICE_CALLERS_B64`：以下 JSON UTF-8 bytes 的 strict standard Base64。

```json
{
  "iwut-app-center": {
    "status": "ACTIVE",
    "keys": {
      "app-center-2026-01": {
        "publicKeyPemB64": "<RSA public-key PEM 的 strict standard Base64>"
      }
    },
    "permissions": [
      "auth.scope-catalog.read",
      "auth.developer-status.read",
      "auth.system-principal.resolve",
      "auth.application-closure.apply",
      "auth.application-closure.read"
    ],
    "systemPrincipalPurposes": [
      "app-center.review-auto-rejection"
    ]
  }
}
```

外层 Base64 只解决环境变量传输与转义，不提供保密性。部署必须用 secret 管理 App 私钥；不得把值提交到仓库、镜像、日志或诊断输出。Auth 公钥注册表不含私钥，可以由 config 或 secret 注入。缺失、未知字段、重复权限、非法 key、未知 permission/purpose 或空注册表必须阻止启动。

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_CALLERS_B64` | 与 Auth caller registry 相同的 strict Base64 JSON schema；首版登记 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` | 接受的最大 token TTL，默认 `1m` |
| `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW` | claims 时钟偏差，默认 `30s` |

App Center registry 中 `iwut-auth-center` 允许上述五个 `app.oauth.*` permission，以及 account-owner-exit-v1 固定的三个 app.account-owner-exit.* 精确权限，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

#### 契约测试要求

至少验证合法调用、缺失/错误签名、未知 serviceId、未知 kid、错误 audience、过长 TTL、disabled caller、缺少 RPC permission 和未允许 purpose。生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor，不能只验证同接口 fake server。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-010`（use-cases/UC-AUTH-010-issue-user-identity-from-session.md）：参考、变更记录
- `UC-AUTH-022`（use-cases/UC-AUTH-022-disable-and-restore-user-account.md）：目标与范围、参与者与接口、主流程、错误语义与配置、验收场景、实现依赖与联动、变更记录
- `UC-AUTH-021`（use-cases/UC-AUTH-021-manage-platform-administrators.md）：目标与范围、参与者与身份、输入与输出、API、主流程、错误语义与运行约束、测试与验收、实现依赖与联动、变更记录
- `UC-AUTH-002`（use-cases/UC-AUTH-002-batch-get-developer-statuses.md）：目标与范围、调用者与输入、输出、主流程、异常流程、数据模型、API 契约、测试与验收、非目标、变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：App Center 固定授权映射、账号归属退出方法、Application 关闭方法

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-010-issue-user-identity-from-session.md` | 145 | `c64b0cd24844` |
| `use-cases/UC-AUTH-022-disable-and-restore-user-account.md` | 183 | `f13eb70a5211` |
| `use-cases/UC-AUTH-021-manage-platform-administrators.md` | 207 | `c21e150ed9b5` |
| `use-cases/UC-AUTH-002-batch-get-developer-statuses.md` | 156 | `220a639a2f73` |
| `use-cases/UC-AUTH-007-login.md` | 252 | `3afbbd9047ae` |
| `platform/contracts/auth-device-session-v1.md` | 125 | `5ff17feb92f9` |
| `platform/contracts/auth-session-identity-issuance-v1.md` | 83 | `eb7024a3ea06` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `platform/contracts/trusted-service-identity-v1.md` | 124 | `4a64372bc9c0` |
