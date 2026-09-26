# Developer 自助申请协议 v1

状态：`ACCEPTED`

## 范围与兼容性

本契约固定 [UC013](../../auth-center/use-cases/UC-AUTH-013-apply-for-developer.md) 在客户端、Gateway 与 Auth 之间的格式。资格前置条件、迁移、审计和部署就绪含义由 UC013 拥有；不改变 UC002 内部批量查询或既有 JWS claims。

## RPC 与认证载体

API 目录 `auth_center/v1/developer_application/`；package `auth_center.v1.developer_application`；service `DeveloperApplicationService`；Go package `github.com/TokenTeam/iwut-api-proto/gen/go/auth_center/v1/developer_application;developer_application`。

| full method | 认证 |
| --- | --- |
| `/auth_center.v1.developer_application.DeveloperApplicationService/ApplyForDeveloper` | 必需有效 USER Session，只申请本人 |
| `/auth_center.v1.developer_application.DeveloperApplicationService/GetOwnDeveloperEligibility` | 必需有效 USER Session，只查询本人 |

两者使用 [设备协议的 Session 载体](auth-device-session-v1.md#session-载体)：恰好一个规范 `x-iwut-session` 值。缺失、空值、多值或非规范编码返回 SESSION_INVALID；Authorization、cookie、x-iwut-identity 或 body 中的 token 均不能替代它。替代身份头的拒绝规则沿用既有 Session 入口。DEVICE_CREDENTIAL 与 EMAIL_CODE_AND_DEVICE 均接受，其它认证方法失败关闭；不能要求已有 Developer 身份或权限。方法逐项登记，未知 RPC 默认拒绝。

## 消息字段

以下是设计字段表；可执行 Proto 及生成代码进入独立 API 仓库。

| 消息 | 固定字段号、类型与名称 |
| --- | --- |
| `ApplyForDeveloperRequest` | `1: string developer_handle`（业务必填） |
| `DeveloperApplicationResult` | `1: auth_center.v1.developer_status.DeveloperStatus developer_status`；`2: optional int64 activated_at_unix_ms`；`3: string developer_handle` |
| `GetOwnDeveloperEligibilityRequest` | 空消息 |
| `OwnDeveloperEligibility` | `1: optional auth_center.v1.developer_status.DeveloperStatus developer_status`；`2: optional int64 activated_at_unix_ms`；`3: bool can_apply`；`4: repeated DeveloperApplicationBlocker blockers`；`5: optional string developer_handle` |

Apply 的 developer_handle 必填，缺失、空字符串或 JSON null 均为 INVALID_DEVELOPER_HANDLE；格式与规范化由 UC013 BR-DEV-011 定义。成功响应的 developer_handle 必为本人已经占用的规范值；查询字段 absent 表示尚无 handle，present 空字符串不是合法输出。既有字段号保持不变。本次增加业务必填项，旧 `{}` 客户端必须更新，不为旧请求自动生成名称。

复用 UC002 的 DeveloperStatus 枚举，不创建另一套状态数字。Apply 成功时 developer_status 必为 DEVELOPER_STATUS_APPROVED；本人查询普通用户的状态字段 absent，代表业务 null。presence 为真但值为 UNSPECIFIED 或未知枚举均不是合法业务输出。

activated_at_unix_ms 是正整数 UTC Unix 毫秒；没有可核实开通记录时 absent，不用 0 伪造时间。ProtoJSON 对 absent optional 字段省略，对 int64 输出十进制字符串；客户端把省略映射为业务 null。can_apply=false 和空 blockers 可按标准 ProtoJSON 省略，客户端读取其默认值。字段名推荐 lowerCamelCase。

DeveloperApplicationBlocker 固定数字：`DEVELOPER_APPLICATION_BLOCKER_UNSPECIFIED=0`、`EMAIL_REQUIRED=1`、`EMAIL_LOGIN_UNAVAILABLE=2`、`ALREADY_DEVELOPER=3`、`EXISTING_APPLICATION=4`、`REAPPLICATION_NOT_ALLOWED=5`；后五个 Proto 枚举名统一加 `DEVELOPER_APPLICATION_BLOCKER_` 前缀。服务端不输出 UNSPECIFIED 或重复 blocker，顺序由 UC013 BR-DEV-010 决定。

两个请求拒绝未知字段（包括原生 gRPC 的 protobuf unknown fields）；不接受 authId、邮箱、状态、requestId 或客户端就绪声明。查询没有一次性凭据，申请按当前账号状态及规范 handle 幂等；相同规范名称重试成功，已有名称时提交不同名称冲突，历史 APPROVED 补设规则见 UC013。

## HTTP 与 Gateway

| HTTP | Auth 内部路径 | RPC 方法 | Gateway 策略 | 成功状态 |
| --- | --- | --- | --- | --- |
| POST | `/v1/users/me/developer-application` | DeveloperApplicationService/ApplyForDeveloper | DIRECT | 200 |
| GET | `/v1/users/me/developer-eligibility` | DeveloperApplicationService/GetOwnDeveloperEligibility | DIRECT | 200 |

Apply annotation body 为 `"*"`，客户端提交例如 `{"developerHandle":"alice"}`，拒绝空 body、null 或数组；空对象缺少必填 handle，返回 INVALID_DEVELOPER_HANDLE；GET 无 body。两个入口均拒绝 query 参数。公共 HTTP 前缀 `/auth-center` 在转发前剥离；原生 gRPC full method 不加前缀，gRPC-Web 沿用既有终止契约。

遵守 [Auth API 路由](auth-center-api-routing.md) 的严格 JSON、默认 16 KiB 消息上限、415 内容类型/压缩拒绝及 Cache-Control: no-store。DIRECT 保留原 Session 并交 Auth 在线验证，不执行 SESSION-to-JWS，不清洗非法身份载体。

错误 reason/HTTP/gRPC 状态由 UC013 定义；超大消息为 DEVELOPER_APPLICATION_REQUEST_TOO_LARGE。限流带正整数秒 retryAfterSeconds metadata 和 HTTP Retry-After。空结果/部分结果不得用于掩盖事务失败；提交未知返回不可用，允许用户沿用原 Session 查询或重试。

## 交付边界

两个用户方法受 UC013 的默认关闭部署开关控制，HTTP/gRPC 注册保持一致。Auth/API 实现不等于 Gateway 路由或客户端入口已交付。内部 UC002 继续只提供原生 gRPC，不因新增本人查询开放给终端。

- 2026-09-26：增加 Apply 必填 developer_handle、结果字段 3 与查询 optional 字段 5；保持既有 Session、路由、枚举及 JWS 契约。
