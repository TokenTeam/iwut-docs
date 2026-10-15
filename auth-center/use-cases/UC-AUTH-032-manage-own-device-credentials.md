# UC-AUTH-032：管理自己的设备登录凭据

状态：`ACCEPTED`

## 目标与范围

已登录用户查看当前 iWUT 账号仍可登录的设备凭据，设置便于辨认的名称，并明确移除不再需要或疑似遗失设备的登录资格。用户界面可以称为“登录设备管理”，但服务端管理对象始终是 credential，不声称一条凭据恰好对应一台物理设备。

本 UC 延续 UC031 的邮箱优先方向：设备密钥在后台生成和使用，用户不需要理解或管理私钥。当前协议是 App 自管 P-256 设备密钥，不是标准 WebAuthn Passkey；本轮不引入 WebAuthn、云端密钥同步、设备指纹或硬件可信认证。

首版列表/命名，其他凭据撤销要求 UC033 当前密码＋当前钥新签名。不可逆状态/指纹归属/Session 失效由 UC009 拥有，退休下界由 UC033；不复制规则。结束 Session 用 UC008/020，新增设备默认 UC034 密码登录、UC012 码备用。

不包含旧设备扫码授权新设备、批量/隐式“移除全部其他设备”、凭据硬数量上限、自动过期或 LRU 移除凭据、历史撤销记录查询、IP/地理位置、推送远端退出、第三方 OAuth 会话回收。10 条有效 Session 上限不变，不能解释为凭据数量上限。

2026-10-13 用户明确要求继续完成 UC032，视为接受已有草案范围。依当前 HEAD/工作树复核：UC009 防旁路、UC006/011/031 v3、共享密码校验/额度/下界和 UC025/026 已交付；UC034/重置/通知未完成，不是本 UC 直接运行依赖。先闭合独立协议、公开向量/清理定义并脚本生成 brief，再实施。扫码/WebAuthn/批量移除不扩入本轮。

## 参与者与前置条件

- 调用者是持有有效平台 Session 的 ACTIVE USER；设备登录与邮箱登录 Session 同等适用。
- authId、当前 sessionId、当前 credentialId 和 accountRevision 全部来自 Auth 在线确认，不接受客户端声明的 owner、设备可信标志或身份材料替代。
- 列表/名称仅有效 Session；移除其他凭据额外要求 UC033 当前密码和当前 Session 所引用凭据新签名，不接受另一条凭据或通用已解锁标志替代。
- 移除当前凭据仍使用 UC009 原入口，无新增签名要求，以保留本机退出和最后凭据撤销的既有语义。
- 若当前私钥不可用，但 Session 尚有效，可以查看列表/编辑名称；移除其他凭据须先用 UC012 邮箱登录建立可签名的新凭据与 Session，不能降级为仅凭 Session 移除。

## 输入与输出

以下逻辑消息已同步独立 API Proto。requestId/operationId/credentialId/sessionId 为小写规范 UUIDv4；内部 authId 仍沿用主体 opaque ID。时间为 UTC Timestamp，精度为整数毫秒；labelRevision 为非负 int64，ProtoJSON 按十进制 string 输出。

```text
ListOwnCredentials {
  pageSize: Int?             // 缺省 10，范围 1..50
  cursor: CredentialId?      // 省略或空字符串表示第一页
}

OwnCredentialPage {
  currentCredentialId: CredentialId
  observedAt: Instant
  credentials: OwnCredentialSummary[]
  nextCursor: CredentialId?
}

OwnCredentialSummary {
  credentialId: CredentialId
  label: String              // 未命名为 ""
  labelRevision: Int64
  createdAt: Instant
  isCurrent: Bool
}

SetOwnCredentialLabel {
  credentialId: CredentialId
  label: String              // 必填，"" 明确清除名称
  expectedLabelRevision: Int64
}

OwnCredentialLabel {
  credentialId: CredentialId
  label: String
  labelRevision: Int64
}

BeginOtherCredentialRevocation {
  requestId: UUIDv4           // 同账号幂等键
  targetCredentialId: CredentialId
}

CredentialRevocationStarted {
  operationId: UUIDv4
  currentSessionId: SessionId
  currentCredentialId: CredentialId
  targetCredentialId: CredentialId
  challenge: Bytes32
  expiresAt: Instant
  signingPayload: Bytes
}

CompleteOtherCredentialRevocation {
  operationId: UUIDv4
  signatureDer: Bytes
  currentPassword: Secret     // UC033 密码验证；不进入签名 payload/持久化正文
}

CredentialRevoked {}          // 沿用 UC009 的成功含义
```

