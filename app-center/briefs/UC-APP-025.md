<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-025 --spec tools/brief-specs/UC-APP-025.json -->
# Brief — UC-APP-025：协调账号归属退出与个人状态清理

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-025` 协调账号归属退出与个人状态清理 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-008`–`BR-APP-011`（4 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-006` |
| 平台共享 | `platform/contracts/account-owner-exit-v1.md`、`platform/contracts/auth-developer-status-v1.md`、`platform/contracts/trusted-service-identity-v1.md` |

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

### 目标与范围

向获授权 Auth 服务提供归属退出准备、终局提交及清理状态查询，支持 Auth UC024/025 在零应用归属条件下安全退出资格或注销账号。App 在本地事务内阻止并发新增归属，并为账号注销清理自身实际持有的个人状态。

本轮不实现应用转让、关闭、恢复、管理员临时接管或应用下架。有名下应用的用户明确 BLOCKED；不假装发布槽清空等于应用已处置。共享线格式、重试、决定查询及终局规则唯一引用 [account-owner-exit-v1](../../platform/contracts/account-owner-exit-v1.md)。

### 主流程与 API

1. Auth 先保存准备操作，通过 service JWS 调用 PrepareAccountOwnerExit。
2. App 在线验证方法权限和 caller，在账号归属事务栅栏内检查当前所有应用义务：非零返回 BLOCKED；零归属则保存不可变准备 receipt 和屏障，返回 PREPARED。
3. Auth 作出持久 COMMITTED/CANCELLED 决定后调用 FinishAccountOwnerExit，App 核对绑定并单调提交终局，CANCELLED 允许先于 Prepare 到达。
4. COMMITTED 将归属屏障永久 sealed；ACCOUNT_CLOSURE 另调度持久清理任务，DEVELOPER_WITHDRAWAL 不删除普通用户个人数据。
5. Auth 通过 GetAccountOwnerExitStatus 获取终局及个人清理回执；App 收敛任务可回查 Auth 的 GetAccountOwnerExitDecision，不根据超时或 NOT_FOUND 自行解除屏障。

方法/字段号/service permissions 按共享契约；只提供原生 gRPC，无 HTTP/gRPC-Web/Gateway。未知调用者、缺方法 permission、错误用途/receipt 拒绝；消息冲突为 FAILED_PRECONDITION，未知状态查询为 NOT_FOUND，存储/依赖故障为 UNAVAILABLE。不得返回个人资料或把底层错误当作零应用。

### 数据与验收

新增 Mongo migration 0020，仅创建本能力集合/validator/索引，不迁移旧 Auth 数据或回填权限。fence 按 authId 唯一，operations 按 operationId 唯一并按 authId/decision 查询；清理进度有界，不记录服务 token 或完整用户身份。

验证真实事务中的 Prepare/Create、Prepare/TesterJoin、终局/清理竞争，取消先到、receipt 错配、永久封闭继承、超时不解锁、双方重启和清理幂等。验证 WITHDRAWN 普通身份、APPROVED 开发门禁、ACTIVE/DISABLED/CLOSED 角色敏感审核判断，以及真实 Auth UC002/内部决定 provider 联调。

执行 make check-full 与 make check-auth-app；Auth 新工作包尚未合入时可先做提供方测试，但最终不得以 fake server 代替跨服务验收。独立开关默认关闭，启用要求 Auth 调用方与回查 service identity 配置齐备，外部不公开本能力。

### 交付依赖

依赖既有 UC001 创建事务、UC009 Tester 事务及 UC005 审核流程，新增 Auth UC024/025 决定 provider。与 Auth 同批交付，完整产品仍需客户端/部署门禁；本用例并不交付已有应用的归属处置入口。

## 业务规则（UC-APP-025 权威正文）

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-008 -->
### BR-APP-008：归属屏障与零义务准备

`adminId=authId` 的所有 Application 都阻止 Prepare，无论其发布或审核状态。使用 `account_owner_exit_fences` 的 authId 唯一记录作为可写事务栅栏；创建应用和 Prepare 在同一事务中先条件写该栅栏，再读取/修改配额和应用，不能仅用 snapshot 读检查。

PREPARED 和永久 sealed 均阻止新的创建；当前没有转让/关闭入口，未来增加这些行为必须在相同协调点检查。旧 APPROVED JWS 不能越过栅栏。账号没有旧 fence 时可原子建立 OPEN 初始事实，不代表补建 Auth 用户。

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-009 -->
### BR-APP-009：单调终局与持久收敛

操作保存 `(authId, operationId, purpose, receiptId)` 与决定，event/operationId 唯一。相同请求幂等，不同绑定冲突。CANCELLED 先到保存终局，延迟 Prepare 拒绝；COMMITTED 不可取消或解封。已因 Developer 退出 sealed 后注销再取消，只取消当前临时变化，不能恢复旧 OPEN。

终局与持久清理/回查任务同一本地事务。App 不按 TTL 解封、不在数据库事务中调用 Auth；未知决定保持屏障，按共享契约有界重试。无需 Redis，生产后台工作器必须可重启继续处理。正常服务启动不能清除操作决定或 sealed 记录。

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-010 -->
### BR-APP-010：注销个人状态清理

ACCOUNT_CLOSURE 的准备及永久 sealed 同时阻止 Tester Join 新增个人状态；DEVELOPER_WITHDRAWAL 仍允许普通 Tester 加入。创建/Join 与 Prepare 共用账号栅栏，涉及 Application coordination fence 时统一顺序 account→Application。

COMMITTED ACCOUNT_CLOSURE 后以有界批次清理该 testerAuthId 的全部 ACTIVE/REMOVED membership episode，并在各 Application coordination fence 内处理，保证人数计数及并发移除一致；其他用户不受影响。零应用账号的 creation quota 可以删除。仅在扫描为空并确认不可重建时标为 COMPLETE。

application_filters/filter_revisions 是应用公开 Filter，不是用户偏好，不能删除。保留 Application、Version、Review、Publication 及历史 createdBy/submittedBy/reviewer 等归因；当前没有独立个人偏好 collection，禁止凭名称猜测清理表。未来新增个人数据需显式纳入清单。

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-011 -->
### BR-APP-011：退出与终止状态的消费

USER JWS 的 WITHDRAWN 是合法身份状态：开发者写入口仍仅允许 APPROVED，普通功能和独立 reviewer 权限不因枚举出现而整体验签失败。

Auth UC002 增加账号状态投影。版本审核批准检查明确区分角色：当前 admin 必须 accountStatus=ACTIVE 且 developerStatus=APPROVED；历史 submittedBy 为 WITHDRAWN 或 CLOSED 不因主动退出本身否定不可变提交，历史提交者 SUSPENDED 或 DISABLED 仍阻止批准。同一人兼任 owner/submitter 时取更严格的 owner 条件。任何未知、损坏或查询故障保持 PENDING，不能作为自动拒绝的证据。

权威状态明确不满足门禁时，沿 UC005 SYSTEM 自动 REJECT 流程，固定文本“当前应用管理员或审核提交者不满足账号与开发者资格要求，待处理审核已由系统自动拒绝。”；不改变已完成的决定。UC005 port 改为显式传入 currentAdminId/submittedBy 的批准资格检查，不能靠数组顺序猜角色。

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

#### 测试环境

MongoDB 集成测试使用真实、支持事务的隔离数据库。测试环境必须能够：

- 初始化 replica set 或连接到等价事务拓扑。
- 每个测试套件使用独立 database/collection 前缀。
- 执行显式迁移。
- 验证并发竞争、事务回滚、唯一索引与 validator。
- 在测试结束时只清理本套件拥有的资源。

内存 fake 只用于 Domain/UseCase 单元测试，不能证明事务或索引语义。

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

### `platform/contracts/account-owner-exit-v1.md`：账号退出时的 App 归属协调 v1

#### 范围与事实来源

本契约是 [UC024](../../auth-center/use-cases/UC-AUTH-024-withdraw-developer.md) 和 [UC025](../../auth-center/use-cases/UC-AUTH-025-close-own-account.md) 所需的 Auth/App 实现契约，App 工作包见 UC-APP-025。Auth 决定资格退出或账号终止；App 决定哪些应用及归属操作仍需该账号承担责任，并阻止并发新增归属。不能用一次无保护的查询代替本协议。

首版 App 中所有 `adminId=authId` 的 Application（包括草稿、审核中、未发布、已发布）都阻止退出。仅清空发布槽不算处置；转让、关闭如何移除归属义务由后续 App UC 明确，在其交付前拥有应用的用户无法完成此流程。历史 creator/reviewer 引用不等于当前所有权，但存在仍需该账号负责的待处理归属操作也阻止退出。

#### 内部接口

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

另由 Auth 向获授权 App 提供 `GetAccountOwnerExitDecision(authId, operationId)`，返回 `PENDING | COMMITTED | CANCELLED`；未知操作返回 NOT_FOUND，不能解释为已取消。Auth 保存的 purpose 和归属目标必须与 App 一致；已获得的非空 receipt 必须精确一致。消息中的 authId 只是被治理对象，不是伪造的终端操作人身份。

#### App 原子屏障

App 的 Prepare 在同一账号归属事务栅栏下检查义务并安装屏障。所有创建应用、转入所有权、撤销转出、恢复已关闭应用以及将来可能增加归属义务的写操作必须参与同一栅栏；包括持有旧 APPROVED JWS 的请求。不能只在 HTTP handler 做预检查。

存在义务时返回 BLOCKED，不安装屏障，不自动转让、关闭或删除应用；用户处理后用新操作重试。零义务时返回 PREPARED，保存不可变 `(authId, operationId, purpose, receiptId)`，阻止该账号新增归属，直到收到终局决定。重复相同请求返回同一结果；同 operationId 换 authId/purpose 或不匹配 receipt 拒绝。

COMMITTED 将本次屏障变为永久 sealed，不允许未来凭旧 JWS 创建或转入应用。首版 Developer 退出不支持重新开通，因此无需解封接口。已因 Developer 退出 sealed 的账号之后申请注销时，仍重新核验无义务，为注销 operation 生成独立 receipt；取消注销不会解除之前的永久 sealed 状态。

COMMITTED 必须携带与 App 完全匹配的非空 receiptId。CANCELLED 允许 receiptId 为空，以覆盖 Prepare 已建立屏障但回包丢失的情况；只对可信 Auth 调用且 authId/operationId/purpose 全部匹配生效，传入非空 receiptId 时仍必须精确匹配。CANCELLED 仅解除该 operation 创建的临时屏障，不能解除其他操作或既有永久 sealed。即使 Prepare 尚未到达，Finish(CANCELLED) 也保存该 operation 的终局记录，拒绝后来延迟到达的 Prepare；不能出现“先取消，再被迟到的准备永久锁住”。一个 authId 同时最多一个未决归属退出操作。

#### Auth 协调与故障

Auth 先保存 PENDING 操作，再调用 Prepare；准备操作寿命最多 10 分钟。随后在 Auth 事务中复核 Session/专用注销证明、accountRevision、developerRevision、权限和业务条件，只有 PREPARED receipt 对应原操作且仍在期限内才可提交资格退出/账号终止，同时写 COMMITTED 决定与待投递通知。

用户取消、条件变化或准备超时由 Auth CAS 为 CANCELLED，不能取消已提交操作。事务提交结果未知时先读取权威决定，不发送推测的 CANCELLED。账号终止后的清理任务不能删除尚未被 App 确认的协调决定。

App 屏障不按租约或本地 TTL 自动解除：Auth 可能已经提交而通知丢失。双方使用持久化、幂等重试收敛，App 可向 Auth 查询终局；Auth 不可用时保持屏障并返回依赖故障。孤立 PENDING 由 Auth 到期任务确认取消再通知，不以“找不到”当取消。故障期间用户可见“处理中/尚未完成”，不能声称数据或资格已经删除。

App 收到终局后回执；Auth 在回执前保留决定。只有协调已终结且超过外部调用最大重试窗口后才允许压缩操作明细；永久 sealed 的最小 authId/purpose/终止操作引用保留。终局不得回退。此为两个本地事务与持久补偿，不假设分布式事务、消息必达或 Redis。

#### 固定线格式与方法授权

App package `app_center.v1.account_owner_exit`、service `AccountOwnerExitService`，PrepareAccountOwnerExit / FinishAccountOwnerExit / GetAccountOwnerExitStatus 分别要求 `app.account-owner-exit.prepare` / `app.account-owner-exit.finish` / `app.account-owner-exit.read`，仅授权 Auth caller。Auth package `auth_center.v1.account_owner_exit`、service `AccountOwnerExitDecisionService/GetAccountOwnerExitDecision` 要求 `auth.account-owner-exit.read`，仅 App caller。均无 HTTP annotation 或终端路由。

消息字段号固定：PrepareRequest auth_id=1, operation_id=2, purpose=3；FinishRequest auth_id=1, operation_id=2, receipt_id=3, decision=4, purpose=5；GetStatusRequest 与 GetDecisionRequest 均 auth_id=1, operation_id=2。Purpose 枚举 0=UNSPECIFIED(拒绝),1=DEVELOPER_WITHDRAWAL,2=ACCOUNT_CLOSURE；Decision 0=UNSPECIFIED,1=PENDING,2=COMMITTED,3=CANCELLED，Finish 不允许 PENDING。

PrepareResponse outcome=1（0非法,1=PREPARED,2=BLOCKED）,receipt_id=2,blocker=3（0=NONE,1=OWNED_APPLICATIONS,2=PENDING_OWNERSHIP_CHANGE）。App 状态/Finish 响应统一 auth_id=1,operation_id=2,purpose=3,decision=4,receipt_id=5,cleanup_state=6（0非法,1=NOT_REQUIRED,2=PENDING,3=COMPLETE）。GetDecisionResponse decision=1,purpose=2,receipt_id=3。状态查询对未知 operation 返回 NOT_FOUND，不暗示取消。

App 的 ACCOUNT_CLOSURE COMMITTED 持久创建个人清理任务，GetStatus 的 cleanup_state=COMPLETE 才表示个人数据清理回执；WITHDRAWAL 为 NOT_REQUIRED。Auth 先调用 Finish 再轮询持久状态确认 App 回执，不把 Finish 网络成功误认为全部清理完成。App 也可回查 Auth 终局用于收敛。

AuthId 沿用现有 1..200 bytes opaque ID；operationId 为 Auth UUIDv4，receiptId 为 App 生成 UUIDv7，不作秘密；所有比较原样精确。双边后台重试初始 1 秒、指数退避最大 60 秒，每批最多 100，RPC deadline 5 秒，含有界抖动。部署参数可调整但不得把到期当作自动解除屏障。每个操作的终局摘要永久保留至关联墓碑被明确政策替代，避免任意迟到 Prepare 越过已清理的取消记录；大体量诊断材料在回执后 30 天内清理。

#### 交付门禁

提供方权威用例为 UC-APP-025，支持零归属用户。转让/关闭已有应用不在本轮，有应用者持续 BLOCKED。必须更新实际创建入口和 ACCOUNT_CLOSURE 下 Tester 加入入口，防止旧 JWS 重建个人状态；未来增加归属写入口必须复用此屏障。

验收覆盖 Prepare 与创建竞争、取消先于 Prepare、Auth 提交后丢响应、双边重启、长时间故障、过期准备、重复 Finish、目标/receipt/purpose 错配、WITHDRAWN 后注销取消不解除原 sealed、注销清理与 Tester 加入竞争。联调前退出/注销公网开关保持关闭。

### `platform/contracts/auth-developer-status-v1.md`：Auth Developer Status v1 跨服务契约

#### 目的与所有权

Auth Center 是 Developer 状态的唯一权威。提供方行为由
[UC-AUTH-002](../../auth-center/use-cases/UC-AUTH-002-batch-get-developer-statuses.md)
及其 `BR-DEV-*` 拥有；本文件只定义跨服务线格式和错误边界。

#### gRPC 方法

```text
/auth_center.v1.developer_status.DeveloperStatusDirectory/BatchGetDeveloperStatuses
```

```proto
service DeveloperStatusDirectory {
  rpc BatchGetDeveloperStatuses(BatchGetDeveloperStatusesRequest)
      returns (BatchGetDeveloperStatusesResponse);
}

