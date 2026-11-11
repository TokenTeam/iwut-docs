# UC-AUTH-039：管理员搜索用户

状态：`ACCEPTED`。2026-11-08 用户明确接受；依赖检查通过，生成 brief 后实施。

## 目标与范围

完整平台管理员通过 Auth ID 或当前已验证的完整邮箱精确定位人员治理目标，取得最小账号摘要。该读取只服务 Admin 治理。转让对象继续使用 opaque Auth ID，Developer 的转让流程沿用 App 现行规则。

本用例归属 Auth 用户目录。App 的平台 Application 目录读取权限见 [UC027](UC-AUTH-027-manage-application-operations-permissions.md#proposed-application-search)。两者分别鉴权。

## 参与者与前置条件

操作人经既有 SESSION → Auth audience USER JWS 链进入。入口要求精确 `auth.account.manage`，最终认证事务中按 [UC021](UC-AUTH-021-manage-platform-administrators.md) 复核 ACTIVE 账号、当前 accountRevision 与完整四项平台管理员资格。Developer、Reviewer、App 运维或搜索权限单独均不足以读取用户目录。

依赖 UC011 的当前邮箱目录、UC022 的账号状态与认证代际、UC002 的 Developer 状态值，以及 UC025 的 CLOSED 最小保留模型。查询不要求目标具有邮箱、恢复能力或 Developer 资格。

## 输入与输出

精确服务 `auth_center.v1.managed_user_search.ManagedUserSearchService/SearchUsers`，提供原生 gRPC 和 HTTP/JSON `POST /v1/managed-users:search`。可执行 Proto 由 Auth API 工作分支固定。

```text
SearchUsersRequest {
  oneof selector {
    authId: string
    email: string
  }
}
ManagedUserSummary {
  authId: string
  accountStatus: ACTIVE | DISABLED
  developerStatus: nullable DeveloperStatus
}
SearchUsersResponse { items: ManagedUserSummary[], asOf: UTC timestamp }
```

两种输入均最多命中一个用户，结果稳定为 `[]` 或单项数组。首期无 pageSize、pageToken、offset、排序或 totalCount。完整地址全局唯一，精确 Auth ID 全局唯一，因此无需分页。空查询、两个 selector、前缀、通配、名字筛选、批量目标或分页字段按非法输入拒绝。

## 业务规则

<a id="br-usr-001"></a>
### BR-USR-001：治理专用且在线复核

先校验可信身份及当前完整管理员资格，再校验业务输入和定位目标。App audience、service/OAuth 凭据、部分管理员权限集合及失效账号代际均不能充当此入口的管理身份。旧管理 JWS 在管理员撤权提交后发起的新查询必须拒绝。

管理者撤权、账号变化与查询使用既有 Auth 认证事务协调边界确定提交顺序。查询先确认提交可返回该次观察；撤权先提交时后续查询不得返回人员结果。该在线检查独立于短期 JWS 的剩余有效期。

<a id="br-usr-002"></a>
### BR-USR-002：精确选择与当前绑定

Auth ID 按既有治理 ID 边界验证，非空、合法 UTF-8、最多 256 字节、无首尾空白，原值精确匹配。不改变大小写、不 trim 后匹配、不从 ID 格式推导身份。

邮箱使用 [UC011 的地址规范化与唯一性](UC-AUTH-011-set-and-activate-email.md#br-eml-002)。去首尾 ASCII 空格、验证现有 ASCII 地址语法后完整地址转小写；保留 `+tag` 和点号，沿既有规则处理长度及非法地址。只在现行 v3 已验证绑定中精确查找，登录邮箱和非登录已验证邮箱均可定位同一账号。待验证操作、解绑后的历史、已退役邮箱记录不参与搜索。

邮箱绑定命中后先核对归属主体。合法 CLOSED 主体按 BR-USR-003 排除；ACTIVE/DISABLED USER 须在同次观察验证绑定与当前目录的归属、唯一性和结构。合法地址没有绑定返回空结果；悬空绑定、重复地址或应有目录损坏返回不可用。邮箱角色、解绑或换绑并发时只能返回合法提交顺序中的一个当前绑定结果。

<a id="br-usr-003"></a>
### BR-USR-003：最小披露与账号状态

仅返回 ACTIVE、DISABLED USER 的 authId、accountStatus 和 developerStatus，Developer 状态沿用 [UC002](UC-AUTH-002-batch-get-developer-statuses.md) 的合法枚举，未申请为 null。按 Auth ID 定位不读取邮箱或动态 Profile，用户没有可用展示名也能被定位。

合法 SYSTEM、CLOSED 或不存在的 Auth ID 返回成功空数组。命中合法 CLOSED 主体的待清理邮箱同样返回空数组；依照 UC025 保留和清理，不能据历史邮箱追踪已注销账号。目标应有的主体、状态或 Developer 结构损坏返回不可用。

返回内容不含邮箱地址或地址列表、姓名等动态 Profile、学号、校园依据、Developer handle、权限集合、认证材料或账号生命周期收据。搜索摘要不含可用于写入的 revision；选中目标后使用现有专用治理 Get 获取当前版本及状态，再执行正式命令。

<a id="br-usr-004"></a>
### BR-USR-004：一致观察与有界读取

每次查询在同一 Auth 认证事务边界取得操作人资格、必要目标事实、邮箱归属和服务端 asOf。只按 Auth ID 或规范邮箱唯一索引定位，检测重复命中最多读取两条；命中邮箱后复用最多十条已验证绑定的有界目录核对。保持目标账号、邮箱、权限及 Session 的业务数据不变，在线管理者复核沿用既有认证栅栏。

成功提交后才释放结果，存储故障、记录损坏或提交结果未知返回不可用。未知目标的成功空集合与依赖失败有明确区别。结果只是该次观察，后续换绑、禁用、退出或权限变化由正式治理命令重新判断。

<a id="br-usr-005"></a>
### BR-USR-005：输入、限流与秘密边界

请求上限 16 KiB，拒绝 query string、未知字段、重复字段和重复 oneof 分支。完整邮箱只进入请求体；访问日志不记录原始请求体、selector 值、邮箱、Session 或 JWS。结构化访问日志可记录 actorAuthId、方法、selector 类型、命中数量、结果分类和 traceId，复用现有日志保留配置。

按已认证 actorAuthId 有界限流，初始每分钟 60 次、最多 4096 个桶；容量耗尽也返回限流，不创建按邮箱或目标 ID 增长的桶。成功和错误均 private, no-store。入口由独立默认关闭的 `AUTH_MANAGED_USER_SEARCH_ENDPOINTS_ENABLED` 控制，启用要求既有用户端点与身份签发配置可用。

## 错误语义

| 条件 | reason | HTTP / gRPC |
| --- | --- | --- |
| 缺失或无效 USER 身份、代际过期 | `USER_IDENTITY_REQUIRED` / `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 当前不具备完整平台管理员资格 | `MANAGED_USER_SEARCH_FORBIDDEN` | 403 / PERMISSION_DENIED |
| selector、编码或输入非法 | `INVALID_MANAGED_USER_SEARCH_REQUEST` | 400 / INVALID_ARGUMENT |
| 请求体超过上限 | `MANAGED_USER_SEARCH_REQUEST_TOO_LARGE` | 413 / RESOURCE_EXHAUSTED |
| 合法输入无可披露 USER 命中 | — | 200 / OK，items=[] |
| 超过额度或限流桶容量 | `MANAGED_USER_SEARCH_RATE_LIMITED` | 429 / RESOURCE_EXHAUSTED |
| 权威数据损坏、存储或事务故障 | `MANAGED_USER_SEARCH_UNAVAILABLE` | 503 / UNAVAILABLE |

## 依赖与交付检查

现有 Auth ID 唯一索引、邮箱唯一索引、v3 目录、主体状态及管理员事务复核可复用。新增精确 RPC、Proto/HTTP 严格解码、查询编排和默认关闭配置。首版无需搜索索引服务、数据迁移、目录副本或新的人员权限。

由 Auth/API owner 实施并固定 API 版本，Gateway owner 加入精确 SESSION → Auth audience 的 Admin surface，Console owner 消费最小摘要并继续调用专用治理 Get。共享路由契约由对应所有者同步。本设计不占用当前 App UC050 的 Proto/生成物工作窗口。

## 验收

1. Auth ID 原值定位；完整邮箱大小写及外侧 ASCII 空格按既有规则归一化；`+tag`、点号及两个用户不同地址保持独立。登录角色切换不改变其他已验证绑定的可搜索性。
2. ACTIVE/DISABLED、未申请 Developer、全部合法 Developer 状态、SYSTEM/CLOSED/未知目标，以及缺失/损坏结构和目录归属不一致。
3. 普通 USER、Developer、Reviewer、仅 App 搜索或运维权、部分管理员、错误 audience、失效代际和撤权前签出的旧 JWS；未授权先于目标读取。
4. 查询与管理员撤权、账号变化、邮箱解绑和新归属竞争，结果符合真实提交顺序；故障不返回成功空集合，查询不改变目标业务状态。
5. 空选择、双选择、未知/重复字段、非法邮箱、超长输入、限流和 private/no-store。真实 Mongo、生产 Wire 和生成 HTTP/gRPC 客户端完成验收。
