<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-004 --spec tools/brief-specs/UC-AUTH-004.json -->
# Brief — UC-AUTH-004：管理 Reviewer 权限

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-004` 管理 Reviewer 权限 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-RVW-001`–`BR-RVW-004`（4 条） |
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

> 平台管理员在 Auth Center 中授予或撤销用户的 `app.version.review` 原子权限，使 Auth 后续签发的 trusted identity 准确反映当前授权，并留下不可变审计记录。

本用例只管理 Reviewer 权限。它不决定 App Center 的审核结果，不提供利益冲突绕过，也不把 `PLATFORM_ADMIN` 自动等同于 reviewer。

### 参与者与 bootstrap

调用者必须是具有 `auth.reviewer.manage` 权限的 `PLATFORM_ADMIN` 用户。平台管理员统揽跨 bounded context 的人员权限治理，但每个能力仍使用独立原子权限。

本用例以 `auth.reviewer.manage` 的显式 grant 表达 PLATFORM_ADMIN 管理能力；主体仍为 USER，不新增 principalType 或通用角色继承。

首个 PLATFORM_ADMIN 通过显式、一次性的运维命令 provision：

```text
auth-center bootstrap-platform-admin --auth-id <existing-user-auth-id>
```

该命令要求 USER principal 已存在，幂等写入管理员 grant 与审计记录；它不是 Auth 普通启动路径，不允许仅因为环境变量仍存在就在每次重启时重新授予已撤销权限。后续管理员全部通过受审计的管理用例授予。bootstrap 在同一事务中保存全局已消费标记：对原目标重跑只报告已执行，不再次写权限或审计；对另一目标重跑拒绝。即使原管理员权限后来被撤销，也不能通过重跑该命令恢复。

### 输入与主流程

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

### 读取 Reviewer 权限状态

`GetReviewerPermission(subjectAuthId)` 是本用例的配套查询，采用与写接口相同的管理员身份要求。
返回目标 authId、是否具有 `app.version.review`、当前 permissionRevision，供客户端提交 expectedRevision
以及在冲突或提交结果未知时重新读取。只返回本能力所需状态，不公开目标的其它权限或学生资料。
不存在、SYSTEM 或不可登录目标不得被当作普通 USER 返回。

### 实现约定

- Proto package 为 `auth_center.v1.reviewer_permission`，service 为 `ReviewerPermissionService`；
  方法为 `ManageReviewerPermission`、`GetReviewerPermission`。
- HTTP 写/读分别为 `PUT` / `GET /v1/users/{subject_auth_id}/reviewer-permission`；Gateway 使用
  SESSION、audience=`iwut-auth-center`，外部前缀为 `/auth-center`。原生 gRPC 和 gRPC-Web 使用同一精确方法授权。
- 写命令 `action` 使用 UNSPECIFIED/GRANT/REVOKE 枚举，UNSPECIFIED 拒绝；expectedRevision
  必填且为正 int64，reason 去除两端空白后为非空 UTF-8 文本且不超过 1024 bytes。
- 已验签 JWS 必须包含 `auth.reviewer.manage`；写入事务内还须确认 actor 为当前 ACTIVE USER 且仍有该权限。
  body/path 不得指定或替代 actor。只修改 reviewer grant，保留其它权限。
- 权限写入、bootstrap 与 [UC010 的签发一致性](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-004)
  使用相同认证事务协调边界；已确认撤销后不能再签出含该权限的新 token。
- 权限 revision 耗尽时拒绝变更，不溢出或回绕。审计插入失败导致权限更新一并回滚；提交结果未知返回不可用，不能伪装成功。
- bootstrap CLI 使用明确的现有 authId 和 Mongo 配置，不启动服务监听，不依赖终端 JWS；审计必须显式区分运维 bootstrap 和已认证用户请求。

### 数据模型

- `auth_principals.permissions`：当前有效原子权限集合，元素唯一且稳定排序。
- `auth_principals.permissionRevision`：正 int64，权限变化时增加。
- `auth_permission_audit_events`：append-only 事件，包含 eventId、subjectAuthId、actorType、action、permission、reason、before/after、beforeRevision、afterRevision、occurredAt。普通管理请求 actorType=`USER`，actorAuthId 为已认证用户；运维初始化 actorType=`BOOTSTRAP_COMMAND`，不伪造 actorAuthId。
- `auth_runtime` 的 `platform-admin-bootstrap` 单例：保存 subjectAuthId、eventId、occurredAt，表示全局初始化已消费，不能通过重启或权限撤销清除。

### API 与实现依赖

管理 API 经 Gateway 使用 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，不使用内部服务身份。可执行 Proto 与路由必须在实现工作包中单独加入。

完整实现依赖普通 USER principal provision、Auth 用户身份签发与 Gateway 到 Auth 的受保护管理路由；在这些入口闭合前，可以实现 Domain/Mongo 核心，但不能暴露绕过认证的临时管理 RPC 或用数据库直改代替本用例。

### 错误语义

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

### 测试与验收

