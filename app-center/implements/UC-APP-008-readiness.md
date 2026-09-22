# UC-APP-008 开工检查

检查日期：2026-09-22。

本文是实现准备记录，不定义业务规则，也不改变 UC 的设计状态。

## 结论

[UC-APP-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md) 的 Application、可信开发者身份、UUIDv7、Clock 和事务基础已具备。链接属于 Application，不依赖 UC-APP-007 的 Publication，也不要求先实现 UC-APP-009 的 Membership。

用户已确认由前端扫码解析 joinUrl，再携带当前用户认证凭证调用 App Center 的 UC-APP-009；见 [扫码职责边界](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#前端扫码与加入边界)。入口归属已明确，不再把独立落地页或部署域名作为后端核心实现的阻塞项。领域、用例和持久化基础可开工；URL builder 与前端共享的精确编码仍须在完整接口交付前确定。UC 保持 `PROPOSED`，尚未激活 008 实现。

## 依赖核对

| 依赖 | 证据与结论 |
| --- | --- |
| Application 与当前管理员 | 现有 Application repository 和 adapter-only coordinationRevision 可用于最终事务授权栅栏；不得只在预加载时检查管理员。 |
| DeveloperIdentity | 复用现有 trusted-identity-v1 和 APPROVED 身份投影，不新增 Auth 查询依赖。 |
| Publication / Membership | 按 BR-TST-002、BR-TST-009，不是创建/轮换链接的前置依赖。 |
| UUIDv7 / Clock | 已有 adapter；32-byte 安全随机 secret、原始 bytes 的 SHA-256 和 URL builder 是 008 本身的交付内容。 |
| MongoDB 原子轮换 | 现有开发测试使用 mongo:8.2.12 replica set；下述实验验证 partial unique index 下的撤销与插入可在一个事务内提交。 |
| API / Wire / migration | 现有生成及组装工具可复用；新增链接资源、敏感响应处理和 schema 属于工作包，不要求提前存在。 |
| 链接消费入口 | 已确认由前端扫码解析，带当前用户认证凭证调用 UC-APP-009。joinLinkId 在路径，secret 在正文，authId 来自后端可信认证上下文；无需新增扫码落地接口。精确 URL 编码仍需由 builder 与前端共同约定。 |

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

## 已确认与待细化的入口约定

- **authority**：[UC-APP-008 的扫码职责边界](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#前端扫码与加入边界)、[BR-TST-004](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004)、[BR-TST-008](../use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008)，以及 [UC-APP-009 输入与身份](../use-cases/UC-APP-009-join-application-as-tester.md#输入与身份)。
- **resolved**：前端负责扫码解析和发起已认证的加入请求；App Center 验证链接并创建 Membership。请求正文不接受自行声明的用户身份。独立 Web 落地页及具体部署域名不是后端核心实现的前置条件。
- **remaining gap**：joinUrl 中 joinLinkId/secret 的精确序列化、base URL/deep-link 配置约束，以及前端凭证保护的接入验收尚未定义；现有登录到可信身份的生产链路仍是外部交付事项。
- **options**：URL fragment 携带凭证，或由前端扫描器独立解析约定的 deep-link 载荷。两种方式都必须遵守 BR-TST-004/008，不能以 URL 中的用户信息建立身份。
- **suggested**：沿用可配置 base URL，凭证放在 fragment，前端解析后将 secret 放入 UC-APP-009 请求正文。精确编码属于双方需要共同遵守的契约，应先落文档再实现 URL builder；目前仍是建议，不把用户对扫码流程的确认扩展为对某个编码格式的确认。

## 激活顺序

1. 基于已确认的前端扫码流程，确定 URL builder 与前端共享的编码及配置约束；用户认证复用既有平台契约。
2. 接受 UC-APP-008，建立 brief spec，使用 `tools/gen_brief.py UC-APP-008` 生成 brief。
3. 在代码仓库声明工作包，交付领域、原子轮换、敏感响应、API 与真实存储验证；UC-APP-009 的加入行为继续单独交付。
