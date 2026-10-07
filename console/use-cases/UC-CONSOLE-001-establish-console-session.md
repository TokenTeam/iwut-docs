# UC-CONSOLE-001：建立浏览器 Console Session

状态：`ACCEPTED`

## 目标与范围

> 用户使用本机已有设备凭据，或通过已激活邮箱为本机登记/复用设备凭据，进入吾理开放平台或吾理平台管理；对应 BFF 接管 Auth Session，并向浏览器建立不可由 JavaScript 读取的 Console Session。

本用例是两个 Console 的共享认证入口。它编排已有的设备登录与邮箱登录能力，不重新定义账号归属、设备证明、邮箱验证码、Session 有效性或服务端限流规则：

- 已有设备凭据登录引用 [UC-AUTH-007](../../auth-center/use-cases/UC-AUTH-007-login.md)；
- 邮箱恢复/新增设备登录引用 [UC-AUTH-012](../../auth-center/use-cases/UC-AUTH-012-login-with-email.md)；
- P-256 公钥、指纹、签名字节、严格 DER 与 Session token 编码引用 [App 设备认证与 Session v1](../../platform/contracts/auth-device-session-v1.md)；
- 邮箱登录签名上下文、消息字段、匿名载体要求与 HTTP 映射引用 [邮箱登录协议 v1](../../platform/contracts/auth-email-login-v1.md)；
- Gateway 的公共前缀、严格 ProtoJSON 与 DIRECT 转发语义引用 [Auth API 路由](../../platform/contracts/auth-center-api-routing.md)。

本用例中的“已登录”只表示目标 Console 已成功建立自己的 BFF Session。Developer 或 Admin 权限仍由后续受保护请求及对应后端规则判断；认证成功不能被界面解释为已经拥有 Developer、Reviewer 或平台管理员权限。

本用例不负责注册新账号、激活或更换邮箱、开通 Developer、显式退出、撤销其它 Session/设备、多账号切换、OAuth consent bridge 或登录后的落地页业务查询。未知邮箱不能自动转入注册。显式退出应另立用例并引用 [UC-AUTH-008](../../auth-center/use-cases/UC-AUTH-008-revoke-own-session.md)。

## 参与者与前置条件

- 主参与者是访问吾理开放平台或吾理平台管理的 USER。
- 浏览器支持 Web Crypto、IndexedDB 和安全 Cookie；不满足时停止登录并说明此浏览器不能安全完成该流程，不降级到明文私钥、`localStorage` 或 `sessionStorage`。
- 使用设备登录时，本机已有可用的 P-256 私钥，以及 credentialId 或可由公钥计算的 fingerprint。
- 使用邮箱登录时，用户已经在目标账号激活邮箱；这是服务端事实，Console 不预先判断。浏览器在 Begin 前生成并持久化本机设备密钥，且在结果确定前始终复用同一密钥。
- 两个 Console 只调用本 surface 的同源入口。登录、恢复和 Session 管理由 BFF 处理；普通 API 按 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 先由本 BFF 的 Session ForwardAuth 把 HttpOnly Cookie 交换为内部 `x-iwut-session`，再进入现有 Gateway 认证链。浏览器始终不能读取 Auth Session token。
- Gateway 已在统一 API 基线中登记设备登录与邮箱登录的精确匿名路由。目标部署仍只开放真实可用的登录方式；Auth 邮箱登录、邮件配置或其它运行依赖未启用时，BFF 必须将邮箱方式标记为不可用，不能由浏览器参数或 mock 覆盖。

## 功能性界面

### 浏览器本地凭据记录

```text
LocalDeviceCredential {
  localId: string
  privateKey: non-extractable CryptoKey
  publicKey: CryptoKey | publicKey65
  credentialId?: UUID
  publicKeyFingerprint: Bytes32
  protocolVersion: "iwut-device-v1"
}
```

`localId` 只用于本机选择记录，不是账号身份。`credentialId`、公钥和 fingerprint 不是私钥替代品；没有对应私钥时不能发起设备证明。私钥生成后必须为 non-extractable，并通过结构化克隆保存在 IndexedDB；不得导出成 JWK/PKCS8、复制到日志、错误、遥测、表单状态、URL 或普通字符串存储。