- 非管理员、身份无效、SYSTEM/未知 subject 均被拒绝且不写审计。
- grant/revoke 改变新签 token 的 permissions；Developer 状态可以为 null 且不影响 reviewer 授权。
- 重复动作与 stale revision 冲突；并发最多一个成功。
- 权限状态与 audit event 原子提交或全部回滚。
- 平台管理员未显式获得 reviewer 权限时不能通过 App Center reviewer 入口。

## 业务规则（UC-AUTH-004 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-001 -->
### BR-RVW-001：Auth 权威所有权

Auth Center 是平台人员权限的唯一权威。App Center 只消费已签名 `permissions` claim，不保存 grant，不直接读 Auth 数据库。

<!-- 权威位置: use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-002 -->
### BR-RVW-002：管理员不隐式成为 Reviewer

`auth.reviewer.manage` 与 `app.version.review` 是两个独立权限。PLATFORM_ADMIN 可以管理 reviewer，但若未显式获得 `app.version.review`，不能审核应用；任何身份仍受 App Center 利益冲突规则约束。

<!-- 权威位置: use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-003 -->
### BR-RVW-003：乐观并发与不可变审计

每次有效变更严格增加 permission revision，并记录 actor、subject、action、reason、before/after、时间。并发变更最多一个匹配 expectedRevision；审计事件不可更新或删除。

<!-- 权威位置: use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-004 -->
### BR-RVW-004：撤销传播上界

撤销后 Auth 不再签发包含该权限的新 token。已经签发并通过本地验签的 token 最多继续有效到 trusted-identity-v1 的 `exp`，因此权限撤销传播上界等于用户身份 token 的最大 TTL。首版不为“即时撤销”引入每请求 Auth introspection；若安全策略要求秒级强制失效，必须另立 ADR 选择 denylist/event push 或在线授权，而不能悄悄改变本地验签模型。

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

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，管理接口还须由 Auth 校验 `auth.reviewer.manage`；路由 SESSION 身份本身不授予管理权。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- Reviewer 管理的 `subject_auth_id` 由路径绑定，覆盖消息体中同名值。
- Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
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

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖九个资料/认证 HTTP 方法与两个 Reviewer 管理方法、
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

#### 签名与验签配置

签发入口使用显式开关 `AUTH_IDENTITY_ISSUANCE_ENABLED`（默认 false）。开启要求现有 `AUTH_USER_ENDPOINTS_ENABLED=true`，且下述 signer 配置完整有效；关闭时不注册签发 RPC，不要求私钥，也不影响已有服务和用户接口。不得因为开关开启而放宽原有鉴权。

新增 signer 配置：`AUTH_USER_IDENTITY_SIGNING_KID`、`AUTH_USER_IDENTITY_PRIVATE_KEY_PEM_B64`、`AUTH_USER_IDENTITY_TTL`（默认 `60s`，1–300 整秒）。issuer 沿用 `AUTH_USER_IDENTITY_ISSUER`；既有 `AUTH_USER_IDENTITY_MAX_TTL` 是 verifier 接受上限，不是 signer 默认 TTL。

私钥使用严格标准 Base64 包装的 PKCS#1/PKCS#8 RSA PEM，至少 2048 bit。Auth 自己作为 audience 时必须部署匹配的 verifier 公钥；其他服务先部署新公钥，再切 signer kid，旧验签公钥覆盖旧 token 的有效期、允许时钟偏差和在途请求后才移除。签发 key 只为此用途配置，不复用学生关联加密/查找密钥或服务身份 key。

输出 identity_jws 不为空，单个 compact JWS，最多 16 KiB；权限投影过大导致超限时不截断权限，按签发不可用拒绝。Gateway 只检查可信 Auth 响应的有界形状、三段格式及必要剩余时间，不解读 claims 进行授权或重签；最终服务仍必须验签。

#### 与现有契约的衔接

- 终端不能经 Gateway 访问 ScopeCatalog、DeveloperStatusDirectory、SystemPrincipalDirectory 或签发 RPC；这些是服务到服务方法。不得仅凭 `/auth-center` 前缀自动开放。
- 本契约不改变 UC008 的幂等匿名 token 定向撤销例外，或 UC009 的有效 Session 授权；这两条 Gateway 路由均走 DIRECT，由 Auth 自己验证。
- Auth 用户资料及未来 UC004 管理入口走 SESSION，得到 audience=`iwut-auth-center` 的用户 JWS；不能因目标是 Auth 而递归触发签发。
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
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 当前只消费精确值 `app.version.review`。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含 `app.version.review` 时按权限不足拒绝；Reviewer 不需要 `developer_status`。
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

- `UC-AUTH-004`（use-cases/UC-AUTH-004-manage-reviewer-permission.md）：变更记录
- `platform/contracts/auth-session-identity-issuance-v1.md`（docs 根级共享文档）：范围与权威来源、服务授权扩展、请求与凭据流向
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-004-manage-reviewer-permission.md` | 128 | `57354143ae4b` |
| `platform/contracts/auth-center-api-routing.md` | 69 | `42cd54d3e9bb` |
| `platform/contracts/auth-session-identity-issuance-v1.md` | 79 | `94ff92abf91d` |
| `platform/contracts/trusted-identity-v1.md` | 133 | `4bb4d40a23c8` |
