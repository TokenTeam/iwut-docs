# UC-APP-029：查询我的 Application 列表与管理详情

状态：`ACCEPTED`

## 目标与范围

> 已认证用户查询自己当前记录为管理员的 Application 列表，并读取一个 Application 的管理概览。结果服务 Developer Console，不复用普通用户 Catalog，也不改变任何领域状态。

本用例交付两个查询：

- `ListMyApplications`：分页列出 `adminId` 等于调用者 `authId` 的 Application；
- `GetMyApplication`：返回一个 Application 的核心状态和依附能力摘要。

本用例不交付 Profile/Version 完整历史、Tester 成员名单、审核队列、secret 明文、审计日志、搜索排名或前端页面。这些事实通过各自能力查询或后续 UC 提供。

## 身份、授权与存在性隐藏

查询只接受 Gateway 验证后的可信 USER 身份。调用者不需要当前仍是 APPROVED Developer；资格变化不删除其已有管理关系，也不能阻止其查看需要处置的 Application。

列表只以可信 `authId` 作为管理员条件。详情中 Application 不存在，或其当前保存的 `adminId` 与调用者不一致，都返回同一个 `ApplicationManagementNotFound`。禁止先返回“存在但无权限”，避免枚举 Application。

转让接受提交后，新管理员立即成为唯一可读管理详情的身份；旧管理员不能依靠旧 cursor 或缓存继续读取。响应使用 `Cache-Control: private, no-store`。

## 列表语义

输入：

```text
ListMyApplicationsQuery {
  lifecycleStatuses?: ACTIVE | CLOSING | CLOSED []
  platformAvailabilityStatuses?: AVAILABLE | SUSPENDED []
  pageSize: 1..100 = 20
  pageToken?
}
```

空 lifecycle filter 默认只返回 `ACTIVE` 与 `CLOSING`；调用者必须显式包含 `CLOSED` 才能读取已关闭历史。空 availability filter 不限制状态。`CLOSED` 仍保留最后记录的 `adminId`，只表示历史读取权，不恢复 owner 义务。

结果按 `(createdAt DESC, applicationId DESC)` 排序，使用不透明 keyset token。token 至少绑定调用者、过滤条件、最后一个 key 和版本；编码不合法、换用户或换 filter 返回 `InvalidApplicationManagementPageToken`。

列表项只返回 Application 核心状态以及管理页导航需要的轻量计数：Version 总数、待处理 Version Review 数、待处理 Profile Review 数、ACTIVE Tester 数。列表不得逐项执行无界子查询。

## 管理详情

详情在一个 MongoDB majority snapshot 中组合以下权威事实：

```text
OwnedApplicationManagementDetail {
  application
  counts
  profileState
  publications[]
  filterState
  oauthRegistrations[]
  pendingTransfer?
  closure?
  asOf
}
```

- `application`：ID、技术名称、记录管理员、createdAt、ownership/lifecycle/platform availability revision 和状态；
- `counts`：Version 总数、四种 Version reviewStatus 计数、PENDING Version/Profile Review 数、ACTIVE Tester 数；
- `profileState`：working 与 currentPublished 指针；指针为空是合法状态；
- `publications`：每个已有 `(applicationId, rpcApiMajor)` 的 TEST/GREY/STABLE 槽位 ID、Version ID、rollout percent 与 Publication revision；
- `filterState`：`ALLOW_ALL` 默认，或当前 Filter revision 的 ID、sequence、schemaVersion、mode 和容器 revision；
- `oauthRegistrations`：每个已有 channel 的 PUBLIC/CONFIDENTIAL clientId、状态、authorizationEpoch、registrationRevision，以及 CONFIDENTIAL credential revision/rotatedAt 元数据；绝不返回 secret/hash；
- `pendingTransfer`：仍为 PENDING 且未到期的转让摘要；已到期但尚未后台收敛的记录按 EXPIRED 对待且不返回；
- `closure`：CLOSING/CLOSED 时返回 closureId、状态、Auth revocation state 和时间摘要。

本详情是读取投影，不能作为后续写命令的授权证明。所有命令仍以各自事务中的最新 owner、lifecycle、revision 和资格检查为准。

