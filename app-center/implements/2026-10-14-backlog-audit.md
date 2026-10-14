# 2026-10-14 App Center 串行工作与相邻服务交接

状态：`ACTIVE`

## 执行边界

用户已授权按顺序执行 App Center 后端与对应 API 的工作。新增或修改 UC、BR 或业务语义时，先准备具体设计与影响范围，再暂停等待用户审核；审核通过前不实现该设计。Auth、Gateway、Console 的代码由用户另行安排其他 agent，本任务只记录需求或准备待审核设计，不向其他 agent 发送任务。

客户端目录及客户端 Filter 求值暂缓。版本批准资格撤销、告警可靠投递和受控 icon 资产暂缓。Tester 主动退出测试纳入后续串行工作。

| 顺序 | 工作事项 | 当前状态 | 完成边界 |
| --- | --- | --- | --- |
| 1 | 核对 UC002–005 实现与验收 | 已完成证据核对；保留 IN_PROGRESS | 不把提供方完成或局部跨服务测试解释为完整用户旅程验收；具体剩余验证见下文 |
| 2 | HTTP 可观测性归类修复 | COMPLETE；check-full 23/23 | 与生成 handler 的 RPC operation 对齐，保持有界白名单；真实 HTTP 回归与 make check-full |
| 3 | [管理员公开资料修订查询 UC039](../use-cases/UC-APP-039-query-owned-application-profile-revisions.md) | PROPOSED / NOT_STARTED，已暂停待用户审核 | 明确管理员列表/详情、历史与隐私边界；审核通过后再生成 brief、实现 API/后端并验收 |
| 4 | Tester 主动退出测试 | 待顺序启动 | 先审核本人退出、episode 历史、幂等/重新加入、容量与运行资格语义，再实现 |
| 5 | App Center 验收与交付收尾 | 待顺序启动 | 完成适用门禁及覆盖记录；相邻服务阻塞交接给用户 |

## UC002–005 证据核对

核对基线为 App `cda84cd` / API `aee1dc6` 加当前未提交工作树，以及本地权威 docs。历史完整门禁 `.artifacts/verification/20261013T073004Z-lgywaop5/report.json` 为 cross-service 26/26 通过、`changed_sources=[]`；该结果仅属于报告记录的输入，不代表后续新增场景已验收。

### 已有实现与证据

- UC002–004 的 Domain/UseCase、Mongo 事务、Scope Catalog consumer/cache、HTTP/gRPC/Wire 和 OAuth 依附配置已实现，当前覆盖表已经列出。
- Auth UC001 配置 OAuth manifest 时使用 Mongo 持久化目录。UC002 Developer 状态、UC003 SYSTEM principal、UC004 两项 Reviewer 权限与 UC010 身份签发已有交付记录；不再把这些提供方写成未实现。
- App 通用真实 Auth 测试 `TestE2E_UCAPP005_026_027_RealAuthProcessServiceIdentity` 验证 service-JWS、Scope consumer、Developer 状态与 SYSTEM 自动拒绝。其管理员和 Reviewer USER JWS 是测试自行签名，Auth 未配置 OAuth manifest；该测试不能证明生产 Mongo Scope 目录或真实 Reviewer 用户身份的完整成功审核。
- UC033/036 专项配置生产 OAuth manifest，App API 完成 Version 创建、提交和批准，然后验证实际 Auth OAuth 行为；其 USER JWS 仍由测试签名，未覆盖 UC003 的草稿编辑。
- Auth 2026-10-03 的双审核权限跨服务验收验证真实 Auth 签发、权限隔离与 App verifier。允许访问的合法不存在 Review 返回 404，权限不符返回 403；它没有对真实 PENDING Review 完成业务审核。

### 尚需闭合的验收

| 用例 | 待补联合场景 |
| --- | --- |
| UC002 | 在真实 Auth 持久化 Scope 目录上，使用真实签发的管理员身份创建 Version；证明 unknown/disabled scope、目录 revision、故障与缓存过期处理 |
| UC003 | 在同一链路编辑真实 DRAFT，覆盖 Scope 变更、OCC/no-op、OAuth 配置同步与失败无部分写入；现有跨服务门禁未执行该场景 |
| UC004 | 对上述编辑后的 Version 提交真实不可变 snapshot，验证目录变化、scope 失效和提交失败边界 |
| UC005 | Auth 实际 grant/revoke Reviewer 权限并签发 USER，批准/拒绝真实 PENDING Review；验证权限撤销、两项权限隔离、Developer 暂停自动拒绝与 SYSTEM attribution |

