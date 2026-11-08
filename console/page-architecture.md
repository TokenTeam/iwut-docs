# Console 页面结构规划

状态：Developer 结构 `ACCEPTED / ITERATING`，2026-10-27；2026-10-30按持续goal授权补充UC015 Admin治理职责。用户接受先建立文档与初版、再通过使用调整结构。功能文档只规定结构、职责与交互语义，不锁定布局；原型验证发现功能结构不合理时同步修订，不要求视觉设计先完整文档化。本轮实施边界见 [UC008](use-cases/UC-CONSOLE-008-version-workspace.md)及[UC015](use-cases/UC-CONSOLE-015-manage-platform-governance.md)。

Console 应围绕用户任务组织，而不是把 App Center 的资源路径逐层翻译成页面。建议采用“全局工作区 + 当前应用工作区”，应用内各模块平级切换；版本配置在同一版本工作页完成，不再继续钻入配置子页面。本规划只定义功能组织与信息层级，不规定具体样式。

## 结构依据与交付边界

2026-10-30 更新：Gateway9d6a27f已交付所列普通P0/P1 Console路由。UC009应用创建、UC008版本写入/送审、UC010资料写入/送审，以及UC011–013测试/OAuth/Filter已有[代表性真实页面证据](implements/2026-10-30-developer-management-writes.md)，不能扩大为旧128全量重新通过。UC014归档/转让已接线、独立实链验收中；UC015治理在实施，Admin布局仍由后续试用迭代。账号与特殊凭据编排未因普通路由补齐而完成。

