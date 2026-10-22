# UC-AUTH-035：在官方宿主内授权第三方应用

状态：`DRAFT`

## 目标与范围

用户从 iWUT 官方宿主打开第三方应用后，通过宿主 RPC 发起 OAuth 授权；不要求为此另建独立网页登录站点。第三方可由 PUBLIC 客户端自行兑换凭据，也可由其 CONFIDENTIAL 后端兑换凭据。平台登录与第三方应用登录保持分离。

2026-10-22 用户授权调查、建立 UC 并实施，另明确要求遇到设计问题中止。调查发现当前接受协议仅覆盖浏览器门户/HTTPS 回调，尚无宿主授权 RPC 契约，因此本 UC 仅建立草案并暂停实现，不视为已接受安全边界。

同日用户已确认由官方宿主显示可信授权确认界面；参考 RPC 修正为 `TokenTeam/native-rpc-h5`，只借鉴调用模型并允许后续扩展，不继承库实现作为安全规范。此项方向已确定，UC 整体仍待依赖闭合与审核。源码基线、分层及候选适配见[宿主 RPC 设计说明](../design-notes/host-oauth-rpc-design.md)。

后续范围澄清：第三方到宿主的 RPC 传输和 Native 内部实现由宿主负责，不作为 Auth 后端设计/开工的前置条件。Auth 只规定宿主使用平台 Session 创建、读取及确认授权交互的接口与业务语义；这里的变更是第三方 OAuth grant，不是用户的平台角色或管理权限。实际宿主交付仍需独立集成验收，不以此要求 Auth 验证 JS bridge 实现。

本 UC 拟补充授权交互的宿主入口与结果交付。grant、运行资格、权限最小化、最终事务确认、授权码与 token 的业务语义仍分别引用 UC014–019，不建立平行的第三方身份、用户密码登录或“宿主已同意”旁路。不因新增入口自动退役既有浏览器流程。

## 参与者与依赖

- 已登录的官方宿主、运行其中的第三方页面/应用、Auth、App 当前批准的运行配置，以及可选的第三方后端。
- 平台 Session 仅由第一方持有。第三方自己的后端持有自身 client secret，不持有平台 Session、设备私钥或用户平台密码。
- Auth 接口需冻结当前用户、client/channel/major、请求与选择 scopes、交互及结果的绑定。宿主负责实际调用页面和结果接收者隔离；现有 App LaunchTargetDescriptor 和 capabilities 不是用户授权证明。具体 bridge 库和 Native 生命周期实现不作为 Auth 后端前置。
- Auth 可复用 `internal/oauth/usecase/authorization.go` 的 Begin/View/Confirm 及最终重查；目前没有对应授权交互 Proto RPC，不能把内部用例视作已交付公开接口。

## 输入与输出（尚未冻结）

拟支持创建交互、读取权威展示、确认/拒绝和向原发起者交付结果。精确 RPC 归属、字段、证明、过期/容量/幂等及错误码尚未确定，不提供可执行 Proto 提案或实现 brief。

宿主须绑定真实发起实例和当前应用运行上下文。第三方提交的 clientId、scope 请求、state/nonce、PKCE challenge 或后端事务引用至多是待校验输入，不能替代宿主调用归属、App 当前批准声明和 Auth 的用户决定。

## 候选流程

1. 宿主识别当前应用及调用实例；Auth 按 UC014 解析并复核 client、channel、major、批准资料/版本和请求 scopes。
2. Auth 返回权威展示；由第三方无法覆盖的官方宿主界面显示应用与权限并收集决定。这一界面归属已获用户确认，具体宿主/服务端确认协议仍待冻结。
3. 确认时复用 UC014 的当前 Session、账号、App、Catalog、grant 和交互最终复核；不能接受第三方直接提交的“用户已同意”。
4. 推荐只向原发起事务交付一次性 code/state/iss；PUBLIC 的 PKCE verifier 与 CONFIDENTIAL 后端的 secret 留在各自应持有的一侧。具体交付路径待定。
5. 兑换继续走 UC015，资料读取走 UC017/028；需要访问独立资源时再满足 UC019/Gateway/资源服务的各自门禁。

## 业务规则（草案，未接受）

<a id="br-oau-029"></a>
### BR-OAU-029：宿主调用上下文与应用归属

