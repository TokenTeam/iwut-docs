# ADR-PLAT-002：内部服务调用使用调用方签名 JWS

状态：`ACCEPTED`

日期：2026-09-22

## 背景

App Center 需要调用 Auth Center 的 Scope Catalog、Developer Status 与 System Principal 原生 gRPC API。仅依赖内网、容器网络或固定源地址不能证明调用方身份；接受 token 自带的公钥也会让调用方自行决定信任根。部署同时需要支持 docker-compose 与本地直接启动，不能要求应用代码只从编排器挂载文件读取配置。

## 决定

内部服务身份采用**调用方用预登记私钥签发短期、audience 绑定的 RS256 compact JWS，提供方按 `serviceId + kid` 选择预登记公钥并本地验签**。

- App Center 为每次 Auth unary RPC 生成新的 JWS，通过 gRPC `authorization: Bearer <JWS>` metadata 发送。
- Auth Center 不接受 token 中的 `jwk`、`x5c`、`x5u` 或其它自带密钥材料；未验签的 `iss` 只用于在本地注册表中定位 `serviceId`，`kid` 只用于定位该服务下的公钥。
- 验签成功后仍要按固定的 RPC → permission 映射检查服务 allowlist。客户端不能在 token 中自报权限。
- 配置由进程直接读取环境变量。PEM 与调用方注册表使用严格 standard Base64 包裹，避免多行、引号和 YAML/shell 转义差异。部署平台可以从 secret/config 注入环境变量，但程序不依赖固定文件路径。
- System principal 的 opaque Auth ID 由 Auth Center 拥有并在启动时幂等 provision。App Center 通过受保护的内部 API 按 purpose 解析并做进程内成功缓存，不把静态 Auth ID 作为启动依赖。

线格式、配置 schema、权限映射与轮换规则见 [trusted-service-identity-v1](../contracts/trusted-service-identity-v1.md)；System principal 查询见 [auth-system-principal-v1](../contracts/auth-system-principal-v1.md)。

## 结果

- 服务认证不依赖数据库直读、网络位置或 token 自带信任根。
- `serviceId + kid` 支持逐服务撤销和双密钥轮换；固定 allowlist 使认证与授权分离。
- Base64 环境变量可用于本地进程和容器编排；私钥仍应由部署 secret 管理，且不得写入仓库、日志或命令回显。
- Auth Center 的启动会建立所需 SYSTEM principal，因此 CD 只需保证 Auth 在 App 首次触发相关业务前可用；App 可以独立启动，依赖失败时业务 fail closed 并可重试。

## 不采用的方案

### token 自带公钥

调用方可自行更换信任根，等价于没有预登记身份，因此禁止。

### 只按环境变量分别列出 serviceId、公钥和权限

多调用方、多 kid 时容易发生并行列表错配。采用一个 Base64 JSON 注册表，使每个服务的状态、keys、permissions 与允许的 System purpose 形成同一条原子配置记录。

### 应用只读取挂载文件

文件挂载适合生产 secret，但会让本地直接启动依赖特定路径。应用统一读取 ENV；编排器负责把 secret/config 投影为 ENV。若未来安全基线禁止私钥 ENV，再通过新 ADR 改为 secret provider，不在本版同时支持两套隐式优先级。

### App Center 配置固定 System Auth ID

这会把 Auth 启动时生成的数据变成 App 的部署时静态耦合，并要求 CD 先查询再改写 App 配置。按 purpose 查询并缓存能保持 Auth 所有权，同时避免每次业务请求查询。

## 关联文档

- [内部服务身份 JWS v1](../contracts/trusted-service-identity-v1.md)
- [Auth System Principal v1](../contracts/auth-system-principal-v1.md)
- [可信用户身份 JWS v1](../contracts/trusted-identity-v1.md)
