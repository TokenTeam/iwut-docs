# Auth Center 开放问题

状态：`ACTIVE`

## UC-AUTH-001 进入 ACCEPTED 前

### 内部服务身份

App Center 调用 Auth Center 内部 gRPC 时使用哪一种可验证服务身份仍未决定。候选方案必须明确 audience、轮换、调用方 allowlist 和本地验证方式；不能继续沿用未签名 Header，也不能把网络位置本身当作身份。

这个问题不阻塞 Proto 消息和测试 Auth Server，但阻塞真实跨服务部署和 UC-AUTH-001 的 `COMPLETE`。

### Catalog 写入与初始装载

UC-AUTH-001 只读取已经存在的权威目录。目录由部署种子、显式管理 UC 还是其它权威源产生仍未决定。生产实现不得把测试 fixture 或 App Center 的硬编码列表当成权威目录。

### 完整 Scope 元数据

首个消费方只需要 `name` 和 `requestable`。面向 consent UI、审计或数据投影所需的 display name、description、sensitivity 等字段，应由后续 Auth UC 引入；不得为了预判未来而提前加入 v1 必填字段。

## UC-AUTH-002 后续写侧

### Principal provision 与状态迁移

UC-AUTH-002 只读取 `auth_principals`。普通用户主体如何创建、Developer 资格如何申请、
审批、暂停和恢复，以及相关审计由后续命令 UC 定义；生产不能通过直接修改 MongoDB
替代这些业务行为。

### System principal

UC-APP-005 需要稳定的 System Auth ID 记录自动拒绝。Auth Center 应通过独立的
provision/bootstrap 决定创建不可登录的 SYSTEM principal，并把其 opaque authId 交给
App Center 启动配置；本查询不把 SYSTEM 伪装成 Developer。
