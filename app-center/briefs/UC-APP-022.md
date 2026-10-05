<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-022 --spec tools/brief-specs/UC-APP-022.json -->
# Brief — UC-APP-022：管理 Application Filter

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-022` 管理 Application Filter |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-FLT-001`–`BR-FLT-010`（10 条） |
| 外部引用 BR | — |
| ADR | `ADR-003`、`ADR-004`、`ADR-005`、`ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/application-filter-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

> developerStatus 为 `APPROVED` 的 Application 当前管理员，为 Application 设置或清空一份立即生效、无需审核的客户端展示 Filter；每次真实变化形成不可变 Revision，Catalog 后续把当前规则随 Grey/Stable 候选发送给官方客户端。

本用例负责：

- 建立 Application 级 `ApplicationFilter` 协调对象。
- 设置类型化 `profile-filter-v1` 规则树；每次真实变化创建并立即发布一个不可变 `ApplicationFilterRevision`。
- 使用 ApplicationFilter revision 执行乐观并发控制。
- 清空规则并形成一条显式 `ALLOW_ALL` Revision。
- 定义跨客户端一致的规则结构、求值和缺失字段语义。
- 提供管理员 Get、Set、Clear 的 HTTP/gRPC API。

本用例不负责：

- 在 App Center 读取或保存任何用户资料值，或在服务端执行 Filter。
- 改变 Test/Grey/Stable 发布槽位、Publication revision、Version、Profile、OAuth 或用户授权。
- 让 Filter 成为安全、授权、Tester 或 Grey cohort 边界。
- 实现普通用户 Catalog、统一启动目标解析或客户端 UI。
- 在线查询 Auth ProfileFieldDefinition；首版只复用其稳定 key 语法和值类型。
- 审核、草稿、回滚到历史 Revision、定时生效或按渠道/rpcApiMajor 配置不同规则。

Filter 作用于公开目录中的 Grey 与 Stable 候选。Test 通过独立的“我参与的测试”入口展示，不执行 Filter。

### 已确认的设计选择

1. Filter 按 Application 管理，不依附 ApplicationVersion、ApplicationPublication、channel 或 rpcApiMajor。
2. Filter 不需要审核。每个真实 Set/Clear 都原子创建一条不可变 Revision，并立即成为当前发布 Revision。
3. ApplicationFilter 不存在等价于 `ALLOW_ALL`、revision 0。第一次真实设置或清空要求 expected revision 0，提交后 revision 为 1。
4. Clear 不是删除聚合或历史，而是发布一条 `ALLOW_ALL` Revision；因此清空行为可审计，后续 Set 继续递增 sequence 和 revision。
5. 规则只使用 `STRING`、`INTEGER`、`BOOLEAN`、`DATE` 四种类型，字段 key 复用 Auth ProfileFieldDefinition 的稳定语法；App Center 不在线查询 Auth，也不判断 key 当前是否已进入生产字段目录。
6. App Center 只验证规则结构和类型并保存。客户端从本地资料读取字段并求值，原始用户信息不上传，命中结果不回传或持久化。
7. Filter 不是安全边界。绕过或无法执行 Filter 不授予 Test、Grey、OAuth、scope 或运行权限。

### 输入与身份

路径参数：

```text
applicationId: ApplicationId
```

读取：

```text
GetApplicationFilterQuery {}
```

设置：

```text
SetApplicationFilterCommand {
  expectedRevision: int64  // >= 0
  rule: FilterRule
}
```

清空：

```text
ClearApplicationFilterCommand {
  expectedRevision: int64  // >= 0
}
```

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

请求不能指定 filterRevisionId、sequence、schemaVersion、publishedBy、publishedAt 或提交后的 revision。

### 规则结构

`profile-filter-v1` 是一棵有界类型化树：

```text
FilterRule = FilterGroup | FilterPredicate

FilterGroup {
  operator: ALL | ANY | NOT
  children: FilterRule[]
}

FilterPredicate {
  fieldKey: string
  operator: EQ | NE | LT | LTE | GT | GTE | EXISTS | NOT_EXISTS
  value?: ProfileScalar
}

