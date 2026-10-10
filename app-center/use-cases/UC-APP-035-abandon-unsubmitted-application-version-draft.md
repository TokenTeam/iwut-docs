# UC-APP-035：放弃从未提交审核的 ApplicationVersion 草稿

状态：`ACCEPTED`

## 设计结论

> Application 当前管理员可以永久放弃一份从未提交审核的 DRAFT ApplicationVersion。该命令不是“删除所有未发布版本”：SUBMITTED、APPROVED、REJECTED，以及从 REJECTED 恢复而来并已具有 Review 历史的 DRAFT，都不能通过本用例删除。

“未发布”不是安全的删除条件。APPROVED Version 即使当前不在 Test、Grey 或 Stable 槽位中，仍保存有效审核决定并可能再次发布；SUBMITTED 正在接受审核；REJECTED 和恢复后的 DRAFT 都连接不可变 Review snapshot、decision 或 restoration。删除这些记录会破坏审核、发布资格与审计关系。

因此本用例只解决 Developer Console 中无用初始草稿无法清理的问题，并把用户动作命名为“放弃草稿”。成功后 Version 当前内容及其一对一 OAuth 配置从有效数据中永久移除，另存最小不可变 `ApplicationVersionAbandonment` 事实支持审计和安全重试。放弃不新增 `ABANDONED` reviewStatus，也不改变任何 Review 或 Publication。

## 目标与范围

本用例负责：

- 允许 Application 当前管理员放弃一份 `reviewStatus=DRAFT` 且从未创建过任何 ApplicationReview 的 Version；
- 使用调用者读取到的 `expectedRevision` 做乐观并发控制；
- 在一个本地事务中复查管理权、Application 生命周期、Version、OAuth 配置、Review 与 Publication 关系；
- 原子删除有效 ApplicationVersion 及其一对一 ApplicationVersionOAuthConfig；
- 写入不含运行内容的最小不可变 ApplicationVersionAbandonment；
- 让相同路径与相同 source revision 的重试稳定返回 no-op 成功；
- 保证 versionId 与 sequence 永不复用，同时允许以后以新的 versionId/sequence 重新使用原 versionLabel；
- 让 UC034 列表、详情及 UC029 Version 计数立即不再包含已放弃草稿。

本用例不负责：

- 删除 SUBMITTED、APPROVED、REJECTED Version；
- 删除曾经提交审核、后来由 UC006 恢复为 DRAFT 的 Version；
- 判断 Version 是否“当前没有被发布”后删除它；Publication 空闲不是可放弃资格；
- 撤销 APPROVED 资格、清空 Test/Grey/Stable、删除 Review、PublicationHistory 或 OAuth client；
- 恢复、复制或查看已经放弃的草稿内容；
- 释放 Application 配额、修改 Application 生命周期、归档状态或平台可用状态；
- 调用 Auth Scope Catalog、URL preflight 或其他外部服务；
- 提供平台人员跨 Application 清理能力、批量清理、自动过期或后台垃圾回收。

## 参与者与授权

- **放弃者**：Gateway 验证后的可信 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **App Center**：拥有 Application、Version、OAuth 配置、Review、Publication 与 Abandonment 权威记录，并在本地事务中执行命令。

本命令不要求 developerStatus=`APPROVED`。Developer 资格下降后，当前管理员仍可通过 UC034 读取并清理自己已有的从未提交草稿；这不授予其创建、编辑、提交或发布 Version 的能力，那些写命令继续执行各自的 Developer 资格检查。

Application 必须保持 `lifecycleStatus=ACTIVE`。平台 `AVAILABLE/SUSPENDED` 与管理员 `UNARCHIVED/ARCHIVED` 不阻止草稿清理，因为放弃不会产生新的运行资格或在线效果。进入 CLOSING 或 CLOSED 后，全部配置写入继续停止，本命令返回 `ApplicationVersionAbandonmentNotAllowed`。

Reviewer 权限、平台 suspend/restore 权限、SYSTEM service identity、Tester 身份和其他角色都不隐式授权。可信身份验证后，Application 或 Version 不存在、调用者不是当前管理员、versionId 不属于路径 Application，统一返回 `ApplicationVersionNotFound`，避免跨 Application 枚举。

