<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-022 --spec tools/brief-specs/UC-AUTH-022.json -->
# Brief — UC-AUTH-022：禁用与恢复用户账号

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-022` 禁用与恢复用户账号 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-ACC-001`–`BR-ACC-008`（8 条） |
| 外部引用 BR | `BR-ADM-003`（来自 `UC-AUTH-021`） |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-device-session-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

管理员禁用明确 authId 的整个平台账号，停止其在 Auth 的认证、会话使用、用户授权和身份签发；管理员恢复后，用户必须重新完成认证，禁用前的 Session、OAuth 凭据和待完成操作不能重新生效。

本用例是可逆的账号使用资格管理，不是注销、数据删除、账号合并、设备密钥撤销、Developer 暂停或应用下架。账号边界不扩展到相同 associationId 或学号声明下的其他账号。设备凭据认证可以按 UC007 自动触发；“重新登录”要求新的服务端挑战与证明，不强制弹窗、邮箱登录或生物识别。

本文设计已接受，正在实施。当前实现已有 ACTIVE 检查，但仅切换 accountStatus 不能满足恢复后旧凭据不复活；实施时必须同时扩展下述认证消费路径，不能只上线状态管理 RPC。

### 参与者与接口

操作人是 ACTIVE USER，持有面向 `iwut-auth-center` 的有效 USER JWS，具有 `auth.account.manage`，并在 Auth 当前权威记录中满足 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-001) 完整管理员集合。每次读写在线复核账号状态、JWS 账号版本和当前权限。SYSTEM 或 service identity 不代替管理员。

目标必须是存在的 USER。允许管理员禁用自己，但必须满足最后有效管理员保护；成功后其 Session 立即不可用，恢复需要其他有效管理员操作。没有自动到期解禁，也不接受用户通过邮箱验证自行恢复状态。

```text
ManageUserAccountStatus {
  subjectAuthId: AuthId
  action: DISABLE | RESTORE
  expectedAccountRevision: Int64  // 必填，正数
  reason: String                 // 去除两端空白后 1..1024 UTF-8 bytes
}
GetUserAccountStatus { subjectAuthId: AuthId }
UserAccountStatus {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  accountRevision: Int64
  statusChangedAt: Instant?       // 从未变更时为空
}
```

独立 package `auth_center.v1.account_management`，service `AccountManagementService`：

| 方法 | Auth HTTP 路径 | 成功结果 |
| --- | --- | --- |
| `ManageUserAccountStatus` | `POST /v1/user-accounts:manage-status` | 200，UserAccountStatus |
| `GetUserAccountStatus` | `POST /v1/user-accounts:get-status` | 200，UserAccountStatus |

两方法使用 Gateway SESSION、audience=`iwut-auth-center`、外部前缀 `/auth-center`。Auth 接受可信 USER JWS，不直接接受 Session、OAuth access token 或 service JWS 替代。同时交付 HTTP/JSON 和原生 gRPC，按完整 RPC 名登记鉴权，不使用 service 通配放行。

使用 ProtoJSON、optional revision presence、Timestamp/UTC；拒绝 query、未知/重复 JSON 字段、非法枚举和超过 16 KiB 的解码请求。body 不允许 actor、声称的当前状态或指定的新版本；expectedAccountRevision 只能用于比较已有版本。响应 no-store；查询不返回邮箱、学生关联、资料或管理原因，不提供普通用户枚举账号状态的入口。

### 主流程

1. 校验身份、参数及入口限额，进入 Auth 现有认证事务协调边界。
2. 在同一检查点复核操作人的 ACTIVE 状态、账号版本和管理权限，读取目标账号及版本。
3. 比较 expectedAccountRevision，检查状态转换；DISABLE 若影响有效管理员数量，复用 UC021 的最后管理员事务保护。
4. 原子更新目标状态、accountRevision、statusChangedAt 与归因，并追加不可变状态变更审计。
5. 确认提交后返回目标状态。状态与版本变更即时决定后续 Auth 权威检查的结果，不等待 token 清理任务。

查询也在线复核管理员，结果来自一个一致快照。自我禁用成功可以返回此次已确认结果，不因响应时操作人已禁用而回滚；之后管理查询和恢复请求均拒绝。

