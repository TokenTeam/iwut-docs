# 审核策略正式变更途径提案


> 2026-11-03 替代说明（新修订技术方案待审）：用户已确认提交时固定政策。本文原“切换打断旧 PENDING 决定、清确认换策略”的要求不再指导后续工作；发布工程范围也按[本轮提案](2026-11-03-submission-bound-review-policy-proposal.md)重新收敛。原文保留历史；Profile 单工作位、公开指针 CAS、Scope 独立门禁和验收分层不在替代范围。

状态：`ACCEPTED`（设计），2026-10-26。用户已同意两项草案并要求编写/修改相应用例；本次仅落实权威文档与派生 brief，不启动实现、迁移、Proto/codegen、测试实现、CI、镜像构建或部署，不 commit/push。

## 接受与权威收敛

2026-10-26整合补记：下文草案过程与“不commit/push”等表述保留当时授权范围；用户后续已授权本地docs分支整合，Console UC006/007的已接受验收文字已在整合main落地，详见[交接状态](2026-10-26-console-review-acceptance-handoff.md)。其原始工作区与业务源码未改，未运行新增联合验收，未push。Auth UC036状态以独立接受的用例及交付记录为准。

以下核对、选项和候选文字保留为提案过程记录，不是第二份权威定义；其原有“待审核/未修改”等描述表示草案阶段。当前业务规则已收敛到 [UC005](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[UC016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)、[UC031](../use-cases/UC-APP-031-query-application-profile-reviews.md#完整策略定义)和 [ADR004](../adr/ADR-004-mongodb-transactions-and-schema-management.md#政策发布回执与恢复)，冲突时以这些权威正文为准。Console 对应文字见[已接受交接](2026-10-26-console-review-acceptance-handoff.md)，由其所有者落地；未修改 Console 工作区。

## 事实核对与来源

2026-10-26 只读核对远端：App `master=d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea`，API `master=27c9743d2d7476511932a83563e103aee5b4e28e`，docs `main=c602e46a161c71b31e6135ff7ad99789901900f8`，均与本地对应源码一致。Console 权威 UC006/007 和发布复验记录来自同一 docs 仓库的独立 `console-uc002` 工作区，核对提交 `534f02f`；不复制或覆盖该工作区。Console 实现只读参考提交 `e1db0af`。

| 事项 | 已有事实 | 权威或实现证据 |
| --- | --- | --- |
| Version 策略所有权 | App 拥有不可变版本和历史；RETIRED 不用于新决定 | [BR-REV-016](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016) |
| 当前 Version 基线 | v1/v2 RETIRED；唯一 ACTIVE v3，四项正式定义与版本绑定 | [正式定义及迁移](../use-cases/UC-APP-005-decide-application-version-review.md#初始正式策略)、[0033 实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/version_review_definitions_migration.go) |
| 当前 Profile 基线 | migration 0013 初始化 `app-profile-review-v1`；两项既定检查；无在线策略管理接口 | [BR-PRF-028](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028)、[初始化实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/profile_review_decision_migration.go) |
| Reviewer 正式读回 | UC030 当前策略带 version/IDs/definitions；UC031 当前 Profile 策略带 version/IDs，并有同次公开指针及公开资料 | [UC030](../use-cases/UC-APP-030-query-application-version-reviews.md#审核详情)、[UC031](../use-cases/UC-APP-031-query-application-profile-reviews.md#审核详情)；API27c 的两个 ReviewQuery service |
| 既有部署入口 | `app-center migrate` 显式运行已编入二进制的 migration；serve 不自动迁移 | [ADR-004](../adr/ADR-004-mongodb-transactions-and-schema-management.md#schema-与索引)、[命令实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/cmd/app-center/migrate.go) |
| 最终决定栅栏 | 两类决定在事务内真实写入 policy coordinationRevision，与退休同一文档串行化 | [Version 实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/application_review_decision_repository.go)、[Profile 实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/decide_application_profile_review.go) |
| Scope | Auth 独占目录与 enabled/revision；UC-AUTH-001 是只读快照，不提供启停命令 | [BR-SCP-001/003/004](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-001) |

这里的 ACTIVE/RETIRED 是正式迁移应形成的基线，不是本次对生产数据库状态的现场查询。没有读取生产数据库或执行部署。

初次核对时，Auth UC036仍是受控发布草案。2026-10-26整合更新：Auth已在独立审核中接受[UC-AUTH-036：管理Scope定义与生命周期](../../auth-center/use-cases/UC-AUTH-036-release-scope-enablement-changes.md)，本地文档提交d3aa53f记录管理员管理API、目录CAS、回执及启动旁路治理；它替代早期候选路径。核心实现状态为CORE_COMPLETE / FULL_REGRESSION_PENDING，开关默认关闭，Gateway接线、App TTL刷新与Console真实联合链尚未验收，详见[Auth交付记录](../../auth-center/implements/UC-AUTH-036-readiness.md)。UC001仍为内部只读快照，App不新增Scope写模型；Auth的接受来自其独立审核，不由本提案代为接受。

Console 基线以[已发布缓存头复验记录](../../console/implements/2026-10-23-published-cache-header-fix-verification.md)为准：API27c，App `8e499500…`、Gateway `509acf96…` 的专项35/35、默认完整115/115通过。缓存问题已经解决，本提案不重开该问题，也不把现有套件全绿等同于所有策略变化验收完成。[UC006 验收4](../../console/use-cases/UC-CONSOLE-006-review-application-versions.md)仍要求真实策略退休/Scope 失效后的恢复。

## 需求判断与选项

当前有“政策发生真实变化时，应可审查、发布、退休并解释历史”的治理需要，已有版本化 BR 支持该需要；没有证据要求运营人员通过在线页面频繁创建、审批、定时激活策略。因此不建议仅为补一条 Console 测试新增生产管理功能。

| 选项 | 范围与代价 | 建议 |
| --- | --- | --- |
| A：正式发布变更流程 | 每次真实政策获批后交付专用、不可变的发布 migration；补审计回执、正式运维读回和恢复规则；不增加在线管理 API | **推荐**，沿用 App 当前责任边界 |
| B：独立治理 UC/API | 需要权限、草拟/审议/发布流程、可查询变更单与运维 UI，API/Gateway/Auth 权限均可能扩展 | 当前暂缓；出现独立运营团队或高频在线治理需要后另提 UC/ADR |
| C：仅为测试制造版本或直接改库退休 | 无真实政策依据，不能形成正式准备链；可能造成无 ACTIVE/多 ACTIVE 或历史语义变化 | 不采用，不作为联合验收准备 |

**现成可复用的是机制，不是任意变更工具。** UC005 已接受的 v2→v3 切换和 0033 是正式历史发布范式；当前已运行0033的环境再次 `migrate` 是 no-op，不会再次退休/激活。它也不能直接证明当前 Console 的“读到有效正式定义并勾选后，再经历下一次变化”：旧 v2 没有 v3 的正式定义投影，当前 UC030 decoder 对缺定义失败关闭。不能倒退数据库/激活 v2来凑此验收。

本提案不定义 `v4` 或 Profile `v2` 的政策内容。没有下一份真实政策获批时，真实切换场景保持“待准备”，不制造同义版本，不把组件测试称为真实链路完成。

## 已接受流程设计摘要：真实政策发布包

以下方向已获用户接受；此处保留设计过程摘要，当前约束以本页“接受与权威收敛”所指 UC/ADR 为准，实施尚未开始。

### 主体、权限与发布输入

政策内容由 App 政策责任人提出、用户/指定治理责任人审核；发布由具有目标环境迁移权限的部署主体执行，部署身份与批准依据进入可信发布审计。Reviewer 的 `app.version.review` / `app.profile.review` 不授予策略变更权，Application admin、SysAdmin 身份也不隐式获得 Mongo 迁移凭据。不新增 Auth 政策管理权限或终端用户 surface。

发布包拟包含：唯一 changeId/migrationId、policyKind（VERSION 或 PROFILE）、fromVersion、不可变旧内容预期、toVersion、完整新策略、批准记录引用、App release commit/digest、发布清单原始字节 SHA-256 与兼容性检查结果。版本沿用既有1–50 ASCII规则，不以字符串排序推断新旧。不可变内容比较排除 status、coordinationRevision 等运行状态；同版本 ID 或文本不能重新解释。[BR-REV-016](../use-cases/UC-APP-005-decide-application-version-review.md#br-rev-016)、[BR-PRF-028](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028)继续拥有业务定义。

发布输入来自受审代码/发布包，不提供接收任意 JSON 并更新 policy 的通用生产 CLI。环境、operator 与清单的绑定由可信发布平台审计，不把可随意填写的 `actorName` 当作可信 Auth 审计主体。

### 状态、并发与事务边界

拟对每一 policyKind 分别保持唯一 ACTIVE；Version 与 Profile 不共用一个“当前策略”。正常变更是同一事务内把唯一预期 A 从 ACTIVE 改为 RETIRED，并插入/精确核对新 B 为 ACTIVE。该事务不重写历史内容、旧 decision、Review snapshot 或 PENDING attempt，不产生对外可见的零 ACTIVE 窗口。不提供单独退休最后一个 ACTIVE 的常规操作。

前置条件为 A 仍是当前唯一 ACTIVE、A 内容精确相符、B 未被其它内容占用、发布清单与批准记录匹配。不允许把已 RETIRED 的版本重新激活作为回滚，延续[UC005 切换规则](../use-cases/UC-APP-005-decide-application-version-review.md#初始正式策略)。兼容故障时先停止决定入口、修复或经批准发布全新版本，不恢复旧策略状态制造 ABA。

拟补每类策略最多一个 ACTIVE 的数据库约束，事务提交前同时验证“至少一个”，并补 Profile 查询/决定对唯一当前策略的严格验证。当前 Version 查询已检查唯一 ACTIVE；**Profile 当前读取只 FindOne(ACTIVE)，不是现成的唯一性证明**。这些是正式切换实施前需要解决的范围，不是本轮已修复的缺陷。

决定与切换沿用现有 policy 文档真实写栅栏：事务读到当次 coordinationRevision 后条件更新，退休也写同一文档。该内部计数会被正常决定增加，不能作为要求操作人员长期持有不变的业务前置值。并发 A→B 与 A→C 只能有一个基于 A 成功；另一个重读后报告基线已变，不自动把目标改成 B→C。决定先提交则保留 A 的历史决定；切换先提交则旧 A 的新决定按既有冲突 reason 拒绝，不产生部分决定。

### 重复、未知结果与可审计读回

拟为新的政策发布 migration 增加**与策略切换同事务的发布回执**，复用 migration ledger，绑定 migrationId/changeId、kind、from/toVersion、清单摘要、批准引用、release、appliedAt；部署身份通过相同 changeId 关联可信发布审计。旧 ledger 记录不改写。

这是需批准的工程扩展：现有 ledger 只有 `_id/appliedAt`，且通用 migrator 在 apply 返回后另行记账，**不能声称现有命令已经实现上述原子审计回执**。新政策 migration 需补齐回执与 apply/重入衔接；若复用 ledger 的兼容性不能证明，应暂停并单独审核，不直接新建政策服务。

重复同一 changeId 且清单一致时读回原回执，不再激活/退休、不新增重复事件；同 ID 不同清单失败关闭。未知提交结果首先按 ADR004 重试同一事务提交，再查同一回执和当前事实，不换 changeId 重放。如果原 A→B 已成功、后来 B→C 也成功，恢复 A→B 只报告原回执和现在 C，不重新激活 B。回执、策略状态不一致或无法判定时报告 UNKNOWN/一致性失败，停止操作并保留证据。

拟增加内部只读运维 `policy-status` 能力（CLI 草案名，不是现有命令），输出 kind、唯一当前版本、ACTIVE/RETIRED 摘要、不可变内容摘要和指定 changeId 回执；受迁移环境访问控制，不经 Console/Gateway。它用于正式读回历史退休及发布事实，不能仅以进程 exit0 或平台日志代替。

Reviewer 继续通过 UC030/031 正式详情读回 currentPolicy 与同次 asOf；历史 decision 继续显示原 policyVersion，不能用新定义解释旧决定。现有 public API 不提供历史策略状态查询，本提案不把该能力说成已经存在。

### 正式定义和兼容性门槛

Version 当前 API 已能承载完整正式定义，下一真实版本可以沿用 UC030 的字段与一致性要求，前提是新定义通过既有结构/文本约束。

Profile 当前 API 只给 version/IDs，Console `review-decisions.tsx` 只对 `app-profile-review-v1` 使用其已知正式解释，未知版本保持只读。**发布新 Profile 版本之前必须先接受其正式文本来源和消费者兼容方案**；不能从相同 ID 沿用旧含义。推荐在发生真实 Profile 政策变更时，单独扩展 UC031/Proto 为版本绑定的正式 definitions，先部署可失败关闭的新客户端，再切换策略。是否采用该扩展是本提案待审点，本轮不新增 Proto 或假定已有字段。

### 错误语义草案

| 边界 | 建议保留或补充的结果 |
| --- | --- |
| Reviewer 持旧 Version 策略作决定 | 保留 `ERROR_REASON_APPLICATION_REVIEW_POLICY_CHANGED`，HTTP409/gRPC ABORTED；不写决定 |
| Reviewer 持旧 Profile 策略作决定 | 保留 `ERROR_REASON_PROFILE_REVIEW_POLICY_UNAVAILABLE`，HTTP409/gRPC ABORTED；不写决定 |
| 当前策略缺失、多 ACTIVE、内容损坏 | 按 UC030/031 的一致性错误失败关闭，不伪装“无权限”或返回任意策略 |
| 发布基线变化、同版本不同内容、同 changeId 不同清单 | 拟议稳定运维分类 BASE_CHANGED / IMMUTABLE_CONFLICT / CHANGE_ID_CONFLICT；非零退出，不改策略，不新增 HTTP reason |
| 运维身份不具备环境权限、依赖故障、提交结果未知 | 由发布平台拒绝，或报告 UNAVAILABLE / UNKNOWN；UNKNOWN 不等于失败回滚，不自动换 ID重放 |

运维分类只是本提案术语，具体 CLI 退出码/格式在审核后的工程 brief 中定稿，不冒充现有 API 枚举。

## 后续联合验收设计（本轮不执行）

1. **准备门槛**：真实新政策正文、发布包和兼容性获批；隔离环境以正式命令创建/提交真实 Review，Reviewer 权限由 Auth 正式授予。保留旧策略下的历史终态及一条待审记录。固定所有镜像/API/发布包输入，不改库 seed 策略。
2. **加载旧策略**：生产 Console 页面读到 A 的正式定义，Reviewer 主动勾选；记录绑定的 reviewId/currentPolicy/当前公开指针，不复制 Cookie 或私有快照。
3. **合法变化**：获权部署主体执行已批准的正式发布 migration A→B。测试 runner 只调用发布入口，不直接写 Mongo；通过正式 policy-status 读回 A RETIRED/B ACTIVE/原子回执，再经 UC030/031 查询 B。重复 migration 不产生第二次变化。
4. **真实旧请求**：在页面尚未重读时人工提交原 A 决定，取得既有409；重读后展示 B，清除旧确认集合、要求重新评审；无自动 POST、补勾、改 outcome 或复用旧确认。缺定义/未知版本/重读失败时只读，不能自行猜 B 的定义。
5. **结果未知与竞态**：切换和决定在同一真实链路竞争，验证符合提交顺序的两种结果及终态只写一次；丢失响应后读同一 Review/发布回执恢复，不重新发决定。运维回执幂等和失败回滚另由真实事务层证据覆盖，不把故障注入的组件证据冒充浏览器业务路径。
6. **Scope 独立门槛**：使用独立接受的[Auth UC036](../../auth-center/use-cases/UC-AUTH-036-release-scope-enablement-changes.md)管理员管理API与原操作回执取得新catalog revision；核心实现不等于全量回归或接入门禁闭合，正式联合环境准备仍依其交付记录。App 只消费快照并按既有 BR-REV-018 复检。遵循 [ADR001 缓存边界](../adr/ADR-001-scope-catalog-cache.md#第一阶段缓存)，冻结实际 TTL 与实例输入，在旧缓存有效期和在途取样窗口后取得真实刷新/消费证据；不能只凭 Auth 新 revision 就声称所有 App 实例立即采用，也不能直接清缓存或伪造时钟。用正确策略与确认集合验证真实 Scope 错误，不把它误记为策略409。无合法 Auth 准备入口时该项继续待准备，不在 App 新增 Scope 写模型，也不把伪造 expectedPolicyVersion 当 Scope 失效。

建议提交用户审核的 UC006 验收4细化文字（**仅候选文字，未修改 Console UC**）：

> 两个 Reviewer 并发、依赖故障、响应丢失/断网及 PENDING/终态重读经真实后端验证。策略变化使用获批的 App 正式发布变更，Scope 失效使用 Auth 所有者的正式变更入口；页面加载旧事实后，真实旧请求被拒绝，重读并清空确认，禁止自动重放。组件恢复测试与事务并发测试分别标记层级，不能替代上述真实变更链；正式变更准备条件未具备的项继续待验收，不以错误版本输入或直接改库关闭。

## 审核后的可能改动范围

| 位置 | 若接受 A，后续拟变更 | 本轮状态 |
| --- | --- | --- |
| UC005 BR-REV-016 及正式策略切换小节 | 明确发布主体、不可变内容、退休/替换与读回；真实新政策另审 | 未改 |
| UC016 BR-PRF-028 / UC031 | 同步 Profile 发布流程；新版本前先解决定义来源与唯一 ACTIVE | 未改 |
| ADR004 | 补政策发布的同事务回执、重入、未知结果与读回约束 | 未改；不另起政策服务 ADR |
| App 实现 | 仅实际获批发布包、相关 migration/校验/只读运维和回归；不做通用在线 CRUD | 未实现 |
| API / Gateway | Version 方案无新增接口；Profile 正式 definitions 扩展需另审后由 API/Console 所有者协作，现有决定 surface 不变 | 未改 |
| Auth / Console UC006 | Scope 正式变更由 Auth 拥有；候选验收文字由 Console 所有者在用户接受后修改 | 未改，无跨聊天消息 |

## 审核结论与尚未实施的范围

用户已接受 A：正式发布治理、原子回执和运维读回，不增加在线策略管理 API；新 Profile 版本先满足正式定义兼容门槛。两项草案不自动接受下一份真实政策正文；Auth UC036的接受与实现以其独立审核及交付记录为准。发布身份/批准凭据、回执具体格式/保留策略等实施参数仍需在工作包冻结，尚未实现。

App对应用例、ADR与索引已更新；Console验收文字后续已在本次整合main落地，业务代码、Proto、迁移和运行环境未改。
