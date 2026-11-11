# UC-APP-047：查询脚本独立分发与应用精确内容

状态：`ACCEPTED`

## 目标与范围

提供两个明确入口：独立查询/获取已经发布的脚本，以及为已通过既有 App 运行资格校验的客户端返回目标 ApplicationVersion 的精确脚本依赖。脚本不以必须关联应用作为独立发布与获取前提。客户端本地执行；本文只设计 App 后端，不实现客户端 Runner、本地权限、凭据、沙箱或离线缓存协议。

## 业务规则

<a id="br-scr-019"></a>
### BR-SCR-019：受审版本的运行清单

依赖清单来自目标已批准 ApplicationVersion 与其批准审核快照的相同引用，返回 resourceId、versionId、contentFormat、digest、byteLength；永不跟随 ScriptResource head，也不按版本标签猜 latest。空依赖返回明确空列表。损坏、缺失或不匹配不退化为空依赖。

<a id="br-scr-020"></a>
### BR-SCR-020：发布与在线解析的精确依赖门禁

App 放入/替换 Test、Stable、Grey 槽位前，所有精确依赖须 APPROVED、曾发布且资源 AVAILABLE；任一不满足则整个发布失败。只调整灰度比例也复核目标，清空槽位仍允许。该规则为对 UC007/020/021 的已接受扩展，在进入发布/运行工作包时同步这些用例及对应 brief。

后续在线 Test/统一启动、普通目录、本人测试和 Auth OAuth 上下文按其原有资格及隐藏语义消费同一门禁：依赖不可分发的候选不能作为可启动/可授权目标，不能省略脚本继续返回目标、替换脚本或自动回退到另一应用版本。既有候选优先级保留，只在原 UC 明确允许的分支选择。管理/审核历史仍可读。

读取可线性化在暂停前或后，已经返回的目标不被撤回；后续实际内容获取再次核验。不可读或事实损坏须失败关闭，并按原 UC 区分业务不可用与依赖故障，不把存储错误当作永久无候选。新增联合门禁的 Catalog/OAuth 错误见下文「既有入口的稳定映射」与运行读契约。

<a id="br-scr-021"></a>
### BR-SCR-021：内容获取的资格与字节一致性

应用关联入口须由可信 ACTIVE USER 指定 applicationId、applicationVersionId、scriptVersionId、期望 digest；先复用既有运行目标选择及 Tester/cohort/RPC major 资格，确认该 App Version 此刻是调用者有权取得的目标并确实引用该脚本，再核对脚本批准、曾发布资格及 AVAILABLE。不能持任意 scriptVersionId 枚举未发布正文，不新增可转发且绕过 gate 的永久公开 URL。

服务返回审核时同一精确文本、format、digest、byteLength，控制响应 private, no-store。所有依赖先整体校验，失败不返回部分“可运行清单”；单份内容传输前再校验该目标和脚本。换槽后旧目标的应用关联请求可能失效，客户端重新解析而非替换脚本。独立获取不能替代这条应用资格验证或改变其清单，独立入口见下一规则。HTTP/gRPC 方法、单份传输与大小上限见下文「正式分发接口」和「内容与传输预算」。

<a id="br-scr-022"></a>
### BR-SCR-022：独立已发布脚本的查询与获取

独立分发向所有可信 ACTIVE USER 开放已发布脚本，不要求 Application 关联、Developer、Tester 或脚本管理权限；匿名读取不在首期范围。已发布文本不是按 Application 权限保密的材料，独立读取不授予应用启动或 OAuth 资格，也不允许将任意独立脚本替代应用固定依赖。