message BatchGetDeveloperStatusesRequest {
  repeated string auth_ids = 1;
}

message BatchGetDeveloperStatusesResponse {
  repeated DeveloperStatusEntry entries = 1;
}

message DeveloperStatusEntry {
  string auth_id = 1;
  DeveloperStatus developer_status = 2;
  AccountStatus account_status = 3;
}

enum DeveloperStatus {
  DEVELOPER_STATUS_UNSPECIFIED = 0;
  DEVELOPER_STATUS_PENDING = 1;
  DEVELOPER_STATUS_APPROVED = 2;
  DEVELOPER_STATUS_REJECTED = 3;
  DEVELOPER_STATUS_SUSPENDED = 4;
  DEVELOPER_STATUS_WITHDRAWN = 5;
}
```

AccountStatus 固定 0=UNSPECIFIED（成功非法）,1=ACTIVE,2=DISABLED,3=CLOSED。CLOSED 是合法 USER 墓碑，仅此状态下 developer_status 必须 UNSPECIFIED；ACTIVE/DISABLED 仍要求明确 Developer 枚举，普通 null Developer 保持 NOT_FOUND。

该方法没有 `google.api.http` annotation，不经 Gateway 暴露，也不提供 gRPC-Web。

#### 完整批量语义

- 请求包含 `1..100` 个唯一 Auth ID。
- 成功响应 entries 数量与请求相同，顺序一致，auth_id 逐项相等。
- `DEVELOPER_STATUS_UNSPECIFIED` 仅在 account_status=CLOSED 的合法终止墓碑响应中允许。
- 任一主体未知或状态无法读取时整个 RPC 失败，不返回部分 entries。
- 请求和响应只包含 opaque authId、账号状态与 Developer 状态，不投影用户资料。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证
内部服务身份。Auth Center 在验签后按固定 full method → `auth.developer-status.read`
映射检查 caller 注册表；测试 server 不能被当作生产无认证入口。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_DEVELOPER_STATUS_READ_FORBIDDEN` |
| 批量输入非法 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_DEVELOPER_STATUS_QUERY` |
| 任一主体未知或不适用 | `NOT_FOUND` | `ERROR_REASON_DEVELOPER_STATUS_NOT_FOUND` |
| 权威状态暂不可读取或记录损坏 | `UNAVAILABLE` | `ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含 MongoDB 查询、用户资料、服务凭证或堆栈。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. package/service/rpc 的 full method 精确一致。
2. request 只有 `auth_ids = 1`，没有用户或服务身份字段。
3. response 和 enum 字段号保持稳定。
4. entries 与请求一一对应并保持顺序。
5. ACTIVE/DISABLED 的 UNSPECIFIED、未知 account_status、缺项、额外项、重复项或错序均拒绝；CLOSED+UNSPECIFIED 为合法终止结果。
6. INVALID_ARGUMENT、NOT_FOUND、UNAVAILABLE 和稳定 reason 映射一致。
7. App Center 测试 Auth Server 实现同一生成接口，不维护手写 wire model。

