# ADR-CONSOLE-001：Console 仓库与应用边界

状态：`ACCEPTED`

日期：2026-10-05

## 背景

Developer Console 与 Admin Console 使用相同的浏览器认证协议、API 编码、基础组件和测试设施，但面向不同角色、业务流程和风险等级。需要在避免共享代码漂移的同时，使 Admin 构建、部署和会话不与 Developer 界面混合。

考虑过三种组织方式：

1. 单个 React 应用，通过 `/developer` 与 `/admin` 路由隔离；
2. 一个 Git monorepo 中的两个独立 npm 应用；
3. 两个完全独立的 Git 仓库，并另外复制或发布共享 package。

## 决定

建立一个名为 `iwut-console` 的 Git 仓库，使用 pnpm workspace。Developer 与 Admin 使用 npm 项目级隔离，不使用单个 Router 根的路由级隔离。

首版逻辑结构为：

```text
apps/
  developer-console/
  developer-bff/
  admin-console/
  admin-bff/
packages/
  api-client/
  browser-auth/
  bff-auth/
  ui/
  validation/
  test-utils/
```

两个 Console 分别拥有独立的：

- `package.json`、Router tree、Vite entry 和构建产物；
- BFF 进程、部署配置、公开 origin、Cookie 名称与 Session 生命周期；
- 环境变量、CSP、发布流水线和端到端测试入口；
- 业务 feature 目录，不从另一个应用导入页面或业务组件。

共享 package 只承载稳定的横切能力。`ui` 提供基础组件而不拥有 Developer/Admin 业务流程；`api-client` 不缓存业务状态；`browser-auth` 不决定角色或页面权限。`bff-auth` 只提供服务端 Cookie 封装、Origin 检查、Session 密文和上游凭据保管机制，不包含产品权限判断；两个 BFF 仍分别注入自己的 origin、Cookie 名和密钥，不能读取对方的 Session。

Git 仓库不是安全边界。Admin 安全边界来自独立构建与部署、独立 BFF/Cookie、Gateway 显式路由，以及 Auth/App 的最终授权校验。

## 结果

优点：

- 两个应用可以独立构建和部署，Admin bundle 不包含 Developer 页面；
- 认证协议、API runtime 与测试向量只有一个实现来源；
- 后端契约变化可以在同一提交中更新共享客户端和两个消费者；
- package 边界为未来拆分仓库保留清晰切点。

代价：

- CI 需要识别受影响 workspace，避免所有改动无条件构建全部应用；
- 根级依赖与工具升级会同时影响两个产品，需要统一验证；
- repository 访问权限不能分别授予两个前端团队。

当两个产品由不同团队维护、仓库访问必须隔离，且共享 package 已具备独立版本发布能力时，可以提出新的 ADR 将它们拆为两个 Git 仓库。在此之前不复制安全敏感的浏览器认证实现。
