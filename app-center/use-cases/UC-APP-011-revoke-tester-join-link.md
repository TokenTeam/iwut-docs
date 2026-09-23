# UC-APP-011：管理员显式撤销 Tester 加入链接

状态：`ACCEPTED`

## 目标与范围

> developerStatus 为 `APPROVED` 的当前应用管理员，显式撤销该 Application 的一个 Tester 加入链接，使它不能再创建新的 Tester Membership，同时不创建替代链接，也不影响现有 Tester。

本用例负责：

- 按 `(applicationId, joinLinkId)` 精确定位 TesterJoinLink。
- 把目标 ACTIVE 链接迁移为 `REVOKED`，记录 reason=`MANUAL`、revokedBy 和 revokedAt。
- 对同一个已经 REVOKED 的 joinLinkId 提供幂等结果。
- 确保撤销提交后，使用该链接的新加入请求不能成功。
- 与轮换、加入及管理员转让并发时保持明确顺序。

本用例不负责：

- 创建新的 Tester 加入链接。
- 把显式撤销伪装成一次没有替代链接的轮换。
- 移除现有 Tester Membership 或减少 activeTesterCount。
- 建立用户黑名单。
- 修改 test/grey/stable 发布槽位。
- 通知现有 Tester 或 Auth。
- 删除 TesterJoinLink 历史记录或 tokenHash。

撤销后，Application 可以处于“没有 ACTIVE TesterJoinLink，但仍有 ACTIVE Tester”的合法状态。管理员以后可以通过 UC-APP-008 使用 `expectedActiveJoinLinkId=null` 创建新链接。

## 输入与身份

路径参数：

```text
applicationId: ApplicationId
joinLinkId: ApplicationTesterJoinLinkId
```

Command 没有业务字段。status、revocationReason、revokedBy、revokedAt 和 replacedByJoinLinkId 都不能由请求正文指定。

可信身份：

```text
DeveloperIdentity {
  authId: string
  developerStatus: PENDING | APPROVED | REJECTED | SUSPENDED
}
```

按 joinLinkId 操作可以保护新链接：管理员基于旧页面撤销一个已经被轮换的链接时，只会得到旧链接的幂等终态，不会误撤销当前 ACTIVE 链接。

## 主流程

1. 从可信身份上下文取得 authId 和 developerStatus。
2. 确认 developerStatus 为 `APPROVED`，applicationId 与 joinLinkId 是合法 UUIDv7。
3. Repository 加载撤销候选并确认：
   - Application 存在且当前 adminId 是调用者 authId。
   - joinLinkId 属于路径中的 Application。
4. 若目标链接已是 REVOKED，返回原链接和 revoked=false；不读取 Clock，不修改撤销原因，也不影响可能存在的其他 ACTIVE 链接。
5. 从 Clock 取得 revokedAt。
6. Repository 在同一事务或等价原子边界中重新确认当前 admin、链接归属和 ACTIVE 状态，然后写入：
   - status=`REVOKED`
   - revocationReason=`MANUAL`
   - revokedBy=当前 authId
   - revokedAt
   - replacedByJoinLinkId=null
7. 返回更新后的链接和 revoked=true。

本用例不需要读取 Tester Membership、activeTesterCount、ApplicationPublication 或 ApplicationVersion。

## 异常流程

- 缺少身份：`DeveloperIdentityRequired`。
- developerStatus 不是 `APPROVED`：`DeveloperApprovalRequired`。
- applicationId 非法：`InvalidApplicationId`。
- joinLinkId 非法：`InvalidTesterJoinLinkId`。
- Application 不存在，或链接不存在/不属于该 Application：统一返回 `ApplicationTesterJoinLinkNotFound`。
- 调用者不是当前 admin：`ApplicationAdminRequired`。
- ACTIVE 链接包含不应存在的撤销字段，或 REVOKED 链接字段组合非法：`ApplicationTesterJoinLinkStateInconsistent`。
- 时钟或持久化失败：内部失败，链接仍保持原状态。

路径关系不匹配按 NotFound 处理，不泄露其他 Application 的链接状态。

