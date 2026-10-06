# UC-AUTH-027：管理应用平台运维权限

状态：`ACCEPTED`

## 目标与范围

平台管理员在 Auth Center 中分别授予或撤销用户的 `app.application.suspend` 与 `app.application.restore` 原子权限，使 App Center 能依据短期可信用户身份授权平台级 Application 暂停与恢复操作，并为每次权限变化留下不可变审计。

本用例只管理人员权限，不暂停或恢复任何 Application。Application 的平台暂停状态、恢复条件、运行与目录门禁、状态 revision 和业务审计由后续 App Center 用例拥有。Application 当前管理员对自己应用的转让、关闭、发布和未来可恢复归档继续依据 App Center 的 `adminId` 与对应用例授权，不需要也不能借此取得平台运维权限。

本用例不提供任意权限编辑接口，不复用 `app.profile.review` 或 `app.version.review`，不把 Developer、Reviewer、Application 管理员或平台管理员自动转换为应用运维人员。两项权限不进入 OAuth Scope Catalog，不能由第三方应用申请，也不能通过用户 consent 获得。

## 参与者与依赖

- **操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的可信 USER JWS；JWS 包含 `auth.platform-admin.manage`，Auth 在线复核其当前完整平台管理员资格。
- **目标用户**：明确 `subjectAuthId` 对应的 ACTIVE USER。SYSTEM、未知用户与 CLOSED 账号不能获得权限；Developer 或 Reviewer 资格不是前提。
- **Auth Center**：唯一保存人员权限、共享 `permissionRevision` 和授权审计，并通过 UC010 投影到 App audience JWS。
- **App Center**：只消费 audience=`iwut-app-center` 的已签名权限 claim，并在未来 Application suspension 用例中执行精确权限检查；不保存另一份 grant。

依赖 [UC021](UC-AUTH-021-manage-platform-administrators.md) 的平台管理员资格和在线复核、[UC022](UC-AUTH-022-disable-and-restore-user-account.md) 的账号状态与版本、[UC010](UC-AUTH-010-issue-user-identity-from-session.md) 的可信身份签发，以及 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。本用例接受后还需要一个独立 App Center 用例定义 Application 平台暂停与恢复；Auth 权限管理可以先实现，但不能据此宣称暂停能力已经交付。

## 输入与输出

```text
ManageApplicationOperationsPermission {
  subjectAuthId: AuthId
  permission: "app.application.suspend" | "app.application.restore"
  action: GRANT | REVOKE
  expectedPermissionRevision: Int64  // 必填，正数
  reason: String                     // 去除两端空白后 1..1024 UTF-8 bytes
}

GetApplicationOperationsPermissions {
  subjectAuthId: AuthId
}

ApplicationOperationsPermission {
  permission: String
  granted: Bool
  effective: Bool
}

ApplicationOperationsPermissions {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  permissions: ApplicationOperationsPermission[2]
  permissionRevision: Int64
  grantBlockers: GrantBlocker[]
}
```

响应固定按 permission 字典序返回两项，即使均未授予也返回两个 `granted=false` 项。`effective` 表示当前账号为 ACTIVE 且已保存该项授权；DISABLED 用户保留 grant 事实但两项均不生效。查询不返回目标的其它权限、邮箱、Developer 状态、学生资料或 Session。

授予目标首版要求 ACTIVE USER、已有激活邮箱且邮箱恢复部署就绪；这些条件与高权限账号的可恢复性有关，不表示邮箱是真实身份认证。撤销允许目标为 ACTIVE 或 DISABLED，不因邮箱缺失或邮件服务不可用受阻。grantBlockers 固定按 `ACCOUNT_DISABLED, EMAIL_REQUIRED, EMAIL_RECOVERY_UNAVAILABLE` 顺序返回适用于所查询目标的公共门禁；某项是否已经授予由对应 permission 的 `granted` 表达。提交时仍须重新检查。

## API 契约

独立 package `auth_center.v1.application_operations_permission`，service `ApplicationOperationsPermissionService`：

