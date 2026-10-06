# UC-AUTH-026：应用关闭授权收敛与近期认证

状态：`ACCEPTED`

## 目标与范围

App Center 把 Application 不可逆地推进到 CLOSING 后，Auth Center 接受经过服务身份授权的关闭事实，持久建立 applicationId 级永久 tombstone，并让全部 OAuth/OIDC 授权消费路径在最终边界执行该栅栏；在关闭发起前，Auth 还为当前用户提供绑定 Application 的同设备新挑战，签发只能用于 `app.close` 的短期近期认证证明。

本用例负责：

- `ApplyApplicationClosure` / `GetApplicationClosureStatus` 的 Auth 提供方行为、幂等 receipt 和永久 tombstone；
- authorize、code exchange、token/refresh、UserInfo、revoke/introspection/delegation 路径的 application closure 最终检查；
- 当前 Session＋同一登记设备新 challenge/signature 的近期认证过程；
- 签发 audience=`iwut-app-center`、purpose=`app.close`、绑定 applicationId/sub/jti/auth_time 的 5 分钟 proof；
- Mongo schema、索引、服务身份、HTTP/native gRPC、限额、审计和真实跨服务验收。

本用例不负责 Application 的本地生命周期、管理员资格、配额、Publication、Tester、OAuth client slot 禁用、关闭确认 UI 或 App proof 消费；这些由 UC-APP-027 负责。它不扫描删除 grant/code/token，不撤销其他 Application，不关闭用户账号，不提供 Application 恢复、强制关闭或 tombstone 删除入口，也不把 applicationId 复用成另一个应用。

## 参与者与依赖

- **App Center closing worker**：通过受信 service JWS 提交已经本地生效的 applicationId、closureId 与 closingStartedAt。
- **当前用户**：使用有效 Session 所属的同一登记设备完成新挑战；Auth 不判断其是否是 Application 管理员。
- **OAuth/OIDC 入口**：UC014–019 的现有授权、token、UserInfo、撤销和委托路径消费 tombstone。
- **Auth Center**：拥有 Session、credential、OAuth 状态、Application sector/sub、proof signer、tombstone 和 receipt。

依赖已经满足：UC006–010 提供设备凭据、Session、设备签名和 signer 基础；UC014–019 提供 OAuth 事务与在线消费边界；UC022 提供 accountRevision 与 ACTIVE 最终检查；[Application 关闭协调 v1](../../platform/contracts/application-closure-v1.md) 和 [Application 关闭近期认证证明 v1](../../platform/contracts/application-close-reauth-proof-v1.md) 固定跨服务格式。

## Application 关闭服务

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

## 近期认证签发

用户入口 `BeginApplicationCloseReauth` / `CompleteApplicationCloseReauth` 同时提供 HTTP/JSON 与原生 gRPC，使用规范 `x-iwut-session`。Begin 在当前 Auth 边界确认 ACTIVE USER、有效 Session 和该 Session 引用的未撤销登记设备，创建最长 5 分钟的随机 challenge operation。

Complete 必须继续使用 Begin 的同一 Session，并由同一 credential 对共享契约固定 Frame 完成一条新 P-256/SHA-256 签名。Auth 在最终事务中复查账号、Session、credential、operation、applicationId、版本和期限，再把 operation 置为 COMPLETED并固定 proof claims。

签名成功时间是 `auth_time`；Session 的 issuedAt、createdAt、lastUsedAt 和普通 USER JWS `iat` 均不能代替。Auth 不在该入口调用 App 或验证管理员归属，以免把跨服务资格查询引入认证原子性；App 在消费 proof 时独立验证当前管理员和 Developer 状态。

proof 使用固定 audience `iwut-app-center`、purpose `app.close`、token_type `APP_CLOSE_REAUTH` 和独立 JOSE typ，绑定 sub、applicationId、jti、auth_time/iat/nbf/exp。TTL 5 分钟、时钟偏差 30 秒。完全相同 Complete 重试返回同一 jti 与同一 JWS，不生成第二份证明或延长期限。

## OAuth 与 OIDC 最终栅栏

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

## 持久化、审计与恢复

新增严格 collection `application_closure_tombstones`，至少包含 applicationId unique、closureId unique、receiptId unique 索引和 schema validator。记录永久保留，不提供 TTL、取消、删除或后台清理。

sector、pairwise sub、grant、code 和 token/family 历史可以按既有保留规则存在；tombstone 是其继续失效的权威原因。备份恢复必须与现有 Auth OAuth 数据一起恢复 tombstone；检测到有 closure receipt 的业务记录缺 tombstone、同 applicationId 多 closure 或 receipt 绑定不一致时拒绝接流量，不能以 App provider 当前失败重新推断。

近期认证 operation 使用现有认证短期数据设施，包含 operationId、authId、sessionId、credentialId、applicationId、用于重建验签 Frame 的 challenge32 原值、绑定 revision、失败计数、状态、固定 proof claims 和期限。challenge 按短期敏感认证数据保护且不进入日志、审计或通用查询；过期 operation 连同 challenge 一并清理。不保存 proof 原文或完整签名。成功审计记录 operationId、主体、credential 引用、applicationId、jti 和时间。

Apply 审计记录 applicationId、closureId、receiptId、closingStartedAt、appliedAt 和 caller；不记录 grant/token 数量、管理员、secret 或用户资料。审计与 tombstone 首次创建同事务提交；重复 Apply 不追加伪造的第二次业务事件。

## 业务规则

<a id="br-oau-022"></a>
### BR-OAU-022：永久 Application 授权墓碑

