# iWUT Console 实现状态

## 当前状态

| 工作包 | 设计 | 实现 | 缺口 |
| --- | --- | --- | --- |
| Console 工程初始化 | `UC-CONSOLE-001`（`ACCEPTED`） | `IMPLEMENTED` | pnpm workspace、严格 TypeScript、固定统一 API 生成输入与验证命令已建立；真实服务 E2E 仍属于 UC001 整体缺口 |
| 共享浏览器 Session | `UC-CONSOLE-001`（`ACCEPTED`） | `IN_PROGRESS` | 浏览器密钥/协议、BFF 加密 Cookie、安全 Session 投影、私有 ForwardAuth、设备/邮箱 Begin/Complete BFF 编排、双登录页面状态机、Gateway surface chain 与共享 Traefik 配置合并验证已实现；重发协调与真实 Auth/邮件链路验收待完成 |
| Developer Console 功能 | `UC-CONSOLE-001`（认证入口） | `IN_PROGRESS` | 独立构建、路由、Query、Session 入口及设备/邮箱登录交互已实现；完整恢复和真实服务验收待完成，业务 UC 尚未分配 |
| Admin Console 功能 | `UC-CONSOLE-001`（认证入口） | `IN_PROGRESS` | 独立构建、BFF/Cookie 边界、Session 入口及设备/邮箱登录交互已实现；完整恢复和真实服务验收待完成，审核业务 UC 尚未建立 |

## 代码位置

实现目录为 `worktrees/iwut-console`。UC001 接受后在该目录初始化独立 Git 仓库与 pnpm workspace；本页的 `IN_PROGRESS` 不表示真实 E2E 或 UC 完成。

## UC-CONSOLE-001 首个实现工作包

状态：`IN_PROGRESS`

代码范围：

- 根 workspace、严格 TypeScript、统一检查命令和固定 lockfile；
- `developer-console`、`admin-console` 的独立 Vite/Router/Query 应用入口；
- `developer-bff`、`admin-bff` 的独立 Hono 进程，以及共享但无产品授权逻辑的 `bff-auth` Cookie/Origin/Session 机制；两个 BFF 分别注入 Cookie 命名空间、密钥、Origin 与超时配置；
- 按 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 为两个 BFF 增加私有 Session ForwardAuth；普通 HTTP/JSON API 由共享 Traefik 经 BFF Cookie 交换后进入现有 Gateway ForwardAuth，登录、恢复与聚合仍经过 BFF；
- 固定统一 API `9f914c5` 的可复现 TypeScript 生成输入，以及原生 fetch/ProtoJSON runtime；
- 共享浏览器设备密钥、签名协议、会话 DTO、错误映射和测试设施；
- UC001 的设备登录、邮箱登录、结果不确定恢复、Session 摘要与失效处理；
- Vitest/Testing Library/BFF 集成测试，并为真实 Playwright E2E 建立入口。

非目标：

- Developer/Application 管理和 Admin 审核业务页面；
- OAuth consent bridge、多账号管理、显式 Session/设备管理；
- 生产部署、生产邮件就绪声明和像素级视觉定稿；
- 用 MSW 或 fixture 代替 UC001 要求的最终真实 Auth/Gateway/邮件 E2E。

首个工作包验证命令：

```bash
pnpm install --frozen-lockfile
pnpm generate:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test
pnpm edge:e2e
```

真实服务 E2E 需要单独的受控环境与 Auth 邮件配置；本地浏览器测试未连接真实服务时必须明确跳过，不能报告为通过。

## 2026-10-07 首个实现增量

`worktrees/iwut-console` 已交付工程与认证安全基线：两个独立 React/Vite 应用、两个独立 Hono BFF、共享且不包含产品授权逻辑的 BFF Session 封装、浏览器 P-256 设备密钥与协议校验、固定 `9f914c5` 的 Proto TypeScript 生成物、原生 fetch transport，以及单元/BFF/壳层浏览器测试。

