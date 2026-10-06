# Gateway 外部 API 接入清单

状态：`ACTIVE`

- 快照日期：2026-10-07
- 统一 API 基线：`9f914c5`
- Gateway 实现基线：`7a3eb7c`

## 目的与使用规则

本清单从已接受的 Auth Center / App Center UC、共享契约和统一 API Proto 派生，回答三个问题：哪些 API 是终端外部入口、Gateway 应采用什么身份策略、当前是否已经接入。它是 Gateway 的实施与验收清单，不复制业务规则；业务语义、权限判断、错误和并发规则仍以所链接的 UC/契约为准。

- 每个外部 `method + path` 必须在 Gateway 静态目录中有精确 route；不能用 service/package/path wildcard 代替。
- 不要求每个 route 单独建立 Gateway UC。已有策略组合下的新接口只增加 route、生成物和三协议测试；只有出现新的 Gateway 行为或信任边界时才新增/扩展 UC、ADR。
- Proto API 的外部路径由服务前缀加内部 annotation 得到：Auth 为 `/auth-center`，App 为 `/app-center`。标准 OAuth/OIDC 端点是 `OIDC_HTTP` 的根路径例外。
- 表中状态只表示 Gateway 接入状态，不表示生产开关已经启用，也不替代 Auth/App 自身的实现状态。
- `HTTP_JSON / GRPC / GRPC_WEB` 是普通 Proto route 的目标协议集合；OAuth/OIDC 标准端点仅为 HTTP。

## 状态与策略图例

| 标记 | 含义 |
| --- | --- |
| `VERIFIED` | 已进入 `config/routes.v2.yaml`，并完成对应业务流的本地三协议联合验证。 |
| `IMPLEMENTED` | 已进入 Gateway `7a3eb7c` 的精确目录，且单元、ForwardAuth、gRPC proxy、Traefik 生成与全量回归通过；对应业务流的真实联合验收仍按各 UC 发布门禁完成。 |
| `BACKLOG` | 尚未进入目录；已有 UC/ADR 足以决定行为，不需要为该 route 新写 Gateway UC。实施时仍须扩充精确 allowlist、生成物与测试。 |
| `POLICY_GAP` | Gateway 运行时无法表达所需凭据组合；当前清单无此状态条目。 |
| `GW002` | 依赖仍为 `PROPOSED / NOT_STARTED` 的 UC-GW-002 与 `OIDC_HTTP` 专用适配，当前不得启用。 |
| `INTERNAL_ONLY` | 服务间原生 gRPC；不得添加终端 HTTP、gRPC 或 gRPC-Web route。 |

| 策略 | Gateway 行为 |
| --- | --- |
| `PUBLIC` | 禁止 Session、Authorization 与外来内部身份；匿名转发。 |
| `AUTH_DIRECT_SESSION` | 要求唯一 Session，不换 USER JWS，保留 Session 给 Auth 自行验证。 |
| `AUTH_OPTIONAL_DIRECT_SESSION` | Session 可缺失；一旦提供必须合法并保留给 Auth，坏 Session 不得降级为匿名。 |
| `AUTH_USER` | 要求 Session，经 UC-AUTH-010 换取 `iwut-auth-center` USER JWS，原 Session 不下传。 |
| `APP_USER` | 要求 Session，经 UC-AUTH-010 换取 `iwut-app-center` USER JWS，原 Session 不下传。 |
| `APP_OPTIONAL_USER` | 无 Session 时匿名；有 Session 时必须成功换取 App USER JWS。 |
| `ACCOUNT_CLOSURE` | 禁止通用 Session/JWS/OAuth；Auth 自行验证设备证明或用途隔离 header。 |
| `APP_HIGH_RISK` | `APP_USER` 加精确保留 `x-iwut-high-risk-proof`。 |
| `OIDC_HTTP` | 标准 OAuth/OIDC 的 Basic、Bearer、指定 Session/Cookie/form 组合；由 UC-GW-002 精确规定。 |

## 汇总

| 范围 | 外部 method/path 数 | `VERIFIED` | `IMPLEMENTED` | `BACKLOG` | `POLICY_GAP` | `GW002` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auth Proto HTTP | 44 | 15 | 29 | 0 | 0 | 0 |
| OAuth/OIDC 标准 HTTP | 8 | 0 | 0 | 0 | 0 | 8 |
| App Proto HTTP | 43 | 8 | 35 | 0 | 0 | 0 |
| **合计** | **95** | **23** | **64** | **0** | **0** | **8** |

