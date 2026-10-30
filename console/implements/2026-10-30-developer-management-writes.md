# Developer 测试、OAuth 与展示规则管理

状态：`ACCEPTED / IMPLEMENTED / REPRESENTATIVE_REAL_CHAIN_VERIFIED`，2026-10-30。依据用户持续 goal 的自主设计与实施授权；功能分别由 [UC011](../use-cases/UC-CONSOLE-011-manage-application-testers.md)、[UC012](../use-cases/UC-CONSOLE-012-manage-oauth-clients.md)、[UC013](../use-cases/UC-CONSOLE-013-compose-application-display-filter.md) 定义。本页登记实际交付与有限证据，不替代后端规则或整体完成审计。

## 产品与自主决策

- 测试配置独立于三个发布渠道卡片。邀请创建/轮换、精确撤销与移除成员均明确确认；成员操作绑定原 membership episode，不凭 Auth ID 删除后来重新加入的记录。邀请 URL 仅一次披露、显式复制/隐藏，不恢复历史 secret。
- OAuth 使用独立正式登记与凭据元数据读模型，分别保持各自前置版本。TEST/GREY/STABLE 的 Public PKCE 与 Confidential 操作共用页面组件；仅精确的登记不存在错误形成未登记空态，其它拒绝不会伪装成新建机会。Confidential secret 仅命令组件内存保存，离页、会话变化与隐藏时清除，不进入 Query/Mutation 缓存。
- Filter 使用整页嵌套树，保留 ALL/ANY/NOT 的顺序和四种标量。Auth 只提供字段目录，不请求用户资料，不预测命中人数。完整规则显式发布或清空；首次逻辑 ALLOW_ALL/revision0、no-op 与未知结果分别处理。
- 所有新命令沿用正式 surface 与后端授权。正常页面不展示 revision；客户端保留正式前置值、验证回执，成功后独立读回。未知结果只核对、不重放；同 key 新 Query 与原 Query data 变化都不能被旧 ACK/读回覆盖。

## 集中组件与客户端检查

- Tester 命令 client 22 项，命令组件与原查询 62 项通过。
- OAuth client 25 项、配置组件 10 项通过。真实联调核实频道 path 使用完整 `OAUTH_CHANNEL_*` 名称；精确未登记 404 在客户端转换后再进入私有消费守卫，避免把正常空态作为失权退场。
- Filter client 30 项、规则模型 56 项通过；首批 Filter 组件 9 项、配置集成 22 项与 OAuth 10 项集中通过。覆盖 ACK 下界单调、读回期间 Query/data 替换，以及新缓存 revision99 不被旧 ACK2 和旧 GET2 采用。
- 真实通过之后补充了 Filter 本地结构调整：保留原树包为条件组、移除单子项外层组、确认后重新编排。新增 3 项组件检查后 Filter 共 12/12；此增量尚不借之前真实成功链宣称已独立实链验证。

## 隔离真实页面验收

轮次 `100874`，同一 runner 执行 `developer-management-writes.real.spec.ts` 与 `developer-write-workspace.real.spec.ts`，终态 **2/2 通过、exit0，无 skip/retry**。浏览器阶段32.5秒：P1为22.1秒，P0为9.7秒；前置真实测试严格类型与隐私护栏通过。

实际入口为 `node scripts/test-real-services.mjs tests/real/developer-management-writes.real.spec.ts tests/real/developer-write-workspace.real.spec.ts`，显式 `VITE_VERSION_DRAFT_WRITES=true`、`E2E_GATEWAY_IMAGE=iwut-gateway:console-local-9d6a27f`、`E2E_GATEWAY_PULL=false`。runner先构建固定静态产物再建立网络；之后源码的并行变动不进入当轮，未采集当轮JS hash，不以当前dist补认历史hash。

本轮 Auth/App 实际重新拉取 published `latest`，解析为 Auth `518b0917…`、App `68ee32b1…`；Gateway 明确使用本地 `iwut-gateway:console-local-9d6a27f` / `90cf10f0…`，inspect 固定 image ID，不 pull、不从相邻源码构建。

P1由实际 production React 页面完成11次写入：

1. 测试邀请首次创建、已有邀请轮换、精确撤销与原 episode 成员移除。
2. Public 与 Confidential 登记、Confidential secret 轮换、停用及重新启用。
3. 从初始规则设置 Filter，随后清空。

专用正式账号/应用通过现有注册、设备会话、资格及 Create/Join 流程准备；准备阶段未向数据库 seed 本链业务结果。隔离新资源不改变原25成员/26链接的只读 fixture。Node 最后正式观察成员、链接历史和有效数量；HTTP201/200、随后权威 GET、完整 body/query/If-Match 和实际 Session 保持分别核对。

同轮 P0 再次完成应用创建、版本创建/保存/送审、资料创建/保存/送审共七次写入。两份 spec 从隐私包装 `./test` 导入，trace/截图/video 均关闭；不输出验证码、Session、join URL 或 OAuth secret。secret 成功响应核对正式 no-store 契约，原私有查询的 private/no-store 断言保留，不额外发明成功写响应要求。

轮次全部容器（含停止项）和 network 均为0，私有临时运行材料保存在仓库外；现有 Dev 预览、会话和回滚容器未改。上述结果不是旧128项全量重新通过，也不是所有频道、失败排列和生命周期的完整证明。

## 后续

[UC014](../use-cases/UC-CONSOLE-014-manage-application-ownership.md) 的归档与管理权交接页面已另行实现，真实链路仍需独立验收；[UC015](../use-cases/UC-CONSOLE-015-manage-platform-governance.md) Admin 治理正在实施。版本恢复/放弃、拒绝资料预填、账号安全/BFF 与正式 IP 部署各按独立范围推进。完整 goal 保持进行中。