用户清除浏览器站点数据后，本地凭据可以消失；Console 不宣称能够恢复该私钥。若用户仍能使用已激活邮箱，可明确选择邮箱登录并生成一把新设备密钥。

### BFF 逻辑命令

路径和传输 DTO 由实现契约固定；本 UC 固定以下语义，BFF 不得接受浏览器提交 `sessionToken` 或任意 `authId`：

```text
BeginDeviceConsoleSession {
  credentialId?: UUID
  publicKeyFingerprint?: Bytes32
}

DeviceConsoleChallenge {
  operationId: UUID
  challenge: Bytes
  signingPayload: Bytes
  protocolVersion: string
  expiresAt: Instant
}

CompleteDeviceConsoleSession {
  operationId: UUID
  proof: CredentialAuthenticationProof
}

BeginEmailConsoleSession {
  requestId: UUID
  email: string
  credentialProposal: CredentialRegistrationProposal
}

EmailConsoleChallenge {
  operationId: UUID
  challenge: Bytes
  signingPayload: Bytes
  protocolVersion: string
  expiresAt: Instant
  resendAfter: Instant
}

CompleteEmailConsoleSession {
  operationId: UUID
  code: string
  proof: CredentialAuthenticationProof
}

ConsoleSessionSummary {
  authId: string
  credentialId: UUID
  expiresAt: Instant
}
```

Challenge 字节按生成 API 的 ProtoJSON 规则使用 Base64，int64 时间由生成客户端按字符串接收后做有界解析；页面组件不得自行猜测编码。`ConsoleSessionSummary` 不含上游 token、Session ID、邮箱、角色或权限。它只说明 BFF 已保存会话及其声明到期时间，不代替 Auth 对下一次受保护请求的在线检查。

## 主流程 A：已有设备凭据登录

1. 用户进入未登录的 Console，选择本机已有设备记录；若只有一条记录，界面可以默认选中，但不得在已有可用 Console Session 时后台持续创建新 Auth Session。
2. 浏览器向同源 BFF 提交 credentialId；credentialId 缺失而公钥仍可用时，可提交按平台契约计算的 fingerprint。两者都缺失则该记录不可用于设备登录。
3. BFF 不附加现有 Console Cookie 对应的 `x-iwut-session`，经 Gateway 调用 `POST /auth-center/v1/device-logins`，返回 challenge。
4. 浏览器严格解析 `signingPayload`，核对协议、`LOGIN` purpose、operationId、challenge、expiresAt、预配置 serviceId、固定 applicationId `iwut-client` 以及本机 locator。任何不一致都在签名前失败关闭。
5. 浏览器用该记录的 non-extractable P-256 私钥签署完整 payload 一次，将浏览器签名输出转换成平台要求的严格 DER 后提交 Complete。
6. BFF 调用 `POST /auth-center/v1/device-logins/{operation_id}/completion`。Auth 确定成功后，BFF 接管返回的 Session secret，建立目标 Console 自己的 Cookie，并只向浏览器返回 `ConsoleSessionSummary`。
7. 浏览器更新该本地记录的 credentialId，丢弃 operation、challenge、proof 和表单敏感状态，然后进入登录后的功能路由。后续权限不足由相应页面处理，不回退成“登录失败”。

## 主流程 B：邮箱恢复或新增设备登录

1. 用户明确选择“使用邮箱登录”。浏览器创建 P-256 密钥对，先把 non-extractable 私钥及公钥记录持久化，再生成本次 requestId；不得先发送 Begin 再保存私钥。
2. 浏览器向同源 BFF 提交邮箱、requestId 与公钥提案。BFF 必须以完全不带 `x-iwut-session` 的匿名请求调用 `POST /auth-center/v1/email-logins`。
3. 对格式有效的请求，页面进入统一的验证码等待状态，不根据响应、用时或提示声称账号存在。页面保留原邮箱、本机公钥、operationId、challenge、expiresAt 和 resendAfter 作为本次操作上下文。
4. 用户输入恰好 8 位 ASCII 数字验证码，保留前导零。浏览器核对 `iwut-email-login-v1` 的十字段签名上下文与本次邮箱、公钥、操作、服务、应用、challenge 和期限一致后签名。
5. BFF 以不带 Session 载体的匿名请求调用 `POST /auth-center/v1/email-logins/{operation_id}/completion`。Auth 成功后，BFF 按主流程 A 的相同边界建立 Console Session；浏览器把返回的 credentialId 写入原本地设备记录。
6. 成功后清除验证码、challenge、proof 和操作上下文。邮箱地址是否继续作为本机账号标签属于后续多账号设计，不得把它当作服务端身份或权限事实。

