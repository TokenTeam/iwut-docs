<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-030 --spec tools/brief-specs/UC-AUTH-030.json -->
# Brief — UC-AUTH-030：读写应用用户存储

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-030` 读写应用用户存储 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-AUS-001`–`BR-AUS-007`（7 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/oauth-oidc-v1.md` |

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

第三方应用使用用户授予的 OAuth access token，在 Auth Center 中为该用户读写一小块由应用解释的隔离字符串 KV。存储逻辑上属于“某个应用在某个用户下的数据”，不是用户资料、平台权限、OIDC claim 或学校验证事实；应用写入不能改变 UC005 UserProfile，也不能经 UC028 UserInfo 披露给其它应用。

首版面向轻量偏好、远端状态和跨设备同步，不是数据库、对象存储、秘密保险箱、日志系统或无限缓存。值对 Auth 不透明，但仍按用户相关数据保护；应用不得依赖 Auth 理解、合并、索引或查询值内容。

旧 Auth Center 仅提供需求证据：旧接口保存 string→string、按 key 读取并限制数量/总长度；不继承其把 Application ID 和 key 拼成 User 文档 Mongo 路径、依赖点分 Application ID、整图覆盖或静默清理异常字段的实现。

### 参与者与依赖检查

- **用户**：ACTIVE USER，通过 UC014–016 给当前 Application、channel 和 client 授予所需 scope；用户不提交 authId。
- **第三方应用**：PUBLIC 或 CONFIDENTIAL OAuth client，持有绑定该用户、client、Application 和 channel 的有效 opaque access token；client secret 或 applicationId 本身不能替代用户授权。
- **Auth Center**：拥有 access token/grant、Application closure tombstone、隔离 KV、revision 和清理任务；从权威 token 记录推导 authId/applicationId/channel。
- **App Center**：继续拥有 client→applicationId、channel、当前批准 Version scopes 和运行资格；不读写 Auth Mongo，也不保存第二份 KV 权威副本。Application 关闭沿用 UC-APP-027 的 durable worker，以 service JWS 调用现有 `ApplyApplicationClosure` / `GetApplicationClosureStatus`，不为存储清理增加第二种通知。

依赖 [UC014](../use-cases/UC-AUTH-014-authorize-application.md) 至 [UC019](../use-cases/UC-AUTH-019-issue-delegation-context.md) 的 OAuth grant/token/current-effective-scope 模型、[UC018](../use-cases/UC-AUTH-018-revoke-application-authorization.md) 的撤权顺序、[UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md) 的 ACTIVE/accountRevision 检查、[UC025](../use-cases/UC-AUTH-025-close-own-account.md) 的账号清理，以及 [UC026](../use-cases/UC-AUTH-026-apply-application-closure.md) 的永久 Application tombstone。

当前 HEAD 已有上述 OAuth 在线验证、Scope Catalog、Application closure gate、全局 OAuth/认证事务边界和 Mongo transaction runner，可以作为实现基础；尚无 ApplicationUserStorage Domain/Port/UseCase、API Proto、生产 scope、Gateway 路由、Mongo collection 或清理步骤。UC030 不依赖 UC005/028 的资料值，但必须保持二者的数据和 scope 边界。

### 隔离模型

```text
ApplicationUserStorageNamespace {
  authId: AuthId                  // 仅 Auth 内部保存，不对应用返回
  applicationId: ApplicationId   // 从 client 权威归属取得
  channel: TEST | GREY | STABLE  // 从 access token 取得
  revision: Int64                // 空且未创建时逻辑值为 0
  entries: Map<StorageKey, UTF8String>
  updatedAt: Instant
}
```

业务唯一键为 `(authId, applicationId, channel)`：同一 Application、同一 channel 下的 PUBLIC/CONFIDENTIAL client、major 和 Version 共享命名空间；三个 channel 彼此隔离，防止 TEST 凭据读取或覆盖 STABLE/GREY 数据。Application 级 pairwise `sub` 可供应用识别用户，但不是 Auth 的存储主键，也不能由请求提交。

实现不得自行改为跨 channel 共享或按 clientId 建立不稳定孤岛。

### 授权与 API

新增两个 audience 固定为 `iwut-auth-center` 的 OAuth RESOURCE scope：

- `storage.read`：读取调用 token 所属用户/Application/channel 的指定 key；
- `storage.write`：原子新增、替换或删除指定 key，不隐含读取其它值。

两项 scope 均进入正常版本审核、consent、grant、token、当前 Scope Catalog 和 runtime effective-scope 交集。`write` 不推导 `read`，`offline_access` 不推导任何存储权限；应用可按 UC014 把它们声明为 required 或 optional，但用户仍可按 UC018 收回。Catalog 展示文案必须明确这是“应用专属数据”的读取或写入，不能表述为读写用户资料。

由 Auth 提供 OAuth Bearer HTTP 资源端点，直接复用其 opaque token 权威读取，不公开 introspection，也不要求 Gateway 先向 Auth 签发再回送一枚委托 JWS。固定路径为：

```text
POST /v1/application-user-storage:batchGet
POST /v1/application-user-storage:mutate
DELETE /v1/users/me/application-user-storage/{application_id}
```

前两个是第三方 HTTP-only 资源端点，首版不提供第三方原生 gRPC。最后一个是用户本人 Session 入口，一次清除该 Application 的 TEST/GREY/STABLE 三个 namespace，不返回 key/value。它只线性化地删除当前数据，不替用户撤销 OAuth 授权；如果 `storage.write` 仍有效，应用可在清除提交后重新创建数据，用户界面应先撤权再清除。

资源端点的请求/响应语义为：

```text
BatchGetApplicationUserStorage {
  keys: StorageKey[1..64]
}

