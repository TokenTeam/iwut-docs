# UC-APP-052：查询 Application 管理动态与历史记录

状态：`ACCEPTED`（2026-11-09 用户要求开始实现，仅实施 App Center 部分）。App实施状态见[实施记录](../implements/UC-APP-052-management-activity-readiness.md)。

## 目标与范围

当前 Application 管理员在 Console 的单应用上下文中，按时间查看 Version/Profile 的审核提交与结果，读取最小历史记录。管理动态是既有业务事实的只读投影，没有个人收件人、投递、已读/未读或新增业务写入。

本 UC 补齐 [UC034](UC-APP-034-query-owned-application-versions.md) 只有 latestReview、不能遍历 Version 全部 attempts 的缺口，并合并 [UC039](UC-APP-039-query-owned-application-profile-revisions.md) 的 Profile 历史；不改变两者当前资源查询，不向 owner 开放 UC030/031 的 Reviewer 正文。投影及消费见[管理动态读契约](../query-contracts/application-management-activity.md)。

转让继续使用 [UC050](UC-APP-050-query-incoming-application-admin-transfers.md) 待接收集合与 [UC026](UC-APP-026-transfer-application-administration.md) 参与者详情；平台脚本继续按 [UC045](UC-APP-045-query-script-management-and-reviews.md) 分角色读取历史；Reviewer 继续原队列。本期没有跨应用/全平台动态、编辑/发布事件、脚本聚合活动、通用通知、应用发送消息或用户客户端通知展示契约。

## 接口与输入

候选正式服务 `app_center.v1.application_management_activity.ApplicationManagementActivityService`，本 UC 不分配 Proto 字段编号：

| RPC | App HTTP |
| --- | --- |
| ListApplicationManagementActivity | POST `/v1/applications/{application_id}/management-activity:search`，body=query |
| GetApplicationManagementActivity | GET `/v1/applications/{application_id}/management-activity/{activity_id}` |

外部增加 `/app-center`。沿现行 Session→App audience USER 管理接入，Gateway 的 Developer Console surface 由其 owner 接入；Admin 域名不赋予 owner 读取资格。“Console 消费”是产品范围，后端仍按可信身份与资源资格授权，不信任客户端来源头，也不阻止有权主体通过正式管理 API 读取。

列表 query 仅含 kinds[]、pageSize、pageToken。kinds 省略/空表示全部六类，非空为所选类别并集，去重并按固定枚举顺序规范化；未知值拒绝。pageSize 省略/0 为20，合法范围1..100；pageToken 最多4096 UTF-8 bytes。无自由搜索、recipient、目标用户、offset、totalCount、自定义排序或读状态过滤。Application ID 沿既有管理查询格式；activityId 须为服务可解析的稳定不透明定位。

POST 仅接受单个 JSON 对象，正文最多16 KiB，无 query string；GET 无正文或 query string。HTTP/native 拒绝未知字段。先验证可信身份，再验证业务输入；合法输入下先确认当前 owner，后处理 token 或定位 activity，避免游标/记录探测泄漏。

## 主流程

1. 验证可信 ACTIVE USER，解析本次输入。
2. 在同一 majority 只读 snapshot 中读取 Application，确认当前 adminId 与 ownershipRevision。
3. 列表验证签名 token，按类别读取四个有界来源并合并；详情定位单一源 Review 和阶段。两者均校验必要来源及父子关系。
4. 依读契约返回最小投影和本次观察时间 asOf；所有成功、空结果和错误均 private,no-store。全程不修改业务事实。

## 业务规则

<a id="br-app-067"></a>
### BR-APP-067：当前管理员的应用历史读取资格

两个方法仅接受可信 ACTIVE USER 且本次 Application.adminId 等于 caller AuthId；不要求 APPROVED Developer，不新增 Auth permission。平台管理员、Reviewer、Tester、SYSTEM、search/suspend/restore 均不隐式授权；同一人恰为 owner 时按 owner 读取。

Developer 资格下降，Application ACTIVE/CLOSING/CLOSED、AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED 均不额外取消当前 owner 的历史读权。转让后新 owner 可读既有历史，旧 owner 后续请求统一隐藏；重新取得管理权也不能使用旧 ownershipRevision token。已合法返回的旧响应不承诺远程撤回，消费端须隔离迟到响应。

App 不存在、非当前 owner、活动不存在或定位源不属于路径 App，统一 APPLICATION_MANAGEMENT_ACTIVITY_NOT_FOUND；不因调用者持有其他权限泄漏目标是否存在。对已经绑定本 App 的必要源发现悬空父资源或错误归属，则属于损坏而非可跳过的不存在。

<a id="br-app-068"></a>
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

<a id="br-app-069"></a>
### BR-APP-069：历史记录的最小披露与原文保真

列表与详情投影只包含读契约定义的定位、类别、时间、attempt 及历史资源标签。Version 标签取该次 Review.snapshot.versionLabel，Profile 序号取所属修订的稳定 sequence；不用当前 Version label 改写过去。

列表不返回拒绝理由；详情仅 REJECTED 项返回该次 decision 的原非空 rejectionReason，SUBMITTED/APPROVED 项明确为 null。这是新增 owner 历史读取范围。历史文本按原事实保留并以纯文本展示，不 trim、裁剪、替换或按当前内容政策重新审核。

两者均不返回 submittedBy、decidedBy、Reviewer 身份、完整 snapshot、政策/检查定义、confirmedCheckIds、approvalValidation、脚本正文、OAuth 配置或凭据；不因动态展示扩展其他角色的资料读取资格。

