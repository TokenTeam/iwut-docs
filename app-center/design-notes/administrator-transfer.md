# 管理员转让设计方向

状态：`PROPOSED`，对应后续独立用例，不属于 UC-APP-001。

## 结论

管理权的当前结果与转让过程应分开保存：

- `application.adminId`：唯一权威的当前管理员。
- `application_admin_transfer`：一次转让申请的参与者、状态与审计记录。
- Auth 消息：通知和进入接受页面的入口，不是转让状态的事实来源。

不建议在 Application 上增加 `pendingAdminId`、`transferStatus` 等字段。转让可能被拒绝、取消或多次发起，把过程塞进 Application 会丢失历史，并让当前状态与流程状态混在一起。

## 最小流程

1. 当前 admin 指定目标 authId 并发起申请。
2. App Center 建立 `PENDING` 转让记录，并发布通知事件。
3. Auth 消息系统向目标用户显示申请；消息投递失败不改变申请事实。
4. 目标用户以自己的可信 authId 调用接受或拒绝入口。
5. 接受时确认：
   - 申请仍为 `PENDING`。
   - Application.adminId 仍等于 fromAdminId。
   - 调用者 authId 等于 toAdminId。
   - 新管理员 developerStatus 为 `APPROVED`。
   - 新管理员没有大小写等价的同名应用。
   - 新管理员有足够配额。
6. 在一个事务中更新 Application.adminId、双方配额占用和转让状态。

原 admin 可以在接受前取消申请；是否允许平台人员强制取消或介入争议，留作后续规则。

## `application_admin_transfer`

| Key | desc | type | format | unique? | nullable? |
| --- | --- | --- | --- | --- | --- |
| `transferId` | 转让申请 ID | string | UUIDv7 | yes | no |
| `applicationId` | 目标 Application | string | UUIDv7 | `partial: one PENDING per applicationId` | no |
| `fromAdminId` | 发起时的当前管理员 | string | opaque authId | no | no |
| `toAdminId` | 被邀请的新管理员 | string | opaque authId | no | no |
| `status` | 申请状态 | string enum | `PENDING/ACCEPTED/REJECTED/CANCELLED` | no | no |
| `requestedAt` | 发起时间 | datetime | UTC / RFC 3339 | no | no |
| `resolvedAt` | 接受、拒绝或取消时间 | datetime | UTC / RFC 3339 | no | yes |
| `resolutionReason` | 拒绝、取消或平台介入理由 | string | UTF-8，长度与内容规则 TBD | no | yes |

约束：

- `fromAdminId != toAdminId`。
- 每个 Application 同时最多有一个 `PENDING` 申请。
- 终态记录不可改回 `PENDING`。
- 接受操作必须具有幂等语义；重复接受同一已成功申请返回既有结果。

## 消息集成

App Center 保存申请后发布 `ApplicationAdminTransferRequested` 集成事件，由 Auth 消息能力消费。可靠投递需要时使用 outbox，但不把消息是否已读作为接受转让的前置条件。

消息中只携带 transferId、applicationId、应用显示名称和发起者展示信息；真正接受时仍由 App Center 重新校验当前状态。

## 仍待决定

- 转让是否把一个配额占用从原 admin 移到新 admin；当前建议是。
- 新 admin 配额不足或存在同名应用时，当前建议拒绝接受，而不是自动改名或临时超额。
- 申请是否过期；如需要，再增加 `EXPIRED` 和 `expiresAt`。
