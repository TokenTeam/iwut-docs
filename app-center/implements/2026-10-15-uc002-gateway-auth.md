# UC002 Gateway / Auth 联合验收

状态：`COMPLETE`（当前 App Center 创建版本后端与接入边界）

用户于 2026-10-15 授权推进 UC002 接入。App Center 本地提交 `15250b9` 增加可重复运行的真实 Gateway/Auth 验收；没有修改 UC/BR、API、Auth、Gateway 或 Console 代码。

## 接入结果

Gateway 的 `app.create-application-version` exact route 已支持 HTTP JSON、原生 gRPC 与 gRPC-Web，目标为现有 `ApplicationVersion/CreateApplicationVersion`。真实 Traefik 使用 Gateway 当前生成配置，HTTP 公网路径为 `POST /app-center/v1/applications/{application_id}/versions`；原生 gRPC 与 gRPC-Web 使用完整 RPC method。三种协议均成功创建真实 Mongo Version 与依附 OAuth 配置。

身份链路为有效设备 Session → Gateway 的 caller-signed service identity → Auth `IssueUserIdentityFromSession` → 面向 `iwut-app-center` 的真实 USER JWS → App 当前管理员/Developer 权限检查。测试没有自行签署 USER JWS。伪造终端 identity 被清理；Session 缺失、非管理员、Developer 暂停及禁止的 Authorization carrier 均被拒绝。内部 Scope 与身份签发 RPC 不可从 edge 调用。

App 使用独立 caller-signed service identity 读取真实 Auth 的 Mongo 持久化 Scope Catalog。验证了 unknown/disabled scope、目录 revision 与持久记录一致、TTL 内复用、准确到期刷新、停用生效、目录不可用时拒绝使用过期数据、revision 回退拒绝及新 revision 恢复。目录故障时真实 Auth USER 签发仍工作，失败明确发生在 App Scope 检查。

所有拒绝请求前后比较 Application、Version、OAuth 配置、Review、Publication 与 History。无部分写入、无序号消耗；目录恢复后 sequence 连续为 4。创建结果为 UUIDv7、DRAFT、revision 1、真实管理员审计；创建不进行 DNS/launch/callback 探测。

## BR 与测试证据

| 范围 | 证据 |
| --- | --- |
| BR-VER-001/002/008/009 | 新增 `TestE2E_UCAPP002GatewayAuthIntegration` 的三协议创建、真实身份、UUIDv7/sequence/DRAFT/revision/audit、拒绝后事实一致与恢复序号；既有事务/并发测试 |
| BR-VER-003–006 | 既有 Domain/UseCase 的 label、URL、RPC range、capability 边界与失败前置检查，纳入本次完整 backend/race 门禁 |
| BR-VER-007、ADR-001 | 真实 Auth Mongo Catalog 的 revision/TTL/停用/故障/回退/恢复；既有 cache singleflight、同 revision 内容变化与配置非法测试 |
| BR-VER-018 | 新链路成功创建与持久依附 OAuth 配置、失败无残留；既有双数组规范化/校验、migration 与同事务测试 |

专项入口为 App 仓库 `make test-uc002-gateway-auth`；最终入口 `make check-auth-app` 已包含该 gate，以及未过滤的 backend/race/Mongo/HTTP/gRPC 与已有 Auth/UC033/UC036 联合验收。

## 固定输入与最终门禁

- Go `1.25.5`；`make check-auth-app` / cross-service **28/28 passed**，`changed_sources=[]`。
- 报告为 App 工作树 `.artifacts/verification/20261015T130002Z-6btcdwdm/report.json`；Mongo/HTTP/gRPC gate 956.230s，UC002 专项 gate 18.614s（Go race 测试 4.628s）。
- 被测 App 为 `ffc7eeb` 加本次已暂存内容，内容指纹 `989f308da85286a2849b71589c90c85934eaf9dbf874493addac97df3058a343`；提交 `15250b9` 保存相同被测内容。
- 被测 API `a5d504c058c62cd91be451074d21608d69789918`，clean，指纹 `0601b2d99c90110bad180e4e979ed14e424e29b1f541c3ff80aba3a322e7fe6b`。这是接入前已有的 Auth API checkout 更新；本提交未暂存 App gitlink 更新。
- 验证克隆的 committed docs main 为 `aff7b10ec6416468bceaa53af13c6cc7b0e6af52`，指纹 `501827b3c055fa76b208d36caa54160c312f88c557e973c9a970521d2ee5c195`。本记录在门禁通过后补记；不把 Auth 文档工作树的其他修改当成本次验收输入。
- Gateway `894221f882254cba2e292e26606469d48b9e6b24` / API `9f914c56a276155ac3b34a980e77ca158e099867`；脚本在临时目录构建两个 committed archive，记录 `gateway-inputs.txt`，不修改相邻 checkout。
- Auth 镜像固定为 `docker.cnb.cool/tokenteam/iwut-auth-center@sha256:902dbad234b21951be12c01719bf06f2f5223c7445c6bb8832231405bd821c04`；所有四项跨服务 gate 使用相同 digest。
- Traefik 使用 Gateway image.lock 的 `v3.7.13@sha256:24841fe2de7304c149343d877d2923b4c8800a38ba015dea9174c23b20e344a0`。隔离 Mongo、进程、网络及临时密钥在测试后移除；诊断文件保留于 ignored artifacts。

## 环境接入与后续分工

| 所属 | 已验证配置与后续边界 |
| --- | --- |
| Auth | 启用现有 Session 身份签发与持久 Catalog 配置；Gateway caller 具备 `auth.identity.issue` 且允许 `iwut-app-center` audience，App caller 具备 `auth.scope-catalog.read`；分别注册对应服务公钥。UC002 暂无提供方代码阻塞。 |
| Gateway | 配置 Auth HTTP/gRPC、App HTTP/gRPC 地址与 Gateway 独立服务签名私钥，生成当前 exact routes；对外接收 Session、清理终端 identity/Authorization。UC002 暂无 route 代码阻塞。 |
| App | 配置 Auth Scope gRPC target、App 独立服务签名私钥和 Auth USER issuer/audience/public keys；生产缓存 TTL 保持既有默认 `5m` 或显式正 duration。测试 API 使用 `1ns` 触发实时刷新，另一个真实 Auth consumer 用注入 Clock 验证 `1m` TTL，不改变生产默认。 |
| 用户分派的相邻 agent | 新密码/邮箱登录与 Console 页面继续按各自工作包验收；若发布新 Auth/Gateway 基线，重新执行此门禁并记录新输入。实际部署与生产启用另行安排。 |

Session fixture 只表示已经完成设备认证的有效会话；用户、credential 和 Session 在隔离 Auth Mongo 中建立。Scope 停用、目录删除及回退同样只在隔离 Mongo fixture 中制造。这证明真实服务的读取/签发/消费行为，不代表注册、邮件、密码登录、Scope 管理入口或生产环境已部署验收。

UC003 的真实草稿编辑/OCC/OAuth 同步、UC004 的提交 snapshot 与目录变化、UC005 的真实 Reviewer grant/revoke/PENDING 决定仍为 `IN_PROGRESS`。可以复用此链路作为后续串行验收基线。UC002 原文“后续接口工作”的历史描述本轮保留；修改 UC 源文件仍遵守用户审核边界。
