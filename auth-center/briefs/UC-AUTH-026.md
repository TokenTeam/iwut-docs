<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-026 --spec tools/brief-specs/UC-AUTH-026.json -->
# Brief — UC-AUTH-026：应用关闭授权收敛与近期认证

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-026` 应用关闭授权收敛与近期认证 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-OAU-022`–`BR-OAU-028`（7 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/application-close-reauth-proof-v1.md`、`platform/contracts/application-closure-v1.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

App Center 把 Application 不可逆地推进到 CLOSING 后，Auth Center 接受经过服务身份授权的关闭事实，持久建立 applicationId 级永久 tombstone，并让全部 OAuth/OIDC 授权消费路径在最终边界执行该栅栏；在关闭发起前，Auth 还为当前用户提供绑定 Application 的同设备新挑战，签发只能用于 `app.close` 的短期近期认证证明。

本用例负责：

- `ApplyApplicationClosure` / `GetApplicationClosureStatus` 的 Auth 提供方行为、幂等 receipt 和永久 tombstone；
- authorize、code exchange、token/refresh、UserInfo、revoke/introspection/delegation 路径的 application closure 最终检查；
- 当前 Session＋同一登记设备新 challenge/signature 的近期认证过程；
- 签发 audience=`iwut-app-center`、purpose=`app.close`、绑定 applicationId/sub/jti/auth_time 的 5 分钟 proof；
- Mongo schema、索引、服务身份、HTTP/native gRPC、限额、审计和真实跨服务验收。

本用例不负责 Application 的本地生命周期、管理员资格、配额、Publication、Tester、OAuth client slot 禁用、关闭确认 UI 或 App proof 消费；这些由 UC-APP-027 负责。它不扫描删除 grant/code/token，不撤销其他 Application，不关闭用户账号，不提供 Application 恢复、强制关闭或 tombstone 删除入口，也不把 applicationId 复用成另一个应用。

### 参与者与依赖

- **App Center closing worker**：通过受信 service JWS 提交已经本地生效的 applicationId、closureId 与 closingStartedAt。
- **当前用户**：使用有效 Session 所属的同一登记设备完成新挑战；Auth 不判断其是否是 Application 管理员。
- **OAuth/OIDC 入口**：UC014–019 的现有授权、token、UserInfo、撤销和委托路径消费 tombstone。
- **Auth Center**：拥有 Session、credential、OAuth 状态、Application sector/sub、proof signer、tombstone 和 receipt。

依赖已经满足：UC006–010 提供设备凭据、Session、设备签名和 signer 基础；UC014–019 提供 OAuth 事务与在线消费边界；UC022 提供 accountRevision 与 ACTIVE 最终检查；[Application 关闭协调 v1](../../platform/contracts/application-closure-v1.md) 和 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md) 固定跨服务格式。

### Application 关闭服务

内部 package `auth_center.v1.application_closure`、service `ApplicationClosureService` 仅提供原生 gRPC：

- `ApplyApplicationClosure(applicationId, closureId, closingStartedAt)`；
- `GetApplicationClosureStatus(applicationId, closureId)`。

两者严格实现共享契约。调用方必须是 App Center service identity，audience=`iwut-auth-center`，并分别具备 `auth.application-closure.apply` / `auth.application-closure.read`。USER identity、终端 Session、错误 audience、未知或禁用 caller、缺少精确 permission 均失败关闭。

Apply 首次成功在一个 Auth 事务中创建：

```text
ApplicationClosureTombstone {
  applicationId
  closureId
  closingStartedAt
  receiptId
  appliedAt
}
```

applicationId 和 closureId 各有唯一约束；同 applicationId＋closureId＋closingStartedAt 重试返回逐字段相同 APPLIED receipt。任一绑定不一致都作为冲突与安全/数据告警，不能覆盖旧记录。Get 只有 applicationId 与 closureId 同时匹配才返回；未知统一 NOT_FOUND。

Auth 不调用 App 复查关闭状态，也不能因为 App provider 暂时失败而自行建立 tombstone。App 的 Apply 是关闭事实唯一来源；服务身份和 App 已提交 CLOSING 是跨边界前提。

### 近期认证签发

用户入口 `BeginApplicationCloseReauth` / `CompleteApplicationCloseReauth` 同时提供 HTTP/JSON 与原生 gRPC，使用规范 `x-iwut-session`。Begin 在当前 Auth 边界确认 ACTIVE USER、有效 Session 和该 Session 引用的未撤销登记设备，创建最长 5 分钟的随机 challenge operation。

