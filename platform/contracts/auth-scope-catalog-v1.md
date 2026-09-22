# Auth Scope Catalog v1 跨服务契约

状态：`PROPOSED` — 本文件是 Auth Center 提供方与 App Center 等内部消费方共同遵守的跨系统契约。

## 目的与所有权

本契约定义读取 Auth 权威 Scope Catalog 完整快照的线格式和原生 gRPC 边界。业务行为由 [UC-AUTH-001](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md) 及其 `BR-SCP-*` 拥有；本文件不复制 Auth 的内部持久化或目录管理规则。

Auth Center 是提供方，App Center 是首个消费方。可执行 Proto 由独立 API 仓库拥有，目标目录为 `auth_center/v1/scope_catalog/`。

## gRPC 方法

首版只提供内部原生 gRPC：

```text
/auth_center.v1.scope_catalog.ScopeCatalog/GetScopeCatalogSnapshot
```

Proto 结构：

```proto
service ScopeCatalog {
  rpc GetScopeCatalogSnapshot(GetScopeCatalogSnapshotRequest)
      returns (GetScopeCatalogSnapshotResponse);
}

message GetScopeCatalogSnapshotRequest {}

message GetScopeCatalogSnapshotResponse {
  int64 revision = 1;
  google.protobuf.Timestamp generated_at = 2;
  repeated ScopeDefinition scopes = 3;
}

message ScopeDefinition {
  string name = 1;
  bool requestable = 2;
}
```

不声明 `google.api.http` annotation，不经 Gateway 暴露，不提供浏览器或 gRPC-Web 入口。

## 快照语义

- `revision` 必须大于零，并遵循 [BR-SCP-003](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-003)。
- `generated_at` 必须是有效 UTC timestamp，并与 revision 绑定。
- `scopes` 是该 revision 的完整集合；空目录编码为空 repeated field。
- 每个 name 非空且唯一；列表按 name 的 Unicode code point 字典序排列。
- 消费方只把 `requestable = true` 的 name 用于新申请校验；它不是最终授权结果。
- 消费方遇到未知追加字段时必须忽略，以保持向后兼容。

## 调用方身份

调用必须携带可验证的内部服务身份，Auth Center 必须同时完成认证与 allowlist 授权。凭证的线格式尚未确定，记录在 [Auth Center 开放问题](../../auth-center/open-questions.md#内部服务身份)；该问题解决前，本契约不能进入 `ACTIVE`，真实跨服务 E2E 也不能标记完成。

测试 Auth Server 可以通过测试专用 interceptor 注入服务身份，但不得由此产生生产默认凭证或跳过生产校验的代码路径。

## 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_SCOPE_CATALOG_READ_FORBIDDEN` |
| 权威目录暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SCOPE_CATALOG_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含凭证、存储查询、连接地址、Scope 私有元数据或堆栈。调用方不得把失败时持有的过期快照包装成本次成功响应。

## 契约测试要求

Provider 与 Consumer 至少共同验证：

1. gRPC full method 与 package/service/rpc 名称准确。
2. request message 没有业务字段或用户身份字段。
3. response 字段号和类型与本契约一致。
4. 空目录编码为空列表，不是错误或伪造占位 Scope。
5. duplicate/empty name、非正 revision、无效 generatedAt 或非稳定排序不能作为成功快照。
6. `UNAUTHENTICATED`、`PERMISSION_DENIED`、`UNAVAILABLE` 与稳定 reason 映射一致。
7. App Center E2E 的测试 Auth Server 实现同一生成接口，不维护另一份手写 wire model。

## 兼容性

- v1 可以追加 optional 字段或新增错误 reason，但不得改变现有字段号、字段类型或 full method。
- 删除字段时保留其 field number 和 name 为 `reserved`。
- 改变完整快照、revision 或 requestable 的语义需要新的平台契约评审；不能只修改某一方实现。

## 关联文档

- [UC-AUTH-001：获取 Scope Catalog 快照](../../auth-center/use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md)
- [ADR-001：Scope Catalog 权威来源与缓存](../../app-center/adr/ADR-001-scope-catalog-cache.md)
- [UC-APP-002：创建应用版本](../../app-center/use-cases/UC-APP-002-create-application-version.md)
