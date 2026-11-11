<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-050 --spec tools/brief-specs/UC-APP-050.json -->
# Brief — UC-APP-050：查询我的待接收 Application 管理权转让

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-050` 查询我的待接收 Application 管理权转让 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-APP-059`–`BR-APP-062`（4 条） |
| 外部引用 BR | `BR-APP-012`、`BR-APP-013`、`BR-APP-019`（来自 `UC-APP-026`） |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |
| 配套查询 | `app-center/query-contracts/incoming-application-transfers.md` |

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

可信 ACTIVE USER 可以分页发现指定给自己的未到期待接收转让，随后进入 UC026 参与者详情并执行原有接受或拒绝。该读取不要求当前仍为 APPROVED Developer。接受资格、七天有效期、终态及并发规则仍以 [UC026](../use-cases/UC-APP-026-transfer-application-administration.md) 的 [BR-APP-012](../use-cases/UC-APP-026-transfer-application-administration.md#br-app-012)、[BR-APP-013](../use-cases/UC-APP-026-transfer-application-administration.md#br-app-013)、[BR-APP-019](../use-cases/UC-APP-026-transfer-application-administration.md#br-app-019) 为唯一权威；搜索命中不构成接受授权。

首期只交付本人入站 PENDING 列表，不交付出站/全状态历史、已读标记、通知、转让对象搜索、Auth 资料批量披露或全平台转让枚举。转让目标继续填写已有 opaque Auth ID。

### 正式接口与输入

现有 `app_center.v1.application_admin_transfer.ApplicationAdminTransferService` 新增 `ListIncomingApplicationAdminTransfers`，App HTTP为 `POST /v1/application-admin-transfers/incoming:search`，body=`query`。Gateway 外部增加 `/app-center`，强制 Session，沿用现有转让查询的协议和 Developer Console 接入，不增加 Admin 枚举入口。

```text
ListIncomingApplicationAdminTransfersQuery {
  pageSize: 1..100 = 20
  pageToken?
}
```

省略/0 pageSize使用默认20，负数或大于100拒绝；pageToken最多4096 UTF-8 bytes。请求不接受 toAuthId、fromAuthId、状态、方向、排序、offset 或任意目标身份。HTTP只接受单个JSON对象、正文最大16 KiB、无query string；未知字段或多份JSON拒绝。native gRPC未知字段同样拒绝。身份验证先于输入解析/校验及数据定位。

### 查询事实与过期边界

同一只读 snapshot 内以可信caller为toAdminId，选取持久状态PENDING且 `expiresAt > asOf` 的申请。App Clock在本次调用取得一个观察时间，按Mongo存储毫秒精度比较，到期边界相等即不返回。查询不调用Auth，不写过期状态、账号 fence、Application fence/revision、业务审计或访问记录。

此列表不承担持久化EXPIRED；UC026详情Get、命令、owner-exit检查与后台收敛继续原规则。列表返回后发生接受/拒绝/取消/关闭/到期是正常变化；操作前重新读取UC026详情与当前事实，不以旧页冻结资格。无符合事项成功返回明确空数组。

### 返回与分页

投影与消费组合见[本人待接收转让读契约](../query-contracts/incoming-application-transfers.md)。每页按 `(requestedAt DESC, transferId DESC)` keyset排序，时间采用存储精度，同时间用规范UUID排序。签名opaque token绑定可信caller、独立查询用途、格式版本和末项位置，换用户、换用途、损坏或不规范编码拒绝。每页重读，不提供跨页冻结、offset或totalCount。

必要申请与Application来源在同一次 majority snapshot中组合；使用技术名称，不依赖公开Profile或发布状态。批准/暂停等Developer资格变化不隐藏本人事项。必要绑定、来源或持久字段损坏整页失败，不丢项、返回部分页或补占位名称。

### 错误与缓存

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信USER | USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY | 401 / UNAUTHENTICATED |
| 非法请求、未知字段或pageSize/token长度 | INVALID_INCOMING_APPLICATION_TRANSFER_QUERY | 400 / INVALID_ARGUMENT |
| token编码、签名、用途、主体或位置非法 | INVALID_INCOMING_APPLICATION_TRANSFER_PAGE_TOKEN | 400 / INVALID_ARGUMENT |
| 必要持久事实损坏 | APPLICATION_ADMIN_TRANSFER_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储或snapshot不可用 | INCOMING_APPLICATION_TRANSFER_UNAVAILABLE | 503 / UNAVAILABLE |

成功与错误均 `Cache-Control: private, no-store`。不披露token、secret、数据库结构或底层原因；读取token只用于本查询，不代替原详情参与者检查。

### 验收

1. 普通ACTIVE USER及Developer PENDING/SUSPENDED/WITHDRAWN读取自己的有效事项；匿名、无效身份先失败。不得根据客户端传入身份读取他人事项。
2. 未发布、无公开Profile、暂停/归档应用事项按原转让事实可读；只读不改变任何gate/revision/转让状态。
3. asOf前/恰好到期/之后，持久EXPIRED及ACCEPTED/REJECTED/CANCELLED均不列出；仅从列表读取不持久化到期，原Get仍收敛EXPIRED。
4. 同时间排序、翻页、跨用户/用途、篡改、畸形、长度与非法pageSize；无事项显式空数组。
5. 必要App丢失、归属/ownership绑定损坏、非法申请字段、存储失败分别按正式错误且无部分页。
6. 与接受、取消、UC027关闭竞争，snapshot只观察完整前/后组合；旧页不能绕过UC026命令。HTTP/原生gRPC及Gateway gRPC-Web输入、缓存和投影一致。

### 实施边界

Domain/UseCase/Port留在Application能力；Mongo adapter增加只读查询与批量来源读取，显式迁移增加 `(toAdminId,status,requestedAt DESC,transferId DESC)` 命名索引并保留原有索引。签名key从已有服务秘密材料按独立用途派生，不引入业务数据兼容或新权限。新生成消息与Proto输入一起提交，Wire使用生成器。先串行专项，后冻结源码/API/已提交docs运行完整backend；Gateway和Console由各自owner接入。

## 业务规则（UC-APP-050 权威正文）

<!-- 权威位置: use-cases/UC-APP-050-query-incoming-application-admin-transfers.md#br-app-059 -->
### BR-APP-059：本人入站集合与读取资格

仅可信ACTIVE USER可查询，toAdminId只取可信主体，当前Developer批准状态不作为列表门槛。集合仅含自己的持久PENDING且未到期申请；其他参与者、已终态和逻辑到期申请不返回。没有事项成功返回空列表，当前源管理员不是申请接收者时不获得该申请的入站事项。

<!-- 权威位置: use-cases/UC-APP-050-query-incoming-application-admin-transfers.md#br-app-060 -->
### BR-APP-060：列表只读与逻辑到期

列表在同一只读snapshot按本次观察时间排除逻辑到期申请，不写状态或协调栅栏。UC026的持久过期收敛和终态互斥不变。返回后的状态变化不保证列表仍可操作，接受/拒绝必须重新走正式详情与命令。

<!-- 权威位置: use-cases/UC-APP-050-query-incoming-application-admin-transfers.md#br-app-061 -->
### BR-APP-061：转让事项的最小一致投影

事项只返回本UC读契约字段，Application技术名称与申请在同一majority snapshot读取。不依赖公开Profile/发布或Auth资料，不披露secret、凭据摘要、配额及私有配置。必要申请/来源缺失、跨应用、参与者或ownership绑定不符和非法字段属于损坏，整页失败。

<!-- 权威位置: use-cases/UC-APP-050-query-incoming-application-admin-transfers.md#br-app-062 -->
### BR-APP-062：本人事项的签名分页与失败边界

使用requestedAt/transferId稳定倒序keyset、1..100默认20和绑定主体/用途/版本/位置的签名token。成功与错误private,no-store；鉴权先于输入和查询，非法token报400、损坏500、存储不可用503，不把失败伪装为空列表。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-026`

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-012 -->
### BR-APP-012：转让身份与参与者

`Application.adminId` 是当前管理权的唯一权威结果；`ApplicationAdminTransfer` 保存过程和审计，不把 `pendingAdminId` 或 transferStatus 塞入 Application。源必须是发起时当前管理员，目标必须是不同的 Auth 用户；只有目标可以接受或拒绝，只有仍为当前管理员的源可以取消。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-013 -->
### BR-APP-013：单一待处理申请与固定过期

每个 Application 最多一个 PENDING 申请，有效期固定 7 天。ACCEPTED、REJECTED、CANCELLED、EXPIRED 均为不可变终态。所有相关命令和 owner-exit 检查都必须先收敛已到期记录，不能让物理上尚未被后台扫描的过期记录永久阻塞新申请或账号退出。

<!-- 权威位置: use-cases/UC-APP-026-transfer-application-administration.md#br-app-019 -->
### BR-APP-019：终态审计、幂等与最小披露

转让终态永久保存参与者、Application、源 ownershipRevision、时间、操作者和 credential handling。读取只允许 from/to 参与者，不提供公开枚举，也不返回技术配额、secret 摘要或其他管理员资料。

同一发起者对相同目标重复发起返回现有 PENDING；目标不同则冲突。终态命令的安全重试返回既有终态，但一次性 secret 永不重放。消息、邮件或 Console deep link 只携带 transferId 等最小定位信息，投递失败不改变转让事实。

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

### `app-center/query-contracts/incoming-application-transfers.md`：本人待接收 Application 转让读契约

#### 权威与投影

集合/身份/过期/分页/错误以 [UC050](../use-cases/UC-APP-050-query-incoming-application-admin-transfers.md) BR-APP-059–062为唯一权威。生命周期和命令仍引用 [UC026](../use-cases/UC-APP-026-transfer-application-administration.md)。

```text
IncomingApplicationAdminTransferItem {
 transferId, applicationId, applicationName
 fromAuthId, toAuthId, status=PENDING
 requestedAt, expiresAt
}
IncomingApplicationAdminTransferPage { items[], nextPageToken?, asOf }
```

#### 组合与消费

技术名称来自同一snapshot的Application，不需要公开Profile或Auth。toAuthId等于本次可信调用者；不返回源/目标资料、secret、配额、原始revision栅栏或私有配置。必要来源和申请归属绑定损坏整页失败，不合成空名或部分页。

列表只用于发现事项，点击后由原GetApplicationAdminTransfer重新读取当前事实；接受/拒绝仍使用UC026，不能把列表状态、前端倒计时或旧页当作资格。列表排除逻辑到期项但不写EXPIRED；没有事项明确items=[]。

分页不承诺跨页冻结。任何新状态均以新的服务端读取为准，已有transferId链接仍有效，不建立通知已读或历史收件模型。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-026`（use-cases/UC-APP-026-transfer-application-administration.md）：目标与范围、参与者与依赖、输入与身份、生命周期、发起流程、接受流程、拒绝与取消、领域与数据模型、API 草图、错误边界、并发验收场景、实现依赖与交付边界、变更记录
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、路由映射、契约测试要求、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、Claims、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-050-query-incoming-application-admin-transfers.md` | 81 | `e7490d217b65` |
| `use-cases/UC-APP-026-transfer-application-administration.md` | 324 | `4e2569e985b2` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `app-center/query-contracts/incoming-application-transfers.md` | 24 | `3e4bdd704f50` |
