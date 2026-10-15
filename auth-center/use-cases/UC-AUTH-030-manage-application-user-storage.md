# UC-AUTH-030：读写应用用户存储

状态：`ACCEPTED`

## 目标与范围

第三方应用使用用户授予的 OAuth access token，在 Auth Center 中为该用户读写一小块由应用解释的隔离字符串 KV。存储逻辑上属于“某个应用在某个用户下的数据”，不是用户资料、平台权限、OIDC claim 或学校验证事实；应用写入不能改变 UC005 UserProfile，也不能经 UC028 UserInfo 披露给其它应用。

首版面向轻量偏好、远端状态和跨设备同步，不是数据库、对象存储、秘密保险箱、日志系统或无限缓存。值对 Auth 不透明，但仍按用户相关数据保护；应用不得依赖 Auth 理解、合并、索引或查询值内容。

旧 Auth Center 仅提供需求证据：旧接口保存 string→string、按 key 读取并限制数量/总长度；不继承其把 Application ID 和 key 拼成 User 文档 Mongo 路径、依赖点分 Application ID、整图覆盖或静默清理异常字段的实现。

## 参与者与依赖检查

- **用户**：ACTIVE USER，通过 UC014–016 给当前 Application、channel 和 client 授予所需 scope；用户不提交 authId。
- **第三方应用**：PUBLIC 或 CONFIDENTIAL OAuth client，持有绑定该用户、client、Application 和 channel 的有效 opaque access token；client secret 或 applicationId 本身不能替代用户授权。
- **Auth Center**：拥有 access token/grant、Application closure tombstone、隔离 KV、revision 和清理任务；从权威 token 记录推导 authId/applicationId/channel。
- **App Center**：继续拥有 client→applicationId、channel、当前批准 Version scopes 和运行资格；不读写 Auth Mongo，也不保存第二份 KV 权威副本。Application 关闭沿用 UC-APP-027 的 durable worker，以 service JWS 调用现有 `ApplyApplicationClosure` / `GetApplicationClosureStatus`，不为存储清理增加第二种通知。

依赖 [UC014](UC-AUTH-014-authorize-application.md) 至 [UC019](UC-AUTH-019-issue-delegation-context.md) 的 OAuth grant/token/current-effective-scope 模型、[UC018](UC-AUTH-018-revoke-application-authorization.md) 的撤权顺序、[UC022](UC-AUTH-022-disable-and-restore-user-account.md) 的 ACTIVE/accountRevision 检查、[UC025](UC-AUTH-025-close-own-account.md) 的账号清理，以及 [UC026](UC-AUTH-026-apply-application-closure.md) 的永久 Application tombstone。

当前 HEAD 已有上述 OAuth 在线验证、Scope Catalog、Application closure gate、全局 OAuth/认证事务边界和 Mongo transaction runner，可以作为实现基础；尚无 ApplicationUserStorage Domain/Port/UseCase、API Proto、生产 scope、Gateway 路由、Mongo collection 或清理步骤。UC030 不依赖 UC005/028 的资料值，但必须保持二者的数据和 scope 边界。

## 隔离模型

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

## 授权与 API

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

## 业务规则

<a id="br-aus-001"></a>
### BR-AUS-001：应用、用户与 channel 三重隔离

Auth 只从有效 access token 和 App 当前权威 client 归属得到 authId、applicationId、channel；请求不得覆盖这些字段。每次读写只能命中一个精确 namespace，不能因 pairwise sub 相同、client 同属一个 Application、grant 共享或 major 变化而跨 channel 访问。

存储记录使用独立 collection 和显式字段，不嵌入 principal/profile/user 文档，不把 applicationId/key 作为 Mongo 字段路径。Application A、channel A 的索引或损坏记录不得影响 Application B、channel B 的返回。

<a id="br-aus-002"></a>
### BR-AUS-002：当前 OAuth 授权是每次访问的必要条件

