# UC-APP-016 开工检查

检查日期：2026-09-27。本文记录实现依赖和待决事项；业务以 UC/BR 为准。

## 当前结论

UC013–015 的本地前置实现已完成。用户已确认首版策略，UC016 已 ACCEPTED；在当前 App Center consumer 范围内无未满足的实现依赖，可以生成 brief 并启动实现。

已确认：不可变版本 `app-profile-review-v1`，固定要求 `content-policy-reviewed` 与 `icon-content-reviewed`；icon 为空时后者确认不适用。首版始终要求两项，正式 migration 写入不可变定义。

## 依赖核对

| 依赖 | 当前证据与结论 |
| --- | --- |
| ProfileRevision、编辑、PENDING Review | UC013–015 已完成；服务 `3a87a0f`、API `a0c158c`，前轮完整 backend 验收已通过。 |
| 最终事务保护 | 现有 Application `coordinationRevision` 写栅栏可复用；决定须在同一事务内加载和复查管理员、Revision、Review、工作指针与公开指针。 |
| 可信 Reviewer 身份 | App Center `internal/adapter/transport/identity.go` 接受通用 permissions；无须 Developer 资格。新入口必须精确检查 `app.profile.review`，不得使用版本审核权限代替。 |
| Auth 正式授权和签发 | Auth `internal/reviewer/domain/permission.go` 当前只定义 `app.version.review`；`internal/identity/domain/identity.go` 对 app-center audience 也只投影该值。生产资料 reviewer 链路尚未闭合，不应将签名测试 token 验证描述为真实 Auth 资料权限签发验收。 |
| 平台契约 | `platform/contracts/trusted-identity-v1.md` 的 Claims 已同步资料权限消费语义。因涉及共享身份契约，最终执行 `make check-auth-app`，并明确该回归不证明尚未实现的资料权限签发。 |
| 本地策略 | 当前无 ProfileReviewPolicy 实现；由本 UC 建立独立不可变策略和 migration，不复用运行版本策略的业务检查项。 |
| 其它外部服务 | 不依赖 Scope Catalog、DNS、资产检查、System 自动拒绝或运行版本发布；管理查询、前端、生产 Gateway 和 Auth 权限管理独立交付。 |

## 实现时必须闭合的边界

- 一次性决定必须同时写入 Review decision/status、Revision status/revision/audit、清空工作指针；批准同时条件更新公开指针，拒绝保留旧公开指针。
- 策略状态必须在最终原子边界复查并有真实并发保护；只读事务快照不能证明与并发 RETIRED 更新串行。保留策略定义不可变，技术协调字段与策略内容分离。
- REJECT 跳过内容复检，但不能跳过结构、归属、快照相等、sourceRevision、attempt 和指针不变量检查。现有严格恢复函数不能在拒绝之前无条件执行内容校验。
- 新 migration 同时升级 Revision 与 Review validator：REJECTED 内容仍要求完整字段和 string/string-or-null 类型，但不以内容长度或字符规则阻止保存拒绝事实；其它状态保持严格内容约束。不得使用运行时 bypassDocumentValidation，也不得自动规范化历史快照。
- 原有已提交 API 的 ReviewRecord.decision 字段为 `google.protobuf.Value`，必须保留字段类型和编号，仅扩充合法输出对象契约。新 RPC 采用显式 command body 与匹配的路径 json_name，并验证真实生成 HTTP 客户端。
- 真实 Mongo 验收覆盖并发决定、管理员转让、策略退休、公开指针冲突、事务回滚、拒绝坏内容、释放工作位后创建新草稿、revision 溢出与脱敏告警。
- 在来源冻结后运行完整验证；API 先本地提交，再提交服务 gitlink。未获额外授权不 push，不扩展后续 UC。

## 后续步骤

已更新 UC016 与共享契约并登记 ACCEPTED；接下来脚本生成 brief，切换服务 AGENTS.md 工作包，启动实现 subagent；主任务审查并运行完整验收，最后记录提交与遗留边界。