不返回公钥、指纹、Session token/digest、邮箱、学校信息、IP、平台型号或原始 User-Agent。当前代码没有凭据级最近登录/使用时间；首版不新增该字段，不把某一 Session 的 lastUsedAt 伪装成凭据或设备最近活动。

## API 契约

独立 package `auth_center.v1.credential_management`，service `CredentialManagementService`；同时交付 HTTP/JSON 与原生 gRPC，Gateway 采用 DIRECT 保留唯一 `x-iwut-session`，由 Auth 自行认证，不先换 USER JWS。

| 方法 | Auth 内部 HTTP 路由 | 成功响应 |
| --- | --- | --- |
| `ListOwnCredentials` | `POST /v1/users/me/credentials:list` | 200，OwnCredentialPage |
| `SetOwnCredentialLabel` | `POST /v1/users/me/credentials:set-label` | 200，OwnCredentialLabel |
| `BeginOtherCredentialRevocation` | `POST /v1/users/me/credentials/revocation:begin` | 200，CredentialRevocationStarted |
| `CompleteOtherCredentialRevocation` | `POST /v1/users/me/credentials/revocation:complete` | 200，CredentialRevoked |

完整 RPC 为 `/auth_center.v1.credential_management.CredentialManagementService/<上述方法名>`，四个方法分别加入精确鉴权分派，无匿名/package 通配例外。POST body `*`，不接受 query、未知/重复 JSON 字段、null、认证材料混用；16 KiB 解码上限、严格 ProtoJSON、bytes 标准 JSON 编码及 no-store 沿用管理接口惯例。

原 `/auth_center.v1.authentication.AuthenticationService/RevokeOwnCredential` 与 `DELETE /v1/users/me/credentials/{credential_id}` 不新增 proof 参数；UC009 已同步修订，这个 Session-only 入口仅允许目标等于当前 Session 的 credentialId。其他目标统一拒绝 `CREDENTIAL_REAUTH_REQUIRED`，不能按目标是否存在提供不同旁路。新增 Complete 是撤销其他凭据的唯一用户入口，在 Auth 内部复用 UC009 的目标撤销事务逻辑，不先提交“已证明”再另调旧接口。

## 主流程

### 查看与命名

1. 在本次一致检查点只读复核调用者 Session、所引用凭据、账号状态和代际。
2. 按可信 authId 有界查询未撤销凭据，或按 `(authId, credentialId)` 定位待命名凭据。
3. 列表返回名称、添加时间和当前标记；命名则在同一认证事务中比较 labelRevision、写入新名称与审计。
4. 查询与命名都不续期 Session、不更新其 LRU 使用时间，也不改变密钥或登录资格。

### 移除其他凭据

1. 用户明确选择一个已展示的目标并确认移除；客户端 Begin 提交固定 requestId/targetCredentialId。
2. Auth 确认当前 Session 与本人目标，保存独立用途的短期挑战。
3. 客户端核对用途、部署上下文、当前 Session/凭据、目标和期限，后台用当前设备私钥签名；不要求用户额外输入邮件码，不声称完成了生物识别或人的在场验证。
4. Complete 使用 Begin 的同一 Session。Auth 在最终事务复核身份和操作，验证签名，原子撤销目标、完成操作并写入必要审计。
5. 只有确认提交后返回成功；未知提交按同一 operationId 重试，不能刷新列表后扩大目标集合。

## 业务规则

<a id="br-lgn-025"></a>
### BR-LGN-025：凭据管理与本人边界

管理范围仅是当前有效 Session 的 authId。所有凭据/游标查询和变更带 owner 条件；他人和未知 ID 使用相同结果。凭据名称、相同邮箱、客户端型号、校园认证和应用 subject 不产生跨账号管理权限。

isCurrent 只表示 credentialId 等于调用 Session 的 credentialId，不证明真实设备型号、唯一物理设备或实时在线。新设备登记不属于此 UC；同一设备可有多把密钥，同一凭据也可有多条 Session。

新增元数据是可选 label 与 labelRevision，放在现有凭据记录，不建立第二套凭据所有权库。已有凭据同时缺少二者时明确解释为未命名、revision=0，仅用于新增元数据；只缺其中之一或非法类型/值按损坏记录拒绝。不得由此给缺失的账号状态、accountRevision、公钥或认证来源补默认值。新创建路径写入空 label/0，不接受未经用户确认的型号或 User-Agent 为权威名称。

