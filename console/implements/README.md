# iWUT Console 实现状态

## 当前状态

| 工作包 | 设计 | 实现 | 缺口 |
| --- | --- | --- | --- |
| Console 工程初始化 | `UC-CONSOLE-001`（`ACCEPTED`） | `IMPLEMENTED` | pnpm workspace、严格 TypeScript、固定统一 API 生成输入与验证命令已建立；真实服务 E2E 仍属于 UC001 整体缺口 |
| 共享浏览器 Session | `UC-CONSOLE-001`（`ACCEPTED`） | `IN_PROGRESS` | 浏览器密钥/协议、BFF 边界、登录/重发/页面回调隔离及双 Console 真实邮件/设备主链通过；跨请求 Cookie fencing 和完整恢复/并发矩阵仍待完成 |
| Developer Console 功能 | `UC-CONSOLE-001`（认证入口）、`UC-CONSOLE-002–005`（只读管理） | `IN_PROGRESS` | 独立构建、认证入口和 Application/Version/Profile/Tester 只读页面已实现；UC001 后续增量及真实浏览器联合验收待完成 |
| Admin Console 功能 | `UC-CONSOLE-001`（认证入口） | `IN_PROGRESS` | 独立构建、BFF/Cookie 边界、Session 入口及设备/邮箱登录交互已实现；完整恢复和真实服务验收待完成，审核业务 UC 尚未接受 |
| Developer Application 管理概览 | `UC-CONSOLE-002`（`ACCEPTED`） | `IMPLEMENTED` | 固定 API、同源 client、列表/详情、筛选/分页、错误与 Session 失效回收均已实现；真实 Gateway/Auth/App 浏览器验收待完成 |
| Developer Application Version | `UC-CONSOLE-003`（`ACCEPTED`） | `IMPLEMENTED` | 固定 API 的 Version 查询类型/client、列表/详情、单状态筛选与当前内容/latestReview 分区均已实现；真实浏览器联合验收待完成 |
| Developer Application 资料修订 | `UC-CONSOLE-004`（`ACCEPTED`） | `IMPLEMENTED` | 固定 API 的资料查询类型/client、列表/详情、权威指针、原文与独立审核历史分页已实现；真实浏览器联合验收待完成 |
| Developer Application Tester 管理 | `UC-CONSOLE-005`（`ACCEPTED`） | `IMPLEMENTED` | 固定 API 的容量/ACTIVE Membership/JoinLink 历史三个独立只读区域、隐私边界和错误恢复已实现；真实浏览器联合验收待完成 |

## 代码位置

实现目录为独立的 `iwut-console` 仓库。UC001 接受后已初始化 pnpm workspace；本页的 `IN_PROGRESS` 不表示真实 E2E 或 UC 完成。

[真实镜像浏览器联合验收工作包](2026-10-16-real-service-browser-verification.md) 已自行接受并交付，`pnpm test:real` 的 2 项真实 Browser/BFF/Gateway/Auth/App 测试通过，覆盖双 Console 邮件/设备登录、UC002–005 成功读取及 Session 失效回收。各 UC 的完整状态/恢复/并发验收矩阵仍继续实施；测试只使用已发布 backend latest 镜像，不依赖相邻源码路径。

[UC001 邮箱重发与浏览器恢复控制增量](2026-10-16-login-recovery-controls.md) 已自行接受并交付，真实 SMTP 重发后登录验证通过。页面回调隔离与 Cookie 的跨请求顺序不是同一保证；[登录 flow fencing 缺口](../query-contracts/login-flow-fencing.md) 独立保持 OPEN，UC001 整体仍为 IN_PROGRESS。

[ADR-CONSOLE-005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) 已接受共享持久 Session 与不同代认证 carrier；[持久状态原子核心工作包](2026-10-16-durable-session-core.md) 后续扩展至24项真实 Mongo 测试，已由 Session v2 接线替换旧无状态 BFF。缺口只有在真实跨副本/浏览器故障门禁完成后才能关闭。

[Session v2 接线工作包](2026-10-16-session-v2-wiring.md) 已同步接入 Browser/BFF/Edge，通过17项真实 Mongo双连接/双Hono交错、fixture浏览器及2项真实镜像成功主链；完整浏览器/生产副本故障矩阵继续实施。精确 wire 与恢复/会话版本边界见 [接线契约](../query-contracts/console-session-v2.md)。

