# App Center 首版产品范围

状态：`PROPOSED`

## 文档目的

本文位于 [愿景](vision.md) 与具体 Use Case 之间，用来回答两个问题：

1. 首版要让哪些参与者完成怎样的端到端旅程？
2. 哪些能力属于这条旅程，哪些能力留待以后？

本文不新增业务规则，也不替代 UC 中的 `BR-*` 权威正文。文中描述的是产品范围和设计方向；具体状态迁移、不变量、权限与并发语义仍由后续 UC 和 BR 定义。

## 首版结果

首版完成后，获批开发者可以把一个网页应用从登记和编辑推进到审核、封闭测试、灰度发布和稳定发布；官方客户端可以取得发布层面可用的候选应用及其 Filter 规则，在本地根据用户信息形成展示列表，并使用 App Center 解析的服务端发布目标启动应用。

这条旅程的产品闭环是：

```text
Developer / Admin
  创建 Application
      │
      ├─ 准备并提交公开资料 ── Reviewer 审核
      │
      └─ 准备并提交运行版本 ── Reviewer 审核
                                  │
                                  ▼
                           Test → Grey → Stable
                             │       │       │
                             └───────┴───────┘
                                     │
                                     ▼
Server Publication ── Test/Grey/Stable 解析 ── 候选应用与启动目标
                                                    │
                                                    ▼
Client User Data + Filter 规则 ──────────────── 最终展示列表
```

运行版本的审核与发布保持分离：版本审核只产生渠道无关的槽位发布资格，Test/Grey/Stable 各自选择 APPROVED Version 并执行自己的渠道规则。公开资料采用更简单的首版流程，资料审核批准后自动成为当前公开资料。公开目录资料与运行版本仍相互分离，可以独立修订和审核。Filter 与 Test/Grey/Stable 同样保持分离：前三者由服务端解析发布目标，Filter 规则由服务端保存和发送、由客户端使用本地用户信息执行。

## 参与者

| 参与者 | 首版目标 |
| --- | --- |
| Developer / Application Admin | 登记应用，维护资料与版本，组织测试，控制发布和回退 |
| Reviewer | 审核确定的版本或公开资料快照，并留下可追溯决定 |
| Tester | 通过加入链接取得 Application 级测试资格，并使用兼容的 test 版本 |
| 普通用户 | 在官方客户端中取得候选应用，由客户端执行 Filter 后看到最终列表，并使用已解析的发布目标 |
| 平台运营者 | 在内容或运行风险出现时停止分发，并查看必要的审核与发布历史 |

Auth 继续拥有身份、Developer 资格、Reviewer 权限和 Scope Catalog；App Center 不收集师生证明材料。

## 首版用户旅程

### 1. 开发者完成应用准备

开发者资格获批后，用户创建 Application，并成为当前管理员。管理员可以查看和修改尚未被业务身份固定的应用信息；需要停止维护时使用可审计的归档行为，而不是物理删除记录。

管理员分别准备两类内容：

- `ApplicationProfileRevision`：面向目录展示的名称、简介和可空 icon 字符串；icon 暂不具有受控资产语义。
- `ApplicationVersion`：入口 URL、RPC API 兼容范围、宿主能力要求、scopes，以及依附 Version 的 pkce/confidential redirect URI 配置。

两类内容各自采用草稿修订和审核快照。公开资料修改不制造虚假的运行版本，运行版本发布也不隐式改变公开资料。

### 2. Reviewer 作出审核决定

管理员提交确定的资料或版本快照。具备相应权限且不存在利益冲突的 Reviewer 对快照批准或拒绝。运行版本拒绝后可以显式恢复原草稿；公开资料拒绝后由网页端预填旧内容，再创建拥有新身份的新 DRAFT。

资料审核通过后自动成为当前公开资料，不再要求管理员执行第二次发布操作，也不提供回滚到旧资料的入口。版本审核通过只产生运行版本的发布资格，仍由管理员决定是否放入 Test、Grey 或 Stable 槽位。

首版不追求通用审核工作流。单次审核、一次性决定、版本化检查策略和完整审计已经足以支撑初始运营。

### 3. 管理员进行封闭测试

管理员在应用已有当前已批准公开资料后，把已批准且兼容的 ApplicationVersion 放入某个 RPC API major 的 test 槽位，并管理 Application 级 Tester 加入链接与最多 100 个 ACTIVE Tester。

Tester 使用自己的官方客户端和实际宿主能力访问 test 版本。管理员不会自动获得测试资格；替换 test 槽位也不会移除既有 Tester。

开发版 iWUT Client 可以直接打开任意 URL 供开发预览；该入口不属于 Test/Grey/Stable，不代表内容已审核，也不向正式客户端开放。

