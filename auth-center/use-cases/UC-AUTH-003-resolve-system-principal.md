# UC-AUTH-003：解析 System Principal

状态：`ACCEPTED`

## 目标与范围

> 获得授权的内部服务按稳定 purpose 解析 Auth Center 拥有的不可登录 SYSTEM principal Auth ID，用于记录可审计的系统动作。

首个 purpose 是 `app-center.review-auto-rejection`。本用例不创建普通用户、不授予 reviewer 权限，也不允许调用方指定或修改 authId。

## 主流程

1. 验证内部服务身份、`auth.system-principal.resolve` permission 与 purpose allowlist。
2. 校验 purpose 是当前支持的枚举值。
3. 从 Auth principal repository 读取 `principalType=SYSTEM` 且 purpose 匹配的唯一记录。
4. 返回 opaque authId 与原 purpose。

服务启动在接收流量前对已知 purpose 执行幂等 provision：记录不存在时生成 UUIDv7 Auth ID 并写入；存在时保持原 ID。并发启动不得创建两个相同 purpose 的主体。

## 异常流程

- 身份缺失或无效：`Unauthenticated`。
- RPC permission 或 purpose allowlist 不满足：`PermissionDenied`。
- purpose 未指定或未知：`InvalidSystemPrincipalPurpose`。
- provision 后记录仍不存在：`SystemPrincipalNotFound`。
- 存储不可用或记录损坏：`SystemPrincipalUnavailable`。

## 业务规则

<a id="br-sys-001"></a>
### BR-SYS-001：Auth 所有权与不可登录

SYSTEM principal 由 Auth Center 唯一拥有，不对应自然人、不能登录、没有 Developer 状态，也不由 App Center 配置固定 ID。

<a id="br-sys-002"></a>
### BR-SYS-002：按 purpose 唯一且稳定

每个已知 purpose 在同一环境最多一条 SYSTEM principal。成功 provision 后重启、重复 provision 与重复查询必须返回同一 authId；禁止轮换 ID 来表示状态变化。

<a id="br-sys-003"></a>
### BR-SYS-003：最小授权解析

服务身份认证成功不自动允许解析。调用方同时需要固定 RPC permission 和其注册记录中精确匹配的 purpose；未知 purpose 默认拒绝。

<a id="br-sys-004"></a>
### BR-SYS-004：消费方失败关闭

消费方只能缓存成功且 purpose 匹配的非空 authId。依赖失败不得使用占位符、调用服务身份或人工 reviewer ID 代替 SYSTEM principal。

## 数据模型

在 `auth_principals` 中增加 SYSTEM 专用字段：

| Key | 约束 |
| --- | --- |
| `authId` | 全局唯一 UUIDv7；opaque |
| `principalType` | 固定 `SYSTEM` |
| `developerStatus` | `null` |
| `systemPurpose` | 非空稳定字符串；对 SYSTEM 建 partial unique index |
| `createdAt` / `updatedAt` | UTC；bootstrap 首次创建时写入 |

## API 契约与测试

跨服务 Proto、错误和缓存语义见 [Auth System Principal v1](../../platform/contracts/auth-system-principal-v1.md)。验收至少覆盖：两次 bootstrap 只产生一条记录、重复查询 ID 稳定、普通 USER 不能冒充、未授权 purpose 被拒绝、真实 Mongo/Kratos/provider E2E。

## 变更记录

- 2026-09-22：接受按 purpose provision/resolve 的 SYSTEM principal，移除 App Center 静态 System Auth ID 部署耦合。