重发必须等待服务端 `resendAfter`，生成新的 requestId，并复用同一设备密钥。新操作替换旧操作后，迟到的旧响应不能改变当前流程。用户取消后若重新开始，可以显式决定复用尚未归属且仍可安全使用的本机密钥；Console 不得因网络失败自动批量生成密钥。

## 业务规则

<a id="br-cse-001"></a>
### BR-CSE-001：认证路径与账号边界

Console 只通过 UC-AUTH-007 和 UC-AUTH-012 建立 Auth Session。设备登录的账号归属来自设备凭据，邮箱登录的账号归属来自 Auth 的当前激活邮箱记录；请求、URL、本地标签和页面状态均不能指定或覆盖 authId。

认证成功不创建新账号、不绑定邮箱、不授予 Developer/Admin/Reviewer 权限。未知、未激活或不可登录邮箱使用后端统一失败语义，页面不得建议“已经为你创建账号”或根据失败原因确认账号是否存在。

<a id="br-cse-002"></a>
### BR-CSE-002：浏览器设备密钥保管

设备私钥必须由浏览器 Web Crypto 生成、保持 non-extractable 并保存在 IndexedDB。所有签名都在持有 CryptoKey 的适配器内部完成；React 状态、表单对象、TanStack Query cache、MSW handler 和序列化调试信息均不得接触私钥字节。

浏览器站点隔离只是保管边界，不等于抵抗同源 XSS：恶意同源脚本仍可能请求使用不可导出的密钥。因此 Console 仍需严格 CSP、依赖治理和输出编码；文案不得把 non-extractable 宣称为“脚本无法使用”。

本地记录损坏、密钥不可用或协议版本未知时失败关闭。不得尝试导出、修复或猜测私钥，也不得把无私钥的 credentialId 当作可登录凭据。

<a id="br-cse-003"></a>
### BR-CSE-003：签名前验证与规范编码

浏览器必须将后端返回的 `signingPayload` 当作需要严格验证的协议消息，而不是任意待签字节。核对项、Frame、UTF8、U64BE、公钥、fingerprint 和 ECDSA 规则以两个平台协议及公开测试向量为唯一权威。

设备适配器对完整 payload 恰好执行一次 SHA-256/ECDSA。它必须把实际 Web Crypto 签名结果规范化成后端接受的严格 DER，并拒绝非法长度、整数、曲线点、尾随数据、上下文不匹配和已过期挑战；不能靠后端拒绝代替客户端核对，也不能二次哈希。

<a id="br-cse-004"></a>
### BR-CSE-004：BFF Session 与 Cookie 隔离

Auth 返回的 Session token 只允许进入对应 BFF 的受保护会话设施，不得出现在浏览器 JSON、HTML、URL、可读 Cookie、Web Storage、IndexedDB、日志、遥测或错误对象。BFF 直接调用 Gateway，或共享 Traefik 调用该 BFF 的 Session ForwardAuth 时，才从自身会话恢复上游 token；普通 Browser API 必须在删除 Cookie 后把唯一的内部 `x-iwut-session` 交给现有 Gateway 认证链。

浏览器 Cookie 必须使用 `Secure`、`HttpOnly`、`Path=/`、无 `Domain` 的 `__Host-` Cookie，并采用不宽于实际导航需求的 SameSite 策略；其到期时间不得晚于 Auth Session 的 `expiresAt`。Cookie 值是 Console BFF 自己的不可伪造会话载体，不能直接等同于 Auth token。使用服务端存储还是认证加密封装由后续实现 ADR 决定，但都必须支持主动清除且不能向浏览器解密上游 secret。

Developer BFF 与 Admin BFF 使用不同 origin、密钥、Cookie 名和会话命名空间。登录其中一个 Console 不得让另一个 Console 自动获得登录态，也不得相互接受 Cookie。

普通 API 使用 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 的混合链路不改变 Cookie 所有权。Gateway 核心不得开始解析 Console Cookie，BFF 与 Gateway 不得复制或共享两套 Cookie 加解密实现；未显式登记 surface 的 Gateway route 默认不能从 Console Host 到达。

