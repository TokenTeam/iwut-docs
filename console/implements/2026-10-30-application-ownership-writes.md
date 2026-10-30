# Developer 应用归档与管理权交接

状态：`ACCEPTED / IMPLEMENTED / REPRESENTATIVE_REAL_CHAIN_VERIFIED`，2026-10-30。依据用户持续 goal 的自主设计与实施授权；功能由 [UC014](../use-cases/UC-CONSOLE-014-manage-application-ownership.md) 定义，后端业务权威为 App [UC033](../../app-center/use-cases/UC-APP-033-archive-and-unarchive-application.md) 和 [UC026](../../app-center/use-cases/UC-APP-026-transfer-application-administration.md)。本页登记实际交付与有限证据，不重定义业务规则，也不关闭完整 goal。

## 实际交付

- 应用设置分别读取归档状态与管理关系，确认绑定对应应用、当前状态和专用修订。归档与恢复按官方正文发送前置值，不使用 If-Match；正常界面不展示技术修订。
- 当前管理员填写已有账号的 opaque Auth ID，明确确认后发起转让。已有待处理申请提供详情入口，不自动覆盖目标；不提供自造的用户搜索、邮箱解析或通知服务。
- 转让详情使用独立参与者读取，接收方无需先拥有应用。源可以取消，目标可以拒绝或显式选择 KEEP/ROTATE 后接受；接受没有默认凭据策略。分享地址仅由用户明确复制，不自动发送或打开。
- 首次 ROTATE 回执的凭据仅保存在当前命令组件内存，按渠道显式复制、隐藏；离页、页面隐藏、会话变化与访问拒绝时清除，不进入 Query/Mutation 缓存或持久存储。未知结果只读取当前事实，不通过重复接受追回 Secret。
- 命令回执之后通过专用 GET 读回，保留已知修订下界与终态。Session、页面 lifetime、精确 Query 实例及较新数据保护由共享私有消费边界约束。
- 关闭区域只展示既有摘要和限制。近期认证、关闭证明及实际关闭写入仍未接通，本次没有把归档当成关闭或删除。

对应实现包括 `application-settings.tsx`、`application-transfer.tsx`、`application-settings-state.ts` 和 `application-settings-client.ts`；真实验收新增 `developer-ownership-writes.real.spec.ts`、`ownership-write-fixture.ts` 及 runner 的限定准备/观察接线。

## 集中静态与组件检查

根代理提供的既有证据：UC014 client **56 项通过**，设置、转让及原配置集成 **54 项通过**。这些结果由相关实现/集成代理执行并转报，本页真实验收代理没有把它们重新执行或计入实链通过数。

本次真实验收前，`test:real:types` 与 runner 语法检查通过；`test:real:privacy` **1/1、exit0**，验证失败报告不会持久化输入内容。新增 spec 从 `./test` 隐私包装导入，trace、截图与 video 均关闭。没有输出验证码、Session、私钥、加入链接或一次性凭据。

## 隔离真实专项

轮次 **114910** 首轮终态为 **1/1 通过、exit0，无 skip/retry**；单项浏览器执行27.4秒，Playwright 汇总28.0秒。实际执行入口：

```sh
VITE_VERSION_DRAFT_WRITES=true \
E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f \
E2E_GATEWAY_PULL=false \
node scripts/test-real-services.mjs tests/real/developer-ownership-writes.real.spec.ts
```

使用私有临时 PATH wrapper 调用已缓存 pnpm；未修改全局工具、未编译后端。Auth/App 按默认流程重新拉取 published `latest`；Gateway 明确使用已构建本地镜像，来源为 `explicit-local-gateway`，不能把本轮称为 published Gateway 验收。

| 后端 | 实际固定 image ID |
| --- | --- |
| Auth | `sha256:518b0917ec8302f9f6cb28bd2e12aa59033cfe6db45c82a81a0afcb1bac5aa16` |
| App | `sha256:68ee32b1e92145734bfa7fe61d003ee7e2ed2bb8b20fd944f861704a8f48ad01` |
| Gateway | `sha256:90cf10f0ea832812ee756e686362e0114d493e090b2286aef76dd9304007fdd7` |

固定官方 API 输入仍为 `6fea3db899d3d096d4d3dfc59b2c85432a4b9eb6`。runner 先完成生产静态构建及 setup/driver 打包再建立轮次 network；构建期间各产品文件停止编辑，构建结束后允许源码继续编辑，但当轮 dist 保持不变。以下 SHA256 在该静态构建完成后记录，不能拿后续 dist 替代：

