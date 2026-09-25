# Auth Center 设计

状态：`PROPOSED`

本目录保存 Auth Center bounded context 的权威业务设计。旧
`iwut-auth-center` 实现只作为历史证据，不自动成为新设计的规范或代码模板。

## 当前迭代

当前已有十三个接受的用例（UC-AUTH-001 至 013）；设计接受与实现完成分别跟踪：

- `UC-AUTH-001`：授权的内部服务读取 Auth 权威的 Scope Catalog 完整快照。
- `UC-AUTH-002`：授权的内部服务按 Auth ID 批量读取当前 Developer 状态。
- `UC-AUTH-003`：授权的内部服务解析指定 purpose 的 SYSTEM 主体。
- `UC-AUTH-004`：平台管理员管理 Reviewer 权限。
- `UC-AUTH-005`：普通用户显式设置/删除自己的资料，以当前账号状态与资料版本原子确认。
- `UC-AUTH-006`：客户端已有本地学校账号，提交必需的学生关联声明，通过设备凭据显式创建正式 USER 和首次 Session。
- `UC-AUTH-007`：设备凭据登录、服务端 Session、在线检查，以及每账号 10 条有效会话的 LRU 管理。
- `UC-AUTH-008`：由当前 token 定向撤销自己的 Session，不改变设备凭据。
- `UC-AUTH-009`：有效用户撤销属于自己账号的设备凭据，并使相关 Session 在后续检查中失效。

- `UC-AUTH-010`：受授权 Gateway 根据有效 Session 获取目标服务的可信用户 JWS。
- `UC-AUTH-011`（ACCEPTED）：无 Session 时通过邮箱验证创建账号；有有效 Session 时绑定或更换邮箱。
- `UC-AUTH-012`（ACCEPTED）：邮箱验证码登录原账号，登记/复用本机设备凭据并建立 Session。
- `UC-AUTH-013`（ACCEPTED）：具备激活邮箱及可用邮箱登录的普通用户自助申请 Developer。

用户资料的字段定义和编辑规则已归入 UC-AUTH-005 的 `BR-UPF-*`，读取本人资料和表单 schema
见[配套查询契约](query-contracts/user-profile-editing.md)。可信身份签发由 UC-AUTH-010 定义，
Gateway 鉴权转发由 UC-GW-001 跟踪。邮箱注册/绑定、邮箱登录与本机设备恢复、Developer 自助申请
分别见已接受的 UC-AUTH-011/012/013；Scope 管理后台、Developer 暂停/恢复、旧设备迁移、
第三方应用资料开放和 consent 仍属于后续独立用例。

创建、登录和两项撤销用例已接受，设备签名、关联声明与 Session/RPC 载体统一引用
[App 设备认证与 Session v1](../platform/contracts/auth-device-session-v1.md)。运行参数及存储原子性由对应 UC 定义。
客户端组合流程见[客户端认证生命周期建议](client-guides/authentication-lifecycle.md)，客户端和 Gateway 独立交付。

用户资料的模型说明保留在
[字段定义说明](design-notes/user-profile-field-definition.md)与
[用户主体和资料模型草案](design-notes/user-model.md)，通过链接引用用例规则，避免形成第二权威。

## 权威边界

- Auth Center 拥有 Scope Catalog 的业务事实、快照与 revision 语义。
- [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 是提供方行为与 `BR-SCP-*` 的权威来源。
- [共享契约](../platform/contracts/auth-scope-catalog-v1.md) 是 Auth Center 与消费方共同遵守的线格式和 gRPC 边界。
- 可执行 Proto 进入独立 API 仓库的 `auth_center/v1/scope_catalog/`，不复制到本仓库。
- App Center 的 TTL、singleflight、revision 回退保护与 fail-closed 策略继续由 App Center 自己的 UC/ADR 拥有。
- Auth Center 拥有 `auth_principals` 中的主体类型与 Developer 状态；UC-AUTH-002
  只公开 App Center 批量暂停检查所需的最小投影。
- 用户资料的定义所有权、信任边界与内嵌存储分别见 UC-AUTH-005 的
  [BR-UPF-001](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)、
  [BR-UPF-002](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002) 和
  [BR-UPF-010](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。

## 文档入口

- [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md)：邮箱验证码登录与本机设备授权已接受；[brief](briefs/UC-AUTH-012.md)，实现集成依赖 UC011。
- [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md)：Developer 自助申请与本人资格查询已接受；[实现 brief](briefs/UC-AUTH-013.md)。

- [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md)：设置并激活邮箱已接受；[实现 brief](briefs/UC-AUTH-011.md)，邮箱登录仍独立交付。

- [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md)：Session 到可信身份签发；[生成 brief](briefs/UC-AUTH-010.md)。
- [Gateway UC-GW-001](../gateway/use-cases/UC-GW-001-authenticate-and-forward.md)：单一路由驱动的认证与转发草案。

- [用户资料字段定义](design-notes/user-profile-field-definition.md)：字段目录的最小结构、类型与已接受的校验规则。
- [用户模型](design-notes/user-model.md)：用户主体固定字段、动态资料实例及相关能力的边界草案。
- [UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md)：用户编辑自己的资料。
- [UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md)：创建用户、设备凭据归属与学生关联。
- [UC-AUTH-007](use-cases/UC-AUTH-007-login.md)：设备登录、Session 建立与在线检查。
- [UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md)：撤销自己的当前 Session。
- [UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md)：撤销自己的设备凭据。
- [客户端认证生命周期建议](client-guides/authentication-lifecycle.md)：客户端注册、自动登录、账号切换和退出的非权威组合建议。
- [UC-AUTH-006 brief](briefs/UC-AUTH-006.md)、[007 brief](briefs/UC-AUTH-007.md)、[008 brief](briefs/UC-AUTH-008.md)、[009 brief](briefs/UC-AUTH-009.md)：脚本生成的已接受认证工作包。
- [UC-AUTH-005 brief](briefs/UC-AUTH-005.md)：脚本生成的资料编辑工作包输入。
- [资料编辑配套查询](query-contracts/user-profile-editing.md)：读取本人资料与字段定义/限制。
- [design-registry.md](design-registry.md)：Auth Center 已分配的 UC 与 BR。
- [open-questions.md](open-questions.md)：进入真实实现前仍需决定的问题。
- [implements/README.md](implements/README.md)：实现覆盖与交付缺口。
- [UC-AUTH-001](use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)：读取 Scope Catalog 快照。
- [UC-AUTH-002](use-cases/UC-AUTH-002-batch-get-developer-statuses.md)：批量读取 Developer 状态。
- [UC-AUTH-003](use-cases/UC-AUTH-003-resolve-system-principal.md)：解析 System Principal。
- [UC-AUTH-004](use-cases/UC-AUTH-004-manage-reviewer-permission.md)：管理 Reviewer 权限。

## 状态

设计使用 `PROPOSED`、`ACCEPTED`、`DEPRECATED`、`SUPERSEDED`；实现覆盖使用
`NOT_STARTED`、`IN_PROGRESS`、`CORE_COMPLETE`、`COMPLETE`。设计状态和实现状态彼此独立。
