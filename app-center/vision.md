# App Center 愿景

状态：`PROPOSED`

## 系统为什么存在

App Center 为开发者提供登记和管理应用的能力，并让 iWUT 客户端在后续用例中发现和使用这些应用。

本阶段不尝试一次定义完整应用平台；UC-APP-001 至 UC-APP-016 验证应用管理与封闭测试闭环，UC-APP-018/019 定义 OAuth/OIDC 的 TEST 接入边界：

> 一个开发者可以创建一个由系统识别的应用记录，为自己管理的应用登记、修改和提交网页版本；独立 reviewer 可以依据可追溯策略批准或拒绝确定的版本或公开资料快照；资料批准后自动公开，拒绝时原公开资料不变，网页端可用被拒绝内容预填一份新草稿；版本批准只产生渠道无关的发布资格，已有当前公开资料的应用可以把已批准版本放入隔离的测试发布槽位，Tester 通过加入链接获得资格，App Center 为其解析经过授权且兼容的 test 启动目标，并为 Auth 提供 Application＋channel 级稳定 OAuth client identity、Version 级受审核回调、scope、公开展示资料和 Tester 资格快照。

## 当前用户

- 已经在 Auth 中获批开发者资格的师生：创建应用、成为当前管理员，并为自己管理的应用登记、修改、提交网页版本，处理被拒绝的版本、设置 test 槽位、管理 Tester 加入链接，以及创建、编辑和提交公开资料草稿。
- Application 当前管理员：管理 ACTIVE Tester Membership；移除只结束当前 episode，不形成黑名单或撤销加入链接。
- Auth 授予 `app.version.review` 权限的平台 reviewer：在没有利益冲突时批准或拒绝 PENDING Review。
- Auth 授予 `app.profile.review` 权限的资料 reviewer：在没有利益冲突时批准或拒绝 PENDING ProfileReview。
- 任意已登录用户：不需要 Developer 资格，即可通过有效链接自行加入 Application Tester 列表。

## 当前核心能力

