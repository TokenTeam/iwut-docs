<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-027 --spec tools/brief-specs/UC-AUTH-027.json -->
# Brief — UC-AUTH-027：管理应用平台运维权限

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-027` 管理应用平台运维权限 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-AOP-001`–`BR-AOP-008`（8 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-center-api-routing.md`、`platform/contracts/auth-session-identity-issuance-v1.md`、`platform/contracts/trusted-identity-v1.md` |

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

平台管理员在 Auth Center 中分别授予或撤销用户的 `app.application.search`、`app.application.suspend` 与 `app.application.restore` 原子权限，使 App Center 能依据短期可信用户身份授权平台级 Application 目录与最小摘要读取、暂停与恢复操作，并为每次权限变化留下不可变审计。

本用例只管理人员权限，不暂停或恢复任何 Application。Application 平台目录的集合、过滤与字段由 App 对应搜索用例拥有。Application 的平台暂停状态、恢复条件、运行与目录门禁、状态 revision 和业务审计由 App UC028 拥有。Application 当前管理员对自己应用的转让、关闭、发布和可恢复归档继续依据 App Center 的 `adminId` 与对应用例授权，不需要也不能借此取得平台运维权限。

本用例不提供任意权限编辑接口，不复用 `app.profile.review` 或 `app.version.review`，不把 Developer、Reviewer、Application 管理员或平台管理员自动转换为应用运维人员。三项权限不进入 OAuth Scope Catalog，不能由第三方应用申请，也不能通过用户 consent 获得。

本次修订增加任意有效 ACTIVE USER 的本人有效运维权限读取，使独立运维人员无需成为平台管理员即可发现自己能执行的动作。不提供他人查询特例、通用权限目录或权限证明，不改变管理员管理入口和 App 写命令的鉴权。

### 参与者与依赖

- **管理操作人**：ACTIVE USER，持有 audience=`iwut-auth-center` 的可信 USER JWS；JWS 包含 `auth.platform-admin.manage`，Auth 在线复核其当前完整平台管理员资格。
- **本人读取者**：任意有效 ACTIVE USER，沿同一 SESSION → Auth audience USER JWS 信任链；不要求完整管理员资格、App 运维权限、Developer 或 Reviewer 资格。此入口的目标只能是该身份的 authId。
- **目标用户**：明确 `subjectAuthId` 对应的 ACTIVE USER。SYSTEM、未知用户与 CLOSED 账号不能获得权限；Developer 或 Reviewer 资格不是前提。
- **Auth Center**：唯一保存人员权限、共享 `permissionRevision` 和授权审计，并通过 UC010 投影到 App audience JWS。
- **App Center**：只消费 audience=`iwut-app-center` 的已签名权限 claim，按 [UC-APP-028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md) 执行精确权限检查；不保存另一份 grant。
- **Gateway / Console**：分别复用精确 SESSION 路由与当前 BrowserSession 绑定读取；只消费本人最小投影，不向浏览器披露 JWS，不把权限放进 BrowserSession。

依赖 [UC021](../use-cases/UC-AUTH-021-manage-platform-administrators.md) 的管理授权、[UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md) 的账号状态与版本、[UC010](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md) 的可信身份签发，以及 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md)。本人读取只复用普通 USER 在线身份确认，不以 UC021 初始化标记或完整管理集合为前置。App 状态机由 UC-APP-028 拥有，Console 消费见 [UC-CONSOLE-015](../../console/use-cases/UC-CONSOLE-015-manage-platform-governance.md) 的已接受修订；设计、后端交付与联合验收分别记录。

### 输入与输出

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

本人响应只包含上列三个字段，不返回 granted、grantBlockers、accountStatus、管理员资格或其它 permissions。精确集合、空集合、并发和失败语义由 [BR-AOP-007](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-007)、[BR-AOP-008](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-008) 定义；它不是管理员管理资源的裁剪复用。

授予目标首版要求 ACTIVE USER、已有激活邮箱且邮箱恢复部署就绪；这些条件与高权限账号的可恢复性有关，不表示邮箱是真实身份认证。撤销允许目标为 ACTIVE 或 DISABLED，不因邮箱缺失或邮件服务不可用受阻。grantBlockers 固定按 `ACCOUNT_DISABLED, EMAIL_REQUIRED, EMAIL_RECOVERY_UNAVAILABLE` 顺序返回适用于所查询目标的公共门禁；某项是否已经授予由对应 permission 的 `granted` 表达。提交时仍须重新检查。

### API 契约

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

### 主流程

#### 授予或撤销

1. 验证可信身份、精确方法、参数与入口限额；确认 permission 严格属于三项 allowlist。
2. 在 Auth 认证事务协调边界中在线确认操作人是 ACTIVE USER 且持有 UC021 完整平台管理员资格。
3. 读取目标账号、权限集合、邮箱绑定与共享 `permissionRevision`；损坏数据失败关闭。
4. 比较 expectedPermissionRevision。GRANT 复核目标 ACTIVE、激活邮箱和恢复就绪；REVOKE 只要求目标当前持有所选权限。
5. 仅修改选定权限，保留其余平台权限、两项审核权限、管理权限和其它合法权限；严格增加一次共享 revision。
6. 权限更新与 append-only 审计在同一事务提交，成功后返回同一提交结果的完整三项状态。

重复 GRANT/REVOKE 或 stale revision 返回冲突，不增加 revision 或审计。事件 ID 在事务重试前生成并保持稳定；提交结果未知时返回不可用，客户端通过 Get 读取权威状态，不能盲目改用新 revision 重放。

#### 查询

只有当前有效的平台管理员可以调用原 `GetApplicationOperationsPermissions`，即使 subjectAuthId 是自己也不例外。Get 对存在且结构合法的 ACTIVE 或 DISABLED USER 返回三项状态；不存在、SYSTEM、CLOSED 或损坏目标不伪装成普通未授权用户。鉴权先于目标读取，未授权调用者不能借错误差异枚举账号。

#### 本人读取

1. 按精确 full method 选择普通 USER 身份分支，校验签名、issuer、audience、typ、时间、唯一载体与请求；不得要求 JWS 包含管理员或 App 运维 permission。未知方法继续失败关闭。
2. 在现有认证事务协调边界中，以身份 authId 为唯一键复核当前 USER、ACTIVE 和 accountRevision；同次读取权威 permissions 及共享 permissionRevision。不能依据入站 JWS 的权限 claim 计算本次集合。
3. 严格校验完整权限数据及版本后，按 BR-AOP-007 投影本人最小资源；不查邮箱、不调用 `RequireAdministratorTx` 或管理员管理 snapshot，不引入恢复部署、初始化标记或管理 bundle 前置。
4. 返回同次观察的完整集合与版本，或按 BR-AOP-008 失败。读取不修改 grant、permissionRevision 或授权业务审计；允许复用既有认证事务技术协调，不建立新业务写入。

### 错误语义与运行约束

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

### 验收场景

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

### 实现依赖与交付边界

原管理基线复用 UC004 的权限集合、共享 revision、审计 repository 与 UC021 的管理员在线复核，并已扩展 UC010/App audience 投影；继续使用独立 allowlist、API 和错误语义，不能扩大 UC004 的审核权限接口。本次本人读取不再扩展身份 claim 或 App verifier allowlist。

原管理员权限管理后端已交付；本次本人读取已 ACCEPTED，实施与验证进行中。只读核对 Auth `bddd98f`、API `6fea3db`、Gateway `9d6a27f`、Console `bd43c3a`、App `a95bd13`：现有服务只有目标 Get/Manage，Auth transport 和 repository 都要求完整管理员；App UC028 状态 Get 只证明三项权限的 OR，不能发现精确能力。本轮按本节交接实施这些仓库；不以旧测试推断新接口已完成。

#### 本次设计依赖检查与交接

| Owner | 审核后工作及验收边界 |
| --- | --- |
| API / Auth | 在既有 package 新增精确空请求及最小资源；固定 Proto 提交并生成客户端/descriptor；Auth 同时补 transport 精确普通 USER 分派、在线账号版本确认和同次权限投影。不能只放宽 middleware 或跳过 repository 的一层管理员检查。旧 Get/Manage 的注释、入口和授权回归保留；不复用依赖邮箱/恢复门禁的管理 snapshot。 |
| Gateway | 消费固定 API 提交，按 [待审路由增量](../../platform/contracts/auth-center-api-routing.md#uc027-本人运维权限读取) 补精确 route、typed unary adapter、descriptor 与生成物。复用 UC-GW-001/007，无新身份策略，不需新 Gateway UC；验证三协议及独立 ADMIN HTTP surface。ADMIN 表示 Console surface，不是完整管理员业务资格。 |
| Console | 先审核 UC-CONSOLE-015 修订，再消费含新 RPC 的固定 API 提交与官方生成客户端；App 运维发现独立于完整管理员发现，按本人精确集合启用动作。保持 BrowserSession 无 permissions、BFF 不聚合权限、不返回原始 JWS，旧未交付时的受限只读行为继续有效。 |
| App / 联合验收 | App UC028 与代码无需新增接口或修改命令字段/授权。使用正式授权入口与真实链按 Auth → Gateway → Console 串行验证四组合、授撤、Session/账号变化及各自拒绝；固定各提交/镜像，未闭合时不得开放新控件或宣称联合完成。 |

2026-11-04 接受前依赖复核结论：普通 USER 身份链、共享权限版本、Auth 事务栅栏及 Gateway 既有策略足以支撑设计，无需新账号角色或信任 ADR；**新增 API、精确鉴权分派、Gateway 路由和 Console 消费均未交付**。用户本轮已明确接受并授权实施；同步状态后脚本生成 brief，按交接串行实现。该段是接受前历史。当前固定 API 与 Auth 交付见[实现记录](../implements/UC-AUTH-027-own-read-readiness.md)；生产开关和消费者联合验收仍独立。

## 业务规则（UC-AUTH-027 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-001 -->
### BR-AOP-001：精确运维权限与职责分离

固定 allowlist 包含 `app.application.search`、`app.application.suspend` 和 `app.application.restore`。search 仅供 App 全平台 Application 目录及最小摘要读取，suspend 只允许 App UC028 把可运行 Application 置为平台暂停，restore 只允许按该用例的恢复门禁解除平台暂停；任一权限都不授予审核、发布、转让、关闭、归档、OAuth client 管理或人员授权能力。

三项权限独立授予。search 不授予暂停、恢复、审核或 owner 私有详情读取权；其他两项也不授予 search。只持有 suspend 的值班人员不能恢复，只持有 restore 的人员不能制造暂停。App Center 不接受 `app.application.*`、`app.*` 或通用 `app.application.manage` 通配能力，也不能把其中一项推导为另一项。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-002 -->
### BR-AOP-002：平台管理员负责授权但不自动获得操作权

UC021 的平台管理员固定 bundle 不包含三项 App 平台权限。完整平台管理员可以通过本用例管理权限，但若要亲自搜索、暂停或恢复 Application，仍须显式向自己的 authId 授予对应权限。Developer、Reviewer、Application 当前管理员和 SYSTEM 均不因身份自动获得这三项权限。

首版复用完整平台管理员资格作为管理授权，不增加 `auth.application-ops.manage`。若未来需要把人员权限管理员从平台管理员中拆分，应另立 UC 修改授权模型，不能把 App 操作权限本身当作授予他人的权限。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-003 -->
### BR-AOP-003：共享权限版本与原子审计

三项平台权限与现有审核、管理权限共用 `auth_principals.permissions` 和正数 `permissionRevision`。每次真实变化严格增加一次 revision；不同权限管理用例对同一目标使用相同旧 revision 并发时最多一个成功，不得通过独立版本覆盖另一项变化。

复用 `auth_permission_audit_events`，事件保存 eventId、actorAuthId、subjectAuthId、精确 permission、GRANT/REVOKE、reason、before/after、before/after revision 与 occurredAt。权限和审计同事务提交；审计失败全部回滚。不得记录邮箱、Session、学生信息或 JWS。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-004 -->
### BR-AOP-004：Audience 最小投影与撤销窗口

UC010 的 `iwut-app-center` allowlist 增加三项平台权限；`iwut-auth-center` audience 不投影它们。Auth 仅从当前权威权限集合签发，App 只接受 audience 正确、签名和时间有效的 USER JWS，不接受 OAuth scope 或客户端自报 permission。

撤销提交后 Auth 不再签发包含该权限的新 JWS。已经签出的 JWS 仍可能在 `exp` 与消费方 clock skew 范围内被 App 接受，传播上界沿用 UC010 当前默认 60 秒、可配置 1–300 秒的短期身份模型。首版不为此能力引入每请求 introspection、denylist 或 Redis；若未来要求立即撤权，必须通过独立 ADR 修改共同信任模型。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005 -->
### BR-AOP-005：账号状态、恢复能力与授权事实

只有 ACTIVE USER 且具备激活邮箱和部署就绪恢复能力时可以 GRANT。账号被禁用时保留三项 grant 事实但不生效，Auth 不向该账号签发新的可信身份；账号恢复后仍须重新登录，既有 grant 可再次投影。账号 CLOSED 后由 UC025 的清理和保留规则处理，不作为可查询运维人员继续存在。

撤销不要求目标仍有邮箱或恢复能力，避免无法收紧权限。授予和撤销不改变 Developer、Reviewer、平台管理员、Session、设备凭据或 OAuth 状态。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-006 -->
### BR-AOP-006：Auth 授权与 App 业务状态分离

Auth 只回答“哪个 USER 当前被授予哪项运维能力”。Application 是否 ACTIVE、已暂停、CLOSING/CLOSED、谁发起过暂停、是否满足恢复条件，以及暂停对目录、启动解析、审核和 OAuth 的影响，全部由 App Center 的 Application suspension 用例定义并持久化。

App UC028 的暂停/恢复命令必须分别检查精确权限并记录其自身业务审计；不能仅凭 Auth grant 修改数据库，也不能要求 Auth 持有 applicationId 状态。CLOSING/CLOSED 不得通过 restore 权限恢复，所有者自助归档不得复用平台 suspension 字段。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-007 -->
### BR-AOP-007：本人最小有效权限集合

`GetOwnApplicationOperationsPermissions` 只允许有效 ACTIVE USER 查询自己；不要求先持有任一公开权限。响应 subjectAuthId 必须严格等于可信身份 authId，首版公开 allowlist 只有 BR-AOP-001 的三项权限。effectivePermissions 是该公开范围内本次读取的完整有效集合，按 BR-AOP-005 的既有效力规则计算，不因读取附加邮箱或恢复就绪条件，不直接透传全量人员 permissions。

集合不分页、不截断、不返回部分成功；无重复并按 permission 字典序输出。合法普通用户和没有另获 App grant 的完整管理员均成功返回 `[]`；仅 suspend 返回 `["app.application.suspend"]`，仅 restore 返回 `["app.application.restore"]`，suspend/restore 都有返回 `["app.application.restore", "app.application.suspend"]`；仅 search 返回 `["app.application.search"]`；三项都有返回 `["app.application.restore", "app.application.search", "app.application.suspend"]`。只有成功完整响应中已公开 ID 的缺席才表示该项当前不生效，不能外推其它权限。

以后只有经对应业务设计审核接受才能扩大公开 allowlist，无需增加逐项布尔字段或客户端查询清单。客户端只按认识的精确 ID 启用已有动作；合法但不认识的新增 ID 不使资源解码失败，也不生成新按钮、推导同前缀权限或扩大授权。ID 必须是非空合法 UTF-8 字符串，不含空白或 `*` 通配；禁止 trim/大小写归一化、重复项及错类型。首版服务端只会输出上述三个 ID，不预先授权通用权限发现。

<!-- 权威位置: use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-008 -->
### BR-AOP-008：本人读取的一致性与失败关闭

当前账号/身份代际、权威权限集合和正数共享 permissionRevision 必须在同一 Auth 认证事务协调边界内形成观察。读与授权变更并发可以观察合法提交顺序中的前或后状态，不得混合不同版本的集合与 revision；撤销已经提交后发起的新读取必须反映该 ID 移除及新 revision。其它人员权限变化也可能推进共享 revision，不据版本变化推断是哪项授权改变。

身份缺失、失效、未知、SYSTEM、DISABLED/CLOSED 或 accountRevision 不匹配按身份拒绝处理，不返回成功空集合或目标管理 404。账号/权限记录结构损坏（包括非法/重复权限项）、版本缺失/非正数/类型错误、存储/事务失败均返回不可用；不能忽略坏数据后返回剩余集合。429、协议错误、关闭入口、网络错误和依赖失败都不是“无权限”。成功及错误响应均 `Cache-Control: private, no-store`。

本人资源仅是本次观察，不是整个 Session 的授权租约或 App 可消费凭据。读取后再撤销仍由 App 精确命令鉴权和 BR-AOP-004 的既有短期 JWS 窗口约束；permissionRevision 不新增 App 命令参数，不提供每请求 introspection 或即时撤权承诺。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-center-api-routing.md`：Auth Center API 路由与 HTTP 映射

