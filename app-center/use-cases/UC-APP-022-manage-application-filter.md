# UC-APP-022：管理 Application Filter

状态：`ACCEPTED`

## 目标与范围

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

## 已确认的设计选择

1. Filter 按 Application 管理，不依附 ApplicationVersion、ApplicationPublication、channel 或 rpcApiMajor。
2. Filter 不需要审核。每个真实 Set/Clear 都原子创建一条不可变 Revision，并立即成为当前发布 Revision。
3. ApplicationFilter 不存在等价于 `ALLOW_ALL`、revision 0。第一次真实设置或清空要求 expected revision 0，提交后 revision 为 1。
4. Clear 不是删除聚合或历史，而是发布一条 `ALLOW_ALL` Revision；因此清空行为可审计，后续 Set 继续递增 sequence 和 revision。
5. 规则只使用 `STRING`、`INTEGER`、`BOOLEAN`、`DATE` 四种类型，字段 key 复用 Auth ProfileFieldDefinition 的稳定语法；App Center 不在线查询 Auth，也不判断 key 当前是否已进入生产字段目录。
6. App Center 只验证规则结构和类型并保存。客户端从本地资料读取字段并求值，原始用户信息不上传，命中结果不回传或持久化。
7. Filter 不是安全边界。绕过或无法执行 Filter 不授予 Test、Grey、OAuth、scope 或运行权限。

## 输入与身份

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

## 规则结构

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

## 客户端求值契约

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

## 设置主流程

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

## 清空主流程

1. 校验身份、applicationId 和 expected revision，并确认当前 admin。
2. 加载当前逻辑 Filter 并精确匹配 revision。
3. 当前逻辑状态已经是 `ALLOW_ALL` 时返回 `changed=false`，不读取 Clock 或 IDGenerator。ApplicationFilter 不存在且 expected revision 为 0 也属于该 no-op。
4. 生成 UUIDv7 filterRevisionId 和 publishedAt。
5. 在同一事务取得 Application 写栅栏并复查管理员和 expected revision，创建不可变 `ALLOW_ALL` Revision，推进 current pointer、revision 和 nextSequence。
6. 返回 `changed=true`。任何发布槽位、Profile、Version、OAuth 与其他 Application 均不改变。

## 读取主流程

管理员 Get 读取当前 Application 和 ApplicationFilter：

- 仅 developerStatus=`APPROVED` 的当前 admin 可读管理视图。
- 聚合不存在时返回合成的 `ALLOW_ALL`、revision 0，不创建记录。
- 已存在时返回当前 Revision；current pointer 丢失、跨 Application、sequence/revision 不一致或规则损坏均为内部不变量异常。
- 历史 Revision 列表不在首版 API；Mongo 中的不可变 Revision 为以后审计查询保留事实。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 APPROVED：`DeveloperApprovalRequired`。
- applicationId、expectedRevision 或规则非法：稳定 INVALID_ARGUMENT reason；规则错误不回显任意嵌套正文。
- Application 不存在：NotFound；调用者不是当前管理员：`ApplicationAdminRequired`。
- expected revision 不匹配：`ApplicationFilterRevisionConflict`，HTTP 409 / gRPC ABORTED。
- 当前指针、Revision、sequence、schemaVersion 或规则持久化状态损坏：`ApplicationFilterStateInconsistent`，HTTP 500 / gRPC INTERNAL。
- ID、Clock、存储、revision/sequence 溢出或事务失败：内部失败，不留下孤立 Revision、错误 pointer 或部分 revision。

## 业务规则

<a id="br-flt-001"></a>
### BR-FLT-001：Application 级公开展示策略

Filter 属于 Application，当前规则同时作用于公开 Catalog 的 Grey 与 Stable 候选，不按 Version、channel 或 rpcApiMajor 分叉。Test 入口不执行 Filter。修改 Filter 不改变 Publication、Profile、Version、OAuth 或服务端运行解析。

<a id="br-flt-002"></a>
### BR-FLT-002：无需审核的不可变 Revision

每次真实 Set/Clear 创建一个不可变 ApplicationFilterRevision 并立即发布。不存在草稿、提交、审核或人工发布步骤；当前 pointer 是读取权威，历史 Revision 不得覆盖修改或物理复用。

