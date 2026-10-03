# UC-AUTH-004：管理用户的应用审核权限

状态：`ACCEPTED`

## 目标与范围

> 平台管理员在 Auth Center 中分别授予或撤销用户的 `app.profile.review`（应用公开资料审核）与 `app.version.review`（应用版本审核）原子权限，使 Auth 后续签发的 trusted identity 准确反映当前授权，并留下不可变审计记录。

本用例只管理这两项应用审核权限，每次命令只选择其中一项；不是任意权限写入口。它不决定 App Center 的审核结果，不提供利益冲突绕过，也不把 PLATFORM_ADMIN 自动等同于 reviewer。这两项是平台人员权限，不进入 OAuth Scope Catalog，也不能通过用户 OAuth consent 获得。既有文件路径、BR-RVW 编号与 legacy API 名称保留，以保持引用和客户端兼容。

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
ManageApplicationReviewPermissionCommand {
  subjectAuthId: AuthId
  permission: "app.profile.review" | "app.version.review"
  action: GRANT | REVOKE
  expectedRevision: int64
  reason: string
}
```

1. 从 trusted identity 取得调用者 authId 与 `auth.reviewer.manage`。
2. 校验 permission 精确属于两项允许值，并确认目标是存在且可登录的 USER principal；SYSTEM principal 不能成为 reviewer。
3. 校验 reason 为非空审计文本，expectedRevision 与当前权限记录一致。
4. 只对选定 permission 执行 GRANT/REVOKE，保留另一项审核权限及所有其它权限；原子写入新集合、revision、updatedBy/updatedAt，并追加包含精确 permission 的不可变 audit event。
5. 返回同一提交结果中的两项审核权限状态与新 permissionRevision。

针对所选 permission 的重复 GRANT/REVOKE 是冲突，不伪装成成功；另一项是否已授予不改变该判断。客户端在不确定结果时查询当前状态。

## 读取应用审核权限状态

`GetApplicationReviewPermissions(subjectAuthId)` 使用与写接口相同的管理员身份要求，返回目标 authId、两项权限各自的 granted 状态和一个共享的 permissionRevision。两项都必须返回，按 permission 字典序排序；都未授予时仍返回两项 false。响应来自同一一致快照，不把分别读取的状态拼接。只公开本能力的两项状态，不返回目标其它权限或学生资料。不存在、SYSTEM 或不可登录目标不得被当作普通 USER 返回。

`GetReviewerPermission(subjectAuthId)` 继续作为旧兼容查询，只返回 app.version.review 对应的 reviewer 布尔值及同一个 permissionRevision；不把 reviewer 解释为任一审核权限的 OR，也不隐含 profile 权限。

## 实现约定

- Proto package 继续为 `auth_center.v1.reviewer_permission`，service 继续为 `ReviewerPermissionService`；保留 ManageReviewerPermission/GetReviewerPermission，并新增 ManageApplicationReviewPermission/GetApplicationReviewPermissions，线格式与兼容规则见下节。
- 四个方法均使用 Gateway SESSION、audience=`iwut-auth-center`、外部前缀 `/auth-center`；原生 gRPC 和 gRPC-Web 使用同一精确方法授权。新方法必须单独加入 Auth 方法鉴权表及 Gateway 静态路由，不因 service 名相同自动放行。HTTP 映射见 [Auth 路由契约](../../platform/contracts/auth-center-api-routing.md)。
- 写命令 `action` 使用 UNSPECIFIED/GRANT/REVOKE 枚举，UNSPECIFIED 拒绝；expectedRevision
  必填且为正 int64，reason 去除两端空白后为非空 UTF-8 文本且不超过 1024 bytes。
- 新命令的 permission 必填且只接受两项精确字符串；不修剪、忽略大小写、接受通配符或默认选择版本权限。auth.reviewer.manage、任意 OAuth scope 和未知 permission 均拒绝。旧命令的固定映射是兼容适配，不是新命令的缺省值。
- 已验签 JWS 必须包含 `auth.reviewer.manage`；写入事务内还须确认 actor 为当前 ACTIVE USER 且仍有该权限。
  body/path 不得指定或替代 actor。只修改选定审核权限，保留其它权限。
- 权限写入、bootstrap 与 [UC010 的签发一致性](UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004)
  使用相同认证事务协调边界；已确认撤销后不能再签出含该权限的新 token。
- 权限 revision 耗尽时拒绝变更，不溢出或回绕。审计插入失败导致权限更新一并回滚；提交结果未知返回不可用，不能伪装成功。
- bootstrap CLI 使用明确的现有 authId 和 Mongo 配置，不启动服务监听，不依赖终端 JWS；审计必须显式区分运维 bootstrap 和已认证用户请求。

## API 扩展与兼容

新增方法复用现有 ReviewerPermissionAction 枚举（0=UNSPECIFIED、1=GRANT、2=REVOKE），不改变其数值。新增消息字段号固定如下，可执行 Proto 和生成物在实现工作包交付：

```text
ManageApplicationReviewPermissionRequest {
  string subject_auth_id = 1;
  string permission = 2;
  ReviewerPermissionAction action = 3;
  optional int64 expected_revision = 4;
  string reason = 5;
}
GetApplicationReviewPermissionsRequest {
  string subject_auth_id = 1;
}
ApplicationReviewPermission {
  string permission = 1;
  bool granted = 2;
}
ApplicationReviewPermissions {
  string subject_auth_id = 1;
  repeated ApplicationReviewPermission permissions = 2;
  int64 permission_revision = 3;
}
```

两个新方法均返回 ApplicationReviewPermissions。Manage 的 optional expected_revision 必须有值；GET 无请求体、无 query。HTTP 新写入口是 `PUT /v1/users/{subject_auth_id}/application-review-permissions/{permission}`，读入口是 `GET /v1/users/{subject_auth_id}/application-review-permissions`。写正文仅需 action、expectedRevision、reason；路径绑定 subject_auth_id 和 permission，覆盖正文中的同名字段，不接受正文替换路径中的目标。采用标准 ProtoJSON 与 `body: "*"`，不另建 envelope；实际生成 HTTP 客户端必须参与验收。

旧 ManageReviewerPermission/GetReviewerPermission 的完整 RPC 名、HTTP `/v1/users/{subject_auth_id}/reviewer-permission`、请求/响应字段号、ReviewerPermissionAction 和错误 reason 保持不变。旧 Manage 只适配到 permission=app.version.review；旧响应的 reviewer 只表示版本审核权限。不能给旧请求增加改变语义的可选 permission，更不能把旧 GRANT 扩大为同时授予两项。

新旧方法共用一个领域命令、一份权限集合、一个 permissionRevision、同一事务栅栏和审计写入。旧入口撤销版本权限时必须保留 profile 权限。升级不得给现有版本 reviewer、管理员或 Developer 自动授予 profile 权限；历史记录未包含该权限即表示未授予，无需改写历史审计。若存储 validator 有权限枚举，显式升级其允许值，不建立第二套 profile grant 集合。

## 业务规则

<a id="br-rvw-001"></a>
### BR-RVW-001：Auth 权威所有权

Auth Center 是平台人员权限的唯一权威。App Center 只消费已签名 `permissions` claim，不保存 grant，不直接读 Auth 数据库。UC004 的目标 allowlist 只有 app.profile.review 与 app.version.review，不能修改管理权限或任意其它 permission；同一账号可独立持有其中零项、一项或两项。

<a id="br-rvw-002"></a>
### BR-RVW-002：管理权与审核权限隔离

auth.reviewer.manage、app.profile.review 与 app.version.review 是三项独立权限。前者允许管理后两项，但不授予任何审核能力；后两项分别只允许公开资料审核和版本审核，也不能管理他人权限。授予或撤销其中一项不联动另一项。Developer 身份不隐含审核能力，reviewer 也不要求 Developer 资格；任何身份仍受 App Center 对应审核用例的利益冲突规则约束。

<a id="br-rvw-003"></a>
### BR-RVW-003：乐观并发与不可变审计

每次有效变更严格增加目标用户共享的 permissionRevision，并记录 actor、subject、精确 permission、action、reason、before/after、时间。两项权限不各设 revision；即使修改不同权限，使用同一 expectedRevision 的并发命令也最多一个成功，另一方必须重读后决定是否重试。新旧入口均参与该 CAS，不能覆盖或丢失另一项权限。审计事件不可更新或删除。

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
| 命令格式、permission、action、revision 或 reason 非法 | `INVALID_REVIEWER_PERMISSION_INPUT` | 400 / INVALID_ARGUMENT |
| 重复动作、revision 不匹配 | `REVIEWER_PERMISSION_CONFLICT` | 409 / ABORTED |
| revision 耗尽 | `PERMISSION_REVISION_EXHAUSTED` | 409 / ABORTED |
| 存储损坏、数据库失败、提交结果未知 | `REVIEWER_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

