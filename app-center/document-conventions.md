# App Center 设计文档命名与编号规范

状态：`ACTIVE`

## 目的

本规范统一 App Center 设计文档中的标识符、文件名、标题和编号分配方式，确保每个设计项具有稳定且唯一的引用。

所有已分配的 UC、BR 和 ADR 标识符必须登记在 [design-registry.md](design-registry.md) 中。注册表用于发现重复编号和定位权威正文，不复制权威正文。

## 权威内容与注册表

- UC 的完整正文位于对应的 `use-cases/UC-*.md` 文件。
- BR 的完整正文位于引入该规则的 UC 文件中，以 `### BR-...` 标题作为权威定义；标题前必须声明对应的稳定锚点。
- ADR 的完整正文位于对应的 `adr/ADR-*.md` 文件。
- `design-registry.md` 是标识符分配和定位的完整目录，不是第二份规则正文。
- 修改标题、状态或权威位置时，必须在同一次变更中更新注册表。

同一内容不得拥有两个权威定义。其他文档需要复用规则时，应引用原 ID 和链接，而不是复制后分配新 ID。

允许在 README、术语表、愿景和背景文档中编写非规范性摘要或背景说明。非规范性摘要凡使用“必须”“不得”“仅允许”等语言表达业务约束，都必须引用对应的 `BR-*` 及其权威正文；摘要与权威正文发生冲突时，以 `BR-*` 权威正文为准。工程架构约束由 `ADR-*` 或状态为 `ACTIVE` 的实现规范定义，不为纯工程规则分配 BR；它们不得改变 UC/BR 的业务语义。

## 标识符格式

### Use Case

格式：

```text
UC-{BOUNDED_CONTEXT}-{NNN}
```

当前上下文代码：

| 代码 | 含义 |
| --- | --- |
| `APP` | App Center Bounded Context |

示例：

```text
UC-APP-004
```

含义是 App Center 中编号为 004 的 Use Case。编号只提供稳定身份，不表达优先级、版本、父子关系或强制执行顺序。

UC 文件名使用：

```text
UC-{BOUNDED_CONTEXT}-{NNN}-{verb-object}.md
```

英文名称使用小写 kebab-case，并优先采用“动作 + 业务对象”，例如：

```text
UC-APP-001-create-application.md
UC-APP-004-submit-application-version-review.md
```

### Business Rule

格式：

```text
BR-{BUSINESS_TOPIC}-{NNN}
```

当前业务主题代码：

| 代码 | 含义 |
| --- | --- |
| `APP` | Application 及创建配额 |
| `PRF` | ApplicationProfileRevision 及公开资料生命周期 |
| `VER` | ApplicationVersion |
| `REV` | ApplicationReview 及审核生命周期 |
| `PUB` | ApplicationPublication 及发布历史 |
| `TST` | Tester Membership 及加入链接 |
| `RUN` | 运行时启动目标解析 |

BR 编号属于业务主题，不属于单个 UC。因此同一主题的编号跨 UC 连续：`BR-VER-001` 至 `BR-VER-009` 位于 UC-APP-002，后续 UC-APP-003 从 `BR-VER-010` 继续。

`BR` 是宽泛的业务规则，可以表示字段规则、权限前置条件、状态迁移、不变量、审计要求或行为边界。当前不另设 `INV-*` 编号；需要登记不变量时，以对应 `BR-*` 作为稳定来源，并把规则类型标记为 `Invariant`。

每个 BR 权威标题前使用其 ID 的全小写形式声明 HTML 锚点，注册表和其他文档必须链接到该锚点，而不是只链接到所属 UC 文件。例如：

```markdown
<a id="br-ver-010"></a>

### BR-VER-010 仅草稿可编辑
```

新增业务主题代码前，必须先更新本文件和注册表，避免同一主题出现多个缩写。

### Architecture Decision Record

格式：

```text
ADR-{NNN}
```

ADR 编号在 `docs/app-center/adr/` 目录范围内全局唯一。文件名使用：

```text
ADR-{NNN}-{decision-topic}.md
```

ADR 记录重要设计选择的背景、决定、替代方案和结果，不替代 UC 或 BR。

## 编号分配规则

1. 编号固定为三位十进制数字，从 `001` 开始。
2. 新条目使用所属编号空间中下一个未分配编号。
3. 编号一旦分配就不得因排序、改名或移动文件而改变。
4. 归档或废弃的编号不得重新使用；在注册表中把状态标记为 `DEPRECATED` 或 `SUPERSEDED`。
5. 创建新条目时，必须在同一次变更中登记注册表。
6. 一个 ID 只能有一个权威正文位置；引用不算重复定义。
7. 标识符统一使用大写前缀和主题代码，例如 `BR-REV-012`。
8. 不在编号中编码日期、实现版本、团队或数据库技术。

## 状态

当前文档使用以下状态：

| 状态 | 含义 |
| --- | --- |
| `ACTIVE` | 治理规范当前生效；适用于本规范等治理文档 |
| `PROPOSED` | 已形成设计，但仍在讨论或尚未被明确接受为实现依据 |
| `ACCEPTED` | 设计已经评审并被接受，是后续实现的权威依据；不表示所有实现层次均已完成 |
| `DEPRECATED` | 不再推荐用于新设计，但仍可能存在引用或兼容需求 |
| `SUPERSEDED` | 已被另一条明确标识的设计取代 |

如果使用 `SUPERSEDED`，注册表必须在“替代项”字段记录替代它的新 ID；“备注”字段可记录替代原因、迁移说明或其他必要上下文。

BR 不维护独立状态，其状态继承唯一权威正文所属 UC 的状态。注册表中的 BR 表不得重复保存状态；需要判断 BR 状态时，应沿“权威位置”找到所属 UC。

设计状态与实现状态必须分开记录。UC、BR 和 ADR 只使用上表中的设计状态；实现覆盖由 `implements/` 记录，使用以下状态：

| 实现状态 | 含义 |
| --- | --- |
| `NOT_STARTED` | 尚未开始实现 |
| `IN_PROGRESS` | 已开始实现，但当前工作包尚未闭合 |
| `CORE_COMPLETE` | Domain、UseCase、必要持久化或核心 adapter 及相应自动化测试已经闭合；Transport、进程组装或端到端链路仍可待完成 |
| `COMPLETE` | 当前 UC 所需的 Transport、进程组装、外部 adapter 与端到端验证均已闭合，没有已知的必需实现缺口 |

实现状态不得反向改变设计状态。`ACCEPTED` 的 UC 可以尚未实现；实现达到 `CORE_COMPLETE` 也不自动证明其 API 或端到端交付已经 `COMPLETE`。

当权威正文不再属于活跃设计文档时，必须将其移动到 `docs/app-center/archive/` 下并保留原 ID、标题、正文和状态说明，不得直接删除。归档必须在同一次变更中更新注册表的“权威位置”链接；如果状态是 `SUPERSEDED`，还必须填写“替代项”。

## 新增条目流程

1. 在 [design-registry.md](design-registry.md) 查找对应编号空间的 `Next ID`。
2. 确认现有条目没有表达相同业务目标或规则。
3. 分配 ID，并创建或修改唯一的权威正文。
4. 在同一次变更中更新注册表、标题、状态和链接。
5. 搜索整个 `docs/app-center`，确认该 ID 只有一个权威标题。

示例检查命令：

```bash
rg -n '^(# UC-|### BR-)' docs/app-center/use-cases
rg -n '^# ADR-' docs/app-center/adr
```

引用同一 ID 的普通文本可以出现多次；检查重点是 `# UC-`、`### BR-` 和 `# ADR-` 权威标题不得重复。