Complete 必须继续使用 Begin 的同一 Session，并由同一 credential 对共享契约固定 Frame 完成一条新 P-256/SHA-256 签名。Auth 在最终事务中复查账号、Session、credential、operation、applicationId、版本和期限，再把 operation 置为 COMPLETED并固定 proof claims。

签名成功时间是 `auth_time`；Session 的 issuedAt、createdAt、lastUsedAt 和普通 USER JWS `iat` 均不能代替。Auth 不在该入口调用 App 或验证管理员归属，以免把跨服务资格查询引入认证原子性；App 在消费 proof 时独立验证当前管理员和 Developer 状态。

proof 使用固定 audience `iwut-app-center`、purpose `app.close`、token_type `APP_CLOSE_REAUTH` 和独立 JOSE typ，绑定 sub、applicationId、jti、auth_time/iat/nbf/exp。TTL 5 分钟、时钟偏差 30 秒。完全相同 Complete 重试返回同一 jti 与同一 JWS，不生成第二份证明或延长期限。

### OAuth 与 OIDC 最终栅栏

tombstone 是 Auth 内 applicationId 级永久授权栅栏，不依赖 App provider 是否在线。下列现有入口必须在其最终权威读取或写事务边界查询 applicationId tombstone：

| 路径 | 最终检查与结果 |
| --- | --- |
| UC014 authorize/consent | 在创建/扩大 grant、创建 authorization interaction/code 的同一事务复查；存在 tombstone 时不写 grant/code，使用既有 OAuth 无效请求/应用不可用语义。 |
| UC015 code exchange | 在消费 code、建立 sector/sub、签发并持久化 token/family 的同一事务复查；存在 tombstone 时不消费 code、不返回 token。 |
| UC016 refresh | 在消费/旋转 family 与签发新 token 的同一事务复查；存在 tombstone 时旧 family 不再可用，失败不产生新一代。 |
| UC017 UserInfo | 在返回资料的最终权威读取边界复查；存在 tombstone 时 access token 不再可用。 |
| UC018 grant 查询/本人撤销/应用 token revoke | 本人撤销可继续幂等收紧历史状态；查询不得把 tombstone 应用显示为仍可授权，任何会创建/扩大可用授权的分支拒绝。 |
| UC019 introspection/delegation | 在判断 token 可用并签发委托 JWS 的最终事务边界复查；存在 tombstone 时不签发，既有 opaque access token在线无效。 |

入口预读 tombstone 可以提前失败，但不能替代上表最终检查。并发时若 OAuth 写事务先提交，随后 tombstone 仍使其结果不可用；若 Apply 事务先提交，所有后提交路径必须看见 tombstone 并失败。实现必须把 tombstone 与既有 Auth 全局 OAuth/认证协调边界放在同一 Mongo 事务可见性域，不允许一方使用不受栅栏保护的缓存。

已签发的离线 ID Token 或已经到达第三方的短期委托 JWS 仍受原离线验证窗口约束；本用例不能从第三方内存中收回它们。所有需要 Auth 在线判断的 code/access/refresh/UserInfo/delegation 在 tombstone 后立即失败。

### 持久化、审计与恢复

新增严格 collection `application_closure_tombstones`，至少包含 applicationId unique、closureId unique、receiptId unique 索引和 schema validator。记录永久保留，不提供 TTL、取消、删除或后台清理。

sector、pairwise sub、grant、code 和 token/family 历史可以按既有保留规则存在；tombstone 是其继续失效的权威原因。备份恢复必须与现有 Auth OAuth 数据一起恢复 tombstone；检测到有 closure receipt 的业务记录缺 tombstone、同 applicationId 多 closure 或 receipt 绑定不一致时拒绝接流量，不能以 App provider 当前失败重新推断。

近期认证 operation 使用现有认证短期数据设施，包含 operationId、authId、sessionId、credentialId、applicationId、用于重建验签 Frame 的 challenge32 原值、绑定 revision、失败计数、状态、固定 proof claims 和期限。challenge 按短期敏感认证数据保护且不进入日志、审计或通用查询；过期 operation 连同 challenge 一并清理。不保存 proof 原文或完整签名。成功审计记录 operationId、主体、credential 引用、applicationId、jti 和时间。

