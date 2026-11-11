# 搜索与待接收转让查询补齐草案

状态：`ACCEPTED`。2026-11-08 用户接受草案并要求编写UC、串行实施，Auth部分明确交auth-center agent设计。App权威已落实为[UC050](../use-cases/UC-APP-050-query-incoming-application-admin-transfers.md)、[UC051](../use-cases/UC-APP-051-query-platform-application-directory.md)、UC026修订与读契约。本文保留接受时的范围；实现以权威UC/BR为准，Auth自身方案仍须其owner交审。

## 已核实的缺口

| 能力 | 当前正式能力与限制 | 本轮归属 |
| --- | --- | --- |
| 用户搜索 | Auth 有按 Auth ID 的账号/Developer/权限查询和平台管理员名单，没有通用用户搜索；管理员名单不能当作用户目录 | Auth owner 设计 UC、实现；App 不复制 Auth 用户目录 |
| 全平台应用搜索 | UC029 的 ListMyApplications/GetMyApplication 只允许当前管理员读取，UC024 是受运行资格约束的公开目录，均不能用于全平台治理 | App 新查询 UC；Auth 管理读取权限，Gateway/Console 分别接入 |
| 我的待接收转让 | UC026 已有六个正式方法，支持按 transferId 读详情及接受/拒绝；正文明确首期不提供列表 | App 新查询 UC，并修订 UC026 的列表排除条款 |

