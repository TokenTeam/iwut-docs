# UC001：context 签发上限后的显式重建

状态：`ACCEPTED / IMPLEMENTED`，2026-10-16，按用户持续授权自行决定。实现ADR-CONSOLE-005的32次签发上限恢复，不扩展Auth/App/Gateway业务或显式注销能力。

## 决定

1. `CONSOLE_CONTEXT_EXHAUSTED`不是短暂限流，不提示等待后盲重试。共享认证入口停止旧登录/恢复，擦除一次性邮箱/验证码状态，保留设备钥匙；说明重建会让共享该旧context的本Console标签页重新登录，但不撤销Auth Session或设备。
2. 新增精确同源命令`POST /api/auth/context/reset`，body为`{contextBinding,revision,resetId}`。resetId为浏览器首次发送前生成的公共Opaque32，只存内存。仅允许仍有效、issuedSessions=32、binding/revision匹配且未reset的旧context原子终止；保持原TTL，revision+1，清flow/session，写一个有界`reset:{id,fromRevision,at}`墓碑。正常读写均排除墓碑；专用receipt读可读它，不能复活或延长期限。
3. 成功receipt为`{state:"RESET",contextBinding,revision:原revision+1,resetId}`；reset响应绝不设置或删除任何Cookie。相同旧Cookie/绑定/revision/resetId重试读回同一receipt；不同ID、陈旧revision、未用尽、跨surface或Cookie已变更均409且无Cookie副作用。写ACK未知时只读回精确墓碑；仍无法确认返回503，不能假装成功。
4. 用户明确选择重建时，先confirm同一binding取得当前revision并冻结reset plan。未知reset重试必须保留该plan和resetId，不自动换revision或重复读取来覆盖另一个命令。并发两reset只有一个胜出；失败方显式重新读取入口，不自动采纳另一标签页的操作。
5. 重建确认后**停止**，显示“返回登录入口”供用户再次明确选择。这个新动作重新载入本源入口并读取权威Session；下一次显式登录才走既有bootstrap/confirm/flow。旧reset回调不自动bootstrap、登录、重放邮箱Begin或采纳新身份；另一标签页已登录时正常读取它，而不是清它。等待可停止，本地Abort不表示服务端未终止；原plan保留以明确继续确认。
6. store startFlow原子检查issuedSessions<32；start/recover一致返回exhausted，不在第32次完成后创建第33个恢复root。有效第32代仍可正常读取，直到用户确认reset或现有Session失效。

这是既有匿名bootstrap迟到失败关闭边界上的恢复，不承诺双bootstrap无缝轮换。surface的32个carrier/8192字节Cookie头上限和单context签发次数是不同约束；本包不放宽Cookie硬上限，不提供wildcard清理，不声称能自助修复任意33+迟到carrier。超限仍431，明确提示只处理Cookie而非删除设备站点存储；更完整的可验证载体清理另行设计。

## 验证与边界

先取得新回归失败，再验证真实Mongo双连接的CAS/墓碑/原TTL/普通读写失效、两BFF handler receipt重试/未知写回执/错误边界、Browser稳定plan/严格receipt/取消与迟到回调、两个共享入口的真实键盘UI。真实镜像浏览器通过实际32次生产登录达到上限，不直接篡改次数，不编译相邻后端；遵守Auth返回的有限重试时间，不以调时或放宽配额取代证明。覆盖显式重建后同钥匙新context登录，以及旧reset回执/重试不能影响另一标签页的新Session。focused仅诊断，最终仍跑无参数全量真实套件和普通门禁。

UC001/fencing仍保持IN_PROGRESS/OPEN，全部私有页/权限变化矩阵及Cookie超限可用性不是本包已完成事项。

## 实施证据（持续更新）

新增回归先取得失败：reset路由404、store方法缺失、recover在32次后仍返回200、Edge缺精确路由；Browser新增13项因API缺失失败，普通DEVICE上限仍误报“请求过于频繁”。两个实际Session入口的431回归也分别失败（503对照均通过），证明仅在登录组件里加说明不足以覆盖初始GET Session失败。

真实Mongo核心26项、双独立连接/Hono handler20项通过；包括终止CAS、精确墓碑、原TTL、namespace、旧读写失效和新context隔离。reset写异常分支是“真实Mongo写＋受控抛错/读回失败”，验证精确确认及503，不冒充线级Mongo ACK丢失。当时真实HTTP回执丢失/在途及实际32次签发尚待独立浏览器场景验收。

普通门禁327项Vitest、28项Node、全部strict typecheck和生成漂移检查通过；fixture浏览器8通过/4项Admin范围跳过，Edge接线门禁通过。新增真实context场景focused单项通过（浏览器约1.3分钟，完整命令exit0）：真实32次提交、最后201 DROP后exhausted、reset200 DROP后的原plan重试、旧200 HOLD期间另一页同钥匙新context登录/实际App读取、旧plan新Cookie重试409无Set-Cookie，放行旧回执不自动推进，显式返回重新读取B。此为定向证据，仍需无参数全量真实套件。

范围复核发现上述定向只操作Developer origin，不能推断Admin独立Cookie/Edge接线也完成上限恢复；因此主动终止尚在准备阶段的全量20项轮次（exit1、finally清理完成，不记作产品失败或通过），先将场景参数化补Admin独立真实账号/32次签发/原plan恢复/迟到回执及surface隔离。Admin没有业务页，不构造Reviewer或App UI，使用已登记的本人profile受保护只读请求实际HTTP与Session权威确认身份链，body不进入测试日志或断言快照；Developer保留实际App UI读取。

## 最终联合验收

无参数`pnpm test:real` **21项全通过**（浏览器约7.8分钟，无重试/跳过，完整命令exit0）。既有19项全部保留；新增Developer与Admin两个origin的真实32次签发、原plan恢复、迟到reset回执与新context交错及surface隔离均通过。不是由定向或共享组件测试外推Admin结果；Admin本人Profile实际HTTP200仅证明已交付的受保护身份链，不证明Reviewer授权或审核UI。

普通327项Vitest、28项Node、strict typecheck、固定API生成漂移检查、fixture浏览器8通过/4项Admin范围跳过、Edge门禁、Mongo26+20及diff检查通过。实现分为持久reset（Console `783305b`）、共享恢复UI（`bcc1f35`）、两入口431表达（`f0a0741`）与真实场景，未修改后端/API仓库或编译其源码。

每轮重新拉取三个backend `latest`，仅在该轮固定image ID；最终轮digest：

| 镜像 | digest |
| --- | --- |
| Gateway | `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9` |
| Auth | `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3` |
| App | `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b` |
| Mongo 8.2.12 | `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3` |
| Traefik | `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0` |

runner finally完成，本轮临时容器/匿名volume、网络、BFF/测试子进程与临时文件清理；随后只读检查资源残留。UC001/fencing及本文列出的非目标继续保留，不把本包交付解释为所有Console功能已完成。
