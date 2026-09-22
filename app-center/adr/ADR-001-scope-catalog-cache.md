# ADR-001：Scope Catalog 权威来源与缓存

状态：`PROPOSED`

日期：2026-09-15

## 背景

ApplicationVersion 创建、修改和提交审核时必须验证 requiredScopes 和 optionalScopes。Scope 的定义与可用状态属于 Auth Context，App Center 不能维护第二份可独立修改的权威目录。

现有代码并没有 Auth Scope Catalog 同步机制：`iwut-app-center/internal/util/config_center.go` 只是硬编码 `read__email/read__phone/read__gender`。当前仓库也没有 RabbitMQ/AMQP 依赖或运行基础设施。

Scope Catalog 很小、变更低频，而创建版本是低频管理操作，不是高吞吐请求路径。

## 决定

### 权威来源

Auth 是 Scope Catalog 唯一权威来源。Auth 提供可读取完整快照的内部接口：

```text
ScopeCatalogSnapshot {
  revision: int64
  scopes: []ScopeDefinition
  generatedAt: Instant
}
```

revision 必须在 Auth 内单调递增。提供方行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 定义；跨服务 `ScopeDefinition` 首版投影和 gRPC 方法由 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md) 定义。

ScopeCatalog adapter 在完成校验时一并返回所使用的 snapshot revision。创建和修改草稿可以忽略它；UC-APP-004 将它写入 ApplicationReview，用于说明提交时依据的 Auth 目录版本。

### 第一阶段缓存

App Center 的 ScopeCatalog adapter 使用每进程 read-through cache：

- TTL 由 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL` 使用 Go duration 文本配置，未设置时默认 `5m`；显式值为空、无法解析、为零或负数时进程组装失败，不静默回退。
- 进程启动或 cache miss 时同步读取 Auth 快照。
- TTL 内直接使用缓存快照。
- TTL 到期时同步刷新；使用 singleflight 合并同一时刻的刷新请求。
- 刷新失败时不使用过期快照创建版本，返回 `ScopeCatalogUnavailable`。
- Auth revision 发生回退时视为不可用并 fail closed，避免用较旧快照覆盖进程已经观察到的较新事实。
- 不为此单独引入 Redis。

这是有界缓存，不是 App Center 自己的 Scope Catalog。缓存内容不能被 App Center 管理接口修改。

环境变量只由 config/composition boundary 读取；Cache adapter 通过构造参数接收已经校验的 TTL、Clock 与 snapshot source，不直接读取进程环境。真实 Auth transport 必须实现共享 gRPC 契约；测试可以使用实现同一生成接口的 Auth Server 或 port fake，不得在生产代码中硬编码目录。

### 多阶段校验

- 创建 DRAFT：使用上述有界缓存，尽早发现无效 scope。
- 提交审核：重新确认 scope 仍允许新版本申请。
- reviewer 批准：再次确认 snapshot 中的全部 scope，并把所用 catalog revision 写入 decision.approvalValidation；详见 UC-APP-005。
- 放入发布槽位：再次确认 approved snapshot 中的 scope，并把所用 catalog revision 写入 PublicationHistory；UC-APP-007 首先应用于 test 槽位。
- consent/token/用户数据读取：Auth 必须以自己的当前规则做最终授权，不能相信 App Center 过去的校验结果。

因此短暂缓存只影响开发体验，不会成为实际授权边界。

## 为什么现在不上 RabbitMQ

RabbitMQ 不是缓存，只能传播“目录发生变化”的消息。仅为一个小型低频目录增加 broker，会同时引入部署、连接恢复、消息积压、重复投递、乱序、死信和可观测性成本。

事件传播也不能取代快照读取：消费者可能离线，消息可能重复，恢复时仍需用 revision 与 Auth 对账。当前 5 分钟 TTL 已经给出明确一致性上界，因此第一阶段不引入 RabbitMQ。

## 未来何时引入事件

满足以下任一条件时再评估：

- 项目已经因多个业务事件统一部署 RabbitMQ，而不是只服务 Scope Catalog。
- Scope 变更必须在明显短于 5 分钟的时间内传播。
- App Center 实例数或读取量使 Auth 快照查询成为实际瓶颈。

届时 RabbitMQ 只用于主动失效/提示刷新：

```text
ScopeCatalogChanged {
  revision: int64
  occurredAt: Instant
}
```

消费者收到比本地更新的 revision 后清除缓存并读取 Auth 快照，不直接把事件 payload 当作长期权威状态。

可靠性最低要求：

- Auth 使用 transactional outbox，在目录修改提交后发布事件。
- durable queue、persistent message、publisher confirms。
- consumer manual acknowledgement，快照刷新成功后再 ack。
- consumer 幂等处理并忽略旧 revision。
- TTL/启动全量同步继续保留，用于修复漏消息和长时间离线。

RabbitMQ 提供的是至少一次投递语义，消费者必须能处理重复消息；不能把它包装成“恰好一次更新”。

## 结果

优点：

- Auth 的事实所有权清晰。
- UC-APP-002 不依赖新的基础设施即可实现。
- 最多 5 分钟缓存时间明确、行为可测试。
- 后续可以无痛增加事件驱动失效，而无需改变 UseCase 的 ScopeCatalog port。

代价：

- 每个 App Center 实例有自己的短期快照。
- Auth 不可用且缓存已过期时，创建版本会暂时失败。
- Scope 紧急撤销仍必须由 Auth 授权路径立即执行，不能依赖 App Center cache。

## 参考

- [RabbitMQ Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ Reliability Guide](https://www.rabbitmq.com/docs/reliability)