Apply 审计记录 applicationId、closureId、receiptId、closingStartedAt、appliedAt 和 caller；不记录 grant/token 数量、管理员、secret 或用户资料。审计与 tombstone 首次创建同事务提交；重复 Apply 不追加伪造的第二次业务事件。

### API、配置与错误

API 仓库新增两个独立 package：内部 `application_closure` 和用户侧 `application_close_reauth`。内部包不带 HTTP annotation；用户侧两个方法具备固定 HTTP annotation，Gateway 只按精确方法配置 SESSION 鉴权，不开放匿名或 USER JWS 旁路。

配置至少包括：

- `AUTH_APPLICATION_CLOSURE_ENABLED`：控制 Apply/Get 注册，默认 false；存在 tombstone 时关闭开关不得让 OAuth 忽略它。
- `AUTH_APPLICATION_CLOSE_REAUTH_ENABLED`：控制 Begin/Complete，默认 false。
- App service caller allowlist、固定 audience 与两项精确 permission。
- proof issuer/signing key、固定 audience；启动时验证与 App trusted key/audience 配置一致。
- Begin/Complete 的有界来源/账号限额，默认每账号每分钟 10 次写、最多 5 个未过期 operation、每 operation 最多 5 次失败。

关闭公网 proof 入口不停止已有 tombstone 生效，也不允许省略启动时 schema/index/一致性检查。若数据库存在 tombstone 而运行代码没有注册 OAuth gate，则启动失败；不能以配置未启用为由恢复已关闭 Application。

稳定错误：参数非法 INVALID_ARGUMENT；身份无效 UNAUTHENTICATED；caller/permission 不允许 PERMISSION_DENIED；未知 Get NOT_FOUND；tombstone 绑定冲突 ALREADY_EXISTS；proof 限额 RESOURCE_EXHAUSTED；暂时依赖/提交未知 UNAVAILABLE；不变量损坏 INTERNAL。OAuth 公网入口沿用各 UC 的标准错误，不披露 tombstone、关闭时间、管理员或 receipt。

### 验收场景

至少覆盖：

1. 首次 Apply、完全相同重试和 Get 返回同一 receipt；applicationId/closureId/time 任一冲突失败。
2. service JWS 的错误 caller/audience/permission/kid/时间、USER JWS 和 HTTP/gRPC-Web 调用内部服务全部拒绝。
3. tombstone 与 UC014 authorize、UC015 exchange、UC016 refresh、UC019 delegation 并发的两个胜序；不产生墓碑之后仍可在线使用的凭据。
4. tombstone 前签发的 code、access、refresh family 在各自入口失败；UserInfo/delegation失败；本人 revoke 保持幂等收紧。
5. App provider 故障不创建 tombstone；已有 tombstone 时 provider 恢复不复活授权。
6. 同一登记设备的新 challenge 签名成功；只有 Session/USER JWS、另一设备、旧 LOGIN 或 account-close 签名失败。
7. Begin 后禁用账号、撤销 Session/credential、revision 或 applicationId 变化，Complete 原子失败且不签 proof。
8. Complete 响应丢失和重试返回同一 jti/JWS/exp；跨 application/subject/closure 重放由 App 拒绝。
9. proof 的 typ/token_type/purpose/audience/auth_time/TTL/偏差完整验证，challenge/signature/proof 不进入日志、审计或缓存。
10. 真实 Mongo transaction/unknown commit、进程重启、索引/validator 升级和备份恢复损坏检查。
11. 真实 Auth/API HTTP/native gRPC、实际 App UC027 worker Apply/Get 与关闭 proof 消费联合验收；不以进程内 fake provider 代替。

### 实现依赖与交付边界

实现顺序建议：独立 API 两个 package与生成物；Auth tombstone domain/repository/usecase/service；UC014–019 最终 gate；reauth challenge/proof signer；production Wire/config；真实 Mongo 与实际 App 联合验收。可复用既有 Mongo transaction runner、全局认证/OAuth fence、设备签名 verifier、Session repository、RS256 keyring 和 trusted service middleware，不复制第二套身份/credential 存储。

Auth/API 后端交付完成不等于 UC-APP-027 已完成，也不自动启用终端入口。App 必须实现生命周期、proof 消费和 durable worker；Gateway 必须显式配置两个 DIRECT 路由；生产需配置 service allowlist、签名轮换、时钟和监控。离线第三方 JWT/会话的残余窗口保持各原契约边界。

