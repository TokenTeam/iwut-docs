# Auth Center 设计标识符注册表

状态：`ACTIVE`

本文件只索引 Auth Center bounded context 的权威 UC 与 BR，不复制规则正文。跨系统契约位于 `platform/`，不登记为 Auth UC 或 BR。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Auth Center | `UC-AUTH-003` |
| Business Rule / Scope Catalog | `BR-SCP-006` |
| Business Rule / Developer Status | `BR-DEV-006` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `UC-AUTH-001` | 获取 Scope Catalog 快照 | `PROPOSED` | [UC-AUTH-001-get-scope-catalog-snapshot.md](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | — | 第一个提供方纵切片；共享线格式见根级平台契约。 |
| `UC-AUTH-002` | 批量读取 Developer 状态 | `PROPOSED` | [UC-AUTH-002-batch-get-developer-statuses.md](use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | — | 为 App Center 审核批准门禁提供 fail-closed 状态查询。 |

## Business Rules

### Scope Catalog (`BR-SCP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SCP-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001) | — | — |
| `BR-SCP-002` | 完整一致快照 | Snapshot / Consistency | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-002) | — | — |
| `BR-SCP-003` | 单调 revision 与生成时间 | Versioning / Audit | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003) | — | — |
| `BR-SCP-004` | ScopeDefinition 投影 | Field / Projection | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) | — | — |
| `BR-SCP-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-005) | — | 服务身份线格式仍待平台决定。 |

### Developer Status (`BR-DEV`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-DEV-001` | Developer 状态权威所有权 | Boundary / Authority | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-001) | — | — |
| `BR-DEV-002` | 有界且唯一的批量输入 | Validation / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-002) | — | — |
| `BR-DEV-003` | 完整结果与 fail closed | Consistency / Failure | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-003) | — | — |
| `BR-DEV-004` | 状态语义 | Field / Projection | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) | — | — |
| `BR-DEV-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-005) | — | 服务身份线格式仍待平台决定。 |

## 维护规则

- UC 使用 `UC-AUTH-NNN`；Scope Catalog 业务规则使用 `BR-SCP-NNN`。
- BR 状态继承其权威 UC，不单独保存状态。
- 新增编号时同时更新 Next ID；废弃编号不得重新分配。
- 同一规则只有一个权威正文；其它 bounded context 通过链接引用。
