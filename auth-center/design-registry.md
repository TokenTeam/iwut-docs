# Auth Center 设计标识符注册表

状态：`ACTIVE`

本文件只索引 Auth Center bounded context 的权威 UC 与 BR，不复制规则正文。跨系统契约位于 `platform/`，不登记为 Auth UC 或 BR。

## 下一个可分配编号

| 编号空间 | Next ID |
| --- | --- |
| Use Case / Auth Center | `UC-AUTH-005` |
| Business Rule / Scope Catalog | `BR-SCP-006` |
| Business Rule / Developer Status | `BR-DEV-006` |
| Business Rule / System Principal | `BR-SYS-005` |
| Business Rule / Reviewer Permission | `BR-RVW-005` |

## Use Cases

| ID | 标题 | 状态 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `UC-AUTH-001` | 获取 Scope Catalog 快照 | `ACCEPTED` | [UC-AUTH-001-get-scope-catalog-snapshot.md](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) | — | 第一个提供方纵切片；共享线格式见根级平台契约。 |
| `UC-AUTH-002` | 批量读取 Developer 状态 | `ACCEPTED` | [UC-AUTH-002-batch-get-developer-statuses.md](use-cases/UC-AUTH-002-batch-get-developer-statuses.md) | — | 为 App Center 审核批准门禁提供 fail-closed 状态查询。 |
| `UC-AUTH-003` | 解析 System Principal | `ACCEPTED` | [UC-AUTH-003-resolve-system-principal.md](use-cases/UC-AUTH-003-resolve-system-principal.md) | — | 为跨服务系统动作提供 Auth-owned opaque actor。 |
| `UC-AUTH-004` | 管理 Reviewer 权限 | `ACCEPTED` | [UC-AUTH-004-manage-reviewer-permission.md](use-cases/UC-AUTH-004-manage-reviewer-permission.md) | — | PLATFORM_ADMIN 管理显式 reviewer grant/revoke。 |

## Business Rules

### Scope Catalog (`BR-SCP`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SCP-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001) | — | — |
| `BR-SCP-002` | 完整一致快照 | Snapshot / Consistency | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-002) | — | — |
| `BR-SCP-003` | 单调 revision 与生成时间 | Versioning / Audit | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003) | — | — |
| `BR-SCP-004` | ScopeDefinition 投影 | Field / Projection | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) | — | — |
| `BR-SCP-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-005) | — | 使用 trusted-service-identity-v1。 |

### Developer Status (`BR-DEV`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-DEV-001` | Developer 状态权威所有权 | Boundary / Authority | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-001) | — | — |
| `BR-DEV-002` | 有界且唯一的批量输入 | Validation / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-002) | — | — |
| `BR-DEV-003` | 完整结果与 fail closed | Consistency / Failure | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-003) | — | — |
| `BR-DEV-004` | 状态语义 | Field / Projection | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) | — | — |
| `BR-DEV-005` | 内部读取边界 | Authorization / Boundary | [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-005) | — | 使用 trusted-service-identity-v1。 |

### System Principal (`BR-SYS`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-SYS-001` | Auth 所有权与不可登录 | Boundary / Authority | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-001) | — | — |
| `BR-SYS-002` | 按 purpose 唯一且稳定 | Identity / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-002) | — | — |
| `BR-SYS-003` | 最小授权解析 | Authorization / Boundary | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-003) | — | — |
| `BR-SYS-004` | 消费方失败关闭 | Failure / Consistency | [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md#br-sys-004) | — | — |

### Reviewer Permission (`BR-RVW`)

| ID | 标题 | 类型 | 权威位置 | 替代项 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `BR-RVW-001` | Auth 权威所有权 | Boundary / Authority | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-001) | — | — |
| `BR-RVW-002` | 管理员不隐式成为 Reviewer | Authorization / Separation | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-002) | — | — |
| `BR-RVW-003` | 乐观并发与不可变审计 | Concurrency / Audit | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-003) | — | — |
| `BR-RVW-004` | 撤销传播上界 | Security / Revocation | [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md#br-rvw-004) | — | — |

## 维护规则

- UC 使用 `UC-AUTH-NNN`；业务规则按能力使用 `BR-SCP/DEV/SYS-NNN`。
- BR 状态继承其权威 UC，不单独保存状态。
- 新增编号时同时更新 Next ID；废弃编号不得重新分配。
- 同一规则只有一个权威正文；其它 bounded context 通过链接引用。
