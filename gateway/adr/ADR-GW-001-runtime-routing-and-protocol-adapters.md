# ADR-GW-001：Gateway 运行时、路由目录与协议适配

状态：`ACCEPTED`

日期：2026-09-24

## 背景

[UC-GW-001](../use-cases/UC-GW-001-authenticate-and-forward.md) 要求同一份路由决定目标服务、认证模式和凭据边界，并同时覆盖 HTTP/JSON、原生 gRPC 与 gRPC-Web。Traefik 继续承担公网 Edge、TLS、路由匹配和 gRPC-Web 终止；Gateway 不能复制 Auth 业务、保存 Session 或依赖客户端提供的策略字段。

Traefik ForwardAuth 能把认证响应头复制到后续请求，适合 HTTP/JSON 的 SESSION 编排。但它拒绝原生 gRPC 时返回普通 HTTP 响应，不能稳定提供协议正确的 gRPC status/trailer。因此三种协议不能仅靠同一 ForwardAuth middleware 完成。

## 决定

### Go module 与 API 依赖

Gateway 是部署型可执行服务，不作为供其它仓库导入的 Go library。首版固定：

```text
module iwut-gateway
go 1.24.0
```

独立 API 仓库作为 `api/` Git submodule 固定 revision，并作为自己的 Go module 使用：

```text
require github.com/TokenTeam/iwut-api-proto v0.0.0
replace github.com/TokenTeam/iwut-api-proto => ./api
```

Gateway 只从 `github.com/TokenTeam/iwut-api-proto/gen/go/...` 导入生成包。不得用 Gateway module 前缀再次形成第三份生成类型身份。submodule pointer 必须已推送且 CI 可获取；浮动远程分支不构成构建输入。

### Traefik 版本与配置提供方

首版固定 Traefik `v3.7.13`。部署清单必须进一步固定官方镜像的 multi-arch digest；禁止 `latest`、`v3` 或 `v3.7` 等浮动标签。升级 patch/minor 版本必须先运行本 ADR 的真实协议 E2E，再在独立提交中修改固定值。

首版使用版本控制内的 file provider 静态/动态 YAML，不同时引入 Docker label、Kubernetes CRD 或 Gateway API provider。公网 entrypoint：

- 显式配置 `aliasHeadersStrategy: reject`；
- ForwardAuth 显式配置 `trustForwardHeader: false`；
- `forwardBody: false`，认证组件永不读取业务 body；
- 只把 Session、终端 Authorization 及 Traefik 生成的请求元数据送往认证组件；
- `authResponseHeaders` 只允许 `x-iwut-identity`；
- 设置 `maxResponseBodySize: 4096`，成功响应 body 为空；
- 认证组件和 gRPC 前置代理监听器仅对 Traefik/内部网络开放。

### HTTP/JSON

HTTP/JSON 由 Traefik 完成最终业务反向代理。每条路由使用由目录生成的 middleware chain：

1. 删除终端提供的 `x-iwut-identity`、旧身份头、内部策略头及不允许的 Forwarded 别名；
2. SESSION 路由调用该 routeId 专属的 ForwardAuth URL；DIRECT 路由不调用认证组件；
3. SESSION 成功时仅复制认证组件返回的单个 `x-iwut-identity`；
4. 按路由删除 Session、Authorization 和内部控制头；仅两个撤销 DIRECT 路由可保留 Session；
5. 按目标服务固定前缀执行一次剥离，再转发到固定 HTTP upstream。

ForwardAuth URL 中的 routeId 由生成的 Traefik 配置写入，不从客户端 header/query/body 读取。认证组件仍用 Traefik 生成的 method/URI 与目录反向核对，任何不一致失败关闭。认证调用不携带或缓冲业务 body。

### 原生 gRPC 与 gRPC-Web

原生 gRPC 不使用 ForwardAuth。Traefik ForwardAuth 的非 2xx 响应是普通 HTTP 响应，无法满足 UC-GW-001 的 gRPC 错误语义。

Gateway Go 进程提供一个仅由 Traefik 到达的原生 gRPC 前置代理：

- 只注册路由目录明确列出的 unary RPC，未知 full method 默认 `UNIMPLEMENTED`；
- 不使用 package/service 通配 unknown handler；
- DIRECT 按路由保留最小凭据后调用固定 generated client；
- SESSION 恰好调用一次 Auth `UserIdentityService/IssueUserIdentityFromSession`，成功后清除 Session、终端 Authorization 和 Gateway 服务 JWS，只向业务 upstream 写入单个 `x-iwut-identity`；
- 签发失败在本地映射为 UC-GW-001 规定的 gRPC status，业务 upstream 不被调用；
- downstream 的业务 status、message 与 trailers 原样返回，不自动重试或重放写请求。

gRPC-Web 先由 Traefik `GrpcWeb` middleware 转成原生 gRPC，再进入同一个 Gateway gRPC 前置代理。这样认证失败先成为正确的原生 gRPC status，再由 Traefik 编码回 gRPC-Web。首版不支持 streaming RPC；新增 streaming 需要独立 ADR 和流量/取消传播验收。

