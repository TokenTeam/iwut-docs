<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-009 --spec tools/brief-specs/UC-AUTH-009.json -->
# Brief — UC-AUTH-009：撤销自己的设备凭据

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-009` 撤销自己的设备凭据 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-LGN-012` |
| 外部引用 BR | `BR-LGN-004`（来自 `UC-AUTH-007`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

> 已认证用户要求 Auth 撤销属于自己账号的一条设备凭据，使该公钥不能再建立新 Session，并使依赖该凭据的既有 Session 在后续在线检查中失效。

本用例只改变 Auth 持有的凭据状态。它不声称能够删除客户端私钥，也不规定退出警告、本地清理和离线体验；客户端组合建议见[客户端认证生命周期建议](../client-guides/authentication-lifecycle.md)。只撤销当前 Session 使用 [UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md)。

### 参与者与前置条件

- 调用者持有通过 BR-LGN-004 检查的有效 Session，主体为 ACTIVE USER。
- 目标 credentialId 由调用者明确提交；Auth 以当前 Session 的 authId 做所有权判断，不接受请求体指定目标 authId。

### 输入与输出

```text
RevokeOwnCredential {
  credentialId: OpaqueId
}

CredentialRevoked {}
```

这是逻辑消息，生成 Proto、Session 载体与 RPC 鉴权遵守 [App 设备认证与 Session v1 契约](../../platform/contracts/auth-device-session-v1.md)。接口名称中的 Revoke 表示不可逆状态迁移，不等同于立即物理删除记录。

### 主流程

1. Auth 验证当前 Session，并取得可信 authId。
2. 校验 credentialId 形状，按 `(authId, credentialId)` 读取目标凭据。
3. 若凭据有效，以服务端时间原子设置 revokedAt；若同一账号的目标已经撤销，幂等返回成功。
4. 提交成功后返回 CredentialRevoked。若目标正是当前 Session 的认证凭据，该 Session 从下一次在线检查开始失效。

### 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| credentialId 缺失或格式非法 | `INVALID_CREDENTIAL_ID` | 400 / INVALID_ARGUMENT |
| Session 无效或主体不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 目标不存在或不属于当前 authId | `CREDENTIAL_NOT_FOUND` | 404 / NOT_FOUND |
| 仓储不可用或提交结果未知 | `CREDENTIAL_REVOCATION_UNAVAILABLE` | 503 / UNAVAILABLE |

客户端不依赖 message 文本判断归属。已撤销的本人凭据返回成功；其它账号和未知目标不做区分。

### 测试与验收

1. 有效 Session 可以撤销同一 authId 的当前或其它凭据；不能撤销其它账号凭据。
2. 撤销后新设备登录失败，引用该凭据的所有 Session 在随后在线检查中失败，其它凭据和 Session 不受影响。
3. 重复与并发撤销幂等，revokedAt 不变化，公钥唯一归属不释放。
4. 撤销当前凭据后当前 Session 失效；注入响应丢失时不把结果未知误报为回滚。
5. 允许撤销最后一条凭据，不使用邮箱、学生关联或客户端恢复声明作为服务端门禁。
6. 未知与他人 credentialId 响应一致；畸形输入、无效 Session、禁用账号和仓储故障失败关闭。
7. 日志和审计只有受控标识与结果，不含 token、私钥或证明正文。

### 交付依赖

- 按共享契约交付 `auth_center/v1/authentication/` RevokeOwnCredential、有效用户 Session middleware 和精确 RPC 鉴权表；Gateway 路由与客户端编排独立验收。
- 凭据记录的状态字段、条件更新与审计存储；物理保留期由后续生命周期策略确定。
- 查询/命名/撤销其它设备的完整管理体验、再认证策略和凭据新增仍可另立管理用例，本用例只提供按 credentialId 的最小撤销命令。

## 业务规则（UC-AUTH-009 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-009-revoke-own-credential.md#br-lgn-012 -->
### BR-LGN-012：本人设备凭据的授权撤销

