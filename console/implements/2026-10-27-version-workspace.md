# Developer 版本工作区初版

状态：`INITIAL_IMPLEMENTED / WRITE_INTEGRATION_BLOCKED / VISUAL_REVIEW_PENDING`。

## 2026-10-28 发布设置增量

本节是发布设置的最新进展；下文“发布命令不在初版范围”和版本草稿写入受阻均保留其原阶段边界。用户已明确授权这次发布设置接通，不代表解除版本创建／更新／提交或 Tester 写入限制。

- 拉取已发布 Gateway `latest`，实际 image ID 为 `sha256:b8a5b26f46e51613623ad212a66cf17cc14c7f4fbb9909e684807347cc55b87a`。镜像生成的配置包含六条 DEVELOPER 发布路由，无对应 ADMIN 路由。本地仅替换 Gateway 并重载 Traefik，保留 Auth/App/Mongo、登录 Session、设备钥匙与 BFF；未编译后端、未改业务数据。
- 第一次本地切换遇到容器生成文件属主问题，自动恢复旧 Gateway；修订为发布宿主拥有的配置副本后切换成功。单文件 bind mount 还需要重启 Traefik 重新挂载，不以宿主文件替换直接宣称路由已加载。正确 Origin 与完整 Fetch Metadata 下，匿名 Developer 写请求实际返回 `401 SESSION_INVALID`、`private, no-store`；缺失 Metadata 的 403、Admin 不匹配的 404 与重启瞬间 502 均不当成业务发布证据。
- API 仍固定 `6fea3db`，从官方远程输入新增 Publication 与错误码生成子集。客户端设置使用 Command ProtoJSON，清空使用精确 bigint revision query；不发送自造 If-Match，不重试写入，严格校验回执归属、目标渠道、修订与历史。
- 版本与发布页加入三个渠道的设置、显式 major／新分区、APPROVED 候选显式分页、百分比至万分比精确转换、明确确认、设置与清空。概览仅提供前往管理入口，两个页面的卡片始终展开，测试配置为同级导航。
- 写后正式读回管理摘要，不把写回执直接塞成摘要；冲突／拒绝／未知暂停操作，明确读回后再确认新基线。使用原 Session 和私有资源消费边界，迟到响应不能向新 Query 实例填数据；不持久化私有表单，不自动刷新并重放旧操作。
- 一次聚焦验证：API client 15/15、Developer Publication 两文件 20/20；API 与 Developer 严格类型检查通过。仅小范围合成检查，没有跑全量测试、production build、真实浏览器或真实账号发布成功链，不以此关闭完整 UC／真实发布验收。

状态：`IMPLEMENTED / FOCUSED_VERIFIED / REAL_PUBLICATION_PENDING`。开发页面已可试用；真实设置、清空、OAuth／公开资料／Scope 前置条件及多端交错仍需后续实际联调。不自动操作用户现有应用来冒充验证，未 commit/push。

后续同日用户修订为整张卡片触发 HeroUI Modal：不再保留卡片内设置按钮，当前引用默认选中，惰性精确读取所选版本基本信息，并提供版本工作页跳转。未加载到当前引用时不无限补页，版本资格仍由详情读取和服务端命令复查。正常关闭支持焦点恢复；在途／未知继续禁止未经核对关闭来重新提交。该交互修订的严格类型检查通过，未重跑上述聚焦测试，旧 35 项结果不挪作浮窗验证。

用户接受先做文档和初版、通过使用调整结构。[UC008](../use-cases/UC-CONSOLE-008-version-workspace.md)与[页面结构](../page-architecture.md)规定功能关系和交互，不固定排版。HeroUI 基础沿用[前一工作包](2026-10-27-heroui-foundation.md)。

## 初版范围

