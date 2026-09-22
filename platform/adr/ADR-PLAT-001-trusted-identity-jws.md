# ADR-PLAT-001：可信身份使用短期、audience 绑定的 JWS

状态：`ACCEPTED`

日期：2026-09-21

## 背景

App Center 的写用例需要可信的 `authId` 与 `developerStatus`。旧系统由 Gateway Auth Forward 把未签名的 JSON claims 放进 `X-Auth-*-Claim` 请求头，下游服务直接信任。该方案没有签名、没有 audience 绑定、没有开发者资格字段，任何能到达后端或绕过 Gateway 的调用方都能伪造身份，无法作为新系统的信任边界。

新系统已经确立 Auth Center、Gateway 与 App Center 的职责分离。需要一条跨系统的身份信任决定：身份由谁签发、如何绑定到目标服务、在哪里校验，以及 Gateway 必须做什么。

## 决定

可信身份采用 **Auth Center 签发短期、audience 绑定的 compact JWS，Gateway 只转发，App Center 本地验签** 的模型。

- Auth Center 是唯一签发方。签发的 JWS 明确绑定目标服务 audience，格式与字段见 [trusted-identity-v1](../contracts/trusted-identity-v1.md)。
- Gateway 不解析、不重签身份。它对每个已完成鉴权的请求**剥离**客户端可能携带的同名头，**写入**由 Auth Center 取得的 JWS，再原样转发。
- App Center 在进程内用启动配置的公钥验签。它**不读取 Auth 数据库**，也**不每请求回调 Auth**。
- 传输载体统一为 `x-iwut-identity`：HTTP 上是请求头，gRPC 上是 metadata 同名键。同一键、同一紧凑 JWS 值。
- 领域层与 UseCase 不感知 JWS。验签、时钟、时钟偏差、issuer/audience/TTL 与密钥解析都是 transport 与 composition root 的职责；验签结果先成为通用可信身份，再由入口投影成用例所需的最小 `DeveloperIdentity`（`authId` + `developerStatus`）或 `ReviewerIdentity`（`authId` + `permissions`）。
- 旧未签名 JSON Header 不进入新系统，也不建立兼容层。

字段级约束、算法、校验顺序、错误边界与密钥轮换细节由 [trusted-identity-v1](../contracts/trusted-identity-v1.md) 单独定义；本 ADR 不复制正文。

## 考虑过的替代方案

### 继续使用未签名的 JSON Header

实现成本低，但信任来自网络位置而不是密码学证明。一旦后端可被直接访问、Gateway 路由配置错误或存在请求头透传，身份即可伪造。缺少 audience 与开发者资格字段也无法满足 UC-APP-001。因此不采用。

### 每请求回调 Auth Center

把校验集中到 Auth Center，但为每个业务请求增加一次同步远程依赖，放大延迟与故障面，并要求 App Center 在 Auth 不可用时拒绝全部写请求。本地验签等价地获得可信身份，且无每请求耦合。因此不采用。

### Gateway 验签后转发明文身份

Gateway 可校验签名，但仍需把结果传给后端；若转发的是明文身份，后端必须信任网关网络位置，与旧模型有相同的伪造面。让 Gateway 只做透传、每个消费方各自验签，信任边界更清晰。因此不采用。

### App Center 直接读取 Auth 数据库

绕过 Auth 的资格判定与审计边界，把数据库 schema 变成跨系统契约，且违反 ADR-003 的能力边界。因此不采用。

## 结果

优点：

- 身份可被离线、可复现地验证，不依赖调用方网络位置。
- audience 绑定限制 token 只能用于声明过的服务；TTL 上限限制泄露窗口。
- App Center 无 Auth 运行时依赖，可用启动配置与 fake 密钥做确定性测试。
- Gateway 职责最小：剥离、写入、转发。

代价：

- 需要跨系统维护 JWS header/claims 契约与密钥轮换流程。
- 每个消费方都要实现验签；契约变更需要多方同步。
- 启动配置必须提供 issuer、audience、最大 TTL、允许时钟偏差与 kid→公钥；缺失或非法必须阻止启动。

## 关联文档

- [可信身份 JWS v1 契约](../contracts/trusted-identity-v1.md)
- [App Center API 路由 v1 契约](../contracts/app-center-api-routing.md)
- [平台共享设计文档](../README.md)