## 业务规则

<a id="br-tst-029"></a>
### BR-TST-029：撤销权限

撤销者必须同时满足：

- developerStatus 为 `APPROVED`。
- 在最终事务中仍是 Application 当前 adminId。

普通 Tester、Reviewer 或链接持有人都不能仅凭自身身份撤销链接。

<a id="br-tst-030"></a>
### BR-TST-030：按链接身份定位

撤销目标由 `(applicationId, joinLinkId)` 唯一确定。请求不能表达“撤销当前任意有效链接”，也不能省略 joinLinkId。

旧链接被轮换后会保留原 joinLinkId。对旧 ID 的迟到请求不得作用于 replacedByJoinLinkId 或当前其他 ACTIVE 链接。

<a id="br-tst-031"></a>
### BR-TST-031：MANUAL 撤销终态

ACTIVE 链接成功显式撤销后必须满足：

```text
status = REVOKED
revocationReason = MANUAL
revokedBy = current admin authId
revokedAt = App Center Clock
replacedByJoinLinkId = null
```

MANUAL 表示没有由本操作创建的替代链接。REVOKED 是终态，链接不能恢复为 ACTIVE。

<a id="br-tst-032"></a>
### BR-TST-032：幂等撤销

- ACTIVE 链接首次显式撤销返回 revoked=true。
- 目标链接已经 REVOKED 时返回既有终态和 revoked=false。
- 幂等结果不修改 `ROTATED/MANUAL` 原因、撤销审计或替代关系。
- 幂等返回前仍要确认当前调用者是 Application admin。

因此，对已经 ROTATED 的旧链接调用本用例不会把 reason 改成 MANUAL，也不会撤销其替代链接。

<a id="br-tst-033"></a>
### BR-TST-033：凭证立即失效

撤销事务提交后，目标 joinLinkId 与 secret 的组合不能再创建 Membership。只在事务开始前做缓存校验不够；UC-APP-009 必须在最终加入事务中复查 status=`ACTIVE`。

撤销不要求删除 tokenHash。保留哈希用于验证历史一致性和统一拒绝旧凭证，但不得记录或恢复明文 secret。

<a id="br-tst-034"></a>
### BR-TST-034：并发线性化

- 撤销先提交、加入后提交：加入必须因链接已 REVOKED 而失败。
- 加入先提交、撤销后提交：已创建的 Membership 保留，撤销只阻止后续加入。
- 轮换先提交：旧链接已 ROTATED，本次撤销幂等返回旧终态，新链接保持 ACTIVE。
- 撤销先提交：基于旧 ACTIVE 链接执行的轮换因 expectedActiveJoinLinkId 不再匹配而失败。
- 管理员转让先提交：旧 admin 的撤销失败。

<a id="br-tst-035"></a>
### BR-TST-035：与 Tester Membership 独立

显式撤销链接不得：

- 移除或修改任何 ACTIVE/REMOVED Membership。
- 改变 activeTesterCount。
- 阻止管理员以后创建新链接。
- 为任何 authId 建立黑名单。

现有 Tester 在链接撤销后继续拥有测试资格，直到被 UC-APP-010 单独移除。

<a id="br-tst-036"></a>
### BR-TST-036：边界、审计与隐私

链接记录不物理删除，createdBy/createdAt/tokenHash 保持不变，撤销字段写入后不可修改。

撤销不得修改 ApplicationPublication、ApplicationVersion、ApplicationReview、Auth 用户或权限，也不自动发送通知。API 响应和日志不能返回 secret 或 tokenHash。

## 最小领域模型

UC-APP-011 扩展 UC-APP-008 已引入的 revocationReason：

```text
ApplicationTesterJoinLink {
  joinLinkId: ApplicationTesterJoinLinkId
  applicationId: ApplicationId
  tokenHash: TesterJoinTokenHash
  status: ACTIVE | REVOKED
  createdBy: AuthId
  createdAt: Instant
  revokedBy: optional AuthId
  revokedAt: optional Instant
  revocationReason: optional ROTATED | MANUAL
  replacedByJoinLinkId: optional ApplicationTesterJoinLinkId
}
```

