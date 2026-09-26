# UC-APP-013–015 统一开工检查

检查日期：2026-09-27。本文记录准备情况；业务以 UC/BR、技术边界以 ADR 为准。

## 结论

无尚未满足的外部实现依赖或需用户追加决策的业务阻塞。三条设计接受后，严格按照013 → 014 → 015串行实现；每步必须通过完整 backend 验收，再激活下一步。

## 依赖与证据

| 用例 | 前置条件 | 结果 |
| --- | --- | --- |
| 013 | Application / APPROVED Developer 身份、技术序号、管理员事务保护、双协议与迁移设施 | UC001及现有 Mongo adapter 已提供 nextProfileRevisionSequence=1 和 validator；共享 coordinationRevision 写栅栏已由008–011验证。可立即开始。 |
| 014 | 013资料值对象、修订、工作指针、schema与API | 当前尚未实现；作为串行内部依赖，必须等待013完整验收。 |
| 015 | 013持久化资料与014编辑/OCC | 当前尚未实现；必须等待014完整验收。Review schema和提交原子操作由015本身交付。 |
| 外部 | Auth Scope Catalog、URL预检、UC016审核决定 | 不属于三条命令前置依赖，不引入这些调用。 |
| 客户端 | 管理读模型、前端、Gateway | 独立交付；不把完整管理流程或响应丢失后的查询恢复宣称已完成。 |

## 已补齐的实现契约

- ADR003只为 profile/domain 的纯NFC处理放行精确的 x/text/unicode/norm 依赖，同步架构护栏正反测试；不扩大其余边界。
- 013严格完整字段与显式null绑定、Profile集合/指针和唯一工作位；已有Application计数器直接复用。
- 014沿用编辑的If-Match与412、gRPC expected_revision和ABORTED；规范化no-op仍做最终权限、状态、revision和指针检查。
- 015沿用现有提交审核的正文expectedRevision及资源POST。已SUBMITTED的重复命令返回NotDraft；DRAFT与Review/工作指针不一致沿用用户已确认的500/INTERNAL及安全告警。
- 015补齐真实“编辑 vs 提交”竞争测试；每条均验收回滚、管理员转让竞争、非法输入与HTTP/gRPC一致性。

## 工作纪律

由主任务维护设计来源和激活顺序，实现subagent独占当前服务/API修改；不得提前实现下一UC。每步运行make check-full，来源冻结后验收，API先提交再提交服务gitlink；交付BR覆盖、报告、commit与遗留边界，所有提交保留本地。
