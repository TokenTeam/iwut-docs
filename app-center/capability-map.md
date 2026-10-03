# App Center Capability Map

状态：`PROPOSED`

## 文档目的

本文把 [首版产品范围](product-scope.md) 分解为稳定的业务能力，作为产品旅程与具体 Use Case 之间的导航层。

Capability 表示 App Center 能持续完成的一类业务职责，不等于一个微服务、代码 package、聚合或 API。本文不新增业务规则；状态迁移、不变量和权限仍以具体 UC 中的 `BR-*` 为权威正文。

## 一级能力

```text
                         Identity Context
                 authId / developer / reviewer / scopes
                                  │
                                  ▼
                      Application Ownership
                    ├── Public Profile ───────────────┐
                    ├── Version Review ───┐           │
                    ├── Tester Management ├── Runtime Publication
                    └── OAuth Client Integration ◄────┤
                                                     ▼
                                          Catalog & Resolution
                                  │
                    candidate apps + Filter rules
                                  │
                                  ▼
                     Client-side Filter evaluation
```

图中的箭头表示事实依赖，不表示同步调用、代码依赖或部署拓扑。

| 能力 | 核心问题 | 主要业务事实 | 首版输出 |
| --- | --- | --- | --- |
| Application Ownership | 这个 Application 是谁管理的，是否仍处于可管理状态？ | Application、adminId、技术名称、创建配额、归档与转让事实 | 稳定 Application 身份与当前管理权 |
| Version Review | 哪个网页版本具备怎样的运行声明，它是否取得发布资格？ | ApplicationVersion、ApplicationReview、审核快照与决定 | 具备或不具备发布资格的 Version |
| Runtime Publication | 对某个 RPC API major，服务端当前选择哪些 test/grey/stable 目标？ | ApplicationPublication、槽位、grey rollout、PublicationHistory | 服务端发布目标与可追溯变化 |
| Public Profile | 普通用户看到的应用资料是哪一版，它是否已经获准公开？ | ApplicationProfileRevision、资料审核与当前公开修订 | 已发布目录资料 |
| Tester Management | 哪些用户拥有某个 Application 的封闭测试资格？ | TesterJoinLink、ApplicationTesterMembership、容量 | Application 级 Tester 资格 |
| OAuth Client Integration | Auth 应该信任哪个稳定 client、哪个已发布 Version 的回调和用户资格？ | ApplicationOAuthRegistration、OAuthClientCredential、Version oauthRedirects、Publication 与 Tester snapshot | client 元数据、secret 校验和短时授权上下文 |
| Catalog & Resolution | 当前请求有哪些候选应用，每个候选使用哪个服务端目标？ | 聚合读取模型和解析结果；不复制来源事实 | 候选应用、公开资料、唯一启动目标与 Filter 规则 |

## 能力边界

### Application Ownership

负责 Application 的稳定身份和管理权，是其他能力的共同根。创建配额属于这项能力，因为它约束 Developer 可以拥有多少个 Application，而不是版本或发布数量。

首版方向包括创建、管理视图、受控改名与归档。管理员转让是否进入首版仍未确定；即使暂缓，`adminId` 继续表达“当前管理员”而不是永久创建者。

这项能力不保存公开 displayName、简介、运行入口、发布槽位或 Tester 列表。

### Version Review

负责 ApplicationVersion 从草稿内容到审核决定的完整链路，包括运行入口、RPC API 兼容范围、宿主能力和 scopes。审核决定只产生发布资格，不直接修改 test、grey 或 stable。

这份发布资格与渠道无关。TEST、GREY、STABLE 都只能选择已批准 Version，但选择和运行时资格由各自的 Publication 逻辑负责。

已有设计覆盖版本创建、草稿更新、提交、批准或拒绝，以及拒绝后恢复草稿。管理查询、放弃未提交草稿，以及已批准版本失去资格后的处理仍需后续设计。

这项能力不决定用户实际得到哪个版本，也不保存面向目录的公开资料。

### Runtime Publication

