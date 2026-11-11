# UC047 运行脚本接口与联合门禁修订草案

状态：`ACCEPTED`。2026-11-07 用户接受本文草案并要求继续。UC046 完整门禁24/24通过后，已串行落实到既有 UC 权威正文、运行读契约和 UC047 实施 brief，并完成实现与完整验收。最终证据见[UC047实施记录](../implements/UC-APP-047-script-distribution-implementation.md)；本文保留当时的审核范围，后续行为以对应权威 UC 为准。

## 审核范围

[UC047](../use-cases/UC-APP-047-resolve-application-script-content.md) 的独立分发、固定应用依赖和在线门禁已接受。本文固定它要求在实施前明确的传输形态、已有入口的错误/隐藏语义，以及既有 UC 的修订位置。用户已接受本次具体修订；先落实到对应 UC、运行读契约和生成 brief，再串行实现。

独立内容向 ACTIVE 登录用户开放；应用关联接口继续验证本人的当前应用运行资格。两个入口都读取同一份获批原文与永久发布事实，不新增执行器、离线缓存协议或旧接口兼容分支。

## 四个分发接口

新增 `app_center.v1.script_distribution.ScriptDistributionService`。Gateway 使用普通 PUBLIC surface、强制 Session，交换 App USER 身份。接口不要求五项脚本管理权限，不向 Developer/Admin Console 自动增加页面。所有成功与错误响应均为 `Cache-Control: private, no-store`。

下表是 App 内部 HTTP 路径；Gateway 对外统一增加 `/app-center` 前缀。同一 Proto 同时提供 HTTP、原生 gRPC 和 gRPC-Web。

| 方法 | HTTP | 输入 |
| --- | --- | --- |
| ListPublishedScripts | GET `/v1/scripts` | 可选 limit、cursor |
| GetPublishedScriptContent | GET `/v1/scripts/{resource_id}/versions/{version_id}/content` | 必填 expectedDigest query |
| ResolveApplicationScriptManifest | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts:resolve` | runtime 正文 |
| GetApplicationScriptContent | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts/{script_version_id}:getContent` | runtime、expectedDigest 正文 |

`runtime` 包含 `mode=PURE_TEST|UNIFIED`、`hostRpcApiMajor` 和 `hostCapabilities[]`。mode 必须显式选择，UNSPECIFIED/未知值拒绝。PURE_TEST 复用 UC012，UNIFIED 复用 UC023；请求只能选择入口语义，不能指定 channel、cohort、Membership 或可信 authId。major/capabilities 沿用现有格式、去重排序及长度限制。

应用入口在同一个只读 snapshot 中重新解析运行目标，再确认其 versionId 等于 path 中 applicationVersionId。相同版本仍在当前合法目标上时，可以使用新 snapshot 的 publicationRevision；不要求客户端锁定已过时的整份 Publication。实际选中另一版本时统一不可获取，不替换请求目标。mode 选择不会绕过 ACTIVE Tester、Grey cohort、RPC major、能力及 Application 在线门禁。

### 结果与最小披露

独立列表只返回资源 `resourceId/name/purpose` 与当前 head 的 `versionId/versionLabel/contentFormat/digest/byteLength`，不返回正文、审核/运维理由、人员、内部 revision 或未发布版本。只列 AVAILABLE、head 非空且批准/首次发布事实完整的资源。元数据是查询时当前资源元数据，版本描述符是精确发布事实。

列表按资源 `createdAt + resourceId` 稳定倒序，limit 默认20、范围1–100。签名 cursor 使用独立用途并绑定可信调用者及过滤条件，记录最后已消费资源位置；每页重新校验 gate。扫描上限500、单页响应预算2 MiB，可返回短页/空页并附下一游标，不越过尚未返回的合法项。不存在 totalCount、offset、跨页冻结或持久化读取副作用。

manifest 返回 `applicationId/applicationVersionId/publicationRevision/channel/rpcApiMajor`、`scripts[]` 和 `asOf`。每个脚本只返回 `resourceId/versionId/contentFormat/digest/byteLength`，顺序采用既有规范化依赖顺序。清单来自批准 Version 与批准 Review 的同一精确依赖，最多16项；合法空依赖显式返回空列表，缺失/损坏不能按空列表处理。返回前整体校验全部依赖，不返回部分清单。

两种 content 响应都包含精确描述符及 `contentText`；应用响应另携带其本次目标身份和 publicationRevision。每次内容请求独立重验整个应用依赖集合及所请求脚本，不能用先前取得的 manifest、永久 URL 或客户端提交的 descriptor 充当资格。应用 path 无需重复 resourceId，由已批准依赖唯一确定资源关系。