证据：App [UC026](../use-cases/UC-APP-026-transfer-application-administration.md#api-草图)、[UC029](../use-cases/UC-APP-029-query-owned-application-management.md#身份授权与存在性隐藏)，Console [UC014](../../console/use-cases/UC-CONSOLE-014-manage-application-ownership.md)、[UC015](../../console/use-cases/UC-CONSOLE-015-manage-platform-governance.md)。当前共享 API 只有转让的 Get/Initiate/Accept/Reject/Cancel 与 ListMyApplications/GetMyApplication，没有上述三个查询的正式方法。

本文只提出新增读取。转让接受、人员治理和应用运维继续走各自正式写入口，不因搜索命中而获得写权限。

## 一、我的待接收转让

建议新增 **UC-APP-050：查询我的待接收 Application 管理权转让**，引用 UC026 的状态、参与者、固定七天期限、资格与终态规则，不另建一套转让状态机。

### 身份与集合

- 可信 ACTIVE USER；查询自己时不额外要求当前为 APPROVED Developer，沿用现有参与者读取边界。接受仍由 UC026 的新鲜 Auth 状态及本地事务最终判定。
- 目标只能是可信调用者。请求不接收 toAuthId、fromAuthId、任意参与者、方向或状态过滤。
- 首期只列 `toAdminId = caller`、持久状态 PENDING、且 `expiresAt > asOf` 的入站申请；无记录返回成功空数组。
- 已取消、已拒绝、已接受和到期申请退出该列表。已知 transferId 的原详情读取继续可用，分享链接仍可使用。
- 不增加已读、未读、通知投递、出站列表或全量转让历史查询。

### 最小返回与一致性

```text
IncomingApplicationAdminTransferItem {
  transferId, applicationId, applicationName
  fromAuthId, toAuthId, status=PENDING
  requestedAt, expiresAt
}
IncomingApplicationAdminTransferPage { items[], nextPageToken?, asOf }
```

applicationName 取同一次 snapshot 中 Application 的技术名称，不依赖公开 Profile，不向 Auth 批量拉取人员资料。没有公开资料或尚未发布的应用也能呈现转让事项。不返回 secret、凭据摘要、配额或私有配置。

必要的申请/Application 绑定缺失或损坏时整页失败，不拼接占位名称或漏掉损坏申请。状态可以在返回后变化；点击进入详情、打开确认及提交前按原 UC026/Console UC014 重新读取，不把列表当作接受凭证。

列表使用一次只读一致 snapshot 和一个 App Clock 观察时间，不因翻页写入过期终态、账号 fence 或 Application revision。它通过期限条件排除逻辑上已到期的申请；UC026 的命令、详情 Get、owner-exit 检查及现有后台收敛仍按原规则持久化 EXPIRED。接受时恰逢到期、取消或账号退出的竞争规则不变。

按 `(requestedAt DESC, transferId DESC)` keyset 分页，pageSize 默认20、范围1–100。签名 token 绑定调用者、查询用途、版本和末项位置，换用户或损坏报400；不提供 offset/totalCount，不承诺跨页冻结。响应与错误均 `private, no-store`。

建议在现有 `ApplicationAdminTransferService` 增加：

| RPC | App 内部 HTTP | Gateway/Console |
| --- | --- | --- |
| ListIncomingApplicationAdminTransfers | POST `/v1/application-admin-transfers/incoming:search`，body=query | 强制 Session，沿用现有转让查询的协议与 Developer Console 接入策略，不增加 Admin 转让枚举入口 |

query 只包含 pageSize/pageToken；Gateway 外部路径增加 `/app-center`。需增加或调整目标+PENDING+稳定排序的有界查询索引，保留既有 owner-exit/过期索引。新增索引由显式 migration 建立，不做兼容别名或后台补数据。

### 对既有 UC 的待审修订

UC026 的“当前不提供列表”改为引用新增本人入站查询；明确新列表的只读期限过滤与原 Get/命令的持久过期收敛职责。UC026 的接受资格、权限、七天期限、KEEP/ROTATE、审计、终态和并发规则均继续为其唯一权威。

Console UC014 由 Console owner 增加“待接收转让”入口和真实分页，保留原链接详情路径和重新读取要求。App 不修改 Console UC 或前端源码。

## 二、管理员用户搜索：交 Auth owner 设计

用户已明确首期仅限平台人员治理，**不用于普通用户或 Developer 的转让对象选择器**，App 不新增用户搜索代理、Auth 数据镜像或邮箱转 Auth ID 的旁路。

建议交 Auth owner 的设计任务：

1. 明确新增或修订哪个 Auth UC，鉴权复用正式治理权限与在线复核边界；仅进入 Admin Console、具备 Reviewer 或 App 运维权均不自动获得用户目录读取权。
2. 首期支持通过已有 Auth ID、完整邮箱定位治理目标，返回可供正式治理查询使用的 opaque Auth ID；邮箱归一化、匹配范围、可查询账号状态和结果字段由 Auth 权威设计固定。昵称/邮箱片段模糊搜索、无条件浏览全量用户如有必要，须在该 UC 中明确接受，不能由前端临时扫描或拼表实现。
3. 返回最小目标标识、可用展示字段和必要账号/Developer 状态；不返回认证秘密、Session、设备、完整动态 Profile 或与治理无关的身份资料。若展示邮箱，明确其披露范围。
4. 固定有界输入、分页与排序、权限撤销后的行为、未知目标与损坏/依赖失败的区别、限流及 private/no-store。
5. 搜索结果不是写入授权或 OCC 基线。Console 选中目标后继续读取现有专用治理资源，再按其 revision、确认和服务端规则执行命令。

以上是需求交接，不是 App 对 Auth 规则的接受或实现授权。Auth owner 先给出权威 UC 与方案，按用户既定审核流程通过后才实现；本轮不修改Auth业务代码；用户接受后已通知Auth owner承接设计。

## 三、全平台 Application 搜索

建议新增 **UC-APP-051：查询平台 Application 管理目录与摘要**。独立于 UC029 当前管理员查询和 UC024 公开运行目录，面向治理定位，不复用或放宽它们的授权。

### 独立读取权限

建议新增精确原子权限 **`app.application.search`**，用于本 UC 的搜索及最小摘要读取。

- App audience 的可信 ACTIVE USER 必须含该精确 permission；权限由 Auth owner 设计独立授撤及本人有效权限发现，并签发到 App audience。
- 平台管理员、Reviewer、Developer、当前应用管理员、suspend/restore 权限均不隐式赋予该权限。搜索权限也不授予审核、暂停、恢复或 owner 私有详情读取权。
- Gateway 增加 ADMIN Console surface，强制 Session；不增加 Developer Console 全平台目录。域名与 surface 不代替 App 的精确授权。
- 权限签发、撤销传播和本人发现的准确语义须由 Auth UC 固定；不承诺离线 App USER JWS 在撤权瞬间失效。没有新权限时继续按已知 Application ID 使用各自原有入口。

此项是本草案需要审核的授权扩展，尚未添加权限、修改 Auth UC 或投影。

### 查询与投影

```text
SearchPlatformApplicationsQuery {
  applicationId?       // 精确定位，使用现有 ApplicationId 语法
  namePrefix?          // Application 技术名称前缀，按现有 nameKey 规则
  adminAuthId?         // 当前管理员的精确 opaque Auth ID
  lifecycleStatuses[]?
  platformAvailabilityStatuses[]?
  archiveStatuses[]?
  pageSize, pageToken?
}
PlatformApplicationSummary {
  applicationId, name, adminAuthId, createdAt
  ownershipRevision
  lifecycleStatus, lifecycleRevision
  platformAvailabilityStatus, platformAvailabilityRevision
  archiveStatus, archiveRevision
}
PlatformApplicationPage { items[], nextPageToken?, asOf }
```

各过滤条件 AND 组合；状态维度为空表示该维度不过滤，包含未发布、无公开 Profile、暂停、归档及关闭应用。空条件可分页浏览本权限范围内的全平台目录。非法/未知状态、ID、token 或超界参数返回400；鉴权先于参数和数据读取。

首期名称搜索针对 Application 技术名称，**不搜索公开资料展示名、描述、版本正文或任意人员资料**。不实现全文相关度排序。名称前缀长度沿用名称本身约束，不接受任意正则。

按 `(nameKey ASC, applicationId ASC)` 稳定 keyset 分页，pageSize 默认20、范围1–100。nameKey 只参与内部排序与 token，不作为响应字段。token 绑定调用者、查询用途、规范过滤条件、版本和末项位置。底层扫描预算500；不足一页或空页可附下一 token，不跳过未返回的合法项。无 offset/totalCount；每页独立 snapshot，不冻结跨页归属或状态。

只读取最小 Application 核心摘要，不逐项聚合 Version/Profile/Tester/OAuth，也不向 Auth 拉取管理员资料。必要数据损坏整页/详情失败；存储不可用报503，不伪装为空结果。不返回待审正文、Filter、凭据、历史人员理由或用户配置。

建议正式方法：

| RPC | App 内部 HTTP |
| --- | --- |
| SearchPlatformApplications | POST `/v1/platform/applications:search`，body=query |
| GetPlatformApplicationSummary | GET `/v1/platform/applications/{application_id}` |

两方法使用同一精确权限与投影。详情用于定位已知 ID 和重读选中项；未知目标404，必要事实损坏500、存储不可用503。缺身份401，缺精确权限403，均先于目标存在性查询。所有响应与错误 `private, no-store`，外部增加 `/app-center`，三协议保持同一语义。

Console UC015 的待审修订由 Console owner 承接：新增应用发现与选择，选择后走实际操作各自的专用读回/权限/双 revision 检查。目录中能看到一项不代表可执行该项操作，不以搜索摘要替代操作确认基线。

## 串行执行与验收

建议工作顺序：

1. 用户审核本草案。通过后写入两个 App 权威 UC、UC026 修订、读契约与 registry，生成各自实施 brief。候选编号以当时 registry 为准。
2. 先完成本人入站列表，复用现有身份与转让事实；App/API 实现及固定门禁关闭后再进入下一 App 工作包。
3. 由用户通知 Auth owner 承接管理员用户搜索和新 App 读取权限的 UC 设计，审核通过后由其实现。App agent 不改 Auth/Console/Gateway 业务源码。
4. Auth 权限签发契约就绪后实现 App 平台目录；沿用户既定 API 对齐→Gateway 接入→本地固定镜像→业务联验流程，Console 由其 owner 接入。

每个 App 实现包先串行专项，再冻结 App/API/已提交 docs 输入执行 Go1.25.5 完整 backend 门禁；跨服务依赖使用固定镜像另行验收，准确区分证据范围。新增 App API 按现有分工和用户届时授权提交输入/生成物，不自动 push、上线或操作现存用户数据。

必须覆盖：本人/非本人、资格变化后只读、逻辑过期与后台收敛、取消/接受/关闭并发、同时间分页及游标绑定、损坏整页失败、无公开资料的待转让应用；平台目录四种以上独立角色组合、精确授权及撤权边界、未发布/关闭应用可见、三种状态正交、前缀/同名/管理员过滤、扫描预算、读后状态变化和每个写入口的独立拒绝。搜索和列表不会自动接受转让、授予权限或发起运维。

本次审核仅覆盖 App 两个新查询及 UC026 修订方向，以及交 Auth/Console owner 的需求边界。Auth 用户搜索的具体权威规则和权限管理方案仍由 Auth owner 单独交审。App先从UC050开始；实施与门禁状态另记。
