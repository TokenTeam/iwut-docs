# App Center Context Map

状态：`PROPOSED`

## 当前边界

```text
Identity Context
  ├─ 提供可信 authId + developerStatus
  ├─ 提供可信 reviewer permissions
  └─ 拥有 Auth Scope Catalog
          │
          ▼
App Center Context
  ├─ 拥有并创建 Application
  ├─ 拥有 ApplicationProfile、ApplicationProfileRevision 及其资料生命周期
  ├─ 拥有独立 ApplicationProfileReview 与提交快照
  ├─ 拥有 ApplicationVersion 及其审核生命周期
  ├─ 拥有 ApplicationReview 与提交快照
  ├─ 拥有按 RPC major 分区的 ApplicationPublication
  ├─ 拥有 ApplicationPublicationHistory
  ├─ 拥有 Application 级 Tester 加入链接
  ├─ 拥有 Application Tester Membership 与容量事实
  ├─ 依据 Membership、Publication、Version 解析 test 启动目标
  └─ 拥有 Application Creation Quota
```

## App Center 当前拥有的事实

- 哪个 Application ID 已经存在。
- Application 的 name 和 createdAt。
- ApplicationProfileRevision 的身份、应用内 sequence、displayName、可空 description、可空不透明 icon、DRAFT/SUBMITTED/APPROVED/REJECTED 状态、revision，以及创建和最近修改审计；资料草稿采用完整替换和乐观并发。
- 每次 ProfileReview attempt 的身份、不可变 displayName/description/icon 快照、sourceRevision、一次性 decision、状态，以及提交和决定审计。
- ApplicationProfile 当前工作修订与公开资料指针，以及 App Center 自己的版本化 ProfileReviewPolicy。
- 哪个 authId 是 Application 当前 adminId。
- 同一 adminId 下哪些名称已经被占用。
- adminId 当前的应用创建配额和已使用数量。
- ApplicationVersion 的身份、应用内 sequence、入口 URL、RPC 兼容声明、scopes、审核状态、revision，以及创建和最近修改审计。
- 每次审核 attempt 的身份、不可变提交快照、一次性决定、状态，以及提交/决定/草稿恢复审计。
- App Center 自己的版本化审核策略和检查项。
- 每个 `(applicationId, rpcApiMajor)` 当前 test 发布指针、Publication revision 和修改审计。
- 每次真实槽位变化的追加式 PublicationHistory。
- 每个 Application 当前有效的 Tester 加入链接、secret 哈希，以及 `ROTATED/MANUAL` 撤销审计。
- 哪些 authId 当前是某个 Application 的 Tester、历史 Membership episode，以及固定 100 人上限下的 ACTIVE Tester 数量。
- 对给定 Tester、hostRpcApiMajor 和 hostCapabilities，哪个 test ApplicationVersion 构成当前 TestLaunchDescriptor。

只有 App Center 可以创建和保存这些 Application 事实。

## Identity Context 当前拥有的事实

- 当前调用者是否已经通过身份验证。
- 当前调用者对应的 authId。
- 当前调用者的 developerStatus；只有 `APPROVED` 可以执行当前已经定义的应用与版本管理写操作。
- Developer 申请状态及必要操作审计。
- reviewer 权限；当前已定义 `app.version.review` 和独立的 `app.profile.review`。
- 可供应用申请的 scope 名称与定义。

客户端在申请时进行弱师生验证，平台后续自行联系确认。App Center 使用 authId 和 developerStatus，但不接收学生证明材料，也不重新执行验证。

## 当前依赖方向

- App Center 依赖一个抽象的 `DeveloperIdentity` 输入，其中包含 authId 和 developerStatus。
- UC-APP-005 依赖可信 `ReviewerIdentity`，其中包含 authId 和 Auth 授予的 reviewer permissions；它不使用宽泛的 `is_admin` 作为领域权限。
- authId 和 developerStatus 可以由已验证的入口上下文传入 UseCase。
- UC-APP-002 至 UC-APP-005 通过 ScopeCatalog 端口验证 scope。adapter 使用 5 分钟进程内 read-through cache，过期时同步读取 Auth；读取失败则 fail closed。提交和批准审核时保存各自依据的 Auth catalog revision。
- UC-APP-004 与 UC-APP-005 通过 LaunchURLSubmissionPolicy 使用 DNS 解析结果执行公网 HTTPS 预检；App Center 在这些用例中不请求目标网页内容。
- UC-APP-007 在 test 槽位真实变化前复用 ScopeCatalog 和 LaunchURLSubmissionPolicy，并记录复检版本。
- UC-APP-008 只使用可信 authId 与 developerStatus 检查当前管理员；Tester 加入链接、secret 哈希和生命周期由 App Center 保存，不依赖 Auth 保存邀请状态。
- UC-APP-009 只依赖 Auth 提供可信 authId；Tester 不要求 Developer 资格，Membership、幂等关系和容量限制由 App Center 负责。
- UC-APP-010 使用可信 developerStatus 和 authId 验证当前 admin；Membership 移除与容量释放由 App Center 原子保存，不修改 Auth 或加入链接。
- UC-APP-011 使用可信 developerStatus 和 authId 验证当前 admin；MANUAL 撤销由 App Center 保存，不修改 Membership、发布状态或 Auth。
- UC-APP-012 使用 Auth 提供的可信 authId，但不读取 developerStatus；App Center 根据自己的 Membership、Publication 和 Version 返回 TestLaunchDescriptor，不调用 Auth consent/token 接口。
- UC-APP-013 使用可信 developerStatus 和 authId 验证当前 admin；公开资料草稿完全由 App Center 保存，不修改 Auth 或 ApplicationVersion。
- UC-APP-014 复用同一身份边界，以 expectedRevision 原子更新 App Center 自己的 DRAFT ProfileRevision，不调用外部目录或资产服务。
- UC-APP-015 复用同一身份边界，重新验证现有资料字段，在本地原子边界创建独立 PENDING ProfileReview 并把 ProfileRevision 迁移为 SUBMITTED；工作修订指针继续占用，因此不能创建并行 DRAFT。icon 不触发资产服务或外部内容检查。
- UC-APP-016 使用 Auth 授予的 `app.profile.review` 和本地版本化 ProfileReviewPolicy；它原子决定 Review/Revision，批准时同时替换当前公开指针，不修改发布槽位。
- UC-APP-016 把 REJECTED ProfileRevision 定义为终态。网页端可以读取被拒绝内容并预填 UC-APP-013 创建表单；App Center 只看到一次普通的新建草稿，不提供恢复/复制接口或保存来源关系。
- 当前不为 Scope Catalog 单独引入 RabbitMQ 或 Redis；未来事件只能用于加速失效，不能取代 Auth 快照读取和 revision 对账。
- Identity Context 不依赖 App Center。

## 当前不存在的上下文关系

- 没有 OAuth Client Registration。
- 没有 Resource Hub 授权。
- 没有 Expo Host RPC bridge、客户端加载或升级实现；App Center 只消费宿主提供的 rpcApiMajor/capabilities 并解析启动描述。
- 没有 Hosting Runtime。

这些关系只有在后续真实用例需要时才加入 Context Map。
