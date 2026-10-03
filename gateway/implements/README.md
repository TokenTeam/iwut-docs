# Gateway 实现状态

| 用例 | 设计 | 实现 | 缺口 |
| --- | --- | --- | --- |
| [UC-GW-001](../use-cases/UC-GW-001-authenticate-and-forward.md) | `ACCEPTED` | `COMPLETE` | —（当前后端/本地部署工作包；生产公网发布仍为独立部署事项） |

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

## 2026-10-03 应用审核权限路由扩展完成

[UC-AUTH-004](../../auth-center/use-cases/UC-AUTH-004-manage-reviewer-permission.md) 新增两个显式应用审核权限方法，映射见 [Auth 路由契约](../../platform/contracts/auth-center-api-routing.md)。Gateway `6b3f0d9` 固定 API `758c426`，已追加静态 HTTP/原生 gRPC/gRPC-Web SESSION 路由、显式 unary 代理适配及生成的 Traefik 配置，目标 audience 仍为 iwut-auth-center，旧 reviewer-permission 路由保持版本权限语义。`make check` 与 `make protocol-e2e` 通过：真实 Traefik/Auth/Mongo 下覆盖两项独立权限、新旧接口混用、路径覆盖和权限不足。增量 COMPLETE，未 push 或生产部署。
