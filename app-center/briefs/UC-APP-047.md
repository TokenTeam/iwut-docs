<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-APP-047 --spec tools/brief-specs/UC-APP-047.json -->
# Brief — UC-APP-047：查询脚本独立分发与应用精确内容

> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-APP-047` 查询脚本独立分发与应用精确内容 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-SCR-019`–`BR-SCR-022`（4 条） |
| 外部引用 BR | `BR-SCR-005`、`BR-SCR-014`（来自 `UC-APP-042`、`UC-APP-045`） |
| ADR | `ADR-006`、`ADR-008` |
| 配套查询 | `app-center/query-contracts/script-distribution.md` |

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

提供两个明确入口：独立查询/获取已经发布的脚本，以及为已通过既有 App 运行资格校验的客户端返回目标 ApplicationVersion 的精确脚本依赖。脚本不以必须关联应用作为独立发布与获取前提。客户端本地执行；本文只设计 App 后端，不实现客户端 Runner、本地权限、凭据、沙箱或离线缓存协议。

### 正式分发接口

2026-11-07 用户接受具体接口与既有 UC 修订，2026-11-08 落实。`app_center.v1.script_distribution.ScriptDistributionService` 提供下列四个方法。表中为 App 内部路径，Gateway 对外增加 `/app-center`，使用普通 PUBLIC surface、强制 Session 和可信 App ACTIVE USER；不要求脚本管理权限。HTTP、原生 gRPC、gRPC-Web 共享语义，所有成功与错误响应均 private, no-store。

| 方法 | HTTP | 输入 |
| --- | --- | --- |
| ListPublishedScripts | GET `/v1/scripts` | 可选 limit、cursor |
| GetPublishedScriptContent | GET `/v1/scripts/{resource_id}/versions/{version_id}/content` | 必填 expectedDigest query |
| ResolveApplicationScriptManifest | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts:resolve` | `{runtime}` 正文 |
| GetApplicationScriptContent | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts/{script_version_id}:getContent` | `{runtime, expectedDigest}` 正文 |

`runtime` 为 `{mode, hostRpcApiMajor, hostCapabilities[]}`。mode 必须显式为 PURE_TEST 或 UNIFIED，缺失/UNSPECIFIED/未知值拒绝。PURE_TEST 复用 [UC012](../use-cases/UC-APP-012-resolve-test-launch-target-for-tester.md)，UNIFIED 复用 [UC023](../use-cases/UC-APP-023-resolve-unified-launch-target.md)。major/capabilities 沿用既有格式、数量、去重排序和长度限制。请求不接受可信身份、channel、Membership、cohort 或命中结果。

应用入口在同一个 snapshot 内重新解析并比较目标 versionId 与 applicationVersionId。目标相同且当前有资格时可使用该 snapshot 的新 publicationRevision，不要求客户端锁定整份旧 Publication；换成其他版本则统一不可获取，不替换请求。正文请求没有重复 resourceId，由批准依赖唯一确定关系。

读取投影、排序、分页和各入口组合见[运行脚本读契约](../query-contracts/script-distribution.md)。它引用本 UC 的 BR，不另定义发布、审核或运行资格。新接口不增加用户可见管理历史、永久下载 URL 或客户端 Runner。

### 内容与传输预算

首期每次返回一份完整 `contentText` 与精确描述符，不分块，不合并16份正文。原文上限1 MiB，沿用 [BR-SCR-005](../use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-005) 的原字节与既有 SHA-256 表示。HTTP 使用标准 Proto JSON，解码后保留 BOM、CRLF、空白等原始 UTF-8 字节，不重新序列化 JSON，不执行脚本。expectedDigest 必填并严格校验格式；格式合法但值不同按统一不可获取，不披露真实摘要。

HTTP JSON 响应最坏转义预算为 `6 × 1 MiB + 16 KiB`，原生 protobuf 单份文本与描述符在4 MiB消息预算内。gRPC-Web 用同一 protobuf；三协议必须用接近原文上限且包含高转义密度的真实文本验收。请求正文上限16 KiB，GET 只接受声明 query，POST 不接受 query 覆盖正文、未知字段或多份 JSON。