<a id="br-cse-005"></a>
### BR-CSE-005：同源建立、并发与迟到响应

所有建立 Session 的 BFF 命令只接受本 Console 精确 Origin 的同源请求，不开放凭据式跨域 CORS；对缺失或不匹配的 Origin/Fetch Metadata 失败关闭。页面跳转目标只能是当前 Console 内经校验的相对路径，不能由任意外部 URL 控制。

每个 Console、每条本地凭据同一时刻最多有一个有效的设备登录流程；每个邮箱表单同一时刻最多有一个当前邮箱登录操作。开始新操作、切换方式、取消流程或离开登录上下文时，旧响应即使稍后成功返回也不能覆盖新状态或设置 Cookie。BFF 也必须把一次 Complete 绑定到自身签发/记录的登录事务上下文，不能仅凭浏览器给出的 operationId 设置会话。

DIRECT 登录请求不得因浏览器已有无效 Cookie 而自动携带上游 Session。邮箱登录要求 `x-iwut-session` 键完全缺失，不能发送空值后再依赖 Gateway 清理。

<a id="br-cse-006"></a>
### BR-CSE-006：结果不确定与幂等恢复

Begin 超时可使用原请求的幂等规则恢复；邮箱 Begin 使用相同 `(public key fingerprint, requestId)` 时参数必须完全相同，且不能被页面当作“重发验证码”。真正重发在 `resendAfter` 后使用新 requestId 和原密钥。

邮箱投递可能占用完整的服务端 SMTP 超时。Gateway/Traefik、BFF 和浏览器的外层超时必须逐层留出转发余量；任一外层不能在正常内层仍可能提交时先把请求解释为确定失败。当前联调基线为 Auth SMTP 30 秒、Gateway/Traefik 上游响应至少 35 秒、BFF 至少 40 秒、浏览器至少 45 秒；这些数值是部署起点，不是协议常量，调整时仍保持“浏览器 > BFF > Gateway/Traefik > Auth/SMTP”的顺序。

邮箱 Begin 在浏览器或 BFF 超时后进入结果待确认。首次恢复必须使用原 requestId、邮箱、公钥与设备密钥重试同一 Begin，以命中 Auth 幂等记录；不得因为超时直接生成新 requestId。只有收到原操作结果，或到达 `resendAfter` 后由用户明确选择重发，才使用新 requestId。界面可以在等待期间持续表达正在发送，但不能以较短的视觉计时器宣称邮件失败。

Complete 超时、连接中断或 BFF 写 Cookie 失败时，页面必须进入“结果待确认”，不能声称成功、失败或创建新账号。它保留原私钥：

1. 先用该公钥 fingerprint 发起新的 UC-AUTH-007 设备登录；
2. 若凭据尚未登记且原邮箱操作仍有效，可用原操作重试 Complete；
3. 否则使用原密钥重新开始邮箱登录。

`LOGIN_ALREADY_COMPLETED` 不返回旧 token，也不能让 BFF 伪造成功。不得通过自动生成新密钥规避恢复流程。认证恢复只重建 Session，不自动重放任何结果未知的业务写操作。

<a id="br-cse-007"></a>
### BR-CSE-007：错误、失效与隐私表达

前端按稳定 reason 和 HTTP 状态映射交互，不解析后端 message：

| 类别 | 后端语义 | Console 行为 |
| --- | --- | --- |
| 输入或本地协议非法 | `INVALID_LOGIN_INPUT`、`INVALID_EMAIL_LOGIN_REQUEST` | 停止当前操作；字段错误可定位到字段，协议/本地记录错误不可盲目重试。 |
| 认证失败 | `AUTHENTICATION_FAILED`、`EMAIL_LOGIN_FAILED` | 使用统一失败提示，不披露账号、凭据或邮箱存在性；允许用户明确重新开始。 |
| 已完成 | `LOGIN_ALREADY_COMPLETED` | 进入结果待确认恢复，不视为成功，不索取或复原旧 token。 |
| 凭据冲突 | `EMAIL_LOGIN_CREDENTIAL_UNAVAILABLE` | 不披露原归属；保留现有本地材料并引导选择另一安全恢复路径。 |
| requestId 冲突 | `EMAIL_LOGIN_REQUEST_CONFLICT` | 停止该请求，生成新 requestId 前先确认仍使用原密钥与表单意图。 |
| 限流或容量 | `AUTHENTICATION_LIMIT_EXCEEDED`、`EMAIL_LOGIN_RATE_LIMITED` | 尊重有效 `Retry-After`，倒计时期间禁止自动轮询/重试。 |
| 邮件或认证依赖不可用 | `EMAIL_DELIVERY_UNAVAILABLE`、`AUTHENTICATION_UNAVAILABLE`、`EMAIL_LOGIN_UNAVAILABLE` | 显示暂时不可用；使用有界退避，保留可恢复上下文，不改成“凭据错误”。 |
| Session 无效 | `SESSION_INVALID` | BFF 清除本 Console Cookie，浏览器回到未登录状态；不删除设备私钥。 |

