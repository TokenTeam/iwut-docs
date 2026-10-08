# iWUT Gateway 设计

状态：`ACCEPTED`

Gateway 为终端到平台服务的请求提供路由选择、认证编排与转发。首版保持薄层，不建立人员权限、用户资料或 Session 数据模型，也不直接访问 Auth MongoDB。

- [UC-GW-001](use-cases/UC-GW-001-authenticate-and-forward.md)：按同一路由选择 DIRECT/SESSION 策略，认证成功后由 Router 转发；OAUTH2 保留但不启用。
- [UC-GW-002](use-cases/UC-GW-002-authenticate-oauth-and-forward.md)：对应用 Bearer 做在线委托交换，并显式接入 OIDC 标准 HTTP 端点；当前为提案。
- [UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md)：公开读取允许匿名，提供 Session 时必须完整验证并附加 USER JWS；已接受并完成本地实现验证。
- [UC-GW-004](use-cases/UC-GW-004-forward-optional-session-to-auth.md)：Auth 双模式入口允许 Session 缺失，提供时原样保留且不得降级；已接受并实现。
- [UC-GW-005](use-cases/UC-GW-005-forward-account-closure-credentials.md)：账号注销 confirmation/receipt 按精确方法用途隔离转发；已接受并实现。
- [UC-GW-006](use-cases/UC-GW-006-forward-application-close-proof.md)：Application 关闭同时转发 App USER JWS 与高风险 proof；已接受并实现。
- [UC-GW-007](use-cases/UC-GW-007-compose-console-session-forward-auth.md)：按 Route/Host 为 Developer、Admin Console 编排 BFF Session ForwardAuth，再进入现有 Gateway 凭据链；已接受，Gateway-owned 外部/私有 chain 与 Console BFF/SPA 路由合并已本地验证，UC-CONSOLE-001 的重发/完整恢复及真实 Auth/邮件链路仍在进行。
- [外部 API 接入清单](external-api-exposure-inventory.md)：从 Auth/App UC 与统一 API 派生全部终端 method/path，记录身份策略、当前 route 与待接入缺口。
- [设计注册表](design-registry.md)：本 context 的 UC/BR 索引。
- [实现状态](implements/README.md)：设计与实现分别跟踪。
- [ADR-GW-001](adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md)：固定 Go module、Traefik 版本、协议适配和路由目录。
- [ADR-GW-002](adr/ADR-GW-002-route-credential-and-identity-policy.md)：把凭据载体、身份交换与下游保留拆成严格路由矩阵；已接受并实现非 OAuth 组合。
- [ADR-PLAT-004](../platform/adr/ADR-PLAT-004-unified-api-integration-baseline.md)：跨服务完成前汇合并固定统一 API commit；已接受并首次应用。
- [Auth 签发用例](../auth-center/use-cases/UC-AUTH-010-issue-user-identity-from-session.md)与[共享调用契约](../platform/contracts/auth-session-identity-issuance-v1.md)：Gateway 的身份来源。

代码位置为 `worktrees/iwut-gateway-ddd`，孤儿分支 `gateway/v1`。旧 `iwut-gateway` 和 `iwut-gateway-auth-forward` 不自动成为新设计的规范；本次保留旧工作区和其中的未提交修改。

Traefik `v3.7.13` 保留 Edge、HTTP Router、TLS 与 gRPC-Web 终止职责。HTTP/JSON 的每条路由使用 route-specific ForwardAuth；原生 gRPC 与转换后的 gRPC-Web 进入 Gateway 精确 unary 前置代理，避免 ForwardAuth 拒绝时返回非 gRPC 响应。配置由严格的 `config/routes.v3.yaml` 驱动，具体边界见 ADR-GW-001/002。具有相同行为的新接口只扩充路由及测试，不为每条业务路径创建独立 UC。不设计 Gateway 数据库、Redis、事件总线、动态策略语言或路由后台。

