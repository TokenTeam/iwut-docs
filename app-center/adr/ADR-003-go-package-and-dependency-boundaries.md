# ADR-003：Go package 与依赖边界

状态：`ACCEPTED`

日期：2026-09-19

## 背景

App Center 包含 Application Ownership、Version Review、Public Profile、Runtime Publication、Tester Management 与 Catalog & Resolution 等能力。它们处于同一 Bounded Context，但拥有不同聚合、生命周期和外部依赖。

若按框架技术层建立全局 `biz/data/service/util` package，所有领域对象会逐渐汇集到少数大包中，能力间可以绕过应用层直接访问彼此内部状态，Repository 也容易退化为通用 CRUD。这会削弱现有 Capability Map 与聚合边界。

同时，新实现需要保持 Domain 可独立测试，不让 Kratos、MongoDB 或 Proto 类型决定业务模型。

## 决定

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

## Port 所有权

Port 由使用它的能力拥有，而不是由提供方或某个全局 infrastructure package 拥有。例如 Application 创建用例需要的原子持久化接口位于 `internal/application/port`，MongoDB adapter 在外部实现它。

Port 方法使用业务语言并表达所需原子边界，不先建立 `Save/Get/Delete` 式通用 Repository。只有多个实际用例证明通用操作具有相同语义时才抽取。

## 自动化约束

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

## 考虑过的替代方案

### 全局 biz/data/service 分层

与常见框架模板一致，但能力边界只能依靠约定维持，容易形成大包和跨聚合直接访问，因此不采用。

### 每个聚合独立 Go module

物理隔离强，但当前规模下会增加版本、依赖、CI 和本地开发成本。先使用同一 module 内的 `internal` package；未来只有出现独立发布需求时再评估。

### 所有领域类型放入一个 domain package

初期文件少，但最终会产生全局模型并放大循环依赖，因此不采用。

## 结果

优点：

- 代码结构与 Capability Map 对齐。
- Domain 与 UseCase 可以脱离基础设施快速测试。
- Port 的原子语义靠近使用它的业务规则。
- 后续增加能力时不需要扩大全局 `biz` 或 `util`。

代价：

- Adapter 需要显式 mapper 和较多小接口。
- 跨能力查询需要明确的组合层，不能直接读取内部 Repository。
- 初期目录数量多于简单框架模板。

## 关联文档

- [Capability Map](../capability-map.md)
- [领域模型](../domain-model.md)
- [统一实现约定](../implements/implementation-conventions.md)
