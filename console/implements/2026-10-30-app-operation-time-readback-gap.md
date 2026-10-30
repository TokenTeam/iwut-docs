# App 平台运维的回执与读回时间差异

状态：`CONFIRMED_WIRE_DIFFERENCE / BACKEND_RESOLUTION_PENDING`，2026-10-30。本页记录真实联调事实和建议核查点，不替 App Center 定义新的时间精度规则；Console 严格断言未删除，也没有增加毫秒容差。

## 实际证据

轮次130809冻结 Console `7fa7662`，显式选择治理场景与Tester旧clear场景，实际2项、1通过/1失败、exit1，浏览器阶段35.3秒，无skip/retry。Auth/App重新pull latest仍为518b0917/68ee32b1，Gateway显式本地90cf10f0；完整ID与历史输入见[集中记录](2026-10-30-console-integration-gates.md)。Tester旧overview DELETE204在7.1秒通过，当前待处理项是治理。

治理完成14条Auth管理命令及读回，首次App暂停后严格比较失败，尚未发送App恢复。新增诊断只输出固定字段名和布尔，实际结果如下：

- 唯一不同字段为 `suspendedAt`；两侧均存在。
- applicationId、lifecycleStatus/revision、platformAvailabilityStatus/revision、lastOperationEventId 均相同。
- suspendedAt的seconds相同、nanos不同；换算到毫秒相同。
- ACK含亚毫秒部分，GET不含；restoredAt在两侧均不存在。

这些事实确认了真实镜像的时间表示差异，不只是本地源码推测。没有把目标ID、事件ID、原始时间、Session、个人正文或响应体写入日志和文档。

## 权威与建议核查

运维业务权威是 App [UC028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md) 中的原子审计规则（BR-APP-036）。该流程要求同次Clock取得操作时间、原子提交并返回状态；Proto使用具体的 `google.protobuf.Timestamp`。目前文档没有明确ACK/GET的精度量化约定，不能由Console把不同nanos自动视为同一瞬间或默认允许任意漂移。

本地App源码的核查线索为 `internal/adapter/mongo/application_operations_repository.go`：事务将同一now写入应用、事件和outbox，随后以内存中的原始now构造返回值；BSON Date持久化只保留毫秒。`SystemClock.Now()`保留亚毫秒，能够解释本轮已观察到的差异，但修复仍应由App所属工作核查。

建议在写入边界为本次操作一次确定实际持久化精度的时间，并让应用状态、不可变事件、outbox和ACK使用同一值；或提出同样能保证事务返回一致性的方案。不要用事务后无版本的额外读取拼成ACK，以免并发操作改变返回目标。增加真实Mongo回归：注入含非零亚毫秒的Clock，比较命令ACK、同event/revision的GET、事件和outbox，保留现有原子性/幂等断言。前端不代改业务规则，不编译App源码，不以代理补写时间或删断言取得绿结果。

## 待交接的具体请求

请求App agent核查上述真实现象与持久化边界；若属实，在自己的仓库补必要文档/回归并修复，按其既有流程构建和发布镜像。Console随后重新pull latest，复验原治理场景及完整门禁，不改为固定旧镜像规避差异。

用户在了解实链差异后明确要求“让后端修改一下，统一时间”。本问题已发送至 `app-center` 聊天（`01a137d2-5901-7a93-85c5-a7eb59328d86`），请求同时核查暂停/恢复、状态/event/outbox/ACK一致性及真实Mongo回归，按后端既有流程反馈提交与镜像状态。当前仍等待后端修复，不能把消息送达当作已经修复或发布。本次授权针对这一问题，不自动扩大为后续所有缺陷或新的业务设计；Console版本闭环继续独立推进。
