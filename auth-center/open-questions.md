# Auth Center 开放问题

状态：`ACTIVE`

## 当前设计优先级（2026-09-27）

用户决定先推进 OIDC 登录、用户 scope 授权和收回，支持 PUBLIC_PKCE 与 CONFIDENTIAL_SECRET。已建立 Auth014–019、App018–019、Gateway002 的 PROPOSED 设计，见 [工作包总览](design-notes/oauth-oidc-delivery-plan.md)。Gateway OAUTH2 仍未启用；生产 Catalog 初始装载、官方门户、资源委托验证及联合测试属于明确交付依赖，在线 Catalog 管理后移。TEST 之外的正式运行资格、原生无感浏览器 SSO 桥和动态资料 scope 仍需后续设计。

## Scope Catalog 后续写侧

### Catalog 写入与初始装载

UC-AUTH-001 只读取已经存在的权威目录。目录由部署种子、显式管理 UC 还是其它权威源产生仍未决定。生产实现不得把测试 fixture 或 App Center 的硬编码列表当成权威目录。

### 完整 Scope 元数据

首个消费方只需要 `name` 和 `requestable`。面向 consent UI、审计或数据投影所需的 display name、description、sensitivity 等字段，应由后续 Auth UC 引入；不得为了预判未来而提前加入 v1 必填字段。

## UC-AUTH-002 后续写侧

### Principal provision 与状态迁移

UC-AUTH-002 只读取 `auth_principals`。普通用户由 UC006 创建，邮箱注册见已接受的 UC011。
Developer 申请与开通审计见 [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md) 已接受，首版采用满足邮箱前置条件后自助开通；
人工审批、拒绝后重申、暂停和恢复仍需独立用例。生产不能通过直接修改 MongoDB 替代这些行为。

Developer 是 USER principal 的可选属性。普通用户的 `developerStatus` 为 null；只有申请
进入 Developer 生命周期后才取 `PENDING/APPROVED/REJECTED/SUSPENDED`。主体建立与
Developer 申请不能被合并成同一个隐式动作。

### 普通 USER provision 与 Auth 用户身份签发

SYSTEM principal provision 已由 UC-AUTH-003 闭合，PLATFORM_ADMIN bootstrap 与 Reviewer
grant/revoke 已由 UC-AUTH-004 决定。其生产入口仍依赖普通 USER 在何时 provision、登录/
session 如何建立，以及 Auth 如何签发 trusted-identity-v1。前两项已有
[UC-AUTH-006](use-cases/UC-AUTH-006-create-user.md) 与
[UC-AUTH-007](use-cases/UC-AUTH-007-login.md) 的 ACCEPTED 设计；Session 与凭据撤销分别由
[UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md) 和
[UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md) 接受。可信身份签发已有 [UC-AUTH-010](use-cases/UC-AUTH-010-issue-user-identity-from-session.md)、Gateway 接入已有 [UC-GW-001](../gateway/use-cases/UC-GW-001-authenticate-and-forward.md) 设计；UC-AUTH-010 已 ACCEPTED 并进入实现，UC-GW-001 仍为 PROPOSED。
不能用数据库直改或无认证临时 RPC 代替这些能力。

## 用户资料生产交付

[UC-AUTH-005](use-cases/UC-AUTH-005-edit-own-user-profile.md) 资料编辑规则和配套读取契约已 ACCEPTED。以下事项仍需推进：

