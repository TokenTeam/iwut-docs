# UC-AUTH-004：管理 Reviewer 权限

状态：`ACCEPTED`

## 目标与范围

> 平台管理员在 Auth Center 中授予或撤销用户的 `app.version.review` 原子权限，使 Auth 后续签发的 trusted identity 准确反映当前授权，并留下不可变审计记录。

本用例只管理 Reviewer 权限。它不决定 App Center 的审核结果，不提供利益冲突绕过，也不把 `PLATFORM_ADMIN` 自动等同于 reviewer。

## 参与者与 bootstrap

调用者必须是具有 `auth.reviewer.manage` 权限的 `PLATFORM_ADMIN` 用户。平台管理员统揽跨 bounded context 的人员权限治理，但每个能力仍使用独立原子权限。

首个 PLATFORM_ADMIN 通过显式、一次性的运维命令 provision，例如：

```text
auth-center bootstrap-platform-admin --auth-id <existing-user-auth-id>
```

该命令要求 USER principal 已存在，幂等写入管理员 grant 与审计记录；它不是 Auth 普通启动路径，不允许仅因为环境变量仍存在就在每次重启时重新授予已撤销权限。后续管理员全部通过受审计的管理用例授予。

## 输入与主流程

```text
ManageReviewerPermissionCommand {
  subjectAuthId: AuthId
  action: GRANT | REVOKE
  expectedRevision: int64
  reason: string
}
```

1. 从 trusted identity 取得调用者 authId 与 `auth.reviewer.manage`。
2. 校验目标是存在且可登录的 USER principal；SYSTEM principal 不能成为 reviewer。
3. 校验 reason 为非空审计文本，expectedRevision 与当前权限记录一致。
4. 原子写入新的有效权限集合、revision、updatedBy/updatedAt，并追加不可变 audit event。
5. 返回目标权限状态与新 revision。

重复 GRANT/REVOKE 是冲突，不伪装成成功；客户端在不确定结果时查询当前状态。

## 业务规则

<a id="br-rvw-001"></a>
### BR-RVW-001：Auth 权威所有权

Auth Center 是平台人员权限的唯一权威。App Center 只消费已签名 `permissions` claim，不保存 grant，不直接读 Auth 数据库。

<a id="br-rvw-002"></a>
### BR-RVW-002：管理员不隐式成为 Reviewer

`auth.reviewer.manage` 与 `app.version.review` 是两个独立权限。PLATFORM_ADMIN 可以管理 reviewer，但若未显式获得 `app.version.review`，不能审核应用；任何身份仍受 App Center 利益冲突规则约束。

<a id="br-rvw-003"></a>
### BR-RVW-003：乐观并发与不可变审计

每次有效变更严格增加 permission revision，并记录 actor、subject、action、reason、before/after、时间。并发变更最多一个匹配 expectedRevision；审计事件不可更新或删除。

<a id="br-rvw-004"></a>
### BR-RVW-004：撤销传播上界

撤销后 Auth 不再签发包含该权限的新 token。已经签发并通过本地验签的 token 最多继续有效到 trusted-identity-v1 的 `exp`，因此权限撤销传播上界等于用户身份 token 的最大 TTL。首版不为“即时撤销”引入每请求 Auth introspection；若安全策略要求秒级强制失效，必须另立 ADR 选择 denylist/event push 或在线授权，而不能悄悄改变本地验签模型。

## 数据模型

- `auth_principals.permissions`：当前有效原子权限集合，元素唯一且稳定排序。
- `auth_principals.permissionRevision`：正 int64，权限变化时增加。
- `auth_permission_audit_events`：append-only 事件，包含 eventId、subjectAuthId、actorAuthId、action、permission、reason、beforeRevision、afterRevision、occurredAt。

## API 与实现依赖

管理 API 经 Gateway 使用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，不使用内部服务身份。可执行 Proto 与路由必须在实现工作包中单独加入。

完整实现依赖普通 USER principal provision、Auth 用户身份签发与 Gateway 到 Auth 的受保护管理路由；在这些入口闭合前，可以实现 Domain/Mongo 核心，但不能暴露绕过认证的临时管理 RPC 或用数据库直改代替本用例。

## 测试与验收

- 非管理员、身份无效、SYSTEM/未知 subject 均被拒绝且不写审计。
- grant/revoke 改变新签 token 的 permissions；Developer 状态可以为 null 且不影响 reviewer 授权。
- 重复动作与 stale revision 冲突；并发最多一个成功。
- 权限状态与 audit event 原子提交或全部回滚。
- 平台管理员未显式获得 reviewer 权限时不能通过 App Center reviewer 入口。

## 变更记录

- 2026-09-22：接受 PLATFORM_ADMIN 统揽人员权限治理、Reviewer 独立显式 grant/revoke 与一次性运维 bootstrap。
