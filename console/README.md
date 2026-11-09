# iWUT Console 设计

状态：`ACTIVE`

## 定位

本目录保存 iWUT Developer Console、Admin Console 及其共享浏览器/BFF 基础能力的权威前端设计。

技术仓库名为 `iwut-console`。两个产品界面分别使用：

- **吾理开放平台**：面向 Developer 的应用管理入口。
- **吾理平台管理**：面向平台管理员与 Reviewer 的治理入口。

代码位于独立的 `iwut-console` 仓库。pnpm workspace、两个独立应用/BFF、设备/邮箱登录与共享私有读取已建立；整体 UC001 仍保留独立架构边界，实际覆盖见 [实施索引](implements/README.md)。

## 权威边界

2026-10-30 [Developer 页面结构](page-architecture.md)继续按接受的全局与平级应用工作区迭代：版本和发布合并、接入配置与展示规则独立。Gateway普通路由已补齐，应用/版本/资料写入与测试/OAuth/Filter管理已有[代表性真实页面证据](implements/2026-10-30-developer-management-writes.md)；归档/转让和Admin治理另包推进。文档描述结构与作用，不固定布局；组件基础见 [HeroUI 工作包](implements/2026-10-27-heroui-foundation.md)。

Console 文档定义：

- 用户能够进入哪些前端流程、看到哪些业务状态并执行哪些已存在的后端能力；
- 页面之间的导航、恢复、失败、重试、并发冲突和敏感信息处理语义；
- Developer Console、Admin Console、BFF 和共享 package 的责任边界；
- 前端特有的安全、可访问性、浏览器存储和测试要求。

Console 文档不重新定义 Auth Center、App Center 或 Gateway 的业务规则。服务端权限、状态迁移、字段约束和错误含义仍由对应后端 UC、BR、平台契约和可执行 API 拥有；前端用例通过稳定 ID 或路径引用它们。

本目录不规定具体视觉样式。颜色、字体、间距、阴影、图形风格、像素布局和纯审美动画不属于 UC/BR/ADR 的业务权威。详见 [ADR-CONSOLE-002](adr/ADR-CONSOLE-002-functional-documentation-boundary.md)。

## 文档结构

| 路径 | 责任 |
| --- | --- |
| `product-scope.md` | 两个 Console 的功能范围与非目标 |
| `use-cases/` | 前端用户目标、组合流程和客户端规则的权威正文 |
| `query-contracts/` | 页面读取后端事实所需的读模型语义与依赖状态 |
| `adr/` | 重要前端架构决定 |
| `implements/` | 实现覆盖、工作包与验收状态 |
| `design-registry.md` | Console UC、BR、ADR 的索引和编号空间 |

## 已接受的架构决定

- [ADR-CONSOLE-001](adr/ADR-CONSOLE-001-repository-and-application-boundaries.md)：一个 Git 仓库内放置两个独立 Web 应用和两个独立 BFF。
- [ADR-CONSOLE-002](adr/ADR-CONSOLE-002-functional-documentation-boundary.md)：权威文档描述功能与交互语义，不固定具体视觉样式。
- [ADR-CONSOLE-003](adr/ADR-CONSOLE-003-frontend-technology-baseline.md)：固定首版 React、Vite、TanStack、Hono 和测试技术基线。
- [ADR-CONSOLE-004](adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)：共享 Traefik；登录/恢复/聚合经过独立 BFF，普通 HTTP/JSON 请求经 BFF Session ForwardAuth 后进入现有 Gateway 认证链。

## 当前用例

完整编号、状态与权威位置见 [设计注册表](design-registry.md)，实际验证范围见 [实施索引](implements/README.md)，不在入口页重复维护另一份阶段状态表。

- UC001：双端浏览器Session、设备/邮箱登录与恢复。
- UC002–005：开发者应用、版本、资料和测试管理读取；UC006–007：两类独立审核任务。
- UC008–010：版本与发布工作区、应用创建、公开资料草稿与送审。
- UC011–014：测试成员/邀请、OAuth客户端、展示规则、归档和管理权交接。
- UC015：人员资格/权限治理与应用可用状态，保留独立运维权限发现的明确缺口。
- UC016：本人账号资料全页编辑，目录驱动且明确提交；共享实现、普通验证与双端五类型代表实链通过。
- UC017：显式退出当前工作台，精确Auth撤销与Console按代清理分别确认；普通、Mongo及双端真实Auth退出代表链通过。
- UC018：Developer 独立本人资格入口，明确申请或补设永久开发者 ID，再主动进入创建应用；首次申请与原会话创建的代表实链通过，当前完整候选回归另行记录。
- UC019–022：平台脚本维护、独立审核、发布门禁与应用引用已获 2026-11-10 实施授权，初版实现与三角色代表实链已完成。整体页面责任、权限治理增量、后端设计依赖与既有策略/运维的验收安排见 [2026-11-09 设计总案](design-notes/2026-11-09-console-completion-design.md)。
- UC023：[查看应用管理动态](use-cases/UC-CONSOLE-023-query-application-management-activity.md)，设计 `ACCEPTED`、实现 `LOCAL_VERIFIED`。单应用六类审核事件与最小历史详情，消费已交付 App UC052；联合验收见本轮实施记录，不包含个人收件/已读或真实通知。

## 开工规则

实现一个前端功能前，先建立一个边界清晰的 Console UC 或工程工作包，并确认它依赖的后端查询、命令、Gateway 路由和部署能力已经实现，或把缺口明确登记为外部依赖。不得以 MSW fixture 冒充已交付的生产 API。

不要求在前端开工前预先猜完全部后台查询。某个 UC 在设计或实现中发现缺失 API 时，先在该 UC 或 `query-contracts/` 登记所需事实与阻塞状态，再由对应后端补充权威 UC/查询契约、Proto 和实现；统一 API 与 Gateway 路由更新后重新生成 TypeScript 客户端，最后解除阻塞。前端不得先发明长期临时 DTO，Gateway 路由存在也不能替代缺失的后端读模型。

设计状态与实现状态分开维护。`ACCEPTED` 只表示可以作为实现依据，不表示页面、BFF、Gateway 路由或部署已经完成。