### 事实一致性与写入排序

读取在原入口的身份/候选隐藏边界后，验证精确批准 Version/Review/decision、永久发布资格及首次来源事件、资源 AVAILABLE，以及文本 format/digest/byteLength。合法 APPROVED 但从未发布，或已知 SUSPENDED，是正常不可分发。本应存在的批准/发布来源缺失、跨资源、描述符冲突或摘要损坏是不变量异常，不能当作普通未发布。head 不参与历史精确资格的选择或替换。

一次读取的全部必要来源在同一 majority read-only snapshot 内，与暂停/恢复或换槽观察提交前后的完整组合；查询不写 coordinationRevision。实际应用槽位发布及 Grey 比例变化在最终事务复核依赖，并按 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md) 对所有资源共享门禁取得真实写栅栏，与 Suspend 确定排序。失败不能留下 Publication revision、History 或部分脚本 fence。

清空槽位仍允许。匹配 OCC 的相同槽位/比例 no-op 保持原幂等行为，不新增发布事实，不赋予运行资格；在线读取继续核验脚本。旧 revision 先按原 OCC 冲突处理。DECREASE 免除的外部 Scope/URL 复检不免除本地脚本依赖门禁，Clear 不依赖该门禁。

### 既有入口的稳定映射

下表的不可分发只指合法的未发布或暂停，不能用业务不可用隐藏存储故障或损坏。实际选择前继续原身份、major、capability 及 cohort 分支，不为已被这些条件排除的私有候选额外读取脚本。

| 入口 | 正常不可分发 | 损坏与故障 |
| --- | --- | --- |
| UC007/020/021 发布 | 新增 APPLICATION_SCRIPT_DEPENDENCY_UNAVAILABLE，422 / FAILED_PRECONDITION；不推进 revision/History | 批准关系损坏复用 review-state inconsistent，发布资格/gate 损坏复用 publication-state inconsistent；存储故障 APPLICATION_PUBLICATION_UNAVAILABLE，503 / UNAVAILABLE |
| UC012 | APPLICATION_TEST_TARGET_UNAVAILABLE，404 / NOT_FOUND，无降级 | 已读损坏仍 test-publication inconsistent，503 / UNAVAILABLE；存储依赖维持服务不可用 |
| UC023 | APPLICATION_LAUNCH_TARGET_UNAVAILABLE，404 / NOT_FOUND，不再尝试低优先级版本 | runtime-state inconsistent 500；存储故障按既有内部失败 |
| UC024 | Stable 基线或最终选中目标不可分发则列表隐藏该项，详情 PUBLIC_APPLICATION_NOT_FOUND | 已读损坏整页/详情500，存储故障整次失败，不静默丢项 |
| UC038 | 公开资料、有效 Test 和 capabilities 之后投影 SCRIPT_DEPENDENCY_UNAVAILABLE，保留参与卡片，无 launchTarget，missingCapabilities 为空 | 原 MY_TEST_APPLICATION_STATE_INCONSISTENT 500 / MY_TEST_APPLICATION_UNAVAILABLE 503 |
| UC019 两个运行查询 | OAUTH_CLIENT_RUNTIME_UNAVAILABLE，422 / FAILED_PRECONDITION；固定渠道，无回退 | OAUTH_CLIENT_STATE_INCONSISTENT 500 / OAUTH_PROVIDER_UNAVAILABLE 503，runtime tuple 不变 |

UC024 的 Stable 仍独立承担普通候选资格，不能因本人 Test 可运行而绕过不可分发 Stable；普通项继续原 Filter 语义。UC038 保持纯 Test 且不执行 Filter，新卡片状态不改变 Membership。

UC019 的 GetClientConfiguration、VerifyClientSecret 和 GetApplicationPublishedRedirects 保持原职责。sector 回调并集不是运行授权，脚本暂停不删改其已批准槽位回调；两个运行查询每次各自重新核验。已下载文本、已签发 token 和现有 consent 不新增后台批量撤销任务。

