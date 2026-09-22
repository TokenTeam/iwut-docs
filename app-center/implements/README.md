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

当前激活 UC-APP-007；代码仓库 `AGENTS.md` 和 [UC-APP-007 brief](../briefs/UC-APP-007.md) 声明本次范围。后续任务必须先在代码仓库的 `AGENTS.md`“Current work package”中声明目标 UC、涉及的 BR/ADR 小节、代码范围、非目标和验证命令；不得依据最近编辑的文档猜测当前任务。

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

- [UC-APP-008 开工检查（2026-09-22）](UC-APP-008-readiness.md)：持久化轮换方案已做真实 MongoDB 验证；已确认前端扫码后发起已认证加入请求，精确 URL 编码待细化，未激活实现。

## 2026-09-22 UC-APP-007 交付记录

- 按 RPC major 创建或替换 test 指针，并原子追加 History；相同目标与匹配 revision 返回 no-op，不调用 Scope/URL 复检、IDGenerator 或 Clock。
- 最终事务复查当前管理员、完整 APPROVED Review/snapshot、Version revision 和 Publication revision，并用 adapter-only 写入栅栏保护资格来源；不改变 Application/Version 业务字段或业务 revision。
- 通过 `0008_application_publication` 显式创建 schema/index 和资格来源的技术栅栏字段；服务启动只检查 migration ledger，缺少 0008 时拒绝服务。
- 代码、API 和设计文档保持本地交付。consumer E2E 使用真实 MongoDB、HTTP/gRPC、可信身份 JWS，以及生成接口的测试 Auth Server；不能据此把 Auth MongoDB 权威目录或完整双服务验证标记为完成。
