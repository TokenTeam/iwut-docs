# ADR-004：MongoDB 事务与 Schema 管理

状态：`ACCEPTED`

日期：2026-09-19

## 背景

现有 BR 包含多项跨文档原子要求，例如 Application 创建与配额占用、Version 与 Review 状态同步、Profile 工作指针与审核决定、Tester 容量竞争，以及 Publication 当前状态与历史记录。

仅依赖“先写 A，再写 B”的 Repository 调用无法满足这些不变量。进程内锁也不能覆盖多实例部署。与此同时，唯一索引、partial index 与 collection validator 是业务保护的一部分，需要有可重复、可审查的管理方式。

## 决定

App Center 的权威写模型使用支持多文档事务的 MongoDB 部署拓扑。开发、测试和生产至少运行 replica set 或其他被当前 MongoDB 版本明确支持事务的拓扑；不支持事务的 standalone 部署不属于受支持环境。

跨文档 BR 使用 MongoDB transaction 实现，并遵循：

- 事务内只执行本地 MongoDB 读写，不调用 Auth、HTTP、消息系统或其他远程服务。
- 外部校验在事务前完成；BR 要求最终复检的本地事实在事务内重新读取或通过条件写保护。
- transient transaction error 或 unknown commit result 按 MongoDB 官方语义重试完整事务/提交，不单独重试其中一次写入。
- 事务重试使用同一组命令输入、ID 与审计时间，避免一次逻辑操作产生多个身份或时间。
- 唯一索引、条件更新和事务共同保护并发不变量；应用层的预检查只用于改善错误体验。
- Adapter 把 duplicate key、write conflict 和事务失败映射为当前 port 能表达的稳定结果。

Repository port 优先暴露一个完整业务原子行为，例如 `CreateWithinQuota`。当一个 UseCase 必须协调多个独立聚合 Repository 时，可以引入窄的 Transaction Manager，但不能让 Domain 感知 MongoDB session。

## Schema 与索引

collection、validator、索引和 schema revision 通过显式、版本化、可重复执行的迁移管理：

- 普通服务启动不创建、删除或修改生产索引与 validator。
- 迁移在部署前单独执行，并记录成功的 migration ID。
- 重复执行已成功迁移是安全的。
- 破坏性变更必须先有对应设计决定和恢复方案。
- 新集合从首次创建起使用明确的 validator 与命名索引。
- 集成测试验证实际索引、validator 和事务行为，而不仅测试 mapper。

具体 collection 名由对应 UC 的数据模型和实现工作包确定，不在本 ADR 中建立跨能力的统一 document 形状。

## 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

## 考虑过的替代方案

### 使用补偿写代替事务

会暴露中间不一致状态，并要求每个用例设计恢复协议。当前服务的相关事实位于同一 MongoDB 边界，没有承担该复杂度的理由，因此不采用。

### 使用 Redis 锁保护 MongoDB 写入

增加第二个故障域，仍不能让多次 MongoDB 写入原子提交，也无法替代唯一索引，因此不采用。

### 服务启动时自动创建索引

本地开发方便，但生产启动可能产生长时间锁、权限扩大和多实例竞态。索引由显式迁移管理，服务启动只验证必要能力并在缺失时失败或告警。

## 结果

优点：

- BR 中的跨文档原子性有明确实现基础。
- 并发正确性不依赖单进程假设。
- Schema 变化可审查、可重复、可测试。

代价：

- 本地和 CI 必须运行支持事务的 MongoDB。
- 需要迁移工具与集成测试基础设施。
- Repository adapter 必须正确处理事务重试和错误分类。

## 关联文档

- [领域模型](../domain-model.md)
- [生命周期模型](../lifecycle-models.md)
- [统一实现约定](../implements/implementation-conventions.md)
