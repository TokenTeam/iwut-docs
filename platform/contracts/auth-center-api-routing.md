# Auth Center API 路由与 HTTP 映射

状态：`ACTIVE`

本契约补充 [App 设备认证与 Session v1](auth-device-session-v1.md) 的 HTTP 绑定。
业务语义及错误 reason 仍由 UC-AUTH-004–009、UC-AUTH-011/012/013 拥有；可执行 HTTP annotation、消息字段和
生成客户端位于独立 API 仓库。现有 gRPC package、方法名、字段编号保持不变。

## 路由边界

与 [App API 路由](app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
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

UC011 追加三个 DIRECT 路由，完整字段及 Session 例外见 [邮箱设置与注册协议](auth-email-binding-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../../auth-center/implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

## JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。
- 普通设备注册/登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

## 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖九个资料/认证 HTTP 方法、两个旧 Reviewer 管理方法与两个新增应用审核权限方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

## 治理工作包路由

UC021/022/023 的管理入口使用 SESSION，Auth audience USER JWS 必须携带 account_revision 并在线复核；UC024 使用 DIRECT 有效 Session；UC025 使用 DIRECT 专用设备证明/用途隔离令牌。精确 package/service/method 和 POST /v1 路径分别引用对应已接受 UC 的 API 表，不提供 wildcard 或公共内部服务入口。API annotations 与 Gateway 清单须逐项验收；后端实现不等于公网已启用。

- [UC021](../../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md#api)：platform_administrator.PlatformAdministratorService 三方法。
- [UC022](../../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md#参与者与接口)：account_management.AccountManagementService 两方法。
- [UC023](../../auth-center/use-cases/UC-AUTH-023-suspend-and-restore-developer.md#参与者与-api)：developer_management.DeveloperManagementService 两方法。
- [UC024](../../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md#参与者与接口)：developer_withdrawal.DeveloperWithdrawalService 四方法。
- [UC025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md#api-与确认过程)：account_closure.AccountClosureService 五方法；确认/查询专用 header 不可被当作一般 Authorization。

## UC020 同账号 Session 管理

独立 `auth_center.v1.session_management.SessionManagementService`，由默认关闭的 `AUTH_SESSION_MANAGEMENT_ENABLED` 控制：

| Method | Auth 内部路径 | RPC | Gateway 模式 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/sessions:list` | SessionManagementService/ListOwnSessions | DIRECT | 200 |
| POST | `/v1/users/me/sessions:revoke` | SessionManagementService/RevokeOwnSessions | DIRECT | 200 |

公网路径加统一 `/auth-center` 前缀。只传唯一 x-iwut-session，不先换 JWS；Auth 在只读/命令最终事务重新检查当前 Session，不刷新 lastUsedAt。严格 ProtoJSON、16 KiB、无 query、no-store。Gateway 实际清单与三协议验收另行交付；新方法未启用时不回退至匿名或普通 JWS 路径。