## 命令与 API 草图

沿用现有 `app_center.v1.application_version.ApplicationVersion` service，新增：

```text
rpc AbandonApplicationVersionDraft(AbandonApplicationVersionDraftRequest)
  DELETE /v1/applications/{application_id}/versions/{version_id}
```

输入：

```text
AbandonApplicationVersionDraftRequest {
  applicationId
  versionId
  expectedRevision
}
```

HTTP 使用强 `If-Match: "<expectedRevision>"`，不接收 body 或 query；原生 gRPC 使用 request 的 `expectedRevision` 字段表达同一语义。缺失、弱 ETag、多个值、非十进制正整数或 HTTP body/query 均拒绝。

成功响应：

```text
AbandonApplicationVersionDraftResponse {
  changed
  abandonment {
    applicationId
    versionId
    sequence
    versionLabel
    sourceRevision
    abandonedAt
  }
}
```

首次提交返回 `changed=true`。相同 Application/versionId 与相同 source revision 的已完成命令返回同一 abandonment 事实及 `changed=false`；它不再次写 Clock、Application coordinationRevision 或任何审计事实。响应不返回 launchUrl、capabilities、scopes、OAuth redirects、createdBy、updatedBy 或 abandonedBy。

HTTP 与原生 gRPC 对成功、no-op 与领域错误均返回 `Cache-Control: private, no-store`。放弃成功返回 `200 OK`，而不是依赖空响应隐藏命令是否首次提交。

## “从未提交”的权威判定

首次放弃的资格必须同时满足：

1. ApplicationVersion 存在且属于路径 Application；
2. `reviewStatus=DRAFT`；
3. 当前 revision 等于 expectedRevision；
4. 一对一 ApplicationVersionOAuthConfig 存在且归属、内容与 Version 一致；
5. `application_reviews` 中不存在任何引用该 versionId 的 attempt；
6. 当前 ApplicationPublication 和追加式 ApplicationPublicationHistory 都不引用该 versionId；
7. 不存在与该 versionId 冲突的既有 abandonment 记录。

若有效 Version 已不存在但存在合法 abandonment，则不再重新计算首次放弃资格，而是按下文的 sourceRevision 规则处理安全重试。幂等返回仍必须验证调用者是 Application 当前管理员，不得把 abandonment 变成公开查询入口。

不能只依据 `reviewStatus=DRAFT`。UC006 会把 REJECTED Version 恢复为 DRAFT，但其 Review 保留 decision 与 draftRestoration；这类 Version 已经提交过审核，必须返回 `ApplicationVersionNotAbandonable`。

不能只依据当前 Publication 没有引用。SUBMITTED、APPROVED 或 REJECTED 即使从未进入任何槽位，也不是可删除草稿。正常系统中从未提交 DRAFT 不可能出现在 Publication 或 History；若出现引用，属于关系损坏而不是普通“不可放弃”。

## 删除、最小事实与身份复用

成功事务从有效集合删除：

- 完整 ApplicationVersion；
- 与其一对一的 ApplicationVersionOAuthConfig。

成功事务同时写入独立且不可变的最小事实：

```text
ApplicationVersionAbandonment {
  abandonmentId
  applicationId
  versionId
  sequence
  versionLabel
  sourceRevision
  abandonedBy
  abandonedAt
}
```

Abandonment 不保存 launchUrl、capabilities、scopes、OAuth redirects 或任何 secret/hash。`abandonedBy` 仅保存在权威审计记录中，不通过本命令响应或 UC034 暴露；普通日志、trace 和 error 也不记录这些身份或被删除内容。

放弃不是 ApplicationVersion 的新审核状态。有效 Version 被删除后：

- UC034 列表不返回该项，详情按不存在处理；
- UC029 的 Version 总数和 DRAFT 数量不包含该项；
- 原 versionId 与 sequence 永不复用；Application.nextVersionSequence 不回退；
- 原 versionLabel 不再占用有效 Version 唯一性，新建草稿可以使用相同标签，但必须得到新的 versionId 和更大的 sequence；
- 不提供恢复入口；若需要相同内容，管理员必须重新创建并重新通过全部校验与审核。

