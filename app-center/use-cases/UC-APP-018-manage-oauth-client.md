# UC-APP-018：管理应用 OAuth Client

状态：`PROPOSED`

## 目标与范围

Application 当前管理员为一个明确的运行接入上下文登记 OAuth client，查询元数据、轮换 confidential secret、禁用或重新启用 client。OAuthClient 只保存稳定身份、客户端类型和凭据状态；回调地址与 scopes 属于受审核、可发布的 ApplicationVersion。

App Center 不签发用户 token、不保存 consent，也不把 launchUrl 推断成 redirect URI。

## 输入与输出

管理方法、client 字段、secret 编码与返回约定见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。所有命令使用既有可信 USER 身份，领域层从身份取得操作者，不接收请求体 adminId/developerHandle 覆盖。

## 主流程

创建：

1. 校验操作者为当前 Application 管理员，当前 Developer 为 `APPROVED`。
2. 校验 type/channel/rpcApiMajor，并读取同一 application、channel 和 exact RPC major 的当前 Publication、APPROVED Version 及批准 snapshot。
3. 从该 Version 对应 client type 的 `oauthRedirects` 取得回调组，按规范 hostname 派生不可变 sector；没有回调组时拒绝创建。
4. 分配 clientId；CONFIDENTIAL client 同时生成高熵 secret。
5. 在同一事务中通过 Application 管理员写栅栏复查归属，写入 client、secret 摘要与不可变审计。
6. 仅在确定提交后返回元数据；confidential secret 只在本次成功响应出现。

状态变更与轮换：

1. 校验当前管理员、Developer 门禁和 expectedRevision。
2. 状态变更只接受 `ACTIVE` 或 `DISABLED`；轮换只适用于 CONFIDENTIAL client。
3. 在同一事务中复查管理员栅栏，递增 configRevision，写 client 与审计。

## 业务规则

<a id="br-oac-001"></a>
### BR-OAC-001：应用归属与接入身份

只有当前 Application 管理员且符合 Developer 门禁者可管理 client。应用身份继续使用 UUID；clientId 是独立 UUID，永久不重用，不因应用名称、管理员或 Developer 公开 ID 变化而变化。

同一 `(applicationId, channel, rpcApiMajor, type)` 唯一。一个 Application 可以为不同运行环境、RPC major 和 client type 拥有不同 client；PUBLIC 与 CONFIDENTIAL 是两个身份，不能用同一个 clientId 在两种认证方式间降级。创建 client 不代表用户已经 consent，也不扩大 Version 已审核的 scopes。

<a id="br-oac-002"></a>
### BR-OAC-002：不可变接入上下文与版本化回调

`applicationId/type/channel/rpcApiMajor/sector` 创建后不可修改。首版 channel 只支持 `TEST`；版本选择由 UC-APP-019 决定，不提供 STABLE 占位成功。

OAuthClient 不保存 redirect URI。创建 client 必须存在 exact-major TEST Publication，其 Version 为 APPROVED、与批准 snapshot 一致，并且 snapshot 中为该 type 提供非空 `oauthRedirects`。sector 从该回调组唯一的规范 DNS hostname 派生。后续发布可以更换路径或端口；同一 client type 的 hostname 必须保持 sector 一致。需要改变 hostname 时创建新的 clientId。

Version 可以省略某一 type 的回调组；该发布生效后，对应 client 暂时不可授权。App Center 不回退到历史 Version、client 旧配置、launchUrl 或前端上报的 URL。

<a id="br-oac-003"></a>
### BR-OAC-003：高熵 secret 与一次披露

PUBLIC 不产生或保存 secret；CONFIDENTIAL 由 App 服务端生成，只存摘要。具体随机性、摘要域隔离和验证接口见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。不允许用户设置弱 secret，不提供读取旧 secret/摘要接口，不向浏览器包、移动安装包或宿主子应用注入 confidential secret。

轮换只保留一个当前 secret，旧 secret 立即不再通过验证。丢失响应时先查询元数据，再发起新轮换；不保存可重放明文响应。

<a id="br-oac-004"></a>
### BR-OAC-004：配置版本与原子管理

client 状态变化和每次 secret 轮换递增 `configRevision`；相同状态请求为 no-op，不增版本。redirect URI 或 scope 随 Version/Publication 变化，由 `versionId/publicationRevision` 表达，不增加 client 的 configRevision。expectedRevision 冲突不能覆盖。

修改与当前管理员/Developer 门禁按现有 App 命令一致性策略确认，事务包含配置和审计；并发创建由唯一约束收敛。旧授权凭据同时绑定 client 配置版本和运行版本资格；重新启用不恢复旧 revision。状态停用保留记录，不释放 clientId。

<a id="br-oac-005"></a>
### BR-OAC-005：scope 与授权所有权

Client 配置不新增可由管理员自由编辑的 scope 白名单。当前批准 Version 声明的 requiredScopes/optionalScopes 由版本审核和发布规则决定，UC-APP-019 对 Auth 提供；scope 语义、consent、code 和 token 归 Auth。

管理查询只返回当前管理员所需元数据；审计记录操作、ID/revision 和状态变化，不记录 secret。API 访问日志、HTTP 缓存和 trace 同样不能保留秘密。

## 验收场景

- 普通用户、其他应用管理员和已转让的旧管理员拒绝；并发转让与轮换不能越权。
- PUBLIC 没有 secret；CONFIDENTIAL secret 只返回一次，读取永远不含明文或摘要。
- 同上下文并发创建至多一条；CAS/no-op/禁用后重新启用保持单调 revision。
- 没有 exact-major TEST 发布、Version 未批准、snapshot 不一致或该 type 无回调组时不能创建。
- sector 从已审核回调组派生；改变回调 path/port 不换 clientId，改变 hostname 必须换 clientId。
- Version 切换后不读取 OAuthClient 内的旧回调，也不使用 launchUrl 兜底。

## 依赖与实现边界

依赖 UC-APP-002 至 UC-APP-005 的 `oauthRedirects` 版本字段与审核快照、UC-APP-007 的发布一致性检查、既有 Application/Developer 可信身份、Mongo 事务和管理员写入栅栏。UC-APP-019 提供 Auth 内部查询。Proto/HTTP 路由仍需独立 API 工作包。

## 变更记录

- 2026-09-27：建立 OAuth client 管理设计。
- 2026-09-27：redirect URI 改由 ApplicationVersion 保存、审核和发布；OAuthClient 仅保存独立身份、类型、sector、状态与 secret 生命周期。