### 4. 管理员逐步发布

测试通过后，管理员可以在同一 RPC API major 分区内配置 grey，再提升为 stable。发布过程保留槽位历史和乐观并发语义，并提供以下产品能力：

- 调整或停止 grey 分流。
- 依据 [UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md)把 stable 指向另一个已批准版本。
- 回退到历史上仍具发布资格的版本。
- 清空或紧急停止某个发布槽位的分发。

具体的状态迁移和资格复检策略留给 `ApplicationPublication` 生命周期模型和对应命令 UC 定义。

### 5. 用户发现并启动应用

官方客户端使用可信用户身份以及实际的 `rpcApiMajor`、`hostCapabilities` 请求候选应用。App Center 组合公开资料、发布槽位、Tester Membership 和版本兼容性，为每个候选 Application 解析服务端发布目标，并返回该 Application 的 Filter 规则。

对于普通用户，Application 进入服务端公开候选集的基础条件是：

- 存在当前已发布的公开资料修订；
- 请求对应的 RPC API major 存在 stable 槽位；
- stable 指向的版本对宿主兼容并保持发布资格；
- 应用没有处于归档或平台停止分发状态。

grey 只覆盖已公开应用中一部分用户的版本选择，不单独让一个没有 stable 的 Application 对普通用户公开。Tester 的 test 访问资格独立于 ordinary catalog；是否把“只有 test、尚无 stable”的应用也放入候选结果，列为本文件末尾的待定产品选择。

服务端为候选 Application 解析一个可启动版本，而不是把所有 Version 和槽位交给客户端自行选择。[UC-APP-023](use-cases/UC-APP-023-resolve-unified-launch-target.md) 已建立该统一解析提案，优先级方向为：

```text
显式 Tester 且存在兼容 test → test
否则命中 grey 分流且存在兼容 grey → grey
否则 → stable
```

任何候选版本不兼容当前 RPC API major 或缺少宿主能力时，该候选不会被返回；服务端不会跨 RPC API major 猜测回退版本。

客户端收到候选结果后，使用本地已有的用户信息执行每个 Application 携带的 Filter 规则。只有规则结果允许展示的 Application 才进入最终用户列表。原始用户信息不会为了执行 Filter 而上传到 App Center，App Center 也不计算或保存 Filter 的用户级命中结果。

## Filter 的首版边界

Filter 是独立于 Test/Grey/Stable 的客户端可见性机制：

| 概念 | 权威数据与执行位置 | 作用 |
| --- | --- | --- |
| Filter | 服务端保存并发送规则；客户端读取本地用户信息并执行 | 决定候选 Application 是否出现在当前客户端的最终展示列表 |
| Test | 服务端执行 | 为具有 Application Tester 资格的用户解析 test 目标 |
| Grey | 服务端执行 | 为命中服务端灰度分流的用户解析 grey 目标 |
| Stable | 服务端执行 | 为普通公开访问解析默认 stable 目标 |

服务端保存 Filter 规则，并随候选 Application 把规则发送给客户端；它不接收规则求值所需的原始用户信息，也不执行规则。客户端负责取得本地用户信息、执行规则并决定是否展示。[UC-APP-022](use-cases/UC-APP-022-manage-application-filter.md) 已确认 Application 级不可变 Revision、无审核立即发布和类型化 `profile-filter-v1`。

Filter 的产品定位是客户端发现和展示机制，而不是安全边界。客户端可能被修改、规则可能无法执行，用户也可能绕过展示界面；服务端鉴权、Tester 资格、scope 授权和发布目标访问仍由各自的服务端规则决定，与 Filter 结果无关。

首版 Filter 字段 key 与四种标量复用 Auth ProfileFieldDefinition 的稳定语法，缺失字段和跨语言求值语义由 [Application Filter v1](../platform/contracts/application-filter-v1.md) 固定。Filter 属于独立 ApplicationFilterRevision，不依附 Profile、Version 或 Publication。

Grey 与 Filter 不共享求值机制。[UC-APP-021](use-cases/UC-APP-021-manage-grey-rollout.md) 已接受只对可信已登录 authId 使用 per-rollout seed 的 HMAC 确定性万分比分桶；同一连续 rollout 调整比例或替换目标时保持 cohort，Clear 后重新分组。

## 首版能力范围

