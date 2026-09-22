# UC-AUTH-009：撤销自己的设备凭据

状态：`ACCEPTED`

## 目标与范围

> 已认证用户要求 Auth 撤销属于自己账号的一条设备凭据，使该公钥不能再建立新 Session，并使依赖该凭据的既有 Session 在后续在线检查中失效。

本用例只改变 Auth 持有的凭据状态。它不声称能够删除客户端私钥，也不规定退出警告、本地清理和离线体验；客户端组合建议见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。只撤销当前 Session 使用 [UC-AUTH-008](UC-AUTH-008-revoke-own-session.md)。

## 参与者与前置条件

- 调用者持有通过 BR-LGN-004 检查的有效 Session，主体为 ACTIVE USER。
- 目标 credentialId 由调用者明确提交；Auth 以当前 Session 的 authId 做所有权判断，不接受请求体指定目标 authId。

## 输入与输出

```text
RevokeOwnCredential {
  credentialId: OpaqueId
}

CredentialRevoked {}
```

这是逻辑消息，生成 Proto、Session 载体与 RPC 鉴权遵守 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)。接口名称中的 Revoke 表示不可逆状态迁移，不等同于立即物理删除记录。

## 主流程

1. Auth 验证当前 Session，并取得可信 authId。
2. 校验 credentialId 形状，按 `(authId, credentialId)` 读取目标凭据。
3. 若凭据有效，以服务端时间原子设置 revokedAt；若同一账号的目标已经撤销，幂等返回成功。
4. 提交成功后返回 CredentialRevoked。若目标正是当前 Session 的认证凭据，该 Session 从下一次在线检查开始失效。

## 业务规则

<a id="br-lgn-012"></a>
### BR-LGN-012：本人设备凭据的授权撤销

只有当前有效 USER 可以撤销归属于相同 authId 的凭据。未知 credentialId 与属于其它账号的 credentialId 使用相同未找到结果，不泄露其归属；客户端不能通过提交 authId、学校关联或设备标签改变授权范围。SYSTEM、禁用账号或无效 Session 不得调用成功。

撤销采用凭据记录的不可逆 revokedAt 状态，不物理删除公钥，不释放规范公钥指纹的唯一归属，也不允许以后清空 revokedAt 复活。重复撤销同一账号已撤销的凭据，在调用 Session 仍有效的前提下幂等成功；并发请求只有一个首次撤销时间。操作记录允许包含 authId、credentialId、调用 sessionId、结果和服务端时间，不记录 Session token 或私钥材料。

凭据撤销提交后，它不能再完成 UC-AUTH-007 登录。BR-LGN-004 每次检查凭据状态，因此所有引用该 credentialId 的 Session 在随后检查中失败，无需在本命令内逐条更新 Session；撤销前已通过检查的在途请求和此前签发的短期 JWS 遵循各自既有边界。

允许撤销当前 Session 使用的凭据，也允许撤销同一账号的其它凭据。撤销当前凭据后，再用原 Session 重试返回 SESSION_INVALID；其它仍有效 Session 可重复撤销同一目标。本次成功响应可能是该 Session 最后一次授权成功的请求；响应丢失时结果可能未知，客户端不能假定回滚。撤销最后一条凭据也不被服务器阻止：Auth 不以邮箱、其它设备或学生关联推断可恢复性，恢复风险提示和本地私钥删除由客户端负责。

撤销凭据不删除 USER、资料、学生关联或其它凭据。物理清理由单独保留策略处理；即使客户端声称已经删除本地私钥，Auth 也不能把该声明当作服务端撤销证据。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| credentialId 缺失或格式非法 | `INVALID_CREDENTIAL_ID` | 400 / INVALID_ARGUMENT |
| Session 无效或主体不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 目标不存在或不属于当前 authId | `CREDENTIAL_NOT_FOUND` | 404 / NOT_FOUND |
| 仓储不可用或提交结果未知 | `CREDENTIAL_REVOCATION_UNAVAILABLE` | 503 / UNAVAILABLE |

客户端不依赖 message 文本判断归属。已撤销的本人凭据返回成功；其它账号和未知目标不做区分。

## 测试与验收

1. 有效 Session 可以撤销同一 authId 的当前或其它凭据；不能撤销其它账号凭据。
2. 撤销后新设备登录失败，引用该凭据的所有 Session 在随后在线检查中失败，其它凭据和 Session 不受影响。
3. 重复与并发撤销幂等，revokedAt 不变化，公钥唯一归属不释放。
4. 撤销当前凭据后当前 Session 失效；注入响应丢失时不把结果未知误报为回滚。
5. 允许撤销最后一条凭据，不使用邮箱、学生关联或客户端恢复声明作为服务端门禁。
6. 未知与他人 credentialId 响应一致；畸形输入、无效 Session、禁用账号和仓储故障失败关闭。
7. 日志和审计只有受控标识与结果，不含 token、私钥或证明正文。

## 交付依赖

- 按共享契约交付 `auth_center/v1/authentication/` RevokeOwnCredential、有效用户 Session middleware 和精确 RPC 鉴权表；Gateway 路由与客户端编排独立验收。
- 凭据记录的状态字段、条件更新与审计存储；物理保留期由后续生命周期策略确定。
- 查询/命名/撤销其它设备的完整管理体验、再认证策略和凭据新增仍可另立管理用例，本用例只提供按 credentialId 的最小撤销命令。

## 变更记录

- 2026-09-22：接受本用例，设备证明、关联声明、Session 载体与 RPC 鉴权引用 auth-device-session-v1；后端、客户端和 Gateway 分别验收。

- 2026-09-22：从客户端退出流程中拆出本人设备凭据撤销，定义授权、幂等、Session 失效传播与最后凭据边界。
