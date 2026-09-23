# iWUT Gateway 设计

状态：`PROPOSED`

Gateway 为终端到平台服务的请求提供路由选择、认证编排与转发。首版保持薄层，不建立人员权限、用户资料或 Session 数据模型，也不直接访问 Auth MongoDB。

- [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md)：按同一路由选择 DIRECT/SESSION 策略，认证成功后由 Router 转发；OAUTH2 保留但不启用。
- [设计注册表](design-registry.md)：本 context 的 UC/BR 索引。
- [实现状态](implements/README.md)：设计与实现分别跟踪。
- [Auth 签发用例](../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)与[共享调用契约](../platform/contracts/auth-session-identity-issuance-v1.md)：Gateway 的身份来源。

代码位置为 `worktrees/iwut-gateway-ddd`，孤儿分支 `gateway/v1`。旧 `iwut-gateway` 和 `iwut-gateway-auth-forward` 不自动成为新设计的规范；本次保留旧工作区和其中的未提交修改。

Traefik 保留 Edge/Router/gRPC-Web 终止职责；认证组件只提供薄编排。配置由路由清单驱动，具有相同行为的新接口只扩充路由及测试，不为每条业务路径创建独立 UC。不设计 Gateway 数据库、Redis、事件总线、动态策略语言或路由后台。

UC 正文中的 `BR-GWR-*` 是本 context 的规则权威；平台目录只保存真正跨系统的约定。当前不生成 Gateway brief，不扩展 brief 生成器；待设计接受、进入实现时再加入 `UC-GW-*` 支持及对应测试。现有脚本不能被当作已经检查 Gateway registry。
