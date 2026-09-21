# UC-APP-010：管理员移除 Application Tester

状态：`PROPOSED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，按 membershipId 移除该 Application 中一个当前 ACTIVE Tester Membership episode，并原子释放一个 Tester 名额。

本用例负责：

- 验证调用者仍是 Application 当前 admin。
- 精确定位所属 Application 下的一次 Membership episode。
- 把 ACTIVE episode 迁移为 REMOVED，记录 removedBy 和 removedAt。
- 原子减少 activeTesterCount。
- 对同一个已经 REMOVED 的 membershipId 提供幂等结果。
- 返回移除完成时是否仍存在 ACTIVE TesterJoinLink，供管理界面显示重新加入警告。

本用例不负责：

- 撤销、轮换或删除 Tester 加入链接。
- 把用户加入黑名单或阻止未来重新加入。
- 删除 Membership 历史记录。
- 按 authId 批量移除所有历史 episode。
- 修改 test/grey/stable 槽位或 ApplicationVersion。
- 通过 Auth 撤销权限、developerStatus 或用户身份。
- 向被移除用户发送通知。
- 允许 Tester 主动退出；那是独立的未来用例。

如果仍存在有效加入链接，管理界面可以在执行前警告：“该用户仍可通过有效的测试加入链接再次加入。”这个提示不构成确认步骤，也不会把移除与链接撤销组合成一个命令。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
membershipId: ApplicationTesterMembershipId
```

Command 没有业务字段。目标用户、status、removedBy、removedAt 和 activeTesterCount 都不能由请求正文指定。

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

按 membershipId 操作而不是按 testerAuthId 操作，可以确保对旧 episode 的重复请求不会误删该用户后来重新加入所产生的新 ACTIVE episode。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，applicationId 和 membershipId 是合法 UUIDv7。
3. Repository 加载移除候选并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - membershipId 属于路径中的 Application。
4. 若目标 episode 已是 REMOVED，返回原 Membership、removed=false、当前 activeTesterCount 和当前是否存在 ACTIVE TesterJoinLink；不读取 Clock，不改变任何记录。
5. 从 Clock 取得 removedAt。
6. Repository 在同一事务或等价原子边界中重新确认当前 admin、Membership 归属和状态，然后：
   - 把 status 从 ACTIVE 改为 REMOVED。
   - 写入 removedBy=当前 authId、removedAt。
   - 将 activeTesterCount 减少 1。
7. 返回更新后的 Membership、removed=true、结果 activeTesterCount，以及提交时是否存在 ACTIVE TesterJoinLink。

