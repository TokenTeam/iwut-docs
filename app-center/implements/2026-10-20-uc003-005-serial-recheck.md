# UC003 → UC004 → UC005 串行联合复验

状态：历史 `BLOCKED` 记录（本轮当时已按用户要求在 UC005 前置失败时中止）。日期：2026-10-20。

后续用户接受 App 夹具适配，原 bootstrap 阻塞已解除，UC003–005 联合专项通过；完整跨服务验收遇到另一处旧夹具阻塞。当前状态与证据见[修复与复验记录](2026-10-20-uc003-005-fixture-repair.md)。

## 本次结果

用户要求三项串行进行，遇到阻碍或依赖问题则中止并说明方案。本次运行既有 `make test-version-review-gateway-auth`，没有修改实现、UC/BR、API 或测试源码，没有切换旧 Auth 镜像重试。

| 步骤 | 结果 | 本次实际覆盖 |
| --- | --- | --- |
| UC003 编辑草稿 | 阶段断言通过 | 同一真实 Session→Auth USER→Gateway→App/Mongo 链路下的 Scope 变更、HTTP/native gRPC/gRPC-Web、no-op/OCC、OAuth 同步及事务回滚 |
| UC004 提交审核 | 阶段断言通过 | 消费 UC003 OCC 胜出后的真实 Version；Scope 停用、目录故障、Review 插入失败回滚；编辑后不可变 snapshot、重复提交/提交后编辑拒绝、三协议真实 PENDING |
| UC005 审核 | 前置准备失败，中止 | `bootstrap-platform-admin` 返回 exit1；尚未执行本阶段 Reviewer grant/revoke/re-grant、批准、拒绝或权限隔离，不登记通过 |

UC003/004 是组合 Go 专项内已完成的阶段检查点，并非两个独立 PASS 的 Go test。组合专项因 UC005 失败，整个 make 入口未通过（exit2）。另行执行的 UC002 前置回归通过。本轮只是上述联合专项复验，不替代完整 `check-auth-app` 验收。

## 固定输入与证据

- Go 1.25.5；App `52ea87aff89e66d32621d508bc2eb6cd486bd984` / API `27c9743d2d7476511932a83563e103aee5b4e28e`。
- Gateway committed archive `3e8a59cd8b309c8f1e096ea95cac25a624738ba4` / API 同为 `27c9743`，未改邻接源码。
- 本轮重新 pull Auth latest，实际 digest/ID 为 `sha256:22795e28977547d2b71179dd7478bd5f3f82c6ae22201c9d3ec40755e3e2c7a3`。
- Traefik digest `sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`，隔离 Mongo 8.2.12。
- App ignored 诊断目录 `.artifacts/integration/run-MA6ANR7b`；完整执行输出 `/tmp/app-uc003-005-20261020.log`。阶段日志位于 `version_review_gateway_auth_e2e_integration_test.go:305`、`:384`，失败位于 `:451`。
- Bootstrap 只输出通用 `auth-center failed`，未给出底层业务 reason，不能据此认定 Auth 实现缺陷。临时进程、测试容器和 network 已清理；App/Gateway/Auth 源码未改。

## 阻塞判断与解决方案

已确认的夹具兼容缺口：App 专项仍只为管理员准备旧形状 `auth_email_bindings`。当前 Auth 的 bootstrap 前置读取通过 `ReadPrimaryEmailTx` 检查登录邮箱，其模型包含邮箱目录和登录 binding；当前测试准备没有建立这些事实。该缺口与 2026-10-16 记录一致；CLI 此轮只给通用错误，底层拒绝分支仍需 Auth owner 确认。

建议后续按以下顺序解除：

1. Auth owner 确认该已发布镜像的 bootstrap 前置条件，提供稳定的正式注册、邮箱验证及设备 Session 测试准备契约/入口。
2. App owner 仅适配本仓库的联合测试夹具，优先通过正式流程建立满足条件的账号，再调用真实 bootstrap；Reviewer 权限继续由真实管理 API grant/revoke，不直接写入权限。
3. 固定上述依赖版本，重新从 UC003 → UC004 → UC005 串行复验；通过后再按修改影响运行要求的完整门禁。

当前没有开始这项修复，没有修改 Auth 代码或任何 UC。若解决方案需要新增/变更业务规则，先提交设计审核；涉及非 App 源码的工作交其 owner。旧镜像的历史通过证据仍只适用于原固定输入，不用于关闭本次阻塞。