ApplicationUserStorageSnapshot {
  entries: StorageEntry[]       // 按 key 字典序；只含存在项
  missingKeys: StorageKey[]     // 按 key 字典序
  revision: Int64               // 未创建的空 namespace 为 0
  updatedAt: Instant?           // revision=0 时缺失
}

MutateApplicationUserStorage {
  expectedRevision: Int64       // 0 表示只接受逻辑空 namespace
  mutations: StorageMutation[1..64]
}

StorageMutation {
  key: StorageKey
  action: PUT | DELETE
  value: String?                // PUT 必填，DELETE 必须缺失
}

ApplicationUserStorageMutationResult {
  revision: Int64
  updatedAt: Instant?
  changed: Bool
}
```

读取只允许明确 key 集合，首版不提供列出全部 key、前缀扫描、全文查询、跨用户批量读取或任意 authId/applicationId/channel 参数。应用后台若要访问某用户的数据，仍须持有该用户当前有效的 access token；首版不增加 client-credentials、管理员代查或 service JWS 旁路。

PUBLIC 浏览器调用沿用 UserInfo 的当前批准 PUBLIC callback origin 动态校验、禁用 cookie credentials；CONFIDENTIAL client 不获得浏览器 CORS。所有响应使用 `Cache-Control: no-store`。

### 错误语义与运行约束

| 条件 | reason | HTTP |
| --- | --- | --- |
| 非 JSON Content-Type 或压缩请求体 | `INVALID_APPLICATION_USER_STORAGE_REQUEST` | 415 |
| 请求形状、key、UTF-8、mutation 非法 | `INVALID_APPLICATION_USER_STORAGE_REQUEST` | 400 |
| Bearer token 缺失、无效或当前主体/应用不可用 | `APPLICATION_USER_STORAGE_TOKEN_INVALID` | 401 |
| 缺少当前 read/write scope | `APPLICATION_USER_STORAGE_SCOPE_REQUIRED` | 403 |
| expectedRevision 过期 | `APPLICATION_USER_STORAGE_CONFLICT`，body 同时返回非负 `minimumRevision`；客户端须重新读取，不得把它当作可直接重试的新 expectedRevision | 409 |
| key/value/namespace/请求超过配额 | `APPLICATION_USER_STORAGE_LIMIT_EXCEEDED` | 413 |
| 入口限额 | `APPLICATION_USER_STORAGE_RATE_LIMITED` | 429 |
| 数据损坏、依赖故障或提交结果未知 | `APPLICATION_USER_STORAGE_UNAVAILABLE` | 503 |

第三方入口建议独立默认关闭；读写按 token digest、client 和 namespace 使用有界限流，不按任意请求 key 建桶。关闭入口不能跳过已有账号/Application 清理任务，也不能使已关闭 Application 的数据重新可访问。

### 验收场景

1. 同一用户/Application/channel 的 PUBLIC、CONFIDENTIAL、多 major 共享；不同用户、Application 和 channel 完全隔离。
2. 明确 keys 批量读取存在/缺失/空字符串；不支持枚举、前缀和跨用户查询。
3. first-write revision=1、真实批次只增一次、全 no-op 不增、stale CAS 和并发批次最多一个成功。
4. key/value/request/总容量边界按 UTF-8 bytes 精确处理；非法 UTF-8、重复 key、PUT/DELETE 形状和 revision 溢出拒绝。
5. read/write scope 独立；offline_access、openid、Profile scope、client secret、service/user JWS 均不能替代。
6. token/grant/family 撤销、scope 停用、Version scope 缩小、账号禁用/关闭、TEST/GREY 资格消失和 Application tombstone 立即阻断后续访问。
7. mutation 与撤权/关闭并发具备明确提交顺序；依赖/提交未知不返回成功或部分结果。
8. 用户在 App 离线或已撤权时仍可清空自己的 namespace；不得借该入口读取值或操作其它用户。
9. 首次 Apply 的 tombstone、关闭审计和唯一存储清理任务同事务；任务写入失败不返回 APPLIED，响应丢失后的 Get/重复 Apply 不产生第二任务。
10. 既有 tombstone 与残留存储在启动/恢复阶段补建并核验清理任务；物理清理可中断、重启、分批幂等恢复，APPLIED/CLOSED 不被误报成物理清理完成。
11. HTTP/Bearer、PUBLIC CORS、no-store、严格 wire/JSON、日志脱敏和真实 Mongo 并发/故障测试；第三方原生 gRPC 必须不可达。

### 已确认的首版取舍

1. namespace 固定按 `(authId, applicationId, channel)` 隔离，同 channel 的 Application clients/majors/Versions 共享。
2. scope 固定为 `storage.read` / `storage.write`，audience 为 `iwut-auth-center`，可声明 required 或 optional，两者不互相推导。
3. 配额使用 128 keys / 8 KiB value / 64 KiB namespace / 16 KiB request / 64 mutations，首版固定而非管理员配置。
4. 撤权后无期保留，重授权可恢复访问；用户清除、账号关闭或 Application 关闭才删除。
5. 用户本人清除以 Application 为单位，一次删除三个 channel，不隐式撤权。
6. Auth 直接消费 opaque Bearer token，第三方首版只提供 HTTP，不提供原生 gRPC。
7. 普通 mutation 不逐次审计；只保存 revision/updatedAt，清空与生命周期清理保存无内容元数据。

## 业务规则（UC-AUTH-030 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-001 -->
### BR-AUS-001：应用、用户与 channel 三重隔离

Auth 只从有效 access token 和 App 当前权威 client 归属得到 authId、applicationId、channel；请求不得覆盖这些字段。每次读写只能命中一个精确 namespace，不能因 pairwise sub 相同、client 同属一个 Application、grant 共享或 major 变化而跨 channel 访问。

存储记录使用独立 collection 和显式字段，不嵌入 principal/profile/user 文档，不把 applicationId/key 作为 Mongo 字段路径。Application A、channel A 的索引或损坏记录不得影响 Application B、channel B 的返回。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-002 -->
### BR-AUS-002：当前 OAuth 授权是每次访问的必要条件

读要求有效集合包含 `storage.read`，写/删 key 要求包含 `storage.write`。有效集合沿用 UC019：token scopes、当前 grant、当前批准 Version scopes 与当前 Catalog enabled 集合的交集，并复核 ACTIVE account、client/authorizationEpoch、family/token、channel 资格和 Application closure tombstone。

旧 token、被撤 scope、REVOKED grant、失效 Tester/GREY 资格、DISABLED/CLOSED 用户、关闭 Application、错误 audience 或错误 client 都失败关闭。已有 KV 不能反向证明授权，也不能因存储存在而恢复 token/grant。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-003 -->
### BR-AUS-003：有界字符串 KV 与精确容量

StorageKey 为 1..64 ASCII 字符，匹配 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，区分大小写并按原字节排序。值为合法 UTF-8 string，允许空字符串，不执行 JSON 解析、Unicode 规范化、压缩或二进制猜测；应用需要 JSON/二进制时自行编码在字符串内。

每 namespace 最多 128 个 key、单值最多 8 KiB、全部 key/value UTF-8 bytes 合计最多 64 KiB；单次读取/变更最多 64 个唯一 key，请求最大 16 KiB。PUT 和 DELETE 后都按最终完整 namespace 重新检查配额，不能靠并发或编码差异越界。这些数值是固定首版契约，不由运维动态调整。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-004 -->
### BR-AUS-004：整命名空间 revision 与原子批量变更

未创建 namespace 的逻辑 revision 为 0；第一次真实 PUT 以 expectedRevision=0 创建 revision=1。此后每个产生内容变化的成功批次只递增一次正数 revision，并原子应用全部 mutation。stale revision 全部拒绝并返回当前最小 revision 元数据，不部分写入。

同一请求不得重复 key。PUT 已有相同值、DELETE 不存在 key，以及全部 mutation 均无变化时返回 `changed=false` 和原 revision，不创建空记录、不更新 updatedAt。事务重试复用稳定操作 ID；提交结果未知返回不可用，客户端先读当前 revision/值再决定是否重试，不能盲目增加 expectedRevision。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-005 -->
### BR-AUS-005：撤权立即阻断访问，数据删除单独表达

部分或全部撤销 grant、scope 停用、token/family 撤销提交后，不再允许新的存储读写；和 mutation 并发时共享 OAuth 最终确认边界，不能出现撤权后提交成功的写入。撤权本身不应被伪装成某个应用 DELETE，也不能在授权事务内同步扫描大批存储。

撤权不自动删除数据，也没有定时保留期；重新授权恢复对旧数据的访问。只有用户明确清除、账号关闭或 Application 关闭才删除。本人 Session 入口使用户即使已经撤权或 App 离线，仍可清空该 Application 的全部 channel；应用凭 `storage.write` 只能删除 key，不能伪造“用户要求删除全部数据”。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-006 -->
### BR-AUS-006：账号关闭与 Application 关闭的清理闭合

UC025 账号关闭后立即由 CLOSED/token gate 阻断访问，并由账号清理任务按 authId 有界删除全部 ApplicationUserStorage；清理完成回执必须包含本 collection。新 authId 不继承旧 namespace。

Application 关闭只复用 UC026 已有 App→Auth 协议。App Center 在本地提交不可逆 `CLOSING` 和 durable task 后，由 worker 使用稳定的 applicationId、closureId、closingStartedAt 调用 `ApplyApplicationClosure`；响应丢失时使用 `GetApplicationClosureStatus` 和相同 Apply 收敛。Auth 不轮询 App、不从 provider 错误推断关闭，也不增加 `DeleteApplicationUserStorage` 一类第二通知。

Auth 首次接受 Apply 时，必须在建立永久 applicationId tombstone 和关闭审计的**同一事务**中，幂等创建唯一的 ApplicationUserStorage 清理任务。只有 tombstone、审计与清理任务都持久提交后，才可返回 APPLIED receipt；清理任务写入失败、事务结果未知或三者绑定不一致时返回不可用，不得先确认关闭再依赖内存补任务。App 保持 CLOSING 并按既有协议重试。

tombstone 提交后立即阻断该 applicationId 的全部 namespace 访问；APPLIED/CLOSED 表示永久访问栅栏和清理任务已经可靠建立，不表示所有 KV 已同步物理删除。Auth 后台按 applicationId 对全部用户/channel 数据有界分批删除，保存游标/进度，失败、进程重启和重复执行均可恢复；任务完成不能删除 tombstone，也不需要回调 App 改写 CLOSED。

同一 applicationId/closureId 的重复 Apply 只能复用一份任务；绑定不一致按 UC026 冲突处理。UC030 上线或恢复时还必须扫描既有 tombstone：若仍存在该 applicationId 的存储却没有匹配清理任务，先幂等补建并核验任务后才能接收存储流量，不能把旧 tombstone 当作无需清理。普通 client/Version/Publication 变更不改变 namespace 归属；若未来允许 Application 转让或恢复归档，仍不得越过永久 tombstone。

<!-- 权威位置: use-cases/UC-AUTH-030-manage-application-user-storage.md#br-aus-007 -->
### BR-AUS-007：不透明数据、最小观测与失败关闭

值、key、Bearer token 和完整 mutation 不进入访问日志、trace、metrics 标签或通用业务审计。响应 `no-store`；错误不泄露其它用户/Application/channel 是否存在数据。持久记录可以保存创建/更新时间和 revision，用户清空、账号清理及 Application 清理保存不含 key/value 的最小事件或进度。

数据损坏、配额无法重算、App 当前资格/目录读取失败、Mongo/事务结果未知均使整次请求失败，不返回部分读取或假空 namespace。普通应用 mutation 不另建逐次审计事件，只在存储记录中保存 revision/updatedAt；用户清空和生命周期清理保存不含 key/value 的最小审计或进度。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

2026-10-12 下表仅已交付基线。密码管理/恢复、默认密码登录已展开 UC033/034 DRAFT 和 auth-password-v1 草案，未注册真实入口；旧 REGISTER/BIND/凭据撤销、注销 Prepare/app.close Complete 须同步密码与防旁路门禁，新修订未实施，不提前启用或登记虚构公网清单。

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
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
| GET | `/v1/academic-year-policy/schedule` | AcademicYearPolicyService/GetAcademicYearSchedule | SESSION | 200 |
| PUT | `/v1/academic-year-policy/schedule/next-rollover` | AcademicYearPolicyService/UpdateNextAcademicYearRollover | SESSION | 200 |
| DELETE | `/v1/users/me/application-user-storage/{application_id}` | ApplicationUserStorageService/ClearOwnApplicationUserStorage | SESSION | 200 |

原 `/v1/registrations` 和 completion 路径不注册，旧 BeginUserRegistration/CompleteUserRegistration RPC 返回 UNIMPLEMENTED；不重定向、不代为发起注册，也不因启用用户入口恢复旧方法。

UC011 是唯一注册入口，三个 DIRECT 路由的字段及 Session 例外见[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)：

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

AcademicYearPolicyService package 为 `auth_center.v1.academic_year_policy`，两个方法由 Auth 在线复核当前完整平台管理员资格；精确时间、递推、并发和审计语义唯一见 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md)。管理入口由独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED` 控制且默认关闭；关闭管理入口不影响 Auth 内部消费已 provision 的时间表。

