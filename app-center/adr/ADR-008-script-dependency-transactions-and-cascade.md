# ADR-008：脚本依赖同库事务与拒绝级联

状态：`ACCEPTED`

## 背景

脚本正式纳入 App Center，同服务同库已由用户确认。[UC048](../use-cases/UC-APP-048-manage-application-script-dependencies.md) 要求允许待审引用但禁止拒绝后新登记待审依赖；[UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 要求可靠处理所有依赖。MongoDB 快照事务中只读脚本再写不同文档，不能阻止写偏斜。

## 决定

沿用 [ADR004](ADR-004-mongodb-transactions-and-schema-management.md) 的 MongoDB 副本集事务、显式 schema migration 和有界重试；不新增 Resource Hub、数据库、服务 audience 或跨服务事务协议。

1. 在 ScriptVersion 权威文档维护 adapter-only dependencyFence。App 送审对所有依赖按确定 ID 顺序做真实条件递增，条件为精确身份/摘要及允许状态，再在同事务创建 AppReview、迁移 Version、写入每个反向依赖。脚本批准/拒绝写同一权威文档，产生真实写冲突并重试；只读、no-op `$set` 或仅插独立依赖行不能充当栅栏。
2. 拒绝决定与唯一持久 cascade task 同事务写入。任务内有源决定 ID、状态、lease、分页进度和失败观测；没有内存通知依赖。worker 以稳定键集分批扫描不可变反向依赖，逐目标条件事务终结，App 原有 writer 共享既有栅栏/锁序，不建立第二个 App 决定通道。
3. 反向依赖唯一键为 `(appReviewId, scriptVersionId)`，查询索引以 scriptVersionId 为首列；任务源 scriptDecisionId 唯一。历史关系保留，当前 Review 状态决定是否需处理。分批后重新验证无 PENDING 目标才能 COMPLETE；已拒绝状态和送审真实写栅栏保证不会有后来的合法登记。
4. App 最终批准在同一决定事务校验固定脚本批准事实。脚本已批准为不可变终态，故无后续拒绝翻转；仍核对一致的身份、摘要和决定关系。分发暂停使用独立 availability 文档/栅栏，不复用不可变审核结果。
5. Script Publish 与 Suspend 通过同一资源 gate 的真实条件写串行化。App 发布在原 Publication 事务中按确定资源顺序消费该 gate 栅栏，核对精确版本的已发布事实；在线解析/内容读取采用一致快照，响应可线性化在暂停前或后。不能把跨请求缓存当作实时 gate。

具体 collection/schema、索引名、批大小、lease 和重试参数在对应 UC 的实施工作包中落定。栅栏溢出、关联缺失、摘要不符必须失败关闭。

## 替代方案与后果

- 前端先后点击、只读检查、异步登记依赖：无法排除拒绝完成后漏入待审，舍弃。
- 一次拒绝把全部应用放进大事务：依赖数量无界，舍弃；采用持久任务并明确 ACK 只代表义务已保存。
- 拆 Resource Hub 与分布式补偿：不符合已确认服务归属，当前不采用。

收益是安全 gate 立即生效且级联可恢复；代价是同一脚本的并发送审争用、额外写索引/任务运维，以及短暂的“脚本已拒绝、应用待自动拒绝”状态。须通过真实 MongoDB 两种提交胜序、崩溃恢复、重复与终态竞争证明，不以 mock 代替并发证据。
