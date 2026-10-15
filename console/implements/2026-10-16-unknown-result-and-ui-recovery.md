# UC001 未知结果与真实 UI 恢复验收

状态：`ACCEPTED / IN_PROGRESS`，按用户持续授权自行接受。承接[真实 Session fencing 验收](2026-10-16-real-session-fencing.md)的未完成项，不放宽 ADR005/UC001 完成条件。

## 范围与决定

1. 使用真实 React 邮箱入口和键盘恢复按钮，验证真实 SMTP 已投递但 Begin 响应丢失时，显式重试保留原 requestId/邮箱/公钥、仅一把设备钥匙且不重复投递；另验证旧 Begin 迟到不能推进已取消的页面。
2. 真实 EMAIL Complete 未到 Auth 而结果未知，随后 DEVICE 探测确实失败，再以原 EMAIL operation/code/密钥成功完成；不把“Auth其实已经提交，DEVICE成功”代替该分支。
3. 为两个 production BFF 的 Mongo 连接增加仅本轮测试拥有的透明 TCP 代理。在 BSON OP_MSG 中只识别本 surface context collection 的 Session 提交命令，原样转发真实写入，按真实 responseTo 丢掉其执行后的回执；不得伪造数据库成功或修改数据。分别验证读回可用和读回也不可达两个分支。代理只记录阶段/计数，不输出 BSON 文档、context hash、密文或 token。
4. Mongo 故障控制仅 loopback、随机 bearer，参数不能选择任意目标、命令或数据库；只控制本轮固定目的地址和库的代理。丢回执后可按显式模式继续放行读回，或在有界窗口拒绝两副本的 Console Mongo 通信，之后由测试显式恢复。依赖未知时无成功Cookie、不擅自撤销Auth token，恢复必须重新证明设备并签发新代。

测试不得更改 Auth/App 业务库安全状态、导入私钥、注入 Session Cookie、修改时钟/lease、自动重试 Complete 或将 fixture 响应冒充真实协议。必要的 Console 修复须按现有权威契约解释原因、补回归并记录；需要新语义时先记录修订。

本包不宣称全部私有 DOM/cache 迟到矩阵、context 32次上限恢复入口或其它 UC 已完成。所有外部服务继续从 published latest 拉取，不读取相邻源码。
