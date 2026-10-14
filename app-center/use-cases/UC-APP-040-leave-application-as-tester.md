# UC-APP-040：Tester 主动退出 Application 测试

状态：`ACCEPTED`

## 设计结论

| 决定 | 已接受决定 |
| --- | --- |
| 谁可以退出 | 已验证 USER 只能退出自己的指定 Membership episode；不要求 Developer 资格、管理员或 Reviewer 权限 |
| 退出目标 | 使用 applicationId + membershipId；重复或迟到请求不影响后来重新加入的新 episode |
| 应用不可用时 | AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED、ACTIVE/CLOSING/CLOSED 的保留 episode 均允许本人退出 |
| 历史与再加入 | 复用 REMOVED 终态及现有审计字段；保留历史、释放容量，再加入仍走 UC009 创建新 episode |
| 交付边界 | 只增加 App 后端与对应 API；不撤销加入链接、Auth 凭证或存量会话，不增加本人离线参与查询或前端实现 |

## 目标与范围

已登录 Tester 可以主动终止自己在一个 Application 下的一次测试参与资格。参与属于 Application，不属于某个 Version、RPC major 或发布槽位。

本用例补齐 [UC009](UC-APP-009-join-application-as-tester.md) 的自助加入和 [UC038](UC-APP-038-query-my-test-applications.md) 的本人参与入口。它与 [UC010](UC-APP-010-remove-application-tester.md) 的管理员移除是两个授权不同的命令；不改变 UC010 的管理员/Developer 资格要求或现有响应。

