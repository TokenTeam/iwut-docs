# Developer 创建、保存与送审接入

状态：`ACCEPTED / IMPLEMENTED / P0_REAL_CHAIN_VERIFIED`，2026-10-30。用户重新激活既有自主实现 goal，授权记录决策后自行接受与实施；本页维护实际接入证据，不把部分验证变成整体 Console 完成。

## 范围与决策

当前开发优先完成“创建应用 → 完善公开资料和版本 → 明确送审 → 审核 → 发布”。应用创建为 [UC009](../use-cases/UC-CONSOLE-009-create-application.md)，版本工作区扩展 [UC008](../use-cases/UC-CONSOLE-008-version-workspace.md)，资料工作区为 [UC010](../use-cases/UC-CONSOLE-010-edit-application-profile.md)。这些用例只规定功能结构与交互，延续当前同一骨架的亮/暗主题与 Tailwind/HeroUI，不规定视觉样式。

- 应用、版本、资料的新建与大内容编辑使用整页；技术名称和公开名称独立，版本声明与公开资料独立。
- 已有草稿对完整有效快照串行自动保存；新建、送审、恢复和放弃为明确命令。送审前必须已保存且再次确认。
- 正常操作不展示或要求输入 revision；实际客户端保留前置值。冲突、明确拒绝和未知结果按职责暂停，读回后由用户采用基线，不自动重放未知写。
- 新接口继续走逐 surface 的 Console Session ForwardAuth、Gateway 身份交换与后端授权；没有浏览器 Session header、直连后端或临时通配 BFF。
- [本地镜像 runner](2026-10-30-local-gateway-runner.md) 提供显式 Gateway 不拉取模式；无参数发布验证仍拉已发布 latest。

## 源与镜像

改动前已有内容保存为 Console 检查点 `869e2f9`，并建立 `checkpoint/2026-10-30-console-workspace`。原 `legacy` 仍为 `e68851e`，没有重置或覆盖。检查点保存了此前 UI/组件/发布设置工作，不表示其后新增写入已被真实验证。检查点中已有 `publication-panel.tsx` 的末尾空行提示另行整理，不隐藏为门禁已通过。

Gateway `9d6a27f` 在既有 130 RPC 上新增 47 条 route 的 Console 声明；前端已独立核对全部 P0/P1 请求，凭据/身份矩阵与旧版逐项相同，特殊关闭/Scope/学年入口保持关闭。Gateway 自仓本地构建：

```text
tag: iwut-gateway:console-local-9d6a27f
image: sha256:90cf10f0ea832812ee756e686362e0114d493e090b2286aef76dd9304007fdd7
API: 6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6
```

该镜像用于本轮开发，不冒称远程 CI 产物。官方同镜像 renderer 与 runtime 已在现有预览接入，保留原 Gateway 容器为回滚实例；Mongo/Auth/App 数据、BFF 密钥和会话未重置。九条 P0 写路由在渲染后检查为 Developer-only，已知六条发布路由保留。实际匿名创建请求在 Developer 为 401/private/no-store，Admin 为 404；页面和 Session 仍为 200。这证明入口链已接入，不证明真实创建成功。

