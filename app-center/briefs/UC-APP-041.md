<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-041 --spec tools/brief-specs/UC-APP-041.json -->
# Brief — UC-APP-041：管理本人爬虫脚本资源

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-041` 管理本人爬虫脚本资源 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-001`–`BR-SCR-003`（3 条） |
| 外部引用 BR | `BR-APP-008`，`BR-SCR-013`（来自 `UC-APP-025`、`UC-APP-045`） |
| ADR | `ADR-006` |
| 平台共享 | `platform/contracts/app-center-api-routing.md`、`platform/contracts/trusted-identity-v1.md` |

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

具备有效 Developer 资格的用户创建本人 ScriptResource，维护名称与用途。所有脚本均由用户上传。平台开发者也使用自己的用户账号和同一套作者规则。2026-11-11 用户确认此归属和创作模式。

脚本资源独立于 Application，不占 Application 创建配额。应用管理权转让、关闭或引用变化不改变脚本归属。独立版本由 [UC042](../use-cases/UC-APP-042-manage-script-version-draft.md) 管理。

### 参与者与操作

`ScriptAuthoringService` 提供 `CreateOwnScriptResource`（`POST /v1/users/me/script-resources`）和 `ReplaceOwnScriptResourceMetadata`（`PUT /v1/users/me/script-resources/{resource_id}/metadata`）。请求包含名称、用途，替换还需 resourceId 和 expectedRevision。服务从可信身份取得 ownerAuthId，生成 UUIDv7、revision=1、创建与更新审计。替换只改变元数据。相同内容且 revision 匹配时返回原状态，不新增业务审计。

### 失败与验收

缺身份为 Unauthenticated。本人写入无有效 Developer 资格时在目标查找前返回 Forbidden。字段非法为 InvalidArgument，非本人或不存在的资源统一 NotFound。通过归属检查后才返回 revision 或状态冲突。退出栅栏阻止写入，必要事实损坏或存储失败时拒绝成功。

- 无脚本权限的 APPROVED Developer 可以创建和修改本人的资源。跨作者或仅持有平台治理权限的调用者不能写入其他人的资源。
- 两个相同 revision 的不同元数据更新最多一项成功；更新不改变已提交版本及摘要。
- 验证 Auth 的真实 Developer 签发与资格变更、跨作者隐藏、账号退出竞争，以及旧维护权限无法通过作者鉴权。

## 业务规则（UC-APP-041 权威正文）

<!-- 权威位置: use-cases/UC-APP-041-manage-script-resource.md#br-scr-001 -->
### BR-SCR-001：脚本身份、本人归属与历史

ScriptResource 使用独立且永久不复用的 ID，必有一个不可变的 `ownerAuthId`。所有者是创建时已验签 USER 的 Auth ID，创建者审计记录实际操作者。系统只建立用户归属，归属不随 Developer 状态变化。版本沿 resourceId 继承归属。资源及其版本、审核和发布历史不提供物理删除、转让或平台接管入口。名称无需全局唯一。元数据更新不修改版本文本、审核快照或应用引用。

<!-- 权威位置: use-cases/UC-APP-041-manage-script-resource.md#br-scr-002 -->
### BR-SCR-002：作者授权与平台职责隔离

创建、改元数据、建版本、改稿和送审均要求可信 ACTIVE USER 的 `developer_status=APPROVED`。对既有资源的写入还要求 `ownerAuthId` 等于调用者 Auth ID。服务在写事务中核对归属及 [BR-APP-008](../use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-008) 的账号退出栅栏。客户端不能自报所有者、角色或权限。本人读取规则见 [BR-SCR-013](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013)。

审核、独立发布、暂停分发和恢复分发分别要求 `app.script.review`、`app.script.publish`、`app.script.suspend`、`app.script.restore`。四项独立授撤，均不授予创作权限。平台管理员、Reviewer、应用所有者及 SYSTEM 不可代用户创作。旧 `app.script.maintain` 退出授权模型，旧平台创作入口退役。