## 原子性与一致性

首次成功必须在一个 MongoDB majority transaction 中完成：

1. 以 Application 当前 adminId、`lifecycleStatus=ACTIVE` 和共享 coordination fence 确认写权限；
2. 读取并验证 Version 与 OAuth 配置；
3. 检查任何 Review attempt、当前 Publication 指针和 PublicationHistory 引用；
4. 插入唯一 ApplicationVersionAbandonment；
5. 删除恰好一份 OAuth 配置和恰好一份 Version；
6. 提交全部变化。

任何一步失败都不留下 tombstone-only、Version-only 或 OAuth-only 状态。删除数量不是预期值、依附配置缺失/重复、跨 Application 归属、Review/Publication 非法引用或 tombstone 与有效 Version 同时存在，都返回 `ApplicationVersionAbandonmentStateInconsistent`，不能自动补写、跳过或部分成功。

ApplicationVersionAbandonment 至少具有全局唯一 versionId，以及单 Application 内唯一 sequence。abandonmentId 使用新的 UUIDv7；它是审计事实身份，不替代 versionId。迁移必须建立严格 validator 和索引，并把 readiness 提升到该 migration。

## OCC、幂等与并发顺序

`expectedRevision` 来自 UC034 详情。首次命令只有当前 Version revision 完全匹配时才能提交；不匹配返回现有 `ApplicationVersionRevisionConflict`。不能以 DELETE 的“最后写入胜出”覆盖刚完成的草稿编辑。

已经存在合法 abandonment 时：

- 路径 applicationId/versionId 与 tombstone 匹配、sourceRevision 等于 expectedRevision，且有效 Version/OAuth 配置均不存在：返回 `changed=false`；
- sourceRevision 不等于 expectedRevision：返回 revision conflict；
- tombstone 与仍存在的有效 Version/OAuth 配置、Review 或 Publication 引用并存：返回 state inconsistent；
- 没有有效 Version也没有 tombstone：返回 not found。

并发结果必须等价于明确先后顺序：

- **编辑草稿 vs 放弃**：编辑先提交则旧 expectedRevision 的放弃冲突；放弃先提交则编辑找不到 Version；
- **提交审核 vs 放弃**：提交先提交则 Version 不再满足从未提交 DRAFT；放弃先提交则提交找不到 Version；
- **两次放弃**：最多一次写入 tombstone，另一次按相同 sourceRevision 返回 no-op；
- **管理员转让 vs 放弃**：转让先提交后旧管理员不能成功；放弃先提交则审计记录保存原实际执行者；
- **Application 关闭 vs 放弃**：进入 CLOSING 先提交则放弃被拒绝；放弃先提交则关闭看到已经清理后的有效状态；
- **以同标签创建新草稿 vs 放弃**：只有放弃提交后标签才被释放；新草稿总是分配新 versionId 和更大 sequence。

命令不与平台暂停或管理员归档争夺业务状态；这些状态只影响在线资格，不改变 ACTIVE Application 的草稿清理权。

