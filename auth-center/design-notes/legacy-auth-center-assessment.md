# 旧 Auth Center 设计扬弃与用户模型建议

状态：`PROPOSED`

日期：2026-09-22

性质：非权威设计评估与后续设计输入。本文不新增 UC/BR，不改变已接受规则，也不代表以下建议已经被产品接受。

## 评估范围与结论

本次以旧 `iwut-auth-center` 的 `e548083` 为源码基线，检查 `biz`、`service`、`data`、身份中间件、JWT 工具、索引初始化及相关 Gateway Auth Forward 读取路径，并与当前 `docs/auth-center`、`docs/platform` 和 App Center 边界对照。

这是静态实现评估，没有执行旧服务或复现并发问题。旧仓库当前没有检出可读取的 `api` Proto 文件，因此不对生成的字段校验、完整协议兼容性或实际部署暴露情况作保证。代码注释与实现不一致时，以函数实际执行路径为依据。

结论：旧实现覆盖了有价值的用户旅程，但主体、登录凭据、资料、资格、授权与应用存储的边界不够清晰，状态变化和失效语义也没有完整闭合。可以继承需求、部分概念与不变量；不能把旧 user 文档或旧 API 直接作为新用户模型。

下一步适合设计最小 USER 主体、账号生命周期和身份建立用例。资料同步、Developer 申请、Consent 与应用存储分别展开，避免一次性复制旧 User 的全部职责。

## 旧模型实际表达了什么

旧 `user` collection 逐步承载了：

- `uid`：注册时生成的 UUIDv7，与 MongoDB `_id` 不同。
- `email`、`password`：邮箱登录标识和密码摘要。
- `version`：供 token 失效判断使用的用户级版本。
- `created_at`、`updated_at`、`deleted_at`：时间与软删除标记。
- `claim.developer_id` 及修改时间：用户自选的唯一开发者名称。
- `profile`：由用户入口写入的动态扁平资料。
- 以应用 ID 构造的字段路径：应用在该用户上的键值存储。

另有 `user_consents`，按 `(user_id, client_id, type)` 保存同意的版本、可选 scope 和 token ID；其中 `type` 是 `TEST/STABLE/GREY`。Redis 保存验证码、授权码、用户 token 版本缓存和 OAuth token allowlist。

证据入口：[注册持久化](../../../iwut-auth-center/internal/data/auth.go)、[用户持久化](../../../iwut-auth-center/internal/data/user.go)、[应用存储](../../../iwut-auth-center/internal/data/oauth2.go)、[索引](../../../iwut-auth-center/internal/data/data.go)。

## 保留、重构与淘汰

| 旧概念或行为 | 取舍 | 新设计方向 |
| --- | --- | --- |
| 独立于邮箱的稳定 `uid` | 保留 | 由 Auth 分配稳定 opaque `authId`；明确它与内部存储 ID 的关系。无需为了改名再造第二套用户身份。 |
| 邮箱注册、验证、密码登录、找回密码 | 保留为首版候选旅程 | 把邮箱作为登录标识/联系方式，把密码作为凭据；明确邮箱唯一性、比较规则、验证与变更流程。首版采用邮箱不意味着现在就实现多登录方式。 |
| 用户级 token 版本 | 保留“全局使登录失效”的需求，重构机制 | 如继续使用，明确为独立的认证版本或 epoch；与资料 revision、权限 revision、Developer 状态分离，单调更新且不取模回绕。 |
| Access/Refresh 分工 | 保留目的，重建会话 | 明确会话身份、刷新、过期、退出和撤销；客户端登录凭证与内部 trusted identity 分开。 |
| `developerId` | 重新命名和定位 | 实际是可修改的唯一 handle，不是资格审批结果。只有产品确实需要公开开发者名称时才引入，不能用于授权或替代稳定主体 ID。 |
| `profile` 动态属性 | 保留资料需求，重构信任和字段契约 | 区分用户自填、客户端同步/弱验证、平台审核结果；逐项决定字段来源、写权限、类型、更新和披露规则。 |
| `claim` 数据与用户资料分开 | 保留意图 | 平台授权事实使用明确模型；签发 claims 是事实的投影，避免把任意 claim 字典当作领域模型。 |
| Consent 与必要/可选 scopes | 保留 | 同意内容、有效状态、变更与撤回成为独立事实；必要权限扩张需要重新同意，可选权限不能被自动增加。具体规则由后续 UC 接受。 |
| 按应用隔离的用户 KV 存储 | 保留为独立能力候选 | 按 `(authId, applicationId)` 隔离，独立定义配额、并发与清理；不继续作为 user 文档的动态顶层字段。 |
| 软删除和恢复窗口 | 保留需求候选，重写生命周期 | 明确注销申请、恢复、最终关闭及权限影响；30 天和登录自动恢复不能直接成为新规则。 |
| UUID、唯一索引、TTL、随机验证码、请求关联信息 | 保留工程意图 | 补齐唯一约束失败时的处理、原子消费与不可变业务审计。 |
| 未签名身份头、Gateway 直读 Auth 数据库、单次 SHA-256 密码摘要 | 淘汰 | 使用当前平台身份契约；认证事实由 Auth 拥有；密码使用专用密码哈希机制。 |
| STABLE/GREY/TEST 作为授权记录的主分类 | 重建 | 新 App Center 已区分版本、发布槽位和 Tester 资格；不能用发布渠道代替授权内容的身份。是否需要测试授权隔离，应由明确用例决定。 |

