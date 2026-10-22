# UC033/034 开工检查：密码生命周期与登录

状态：`ACCEPTED / COMPLETE`（UC033/034 Auth 后端；生产入口默认关闭）

2026-10-13 用户授权开始实现；[UC033](../use-cases/UC-AUTH-033-manage-password-and-recovery.md)、[UC034](../use-cases/UC-AUTH-034-login-with-password.md)与[密码协议](../../platform/contracts/auth-password-v1.md)已接受并用脚本生成 brief。下面第一节是本轮现状；后续 2026-10-12/13 批次均保留作历史记录，其中“未实现/未交付”不覆盖最新结论。

## 2026-10-15 串行续作：先 UC033，再 UC034

最终两项 Auth 后端 COMPLETE：UC033 验收后才开始 UC034，未调用 subagent。UC034 已接入两项精确 HTTP/native gRPC 方法及生产 Wire；普通密码与独立设备证明同操作验证，最终版本/归属/下界/审计/Session/LRU 原子提交，完成不重返 token，退休/撤销/他人钥不复活，参数重哈希不改安全代际。没有新增产品恢复方式或旧数据迁移。

最终验证：make check（build/test/vet/Wire/proto）、make test-race 通过；真实 Mongo 全包 `-race -timeout=25m` 通过（Wire 244.829s / Mongo 737.131s / transport 1.795s）。密码登录专项通过（Wire 13.993s / Mongo 54.452s），含永久 dummy/非登录邮箱、NFC/重哈希、五次共享失败/容量、并发同公钥与完成、实际重置竞争、换角色/禁用恢复/注销、审计回滚/未知提交、部署与严格 BSON、清理隔离、真实重置后新钥登录。最终新增混合 Session LRU、跨挑战/冷换操作 key 不补地址额度、损坏 verifier 不计密码失败的真实 race 补测通过（16.144s）。OAuth reset 专项使用隔离 App provider，不冒称 Auth+App 双服务或 Gateway 联测。

两 API proto-check 与密码 Proto 输入一致性通过；71 份 brief、30 项 docs 工具测试、App registry、独立 libargon2 密码向量及设备/邮箱 v2/v3/UC032 向量通过。测试容器自动清理；本轮无提交、推送、部署或生产数据修改。入口仍默认关闭：正式 blocklist 来源/发布、目标机器参数及容量压测、Gateway DIRECT 与联合回归、Console/移动 UI/安全存储属于独立交付和启用门禁，不能据后端 COMPLETE 宣称完整产品可用。

UC033 后端验收完成：make check、普通 race、全仓真实 Mongo race（Wire 189.683s / Mongo 567.703s）通过；最终补充真实 race（Wire 12.385s / Mongo 60.408s）覆盖重置 OAuth 失效但 grant/sub 保留、注销清理隔离、严格 BSON/部署上下文、未知提交/审计回滚，以及关闭公开开关后 outbox 仍投递。通知是有界至少一次，不承诺 SMTP exactly-once。四方法已接入 HTTP/native gRPC/Wire，不表示 Gateway/客户端或生产启用。

随后开始 UC034：复用已验证的 UC033 runtime/统一额度及邮箱 v3 角色，独立 auth_password_logins 严格挑战记录，5 分钟/五次失败/24 小时请求幂等、每 owner 或受保护地址最多五个活跃操作，计入共享 10000 PENDING/1000000 物理保留上限。AUTH_PASSWORD_LOGIN_ENABLED 缺省关闭，启用要求 UC033 management/password runtime；无 SMTP 调用。不可接受操作永久 dummy，使用配置成本的随机 dummy verifier；最终 Auth 事务复核角色/密码/账号/凭据下界，不能复活旧钥。新增集合接入保留清理与 UC025；先重生成 brief 再实现。正式 blocklist 来源、部署压测、Gateway/客户端仍为独立门禁。

