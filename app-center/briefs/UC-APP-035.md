<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-035 --spec tools/brief-specs/UC-APP-035.json -->
# Brief — UC-APP-035：放弃从未提交审核的 ApplicationVersion 草稿

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-035` 放弃从未提交审核的 ApplicationVersion 草稿 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-VER-026`–`BR-VER-033`（8 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 设计结论

> Application 当前管理员可以永久放弃一份从未提交审核的 DRAFT ApplicationVersion。该命令不是“删除所有未发布版本”：SUBMITTED、APPROVED、REJECTED，以及从 REJECTED 恢复而来并已具有 Review 历史的 DRAFT，都不能通过本用例删除。

“未发布”不是安全的删除条件。APPROVED Version 即使当前不在 Test、Grey 或 Stable 槽位中，仍保存有效审核决定并可能再次发布；SUBMITTED 正在接受审核；REJECTED 和恢复后的 DRAFT 都连接不可变 Review snapshot、decision 或 restoration。删除这些记录会破坏审核、发布资格与审计关系。

因此本用例只解决 Developer Console 中无用初始草稿无法清理的问题，并把用户动作命名为“放弃草稿”。成功后 Version 当前内容及其一对一 OAuth 配置从有效数据中永久移除，另存最小不可变 `ApplicationVersionAbandonment` 事实支持审计和安全重试。放弃不新增 `ABANDONED` reviewStatus，也不改变任何 Review 或 Publication。

### 目标与范围

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

### 参与者与授权

- **放弃者**：Gateway 验证后的可信 USER，且其 `authId` 等于 Application 当前保存的 `adminId`。
- **App Center**：拥有 Application、Version、OAuth 配置、Review、Publication 与 Abandonment 权威记录，并在本地事务中执行命令。

本命令不要求 developerStatus=`APPROVED`。Developer 资格下降后，当前管理员仍可通过 UC034 读取并清理自己已有的从未提交草稿；这不授予其创建、编辑、提交或发布 Version 的能力，那些写命令继续执行各自的 Developer 资格检查。

Application 必须保持 `lifecycleStatus=ACTIVE`。平台 `AVAILABLE/SUSPENDED` 与管理员 `UNARCHIVED/ARCHIVED` 不阻止草稿清理，因为放弃不会产生新的运行资格或在线效果。进入 CLOSING 或 CLOSED 后，全部配置写入继续停止，本命令返回 `ApplicationVersionAbandonmentNotAllowed`。

Reviewer 权限、平台 suspend/restore 权限、SYSTEM service identity、Tester 身份和其他角色都不隐式授权。可信身份验证后，Application 或 Version 不存在、调用者不是当前管理员、versionId 不属于路径 Application，统一返回 `ApplicationVersionNotFound`，避免跨 Application 枚举。

### 命令与 API 草图

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

### “从未提交”的权威判定

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

### 删除、最小事实与身份复用

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

### 原子性与一致性

首次成功必须在一个 MongoDB majority transaction 中完成：

1. 以 Application 当前 adminId、`lifecycleStatus=ACTIVE` 和共享 coordination fence 确认写权限；
2. 读取并验证 Version 与 OAuth 配置；
3. 检查任何 Review attempt、当前 Publication 指针和 PublicationHistory 引用；
4. 插入唯一 ApplicationVersionAbandonment；
5. 删除恰好一份 OAuth 配置和恰好一份 Version；
6. 提交全部变化。

任何一步失败都不留下 tombstone-only、Version-only 或 OAuth-only 状态。删除数量不是预期值、依附配置缺失/重复、跨 Application 归属、Review/Publication 非法引用或 tombstone 与有效 Version 同时存在，都返回 `ApplicationVersionAbandonmentStateInconsistent`，不能自动补写、跳过或部分成功。

ApplicationVersionAbandonment 至少具有全局唯一 versionId，以及单 Application 内唯一 sequence。abandonmentId 使用新的 UUIDv7；它是审计事实身份，不替代 versionId。迁移必须建立严格 validator 和索引，并把 readiness 提升到该 migration。

### OCC、幂等与并发顺序

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

### 错误语义

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

### 持久化与迁移草图

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

### 验收场景

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

### 实现依赖与交付边界

实现至少需要：