只处理一个属于当前 USER 的 Membership episode。普通退出保留 episode 和来源事实，不恢复终态、不物理删除记录、不新增 LEFT 状态或 removalReason 字段。账号关闭的个人状态清理仍由 [BR-APP-010](UC-APP-025-coordinate-account-owner-exit.md#br-app-010) 负责，已清理的 episode 不重建。

资格由本地 Membership 事实判定，不调用 Auth、Scope Catalog、DNS 或资产服务。

不提供按 authId 批量退出、退出所有测试、黑名单、加入链接撤销、发布清空、Version/Profile 修改、通知、Auth grant/token/session 撤销或正在运行网页的强制断开。

## 身份、目标与生命周期

身份为可信 USER，testerAuthId 只能来自认证上下文。管理员、Reviewer、平台运维或 SYSTEM 身份不能代替目标 Tester；管理员若有自己的 Membership，也按普通 USER 退出自己的 episode。

目标为 `(applicationId, membershipId, callerAuthId)`。不存在、属于其他 Application、属于其他用户或已被账号清理的 episode，统一 NotFound。相同用户重新加入得到的新 membershipId 不在旧请求的作用范围内。

退出是减少既有资格的操作。Application 暂停、归档、CLOSING/CLOSED 不阻止退出；不要求当前公开 Profile、Test 槽位、兼容 runtime 或 ACTIVE 加入链接。允许退出不恢复应用在线资格、管理员义务、配额、写权限或重新加入条件。

本用例不扩大 UC038 的查询可见性。不可用应用仍由其在线 gate 隐藏；调用者可以使用自己已经取得的 episode 句柄退出。首版不新增离线参与列表或历史查询。

## 命令与 API 草图

在现有 `app_center.v1.tester_membership.TesterMembership` 服务追加：

```text
LeaveApplicationAsTester {
  applicationId: UUIDv7
  membershipId: UUIDv7
}

POST /v1/applications/{application_id}/tester-memberships/{membership_id}:leave
```

外部 URL 仅由 Gateway 加 `/app-center` 前缀。HTTP 不接受 query 或请求正文；原生 gRPC 请求只有这两个目标字段，拒绝未知字段。调用者、目标用户、状态、时间、计数和审计字段不能由请求指定。UUID 输入沿用现有 canonical 解析；先验证 USER，再处理业务输入。不要求 If-Match、运行参数、joinLink secret 或确认字段。

成功和幂等均为 HTTP 200 / gRPC OK：

```text
LeaveApplicationAsTesterResult {
  left: boolean
  membership: {
    membershipId
    applicationId
    status: REMOVED
    joinedAt
    removedAt
  }
}
```

left=true 表示本命令完成了该 episode 的 ACTIVE → REMOVED；left=false 表示所指定 episode 已是 REMOVED。返回保存的 UTC 时间。两种结果都不承诺调用者在该 Application 下没有后来创建的其他 ACTIVE episode。

不返回 removedBy、其他 Tester、容量、当前加入链接及其凭证、Auth 资料或应用私有管理信息。所有正常、幂等与错误响应为 `private, no-store`。

## 主流程与原子边界

1. 验证可信 USER，解析 applicationId 和 membershipId。
2. 加载只属于该调用者的目标及必要来源。验证 Application 和 episode 的结构、归属、状态、审计和加入来源关系。
3. 已确认 REMOVED 时返回原终态和 left=false；不取新的业务时间、不改审计、不重复释放容量。
4. 对 ACTIVE 候选从 App Clock 取得退出时间。时间须合法、可编码且不早于 joinedAt；不能先提交非法时间再在响应编码阶段报错。
5. 在一个 majority transaction 中复查身份归属和目标状态，复用 Application coordination fence 与现有 ACTIVE unique 约束，原子迁移到 REMOVED。没有单独持久化的 activeTesterCount 副本；由同一事务内的 ACTIVE 事实确认容量减少一次。
6. 返回该次事务中的目标和 left 标记。竞争者已经终止该 episode 时保留其原审计，返回 left=false，丢弃本次预取时间。

成功退出记录 removedBy=callerAuthId、removedAt=App Clock，其他加入事实不变。这里的 actor 由本用例定义；UC010 的管理员移除仍记录其执行管理员，不能改写过去的 removedBy 或重新解释旧记录。

与加入、管理员移除、账号清理等 Membership writer 共用既有 Application 栅栏和锁顺序，不建立第二份锁或计数。幂等路径允许维护 adapter-only 栅栏，不能写新的业务审计。身份/目标不匹配、持久化错误、栅栏溢出或不变量错误必须无部分提交。

## 并发、再加入与资格消费

- 两个本人退出或本人退出与管理员移除并发，最多一次状态迁移；最后的终态及审计来自赢家。
- 退出与 UC009 加入并发须线性化。退出前的幂等加入仍是原 episode；退出后的有效加入创建新 episode。旧 membershipId 的任何重试都不能操作新 episode。
- 管理权转让不改变 testerAuthId，也不授予新管理员代他人执行本人退出的权限。
- 暂停、归档和关闭与退出按共享栅栏串行提交；终止本人 episode 不能解除这些 gate。
- 账号清理可以最终删除个人 episode；退出与清理协调且不重建已清理记录。账号准备/注销屏障继续禁止 Join 新建个人状态；本命令只减少已存在状态，不提供屏障绕过或恢复入口。
- 提交后，UC038 不再把该 REMOVED episode 作为参与候选，UC012 和 UC019 后续资格读取不再从它建立 ACTIVE Tester 资格。正在进行的读取可落在提交前或后；已返回的描述符不会被撤回。退出不强制结束已经运行的页面，也不新增 Auth token/session 的即时撤销承诺。
- 后续仍可持有效链接依 UC009 重新加入，受当前在线 gate、账号屏障和 100 人容量约束；退出本身不生成或返回加入凭证。

## 必要来源与错误

授权先按 callerAuthId 限定目标，不能以校验其他用户的损坏记录代替统一 NotFound。属于调用者的目标一旦找到，其必要 Application、加入来源链接及 episode 关系损坏须失败关闭。来源链接已 REVOKED 是正常历史，不能要求其继续 ACTIVE 或读取 secret。

至少验证 canonical ID、同 Application 来源、唯一目标/唯一 ACTIVE 关系、ACTIVE/REMOVED 审计形状、合法 UTF-8/时间、终止时间顺序、ACTIVE 计数范围和可安全推进的技术栅栏。已移除的旧 episode 与另一个新的 ACTIVE episode 并存是合法状态，不得误判或把新 episode 当成退出目标。

| 情况 | 候选业务错误 | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效 USER | UserIdentityRequired / InvalidUserIdentity | 401 / UNAUTHENTICATED |
| UUID 或 HTTP/gRPC 输入非法 | InvalidApplicationId / InvalidTesterMembershipId / InvalidTesterExitRequest | 400 / INVALID_ARGUMENT |
| 目标不存在、跨应用、属于他人或已清理 | ApplicationTesterMembershipNotFound | 404 / NOT_FOUND |
| 必要事实、计数、栅栏或审计损坏 | ApplicationTesterStateInconsistent | 500 / INTERNAL |
| 持久化不可用 | ApplicationTesterExitUnavailable | 503 / UNAVAILABLE |

首次退出、重复退出以及输赢竞争都不返回其他用户的存在性或个人信息。日志、指标和告警遵循 ADR007，只使用有界操作/错误分类，不记录身份载体或完整请求。

## 业务规则

<a id="br-tst-044"></a>
### BR-TST-044：本人退出授权

仅可信 USER 且 authId 等于目标 episode.testerAuthId 可执行本人退出；Developer 资格、管理员、Reviewer、平台或 SYSTEM 权限不替代这个关系。

<a id="br-tst-045"></a>
### BR-TST-045：精确 episode 与统一隐藏

命令只定位指定 applicationId/membershipId 的本人 episode。不存在、跨应用、属于他人和已清理统一 NotFound；迟到的旧目标请求不得影响重新加入产生的新 episode。

<a id="br-tst-046"></a>
### BR-TST-046：退出终态与幂等审计

首次本人退出将 ACTIVE 迁移到既有 REMOVED，记录本人 removedBy 和 App Clock removedAt，保持加入事实。已经 REMOVED 返回原终态、left=false，不改审计、不取新业务时间、不重建记录。

<a id="br-tst-047"></a>
### BR-TST-047：保留状态允许退出

暂停、归档及 ACTIVE/CLOSING/CLOSED 的保留 episode 均允许本人退出，不要求公开资料、发布目标、runtime 或 ACTIVE 链接。退出不解除任何应用 gate、治理屏障或未来加入前置条件。

<a id="br-tst-048"></a>
### BR-TST-048：原子释放容量与并发协调

在单个 majority transaction 及既有 Application 栅栏内复查本人关系，最多一次终止指定 ACTIVE episode 并释放一个名额；与加入、管理员移除、关闭、转让、账号清理线性化。失败无部分提交，不维护计数副本。

<a id="br-tst-049"></a>
### BR-TST-049：重新加入与消费边界

退出仅终止指定 episode，不建立黑名单或修改链接、发布与 Auth 凭证。后续 ACTIVE 资格消费依据提交后的 Membership；重新加入须独立走 UC009 并创建新 episode，不撤回旧读取或强制断开运行页面。

<a id="br-tst-050"></a>
### BR-TST-050：退出最小披露与私有响应

只返回目标 ID、REMOVED、必要加入/终止时间与 left 标记；不返回操作人、容量、其他 Tester、链接/凭证或私有应用资料。所有成功、幂等和错误响应 private, no-store；观测遵循 ADR007。

<a id="br-tst-051"></a>
### BR-TST-051：必要退出来源损坏失败关闭

找到本人目标后，必要 Application、Membership、来源链接、唯一性、计数、时间和审计不变量损坏必须 INTERNAL，无部分结果或自动修复；合法已撤销来源、旧 REMOVED 加新 ACTIVE 不属于损坏。

## 既有规则依赖

- UC009：BR-TST-010–019 的 USER 加入、100 人容量、ACTIVE 唯一性与新 episode；不改变 Join 的在线门禁和凭证校验。
- UC010：BR-TST-021–027 的 episode 身份、终态、容量、重新加入、链接独立和共享并发机制；该命令的授权及管理员审计 actor 保持原定义。
- UC025：BR-APP-010 的账号屏障、个人状态清理和不可重建边界。
- UC012/019/037/038：复用已接受的 ACTIVE Tester 消费和管理/本人查询规则，不新增查询可见性或 Auth 行为。

规则权威仍在各自 UC；本节只引用依赖，不复制或修改它们。

## 验收矩阵

1. 普通 USER、资格已下降的 Developer 和拥有自身 Membership 的管理员可退出自己；匿名、他人、仅角色权限和伪造目标拒绝。
2. 首次 left=true、重复 left=false，原审计保持；管理员已移除后本人重复退出仍不改操作人/时间，不读取新 Clock。
3. 暂停/归档/ACTIVE/CLOSING/CLOSED、无资料/无 Test、撤销来源链接都可终止本人保留 episode，其他 gate 不变。
4. 与本人重复、管理员移除、同用户重新加入、容量竞争、转让、关闭及账号清理并发，证明提交顺序和一次释放；旧请求永不误退新 episode。
5. 退出后 UC038/UC012/UC019 使用当前 ACTIVE 事实；其他 Tester、其他 Application、发布及 Auth 状态不变，有效链接重新加入取得新 membershipId。
6. 来源/归属、重复 ACTIVE、BSON/UTF-8、时间、非法审计、计数和栅栏溢出失败关闭；真实 Mongo 写失败回滚全部变化。
7. 真实 HTTP、原生 gRPC、实际生成 HTTP client、严格空请求、身份校验顺序、错误映射、字段白名单和全部 no-store。
8. UC009/010/011/012/019/025/037/038 原有完整验收保持，App/API/Wire、Go 1.25.5 与未过滤 make check-full 通过。

## 实现与相邻服务交付边界

用户于 2026-10-15 接受本设计。创建 UC040 spec/brief 和声明工作包，并实现 Tester Domain/UseCase/port、Mongo、传输层与 Wire。复用现有 Membership schema、唯一索引、容量统计和 coordination fence；不预先创建新状态、计数或历史模型。

App 本任务负责后端及 App API。Gateway 的 exact route/USER/CSRF 策略和客户端按钮、迟到响应协调、刷新参与卡片由用户交给其他 agent；本任务只提供契约和交接说明。客户端普通目录/Filter 求值、版本批准撤销、可靠告警投递与受控 icon 仍暂缓。

## 变更记录

- 2026-10-14：用户授权纳入 Tester 主动退出，在 UC039 完整验收后建立本 PROPOSED 串行工作设计；等待审核，不实现。

- 2026-10-15：用户接受设计并授权开始实现；状态转为 ACCEPTED，生成实施 brief。
