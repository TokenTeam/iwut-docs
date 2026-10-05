# UC-AUTH-023：暂停与恢复 Developer 资格

状态：`PROPOSED`

## 目标与范围

管理员暂停或恢复指定 authId 的 Developer 资格，保留普通账号使用能力、developerHandle 和应用归属。暂停限制开发者行为，不等同于禁用账号、注销、应用下架、撤销 reviewer 权限或撤销所有应用用户的 OAuth 授权。

本用例只支持 APPROVED 与 SUSPENDED 之间的转换，不批准 PENDING、不恢复 REJECTED，不重新开通 UC024 的 WITHDRAWN。没有定时自动恢复。

## 参与者与 API 草案

操作人使用 Gateway SESSION 换取面向 Auth 的 USER JWS，必须是当前 ACTIVE、账号版本匹配且具备 UC021 完整管理员集合和 `auth.developer.manage` 的 USER。目标可以是 ACTIVE 或 DISABLED USER；改变其 Developer 资格不会改变账号状态。

```text
ManageDeveloperStatus {
  subjectAuthId: AuthId
  action: SUSPEND | RESTORE
  expectedDeveloperRevision: Int64  // 必填，正数
  reason: String                    // trim 后 1..1024 UTF-8 bytes
}
GetManagedDeveloperStatus { subjectAuthId: AuthId }
ManagedDeveloperStatus {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED | WITHDRAWN
  developerRevision: Int64
  statusChangedAt: Instant?
}
```

独立 package `auth_center.v1.developer_management`，service `DeveloperManagementService`：

| 方法 | Auth HTTP 路径 | 结果 |
| --- | --- | --- |
| ManageDeveloperStatus | POST /v1/developers:manage-status | 200，ManagedDeveloperStatus |
| GetManagedDeveloperStatus | POST /v1/developers:get-managed-status | 200，ManagedDeveloperStatus |

HTTP 与原生 gRPC 同时交付，Gateway 外部前缀 `/auth-center`，精确登记方法；只接受 trusted USER JWS，不以 service/OAuth token 或直接 Session 替代。ProtoJSON、optional revision、UTC Timestamp、16 KiB 上限、无 query、拒绝未知/重复字段；no-store。查询不返回邮箱、学生关联、审核理由或应用清单。

## 主流程

1. 验证输入与操作人身份，在 Auth 全局认证事务协调边界内在线复核其当前管理资格。
2. 读取目标合法 Developer 状态及 developerRevision，校验 expectedDeveloperRevision。
3. SUSPEND 要求 APPROVED；RESTORE 要求 SUSPENDED。恢复还需当前激活邮箱和 UC013 的邮箱恢复部署就绪条件。
4. 若存在未提交的 Developer 退出/账号注销操作，按 BR-DEV-015 处理，不能与终止资格竞争提交。
5. 原子更新状态、developerRevision、归因/时间并追加独立生命周期审计，确认提交后返回。

## 业务规则

<a id="br-dev-013"></a>
### BR-DEV-013：独立资格与单调版本

普通 USER 的 developerRevision 初始为 0，首次 UC013 开通时变为 1；已有非 null Developer 状态必须有正 int64 revision。后续暂停、恢复和 UC024 退出每次成功严格递增，版本耗尽拒绝。不是 permissionRevision、accountRevision 或 developerHandle 版本。

SUSPEND/RESTORE 是显式状态转换，重复操作和过期 revision 均冲突，不产生重复事件。恢复要求已有激活邮箱及恢复能力就绪，暂停不依赖邮件配置。null 不是待批准 Developer；PENDING、REJECTED、WITHDRAWN 不通过此入口转为 APPROVED。首版无历史数据补齐迁移。

<a id="br-dev-014"></a>
### BR-DEV-014：保留普通功能与传播边界

不递增 accountRevision，不撤销 Session、邮箱或设备密钥，不改变普通用户的资料、作为应用用户的历史 grant 或独立 reviewer/管理员权限。管理员即使暂停自身 Developer 资格也仍可管理平台，权限由对应 UC 判断。

新的 UC010 App audience 身份携带当前 Developer 状态；Auth OAuth 所有者检查读到 SUSPENDED 时拒绝该所有者应用的相关签发/使用。普通用户功能不要求 Developer APPROVED。

App 只允许 APPROVED 的开发写入口在新身份下拒绝；已有离线验签的短期 Developer JWS 存在原 TTL/leeway 窗口，暂停不提供跨库即时撤销。已有 UC002 当前状态检查仍按其消费用例生效，但不能宣称所有 App 方法已经在线查询。接受时必须列出并验收受影响入口。

暂停不清空 TEST/GREY/STABLE、不撤销审核结论、不隐藏 Catalog，也不删除应用 URL。若需立即停止应用服务，应另行执行 App 应用治理；不得让 Auth 直接修改 App 数据库。