#### 兼容性

- v1 可以追加 optional 字段或错误 reason，但不得改变现有字段号、类型、枚举值或 full method。
- 删除字段或枚举时必须 reserve 原 name 与 number。
- 改变完整批量和 fail-closed 语义需要新的平台契约评审。

2026-10-05：治理工作包共同接受 CLOSED 终止投影与 WITHDRAWN 枚举扩展，保持完整批量和失败关闭规则；未上线系统的测试 fixture 同步升级，不接受缺 account_status 的旧响应。

### `platform/contracts/trusted-service-identity-v1.md`：内部服务身份 JWS v1 契约（trusted-service-identity-v1）

#### 目的与范围

本契约定义服务到服务调用的认证与授权边界。它与面向用户请求的 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 是两个独立凭证：前者的主体是调用服务，后者的主体是用户或平台人员，二者不能互换或互相派生权限。

#### 传输与 JOSE

- gRPC metadata：`authorization: Bearer <compact-JWS>`；必须恰好一个值。
- JOSE header 必须包含 `alg=RS256`、`typ=JWT` 与非空 `kid`。
- 禁止接受或解析 token 自带的 `jwk`、`x5c`、`x5u` 等密钥来源。
- RSA key 至少 2048 bit。

#### Claims

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `iss` | string | 预登记 `serviceId` |
| `sub` | string | 必须与 `iss` 完全相同 |
| `aud` | string 或 string[] | 必须包含提供方 audience；Auth Center 为 `iwut-auth-center`，App Center 为 `iwut-app-center` |
| `iat` / `nbf` / `exp` | Unix 秒 | 必填；`exp > iat`、`exp > nbf`、TTL 不超过提供方上限 |
| `jti` | string | 每次签发的非空唯一值 |

