# Console 管理动态 V1：设计草案

状态：方案方向已获用户认可（2026-11-09）；具体正文已收敛为 [UC052](../use-cases/UC-APP-052-query-application-management-activity.md)及[读契约](../query-contracts/application-management-activity.md)，App正文已于2026-11-09获接受并授权实施，状态 `ACCEPTED`、App后端实现 `COMPLETE`（完整backend24/24通过），详见[实施记录](../implements/UC-APP-052-management-activity-readiness.md)。本文件保留设计推导与范围选择，不作为第二权威；下文旧计划为历史说明。

2026-11-11 状态更新：[Console UC023](../../console/use-cases/UC-CONSOLE-023-query-application-management-activity.md)已于2026-11-10获接受，实现与验收由Console owner维护。App功能分支已推送`db01313`、API为`241d56de6f8a3f68ed91969a4239a8c9fe32baad`；本轮master合入与CNB镜像发布仍在核验，尚不记录为成功。个人通知、自动加载、long polling与WebSocket均未进入本轮。

## 需求与名称

建议名称为“管理动态”：让管理人员在 Console 的管理上下文中看到业务发生的变化、定位相关资源，再进入正式详情。用户客户端没有本功能的展示契约，也不向第三方应用开放发送消息的入口。

名称同时收敛模型：本轮不建立 Notification、个人收件箱或消息投递任务；管理动态是 App 已有业务事实的读取视图。初期不附带“已读／未读／已送达”语义，不复制上一稿的个人收件记录与逐条标读功能。

现有“待接收转让”继续使用该名称和 [UC050](../use-cases/UC-APP-050-query-incoming-application-admin-transfers.md)：它表达本人的当前有效 PENDING 事项。管理动态可以解释转让曾被发起、接受或结束，但不替代这份待处理集合。

## 当前管理动态与未来通知的责任

| 方面 | 本轮管理动态 | 未来真实通知需要另定 |
| --- | --- | --- |
| 产品目的 | 管理资源时查询发生过的业务变化，打开正式详情 | 平台或应用主动把某件事告知目标用户 |
| 对象 | Application、Transfer、Review 等业务资源及其事实 | 通知意图、发送主体、目标用户/受众、渠道与投递尝试 |
| 资格 | 本次调用者当前拥有的业务读取资格 | 谁能发送给谁、用户是否接收、内容可见性与撤权规则 |
| 出现方式 | 用户在 Console 明确加载当前管理上下文 | 用户客户端/Console/其他渠道如何呈现、同步或推送 |
| 状态 | 原业务状态及其历史；本轮没有个人读标记 | 是否需要已读/送达、跨端同步、到期/删除和偏好 |
| 成本 | 有界查询、既有历史存储及必要读索引 | 应用配额、扇出、限流、存储周期、渠道成本与防滥用等 |

以用户为一个字段保存列表，可以表达简单数据结构，但不会自动决定上述通知语义。本轮不选择“将管理动态塞进 Auth 用户记录”，也不提前建立能接入所有应用消息的统一消息管道。App 拥有自己的业务事实和读取视图，Auth 仍拥有身份与权限。

“只在 Console 显示”是本轮产品与消费契约的边界，不是可信身份判定：后端仍依据可信身份和当前业务权限授权，不能信任客户端自报“我来自 Console”。接受后由 Gateway/Console owner 核定管理 surface 与 BFF 消费；不默认产生普通用户客户端的通知 API 或应用发送权限。

## 建议最小范围

优先在既有管理资源上下文展示，而不是新增一个按个人投递的全局收件入口：

| 资源上下文 | 可复用的事实与正式入口 |
| --- | --- |
| 转让详情 | [UC026](../use-cases/UC-APP-026-transfer-application-administration.md) 的申请、当前状态和处理事实；参与者边界不变 |
| 当前所管理应用的版本 | [UC034](../use-cases/UC-APP-034-query-owned-application-versions.md) 的当前版本及最新审核摘要；完整attempt历史需要下文的新查询 |
| 当前所管理应用的资料 | [UC039](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md) 的修订/审核历史与正式详情 |

应先核对这些现有读模型是否足以支撑页面，已有正式查询可组合时无需再建立一套事件或写入流程。若需要统一排序、分页或缺少必要的历史读取，接受后再明确一个窄的管理活动查询 UC；不能由前端扫描全部应用、审核队列或无限翻页拼出全局列表。