合法状态组合：

```text
ACTIVE
  revokedBy=null
  revokedAt=null
  revocationReason=null
  replacedByJoinLinkId=null

REVOKED / ROTATED
  revokedBy!=null
  revokedAt!=null
  replacedByJoinLinkId!=null

REVOKED / MANUAL
  revokedBy!=null
  revokedAt!=null
  replacedByJoinLinkId=null
```

## 用例端口

```go
type Clock interface {
    Now() time.Time
}

type ApplicationTesterJoinLinkRepository interface {
    LoadRevocationCandidate(
        ctx context.Context,
        applicationID ApplicationID,
        joinLinkID ApplicationTesterJoinLinkID,
        expectedAdminID AuthID,
    ) (*TesterJoinLinkRevocationCandidate, error)

    Revoke(
        ctx context.Context,
        applicationID ApplicationID,
        joinLinkID ApplicationTesterJoinLinkID,
        expectedAdminID AuthID,
        revokedAt time.Time,
    ) (*RevokeTesterJoinLinkResult, error)
}
```

`Revoke` 必须重新比较 Application.adminId、TesterJoinLink.applicationId/status，并只对目标 ACTIVE joinLinkId 写入 MANUAL 撤销字段。

## 数据模型

UC-APP-011 不新增 collection，复用 `application_tester_join_links`：

| Key | 本用例行为 |
| --- | --- |
| `status` | 从 `ACTIVE` 单向变为 `REVOKED` |
| `revokedBy` | 成功撤销时写当前 admin authId；之后不可修改 |
| `revokedAt` | 成功撤销时写 App Center UTC 时间；之后不可修改 |
| `revocationReason` | 本用例写 `MANUAL` |
| `replacedByJoinLinkId` | MANUAL 时固定为空 |
| `tokenHash` | 保持不变，不对外返回 |

索引与 validator：

- ACTIVE 的四个撤销字段必须全部为空。
- REVOKED 必须具有 revokedBy、revokedAt 和 revocationReason。
- ROTATED 必须具有 replacedByJoinLinkId。
- MANUAL 的 replacedByJoinLinkId 必须为空。
- REVOKED 不能恢复为 ACTIVE，撤销字段不能二次改写。
- partial unique ACTIVE 索引在撤销提交后允许同一 Application 创建新链接。

## API 草图

```text
DELETE /applications/{applicationId}/tester-join-links/{joinLinkId}
Authorization: <authenticated developer identity>
```

首次撤销和幂等重复均返回 `200 OK`：

```json
{
  "revoked": true,
  "joinLink": {
    "joinLinkId": "join-link-uuid",
    "applicationId": "application-uuid",
    "status": "REVOKED",
    "createdBy": "admin-auth-id",
    "createdAt": "2026-09-16T12:00:00Z",
    "revokedBy": "admin-auth-id",
    "revokedAt": "2026-09-16T15:00:00Z",
    "revocationReason": "MANUAL",
    "replacedByJoinLinkId": null
  }
}
```

API 不接受 `createReplacement`、`removeTesters` 或目标状态字段。需要新链接时，管理员随后独立调用 UC-APP-008。

候选 HTTP 映射：

- 缺少身份：`401 Unauthorized`。
- developerStatus 非 APPROVED 或不是当前 admin：`403 Forbidden`。
- Application/TesterJoinLink 不存在或归属不匹配：`404 Not Found`。
- applicationId 或 joinLinkId 格式非法：`400 Bad Request`。
- 链接状态字段不一致：HTTP `500 Internal Server Error` / gRPC `INTERNAL`，稳定 reason 为 `ERROR_REASON_APPLICATION_TESTER_JOIN_LINK_STATE_INCONSISTENT`。沿用已确认的内部数据不变量异常分类，触发不含凭证的服务端告警，不暴露底层存储细节。

## 测试与验收

领域测试：

- ACTIVE 可以迁移为 REVOKED/MANUAL，replacedByJoinLinkId 必须为空。
- REVOKED/ROTATED 的替代关系保持不变，不能改写为 MANUAL。
- REVOKED 不能恢复为 ACTIVE。

