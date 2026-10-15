# UC001 持久 Session 原子核心

状态：`ACCEPTED / IMPLEMENTED`（存储第一阶段；产品协议接线未完成）。2026-10-16 按用户授权自行接受。

依据 [ADR-CONSOLE-005](../adr/ADR-CONSOLE-005-durable-session-and-login-fencing.md) 第一阶段建立 `@iwut/console-session-store`：有界且校验过的单文档 context、root flow 与 Session CAS 存储；按 namespace/context 摘要隔离，primary+linearizable 读取、majority+journal 写入、Mongo 服务端到期判断与 TTL 回收。意图命令比较 root revision，操作转换还比较 attempt/operation/claim ID；Session clear 独立比较预期 generation，不取消另一条进行中的新 flow。存储层不自动重放非幂等上游 Complete。

本阶段 API 只接受加密 envelope，不接收 Auth token、验证码、proof 或设备私钥；加密与 Cookie 签发由第二阶段的 BFF Authority 负责。启动显式初始化索引，运行时不自动补建丢失 context。没有生产内存 fallback。新 package 尚不接入现有 BFF，不能声称新协议或生产存储已启用。

验证使用独立 Docker Mongo replica set、两个独立 MongoClient 和同一临时数据库；验证并发 CAS 单胜者、旧 claim 不能提交、取消/条件 clear、当前载体摘要匹配与到期、跨 surface 隔离、客户端重建后持久恢复、数据库不可达失败关闭。测试不得读取相邻源码或宿主 Mongo，不用 sudo，结束只删除本次命名容器/网络与临时数据。轻量测试覆盖输入边界和纯命令构造；真实 Mongo 另有明确命令，不静默跳过。

本工作包不修改 Auth/App/Gateway、Cookie 路径或页面流程，也不代表 UC001 完成。后续接线必须沿用 ADR 的完整身份不变量，不以存储单测代替真实浏览器验收。

## 实现与验证结果

Console 实现 commit：`92f9e4d`。

- 新增原子 context 创建（重复创建不续期或覆盖 binding）、单 root 替换/取消、EMAIL/DEVICE 两个独立操作槽、执行 claim/结果未知/显式重试、单胜者 Session commit、精确当前载体读取和条件 clear。新 commit 不能复用当前 generation 或 carrier 摘要，最多签发 32 次。
- Mongo 内只有 context/carrier 摘要、有限元数据与版本化加密 envelope。输入拒绝直接把原始 43 字符 Auth token 当作 envelope，拒绝额外 secret 字段；AEAD 验证和 surface/context/generation AAD 的加解密仍由后续 BFF Authority 完成，格式检查不等于密码学认证。
- `pnpm test:session-store` 16 项真实 replica-set 测试通过，使用两个独立 MongoClient 验证原子竞争、旧 claim 拒绝、恢复子操作单胜者、精确代际/命名空间隔离、条件 clear 不干扰新 flow、到期/未知 schema/签发上限和客户端重建。
- 真正重启本轮 Mongo 容器后，多数+journal 确认的 Session 仍可由重建客户端读取；Docker 可能重分配随机发布端口，测试仅重新检查该 owned container 的 loopback 绑定后连接，不访问其它数据库。
- 写响应丢失测试通过临时 loopback TCP 代理丢弃真实提交回复：写调用报告依赖不可用，但第二个连接读到稳定 commit ID/current generation；重试旧 claim 不能重复签发。此证据不等于 Auth→Mongo 的完整跨系统恢复已经交付。
- 停止本轮 Mongo 后，读取抛出固定、不含连接串/材料的依赖错误，未降级成已登录或空白内存状态。完成/失败/SIGINT 的 runner 清理均经过精确 container ID/name/ownership label 校验；最终无遗留测试容器。
- 轻量单元测试 9 项、全量 workspace Vitest、strict typecheck、production build、API 生成漂移和仓库独立性检查通过；现有 fixture Playwright 8 项通过、4 项按 Admin surface 跳过。它们未用于宣称新 Cookie 协议已经启用；本轮没有重新执行 Auth/App/Gateway 镜像浏览器成功链。

真实命令监控曾发现驱动 CSOT 按总预算覆盖服务端 maxTimeMS；实现已将总操作预算和配置对齐，并对实际 find/insert 命令断言 linearizable/majority+journal 和有界预算，而不是仅检查构造器参数。

下一阶段为 BFF/Browser/Edge 同步切换：context bootstrap/确认、意图 generation、匿名登录外呼、邮箱/设备恢复组合、不同代 carrier 与 AEAD、Session query/ForwardAuth 同权威读取、按发起时 generation 的私有请求失效清理，以及资源/限流配置和真实跨副本/迟到响应门禁。旧无状态运行链路仍存在，UC001 与 fencing 缺口保持未完成。
