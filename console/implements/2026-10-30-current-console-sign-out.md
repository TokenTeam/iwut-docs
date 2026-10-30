# 当前 Console 会话的显式退出接入

状态：`IMPLEMENTED / ORDINARY_VERIFIED / REAL_REPRESENTATIVE_VERIFIED`，2026-10-30。依据持续 goal 自主设计、接受并实现 [UC017](../use-cases/UC-CONSOLE-017-sign-out-current-console.md)。共享 BFF、精确 Edge 入口、浏览器客户端和双端退出已接通；普通检查、独立真实 Mongo 交错与两端真实 Auth/Gateway 代表链通过。验收范围与失败历史分开记录，不以正常退出代表链宣称全部未知/迟到矩阵或完整goal已完成。

## 设计核对基线

- UC001 明确排除了显式退出，并要求另立用例引用 Auth UC008。设计核对时两个 Shell 没有显式退出入口；两端 `session.ts` 的 `clearSession` 仅发送带 binding/generation 的 `DELETE /api/session`。下文实现新增专用流程，原 clear 语义不变。
- `packages/bff-auth/src/authority.ts` 的 `clearResponse` 调用 `store.clearSession` 并删除该 generation 的已观察 carrier，没有向 Auth 外呼。`console-session-store` 的清理只按匹配 generation `$unset session`，刻意不清新 flow，也不修改另一代。
- 正式 `AuthenticationService.RevokeCurrentSession` 已由固定 API `6fea3db` 生成，HTTP 为 `DELETE /auth-center/v1/sessions/current`、无正文，token 只在专用 header。Gateway `9d6a27f` 的 `auth.revoke-current-session` 使用 DIRECT/preserve SESSION，不先在线验证 token 有效性，已有普通内部路径可供 BFF 精确调用。
- `RevokeOwnSessions` 是其它有效 Session 的明确集合回收，禁止包含当前 Session，不能用于实现本次退出。此前仅按名称查找而遗漏 `revoke-current-session` 的判断不作为设计依据。
- Edge 对 `/api/auth/*` 是精确 allowlist，未知 `/api` 拒绝。因此本次在共享 Edge renderer 明确增加 `POST /api/auth/logout`，不能只依赖已有前缀路由。

以上是设计时的源码与权威文档核对，不等于已验证发布镜像上的新退出流程。没有把运行中的 Session token、Cookie、钥匙或个人正文写入记录。

## 自主决定及取舍

### 默认精确撤销，同时分别陈述两个结果

选用专用 BFF `POST /api/auth/logout`：捕获当前 A token，单次调用 Auth UC008，再独立按 A generation 清理 Console Authority。相比只复用 clear，此流程真正尝试结束上游当前 token；相比清整个浏览器，它保留设备登录能力及另一端独立性。既有失效 clear 不增加 Auth 副作用，避免迟到业务拒绝升级为用户未选择的撤销。

Auth 回执确认和 Console 清理确认是两个事实。200 正文必须同时携带精确目标、`console: CLEARED` 与 `auth: REVOCATION_CONFIRMED | UNCONFIRMED`；只清理成功时使用明确部分成功文案。Auth 已撤销但本地写未知，或两者均未知，不能以成功状态结束等待，必须明确核对。

### 不额外持久化退出秘密队列

上游 token 仅在已存在的 Authority 密文和当前 handler 闭包内出现，不为退出再建可重放秘密副本。清理后若 Auth 回执未知，无法在后续请求重新取得旧 token：产品接受并明确告知“本地已退出、服务端撤销尚未确认”，不将这种有限能力包装成可无限恢复的全远端退出。

若浏览器收到未知而原 Authority 仍存在，用户可以明确重试同一目标；若已清理，只读核对即可，不重建旧代、不拿新 token 代替旧 token。响应丢失后即使状态恰为 SIGNED_OUT，也没有证据补造 Auth 成功回执。此取舍避免为了退出引入第二套 token 生命周期、后台重试和秘密清理义务。

