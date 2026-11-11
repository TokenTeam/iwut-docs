# 独立 App 运维人员：本人精确权限发现提案

状态：`ACCEPTED / AUTH_BACKEND_PUBLISHED`；2026-11-04 用户明确接受并授权实现。此前设计审核草案已展开为正式 UC 修订并获接受；先生成 brief，再按 API/Auth → Gateway → Console 串行实施；当时未授权自动 commit/push。此前提案提交 `0e7e326`、`fed6c72` 仅是提案历史，不是 API 发布或功能交付。最新实现与验证见 [readiness](UC-AUTH-027-own-read-readiness.md)。

## 权威设计入口

- [UC-AUTH-027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)：本次已接受修订，新增本人最小读取，含 API/消息、流程、错误、依赖检查与验收。既有管理员 Get/Manage 的 ACCEPTED 基线保留。
- [BR-AOP-007](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-007)、[BR-AOP-008](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-008)：本人公开范围完整有效 ID 集合，以及同次观察/失败关闭的唯一规则正文。
- [UC-CONSOLE-015](../../console/use-cases/UC-CONSOLE-015-manage-platform-governance.md#本人运维能力发现本次修订)：本次已接受消费修订，独立于完整管理员发现、精确动作控制与 Session/attempt/确认隔离；旧受限交付行为保留。
- [路由增量](../../platform/contracts/auth-center-api-routing.md#uc027-本人运维权限读取)：API/Auth → Gateway → Console 的精确路由与信任边界交接，不是已接入清单。
- [生成 brief](../briefs/UC-AUTH-027.md)：已在用户接受后脚本刷新，是本次实施输入。

本文只记录缺口证据、取舍与交接，不重复定义 API 字段、权限规则或 Console 行为；冲突时以上方权威正文为准。

## 缺口与只读证据

Auth `bddd98f` 的 `UserCapabilityIdentityMiddleware` 将现有运维权限方法分派到管理员能力检查，`ApplicationOperationsPermissionRepository.Get/authorize` 在事务内再次执行 `RequireAdministratorTx`；即使目标是本人也不例外。管理 `snapshot()` 还会查询邮箱/恢复及管理门禁，不适合作为普通 USER 本人读取路径。

App `a95bd13` 的 [UC028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md) Get 只要求 suspend OR restore，返回 Application 可用状态，不返回具体权限。成功读取不能据此开启两项写操作。

Gateway `9d6a27f` 已有精确 ADMIN/SESSION 路由与 typed proxy；API `6fea3db` 仍只有管理 Get/Manage。Console `bd43c3a` 的 `OperationsDiscovery` 先确认完整管理员资格，`ExactOperationsDiscovery` 才能读取自己两项权限；非管理员运维人员保留按已知 App ID 读取，写动作不开放。这些是本地 HEAD 源码证据，不是远端部署或新链验收。

## 方案取舍

选择新增独立本人只读 RPC，不给旧目标 Get 加 actor=subject 特例。这样无需目标输入或管理资源中的 granted/grantBlockers，不混合普通用户发现与管理员授权，也不会降低原 Get/Manage 门槛。

响应采用有效 permission ID 集合，而非逐项布尔值；首版只公开两项 App 运维权限，合法 ACTIVE USER 无此权限时成功空集合。后续新增公开 ID 必须单独审核；本轮不建设通用权限目录。

不扩大 Auth audience permissions allowlist，不解析 App audience JWS，不把权限放进 BrowserSession，不让 BFF 聚合或计算权限。App 写命令保持独立精确鉴权、双 revision 与既有短期身份撤权窗口。

## 审核点与后续交接

1. **用户审核已完成**：本轮明确接受 UC027/UC-CONSOLE-015、BR-AOP-007/008 和路由修订；不是从旧 ACCEPTED 推断授权。
2. **API / Auth**：审核后复核依赖、标为 ACCEPTED、脚本重新生成 brief；固定 Proto 输入/输出，再实现精确普通 USER 分派、在线账号版本确认和同次完整集合投影。旧 Get/Manage 的授权与回归保留。
3. **Gateway**：消费固定新增 API 提交，追加精确 route、descriptor、typed proxy 与生成物，验证三协议及 ADMIN HTTP surface Session 链；复用既有 UC-GW-001/007，不新增身份策略或通配授权。
4. **Console**：审核消费修订并固定新客户端输入，独立调用本人读取；只启用认识的精确动作，严格区分成功 [] 与失败。新链完成前仍保留旧受限行为。
5. **联合验收**：按 Auth → Gateway → Console 串行完成四组合、授撤、Session/账号代际、协议/失败、确认/迟到响应矩阵，固定各提交/镜像。App 后端无需新增接口或改变 UC028 写授权。

接受前依赖结论为设计可闭合。用户现已接受并授权实施，依次进行 API/Auth、Gateway、Console；未完成的固定 API 输入与真实链门禁仍显式保留，不自动 commit/push、部署或发送跨聊天消息，保护 resource-hub。