[真实浏览器 Session fencing 验收](2026-10-16-real-session-fencing.md) 已交付7项真实迟到响应头、双标签页、两生产副本及Auth提交点崩溃/依赖故障场景，与原2项UI成功主链联合通过；Begin未知、失败兄弟恢复、Mongo回执丢失及真实UI/cache故障矩阵仍开放。

[未知结果与真实 UI 恢复验收](2026-10-16-unknown-result-and-ui-recovery.md) 已交付实际Begin原请求恢复、两次DEVICE认证失败后原EMAIL成功，以及Mongo提交回执丢失两个分支；修复UI对Begin5xx的未知结果分类，联合真实测试13项通过。迟到Begin与真实私有DOM/cache矩阵仍待补，UC001/fencing不关闭。

[真实浏览器失败报告隐私护栏](2026-10-16-real-report-privacy.md) 已交付：合成定位器/hook/API回归保持4失败/1通过，当前标准报告无随机输入材料；共用fixture后重新拉取latest，13项真实测试再次全通过。不以隐藏诊断替代失败状态，不改变上述真实验收的完成边界。

[真实UI迟到与私有视图隔离验收](2026-10-16-real-ui-concurrency.md) 已交付：实际Begin等待取消/新意图替换及旧业务成功/SESSION_INVALID与新身份交错；完整真实套件16项通过。直接Query内存检查与真实DOM/网络证据分层记录；Complete/Recover等待取消、旧清理回执与新同页缓存交错、context上限恢复仍开放，UC001/fencing不关闭。

## UC-CONSOLE-002 首个实现工作包

状态：`IMPLEMENTED`（真实浏览器联合验收仍待完成）

接受输入与范围：

- 固定统一 API commit `a5d504c058c62cd91be451074d21608d69789918`；
- 生成 `app_center/v1/application_management` 类型并提供严格 ProtoJSON fetch client；
- Developer Console 增加 `/applications` 列表与 `/applications/{applicationId}` 只读详情；
- 列表覆盖服务端默认筛选、生命周期/平台/归档状态筛选、不透明 token 逐页加载与显式刷新；归档默认不限制且不能从管理面隐藏；
- 详情覆盖深链接、统一不可访问、刷新、返回列表和 UC003–005 的禁用/未交付导航表达；
- `SESSION_INVALID` 只清 Developer Session 并返回登录入口，网络/5xx 不清 Session；
- 所有业务响应只在内存 Query cache 中短暂存在，不启用持久化，不写入 Web Storage、IndexedDB 或日志。

非目标：

- Application 创建、编辑、转让、关闭、归档或任何其它写命令；
- UC003–005 的 Version、ProfileRevision、Tester 具体页面；
- 用 mock 或组件测试宣称真实管理授权链完成。

验证命令：

```bash
pnpm generate:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test
pnpm edge:e2e
```

2026-10-15 实现结果：

