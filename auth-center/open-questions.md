# Auth Center 开放问题

状态：`ACTIVE`

## Scope Catalog 后续写侧

### Catalog 写入与初始装载

UC-AUTH-001 只读取已经存在的权威目录。目录由部署种子、显式管理 UC 还是其它权威源产生仍未决定。生产实现不得把测试 fixture 或 App Center 的硬编码列表当成权威目录。

### 完整 Scope 元数据

首个消费方只需要 `name` 和 `requestable`。面向 consent UI、审计或数据投影所需的 display name、description、sensitivity 等字段，应由后续 Auth UC 引入；不得为了预判未来而提前加入 v1 必填字段。

## UC-AUTH-002 后续写侧

### Principal provision 与状态迁移

UC-AUTH-002 只读取 `auth_principals`。普通用户主体如何创建、Developer 资格如何申请、
审批、暂停和恢复，以及相关审计由后续命令 UC 定义；生产不能通过直接修改 MongoDB
替代这些业务行为。

Developer 是 USER principal 的可选属性。普通用户的 `developerStatus` 为 null；只有申请
进入 Developer 生命周期后才取 `PENDING/APPROVED/REJECTED/SUSPENDED`。主体建立与
Developer 申请不能被合并成同一个隐式动作。

### 普通 USER provision 与 Auth 用户身份签发

SYSTEM principal provision 已由 UC-AUTH-003 闭合，PLATFORM_ADMIN bootstrap 与 Reviewer
grant/revoke 已由 UC-AUTH-004 决定。其生产入口仍依赖普通 USER 在何时 provision、登录/
session 如何建立，以及 Auth 如何签发 trusted-identity-v1。这些能力必须独立设计，不能
用数据库直改或无认证临时 RPC 代替。
