# UC-AUTH-027：管理应用平台运维权限

状态：`ACCEPTED`（2026-11-04 用户明确接受本人运维权限读取修订并授权实现）

2026-11-08 用户接受 `app.application.search` 的独立授撤、本人发现及 App audience 签发修订，三项精确 allowlist 同步生效。

2026-10-06 已接受并交付的管理员目标 Get/Manage 与 App audience 权限投影继续有效。本次新增本人最小读取及其 API/Gateway/Console 交接；旧版 ACCEPTED 不授权实施本次修订。2026-11-04 用户明确接受本次修订并授权实现；依赖复核通过，先同步接受状态并脚本生成 brief，再按 API/Auth → Gateway → Console 串行实施。不开生产开关，不自动 commit/push。

## 目标与范围

平台管理员在 Auth Center 中分别授予或撤销用户的 `app.application.search`、`app.application.suspend` 与 `app.application.restore` 原子权限，使 App Center 能依据短期可信用户身份授权平台级 Application 目录与最小摘要读取、暂停与恢复操作，并为每次权限变化留下不可变审计。

本用例只管理人员权限，不暂停或恢复任何 Application。Application 平台目录的集合、过滤与字段由 App 对应搜索用例拥有。Application 的平台暂停状态、恢复条件、运行与目录门禁、状态 revision 和业务审计由 App UC028 拥有。Application 当前管理员对自己应用的转让、关闭、发布和可恢复归档继续依据 App Center 的 `adminId` 与对应用例授权，不需要也不能借此取得平台运维权限。

本用例不提供任意权限编辑接口，不复用 `app.profile.review` 或 `app.version.review`，不把 Developer、Reviewer、Application 管理员或平台管理员自动转换为应用运维人员。三项权限不进入 OAuth Scope Catalog，不能由第三方应用申请，也不能通过用户 consent 获得。

本次修订增加任意有效 ACTIVE USER 的本人有效运维权限读取，使独立运维人员无需成为平台管理员即可发现自己能执行的动作。不提供他人查询特例、通用权限目录或权限证明，不改变管理员管理入口和 App 写命令的鉴权。

## 参与者与依赖

- **管理操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的可信 USER JWS；JWS 包含 `auth.platform-admin.manage`，Auth 在线复核其当前完整平台管理员资格。
- **本人读取者**：任意有效 ACTIVE USER，沿同一 SESSION → Auth audience USER JWS 信任链；不要求完整管理员资格、App 运维权限、Developer 或 Reviewer 资格。此入口的目标只能是该身份的 authId。
- **目标用户**：明确 `subjectAuthId` 对应的 ACTIVE USER。SYSTEM、未知用户与 CLOSED 账号不能获得权限；Developer 或 Reviewer 资格不是前提。
- **Auth Center**：唯一保存人员权限、共享 `permissionRevision` 和授权审计，并通过 UC010 投影到 App audience JWS。
- **App Center**：只消费 audience=`iwut-app-center` 的已签名权限 claim，按 [UC-APP-028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md) 执行精确权限检查；不保存另一份 grant。
- **Gateway / Console**：分别复用精确 SESSION 路由与当前 BrowserSession 绑定读取；只消费本人最小投影，不向浏览器披露 JWS，不把权限放进 BrowserSession。

依赖 [UC021](UC-AUTH-021-manage-platform-administrators.md) 的管理授权、[UC022](UC-AUTH-022-disable-and-restore-user-account.md) 的账号状态与版本、[UC010](UC-AUTH-010-issue-user-identity-from-session.md) 的可信身份签发，以及 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。本人读取只复用普通 USER 在线身份确认，不以 UC021 初始化标记或完整管理集合为前置。App 状态机由 UC-APP-028 拥有，Console 消费见 [UC-CONSOLE-015](../../console/use-cases/UC-CONSOLE-015-manage-platform-governance.md) 的已接受修订；设计、后端交付与联合验收分别记录。

## 输入与输出