token 不携带 permission。提供方先用未验签的 `iss + kid` 只做本地 key lookup，完成签名和全部 claims 校验后，才取得该 `serviceId` 注册记录中的权限。

#### Auth Center 固定授权映射

| gRPC 方法 | 必需 permission |
| --- | --- |
| `ScopeCatalog/GetScopeCatalogSnapshot` | `auth.scope-catalog.read` |
| `DeveloperStatusDirectory/BatchGetDeveloperStatuses` | `auth.developer-status.read` |
| `SystemPrincipalDirectory/ResolveSystemPrincipal` | `auth.system-principal.resolve` |
| `UserIdentityService/IssueUserIdentityFromSession` | `auth.identity.issue` |
| `ApplicationClosureService/ApplyApplicationClosure` | `auth.application-closure.apply` |
| `ApplicationClosureService/GetApplicationClosureStatus` | `auth.application-closure.read` |

签发方法的完整名称、caller `identityAudiences` 扩展与用户 Session 双重认证见 [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)；只有方法 permission 不足以请求任意 audience。

未知 RPC 默认拒绝。System principal 查询还必须检查 caller 注册记录中的 purpose allowlist；拥有 resolve permission 不代表可以解析任意 SYSTEM principal。

#### App Center 固定授权映射

App Center 通过原生 gRPC 开放 OAuth provider 和账号归属退出 provider，不生成 HTTP annotation。完整方法与本地 caller registry permission 固定为：

