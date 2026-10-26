# UC-AUTH-032 开工检查：设备登录凭据管理

状态：`ACCEPTED / COMPLETE`（Auth/API 后端）

2026-10-15 后续密码包现状见 [UC033/034 readiness](UC-AUTH-033-034-readiness.md)。以下 UC032 批次中的“密码登录/重置/通知未完成”均是 2026-10-13 历史检查，不覆盖后续进展；不改变客户端/Gateway 独立交付门禁。

## 2026-10-13 当前开工结论

用户要求继续完成 UC032，接受既有列表/命名/当前密码＋当前钥单目标撤销范围。当前 docs HEAD=df10243、Auth=b20ca1d、API=507e252，现有未提交修改全部保留；不依赖旧对话或旧分支。源 UC 与索引 ACCEPTED，先脚本 brief，再实现。

直接依赖均具备：CheckSessionReadTx、CredentialBoundsTx、共享 passwordRuntime/持久额度、UC009 current-only 门禁、邮箱 v3 恢复、UC025 终止/清理及 UC026 双证明样式。UC034 默认密码登录、UC033 重置/通知尚未完成，不是本 UC 直接阻塞；完整新模型不宣布生产就绪。

新增设备协议固定 Frame/Proto presence，Begin 保存密码版本；新集合加入共享容量、独立有界到期任务与 UC025 清理/180 天审计。已撤销钥也必须按合法结构保留占用后清理名称。公开向量、HTTP/native gRPC/生产 Wire/真实 Mongo/race 为交付门禁；Gateway/客户端/扫码/WebAuthn 不在本轮，无生产迁移、提交或部署。

## 2026-10-13 实施与验收结论

独立 API 两处 Proto/生成客户端、Domain/Port/UseCase、Mongo、Transport/config/Wire 与清理 worker 已交付。列表扫描上限 200、10/50 页大小、no-touch；label 严格 Unicode/CAS/no-op/溢出；Begin 幂等、原 Session/钥/目标/密码及账号版本；Complete 先设备证明后共享密码计算，最终同事务复核和撤销/操作/必要审计。旧 UC009 防旁路持续通过，默认关闭新入口不恢复旧授权。

严格 BSON 不默认为损坏字段补版本；只有双缺省 label/revision 才兼容旧未命名元数据。合法 CLOSED 最小记录返回无权，损坏 CLOSED 仍失败关闭。未知提交不返回成功；已完成重放仍复核当前 Session/密码/版本/签名；被撤销/禁用/恢复/注销后的旧调用权不复活。

新集合进入共享操作容量、五个本人 PENDING/全局 10000、24 小时保留与每批 64 清理；真实注销覆盖已命名且已撤销钥的占用保留、名称/操作删除、他人隔离及 CLOSED 满 180 天才删除审计。新入口默认关闭，持久操作存在时关闭开关仍保留清理 worker。

- `make check`、`make test-race`、两处 `proto-check` 通过。
- 真实 Mongo 全仓 `-race -timeout=20m` 通过：Wire 255.910s、Mongo 791.655s、transport 2.113s。
- 最终补充 UC032/生产 Wire/共享容量/账号版本 race 通过：Wire 11.887s、Mongo 116.913s；覆盖严格完成状态、并发 label CAS 单审计、全局 PENDING 不驱逐、五次失败、密码最终版本竞争、审计失败回滚、未知提交、扫描预算和完成重放。
- 独立 Python/Go Frame/DER 正反向量通过，两处向量与两 API 新 Proto/生成物完全一致；共享设备/邮箱 v2/v3/密码 v1 向量通过。
- 69 份脚本 brief、30 项 docs 工具测试、App registry、Auth 34 ACCEPTED UC/源索引一致及 whitespace 通过；脚本 brief 在实现前已生成，最终按权威源刷新。

测试 Mongo 容器由脚本自动清理，未修改生产数据或环境、迁移、提交、推送或部署。Gateway DIRECT 清单与三协议联合验收、移动页面及正式启用独立交付；扫码授权新设备、WebAuthn、批量撤销不在首版。UC033/034 的密码登录、重置、通知 worker 和公开密码服务仍未完成，不把本 UC COMPLETE 解释为完整模型生产就绪。

## 历史记录（以下仅为当时快照）

