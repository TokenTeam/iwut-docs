# Gateway 实现状态

| 用例 | 设计 | 实现 | 缺口 |
| --- | --- | --- | --- |
| [UC-GW-001](../use-cases/UC-GW-001-authenticate-and-forward.md) | `ACCEPTED` | `COMPLETE` | —（当前后端/本地部署工作包；生产公网发布仍为独立部署事项） |
| [UC-GW-003](../use-cases/UC-GW-003-attach-optional-user-identity.md) | `ACCEPTED` | `VERIFIED_LOCAL` | API 与服务提交尚未 push；CI/发布候选需先发布统一基线。 |
| [UC-GW-004](../use-cases/UC-GW-004-forward-optional-session-to-auth.md) | `ACCEPTED` | `IMPLEMENTED` | 真实邮箱注册/绑定三协议联合验收与生产开关待完成。 |
| [UC-GW-005](../use-cases/UC-GW-005-forward-account-closure-credentials.md) | `ACCEPTED` | `IMPLEMENTED` | 真实五方法三协议联合验收、Edge 脱敏与生产开关待完成。 |
| [UC-GW-006](../use-cases/UC-GW-006-forward-application-close-proof.md) | `ACCEPTED` | `IMPLEMENTED` | 真实 proof 签发/消费及三协议业务拒绝联合验收与生产开关待完成。 |
| [UC-GW-007](../use-cases/UC-GW-007-compose-console-session-forward-auth.md) | `ACCEPTED` | `IN_PROGRESS` | Gateway-owned route schema、surface/Host、Traefik chain 与真实双 surface E2E 已本地通过；等待 Console deployment-owned 完整拓扑验收。Gateway 核心不消费 Console Cookie。 |

2026-09-23：已建立 `worktrees/iwut-gateway-ddd` 的空白孤儿分支 `gateway/v1`，仅放工程设计入口。没有复制旧配置、启用公开路由或部署服务。OAuth2、Redis 和 Gateway 管理后台不属于当前首版实现。

2026-09-24：UC-GW-001 与 [ADR-GW-001](../adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md) 已接受，Auth UC010 后端为 `CORE_COMPLETE`，首个实现工作包可以启动。设计接受不等于已公开任何路由。

2026-09-24：首个实现工作包已闭合。Gateway 提交 `af82578` 交付固定 API module、严格路由目录/descriptor 校验、确定性 Traefik 生成器、HTTP ForwardAuth、caller-signed Auth client 与 exact unary gRPC proxy；`ca0606b` 使用固定 digest Traefik、真实 Auth production composition/Mongo 和实际验签 backend 验证 HTTP/JSON、原生 gRPC、gRPC-Web 的成功与失败不抵达 upstream；运行说明为 `31816ad`。固定 API revision 为 `ef8957505d9870f9ec51c659a9d62808565aefef`。

## 首个实现工作包：UC-GW-001 v1

### 必读输入

1. [UC-GW-001](../use-cases/UC-GW-001-authenticate-and-forward.md) 全文及 BR-GWR-001–005。
2. [ADR-GW-001](../adr/ADR-GW-001-runtime-routing-and-protocol-adapters.md)。
3. [Session 签发契约](../../platform/contracts/auth-session-identity-issuance-v1.md)、[可信服务身份](../../platform/contracts/trusted-service-identity-v1.md)、[可信用户身份](../../platform/contracts/trusted-identity-v1.md)。
4. [Auth 路由](../../platform/contracts/auth-center-api-routing.md)与[App 路由](../../platform/contracts/app-center-api-routing.md)。
5. 固定 API repository revision 中的 Proto descriptors 和生成 Go module。

Gateway 当前只有一个实现 UC，本工作包直接读取以上权威输入，不扩展 App/Auth brief 生成器。

### 必须交付

