<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-052 --spec tools/brief-specs/UC-APP-052.json -->
# Brief — UC-APP-052：查询 Application 管理动态与历史记录

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-052` 查询 Application 管理动态与历史记录 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-067`–`BR-APP-071`（5 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |
| 配套查询 | `app-center/query-contracts/application-management-activity.md` |

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

当前 Application 管理员在 Console 的单应用上下文中，按时间查看 Version/Profile 的审核提交与结果，读取最小历史记录。管理动态是既有业务事实的只读投影，没有个人收件人、投递、已读/未读或新增业务写入。

本 UC 补齐 [UC034](../use-cases/UC-APP-034-query-owned-application-versions.md) 只有 latestReview、不能遍历 Version 全部 attempts 的缺口，并合并 [UC039](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md) 的 Profile 历史；不改变两者当前资源查询，不向 owner 开放 UC030/031 的 Reviewer 正文。投影及消费见[管理动态读契约](../query-contracts/application-management-activity.md)。

转让继续使用 [UC050](../use-cases/UC-APP-050-query-incoming-application-admin-transfers.md) 待接收集合与 [UC026](../use-cases/UC-APP-026-transfer-application-administration.md) 参与者详情；平台脚本继续按 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md) 分角色读取历史；Reviewer 继续原队列。本期没有跨应用/全平台动态、编辑/发布事件、脚本聚合活动、通用通知、应用发送消息或用户客户端通知展示契约。

### 接口与输入

候选正式服务 `app_center.v1.application_management_activity.ApplicationManagementActivityService`，本 UC 不分配 Proto 字段编号：

| RPC | App HTTP |
| --- | --- |
| ListApplicationManagementActivity | POST `/v1/applications/{application_id}/management-activity:search`，body=query |
| GetApplicationManagementActivity | GET `/v1/applications/{application_id}/management-activity/{activity_id}` |

外部增加 `/app-center`。沿现行 Session→App audience USER 管理接入，Gateway 的 Developer Console surface 由其 owner 接入；Admin 域名不赋予 owner 读取资格。“Console 消费”是产品范围，后端仍按可信身份与资源资格授权，不信任客户端来源头，也不阻止有权主体通过正式管理 API 读取。

列表 query 仅含 kinds[]、pageSize、pageToken。kinds 省略/空表示全部六类，非空为所选类别并集，去重并按固定枚举顺序规范化；未知值拒绝。pageSize 省略/0 为20，合法范围1..100；pageToken 最多4096 UTF-8 bytes。无自由搜索、recipient、目标用户、offset、totalCount、自定义排序或读状态过滤。Application ID 沿既有管理查询格式；activityId 须为服务可解析的稳定不透明定位。

POST 仅接受单个 JSON 对象，正文最多16 KiB，无 query string；GET 无正文或 query string。HTTP/native 拒绝未知字段。先验证可信身份，再验证业务输入；合法输入下先确认当前 owner，后处理 token 或定位 activity，避免游标/记录探测泄漏。

### 主流程

1. 验证可信 ACTIVE USER，解析本次输入。
2. 在同一 majority 只读 snapshot 中读取 Application，确认当前 adminId 与 ownershipRevision。
3. 列表验证签名 token，按类别读取四个有界来源并合并；详情定位单一源 Review 和阶段。两者均校验必要来源及父子关系。
4. 依读契约返回最小投影和本次观察时间 asOf；所有成功、空结果和错误均 private,no-store。全程不修改业务事实。

### 错误与协议

| 情况 | 稳定 reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信 USER | USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY | 401 / UNAUTHENTICATED |
| 非法输入（含无法解析的 activityId） | INVALID_APPLICATION_MANAGEMENT_ACTIVITY_QUERY | 400 / INVALID_ARGUMENT |
| 当前 owner 的非法 token | INVALID_APPLICATION_MANAGEMENT_ACTIVITY_PAGE_TOKEN | 400 / INVALID_ARGUMENT |
| 目标隐藏/不存在 | APPLICATION_MANAGEMENT_ACTIVITY_NOT_FOUND | 404 / NOT_FOUND |
| 必要事实损坏 | APPLICATION_MANAGEMENT_ACTIVITY_STATE_INCONSISTENT | 500 / INTERNAL |
| 响应超预算 | APPLICATION_MANAGEMENT_ACTIVITY_RESPONSE_TOO_LARGE | 413 / RESOURCE_EXHAUSTED |
| 存储或 snapshot 不可用 | APPLICATION_MANAGEMENT_ACTIVITY_UNAVAILABLE | 503 / UNAVAILABLE |