本文件记录依赖和实施范围，不定义第二份业务规则。权威草案见 [UC-AUTH-032](../use-cases/UC-AUTH-032-manage-own-device-credentials.md)。用户仅授权建立草案，尚未审核接受；没有生成 UC032 brief、修改 API 或启动代码实现。

## 2026-10-12 历史检查（下文为当时快照）

以各仓库当前 HEAD 加工作树为现状，不把旧对话或历史交付记录当实现证据。检查时 docs HEAD=`910a691`、Auth HEAD=`b20ca1d`、API HEAD=`507e252`；三者存在既有未提交修改，包括 UC031 与资料/学年/KV 工作，均保留。本轮没有引用旧分支实现。

| 依赖 | 当前证据 | 判断 |
| --- | --- | --- |
| 有效 Session、ACTIVE/代际与只读检查 | Auth `internal/adapter/mongo/authentication_repository.go`：`CheckSessionTx` / `CheckSessionReadTx`；UC007/022 | 可复用；不能通过普通 touch middleware 破坏列表只读语义 |
| 不可逆本人凭据撤销 | 已交付 UC009 基线；新防旁路修订 DRAFT | 生命周期可复用，原入口收紧和当前密码＋签名验证尚未实施，不能独立事务嵌套 |
| 当前旧入口授权 | `internal/adapter/transport/credential_revocation.go`、API `auth_center/v1/authentication/authentication.proto` | 有效 Session 可撤销其他凭据，无新证明；必须在接受时修订 UC009 并实施服务端防旁路 |
| 同设备挑战与真实签名 | UC025/026；Auth `internal/applicationclosereauth/`、`internal/adapter/mongo/application_close_reauth_repository.go` | 可复用验证器/事务设施；不能复用其 purpose、签名 Frame 或 app.close JWS |
| 列表/命名元数据 | Credential / CredentialDocument 当前只有 ID/owner/协议/公钥/指纹/创建与撤销时间 | 无列表/命名实现，无凭据级最近使用时间；需要新增元数据和有界查询 |
| 分页、只读栅栏、管理入口限流 | UC020 COMPLETE；Auth `internal/adapter/mongo/session_management_repository.go`、`internal/sessionmanagement/` | 可复用模式，不复用 Session 数量上限为凭据上限 |
| 新设备与丢失设备恢复 | UC012 COMPLETE，邮箱验证码＋本机新密钥登记原 authId | 已有；无需把旧设备授权新设备加入首版 |
| 注销/保留与恢复 | UC025 COMPLETE，已包含凭据占用保留、个人数据及审计清理 | 接受时补名称/挑战/新增审计清单及回归；不能永久保留名称 |
| 邮箱更换安全边界 | UC011 BR-EML-003 的 BIND 为有效 Session＋新邮箱码，无平台密码 | 用户已确认切换需当前密码；密码体系尚未实现，不能用扫码默认替代 |
| 邮箱列表/校园解绑 | UC011 单一激活邮箱；UC031 永久认证事实不保留校园邮箱归属 | 已确认邮箱列表唯一登录角色、当前学校绑定导出认证；需正式修订 UC011/012/031 |
| 密码恢复 | 现有邮件验证/限额可复用，无密码存储或重置 API | 已确认登录邮箱码重置，不要求旧密码；独立用途/版本/事务/凭据收敛待设计 |

技术结论：UC032 列表/命名/同设备签名撤销的后端基础具备；用户新加的邮箱列表、密码和校园解绑产品模型已确认，但协议与工作包尚未闭合，不能将它们视为现有能力。须明确正式 UC/契约修订和危险动作验证矩阵，尤其密码恢复后的设备/会话策略。没有外部业务次数权益或旧代码迁移的依赖；产品/协议接受仍是硬门禁，不能据此自动 ACCEPTED。

## 历史审核与接受清单（2026-10-12）

