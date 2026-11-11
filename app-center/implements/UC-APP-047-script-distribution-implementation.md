# UC047 精确脚本分发与联合门禁实施记录

状态：`COMPLETE`。2026-11-08。用户已接受[具体修订方案](../design-notes/2026-11-07-uc047-runtime-script-contract-proposal.md)。UC046 完整门禁24/24通过后，已串行落实 UC047、UC007/012/019/020/021/023/024/038、[运行读契约](../query-contracts/script-distribution.md)及对应生成 brief；App/API、Gateway接入、专项、固定三镜像联验和完整后端门禁均已完成，24/24通过，`changed_sources=[]`。

## 实现与不变量

应用实际发布在现有 Publication transaction 中复核批准 Review 的精确依赖、注册关系、批准时保存的脚本 decision、永久首次发布事实和 AVAILABLE，并按资源 ID 顺序真实递增共享 gate fence。Test、Stable、Grey 设置/替换及实际比例调整均消费门禁，DECREASE 不要求外部 Scope/URL 复检但仍执行本地脚本门禁。Clear 继续允许，匹配 OCC 的 no-op 不增加事实，旧正 revision 继续冲突；失败不留下 Publication、History 或部分脚本 fence。

在线 Test、统一启动、普通 Catalog、本人测试和两个 OAuth 运行查询消费同一事实检查。原身份、capability、major 和 cohort 分支保留；被选目标的脚本不可分发时不换版本回退。Catalog 同时检查 Stable 基线及实际目标，正常不可分发隐藏项，损坏整次失败。本人测试保留参与卡片，新增 SCRIPT_DEPENDENCY_UNAVAILABLE。OAuth runtime tuple 不变，sector 回调并集查询保持原职责。

页面读取按最多16份脚本版本/审核原文一批验证，批间只保留描述符、门禁和来源证明，不保留整页正文。反向关系按精确键有界读取，缺永久资格的历史检查在数据库中按精确版本分组，不把无界发布历史载入内存。所有读取保持同一次 majority snapshot，不写访问记录或 coordinationRevision，不调用 Auth Scope Catalog/DNS。

独立内容在读取正文/私有审核前先确认永久发布事实，未发布/不存在统一不可获取。丢失永久资格但仍有历史公开发布事件是损坏，不伪装为从未发布。精确获取不读取或跟随当前 head；ClearHead、换 head 不改历史精确资格。应用内容每次重新解析当前 PURE_TEST/UNIFIED 目标并整体复核全部依赖，旧 manifest 不承载资格。

复用现有0040及此前的 schema/index，没有兼容/backfill、Runner、离线缓存协议或新的 Auth permission。宿主能力声明的原有集合语法抽为 shared 纯值校验，Catalog 和 Script 的 Domain 不互相导入；权限验证与正文 SHA-256 校验在各自边界保留。

## API 与 Gateway 交接

新增 `app_center.v1.script_distribution.ScriptDistributionService`，四条均为 PUBLIC surface、Session REQUIRED，普通 ACTIVE App USER，不要求脚本管理/Developer/Tester 权限才能独立读取。应用关联入口另按本人的运行资格复核。对外路径增加 `/app-center`。