平台脚本管理可按 [UC045](../use-cases/UC-APP-045-query-script-management-and-reviews.md) 已有的审核/发布历史展示其对应动态。maintain、review、publish 与运维的披露范围各自保留，不能把完整审核正文/拒绝理由通过动态统一展示给只拥有发布或运维权的人。本草案不新增脚本角色广播或全 Reviewer 提醒。

若希望 Console 另有跨应用集中的“管理动态”入口，需要再审其授权集合、有界聚合、排序和分页；它仍可作为管理读模型，但不因“集中展示”而生成固定个人收件人、后台投递或未读计数。本稿建议首期先做资源上下文，集中入口保留待选择。

## 模型与可见性

候选投影可表达稳定的活动定位、业务类型、资源引用、发生时间、变化类别，以及定位正式详情所需的最小结果。底层可以从已有不可变业务事实派生，不预先要求新的 activity collection；它没有 recipient、channel、deliveryStatus、readAt 或任意消息正文。

管理动态不成为第二份业务真相：

- 源审核结果、转让和发布历史继续由原业务拥有；不能通过改动态条目改变业务状态。
- 同一事实在读取/刷新后只有一个稳定定位，不因每次查询重新生成一条事件；没有“重新发给某个人”的语义。
- Application 动态沿当前 owner 历史读权。转让后新 owner 可以查看其按 UC034/039 有权读取的既有业务历史；原 owner 失去该读取资格时相应视图退场。这与原稿“固定收件人且新 owner 不收到旧通知”的模型不同，原固定收件安排不再沿用。
- Transfer 动态沿原 from/to 参与者读权；不能因为发起人已转出应用而抹掉其参与者读取资格。
- Developer 资格下降或应用暂停/归档/关闭，不自行改变原 UC 的历史读取规则。Reviewer/脚本角色也不因动态入口扩大到 owner 私有数据。
- 必要事实缺失或损坏、存储不可用与正常无记录/失权须区分；不合成成功记录或通过隐藏损坏凑空列表。

查询保持只读；尤其不能为了拼动态调用会持久化 EXPIRED 的转让 Get。若新建聚合查询，需定义同次一致读取、有界扫描、签名分页、空页继续和 private,no-store。上述具体契约仍在接受后的 UC 中固定，不在本稿假定新 API 已存在。

## 点击、可靠性与写入边界

点击动态进入现有正式详情。确认、接受/拒绝、批准/拒绝等动作继续重读当前事实、权限和命令前置条件；动态里的过去状态不能当作当前操作基线。

本稿撤下原“业务事务同时写个人收件记录”的建议。动态读取失败应如实失败和允许重读，不因此回滚已提交的转让或审核，也不为生成管理动态给每次业务写入新增收件义务、投递 worker 或 outbox。

可靠性首先来自已有不可变业务事实和历史；查询或页面失败后可重新读取。若实际发现业务缺少需要展示的事实，应指出具体来源缺口并另行设计记录规则，不能先用内存消息补足，也不能声称现有字段提供它并没有的完整事件流。UC028 的运维告警 outbox 及其外部可靠投递维持原范围。

## 与未来通知的关系

未来如果接受向用户客户端显示通知、或允许应用主动发送消息，应单独设计通知能力的 bounded context、发送授权、受众、跨端语义、成本与可靠投递。届时可以引用 App 原有审核/转让等业务事实，避免让发送方重复解释业务结果；不预承诺复用管理动态的表、API 或读取链作为投递管道。

两者保留的是不同责任：App 的业务事实只定义一次；管理动态负责有权管理者如何查询这些事实；通知能力负责一次告知意图如何路由、限制和投递。将来可以消费同一个事实来源，不需要现在复制一份通用通知领域模型，也不要求把管理查询绑定到未来通知服务才能运行。

## V1 采用的具体范围

建议首期采用下表，不同时建设两个入口方案：

| 范围 | V1 安排 |
| --- | --- |
| Developer 的当前应用 | 新增“管理动态”整页，集中展示该应用 Version/Profile 的审核提交与结果；提供最小历史记录详情 |
| 转让 | 保留“待接收转让”和按 transferId 的参与者详情；详情中的申请/处理事实继续由 UC026 提供，不把全应用转让史加入 owner 动态 |
| Admin 平台脚本 | 继续使用 UC045 的审核/发布历史，在各自权限下展示；本期不新增脚本聚合活动 API |
| Reviewer | 继续正式待审队列和审核详情，不新建个人 Reviewer 收件箱 |
| 跨应用集中页、全平台动态 | V1 不包含；当前应用页面不能通过前端遍历所有应用伪造这种能力 |
| 个人读状态 | 不保存已读/未读，不新增标读命令、角标或后台轮询 |