## 业务规则（UC-AUTH-026 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-022 -->
### BR-OAU-022：永久 Application 授权墓碑

合法 Apply 为 applicationId 创建唯一、不可取消、不可删除的永久 tombstone。applicationId、closureId、closingStartedAt 和 receipt 一经绑定不可改变；相同请求幂等，不一致请求冲突。Application、sector 和既有 pairwise sub 不得借关闭后重新分配或复活。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-023 -->
### BR-OAU-023：全部 OAuth 路径的最终闭合

authorize、grant 扩大、code 签发/消费、token/refresh、UserInfo 和 introspection/delegation 必须在最终权威边界复查 tombstone。provider 可用、旧 grant/code/token/family 尚在或本地缓存命中都不能绕过。本人撤销可以继续收紧历史状态，但不能形成新授权。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-024 -->
### BR-OAU-024：服务身份、幂等回执与未知结果

只有具备精确 permission 的 App service identity 能 Apply/Get。首次 tombstone 与 receipt 同事务持久化；响应丢失后相同 Apply 或 Get 返回稳定 APPLIED。Auth 不能从 provider 错误猜测关闭，App 也不能把超时当作 APPLIED。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-025 -->
### BR-OAU-025：同设备新挑战证明近期认证

app.close proof 必须来自有效 Session 所属同一登记设备对全新 challenge 的用途隔离签名。普通 USER JWS、Session 时间、另一个设备、旧登录/注销签名或 UI confirmation 均不满足近期认证。Complete 在最终事务复查 ACTIVE account、Session、credential、revision 和 operation 绑定。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-026 -->
### BR-OAU-026：Proof 最小权力与固定时限

proof 仅面向 iwut-app-center、仅用于 app.close，绑定一个 sub、applicationId 和 jti；auth_time 是新签名成功时间。proof 固定 5 分钟寿命、30 秒偏差，不刷新、不改变 Application、不授予管理员身份，App 必须另行完成业务授权。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-027 -->
### BR-OAU-027：Proof 幂等与单次业务消费

相同 Complete 只得到一个固定 jti 和不延长的相同 JWS。App 在关闭事务内把 jti 唯一绑定同一 subject、applicationId 和 closureId；同一关闭的网络重试返回既有结果，跨主体、Application、purpose 或 closure 重放失败。Auth 不维护跨服务消费回调。

<!-- 权威位置: use-cases/UC-AUTH-026-apply-application-closure.md#br-oau-028 -->
### BR-OAU-028：并发、故障关闭与审计边界

Apply 与全部 OAuth 最终消费共享事务可见的协调边界；proof Complete 与账号/Session/credential 变更共享认证协调边界。依赖、签名或存储结果未知时失败关闭，不返回未持久化 receipt/proof。审计保存稳定 ID 与时间，不保存 challenge、signature、proof、token、secret 或用户资料。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/application-close-reauth-proof-v1.md`：Application 关闭近期认证证明 v1

#### 目的与边界

本契约定义用户在关闭一个 Application 前，如何用当前 Session 所属的同一登记设备完成一次新的 challenge/signature，并由 Auth Center 签发只能交给 App Center、只能用于该 Application 关闭的短期 JWS。

普通 USER JWS 的 `iat` 表示可信身份何时签发，不表示用户刚刚重新证明设备私钥控制权。前端确认框、Session 最近使用时间、密码输入字符串和已有 OAuth token 也不能代替本文证明。

Auth Center 拥有 Session、设备凭据、新挑战、签发密钥和 proof claims；App Center 验证 proof，并把 `jti` 唯一绑定到 ApplicationClosure。本契约不授予 Application 管理权；App 仍须依据 UC-APP-027 复查当前管理员、Developer 状态和 revision。

#### 签发入口

独立 package `auth_center.v1.application_close_reauth`，service `ApplicationCloseReauthService`。两个入口同时提供 HTTP/JSON 与原生 gRPC，由 Gateway DIRECT 转发；均要求规范 `x-iwut-session`，不接受 USER JWS、OAuth token 或 service JWS 替代。

```proto
message BeginApplicationCloseReauthRequest {
  string application_id = 1;
}

message BeginApplicationCloseReauthResponse {
  string operation_id = 1;
  bytes challenge = 2;
  google.protobuf.Timestamp expires_at = 3;
}