- `@iwut/api-client` 已按固定输入生成 Application Management 类型；浏览器 transport 只接受同源绝对路径并使用 `credentials: same-origin`、`cache: no-store` 和严格 ProtoJSON 解析，BFF 登录 transport 继续使用 `credentials: omit`；
- Developer Console 已交付 `/applications` 和 `/applications/{applicationId}`，筛选写入 URL search，分页 token 只留在 Query 内存状态；默认请求不施加归档过滤，因此保留 `ARCHIVED` 与 `UNARCHIVED`；
- `SESSION_INVALID` 会清除当前 surface Session 和私有 Query，BFF 清理失败也不会把旧页面继续当作已登录；网络/5xx 不主动清 Session；
- Vitest 覆盖 client、筛选、详情、不可恢复 secret 和 Session 失效；Playwright 在真实浏览器 origin 上覆盖同源请求、归档默认可见、筛选和详情导航，但业务响应仍为类型化 fixture；
- Console `edge:e2e` 拉取 Gateway `latest`（验证 digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`），确认 UC002 两条 Developer route 与失败关闭；Gateway 协议 E2E 使用 Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`、App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`、真实 Mongo/BFF/Gateway 验证身份交换和 16 条管理查询/本人退出路由。

剩余验收只限于把已实现页面连接到同一套真实服务环境，准备真实管理员与 Application 数据并由 Playwright 操作页面；完成前不得把 fixture 浏览器测试表述为完整业务 E2E。

## UC-CONSOLE-003 首个实现工作包

状态：`IMPLEMENTED`（真实浏览器联合验收仍待完成）

接受输入与范围：

- 继续使用统一 API commit `a5d504c058c62cd91be451074d21608d69789918`；
- 生成 `app_center/v1/application_version` 类型并提供严格 ProtoJSON 同源 fetch client；
- Developer Console 增加 Version 列表与详情路由，UC002 详情启用 Version 导航；
- 列表覆盖服务端默认查询、DRAFT/SUBMITTED/APPROVED/REJECTED 单状态筛选、不透明 token 加载更多和显式刷新；
- 详情把当前 Version、latestReview decision/restoration、capability/scope 与 OAuth redirect 明确分区；运行声明只显示文本；
- 复用 UC002 的身份隔离、`SESSION_INVALID`、统一404、无效 token 从头刷新和仅内存 Query cache 规则。

非目标：

- Version 创建、编辑、提交、恢复、放弃草稿或发布槽位写操作；
- Reviewer snapshot、完整审核历史、当前 policy、confirmed checks 或 Reviewer 身份；
- 把 launch URL / OAuth redirect 变成可执行导航，或用 fixture 宣称真实管理链完成。

验证命令沿用 UC002，并要求 Gateway `latest` 显式包含 `ListApplicationVersions` 与 `GetApplicationVersion` 的 DEVELOPER surface route。

2026-10-15 实现结果：

- `@iwut/api-client` 已生成 Application Version 类型；list 正文严格为直接 query ProtoJSON，detail 无正文，两个 ID 均按独立 path segment 编码，`int64` 保持 `bigint`；
- Developer Console 已交付 Version 列表/详情、单状态 URL 筛选、显式游标翻页、无效 token 从头刷新、同 token 分页重试与共享 Session 失效回收；
- 当前 Version 与 latestReview 独立展示，覆盖恢复后 DRAFT + 最近 REJECTED 摘要；launch URL、capability、scope 与 OAuth redirect 都是不可点击的惰性纯文本，不执行预取或外部探测；
- Vitest 覆盖 direct query body、strict ProtoJSON、大 int64、四状态基础表达、筛选、坏 token 与详情隐私边界；Playwright 在真实浏览器 origin 上覆盖同源 list/detail、筛选、导航与不可执行 URL，但业务响应仍为类型化 fixture；
- Console `edge:e2e` 已显式确认 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` 包含两条 Version DEVELOPER route，并验证 BFF 不可用时失败关闭；同 digest 的 Gateway 协议 E2E 已通过真实 Auth/App/Mongo 和 BFF Cookie 身份交换，Version 两条路由包含在已验收的 16 条管理查询/本人退出路由中。

剩余验收是让浏览器页面直接连接同一套真实 Gateway/Auth/App 环境，使用真实管理员及四状态 Version 数据覆盖管理权变化、生命周期组合、no-store 与迟到响应；完成前不得把 fixture 浏览器测试表述为完整业务 E2E。

## UC-CONSOLE-004 首个实现工作包

状态：`IMPLEMENTED`（真实浏览器联合验收仍待完成）

首包实现固定 API 的 ProfileRevision List/Get 同源 client、资料列表/详情路由、单状态筛选、独立修订/审核历史 token、页级指针、latestReview 与原文纯文本表达。`null`、空字符串和有值必须分开，不执行 icon/正文/reason 内容。复用 UC002 的身份、错误、Session 和仅内存缓存规则。

非目标包括所有资料写操作、Reviewer queue/snapshot/decision、Admin Console、受控 icon 资产、外链代理、跨页冻结和持久缓存。验证命令沿用 UC002，并要求 Gateway `latest` 显式包含两个 ProfileRevision DEVELOPER surface route。

2026-10-16 实现结果：