- `iwut-app-center-api`：在现有 ApplicationVersion service 增加 abandon RPC、最小 abandonment response 和稳定 error reasons；
- `iwut-app-center`：独立 command usecase/port、领域 abandonment 事实、MongoDB transaction adapter、HTTP/gRPC transport 与 composition wiring；
- MongoDB：`0028_application_version_abandonment` migration、严格 validator、唯一索引和 readiness；
- 查询兼容：UC034 与 UC029 继续只读取有效 Version，并验证 tombstone 不与有效 Version 共存；
- 测试：资格边界、恢复后 DRAFT、OCC/no-op、标签再用、管理权转让/提交/编辑/关闭并发、损坏关系、回滚、HTTP/gRPC 与真实 MongoDB 验收；
- 最终门禁：`make check-full`。

本用例不需要 Auth schema/API 变化或真实 OAuth 流程，因此不以 `make check-auth-app` 作为最低验收层级。若实现需要删除 Review/Publication 历史、增加 `ABANDONED` reviewStatus、调用 Auth 或清理跨服务 grant/token，说明范围已偏离本用例，必须返回设计层重新评审。

## 业务规则（UC-APP-035 权威正文）

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-026 -->
### BR-VER-026：当前管理员可以清理未提交草稿

只有 Application 当前 adminId 对应的可信 USER 可以放弃该 Application 的 Version 草稿。命令不要求 APPROVED Developer，但只在 Application lifecycle ACTIVE 时可写；平台暂停和管理员归档不阻止清理。非管理员与不存在资源统一隐藏。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-027 -->
### BR-VER-027：从未提交是可放弃的唯一内容边界

可放弃 Version 必须为 DRAFT 且不存在任何 ApplicationReview attempt。SUBMITTED、APPROVED、REJECTED 和具有历史 Review 的恢复后 DRAFT 永远不能由本命令删除；当前未被 Publication 引用不能替代该判定。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-028 -->
### BR-VER-028：有效内容删除与最小放弃事实分离

首次成功原子删除有效 Version 及其一对一 OAuth 配置，并写入不含运行内容的不可变 ApplicationVersionAbandonment。放弃不是新的 reviewStatus；UC034 和管理计数只读取仍有效的 Version。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-029 -->
### BR-VER-029：Version 身份不复用而标签可以重新使用

放弃不回退 nextVersionSequence，也不允许复用 versionId 或 sequence。有效 Version 被移除后，原 versionLabel 可以由以后创建的新草稿重新使用，但新草稿必须获得新的身份并重新经过全部校验与审核。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-030 -->
### BR-VER-030：revision 前置条件与确定性幂等

首次放弃必须匹配当前 Version revision。相同 versionId 与 sourceRevision 的已完成重试返回同一 abandonment 且 `changed=false`；不同 revision 冲突。no-op 不推进 Clock、coordinationRevision 或新增审计事实。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-031 -->
### BR-VER-031：原子删除与关系损坏失败关闭

管理权、生命周期、Version、OAuth 配置、Review、Publication、History、tombstone、删除和审计写入必须在同一本地事务中保持一致。依附缺失、非法引用、重复或部分状态一律 INTERNAL，不得自动修复或部分删除。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-032 -->
### BR-VER-032：共享写栅栏定义并发顺序

放弃必须与草稿编辑、提交审核、管理员转让和 Application 关闭通过 Version OCC、唯一约束及 Application coordination fence 得到明确先后顺序；旧管理员、旧 revision 或已离开可放弃边界的命令不能提交。

<!-- 权威位置: use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md#br-ver-033 -->
### BR-VER-033：不可恢复与最小披露

放弃成功后不提供恢复或内容读取。响应只返回定位和审计时间所需摘要；不得返回被删除运行内容、OAuth 配置、secret/hash、Reviewer 事实或 abandonedBy。日志、错误和 trace 同样不得记录这些敏感事实。

## 架构决定（仅本次需要的章节）

### ADR-003：Go package 与依赖边界（`ACCEPTED`）

#### 决定

代码首先按业务能力组织，每项能力内部再分 Domain、UseCase 与 Port：

```text
internal/application/domain
internal/application/usecase
internal/application/port
internal/version/domain
internal/version/usecase
internal/version/port
internal/profile/domain
internal/profile/usecase
internal/profile/port
internal/publication/...
internal/tester/...
internal/catalog/...
```

跨能力稳定且确实共享的类型放入小型 `internal/shared` package。只有在至少两个已实现能力出现相同语义时才提升为共享类型，不提前建立通用工具箱。

