# UC-AUTH-007：登录并建立会话

状态：`ACCEPTED`

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。

> 已有平台账号的用户通过设备凭据证明账号控制权，由 Auth 建立可在线检查、可撤销的 Session，供后续受保护请求使用。

本文件是设备登录、Session 建立与在线检查规则的权威正文，也供 [UC-AUTH-006](UC-AUTH-006-create-user.md) 建立首次会话引用。Session 与凭据撤销的 `BR-LGN-*` 正文分别位于 UC-AUTH-008/009。认证协议引用 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)，运行参数由本 UC 定义；设计接受不表示已实现。

本轮闭合设备凭据登录、Session 建立与在线检查。Session 撤销由 [UC-AUTH-008](UC-AUTH-008-revoke-own-session.md) 定义，设备凭据撤销由 [UC-AUTH-009](UC-AUTH-009-revoke-own-credential.md) 定义；退出、账号切换、自动登录和本地秘密删除属于客户端编排，见非权威的[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。邮箱认证、邮箱绑定、旧设备迁移授权、账号禁用和全设备管理分别另立用例。

客户端使用随机 opaque sessionToken。服务间可信身份继续遵守 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md) 和 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)，本 UC 不修改 JWS 格式、不把 Session 令牌作为可信身份头转发给业务服务。

## 参与者与前置条件