| RPC | App HTTP |
| --- | --- |
| ListPublishedScripts | GET `/v1/scripts`，limit/cursor |
| GetPublishedScriptContent | GET `/v1/scripts/{resource_id}/versions/{version_id}/content`，expectedDigest |
| ResolveApplicationScriptManifest | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts:resolve`，`{runtime}` |
| GetApplicationScriptContent | POST `/v1/applications/{application_id}/versions/{application_version_id}/scripts/{script_version_id}:getContent`，`{runtime,expectedDigest}` |

Proto JSON 的 runtime.mode 使用 SCRIPT_RUNTIME_MODE_PURE_TEST / SCRIPT_RUNTIME_MODE_UNIFIED；UNSPECIFIED、未知枚举、未知字段和用户自报身份/channel/cohort 均拒绝。POST 正文16 KiB上限，GET只允许声明 query。所有成功与错误 private, no-store。原文最多1 MiB，单次一份，HTTP最坏 JSON 转义预算 `6 MiB + 16 KiB`，原生 protobuf/gRPC-Web沿用单份消息。客户端解码后按原UTF-8字节核验摘要，不规范化或解析执行。

应用发布新增 APPLICATION_SCRIPT_DEPENDENCY_UNAVAILABLE（422 / FAILED_PRECONDITION）及 APPLICATION_PUBLICATION_UNAVAILABLE（503 / UNAVAILABLE），分别为合法不可分发与存储故障。本人测试枚举新增 TEST_AVAILABILITY_SCRIPT_DEPENDENCY_UNAVAILABLE。新分发接口的 reason 及原入口映射见 UC047 权威表。

正式生成 HTTP 客户端验证发现既有 Script 与 ApplicationPublication 的 URI参数没有显式 json_name，Kratos form encoder 会按 camelCase 编码，留下空 snake_case URI并把 ID放进 query。本轮只给 URI参数补齐精确名字，原生字段号、业务路径和命令语义不变，不引入别名或兼容层。新 expectedDigest query 显式使用其声明名字；已增加实际框架 encoder 与正式生成 HTTP client 回归。

Gateway 已按最新固定 API 增加四个 PUBLIC 路由、HTTP/原生 gRPC/gRPC-Web typed adapters，保持强制 Session、身份清洗及 no-store；不生成 Developer/Admin Console surface。既有 ADMIN 脚本管理路由保持原分工。Auth 无新增业务权限，已按 API 对齐后的同一提交重建本地联验镜像。

## 当前验证

按串行顺序完成的专项：

- 发布门禁、三个槽位、Grey 下调及 App 发布/Suspend 两个提交胜序通过，Mongo race 28.655秒。
- 在线消费与原目录/本人测试/Grey 相关回归通过，Mongo race 68.764秒；包含不可分发不回退、损坏不隐藏、capability 优先分支及 sector 不变。
- 独立精确文本、未发布私有事实隐藏、500扫描/同时间分页/游标绑定、暂停并发 snapshot 通过，Mongo race 24.905秒。
- 应用 manifest/content、Tester/cohort/模式/换槽、head 变更和显式空依赖通过，Mongo race 6.487秒。
- 正常 Wire 启动 HTTP/原生 gRPC 与正式生成客户端通过，E2E 10.247秒；包括 App 批准先于脚本发布、实际发布阻断、普通无角色 USER、重新核验、嵌套未知字段，以及1 MiB高转义密度原文的生成上传/HTTP下载/native下载。
- 多依赖回滚、资源 fence 排序、16项清单和跨应用批量读取通过，Mongo race 14.398秒；包含最终 History 写失败的所有 gate/Publication 回滚及单项暂停拒绝整个 manifest。
- `go test ./...`、格式/Wire/Proto 生成漂移检查及82份 brief / 408行 registry 检查通过。最终组合专项通过：Mongo race 125.252秒、正常 Wire E2E 13.035秒，包含新增业务422的实际HTTP映射。固定三镜像已通过98.72秒：真实Auth注册/设备Session、权限独立授撤、人工审核发布，以及无脚本角色USER的HTTP/native/gRPC-Web近1 MiB高转义正文；完整backend最终24/24通过。

历史夹具编译/边界数据失败不作为最终通过证据；最终源码已固定，以下记录本次输入与完整验收。

## 固定本地输入

App `bff03181589838141c73ea63730a96730f159ce9`；API `01f2ecb633120662d9a74d0263d9aebda37b6e16`。两者已分别提交，无 push。三处API对齐、Gateway接入已由各自owner完成。App最终测试夹具提交 `64a8a06699bc752d92358aa842d263c1617354ed`，仅改匿名空Session泄漏断言，业务源码与镜像 `bff0318` 完全一致；App/API工作树干净。

Gateway `e2293ca32c4e3debc947b15a3fb440c2a339b2ec`，make check及完整protocol-e2e通过，31条App路由完成HTTP/native/gRPC-Web验证；四个分发PUBLIC路由强制Session且无Console surface。Auth HEAD `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f`，保留既有dirty业务源，指纹 `22298e2e70f8306d616e13199ba3dd9b66bd079aa49f03bff6a4539072d3c6a9`，构建前后相等；无新权限或业务变更。

固定镜像：

| 服务 | 本地标签 | Image ID |
| --- | --- | --- |
| App | `iwut-app-center:script-distribution-bff0318` | `sha256:e1363b72fc93febae4c4522f573048c90f5ea0ad281dde1c8dd0537470716c2d` |
| Gateway | `iwut-gateway:script-distribution-e2293ca` | `sha256:9eb65645da5fad28bbd0bd9c902344f9627879a212a71eb1b6073df69b4a366c` |
| Auth | `iwut-auth-center:script-local-uc047-01f2ecb-22298e2e70f8` | `sha256:f7bd0572c94821a6919273ad3a3173cb94d1cb3d585c5a6e1daeb06cf15312a5` |

App忽略制品 `.artifacts/script-distribution-uc047/three-image-test-2.log` 记录最终通过；应用manifest/content正向由正常Wire与Mongo矩阵覆盖，此三镜像夹具验证独立分发正向和应用入口真实Session/统一目标隐藏边界，不将未执行的应用正向三镜像场景计为通过。首轮匿名夹具把空字符串当作凭据，误判泄漏；修正后重跑通过，不更改生产接口。完整门禁冻结在最终测试提交和新的已提交docs快照。

## 完整门禁与覆盖

最终 `GOTOOLCHAIN=go1.25.5 make check-full` **24/24 PASS**，报告位于 App 工作树 `.artifacts/verification/20261107T175055Z-mczjna6t/report.json`，`changed_sources=[]`。执行时间为UTC 2026-11-07 17:50:55–18:26:11，最后一项2100.535秒：Mongo race包2094.242秒、正常HTTP/gRPC E2E包249.802秒。该backend报告本身不包含真实Auth进程；真实Session链和三协议正文另由前述固定三镜像测试证明，不混用验收层级。

冻结App为 `64a8a06699bc752d92358aa842d263c1617354ed`，API为 `01f2ecb633120662d9a74d0263d9aebda37b6e16`，已提交的独立docs快照为 `c2afebed6daaf3cf9e5e5b4af1677f4fb527118f`。三个来源起止HEAD、dirty状态和内容指纹相同；App/API干净，owned验收容器已清理。快照是忽略制品目录中的独立仓库，没有使用docs main作为worktree。最终证据清单为 `.artifacts/script-distribution-uc047/delivery.json`。代码、镜像与快照均为本地结果，没有push或部署。

| 权威规则 | 自动覆盖 |
| --- | --- |
| BR-SCR-019 | `TestScriptDistributionManifestIntegration_UCAPP047_BRSCR019021`、`TestScriptDistributionBatchIntegration_UCAPP047_BRSCR019020`：精确批准依赖、空列表、规范顺序、16项与整体验证 |
| BR-SCR-020 | `TestScriptDistributionPublicationIntegration_UCAPP047_BRSCR020`、`TestScriptDistributionPublicationConcurrencyIntegration_UCAPP047_BRSCR020`、`TestScriptDistributionAtomicMultiDependencyIntegration_UCAPP047_BRSCR020`、runtime/OAuth专项：发布/暂停排序、回滚、Grey下调、no-op/OCC与各在线入口 |
| BR-SCR-021 | manifest/content/snapshot专项及正常Wire E2E：本人资格、当前目标、重新校验、精确原字节；固定三镜像覆盖近1 MiB高转义内容的三协议传输 |
| BR-SCR-022 | `TestScriptDistributionContentIntegration_UCAPP047_BRSCR021022`、`TestScriptDistributionPagingIntegration_UCAPP047_BRSCR022`、固定三镜像：独立普通USER、head/历史、未发布隐藏、500扫描及游标绑定 |

UC047后端范围关闭，UC041–049的本轮App后端串行工作全部完成。Console/客户端Runner、机器自动检查、Lua格式和离线缓存协议没有纳入本轮实现。
