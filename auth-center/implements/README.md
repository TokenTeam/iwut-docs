# Auth Center 实现入口

状态：`ACTIVE`

## 当前实现覆盖

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-AUTH-001](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | `ACCEPTED` | `IN_PROGRESS` | 独立 API Proto 与生成代码、Domain/Port/UseCase、临时硬编码 catalog adapter、Kratos 原生 gRPC transport、goforj/wire Composition Root、service JWS/固定 allowlist、未认证 provider E2E、真实 App+Auth 双服务 E2E | MongoDB 权威目录 |
| [UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | `ACCEPTED` | `COMPLETE` | 权威设计、共享契约、独立 API Proto 与生成代码、Domain/Port/UseCase、MongoDB Repository 与唯一索引、Kratos 原生 gRPC Transport、service JWS/固定 allowlist、真实 MongoDB provider E2E、App Center consumer adapter、真实 App+Auth 双服务 E2E | — |
| [UC-AUTH-003](../use-cases/UC-AUTH-003-resolve-system-principal.md) | `ACCEPTED` | `COMPLETE` | 独立 API Proto、启动时幂等 Mongo provision、purpose partial unique index、Domain/Port/UseCase、受 service identity 与 purpose allowlist 保护的原生 gRPC、App Center 延迟解析与成功缓存、provider E2E | — |
| [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) | `ACCEPTED` | `COMPLETE` | Reviewer 授予/撤销与状态查询、HTTP/gRPC、当前管理员权限复核、权限 revision CAS、原子不可变审计、全局一次性 bootstrap、防复活标记、与 UC010 共用事务栅栏、Gateway SESSION 三协议联调 | —（生产管理员初始化与公网部署由运维执行） |
| [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) | `ACCEPTED` | `CORE_COMPLETE` | 独立 Proto、配置字段目录、Domain/Port/UseCase、Mongo 内嵌资料 CAS、严格 oneof 解码、可信用户 JWS、HTTP/JSON 与原生 gRPC、生产 Wire 与真实 Mongo E2E；注册初始化空资料 | 生产实际字段清单、既有 USER 数据迁移、Gateway 接入与客户端确认交互 |
| [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实 P-256 验证、必填关联声明、独立 Proto、原子注册、关联认证加密/HMAC、启动前离线轮换与幂等重跑、全量核验、限额、生产 Wire/Mongo/HTTP/gRPC E2E | 正式事务部署上的维护窗口验收；客户端、Gateway 独立交付 |
| [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) | `ACCEPTED` | `CORE_COMPLETE` | 真实设备登录、严格编码、Session 在线检查、固定寿命配置、10 会话精确 LRU、有界限流、事务栅栏、HTTP/gRPC/生产 Wire/Mongo 并发与故障测试 | Gateway 的 Session-to-JWS 编排与客户端接入；物理清理暂以保留记录处理 |
| [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) | `ACCEPTED` | `COMPLETE` | token 定向幂等撤销、专用载体、精确鉴权例外、首次 revokedAt、保守保留记录、真实 Mongo 故障/未知提交测试与生产 HTTP/gRPC E2E | —（Gateway 与客户端退出编排独立交付） |
| [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) | `ACCEPTED` | `COMPLETE` | 有效 Session 授权及事务内复核、本人目标隔离、首次撤销记录、公钥归属保留、引用 Session 即时拒绝、并发登录/撤销及生产 HTTP/gRPC E2E | —（客户端编排独立交付） |
| [UC-AUTH-010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) | `ACCEPTED` | `CORE_COMPLETE` | 固定 identity RPC、双重认证、独立 RSA signer、audience 能力投影、Mongo 当前状态事务确认及无缓存、caller audience 配置、生产 Wire/gRPC/Mongo 测试、实际 App verifier 兼容验证 | Gateway 联合入口验收（UC-GW-001 独立交付） |
| [UC-AUTH-011](../use-cases/UC-AUTH-011-set-and-activate-email.md) | `ACCEPTED` | `COMPLETE` | Auth e6711d9/API 39122c2；原子邮箱注册/绑定、严格 Session presence、持久化额度、TLS SMTP、轮换/幂等、真实 Mongo/Wire/HTTP/gRPC 验收 | Gateway 与客户端独立交付，生产配置未启用 |
| [UC-AUTH-012](../use-cases/UC-AUTH-012-login-with-email.md) | `ACCEPTED` | `COMPLETE` | 已基于 UC011 rebase；代码 9ee4d4b、运行说明 58f8a67/API 46544d1；邮箱登录/设备授权、共享额度/SMTP、全部 Session 消费路径和真实集成验收 | 已快进合入 auth-center/v1；Gateway 与客户端独立交付 |
| [UC-AUTH-013](../use-cases/UC-AUTH-013-apply-for-developer.md) | `PROPOSED` | `NOT_STARTED` | 邮箱门禁、自助开通与本人资格查询草案 | UC011/012 恢复能力、设计接受、Proto/路由、资格与审计原子提交及 App Center 联合验收 |

## 实现边界

- 不在旧 Auth Center 代码中直接追加一个临时 JSON 接口。
- 不把 App Center 测试 fixture、cache 或硬编码 Scope 列表提升为 Auth 权威数据。
- 当前 `internal/adapter/catalog` 硬编码实现只用于启动纵切和 E2E；它不是 BR-SCP-001 所指的生产权威目录，必须由 Auth 自有 MongoDB adapter 替换。
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