负责按 `(applicationId, rpcApiMajor)` 维护服务端发布选择。Test、Grey 和 Stable 是三个发布概念，共享 Publication 并发控制与历史，但拥有不同的适用条件：

- Test 结合 Tester Management 提供的资格。
- Grey 使用服务端灰度分流结果。
- Stable 是普通公开访问的默认目标。

三个槽位在设置 Version 时一致要求同一 Application 的 APPROVED Version，再叠加各自规则。TEST 是已审核的小范围用户分发，还要求当前已批准 Public Profile；开发版 iWUT Client 直接打开任意 URL 属于客户端开发预览，不进入三个槽位，也不产生发布或 OAuth 资格。

已有权威设计覆盖设置 test 槽位；[UC-APP-020](use-cases/UC-APP-020-manage-stable-publication-slot.md) 已接受 stable 设置、替换、清空、回退语义和 EMPTY Publication。首版还需要 grey 设置与调整、test 清空、Application 级停止分发和统一服务端解析。

Runtime Publication 不读取客户端本地用户字段，也不执行 Filter。

### Public Profile

负责可公开展示资料的独立修订与审核。它与 ApplicationVersion 分离，因此修改 displayName、description 或 icon 不会制造新的运行版本。Profile Review 批准时自动成为当前公开资料，不再建立管理员手动发布步骤。

已有设计覆盖 displayName、可空 description 和可空不透明 icon 字符串的资料草稿创建、更新、提交审核、批准或拒绝，以及批准时自动公开。[Profile Management Query Contract](query-contracts/profile-management.md) 已定义管理员和 Reviewer 的列表/详情读取语义。SUBMITTED 继续占用唯一工作修订位，不能并行创建下一份 DRAFT；REJECTED Revision 保持终态，网页端可预填旧内容后调用普通创建用例，但服务端不提供恢复/复制接口。首版还需要面向普通用户的当前公开资料查询；受控 icon 资产是以后可选扩展，不提供旧资料回滚。

紧急隐藏不属于资料修订撤销。后续由 Application Ownership 定义 Application admin 或 SysAdmin 发起的 Application 级禁用，并统一影响目录与运行分发。

这项能力提供“展示什么”，不决定“运行哪个 Version”。

### Tester Management

负责 Application 级 Tester 加入链接、Membership episode、100 人容量和移除历史。Tester 资格不绑定 Version 或 RPC API major；实际 test 目标由 Runtime Publication 解析。

已有设计覆盖链接创建与轮换、自助加入、管理员移除和链接撤销。Tester 管理视图、主动退出是否进入首版，以及 test-only Application 的列表体验仍需确定。

这项能力不实现二维码界面，也不把 Tester 状态保存到 Auth。

### Catalog & Resolution

这是面向读取的组合能力，不拥有其他能力的源事实。它在同一查询语义中组合：

- Application 是否仍可参与分发；
- 当前已发布的 Public Profile；
- Tester Membership；
- 对请求 RPC API major 的 Test/Grey/Stable 服务端解析结果；
- ApplicationVersion 与 hostCapabilities 的兼容性；
- 随候选 Application 返回的 Filter 规则。

服务端产物是“候选 Application + 已解析启动目标 + Filter 规则”，不是客户端最终展示列表。客户端使用本地用户信息执行 Filter 后形成最终列表；App Center 不接收这些本地字段，也不保存用户级 Filter 求值结果。

已有设计只覆盖 Tester 的 test 启动目标解析。首版还需要候选列表、详情、统一发布目标解析和 Filter 规则分发契约。这些读取行为优先写成较短的 Query Contract，而不是复制命令 UC 的全部结构。

### OAuth Client Integration

负责 Application＋channel 级稳定 clientId、PUBLIC/CONFIDENTIAL 状态和独立 secret credential，并按 channel/rpcApiMajor 把当前批准 Version 的 redirect URIs/scopes 与 Tester 资格组合为 Auth 可验证的短时快照。redirect URI 属于 Version Review，运行选择属于 Runtime Publication；本能力不复制它们，也不拥有用户 consent、code、grant 或 token。

## Filter 在能力图中的位置

Filter 不是第四种发布槽位，也不参与 Test/Grey/Stable 的服务端选择。