- `module iwut-gateway`、Go 1.24、固定 `api/` submodule，以及 `github.com/TokenTeam/iwut-api-proto => ./api`。
- Domain/UseCase/Port/Adapter 边界与只含 composition root 的 `cmd/gateway`。
- 严格的 `config/routes.v1.yaml` schema、启动校验、重复/歧义检测及 descriptor 交叉验证。
- 从同一路由目录确定性生成并 `--check` Traefik file-provider 配置；固定 Traefik `v3.7.13`，部署镜像固定 digest。
- 首批路由全部登记；未登记 method/path、内部 Auth RPC 和启用的 OAUTH2 默认拒绝。
- Gateway caller-signed RS256 service JWS，调用 Auth identity RPC 时使用唯一 Gateway credential + 唯一终端 Session，2 秒默认有界 deadline，不重试。
- HTTP/JSON SESSION ForwardAuth；DIRECT 的逐路由凭据保留；前后两阶段 header 清理和固定前缀剥离。
- 原生 gRPC exact unary 前置代理；gRPC-Web 由 Traefik 转换后进入同一代理；正确 status/trailer、metadata 清理和 deadline/cancel 传播。
- 安全日志，只含 routeId、requestId、目标、结果类别和耗时，不含 Session、Authorization、JWS、body 或 private key。
- 真实 Traefik + Auth production composition/Mongo + verifier backend E2E，覆盖 HTTP/JSON、原生 gRPC、gRPC-Web 的成功与失败不会到达 upstream。

### 明确非目标

- OAuth2 路由、公开读取的新增策略、动态路由、热更新、数据库、Redis、事件总线或管理后台。
- streaming RPC、WebSocket、任意 transparent gRPC proxy、通配 service/package 转发。
- 客户端、Auth/App 业务逻辑、Auth 数据库直读、Gateway 自签用户身份或解析用户 claims 做业务授权。
- 生产公网发布；工作包只交付可复现部署配置和真实本地/CI 协议验收。

### 验收命令

仓库实现完成后至少提供并通过：

```bash
test -z "$(gofmt -l .)"
go test ./...
go test -race ./...
go vet ./...
go run github.com/goforj/wire/cmd/wire@v1.2.0 diff ./cmd/gateway
make -C api proto-check
go run ./cmd/gateway-config --check \
  --routes config/routes.v1.yaml \
  --traefik deploy/traefik/dynamic.generated.yaml
./scripts/test-protocol-e2e.sh
git diff --check

cd ../../docs
python3 -B -m unittest discover -s tools/tests
python3 -B tools/gen_brief.py --check --all
python3 -B tools/registry.py --check
git diff --check
```

`test-protocol-e2e.sh` 必须启动固定 Traefik、真实 Auth/Mongo、Gateway 和记录调用次数的 verifier backend；禁止用“直接请求 Gateway adapter”替代经过 Traefik 的三协议链路。测试结束必须清理自己的容器、网络和临时密钥。

## 2026-09-24 UC-AUTH-004 路由补充

Gateway `7ac853a` 固定 API `3912b55`，新增 Reviewer 管理与查询两条 SESSION 路由、显式 unary
代理适配以及重新生成的 Traefik 配置。Auth audience 不等同管理员授权，权限判断由 Auth 完成。
`make check` 与真实三协议 E2E 通过；测试使用 Auth 的真实 bootstrap CLI，并覆盖管理操作的
成功、权限不足、重复操作和 revision 冲突。未公开新的内部服务 RPC，未执行生产部署。

## OAuth / OIDC 后续工作包

以下只完成设计，均未启动实现；既有实现完成记录不包含这些能力。

| Use Case | 设计状态 | 实现状态 | 主要交付 |
| --- | --- | --- | --- |
| [UC-GW-002](../use-cases/UC-GW-002-authenticate-oauth-and-forward.md) | `PROPOSED` | `NOT_STARTED` | 应用委托请求鉴权与转发 |

## Console Session ForwardAuth 后续工作包