读要求有效集合包含 `storage.read`，写/删 key 要求包含 `storage.write`。有效集合沿用 UC019：token scopes、当前 grant、当前批准 Version scopes 与当前 Catalog enabled 集合的交集，并复核 ACTIVE account、client/authorizationEpoch、family/token、channel 资格和 Application closure tombstone。

旧 token、被撤 scope、REVOKED grant、失效 Tester/GREY 资格、DISABLED/CLOSED 用户、关闭 Application、错误 audience 或错误 client 都失败关闭。已有 KV 不能反向证明授权，也不能因存储存在而恢复 token/grant。

<a id="br-aus-003"></a>
### BR-AUS-003：有界字符串 KV 与精确容量

StorageKey 为 1..64 ASCII 字符，匹配 `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`，区分大小写并按原字节排序。值为合法 UTF-8 string，允许空字符串，不执行 JSON 解析、Unicode 规范化、压缩或二进制猜测；应用需要 JSON/二进制时自行编码在字符串内。

每 namespace 最多 128 个 key、单值最多 8 KiB、全部 key/value UTF-8 bytes 合计最多 64 KiB；单次读取/变更最多 64 个唯一 key，请求最大 16 KiB。PUT 和 DELETE 后都按最终完整 namespace 重新检查配额，不能靠并发或编码差异越界。这些数值是固定首版契约，不由运维动态调整。

<a id="br-aus-004"></a>
### BR-AUS-004：整命名空间 revision 与原子批量变更

未创建 namespace 的逻辑 revision 为 0；第一次真实 PUT 以 expectedRevision=0 创建 revision=1。此后每个产生内容变化的成功批次只递增一次正数 revision，并原子应用全部 mutation。stale revision 全部拒绝并返回当前最小 revision 元数据，不部分写入。

同一请求不得重复 key。PUT 已有相同值、DELETE 不存在 key，以及全部 mutation 均无变化时返回 `changed=false` 和原 revision，不创建空记录、不更新 updatedAt。事务重试复用稳定操作 ID；提交结果未知返回不可用，客户端先读当前 revision/值再决定是否重试，不能盲目增加 expectedRevision。

<a id="br-aus-005"></a>
### BR-AUS-005：撤权立即阻断访问，数据删除单独表达

部分或全部撤销 grant、scope 停用、token/family 撤销提交后，不再允许新的存储读写；和 mutation 并发时共享 OAuth 最终确认边界，不能出现撤权后提交成功的写入。撤权本身不应被伪装成某个应用 DELETE，也不能在授权事务内同步扫描大批存储。

撤权不自动删除数据，也没有定时保留期；重新授权恢复对旧数据的访问。只有用户明确清除、账号关闭或 Application 关闭才删除。本人 Session 入口使用户即使已经撤权或 App 离线，仍可清空该 Application 的全部 channel；应用凭 `storage.write` 只能删除 key，不能伪造“用户要求删除全部数据”。

<a id="br-aus-006"></a>
### BR-AUS-006：账号关闭与 Application 关闭的清理闭合

UC025 账号关闭后立即由 CLOSED/token gate 阻断访问，并由账号清理任务按 authId 有界删除全部 ApplicationUserStorage；清理完成回执必须包含本 collection。新 authId 不继承旧 namespace。

Application 关闭只复用 UC026 已有 App→Auth 协议。App Center 在本地提交不可逆 `CLOSING` 和 durable task 后，由 worker 使用稳定的 applicationId、closureId、closingStartedAt 调用 `ApplyApplicationClosure`；响应丢失时使用 `GetApplicationClosureStatus` 和相同 Apply 收敛。Auth 不轮询 App、不从 provider 错误推断关闭，也不增加 `DeleteApplicationUserStorage` 一类第二通知。

