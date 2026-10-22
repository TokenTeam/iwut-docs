# Auth Center 开放问题

状态：`ACTIVE`

## 宿主 OAuth RPC（2026-10-22）

[UC035](use-cases/UC-AUTH-035-authorize-application-in-host.md) 保持 DRAFT：用户已确认官方宿主可信 consent 界面，并指定 `TokenTeam/native-rpc-h5` 仅作参考、允许扩展。[适配设计说明](design-notes/host-oauth-rpc-design.md)记录调用模型与分层。尚待冻结宿主→Auth 交互/确认保护及两类 client 的 code 交付/兑换绑定；RPC 传输和 Native 内部实现由宿主负责，不再作为 Auth 后端开工依赖。账号管理 UI 归属独立决定，不因本项确认自动 ACCEPTED 或开工。

## 设备登录凭据管理（2026-10-12）

2026-10-15：已接受的邮箱 v3 与 UC006/011/031、UC009/025/026 防旁路及 UC032 后端均已交付。UC033 四项密码管理/恢复方法和通知 worker、UC034 两项密码登录方法已串行完成并通过全仓真实 Wire/Mongo/race。当前 [readiness](implements/UC-AUTH-033-034-readiness.md) 为交付依据；入口默认关闭，Gateway/客户端与生产启用独立验收，不据后端完成宣布完整产品可用。

用户 2026-10-13 授权继续完成 [UC-AUTH-032](use-cases/UC-AUTH-032-manage-own-device-credentials.md)，已 ACCEPTED/后端 COMPLETE；[依赖与验收记录](implements/UC-AUTH-032-readiness.md)记录本轮代码基础和真实回归。本轮先依赖复核、脚本 brief，再实施既有草案范围；四方法、双证明、限额与清理已交付。设备密钥继续退居后台，当前方案不是标准 WebAuthn Passkey。

- 已接受首版：未撤销凭据的有界列表、可选名称和独立 revision、当前凭据标记；不收集 IP/型号/位置，不虚构凭据最近使用时间。移除其他凭据用当前密码＋当前 Session 所引用设备的新签名，与目标撤销同事务提交；当前凭据仍按 UC009 退出。
- 审核门禁已通过：用户授权继续完成既有范围；UC009 已限制为当前凭据，不能由 UC032 开关关闭而恢复旧旁路。Gateway、客户端与生产启用仍独立交付，不包含扫码新增、WebAuthn 或批量撤销。
- 邮箱与密码方向已同步权威 UC006/011/031，三项实质修订已 ACCEPTED 并实施；UC012/013/017 与共享契约同步消费边界，代码已改新目录/角色并通过全仓回归。密码工作包 UC033/034 后端 COMPLETE；UC032 仅引用其依赖，不作第二份邮箱/校园规则正文，客户端仍独立交付。
- 已审核接受：[邮箱 v3 契约](../platform/contracts/auth-email-account-v3.md)的新注册/目录/角色协议与校园时间语义；所有地址全局唯一/最多 10 个已确认，不再开放。正式 blocklist/部署压测、客户端和 Gateway 属于生产交付门禁；密码后端/清理恢复现状见 readiness。扫码后移，不替代密码。
- 后移：旧设备授权新设备另立 UC；新增设备可通过 UC034 主动密码登录或 UC012 备用码登录。凭据硬上限、自动淘汰、批量撤销、标准 WebAuthn 和真实物理设备识别不进入首版。

## 邮箱账号与应用次数权益（2026-10-12）

此前邮箱显式注册/关联退役和永久独立认证基线已交付；最新密码/邮箱列表/当前学校绑定模型见上方及修订 UC006/011/031，不再永久保留无依据认证。校园成员不等于学生权限，应用次数仍自管。

UC031 本次修订已 ACCEPTED 并实现当前依据模型，旧永久事实仅作历史；应用次数参考保持 GUIDANCE。仍按依赖闭合、用户审核、ACCEPTED、脚本 brief 后才实施；文档修订与代码完成分开，见 implements。

- Auth：当前学校绑定与最后依据撤回、密码注册/邮箱列表已交付；旧独立永久认证不再授权，不用资料/未验证后缀替代。普通密码入口的最新验收见 readiness，不以旧测试证明新增模型。
- 应用：一次性赠送按账号与活动去重，余额和消费流水由应用服务端持有，不信任客户端可写 UC030 KV。仅提供非权威开发者参考；具体活动/数量/业务/失败定义由应用决定，不是 Auth 实施依赖，不在 Auth 建立次数账本 UC。
- 边界：按账号一次不承诺按自然人一次；注销新账号可能再次符合条件。若应用不能接受，须先独立设计跨账号防重复方案，不默认为 Auth 保存永久邮箱已消费库。
- 外部业务：扣次后执行若不能同事务提交，需要幂等执行或结果查询；未知结果不能直接退款或重做。GREY/STABLE 余额隔离与应用账本注销保留也需应用确认。

