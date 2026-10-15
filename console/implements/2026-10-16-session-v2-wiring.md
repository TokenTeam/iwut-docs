# UC001 持久 Session v2 接线工作包

状态：`ACCEPTED / IN_PROGRESS`。按用户授权自行接受。

依据 ADR-CONSOLE-005 和 [Session v2 接线契约](../query-contracts/console-session-v2.md)，同步迁移 BFF Authority、登录编排、浏览器 intent 状态、按 generation 的 Session/私有数据协调、Edge exact routes 与真实镜像 runner。旧无状态 Cookie 不双读、不回退；新 Mongo 依赖未就绪时服务启动失败。测试设施不得提供生产内存 fallback。

生产接线只在这组修改整体类型/单测/build及真实 Browser/BFF/Gateway/Auth/App 主链通过后提交为可用增量；过程中不单独启用半套协议。存储扩展补齐 pending Begin/Complete 的截止与显式未知恢复、参数 hash、刚提交 Session 的条件取消及共享 bootstrap 配额。

本包不新增账号能力、Auth/App 写命令或 Admin 审核功能。也不把成功主链解释为完整并发完成；跨副本/浏览器的完整故障矩阵与 UC001 原完成定义继续有效。