### 错误语义与配置

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| JWS 缺失、无效、账号禁用或账号版本失配 | `ACCOUNT_MANAGEMENT_IDENTITY_INVALID` | 401 / UNAUTHENTICATED |
| 当前操作人缺少管理资格 | `ACCOUNT_MANAGEMENT_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 非法输入 | `INVALID_ACCOUNT_STATUS_REQUEST` | 400 / INVALID_ARGUMENT |
| 目标不存在或为 SYSTEM | `ACCOUNT_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| 版本不符或重复状态操作 | `ACCOUNT_STATUS_CONFLICT` | 409 / ABORTED |
| 会失去最后有效管理员 | `LAST_PLATFORM_ADMIN_REQUIRED` | 409 / FAILED_PRECONDITION |
| 账号版本耗尽 | `ACCOUNT_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 超出限额 | `ACCOUNT_MANAGEMENT_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 损坏数据、存储故障、未知提交结果 | `ACCOUNT_MANAGEMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

这些 reason 只用于新管理接口。UC007/011/012 和 OAuth 对旧代材料分别沿用自己的认证失败、invalid_grant 或 invalid_token；故障不可伪装为凭据失效。

新增 `AUTH_ACCOUNT_MANAGEMENT_ENDPOINTS_ENABLED` 默认 false，与用户入口总开关共同控制两个 API；显式启用但用户入口关闭属于配置错误。开关不关闭已交付的账号版本检查；关闭管理 UI/API 后仍不能复活旧凭据。按已认证 actorAuthId 分离有界读写限流，默认每分钟读 60、写 10，部署参数可调整。

### 验收场景

1. ACTIVE/1 登录，DISABLE/2，RESTORE/3：旧 Session、access、refresh、code 在原到期前仍全部失败；新设备挑战或邮箱登录产生版本 3 Session，原 authId、邮箱、公钥和 pairwise sub 不变。
2. 所有当前认证方法、三渠道 OAuth、两种 client 类型以及无 refresh 的 access family 都覆盖；禁用不波及关联组其他账号。
3. 禁用前 Begin、恢复后 Complete 的设备/邮箱挑战和邮箱 BIND 均失败；禁用期间 Begin 的占位操作不可转为有效；重新 Begin 才能登录。
4. 已绑定 consent 页面、旧 code、已完成注册/登录结果重试不能越过版本；匿名 interaction 首次绑定新 Session 仍按 UC014 规则正常工作。
5. 恢复后旧 Auth audience JWS 仍拒绝；缺 account_revision 或记录缺版本失败关闭；App/委托 JWS 按原 TTL/leeway 测试残余窗口，不断言立即离线失效。
6. 重复状态命令和旧 revision 重放无额外事件；事务失败全部回滚，未知提交不返回成功。版本耗尽不回绕，同秒禁用/恢复不复活旧材料。
7. 两管理员互相禁用、禁用与撤销管理员并发、自我禁用，以及与登录/绑定/OAuth 刷新/签发并发，验证明确先后、最后管理员保护和秘密不越界释放。
8. 恢复不修改独立撤销的权限、凭据、grant 或 Developer 状态；历史 consent 可依既有规则复用；开发者名下其他用户 token 的暂时受阻与恢复行为符合 BR-ACC-005。
9. UC020 列表/LRU 排除旧代 Session，所有 Session 消费路径一致；禁用期间查询普通用户功能失败，管理员仍可查看和恢复目标。
10. 真实 Mongo 副本集、实际签名、生产 Wire、HTTP/原生 gRPC 及生成客户端覆盖上述场景；以大量历史凭据确认状态变更不执行全量撤销扫描。Gateway 和下游窗口分别联合验收。

### 实现依赖与联动

硬依赖 UC021 管理资格和最后管理员保护；UC021 已接受并先行实施；本 UC 可以并行开发，集成与启用前必须接入其最后管理员保护。UC004–019 已有相关后端基础，本用例需要横向扩展；UC020 尚未实施，未来实现必须消费同一版本判定，不要求先实现 UC020 才能交付本用例。

实施时同步 UC006/011 的 USER 初始化、UC007–013 的认证/会话/身份消费、UC014–019 的 OAuth 记录与验证、UC020/021 的身份检查，以及 user-model、trusted-identity-v1、RPC/HTTP 路由契约、Proto/存储 schema 和对应生成 brief。固定签名字节及客户端请求不因服务端内部绑定版本而改变。App 无新增数据接口依赖，但离线验签窗口必须明确验收。

本用例不解决被禁用用户的申诉、注销受理或凭据全丢失；后续治理流程另行定义，不能通过普通登录或 bootstrap 自动解禁。

## 业务规则（UC-AUTH-022 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-001 -->
### BR-ACC-001：账号边界与状态转换

唯一转换为 `ACTIVE → DISABLED` 和 `DISABLED → ACTIVE`。恢复的是相同 authId，不新建账号、不改学号关联、不合并其他主体。重复 DISABLE/RESTORE 返回冲突，不递增版本或新增审计；禁止用重复禁用充当反复踢下线接口。

禁用保留资料、邮箱绑定、设备公钥、Developer 状态、permissions、developerHandle、应用归属、历史同意和 pairwise sub。账号不可用时这些事实不赋予操作资格。恢复不重新授予已经单独撤销的权限、不恢复被撤销设备凭据、不解除 Developer 暂停、不撤销用户此前的 OAuth 撤回决定。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002 -->
### BR-ACC-002：账号版本与不可复活

`auth_principals.accountRevision` 是账号状态的正 int64 版本。UC006/011 新建 USER 时初始化为 1；DISABLE 和 RESTORE 每次成功都严格加 1。它同时作为本账号认证材料的有效代际，不新增另一份 authenticationEpoch，不复用权限 permissionRevision 或 grant revocationEpoch，也不使用墙上时钟比较替代。

受账号版本约束的记录在创建或首次绑定用户时保存服务端读出的 accountRevision；消费时必须验证所属 authId 相同、当前 ACTIVE、记录版本等于当前账号版本，并满足原有凭据/Session/grant 条件。已绑定的版本不可更新成当前版本，刷新、重试、查询和恢复不得覆盖旧版本以使记录有效。

例如 ACTIVE/1 签发的 Session，在禁用为 DISABLED/2 后失败；恢复为 ACTIVE/3 后仍失败。只有恢复后新认证产生的版本 3 Session 才能使用。单次状态变更的即时失效成本不随历史 Session 或 OAuth token 数量增长，不在事务中批量扫描所有凭据，也不依赖 TTL 删除。

版本缺失、非法或耗尽失败关闭，不在运行请求中补默认值或回绕。系统尚未上线，首版不为旧测试记录提供自动补齐/迁移；测试 fixture、注册初始化和存储校验需统一升级，不自动删除现存数据。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-003 -->
### BR-ACC-003：所有认证路径的版本闭合

| 对象或入口 | 绑定和校验要求 |
| --- | --- |
| UC007 设备登录挑战 | Begin 时在服务端确定有效凭据归属及账号版本；未知、撤销、禁用或不可识别的目标固定为不可登录占位操作。Complete 不得重新解析占位操作使其后来变为有效；正常操作必须比较 Begin 绑定版本 |
| UC012 邮箱登录操作 | 在原 authId、绑定 revision 和可登录标记之外固定账号版本；Begin 与 Complete 之间经历禁用/恢复时拒绝，必须重新 Begin |
| UC011 邮箱绑定/更换 | BIND 操作固定本人账号版本及原有绑定条件，提交时还需有效 Session；禁用前 pending 操作恢复后仍失败，原激活邮箱保留 |
| Session 与 UC007/008/009/010/013/018/020 的消费路径 | 所有新 Session 绑定账号版本；普通在线检查、容量/LRU、列表、身份签发和本人写操作使用同一有效性判定。旧代 Session 不占有效会话名额、不出现在有效列表、不刷新 lastUsedAt |
| UC014 已绑定用户的 interaction | 首次关联 Session/用户时固定账号版本；同意、拒绝、重新展示和恢复交互不得改绑为新版本；旧页面要求重新发起授权 |
| UC014/015 code、UC015 access 与 family、UC016 refresh | code、family、access 各自保存一致的账号版本；refresh 经不可变 family 继承版本。兑换、刷新、UserInfo、委托签发均在线比较，禁止从旧 code/family 产生新代材料 |
| 已完成操作的幂等结果恢复 | 注册、登录、绑定等重试若要返回认证秘密或继续业务副作用，仍检查当前账号、结果 Session 及版本。旧成功记录只能按原规则报告已完成或失败，不能重新造新 Session 或重新发送旧秘密 |

未绑定用户的匿名 OAuth interaction 不属于被禁用账号，可在用户恢复并重新登录后首次绑定当前版本；曾由旧 Session 绑定的 interaction 不能退回匿名状态绕过校验。UC006 和 UC011 REGISTER 只创建新账号：新 USER 与首次 Session 原子初始化为版本 1；已登记设备不能通过重新注册恢复原账号。

原有随机挑战、设备签名字节及邮箱验证码协议无需把账号版本交给客户端；版本作为不可变操作内部绑定，在原子确认点验证。设备凭据和激活邮箱自身不绑定会随禁用失效的版本，否则会失去恢复后的重新认证能力。

UC008 的幂等 token 撤销、UC009 的已有撤销事实及物理清理可以继续处理旧代记录，但不得将其解释为有效认证或返回秘密。账号版本失效不要求逐条写 revokedAt；审计可由账号状态事件解释失效原因。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-004 -->
### BR-ACC-004：可信身份与下游生效边界

Auth 自身消费的 USER JWS 也必须防止恢复后重放。UC010 为 `iwut-auth-center` 签发时增加 `account_revision` claim，值为当前 accountRevision 的规范十进制字符串（正 int64，无前导零），来自与 Session 检查相同的快照。Auth 的所有 USER JWS 入口统一在线比较该 claim 与当前 ACTIVE 账号版本；缺失或不一致拒绝，不只在本用例管理入口校验。实施时同步 trusted-identity-v1 的条件必需字段与实现。

该字段首版只向 Auth audience 投影；不加入 OIDC ID Token、用户资料或第三方身份，不为 App 引入新的在线 introspection 要求。App audience USER JWS 及 UC019 委托 JWS 仍按既有短 TTL/leeway 离线校验。禁用确认后，Auth 不再为目标账号签发新身份；在此之前已签发的短期 JWS 可能继续被下游接受直到到期，不能承诺瞬间阻断已转发请求。

OIDC ID Token 是一次认证的证据，第三方自己建立的 Cookie/Session 不由本用例远程销毁。旧 opaque access/refresh token 在 Auth 在线检查时永久失败；第三方继续访问平台资源必须经过这些检查。要求应用立即登出需另行设计 OIDC logout/通知协议，不由本 UC 暗中增加。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-005 -->
### BR-ACC-005：OAuth 同意、开发者及应用边界

禁用使目标 authId 作为授权人的全部渠道、client 和应用下的旧 code/token/family 失效，不需要逐条推进每个 grant epoch；保留历史 consent 和用户撤销记录。恢复后先新登录，再走 UC014/015 获取新凭据；历史同意仍按原 prompt、scope 和 offline_access 规则复用，不保证全部静默、不强制无差别重新同意。

若目标也是 Developer，当前所有者可用性检查会阻止其名下应用的相关 OAuth 使用，但这不是撤销其他用户自己的账号版本或 grant。其他用户尚未过期、未撤销的凭据在所有者恢复后可能重新可用；要永久撤销这些应用凭据或停用应用，需单独的 App/client 治理动作。

公开 Catalog、静态内容和统一启动目标不会仅凭此 Auth 状态写入自动下架。App 不直接读 Auth 数据库；若上线策略要求应用随所有者禁用停用，需要另立跨服务契约。审核和管理权限虽然保留，目标账号本身不可用时不得在 Auth 行使，App 已签身份的残余窗口遵守 BR-ACC-004。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-006 -->
### BR-ACC-006：事务、并发与最后管理员保护

状态写入、版本递增、最后管理员计数和审计使用现有 Auth 全局认证事务栅栏，并与 UC021 的资格变更、UC004 权限管理、认证 Begin/Complete、Session 检查、邮箱变更及 OAuth 确认/兑换/刷新/签发协调。actor 和 subject 同一人时只处理一个主体，不依赖锁顺序碰巧避开冲突。

DISABLE 使有效管理员数量减少时，强制引用 [BR-ADM-003](../use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-003)。并发“撤销管理员 A + 禁用管理员 B”必须在同一协调点重新检查，不能各自以旧快照通过。RESTORE 不要求目标邮箱恢复就绪，只恢复已有账号状态；操作人自身必须有效。

在禁用前先提交的认证操作，其结果因版本变化而失效；禁用先提交时，旧版本操作必须失败。即使禁用与恢复都发生在同一秒，也不能接受旧挑战。UC010/019 签名候选仅在事务确认后释放；未知提交结果不返回候选秘密或声称成功。

读取外部 App 资格不能提供跨库原子性，但账号状态/版本在 Auth 最终提交点必须重新验证；网络快照或事前读取不能替代。恢复与 UC021 权限撤销并发时保留独立权限变化，不能恢复整份旧 principal 快照覆盖其他事实。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-007 -->
### BR-ACC-007：审计、查询与错误边界

`auth_account_status_audit_events` 为 append-only，保存 eventId、actorAuthId、subjectAuthId、action、reason、before/after 状态和 accountRevision、occurredAt。权限和 Developer revision 不随状态变化递增；原子设置 accountStatusUpdatedBy/statusChangedAt，归因不复用其他能力的 updatedBy 字段。审计失败回滚，重试保留同一候选 eventId；建立 eventId 唯一及 subjectAuthId/occurredAt/eventId 查询索引。

管理员可查询明确目标的状态和版本，但禁用原因不作为匿名登录错误或邮箱通知披露。本用例不自动发信，不收集 IP、设备位置或学校信息。正常用户认证入口对未知、禁用、旧代材料继续返回原有统一失败；不得把管理 API 的目标存在性响应搬到登录流程。

参数验证及 actor 鉴权后再读取目标；先检查 expectedAccountRevision，再判断状态转换和最后管理员约束。结果未知时管理员通过 Get 查询；不携带原 revision 自动重放到新状态，防止延迟请求误禁用已经恢复的账号。

<!-- 权威位置: use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-008 -->
### BR-ACC-008：完整交付与历史数据边界

状态命令只有在所有认证材料创建/消费路径都实现账号版本判定后才能启用，包括 HTTP、gRPC、内部签发、成功结果恢复和 Session 有效性列表。不得只给新 Session 加字段，却允许缺字段的旧 Session/token 继续使用。旧版与新版认证服务不得混跑绕过检查。

本方案不要求新增 Redis、后台遍历撤销或断点迁移任务。失效记录沿用各自保留和清理规则；删除历史记录不是禁用成功的前置条件。测试环境需要按新 schema 初始化，不自动迁移旧测试库，也不把新增字段缺失当作版本 1。

## 外部引用的业务规则

> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。

### 来自 `UC-AUTH-021`

<!-- 权威位置: use-cases/UC-AUTH-021-manage-platform-administrators.md#br-adm-003 -->
### BR-ADM-003：最后有效管理员保护

治理初始化成功后，正常治理命令提交时必须至少保留一个 ACTIVE USER 且 membership=GRANTED。DISABLED 管理员、SYSTEM 及损坏记录不能用于满足此约束。该判定不依赖瞬时 SMTP 健康，不声称能够证明某人仍掌握登录材料。

允许自我撤销，但必须存在另一个满足条件的管理员。禁止两个管理员在并发撤销中分别基于旧快照把双方都移除。后续账号禁用、注销及任何减少有效管理员数量的入口必须复用这一约束，不能只在本用例做检查。

统计和修改须参与同一可写事务协调点；单纯 Mongo snapshot 下 count 后更新不同主体不能防止并发写偏差。复用现有全局认证事务栅栏并确认它覆盖所有相关写入口；若实现调整为专用治理栅栏，仍须与身份签发、UC004 和后续账号状态变更建立一致锁顺序。无需 Redis 或跨服务事务。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-device-session-v1.md`：App 设备认证与 Session v1 契约