- 首批实际字段及其用途；示例学校名称/入学年份不是已批准的收集清单。
- 普通 USER 创建时的账号/资料初始化，以及既有主体记录的迁移工作包；本用例不在读取或编辑时静默修复。
- 面向 Auth audience 的用户身份签发、Gateway 受保护路由、登录引导和客户端明确确认上传的交付。
- 字段目录在线管理、停用与演进；当前首版部署装载与稳定性方向见 [BR-UPF-002](use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。
- 第三方应用访问资料所需的字段到 scope 映射、用户 consent 与读取授权，另立用例，不由本人编辑接口替代。


## 创建、登录与撤销的实现交付

UC-AUTH-006 至 009 已 ACCEPTED；设备证明、学号规范化和散列、Session 载体及 RPC 鉴权由[共享契约](../platform/contracts/auth-device-session-v1.md)闭合。设计接受不等于生产交付，本页只跟踪实现工作：

- 后端真实验证器、共享测试向量、生成 Proto、原生 gRPC、方法级 middleware 与生产组合根；不得以 fake verifier 代替认证。
- Mongo 原子注册、登录/撤销栅栏、会话一致检查、10 会话 LRU 及真实副本集故障测试，按 UC006–009 验收。
- 学生关联仍是注册必填的客户端声明；启动前离线密钥轮换、正式环境维护窗口、故障测试及备份保留按 [BR-REG-008](use-cases/UC-AUTH-006-create-user.md#br-reg-008) 交付，不等待在线迁移。
- Session 的 AUTH_SESSION_TTL 必填配置、认证入口有界默认参数与非法配置拒绝启动，见 [BR-LGN-004](use-cases/UC-AUTH-007-login.md#br-lgn-004) 和 [BR-LGN-009](use-cases/UC-AUTH-007-login.md#br-lgn-009)；部署调优不改变固定会话及 LRU 语义。
- Android/iOS 安全存储、客户端兼容矩阵、注册关联披露、签名前检查、自动登录和可靠删除独立验收，组合建议见[客户端生命周期](client-guides/authentication-lifecycle.md)。
- Gateway 路由与 Session 到用户身份 JWS 签发已在 UC-GW-001/UC-AUTH-010 分别跟踪。UC010 已接受；现有后端通过不表示 UC005 公网调用链已贯通。

## 后续认证与关联能力

- k8s 改造时再评审多实例在线密钥轮换；当前单实例离线方案见 [BR-REG-008](use-cases/UC-AUTH-006-create-user.md#br-reg-008)。
- Auth 基于有效 Session 签发目标服务身份、Gateway 鉴权 RPC/路由与秘密转发边界，跟踪已接受的 UC-AUTH-010 与 UC-GW-001 草案；首版不引入 Redis 或身份缓存，OAuth2 单独设计。
- 邮箱设置/注册见 [UC-AUTH-011](use-cases/UC-AUTH-011-set-and-activate-email.md)，已有账号邮箱登录及本机设备授权见 [UC-AUTH-012](use-cases/UC-AUTH-012-login-with-email.md)，Developer 自助申请见 [UC-AUTH-013](use-cases/UC-AUTH-013-apply-for-developer.md)，UC011 已 ACCEPTED，其独立协议与向量已闭合；UC012 的专用签名、向量和接口也已闭合并 ACCEPTED，后端已基于 UC011 完成集成并合回 auth-center/v1，仍需交付 Gateway/客户端；UC013 已 ACCEPTED，后端依赖已满足，协议与默认关闭的恢复就绪声明已固定，进入实现流程。公网资格开通仍等待邮箱恢复链路实际交付，不能仅以后端实现完成视为产品可用。
- 旧设备明确授权新增凭据、凭据/Session 列表与命名、撤销其它 Session、账号禁用/重新启用和注销仍需独立用例。当前 token 的 Session 撤销由 [UC-AUTH-008](use-cases/UC-AUTH-008-revoke-own-session.md) 定义，本人 credentialId 的凭据撤销由 [UC-AUTH-009](use-cases/UC-AUTH-009-revoke-own-credential.md) 定义，客户端退出组合见[生命周期建议](client-guides/authentication-lifecycle.md)。
- 外部应用的专属学生关联标识：披露授权、未关联语义、保留/删除/改绑与配额连续性；当前注册仅建立内部关系，不发布新的对外身份 claim。