合法 Apply 为 applicationId 创建唯一、不可取消、不可删除的永久 tombstone。applicationId、closureId、closingStartedAt 和 receipt 一经绑定不可改变；相同请求幂等，不一致请求冲突。Application、sector 和既有 pairwise sub 不得借关闭后重新分配或复活。

<a id="br-oau-023"></a>
### BR-OAU-023：全部 OAuth 路径的最终闭合

authorize、grant 扩大、code 签发/消费、token/refresh、UserInfo 和 introspection/delegation 必须在最终权威边界复查 tombstone。provider 可用、旧 grant/code/token/family 尚在或本地缓存命中都不能绕过。本人撤销可以继续收紧历史状态，但不能形成新授权。

<a id="br-oau-024"></a>
### BR-OAU-024：服务身份、幂等回执与未知结果

只有具备精确 permission 的 App service identity 能 Apply/Get。首次 tombstone 与 receipt 同事务持久化；响应丢失后相同 Apply 或 Get 返回稳定 APPLIED。Auth 不能从 provider 错误猜测关闭，App 也不能把超时当作 APPLIED。

<a id="br-oau-025"></a>
### BR-OAU-025：同设备新挑战证明近期认证

app.close proof 必须来自有效 Session 所属同一登记设备对全新 challenge 的用途隔离签名。普通 USER JWS、Session 时间、另一个设备、旧登录/注销签名或 UI confirmation 均不满足近期认证。Complete 在最终事务复查 ACTIVE account、Session、credential、revision 和 operation 绑定。

<a id="br-oau-026"></a>
### BR-OAU-026：Proof 最小权力与固定时限

proof 仅面向 iwut-app-center、仅用于 app.close，绑定一个 sub、applicationId 和 jti；auth_time 是新签名成功时间。proof 固定 5 分钟寿命、30 秒偏差，不刷新、不改变 Application、不授予管理员身份，App 必须另行完成业务授权。

<a id="br-oau-027"></a>
### BR-OAU-027：Proof 幂等与单次业务消费

相同 Complete 只得到一个固定 jti 和不延长的相同 JWS。App 在关闭事务内把 jti 唯一绑定同一 subject、applicationId 和 closureId；同一关闭的网络重试返回既有结果，跨主体、Application、purpose 或 closure 重放失败。Auth 不维护跨服务消费回调。

<a id="br-oau-028"></a>
### BR-OAU-028：并发、故障关闭与审计边界

Apply 与全部 OAuth 最终消费共享事务可见的协调边界；proof Complete 与账号/Session/credential 变更共享认证协调边界。依赖、签名或存储结果未知时失败关闭，不返回未持久化 receipt/proof。审计保存稳定 ID 与时间，不保存 challenge、signature、proof、token、secret 或用户资料。

## API、配置与错误

API 仓库新增两个独立 package：内部 `application_closure` 和用户侧 `application_close_reauth`。内部包不带 HTTP annotation；用户侧两个方法具备固定 HTTP annotation，Gateway 只按精确方法配置 SESSION 鉴权，不开放匿名或 USER JWS 旁路。

配置至少包括：

- `AUTH_APPLICATION_CLOSURE_ENABLED`：控制 Apply/Get 注册，默认 false；存在 tombstone 时关闭开关不得让 OAuth 忽略它。
- `AUTH_APPLICATION_CLOSE_REAUTH_ENABLED`：控制 Begin/Complete，默认 false。
- App service caller allowlist、固定 audience 与两项精确 permission。
- proof issuer/signing key、固定 audience；启动时验证与 App trusted key/audience 配置一致。
- Begin/Complete 的有界来源/账号限额，默认每账号每分钟 10 次写、最多 5 个未过期 operation、每 operation 最多 5 次失败。

关闭公网 proof 入口不停止已有 tombstone 生效，也不允许省略启动时 schema/index/一致性检查。若数据库存在 tombstone 而运行代码没有注册 OAuth gate，则启动失败；不能以配置未启用为由恢复已关闭 Application。

稳定错误：参数非法 INVALID_ARGUMENT；身份无效 UNAUTHENTICATED；caller/permission 不允许 PERMISSION_DENIED；未知 Get NOT_FOUND；tombstone 绑定冲突 ALREADY_EXISTS；proof 限额 RESOURCE_EXHAUSTED；暂时依赖/提交未知 UNAVAILABLE；不变量损坏 INTERNAL。OAuth 公网入口沿用各 UC 的标准错误，不披露 tombstone、关闭时间、管理员或 receipt。

## 验收场景

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

## 实现依赖与交付边界

实现顺序建议：独立 API 两个 package与生成物；Auth tombstone domain/repository/usecase/service；UC014–019 最终 gate；reauth challenge/proof signer；production Wire/config；真实 Mongo 与实际 App 联合验收。可复用既有 Mongo transaction runner、全局认证/OAuth fence、设备签名 verifier、Session repository、RS256 keyring 和 trusted service middleware，不复制第二套身份/credential 存储。

Auth/API 后端交付完成不等于 UC-APP-027 已完成，也不自动启用终端入口。App 必须实现生命周期、proof 消费和 durable worker；Gateway 必须显式配置两个 DIRECT 路由；生产需配置 service allowlist、签名轮换、时钟和监控。离线第三方 JWT/会话的残余窗口保持各原契约边界。

## 变更记录

- 2026-10-06：接受首版设计；固定永久 applicationId tombstone、UC014–019 最终栅栏、App service 幂等回执，以及当前 Session 同一登记设备新挑战换取 5 分钟 app.close proof。
