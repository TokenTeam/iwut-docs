# 账号退出时的 App 归属协调 v1

状态：`ACCEPTED`

## 范围与事实来源

本契约是 [UC024](../../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md) 和 [UC025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md) 所需的 Auth/App 实现契约，App 工作包见 UC-APP-025。Auth 决定资格退出或账号终止；App 决定哪些应用及归属操作仍需该账号承担责任，并阻止并发新增归属。不能用一次无保护的查询代替本协议。

首版 App 中所有 `adminId=authId` 的 Application（包括草稿、审核中、未发布、已发布）都阻止退出。仅清空发布槽不算处置；转让、关闭如何移除归属义务由后续 App UC 明确，在其交付前拥有应用的用户无法完成此流程。历史 creator/reviewer 引用不等于当前所有权，但存在仍需该账号负责的待处理归属操作也阻止退出。

## 内部接口

均为原生 gRPC、独立 trusted-service-identity 方法权限和调用方 allowlist，Auth→App，Finish 的决定必须与 Auth 持久状态一致；不通过用户 Gateway，不信任终端声称“没有应用”。

```text
PrepareAccountOwnerExit {
  authId, operationId: opaque ID
  purpose: DEVELOPER_WITHDRAWAL | ACCOUNT_CLOSURE
}
OwnerExitPreparation {
  outcome: PREPARED | BLOCKED
  receiptId: opaque ID?  // 只有 PREPARED 返回
  blocker: OWNED_APPLICATIONS | PENDING_OWNERSHIP_CHANGE | NONE
}
FinishAccountOwnerExit {
  authId, operationId, receiptId?: opaque ID
  decision: COMMITTED | CANCELLED
  purpose: DEVELOPER_WITHDRAWAL | ACCOUNT_CLOSURE
}
```

另由 Auth 向获授权 App 提供 `GetAccountOwnerExitDecision(authId, operationId)`，返回 `PENDING | COMMITTED | CANCELLED`；未知操作返回 NOT_FOUND，不能解释为已取消。Auth 保存的 receipt/purpose 和归属目标必须与 App 一致。消息中的 authId 只是被治理对象，不是伪造的终端操作人身份。

## App 原子屏障

App 的 Prepare 在同一账号归属事务栅栏下检查义务并安装屏障。所有创建应用、转入所有权、撤销转出、恢复已关闭应用以及将来可能增加归属义务的写操作必须参与同一栅栏；包括持有旧 APPROVED JWS 的请求。不能只在 HTTP handler 做预检查。

存在义务时返回 BLOCKED，不安装屏障，不自动转让、关闭或删除应用；用户处理后用新操作重试。零义务时返回 PREPARED，保存不可变 `(authId, operationId, purpose, receiptId)`，阻止该账号新增归属，直到收到终局决定。重复相同请求返回同一结果；同 operationId 换 authId/purpose 或不匹配 receipt 拒绝。

COMMITTED 将本次屏障变为永久 sealed，不允许未来凭旧 JWS 创建或转入应用。首版 Developer 退出不支持重新开通，因此无需解封接口。已因 Developer 退出 sealed 的账号之后申请注销时，仍重新核验无义务，为注销 operation 生成独立 receipt；取消注销不会解除之前的永久 sealed 状态。

CANCELLED 仅解除该 operation 创建的临时屏障，不能解除其他操作或既有永久 sealed。即使 Prepare 尚未到达，Finish(CANCELLED) 也保存该 operation 的终局记录，拒绝后来延迟到达的 Prepare；不能出现“先取消，再被迟到的准备永久锁住”。一个 authId 同时最多一个未决归属退出操作。

## Auth 协调与故障

Auth 先保存 PENDING 操作，再调用 Prepare；准备操作寿命最多 10 分钟。随后在 Auth 事务中复核 Session/专用注销证明、accountRevision、developerRevision、权限和业务条件，只有 PREPARED receipt 对应原操作且仍在期限内才可提交资格退出/账号终止，同时写 COMMITTED 决定与待投递通知。

用户取消、条件变化或准备超时由 Auth CAS 为 CANCELLED，不能取消已提交操作。事务提交结果未知时先读取权威决定，不发送推测的 CANCELLED。账号终止后的清理任务不能删除尚未被 App 确认的协调决定。

