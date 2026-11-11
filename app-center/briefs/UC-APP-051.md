<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-051 --spec tools/brief-specs/UC-APP-051.json -->
# Brief — UC-APP-051：查询平台 Application 管理目录与摘要

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-051` 查询平台 Application 管理目录与摘要 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-063`–`BR-APP-066`（4 条） |
| 外部引用 BR | — |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |
| 配套查询 | `app-center/query-contracts/platform-application-directory.md` |

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

### 目标与边界

获精确读取权限的可信ACTIVE USER可搜索所有Application的最小核心目录与摘要，定位后进入各正式治理/运维入口。该目录独立于 [UC029](../use-cases/UC-APP-029-query-owned-application-management.md) 当前管理员私有查询及 [UC024](../use-cases/UC-APP-024-query-public-application-catalog.md) 公开运行目录，不放宽其权限或复用其数据拼出全平台目录。

用户搜索只服务管理员治理，由Auth拥有；本UC不提供人员目录/邮箱解析、不查询Auth资料、不返回Version/Profile/Review正文、OAuth/Filter配置、凭据或人员治理理由。Console所有者负责页面接入，App不实现Console。

### 精确读取权限

两个方法均要求App audience可信ACTIVE USER含精确 `app.application.search`。平台管理员、Reviewer、Developer、应用owner、suspend/restore权限均不隐式赋予该权限；该权限也不赋予任何写入或UC029私有详情读取权。鉴权先于参数/目标读取。

Auth owner负责新权限独立授撤、本人有效权限发现、permissionRevision及App audience签发的权威UC；其设计需按用户流程单独审核。App只消费该精确ID，不在App建立权限来源副本。撤权沿正式短期JWS边界，不承诺离线App瞬时撤权。该Auth契约就绪前不开放依赖其签发的真实链验收。

Gateway强制Session，增加ADMIN Console surface，不增加Developer Console全平台目录；域名不代替App授权。

### 正式接口与输入

独立 `app_center.v1.application_platform_query.ApplicationPlatformQueryService`：

| RPC | App HTTP |
| --- | --- |
| SearchPlatformApplications | POST `/v1/platform/applications:search`，body=query |
| GetPlatformApplicationSummary | GET `/v1/platform/applications/{application_id}` |

外部增加 `/app-center`。搜索输入和返回字段见[平台应用目录读契约](../query-contracts/platform-application-directory.md)。query中applicationId/adminAuthId精确匹配，namePrefix使用Application技术名称的现有nameKey规则，不接受正则。各非空过滤条件AND组合；空状态维度不限制，空query可分页浏览。首期不搜索公开Profile展示名、描述、版本内容，不提供全文排序。

pageSize省略/0为20，范围1..100，pageToken最大4096 UTF-8 bytes。拒绝未知字段、非法/未知状态及非法ID/前缀；POST只接受单个JSON对象、最大16KiB、无query string覆盖；GET无body/query。native未知字段同样拒绝。

### 读取与分页

每次使用一致majority只读snapshot和本次观察时间，不写访问事实或gate。覆盖未发布、无公开Profile、暂停、归档、CLOSING/CLOSED应用；三种状态维度独立，不以某一状态推导另一状态。

按 `(nameKey ASC,applicationId ASC)` keyset排序；比较键不作为响应字段。签名token绑定caller、用途、版本、规范过滤条件与末项位置。每页底层扫描最多500条，允许短页/空页附nextPageToken，但不跳过尚未返回的合法项；无offset/totalCount或跨页冻结。读取只组合最小核心状态，不逐项聚合子资源或调用Auth。

目录详情与搜索使用同一权限及相同最小投影，用于重新定位已知ID。选中摘要不构成操作授权或专用revision基线；写命令仍依各自正式入口重读/确认/鉴权。

### 错误与缓存

缺失/无效USER401，缺精确permission403；非法请求400，错误token400；摘要目标不存在404；必要事实损坏500；存储/snapshot不可用503。稳定reason分别为 USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY、APPLICATION_PLATFORM_SEARCH_REQUIRED、INVALID_PLATFORM_APPLICATION_QUERY、INVALID_PLATFORM_APPLICATION_PAGE_TOKEN、PLATFORM_APPLICATION_NOT_FOUND、PLATFORM_APPLICATION_STATE_INCONSISTENT、PLATFORM_APPLICATION_UNAVAILABLE。损坏/故障不转成空页或单项隐藏。所有响应与错误private,no-store，消息不回显输入、权限材料或底层原因。