Auth 首次接受 Apply 时，必须在建立永久 applicationId tombstone 和关闭审计的**同一事务**中，幂等创建唯一的 ApplicationUserStorage 清理任务。只有 tombstone、审计与清理任务都持久提交后，才可返回 APPLIED receipt；清理任务写入失败、事务结果未知或三者绑定不一致时返回不可用，不得先确认关闭再依赖内存补任务。App 保持 CLOSING 并按既有协议重试。

tombstone 提交后立即阻断该 applicationId 的全部 namespace 访问；APPLIED/CLOSED 表示永久访问栅栏和清理任务已经可靠建立，不表示所有 KV 已同步物理删除。Auth 后台按 applicationId 对全部用户/channel 数据有界分批删除，保存游标/进度，失败、进程重启和重复执行均可恢复；任务完成不能删除 tombstone，也不需要回调 App 改写 CLOSED。

同一 applicationId/closureId 的重复 Apply 只能复用一份任务；绑定不一致按 UC026 冲突处理。UC030 上线或恢复时还必须扫描既有 tombstone：若仍存在该 applicationId 的存储却没有匹配清理任务，先幂等补建并核验任务后才能接收存储流量，不能把旧 tombstone 当作无需清理。普通 client/Version/Publication 变更不改变 namespace 归属；若未来允许 Application 转让或恢复归档，仍不得越过永久 tombstone。

<a id="br-aus-007"></a>
### BR-AUS-007：不透明数据、最小观测与失败关闭

值、key、Bearer token 和完整 mutation 不进入访问日志、trace、metrics 标签或通用业务审计。响应 `no-store`；错误不泄露其它用户/Application/channel 是否存在数据。持久记录可以保存创建/更新时间和 revision，用户清空、账号清理及 Application 清理保存不含 key/value 的最小事件或进度。

数据损坏、配额无法重算、App 当前资格/目录读取失败、Mongo/事务结果未知均使整次请求失败，不返回部分读取或假空 namespace。普通应用 mutation 不另建逐次审计事件，只在存储记录中保存 revision/updatedAt；用户清空和生命周期清理保存不含 key/value 的最小审计或进度。

## 错误语义与运行约束

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

## 验收场景

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

## 已确认的首版取舍

1. namespace 固定按 `(authId, applicationId, channel)` 隔离，同 channel 的 Application clients/majors/Versions 共享。
2. scope 固定为 `storage.read` / `storage.write`，audience 为 `iwut-auth-center`，可声明 required 或 optional，两者不互相推导。
3. 配额使用 128 keys / 8 KiB value / 64 KiB namespace / 16 KiB request / 64 mutations，首版固定而非管理员配置。
4. 撤权后无期保留，重授权可恢复访问；用户清除、账号关闭或 Application 关闭才删除。
5. 用户本人清除以 Application 为单位，一次删除三个 channel，不隐式撤权。
6. Auth 直接消费 opaque Bearer token，第三方首版只提供 HTTP，不提供原生 gRPC。
7. 普通 mutation 不逐次审计；只保存 revision/updatedAt，清空与生命周期清理保存无内容元数据。

## 变更记录

- 2026-10-10：建立待审核草案；依据当前 OAuth/lifecycle 设计和旧系统需求证据，提出 channel 隔离的有界字符串 KV、独立 read/write scope、CAS 批量变更与账号/Application 清理边界。未接受、未生成 brief、未开始实现。
- 2026-10-10：确认 Application 关闭复用 UC026 的 App→Auth Apply/Get 协议，不增加第二通知；Auth 在 tombstone/审计同一事务中建立唯一清理任务后才返回 APPLIED，物理删除异步收敛，并为既有 tombstone 提供启动/恢复补建检查。
- 2026-10-10：用户审核通过；固定 namespace、scope/audience、配额、撤权后保留、本人清除、HTTP-only 第三方入口与最小审计取舍，状态改为 ACCEPTED 并进入实现。
- 2026-10-10：完成 Auth/API 后端实现与真实 Mongo 验收；实现覆盖单独在 `implements/README.md` 跟踪，设计状态仍为 ACCEPTED。