## 对用户模型影响最大的六个问题

### 1. Developer ID 是名称，Developer 资格是授权事实

`UserUsecase.SetUserDeveloperId` 只检查格式、用户存在和预期的 30 天修改间隔；Service 允许持普通用户身份调用。该路径没有资格申请、审批或暂停。登录把它写入 `did`，刷新 token 时又没有重新加入该字段。

因此，旧名称可以成为将来的 `developerHandle` 候选，但新系统的 Developer 生命周期必须按已接受的 [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) 继续设计。

同样，权限管理遵循 [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md)，不能从 handle、邮箱或资料字段推导 Reviewer/管理员权限。

证据：[SetUserDeveloperId](../../../iwut-auth-center/internal/biz/user.go)、[用户入口](../../../iwut-auth-center/internal/service/user.go)、[登录与刷新](../../../iwut-auth-center/internal/service/auth.go)。

### 2. “OfficialAttrs”没有形成官方可信证明

`UserService.UpdateProfile` 允许用户提交资料，UseCase 只检查字段名、值形状和本次请求大小，然后 patch 到 `profile`。没有按字段验证来源或证明真伪，也没有把姓名、学号、院系等定义成已验证事实。

所以 `OfficialAttrs` 最多说明官方客户端使用的资料命名空间，不能从名称推断其权威性。这与当前 App Center glossary 所述师生身份弱验证应保持一致。

建议把以下事实分开表达：用户声称/同步的资料、具体核验过程及其可信程度、平台最终授予的资格。不要把邮箱验证等同于师生验证，也不要把师生资料直接等同于 Developer 获批。

动态字段也不能直接兼任 Scope Catalog：字段存在只说明有数据，不意味着应用可以申请访问它。scope 应由 Auth 权威目录定义，再映射到明确的数据投影。

证据：[资料写入规则](../../../iwut-auth-center/internal/biz/user.go)、[资料 patch](../../../iwut-auth-center/internal/data/user.go)、[当前 Developer 术语](../../app-center/glossary.md)。

### 3. 用户身份、登录会话、内部凭证需要分开

旧普通用户 token 主要包含 `uid/type/version`，刷新只检查用户级 version 并签发新 token，没有消费旧 refresh token 或独立 session 状态。它能表达粗粒度全局失效，但不能清楚表达单设备退出、单会话撤销、刷新重放和最长会话寿命。

旧改密/注销还存在两个版本来源：Mongo 更新根据数据库 version，Service 写 Redis 根据 token 中的 version；两次写也不是原子操作。因此“操作返回成功/失败”和“旧登录到底何时失效”缺少一致语义。

新设计建议区分：

1. Principal：动作由谁执行。
2. 登录凭据与 Session：如何证明身份、登录能维持多久、如何退出或撤销。
3. trusted identity：Auth 基于有效身份和当前资格/权限，向目标服务提供的短期投影。

