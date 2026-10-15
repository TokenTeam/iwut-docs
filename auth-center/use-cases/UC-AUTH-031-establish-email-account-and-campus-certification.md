# UC-AUTH-031：建立邮箱账号与校园成员认证

状态：`ACCEPTED`

2026-10-13：用户审核并接受邮箱账号 v3 契约，授权本 UC 修订开始实现；密码初始化、目录/角色版本、校园当前依据和旧入口退役按 [v3 契约](../../platform/contracts/auth-email-account-v3.md)交付。下文此前待审核/单邮箱 v2 工程描述保留为历史基线，不作为新实现输入；新契约与本段优先。已完成依赖检查，公开启用仍需完整链路验收。

## 目标与范围

邮箱列表/唯一登录角色和密码注册由修订中的 UC006/011 拥有；本 UC 定义以当前已验证学校邮箱绑定为依据的校园成员认证及授权披露，不另定义账号创建/密码接口。

账号当前至少绑定一个 Auth 已验证的精确 `@whut.edu.cn` 地址时，具备 WHUT 校园成员认证；普通邮箱可注册并另加学校邮箱。无需定期重新验证，但删除最后一个学校依据会失去认证，已取得过认证不等于永久保留。认证不证明在校学生、学籍、年级或用户资料真实性。

认证事实可以在用户同意后披露给应用，作为应用赠送一次性权益的依据。Auth 不保存或扣减应用权益余额，不决定赠送次数，不替第三方发放权益。应用次数仅见非权威的[开发者参考](../design-notes/email-first-campus-entitlements.md)。

2026-10-12 此前永久独立认证基线曾由用户审核 ACCEPTED 并完成后端；用户随后确认邮箱列表与解绑撤回的新方向，本次实质修订为 DRAFT，须重新闭合协议/依赖、审核后接受。旧接口和 HMAC/存储在下文只记录已交付基线；新绑定依据与撤回尚未实现，不生成已经开工的假象。

## 参与者与依赖检查

- 注册者明确创建账号、验证邮箱并设置平台密码；邮箱登录失败不自动转注册。
- 已登录 ACTIVE USER 可添加已验证学校邮箱作非登录绑定；登录角色切换另按 UC011 要求密码，普通添加不替换角色。
- Auth 拥有稳定 authId、邮箱验证、校园认证、Session 与 OAuth 授权。
- 第三方应用通过当前有效 access token 读取 UserInfo，按 Application 范围内的 pairwise sub 识别账号；权益记录由应用持有。

当前 HEAD/工作树检查：UC011 已有真实邮件、REGISTER/BIND、持久化限额与原子创建；UC012 已有邮箱登录和设备登记；UC014–018 已有 consent、scope 交集和 UserInfo。可以复用这些设施。

当前代码缺口：旧 v2/关联退役、独立校园认证、USERINFO_CAMPUS 披露已交付，不再是缺口。当前没有平台密码/多绑定邮箱，校园认证仍是独立 authId/institution/certifiedAt 事实，没有绑定依据与解绑撤回；这些才是本次新增交付项。App 创建额度仍按 authId，具体次数权益不由 Auth 管理。

保留设备签名用于自动登录/设备证明，同时新增平台密码要求；UC025/026 等危险动作是否再加密码须验证矩阵另行审核，不把后台签名默认视为密码替代。没有标准 WebAuthn；学号声明退役不删除 UC005 可选一卡通号。

## 输入与输出

注册/绑定和登录角色输入引用 UC006/011；邮箱 v2 是已交付的无密码基线，不是新注册完整协议。当前认证查询/披露须引用当前有效学校绑定，不在本 UC 建第二套邮箱目录。

以下 `auth_center.v1.campus_certification/CampusCertificationService` 是已交付独立认证 API。新增模型中它与 UC011 添加邮箱如何统一、是否保留验证别名以及 certifiedAt 的时间含义待审核；不能完成独立永久事实后漏掉邮箱绑定，或用 CAMPUS_ALREADY_CERTIFIED 阻止添加第二个学校依据：

| 方法 | service-local HTTP | 身份 |
| --- | --- | --- |
| BeginOwnCampusCertification | POST `/v1/users/me/campus-certification/verifications` | DIRECT，当前有效 Session |
| CompleteOwnCampusCertification | POST `/v1/users/me/campus-certification/verifications/{operation_id}/completion` | DIRECT，同 authId 当前有效 Session |
| GetOwnCampusCertification | GET `/v1/users/me/campus-certification` | DIRECT，当前有效 Session |