### 字节与传输预算

首期每次返回一份完整文本，不分块，不把16份正文装入单个响应。原文最大1 MiB，沿用 BR-SCR-005；UTF-8 字节、CRLF、空白等全部保留，不重新序列化 JSON。digest 为既有精确原文 SHA-256 表示，expectedDigest 必填且格式严格校验；相同格式而值不匹配按目标不可获取处理，不披露真实摘要。

HTTP 使用标准 Proto JSON，`contentText` JSON 解码后恢复原始文本；不增加 raw/压缩下载或可缓存 URL。JSON 转义最坏情况按 `6 × 1 MiB + 16 KiB` 响应预算验收，原生 protobuf 单份1 MiB 加元数据在4 MiB消息预算内。请求正文上限16 KiB，GET 只接受声明的 query，POST 不接受 query 覆盖正文、未知字段或多份 JSON。HTTP、原生 gRPC、gRPC-Web 必须用接近上限且包含高转义密度的真实文本共同验证，不能仅证明小样本成功。

## 统一事实检查与并发

读取依次验证可见目标、批准 Version/Review/decision 一致、首次发布资格及来源事件一致、资源 AVAILABLE、原文格式/字节数/摘要一致。合法 APPROVED 但从未发布，或已知 SUSPENDED，属于正常不可分发；本应存在的批准/发布来源记录缺失、跨资源、描述符冲突或摘要损坏属于内部不变量异常。存储、超时或 snapshot 故障不当作不存在/暂停。

一次读取的全部来源使用同一 majority read-only snapshot，与 Suspend/Restore、head 变化或换槽并发时观察提交前或后的完整组合。查询不写 coordinationRevision。ClearHead 不影响历史精确获取与应用固定依赖，切换 head 不改变 manifest。已经发出的内容不承诺追回；后续新请求重新检查。

App 放入/替换 Test、Stable、Grey，或实际调整 Grey 比例时，在提交事务内检查所有精确依赖，并使用 ADR008 的共享资源 gate 写栅栏与 Suspend 排序。事务失败不得留下 Publication revision、History、部分脚本 fence 或外部成功回执。清空槽位继续允许。已有相同目标/比例且匹配 OCC 的 no-op 保持既有幂等语义，不新增发布事实；它不能产生新的可运行资格，在线读取仍检查脚本门禁。旧 revision 先返回原 OCC 冲突。

## 既有入口的结果映射

下表中的“不可分发”指合法的未发布或暂停；损坏和依赖故障另按各入口既有分类处理。所有检查发生在原入口的身份/候选隐藏边界之后，不为未授权者探测 Test/Grey 或脚本私有管理状态。

| 入口 | 合法脚本不可分发时的结果 | 损坏与依赖故障 |
| --- | --- | --- |
| UC007/020/021 应用发布 | 新增 `APPLICATION_SCRIPT_DEPENDENCY_UNAVAILABLE`，HTTP422 / FAILED_PRECONDITION；不推进 revision/History | 完整批准关系不一致复用 review-state inconsistent，发布资格/gate 不变量复用 publication-state inconsistent；存储故障503，不按业务422处理 |
| UC012 纯 Test 解析 | 复用 `APPLICATION_TEST_TARGET_UNAVAILABLE`，404 / NOT_FOUND，无降级 | 已读损坏沿用 test-publication inconsistent，503 / UNAVAILABLE；依赖故障维持服务不可用 |
| UC023 统一解析 | 原身份/major/capability 选择出的目标依赖不可分发时，复用 `APPLICATION_LAUNCH_TARGET_UNAVAILABLE`，404 / NOT_FOUND；不再尝试低优先级版本 | 损坏500 / INTERNAL，服务故障按既有内部失败；不返回部分 descriptor |
| UC024 普通 Catalog | Stable 基线脚本不可分发则不入候选；合格基线上最终选中 Test/Grey 的脚本不可分发也不返回该项；详情统一 PUBLIC_APPLICATION_NOT_FOUND | 已读损坏整页/详情500；存储故障整次失败，不静默丢项 |
| UC038 本人测试卡片 | 在公开资料、有效 Test 和 capabilities 检查之后，增加 `SCRIPT_DEPENDENCY_UNAVAILABLE` availability；保留参与卡片，隐藏 launchTarget，missingCapabilities 为空 | 损坏 MY_TEST_APPLICATION_STATE_INCONSISTENT 500；存储 MY_TEST_APPLICATION_UNAVAILABLE 503，不能变成普通卡片 |
| UC019 OAuth 运行配置与用户授权上下文 | 复用 `OAUTH_CLIENT_RUNTIME_UNAVAILABLE`，422 / FAILED_PRECONDITION；固定渠道，不增加回退 | 不变量 OAUTH_CLIENT_STATE_INCONSISTENT 500；依赖 OAUTH_PROVIDER_UNAVAILABLE 503；不改 runtime tuple |

