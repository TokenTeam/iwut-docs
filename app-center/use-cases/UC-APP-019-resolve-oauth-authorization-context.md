# UC-APP-019：为 Auth 解析 OAuth 应用授权上下文

状态：`ACCEPTED`

## 目标与范围

向 Auth 提供稳定 OAuth client 元数据、confidential secret 验证、用户登录前可验证的当前运行配置，以及特定用户的授权资格快照。当前实现以 TEST 为基础，[UC-APP-020 / BR-OAC-012](UC-APP-020-manage-stable-publication-slot.md#br-oac-012) 在同一接口上增加 STABLE，[UC-APP-021 / BR-OAC-013](UC-APP-021-manage-grey-rollout.md#br-oac-013) 增加 GREY 和服务端 cohort 复算。Auth 不依赖客户端上报的 redirect URI、scope、Version、批准状态或 Grey 命中结果；App Center 不签发用户 token。

## 输入与输出

五个精确内部方法、权限和字段见 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md)。clientId 必填；运行解析还必须给出 channel 和 rpcApiMajor。authId 只来自受信 Auth 服务身份，不开放普通用户查询。

## 主流程

1. 使用 App Center 本地 caller registry 验证服务 JWS、固定 audience `iwut-app-center` 和方法级 permission；仅注册原生 gRPC，不生成 HTTP annotation。
2. `GetClientConfiguration` 返回稳定 identity 元数据，并为 CONFIDENTIAL 返回当前 credentialRevision；`VerifyClientSecret` 只比较调用方刚读取的 expectedCredentialRevision 与当前摘要。
3. `ResolveClientRuntimeConfiguration` 由 clientId 找到 Application 和 type，先核对请求 channel 等于登记 channel，再使用该 channel/rpcApiMajor 在单个 Mongo snapshot 中读取当前 Publication、APPROVED Version/Review 及依附 Version 的 OAuth 配置，从批准 snapshot 取得该 type 的 redirect URIs 与 scopes。该方法不需要 authId，供 Auth 在登录前校验 redirect URI。
4. `ResolveAuthorizationContext` 在相同运行配置检查基础上读取指定用户当前 ACTIVE Tester，并校验调用方传入的 expected runtime tuple。
5. 从当前已批准公开 ProfileRevision 返回最小展示资料，并把 profileRevisionId 纳入短时运行版本；任何缺失或不一致失败关闭。

## 业务规则

<a id="br-oac-006"></a>
### BR-OAC-006：内部查询与最小披露

只允许显式配置的 Auth service principal，并按共享契约分离读取、验证、运行配置解析和用户上下文解析权限。输入 channel 必须等于 client 固定渠道；rpcApiMajor 只能选择该渠道服务端权威 Publication，不能替换批准 redirect URI、scopes、Version 或 adminAuthId；输出不含 secret/摘要、学生资料或用户邮箱。

GetClientConfiguration 可以返回 DISABLED 元数据供 Auth 解释；VerifyClientSecret、ResolveClientRuntimeConfiguration 和 ResolveAuthorizationContext 对 DISABLED client 均不成功。

<a id="br-oac-007"></a>
### BR-OAC-007：TEST 资格与批准运行配置

首版 channel 只接受 `TEST`，并复用 UC-APP-012 的 exact-major TEST Publication；用户上下文还要求 ACTIVE Tester。必须存在 client 所属 applicationId 与请求 rpcApiMajor 对应的 testVersionId，Version 属于该应用且 APPROVED，并与批准 Review snapshot 完全一致；不可回退 draft、其他 major 或任意历史批准版本。

redirect URIs、requiredScopes 和 optionalScopes 都从该批准 snapshot 取得。PUBLIC client 选择 `pkceRedirectUris`，CONFIDENTIAL client 选择 `confidentialRedirectUris`；对应数组为空时运行配置不可用。Auth 再按 UC-AUTH-001/014 检查当前权威 Scope Catalog 的 enabled。Provider 保留批准 snapshot 的 scope 原值，不按 App 缓存的 requestable 裁剪返回集合，也不把快照当成运行启用证明；宿主 capabilities 的完整匹配仍由 UC-APP-012 执行。

<a id="br-oac-008"></a>
### BR-OAC-008：一致快照与资格版本

一次 provider 响应的 registration、Publication、Version、Review、当前公开 ProfileRevision、回调和 scopes 来自同一个 Mongo snapshot。`RuntimeConfiguration` 返回 `(registrationRevision, authorizationEpoch, versionId, publicationRevision, profileRevisionId, adminAuthId)`；用户授权上下文在此基础上增加 `testerMembershipId`。Auth 必须把运行 tuple 作为不可拆分值比较，不能拼接不同调用的字段。

credentialRevision 只用于一次 confidential secret 验证，不属于运行 tuple。secret 轮换不会使已建立的 grant、授权交互、code 或 token 仅因 revision 改变而失效。移除后重新加入的 Tester 必须产生新的 membership episode；发布、公开资料、管理员或 client 状态变化后不能用旧查询继续成功。App 不回调 Auth；当前 Developer 状态由 Auth 自己确认。

