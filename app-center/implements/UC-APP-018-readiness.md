# UC-APP-018 开工检查

检查日期：2026-09-28。本文记录实现依赖与工作包边界；业务以 UC/BR 为准。

## 当前结论

UC018 不依赖 Version、Review、Publication 或 Auth refresh family，可以先于其它 OAuth 扩展独立实现。既有 Application、可信 Developer 身份、Mongo 事务、Application `coordinationRevision` 管理员写栅栏、双协议 Transport 与完整验证入口均已交付。依赖检查没有发现领域阻塞，工作包现已 ACCEPTED / COMPLETE：服务 `041a929`、API `51e6572`。

Auth 最新的 offline_access/refresh 期限变更只消费后续 UC019 provider 快照，不改变 registration、credential、secret 轮换或 client 状态语义，因此不阻塞本工作包。

## 依赖核对

| 依赖 | 当前证据与结论 |
| --- | --- |
| Application 与管理员竞争 | 已有 Application collection、`coordinationRevision` 和事务写栅栏；UC018 在同一事务复查 adminId/Developer 门禁并写 fence。 |
| 可信 Developer 身份 | 复用现有 USER JWS 与 `DeveloperIdentity`，只接受 APPROVED 当前管理员。 |
| ID、secret 与时钟 | clientId 使用独立 UUIDv4 generator；secret 使用 CSPRNG 32 bytes、base64url/no-padding；摘要按共享契约域隔离；时间与随机性通过 ports。 |
| MongoDB | 新增 registration/credential collections、validator、唯一索引、migration/readiness；CONFIDENTIAL 双写必须事务原子。 |
| API 仓库 | 新增 `app_center.v1.oauth_client` 管理 service、enum、presence、error reason、HTTP annotation 和生成物；API 先提交，再更新服务 gitlink。 |
| Version OAuth 配置 | UC018 创建 identity 时不读取 Version/Review/Publication；002–005/007 扩展随后串行交付。 |
| Auth provider | Get/Verify/Resolve 方法属于 UC019；本轮不注册内部 provider service，也不宣称 OAuth 登录可用。 |

## 实现边界

- Domain/UseCase 使用独立 `internal/oauthclient` 能力，不把 credential 塞入 Application 聚合或 Version package。
- registrationRevision 管 identity/status；credentialRevision 只管 secret。authorizationEpoch 只在实际禁用/启用时递增。
- secret 只在确定提交的 CONFIDENTIAL 登记/轮换成功响应披露一次；持久化、日志、错误、测试报告均只含摘要或占位符。
- 管理查询要求当前 APPROVED 管理员；旧管理员、普通用户、PUBLIC credential 查询和跨应用 clientId 均失败关闭。
- 完整验收执行 `make check-auth-app`；冻结 service/API/docs 来源，报告覆盖真实 Mongo、HTTP/gRPC 与已有 Auth 回归。全部提交保留本地，不 push。

## 完成证据

- Domain/UseCase、CSPRNG与摘要、0014 migration、真实Mongo事务/validator/index、管理员栅栏、双类型并发、registration/credential OCC隔离、secret脱敏及实际HTTP/gRPC均已自动验证。
- `make check-auth-app` 22/22通过：`.artifacts/verification/20260928T070657Z-ed6ypm5s/report.json`，`changed_sources=[]`。
- UC019 provider/secret验证、Version OAuth配置、授权/token与未来渠道保持未实现，未越过本工作包边界。