- 应用工作区的平级导航；已交付的概览、版本与发布、公开资料保持深链接，规划中的接入配置、展示规则和设置不生成空壳页面。应用名称的统一上下文与其他旧页面信息重组仍需后续迭代。
- 版本与发布主页：独立读取 Application 的 Publication 摘要，选择已有 RPC major，正式、灰度、测试三槽位分别折叠；空分区不虚构 major。测试区进入应用级成员/链接页。
- 全部版本保留原单状态筛选、游标、每批数据时间和拒绝投影回收；默认显示标签、状态、序号、创建时间、审核摘要和下一步提示，技术 ID/revision 不再铺在列表中。槽位只有引用时按引用进入详情，不无界补查版本名称。
- 新建与已有版本共用整页表单，分组填写入口、RPC 兼容性、能力、Scope 和回调；SUBMITTED/APPROVED/REJECTED 只读，最新审核仍单独展示。
- 生成类型的同源创建/更新 client；整份替换、强 If-Match bigint、800ms 防抖串行保存；旧 ACK 不赋值回表单；无效中间输入不发送。冲突、失败和未知暂停，创建未知不重放。
- 新建清空、已有草稿还原进入时基线的确认、未保存/在途/未知的离页保护；不默认持久化私有输入，不依赖卸载发送保存。原访问拒绝和 Session 退场优先。

## 网络写入边界

核对当前 Gateway `routes.v3.yaml`：`app.create-application-version` 与 `app.update-application-version` 都没有 `consoleSurfaces: [DEVELOPER]`。本包不改 Gateway、后端、BFF 代理或信任链，不向外部聊天发送消息。

`VITE_VERSION_DRAFT_WRITES` 默认 false；当前本地预览也是 false。可以填写和重置，页面明确说明未保存，不发送业务写请求。创建/自动保存路径目前只有合成客户端与组件测试证据。只有对应路由部署、通过 Console 实链验证后才可构建开启；该变量不提供服务端授权，也不探测/回退路由。

提交审核、拒绝后恢复、放弃、发布槽位写入、灰度设置、Tester 写入均不在本包交付范围；不宣称 Developer 创建到发布的闭环已完成。

## 验证范围

本轮工作区 1111 项 Vitest 通过（Developer 337、API client 214；比 HeroUI 基线增加 43 项），默认 377 项 Node 测试通过；工作区严格类型、real/privacy/build-policy 类型及全生产构建通过，独立性检查通过。文档 72 份 brief、App registry、22 个新增相关本地链接及 diff 空白检查通过。原真实 128 项与 HeroUI 两项的结果属于各自冻结，不挪作本次页面变更验收。

新增测试覆盖：四个槽位/major 场景、表单转换与输入、同源 ProtoJSON/强前置值、串行/迟到/未知保存、全页创建/只读/重置/离页。旧只读断言已改为读取表单值与次级技术信息；追加离页测试首轮因等待被阻止的导航 Promise 超时，且影响下一用例（335 通过、2 失败），修订为确认调用与最终位置断言后工作区全部通过，没有删除离页护栏。

构建仍有原 Vite future-native-loader 与大 chunk 警告，未屏蔽。Developer 当前约 441 kB CSS / 828 kB JS（未 gzip）；代码拆分和视觉微调留后续迭代，不以测试数量宣称性能或体验已经完成。

原两个版本浏览器 spec 和正式关闭后版本读取 spec 已按表单值、折叠技术详情及引用导航调整断言；本轮不宣称其已运行。浏览器工具访问本地预览被安全策略拒绝，未通过其他浏览器入口绕过，视觉检查待用户刷新预览。

本地预览仍为 `https://developer.localhost:37117` 与 `https://admin.localhost:37117`，公网侧只监听 loopback，Docker bridge 仅供内部转发；未恢复 NetBird 绑定。原后端容器/数据和 BFF keys 保留；修复临时预览脚本把 bridge 绑定错误探测为 loopback 导致启动失败的问题。HTTP 状态检查两端 200，不等于已完成登录后视觉验收。

未 commit/push；未重跑默认 published-latest 全量或命令实链；不关闭整体 UC/goal。