当前把“随候选 Application 分发 Filter 规则”放在 Catalog & Resolution，把“读取本地用户信息并求值”放在客户端边界。Filter 规则的作者、审核方式、修订身份以及它最终属于 Application、Public Profile 还是独立对象，仍由后续领域模型决定。

Filter 结果只影响客户端展示。服务端的身份鉴权、Tester 资格、scope 授权与启动目标访问继续使用各自的服务端事实。

## 能力协作

| 消费方 | 使用的上游事实 | 用途 |
| --- | --- | --- |
| Version Review | Ownership 的当前 adminId；Identity 的 Developer/Reviewer 与 Scope Catalog | 管理和审核 Version |
| Public Profile | Ownership 的当前 adminId；Identity 的 Developer/Reviewer | 管理和审核公开资料 |
| Tester Management | Ownership 的当前 adminId；Identity 的 authId | 管理链接与 Membership |
| Runtime Publication | Ownership、Version Review、Tester Management | 检查管理权和发布资格，解析 test 资格与服务端槽位 |
| OAuth Client Integration | Ownership、Version Review、Runtime Publication、Tester Management | 管理 client 并为 Auth 解析登录前运行配置与登录后用户资格 |
| Catalog & Resolution | Ownership、Public Profile、Runtime Publication、Tester Management、Version Review | 构造内部一致的候选目录与启动目标 |
| 官方客户端 | Catalog & Resolution 返回的候选与 Filter 规则；客户端本地用户信息 | 执行 Filter 并展示最终列表 |

这张表描述领域事实流向。跨能力的一致性策略由后续领域模型和生命周期模型决定；它本身不隐含共享数据库或分布式事务要求。

## 当前设计覆盖度

| 能力 | 已有设计证据 | 首版主要缺口 |
| --- | --- | --- |
| Application Ownership | `UC-APP-001` | 管理查询、改名、归档、Application 级禁用；转让与禁用是否纳入首版 |
| Version Review | `UC-APP-002`–`UC-APP-006` | 查询、草稿放弃、批准资格撤销或紧急处置 |
| Runtime Publication | `UC-APP-007`、`UC-APP-020` | grey、test 清空、Application 级停止分发、统一解析 |
| Public Profile | `UC-APP-013`–`UC-APP-016`；[Profile Management Query Contract](query-contracts/profile-management.md) | 普通用户公开资料查询；受控 icon 资产为以后扩展 |
| Tester Management | `UC-APP-008`–`UC-APP-011` | 管理查询；主动退出和 test-only 列表体验待定 |
| Catalog & Resolution | `UC-APP-012` 的 test-only 解析 | 候选列表、详情、统一解析、Filter 规则契约 |
| OAuth Client Integration | `UC-APP-018`–`UC-APP-020` | TEST/STABLE 后端、API、Auth-only provider 与跨服务验证已完成；GREY 尚未设计 |

“已有设计证据”只表示存在相应设计文档；应沿链接查看其设计状态，并到 `implements/` 查看独立的实现状态。`ACCEPTED` 不等于实现 `COMPLETE`。

## 对后续设计的约束方式

后续文档按以下层次继续：

1. [domain-model.md](domain-model.md) 描述这些能力需要的聚合、实体和值对象关系。
2. [lifecycle-models.md](lifecycle-models.md) 集中描述 ApplicationVersion、ApplicationProfileRevision 和 ApplicationPublication 状态机。
3. 会改变领域状态的近期命令再扩写完整 UC；只读组合行为使用较短 Query Contract。
4. HTTP、数据库索引、缓存和 Go package 结构留到实现设计，不写入 Capability Map。

这两份模型文档与 Capability Map 共同构成本次设计检查点；具体行为仍回到近期 UC 与 Query Contract 中定义。

OAuth 身份隔离：client/credential 按渠道隔离；major 共用同渠道 client。Application 级 sector 与用户 sub 仅由 Auth 保存，App 仅提供 client 归属及批准回调事实，见 [提供方契约](../platform/contracts/app-oauth-client-v1.md)。