只有当前有效 USER 可以撤销归属于相同 authId 的凭据。未知 credentialId 与属于其它账号的 credentialId 使用相同未找到结果，不泄露其归属；客户端不能通过提交 authId、学校关联或设备标签改变授权范围。SYSTEM、禁用账号或无效 Session 不得调用成功。

撤销采用凭据记录的不可逆 revokedAt 状态，不物理删除公钥，不释放规范公钥指纹的唯一归属，也不允许以后清空 revokedAt 复活。重复撤销同一账号已撤销的凭据，在调用 Session 仍有效的前提下幂等成功；并发请求只有一个首次撤销时间。操作记录允许包含 authId、credentialId、调用 sessionId、结果和服务端时间，不记录 Session token 或私钥材料。

凭据撤销提交后，它不能再完成 UC-AUTH-007 登录。BR-LGN-004 每次检查凭据状态，因此所有引用该 credentialId 的 Session 在随后检查中失败，无需在本命令内逐条更新 Session；撤销前已通过检查的在途请求和此前签发的短期 JWS 遵循各自既有边界。

允许撤销当前 Session 使用的凭据，也允许撤销同一账号的其它凭据。撤销当前凭据后，再用原 Session 重试返回 SESSION_INVALID；其它仍有效 Session 可重复撤销同一目标。本次成功响应可能是该 Session 最后一次授权成功的请求；响应丢失时结果可能未知，客户端不能假定回滚。撤销最后一条凭据也不被服务器阻止：Auth 不以邮箱、其它设备或学生关联推断可恢复性，恢复风险提示和本地私钥删除由客户端负责。