### 新接口错误

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信 ACTIVE USER | 复用既有 USER 身份错误 | 401 / UNAUTHENTICATED |
| 非法 ID、mode、runtime、digest 格式、limit 或 HTTP 输入 | INVALID_SCRIPT_DISTRIBUTION_REQUEST | 400 / INVALID_ARGUMENT |
| cursor 损坏、用途或绑定不匹配 | INVALID_SCRIPT_DISTRIBUTION_CURSOR | 400 / INVALID_ARGUMENT |
| 目标不存在、未批准、未发布、暂停、摘要不匹配，或应用目标/运行资格不成立 | SCRIPT_CONTENT_UNAVAILABLE | 404 / NOT_FOUND |
| 已读必要事实损坏 | SCRIPT_DISTRIBUTION_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储/snapshot/依赖不可用 | SCRIPT_DISTRIBUTION_UNAVAILABLE | 503 / UNAVAILABLE |

新应用内容接口统一隐藏目标与资格，不携带真实摘要、正文或私有管理信息；原 UC012/023 公共 RPC 仍用各自错误。独立列表无候选成功空数组，损坏整页失败。

### 验收

- 应用关联入口：未发布、暂停、未授权 Tester、错误 cohort、旧换槽目标、错误摘要与无关版本请求不能取得正文。
- 上述 Tester/cohort/目标条件适用于应用关联入口；独立入口仅分发已批准且已发布的 AVAILABLE 脚本，不能因此启动原无权应用。
- 未关联应用的已发布脚本可独立查询/下载；普通用户不取得未发布正文，匿名请求失败。
- 人工审核批准应用可发生在脚本发布前，但应用发布在脚本可分发前被阻止。
- B 成为 head 后 A 的引用/正文/摘要不变；服务不执行 JSON，不静默返回另一格式。
- 暂停和目标/内容读取竞争有确定序列；客户端已下载文本的撤回不在后端承诺内。
- Test、Stable、Grey 新发布和 Grey 实际比例调整复核全部依赖，任一失败整体回滚；清空与匹配 no-op 保持既有语义。
- 原候选仅因 capability 不足时仍可按原规则选择；已选择候选因脚本不可分发不能降级，普通目录隐藏、本人的纯 Test 参与卡片保留。
- 近1 MiB 高转义密度文本经 HTTP、原生 gRPC、gRPC-Web 恢复原字节；同时间分页、调用者绑定和空依赖明确返回。

## 业务规则（UC-APP-047 权威正文）

<!-- 权威位置: use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-019 -->
### BR-SCR-019：受审版本的运行清单

依赖清单来自目标已批准 ApplicationVersion 与其批准审核快照的相同引用，返回 resourceId、versionId、contentFormat、digest、byteLength；永不跟随 ScriptResource head，也不按版本标签猜 latest。空依赖返回明确空列表。损坏、缺失或不匹配不退化为空依赖。

<!-- 权威位置: use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-020 -->
### BR-SCR-020：发布与在线解析的精确依赖门禁

App 放入/替换 Test、Stable、Grey 槽位前，所有精确依赖须 APPROVED、曾发布且资源 AVAILABLE；任一不满足则整个发布失败。只调整灰度比例也复核目标，清空槽位仍允许。该规则为对 UC007/020/021 的已接受扩展，在进入发布/运行工作包时同步这些用例及对应 brief。

后续在线 Test/统一启动、普通目录、本人测试和 Auth OAuth 上下文按其原有资格及隐藏语义消费同一门禁：依赖不可分发的候选不能作为可启动/可授权目标，不能省略脚本继续返回目标、替换脚本或自动回退到另一应用版本。既有候选优先级保留，只在原 UC 明确允许的分支选择。管理/审核历史仍可读。

读取可线性化在暂停前或后，已经返回的目标不被撤回；后续实际内容获取再次核验。不可读或事实损坏须失败关闭，并按原 UC 区分业务不可用与依赖故障，不把存储错误当作永久无候选。新增联合门禁的 Catalog/OAuth 错误见下文「既有入口的稳定映射」与运行读契约。

