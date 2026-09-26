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
| [UC-APP-002](../use-cases/UC-APP-002-create-application-version.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、Scope Catalog cache、生成 Auth gRPC client、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-003](../use-cases/UC-APP-003-update-draft-application-version.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、显式 migration、生成 Auth gRPC client、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 JWS 与 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-004](../use-cases/UC-APP-004-submit-application-version-review.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、MongoDB Repository、ApplicationReview migration、事务与管理员转让并发集成测试、生成 Auth gRPC client、DNS-only 公网 HTTPS 预检、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、caller-signed service JWS、真实 JWS 与 MongoDB consumer E2E | Auth MongoDB 权威目录、完整双服务 E2E |
| [UC-APP-005](../use-cases/UC-APP-005-decide-application-version-review.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、决定与本地不可变策略 MongoDB Repository、0005/0007 migrations、System 自动拒绝、事务与并发集成测试、trusted-identity-v1 reviewer permissions、Auth Developer Status consumer、caller-signed service JWS、Auth SYSTEM principal 延迟解析/成功缓存、资源化 Proto、Kratos HTTP/gRPC Transport、Wire Composition Root、测试 Auth Server E2E、真实 App+Auth 双服务 E2E | Auth 普通 USER provision/身份签发与 reviewer grant/revoke 实现 |
| [UC-APP-006](../use-cases/UC-APP-006-restore-rejected-version-to-draft.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、0006 migration、MongoDB 原子 Repository、资源化 Proto、Kratos HTTP/gRPC Transport、可信身份 JWS、Wire Composition Root、真实 MongoDB 事务/并发集成测试与端到端测试 | — |
| [UC-APP-007](../use-cases/UC-APP-007-place-approved-version-in-test-slot.md) | `ACCEPTED` | `IN_PROGRESS` | Domain、UseCase、Publication/History MongoDB Repository、0008 migration、管理员与 Version/Review 事务写入栅栏、并发与回滚集成测试、复用 Auth Scope Catalog cache 与 DNS-only URL 预检、资源化 Proto、可信身份 HTTP/gRPC Transport、Wire、真实 MongoDB consumer E2E | Auth MongoDB 权威 Scope Catalog、完整双服务验证 |
| [UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) | `ACCEPTED` | `COMPLETE` | Domain、UseCase、真实 CSPRNG/SHA-256、env 可配置 mock URL、MongoDB 原子轮换与管理员栅栏、0009 migration、并发/回滚/脱敏集成测试、资源化 Proto、可信身份 HTTP/gRPC Transport、no-store、Wire、默认/自定义前缀真实 MongoDB E2E | —（当前 mock 入口后端工作包；前端及 UC-APP-009 独立交付） |
| [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md) | `ACCEPTED` | `COMPLETE` | Membership Domain/UseCase、0010 migration、Application 写栅栏与事务内 ACTIVE 统计/插入、普通用户可信身份、API/Wire、并发/回滚/脱敏测试及真实 MongoDB HTTP/gRPC E2E | —（当前后端工作包；生产 Gateway 身份签发与客户端独立交付） |
| [UC-APP-010](../use-cases/UC-APP-010-remove-application-tester.md) | `ACCEPTED` | `COMPLETE` | 精确 episode 移除、不可变审计、幂等无 Clock、共享写栅栏与人数统计、500/INTERNAL 安全告警、API/Wire、真实并发/回滚/HTTP/gRPC E2E | —（当前后端工作包；列表查询、前端与生产 Gateway 独立交付） |
| [UC-APP-011](../use-cases/UC-APP-011-revoke-tester-join-link.md) | `ACCEPTED` | `COMPLETE` | 精确链接 MANUAL 撤销、无 Clock 幂等、ROTATED 历史保护、写栅栏、500/INTERNAL 安全告警、API/Wire、真实 MongoDB 并发及 HTTP/gRPC E2E | —（当前后端工作包；前端和生产 Gateway 独立交付） |
| [UC-APP-012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md) | `ACCEPTED` | `IN_PROGRESS` | 依赖检查通过；选定只读 snapshot 与发布批准事实校验；brief 已配置 | Catalog 查询、MongoDB snapshot resolver、HTTP/gRPC/Wire、授权/兼容/并发及真实 E2E 验收 |

当前激活 UC-APP-012；代码仓库 `AGENTS.md` 和 [UC-APP-012 brief](../briefs/UC-APP-012.md) 声明本次范围。后续任务必须先在代码仓库的 `AGENTS.md`“Current work package”中声明目标 UC、涉及的 BR/ADR 小节、代码范围、非目标和验证命令；不得依据最近编辑的文档猜测当前任务。

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
- Grey、Stable、Filter 和 Catalog 的后续设计。
- CI/CD、可观测性和生产部署。

它们进入对应工作包前必须有明确契约，但不能提前渗入 Application 领域模型。

## 后续工作包依赖检查

- [UC-APP-008 开工检查（2026-09-22）](UC-APP-008-readiness.md)：持久化轮换方案已做真实 MongoDB 验证；用户已接受 mock URL/env 前缀方案，编码契约和 brief 已生成，工作包已激活。

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
