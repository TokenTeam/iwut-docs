# 正式审核策略 A→B：候选内容与联合验收工作包

状态：`SUPERSEDED`。2026-11-11，本方案退出本轮，保留2026-11-09的候选推导和引用作为历史记录。系统尚未上线，本轮直接采用已接受的新审核策略，不要求A→B迁移或另造候选政策作为接口接入、代码合入、镜像发布和验收的前置。

下文Version v4/Profile v2及新增人工检查未获接受，不构成正式政策或实施授权；“本次待补”“用户可选”“接受后”等均为当时草案语境，不是当前待办。已接受UC/ADR及既有提交绑定、并发与恢复机制保持有效；未来若确有新增政策业务需求，再独立提出和审核。当前范围见[实现入口](../implements/README.md#当前实现覆盖)。

## 已有设计与实际缺口

| 项目 | 核查结论 |
| --- | --- |
| 业务规则 | 已接受的 [UC004 提交/发布](../use-cases/UC-APP-004-submit-application-version-review.md#策略绑定与提交并发)、[UC005 正式发布与读回](../use-cases/UC-APP-005-decide-application-version-review.md#策略正式发布与运维读回)、[UC015](../use-cases/UC-APP-015-submit-application-profile-revision-review.md)、[UC016 BR-PRF-028](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028) 和 [ADR004](../adr/ADR-004-mongodb-transactions-and-schema-management.md#政策发布回执与恢复) 已定义每类唯一 ACTIVE、提交绑定、原子退休/激活与回执、历史重入和未知结果恢复 |
| 后端原语 | App 当前本地 `3c611d9` 中 `internal/adapter/mongo/review_policy_release.go` 已有窄的内部 applyReviewPolicyRelease，固定清单、原内容校验、同事务 ledger、历史重放不重新激活；不是公网接口或通用 CLI |
| 组件证据 | [提交绑定实施记录](../implements/2026-11-04-submission-bound-review-policy-implementation.md) 有 Version/Profile A→B、竞争提交、回滚和 unknown commit 的真实 Mongo 组件证据，使用明确标记的隔离测试政策；不能替代真实候选发布后的 Console 联合证据 |
| 实际入口 | 当前 migrate 只跑已编入序列的 migration；未检出获批 B 的专用发布 migration，也未检出生产政策 B。通用 applyMigration 命中 ledger 就跳过，不能替代发布原语的清单重入核对。当前普通 readiness 只检查事务拓扑和最新 schema ledger，不输出指定政策发布回执/定义/current ACTIVE 的完整校验结论 |
| 本次待补 | 用户选择真实候选内容、指定验收环境及发布责任人；之后才交付专用受审发布包及其最小只读核验，再通过真实 Session/Gateway/Console 链验收 |

因此无需重新设计一套泛化发布治理 UC/API。既有 UC/ADR 仍是唯一机制权威；接受候选后，只补政策正文的权威修订、专用实施 brief/发布清单及验收计划。任何超出现行机制的变更仍须另交审。

## 当前 A 与候选 B

当前基线来自文档和初始化代码，**不是本次对某个运行数据库的现场查询**：Version A=`app-version-review-v3`，四项完整人工检查；Profile A=`app-profile-review-v1`，两项完整人工检查。执行前必须从目标环境的正式只读校验重新确认。

### 候选 V：Version v4 增加脚本用途人工核对

候选版本名 `app-version-review-v4`。保留 [v3 四项 ID、顺序及正文](../use-cases/UC-APP-005-decide-application-version-review.md#v3-正式人工检查定义) 逐字不变，末尾新增一项，对全部新提交均需明确确认：

| 字段 | 候选值 |
| --- | --- |
| id | `script-dependencies-reviewed` |
| title | 爬虫脚本用途与应用声明 |
| description | 已逐项阅读本次审核快照引用的固定脚本版本及其可读取的原文、摘要和审核事实，确认脚本所声明的采集用途与应用实际展示的功能和访问请求相符，未发现与该应用用途无关的额外采集目的。引用为空时，明确确认本次快照未依赖平台脚本。无法读取固定引用或无法完成用途核对时，不得确认通过。 |

这是**新增人工义务**，不只是改版本号：含脚本版本需要应用 Reviewer 通过 UC030/048 的受限正式读取逐一观察；无脚本版本也需明确确认“无依赖”。新 B 下缺该项不能批准；A 下仍只按 A 原有四项确认。它不要求 App 解析 JSON/Lua、不运行脚本、不新增机器检查状态或证据字段，也不改变独立脚本 Reviewer 的权限/利益冲突或人工政策。

UC048 的脚本获批、精确版本/digest 与依赖一致性仍为独立后端批准门禁；新人工勾选不能替代该门禁，也不授予应用 Reviewer 全部脚本管理权限。

### 候选 P：Profile v2 增加主体表述核对

候选版本名 `app-profile-review-v2`。保留 [v1 两项 ID、顺序及正文](../use-cases/UC-APP-016-decide-application-profile-revision-review.md#br-prf-028) 逐字不变，末尾新增一项：

| 字段 | 候选值 |
| --- | --- |
| id | `profile-identity-reviewed` |
| title | 主体与认证表述 |
| description | 已检查本次资料快照中的显示名称和简介，未发现冒充平台或其他主体、伪造官方认证或授权关系、或诱骗用户交付账号凭据的表述。简介为空时仍须检查显示名称；无法完成判断时，不得确认通过。 |

新 B 对 Profile 新增独立人工确认，缺项不能批准；不引入机构证明材料、外部认证标准、自动人员校验或新的 icon 解析/托管要求。A 的两项原义保持不变。Profile 工作修订/公开指针 CAS、拒绝终态及一次性决定不变。

### 用户可选范围与影响

| 选择 | 真正业务影响 | 能关闭的联合证据 |
| --- | --- | --- |
| 同时接受 V 和 P（建议用于覆盖两类完整链） | Version 增至5项、Profile 增至3项；新增人工核对成本，分别发布 | Version 与 Profile 两套 A→B |
| 只接受 V 或只接受 P | 只改变所选政策；另一类保持 A | 仅所选类；另一类真实切换仍待准备 |
| 修改候选正文后再审 | 按最终获批语义准备清单 | 审核前不发布 |
| 当前无业务需要，暂不新增政策 | 不制造同义版本，不扩大检查义务 | 保留已有组件证据；真实 A→B 继续待准备 |

这些版本名与正文均未成为正式政策。不因用户要求“补测试”自动选择任一候选，不修改 ScriptReview 的 `crawler-script-manual-v1`，不恢复旧实验策略或提供旧客户端兼容。

## 环境与固定发布包

建议首轮使用用户指定的**独立验收环境**：真实 Auth、App、Gateway、Console/BFF 的固定源码/生成客户端/镜像，同一事务型 Mongo，正式注册/设备登录及实际 Reviewer 授权；不是 mock policy provider、测试专用发布路由或直接改库。可以是本地隔离固定镜像栈，不据此声称已在共享环境或生产发布。

执行授权另行明确环境、部署主体、受审清单和窗口。不得默认连接现存用户库、自动重建用户数据，或在普通服务实例启动时悄悄切换。

每个 policyKind 独立一份专用发布 migration，放入获批发布二进制并从既有 migrate 序列调用窄的内部原语。Version、Profile 不组成一笔跨种类事务；建议先 Version 验收并收证，再 Profile。第一类成功/第二类失败时如实报告部分发布，不能回拨第一类，也不能把整个批次写成已完成。

具体实现须让这类专用条目在账本已存在时仍进入原语的“核对原清单和历史”分支，不能被现有通用 applyMigration 的提前跳过吞掉核对，也不能把通用“apply 后补一条账本”当作发布原子成功的依据。不要求重构所有 schema migration；只为代码化的获批发布条目衔接事务内回执及始终执行的只读核验。必须从真实 migrate 入口重复执行并验证这一点，不能仅测内部 helper。

发布清单至少固定：

- policyKind、原 ACTIVE A 与完整不可变原内容、新 B 的完整内容/顺序及全新版本名。
- 正式分配的唯一 migrationId、批准记录、部署平台 releaseId/构建来源、清单摘要、App commit/镜像 digest、生成 API 与 Console/Gateway/Auth 输入。
- 旧 A 待审与历史样本、B 提交样本的准备计划和目标环境标识；样本通过正式业务命令创建。

这里 releaseId 是部署批次/审计关联，不再发明第二个政策业务标识：清单明确 `(releaseId, policyKind) → migrationId`。现有原子 ledger 以 migrationId 为持久成功键，并保存 kind、from/toVersion、manifestHash、appliedAt；同批两个 kind 有各自标识。migration 编号在接受及实际实施时按当时序列分配，本草案不占用编号。

同 ID 不同清单拒绝，不能改已有 migration 内容；A→B 与 A→C 竞争失败方停止，不自动重基为 B→C。只对代码化、已批准清单执行发布，不接收任意 JSON 政策的通用在线 CRUD/CLI。

## 最小运维读回与未知结果

接受后，专用发布包必须补足现有普通 readiness 尚未提供的只读核验：由受限发布作业在同一次 majority snapshot 核对指定 migration 的原子回执、A/B 不可变定义与唯一当前 ACTIVE，输出可关联 releaseId / migrationId / manifestHash 的脱敏工件。可以依附现有迁移校验，不新增公网运维 API、Console 发布按钮或通用 policy-status 服务。普通 `/readyz` 200 和一条“migrations applied”日志都不构成这份证据。

| 观察 | 操作规则 |
| --- | --- |
| 正常成功 | 核对同一受审清单的原子回执、完整定义与当前选择；保留工件，不只信退出码 |
| 响应/进程结果未知 | 先按 ADR004 恢复原事务提交，再以原 releaseId 对应的原 migrationId/原清单读取；不换 ID，不直接重发激活 |
| 回执存在且事实匹配 | 认定该次历史发布成功；即使以后另有获批 B→C，重读 A→B 不重新激活 B，也不把当前 C 报为 B |
| 未找到回执 | 不能单凭缺失认定失败/回滚成功。停止发布推进并核实原事务及同次一致事实；仅在已证明未执行/已回滚后，才允许用原 ID、原清单安全重试 |
| 回执/定义/唯一 ACTIVE 不一致，或存储不可用 | 停止并报告，分别保留损坏与暂不可用证据，不覆盖账本、改库或产生补审记录 |

不能以自动重新激活 A 来“回滚”B。发布包交付/验收失败先停止后续步骤并修复；政策本身需要纠正时另审全新版本。已存在且定义完整的 A 绑定不会单因这次全局切换而失去审核资格。

## 逐类串行联合验收

每类按下表独立执行，样本和角色 ID 写入验收工件。Snapshot、binding、decision 和政策完整定义均通过正式读回固定，不能仅断言 HTTP 状态码。

| 步骤 | 正式动作与预期 |
| --- | --- |
| 0. 固定输入 | 核对唯一 A 与完整定义、环境/schema、来源镜像和 API；确认正式客户端/BFF可消费绑定政策完整定义及新增合法检查ID，不把初始4项/2项硬编码为永久集合，不凭ID猜文字；准备真实开发者、非利益冲突 Reviewer；Profile 当前仅一工作修订，多个 pending 样本用不同应用 |
| 1. A 下准备 | 用正式创建/编辑/提交 API 产生至少两份 A PENDING（分别用于批准/拒绝）、一份 A 既有终态；在真实页面打开 A 详情并明确确认 A 的检查 |
| 2. 发布 B | 由授权部署主体运行专用受审 migration，取原子回执与最小运维读回；A 退休、B 成为唯一 ACTIVE，没有零/双 ACTIVE 可见窗口 |
| 3. 保留 A 待审 | 页面与重新查询仍返回 A 全部原定义；页面不因 B 发布清空其 A 确认或强制重提。分别按 A 批准/拒绝，decision 版本等于绑定，不要求 B 新检查 |
| 4. B 下提交 | 新提交绑定 B，详情显示 B 新增检查；少确认新增项应失败且不落部分决定，按完整 B 检查可成功；拒绝仍只要求空检查集和有效理由 |
| 5. 再提交与历史 | Version 的 A 拒绝后按 UC006 恢复/再提交应新建 B attempt，旧 A 历史不改；Profile 拒绝保持终态，按UC013/015新建下一修订并绑定 B，不制造 Profile 恢复命令 |
| 6. 错版本与其他冲突 | 用 B 版本去决定 A attempt 报原 PolicyMismatch；缺/坏绑定定义为损坏，不能换当前策略降级。权限撤销、Scope/URL/OAuth、脚本依赖、利益冲突与 Profile 当前公开指针冲突按各自当前规则失败/恢复，清确认的原因不能伪装成“A退休” |
| 7. 决定未知 | 只读回同一 Review/Version/Profile 和指针事实确认原命令结果，按现行规则处理；不因通知或发布回执推测决定成功，不自动重放一次性决定 |
| 8. 发布重复/未知 | 用相同专用发布输入核对回执，证明无第二份发布或旧策略重新激活；丢失作业结果后按上一节恢复，区分未确认与已证明成功 |

提交与发布的两个胜序、并发 A→B/A→C、提交前回滚、原事务 unknown commit，以及更晚 C 后重读 A→B，保留真实 Mongo 受控组件测试；不为这些负例在共享环境发布未获批 C，或在生产启用测试 failpoint。可在独立可销毁验收栈受控截断**作业结果**验证只读恢复，但不能把网络丢结果等同于数据库 UnknownTransactionCommitResult 的全部语义。

前端 evidence 必须覆盖正式 Cookie/ForwardAuth→Gateway→App、现有 Reviewer 详情/决定与历史消费；HTTP/原生 gRPC/gRPC-Web 的后端契约证据按现行分工补足。后台组件测试、三协议结果和 React 页面证据分别记录；普通套件全绿、伪造版本不匹配负例或 mock A/B 不关闭真实联合验收。

## 接受后的交付与当前待决策

1. **政策内容**：接受 V、P、两者，还是修改/暂缓？所有新增文本需用户或指定政策责任人明确批准。
2. **验收环境**：建议独立固定本地镜像栈；若选择共享环境，需指定环境与部署主体。设计接受不自动授权任何现存环境切换。
3. **顺序**：接受逐类独立发布、先 Version 后 Profile、每步先核验回执再推进的工作包吗？

审核后才把获批正文收敛至 UC005/016 对应政策章节并生成 brief，交付代码化专用发布包、最小运维核验和测试；App、Gateway、Console 由各 owner 按固定输入实施，不新建泛化发布产品。需要更新的 Console UC006/007 验收由 Console owner 按其审核流程处理。

当前结论：机制设计和后端原语已有，真实新内容及具体发布/联合验收包待审；本页没有运行发布，没有读取运行数据库，没有把任何候选标为 ACTIVE 或把联合验收标为完成。