ACTIVE TesterJoinLink 的存在性只是提示快照，不是移除前置条件。链接在操作前后发生轮换或撤销，不影响 Membership 移除是否成功。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- membershipId 非法：`InvalidTesterMembershipId`。
- Application 不存在，或 Membership 不存在/不属于该 Application：统一返回 `ApplicationTesterMembershipNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- ACTIVE Membership 存在但 activeTesterCount 已为 0，或计数与状态无法一致提交：`ApplicationTesterStateInconsistent`。
- 时钟或持久化失败：内部失败，不改变 Membership 或计数。

路径关系不匹配按 NotFound 处理，不泄露其他 Application 的 Tester 信息。

## 业务规则

<a id="br-tst-020"></a>
### BR-TST-020：移除权限

移除者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

管理员可以移除自己的 Tester Membership；管理员身份与 Tester 资格相互独立。Reviewer 或普通 Tester 不因其他身份获得移除权限。

<a id="br-tst-021"></a>
### BR-TST-021：按 Membership episode 定位

移除目标由 `(applicationId, membershipId)` 唯一确定。membershipId 必须属于该 Application；请求不能用 testerAuthId 代替。

同一用户重新加入会取得新的 membershipId。对旧 REMOVED membershipId 的迟到或重复请求不得影响新的 ACTIVE episode。

<a id="br-tst-022"></a>
### BR-TST-022：幂等移除

- ACTIVE episode 首次成功移除时返回 removed=true。
- 同一 membershipId 已经 REMOVED 时返回原终态和 removed=false。
- 幂等结果不改写 removedBy/removedAt，不再次减少计数，也不创建新的审计记录。
- 幂等返回前仍要确认当前调用者是 Application admin，不能把旧 Membership 当作公开查询入口。

<a id="br-tst-023"></a>
### BR-TST-023：REMOVED 终态与审计

成功移除必须记录：

```text
status = REMOVED
removedBy = current admin authId
removedAt = App Center Clock
```

joinedViaJoinLinkId 和 joinedAt 保持不变。REMOVED episode 不恢复为 ACTIVE、不物理删除；用户再次加入时创建新的 episode。

<a id="br-tst-024"></a>
### BR-TST-024：原子释放容量

Membership 的 `ACTIVE -> REMOVED` 与 activeTesterCount `-1` 必须全部成功或全部失败。

- activeTesterCount 不能小于 0。
- 幂等移除不改变计数。
- 成功释放的名额可以被后续有效加入使用。
- 每个 Application 的 ACTIVE Tester 上限仍固定为 100。

<a id="br-tst-025"></a>
### BR-TST-025：不建立黑名单

移除只终止当前 Membership episode，不表示封禁 authId。被移除用户只要取得当前有效加入链接，且 ACTIVE Tester 数量小于 100，就可以重新加入。

若未来需要禁止特定用户再次加入，必须引入明确的封禁/黑名单用例、权限、期限和申诉规则，不能改变本用例语义。

<a id="br-tst-026"></a>
### BR-TST-026：加入链接独立

移除 Membership 不得撤销、轮换或删除任何 TesterJoinLink。链接是否 ACTIVE 不影响移除能否执行。

Repository 返回的 activeJoinLinkExists 只用于界面提示。提示不要求管理员确认，也不能把两个动作包装为一个领域命令。

<a id="br-tst-027"></a>
### BR-TST-027：并发线性化

- 两个并发移除请求最多一个执行状态迁移和计数减少；另一个安全返回幂等结果或在冲突后重读。
- 移除与同一用户重新加入并发时，结果必须等价于某个明确顺序：加入先发生则本次移除该 ACTIVE episode；移除先发生则持有效链接的用户可以创建新的 episode。
- 管理员转让与移除并发时，旧 admin 不能在转让提交后成功移除。
- 链接轮换/撤销与移除相互独立，不需要跨两个生命周期建立联合事务。

<a id="br-tst-028"></a>
### BR-TST-028：边界与隐私

移除 Tester 不得：

- 修改 ApplicationPublication、ApplicationVersion 或 ApplicationReview。
- 修改 Auth 用户、Developer 状态或权限。
- 返回其他 Tester 的列表或个人资料。
- 删除加入来源、加入时间或其他 Membership 审计事实。
- 自动发送通知。

App Center 只保存和返回完成本操作所需的 opaque authId 与 Membership 审计字段。

## 最小领域模型

UC-APP-010 完成 UC-APP-009 已引入的 Membership 生命周期：

```text
ApplicationTesterMembership {
  membershipId: ApplicationTesterMembershipId
  applicationId: ApplicationId
  testerAuthId: AuthId
  status: ACTIVE | REMOVED
  joinedViaJoinLinkId: ApplicationTesterJoinLinkId
  joinedAt: Instant
  removedBy: optional AuthId
  removedAt: optional Instant
}
```

合法状态组合：

```text
ACTIVE  -> removedBy=null, removedAt=null
REMOVED -> removedBy!=null, removedAt!=null
```

REMOVED 是该 episode 的终态。当前模型不保存 removalReason，因为移除行为没有要求管理员填写理由。

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ApplicationTesterMembershipRepository interface {
    LoadRemovalCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        membershipID ApplicationTesterMembershipID,
        expectedAdminID AuthID,
    ) (*TesterRemovalCandidate, error)

    Remove(
        ctx context.Context,
        applicationID ApplicationID,
        membershipID ApplicationTesterMembershipID,
        expectedAdminID AuthID,
        removedAt time.Time,
    ) (*RemoveApplicationTesterResult, error)
}
```

`Remove` 必须重新比较 Application.adminId、Membership.applicationId/status 和 activeTesterCount，并在同一原子边界写 REMOVED 与计数。结果中的 activeJoinLinkExists 是提交时的提示快照，不参与事务成败判断。

## 数据模型