[ADR-CONSOLE-004](../../console/adr/ADR-CONSOLE-004-hybrid-bff-session-forward-auth.md) 已接受共享 Traefik + 混合 BFF 流量边界；Gateway 侧 [UC-GW-007](../use-cases/UC-GW-007-compose-console-session-forward-auth.md) 也已接受，由路由目录逐 Route 声明 Developer/Admin surface，并在 HTTP/JSON 上生成“清除外来 Session/内部身份 → 对应 BFF Session ForwardAuth → 删除 Cookie → 现有 route-specific Gateway ForwardAuth → post-auth scrub”的严格链。现有 Session `FORBIDDEN/OPTIONAL/REQUIRED` 决定是否调用 BFF，不新增第二套认证策略。

该工作包为 `IN_PROGRESS`。已接受 route schema 升版、固定 Router 优先级与公共 API Host 隔离、首版特殊凭据排除范围，以及下游 `SESSION_INVALID` 统一经 BFF Session clear 路径清理。实现依赖两个 BFF 的私有 ForwardAuth endpoint 和部署 surface 配置；必须以真实 Traefik、两个 BFF、Gateway ForwardAuth、Auth/backend 验证隔离、绕过与失败不抵达。设计状态更新本身不表示 Gateway Go、route catalog、生成物或部署已经完成。

实施所有权按包拆分：Gateway 包/生成器只交付普通 Console API exact Router、API deny Router 与 Session ForwardAuth 引用；BFF-owned `/api/*` 登录、Session、恢复、聚合 exact Router、SPA/static Router 和 BFF→Gateway 内部入口由 Console 部署 composition 交付。Console deployment composition 已验证当前 Session `40000` Router、SPA/static `1000` Router、私有路径隔离及与 Gateway 动态文件的合并装载；登录/恢复/聚合 exact Router 与 BFF→Gateway 非 Console 内部入口仍随 UC001 实现。完整部署验收前，UC-GW-007 保持 `IN_PROGRESS`，验收场景 6 不记为完成。

2026-10-07 接受失败契约修订：BFF Session ForwardAuth 基础设施故障允许任意 HTTP `5xx`，不再要求精确 `503/504`；固定 Traefik `v3.7.13` 的连接拒绝实测为 `500`。发布门禁固定为失败关闭、Gateway ForwardAuth 与业务 upstream 零调用，并且响应不得设置或清除 Console Cookie。联合 E2E 已通过双 BFF 正常路径、surface/AAD 隔离、来源与 Forwarded 清理、Gateway/Auth 身份失败不抵达、匿名 OPTIONAL、坏/过期 Cookie 响应无 `Set-Cookie`、backend `Set-Cookie` 删除、backend `500` 保持，以及 BFF 连接拒绝 5xx 的零下游调用/无 `Set-Cookie`。`make check` 与 `make protocol-e2e` 通过。Gateway-owned chain 已完成本地验证；Console deployment composition 随后也验证了当前 Session `40000` Router、SPA/static `1000` Router 和共享文件 Provider 合并。BFF-owned 登录/恢复 exact Router 与 BFF→Gateway 内部入口仍待 UC001 实现，因此本 UC 继续保持 `IN_PROGRESS`。

## 2026-10-06 后续 Gateway 设计记录

[ADR-GW-002](../adr/ADR-GW-002-route-credential-and-identity-policy.md) 提出新的路由凭据/身份交换矩阵；[ADR-PLAT-004](../../platform/adr/ADR-PLAT-004-unified-api-integration-baseline.md) 提出跨服务统一 API commit 门禁；UC-GW-002/003 均保持 `PROPOSED / NOT_STARTED`。本轮只记录设计，没有修改 Gateway worktree、API submodule、路由目录、Traefik 生成物或部署。

后续实现应等待正在进行的 Application suspension/restore 与对应 Auth 权限设计、API 形状和共同基线稳定，并由用户另行启动。当前 Auth registry 的 `UC-AUTH-026` 已用于 Application 关闭收敛；若新的权限用例尚未登记，应按届时 registry 的 Next ID 分配，不能复用已有编号。

## 2026-10-07 路由矩阵、应用运维路由与 UC-GW-003 本地完成