合法但无历史返回200及空 items。HTTP、native gRPC、Gateway gRPC-Web 和生成客户端保持同一授权、字段与错误语义；body/token 超限属于请求无效，不能当作存储错误。App 稳定 reason 经现行 ErrorInfo/envelope 机制投影，不另建通知错误协议。

### 消费与写命令边界

Console 当前应用增加独立“管理动态”页，详情区分“查看记录”和“查看当前版本/资料”。历史记录不包含批准、拒绝、恢复、重提等动作；进入原正式详情后按原 UC 重读、确认、鉴权，不能把动态或 asOf 当作 OCC/命令基线。历史批准不冒充当前公开资料或发布状态。

仅显式加载、翻下一页和刷新；不后台扫描全部页/应用，不轮询、红点或未读数。无历史与读取失败分开呈现。Session、App、筛选或查询代际变化隔离旧分页链/详情/迟到响应，归属拒绝清除对应私有数据。具体页面 UC 由 Console owner 设计维护，不以本 UC 代替前端审核。

### 验收与串行依赖

1. 六类活动、同 Review 双阶段、多 attempt、原快照标签、原拒绝理由、人工/自动/级联拒绝、APPLICATION_CLOSED 无伪事件；恢复/编辑后的旧 Review 可读，Profile 新修订不覆盖旧记录。
2. owner 与无 owner 的平台管理员/Reviewer/Tester/仅 search 或运维权限；Developer 资格下降、应用关闭/暂停/归档；转让后新旧 owner 和重新取得管理权的旧 token。
3. 四来源同毫秒/同父多 attempt、单类/混合/全部 kinds、变 pageSize、未返回候选保留、空集合无 token、篡改/换人/换 App/换筛选；实际候选与父读取预算和命名索引验证。
4. 提交/决定/恢复/转让/关闭在受控事务前后竞争，只返回完整 snapshot；必要父源缺失、错误归属/绑定、非法 BSON/时间/状态、存储失败均按分类失败，无部分成功或写入。
5. 列表无理由、详情只含本次合法披露、无 Reviewer/策略/正文/凭据；输入/响应预算、private,no-store、三协议和 SDK、实际 Console Cookie/BFF 读取及迟到响应隔离。

正文接受后，串行完成 App 只读 UseCase/Port/Mongo 查询与显式索引、Proto/生成物和专项；按用户 API 对齐→Gateway owner 接入→固定本地三镜像联验→冻结完整 backend 门禁流程实施。Console 仅在其 UC 接受和后端契约就绪后实现。现有完成项不重标未完成；真实通知与正式新政策发布草案不是前置。本轮只实施 App Center；Auth、Gateway、Console 不在本轮实现范围，跨服务消费验收保留待接入状态，不 push 或部署。

## 业务规则（UC-APP-052 权威正文）

<!-- 权威位置: use-cases/UC-APP-052-query-application-management-activity.md#br-app-067 -->
### BR-APP-067：当前管理员的应用历史读取资格

两个方法仅接受可信 ACTIVE USER 且本次 Application.adminId 等于 caller AuthId；不要求 APPROVED Developer，不新增 Auth permission。平台管理员、Reviewer、Tester、SYSTEM、search/suspend/restore 均不隐式授权；同一人恰为 owner 时按 owner 读取。

Developer 资格下降，Application ACTIVE/CLOSING/CLOSED、AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED 均不额外取消当前 owner 的历史读权。转让后新 owner 可读既有历史，旧 owner 后续请求统一隐藏；重新取得管理权也不能使用旧 ownershipRevision token。已合法返回的旧响应不承诺远程撤回，消费端须隔离迟到响应。

App 不存在、非当前 owner、活动不存在或定位源不属于路径 App，统一 APPLICATION_MANAGEMENT_ACTIVITY_NOT_FOUND；不因调用者持有其他权限泄漏目标是否存在。对已经绑定本 App 的必要源发现悬空父资源或错误归属，则属于损坏而非可跳过的不存在。

<!-- 权威位置: use-cases/UC-APP-052-query-application-management-activity.md#br-app-068 -->
### BR-APP-068：六类审核事实与稳定历史定位

