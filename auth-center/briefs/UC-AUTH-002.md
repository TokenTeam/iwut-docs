<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-002 --spec tools/brief-specs/UC-AUTH-002.json -->
# Brief — UC-AUTH-002：批量读取 Developer 状态

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-002` 批量读取 Developer 状态 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-DEV-001`–`BR-DEV-005`（5 条） |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/auth-developer-status-v1.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

> 一个获得授权的内部服务，按一组 Auth ID 批量读取 Auth Center 当前权威的
> Developer 状态，用于在高风险业务决定前 fail closed 地检查主体是否已暂停。

本用例是只读查询。首个消费方是 App Center 的 UC-APP-005；它批量读取当前
Application 管理员和审核提交者的状态，然后在任一主体为 `SUSPENDED` 时执行系统
自动拒绝。

本用例不创建用户、不申请或审批 Developer 资格、不修改状态、不签发可信身份
JWS，也不定义 reviewer permissions。

### 调用者与输入

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

### 输出

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

### 主流程

1. 验证调用方内部服务身份和 allowlist 权限。
2. 校验 authIds 数量、长度和唯一性。
3. Repository 用一次批量读取取得全部匹配的 Auth principal。
4. 确认每个请求主体都存在、类型为 `USER`，并具有合法 Developer 状态，或为合法 CLOSED 墓碑。
5. 按请求顺序返回完整结果。

### 异常流程

- authIds 为空、超过上限、包含空值/超长值或重复：`InvalidDeveloperStatusQuery`。
- 任一 Auth ID 不存在、不是 USER principal 或没有 Developer 状态：
  `DeveloperStatusNotFound`，整个查询失败。
- MongoDB 暂不可用、记录损坏或无法完成完整批量读取：
  `DeveloperStatusUnavailable`，不得返回部分结果。
- 缺少或无效服务身份：`Unauthenticated`。
- 服务身份有效但未获读取权限：`PermissionDenied`。
- 未预期内部错误：`Internal`，不得泄露 Auth ID 以外的用户资料、存储查询或堆栈。

### 数据模型

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

### API 契约

跨服务 full method、字段号和错误映射由
[Auth Developer Status v1](../../platform/contracts/auth-developer-status-v1.md) 统一定义。
可执行 Proto 位于独立 API 仓库 `auth_center/v1/developer_status/`。

### 测试与验收

- 输入顺序与输出顺序一致。
- PENDING、APPROVED、REJECTED、SUSPENDED 均能无损返回。
- 空、过量、超长和重复 Auth ID 在 Repository 前失败。
- 任一未知、普通非 Developer USER、SYSTEM 或损坏记录使整个请求失败，不返回部分结果。
- MongoDB 读取失败映射为 `DeveloperStatusUnavailable`。
- Mongo repository 使用一次批量查询，不进行逐 ID N+1 查询。
- Provider E2E 使用真实 MongoDB、Kratos gRPC listener 和生成 client。

### 非目标

- 用户注册、登录、资料管理或删除。
- Developer 资格申请、审批、暂停和恢复命令。
- reviewer permission 的授予或可信身份 JWS 签发。
- System principal 创建、轮换或禁用。
- HTTP、Gateway、gRPC-Web、事件或缓存。

## 业务规则（UC-AUTH-002 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-001 -->
### BR-DEV-001：Developer 状态权威所有权

Auth Center 是 Developer 状态的唯一权威来源。调用方缓存、JWS 中较早签发的
developer_status、测试 fixture 或其它服务数据库不能替代本查询得到的当前状态。

本查询只给出批准门禁所需的当前事实，不替代 Auth 在其它授权路径上的最终决定。

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-002 -->
### BR-DEV-002：有界且唯一的批量输入

单次请求必须包含 `1..100` 个互不重复的 Auth ID。Auth ID 按原始 bytes 精确比较，
不 trim、不折叠大小写。无效输入在访问 Repository 前失败。

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-003 -->
### BR-DEV-003：完整结果与 fail closed

成功响应必须与请求形成一一对应关系并保持请求顺序。任一主体未知、类型不适用、状态
缺失或非法时，整个查询失败；消费方不得把未知或读取失败解释为“未暂停”。

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004 -->
### BR-DEV-004：状态语义

公开 `PENDING/APPROVED/REJECTED/SUSPENDED/WITHDRAWN`。UC-APP-005 只把
`SUSPENDED` 判断为暂停，但 Auth 返回完整枚举，让消费方不需要用 bool 掩盖未知状态。