## 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信 USER 身份 | 沿用 `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| Application/Version 不存在、非当前管理员或路径归属不匹配 | 沿用 `APPLICATION_VERSION_NOT_FOUND` | 404 / NOT_FOUND |
| applicationId、versionId 或 expectedRevision 格式非法 | `INVALID_APPLICATION_VERSION_ABANDONMENT` | 400 / INVALID_ARGUMENT |
| HTTP 缺少强 If-Match | 沿用 `APPLICATION_VERSION_REVISION_REQUIRED` | 428 / INVALID_ARGUMENT |
| current revision 或既有 tombstone sourceRevision 不匹配 | 沿用 `APPLICATION_VERSION_REVISION_CONFLICT` | 412 / ABORTED |
| Version 非 DRAFT，或 DRAFT 已存在任意 Review attempt | `APPLICATION_VERSION_NOT_ABANDONABLE` | 409 / FAILED_PRECONDITION |
| Application 为 CLOSING/CLOSED | `APPLICATION_VERSION_ABANDONMENT_NOT_ALLOWED` | 422 / FAILED_PRECONDITION |
| OAuth、Review、Publication、History 或 tombstone 关系损坏 | `APPLICATION_VERSION_ABANDONMENT_STATE_INCONSISTENT` | 500 / INTERNAL |
| MongoDB transaction 或存储依赖不可用 | `APPLICATION_VERSION_ABANDONMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

平台 SUSPENDED、管理员 ARCHIVED 不是错误条件。调用者不能通过错误差异得知其他管理员的 Application 或 Version 是否存在。

## 业务规则

<a id="br-ver-026"></a>
### BR-VER-026：当前管理员可以清理未提交草稿

只有 Application 当前 adminId 对应的可信 USER 可以放弃该 Application 的 Version 草稿。命令不要求 APPROVED Developer，但只在 Application lifecycle ACTIVE 时可写；平台暂停和管理员归档不阻止清理。非管理员与不存在资源统一隐藏。

<a id="br-ver-027"></a>
### BR-VER-027：从未提交是可放弃的唯一内容边界

可放弃 Version 必须为 DRAFT 且不存在任何 ApplicationReview attempt。SUBMITTED、APPROVED、REJECTED 和具有历史 Review 的恢复后 DRAFT 永远不能由本命令删除；当前未被 Publication 引用不能替代该判定。

<a id="br-ver-028"></a>
### BR-VER-028：有效内容删除与最小放弃事实分离

首次成功原子删除有效 Version 及其一对一 OAuth 配置，并写入不含运行内容的不可变 ApplicationVersionAbandonment。放弃不是新的 reviewStatus；UC034 和管理计数只读取仍有效的 Version。

<a id="br-ver-029"></a>
### BR-VER-029：Version 身份不复用而标签可以重新使用

放弃不回退 nextVersionSequence，也不允许复用 versionId 或 sequence。有效 Version 被移除后，原 versionLabel 可以由以后创建的新草稿重新使用，但新草稿必须获得新的身份并重新经过全部校验与审核。

<a id="br-ver-030"></a>
### BR-VER-030：revision 前置条件与确定性幂等

首次放弃必须匹配当前 Version revision。相同 versionId 与 sourceRevision 的已完成重试返回同一 abandonment 且 `changed=false`；不同 revision 冲突。no-op 不推进 Clock、coordinationRevision 或新增审计事实。

<a id="br-ver-031"></a>
### BR-VER-031：原子删除与关系损坏失败关闭

管理权、生命周期、Version、OAuth 配置、Review、Publication、History、tombstone、删除和审计写入必须在同一本地事务中保持一致。依附缺失、非法引用、重复或部分状态一律 INTERNAL，不得自动修复或部分删除。

<a id="br-ver-032"></a>
### BR-VER-032：共享写栅栏定义并发顺序

放弃必须与草稿编辑、提交审核、管理员转让和 Application 关闭通过 Version OCC、唯一约束及 Application coordination fence 得到明确先后顺序；旧管理员、旧 revision 或已离开可放弃边界的命令不能提交。

<a id="br-ver-033"></a>
### BR-VER-033：不可恢复与最小披露

放弃成功后不提供恢复或内容读取。响应只返回定位和审计时间所需摘要；不得返回被删除运行内容、OAuth 配置、secret/hash、Reviewer 事实或 abandonedBy。日志、错误和 trace 同样不得记录这些敏感事实。

## 持久化与迁移草图

建议新增 migration `0028_application_version_abandonment`，建立 `application_version_abandonments` 集合：

```text
application_version_abandonments
  abandonmentId                       unique
  applicationId + versionId           unique
  applicationId + sequence            unique
  applicationId + abandonedAt         query-supporting index
