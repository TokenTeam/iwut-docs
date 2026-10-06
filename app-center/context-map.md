# App Center Context Map

状态：`PROPOSED`

## 当前边界

```text
Identity Context
  ├─ 提供可信 authId + developerStatus
  ├─ 提供可信 reviewer permissions
  ├─ 提供可信 Application 运维 permissions
  ├─ 拥有 Auth Scope Catalog
  ├─ 签发绑定用途的近期重新认证证明
  └─ 拥有 Application 授权关闭 tombstone
          │
          ▼
App Center Context
  ├─ 拥有并创建 Application
  ├─ 拥有当前管理员、管理权 revision 与转让生命周期
  ├─ 拥有 Application 生命周期与不可逆关闭过程
  ├─ 拥有 Application 平台可用状态与暂停/恢复审计
  ├─ 拥有 ApplicationProfile、ApplicationProfileRevision 及其资料生命周期
  ├─ 拥有独立 ApplicationProfileReview 与提交快照
  ├─ 拥有 ApplicationVersion 及其审核生命周期
  ├─ 拥有 ApplicationReview 与提交快照
  ├─ 拥有 Application 级 OAuth registration、稳定 client identity 与独立 credential
  ├─ 拥有按 RPC major 分区的 ApplicationPublication
  ├─ 拥有 ApplicationPublicationHistory
  ├─ 拥有 Application 级 Tester 加入链接
  ├─ 拥有 Application Tester Membership 与容量事实
  ├─ 依据 Membership、Publication、Version 解析 Test/Grey/Stable 统一启动目标
  └─ 拥有 Application Creation Quota
```

## App Center 当前拥有的事实

- 哪个 Application ID 已经存在。
- Application 的 name 和 createdAt。
- Application 的 `ACTIVE/CLOSING/CLOSED` 生命周期、与其正交的 `AVAILABLE/SUSPENDED` 平台可用状态，以及各自 revision。
- ApplicationProfileRevision 的身份、应用内 sequence、displayName、可空 description、可空不透明 icon、DRAFT/SUBMITTED/APPROVED/REJECTED 状态、revision，以及创建和最近修改审计；资料草稿采用完整替换和乐观并发。
- 每次 ProfileReview attempt 的身份、不可变 displayName/description/icon 快照、sourceRevision、一次性 decision、状态，以及提交和决定审计。
- ApplicationProfile 当前工作修订与公开资料指针，以及 App Center 自己的版本化 ProfileReviewPolicy。
- 哪个 authId 是 Application 当前 adminId，以及用于管理权 OCC 的 ownershipRevision。
- 每次管理权转让的源、目标、PENDING/终态与审计；App Center 不把通知消息当作事实来源。
- Application 的 ACTIVE/CLOSING/CLOSED、lifecycleRevision、关闭过程、Auth 回执与本地持久重试事实。
- 同一 adminId 下哪些名称已经被占用。
- adminId 当前的应用创建配额和已使用数量。
- ApplicationVersion 的身份、应用内 sequence、入口 URL、RPC 兼容声明、scopes、依附 Version 的 pkce/confidential OAuth redirect URIs、审核状态、revision，以及创建和最近修改审计。
- 每次审核 attempt 的身份、不可变提交快照、一次性决定、状态，以及提交/决定/草稿恢复审计。
- App Center 自己的版本化审核策略和检查项。
- 每个 `(applicationId, rpcApiMajor)` 当前 test 发布指针、Publication revision 和修改审计。
- 每次真实槽位变化的追加式 PublicationHistory。
- 每个 Application 当前有效的 Tester 加入链接、secret 哈希，以及 `ROTATED/MANUAL/ADMIN_TRANSFER/APPLICATION_CLOSURE` 撤销审计。
- 哪些 authId 当前是某个 Application 的 Tester、历史 Membership episode，以及固定 100 人上限下的 ACTIVE Tester 数量。
- 对给定 Tester、hostRpcApiMajor 和 hostCapabilities，哪个 test ApplicationVersion 构成当前 TestLaunchDescriptor。
- 对给定 Application、可选可信用户身份、hostRpcApiMajor 和 hostCapabilities，哪个 Test、Grey 或 Stable ApplicationVersion 构成唯一 LaunchTargetDescriptor；该统一查询由 UC-APP-023 定义。
- ApplicationOAuthRegistration 的稳定 PUBLIC/CONFIDENTIAL clientId 与状态、OAuthClientCredential 的摘要/revision，以及 Auth 按 channel/rpcApiMajor 所需的当前 Version 运行配置和用户资格快照。