本增量没有宣称 UC001 完成：登录按钮尚未接入 Begin/Complete 流程，BFF 尚未消费 Gateway 登录 RPC，结果不确定恢复、邮件收取和真实 Auth/Gateway/邮件 Playwright E2E 均待后续增量。Playwright 壳层测试拦截 `/api/session`，只能证明两个前端入口可运行，不能替代真实登录验收。

2026-10-07 接受 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)。两个 BFF 已提供同构的私有 `/internal/forward-auth`：无 Cookie 时不产生 Session，合法 Cookie 只返回一个 `x-iwut-session`，出现但无效的 Cookie 与来源不匹配均失败关闭。该 ForwardAuth 拒绝响应不直接设置或清除 Cookie；Cookie 清理由显式 BFF Session 路径拥有。Gateway route schema v3、两个 surface chain 及其真实 Traefik E2E 已通过。

## 2026-10-08 共享 Edge composition 增量

Console 侧已增加共享 Traefik 的 BFF/SPA 动态配置生成器，并以固定 Traefik 镜像验证两份动态文件可合并装载、Session 与 SPA Router 按固定优先级命中、私有 ForwardAuth 不可公开访问、Gateway 链在 BFF 基础设施失败时保持失败关闭。BFF 登录/恢复调用 Gateway 的内部入口与真实 Auth/邮件 E2E 仍待 UC001 后续增量。

同日后续增量新增两个 surface 共用的设备/邮箱登录 BFF 编排：四条固定同源 Begin/Complete 路径通过生成的 ProtoJSON 类型调用非 Console Gateway origin，完全不转发浏览器 Cookie 或 Session；BFF 用独立、加密、HttpOnly 的短期 flow Cookie 将 Complete 绑定到 Begin，校验 Auth challenge/Session 形状，并只在确定成功后写入对应 Console Session Cookie。共享 Traefik 已为四条路径生成优先级 `40000` 的精确 Router。浏览器页面状态机、签名接线、结果不确定恢复及真实 Auth/邮件 E2E 尚未完成，因此 UC001 继续保持 `IN_PROGRESS`。

本机设备登录页面随后接入两个 Console：页面只读取不含私钥的 IndexedDB 凭据摘要，完整 challenge 的 protocol/purpose/service/application/operation/locator/expiry 全部通过后才要求凭据适配器签名；React state、Query cache 和表单均不接触 `CryptoKey`。目标 `AUTH_AUTHENTICATION_SERVICE_ID` 由 `VITE_AUTH_SERVICE_ID` 预配置，缺失或非法时入口失败关闭；成功响应更新安全 Session 投影与本机 credentialId。该组件测试使用 mock BFF，只验证浏览器分支，不能替代真实设备登录 E2E。邮箱页面和结果不确定恢复仍待实现。

邮箱页面增量随后接入：BFF 以默认关闭的 `EMAIL_LOGIN_ENABLED` 发布只读 capability；浏览器严格复现平台 ASCII 邮箱规范，在 Begin 前生成并持久化 non-extractable P-256 密钥，使用 8 位字符串验证码并核对邮箱协议十字段签名上下文。Begin 网络结果不确定时页面保留原 requestId、邮箱和同一 localId 进行幂等重试；Complete 结果不确定时可先用同一公钥 fingerprint 走设备登录探测，也可保留原验证码重试。Playwright 已在两个真实浏览器 origin 上覆盖 Web Crypto/IndexedDB、签名和 Session 投影，但 BFF/Auth/SMTP 均为拦截响应，不能代替真实邮件验收。服务端 `resendAfter` 冷却后的显式重发、迟到响应竞争与完整真实链路仍待实现，因此 UC001 保持 `IN_PROGRESS`。

## 实现登记原则

- 设计状态与实现状态分开维护；
- MSW 页面演示不等于 API、Gateway 或端到端交付；
- 每个工作包登记目标 UC/ADR、代码范围、非目标、验证命令和真实外部依赖；
- 两个应用分别记录构建、组件测试、BFF 测试和 Playwright 验收；
- 涉及浏览器认证协议时必须复用平台公开测试向量，并包含真实 Auth/Gateway 验证。
