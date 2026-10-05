# UC-AUTH-024：本人退出 Developer 资格

状态：`ACCEPTED`

## 目标与范围

用户主动终止自己的 Developer 资格，先处理所有名下应用及未决归属义务，再进入 WITHDRAWN。保留普通账号、Session、邮箱、用户资料和 developerHandle 的永久占用。

首版退出后不支持重新开通，不把 WITHDRAWN 当作 null 或 SUSPENDED。后续若需要重新开通，须新设计审核/门禁及 App 屏障解除协议，且只能沿用原 handle；当前 UC013 和 UC023 都不能重新激活。客户端在确认前必须明确展示此结果。

## 参与者与接口

只有当前有效 Session 对应的 ACTIVE USER 可以操作本人，不接收 subjectAuthId。要求 developerStatus=APPROVED、有合法永久 handle 占用，并使用 UC023 的 developerRevision；无需管理员同意或额外绑定邮箱。SUSPENDED、PENDING、REJECTED 不走自助退出，避免将治理状态转换成可以重新申请的空状态。

独立 package `auth_center.v1.developer_withdrawal`，service `DeveloperWithdrawalService`。四个方法均为直接有效 Session 鉴权，Gateway DIRECT 精确转发（不代表匿名），不先换 USER JWS；HTTP/原生 gRPC 同时交付：

| 方法 | HTTP POST 路径 | 输入/结果 |
| --- | --- | --- |
| PrepareDeveloperWithdrawal | /v1/users/me/developer-withdrawal:prepare | requestId(UUIDv4)、expectedDeveloperRevision → operation |
| ConfirmDeveloperWithdrawal | /v1/users/me/developer-withdrawal:confirm | operationId、confirmation=WITHDRAW_DEVELOPER → operation |
| CancelDeveloperWithdrawal | /v1/users/me/developer-withdrawal:cancel | operationId → operation |
| GetDeveloperWithdrawal | /v1/users/me/developer-withdrawal:get | operationId → operation |

operation 仅返回本人的 operationId、state=`PREPARING | READY | BLOCKED | COMPLETED | CANCELLED`、expiresAt、developerStatus/revision、blocker 和 completedAt；不返回 App receipt、其他应用所有者或邮箱。BLOCKED 原因可为 OWNED_APPLICATIONS/PENDING_OWNERSHIP_CHANGE；客户端引导到 App 处理，不由 Auth 代办转让。

请求采用严格 ProtoJSON、UTC Timestamp、16 KiB 上限、无 query/未知重复字段；Session 唯一载体沿用设备协议。读写都复核 Session/accountRevision，不增加新登录方法。只读查询不 touch lastUsedAt；成功变更按既有有效 Session 操作规则处理。

## 主流程

1. Prepare 在 Auth 事务中复核资格、目标版本，保存本人 PENDING 操作、当前 Session ID、accountRevision、developerRevision 和固定 10 分钟期限；不先修改 Developer 状态。
2. 调用 [App 归属退出协调](../../platform/contracts/account-owner-exit-v1.md) 的 Prepare。存在名下应用或未决归属时返回 BLOCKED；零义务并建立屏障后为 READY。当前 session/版本条件变化则取消，不能把新状态重新绑定到旧操作。
3. 客户端展示资格退出、handle 保留和首版不可重新开通，由用户明确 Confirm；确认不是 Prepare 的隐式后续。
4. 同一 Auth 事务重新确认原 Session 仍有效、账号/Developer 版本未变、APPROVED、receipt 匹配且未过期，设置 WITHDRAWN、增加 developerRevision、写生命周期审计和 COMMITTED 决定。
5. 持久通知 App 将屏障 sealed；通知失败重试，不把已退出的资格恢复。返回 COMPLETED 后普通用户功能继续可用。

## 业务规则

<a id="br-dev-018"></a>
### BR-DEV-018：明确本人退出与稳定身份

只修改当前 authId 的 Developer 资格。保留 handle 原归属、claimedAt、原始开通事实和历史应用/审核引用；不释放名称、不重置配额或创建第二身份。不改 accountRevision、permissionRevision，不回收本人 Session、独立 reviewer/管理员权限或作为应用用户的 grant。

转换固定为 APPROVED→WITHDRAWN，版本只递增一次；同 operationId 的已确认操作重复 Confirm 返回原完成结果，不能生成第二事件。对 WITHDRAWN 新建退出操作返回 ALREADY_WITHDRAWN，不重走 App 或增加版本。

<a id="br-dev-019"></a>
### BR-DEV-019：先处置应用再退出

App 是当前应用归属义务的唯一权威。所有名下 Application 均计入，包括未发布草稿；没有公开发布不等于没有义务。先通过 App 正式用例转出或关闭，Auth 不帮用户删除 App 数据，也不将应用自动移交平台。