UC-APP-010 不新增 collection，复用 `application_tester_memberships`：

| Key | 本用例行为 |
| --- | --- |
| `status` | 从 `ACTIVE` 单向变为 `REMOVED` |
| `removedBy` | 成功移除时写当前 admin authId；之后不可修改 |
| `removedAt` | 成功移除时写 App Center UTC 时间；之后不可修改 |
| `joinedViaJoinLinkId` | 保持不变 |
| `joinedAt` | 保持不变 |

存储约束：

- REMOVED 必须同时具有 removedBy 和 removedAt。
- REMOVED 不能恢复为 ACTIVE。
- partial unique ACTIVE 索引在状态迁移后释放 `(applicationId, testerAuthId)`，允许重新加入创建新 episode。
- Membership 状态迁移与 activeTesterCount 减少必须原子提交。
- 历史查询索引继续保留 REMOVED episode。

## API 草图

```text
DELETE /applications/{applicationId}/tester-memberships/{membershipId}
Authorization: <authenticated developer identity>
```

首次移除和幂等重复均返回 `200 OK`：

```json
{
  "removed": true,
  "membership": {
    "membershipId": "membership-uuid",
    "applicationId": "application-uuid",
    "testerAuthId": "tester-auth-id",
    "status": "REMOVED",
    "joinedViaJoinLinkId": "join-link-uuid",
    "joinedAt": "2026-09-16T13:00:00Z",
    "removedBy": "admin-auth-id",
    "removedAt": "2026-09-16T14:00:00Z"
  },
  "capacity": {
    "activeTesterCount": 16,
    "testerLimit": 100
  },
  "activeJoinLinkExists": true
}
```

当 activeJoinLinkExists=true 时，管理界面显示重新加入警告。API 不要求 `confirm` 或 `revokeJoinLink` 参数。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application/Membership 不存在或归属不匹配：`404 Not Found`。
- applicationId 或 membershipId 格式非法：`400 Bad Request`。
- Membership 与计数状态不一致：`409 Conflict` 或内部一致性错误，并触发告警。

## 测试与验收

领域测试：

- ACTIVE 可以迁移为 REMOVED，并写入 removedBy/removedAt。
- REMOVED 不能恢复为 ACTIVE，加入字段保持不变。
- 没有 removalReason，也没有 blacklist 状态。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以移除。
- admin 可以移除自己的 Tester Membership。
- 首次移除返回 removed=true；重复移除返回 removed=false 且不读取 Clock。
- membershipId 归属不匹配按 NotFound 处理。
- activeJoinLinkExists 只影响响应提示，不影响移除结果。
- 请求不能要求同时撤销链接。

Repository 集成测试：

- Membership 状态与 activeTesterCount 原子更新。
- 同一 Membership 并发移除只减少一次计数。
- 对旧 REMOVED episode 的重复删除不影响后来重新加入的新 episode。
- 移除与重新加入并发结果满足明确线性化顺序。
- 管理员转让与移除并发时旧 admin 不能成功。
- activeTesterCount 为 0 但 Membership 为 ACTIVE 时拒绝提交并报告不一致。

API 测试：

- 首次和重复移除都返回 200，并正确区分 removed。
- 请求不能指定 testerAuthId、status、removedBy、removedAt 或计数。
- 响应在存在 ACTIVE 加入链接时返回 activeJoinLinkExists=true。
- API 不接受组合撤销链接参数。

## 实现前需要确认

- activeTesterCount 的最终存储方式及事务重试策略，与 UC-APP-009 使用同一实现。
- Tester 管理查询需要返回哪些字段和分页方式，以便界面在删除前展示 activeJoinLinkExists 警告；查询本身是独立读模型，不改变本用例命令。

## 后续用例

```text
UC-APP-011：当前管理员显式撤销 Tester 加入链接
UC-APP-012：为 Tester 解析 Application 的 test 启动目标
```

## 变更记录

- 2026-09-16：建立 UC-APP-010；当前 admin 按 membershipId 幂等移除 ACTIVE Tester、原子释放容量并保留 episode，加入链接只产生重新加入警告，不被组合撤销。
- 2026-09-16：UC-APP-011 已把显式链接撤销定义为独立 MANUAL 终态，继续保持与 Tester 移除完全分离。
