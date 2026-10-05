# UC-AUTH-020：管理及回收同一账号的 Session

状态：`ACCEPTED`

## 目标与范围

已登录用户查看当前平台账号的有效 Session，并明确选择撤销一个或多个其他 Session，回收其会话使用资格与容量。本人范围固定为当前有效 Session 的 authId；不扩展到相同学号声明或 associationId 下的其他账号。

本用例新增会话列表与按 ID 撤销能力。登录创建、10 条有效会话上限和 LRU 仍由 UC007 拥有；当前 Session 的 token 定向撤销仍由 UC008 拥有；禁止某把设备密钥继续登录使用 UC009。这里的“回收”是写入不可逆 revokedAt，不是物理删除，不清理账号资料、设备私钥或 OAuth grant/family。

不包含设备凭据列表/命名、设备可信认证、账号关联组管理、账号合并/删除、失效会话历史查询、推送远端退出通知或数据库保留期/物理清理任务。

## 参与者与前置条件

- 调用者持有当前有效的平台 Session，主体为 ACTIVE USER；DEVICE_CREDENTIAL 与 EMAIL_CODE_AND_DEVICE 同等适用。
- Auth 在线检查主体、Session、所引用凭据及认证来源完整性，条件引用 [BR-LGN-004](UC-AUTH-007-login.md#br-lgn-004) 与 [BR-LGN-016](UC-AUTH-012-login-with-email.md#br-lgn-016)。不另要求 Developer、Reviewer、邮箱绑定或生物识别。
- callerAuthId 与 callerSessionId 仅从服务端确认的 Session 得出，不接收客户端指定 owner、学号、associationId 或认证结论。

## 输入与输出

```text
ListOwnSessions {
  pageSize: Int?       // 缺省 10，范围 1..50
  cursor: SessionId?  // 缺省为空；后续页用上一页 nextCursor
}

OwnSessionPage {
  currentSessionId: SessionId
  observedAt: Instant
  sessions: OwnSessionSummary[]
  nextCursor: SessionId?  // 最后扫描的候选 ID；没有下一页时为空
}

OwnSessionSummary {
  sessionId: SessionId
  credentialId: CredentialId
  authenticationMethod: DEVICE_CREDENTIAL | EMAIL_CODE_AND_DEVICE
  authenticatedAt: Instant
  createdAt: Instant
  lastUsedAt: Instant
  expiresAt: Instant
  isCurrent: Bool
}

RevokeOwnSessions {
  sessionIds: SessionId[]  // 1..50 个唯一、合法 ID；不能含调用者当前 Session
}

SessionsRevoked {}
```

sessionId/credentialId 是引用标识，不是认证材料。列表不返回 sessionToken/tokenDigest、公钥/指纹、邮箱、IP、地理位置、学校信息或其他账号资料；首版不新增这些数据的收集。credentialId 仅帮助辨识哪些会话使用同一凭据，不表示已经验证物理设备名称或“一个凭据等于一台设备”。

## API 契约

独立 package `auth_center.v1.session_management`，service `SessionManagementService`：

| 方法 | Auth 内部 HTTP 路径 | 认证与成功响应 |
| --- | --- | --- |
| `ListOwnSessions` | `POST /v1/users/me/sessions:list` | 有效 x-iwut-session；200，OwnSessionPage |
| `RevokeOwnSessions` | `POST /v1/users/me/sessions:revoke` | 有效 x-iwut-session；200，`{}` |

完整 RPC 方法名为 `/auth_center.v1.session_management.SessionManagementService/ListOwnSessions` 与 `/auth_center.v1.session_management.SessionManagementService/RevokeOwnSessions`。两者同时交付 HTTP/JSON 与原生 gRPC，POST JSON 不接受 query、未知字段、重复字段或 null 列表/条目。pageSize 缺省与显式 0 要区分；cursor 省略或空字符串表示第一页。

Session 唯一载体沿用 [Session 载体](../../platform/contracts/auth-device-session-v1.md#session-载体)，只接受一个规范的 x-iwut-session。拒绝 Authorization、Cookie、x-iwut-identity 或 OAuth access token 作为替代/混合认证；Session token 不进入正文、路径或 query。

Gateway 将来按 DIRECT 转发并保留原 Session，由 Auth 自行鉴权；不能先换 USER JWS，否则既无法可靠确定“当前 Session”，也会改变列表对 LRU 的只读语义。DIRECT 不代表匿名。只有两个完整方法加入明确的 Session 管理分派，不使用 package 通配匿名例外。

API Proto、共享 RPC 鉴权表和公共 `/auth-center` 路由映射随本次后端实施同步；Gateway 的实际清单与三协议联合验收保持独立交付。响应 no-store，时间采用 Timestamp/UTC，16 KiB 解码上限及严格 ProtoJSON 沿用既有管理接口惯例。

## 主流程

### 查看会话

1. 校验参数、认证载体和入口限额。
2. 在一个 Auth 一致检查点验证调用者当前 Session，取得 authId/currentSessionId；本查询不刷新 lastUsedAt。
3. 按同一 authId 读取会话，复核每条候选所引用凭据及认证来源，按 BR-LGN-020 过滤和排序。
4. 返回当前页、同一检查点的 observedAt、currentSessionId 和后续游标；不声称所有设备此刻在线。

### 回收一个或多个其他会话

1. 验证调用者当前 Session，再验证非空、有界、唯一的目标 ID 集合。
2. 若任一目标等于 callerSessionId，整个请求拒绝；调用者主动退出自身应单独使用 UC008。
3. 按 `(callerAuthId, sessionId)` 定向选择目标；首次撤销写入同一个服务端时间，已有 revokedAt 保持不变。
4. 目标状态和真实变化的审计在同一 Auth 事务提交。只有确认提交后才返回成功。

## 业务规则

<a id="br-lgn-019"></a>
### BR-LGN-019：同账号授权边界

“本人”只指当前有效 Session 的 authId。列表和撤销目标都必须带此 owner 条件，不得先无约束读取任意 ID 后把结果暴露给调用者。关联组、客户端学校登录状态、相同邮箱字符串、相同设备标签或公开 sessionId 均不产生跨账号管理权限。

列表和撤销都在各自最终一致检查点复核调用者的主体、Session、凭据与认证来源；仅相信请求开始时的身份快照不足以授权最终提交。凭据被撤销、Session 被 LRU 淘汰或主体不可用先完成时，后续管理动作失败。既有 token 定向 UC008 的匿名/幂等例外不扩展到本用例。

<a id="br-lgn-020"></a>
### BR-LGN-020：有效会话列表与只读语义

只返回符合 BR-LGN-004 的同账号有效会话：Session 未撤销、未到期且当前所引用凭据及认证来源有效。过期、已撤销或凭据已撤销的历史记录不显示；未知认证方法、损坏的来源记录、缺失或跨账号凭据不是普通失效，按依赖/数据异常失败关闭，不能伪装成完整列表成功。

正常最多 10 条有效会话，数量语义引用 [BR-LGN-010](UC-AUTH-007-login.md#br-lgn-010)。仍提供有界分页以覆盖合法历史超额状态，不能为了返回列表偷偷执行 LRU 或截掉数据而不提供 nextCursor。排序固定为 `(createdAt DESC, sessionId DESC)`，不按易变的 lastUsedAt 排序；isCurrent 由与当前 Session ID 比较得出。

cursor 为上页最后扫描的候选 sessionId，由服务端 nextCursor 指定，可能不在 sessions 中。服务端按当前 authId 定位游标记录，以其不可变 createdAt/sessionId 作为排他排序边界；该记录后来过期/撤销仍可作锚点，但不再进入有效列表。未知、非本人或已物理清理的合法游标统一 INVALID_SESSION_CURSOR，客户端重新查询第一页。每页有独立 observedAt，不承诺跨页数据库快照；分页期间的新会话由重新查询第一页发现，不能据此构造“原子全部在线设备清单”。

每页最多处理 200 条同账号排序候选，凭据按候选批量加载；达到 pageSize 后停止，或扫描预算耗尽后返回已取得的有效项。若仍有后续候选，nextCursor 为最后实际处理的候选 ID；允许不足页甚至空 sessions 但有 nextCursor，客户端须继续翻页，只有空 nextCursor 才表示扫描结束。至多多读一条候选用于判断后续是否存在，不将它作为已处理游标。正常撤销/过期/旧账号版本候选过滤；已选中候选的损坏或跨账号来源仍失败关闭。此规则避免历史数据增长造成单次无界扫描，也不把预算耗尽伪装成没有其他有效 Session。

查询不更新调用者或任何被列举会话的 lastUsedAt、expiresAt、credential 使用时间或容量；可使用必要的内部一致性栅栏，但不得调用会顺带 touch 的普通 Session 检查路径。与 UC007 的“查询会话列表不刷新”规则保持一致。lastUsedAt 是 Auth 最近一次成功权威会话检查时间，不是设备在线心跳；列表中的有效记录也可能来自客户端未收到响应的成功登录。

<a id="br-lgn-021"></a>
### BR-LGN-021：明确目标集合的幂等回收

撤销输入是确定的 1..50 个 sessionIds，既支持单条也支持批量。不提供隐式“每次执行时删除所有其他会话”的命令；客户端可从已展示的列表选取非当前 ID 实现回收所选或回收所见其他会话。新登录创建了不同 ID 的会话，不能因旧操作网络重试而被顺带撤销。

语法非法、重复 ID、空集合、超限或包含当前 Session 均拒绝整个请求，不产生部分撤销。有效调用者提交的合法目标 ID，若属于别人、不存在或已被清理，与已撤销目标返回相同空成功结果，不披露其存在性、归属或逐条结果。存在的本人未撤销目标即使已经过期或其凭据已撤销，也允许补写 revokedAt；首个撤销时间永不覆盖。

成功只保证明确目标集合中属于调用者账号的 Session 已撤销或不存在；不对他人会话作出状态保证，也不保证同账号“以后没有其他会话”。相同目标集合重复请求保持状态幂等，不需新增操作幂等键或保留可恢复的秘密响应；调用者 Session 在重试前失效仍必须返回认证失败，不能为幂等而跳过鉴权。结果未知时可以使用仍有效的本人 Session 重试同一目标集合；不得自动重新列出更多 ID 后扩张重试范围。

<a id="br-lgn-022"></a>
### BR-LGN-022：回收与登录检查的原子顺序

本用例的列表与回收均不刷新 lastUsedAt 或延长 expiresAt；管理鉴权只作有效性复核。

每个批量命令的当前身份复核、全部目标撤销及审计共用 Auth 现有认证事务栅栏，并与 UC007 登录/LRU/在线检查、UC008、UC009 和 UC010 签发保持明确先后顺序。不能用单独的无事务 UpdateMany 代替整个授权和提交过程，也不能对每个目标分别提交后返回整体成功。数据库冲突按现有事务策略重试，重新复核身份/目标，重试保留相同 ID 集合与候选审计标识。

撤销提交后才开始的会话检查和新 USER JWS 签发必须失败；先完成的检查/签发仍按 UC008 与 UC010 的在途请求、短期 JWS 边界处理，不承诺终止已经开始的业务或立即使离线验签结果失效。

新登录在批量提交之前或之后发生，都只可能被撤销显式列出的 sessionId；同一凭据随后新建的不同 Session 不继承旧 revokedAt。并发 LRU 和手动回收只写一次首次撤销时间，不复活会话、不扩大目标集合；事务回滚不留下部分目标失效或孤立的成功审计。正常失效记录按 UC007 不占有效容量，不等待物理删除。

<a id="br-lgn-023"></a>
### BR-LGN-023：会话回收与设备、OAuth 生命周期隔离

本用例不撤销 credential，也不要求或声称能够删除远端私钥。被回收的设备若仍控制有效密钥，可以按 UC007 再次登录（包括客户端自动登录）；因此此能力不是“禁止该设备再次访问”。需要阻断某个凭据继续登录时，由用户另外明确调用 UC009；不能把会话回收暗中升级成凭据撤销。

一条凭据可能拥有多个 Session，同一台物理设备也可能有多条凭据；首版不提供未经验证的设备聚合或设备名称。平台 Session 回收不撤销第三方 OAuth grant/access/refresh family，相关控制继续使用 UC018；不改变资料、邮箱、Developer/Reviewer 权限或学生关联。

<a id="br-lgn-024"></a>
### BR-LGN-024：有界处理、审计与错误

两个入口共用有界请求限额，默认全局 600 次/分钟、每 socket 来源 120 次/分钟、每已认证 authId 30 次/分钟，最多 4096 个细分桶；部署参数必须为有限正整数。账户额度仅在身份确认后计算且事务重试不重复扣减，不信任客户端 forwarded header；桶满拒绝新增桶请求，过期桶可回收。返回限流时携带 Retry-After=60；不声明单进程限流可以跨重启保留。

真实撤销产生一条不可变批量审计，包含事件 ID、action=REVOKE_OWN_SESSIONS、可信 actorAuthId、actorSessionId、本次首次撤销的本人目标 ID 和统一时间；不记录他人/未知目标归属或 token。无实际变化的重试不再创建撤销事件。审计失败则整批回滚，提交未知返回不可用；读取列表不写业务审计和使用时间。

| 原因 | reason | HTTP / gRPC |
| --- | --- | --- |
| 列表参数/目标集合或 ID 形状非法 | `INVALID_SESSION_MANAGEMENT_REQUEST` | 400 / INVALID_ARGUMENT |
| 未知、非本人或已清理的列表游标 | `INVALID_SESSION_CURSOR` | 400 / INVALID_ARGUMENT |
| 撤销集合含当前 Session | `CURRENT_SESSION_NOT_ALLOWED` | 400 / INVALID_ARGUMENT |
| 缺少或畸形 Session、混合认证载体 | `INVALID_SESSION_TOKEN` | 400 / INVALID_ARGUMENT |
| Session 失效、账号/凭据不可用 | `SESSION_INVALID` | 401 / UNAUTHENTICATED |
| 限流/细分桶容量耗尽 | `SESSION_MANAGEMENT_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 存储、损坏数据、审计失败或提交未知 | `SESSION_MANAGEMENT_UNAVAILABLE` | 503 / UNAVAILABLE |

凭据与认证来源的内部失败原因不向终端细分。撤销响应不返回逐项 owner、affectedCount 或敏感记录；列表/命令正文和 token 不进入常规日志。每页数据库候选处理须有界，并使用 owner/排序索引及批量凭据复查，不能因失效历史增长而逐条无界扫描；不能为避免依赖错误而返回伪造的空列表。

## 测试与验收

1. 设备登录和邮箱登录 Session 均能管理本人会话；不同 authId 即使同 associationId 也不能读到对方列表或改变其记录。
2. 列表包含当前和其他有效会话，isCurrent/currentSessionId 一致，认证方法和时间来自权威记录；无 token/digest/邮箱/设备指纹等额外信息。
3. 过期、撤销和撤销凭据下的会话不显示；损坏/跨账号来源、未知方法、存储错误失败关闭；列表不改变任何 lastUsedAt 或 expiresAt。
4. 默认页大小、上下界、稳定同时间排序、合法历史超额分页、锚点撤销后续页、跨账号/未知/清理游标、并发新增与重新查询第一页。
5. 单条和批量撤销释放有效容量；首次 revokedAt 保留；不存在、他人、已撤销和已清理目标同形成功且不触碰他人记录。
6. 包含当前 Session、重复/畸形 ID、空集合、超过 50 条或严格 JSON 错误时整批拒绝，没有部分写入。
7. 双重回收、回收与登录/LRU/在线检查/当前 Session 撤销/凭据撤销竞争；先失效的调用者不得授权成功，新 Session ID 不被旧批次重试误伤。
8. 全部目标与审计同时提交；注入中途失败、事务重试、审计失败和未知提交，验证回滚/幂等及无假成功。
9. 回收后旧 Session 在线检查/UC010 签发失败，其他 Session 保持；同凭据可再次登录，新 Session 不被旧集合重试撤销。
10. 回收列表中的全部非当前会话仍保留当前会话；OAuth UserInfo/refresh 不因平台 Session 回收失效，UC018 撤销边界独立。
11. 真实 Mongo/Wire、HTTP 与生成 gRPC 客户端、精确方法鉴权、无效载体、限流及记录脱敏；Gateway 对新 DIRECT 路由另行联合验收。

## 依赖与交付边界

UC007/008/009/010/012 的后端依赖已交付。实现需新增无 lastUsedAt 副作用的 Session 管理鉴权读取路径，复用完整有效性校验及事务栅栏，不能复制一个遗漏 EMAIL_CODE_AND_DEVICE 的简化检查器。需补充 owner/createdAt/sessionId 查询索引、批量命令审计及限流；不要求 Redis、学校权威接口或新的学生身份校验。

列表与命令设计属于本 UC，同一账号的设备凭据列表、远端持久退出策略和跨账号关联组管理仍另立用例。本用例已 ACCEPTED；脚本生成实施 brief 并交付 Proto、适配器与验证，不以设计接受代替部署启用。独立 `AUTH_SESSION_MANAGEMENT_ENABLED` 默认 false；开启要求用户入口启用。限额配置为 `AUTH_SESSION_MANAGEMENT_GLOBAL_PER_MINUTE=600`、`AUTH_SESSION_MANAGEMENT_SOURCE_PER_MINUTE=120`、`AUTH_SESSION_MANAGEMENT_ACCOUNT_PER_MINUTE=30`、`AUTH_SESSION_MANAGEMENT_MAX_BUCKETS=4096`，有限正整数上限 1000000。正文/原生消息统一 16 KiB；过大视为 INVALID_SESSION_MANAGEMENT_REQUEST（400），不新增另一组业务 reason。

## 变更记录

- 2026-10-04：提出同 authId 会话列表与显式集合回收；保持当前退出/凭据撤销独立，明确 LRU 只读、分页、原子批量、重试不扩大目标及跨账号边界。

- 2026-10-05：接受并启动实现；明确 200 条候选扫描预算、可继续的短页/空页游标、默认关闭开关和固定入口限额；沿用已交付的只读 Session 检查及账号版本，不增加 Redis 或学生身份依赖。
