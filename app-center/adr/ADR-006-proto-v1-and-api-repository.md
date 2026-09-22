# ADR-006：Proto v1 与独立 API 仓库协作

状态：`ACCEPTED`

日期：2026-09-19

## 背景

App Center 的 Proto 源文件由独立 API 仓库管理，服务仓库通过固定 revision 使用生成代码。旧实现与其实验性协议已雪藏，不构成当前系统的数据、API 或行为兼容负担。

当前设计是首个正式版本，使用 `app_center.v1` 作为协议命名空间。Domain 不应由 Proto message 的字段布局驱动。

## 决定

新协议在 API 仓库使用独立命名空间和目录：

```text
app_center/v1/...
package app_center.v1.<capability>
```

`v1` 只表示共享协议命名空间，不进入 App Center 的领域 package、collection 名或业务身份。Schema revision 由 migration ledger 中的 `0001`、`0002` 等迁移 ID 管理，collection 名保持无版本的业务命名。

Proto 源文件继续由独立 API 仓库拥有。App Center 服务仓库固定引用一个明确的 API repository revision；不得依赖浮动分支或在服务仓库手工维护生成代码的私有修改。

协作顺序为：

1. Domain 与 UseCase 通过自己的 Command/Result 类型稳定业务行为。
2. 在 API 仓库增加或修改 v1 Proto、error reason 和生成配置。
3. 生成代码并在 API 仓库通过检查后提交。
4. App Center 更新固定 revision。
5. Transport adapter 显式完成 Proto 与 UseCase 类型转换。
6. 两个仓库分别使用各自可审查的 commit。

Proto 不直接复用 Domain struct，也不把生成 message 传入 Domain。字段 presence、oneof、timestamp、enum unknown value 和 transport validation 在 adapter 边界处理。

## 协议演进

即使系统尚未上线，已提交到共享 API 仓库的 v1 字段编号也保持稳定：

- 不重用删除字段的编号或名称，使用 `reserved`。
- enum 保留明确的 `UNSPECIFIED = 0`，业务上不接受时由 adapter 拒绝。
- 不把数据库内部字段、comparison key、技术计数器或 secret 暴露为公共字段。
- 写请求不接受可信身份、服务端状态和审计字段。
- 分页 cursor 是不透明 bytes/string，不承诺内部编码。
- Error reason 与 [ADR-005](ADR-005-domain-errors-and-transport-mapping.md) 的稳定业务 code 对齐。

HTTP annotation 和 gRPC service 共享同一 Proto 语义。HTTP API 使用 [ADR-005](ADR-005-domain-errors-and-transport-mapping.md) 定义的标准状态映射。

## 子模块与构建

如果服务仓库继续使用 Git submodule：

- submodule pointer 必须指向已经推送且 CI 可获取的 API commit；
- 服务变更不得引用只存在于本地的 API commit；
- CI 验证 submodule 已初始化且工作树干净；
- Proto 生成命令和工具版本应可重复。

未来可以把生成代码改为版本化 Go module，但需要新的 ADR；本决定不在首次实现中同时改变 API 所有权和分发机制。

## 考虑过的替代方案

### 继续使用 app_center.v2

会让尚未发布、不承担兼容负担的首个正式版本看起来像是第二代协议，因此不采用。

### 先从 Proto 生成 Domain

减少 mapper，但 transport presence、兼容性和生成工具会进入业务模型，因此不采用。

### 在服务仓库复制 Proto

会产生两个权威来源，并绕过统一 API 仓库的评审和生成流程，因此不采用。

## 结果

优点：

- v1 schema 直接表达当前首个正式领域契约。
- Domain 与 Proto 独立演进。
- API 所有权和跨服务共享方式清楚。
- 字段编号与错误 code 有明确治理。

代价：

- 一个功能通常需要两个仓库的提交。
- Transport 需要显式 mapper。
- submodule revision 管理和 CI 初始化增加少量流程成本。

## 关联文档

- [ADR-005：领域错误与 Transport 映射](ADR-005-domain-errors-and-transport-mapping.md)
- [统一实现约定](../implements/implementation-conventions.md)
