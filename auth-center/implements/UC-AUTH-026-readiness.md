# UC-AUTH-026 开工检查

日期：2026-10-06

状态：`READY`

## 结论

UC-AUTH-026 没有未满足的产品设计依赖，可以作为一个 Auth/API 后端工作包实现。现有设备凭据、Session、账号版本、RS256 signer、service identity、OAuth 014–019 事务和真实 Mongo/Wire 测试基础均已交付；跨服务 closure 与 reauth proof 契约已经接受。

## 已确认决定

- Application closure 以 applicationId 保存永久且不可取消的唯一 tombstone；Apply/Get 使用 App service JWS、稳定 receipt 和相同请求幂等。
- authorize、code exchange、refresh、UserInfo、revoke/query 与 delegation 在最终权威边界复查 tombstone；不依赖 App provider 错误推断关闭。
- 近期认证必须由当前 Session 所属同一登记设备对新 challenge 签名；普通 USER JWS `iat`、Session 时间或另一设备不能替代。
- proof 固定 audience=`iwut-app-center`、purpose=`app.close`，绑定 sub/applicationId/jti/auth_time，TTL 5 分钟、偏差 30 秒。
- 完全相同 Complete 返回同一 jti/JWS/exp；App 在本地关闭事务中完成同 closure 幂等消费和跨 closure 重放拒绝。
- tombstone 不扫描改写 grant/code/token/family；历史记录、sector 与 pairwise sub 保留但永不复活。

## 依赖核对

| 依赖 | 结论 |
| --- | --- |
| 设备证明与 Session | UC006–010/020–022 已交付设备签名、Session、accountRevision 与最终状态检查。 |
| OAuth/OIDC | UC014–019 后端与 Mongo 事务边界已交付，可加入统一 tombstone gate。 |
| Service identity | trusted-service-identity-v1 已交付固定 audience、caller allowlist 和精确 permission。 |
| App closure 契约 | application-closure-v1 已接受，RPC、幂等键、receipt 与错误已固定。 |
| Reauth proof 契约 | application-close-reauth-proof-v1 已接受，Frame/JWS/TTL/消费语义已固定。 |
| 联合验收 | 实际 App UC027 尚待实现；Auth 可先完成自身与 API，最终 COMPLETE 需真实 App Apply/Get 和 proof 消费。 |

## Auth/API 工作包

- API 新增原生 gRPC-only `application_closure` package，以及 HTTP/native gRPC `application_close_reauth` package、固定字段号和错误 reason。
- Auth 新增 tombstone domain/repository/usecase、唯一索引/validator、service JWS transport 和 production Wire/config。
- 把 tombstone 检查接入 UC014–019 最终事务/读取边界，并覆盖并发两个胜序。
- 复用 Session 所属 credential verifier 建立短期 challenge operation，签发用途隔离 RS256 JWS；不复制账号或凭据存储。
- 加入启动一致性检查、默认关闭入口、有界限额、审计、真实 Mongo unknown commit/race/Wire 测试。
- 与实际 App UC027 联调 service Apply/Get、响应丢失恢复、proof 消费和 CLOSING→CLOSED。

## 非目标与启用边界

不实现 App lifecycle、配额、Publication、Tester、client slot 禁用、管理员 UI、Gateway 页面、第三方本地会话撤销或 Application 恢复。后端完成后两个入口仍默认关闭；生产启用需配置 Gateway DIRECT、App service allowlist、签名轮换、时钟与监控。
