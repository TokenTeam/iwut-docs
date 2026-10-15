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
