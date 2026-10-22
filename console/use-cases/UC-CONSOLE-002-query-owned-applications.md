# UC-CONSOLE-002：查询我的 Application 管理概览

状态：`ACCEPTED`

接受日期：2026-10-15

## 用户目标与范围

已建立 Developer Console Session 的用户查看自己当前管理的 Application，进入一个 Application 的只读管理概览，并导航到 Version、ProfileRevision 和 Tester 管理查询。当前管理关系由 App 判定，登录成功或 Developer 身份不代替管理授权。

本提案只增加管理读取与导航；不提供创建、编辑、提交、发布、转让、关闭、归档命令、平台治理、OAuth secret 或客户端普通目录。对应后端为 [UC-APP-029](../../app-center/use-cases/UC-APP-029-query-owned-application-management.md)，业务字段、可见状态与管理权规则引用 BR-APP-038–043；归档状态及其管理可见性引用 [UC-APP-033 / BR-APP-058](../../app-center/use-cases/UC-APP-033-archive-and-unarchive-application.md#br-app-058)。

## 入口、页面与请求

- 登录后提供“我的应用”入口。无需以 Developer APPROVED 为前置：资格下降不应使当前管理员失去只读处置历史的入口。
- 列表使用 `ListMyApplications`，同源 `POST /app-center/v1/applications:search`，正文严格服从 Proto 的 `query` 映射。显示返回的名称、标识、生命周期、平台可用状态与导航必需摘要；不请求或添加用户资料。
- 提供后端已支持的生命周期、平台可用状态与归档状态过滤；初次查询用服务端默认筛选。归档默认不限制，`ARCHIVED` 与 `UNARCHIVED` 都可见；修改筛选从第一页重新查询。
- 点击项目或访问已校验 ID 的深链接后，用 `GetMyApplication`，`GET /app-center/v1/applications/{application_id}` 读取组合管理概览。Version、资料、发布、Tester、OAuth 和待处理操作的摘要按后端投影表达；摘要不生成未在本提案接受的操作按钮。
- 详情提供返回列表、刷新，以及前往 UC-CONSOLE-003/004/005 的入口。返回可保留本次会话内的筛选和滚动位置，但需重新确认权限和数据；不把旧页作为实时事实。
- loading、空列表、过滤后无结果、读取失败、统一资源不可访问分别有可读状态。详情初次失败不显示上一 Application 内容。

## 前端业务规则

<a id="br-cmg-001"></a>
### BR-CMG-001：管理读取与动作权限分离

页面只把后端管理查询成功解释为可读取该次投影；生命周期、APPROVED Developer、审核权限和写命令仍属于其各自规则。不从技术名称、URL ID、登录摘要、缓存或组件参数推导写权限。404 使用“此应用不存在或当前不可访问”的统一表达，不确认他人资源是否存在。

<a id="br-cmg-002"></a>
### BR-CMG-002：私有页面数据与身份隔离

管理查询沿用 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 的普通 HTTP/JSON chain，BFF 不代理业务正文或补查数据库。响应及错误的 `private, no-store` 必须保留；不进入共享缓存、Service Worker、持久 Query cache、Web Storage 或 IndexedDB。页面内存状态按 surface、Session 身份和资源隔离。身份切换、确认失效、失去管理权或目标变化后清除不再可见的私有内容，丢弃旧请求迟到结果。

<a id="br-cmg-003"></a>
### BR-CMG-003：私有分页与刷新

使用后端不透明 keyset 和返回的 nextPageToken，不解析或制造 token，不使用 offset、不宣称跨页冻结或推测总数。换身份、目标、筛选或查询类型时清除旧 token；无下一 token 才结束。无效 token 提供“从头刷新”，不能静默补 offset。刷新后按当次正式投影更新指针、计数和状态，不把多个请求的 asOf 拼成同一快照。

<a id="br-cmg-004"></a>
### BR-CMG-004：错误、会话与可访问性

按稳定 reason 与 HTTP 状态映射错误，不解析 message。`SESSION_INVALID` 按 UC-CONSOLE-001 清除本 surface Cookie 并回登录，保留浏览器设备私钥；5xx、网络失败和读取结果未知不清 Cookie，允许有界的用户重试。权限变化/统一404后移除不可访问内容，不能用旧缓存“恢复”权限。loading、空态、失败、刷新与分页均可键盘操作，有焦点、语义文本及异步宣告，不只依赖颜色或 toast。失败重试不自动重放任何业务写操作。

## 依赖与验收

依赖固定 API 生成类型、Gateway 精确 DEVELOPER surface、两个 BFF 隔离及真实 Auth USER 签发。没有已授权页面时，不能用通配 Host 暴露所有 App 路由。后续只读用例复用本 UC 的前端规则，不复制后端 BR。

1. 真实当前管理员、资格下降管理员均能读；`ARCHIVED` 不从默认列表消失且与平台暂停、关闭分别表达；其他用户、旧管理员、Reviewer 和不存在资源得到后端规定的统一隐藏。
2. 初次、筛选、翻页、空页、失效 token、刷新、返回和深链接可验证；无未设计的写入口。
3. 转让、身份切换和网络迟到不会向新页面呈现旧管理数据；5xx 保留会话，确认 SESSION_INVALID 只清当前 surface Cookie。
4. Browser→BFF ForwardAuth→Gateway→真实 Auth/App 链路通过，伪造身份、跨源和其他 surface Cookie 失败；成功与业务错误 no-store，浏览器持久存储与日志无私有响应正文/token。
5. 组件测试只证明页面分支；正式完成需真实浏览器联合验收并记录固定输入版本。

## 首个实现决定

本 UC 自 2026-10-15 起接受，并按以下边界启动首个实现工作包：

- 固定统一 API 输入升级为 `a5d504c058c62cd91be451074d21608d69789918`，只从该输入生成 Application Management 查询类型；不得手写第二套响应 DTO。
- Developer Console 使用 `/applications` 作为列表入口，使用 `/applications/{applicationId}` 作为只读详情入口；筛选属于列表 URL search state，详情返回列表时恢复该 search state。
- 首包实现列表、生命周期/平台可用/归档状态筛选、不透明 token 的逐页加载、详情读取、显式刷新、统一不可访问表达和 Session 失效回收；不提前实现 UC003–005 页面或任何写命令。
- 普通管理查询直接使用 ADR-CONSOLE-004 的同源 Gateway route，不增加 BFF body proxy；浏览器 transport 必须携带本 surface Cookie，但不得持久化响应正文或 page token。
- 组件和浏览器测试可以用类型化 fixture 验证页面分支；只有连接真实 Gateway/Auth/App 的联合测试才能登记真实业务链路完成。

## 实现登记

2026-10-15 首个实现工作包已交付：固定类型与同源 client、列表/详情路由、URL 筛选、显式游标翻页、刷新、统一不可访问、`SESSION_INVALID` 回收和仅内存 Query 隔离均已落地。浏览器 fixture 用例、Gateway `latest` 路由组成测试及真实 Auth/App/Mongo 协议 E2E 已通过。

本登记不宣称 UC 的真实浏览器联合验收已完成：仍需由浏览器页面连接同一套真实 Gateway/Auth/App 环境，使用真实管理员与 Application 数据覆盖默认归档可见、深链接、权限隐藏、身份切换和迟到响应。证据与固定镜像 digest 记录在 [Console 实现状态](../implements/README.md)。
