# UC-APP-008 开工检查

检查日期：2026-09-22。

本文是实现准备记录，不定义业务规则，也不改变 UC 的设计状态。

## 结论

[UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) 的 Application、可信开发者身份、UUIDv7、Clock 和事务基础已具备。链接属于 Application，不依赖 UC-APP-007 的 Publication，也不要求先实现 UC-APP-009 的 Membership。

可以着手领域、用例和持久化实现准备；完整工作包尚不能直接激活：正式 join URL / deep-link 的入口归属、编码格式及入口凭证保护尚无契约。UC 保持 `PROPOSED`，本次未生成 brief 或开始 008 实现。

## 依赖核对

| 依赖 | 证据与结论 |
| --- | --- |
| Application 与当前管理员 | 现有 Application repository 和 adapter-only coordinationRevision 可用于最终事务授权栅栏；不得只在预加载时检查管理员。 |
| DeveloperIdentity | 复用现有 trusted-identity-v1 和 APPROVED 身份投影，不新增 Auth 查询依赖。 |
| Publication / Membership | 按 BR-TST-002、BR-TST-009，不是创建/轮换链接的前置依赖。 |
| UUIDv7 / Clock | 已有 adapter；32-byte 安全随机 secret、原始 bytes 的 SHA-256 和 URL builder 是 008 本身的交付内容。 |
| MongoDB 原子轮换 | 现有开发测试使用 mongo:8.2.12 replica set；下述实验验证 partial unique index 下的撤销与插入可在一个事务内提交。 |
| API / Wire / migration | 现有生成及组装工具可复用；新增链接资源、敏感响应处理和 schema 属于工作包，不要求提前存在。 |
| 链接消费入口 | UC-APP-009 只规定接收 joinLinkId 和请求正文中的 secret，未决定 joinUrl 如何编码和落地。平台契约中未找到对应约定。 |

## MongoDB 可行性实验

使用独立的一次性 mongo:8.2.12 单成员 replica set，创建唯一部分索引：

```javascript
links.createIndex(
  { applicationId: 1 },
  { unique: true, partialFilterExpression: { status: "ACTIVE" } }
);
```

预先插入一条 ACTIVE 旧链接；在同一 session transaction 中，先把旧记录改为 REVOKED，再为相同 applicationId 插入新的 ACTIVE 记录，然后提交。

实际结果：事务成功，旧记录为 REVOKED，新记录为 ACTIVE。实验资源已清理。该结果只证明当前 MongoDB 版本下基础轮换可行；正式实现仍须覆盖 BR-TST-006/007 要求的并发首次创建、并发轮换、管理员转让、失败回滚，以及 validator/不可变字段测试，不能用此实验代替验收。

## 待定入口契约

- **authority**：[UC-APP-008 的“实现前需要确认”](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#实现前需要确认)、[BR-TST-004](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004)、[BR-TST-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008)，以及 [UC-APP-009 的“实现前需要确认”](../use-cases/UC-APP-009-join-application-as-tester.md#实现前需要确认)。
- **conflict / gap**：当前仅有示例 joinUrl 和 URL builder port，缺少正式入口所属客户端/服务、HTTPS base URL 或 deep-link scheme、joinLinkId/secret 编码位置、落地后如何提交加入命令及入口日志策略。现有 Traefik 配置启用了 access log，未发现针对 tester 凭证的路径/查询串处理约定；这不证明实际泄露，但不能据此认定链路已满足 BR-TST-008。
- **options**：由官方 Web 落地页承接 HTTPS 链接，或由官方客户端承接 app deep link；两者都需要明确 URL builder 与消费方共同遵守的格式和凭证保护责任。
- **suggested**：优先定义可配置的官方 HTTPS 落地页；将 secret 放在 URL fragment，由页面读取后放入 UC-APP-009 请求正文，避免把 secret 放进服务端请求路径或 query；页面不接入第三方统计并及时清理地址栏中的凭证。此项仅为待评审建议，不是已接受的跨系统契约。部署域名可以作为配置，格式和消费方职责必须先明确。

## 激活顺序

1. 确定上述入口契约，并在适当的客户端/平台文档中保存权威定义；UC 只引用，不复制。
2. 接受 UC-APP-008，建立 brief spec，使用 `tools/gen_brief.py UC-APP-008` 生成 brief。
3. 在代码仓库声明工作包，交付领域、原子轮换、敏感响应、API 与真实存储验证；UC-APP-009 的加入行为继续单独交付。