CLOSED 墓碑作为明确终止状态返回是本规则的例外，不将其伪装成 PENDING 或 WITHDRAWN。

普通 USER 可以不是 Developer，此时 `developerStatus = null`；SYSTEM principal 也不具有
Developer 状态。两者都不能作为本查询的成功结果，且不得被伪装成 `PENDING`。

<!-- 权威位置: use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-005 -->
### BR-DEV-005：内部读取边界

该查询只通过原生 gRPC 向获得明确授权的内部服务开放，不经过终端用户 Gateway，也不
提供 HTTP 或 gRPC-Web。认证成功不自动等于授权成功。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/auth-developer-status-v1.md`：Auth Developer Status v1 跨服务契约

#### 目的与所有权

Auth Center 是 Developer 状态的唯一权威。提供方行为由
[UC-AUTH-002](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md)
及其 `BR-DEV-*` 拥有；本文件只定义跨服务线格式和错误边界。

#### gRPC 方法

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

#### 完整批量语义

- 请求包含 `1..100` 个唯一 Auth ID。
- 成功响应 entries 数量与请求相同，顺序一致，auth_id 逐项相等。
- `DEVELOPER_STATUS_UNSPECIFIED` 仅在 account_status=CLOSED 的合法终止墓碑响应中允许。
- 任一主体未知或状态无法读取时整个 RPC 失败，不返回部分 entries。
- 请求和响应只包含 opaque authId、账号状态与 Developer 状态，不投影用户资料。

#### 调用方身份

调用必须携带 [trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 定义的可验证
内部服务身份。Auth Center 在验签后按固定 full method → `auth.developer-status.read`
映射检查 caller 注册表；测试 server 不能被当作生产无认证入口。

#### 错误边界

| 情况 | gRPC code | 稳定 reason |
| --- | --- | --- |
| 身份缺失或无效 | `UNAUTHENTICATED` | `ERROR_REASON_SERVICE_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_SERVICE_IDENTITY` |
| 身份有效但无读取权限 | `PERMISSION_DENIED` | `ERROR_REASON_DEVELOPER_STATUS_READ_FORBIDDEN` |
| 批量输入非法 | `INVALID_ARGUMENT` | `ERROR_REASON_INVALID_DEVELOPER_STATUS_QUERY` |
| 任一主体未知或不适用 | `NOT_FOUND` | `ERROR_REASON_DEVELOPER_STATUS_NOT_FOUND` |
| 权威状态暂不可读取或记录损坏 | `UNAVAILABLE` | `ERROR_REASON_DEVELOPER_STATUS_UNAVAILABLE` |
| 未预期内部错误 | `INTERNAL` | `ERROR_REASON_INTERNAL` |

错误 message 不得包含 MongoDB 查询、用户资料、服务凭证或堆栈。

#### 契约测试要求

Provider 与 Consumer 至少共同验证：

1. package/service/rpc 的 full method 精确一致。
2. request 只有 `auth_ids = 1`，没有用户或服务身份字段。
3. response 和 enum 字段号保持稳定。
4. entries 与请求一一对应并保持顺序。
5. ACTIVE/DISABLED 的 UNSPECIFIED、未知 account_status、缺项、额外项、重复项或错序均拒绝；CLOSED+UNSPECIFIED 为合法终止结果。
6. INVALID_ARGUMENT、NOT_FOUND、UNAVAILABLE 和稳定 reason 映射一致。
7. App Center 测试 Auth Server 实现同一生成接口，不维护手写 wire model。

#### 兼容性

- v1 可以追加 optional 字段或错误 reason，但不得改变现有字段号、类型、枚举值或 full method。
- 删除字段或枚举时必须 reserve 原 name 与 number。
- 改变完整批量和 fail-closed 语义需要新的平台契约评审。

2026-10-05：治理工作包共同接受 CLOSED 终止投影与 WITHDRAWN 枚举扩展，保持完整批量和失败关闭规则；未上线系统的测试 fixture 同步升级，不接受缺 account_status 的旧响应。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-002`（use-cases/UC-AUTH-002-batch-get-developer-statuses.md）：变更记录

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-002-batch-get-developer-statuses.md` | 156 | `220a639a2f73` |
| `platform/contracts/auth-developer-status-v1.md` | 97 | `65d986d93af1` |