### 精确目标优先于全局清退

命令绑定当前 surface、binding、generation，而不接受客户端指定的 Auth Session ID。BFF 捕获 token 后即使 B 登录，A 的撤销与 CAS 清理仍只针对 A；旧回执不把 B 导航回入口或清新缓存。别的明确登录 flow 不在本命令范围，不能借退出旧代取消较新的登录意图。

确认后立即卸载 A 私有子树、清对应内存和一次性秘密；服务端清理未知时仍不能宣称已退出。保留设备私钥不代表自动登录授权，退出后等待用户新的明确选择。过期/失效会话仍由原恢复机制处理，不让缺少有效本地 target 的请求随意撤销其它目标。

## 已实现范围

- `@iwut/validation` 新增严格 `consoleLogoutRequestSchema`、`consoleLogoutResponseSchema` 及推导类型。请求只有原 binding/generation；结果必须逐项区分 `CLEARED` 和 Auth 确认状态，不接受 token、目标账号、任意上游路径或额外字段。
- `@iwut/bff-auth` 导出 `createBffLogoutApi`，已在两端 BFF 安装于 login API 之前。handler 核对原 context、generation 和 carrier 才捕获原 token，固定无正文 DELETE 当前 Auth Session；只接受 HTTP 200、JSON 媒体类型和严格正式 `SessionRevoked`，成功正文限制 1 KiB。网络、非契约状态或畸形成功不确认 Auth，但仍尝试原代本地清理。原 `clearResponse` 没有增加 Auth 副作用。
- 本地 clear 只操作捕获的 selector/generation。写 ACK 丢失或 CAS no-op 后仅追加一次同一 context 读取；真实 store 的 majority 写后像或 primary/linearizable 读取证明 A 已不存在，才能返回清理确认。仍为 A 或读取失败均保持未知，不自动再次写入。B 新登录和新 flow 不被旧退出清除；只有原请求观察到的 A carrier 可被删除。
- 共享 Edge renderer 只新增精确 POST logout 路由，仍拒绝其它未知 `/api`。固定 API 和 Gateway 凭据矩阵没有扩展。新增包依赖已通过离线 install 接线，下载 0、不执行安装脚本。
- `@iwut/browser-auth` 提供严格的同源退出和当前 Session 核对客户端；回执需与原目标精确一致。`@iwut/console-auth-ui` 共用退出 runtime、短确认、结果与核对面板、菜单及宿主 hook，两端 Shell 已安装。
- 宿主 `onStart` 先捕获原代私有 Query 实例，以 `revert: false` 取消，随后 `flushSync` 卸载私有子树，再清 data/remove。这样取消不会回滚复活旧快照，组件退场也先于旧数据清理可能触发的更新；同 key 新 Query 不被旧清理误删。A 的 Session Query 保留给结果和未知核对，不能先伪造 SIGNED_OUT；真正读到 SIGNED_OUT 后退出结果面板仍保留，只有用户明确返回才进入登录入口。
- 新 B 或同 key 新 Session Query 会终止旧面板操作，不允许旧响应写入新状态或导航 B。最后一项小修订补齐 `CHANGED` 且当前缓存已为 SIGNED_OUT 的情况：可明确返回登录入口，但仍不补造 Auth 撤销回执；若已经是 B，则不提供旧退出的返回动作。退出后不自动登录、不删除设备钥匙、不调用另一工作台。

不新增 Auth/Gateway 业务接口，不要求新增 Console direct surface，也不修改 Auth UC008 的幂等规则。部署仍须具有既有内部 `auth.revoke-current-session` 路径；若目标镜像缺路由或正式 ProtoJSON/错误行为不符，则据实登记外部阻塞，不能回退为仅 clear 却报告完全退出。Cookie header 431/33+ carrier 的传输边界仍独立，不因新按钮而宣称已修复。

## 普通检查与真实 Mongo 证据