#### 路由边界

UC038 新增已接受的本人读取 `/auth_center.v1.script_permission.ScriptPermissionService/GetOwnScriptPermissions`，GET `/v1/users/me/script-permissions`，空请求返回本人四项状态和共享版本。Gateway 采用 SESSION → Auth audience、ADMIN Console surface，原生 gRPC/HTTP/gRPC-Web 按精确方法接入。该本人方法不要求管理或脚本 permission，目标管理方法沿原规则鉴权。开关、无权限与失败区分唯一见 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#br-smp-004)。


UC039 的 `ManagedUserSearchService/SearchUsers` 使用 `POST /v1/managed-users:search` 和原生 gRPC，业务及最小披露见 [UC039](../use-cases/UC-AUTH-039-search-users-for-administration.md)。Gateway 接入时使用 SESSION → Auth audience，限定 Admin surface。UC027 的固定管理和本人公开范围已接受增加精确 `app.application.search`，沿用现有方法及线格式。


UC038 的目标脚本权限查询和授撤方法按 [UC038 API 契约](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#api-契约) 固定 HTTP 和原生 gRPC。Gateway 按精确 RPC 接入 Admin 管理路由，采用 SESSION → Auth audience USER JWS，管理权限由 Auth 复核。旧 `ScriptMaintainerPermissionService` 及其两条 HTTP 路由退役。

2026-10-12 下表仅已交付基线。密码管理/恢复、默认密码登录已展开 UC033/034 DRAFT 和 auth-password-v1 草案，未注册真实入口；旧 REGISTER/BIND/凭据撤销、注销 Prepare/app.close Complete 须同步密码与防旁路门禁，新修订未实施，不提前启用或登记虚构公网清单。

与 [App API 路由](../../platform/contracts/app-center-api-routing.md) 一致，Proto 只声明服务内部 `/v1/...` 路径。
Gateway 公共入口前缀为 `/auth-center`，在转发前剥离；原生 gRPC full method 不加前缀。
UC004–009 的 HTTP 绑定由 Auth 后端实现。Gateway 的路由与认证编排按
[UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 独立交付。

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/device-logins` | AuthenticationService/BeginDeviceLogin | DIRECT | 200 |
| POST | `/v1/device-logins/{operation_id}/completion` | AuthenticationService/CompleteDeviceLogin | DIRECT | 201 |
| DELETE | `/v1/sessions/current` | AuthenticationService/RevokeCurrentSession | DIRECT | 200 |
| DELETE | `/v1/users/me/credentials/{credential_id}` | AuthenticationService/RevokeOwnCredential | DIRECT | 200 |
| GET | `/v1/users/me/profile` | UserProfileService/GetOwnProfile | SESSION | 200 |
| PATCH | `/v1/users/me/profile` | UserProfileService/EditOwnProfile | SESSION | 200 |
| GET | `/v1/user-profile-schema` | UserProfileService/GetProfileEditingSchema | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/ManageReviewerPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/reviewer-permission` | ReviewerPermissionService/GetReviewerPermission | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-review-permissions/{permission}` | ReviewerPermissionService/ManageApplicationReviewPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-review-permissions` | ReviewerPermissionService/GetApplicationReviewPermissions | SESSION | 200 |
| PUT | `/v1/users/{subject_auth_id}/application-operation-permissions/{permission}` | ApplicationOperationsPermissionService/ManageApplicationOperationsPermission | SESSION | 200 |
| GET | `/v1/users/{subject_auth_id}/application-operation-permissions` | ApplicationOperationsPermissionService/GetApplicationOperationsPermissions | SESSION | 200 |
| GET | `/v1/academic-year-policy/schedule` | AcademicYearPolicyService/GetAcademicYearSchedule | SESSION | 200 |
| PUT | `/v1/academic-year-policy/schedule/next-rollover` | AcademicYearPolicyService/UpdateNextAcademicYearRollover | SESSION | 200 |
| DELETE | `/v1/users/me/application-user-storage/{application_id}` | ApplicationUserStorageService/ClearOwnApplicationUserStorage | SESSION | 200 |

原 `/v1/registrations` 和 completion 路径不注册，旧 BeginUserRegistration/CompleteUserRegistration RPC 返回 UNIMPLEMENTED；不重定向、不代为发起注册，也不因启用用户入口恢复旧方法。

UC011 是唯一注册入口，三个 DIRECT 路由的字段及 Session 例外见[邮箱协议 v2](../../platform/contracts/auth-email-binding-v2.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-bindings` | EmailBindingService/BeginSetEmail | DIRECT | 200 |
| POST | `/v1/email-bindings/{operation_id}/completion` | EmailBindingService/CompleteSetEmail | DIRECT | 200 |
| GET | `/v1/users/me/email-binding` | EmailBindingService/GetOwnEmailBinding | DIRECT | 200 |

EmailBindingService package 为 `auth_center.v1.email_binding`；额外受 AUTH_EMAIL_BINDING_ENABLED 开关控制，默认不启用。DIRECT 不得将空/坏 Session 清理成缺失 Session。

UC012 追加独立的邮箱登录 DIRECT 路由，见 [邮箱登录协议](../../platform/contracts/auth-email-login-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/email-logins` | EmailLoginService/BeginEmailLogin | DIRECT | 200 |
| POST | `/v1/email-logins/{operation_id}/completion` | EmailLoginService/CompleteEmailLogin | DIRECT | 201 |

EmailLoginService package 为 `auth_center.v1.email_login`，由 AUTH_EMAIL_LOGIN_ENABLED 独立控制，默认关闭；两个入口拒绝任何已提供的 x-iwut-session。Complete body 为 code 和 proof，路径 operation_id 覆盖体中值。

UC013 追加两个必需有效 Session 的 DIRECT 路由，字段与认证约定见 [Developer 自助申请协议](../../platform/contracts/auth-developer-application-v1.md)：

| HTTP method | Auth 服务内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

DeveloperApplicationService package 为 `auth_center.v1.developer_application`，由默认关闭的 AUTH_DEVELOPER_APPLICATION_ENABLED 控制。Apply body 必须包含 developerHandle（例如 `{"developerHandle":"alice"}`）；GetOwn 无 body；均拒绝 query。DIRECT 保留 Session，不提前交换 Developer JWS。部署恢复就绪声明见 UC013，不由客户端提供。

ReviewerPermissionService package 为 `auth_center.v1.reviewer_permission`，四个管理/查询方法均由 Auth 校验 auth.reviewer.manage；路由 SESSION 身份本身不授予管理权。旧 reviewer-permission 路由继续只操作版本审核权限；新路由的目标 allowlist、消息字段和兼容规则唯一见 [UC004 API 扩展与兼容](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#api-扩展与兼容)。新路由属于 2026-10-03 扩展，Auth/API/Gateway 实现与联合验收已完成，见 [交付记录](../implements/README.md#2026-10-03-uc004010-应用审核权限扩展)；生产部署仍沿用下述用户入口开关。

ApplicationOperationsPermissionService package 为 `auth_center.v1.application_operations_permission`，两个方法由 Auth 校验当前完整平台管理员资格；SESSION 身份本身和 App 操作权限都不能管理他人权限。精确 allowlist、共享 revision、邮箱恢复门禁及投影边界唯一见 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md)。入口默认关闭；App Center 的暂停/恢复业务路由不属于本契约。

AcademicYearPolicyService package 为 `auth_center.v1.academic_year_policy`，两个方法由 Auth 在线复核当前完整平台管理员资格；精确时间、递推、并发和审计语义唯一见 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md)。管理入口由独立 `AUTH_ACADEMIC_YEAR_POLICY_ENDPOINTS_ENABLED` 控制且默认关闭；关闭管理入口不影响 Auth 内部消费已 provision 的时间表。

ApplicationUserStorageService package 为 `auth_center.v1.application_user_storage`。本人清除使用 SESSION 身份，`application_id` 仅由路径绑定，一次删除该用户与 Application 的 TEST/GREY/STABLE 数据，不返回应用 key/value。第三方读写另使用 `POST /v1/application-user-storage:batchGet` 与 `POST /v1/application-user-storage:mutate`；两者是 Auth 直接验证 opaque OAuth Bearer token 的 HTTP-only 资源端点，不经 SESSION 转换、不生成原生 gRPC 第三方方法。三个入口均由 `AUTH_APPLICATION_USER_STORAGE_ENABLED` 控制且默认关闭，精确语义见 [UC030](../use-cases/UC-AUTH-030-manage-application-user-storage.md)。

AuthenticationService package 为 `auth_center.v1.authentication`；UserProfileService package
为 `auth_center.v1.user_profile`。DIRECT 不代表无鉴权：各方法继续遵守设备证明、token 定向
撤销或有效 Session 的独立边界。SESSION 路由须经 Gateway 签发 `iwut-auth-center` audience
的可信用户 JWS；直接调用 Auth 时仅传 Session 不能访问资料接口。

Scope Catalog、UC002 内部批量 Developer 状态查询、SYSTEM principal 查询及 UC010 Session-to-JWS 签发
继续是内部 gRPC API，不增加 HTTP annotation，也不开放终端路由。

#### JSON 与载体

UC036 的 `auth_center.v1.scope_management.ScopeManagementService` 提供三个 SESSION 管理方法：POST `/v1/scope-catalog:get`、POST `/v1/scope-catalog:change`、POST `/v1/scope-catalog/operations:get`，分别为 GetManagedScopeCatalog、ChangeScopeCatalog、GetScopeCatalogOperation。独立 `AUTH_SCOPE_MANAGEMENT_ENABLED` 缺省关闭，在线复核当前完整平台管理员，不增加权限或 service 写权。正文上限 128 KiB；严格解码/no-store/原生 gRPC；精确语义唯一引用 [UC036](../use-cases/UC-AUTH-036-release-scope-enablement-changes.md#api-契约)。UC001 内部 ScopeCatalog 只读方法不变，Gateway 实际路由清单另行交付，不因本文登记自动开放。

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

#### UC027 本人运维权限读取

状态：`ACCEPTED`，2026-11-04 用户接受并授权实现；登记 [UC-AUTH-027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#api-契约) 本次修订的跨系统路由输入，不属于上方历史已交付清单；本地实施获授权，生产启用仍需独立验收。原两个管理员 Get/Manage 的 SESSION 策略和完整管理员门禁不变。

| 项 | 设计固定值 |
| --- | --- |
| RPC full method | `/auth_center.v1.application_operations_permission.ApplicationOperationsPermissionService/GetOwnApplicationOperationsPermissions` |
| Auth 内部 HTTP | `GET /v1/users/me/application-operation-capabilities` |
| Gateway HTTP | `GET /auth-center/v1/users/me/application-operation-capabilities` |
| 路由标识 | `auth.get-own-application-operations-permissions` |
| 策略 / 目标 | `AUTH_USER`（SESSION → audience=`iwut-auth-center` USER JWS）；targetService=`auth-center` |
| 协议 / Console surface | `HTTP_JSON, GRPC, GRPC_WEB`；只有 HTTP/JSON 声明 `consoleSurfaces: [ADMIN]` |

ADMIN 是 Console Host/surface，不表示 Auth 平台管理员资格。按 [UC-GW-001](../../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 的 SESSION 策略及 [UC-GW-007](../../gateway/use-cases/UC-GW-007-compose-console-session-forward-auth.md) 组合现有 BFF Session ForwardAuth → Gateway USER 交换，移除客户端伪造内部身份，Session 不下传 Auth。原生 gRPC/gRPC-Web 沿既有 Session 入口，不从 Console Cookie 创建 Session。无新 Gateway 策略或 UC，不扩大 service/package/path 通配。

请求、响应、错误及效力唯一引用 UC027 的 BR-AOP-007/008；本人读取不借旧管理方法的管理员资格/邮箱恢复路径。BrowserSession 不增加 permissions，BFF 不计算或聚合权限、不返回 JWS。成功及错误透传 private/no-store；入口关闭、身份/存储/协议失败不合成为 200 或空集合。

交付顺序：用户审核 UC027/UC-CONSOLE-015 → API/Auth 固定新增 Proto 与生成物提交并实现/验证 → Gateway 固定该输入，补精确 route、typed unary proxy、descriptor/Traefik 生成物及三协议测试 → Console 固定客户端并验证对应按钮。关闭/缺失新方法时保持既有受限行为，不改道旧 Get、匿名或 App 写入。Auth 已固定包含此方法的 API，发布和精确路由交接见 [UC027 交付记录](../implements/UC-AUTH-027-own-read-readiness.md)。Gateway/Console 是否完成以各自验证记录为准。

### `platform/contracts/auth-session-identity-issuance-v1.md`：Session 到可信用户身份签发 v1

#### 内部 RPC

独立 API 路径 `auth_center/v1/identity/identity.proto`，package `auth_center.v1.identity`：

```text
/auth_center.v1.identity.UserIdentityService/IssueUserIdentityFromSession

IssueUserIdentityFromSessionRequest {
  string audience = 1;
}
IssuedUserIdentity {
  string identity_jws = 1;
  int64 expires_at_unix_seconds = 2;
}
```

以上为设计线格式，正式 Proto 及生成代码在实现时进入独立 API 仓库。首版仅 unary 原生 gRPC；不注册终端 HTTP、gRPC-Web 或网关公开路由。

- `authorization`：由 Gateway 自己生成的内部服务 Bearer JWS，严格遵循 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md)，不能使用客户端 Authorization。
- `x-iwut-session`：本次终端请求提供的唯一 token，采用 [auth-device-session-v1 的 Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，消息体不重复承载。
- 不接收 `x-iwut-identity` 作为签发授权，也不通过 JWS 自身换取新 JWS。
- 目标 audience 精确匹配预登记值；无空白修剪、URL 解释或客户端动态指定。首批值为 `iwut-auth-center` 和 `iwut-app-center`。
- body、metadata、返回体均不得进入通用请求/响应日志；传输必须受保护。客户端 token 与服务 token 均不能透传给最终业务服务。

#### 应用审核权限投影

用户能力投影唯一遵循 [UC010 / BR-IDN-002](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#br-idn-002)：App audience 可携带用户实际拥有的 `app.application.search`、`app.profile.review`、`app.version.review`、`app.application.suspend` 与 `app.application.restore`；Auth 管理权限不因此下发给 App。审核权限由 [UC004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md) 管理，运维权限由 [UC027](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md) 管理；均复用现有 `permissions` claim 和签发 RPC。平台管理员不会被自动投影为 Reviewer 或 Application 运维人员。

已接受的四项脚本权限按 [UC038](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md) 独立授撤，按 UC010 的 App audience 清单投影。继续使用现有 `permissions` claim、签发 RPC 和 caller audience 配置。App 作者沿用 UC010 的 `developer_status`。

#### 签名与验签配置

签发入口使用显式开关 `AUTH_IDENTITY_ISSUANCE_ENABLED`（默认 false）。开启要求现有 `AUTH_USER_ENDPOINTS_ENABLED=true`，且下述 signer 配置完整有效；关闭时不注册签发 RPC，不要求私钥，也不影响已有服务和用户接口。不得因为开关开启而放宽原有鉴权。

新增 signer 配置：`AUTH_USER_IDENTITY_SIGNING_KID`、`AUTH_USER_IDENTITY_PRIVATE_KEY_PEM_B64`、`AUTH_USER_IDENTITY_TTL`（默认 `60s`，1–300 整秒）。issuer 沿用 `AUTH_USER_IDENTITY_ISSUER`；既有 `AUTH_USER_IDENTITY_MAX_TTL` 是 verifier 接受上限，不是 signer 默认 TTL。

私钥使用严格标准 Base64 包装的 PKCS#1/PKCS#8 RSA PEM，至少 2048 bit。Auth 自己作为 audience 时必须部署匹配的 verifier 公钥；其他服务先部署新公钥，再切 signer kid，旧验签公钥覆盖旧 token 的有效期、允许时钟偏差和在途请求后才移除。签发 key 只为此用途配置，不复用学生关联加密/查找密钥或服务身份 key。

输出 identity_jws 不为空，单个 compact JWS，最多 16 KiB；权限投影过大导致超限时不截断权限，按签发不可用拒绝。Gateway 只检查可信 Auth 响应的有界形状、三段格式及必要剩余时间，不解读 claims 进行授权或重签；最终服务仍必须验签。

#### 与现有契约的衔接

- 终端不能经 Gateway 访问 ScopeCatalog、DeveloperStatusDirectory、SystemPrincipalDirectory 或签发 RPC；这些是服务到服务方法。不得仅凭 `/auth-center` 前缀自动开放。
- 本契约不改变 UC008 的幂等匿名 token 定向撤销例外，或 UC009 的有效 Session 授权；这两条 Gateway 路由均走 DIRECT，由 Auth 自己验证。
- Auth 用户资料及 UC004 新旧管理入口均走 SESSION，得到 audience=`iwut-auth-center` 的用户 JWS；不能因目标是 Auth 而递归触发签发。
- Gateway 只为外部用户请求编排身份。服务到服务调用继续使用独立 service JWS，不能借用某位用户的 Session。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 传输载体

- HTTP：请求头 `x-iwut-identity`（HTTP 头名大小写不敏感）。
- gRPC：metadata 键 `x-iwut-identity`（gRPC metadata 键为小写）。
- 值统一为一个 compact JWS：`<base64url(header)>.<base64url(payload)>.<base64url(signature)>`。
- 不允许 `Bearer ` 前缀或任何包裹；出现即视为无效身份。
- 一个请求最多携带一个身份值；出现多个值时全部拒绝，不得任取其一。

#### JOSE Header

JOSE header 是 JSON 对象，至少包含：

| 字段 | 必需 | 约束 |
| --- | --- | --- |
| `typ` | 是 | 必须**精确**等于 `JWT`（区分大小写；`jwt`、`JWS` 等变体一律拒绝） |
| `alg` | 是 | 必须等于 `RS256` |
| `kid` | 是 | 非空字符串；必须能解析到本地启动配置中的一把 RSA 公钥 |

`alg` 为 `none`、`HS*` 或任何非 `RS256` 值都必须拒绝。禁止根据 token 自带的 `jwk`/`x5u` 等字段在运行时拉取密钥。

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

`sub` 是身份主体，不是 `uid` 的同义词；当 Auth 的内部用户标识与 `authId` 不同时，以 `authId` 为准。`developer_status` 表达 Auth 权威给出的开发者资格结果，而不是 token 类型；字段缺失表示该主体是尚未进入 Developer 生命周期的普通用户，不表示 token 或身份无效。`permissions` 表达 Auth 在签发时授予该主体、且绑定本 token audience 的原子权限集合；App Center 运行版本审核消费精确值 `app.version.review`，公开资料审核消费 `app.profile.review`，平台暂停与恢复分别消费 `app.application.suspend` 与 `app.application.restore`；四项互不隐式授权。

消费方先验签并构造通用可信身份，再由具体入口要求自己的能力字段：

- Developer 入口缺少 `developer_status` 时，可信用户身份仍然有效，但不具备 Developer
  能力；UseCase 按授权失败拒绝，不能把缺失解释为 `PENDING` 或认证失败。
- Reviewer 决定入口缺少 `permissions` 或不含目标能力要求的精确权限时按权限不足拒绝：运行版本审核要求 `app.version.review`，公开资料审核要求 `app.profile.review`；Reviewer 不需要 `developer_status`。
- Application 平台暂停与恢复入口分别要求 `app.application.suspend` 与 `app.application.restore`；Application 管理员关系、Reviewer、Developer 或平台管理员身份不能替代精确权限。
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

#### 校验顺序

消费方必须按以下顺序校验，且在任何一步失败时立即以认证失败结束，不继续解析后续内容：

1. 从 HTTP header / gRPC metadata 取 `x-iwut-identity`；缺失、为空或存在多个值 → 认证失败。
2. 按 `.` 切分 compact JWS，必须恰好三段且每段非空 → 否则认证失败。
3. base64url 解码并解析 JOSE header；必须为 JSON 对象。
4. 校验 `alg = RS256`、`typ = JWT`、`kid` 非空且存在于本地 kid→公钥表。
5. 用该 kid 的 RSA 公钥对 ASCII 串 `<header>.<payload>` 做 RS256 验签；验签失败 → 认证失败。
6. base64url 解码并解析 payload；必须为 JSON 对象。
7. 校验 `iss`、`aud`、`sub`、`jti` 的存在性、类型和值；若能力字段存在，同时校验 `developer_status` 与 `permissions` 的类型和值。
8. 校验时间声称（见「时间与有效期」）。
9. 构造包含 `authId`、可选 Developer 状态和权限集合的可信身份并注入请求 context；具体入口再投影为自己的最小身份类型。

签名验证必须先于对 claims 的任何业务判断。步骤 3–5 只允许基于 header 选择公钥，不允许基于未验签的 payload 做授权决定。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

#### 密钥与轮换

- 消费方启动时加载一组 `kid → RSA 公钥` 映射；公钥以来自身份配置的 PEM 文件或等价明确配置提供。
- 至少配置一把公钥；`kid` 为空、重复或公钥无法解析时必须**阻止启动**，不得跳过或降级。
- 每把 RSA 公钥的模数至少 **2048 bit**；小于 2048 bit 的密钥必须**阻止启动**，不得降级接受。
- 轮换采用双密钥重叠：先发布新 kid 的公钥并让签发方开始使用新 kid，旧 kid 公钥保留到持有旧 token 的最长寿命（不超过 `maxTTL`）之后才移除。
- 未知 `kid` 一律认证失败，禁止回退到「唯一的公钥」或首次见到的密钥。
- 不在请求路径上拉取或刷新密钥。密钥分发是部署配置问题，不是每请求行为。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-027`（use-cases/UC-AUTH-027-manage-application-operations-permissions.md）：主流程/授予或撤销、主流程/查询、主流程/本人读取、实现依赖与交付边界/本次设计依赖检查与交接、变更记录、2026-11-08 已接受的搜索权限交付
- `platform/contracts/auth-center-api-routing.md`（docs 根级共享文档）：校园认证入口（UC031）、UC032 本人设备凭据管理、治理工作包路由、UC020 同账号 Session 管理
- `platform/contracts/auth-session-identity-issuance-v1.md`（docs 根级共享文档）：范围与权威来源、服务授权扩展、请求与凭据流向
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-027-manage-application-operations-permissions.md` | 245 | `9fd8067fe545` |
| `platform/contracts/auth-center-api-routing.md` | 171 | `ec86209bbd44` |
| `platform/contracts/auth-session-identity-issuance-v1.md` | 85 | `298ed207961b` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
