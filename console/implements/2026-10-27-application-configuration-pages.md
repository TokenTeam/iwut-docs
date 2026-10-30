# Developer 应用配置页面首版

状态：`IMPLEMENTED / LOCAL_VERIFIED / VISUAL_REVIEW_PENDING`。

用户要求补齐其他应用管理页面。本包按已接受的[页面结构](../page-architecture.md)，补充接入配置、展示规则与应用设置三个独立模块；复用 [UC002](../use-cases/UC-CONSOLE-002-query-owned-applications.md) 已有管理摘要，不引入新业务命令。

## 页面职责

- 接入配置 `/applications/:appId/integration`：按正式、灰度、测试渠道区分 PUBLIC 与 CONFIDENTIAL 客户端，显示服务返回的 clientId、状态及凭证轮换元数据。注册、授权代际与凭证修订放在技术信息中。未知渠道和状态保留原值，不静默丢弃。回调地址和权限声明引导到版本工作区，不把它们当作 registration 配置。秘密不读取、不恢复、不渲染输入框。
- 展示规则 `/applications/:appId/display-rules`：显示 Filter 模式与次级修订信息，保留独立全页编排区域。初始零修订摘要按后端默认 ALLOW_ALL 表达；已有修订却缺少模式不猜为 ALLOW_ALL。当前没有规则树或字段目录，不渲染虚构条件、空白表单或保存动作。适用范围与语义引用 [App UC022](../../app-center/use-cases/UC-APP-022-manage-application-filter.md)。
- 应用设置 `/applications/:appId/settings`：分为不可变技术信息、独立运行状态、归档、管理权及关闭历史。待处理转让只显示摘要，不从本地时间推断申请终态；管理员账号 ID 不扩查个人资料。关闭历史不提供取消或恢复。业务语义分别引用 [App UC033](../../app-center/use-cases/UC-APP-033-archive-and-unarchive-application.md)、[UC026](../../app-center/use-cases/UC-APP-026-transfer-application-administration.md) 与 [UC027](../../app-center/use-cases/UC-APP-027-close-application.md)。

应用模块导航补齐为概览、版本与发布、公开资料、接入配置、展示规则、应用设置。三个新页面均支持深链接、当前应用上下文、显式刷新与查询时间；未改变用户调整后的外层侧栏与滚动方式。文档只规定结构、职责和交互语义，具体样式继续通过原型调整。

## 数据与能力边界

三个页面与概览共用同一管理摘要 hook、固定生成类型和 `GetMyApplication` 同源查询，不新增 API pin、查询根或 BFF 聚合。每条路由有独立资源 attempt；查询仍按原 Session/application scope 退场，离页清理与常驻侧栏清理策略不变。网络/503 仅保留同上下文带原 asOf 的旧快照；协议错误清精确 Query.data；权限拒绝卸载内容与关联侧栏摘要；旧会话迟到正文不能填入新代页面。

当前 Gateway 工作区的 OAuth registration/credential、Filter、归档、转让和关闭专用路由没有 DEVELOPER surface，本包不调用这些路由，也不以邻接源码代替发布镜像验收。客户端元数据、Filter 摘要和生命周期状态来自原已开放的 `GetMyApplication`，读取成功不代表具备写权限。完整规则读取、编排、登记、轮换、归档、转让及关闭仍需独立接线与验收；没有假成功、禁用保存按钮或新密码收集流程。

## 验证

新增 21 项组件测试使用合成 HTTP 响应，不 mock 生成 client 或私有读取边界；覆盖六模块导航、三渠道/未知渠道与客户端类型、Filter 默认/规则/未知模式、三生命周期历史、未登录门禁、三页拒绝退场、不自动重读、503 旧快照与恢复、协议错误不复活、跨应用及换代迟到响应。首轮 21 项有 11 项失败，原 31 项 Application 回归通过；原因是新测试把重复名称当唯一元素，以及把会话焦点重读计入业务自动重读。改为等待页面数据时间、按业务请求计数后 21 项通过。新测试误用了另一测试库的 `exact` role 参数，已按 Testing Library 类型修正；未放宽业务断言或产品边界。

工作区 1148 项 Vitest（Developer 374）、16 项构建/CSP Node 回归、工作区及 real/privacy 严格类型、全生产构建通过；独立性检查 358 文件、72 份 brief、App registry 与 diff 检查通过。Vite future-native-loader 与大 chunk 提示保留，未屏蔽。组件的合成响应不代表真实业务 E2E；本包不重跑已发布镜像浏览器全量，不关闭完整 UC/goal。当前 Vite dev 本地热更新服务继续运行，三个新深链接返回 HTTP 200 且仍为 dev 源码服务；后端数据不重建，未恢复 NetBird 暴露，未 commit/push。实际浏览器观感仍由用户试用确认，不绕过此前浏览器访问限制运行其他控制工具。