用户授权按顺序继续实现；以 docs b3eaad1、Auth a9003f3、API d1a8ac5（Auth 子模块 7a723bc）和工作树为现状。UC006/011/031 邮箱 v3、UC009/025/026 双证明及 UC032 已交付，UC033 的目录、共享密码计算/额度、凭据下界、退出屏障均可复用；不再将旧快照中的缺口当成当前阻塞。UC033/034 已 ACCEPTED，先刷新脚本 brief 再开工；本轮不新增产品恢复方式、不动 Gateway/客户端、不部署或自动迁移。

UC033 先完成：默认关闭的 `AUTH_PASSWORD_MANAGEMENT_ENABLED` 精确四方法（依赖已有 password/email runtime），独立 `auth_password_resets` 的严格记录/版本/码与完成 HMAC/24 小时幂等，接入共享操作容量、验证码发送额度及 UC025 清理。通知沿用唯一事件 outbox；每秒批次最多 32 条、租约覆盖 SMTP deadline，最多 8 次指数退避（1 分钟起、1 小时封顶），24 小时保留，到期每集合最多清理 64。SMTP 在事务外且可取消；固定事件 Message-ID 用于排重，网络未知投递可重复通知，但绝不重复密码变更。关闭公开入口仍维护保留数据；无 SMTP 配置时仅清理、不把未投递状态伪装成功。完成 UC033 的真实 API/Wire/SMTP/Mongo/race 后才开始 UC034。

## 2026-10-13 UC009/025/026 密码门禁修订（历史快照）

用户明确接受三项修订后标为 ACCEPTED，脚本生成 brief 后实现；UC032 仍 DRAFT，未生成新 brief 或开放跨设备管理。UC009 的旧入口只可撤销当前 Session 的凭据；其它合法形状目标在最终检查后统一 403，不查询目标归属。UC025 Prepare 字段 3、UC026 Complete 字段 4 强制 currentPassword＋原登记设备新签名，无旧省略密码旁路。

双证明使用同一进程密码计算器及共享持久额度，密码错误和签名错误共用五次上限。密码不进入原 Frame/JWS、日志或 App；最终事务复核密码/账号版本、当前 Session（app.close）、设备归属/下界和期限。DISABLED 只允许专用注销，无普通 Session/解除禁用。注销准备跨 App RPC、Ready/Confirm 复核及恢复/清理路径保留。

新增负测发现框架默认 1 秒请求超时不足，已显式设为 15 秒（客户端更短 deadline 保留），不延长证明/令牌期限。最终 make check、全仓 make test-race、真实 Mongo 全包 -race -timeout=20m 均通过（Wire 211.879s / Mongo 554.595s / transport 2.229s）；账号注销超时修复后真实 App Wire 连续两轮通过（117.509s）。两 API proto-check、68 份 brief、30 项 docs 测试、registry/公开向量通过，Auth 33 ACCEPTED/1 DRAFT 一致。测试容器自动清理。三项门禁后端 COMPLETE；Gateway/客户端、生产启用独立交付。完整密码登录/重置/通知 worker/公开密码服务仍未完成，不宣布新模型可部署。无迁移、提交、推送或部署。

## 2026-10-13 邮箱 v3 已接受并实施

用户审核接受 `auth-email-account-v3` 与 UC006/011/031 修订后，三项已标为 ACCEPTED 并用脚本生成 brief，再启动代码。当前工作树已交付密码＋邮箱＋后台密钥的原子注册、最多 10 个全局唯一已验证邮箱、目录/唯一登录角色独立版本、密码换主且保留设备/Session、非登录地址不可用于邮箱登录，以及当前 WHUT 绑定的校园投影/最后依据撤回。

七个 v3 HTTP/native gRPC 方法、严格载体/JSON/Proto、真实 SMTP、生产 Wire 与两 API 生成物已接入；旧 BeginSetEmail/CompleteSetEmail 永久 UNIMPLEMENTED 且撤去 HTTP 注解，旧 Get 只投影登录邮箱/角色版本。校园旧方法成为 ADD 别名；旧永久事实不再授权。OAuth/Developer/密码通知读取登录角色；新增目录/操作/变更集合进入有界注销清理。无生产迁移、自动修复/删除旧数据、提交、推送或部署。

