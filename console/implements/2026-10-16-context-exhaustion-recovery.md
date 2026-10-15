# UC001：context 签发上限后的显式重建

状态：`ACCEPTED / IN_PROGRESS`，2026-10-16，按用户持续授权自行决定。实现ADR-CONSOLE-005的32次签发上限恢复，不扩展Auth/App/Gateway业务或显式注销能力。

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