基础设施放在能力之外：

```text
internal/adapter/mongo
internal/adapter/auth
internal/adapter/transport
cmd/app-center
```

主要依赖方向为：

```text
transport -> usecase -> domain
adapter -> capability port + required domain types
composition root -> concrete implementations
```

Domain 不依赖 Kratos、MongoDB driver、Proto 生成包、HTTP、配置或具体日志实现。UseCase 只依赖 Domain 与当前能力声明的 ports。Adapter 实现 ports，composition root 负责组装。

能力间协作通过显式应用服务、port 或只读 Query 接口完成。一个能力不得直接导入另一个能力的 MongoDB document 或未导出的聚合内部结构。

当前代码树只使用表达业务职责的目录名，不以迁移阶段或实现世代划分代码。

#### Port 所有权

Port 由使用它的能力拥有，而不是由提供方或某个全局 infrastructure package 拥有。例如 Application 创建用例需要的原子持久化接口位于 `internal/application/port`，MongoDB adapter 在外部实现它。

Port 方法使用业务语言并表达所需原子边界，不先建立 `Save/Get/Delete` 式通用 Repository。只有多个实际用例证明通用操作具有相同语义时才抽取。

#### 自动化约束

代码仓库根目录的 `architecture_test.go` 作为 ADR 的可执行护栏，并由 `go test ./...` 自动运行。它至少强制以下规则：

- 业务能力的 Go 文件只能位于该能力的 `domain`、`usecase` 或 `port` package。
- Domain 的项目内依赖只能指向 `internal/shared`，并禁止 MongoDB、HTTP、Proto、配置、JSON 和具体日志依赖及 `bson/json/protobuf` struct tag。
- Port 只能依赖同能力 Domain 与 `internal/shared`。
- UseCase 只能依赖同能力 Domain、Port 与 `internal/shared`。
- `internal/shared` 不得反向依赖任何业务能力。
- Domain、UseCase、Port 与 `internal/shared` 默认不得新增第三方依赖；确需窄依赖时先接受相应架构变更并显式调整测试。
- 已接受的窄例外（2026-09-27，UC-APP-013）：仅 `internal/profile/domain` 可直接导入 `golang.org/x/text/unicode/norm`，用于 BR-PRF-003–005 的纯 NFC 规范化。它无网络、时钟或存储副作用；不扩大到 x/text 其他包、其他能力、UseCase、Port 或 shared。架构测试必须同时覆盖允许位置及这些拒绝位置。
- 具体 adapter package 之间不得互相导入；只有 transport adapter 可以导入 UseCase，MongoDB/Auth 等 provider adapter 只面向能力 Port 与必要的 Domain 类型。
- Adapter 不得读取 `internal/config`；只有 composition root 可以同时依赖配置与具体 adapter。
- 禁止全局 `internal/biz`、`internal/data`、`internal/domain`、`internal/service` 和 `internal/util` package。
- composition root 只位于 `cmd/app-center`。

自动化检查只维护依赖和物理结构，不推断业务语义，也不取代 BR 测试和评审。确有新依赖方向需求时，必须先修改本 ADR，再在同一变更中调整架构测试；不得通过删除、跳过或弱化测试绕过边界。

### ADR-004：MongoDB 事务与 Schema 管理（`ACCEPTED`）

#### 决定

App Center 的权威写模型使用支持多文档事务的 MongoDB 部署拓扑。开发、测试和生产至少运行 replica set 或其他被当前 MongoDB 版本明确支持事务的拓扑；不支持事务的 standalone 部署不属于受支持环境。

跨文档 BR 使用 MongoDB transaction 实现，并遵循：

- 事务内只执行本地 MongoDB 读写，不调用 Auth、HTTP、消息系统或其他远程服务。
- 外部校验在事务前完成；BR 要求最终复检的本地事实在事务内重新读取或通过条件写保护。
- transient transaction error 或 unknown commit result 按 MongoDB 官方语义重试完整事务/提交，不单独重试其中一次写入。
- 事务重试使用同一组命令输入、ID 与审计时间，避免一次逻辑操作产生多个身份或时间。
- 唯一索引、条件更新和事务共同保护并发不变量；应用层的预检查只用于改善错误体验。
- Adapter 把 duplicate key、write conflict 和事务失败映射为当前 port 能表达的稳定结果。