Go 进程可在同一 composition root 中启动内部 HTTP ForwardAuth listener 与 gRPC listener，但两个 transport adapter 共享同一 Route Catalog UseCase、Auth issuer port、服务身份 signer 和有界错误分类。

### 机器可读路由目录

唯一人工维护的路由源为 `config/routes.v1.yaml`，schema 标识固定为：

```yaml
apiVersion: iwut.gateway.routes/v1
services:
  auth-center:
    externalPrefix: /auth-center
    httpUpstreamEnv: GATEWAY_AUTH_CENTER_HTTP_URL
    grpcUpstreamEnv: GATEWAY_AUTH_CENTER_GRPC_TARGET
  app-center:
    externalPrefix: /app-center
    httpUpstreamEnv: GATEWAY_APP_CENTER_HTTP_URL
    grpcUpstreamEnv: GATEWAY_APP_CENTER_GRPC_TARGET
routes:
  - id: app.create-application
    rpc: /app_center.v1.application.Application/CreateApplication
    targetService: app-center
    protocols: [HTTP_JSON, GRPC, GRPC_WEB]
    auth:
      mode: SESSION
      audience: iwut-app-center
      directCredential: NONE
```

规则：

- YAML 使用严格 decoder：拒绝未知字段、重复 key、隐式类型替换和多个 document；
- `id`、`rpc`、HTTP method/path、外部匹配和 target 必须唯一且无歧义；
- `rpc` 必须存在于固定 API descriptor；HTTP_JSON 还必须存在 `google.api.http` annotation；
- 外部 HTTP path 只能由服务前缀加 Proto 内部 path 推导，目录不重复手写第二份内部/外部路径；
- SESSION 必须使用目标服务固定 audience；DIRECT 禁止 audience；OAUTH2 在 v1 schema 中可解析但任何启用路由均拒绝启动；
- `directCredential` 只有 `NONE` 或 `SESSION`，且 SESSION 仅允许登记的撤销方法；
- upstream 实际地址只从上表命名的环境变量取得，目录不保存 URL、secret 或动态 target；
- 内部 Auth RPC（签发、Scope Catalog、Developer Status、System Principal）禁止进入公开目录。

同一个校验/生成程序读取该目录与 API descriptors，确定性地产生 Traefik file-provider 配置，并生成或验证 Gateway 使用的路由常量。生成物可提交，但手工修改必须被 `--check` 检出。运行时启动仍校验目录、upstream 配置和生成摘要一致，不接受热更新或远程策略。

## 代码边界

首版采用：

```text
cmd/gateway/                 composition root
cmd/gateway-config/          route/descriptor validator and deterministic generator
internal/route/domain/       Route、协议与认证模式值
internal/route/usecase/      路由选择和认证编排
internal/route/port/         identity issuer、HTTP/gRPC forward ports
internal/adapter/authgrpc/   Auth 签发 generated client 与 service JWS
internal/adapter/forwardauth/ HTTP ForwardAuth transport
internal/adapter/grpcproxy/  精确 unary gRPC transport/forwarder
internal/config/             严格环境与 route catalog 装载
config/routes.v1.yaml        唯一路由源
deploy/traefik/              固定 v3.7.13 配置与生成物
api/                         固定 API repository revision
```

Domain/UseCase 不导入 Traefik、gRPC、HTTP、generated Proto、JWS 库或部署配置。只有 adapter/composition root 知道协议和具体依赖。

## 考虑过的替代方案

### 三种协议全部使用 ForwardAuth

成功请求可工作，但 gRPC 认证失败会收到普通 HTTP 响应而不是正确 gRPC status/trailer，因此不采用。

### 全部业务流量由自写 Go reverse proxy 转发

可统一协议控制，但会重复 Traefik 已承担的 HTTP Router 能力并扩大自研代理面。首版仅让 gRPC 进入必要的协议前置代理，HTTP 保持 Traefik 最终转发。

### 每个服务维护独立路由 YAML

会让认证策略、Traefik 配置和 Gateway 运行时目录漂移，因此不采用。只有 `config/routes.v1.yaml` 是人工权威。

### 动态数据库路由或管理后台

首版只有固定平台 API，不值得引入状态、热更新和新的授权面，因此不采用。

## 结果

优点：

- HTTP 保留 Traefik 的成熟代理路径，gRPC 失败保持协议正确；
- 三种协议共享一个严格路由目录和认证 UseCase；
- API 类型只有一个 canonical Go import identity；
- 未登记方法、OAUTH2 和内部 RPC 默认关闭。

代价：

- Gateway 同时维护 HTTP ForwardAuth 与 unary gRPC transport；
- 每个公开 gRPC RPC 需要显式 generated adapter 注册；
- Traefik 升级必须跑真实三协议 E2E。

## 参考

- [Traefik v3.7.13 release](https://github.com/traefik/traefik/releases/tag/v3.7.13)
- [Traefik ForwardAuth v3.7](https://doc.traefik.io/traefik/v3.7/reference/routing-configuration/http/middlewares/forwardauth/)
- [Traefik GrpcWeb middleware](https://doc.traefik.io/traefik/v3.7/reference/routing-configuration/http/middlewares/grpcweb/)
- [Traefik issue #3654: ForwardAuth gRPC failure response](https://github.com/traefik/traefik/issues/3654)