## 账号与平台资格治理（2026-10-05）

新增[治理设计草案](design-notes/account-governance-delivery-plan.md)，规划管理员授予/撤销、账号禁用/恢复、Developer 暂停/恢复、Developer 退出及本人注销五个候选 UC。治理设计已接受，既有权限/状态/初始化契约同步修订；代码和部署状态独立跟踪。管理员管理已展开为 [UC021](use-cases/UC-AUTH-021-manage-platform-administrators.md)（ACCEPTED），固定集合、最后管理员保护及一次性初始化仍待接受；系统未上线，不设计旧 bootstrap 迁移，生产应急恢复规程独立交付；App 应用归属处置、暂停的对外生效边界与注销数据清理仍是跨服务交付依赖。具体实现现状以 [实现记录](implements/README.md) 为准，不以本页历史开放问题推断实现缺失。

账号禁用与恢复已展开为 [UC022](use-cases/UC-AUTH-022-disable-and-restore-user-account.md)（ACCEPTED）：选择 accountRevision 作为认证材料代际；UC021 前置能力及全部认证/OAuth 消费路径的版本校验是实施依赖。已签下游短期 JWS 和第三方自身登录态的边界见该 UC，不宣称全部即时登出。

Developer 暂停/恢复、主动退出和本人注销已展开为 UC023–025（均 ACCEPTED/IN_PROGRESS）。退出首版不重新开通；注销允许保有有效设备密钥的禁用账号使用专用途径，先满足应用归属/管理员交接门禁。共同硬依赖见 [App 归属退出协调草案](../platform/contracts/account-owner-exit-v1.md)；WITHDRAWN/CLOSED 消费语义、数据清理与保留策略、终止清单及备份恢复必须在接受和上线前分别闭合，不能视为现有能力。

## 当前设计优先级（2026-09-27）

用户决定先推进 OIDC 登录、用户 scope 授权和收回，支持 PUBLIC_PKCE 与 CONFIDENTIAL_SECRET。已建立 Auth014–019、App018–019、Gateway002 的 PROPOSED 设计，见 [工作包总览](design-notes/oauth-oidc-delivery-plan.md)。Gateway OAUTH2 仍未启用；生产 Catalog 初始装载、官方门户、资源委托验证及联合测试属于明确交付依赖，在线 Catalog 管理后移。TEST 之外的正式运行资格、原生无感浏览器 SSO 桥和动态资料 scope 仍需后续设计。

## Scope Catalog 后续写侧

### Catalog 写入与初始装载

UC-AUTH-001 只读取已经存在的权威目录。目录由部署种子、显式管理 UC 还是其它权威源产生仍未决定。生产实现不得把测试 fixture 或 App Center 的硬编码列表当成权威目录。

### Scope 启用语义已明确

2026-09-28：采用 enabled 单一权威状态，对 App 固定投影 requestable=enabled；不存在“禁止新申请但继续运行”的独立状态。规则见 [BR-SCP-004](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)，OAuth 实际权限与历史同意恢复见 UC014–019。该设计决定已闭合；生产持久化、部署装载和相应验证仍待交付，不影响已完成的 UC-APP-018 client 管理。

### 完整 Scope 元数据

首个消费方只需要 `name` 和 `requestable`。面向 consent UI、审计或数据投影所需的 display name、description、sensitivity 等字段，应由后续 Auth UC 引入；不得为了预判未来而提前加入 v1 必填字段。

## UC-AUTH-002 后续写侧

### Principal provision 与状态迁移

UC-AUTH-002 只读取 `auth_principals`。普通用户由 UC006 创建，邮箱注册见已接受的 UC011。
Developer 申请与开通审计见 [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md) 已接受，首版采用满足邮箱前置条件后自助开通；
人工审批、拒绝后重申、暂停和恢复仍需独立用例。生产不能通过直接修改 MongoDB 替代这些行为。

Developer 是 USER principal 的可选属性。普通用户的 `developerStatus` 为 null；只有申请
进入 Developer 生命周期后才取 `PENDING/APPROVED/REJECTED/SUSPENDED`。主体建立与
Developer 申请不能被合并成同一个隐式动作。