| kind | 来源时间 | 资源定位 |
| --- | --- | --- |
| VERSION_REVIEW_SUBMITTED | ApplicationReview.submittedAt | versionId、reviewId、attempt |
| VERSION_REVIEW_APPROVED | decision.decidedAt | 同上 |
| VERSION_REVIEW_REJECTED | decision.decidedAt | 同上 |
| PROFILE_REVIEW_SUBMITTED | ProfileReview.submittedAt | profileRevisionId、profileReviewId、attempt |
| PROFILE_REVIEW_APPROVED | decision.decidedAt | 同上 |
| PROFILE_REVIEW_REJECTED | decision.decidedAt | 同上 |

每个 Review 提供一项提交和至多一项决定。activityId 由源类型、源 Review ID、SUBMISSION/DECISION 阶段确定稳定不透明定位，不是授权或命令凭据；不因刷新生成 UUID，不单独存储活动。终态的提交项仍表达当时提交，不标为当前待审。

人工/自动拒绝及 UC049 的实际应用拒绝均映射同一拒绝项，不重复生成级联提醒；没有决定的 APPLICATION_CLOSED 豁免不合成拒绝。Version 拒绝恢复、重新编辑和新 attempt 不覆盖旧事实；Profile 拒绝终态及后来新修订各自独立。不使用 updatedAt 推算编辑史，不用当前最新 Review 替换被定位的历史记录。

<!-- 权威位置: use-cases/UC-APP-052-query-application-management-activity.md#br-app-069 -->
### BR-APP-069：历史记录的最小披露与原文保真

列表与详情投影只包含读契约定义的定位、类别、时间、attempt 及历史资源标签。Version 标签取该次 Review.snapshot.versionLabel，Profile 序号取所属修订的稳定 sequence；不用当前 Version label 改写过去。

列表不返回拒绝理由；详情仅 REJECTED 项返回该次 decision 的原非空 rejectionReason，SUBMITTED/APPROVED 项明确为 null。这是新增 owner 历史读取范围。历史文本按原事实保留并以纯文本展示，不 trim、裁剪、替换或按当前内容政策重新审核。

两者均不返回 submittedBy、decidedBy、Reviewer 身份、完整 snapshot、政策/检查定义、confirmedCheckIds、approvalValidation、脚本正文、OAuth 配置或凭据；不因动态展示扩展其他角色的资料读取资格。

<!-- 权威位置: use-cases/UC-APP-052-query-application-management-activity.md#br-app-070 -->
### BR-APP-070：管理动态的只读快照与失败关闭

每页/详情在一个 majority 只读 snapshot 内确认当前 Application 归属、ownershipRevision、必要源和父资源。校验源/父 ID 与所属 App、正 attempt/sourceRevision、时间及 BSON 类型、PENDING 无决定/终态唯一匹配决定、决定与绑定政策版本一致，以及本投影所需的历史标签/sequence；时间关系沿源 UC 的既有不变量。校验最终页和必要 lookahead，不为验证全库完整性扫描所有历史。

历史 Review 与当前 Version 最新状态、revision、内容不同可以合法存在，不能强套当前资源一致性；过去批准不是当前已发布或公开的证明。只读取本投影必需的字段，不查询完整政策定义，也不加载其正文作为 owner 输出。

必要事实缺失/损坏整页或详情500，存储/snapshot 不可用503；不漏项、隐藏损坏、返回部分成功或伪装为空。每协议编码响应最多512 KiB，超出明确413/RESOURCE_EXHAUSTED，不截断文本或改序。成功与错误 private,no-store，不回显输入、认证材料或底层原因。

不写 fence、revision、业务审计、访问/活动/已读事实，不调用 Auth、Scope、DNS 或外部网页，不用可能持久化过期状态的转让 Get 拼装结果。没有新增活动集合、用户列表字段、写入义务、outbox、worker、回填或兼容分支；源历史继续沿已有保存规则。读取失败不回滚或改变已经提交的业务结果。

<!-- 权威位置: use-cases/UC-APP-052-query-application-management-activity.md#br-app-071 -->
### BR-APP-071：四来源有界合并与归属绑定分页

固定全序 `(occurredAt DESC, sourceKindRank ASC, phaseRank ASC, sourceReviewId DESC)`；VERSION 在 PROFILE 前，DECISION 在 SUBMISSION 前，源 ID 依其规范字符串的二进制字典序比较。相同毫秒仍按完整键确定唯一位置，同一 Review 双阶段不去重为一项。

最多四个索引来源：Version 提交/决定、Profile 提交/决定。每个来源按本 App、所选类别和全局 cursor 后的键过滤，至多取 pageSize+1 候选，总上界404。按完整全序合并取前 pageSize+1，返回前 pageSize，用多出一项判断后续。父资源只对最终页及必要 lookahead 批量读取，不做 N+1、全历史扫描、逐项远程调用或平台级权限后过滤。