ProfileScalar = StringValue | IntegerValue | BooleanValue | DateValue
```

结构约束：

- 整棵树最多 128 个节点，根计一个节点；最大深度为 8，根深度为 1。
- `ALL`、`ANY` 必须有 1–32 个 children；`NOT` 必须恰有一个 child。
- `fieldKey` 为 1–128 ASCII bytes，符合 `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$`。
- `EQ`、`NE` 对四种标量均可用；`LT`、`LTE`、`GT`、`GTE` 只接受 INTEGER 或 DATE；`EXISTS`、`NOT_EXISTS` 不得携带 value。
- STRING 必须是有效 UTF-8，最多 4096 Unicode code points；INTEGER 为 int32；BOOLEAN 为 bool；DATE 是 `0001-01-01` 至 `9999-12-31` 的严格真实公历日期，格式 `YYYY-MM-DD`。
- 不接受 null、float、数组、对象、脚本、正则表达式、字段间比较或字符串隐式转数字。
- Proto/JSON 的 oneof 必须精确选择 group 或 predicate；未知 enum、未设置 oneof 或多余结构均无效。

这些限制同时控制持久化大小、客户端递归成本和跨语言实现差异，不由部署配置或单个客户端改变。

### 客户端求值契约

客户端对一个 Application 的当前完整规则执行纯函数：

```text
evaluate(rule, localProfileFields) -> bool
```

- `ALL` 对 children 做短路与；`ANY` 做短路或；`NOT` 对唯一 child 取反。
- `EQ`、`NE` 要求本地值与规则值类型一致；STRING 按原始 Unicode scalar sequence 精确比较，不 trim、不归一化、不折叠大小写；INTEGER/BOOLEAN 按值比较；DATE 按已校验公历值比较。
- 顺序比较只用于 INTEGER/DATE，端点分别按操作符包含或排除。
- 字段缺失或本地类型与规则值不一致时，普通比较叶节点返回 false；`EXISTS` 仅在字段存在且属于四种支持类型时为 true，`NOT_EXISTS` 为其反值。
- `NOT` 可以反转任何 child 的结果，包括由缺失字段产生的 false；需要直接表达缺失时应使用 `NOT_EXISTS`。
- 没有 ApplicationFilter 或当前 Revision 为 `ALLOW_ALL` 时返回 true。
- 客户端不认识 schemaVersion、节点或操作符时必须 fail closed：该 Application 不进入最终展示列表；不能把未知规则当作允许。

规则只决定展示。客户端即使显示、隐藏错误或被修改，也不能改变服务端解析和授权结果。

### 设置主流程

1. 从可信身份取得 authId/developerStatus，校验 developerStatus=`APPROVED`、applicationId 和 expected revision。
2. 完整验证并规范化规则；保留 children 输入顺序，标量值不做隐式转换或文本规范化。
3. 加载 Application，确认调用者是当前 admin；加载 ApplicationFilter。不存在时当前逻辑状态为 `ALLOW_ALL`、revision 0、nextSequence 1。
4. expected revision 必须与当前逻辑 revision 精确匹配。
5. 若当前已发布 `RULE` 与规范化规则结构和值完全相等，返回 `changed=false`；不读取 Clock 或 IDGenerator，不创建 Revision。
6. 生成 UUIDv7 filterRevisionId 和 publishedAt。
7. 在同一事务中取得 Application 写栅栏并复查管理员和 expected revision，然后：
   - 创建不可变 `RULE` ApplicationFilterRevision，sequence 使用 nextSequence。
   - 建立或更新 ApplicationFilter 的 currentFilterRevisionId、revision、nextSequence、updatedBy/updatedAt。
8. 返回 `changed=true`、当前 ApplicationFilter 和新 Revision。

App Center 不在本流程调用 Auth、Publication、Profile、Scope、URL 或 OAuth 服务。

### 清空主流程

1. 校验身份、applicationId 和 expected revision，并确认当前 admin。
2. 加载当前逻辑 Filter 并精确匹配 revision。
3. 当前逻辑状态已经是 `ALLOW_ALL` 时返回 `changed=false`，不读取 Clock 或 IDGenerator。ApplicationFilter 不存在且 expected revision 为 0 也属于该 no-op。
4. 生成 UUIDv7 filterRevisionId 和 publishedAt。
5. 在同一事务取得 Application 写栅栏并复查管理员和 expected revision，创建不可变 `ALLOW_ALL` Revision，推进 current pointer、revision 和 nextSequence。
6. 返回 `changed=true`。任何发布槽位、Profile、Version、OAuth 与其他 Application 均不改变。

### 读取主流程

管理员 Get 读取当前 Application 和 ApplicationFilter：

- 仅 developerStatus=`APPROVED` 的当前 admin 可读管理视图。
- 聚合不存在时返回合成的 `ALLOW_ALL`、revision 0，不创建记录。
- 已存在时返回当前 Revision；current pointer 丢失、跨 Application、sequence/revision 不一致或规则损坏均为内部不变量异常。
- 历史 Revision 列表不在首版 API；Mongo 中的不可变 Revision 为以后审计查询保留事实。

### 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 APPROVED：`DeveloperApprovalRequired`。
- applicationId、expectedRevision 或规则非法：稳定 INVALID_ARGUMENT reason；规则错误不回显任意嵌套正文。
- Application 不存在：NotFound；调用者不是当前管理员：`ApplicationAdminRequired`。
- expected revision 不匹配：`ApplicationFilterRevisionConflict`，HTTP 409 / gRPC ABORTED。
- 当前指针、Revision、sequence、schemaVersion 或规则持久化状态损坏：`ApplicationFilterStateInconsistent`，HTTP 500 / gRPC INTERNAL。
- ID、Clock、存储、revision/sequence 溢出或事务失败：内部失败，不留下孤立 Revision、错误 pointer 或部分 revision。

### 最小领域模型变化

```text
ApplicationFilter {
  applicationId
  currentFilterRevisionId
  revision
  nextSequence
  updatedBy
  updatedAt
}