第三项已有 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，前两项仍待 Auth 用例定义。未来若采用 OAuth public client 刷新机制，应遵循发送方绑定或刷新轮换及重放检测要求，见 [RFC 9700 §4.14](https://www.rfc-editor.org/rfc/rfc9700.html#section-4.14)。

### 4. “撤销 token”和“撤回同意”必须是不同操作

`RevokeUserConsent` 清空 consent 的 `token_id` 并删除 Redis allowlist，却没有删除或标记同意记录失效。`LoadUserConsentRecords` 和 `resolveUserConsentAccess` 仍可使用留下的版本与 scopes；在其他条件满足时，用户无需重新提交同意便可再次取得授权码。

所以旧函数实现的是已有 token 的撤销意图，不能代表用户撤回同意。新模型需要显式区分 Consent、一次授权/会话和派生 token，定义撤回后是否禁止继续签发、存量凭证多久失效、重新授权如何发生。

旧代码还根据 App Center 的 STABLE/GREY/TEST 状态组织 consent 并互删 stable/grey 记录。该结构绑定旧发布模型，不适合直接套用新 ApplicationVersion/Publication 设计。

证据：[RevokeUserConsent](../../../iwut-auth-center/internal/data/user.go)、[consent 解析](../../../iwut-auth-center/internal/biz/oauth2.go)、[当前发布模型](../../app-center/lifecycle-models.md)。

### 5. 账号注销需要业务生命周期

旧代码设置 `deleted_at` 后，密码登录以及 `GetDeveloperIdByUserId` 都可能调用 `TryRestoreDeletedUser`，在 30 天内清除标记。超过期限则拒绝恢复；本次读取范围内未看到与之闭合的最终清理工作流。

这可以是产品选择，但不应该隐藏在 Repository 读取方法中。新设计需要决定恢复是否显式确认、注销后是否还可刷新/签发、邮箱何时可重新使用，以及应用管理员归属、历史审核和授权记录如何处理。

账号禁用、用户申请注销、Developer 暂停、某权限撤销表达不同业务事实，不能共用一个“禁用”字段。完整注销实现可以后置，但至少应先明确账号是否允许认证/签发的规则。

证据：[删除账号](../../../iwut-auth-center/internal/data/user.go)、[自动恢复](../../../iwut-auth-center/internal/data/auth.go)。

### 6. 用户数据承载能力需要边界

旧 User 同时承载登录资料、平台资料和每个应用的 KV，后者还假定应用 ID 有两个由点分隔的部分。它将应用标识格式直接变成 Mongo 路径，是旧系统的存储耦合。

建议资料与应用存储在逻辑上独立，是否独立服务以后决定。不要因为拆分领域责任就立即增加微服务，也不要在没有用例时确定所有集合。后续分别决定其配额、并发、生命周期和授权方式。

证据：[SetUserStorageData / validateApplicationId](../../../iwut-auth-center/internal/data/oauth2.go)、[旧 ApplicationInfo](../../../iwut-auth-center/internal/util/app_center.go)。

## 不应继承的实现机制

以下为静态源码中可定位的问题；其影响范围仍取决于实际入口和部署配置。

| 实现依据 | 问题 | 新设计需保证的性质 |
| --- | --- | --- |
| `util/sha256.go: HashPassword` | 使用全局配置 salt 做一次 SHA-256；注释还保留客户端密码预处理不确定性 | 明确密码输入契约，使用 Argon2id 等专用密码哈希及每条凭据的随机 salt。参见 [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)。 |
| `middleware/jwt_info.go` | 后端解析 `X-Auth-*-Claim` JSON 即建立身份，没有在此边界验签 | 遵循已接受的用户/服务 JWS 契约，认证与 RPC 授权分别检查。 |
| Gateway Auth Forward 的 `data/auth.go`、`data/oauth2.go` | 直接读取 Auth Mongo/Redis；用户版本回源还使用 `_id`，与旧注册写入独立 `uid` 不一致 | 认证存储由 Auth 私有拥有，Gateway 通过明确契约取得认证结果。 |
| `data/auth.go: Check*CaptchaUsable` | 先检查再删除；删除失败仍成功；并发请求可能重复使用同一验证码 | 校验和消费原子化，限定用途、有效期和尝试次数，并定义后续写入失败的重试语义。 |
| `service/oauth2.go: GetToken` + `data/oauth2.go` | 授权码先 GET，签发后 DEL；并发交换可能都成功 | 授权码最多成功消费一次；消费、业务确认和失败恢复有明确顺序。 |
| `biz/user.go: UpdateUserConsent` | App Center 返回 `allowed=false` 时仅写日志，随后仍可写入 consent | 业务前置条件失败时拒绝写入；该缺陷本身不等于后续所有访问都被放行。 |
| `biz/oauth2.go: GetUserOfficialProfile` | 已解析可选授权 scope，但读取只与 `BasicScope` 求交 | 必要/可选授权在签发和实际读取中采用一致的有效权限计算。 |
| `data/data.go: NewData` | 唯一索引创建失败只警告，服务继续启动 | 邮箱等业务唯一性是运行前提，迁移/启动流程必须保证约束有效。 |
| `biz/user.go: UpdateUserProfile` | 只限制本次 patch 大小，持久化不断合并字段 | 如果限制总资料容量，必须检查合并后的状态并处理并发。 |
| `service`、`data` 中的状态变化 | 大量业务编排在 Service，恢复/撤销策略在 Repository；`AuthUsecase` 主要暴露 Repo | 用例负责流程，领域模型负责规则，Repository 负责持久化；不可变审计与业务写入的一致性单独明确。 |

旧 OAuth 中已有 redirect URI 比较、S256 校验和 scope 集合处理，这些需求值得保留，但协议不完整：PKCE 可选、所有客户端统一要求 secret、access token 同时作为 id token 返回、此仓库 token endpoint 仅处理 authorization_code。不能把“已经有 OAuth2Service”视为新系统已有完整 OAuth/OIDC 能力。

若未来确实建设第三方 OAuth 登录/授权，先确认 public/confidential client、资源 audience、ID token 与 access token 的职责，再形成独立协议设计；当前最小 USER 设计不以重建整套 OAuth 为前置。Public client 的 PKCE 要求参见 [RFC 9700 §2.1.1](https://www.rfc-editor.org/rfc/rfc9700.html#section-2.1.1)。

## 建议的新概念边界

以下是设计候选，不是已接受的数据 schema，也不预设必须拆成独立 collection：

| 概念 | 负责的事实 | 本轮范围 |
| --- | --- | --- |
| Principal | 稳定主体身份与主体类型 | 延续已接受的 USER/SYSTEM 基础，明确 USER 创建。 |
| UserAccount / 账号生命周期 | 用户是否可以认证、是否申请关闭及相关状态 | 确认最小可登录规则；是否独立于 Principal 表达由用例决定。 |
| LoginIdentifier / Credential | 邮箱标识、验证事实和密码证明 | 按首版登录方式设计；不提前实现所有身份提供方。 |
| AuthenticationChallenge | 邮箱验证/重置的一次性证明 | 首版若使用邮箱验证，需要明确消费和重试语义。 |
| Session | 一次登录的持续性、刷新、退出与撤销 | 与身份签发一起设计。 |
| Developer 资格 | 申请、审批、暂停和恢复 | 保留既有状态约束，独立 UC 定义迁移。 |
| PermissionGrant | 平台人员原子权限与审计 | 延续 UC-AUTH-004，不与资格或 handle 合并。 |
| UserProfile / VerificationEvidence | 用户资料与其来源、核验事实 | 先定职责边界，按真实资料用例扩展。 |
| ConsentGrant | 用户同意应用访问什么、何时撤回 | 后续独立纵切片，不作为 USER 创建的必填内容。 |
| ApplicationUserStorage | 应用在某用户下保存的隔离数据 | 后续独立能力。 |

## 建议的下一轮设计顺序

1. 先确认产品边界：谁可以注册、首版登录方式、邮箱验证代表什么、Auth 与用户资料能力的关系。
2. 设计普通 USER 建立用例：主体生成、唯一性、初始状态、重复请求及审计。创建 USER 不隐式申请 Developer。
3. 设计认证与 Session：登录、刷新、退出、改密/重置对会话的影响，以及从有效会话取得 trusted identity 的流程。
4. 接通平台管理员 bootstrap 与 Reviewer 管理，再以独立用例闭合 Developer 申请/审批/暂停/恢复；二者不存在必须先获 Developer 才能管理权限的前置关系。
5. 随真实需求设计资料、核验、Consent 和应用存储。

本轮尤其应避免把旧 handle 变成身份主键、把客户端资料变成平台授予事实、把 token 撤销当作 consent 撤回，以及把全部旧 User 功能一次性塞入新聚合。

本文不隐含旧数据迁移任务。若未来需要迁移真实用户，另行评估稳定 ID 映射、邮箱冲突、密码升级、旧 consent 的可证明性和用户重新登录要求。
