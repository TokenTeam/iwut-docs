# UC041 实施准备与 Auth 权限交接

2026-11-06：设计 `ACCEPTED`；[实施 brief](../briefs/UC-APP-041.md)已生成。本文保留首轮 Auth 交接。Auth 已在本地补齐权限授撤与签发，原依赖检查已解除；App 当前状态、API 固定版本依赖和下一步见 [UC041 实施记录](UC-APP-041-script-resource-implementation.md)。

## 初始阻塞（历史）

- **Authority**：[UC041 / BR-SCR-002](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002) 规定：创建资源、替换元数据需要可信 ACTIVE USER 和精确 `app.script.maintain`。App 使用现有 `iwut-app-center` audience 的短期 USER JWS；Auth 拥有权限授予、撤销与签发投影。
- **Conflict**：本地 Auth `bddd98f` 及其当前工作区的 App audience allowlist 只投影 `app.application.restore`、`app.application.suspend`、`app.profile.review` 和 `app.version.review`。见 [Auth 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md#应用审核权限投影)及 `iwut-auth-center/internal/identity/domain/identity.go` 的 App audience 分支。即使签发输入已有 `app.script.maintain`，该分支也会过滤；当前未找到该权限的正式授予/撤销和签发路径。未运行新功能的联合测试。
- **Options**：由 Auth 增补精确权限的正式管理和签发；或者重新评审并改变权限模型。复用已有 Reviewer/运维权限、给平台管理员隐式授权、由 App 伪造身份均与已接受设计冲突。
- **Suggested**：保持已接受权限模型，先交付 `app.script.maintain` 的真实授予/撤销及签发；如 Auth 所有者更适合一次交付五项，可同步完成下表，其余四项不阻塞 UC041 的恢复。既有本人运维权限查询工作不需要为本项改口径。

## Auth 所有者可接手的内容

请在 Auth 一侧设计相应 UC/权限管理、持久授权和 App audience 投影；按需同步其权威共享契约。沿用现有身份发行链路，无需新 audience、USER JWS claim 或运行时客户端自报权限。

| 精确权限 | App 侧消费 |
| --- | --- |
| `app.script.maintain` | UC041 资源维护、UC042 草稿维护、UC043 提交 |
| `app.script.review` | UC044 脚本决定、UC045 相关审核查询 |
| `app.script.publish` | UC046 发布与清除推荐指针 |
| `app.script.suspend` | UC046 暂停分发 |
| `app.script.restore` | UC046 恢复分发 |

**解除 UC041 阻塞的证据**：提供可用于联合验证的 Auth 修订及测试入口。用真实受支持的身份签发链验证同一 ACTIVE 用户在未授予、正式授予和正式撤销后新签三种情形，`permissions` 分别无、有、无 `app.script.maintain`；已签发短期 JWS 的残余窗口沿用现有契约。独立验证现有 App Reviewer、Developer、普通 Application 管理员和完整平台管理员无隐式授予；权限不进入错误 audience，且既有四项投影不回归。

后续 UC044/049 需要另确认 `APP_CENTER_REVIEW_AUTO_REJECTION` 是否覆盖脚本依赖自动拒绝，能复用则保留现有解析 RPC 和 SYSTEM ID。这个确认属于后续工作包，无需为 UC041 增加 SYSTEM 依赖。

## 原交接约定的 App 验收顺序

1. 恢复 UC041：实现资源创建/元数据替换、精确权限检查及 MongoDB OCC，落定该工作包的 Proto/HTTP/gRPC 接口。保持 UC042 及后续脚本逻辑在各自工作包。
2. 验证同名不同 ID、无权与不存在的边界、并发替换最多一项成功、失败不留部分写入；用正式 Auth 授予、签发和撤销串起联验，并运行规定的后端门禁。Gateway 与 Console 接线仍由各自所有者负责。
3. UC041 所需验证通过后再进入 UC042。当前未修改 App 生产代码、共享 API 或其他模块，未提交或推送。