- [ ] 用户审核 UC032 的列表、命名、单目标移除及明确不包含项。
- [ ] 审核名称规则、分页、CAS、新签名字节、5 分钟/5 次失败/24 小时窗口与有界额度。
- [ ] 确认旧 UC009 Session-only 入口收紧为当前凭据，其他目标通过 UC032 同设备签名；不是只保护 UI。
- [x] 产品方向：平台密码、邮箱列表唯一登录角色、切换密码验证、非登录邮箱无登录/恢复权限、学校绑定导出认证，以及当前登录邮箱码重置已确认；并非 UC 接受。
- [x] 产品建议已接受，UC033/034/密码协议展开 DRAFT，危险动作矩阵、正常改密/重置收敛已确定；完整工程参数/向量/依赖仍待审核。
- [x] 已把确认的方向同步 UC006/011/031 DRAFT，以及 UC012/013/017/025/客户端/共享契约引用；旧实现仍只为基线，不是新设计开工。
- [ ] 完整闭合密码/邮箱/校园新协议、容量/归属/版本/清理及危险动作矩阵，逐项用户审核后接受。
- [ ] 接受时同步 UC009 / UC025、客户端组合建议、共享路由/精确 RPC 鉴权，以及新增证明的独立平台契约和公开向量。
- [ ] 经用户授权标为 ACCEPTED，配置 `tools/brief-specs/UC-AUTH-032.json`，脚本生成 UC032 和受影响既有 brief；未完成前不开工。

## 历史实施计划（当时未启动）

1. 独立 API Proto/生成代码：四个新方法、字段 presence、严格解码、完整方法名鉴权；旧入口的非当前目标禁止旁路。
2. Domain/Port/UseCase：列表、名称校验/CAS、目标绑定挑战与 Complete；复用现有凭据权威和签名验证器，不建第二套 owner。
3. Mongo：可选名称元数据、owner/排序索引、挑战幂等与容量、共享认证栅栏内的目标撤销/操作/审计；旧撤销逻辑拆成可在已有事务调用的原语，避免嵌套独立提交。
4. Transport/config/Wire：Session-only 精确分派，管理流程 no-touch，有界限流/严格 JSON/no-store，默认关闭新入口；旧入口修订是安全门禁，不能由新功能开关关闭而恢复绕过。
5. UC025 清理/终止清单/恢复：名称属于应清理个人数据，新增挑战及审计集合纳入分类与真实恢复验收。
6. 真实验证：公开正反向量、HTTP/native gRPC/Wire、Mongo 副本集/race、签名/重放/未知提交/账号治理竞争、旧登录和邮箱恢复回归。

Gateway DIRECT 清单、HTTP/gRPC/gRPC-Web 联合验收及移动客户端管理页面独立交付，不把 Auth/API 通过标为用户已可用。Android/iOS 安全存储签名/删除等既有客户端验证继续适用；没有后台签名能力的入口必须准确报错或引导邮箱登录，不能退回 Session-only 移除其他凭据。

## 历史文档验证

后续注册/登录文档审计已同步 UC006/011/031（DRAFT）、UC007/012/013/017/025 的关联边界、客户端/模型/权益参考、平台注册/登录/路由/OAuth 契约，以及 Console/Gateway 的消费提示。旧编码/向量和已交付历史证据保留；没有代码/API 修改。既有 brief 用脚本刷新以消除源漂移，不是接受 DRAFT 或启动实施；UC032 仍无 brief/spec。

后续审计实际验证：Auth 全索引 32 UC/179 BR 的标题/状态/锚点一致，4 DRAFT/28 ACCEPTED；UC030 五处旧缩写标题仅按正文修正索引。66 份既有 brief、App registry、30 项工具测试、设备 v1/邮箱 v2 向量及 diff whitespace 检查通过。密码/邮箱新接口未实现，不运行或冒称通过新模型代码验收。

草案仅加入导航和注册表索引，不改既有 ACCEPTED 规则或生成物。2026-10-12 实际执行：

- `python3 tools/gen_brief.py --check --all`：通过，66 份既有 brief；未新增 UC032 brief/spec。
- `python3 tools/registry.py --check`：通过，347 rows / 8 retired IDs；该工具只检查 App，不冒称已机械验证 Auth。
- `python3 -m unittest discover -s tools/tests`：30 项通过。
- Auth 独立检查：UC032 DRAFT、BR-LGN-025–030 唯一定义/登记/锚点、Next UC033/BR-LGN-031，以及新 UC/检查单 5 个本地链接通过。
- `git diff --check`：通过；没有代码/API 修改、提交、推送或生产部署。