| gRPC 方法 | 必需 permission |
| --- | --- |
| `OAuthClientProviderService/GetClientConfiguration` | `app.oauth.client.read` |
| `OAuthClientProviderService/VerifyClientSecret` | `app.oauth.client.verify` |
| `OAuthClientProviderService/ResolveClientRuntimeConfiguration` | `app.oauth.runtime.resolve` |
| `OAuthClientProviderService/ResolveAuthorizationContext` | `app.oauth.context.resolve` |
| `OAuthClientProviderService/GetApplicationPublishedRedirects` | `app.oauth.redirects.read` |

未知方法默认拒绝。普通 USER/SYSTEM trusted identity、第三方 access token、client secret 和网络位置都不能替代 Auth service identity。

#### ENV 配置

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_IDENTITY_ID` | `serviceId` |
| `APP_CENTER_SERVICE_IDENTITY_KID` | 当前签名 key ID |
| `APP_CENTER_SERVICE_IDENTITY_AUDIENCE` | 默认 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_PRIVATE_KEY_PEM_B64` | PKCS#1 或 PKCS#8 RSA private-key PEM 的 strict standard Base64 |
| `APP_CENTER_SERVICE_IDENTITY_TTL` | 正 Go duration；默认 `1m` |

Auth Center 必须提供 `AUTH_CENTER_SERVICE_CALLERS_B64`：以下 JSON UTF-8 bytes 的 strict standard Base64。

