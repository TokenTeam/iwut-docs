# UC-AUTH-036 管理员 Scope 生命周期交付记录

状态：`CORE_COMPLETE / FULL_REGRESSION_PENDING`

2026-10-26 用户接受简化管理员方案后，UC036/UC014 相关修订已 ACCEPTED，先由脚本生成 brief，再由三个 subagent 分工实现，父代理完成启动及生产 Wire 集成。权威规则仅见 [UC036](../use-cases/UC-AUTH-036-release-scope-enablement-changes.md) 与 [UC014](../use-cases/UC-AUTH-014-authorize-application.md)。

## 实现范围

- 三个 HTTP/native gRPC 管理方法，完整平台管理员 USER JWS 与在线复核；精确 method 鉴权、严格 128 KiB ProtoJSON/Protobuf、presence/重复/unknown/null 拒绝、no-store、有界限流。无新增权限、签名发布身份或双人审批。
- REGISTER/CORRECT_TEXT/SET_ENABLED 分型；真实提供方清单/资料派生类型/资源路由/UC030 存储依赖门禁，不提供删除/重命名/同名改义。完整目录仍最多 32 项。
- 全局 Auth fence 内目录 revision/digest CAS、NO_CHANGE、同 operationId 原回执重放/异参拒绝；目录/不可变契约/审计/回执同事务，首版无 TTL。
- 首次系统基线、不可变初始审计与持久标记；后续重启只验证 stable 提供方和 live 约束，不覆盖文案/启停，不自动加入清单新项，损坏/缺失拒绝。
- UC001 一致事务读取，避免 REGISTER 时目录与契约跨批混读；OAuth/UC001 仍共享同一目录，不改外部 v1 读投影。
- 每次 consent View 旋转 presentation，绑定本请求定义；相关变更/旧标签/无证据提交拒绝，无关目录变化不冲突。显式同意审计保存展示，静默复用仅记录来源，不伪造已展示事实。
- 初始生产 Scope manifest 的 email/campus.whut 文案对齐已接受邮箱 v3：只读当前登录邮箱，校园认证来自当前绑定而非永久事实。仅修正与现有权威语义不符的说明，不改变权限含义或自动更新任何已有数据库。

## 验证

已通过的分项：

- `make check`，普通全仓 `make test-race`；两份独立 API `make proto-check`。
- docs 72 份 brief 一致性、App registry、30 项工具测试。
- 实际 Mongo replica-set/race：CAS/并发/no-op/replay/unknown commit/审计回滚/溢出/时钟回拨、首次纯验证不写入、严格标记/契约、真实治理撤权与目录写竞争。
- 实际 Mongo/race：相关/无关文案变化、旧 tab/缺 presentation/旧交互重新 View、坏 BSON、同意审计写失败回滚、silent reuse 不造展示。
- UC001 并发读取与 REGISTER 同跑，验证公开快照不会混合目录/契约世代。
- 生产 Wire、真实 HTTP/gRPC 生成客户端的管理员读写/查询/权限/严格输入、停用 email 后重建 runtime 不覆盖及前向恢复；实际 App provider OAuth 全链专项通过。

首次全仓真实回归暴露新增测试 helper 复用 Kratos 响应 Header 造成丢失请求身份，以及历史 OAuth fixture 写死已退休的 App v2 审核策略；均已修复。fixture 现从正式审核详情读取当前 policy version，同时断言已知四项检查，不跳过新检查。代码复核另修复 UC001 事务外读的混合世代伪故障。

最终稳定版本（含实际提交成功但调用者响应丢失的原编号恢复）的完整 Wire 包独立 replica-set/race 已通过，189.170s。全仓真实 Mongo/race 已执行但未全绿，故仅记 CORE_COMPLETE，不宣称 COMPLETE 或生产就绪。

该轮完整运行中的旧 `TestE2E_IdentityIssuance_ProductionWire` 出现一次 `GetOwnEmails/PASSWORD_UNAVAILABLE`。同一串行 fixture 的 Begin 日志为 `17:44:50.016736`，后续 Complete 日志却为 `17:44:49.608721`，紧接 Get 为 `49.623625`；高置信为宿主墙钟倒退触发现有 PasswordQuota 的 future-unit 保护。该测试不配置 OAuth/Scope 管理，本次未改 quota；故障注入为独立 appName，不能将这个 reason 混作其结果。原 DB 已清理，未声称直接查实额度行；保留全套非零退出事实，不通过复验抹去失败，也不放松安全策略。其后 Identity+OAuth 联合专项通过（Wire 43.732s），再独立复验整个 Wire 包通过（189.170s）。

同一全仓运行的 Mongo 包耗时 729.240s，仅旧 `TestEmailAccountAndLoginShareOwnerMailCooldownAcrossAddresses` 在 `accounts.Own` 返回 password unavailable；新增 Scope/consent 用例无失败。该路径同样复用 PasswordQuota，但无独立墙钟日志，不能仅凭相同 reason 宣称根因已确证。较早一次完整 Mongo 包通过（630.800s），随后追加的新测试/一致读取修订均有真实专项 race 通过。最后对该旧用例及全部新增 Scope/consent 用例三轮独立 replica-set/race 复验通过（Mongo 117.120s）。全量门禁仍保留未通过，下一步是在稳定墙钟下重跑，不修改配额策略或给测试无条件重试。

最终 `make check`、普通全仓 `make test-race`、两份 API proto-check、72 brief 一致性、registry 与 30 工具测试通过；独立测试容器全部自动清理。最终全量失败日志位于本机 `/tmp/uc036-final-mongo.Hy2cz0`，完整 Wire 独立通过日志 `/tmp/uc036-wire-isolated.i3m2P5`，三轮 Mongo 专项 `/tmp/uc036-final-targeted.hBFbmJ`（临时日志不作为可恢复的版本化证据，失败与结论已摘要保留在本文）。

## 独立交付与部署门禁

`AUTH_SCOPE_MANAGEMENT_ENABLED` 缺省 false；现阶段实现不打开生产。Gateway SESSION 三路由、管理员 UI、App TTL/刷新/Reviewer 与 Console 真实界面联合链另行验收，UC035 仍 DRAFT。单纯真实 App provider 测试不等同真实 Console 审核证据。

启用前需要全部副本一致的已交付提供方清单，撤除旧 SeedCatalog writer；不自动修复/迁移已有无标记数据库，不部署、不删用户数据。实现阶段 API 主仓库与 Auth API 子模块两份生成输入输出已同步；用户随后仅授权本地 commit，本批先提交 API、将相同 commit 同步到 Auth API 子模块，再提交父仓库 pin。文档与生成 brief 一并提交；不 push、不代表全量门禁已闭合。远端发布及后续上线仍须单独授权，不能只提交父仓库遗漏 API 内容。
