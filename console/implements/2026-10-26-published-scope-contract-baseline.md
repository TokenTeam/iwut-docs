# Scope 管理契约发布后的 Console 基线复验

状态：`BASELINE_VERIFIED / SCOPE_CHANGE_PENDING`，2026-10-26。用户通知 Auth/App/API 已发布并授权开始新镜像联调。本包复验既有 Console 功能，专项27/27及默认全量115/115通过；区分 Gateway 路由交付、Scope 正式变化的新增准备以及 App 尚未实现的策略发布能力。不新增业务 UI，不将基线回归冒充 Scope 变更验收。

## 冻结输入与边界

Console：`e1db0af1de86fe556122d3fc84068d0cb04dfd68`，工作区干净；产品/runtime/runner/spec 未修改。现有 Console 客户端继续使用 API `27c9743d2d7476511932a83563e103aee5b4e28e`，本轮不消费新 Scope 管理 Proto，因此不是新 API 客户端生成验收。后端 Auth/App 已引用独立 API `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。

每轮从正式 CNB 拉取 `latest`，随后固定实际解析的镜像 ID；不编译相邻后端、不回退本地兼容镜像、不修改既有断言：

| 输入 | 专项实际镜像 ID |
| --- | --- |
| Auth | `sha256:518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16` |
| App | `sha256:68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01` |
| Gateway | `sha256:444c75a71fc74fb14840718b259aeec14fbe2bbcda0a9832340c70b64ed099b0` |
| Mongo | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` |

Auth 远端提交为 `bddd98f5d922a1f5b9f4e5ee9f0976cd87f8a1b8`；App 为 `4f62badc199139c73fad920f40cbcf56e9b391aa`，后者只更新 API gitlink，不包含策略发布回执或运维读回实现。文档本地 main `e424e3d` 已合并双方设计，检查时远端 main 仍为 `c602e46`，本包无 push 授权、不代为推送。

## Gateway 前置与普通门禁

已直接从发布 Gateway 镜像读取路由清单，确认 GetManagedScopeCatalog、ChangeScopeCatalog、GetScopeCatalogOperation 三条精确 SESSION 路由存在。它们没有 Console surface allowlist；符合独立管理入口与治理 UI 分离的交付边界，不擅自开放 Admin Console 域名。读取静态清单不等于验证成功的目录修改。

`pnpm edge:e2e` 通过：既有六条 ADMIN 查询/决定链失败关闭、伪造头无旁路、Developer api-deny 保持。`pnpm test`、`pnpm typecheck`、`pnpm generate:check` 均 exit0；普通测试为原 954 项 Vitest 与 221 项 Node，官方固定 API 生成校验未回退本地来源。真实测试的严格类型、合成失败报告隐私护栏及生产 build 前置通过。

## 审核决定专项

命令：`pnpm test:real tests/real/review-decisions.real.spec.ts`。

轮次 `iwut-console-real-120753`：27/27 通过，浏览器阶段 2.9 分钟，exit0，无 skip/retry。包含既有真实批准/拒绝、同 Review 双 Reviewer 竞争、未知结果/30 秒期限、正式撤权与管理关系变化、六项旧决定响应跨 Session 隔离、App→Auth 依赖断链恢复及 Admin→Developer 实际批准资料投影。既有决定响应的 private/no-store 断言保持通过。

准备阶段遇到正式密码限流，按 runner 既定规则尊重 Retry-After，重试相同注册完成正文；另等待真实邮件冷却。这些不是浏览器失败重试，也不放松 Auth 安全规则。专项退出后容器（含已退出）及 network 均已核验为空。

## 无参数完整门禁

同一源码冻结下执行无参数 `pnpm test:real`，轮次 `iwut-console-real-129855`：115/115通过，浏览器阶段19.2分钟，exit0，无skip/retry。重新拉取五个输入，实际解析ID与专项表一致；轮内产品/runtime/runner/spec未改，不借专项27项或2026-10-23的115项结果替代本轮完整门禁。

原登录/双surface隔离、32次签发显式重建、双生产副本/Mongo提交点故障、Developer只读分页/预算/资格/转让、Admin查询/决定/恢复均按既有用例完成。原全部缓存头断言仍在，既有App错误头和Gateway决定Session401头保持通过；没有代理补头、删除断言或后端源码编译。19.2分钟是Playwright报告的浏览器阶段，不含前置构建、账号准备及清理。

完整轮次结束后，容器（含已退出）及network已核对为空，Edge临时容器亦无残留。legacy本地与本次远端仍为`e68851e343bd0e077e5ccd0b680fe6813216ced0`。Console在专项/全量执行期间工作区干净；之后只更新AGENTS和测试README状态导航，产品/runtime/runner/spec不变。没有commit/push，也未更新目标状态；完整UC仍未完成。

## 基线时的剩余准备（后续增量已另行验证）

本节保留基线轮次的事实。后续[正式Scope变化工作包](2026-10-26-scope-review-change.md)已补齐准备并以30/30专项、118/118全量验证其有界链路；不把新证据追写成e1db基线当时已覆盖。

需求与业务语义继续引用 [UC006](../use-cases/UC-CONSOLE-006-review-application-versions.md#验收与完成标准)、[Auth UC036](../../auth-center/use-cases/UC-AUTH-036-release-scope-enablement-changes.md#验收与交付边界)及 [App ADR001](../../app-center/adr/ADR-001-scope-catalog-cache.md#第一阶段缓存)，不在此重定义规则。

基线时 runner 未配置持久 OAuth Scope manifest，也未启用 Scope 管理，原审核 Version 准备不能替代实际非空 Scope 变化链。当时的后续有界工作为先补隔离环境的正式持久配置、独立生成客户端和操作回执读取，再实施页面已加载后的 email 停用、App 真实 TTL/消费证据、旧 APPROVE 拒绝且保持 PENDING、前向恢复与明确重评，以及独立 Review 的停用期间 REJECT。使用现有正式管理员与管理入口，不为此扩展 Console surface、加入治理 UI、直接写目录数据库或伪造快照。未知管理写入只按原 operationId 恢复。

本轮不声称完成上述新增链路，也不关闭 Auth 自身尚未全绿的全量回归；Console 回归不能代替后端门禁。App 正式策略发布仍待实现和下一份真实政策审核；不造同义版本、不重新激活旧版。Cookie 33+ carrier 架构问题不在本包范围，完整 UC/广泛目标仍未完成。
