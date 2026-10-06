# Application 关闭协调 v1

状态：`PROPOSED`

## 目的与边界

本契约定义 App Center 在 Application 进入不可逆 `CLOSING` 后，如何要求 Auth Center 建立永久的 applicationId 级授权撤销事实，并在未知结果、重试和进程重启后收敛。

App Center 是 Application 生命周期、Publication、OAuth registration 和关闭流程的权威；Auth Center 是 consent grant、authorization code、token family、sector、pairwise sub 及授权执行的权威。双方不共享数据库，也不把远程调用放进本地事务。

本契约不定义用户发起关闭的公网 API、近期重新认证证明格式、账号关闭或平台强制关闭。

## 先决条件与生效点

App 必须先在一个本地事务中：

- 把 Application 从 ACTIVE 改为 CLOSING；
- 安装所有本地运行与写入 gate；
- 禁用既有 OAuth client slot；
- 创建稳定 closureId 和 durable delivery task。

该事务提交是 App 侧停止服务的生效点。Auth 调用失败不能恢复 ACTIVE。App 只有取得 Auth 的 APPLIED receipt 后才能把 Application 改为 CLOSED。

## 服务身份

仅提供原生 gRPC，不提供 HTTP annotation、gRPC-Web 或终端路由。

```text
package auth_center.v1.application_closure
service ApplicationClosureService
```

App→Auth 使用 [Trusted Service Identity v1](trusted-service-identity-v1.md)、固定 audience `iwut-auth-center` 和 Auth 本地 App caller allowlist：

| 方法 | permission |
| --- | --- |
| `ApplyApplicationClosure` | `auth.application-closure.apply` |
| `GetApplicationClosureStatus` | `auth.application-closure.read` |

USER identity、未知 key、错误 audience、禁用 caller、缺少精确 permission 或过期 service JWS 一律失败关闭。Auth 不能接受终端自报的 applicationId/closureId。

## RPC 草图

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

## Auth 持久事实

Auth 保存以 applicationId 唯一的永久 application closure tombstone，至少包含 applicationId、closureId、closingStartedAt、receiptId、appliedAt。约束如下：

- 第一次合法 Apply 原子创建 tombstone 和稳定 receipt。
- 相同 applicationId、closureId 和 closingStartedAt 的重复 Apply 返回原结果。
- 相同 applicationId/closureId 但 closingStartedAt 不同，或相同 applicationId 使用不同 closureId，返回冲突并记录安全/数据告警。
- Get 的 applicationId、closureId 必须同时匹配；未知记录返回 NOT_FOUND，不能推断为“尚未应用”以外的更多事实。
- tombstone 不过期、不可取消、不可删除；Application ID、sector 和既有 pairwise sub 映射不得复用。

Auth 无需扫描改写每条 grant/code/token。所有相关用例必须在最终事务或最终权威读取边界复查 tombstone，使它成为 applicationId 级撤销栅栏。

## Auth 执行语义

tombstone 存在后，Auth 必须阻止：

- 创建或扩大该 Application 任一 channel 的用户授权；
- 签发和消费 authorization code；
- 通过 code 或 refresh token 签发 access token、ID token、refresh token；
- 使用任何既有 refresh token family；
- 在线 introspection/delegation 把该 Application 的既有 token 判断为可用。

失败应使用现有 OAuth/OIDC 对外错误语义，不能向终端泄露关闭时间、管理员或内部 tombstone。历史 grant、code、token family、sector 与 sub 可以继续保存供审计；它们不因保留而重新有效。

App 的 OAuth provider 暂时不可用或返回 Application 不可运行，不能替代 tombstone。Auth 也不能根据一次 provider 调用失败自行推断永久关闭，因为失败还可能来自网络、临时依赖或数据错误。

## 投递、查询与收敛

- App 使用同一个 closureId 至少一次投递 Apply。
- 建议初始退避 1 秒、指数增长、最大 60 秒；单次 RPC deadline 5 秒。
- Apply 超时、断连或响应丢失时，App 使用相同 applicationId＋closureId 查询 Get；Get NOT_FOUND 后才能重试相同 Apply。
- App 不能因未知结果生成新 closureId，也不能把超时当成 APPLIED。
- Auth 返回 APPLIED 后，App 验证 applicationId、closureId、receiptId、appliedAt 完整且匹配，再持久保存回执并推进 CLOSED。
- App 的 CLOSING 没有协议超时。长期故障触发运维告警，但不回滚关闭或恢复运行。

## 错误与兼容

- 参数格式错误：INVALID_ARGUMENT。
- service identity 无效：UNAUTHENTICATED。
- caller 或 permission 不允许：PERMISSION_DENIED。
- Get 无匹配记录：NOT_FOUND。
- 既有 applicationId/closureId/时间绑定冲突：ALREADY_EXISTS 或 FAILED_PRECONDITION；实现必须固定一种 reason 供契约测试。
- Auth 暂时无法提交持久事实：UNAVAILABLE。
- tombstone 或 receipt 数据不变量损坏：INTERNAL。

v1 只允许追加可选字段和新的只读方法。改变幂等键、允许取消、缩短永久保留、把 APPLIED 拆成可回退状态或削弱最终 tombstone 检查都需要新版本。

## 验收矩阵

双方契约测试至少覆盖：

1. 首次 Apply、相同请求重复 Apply 和 Get 返回完全相同 receipt。
2. 相同 applicationId 使用不同 closureId、相同 closureId 使用不同时间的冲突。
3. Apply 已提交但响应丢失、Get 已提交但响应丢失、App/Auth 任一侧重启。
4. USER JWS、错误 audience、未知/禁用 caller、错误 permission 和过期 service JWS。
5. tombstone 前取得的 code、access token、refresh family 在 tombstone 后全部按对应入口失败。
6. tombstone 后并发 authorize/exchange/refresh/delegation 的最终事务复查，不能产生晚到的有效凭证。
7. provider 暂时不可用不创建 tombstone；已有 tombstone 时 provider 恢复也不能重新授权。
8. 历史 sector/sub/grant 保留但 applicationId 永不复用。

## 权威用例

- App 提供方：[UC-APP-027](../../app-center/use-cases/UC-APP-027-close-application.md)。
- Auth 消费方：尚待建立；在该 UC 接受并定位全部 Auth 最终检查点前，本契约和 UC-APP-027 均保持 PROPOSED。