bootstrap 重定向到另一目标时返回 `PLATFORM_ADMIN_BOOTSTRAP_CONSUMED` 并以非零退出码退出。
首次成功输出 `{"authId":"...","applied":true}`，同目标重跑为 `applied:false`，不代表重新授予权限。

## 测试与验收

- 非管理员、身份无效、SYSTEM/未知 subject 均被拒绝且不写审计。
- 两项权限分别覆盖 GRANT/REVOKE；未知、空白、通配或管理 permission 拒绝且无写入。Developer 状态为 null 仍可获得任一审核权限。
- 状态查询始终返回两项独立状态及同一 revision；用户的其它权限不披露。
- 新旧入口混用、跨两项权限并发及共享 revision 冲突不丢失权限；旧 reviewer 布尔值始终仅表示版本权限。
- 旧 Proto/生成 HTTP 客户端保持兼容；新 HTTP/gRPC 客户端的路径字段绑定、错误 reason 与 SESSION 认证一致。
- 真实 UC010 签发及 App verifier/审核入口验证：仅 profile、仅 version、两项、零项四种组合，互不越权；profile-only 可进入资料审核资格检查，但不能进入版本审核，反之亦然。
- 重复动作与 stale revision 冲突；并发最多一个成功。
- 权限状态与 audit event 原子提交或全部回滚。
- 平台管理员未显式获得目标审核权限时不能通过对应 App 审核入口；升级/bootstrap/Developer 开通不自动授予两项权限。
- 分别撤销两项权限后，后续 UC010 新签发不包含被撤销项；另一项保留，与签发竞争有明确先后顺序；已签 JWS 仍遵循既有有效期及容差。

## 变更记录

- 2026-09-22：接受 PLATFORM_ADMIN 统揽人员权限治理、Reviewer 独立显式 grant/revoke 与一次性运维 bootstrap。

- 2026-09-24：启动实现，固定权限状态查询、HTTP/gRPC 绑定、管理员能力表达、全局一次性 bootstrap 与 UC010 事务协调要求。

- 2026-10-03：扩展为管理用户的两项应用审核权限，新增显式权限命令/组合查询，保留旧版本审核 API，并与 UC010 投影扩展同步交付；设计接受不表示扩展实现已完成。
