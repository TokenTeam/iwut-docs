# UC-APP-027 开工检查

日期：2026-10-06

状态：`READY`

## 结论

UC-APP-027 的产品与跨服务设计依赖已闭合，可以在 UC026 管理员转让实现完成后串行实现。Auth UC026 与共享契约已经接受，固定同一登记设备近期认证 proof、永久 applicationId tombstone、Apply/Get receipt 和 OAuth 最终 gate。

## 已确认决定

- Application 生命周期为不可逆 `ACTIVE → CLOSING → CLOSED`；CLOSING 是本地停止运行、释放配额和 owner 义务的生效点。
- Close 要求 current admin、ACTIVE＋APPROVED 新鲜检查、ownership/lifecycle revision、逐字确认和 5 分钟 app.close proof。
- 本地事务取消 PENDING transfer、撤销 ACTIVE Tester link、禁用所有 active OAuth slot，并持久创建 closure/outbox/proof jti 消费。
- Version/Profile/Review/Publication/Filter/Membership/OAuth 历史保留；所有写入与运行入口最终要求 Application ACTIVE。
- durable worker 使用稳定 closureId Apply/Get；只有匹配 Auth APPLIED receipt 才推进 CLOSED，未知结果或长期故障不回滚。
- technical name 和 ApplicationId 不复用；不轮换 secret，不扫描删除 App/Auth 历史。

## 依赖核对

| 依赖 | 结论 |
| --- | --- |
| 管理员转让 | UC026 已接受并生成 brief；APP027 实现必须基于其 ownershipRevision、transfer 与 account fence schema。 |
| Auth closure | UC-AUTH-026/application-closure-v1 已接受；Auth/API 可并行实现，最终联调不能用永久 fake。 |
| Reauth proof | application-close-reauth-proof-v1 已接受；App verifier/唯一 jti 消费语义已固定。 |
| 本地依附模型 | Publication、Filter、Tester、OAuth registration、review queue 均已有实现和事务边界。 |
| Owner exit | UC025 已交付 account_owner_exit_fences；CLOSING 与 Prepare 共享锁序。 |

## App/API 工作包

- API 新增 application_closure 管理 package、HTTP/native gRPC、202/no-store 与稳定错误 reason。
- App migration 0022 增加 lifecycle、ApplicationClosure、durable task、proof jti，扩展 transfer/link 关闭原因。
- 全部管理写、审核、目录/详情/解析、Tester 与 OAuth provider 在最终边界加入 ACTIVE gate。
- 实现原子 CLOSING 事务、配额释放、依附状态处置、outbox worker 和 APPLIED receipt 收敛。
- 真实 Mongo race 覆盖 transfer/owner-exit/配额/Publication/Tester/OAuth/review；与真实 Auth 完成 proof 与 Apply/Get 联合验收。

## 非目标与启用边界

不提供恢复、取消、归档、临时禁用、平台强制关闭、物理删除或通知。终端路由和确认 UI 独立交付；Auth service/proof 配置不完整时关闭入口默认不可用，但已有 CLOSING worker 必须继续收敛。
