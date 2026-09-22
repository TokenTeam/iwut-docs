# Auth System Principal v1 跨服务契约

状态：`ACTIVE`

## 目的与所有权

Auth Center 拥有不可登录的 SYSTEM principal 及其 opaque Auth ID。消费方只按稳定 purpose 解析 ID，不创建、猜测或通过部署配置复制它。提供方业务语义由 [UC-AUTH-003](../../auth-center/use-cases/UC-AUTH-003-resolve-system-principal.md) 拥有。

## gRPC 方法

```text
/auth_center.v1.system_principal.SystemPrincipalDirectory/ResolveSystemPrincipal
```

```proto
service SystemPrincipalDirectory {
  rpc ResolveSystemPrincipal(ResolveSystemPrincipalRequest)
      returns (ResolveSystemPrincipalResponse);
}

enum SystemPrincipalPurpose {
  SYSTEM_PRINCIPAL_PURPOSE_UNSPECIFIED = 0;
  SYSTEM_PRINCIPAL_PURPOSE_APP_CENTER_REVIEW_AUTO_REJECTION = 1;
}

message ResolveSystemPrincipalRequest {
  SystemPrincipalPurpose purpose = 1;
}

message ResolveSystemPrincipalResponse {
  string auth_id = 1;
  SystemPrincipalPurpose purpose = 2;
}
```

只提供内部原生 gRPC，不声明 HTTP annotation，不经 Gateway，不提供 gRPC-Web。

## 调用与缓存语义

- 调用使用 [trusted-service-identity-v1](trusted-service-identity-v1.md)，同时要求 `auth.system-principal.resolve` permission 与 caller 的 purpose allowlist。
- Auth 启动时幂等 provision 已知 purpose；同一 purpose 在同一环境中映射到唯一、稳定、非空 authId。
- App Center 不以该 ID 作为启动依赖。首次需要自动审核决定时查询；成功结果可缓存到进程结束。
- 查询失败或返回不匹配 purpose/空 ID 时不得缓存，当前决定 fail closed；后续请求可重试。

## 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 服务身份缺失/无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 无 RPC 或 purpose 权限 | `PERMISSION_DENIED` | `ERROR_REASON_SYSTEM_PRINCIPAL_READ_FORBIDDEN` |
| purpose 未指定/未知 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_SYSTEM_PRINCIPAL_PURPOSE` |
| principal 不存在 | `NOT_FOUND` | `ERROR_REASON_SYSTEM_PRINCIPAL_NOT_FOUND` |
| 存储暂不可用 | `UNAVAILABLE` | `ERROR_REASON_SYSTEM_PRINCIPAL_UNAVAILABLE` |

## 契约测试要求

Provider/consumer 必须验证 full method、字段号、purpose 枚举、稳定 ID、身份与 purpose allowlist、失败不缓存，以及 App 自动拒绝最终写入 Auth 返回的 SYSTEM authId。