message CompleteApplicationCloseReauthRequest {
  string operation_id = 1;
  string application_id = 2;
  bytes signature_der = 3;
}

message CompleteApplicationCloseReauthResponse {
  string proof_jws = 1;
  google.protobuf.Timestamp expires_at = 2;
}
```

建议 HTTP 路由：

| 方法 | 路由 |
| --- | --- |
| `BeginApplicationCloseReauth` | `POST /v1/application-close-reauth:begin` |
| `CompleteApplicationCloseReauth` | `POST /v1/application-close-reauth:complete` |

请求与响应均 `Cache-Control: no-store`，不得出现在 URL query、Referer、普通日志或审计 payload 中。`application_id` 与 `operation_id` 使用规范 UUID 文本；challenge 固定 32 个随机字节；DER signature 使用登记设备 P-256/SHA-256 的严格最短编码。

#### 新挑战和设备签名

Begin 必须在 Auth 当前权威边界确认：

- Session 当前有效且属于 ACTIVE USER；
- Session 引用的同一登记设备凭据存在、未撤销，且账号、凭据、Session revision 仍匹配；
- applicationId 格式合法；Auth 不在此判断调用者是不是该 Application 的管理员。

Auth 保存 operationId、authId、sessionId、credentialId、applicationId、challenge32 原值、账号/凭据版本、创建时间、过期时间和失败计数。challenge 按短期敏感认证数据保护，只能用于重建待验签 Frame，不进入日志、审计或通用查询；operation 清理时一并删除。operation 最长 5 分钟；每个 operation 最多 5 次失败验证。每个账号同时最多 5 个未过期 operation，超额拒绝而不驱逐已完成结果。

客户端用 Session 所属设备私钥签名：

```text
Frame(
  UTF8("iwut-application-close-reauth-v1"),
  UTF8("COMPLETE_APPLICATION_CLOSE_REAUTH"),
  UUIDBytes(operationId),
  UUIDBytes(applicationId),
  challenge32
)
```

`Frame(part...) = concat(U32BE(len(part)), part)`。UUIDBytes 是 RFC 4122 网络字节序的 16 字节值。签名算法、低 S 规范化、公钥编码和 DER 严格校验沿用 [App 设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)，但 domain/action 与其他设备证明完全隔离。

Complete 必须携带 Begin 时的同一 Session。Auth 在最终事务中重新确认 Session、账号、凭据、版本、operation 绑定和未过期，再验证 signature。Session、credential、authId 或 applicationId 任一漂移都失败；不能把另一个有效设备或同账号另一条 Session 替换进已有 operation。

#### Proof JWS

成功 Complete 返回 compact JWS。JOSE header：

```json
{
  "alg": "RS256",
  "kid": "<auth-key-id>",
  "typ": "iwut-app-close-reauth+jwt"
}
```

payload 必须包含：

```json
{
  "iss": "<configured-auth-issuer>",
  "aud": "iwut-app-center",
  "sub": "<authId>",
  "token_type": "APP_CLOSE_REAUTH",
  "purpose": "app.close",
  "application_id": "<applicationId>",
  "jti": "<UUIDv7>",
  "auth_time": 0,
  "iat": 0,
  "nbf": 0,
  "exp": 0
}
```

`auth_time` 是 Auth 成功验证本次新设备签名的时间，不得取 Session 创建/使用时间；`iat` 与 `auth_time` 相同。`nbf = iat - 30s`，`exp = iat + 5m`。签发后不允许刷新或换取新 proof；过期后必须重新 Begin/Complete。

签名密钥可以与 Auth 的可信用户身份签发共用轮换设施，但 verifier 必须按精确 `typ`、`token_type`、audience 和 purpose 分派，不能把该 proof 当 USER identity，反向也不能把 USER identity 当 proof。

#### 幂等、重放与消费

首次成功 Complete 在同一 Auth 事务中把 operation 置为 COMPLETED，并固定 `jti/auth_time/iat/nbf/exp`。完全相同 operation、applicationId、Session 和签名的重试返回同一 claims 和逐字节相同 JWS；不得签发第二个 jti 或延长期限。实现可持久化固定 claims 并按规范编码重签，不需要保存 proof 明文。

已完成 operation 的不同签名、不同 Session 或不同 applicationId 均拒绝。未完成 operation 的签名失败只递增有界失败计数，不生成 proof。

App 验证签名、issuer、固定 audience、typ、token_type、purpose、applicationId、subject、时间和 `jti`。允许最大 30 秒时钟偏差，但 proof 的总寿命仍固定 5 分钟；App 接受时还要求 `now - auth_time <= 5m`。

App 在 UC-APP-027 的本地关闭事务中唯一消费 `jti`：

- 首次消费只能绑定一个 applicationId、subject 和 closureId；
- 同一 `jti` 对同一 ApplicationClosure 的网络重试返回既有 CLOSING/CLOSED 结果；
- 跨 Application、跨 subject、跨 purpose 或绑定另一个 closureId 一律按重放拒绝；
- 只在关闭事务成功时提交消费记录，事务回滚不能永久烧掉 proof。

Auth 不回调 App 查询 `jti` 是否消费；App 不向 Auth 声称 proof 已使用。短寿命、App 唯一约束和业务绑定共同提供重放边界。

#### 错误、限额与隐私

- 非法字段、UUID、长度或 DER：HTTP 400 / INVALID_ARGUMENT。
- Session、operation、签名或绑定无效以及过期：统一 HTTP 401 / UNAUTHENTICATED；未经证明不能区分账号、凭据或 operation 状态。
- 账号级限额：HTTP 429 / RESOURCE_EXHAUSTED，并提供有界 Retry-After。
- 持久化或签名服务暂不可用：HTTP 503 / UNAVAILABLE；不能返回未持久化的 proof。
- 记录损坏、已完成 claims 不一致：HTTP 500 / INTERNAL。

proof、challenge 和 signature 不进入业务审计。Auth 审计只记录 operationId、authId、credentialId、applicationId、结果类别、jti（成功时）和时间；App 审计只保存 proof jti，不保存 proof 原文。短期 operation 在过期后按既有认证挑战清理机制删除；已消费 jti 的永久/长期保留由 ApplicationClosure 审计拥有。

#### 兼容与验收

v1 允许追加可选响应字段；改变 domain/action、Frame 顺序、签名算法、固定 audience/purpose、5 分钟上限或消费键需要新版本。

双方至少覆盖：

1. 同一登记设备的新签名成功，只有 Session、USER JWS、旧登录签名或另一设备签名失败。
2. Begin 后账号禁用、Session/credential 撤销、revision 变化或 applicationId 改写时 Complete 失败。
3. Complete 提交后响应丢失，重试返回同一 jti、时间和 JWS；不延长 exp。
4. 错误 issuer/audience/typ/token_type/purpose/sub/applicationId、未来 auth_time、过期和超过允许时钟差均被 App 拒绝。
5. App 关闭事务失败后 proof 可在原期限内重试；事务成功后的同 closure 重试幂等，跨 closure/application/subject 重放失败。
6. challenge/签名/proof 不进 URL、普通日志、审计或缓存；限额与失败计数有界。

### `platform/contracts/application-closure-v1.md`：Application 关闭协调 v1

#### 目的与边界

本契约定义 App Center 在 Application 进入不可逆 `CLOSING` 后，如何要求 Auth Center 建立永久的 applicationId 级授权撤销事实，并在未知结果、重试和进程重启后收敛。

App Center 是 Application 生命周期、Publication、OAuth registration 和关闭流程的权威；Auth Center 是 consent grant、authorization code、token family、sector、pairwise sub 及授权执行的权威。双方不共享数据库，也不把远程调用放进本地事务。

本契约不定义用户发起关闭的公网 API、账号关闭或平台强制关闭。近期重新认证格式见 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md)。

#### 服务身份

仅提供原生 gRPC，不提供 HTTP annotation、gRPC-Web 或终端路由。

```text
package auth_center.v1.application_closure
service ApplicationClosureService
```

App→Auth 使用 [Trusted Service Identity v1](../../platform/contracts/trusted-service-identity-v1.md)、固定 audience `iwut-auth-center` 和 Auth 本地 App caller allowlist：

| 方法 | permission |
| --- | --- |
| `ApplyApplicationClosure` | `auth.application-closure.apply` |
| `GetApplicationClosureStatus` | `auth.application-closure.read` |

USER identity、未知 key、错误 audience、禁用 caller、缺少精确 permission 或过期 service JWS 一律失败关闭。Auth 不能接受终端自报的 applicationId/closureId。

#### RPC 草图

```proto
message ApplyApplicationClosureRequest {
  string application_id = 1;
  string closure_id = 2;
  google.protobuf.Timestamp closing_started_at = 3;
}