首轮专项真实 Mongo/race（生产 Wire 18.920s、邮箱事务 8.588s）和 `make check` 通过。公开 v3 Frame/签名/HMAC 向量已由独立 Python 生成并与 Go 对照。旧格式 fixture 已显式更新；最终全仓真实回归通过，见上节。

UC033/034 仍 IN_PROGRESS：普通密码登录、重置、通知 worker、公开密码接口尚未交付；危险动作门禁见上节，完整新模型不能宣布生产就绪。UC009/025/026 修订已于 2026-10-13 获用户明确接受，生成 brief 后实施；UC032 继续 DRAFT。下文旧记录只表示相应历史批次。

## 2026-10-13 第一批密码核心历史快照

以 HEAD＋工作树为现状：Auth `b20ca1d`、docs `910a691`、API `507e252`；此前资料/学年/KV/UC031 未提交内容均保留，不从旧分支继承密码逻辑。UC033/034 已 ACCEPTED；其它邮箱/校园/设备/危险动作修订仍有独立审核门禁。没有生产迁移、自动删除开发数据、提交、推送或部署。

| 依赖 | 当前证据 | 剩余工作 |
| --- | --- | --- |
| 策略/crypto | password domain、passwordcrypto：NFC Unicode 15、Argon2id v19、随机 salt、成本上下界、摘要 pin 的版本化 blocklist、有界队列 | 正式列表来源/发布、配置和部署机器并发压测 |
| 协议/API | Frame/change/reset MAC、公开 JSON；独立 libargon2→Go x/crypto hash/NFC 对照；两 API checkout 的密码 Proto/生成物 | 严格 Transport/Wire/精确认证分派未实现，不注册端点 |
| 正常改密 | change UseCase 与 Mongo：旧密码验证、最终版本/Session/退出复核、下界/唯一保留设备、新 Session、幂等/审计/outbox 同事务 | 暂用旧单主邮箱通知 adapter；须换新目录，公开接入未交付 |
| 设备下界 | principal.minimumCredentialRevision、credential.credentialRevision；缺字段不补默认；设备/Session/LRU/邮箱复用最终栅栏、DISABLED 专用注销 | UC032 列表/命名/移除仍未实现 |
| Session 来源 | 两种新方法的严格 BSON/管理枚举/在线密码版本检查、只读列表 | UC034 登录 orchestration 尚未签发此类 Session，不把枚举当登录交付 |
| 额度 | Mongo sliding-window 全局/来源/owner、跨重启桶容量、Argon 取消不提前释放槽 | reset/login 匿名地址/操作总容量仍需统一 |
| 注册/邮箱/校园 | 用户确认地址全局唯一/最多 10 个、换主保留设备；新增 v3 草案 | [auth-email-account-v3](../../platform/contracts/auth-email-account-v3.md)须审核后接受 UC006/011/031、生成 brief 再实现 |
| 重置/通知 | 独立 reset MAC；唯一通知事件/期限/容量及原子 outbox | Reset Begin/Complete、共享 SMTP/码额度、dummy/角色复核、通知 worker 未实现 |
| OAuth/JWS | 复用 accountRevision；新增实际改密→OAuth code/access/refresh 拒绝、grant 原字节不变及 sub 保留的两类 client Mongo 集成通过 | 新密码公开接口的 Auth+App/Gateway 联测仍须补；离线短 proof 不承诺即时收回 |
| 注销/恢复 | 密码/改密/通知新增 bounded cleanup step、密码审计接入 180 天保留 | 后续 reset/login/目录新集合也须进入终止清单/真实恢复验收 |
| 危险动作 | 凭据下界作为共用安全依赖，不改原 proof 字节 | UC009 防旁路、UC025/026 密码提交与 UC032 新证明未交付 |

