# 独立 App 运维人员：本人精确权限发现提案

状态：`PROPOSED`；2026-11-04。用户要求先核查并记录供审核的方案，本提案尚未接受，不授权实现。现行 UC-AUTH-027、UC-CONSOLE-015 及 App UC028 的已接受规则继续有效；本文不直接修改 Auth UC/BR、共享 Proto 或服务代码。

## 已确认的缺口

[UC-CONSOLE-015 的最小缺口](../../console/use-cases/UC-CONSOLE-015-manage-platform-governance.md#保留的最小缺口)真实存在。独立持有 `app.application.suspend` 或 `app.application.restore` 的人员不必是平台管理员；但现有 Auth `GetApplicationOperationsPermissions` 即使查本人，也先要求入口 JWS 中的 `auth.platform-admin.manage`，再在事务内 `RequireAdministratorTx` 复核完整平台管理员资格。[UC-AUTH-027 查询](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#查询)明确规定了这个门槛。

App 的 [UC028](../../app-center/use-cases/UC-APP-028-suspend-and-restore-application.md#输入输出与-api-草图) 状态 GET 允许两项权限的 OR，返回 Application 可用状态，不返回调用者究竟有哪一项权限。因此成功读取只能证明满足 OR 条件。Console 保持按 App ID 读取、写控件不可用，并且不用 suspend/restore 写请求试探权限，是正确的现行处理。

只读核对点：Auth `bddd98f` 的 `UserCapabilityIdentityMiddleware`、`ApplicationOperationsPermissionRepository.Get/authorize/snapshot`；Gateway `9d6a27f` 的精确 ADMIN/SESSION 路由与代理分派；App `a95bd13` 的 `ApplicationOperationsHandlers.Get/Suspend/Restore`；共享 API 的现有两种运维授权方法。Console `bd43c3a` 的 `governance.tsx` 亦先由 `OperationsDiscovery` 查询完整管理员资格，再运行 `ExactOperationsDiscovery`；未确认时保留按 ID 读取并传入空的写动作 allowlist。上述是本地源码证据，未调用真实环境，不代表已发布版本或联合链验收。

## 建议：新增独立的本人只读方法

建议扩展 UC-AUTH-027 的读取范围，增加 `GetOwnApplicationOperationsPermissions`，保留既有面向目标用户的管理 GET/PUT。新方法只允许读取调用者本人，不要求完整平台管理员资格，也不要求调用者已经持有任一 App 运维权限。

| 方案 | 取舍 |
| --- | --- |
| **新增本人只读 RPC（建议）** | 无可替换的目标参数；返回本人最小投影；与管理员目标读取、授权门禁及错误语义清楚分开。需要 API、Auth、Gateway、Console 的一次协作。 |
| 扩展既有 Get 的 actor=subject 特例 | 可以复用路由，但改变现行管理员专用方法的授权语义和响应披露；同一 RPC 混合本人发现与管理员目标读取，还会带出不需要的 granted、账号状态和 grantBlockers。不推荐作为本轮方案。 |

不将 permissions 放进 BrowserSession，不新建通用能力目录或 BFF 权限聚合。Auth audience 当前不投影这两项 App 权限；不能通过扩大该 audience allowlist、解析 App audience JWS 或把 JWS 返回浏览器来补此读取。

### 候选接口与最小读模型

在现有 `auth_center.v1.application_operations_permission.ApplicationOperationsPermissionService` 增加精确 RPC；候选 HTTP 绑定为 `GET /v1/users/me/application-operation-capabilities`，与现有 `/v1/users/{subject_auth_id}/application-operation-permissions` 的目标管理读取分开。请求为空，不接受 body、query、subjectAuthId、actor、目标权限或通配筛选；身份完全取可信请求上下文。

```text
GetOwnApplicationOperationsPermissions {}

OwnApplicationOperationsPermissions {
  subjectAuthId: AuthId             // 只来自当前可信 USER 身份
  permissionRevision: Int64         // 权威共享正数版本；ProtoJSON/int64 精确处理
  permissions: [                   // 固定两项，按 permission 字典序
    { permission: "app.application.restore", effective: Bool },
    { permission: "app.application.suspend", effective: Bool }
  ]
}
```

每项 effective 必须具有明确 presence（例如 Proto 的 optional bool），以便 HTTP/JSON 和原生 gRPC 都能区分“显式 false”与“字段缺失”；不得依赖无 presence 的 proto3 bool 默认值补 false。

字段名、tag 和路径在方案接受后由 Auth/API owner 同步到正式 UC 与可执行 Proto；本提案中的候选名称不作为已发布契约。响应不含其它 permissions、granted、grantBlockers、邮箱、Developer、平台管理员资格、Application 列表、Session 或原始 JWS。这里不增加账户/授权管理读模型；只回答本人本次权威读取观察到的两项有效能力。

`effective` 引用 [BR-AOP-005](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-005) 的既有效力规则，不引入新的授权条件。合法 ACTIVE USER 没有这两项授权时成功返回两个 false，不能把“没有授权”伪装成 403、404 或查询不可用。

| 本人的已保存授权 | restore.effective | suspend.effective |
| --- | --- | --- |
| 无两项授权，包括没有另获 App 权限的完整平台管理员 | false | false |
| 仅 suspend | false | true |
| 仅 restore | true | false |
| 两项都有 | true | true |

### Auth 身份、读取与失败语义

沿当前 Gateway SESSION → Auth audience USER 身份链，Auth 校验签名、issuer/audience/typ/时间及在线当前身份/账号版本，以调用者 authId 为唯一查找键。在现有认证事务协调边界中读取当前有效账号、权威 permissions 和共享 permissionRevision，返回同次观察的两项最小投影。

- 新方法不能进入现有“整个运维权限 service 都要求 admin.Manager”的分派分支；必须按精确 full method 区分本人读取与管理员 Get/Manage。只放宽 transport 或只跳过 repository 管理员检查，任一单层修改都不足以交付，也不得按 service 通配放宽。
- 不调用 `RequireAdministratorTx`，不依赖管理员初始化标记、完整管理 bundle、Developer 或 Reviewer 资格。复用普通 USER 的在线身份确认，不把普通 USER 变成管理员。
- 不直接复用现有管理 `snapshot()` 的邮箱/恢复配置和 grantBlockers 路径。已有 grant 的效力不因本人查询引入新的邮箱或部署恢复前置；授予时的门禁继续由原管理写入拥有。
- 身份缺失、失效、被禁用/关闭或在线版本不符，沿既有身份拒绝处理；不把它降级成两个 false。存储不可用、权限结构损坏、重复非法项目或版本异常失败关闭，沿 Auth 不可用语义处理，不合成“未授予”。429 与协议错误也不能解释为无权限。
- 读取不改变 grant、permissionRevision 或授权业务审计；现有认证事务的技术协调机制可以复用。响应及错误采用私有 no-store 策略；严格拒绝请求的未知/重复输入，不暴露其它用户的存在性。

“当前”指本次 Auth 权威读取的观察，不是整个 Session 生命周期的授权租约。查询与并发授权变更可以观察合法提交顺序中的前/后事实；不能从旧 JWS claim 推算当前值。撤销已提交后发起的新读取应观察到 false/更新后的共享版本。读取后的再撤销仍由实际命令鉴权及既有身份传播窗口约束。

### Gateway 与 Console 消费

Gateway 增加该精确方法的 ADMIN surface、SESSION、目标 Auth audience 路由和代理/descriptor；ADMIN 是 Console surface 名，不是平台管理员业务资格。复用既有 BrowserSession ForwardAuth，服务端换取并转发 USER JWS，浏览器接收最小资源。沿三个既有协议核对，不新增特权 BFF 旁路、权限判断或 Session 字段。

Console 的“应用平台运维”能力发现独立调用新方法，不再先要求平台管理员查询成功。人员资格管理仍使用现有完整管理员链；没有另获运维权限的管理员不能凭管理资格打开操作按钮。

- 读取成功须严格匹配当前 Session 的 authId，恰好包含两个已知 permission、每项显式布尔值及合法正数 int64；拒绝缺项、重复项、未知项目、错主体、非法版本或畸形成功，不补 false/true。生成/解码策略沿既有官方工具链，不手写第二套 DTO。
- suspend/restore 各用自己的 effective 与 Application 当前状态、双 revision 控制动作。打开/提交确认前完成当前 Session/attempt 的明确能力读取和目标专用状态核对；两个服务的 GET 不宣称原子快照。permissionRevision 仅作观察及旧确认失效依据，不新增 App 命令参数，也不是权限证明。
- 某项失效只关闭对应动作及旧确认；无两项权限时关闭 App 运维写入和相应私有范围，不影响独立 Reviewer 或人员治理。权限读取失败为“无法确认”，禁止据旧快照发新命令；现有按 App ID 的只读请求仍受 App OR 鉴权独立保护，不利用其成功反推精确写权限。
- Session 换代、离页、目标切换、迟到响应、读取/命令未知结果继续按 UC015 的 attempt 与 Query 身份隔离。能力不持久化进 BrowserSession、URL 或本地存储，不轮询续权，不发送写请求探权或自动重放。

App Suspend/Restore 继续独立检查各自精确权限、双 revision、生命周期和原事务门禁。本人发现不会消除 [BR-AOP-004](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#br-aop-004) 的既有短期 USER JWS 撤权窗口，不增加每请求 introspection 或即时撤权承诺。

## 审核后的协作顺序与所有权

1. **用户审核本提案**：重点是“新增本人最小读取，不放宽管理员目标 Get/Manage”和“ACTIVE 普通用户无授权返回两个 false”。未接受前继续现行 UC015 的受限只读行为。
2. **Auth 设计/实现 owner**：接受后修改 UC-AUTH-027 的参与者、本人读取、错误与验收，并登记相应 BR/registry、刷新 brief；完成普通 USER 在线身份确认、同次权威投影和精确方法分派。具体 Auth 源码修改由 Auth agent 承接，本 App 任务不越界实现。
3. **共享 API owner**：按被接受的正式 Auth 契约修改 App 运维权限相关 Auth Proto 与生成物，输入/输出一起提交。该工作属于 Auth API，不能沿用上轮“允许本任务修改 App 相关 Proto”的授权自行实施。
4. **Gateway owner**：消费固定 API 提交，新增精确 ADMIN/SESSION surface、代理和路由生成物，验证三协议、Session 与失败透传；不代替 Auth 计算权限。
5. **Console owner**：更新 UC-CONSOLE-015 对该缺口的接受说明、固定客户端输入和能力观察实现，再接入精确控件与恢复规则。本提案不修改已接受 Console 语义，也不先开放按钮。
6. **联合验收**：Auth → Gateway → Console，固定各提交/镜像后串行执行；遇到未解决的身份、路由或权限依赖即停止并交接。本轮 App 后端无需新增读取/写入，也不变更 UC028。

## 有界验收计划（尚未执行）

- 非平台管理员的 none / suspend-only / restore-only / both 四组合；完整管理员无 App grant 仍为双 false；身份或其它资格不能隐式授予 App 权限。
- 正式管理入口授予/撤销单项后，同一有效 Session 的新本人读取反映新共享版本和对应项目，另一项保持。读取与并发授权变更按合法快照取值；读取没有授权业务写入或业务审计。
- 非管理员旧的目标 Get/Manage 仍 403（包括目标是自己），新本人方法不能指定他人或查询目录；错误 audience、OAuth/service 身份、伪造输入与未知方法拒绝。
- 禁用/关闭/身份版本不符、Session 换代和恢复后重新登录；邮箱/恢复配置故障不成为合法本人读取的新授权前置。数据损坏或依赖不可用不回填 false。
- Gateway 三协议、严格 DTO、私有 no-store、限流和 Auth reason 透传；未授予用户的成功双 false 与基础设施失败可明确区分。
- Console 真页面仅打开对应动作；在权限读取后撤销、旧响应迟到和目标/Session 换代下清除相应确认。实际 App 写接口仍拒绝缺项权限，并分别验证已有 JWS 传播窗口与新身份签发后的授权事实。

本轮交付仅为待审方案与只读核查；没有运行新业务测试、生成 API、修改产品代码、发送跨聊天消息、部署或 push。