| 方法 | Auth HTTP 路径 | 成功响应 |
| --- | --- | --- |
| `ManageApplicationOperationsPermission` | `PUT /v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | 200，完整两项状态 |
| `GetApplicationOperationsPermissions` | `GET /v1/users/{subject_auth_id}/application-operation-permissions` | 200，完整两项状态 |

Manage 的路径固定目标和 permission，正文只提交 action、expectedPermissionRevision 与 reason；正文不能替换路径身份。Get 无正文、无 query。两种方法同时提供 HTTP/JSON 与原生 gRPC，并以精确 full method 加入鉴权表。

Gateway 使用 SESSION 路由向 Auth 换取 audience=`iwut-auth-center` 的 USER JWS。Auth 只接受该可信身份，不接受 OAuth access token、App audience JWS、service JWS、直接 Session 或请求正文自报 actor。响应 `no-store`；拒绝未知或重复字段、非法枚举、query 和超过 16 KiB 的请求。

## 主流程

### 授予或撤销

1. 验证可信身份、精确方法、参数与入口限额；确认 permission 严格属于两项 allowlist。
2. 在 Auth 认证事务协调边界中在线确认操作人是 ACTIVE USER 且持有 UC021 完整平台管理员资格。
3. 读取目标账号、权限集合、邮箱绑定与共享 `permissionRevision`；损坏数据失败关闭。
4. 比较 expectedPermissionRevision。GRANT 复核目标 ACTIVE、激活邮箱和恢复就绪；REVOKE 只要求目标当前持有所选权限。
5. 仅修改选定权限，保留另一项运维权限、两项审核权限、管理权限和其它合法权限；严格增加一次共享 revision。
6. 权限更新与 append-only 审计在同一事务提交，成功后返回同一提交结果的完整两项状态。

重复 GRANT/REVOKE 或 stale revision 返回冲突，不增加 revision 或审计。事件 ID 在事务重试前生成并保持稳定；提交结果未知时返回不可用，客户端通过 Get 读取权威状态，不能盲目改用新 revision 重放。

### 查询

只有当前有效的平台管理员可以查询。Get 对存在且结构合法的 ACTIVE 或 DISABLED USER 返回两项状态；不存在、SYSTEM、CLOSED 或损坏目标不伪装成普通未授权用户。鉴权先于目标读取，未授权调用者不能借错误差异枚举账号。

## 业务规则

<a id="br-aop-001"></a>
### BR-AOP-001：精确运维权限与职责分离

首版 allowlist 只有 `app.application.suspend` 和 `app.application.restore`。前者只允许未来 App 用例把可运行 Application 置为平台暂停，后者只允许按该用例的恢复门禁解除平台暂停；任一权限都不授予审核、发布、转让、关闭、归档、OAuth client 管理或人员授权能力。

两项权限独立授予。只持有 suspend 的值班人员不能恢复，只持有 restore 的人员不能制造暂停。App Center 不接受 `app.application.*`、`app.*` 或通用 `app.application.manage` 通配能力，也不能把其中一项推导为另一项。

<a id="br-aop-002"></a>
### BR-AOP-002：平台管理员负责授权但不自动获得操作权

UC021 的平台管理员固定 bundle 不包含两项 App 运维权限。完整平台管理员可以通过本用例管理权限，但若要亲自暂停或恢复 Application，仍须显式向自己的 authId 授予对应权限。Developer、Reviewer、Application 当前管理员和 SYSTEM 均不因身份自动获得这两项权限。

首版复用完整平台管理员资格作为管理授权，不增加 `auth.application-ops.manage`。若未来需要把人员权限管理员从平台管理员中拆分，应另立 UC 修改授权模型，不能把 App 操作权限本身当作授予他人的权限。

<a id="br-aop-003"></a>
### BR-AOP-003：共享权限版本与原子审计

两项运维权限与现有审核、管理权限共用 `auth_principals.permissions` 和正数 `permissionRevision`。每次真实变化严格增加一次 revision；不同权限管理用例对同一目标使用相同旧 revision 并发时最多一个成功，不得通过独立版本覆盖另一项变化。

复用 `auth_permission_audit_events`，事件保存 eventId、actorAuthId、subjectAuthId、精确 permission、GRANT/REVOKE、reason、before/after、before/after revision 与 occurredAt。权限和审计同事务提交；审计失败全部回滚。不得记录邮箱、Session、学生信息或 JWS。

<a id="br-aop-004"></a>
### BR-AOP-004：Audience 最小投影与撤销窗口

UC010 的 `iwut-app-center` allowlist 增加两项运维权限；`iwut-auth-center` audience 不投影它们。Auth 仅从当前权威权限集合签发，App 只接受 audience 正确、签名和时间有效的 USER JWS，不接受 OAuth scope 或客户端自报 permission。

撤销提交后 Auth 不再签发包含该权限的新 JWS。已经签出的 JWS 仍可能在 `exp` 与消费方 clock skew 范围内被 App 接受，传播上界沿用 UC010 当前默认 60 秒、可配置 1–300 秒的短期身份模型。首版不为此能力引入每请求 introspection、denylist 或 Redis；若未来要求立即撤权，必须通过独立 ADR 修改共同信任模型。

<a id="br-aop-005"></a>
### BR-AOP-005：账号状态、恢复能力与授权事实

只有 ACTIVE USER 且具备激活邮箱和部署就绪恢复能力时可以 GRANT。账号被禁用时保留两项 grant 事实但不生效，Auth 不向该账号签发新的可信身份；账号恢复后仍须重新登录，既有 grant 可再次投影。账号 CLOSED 后由 UC025 的清理和保留规则处理，不作为可查询运维人员继续存在。

撤销不要求目标仍有邮箱或恢复能力，避免无法收紧权限。授予和撤销不改变 Developer、Reviewer、平台管理员、Session、设备凭据或 OAuth 状态。

<a id="br-aop-006"></a>
### BR-AOP-006：Auth 授权与 App 业务状态分离

Auth 只回答“哪个 USER 当前被授予哪项运维能力”。Application 是否 ACTIVE、已暂停、CLOSING/CLOSED、谁发起过暂停、是否满足恢复条件，以及暂停对目录、启动解析、审核和 OAuth 的影响，全部由 App Center 的 Application suspension 用例定义并持久化。

App 的未来暂停/恢复命令必须分别检查精确权限并记录其自身业务审计；不能仅凭 Auth grant 修改数据库，也不能要求 Auth 持有 applicationId 状态。CLOSING/CLOSED 不得通过 restore 权限恢复，所有者自助归档不得复用平台 suspension 字段。

## 错误语义与运行约束

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信用户身份 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 操作人非当前有效平台管理员 | `APPLICATION_OPERATIONS_PERMISSION_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 参数、permission、action、revision 或 reason 非法 | `INVALID_APPLICATION_OPERATIONS_PERMISSION_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不存在、SYSTEM、CLOSED 或不可管理 | `APPLICATION_OPERATIONS_PERMISSION_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| stale revision 或重复动作 | `APPLICATION_OPERATIONS_PERMISSION_CONFLICT` | 409 / ABORTED |
| GRANT 目标禁用、无邮箱或恢复未就绪 | `APPLICATION_OPERATIONS_PERMISSION_GRANT_BLOCKED` | 409 / FAILED_PRECONDITION |
| permissionRevision 耗尽 | `PERMISSION_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 入口限额 | `APPLICATION_OPERATIONS_PERMISSION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 数据损坏、存储故障或提交结果未知 | `APPLICATION_OPERATIONS_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

入口使用独立默认关闭配置 `AUTH_APPLICATION_OPERATIONS_PERMISSION_ENDPOINTS_ENABLED`，启用时要求用户端点、身份签发和平台管理员能力已配置。限流按已认证 actorAuthId 分开读写计数，默认每分钟读 60、写 10，桶容量有界；不能按任意 subjectAuthId 建立无界状态。

## 验收场景

1. 分别授予、撤销两项权限，以及零项、仅 suspend、仅 restore、两项的完整状态投影。
2. Reviewer、Developer、Application 管理员、SYSTEM 和没有完整管理员资格的用户均不能管理权限；平台管理员未显式获得操作权限时，App JWS 不含两项权限。
3. 平台管理员向自己显式授权后只获得选定能力；授予一项不改变另一项或任何审核/管理权限。
4. ACTIVE＋邮箱＋恢复就绪门禁；DISABLED/无邮箱目标不能 GRANT，但已有 grant 可以撤销。账号禁用时 grant 保留且不生效，恢复后仅新签发身份重新生效。
5. 与 UC004、UC021 及另一项运维权限同时使用相同 expected revision 并发，最多一个成功且不丢失权限。
6. 审计失败、事务重试和 unknown commit；真实变化只有一个事件，重复命令无事件。
7. Auth 与 App audience 投影隔离；OAuth、service JWS、错误 audience、伪造权限、通配权限全部拒绝。
8. 撤销与 UC010 签发竞争具有明确提交顺序；撤销后新 JWS 不含权限，旧 JWS 的残余窗口不超过既有 TTL/clock-skew 契约。
9. HTTP/JSON、原生 gRPC、生成客户端、Gateway SESSION 路由、严格解码、no-store 和有界限流。
10. 实际 App consumer 验证精确权限组合；业务暂停/恢复状态机由对应 App UC 单独完成联合验收。

## 实现依赖与交付边界

Auth 侧可复用 UC004 的权限集合、共享 revision、审计 repository 与 UC021 的管理员在线复核，但必须使用独立 allowlist、API 和错误语义，不能扩大 UC004 的审核权限接口。UC010、trusted-identity-v1、Auth 路由契约和 App verifier allowlist 需要同步扩展。

本用例已接受为 Auth/API 后端工作包。App Center 的 Application suspension 用例仍须独立确认暂停状态模型、运行/目录/OAuth 门禁、恢复条件、CLOSING/CLOSED 交互，以及 App 业务审计字段；不阻塞 Auth 先交付权限管理，但在实际 App consumer 完成前不能宣称平台暂停/恢复能力已交付。是否要求“恢复操作者不得是原暂停操作者”属于 App 治理策略，不由 Auth grant 模型预先决定。

## 变更记录

- 2026-10-06：建立首版提案；固定 suspend/restore 两项独立权限、平台管理员管理但不自动获得操作权、共享 permissionRevision 和 App audience 最小投影。因 UC-AUTH-026 已用于 Application 关闭协议，本用例使用下一个可分配编号 UC-AUTH-027。
- 2026-10-06：接受 Auth/API 后端工作包；App 暂停/恢复状态机继续独立设计和实现，实际 consumer 联合验收作为交付边界保留。
