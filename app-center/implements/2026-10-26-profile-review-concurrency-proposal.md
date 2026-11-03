# 资料审核不同修订并发的可达性与验收分层提案

状态：`ACCEPTED`（设计），2026-10-26。用户已同意两项草案并要求编写/修改相应用例；本次仅落实权威文档与派生 brief，不启动实现、迁移、Proto/codegen、测试实现、CI、镜像构建或部署，不 commit/push。

## 接受与权威收敛

2026-10-26整合补记：下文草案过程与“不commit/push”等表述保留当时授权范围；用户后续已授权本地docs分支整合，Console UC006/007的已接受验收文字已在整合main落地，详见[交接状态](2026-10-26-console-review-acceptance-handoff.md)。其原始工作区与业务源码未改，未运行新增联合验收，未push。Auth UC036状态以独立接受的用例及交付记录为准。

以下核对、选项和候选文字保留为提案过程记录，不是第二份权威定义；其原有“待审核/未修改”等描述表示草案阶段。当前业务规则已收敛到 [UC005](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[UC016](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030)、[UC031](../use-cases/UC-APP-031-query-application-profile-reviews.md#完整策略定义)和 [ADR004](../adr/ADR-004-mongodb-transactions-and-schema-management.md#政策发布回执与恢复)，冲突时以这些权威正文为准。Console 对应文字见[已接受交接](2026-10-26-console-review-acceptance-handoff.md)，由其所有者落地；未修改 Console 工作区。

## 核对基线与结论

基线同[策略变更途径提案](2026-10-26-review-policy-change-proposal.md#事实核对与来源)：App `d3f510e`、API `27c9743`、docs main `c602e46`，Console 文档 `console-uc002@534f02f`。2026-10-23 缓存头修复后的 published 专项35/35、全量115/115已经通过，不是本提案的待修故障。

**当前规则下，同一 Application 的两条不同 ProfileRevision 无法同时具有可决定的 PENDING Review。** Console UC007 验收4提出的用户场景与当前工作位规则仍存在准备矛盾；不是缺少一个 seed 脚本。不同 Application 可以各有 PENDING，但它们写各自的公开指针，不竞争同一前置值。

| 权威/实现 | 核对事实 |
| --- | --- |
| [UC013 BR-PRF-006](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-006) | 同一 Application 最多一条 DRAFT/SUBMITTED，PENDING 决定前不能创建下一份 DRAFT |
| [UC013 BR-PRF-007](../use-cases/UC-APP-013-create-application-profile-revision.md#br-prf-007) | 工作位检查、序号、修订插入与 working 指针在同一原子边界 |
| [UC016 BR-PRF-024/025/026](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-024) | 仅一次性决定 PENDING/SUBMITTED；修订与 snapshot 一致；决定才清空目标 working 指针并释放工作位 |
| [UC016 BR-PRF-030](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-030) | APPROVE 比较明确 expectedCurrentPublishedProfileRevisionId 并原子自动公开；保留旧 APPROVED 历史，无历史重新选择/回滚入口 |
| [UC031 BR-PRF-043/046](../use-cases/UC-APP-031-query-application-profile-reviews.md#br-prf-043) | Reviewer 当前公开资料和指针来自同次详情；未知/损坏不能当 NONE |
| [Console UC007 验收4](../../console/use-cases/UC-CONSOLE-007-review-application-profiles.md) | 仍写“两个 Reviewer 分别批准不同修订导致公开指针冲突” |
| [唯一索引实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/profile_migration.go) | `uq_application_profile_revisions_working_application` 对 DRAFT/SUBMITTED 做 applicationId partial unique |
| [决定事务实现](https://github.com/TokenTeam/iwut-app-center/blob/d3f510e9b5b6f332405c773e11dfe1aa6cd0d2ea/internal/adapter/mongo/decide_application_profile_review.go) | 复检 working 归属和唯一工作修订；先拒绝已决定 Review，再核对公开指针；批准/拒绝和释放工作位在同事务 |

BR-PRF-030 中“两个针对不同 ProfileRevision 的并发批准”这一解释也需要由用户审核澄清，不能只改 Console 验收掩盖 App 权威正文中的相同暗示。**需要澄清的是可达性说明，不是取消 expected pointer 的校验或事务原子性。**

## 正式命令顺序与状态证明

设同一 Application 初始公开资料为 P0（或 NONE），新修订 R1/R2，对应审核 Q1/Q2。以下只用现有 UC013 创建、UC014 编辑、UC015 提交、UC016 决定；没有直接改库或隐藏发布接口。

| 步骤 | 正式操作 | 修订/Review | working 指针 | 当前公开指针 | 可决定 Review |
| --- | --- | --- | --- | --- | --- |
| 0 | 初始状态 | 尚无新修订 | NONE | P0/NONE | 无 |
| 1 | 创建 R1，按需编辑 | R1 DRAFT | R1 | P0/NONE | 无 |
| 2 | 提交 R1 | R1 SUBMITTED，Q1 PENDING | R1 | P0/NONE | Q1 |
| 3 | 此时尝试创建 R2 | 正式工作位冲突，R2 不创建 | R1 | P0/NONE | 仍只有 Q1 |
| 4a | 批准 Q1，expected=P0/NONE | R1/Q1 APPROVED | NONE | R1 | 无 |
| 4b | 或拒绝 Q1 | R1/Q1 REJECTED | NONE | P0/NONE | 无 |
| 5 | 步骤4提交后创建 R2 | R2 DRAFT，Q1 已终态 | R2 | R1 或旧 P0/NONE | 无 |
| 6 | 提交 R2 | R2 SUBMITTED，Q2 PENDING | R2 | 同上 | 只有 Q2 |
| 7 | 批准 Q2，使用其正式详情指针 | R2/Q2 APPROVED | NONE | R2 | 无 |

因此不存在同时满足 Q1/Q2 均 PENDING、两条修订均 SUBMITTED、二者都占同一合法 working 位的时刻。步骤4的终态、释放工作位与公开指针写入是原子的；不能在该事务的“中间一半”插入步骤5。

**迟到请求不构成反例**：Reviewer A 的 Q1 请求暂停，Reviewer B 先批准 Q1；之后管理员创建/提交 R2，Reviewer C 批准 Q2，最后 A 的 Q1 请求恢复。Q1 已终态，现有顺序返回 AlreadyDecided；它不是一条仍可决定的不同修订批准，也不证明 PublicationConflict。响应仍在网络中并不等于数据库中的 Review 仍 PENDING。

管理员转让不创建第二工作位；REJECTED/APPROVED 修订无原地恢复/再提交/重新公开能力；Version 的 Test/Grey/Stable 操作不改变 Profile 的公开指针。UC017 已被自动公开设计替代，当前 Proto 未暴露历史 Profile Publish。以上都不能用于构造所谓合法并行准备。

## 选项与推荐

| 选项 | 影响 | 建议 |
| --- | --- | --- |
| A：保留单工作位和指针前置防御，修正场景措辞并分层取证 | 不增加产品能力、不改变现有合法状态机；明确每层证据证明什么 | **推荐** |
| B：允许多条并行工作修订 | 改变 BR-PRF-006、工作指针、唯一索引、创建/编辑/提交/决定/查询和资料展示；需完整新业务设计 | 本轮不采用，仅有真实产品需求时另提案 |
| C：增加历史资料重新发布/回滚 | 新业务权限、审核时效和公开策略问题，不是验收工具 | 不采用 |
| D：直接 seed 平行 PENDING 或绕过 validator/index | 构造违反当前 BR 的状态，不能形成真实用户路径 | 不采用，仓库集成测试也不借此冒充合法并发 |

指针防御继续保证：APPROVE 的前置值必须来自正式详情，实际值不相同则409且无部分写；NONE 与缺失不同；批准时 Review/Revision/working/public 指针同事务更新。此防御可阻止错误/陈旧客户端输入并为未来经审核的并行业务保留保护，不表示当前已经存在不同修订同时可决定的路径。

## 已接受的权威文字调整

以下为用户接受时的文字记录。UC016 已在本次更新中落地，当前规则以该 UC 为准；Console UC007 的接受文字已交接，原工作区未修改。

### UC016 BR-PRF-030 的解释句

建议保留字段、前置匹配与自动公开规则，将“指针前置值使两个针对不同 ProfileRevision 的并发批准……”的解释替换为：

> 公开指针前置值防止错误或过期的客户端预期静默覆盖当前公开资料；不匹配时不写入决定或公开指针。按 BR-PRF-006 与 BR-PRF-026，同一 Application 当前仅有一个 DRAFT/SUBMITTED 工作修订，批准或拒绝并释放工作位后才能创建下一份；当前不将不同修订同时待审并发批准列为可达用户场景。此说明不放宽指针前置校验、一次性决定或原子写入。未来如开放并行工作修订，应另行接受业务设计并补相应真实并发验收。

### Console UC007 验收4

建议用以下文字替代现有第4项，保持其它验收项及 BR-CRV-006 不变：

> 4. 同一 Review 的双 Reviewer 决定经真实链路验证最多一个成功，另一个按稳定冲突 reason 重读，不自动重放。按单工作位规则验证首次批准后顺序创建、提交并批准下一修订，以及当前公开指针与历史投影。公开指针前置冲突单列为协议防御验收：一条合法 PENDING 使用与正式当前指针不相符的 expected 值时真实返回409且无部分写；该负例不称为“不同修订并发”。前端对该 reason 的重读、展示替换目标、清空确认和重新评审由明确标注的组件/状态恢复证据验证，不伪造为当前可达的浏览器业务竞态。revision、策略变化、响应丢失与权限撤销仍按规定恢复；需要正式准备能力的项保持待验收。

App 的验收说明同时补充可达性分类，避免留下“完整 UC 必须先构造两份 PENDING”的隐含要求。UC013 BR-PRF-006 不改，UC031 公开资料读取契约不改，决定 Proto/error reason 不改。上述措辞由用户先审核，后续各所有者分别修改权威正文及其派生 brief；不在本轮自行接受或删除验收。

## 后续联合验收分层设计（本轮不新增测试）

| 层级 | 合法准备与观测 | 可以证明 | 不能冒充 |
| --- | --- | --- | --- |
| 真实业务 E2E | 正式创建/提交 R1，工作位占用时创建 R2 被拒；Q1 决定后才创建/提交 R2；批准后 Admin→Developer 查询实际指针/两份历史 | 单工作位可达性、释放、顺序替换与公开投影 | 不同修订并发批准 |
| 同一 Review 实际竞争 | 两个真实 Reviewer 使用同一 Q1 的正式详情同时决定，实际200/409和唯一 decision | 一次性决定、冲突后重读 | 不同修订的 pointer 冲突 |
| 协议防御负例 | 先经正式批准留下 P0，再经正式下一次批准形成 P1，再创建/提交唯一工作 R2；仅在 R2 请求中故意传历史 P0，正式当前指针为 P1 | 错误/过期 expected pointer 的409、无部分写和正确正式读回 | 浏览器从有效详情加载后真的遭遇同 App 另一待审修订抢先批准 |
| 前端组件/状态恢复 | 显式提供 PublicationConflict 作为组件边界输入，检查重读、重新展示资料、清空批准确认与禁止自动 POST | UI 对稳定错误协议的恢复行为 | 实际后端竞态或真实浏览器 E2E；不把合成响应混入生产链 |
| Domain/Mongo 原子边界 | 在一个合法工作位中验证 expected 匹配、NONE/缺失/错误值、事务回滚与一次性决定；已有策略/管理员变更竞争分别标识 | 指针防御、不变量和事务性 | seed 两个平行 PENDING 取得的虚构用户路径 |

既有同 Review 200/409、错误 expected pointer 协议409、首次批准和顺序替换、Admin→Developer 指针投影均已有证据；这些记录保留其原范围。本次是验收口径审查，不要求重复无变化全量，也不把已有证据改名为缺失场景。将来实施获批的设计或更换实际输入后，再按所有者统一门禁执行新增专项和完整联合验收。

## 审核结论与落地边界

用户已接受 A：保留单工作位与指针前置防御，按可达性分层验收。UC016 BR-PRF-030 已澄清，UC031 读取及验收说明已关联，不修改 UC013 的单工作位、不新增产品UC/ADR/API或历史重新发布能力。Console UC007第4项已接受文字已在本次整合main中落地，见交接状态；不把文档同步等同于新增实现或验收完成。

本轮完成文档更新与派生 brief，不修改实现或运行环境、不执行联合验收、不 commit/push。策略/Scope 依赖仍遵循各自已接受来源；Cookie 恢复架构不在本次范围。