作者资格取自现有 App audience 的 Auth 可信身份投影。资格变化后，Auth 后续签发使用当前状态，已签身份遵守既有期限与时钟容差。退出栅栏同时约束旧 APPROVED 身份。资格失效不改变既有审核或发布事实。

<!-- 权威位置: use-cases/UC-APP-041-manage-script-resource.md#br-scr-003 -->
### BR-SCR-003：资源元数据与乐观并发

name 去除首尾空白后为 1..128 UTF-8 bytes，purpose 为 1..2048 UTF-8 bytes；不含 NUL。resourceId、revision、时间与操作人不由正文指定。替换需正数 expectedRevision，过期即冲突，无部分写入。每次实际更新原子保存元数据、递增 revision 和可信身份/服务时钟审计；资源元数据 revision 与发布 revision 相互独立。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-025`

<!-- 权威位置: use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-008 -->
### BR-APP-008：归属屏障与零义务准备

`adminId=authId` 的所有 Application 都阻止 Prepare，无论其发布或审核状态。使用 `account_owner_exit_fences` 的 authId 唯一记录作为可写事务栅栏；创建应用和 Prepare 在同一事务中先条件写该栅栏，再读取/修改配额和应用，不能仅用 snapshot 读检查。

PREPARED 和永久 sealed 均阻止新的创建；当前没有转让/关闭入口，未来增加这些行为必须在相同协调点检查。旧 APPROVED JWS 不能越过栅栏。账号没有旧 fence 时可原子建立 OPEN 初始事实，不代表补建 Auth 用户。

脚本资源归属不计入退出义务。依据 [BR-SCR-002](../use-cases/UC-APP-041-manage-script-resource.md#br-scr-002)，作者创建脚本资源、更新元数据、建版本、改稿和送审均在写事务中先条件写同一账号栅栏。PREPARED 或 sealed 拒绝作者写入。作者写入先提交时，脚本按保留记录处理，退出仍按应用义务判定。

### 来自 `UC-APP-045`

<!-- 权威位置: use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-013 -->
### BR-SCR-013：按职责限定查询披露

本人视图要求有效可信 USER 且 `ownerAuthId` 为调用者。Developer 资格失效后，仍可登录的作者可以读取本人历史、草稿和审核结果。本人入口从可信身份确定范围，平台权限不会扩大该范围。未送审的 DRAFT 仅向本人披露，治理视图不列出 DRAFT 或仅有 DRAFT 的资源。

本人资源列表及详情返回 resourceId、名称、用途、revision、时间和最近创建版本的最小摘要。无版本时摘要为空，最近版本按 createdAt 和 versionId 判定。本人版本列表返回 resourceId、versionId、标签、状态、format、digest、revision、时间和已有 reviewId，详情另返回原文。作者审核结果返回 resourceId、versionId、reviewId、审核状态、提交时间、提交时的名称/用途、资源 revision、源版本 revision、format、digest 和 policyVersion。终态另返回决定 ID、结果、决定时间和已保存理由。该投影省略审核人员身份、平台内部审计和跨应用级联信息。

`app.script.review` 可读取脚本队列、受审原文和检查定义、相关资源与已送审版本、决定与级联详情。利益冲突仍可读，详情显示 `canDecide=false` 及冲突类别，决定入口独立校验。`app.script.publish` 可读已送审资源与版本摘要、批准事实和发布历史。`app.script.suspend` 和 `app.script.restore` 可读分发门禁和发布摘要。发布和运维按职责只披露相应摘要与状态。治理查询无权读取作者的私有草稿，也不授予本人写操作。

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

#### 路由映射

App Center 的每个 HTTP 资源在 Proto 内部使用的路径**不含服务前缀**。Gateway 为外部请求增加且只增加一个服务前缀 `/app-center`。

首个正式资源 CreateApplication 的映射是：

| 层 | 方法与路径 | 说明 |
| --- | --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications` | 客户端唯一可见的地址；`app-center` 是服务前缀 |
| Gateway | 剥离前缀 `/app-center` | 只做前缀剥离，不重写其余路径 |
| 内部（Gateway → App Center） | `POST /v1/applications` | Proto `google.api.http` annotation 声明的路径；请求体 `body: "*"` |
| gRPC | `/app_center.v1.application.Application/CreateApplication` | proto package `app_center.v1.application`，service `Application`，rpc `CreateApplication` |