ApplicationFilterRevision {
  filterRevisionId
  applicationId
  sequence
  schemaVersion: "profile-filter-v1"
  mode: RULE | ALLOW_ALL
  rule?
  publishedBy
  publishedAt
}
```

ApplicationFilter 是 OCC 与当前 pointer 的协调聚合；ApplicationFilterRevision 是不可变发布事实。二者可以物理拆 collection，但真实变化必须同事务提交。

### API 草图

```text
GET    /v1/applications/{applicationId}/filter
PUT    /v1/applications/{applicationId}/filter
DELETE /v1/applications/{applicationId}/filter?expected_revision={revision}
```

独立 API package 为 `app_center.v1.application_filter`，service 为 `ApplicationFilterService`：

```text
GetApplicationFilter
SetApplicationFilter
ClearApplicationFilter
```

响应资源包含 ApplicationFilter revision、当前 Revision 的 mode/schemaVersion/rule/sequence/publishedBy/publishedAt；不存在聚合时返回合成 `ALLOW_ALL` revision 0，current revision 为空。Rule 使用 oneof group/predicate，ProfileScalar 使用 oneof 四种值。

新增稳定 error reason：

```text
ERROR_REASON_INVALID_APPLICATION_FILTER = 26
ERROR_REASON_APPLICATION_FILTER_REVISION_CONFLICT = 27
ERROR_REASON_APPLICATION_FILTER_STATE_INCONSISTENT = 28
```

Mongo migration 预留为 `0018_application_filter`，创建 `application_filters` 与 `application_filter_revisions` 的严格 validator/index；验证 fresh、0017→0018、重复执行和非法树/指针文档。规则树的完整语义由 Domain 解码保护，Mongo validator 保护身份、模式、元数据和有界 BSON 形状，不在 `$jsonSchema` 中实现递归求值器。

### 验收场景

- 不存在 Filter 时 Get 返回 revision 0、ALLOW_ALL 且不写数据库。
- 首次 Set 使用 expected revision 0，创建 sequence/revision 1 并立即可读。
- Set 支持四种标量、全部操作符和嵌套 group；拒绝未知 enum、非法日期、类型错配、空 group、非一元 NOT、超过 8 层/128 节点/32 children。
- 相同规则 Set 是无 ID/Clock/数据库写入的 no-op；children 顺序属于结构等价的一部分。
- Clear 创建不可变 ALLOW_ALL Revision；重复 Clear 是 no-op；Clear 后再次 Set 使用后续 sequence。
- 并发相同 expected revision 的 Set/Clear 最多一个提交；管理员转让竞争不会由旧管理员越权成功。
- 持久化 pointer、Revision 或规则损坏返回 INTERNAL，不静默降级为 ALLOW_ALL。
- Filter 修改不改变任何 Publication revision、槽位、Profile、Version、OAuth 或 Tester 数据。
- App Center 不调用 Auth profile、Scope、URL 或 OAuth 依赖，不记录规则正文或用户字段。
- 客户端共享测试向量覆盖缺失字段、类型不匹配、NOT、DATE/INTEGER 边界和未知 schema fail-closed。
- API、Mongo integration、HTTP/gRPC E2E 与 race 验证通过；0018 migration fresh/sequential/idempotent 一致。

### 依赖与实现边界

- 依赖 UC-APP-001 的 Application、管理员关系和 Application 写栅栏；不依赖任何 Publication 已存在。
- 复用 Auth ProfileFieldDefinition 的 key 语法和值类型定义，但没有 Auth 运行时调用或服务身份依赖。
- 需要独立 API Proto、Filter Domain/UseCase/Repository、0018 migration、HTTP/gRPC/Wire 和真实 MongoDB 验证。
- Catalog 后续只读取 current Revision 并原样分发；客户端求值器与共享向量属于独立客户端交付。
- 统一启动解析、Catalog、test clear、Application disable、Filter UI 和 Auth 用户资料生产字段清单不属于本工作包。
- 实现必须使用生成 brief，API 输入/生成物先提交，再由服务提交 gitlink；所有提交保持本地。

## 业务规则（UC-APP-022 权威正文）

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-001 -->
### BR-FLT-001：Application 级公开展示策略

Filter 属于 Application，当前规则同时作用于公开 Catalog 的 Grey 与 Stable 候选，不按 Version、channel 或 rpcApiMajor 分叉。Test 入口不执行 Filter。修改 Filter 不改变 Publication、Profile、Version、OAuth 或服务端运行解析。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-002 -->
### BR-FLT-002：无需审核的不可变 Revision

每次真实 Set/Clear 创建一个不可变 ApplicationFilterRevision 并立即发布。不存在草稿、提交、审核或人工发布步骤；当前 pointer 是读取权威，历史 Revision 不得覆盖修改或物理复用。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-003 -->
### BR-FLT-003：默认允许与显式 Clear

ApplicationFilter 不存在表示 revision 0、`ALLOW_ALL`。Clear 发布一条新的 `ALLOW_ALL` Revision而不是删除聚合或历史。当前已经允许全部时 Clear 是 no-op。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-004 -->
### BR-FLT-004：类型化有界规则

`profile-filter-v1` 只接受本用例定义的 group、predicate、ProfileScalar、操作符、字段 key、节点数与深度。服务端拒绝未知、歧义、超限或类型不匹配的树，不执行脚本或隐式转换。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-005 -->
### BR-FLT-005：字段目录解耦

字段 key 和标量类型复用 Auth ProfileFieldDefinition 的稳定语法和四种类型，但 App Center 首版不在线查询 Auth 目录。有效但客户端未知/未提供的字段按缺失处理；未来新增字段不要求迁移 App Center Filter 存储格式。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-006 -->
### BR-FLT-006：客户端确定性求值

官方客户端必须实现本用例的相同布尔、类型、比较和缺失字段语义。未知 schemaVersion 或节点 fail closed。App Center 不接收原始用户字段，不执行或保存用户级求值结果。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-007 -->
### BR-FLT-007：Filter 不是安全边界

Filter 结果只影响最终展示列表。服务端 Tester、Grey cohort、OAuth、scope 和运行资格始终独立验证，不能信任客户端的 Filter 命中声明。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-008 -->
### BR-FLT-008：OCC、no-op 与序号

ApplicationFilter revision 从首次真实变化的 1 开始，每次真实 Set/Clear 精确增加 1；nextSequence 同步推进。命令必须携带当前 expected revision。相同 RULE Set 或当前 ALLOW_ALL Clear 是 no-op，不生成 ID/时间/Revision。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-009 -->
### BR-FLT-009：管理员与原子写栅栏

只有 developerStatus=`APPROVED` 的当前 Application admin 可以读取管理视图或修改 Filter。真实变化在一个事务中取得 Application 写栅栏、复查管理员/OCC、插入 Revision 并更新当前 pointer；与管理员转让并发时结果等价于明确先后顺序。

<!-- 权威位置: use-cases/UC-APP-022-manage-application-filter.md#br-flt-010 -->
### BR-FLT-010：最小披露与不可变历史

管理 API 返回当前规则和当前 Revision 元数据，不返回历史列表或任何用户资料。日志、错误和普通追踪不得记录完整规则正文。已保存 Revision 只读，Clear 和后续 Set 不删除历史。

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

### `platform/contracts/application-filter-v1.md`：Application Filter v1

#### 目的与边界

本契约固定 App Center 与官方客户端之间的 `profile-filter-v1` 规则线格式和求值语义。权威业务规则位于 [UC-APP-022](../use-cases/UC-APP-022-manage-application-filter.md)。

App Center 保存并分发规则，不读取用户资料或执行规则。客户端只使用本地资料求值。Filter 只影响 Grey/Stable 候选的展示，不授予任何服务端权限；Test 入口不执行 Filter。

#### 规则线格式

规则是 oneof group/predicate 的树：

```text
Rule {
  oneof node {
    Group group
    Predicate predicate
  }
}