公开服务器仍为旧无密码邮箱 v2/单邮箱基线；没有新密码服务或启用开关。不能对外宣称新模型已安全可用，API 定义/核心测试不证明 Gateway/客户端交付。

已完成：用户授权、registry ACCEPTED、脚本 brief、工程字段/参数/Frame/MAC/API 生成物、公开向量、第一批核心真实测试。启用前仍需：v3 依赖协议审核/接受与注册初始化、目录/角色及校园依据、重置/登录/通知、危险动作防旁路、正式 blocklist/配置和 Wire/HTTP/gRPC/SMTP/专项 OAuth 联测。未经审核不实施新增 v3 协议。

本批实际验证：

- crypto/domain/BSON/向量 unit race；Python argon2-cffi 独立 libargon2 与 Go x/crypto 的 Argon2id/NFC、Frame/MAC、DER/high-S/low-S 对照通过，13 个字段/签名负向量拒绝。
- 开发机 benchmark（i7-12700H，5 次）约 19.08 ms/op、19.93 MB/op，不代替部署机器/并发压测。
- 正常改密真实 Mongo race：新 token 一次返回、结果丢失经当前钥恢复、旧 token/其他设备退休、禁用恢复不复活、错误密码/版本/退出/审计回滚、跨重启及并发共享额度。
- `make check` 通过；真实 Mongo 全包 `-race` 通过：Wire 160.860s、Mongo 319.313s。HTTP/SMTP/App 部分仅是旧公开基线回归，不冒称密码端点通过。
- 最后严化 outbox 容量/绑定 BSON、密码 Session 列表、TTL 延迟时的物理额度桶容量及清理隔离后，针对性真实 Mongo race 通过（38.249s）；实际改密→OAuth 两类 client 专项 race 通过（7.968s，App provider 使用隔离 fixture，不冒称双服务联测）。
- docs 工具测试 30 项、68 份 brief、App registry、Auth 独立 34 UC/191 BR（27 ACCEPTED/7 DRAFT）、新本地链接、旧设备/邮箱及新密码向量、各工作树 whitespace 检查通过；两 API checkout `proto-check` 通过。

## 2026-10-12 历史检查（下文为当时快照）

## 当前基线与可实现性

检查当前 Auth HEAD `b20ca1d` 与工作树：`internal/authentication/domain/authentication.go` 只有两种既有认证来源，Credential 没有持久 credentialRevision，Session 没有 passwordRevision/sourceSessionId；`internal/adapter/mongo/authentication_repository.go` 提供 WithAuthTransaction、最终账号/凭据确认与 CreateSessionTx。UC022 已有 accountRevision，OAuth model 与消费使用其当前版本。UC031/资料/学年/KV 既有工作树保留，不从旧系统复制密码代码。

| 依赖 | 已有基础 | 新缺口 |
| --- | --- | --- |
| 密码策略/存储 | Go crypto/配置与 adapter 边界 | Argon2id/NFC、参数/损坏校验、正式 blocklist/压测、密码版本及独立操作 key |
| 邮箱恢复 | UC011/012 SMTP/持久额度/冷换钥、校园共享发送 | RESET_PASSWORD 独立 HMAC/占位/幂等/容量/API；通知 outbox |
| 默认密码登录 | UC012 新钥＋邮箱操作结构、设备真实验证器 | 新 Frame/密码验证/不可接受占位、PASSWORD_AND_DEVICE、严格 API |
| 当前设备保留 | Session credentialId 和明确 owner | PASSWORD_AND_SESSION 新来源、保留凭据推进/新 Session 一次性结果恢复 |
| 大量旧钥收回 | UC022 accountRevision、认证事务栅栏 | minimumCredentialRevision/credentialRevision，避免无界逐钥事务写入 |
| OAuth/JWS 收敛 | 现有 code/access/family 的 accountRevision；Auth audience 在线检查 | 所有新增认证方法/密码写入推进版本回归，保留 grant/sub；离线残余明确 |
| 邮箱模型/注册 | 单邮箱 v2 基线，UC006/011 已 DRAFT | 注册密码完成版本、绑定列表/角色接口与版本、旧 REGISTER/BIND 防旁路 |
| 危险动作 | UC025/026 设备专用证明，UC032 挑战草案 | 密码提交验证/版本绑定、禁用账号专用注销校验；不得仅 UI 改造 |
| 注销/恢复 | UC025 分类清理/终止清单 | 密码记录、操作/通知、下界及版本加入清理/备份恢复，不复活退休钥 |

