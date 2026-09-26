<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py --baseline -->
# Brief — 工程基线（跨能力）

> **非权威派生制品。** 跨能力的工程约定，对每个实现工作包都成立；与源文件冲突时以 §溯源 为准。
> 变化很少：读一次后可以长期复用，不必随每个 UC 重新加载。

## 本次范围

| 项 | 值 |
| --- | --- |
| 类型 | 跨能力工程基线（不绑定单个 UC） |
| ADR | `ADR-003`、`ADR-004`、`ADR-005` |
| 变化频率 | 低；仅在架构决定变化时重新生成 |

## 遇到 brief 未覆盖的问题

先查 §未纳入本 brief 的源小节；仍不确定，或发现两条权威规则冲突，产出结构化 gap 并路由给设计任务，不要自行发明。

## 架构决定（仅本次需要的章节）

### ADR-003：Go package 与依赖边界（`ACCEPTED`）

#### 决定

代码首先按业务能力组织，每项能力内部再分 Domain、UseCase 与 Port：

```text
internal/application/domain
internal/application/usecase
internal/application/port
internal/version/domain
internal/version/usecase
internal/version/port
internal/profile/domain
internal/profile/usecase
internal/profile/port
internal/publication/...
internal/tester/...
internal/catalog/...
```

跨能力稳定且确实共享的类型放入小型 `internal/shared` package。只有在至少两个已实现能力出现相同语义时才提升为共享类型，不提前建立通用工具箱。

基础设施放在能力之外：

```text
internal/adapter/mongo
internal/adapter/auth
internal/adapter/transport
cmd/app-center
```

主要依赖方向为：

```text
transport -> usecase -> domain
adapter -> capability port + required domain types
composition root -> concrete implementations
```

Domain 不依赖 Kratos、MongoDB driver、Proto 生成包、HTTP、配置或具体日志实现。UseCase 只依赖 Domain 与当前能力声明的 ports。Adapter 实现 ports，composition root 负责组装。

能力间协作通过显式应用服务、port 或只读 Query 接口完成。一个能力不得直接导入另一个能力的 MongoDB document 或未导出的聚合内部结构。

当前代码树只使用表达业务职责的目录名，不以迁移阶段或实现世代划分代码。

#### Port 所有权

Port 由使用它的能力拥有，而不是由提供方或某个全局 infrastructure package 拥有。例如 Application 创建用例需要的原子持久化接口位于 `internal/application/port`，MongoDB adapter 在外部实现它。

Port 方法使用业务语言并表达所需原子边界，不先建立 `Save/Get/Delete` 式通用 Repository。只有多个实际用例证明通用操作具有相同语义时才抽取。

#### 自动化约束

代码仓库根目录的 `architecture_test.go` 作为 ADR 的可执行护栏，并由 `go test ./...` 自动运行。它至少强制以下规则：

- 业务能力的 Go 文件只能位于该能力的 `domain`、`usecase` 或 `port` package。
- Domain 的项目内依赖只能指向 `internal/shared`，并禁止 MongoDB、HTTP、Proto、配置、JSON 和具体日志依赖及 `bson/json/protobuf` struct tag。
- Port 只能依赖同能力 Domain 与 `internal/shared`。
- UseCase 只能依赖同能力 Domain、Port 与 `internal/shared`。
- `internal/shared` 不得反向依赖任何业务能力。
- Domain、UseCase、Port 与 `internal/shared` 默认不得新增第三方依赖；确需窄依赖时先接受相应架构变更并显式调整测试。
- 已接受的窄例外（2026-09-27，UC-APP-013）：仅 `internal/profile/domain` 可直接导入 `golang.org/x/text/unicode/norm`，用于 BR-PRF-003–005 的纯 NFC 规范化。它无网络、时钟或存储副作用；不扩大到 x/text 其他包、其他能力、UseCase、Port 或 shared。架构测试必须同时覆盖允许位置及这些拒绝位置。
- 具体 adapter package 之间不得互相导入；只有 transport adapter 可以导入 UseCase，MongoDB/Auth 等 provider adapter 只面向能力 Port 与必要的 Domain 类型。
- Adapter 不得读取 `internal/config`；只有 composition root 可以同时依赖配置与具体 adapter。
- 禁止全局 `internal/biz`、`internal/data`、`internal/domain`、`internal/service` 和 `internal/util` package。
- composition root 只位于 `cmd/app-center`。

