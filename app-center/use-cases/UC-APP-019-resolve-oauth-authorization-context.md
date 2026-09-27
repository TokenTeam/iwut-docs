# UC-APP-019：为 Auth 解析 OAuth 应用授权上下文

状态：`PROPOSED`

## 目标与范围

向 Auth 提供稳定 OAuth client 元数据、confidential secret 验证、用户登录前可验证的当前运行配置，以及特定用户的授权资格快照。Auth 不依赖客户端上报的 redirect URI、scope、Version 或批准状态；App Center 不签发用户 token。

## 输入与输出

四个精确内部方法、权限和字段见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。clientId 必填；运行解析还必须给出 channel 和 rpcApiMajor。authId 只来自受信 Auth 服务身份，不开放普通用户查询。

## 主流程

1. 验证服务 JWS、audience 和方法级 permission。
2. `GetClientConfiguration` 返回稳定 identity 元数据，并为 CONFIDENTIAL 返回当前 credentialRevision；`VerifyClientSecret` 只比较调用方刚读取的 expectedCredentialRevision 与当前摘要。
3. `ResolveClientRuntimeConfiguration` 由 clientId 找到 Application 和 type，再使用请求中的 channel/rpcApiMajor 在单个 Mongo snapshot 中读取当前 Publication、APPROVED Version/Review 及依附 Version 的 OAuth 配置，从批准 snapshot 取得该 type 的 redirect URIs 与 scopes。该方法不需要 authId，供 Auth 在登录前校验 redirect URI。
4. `ResolveAuthorizationContext` 在相同运行配置检查基础上读取指定用户当前 ACTIVE Tester，并校验调用方传入的 expected runtime tuple。
5. 返回资格版本、最小展示资料与短时快照期限；任何缺失或不一致失败关闭。

## 业务规则

<a id="br-oac-006"></a>
### BR-OAC-006：内部查询与最小披露

只允许显式配置的 Auth service principal，并按共享契约分离读取、验证、运行配置解析和用户上下文解析权限。输入中的 channel/rpcApiMajor 只能选择服务端权威 Publication，不能替换批准 redirect URI、scopes、Version 或 adminAuthId；输出不含 secret/摘要、学生资料或用户邮箱。

GetClientConfiguration 可以返回 DISABLED 元数据供 Auth 解释；VerifyClientSecret、ResolveClientRuntimeConfiguration 和 ResolveAuthorizationContext 对 DISABLED client 均不成功。

<a id="br-oac-007"></a>
### BR-OAC-007：TEST 资格与批准运行配置

首版 channel 只接受 `TEST`，并复用 UC-APP-012 的 exact-major TEST Publication；用户上下文还要求 ACTIVE Tester。必须存在 client 所属 applicationId 与请求 rpcApiMajor 对应的 testVersionId，Version 属于该应用且 APPROVED，并与批准 Review snapshot 完全一致；不可回退 draft、其他 major 或任意历史批准版本。

redirect URIs、requiredScopes 和 optionalScopes 都从该批准 snapshot 取得。PUBLIC client 选择 `pkceRedirectUris`，CONFIDENTIAL client 选择 `confidentialRedirectUris`；对应数组为空时运行配置不可用。Auth 再查当前权威 Scope Catalog；宿主 capabilities 的完整匹配仍由 UC-APP-012 执行。

<a id="br-oac-008"></a>
### BR-OAC-008：一致快照与资格版本

一次 provider 响应的 registration、Publication、Version、Review、回调和 scopes 来自同一个 Mongo snapshot。`RuntimeConfiguration` 返回 `(registrationRevision, versionId, publicationRevision, adminAuthId)`；用户授权上下文在此基础上增加 `testerMembershipId`。Auth 必须把运行 tuple 作为不可拆分值比较，不能拼接不同调用的字段。

credentialRevision 只用于一次 confidential secret 验证，不属于运行 tuple。secret 轮换不会使已建立的 grant、授权交互、code 或 token 仅因 revision 改变而失效。移除后重新加入的 Tester 必须产生新的 membership episode；发布、管理员或 client 状态变化后不能用旧查询继续成功。App 不回调 Auth；当前 Developer 状态由 Auth 自己确认。

<a id="br-oac-009"></a>
### BR-OAC-009：展示来源与失败关闭

consent 展示只能读取当前已公开 ApplicationProfile 的投影；未有公开资料时返回技术名称和明确的 fallback 标记。不能展示未经审核的 DRAFT，也不返回应用控制的 HTML。

未知 client、无 TEST 发布、对应 redirect 数组为空、非 Tester、批准事实不一致或依赖故障均不能产生可授权上下文。面向 Auth 的无资格原因使用共享错误分类，不返回空 scopes 或前端值兜底。

<a id="br-oac-010"></a>
### BR-OAC-010：登录前回调校验与两阶段一致性

Auth 必须先调用 `ResolveClientRuntimeConfiguration`，并在发起登录或任何可能跳转到应用的响应前，对请求 redirect URI 做完整字符串精确匹配。未知或非法 redirect URI 只在 Auth 本地显示错误，绝不跳转。

用户登录后，Auth 使用预登录取得的 runtime tuple 调用 `ResolveAuthorizationContext`。App 必须在同一 snapshot 复查 tuple 和 ACTIVE Tester；任一字段变化返回前置条件失败。Auth 不得把旧 runtime 的 redirect URI 与新 Version 的 scopes 或 Tester 资格组合。授权确认和 code 兑换仍重新解析并绑定精确 Version/Publication；grant 与已签发 token 是否延续则按当前允许 scopes 和资格判断，Version ID 变化本身不是撤销理由。

## 验收场景

- 服务凭据逐方法授权；错误 audience、USER token 和公网访问拒绝。
- 同一 clientId 可解析不同 exact-major Publication；请求 major 不匹配时不会回退或猜测。
- 登录前可取得当前受审核回调并精确校验，不需要伪造 authId；非法回调不发生重定向。
- 当前 Tester 正常解析；移除后重加返回新 membershipId，旧资格不能恢复。
- TEST 槽切换、major 不同、跨应用 Version、批准 snapshot 不一致或对应 redirect 数组为空失败。
- secret 轮换与 Verify 交错由 credentialRevision 拒绝混合，但不改变 RuntimeConfiguration tuple。
- 无公开资料只返回技术 fallback；存储故障不能成功输出空范围。

## 依赖与实现边界

依赖 UC-APP-018、版本依附的 OAuth redirect 配置、版本审核/TEST 发布/Tester 与公开资料读取。STABLE/灰度公开运行资格尚无 UC，不阻碍本 TEST 纵切片设计。Auth Scope Catalog 的生产来源仍需实现。

## 变更记录

- 2026-09-27：建立 OAuth 授权上下文提供方设计。
- 2026-09-27：增加用户无关的运行配置解析与登录前后 runtime tuple 检查。
- 2026-09-27：运行选择改为稳定 clientId 加显式 channel/rpcApiMajor；credential revision 与运行资格分离。