```text
ManageApplicationOperationsPermission {
  subjectAuthId: AuthId
  permission: "app.application.search" | "app.application.suspend" | "app.application.restore"
  action: GRANT | REVOKE
  expectedPermissionRevision: Int64  // 必填，正数
  reason: String                     // 去除两端空白后 1..1024 UTF-8 bytes
}

GetApplicationOperationsPermissions {
  subjectAuthId: AuthId
}

GetOwnApplicationOperationsPermissions {} // 无任何目标或筛选输入

OwnApplicationOperationsPermissions {
  subjectAuthId: AuthId              // 仅来自当前可信 USER 身份
  permissionRevision: Int64          // 当前权威共享正数版本
  effectivePermissions: String[]     // 公开范围内完整有效 permission ID 集合
}

ApplicationOperationsPermission {
  permission: String
  granted: Bool
  effective: Bool
}

ApplicationOperationsPermissions {
  subjectAuthId: AuthId
  accountStatus: ACTIVE | DISABLED
  permissions: ApplicationOperationsPermission[2]
  permissionRevision: Int64
  grantBlockers: GrantBlocker[]
}
```

管理员 Get/Manage 的响应固定按 permission 字典序返回三项，即使均未授予也返回三个 `granted=false` 项。`effective` 表示当前账号为 ACTIVE 且已保存该项授权；DISABLED 用户保留 grant 事实但三项均不生效。查询不返回目标的其它权限、邮箱、Developer 状态、学生资料或 Session。