- 调用方持有已登记设备凭据的私钥及 credentialId。客户端记录缺失时，可通过协议定义的公钥定位摘要发起登录，不能用学号关联定位并授权账号。
- Auth 中有归属唯一、有效的设备凭据；其账号当前是 ACTIVE USER。
- Begin/Complete 是匿名认证入口，不要求已有 Session 或用户 JWS；校验真实证明而非信任客户端账号标签。
- 凭据的身份/公钥规范化与唯一归属引用 [BR-REG-003](UC-AUTH-006-create-user.md#br-reg-003)。

## 输入与输出

```text
BeginDeviceLogin {
  credentialLocator: CredentialId | CanonicalPublicKeyFingerprint
}

LoginChallenge {
  operationId: OpaqueId
  challenge: Bytes
  signingPayload: Bytes
  protocolVersion: string
  expiresAt: Instant
}

CompleteDeviceLogin {
  operationId: OpaqueId
  proof: CredentialAuthenticationProof
}

SessionEstablished {
  authId: AuthId
  credentialId: OpaqueId
  sessionId: OpaqueId
  sessionToken: Secret
  expiresAt: Instant
}
```

凭据定位信息不是身份秘密，也不能独立授权。Complete 不接受目标 authId、角色、权限或客户端指定有效期。protocolVersion 取自服务端已登记凭据和允许配置，不允许客户端在登录时替换公钥/算法。

以上为逻辑消息。proof 结构引用[公钥与签名](../../platform/contracts/auth-device-session-v1.md#公钥与签名)，signingPayload 及成功登录返回的 credentialId 引用[挑战与待签消息](../../platform/contracts/auth-device-session-v1.md#挑战与待签消息)。生成 Proto、原生 gRPC 和 middleware 按共享契约交付，Gateway 路由另行验收。

## 主流程

1. 调用方为本次登录选择本机仍持有的设备凭据；是用户点击还是客户端自动触发，不改变服务端协议和结果。
2. Begin 校验输入与限额，创建 purpose 为 LOGIN 的挑战，并固定凭据定位、协议版本、服务/应用上下文。
3. 客户端使用对应私钥生成登录证明；本产品不要求额外的生物识别或每次签名前确认，所选平台 API 必需的交互仍须遵从。它不上传私钥或学校凭据。
4. Complete 检查挑战、协议和签名；用登记公钥确定凭据，再由服务端凭据记录确定 authId。
5. 在原子确认点复核操作未消费/未过期、凭据有效、主体为 ACTIVE USER，按 BR-LGN-010 处理会话容量，消费挑战并创建新 Session。
6. 提交成功后返回 SessionEstablished。客户端安全保存令牌，加载该账号的数据。

已有账号登录失败不会创建新 USER、添加新凭据或自动改绑学号关联。UC-AUTH-006 的成功注册可以复用会话建立规则，但不再次要求用户完成一轮登录交互。

## 业务规则

<a id="br-lgn-001"></a>
### BR-LGN-001：账号来源与认证方法隔离

设备登录的 authId 只来自通过证明验证的服务器凭据归属。显示名、设备 ID、学校登录成功标志、associationToken、associationId、邮箱字符串和客户端缓存不能替代认证。

登录只允许 ACTIVE USER 和有效凭据。未知、已撤销、禁用或非 USER 主体不建立 Session；对外统一返回认证失败，不泄露对应邮箱、资料或关联成员。

未来邮箱认证和旧设备授权可为同一 authId 建立会话或新增凭据，但必须由各自用例验证控制权；不能通过增加 loginMethod 字符串、复用客户端布尔值就进入此成功路径。登录方式、凭据、Session 和恢复能力是独立事实。

<a id="br-lgn-002"></a>
### BR-LGN-002：挑战绑定与一次性证明

注册和登录均使用 Auth 生成的密码学随机挑战及不可变操作记录。首版挑战具有 256 bit 随机性，寿命固定为 5 分钟；编码和上下文遵守共享契约。服务端以自己的时间检查过期，不依赖 TTL 清理是否已发生。

挑战记录绑定 purpose（REGISTER/LOGIN）、operationId、协议版本、服务标识、允许的应用/来源上下文，以及完整的注册提案快照或登录凭据定位。注册关联声明以受控摘要绑定，存储边界引用 BR-REG-004。签名/协议证明须覆盖挑战及规定上下文，不能跨用途、账号、凭据或服务重放；客户端不能在 Complete 改写 Begin 的输入。

每个 operation 的成功消费与业务提交原子发生。失败尝试需要有界计数及最终关闭状态，随机 operationId 本身不是认证凭证。并发提交不能多次消费，超时或网络重试不能延长挑战寿命；无效证明不修改账号、凭据或建立会话。

未知凭据的 Begin 应返回与已知凭据兼容的普通挑战或统一响应，不提供账号存在性和状态查询；Complete 统一失败。单凭持有挑战/定位摘要不能登录。挑战签名成功仅证明密钥控制权，不自动证明客户端未被篡改、硬件安全等级或生物识别已执行；相关声明须由所选协议的可验证证据支持。

<a id="br-lgn-003"></a>
### BR-LGN-003：会话权威与秘密令牌

Auth 保存 Session 权威状态，每个 Session 只对应一个 authId。sessionId 是非秘密的记录标识，sessionToken 是 CSPRNG 生成、至少 256 bit 随机性的 bearer secret；二者不得互相替代。令牌不编码学号、邮箱、权限或用户资料，不要求 JWT。

token 线格式、摘要输入和认证载体引用[Session 载体契约](../../platform/contracts/auth-device-session-v1.md#session-载体)。服务端持久化 token 的 SHA-256 摘要并建立唯一索引，不保存明文令牌；高熵随机令牌不同于低熵密码，不从密码/学号派生。客户端通过 TLS 传输并安全存储令牌，不在 URL、普通日志、分析事件或崩溃报告中包含它。拥有有效 bearer token 即可使用会话，本规则不宣称自动具有设备持有证明或防重放能力。

每条 Session 记录本次认证方法、凭据引用（设备认证时必填）、authenticatedAt、createdAt、lastUsedAt、expiresAt、撤销状态与时间。lastUsedAt 的使用与更新规则见 [BR-LGN-010](#br-lgn-010)。Session 不包含私钥，不被 profile、学生关联或客户端设备名称决定归属。以后添加邮箱方法时必须扩展明确的认证记录语义。

<a id="br-lgn-004"></a>
### BR-LGN-004：有效期与在线检查

首版采用固定绝对有效期：T_session 通过 AUTH_SESSION_TTL 配置，为部署必填的正时长，创建时固定 expiresAt；缺失/非法配置拒绝接流量。配置采用 Go duration 格式，示例部署值为 `720h`（30 天）；该示例不是隐式默认值。本轮不自动滑动续期、不签发 refresh token，也不因请求活跃无限延长会话。到期后必须重新完成本用例的设备认证并建立新 Session，不延长旧会话的 expiresAt。后续若增加续期，另行设计轮换与并发语义。

一次成功会话检查必须得到一致、当前的事实：token 摘要匹配，Session 未撤销且 `now < expiresAt`，所属主体为 ACTIVE USER，作为会话认证依据的设备凭据仍有效且归属一致。缺失、损坏、超时或无法读取均失败关闭，不能回退到客户端缓存或只凭旧 JWT 放行。

首版不缓存正向会话授权结果，权威读取不得使用可能落后的副本。建议使用一致快照读取主体、凭据和 Session；检查与撤销/禁用存在并发时，以明确的检查快照为边界。变更提交后才开始的新检查必须看到变更；先已通过的请求可能继续执行，不承诺取消在途业务。

成功检查还须完成 [BR-LGN-010](#br-lgn-010) 的使用时间更新；不能先返回检查成功，再异步记录使用时间。此更新不改变固定 expiresAt。

清理过期会话只是存储维护；即使记录未被删除也不能再通过检查。更改配置不追溯改变已有 expiresAt；紧急失效使用显式撤销，不通过重解释时间或静默换令牌完成。

<a id="br-lgn-006"></a>
### BR-LGN-006：多账号与会话独立

同一 App 安装可以分别持有多个账号的设备凭据与 Session。登录 B 只建立 B 的新 Session，不覆盖、撤销、删除或改绑 A 的凭据与 Session；Auth 不提供“切换账号”的跨账号原子命令。客户端如何选择当前账号及隔离缓存/后台任务属于客户端编排建议。

不同设备独立建立 Session；新会话不默认踢掉全部旧会话。单账号达到上限时按 [BR-LGN-010](#br-lgn-010) 淘汰最久未使用的会话，为新登录腾出容量。新增设备凭据必须单独获得授权，本登录接口不能把请求里的新公钥加入账号。

<a id="br-lgn-007"></a>
### BR-LGN-007：原子登录与重试

消费挑战、最后复核账号/凭据状态、必要的 LRU 淘汰和创建 Session 必须作为一个原子业务提交，不能先消费挑战或撤销旧会话，再在非原子步骤中写新会话。Mongo 实现使用事务；只有读取快照不足以排除并发禁用/撤销的写偏差，必须对参与认证的主体与凭据做条件更新/版本栅栏等可串行化确认，并保证同一账号并发创建不会突破 BR-LGN-010 的容量约束。实现工作包需给出具体字段、锁定顺序和真实并发测试，不能只在代码注释声称原子。

当禁用/凭据撤销先完成时登录失败；登录先完成则可以建立会话，后续检查仍受 BR-LGN-004 控制。事务回滚不留下已消费成功状态或可用 Session；服务端事务自动重试使用固定的候选 sessionId/token。

成功证明不可重放领取更多 Session。相同操作已成功时返回 LOGIN_ALREADY_COMPLETED，不重发原 token、不生成第二个 token。响应丢失时客户端保留原凭据，重新发起挑战建立新 Session；可能遗留的未取得令牌会话按寿命/限额规则处理。不能把“已完成”当作客户端已经登录，也不能明文保存 token 以支持重放。

<a id="br-lgn-008"></a>
### BR-LGN-008：会话检查与可信身份签发衔接

会话检查是 Auth 的内部能力，成功得到 authId、sessionId、认证时间/方法等最小可信上下文；SessionEstablished 不是业务服务接受的身份 JWS。客户端不能拿 sessionId、associationId 或 Session token 直接构造 x-iwut-identity。

建议 Gateway 把会话令牌提交给获授权的 Auth 鉴权入口；Auth 完成 BR-LGN-004 检查后，按目标服务签发可信身份，再由 Gateway 转发。目标 audience 来自服务端路由/调用权限约束，不信任终端任意指定。业务服务本地验签和权限投影继续引用既有平台契约，不增加每个业务服务的 Session introspection。

本规则只定义前置条件和能力边界。Gateway→Auth 鉴权 RPC、秘密头移除、受保护/匿名路由划分、身份签发权限投影与密钥接入需要后续签发用例及平台契约闭合。不得在缺少这些交付时，把本 UC 的成功 Session 当成 UC-AUTH-005 已能从公网调用。

撤销后不再为随后检查的 Session 签发新身份。此前已经签发的 JWS 仍按 [trusted-identity-v1 的时间规则](../../platform/contracts/trusted-identity-v1.md#时间与有效期) 被消费方验证，包含配置的时钟容差；不能声称 Session 撤销让所有已签发凭证即时失效，也不绕过 [BR-RVW-004](UC-AUTH-004-manage-reviewer-permission.md#br-rvw-004) 的本地验签边界。

<a id="br-lgn-009"></a>
### BR-LGN-009：认证入口的失败与披露边界

Begin/Complete 需要请求大小、挑战尝试次数、创建速率和未完成操作容量限制；按来源/操作/凭据等维度组合，不信任客户端设备 ID。初始参数如下，必须在上线前配置校验，不由学生关联分组代替。

认证入口工程默认值：解压后消息上限 16 KiB、单挑战最多 5 次失败、全局 Begin 每分钟 600 次、全局 Complete 每分钟 1200 次、同来源 Begin 每分钟 30 次、同定位 Complete 每分钟 60 次、未完成挑战最多 10000 条。参数可配置但必须有限且为正，非法配置拒绝启动；总体容量和全局限速即使来源不可确认也必须生效。未知 operationId 的 Complete 同样计入全局 Complete 限流，不能通过制造新定位或未知操作绕过总量保护。来源默认使用受信网络对端，不信任终端自填 forwarded header；Gateway 精细来源限流以后通过受信转发契约接入。挑战次数和未完成容量在 Auth 持久化层原子确认；单进程速率桶允许重启清空，不称为跨重启风控。每来源及每定位桶的存储必须有有限容量、过期淘汰和容量耗尽策略，不能因任意客户端定位形成无限内存增长；即使无法新增细分桶，全局限流仍须生效。

错误不区分未知账号、已撤销凭据、错误签名与账号禁用的具体身份事实。依赖不可用与错误凭据区分，便于客户端重试而不是误创建账号。对外不返回账号是否绑定邮箱、关联组成员、内部验签细节或堆栈。

认证请求/响应正文不进入常规日志；禁止记录 token、完整挑战/证明或任何私钥。操作元数据可以记录 operationId、sessionId、结果和时间，已确认身份后才记录可信 authId。Session 不含用户资料，认证事件不广播敏感声明。

<a id="br-lgn-010"></a>
### BR-LGN-010：会话容量与 LRU 淘汰

首版确定单账号最多 10 个有效 Session，即 `N_session = 10`。容量按 authId 统计，覆盖该账号全部设备，不按设备、公钥或学生关联组分别计算；它不是设备凭据数量上限。已撤销、已过期或认证凭据已失效的会话不占有效容量，其物理记录可随后清理，不等待 TTL 删除后才释放名额。

有效登录将创建新 Session 时，若当前有效会话数为 M，先从既有有效会话中按 LRU 选择 `max(0, M + 1 - N_session)` 条撤销，保证提交后的有效数量不超过上限。通常满额时淘汰一条；若既有数据超过上限，在下一次成功登录一并收敛。容量满额本身不拒绝已通过认证的新登录，入口限流规则仍然适用。Begin、无效证明、登录失败和已完成操作的重放均不能触发淘汰。

LRU 以服务端保存的 `lastUsedAt` 升序决定；相同时依次按 createdAt、sessionId 升序确定顺序。新会话的 lastUsedAt 初始化为 createdAt；从未被使用的会话按建立时间参与排序，包括成功响应丢失后遗留的会话。新会话不参加本次既有会话的淘汰候选。

“使用”指 Auth 成功完成 BR-LGN-004 的权威会话检查。检查成功返回前，以服务端时间单调更新 lastUsedAt，不接收客户端提供的使用时间，不因失败检查、退出请求或查询会话列表刷新。后续业务因权限或参数等原因失败，不回滚已发生的会话使用；业务服务仅本地验证既有 JWS 不产生新的 Auth 会话使用事件。首版每次成功检查同步记录，不引入异步写回或时间窗口合并；若以后接受近似 LRU，须显式修改本规则。lastUsedAt 更新不延长 expiresAt。

会话检查及使用时间更新，与 LRU 选择/撤销必须有一致的并发顺序：先完成的使用更新影响后发生的淘汰选择；先被淘汰的会话不能再通过检查或被使用时间更新复活。并发冲突时重新确认状态和候选，不用陈旧候选强制撤销；更新失败不能返回会话检查成功。单机多请求也须满足此规则，具体存储栅栏与 BR-LGN-007 一并验收。

淘汰采用逻辑删除，即写入 revokedAt 并立即停止接受其后续会话检查；物理删除沿用生命周期清理策略。被淘汰会话的设备凭据、账号资料和其他账号会话保持不变，用户仍可用有效凭据重新登录。淘汰、挑战消费与新 Session 创建遵循 BR-LGN-007 的同一原子提交：创建失败则不丢失旧会话；提交成功但响应丢失时，已发生的淘汰不回滚，客户端按既有未知结果规则重新认证。

<a id="br-lgn-011"></a>
### BR-LGN-011：登录触发与客户端边界

Auth 不区分本次登录由用户点击、应用启动、Session 到期还是业务请求恢复触发；所有调用都必须执行相同的挑战、私钥持有证明、账号/凭据复核、限流和 Session 创建规则。客户端的 `automatic=true`、`userConfirmed=true` 或类似声明不构成认证证据，也不改变服务端权限。

首版 App 管理设备密钥的服务端协议不要求生物识别、设备 PIN 或额外点击的证明；它只证明对应私钥控制权。操作系统安全存储若要求本地交互，客户端必须遵从，但 Auth 不接收无法验证的布尔声明。客户端何时自动调用、如何合并并发登录、退出后是否继续尝试及如何删除本地秘密不属于本 UC 的服务端后置条件。

每次成功调用都创建一条新 Session，并受 BR-LGN-010 的 10 条上限和 LRU 约束；不得用自动触发名义绕过限流或无限创建 Session。Session 建立不授权客户端自动重放结果未知的业务写命令，业务重试遵守对应命令的幂等规则。

## Session 持久化结构

```text
Session {
  sessionId: OpaqueId
  authId: AuthId
  tokenDigest: Bytes
  authenticationMethod: DEVICE_CREDENTIAL
  credentialId: OpaqueId
  authenticatedAt: Instant
  createdAt: Instant
  lastUsedAt: Instant
  expiresAt: Instant
  revokedAt: Instant?
}
```

`auth_sessions` 独立于 principal/profile 保存；sessionId 和 tokenDigest 分别唯一，authId/credentialId 支持管理查询。过期是时间判定，不要求后台及时把状态改成 EXPIRED。revokedAt 一旦设置不能通过登录/续期清空；新登录生成新 Session。

LRU 查询需支持按 authId 过滤，并按 lastUsedAt、createdAt、sessionId 稳定排序；有效候选与容量语义引用 BR-LGN-010，索引设计需结合有效期和撤销状态验收。

会话令牌与服务间 JWS 签名密钥、关联查找 HMAC 密钥各自独立；Session 随机令牌无需复用这些密钥。多实例共享权威存储，不依赖进程内会话；初版不强制 Redis。

## 错误语义

内部会话检查不直接暴露 token 到 authId 的公共查询，不签发客户端可自行选择任意 audience 的身份。内部调用认证、路由和具体 RPC 权限见交付依赖。

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 输入形状或定位信息非法 | `INVALID_LOGIN_INPUT` | 400 / INVALID_ARGUMENT |
| 挑战、证明、凭据或账号不可接受 | `AUTHENTICATION_FAILED` | 401 / UNAUTHENTICATED |
| 相同登录操作已经成功 | `LOGIN_ALREADY_COMPLETED` | 409 / ALREADY_EXISTS |
| 会话检查缺少/无效/过期/撤销 token 或当前账号不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 请求速率或未完成挑战容量达到上限 | `AUTHENTICATION_LIMIT_EXCEEDED` | 429 / RESOURCE_EXHAUSTED |
| 解压后输入过大 | `AUTHENTICATION_INPUT_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 仓储、协议配置不可用或提交结果未知 | `AUTHENTICATION_UNAVAILABLE` | 503 / UNAVAILABLE |

表中 reason 为本用例错误语义，框架解码前的错误至少保持标准状态。Session 撤销和凭据撤销的错误语义分别由 UC-AUTH-008/009 定义。

## 测试与验收

1. 有效凭据只登录其归属 authId；账号名、学校声明和请求里的其他 authId 均不能改变归属。
2. 未知、撤销、禁用、SYSTEM、错误签名均不建立会话；Begin 不提供可直接枚举账号状态的分支。
3. 注册证明不能作为登录证明，跨操作/服务/凭据/版本重放失败；过期时间在 TTL 清理前即生效。
4. 并发 Complete 最多建立一条 Session；故障注入证明挑战消费和 Session 创建原子，响应丢失后可用新挑战登录。
5. 登录与禁用/撤销并发有明确顺序，不能凭陈旧读取通过最后确认；使用真实 Mongo 并发测试验证栅栏。
6. Session 明文只在成功响应和客户端受保护存储出现；数据库只有摘要，sessionId 本身不能认证。
7. 到期、撤销、主体禁用和凭据撤销后的新会话检查失败；损坏数据和依赖故障不降级放行。
8. 登录 B 不修改 A 的凭据和 Session；Auth 不接受把账号切换伪装成跨账号原子命令，也不混合两个 authId 的状态。
9. 已签发 JWS 的本地验证不受本 UC 悄悄改变；新鉴权失败时不新签身份，签发链路单独 E2E 验收。
10. 固定会话寿命不因活跃请求滑动；到期需要重新执行设备登录；日志、错误和限流测试覆盖信息披露边界。
11. 满额时成功登录淘汰 lastUsedAt 最早的既有有效 Session，即使另一个会话创建更早但最近使用也应保留；时间相同按规定次序处理，新会话保留，账号和设备凭据不受影响。
12. 每次成功会话检查同步且单调更新 lastUsedAt，不改变 expiresAt；失败检查或列表查询不刷新，后续业务拒绝不回滚更新。已过期/撤销/凭据失效会话不占容量，未使用会话以 createdAt 排序。
13. 满额并发登录后有效数量不超过 N_session；使用时间更新与淘汰并发符合规定顺序，被淘汰会话不被复活；注入事务失败证明旧会话撤销与新会话创建一起回滚。
14. 无效登录/Begin/成功操作重放不淘汰会话；响应丢失后的重新认证仍可建立新会话。覆盖已有 9 条时不淘汰、10 条时淘汰一条、历史超过 10 条时收敛，不以会话满额返回 AUTHENTICATION_LIMIT_EXCEEDED。
15. 手动和自动触发得到相同的挑战与验证结果；客户端布尔声明不能代替签名、绕过限流或改变账号归属。自动触发也不能无限创建 Session 或授权重放结果未知的业务写命令。

## 交付依赖与后续用例

- 与 UC-AUTH-006 共用共享协议的真实验证器、生成 Proto 和测试向量；Android/iOS 安全存储与兼容性由客户端独立验收。
- AUTH_SESSION_TTL 的部署配置与非法配置拒绝启动；到期后重新执行同一登录协议，客户端触发体验见指导文件。
- 失效记录的物理清理保留期；每账号 10 个有效 Session 及 LRU 淘汰行为已由 BR-LGN-010 确定。
- 按 BR-LGN-009 交付挑战失败次数、速率/消息大小与未完成操作上限；与 UC-AUTH-006 共用有界入口策略。
- Mongo 登录条件栅栏、会话检查及使用时间更新的一致策略、LRU 排序索引，以及未来禁用/撤销命令共用的并发约定。
- 独立 API 包 `auth_center/v1/authentication/`；BeginDeviceLogin/CompleteDeviceLogin、匿名入口及 Session 入口按[RPC 鉴权表](../../platform/contracts/auth-device-session-v1.md#rpc-鉴权表)实现 middleware。
- 持久化表结构、端口接口与 Mongo 事务栅栏由实现集成负责人统一；单机多请求仍须满足原子登录、撤销及 LRU 顺序，不新增在线密钥迁移。物理删除未单独验收前可保守保留撤销记录，不能释放公钥唯一归属。
- Auth 身份签发用例及 Gateway 鉴权契约，随后贯通 UC-AUTH-005 的用户调用链。
- Session/凭据撤销分别由 UC-AUTH-008/009 定义；邮箱绑定及认证（验证码还是密码尚未决定）、旧设备授权新增凭据、其它设备/会话管理、注销、关联修改与对外披露另立用例。

## 变更记录

- 2026-09-22：接受本用例，设备证明、关联声明、Session 载体与 RPC 鉴权引用 auth-device-session-v1；后端、客户端和 Gateway 分别验收。

- 2026-09-22：建立设备凭据登录与服务端 Session 草案，定义一次性挑战、有效期候选、退出、多账号、并发/重试及与既有身份 JWS 的边界。
- 2026-09-22：复核待定项，明确会话到期后的客户端交互、容量耗尽时的登录恢复路径仍需决定；密钥迁移性能不再作为设备登录设计的未决项。
- 2026-09-22：确定会话满额采用 LRU，按服务端 lastUsedAt 淘汰最久未使用的有效会话；补充使用时间更新、原子淘汰/创建及并发验收，具体容量数值仍待定。
- 2026-09-22：确定每账号最多 10 个有效 Session，允许保持登录的账号使用本机凭据自动重新认证，不要求额外生物识别；补充退出意图持久化、认证合并及防循环边界。
- 2026-09-22：首版改为 App 管理设备密钥；用户确认退出后删除本机私钥和 token，并撤销当前服务端凭据。退出警告承担不可恢复风险披露，不再保留本机凭据供退出后再次登录。
- 2026-09-22：将 Session 撤销和凭据撤销拆到 UC-AUTH-008/009；UC7 只保留登录、Session 建立/检查及服务端触发边界，客户端退出和切换流程移至指导文件。