| 产物 | SHA256 |
| --- | --- |
| Developer `index-DngIePw1.js` | `684220f7f855a1c550a8948cfacf77752c8f23d2a0b9b78c2cf79a3f0830ccf5` |
| Admin `index-3FaQHHzh.js` | `a23e8fff40e8abd9004af98fce5daef70011821ba2e0fd77b49819bfc88e7d7e` |

该构建同时包含当时尚在收尾的 UC010 预填与 UC015 Admin 源码；本项只操作 UC014，不以构建成功或 Admin hash 证明这两项功能已验收。

## 准备边界与十次页面命令

专用源和目标账号通过正式注册、Apply、DEVICE 准备；各自只消耗注册1封与浏览器 EMAIL 登录1封，共2封/小时，并遵守真实邮件冷却。两个独立 BrowserContext 分别通过实际 React 邮箱登录，没有从 Node 拷贝 Session。测试成员复用既有普通账号的 Node DEVICE 能力，只向本轮新应用正式 Join，不新增该账号邮件或改变旧应用的成员 episode。

准备阶段正式创建两个独立应用，各登记 TEST Confidential 客户端、创建邀请并加入一个成员；准备回执中的 Secret/加入 URL 只在 Node 临时作用域使用，不返回控制端。没有 seed 本链成功状态，不复用原只读矩阵固定的25成员/26链接应用，也没有使用预览数据库。

浏览器通过生产 React 页面完成 **10次 App 写入**：

1. KEEP 应用归档、取消归档；专用归档修订从1到2再到3。
2. 四次明确发起转让，分别进入取消、拒绝、KEEP 接受与 ROTATE 接受；发起均为201，专用 ownership 基线保持到最终接受。
3. 源取消一次、目标拒绝一次、目标接受 KEEP 一次及 ROTATE 一次；这些处理均为200，并有独立参与者 GET 读回。

核对正式正文、ProtoJSON 枚举、无额外 If-Match、对应201/200与 no-store 契约；归档及私有读取继续保留 private/no-store 断言，没有为转让成功响应额外发明 private 要求。

真实结果还核实：

- 目标未拥有应用时即可从独立转让详情读取并拒绝；操作未依赖 owner 专用管理摘要。
- 两个应用最终都由目标管理，ownershipRevision为2且无 pending transfer。源再次进入 owner 页面时管理详情正式返回404，但仍可读取自己参与的 ACCEPTED 转让终态。
- KEEP 的 Confidential credentialRevision保持1、轮换归因保持源；ROTATE升至2、归因为目标，clientId保持不变。ROTATE只披露一个 TEST 凭据，页面值与首次回执一致。
- ROTATE Secret没有进入 localStorage/sessionStorage；带未隐藏凭据离页后返回及刷新都不能恢复显示，终态页也不提供再次接受按钮。本项没有为追回 Secret 重放接受命令。
- 两个原活动邀请均以 ADMIN_TRANSFER 撤销，没有自动创建替代链接；各自原 membership episode保持ACTIVE，activeTesterCount保持1。
- Node 观察能力只对两个已固定应用读取管理、归档、ownership、凭据元数据与测试管理事实，不接收任意 RPC/目标或访问数据库。控制入口拒绝额外正文、query与未知操作；重复 prepare只返回原准备结果，不重放正式写入。
- 双方原 Browser Session 的 authId、generation、contextBinding保持；没有外源请求或新标签页。

终态后轮次容器（包括停止项）与 network均为0；原预览轮次的五个容器继续运行。私有运行材料保存在仓库外，没有凭据或原始诊断内容进入文档及版本控制，未提交或推送本轮改动。

## 有限范围与下一门禁

本轮只证明上述成功组合及明确的数据/会话边界。它不等于旧128项完整回归，不覆盖所有渠道、超时/冲突/拒绝排列、过期收敛、失效资格、页面隐藏与 Session 变化的全部浏览器矩阵，也不替代 UC010/UC015 自身验收。关闭/BFF证明和正式 IP 部署仍属独立范围。

下一步等待 UC010/UC015 源码定稿及根代理确认后，再集中运行 ordinary 检查与无 spec 筛选的完整真实门禁。准备方案沿用同一隔离 runner、默认 Auth/App latest、显式本地 Gateway 9d6a27f、私有缓存 pnpm wrapper与隐私报告；不加 skip/retry、不放宽邮件预算、不从相邻仓编译后端。构建前冻结产品源，完成后记录静态 hash并保持当轮 dist不变；只清理本轮资源。届时按实际发现和终态记录总数，不提前宣称全量通过。本页登记时尚未启动该轮。