- 生成并固定 ProfileRevision ProtoJSON 类型；两个同源 GET client 只发白名单 query、无正文，拒绝未知字段、畸形必需对象与非 `null | string` Value；
- Developer Console 提供资料列表/详情、单状态筛选、显式前后页、页级指针、当前内容、latestReview 和独立审核历史页；当前 token 进入仅内存 query key，身份、Application、筛选或修订变化即重置；
- 审核翻页返回的新完整详情整体替换旧页，不拼接跨时点 snapshot；原文保留空白并区分 null/空串，所有 URL 形字符串都是不可执行文本；
- Session 失效回收覆盖新增私有 query root；404、坏 token、413、5xx/网络均有独立恢复边界；UC002 详情中的资料入口已启用，所有写操作和 Reviewer/Admin 入口仍不存在；
- `generate:check`、strict typecheck、全量 Vitest、production build、Playwright 与 `git diff --check` 通过；Playwright 共 7 项通过、3 项按 Admin surface 跳过；
- `edge:e2e` 从 CNB 拉取 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，确认两个 ProfileRevision route 存在且 BFF 不可用时 fail closed。浏览器业务响应仍是 fixture，真实后端浏览器联合验收待补。

## UC-CONSOLE-005 首个实现工作包

状态：`IMPLEMENTED`（真实浏览器联合验收仍待完成）

首包实现固定 API 的 Tester Management Get 与两类 Search 同源 client、Developer Tester 路由、容量/当前链接 overview、固定 ACTIVE Membership 列表及 ACTIVE/REVOKED/ALL JoinLink 列表。三个区域各自维护 asOf/loading/error/refresh，两类 token 仅在当前身份、Application、查询种类和 filter 的内存上下文内使用。

非目标包括 REMOVED/ALL Membership UI、创建/轮换/撤销链接、移除 Tester、任何 join URL/secret/hash 恢复或复制、Auth 用户补查、本人 Tester 客户端入口、Admin Console、跨 RPC 原子 snapshot 和持久缓存。验证命令沿用 UC002，并要求 Gateway `latest` 显式包含三个 Tester Management DEVELOPER surface route。

2026-10-16 实现结果：

- 按固定 API 输入生成 Tester Management 类型与完整 enum/error reason，并实现一个 GET 和两个直接 Query body 的 POST 同源 client；Application ID 独立编码，所有方法支持取消，成功响应在 Proto 默认值生效前验证必需 envelope；
- 真实镜像联合验收纠正了首包的内容协商判断：App 实际依赖 Kratos v2.9.2，其 `application/json` codec 对 protobuf 消息已经使用 ProtoJSON；首包误根据缓存 v3 实现改用 `application/protojson`，真实镜像返回 400。现已修回 `Accept: application/json` 与正文 `Content-Type: application/json`，继续使用生成客户端的 camelCase、完整字符串 enum 和 RFC3339 Timestamp；
- Developer Console 交付 `/applications/{applicationId}/testers`，overview、ACTIVE Membership 和 JoinLink 三块使用独立 query key、loading/error/asOf/refresh 和分页状态；JoinLink 首次与重置均显式发送 ACTIVE，切换 ACTIVE/REVOKED/ALL 时只重置该列表 token；
- 容量以 overview 为权威，不从行数计算；Tester Auth ID、Membership ID 和 JoinLink ID 仅作不可点击的不透明文本，不进行 Auth enrichment，也不展示或拼接 URL、secret、hash、actor、复制、导出或写操作；
- 任一查询返回 401/统一 404 时取消并清除三块私有缓存；`SESSION_INVALID` 继续走共享 Session 回收；网络/5xx 的刷新失败保留并明确标记带 asOf 的旧快照；坏 token 只重置对应列表；
- `generate:check`、strict typecheck、全量 Vitest、production build与 Playwright 协议测试通过；浏览器测试核对两个 POST 无 URL query、body 不包 `query`、完整 enum 和 ProtoJSON headers，但业务响应仍为 fixture；
- `edge:e2e` 拉取 Gateway `latest` digest `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`，确认三条 Tester Management DEVELOPER route 存在且 BFF 不可用时均 fail closed。真实 Browser/BFF/Gateway/Auth/App 成功数据链仍待联合验收。

## UC-CONSOLE-001 首个实现工作包

状态：`IN_PROGRESS`

代码范围：