<a id="br-lgn-026"></a>
### BR-LGN-026：仍可登录凭据的有界列表

列表包括未撤销且满足 UC033 凭据下界的合法同账号凭据，即使没有有效 Session；不显示撤销/密码退休历史。缺安全版本不默认有效。列表只说明仍允许登录，不证明远端持有私钥；坏认证/元数据依赖失败关闭。

排序固定 `(createdAt DESC, credentialId DESC)`。游标是上页最后实际处理的同账号候选 ID，按该记录不可变时间/ID 作排他锚点；记录后来撤销仍能定位，物理清理后以及未知/非本人游标统一 `INVALID_CREDENTIAL_CURSOR`。每页独立 observedAt，不承诺跨页快照；新登记凭据通过重新查询第一页发现。

每页最多处理 200 条同账号排序候选，达到 pageSize 或扫描预算即停止，至多额外读取一条用于判断是否还有后续。存在后续时 nextCursor 指向最后处理的候选，允许空列表但有游标；客户端只有看到空 nextCursor 才结束。须新增 owner/稳定排序索引，不能因历史撤销记录多而无界扫描。

列表使用不 touch 的 Session 检查，既不刷新 lastUsedAt，也不延长 expiresAt 或执行凭据/Session 淘汰。每账号 10 Session 的容量与 LRU 引用 UC007；本 UC 不引入凭据自动移除或数量硬上限。

<a id="br-lgn-027"></a>
### BR-LGN-027：名称校验与独立乐观并发

label 必填、UTF-8 有效；服务端去除首尾 Unicode 空白后校验，结果允许为空，最多 64 个 Unicode code point 且最多 256 UTF-8 字节。拒绝 Unicode Cc/Cf/Cs 控制、格式及代理类别字符，不作隐式 NFC/NFKC 转换，不支持 HTML/富文本。名称不要求唯一，展示端按普通文本转义，默认未命名文案由客户端本地化。

仅未撤销的本人凭据可改名，未知、非本人和已撤销目标统一 `CREDENTIAL_NOT_FOUND`。expectedLabelRevision 必填且非负，只控制名称；不承担认证代际，不使 Session 或未决撤销挑战失效。

先检查 revision，再判断内容是否改变；同 revision、同规范化名称返回原 revision、不写审计。实际改变 revision 加一并与名称/审计原子提交。过期 revision 即使目标名称已相同也冲突；未知提交后重新读取本人列表，不能盲目覆盖他人并发修改。int64 溢出按数据/依赖异常失败关闭。

<a id="br-lgn-028"></a>
### BR-LGN-028：目标绑定的新设备证明与无旁路要求

移除其他凭据同时要求有效 Session、UC033 当前密码和该 Session 私钥的新签名。Begin 目标不得为当前凭据；当前退出用 UC009。他人/未知拒绝，本人已撤销/退休目标可发新操作确认无秘密结果，但不会恢复目标。

operation 固定 purpose=`REVOKE_OTHER_CREDENTIAL`，绑定 authId、accountRevision、sessionId、调用 credentialId、targetCredentialId、requestId、部署 serviceId、固定 applicationId=`iwut-client`、challenge32、createdAt/expiresAt、Begin 时严格 passwordRevision、状态和失败次数。serviceId 复用客户端预配的 `AUTH_AUTHENTICATION_SERVICE_ID`。challenge 为 CSPRNG 32 字节，首次执行期限 5 分钟，`now >= expiresAt` 即过期，无时钟宽限。目标名称不进入安全绑定，重命名不改变目标。

签名字节如下；UTF8/Frame/U64BE、P-256/SHA-256、严格 DER、high-S/low-S 验证引用[设备协议基础编码与公钥签名](../../platform/contracts/auth-device-session-v1.md)，不改变既有 LOGIN 字节。此处 ID 按规范 UUID 文本 UTF-8 编码，不使用 UUIDBytes。

```text
Frame(
  UTF8("iwut-credential-revocation-proof-v1"),
  UTF8("REVOKE_OTHER_CREDENTIAL"),
  UTF8(serviceId), UTF8("iwut-client"),
  UTF8(operationId), UTF8(sessionId),
  UTF8(callerCredentialId), UTF8(targetCredentialId),
  challenge32, U64BE(expiresAtUnixMs)
)
```