### 验收与依赖

覆盖none/search-only/suspend-only/restore-only/Reviewer/完整平台管理员无grant/owner等独立组合；按Auth实际授撤与签发证明权限边界。覆盖名称前缀、同名不同owner、精确ID/owner与状态组合、未公开/关闭应用、同key分页、篡改/换主体/过滤/用途、500扫描和空页继续、必要损坏/存储失败、读后状态变化及不能绕过其他入口。三协议与ADMIN/Developer surface隔离均需验收。

本UC在UC050完成后串行实现；Auth权限契约先就绪，App/API固定后按用户的API对齐→Gateway接入→固定本地镜像流程联合验证，再执行冻结完整backend；如共享Auth身份契约改变，补相应跨服务tier。用户搜索及Auth授权方案仍由Auth owner独立设计，不用本UC自批其语义。

## 业务规则（UC-APP-051 权威正文）

<!-- 权威位置: use-cases/UC-APP-051-query-platform-application-directory.md#br-app-063 -->
### BR-APP-063：平台应用发现的精确只读授权

平台目录与最小摘要只接受含app.application.search的可信ACTIVE USER。所有其他角色/权限不隐式授权，本权限不授予写入或owner私有配置读取。Auth是权限权威，App只按精确ID校验，授权先于输入/目标定位。

<!-- 权威位置: use-cases/UC-APP-051-query-platform-application-directory.md#br-app-064 -->
### BR-APP-064：全平台核心目录与过滤

所有Application生命周期、可用性与归档状态及未公开/未发布应用均可被本权限发现。过滤为ApplicationId、当前管理员opaque AuthId、技术名称前缀和三个独立状态维度的AND组合；空维度不过滤。仅披露读契约定义的核心摘要，不能沿目录读取下级私有资源或Auth资料。

<!-- 权威位置: use-cases/UC-APP-051-query-platform-application-directory.md#br-app-065 -->
### BR-APP-065：平台目录的有界签名分页

按nameKey/applicationId升序keyset，默认20最多100，扫描预算500。签名token绑定主体、用途、版本、规范过滤及末项位置；不跳过合法未返回项，允许短/空页继续，无offset/totalCount或跨页冻结。

<!-- 权威位置: use-cases/UC-APP-051-query-platform-application-directory.md#br-app-066 -->
### BR-APP-066：平台摘要快照与失败关闭

必要核心状态在同一majority只读snapshot校验并投影；当前摘要只表达本次观察，不构成操作授权。必要事实损坏整页/详情500，存储故障503，不隐藏损坏、不伪装为空。成功和错误private,no-store；非法请求/token、未知目标和授权失败依本UC稳定错误区分。

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

### `app-center/query-contracts/platform-application-directory.md`：平台 Application 目录与摘要读契约

#### 权威与输入

授权、集合、过滤、分页及错误以 [UC051](../use-cases/UC-APP-051-query-platform-application-directory.md) BR-APP-063–066为唯一权威，不替代UC029/UC024或Auth权限定义。

```text
SearchPlatformApplicationsQuery {
 applicationId?, namePrefix?, adminAuthId?
 lifecycleStatuses[]?, platformAvailabilityStatuses[]?, archiveStatuses[]?
 pageSize, pageToken?
}
```

#### 核心投影

```text
PlatformApplicationSummary {
 applicationId, name, adminAuthId, createdAt
 ownershipRevision
 lifecycleStatus, lifecycleRevision
 platformAvailabilityStatus, platformAvailabilityRevision
 archiveStatus, archiveRevision
}
PlatformApplicationPage { items[], nextPageToken?, asOf }
```

详情与每个列表项使用同一投影，不返回比较键、Version/Profile/Review正文、计数、Filter/OAuth、凭据、历史理由或Auth用户资料。未发布/无公开资料不影响核心摘要。

#### 消费组合

目录只用于定位，当前摘要不是暂停/恢复等操作的确认基线。Console须按已获得的独立操作权限进入专用读取并重新确认各自revision；search权限本身不授予任何写权。

三种状态维度独立。每页snapshot可观察到不同归属或状态，旧token不是权限缓存；每次仍须验证本次身份与精确permission。界面不能以空页替代故障，也不能拼接UC029/UC024结果填充此目录。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、路由映射、契约测试要求、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、Claims、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-051-query-platform-application-directory.md` | 70 | `3c3c13e09bb0` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `app-center/query-contracts/platform-application-directory.md` | 36 | `444599f0fb51` |