<a id="br-app-070"></a>
### BR-APP-070：管理动态的只读快照与失败关闭

每页/详情在一个 majority 只读 snapshot 内确认当前 Application 归属、ownershipRevision、必要源和父资源。校验源/父 ID 与所属 App、正 attempt/sourceRevision、时间及 BSON 类型、PENDING 无决定/终态唯一匹配决定、决定与绑定政策版本一致，以及本投影所需的历史标签/sequence；时间关系沿源 UC 的既有不变量。校验最终页和必要 lookahead，不为验证全库完整性扫描所有历史。

历史 Review 与当前 Version 最新状态、revision、内容不同可以合法存在，不能强套当前资源一致性；过去批准不是当前已发布或公开的证明。只读取本投影必需的字段，不查询完整政策定义，也不加载其正文作为 owner 输出。

必要事实缺失/损坏整页或详情500，存储/snapshot 不可用503；不漏项、隐藏损坏、返回部分成功或伪装为空。每协议编码响应最多512 KiB，超出明确413/RESOURCE_EXHAUSTED，不截断文本或改序。成功与错误 private,no-store，不回显输入、认证材料或底层原因。

不写 fence、revision、业务审计、访问/活动/已读事实，不调用 Auth、Scope、DNS 或外部网页，不用可能持久化过期状态的转让 Get 拼装结果。没有新增活动集合、用户列表字段、写入义务、outbox、worker、回填或兼容分支；源历史继续沿已有保存规则。读取失败不回滚或改变已经提交的业务结果。

<a id="br-app-071"></a>
### BR-APP-071：四来源有界合并与归属绑定分页

固定全序 `(occurredAt DESC, sourceKindRank ASC, phaseRank ASC, sourceReviewId DESC)`；VERSION 在 PROFILE 前，DECISION 在 SUBMISSION 前，源 ID 依其规范字符串的二进制字典序比较。相同毫秒仍按完整键确定唯一位置，同一 Review 双阶段不去重为一项。

最多四个索引来源：Version 提交/决定、Profile 提交/决定。每个来源按本 App、所选类别和全局 cursor 后的键过滤，至多取 pageSize+1 候选，总上界404。按完整全序合并取前 pageSize+1，返回前 pageSize，用多出一项判断后续。父资源只对最终页及必要 lookahead 批量读取，不做 N+1、全历史扫描、逐项远程调用或平台级权限后过滤。

签名 token 绑定用途、格式版本、caller 固定摘要、App、ownershipRevision、规范 kinds 和最后实际返回项的完整排序键；pageSize 不绑定。未返回候选不能推进游标；空集合返回 items=[] 且无 token，本 UC 不产生空页带 token。先确认当前 owner 再检查 token，旧 owner404，当前 owner 的无效/过期归属上下文 token400。

每页独立 snapshot，asOf 为本次观察时间，不承诺跨页冻结。并发新提交/决定可能落在已经翻过的较新区间，显式刷新第一页重新发现。所需 App+submittedAt/源ID、App+decision.decidedAt/源ID 索引由显式 migration 添加，启动不建索引；索引与查询须证明上述候选预算，而非先取全部记录再截断。

## 错误与协议

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

## 消费与写命令边界

Console 当前应用增加独立“管理动态”页，详情区分“查看记录”和“查看当前版本/资料”。历史记录不包含批准、拒绝、恢复、重提等动作；进入原正式详情后按原 UC 重读、确认、鉴权，不能把动态或 asOf 当作 OCC/命令基线。历史批准不冒充当前公开资料或发布状态。

仅显式加载、翻下一页和刷新；不后台扫描全部页/应用，不轮询、红点或未读数。无历史与读取失败分开呈现。Session、App、筛选或查询代际变化隔离旧分页链/详情/迟到响应，归属拒绝清除对应私有数据。具体页面 UC 由 Console owner 设计维护，不以本 UC 代替前端审核。

## 验收与串行依赖

1. 六类活动、同 Review 双阶段、多 attempt、原快照标签、原拒绝理由、人工/自动/级联拒绝、APPLICATION_CLOSED 无伪事件；恢复/编辑后的旧 Review 可读，Profile 新修订不覆盖旧记录。
2. owner 与无 owner 的平台管理员/Reviewer/Tester/仅 search 或运维权限；Developer 资格下降、应用关闭/暂停/归档；转让后新旧 owner 和重新取得管理权的旧 token。
3. 四来源同毫秒/同父多 attempt、单类/混合/全部 kinds、变 pageSize、未返回候选保留、空集合无 token、篡改/换人/换 App/换筛选；实际候选与父读取预算和命名索引验证。
4. 提交/决定/恢复/转让/关闭在受控事务前后竞争，只返回完整 snapshot；必要父源缺失、错误归属/绑定、非法 BSON/时间/状态、存储失败均按分类失败，无部分成功或写入。
5. 列表无理由、详情只含本次合法披露、无 Reviewer/策略/正文/凭据；输入/响应预算、private,no-store、三协议和 SDK、实际 Console Cookie/BFF 读取及迟到响应隔离。

正文接受后，串行完成 App 只读 UseCase/Port/Mongo 查询与显式索引、Proto/生成物和专项；按用户 API 对齐→Gateway owner 接入→固定本地三镜像联验→冻结完整 backend 门禁流程实施。Console 仅在其 UC 接受和后端契约就绪后实现。现有完成项不重标未完成；真实通知与正式新政策发布草案不是前置。本轮只实施 App Center；Auth、Gateway、Console 不在本轮实现范围，跨服务消费验收保留待接入状态，不 push 或部署。