因此，当前 Gateway 目录已接入全部 87 个 Auth/App Proto 外部 method/path：23 个已完成对应业务流的真实联验，64 个已实现并通过策略类别的三协议真实 smoke。剩余 8/95 是 UC-GW-002 管辖的 OAuth/OIDC 标准 HTTP 端点，仍失败关闭。“已进入 Gateway 目录”仍不等于所有后端 feature flag 已开启或已生产发布。

## Auth Center 外部入口

### 已接入

| UC | 接口（RPC — 外部 HTTP） | 策略 | 状态 / routeId |
| --- | --- | --- | --- |
| [UC-AUTH-006] | `BeginUserRegistration` — `POST /auth-center/v1/registrations` | `PUBLIC` | `VERIFIED` — `auth.begin-user-registration` |
| [UC-AUTH-006] | `CompleteUserRegistration` — `POST /auth-center/v1/registrations/{operation_id}/completion` | `PUBLIC` | `VERIFIED` — `auth.complete-user-registration` |
| [UC-AUTH-007] | `BeginDeviceLogin` — `POST /auth-center/v1/device-logins` | `PUBLIC` | `VERIFIED` — `auth.begin-device-login` |
| [UC-AUTH-007] | `CompleteDeviceLogin` — `POST /auth-center/v1/device-logins/{operation_id}/completion` | `PUBLIC` | `VERIFIED` — `auth.complete-device-login` |
| [UC-AUTH-008] | `RevokeCurrentSession` — `DELETE /auth-center/v1/sessions/current` | `AUTH_DIRECT_SESSION` | `VERIFIED` — `auth.revoke-current-session` |
| [UC-AUTH-009] | `RevokeOwnCredential` — `DELETE /auth-center/v1/users/me/credentials/{credential_id}` | `AUTH_DIRECT_SESSION` | `VERIFIED` — `auth.revoke-own-credential` |
| [UC-AUTH-005] | `GetOwnProfile` — `GET /auth-center/v1/users/me/profile` | `AUTH_USER` | `VERIFIED` — `auth.get-own-profile` |
| [UC-AUTH-005] | `GetProfileEditingSchema` — `GET /auth-center/v1/user-profile-schema` | `AUTH_USER` | `VERIFIED` — `auth.get-profile-editing-schema` |
| [UC-AUTH-005] | `EditOwnProfile` — `PATCH /auth-center/v1/users/me/profile` | `AUTH_USER` | `VERIFIED` — `auth.edit-own-profile` |
| [UC-AUTH-004] | `ManageReviewerPermission` — `PUT /auth-center/v1/users/{subject_auth_id}/reviewer-permission` | `AUTH_USER` | `VERIFIED` — `auth.manage-reviewer-permission` |
| [UC-AUTH-004] | `GetReviewerPermission` — `GET /auth-center/v1/users/{subject_auth_id}/reviewer-permission` | `AUTH_USER` | `VERIFIED` — `auth.get-reviewer-permission` |
| [UC-AUTH-004] | `ManageApplicationReviewPermission` — `PUT /auth-center/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | `AUTH_USER` | `VERIFIED` — `auth.manage-application-review-permission` |
| [UC-AUTH-004] | `GetApplicationReviewPermissions` — `GET /auth-center/v1/users/{subject_auth_id}/application-review-permissions` | `AUTH_USER` | `VERIFIED` — `auth.get-application-review-permissions` |
| [UC-AUTH-027] | `ManageApplicationOperationsPermission` — `PUT /auth-center/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | `AUTH_USER` | `VERIFIED` — `auth.manage-application-operations-permission` |
| [UC-AUTH-027] | `GetApplicationOperationsPermissions` — `GET /auth-center/v1/users/{subject_auth_id}/application-operation-permissions` | `AUTH_USER` | `VERIFIED` — `auth.get-application-operations-permissions` |
| [UC-AUTH-011] | `BeginSetEmail` — `POST /auth-center/v1/email-bindings` | `AUTH_OPTIONAL_DIRECT_SESSION` | `IMPLEMENTED` — `auth.begin-set-email` |
| [UC-AUTH-011] | `CompleteSetEmail` — `POST /auth-center/v1/email-bindings/{operation_id}/completion` | `AUTH_OPTIONAL_DIRECT_SESSION` | `IMPLEMENTED` — `auth.complete-set-email` |
| [UC-AUTH-011] | `GetOwnEmailBinding` — `GET /auth-center/v1/users/me/email-binding` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.get-own-email-binding` |
| [UC-AUTH-025] | `BeginAccountClosure` — `POST /auth-center/v1/account-closures:begin` | `ACCOUNT_CLOSURE`（设备定位在 body） | `IMPLEMENTED` — `auth.begin-account-closure` |
| [UC-AUTH-025] | `PrepareAccountClosure` — `POST /auth-center/v1/account-closures:prepare` | `ACCOUNT_CLOSURE`（设备证明在 body） | `IMPLEMENTED` — `auth.prepare-account-closure` |
| [UC-AUTH-025] | `ConfirmAccountClosure` — `POST /auth-center/v1/account-closures:confirm` | `ACCOUNT_CLOSURE` + confirmation | `IMPLEMENTED` — `auth.confirm-account-closure` |
| [UC-AUTH-025] | `CancelAccountClosure` — `POST /auth-center/v1/account-closures:cancel` | `ACCOUNT_CLOSURE` + confirmation | `IMPLEMENTED` — `auth.cancel-account-closure` |
| [UC-AUTH-025] | `GetAccountClosure` — `POST /auth-center/v1/account-closures:get` | `ACCOUNT_CLOSURE` + receipt | `IMPLEMENTED` — `auth.get-account-closure` |
| [UC-AUTH-026] | `BeginApplicationCloseReauth` — `POST /auth-center/v1/application-close-reauth:begin` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.begin-application-close-reauth` |
| [UC-AUTH-026] | `CompleteApplicationCloseReauth` — `POST /auth-center/v1/application-close-reauth:complete` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.complete-application-close-reauth` |

### 已实现：复用现有策略

| UC | 接口（RPC — 外部 HTTP） | 策略 | 状态 |
| --- | --- | --- | --- |
| [UC-AUTH-012] | `BeginEmailLogin` — `POST /auth-center/v1/email-logins` | `PUBLIC` | `IMPLEMENTED` — `auth.begin-email-login` |
| [UC-AUTH-012] | `CompleteEmailLogin` — `POST /auth-center/v1/email-logins/{operation_id}/completion` | `PUBLIC` | `IMPLEMENTED` — `auth.complete-email-login` |
| [UC-AUTH-013] | `ApplyForDeveloper` — `POST /auth-center/v1/users/me/developer-application` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.apply-for-developer` |
| [UC-AUTH-013] | `GetOwnDeveloperEligibility` — `GET /auth-center/v1/users/me/developer-eligibility` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.get-own-developer-eligibility` |
| [UC-AUTH-018] | `ListOwnApplicationGrants` — `POST /auth-center/v1/users/me/application-grants:list` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.list-own-application-grants` |
| [UC-AUTH-018] | `RevokeOwnApplicationGrant` — `POST /auth-center/v1/users/me/application-grants/{grant_id}:revoke` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.revoke-own-application-grant` |
| [UC-AUTH-020] | `ListOwnSessions` — `POST /auth-center/v1/users/me/sessions:list` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.list-own-sessions` |
| [UC-AUTH-020] | `RevokeOwnSessions` — `POST /auth-center/v1/users/me/sessions:revoke` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.revoke-own-sessions` |
| [UC-AUTH-021] | `ManagePlatformAdministrator` — `POST /auth-center/v1/platform-administrators:manage` | `AUTH_USER` | `IMPLEMENTED` — `auth.manage-platform-administrator` |
| [UC-AUTH-021] | `GetPlatformAdministrator` — `POST /auth-center/v1/platform-administrators:get` | `AUTH_USER` | `IMPLEMENTED` — `auth.get-platform-administrator` |
| [UC-AUTH-021] | `ListPlatformAdministrators` — `POST /auth-center/v1/platform-administrators:list` | `AUTH_USER` | `IMPLEMENTED` — `auth.list-platform-administrators` |
| [UC-AUTH-022] | `ManageUserAccountStatus` — `POST /auth-center/v1/user-accounts:manage-status` | `AUTH_USER` | `IMPLEMENTED` — `auth.manage-user-account-status` |
| [UC-AUTH-022] | `GetUserAccountStatus` — `POST /auth-center/v1/user-accounts:get-status` | `AUTH_USER` | `IMPLEMENTED` — `auth.get-user-account-status` |
| [UC-AUTH-023] | `ManageDeveloperStatus` — `POST /auth-center/v1/developers:manage-status` | `AUTH_USER` | `IMPLEMENTED` — `auth.manage-developer-status` |
| [UC-AUTH-023] | `GetManagedDeveloperStatus` — `POST /auth-center/v1/developers:get-managed-status` | `AUTH_USER` | `IMPLEMENTED` — `auth.get-managed-developer-status` |
| [UC-AUTH-024] | `PrepareDeveloperWithdrawal` — `POST /auth-center/v1/users/me/developer-withdrawal:prepare` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.prepare-developer-withdrawal` |
| [UC-AUTH-024] | `ConfirmDeveloperWithdrawal` — `POST /auth-center/v1/users/me/developer-withdrawal:confirm` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.confirm-developer-withdrawal` |
| [UC-AUTH-024] | `CancelDeveloperWithdrawal` — `POST /auth-center/v1/users/me/developer-withdrawal:cancel` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.cancel-developer-withdrawal` |
| [UC-AUTH-024] | `GetDeveloperWithdrawal` — `POST /auth-center/v1/users/me/developer-withdrawal:get` | `AUTH_DIRECT_SESSION` | `IMPLEMENTED` — `auth.get-developer-withdrawal` |