Repository port 优先暴露一个完整业务原子行为，例如 `CreateWithinQuota`。当一个 UseCase 必须协调多个独立聚合 Repository 时，可以引入窄的 Transaction Manager，但不能让 Domain 感知 MongoDB session。

#### Schema 与索引

collection、validator、索引和 schema revision 通过显式、版本化、可重复执行的迁移管理：

- 普通服务启动不创建、删除或修改生产索引与 validator。
- 迁移在部署前单独执行，并记录成功的 migration ID。
- 重复执行已成功迁移是安全的。
- 破坏性变更必须先有对应设计决定和恢复方案。
- 新集合从首次创建起使用明确的 validator 与命名索引。
- 集成测试验证实际索引、validator 和事务行为，而不仅测试 mapper。

具体 collection 名由对应 UC 的数据模型和实现工作包确定，不在本 ADR 中建立跨能力的统一 document 形状。

#### 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

### ADR-005：领域错误与 Transport 映射（`ACCEPTED`）

#### 决定

Domain 与 UseCase 使用协议无关的稳定错误分类。每个可预期业务失败具有：

```text
stable code
human-readable internal message
optional safe details
optional wrapped cause
```

稳定 code 使用设计文档中的业务失败名称。调用者通过错误类型、code 或 `errors.Is` 判断，不解析 message。

错误分为：

- Validation：输入无法形成合法值对象。
- Authentication：缺少或无效可信身份。
- Authorization：身份存在但没有执行权限。
- NotFound：目标不存在，或按隐私规则必须隐藏归属不匹配。
- Conflict：状态、唯一性、revision、容量或并发前置条件冲突。
- DependencyUnavailable：完成当前行为所需的外部事实暂不可用。
- Internal：未预期的实现或基础设施失败。

MongoDB/Auth 等 adapter 负责把技术错误转换为 port 定义的稳定结果，同时保留 cause。UseCase 再按业务上下文确定最终领域错误。例如 duplicate key 不能直接泄露索引名。

Transport adapter 在一个集中映射表中把领域错误转换为：

- 稳定 Proto error reason；
- canonical gRPC status；
- 对应 HTTP status；
- 可以安全返回的 message/details。

新 API 不采用“所有 HTTP 响应都返回 200，再在 JSON body 中表达错误”的形式。HTTP 与 gRPC 使用各自标准状态语义，稳定业务 code 供客户端做细分处理。

未知错误统一映射为 Internal，不向客户端返回 cause、数据库字段、索引名、远程地址、token、secret 或 stack trace。日志和 trace 在服务端保留原 cause，并使用同一 trace ID 关联。

#### 隐私与存在性隐藏

当 UC 规定跨 Application 的资源归属不匹配按 NotFound 处理时，Transport 不得把内部的“存在但不属于调用者”转换成 Forbidden。存在性隐藏属于业务契约，而不是展示文案。

错误 details 采用明确 allowlist。字段校验可以返回安全字段名和约束类别，但不能回显任意用户内容或凭证。

### ADR-006：Proto v1 与独立 API 仓库协作（`ACCEPTED`）

#### 决定

新协议在 API 仓库使用独立命名空间和目录：

```text
app_center/v1/...
package app_center.v1.<capability>
```

`v1` 只表示共享协议命名空间，不进入 App Center 的领域 package、collection 名或业务身份。Schema revision 由 migration ledger 中的 `0001`、`0002` 等迁移 ID 管理，collection 名保持无版本的业务命名。

Proto 源文件继续由独立 API 仓库拥有。App Center 服务仓库固定引用一个明确的 API repository revision；不得依赖浮动分支或在服务仓库手工维护生成代码的私有修改。

协作顺序为：

1. Domain 与 UseCase 通过自己的 Command/Result 类型稳定业务行为。
2. 在 API 仓库增加或修改 v1 Proto、error reason 和生成配置。
3. 生成代码并在 API 仓库通过检查后提交。
4. App Center 更新固定 revision。
5. Transport adapter 显式完成 Proto 与 UseCase 类型转换。
6. 两个仓库分别使用各自可审查的 commit。

Proto 不直接复用 Domain struct，也不把生成 message 传入 Domain。字段 presence、oneof、timestamp、enum unknown value 和 transport validation 在 adapter 边界处理。

#### 协议演进

即使系统尚未上线，已提交到共享 API 仓库的 v1 字段编号也保持稳定：

