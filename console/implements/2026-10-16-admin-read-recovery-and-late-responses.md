# UC006–007：Admin 读取恢复与迟到响应

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16。按用户持续授权自行决定、记录并接受本增量；完整UC006/007的审核决定、政策解释、冲突和结果未知恢复范围不变，不以读取加固替代完整交付。

## 输入与边界

沿用[UC006 BR-CRV-004](../use-cases/UC-CONSOLE-006-review-application-versions.md#br-crv-004)、[UC007](../use-cases/UC-CONSOLE-007-review-application-profiles.md)及[查询首阶段](2026-10-16-admin-review-queries.md)的两个独立capability、Session generation、明确拒绝退场、同上下文旧快照和不持久化规则。固定API输入不变，不改后端、路由、权限或决定规则；已知App错误响应头门禁继续失败，不补代理头。

当前队列只有“从头刷新”，它创建新attempt并回第一页，不能用其丢弃旧页行为冒充同页网络恢复。核心attempt隔离已有页面生命周期，但个别已取消请求仍须在自己的信号边界校验，不能仅依靠fetch遵守Abort。既有投影拒绝分类只覆盖400/畸形成功，需补齐未获允许保留旧快照的错误分支。

## 功能决定

1. 两类队列新增“刷新当前页”：保留当前applicationId、token及前页栈，明确重读同一Query；与已有“从头刷新”的新attempt/首token语义分开。正在读取时禁止重复刷新。详情继续使用“刷新详情”。不借同页刷新自动恢复已明确权限/目标拒绝的attempt。
2. 仅已知网络TypeError、AbortError、HTTP500–599允许在同上下文保留已核验快照，明确显示原asOf与旧数据警告；成功后替换为本次事实和时间。没有旧数据不得伪造空页，换filter/目标/Session/attempt不得借用旧投影。
3. Session类错误继续走按代恢复；非Session401/403按capability退场、404按目标退场。400、其它明确4xx、完整畸形成功及未分类异常没有旧投影保留许可：先遮蔽当前Query，再只清捕获实例的data，后续5xx不能复活它；不扩大成另一个capability失效或清有效Session。明确失败不由focus/reconnect自动循环恢复，用户仍可明确刷新。
4. 每个实际查询把自己的AbortSignal传入attempt。开始前、成功后和处理错误前检查该请求仍未取消，以及原attempt/Session仍有效。被取消操作即使忽略Abort并迟到成功或拒绝，也不能广播权限撤销、清除新页Query或交付旧数据；取消本身不是权限撤销、Cookie安全或全局fencing完成证明。
5. 键盘可触发刷新，读取中有状态，失败有明确警告。内容仍为惰性文本，无决定请求、外部探测、Auth补查、持久化或生产治理写入口。

## 验收层次

- 先以核心/React测试证明取消后迟到403/404/成功不伤新读取、未分类拒绝精确退场、400/协议后503不复活、网络/5xx旧时间保留与成功替换、队列同页token/前页栈保持；Query对象内存证据不扩大为浏览器全heap。
- 实际浏览器复用已建立R的正式双权限Session及既有读取fixture，在最终撤重授矩阵前补两能力队列/详情恢复。单次透明TLS TRUNCATE只在真实上游成功200后发送原status/headers/正文首字节并断流，独立原生fetch先验证200正文TypeError，再验证生产React旧投影/原时间和显式成功恢复。不伪造JSON、错误码、响应头或App5xx，不把gate状态当浏览器失败。
- 真实Session跨账号交错仍需独立增量；本次组件迟到响应不替代该证据。服务5xx分类为组件证据，不将断流声称App依赖500。保留首阶段全部真实权限/错误头/最终Session断言。
- 完成后运行普通测试、strict、同pin生成漂移、生产build、fixture浏览器、Edge、focused及无参数真实门禁。每轮重新pull后端latest，轮内记录image ID，终态检查清理；不能因既有错误头失败跳过新增功能或放宽门禁。

## 实施与证据

本次只完成设计接受；实现、红绿过程、实际命令与结果待追加。当前不登记本包或上层UC完成。
