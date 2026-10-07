# iWUT Console 产品范围

状态：`PROPOSED`

## 目标

iWUT Console 为平台自有用户提供两个相互隔离的工作入口：

- Developer Console 帮助用户完成账号准备、Developer 开通及 Application 生命周期管理。
- Admin Console 帮助平台管理员治理审核权限，并帮助具有相应权限的 Reviewer 处理 Application 资料与版本审核。

两个 Console 组合已有后端能力，不绕过 Gateway、Auth Center 或 App Center，也不直接访问服务数据库。

## 共享功能范围

- 设备或邮箱登录、Session 建立、失效处理和退出；
- OAuth 官方门户所需的同源 Session bridge；
- 当前账号资料、邮箱和 Developer eligibility 的必要入口；
- 统一的 API 错误、网络失败、超时、乐观并发冲突与结果未知提示；
- 安全处理一次性 secret、Tester join URL、Session 和设备私钥；
- 键盘操作、焦点管理、语义标记及错误提示等功能性可访问性要求。

共享范围不表示两个应用共享登录态。Developer Console 与 Admin Console 使用独立部署、BFF、Cookie 和会话边界。

## Developer Console 范围

- 查询本人 Developer 资格并完成允许的自助开通；
- 创建并管理本人持有的 Application；
- 管理 Application Version、公开资料修订、审核提交及拒绝后的后续编辑流程；
- 管理测试入口、Tester、发布槽位、Grey rollout、Application Filter 与 OAuth Client；
- 展示操作需要的当前 revision、状态、审核结果和后端返回的恢复信息。

只有后端已经提供权威读模型和 Gateway 入口的能力才可标记为前端完整交付。当前 App Center 的多项命令已经存在，但开发者管理读模型仍需单独设计和实现。

## Admin Console 范围

- 按已知或可查询用户管理两项独立 Application 审核权限；
- 分别展示资料审核和版本审核队列；
- 展示完成审核决定所需的一致详情、策略版本、检查项和利益冲突提示；
- 提交审核决定，并正确处理并发变化、权限变化和结果未知；
- 只向当前身份展示其服务端实际授权的入口，不以前端隐藏代替后端授权。

Admin Console 不提供数据库运维、任意主体修改、Scope Catalog 在线编辑或 Gateway 动态路由管理，除非未来已有独立接受的后端能力和 Console UC。

## 明确非目标

- 在前端复制或重新解释后端业务规则；
- 通过浏览器直接访问 MongoDB、内部 gRPC Provider 或服务身份接口；
- 把 mock 数据、客户端缓存或 URL 参数当作权限与状态权威；
- 在功能文档中固定品牌色、字体、间距、阴影、插画或像素级页面布局；
- 在首个工作包中一次性实现本文件列出的全部能力。