```text
BeginOwnCampusCertification { requestId, email }
CampusVerificationStarted { operationId, targetEmail, expiresAt, resendAfter }
CompleteOwnCampusCertification { operationId, code }
OwnCampusCertification { institution: "WHUT", certified: Bool, certifiedAt: Instant? }
```

所有主体来自 Session；输入不接受 authId、学生状态、校园认证结果、次数或消费记录。规范化地址沿用 UC011，不支持通配域名或任意学校配置；首版只接受精确 `whut.edu.cn`，不接受 `other.whut.edu.cn`、`whut.edu.cn.evil.test`。

独立 OAuth scope 固定为 `campus.whut`，内部 kind 为 `USERINFO_CAMPUS`、audience 为空；经 App Version 声明、审核和用户 consent。当前有效集合包含它时，UserInfo 可以输出：

```json
{"sub":"<application-pairwise-sub>","iwut_campus":{"institution":"WHUT","certified":true}}
```

无认证时省略 `iwut_campus`。不披露校园邮箱、内部认证记录 ID、authId、邮箱防重标识或其它应用身份；不放进 ID Token、用户 profile 或 UC010 的管理权限集合。

## 主流程

1. 注册者明确邮箱注册、设置密码、验证邮件并完成后台设备证明。
2. UC006/011 同一事务建立 USER、密码材料、唯一登录邮箱及绑定、空资料、设备凭据/Session、操作消费和审计；不创建学校关联组。
3. 注册邮箱为精确学校域时，当前绑定成为校园依据，认证查询/披露同事务一致；普通邮箱不授予认证，不能用校园标志绕过登录邮箱归属。
4. 以后普通添加并验证学校邮箱增加认证依据，不改变登录角色；解绑在 UC011 最终提交中收敛依据及认证，只有最后一个被移除才撤回。
5. 邮箱登录只回到已存在且可登录的 authId。登录未找到、设备存储丢失或学校客户端登录失败均不自动创建新账号。
6. 应用获得校园认证披露同意后，通过有效 UserInfo 读取认证事实；应用在自己的事务内按自己的权益规则完成一次性领取及使用。

## 业务规则

<a id="br-cmp-001"></a>
### BR-CMP-001：邮箱账号与学校信息脱离

账号注册、关联退役和应用身份边界引用 UC006/BR-REG-001/004/005；校园认证绑定已有或同事务新建的 authId，不创建第二个主体、不合并账号，也不修改 profile、人员权限或 Developer 状态。

<a id="br-cmp-002"></a>
### BR-CMP-002：服务端邮件验证与当前绑定依据

校园认证依据仅来自 Auth 真实邮件验证后仍归属本 authId 的有效学校邮箱绑定。验证操作、绑定与 owner/代际一致，首次建立/移除与认证投影在同一事务确认；客户端 verified/profile/学号/截图或未经验证后缀均不能授予。绑定目录属于 UC011，不在校园组件单独复制邮箱归属。

验证期限、尝试次数/发送额度复用 UC011；验证码各用途隔离，不能拿登录/重置码绑定学校邮箱。注册学校邮箱或普通添加验证后可以建立校园依据，不需第二次无意义验证；如果保留独立校园验证 API，必须同事务落实真实绑定而不是仅存永久事实，最终用途/协议待审核。SMTP 不在事务重试中发送。

认证为当前有效学校绑定集合非空的结果，不设周期性复验；毕业/自填年级不改变绑定认证。学校邮箱可兼任登录角色，切换登录角色但仍保留绑定不撤回认证；移除最后一个学校绑定才撤回，仍有其他依据时保留。解绑前提示影响，但最终正确性由服务端事务保证。DISABLED/CLOSED 仍按账号 gate，认证不恢复账号或授予学生/管理/Developer 权限及 scope 同意。

<a id="br-cmp-003"></a>
### BR-CMP-003：账号认证与应用一次性领取分离

同一 authId 对 WHUT 只有一个当前认证结果，多个学校绑定不累积多份资格。解绑后重新绑定可以恢复认证，但不生成新的账号或应用活动领取身份；认证不需定期复验与应用按账号/活动一次赠送是两回事，不能用重新认证时间重置领取记录。

本 UC 不建跨账号校园邮箱已消费库。地址当前归属/可绑定性引用 UC011；2026-10-13 用户确认所有已验证邮箱跨账号全局唯一、每账号最多 10 个地址。不能用校园验证转移他人邮箱/账号或找回原账号。非登录学校邮箱不能授权登录/密码重置，当前登录学校邮箱的恢复权限来自登录角色而不是校园认证。

