# iWUT Gateway 设计

状态：`ACCEPTED`

Gateway 为终端到平台服务的请求提供路由选择、认证编排与转发。首版保持薄层，不建立人员权限、用户资料或 Session 数据模型，也不直接访问 Auth MongoDB。

- [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md)：按同一路由选择 DIRECT/SESSION 策略，认证成功后由 Router 转发；OAUTH2 保留但不启用。
- [设计注册表](design-registry.md)：本 context 的 UC/BR 索引。
- [实现状态](implements/README.md)：设计与实现分别跟踪。
- [ADR-GW-001](adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md)：固定 Go module、Traefik 版本、协议适配和路由目录。
- [Auth 签发用例](../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)与[共享调用契约](../platform/contracts/auth-session-identity-issuance-v1.md)：Gateway 的身份来源。

代码位置为 `worktrees/iwut-gateway-ddd`，孤儿分支 `gateway/v1`。旧 `iwut-gateway` 和 `iwut-gateway-auth-forward` 不自动成为新设计的规范；本次保留旧工作区和其中的未提交修改。

Traefik `v3.7.13` 保留 Edge、HTTP Router、TLS 与 gRPC-Web 终止职责。HTTP/JSON 的 SESSION 路由使用 ForwardAuth；原生 gRPC 与转换后的 gRPC-Web 进入 Gateway 精确 unary 前置代理，避免 ForwardAuth 拒绝时返回非 gRPC 响应。配置由严格的 `config/routes.v1.yaml` 驱动，具体边界见 ADR-GW-001。具有相同行为的新接口只扩充路由及测试，不为每条业务路径创建独立 UC。不设计 Gateway 数据库、Redis、事件总线、动态策略语言或路由后台。

UC 正文中的 `BR-GWR-*` 是本 context 的规则权威；平台目录只保存真正跨系统的约定。UC-GW-001 首个实现工作包已 `COMPLETE`，覆盖详情和验收提交见[实现状态](implements/README.md)。UC-GW-001 工作包直接读取 UC、ADR 与它们点名的共享契约；新 UC-GW-002 尚为 PROPOSED，其进入实现前须决定工作包输入方式，不假定 App/Auth brief 生成器已经支持 Gateway。现有 `tools/registry.py` 仍不能被当作已经检查 Gateway registry，Gateway registry 必须人工同步审查。

## OAuth / OIDC 设计（2026-09-27，PROPOSED）

整体顺序、现有能力和交付门禁见 [OAuth/OIDC 工作包总览](../auth-center/design-notes/oauth-oidc-delivery-plan.md)。以下条目尚未接受或实现，不改变已启用接口。

- [UC-GW-002：应用委托请求鉴权与转发](use-cases/UC-GW-002-authenticate-oauth-and-forward.md)。
