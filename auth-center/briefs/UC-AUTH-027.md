<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-027 --spec tools/brief-specs/UC-AUTH-027.json -->
# Brief — UC-AUTH-027：管理应用平台运维权限

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-027` 管理应用平台运维权限 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-AOP-001`–`BR-AOP-006`（6 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-session-identity-issuance-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

平台管理员在 Auth Center 中分别授予或撤销用户的 `app.application.suspend` 与 `app.application.restore` 原子权限，使 App Center 能依据短期可信用户身份授权平台级 Application 暂停与恢复操作，并为每次权限变化留下不可变审计。

本用例只管理人员权限，不暂停或恢复任何 Application。Application 的平台暂停状态、恢复条件、运行与目录门禁、状态 revision 和业务审计由后续 App Center 用例拥有。Application 当前管理员对自己应用的转让、关闭、发布和未来可恢复归档继续依据 App Center 的 `adminId` 与对应用例授权，不需要也不能借此取得平台运维权限。

本用例不提供任意权限编辑接口，不复用 `app.profile.review` 或 `app.version.review`，不把 Developer、Reviewer、Application 管理员或平台管理员自动转换为应用运维人员。两项权限不进入 OAuth Scope Catalog，不能由第三方应用申请，也不能通过用户 consent 获得。

### 参与者与依赖

- **操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的可信 USER JWS；JWS 包含 `auth.platform-admin.manage`，Auth 在线复核其当前完整平台管理员资格。
- **目标用户**：明确 `subjectAuthId` 对应的 ACTIVE USER。SYSTEM、未知用户与 CLOSED 账号不能获得权限；Developer 或 Reviewer 资格不是前提。
- **Auth Center**：唯一保存人员权限、共享 `permissionRevision` 和授权审计，并通过 UC010 投影到 App audience JWS。
- **App Center**：只消费 audience=`iwut-app-center` 的已签名权限 claim，并在未来 Application suspension 用例中执行精确权限检查；不保存另一份 grant。