signingPayload 最大 1024 字节，客户端必须重建并逐字匹配，核对当前账号上下文与用户所选目标后才签名。Complete 不接受新公钥、目标、期限或可信证明布尔值。旧 LOGIN、注销、app.close 签名不能复用；同账号另一条 Session、另一把凭据或不同部署也不能替换。签名仅证明私钥控制权，不证明用户亲自确认、设备硬件等级或客户端未被控制。

直接 HTTP、原生 gRPC、Gateway 转发均不能绕过 UC009 的当前凭据限制。仅在 UI 增加签名确认而旧入口继续接受 Session-only 其他目标，不算交付完成。UC009 当前凭据限制已接受并交付，必须持续回归，不能由本 UC 开关关闭而恢复旧旁路。

安全保证仅限本 UC。UC011 邮箱 v3 的密码换主和全局唯一列表已交付；UC033/034 重置/登录/通知仍未交付，不宣称完整新模型已可部署，UC020 不因此自动升级强认证。

<a id="br-lgn-029"></a>
### BR-LGN-029：证明与撤销的原子提交及重试

Begin 幂等范围 `(authId, requestId)`，操作自创建保留 24 小时；同键还必须匹配 sessionId、调用/目标 credentialId、accountRevision 和部署上下文，异参冲突。不延长挑战、不复活过期/失败耗尽操作；过期/耗尽返回证明失败，已完成 Begin 返回 `CREDENTIAL_REVOCATION_ALREADY_COMPLETED`，客户端恢复原 Complete。新 requestId 不撤销旧操作，但受未完成容量限制。

Complete 先在 UC033 有界执行器验密码，最终认证事务复核原密码/账号版本、Session/凭据下界/目标及固定新签名，再复用 UC009 目标变更。密码快照不能穿过并发改密/重置，5 次失败同时涵盖密码/签名；操作/状态/真实变更审计原子，不签通用 proof token。

每个未完成操作最多 5 次密码/验签失败，失败计数与关闭状态原子提交；只有原 owner/Session 匹配后的验签失败计数，其他账号/Session 不能消耗该操作次数。畸形 DER 在入口拒绝，仍受一般限流。复核和验签不得在事务重试时沿用过期的授权快照或时间。

首次执行必须未过期；已确认完成的操作在创建后 24 小时保留窗口内，可由同一仍有效 Session 提交同一操作的新或原合法签名，返回原空成功结果，即使原 5 分钟挑战已过期。该分支只恢复已持久化结果，不再执行变更、延长窗口或签发新权限；幂等键是 operationId，不是可变的 ECDSA 签名字节。错误签名或不同绑定均失败。已经撤销的本人目标在首次 Complete 时幂等完成操作，不覆盖其首次时间、不重复写撤销审计。

账号禁用/恢复、CLOSED、原 Session/调用凭据撤销或过期在最终检查前生效时，Begin/Complete/命名均失败；不能为返回历史成功跳过身份校验。目标撤销与 UC007 登录、UC008/020、UC009、UC022/025 有明确提交先后。撤销后引用 Session 拒绝和在途请求/短期 JWS 的边界继续引用 UC009，不保证第三方独立登录态立即退出。

名称/挑战/完成的管理路径均不 touch Session LRU。签名流程不撤销调用凭据，目标永远为所选单一 ID；网络重试不自动扩大目标。若原 Session 已失效，使用 UC012 恢复后可对同一目标发起新证明，不复用旧操作的授权。

<a id="br-lgn-030"></a>
### BR-LGN-030：有界请求、审计与生命周期清理

四个入口共用有界限流，默认全局 600 次/分钟、每 socket 来源 120 次/分钟、每确认 authId 30 次/分钟，最多 4096 个细分桶；有限正值可配置，桶满失败关闭，不信任 forwarded header。账户额度在身份确认后计入，事务重试不重复扣减，429 携带 Retry-After=60；单进程限流不宣称跨实例/重启持久。

未过期 PENDING 挑战每 authId 最多 5 个、全局最多 10000 个；新集合加入既有 Auth 共享操作容量（总物理保留 1000000，过期每集合每次最多清理 64），不开第二套无界存储，同一次 Begin/Complete 的创建/计数/状态更改原子维护。已完成/到期/耗尽记录不占未完成容量；存储和限流故障不能释放仍有效占用。保留窗口到点后按有界任务清理操作与 challenge；拒绝过期依赖服务端时间，不依赖 TTL 删除是否及时。

