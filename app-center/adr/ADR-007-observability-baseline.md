# ADR-007：App Center 可观测性基线

状态：`ACCEPTED`

日期：2026-10-07

## 背景

App Center 已有少量针对数据不变量和后台协调失败的结构化错误日志，也由 Kratos 暴露标准 gRPC health service；但各入口尚无统一的请求日志、分布式 trace、请求指标与 HTTP 探针。故障排查目前无法稳定关联一次 HTTP/gRPC 请求及其下游 Auth 调用，也无法从低基数指标判断错误率和延迟。

可观测性是进程和 adapter 的技术职责。它不改变 Application、ApplicationVersion、Review、Publication、Tester、OAuth Client 或其他领域对象，也不产生领域审计事实。

## 决定

App Center 建立以下首版基线：

1. 进程日志使用 JSON Lines 输出到标准错误，至少包含时间、级别、消息和 `service.name=iwut-app-center`。请求日志只记录 transport、固定路由/RPC operation、稳定状态码、稳定 error reason、耗时以及存在时的 trace/span ID。
2. HTTP 与 gRPC 服务入口使用 W3C Trace Context/Baggage 传播并创建 server span；原生 gRPC Auth client 继续传播同一上下文。Trace 和 metric 通过 OTLP gRPC 导出；未配置 collector endpoint 时 exporter 关闭，服务仍可启动。
3. 请求总量和耗时只使用有界标签：transport kind、固定 operation、状态码和稳定 error reason。进程从实际注册的 HTTP route 与 gRPC service 建立 operation 白名单，未注册值统一折叠为每种 transport 的 `unmatched`。禁止把 `applicationId`、`authId`、`clientId`、URL、hostname、scope、自由文本或任何用户输入用作 metric label。
4. Kratos 自带的标准 gRPC health service 保持无身份可访问。HTTP 同一监听器增加 `/livez` 和 `/readyz`：liveness 只表示进程能响应；readiness 在有界超时内重新验证 MongoDB 事务拓扑和最新 migration ledger。探针不返回内部错误正文。
5. OTLP endpoint、TLS/plaintext、trace 采样比例、metric 导出周期和日志级别只在配置边界读取。显式非法值阻止启动。生产默认使用 TLS；本地 collector 可以显式开启 plaintext。
6. exporter 初始化失败时，显式配置的服务启动失败。运行期间 collector 暂时不可达由 OTel exporter 有界重试，不影响业务请求；进程关闭时以固定超时 flush trace 和 metric。

## 数据最小化

日志、span、metric 和探针都不得记录或附加以下内容：

- JWS/JWT、Authorization header、OAuth secret 或 digest、Tester secret/tokenHash、完整加入 URL；
- 请求或响应 body、任意用户 KV、资料正文、redirect URI 清单、完整 scope 清单；
- MongoDB URI、私钥、公钥正文、caller registry 或其他配置 secret；
- 自由文本暂停/关闭/审核理由和底层数据库错误正文。

稳定 error reason、固定 operation、transport、状态码和 duration 可以进入日志、span 或 metric。现有领域审计记录仍由各 UC 的事务规则产生，技术 telemetry 不替代也不补写审计记录。

## 性能与可靠性

- trace 使用 parent-based ratio sampling；默认采样率为 `0.1`，可配置为 `0`–`1`。
- trace 使用 batch processor，metric 使用 periodic reader；默认 metric 周期 `30s`。
- 请求热路径不进行同步网络导出。collector 故障不得改变业务返回值。
- readiness 的 MongoDB 检查使用 `2s` 超时，失败只返回 `503` 和固定响应。

## 结果

服务获得厂商中立的 OTLP 出口、可关联的结构化日志和标准探针。增加的代价是 OTel SDK/exporter 依赖、少量内存与 CPU 开销，以及 readiness 对 MongoDB 的周期性只读检查。采样、批处理、低基数标签和默认关闭 exporter 控制这部分成本。

## 验证

- 配置单元测试覆盖默认值、显式值和 fail-closed 校验。
- middleware 测试覆盖低基数字段、trace 关联、错误脱敏和 body/token 不进入日志。
- HTTP 测试覆盖 `/livez`、readiness 成功/失败及固定响应。
- 真实服务 E2E 覆盖标准 gRPC health、HTTP 探针和原有 HTTP/gRPC 业务回归。

## 关联文档

- [ADR-003：Go package 与依赖边界](ADR-003-go-package-and-dependency-boundaries.md)
- [ADR-005：领域错误与 Transport 映射](ADR-005-domain-errors-and-transport-mapping.md)
- [实现总览](../implements/README.md)