UC-APP-005 审核决定命令遵循同一映射规则：

| 层 | 方法与路径 |
| --- | --- |
| 外部（客户端 → Gateway） | `POST /app-center/v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| Gateway | 只剥离前缀 `/app-center` |
| 内部（Gateway → App Center） | `POST /v1/applications/{application_id}/versions/{version_id}/reviews/{review_id}/decision` |
| gRPC | `/app_center.v1.application_review.ApplicationReview/DecideApplicationVersionReview` |

规则：

- Gateway 必须按**服务名到前缀**的映射表工作，不得把 `/app-center` 硬编码进业务路径，也不得同时改写内部资源路径。
- 前缀剥离后必须保留查询串与请求体。
- 内部路径与 gRPC full method 由 Proto 定义，App Center 的 HTTP 路由注册必须与 Proto annotation 一致；两者不得各写一份。
- 写请求只通过请求体传递资源字段；可信身份只通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 定义的 `x-iwut-identity` 传递，路径或 query 不承载身份。
- 未匹配的服务前缀或缺少前缀的外部请求由 Gateway 拒绝，不转发给 App Center。

#### 契约测试要求

外部到内部的映射必须由**自动化契约测试**机械验证，不能只靠文档。测试至少断言：

1. Proto HTTP annotation 的内部路径等于 `POST /v1/applications`。
2. 外部路径等于服务前缀 `/app-center` 加内部路径，即 `POST /app-center/v1/applications`。
3. 前缀映射只剥离 `/app-center`，得到的内部路径与第 1 项一致。
4. gRPC full method 等于 `/app_center.v1.application.Application/CreateApplication`。
5. 写请求 message 只包含 `name`，不包含身份字段（`authId`、`developer_status`）、服务端字段（`id`、`adminId`、`createdAt`）或持久化技术字段。
6. 响应 message 不包含 `nameKey`、`nextVersionSequence`、`nextProfileRevisionSequence` 或其它内部技术字段。
7. 审核决定的外部/内部路径与上述 UC-APP-005 映射精确一致，gRPC full method 使用同一生成 service。
8. UC-APP-005 审核决定 request body 只包含 `outcome`、`expected_policy_version`、`confirmed_check_ids`、`reason`，不包含 `auth_id`、`permissions`、`developer_status`、`decided_by`、`decided_at`、`approval_validation` 或最终状态。

外部路径可以作为 contract constant / fixture 存在于测试中，但它必须与内部路径、前缀和 gRPC method 在同一测试里被自动验证，任何一侧漂移都必须让测试失败。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-025`（use-cases/UC-APP-025-coordinate-account-owner-exit.md）：目标与范围、主流程与 API、数据与验收、交付依赖
- `UC-APP-045`（use-cases/UC-APP-045-query-script-management-and-reviews.md）：目标与查询、验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `platform/contracts/app-center-api-routing.md`（docs 根级共享文档）：目的与范围、gRPC-Web 终止、关联文档
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、JOSE Header、Claims、时间与有效期、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-041-manage-script-resource.md` | 42 | `260106d12ddb` |
| `use-cases/UC-APP-025-coordinate-account-owner-exit.md` | 69 | `830ba8fcb45d` |
| `use-cases/UC-APP-045-query-script-management-and-reviews.md` | 42 | `deb5f31b4fbd` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `platform/contracts/app-center-api-routing.md` | 67 | `265d198ed686` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