<!-- 权威位置: use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-021 -->
### BR-SCR-021：内容获取的资格与字节一致性

应用关联入口须由可信 ACTIVE USER 指定 applicationId、applicationVersionId、scriptVersionId、期望 digest；先复用既有运行目标选择及 Tester/cohort/RPC major 资格，确认该 App Version 此刻是调用者有权取得的目标并确实引用该脚本，再核对脚本批准、曾发布资格及 AVAILABLE。不能持任意 scriptVersionId 枚举未发布正文，不新增可转发且绕过 gate 的永久公开 URL。

服务返回审核时同一精确文本、format、digest、byteLength，控制响应 private, no-store。所有依赖先整体校验，失败不返回部分“可运行清单”；单份内容传输前再校验该目标和脚本。换槽后旧目标的应用关联请求可能失效，客户端重新解析而非替换脚本。独立获取不能替代这条应用资格验证或改变其清单，独立入口见下一规则。HTTP/gRPC 方法、单份传输与大小上限见下文「正式分发接口」和「内容与传输预算」。

<!-- 权威位置: use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-022 -->
### BR-SCR-022：独立已发布脚本的查询与获取

独立分发向所有可信 ACTIVE USER 开放已发布脚本，不要求 Application 关联、Developer、Tester 或脚本管理权限；匿名读取不在首期范围。已发布文本不是按 Application 权限保密的材料，独立读取不授予应用启动或 OAuth 资格，也不允许将任意独立脚本替代应用固定依赖。

独立列表只返回 AVAILABLE 且 head 非空资源的最小元数据和推荐精确版本描述符，分页按 [BR-SCR-014](../use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-014)。独立内容获取必须指定 resourceId、versionId 和期望 digest，再核对属于该资源、已批准、曾发布和 AVAILABLE，返回同一原文及摘要；未关联任何应用的版本同样可用。历史已发布版本可凭精确 ID 获取，不因 head 变更而替换。ClearHead 使资源退出独立推荐列表，仍保留历史精确获取；Suspend 阻断两者。