选单个应用是为了先固定明确的资源授权和有限来源合并，提供完整审核时间线；跨应用入口还需要独立解决资源集合和聚合成本，不借这次设计自动引入。

### 已有数据与实际查询缺口

[UC034](../use-cases/UC-APP-034-query-owned-application-versions.md) 明确只返回 Version 的 latestReview，不提供完整历史 attempts。它不能支撑旧拒绝、重新提交等全部活动的时间线；前端也不能调用只给 Reviewer 的 UC030 来补 owner 历史。

[UC039](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md) 已有按单个 ProfileRevision 的有界审核历史，但不能直接与全部 Version/Profile 活动合并分页。故建议接受后新增一个窄的 Application 管理活动查询 UC，覆盖本节列表和最小历史详情；不是新建收件或事件写入 UC。

源事实已存在：ApplicationReview/ProfileReview 的 submittedAt、唯一 decision 及 decidedAt，Review 与所属 Version/ProfileRevision 的关系。没有新增业务事实或“所有编辑事件”的假设，不使用可变 updatedAt 推算历史。

## 新应用活动读取：事件与最小投影

V1 六种活动都从已有记录派生，同一次审核可以产生一项提交、一项决定：

| kind | 发生时间 | 最小定位 |
| --- | --- | --- |
| VERSION_REVIEW_SUBMITTED | Review.submittedAt | applicationId、versionId、reviewId、attempt |
| VERSION_REVIEW_APPROVED | decision.decidedAt | 同上 |
| VERSION_REVIEW_REJECTED | decision.decidedAt | 同上 |
| PROFILE_REVIEW_SUBMITTED | ProfileReview.submittedAt | applicationId、profileRevisionId、profileReviewId、attempt |
| PROFILE_REVIEW_APPROVED | decision.decidedAt | 同上 |
| PROFILE_REVIEW_REJECTED | decision.decidedAt | 同上 |

历史提交项表达“当时提交”，不以当前已终态为理由消失，也不标为当前仍待审。自动拒绝及 UC049 的实际应用拒绝复用同一 Version 拒绝项，不另产生“收到级联消息”；没有决定的 APPLICATION_CLOSED 豁免不产生拒绝项。

候选逻辑投影：

```text
ApplicationManagementActivity {
 activityId                 // 稳定、不透明；不得当作命令或授权凭据
 applicationId, kind, occurredAt
 target: VersionReviewRef | ProfileReviewRef
 versionLabelAtSubmission?  // 仅 Version，取原审核快照的 label
 profileRevisionSequence?   // 仅 Profile，取所属修订的稳定 sequence
}
ApplicationManagementActivityPage { items[], nextPageToken?, asOf }
ApplicationManagementActivityDetail {
 activity
 rejectionReason: string | null
 asOf
}
```

activityId 由源类型、源 Review ID 和 SUBMISSION/DECISION 阶段确定稳定定位，不因每次读取生成新 UUID，不保存独立活动记录。列表文案由 kind 的固定展示规则及上述资源标签构成，标签按纯文本原样显示，不能用当前 Version label 代替旧快照标签。

列表不包含 reason；单项拒绝记录详情从该次不可变 decision 读取原 rejectionReason。提交/批准项的 rejectionReason 明确为空。历史拒绝理由属于本次新增 owner 历史读取范围，须随新 UC 审核，不能把它误说成 UC034 已提供的全部历史能力。

两个读取均不返回 submittedBy、decidedBy、Reviewer 身份、完整 snapshot、policy/check definitions、confirmedCheckIds、approvalValidation、脚本正文、OAuth 配置或凭据。不会为展示原因而开放 Reviewer 的完整详情。

## 身份与访问规则

1. 请求先验证可信 ACTIVE USER，调用者身份只来自认证上下文。随后依当前 Application.adminId 授权；不需要 APPROVED Developer，不新增 Auth permission。
2. 平台管理员、Reviewer、Tester、SYSTEM 或仅有 search/suspend/restore 的人，不因此获得 owner 动态。若其恰为当前 owner，按 owner 范围读取。
3. App 不存在、不是当前 owner、活动不存在或源关系不属于该 App，统一 404。ACTIVE/CLOSING/CLOSED、AVAILABLE/SUSPENDED、UNARCHIVED/ARCHIVED 不额外删除已有 owner 历史读权。
4. 新 owner 可以查询当前所管理 App 的既有管理历史；旧 owner 后续请求退场。已返回给旧 owner 的合法旧响应无法远程撤回，Console 需按 Session/应用/查询代际隔离迟到响应。
5. 每页和单项在同一次 majority read-only snapshot 中确认 owner、ownershipRevision、必要来源与父子关系。查询不写 fence、revision、访问事实、活动、读标记或业务审计，不调用 Auth、Scope、DNS 或目标网页。

