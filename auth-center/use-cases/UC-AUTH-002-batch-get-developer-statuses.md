# UC-AUTH-002：批量读取 Developer 状态

状态：`ACCEPTED`

## 目标与范围

> 一个获得授权的内部服务，按一组 Auth ID 批量读取 Auth Center 当前权威的
> Developer 状态，用于在高风险业务决定前 fail closed 地检查主体是否已暂停。

本用例是只读查询。首个消费方是 App Center 的 UC-APP-005；它批量读取当前
Application 管理员和审核提交者的状态，然后在任一主体为 `SUSPENDED` 时执行系统
自动拒绝。

本用例不创建用户、不申请或审批 Developer 资格、不修改状态、不签发可信身份
JWS，也不定义 reviewer permissions。

## 调用者与输入

调用者必须通过平台内部服务身份认证，并被 Auth Center allowlist 明确授权读取
Developer 状态。

```text
BatchGetDeveloperStatusesQuery {
  authIds: []AuthId
}
```

- authIds 数量必须为 `1..100`。
- 每个 Auth ID 是 1–200 UTF-8 bytes 的非空 opaque 值；Auth 不对其大小写、空白或
  其它字符做规范化。
- 同一请求不能包含重复 Auth ID。
- 内部服务身份不进入请求 message。

## 输出

```text
BatchDeveloperStatuses {
  entries: []DeveloperStatusEntry
}

DeveloperStatusEntry {
  authId: AuthId
  accountStatus: ACTIVE | DISABLED | CLOSED
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED | WITHDRAWN | null // null 仅 CLOSED
}
```

成功响应为每个请求 Auth ID 返回且只返回一条记录，顺序与请求一致。不得追加未请求
主体，也不得省略未知或损坏记录后返回部分成功。

WITHDRAWN 为已退出，不是暂停或普通用户；历史提交者可返回该状态。响应增加 accountStatus=ACTIVE/DISABLED/CLOSED；CLOSED 的合法 USER 墓碑可成功返回，developerStatus 在此唯一例外为 null/线格式 UNSPECIFIED，不恢复旧资格。ACTIVE/DISABLED 普通非 Developer 仍 NOT_FOUND。App 角色区分规则由 [App 退出协调用例的状态消费规则](../../app-center/use-cases/UC-APP-025-coordinate-account-owner-exit.md#br-app-011) 定义。

## 主流程

1. 验证调用方内部服务身份和 allowlist 权限。
2. 校验 authIds 数量、长度和唯一性。
3. Repository 用一次批量读取取得全部匹配的 Auth principal。
4. 确认每个请求主体都存在、类型为 `USER`，并具有合法 Developer 状态，或为合法 CLOSED 墓碑。
5. 按请求顺序返回完整结果。

## 异常流程

- authIds 为空、超过上限、包含空值/超长值或重复：`InvalidDeveloperStatusQuery`。
- 任一 Auth ID 不存在、不是 USER principal 或没有 Developer 状态：
  `DeveloperStatusNotFound`，整个查询失败。
- MongoDB 暂不可用、记录损坏或无法完成完整批量读取：
  `DeveloperStatusUnavailable`，不得返回部分结果。
- 缺少或无效服务身份：`Unauthenticated`。
- 服务身份有效但未获读取权限：`PermissionDenied`。
- 未预期内部错误：`Internal`，不得泄露 Auth ID 以外的用户资料、存储查询或堆栈。

## 业务规则

<a id="br-dev-001"></a>
### BR-DEV-001：Developer 状态权威所有权

Auth Center 是 Developer 状态的唯一权威来源。调用方缓存、JWS 中较早签发的
developer_status、测试 fixture 或其它服务数据库不能替代本查询得到的当前状态。

本查询只给出批准门禁所需的当前事实，不替代 Auth 在其它授权路径上的最终决定。

<a id="br-dev-002"></a>
### BR-DEV-002：有界且唯一的批量输入

单次请求必须包含 `1..100` 个互不重复的 Auth ID。Auth ID 按原始 bytes 精确比较，
不 trim、不折叠大小写。无效输入在访问 Repository 前失败。

<a id="br-dev-003"></a>
### BR-DEV-003：完整结果与 fail closed

成功响应必须与请求形成一一对应关系并保持请求顺序。任一主体未知、类型不适用、状态
缺失或非法时，整个查询失败；消费方不得把未知或读取失败解释为“未暂停”。

<a id="br-dev-004"></a>
### BR-DEV-004：状态语义

公开 `PENDING/APPROVED/REJECTED/SUSPENDED/WITHDRAWN`。UC-APP-005 只把
`SUSPENDED` 判断为暂停，但 Auth 返回完整枚举，让消费方不需要用 bool 掩盖未知状态。

CLOSED 墓碑作为明确终止状态返回是本规则的例外，不将其伪装成 PENDING 或 WITHDRAWN。

普通 USER 可以不是 Developer，此时 `developerStatus = null`；SYSTEM principal 也不具有
Developer 状态。两者都不能作为本查询的成功结果，且不得被伪装成 `PENDING`。

<a id="br-dev-005"></a>
### BR-DEV-005：内部读取边界

该查询只通过原生 gRPC 向获得明确授权的内部服务开放，不经过终端用户 Gateway，也不
提供 HTTP 或 gRPC-Web。认证成功不自动等于授权成功。

## 数据模型

Auth Center 使用 `auth_principals` collection 保存最小主体事实：

| Key | type | 约束 |
| --- | --- | --- |
| `authId` | string | 全局唯一；1–200 UTF-8 bytes；opaque |
| `principalType` | string enum | `USER` 或 `SYSTEM` |
| `developerStatus` | string enum / null | 普通 USER 可以为 null；进入 Developer 生命周期的 USER 必须为四种合法状态；SYSTEM 必须为 null |
| `createdAt` | datetime | UTC；创建后不可修改 |
| `updatedAt` | datetime | UTC；状态变化时更新 |

`authId` 建立唯一索引。本 UC 只读取这些字段；主体创建、System principal provision、
Developer 状态迁移和审计由后续 Auth UC 定义。

## API 契约

跨服务 full method、字段号和错误映射由
[Auth Developer Status v1](../../platform/contracts/auth-developer-status-v1.md) 统一定义。
可执行 Proto 位于独立 API 仓库 `auth_center/v1/developer_status/`。

## 测试与验收

- 输入顺序与输出顺序一致。
- PENDING、APPROVED、REJECTED、SUSPENDED 均能无损返回。
- 空、过量、超长和重复 Auth ID 在 Repository 前失败。
- 任一未知、普通非 Developer USER、SYSTEM 或损坏记录使整个请求失败，不返回部分结果。
- MongoDB 读取失败映射为 `DeveloperStatusUnavailable`。
- Mongo repository 使用一次批量查询，不进行逐 ID N+1 查询。
- Provider E2E 使用真实 MongoDB、Kratos gRPC listener 和生成 client。

## 非目标

- 用户注册、登录、资料管理或删除。
- Developer 资格申请、审批、暂停和恢复命令。
- reviewer permission 的授予或可信身份 JWS 签发。
- System principal 创建、轮换或禁用。
- HTTP、Gateway、gRPC-Web、事件或缓存。

## 变更记录

- 2026-09-21：建立批量 Developer 状态读取，为 UC-APP-005 暂停门禁提供
  fail-closed 的 Auth 权威查询。
- 2026-09-22：确认 Developer 是 USER 的可选属性；普通用户的 `developerStatus` 为 null，
  Developer Status 查询对其返回 NotFound。
- 2026-09-22：内部服务身份与固定 allowlist 契约闭合，设计进入 `ACCEPTED`。