自动化检查只维护依赖和物理结构，不推断业务语义，也不取代 BR 测试和评审。确有新依赖方向需求时，必须先修改本 ADR，再在同一变更中调整架构测试；不得通过删除、跳过或弱化测试绕过边界。

### ADR-004：MongoDB 事务与 Schema 管理（`PROPOSED`）

#### 决定

App Center 的权威写模型使用支持多文档事务的 MongoDB 部署拓扑。开发、测试和生产至少运行 replica set 或其他被当前 MongoDB 版本明确支持事务的拓扑；不支持事务的 standalone 部署不属于受支持环境。

跨文档 BR 使用 MongoDB transaction 实现，并遵循：

- 事务内只执行本地 MongoDB 读写，不调用 Auth、HTTP、消息系统或其他远程服务。
- 外部校验在事务前完成；BR 要求最终复检的本地事实在事务内重新读取或通过条件写保护。
- transient transaction error 或 unknown commit result 按 MongoDB 官方语义重试完整事务/提交，不单独重试其中一次写入。
- 事务重试使用同一组命令输入、ID 与审计时间，避免一次逻辑操作产生多个身份或时间。
- 唯一索引、条件更新和事务共同保护并发不变量；应用层的预检查只用于改善错误体验。
- Adapter 把 duplicate key、write conflict 和事务失败映射为当前 port 能表达的稳定结果。

Repository port 优先暴露一个完整业务原子行为，例如 `CreateWithinQuota`。当一个 UseCase 必须协调多个独立聚合 Repository 时，可以引入窄的 Transaction Manager，但不能让 Domain 感知 MongoDB session。

#### Schema 与索引

collection、validator、索引和 schema revision 通过显式、版本化、可重复执行的迁移管理：

- 普通服务启动不创建、删除或修改生产索引与 validator。
- 迁移在部署前单独执行，并记录成功的 migration ID。
- 重复执行已成功迁移是安全的。
- 破坏性变更必须先有对应设计决定和恢复方案。
- 新集合从首次创建起使用明确的 validator 与命名索引。
- 集成测试验证实际索引、validator 和事务行为，而不仅测试 mapper。

具体 collection 名由对应 UC 的数据模型和实现工作包确定，不在本 ADR 中建立跨能力的统一 document 形状。

#### 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

### ADR-005：领域错误与 Transport 映射（`PROPOSED`）

#### 决定

Domain 与 UseCase 使用协议无关的稳定错误分类。每个可预期业务失败具有：

```text
stable code
human-readable internal message
optional safe details
optional wrapped cause
```

稳定 code 使用设计文档中的业务失败名称。调用者通过错误类型、code 或 `errors.Is` 判断，不解析 message。

错误分为：

- Validation：输入无法形成合法值对象。
- Authentication：缺少或无效可信身份。
- Authorization：身份存在但没有执行权限。
- NotFound：目标不存在，或按隐私规则必须隐藏归属不匹配。
- Conflict：状态、唯一性、revision、容量或并发前置条件冲突。
- DependencyUnavailable：完成当前行为所需的外部事实暂不可用。
- Internal：未预期的实现或基础设施失败。

MongoDB/Auth 等 adapter 负责把技术错误转换为 port 定义的稳定结果，同时保留 cause。UseCase 再按业务上下文确定最终领域错误。例如 duplicate key 不能直接泄露索引名。

Transport adapter 在一个集中映射表中把领域错误转换为：

- 稳定 Proto error reason；
- canonical gRPC status；
- 对应 HTTP status；
- 可以安全返回的 message/details。

新 API 不采用“所有 HTTP 响应都返回 200，再在 JSON body 中表达错误”的形式。HTTP 与 gRPC 使用各自标准状态语义，稳定业务 code 供客户端做细分处理。

未知错误统一映射为 Internal，不向客户端返回 cause、数据库字段、索引名、远程地址、token、secret 或 stack trace。日志和 trace 在服务端保留原 cause，并使用同一 trace ID 关联。

#### 隐私与存在性隐藏

当 UC 规定跨 Application 的资源归属不匹配按 NotFound 处理时，Transport 不得把内部的“存在但不属于调用者”转换成 Forbidden。存在性隐藏属于业务契约，而不是展示文案。

错误 details 采用明确 allowlist。字段校验可以返回安全字段名和约束类别，但不能回显任意用户内容或凭证。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `4cb59593e39d` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `084c3d26d483` |
