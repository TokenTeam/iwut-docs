# UC-APP-050：查询我的待接收 Application 管理权转让

状态：`ACCEPTED`（2026-11-08 用户接受搜索与待接收转让草案，要求编写 UC 并串行实现）。

## 目标与范围

可信 ACTIVE USER 可以分页发现指定给自己的未到期待接收转让，随后进入 UC026 参与者详情并执行原有接受或拒绝。该读取不要求当前仍为 APPROVED Developer。接受资格、七天有效期、终态及并发规则仍以 [UC026](UC-APP-026-transfer-application-administration.md) 的 [BR-APP-012](UC-APP-026-transfer-application-administration.md#br-app-012)、[BR-APP-013](UC-APP-026-transfer-application-administration.md#br-app-013)、[BR-APP-019](UC-APP-026-transfer-application-administration.md#br-app-019) 为唯一权威；搜索命中不构成接受授权。

首期只交付本人入站 PENDING 列表，不交付出站/全状态历史、已读标记、通知、转让对象搜索、Auth 资料批量披露或全平台转让枚举。转让目标继续填写已有 opaque Auth ID。

## 正式接口与输入

现有 `app_center.v1.application_admin_transfer.ApplicationAdminTransferService` 新增 `ListIncomingApplicationAdminTransfers`，App HTTP为 `POST /v1/application-admin-transfers/incoming:search`，body=`query`。Gateway 外部增加 `/app-center`，强制 Session，沿用现有转让查询的协议和 Developer Console 接入，不增加 Admin 枚举入口。

```text
ListIncomingApplicationAdminTransfersQuery {
  pageSize: 1..100 = 20
  pageToken?
}
```

省略/0 pageSize使用默认20，负数或大于100拒绝；pageToken最多4096 UTF-8 bytes。请求不接受 toAuthId、fromAuthId、状态、方向、排序、offset 或任意目标身份。HTTP只接受单个JSON对象、正文最大16 KiB、无query string；未知字段或多份JSON拒绝。native gRPC未知字段同样拒绝。身份验证先于输入解析/校验及数据定位。

## 查询事实与过期边界

同一只读 snapshot 内以可信caller为toAdminId，选取持久状态PENDING且 `expiresAt > asOf` 的申请。App Clock在本次调用取得一个观察时间，按Mongo存储毫秒精度比较，到期边界相等即不返回。查询不调用Auth，不写过期状态、账号 fence、Application fence/revision、业务审计或访问记录。

此列表不承担持久化EXPIRED；UC026详情Get、命令、owner-exit检查与后台收敛继续原规则。列表返回后发生接受/拒绝/取消/关闭/到期是正常变化；操作前重新读取UC026详情与当前事实，不以旧页冻结资格。无符合事项成功返回明确空数组。

## 返回与分页

投影与消费组合见[本人待接收转让读契约](../query-contracts/incoming-application-transfers.md)。每页按 `(requestedAt DESC, transferId DESC)` keyset排序，时间采用存储精度，同时间用规范UUID排序。签名opaque token绑定可信caller、独立查询用途、格式版本和末项位置，换用户、换用途、损坏或不规范编码拒绝。每页重读，不提供跨页冻结、offset或totalCount。

必要申请与Application来源在同一次 majority snapshot中组合；使用技术名称，不依赖公开Profile或发布状态。批准/暂停等Developer资格变化不隐藏本人事项。必要绑定、来源或持久字段损坏整页失败，不丢项、返回部分页或补占位名称。

## 错误与缓存

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失/无效可信USER | USER_IDENTITY_REQUIRED / INVALID_USER_IDENTITY | 401 / UNAUTHENTICATED |
| 非法请求、未知字段或pageSize/token长度 | INVALID_INCOMING_APPLICATION_TRANSFER_QUERY | 400 / INVALID_ARGUMENT |
| token编码、签名、用途、主体或位置非法 | INVALID_INCOMING_APPLICATION_TRANSFER_PAGE_TOKEN | 400 / INVALID_ARGUMENT |
| 必要持久事实损坏 | APPLICATION_ADMIN_TRANSFER_STATE_INCONSISTENT | 500 / INTERNAL |
| 存储或snapshot不可用 | INCOMING_APPLICATION_TRANSFER_UNAVAILABLE | 503 / UNAVAILABLE |

成功与错误均 `Cache-Control: private, no-store`。不披露token、secret、数据库结构或底层原因；读取token只用于本查询，不代替原详情参与者检查。

## 业务规则

<a id="br-app-059"></a>
### BR-APP-059：本人入站集合与读取资格

仅可信ACTIVE USER可查询，toAdminId只取可信主体，当前Developer批准状态不作为列表门槛。集合仅含自己的持久PENDING且未到期申请；其他参与者、已终态和逻辑到期申请不返回。没有事项成功返回空列表，当前源管理员不是申请接收者时不获得该申请的入站事项。

<a id="br-app-060"></a>
### BR-APP-060：列表只读与逻辑到期

列表在同一只读snapshot按本次观察时间排除逻辑到期申请，不写状态或协调栅栏。UC026的持久过期收敛和终态互斥不变。返回后的状态变化不保证列表仍可操作，接受/拒绝必须重新走正式详情与命令。

<a id="br-app-061"></a>
### BR-APP-061：转让事项的最小一致投影

事项只返回本UC读契约字段，Application技术名称与申请在同一majority snapshot读取。不依赖公开Profile/发布或Auth资料，不披露secret、凭据摘要、配额及私有配置。必要申请/来源缺失、跨应用、参与者或ownership绑定不符和非法字段属于损坏，整页失败。

<a id="br-app-062"></a>
### BR-APP-062：本人事项的签名分页与失败边界

使用requestedAt/transferId稳定倒序keyset、1..100默认20和绑定主体/用途/版本/位置的签名token。成功与错误private,no-store；鉴权先于输入和查询，非法token报400、损坏500、存储不可用503，不把失败伪装为空列表。

## 验收

1. 普通ACTIVE USER及Developer PENDING/SUSPENDED/WITHDRAWN读取自己的有效事项；匿名、无效身份先失败。不得根据客户端传入身份读取他人事项。
2. 未发布、无公开Profile、暂停/归档应用事项按原转让事实可读；只读不改变任何gate/revision/转让状态。
3. asOf前/恰好到期/之后，持久EXPIRED及ACCEPTED/REJECTED/CANCELLED均不列出；仅从列表读取不持久化到期，原Get仍收敛EXPIRED。
4. 同时间排序、翻页、跨用户/用途、篡改、畸形、长度与非法pageSize；无事项显式空数组。
5. 必要App丢失、归属/ownership绑定损坏、非法申请字段、存储失败分别按正式错误且无部分页。
6. 与接受、取消、UC027关闭竞争，snapshot只观察完整前/后组合；旧页不能绕过UC026命令。HTTP/原生gRPC及Gateway gRPC-Web输入、缓存和投影一致。

## 实施边界

Domain/UseCase/Port留在Application能力；Mongo adapter增加只读查询与批量来源读取，显式迁移增加 `(toAdminId,status,requestedAt DESC,transferId DESC)` 命名索引并保留原有索引。签名key从已有服务秘密材料按独立用途派生，不引入业务数据兼容或新权限。新生成消息与Proto输入一起提交，Wire使用生成器。先串行专项，后冻结源码/API/已提交docs运行完整backend；Gateway和Console由各自owner接入。
