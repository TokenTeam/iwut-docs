# UC-AUTH-014：用户确认应用授权并签发授权码

状态：`ACCEPTED`

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

让当前用户了解应用及其请求的权限，通过 Auth 控制的门户作出决定，生成只供本次 client 兑换的一次性授权码。本用例拥有授权交互和用户 grant；不兑换 token、不把应用的前端“已同意”声明当作用户决定。

## 输入与输出

标准 authorize 参数、门户 Session/确认命令及 HTTP 线格式见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。服务端 interaction 记录 clientId、channel、rpcApiMajor、精确 redirectUri、state、nonce、PKCE、请求 scopes、用户绑定、包含 profileRevisionId 的 App 运行 tuple、展示时的 grant revision（不存在为 0）和到期时间。匿名创建交互时 authId 为空，门户完成有效登录后只能绑定一次；换账号必须创建新交互。

输出为官方授权页或带 code/state/iss 的回调；拒绝返回 access_denied。服务端内部生成 grantId、revision，不在回调 URL 中公开内部 authId 或 Session。

## 主流程

1. 读取稳定 client 元数据，以请求中的 channel/rpcApiMajor 调用 App 的 `ResolveClientRuntimeConfiguration`，取得当前批准 Version 的 redirect URIs、scopes 和 runtime tuple；先对 redirect_uri 做完整字符串精确匹配，再校验其余协议参数并建立限时 interaction。未知或非法回调只显示 Auth 本地错误，不得重定向。准备静态 OIDC 注册元数据时复用 UC015/BR-OAU-021 的 Auth sector 模块确认该 Application 的稳定 sector，并按共享协议验证批准回调清单；不要求 App 保存 sector。
2. 官方门户确认当前登录用户；Auth 使用预登录 runtime tuple 调用 `ResolveAuthorizationContext`，取得 Tester 资格并确认运行配置未变化，再从自己的 Catalog 取得 scope 含义和映射。
3. 使用 App 返回的当前已批准 ProfileRevision 展示应用及开发者可核实信息、必需/可选权限、已有授权与新增权限。用户可以拒绝整个申请，也可以不选 optional 项；App 没有公开资料时不展示技术名称 fallback。
4. 确认时重新检查 Session、App 授权上下文及目录，并逐字段比较 registrationRevision、authorizationEpoch、versionId、publicationRevision、profileRevisionId、testerMembershipId 和 adminAuthId；权限/资格或展示资料变化时要求重新开始或重新展示，不能静默提交旧页面。
5. 原子确认 interaction、保存 grant 及审计、创建一次性 code。仅确定提交后回调；未知提交结果不重放旧 code，重新发起授权。

## 业务规则

<a id="br-oau-001"></a>
### BR-OAU-001：授权来源与运行资格

