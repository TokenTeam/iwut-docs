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
| [UC-APP-001](../use-cases/UC-APP-001-create-application.md) | `ACCEPTED` | `CORE_COMPLETE` | Domain、UseCase、MongoDB Repository、配置注入、事务与并发集成测试 | API Transport、Composition Root、端到端测试 |
| [UC-APP-002](../use-cases/UC-APP-002-create-application-version.md) | `ACCEPTED` | `CORE_COMPLETE` | Domain、UseCase、MongoDB Repository、Scope Catalog cache、事务与并发集成测试 | 真实 Auth transport、API Transport、Composition Root、端到端测试 |
| [UC-APP-003](../use-cases/UC-APP-003-update-draft-application-version.md) | `ACCEPTED` | `CORE_COMPLETE` | Domain、UseCase、MongoDB Repository、显式 migration、事务与管理员转让并发集成测试 | 真实 Auth transport、API Transport、Composition Root、端到端测试 |
| [UC-APP-004](../use-cases/UC-APP-004-submit-application-version-review.md) | `ACCEPTED` | `CORE_COMPLETE` | Domain、UseCase、MongoDB Repository、ApplicationReview migration、事务与管理员转让并发集成测试 | 真实 Auth transport、真实公网 HTTPS 预检、API Transport、Composition Root、端到端测试 |
| [UC-APP-005](../use-cases/UC-APP-005-decide-application-version-review.md) | `ACCEPTED` | `CORE_COMPLETE` | Domain、UseCase、MongoDB Repository、0005 migration、System 自动拒绝、事务与并发集成测试 | 真实 Auth/ConfCenter/暂停检查/公网 URL adapters、API Transport、Composition Root、端到端测试 |

没有在本文中激活下一个实现工作包。具体任务必须先在代码仓库的 `AGENTS.md`“Current work package”中声明目标 UC、涉及的 BR/ADR 小节、代码范围、非目标和验证命令；不得依据最近编辑的文档猜测当前任务。

API 与真实 Auth transport 作为后续独立工作包接入。MongoDB document、driver error、Auth transport、环境读取和 cache 状态不能进入领域对象或 UseCase。

## 局部阅读协议

设计完整性用于支持按需定位，不表示每个实现者都要通读全部文档。开始一个工作包时只建立以下工作集：

### Required

- 代码仓库 `AGENTS.md` 中的当前工作包声明。
- 目标 UC 的目标、主流程、异常流程、测试与验收，以及当前改动涉及的 `BR-*` 权威小节。
- 当前改动涉及的实现约定小节与 ADR 精确小节。

### Lookup only

- 使用搜索定位 [设计注册表](../design-registry.md) 中的目标 ID；不得把整个注册表作为默认必读材料。
- 只读取 [领域模型](../domain-model.md) 和 [生命周期模型](../lifecycle-models.md) 中与当前聚合或状态转换直接相关的小节。
- 相邻 UC 只有被当前工作包精确引用时才读取对应小节，不因编号相邻而自动加载。

### Out of scope by default

- 其他 UC、其他聚合、未来 Transport、未被引用的 ADR，以及 README、愿景、Capability Map 等非规范性摘要。
- 旧实现；除非工作包明确要求把它作为某条需求的历史证据。

如果工作包无法给出精确到小节的 Required 列表，应先收紧工作包，而不是通过通读全部 docs 弥补边界不清。实现过程中只有遇到明确引用、冲突或缺失定义时才扩展工作集，并记录扩展原因。

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

以下事项不影响 UC-APP-001 至 UC-APP-005 保持 `ACCEPTED / CORE_COMPLETE`，但对应实现完成前不能把它们标记为 `COMPLETE`：

- Proto 字段编号和 HTTP 路径。
- Auth 的具体传输协议。
- ConfCenter 的 VersionReviewPolicy 契约、正式策略与历史版本 adapter。
- Developer suspension 和 System Auth ID 的真实 Auth adapter/启动配置。
- Grey、Stable、Filter 和 Catalog 的后续设计。
- CI/CD、可观测性和生产部署。

它们进入对应工作包前必须有明确契约，但不能提前渗入 Application 领域模型。