独立列表只返回 AVAILABLE 且 head 非空资源的最小元数据和推荐精确版本描述符，分页按 [BR-SCR-014](UC-APP-045-query-script-management-and-reviews.md#br-scr-014)。独立内容获取必须指定 resourceId、versionId 和期望 digest，再核对属于该资源、已批准、曾发布和 AVAILABLE，返回同一原文及摘要；未关联任何应用的版本同样可用。历史已发布版本可凭精确 ID 获取，不因 head 变更而替换。ClearHead 使资源退出独立推荐列表，仍保留历史精确获取；Suspend 阻断两者。

未发布/不存在目标统一不可获取，不泄漏待审正文或私有管理信息。

## 正式分发接口

2026-11-07 用户接受具体接口与既有 UC 修订，2026-11-08 落实。`app_center.v1.script_distribution.ScriptDistributionService` 提供下列四个方法。表中为 App 内部路径，Gateway 对外增加 `/app-center`，使用普通 PUBLIC surface、强制 Session 和可信 App ACTIVE USER；不要求脚本管理权限。HTTP、原生 gRPC、gRPC-Web 共享语义，所有成功与错误响应均 private, no-store。

| 方法 | HTTP | 输入 |
| --- | --- | --- |
| ListPublishedScripts | GET `/v1/scripts` | 可选 limit、cursor |
| GetPublishedScriptContent | GET `/v1/scripts/{resource_id}/versions/{version_id}/content` | 必填 expectedDigest query |
| ResolveApplicationScriptManifest | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts:resolve` | `{runtime}` 正文 |
| GetApplicationScriptContent | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts/{script_version_id}:getContent` | `{runtime, expectedDigest}` 正文 |

`runtime` 为 `{mode, hostRpcApiMajor, hostCapabilities[]}`。mode 必须显式为 PURE_TEST 或 UNIFIED，缺失/UNSPECIFIED/未知值拒绝。PURE_TEST 复用 [UC012](UC-APP-012-resolve-test-launch-target-for-tester.md)，UNIFIED 复用 [UC023](UC-APP-023-resolve-unified-launch-target.md)。major/capabilities 沿用既有格式、数量、去重排序和长度限制。请求不接受可信身份、channel、Membership、cohort 或命中结果。

应用入口在同一个 snapshot 内重新解析并比较目标 versionId 与 applicationVersionId。目标相同且当前有资格时可使用该 snapshot 的新 publicationRevision，不要求客户端锁定整份旧 Publication；换成其他版本则统一不可获取，不替换请求。正文请求没有重复 resourceId，由批准依赖唯一确定关系。

读取投影、排序、分页和各入口组合见[运行脚本读契约](../query-contracts/script-distribution.md)。它引用本 UC 的 BR，不另定义发布、审核或运行资格。新接口不增加用户可见管理历史、永久下载 URL 或客户端 Runner。

## 内容与传输预算

首期每次返回一份完整 `contentText` 与精确描述符，不分块，不合并16份正文。原文上限1 MiB，沿用 [BR-SCR-005](UC-APP-042-manage-script-version-draft.md#br-scr-005) 的原字节与既有 SHA-256 表示。HTTP 使用标准 Proto JSON，解码后保留 BOM、CRLF、空白等原始 UTF-8 字节，不重新序列化 JSON，不执行脚本。expectedDigest 必填并严格校验格式；格式合法但值不同按统一不可获取，不披露真实摘要。

HTTP JSON 响应最坏转义预算为 `6 × 1 MiB + 16 KiB`，原生 protobuf 单份文本与描述符在4 MiB消息预算内。gRPC-Web 用同一 protobuf；三协议必须用接近原文上限且包含高转义密度的真实文本验收。请求正文上限16 KiB，GET 只接受声明 query，POST 不接受 query 覆盖正文、未知字段或多份 JSON。

## 事实一致性与写入排序

读取在原入口的身份/候选隐藏边界后，验证精确批准 Version/Review/decision、永久发布资格及首次来源事件、资源 AVAILABLE，以及文本 format/digest/byteLength。合法 APPROVED 但从未发布，或已知 SUSPENDED，是正常不可分发。本应存在的批准/发布来源缺失、跨资源、描述符冲突或摘要损坏是不变量异常，不能当作普通未发布。head 不参与历史精确资格的选择或替换。

一次读取的全部必要来源在同一 majority read-only snapshot 内，与暂停/恢复或换槽观察提交前后的完整组合；查询不写 coordinationRevision。实际应用槽位发布及 Grey 比例变化在最终事务复核依赖，并按 [ADR008](../adr/ADR-008-script-dependency-transactions-and-cascade.md) 对所有资源共享门禁取得真实写栅栏，与 Suspend 确定排序。失败不能留下 Publication revision、History 或部分脚本 fence。

清空槽位仍允许。匹配 OCC 的相同槽位/比例 no-op 保持原幂等行为，不新增发布事实，不赋予运行资格；在线读取继续核验脚本。旧 revision 先按原 OCC 冲突处理。DECREASE 免除的外部 Scope/URL 复检不免除本地脚本依赖门禁，Clear 不依赖该门禁。

## 既有入口的稳定映射

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

## 新接口错误

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信 ACTIVE USER | 复用既有 USER 身份错误 | 401 / UNAUTHENTICATED |
| 非法 ID、mode、runtime、digest 格式、limit 或 HTTP 输入 | INVALID_SCRIPT_DISTRIBUTION_REQUEST | 400 / INVALID_ARGUMENT |
| cursor 损坏、用途或绑定不匹配 | INVALID_SCRIPT_DISTRIBUTION_CURSOR | 400 / INVALID_ARGUMENT |
| 目标不存在、未批准、未发布、暂停、摘要不匹配，或应用目标/运行资格不成立 | SCRIPT_CONTENT_UNAVAILABLE | 404 / NOT_FOUND |
| 已读必要事实损坏 | SCRIPT_DISTRIBUTION_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储/snapshot/依赖不可用 | SCRIPT_DISTRIBUTION_UNAVAILABLE | 503 / UNAVAILABLE |

新应用内容接口统一隐藏目标与资格，不携带真实摘要、正文或私有管理信息；原 UC012/023 公共 RPC 仍用各自错误。独立列表无候选成功空数组，损坏整页失败。

## 验收

- 应用关联入口：未发布、暂停、未授权 Tester、错误 cohort、旧换槽目标、错误摘要与无关版本请求不能取得正文。
- 上述 Tester/cohort/目标条件适用于应用关联入口；独立入口仅分发已批准且已发布的 AVAILABLE 脚本，不能因此启动原无权应用。
- 未关联应用的已发布脚本可独立查询/下载；普通用户不取得未发布正文，匿名请求失败。
- 人工审核批准应用可发生在脚本发布前，但应用发布在脚本可分发前被阻止。
- B 成为 head 后 A 的引用/正文/摘要不变；服务不执行 JSON，不静默返回另一格式。
- 暂停和目标/内容读取竞争有确定序列；客户端已下载文本的撤回不在后端承诺内。
- Test、Stable、Grey 新发布和 Grey 实际比例调整复核全部依赖，任一失败整体回滚；清空与匹配 no-op 保持既有语义。
- 原候选仅因 capability 不足时仍可按原规则选择；已选择候选因脚本不可分发不能降级，普通目录隐藏、本人的纯 Test 参与卡片保留。
- 近1 MiB 高转义密度文本经 HTTP、原生 gRPC、gRPC-Web 恢复原字节；同时间分页、调用者绑定和空依赖明确返回。
