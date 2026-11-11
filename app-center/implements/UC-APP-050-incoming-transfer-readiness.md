# UC050 本人待接收转让实施记录

状态：`COMPLETE`。2026-11-08。用户接受搜索与转入列表草案，App已落实UC050/051、UC026修订、读契约、registry与brief，并已通知Auth owner设计；用户随后明确接受Auth UC039及UC027/010方案并授权该owner实现。本记录只覆盖先行串行工作包UC050，UC051的后续实施和验收另见[独立记录](UC-APP-051-platform-application-directory-readiness.md)。

## 实现

在原ApplicationAdminTransferService新增ListIncomingApplicationAdminTransfers。可信USER主体为唯一收件人，不要求当前APPROVED Developer；仅返回持久PENDING且本次观察时间未到期事项。查询使用majority只读snapshot，批量读取Application技术名称与精确归属/ownership绑定；不调用Auth、不写EXPIRED/fence/revision或访问事实。原Get、命令和owner-exit过期收敛继续原语义。

投影独立于命令资源，只有transfer/application ID、技术名称、from/to opaque Auth ID、PENDING及申请/到期时间。pageSize默认20最大100，稳定requestedAt/transferId倒序keyset，独立用途/主体摘要/版本/位置绑定HMAC。key从既有服务私密材料按独立用途派生，无新密钥env或兼容层。0041显式迁移增加目标/状态/申请时间/ID索引，旧owner-exit和expiry索引保留，readiness要求新ledger。

HTTP正文单JSON对象最多16KiB，无query覆盖，未知字段拒绝；native未知字段也拒绝。身份在输入前，成功/错误private,no-store。bad query/token400、必要损坏500、存储503；空集合明确items=[]。Wire和Proto均由生成器产生。

## 已有专项证据

- 串行真实Mongo专项（含新查询、同时间翻页、到期、终态、必要损坏、三种写入竞争、旧转让迁移与fresh/sequential迁移）通过37.648秒。
- 最终组合Mongo race36.031秒、正常Wire HTTP/native gRPC E2E12.543秒通过。真实事务先读申请、在App批读前受控暂停，再分别提交取消/接受/关闭；前后快照均完整。
- Wire E2E证明普通USER及多种Developer资格标记可读，Auth资格provider不可用不影响读取且接受仍失败，不通过列表绕过原新鲜资格检查；覆盖身份先于输入、未知字段、他人空集合、最小投影和显式空数组。
- 单元/transport/架构go test ./...、fmt/Wire漂移与API Proto生成校验通过。新增本地三镜像入口 --incoming-transfers，使用正式注册及设备登录，受控Developer资格数据不手工构造凭据或Session；固定三镜像业务链已实际通过。

首轮专项中的损坏数据构造被validator拒绝，已仅在隔离测试数据写入加显式bypass后重跑通过；开发期夹具编译失败不计为通过。最终固定输入的Gateway协议/Console、App侧三镜像业务验收和完整backend现已闭合；专项与最终完整证据分开记录。

## 规则覆盖

| 权威 | 自动覆盖 |
| --- | --- |
| BR-APP-059 | usecase/transport guards、Mongo本人/他人/终态及Wire普通USER/资格标记 |
| BR-APP-060 | Mongo期限边界、原Get收敛和只读持久状态不变；cancel/accept/close受控snapshot |
| BR-APP-061 | 必要App/ownership/name/expiry/type损坏整页失败、批量来源与Wire最小字段 |
| BR-APP-062 | HMAC跨主体/用途/key/畸形/篡改、同毫秒分页、HTTP/native输入/缓存/400/500/503 |

App、Gateway提交及三镜像保留本地，未部署。接入中Gateway owner误用11月6日历史push指令，已将统一API 7091db7推至远端新分支 `integration/script-query-api-20261106`；确认本轮no-push边界后停止后续推送，Gateway未push，未擅自删除远端分支。

## 固定输入与接入进度

App业务提交 `7424ad6e12194681b6170d03282d75d9efd1a07e`，官方HTTP client专项追加 `69f054b918270250af688c7836a1d4cd1bc372d5`（5.744秒通过），合并API gitlink提交 `a4f34c79226bc143e1dda31bf83ac1fa45a62b55`。App API增量 `83b52a4d580a3ea717311f646443be19256fff67` 与 Auth `bf0f17d4943b13cddf57d570c7003596be14ebd7` 已由API owner合并为 `7091db7db2e747babfd66f52dfd601968228477a`，三处API干净且tree一致，Go1.25.5的生成检查/API测试复核通过。

App旧API83输入的22项quick通过，报告 `.artifacts/verification/20261108T060602Z-1es6cidy/report.json`；它是接入前预检，不替代最终7091db7的完整backend。Gateway `29d92af1cbc820cf334d7d30ebd98fb6039d0d23` 已接入UC050与Auth UC039，161项路由的check和固定后端协议/Console E2E通过。App/Auth/Gateway同API本地镜像已构建，App侧真实注册/设备登录、转让发起/三协议查询/Developer Console、资格变化/取消的三镜像业务验收已通过。Auth权限依赖已由其owner实现并完整验证，UC050已关闭，UC051已按接受方案串行完成，见其独立记录。

## 固定本地镜像

- App `iwut-app-center:incoming-transfers-a4f34c7` / `sha256:a5525de0e7cef245fb0536b4a865a996b7d217ae21d7cde7227158076dbafc6d`。
- Auth `iwut-auth-center:search-local-uc050-7091db7-6e680a1e5700` / `sha256:06e5d4def7e9b68819979d0660f9463e6f899aa9945bc2253fce727d80038083`；业务指纹 `6e680a1e57005d31ecf4e192b19df864fc420d53a8df4346ee3ff01d15dacf7f`。
- Gateway `iwut-gateway:incoming-transfer-user-search-29d92af` / `sha256:1d2a729c141faf2b563ef6dcb07daf232daa060e7e69c6581ddd0f10a3285c5d`。

## 最终验收

Go1.25.5，冻结App `a4f34c79226bc143e1dda31bf83ac1fa45a62b55`、API `7091db7db2e747babfd66f52dfd601968228477a`、独立本地docs snapshot `48e561989a07ba3a44f9df4daee86c8bf46376eb`。完整 `make check-full` backend **24/24 PASS**，`changed_sources=[]`；Mongo race2363.939秒，正常Wire HTTP/gRPC E2E248.032秒。报告 `.artifacts/verification/20261108T063716Z-9tccgw5z/report.json`。

固定三镜像业务测试 `TestE2E_UCAPP050_IncomingTransfersLocalImages` 通过，包race1.643秒；证明同一真实Session的资格暂停不影响本人列表读取，但接受仍失败，取消后空集合。Gateway161路由check及完整协议/Console E2E通过。证据汇总在App忽略目录 `.artifacts/incoming-transfer-uc050/delivery.json`。本轮不把未部署状态或Console页面实现列为App UC050后端未完成项。
