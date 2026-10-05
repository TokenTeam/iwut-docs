# UC-AUTH-008：撤销自己的当前 Session

状态：`ACCEPTED`

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。

> Session 持有者要求 Auth 撤销当前 Session，使该 token 不再通过后续在线检查，而不改变设备凭据、账号或其它 Session。

本用例只定义服务端 Session 撤销能力。它不定义“退出登录”的界面、是否删除本地 token/私钥、账号切换或离线提示；这些属于非权威的[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。设备凭据撤销由 [UC-AUTH-009](UC-AUTH-009-revoke-own-credential.md) 定义。

## 输入与输出

```text
RevokeCurrentSession {
  // sessionToken 来自专用认证载体，不出现在消息正文
}

SessionRevoked {}
```

接口不接受 authId、sessionId 或 credentialId。sessionToken 是唯一定位依据，格式和摘要规则引用 [BR-LGN-003](UC-AUTH-007-login.md#br-lgn-003)，具体载体和方法分派遵守 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)。

## 主流程

1. Auth 从专用认证载体读取 sessionToken，完成形状和长度校验并计算摘要。
2. 按 tokenDigest 查找 Session；不先经过要求 Session 当前有效的普通鉴权中间件。
3. 若记录存在且未撤销，以服务端时间设置 revokedAt；若已撤销、已过期或不存在，按 BR-LGN-005 返回幂等成功。
4. 提交成功后返回 SessionRevoked。客户端是否以及何时清除本地状态不属于服务端后置条件。

## 业务规则

<a id="br-lgn-005"></a>
### BR-LGN-005：当前 Session 的定向撤销

RevokeCurrentSession 只能撤销调用者提交 token 对应的 Session，不接受客户端指定记录标识，也不能由 token 中的客户端标签改变目标。已知 Session 无论当前是否过期都可以写入 revokedAt；已经撤销或没有匹配记录时返回相同成功结果，不泄露 token 是否曾存在。

缺少、为空、长度或编码非法的 token 是请求错误，不当作幂等成功；仓储不可用或提交结果未知不能声称服务端已经撤销。撤销提交后才开始的 BR-LGN-004 在线检查必须失败，已经通过检查的在途业务不承诺中止，已签发 JWS 仍按其自身短有效期验证。

本命令不撤销设备凭据、不删除 USER/资料/学生关联、不影响其它 Session，也不释放任何凭据公钥唯一性。以后需要撤销指定的其它 Session，应以有效用户身份授权并另行扩展，不能把本接口改成接受任意 sessionId 的匿名删除入口。

撤销是逻辑状态变化，revokedAt 一旦写入不能清空；物理记录由保留期和清理任务处理。实现使用 tokenDigest 唯一索引和单文档条件更新，重复及并发请求最终只有一个首次撤销时间。允许记录 sessionId、可信 authId、结果和服务端时间，不记录 sessionToken。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| token 缺失或格式非法 | `INVALID_SESSION_TOKEN` | 400 / INVALID_ARGUMENT |
| 仓储不可用或提交结果未知 | `SESSION_REVOCATION_UNAVAILABLE` | 503 / UNAVAILABLE |

已撤销、已过期和未知的有效格式 token 均返回成功，不以差异响应形成 Session 探测接口。

## 测试与验收

1. 当前有效 Session 撤销成功，随后在线检查失败；其它 Session 和设备凭据保持不变。
2. 相同 token 重复及并发撤销幂等，revokedAt 不被后续请求改写。
3. 已过期、已撤销和未知的有效格式 token 返回相同成功形状，不泄露记录存在性。
4. 缺失、空值、畸形和超长 token 在访问仓储前拒绝；日志中不出现 token。
5. 数据库失败或结果未知不返回已确认成功；重试后收敛到已撤销状态。
6. 与在线检查并发时具有明确提交顺序；撤销前已通过的请求可以完成，撤销提交后的新检查失败。

## 交付依赖

- 按共享契约交付 `auth_center/v1/authentication/` RevokeCurrentSession、专用 Session 载体、精确方法例外和日志脱敏，并通过原生 gRPC 验收；Gateway 路由另行交付。
- revoked Session 的保留期和物理清理策略；清理不得早于幂等重试及审计所需窗口。
- 与 BR-LGN-004 会话检查共用 tokenDigest 查询和并发测试。

## 变更记录

- 2026-09-22：接受本用例，设备证明、关联声明、Session 载体与 RPC 鉴权引用 auth-device-session-v1；后端、客户端和 Gateway 分别验收。

- 2026-09-22：从 UC-AUTH-007 拆出当前 Session 撤销，限定为 token 定向、幂等的服务端能力；客户端退出编排移至指导文件。
