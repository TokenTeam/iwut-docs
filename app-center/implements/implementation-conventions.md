# App Center 统一实现约定

状态：`ACTIVE`

## 适用范围

本文约束 App Center 新实现中的代码组织、依赖、错误、持久化、测试和提交。业务规则不在本文重复定义；业务行为始终引用 `UC-*` 与 `BR-*` 权威正文。

## 基本原则

- 先实现当前工作包，不为尚未出现的用例预留抽象。
- 领域模型表达业务语言，不表达 MongoDB、Proto、HTTP 或框架形状。
- 外部系统和不稳定选择通过小型 port 隔离。
- 优先编写能证明 BR 的测试，再补齐最小实现。
- 不维护尚未对外发布的兼容性。

## 代码组织

目录遵循 [ADR-003](../adr/ADR-003-go-package-and-dependency-boundaries.md)，按业务能力组织：

```text
cmd/app-center/                   composition root
internal/shared/                 跨能力稳定值类型和最小 ports
internal/application/domain/     Application 与 Quota 领域模型
internal/application/usecase/    Application commands/queries
internal/application/port/       当前能力需要的外部接口
internal/version/...
internal/profile/...
internal/publication/...
internal/tester/...
internal/catalog/...
internal/adapter/mongo/          MongoDB adapters
internal/adapter/auth/           Auth adapters
internal/adapter/transport/      HTTP/gRPC/Proto adapters
```

代码目录只按当前业务职责命名，不使用迁移阶段或实现世代作为目录名。

一个 package 应围绕单一业务职责命名。禁止重新建立包含所有实体的通用 `biz`、所有持久化的通用 `data` 或无限增长的 `util` package。

代码仓库根目录的 `architecture_test.go` 是测试期治理文件，不是业务 package。它按照 ADR-003 自动验证上述目录与依赖方向；新增结构或依赖方向时必须同步修改 ADR 和测试。

## 依赖方向

允许的主要依赖方向：

```text
transport adapter -> usecase -> domain
mongo/auth adapter -> capability port + domain value types
composition root -> all concrete providers
```

Domain：

- 不导入 Kratos、MongoDB driver、Proto 生成包、HTTP 包或配置包。
- 默认只使用标准库；Unicode 规范化等确定性值对象需求可以使用经过明确引入的窄依赖。
- Domain、UseCase、Port 与 `internal/shared` 当前由 architecture test 禁止直接新增第三方依赖；引入上述窄依赖前必须先更新并接受相应 ADR，再显式修改测试允许项。
- 不读取环境变量、系统时钟、随机数或全局单例。
- 不带 `bson`、`json`、`protobuf` 等基础设施 tag。

UseCase：

- 协调领域对象和 ports。
- 不解析 JWT、HTTP header、Proto presence 或 MongoDB error。
- 不依赖具体 adapter。
- 不把业务规则降级为 Repository 内的隐式行为。

Adapter：

- 负责外部类型转换、协议校验和技术错误映射。
- 不产生新的业务决定。
- 不把 MongoDB document 或 Proto message 直接返回给 Domain。

## 配置

- 环境变量只在 config/composition boundary 读取一次；Domain、UseCase 与具体 adapter 不直接调用 `os.Getenv` 或等价全局读取。
- 配置加载负责格式、范围与必填关系校验。变量未设置时可以使用文档声明的默认值；变量显式存在但非法时必须阻止进程组装，不得静默回退。
- 经过校验的标量配置通过构造参数注入消费方，不能把通用配置对象传入 Domain。
- 改变“初始值”配置只影响之后新建的持久化记录，除非对应 UC 明确授权修改已有业务事实。
- 当前变量为 `APP_CENTER_INITIAL_APPLICATION_QUOTA`（默认 `10`）和 `APP_CENTER_SCOPE_CATALOG_CACHE_TTL`（默认 `5m`）。新增变量时必须同步更新其所属 UC/ADR 与测试。

## 类型与命名

- 使用类型化 ID，禁止在领域接口中用一个裸 `string` 同时表示多种实体身份。
- `AuthID` 是不透明值，不解释学校身份、学号或用户类型。
- 系统时间通过 `Clock` port 获取，领域审计时间统一为 UTC `time.Time`。
- UUIDv7 通过 `IDGenerator` port 产生；测试不得依赖真实随机值。
- Command 使用动词开头；Query 使用 `Get/List/Resolve` 等读取动词。
- Repository port 以业务原子行为命名，避免先建立通用 CRUD。
- bool 字段使用能直接读出真假含义的名称，避免 `flag`、`statusBool` 等模糊命名。
- 缩写在同一标识符中保持一致，例如 `ID`、`URL`、`RPC`。

## 值对象与校验

- 字段规范化与校验由领域值对象完成；transport validation 只能提前拒绝明显的形状错误，不能成为唯一业务校验。
- 保存和比较使用规范化后的值，原值是否保留由对应 BR 决定。
- Unicode 长度按对应 BR 指定的 code point 语义计算，不能误用字节长度。
- 大小写不敏感唯一性使用显式 comparison key，不依赖数据库默认 collation。
- 无效值在构造边界被拒绝；禁止让“半合法”领域对象在系统中流动。

## 身份与权限

- Transport/Auth adapter 把可信外部身份转换成当前用例需要的最小 Identity。
- UseCase 不从请求正文接受 authId、developerStatus、permissions 或 SysAdmin 标记。
- 最终写入前需要重新确认的权限和所有权必须与写入处于 BR 指定的同一原子边界。
- 缺少外部身份契约时先定义 port 和 fake，不能临时读取未经设计的 claim 字段。