结论：现有基础支持该方案，产品失效策略已确认，没有外部学校/次数业务依赖；新密码适配器、消息/容量/向量和消费方完整升级仍为可实现性审核项，不能自动 ACCEPTED。当前 UC022 禁止另建 authenticationEpoch，本提案复用 accountRevision，并将密码凭据失效下界与账号禁用恢复区分；需同步其正文。

## 接受前清单

- [x] 默认邮箱＋密码、备用邮箱码、后台自动登录，以及正常保留当前设备/重置全部清退的产品方向已获用户接受。
- [x] 密码管理 UC033、密码登录 UC034、跨系统契约及相关 UC 同步路径已展开；仍 DRAFT。
- [ ] 审核 NFC/字符/算法默认、生产 blocklist 装载及真实 hash 压测；高成本验证并发/持久失败额度/容量取值闭合。
- [x] 密码契约已展开字段号/presence、HTTP/RPC/reason、重置 HMAC与幂等/冷换钥提案，UC033 已明确执行/操作容量；尚未成为已验收 API。
- [ ] 完整审核上述工程提案、通知 outbox/任务/索引并生成新公开向量，独立 API实现和真实压测不得以旧检查代替。
- [ ] 闭合 UC011 注册新版本、邮箱列表容量/归属/角色协议与 UC031 当前校园依据；不恢复旧无密码入口。
- [ ] 全部 Session 方法、凭据下界/代际、USER JWS/OAuth 消费与敏感动作密码校验列清楚验收；App 旧离线 proof 窗口不能承诺即时撤销。
- [ ] 用户审核完整 UC/契约后接受，才创建 UC033/034 brief specs 并脚本生成开工 brief；UC032 依赖先闭合。

## 建议实施顺序（未开始）

1. 密码/代际 domain、策略/crypto adapter、schema/init/fixture、完整认证消费与注销/恢复；不在生产请求中给缺字段补默认值。
2. UC011 新密码注册与邮箱列表/唯一角色，UC031 当前学校依据；新注册协议可测试后再启用入口。
3. UC033 改密/重置/API/SMTP 通知，UC034 密码登录、UC012 保留备用以及全部 Session 来源。
4. UC025/026/011 危险动作密码验证、UC032 密码＋当前钥单目标撤销；默认关闭直到无旁路。
5. make/check、公开向量/策略/存储测试、真实 Wire/HTTP/native gRPC/SMTP/Mongo race、改密/重置/角色/治理竞争、OAuth/Auth+App/Console/Gateway 联合回归。

本轮只做文档工具/索引/向量基线检查；新密码实现没有代码，不能宣称通过其真实集成验收。无生产迁移、提交、推送或部署。

## 本轮实际验证（2026-10-12）

- 既有 brief 脚本刷新与 `--check --all`：66 份通过；无 UC032/033/034 brief/spec。
- App registry：347 rows / 8 retired 通过；Auth 独立检查：34 UC/191 BR，标题/状态/锚点/唯一规则与 Next ID 闭合，9 DRAFT/25 ACCEPTED。
- 新 UC/readiness/密码契约的 12 个本地链接检查通过。
- docs 工具测试 30 项、设备 v1/邮箱 v2 既有向量与 `git diff --check` 通过。
- 新密码向量、Argon 压测及真实密码 API/Mongo/跨服务验收尚未执行，不以历史检查背书。