学校别名无法由 Auth 可靠归并，不剥离点号、加号或根据校园卡号猜测等价关系；不承诺每自然人、每校园邮箱只能领取一次。注销后重新注册产生新 authId 和新的应用 sub，按账号一次的活动可能再次符合条件；若某应用要求跨账号防重复领取，需要单独明确风险规则与最小可信依据，不能从认证事实推断已经满足。

<a id="br-cmp-004"></a>
### BR-CMP-004：披露授权与权益职责

campus.whut 按 UC014–018 当前 token/grant/Version/Catalog 交集授权，并在线确认账号/应用资格和当前有效学校依据。移除最后依据提交后的新 UserInfo 不再返回 iwut_campus；不得读独立旧永久缓存继续宣称认证。坏绑定/必要依赖故障失败关闭，无有效 scope 不读取认证。撤权/应用关闭/账号 gate 继续生效。

认证事实独立于 UserProfile，不通过 USERINFO_PROFILE 映射；scope 不隐含 email 或任何资料 scope。校园邮件后缀、客户端 claim 和 ApplicationUserStorage KV 不能替代受信 UserInfo。

Auth 不生成次数余额、权益活动或消费 API。领取与扣次方案由应用自行决定，参考方案不是 Auth 强制协议；不同应用独立。OAuth 重授权、客户端切换和 Version 升级不替应用重置领取记录。

<a id="br-cmp-005"></a>
### BR-CMP-005：并发、审计与注销清理

邮箱绑定是认证依据的权威来源；是否维护带绑定版本的认证投影及 certifiedAt 含义须在存储契约闭合，不能单独保存无依据永久 true。添加/解绑、唯一登录角色保护、认证投影与审计共用认证事务栅栏，和 UserInfo 有明确检查顺序；并发两个学校依据解绑不能留下幽灵认证，结果未知查询恢复，不假成功或发权益。

账号注销按 UC025 清除全部邮箱绑定/登录角色、校园依据/投影、验证地址/挑战与个人可读数据，CLOSED 不披露认证。校园组件不额外保存第二套邮箱，最小投影也不得在解绑/恢复后脱离当前绑定。清理/终止清单和备份恢复须补新字段/集合；不为应用保留永久邮箱指纹或消费历史，应用账本自管。

日志、trace、metrics 和业务审计不记录邮箱验证码、Session、邮件正文、完整签名或关联声明；UserInfo 不披露防重标识。

## 验收场景

1. 邮箱/设备证明及密码设置完成后建立正式账号；注册学校邮箱同事务建立依据，无学号声明也可注册。
2. 无邮箱创建路径不可用；邮箱登录失败不会转注册；旧协议、旧 association 字段与旧注册签名明确拒绝。
3. 普通账号独立认证校园邮箱后，登录邮箱、authId、pairwise sub 和业务数据不变。
4. 验证仅接受精确域名；伪造认证标志、错误/过期验证码、错误用途、其他账号和失效 Session 失败关闭。
5. 多个学校绑定维持单一结果；只换登录角色不撤回，删最后学校依据则本人查询/UserInfo 撤回；并发添加/解绑、重新绑定不改变 authId/sub 或重置应用领取记录。注销新账号不承诺跨账号防重复。
6. 校园认证与账号禁用/关闭并发具备明确提交顺序；审计失败回滚，未知提交可查询恢复。
7. OAuth 只在有效校园 scope 下返回最小事实，坏认证记录或必要依赖故障整次拒绝；无 scope 不依赖认证读取。
8. App 声明/审核、两类 client consent、三渠道/current grant、关闭和撤权通过真实 Auth/App/OIDC 联合验收。
9. 原有后台设备登录、邮箱恢复、注销高风险证明、资料与 KV 回归保持通过；不把设备凭据保留误称为用户须主动管理 Passkey。
10. Auth 不提供领取次数或扣减余额；应用自己的重领、并发扣减及业务失败恢复另行验收。

## 实现约定与依赖闭合

以下子节只记录已经交付的“独立永久事实”基线，不是本次修订实现契约。新模型需闭合 UC011 邮箱绑定目录、来源/版本、最后依据撤回、查询时间含义、旧验证 API 防旁路及 UC025 清单；旧 CAMPUS_ALREADY_CERTIFIED、三字段永久文档和无绑定缓存不能直接沿用。禁止为未部署系统凭空新增生产历史迁移，也不删除旧公开向量来冒充新模型完成。

