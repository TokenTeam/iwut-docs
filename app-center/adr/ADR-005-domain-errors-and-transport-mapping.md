# ADR-005：领域错误与 Transport 映射

状态：`PROPOSED`

日期：2026-09-19

## 背景

Use Case 已定义稳定的业务失败名称，例如 `InvalidApplicationName`、`ApplicationQuotaExceeded` 和 `ApplicationProfileRevisionConflict`。这些错误需要被 Domain、UseCase、MongoDB adapter、gRPC 和 HTTP 一致识别。

若 Domain 直接返回 Kratos error、gRPC status 或 Proto enum，业务模型会依赖 transport；若客户端根据错误文本判断，修改文案就会破坏行为。基础设施错误也不能直接暴露数据库或网络细节。

## 决定

Domain 与 UseCase 使用协议无关的稳定错误分类。每个可预期业务失败具有：

```text
stable code
human-readable internal message
optional safe details
optional wrapped cause
```

稳定 code 使用设计文档中的业务失败名称。调用者通过错误类型、code 或 `errors.Is` 判断，不解析 message。

错误分为：

- Validation：输入无法形成合法值对象。
- Authentication：缺少或无效可信身份。
- Authorization：身份存在但没有执行权限。
- NotFound：目标不存在，或按隐私规则必须隐藏归属不匹配。
- Conflict：状态、唯一性、revision、容量或并发前置条件冲突。
- DependencyUnavailable：完成当前行为所需的外部事实暂不可用。
- Internal：未预期的实现或基础设施失败。

MongoDB/Auth 等 adapter 负责把技术错误转换为 port 定义的稳定结果，同时保留 cause。UseCase 再按业务上下文确定最终领域错误。例如 duplicate key 不能直接泄露索引名。

Transport adapter 在一个集中映射表中把领域错误转换为：

- 稳定 Proto error reason；
- canonical gRPC status；
- 对应 HTTP status；
- 可以安全返回的 message/details。

新 API 不采用“所有 HTTP 响应都返回 200，再在 JSON body 中表达错误”的形式。HTTP 与 gRPC 使用各自标准状态语义，稳定业务 code 供客户端做细分处理。

未知错误统一映射为 Internal，不向客户端返回 cause、数据库字段、索引名、远程地址、token、secret 或 stack trace。日志和 trace 在服务端保留原 cause，并使用同一 trace ID 关联。

## 隐私与存在性隐藏

当 UC 规定跨 Application 的资源归属不匹配按 NotFound 处理时，Transport 不得把内部的“存在但不属于调用者”转换成 Forbidden。存在性隐藏属于业务契约，而不是展示文案。

错误 details 采用明确 allowlist。字段校验可以返回安全字段名和约束类别，但不能回显任意用户内容或凭证。

## 考虑过的替代方案

### Domain 直接使用 Kratos errors

实现较快，但 Domain 被框架和协议状态绑定，单元测试也需要理解 transport，因此不采用。

### 只返回 sentinel errors

适合少量错误，但难以携带安全 details、cause 和统一分类。允许内部使用 sentinel 作为匹配机制，但对外仍通过结构化领域错误表达。

### 客户端只根据 HTTP/gRPC status 处理

同一 status 下存在多个不同业务恢复动作，例如 revision conflict 与容量已满。仅使用协议状态不够，因此同时返回稳定业务 code。

## 结果

优点：

- Domain 不依赖 transport/framework。
- 客户端可以依赖稳定 code，而不是文本。
- HTTP、gRPC、日志和基础设施错误的职责清楚。
- 隐私隐藏规则可以被契约测试验证。

代价：

- 需要维护领域错误、Proto reason 和 transport mapping。
- 新增业务错误时必须同时增加映射测试。

## 关联文档

- [统一实现约定](../implements/implementation-conventions.md)
- [文档规范](../document-conventions.md)
