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

## 政策发布回执与恢复

2026-11-03 用户确认业务改为提交时固定政策；对应 UC004/005/015/016/030/031 修订已于 2026-11-04 ACCEPTED。本 ADR 的通用本地事务、显式迁移、重试与历史保护规范保持 ACCEPTED；本节撤下 2026-10-26 仅服务于“退休打断决定”的工程要求，具体业务方案由已接受 UC 拥有，用户已授权本次实施。

- 新提交与政策发布的一致性方案引用 [UC004 策略绑定与提交并发](../use-cases/UC-APP-004-submit-application-version-review.md#策略绑定与提交并发)。关键原子保护对象从“退休与决定”移到“政策选择与新提交”；决定不为退休写全局政策栅栏。
- 专用发布 migration 的最小同事务标识、清单核对与 unknown commit 恢复，引用 [UC005 正式发布与运维读回](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)。首次初始化按新模型建立账本；通用 apply 后记账不能单独证明未来政策切换原子成功，需在专用实现时验证衔接。
- 不再要求为此建设通用政策发布 CLI、policy-status 服务或扩展整套治理回执状态机；仍以现有受控迁移/发布审计承载最小恢复证据。不把不同 migration 的重入当作历史重新激活。
- 用户确认尚未上线，按 [UC005 新模型初始化](../use-cases/UC-APP-005-decide-application-version-review.md#新模型初始化与运行门禁)建立完整数据与夹具；删除旧记录过渡、分批回填、维护窗口及新旧版本双读方案。本轮没有执行数据库操作。
- 技术验收围绕提交/发布两个胜序、同 ID 重入、未知提交、无部分绑定和不可变历史；旧“切换先提交则旧决定409”不再是目标。正式联合验收仍不能直接改库或制造同义生产政策。

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
