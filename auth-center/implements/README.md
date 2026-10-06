# Auth Center 实现入口

状态：`ACTIVE`

## 当前实现覆盖

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | `ACCEPTED` | `COMPLETE` | 独立 API、Domain/Port/UseCase、原生 gRPC、service JWS；显式 OAuth manifest 下使用 Mongo 权威目录、完整快照 revision、幂等启动装载、enabled/requestable 投影，与 OAuth 共用同一目录 | 未配置 manifest 的旧开发模式仍使用临时硬编码目录；线上目录编辑后台不在本 UC 范围 |
| [UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | `ACCEPTED` | `COMPLETE` | 权威设计、共享契约、独立 API Proto 与生成代码、Domain/Port/UseCase、MongoDB Repository 与唯一索引、Kratos 原生 gRPC Transport、service JWS/固定 allowlist、真实 MongoDB provider E2E、App Center consumer adapter、真实 App+Auth 双服务 E2E | — |
| [UC-AUTH-003](../use-cases/UC-AUTH-003-resolve-system-principal.md) | `ACCEPTED` | `COMPLETE` | 独立 API Proto、启动时幂等 Mongo provision、purpose partial unique index、Domain/Port/UseCase、受 service identity 与 purpose allowlist 保护的原生 gRPC、App Center 延迟解析与成功缓存、provider E2E | — |
| [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) | `ACCEPTED` | `COMPLETE` | 两项独立审核权限的授予/撤销与组合查询、旧 API 版本权限语义兼容、HTTP/gRPC、当前管理员复核、共享 revision CAS、原子不可变审计、全局一次性 bootstrap、UC010 事务协调、真实 App 双审核权限隔离与 Gateway SESSION 三协议验收 | 未部署到生产；不自动授予历史用户 profile 权限 |
| [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) | `ACCEPTED` | `CORE_COMPLETE` | 独立 Proto、配置字段目录、Domain/Port/UseCase、Mongo 内嵌资料 CAS、严格 oneof 解码、可信用户 JWS、HTTP/JSON 与原生 gRPC、生产 Wire 与真实 Mongo E2E；注册初始化空资料 | 生产实际字段清单、既有 USER 数据迁移、Gateway 接入与客户端确认交互 |
| [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实 P-256 验证、必填关联声明、独立 Proto、原子注册、关联认证加密/HMAC、启动前离线轮换与幂等重跑、全量核验、限额、生产 Wire/Mongo/HTTP/gRPC E2E | 正式事务部署上的维护窗口验收；客户端、Gateway 独立交付 |
| [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实设备登录、严格编码、Session 在线检查、固定寿命配置、10 会话精确 LRU、有界限流、事务栅栏、HTTP/gRPC/生产 Wire/Mongo 并发与故障测试 | Gateway 的 Session-to-JWS 编排与客户端接入；物理清理暂以保留记录处理 |
| [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) | `ACCEPTED` | `COMPLETE` | token 定向幂等撤销、专用载体、精确鉴权例外、首次 revokedAt、保守保留记录、真实 Mongo 故障/未知提交测试与生产 HTTP/gRPC E2E | —（Gateway 与客户端退出编排独立交付） |
| [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) | `ACCEPTED` | `COMPLETE` | 有效 Session 授权及事务内复核、本人目标隔离、首次撤销记录、公钥归属保留、引用 Session 即时拒绝、并发登录/撤销及生产 HTTP/gRPC E2E | —（客户端编排独立交付） |
| [UC-AUTH-010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) | `ACCEPTED` | `CORE_COMPLETE` | 固定 identity RPC、双重认证、独立 RSA signer、audience 最小投影（含两项审核权限）、Mongo 当前状态事务确认及无缓存、caller audience 配置、生产 Wire/gRPC/Mongo、真实 App verifier/双审核入口与 Gateway SESSION 验收 | 新增业务路由和生产部署继续独立验收 |
| [UC-AUTH-011](../use-cases/UC-AUTH-011-set-and-activate-email.md) | `ACCEPTED` | `COMPLETE` | Auth e6711d9/API 39122c2；原子邮箱注册/绑定、严格 Session presence、持久化额度、TLS SMTP、轮换/幂等、真实 Mongo/Wire/HTTP/gRPC 验收 | Gateway 与客户端独立交付，生产配置未启用 |
| [UC-AUTH-012](../use-cases/UC-AUTH-012-login-with-email.md) | `ACCEPTED` | `COMPLETE` | 已基于 UC011 rebase；代码 9ee4d4b、运行说明 58f8a67/API 46544d1；邮箱登录/设备授权、共享额度/SMTP、全部 Session 消费路径和真实集成验收 | 已快进合入 auth-center/v1；Gateway 与客户端独立交付 |
| [UC-AUTH-013](../use-cases/UC-AUTH-013-apply-for-developer.md) | `ACCEPTED` | `COMPLETE` | Auth 3587ba7/API b7d9b6c；Session 申请/查询、邮箱恢复门禁、有界限流、原子资格/审计；developerHandle 全局唯一占用、禁止改名/转让/释放、历史 APPROVED 首次补设、审计索引升级、Mongo 并发/损坏数据/迁移与实际 App 联调验收 | Gateway 与客户端独立交付，生产入口及恢复就绪声明默认关闭 |
| [UC-AUTH-020](../use-cases/UC-AUTH-020-manage-own-sessions.md) | `ACCEPTED` | `COMPLETE` | 同账号有效 Session 分页、明确集合原子回收、幂等审计；HTTP/gRPC、真实 Mongo 与 Wire 验证通过 | 默认关闭；Gateway DIRECT 路由及客户端 Session 管理界面独立交付 |
| [UC-AUTH-021](../use-cases/UC-AUTH-021-manage-platform-administrators.md) | `ACCEPTED` | `COMPLETE` | Auth ea13341（UC022 集成 ccee202）、API 0b36b6c；固定四项管理权限、邮箱恢复门禁、HTTP/gRPC 查询/授撤、共享权限 CAS、最后管理员保护、原子审计、一次性 bootstrap；真实 Mongo/Wire/邮件激活与撤权测试 | 公网开关默认关闭；生产应急恢复规程、Gateway 与客户端独立交付；UC025 已实现 bootstrap 审计到期原子收据，生产恢复仍需演练 |
| [UC-AUTH-022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md) | `ACCEPTED` | `COMPLETE` | Auth ccee202/API d5e170b；账号状态 HTTP/gRPC、accountRevision、最后管理员保护、原子审计，设备/邮箱/Session/LRU/OAuth/JWS/Profile 最终写入均校验版本；禁用后恢复不复活旧认证材料，真实 Mongo/Wire 验收 | 已接入禁用时原子取消未决退出；App audience 短期离线窗口及 Gateway/客户端独立交付 |
| [UC-AUTH-023](../use-cases/UC-AUTH-023-suspend-and-restore-developer.md) | `ACCEPTED` | `COMPLETE` | Auth 08fa346/API e4c01b3；独立资格治理 HTTP/gRPC、developerRevision、邮箱恢复门禁、原子审计、取消未决退出；普通登录保留，真实 Mongo/Wire、App 与 OAuth 状态消费验收 | 入口默认关闭；Gateway、客户端与生产治理规程独立交付 |
| [UC-AUTH-024](../use-cases/UC-AUTH-024-withdraw-developer.md) | `ACCEPTED` | `COMPLETE` | Auth ab60f32/API 5144c8c；本人 Session 准备/确认/取消/查询、WITHDRAWN、永久 handle、独立 App provider、持久协调及回执丢失恢复；真实 Auth＋App 验收 | 公网默认关闭；名下应用转让/关闭仍为独立 UC，存在归属时明确阻止退出；Gateway/客户端独立交付 |
| [UC-AUTH-025](../use-cases/UC-AUTH-025-close-own-account.md) | `ACCEPTED` | `COMPLETE` | Auth 95a3c3a/API 4babe5b；ACTIVE/DISABLED 专用设备证明、明确确认、CLOSED、永久占用、独立终止清单与离线恢复、分批清理及保留期、App 回执；真实 Mongo/HTTP/gRPC/双服务与恢复测试 | 公网默认关闭；生产数据清单、30 天备份/日志期限、独立清单恢复演练和无密钥受理仍是启用门禁，Gateway/客户端独立交付 |
| [UC-AUTH-026](../use-cases/UC-AUTH-026-apply-application-closure.md) | `ACCEPTED` | `COMPLETE` | 永久 application tombstone/receipt、UC014–019 最终 gate、同 Session/设备 challenge32 P-256 reauth、5 分钟 app.close proof、Mongo/transport/config/Wire 与真实 App UC027 proof/Apply/Get/故障恢复联调；服务 `5d26cb3`、权限修复 `4f661e4`、API `1ba1b81` | 生产/Gateway 入口默认关闭；网络帧级丢包和双边进程重启演练独立交付 |
| [UC-AUTH-027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md) | `PROPOSED` | `NOT_STARTED` | suspend/restore 两项独立权限、平台管理员授权但不自动获得操作权、共享权限版本和 App audience 投影提案 | 接受前需与 App Center 的平台暂停/恢复状态机、门禁和审计设计对齐；尚未生成 brief |

## 实现边界

- 不在旧 Auth Center 代码中直接追加一个临时 JSON 接口。
- 不把 App Center 测试 fixture、cache 或硬编码 Scope 列表提升为 Auth 权威数据。
- 显式 OAuth manifest 启动路径已绑定 Auth 自有 MongoDB Catalog；`internal/adapter/catalog` 仅保留为未配置 manifest 时的开发兼容路径，不能作为生产权威目录。
- Provider E2E 使用生产 Composition Root、真实 Kratos gRPC listener 和生成 client，不使用进程内假 Server。
- UC-AUTH-002 使用 Auth 自有 MongoDB `auth_principals` repository；测试 fixture 只能
  建立输入记录，不能替代生产 repository。
- 内部服务调用 transport 统一使用 trusted-service-identity-v1；未知 RPC、permission 或 purpose 默认拒绝。UC-AUTH-004/005 的用户入口按各自用例使用 trusted-identity-v1。
- UC-AUTH-006/007 的 Begin/Complete 是有界匿名认证入口，使用挑战证明，不以已有用户 JWS 作为前提；UC-AUTH-008 只有 token 定向撤销可以不经过普通有效 Session middleware，UC-AUTH-009 必须使用有效用户 Session。仅允许显式登记的方法，不扩大其他用户能力的匿名访问面。

## 2026-09-22 后端集成记录

- 五个工作包在独立 worktree 实现，按完成顺序 `005 → 007 → 006 → 008 → 009`
  rebase 后快进合入 `worktrees/iwut-auth-center-ddd` 的 `auth-center/v1`，没有 push。
- 独立 API 分支 `auth-scope-catalog/v1` 包含 authentication 与 user_profile 的 Proto
  和生成代码；Auth 集成提交 `565c58d` 固定 API 提交 `439942a`。协议与公开测试向量见
  [设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)。
- 生产 Wire 统一注册按完整方法名分派的鉴权：设备证明、token 定向撤销、有效 Session、
  trusted-user JWS、内部 service JWS。新增用户入口默认关闭，显式设置
  `AUTH_USER_ENDPOINTS_ENABLED=true` 并满足部署配置才启用。启动前完成事务探测、
  索引和关联密文核验/迁移；失败不监听。具体环境变量见实现仓库 README。
- 验证包括 `make check`、真实 MongoDB 单成员副本集上的全包 `-race`，以及生产 Wire
  端到端注册、资料编辑、登录、两类撤销、停机轮换和仅当前密钥重启后的关联复用。
  本地运行不代替正式服务器的停机维护窗口验收。
- `COMPLETE` 指对应后端工作包，不表示外部客户端已经可用。已有 USER fixture/历史记录
  没有被静默补全资料；生产资料字段清单未自行确定。撤销和完成记录暂时保守保留，
  后续物理清理必须另行确定审计窗口且不能释放凭据公钥唯一归属。

## 2026-09-23 HTTP 接入

UC005–009 的九个用户方法增加 Proto HTTP annotation 与生成客户端；生产 Wire 同时启动
HTTP/gRPC，复用相同服务与鉴权分派。HTTP 额外验证标准 ProtoJSON、请求体上限及错误状态映射，
Session 撤销与来源限流支持 HTTP transport。路由绑定见 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md)。
内部服务查询及 UC010 签发仍仅通过 gRPC 提供，Gateway 路由独立交付。

UC010 后端实现提交为 `592eca6`，接口命名修正为 `834a801`，对应 API `fb68445`。
实际 App verifier 在有效时间内接受普通/有能力的 App audience token，并拒绝 Auth audience；
此前临时 fixture 的失败由过期引起，未修改生产验签逻辑。HTTP 接入不改变其内部 gRPC 边界。

HTTP 集成提交：Auth `afe227a`，API `5a6d439`。`make check`、`make test-race`、
`make test-mongo` 及真实 MongoDB 上的全包 `-race` 均通过；测试容器已清理，提交未 push。

## 性能测量记录

- [UC010 本地性能测量（2026-09-23）](benchmarks/uc010-local-20260923.md)：实现验证记录，包含环境、复现命令和结果，不作为生产容量保证。测试与测量代码保留在 Auth 实现仓库。

## 2026-09-24 Reviewer 管理

UC004 brief 通过 `tools/gen_brief.py UC-AUTH-004` 生成，保留 `ACCEPTED` 设计状态。
Auth 实现 `5c5e11b`、独立 API `3912b55`、Gateway 集成 `7ac853a` 均已本地提交。

- 新增配套查询及 GRANT/REVOKE 管理接口，Gateway 以 SESSION 换取 Auth audience JWS；
  Auth 验签并要求 `auth.reviewer.manage`，事务内复核当前 ACTIVE USER 管理员权限。
- 权限与审计原子提交，保留其它权限，使用全局认证事务栅栏与 UC010 签发协调。
  重复动作和 stale revision 冲突；未知提交不返回成功。
- `auth-center bootstrap-platform-admin --auth-id <existing-user-auth-id>` 仅使用 Mongo 配置，
  不监听端口，不隐式授予 Reviewer。持久化全局标记保证重跑不能恢复后来撤销的管理权限。
- Auth 的 `make check`、`make test-race`、`make test-mongo` 通过；覆盖真实 Wire/Mongo/JWS、
  审计失败回滚、提交结果未知、并发 CAS、撤销与签发串行化、bootstrap 防复活。
- Gateway 的 `make check` 与真实 Traefik/Auth/Mongo 协议验收通过，覆盖 HTTP grant、原生 gRPC revoke、
  gRPC-Web query、普通用户拒绝及版本冲突。通过真实 CLI 初始化测试管理员，不以数据库直改替代用例。

## 2026-09-25 邮箱注册与绑定

UC011 已接受，协议与公开测试向量、脚本生成 brief 位于 docs 提交 `ef310c0`。
`implement_uc011` subagent 已在 `worktrees/iwut-auth-center-ddd` 的 `auth-center/v1`
及其独立 API 仓库开始实现；API/后端实现与测试结果仍待交付，不提前标为完成。

工作包包括 REGISTER/BIND、精确可选 Session 鉴权、原子注册与绑定、真实 TLS SMTP、
有界持久化发送额度、邮件 HMAC 与关联密钥冷更新清理，以及生产 Wire/Mongo/HTTP/gRPC 验收。
客户端、Gateway 和 UC012/013 保持独立交付。

## 2026-09-25 邮箱登录

UC012 契约、公开向量和脚本生成 brief 已在 `c63af0c` 接受。`implement_uc012`
subagent 已在隔离 worktree `worktrees/iwut-auth-center-uc012`（Auth 分支 `auth-center/uc012`，
独立 API 分支 `auth-email-login/v1`）开始协议、API、领域层及测试工作。

UC011 的 API 基线为 `39122c2`，后端仍在实现。UC012 完整集成必须等待其稳定 Auth/API 提交，
随后 rebase 并复用邮箱目录、共享额度、SMTP 和认证事务；不能以重复邮箱目录或 fixture 代替依赖。
两位 subagent 通过消息交接，不在同一 worktree 并发修改。完整 Mongo/Wire/SMTP/HTTP/gRPC 验收待交付，
未提前标记完成；UC013、客户端与 Gateway 仍独立跟踪。

## 2026-09-25 实现完成核对

此前“实现中/等待 UC011”的记录是当时的进度；当前完成情况以本节和顶部表格为准。

- UC011：Auth `e6711d919e85cdf2b28393eaa4c3e42b20a3776a` 已在 `auth-center/v1`，
  固定独立 API `39122c2d03aafd151aeb808789cb19fe7e5a87c4`。
- UC012：已 rebase UC011，代码提交为 `ac8765f`、`9ee4d4b37f5ec198321e8b288ce3d2e0ecf27d24`，
  固定独立 API `46544d1912e002ceb7d218e326bacc64874caf67`。
  后续 `58f8a67` 仅补充 README/工作包说明。本次核对时该分支尚未合回；随后合入记录见下节。
- 两个 subagent 均报告 `make check`、`make test-race`、完整 `make test-mongo` 通过，
  另有真实 Mongo/Wire/TLS SMTP 的针对性 race 验收及三套协议向量检查。测试资源已清理，无真实用户邮件。
- 本次核对确认提交、API 指针、祖先关系、干净工作区及对应测试代码；未重复运行已通过的代码门禁。
  UC008 对未知认证方法/损坏来源记录失败关闭，保持正常未知/过期/已撤销 token 的幂等撤销。
- 本页 COMPLETE 仍指 Auth/API 后端工作包。Gateway 尚未加入邮箱路由，客户端、公网与生产邮件配置独立验收。
  UC013 仍为 PROPOSED/NOT_STARTED；不能将后端实现完成解释为开发者申请已开放。

## 2026-09-25 UC012 合入后验证

UC012 已在完成 rebase 的基础上快进合入 `worktrees/iwut-auth-center-ddd` 的 `auth-center/v1`。
当前 Auth HEAD 为 `58f8a67c945705e390eb3378fc634df9ea8f1dda`，API 工作树与提交指针均为
`46544d1912e002ceb7d218e326bacc64874caf67`；没有合并冲突或额外实现改动。

在合入后的主实现工作树重新运行并全部通过：

- `make check`：格式、构建、单元/契约测试、vet、Wire 和 Proto 生成一致性。
- `make test-race`：race 检查通过。
- `MONGODB_INTEGRATION_PORT=27047 make test-mongo`：真实 MongoDB 副本集全包验收，
  包含生产 Wire HTTP/gRPC 和可控 TLS SMTP；Mongo 包约 75 秒。
- 旧设备、邮箱注册与邮箱登录三套公开协议向量检查。

测试容器已由脚本退出清理；Auth/API 工作树干净，所有提交仍仅本地保存，未推送。
Gateway 邮箱路由及客户端/生产配置交付不包含在此次合入和测试内。

## 2026-09-26 UC013 接受与工作树清理

UC012 的 Auth/API worktree 与主实现的提交完全一致且无未保存改动；已先移除独立 API worktree，再删除 `worktrees/iwut-auth-center-uc012`。保留本地分支与提交记录，没有推送。

UC013 后端依赖已由 UC011/012 合入及测试闭合。现已接受自助开通设计，固定两个有效 Session 接口、字段 presence、部署恢复就绪声明及验收边界，并用脚本生成 [brief](../briefs/UC-AUTH-013.md)。实现状态单独跟踪，不把设计接受或后端测试视为公网入口已开放。

`implement_uc013` 已确认开始，在 `worktrees/iwut-auth-center-ddd` 的 `auth-center/v1` 及嵌套独立 API 仓库实现；设计/brief 提交为 `c254d9f`。工作包要求 check、race、真实 Mongo/Wire/HTTP/gRPC 和实际 App Center 联合验收。当前为 IN_PROGRESS，尚无本用例完成或测试通过的声明；父代理不轮询工作日志。

## 2026-09-26 UC013 完成交付核对

UC013 已由 implement_uc013 完成，直接提交在 auth-center/v1，Auth 提交
`68046e7842a0ccdfbc48e707edbf97c8b1286fa3`，固定 API
`9bcddc3bfc3383cce6d21bcb2ed6aca3ff94d521`。此前 IN_PROGRESS 是历史进度。

代理报告通过 make check、make test-race、MONGODB_INTEGRATION_PORT=27048 make test-mongo
及三套协议向量检查；实际 App Center 生产服务接受开通后的新 JWS 创建应用，配额与 Reviewer
限制仍生效。测试资源已清理，无推送。本次核对确认主分支提交、API 指针、实现及测试代码，
未重复运行已报告通过的完整测试。生产入口和邮箱恢复就绪声明默认关闭。

当前全部十三项 UC 已接受，但 UC001 仍使用硬编码 Scope Catalog，MongoDB 权威目录尚未交付；
UC005/006/007/010 的核心实现及产品/部署边界继续按顶部表格分别跟踪，不能把 UC013 完成解释为全部生产交付完成。

## 2026-09-26 UC013 开发者 ID 修正

用户要求为 Developer 增加自取公开 ID。UC013 保持 ACCEPTED，增加 BR-DEV-011/012 及共享协议字段，重新生成 brief；实现从原 COMPLETE 回到 IN_PROGRESS。修正基线为 Auth 68046e7/API 9bcddc3，要求原子唯一占用、同名幂等、禁止改名及历史 APPROVED 一次补设，不改变 App UUID、adminId 或 JWS，也不在此交付公开名称路由。

`implement_uc013` 已确认恢复工作，按文档提交 `68f4626` 在原 Auth/API 分支修正。要求完成 check、race、真实 Mongo 并发/故障/索引升级、生产 HTTP/gRPC 与实际 App 回归；新增 handle 能力尚未声明实现完成。

## 2026-10-03 UC013 开发者 ID 完成状态补记

前节 IN_PROGRESS 是修正开始时的历史记录。developerHandle 修正已由 Auth
`3587ba78496bd46d2d6cb76ac64bfb28d579b8d2` 完成，固定 API
`b7d9b6c8c860cc9d813f97023016c8e83ccebbea`；该提交是本次核对时 Auth HEAD
`be75692` 的祖先。顶部状态现补正为 COMPLETE，属于文档漏记，没有新增实现工作。

核对代码与测试确认：全局唯一归属、已有名称不可修改/转让/释放、历史 APPROVED 首次补设、
审计复合唯一索引升级，以及并发竞争、损坏归属、迁移冲突/回滚和实际 App 联调均已覆盖。
本轮 OAuth 的全量 Mongo 回归也已覆盖这些既有测试；此次仅修正文档，不重复运行后端测试。
后端完成仍不表示客户端、Gateway 或生产入口已交付。

## OAuth / OIDC 后续工作包

App019 已交付；以下设计已接受，Auth 后端已按 UC014→019 顺序实现。验收与上线边界见下方本轮交付记录。

| Use Case | 设计状态 | 实现状态 | 主要交付 |
| --- | --- | --- | --- |
| [UC-AUTH-014](../use-cases/UC-AUTH-014-authorize-application.md) | `ACCEPTED` | `CORE_COMPLETE` | 用户确认应用授权并签发授权码 |
| [UC-AUTH-015](../use-cases/UC-AUTH-015-exchange-authorization-code.md) | `ACCEPTED` | `COMPLETE` | 兑换授权码并签发 OIDC 凭据 |
| [UC-AUTH-016](../use-cases/UC-AUTH-016-refresh-application-tokens.md) | `ACCEPTED` | `COMPLETE` | 刷新应用访问凭据 |
| [UC-AUTH-017](../use-cases/UC-AUTH-017-get-oidc-user-info.md) | `ACCEPTED` | `COMPLETE` | 读取 OIDC 用户信息 |
| [UC-AUTH-018](../use-cases/UC-AUTH-018-revoke-application-authorization.md) | `ACCEPTED` | `COMPLETE` | 查看及收回本人应用授权 |
| [UC-AUTH-019](../use-cases/UC-AUTH-019-issue-delegation-context.md) | `ACCEPTED` | `CORE_COMPLETE` | 校验应用访问凭据并签发可信委托上下文 |

## 2026-09-28 Scope 单状态设计同步

已确定 UC001/BR-SCP-004 的 enabled 单状态与 requestable 兼容投影，并同步 OAuth UC 的运行校验与恢复规则。仅修改设计；当前临时硬编码 provider 不因此成为生产目录。后续生产目录工作包需交付 enabled 持久化/装载、revision 一致快照及投影测试，OAuth 工作包需验证停用、恢复、旧 App 缓存和目录故障场景。App 的既有 Proto 字段与已完成 UC-APP-018 无需为此变更；版本审核/发布继续按现有 requestable 消费方式校验。

## 2026-10-03 UC004/010 应用审核权限扩展

UC004 扩展已完成，设计继续 ACCEPTED。Auth `dc6acb1`（auth-center/v1）固定 API `649fc30`，Gateway `6b3f0d9`（gateway/v1）固定等价 API `758c426`；全部为本地提交，未 push/部署。实现新增单项权限命令、双项一致快照查询、旧接口兼容及 UC010 双权限投影，新旧入口共用集合、revision、审计及事务栅栏，历史用户不自动获得 profile 权限。

验收通过：

- Auth `make check`、`make test-race`、`APP_CENTER_SOURCE_DIR=/tmp/iwut-app-review-fixture make test-mongo`；真实 Mongo 副本集覆盖跨权限并发 CAS、审计回滚、未知提交以及两项撤销与签发竞争。
- 生产 Wire/HTTP/gRPC、生成 HTTP 客户端、无效 permission/严格 JSON/缺失 revision、旧接口撤销保留另一权限、查询不泄露其它能力。
- 跨服务测试使用 App 已提交版本 `f0ffd06` / API `88f182d` 的独立快照，运行真实 App 进程和 verifier；Auth 正常授权并签发后验证零项/profile-only/version-only/两项组合。允许的审核入口对不存在的合法 review ID 返回 404，权限不符返回 403，证明能力门禁独立；不将该检查解释为真实业务审核成功。
- Gateway `make check`、`make protocol-e2e`，经固定 Traefik、真实 Auth/Mongo 测试 HTTP、原生 gRPC 和 gRPC-Web，包含 Session 身份、伪造头清理、路径覆盖、独立授予及新旧 API 混用。

实现同时修复生成查询客户端的 subject 路径绑定，具体 `json_name` 约定见 UC004。App 工作树当时有其它任务进行中的修改，验收未修改该工作树，也不涵盖尚未提交的 OAuth provider 能力。

## 2026-10-03 UC014–019 后端交付

Auth `be75692`（`auth-center/v1`）固定独立 API `d187bee`，在主实现工作树完成；全部仅本地提交，未 push/部署。App019 联调基线为实际 App `657eccd` / API `310fc10`。六个 UC 均保持 ACCEPTED，brief 由脚本生成。

- UC014：真实 App 当前运行配置、Mongo 权威 Catalog、Session 同源门户桥、最小 consent 页面、共享 grant 和一次性 code；同渠道两类 client/各 major 共用历史授权。官方登录页面与公网接入仍独立交付，因此整体为 CORE_COMPLETE。
- UC015：PUBLIC_PKCE/S256、CONFIDENTIAL_SECRET/Basic（可叠加 PKCE），独立 RS256 ID Token、JWKS/discovery、opaque access token、每 Application 稳定 sector/subject 和 Auth 静态注册映射。code 消费、family 与审计原子提交。
- UC016：opaque refresh 单次旋转、重放整 family 撤销，30 天闲置期限/180 天绝对上限；显式 scope 上限与当前有效交集分离，停用恢复不会扩张用户主动缩小的上限。
- UC017：标准 UserInfo 仅返回 pairwise sub 与当前已验证、已授权邮箱；每次读取当前 App、USER、grant 和 Catalog，不复用 ID Token 为资源访问凭据。
- UC018：本人 Session 列表、部分/全部撤销及标准 token revoke；权限撤销推进 epoch，旧凭据不因后续重新同意而恢复。平台 Session 退出与第三方 family 独立。
- UC019：内部原生 gRPC 在线校验、route/caller/audience 策略、受信时钟健康检查、最长 5 秒专用 delegation JWS。Gateway/Traefik 和资源服务验证器未在本轮实现，因此整体为 CORE_COMPLETE。

验收均通过：

- `make check`：格式、构建、单元/契约测试、vet、Wire/Proto 一致性；`make test-race`。
- `MONGODB_INTEGRATION_PORT=27059 make test-mongo`：真实副本集全包回归，Mongo 包约 127 秒；既有设备、邮箱、Developer、审核权限和 Session 流程保持通过。同步更新实际 App 测试调用方注册表，并修正旧邮箱/注册竞争测试对注册领域预期错误的断言。
- `MONGODB_INTEGRATION_PORT=27059 ./scripts/test-mongo-integration.sh -race -run TestOAuth`：真实数据库 OAuth 并发/故障验收及生产 Wire HTTP/gRPC。覆盖 code/refresh 竞争和重放、grant epoch、陈旧 consent、Catalog 停用恢复、App 运行版本变化、事务回滚与未知提交不返回凭据、token 记录归属/撤销状态损坏时拒绝。
- 实际 App 进程通过 API 创建/审核/发布应用与版本、注册两类 OAuth client、加入 TEST；Auth 经真实 App019 provider 完成授权、兑换、刷新、UserInfo、委托和撤销。独立 `coreos/go-oidc` 客户端验证 discovery/JWKS/ID Token；测试额外校验 nonce、audience、issuer、at_hash。
- App URL 校验依赖在隔离测试构建中使用确定性公共 DNS resolver（Go build overlay）；未改 App 源码/系统 DNS。测试 HTTPS issuer 通过专用测试 transport 映射至本机 Auth listener，不替代生产 TLS/Traefik 验收。
- brief 漂移、registry 和 30 项文档工具测试通过。临时 Mongo 容器已清理。

UC001 的生产 Catalog 缺口同时闭合：配置 OAuth manifest 时绑定 Mongo 持久化完整快照，并复用既有 provider RPC；未配置时的硬编码兼容路径仍仅限开发。没有新增在线目录管理后台。

运行配置及接入说明见 [OAuth runtime](../design-notes/oauth-runtime-implementation.md)。`publicEnabled` 默认关闭，启用还需官方登录门户与 Gateway 的明确交付声明。资源 scope/委托还需资源验证器与策略及时钟观测配置。当前仍仅支持已设计的 TEST 渠道；以上 COMPLETE 只指 Auth/API 后端能力，不代表完成公网 OIDC 认证、GREY/STABLE 或资源业务交付。

## 2026-10-04 OAuth 多渠道扩展启动

App UC020/021 已交付，Auth UC014–019 的 TEST-only 实现现在扩展为 TEST/STABLE/GREY。
设计与 brief 已同步：按渠道检查 Tester/当前发布/cohort，跨渠道隔离 grant 和凭据，
共享 Application sector/sub，支持批准回调并集和多渠道 route policy。
当前扩展状态为 IN_PROGRESS；原 TEST 完成记录保留，待真实 App 三渠道联调后补记完成。

## 2026-10-04 OAuth 多渠道扩展完成

本节取代前节的扩展 IN_PROGRESS。先以文档提交 `3b15291` 明确 UC014–019 的三渠道规则并重新生成 brief，随后在 Auth `4f50f6a` 完成实现。API 沿用 `d187bee`，既有枚举和五个 App provider 方法无需变更；旧 TEST Mongo 记录无需迁移。Auth、API 和文档均未 push/部署。

- TEST 保留 ACTIVE Tester episode 校验；STABLE/GREY 必须无 Tester 字段，分别依赖当前正式发布/当前灰度 cohort；拒绝未知渠道及跨渠道 runtime，不自动切换 channel/major。
- grant、code、access/refresh 仍按原渠道隔离；Application sector/sub 跨渠道稳定。批准回调并集接受三渠道，修复同一应用新增正式/灰度发布后 TEST sector 查询被拒绝的问题。
- route policy 可声明三渠道的非空唯一子集，拒绝未知/重复项；摘要算法未变，扩大渠道需要同步 Gateway 策略。
- 发布清空或灰度资格丢失时，UserInfo、refresh、委托签发均拒绝；失败 refresh 不消费、不续期。资格恢复仍须满足原凭据的期限/撤销/权限边界；旧 code 的精确 publication tuple 不随恢复而更新。撤销 TEST grant 不影响同应用 STABLE/GREY grant。

验证通过 `make check`、`make test-race`、`MONGODB_INTEGRATION_PORT=27059 make test-mongo`，以及 OAuth 专项真实 Mongo 验收；完整 Mongo 包约 119 秒，生产 Wire/跨服务测试包约 50 秒。使用实际 App `4dfe8d6` / API `8f7ad35`，通过其管理 API 创建三渠道 client、正式/灰度发布及比例/清空变更，覆盖两类客户端、非 Tester、灰度缩量/恢复、清空/恢复、陈旧 code、同 sub/不同 grant、跨渠道请求和路由拒绝、撤销隔离。仍沿用确定性 DNS 测试依赖，未修改 App 源码/系统 DNS；没有把实际 App provider 替换为测试桩。适配器单元测试另覆盖畸形响应和未知渠道。

全部 40 份 brief 漂移检查、registry 及 30 项文档工具测试通过，临时 Mongo 容器已清理。公网默认关闭不变，官方登录客户端、Gateway/Traefik 和资源服务仍须独立交付与验收；UC014/019 的整体 CORE_COMPLETE 边界不因此改变。

## 2026-10-05 治理工作包后端交付

UC021–025 已 ACCEPTED，brief 由脚本生成，subagent 在独立服务/API worktree 中实施；依次集成到 `auth-center/v1`。最终 Auth `95a3c3a` 固定 API `4babe5b`；配套 App `b346cfa` 固定 API `1d7b87b`。UC025 rebase 到 UC024 后快进合入，重排前后业务文件逐项一致。全部为本地提交，未 push 或修改生产配置。

- UC021/022：完整管理权限、最后有效管理员、一次性 bootstrap、账号版本及全认证消费检查。恢复账号需重新登录，旧 Session/code/access/refresh/JWS 不复活；UC024/025 协调决定与治理变化同事务取消。
- UC023/024：Developer 暂停/恢复保留普通用户能力；本人退出需零 App 归属义务，永久保留 handle。WITHDRAWN 不重新开通；App 屏障、回执重试和未知提交不会重新放开已退出主体。
- UC025：专用近期设备证明支持禁用账号，确认后不可恢复；独立终止事实和永久 key/handle 占用先持久化，再承诺 TERMINATED。清理按 500 条批次重试，App 回执完成才报告 CLEANUP_COMPLETE；30 天令牌到期清理独立于 App 恢复故障，180 天审计清理原子退休 bootstrap 审计。旧备份缺失回执时先隔离待恢复决定，避免通用工作器误取消永久终止。
- 验证通过 Auth `make check`、`make test-race`、最终全量 `make test-mongo`；新增事务/恢复场景另有真实 Mongo race 验证。生产 Wire 的 HTTP/原生 gRPC 与真实 App 流程覆盖普通/禁用账号、令牌用途隔离、旧 Session 拒绝、后台清理、关闭公网后继续恢复，以及缺清单拒绝启动。离线 CLI 使用同一恢复逻辑，不启动监听或依赖 App 签名配置。
- App 最高层 `make check-auth-app` 的 22 项检查均通过，报告 `.artifacts/verification/20261005T121507Z-mf6vlagz/report.json`。总门禁为 `source-changed`，仅 `docs` 发生变化：并行任务新增 Console 设计及 AGENTS 导航，Auth/App/API 来源均未变化；本轮涉及的权威 UC/契约未被并行修改，随后再次核验 brief/registry/文档工具。该固定基线使用 Auth UC024 `ab60f32`，其后以最终 Auth `95a3c3a` 重新执行真实 Auth–App 脚本通过。最终 Auth 自身的联合验收直接启动 App `b346cfa`，覆盖完整注销与回执恢复。

COMPLETE 表示本次后端工作包；Gateway 路由/客户端确认 UI、名下应用转让或关闭、生产数据保留与恢复演练、禁用用户无私钥受理仍按各 UC 的交付边界处理。新增公网入口默认关闭，后台终止清理不能随公网开关关闭而停止。UC020 随后作为独立工作包接受并开始实施，见顶部状态表。


## 2026-10-05 UC020 Session 管理交付

UC020 原为 PROPOSED，本轮接受为 ACCEPTED，并以脚本生成 brief。subagent 完成核心仓储及传输测试，主任务完成 Proto、配置、限流、HTTP/gRPC、生产 Wire 集成及交叉评审修正；分支 rebase 确认后快进合入 `auth-center/v1`。Auth `85fb5e0` 固定 API `72fa554`，本地提交，未 push 或部署。

- `ListOwnSessions` 只列当前 authId 的有效 Session，不跨 association 账号，不刷新 lastUsedAt/有效期。排序及游标基于不可变创建时间和 ID；每页最多处理 200 候选，可返回空页及继续游标，避免历史记录造成无界扫描。
- `RevokeOwnSessions` 只处理明确的 1–50 个目标，包含当前 Session 时整批拒绝。未知、其他账号和已撤销 ID 不泄露状态；实际变化和单条审计同事务，重试不扩大目标，不撤销凭据或 OAuth。新审计纳入 CLOSED 后 180 天清理。
- 两个精确 DIRECT 方法只接受规范 `x-iwut-session`；严格 HTTP/Proto 输入、错误码、no-store 及 Retry-After 对齐。原生 gRPC 的畸形 wire 在 handler 阶段返回约定参数错误，避免 codec 错误被框架改为 INTERNAL；拒绝前执行入口限流。
- `AUTH_SESSION_MANAGEMENT_ENABLED` 默认 false；启用需用户端点。全局/来源/账号分钟配额默认 600/120/30，来源与账号共享 4096 个有界桶。部署说明见 Auth README。
- 验证通过 `make check`、`make test-race`、全量 `MONGODB_INTEGRATION_PORT=37044 make test-mongo`（真实 Mongo 包约 236 秒，生产 Wire/实际 App 包约 111 秒；App `b346cfa`）。新增真实 Mongo race 专项覆盖事务重试、未知提交、审计回滚、回收/LRU 并发、禁用/恢复/CLOSED、邮箱来源、损坏数据和有界分页。真实 HTTP/gRPC 验证同关联不同账号隔离、只读 LRU、当前 Session 拒绝、幂等回收、同凭据重新登录及开关关闭。
- 48 份 brief 漂移检查、registry、Auth 协议向量和 30 项文档工具测试通过。Gateway 实际 DIRECT 清单、三协议联合验收及客户端界面保持独立交付；COMPLETE 指本次 Auth/API 后端工作包。