```json
{
  "iwut-app-center": {
    "status": "ACTIVE",
    "keys": {
      "app-center-2026-01": {
        "publicKeyPemB64": "<RSA public-key PEM 的 strict standard Base64>"
      }
    },
    "permissions": [
      "auth.scope-catalog.read",
      "auth.developer-status.read",
      "auth.system-principal.resolve",
      "auth.application-closure.apply",
      "auth.application-closure.read"
    ],
    "systemPrincipalPurposes": [
      "app-center.review-auto-rejection"
    ]
  }
}
```

外层 Base64 只解决环境变量传输与转义，不提供保密性。部署必须用 secret 管理 App 私钥；不得把值提交到仓库、镜像、日志或诊断输出。Auth 公钥注册表不含私钥，可以由 config 或 secret 注入。缺失、未知字段、重复权限、非法 key、未知 permission/purpose 或空注册表必须阻止启动。

App Center 必须提供：

| 环境变量 | 内容 |
| --- | --- |
| `APP_CENTER_SERVICE_CALLERS_B64` | 与 Auth caller registry 相同的 strict Base64 JSON schema；首版登记 `iwut-auth-center` |
| `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` | 接受的最大 token TTL，默认 `1m` |
| `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW` | claims 时钟偏差，默认 `30s` |

