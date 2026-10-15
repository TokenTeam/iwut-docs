<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-031 --spec tools/brief-specs/UC-AUTH-031.json -->
# Brief — UC-AUTH-031：建立邮箱账号与校园成员认证

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-031` 建立邮箱账号与校园成员认证 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-CMP-001`–`BR-CMP-005`（5 条） |
| 外部引用 BR | `BR-REG-001`（来自 `UC-AUTH-006`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-device-session-v1.md`、`platform/contracts/auth-email-account-v3.md`、`platform/contracts/oauth-oidc-v1.md` |

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

邮箱列表/唯一登录角色和密码注册由修订中的 UC006/011 拥有；本 UC 定义以当前已验证学校邮箱绑定为依据的校园成员认证及授权披露，不另定义账号创建/密码接口。

账号当前至少绑定一个 Auth 已验证的精确 `@whut.edu.cn` 地址时，具备 WHUT 校园成员认证；普通邮箱可注册并另加学校邮箱。无需定期重新验证，但删除最后一个学校依据会失去认证，已取得过认证不等于永久保留。认证不证明在校学生、学籍、年级或用户资料真实性。

认证事实可以在用户同意后披露给应用，作为应用赠送一次性权益的依据。Auth 不保存或扣减应用权益余额，不决定赠送次数，不替第三方发放权益。应用次数仅见非权威的[开发者参考](../design-notes/email-first-campus-entitlements.md)。

2026-10-12 此前永久独立认证基线曾由用户审核 ACCEPTED 并完成后端；用户随后确认邮箱列表与解绑撤回的新方向，本次实质修订为 DRAFT，须重新闭合协议/依赖、审核后接受。旧接口和 HMAC/存储在下文只记录已交付基线；新绑定依据与撤回尚未实现，不生成已经开工的假象。

### 参与者与依赖检查

- 注册者明确创建账号、验证邮箱并设置平台密码；邮箱登录失败不自动转注册。
- 已登录 ACTIVE USER 可添加已验证学校邮箱作非登录绑定；登录角色切换另按 UC011 要求密码，普通添加不替换角色。
- Auth 拥有稳定 authId、邮箱验证、校园认证、Session 与 OAuth 授权。
- 第三方应用通过当前有效 access token 读取 UserInfo，按 Application 范围内的 pairwise sub 识别账号；权益记录由应用持有。

当前 HEAD/工作树检查：UC011 已有真实邮件、REGISTER/BIND、持久化限额与原子创建；UC012 已有邮箱登录和设备登记；UC014–018 已有 consent、scope 交集和 UserInfo。可以复用这些设施。

当前代码缺口：旧 v2/关联退役、独立校园认证、USERINFO_CAMPUS 披露已交付，不再是缺口。当前没有平台密码/多绑定邮箱，校园认证仍是独立 authId/institution/certifiedAt 事实，没有绑定依据与解绑撤回；这些才是本次新增交付项。App 创建额度仍按 authId，具体次数权益不由 Auth 管理。

保留设备签名用于自动登录/设备证明，同时新增平台密码要求；UC025/026 等危险动作是否再加密码须验证矩阵另行审核，不把后台签名默认视为密码替代。没有标准 WebAuthn；学号声明退役不删除 UC005 可选一卡通号。

### 输入与输出

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

### 主流程

1. 注册者明确邮箱注册、设置密码、验证邮件并完成后台设备证明。
2. UC006/011 同一事务建立 USER、密码材料、唯一登录邮箱及绑定、空资料、设备凭据/Session、操作消费和审计；不创建学校关联组。
3. 注册邮箱为精确学校域时，当前绑定成为校园依据，认证查询/披露同事务一致；普通邮箱不授予认证，不能用校园标志绕过登录邮箱归属。
4. 以后普通添加并验证学校邮箱增加认证依据，不改变登录角色；解绑在 UC011 最终提交中收敛依据及认证，只有最后一个被移除才撤回。
5. 邮箱登录只回到已存在且可登录的 authId。登录未找到、设备存储丢失或学校客户端登录失败均不自动创建新账号。
6. 应用获得校园认证披露同意后，通过有效 UserInfo 读取认证事实；应用在自己的事务内按自己的权益规则完成一次性领取及使用。

### 验收场景

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

### 实现约定与依赖闭合

以下子节只记录已经交付的“独立永久事实”基线，不是本次修订实现契约。新模型需闭合 UC011 邮箱绑定目录、来源/版本、最后依据撤回、查询时间含义、旧验证 API 防旁路及 UC025 清单；旧 CAMPUS_ALREADY_CERTIFIED、三字段永久文档和无绑定缓存不能直接沿用。禁止为未部署系统凭空新增生产历史迁移，也不删除旧公开向量来冒充新模型完成。

2026-10-13 新增[邮箱账号 v3 契约](../../platform/contracts/auth-email-account-v3.md)审核提案：认证直接读取当前绑定；certifiedAt 为当前 WHUT 依据中最早 verifiedAt；原校园验证入口成为目录 ADD 的别名；旧永久集合不继续授权。此部分仍待审核，不按历史 ACCEPTED 自动实施。

#### API、载体与错误

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

#### 操作、密钥与邮件额度

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

#### 存储、初始化、注销与开关

`auth_campus_certifications` 仅保存 authId、institution=WHUT、certifiedAt，对 `(authId,institution)` 唯一；不保存认证邮箱、指纹或业务权益。注册邮箱符合精确域且验证码通过时，在 REGISTER 同事务插入该事实，时间取验证提交时间；不能仅凭待验证地址建立认证。

独立校园操作保存 operationId、authId、accountRevision、requestId、目的、规范化邮箱、keyId/MAC、期限、失败/消费状态和保留截止；operationId 与 authId/requestId 唯一，retention 辅助 TTL 不替代业务期限。必要 schema 在正常 USER 初始化时建立，保证校园邮箱注册即使专用 API 关闭也能记录事实；不在读取中修复或回填。

`AUTH_CAMPUS_CERTIFICATION_ENABLED` 默认 false，只控制三个独立验证/查询入口。true 时需 USER 入口与独立邮件 key/TLS/额度合法；关闭不取消注册同事务认证或已有事实，也不阻止已实现且 enabled 的 scope 授权披露。OAuth 没有校园 scope 时不读取认证存储；有 scope 时在同一当前 token/grant/账号/应用事务读取事实，必要故障整次拒绝。scope kind 只允许 campus.whut、空 audience、无 profileField/ProfileValueType；Discovery 增加 iwut_campus，scope 列表仍按实际 enabled。

UC025 清理认证事实、该 authId 的校园验证地址/MAC/操作及最小校园审计，遵守原有有界清理、180 天普通审计与终止清单恢复。清理不按已释放邮箱定位，不保留全局邮箱已消费库；注销后旧 token 不披露认证。校园认证依赖 USER gate，不授予人员权限或 Developer。

#### 工作包与验收边界

邮箱 v2 精确字节与旧入口/字段退役已由 UC006/011 规定；公开向量/API/实现为本次交付项，不需要生产历史迁移。同步扩展 UC001 Catalog、UC017 UserInfo 及 OAuth 契约；App 继续消费不变的 name/requestable 并走现有声明/审核，Portal/Gateway/移动端分别交付，不宣称已上线。次数余额、领取或扣减不在 Auth/API 范围。

## 业务规则（UC-AUTH-031 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-001 -->
### BR-CMP-001：邮箱账号与学校信息脱离

账号注册、关联退役和应用身份边界引用 UC006/BR-REG-001/004/005；校园认证绑定已有或同事务新建的 authId，不创建第二个主体、不合并账号，也不修改 profile、人员权限或 Developer 状态。

<!-- 权威位置: use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-002 -->
### BR-CMP-002：服务端邮件验证与当前绑定依据

校园认证依据仅来自 Auth 真实邮件验证后仍归属本 authId 的有效学校邮箱绑定。验证操作、绑定与 owner/代际一致，首次建立/移除与认证投影在同一事务确认；客户端 verified/profile/学号/截图或未经验证后缀均不能授予。绑定目录属于 UC011，不在校园组件单独复制邮箱归属。

验证期限、尝试次数/发送额度复用 UC011；验证码各用途隔离，不能拿登录/重置码绑定学校邮箱。注册学校邮箱或普通添加验证后可以建立校园依据，不需第二次无意义验证；如果保留独立校园验证 API，必须同事务落实真实绑定而不是仅存永久事实，最终用途/协议待审核。SMTP 不在事务重试中发送。

认证为当前有效学校绑定集合非空的结果，不设周期性复验；毕业/自填年级不改变绑定认证。学校邮箱可兼任登录角色，切换登录角色但仍保留绑定不撤回认证；移除最后一个学校绑定才撤回，仍有其他依据时保留。解绑前提示影响，但最终正确性由服务端事务保证。DISABLED/CLOSED 仍按账号 gate，认证不恢复账号或授予学生/管理/Developer 权限及 scope 同意。

<!-- 权威位置: use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-003 -->
### BR-CMP-003：账号认证与应用一次性领取分离

同一 authId 对 WHUT 只有一个当前认证结果，多个学校绑定不累积多份资格。解绑后重新绑定可以恢复认证，但不生成新的账号或应用活动领取身份；认证不需定期复验与应用按账号/活动一次赠送是两回事，不能用重新认证时间重置领取记录。

本 UC 不建跨账号校园邮箱已消费库。地址当前归属/可绑定性引用 UC011；2026-10-13 用户确认所有已验证邮箱跨账号全局唯一、每账号最多 10 个地址。不能用校园验证转移他人邮箱/账号或找回原账号。非登录学校邮箱不能授权登录/密码重置，当前登录学校邮箱的恢复权限来自登录角色而不是校园认证。

学校别名无法由 Auth 可靠归并，不剥离点号、加号或根据校园卡号猜测等价关系；不承诺每自然人、每校园邮箱只能领取一次。注销后重新注册产生新 authId 和新的应用 sub，按账号一次的活动可能再次符合条件；若某应用要求跨账号防重复领取，需要单独明确风险规则与最小可信依据，不能从认证事实推断已经满足。

<!-- 权威位置: use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-004 -->
### BR-CMP-004：披露授权与权益职责

campus.whut 按 UC014–018 当前 token/grant/Version/Catalog 交集授权，并在线确认账号/应用资格和当前有效学校依据。移除最后依据提交后的新 UserInfo 不再返回 iwut_campus；不得读独立旧永久缓存继续宣称认证。坏绑定/必要依赖故障失败关闭，无有效 scope 不读取认证。撤权/应用关闭/账号 gate 继续生效。

认证事实独立于 UserProfile，不通过 USERINFO_PROFILE 映射；scope 不隐含 email 或任何资料 scope。校园邮件后缀、客户端 claim 和 ApplicationUserStorage KV 不能替代受信 UserInfo。

Auth 不生成次数余额、权益活动或消费 API。领取与扣次方案由应用自行决定，参考方案不是 Auth 强制协议；不同应用独立。OAuth 重授权、客户端切换和 Version 升级不替应用重置领取记录。

<!-- 权威位置: use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md#br-cmp-005 -->
### BR-CMP-005：并发、审计与注销清理

邮箱绑定是认证依据的权威来源；是否维护带绑定版本的认证投影及 certifiedAt 含义须在存储契约闭合，不能单独保存无依据永久 true。添加/解绑、唯一登录角色保护、认证投影与审计共用认证事务栅栏，和 UserInfo 有明确检查顺序；并发两个学校依据解绑不能留下幽灵认证，结果未知查询恢复，不假成功或发权益。

账号注销按 UC025 清除全部邮箱绑定/登录角色、校园依据/投影、验证地址/挑战与个人可读数据，CLOSED 不披露认证。校园组件不额外保存第二套邮箱，最小投影也不得在解绑/恢复后脱离当前绑定。清理/终止清单和备份恢复须补新字段/集合；不为应用保留永久邮箱指纹或消费历史，应用账本自管。

日志、trace、metrics 和业务审计不记录邮箱验证码、Session、邮件正文、完整签名或关联声明；UserInfo 不披露防重标识。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-006`

