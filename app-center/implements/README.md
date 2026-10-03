# App Center 实现入口

状态：`ACTIVE`

## 目的

本文是新实现参与者和自动化 agent 的首个阅读入口。它负责把领域设计导航到代码工作，不复制 Use Case、Business Rule 或 ADR 的权威正文。

业务语义以具体 `UC-*` 与 `BR-*` 为准；架构选择以 `ADR-*` 为准；日常工程规则以 [实现约定](implementation-conventions.md) 为准。发生冲突时，先停止受冲突影响的工作并修正文档，不由实现者自行选择其中一个版本。

## 实现上下文

App Center 的新实现从空白代码树开始，不承担旧实现的数据迁移、API 兼容、包兼容或行为兼容。旧实现只用于追溯历史需求，不是新代码的模板，不向新实现复制领域模型、目录结构、API envelope、数据库 collection 或工具函数。

设计文档有意独立于 App Center 代码仓库保存，未来将进入统一文档仓库。代码仓库不得复制一份文档作为第二权威来源。当前工作区中的权威目录是：

```text
docs/app-center/
```

agent 在无法访问该目录时不得依据记忆补写业务规则，应先报告缺少设计输入。

## 当前实现覆盖

设计状态与实现状态彼此独立，定义见[文档约定](../document-conventions.md#状态)。当前覆盖如下：

| Use Case | 设计状态 | 实现状态 | 已闭合 | 尚未闭合 |
| --- | --- | --- | --- | --- |
| [UC-APP-001](../use-cases/UC-APP-001-create-application.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、MongoDB Repository、配置注入、事务与并发集成测试、Proto、Kratos HTTP/gRPC Transport、可信身份 JWS、本地 Wire Composition Root、真实 MongoDB 端到端测试 | — |
| [UC-APP-002](../use-cases/UC-APP-002-create-application-version.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、Version 依附 OAuth 双数组配置及同事务创建、0015 migration/backfill、Scope Catalog cache、生成 Auth gRPC client、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-003](../use-cases/UC-APP-003-update-draft-application-version.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、OAuth 双数组完整替换/no-op/OCC 与同 revision 事务、显式 migration、生成 Auth gRPC client、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 JWS 与 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-004](../use-cases/UC-APP-004-submit-application-version-review.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、OAuth 回调策略复检及不可变深拷贝 snapshot、ApplicationReview migration、事务与管理员转让并发集成测试、生成 Auth gRPC client、DNS-only 公网 HTTPS 预检、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 JWS 与 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-005](../use-cases/UC-APP-005-decide-application-version-review.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、决定与本地不可变策略 MongoDB Repository、app-version-review-v2 激活/v1 退役、批准时 OAuth 回调复检、0005/0007/0015 migrations、System 自动拒绝、事务与并发集成测试、trusted-identity-v1 reviewer permissions、Auth Developer Status consumer、caller-signed service JWS、Auth SYSTEM principal 延迟解析/成功缓存、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、测试 Auth Server E2E、真实 App+Auth 双服务 E2E | Auth 普通 USER provision/身份签发与 reviewer grant/revoke 实现 |
| [UC-APP-006](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、0006 migration、MongoDB 原子 Repository、资源化 Proto、Kratos HTTP/gRPC Transport、可信身份 JWS、Wire Composition Root、真实 MongoDB 事务/并发集成测试与端到端测试 | — |
| [UC-APP-007](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、Publication/History MongoDB Repository、0008/0015 migrations、管理员/Version/Review/Profile 事务写入栅栏、当前 APPROVED Profile gate、批准 OAuth snapshot 一致性复查、按非空双数组检查 TEST PUBLIC/CONFIDENTIAL registration 与 credential、并发与回滚集成测试、复用 Auth Scope Catalog cache 与 DNS-only URL 预检、资源化 Proto、可信身份 HTTP/gRPC Transport、Wire、真实 MongoDB consumer E2E；服务 `f0ffd06`、API `88f182d` | —（当前 App Center 后端范围） |
| [UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、真实 CSPRNG/SHA-256、env 可配置 mock URL、MongoDB 原子轮换与管理员栅栏、0009 migration、并发/回滚/脱敏集成测试、资源化 Proto、可信身份 HTTP/gRPC Transport、no-store、Wire、默认/自定义前缀真实 MongoDB E2E | —（当前 mock 入口后端工作包；前端及 UC-APP-009 独立交付） |
| [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md) | `ACCEPTED` | `COMPLETE` | Membership Domain/UseCase、0010 migration、Application 写栅栏与事务内 ACTIVE 统计/插入、普通用户可信身份、API/Wire、并发/回滚/脱敏测试及真实 MongoDB HTTP/gRPC E2E | —（当前后端工作包；生产 Gateway 身份签发与客户端独立交付） |
| [UC-APP-010](../use-cases/UC-APP-010-remove-application-tester.md) | `ACCEPTED` | `COMPLETE` | 精确 episode 移除、不可变审计、幂等无 Clock、共享写栅栏与人数统计、500/INTERNAL 安全告警、API/Wire、真实并发/回滚/HTTP/gRPC E2E | —（当前后端工作包；列表查询、前端与生产 Gateway 独立交付） |
| [UC-APP-011](../use-cases/UC-APP-011-revoke-tester-join-link.md) | `ACCEPTED` | `COMPLETE` | 精确链接 MANUAL 撤销、无 Clock 幂等、ROTATED 历史保护、写栅栏、500/INTERNAL 安全告警、API/Wire、真实 MongoDB 并发及 HTTP/gRPC E2E | —（当前后端工作包；前端和生产 Gateway 独立交付） |
| [UC-APP-012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) | `ACCEPTED` | `COMPLETE` | Catalog Domain/UseCase、只读 MongoDB snapshot、ACTIVE Tester 授权、exact-major 解析、批准事实校验、HTTP/gRPC/Wire、真实并发与 E2E；服务 `95f3feb`、API `acfab91` | —（当前后端范围；前端宿主和生产认证链路独立交付） |
| [UC-APP-013](../use-cases/UC-APP-013-create-application-profile-revision.md) | `ACCEPTED` | `COMPLETE` | Domain/UseCase、严格 NFC、0011 migration、事务/指针/序号、HTTP/gRPC/Wire 与完整 backend 验收；服务 `d121d4e`、API `219419b` | —（当前后端范围） |
| [UC-APP-014](../use-cases/UC-APP-014-update-draft-application-profile-revision.md) | `ACCEPTED` | `COMPLETE` | 完整替换、NFC no-op、OCC/If-Match、事务栅栏与状态竞争、HTTP/gRPC及生成HTTP客户端、完整backend验收；服务 `a712456`、API `94347df` | —（015已闭合真实编辑/提交双命令竞争） |
| [UC-APP-015](../use-cases/UC-APP-015-submit-application-profile-revision-review.md) | `ACCEPTED` | `COMPLETE` | PENDING不可变快照、0012 migration、原子提交/OCC/attempt、指针保留、重复/回滚/双命令竞争、HTTP/gRPC与生成客户端、完整backend验收；服务 `3a87a0f`、API `a0c158c` | —（当前后端范围；审核决定、资料查询、前端与生产Gateway独立交付） |
| [UC-APP-016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md) | `ACCEPTED` | `COMPLETE` | 一次性审核/自动公开、独立权限与策略、0013 migration、事务写栅栏/指针CAS、REJECT原文保留、双协议与生成客户端、完整cross-service验收；服务 `a844f08`、API `bc05993` | —（当前App Center后端范围；Auth资料权限授予/签发、管理查询与前端独立交付） |
| [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md) | `ACCEPTED` | `COMPLETE` | 独立OAuth Client Domain/UseCase、TEST渠道稳定PUBLIC/CONFIDENTIAL UUIDv4 identity、一次性secret与独立credential revision、状态epoch、0014 migration、管理员事务栅栏、HTTP/gRPC/Wire及完整cross-service验收；服务 `041a929`、API `51e6572` | —（当前管理员管理范围；Version OAuth配置与Auth provider已由后续工作包交付，Auth授权和后续渠道独立交付） |
| [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md) | `ACCEPTED` | `COMPLETE` | 五个 Auth-only 原生 gRPC Provider 方法、本地 service caller registry 与逐方法权限、secret revision 验证、TEST exact-major/批准 Version/Review/Profile/Tester 单 Mongo snapshot、5秒 runtime tuple、sector 回调事实并集及完整 cross-service 验收；服务 `657eccd`、API `310fc10` | —（当前 TEST 后端范围；Auth grant/code/token、Scope enabled 过滤、sector/sub 与未来渠道由 Auth/后续 UC 交付） |
| [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) | `ACCEPTED` | `COMPLETE` | exact-major stable set/replace/clear、共享 Publication OCC、EMPTY 保留与 History、0016 migration、HTTP/gRPC、STABLE OAuth 管理及五个 Auth-only Provider 方法、完整 cross-service 验收；服务 `531f077`、API `90519af` | —（当前 App Center 后端范围；Grey、test clear、Catalog 与 Auth grant/code/token 独立交付） |
| [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md) | `ACCEPTED` | `COMPLETE` | Stable-backed Grey set/adjust/replace/clear、固定 HMAC cohort、共享 Publication OCC/History、0017 migration、双协议、GREY OAuth 与 Provider cohort 复算、完整 cross-service 验收；服务 `d8369b1`、API `59436f1` | —（当前 Grey 管理与 Auth provider 范围；统一 test>grey>stable 解析、Catalog、test clear 与 Auth grant/token 独立交付） |

UC-APP-013 → UC-APP-014 → UC-APP-015 已按顺序完成，UC016、UC018、UC019 与 UC020 也已完成；UC002 → UC003 → UC004 → UC005 → UC007 的 Version OAuth 扩展已按同一依附配置纵切片交付。后续任务必须先在代码仓库的 `AGENTS.md`“Current work package”中声明目标 UC、涉及的 BR/ADR 小节、代码范围、非目标和验证命令；不得依据最近编辑的文档猜测当前任务。

API 与真实 Auth transport 作为后续独立工作包接入。MongoDB document、driver error、Auth transport、环境读取和 cache 状态不能进入领域对象或 UseCase。

## 局部阅读协议

设计完整性用于支持按需定位，不表示每个实现者都要通读全部文档。开始一个工作包时只建立以下工作集：

实现类工作包的默认设计输入是**生成的 brief**，不是 UC/ADR 原文。brief 由 `tools/gen_brief.py` 从权威正文确定性抽取，抽取范围写在 `tools/brief-specs/*.json`。

### Required

- 代码仓库 `AGENTS.md` 中的当前工作包声明。
- [`briefs/_engineering-baseline.md`](../briefs/_engineering-baseline.md)：跨能力架构决定，每个 agent 会话读取一次，之后长期复用。
- [`briefs/UC-APP-XXX.md`](../briefs/UC-APP-XXX.md)：该工作包的 brief，含本 UC 正文小节、本 UC 权威 `BR-*` 正文与外部引用 `BR-*`。

工作包声明必须**指向 brief**，而不是重复列出 UC/BR/ADR 小节标题。目标 UC 尚无 brief 时，先建立或刷新 `tools/brief-specs/UC-APP-XXX.json` 并生成 brief，再开始实现；确定 spec 范围属于设计决策，不是实现者的自由裁量。

brief 是派生制品，不是权威。生成时若某个选中的小节、`BR-*` 或 ADR 章节无法在源文件中找到，生成会 fail closed，而不是产出残缺 brief。

### Lookup only

- brief 末尾的「未纳入本 brief 的源小节」列出了被省略的小节标题。只有工作包确实需要其中某一节时，才按锚点读取该**单个**小节，不整文件加载。
- 使用搜索定位 [设计注册表](../design-registry.md) 中的目标 ID；不得把整个注册表作为默认必读材料。
- [领域模型](../domain-model.md)、[生命周期模型](../lifecycle-models.md)、[Capability Map](../capability-map.md)、[愿景](../vision.md)、[术语表](../glossary.md) 等概述文档是**设计任务**的工作集，不是实现类工作包的默认输入。

### Out of scope by default

- 其他 UC、其他聚合、未来 Transport、未被引用的 ADR。
- 旧实现；除非工作包明确要求把它作为某条需求的历史证据。
- 任何 UC/ADR 原文的整文件加载。

brief 未覆盖、或两条权威规则冲突时，不要自行发明：产出结构化 gap（`authority` / `conflict` / `options` / `suggested`），路由给读全量概述文档的设计任务；权威正文更新后重新生成 brief，再继续实现。

## 权威层次

从高到低使用以下顺序：

1. `BR-*` 权威正文：业务不变量、权限、状态、审计与原子性。
2. 所属 `UC-*`：命令目标、流程、输入输出和验收场景。
3. `ADR-*`：技术与架构决定。
4. Query Contract：读模型的应用层语义。
5. `implements/*`：实现组织、工作范围和交付约定。
6. README、愿景、Capability Map、术语表等非规范性摘要。

下层文档不得改变上层语义。发现冲突时记录具体链接与条目，并在继续编码前修正权威文档。

## 已锁定的实现决定

- 新代码不建立旧实现兼容层，也不读取或写入旧数据结构。
- 代码按业务能力组织，依赖方向遵循 [ADR-003](../adr/ADR-003-go-package-and-dependency-boundaries.md)。
- 需要跨文档或跨聚合原子性时使用支持事务的 MongoDB 拓扑和显式迁移，遵循 [ADR-004](../adr/ADR-004-mongodb-transactions-and-schema-management.md)。
- `application_creation_quotas` 是 Application 创建配额的唯一权威来源；`CreateWithinQuota` 仅在记录不存在时使用已注入的启动配置建立它，不得改写已有 `limit`。配置默认 10。
- capability 名称由客户端 RPC 契约负责；当前 App Center 不建立在线 Capability Catalog，只按 UC-APP-002 校验、排序和保存。
- Auth 是 Scope Catalog 唯一权威；cache adapter 实现 port，fake/mock 只能位于测试，真实 Auth transport 仍是后续工作包。
- 环境变量只在 config/composition boundary 读取并校验；UseCase 和 adapter 只接收构造参数。显式非法配置必须阻止启动，不得静默使用默认值。
- 领域错误不依赖 transport/framework，遵循 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md)。
- Proto 源文件位于独立 API 仓库，当前首个正式协议使用 `app_center.v1` 命名空间，遵循 [ADR-006](../adr/ADR-006-proto-v1-and-api-repository.md)。
- 设计经必要评审后可以从 `PROPOSED` 进入 `ACCEPTED`；实现覆盖在上方独立登记，不用设计状态暗示交付完成度。

## 开始工作前检查

- 当前任务明确指出一个 UC 或一个有边界的工程工作包。
- 已阅读当前工作包 Required 列表中的 UC/BR/ADR 小节；没有默认加载未引用文档。
- 所需 ADR 不存在未解决冲突。
- 工作树中没有不属于当前任务且会被覆盖的修改。
- 测试计划能把每一条相关 BR 映射到至少一个验证点。
- 外部契约尚未确定时使用 port 隔离，不猜测 Auth、MongoDB 或 Proto 的具体实现。

## 完成标准

一个工作包只有同时满足以下条件才完成：

- 代码只实现声明的范围，没有顺手加入后续领域能力。
- 相关 BR 有自动化测试或明确说明为何只能由更高层测试覆盖。
- 正常、边界、失败和并发语义按风险得到验证。
- Domain 不依赖 Kratos、MongoDB、Proto、HTTP 或配置结构。
- 生成物由生成命令产生，不手工修改。
- 格式化、静态检查和相关测试通过。
- 新增或改变架构决定时，同步更新 ADR 与注册表。
- 新增业务语义时，先修改 UC/BR，而不是只把规则藏在代码中。
- commit message 遵循 [实现约定](implementation-conventions.md#commit-message)。

## 已知的后续交付事项

UC-APP-001 已闭合其当前所需的 Proto、可信身份、Transport、进程组装和端到端验证。以下事项不影响 UC-APP-002 至 UC-APP-005 保持各自已登记的设计与实现状态，但对应实现完成前不能把它们标记为 `COMPLETE`：

- Auth 的 reviewer 权限签发/撤销生命周期。
- Auth 普通 USER provision 与 trusted identity 签发。
- test clear、Filter 和 Catalog 的后续设计。
- CI/CD、可观测性和生产部署。

它们进入对应工作包前必须有明确契约，但不能提前渗入 Application 领域模型。

## 后续工作包依赖检查

- [UC-APP-008 开工检查（2026-09-22）](UC-APP-008-readiness.md)：持久化轮换方案已做真实 MongoDB 验证；用户已接受 mock URL/env 前缀方案，编码契约和 brief 已生成，工作包已激活。
- [UC-APP-019 开工检查（2026-09-29，2026-10-03 确认）](UC-APP-019-readiness.md)：数据依赖、consent 展示投影、TEST 边界和入站 Auth service identity 均已确认；设计已接受并生成实现 brief。

## 2026-09-22 UC-APP-007 交付记录

- 按 RPC major 创建或替换 test 指针，并原子追加 History；相同目标与匹配 revision 返回 no-op，不调用 Scope/URL 复检、IDGenerator 或 Clock。
- 最终事务复查当前管理员、完整 APPROVED Review/snapshot、Version revision 和 Publication revision，并用 adapter-only 写入栅栏保护资格来源；不改变 Application/Version 业务字段或业务 revision。
- 通过 `0008_application_publication` 显式创建 schema/index 和资格来源的技术栅栏字段；服务启动只检查 migration ledger，缺少 0008 时拒绝服务。
- 代码、API 和设计文档保持本地交付。consumer E2E 使用真实 MongoDB、HTTP/gRPC、可信身份 JWS，以及生成接口的测试 Auth Server；不能据此把 Auth MongoDB 权威目录或完整双服务验证标记为完成。

## 2026-09-22 UC-APP-008 交付记录

- 依据 [UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) 交付 Application 级加入链接创建/轮换。真实 CSPRNG 生成 secret，数据库只保存原始 bytes 的 SHA-256；成功响应只返回公开元数据与一次性 joinUrl。
- URL 采用 [共享 fragment 格式](../../platform/contracts/tester-join-url-v1.md)，默认 mock 入口与 env 自定义前缀均不要求网络可达。配置只在边界读取，显式非法值拒绝启动。
- `0009_application_tester_join_link` 迁移提供链接/哈希唯一索引、单一 ACTIVE 部分唯一索引与审计 validator；保留 MANUAL 历史形状，当前命令只创建 ACTIVE 或轮换为 ROTATED。
- 旧链接撤销、新链接插入与当前管理员栅栏在同一事务提交；失败保留旧链接。明文凭证不进入 Repository，驱动唯一键与迁移失败也不能把哈希带入普通错误日志。
- HTTP/gRPC 成功响应带 no-store；HTTP query 不能覆盖正文中的 expectedActiveJoinLinkId。原始 secret、哈希与完整 URL 不进入失败响应。
- 本次 COMPLETE 范围是用户明确接受的 mock 入口后端工作包；前端扫码/托管、正式域名、UC-APP-009 加入、UC-APP-011 显式撤销和生产登录链路仍各自交付，不由本 UC 自动实现。

验证：`go test ./...`、`go vet ./...`、`go test -race ./...`、格式化、Wire diff、Proto 生成一致性与完整副本集集成脚本均通过；Mongo 套件 119.818s、cmd E2E 17.403s。服务本地提交 `f39f561`，API 本地提交 `9365b1d`，未 push。

## 2026-09-22 UC-APP-009 交付记录

- 服务提交 `2d19738`、独立 API 提交 `993eb3e`，均为本地提交，未 push。服务/API 工作树已核对干净。
- 采用与 UC-APP-008 共享的 Application `coordinationRevision` 写栅栏，在同一事务内复查链接、判断 ACTIVE 幂等、统计人数与插入 Membership；上限固定 100，不新增持久化计数器。
- BR-TST-010–019 均有自动测试覆盖，包括普通用户身份、严格凭证校验、满员幂等、移除历史与重新加入、最后名额竞争、同用户竞争、轮换双向竞争、回滚和敏感数据保护。
- 实现 agent 报告全量 `go test ./...`、`go vet ./...`、`go test -race ./...`、gofmt、Wire diff、Proto 一致性全部通过。完整副本集脚本最终 exit 0：Mongo 集成 `157.480s`，真实 HTTP/gRPC cmd E2E `23.055s`。文档 30 项测试、15 份 brief freshness、registry 与 diff 检查通过。
- 部署前需显式执行 `0010_application_tester_membership` migration。COMPLETE 仅指当前后端范围，生产 Gateway 的登录凭证到 JWS 链路和前端接入仍独立交付。

## 2026-09-22 UC-APP-010 激活记录

- [开工检查](UC-APP-010-readiness.md) 已闭合依赖和错误映射决策；当前后端工作包已进入实现阶段。

## 2026-09-23 UC-APP-010 交付核对

- 服务提交 `5352758`、独立 API 提交 `e46c75b` 已核对，服务/API 工作树干净，均未 push。
- BR-TST-020–028 已实现：管理员按精确 Membership episode 幂等移除、审计保留、释放容量、原链接不变；一致性异常固定 HTTP500/gRPC INTERNAL，并有脱敏 ERROR 级告警。
- 本次复核 `go test ./...`、`go vet ./...`、`go test -race ./...`、gofmt、Wire diff、Proto 一致性与 diff 检查均通过。完整副本集脚本 exit 0：Mongo 集成 `170.466s`，真实 HTTP/gRPC cmd E2E `24.979s`；涵盖双重移除、旧 episode 保护、移除/重新加入和管理员转让竞争、回滚与容量复用。
- 复用现有 0010 schema，无新增 migration；列表查询、前端及生产 Gateway 仍独立交付。

## 2026-09-23 UC-APP-011 激活记录

- [开工检查](UC-APP-011-readiness.md) 无前置实现阻塞。沿用用户已确认的内部不变量异常 500/INTERNAL 分类，无新增业务决策。
- UC011 已 ACCEPTED，脚本生成 brief，代码仓库 AGENTS 工作包切换，交由 subagent 实现当前后端范围。

## 2026-09-26 UC-APP-011 完成核对

- 实现提交为服务 `1630c9c`、API `6dc372d`；当前基线已包含统一 API 路径变更（服务 `88f3a6d`、API `ef89575`），工作树干净，无推送操作。
- 原实现 agent 已报告全量 go test/vet/race、Proto/Wire 与完整副本集 runner 通过（Mongo190.136s，cmd E2E26.958s）。本次进一步检查实际仓库代码，重跑全量 go test、vet、Proto/Wire，并运行 `./scripts/test-mongo-integration.sh -run 'Revocation|UCAPP011'`：Mongo23.134s，真实HTTP/gRPC E2E2.731s，exit0。
- BR-TST-029–036 已交付；无新增 migration，Membership 和人数不受撤销影响。当前后端工作包登记 COMPLETE。

## 2026-09-26 UC-APP-012 激活记录

- [开工检查](UC-APP-012-readiness.md) 确认前置数据、事务与接入设施已具备；UC007 的外部 Auth Catalog 交付不阻塞本只读解析。
- UC012 已 ACCEPTED，brief 由脚本生成，AGENTS 切换至 Catalog & Resolution 查询工作包，交由 subagent 实现；前端宿主和生产认证链路独立交付。

## 2026-09-27 UC012 完成与 UC013–015 开工核对

- UC012 已交付服务 `95f3feb`、API `acfab91`；随后工程工具提交 `489a117` 的完整 cross-service 报告通过22道门禁，包含全量 race、Mongo 与 HTTP/gRPC E2E，验证期间来源未变化。报告为服务工作树 `.artifacts/verification/20260926T161006Z-rbq4hmto/report.json`。
- [统一依赖检查](UC-APP-013-015-readiness.md) 已完成，无新增产品决策阻塞；按用户要求串行推进013、014、015，禁止提前并行实现后续用例。

## 2026-09-27 UC013 完成与 UC014 激活

- 服务 `d121d4e`、API `219419b`，本地工作树干净，无push。BR-PRF-001–007全覆盖；0011 migration显式执行并由readiness检查。
- `make check-full` 21/21通过，报告 `.artifacts/verification/20260926T163406Z-_pj4bwls/report.json`；`changed_sources=[]`，Mongo race314.489s、真实HTTP/gRPC E2E35.516s。严格NFC另经Python独立12,064条向量逐字对照，无差异。
- UC014的前置依赖已完成，按已生成brief串行激活；UC015继续等待。

## 2026-09-27 UC014 完成与 UC015 激活

- 服务 `a712456`、API `94347df`，均本地提交且工作树干净。BR-PRF-008–014完成；无schema/migration变化。真实编辑与提交双命令竞争由015闭合。
- 修正013/014的生成HTTP客户端绑定：资料放独立profile子message，HTTP正文仍为原三字段；path-only字段显式JSON名与路由模板匹配。013旧请求字段编号2/3/4及名称reserved，gRPC创建改用profile子message，所有本地调用与生成物同步更新；新增真实生成HTTP客户端创建/更新回归。未扩展其他历史接口。
- 最终 `make check-full` 21/21通过：`.artifacts/verification/20260926T165213Z-dyloh589/report.json`，`changed_sources=[]`，Mongo race317.175s、HTTP/gRPC E2E39.931s。修复前中断的报告不作为验收证据。
- 015前置依赖已满足，按既有ACCEPTED设计和脚本brief激活。只交付提交审核，不提前实现审核决定/查询/前端。

## 2026-09-27 UC015 完成与本轮串行交付闭合

- 服务 `3a87a0f`、API `a0c158c`，均本地提交，工作树干净，未push。BR-PRF-015–022全部覆盖；显式 `0012_application_profile_review` migration已接入readiness。
- 最终 `make check-full` 21/21通过，报告 `.artifacts/verification/20260926T171817Z-0o1w1gkw/report.json`，`changed_sources=[]`；Mongo race415.916s、真实HTTP/gRPC E2E69.237s，包含实际生成HTTP客户端。验收后仅提交相同源码内容。
- 真实公开 `ReplaceDraft` / `SubmitDraft` 的两种确定性竞争胜序已验证，闭合014留下的双命令测试义务；同时覆盖快照深拷贝、内容复检/内部异常区分、attempt唯一性与溢出、重复请求、管理员转让、回滚及指针保留。
- 首轮完整回归发现两处既有迁移数量断言仍为11，修正为12后定向验证并完整重跑；首轮失败报告不作为验收证据。
- 本批次013/014/015均为ACCEPTED/COMPLETE，各自完整backend验收通过。部署当前代码需显式执行包含0011与0012的迁移；审核决定、资料管理查询、前端和生产Gateway仍独立交付，未启动UC016。


## 2026-09-27 UC016 完成

- [依赖检查](UC-APP-016-readiness.md)与用户确认的两项固定审核检查已落实；UC016 为 ACCEPTED / COMPLETE（App Center 后端范围）。服务 `a844f08`、API `bc05993` 均已本地提交，未 push。
- BR-PRF-023–032全部交付：独立 `app.profile.review` 权限与三类利益冲突，PENDING 一次性决定，本地不可变 `app-profile-review-v1`，Application/policy 真写栅栏，Review/Revision/资料指针原子变化，APPROVE 自动公开，REJECT 原文保留与工作位释放。包含真实双向竞争、回滚、历史重建、坏内容与结构异常区分、后续新草稿和实际生成HTTP客户端。
- 显式 `0013_application_profile_review_decision` migration 已接入 readiness：升级 Review/Revision validator，建立正式策略；部署前需执行迁移。已提交 decision 字段保留 Value 类型和 field 10，扩充终态对象输出；新增资源化 HTTP/gRPC 决定命令。
- 最终 `make check-auth-app` 22/22通过，报告为服务工作树 `.artifacts/verification/20260927T023242Z-hs0ev8iq/report.json`，`changed_sources=[]`。Mongo race439.604s、真实HTTP/gRPC E2E59.976s、真实Auth进程回归3.184s。报告记录提交前服务 `3a87a0f` / API `a0c158c` 的dirty来源；提交前指纹与报告完全一致，提交后逐文件内容校验保持一致。
- 首轮全量验收发现0013 schema 使用多键无序map，造成fresh/sequential的BSON字段顺序不同；已改为有序BSON并新增递归schema及重复编码一致性测试。定向真实迁移验证后完整重跑通过，首轮失败报告不作为验收证据。独立最终审查未发现剩余问题。
- Auth 正式 `app.profile.review` 授予/签发仍单独交付；现有真实Auth回归不证明该新增权限的生产链路已可用。资料管理查询、前端、生产Gateway与后续UC未扩展。本次验收后只记录提交和完成状态，未再改变服务/API内容。

## OAuth / OIDC 后续工作包

OAuth/OIDC 设计采用三种生命周期。UC018 已实现 Application＋channel 级 `ApplicationOAuthRegistration` 与独立 `OAuthClientCredential` 的管理员管理；UC002/003/004/005/007 已实现一对一依附 Version 的 `ApplicationVersionOAuthConfig`，包括 `{pkceRedirectUris, confidentialRedirectUris}`、历史双空数组 migration、同事务/revision 编辑、审核 snapshot 深拷贝和复检、`app-version-review-v2`，以及发布时非空数组对应 identity/credential 的存在性检查。UC019 已实现 Auth 专用 provider 查询与服务身份边界。

| Use Case | 设计状态 | 实现状态 | 主要交付 |
| --- | --- | --- | --- |
| [UC-APP-018](../use-cases/UC-APP-018-manage-oauth-client.md) | `ACCEPTED` | `COMPLETE` | 管理 TEST 稳定 OAuth registration 与独立 credential；服务 `041a929`、API `51e6572` |
| [UC-APP-019](../use-cases/UC-APP-019-resolve-oauth-authorization-context.md) | `ACCEPTED` | `COMPLETE` | 五个 Auth-only 原生 gRPC 方法、服务身份逐方法授权、单 snapshot runtime/context/redirect 解析；服务 `657eccd`、API `310fc10` |
| [UC-APP-020](../use-cases/UC-APP-020-manage-stable-publication-slot.md) | `ACCEPTED` | `COMPLETE` | Stable 发布管理、共享 Publication OCC、STABLE client 与 Provider 解析；服务 `531f077`、API `90519af` |
| [UC-APP-021](../use-cases/UC-APP-021-manage-grey-rollout.md) | `ACCEPTED` | `COMPLETE` | Grey rollout 管理、确定性 cohort、GREY client 与 Provider cohort 资格；服务 `d8369b1`、API `59436f1` |

UC018 已在 Version OAuth 扩展之前独立交付，随后 UC002→003→004→005→007 的 Version 配置/审核/发布扩展串行闭合，UC019 开放 Auth provider 方法，UC020/021 在相同边界上启用 STABLE/GREY；各批次保持独立 API 与服务提交。

## 2026-09-28 UC018 完成

- [依赖检查](UC-APP-018-readiness.md)结论已落实；UC018 为 ACCEPTED / COMPLETE（TEST渠道管理员管理范围）。服务 `041a929`、独立 API `51e6572` 均已本地提交，未 push。
- BR-OAC-001–005 已交付：每 Application＋channel 两个稳定 identity 槽位、跨槽位全局唯一 UUIDv4 clientId、registration/credential 独立 OCC、实际状态变化递增 authorizationEpoch、PUBLIC 无 secret、CONFIDENTIAL 32字节 CSPRNG secret 一次披露及域隔离 SHA-256 摘要。管理员归属通过 Application 真写栅栏在事务内复查。
- 显式 `0014_oauth_client_management` migration 建立 registration/credential collections、严格 validator 与唯一索引；CONFIDENTIAL identity 和 credential 原子创建。五个管理员方法均已接入资源化 HTTP/gRPC、稳定错误 reason、`Cache-Control: no-store` 与 Wire。GREY/STABLE 明确返回渠道未启用。
- 最终 `make check-auth-app` 22/22通过，报告为服务工作树 `.artifacts/verification/20260928T070657Z-ed6ypm5s/report.json`，`changed_sources=[]`；race 1.970s、Mongo/HTTP/gRPC race 726.985s、真实Auth进程回归10.340s。报告记录提交前服务 `a844f08` 的dirty来源，冻结指纹在验收期间未变化；相同内容随后提交为 `041a929`。
- 完整 migration/race 套件因重复验证隔离数据库已超过 Go 默认10分钟 package timeout，runner 默认调整为20分钟且保留命令行覆盖能力。UC019 provider、confidential secret验证、Version redirect/scopes、授权/token、sector/sub、前端与未来渠道均未实现。

## 2026-09-29 UC002–007 Version OAuth 扩展完成

- 服务 `3397cf1`、独立 API `12bf209` 均已本地提交，未 push。UC002/003 的创建、完整替换、规范化、no-op 与 OCC 共用 Version revision；配置在独立 collection 中一对一依附 Version，并和 Version 同事务写入。
- UC004/005 的提交和批准均显式重跑完整 OAuth redirect 策略；审核 snapshot 深拷贝并参与 Version/Review 一致性判断。`0015_version_oauth_redirects` 为历史 Version/Review 回填双空数组，退役不可变 v1 并激活含 `oauth-redirects-reviewed` 的不可变 v2。
- UC007 在初次读取和最终提交事务中都复查批准 snapshot 与 Version 配置；PKCE 非空要求 TEST PUBLIC identity，confidential 非空要求 TEST CONFIDENTIAL identity 和 credential。空数组不要求 client，禁用 identity 不阻止发布。
- 全量 Go 单元/架构测试、`go vet`、Wire diff 与 Proto 生成一致性已通过；真实 Mongo 定向回归通过（Mongo `169.476s`、HTTP/gRPC E2E `17.438s`）。最终交付门禁使用 `make check-auth-app`；UC019 provider、secret 验证、授权/token、sector/sub、前端及未来渠道不在本批次范围。

## 2026-10-03 UC007 当前公开资料 gate 完成

- 服务 `f0ffd06`、独立 API `88f182d` 均为本地提交，未 push。TEST 创建、替换和 no-op 在初次读取与最终事务中都要求 `currentPublishedProfileRevisionId` 指向同一 Application 的有效 APPROVED ProfileRevision。
- 缺少资料投影或当前公开指针固定返回 `ApplicationProfileRequired`（HTTP 422 / gRPC FAILED_PRECONDITION）；损坏指针、缺失目标、非 APPROVED 或内容不变量异常固定返回 `ApplicationProfileStateInconsistent`（HTTP 500 / gRPC INTERNAL），日志只记录稳定 reason。
- 复用 Application `coordinationRevision` 真写栅栏串行化资料审核批准和 TEST 槽位设置；真实 MongoDB 测试覆盖外部检查后的资料移除/损坏、资料指针替换竞争、回滚与 publication/history 唯一提交。E2E 先验证无公开资料被拒绝，再完成资料审核并发布。
- 最终 `make check-auth-app` 22/22 通过，报告为服务工作树 `.artifacts/verification/20261003T083148Z-98c6cmj7/report.json`，`changed_sources=[]`；Mongo/HTTP/gRPC race `629.019s`，真实 Auth/App 回归 `10.192s`。

## 2026-10-03 UC019 完成

- 服务 `657eccd`、独立 API `310fc10` 均为本地提交，未 push。API 新增无 HTTP annotation 的 `OAuthClientProviderService` 五个方法及稳定错误 reason；服务只在原生 gRPC 注册 Provider。
- `APP_CENTER_SERVICE_CALLERS_B64` 启动时严格解析并预加载至少 2048-bit RSA 公钥；固定 audience `iwut-app-center`、默认最大 TTL `1m`、时钟偏差 `30s`，按五个 `app.oauth.*` permission 精确授权。错误 audience、USER identity、缺失凭据、disabled caller、未知 key 和权限不足均失败关闭。
- client metadata 可解释 DISABLED identity；confidential secret 以恒定时间比较并绑定 expected credentialRevision。运行解析在单个只读 Mongo snapshot 中复查 registration、exact-major TEST Publication/History、APPROVED Version/Review snapshot、Version OAuth config、Application admin 与当前 APPROVED Profile；用户上下文额外绑定 ACTIVE Tester episode 和预登录 runtime tuple。快照有效期固定不超过5秒。
- sector 清单返回当前已发布 major 的批准回调去重排序并集，按已登记 type 选择数组，DISABLED identity 不删除既有 sector 事实；App 不生成 sector/sub。测试覆盖 secret 轮换、跨渠道/major、Tester 移除、资料缺失/损坏、批准 snapshot 漂移、资料切换并发、方法权限和真实 gRPC service JWS。
- 最终 `make check-auth-app` 22/22 通过，报告为服务工作树 `.artifacts/verification/20261003T133723Z-hhgptyx2/report.json`，`changed_sources=[]`；race `4.027s`、Mongo/HTTP/gRPC race `649.778s`、真实 Auth/App race `10.145s`。Auth grant/code/token、Scope Catalog enabled 交集、sector/sub、OIDC 标准 endpoint 和未来渠道仍由 Auth/后续工作包交付。

## 2026-10-04 UC020 完成

- 服务 `531f077`、独立 API `90519af` 均为本地提交，未 push。Stable 支持按 `(applicationId, rpcApiMajor)` 直接设置、替换、回退或清空 APPROVED Version；不要求先进入 Test/Grey。Test 与 Stable 共用 Publication revision，跨槽位并发只有一个命令提交。
- Stable 设置复用 UC007 的管理员、APPROVED Review/Version snapshot、当前公开 Profile、Scope 和 URL 复检，并按 Version 的非空 OAuth 数组要求独立 STABLE PUBLIC/CONFIDENTIAL registration 与 credential。清空保留 EMPTY Publication 和追加式 CLEAR_STABLE History；存在 Grey 时拒绝清空，损坏的 Grey-without-Stable 状态失败关闭。
- `0016_stable_publication` migration 扩展 Publication、History 与 OAuth registration schema。API 新增 Stable set/clear 双协议命令及可选 test/stable/history/provider 字段；HTTP 严格限制 query/body 形状。
- 五个 Auth-only Provider 方法支持 STABLE。Stable 用户上下文不要求 Tester，TEST 语义保持不变；redirect facts 对当前 Test/Stable 已发布 Version 按 channel/type 聚合，禁用 identity 仍保留 sector 回调事实。STABLE 与 TEST client identity、secret、状态和 authorizationEpoch 独立。
- 最终 `make check-auth-app` 22/22 通过，报告为服务工作树 `.artifacts/verification/20261003T181212Z-i3gxai6q/report.json`，`changed_sources=[]`；race `6.983s`、Mongo/HTTP/gRPC race `699.092s`、Auth/App race `10.193s`。报告记录提交前服务 `657eccd` 的 dirty 来源，验收期间指纹未变化，相同内容随后提交为 `531f077`。
- Grey rollout、test clear、Catalog/普通公开运行解析、Application disable 及 Auth grant/code/token/sector/sub 不在本工作包。

## 2026-10-04 UC021 完成

- 服务 `d8369b1`、独立 API `59436f1` 均为本地提交，未 push。Grey 支持在已有 exact-major Stable 基线上建立、扩大、缩小、替换 Version 与清空；与 Test/Stable 共用 Publication revision 和管理员写栅栏。
- `grey-bucket-v1` 使用每个 rollout 的 32 字节 CSPRNG seed 和可信 authId 执行固定 HMAC-SHA-256 万分比分桶。调整比例或替换 Version 保留 rolloutId/seed，Clear 后重建会生成新 cohort；seed 只保存于当前状态和首次 SET 内部历史，不进入 Proto、日志或普通追踪字段。
- START、INCREASE、REPLACE 复查当前公开 Profile、批准 Version/Review snapshot、Scope、URL 与独立 GREY OAuth registration/credential；DECREASE、Clear 和完全相同的 no-op 不依赖外部服务。五类 Grey History 均由 `0017_grey_rollout` 严格 validator 约束。
- 管理 API 同时支持 HTTP/gRPC。UC018 的三个 channel 均已启用；UC019 的五个 Auth-only Provider 方法支持 GREY runtime、已发布回调并集与服务端 cohort 复算，未命中统一返回 runtime unavailable，且不读取 Tester Membership。
- 最终 `make check-auth-app` 22/22 通过，报告为服务工作树 `.artifacts/verification/20261003T193810Z-aeknf0s6/report.json`；Mongo/HTTP/gRPC race 与 Auth/App race 均通过。首轮全量运行暴露的迁移计数、顺序升级清单和旧 History validator 回归已修复并在最终报告中复验。
- 统一 `test > grey > stable` 启动解析、匿名 Stable fallback、Catalog、test clear、Application disable、Auth grant/code/token/sector/sub 和前端不在本工作包。
