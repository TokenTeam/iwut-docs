# UC003–005 夹具修复与串行复验

状态：UC003–005 联合专项 `PASS`；完整跨服务验收 `BLOCKED`。日期：2026-10-20。

## 修复范围

用户接受更新 App 测试夹具，并要求遇到新的阻碍或依赖问题即停止。本次只修改 App 仓库测试与启动脚本，没有修改 UC/BR、生产实现、API、Auth、Gateway 或 Console 源码。

- 用 Auth v3 正式邮箱注册接口、受控 TLS SMTP 验证码和 P-256 持有证明建立 bootstrap 管理员；随后完成真实设备登录，并通过 `GetOwnEmails` 确认已验证的当前登录邮箱。
- 删除该管理员的旧形状 `auth_email_bindings` 直接写入；真实 bootstrap 检查 `applied/authId/eventId`，不重放结果不明的操作。Reviewer 权限仍经真实管理 API 授予、撤销和重新授予。
- 测试脚本提供临时 SMTP 证书、独立随机 HMAC key、按当前格式固定摘要的测试密码 blocklist，保留默认密码工作因子与限额。秘密只在临时目录或内存中保存，不写入仓库或日志。
- 开发过程中修正了新夹具的 blocklist 摘要格式和注册 challenge 协议版本断言；最终输入均已冻结后复验。

其他参与者仍从已有有效 Session 夹具开始；这里新增的正式注册与设备登录覆盖限于 bootstrap 管理员。受控 SMTP 不代表生产邮件投递、Console 页面或生产部署验收。

## 串行结果

| 步骤 | 结果 | 覆盖 |
| --- | --- | --- |
| UC003 编辑草稿 | PASS 阶段检查点 | 同一真实链路的 Scope 变更、三协议、no-op/OCC、OAuth 同步与事务回滚 |
| UC004 提交审核 | PASS 阶段检查点 | 编辑后提交、不可变 snapshot、目录变更/停用/故障、真实 PENDING 与回滚 |
| UC005 审核 | PASS 阶段检查点 | 正式管理员前置、真实 Reviewer grant/revoke/re-grant、权限隔离/所有者冲突、真实待审批准/拒绝、依赖门禁与 SYSTEM 自动拒绝 |

三项是同一组合 Go test 中串行执行的阶段；组合 test 最终 PASS，独立 UC002 回归也 PASS。专项成功运行两轮：开发诊断 `run-yusn2eLe`，以及完整门禁第 25 项。此前 [bootstrap 阻塞](2026-10-20-uc003-005-serial-recheck.md) 已由 App 夹具适配解除，当前没有要求修改 Auth 的证据。

## 固定输入与完整门禁

- App 修复提交：`945b625a550f7bc71479d79bf541b6c8a08266a7`；验收时基于 `52ea87a` 的未提交最终同内容，提交后未再改源码。
- App/API：`27c9743d2d7476511932a83563e103aee5b4e28e`；Gateway committed archive：`3e8a59cd8b309c8f1e096ea95cac25a624738ba4` / API 同为 `27c9743`。
- Auth 固定镜像：`docker.cnb.cool/tokenteam/iwut-auth-center@sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`。
- Go 1.25.5；Mongo 8.2.12；Traefik `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。
- 权威文档使用本地已提交的 `d8f800c41bde95ffad710fb9501440133f2ef30c`，从分支 `auth-account-checkpoint` 克隆隔离输入，不使用其他所有者的 24 项未提交 Auth/platform 修改。
- 正式执行：固定上述 Auth image、`IWUT_DOCS_GIT_URL` 为本地 docs、`IWUT_DOCS_GIT_REF=auth-account-checkpoint`，运行 `GOTOOLCHAIN=go1.25.5 make check-auth-app`。
- 报告：App ignored `.artifacts/verification/20261020T011207Z-4oaqomkw/report.json`；`status=failed`，25 项通过，第 26 项失败，第 27/28 项未运行。不能登记完整跨服务 PASS 或合并准备完成。
- 服务提交前指纹：`97dde60b505074481a5a06816a16143766c4103bf970f28cf79f9fba9bed7778`；API：`85bff81fa5209ae63459fa7b104330177ecc4eb9bc81d61a6f2490b6b29286fb`；文档：`d9cec72dcb2d6de13e3210a1836a7404c5390f812552bcf0fa4889f9972ac8a0`。`changed_sources=[]`。
- 前 25 项包含脚本、格式、构建、单元/架构/transport、vet、Wire、Proto、文档、race、完整 Mongo/HTTP/gRPC 及 UC002–005。Mongo 项 1174.586s，通过；UC002–005 项 29.172s，通过。
- 最初误用默认远端 main 文档的门禁已主动中止，不作为最终完整验收证据；本地文档轮如上。

## 新阻塞与解除方案

第 26 项 `auth-app-e2e-race` / `TestE2E_UCAPP005_026_027_RealAuthProcessServiceIdentity` 失败于 `e2e_integration_test.go:1330`：创建 Version 返回 `503 ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE`。其 Auth 诊断仅报告 `error.type=startup`，没有内部原因；该镜像在第 25 项已经正常启动并完成联合验收。

只读检查确认另一处旧夹具不满足当前契约：`scripts/test-auth-app-integration.sh` 开启 `AUTH_APPLICATION_CLOSE_REAUTH_ENABLED=true`，没有密码运行时；当前 Auth `internal/config/danger_password.go` 明确拒绝该配置。现有 `e2eIssueApplicationCloseProofFromAuth` 也只准备旧 credential/Session，并在完成请求中漏传现有 API 的必填 `current_password`。这解释了为何应继续修 App 测试准备；CLI 通用错误仍不用于宣称已获得镜像内部异常栈。

后续方案（本轮未实施）：

1. 为旧 Auth/App 专项配置当前密码/邮件运行时和受控 SMTP，通过正式注册准备关闭场景账号，保留真实权限及状态验证。
2. 设备签名加当前密码取得真实关闭证明，覆盖漏传/错误密码及密码 revision 变化等相关边界；不关闭 reauth、不伪造 proof，也不回退旧镜像。
3. 加固 readiness，检查容器仍在运行及实际 gRPC 服务可用；仅 TCP 连接成功不能代表 Auth 就绪。
4. 固定最终输入，先跑该旧专项，再重新跑要求的完整跨服务门禁，继续到 UC033/036 两个未运行项目。

按用户“遇阻即停”要求，发现后未修改该专项或 Auth 源码，没有绕过失败继续后续项目。所有本轮临时进程、容器和 network 已清理；修复仅本地提交，未 push 或部署。
