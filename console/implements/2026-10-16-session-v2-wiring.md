# UC001 持久 Session v2 接线工作包

状态：`ACCEPTED / IN_PROGRESS`。按用户授权自行接受。

依据 ADR-CONSOLE-005 和 [Session v2 接线契约](../query-contracts/console-session-v2.md)，同步迁移 BFF Authority、登录编排、浏览器 intent 状态、按 generation 的 Session/私有数据协调、Edge exact routes 与真实镜像 runner。旧无状态 Cookie 不双读、不回退；新 Mongo 依赖未就绪时服务启动失败。测试设施不得提供生产内存 fallback。

生产接线只在这组修改整体类型/单测/build及真实 Browser/BFF/Gateway/Auth/App 主链通过后提交为可用增量；过程中不单独启用半套协议。存储扩展补齐 pending Begin/Complete 的截止与显式未知恢复、参数 hash、刚提交 Session 的条件取消及共享 bootstrap 配额。

本包不新增账号能力、Auth/App 写命令或 Admin 审核功能。也不把成功主链解释为完整并发完成；跨副本/浏览器的完整故障矩阵与 UC001 原完成定义继续有效。

## 2026-10-16 可提交增量

接线与成功主链已实现；本工作包继续 `IN_PROGRESS`，UC001 与 fencing 缺口保持开放。

- 两个 BFF 在 Mongo 连接/索引就绪后才监听，独立数据库与 key ring；所有 Session query、ForwardAuth、条件 clear、登录根意图及 EMAIL/DEVICE claim 共用持久 Authority。旧无状态 Cookie 不接受，无进程内安全状态 fallback。
- Browser 预留公共 flow ID、确认 context、保留原密钥/requestId 恢复；Complete 成功 JSON 需再次确认当前 Session 后才接管。Developer 私有响应消费前核对 generation，按原代清理、取消与隔离 query/cache。
- Edge 新增精确 context/flow 命令路由；真实镜像 runner 为两个 BFF 注入本轮 Mongo 的独立 Console 数据库，不编译后端源码。
- DELETE 要求同源 JSON 且最多16 KiB；旧 binding 或 generation 均204 no-op，不清除新 context/载体。数据库故障仍503，不能冒充安全注销。

验证结果：

| 验证 | 结果与边界 |
| --- | --- |
| 全量 Vitest、strict typecheck、API 生成漂移及 diff 检查 | 通过；修正 BFF Login 测试范围，避免覆盖默认 exclude 后扫描 node_modules 的上游测试 |
| 双 BFF 配置、启动及 handler 单测 | 各18项通过，含依赖故障、旧 Cookie 拒绝、JSON 限制及迟到 binding clear |
| `pnpm test:session-store` | 24项真实 Mongo 测试通过，隔离容器/volume 已清理 |
| `pnpm test:session-v2` | 17项真实 Mongo、双连接/双 Hono 通过；仅 Auth 外呼为受控 fixture。含未知恢复、迟到提交/取消、旧 carrier/clear、新代隔离、AAD、配额及真实数据库中断 |
| fixture Playwright | 8通过、4按 Admin surface 跳过；不算真实认证证据 |
| `pnpm edge:e2e` | Gateway latest 路由生成、Traefik 合并与依赖故障关闭通过 |
| `pnpm test:real` | 生产 build + 双 Console、真实 HTTPS/SMTP/Gateway/Auth/App 的2项主链通过。Developer 显式重发、UC002–005读取、失效回收及 Admin 邮件/设备登录通过 |

本轮实际镜像（每轮仍先拉 latest，随后固定该轮 image ID）：Auth `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`；App `sha256:6f20c469a0e9566e045a5966fd51d81ce0b1293c650e2b277fa62bc3b5a3579b`；Gateway `sha256:a048de73b03ca6eaefb3b9897d64c73b2956a80738aea4eea343730c8bab48e9`；Mongo `sha256:e0ce8c35124d4a9f9785532d1f268f39e9728ffa1cb38f46fa482436424c4bd3`。

首轮真实测试在 Profile 列表 HTTP200 后出现页面通用读取错误；与误扫依赖测试的高负载并行，但不能据此断定根因。补充真实 Profile HTTP/JSON 必需字段断言后重跑全链通过，未修改 Profile 解析规则，不将此描述成已定位修复；保留后续稳定性观察项。

剩余验证/可用性项：真实浏览器延迟响应头与双标签页身份交错、两生产 BFF 副本/提交点重启完整矩阵；context 32次签发硬上限目前失败关闭，尚无显式 context 重建交互。不得自动换密钥/绕过配额，后续需独立设计用户恢复入口。