受保护请求遇到基础设施 5xx 或网络错误时不得清除 Cookie 或本地设备凭据，因为依赖故障不证明 Session 无效。BFF 会话摘要到期或 Auth 明确返回 `SESSION_INVALID` 时才转为未登录。所有错误和遥测都不得包含 token、验证码、proof、完整 challenge/signingPayload、邮箱或私钥；必要的 operationId 仅按既定日志规则处理。

<a id="br-cse-008"></a>
### BR-CSE-008：功能可访问性与秘密生命周期

登录方式、字段、提交、重发、取消、错误与结果待确认状态必须可由键盘操作，并通过语义、焦点和可读文本表达；不能只依赖颜色、位置、倒计时动画或 toast。提交失败后焦点移到错误摘要或首个无效字段；异步状态变化通过合适的 live region 宣告，但验证码、邮箱和协议字节不被朗读到无关区域。

验证码使用字符串字段以保留前导零，并允许密码管理器/邮件客户端完成用户主动粘贴；不得把验证码放进 URL。验证码、proof、challenge 与 signingPayload 在成功、取消、过期或被新操作替代后立即从表单和查询 cache 移除。设备私钥及长期本地凭据不因清理一次性状态而删除。

## 页面状态模型

```text
SIGNED_OUT
  -> DEVICE_CHALLENGE -> SIGNING -> COMPLETING
  -> EMAIL_BEGIN -> EMAIL_CODE_PENDING -> SIGNING -> COMPLETING

COMPLETING -> ESTABLISHED
COMPLETING -> RESULT_UNCERTAIN -> DEVICE_RECOVERY | EMAIL_RECOVERY
any transient state -> SIGNED_OUT | TEMPORARILY_UNAVAILABLE
ESTABLISHED -> SIGNED_OUT       (local expiry or confirmed SESSION_INVALID)
```

状态转换由当前 flowId 与 operationId 共同约束。组件卸载、用户取消或新 flowId 产生后，旧异步结果只能被丢弃。`TEMPORARILY_UNAVAILABLE` 可以返回原可恢复状态，但不得私自延长后端 challenge、验证码或 Session 的 expiresAt。

## API 与实现依赖

| 依赖 | 当前事实 | 对 UC001 的影响 |
| --- | --- | --- |
| Auth 设备登录 API | UC-AUTH-007、Proto 与实现已存在 | 可以开始生成客户端和 BFF 接入；仍需真实环境验收。 |
| Gateway 设备登录路由 | `routes.v3.yaml` 保留 Begin/Complete 匿名路由 | 设备主流程具备接入路径。 |
| Auth 邮箱登录 API | UC-AUTH-012、Proto、实现与公开向量已存在 | 可以实现协议适配器和 BFF 客户端。 |
| Gateway 邮箱登录路由 | Gateway `7a3eb7c` 已在统一 API `9f914c5` 上登记 Begin/Complete；87 条外部 Proto 路由及 typed adapter 闭合检查通过 | Gateway 不再阻塞邮箱主流程；仍需 Console 真实 E2E。 |
| Auth 邮件投递 | 本地联调已通过启动时配置注入验证，当前 SMTP timeout 为 30 秒 | 可开展邮箱流程联调；生产配置与可用性仍需独立验收，Console 按 BR-CSE-006 分层超时。 |
| TypeScript 生成客户端 | 已固定统一 API `9f914c5`，生成认证/邮箱登录消息与 `google.api` 依赖，并提供漂移检查和原生 fetch runtime | 登录端点的 BFF 编排仍待接入；不得绕过生成类型手写权威 DTO。 |
| Console BFF 会话设施 | AES-256-GCM 封装、独立 `__Host-` Cookie、精确来源校验、Session 安全投影/清理与两个私有 ForwardAuth 已实现；Gateway `routes.v3.yaml` 的双 surface chain 已通过真实本地联合 E2E；Console deployment composition 已生成并合并验证 Session `40000` Router、SPA/static `1000` Router 与私有路径隔离 | BFF-owned 登录/恢复 exact Router、BFF→Gateway 非 Console 内部入口、Begin/Complete 事务绑定、恢复和完整登录 E2E 仍待完成。 |

