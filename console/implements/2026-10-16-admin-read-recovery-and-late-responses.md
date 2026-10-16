# UC006–007：Admin 读取恢复与迟到响应

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行决定、记录并接受本增量；完整UC006/007的审核决定、政策解释、冲突和结果未知恢复范围不变，不以读取加固替代完整交付。

## 输入与边界

沿用[UC006 BR-CRV-004](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-004)、[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)及[查询首阶段](2026-10-16-admin-review-queries.md)的两个独立capability、Session generation、明确拒绝退场、同上下文旧快照和不持久化规则。固定API输入不变，不改后端、路由、权限或决定规则；已知App错误响应头门禁继续失败，不补代理头。

当前队列只有“从头刷新”，它创建新attempt并回第一页，不能用其丢弃旧页行为冒充同页网络恢复。核心attempt隔离已有页面生命周期，但个别已取消请求仍须在自己的信号边界校验，不能仅依靠fetch遵守Abort。既有投影拒绝分类只覆盖400/畸形成功，需补齐未获允许保留旧快照的错误分支。

## 功能决定

1. 两类队列新增“刷新当前页”：保留当前applicationId、token及前页栈，明确重读同一Query；与已有“从头刷新”的新attempt/首token语义分开。正在读取时禁止重复刷新。详情继续使用“刷新详情”。不借同页刷新自动恢复已明确权限/目标拒绝的attempt。
2. 仅已知网络TypeError、AbortError、HTTP500–599允许在同上下文保留已核验快照，明确显示原asOf与旧数据警告；成功后替换为本次事实和时间。数据时间使用语义time元素，其dateTime由正式protobuf Timestamp转换为RFC3339并保留精度，可见本地化文案仍按分钟显示；不能据同分钟的相同文案推断asOf未变或已变。没有旧数据不得伪造空页，换filter/目标/Session/attempt不得借用旧投影。
3. Session类错误继续走按代恢复；非Session401/403按capability退场、404按目标退场。400、其它明确4xx、完整畸形成功及未分类异常没有旧投影保留许可：先遮蔽当前Query，再只清捕获实例的data，后续5xx不能复活它；不扩大成另一个capability失效或清有效Session。明确失败不由focus/reconnect自动循环恢复，用户仍可明确刷新。
4. 每个实际查询把自己的AbortSignal传入attempt。开始前、成功后和处理错误前检查该请求仍未取消，以及原attempt/Session仍有效。被取消操作即使忽略Abort并迟到成功或拒绝，也不能广播权限撤销、清除新页Query或交付旧数据；取消本身不是权限撤销、Cookie安全或全局fencing完成证明。
5. 键盘可触发刷新，读取中有状态，失败有明确警告。内容仍为惰性文本，无决定请求、外部探测、Auth补查、持久化或生产治理写入口。

## 验收层次

- 先以核心/React测试证明取消后迟到403/404/成功不伤新读取、未分类拒绝精确退场、400/协议后503不复活、网络/5xx旧时间保留与成功替换、队列同页token/前页栈保持；Query对象内存证据不扩大为浏览器全heap。
- 实际浏览器复用已建立R的正式双权限Session及既有读取fixture，在最终撤重授矩阵前补两能力队列/详情恢复。单次透明TLS TRUNCATE只在真实上游成功200后发送原status/headers/正文首字节并断流，独立原生fetch先验证200正文TypeError，再验证生产React旧投影/原时间和显式成功恢复。不伪造JSON、错误码、响应头或App5xx，不把gate状态当浏览器失败。
- 真实Session跨账号交错仍需独立增量；本次组件迟到响应不替代该证据。服务5xx分类为组件证据，不将断流声称App依赖500。保留首阶段全部真实权限/错误头/最终Session断言。
- 完成后运行普通测试、strict、同pin生成漂移、生产build、fixture浏览器、Edge、focused及无参数真实门禁。每轮重新pull后端latest，轮内记录image ID，终态检查清理；不能因既有错误头失败跳过新增功能或放宽门禁。

## 实施与证据

已实现请求自己的signal透传与三个检查点、同页刷新、未许可错误精确退场和语义数据时间。核心新增测试先38项22红/16绿，再最小修复转38绿，补Session原因对照后40绿；页面同页入口2红、语义时间2红后修复，新增取消旧请求/新页的6项真实wrapper组件对照（这些补测时实现已绿，不伪称全部先红）。Admin初轮106项全绿（页面62、核心40、原Session4），strict通过。

普通统一682项Vitest＋89项Node、strict、固定生成漂移、production build、Edge及报告隐私前置回归通过。构建仍保留大chunk警告，不放宽阈值。此时首次完整fixture浏览器为8通过/2失败/6跨surface非目标skip（9.4秒）：两个Admin在同URL重新进入终态详情后找不到region，原断言保留，未获得错误类型/DOM证据，原因未定。不是已确认的StrictMode或HMR问题，也未以推测改产品。

冻结生产源后，原Admin专项2通过/2skip、Admin repeat8共16通过，完整fixture10通过/6skip、完整repeat3共30通过/18skip；临时仅失败synthetic诊断未触发且已移除，fixture源diff为零。未mock client的createRoot＋StrictMode＋异步Session/DTO初始8项对照亦通过。这些只说明目前未复现，不宣称已修复首轮异常；该间歇性验证问题保留OPEN并继续监测。生产dist真实恢复专项将独立验证，不替代开发模式定因，不关闭完整门禁、本包或上层UC。