当前 NetBird 双端使用的本机临时部署适配沿用 [Gateway 交接](2026-10-30-gateway-console-capability-gaps.md#p2ip-加端口的正式本地配置能力) 所述边界，尚未升级为正式 Gateway 支持。实际证书、邮件和任何个人配置仅在私有运行目录，不进本仓。正式 entrypoint 方案不阻塞 P0，但不因此标记 P2 完成。

## 产品实现

| 部分 | 已实现 | 尚需实际证据 |
| --- | --- | --- |
| UC009 应用创建 | `/applications/new`，列表/侧栏入口，原样 name，创建回执 owner/目标检查，正式详情导航，未知不重创 | 真实 React 创建及后续管理读取已通过；剩余失败矩阵不由成功链代表 |
| UC008 版本 | 同页新建/编辑，串行保存，明确送审/恢复/放弃，ACK 下界单调读回、未知只读核对、输入保留 | 真实创建/保存/送审已通过；恢复和放弃仍需独立真实动作证据 |
| UC010 资料 | 全页新建/草稿编辑，显式nullable字段，串行保存/明确送审，ACK后真实详情；REJECTED只读并可显式预填新建，正文仅短命内存 | 真实创建/保存/送审已通过；拒绝后新建预填49组件/7client通过，仍用正式Create，不虚构恢复命令，新增预填未借先前实链宣称验证 |
| 原功能 | 应用/版本/资料/Tester 读取、Admin 两类审核、发布六命令继续保留 | 本轮代表性回归与适时整体验证，不借过去128项绿结果替代 |

版本写入以当前 Gateway 契约默认启用；部署可显式 `VITE_VERSION_DRAFT_WRITES=false` 保持只读编辑器。此变量不代替权限检查或路由探测。P0真实链通过后，预览已切换为显式 true 并重启 Dev/BFF 宿主；沿用原 NetBird BFF 数据库和密钥，未清数据库或会话。开发收件箱内存随宿主重启清空，可请求新验证码。

## 验证记录

集中进行有意义的回归，遵守用户不要求每次 UI 修改后整套测试的偏好：

- 应用创建 client 10/10、创建页 8/8、既有列表/侧栏 46 项、新创建入口/静态路由 1 项通过（subagent 执行）。
- 资料 client 7/7、资料编辑与既有查询 39/39 通过（subagent 执行），覆盖未知不重放、后续输入、写拒绝安全退场、旧编辑器不覆盖 same-key 新 Query。
- API client 与 Developer strict 在整合后均 exit0。版本命令 client 46/46、Workflow与原Editor19/19通过；读回修订下界跨重读保持，以及成功读回清除旧错误均有组件回归，后者已进入实际构建。
- 本地镜像 runner 配置/CI 定向回归 31/31、语法与实际 image inspect 通过；旧命令精确断言首轮失败及修订记录保留在对应实现页。
- 新增 `developer-write-workspace.real.spec.ts` 使用已正式开通的测试 owner、独立浏览器 context，在隔离数据库中通过生产 React 创建全新 App/Version/Profile；不修改其原读取矩阵 App，不 seed 本链业务资源。第三轮 handle52740 为 exit0，专项 **1/1**，浏览器10.3秒，types/privacy前置通过。Gateway90cf10f0、Auth518b0917、App68ee32b1；每轮Auth/App实际pull latest，本地Gateway显式inspect且不pull。
- 第一轮71677在 EMAIL Complete 错误预期200时失败，真实成功码201，尚无 App 写；第二轮76827在 UI CreateApplication 错误的统一响应helper预期200时失败，真实201且已创建一个隔离App。两轮均exit1且资源清空；没有把它们记成产品失败或成功链。依据正式编码集中核对七命令后，五次POST精确201，两PUT/各GET精确200；原GET的private/no-store断言保留，未对无权威要求的成功写额外发明缓存断言。
- 第三轮实际静态JS `index-OsuMQHqK.js` SHA256 `a1a770bf4fca94fffc168cbb14ca73cbf33ccf658c7d0bf4b531f4ae574d125e` 包含成功读回清旧错误的修正。P1新源码在此静态构建固定后才并行推进，不把该成功链扩大为P1验收。三轮测试容器/网络与临时pnpm wrapper均清理，既有预览及回滚容器保留；无当前个人数据写入。

真实 spec 核对每次写 ACK 和随后 GET 的 target/revision/review，要求恰好七次业务写、零外域请求、原 Session 代际保持；测试从 `./test` 导入，trace/截图/video关闭，不输出 OTP/私有响应。恢复、放弃、审核后发布及新 P1 功能不由这一条测试代表。

## 后续实际进展

同日轮次100874在新的P1构建中集中执行本页P0与[测试、OAuth、Filter管理](2026-10-30-developer-management-writes.md)，**2/2、exit0，无skip/retry**，P0再次通过。该包记录P1的11次实际页面写、客户端/组件修正和资源清理；不把本页第三轮1/1扩大为P1证据。

## 下一步

P0成功链已收齐并开启预览写入；Tester管理、OAuth接入和Filter编排已有上述代表链。继续UC014归档/转让与UC015 Admin治理，必要时新增功能UC并记录自主决策，保持当前goal完整范围。本轮未跑旧128项默认全量、未覆盖恢复/放弃及审核后发布，后续按实际变更补证据。账号安全/BFF、正式政策发布和Cookie传输边界仍单独开放，不能通过重复既有绿门禁或忽略契约来宣布全目标完成。