业务语义以 [App Center 用例](../app-center/README.md)及下文具体 UC 为准；API 输入固定为 [iwut-api-proto 6fea3db](https://github.com/TokenTeam/iwut-api-proto/tree/6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6/app_center/v1)。Gateway 依据[当前 routes.v3](https://github.com/TokenTeam/iwut-gateway/blob/master/config/routes.v3.yaml)核对；正式实施时重新验证发布镜像，不能仅凭 Proto 存在认定浏览器可调用。

区分三个层次：App 已有 RPC，不等于已开放对应 Console surface；已开放 surface，也不等于页面已实现。当前 Developer 管理读取与 Admin 两类审核已接入；本规划中的 Developer 写入、发布、OAuth、Filter、转让和关闭仍须各自 Console UC、最小 API 生成子集、精确 Gateway 路由与真实验收。不得改走非 Console Gateway、浏览器 Session header 或数据库来绕过缺口。

## Developer 导航

```text
吾理开放平台
├─ 应用                             默认平台栏目，不另设首页
│  ├─ 应用切换                      持续可用的应用列表与选中状态
│  ├─ 全部应用与筛选                保留完整列表入口
│  └─ 当前应用工作区                 进入应用后仍可直接切换其他应用
│     ├─ 概览
│     ├─ 版本与发布                   三个发布槽位、版本列表 → 版本工作页
│     ├─ 测试配置                     应用级测试成员与邀请链接
│     ├─ 公开资料                     当前公开资料、工作修订、历史
│     ├─ 接入配置                     OAuth 客户端
│     ├─ 展示规则                     应用级 Filter 独立编排空间
│     └─ 应用设置                     技术信息、归档、管理权转让、关闭
├─ 爬虫配置                         平台级栏目；目前只说明尚未建设
└─ 全局账号入口                     独立于当前应用及 Developer 资格
   ├─ 本人资料                      /account/profile，UC016
   ├─ 开发者资格                    /account/developer，UC018，仅 Developer Console
   ├─ 待接收转让                    /application-transfers，UC014，不依赖当前应用或Developer批准
   └─ 退出此工作台                  UC017，明确确认后结束当前会话
```

上图是产品区域，不要求每个分组都对应一个新 URL。应用上下文作为可复用布局，与全局布局分离；登录入口不充当登录后的工作台。现有深链接保留可达性，调整页面结构时不要求用户重新逐层进入。

2026-10-27 用户试用后的外层修订：平台导航与应用切换从进入前就保持一致，选择一个应用只替换当前应用内容，不再像从小卡片进入另一套后台。应用切换列表支持紧凑与详细两种表达，详细态提供名称和管理摘要，当前应用明确标记。两态均可滚动，只通过显式按钮展开/收起，不随悬浮、离开或失焦自动切换。

按用户后续简化，两态保持原生滚动，不再使用展开动画、位置补偿、占位空白或日常滚动强制边界校正。展开或选择应用后仅尝试把已加载目标滚入可见区域；当前应用不在已加载列表时取可见项，不无限查找页外数据。选择应用后收起；未选择应用而直接收起（含 Escape）时恢复原紧凑列表滚动位置。具体呈现继续通过原型调整。应用内模块与平台栏目分层，切换应用继续适用未保存离页提示。

应用切换复用 `ListMyApplications` 默认范围和显式游标加载，不受当前内容区筛选影响；不为了寻找一个页外当前应用无限自动翻页。列表绑定会话代际、独立读取时间，失效后清理，不以常驻导航保留旧权限下的私有名称。爬虫配置没有设计/API，仅显示规划说明，不发明设置项或调用。

| 页面或区域 | 用户任务与主信息 | 操作规划与 API 依据 | 当前接入状态 |
| --- | --- | --- | --- |
| 我的应用 `/applications` | 找到应用；默认名称、生命周期、平台可用性、待审核计数，归档状态独立筛选 | `ListMyApplications`；创建用 `CreateApplication`，只输入技术名称，不冒充公开名称。[UC029](../app-center/use-cases/UC-APP-029-query-owned-application-management.md)、[UC001](../app-center/use-cases/UC-APP-001-create-application.md) | 列表及创建页已实现；UC009真实创建成功链通过，技术名称不冒充公开名称 |
| 概览 `/applications/:appId` | 看应用当前进展与下一步；分别展示版本审核、公开资料、发布和测试摘要，以明确入口进入模块 | `GetMyApplication`；使用其 counts、profileState、publications、oauthRegistrations 等摘要，不逐行展开整个响应 | 读取已实现；这里规划的是重新组织信息，不新增“全球统计”或无限聚合请求 |
| 版本与发布 `…/versions` | 按 RPC major 看正式、灰度、测试槽位；查看全部版本、筛选审核状态和新建版本 | 复用 UC002 的独立 Publication 摘要和 UC003 的版本查询，不合成跨 RPC 原子快照 | 三个槽位始终展开，点击卡片打开发布浮窗；版本列表固定服务端顺序，详见 UC008 |
| 单个版本 `…/versions/:versionId` | 在同一工作页看内容、编辑声明并理解审核结果 | 内容分为基本入口、运行兼容性、权限与 Scope、OAuth redirects、最新审核；编辑使用同页分区或可深链接标签，不再增加“Version config → 每个字段”页面 | 不以一个大表单同时保存独立领域；当前内容、最新 Review 与发布状态仍明确分开 |
| 公开资料 `…/profile-revisions` | 看“现在公开的是什么”和“正在修改哪份”；当前公开与工作修订置前，历史次之 | `ListApplicationProfileRevisions` / `GetApplicationProfileRevision`；创建、草稿修改、提交见 [UC013–015](../app-center/use-cases/UC-APP-013-create-application-profile-revision.md)；单工作修订规则仍由 App 拥有 | 查询与UC010完整草稿/保存/送审已接入且代表实链通过；拒绝后基于原内容新建修订继续补齐，不修改旧REJECTED对象 |
| 发布区域，包含在 `…/versions` | 正式、灰度、测试是可为空、可指向相同版本的三个槽位，不是版本审核状态；点击卡片在短浮窗中选择版本、查看基本信息和跳转版本工作页，测试管理为同级选项卡 | [UC007](../app-center/use-cases/UC-APP-007-place-approved-version-in-test-slot.md)、[UC020–021](../app-center/use-cases/UC-APP-020-manage-stable-publication-slot.md)、[UC036](../app-center/use-cases/UC-APP-036-clear-test-publication-slot.md) | 六条发布命令已接入；保留共享修订、确认、冲突及未知恢复，真实发布成功链仍待验证，不伪造发布历史 |
| 测试管理 `…/testers` | 看容量与参与成员，管理可用邀请；成员和链接记录各自筛选分页 | `GetApplicationTesterManagement`、`ListApplicationTesterMemberships`、`ListApplicationTesterJoinLinks`；创建/轮换/撤销链接、移除成员见 [UC008–011](../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)、[UC037](../app-center/use-cases/UC-APP-037-query-application-tester-management.md) | 三个读取区域与UC011创建/轮换/撤销/成员移除已接入，代表写链通过；秘密仅一次披露，不从历史记录恢复 |
| 接入配置 `…/integration` | 独立管理各分发环境 OAuth 客户端和凭证元数据 | [UC018](../app-center/use-cases/UC-APP-018-manage-oauth-client.md)；不把版本化 redirects 混同客户端凭证 | UC012使用独立登记/凭据查询与登记/启停/轮换命令；三渠道共用组件，代表写链通过，秘密仅一次披露 |
| 展示规则 `…/display-rules` | 独立全页编排公开展示 Filter，不挤在接入或版本表单中 | [UC022](../app-center/use-cases/UC-APP-022-manage-application-filter.md)；应用级、即时生效、不送审，仅影响 GREY/STABLE 展示而非 TEST，也不构成访问授权 | UC013完整树/字段目录/本地编排/发布清空已接入，设置清空代表实链通过；不是用户资料读取或求值服务 |
| 应用设置 `…/settings` | 查看技术身份、整理应用、处理管理权与终止使用 | `GetApplicationArchiveState` / Archive / Unarchive；Ownership / Initiate / Get / Accept / Reject / Cancel transfer；ClosurePreview / Close / Closure，见 [UC026](../app-center/use-cases/UC-APP-026-transfer-application-administration.md)、[UC027](../app-center/use-cases/UC-APP-027-close-application.md)、[UC033](../app-center/use-cases/UC-APP-033-archive-and-unarchive-application.md) | UC014归档/所有权专用读取及归档/转让已接线，真实验收中；关闭仍只读摘要，实际关闭需独立Auth近期认证和proof |

当前查询按不透明 cursor 翻页，不改为猜测总数的数字分页。若选择的版本已在当前页，展示版本标签；仅有 ID 的槽位摘要必须标为引用，不拿当前页猜标签或做无界补查。不存在的字段和跨应用统计不以占位数字冒充。

管理权转让接受/拒绝先作为已知 transfer 深链接流程，不先做“所有待处理转让”收件箱：当前没有查询我收到的转让列表 API。App 的 `adminId` 是应用管理关系，不是平台管理员角色。

## 单个应用内的导航与引导

各模块共享固定应用上下文和同级导航。版本详情可直接进入同应用的概览、公开资料等已交付模块，不必逐层返回。测试管理 `/applications/:appId/testers` 从“测试配置”同级选项卡进入，成员和链接仍属于应用，不属于某个版本或 major，切换 TEST 不重置它们。概览与版本页的三个发布槽位始终展开；发布操作只在版本与发布页明确进行，见 UC008 的发布增量。面包屑用于定位，不是唯一导航；未实现模块不显示假链接。换身份、换应用或筛选条件仍重置私有分页。

版本工作页的配置区只是同一资源的不同视角。`/versions/:versionId?section=permissions` 可作为分区深链接示例；它不是新领域对象、权限来源或前端持久状态。独立查询仍保留各自 `asOf`，不拼成不存在的跨 RPC 原子快照。

引导按实际事实给出下一动作：DRAFT 提示编辑与提交；SUBMITTED 等待审核；REJECTED 展示原因和明确恢复路径；APPROVED 提示“审核通过，尚不等于发布”。写能力未接通时明确说明依赖，不显示可成功执行的假按钮。公开资料按真实 currentPublished 指针展示。多重状态分别表达，不用一个红绿灯覆盖生命周期、平台可用性与归档状态。

## 复用的版本工作页

新建 `/applications/:appId/versions/new` 和已有 `/applications/:appId/versions/:versionId` 共用整页内容结构：基本入口、兼容性、能力与 Scope、OAuth 回调、审核信息。大量编辑不用浮窗。新建、可编辑 DRAFT、只读终态是同一工作页的不同模式，不能因共用组件混淆资源是否已经存在。

新建时内容只留当前页面内存；必填有效后由用户明确创建完整草稿，成功后替换 URL 进入已有资源。已有 DRAFT 的有效完整快照防抖串行保存，使用后端 revision 并发前置值；无效中间值不提交，迟到响应不能覆盖继续输入。失败、冲突、结果未知均不能显示为已保存或自动重放。

新建提供“清空填写”；已有草稿提供“还原至本次打开时”，后者在自动保存后可能是真实写入，需确认且保留并发检查，不是服务端历史回滚。REJECTED 的“恢复为草稿”是另一独立业务命令。未保存或结果未知时离页提示，不能依赖卸载时发送保存；不将私有表单默认持久化到 localStorage。

## Admin 导航

```text
吾理平台管理
├─ 审核工作区
│  ├─ 版本审核队列 → 审核工作页
│  └─ 资料审核队列 → 审核工作页
├─ 平台治理                         UC015独立入口，与Reviewer权限隔离
│  ├─ 应用可用性                    已知 Application ID 的暂停与恢复
│  └─ 人员与审核权限                属于 Auth 的独立功能
└─ 全局账号入口                     不要求 Reviewer 或平台管理员资格
   ├─ 本人资料                      /account/profile，UC016
   └─ 退出此工作台                  UC017
```

审核工作页直接从队列进入，不先经过 Application 管理详情。两个队列保留独立精确权限，不把“登录 Admin”解释成拥有两项权限，也不要求 Reviewer 先取得 Developer 资格。

| 区域 | 页面组织 | API 与边界 |
| --- | --- | --- |
| 版本审核 | 队列显示应用名称、版本标签、提交时间和利益冲突提示；工作页依次组织提交内容、当前资格/策略、必要检查项、决定；当前对象和技术详情次之 | `ListPendingApplicationVersionReviews`、`GetApplicationVersionReview`、`DecideApplicationVersionReview` 已有 ADMIN surface/UI。待办队列不是“所有审核历史”列表 |
| 资料审核 | 队列显示应用名称、送审公开名称和提交时间；工作页对照送审内容与当前公开资料，呈现可理解的变更和必要检查 | `ListPendingApplicationProfileReviews`、`GetApplicationProfileReview`、`DecideApplicationProfileRevisionReview` 已有 ADMIN surface/UI；只用返回的 currentPublished 指针/内容，不补查 Developer 私有管理 API |
| 应用可用性 | 按已知应用 ID 精确进入，明确暂停原因、当前状态和恢复影响 | UC015使用 `GetApplicationPlatformAvailability`、`SuspendApplication`、`RestoreApplication` 已有ADMIN surface。权限与审核权限不同；独立运维具体权限无法自查时仅保留状态读取，不猜写。没有全平台应用搜索，不伪造全量表格 |
| 人员与权限治理 | 与审核执行分区，平台管理员列表或已知Auth ID定位；账号状态、Developer资格及独立权限分别读取/处理 | UC015接入现有Auth治理API与ADMIN surface，不发明用户搜索/角色目录；平台管理员资格及各前置版本仍以后端权威为准，治理失权不撤销独立Reviewer能力 |

批准/拒绝始终是审核任务内明确动作，确认阶段绑定原 Review、snapshot、策略和所需前置值。字段可以调整主次，但不能隐藏影响决定的冲突、系统拒绝、策略变化、公开指针或结果未知状态；不因换组件移除逐项检查或自动重放决定。

## 信息层级与字段取舍

| 信息类别 | 默认展示 | 次级展示或按需读取 |
| --- | --- | --- |
| 识别与进度 | 名称、版本标签、用户可理解的状态、必要时间、下一步 | 稳定 ID 放技术详情；需要配置 OAuth 时 clientId 是主信息，不一概隐藏全部 ID |
| 内容与配置 | 与本任务相关的内容；编辑时显示可编辑字段、约束和错误 | 原始 launch URL / redirect / Scope 声明保持准确，按区展示；非当前任务不整页铺开 |
| 并发与诊断 | 冲突/过期/读取失败说明及明确恢复操作 | revision、epoch、内部引用按需展开；客户端仍完整保留命令所需前置值，不让用户手填 |
| 审核依据 | 送审 snapshot、当前决定资格、策略/检查要求、决定原因 | 历史决定、恢复记录和技术引用分组；“提交时”与“当前”不能因折叠而混淆 |
| 敏感材料 | 仅在相应明确操作成功时一次展示所需 secret/邀请 URL | 不进 Query 持久缓存、日志、URL 或历史页，不根据已有元数据恢复秘密 |

不再默认逐字段映射 DTO，但也不把“技术字段”当作删除校验的理由。description/icon/launch URL 等现阶段继续按已接受的惰性文本边界处理；新增富文本、图片加载或可执行外链须另作安全设计，不混进组件替换。

## 首版与后续迭代

1. 本轮接入 HeroUI 基础组件与双端样式，保持现有业务和路由；验证禁用、表单提交、键盘、焦点和真实页面加载。
2. 实现可复用应用导航、版本与发布工作台、新建与版本工作页，先在初版中检验信息结构，按 UC008 登记命令接入边界。
3. 继续补 Developer 完整任务闭环：创建应用 → 创建/编辑版本与公开资料 → 提交 → Admin 审核 → Developer 读回结果。每包补精确 surface 和验收。
4. 再补发布与测试管理操作；OAuth/Filter 和归档/转让/关闭按独立工作包逐步引入。后端没有通用 DeleteApplication，因此不以凑齐 CRUD 为由增加删除按钮。

暂定导航顺序已接受；具体布局通过初版调整，必要时同步修订结构文档。后端规则、密码/设备治理和 Tester 本人客户端不由本规划自动授权。

## 2026-11-08 已接受的发现入口

Developer账号入口新增本人待接收转让整页；Admin应用运维增加精确权限保护的应用目录，人员治理增加完整管理员专用的Auth ID/邮箱精确查找。目录和搜索只定位，选择后先读原专用资源再确认写入。功能与验收以[UC014](use-cases/UC-CONSOLE-014-manage-application-ownership.md)、[UC015](use-cases/UC-CONSOLE-015-manage-platform-governance.md)为准，交付状态另记；不扩展爬虫页面。