Gateway `0009947` 固定统一 API `9f914c5`，把 `routes.v1.yaml` 迁移为严格的 `iwut.gateway.routes/v2` 凭据矩阵。Session 的禁止/可选/必需、USER 的从不/有 Session 时/必需交换、原始凭据保留和 OAuth 相关失败关闭由同一 domain/usecase 模型驱动 HTTP ForwardAuth、原生 gRPC 与 gRPC-Web。首批 23 条路由还包括 Auth UC-AUTH-027 的应用运维权限接口、App UC-APP-028 的查询/暂停/恢复接口，以及 App UC023/024 的三个可选身份公开查询。

统一基线和消费者提交为：

- API `9f914c5`，共同包含 Gateway `758c426`、Auth `359c6bc`、App `a1bf6dd`；
- Auth `50dbbe7`，修正 optional `tester_membership_id` 消费并固定共同 API；
- App `0d06bbf` 固定共同 API，`b93fb25` 修复空 Catalog 应返回空页而不是 500；
- Gateway `0009947` 实现路由矩阵、路由扩展、生成配置和真实联合 E2E。

验收已通过 Gateway `make check`、`make protocol-e2e`，Auth `make check`，App quick verification 与定向 Mongo 空 Catalog 集成测试。协议 E2E 启动固定 Traefik、真实 Auth/Mongo、真实 App/Mongo 和 Gateway，覆盖 Auth 必需身份，以及 App 三个公开查询的匿名路径与 Catalog 的有效/无效 Session 路径；HTTP/JSON、原生 gRPC、gRPC-Web 均经过真实进程。OAuth Bearer、OIDC Basic/Portal Cookie 与委托交换仍在装载期失败关闭，UC-GW-002 未开始。

以上提交尚未 push，因此状态为 `VERIFIED_LOCAL`，不能作为 CI/发布候选；未执行生产部署。

## 2026-10-07 特殊终端凭据路由实现

基于 Auth UC011/025、Auth UC026 与 App UC027，把当前 v2 无法表达的六条特殊 route 拆为三个 Gateway 行为用例：

- [UC-GW-004](../use-cases/UC-GW-004-forward-optional-session-to-auth.md)：Begin/Complete EmailBinding 允许 Session 缺失；提供时只原样下传给 Auth，任何坏 Session 不匿名降级。
- [UC-GW-005](../use-cases/UC-GW-005-forward-account-closure-credentials.md)：账号注销五条 route 作为闭合工作包；Confirm/Cancel 只允许 confirmation token，Get 只允许 receipt token，全部禁止通用身份混用。
- [UC-GW-006](../use-cases/UC-GW-006-forward-application-close-proof.md)：CloseApplication 同时要求 Session→App USER JWS 和唯一 high-risk proof；身份交换成功后才向 App 下传，Gateway 不解析 proof claims。

三项均已接受，Gateway `293ebc9` 在固定 API `9f914c5` 上实现：新增 13 条精确 route（共 36 条），包含邮箱 GetOwn 和 ApplicationCloseReauth Begin/Complete 三条配套入口；增加严格 32-byte RawURL Session/token、16 KiB compact-JWS proof、Cookie/已知 terminal header 全局默认拒绝、路由后最小恢复与 13 条特殊 RPC 完整认证矩阵防漂移。HTTP ForwardAuth、原生 gRPC 和 gRPC-Web 共用同一 usecase 判定；伪造内部身份仍先清除。

`make check` 与 `make protocol-e2e` 通过；后者继续使用真实 Traefik、Auth、App 与 Mongo 验证现有 HTTP/JSON、原生 gRPC、gRPC-Web 链路无回归。新特殊 route 已通过 usecase、ForwardAuth、记录式 gRPC proxy 和 Traefik 生成契约测试，但现有真实 E2E 尚未打开邮箱绑定、账号注销与应用关闭 feature flag，也未覆盖 Prepare token 响应正文、proof 真实业务拒绝或 gRPC-Web 重复 header。因此状态为 `IMPLEMENTED`，不记为 `VERIFIED_LOCAL/COMPLETE`。未 push，未生产部署。