未发布/不存在目标统一不可获取，不泄漏待审正文或私有管理信息。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-APP-042`

<!-- 权威位置: use-cases/UC-APP-042-manage-script-version-draft.md#br-scr-005 -->
### BR-SCR-005：不透明文本及精确摘要

首期仅受理显式 `contentFormat=json`，非空且不全为空白、UTF-8 编码后不超过 1,048,576 bytes 的合法文本，拒绝 NUL 和非法 UTF-8。不 trim、不格式化、不改写 BOM/换行、不重排 JSON 键。摘要为 `SHA-256(受理原文的 UTF-8 bytes)`，小写十六进制；格式作为独立字段参与审核快照核对。HTTP JSON 转义仅为传输编码，不参与正文摘要。

后端不解析 JSON 结构、执行、推断权限或依据语法自动判为通过；即使 JSON 语法错误，满足文本边界仍可保存，逻辑正确性进入人工检查。`lua` 目前返回 UnsupportedScriptFormat，未来以新格式支持和新版本扩展，不推测格式、不转换旧文本、不建立未上线旧数据兼容分支。

### 来自 `UC-APP-045`

<!-- 权威位置: use-cases/UC-APP-045-query-script-management-and-reviews.md#br-scr-014 -->
### BR-SCR-014：一致详情与有界列表

详情在同一次一致读取中校验资源归属、resourceId/versionId/reviewId 关联、状态、原文/digest、绑定政策和唯一决定，并按职责投影。PENDING 队列仅包含待审。Reviewer 的级联详情返回 taskId、状态、进度观测时间、已处理数量、实际拒绝/既有终态/关闭豁免的分别计数及受控失败分类。完成以 [UC049](../use-cases/UC-APP-049-cascade-script-rejection.md) 的判据为准。

limit 默认 20、最大 100，按 createdAt 和唯一 ID 稳定倒序。本人的版本列表可按状态过滤。先按所有者或平台职责过滤，再做有界分页。opaque cursor 绑定调用者、查询范围、父资源、过滤与排序。非法或不匹配 cursor 报错。正文只在详情返回，决定前重读详情。

所有视图为 `private, no-store`。先鉴权再定位目标。本人查询的未知、非本人或路径关联不匹配统一 NotFound。必要事实损坏时明确失败。

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

### ADR-008：脚本依赖同库事务与拒绝级联（`ACCEPTED`）

#### 决定

沿用 [ADR004](../adr/ADR-004-mongodb-transactions-and-schema-management.md) 的 MongoDB 副本集事务、显式 schema migration 和有界重试；不新增 Resource Hub、数据库、服务 audience 或跨服务事务协议。

1. 在 ScriptVersion 权威文档维护 adapter-only dependencyFence。App 送审对所有依赖按确定 ID 顺序做真实条件递增，条件为精确身份/摘要及允许状态，再在同事务创建 AppReview、迁移 Version、写入每个反向依赖。脚本批准/拒绝写同一权威文档，产生真实写冲突并重试；只读、no-op `$set` 或仅插独立依赖行不能充当栅栏。
2. 拒绝决定与唯一持久 cascade task 同事务写入。任务内有源决定 ID、状态、lease、分页进度和失败观测；没有内存通知依赖。worker 以稳定键集分批扫描不可变反向依赖，逐目标条件事务终结，App 原有 writer 共享既有栅栏/锁序，不建立第二个 App 决定通道。
3. 反向依赖唯一键为 `(appReviewId, scriptVersionId)`，查询索引以 scriptVersionId 为首列；任务源 scriptDecisionId 唯一。历史关系保留，当前 Review 状态决定是否需处理。分批后重新验证无 PENDING 目标才能 COMPLETE；已拒绝状态和送审真实写栅栏保证不会有后来的合法登记。
4. App 最终批准在同一决定事务校验固定脚本批准事实。脚本已批准为不可变终态，故无后续拒绝翻转；仍核对一致的身份、摘要和决定关系。分发暂停使用独立 availability 文档/栅栏，不复用不可变审核结果。
5. Script Publish 与 Suspend 通过同一资源 gate 的真实条件写串行化。App 发布在原 Publication 事务中按确定资源顺序消费该 gate 栅栏，核对精确版本的已发布事实；在线解析/内容读取采用一致快照，响应可线性化在暂停前或后。不能把跨请求缓存当作实时 gate。

具体 collection/schema、索引名、批大小、lease 和重试参数在对应 UC 的实施工作包中落定。栅栏溢出、关联缺失、摘要不符必须失败关闭。

## 配套查询契约（按 spec 显式抽取）

> 这些是当前 bounded context 的查询契约；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `app-center/query-contracts/script-distribution.md`：独立脚本分发与应用精确依赖读契约

#### 定位与权威

本文定义 [UC047](../use-cases/UC-APP-047-resolve-application-script-content.md) 四个查询的投影、分页和组合语义。资格及固定依赖以 BR-SCR-019–022 为唯一权威；HTTP/RPC、错误、文本与传输预算见该 UC 的正式分发接口及后续章节。查询不写访问事实、业务 revision 或审计，不构成运行租约。

#### 身份与查询边界

四个查询只向可信 ACTIVE USER 开放。独立分发不要求应用关联、Developer、Tester 或五项脚本管理权限。应用入口根据 PURE_TEST/UNIFIED 选择既有运行解析规则，再验证请求的精确 ApplicationVersion；不信任用户自报身份、channel、cohort 或 Membership。

所有返回只使用同一次一致读取的必要事实。未授权目标、未发布正文及运维/审核私有信息不通过状态差异或字段披露。整个 manifest 校验后才能返回，内容请求重新验证当前目标和全部依赖，不信任前一次查询结果。

#### 独立推荐列表

ListPublishedScripts 依 [BR-SCR-022](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-022) 选取当前 AVAILABLE 且 head 非空资源，返回：

```text
PublishedScriptItem {
  resourceId, name, purpose
  head: { versionId, versionLabel, contentFormat, digest, byteLength }
}
PublishedScriptPage { items[], nextCursor?, asOf }
```

name/purpose 是当前资源元数据；head 是精确发布事实，不返回正文、人员、理由、私有 revision 或未发布版本。发布 head 的必要关系损坏时整页失败，不能用普通隐藏掩盖。

按资源 createdAt/resourceId 稳定倒序，limit 默认20、范围1–100；游标采用独立签名用途并绑定可信调用者、过滤条件和最后已消费资源位置。每页重新读取 gate，不跨页冻结。扫描预算500，响应预算2 MiB；可返回短页/空页及 nextCursor，不越过尚未返回的合法项。不返回 totalCount，不使用 offset。正常不可推荐项消耗扫描位置，不消耗返回条数。单个合法项必须能独立返回。

#### 应用 manifest

ResolveApplicationScriptManifest 返回：

```text
ApplicationScriptManifest {
  applicationId, applicationVersionId
  publicationRevision, channel, rpcApiMajor
  scripts: [{ resourceId, versionId, contentFormat, digest, byteLength }]
  asOf
}
```

scripts 的精确来源、0..16上限、明确空列表及规范排序以 [BR-SCR-019](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-019) 和 [BR-SDP-001](../use-cases/UC-APP-048-manage-application-script-dependencies.md#br-sdp-001) 为准。它不跟随 head、不返回备用依赖，不包含 launch URL、scopes、Filter、Tester/cohort 材料或其他槽位。publicationRevision 只表示本次解析事实，不冻结随后内容请求。

#### 单份精确内容

独立 GetPublishedScriptContent 返回 resourceId、versionId、contentFormat、digest、byteLength、contentText 和 asOf。应用 GetApplicationScriptContent 在相同内容字段外返回本次 applicationId、applicationVersionId、publicationRevision、channel、rpcApiMajor。字段全部来自同一事实组合，不返回管理/审核人员、决定、理由或策略。

每次只返回一份完整文本，正文及摘要按 [BR-SCR-021](../use-cases/UC-APP-047-resolve-application-script-content.md#br-scr-021) 和 UC047 内容预算校验。ClearHead 后历史精确内容仍可用；Suspend 后新内容请求不可用。已取得文本不提供服务端追回承诺。

#### 既有消费入口

[UC047 稳定映射](../use-cases/UC-APP-047-resolve-application-script-content.md#既有入口的稳定映射)固定各入口的业务不可用、损坏及故障分类。UC012/023 保留原运行资格和能力分支；UC024 独立验证 Stable 基线并消费最终目标；UC038 保留本人的参与事实，增加 SCRIPT_DEPENDENCY_UNAVAILABLE 卡片状态；UC019 两个运行查询复核 gate，sector 回调查询不承担运行授权。

脚本 gate 不省略固定依赖、不替换版本、不把存储失败伪装成无候选、不返回部分“可运行”结果。对应管理/审核历史继续按各自权限读取。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-APP-042`（use-cases/UC-APP-042-manage-script-version-draft.md）：目标与输入、流程与验收
- `UC-APP-045`（use-cases/UC-APP-045-query-script-management-and-reviews.md）：目标与查询、验收
- `ADR-006`（adr/ADR-006-proto-v1-and-api-repository.md）：背景、协议演进、考虑过的替代方案、结果、关联文档
- `ADR-008`（adr/ADR-008-script-dependency-transactions-and-cascade.md）：背景、替代方案与后果

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-APP-047-resolve-application-script-content.md` | 112 | `eb7fc45df935` |
| `use-cases/UC-APP-042-manage-script-version-draft.md` | 38 | `7e9b905d0081` |
| `use-cases/UC-APP-045-query-script-management-and-reviews.md` | 42 | `deb5f31b4fbd` |
| `adr/ADR-006-proto-v1-and-api-repository.md` | 93 | `6ac581622139` |
| `adr/ADR-008-script-dependency-transactions-and-cascade.md` | 27 | `f86c4e6d9c1d` |
| `app-center/query-contracts/script-distribution.md` | 56 | `db08be9f7cb0` |