本人响应只包含上列三个字段，不返回 granted、grantBlockers、accountStatus、管理员资格或其它 permissions。精确集合、空集合、并发和失败语义由 [BR-AOP-007](#br-aop-007)、[BR-AOP-008](#br-aop-008) 定义；它不是管理员管理资源的裁剪复用。

授予目标首版要求 ACTIVE USER、已有激活邮箱且邮箱恢复部署就绪；这些条件与高权限账号的可恢复性有关，不表示邮箱是真实身份认证。撤销允许目标为 ACTIVE 或 DISABLED，不因邮箱缺失或邮件服务不可用受阻。grantBlockers 固定按 `ACCOUNT_DISABLED, EMAIL_REQUIRED, EMAIL_RECOVERY_UNAVAILABLE` 顺序返回适用于所查询目标的公共门禁；某项是否已经授予由对应 permission 的 `granted` 表达。提交时仍须重新检查。

## API 契约

独立 package `auth_center.v1.application_operations_permission`，service `ApplicationOperationsPermissionService`：

| 方法 | Auth HTTP 路径 | 成功响应 |
| --- | --- | --- |
| `ManageApplicationOperationsPermission` | `PUT /v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | 200，完整三项状态 |
| `GetApplicationOperationsPermissions` | `GET /v1/users/{subject_auth_id}/application-operation-permissions` | 200，完整三项状态 |
| `GetOwnApplicationOperationsPermissions`（本次修订） | `GET /v1/users/me/application-operation-capabilities` | 200，`OwnApplicationOperationsPermissions` |

Manage 的路径固定目标和 permission，正文只提交 action、expectedPermissionRevision 与 reason；正文不能替换路径身份。两种 Get 均无正文、无 query。三个方法同时提供 HTTP/JSON 与原生 gRPC，并以精确 full method 分别加入鉴权表；不按 service 通配放宽。

本人方法的精确 full method 为 `/auth_center.v1.application_operations_permission.ApplicationOperationsPermissionService/GetOwnApplicationOperationsPermissions`。已接受 Proto 形状：空 `GetOwnApplicationOperationsPermissionsRequest`；新资源的 `subject_auth_id = 1`（string）、`permission_revision = 2`（int64）、`effective_permissions = 3`（repeated string），标准 ProtoJSON 名称分别为 subjectAuthId、permissionRevision、effectivePermissions。不改已有消息、字段编号或 RPC；按上述形状生成可执行 API；旧输入提交不含新方法，不得声称已固定新增发布版本。

本人 HTTP 请求拒绝任何正文、query、subjectAuthId/actor/permissions 等替代输入；原生 gRPC 空消息拒绝未知字段。HTTP 成功响应必须明确输出 `effectivePermissions: []`（即使零项）；只为该新资源保障空数组输出，不借此修改旧 API 的默认序列化。客户端先验证 JSON 集合字段存在且非 null，再用官方生成契约解码；不能用 repeated 默认值吞掉缺字段。原生 gRPC repeated 零项表示空集合，但主体及正数 revision 仍必须有效。int64 按标准 ProtoJSON 十进制字符串精确处理，不经浮点数。

Gateway 使用 SESSION 路由向 Auth 换取 audience=`iwut-auth-center` 的 USER JWS。Auth 只接受该可信身份，不接受 OAuth access token、App audience JWS、service JWS、直接 Session 或请求正文自报 actor。响应 `no-store`；拒绝未知或重复字段、非法枚举、query 和超过 16 KiB 的请求。

## 主流程

### 授予或撤销

1. 验证可信身份、精确方法、参数与入口限额；确认 permission 严格属于三项 allowlist。
2. 在 Auth 认证事务协调边界中在线确认操作人是 ACTIVE USER 且持有 UC021 完整平台管理员资格。
3. 读取目标账号、权限集合、邮箱绑定与共享 `permissionRevision`；损坏数据失败关闭。
4. 比较 expectedPermissionRevision。GRANT 复核目标 ACTIVE、激活邮箱和恢复就绪；REVOKE 只要求目标当前持有所选权限。
5. 仅修改选定权限，保留其余平台权限、两项审核权限、管理权限和其它合法权限；严格增加一次共享 revision。
6. 权限更新与 append-only 审计在同一事务提交，成功后返回同一提交结果的完整三项状态。

重复 GRANT/REVOKE 或 stale revision 返回冲突，不增加 revision 或审计。事件 ID 在事务重试前生成并保持稳定；提交结果未知时返回不可用，客户端通过 Get 读取权威状态，不能盲目改用新 revision 重放。

### 查询

只有当前有效的平台管理员可以调用原 `GetApplicationOperationsPermissions`，即使 subjectAuthId 是自己也不例外。Get 对存在且结构合法的 ACTIVE 或 DISABLED USER 返回三项状态；不存在、SYSTEM、CLOSED 或损坏目标不伪装成普通未授权用户。鉴权先于目标读取，未授权调用者不能借错误差异枚举账号。

### 本人读取

1. 按精确 full method 选择普通 USER 身份分支，校验签名、issuer、audience、typ、时间、唯一载体与请求；不得要求 JWS 包含管理员或 App 运维 permission。未知方法继续失败关闭。
2. 在现有认证事务协调边界中，以身份 authId 为唯一键复核当前 USER、ACTIVE 和 accountRevision；同次读取权威 permissions 及共享 permissionRevision。不能依据入站 JWS 的权限 claim 计算本次集合。
3. 严格校验完整权限数据及版本后，按 BR-AOP-007 投影本人最小资源；不查邮箱、不调用 `RequireAdministratorTx` 或管理员管理 snapshot，不引入恢复部署、初始化标记或管理 bundle 前置。
4. 返回同次观察的完整集合与版本，或按 BR-AOP-008 失败。读取不修改 grant、permissionRevision 或授权业务审计；允许复用既有认证事务技术协调，不建立新业务写入。

## 业务规则

<a id="br-aop-001"></a>
### BR-AOP-001：精确运维权限与职责分离

固定 allowlist 包含 `app.application.search`、`app.application.suspend` 和 `app.application.restore`。search 仅供 App 全平台 Application 目录及最小摘要读取，suspend 只允许 App UC028 把可运行 Application 置为平台暂停，restore 只允许按该用例的恢复门禁解除平台暂停；任一权限都不授予审核、发布、转让、关闭、归档、OAuth client 管理或人员授权能力。

三项权限独立授予。search 不授予暂停、恢复、审核或 owner 私有详情读取权；其他两项也不授予 search。只持有 suspend 的值班人员不能恢复，只持有 restore 的人员不能制造暂停。App Center 不接受 `app.application.*`、`app.*` 或通用 `app.application.manage` 通配能力，也不能把其中一项推导为另一项。

<a id="br-aop-002"></a>
### BR-AOP-002：平台管理员负责授权但不自动获得操作权

UC021 的平台管理员固定 bundle 不包含三项 App 平台权限。完整平台管理员可以通过本用例管理权限，但若要亲自搜索、暂停或恢复 Application，仍须显式向自己的 authId 授予对应权限。Developer、Reviewer、Application 当前管理员和 SYSTEM 均不因身份自动获得这三项权限。

首版复用完整平台管理员资格作为管理授权，不增加 `auth.application-ops.manage`。若未来需要把人员权限管理员从平台管理员中拆分，应另立 UC 修改授权模型，不能把 App 操作权限本身当作授予他人的权限。

<a id="br-aop-003"></a>
### BR-AOP-003：共享权限版本与原子审计

三项平台权限与现有审核、管理权限共用 `auth_principals.permissions` 和正数 `permissionRevision`。每次真实变化严格增加一次 revision；不同权限管理用例对同一目标使用相同旧 revision 并发时最多一个成功，不得通过独立版本覆盖另一项变化。

复用 `auth_permission_audit_events`，事件保存 eventId、actorAuthId、subjectAuthId、精确 permission、GRANT/REVOKE、reason、before/after、before/after revision 与 occurredAt。权限和审计同事务提交；审计失败全部回滚。不得记录邮箱、Session、学生信息或 JWS。

<a id="br-aop-004"></a>
### BR-AOP-004：Audience 最小投影与撤销窗口

UC010 的 `iwut-app-center` allowlist 增加三项平台权限；`iwut-auth-center` audience 不投影它们。Auth 仅从当前权威权限集合签发，App 只接受 audience 正确、签名和时间有效的 USER JWS，不接受 OAuth scope 或客户端自报 permission。

撤销提交后 Auth 不再签发包含该权限的新 JWS。已经签出的 JWS 仍可能在 `exp` 与消费方 clock skew 范围内被 App 接受，传播上界沿用 UC010 当前默认 60 秒、可配置 1–300 秒的短期身份模型。首版不为此能力引入每请求 introspection、denylist 或 Redis；若未来要求立即撤权，必须通过独立 ADR 修改共同信任模型。

<a id="br-aop-005"></a>
### BR-AOP-005：账号状态、恢复能力与授权事实

只有 ACTIVE USER 且具备激活邮箱和部署就绪恢复能力时可以 GRANT。账号被禁用时保留三项 grant 事实但不生效，Auth 不向该账号签发新的可信身份；账号恢复后仍须重新登录，既有 grant 可再次投影。账号 CLOSED 后由 UC025 的清理和保留规则处理，不作为可查询运维人员继续存在。

撤销不要求目标仍有邮箱或恢复能力，避免无法收紧权限。授予和撤销不改变 Developer、Reviewer、平台管理员、Session、设备凭据或 OAuth 状态。

<a id="br-aop-006"></a>
### BR-AOP-006：Auth 授权与 App 业务状态分离

Auth 只回答“哪个 USER 当前被授予哪项运维能力”。Application 是否 ACTIVE、已暂停、CLOSING/CLOSED、谁发起过暂停、是否满足恢复条件，以及暂停对目录、启动解析、审核和 OAuth 的影响，全部由 App Center 的 Application suspension 用例定义并持久化。

App UC028 的暂停/恢复命令必须分别检查精确权限并记录其自身业务审计；不能仅凭 Auth grant 修改数据库，也不能要求 Auth 持有 applicationId 状态。CLOSING/CLOSED 不得通过 restore 权限恢复，所有者自助归档不得复用平台 suspension 字段。

<a id="br-aop-007"></a>
### BR-AOP-007：本人最小有效权限集合

`GetOwnApplicationOperationsPermissions` 只允许有效 ACTIVE USER 查询自己；不要求先持有任一公开权限。响应 subjectAuthId 必须严格等于可信身份 authId，首版公开 allowlist 只有 BR-AOP-001 的三项权限。effectivePermissions 是该公开范围内本次读取的完整有效集合，按 BR-AOP-005 的既有效力规则计算，不因读取附加邮箱或恢复就绪条件，不直接透传全量人员 permissions。

集合不分页、不截断、不返回部分成功；无重复并按 permission 字典序输出。合法普通用户和没有另获 App grant 的完整管理员均成功返回 `[]`；仅 suspend 返回 `["app.application.suspend"]`，仅 restore 返回 `["app.application.restore"]`，suspend/restore 都有返回 `["app.application.restore", "app.application.suspend"]`；仅 search 返回 `["app.application.search"]`；三项都有返回 `["app.application.restore", "app.application.search", "app.application.suspend"]`。只有成功完整响应中已公开 ID 的缺席才表示该项当前不生效，不能外推其它权限。

以后只有经对应业务设计审核接受才能扩大公开 allowlist，无需增加逐项布尔字段或客户端查询清单。客户端只按认识的精确 ID 启用已有动作；合法但不认识的新增 ID 不使资源解码失败，也不生成新按钮、推导同前缀权限或扩大授权。ID 必须是非空合法 UTF-8 字符串，不含空白或 `*` 通配；禁止 trim/大小写归一化、重复项及错类型。首版服务端只会输出上述三个 ID，不预先授权通用权限发现。

<a id="br-aop-008"></a>
### BR-AOP-008：本人读取的一致性与失败关闭

当前账号/身份代际、权威权限集合和正数共享 permissionRevision 必须在同一 Auth 认证事务协调边界内形成观察。读与授权变更并发可以观察合法提交顺序中的前或后状态，不得混合不同版本的集合与 revision；撤销已经提交后发起的新读取必须反映该 ID 移除及新 revision。其它人员权限变化也可能推进共享 revision，不据版本变化推断是哪项授权改变。

身份缺失、失效、未知、SYSTEM、DISABLED/CLOSED 或 accountRevision 不匹配按身份拒绝处理，不返回成功空集合或目标管理 404。账号/权限记录结构损坏（包括非法/重复权限项）、版本缺失/非正数/类型错误、存储/事务失败均返回不可用；不能忽略坏数据后返回剩余集合。429、协议错误、关闭入口、网络错误和依赖失败都不是“无权限”。成功及错误响应均 `Cache-Control: private, no-store`。

本人资源仅是本次观察，不是整个 Session 的授权租约或 App 可消费凭据。读取后再撤销仍由 App 精确命令鉴权和 BR-AOP-004 的既有短期 JWS 窗口约束；permissionRevision 不新增 App 命令参数，不提供每请求 introspection 或即时撤权承诺。

## 错误语义与运行约束

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺少或无效可信用户身份 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 管理 Get/Manage 操作人非当前有效平台管理员（不用于本人零权限读取） | `APPLICATION_OPERATIONS_PERMISSION_FORBIDDEN` | 403 / PERMISSION_DENIED |
| 参数、permission、action、revision 或 reason 非法 | `INVALID_APPLICATION_OPERATIONS_PERMISSION_REQUEST` | 400 / INVALID_ARGUMENT |
| 管理 Get/Manage 目标不存在、SYSTEM、CLOSED 或不可管理 | `APPLICATION_OPERATIONS_PERMISSION_SUBJECT_UNAVAILABLE` | 404 / NOT_FOUND |
| stale revision 或重复动作 | `APPLICATION_OPERATIONS_PERMISSION_CONFLICT` | 409 / ABORTED |
| GRANT 目标禁用、无邮箱或恢复未就绪 | `APPLICATION_OPERATIONS_PERMISSION_GRANT_BLOCKED` | 409 / FAILED_PRECONDITION |
| permissionRevision 耗尽 | `PERMISSION_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 入口限额 | `APPLICATION_OPERATIONS_PERMISSION_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 数据损坏、存储故障或提交结果未知 | `APPLICATION_OPERATIONS_PERMISSION_UNAVAILABLE` | 503 / UNAVAILABLE |

本人入口在线身份拒绝使用 `INVALID_USER_IDENTITY`（401 / UNAUTHENTICATED），不得用管理员 forbidden、目标 404 或 grant blocker 表示没有三项权限。错误请求仍复用 `INVALID_APPLICATION_OPERATIONS_PERMISSION_REQUEST`；权限/版本损坏与依赖故障复用 `APPLICATION_OPERATIONS_PERMISSION_UNAVAILABLE`。

入口复用独立默认关闭配置 `AUTH_APPLICATION_OPERATIONS_PERMISSION_ENDPOINTS_ENABLED`，要求用户端点和身份签发已配置；本人方法不额外依赖平台管理员配置或初始化。管理 Get/Manage 的完整管理员与授予恢复门禁不变。限流按已认证 actorAuthId 分开读写计数，本人 Get 与管理 Get 共用每分钟读 60，写 10，桶容量有界；不能按任意 subjectAuthId 建立无界状态。关闭时不注册本人 HTTP/gRPC 方法，Gateway/Console 不回退旧管理员查询或 App 写命令探权。部署启用必须等待本次审核和独立交付验收。

## 验收场景

1. 分别授予、撤销三项权限，以及零项、仅 search、仅 suspend、仅 restore 及组合的完整状态投影。
2. Reviewer、Developer、Application 管理员、SYSTEM 和没有完整管理员资格的用户均不能管理权限；平台管理员未显式获得操作权限时，App JWS 不含三项权限。
3. 平台管理员向自己显式授权后只获得选定能力；授予一项不改变另一项或任何审核/管理权限。
4. ACTIVE＋邮箱＋恢复就绪门禁；DISABLED/无邮箱目标不能 GRANT，但已有 grant 可以撤销。账号禁用时 grant 保留且不生效，恢复后仅新签发身份重新生效。
5. 与 UC004、UC021 及其余平台权限同时使用相同 expected revision 并发，最多一个成功且不丢失权限。
6. 审计失败、事务重试和 unknown commit；真实变化只有一个事件，重复命令无事件。
7. Auth 与 App audience 投影隔离；OAuth、service JWS、错误 audience、伪造权限、通配权限全部拒绝。
8. 撤销与 UC010 签发竞争具有明确提交顺序；撤销后新 JWS 不含权限，旧 JWS 的残余窗口不超过既有 TTL/clock-skew 契约。
9. HTTP/JSON、原生 gRPC、生成客户端、Gateway SESSION 路由、严格解码、no-store 和有界限流。
10. 实际 App consumer 验证精确权限组合；业务暂停/恢复状态机由对应 App UC 单独完成联合验收。
11. 本次新增：非管理员 none/suspend-only/restore-only/both 四组合与无另获 App grant 的完整管理员；同一有效 Session 在正式授予/撤销后新读反映所选项及新共享版本。其它权限/资格不隐式授予 App 权限，读取无授权业务副作用。
12. 非管理员旧目标 Get/Manage（包括目标为自己）仍 403；新本人方法不能输入他人/筛选或绕过精确分派。无管理员初始化标记、无邮箱/恢复能力仍可读合法本人；SYSTEM、禁用/关闭、旧身份代际、错 audience、OAuth/service JWS 均拒绝。
13. 读取与授撤/账号禁用并发保持合法观察；权限/版本损坏、事务失败与未知结果、入口关闭及限流均不补空集合。HTTP 显式空数组、缺字段/null/畸形资源拒绝，原生 gRPC 零项资源、int64 精度和未来合法未知 ID 的消费均覆盖。
14. Gateway 精确 route、三协议与 ADMIN HTTP surface 的 Session 信任链、伪造内部头清理、错误 reason/no-store 透传；Console 非管理员单项按钮、主体/版本/Session/attempt 隔离、确认前显式读取、迟到拒绝和未知只读核对。App 继续各自精确写鉴权及双 revision，不把本人观察当权限证明。

## 实现依赖与交付边界

原管理基线复用 UC004 的权限集合、共享 revision、审计 repository 与 UC021 的管理员在线复核，并已扩展 UC010/App audience 投影；继续使用独立 allowlist、API 和错误语义，不能扩大 UC004 的审核权限接口。本次本人读取不再扩展身份 claim 或 App verifier allowlist。

原管理员权限管理后端已交付；本次本人读取已 ACCEPTED，实施与验证进行中。只读核对 Auth `bddd98f`、API `6fea3db`、Gateway `9d6a27f`、Console `bd43c3a`、App `a95bd13`：现有服务只有目标 Get/Manage，Auth transport 和 repository 都要求完整管理员；App UC028 状态 Get 只证明三项权限的 OR，不能发现精确能力。本轮按本节交接实施这些仓库；不以旧测试推断新接口已完成。

### 本次设计依赖检查与交接

| Owner | 审核后工作及验收边界 |
| --- | --- |
| API / Auth | 在既有 package 新增精确空请求及最小资源；固定 Proto 提交并生成客户端/descriptor；Auth 同时补 transport 精确普通 USER 分派、在线账号版本确认和同次权限投影。不能只放宽 middleware 或跳过 repository 的一层管理员检查。旧 Get/Manage 的注释、入口和授权回归保留；不复用依赖邮箱/恢复门禁的管理 snapshot。 |
| Gateway | 消费固定 API 提交，按 [待审路由增量](../../platform/contracts/auth-center-api-routing.md#uc027-本人运维权限读取) 补精确 route、typed unary adapter、descriptor 与生成物。复用 UC-GW-001/007，无新身份策略，不需新 Gateway UC；验证三协议及独立 ADMIN HTTP surface。ADMIN 表示 Console surface，不是完整管理员业务资格。 |
| Console | 先审核 UC-CONSOLE-015 修订，再消费含新 RPC 的固定 API 提交与官方生成客户端；App 运维发现独立于完整管理员发现，按本人精确集合启用动作。保持 BrowserSession 无 permissions、BFF 不聚合权限、不返回原始 JWS，旧未交付时的受限只读行为继续有效。 |
| App / 联合验收 | App UC028 与代码无需新增接口或修改命令字段/授权。使用正式授权入口与真实链按 Auth → Gateway → Console 串行验证四组合、授撤、Session/账号变化及各自拒绝；固定各提交/镜像，未闭合时不得开放新控件或宣称联合完成。 |

2026-11-04 接受前依赖复核结论：普通 USER 身份链、共享权限版本、Auth 事务栅栏及 Gateway 既有策略足以支撑设计，无需新账号角色或信任 ADR；**新增 API、精确鉴权分派、Gateway 路由和 Console 消费均未交付**。用户本轮已明确接受并授权实施；同步状态后脚本生成 brief，按交接串行实现。该段是接受前历史。当前固定 API 与 Auth 交付见[实现记录](../implements/UC-AUTH-027-own-read-readiness.md)；生产开关和消费者联合验收仍独立。

## 变更记录

- 2026-10-06：建立首版提案；固定 suspend/restore 两项独立权限、平台管理员管理但不自动获得操作权、共享 permissionRevision 和 App audience 最小投影。因 UC-AUTH-026 已用于 Application 关闭协议，本用例使用下一个可分配编号 UC-AUTH-027。
- 2026-10-06：接受 Auth/API 后端工作包；App 暂停/恢复状态机继续独立设计和实现，实际 consumer 联合验收作为交付边界保留。
- 2026-11-04：新增本人最小有效权限读取修订，BR-AOP-007/008、API/Gateway/Console 交接及验收矩阵；当前修订 DRAFT 待用户审核，旧管理基线继续有效。仅改设计并脚本刷新审核用 brief，未实现/部署。
- 2026-11-04：用户明确接受本次本人读取/消费修订并授权实现；依赖复核通过，同步 ACCEPTED 后脚本生成 brief，开始串行实施；未授权自动 commit/push 或生产启用。


<a id="proposed-application-search"></a>
## 2026-11-08 已接受的搜索权限交付

本节保留原审核链接。用户已接受的语义已合入 BR-AOP-001–008 正文。复用现有三项 RPC 和消息字段，固定 allowlist 及目标响应、本人公开范围扩为三项，继续按精确 ID 字典序输出。人员搜索由 UC039 拥有。

本轮使用 Auth 自己的 API 分支，现有字符串 permission 和重复结果足以承载 search；保留 App 正在修改的 API 工作树。存储和审计复用既有集合，无需迁移或默认 grant。部署新版签发器前只读核对历史同名授权。

验收使用同一真实 Session，正式授予/撤销 search 后读取本人集合并新签 App JWS，验证无→有→无、Auth audience 隔离、其他授权保持有效、共享版本并发和审计回滚。App UC051 的实际目录/摘要鉴权由其工作包验收。