- 创建一个最小 Application。
- 系统为 Application 分配 UUIDv7 ID。
- Application 记录当前 adminId；创建时它等于调用者的 authId。
- 每个开发者受到可调整的应用创建配额限制；初始配额暂定为 10。
- 记录 createdAt，作为后续审计事实。
- name 在同一 adminId 下按大小写不敏感方式唯一。
- 面向目录的资料不直接写入 Application；当前管理员可以依据 [BR-PRF-002](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-002) 创建独立的 DRAFT ApplicationProfileRevision。
- 资料草稿当前包含受 [BR-PRF-003](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-003)、[BR-PRF-004](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-004) 与 [BR-PRF-005](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-005) 约束的 displayName、可空 description 和可空不透明 icon 字符串。
- 当前管理员可以依据 [BR-PRF-009](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-009) 完整替换资料草稿，并由 [BR-PRF-011](use-cases/UC-APP-014-update-draft-application-profile-revision.md#br-prf-011) 防止并发静默覆盖。
- 当前管理员可以依据 [BR-PRF-016](use-cases/UC-APP-015-submit-application-profile-revision-review.md#br-prf-016) 提交 DRAFT，创建独立 PENDING ProfileReview snapshot；提交本身不改变当前公开资料。
- 无利益冲突的资料 reviewer 可以依据 [BR-PRF-023](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-023) 和版本化策略写入一次性决定；批准依据 [BR-PRF-030](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030) 自动替换当前公开资料，拒绝不影响旧公开资料。
- 被拒绝的 ProfileRevision 保持终态；网页端可以依据 [BR-PRF-031](use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-031) 用旧内容预填创建表单，再调用普通创建用例产生新 DRAFT；服务端不提供恢复接口。
- 返回创建后的完整 Application。
- 当前管理员可以创建一个 DRAFT ApplicationVersion。
- Version 获得独立 UUIDv7、应用内 sequence、入口 URL、RPC API 兼容范围、capabilities、scopes 和依附 Version 的 pkce/confidential OAuth redirect URIs。
- 当前管理员可以完整替换 DRAFT 的可编辑内容；revision 防止多个编辑页面静默覆盖。
- 当前管理员可以提交 DRAFT；系统重新验证 scopes 和公网 HTTPS URL，并创建独立 ApplicationReview 快照。
- reviewer 使用版本化策略作出一次性决定；批准前再次验证 scopes 和 URL，拒绝必须说明原因。
- 当前管理员可以把最新被拒绝的 Version 显式恢复为 DRAFT，保留拒绝决定并记录恢复审计。
- 当前管理员可以把兼容的 APPROVED Version 放入一个 rpcApiMajor 的 test 槽位；Publication revision 和追加式 History 保护并发与审计。
- 当前管理员可以为整个 Application 创建或原子轮换一个有效 Tester 加入链接；二维码只是链接的客户端展示，App Center 只保存 secret 哈希和生命周期审计。
- 已登录用户可以在 Application Tester 上限内通过有效链接创建 ACTIVE Membership；重复加入幂等，被移除后仍可使用有效链接重新加入。
- 每个 Application 最多有 100 个 ACTIVE Tester；当前管理员可以按 membershipId 幂等移除并原子释放名额。
- 当前管理员可以按 joinLinkId 幂等执行 MANUAL 撤销；撤销立即阻止后续加入，但不影响现有 Tester。
- App Center 根据 ACTIVE Membership、exact RPC major Publication 和 host capabilities 返回 TestLaunchDescriptor，不把授权或版本选择下放给客户端。
- 当前管理员可以为 Application 登记长期稳定的 PUBLIC/CONFIDENTIAL clientId；identity/status 与 confidential credential 使用独立 revision，redirect URI 与 scopes 继续由 ApplicationVersion 审核和发布。Version、major 或 hostname 变化不重建 clientId。
- Auth 可以在登录前取得用户无关的当前运行配置，在登录后取得 TEST 的 ACTIVE Tester episode 或公开 STABLE 的授权上下文；App Center 不签发 code 或 token。
- 当前管理员可以直接设置、替换、回退或清空 exact-major stable 槽位；空记录、共享 Publication revision 和追加式 History 保留并发与审计事实，STABLE OAuth channel 独立于 TEST。

## 当前尚未设计或明确后置的能力

- Application 管理查询、受控改名、归档、禁用和恢复；物理删除仍不是首版目标。
- 协作者和角色。
- 管理员转让；当前只为未来转让保留 adminId 语义。
- ApplicationVersion 的审核撤回、决定推翻和已批准资格撤销；Grey 发布已有已接受的 UC-APP-021，当前正在实现。
- versionLabel 语义比较和 SemVer 校验。
- 受控图标资产生命周期、AI 对 DRAFT 的审核，以及 release notes 等版本展示资料。
- reviewer 分配、双人审批、SLA 和系统内申诉渠道；申诉当前直接联系平台。
- Application admin 或 SysAdmin 发起的 Application 级禁用及重新启用；紧急隐藏不作为 ProfileRevision 状态。
- Tester 主动退出、UC-APP-021 Grey rollout 实现、test clear 和普通用户统一运行解析。
- Expo RPC 握手、运行时兼容解析和客户端升级提示；当前只登记 RPC major range 与 capabilities。
- Resource Hub、Hosting Runtime，以及 Auth consent/token 等用户数据授权执行；App Center 只登记版本申请的 scopes/redirect URIs 并提供资格快照。
- 兼容现有 App Center API 和 MongoDB 文档。

## 本轮成功标准

- UC-APP-001 的输入、结果和错误没有歧义。
- Application 的四个业务字段有明确来源。
- adminId 不能由请求正文冒充，必须取自已验证的 authId。
- 只有 Auth 中开发者资格为 APPROVED 的调用者可以创建。
- `(adminId, name)` 唯一约束和创建配额在并发请求下仍成立。
- ID 唯一性由系统负责。
- createdAt 由系统时钟生成。
- 可以用不依赖数据库的测试证明领域规则。
- 可以用 Repository fake 证明创建用例的协调行为。
- 新建版本只能处于 DRAFT，且不会自动进入目录或任何发布槽位。
- 管理员检查、sequence 分配和版本插入在并发及管理员转让时保持原子。
- 只有 DRAFT 可以编辑，且管理员、状态、revision 检查与更新在同一原子边界中完成。
- 提交审核会冻结登记信息快照，并与 Version 的 `DRAFT -> SUBMITTED`、revision 和审计更新原子提交。
- 审核决定只能写入一次，不能自审；Review 与 Version 的批准或拒绝状态原子一致，且不会自动发布。
- 恢复拒绝不会改写原 decision；恢复审计与 `REJECTED -> DRAFT`、revision 更新原子一致。
- test 槽位按 `(applicationId, rpcApiMajor)` 唯一，只引用兼容的 APPROVED Version；真实变化与 History 原子提交且不修改 Version。
- Tester 加入链接属于整个 Application，不绑定 RPC major、Version 或目标用户；每个 Application 同时最多一个有效链接，轮换不会创建 Tester Membership。
- Tester Membership 按 `(applicationId, authId)` 保证唯一 ACTIVE episode，容量检查、Membership 创建和计数变化在并发下保持原子。
- 移除保留 REMOVED episode 和审计，不撤销加入链接；存在有效链接时管理界面仅提示该用户仍可再次加入。
- 显式撤销链接保留 REVOKED/MANUAL 审计，不创建替代链接、不移除 Tester，也不建立黑名单。
- test 启动解析是只读服务端查询，不回退其他 RPC major/grey/stable，不在启动热路径同步访问 Auth Scope Catalog 或 launchUrl。
- 新建 ProfileRevision 是完整且非公开的 DRAFT；displayName/description/icon 与 Application、ApplicationVersion 分离，同一 Application 同时至多有一份 DRAFT 或 SUBMITTED 工作修订，见 [BR-PRF-006](use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006)。
- 只有 DRAFT ProfileRevision 可以完整替换；expectedRevision、当前管理员和状态检查与真实修改原子完成，no-op 不制造审计变化。
- 提交资料审核会冻结 displayName/description/icon 快照，并与 ProfileRevision 的 `DRAFT -> SUBMITTED`、revision 和审计更新原子提交；当前公开资料保持不变，工作修订位继续被占用。
- 资料审核决定只能写入一次，不能审核自己创建、提交或当前管理的资料；Review 与 Revision 的结果原子一致。
- 资料批准与当前公开指针替换原子完成，但不创建 stable 槽位；资料拒绝不改变原公开指针。
- REJECTED ProfileRevision 保持原 decision、snapshot、内容与审计；网页端重新编辑时通过 UC-APP-013 创建独立新 DRAFT，仍受单一 DRAFT 约束保护。

OAuth 身份隔离：client/credential 按渠道隔离；major 共用同渠道 client。Application 级 sector 与用户 sub 仅由 Auth 保存，App 仅提供 client 归属及批准回调事实，见 [提供方契约](../platform/contracts/app-oauth-client-v1.md)。