Group {
  GroupOperator operator // ALL, ANY, NOT
  Rule[] children
}

Predicate {
  string fieldKey
  PredicateOperator operator
  optional ProfileScalar value
}

ProfileScalar {
  oneof value {
    string stringValue
    int32 integerValue
    bool booleanValue
    string dateValue
  }
}
```

字段 key 语法和值类型与 Auth ProfileFieldDefinition 对齐，但客户端不得把规则中的 key 当作用户已提供该字段、已授予第三方读取权限或字段当前存在的证明。

#### 结构限制

- schemaVersion 固定 `profile-filter-v1`。
- 最大 128 节点、深度 8；ALL/ANY 为 1–32 children，NOT 恰为 1。
- EQ/NE 支持四种标量；LT/LTE/GT/GTE 只支持 INTEGER/DATE；EXISTS/NOT_EXISTS 不携带值。
- STRING 最大 4096 Unicode code points；DATE 是严格 `YYYY-MM-DD` 公历日期。
- 未知 enum、未设置 oneof、类型错配或超限均为无效规则。

#### 求值

普通比较遇到缺失字段或本地类型不匹配时为 false。EXISTS 只在存在支持类型的字段时为 true，NOT_EXISTS 为其反值。NOT 正常反转 child 的结果。字符串精确比较，不 trim、归一化或折叠大小写；INTEGER、BOOLEAN、DATE 按类型值比较。

没有 Filter 或 mode=`ALLOW_ALL` 时允许展示。客户端遇到未知 schemaVersion、节点或操作符时 fail closed，不展示该候选。客户端不向 App Center 返回原始字段、求值轨迹或命中结果。

#### 版本与缓存

Catalog 返回 applicationId、ApplicationFilter revision、当前 filterRevisionId、schemaVersion、mode 和 rule。客户端可按 `(applicationId, filterRevisionId)` 缓存已解析规则；新的 Revision 使旧缓存失效。Revision 不与 Publication revision、Version 或 Profile revision 合并。

#### 共享验收向量

服务端 Domain 与各官方客户端应共享覆盖以下行为的固定向量：ALL/ANY 短路、NOT、四种标量、日期和整数端点、缺失字段、类型不匹配、EXISTS/NOT_EXISTS、ALLOW_ALL，以及未知 schemaVersion fail closed。向量不包含真实用户资料或生产字段名。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
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

- `UC-APP-022`（use-cases/UC-APP-022-manage-application-filter.md）：后续设计顺序、变更记录
- `ADR-003`（adr/ADR-003-go-package-and-dependency-boundaries.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-004`（adr/ADR-004-mongodb-transactions-and-schema-management.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-005`（adr/ADR-005-domain-errors-and-transport-mapping.md）：背景、考虑过的替代方案、结果、关联文档
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：JOSE Header、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-022-manage-application-filter.md` | 314 | `385fb67364de` |
| `adr/ADR-003-go-package-and-dependency-boundaries.md` | 116 | `f1ac7dfa45a0` |
| `adr/ADR-004-mongodb-transactions-and-schema-management.md` | 85 | `c2915d5ec05e` |
| `adr/ADR-005-domain-errors-and-transport-mapping.md` | 86 | `50247ceb0782` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/application-filter-v1.md` | 66 | `58edc31edebd` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