部署联合验收至少需显式配置 `AUTH_USER_ENDPOINTS_ENABLED`、`AUTH_EMAIL_BINDING_ENABLED`、`AUTH_ACCOUNT_CLOSURE_ENABLED`、`AUTH_APPLICATION_CLOSE_REAUTH_ENABLED` 与 `APP_CENTER_APPLICATION_CLOSURE_ENABLED`，并满足邮件/HMAC、账号归属退出、身份签名及 App 关闭依赖。Gateway 不感知这些开关；后端关闭时的 404/UNIMPLEMENTED/UNAVAILABLE 不得误记为路由验收成功。

## 2026-10-07 Auth/App Proto 外部 API 全量接入

Gateway `7a3eb7c` 在固定 API `9f914c5` 上再新增 51 条普通策略 route：Auth 19 条（`PUBLIC` 2、`AUTH_DIRECT_SESSION` 10、`AUTH_USER` 7）与 App `APP_USER` 32 条。目录现有 87 条精确 Proto route，与 pinned descriptors 中全部 44 个 Auth、43 个 App `google.api.http` 外部方法闭合；每条 gRPC route 均有编译期类型化 unary adapter。Scope/DeveloperStatus/SystemPrincipal/identity/OAuth delegation/Auth application-closure/account-owner-exit 与 App OAuth provider/account-owner-exit 等内部 RPC 继续不登记。

实现同时把 `x-iwut-access-token` 加入全局已知敏感载体：在 UC-GW-002 接受/实现前，所有已有 route 均在认证阶段拒绝，HTTP 请求/响应与 gRPC metadata 均清理，不把 OAuth access token 静默传给普通业务 upstream。DIRECT Session 仍为逐 RPC 有限白名单；App 细粒度 Developer/Reviewer/管理员授权仍由下游基于 `iwut-app-center` USER JWS 权威判断。

`make check` 与 `make protocol-e2e` 在最终冻结内容上通过。真实 Traefik、Gateway、Auth、App、Mongo E2E 新增覆盖 Auth `ListOwnSessions` DIRECT 路由和 App `GetApplicationFilter` USER 路由，三协议均验证有效 Session 到达真实后端以及缺失 Session 失败关闭。其它 49 条新 route 由 descriptor/catalog/typed-adapter 闭合测试与 Auth/App 各 UC 后端测试覆盖，仍应在对应 feature flag 部署批次执行业务成功/拒绝联合验收。未 push，未生产部署。

Auth 发布批次需按能力显式开启 `AUTH_USER_ENDPOINTS_ENABLED`、`AUTH_EMAIL_LOGIN_ENABLED`、`AUTH_DEVELOPER_APPLICATION_ENABLED`、`AUTH_SESSION_MANAGEMENT_ENABLED`、`AUTH_PLATFORM_ADMIN_ENDPOINTS_ENABLED`、`AUTH_ACCOUNT_MANAGEMENT_ENDPOINTS_ENABLED`、`AUTH_DEVELOPER_MANAGEMENT_ENDPOINTS_ENABLED`、`AUTH_DEVELOPER_WITHDRAWAL_ENABLED` 及相应邮件、OAuth manifest、owner-exit、身份签名/受信 caller 依赖。App 这 32 条无独立 feature flag，但仍依赖各 UC 的 migration、外部 provider 与业务数据就绪。

## 2026-10-03 应用审核权限路由扩展完成

[UC-AUTH-004](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md) 新增两个显式应用审核权限方法，映射见 [Auth 路由契约](../../platform/contracts/auth-center-api-routing.md)。Gateway `6b3f0d9` 固定 API `758c426`，已追加静态 HTTP/原生 gRPC/gRPC-Web SESSION 路由、显式 unary 代理适配及生成的 Traefik 配置，目标 audience 仍为 iwut-auth-center，旧 reviewer-permission 路由保持版本权限语义。`make check` 与 `make protocol-e2e` 通过：真实 Traefik/Auth/Mongo 下覆盖两项独立权限、新旧接口混用、路径覆盖和权限不足。增量 COMPLETE，未 push 或生产部署。