2026-10-13 新增[邮箱账号 v3 契约](../../platform/contracts/auth-email-account-v3.md)审核提案：认证直接读取当前绑定；certifiedAt 为当前 WHUT 依据中最早 verifiedAt；原校园验证入口成为目录 ADD 的别名；旧永久集合不继续授权。此部分仍待审核，不按历史 ACCEPTED 自动实施。

### API、载体与错误

独立 API 为 `auth_center/v1/campus_certification/`，package `auth_center.v1.campus_certification`、service `CampusCertificationService`。三种 request 和 response 固定字段：

| 消息 | 字段号与类型 |
| --- | --- |
| BeginOwnCampusCertificationRequest | 1 string request_id；2 string email |
| CampusVerificationStarted | 1 string operation_id；2 string target_email；3 int64 expires_at_unix_ms；4 int64 resend_after_unix_ms |
| CompleteOwnCampusCertificationRequest | 1 string operation_id；2 string code |
| GetOwnCampusCertificationRequest | 空 |
| OwnCampusCertification | 1 string institution；2 bool certified；3 optional int64 certified_at_unix_ms |

时间使用 UTC Unix 毫秒，ProtoJSON int64 为 string；requestId/operationId 为小写规范 UUIDv4。certified=false 时不提供 certifiedAt；true 必须有合法认证时间。缺记录与损坏记录区分，损坏/依赖故障不能当作未认证。

上述三方法均按精确 full method 校验唯一 `x-iwut-session`，ACTIVE USER，DIRECT 不接受用户 JWS 替代。Begin POST body `*`；Complete 的 operationId 来自路径覆盖体；Get 无 body。使用既有严格 JSON/16 KiB/no-query/no-store、大小与未知字段拒绝规则，不开放 wildcard。

| 原因 | reason | HTTP/gRPC |
| --- | --- | --- |
| 请求超过 16 KiB | CAMPUS_CERTIFICATION_REQUEST_TOO_LARGE | 413/RESOURCE_EXHAUSTED |
| 地址/ID/code/请求非法 | INVALID_CAMPUS_CERTIFICATION_REQUEST | 400/INVALID_ARGUMENT |
| 缺失/坏/失效 Session | SESSION_INVALID | 401/UNAUTHENTICATED |
| 错误、过期、被替代、耗尽或其他账号操作 | CAMPUS_VERIFICATION_FAILED | 400/INVALID_ARGUMENT |
| 同 requestId 不同输入 | CAMPUS_REQUEST_CONFLICT | 409/ALREADY_EXISTS |
| Begin 时已经认证 | CAMPUS_ALREADY_CERTIFIED | 409/ALREADY_EXISTS |
| 发送/操作额度耗尽 | CAMPUS_RATE_LIMITED | 429/RESOURCE_EXHAUSTED |
| 投递失败/未知 | EMAIL_DELIVERY_UNAVAILABLE | 503/UNAVAILABLE |
| 存储/必要依赖/提交未知 | CAMPUS_CERTIFICATION_UNAVAILABLE | 503/UNAVAILABLE |

已认证 Begin 不再发邮件；客户端通过 Get 恢复事实。Complete 的已完成操作仅在当前账号有效、原 code 正确且保留窗口内返回原事实；不新增认证或更新认证时间。

### 操作、密钥与邮件额度

独立 purpose 固定 `CERTIFY_CAMPUS_WHUT`，不要求额外设备签名；有效 Session 与服务端邮箱码共同授权。验证码、期限、失败次数与邮件额度沿用 UC011：8 ASCII 数字、10 分钟、5 次失败，60 秒重发冷却、账号/地址各 5 次每小时、来源 20 次每小时。沿用相同全局/地址/来源 quota 集合与键，不能切换注册、绑定、登录、校园验证翻倍额度；账号计数也与 BIND 同一 authId 桶。一般请求/未完成操作容量继续有界。

Begin 幂等为 `(authId, requestId)`，24 小时；相同邮箱/账号代际返回同操作且不重发，同键异参拒绝。本人查询也通过一般有界读取限流；每账号最多一个有效校园提案；新 requestId 的成功 Begin 作废旧提案，不延长旧码。验证码失败计数、提案替代、完成与认证在共享认证事务栅栏中处理。