<a id="br-flt-003"></a>
### BR-FLT-003：默认允许与显式 Clear

ApplicationFilter 不存在表示 revision 0、`ALLOW_ALL`。Clear 发布一条新的 `ALLOW_ALL` Revision而不是删除聚合或历史。当前已经允许全部时 Clear 是 no-op。

<a id="br-flt-004"></a>
### BR-FLT-004：类型化有界规则

`profile-filter-v1` 只接受本用例定义的 group、predicate、ProfileScalar、操作符、字段 key、节点数与深度。服务端拒绝未知、歧义、超限或类型不匹配的树，不执行脚本或隐式转换。

<a id="br-flt-005"></a>
### BR-FLT-005：字段目录解耦

字段 key 和标量类型复用 Auth ProfileFieldDefinition 的稳定语法和四种类型，但 App Center 首版不在线查询 Auth 目录。有效但客户端未知/未提供的字段按缺失处理；未来新增字段不要求迁移 App Center Filter 存储格式。

<a id="br-flt-006"></a>
### BR-FLT-006：客户端确定性求值

官方客户端必须实现本用例的相同布尔、类型、比较和缺失字段语义。未知 schemaVersion 或节点 fail closed。App Center 不接收原始用户字段，不执行或保存用户级求值结果。

<a id="br-flt-007"></a>
### BR-FLT-007：Filter 不是安全边界

Filter 结果只影响最终展示列表。服务端 Tester、Grey cohort、OAuth、scope 和运行资格始终独立验证，不能信任客户端的 Filter 命中声明。

<a id="br-flt-008"></a>
### BR-FLT-008：OCC、no-op 与序号

ApplicationFilter revision 从首次真实变化的 1 开始，每次真实 Set/Clear 精确增加 1；nextSequence 同步推进。命令必须携带当前 expected revision。相同 RULE Set 或当前 ALLOW_ALL Clear 是 no-op，不生成 ID/时间/Revision。

<a id="br-flt-009"></a>
### BR-FLT-009：管理员与原子写栅栏

只有 developerStatus=`APPROVED` 的当前 Application admin 可以读取管理视图或修改 Filter。真实变化在一个事务中取得 Application 写栅栏、复查管理员/OCC、插入 Revision 并更新当前 pointer；与管理员转让并发时结果等价于明确先后顺序。

<a id="br-flt-010"></a>
### BR-FLT-010：最小披露与不可变历史

管理 API 返回当前规则和当前 Revision 元数据，不返回历史列表或任何用户资料。日志、错误和普通追踪不得记录完整规则正文。已保存 Revision 只读，Clear 和后续 Set 不删除历史。

## 最小领域模型变化

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

## API 草图

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

## 验收场景

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

## 依赖与实现边界

- 依赖 UC-APP-001 的 Application、管理员关系和 Application 写栅栏；不依赖任何 Publication 已存在。
- 复用 Auth ProfileFieldDefinition 的 key 语法和值类型定义，但没有 Auth 运行时调用或服务身份依赖。
- 需要独立 API Proto、Filter Domain/UseCase/Repository、0018 migration、HTTP/gRPC/Wire 和真实 MongoDB 验证。
- Catalog 后续只读取 current Revision 并原样分发；客户端求值器与共享向量属于独立客户端交付。
- 统一启动解析、Catalog、test clear、Application disable、Filter UI 和 Auth 用户资料生产字段清单不属于本工作包。
- 实现必须使用生成 brief，API 输入/生成物先提交，再由服务提交 gitlink；所有提交保持本地。

## 后续设计顺序

1. 统一 `test > grey > stable` 服务端启动目标解析。
2. 普通 Catalog 列表/详情，把 Grey/Stable 候选与当前 Filter Revision 一起返回。
3. 官方客户端 `profile-filter-v1` 求值器和共享测试向量。
4. test clear、Application disable/suspension 与管理查询。

## 变更记录

- 2026-10-04：确认 Filter 为 Application 级、同时作用 Grey/Stable 的独立修订对象；Test 不受影响。
- 2026-10-04：确认 Filter 无需审核，每次真实修改立即发布不可变 Revision；接受类型化规则、Auth 同构字段 key/标量、缺失字段语义和客户端本地求值边界，设计进入 `ACCEPTED`。