只有 App Center 可以创建和保存这些 Application 事实。

## Identity Context 当前拥有的事实

- 当前调用者是否已经通过身份验证。
- 当前调用者对应的 authId。
- 当前账号的 accountStatus 与 developerStatus；只有 `ACTIVE`＋`APPROVED` 可以接受管理权转让，其他管理写操作沿各自 UC 的门禁。
- Developer 申请状态及必要操作审计。
- reviewer 权限；当前已定义 `app.version.review` 和独立的 `app.profile.review`。
- Application 平台运维人员权限；`app.application.suspend` 与 `app.application.restore` 独立授予且不在平台管理员固定 bundle 中。
- 可供应用申请的 scope 名称与定义。
- Application 级永久授权关闭 tombstone，以及它对 grant、code、token、refresh、introspection/delegation 的最终执行。
- 能证明用户刚完成认证、绑定具体高风险用途与 Application 的短时证明。

客户端在申请时进行弱师生验证，平台后续自行联系确认。App Center 使用 authId 和 developerStatus，但不接收学生证明材料，也不重新执行验证。

## 当前依赖方向

- App Center 依赖一个抽象的 `DeveloperIdentity` 输入，其中包含 authId 和 developerStatus。
- UC-APP-005 依赖可信 `ReviewerIdentity`，其中包含 authId 和 Auth 授予的 reviewer permissions；它不使用宽泛的 `is_admin` 作为领域权限。
- authId 和 developerStatus 可以由已验证的入口上下文传入 UseCase。
- UC-APP-002 至 UC-APP-005 通过 ScopeCatalog 端口验证 scope。adapter 使用 5 分钟进程内 read-through cache，过期时同步读取 Auth；读取失败则 fail closed。提交和批准审核时保存各自依据的 Auth catalog revision。
- UC-APP-004 与 UC-APP-005 通过 LaunchURLSubmissionPolicy 使用 DNS 解析结果执行公网 HTTPS 预检；App Center 在这些用例中不请求目标网页内容。
- UC-APP-007 在 test 槽位真实变化前要求当前已批准公开资料，复用 ScopeCatalog 和 LaunchURLSubmissionPolicy，并记录外部复检版本；Version 审核只产生渠道无关资格，TEST Publication 独立选择 Version。开发版客户端任意 URL 直开不属于发布槽位。
- UC-APP-008 只使用可信 authId 与 developerStatus 检查当前管理员；Tester 加入链接、secret 哈希和生命周期由 App Center 保存，不依赖 Auth 保存邀请状态。
- UC-APP-009 只依赖 Auth 提供可信 authId；Tester 不要求 Developer 资格，Membership、幂等关系和容量限制由 App Center 负责。
- UC-APP-010 使用可信 developerStatus 和 authId 验证当前 admin；Membership 移除与容量释放由 App Center 原子保存，不修改 Auth 或加入链接。
- UC-APP-011 使用可信 developerStatus 和 authId 验证当前 admin；MANUAL 撤销由 App Center 保存，不修改 Membership、发布状态或 Auth。
- UC-APP-012 使用 Auth 提供的可信 authId，但不读取 developerStatus；App Center 根据自己的 Membership、Publication 和 Version 返回 TestLaunchDescriptor，不调用 Auth consent/token 接口。
- UC-APP-023 接受可选的可信身份：匿名调用只考虑 Stable；有效已认证身份按 Test、Grey、Stable 顺序解析；无效凭证失败而不降级为匿名。该查询只读组合 App Center 已有事实，不同步调用 Auth、Scope Catalog 或目标 URL。
- UC-APP-024 沿用同一可选可信身份和运行输入，批量组合 Stable-backed 普通公开候选、当前公开 Profile、UC023 唯一目标与 Filter；Filter 在官方客户端使用本地用户资料求值，App Center 不读取这些字段。
- UC-APP-013 使用可信 developerStatus 和 authId 验证当前 admin；公开资料草稿完全由 App Center 保存，不修改 Auth 或 ApplicationVersion。
- UC-APP-014 复用同一身份边界，以 expectedRevision 原子更新 App Center 自己的 DRAFT ProfileRevision，不调用外部目录或资产服务。
- UC-APP-015 复用同一身份边界，重新验证现有资料字段，在本地原子边界创建独立 PENDING ProfileReview 并把 ProfileRevision 迁移为 SUBMITTED；工作修订指针继续占用，因此不能创建并行 DRAFT。icon 不触发资产服务或外部内容检查。
- UC-APP-016 使用 Auth 授予的 `app.profile.review` 和本地版本化 ProfileReviewPolicy；它原子决定 Review/Revision，批准时同时替换当前公开指针，不修改发布槽位。
- UC-APP-016 把 REJECTED ProfileRevision 定义为终态。网页端可以读取被拒绝内容并预填 UC-APP-013 创建表单；App Center 只看到一次普通的新建草稿，不提供恢复/复制接口或保存来源关系。
- UC-APP-018 管理 Application＋channel 级稳定 client identity、状态与独立 secret credential；redirect URI 不复制到 registration，而由当前批准并发布的 ApplicationVersion 提供。
- UC-APP-019 向 Auth 分别提供登录前运行配置和登录后用户授权上下文；运行 tuple 包含当前 profileRevisionId，展示资料只来自当前 APPROVED ProfileRevision，没有技术名称 fallback。Auth 拥有 consent、code、token 和 grant。
- UC-APP-025 在 App 本地拥有账号归属退出 fence、决定与清理回执；Auth 拥有退出/关闭操作及其权威终局。
- [UC-APP-026](use-cases/UC-APP-026-transfer-application-administration.md) 在发起时新鲜检查目标、接受时新鲜批量检查源和目标的 Auth 状态；App 本地事务拥有转让终态、配额移动、名称冲突和 current admin 变化。它不要求 Auth 提供 revision 或 reservation，而是通过 UC025 的账号 fence 阻止退出终局竞态。
- [UC-APP-027](use-cases/UC-APP-027-close-application.md) 在 App 本地拥有不可逆生命周期、即时运行 gate、配额释放和关闭收敛任务；Auth 依据 [Application Closure v1](../platform/contracts/application-closure-v1.md) 与 [UC-AUTH-026](../auth-center/use-cases/UC-AUTH-026-apply-application-closure.md) 拥有永久授权 tombstone。两边以稳定 closureId 和持久回执收敛，不共享事务。关闭 proof 由 Auth 按 [近期认证证明 v1](../platform/contracts/application-close-reauth-proof-v1.md) 对当前 Session 所属同一登记设备的新挑战签发；普通 USER JWS 不能替代它。
- [UC-APP-028](use-cases/UC-APP-028-suspend-and-restore-application.md) 由 App 本地保存正交的平台可用状态、OCC revision 和运维审计；Auth 只依据 [UC-AUTH-027](../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 投影两项精确人员权限，不保存 applicationId 的暂停事实。暂停通过现有 UC019 provider 在线门禁影响 Auth，不建立 Auth 永久 tombstone。
- 当前不为 Scope Catalog 单独引入 RabbitMQ 或 Redis；未来事件只能用于加速失效，不能取代 Auth 快照读取和 revision 对账。
- Identity Context 不依赖 App Center。

## 当前不存在的上下文关系

- 没有 Resource Hub 授权。
- 没有 Expo Host RPC bridge、客户端加载或升级实现；App Center 只消费宿主提供的 rpcApiMajor/capabilities 并解析启动描述。
- 没有 Hosting Runtime。

这些关系只有在后续真实用例需要时才加入 Context Map。

OAuth 身份隔离：client/credential 按渠道隔离；major 共用同渠道 client。Application 级 sector 与用户 sub 仅由 Auth 保存，App 仅提供 client 归属及批准回调事实，见 [提供方契约](../platform/contracts/app-oauth-client-v1.md)。