## 错误

- Domain 和 UseCase 使用 [ADR-005](../adr/ADR-005-domain-errors-and-transport-mapping.md) 定义的稳定错误分类。
- 预期业务错误必须可用 `errors.Is` 或等价的类型判断稳定识别。
- 错误文本用于诊断，不作为客户端分支条件。
- 基础设施错误必须保留 cause 供日志和追踪使用，但不能把数据库、网络或密钥信息暴露给客户端。
- Transport 在一个集中位置完成领域错误到 gRPC/HTTP/Proto reason 的映射。
- 不允许用 `panic` 表达可预期的业务失败。

## 持久化与事务

- MongoDB document 与领域实体使用显式 mapper，相互转换时重新验证不变量。
- collection 名、字段名、索引和 validator 属于 adapter/schema 层，不进入 Domain。
- 跨文档业务不变量遵循 [ADR-004](../adr/ADR-004-mongodb-transactions-and-schema-management.md)。
- 每个事务只包含本地持久化，不在事务内调用 Auth、HTTP、消息系统或其他远程服务。
- 事务重试必须重放整个业务原子操作；不能只重试其中一次写入。
- 唯一索引和条件写入是业务并发保护的一部分，不能只依赖进程内锁。
- Redis、缓存和读投影不是权威写模型，除非未来 ADR 明确改变这一点。
- schema/index 变更通过显式、可重复执行的迁移完成，不在普通服务启动时静默修改生产 schema。

## API 与生成代码

- Proto 协作遵循 [ADR-006](../adr/ADR-006-proto-v1-and-api-repository.md)；首个正式命名空间为 `app_center.v1`。
- Proto message 不是领域对象；transport 必须显式映射。
- API 不暴露内部 sequence、comparison key、配额计数器或持久化 revision，除非 Query/UC 明确要求。
- 请求不能覆盖服务端生成的 ID、可信身份、状态或审计字段。
- 生成文件不得手工修改；源 Proto 与生成命令必须能重现结果。
- API 尚未形成兼容承诺前仍要保持字段编号稳定；删除字段时保留 `reserved`。

## 日志与敏感信息

- 日志记录稳定实体 ID、操作名、结果类别和 trace ID，不记录完整请求对象。
- Tester secret、JWT、authorization header、client credential 和用户任意 KV 数据不得进入日志。
- 预期业务拒绝使用适当的低噪声级别；基础设施失败记录 cause 和上下文。
- Domain 不直接写日志；由 UseCase 边界或 Adapter 记录一次有意义的结果。

## 测试

测试分为三层：

1. Domain/UseCase 单元测试：使用 fake ports，覆盖字段边界、状态、不变量、权限和 no-op。
2. Adapter 集成测试：使用真实依赖，覆盖索引、validator、事务、错误映射和并发竞争。
3. Transport 契约测试：覆盖身份提取、请求映射、错误映射和响应字段。

此外，根目录 architecture test 对所有层执行结构和导入边界检查，并包含规则自身的正反例测试。该检查随 `go test ./...` 运行，不得通过 build tag、测试跳过或独立命令使其脱离最低验证流程。

要求：

- 测试名称或 table case 标明关联的 BR ID。
- 时间、ID 和外部返回值通过 fake 控制，测试必须可重复。
- 并发不变量不能只用顺序单元测试证明，必须有真实存储上的竞争测试。
- 不用 sleep 猜测并发顺序；使用 barrier、channel 或数据库事务协调。
- 修复缺陷时先增加能重现问题的测试。
- `go test ./...` 是最低验证要求；涉及竞态的纯 Go 代码增加 `go test -race ./...`。
- MongoDB 集成测试应明确标记并提供可重复启动的支持事务环境。

## 格式化与生成

- Go 代码提交前运行 `gofmt`。
- `go.mod` 与 `go.sum` 由 Go 工具维护，不手工排列。
- 生成代码、迁移和 schema 文件必须与其源文件在同一变更中提交。
- 不提交二进制、临时数据库、编辑器状态、密钥或本地环境配置。

## Commit message

每个 commit message 的标题必须使用以下格式：

```text
:emoji: type: commit title
```

其中 `:emoji:` 使用可读的 gitmoji shortcode，`type` 使用下列之一：

```text
feat
fix
docs
test
refactor
perf
build
ci
chore
revert
```

示例：

```text
:sparkles: feat: implement application name value object
:white_check_mark: test: cover application quota concurrency
:memo: docs: define mongodb transaction boundary
```

标题使用英文、祈使式、简洁描述实际变化，不以句号结尾。一个 commit 只承担一个可审查目的；生成代码与触发生成的源文件放在同一个 commit 中。

推荐校验正则：

```text
^:[a-z0-9_+\-]+: (feat|fix|docs|test|refactor|perf|build|ci|chore|revert): .+$
```

## 文档与实现同步

- 实现发现 BR 无法满足或相互冲突时，先修正文档再改变代码语义。
- 纯实现选择不新增 BR；达到 ADR 门槛的跨模块、难以回退决定应新增 ADR。
- 设计文档独立保存，代码仓库只通过 AGENTS.md 指向权威位置，不复制正文。
- UC 从 `PROPOSED` 进入 `ACCEPTED` 前，应完成必要设计评审；实现覆盖使用 `NOT_STARTED/IN_PROGRESS/CORE_COMPLETE/COMPLETE` 独立记录，不以设计状态暗示交付完成度。