宿主负责识别实际调用实例并约束页面 origin、导航/销毁代际、应用/channel/major。不得把第三方自报标识或 capability 名当作受信来源。Auth 仍按 UC014 的 App 在线权威解析 client 与运行资格；宿主的调用隔离不替代服务端授权。Native 上下文来源与序列化由宿主集成决定，不要求 Auth 对 bridge 做身份鉴定，也不阻塞 Auth 接口设计；其真实交付作为宿主启用门禁。

<a id="br-oau-030"></a>
### BR-OAU-030：官方用户决定与秘密隔离

不另建网页不等于取消用户 consent。采用用户已确认的官方宿主受信界面；应用名称、批准资料和 scopes 来自 Auth，不接受第三方自绘界面或布尔值代替用户决定。选择、已有 grant 与最终复核引用 UC014。平台 Session、设备私钥和用户密码不交给第三方及其后端；Auth 不以内部 USER/delegation JWS 代替第三方 OAuth 登录结果。参考 RPC 仅提供传输模型，后续能力扩展不改变本边界。

<a id="br-oau-031"></a>
### BR-OAU-031：发起事务与授权结果绑定

授权结果必须绑定原调用应用、原页面实例、原账号、交互和 client；不能将结果送给复用同一 WebView 的新页面或新账号。授权码消费、client 认证及 PKCE 引用 UC015。PUBLIC 和 CONFIDENTIAL 的发起者、verifier/state/nonce 保存方及 code 交付方式必须分别冻结，不能把两类 client 简化为“宿主拿 token 再分发”。直接 RPC 返回与登记 HTTPS callback 的选择仍是开放问题。

<a id="br-oau-032"></a>
### BR-OAU-032：失效、取消与结果不确定

用户拒绝、宿主退出/换账号、应用页面跳转/销毁和操作超时必须保持结果接收隔离；结果不确定不能自动重做用户同意、泄露新凭据或隐式创建账号。具体取消是否仅阻止结果交付、是否撤销尚未消费 code、以及最终提交/交付恢复规则须在协议中明确，不借“取消”撤回已合法提交的业务事实。

## 设计阻塞与审核问题

1. **已确认**：采用官方宿主受信界面完成 consent；第三方不能直接声明同意。仅交付绑定的一次性授权码仍为候选方案，具体确认保护与交付契约尚未接受。
2. PUBLIC 结果直接经 RPC 返回，还是仍走登记的 HTTPS callback？CONFIDENTIAL 后端发起事务如何与宿主调用及 code 交付绑定？须统一规定 state/nonce/PKCE 的归属，不能仅凭一个来自 H5 的“后端地址”转发结果。
3. **职责已明确，不再作为 Auth 开工阻塞**：`TokenTeam/native-rpc-h5` 仅作参考，Native handler、运行上下文和生命周期钩子由宿主负责。App UC023 不实现 bridge，也不提供 OAuth clientId 发现；这些是宿主交付事项，不要求 Auth 包办。不能用 SDK callbackId 或测试构造的上下文宣称实际宿主已完成。

现有 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md) 的门户、Cookie、系统浏览器和 303 回调规则保持有效；本草案不偷偷覆盖它们。接受前须明确新增宿主分支与既有浏览器分支的兼容边界，并同步 UC014、App/宿主共享契约及精确 API/Gateway 分派。

## 实施状态与验收门禁

`NOT_STARTED / DESIGN_BLOCKED`。剩余阻塞是宿主→Auth 的精确交互接口、确认保护及两类 client 的授权码交付/兑换语义，不是 RPC 库或 Native 实现。未标 ACCEPTED，未生成本 UC brief，未修改 API、Auth、Gateway、Console 或宿主代码。依赖检查见 [UC035 与接入续作检查](../implements/UC-AUTH-035-readiness.md)。

先冻结协议/向量并完成依赖检查，经审核接受后生成 brief，再实施。验收至少覆盖两类 client、现有 grant/新增 scopes、拒绝、换账号/跳转/销毁、伪造 caller/跨 origin/跨应用/跨渠道、取消与完成竞争、码交付丢失/重复消费、依赖失败和真实宿主→Auth→App 链路；Auth 后端验收与宿主交付分别记录，不以模拟 RPC 或普通网页登录测试宣称宿主授权完成。