撤销凭据不删除 USER、资料、学生关联或其它凭据。物理清理由单独保留策略处理；即使客户端声称已经删除本地私钥，Auth 也不能把该声明当作服务端撤销证据。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-007`

<!-- 权威位置: use-cases/UC-AUTH-007-login.md#br-lgn-004 -->
### BR-LGN-004：有效期与在线检查

首版采用固定绝对有效期：T_session 通过 AUTH_SESSION_TTL 配置，为部署必填的正时长，创建时固定 expiresAt；缺失/非法配置拒绝接流量。配置采用 Go duration 格式，示例部署值为 `720h`（30 天）；该示例不是隐式默认值。本轮不自动滑动续期、不签发 refresh token，也不因请求活跃无限延长会话。到期后必须重新完成本用例的设备认证并建立新 Session，不延长旧会话的 expiresAt。后续若增加续期，另行设计轮换与并发语义。

一次成功会话检查必须得到一致、当前的事实：token 摘要匹配，Session 未撤销且 `now < expiresAt`，所属主体为 ACTIVE USER，作为会话认证依据的设备凭据仍有效且归属一致。缺失、损坏、超时或无法读取均失败关闭，不能回退到客户端缓存或只凭旧 JWT 放行。

首版不缓存正向会话授权结果，权威读取不得使用可能落后的副本。建议使用一致快照读取主体、凭据和 Session；检查与撤销/禁用存在并发时，以明确的检查快照为边界。变更提交后才开始的新检查必须看到变更；先已通过的请求可能继续执行，不承诺取消在途业务。

成功检查还须完成 [BR-LGN-010](../use-cases/UC-AUTH-007-login.md#br-lgn-010) 的使用时间更新；不能先返回检查成功，再异步记录使用时间。此更新不改变固定 expiresAt。

清理过期会话只是存储维护；即使记录未被删除也不能再通过检查。更改配置不追溯改变已有 expiresAt；紧急失效使用显式撤销，不通过重解释时间或静默换令牌完成。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### 范围与权威来源

本契约固定官方客户端、Auth Center 与未来 Gateway 接入共同使用的字节格式。业务规则由 [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md)、[UC-AUTH-007](../use-cases/UC-AUTH-007-login.md)、[UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md)、[UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 拥有；本文件不引入邮箱恢复、设备迁移或新的身份签发能力。

首版选择是 App 管理设备密钥。协议只证明私钥控制权，不声称验证官方客户端、学校身份、硬件等级或生物识别。签名中的 applicationId 用于隔离上下文，不是 App attestation。

#### 基础编码

- `UTF8(s)` 是字符串的 UTF-8 字节，不添加 BOM、终止符或隐式 Unicode 规范化。
- `LP(b) = U32BE(len(b)) || b`；长度为字节数，U32BE 是 4 字节无符号大端整数。`Frame(b1,...,bn)` 为依次连接各 LP，无额外分隔符或字段数量。每种消息固定字段数量，拒绝尾随数据、截断及超过上限的字段。
- `B64U(b)` 为 RFC 4648 URL-safe Base64，无 `=` 填充。解码必须严格并满足重新编码逐字相等，不接受空白、标准 Base64 的 `+`/`/` 或非零尾部填充位。
- 下述 Proto `bytes` 字段传原始字节；JSON 映射遵循 Proto 标准。文档向量的 hex 仅为测试展示，不能作为线上 bytes 字段的另一种编码。
- 新 operationId、credentialId、sessionId 使用小写标准连字符 UUIDv4；authId 沿用主体的 opaque 标识语义，不能由客户端指定或从学号派生。
- 时间采用 UTC Unix 毫秒；签名输入中为 8 字节无符号大端整数。服务端使用整数毫秒创建挑战并持久化，避免 Proto 与 MongoDB 精度转换改变签名。时间过期规则仍由 UC 拥有。

#### 公钥与签名

`protocolVersion = "iwut-device-v1"`，唯一支持的算法为 ECDSA P-256（secp256r1）配合 SHA-256。

公钥使用固定 65 字节未压缩 SEC1 / X9.63 点编码：`0x04 || X[32] || Y[32]`，坐标为无符号大端、保留左侧零字节。拒绝压缩点、PEM、SPKI、其它曲线、无穷点和不在 P-256 曲线上的坐标。Android 的 SPKI 公钥需要在客户端提取坐标转换，不能直接上传证书或 SubjectPublicKeyInfo。

规范公钥指纹为 32 字节：

```text
fingerprint = SHA256(Frame(UTF8("iwut-device-public-key-v1"), publicKey65))
```

`CredentialRegistrationProposal` 的具体字段为 `protocolVersion: string` 与 `publicKey: bytes`。两类 proof 均只有 `signature: bytes`；服务器从 operation 快照取得算法、公钥及待签消息，不接受 Complete 指定新算法、公钥或可信布尔值。

签名为对完整 signingPayload 做一次 SHA-256 后的 ECDSA，在线格式是严格 ASN.1 DER `SEQUENCE(INTEGER r, INTEGER s)`。要求最短 DER、无尾随字节、`1 <= r,s < curveOrder`，最多 72 字节。接受合法 high-S 和 low-S，不把签名字节当幂等键；一次性消费依据 operationId。Android 可使用 `SHA256withECDSA` 对原始 payload 签名；CryptoKit 使用对 Data 签名的 API 并导出 `derRepresentation`。调用会自行哈希的 API 时不得先手动哈希一次。

选型依据：[Apple SecureEnclave P-256 签名](https://developer.apple.com/documentation/cryptokit/secureenclave/p256/signing)、[Apple P256 公钥表示](https://developer.apple.com/documentation/cryptokit/p256/signing/publickey)、[Android KeyGenParameterSpec 的 P-256 / SHA256withECDSA 示例](https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec)。客户端优先使用系统密钥设施，不要求用户认证标志；具体设备不可用时明确报错或采用经客户端验证的系统安全存储方案，不把私钥写入普通业务存储。

#### 挑战与待签消息

注册和登录的挑战响应都增加 `signingPayload: bytes`。服务器保存结构化不可变快照，返回下式的准确字节，Complete 必须从快照重建并验证。客户端签名前严格解析 payload，核对协议、purpose、operationId、challenge、expiresAt、本地预期 serviceId/applicationId，以及自己刚提交的定位与关联摘要；不能把它当作签署任意服务端字节的通用 API。

REGISTER 的 signingPayload 和无密钥 associationDigest 仅在请求内存中生成，不单独持久化、不进入日志；operation 只按 BR-REG-008 保存 lookupKey 与 token 的认证加密密文。Complete 验证解密 token 后重建摘要与 payload，避免明文摘要绕过关联信息的数据库保护。

```text
signingPayload = Frame(
  UTF8("iwut-device-proof-v1"), UTF8(protocolVersion), UTF8(purpose),
  UTF8(serviceId), UTF8(applicationId), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs),
  UTF8(locatorKind), locatorValue, associationDigest
)
```

- `purpose` 精确为 `REGISTER` 或 `LOGIN`；challenge 为 CSPRNG 生成的 32 字节，寿命固定 5 分钟，过期不加客户端时钟容差。
- `serviceId` 为服务端部署必填的 `AUTH_AUTHENTICATION_SERVICE_ID`，1–128 个 ASCII 字符，允许字母、数字、`.`、`_`、`:`、`-`。示例 `iwut-auth-center:prod` 与 `iwut-auth-center:test` 必须不同。官方客户端为其目标环境预配置相同值，不能只相信响应。首版 applicationId 固定为 `iwut-client`；不提供动态选择应用参数。
- REGISTER 的 locatorKind 固定 `PUBLIC_KEY_FINGERPRINT`，locatorValue 为新公钥的指纹；associationDigest 为 `SHA256(Frame(UTF8(schemeVersion), associationToken32))`。
- LOGIN 的 locatorKind 为 `CREDENTIAL_ID` 或 `PUBLIC_KEY_FINGERPRINT`，locatorValue 分别为提交的 UUID 文本 UTF-8 或原始 32 字节指纹；associationDigest 为空字节串。BeginDeviceLogin 使用 oneof，必须恰好一个定位值。
- 登录的 payload 保留请求定位方式，不将指纹静默转换为 credentialId。对于未知、禁用、已撤销凭据，Begin 仍返回同形状的 v1 挑战，不返回 authId、credentialId、账号状态或恢复方式；Complete 统一认证失败。依赖故障与限流可以分别返回不可用和限流错误。
- LOGIN 操作保存 Begin 时的内部凭据解析结果；当时不可接受的目标在本操作中始终不可接受。后来注册同公钥或重新启用账号不会让这个旧挑战变成有效登录操作；需重新 Begin。Begin 时有效也不免除 Complete 的当前状态复核。
- 客户端签名输入上限 1024 字节。未知版本、枚举变体、字段错位及额外字段均拒绝；不协商降级到其它算法。
- 成功设备登录结果补充 `credentialId`，使注册响应丢失后通过指纹登录的客户端能恢复非秘密定位信息。它来自成功认证后的服务端凭据，不能成为客户端选择 authId 的输入。

#### 学号关联声明

`schemeVersion = "iwut-student-association-v1"`。首版只有武汉理工大学，没有学校 namespace 或学校选择参数。

客户端先去掉输入两端的 ASCII SP、HT、CR、LF，再要求 1–64 个 ASCII 数字 `0`–`9`。内部空白、全角数字、符号、空串或超长均拒绝；不转整数、不去前导零、不按本科/研究生长度分流。64 是输入容量限制，不表示对学校学号规则的权威验证。

```text
associationToken32 = SHA256(Frame(UTF8(schemeVersion), UTF8(normalizedStudentNumber)))
```

版本字符串兼作用途前缀，是公开常量，不称为秘密盐。Auth 只接受该版本和恰好 32 字节 token；不能在服务器用学校接口或原始学号校验内容。真实性、明确提交和配额边界引用 BR-REG-004/005。

服务端加密、查找和密钥轮换的精确编码由 [BR-REG-008](../use-cases/UC-AUTH-006-create-user.md#br-reg-008) 定义，客户端不参与这些密钥或内部存储格式。

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

#### RPC 鉴权表

Auth 原生 gRPC 新接口固定为以下 full method；可执行 Proto 在独立 API 仓库。middleware 按精确方法表分派，未知方法默认拒绝，不能把整个 package 标成匿名。

| full method | 认证与授权 |
| --- | --- |
| `/auth_center.v1.authentication.AuthenticationService/BeginUserRegistration` | 有界匿名；校验输入与容量，创建 REGISTER 挑战。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteUserRegistration` | 有界匿名；仅挑战与私钥证明可完成注册。 |
| `/auth_center.v1.authentication.AuthenticationService/BeginDeviceLogin` | 有界匿名；创建 LOGIN 挑战。 |
| `/auth_center.v1.authentication.AuthenticationService/CompleteDeviceLogin` | 有界匿名；仅挑战与私钥证明可建立 Session。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeCurrentSession` | 仅 token 定向撤销；必须绕过普通“当前 Session 有效”前置检查，按 UC008 幂等处理。 |
| `/auth_center.v1.authentication.AuthenticationService/RevokeOwnCredential` | 有效 Session，ACTIVE USER；以可信 authId 检查目标凭据归属，执行 UC009。 |
| `/auth_center.v1.user_profile.UserProfileService/EditOwnProfile` | trusted-identity-v1 用户 JWS，audience 为 `iwut-auth-center`；按 UC005 再查当前主体。 |
| `/auth_center.v1.user_profile.UserProfileService/GetOwnProfile` | 同上。 |
| `/auth_center.v1.user_profile.UserProfileService/GetProfileEditingSchema` | 同上。 |
| 既有 Scope/Developer/SystemPrincipal 方法 | 保持 trusted-service-identity-v1 与各自固定 permission/purpose allowlist。 |

同一调用只依据该方法规定的认证类型授权，不接受其它类型替代。会话撤销请求不因携带一个失效用户 JWS 而失去幂等性；匿名证明接口也不因附带身份获得额外权限。所有认证材料均需脱敏。客户端请求中声明的 authId、角色、设备名称或 applicationId 不生成可信 context。

UC009 撤销当前认证凭据后，再用原 Session 重试会得到 SESSION_INVALID；“幂等撤销已撤销凭据成功”以前置有效 Session 为限。其它仍有效 Session 可重复撤销同一目标。认证检查成功后的在途撤销请求按 UC007 的检查时间边界处理。

#### 实现配置与验收边界

Session 寿命、认证限额、MongoDB 并发实现与保留策略由 [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) 拥有；本契约只固定相互通信所需的格式和认证方法。并行工作包共用同一套端口和持久化约定。

本轮后端验收包括真实协议验证器、正反测试向量、生成 Proto、原生 gRPC、生产组合根与真实 Mongo 副本集上的事务/撤销测试。Android/iOS 私钥安全存储、客户端界面与恢复体验由客户端独立验收；Gateway 路由、在线 Session 到身份 JWS 签发仍为后续工作。不得用测试签名密钥或 fake verifier 代替生产认证，不把后端测试通过描述为移动端及公网调用已贯通。

#### 测试向量

确定性编码、关联 token、公钥指纹、REGISTER/LOGIN 签名验证、Session 摘要和关联认证加密样例见 [auth-device-session-v1.json](../../platform/contracts/test-vectors/auth-device-session-v1.json)。签名可以使用随机 nonce，因此验签结果固定，不要求生产端每次产生与样例相同的 DER 字节。负例必须覆盖错误 purpose/serviceId/locator、双重哈希、错误 DER、公钥编码、token 别名和前导零丢失。

生成与验证脚本位于 [tools/auth_protocol_vectors.py](../../tools/auth_protocol_vectors.py)。脚本中的私钥和服务端密钥是公开测试数据，只能用于向量；不得作为生产默认配置。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-009`（use-cases/UC-AUTH-009-revoke-own-credential.md）：变更记录
- `UC-AUTH-007`（use-cases/UC-AUTH-007-login.md）：目标与范围、参与者与前置条件、输入与输出、主流程、Session 持久化结构、错误语义、测试与验收、交付依赖与后续用例、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-009-revoke-own-credential.md` | 81 | `d415b7913dd8` |
| `use-cases/UC-AUTH-007-login.md` | 250 | `c38e3a56e232` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