UC023 原有的无 Membership、无 Test、Grey 未命中及 capability 不足分支仍按原规则选择。脚本检查作用于原规则所需的当前候选，不为已被能力条件排除的私有候选额外读取正文，也不能把脚本不可分发当作新的 capability 回退理由。

UC024 的 Stable 仍独立承担普通目录候选资格，不能因本人 Test 可运行而绕过不可分发 Stable。该入口继续分发原有 Filter；manifest/content 接口不负责执行 Filter。UC038 继续纯 Test 且不执行 Filter，新增卡片状态不改变 Membership。

UC019 的 `GetClientConfiguration`、`VerifyClientSecret` 和 `GetApplicationPublishedRedirects` 维持既有职责；sector 回调并集查询不是运行授权，脚本暂停不删改其已批准槽位回调。`ResolveClientRuntimeConfiguration` 与 `ResolveAuthorizationContext` 两次均检查 gate，Auth 后续已有的重新解析继续生效。已下载文本、已签发 token 或现有 consent 不增加后台批量撤销任务。

## 新接口稳定错误

| 条件 | 新 ScriptDistribution reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信 ACTIVE USER | 复用现有 USER 身份错误 | 401 / UNAUTHENTICATED |
| 非法 ID、mode、runtime、digest 格式、limit 或 HTTP 形状 | INVALID_SCRIPT_DISTRIBUTION_REQUEST | 400 / INVALID_ARGUMENT |
| cursor 损坏、用途或绑定不匹配 | INVALID_SCRIPT_DISTRIBUTION_CURSOR | 400 / INVALID_ARGUMENT |
| 内容目标不存在、未批准、从未发布、暂停、digest 不匹配，或应用请求目标/资格不成立 | SCRIPT_CONTENT_UNAVAILABLE | 404 / NOT_FOUND |
| 已读必要事实损坏 | SCRIPT_DISTRIBUTION_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储、snapshot、依赖服务不可用 | SCRIPT_DISTRIBUTION_UNAVAILABLE | 503 / UNAVAILABLE |

独立列表无合法候选成功空数组；损坏整页失败。新应用内容接口的404统一隐藏目标和资格细节，底层 UC012/023 公共 RPC 继续使用各自既有错误表。输入不合法仍按400区分，不用真实目标内容补全请求。错误不携带脚本正文、真实摘要、运维理由或其他用户身份。

## 接受后的文档与交付顺序

| 权威输入 | 接受后修改 |
| --- | --- |
| UC047 | 固定四个方法、mode、结果、大小、分页与错误，引用已有 BR-SCR-019–022 |
| 新运行脚本 query-contract | 收敛读取语义与各消费入口映射，引用上述 UC，HTTP/存储细节保留在接口实施交接 |
| UC007/020/021 | 发布前置、写栅栏、清空/no-op/OCC、稳定业务失败及验收；替换旧“脚本不参与发布”的说明 |
| UC012/023 | 同一快照的依赖 gate、原候选顺序、脚本不可用无回退、错误与验收 |
| UC024 | Stable 与实际目标双层门禁、列表隐藏/详情404、故障和损坏不隐藏 |
| UC038 | 新 availability、投影优先级、同快照/批量读取及损坏边界；重新生成 API 枚举与对应 brief |
| UC019 | 两个运行查询复核脚本、既有错误和 tuple、sector 查询职责；移除已被 UC020/021 和正式 Scope Catalog 替代的过时依赖说明 |
| UC048 brief 与相关实现导航 | 引用最新发布/运行契约，不重定义脚本审核依赖规则 |

先完成并检查权威正文、registry 和所有受影响 brief，再实现 App 原子发布门禁，接着实现共享在线读取和四个分发接口。测试串行执行发布并发专项、运行/Catalog/本人测试/OAuth 专项、正文与分页专项、完整后端门禁。代码固定后按用户 API 流程交 API 对齐和 Gateway；相邻模块由对应 agent 实现，最后用固定本地三镜像完成真实协议与资格联验，不 push。

验收至少覆盖空依赖、16项全有/一项暂停、批准先于脚本发布、A→B→ClearHead 后精确 A、两种模式的 Tester/cohort/能力/换槽差异、错误 digest、未发布正文隔离、暂停与读取/应用发布两个提交胜序、同一 snapshot 不混合、损坏整页失败、最大字节传输和无旧模型兜底。