```

validator 要求所有字段存在、禁止额外字段，并验证 UUIDv7、正 sequence/sourceRevision、非空 versionLabel/authId 与 UTC date。集合不保存 Version 内容，也不参与 `(applicationId, versionLabel)` 有效唯一索引。

现有 `application_versions` 标签唯一索引无需改成 partial index，因为有效 Version 文档在同一事务中被删除。`applications.nextVersionSequence` 不回写。当前 UC 不提供 abandonment 列表，因此 abandonedAt 索引主要服务运维审计和未来受控查询；实现若确认无当前读取方，可只保留唯一索引并在未来查询 UC 中显式增加时间索引。

## 验收场景

1. 当前管理员可以放弃刚创建或多次编辑、但从未提交的 DRAFT；Version 与 OAuth 配置原子消失，并产生一个最小 tombstone。
2. developerStatus 非 APPROVED 的当前管理员仍可放弃已有未提交草稿，但不能借本命令创建、编辑、提交或发布 Version。
3. 非管理员、旧管理员、Reviewer、SYSTEM、平台运维人员和跨 Application versionId 统一得到 NOT_FOUND。
4. SUBMITTED、APPROVED、REJECTED 均返回 not abandonable，不删除 Review、Publication 或任何依附事实。
5. 经 UC006 恢复的 DRAFT 因存在 Review attempt 返回 not abandonable。
6. ACTIVE+SUSPENDED 与 ACTIVE+ARCHIVED 仍可清理；CLOSING/CLOSED 被拒绝且不写 tombstone。
7. 正确 expectedRevision 首次返回 `changed=true`；同 revision 重试返回 `changed=false` 和同一 abandonment；不同 revision 返回冲突。
8. 放弃后 UC034 列表/详情和 UC029 Version/DRAFT 计数不再包含该 Version。
9. 放弃不回退 nextVersionSequence；使用相同 versionLabel 新建草稿得到新 versionId 和更大 sequence。
10. 与编辑、提交、转让、关闭和同标签创建并发时，结果等价于明确先后顺序，没有越权提交、孤立 OAuth 配置或重复 tombstone。
11. 缺少/重复 OAuth 配置、已有 Review、Publication/History 非法引用、tombstone 与有效 Version 并存或删除数量异常均失败关闭且事务回滚。
12. HTTP DELETE 拒绝 body/query、弱或非法 If-Match；原生 gRPC 与 HTTP 共享身份、OCC、幂等、错误和响应语义。
13. 成功、no-op 和领域错误都设置 `private, no-store`，响应与 telemetry 不泄露被删除内容、身份凭据或内部数据库错误。
14. 命令不调用 Scope Catalog、URL preflight 或 Auth，不改变 Application、Review、Publication、OAuth client、Tester、Filter 或 Profile 状态。

## 实现依赖与交付边界

实现至少需要：

- `iwut-app-center-api`：在现有 ApplicationVersion service 增加 abandon RPC、最小 abandonment response 和稳定 error reasons；
- `iwut-app-center`：独立 command usecase/port、领域 abandonment 事实、MongoDB transaction adapter、HTTP/gRPC transport 与 composition wiring；
- MongoDB：`0028_application_version_abandonment` migration、严格 validator、唯一索引和 readiness；
- 查询兼容：UC034 与 UC029 继续只读取有效 Version，并验证 tombstone 不与有效 Version 共存；
- 测试：资格边界、恢复后 DRAFT、OCC/no-op、标签再用、管理权转让/提交/编辑/关闭并发、损坏关系、回滚、HTTP/gRPC 与真实 MongoDB 验收；
- 最终门禁：`make check-full`。

本用例不需要 Auth schema/API 变化或真实 OAuth 流程，因此不以 `make check-auth-app` 作为最低验收层级。若实现需要删除 Review/Publication 历史、增加 `ABANDONED` reviewStatus、调用 Auth 或清理跨服务 grant/token，说明范围已偏离本用例，必须返回设计层重新评审。

## 变更记录

- 2026-10-10：建立 UC-APP-035 提案；产品确认通用“删除未发布版本”应收敛为放弃从未提交审核的 DRAFT，并保留最小不可变放弃记录。
- 2026-10-10：产品审核通过，状态转为 ACCEPTED；固定仅放弃从未审核 DRAFT、最小 abandonment、身份不复用和标签可再用边界。
