# UC-APP-011 开工检查

检查日期：2026-09-23。本文是实现准备记录，不定义业务规则。

## 依赖结论

- UC-APP-008 已提供链接领域模型、hash 脱敏、持久化历史、唯一 ACTIVE 索引、原子轮换和 Application `coordinationRevision` 写栅栏。
- 已交付的 0009 schema 和领域恢复逻辑均支持 REVOKED/MANUAL，且要求 replacedByJoinLinkId 为空；本次需要新增显式撤销行为，不需要为了 UC 编号新增 migration。
- UC-APP-009 的最终加入事务在取得同一 Application 写栅栏后重新校验链接 ACTIVE 状态，因此可与撤销事务按提交顺序串行化。
- UC-APP-010 已提供同类“当前管理员 + 精确 episode + 幂等无 Clock”的实现范式和安全告警方式；011 不读取或修改 Membership，不依赖010移除调用。
- 可信 DeveloperIdentity、APPROVED 校验、Clock、Proto/Wire 和真实 MongoDB 副本集设施均可复用。
- 不依赖测试发布、Auth Scope Catalog、UC-APP-012 解析、前端或生产 Gateway 身份签发先完成。

## 设计处理

- 沿用用户已确认的内部数据不变量异常规则：ApplicationTesterJoinLinkStateInconsistent 映射为 HTTP 500 / gRPC INTERNAL，并保留稳定 reason 与不含凭证的服务端告警。
- 沿用 UC008/009/010 共用 Application 写栅栏与 snapshot/majority 事务；重试不得更换目标 joinLinkId，不得顺着 replacedByJoinLinkId 撤销新链接。
- 已 REVOKED 候选的幂等快捷结果仍须在写栅栏和一致快照中验证当前管理员；不读 Clock、不改写原 ROTATED/MANUAL 原因、审计或替代关系。
- 撤销先提交时，等待中的加入必须失败；加入先提交时，Membership 保留。轮换先提交时返回旧 ROTATED 终态；撤销先提交时旧 expectedActiveJoinLinkId 轮换失败。
- 当前没有需要新增用户决策的业务分歧。平台和前端边界继续独立交付。
