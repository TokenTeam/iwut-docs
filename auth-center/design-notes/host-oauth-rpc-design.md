# 宿主 OAuth RPC 设计说明

状态：`DRAFT / GUIDANCE`。这是 [UC035](../use-cases/UC-AUTH-035-authorize-application-in-host.md) 的设计推导与外部参考记录，不是另一份业务规则或已接受的 wire 契约。

## 已确认方向与参考基线

2026-10-22 用户确认由官方宿主显示可信授权确认界面，并要求参考 `TokenTeam/native-rpc-h5`，允许该 RPC 后续增加能力。此确认不等于接受整个 UC035，也没有决定通用账号管理 UI 的归属。

随后明确职责：应用调用 RPC，宿主用平台 Session 请求 Auth；RPC 传输及 Native 内部过程不属于 Auth 后端工作包，也不作为其开工依赖。下述 SDK 能力差距、页面隔离和生命周期建议供宿主集成使用，不要求先改库再设计 Auth。Auth 仍须冻结有效用户/交互/client/scopes 的最终校验和 code 交付语义。

只读参考：

- [GitHub 仓库](https://github.com/TokenTeam/native-rpc-h5)，检查 HEAD `87ce6d89ff99ad6fd6dc57fd1ae4390840857f14`。
- [README](https://github.com/TokenTeam/native-rpc-h5/blob/87ce6d89ff99ad6fd6dc57fd1ae4390840857f14/README.md)、[调用实现](https://github.com/TokenTeam/native-rpc-h5/blob/87ce6d89ff99ad6fd6dc57fd1ae4390840857f14/src/native-rpc.ts)和[消息类型](https://github.com/TokenTeam/native-rpc-h5/blob/87ce6d89ff99ad6fd6dc57fd1ae4390840857f14/src/definitions.ts)。
- [npm 包](https://www.npmjs.com/package/@token-team/native-rpc-h5)：检查时 latest 为 `0.0.1`，元数据 gitHead 为 `d03aec21ff0328e18723c8d163fa24d686e1eda1`；不能把 GitHub HEAD 与 npm 发布包当成同一份源码。

没有安装或修改该库，也没有把它的发布版本固定为平台协议。README 指向的 NativeRPCServiceKit 在本次公开读取中不可访问；以下对能力的判断仅来自 H5 源码，不推断实际 Native 端已实现或缺少何种安全校验。

## 当前 SDK 可参考的机制与边界

| 已观察机制 | OAuth 设计中的用途与限制 |
| --- | --- |
| `NativeRPC.call<T>(signature, params)` 返回 Promise，signature 拆为 service/method | 可承载一次发起授权的异步调用；泛型不提供运行时输入校验 |
| `_meta.callbackId` 为页面内递增计数，回包关联后删除 callback | 仅定位当前页面内的响应，不能作为不可猜事务 ID、应用证明、幂等键或授权交互 ID；重载后可能复用 |
| Android/iOS bridge 发送路径 | 适配传输，不由 H5 上报值证明可信 origin、frame 或 launch context |
| `on` 订阅及服务事件 | 可承载非敏感进度；不向广播事件发送 code、token、Session 或资料 |
| `code=1000` resolve，其他响应转为普通 Error | OAuth 需可区分拒绝、交互失效、能力不支持和结果不确定；错误表示需适配，不能依赖 message 文本判断 |

检查的 H5 调用路径未提供授权级 capability 协商、调用上下文证明、导航代际、超时取消和恢复协议。它们是宿主集成的待交付要求，不意味着这些职责必须全部塞进通用 SDK。当前 SDK 没有公开的调用超时/取消选项，不能据 Promise 尚未完成就认定服务端尚未提交。

## 建议的职责分层

1. **Bridge 传输层**：保留命名服务、异步请求/响应和可扩展适配方式；不定义账号身份、OAuth consent 或 scope 含义。
2. **官方宿主 OAuth 适配层**：从真实 WebView/launch 对象获得应用/channel/major、当前顶层页面、frame、origin、页面代际与当前账号上下文；先限制调用，再使用第一方 Session 调用 Auth。授权确认 UI 由宿主控制，第三方不能提供确认结果或调用确认内部 handler。
3. **Auth 授权层**：按 UC014–019 复用 App 在线权威配置、Catalog、grant、code 与最终事务检查。宿主上下文只约束交付对象，不替代 Auth 的用户认证、App 资格或 scope 校验，也不因一个自报“官方客户端”字段而获得特权。

SDK 参数中的 appId/origin/frame/account 等值都不是上述宿主上下文的来源。若原生平台不能可靠区分调用 frame，首版应禁止该容器提供 OAuth RPC，不能信任 H5 的顶层页面声明。平台 Session 与服务端确认材料只存在第一方路径，不随 H5 参数转发至任意后端。

## H5 调用形态与能力演进

候选业务入口为一次 `oauth.authorize` 式异步调用；名称仅示意，**不是已经存在或冻结的 SDK API**。H5 可提交 client、请求 scopes、state/nonce、PKCE challenge 和登记 redirect URI 等待校验输入。宿主内部再组合创建交互、读取权威展示、收集决定及提交；H5 不获得独立的 `confirm(approved=true)` 能力。

协议接受前应冻结版本化输入/输出 schema、有界字段/并发/等待时间和结构化错误；H5 和 Native 两侧都做运行时校验。业务 transactionId 与 SDK callbackId 分离，并绑定宿主当前实例与代际。Auth 仍使用自己的 interaction 标识，不能由 H5 选定或跨调用替换。

建议提供显式的授权能力发现：精确的 OAuth 业务协议版本和已支持功能，区分普通 bridge 版本与 App 的 `rpcApiMajor`。没有相应能力则返回不支持，不回退到旧 getToken、平台凭据注入或偷偷打开网页。能力发现仅用于兼容性选择，不是安全证明；具体方法名/字段由后续共享契约冻结。

新 bridge 能力通过适配层接入，不改变已接受的 consent、client/channel 绑定或秘密隔离。只接受当前协商版本定义的输入，新增敏感语义必须显式协商，不能因客户端忽略未知字段而“兼容成功”。

## 授权结果交付的候选方案（仍待审核）

建议本宿主分支将 code/state/iss 定向返回原调用，浏览器分支保留既有登记 HTTPS callback。只返回授权码而非由宿主代取 token；精确 redirect URI 仍须登记、校验和绑定，直接 RPC 返回是否及如何影响授权码兑换规则，必须在共享契约中明确，不能省略现有校验。

- PUBLIC：发起 H5 保存自己的 state/nonce/verifier，向宿主提交 challenge；定向收到结果后自行校验并兑换。宿主不为别的页面代管 verifier。
- CONFIDENTIAL：第三方后端建立一次登录事务并保存 state/nonce，建议同时保存 verifier，由 H5 携带 challenge 发起宿主授权；H5 将 code 交回自己的后端，由后端用 client secret 及相应证明兑换。后端事务如何与当前 H5 登录尝试绑定、PKCE 是否扩展为此分支强制要求，仍需设计与验收；不能把来自 H5 的任意 URL 当作宿主代投地址。

这不是新 token grant，也不把 H5 桥当成标准浏览器重定向。客户端类型、回调/兑换兼容及后端事务证明冻结前不生成 Proto 或上线宿主入口。

## 生命周期与不确定结果

宿主在受理调用、显示授权、提交决定、交付结果前分别核对原调用上下文。换账号、跨页面导航、刷新/重载、销毁或离开允许 origin 后，不能把迟到结果交给新页面；首版可保守地使页面生命周期变化后的待交付调用失效，而不是依赖相同 callbackId。

授权结果只能定向给原调用；不得通过事件、URL 日志或通用缓存恢复。取消/超时不承诺事务回滚。若完成状态未知，不自动重发确认、不重放旧 code、不自动换绑接收者；按 UC014 现有未知结果规则重新发起授权，未来若要增加恢复能力须单独定义保密与幂等协议。

## Auth 接受前仍需闭合

- PUBLIC/CONFIDENTIAL 精确交付协议、redirect URI 与 PKCE/后端事务规则。
- 宿主→Auth 的第一方 Session 载体、交互读取/确认保护、幂等和不确定结果规则；有效 Session 不等于任意 client/scopes 已获授权。

实际宿主仓库、Native handler 的上下文来源及导航/账号代际由宿主工作包确认。真实宿主联合验收需覆盖伪造 client/origin/frame、导航后 callbackId 复用、换账号、重复调用、拒绝、超时/提交竞争、错误回包、版本不支持、事件泄密和两类 client 兑换；这些是宿主启用门禁，不是 Auth 后端开工前必须完成的实现。

独立站点不是前置要求；缺少 bridge 能力可另列宿主扩展工作包，不降低授权边界，也不阻塞 Auth 协议设计。Console 的账号管理归属与通用资源委托路由仍由各自工作包决定，不在本说明里默认选定。