当前不把上述四项标为 COMPLETE。新增验收应先复用现有 ACCEPTED 契约；若需要 Auth 新行为或 UC 语义修订，则暂停并交接，不修改 Auth 代码。

## 相邻服务交接事项（供用户分派）

### Auth agent

- 完成上述生产 Scope manifest、真实 Session/USER 签发和 Reviewer grant/revoke 的可复用联合验收环境；与 App agent 约定已发布镜像或固定服务/API 基线。
- 最新密码/邮箱模型与 ApplicationCloseReauth 已在 Auth 工作树演进。提供最终协议/开关与真实证明验收基线，避免拿旧设备-only 证据说明新密码门禁已闭合。
- 提供方侧不能以不存在 Review 的 404 作为真实审核成功；业务成功用 App 真实 PENDING Review 验证。

### Console agent

- 先完成 UC-CONSOLE-001 的重发、迟到响应协调、结果未知恢复及真实 Auth/Gateway/邮件验收，并核对最新 Auth 密码/邮箱协议。
- 按应用/版本、公开资料、发布/Tester、OAuth/Filter 管理拆分 Developer Console 工作包；管理员公开资料查询须等 App 新 UC 接受及 API 完成。
- 按版本审核、资料审核、平台运维拆分 Admin Console 工作包。新的业务 UC 先交用户审核；App 只提供后端与 API，不实施 Console 代码。

### Gateway agent

- 对已接受 App API 按功能批次完成 HTTP/原生 gRPC/gRPC-Web 的实际成功/拒绝联合验收，优先核对关闭 proof 与最新 Auth 协议。
- App 后续资料管理查询及 Tester 退出 API 接受/生成后，补 exact route、身份矩阵、隐私与功能开关验收；不得先设计或公开未接受的 API。
- 生产启用与部署单独交用户审核。客户端目录、Filter 客户端求值不在本次交接执行范围。

## 待用户审核的设计点

管理员 ProfileRevision 查询目前只有 PROPOSED Query Contract。应明确跨管理员隐藏、Application 所有保留状态的读取、不可变历史/当前内容区分、完整 Review 历史的响应预算、分页游标 ownership 绑定，以及最小披露边界，再建立正式 UC。旧契约拟返回的 updatedBy 等字段与 UC034 的最小披露风格不同，不能直接照搬后实施。

UC002 的“后续接口工作”等历史文字仍描述提供方未完成。修正这些 UC 原文属于用户要求的审核暂停范围；本次核对只修实现记录，不修改 UC/BR 或生成的 brief。

## 2026-10-14 工程修复验收

- 修复 `internal/adapter/transport/observable_operations.go`：用实际注册 HTTP method/path 与 Proto HTTP annotations 的交集识别生成 handler 的 RPC operation。手工固定 route path 和未知值折叠继续保留，gRPC-only/未注册 method 不进入 HTTP RPC 白名单。
- 新增真实 HTTP 创建请求回归和 HTTP method/路由缺失/gRPC-only 白名单边界测试；修复前两项复现失败，修复后通过。
- Go 1.25.5 `make check-full` / backend 23/23 通过、`changed_sources=[]`，报告在 App 工作树 `.artifacts/verification/20261014T115805Z-twrkre1b/report.json`。真实 Mongo race 1775.715s、cmd HTTP/gRPC 141.621s，最终阶段 1783.499s；本轮没有执行真实 Auth tier。
- 被测基线为服务 `cda84cd` + 本轮未提交工程修改、API `aee1dc6`、克隆的本地 committed docs `df10243`。新审核草案和 registry 在工程验收完成后建立，只声明 PROPOSED，不作为这次后端业务验收的输入。
- 首次 sandbox quick gate 因测试临时 Git commit 继承个人 GPG 签名、无法访问签名 agent 而失败。完整验收通过进程级 `commit.gpgsign=false` 重跑，未改个人 Git 配置。Go cache 使用 `/tmp/iwut-app-center-go-cache`，Docker/Mongo 使用隔离测试资源。
- 原有未提交业务/验证文件逐文件 hash 保持不变；仅 AGENTS 的 Current work package 按本次授权更新。没有修改 Auth/Gateway/Console 代码、API 子模块、部署或 push。
- 当前暂停于 UC039 草案审核：下一步待用户接受后同步候选 Query Contract、生成 brief 并实施。Tester 主动退出保持下一串行工作，未提前建立或实现新语义。
