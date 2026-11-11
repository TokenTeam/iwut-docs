# UC051 平台 Application 目录实施记录

状态：`COMPLETE`。2026-11-08。UC050 完整backend 24/24及固定三镜像关闭后，按用户接受的 UC051 / BR-APP-063–066 串行实施。Auth UC039与UC027/010已由其owner实现并验证；本工作包只消费精确 `app.application.search`，不改Auth/Gateway/Console源。

## 实现

Application能力新增Domain/Port/UseCase与独立ApplicationPlatformQueryService。搜索和最小详情均先验证可信USER及精确search权限；无平台管理员、Reviewer、owner、Developer、suspend/restore隐式授权。HTTP入口在JSON解析前同样检查身份/权限，成功和错误private,no-store。未知字段、非法状态、ID/名称前缀、大小/游标边界均拒绝；POST单对象16KiB，无query覆盖；GET无body/query。

同一majority只读snapshot只投影Application核心字段和内部nameKey，不读Auth或下级Version/Profile/Review/OAuth/配额/计数等。严格校验BSON必要类型、规范名称/ID、三个独立状态维度及其revision，必要损坏整页/详情500，存储503，不伪装为空。

名称按既有规则规范化为nameKey；精确Application/owner、前缀和三个状态维度AND组合。nameKey/id升序keyset；HMAC用途、版本、主体摘要、规范过滤摘要和位置绑定，空状态维度等价规范化，pageSize可改变。底层一次最多500条候选，逐条校验后按状态过滤；短/空页可继续，不跳过已取得但尚未返回的合法项。0042显式迁移增加全平台name/id、owner/name/id命名索引，查询选定索引，保留既有唯一与业务索引。readiness与完整迁移链测试同步。

Proto独立namespace与输入/生成物一起本地提交 `a57bb969f20141a183942a28e529c5c21ee5cc79`，基于统一7091db7。GET请求的application_id明确json_name以使正式Kratos生成HTTP client正确绑定路径；不增加query别名或兼容路由。Wire由生成器更新。

## 规则与自动验证

| 规则 | 验证 |
| --- | --- |
| BR-APP-063 | UseCase/transport身份先于参数；无grant/suspend/restore/Reviewer/平台管理员等组合；正常Wire不授予操作权；真实Auth授撤待三镜像 |
| BR-APP-064 | 真实Mongo全部12种独立状态组合、无公开资料/版本、精确ID/owner/前缀AND、核心最小白名单 |
| BR-APP-065 | 500候选空页继续、同key不同owner、改变pageSize不跳项、主体/过滤/用途/MAC/编码/尺寸；有界caller摘要 |
| BR-APP-066 | 必要损坏/BSON类型整页与详情500，存储503；实际find/getMore间提交owner/生命周期变化，前后完整snapshot；HTTP/native及正式生成client |

首轮真实Mongo专项30.584秒通过，含迁移复验的扩大专项45.730秒通过。初次Wire专项暴露测试复用响应头丢身份、以及生成GET路径字段编码问题，修正后正常Wire HTTP/native及生成HTTP client6.416秒通过。最终索引hint输入专项Mongo race46.320秒、正常Wire HTTP/gRPC9.798秒通过，go test ./...通过；App本地提交 `fb8d9de6ac050e3f323ce6964395ea274387a48c`，API `a57bb969f20141a183942a28e529c5c21ee5cc79`。API已统一，Gateway及固定三镜像均通过，最终重跑完整backend已通过，首轮失败与修正记录分开保留。

三镜像夹具使用Auth正式注册、设备登录、平台管理员bootstrap及独立权限授撤；仅受控Developer资格seed。已在同一Session下证明none/suspend/restore仍403、grant search后三协议可读、撤销其他操作权限不影响search、search不赋写权、撤search后新签发请求403，以及ADMIN/Developer surface隔离。入口 `scripts/test-uc002-gateway-auth-integration.sh --platform-applications`。

## 固定输入与集成验收