独立 `AUTH_CAMPUS_CERTIFICATION_CODE_KEY` 为严格标准 Base64 的独立随机 32 字节密钥，不能与邮箱绑定/登录 HMAC 共用。Frame 基础编码引用设备协议；定义：

```text
requestMac = HMAC-SHA256(K_campus, Frame(
  UTF8("iwut-campus-request-v1"), UTF8(requestId), UTF8(authId),
  U64BE(accountRevision), UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client")))
codeMac = HMAC-SHA256(K_campus, Frame(
  UTF8("iwut-campus-code-v1"), UTF8("CERTIFY_CAMPUS_WHUT"), UTF8(operationId),
  U64BE(expiresAtUnixMs), requestMac, UTF8(code8)))
keyId = SHA256(Frame(UTF8("iwut-campus-key-id-v1"), K_campus))
```

只保存 HMAC，不保存明文码。冷换 keyId 关闭该 key 的未完成校园操作，同 requestId 保留至窗口结束，不用换钥绕过去重；无需保有旧 key，不影响永久事实。SMTP 复用已接受的 TLS 配置/适配器及用途模板，在事务确认后调用，失败仍扣发送额度；不对真实用户发测试邮件。

### 存储、初始化、注销与开关

`auth_campus_certifications` 仅保存 authId、institution=WHUT、certifiedAt，对 `(authId,institution)` 唯一；不保存认证邮箱、指纹或业务权益。注册邮箱符合精确域且验证码通过时，在 REGISTER 同事务插入该事实，时间取验证提交时间；不能仅凭待验证地址建立认证。

独立校园操作保存 operationId、authId、accountRevision、requestId、目的、规范化邮箱、keyId/MAC、期限、失败/消费状态和保留截止；operationId 与 authId/requestId 唯一，retention 辅助 TTL 不替代业务期限。必要 schema 在正常 USER 初始化时建立，保证校园邮箱注册即使专用 API 关闭也能记录事实；不在读取中修复或回填。

`AUTH_CAMPUS_CERTIFICATION_ENABLED` 默认 false，只控制三个独立验证/查询入口。true 时需 USER 入口与独立邮件 key/TLS/额度合法；关闭不取消注册同事务认证或已有事实，也不阻止已实现且 enabled 的 scope 授权披露。OAuth 没有校园 scope 时不读取认证存储；有 scope 时在同一当前 token/grant/账号/应用事务读取事实，必要故障整次拒绝。scope kind 只允许 campus.whut、空 audience、无 profileField/ProfileValueType；Discovery 增加 iwut_campus，scope 列表仍按实际 enabled。

UC025 清理认证事实、该 authId 的校园验证地址/MAC/操作及最小校园审计，遵守原有有界清理、180 天普通审计与终止清单恢复。清理不按已释放邮箱定位，不保留全局邮箱已消费库；注销后旧 token 不披露认证。校园认证依赖 USER gate，不授予人员权限或 Developer。

### 工作包与验收边界

邮箱 v2 精确字节与旧入口/字段退役已由 UC006/011 规定；公开向量/API/实现为本次交付项，不需要生产历史迁移。同步扩展 UC001 Catalog、UC017 UserInfo 及 OAuth 契约；App 继续消费不变的 name/requestable 并走现有声明/审核，Portal/Gateway/移动端分别交付，不宣称已上线。次数余额、领取或扣减不在 Auth/API 范围。

## 变更记录

- 2026-10-12：本次修订 DRAFT；以当前学校邮箱绑定集合代替永久独立事实，补最后依据解绑/重新绑定/OAuth 收敛与密码注册依赖，旧技术默认标为已交付基线。
- 2026-10-12：生成 brief 后完成 Auth/API 后端；邮箱 v2/关联退役、校园验证与注册同事务认证、OAuth 披露及注销清理通过全包真实 Mongo/race/Wire 回归。实现状态与公网投产边界见 implements/README.md，不涉及应用次数账本。

- 2026-10-12：依据用户确认的邮箱注册、永久校园成员认证、账号权益归属和取消学号上传方向建立待审核草案；用户澄清权益属于具体应用后，去掉未经确认的全局邮箱已消费限制。校园认证披露与注销清理仍需审核。未 ACCEPTED，未生成实施 brief，未实施。

- 2026-10-12：用户审核后 ACCEPTED；固定独立 API、用途/HMAC/共享额度、注册原子事实、当前 OAuth 披露与注销步骤。依赖检查可实现，生成 brief 后开始 Auth/API 后端交付。
