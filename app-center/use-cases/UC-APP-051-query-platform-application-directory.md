# UC-APP-051：查询平台 Application 管理目录与摘要

状态：`ACCEPTED`（2026-11-08 用户接受草案并授权按顺序实施；Auth权限管理设计由Auth owner另行交审）。

## 目标与边界

获精确读取权限的可信ACTIVE USER可搜索所有Application的最小核心目录与摘要，定位后进入各正式治理/运维入口。该目录独立于 [UC029](UC-APP-029-query-owned-application-management.md) 当前管理员私有查询及 [UC024](UC-APP-024-query-public-application-catalog.md) 公开运行目录，不放宽其权限或复用其数据拼出全平台目录。

用户搜索只服务管理员治理，由Auth拥有；本UC不提供人员目录/邮箱解析、不查询Auth资料、不返回Version/Profile/Review正文、OAuth/Filter配置、凭据或人员治理理由。Console所有者负责页面接入，App不实现Console。

## 精确读取权限

两个方法均要求App audience可信ACTIVE USER含精确 `app.application.search`。平台管理员、Reviewer、Developer、应用owner、suspend/restore权限均不隐式赋予该权限；该权限也不赋予任何写入或UC029私有详情读取权。鉴权先于参数/目标读取。

Auth owner负责新权限独立授撤、本人有效权限发现、permissionRevision及App audience签发的权威UC；其设计需按用户流程单独审核。App只消费该精确ID，不在App建立权限来源副本。撤权沿正式短期JWS边界，不承诺离线App瞬时撤权。该Auth契约就绪前不开放依赖其签发的真实链验收。

Gateway强制Session，增加ADMIN Console surface，不增加Developer Console全平台目录；域名不代替App授权。

## 正式接口与输入

独立 `app_center.v1.application_platform_query.ApplicationPlatformQueryService`：

| RPC | App HTTP |
| --- | --- |
| SearchPlatformApplications | POST `/v1/platform/applications:search`，body=query |
| GetPlatformApplicationSummary | GET `/v1/platform/applications/{application_id}` |

外部增加 `/app-center`。搜索输入和返回字段见[平台应用目录读契约](../query-contracts/platform-application-directory.md)。query中applicationId/adminAuthId精确匹配，namePrefix使用Application技术名称的现有nameKey规则，不接受正则。各非空过滤条件AND组合；空状态维度不限制，空query可分页浏览。首期不搜索公开Profile展示名、描述、版本内容，不提供全文排序。

pageSize省略/0为20，范围1..100，pageToken最大4096 UTF-8 bytes。拒绝未知字段、非法/未知状态及非法ID/前缀；POST只接受单个JSON对象、最大16KiB、无query string覆盖；GET无body/query。native未知字段同样拒绝。

## 读取与分页

每次使用一致majority只读snapshot和本次观察时间，不写访问事实或gate。覆盖未发布、无公开Profile、暂停、归档、CLOSING/CLOSED应用；三种状态维度独立，不以某一状态推导另一状态。

按 `(nameKey ASC,applicationId ASC)` keyset排序；比较键不作为响应字段。签名token绑定caller、用途、版本、规范过滤条件与末项位置。每页底层扫描最多500条，允许短页/空页附nextPageToken，但不跳过尚未返回的合法项；无offset/totalCount或跨页冻结。读取只组合最小核心状态，不逐项聚合子资源或调用Auth。

目录详情与搜索使用同一权限及相同最小投影，用于重新定位已知ID。选中摘要不构成操作授权或专用revision基线；写命令仍依各自正式入口重读/确认/鉴权。

## 错误与缓存

缺失/无效USER401，缺精确permission403；非法请求400，错误token400；摘要目标不存在404；必要事实损坏500；存储/snapshot不可用503。稳定reason分别为 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY、APPLICATION_PLATFORM_SEARCH_REQUIRED、INVALID_PLATFORM_APPLICATION_QUERY、INVALID_PLATFORM_APPLICATION_PAGE_TOKEN、PLATFORM_APPLICATION_NOT_FOUND、PLATFORM_APPLICATION_STATE_INCONSISTENT、PLATFORM_APPLICATION_UNAVAILABLE。损坏/故障不转成空页或单项隐藏。所有响应与错误private,no-store，消息不回显输入、权限材料或底层原因。

## 业务规则

<a id="br-app-063"></a>
### BR-APP-063：平台应用发现的精确只读授权

平台目录与最小摘要只接受含app.application.search的可信ACTIVE USER。所有其他角色/权限不隐式授权，本权限不授予写入或owner私有配置读取。Auth是权限权威，App只按精确ID校验，授权先于输入/目标定位。

<a id="br-app-064"></a>
### BR-APP-064：全平台核心目录与过滤

所有Application生命周期、可用性与归档状态及未公开/未发布应用均可被本权限发现。过滤为ApplicationId、当前管理员opaque AuthId、技术名称前缀和三个独立状态维度的AND组合；空维度不过滤。仅披露读契约定义的核心摘要，不能沿目录读取下级私有资源或Auth资料。

<a id="br-app-065"></a>
### BR-APP-065：平台目录的有界签名分页

按nameKey/applicationId升序keyset，默认20最多100，扫描预算500。签名token绑定主体、用途、版本、规范过滤及末项位置；不跳过合法未返回项，允许短/空页继续，无offset/totalCount或跨页冻结。

<a id="br-app-066"></a>
### BR-APP-066：平台摘要快照与失败关闭

必要核心状态在同一majority只读snapshot校验并投影；当前摘要只表达本次观察，不构成操作授权。必要事实损坏整页/详情500，存储故障503，不隐藏损坏、不伪装为空。成功和错误private,no-store；非法请求/token、未知目标和授权失败依本UC稳定错误区分。

## 验收与依赖

覆盖none/search-only/suspend-only/restore-only/Reviewer/完整平台管理员无grant/owner等独立组合；按Auth实际授撤与签发证明权限边界。覆盖名称前缀、同名不同owner、精确ID/owner与状态组合、未公开/关闭应用、同key分页、篡改/换主体/过滤/用途、500扫描和空页继续、必要损坏/存储失败、读后状态变化及不能绕过其他入口。三协议与ADMIN/Developer surface隔离均需验收。

本UC在UC050完成后串行实现；Auth权限契约先就绪，App/API固定后按用户的API对齐→Gateway接入→固定本地镜像流程联合验证，再执行冻结完整backend；如共享Auth身份契约改变，补相应跨服务tier。用户搜索及Auth授权方案仍由Auth owner独立设计，不用本UC自批其语义。