App `fb8d9de6ac050e3f323ce6964395ea274387a48c` / API `a57bb969f20141a183942a28e529c5c21ee5cc79`，Gateway `9de4e70e13f1c7e28c11cf48a6c56b5c83cfd9a7`。三处API干净同tree `d7c9a7b5b480c412f99cfd64588e96e3dbda6984`；Auth业务指纹仍为 `6e680a1e57005d31ecf4e192b19df864fc420d53a8df4346ee3ff01d15dacf7f`，原未提交工作保留。

Gateway163路由make check及完整协议/Console E2E通过；App侧 `TestE2E_UCAPP051_PlatformApplicationsLocalImages` 真实授撤/本人发现/三协议/ADMIN与Developer隔离通过，包race2.387秒。复用既有permissions列表、Session与JWS协议，不改App Auth client或共享身份格式，本轮完整tier为backend并补上述真实Auth业务链，不把历史跨服务tier报告混作当前证据。

- App `iwut-app-center:platform-directory-fb8d9de` / `sha256:8d2a2bb093a20c1a89ad97d33d205e03692ec34c72c466f996160402e899f15f`。
- Auth `iwut-auth-center:search-local-uc051-a57bb96-6e680a1e5700` / `sha256:2175b7d0d1f4d3cd22ef5cd3ddc9c9f96a3ae4f32d4031578ed85d82a71dccfc`。
- Gateway `iwut-gateway:platform-directory-9de4e70` / `sha256:f4bb4042b23a46225c73efb6d1c932364af806cbb574a8e5851fa9b9116a0e43`。

本UC所有提交及镜像均保留本地，未push/部署。完整backend固定报告见下节。

## 首轮完整门禁及测试清单修正

冻结App fb8d9de/API a57bb96/docs a51be29的完整backend首轮未通过：23项通过，最后Mongo/E2E项仅 `TestMigratorIntegration_IsIdempotentAndCreatesNamedSchema` 失败，旧精确索引清单漏登记0042的两个新索引。Mongo2255.579秒，HTTP/gRPC E2E254.562秒；`changed_sources=[]`。报告 `.artifacts/verification/20261108T074553Z-26y6xanq/report.json` 保留为失败证据，不记作交付。已补上两个正式索引名称，保留原精确断言；仅测试文件修正，无业务、Proto或迁移变更。先重跑全迁移链与UC051专项，再冻结重跑完整backend。

扩大后的全部MigratorIntegration、旧转让迁移及UC051专项通过：Mongo race56.037秒、正常Wire9.365秒；go test ./...通过。仅测试断言的跟进提交 `3c611d910f605cfc394726095926d3d21607bf2c`，相对fb8d9de只有 `internal/adapter/mongo/application_repository_integration_test.go` 一行新增预期索引；生产镜像输入仍为fb8d9de/API a57bb96，测试文件由Docker构建上下文明确排除，镜像及原固定三镜像证据继续有效。最终完整backend在3c611d9上重新冻结，首轮失败不能替代重跑结果。

## 最终完整验收

Go1.25.5，App `3c611d910f605cfc394726095926d3d21607bf2c` / API `a57bb969f20141a183942a28e529c5c21ee5cc79` / 独立本地docs snapshot `86c2cc4d6ed70cdd0d0bd5bfb01d9ae084f5c696`。修正上述一行测试清单后重跑 `make check-full`，backend **24/24 PASS**，`changed_sources=[]`；Mongo race2112.872秒，HTTP/gRPC E2E251.220秒。报告 `.artifacts/verification/20261108T082730Z-4t2vdlik/report.json`。App/API工作区干净，生产镜像仍对应未变化的fb8d9de运行内容。

用户已接受Console owner的[UC014/015修订草案](../../console/design-notes/2026-11-08-search-and-incoming-transfer-proposal.md)，已通知其先更新权威UC再串行实现。Console实现及发布由其owner记录，不作为App后端未实现项；本记录不预先宣称前端验收通过。
