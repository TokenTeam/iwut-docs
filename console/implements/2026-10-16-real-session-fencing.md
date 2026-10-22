# UC001 真实浏览器 Session fencing 验收

状态：`ACCEPTED / IN_PROGRESS`。按用户持续授权自行接受；不接受新业务 UC，不改变 ADR005 的不变量。

上一轮 Session v2 接线已通过真实成功主链。本轮落实 [ADR-CONSOLE-005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) 第三阶段，检验同 Cookie 双标签页、真实浏览器应用迟到响应头、两生产 BFF 进程共享持久状态，以及重启/数据库故障。UC001 与 fencing 缺口在完整证据齐备前仍保持开放。

## 测试架构与决定

- 继续 `pnpm test:real` 的 latest Auth/App/Gateway 镜像、隔离 Mongo、真实 TLS SMTP/HTTPS Traefik、production Browser/BFF 构建；不读取或编译后端源码。
- 每 surface 启动两个生产 BFF 子进程，共享该 surface 的独立数据库与 key ring。测试专用 HTTP 转发器按请求轮转副本，不要求 sticky session；其故障门只可延迟真实请求发送或真实响应头交付、或在真实上游完成后断连接，不生成成功响应、不修改 Cookie/身份/业务正文。
- 故障控制仅监听 loopback，以本轮随机 bearer 保护。只允许操作本轮创建的转发器 gate、生产 BFF 子进程和经完整 ID/ownership label 核验的 Mongo；不得提供任意命令、地址或容器控制。
- 仅本轮静态测试服务器额外提供一个临时 browser driver 模块，复用产品 `browser-auth` 与 IndexedDB 设备适配器。私钥仍由真实浏览器生成、non-extractable、结构化存储并在浏览器签名；不导入私钥，不注入 Session Cookie，不用 page.route/MSW。该模块不得进入两个 Web 的产品 dist 或部署路径。
- driver 验证协议与 Cookie 不变量，不自动等同于 React 页面所有回调/恢复按钮已经验收；既有 UI 成功主链继续同时执行。故障状态与报告只输出 gate状态、HTTP状态与副本序号，不输出 Cookie、Session token、验证码、proof 或私钥。

## 目标矩阵

1. Auth/Mongo 已提交的 Complete 响应头暂不交付；另一标签页取消或提交不同身份的新 Session；迟到旧 carrier 可物理落盘，但不覆盖/恢复当前身份。检查实际 Cookie、权威 Session 与 Gateway/App 私有读取，而非只检查 JSON 回调。
2. 旧代条件 clear 已在服务端执行但删除响应迟到，新代登录后再交付；新 carrier 和权威身份不得被清除。
3. Complete 发送前被延迟，其间另一标签页确认新 flow/Session；释放后旧 Complete 应被拒绝，不能签发有效载体。
4. 无 Cookie 的 bootstrap 交错：迟到匿名 Cookie 不得提升为其它身份；原 binding 后续失败关闭。此可用性边界不冒充无感恢复。
5. 两生产副本交错与重启后从 Mongo 恢复；依赖暂停时 Session/ForwardAuth/业务失败关闭、不发送清 Cookie，恢复后原有效代可继续读取。
6. 真实 Auth Complete 已提交但返回丢失时，以原本机密钥显式设备恢复，不重放旧 token、不自动创建新密钥。仍需分别登记 UI 与协议层证据。

本轮若发现实现不符合既有契约，可以修复 Console 并记录原因；不得通过缩小断言、伪造 Auth 成功、修改上游业务库的安全状态或把 handler fixture 说成真实浏览器验收来关闭缺口。独立的资源上限恢复交互继续另包设计。

## 2026-10-16 验收增量

本轮无需修改产品实现；新增有界测试转发器、双生产副本 runner、临时 browser driver 与七个真实故障场景。第一轮原主链2项+故障6项全通过；第二轮补强旧载体单独拒绝/真实业务故障断言，并新增 Auth 成功后 BFF 未提交即崩溃的场景，最终 `pnpm test:real` **9项全通过**（约3.5分钟，不跳过、不自动重试）。