## 一致性与损坏状态

列表允许读取投影短暂滞后，但每页返回 `asOf`，且每个列表项内部必须一致。详情必须来自单个 snapshot。

依附记录缺失且语义允许默认值时返回默认值，例如没有 Profile、Filter、Publication 或 OAuth registration。出现不可能状态时整次查询返回 `ApplicationManagementStateInconsistent` / `INTERNAL`，不得隐藏损坏字段并返回部分详情。不可能状态包括指针指向错误 Application、负计数、重复唯一槽位、CLOSING/CLOSED 缺少匹配 closure，以及 malformed OAuth registration。

## 最小查询模型与索引

实现新增管理查询 port，不让读取模型进入 Application 聚合。MongoDB 为 Application 列表增加：

```text
(adminId ASC, lifecycleStatus ASC, createdAt DESC, id DESC)
```

详情复用既有唯一索引，并使用按 applicationId 的批量查询。禁止为每个列表项串行加载完整依附集合。

## API 草图

```text
rpc ListMyApplications(ListMyApplicationsRequest)
  POST /v1/applications:search body=query

rpc GetMyApplication(GetMyApplicationRequest)
  GET /v1/applications/{application_id}
```

请求 body 不包含 authId。列表返回 `items`, `nextPageToken`, `asOf`；详情返回上述管理快照。

## 验收场景

1. 当前管理员能列出 ACTIVE 与 SUSPENDED Application；SUSPENDED 不从管理面隐藏。
2. 默认列表排除 CLOSED；显式筛选能读取由调用者最后管理的 CLOSED 历史。
3. 转让前后只有当前保存的管理员能读取；旧 token 不能跨身份使用。
4. 非管理员详情与不存在统一返回 NOT_FOUND。
5. 列表排序、同时间 tie-break、翻页、非法 token 和过滤条件绑定稳定。
6. 详情正确组合无 Profile/无 Publication/默认 Filter 等合法空状态。
7. 详情返回 publication、OAuth、transfer、closure 元数据且永不披露 credential secret/hash。
8. snapshot 并发测试不返回新 owner 配旧 dependent state 的撕裂结果。
9. 损坏指针、重复槽位或闭合状态不一致返回 INTERNAL，不返回部分结果。
10. HTTP 与原生 gRPC 共享相同身份、错误和结果语义。

## 实现依赖与交付边界

Application、Profile、Version、Publication、Filter、OAuth、Transfer、Closure 和 Tester 集合均已存在；本用例不依赖 Auth 新接口。需要新增 Proto、Mongo 查询适配器、列表索引、HTTP/gRPC transport、composition wiring 和真实 MongoDB 验收。

## 业务规则

<a id="br-app-038"></a>
### BR-APP-038：当前管理员私有读取

管理查询只向 Application 当前保存的 adminId 对应可信用户返回；不存在与非管理员必须统一隐藏。

<a id="br-app-039"></a>
### BR-APP-039：生命周期可见性

SUSPENDED Application 始终保留管理可见性；CLOSED 只在显式筛选或直接详情中作为历史可见，不恢复 owner 义务。

<a id="br-app-040"></a>
### BR-APP-040：稳定私有分页

列表使用绑定调用者与过滤条件的 `(createdAt, applicationId)` 降序 keyset，不接受 offset；token 只是查询游标，不承载授权结论。

<a id="br-app-041"></a>
### BR-APP-041：管理详情是组合读取投影

详情组合已有聚合的权威事实，不扩大 Application 聚合，也不成为写入授权证明。

<a id="br-app-042"></a>
### BR-APP-042：一致快照与失败关闭

详情必须来自单个一致 snapshot；不变量损坏导致整次查询 INTERNAL，不能返回部分详情。

<a id="br-app-043"></a>
### BR-APP-043：管理最小披露

管理结果只披露当前管理任务需要的事实，永不返回 OAuth secret/hash、Tester 身份名单或 Reviewer 内部事实，并禁止共享缓存。

## 变更记录

- 2026-10-07：确认公开 Catalog 不能替代 Developer Console 管理读取；设计进入 `ACCEPTED`。