UC 正文中的 `BR-GWR-*` 是本 context 的规则权威；平台目录只保存真正跨系统的约定。UC-GW-001 首个实现工作包已 `COMPLETE`，UC-GW-003 已完成本地联合验证，UC-GW-004/005/006 已接受并由 Gateway `293ebc9` 实现；Gateway `7a3eb7c` 又将全部 44 条 Auth 与 43 条 App Proto 外部方法纳入精确目录。各业务成功/拒绝的真实联合验收仍按 UC 是发布门禁，详情见[实现状态](implements/README.md)。Gateway 工作包直接读取 UC、ADR 与它们点名的共享契约；当前 brief 生成器仍不生成 Gateway brief。UC-GW-002 仍为 `PROPOSED / NOT_STARTED`，8 个 OAuth/OIDC 标准 HTTP 端点仍失败关闭；ADR-GW-002/ADR-PLAT-004 已接受。现有 `tools/registry.py` 仍不能被当作已经检查 Gateway registry，Gateway registry 必须人工同步审查。

Console 混合流量由 [ADR-CONSOLE-004](../console/adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 决定前端/BFF 所有权，[UC-GW-007](use-cases/UC-GW-007-compose-console-session-forward-auth.md) 固定 Gateway 侧的逐 Route surface、精确 Host、middleware 顺序和失败不抵达语义。Gateway-owned Cookie→Session chain 与 BFF 私有 exact/deny Router 已通过真实双 surface 共享 Traefik E2E；Console deployment composition 负责 BFF-owned/SPA 路由、内部端口网络隔离和 URL 注入。该 UC 仍等待 UC-CONSOLE-001 的显式重发/迟到响应协调、完整结果恢复及真实 Auth/邮件链路验收，所以保持 `IN_PROGRESS`。

## OAuth / OIDC 设计（2026-09-27，PROPOSED）

整体顺序、现有能力和交付门禁见 [OAuth/OIDC 工作包总览](../auth-center/design-notes/oauth-oidc-delivery-plan.md)。以下条目尚未接受或实现，不改变已启用接口。

- [UC-GW-002：应用委托请求鉴权与转发](use-cases/UC-GW-002-authenticate-oauth-and-forward.md)。

## 可选身份公开读取（2026-10-07，ACCEPTED）

[UC-GW-003](use-cases/UC-GW-003-attach-optional-user-identity.md) 为 App UC023/024 建立统一入口：没有 Session 时匿名转发，存在 Session 时调用 Auth UC010 换取目标 audience USER JWS；任何已提供但无效或歧义的凭据都失败关闭。Gateway `0009947` 已按 [ADR-GW-002](adr/ADR-GW-002-route-credential-and-identity-policy.md) 实现 v2 路由矩阵，并按 [ADR-PLAT-004](../platform/adr/ADR-PLAT-004-unified-api-integration-baseline.md) 固定共同 API `9f914c5`。本地真实 Auth/App 三协议 E2E 已通过；尚未 push 或生产部署。

Gateway `293ebc9` 在同一 API 基线上把目录扩展为 36 条精确 route，实现 UC-GW-004/005/006 及三条配套入口。新特殊路由已通过单元、ForwardAuth、gRPC proxy、Traefik 生成与全量回归；现有真实 Auth/App 三协议 E2E 也已通过，但该 E2E 未覆盖邮箱、账号注销和应用关闭的新业务流。尚未 push 或生产部署。

Gateway `7a3eb7c` 继续扩展为 87 条精确 Proto route，与固定 API 中 44 个 Auth、43 个 App 外部 annotation 方法闭合；同时固定 87 个 typed unary adapter，并在 UC-GW-002 实现前全局拒绝/清理 `x-iwut-access-token`。真实 Traefik、Gateway、Auth、App、Mongo E2E 已对新 Auth DIRECT 与 App USER 策略各选代表 route，通过 HTTP/JSON、原生 gRPC 与 gRPC-Web 验证有效/缺失 Session 边界。尚未 push 或生产部署。
