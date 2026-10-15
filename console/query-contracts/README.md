# Console 查询契约

本目录记录页面读取后端事实所需的应用层语义和依赖状态，不保存 mock response 作为权威数据模型。

若 Auth Center 或 App Center 已拥有对应 query contract，Console 只引用它并补充页面消费方式；不得复制后形成第二份状态定义。后端尚无查询时，可以在此记录结构化需求，但最终业务读模型仍由拥有数据的 bounded context 接受并实现。

- [Version 审核决定接入准备](version-review-decision-readiness.md)：UC-CONSOLE-006 的现有 wire、正式检查定义来源与 Gateway ADMIN 决定路由缺口及解除证据。
- [登录 flow fencing 缺口](login-flow-fencing.md)：UC001 页面取消与 BFF Cookie 并发的能力边界、跨副本/重启要求及待定架构；不是已经接受的新 Session 契约。
