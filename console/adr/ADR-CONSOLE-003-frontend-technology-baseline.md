# ADR-CONSOLE-003：Console 首版技术基线

状态：`ACCEPTED`

日期：2026-10-05

## 背景

两个 Console 以数据读取、复杂表单、审核状态、表格和权限入口为主，需要严格 TypeScript、明确的状态所有权、可生成的 API 类型，以及覆盖浏览器认证协议和关键用户流程的自动化测试。

## 决定

首版采用以下基线：

| 范围 | 选择 |
| --- | --- |
| 仓库与包管理 | pnpm workspace monorepo |
| 语言 | TypeScript strict mode |
| UI | React 19 + TSX |
| 构建 | Vite |
| 路由 | TanStack Router |
| 服务端状态 | TanStack Query |
| 表单与输入校验 | React Hook Form + Zod |
| 样式 | Tailwind CSS v4 |
| 组件基础 | shadcn/ui + Radix primitives |
| 数据表格 | TanStack Table |
| 图标 | Lucide |
| BFF | Hono |
| API | 原生 `fetch` runtime + 生成的 TypeScript 类型/客户端 |
| Mock | MSW，仅用于开发和测试 |
| 测试 | Vitest + Testing Library + Playwright |

具体 patch 版本由首个工程工作包的 lockfile 固定；本 ADR 不允许生产或 CI 使用未锁定依赖解析结果。

## 状态所有权

状态按来源归属，不建立默认全局 store：

- 组件瞬时交互使用 React local state；
- 可分享、可刷新恢复的筛选与分页使用 TanStack Router search params；
- 服务端读取、失效与 mutation 协调使用 TanStack Query；
- 表单编辑与校验使用 React Hook Form + Zod；
- BFF Session 通过 HttpOnly Cookie 和显式 session query 表达；
- 只有无法合理归入以上类别的跨页面纯客户端状态，才评估引入 Zustand 等额外 store。

TanStack Query 不自动重试结果未知的业务 mutation。创建、审核决定、发布、secret 轮换和其它非幂等或需要显式并发前置值的命令，按对应 Console UC 决定人工恢复流程。

## Hono BFF

Vite 只负责 Web 构建。两个独立 Hono BFF 负责：

- 作为各自 Console Cookie 的唯一签发/解密权威，并按 [ADR-CONSOLE-004](ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 为普通 API 提供轻量 Session ForwardAuth；
- 执行 Origin/CSRF、请求大小、超时和响应头边界；
- 代理登录完成响应，使原始 Session 不进入可持久化的浏览器 JavaScript 状态；
- 处理登录、结果不确定恢复和明确登记的聚合请求；普通单服务 HTTP/JSON 请求不默认完整经过 BFF body proxy；
- 支持 OAuth 官方门户的同源 Session bridge；
- 隐藏内部 upstream 地址，但不复制 Auth/App 业务授权。

BFF 不签发可信用户身份、不读取服务数据库、不根据前端角色字段授权，也不把后端业务错误改写成成功响应。

## MSW 边界

MSW 在本地开发、Vitest 和确定性页面测试中拦截真实 `fetch` 契约。Mock handler 应复用生成类型并覆盖成功、空结果、权限拒绝、并发冲突、依赖不可用和结果未知等场景。

MSW 不进入生产构建，不作为端到端验收的后端替代，也不能使一个尚未实现的 Gateway/API 依赖被登记为已交付。关键登录、权限与审核链路最终通过真实 BFF、Gateway、Auth/App 环境验证。

## 结果

- 两个应用共享同一类型化技术栈，同时保留独立构建和部署；
- 状态来源明确，首版不承担 Redux 类全局状态框架的额外复杂度；
- BFF 降低 Session 暴露给浏览器 JavaScript 的范围；
- Mock 与真实网络使用同一 fetch 调用面，但生产交付仍需真实系统验收。
