# Auth Developer Status v1 跨服务契约

状态：`ACTIVE` — 本文件是 Auth Center 提供方与 App Center 等内部消费方共同遵守的
原生 gRPC 契约。

## 目的与所有权

Auth Center 是 Developer 状态的唯一权威。提供方行为由
[UC-AUTH-002](../../auth-center/use-cases/UC-AUTH-002-batch-get-developer-statuses.md)
及其 `BR-DEV-*` 拥有；本文件只定义跨服务线格式和错误边界。

## gRPC 方法

```text
/auth_center.v1.developer_status.DeveloperStatusDirectory/BatchGetDeveloperStatuses
```

```proto
service DeveloperStatusDirectory {
  rpc BatchGetDeveloperStatuses(BatchGetDeveloperStatusesRequest)
      returns (BatchGetDeveloperStatusesResponse);
}

message BatchGetDeveloperStatusesRequest {
  repeated string auth_ids = 1;
}

message BatchGetDeveloperStatusesResponse {
  repeated DeveloperStatusEntry entries = 1;
}

message DeveloperStatusEntry {
  string auth_id = 1;
  DeveloperStatus developer_status = 2;
  AccountStatus account_status = 3;
}

enum DeveloperStatus {
  DEVELOPER_STATUS_UNSPECIFIED = 0;
  DEVELOPER_STATUS_PENDING = 1;
  DEVELOPER_STATUS_APPROVED = 2;
  DEVELOPER_STATUS_REJECTED = 3;
  DEVELOPER_STATUS_SUSPENDED = 4;
  DEVELOPER_STATUS_WITHDRAWN = 5;
}
```

AccountStatus 固定 0=UNSPECIFIED（成功非法）,1=ACTIVE,2=DISABLED,3=CLOSED。CLOSED 是合法 USER 墓碑，仅此状态下 developer_status 必须 UNSPECIFIED；ACTIVE/DISABLED 仍要求明确 Developer 枚举，普通 null Developer 保持 NOT_FOUND。

该方法没有 `google.api.http` annotation，不经 Gateway 暴露，也不提供 gRPC-Web。

## 完整批量语义

- 请求包含 `1..100` 个唯一 Auth ID。
- 成功响应 entries 数量与请求相同，顺序一致，auth_id 逐项相等。
- `DEVELOPER_STATUS_UNSPECIFIED` 仅在 account_status=CLOSED 的合法终止墓碑响应中允许。
- 任一主体未知或状态无法读取时整个 RPC 失败，不返回部分 entries。
- 请求和响应只包含 opaque authId、账号状态与 Developer 状态，不投影用户资料。

## 调用方身份

调用必须携带 [trusted-service-identity-v1](trusted-service-identity-v1.md) 定义的可验证
内部服务身份。Auth Center 在验签后按固定 full method → `auth.developer-status.read`
映射检查 caller 注册表；测试 server 不能被当作生产无认证入口。

## 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_DEVELOPER_STATUS_READ_FORBIDDEN` |
| 批量输入非法 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_DEVELOPER_STATUS_QUERY` |
| 任一主体未知或不适用 | `NOT_FOUND` | `ERROR_REASON_DEVELOPER_STATUS_NOT_FOUND` |
| 权威状态暂不可读取或记录损坏 | `UNAVAILABLE` | `ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含 MongoDB 查询、用户资料、服务凭证或堆栈。

## 契约测试要求

Provider 与 Consumer 至少共同验证：

1. package/service/rpc 的 full method 精确一致。
2. request 只有 `auth_ids = 1`，没有用户或服务身份字段。
3. response 和 enum 字段号保持稳定。
4. entries 与请求一一对应并保持顺序。
5. ACTIVE/DISABLED 的 UNSPECIFIED、未知 account_status、缺项、额外项、重复项或错序均拒绝；CLOSED+UNSPECIFIED 为合法终止结果。
6. INVALID_ARGUMENT、NOT_FOUND、UNAVAILABLE 和稳定 reason 映射一致。
7. App Center 测试 Auth Server 实现同一生成接口，不维护手写 wire model。

## 兼容性

- v1 可以追加 optional 字段或错误 reason，但不得改变现有字段号、类型、枚举值或 full method。
- 删除字段或枚举时必须 reserve 原 name 与 number。
- 改变完整批量和 fail-closed 语义需要新的平台契约评审。

2026-10-05：治理工作包共同接受 CLOSED 终止投影与 WITHDRAWN 枚举扩展，保持完整批量和失败关闭规则；未上线系统的测试 fixture 同步升级，不接受缺 account_status 的旧响应。