Reviewer 权限授撤不影响独立 owner 读权；应用管理权变化须使旧分页上下文失效。调用者后来重新取得该应用管理权，其旧 ownershipRevision 游标也不可复用。

## 候选接口与请求边界

接受后由 App/API owner 按以下语义编写正式 Proto，本文没有定义字段编号或增加实现：

| 动作 | 候选 App HTTP |
| --- | --- |
| ListApplicationManagementActivity | POST `/v1/applications/{application_id}/management-activity:search`，body=query |
| GetApplicationManagementActivity | GET `/v1/applications/{application_id}/management-activity/{activity_id}` |

列表 query 仅有 kinds[]、pageSize、pageToken。kinds 省略或空表示六类全部；非空为所选类别并集，去重/规范化，未知值拒绝。pageSize 省略/0为20，范围1..100，pageToken最多4096 UTF-8 bytes。没有 recipient、目标用户、offset、总数、任意排序、已读过滤或自由搜索。

POST只接受一个JSON对象，正文最多16 KiB，无query string覆盖；GET无正文/query；HTTP及native未知字段拒绝，身份先于业务输入。候选错误为：缺/坏身份401、非法输入/游标400、统一隐藏404、必要事实损坏500、存储不可用503。成功、空结果和错误都 private,no-store，不回显输入或底层原因。

沿既有管理 API 的 Session→App audience USER 接入模式；Gateway 增加 Developer Console 管理 surface，Admin 不因页面域名取得 owner 权限。内部 HTTP/native gRPC 及 Gateway 协议消费由各 owner 按现行平台契约核定，不因存在可授权的管理 API 就自动产生用户客户端消息展示或应用发送契约，也不信任自报 Console 来源的请求头。本文不以“普通客户端没有该页面”作网络访问控制；拥有业务读取资格者通过受授权管理 API 访问，仍属于该资源管理查询，不代表获得用户通知订阅或应用发送权。

## 排序、分页与可控成本

排序固定为 `(occurredAt DESC, sourceKindRank ASC, phaseRank ASC, sourceReviewId DESC)`；sourceKindRank为VERSION在PROFILE前，phaseRank为DECISION在SUBMISSION前。同一毫秒的多项不会随机换序或被去重为一项。内部比较键不作为普通展示字段；activityId 定位单项。

列表最多四个有序来源：Version提交、Version决定、Profile提交、Profile决定。每个来源限定该 Application 及所选类别，在全局 cursor 后读取至多 `pageSize+1` 个候选；固定上界为404项候选。按全局顺序合并至多 `pageSize+1` 项，返回前pageSize项，以额外一项判断nextPageToken。不能以每个来源各拿一页后拼接的方式改变全局排序。

游标仅推进至**实际最后返回项**，未返回的合法候选留待后续；同一 Review 的两个阶段各有独立位置。无结果且没有更多候选返回明确空数组和空token；本方案不包含按权限后过滤的大范围平台扫描，因而不设计空页带token的扫描流程。

签名 token 绑定用途、格式版本、调用者固定摘要、App、当前ownershipRevision、规范kinds及完整末项比较键；pageSize不绑定，可调整后续页大小。先确认当前owner再处理token，旧owner继续统一404；已获权的新owner不能复用旧token。每页重新读取，asOf不承诺跨页冻结，新的决定可能出现在已翻过的较新区间，明确刷新第一页才能重新发现。

来源查询按App和时间/唯一ID的命名索引支撑，提交与决定时间分别建立必要索引，由显式migration添加；服务启动不建索引。不做全历史扫描、逐项远程调用或N+1事务。只批量加载最终页及必要lookahead的父资源，响应各协议最大512 KiB；超预算明确失败，不裁剪理由、漏项或隐式改变顺序。

不增加活动集合、个人列表字段、写入义务、outbox、worker或保留周期；动态和现有源事实共享既有保存规则。成本来自有限索引与有界查询，不预先承担未来通知的扇出、接收人存储和外部渠道费用。

## 来源一致性与历史保真