只接受 Auth 在线确认的 ACTIVE USER，Auth 同时确认应用当前 adminAuthId 具有 APPROVED Developer 资格。App 资格通过 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md) 获取；redirect URI 与 scopes 必须来自同一个批准 Version snapshot，展示资料必须来自当前已批准 ProfileRevision，不信任应用提交的版本、URL、scope、展示值或批准状态。Scope Catalog 所有权与 enabled 单状态由 [BR-SCP-004](UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 决定；令 C 为 Auth 当前 enabled=true 且具备已交付资源访问、资料披露或协议控制处理的 scopes；offline_access 的处理由 UC016 定义，不要求为它虚构业务资源 audience。本次请求包含未知、enabled=false 或无对应处理的项时返回 invalid_scope，不展示为可授予权限，也不静默删除请求项后继续。Catalog 读取故障返回依赖不可用，不能当作停用或用户拒绝。首版技术 scopes 及装载门禁见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

渠道资格统一使用 App 的 UC-APP-019/020/021 provider：TEST 要求当前 ACTIVE Tester episode；STABLE 要求原 exact-major 的正式发布可用，不要求 Tester；GREY 要求原 exact-major 的当前 rollout 可用且可信 authId 命中当前 cohort。testerMembershipId 仅 TEST 必填，STABLE/GREY 必须为空，未知渠道或字段组合异常失败关闭。Auth 不计算 cohort、不接收客户端自报命中结果，也不使用客户端 Application Filter 作为授权边界。应用启动的 TEST > GREY > STABLE 选择属于 App/客户端；OAuth 始终验证明确的 client/channel，不自动换渠道或 major。

<a id="br-oau-002"></a>
### BR-OAU-002：显式同意与最小授权

令 D=当前批准版本 requiredScopes∪optionalScopes，R=本次请求 scopes，S=用户本次选择；必须 requiredScopes⊆R⊆D∩C，S 包含 requiredScopes 且 S⊆R。登录必需 openid；不允许用“不选 optional”偷增其他权限。无法接受必需权限时用户仍可拒绝全部。

Grant 的业务主键为 `(authId, applicationId, channel)`，Mongo 必须以这三个字段建立复合唯一约束；grantId 仅为稳定、不透明的引用 ID，供 token 和本人管理接口引用。authId 来自当前 Session，applicationId/channel 来自 App 确认的 client 归属，不接受客户端自行指定授权归属。同一 Application 同一 channel 的 PUBLIC/CONFIDENTIAL client 及各 RPC major 共享一个 grant；TEST/GREY/STABLE 分别保存，不因跨渠道 sub 相同而共享授权。clientId、major、Version 均不进入 grant 唯一键。保存历史同意集合 G=grantedScopes、revision、revocationEpoch（初始 1）和 status；发起 clientId 与运行 tuple 记录在交互及审计中。

授权页明确展示应用和渠道，并说明本次同意可由该渠道的两类 client 复用。共享的是用户同意；每个 client 仍须分别满足自己的当前批准版本、运行资格和凭据证明，code/token/family 不跨 client 使用。

首次同意保存 S；以后只展示本次尚未同意的 `S−G`，明确同意后更新为 `G∪S`。若本次 R 已包含于 G 且满足当前 D∩C，可按 prompt 规则静默取得本次需要的 S。prompt=consent 仍展示确认，offline_access 的专用规则保持有效。不能把历史 G 全部签入 token；S 必须是当前请求与当前允许集合的子集。

Version、major 或 Publication 变化不删除 G，不因当前 D 变小写回 `G∩D`，也不改变 grant 的 revision/epoch。某个 scope 未来再次由批准版本声明，只要用户未主动撤回，仍可复用原同意。Catalog enabled=false 同样不删除 G 或推进 grant revision/revocationEpoch；恢复后只可在仍有效的凭据原范围、G 与当前 D 内继续使用，不能复活已过期或被用户撤销的凭据，不能自动扩大停用期间新发 token 的范围。恢复同名含义必须保持 Catalog 的稳定语义。所有资源实际权限为 `token.scopes ∩ G ∩ D ∩ C`，不满足本次路由的权限时拒绝该操作，而非因为 token 另含一个暂不可用 scope 就拒绝全部操作。

新增同意递增 revision（OCC/审计），不递增 revocationEpoch，不使已签发凭据失效；旧 token 不会因此自动获得新 scope。用户显式撤回按 UC018 改变 G/status 并递增两者，旧 code/token/family 通过 epoch 失效。重新同意也不能复活已撤销代的凭据。交互提交仍比较展示时 revision，竞争时要求刷新页面，不能覆盖用户后来决定。

<a id="br-oau-003"></a>
### BR-OAU-003：交互和授权码原子性

确认必须绑定当前 Session 的用户、interaction、CSRF 及展示版本；同一 interaction 只能同意或拒绝一次。code 保存用户、client、channel/rpcApiMajor、grant revision（审计）、revocationEpoch、完整 App 资格 tuple、从受审核回调集合精确匹配的 redirect URI、scope、nonce、auth_time、PKCE 和到期时间，存摘要不存原值。grant 可跨兼容 Version 延续，不允许 code 脱离其精确 tuple 使用。

同意时 grant、code、interaction 状态和不可变审计同一 Mongo 事务提交；同一业务主键下所有 client 的确认、签发与本人撤销共用 grant 写入栅栏。首次并发创建由复合唯一约束保证仅一条 grant；竞争失败后重新读取既有记录并执行 revision 校验，不能另建按 client 隔离的记录或覆盖已保存的同意集合。撤销后旧页面不得悄悄重授，必须刷新交互并显式确认。无效请求不改变既有 grant。

<a id="br-oau-004"></a>
### BR-OAU-004：门户与撤销语义隔离

登录入口、prompt/max_age、cookie/CSRF 和回调规则见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。门户只复用或重新完成已有注册/登录，不因 OAuth 请求静默创建平台账号。用户取消本次交互不撤回历史授权；退出平台 Session 不注销第三方应用。交互日志只含内部 ID、scope 名称与决定，不含凭据、资料值。

## 验收场景

- 同渠道 major 1 只需 openid、major 2 需 openid/email：运行 major 1 不删除已同意 email，major 2 不重复要求同意。
- 同应用同渠道 PUBLIC 已同意 openid/email 后，CONFIDENTIAL 请求相同范围可按 prompt 规则复用；新增权限只确认差集，offline_access 仍须满足专用确认规则。
- TEST/STABLE/GREY 均可完成授权；STABLE 非 Tester 可用，GREY 仅当前命中用户可用。未知渠道、client/channel 不一致和错误 Tester 字段组合拒绝。
- TEST grant 不用于 GREY/STABLE；同一应用跨渠道 sub 相同也不绕过 consent。
- 两类 client 并发首次同意只产生一条 grant；冲突交互重新展示后合并新增同意，不丢失已有范围；撤销前的旧页面不能重新授予权限。
- email 停用时，请求 email 返回 invalid_scope，已有同意不能绕过；若 email 仅是版本 optional 项，客户端改为只请求 openid 可继续。必需项停用时无法满足 requiredScopes，不静默降级。
- 授权页展示后 scope 停用，确认时不能沿用旧页面授予或签发；目录故障按依赖失败处理。
- 授权页展示后当前 ProfileRevision 改变时必须重新展示；没有公开资料不能建立交互，不能展示 Application 技术名称兜底。
- 增加 scope 仅更新 G/revision；旧 token 继续使用原权限，撤回则通过 revocationEpoch 使旧代失效。

- public 缺 challenge、错误回调、伪造 App 版本或未批准 scope 拒绝，且不会回跳恶意 URL。
- 匿名用户可登录后继续；换账号、跨 Session 确认、CSRF、过期交互拒绝。
- 必需权限不能静默省略，可选权限未勾选不签入 code；openid 不自动附带 email。
- prompt=none 无登录/新权限按协议报错；已有同范围 grant 可复用。
- 两次确认、确认与撤销并发、App 发布变化、事务失败均不多发码或复活已撤回授权。
- 同一 clientId 升级到新 Version 时既有同范围 grant 可延续；新增 scope 必须重新 consent，旧 interaction/code 不能改绑新 redirect。

## 依赖与实现边界

依赖 UC007/012 Session、UC001 权威目录、UC-APP-018/019 及已交付的 UC-APP-020/021 渠道扩展；UC015 消费授权码。官方门户是独立交付项但属于上线验收，不能仅实现后端就启用授权入口。参数/时限/密钥格式引用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)，不在本 UC 重定义。

## 变更记录

- 2026-09-27：授权入口改为先解析用户无关的 Version 运行配置并校验回调，登录后以同一 runtime tuple 解析用户资格。
- 2026-09-30：runtime tuple 纳入 profileRevisionId，授权页只展示 App 当前已批准公开资料，资料变化后重新展示。
