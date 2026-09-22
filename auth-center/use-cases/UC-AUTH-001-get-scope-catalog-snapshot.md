# UC-AUTH-001：获取 Scope Catalog 快照

状态：`PROPOSED`

## 目标与范围

> 一个获得授权的内部服务读取 Auth Center 当前权威 Scope Catalog 的完整一致快照，并取得可用于缓存、审计和回退检测的 revision。

本用例是只读查询。它不创建、修改、停用或删除 Scope，不定义 consent UI，不签发 OAuth token，也不发布目录变更事件。

## 调用者与输入

调用者是经过平台内部服务身份机制认证且被 Auth Center allowlist 授权的服务。首个消费方是 App Center。

请求没有业务字段：

```text
GetScopeCatalogSnapshotQuery {}
```

内部服务身份不由请求 message 字段表达。具体凭证格式仍是 [开放问题](../open-questions.md#内部服务身份)，因此本 UC 在该决定完成前保持 `PROPOSED`。

## 输出

```text
ScopeCatalogSnapshot {
  revision: int64
  generatedAt: Instant
  scopes: []ScopeDefinition
}

ScopeDefinition {
  name: string
  requestable: bool
}
```

`name` 是 Auth 拥有的稳定、不透明 Scope 标识；消费方只能做精确匹配，不能从命名形式推断权限。`requestable` 只表示当前是否允许新 ApplicationVersion 申请，不代表某个用户已经授权，也不替代 Auth 在 consent/token/数据读取路径上的最终授权。

## 主流程

1. 验证调用方内部服务身份并确认其被允许读取 Scope Catalog。
2. 从 Auth 的权威目录读取一个一致版本的全部 ScopeDefinition。
3. 取得与该版本绑定的 revision 和 generatedAt。
4. 按 Scope name 的 Unicode code point 字典序返回完整快照。

## 异常流程

- 缺少或无效服务身份：`Unauthenticated`。
- 服务身份有效但未获准读取目录：`PermissionDenied`。
- 权威目录暂时不可读取或无法形成一致快照：`ScopeCatalogUnavailable`。
- 未预期内部错误：`Internal`，不得泄露存储结构、凭证或堆栈。

## 业务规则

<a id="br-scp-001"></a>
### BR-SCP-001：Auth 权威所有权

Auth Center 是 Scope Catalog、ScopeDefinition 和 catalog revision 的唯一权威来源。消费方 cache、测试 fixture、配置文件副本或历史快照都不能独立修改或替代该权威目录。

<a id="br-scp-002"></a>
### BR-SCP-002：完整一致快照

一次成功响应必须来自同一个 catalog revision，并包含该 revision 下的全部 ScopeDefinition。响应不得混合两个 revision 的内容，不分页，也不把部分读取包装成成功。

空目录返回空数组，不返回 null。快照中 Scope name 不得重复，并按 Unicode code point 字典序稳定排序。

<a id="br-scp-003"></a>
### BR-SCP-003：单调 revision 与生成时间

revision 是正 int64，在 Auth 内随目录语义变化严格单调增加；消费方不得把它解释为时间戳，也不得要求连续无间隙。相同 revision 必须表示相同的 ScopeDefinition 集合与 requestable 值。

generatedAt 是该 revision 成为权威版本的 UTC 时间。同一 revision 的重复读取必须返回相同 generatedAt。

<a id="br-scp-004"></a>
### BR-SCP-004：ScopeDefinition 投影

首版跨服务投影只包含稳定 `name` 和 `requestable`：

- name 必须非空，在同一快照内唯一，并由 Auth 原样返回。
- requestable 为 true 时，新的 ApplicationVersion 可以申请该 Scope；为 false 时必须被新的申请拒绝。
- requestable 不表达用户 consent、token grant 或实际数据访问授权。
- 其它展示、安全分类或数据投影元数据不在本 UC 中提前定义。

<a id="br-scp-005"></a>
### BR-SCP-005：内部读取边界

该查询只向获得明确授权的内部服务开放，不通过面向终端用户的 Gateway 路由，也不提供 gRPC-Web。认证成功不自动等于授权成功；Auth Center 必须按服务身份 allowlist 做授权判断。

## API 契约

跨服务方法、消息字段、错误映射和契约测试要求由根级 [Auth Scope Catalog v1 契约](../../platform/contracts/auth-scope-catalog-v1.md) 统一定义。可执行 Proto 由独立 API 仓库拥有。

## 测试与验收

- 未认证和未授权调用分别失败，且不读取目录内容。
- 成功响应包含同一 revision 下的完整定义集合。
- 空目录使用空数组；重复 name 或不一致快照不能作为成功返回。
- 返回顺序稳定，与权威存储的物理顺序无关。
- 相同 revision 的内容和 generatedAt 稳定。
- 目录语义变化产生更大的 revision。
- 依赖失败映射为 `ScopeCatalogUnavailable`，不返回部分或旧快照冒充成功。
- Provider 与 Consumer 都针对同一生成 Proto 运行契约测试。

## 非目标

- Scope 的创建、编辑、停用、恢复或删除。
- 管理员界面和审计日志查询。
- 增量同步、分页、ETag、长轮询、消息队列或推送失效。
- OAuth consent、token issuance 和用户数据字段投影。
- 重构旧 Auth Center 的其它能力。

## 变更记录

- 2026-09-21：建立 Auth Center 第一个纵切片，定义完整 Scope Catalog 快照、单调 revision 和内部读取边界。