| 能力 | 首版纳入 | 说明 |
| --- | --- | --- |
| Application Ownership | 是 | 创建、读取、受控修改、归档；管理员转让与 Application 级禁用是否进入首版见待定项 |
| Public Profile | 是 | 资料草稿、审核、批准后自动公开和读取；icon 先作为不透明字符串 |
| Version Review | 是 | Version 草稿、编辑、提交、决定、拒绝后恢复和查询 |
| Tester Management | 是 | 加入链接、加入、移除、撤销链接和 test 目标解析 |
| Runtime Publication | 是 | 按 RPC API major 的 test、grey、stable、回退和停止分发 |
| Catalog & Resolution | 是 | 候选应用聚合、Filter 规则分发、客户端展示过滤和服务端发布目标解析 |
| OAuth/OIDC Application Integration | 扩展纳入 | Application＋channel 级稳定 PUBLIC/CONFIDENTIAL clientId、独立 secret credential，以及从批准 Version 解析回调和 scopes |
| Application Creation Quota | 是 | 保留当前按 Developer 管理的可调整配额方向 |

这里的“读取”包含开发者管理查询、Reviewer 待办查询和用户目录查询，但它们可以采用较短的 Query Contract，不需要全部扩写成与命令相同体量的 UC。

## 明确不纳入首版

- 网页托管、构建、静态资源发布或 Resource Hub。
- Expo 客户端、WebView、RPC bridge 和客户端升级机制的实现。
- Auth consent、token 签发以及 RPC 用户数据读写的执行由 Auth Center 拥有；App Center 只提供 client 与应用资格事实。
- 协作者、细粒度 Application 团队角色和多租户组织。
- 向 App Center 上传仅用于 Filter 求值的原始用户资料，或由服务端执行客户端 Filter。
- 推荐、排行、搜索相关性、评论、评分、收藏和社交分发。
- 付费、结算、广告、商业化配额和 SLA。
- 双人审批、自动 reviewer 分配、申诉委员会等通用工作流能力。
- 系统内申诉渠道；需要申诉时直接联系平台运营人员。
- AI 审核 DRAFT 或自动决定；其输入、结论效力与状态模型留给未来独立设计。
- icon 上传、资产所有权、内容寻址与失效处理等受控资产生命周期。
- 为尚未上线的旧服务维护 API 或数据兼容。

## 首版完成的产品判据

以下场景可以在不修改领域定义的前提下贯通时，首版产品闭环成立：

1. 获批 Developer 创建 Application，准备公开资料和一个网页版本。
2. Reviewer 分别审核资料快照与版本快照；资料批准后自动公开，版本批准只产生槽位发布资格。
3. Admin 组织 Tester 使用 test 槽位验证真实客户端兼容性。
4. Admin 配置小比例 grey，随后提升 stable；也能回退或停止分发。
5. 普通用户请求候选应用时，服务端只聚合具有已发布资料和兼容 stable 的 Application，并返回对应 Filter 规则。
6. 客户端使用本地用户信息执行 Filter，并由此生成最终展示列表，不向 App Center 上传用于规则求值的原始字段。
7. 同一用户在相同 rollout 配置下得到稳定的 grey/stable 选择，Tester 则优先得到兼容 test；这些发布选择由服务端完成。
8. 聚合查询为每个候选 Application 返回公开资料与唯一解析后的启动目标，不暴露无权访问的槽位或全部 Version。
9. 审核、发布、回退和停止分发均能追溯到操作者、时间和对应快照。

## 后续用例前仍需要决定

以下问题会改变尚未具体化的能力边界，应在对应 UC 开始前确认：

1. **Application 归档与禁用细节**：方向已经确定为管理员日常 clear、普通归档和平台紧急 suspension/disable 分离；仍需确定 admin/SysAdmin 权限、审计、对既有 token 的影响和重新启用条件。
2. **Test-only 查询契约**：已确定不混入普通公开目录，而进入独立的“我参与的测试”入口；仍需定义分页、移除后的可见性和无兼容 test 时的结果。
3. **管理员转让**：它是首版 Ownership 的必要能力，还是进入首版后的下一阶段治理能力？
4. **受控图标资产**：当前 icon 只是可空不透明字符串；何时升级为受控资产、由谁拥有并如何迁移，等待真实需求后决定，不阻塞首版资料审核。
5. **Filter 客户端交付**：App Center 规则模型与管理流程已由 UC-APP-022 确定；官方客户端仍需实现求值器、共享向量和管理 UI。

这些选择不阻塞当前已有 UC-APP-001 至 UC-APP-016、OAuth/OIDC 扩展 UC-APP-018/019 以及 Stable/Grey UC-APP-020/021 作为需求发现成果保留，但会影响后续 Capability Map、领域模型和生命周期模型。

OAuth 身份隔离：client/credential 按渠道隔离；major 共用同渠道 client。Application 级 sector 与用户 sub 仅由 Auth 保存，App 仅提供 client 归属及批准回调事实，见 [提供方契约](../platform/contracts/app-oauth-client-v1.md)。
