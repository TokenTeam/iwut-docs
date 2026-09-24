# UC-AUTH-004：管理 Reviewer 权限

状态：`ACCEPTED`

## 目标与范围

> 平台管理员在 Auth Center 中授予或撤销用户的 `app.version.review` 原子权限，使 Auth 后续签发的 trusted identity 准确反映当前授权，并留下不可变审计记录。

本用例只管理 Reviewer 权限。它不决定 App Center 的审核结果，不提供利益冲突绕过，也不把 `PLATFORM_ADMIN` 自动等同于 reviewer。

## 参与者与 bootstrap

调用者必须是具有 `auth.reviewer.manage` 权限的 `PLATFORM_ADMIN` 用户。平台管理员统揽跨 bounded context 的人员权限治理，但每个能力仍使用独立原子权限。

本用例以 `auth.reviewer.manage` 的显式 grant 表达 PLATFORM_ADMIN 管理能力；主体仍为 USER，不新增 principalType 或通用角色继承。

首个 PLATFORM_ADMIN 通过显式、一次性的运维命令 provision：

```text
auth-center bootstrap-platform-admin --auth-id <existing-user-auth-id>
```

该命令要求 USER principal 已存在，幂等写入管理员 grant 与审计记录；它不是 Auth 普通启动路径，不允许仅因为环境变量仍存在就在每次重启时重新授予已撤销权限。后续管理员全部通过受审计的管理用例授予。bootstrap 在同一事务中保存全局已消费标记：对原目标重跑只报告已执行，不再次写权限或审计；对另一目标重跑拒绝。即使原管理员权限后来被撤销，也不能通过重跑该命令恢复。

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

## 读取 Reviewer 权限状态

`GetReviewerPermission(subjectAuthId)` 是本用例的配套查询，采用与写接口相同的管理员身份要求。
返回目标 authId、是否具有 `app.version.review`、当前 permissionRevision，供客户端提交 expectedRevision
以及在冲突或提交结果未知时重新读取。只返回本能力所需状态，不公开目标的其它权限或学生资料。
不存在、SYSTEM 或不可登录目标不得被当作普通 USER 返回。

## 实现约定

- Proto package 为 `auth_center.v1.reviewer_permission`，service 为 `ReviewerPermissionService`；
  方法为 `ManageReviewerPermission`、`GetReviewerPermission`。
- HTTP 写/读分别为 `PUT` / `GET /v1/users/{subject_auth_id}/reviewer-permission`；Gateway 使用
  SESSION、audience=`iwut-auth-center`，外部前缀为 `/auth-center`。原生 gRPC 和 gRPC-Web 使用同一精确方法授权。
- 写命令 `action` 使用 UNSPECIFIED/GRANT/REVOKE 枚举，UNSPECIFIED 拒绝；expectedRevision
  必填且为正 int64，reason 去除两端空白后为非空 UTF-8 文本且不超过 1024 bytes。
- 已验签 JWS 必须包含 `auth.reviewer.manage`；写入事务内还须确认 actor 为当前 ACTIVE USER 且仍有该权限。
  body/path 不得指定或替代 actor。只修改 reviewer grant，保留其它权限。
- 权限写入、bootstrap 与 [UC010 的签发一致性](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004)
  使用相同认证事务协调边界；已确认撤销后不能再签出含该权限的新 token。
- 权限 revision 耗尽时拒绝变更，不溢出或回绕。审计插入失败导致权限更新一并回滚；提交结果未知返回不可用，不能伪装成功。
- bootstrap CLI 使用明确的现有 authId 和 Mongo 配置，不启动服务监听，不依赖终端 JWS；审计必须显式区分运维 bootstrap 和已认证用户请求。

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
- `auth_permission_audit_events`：append-only 事件，包含 eventId、subjectAuthId、actorType、action、permission、reason、before/after、beforeRevision、afterRevision、occurredAt。普通管理请求 actorType=`USER`，actorAuthId 为已认证用户；运维初始化 actorType=`BOOTSTRAP_COMMAND`，不伪造 actorAuthId。
- `auth_runtime` 的 `platform-admin-bootstrap` 单例：保存 subjectAuthId、eventId、occurredAt，表示全局初始化已消费，不能通过重启或权限撤销清除。

## API 与实现依赖

管理 API 经 Gateway 使用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，不使用内部服务身份。可执行 Proto 与路由必须在实现工作包中单独加入。

完整实现依赖普通 USER principal provision、Auth 用户身份签发与 Gateway 到 Auth 的受保护管理路由；在这些入口闭合前，可以实现 Domain/Mongo 核心，但不能暴露绕过认证的临时管理 RPC 或用数据库直改代替本用例。

## 错误语义

| 场景 | reason | HTTP / gRPC |
| --- | --- | --- |
| 身份缺失/无效 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 无管理权限、actor 非当前 ACTIVE USER | `REVIEWER_MANAGEMENT_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 目标不存在、SYSTEM 或不可登录 | `REVIEWER_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| 命令格式、action、revision 或 reason 非法 | `INVALID_REVIEWER_PERMISSION_INPUT` | 400 / INVALID_ARGUMENT |
| 重复动作、revision 不匹配 | `REVIEWER_PERMISSION_CONFLICT` | 409 / ABORTED |
| revision 耗尽 | `PERMISSION_REVISION_EXHAUSTED` | 409 / ABORTED |
| 存储损坏、数据库失败、提交结果未知 | `REVIEWER_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

bootstrap 重定向到另一目标时返回 `PLATFORM_ADMIN_BOOTSTRAP_CONSUMED` 并以非零退出码退出。
首次成功输出 `{"authId":"...","applied":true}`，同目标重跑为 `applied:false`，不代表重新授予权限。

## 测试与验收

- 非管理员、身份无效、SYSTEM/未知 subject 均被拒绝且不写审计。
- grant/revoke 改变新签 token 的 permissions；Developer 状态可以为 null 且不影响 reviewer 授权。
- 重复动作与 stale revision 冲突；并发最多一个成功。
- 权限状态与 audit event 原子提交或全部回滚。
- 平台管理员未显式获得 reviewer 权限时不能通过 App Center reviewer 入口。

## 变更记录

- 2026-09-22：接受 PLATFORM_ADMIN 统揽人员权限治理、Reviewer 独立显式 grant/revoke 与一次性运维 bootstrap。

- 2026-09-24：启动实现，固定权限状态查询、HTTP/gRPC 绑定、管理员能力表达、全局一次性 bootstrap 与 UC010 事务协调要求。