ApplicationUserStorageService package 为 `auth_center.v1.application_user_storage`。本人清除使用 SESSION 身份，`application_id` 仅由路径绑定，一次删除该用户与 Application 的 TEST/GREY/STABLE 数据，不返回应用 key/value。第三方读写另使用 `POST /v1/application-user-storage:batchGet` 与 `POST /v1/application-user-storage:mutate`；两者是 Auth 直接验证 opaque OAuth Bearer token 的 HTTP-only 资源端点，不经 SESSION 转换、不生成原生 gRPC 第三方方法。三个入口均由 `AUTH_APPLICATION_USER_STORAGE_ENABLED` 控制且默认关闭，精确语义见 [UC030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。学年时间表 PUT 只接受 nextRolloverAt、expectedRevision 和 reason，不接受客户端提交 currentAcademicYear。
- 设备登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 和应用存储清除的 `application_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB，应用用户存储固定 16 KiB。
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

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖修订后的资料/认证方法及退役无邮箱路径拒绝、Reviewer/应用运维权限方法、两个学年时间表管理方法及应用用户存储 HTTP/本人清除方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/oauth-oidc-v1.md`：OAuth 与 OIDC 接入协议 v1

#### 范围与职责

提供 Authorization Code Flow，用 OIDC ID Token 表达应用登录结果，用独立的 opaque access token 表达委托访问。Auth 拥有登录、consent、grant 和 token；App 拥有 client 身份/secret，以及 ApplicationVersion 中受审核的 redirect URI 和 scopes；Traefik/Gateway 执行入口鉴权，资源服务执行业务授权。

相关业务规则由 [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) 至 [019](../use-cases/UC-AUTH-019-issue-delegation-context.md)、[UC-AUTH-028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md)、[UC-AUTH-030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)、[UC-APP-018](../../app-center/use-cases/UC-APP-018-manage-oauth-client.md) 至 [021](../../app-center/use-cases/UC-APP-021-manage-grey-rollout.md) 拥有。跨服务 App 接口见 [App OAuth Client v1](../../platform/contracts/app-oauth-client-v1.md)，入口和下游身份见 [OAuth 委托上下文 v1](../../platform/contracts/oauth-delegation-v1.md)。

#### 公网端点与响应

部署固定 HTTPS issuer，例如 `https://auth.example.org/auth-center/oidc`。issuer、端点和签发内容都来自受信配置，不能从请求 Host/Forwarded 推导。

| 相对 issuer 的路径 | 方法 | 入口策略与用途 |
| --- | --- | --- |
| `/.well-known/openid-configuration` | GET | DIRECT；discovery |
| `/jwks` | GET | DIRECT；仅 OIDC 公钥 |
| `/authorize` | GET、POST | DIRECT；Auth 自行校验参数及官方登录门户会话 |
| `/token` | POST | DIRECT；Auth 自行校验 client/code/verifier 或 refresh token |
| `/userinfo` | GET、POST | DIRECT；Auth 自行在线校验 access token，不使用 Session |
| `/revoke` | POST | DIRECT；Auth 自行校验 client 与待撤销 token |

上述 DIRECT 不等于无鉴权，只是不经过 Session→用户 JWS 的转换。标准端点属于 `OIDC_HTTP`，显式加入 Gateway 路由 schema；不能假造 HTTP annotation 或套用 Kratos ProtoJSON envelope。POST authorize/token/revoke 使用 `application/x-www-form-urlencoded`；UserInfo 的 token 仅接受 `Authorization: Bearer …`。不支持 query/body 传 access token。Discovery/JWKS 可公开缓存，其余响应 `Cache-Control: no-store`、`Pragma: no-cache`。

成功兑换示例（示例值不是可用凭据）：

```json
{
  "token_type": "Bearer",
  "access_token": "<opaque random token>",
  "expires_in": 900,
  "id_token": "<signed JWT, different from access_token>",
  "scope": "openid email"
}
```

只有按 UC-AUTH-016 获得离线授权时才增加 `refresh_token`。刷新响应保留 access_token/token_type/expires_in/scope/refresh_token，首版不重新签发 ID Token。

Discovery 必须准确声明 issuer、authorization_endpoint、token_endpoint、userinfo_endpoint、jwks_uri、revocation_endpoint；`response_types_supported=[code]`、`grant_types_supported=[authorization_code,refresh_token]`、`subject_types_supported=[pairwise]`、`id_token_signing_alg_values_supported=[RS256]`、`token_endpoint_auth_methods_supported=[none,client_secret_basic]`、`code_challenge_methods_supported=[S256]`。`response_modes_supported=[query]`、`authorization_response_iss_parameter_supported=true`；revocation 同样支持 none/basic。scopes_supported 仅列出实际装载、enabled=true 且已实现的 scope；不宣称动态注册、logout、introspection 或 JWT access token profile 已实现。

UC030 的 `POST /v1/application-user-storage:batchGet` 和 `POST /v1/application-user-storage:mutate` 不是 issuer-relative OIDC 端点，也不写入 Discovery。它们是 Auth Center 资源端点，只接受 `Authorization: Bearer <opaque access token>`，要求当前 `iwut-auth-center` audience 与独立 `storage.read` / `storage.write` scope；不接受 Session、service/user JWS、client secret、query 或 body token 替代。

#### Scope 启用与兼容投影

Scope 单一启用状态与 requestable 投影唯一由 [UC-AUTH-001 / BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 定义；OAuth 当前目录许可集合 C 及授权/恢复边界见 [UC-AUTH-014 / BR-OAU-001、002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-001)。本协议不增加 requestable 与 runtimeEnabled 两个独立开关。

App 继续使用已有 requestable 字段进行版本管理检查；Auth 的 authorize、code 兑换、refresh、UserInfo 和委托签发分别遵循 UC014–019 的当前目录检查。停用不会调用用户撤销用例或抹掉历史同意。目录故障使用依赖错误，Discovery 缓存或 App 旧快照不改变运行判断。

`kind=USERINFO_PROFILE` 是 Auth 内部 Scope Catalog 元数据，不扩展跨服务 `ScopeDefinition` 线格式。其名称固定为 `profile.<fieldKey>`，audience 为空，并按 UC028 一对一映射 UC005 字段；App 仍只看到 name/requestable。该类 scope 与 PROTOCOL/RESOURCE 一起进入实际 enabled 集合，但只用于 UserInfo，不产生 Gateway 资源 audience 或委托路由。

`storage.read` 与 `storage.write` 是 audience 固定为 `iwut-auth-center` 的 RESOURCE scope，可由 Application Version 声明为 required 或 optional。两者互不推导，也不由 `openid`、`offline_access` 或 Profile scope 推导；每次存储请求均重新计算 token、grant、当前 Version scopes 与 enabled Catalog 的交集。

UC031 扩展内部 kind=USERINFO_CAMPUS：只允许 campus.whut，audience/profileField/ProfileValueType 为空。它进入当前 enabled scope 集合、App 声明审核与 consent，UserInfo audience 覆盖它，不产生资源 audience。UserInfo 有有效 scope 且认证存在时输出 iwut_campus={institution:"WHUT",certified:true}，未认证省略；不披露邮箱/认证时间/标识，不进入 ID Token。Discovery claims_supported 增加 iwut_campus，scope 列表仅实际 enabled；授权、故障与注销规则唯一见 UC031。

#### 凭据与身份格式

授权码、access token、refresh token 分别由 CSPRNG 产生 32 字节，base64url 无 padding；用途隔离的 SHA-256 摘要建索引，原值只在成功响应中出现。Session、三类 OAuth 凭据即使形状相同也只能查各自的存储，禁止自动回退。数据库 TTL 清理不代替 expiresAt 检查。

| 对象 | 首版有效期 | 消费方 |
| --- | --- | --- |
| 授权交互 | 10 分钟 | 官方门户 |
| 授权码 | 90 秒，一次性 | token endpoint |
| access token | 15 分钟，仍逐次在线查授权 | UserInfo / Gateway |
| ID Token | 5 分钟 | 该 client 的登录处理 |
| refresh family | 30 天未成功刷新失效；自首次签发起最长 180 天 | token endpoint；滑动闲置期限＋固定绝对上限 |

上述天数按 24 小时计算。refresh 的滑动更新、到期边界和 access token 剩余寿命截断规则唯一由 [UC-AUTH-016 / BR-OAU-010](../use-cases/UC-AUTH-016-refresh-application-tokens.md#br-oau-010) 定义；轮换改变 token 值，续期只移动闲置截止时间，不重置整条链的绝对上限。

ID Token 使用独立 OIDC RSA 签名密钥与 JWKS（RS256，RSA 至少 2048 bit）。header 为 `alg=RS256,typ=JWT,kid=<configured key>`；claims 为 iss、sub、单值 aud=client_id、iat、exp、auth_time、nonce、at_hash。at_hash 按 OIDC RS256 的 SHA-256 左半摘要规则，从实际 access token 计算。不包含平台 Session、内部 authId、学生关联值、developer/reviewer 权限或全量资料。

client 必须用预先信任 issuer 的 discovery/JWKS 验签，检查算法、iss、aud、exp、nonce、at_hash；ID Token 的时钟容差最多 30 秒，max_age 请求还须检查 auth_time；未知 kid 只允许对固定 JWKS 地址进行有界刷新，不访问 JWT 提供的 URL。ID Token 不作为 API Bearer token；取得后 client 可自行建立应用会话，其寿命由应用管理。OIDC 签名密钥退役前保留公钥至少覆盖已签 token 的有效期、容许时钟差和 JWKS 缓存期限。

pairwise sub 的业务所有权和持久化由 [BR-OAU-021](../use-cases/UC-AUTH-015-exchange-authorization-code.md#br-oau-021) 定义：一个 Application 一个稳定 sector，所有 channel/type/major/Version 共用。Auth 从 App 验证 clientId→applicationId 后创建映射；App 不保存 sector/sub，用户和开发者不能自选其他应用的 sector。同一 sector 下 PUBLIC/CONFIDENTIAL 的 sub 相同，但 ID Token 的 aud 仍分别为各自 clientId，不能跨 client 使用 ID Token 登录。

UserInfo 的资料扩展使用固定顶层自定义 claim `iwut_profile`，其值是完整 field key 到已定义 JSON 值的 object；每次只包含当前有效 `profile.<fieldKey>` scope 对应且用户当前已填写的字段。STRING/DATE 为 string、INTEGER 为 number、BOOLEAN 为 boolean、STRING_SET 为规范排序的 string array；ACADEMIC_GRADE 输出按服务端当前学年推算、在所属阶段最后学年封顶的 `<STAGE>_<YEAR>` string，不披露锚点或确认时间。没有值时省略该 key，全部为空时省略 `iwut_profile`。该 claim 不进入 ID Token，不包含 revision/updatedAt，也不能覆盖 sub/email/email_verified。精确授权、生产字段、推算、故障与生命周期规则见 [UC-AUTH-028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md) 与 [UC-AUTH-005 / BR-UPF-017–018](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017)。Discovery 的 `claims_supported` 在交付后增加 `iwut_profile`，`scopes_supported` 只列实际 enabled 的资料 scope。

UserInfo 的 `email/email_verified` 只投影 UC011 当前唯一已验证登录邮箱，不披露列表或其他学校地址。校园扩展 `campus.whut` 输出最小 `iwut_campus` 对象 `{"institution":"WHUT","certified":true}`，只在当前授权与学校绑定依据有效时提供，删除最后依据后的新读取省略；不进入 ID Token、不带校园邮箱/认证时间/内部 ID。规则引用 UC017 与修订 UC031；旧独立永久事实披露已经交付，新绑定/撤回消费尚未实施，不能把历史 token 中的事实当作永久当前资格。

#### 错误、CORS 与限额

协议端点返回 OAuth/OIDC JSON error，不包装业务 envelope。无效 client 统一 invalid_client（Basic 失败 HTTP 401 并带 WWW-Authenticate）；失效 code/verifier/refresh 统一 invalid_grant（400）；非法参数 invalid_request，越界 scope invalid_scope。不要向攻击者区分 secret、用户、grant 是否存在。依赖故障返回 503 与 temporarily_unavailable，不当成用户拒绝或已撤销。

UserInfo 无效 token 返回 401 Bearer invalid_token；scope 不够返回 403 insufficient_scope。API 不返回登录 302。revocation 已失效/未知/不属于调用 client 的 token 统一 200；不支持的 token 类型用 unsupported_token_type。

PUBLIC token/UserInfo/revoke 的浏览器 CORS 只允许当前批准并发布 Version 中 PUBLIC_PKCE effective callbacks 对应的 HTTPS origin（无 cookie credentials），缺 Origin 的原生调用仍按协议认证；preflight 无 token 时仅根据当前 effective public origins 联集返回允许的方法/headers，实际请求仍按认证后的 client 再匹配 Origin；验证 preflight 不授予访问权限。CONFIDENTIAL token/revoke 不启用跨域浏览器访问。授权端点仅允许顶层导航，不提供跨域 fetch 登录。

请求体最大 16 KiB、scope 最多 32 项、单项最多 128 ASCII 字符；单值参数重复、未知 grant/response_type 均拒绝。默认每 IP 120 次/分钟、每 client 300 次/分钟、每登录用户 30 次授权确认/分钟，可部署调小；429 携 Retry-After。code、token、secret、verifier、cookie、签名上下文、邮件及用户资料不得进入访问日志、trace、metrics 标签或审计原文。

ApplicationUserStorage 对 PUBLIC client 复用同一当前 callback HTTPS origin 校验，无 cookie credentials；CONFIDENTIAL client 不开放浏览器 CORS。无效 token 返回 401 Bearer invalid_token，缺 scope 返回 403 insufficient_scope；stale CAS 返回 409 和非负 `minimumRevision` 下界，调用方仍须重新读取，不能把该值直接当作下一次 expectedRevision。响应固定 `Cache-Control: no-store`，请求固定最大 16 KiB，限额不以任意存储 key 作为无界维度。

#### 交付依赖与验收

1. App 先扩展 UC-APP-002/003/004/005 的 Version 依附 oauthRedirects 创建、编辑、审核与策略，再由 UC-APP-018 提供 Application＋channel 级稳定 identity/credential，UC-APP-007/019 负责发布检查与运行资格快照。
2. Auth 实现 UC-AUTH-014/015/017/018/019，门户与 Gateway 同步交付；UC-AUTH-016 是独立离线授权工作包，未启用时 discovery 必须去掉 refresh_token，拒绝 offline_access，不能部分宣称支持。
3. 初版最小协议 scope 装载 `openid`、`email`、`offline_access`：Auth 维护稳定语义/用户可读说明/映射；App 版本仍须声明并通过原有审核。资源 scope 必须有已交付资源服务、scope→audience→route 映射；USERINFO_PROFILE scope 必须有 UC028 已验证的一字段一 scope 映射、BR-UPF-017 真实资料字段定义，当前年级还必须有 UC029 权威时间表。不接受开发 fixture。生产 Catalog 装载能力是实现依赖，不需要先做在线 Catalog 管理 UC。
4. Gateway OAUTH2、OIDC_HTTP 与资源服务委托验证通过真实三方联合测试后显式启用。当前 ACTIVE 契约继续有效，本文不使旧实现自动具备新能力。

验收至少覆盖两种 client、confidential+PKCE、code/refresh 重放、nonce/state 错配、同一 clientId 的 Version/hostname/major 回调切换与未登记回调、登录前后 runtime tuple 变化、scope 越权、跨 major 历史授权保留、渠道授权隔离、仅新增 scope 重新 consent、同应用所有渠道/type 的 sub 一致及不同应用隔离、secret 轮换不撤销 grant/既有 token、App 停用、UserInfo 最小披露、HTTP/原生 gRPC/gRPC-Web，以及依赖故障时不转发。启用前还需实际 OIDC 客户端库互通测试；未通过认证不得宣称通过 OpenID Certification。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-030`（use-cases/UC-AUTH-030-manage-application-user-storage.md）：变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/oauth-oidc-v1.md`（docs 根级共享文档）：客户端配置、授权请求与登录门户、标准 sector 注册与回调清单、标准依据

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-030-manage-application-user-storage.md` | 197 | `44f02f431092` |
| `platform/contracts/auth-center-api-routing.md` | 142 | `c300b311eaac` |
| `platform/contracts/oauth-oidc-v1.md` | 148 | `9fec6b0f0311` |