签名 token 绑定用途、格式版本、caller 固定摘要、App、ownershipRevision、规范 kinds 和最后实际返回项的完整排序键；pageSize 不绑定。未返回候选不能推进游标；空集合返回 items=[] 且无 token，本 UC 不产生空页带 token。先确认当前 owner 再检查 token，旧 owner404，当前 owner 的无效/过期归属上下文 token400。

每页独立 snapshot，asOf 为本次观察时间，不承诺跨页冻结。并发新提交/决定可能落在已经翻过的较新区间，显式刷新第一页重新发现。所需 App+submittedAt/源ID、App+decision.decidedAt/源ID 索引由显式 migration 添加，启动不建索引；索引与查询须证明上述候选预算，而非先取全部记录再截断。

## 架构决定（仅本次需要的章节）

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

#### gRPC-Web 终止

- gRPC-Web 在 **Traefik** 终止，不进入 App Center 进程。
- App Center 后端只暴露**原生 gRPC**；不嵌入 `grpc-web` wrapper，也不注册 gRPC-Web 专用的 HTTP handler。
- 浏览器流量由 Traefik 完成 gRPC-Web ⇄ gRPC 转换后，以原生 gRPC 到达 App Center；身份键仍为 metadata `x-iwut-identity`。
- 因此 App Center 不为 gRPC-Web 增加 CORS、content-type 或协议转换配置；这些属于 Traefik。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 配套查询契约（按 spec 显式抽取）

> 这些是当前 bounded context 的查询契约；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `app-center/query-contracts/application-management-activity.md`：Application 管理动态读契约

#### 权威与输入

授权、来源、披露、快照、分页及错误以 [UC052](../use-cases/UC-APP-052-query-application-management-activity.md) BR-APP-067–071 为唯一权威。本文件定义最小读投影，不新增事件写入或通知语义。

```text
ListApplicationManagementActivityRequest {
 applicationId
 query: { kinds[], pageSize, pageToken? }
}
GetApplicationManagementActivityRequest { applicationId, activityId }
```

kinds 为 UC052 六种审核提交/结果；省略/空表示全部。不得通过额外过滤项扩展成个人收件箱、人员目录或全平台聚合。

#### 最小投影

```text
VersionReviewRef { versionId, reviewId, attempt, versionLabelAtSubmission }
ProfileReviewRef { profileRevisionId, profileReviewId, attempt, profileRevisionSequence }
ApplicationManagementActivity {
 activityId, applicationId, kind, occurredAt
 target: VersionReviewRef | ProfileReviewRef
}
ApplicationManagementActivityPage { items[], nextPageToken?, asOf }
ApplicationManagementActivityDetail {
 activity
 rejectionReason: string | null
 asOf
}
```

target 与 kind 严格配对，版本标签/资料序号亦为互斥分支。列表没有理由；详情拒绝项返回该次原始理由，其他类别为 null。activityId 稳定定位历史来源，不证明权限。内部比较键、Reviewer 身份和完整审核正文不在投影内。正式Proto把版本标签/资料序号放入各自target分支；rejection_reason使用google.protobuf.Value，服务必须填StringValue或NullValue，使HTTP为明确字符串/null，native亦能区分。其余字段编号与JSON命名以API提交7651f96为准，不因编码差异改变逻辑空值与字段缺席的区别。

#### 消费组合

管理动态只有当前单 App；转让待处理和参与者详情、脚本角色历史、Reviewer 队列沿原入口。前端不得遍历全应用或调用 Reviewer API 补 owner 时间线。

“查看记录”使用 activityId 查询原历史，“查看当前资源”使用 target 中的父资源 ID 进入原管理详情。Version 旧标签、旧拒绝及 Profile 旧批准不改写成当前状态。列表结果和历史详情不携带写操作基线，不能直接触发审核/恢复/重提命令。

asOf 不冻结后续页面，显式刷新重建第一页。Session/App/kinds 变化隔离旧数据；空结果与错误分别展示。没有已读、未读、计数、后台轮询或通知发送。未来真实通知需要独立设计，不能把本投影当作接收/投递协议。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、路由映射、契约测试要求、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、Claims、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-052-query-application-management-activity.md` | 121 | `b2ff2d021587` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `app-center/query-contracts/application-management-activity.md` | 44 | `0ae2e08c7b57` |