### 待设计/实现策略能力

当前 44 条 Auth Proto 外部入口已全部进入 Gateway 精确目录，无 `BACKLOG` 或 `POLICY_GAP`。

### OAuth/OIDC 标准端点

这些路径由 [OAuth/OIDC v1] 和 [UC-GW-002] 共同约束，不从 Proto HTTP annotation 推导。

| Auth UC | 外部 HTTP | 策略 | 状态 |
| --- | --- | --- | --- |
| [UC-AUTH-014] | `GET /.well-known/openid-configuration` | `OIDC_HTTP` discovery | `GW002` |
| [UC-AUTH-014] | `GET /jwks` | `OIDC_HTTP` public keys | `GW002` |
| [UC-AUTH-014] | `GET /authorize` | `OIDC_HTTP` portal/session/cookie 精确策略 | `GW002` |
| [UC-AUTH-014] | `POST /authorize` | `OIDC_HTTP` form + portal/session/cookie 精确策略 | `GW002` |
| [UC-AUTH-015], [UC-AUTH-016] | `POST /token` | `OIDC_HTTP` form + PUBLIC/Basic client authentication | `GW002` |
| [UC-AUTH-017] | `GET /userinfo` | `OIDC_HTTP` Bearer | `GW002` |
| [UC-AUTH-017] | `POST /userinfo` | `OIDC_HTTP` Bearer | `GW002` |
| [UC-AUTH-018] | `POST /revoke` | `OIDC_HTTP` form + PUBLIC/Basic client authentication | `GW002` |