#### Session 载体

Session 秘密为 CSPRNG 生成的 32 字节，线上 token 为其 B64U 编码，恰好 43 字符。数据库 tokenDigest 为 `SHA256(rawToken32)`，不是对 43 字符文本做散列。sessionId 不等于 token，也不能用于鉴权。

HTTP header 与 gRPC metadata 均使用 `x-iwut-session`，值仅为 token，不加 `Bearer `。最多一个值，缺失、空白、重复、逗号合并、错误长度/编码均拒绝；不能从 query、cookie、消息正文、`Authorization` 或 `x-iwut-identity` 回退取值。对 UC008 格式错误映射 INVALID_SESSION_TOKEN；对需要有效 Session 的 UC009 映射 SESSION_INVALID。

Gateway 仅对显式 Auth Session 路由转发该秘密，不转发到 App Center 或其它业务服务。入口必须通过 TLS；内部 gRPC 使用部署控制的私有网络或 TLS。后续 Gateway 签发链路继续独立设计，本契约不开放任意 audience 的公共 introspection。

UC011 的可选 Session 例外仅用于其精确 Begin/Complete 方法，详见 [邮箱设置与注册协议](../../platform/contracts/auth-email-binding-v1.md#rpc-与-session-鉴权)；其它接口的必需载体规则不变。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### Claims

payload 是 JSON 对象。公共身份字段始终必填；能力字段保持在同一个 v1
线格式中按消费用例条件必填。新增能力字段不改变 JWS 算法、载体、audience 或
信任边界，因此不建立 v2。

| 字段 | 类型 | 必需 | 语义 |
| --- | --- | --- | --- |
| `iss` | string | 是 | 签发方；必须等于本地配置的 issuer |
| `sub` | string | 是 | Auth 的 opaque `authId`；非空；成为可信身份主体 |
| `aud` | string 或 string 数组 | 是 | 目标 audience；必须包含本地配置的 audience（App Center 为 `iwut-app-center`） |
| `iat` | number（Unix 秒） | 是 | 签发时间 |
| `nbf` | number（Unix 秒） | 是 | 生效时间 |
| `exp` | number（Unix 秒） | 是 | 失效时间 |
| `jti` | string | 是 | 该 token 的唯一标识；非空 |
| `account_revision` | string | Auth audience USER 必需 | 规范无前导零的正 int64 十进制字符串；Auth 在线比较当前 ACTIVE 主体版本，规则见 UC-AUTH-022/BR-ACC-004；其他 audience 不要求或推导此字段 |
| `developer_status` | string | 可选 | 仅 Developer 主体携带；取值 `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED`、`WITHDRAWN` 之一；普通用户省略 |
| `permissions` | array&lt;string&gt; | 条件必需 | 权限用例必需；元素必须是非空、无首尾 whitespace 的唯一字符串，按精确字符串匹配；未知权限可以透传但不能产生隐式授权 |

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费独立精确值 `app.profile.review`；二者不互相隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- 同一主体可以同时携带两类字段，但任一字段都不能替代另一类字段。
- 已按旧版 v1 签发、只含合法 `developer_status` 的 Developer token 继续有效；增加 `permissions` 不改变既有字段含义。

#### 时间与有效期

- 所有时间字段都是 JSON number，表示 Unix 秒；允许小数秒但校验以秒为粒度。
- 必须满足 `exp > iat`，且 `exp - iat <= maxTTL`。`maxTTL` 由消费方启动配置注入，默认 5 分钟。
- 必须满足 `exp > nbf`。
- 以消费方时钟为准，允许 `clockSkew` 的容差（默认给一个小值，例如 30 秒，具体由启动配置决定）：
  - `now <= exp + clockSkew`，否则视为过期；
  - `nbf - clockSkew <= now`，否则视为尚未生效；
  - `iat <= now + clockSkew`，否则视为签发时间在未来。
- `maxTTL` 以 `exp - iat` 度量，不叠加 clockSkew；clockSkew 只用于与当前时间比较。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-022`（use-cases/UC-AUTH-022-disable-and-restore-user-account.md）：变更记录
- `UC-AUTH-021`（use-cases/UC-AUTH-021-manage-platform-administrators.md）：目标与范围、参与者与身份、输入与输出、API、主流程、错误语义与运行约束、测试与验收、实现依赖与联动、变更记录
- `platform/contracts/auth-device-session-v1.md`（docs 根级共享文档）：范围与权威来源、基础编码、公钥与签名、挑战与待签消息、学号关联声明、RPC 鉴权表、实现配置与验收边界、测试向量、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：目的与范围、传输载体、JOSE Header、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-022-disable-and-restore-user-account.md` | 183 | `f13eb70a5211` |
| `use-cases/UC-AUTH-021-manage-platform-administrators.md` | 207 | `db46fb9b9689` |
| `platform/contracts/auth-device-session-v1.md` | 123 | `501e81cdeb09` |
| `platform/contracts/trusted-identity-v1.md` | 138 | `e9d524a5a5e3` |