- 根 workspace、严格 TypeScript、统一检查命令和固定 lockfile；
- `developer-console`、`admin-console` 的独立 Vite/Router/Query 应用入口；
- `developer-bff`、`admin-bff` 的独立 Hono 进程，以及共享但无产品授权逻辑的 `bff-auth` Cookie/Origin/Session 机制；两个 BFF 分别注入 Cookie 命名空间、密钥、Origin 与超时配置；
- 按 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 为两个 BFF 增加私有 Session ForwardAuth；普通 HTTP/JSON API 由共享 Traefik 经 BFF Cookie 交换后进入现有 Gateway ForwardAuth，登录、恢复与聚合仍经过 BFF；
- 初始固定统一 API `9f914c5` 的可复现 TypeScript 生成输入，以及原生 fetch/ProtoJSON runtime；当前代码输入已随 UC002 升级为 `a5d504c058c62cd91be451074d21608d69789918`；
- 共享浏览器设备密钥、签名协议、会话 DTO、错误映射和测试设施；
- UC001 的设备登录、邮箱登录、结果不确定恢复、Session 摘要与失效处理；
- Vitest/Testing Library/BFF 集成测试，并为真实 Playwright E2E 建立入口。

非目标：

- Developer/Application 管理和 Admin 审核业务页面；
- OAuth consent bridge、多账号管理、显式 Session/设备管理；
- 生产部署、生产邮件就绪声明和像素级视觉定稿；
- 用 MSW 或 fixture 代替 UC001 要求的最终真实 Auth/Gateway/邮件 E2E。

首个工作包验证命令：

```bash
pnpm install --frozen-lockfile
pnpm generate:check
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test
pnpm edge:e2e
```

真实服务 E2E 需要单独的受控环境与 Auth 邮件配置；本地浏览器测试未连接真实服务时必须明确跳过，不能报告为通过。

## 2026-10-07 首个实现增量

`worktrees/iwut-console` 已交付工程与认证安全基线：两个独立 React/Vite 应用、两个独立 Hono BFF、共享且不包含产品授权逻辑的 BFF Session 封装、浏览器 P-256 设备密钥与协议校验、固定 `9f914c5` 的 Proto TypeScript 生成物、原生 fetch transport，以及单元/BFF/壳层浏览器测试。

本增量没有宣称 UC001 完成：登录按钮尚未接入 Begin/Complete 流程，BFF 尚未消费 Gateway 登录 RPC，结果不确定恢复、邮件收取和真实 Auth/Gateway/邮件 Playwright E2E 均待后续增量。Playwright 壳层测试拦截 `/api/session`，只能证明两个前端入口可运行，不能替代真实登录验收。

2026-10-07 接受 [ADR-CONSOLE-004](../adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md)。两个 BFF 已提供同构的私有 `/internal/forward-auth`：无 Cookie 时不产生 Session，合法 Cookie 只返回一个 `x-iwut-session`，出现但无效的 Cookie 与来源不匹配均失败关闭。该 ForwardAuth 拒绝响应不直接设置或清除 Cookie；Cookie 清理由显式 BFF Session 路径拥有。Gateway route schema v3、两个 surface chain 及其真实 Traefik E2E 已通过。

## 2026-10-08 共享 Edge composition 增量

Console 侧已增加共享 Traefik 的 BFF/SPA 动态配置生成器，并以固定 Traefik 镜像验证两份动态文件可合并装载、Session 与 SPA Router 按固定优先级命中、私有 ForwardAuth 不可公开访问、Gateway 链在 BFF 基础设施失败时保持失败关闭。BFF 登录/恢复调用 Gateway 的内部入口与真实 Auth/邮件 E2E 仍待 UC001 后续增量。

同日后续增量新增两个 surface 共用的设备/邮箱登录 BFF 编排：四条固定同源 Begin/Complete 路径通过生成的 ProtoJSON 类型调用非 Console Gateway origin，完全不转发浏览器 Cookie 或 Session；BFF 用独立、加密、HttpOnly 的短期 flow Cookie 将 Complete 绑定到 Begin，校验 Auth challenge/Session 形状，并只在确定成功后写入对应 Console Session Cookie。共享 Traefik 已为四条路径生成优先级 `40000` 的精确 Router。浏览器页面状态机、签名接线、结果不确定恢复及真实 Auth/邮件 E2E 尚未完成，因此 UC001 继续保持 `IN_PROGRESS`。