## App Center 外部入口

### 已接入

| UC | 接口（RPC — 外部 HTTP） | 策略 | 状态 / routeId |
| --- | --- | --- | --- |
| [UC-APP-001] | `CreateApplication` — `POST /app-center/v1/applications` | `APP_USER` | `VERIFIED` — `app.create-application` |
| [UC-APP-005] | `DecideApplicationVersionReview` — `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` | `APP_USER` | `VERIFIED` — `app.decide-application-version-review` |
| [UC-APP-023] | `ResolveLaunchTarget` — `POST /app-center/v1/applications/{application_id}/launch-target:resolve` | `APP_OPTIONAL_USER` | `VERIFIED` — `app.resolve-launch-target` |
| [UC-APP-024] | `ListPublicApplications` — `POST /app-center/v1/catalog/applications:search` | `APP_OPTIONAL_USER` | `VERIFIED` — `app.list-public-applications` |
| [UC-APP-024] | `GetPublicApplication` — `POST /app-center/v1/catalog/applications/{application_id}:get` | `APP_OPTIONAL_USER` | `VERIFIED` — `app.get-public-application` |
| [UC-APP-028] | `GetApplicationPlatformAvailability` — `GET /app-center/v1/applications/{application_id}/platform-availability` | `APP_USER` | `VERIFIED` — `app.get-application-platform-availability` |
| [UC-APP-028] | `SuspendApplication` — `POST /app-center/v1/applications/{application_id}:suspend` | `APP_USER` | `VERIFIED` — `app.suspend-application` |
| [UC-APP-028] | `RestoreApplication` — `POST /app-center/v1/applications/{application_id}:restore` | `APP_USER` | `VERIFIED` — `app.restore-application` |
| [UC-APP-027] | `GetApplicationClosurePreview` — `GET /app-center/v1/applications/{application_id}/closure-preview` | `APP_USER` | `IMPLEMENTED` — `app.get-application-closure-preview` |
| [UC-APP-027] | `CloseApplication` — `POST /app-center/v1/applications/{application_id}:close` | `APP_HIGH_RISK` | `IMPLEMENTED` — `app.close-application` |
| [UC-APP-027] | `GetApplicationClosure` — `GET /app-center/v1/applications/{application_id}/closure` | `APP_USER` | `IMPLEMENTED` — `app.get-application-closure` |

