# Console Use Cases

本目录保存 Developer Console、Admin Console 和共享账号入口的前端用例。

每个 UC 描述一个可独立验收的用户目标，不按页面数量机械拆分，也不把整个 Console 写成一个大用例。UC 应引用已有后端权威规则，只定义前端新增的流程编排、状态表达、失败恢复、客户端安全和功能性可访问性。

新 UC 使用 `UC-CONSOLE-NNN-verb-object.md` 命名，并在同一变更中登记到 `../design-registry.md`。设计被接受前保持 `PROPOSED`；进入实现前必须确认所需 API、Gateway 路由和查询契约的真实状态。

不预先为全部页面一次性设计后端 API。编写或实现 UC 时遇到缺失读模型/命令，应在当前 UC 或 `../query-contracts/` 记录最小功能需求和阻塞状态，再按“后端权威设计 → Proto/实现 → 统一 API → Gateway → TypeScript 生成客户端 → 真实 E2E”的顺序补齐。MSW 可以让前端分支并行开发，但不能把缺失依赖改记为已交付。

具体视觉样式不写入 UC，边界见 [ADR-CONSOLE-002](../adr/ADR-CONSOLE-002-functional-documentation-boundary.md)。
