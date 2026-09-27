# UC-AUTH-014：用户确认应用授权并签发授权码

状态：`PROPOSED`

## 目标与范围

让当前用户了解应用及其请求的权限，通过 Auth 控制的门户作出决定，生成只供本次 client 兑换的一次性授权码。本用例拥有授权交互和用户 grant；不兑换 token、不把应用的前端“已同意”声明当作用户决定。

## 输入与输出

标准 authorize 参数、门户 Session/确认命令及 HTTP 线格式见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。服务端 interaction 记录 clientId、精确 redirectUri、state、nonce、PKCE、请求 scopes、用户绑定、App 资格版本、展示时的 grant revision（不存在为 0）和到期时间。匿名创建交互时 authId 为空，门户完成有效登录后只能绑定一次；换账号必须创建新交互。

输出为官方授权页或带 code/state/iss 的回调；拒绝返回 access_denied。服务端内部生成 grantId、revision，不在回调 URL 中公开内部 authId 或 Session。

## 主流程

1. 校验登记的 client、回调及协议参数，建立限时 interaction；未知回调不得重定向。
2. 官方门户确认当前登录用户；Auth 从 App 取得当前运行资格与批准 scope，从自己的 Catalog 取得 scope 含义和映射。
3. 展示应用及开发者可核实信息、必需/可选权限、已有授权与新增权限。用户可以拒绝整个申请，也可以不选 optional 项。
4. 确认时重新检查 Session、App 资格及目录，与展示版本比较；权限/资格变化时要求重新展示确认，不能静默提交旧页面。
5. 原子确认 interaction、保存 grant 及审计、创建一次性 code。仅确定提交后回调；未知提交结果不重放旧 code，重新发起授权。

## 业务规则

<a id="br-oau-001"></a>
### BR-OAU-001：授权来源与运行资格

只接受 Auth 在线确认的 ACTIVE USER，Auth 同时确认应用当前 adminAuthId 具有 APPROVED Developer 资格。App 资格通过 [App 提供方契约](../../platform/contracts/app-oauth-client-v1.md) 获取，不信任应用提交的版本、scope 定义或批准状态。Scope Catalog 所有权继续由 UC001 决定；未知、停用或没有资源/披露映射的 scope 失败关闭。首版技术 scopes 及装载门禁见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

<a id="br-oau-002"></a>
### BR-OAU-002：显式同意与最小授权

令 D=当前批准版本 requiredScopes∪optionalScopes，R=本次请求 scopes，S=用户本次选择；必须 requiredScopes⊆R⊆D，S 包含 requiredScopes 且 S⊆R。登录必需 openid；不允许用“不选 optional”偷增其他权限。无法接受必需权限时用户仍可拒绝全部；已有授权是否撤销由 UC018 决定。

Grant 按 (authId,clientId) 唯一，保存 grantedScopes、revision、status、consentContext（本次确认的 App 资格版本）。已有相同或更大授权且 consentContext 仍一致时可在 prompt 允许时复用；新增权限和 offline_access 按各自规则显式同意。首次为 S，新增授权取既有集合与 S 的并集，再收缩到当前 D；实际 code 只绑定本次 S，不携带全部历史 grant。集合或 consentContext 改变递增 revision，使旧凭据重新验证失败；两者相同的重复同意不无故增版本。资格版本变化必须重新展示确认，不能只按 scope 名称相同静默复用。应用声明/升级不会自行新增 grant。

<a id="br-oau-003"></a>
### BR-OAU-003：交互和授权码原子性

确认必须绑定当前 Session 的用户、interaction、CSRF 及展示版本；同一 interaction 只能同意或拒绝一次。code 保存用户、client、grant revision、App 资格版本、redirect URI、scope、nonce、auth_time、PKCE 和到期时间，存摘要不存原值。

同意时 grant、code、interaction 状态和不可变审计同一 Mongo 事务提交；与本人撤销同一 grant 的写入栅栏串行确认。撤销后旧页面不得悄悄重授，必须刷新交互并显式确认。无效请求不改变既有 grant。

<a id="br-oau-004"></a>
### BR-OAU-004：门户与撤销语义隔离

登录入口、prompt/max_age、cookie/CSRF 和回调规则见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。门户只复用或重新完成已有注册/登录，不因 OAuth 请求静默创建平台账号。用户取消本次交互不撤回历史授权；退出平台 Session 不注销第三方应用。交互日志只含内部 ID、scope 名称与决定，不含凭据、资料值。

## 验收场景

- public 缺 challenge、错误回调、伪造 App 版本或未批准 scope 拒绝，且不会回跳恶意 URL。
- 匿名用户可登录后继续；换账号、跨 Session 确认、CSRF、过期交互拒绝。
- 必需权限不能静默省略，可选权限未勾选不签入 code；openid 不自动附带 email。
- prompt=none 无登录/新权限按协议报错；已有同范围 grant 可复用。
- 两次确认、确认与撤销并发、App 发布变化、事务失败均不多发码或复活已撤回授权。

## 依赖与实现边界

依赖 UC007/012 Session、UC001 权威目录、UC-APP-018/019；UC015 消费授权码。官方门户是独立交付项但属于上线验收，不能仅实现后端就启用授权入口。参数/时限/密钥格式引用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)，不在本 UC 重定义。
