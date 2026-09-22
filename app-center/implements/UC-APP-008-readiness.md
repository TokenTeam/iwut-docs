# UC-APP-008 开工检查

检查日期：2026-09-22。

本文是实现准备记录，不定义业务规则，也不改变 UC 的设计状态。

## 结论

[UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) 的 Application、可信开发者身份、UUIDv7、Clock 和事务基础已具备。链接属于 Application，不依赖 UC-APP-007 的 Publication，也不要求先实现 UC-APP-009 的 Membership。

用户已确认由前端扫码解析，并允许使用带完整凭证的 mock URL，前缀通过环境变量配置。入口格式与配置已分别落入 [Tester 加入 URL v1](../../platform/contracts/tester-join-url-v1.md) 和 [UC 配置章节](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#配置与临时入口)。此前的 URL 入口阻塞已解除。

UC 已进入 `ACCEPTED`，brief 已由脚本生成，代码仓库已激活 008 工作包。真实前端扫码、生产入口域名和 UC-APP-009 加入行为不属于本工作包。

## 依赖核对

| 依赖 | 证据与结论 |
| --- | --- |
| Application 与当前管理员 | 现有 Application repository 和 adapter-only coordinationRevision 可用于最终事务授权栅栏；不得只在预加载时检查管理员。 |
| DeveloperIdentity | 复用现有 trusted-identity-v1 和 APPROVED 身份投影，不新增 Auth 查询依赖。 |
| Publication / Membership | 按 BR-TST-002、BR-TST-009，不是创建/轮换链接的前置依赖。 |
| UUIDv7 / Clock | 已有 adapter；32-byte 安全随机 secret、原始 bytes 的 SHA-256 和 URL builder 是 008 本身的交付内容。 |
| MongoDB 原子轮换 | 现有开发测试使用 mongo:8.2.12 replica set；下述实验验证 partial unique index 下的撤销与插入可在一个事务内提交。 |
| API / Wire / migration | 现有生成及组装工具可复用；新增链接资源、敏感响应处理和 schema 属于工作包，不要求提前存在。 |
| 链接消费入口 | 已确认由前端扫码解析，带当前用户认证凭证调用 UC-APP-009。joinLinkId 在路径，secret 在正文，authId 来自后端可信认证上下文；无需新增扫码落地接口。精确 URL 编码已由共享契约确定。 |

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

## 已闭合的入口约定

- **authority**：[UC 配置与临时入口](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#配置与临时入口)、[Tester 加入 URL v1](../../platform/contracts/tester-join-url-v1.md)。
- **resolved**：前端负责扫码；mock URL 无需页面真实存在；env 可配置前缀；fragment 携带 joinLinkId 和 secret。扫码后的用户身份仍由既有认证链路提供。
- **implementation boundary**：真实安全随机 secret、哈希存储、当前管理员授权、原子轮换、敏感响应、配置和 URL 编码均在本次交付；前端页面、扫码组件、真实域名和 UC-APP-009 不在范围内。

## 激活记录

1. 用户接受 mock URL 及环境变量前缀，UC-APP-008 已设为 `ACCEPTED`。
2. 新增 `tools/brief-specs/UC-APP-008.json`，以 `python3 -B tools/gen_brief.py UC-APP-008` 生成 [brief](../briefs/UC-APP-008.md)。
3. 代码仓库 `AGENTS.md` 已切换工作包，已由 subagent 完成实现并通过完整验证；当前工作包登记为 COMPLETE，具体覆盖和验证结果见 [实现入口](README.md)。