UseCase 测试：

- 只有 `APPROVED` 的当前 admin 可以撤销。
- 首次撤销返回 revoked=true；重复撤销返回 revoked=false 且不读取 Clock。
- 对已 ROTATED 旧链接撤销不影响替代链接。
- 撤销不读取或修改 Membership、activeTesterCount 和 Publication。
- 请求不能要求创建替代链接或移除 Tester。

Repository 集成测试：

- 两个并发撤销最多一个写入审计字段。
- 撤销与加入的提交顺序决定加入成功或失败。
- 撤销与轮换同一 ACTIVE 链接时最多一个状态迁移成功。
- 管理员转让与撤销并发时旧 admin 不能成功。
- partial unique ACTIVE 索引在撤销后允许创建新链接。

API 与安全测试：

- 首次与重复撤销都返回 200，并正确区分 revoked。
- 请求不能指定 status、reason、revokedBy、revokedAt 或 replacedByJoinLinkId。
- 响应、日志、trace 和错误详情不包含 secret 或 tokenHash。
- 不存在与归属不匹配使用统一外部错误。

## 实现依赖与交付边界

- UC-APP-008 已交付链接、哈希、历史审计、ACTIVE partial unique index，现有 0009 schema 和领域恢复逻辑已支持 MANUAL；当前不要求新增 collection 或 migration。如确需改变存储约束，新增显式迁移，不修改已交付迁移。
- 复用 UC008/009/010 的 Application `coordinationRevision` 写栅栏。事务内先取得该 Application 的真实写栅栏，再校验当前 admin 和精确目标链接的归属及状态；仅把该 ACTIVE joinLinkId 改为 REVOKED/MANUAL，不读取或改写 Membership 或人数。
- `LoadRevocationCandidate` 的 REVOKED 幂等快捷结果也必须在上述栅栏与一致快照中校验当前 admin；不读取 Clock，不修改业务记录或原审计，仅允许维护 adapter-only 写栅栏。ACTIVE 候选是预检查，最终 `Revoke` 必须重新取得栅栏并复查；若并发轮换/撤销已完成，则返回原终态并丢弃预取时间。
- 使用 snapshot read concern 与 majority write concern，沿用 [UC-APP-009 事务重试协议](UC-APP-009-join-application-as-tester.md#active-tester-计数)。事务重试始终针对原 `(applicationId, joinLinkId)`，不得自动跟随替代关系或选择当前其他 ACTIVE 链接。
- UC-APP-009 已在取得同一写栅栏后最终验证链接，必须通过真实 MongoDB 测试证明撤销/加入和撤销/轮换的双向提交顺序。撤销后现有 Membership 完整保留，UC008 可独立创建新链接。
- 复用可信 DeveloperIdentity、APPROVED 校验、Clock、Proto/Wire 与真实 MongoDB 副本集设施；前端和生产 Gateway 身份签发链路独立交付。
- 不依赖测试发布、Auth Scope Catalog、UC-APP-012 解析，也不实现 Tester 移除、黑名单、替代链接生成或通知。

## 后续用例

```text
UC-APP-012：为 Tester 解析 Application 的 test 启动目标
```

## 变更记录

- 2026-09-16：建立 UC-APP-011；当前 admin 可按 joinLinkId 幂等执行 MANUAL 撤销，阻止后续加入但不创建替代链接、不移除 Tester。
- 2026-09-16：后续解析用例重命名为 UC-APP-012“为 Tester 解析 Application 的 test 启动目标”，明确它是 App Center 查询而非客户端实现。

- 2026-09-23：开工检查确认复用既有 MANUAL schema、Application 写栅栏及事务重试；一致性异常沿用用户已确认的 HTTP 500 / gRPC INTERNAL 分类，明确幂等无 Clock 和独立交付边界。
- 2026-09-23：UC010 完整回归通过，UC011 依赖与设计检查无阻塞，状态改为 ACCEPTED 并激活后端实现工作包。
