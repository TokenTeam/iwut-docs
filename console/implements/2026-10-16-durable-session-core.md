# UC001 持久 Session 原子核心

状态：`ACCEPTED / IN_PROGRESS`。2026-10-16 按用户授权自行接受。

依据 [ADR-CONSOLE-005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) 第一阶段建立 `@iwut/console-session-store`：有界且校验过的单文档 context、root flow 与 Session CAS 存储；按 namespace/context 摘要隔离，primary+linearizable 读取、majority+journal 写入、Mongo 服务端到期判断与 TTL 回收。所有命令比较预期 revision 和稳定命令/claim ID，不会盲目重试非幂等上游 Complete。

本阶段 API 只接受加密 envelope，不接收 Auth token、验证码、proof 或设备私钥；加密与 Cookie 签发由第二阶段的 BFF Authority 负责。启动显式初始化索引，运行时不自动补建丢失 context。没有生产内存 fallback。新 package 尚不接入现有 BFF，不能声称新协议或生产存储已启用。

验证使用独立 Docker Mongo replica set、两个独立 MongoClient 和同一临时数据库；验证并发 CAS 单胜者、旧 claim 不能提交、取消/条件 clear、当前载体摘要匹配与到期、跨 surface 隔离、客户端重建后持久恢复、数据库不可达失败关闭。测试不得读取相邻源码或宿主 Mongo，不用 sudo，结束只删除本次命名容器/网络与临时数据。轻量测试覆盖输入边界和纯命令构造；真实 Mongo 另有明确命令，不静默跳过。

本工作包不修改 Auth/App/Gateway、Cookie 路径或页面流程，也不代表 UC001 完成。后续接线必须沿用 ADR 的完整身份不变量，不以存储单测代替真实浏览器验收。