### 已实现：复用现有策略

| UC | 接口（RPC — 外部 HTTP） | 策略 | 状态 |
| --- | --- | --- | --- |
| [UC-APP-002] | `CreateApplicationVersion` — `POST /app-center/v1/applications/{application_id}/versions` | `APP_USER` | `IMPLEMENTED` — `app.create-application-version` |
| [UC-APP-003] | `UpdateApplicationVersion` — `PUT /app-center/v1/applications/{application_id}/versions/{version_id}` | `APP_USER` | `IMPLEMENTED` — `app.update-application-version` |
| [UC-APP-004] | `SubmitApplicationVersionReview` — `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews` | `APP_USER` | `IMPLEMENTED` — `app.submit-application-version-review` |
| [UC-APP-006] | `RestoreRejectedApplicationVersionToDraft` — `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/draft-restoration` | `APP_USER` | `IMPLEMENTED` — `app.restore-rejected-application-version-to-draft` |
| [UC-APP-007] | `PlaceApprovedVersionInTestSlot` — `PUT /app-center/v1/applications/{application_id}/publications/{rpc_api_major}/test-slot` | `APP_USER` | `IMPLEMENTED` — `app.place-approved-version-in-test-slot` |
| [UC-APP-008] | `CreateOrRotateTesterJoinLink` — `POST /app-center/v1/applications/{application_id}/tester-join-links` | `APP_USER` | `IMPLEMENTED` — `app.create-or-rotate-tester-join-link` |
| [UC-APP-009] | `JoinApplicationAsTester` — `POST /app-center/v1/tester-join-links/{join_link_id}/memberships` | `APP_USER` | `IMPLEMENTED` — `app.join-application-as-tester` |
| [UC-APP-010] | `RemoveApplicationTester` — `DELETE /app-center/v1/applications/{application_id}/tester-memberships/{membership_id}` | `APP_USER` | `IMPLEMENTED` — `app.remove-application-tester` |
| [UC-APP-011] | `RevokeTesterJoinLink` — `DELETE /app-center/v1/applications/{application_id}/tester-join-links/{join_link_id}` | `APP_USER` | `IMPLEMENTED` — `app.revoke-tester-join-link` |
| [UC-APP-012] | `ResolveTestLaunchTarget` — `POST /app-center/v1/applications/{application_id}/test-launch:resolve` | `APP_USER` | `IMPLEMENTED` — `app.resolve-test-launch-target` |
| [UC-APP-013] | `CreateApplicationProfileRevision` — `POST /app-center/v1/applications/{application_id}/profile-revisions` | `APP_USER` | `IMPLEMENTED` — `app.create-application-profile-revision` |
| [UC-APP-014] | `UpdateApplicationProfileRevision` — `PUT /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}` | `APP_USER` | `IMPLEMENTED` — `app.update-application-profile-revision` |
| [UC-APP-015] | `SubmitApplicationProfileRevisionReview` — `POST /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews` | `APP_USER` | `IMPLEMENTED` — `app.submit-application-profile-revision-review` |
| [UC-APP-016] | `DecideApplicationProfileRevisionReview` — `POST /app-center/v1/applications/{application_id}/profile-revisions/{profile_revision_id}/reviews/{profile_review_id}/decision` | `APP_USER` | `IMPLEMENTED` — `app.decide-application-profile-revision-review` |
| [UC-APP-018] | `RegisterOAuthClient` — `POST /app-center/v1/applications/{application_id}/oauth-registrations/{channel}/clients` | `APP_USER` | `IMPLEMENTED` — `app.register-oauth-client` |
| [UC-APP-018] | `GetApplicationOAuthRegistration` — `GET /app-center/v1/applications/{application_id}/oauth-registrations/{channel}` | `APP_USER` | `IMPLEMENTED` — `app.get-application-oauth-registration` |
| [UC-APP-018] | `SetOAuthClientStatus` — `PUT /app-center/v1/oauth-clients/{client_id}/status` | `APP_USER` | `IMPLEMENTED` — `app.set-oauth-client-status` |
| [UC-APP-018] | `GetOAuthClientCredentialMetadata` — `GET /app-center/v1/oauth-clients/{client_id}/credential` | `APP_USER` | `IMPLEMENTED` — `app.get-oauth-client-credential-metadata` |
| [UC-APP-018] | `RotateOAuthClientSecret` — `POST /app-center/v1/oauth-clients/{client_id}/credential-rotations` | `APP_USER` | `IMPLEMENTED` — `app.rotate-oauth-client-secret` |
| [UC-APP-020] | `SetApprovedVersionInStableSlot` — `PUT /app-center/v1/applications/{application_id}/publications/{rpc_api_major}/stable-slot` | `APP_USER` | `IMPLEMENTED` — `app.set-approved-version-in-stable-slot` |
| [UC-APP-020] | `ClearStableSlot` — `DELETE /app-center/v1/applications/{application_id}/publications/{rpc_api_major}/stable-slot` | `APP_USER` | `IMPLEMENTED` — `app.clear-stable-slot` |
| [UC-APP-021] | `SetGreyRollout` — `PUT /app-center/v1/applications/{application_id}/publications/{rpc_api_major}/grey-rollout` | `APP_USER` | `IMPLEMENTED` — `app.set-grey-rollout` |
| [UC-APP-021] | `ClearGreyRollout` — `DELETE /app-center/v1/applications/{application_id}/publications/{rpc_api_major}/grey-rollout` | `APP_USER` | `IMPLEMENTED` — `app.clear-grey-rollout` |
| [UC-APP-022] | `GetApplicationFilter` — `GET /app-center/v1/applications/{application_id}/filter` | `APP_USER` | `IMPLEMENTED` — `app.get-application-filter` |
| [UC-APP-022] | `SetApplicationFilter` — `PUT /app-center/v1/applications/{application_id}/filter` | `APP_USER` | `IMPLEMENTED` — `app.set-application-filter` |
| [UC-APP-022] | `ClearApplicationFilter` — `DELETE /app-center/v1/applications/{application_id}/filter` | `APP_USER` | `IMPLEMENTED` — `app.clear-application-filter` |
| [UC-APP-026] | `GetApplicationOwnership` — `GET /app-center/v1/applications/{application_id}/ownership` | `APP_USER` | `IMPLEMENTED` — `app.get-application-ownership` |
| [UC-APP-026] | `InitiateApplicationAdminTransfer` — `POST /app-center/v1/applications/{application_id}/admin-transfers` | `APP_USER` | `IMPLEMENTED` — `app.initiate-application-admin-transfer` |
| [UC-APP-026] | `GetApplicationAdminTransfer` — `GET /app-center/v1/application-admin-transfers/{transfer_id}` | `APP_USER` | `IMPLEMENTED` — `app.get-application-admin-transfer` |
| [UC-APP-026] | `AcceptApplicationAdminTransfer` — `POST /app-center/v1/application-admin-transfers/{transfer_id}:accept` | `APP_USER` | `IMPLEMENTED` — `app.accept-application-admin-transfer` |
| [UC-APP-026] | `RejectApplicationAdminTransfer` — `POST /app-center/v1/application-admin-transfers/{transfer_id}:reject` | `APP_USER` | `IMPLEMENTED` — `app.reject-application-admin-transfer` |
| [UC-APP-026] | `CancelApplicationAdminTransfer` — `POST /app-center/v1/application-admin-transfers/{transfer_id}:cancel` | `APP_USER` | `IMPLEMENTED` — `app.cancel-application-admin-transfer` |