- 不重用删除字段的编号或名称，使用 `reserved`。
- enum 保留明确的 `UNSPECIFIED = 0`，业务上不接受时由 adapter 拒绝。
- 不把数据库内部字段、comparison key、技术计数器或 secret 暴露为公共字段。
- 写请求不接受可信身份、服务端状态和审计字段。
- 分页 cursor 是不透明 bytes/string，不承诺内部编码。
- Error reason 与 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 的稳定业务 code 对齐。

HTTP annotation 和 gRPC service 共享同一 Proto 语义。HTTP API 使用 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 定义的标准状态映射。

#### 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/app-center-api-routing.md`：App Center API 路由 v1 契约

#### 路由映射

App Center 的每个 HTTP 资源在 Proto 内部使用的路径**不含服务前缀**。Gateway 为外部请求增加且只增加一个服务前缀 `/app-center`。

首个正式资源 CreateApplication 的映射是：

| 层 | 方法与路径 | 说明 |
| --- | --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications` | 客户端唯一可见的地址；`app-center` 是服务前缀 |
| Gateway | 剥离前缀 `/app-center` | 只做前缀剥离，不重写其余路径 |
| 内部（Gateway → App Center） | `POST /v1/applications` | Proto `google.api.http` annotation 声明的路径；请求体 `body: "*"` |
| gRPC | `/app_center.v1.application.Application/CreateApplication` | proto package `app_center.v1.application`，service `Application`，rpc `CreateApplication` |

UC-APP-005 审核决定命令遵循同一映射规则：

| 层 | 方法与路径 |
| --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| Gateway | 只剥离前缀 `/app-center` |
| 内部（Gateway → App Center） | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| gRPC | `/app_center.v1.application_review.ApplicationReview/DecideApplicationVersionReview` |

规则：

- Gateway 必须按**服务名到前缀**的映射表工作，不得把 `/app-center` 硬编码进业务路径，也不得同时改写内部资源路径。
- 前缀剥离后必须保留查询串与请求体。
- 内部路径与 gRPC full method 由 Proto 定义，App Center 的 HTTP 路由注册必须与 Proto annotation 一致；两者不得各写一份。
- 写请求只通过请求体传递资源字段；可信身份只通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 定义的 `x-iwut-identity` 传递，路径或 query 不承载身份。
- 未匹配的服务前缀或缺少前缀的外部请求由 Gateway 拒绝，不转发给 App Center。

#### gRPC-Web 终止

- gRPC-Web 在 **Traefik** 终止，不进入 App Center 进程。
- App Center 后端只暴露**原生 gRPC**；不嵌入 `grpc-web` wrapper，也不注册 gRPC-Web 专用的 HTTP handler。
- 浏览器流量由 Traefik 完成 gRPC-Web ⇄ gRPC 转换后，以原生 gRPC 到达 App Center；身份键仍为 metadata `x-iwut-identity`。
- 因此 App Center 不为 gRPC-Web 增加 CORS、content-type 或协议转换配置；这些属于 Traefik。

#### 契约测试要求

外部到内部的映射必须由**自动化契约测试**机械验证，不能只靠文档。测试至少断言：

1. Proto HTTP annotation 的内部路径等于 `POST /v1/applications`。
2. 外部路径等于服务前缀 `/app-center` 加内部路径，即 `POST /app-center/v1/applications`。
3. 前缀映射只剥离 `/app-center`，得到的内部路径与第 1 项一致。
4. gRPC full method 等于 `/app_center.v1.application.Application/CreateApplication`。
5. 写请求 message 只包含 `name`，不包含身份字段（`authId`、`developer_status`）、服务端字段（`id`、`adminId`、`createdAt`）或持久化技术字段。
6. 响应 message 不包含 `nameKey`、`nextVersionSequence`、`nextProfileRevisionSequence` 或其它内部技术字段。
7. 审核决定的外部/内部路径与上述 UC-APP-005 映射精确一致，gRPC full method 使用同一生成 service。
8. UC-APP-005 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

外部路径可以作为 contract constant / fixture 存在于测试中，但它必须与内部路径、前缀和 gRPC method 在同一测试里被自动验证，任何一侧漂移都必须让测试失败。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-035`（use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md）：变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-035-abandon-unsubmitted-application-version-draft.md` | 283 | `42cc1cff657d` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
