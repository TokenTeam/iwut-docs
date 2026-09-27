# UC-APP-018：管理应用 OAuth Client

状态：`PROPOSED`

## 目标与范围

Application 当前管理员为应用登记 OAuth 接入配置，查询配置、轮换 secret、禁用/重新启用 client。扩展当前 App 只保存版本 scopes 的边界；不在 App 签发用户 token 或保存用户 consent。

## 输入与输出

管理方法、client 字段、secret 编码与返回约定见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。所有命令使用既有可信 USER 身份，领域层从身份取得操作者，不接收请求体 adminId/developerHandle 覆盖。

## 主流程

1. 校验操作者为当前应用管理员、当前 Developer 为 APPROVED；验证 client 配置。
2. 创建时分配 clientId 与必要的随机 secret；修改/轮换时校验 expectedRevision。
3. 在同一事务中与 Application 管理员变更栅栏确认归属，写配置/secret 摘要与不可变审计。
4. 仅确定提交后返回元数据，创建/轮换的 confidential secret 只在本次响应中出现。

## 业务规则

<a id="br-oac-001"></a>
### BR-OAC-001：应用归属与接入身份

只有当前 Application 管理员且符合现有 Developer 门禁者可管理，非管理员不能读取配置或轮换。禁用能力不授予其他应用、普通 Tester 或 SYSTEM。应用身份继续用 UUID，clientId 独立、永久不重用，不因应用名称或开发者公开 ID 改变而变化。

同一 (applicationId,channel,rpcApiMajor,type) 唯一；PUBLIC 和 CONFIDENTIAL 是两个独立 client，不自动共享用户授权。client 创建不代表应用批准、已发布或可被所有用户运行。

<a id="br-oac-002"></a>
### BR-OAC-002：静态回调与不可变接入配置

applicationId/type/channel/rpcApiMajor/sector 创建后不可修改。首版 channel 只支持 TEST，版本选择由 UC019 决定，不提供 STABLE 占位成功。

redirectUris 为 1–10 个绝对 HTTPS URL，单项最多 2048 字节、去重、无 userinfo/fragment/wildcard；禁止 IP literal/localhost 和响应参数 code/state/iss/error/error_description/error_uri。必须同一规范 DNS hostname，登记后按完整字符串精确匹配，不用前缀匹配、launchUrl 或运行时 URL 替代。域名规范为小写 ASCII/IDNA，拒绝非规范输入；其余 URL 不静默改写。客户端需实际控制回调处理，平台不通过请求时抓取 redirect 地址做 SSRF 式“验证”。原生回调范围见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

<a id="br-oac-003"></a>
### BR-OAC-003：高熵 secret 与一次披露

PUBLIC 不产生/保存 secret；CONFIDENTIAL 由 App 服务端生成，只存摘要。具体随机性、摘要域隔离和验证接口见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。不允许用户设置弱 secret，不提供读取旧 secret/摘要接口，不向浏览器包、移动安装包或宿主子应用注入 confidential secret。

轮换只保留一个当前 secret，旧 secret 立即不再通过验证。丢响应时查询元数据后再次轮换，不做可重放明文响应存储。

<a id="br-oac-004"></a>
### BR-OAC-004：配置版本与原子管理

有效配置变更、禁用、重新启用和每次 secret 轮换递增 configRevision；完全相同的 Update 为 no-op，不增版本。expectedRevision 冲突不覆盖。修改与当前管理员/Developer 门禁按现有 App 命令一致性策略确认，事务含配置和审计；并发创建由唯一约束收敛。

旧授权凭据绑定配置版本；重新启用不回到旧 revision。轮换会使原 code/access/refresh 在后续检查中失效，管理 UI 必须明确提示应用需重新授权；不承诺零中断轮换。状态停用保留记录，不释放 clientId。

<a id="br-oac-005"></a>
### BR-OAC-005：scope 与授权所有权

Client 配置不新增一套可由管理员自由编辑的 scope 白名单。当前批准版本声明哪些 scopes 由既有版本审核/发布规则决定，UC019 对外提供；其语义及用户 consent 归 Auth。创建 client 不授予资料访问、Reviewer 权限或学生关联标识。

管理查询只返回当前管理员所需元数据，审计记录操作、ID/revision、配置变化，不记录 secret。管理 API 的访问日志、HTTP 缓存和 trace 同样不能保留秘密。

## 验收场景

- 普通用户/其他管理员/已转让的旧管理员拒绝；并发转让与轮换不能越权。
- PUBLIC 没有 secret，CONFIDENTIAL 只返回一次；读取永远没有 secret/摘要。
- 同配置并发创建至多一条；CAS/no-op/禁用后重新启用保持单调 revision。
- 多 hostname、wildcard、恶意回调、已占响应参数拒绝；launchUrl 不自动登记。
- 未发布应用可准备配置，但 Auth 不能据此给没有资格的用户发 token。

## 依赖与实现边界

依赖既有 Application、Developer 可信身份、Mongo 事务/管理员写入栅栏；无需先有 OAuth 用户授权实现。UC019 提供 Auth 内部查询。Proto/HTTP 路由仍需独立 API 工作包，这里不在 docs 复制可执行 Proto。
