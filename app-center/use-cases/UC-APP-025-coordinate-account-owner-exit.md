# UC-APP-025：协调账号归属退出与个人状态清理

状态：`ACCEPTED`

## 目标与范围

向获授权 Auth 服务提供归属退出准备、终局提交及清理状态查询，支持 Auth UC024/025 在零应用归属条件下安全退出资格或注销账号。App 在本地事务内阻止并发新增归属，并为账号注销清理自身实际持有的个人状态。

本轮不实现应用转让、关闭、恢复、管理员临时接管或应用下架。有名下应用的用户明确 BLOCKED；不假装发布槽清空等于应用已处置。共享线格式、重试、决定查询及终局规则唯一引用 [account-owner-exit-v1](../../platform/contracts/account-owner-exit-v1.md)。

## 主流程与 API

1. Auth 先保存准备操作，通过 service JWS 调用 PrepareAccountOwnerExit。
2. App 在线验证方法权限和 caller，在账号归属事务栅栏内检查当前所有应用义务：非零返回 BLOCKED；零归属则保存不可变准备 receipt 和屏障，返回 PREPARED。
3. Auth 作出持久 COMMITTED/CANCELLED 决定后调用 FinishAccountOwnerExit，App 核对绑定并单调提交终局，CANCELLED 允许先于 Prepare 到达。
4. COMMITTED 将归属屏障永久 sealed；ACCOUNT_CLOSURE 另调度持久清理任务，DEVELOPER_WITHDRAWAL 不删除普通用户个人数据。
5. Auth 通过 GetAccountOwnerExitStatus 获取终局及个人清理回执；App 收敛任务可回查 Auth 的 GetAccountOwnerExitDecision，不根据超时或 NOT_FOUND 自行解除屏障。

方法/字段号/service permissions 按共享契约；只提供原生 gRPC，无 HTTP/gRPC-Web/Gateway。未知调用者、缺方法 permission、错误用途/receipt 拒绝；消息冲突为 FAILED_PRECONDITION，未知状态查询为 NOT_FOUND，存储/依赖故障为 UNAVAILABLE。不得返回个人资料或把底层错误当作零应用。

## 业务规则

<a id="br-app-008"></a>
### BR-APP-008：归属屏障与零义务准备

`adminId=authId` 的所有 Application 都阻止 Prepare，无论其发布或审核状态。使用 `account_owner_exit_fences` 的 authId 唯一记录作为可写事务栅栏；创建应用和 Prepare 在同一事务中先条件写该栅栏，再读取/修改配额和应用，不能仅用 snapshot 读检查。

PREPARED 和永久 sealed 均阻止新的创建；当前没有转让/关闭入口，未来增加这些行为必须在相同协调点检查。旧 APPROVED JWS 不能越过栅栏。账号没有旧 fence 时可原子建立 OPEN 初始事实，不代表补建 Auth 用户。

<a id="br-app-009"></a>
### BR-APP-009：单调终局与持久收敛

操作保存 `(authId, operationId, purpose, receiptId)` 与决定，event/operationId 唯一。相同请求幂等，不同绑定冲突。CANCELLED 先到保存终局，延迟 Prepare 拒绝；COMMITTED 不可取消或解封。已因 Developer 退出 sealed 后注销再取消，只取消当前临时变化，不能恢复旧 OPEN。

终局与持久清理/回查任务同一本地事务。App 不按 TTL 解封、不在数据库事务中调用 Auth；未知决定保持屏障，按共享契约有界重试。无需 Redis，生产后台工作器必须可重启继续处理。正常服务启动不能清除操作决定或 sealed 记录。

<a id="br-app-010"></a>
### BR-APP-010：注销个人状态清理

ACCOUNT_CLOSURE 的准备及永久 sealed 同时阻止 Tester Join 新增个人状态；DEVELOPER_WITHDRAWAL 仍允许普通 Tester 加入。创建/Join 与 Prepare 共用账号栅栏，涉及 Application coordination fence 时统一顺序 account→Application。

COMMITTED ACCOUNT_CLOSURE 后以有界批次清理该 testerAuthId 的全部 ACTIVE/REMOVED membership episode，并在各 Application coordination fence 内处理，保证人数计数及并发移除一致；其他用户不受影响。零应用账号的 creation quota 可以删除。仅在扫描为空并确认不可重建时标为 COMPLETE。

application_filters/filter_revisions 是应用公开 Filter，不是用户偏好，不能删除。保留 Application、Version、Review、Publication 及历史 createdBy/submittedBy/reviewer 等归因；当前没有独立个人偏好 collection，禁止凭名称猜测清理表。未来新增个人数据需显式纳入清单。

<a id="br-app-011"></a>
### BR-APP-011：退出与终止状态的消费

USER JWS 的 WITHDRAWN 是合法身份状态：开发者写入口仍仅允许 APPROVED，普通功能和独立 reviewer 权限不因枚举出现而整体验签失败。

Auth UC002 增加账号状态投影。版本审核批准检查明确区分角色：当前 admin 必须 accountStatus=ACTIVE 且 developerStatus=APPROVED；历史 submittedBy 为 WITHDRAWN 或 CLOSED 不因主动退出本身否定不可变提交，历史提交者 SUSPENDED 或 DISABLED 仍阻止批准。同一人兼任 owner/submitter 时取更严格的 owner 条件。任何未知、损坏或查询故障保持 PENDING，不能作为自动拒绝的证据。

权威状态明确不满足门禁时，沿 UC005 SYSTEM 自动 REJECT 流程，固定文本“当前应用管理员或审核提交者不满足账号与开发者资格要求，待处理审核已由系统自动拒绝。”；不改变已完成的决定。UC005 port 改为显式传入 currentAdminId/submittedBy 的批准资格检查，不能靠数组顺序猜角色。

## 数据与验收

新增 Mongo migration 0020，仅创建本能力集合/validator/索引，不迁移旧 Auth 数据或回填权限。fence 按 authId 唯一，operations 按 operationId 唯一并按 authId/decision 查询；清理进度有界，不记录服务 token 或完整用户身份。

验证真实事务中的 Prepare/Create、Prepare/TesterJoin、终局/清理竞争，取消先到、receipt 错配、永久封闭继承、超时不解锁、双方重启和清理幂等。验证 WITHDRAWN 普通身份、APPROVED 开发门禁、ACTIVE/DISABLED/CLOSED 角色敏感审核判断，以及真实 Auth UC002/内部决定 provider 联调。

执行 make check-full 与 make check-auth-app；Auth 新工作包尚未合入时可先做提供方测试，但最终不得以 fake server 代替跨服务验收。独立开关默认关闭，启用要求 Auth 调用方与回查 service identity 配置齐备，外部不公开本能力。

## 交付依赖

依赖既有 UC001 创建事务、UC009 Tester 事务及 UC005 审核流程，新增 Auth UC024/025 决定 provider。与 Auth 同批交付，完整产品仍需客户端/部署门禁；本用例并不交付已有应用的归属处置入口。