App 屏障不按租约或本地 TTL 自动解除：Auth 可能已经提交而通知丢失。双方使用持久化、幂等重试收敛，App 可向 Auth 查询终局；Auth 不可用时保持屏障并返回依赖故障。孤立 PENDING 由 Auth 到期任务确认取消再通知，不以“找不到”当取消。故障期间用户可见“处理中/尚未完成”，不能声称数据或资格已经删除。

App 收到终局后回执；Auth 在回执前保留决定。只有协调已终结且超过外部调用最大重试窗口后才允许压缩操作明细；永久 sealed 的最小 authId/purpose/终止操作引用保留。终局不得回退。此为两个本地事务与持久补偿，不假设分布式事务、消息必达或 Redis。

## 固定线格式与方法授权

App package `app_center.v1.account_owner_exit`、service `AccountOwnerExitService`，PrepareAccountOwnerExit / FinishAccountOwnerExit / GetAccountOwnerExitStatus 分别要求 `app.account-owner-exit.prepare` / `app.account-owner-exit.finish` / `app.account-owner-exit.read`，仅授权 Auth caller。Auth package `auth_center.v1.account_owner_exit`、service `AccountOwnerExitDecisionService/GetAccountOwnerExitDecision` 要求 `auth.account-owner-exit.read`，仅 App caller。均无 HTTP annotation 或终端路由。

消息字段号固定：PrepareRequest auth_id=1, operation_id=2, purpose=3；FinishRequest auth_id=1, operation_id=2, receipt_id=3, decision=4, purpose=5；GetStatusRequest 与 GetDecisionRequest 均 auth_id=1, operation_id=2。Purpose 枚举 0=UNSPECIFIED(拒绝),1=DEVELOPER_WITHDRAWAL,2=ACCOUNT_CLOSURE；Decision 0=UNSPECIFIED,1=PENDING,2=COMMITTED,3=CANCELLED，Finish 不允许 PENDING。

PrepareResponse outcome=1（0非法,1=PREPARED,2=BLOCKED）,receipt_id=2,blocker=3（0=NONE,1=OWNED_APPLICATIONS,2=PENDING_OWNERSHIP_CHANGE）。App 状态/Finish 响应统一 auth_id=1,operation_id=2,purpose=3,decision=4,receipt_id=5,cleanup_state=6（0非法,1=NOT_REQUIRED,2=PENDING,3=COMPLETE）。GetDecisionResponse decision=1,purpose=2,receipt_id=3。状态查询对未知 operation 返回 NOT_FOUND，不暗示取消。

App 的 ACCOUNT_CLOSURE COMMITTED 持久创建个人清理任务，GetStatus 的 cleanup_state=COMPLETE 才表示个人数据清理回执；WITHDRAWAL 为 NOT_REQUIRED。Auth 先调用 Finish 再轮询持久状态确认 App 回执，不把 Finish 网络成功误认为全部清理完成。App 也可回查 Auth 终局用于收敛。

AuthId 沿用现有 1..200 bytes opaque ID；operationId 为 Auth UUIDv4，receiptId 为 App 生成 UUIDv7，不作秘密；所有比较原样精确。双边后台重试初始 1 秒、指数退避最大 60 秒，每批最多 100，RPC deadline 5 秒，含有界抖动。部署参数可调整但不得把到期当作自动解除屏障。每个操作的终局摘要永久保留至关联墓碑被明确政策替代，避免任意迟到 Prepare 越过已清理的取消记录；大体量诊断材料在回执后 30 天内清理。

## 交付门禁

提供方权威用例为 UC-APP-025，支持零归属用户。转让/关闭已有应用不在本轮，有应用者持续 BLOCKED。必须更新实际创建入口和 ACCOUNT_CLOSURE 下 Tester 加入入口，防止旧 JWS 重建个人状态；未来增加归属写入口必须复用此屏障。

验收覆盖 Prepare 与创建竞争、取消先于 Prepare、Auth 提交后丢响应、双边重启、长时间故障、过期准备、重复 Finish、目标/receipt/purpose 错配、WITHDRAWN 后注销取消不解除原 sealed、注销清理与 Tester 加入竞争。联调前退出/注销公网开关保持关闭。
