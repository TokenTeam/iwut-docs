# UC-AUTH-011：设置并激活邮箱

状态：`PROPOSED`

## 目标与范围

> 已登录用户主动设置邮箱，通过验证码证明对该邮箱的控制权，使其成为当前平台账号已激活的邮箱凭据；更换邮箱时，新邮箱验证成功后才替换旧邮箱。

本用例覆盖首次设置、更换、重发验证和读取本人绑定状态。不要求学校邮箱，不设置平台密码，不修改学生资料，不创建 USER，不合并账号，不授予 Developer 资格。

这里的“激活”是邮箱凭据从未验证提案变为有效认证资料。**通过邮箱登录、建立 Session 以及在新设备登记设备凭据仍须独立用例**；本用例完成不等于恢复流程已经交付。普通用户仍可只使用设备凭据，已有注册和登录流程不增加邮箱前置条件。

## 参与者与前置条件

- 调用者是持有有效 Session 的 ACTIVE USER；当前身份及凭据有效性遵守 [BR-LGN-004](UC-AUTH-007-login.md#br-lgn-004)。所有命令和查询都要求在线检查，不能仅凭用户 JWS 快照执行。
- 目标 authId 仅取自 Session，不接受客户端指定。Begin 与 Complete 可以使用同一账号的不同有效 Session；操作不能跨账号使用。
- 用户明确提交目标邮箱。客户端不得从学校数据、资料字段或本机缓存自动发起绑定。
- Auth 配有可用邮件发送适配器；邮件系统不参与用户身份和绑定状态的权威判断。

## 输入与输出

```text
BeginSetEmail {
  requestId: UUID                  // 客户端生成的幂等键
  email: string
  expectedRevision: int64         // 必填；未绑定时为 0
}

EmailVerificationStarted {
  operationId: UUID
  targetEmail: string             // 规范化后的本人提交值
  expiresAt: Instant
  resendAfter: Instant
}

CompleteSetEmail {
  operationId: UUID
  code: string
}

EmailActivated {
  operationId: UUID
  email: string
  verifiedAt: Instant
  revision: int64
}

GetOwnEmailBinding {}

OwnEmailBinding {
  revision: int64                 // 首次激活前为 0
  activeEmail: null | { email, verifiedAt }
  pending: null | { operationId, targetEmail, expiresAt, resendAfter }
}
```

以上是逻辑消息，时间和 UUID 的编码沿用 [设备认证与 Session 契约](../../platform/contracts/auth-device-session-v1.md#基础编码)。邮箱凭据是否存在由 `activeEmail` 表达，不增加可以由客户端写入的 `verified`、`emailLoginEnabled` 或 Developer 标志。

重发使用新的 requestId 再次 Begin，仍提交目标邮箱与当前 revision；不增加独立 Resend 命令。查询中的 pending 只表示仍可验证的提案，不表示邮件送达；失败、过期和已被替代的操作不列入 pending。

## 主流程

1. 用户查询当前绑定状态，明确输入邮箱并提交 Begin。
2. Auth 检查 Session、地址格式、revision、幂等键和限额，保存绑定目标及一次性验证操作；已有激活邮箱保持不变。
3. 操作提交后，Auth 向目标邮箱发送用途为“设置登录邮箱”的验证码，返回操作标识与时限。发送适配器接受邮件不等于收件箱已送达。
4. 用户输入验证码，客户端使用有效 Session 提交 Complete。
5. Auth 校验操作归属、用途、验证码、有效期和尝试次数。在原子提交点复核当前 Session、主体、绑定 revision、操作仍为当前待验证操作，以及目标地址未被其它账号占用。
6. 原子激活邮箱、增加 revision、消费操作并记录结果。更换时同时移除旧邮箱的有效绑定，提交后返回 EmailActivated。
7. 客户端重新查询当前状态。激活成功不创建 Session，也不改变现有设备凭据。

## 业务规则

<a id="br-eml-001"></a>
### BR-EML-001：邮箱凭据与资料、身份分离

邮箱绑定由 Auth 独立管理，不写入用户资料 KV；资料中的邮箱即使文字相同，也不成为已验证凭据，二者不自动同步。邮箱验证只证明本次操作期间的邮箱控制权，不证明学生身份、真实姓名或永久所有权。

首版每个 authId 最多有一个激活邮箱，每个规范化邮箱最多属于一个 authId。待验证提案不占用全局邮箱归属，不能阻止真实邮箱持有人操作。已激活邮箱只允许由其所属账号更换，不能因另一个账号提供了正确验证码就转移归属。冲突不创建或合并 USER，也不沿学生关联寻找账号。

<a id="br-eml-002"></a>
### BR-EML-002：地址规范化与唯一性

首版采用平台明确限定的邮箱格式：去掉首尾 ASCII 空格后，只接受 ASCII 地址；local part 为非空 dot-atom，domain 为至少两个非空 DNS 标签，不接受显示名、注释、引号 local part、域名字面量或地址中的空白/控制字符。local part 最多 64 字节，整串最多 254 字节，DNS 标签最多 63 字节，标签仅允许字母、数字和连字符且首尾不能是连字符。dot-atom 的每段允许字母、数字及 `!#$%&'*+-/=?^_{|}~` 以及反引号，不允许连续点或首尾点。国际化地址另行扩展，不隐式转换。

**本平台将完整地址转为 ASCII 小写作为登录标识、存储和收件地址**。这是产品接受范围，不宣称所有邮件服务都将 local part 视为大小写等价。不移除 `+tag`，不合并点号，不做服务商别名映射；别名邮箱不代表同一个自然人。

规范化发生在格式校验、幂等比较、查重和投递之前，所有入口共用同一实现。数据库对激活邮箱建立全局唯一约束，不能仅依靠先查询再写入保证唯一。

<a id="br-eml-003"></a>
### BR-EML-003：绑定授权与验证码隔离

Begin、Complete 和查询均要求当前有效 USER Session。首次绑定和更换均以该 Session 加新邮箱验证码授权，首版不额外要求生物识别、旧邮箱验证码或学校认证。这沿用 bearer Session 的信任边界，不额外声称绑定操作具备设备再次持有证明。

验证码由服务端密码学随机生成，首版为均匀的 8 位十进制字符串，保留前导零，寿命 10 分钟，最多 5 次错误尝试；等于 expiresAt 时即过期。操作绑定固定 purpose `SET_EMAIL`、authId、规范化目标邮箱、Begin 时的绑定 revision 和服务部署上下文。Complete 不允许修改这些字段；任何未来登录/找回验证码不能用于绑定，绑定验证码也不能用来登录。

持有邮箱验证码而没有原账号有效 Session，不能绑定或更换该账号邮箱。持有 operationId 本身也不是授权。错误尝试计数与关闭操作必须原子更新；并发提交不能突破次数限制。过期判断使用服务端时间，不依赖 Mongo TTL 清理。

<a id="br-eml-004"></a>
### BR-EML-004：更换与原子激活

每个账号只保留一个当前可验证提案；新 Begin 成功创建操作时使旧提案失效，且必须先通过 revision 和限额检查。重发不延长旧验证码寿命，生成新验证码和新 operationId；晚到的旧邮件不能激活。Begin 的数据库失败不替换原提案。

邮箱绑定 revision 独立于用户资料 revision；未绑定为 0，每次成功激活递增一次。请求当前已激活的同一规范化地址返回 `EMAIL_ALREADY_ACTIVE`，不发邮件、不增加 revision。提交必须与 Begin 固定的 expectedRevision 相符，且操作仍是当前提案；冲突不自动覆盖新绑定。

激活将唯一邮箱归属、账号绑定、revision、操作成功结果和最小审计记录原子提交。旧邮箱在此之前始终有效；新验证码错误、过期、投递失败、冲突或事务回滚均不删除旧绑定。提交后旧地址释放，可被以后验证成功的账号使用；它不再具有原账号的认证资格。

更换不撤销已有设备 Session，不修改设备密钥或 Developer 状态。本 UC 不定义尚未存在的邮箱认证 Session；未来邮箱登录用例必须定义凭据版本引用、待登录挑战在更换后的失效，以及既有邮箱 Session 的处理，再开放该登录入口。

<a id="br-eml-005"></a>
### BR-EML-005：重试与提交结果不确定

Begin 的幂等范围是 `(authId, requestId)`，规范化目标邮箱和 expectedRevision 相同才算同一请求。服务端至少保留该映射 24 小时；窗口内相同请求返回原操作元数据，不重新投递、不延长时限、不重新激活被替代的提案；参数不同返回冲突。窗口后不保证 Begin 去重，客户端不得将旧 requestId 用于新的业务请求。

Complete 的成功结果至少保留 24 小时。窗口内同一账号通过有效 Session 重试成功操作，仅返回原结果，不再次消费、增加 revision、发邮件或恢复已经被更换的旧邮箱；仍要求提交与原操作匹配的验证码。返回值是本次操作的历史结果，当前状态以 GetOwnEmailBinding 为准。保留窗口后返回操作不可用，客户端查询当前状态，不推断回滚。

Begin 和 Complete 提交结果未知时返回不可用，不声称失败已回滚。Begin 可用原 requestId 重试并查询 pending；Complete 可用原 operationId 重试并查询当前绑定。Session 已失效时仍拒绝查询和重试，不能以幂等恢复为理由跳过授权。

<a id="br-eml-006"></a>
### BR-EML-006：投递、限额与秘密保护

首版使用 Mongo 保存操作与限额，不引入 Redis 或消息队列。先提交待验证操作，再在事务外投递；事务重试不得重复发送。进程在提交后、发送前中断可能导致该次邮件未发送，用户冷却后以新 requestId 重发即可，不承诺可靠异步投递。发送明确失败返回 `EMAIL_DELIVERY_UNAVAILABLE`，结果不确定也按未确认送达处理；不得因此激活邮箱或撤销已有绑定。

发送额度在 Begin 接受新操作时原子消耗，即使投递失败也不退还。默认同一账号发送间隔至少 60 秒，每账号及每目标邮箱分别每小时最多 5 次，可信来源 IP 每小时最多 20 次；限额窗口和计数必须有界并在重启后有效。对相同幂等请求不重复扣发送额度，但所有 RPC 仍受一般请求限流。部署可以调整正值参数，非法配置拒绝启用入口；被限流返回 retryAfter，不触发邮件。

验证码不以明文持久化，不写入日志、URL、审计或错误；以独立的邮件验证 HMAC 密钥保护校验值，输入覆盖完整操作上下文和验证码，采用无歧义编码与恒定时间比较。不与学生关联密钥、Session 摘要或 JWS 签名密钥共用秘密。密钥由 ENV 注入；首版冷更新换钥可使未完成验证码失效，不需要为临时操作无限保留旧密钥，已激活邮箱不受影响。换钥后旧成功操作可能无法凭原码重放，客户端以当前查询恢复状态。

邮箱明文是用户主动提供的认证数据，仅在 Auth 的绑定、短期操作及邮件投递中使用；不自动加入用户 JWS、对外资料接口或 Developer 状态投影。审计只保留 authId、operationId、绑定 revision、时间和结果，不记录完整邮箱、验证码或 Session token。过期操作和成功结果在所需保留窗口后清理。

<a id="br-eml-007"></a>
### BR-EML-007：查询与占用披露边界

本人查询返回一致快照，包含当前激活地址及当前待验证提案；不接受按邮箱或他人 authId 查询。Begin 对空闲邮箱和被其它账号占用的邮箱采用相同正常验证流程、响应结构和邮件措辞，不提供预查“是否已注册”接口。

只有已通过当前操作邮箱验证码验证后，Complete 才可返回 `EMAIL_UNAVAILABLE` 表示地址不可用于本账号，不返回占用者 authId、资料或 Developer 状态。占用判断必须在提交点重新确认，不能把 Begin 时查重当成承诺。

<a id="br-eml-008"></a>
### BR-EML-008：恢复与 Developer 开通边界

激活邮箱不自动开放邮箱登录、不签发 Session、不添加新设备公钥，也不为账号加 Developer 标记。未来邮箱登录必须独立验证当前邮箱控制权并回到原 authId；新增设备凭据也要有独立授权与私钥持有证明，不能继承旧设备私钥或由 associationToken 授权。

后续 Developer 开通用例应以“已有激活邮箱，且平台已交付可用的邮箱登录能力”为前置条件，不能仅检查资料中存在邮箱或本 UC 的 activeEmail 非空。日常设备凭据登录不因此被禁止。邮箱移除不在本 UC 内；未来若提供移除，应确保 Developer 不失去最后可用的邮箱登录方式，更换则沿用本 UC 的先验证后替换。

## 错误语义

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 地址、标识、必填 revision 或验证码格式非法 | `INVALID_EMAIL_REQUEST` | 400 / INVALID_ARGUMENT |
| 当前 Session 或主体不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 未知/他人/过期/被替代/次数耗尽的操作，或验证码错误 | `EMAIL_VERIFICATION_FAILED` | 400 / INVALID_ARGUMENT |
| Begin 或原子激活的绑定 revision 冲突 | `EMAIL_REVISION_CONFLICT` | 409 / ABORTED |
| 同一 requestId 的参数不同 | `EMAIL_REQUEST_CONFLICT` | 409 / ALREADY_EXISTS |
| 本人已激活该地址 | `EMAIL_ALREADY_ACTIVE` | 409 / ALREADY_EXISTS |
| 验证码正确但地址已被占用 | `EMAIL_UNAVAILABLE` | 409 / ALREADY_EXISTS |
| 请求或发送额度耗尽 | `EMAIL_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 邮件发送失败或结果不确定 | `EMAIL_DELIVERY_UNAVAILABLE` | 503 / UNAVAILABLE |
| 存储不可用或提交结果未知 | `EMAIL_BINDING_UNAVAILABLE` | 503 / UNAVAILABLE |

错误响应不回显邮箱、验证码或占用者信息。成功 Begin 不证明送达；成功 Complete 只在事务确定提交后返回。

## 测试与验收

1. 首次设置必须同时通过有效 Session 和邮箱验证码；学生资料邮箱、学校登录声明及伪造 verified 标志均不能替代验证。
2. 格式边界、大小写规范化、前导零验证码、`+tag` 和点号不合并；HTTP/gRPC 使用同一规范化实现。
3. 更换验证前旧绑定可用；投递失败、错误、过期或冲突不改变旧绑定；成功提交原子切换且只增加一次 revision。
4. 两账号并发激活同一地址最多一个成功；失败方看不到另一账号资料，验证码控制权不允许抢占旧绑定。
5. 同账号重发使旧操作失效；错误尝试、激活和重发并发不突破次数或多次消费；冷却和限额跨重启有效。
6. 跨账号、跨用途、无效 Session、撤销凭据和禁用 USER 失败关闭；激活与撤销并发遵循现有认证事务确认边界。
7. Begin 幂等不重复发信，Complete 幂等不重复变更；后续已换邮箱时重放旧成功操作不恢复旧邮箱。
8. 注入 Mongo 回滚、唯一约束冲突、提交结果未知及发送前后进程中断，均可经重试/本人查询/重发恢复，不误报成功或已回滚。
9. 本人查询区分激活与待验证状态；过期提案不显示为有效；读接口不允许查询其他账号。
10. 邮箱和秘密不出现在 JWS、普通日志、审计与异常回显；换邮件校验密钥只影响临时操作，不影响激活绑定。
11. 激活不签发 Session、不新增设备、不授予 Developer，不改变现有 UC008/009 的撤销语义。

## 交付依赖与边界

- 复用 UC006/007 的 ACTIVE USER、有效 Session 与 Mongo 事务设施；不依赖新的邮箱登录 UC 即可实现绑定。已有实现不等于本草案已接受。
- 实现时补齐独立 API 的 EmailBinding 服务 Proto、HTTP annotation、严格输入校验及 Auth 精确方法鉴权表。三个方法均走有效用户 Session；建议 Gateway 使用 DIRECT 将 `x-iwut-session` 交给 Auth 检查，不以 SESSION-to-JWS 替换该验证。路由只在契约和实现同时交付后启用。
- 新增邮箱唯一索引、账号绑定 revision、操作/幂等记录、持久化限额、原子审计与邮件适配器。邮件不放进数据库事务；生产 SMTP/API 参数与发件域名由部署配置，不写入文档或仓库。
- 后端验收使用真实 Mongo 事务和可控邮件接收端；公网邮件送达与客户端绑定体验独立验收，不以向真实用户发测试信代替自动化测试。
- 后续优先设计邮箱登录及新设备凭据登记，闭合独立恢复能力后再启用 Developer 开通。解绑、旧设备迁移和账号注销分别设计。

## 变更记录

- 2026-09-24：提出设置并激活邮箱草案，定义验证码激活、先验证后更换、唯一归属、重试与邮箱登录/Developer 开通边界；尚未接受或实现。
