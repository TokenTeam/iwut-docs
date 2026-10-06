# Application 关闭近期认证证明 v1

状态：`ACCEPTED`

## 目的与边界

本契约定义用户在关闭一个 Application 前，如何用当前 Session 所属的同一登记设备完成一次新的 challenge/signature，并由 Auth Center 签发只能交给 App Center、只能用于该 Application 关闭的短期 JWS。

普通 USER JWS 的 `iat` 表示可信身份何时签发，不表示用户刚刚重新证明设备私钥控制权。前端确认框、Session 最近使用时间、密码输入字符串和已有 OAuth token 也不能代替本文证明。

Auth Center 拥有 Session、设备凭据、新挑战、签发密钥和 proof claims；App Center 验证 proof，并把 `jti` 唯一绑定到 ApplicationClosure。本契约不授予 Application 管理权；App 仍须依据 UC-APP-027 复查当前管理员、Developer 状态和 revision。

## 签发入口

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

## 新挑战和设备签名

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

`Frame(part...) = concat(U32BE(len(part)), part)`。UUIDBytes 是 RFC 4122 网络字节序的 16 字节值。签名算法、低 S 规范化、公钥编码和 DER 严格校验沿用 [App 设备认证与 Session v1](auth-device-session-v1.md)，但 domain/action 与其他设备证明完全隔离。

Complete 必须携带 Begin 时的同一 Session。Auth 在最终事务中重新确认 Session、账号、凭据、版本、operation 绑定和未过期，再验证 signature。Session、credential、authId 或 applicationId 任一漂移都失败；不能把另一个有效设备或同账号另一条 Session 替换进已有 operation。

## Proof JWS

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

## 幂等、重放与消费

首次成功 Complete 在同一 Auth 事务中把 operation 置为 COMPLETED，并固定 `jti/auth_time/iat/nbf/exp`。完全相同 operation、applicationId、Session 和签名的重试返回同一 claims 和逐字节相同 JWS；不得签发第二个 jti 或延长期限。实现可持久化固定 claims 并按规范编码重签，不需要保存 proof 明文。

已完成 operation 的不同签名、不同 Session 或不同 applicationId 均拒绝。未完成 operation 的签名失败只递增有界失败计数，不生成 proof。

App 验证签名、issuer、固定 audience、typ、token_type、purpose、applicationId、subject、时间和 `jti`。允许最大 30 秒时钟偏差，但 proof 的总寿命仍固定 5 分钟；App 接受时还要求 `now - auth_time <= 5m`。

App 在 UC-APP-027 的本地关闭事务中唯一消费 `jti`：

- 首次消费只能绑定一个 applicationId、subject 和 closureId；
- 同一 `jti` 对同一 ApplicationClosure 的网络重试返回既有 CLOSING/CLOSED 结果；
- 跨 Application、跨 subject、跨 purpose 或绑定另一个 closureId 一律按重放拒绝；
- 只在关闭事务成功时提交消费记录，事务回滚不能永久烧掉 proof。

Auth 不回调 App 查询 `jti` 是否消费；App 不向 Auth 声称 proof 已使用。短寿命、App 唯一约束和业务绑定共同提供重放边界。

## 错误、限额与隐私

- 非法字段、UUID、长度或 DER：HTTP 400 / INVALID_ARGUMENT。
- Session、operation、签名或绑定无效以及过期：统一 HTTP 401 / UNAUTHENTICATED；未经证明不能区分账号、凭据或 operation 状态。
- 账号级限额：HTTP 429 / RESOURCE_EXHAUSTED，并提供有界 Retry-After。
- 持久化或签名服务暂不可用：HTTP 503 / UNAVAILABLE；不能返回未持久化的 proof。
- 记录损坏、已完成 claims 不一致：HTTP 500 / INTERNAL。

proof、challenge 和 signature 不进入业务审计。Auth 审计只记录 operationId、authId、credentialId、applicationId、结果类别、jti（成功时）和时间；App 审计只保存 proof jti，不保存 proof 原文。短期 operation 在过期后按既有认证挑战清理机制删除；已消费 jti 的永久/长期保留由 ApplicationClosure 审计拥有。

## 兼容与验收

v1 允许追加可选响应字段；改变 domain/action、Frame 顺序、签名算法、固定 audience/purpose、5 分钟上限或消费键需要新版本。

双方至少覆盖：

1. 同一登记设备的新签名成功，只有 Session、USER JWS、旧登录签名或另一设备签名失败。
2. Begin 后账号禁用、Session/credential 撤销、revision 变化或 applicationId 改写时 Complete 失败。
3. Complete 提交后响应丢失，重试返回同一 jti、时间和 JWS；不延长 exp。
4. 错误 issuer/audience/typ/token_type/purpose/sub/applicationId、未来 auth_time、过期和超过允许时钟差均被 App 拒绝。
5. App 关闭事务失败后 proof 可在原期限内重试；事务成功后的同 closure 重试幂等，跨 closure/application/subject 重放失败。
6. challenge/签名/proof 不进 URL、普通日志、审计或缓存；限额与失败计数有界。

## 权威用例

- Auth 签发方：[UC-AUTH-026](../../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md)。
- App 消费方：[UC-APP-027](../../app-center/use-cases/UC-APP-027-close-application.md)。