### 普通 USER provision 与 Auth 用户身份签发

SYSTEM principal provision 已由 UC-AUTH-003 闭合，PLATFORM_ADMIN bootstrap 与 Reviewer
grant/revoke 已由 UC-AUTH-004 决定。其生产入口仍依赖普通 USER 在何时 provision、登录/
session 如何建立，以及 Auth 如何签发 trusted-identity-v1。前两项已有
[UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md) 与
[UC-AUTH-007](use-cases/UC-AUTH-007-login.md) 的 ACCEPTED 设计；Session 与凭据撤销分别由
[UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md) 和
[UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md) 接受。可信身份签发已有 [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md)、Gateway 接入已有 [UC-GW-001](../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 设计；UC-AUTH-010 已 ACCEPTED 并进入实现，UC-GW-001 仍为 PROPOSED。
不能用数据库直改或无认证临时 RPC 代替这些能力。

## 用户资料生产交付

[UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md) 资料编辑规则和配套读取契约已 ACCEPTED。以下事项仍需推进：

- 2026-10-10 已由用户审核接受 [BR-UPF-017](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017) 首批九个实际字段和 UC028 逐字段 scope；活动片区是多选集合，当前年级按 [BR-UPF-018](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018) 的用户确认锚点阶段内推进并封顶。旧学校名称/入学年份示例不是生产字段；测试中的 `basic.name` fixture 即使 key 相同，其临时目录内容也不能代替正式配置。
- 普通 USER 创建时的账号/资料初始化，以及既有主体记录的迁移工作包；本用例不在读取或编辑时静默修复。
- 面向 Auth audience 的用户身份签发、Gateway 受保护路由、登录引导和客户端明确确认上传的交付。
- 字段目录在线管理、停用与演进；当前首版部署装载与稳定性方向见 [BR-UPF-002](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。
- STRING_SET、ACADEMIC_GRADE、字段 options/格式约束、UC029 学年时间表及真实生产目录/Scope 已实现但尚未部署；客户端确认交互和生产启用仍需独立验收。
- 第三方应用访问资料已展开为 [UC-AUTH-028](use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md)：一字段一 scope、用户 consent、固定 `iwut_profile` claim 与在线当前读取；敏感字段分级/二次确认继续后移。ApplicationUserStorage 已建立为 [UC-AUTH-030](use-cases/UC-AUTH-030-manage-application-user-storage.md) ACCEPTED，与 Profile 完全分离。

### ApplicationUserStorage（UC-AUTH-030）

2026-10-10 已审核接受并完成 Auth/API 后端：按 `(authId, applicationId, channel)` 隔离，使用固定有界 string KV、`storage.read/write` 与 `iwut-auth-center` audience；撤权后保留且重授权恢复访问，用户清空整个 Application 的三个 channel。第三方只开放 Auth 直接消费 opaque Bearer token 的 HTTP 入口；PUBLIC CORS 按当前 callback origin，普通 mutation 不另建逐次审计。Application 关闭复用 UC026 Apply/Get，首次 Apply 与 tombstone/审计同事务建立唯一存储清理任务。Gateway 路由、用户/第三方客户端界面和生产开关仍是交付项，但不再是开放产品问题。

### 学年切换规则在线管理（2026-10-10）

用户提出 `AUTH_ACADEMIC_CALENDAR_FILE` 不应继续是只能由部署修改的权威输入，系统管理员应能修改学年切换设置，缺省为每年 9 月 1 日。[UC-AUTH-029](use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 已 ACCEPTED：读取返回当前学年和下一次更新时间；设置提交带年份且严格晚于当前服务端时间的下一次 Instant，到点后按 `Asia/Shanghai` 公历逐次增加一年。2 月 29 日的下一次为次年 3 月 1 日并从此继续逐年推进。

UC005/028 和配套查询契约随接受同步修订，并生成 UC029 brief 后实施。代码不再读取 `AUTH_ACADEMIC_CALENDAR_FILE`，但外部环境残留同名变量不构成启动错误。


## 创建、登录与撤销的实现交付

UC007/008 保持 ACCEPTED；UC006/011/031 v3、UC009 防旁路及 UC032 后端完成。设备 LOGIN/Session 字节保留；无密码邮箱 v2 已从公开运行时退役，学号关联亦退役。UC033/034 串行交付与验收见 readiness；客户端/Gateway 独立验收，不以旧向量和后端通过替代新需求。

- 后端真实验证器、共享测试向量、生成 Proto、原生 gRPC、方法级 middleware 与生产组合根；不得以 fake verifier 代替认证。
- Mongo 原子注册、登录/撤销栅栏、会话一致检查、10 会话 LRU 及真实副本集故障测试，按 UC006–009 验收。
- 学生关联输入、快照、组/成员写入、配置与启动前离线迁移按 BR-REG-004/008 退役；系统未部署，不新增生产历史迁移。邮件/JWS 密钥更新及注销终止清单恢复保留各自门禁。
- Session 的 AUTH_SESSION_TTL 必填配置、认证入口有界默认参数与非法配置拒绝启动，见 [BR-LGN-004](use-cases/UC-AUTH-007-login.md#br-lgn-004) 和 [BR-LGN-009](use-cases/UC-AUTH-007-login.md#br-lgn-009)；部署调优不改变固定会话及 LRU 语义。
- Android/iOS 安全存储、客户端兼容矩阵、邮箱注册/登录界面、签名前检查、自动登录和可靠删除独立验收，组合建议见[客户端生命周期](client-guides/authentication-lifecycle.md)。
- Gateway 路由与 Session 到用户身份 JWS 签发已在 UC-GW-001/UC-AUTH-010 分别跟踪。UC010 已接受；现有后端通过不表示 UC005 公网调用链已贯通。

## 后续认证能力

- 关联密钥轮换与 k8s 在线迁移候选已经退役；其它认证密钥维护按各自用途，不重新引入学校关联。
- Auth 基于有效 Session 签发目标服务身份、Gateway 鉴权 RPC/路由与秘密转发边界，跟踪已接受的 UC-AUTH-010 与 UC-GW-001 草案；首版不引入 Redis 或身份缓存，OAuth2 单独设计。
- 邮箱设置/注册见 [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md)，已有账号邮箱登录及本机设备授权见 [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md)，Developer 自助申请见 [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md)，UC011 已 ACCEPTED，其独立协议与向量已闭合；UC012 的专用签名、向量和接口也已闭合并 ACCEPTED，后端已基于 UC011 完成集成并合回 auth-center/v1，仍需交付 Gateway/客户端；UC013 已 ACCEPTED，后端依赖已满足，协议与默认关闭的恢复就绪声明已固定，进入实现流程。公网资格开通仍等待邮箱恢复链路实际交付，不能仅以后端实现完成视为产品可用。
- 凭据列表/命名/移除已展开为 UC032 ACCEPTED；旧设备明确授权新增凭据仍后移。Session 列表与回收已有 UC020，账号禁用/恢复和注销已有 UC022/025，当前交付现状以 implements 为准。当前 token 的 Session 撤销由 [UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md) 定义，当前 Session 凭据撤销由 [UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md) 定义，撤销其他凭据由 UC032 定义，客户端退出组合见[生命周期建议](client-guides/authentication-lifecycle.md)。
- 应用专属学生关联标识取消，对外仍用 pairwise sub；当前学校绑定认证披露由修订中的 UC031 定义，不等于学生权限或自然人标识。

## OAuth 身份与授权分组已明确

sector 与 sub 由 Auth 按 Application 保存，不由 App 保存；渠道/type/major 共用该身份分组。client/credential 和用户授权按渠道隔离，major 共用历史授权，版本变化不自动删减历史同意。具体规则与标准 sector URI 见 [OAuth/OIDC v1](../platform/contracts/oauth-oidc-v1.md)，当前仍待整体用例接受与实现。

## 应用审核权限扩展（2026-10-03）

UC004 已接受管理 app.profile.review 与 app.version.review 两项独立权限，UC010 同步扩充 App audience 投影，沿用 auth.reviewer.manage 作为管理入口权限。设计见 [UC004](use-cases/UC-AUTH-004-manage-reviewer-permission.md)；新增 Auth/API/Gateway 实现及真实 App 回归已完成，证据见 [实现记录](implements/README.md#2026-10-03-uc004010-应用审核权限扩展)。TEST/OAuth 的权限授予与签发依赖已闭合；OAuth 自身仍按独立工作包交付，生产环境仍需显式授予相关人员权限。

2026-10-05：UC021–025 已接受并生成 brief，独立 subagent 工作包开始实施；App UC025 提供归属屏障/个人清理前置能力。有应用者继续 BLOCKED，应用转让/关闭不在本轮，公网部署与无密钥受理需独立验收。