<!-- 权威位置: use-cases/UC-AUTH-006-create-user.md#br-reg-001 -->
### BR-REG-001：显式创建与平台账号独立

authId 为服务端生成的稳定 opaque 标识，引用 [UC002 数据模型](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#数据模型)；不由邮箱、学号或设备标识派生。注册与登录是明确分开的意图；注册占用邮箱冲突不自动登录旧账号，登录失败不自动注册。

新账号必须通过 UC011 邮箱验证并设置有效平台密码，不提供无邮箱/无密码创建旁路。切换登录邮箱不改变 authId、不重新创建账号；非登录邮箱不能用来找回或登录账号。UC012 的已交付验证码登录基线与未来邮箱＋密码登录的范围仍须明确，不能因为设置密码就悄悄改写普通设备登录证明。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### JSON 与载体

- POST/PUT/PATCH 使用 `Content-Type: application/json`，消息遵循标准 ProtoJSON；`bytes` 为 Base64，
  `int64` 响应为十进制字符串，Timestamp 为 RFC3339；JSON 字段推荐 lowerCamelCase。
- 审核与应用运维权限管理的 subject_auth_id 由路径绑定，写方法还绑定 permission，覆盖消息体中同名值。旧 reviewer 方法不接受新增 permission 字段；各自 allowlist 和错误规则见 UC004 与 UC027。学年时间表 PUT 只接受 nextRolloverAt、expectedRevision 和 reason，不接受客户端提交 currentAcademicYear。
- 设备登录的 Complete 消息体仅需 `proof`；`operation_id` 由路径绑定，覆盖消息体中同名值。
  邮箱 Complete 消息体为 code 和条件必需的 registrationProof，路径 operation_id 同样覆盖体中值。
  凭据撤销的 `credential_id` 和应用存储清除的 `application_id` 仅来自路径。GET/DELETE 不带请求体。
- 资料编辑保留消息体中的 `expectedRevision` 和显式 ProfileValue oneof，不引入另一套
  原始 KV 或 `If-Match` 协议。具体字段值类型仍按 UC005 校验。
- 不接受 query 参数作为消息、Session 或身份来源。Session、可信用户身份载体完全遵守
  [设备认证契约](../../platform/contracts/auth-device-session-v1.md#session-载体) 与 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。
- JSON 解码拒绝未知字段、重复字段和冲突的 oneof 分支；资料编辑还拒绝 null 操作列表、条目及值分支，
  保留 UC005 的显式编辑规则。不把解析器的原始输入内容返回给客户端。
- HTTP 请求体在分配前有界读取：认证入口默认 16 KiB（由部署配置），资料编辑 128 KiB，应用用户存储固定 16 KiB。
  业务容量限制另行生效；暂不支持压缩请求体，返回 415。非 JSON POST/PUT/PATCH 同样返回 415。
- 所有响应设置 `Cache-Control: no-store`；撤销成功响应为 `{}`。错误 reason 复用 gRPC，
  HTTP 状态遵守各 UC：大小超限 413、限流 429、版本冲突/耗尽 409。
- 限流来源使用连接的 socket peer；不信任客户端的 Forwarded / X-Forwarded-For。
  经过 Gateway 时按代理来源计算，部署需按聚合流量设置限额。

#### 部署开关与验收

生产 Wire 同时启动 HTTP 和 gRPC Server；默认地址分别为 `:8000`、`:9000`，
通过 `AUTH_CENTER_HTTP_ADDR`、`AUTH_CENTER_GRPC_ADDR` 配置。
`AUTH_USER_ENDPOINTS_ENABLED=false` 时不注册上述 HTTP 用户路由，与 gRPC 开关一致。
TLS 与公网可达性由部署和 Gateway 决定，监听 HTTP 不代表公网入口已经交付。

验收使用生产 Wire、真实 HTTP/gRPC listener 和 MongoDB 副本集，覆盖修订后的资料/认证方法及退役无邮箱路径拒绝、Reviewer/应用运维权限方法、两个学年时间表管理方法及应用用户存储 HTTP/本人清除方法、
生成客户端、当前用户隔离、重复/替代身份头拒绝、严格 JSON、资料 CAS、撤销幂等性及内部 RPC
不暴露为 HTTP。保留原生 gRPC 回归测试。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

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

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。UC020 独立入口的缺失/畸形或混用载体为 INVALID_SESSION_TOKEN（400），载体合法但当前资格失效为 SESSION_INVALID（401），不得沿用 UC008 的免有效性检查。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 新注册/目录使用 [已接受的邮箱账号 v3](../../platform/contracts/auth-email-account-v3.md) 的精确载体；旧可选 Session REGISTER/BIND 已退役，其它接口的必需载体不变。

### `platform/contracts/auth-email-account-v3.md`：邮箱账号、密码注册与登录角色协议 v3 草案

#### 范围与审核边界

UC006/011 拥有注册及邮箱集合规则，UC031 拥有当前校园依据，UC033 拥有密码策略/安全验证。本契约补齐原草案未固定的接口、集合版本及注册字节，2026-10-13 新增并经用户明确审核接受，授权 UC006/011/031 修订生成 brief 后实现；公开启用仍须完整验收。

用户已明确确认：最多 10 个已验证地址、所有地址跨账号全局唯一；切换唯一登录邮箱不清退现有设备/Session，但旧邮箱登录/恢复操作失效。本文不重新讨论这些规则。没有旧账号生产迁移；现有开发数据库不自动删除、补密码或补版本。

#### 精确入口与载体

新 package `auth_center.v3.email_account`，service `EmailAccountService`。每个 exact full method 单独登记，不用匿名 wildcard。

| RPC | service-local HTTP | 身份 |
| --- | --- | --- |
| BeginEmailRegistration | POST `/v3/email-registrations` | Session 键不存在 |
| CompleteEmailRegistration | POST `/v3/email-registrations:complete` | Session 键不存在 |
| GetOwnEmails | GET `/v3/users/me/emails` | 当前有效 Session、no-touch |
| BeginAddOwnEmail | POST `/v3/users/me/email-verifications` | 当前有效 Session、no-touch |
| CompleteAddOwnEmail | POST `/v3/users/me/email-verifications:complete` | 同 authId 当前有效 Session、no-touch |
| SwitchOwnLoginEmail | POST `/v3/users/me/login-email:switch` | 当前有效 Session＋当前密码、no-touch |
| RemoveOwnEmail | POST `/v3/users/me/emails:remove` | 当前有效 Session、no-touch |

复用唯一 `x-iwut-session` 载体；无效/空 token 不匿名降级。所有正文严格 ProtoJSON、lowerCamelCase、bytes 标准 Base64、int64 JSON string，16 KiB、无 query/重复/未知/null 字段、no-store。用户名、owner、校园属性、版本和提交时间不能由客户端指定。密码只在 TLS Complete/Switch 正文出现，不进挑战/签名/日志。

#### 消息字段提案

字段号从 1 起，不复用旧 REGISTER/BIND 消息；所有非 optional 请求字段必需且非空。注册 proof/proposal presence 必需；密码生命周期规则不在本契约另定义。

| 消息 | 字段号/类型 |
| --- | --- |
| BeginEmailRegistrationRequest | 1 string request_id；2 string email；3 v1.authentication.CredentialRegistrationProposal credential_proposal |
| EmailRegistrationStarted | 1 string operation_id；2 string target_email；3 bytes challenge；4 bytes signing_payload；5 string protocol_version；6 int64 expires_at_unix_ms；7 int64 resend_after_unix_ms |
| CompleteEmailRegistrationRequest | 1 string operation_id；2 string code；3 string password；4 v1.authentication.CredentialProof proof |
| EmailRegistrationCompleted | 1 string operation_id；2 v1.authentication.UserRegistrationResult registration_result |
| GetOwnEmailsRequest | 空 |
| OwnEmail | 1 string binding_id；2 string email；3 int64 verified_at_unix_ms；4 bool is_login；5 bool is_whut |
| OwnEmails | 1 int64 directory_revision；2 int64 login_role_revision；3 repeated OwnEmail emails；4 repeated PendingOwnEmail pending |
| PendingOwnEmail | 1 string operation_id；2 string target_email；3 int64 expires_at_unix_ms；4 int64 resend_after_unix_ms |
| BeginAddOwnEmailRequest | 1 string request_id；2 string email；3 int64 expected_directory_revision |
| OwnEmailVerificationStarted | 1 string operation_id；2 string target_email；3 int64 expires_at_unix_ms；4 int64 resend_after_unix_ms |
| CompleteAddOwnEmailRequest | 1 string operation_id；2 string code |
| OwnEmailAdded | 1 string operation_id；2 OwnEmails emails |
| SwitchOwnLoginEmailRequest | 1 string request_id；2 string target_binding_id；3 string current_password；4 int64 expected_directory_revision；5 int64 expected_login_role_revision |
| LoginEmailSwitched | 1 string operation_id；2 OwnEmails emails |
| RemoveOwnEmailRequest | 1 string request_id；2 string binding_id；3 int64 expected_directory_revision |
| OwnEmailRemoved | 1 string operation_id；2 OwnEmails emails |

所有 ID 为小写 UUIDv4，authId 不放入上述本人输入。OwnEmails 必须恰好一个 isLogin；isWhut 精确域规则引用 UC031。emails 最多 10 个，按 `(verifiedAt,bindingId)` 升序；pending 最多 3 个，均为本人仍可完成 ADD 操作，不含匿名注册。不存在目录或角色不一致为依赖损坏，不伪装为空账号。

#### 注册签名字节

设备 proposal 仍 `iwut-device-v1`，注册操作版本 `iwut-email-registration-v3`，用途 `REGISTER_WITH_PASSWORD_EMAIL`。仅该版本可以调用新的密码注册完成路径。基础 Frame/U64BE/UUID/P-256/严格 DER 引用设备 v1；恰好十字段：

```text
Frame(
  UTF8("iwut-email-registration-proof-v3"),
  UTF8("iwut-email-registration-v3"), UTF8("REGISTER_WITH_PASSWORD_EMAIL"),
  UTF8(serviceId), UTF8("iwut-client"), UTF8(operationId),
  challenge32, U64BE(expiresAtUnixMs), publicKey65, UTF8(normalizedEmail))
```

challenge 32 随机字节、10 分钟、payload 最多 1024 字节；新密码不进入 Frame。Begin 不建 USER、不设置密码、不占邮箱归属；Complete 校验码、签名、新密码策略，在有界 Argon 执行器准备材料后，同一认证事务创建全部事实。密码策略失败不消费码；昂贵计算前扣共享额度，事务重试不重复 hash。

注册初始 principal.accountRevision/minimumCredentialRevision、独立密码记录的 passwordRevision、目录 revision、登录角色 revision、凭据 credentialRevision 均为 1。密码记录独立存储；初始设备 Session 的 DEVICE_CREDENTIAL 方法不伪称本次密码登录或现有 Session 重认证。操作完成后不再次返回秘密；丢失响应保留同一密钥→UC007 恢复。

#### 邮箱目录与独立版本

新目录 `auth_email_directories` 每 authId 唯一：`revision`、`loginRoleRevision`、`loginBindingId`、`verifiedCount` 均在服务端管理；revision/role 为正 int64，verifiedCount 为 1..10。

`auth_email_bindings` 每 bindingId 一条：authId、规范 email、verifiedAt；bindingId 与规范 email 各全局唯一，authId 不是唯一键。一次查询最多读 11 个绑定并验证 count/角色/owner 一致；第 11 个或多个/缺失登录角色失败关闭。删除后的 bindingId 不复用；重新验证原地址得到新 ID。

新增/解绑推进 directoryRevision，不改变 loginRoleRevision。切换登录角色推进两者；同目标为验证密码后的幂等 no-op，不增加版本。登录提案和密码恢复绑定 loginRoleRevision，不因添加/移除无关非登录地址而失效；角色 A→B→A 后原提案仍不能使用。目录版本溢出拒绝变更，不重置版本。

添加 Begin 固定 owner、accountRevision、目标和 expectedDirectoryRevision；首次/重复提交均需同 owner 当前有效 Session。Complete 最终比较快照、目录 CAS 和地址全局归属，成功只添加非登录绑定；并发目录变更为冲突，不自动改角色或复用旧验证另做动作。切换新地址先 ADD 验证，再 SWITCH，不能把新邮箱码当作原账号密码。

Remove 最终确认目标不是登录绑定；始终保留当前登录地址。解绑最后学校依据时客户端提前提示失去认证，但不额外要求密码；服务端不信任客户端校园标志。切换登录邮箱不修改账号代际、设备或 Session，不隐式删旧地址；Auth 消费方读取新主角色，旧邮箱码/恢复的角色版本复核失败。

#### 用途、HMAC 与重试

继续使用独立 `AUTH_EMAIL_BINDING_HMAC_KEY`，不与密码操作 key 混用。验证码 8 ASCII 数字、10 分钟/5 次错误/60 秒冷却；REGISTER/ADD/LOGIN/RESET 的发送共享既有账号、地址、来源额度，不按 v3 扩大预算。

```text
registerRequestMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-request-v3"), UTF8("REGISTER_WITH_PASSWORD_EMAIL"),
  UTF8(requestId), UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8("iwut-device-v1"), publicKey65))
addRequestMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-request-v3"), UTF8("ADD_VERIFIED_EMAIL"),
  UTF8(requestId), UTF8(normalizedEmail), UTF8(serviceId), UTF8("iwut-client"),
  UTF8(authId), U64BE(accountRevision), U64BE(expectedDirectoryRevision)))
codeMac = HMAC-SHA256(K_email, Frame(
  UTF8("iwut-email-code-v3"), UTF8(purpose), UTF8(operationId),
  U64BE(expiresAtUnixMs), requestMac, UTF8(code8)))
```

keyId 继续使用邮箱 v1 域；新 request/code 域防止旧码复用。Begin 幂等 24 小时，键分别为 `(purpose,publicKeyFingerprint,requestId)`、`(purpose,authId,requestId)`，不受 keyId 冷换影响；同键异参冲突、不重发/延期。完成操作不重新给 token 或重新创建绑定。

每 owner 最多 3 个有效 ADD，同 owner/目标的新成功 Begin 只替代该地址原提案，不替代其它地址；容量和共享发信额度检查后才替代。同公钥 REGISTER 最多 1 个，沿用全局 10000 PENDING、1000000 保留记录的拒绝式容量边界，不能驱逐活跃/幂等记录。换 key 废止旧未完成操作，不释放幂等键，不影响已验证绑定。

Switch/Remove 幂等 24 小时，按 `(authId,purpose,requestId)` 固定目标/期望版本。Switch 的指纹由密码 operation key 以新专用域 HMAC 绑定参数和规范当前密码；不存明文密码，不签发通用解锁 token。完成重放只能恢复无秘密当前状态，不重复变更；后续目录已变化不能把历史结果冒充当前快照。

#### 校园依据与旧入口退役

校园 true 只从当前 verified WHUT 绑定集合导出，不另写永久 true 记录。OwnCampusCertification 的 certifiedAt 定义为**当前有效 WHUT 依据中最早 verifiedAt**；删除最早依据可能改变此时间，删除最后依据为 false 且无时间，重新绑定产生新验证时间。它不是首次领取/自然人身份，不得用其重置权益活动。

独立旧校园 Begin/Complete 作为受同一目录/容量/额度约束的 ADD 验证别名，使用新 ADD 用途；不再写旧永久集合，不因已经认证拒绝添加第二个学校地址。Get 与 UserInfo 在同一当前授权事务读取目录/绑定；最后依据移除提交后即不披露认证。坏目录整次拒绝。

旧 v1 EmailBindingService 的 BeginSetEmail/CompleteSetEmail（无密码 REGISTER、隐式更换主邮箱 BIND）退役，不允许通过开关恢复；旧只读 Get 可投影当前主邮箱及 loginRoleRevision，不提供旧 pending。历史 v2 向量保留，不改其字节或作为 v3 输入。Campus 旧永久文档不作为认证依据，无自动迁移。

#### 错误、依赖与启用

沿用邮箱规范错误，并增加 EMAIL_DIRECTORY_CONFLICT（409）、EMAIL_LOGIN_ROLE_CONFLICT（409）、EMAIL_BINDING_LIMIT_REACHED（409）、LOGIN_EMAIL_REMOVAL_FORBIDDEN（409）、EMAIL_BINDING_NOT_FOUND（404）。密码错误/成本额度/依赖按 UC033，不披露另一账号 owner。匿名注册的地址冲突只在证明该地址和新私钥控制后给出受控冲突，不提供存在性预查询。

硬依赖：本契约审核与公开 v3 正反向量、独立 API、密码初始化、目录角色读取和 UC012/013/017/033/034 的角色版本复核、共享邮件/昂贵额度、校园目录投影、UC025 清理/终止清单及旧入口防旁路。首版配置启用必须覆盖完整链路；不能先开密码 API 而保留旧无密码创建/换主入口。

2026-10-13 用户明确接受并授权实现；同步 UC006/011/031 ACCEPTED、脚本生成 brief 后开工。实现覆盖和启用门禁独立记录，不以接受代替验收。

### `platform/contracts/oauth-oidc-v1.md`：OAuth 与 OIDC 接入协议 v1

#### Scope 启用与兼容投影

Scope 单一启用状态与 requestable 投影唯一由 [UC-AUTH-001 / BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004) 定义；OAuth 当前目录许可集合 C 及授权/恢复边界见 [UC-AUTH-014 / BR-OAU-001、002](../use-cases/UC-AUTH-014-authorize-application.md#br-oau-001)。本协议不增加 requestable 与 runtimeEnabled 两个独立开关。

App 继续使用已有 requestable 字段进行版本管理检查；Auth 的 authorize、code 兑换、refresh、UserInfo 和委托签发分别遵循 UC014–019 的当前目录检查。停用不会调用用户撤销用例或抹掉历史同意。目录故障使用依赖错误，Discovery 缓存或 App 旧快照不改变运行判断。

`kind=USERINFO_PROFILE` 是 Auth 内部 Scope Catalog 元数据，不扩展跨服务 `ScopeDefinition` 线格式。其名称固定为 `profile.<fieldKey>`，audience 为空，并按 UC028 一对一映射 UC005 字段；App 仍只看到 name/requestable。该类 scope 与 PROTOCOL/RESOURCE 一起进入实际 enabled 集合，但只用于 UserInfo，不产生 Gateway 资源 audience 或委托路由。

`storage.read` 与 `storage.write` 是 audience 固定为 `iwut-auth-center` 的 RESOURCE scope，可由 Application Version 声明为 required 或 optional。两者互不推导，也不由 `openid`、`offline_access` 或 Profile scope 推导；每次存储请求均重新计算 token、grant、当前 Version scopes 与 enabled Catalog 的交集。

UC031 扩展内部 kind=USERINFO_CAMPUS：只允许 campus.whut，audience/profileField/ProfileValueType 为空。它进入当前 enabled scope 集合、App 声明审核与 consent，UserInfo audience 覆盖它，不产生资源 audience。UserInfo 有有效 scope 且认证存在时输出 iwut_campus={institution:"WHUT",certified:true}，未认证省略；不披露邮箱/认证时间/标识，不进入 ID Token。Discovery claims_supported 增加 iwut_campus，scope 列表仅实际 enabled；授权、故障与注销规则唯一见 UC031。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-031`（use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md）：实现约定与依赖闭合/API、载体与错误、实现约定与依赖闭合/操作、密钥与邮件额度、实现约定与依赖闭合/存储、初始化、注销与开关、实现约定与依赖闭合/工作包与验收边界、变更记录
- `UC-AUTH-006`（use-cases/UC-AUTH-006-create-user.md）：目标与范围、参与者与前置条件、输入与输出、主流程、持久化候选、异常语义、测试与验收、交付依赖与验收边界、变更记录
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：路由边界、校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/auth-email-account-v3.md`（docs 根级共享文档）：实施证据与公开向量（2026-10-13）
- `platform/contracts/oauth-oidc-v1.md`（docs 根级共享文档）：范围与职责、客户端配置、公网端点与响应、授权请求与登录门户、凭据与身份格式、标准 sector 注册与回调清单、错误、CORS 与限额、交付依赖与验收、标准依据

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-031-establish-email-account-and-campus-certification.md` | 201 | `beaa795c7419` |
| `use-cases/UC-AUTH-006-create-user.md` | 171 | `e30e98fe13c9` |
| `platform/contracts/auth-center-api-routing.md` | 142 | `c300b311eaac` |
| `platform/contracts/auth-device-session-v1.md` | 118 | `ec97f26c28b8` |
| `platform/contracts/auth-email-account-v3.md` | 126 | `b13b360d803f` |
| `platform/contracts/oauth-oidc-v1.md` | 148 | `9fec6b0f0311` |