共享 BFF **47/47**、validation **37/37**及两个包 strict 通过；BFF 回归保留原 clear 与 Cookie/Origin 边界，并覆盖固定上游外呼、Auth 错误/断流/畸形成功、精确原代清理、ACK 未知、A/B 交错和原 carrier 精确删除策略。这些单测中的 Auth HTTP 与存储替身不构成实际 Auth 撤销证据。

浏览器退出客户端新增 **29项**回归通过，browser-auth 完整包 **212/212**通过。共享 runtime/Panel 初批24项与宿主8项通过；最后补齐上述 `CHANGED` 分支后，runtime/Panel **32项**与共享 strict 通过。两端共用宿主的8项证明按捕获 Query 实例退场、SIGNED_OUT 结果保留以及 B/同 key 新 Session Query 不受旧操作影响；不将此内存/组件证据扩为真实浏览器全 heap 验收。

root 完整普通 `pnpm test` **exit0：1866项 Vitest＋404项 Node**，full types 与 build 均 exit0。该完整批次在最后 `CHANGED` 小修订之前执行；修订后的验证是上述共享 strict 与32项定向回归，没有把未再次执行的完整 test/build 写成最后源码的第二轮全绿。遵循用户集中必要检查的要求，不在每个小改动后重跑整套。

新增 `test:logout` 使用独立 owned Mongo runner，两条独立连接与生产 Authority/logout handler 的 **3/3真实 Mongo 交错通过**：A 上游等待期间 B 提交；clear 实际提交但 ACK 丢失后只读确认；clear 未提交仍为 A 时503，只有用户明确重试才发生第二次外呼。独立 runner 已确认清理其 Mongo 容器和卷。这里只控制 Auth HTTP 回执，不能称为真实 Auth/Gateway 成功或双端实际退出通过。

## 真实链与当前完成边界

最新119394固定 `5a6e723` 的四文件30项专项已终态28通过/2失败，**双端本包真实退出各1.1分钟通过**，没有skip/retry。原token在线200→正式DELETE→在线401/SESSION_INVALID、Mongo同一Session撤销、peer原代和在线200、两端原钥匙不可导出且指纹保留、明确DEVICE同credential新generation均实际核对。页面没有自动登录或直接发送Auth token。完整镜像/静态hash及资源清理见[集中记录](2026-10-30-console-integration-gates.md#四文件专项119394)。两条失败在其它治理/隔离场景；不借本包通过改写整轮exit1，也不把组件/真实Mongo的故障组合冒称逐一在Auth镜像上复现。下方“待验证”保留当时接线阶段，已由本段正常链结果推进。

产品已本地提交 `8dd231e`；真实接线另提交 `5a6e723`，新增两个独立普通账号与实际页面spec。测试专用固定relay只在捕获的正式DELETE请求闭包使用token，固定GET撤销前200、原DELETE一次、固定GET撤销后401；Mongo只读锚定同一账号/公开credential对应的唯一EMAIL Session，控制端仅返回固定布尔/计数，不使用mongosh命令传秘密。目标/peer两origin邮箱各一次，含注册共三封，按真实返回的冷却等待。

新模块7项Node边界回归已纳入默认CI policy，该入口48项Node＋6项诊断Vitest通过，real types/privacy通过；没有把这些合成观察冒称实际Auth成功。下一轮选择四个完整spec，预计30项，包含退出、本人资料、Developer隔离与治理；不是无筛选完整门禁，结果另行记录。

专用 relay 与浏览器退出 spec 正在准备，用于在真实 Auth/Gateway 下核对当前 token 后续在线拒绝、另一独立 Session/另一端保持、原设备钥匙保留与用户明确设备重新登录。尚无本包真实 Auth 退出成功证据，状态保持 `REAL_AUTH_PENDING`，不以普通绿或 Mongo3项代替。

本次产品和文档等待 root 统一记录候选并提交，没有自行 push。原设计阶段仅文档、未实施的记录已由上述实际增量推进；完整 UC/goal 不因本包普通验证通过而关闭。