<a id="br-dev-015"></a>
### BR-DEV-015：暂停优先与退出竞争

与 UC024/025 共享 Auth 认证事务栅栏。暂停先提交时，未完成的 Developer 退出操作被原子标为 CANCELLED，交由共享归属屏障协议解除本次临时屏障；不得阻止管理员因网络挂起的退出请求执行暂停。退出先提交为 WITHDRAWN 时，暂停请求冲突，不把已退出者改成 SUSPENDED。

若本账号已有未提交的注销准备，任何 Developer 状态变化都令该准备失效并取消，用户需重新取得注销预览及确认。注销先提交后目标已终止，本用例拒绝。恢复与账号禁用可分别提交，但恢复 Developer 不恢复 DISABLED 账号。

外部屏障解除不能在 Auth 事务中调用 App；先持久化取消决定，再按 [归属退出协调草案](../../platform/contracts/account-owner-exit-v1.md) 重试通知。App 故障可延迟解除临时限制，不能回滚已完成暂停。

<a id="br-dev-016"></a>
### BR-DEV-016：OAuth 恢复及 handle 连续性

developerHandle 及其永久唯一占用不变化。原应用归属、审核历史和发布事实保留；恢复不创建新的 Developer 身份或释放配额。

暂停本身不推进其他用户 grant/client epoch，也不逐条撤销其 token family。所有者恢复后，仍未过期、未撤销并满足当前全部条件的凭据可以再次使用；到期、重放撤销、用户撤回和账号禁用引起的失效不能恢复。永久停止应用凭据必须使用单独的应用/client 治理行为。

<a id="br-dev-017"></a>
### BR-DEV-017：审计与并发一致性

新建 append-only `auth_developer_lifecycle_audit_events`，记录 eventId、actorType=USER、actorAuthId、subjectAuthId、action、reason、before/after 状态及 revision、occurredAt；UC024 复用该生命周期审计。eventId 唯一，按 subjectAuthId/occurredAt/eventId 查询，不复用 UC013 一次性 ACTIVATE/CLAIM 审计唯一约束，不改写历史开通记录。

状态、版本、取消决定和审计同一事务提交；与 UC010/019 签发和 OAuth 所有者读取协调。提交前重查当前权限，审计失败回滚，未知提交返回不可用。客户端通过查询确认结果，不能以旧版本覆盖新决定。

## 错误与运行约束

身份失效为 401/UNAUTHENTICATED，缺当前管理资格为 403/PERMISSION_DENIED；不存在、SYSTEM、非 Developer 或已注销目标统一 `DEVELOPER_SUBJECT_UNAVAILABLE`（404/NOT_FOUND）。输入非法为 400/INVALID_ARGUMENT；revision/重复或非法状态转换为 `DEVELOPER_STATUS_CONFLICT`（409/ABORTED）；恢复邮箱门禁为 `DEVELOPER_RESTORE_BLOCKED`（409/FAILED_PRECONDITION）；版本耗尽拒绝。损坏数据、依赖故障或未知提交为 503/UNAVAILABLE，限流为 429/RESOURCE_EXHAUSTED。

独立 `AUTH_DEVELOPER_MANAGEMENT_ENDPOINTS_ENABLED` 默认 false，开启要求用户入口启用。按已认证 actor 的有界读/写桶默认每分钟 60/10，可部署调节；失败日志不含 JWS 或邮箱。

## 验收与依赖

- 同一用户的普通登录、资料和独立审核/管理权限在 Developer 暂停后仍可用；DISABLED 账号即使恢复 Developer 也不能登录。
- 版本冲突、重复转换、无邮箱恢复、PENDING/REJECTED/WITHDRAWN 非法恢复、数据损坏均不改变状态。
- 暂停与退出/注销确认竞争只有一个合法先后；取消决定持久化后 App 故障可重试，不永久阻塞治理。
- 真实 App 消费新的身份及 UC002 状态，验证暂停窗口与恢复；OAuth 不误撤销其他用户 grant，也不复活已有撤销 token。
- 使用真实 Mongo、签名、生产 HTTP/gRPC、并发和未知提交测试。

硬依赖 UC021 管理权限及 UC022 的 Auth 身份账号版本复核，两者尚未实现。UC024/025 未启用时无需提前存在退出操作，但启用它们前必须接入取消协调。接受时同步 UC013 的 developerRevision 初始化、UC002/UC010 状态消费说明、存储校验、API/路由和 brief；WITHDRAWN 的完整扩展由 UC024 负责。

## 变更记录

- 2026-10-05：提出 Developer 暂停/恢复；保留普通功能，固定资格版本、生命周期审计、恢复门禁和与终止流程的竞争规则。
