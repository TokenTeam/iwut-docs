# Application 关闭认证夹具适配与完整复验

状态：关闭认证专项 `PASS`；完整跨服务门禁 `BLOCKED`。日期：2026-10-20。

## 本轮范围与交付

用户授权继续适配 App 关闭认证测试夹具、重跑完整门禁，遇新阻塞即停止。App 本地提交 `b1c85625a330381fd5ee3a7dd7331775999c47c0`，未 push 或部署。未修改生产实现、UC/BR、API、Auth、Gateway 或 Console 源码。

- 将上一轮正式注册 helper 提取为共享测试夹具，返回 Auth 实际生成的账号、密码、设备私钥和设备登录 Session；受控 TLS SMTP 在单次注册后关闭，秘密只存临时目录或内存。
- 关闭场景的源账号经正式 v3 邮箱注册、验证码、设备持有证明和设备登录创建；删除旧的 credential/Session 直接插入。既有 Developer 状态夹具保留，不扩展为 Developer 申请流程验收。
- Auth/App 脚本补齐密码运行时、SMTP 信任和固定摘要的测试密码 blocklist，保留默认密码工作因子与限额；固定镜像 ID 启动，监听限定 loopback。
- readiness 同时检查容器运行状态及真实 gRPC 校验响应；空注册请求必须返回 `InvalidArgument`，不建立注册操作，不能只凭 TCP 连接判定就绪。
- 真实关闭证明提交当前密码和该账号同一登记设备的新签名；缺密码返回 `InvalidArgument`，错误密码返回 `Unauthenticated`，两者后仍为 PENDING 且无 JTI。正确密码签发后核对 COMPLETED、应用绑定、JTI、签名摘要和捕获的 password revision。
- 保留 UC005 自动拒绝、UC026 管理员转让、UC027 CLOSING、本地关闭、真实 Auth 断连重试、永久 tombstone 与最终 CLOSED 断言，没有关掉二次认证或伪造 proof。

旧 Auth/App 专项仍使用测试签名的 App USER 和受控 Developer 状态；其覆盖不是 Console 或 Gateway 的完整登录体验。UC002–005 的真实 Gateway/Session→USER 链路另由第 25 项验证。未测试密码变更后的旧 challenge 失效，不把正常 proof 的 revision 核对描述为该边界已完成。

## 运行结果

| 检查 | 结果 |
| --- | --- |
| 注册验证码解析 race 检查、Shell 语法和 diff | PASS |
| `make test-auth-app` 固定镜像专项 | PASS，Go test 7.99s；诊断 `run-IbXLsaMB` |
| 完整门禁第 1–23 项 | PASS，含构建、单元/transport/架构、vet、Wire、Proto、文档和 race |
| 第 24 项 Mongo/HTTP/gRPC 全量 | PASS，1159.383s |
| 第 25 项 UC002–005 Gateway/Auth | PASS，29.764s；三项阶段按 UC003→UC004→UC005 串行 |
| 第 26 项 Auth/App 关闭认证等专项 | PASS，17.865s；本轮原阻塞已解除 |
| 第 27 项 UC033 Auth/OAuth | FAIL，12.591s；发现新阻塞即停 |
| 第 28 项 UC036 Auth/OAuth | 未运行，不能登记通过或失败 |

完整命令为 `GOTOOLCHAIN=go1.25.5 make check-auth-app`，显式指定固定 Auth image、本地 `IWUT_DOCS_GIT_URL` 和 `IWUT_DOCS_GIT_REF=auth-account-checkpoint`。报告 `.artifacts/verification/20261020T060938Z-df_d_p5l/report.json` 为 `status=failed`，26 项通过、27 失败、28 未运行；`changed_sources=[]`。整体不能登记完整跨服务 PASS 或以此声明合并准备完成。

## 固定输入与指纹

- 验收时 App HEAD `945b625a550f7bc71479d79bf541b6c8a08266a7` 加最终维护改动；对应提交 `b1c8562` 的内容未在验证后修改。提交前指纹 `151322c3b21cce96cfc09dbd0a343af3e3876169520c87b331ad739040b87a4f`。
- App/API `27c9743d2d7476511932a83563e103aee5b4e28e`，指纹 `85bff81fa5209ae63459fa7b104330177ecc4eb9bc81d61a6f2490b6b29286fb`。
- 权威文档从本地已提交的 `350ba9b425bcf05eaed4a848a5f67b4a9dddc401` 隔离克隆，指纹 `33fc89f28d2242b2f18159cedcb3f4c6ec67cdba9440231a2c5b3c054e7b834d`；未使用或改动其他所有者的 24 项未提交 Auth/platform 文件。
- Gateway committed archive `3e8a59cd8b309c8f1e096ea95cac25a624738ba4` / API 同为 `27c9743`。
- Auth 固定镜像 `docker.cnb.cool/tokenteam/iwut-auth-center@sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`；Go 1.25.5、Mongo 8.2.12；Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。

## 新阻塞与后续方案

失败用例：`TestE2E_UCAPP033_RealAuthOAuthArchival`，`uc033_auth_app_e2e_integration_test.go:185` 调用 `/portal/session`，返回 `503 {"error":"temporarily_unavailable"}`。Auth HTTP/gRPC 已正常启动，并成功处理 Scope Catalog 与 Developer 查询；App 资料/版本审核、OAuth client 注册和发布准备已成功。门户会话未建立，后续授权、换码和归档/恢复门禁尚未开始，不能登记 UC033 通过。

只读检查发现 `uc033SeedAuthSession` 仍直接写旧 credential/Session，缺少当前 credential revision，并为固定 principal 准备 Developer handle，但没有正式注册产生的已验证登录邮箱目录。当前 Auth Session 校验有 credential revision 门禁，OAuth 用户投影也读取当前登录邮箱。UC036 同样调用这个 helper。上述是已确认的兼容缺口；当前 503 没有披露内部 reason，尚未取得对其底层具体分支的验证，不据此认定 Auth 实现错误。

建议下一包：

1. 在 App 的 UC033/036 测试准备中复用正式邮箱注册、设备登录和当前邮箱目录验证；保留必要的现有 Developer/handle 夹具，不回填猜测的密码或凭据文档。
2. 先建立门户会话并验证授权/换码基线，再保留原 UC033 归档/恢复与 UC036 Test clear 的真实 OAuth 行为断言；UC036 仍需实际运行确认。
3. 先按顺序运行两个专项，确认依赖后再冻结最终输入重跑完整门禁。若合法账号仍出现 503，保存精确操作和必要诊断交 Auth owner 定位，不关闭校验、不换旧镜像掩盖。

遵照“遇到新的阻塞再停下来说明”，本轮未修改 UC033/036 代码或 Auth 实现。当前临时容器、进程和 network 已清理。此前 [UC003–005 夹具修复记录](2026-10-20-uc003-005-fixture-repair.md) 中的第 26 项旧阻塞已解除，本记录中的第 27 项为当前未解除阻塞。
