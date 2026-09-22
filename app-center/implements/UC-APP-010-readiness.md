# UC-APP-010 开工检查

检查日期：2026-09-22。本文记录实现准备，不定义业务规则。

## 依赖结论

- [UC-APP-009](../use-cases/UC-APP-009-join-application-as-tester.md) 后端已完成：Membership episode、ACTIVE/REMOVED 字段组合、0010 migration、ACTIVE partial unique index 和事务内 ACTIVE 统计均已具备。
- UC-APP-008/009 共用 Application `coordinationRevision` 写栅栏；移除可复用，管理员最终校验与移除/加入并发必须在同一串行化协议下验证。
- 可信 DeveloperIdentity、APPROVED 校验、Clock、Proto/Wire 和真实 MongoDB 副本集测试基础设施已具备。
- UC-APP-010 不需要独立计数器，也不预设新增 migration；只有现有 schema 无法承载当前契约时才增加迁移，不修改已交付迁移历史。
- Tester 管理列表与分页属于独立读模型，不阻塞当前按 applicationId/membershipId 移除命令；生产前端和 Gateway 身份链路独立交付。
- 不依赖 UC-APP-011 撤销链接或 UC-APP-012 启动目标解析。

## 已确定的对外契约

- **authority**：[UC-APP-010 API 草图](../use-cases/UC-APP-010-remove-application-tester.md#api-草图)。
- **resolved**：用户于 2026-09-22 确认 `ApplicationTesterStateInconsistent` 使用 HTTP 500 / gRPC INTERNAL，表示内部数据不变量异常；保留稳定 reason，不泄露底层数据。
- 原先两种 HTTP 映射选项已从权威正文消除，没有剩余的开工设计阻塞。

## 实现注意事项

- activeTesterCount 来自同一事务内的 ACTIVE episode 统计；ACTIVE → REMOVED 自然释放名额，不引入另一份计数事实。
- 已 REMOVED 候选不读 Clock、不覆盖移除审计；仍须按 BR-TST-020/022 校验当前管理员，结果中的 count 与 activeJoinLinkExists 必须来自一致快照。
- 按 membershipId 精确更新，旧 episode 的重复请求不得影响重新加入的新 episode。
- 保留 count 不变量检查；原“ACTIVE 且计数为 0”验收不能通过制造一个不存在的独立计数器实现，可在领域/端口异常测试验证防御分支，真实 MongoDB 验证统计、回滚和并发正确性。
- 重点验收双重移除、移除/重新加入的双向顺序、管理员转让竞争、容量释放、旧 episode 幂等、链接提示和审计不变性。

## 工作包状态

UC 已设为 ACCEPTED；使用 `tools/brief-specs/UC-APP-010.json` 脚本生成 brief，代码仓库 AGENTS 切换至 UC010，交由实现 subagent 完成当前后端工作包。