message GetApplicationClosureStatusRequest {
  string application_id = 1;
  string closure_id = 2;
}

enum ApplicationClosureState {
  APPLICATION_CLOSURE_STATE_UNSPECIFIED = 0;
  APPLICATION_CLOSURE_STATE_APPLIED = 1;
}

message ApplicationClosureStatus {
  string application_id = 1;
  string closure_id = 2;
  ApplicationClosureState state = 3;
  string receipt_id = 4;
  google.protobuf.Timestamp applied_at = 5;
}
```

`ApplyApplicationClosure` 成功只返回 APPLIED，不暴露内部扫描、grant 数量、用户数量或 token 数量。`GetApplicationClosureStatus` 返回相同资源。

#### Auth 持久事实

Auth 保存以 applicationId 唯一的永久 application closure tombstone，至少包含 applicationId、closureId、closingStartedAt、receiptId、appliedAt。约束如下：

- 第一次合法 Apply 原子创建 tombstone 和稳定 receipt。
- 相同 applicationId、closureId 和 closingStartedAt 的重复 Apply 返回原结果。
- 相同 applicationId/closureId 但 closingStartedAt 不同，或相同 applicationId 使用不同 closureId，返回冲突并记录安全/数据告警。
- Get 的 applicationId、closureId 必须同时匹配；未知记录返回 NOT_FOUND，不能推断为“尚未应用”以外的更多事实。
- tombstone 不过期、不可取消、不可删除；Application ID、sector 和既有 pairwise sub 映射不得复用。

Auth 无需扫描改写每条 grant/code/token。所有相关用例必须在最终事务或最终权威读取边界复查 tombstone，使它成为 applicationId 级撤销栅栏。

#### Auth 执行语义

tombstone 存在后，Auth 必须阻止：

- 创建或扩大该 Application 任一 channel 的用户授权；
- 签发和消费 authorization code；
- 通过 code 或 refresh token 签发 access token、ID token、refresh token；
- 使用任何既有 refresh token family；
- 在线 introspection/delegation 把该 Application 的既有 token 判断为可用。

失败应使用现有 OAuth/OIDC 对外错误语义，不能向终端泄露关闭时间、管理员或内部 tombstone。历史 grant、code、token family、sector 与 sub 可以继续保存供审计；它们不因保留而重新有效。

App 的 OAuth provider 暂时不可用或返回 Application 不可运行，不能替代 tombstone。Auth 也不能根据一次 provider 调用失败自行推断永久关闭，因为失败还可能来自网络、临时依赖或数据错误。

#### 错误与兼容

- 参数格式错误：INVALID_ARGUMENT。
- service identity 无效：UNAUTHENTICATED。
- caller 或 permission 不允许：PERMISSION_DENIED。
- Get 无匹配记录：NOT_FOUND。
- 既有 applicationId/closureId/时间绑定冲突：ALREADY_EXISTS 或 FAILED_PRECONDITION；实现必须固定一种 reason 供契约测试。
- Auth 暂时无法提交持久事实：UNAVAILABLE。
- tombstone 或 receipt 数据不变量损坏：INTERNAL。

v1 只允许追加可选字段和新的只读方法。改变幂等键、允许取消、缩短永久保留、把 APPLIED 拆成可回退状态或削弱最终 tombstone 检查都需要新版本。

#### 验收矩阵

双方契约测试至少覆盖：

1. 首次 Apply、相同请求重复 Apply 和 Get 返回完全相同 receipt。
2. 相同 applicationId 使用不同 closureId、相同 closureId 使用不同时间的冲突。
3. Apply 已提交但响应丢失、Get 已提交但响应丢失、App/Auth 任一侧重启。
4. USER JWS、错误 audience、未知/禁用 caller、错误 permission 和过期 service JWS。
5. tombstone 前取得的 code、access token、refresh family 在 tombstone 后全部按对应入口失败。
6. tombstone 后并发 authorize/exchange/refresh/delegation 的最终事务复查，不能产生晚到的有效凭证。
7. provider 暂时不可用不创建 tombstone；已有 tombstone 时 provider 恢复也不能重新授权。
8. 历史 sector/sub/grant 保留但 applicationId 永不复用。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### 基础编码

- `UTF8(s)` 是字符串的 UTF-8 字节，不添加 BOM、终止符或隐式 Unicode 规范化。
- `LP(b) = U32BE(len(b)) || b`；长度为字节数，U32BE 是 4 字节无符号大端整数。`Frame(b1,...,bn)` 为依次连接各 LP，无额外分隔符或字段数量。每种消息固定字段数量，拒绝尾随数据、截断及超过上限的字段。
- `B64U(b)` 为 RFC 4648 URL-safe Base64，无 `=` 填充。解码必须严格并满足重新编码逐字相等，不接受空白、标准 Base64 的 `+`/`/` 或非零尾部填充位。
- 下述 Proto `bytes` 字段传原始字节；JSON 映射遵循 Proto 标准。文档向量的 hex 仅为测试展示，不能作为线上 bytes 字段的另一种编码。
- 新 operationId、credentialId、sessionId 使用小写标准连字符 UUIDv4；authId 沿用主体的 opaque 标识语义，不能由客户端指定或从学号派生。
- 时间采用 UTC Unix 毫秒；签名输入中为 8 字节无符号大端整数。服务端使用整数毫秒创建挑战并持久化，避免 Proto 与 MongoDB 精度转换改变签名。时间过期规则仍由 UC 拥有。

#### 公钥与签名

`protocolVersion = "iwut-device-v1"`，唯一支持的算法为 ECDSA P-256（secp256r1）配合 SHA-256。

公钥使用固定 65 字节未压缩 SEC1 / X9.63 点编码：`0x04 || X[32] || Y[32]`，坐标为无符号大端、保留左侧零字节。拒绝压缩点、PEM、SPKI、其它曲线、无穷点和不在 P-256 曲线上的坐标。Android 的 SPKI 公钥需要在客户端提取坐标转换，不能直接上传证书或 SubjectPublicKeyInfo。

规范公钥指纹为 32 字节：

```text
fingerprint = SHA256(Frame(UTF8("iwut-device-public-key-v1"), publicKey65))
```

`CredentialRegistrationProposal` 的具体字段为 `protocolVersion: string` 与 `publicKey: bytes`。两类 proof 均只有 `signature: bytes`；服务器从 operation 快照取得算法、公钥及待签消息，不接受 Complete 指定新算法、公钥或可信布尔值。

签名为对完整 signingPayload 做一次 SHA-256 后的 ECDSA，在线格式是严格 ASN.1 DER `SEQUENCE(INTEGER r, INTEGER s)`。要求最短 DER、无尾随字节、`1 <= r,s < curveOrder`，最多 72 字节。接受合法 high-S 和 low-S，不把签名字节当幂等键；一次性消费依据 operationId。Android 可使用 `SHA256withECDSA` 对原始 payload 签名；CryptoKit 使用对 Data 签名的 API 并导出 `derRepresentation`。调用会自行哈希的 API 时不得先手动哈希一次。

选型依据：[Apple SecureEnclave P-256 签名](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing)、[Apple P256 公钥表示](https://developer.apple.com/documentation/cryptokit/p256/signing/publickey)、[Android KeyGenParameterSpec 的 P-256 / SHA256withECDSA 示例](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec)。客户端优先使用系统密钥设施，不要求用户认证标志；具体设备不可用时明确报错或采用经客户端验证的系统安全存储方案，不把私钥写入普通业务存储。

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。UC020 独立入口的缺失/畸形或混用载体为 INVALID_SESSION_TOKEN（400），载体合法但当前资格失效为 SESSION_INVALID（401），不得沿用 UC008 的免有效性检查。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

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

- `UC-AUTH-026`（use-cases/UC-AUTH-026-apply-application-closure.md）：变更记录
- `platform/contracts/application-close-reauth-proof-v1.md`（docs 根级共享文档）：权威用例
- `platform/contracts/application-closure-v1.md`（docs 根级共享文档）：先决条件与生效点、投递、查询与收敛、权威用例
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：App Center 固定授权映射、ENV 配置、账号归属退出方法、Application 关闭方法

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-026-apply-application-closure.md` | 167 | `0e5af4dcd172` |
| `platform/contracts/application-close-reauth-proof-v1.md` | 152 | `1e16aa4fe484` |
| `platform/contracts/application-closure-v1.md` | 135 | `05e04ba6d669` |
| `platform/contracts/auth-device-session-v1.md` | 125 | `5ff17feb92f9` |
| `platform/contracts/trusted-service-identity-v1.md` | 124 | `4a64372bc9c0` |