App Center registry 中 `iwut-auth-center` 允许上述五个 `app.oauth.*` permission，以及 account-owner-exit-v1 固定的三个 app.account-owner-exit.* 精确权限，不允许 Auth provider permission、system principal purpose 或 identity audience 扩展。App provider audience 固定为 `iwut-app-center`，不能用环境变量改成 Auth audience。registry 在启动时严格解析并预加载公钥；每次 RPC 本地验签和授权，不回调 Auth。

#### 错误与轮换

- 缺失凭证：`UNAUTHENTICATED / ERROR_REASON_SERVICE_IDENTITY_REQUIRED`。
- 无效凭证：`UNAUTHENTICATED / ERROR_REASON_INVALID_SERVICE_IDENTITY`。
- 身份有效但 RPC/purpose 未授权：`PERMISSION_DENIED`，使用目标契约的稳定 forbidden reason。
- 错误不得泄漏 token、PEM、service registry 或底层 crypto 信息。
- 轮换时先把新 `kid` 公钥加入 Auth 注册表，再切换 App signer；旧 key 保留至少最大 token TTL 后移除。紧急撤销把 caller 状态设为 `DISABLED` 或移除对应 kid。

#### 契约测试要求

至少验证合法调用、缺失/错误签名、未知 serviceId、未知 kid、错误 audience、过长 TTL、disabled caller、缺少 RPC permission 和未允许 purpose。生产等价 E2E 必须由真实 App signer 调用真实 Auth interceptor，不能只验证同接口 fake server。

#### 账号归属退出方法

精确 full method、调用方向及权限以 [account-owner-exit-v1](../../platform/contracts/account-owner-exit-v1.md#固定线格式与方法授权) 为准。Auth 接受 App 的 auth.account-owner-exit.read；App 接受 Auth 的 prepare/finish/read。它们不授予其他服务权限、不开放 HTTP 或通用 wildcard。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、Schema 与索引、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/trusted-service-identity-v1.md`（docs 根级共享文档）：Application 关闭方法

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-025-coordinate-account-owner-exit.md` | 65 | `730a0ecc6a28` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/account-owner-exit-v1.md` | 70 | `70d736bfa904` |
| `platform/contracts/auth-developer-status-v1.md` | 97 | `65d986d93af1` |
| `platform/contracts/trusted-service-identity-v1.md` | 124 | `4a64372bc9c0` |