依赖 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md) 的平台管理员资格和在线复核、[UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md) 的账号状态与版本、[UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 的可信身份签发，以及 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。本用例接受后还需要一个独立 App Center 用例定义 Application 平台暂停与恢复；Auth 权限管理可以先实现，但不能据此宣称暂停能力已经交付。

### 输入与输出

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

### API 契约

独立 package `auth_center.v1.application_operations_permission`，service `ApplicationOperationsPermissionService`：

| 方法 | Auth HTTP 路径 | 成功响应 |
| --- | --- | --- |
| `ManageApplicationOperationsPermission` | `PUT /v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | 200，完整两项状态 |
| `GetApplicationOperationsPermissions` | `GET /v1/users/{subject_auth_id}/application-operation-permissions` | 200，完整两项状态 |

Manage 的路径固定目标和 permission，正文只提交 action、expectedPermissionRevision 与 reason；正文不能替换路径身份。Get 无正文、无 query。两种方法同时提供 HTTP/JSON 与原生 gRPC，并以精确 full method 加入鉴权表。

Gateway 使用 SESSION 路由向 Auth 换取 audience=`iwut-auth-center` 的 USER JWS。Auth 只接受该可信身份，不接受 OAuth access token、App audience JWS、service JWS、直接 Session 或请求正文自报 actor。响应 `no-store`；拒绝未知或重复字段、非法枚举、query 和超过 16 KiB 的请求。

### 主流程

#### 授予或撤销

1. 验证可信身份、精确方法、参数与入口限额；确认 permission 严格属于两项 allowlist。
2. 在 Auth 认证事务协调边界中在线确认操作人是 ACTIVE USER 且持有 UC021 完整平台管理员资格。
3. 读取目标账号、权限集合、邮箱绑定与共享 `permissionRevision`；损坏数据失败关闭。
4. 比较 expectedPermissionRevision。GRANT 复核目标 ACTIVE、激活邮箱和恢复就绪；REVOKE 只要求目标当前持有所选权限。
5. 仅修改选定权限，保留另一项运维权限、两项审核权限、管理权限和其它合法权限；严格增加一次共享 revision。
6. 权限更新与 append-only 审计在同一事务提交，成功后返回同一提交结果的完整两项状态。

重复 GRANT/REVOKE 或 stale revision 返回冲突，不增加 revision 或审计。事件 ID 在事务重试前生成并保持稳定；提交结果未知时返回不可用，客户端通过 Get 读取权威状态，不能盲目改用新 revision 重放。

#### 查询

只有当前有效的平台管理员可以查询。Get 对存在且结构合法的 ACTIVE 或 DISABLED USER 返回两项状态；不存在、SYSTEM、CLOSED 或损坏目标不伪装成普通未授权用户。鉴权先于目标读取，未授权调用者不能借错误差异枚举账号。

### 错误语义与运行约束

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

### 验收场景

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

### 实现依赖与交付边界

Auth 侧可复用 UC004 的权限集合、共享 revision、审计 repository 与 UC021 的管理员在线复核，但必须使用独立 allowlist、API 和错误语义，不能扩大 UC004 的审核权限接口。UC010、trusted-identity-v1、Auth 路由契约和 App verifier allowlist 需要同步扩展。

本用例已接受为 Auth/API 后端工作包。App Center 的 Application suspension 用例仍须独立确认暂停状态模型、运行/目录/OAuth 门禁、恢复条件、CLOSING/CLOSED 交互，以及 App 业务审计字段；不阻塞 Auth 先交付权限管理，但在实际 App consumer 完成前不能宣称平台暂停/恢复能力已交付。是否要求“恢复操作者不得是原暂停操作者”属于 App 治理策略，不由 Auth grant 模型预先决定。

## 业务规则（UC-AUTH-027 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-001 -->
### BR-AOP-001：精确运维权限与职责分离

首版 allowlist 只有 `app.application.suspend` 和 `app.application.restore`。前者只允许未来 App 用例把可运行 Application 置为平台暂停，后者只允许按该用例的恢复门禁解除平台暂停；任一权限都不授予审核、发布、转让、关闭、归档、OAuth client 管理或人员授权能力。

两项权限独立授予。只持有 suspend 的值班人员不能恢复，只持有 restore 的人员不能制造暂停。App Center 不接受 `app.application.*`、`app.*` 或通用 `app.application.manage` 通配能力，也不能把其中一项推导为另一项。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-002 -->
### BR-AOP-002：平台管理员负责授权但不自动获得操作权

UC021 的平台管理员固定 bundle 不包含两项 App 运维权限。完整平台管理员可以通过本用例管理权限，但若要亲自暂停或恢复 Application，仍须显式向自己的 authId 授予对应权限。Developer、Reviewer、Application 当前管理员和 SYSTEM 均不因身份自动获得这两项权限。

首版复用完整平台管理员资格作为管理授权，不增加 `auth.application-ops.manage`。若未来需要把人员权限管理员从平台管理员中拆分，应另立 UC 修改授权模型，不能把 App 操作权限本身当作授予他人的权限。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-003 -->
### BR-AOP-003：共享权限版本与原子审计

两项运维权限与现有审核、管理权限共用 `auth_principals.permissions` 和正数 `permissionRevision`。每次真实变化严格增加一次 revision；不同权限管理用例对同一目标使用相同旧 revision 并发时最多一个成功，不得通过独立版本覆盖另一项变化。

复用 `auth_permission_audit_events`，事件保存 eventId、actorAuthId、subjectAuthId、精确 permission、GRANT/REVOKE、reason、before/after、before/after revision 与 occurredAt。权限和审计同事务提交；审计失败全部回滚。不得记录邮箱、Session、学生信息或 JWS。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-004 -->
### BR-AOP-004：Audience 最小投影与撤销窗口

UC010 的 `iwut-app-center` allowlist 增加两项运维权限；`iwut-auth-center` audience 不投影它们。Auth 仅从当前权威权限集合签发，App 只接受 audience 正确、签名和时间有效的 USER JWS，不接受 OAuth scope 或客户端自报 permission。

撤销提交后 Auth 不再签发包含该权限的新 JWS。已经签出的 JWS 仍可能在 `exp` 与消费方 clock skew 范围内被 App 接受，传播上界沿用 UC010 当前默认 60 秒、可配置 1–300 秒的短期身份模型。首版不为此能力引入每请求 introspection、denylist 或 Redis；若未来要求立即撤权，必须通过独立 ADR 修改共同信任模型。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005 -->
### BR-AOP-005：账号状态、恢复能力与授权事实

只有 ACTIVE USER 且具备激活邮箱和部署就绪恢复能力时可以 GRANT。账号被禁用时保留两项 grant 事实但不生效，Auth 不向该账号签发新的可信身份；账号恢复后仍须重新登录，既有 grant 可再次投影。账号 CLOSED 后由 UC025 的清理和保留规则处理，不作为可查询运维人员继续存在。

撤销不要求目标仍有邮箱或恢复能力，避免无法收紧权限。授予和撤销不改变 Developer、Reviewer、平台管理员、Session、设备凭据或 OAuth 状态。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-006 -->
### BR-AOP-006：Auth 授权与 App 业务状态分离

Auth 只回答“哪个 USER 当前被授予哪项运维能力”。Application 是否 ACTIVE、已暂停、CLOSING/CLOSED、谁发起过暂停、是否满足恢复条件，以及暂停对目录、启动解析、审核和 OAuth 的影响，全部由 App Center 的 Application suspension 用例定义并持久化。

App 的未来暂停/恢复命令必须分别检查精确权限并记录其自身业务审计；不能仅凭 Auth grant 修改数据库，也不能要求 Auth 持有 applicationId 状态。CLOSING/CLOSED 不得通过 restore 权限恢复，所有者自助归档不得复用平台 suspension 字段。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/registrations` | AuthenticationService/BeginUserRegistration | DIRECT | 200 |
| POST | `/v1/registrations/{operation_id}/completion` | AuthenticationService/CompleteUserRegistration | DIRECT | 201 |
| POST | `/v1/device-logins` | AuthenticationService/BeginDeviceLogin | DIRECT | 200 |
| POST | `/v1/device-logins/{operation_id}/completion` | AuthenticationService/CompleteDeviceLogin | DIRECT | 201 |
| DELETE | `/v1/sessions/current` | AuthenticationService/RevokeCurrentSession | DIRECT | 200 |
| DELETE | `/v1/users/me/credentials/{credential_id}` | AuthenticationService/RevokeOwnCredential | DIRECT | 200 |
| GET | `/v1/users/me/profile` | UserProfileService/GetOwnProfile | SESSION | 200 |
| PATCH | `/v1/users/me/profile` | UserProfileService/EditOwnProfile | SESSION | 200 |
| GET | `/v1/user-profile-schema` | UserProfileService/GetProfileEditingSchema | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/ManageReviewerPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/GetReviewerPermission | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | ReviewerPermissionService/ManageApplicationReviewPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-review-permissions` | ReviewerPermissionService/GetApplicationReviewPermissions | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | ApplicationOperationsPermissionService/ManageApplicationOperationsPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-operation-permissions` | ApplicationOperationsPermissionService/GetApplicationOperationsPermissions | SESSION | 200 |

UC011 追加三个 DIRECT 路由，完整字段及 Session 例外见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](../../platform/contracts/auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。
- 普通设备注册/登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

#### 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖九个资料/认证 HTTP 方法、两个旧 Reviewer 管理方法与两个新增应用审核权限方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/auth-session-identity-issuance-v1.md`：Session 到可信用户身份签发 v1

#### 内部 RPC

独立 API 路径 `auth_center/v1/identity/identity.proto`，package `auth_center.v1.identity`：

```text
/auth_center.v1.identity.UserIdentityService/IssueUserIdentityFromSession

IssueUserIdentityFromSessionRequest {
  string audience = 1;
}
IssuedUserIdentity {
  string identity_jws = 1;
  int64 expires_at_unix_seconds = 2;
}
```

以上为设计线格式，正式 Proto 及生成代码在实现时进入独立 API 仓库。首版仅 unary 原生 gRPC；不注册终端 HTTP、gRPC-Web 或网关公开路由。

- `authorization`：由 Gateway 自己生成的内部服务 Bearer JWS，严格遵循 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，不能使用客户端 Authorization。
- `x-iwut-session`：本次终端请求提供的唯一 token，采用 [auth-device-session-v1 的 Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，消息体不重复承载。
- 不接收 `x-iwut-identity` 作为签发授权，也不通过 JWS 自身换取新 JWS。
- 目标 audience 精确匹配预登记值；无空白修剪、URL 解释或客户端动态指定。首批值为 `iwut-auth-center` 和 `iwut-app-center`。
- body、metadata、返回体均不得进入通用请求/响应日志；传输必须受保护。客户端 token 与服务 token 均不能透传给最终业务服务。

#### 应用审核权限投影

用户能力投影唯一遵循 [UC010 / BR-IDN-002](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002)：App audience 可携带用户实际拥有的 `app.profile.review`、`app.version.review`、`app.application.suspend` 与 `app.application.restore`；Auth 管理权限不因此下发给 App。审核权限由 [UC004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) 管理，运维权限由 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 管理；均复用现有 `permissions` claim 和签发 RPC。平台管理员不会被自动投影为 Reviewer 或 Application 运维人员。

#### 签名与验签配置

签发入口使用显式开关 `AUTH_IDENTITY_ISSUANCE_ENABLED`（默认 false）。开启要求现有 `AUTH_USER_ENDPOINTS_ENABLED=true`，且下述 signer 配置完整有效；关闭时不注册签发 RPC，不要求私钥，也不影响已有服务和用户接口。不得因为开关开启而放宽原有鉴权。

新增 signer 配置：`AUTH_USER_IDENTITY_SIGNING_KID`、`AUTH_USER_IDENTITY_PRIVATE_KEY_PEM_B64`、`AUTH_USER_IDENTITY_TTL`（默认 `60s`，1–300 整秒）。issuer 沿用 `AUTH_USER_IDENTITY_ISSUER`；既有 `AUTH_USER_IDENTITY_MAX_TTL` 是 verifier 接受上限，不是 signer 默认 TTL。

私钥使用严格标准 Base64 包装的 PKCS#1/PKCS#8 RSA PEM，至少 2048 bit。Auth 自己作为 audience 时必须部署匹配的 verifier 公钥；其他服务先部署新公钥，再切 signer kid，旧验签公钥覆盖旧 token 的有效期、允许时钟偏差和在途请求后才移除。签发 key 只为此用途配置，不复用学生关联加密/查找密钥或服务身份 key。

输出 identity_jws 不为空，单个 compact JWS，最多 16 KiB；权限投影过大导致超限时不截断权限，按签发不可用拒绝。Gateway 只检查可信 Auth 响应的有界形状、三段格式及必要剩余时间，不解读 claims 进行授权或重签；最终服务仍必须验签。

#### 与现有契约的衔接

- 终端不能经 Gateway 访问 ScopeCatalog、DeveloperStatusDirectory、SystemPrincipalDirectory 或签发 RPC；这些是服务到服务方法。不得仅凭 `/auth-center` 前缀自动开放。
- 本契约不改变 UC008 的幂等匿名 token 定向撤销例外，或 UC009 的有效 Session 授权；这两条 Gateway 路由均走 DIRECT，由 Auth 自己验证。
- Auth 用户资料及 UC004 新旧管理入口均走 SESSION，得到 audience=`iwut-auth-center` 的用户 JWS；不能因目标是 Auth 而递归触发签发。
- Gateway 只为外部用户请求编排身份。服务到服务调用继续使用独立 service JWS，不能借用某位用户的 Session。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### JOSE Header

JOSE header 是 JSON 对象，至少包含：

| 字段 | 必需 | 约束 |
| --- | --- | --- |
| `typ` | 是 | 必须**精确**等于 `JWT`（区分大小写；`jwt`、`JWS` 等变体一律拒绝） |
| `alg` | 是 | 必须等于 `RS256` |
| `kid` | 是 | 非空字符串；必须能解析到本地启动配置中的一把 RSA 公钥 |

`alg` 为 `none`、`HS*` 或任何非 `RS256` 值都必须拒绝。禁止根据 token 自带的 `jwk`/`x5u` 等字段在运行时拉取密钥。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

#### 密钥与轮换

- 消费方启动时加载一组 `kid → RSA 公钥` 映射；公钥以来自身份配置的 PEM 文件或等价明确配置提供。
- 至少配置一把公钥；`kid` 为空、重复或公钥无法解析时必须**阻止启动**，不得跳过或降级。
- 每把 RSA 公钥的模数至少 **2048 bit**；小于 2048 bit 的密钥必须**阻止启动**，不得降级接受。
- 轮换采用双密钥重叠：先发布新 kid 的公钥并让签发方开始使用新 kid，旧 kid 公钥保留到持有旧 token 的最长寿命（不超过 `maxTTL`）之后才移除。
- 未知 `kid` 一律认证失败，禁止回退到「唯一的公钥」或首次见到的密钥。
- 不在请求路径上拉取或刷新密钥。密钥分发是部署配置问题，不是每请求行为。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-027`（use-cases/UC-AUTH-027-manage-application-operations-permissions.md）：主流程/授予或撤销、主流程/查询、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/auth-session-identity-issuance-v1.md`（docs 根级共享文档）：范围与权威来源、服务授权扩展、请求与凭据流向
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-027-manage-application-operations-permissions.md` | 168 | `bbbc21f935a1` |
| `platform/contracts/auth-center-api-routing.md` | 125 | `3c4fa072811e` |
| `platform/contracts/auth-session-identity-issuance-v1.md` | 83 | `eb7024a3ea06` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