| 真实场景 | 证据 |
| --- | --- |
| Complete A 已提交但响应头被扣留，另一tab取消并登录B，再释放A | 浏览器实际保留不同名A/B载体；A的成功JSON被产品客户端拒绝接管，权威Session/真实App读取保持B。fixture仅删除B精确Cookie后，旧A载体单独存在不能认证，业务HTTP401 |
| 旧条件DELETE已执行但删除头迟到，B已登录后释放 | 只删除旧名；B载体、当前generation及真实B业务结果保留 |
| 旧Complete在到BFF前被扣留，另一tab已建立新flow/Session | 释放后409，无额外载体，权威身份与业务结果不变 |
| 两生产副本逐个重启及Mongo暂停/恢复 | 重启后持久身份/业务读取保留；暂停时Session503、真实业务HTTP5xx、无Set-Cookie、客户端拒绝消费；恢复后原代可用 |
| 真实Auth邮箱Complete成功，BFF未得到响应 | 不复发邮箱Complete或换密钥；显式同公钥DEVICE恢复成功，credentialId写回原non-extractable密钥记录，真实A业务读取正确 |
| 真实Auth设备Complete成功，BFF收到响应前两个进程被终止 | 上游扣留头随断连丢弃，旧浏览器结果不确定；重启后原Mongo claim仍阻止立即恢复，返回合法等待秒数；到期后第二次显式恢复得到新operationId并成功 |
| 无Cookie的双tab bootstrap交错，旧匿名头最后到达 | 迟到context不能承载已建立身份；Session SIGNED_OUT、原binding确认409、私有transport拒绝旧身份消费，符合已接受的失败关闭边界 |

其中 A 有独立的真实 Application fixture，B 列表为空；断言同时先验证 A 可读、再验证 B 不会读到 A 数据。每个 surface 的两进程共用其独立库与 key ring，转发轮转由13项真实Node HTTP测试验证；该测试已纳入 `pnpm test`。

其它门禁：全量Vitest、包含新增driver/spec的strict typecheck、固定API生成漂移、production build及diff检查通过。新driver仅存在于本轮临时目录，两个生产Web dist均未包含测试入口。所有临时容器、网络、进程、转发器和Mongo volume均已清理。此次每轮仍先拉backend latest，解析出的Auth/App/Gateway/Mongo image ID与[Session v2接线记录](2026-10-16-session-v2-wiring.md)一致。先前Profile读取瞬时失败未在本轮两次主链中复现；仍不据此声称已定位其根因。

## 保留的联合验收项

本包与UC001/fencing继续 `IN_PROGRESS/OPEN`，不能用以上成功重定义整个完成条件。后续优先补：

1. EMAIL Complete未到真实Auth而结果未知，DEVICE探测失败后，仍可显式完成原EMAIL操作。现有两次DEVICE失败后EMAIL成功证据在真实Mongo+fixture Auth的handler层，尚非真实Auth浏览器组合。
2. Begin真实SMTP投递后的响应丢失，按原requestId/邮箱/公钥恢复且不重复投递，以及取消/替换后的迟到Begin。已有handler/浏览器mock覆盖；显式重发成功不等于Begin未知恢复。
3. Mongo已持久提交而回执丢失的两个分支：读回确认签发，以及读回仍不可达无Cookie、后续重新证明设备。真实Mongo wire丢ACK已有存储层证据，尚未与真实Auth/production BFF/browser联合。
4. 实际React UI恢复按钮、卸载/onEstablished、旧业务数据与Query cache回收的迟到响应矩阵。当前driver复用产品browser协议和私有transport，但不操作这些UI路径；现有UI/私有cache证据主要是mock/单测。

context 32次签发上限的显式重建交互仍需独立设计，不随故障测试自动解决。