本机设备登录页面随后接入两个 Console：页面只读取不含私钥的 IndexedDB 凭据摘要，完整 challenge 的 protocol/purpose/service/application/operation/locator/expiry 全部通过后才要求凭据适配器签名；React state、Query cache 和表单均不接触 `CryptoKey`。目标 `AUTH_AUTHENTICATION_SERVICE_ID` 由 `VITE_AUTH_SERVICE_ID` 预配置，缺失或非法时入口失败关闭；成功响应更新安全 Session 投影与本机 credentialId。该组件测试使用 mock BFF，只验证浏览器分支，不能替代真实设备登录 E2E。邮箱页面和结果不确定恢复仍待实现。

邮箱页面增量随后接入：BFF 以默认关闭的 `EMAIL_LOGIN_ENABLED` 发布只读 capability；浏览器严格复现平台 ASCII 邮箱规范，在 Begin 前生成并持久化 non-extractable P-256 密钥，使用 8 位字符串验证码并核对邮箱协议十字段签名上下文。Begin 网络结果不确定时页面保留原 requestId、邮箱和同一 localId 进行幂等重试；Complete 结果不确定时可先用同一公钥 fingerprint 走设备登录探测，也可保留原验证码重试。Playwright 已在两个真实浏览器 origin 上覆盖 Web Crypto/IndexedDB、签名和 Session 投影，但 BFF/Auth/SMTP 均为拦截响应，不能代替真实邮件验收。服务端 `resendAfter` 冷却后的显式重发、迟到响应竞争与完整真实链路仍待实现，因此 UC001 保持 `IN_PROGRESS`。

## 实现登记原则

- 设计状态与实现状态分开维护；
- MSW 页面演示不等于 API、Gateway 或端到端交付；
- 每个工作包登记目标 UC/ADR、代码范围、非目标、验证命令和真实外部依赖；
- 两个应用分别记录构建、组件测试、BFF 测试和 Playwright 验收；
- 涉及浏览器认证协议时必须复用平台公开测试向量，并包含真实 Auth/Gateway 验证。

## 2026-10-15 App 管理与审核页面设计草案

用户已明确授权“同时起草只读管理和审核页面设计”。以下表格保留起草时的整体分包，并按后续接受与实现结果更新状态：

| 草案 | 页面范围 | 实现前置与当前缺口 |
| --- | --- | --- |
| [UC-CONSOLE-002：查询我的 Application 管理概览](../use-cases/UC-CONSOLE-002-query-owned-applications.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-003：只读管理 Application Version](../use-cases/UC-CONSOLE-003-query-owned-application-versions.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-004：只读管理 Application 资料修订](../use-cases/UC-CONSOLE-004-query-owned-profile-revisions.md) | `ACCEPTED / IMPLEMENTED` | 页面代码与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-005：只读查询 Application Tester 管理](../use-cases/UC-CONSOLE-005-query-application-tester-management.md) | `ACCEPTED / IMPLEMENTED` | 三块独立只读区域、隐私/恢复边界与协议/边缘链验证已交付；真实浏览器联合验收待补 |
| [UC-CONSOLE-006：审核 Application Version](../use-cases/UC-CONSOLE-006-review-application-versions.md) | `PROPOSED / NOT_STARTED` | 用户接受设计、ADMIN surface、真实 Reviewer 权限链路及正式检查项定义来源；currentPolicy 版本和 ID 已有 |
| [UC-CONSOLE-007：审核 Application 公开资料](../use-cases/UC-CONSOLE-007-review-application-profiles.md) | `PROPOSED / NOT_STARTED` | 用户接受设计、ADMIN surface 与精确权限；Reviewer 当前公开指针读取缺失，APPROVE 阻塞；REJECT 不需指针 |

接入调查与分包见 [App API 接入计划](2026-10-15-app-api-integration-plan.md)。Console 页面的业务授权由相应 App/Auth UC 拥有；新提案仅规定前端编排、安全与恢复。Tester 本人 UC038/040 入口继续暂缓，未创建其 Console UC，未伪造宿主 runtime。

本次没有修改 Console 源码、App/Auth/Gateway/API 或生成 brief。正式检查定义、Reviewer 公开指针等后端缺口只记录交接方案；不得以 BFF 数据库读取、管理员查询或临时 DTO 绕过。设计接受前仅可做已授权工程核对，不将草案标记为已实现。最终页面验收仍需真实 Browser/BFF/Gateway/Auth/App，mock 不计真实 E2E。