活动基于原Review固定提交事实及其唯一决定，审核恢复/新attempt后原条目仍存在。历史Review不能强套“必须与当前Version的最新状态、revision、内容相等”的判断，否则恢复后的合法旧拒绝会被误判损坏。

必要校验包括源ID/父ID和所属App、正attempt/源revision、时间/BSON类型、状态与decision相斥关系、决定结果及绑定版本一致、父Version或ProfileRevision属于该App，以及用于展示的快照标签/稳定sequence。终态有完整唯一决定且时间关系合法；PENDING没有决定。损坏整页/详情失败，不跳过或替换为最新Review。

只验证和组合本投影需要的事实，不加载完整政策定义或历史正文再暴露给owner。合法历史文本按原事实保留，纯文本展示，不借查询做trim、重写或当前内容政策重新审核。

## Console 消费方案交接

建议 Developer 当前应用导航增加“管理动态”，打开独立整页，列出时间、活动类别、版本标签/资料修订及审核次数。默认全部，可按上述六类筛选；每页20，提供明确的下一页和刷新，不自动扫描所有页，不后台轮询或显示红点/未读数。

“查看记录”读取该项历史详情，展示当时发生的事实；拒绝时可看到该次原理由。“查看当前版本／资料”进入原管理详情，两者文案区分，不能以最新Review覆盖被点击的历史事件。若原有路由无法表达所选历史记录，由Console owner在其待审设计中定义独立记录页，不伪造历史链接。

此处没有接受、拒绝、批准、恢复或重提按钮，也不以该页的revision作为写操作基线；进入原页面后照原UC读取、确认及命令恢复。Profile“当时批准”不表示仍为当前公开资料；Version“当时批准”不表示已发布。

成功空结果显示“该应用暂无审核动态”；故障显示读取失败，不能当作无活动。Session/应用/筛选变化取消旧分页链和详情，旧403/成功不能覆盖新Query。其余暂时失败处理沿Console私有读取规范；权限/归属拒绝移除对应内容。

本段是App读契约的产品交接建议，Console具体UC和页面由其owner编写，不在App任务中改Console源。Console owner已补[消费设计](../../console/design-notes/2026-11-09-application-management-activity-consumption.md)及待审[UC-CONSOLE-023](../../console/use-cases/UC-CONSOLE-023-query-application-management-activity.md)，确认现有平级导航可以承载；App具体UC已接受并实施；Console具体UC仍待审且不推进，不以互相引用替代审核。

## 验收与串行实施计划

- 权限：当前owner、无应用普通USER、平台管理员无owner、Reviewer无owner、仅search/运维权；Developer资格下降与应用关闭仍可读原历史。
- 来源：六类、自动拒绝/级联拒绝、单Review双阶段、Version拒绝恢复/新提交后旧attempt、Profile终态及新修订、旧批准不冒充当前公开/发布。
- 分页：四来源同毫秒、相同父资源多attempt、仅一种/混合类别、页大小变化、不丢未返回候选、游标篡改/换人/换App/换筛选/转让后失效；每来源候选与父批量读取有实际上界。
- 一致性：提交、决定、恢复、转让、关闭在受控事务前后竞争，只返回完整快照；错误父归属、绑定、时间、状态/决定、必要父源缺失与存储失败按正式分类，不返回部分成功。
- 隐私与协议：列表无理由、详情只披露该次owner可见理由，无Reviewer/内部政策/正文/凭据；三协议、生成客户端、缓存头、输入校验及实际Console Cookie/BFF链。
- 写入隔离：列表/详情不产生活动、收件记录或任何业务写入；读取故障不改变审核或转让事实，点击不触发旧命令。

2026-11-09 用户认可具体V1并要求编写UC，现已分配待审UC052/BR-APP-067–071及读契约/brief，并给UC034补充边界引用，未改变latestReview行为。正文接受后才启动App/API串行实现/专项，交Gateway owner，固定镜像联合验收及完整backend后，再由Console owner按已接受页面设计实现。

## 本次审核点

本稿建议接受的具体交付为：**按应用的六类审核管理动态、只读列表与最小历史详情、当前owner授权、无个人读状态或投递、保留转让与脚本既有入口。** 新增历史理由的最小披露和Console页面交接也随本稿交审。

真实通知继续独立后置，正式审核策略A→B候选仍按另一份待审稿处理，两者不作为本方案前置。App UC052已获接受并进入独立实现；Console保持待审、不推进。实施和验收状态以对应记录为准，无push/部署。