共享协议的 PREPARED 屏障是提交前置条件；普通读 API、缓存名单或用户声明不可替代。即使旧 APPROVED JWS 尚未过期，并发创建/转入也不能在 READY 之后成功，COMPLETED 后永久拒绝新增归属。

App 当前缺少完整转让/关闭及该屏障能力。其交付前入口保持关闭；仅向无应用用户开放也仍需屏障，不能以“没有查询到”提前完成。

<a id="br-dev-020"></a>
### BR-DEV-020：可取消准备与不可逆提交

Prepare/READY 不改变资格，但 App 可暂时阻止增加归属。用户可在提交前 Cancel；过期、账号版本变化、Session 失效或管理员暂停导致 Auth 终局 CANCELLED，按共享协议解除本次临时屏障。UC023 暂停可以取消退出，退出不得占锁阻止治理。

一个 authId 最多一个未决生命周期退出操作，UC025 注销准备不能并行另开。requestId 在 24 小时内按 `(authId, requestId)` 去重；相同请求返回已有 operation，不延长期限，同键不同 revision 冲突。已取消/阻塞结果不复活，重新尝试使用新 requestId。BLOCKED 是对本次失败准备的展示状态，对协调协议保存终局 CANCELLED；释放未决操作占用并发送必要的取消通知，不让用户无谓等待 10 分钟。

COMPLETED 不可 Cancel，也不因 App 回执丢失恢复 APPROVED。未知提交先读取终局，不能推测取消。操作决定及重试任务持久化，跨服务故障处理严格引用共享协议。

<a id="br-dev-021"></a>
### BR-DEV-021：状态消费与历史审核

WITHDRAWN 是 Developer 生命周期终态，不是违规暂停。UC002 返回这一明确状态；UC010 可携带 WITHDRAWN，所有 APPROVED-only 开发入口及 Auth OAuth owner 检查均拒绝其行使开发者资格。不得将未知枚举默认为 APPROVED、null 或 SUSPENDED。

App 对历史 submitter、creator 或 reviewer 的处理不能只使用“不是 SUSPENDED 就允许”：WITHDRAWN/已终止账号在具体审核批准门禁中的含义必须由 App 同步明确。退出不撤销已作出的审核决定，不抹去审计归因；作为 reviewer 的权限仍由 UC004 独立控制。当前管理员必须具备有效资格，历史提交者是否阻止新决定由 App 用例逐项固定，未对齐前不可启用退出。

<a id="br-dev-022"></a>
### BR-DEV-022：原子性、查询与审计

复用 UC023 生命周期审计，operation=WITHDRAW、actorAuthId=subjectAuthId，记录 before/after 状态及版本和 operationId，不强制用户填写退出理由。资格、审计、协调终局及通知任务同一 Auth 事务提交，与申请、暂停、恢复、账号禁用/注销和身份签发共用认证栅栏。

属于其他账号或不存在的 operation 统一不可用；只对本人披露 blocker。普通数据损坏、App 故障或状态未知均返回不可用/处理中，不伪装为“名下没有应用”。App 未收终局回执前，不清理所需操作决定。

## 错误与验收

Session 无效为 401；请求非法为 400；operation 不属于本人为统一 404；版本/状态冲突或过期确认为 409；依赖/存储/未知提交为 503；限流为 429。Prepare 的应用义务为正常 BLOCKED 结果，不以 500 表示。默认关闭 `AUTH_DEVELOPER_WITHDRAWAL_ENABLED`，开启要求用户入口及 App provider 配置齐备；有界账号读/写桶默认每分钟 60/10。

必须测试：草稿/未发布/已发布均阻止；并发创建、转入与退出；旧 JWS；Prepare 后取消/过期/暂停/禁用；提交丢响应和 App 不可用；永久 handle 占用；新 Apply/管理 RESTORE 拒绝 WITHDRAWN；普通登录与独立权限保留；已退出后再注销并取消不解除既有 sealed。覆盖真实双服务、Mongo 事务与 HTTP/gRPC。

## 实现依赖与联动

依赖 UC021–023 的治理、账号/资格版本和取消边界；App 归属屏障由已交付的 UC-APP-025 满足。实施时扩展 UC002、UC013、UC010、JWS/内部状态 Proto 和所有 App 状态消费者，明确 App 归属处置与历史审核政策；同步 brief。首版不增加重新申请、资格审批或旧数据迁移。本 UC 已 ACCEPTED，设计接受不等于依赖已实现。

## 变更记录

- 2026-10-05：提出本人退出 Developer；WITHDRAWN、永久 handle 占用、App 归属屏障、可取消准备与不可逆资格退出，首版不支持重新开通。

- 2026-10-05：按用户决定接受，生成 brief 并启动独立工作包；依赖顺序与生产启用门禁继续有效，不把设计接受记为实现完成。