真实改名和首次撤销产生不可变审计，包含事件 ID、action、可信 actorAuthId/actorSessionId、调用/目标 credentialId、时间；改名仅记录新 revision，不保存旧/新名称。无变化重试不重复审计，审计失败事务回滚。列表不写业务审计；验签失败仅作脱敏有界安全统计，不写签名、payload 或 challenge。

label 是用户数据，注销清理从保留的凭据占用记录移除；撤销挑战/op 按 authId 纳入 UC025 清理清单，相关审计引用 UC025 的 180 天受控清理和恢复规则。保留最小公钥归属不等于永久保留名称。UC025 已同步集合清单；真实清理/备份恢复必须回归，不新增凭据私钥或硬件数据收集。

请求正文、名称、Session、challenge、signingPayload 和签名不进入普通日志、trace/metrics、URL 或审计正文。返回存储/损坏数据错误而不是伪造空列表或未持久化的成功。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 超过 16 KiB | `CREDENTIAL_MANAGEMENT_REQUEST_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 参数、ID、名称、DER、页大小或 revision 非法 | `INVALID_CREDENTIAL_MANAGEMENT_REQUEST` | 400 / INVALID_ARGUMENT |
| 游标未知/非本人/已清理 | `INVALID_CREDENTIAL_CURSOR` | 400 / INVALID_ARGUMENT |
| Begin 目标为当前凭据 | `CURRENT_CREDENTIAL_NOT_ALLOWED` | 400 / INVALID_ARGUMENT |
| 缺失/畸形/失效 Session、混用认证、不可用主体 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 未知/非本人目标；改名已撤销目标 | `CREDENTIAL_NOT_FOUND` | 404 / NOT_FOUND |
| 旧 UC009 入口指定非当前凭据 | `CREDENTIAL_REAUTH_REQUIRED` | 403 / PERMISSION_DENIED |
| 未知/非本人操作、绑定/签名无效、过期或耗尽 | `CREDENTIAL_REAUTH_FAILED` | 401 / UNAUTHENTICATED |
| 名称 revision 过期 | `CREDENTIAL_LABEL_CONFLICT` | 409 / ABORTED |
| Begin 同幂等键不同上下文 | `CREDENTIAL_REVOCATION_REQUEST_CONFLICT` | 409 / ALREADY_EXISTS |
| 重复 Begin 对应操作已完成 | `CREDENTIAL_REVOCATION_ALREADY_COMPLETED` | 409 / ALREADY_EXISTS |
| 请求/未完成操作容量耗尽 | `CREDENTIAL_MANAGEMENT_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 存储、损坏数据、审计失败或提交未知 | `CREDENTIAL_MANAGEMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

## 测试与验收

1. 两类有效 Session 均可管理本人；不同 authId 隔离，不接受客户端 owner/JWS/OAuth token 替代。
2. 未撤销但没有 Session 的凭据仍显示；当前标记正确；不泄露公钥、指纹、邮箱或虚构最近使用时间。
3. 已有凭据未命名投影为 label=""/revision=0；损坏认证字段和元数据失败关闭，不补认证默认值。
4. 页大小、稳定排序、200 条扫描预算、空页续游标、已撤销游标、新增/清理竞争；列表不改变 LRU/期限/容量。
5. 名称空值/Unicode/256 字节与 64 code point 边界、控制字符、CAS、无变化、revision 溢出、改名/撤销竞争、审计回滚和未知提交恢复。
6. 当前设备新签名移除其他凭据；只有 Session、另一设备或旧 LOGIN/app.close/注销签名均失败；同操作换 Session/目标/部署不可用。
7. 旧 UC009 HTTP/gRPC 对非当前目标拒绝，不能绕过；撤销当前凭据及本机退出、最后凭据语义保持通过。
8. 5 分钟过期、5 次验签失败、每账号/全局 PENDING 容量、24 小时幂等、异参冲突、完成响应丢失重试；合法不同 DER 不产生第二次变更。
9. Complete 的操作/目标/审计同事务；并发登录、双撤销、Session 回收、账号禁用/恢复/注销与事务重试具备明确顺序；失败无部分成功。
10. 目标全部引用 Session 后续检查失败，其他凭据不受影响；重新添加必须 UC012 新密钥，不恢复旧凭据，不撤销 OAuth grant。
11. 四个新入口与旧撤销入口的真实 HTTP/native gRPC/Wire/Mongo 副本集 race 验收；PUBLIC Gateway/客户端独立验收，不能以 fake verifier 代替。
12. 注销清理名称与挑战、审计受控到期、备份恢复不复活账号/凭据；签名/payload/challenge/token 不进入日志、审计或 URL。

## 依赖检查与接受门禁

[开工检查](../implements/UC-AUTH-032-readiness.md)已按当前 HEAD/工作树更新；用户 2026-10-13 授权继续完成。已有 no-touch Session、P-256、共享密码校验/持久额度、下界与 Auth 事务栅栏可复用；邮箱 v3、UC009/025/026 已交付。普通密码登录、重置/通知和 Gateway/客户端仍单独交付，不据此卡住本 UC 的直接依赖，也不宣称完整新模型可启用。

新签名字节/Proto presence/向量见 [设备凭据管理 v1](../../platform/contracts/auth-credential-management-v1.md)。接受后先配置 spec、脚本生成 brief，再实现。UC025 增加管理操作清理和审计 180 天受控保留；已撤销凭据也必须保留最小归属后删除名称，不能因 revokedAt 而阻断注销。没有生产迁移、自动修复、提交、推送或部署。

## 邮箱安全新要求与待确认依赖

密码生命周期/危险动作和默认密码登录 UC033/034 已 ACCEPTED，共享校验/额度/下界已交付；登录/重置/通知与公开密码服务仍未交付。UC006/009/011/031 等相关修订及代码状态独立跟踪；本节仅导航，不另定义密码规则。

- 注册设置密码及完整原子创建引用 [UC006 / BR-REG-001/002/006](UC-AUTH-006-create-user.md#br-reg-001)。
- 邮箱列表唯一登录角色、切换需密码和非登录绑定增删引用 [UC011 / BR-EML-001/003/004](UC-AUTH-011-set-and-activate-email.md#br-eml-001)；登录邮箱为最终恢复依据，正常改密码需旧密码，忘记密码仅登录邮箱码重置引用 [BR-EML-008](UC-AUTH-011-set-and-activate-email.md#br-eml-008)。
- 当前学校绑定依据/最后解绑撤回引用 [UC031 / BR-CMP-002/004/005](UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-002)，不是学生/学籍证明。

### 密码恢复与登录依赖

修改/恢复状态、版本、设备清退和 OAuth 失效的唯一规则见 [UC033 / BR-PWD-004–007](UC-AUTH-033-manage-password-and-recovery.md#br-pwd-004)：正常保留当前钥并新建 Session，重置全部旧钥/Session 失效，不自动登录；grant/sub 保留，旧离线窗口明确。默认密码登录见 UC034，UC012 码登录保留备用，不能沿用本节旧“策略未确定”作为最新需求。

### 剩余交付依赖

邮箱 v3 容量/归属/角色/校园语义已接受并实现；当前密码 verifier 可供本 UC 使用。正式部署仍需要正式 blocklist、目标机器压测、完整密码登录/重置/通知、Gateway 与客户端验收。本 UC 不实现这些独立工作包，不降低现有安全门禁。

用户最新明确登录邮箱切换必须密码，不把此前“密码或手机扫码二选一”继续作为有效需求。手机扫码仍属另行设计的跨设备审批，不是 UC032 的当前 Session 同设备签名，也不是已实现的 WebAuthn Passkey。本轮不实现扫码、不将其默认为登录邮箱切换或密码恢复的替代授权。

校园认证撤回不改变 authId/pairwise sub，不由 Auth 回收或重置应用已发放次数；应用的存量权益和重复领取继续自行管理。新的实时认证披露与第三方已取得的历史数据/独立登录态不能混为立即全量删除。

## 变更记录

- 2026-10-13：用户授权继续完成既有 UC032，依赖复核后 ACCEPTED，脚本生成 brief 再实施；独立管理协议、UC009 防旁路及 UC025 清理同步，Gateway/客户端独立交付。
- 2026-10-12：记录用户确认的平台密码、邮箱列表唯一登录角色、当前学校绑定导出校园认证，以及仅当前登录邮箱验证码重置密码；覆盖此前密码/单多邮箱待确认项与邮箱切换扫码替代方向，协议和恢复后凭据策略仍待审核。
- 2026-10-12：追加用户要求的邮箱更换强认证、最后登录邮箱保护与解绑学校邮箱撤回认证方向；密码/扫码及单多邮箱模型待确认，现有 ACCEPTED UC 未自动修订。
- 2026-10-12：建立 DRAFT；首版列表/命名/单目标移除，当前设备新签名与目标撤销同事务；记录 UC009 防旁路修订、UC011 安全保证边界和独立交付依赖，待用户审核。