### 待设计/实现策略能力

当前 43 条 App Proto 外部入口已全部进入 Gateway 精确目录，无 `BACKLOG` 或 `POLICY_GAP`。

## 明确不接入 Gateway 的内部 RPC

下列 API 即使已经由 Auth/App 实现，也不得为了“覆盖全部 API”加入终端 route：

| 所属 | UC / 契约 | 内部 service / method | 原因 |
| --- | --- | --- | --- |
| Auth | [UC-AUTH-001] | `ScopeCatalogService/GetScopeCatalogSnapshot` | 服务内/受信调用方目录读取，无终端 HTTP annotation。 |
| Auth | [UC-AUTH-002] | `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | App→Auth 批量状态查询。 |
| Auth | [UC-AUTH-003] | `SystemPrincipalDirectory/ResolveSystemPrincipal` | 受信系统主体解析。 |
| Auth | [UC-AUTH-010] | `UserIdentityService/IssueUserIdentityFromSession` | Gateway→Auth 的身份交换内部调用。 |
| Auth | [UC-AUTH-019] | `OAuthDelegationService/IssueDelegationContext` | Gateway→Auth 的 OAuth 委托交换内部调用。 |
| Auth | [UC-AUTH-026] | `ApplicationClosureService/ApplyApplicationClosure`, `GetApplicationClosureStatus` | App service identity 专用。 |
| Auth | [Account owner exit v1] | `AccountOwnerExitDecisionService/GetAccountOwnerExitDecision` | App service identity 专用。 |
| App | [UC-APP-019] | `OAuthClientProviderService` 五个方法 | Auth service identity 专用。 |
| App | [UC-APP-025] | `AccountOwnerExitService` 三个方法 | Auth service identity 专用。 |

## 下一批实施切分建议

1. **Proto 业务流联合验收**：按 Auth/App feature flag 和依赖组分批打开真实后端，补齐 64 条 `IMPLEMENTED` route 的业务成功/拒绝、一次性 secret/token 响应与下游调用次数验收；不再新增 Gateway 策略类型。
2. **特殊终端载体验收**：开启相应 Auth/App feature flag，用真实 Traefik、Gateway、Auth、App 与 Mongo 补齐邮箱双分支、Prepare token 正文、注销用途隔离和 proof 真实拒绝的三协议联合测试。
3. **OAuth/OIDC**：单独完成并接受 [UC-GW-002] 后再接 8 个 `OIDC_HTTP` method/path；不得和普通 Proto route 批次混开。`x-iwut-access-token` 在此之前于所有已有 route 全局拒绝并清理。
4. 每批完成后以本文件为验收台账：代码和适配器边界完成时可先记 `IMPLEMENTED`，对应业务流的真实三协议联合验收后才记 `VERIFIED`，并记录 Gateway/API commit；不要用“后端已实现”代替 Gateway 联合验证。

## 权威来源

- [ADR-GW-002：路由凭据载体与条件身份交换策略](adr/ADR-GW-002-route-credential-and-identity-policy.md)
- [UC-GW-001：按路由认证并转发请求](use-cases/UC-GW-001-authenticate-and-forward.md)
- [UC-GW-002：应用委托请求鉴权与转发](use-cases/UC-GW-002-authenticate-oauth-and-forward.md)
- [UC-GW-003：为公开读取附加可选用户身份](use-cases/UC-GW-003-attach-optional-user-identity.md)
- [Auth Center API 路由与 HTTP 映射](../platform/contracts/auth-center-api-routing.md)
- [App Center API 路由 v1](../platform/contracts/app-center-api-routing.md)
- [OAuth/OIDC v1](../platform/contracts/oauth-oidc-v1.md)
- 统一 API Proto `9f914c5` 的 `google.api.http` annotations；Gateway 当前目录 `7a3eb7c` 的 `config/routes.v2.yaml`。

[UC-AUTH-001]: ../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md
[UC-AUTH-002]: ../auth-center/use-cases/UC-AUTH-002-batch-get-developer-statuses.md
[UC-AUTH-003]: ../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md
[UC-AUTH-004]: ../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md
[UC-AUTH-005]: ../auth-center/use-cases/UC-AUTH-005-edit-own-user-profile.md
[UC-AUTH-006]: ../auth-center/use-cases/UC-AUTH-006-create-user.md
[UC-AUTH-007]: ../auth-center/use-cases/UC-AUTH-007-login.md
[UC-AUTH-008]: ../auth-center/use-cases/UC-AUTH-008-revoke-own-session.md
[UC-AUTH-009]: ../auth-center/use-cases/UC-AUTH-009-revoke-own-credential.md
[UC-AUTH-010]: ../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md
[UC-AUTH-011]: ../auth-center/use-cases/UC-AUTH-011-set-and-activate-email.md
[UC-AUTH-012]: ../auth-center/use-cases/UC-AUTH-012-login-with-email.md
[UC-AUTH-013]: ../auth-center/use-cases/UC-AUTH-013-apply-for-developer.md
[UC-AUTH-014]: ../auth-center/use-cases/UC-AUTH-014-authorize-application.md
[UC-AUTH-015]: ../auth-center/use-cases/UC-AUTH-015-exchange-authorization-code.md
[UC-AUTH-016]: ../auth-center/use-cases/UC-AUTH-016-refresh-application-tokens.md
[UC-AUTH-017]: ../auth-center/use-cases/UC-AUTH-017-get-oidc-user-info.md
[UC-AUTH-018]: ../auth-center/use-cases/UC-AUTH-018-revoke-application-authorization.md
[UC-AUTH-019]: ../auth-center/use-cases/UC-AUTH-019-issue-delegation-context.md
[UC-AUTH-020]: ../auth-center/use-cases/UC-AUTH-020-manage-own-sessions.md
[UC-AUTH-021]: ../auth-center/use-cases/UC-AUTH-021-manage-platform-administrators.md
[UC-AUTH-022]: ../auth-center/use-cases/UC-AUTH-022-disable-and-restore-user-account.md
[UC-AUTH-023]: ../auth-center/use-cases/UC-AUTH-023-suspend-and-restore-developer.md
[UC-AUTH-024]: ../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md
[UC-AUTH-025]: ../auth-center/use-cases/UC-AUTH-025-close-own-account.md
[UC-AUTH-026]: ../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md
[UC-AUTH-027]: ../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md
[UC-APP-001]: ../app-center/use-cases/UC-APP-001-create-application.md
[UC-APP-002]: ../app-center/use-cases/UC-APP-002-create-application-version.md
[UC-APP-003]: ../app-center/use-cases/UC-APP-003-update-draft-application-version.md
[UC-APP-004]: ../app-center/use-cases/UC-APP-004-submit-application-version-review.md
[UC-APP-005]: ../app-center/use-cases/UC-APP-005-decide-application-version-review.md
[UC-APP-006]: ../app-center/use-cases/UC-APP-006-restore-rejected-version-to-draft.md
[UC-APP-007]: ../app-center/use-cases/UC-APP-007-place-approved-version-in-test-slot.md
[UC-APP-008]: ../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md
[UC-APP-009]: ../app-center/use-cases/UC-APP-009-join-application-as-tester.md
[UC-APP-010]: ../app-center/use-cases/UC-APP-010-remove-application-tester.md
[UC-APP-011]: ../app-center/use-cases/UC-APP-011-revoke-tester-join-link.md
[UC-APP-012]: ../app-center/use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md
[UC-APP-013]: ../app-center/use-cases/UC-APP-013-create-application-profile-revision.md
[UC-APP-014]: ../app-center/use-cases/UC-APP-014-update-draft-application-profile-revision.md
[UC-APP-015]: ../app-center/use-cases/UC-APP-015-submit-application-profile-revision-review.md
[UC-APP-016]: ../app-center/use-cases/UC-APP-016-decide-application-profile-revision-review.md
[UC-APP-018]: ../app-center/use-cases/UC-APP-018-manage-oauth-client.md
[UC-APP-019]: ../app-center/use-cases/UC-APP-019-resolve-oauth-authorization-context.md
[UC-APP-020]: ../app-center/use-cases/UC-APP-020-manage-stable-publication-slot.md
[UC-APP-021]: ../app-center/use-cases/UC-APP-021-manage-grey-rollout.md
[UC-APP-022]: ../app-center/use-cases/UC-APP-022-manage-application-filter.md
[UC-APP-023]: ../app-center/use-cases/UC-APP-023-resolve-unified-launch-target.md
[UC-APP-024]: ../app-center/use-cases/UC-APP-024-query-public-application-catalog.md
[UC-APP-025]: ../app-center/use-cases/UC-APP-025-coordinate-account-owner-exit.md
[UC-APP-026]: ../app-center/use-cases/UC-APP-026-transfer-application-administration.md
[UC-APP-027]: ../app-center/use-cases/UC-APP-027-close-application.md
[UC-APP-028]: ../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md
[OAuth/OIDC v1]: ../platform/contracts/oauth-oidc-v1.md
[Account owner exit v1]: ../platform/contracts/account-owner-exit-v1.md
[UC-GW-002]: use-cases/UC-GW-002-authenticate-oauth-and-forward.md
[UC-GW-004]: use-cases/UC-GW-004-forward-optional-session-to-auth.md
[UC-GW-005]: use-cases/UC-GW-005-forward-account-closure-credentials.md
[UC-GW-006]: use-cases/UC-GW-006-forward-application-close-proof.md
