# Console 搜索与待接收转让：UC014/015 修订草案

状态：`ACCEPTED`，2026-11-08。用户明确答复“接受，交 Console owner 更新 UC 并串行实现”。据此更新 UC014/015、必要导航与实施计划，随后本地串行实施和检查；不授权推送或部署。本文规定拟增加的页面结构和功能，不规定视觉样式。App/Auth 的设计接受与后端完成不等于本 Console 修订已接受。

## 依据与拟修订范围

| 拟修订项 | 后端权威 | Console 修订内容 |
| --- | --- | --- |
| [UC014](../use-cases/UC-CONSOLE-014-manage-application-ownership.md) | [App UC050 / BR-APP-059–062](../../app-center/use-cases/UC-APP-050-query-incoming-application-admin-transfers.md)、[本人入站读契约](../../app-center/query-contracts/incoming-application-transfers.md) | 增加本人待接收列表，沿用参与者详情和原接受/拒绝流程 |
| UC014 的命令与凭据 | [App UC026](../../app-center/use-cases/UC-APP-026-transfer-application-administration.md) | 保留接受资格、KEEP/ROTATE、一次性 Secret 和未知结果恢复，不增加转让对象搜索 |
| [UC015](../use-cases/UC-CONSOLE-015-manage-platform-governance.md) 的应用发现 | [App UC051 / BR-APP-063–066](../../app-center/use-cases/UC-APP-051-query-platform-application-directory.md)、[平台目录读契约](../../app-center/query-contracts/platform-application-directory.md) | 增加独立只读目录和最小摘要，再连接已有专用运维读取 |
| UC015 的权限发现与管理 | [Auth UC027 / BR-AOP-001–008](../../auth-center/use-cases/UC-AUTH-027-manage-application-operations-permissions.md)、[UC010 / BR-IDN-002](../../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002) | 识别独立 search 权限，管理投影由两项变为三项，人员治理和 App 动作继续独立 |
| UC015 的人员定位 | [Auth UC039 / BR-USR-001–005](../../auth-center/use-cases/UC-AUTH-039-search-users-for-administration.md) | 仅完整平台管理员精确定位治理目标，不创建用户目录浏览或 Developer 选择器 |
| 共享私有读取 | [Console UC002 / BR-CMG-001–004](../use-cases/UC-CONSOLE-002-query-owned-applications.md#br-cmg-001)、[私有读取边界](../query-contracts/private-read-boundary.md) | 绑定 Session/attempt/Query 实例，区分权限拒绝、协议错误、暂时失败和成功空集合 |

本轮只拟修订 UC014/015 及其接受后必要的导航、能力边界和验收描述，不扩展爬虫页面。后端规则以所链接 UC 为准；下文是 Console 消费安排，不创建第二份业务规则。

## UC014：本人待接收转让

### 页面入口和可达性

建议 Developer 的账号菜单提供“待接收转让”，进入独立整页 `/application-transfers`。它与已有 `/application-transfers/:transferId` 并列，不放在应用切换侧栏或某一应用的管理权门禁内。

入口只依赖 Developer Console 当前会话，不要求当前为 APPROVED Developer、不要求已有应用或能读取“我的应用”。未申请、待审核、暂停或已退出 Developer 的 ACTIVE USER 仍能访问本人列表。是否可接受由原详情及命令最终判定。

保留用户手中的 transferId 分享链接；没有列表入口、不在当前页或事项已退出待接收列表，都不使参与者详情链接失效。未登录时使用既有登录/恢复流程，不自动申请 Developer 或创建应用。

### 列表与分页

- 正式调用 `ListIncomingApplicationAdminTransfers`，外部 HTTP 为 `POST /app-center/v1/application-admin-transfers/incoming:search`。请求体是 annotation 所指定的 query 本身，仅传 `pageSize`、`pageToken`；不包一层 `query`，不传本人 Auth ID、方向或状态。
- 首版每页 20 项，使用服务端 token 明确加载下一页和重新读取第一页。按服务端顺序显示，不本地重排、不自动扫完全部页、不显示推算总数或未读数。刷新重建本次分页链，换 Session 丢弃全部旧页和 token。
- 每项仅展示应用技术名称/ID、发起者 Auth ID、申请及到期时间；transferId 用于详情导航。只消费该次 `asOf` 下的本人 PENDING 未到期集合，不拉取 Auth 资料补姓名、邮箱或头像。
- 成功空数组显示“当前没有待接收转让”。查询失败明确显示无法读取，不能显示为空；协议错误或身份/权限拒绝先移除对应私有内容。暂时故障保留的同上下文旧页必须标明原读取时间，并允许明确重读。
- 到期时间只作说明，不用浏览器时钟删除事项、改写 EXPIRED 或开放/关闭接受按钮；已退出列表的事项仍可通过原链接由正式详情解释当前状态。

### 选择与操作

点击事项只携带 transferId 进入原整页详情，重新调用 `GetApplicationAdminTransfer`。列表项不充当接受、拒绝、KEEP/ROTATE 或 Secret 披露的基线。

建议在打开动作确认及实际提交前，分别重读同一转让详情。若参与者、应用、状态或原命令需要的前置事实改变，清掉旧确认与选择，先解释最新事实；不沿用旧列表的 PENDING。原命令仍负责资格、到期和并发判定。

接受/拒绝明确完成后，沿原 UC014 先读回转让事实；返回列表时重新读取第一页，不将客户端删除行当作业务成功证据。未知结果只做原只读核对，不自动接受/拒绝。KEEP/ROTATE 必须明确选择，一次性 Secret 的内存、隐藏和离页清除边界继续沿用 UC014。

发起转让的目标仍手填已有 opaque Auth ID。本次不把 Auth 搜索加入 Developer、不提供邮箱转 Auth ID 的旁路、不发送通知。

## UC015：平台应用发现

### 页面组织和能力发现

建议在 Admin 已有 `/governance/applications` 页面增加“查找应用”分区，与按已知 Application ID 读取运维状态并列。目录筛选和结果占据页面主要区域；选择应用后在独立目标区读取摘要或运维状态，不层层堆叠应用内部配置。

使用既有 `GetOwnApplicationOperationsPermissions`，独立识别 `app.application.search`、`app.application.suspend`、`app.application.restore`。本人结果必须严格匹配当前主体及合法正数版本，完整集合只在当前私有页面内存消费。搜索能力不以前置平台管理员查询成功为条件。

| 本次明确本人观察 | 可用入口 |
| --- | --- |
| 只有 search | 平台目录与最小摘要；没有暂停/恢复动作 |
| 只有 suspend 或 restore | 按已知 ID 调用原运维专用读取；没有平台目录 |
| search 与任一运维权 | 目录定位，然后独立进入所获运维动作 |
| 完整平台管理员、Reviewer、Developer 或 owner，无 search grant | 不因其身份开放平台目录 |
| 成功空集合 | 不开放目录或 App 写动作；不影响独立人员治理/Reviewer，原已知 ID 读取仍由其服务鉴权 |
| 本人读取失败 | 提示无法确认；不把失败当空集合、不以旧权限开放搜索/写入、不回退管理员查询或写请求探权 |

当前 UC015 的“空集合/无暂停恢复权关闭 App 目标范围”需区分目录和运维两种范围：search-only 必须保留目录。管理他人应用权限的资源也须按 Auth 新三项完整集合严格消费并分别提供授撤，不能继续要求恰好两项，亦不能把新 search 项当成 restore。授撤和原动作各自重新读取并确认其专用 revision。

### 查询、列表和最小摘要

调用 `SearchPlatformApplications`，外部 HTTP 为 `POST /app-center/v1/platform/applications:search`，正文是 query。首版由用户明确提交查询，也允许明确点击查看未加筛选的目录；不在未确认能力前预取。

筛选提供精确 Application ID、技术名称前缀、当前 owner 的完整 Auth ID，以及生命周期、平台可用性、归档三个独立状态维度。维度为空表示该维度不限；组合含义引用 UC051。不提供公开 Profile 名称全文搜索、相关度排序、任意正则或人员模糊搜索。

结果仅显示技术名称/ID、owner Auth ID、创建时间和三个独立状态。后台版本用于解析和保护，不作为普通用户提示，也不允许编辑。选择已知 ID 或结果后，可用 `GetPlatformApplicationSummary` 重新读取相同最小投影；这个摘要不包含私有子资源或任何写命令授权。

每页 20 项，沿服务端 token 与顺序明确续读；空页但有 token 时显示“本页没有符合项，可继续”，保持下一页可用，不自动判断搜索结束。没有 token 才说明本次分页链已结束；不推算总数。改变筛选、重新搜索或刷新回到第一页，原 token 不用于另一个主体或筛选。每页保留自己的 `asOf`，不冒充跨页同一快照。

App 损坏/不可用不能转换为空列表或跳过某条。状态和归属在翻页后变化属于新观察，不由浏览器拼接 owner 私有应用列表、公开目录或审核队列“修复”全平台结果。

### 从发现进入原运维流程

选中目录项不创建写确认。若当前已明确拥有相应运维权，进入原 `GetApplicationPlatformAvailability` 取得最新目标状态及双 revision；确认前和提交前仍分别重读本人权限与目标，引用 UC015 现有语义。目录里的 ownership/archive/lifecycle 等版本均不能替代专用命令基线。

search-only 不尝试运维读取来探权，也不开放 owner 配置。没有 search 的独立运维人员继续用已知 Application ID，不强制授予目录权。搜索撤权只退场目录/摘要；运维动作、人员治理和 Reviewer 按各自观察独立处理。同一共享 permissionRevision 的变化须使旧确认重新核对，不能据版本变化猜是哪项授权改变。

## UC015：平台人员精确定位

建议在已有 `/governance/personnel` 的目标输入区域增加“按 Auth ID / 按完整邮箱”两种明确方式。它只服务当前页面的人员治理选择；既有已知 Auth ID 专用读取保留，不增设全用户浏览页面。

只有本次已确认完整平台管理员资格才发起 `SearchUsers`；服务端仍在线复核。Reviewer、App search/运维人员以及 Developer 没有用户目录入口。管理者能授予 search 不代表自己拥有 App search，人员目录与应用目录的失败处理独立。

外部 HTTP 为 `POST /auth-center/v1/managed-users:search`，正文只包含一个 selector：`authId` 或 `email`。完整邮箱仅放 POST 正文；不放 URL/search 参数、持久存储或遥测，不在 Query key 内使用邮箱原值。输入只在当前表单内存保留，换 Session、离页或人员治理拒绝时清掉。

Auth ID 原值提交，不 trim/改大小写后悄悄定位另一个主体。邮箱规范化由 Auth UC039/UC011 决定，不在前端另写模糊匹配或剥离点号、+tag。切换 selector、修改输入或重新提交会清除旧结果、所选治理目标及未提交确认；旧响应不能恢复它们。

正式结果只接受零项或一项，展示 Auth ID、账号状态、nullable Developer 状态和读取时间；null 表示尚未申请，不显示为错误或已拒绝。没有分页、排序、总数或自动联想。零项提示“没有匹配的可治理账号”，不判定邮箱从未使用或账号不存在。

选中后以返回 Auth ID 重新调用当前治理模块的专用 Get，再展示状态、确认及正式命令。搜索摘要没有 OCC revision；不能拿搜索的状态直接禁用、恢复、授权或撤权。该邮箱后来换绑也不能把已有的所选 Auth ID 偷换为另一个账号；再次搜索必须明确重新选择。

## 读取失效、缓存与隐私

三类发现分别使用 Session/attempt/查询输入代际，分页和详情绑定原 Query 实例；重复同 key 的新对象、输入变更、新 Session 或较新数据不能被迟到成功/拒绝覆盖。

业务 401/403 仅按对应能力退场，明确 Session 失效沿现有跨私有页恢复。search 403 不撤销 App suspend/restore；人员搜索拒绝不删除 Reviewer 或本人 App 能力；入站列表不要求 owner 数据成功。协议错误移除当前不可用投影；网络/5xx 的保留仅限同上下文带原读取时间，不能沿旧搜索摘要开启新写入。

成功和错误必须验证 `private, no-store`。Query 数据只保留本次私有读取需要的最小投影，不进入浏览器持久状态、日志或公开遥测；不聚合 Auth Profile、不暴露邮箱、JWS 或 Secret。正常页面不展示技术 revision、cursor 内容或权限签发细节。

## 已接受的验收范围

| 范围 | 关键验收 |
| --- | --- |
| UC014 可达性 | 无应用的普通 ACTIVE USER，以及非 APPROVED Developer 可查本人列表；不能自报身份或读取他人入站事项；原详情链接仍可用 |
| UC014 集合/分页 | 本人有效 PENDING、空数组、同时间排序、分页和刷新；到期及取消/接受后的旧页不能触发旧确认；失败不伪装无事项 |
| UC014 命令复用 | 点击/确认/提交均走正式详情与原命令；KEEP/ROTATE 无默认、Secret 只披露一次、未知不重放和终态读回不退步 |
| App 授权组合 | none、search-only、suspend-only、restore-only、search+动作、完整管理员无 grant、Reviewer、owner；同 Session 正式授撤后观察变化 |
| App 查询 | 技术前缀、同名不同 owner、精确 ID/owner、三个状态的 AND；未公开和关闭项；空页可继续，不本地扫表或推算总数 |
| 发现与写入隔离 | 选择目录项/人员摘要后先读专用资源；权限或目标版本变化使确认失效；search-only 不发写入；旧页不绕过原服务判定 |
| 人员定位 | 两种 selector、零/一项、nullable Developer、DISABLED；邮箱遵循 Auth 精确规则；无前缀/模糊匹配/分页，不把用户搜索用于转让 |
| 并发和私有读取 | 换输入/筛选/目标/Session、同 key 新 Query、旧成功/403/ACK；清掉本次范围而不误清独立能力；错误和响应头保持真实分类 |
| 分层证据 | 客户端/组件先验消费保护；实际 Auth 授撤、原 Console Cookie/ForwardAuth、原 App 命令及读回走独立真实链；后端三镜像成功不代替 React 验收 |

## 权威冲突与建议

| authority / conflict | options | suggested |
| --- | --- | --- |
| Console UC014 仍写“无列表”，App UC050 已接受本人列表 | 保留只通过链接；或接受本草案后增加独立本人入口 | 后者；只替代“无入站列表”的限制，手填转让目标/分享链接和原命令继续保留 |
| Console UC015 排除用户/平台搜索，App UC051 与 Auth UC039 已接受新增读取 | 把后端完成视作 Console 已接受；或本草案另交用户接受再改 UC | 后者；不依据旧 Goal 的自主接受授权覆盖这次明确待审流程 |
| Console 本人运维消费只认识两项，Auth UC027 已增加 search，旧目标权限严格解码亦假定两项 | 将 search 混入 suspend/restore；或分离 search 发现范围并更新三项完整管理资源 | 后者；三种权限分别授权，不对 search-only 误显示“没有任何 App 能力”或清掉目录 |
| 平台 App 搜索可返回 owner Auth ID，但 Auth 只允许完整管理员查人员 | 自动补查邮箱/Profile；或只显示 opaque ID | 后者；目录筛选 owner 仍手填精确 ID，不给独立 App 搜索者用户目录权 |

## 交付依赖和已接受安排

设计输入为 App/API 本地交接 `fb8d9de` / `a57bb96`、Gateway `9de4e70`，Auth 本地业务指纹 `6e680a1e5700`。这是输入说明，不表示已发布。App UC050/051 均已给出完整 backend 24/24 和三镜像证据；UC051 最终 App 为 3c611d9，生产业务源码与 fb8d9de 相同。该后端证据不替代 React 验收。

接受并实现前需固定可消费 API、官方生成客户端、核对三条新增查询的 Console surface；联调环境还需 Auth 用户搜索与原能力读取开关及真实授权就绪。默认已发布 latest 不含这些新入口，不据本地镜像存在宣称线上可用，不因本草案推送、部署或重建用户数据库。

用户已接受以下 Console 产品安排；前文建议语气保留为设计形成记录，交付状态另记：

1. 本人“待接收转让”放 Developer 账号菜单，使用独立整页，不依赖当前应用或 Developer 批准状态。
2. 平台应用搜索放现有 Admin 应用运维页；独立目录与最小摘要，保留无 search 时按已知 ID 运维的入口。
3. 用户精确查找放 Admin 人员治理的目标区域，不建全用户目录，不用于 Developer 转让对象选择。
4. 先更新 UC014/015 和必要导航、能力边界、实施计划，再按待接收列表 → 应用目录 → 人员精确查找串行实现。

## 接受后权威位置

Console 交互以更新后的 UC014/015 为准；本提案保留形成记录，不作为第二权威。串行工作输入与证据见 [实施工作包](../implements/2026-11-08-search-and-incoming-transfer.md)。