部署能力必须来自 BFF 的只读服务端配置，不能由 query、`localStorage` 或页面调试开关启用。Gateway 路由存在不等于目标环境已启用 Auth 邮箱登录或邮件投递；未就绪时可以不展示入口或明确显示暂不可用。

## 测试与验收

1. 已有有效本机凭据通过真实浏览器 Web Crypto、BFF、Gateway 与 Auth 建立 Session；浏览器响应与可读存储中没有 Auth token。
2. credentialId 缺失但同一私钥、公钥和 fingerprint 完整时可以登录；缺少私钥、记录损坏或协议未知时在签名前失败关闭。
3. 使用公开设备协议向量验证精确 payload、fingerprint、Base64 和 DER；覆盖双重哈希、跨 purpose/service/application/operation/locator 重放及 now == expiresAt 拒绝。
4. 已激活邮箱在无旧设备、无旧 Session 时，用新 non-extractable 密钥、8 位验证码和严格邮箱协议向量进入原账号并保存返回 credentialId；未知与不可登录邮箱不泄露账号存在性。
5. 邮箱 Begin、Complete 的上游请求完全不含 `x-iwut-session`；即使浏览器残留 Console Cookie 也不能污染匿名 Auth 请求。
6. 同 requestId 重试不重复发送，参数变化冲突；30 秒 SMTP 联调配置下，Gateway/Traefik、BFF 和浏览器使用逐层更长的超时。任一外层超时先以原 requestId 恢复；真正重发等待 `resendAfter`、使用新 requestId 和原密钥，并使迟到旧响应无法设置当前 Cookie。
7. Complete 响应丢失、BFF 提交结果未知及 `LOGIN_ALREADY_COMPLETED` 按 BR-CSE-006 恢复；不返回旧 token、不重复登记凭据、不创建账号、不自动重放业务写命令。
8. `SESSION_INVALID` 清除且只清除当前 Console Cookie，不删除设备私钥；基础设施 5xx、网络中断和邮件投递故障不清除仍可能有效的会话或恢复材料。
9. Developer 与 Admin 在不同 origin 登录后只能使用各自 Cookie；交换 Cookie、跨 Origin 建立会话、外部 return target 和凭据式 CORS 请求均失败。
10. `document.cookie`、页面 HTML、Query cache、IndexedDB 普通记录、Web Storage、日志、遥测和错误快照中没有 Auth token、验证码、proof 或私钥材料；测试不把“私钥不可导出”误断言为“同源脚本不可调用”。
11. 键盘、焦点、错误摘要、异步宣告、重发倒计时和结果待确认恢复通过 Testing Library 与 Playwright 验收，不依赖特定颜色或像素布局。
12. MSW 仅验证前端分支与错误映射；至少一组设备登录和一组邮箱登录使用真实 Auth/Gateway，邮箱用例还必须经过真实测试邮件投递。不能用 mock 宣称 UC 完成。

## 完成标准

本设计已经接受并作为实现基线。实现只有同时满足以下条件才能标记完成：

- 两个 Console 的 BFF Session 边界、浏览器设备适配器和共享错误映射已实现；
- 设备登录真实 E2E 通过；
- 邮箱登录通过真实 BFF、Gateway、Auth 和测试邮件投递 E2E；
- 生成客户端固定到可复现的 API 输入版本，公开协议向量纳入 CI；
- 本节全部安全、恢复、隔离与可访问性验收通过。

若先交付设备登录，可以登记为 UC001 的部分实现；不得把邮箱流程从完成定义中静默删除。Gateway 路由和 Auth 本地邮件验证已经消除外部入口阻塞，但不等于 Console E2E 已完成。