<a id="br-oac-009"></a>
### BR-OAC-009：展示来源与失败关闭

consent 展示只能读取 `currentPublishedProfileRevisionId` 指向的同一 Application、status=`APPROVED` 的 ApplicationProfileRevision。`ApplicationDisplay` 固定包含 profileRevisionId、displayName、可空 description 和可空 icon；不提供技术名称 fallback，不展示未经审核的 DRAFT，也不返回应用控制的 HTML。

未知 client、无 TEST 发布、没有当前公开资料、对应 redirect 数组为空、非 Tester、批准事实不一致或依赖故障均不能产生可授权上下文。没有公开资料属于运行资格未满足，返回统一 `FAILED_PRECONDITION`；指针存在但 Revision 缺失、跨 Application、不是 APPROVED 或内容损坏属于内部数据不变量异常，返回 `INTERNAL`。面向 Auth 的无资格原因使用共享错误分类，不返回空 scopes、技术名或前端值兜底。

<a id="br-oac-010"></a>
### BR-OAC-010：登录前回调校验与两阶段一致性

Auth 必须先调用 `ResolveClientRuntimeConfiguration`，并在发起登录或任何可能跳转到应用的响应前，对请求 redirect URI 做完整字符串精确匹配。未知或非法 redirect URI 只在 Auth 本地显示错误，绝不跳转。

用户登录后，Auth 使用预登录取得的 runtime tuple 调用 `ResolveAuthorizationContext`。App 必须在同一 snapshot 复查 tuple 和 ACTIVE Tester；Version、Publication、Profile、管理员或 registration 任一字段变化都返回前置条件失败。Auth 不得把旧 runtime 的 redirect URI、展示资料与新 Version 的 scopes 或 Tester 资格组合。授权确认和 code 兑换仍重新解析并绑定精确 Version/Publication/Profile；grant 的历史同意集合不因版本许可减少而删减；已签发 token 以原 channel/major 的当前资格和有效 scope 交集决定访问，Version ID 或 ProfileRevision ID 变化本身不是撤销理由。

<a id="br-oac-011"></a>
### BR-OAC-011：Auth sector 的回调事实来源

GetApplicationPublishedRedirects 仅向授权 Auth 服务返回单个应用当前批准且已发布回调的快照并集，具体字段与快照比较见共享契约。App 不生成 sector、不保存用户 sub；同一应用所有渠道/type 可归入一个 sector，但查询成功不授予任何用户运行资格。清单不含草稿或未发布历史版本，故障不得用空清单伪装成功。

## 验收场景

- 服务凭据逐方法授权；错误 audience、USER token 和公网访问拒绝。
- 同一渠道 clientId 可解析不同 exact-major Publication；跨渠道解析拒绝，major 不存在不回退。
- sector 回调查询跨已启用渠道/major 取得同一应用的批准并集，忽略 draft；App 输出无 sector/sub。
- 登录前可取得当前受审核回调并精确校验，不需要伪造 authId；非法回调不发生重定向。
- 当前 Tester 正常解析；移除后重加返回新 membershipId，旧资格不能恢复。
- TEST 槽切换、major 不同、跨应用 Version、批准 snapshot 不一致或对应 redirect 数组为空失败。
- 没有当前公开资料时运行解析失败；损坏的公开资料指针返回 INTERNAL，不回退 Application 技术名称。
- 登录前后 ProfileRevision 切换时 expected runtime tuple 不匹配，Auth 必须重新开始或重新展示。
- secret 轮换与 Verify 交错由 credentialRevision 拒绝混合，但不改变 RuntimeConfiguration tuple。
- 开发版客户端直开任意 URL 不产生可授权上下文，也不能替代已审核 TEST Publication。

## 依赖与实现边界

依赖 UC-APP-018、版本依附的 OAuth redirect 配置、版本审核/TEST 发布/Tester 与公开资料读取。STABLE/灰度公开运行资格尚无 UC，不阻碍本 TEST 纵切片设计。Auth Scope Catalog 的生产来源仍需实现。

## 变更记录

- 2026-09-27：建立 OAuth 授权上下文提供方设计。
- 2026-09-27：增加用户无关的运行配置解析与登录前后 runtime tuple 检查。
- 2026-09-27：运行选择改为稳定 clientId 加显式 channel/rpcApiMajor；credential revision 与运行资格分离。

- 2026-09-27：client/registration 按渠道隔离，同渠道各 major 共享；sector/sub 由 Auth 按 Application 唯一管理。
- 2026-09-30：明确 Version 审核与三个发布槽位解耦；TEST 仍要求已审核 Version、当前已批准公开资料和 Tester 资格，运行 tuple 纳入 profileRevisionId 并删除技术名 fallback。
- 2026-10-03：接受 UC019；确认 Auth→App 使用 App Center 本地 caller registry、固定 audience、短时 service JWS 与五个方法级权限，并开始 provider 实现。
- 2026-10-03：完成 App Center TEST 范围 provider 实现与完整 cross-service 验收；实现状态和提交证据见 `implements/README.md`。
