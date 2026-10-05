# UC-AUTH-005：用户编辑自己的资料

状态：`ACCEPTED`

## 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

> 已认证且账号可用的普通用户，明确提交要设置和删除的资料字段，在不覆盖其他客户端修改的前提下，一次性更新自己的资料。

本用例承接用户已确认的资料定位、字段定义方向，以及“主体内嵌基础资料”的存储方向。命令细节、容量限制和错误语义已接受；实际字段目录及生产接入仍按交付依赖推进。本文件是本用例与 `BR-UPF-*` 的唯一规则正文；此前设计笔记转为导航和示例。

本用例不注册用户、不修改登录凭据、不建立学校身份认证，不授予 Developer/Reviewer 权限，也不授权第三方应用读取资料。资料编辑不要求 Developer 资格。

## 参与者与前置条件

- 调用者通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 提供面向 Auth Center 的有效用户身份；本能力的目标 audience 为 `iwut-auth-center`。
- 从可信身份提取 authId，读取 Auth 自有的 USER 主体及当前 accountStatus；具体规则见 [BR-UPF-004](#br-upf-004)。
- 普通 USER 创建流程已建立 accountStatus 和初始 profile。该创建流程仍是独立实现依赖，本用例不隐式 provision、不在资料缺失时猜测初始状态。
- 使用 set 时，Auth 能提供符合 [BR-UPF-002](#br-upf-002) 的已发布字段定义。

用户先通过[资料编辑配套查询](../query-contracts/user-profile-editing.md)读取自己的资料和字段目录，在客户端编辑、预览并明确提交。本地教务导入只辅助填写，规则见 [BR-UPF-001](#br-upf-001)。

## 输入

```text
EditOwnUserProfileCommand {
  expectedRevision: int64
  set: []ProfileFieldAssignment
  remove: []FieldKey
}

ProfileFieldAssignment {
  key: FieldKey
  value: ProfileValue
}

ProfileValue = exactly one of {
  stringValue: string
  integerValue: int32
  booleanValue: bool
  dateValue: YYYY-MM-DD
}
```

authId 来自可信上下文，不接受请求中的目标用户 ID。客户端不提交 profile revision 的新值、时间戳、账号状态或资格/权限；这些都不是可编辑字段。

set 使用带显式类型的条目列表，便于 transport 保留并拒绝重复 key，也能区分 DATE 与普通 STRING。JSON/Proto 的最终线格式由独立 API 仓库落实，不能使用丢失字段存在性或类型信息的转换。缺少 value、null、同时指定多个值分支均为无效输入；`false`、`0` 有明确的值存在性。

示意命令（不是已发布 HTTP 请求契约）：

```json
{
  "expectedRevision": 3,
  "set": [
    {
      "key": "education.school_name",
      "value": { "stringValue": "示例大学" }
    }
  ],
  "remove": ["education.enrollment_year"]
}
```

示例字段不是生产收集清单。expectedRevision、操作集合和容量边界分别见 [BR-UPF-005](#br-upf-005)、[BR-UPF-007](#br-upf-007)、[BR-UPF-008](#br-upf-008)。

## 输出

```text
EditOwnUserProfileResult {
  changed: bool
  profile: OwnUserProfileSnapshot
}

OwnUserProfileSnapshot {
  entries: []ProfileFieldAssignment
  revision: int64
  updatedAt: Instant
}
```

profile 是本次操作在其原子确认点得到的完整资料快照，entries 按 key 的 ASCII 字典序排列，不因客户端只提交部分字段而省略其他已有字段。并发请求可以在本次操作完成后继续修改；该返回值不宣称是客户端收到响应瞬间的最新状态。

只返回资料，不混入主体权限、凭据、会话或第三方 consent。写入后的返回值由同一次更新返回，或由成功提交的确定性候选快照构造，不再通过无版本约束的第二次读取拼接结果。

## 主流程

1. 验证用户可信身份，取得 authId。
2. 校验命令形状、expectedRevision、操作数量、key 语法、类型分支与输入容量；结构不合法不访问资料仓储。
3. 读取主体和嵌入的 profile，确认存在、类型为 USER、账号 ACTIVE、存储结构完整。
4. 确认当前 profile.revision 等于 expectedRevision；过期版本立即冲突，不因为目标值碰巧相同而成功。
5. 对 set 批量取得本次使用的一致字段定义视图，校验每个赋值；remove 按 [BR-UPF-006](#br-upf-006) 处理。
6. 在内存中从当前完整快照计算候选资料：保留未涉及的值，执行显式删除和设置，检查最终容量。
7. 按 [BR-UPF-009](#br-upf-009) 判断是否真实变化；变更分支按 [BR-UPF-010](#br-upf-010) 原子确认当前账号状态与版本，并一次性提交 profile。no-op 分支执行最后一次带相同身份、状态和版本条件的权威读取确认。
8. 返回 changed 和对应完整资料快照。

任一步业务校验失败均不提交任何资料变更。数据库超时或网络中断可能使提交结果不确定，不能将此类失败宣称为“必定没有写入”；客户端恢复规则见 [BR-UPF-009](#br-upf-009)。

## 业务规则

<a id="br-upf-001"></a>
### BR-UPF-001：主动提交与资料信任边界

资料是用户主动提供的学生资料，平台校验格式，不保证真实性。客户端从教务系统拉取内容后在本地展示，用户可以选择、修改或取消；只有明确提交的值进入本命令。平台不因启动客户端、登录或本地取数成功而隐式上传或自动刷新资料。

学校密码、登录 cookie 和原始教务响应不属于本资料能力，平台字段目录不得为这些凭据建立上传字段。客户端声明来源不能自动形成 verified 身份或平台资格。服务端的“格式校验成功”也不证明用户界面已完成确认，客户端交互需要独立验收。

上传资料与向应用授予读取权限是不同动作。本用例不改变应用授权，也不自动为新字段扩张既有访问权限；Scope 的边界引用 [BR-SCP-004](UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。

<a id="br-upf-002"></a>
### BR-UPF-002：平台字段定义与稳定标识

Auth 拥有共享 ProfileFieldDefinition：`key`、`label`、`description`、`valueType`、`constraints` 五项均存在；label 和 description 是非空有效 UTF-8 文本。字段定义不包含某位用户的值，不要求每位用户填写，也不隐含应用读取授权。

key 在目录中唯一，长度为 1–128 ASCII bytes，符合 `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$`。按完整原始字符串比较；点只用于名称组织，不表示对象路径或权限继承。

已发布 key、业务含义、valueType 和 constraints 在首版保持不变，key 不更名、不复用。展示文案可以修正但不改变含义。首版允许新增定义，不提供在线停用、删除或修改已发布校验规则的管理命令；这些变化由后续用例定义兼容和数据清理规则。

首版定义可由 Auth 自有、纳入版本管理的部署配置显式装载；启动时验证整个目录的唯一性、语法和类型约束，无效配置阻止该服务实例接流量。发布流程保留全部既有定义及其校验含义，不用客户端提交的 schema、测试 fixture 或 Scope 列表代替字段目录。一次 set 校验使用一个完整一致的定义视图，定义不完整或损坏时失败关闭。

<a id="br-upf-003"></a>
### BR-UPF-003：字段值类型与声明式校验

| valueType | 值 | constraints |
| --- | --- | --- |
| `STRING` | 有效 UTF-8 文本 | `maxLength` 必填；`minLength` 可选、默认 1；二者为正整数且 min <= max，按 Unicode code point 计数。 |
| `INTEGER` | 有符号 32 位整数 | 可选 `minimum`、`maximum`，均为该类型范围内的整数且包含端点；同时存在时 minimum <= maximum。 |
| `BOOLEAN` | true 或 false | 空对象。 |
| `DATE` | 0001–9999 年范围内的真实公历日期，格式严格为 `YYYY-MM-DD`，无时区 | 空对象。 |

未知类型、未知或错配 constraints 为无效定义。字段值分支必须与 valueType 一致；null、数组、对象、任意脚本、隐式字符串转数字、默认值填充均不支持。不 trim、不折叠大小写、不做 Unicode 规范化；空格属于原始内容并计入长度，STRING 不能用空字符串表示删除。日期校验包含闰年和真实月份天数。

这些类型只定义基础格式。学号等带前导零的标识应定义为 STRING；不得由 INTEGER 或字段值自动推导身份资格。

<a id="br-upf-004"></a>
### BR-UPF-004：仅当前可用用户编辑本人资料

目标 authId 只能来自通过 trusted-identity-v1 验证的用户身份。本用例不接受服务身份作为用户，不提供管理员代填，也不接受客户端指定其他用户。Developer 状态及 Reviewer permissions 不构成本用例的授权前提。

Auth 当前持久化主体必须为 USER 且 accountStatus 为 ACTIVE。SYSTEM 拒绝；未知主体返回 NotFound；DISABLED 拒绝。accountStatus 缺失或非法、profile 缺失或损坏都视为依赖数据不可用，不默认为 ACTIVE，不自动补空资料。有效的旧身份凭证不绕过此处的当前账号检查。

账号禁用命令需要写入同一主体的 accountStatus；其操作权限、会话撤销和完整生命周期不在本用例中定义。

<a id="br-upf-005"></a>
### BR-UPF-005：显式设置与删除

set 对每个 key 新增或替换一个完整标量值；remove 删除列出的 key。未在两者出现的资料保持原样。

set 内重复 key、remove 内重复 key、set/remove 相交均拒绝整个命令，不采用“最后一个值获胜”或指定执行顺序来消除歧义。至少提供一个操作；缺省操作列表按空列表处理，但不得用 null 列表或含 null 条目替代有效结构。

删除一个已经不存在的合法 key 本身没有副作用。null、空字符串和漏传 key 不代表删除。不提供 `clearAll` 通配符，清空资料由客户端在读取当前快照后显式列出待删 key，并仍携带 expectedRevision。

<a id="br-upf-006"></a>
### BR-UPF-006：写入校验与删除独立

每个 set key 必须存在于本次已发布字段定义视图，且值满足对应定义。未知 key、类型或约束不满足时整体失败；不能跳过无效字段后部分成功。

remove 只检查 key 语法和命令边界，不要求 key 仍在目录中；它只能删除已有值或成为 no-op，不能引入新资料。纯 remove 不依赖字段目录可用性。这也允许用户清理未来迁移遗留的未知字段。

未编辑的历史值不因本次命令而重新按当前目录校验或自动清除；仓储结构本身仍需完整有效。混合 set/remove 请求只要 set 校验失败，删除也不提交。

<a id="br-upf-007"></a>
### BR-UPF-007：操作与资料容量上限

首版容量规则如下，不能由每个客户端自行改变：

| 项目 | 上限 |
| --- | --- |
| 单次 set 条目数与 remove key 数之和 | 128 |
| 变更后资料字段总数 | 64 |
| 变更后资料逻辑容量 | 32 KiB（32768 bytes） |
| 单次命令逻辑容量 | 64 KiB（65536 bytes） |

逻辑容量统一计算：每项加上 key 的 UTF-8 byte 数；STRING 值计 UTF-8 bytes，INTEGER 计 4 bytes，BOOLEAN 计 1 byte，DATE 计 10 bytes。资料容量对最终全部条目求和；命令容量对所有 set 的 key/value 和所有 remove 的 key 求和。revision、JSON 标点、类型标签和 BSON 元数据不计入此业务度量，因此它不等于传输大小或 BSON 大小。

客户端收到具体字段约束时，也需要知道这些全局上限。字段定义允许的单值长度不能绕过总容量。64 个删除加 64 个新增可以在一次命令中完成，只检查最终资料数量，而不把中间临时状态当作最终状态。

transport 另将解压后的单次请求 message/body 限为 128 KiB，并在无界分配前拒绝超限请求；原生 gRPC 按解压后的 protobuf message、HTTP 按解压后的 body 计量。该工程上限不替代应用层的逻辑容量校验。

<a id="br-upf-008"></a>
### BR-UPF-008：资料初始化与乐观并发

普通 USER 创建时初始化逻辑空资料，values 为空，revision 为 1，profile.updatedAt 等于主体 createdAt；本编辑用例只处理已经完成初始化的主体。

expectedRevision 必填且为正 int64。当前版本不匹配则冲突，即使目标值与现有值相同。每次真实变化将 revision 精确增加 1，并将 profile.updatedAt 设为服务端本次提交使用的 UTC 时间；时间戳不承担并发比较，也不保证因时钟调整严格递增。

revision 属于整份资料，与权限版本、目录版本和认证版本相互独立。任何写 profile 的生产路径都遵循本规则，不能绕过版本更新。revision 达到 int64 最大值时拒绝真实变更并报告耗尽，不回绕；合法 no-op 仍可返回原版本。

<a id="br-upf-009"></a>
### BR-UPF-009：无变化与结果不确定的重试

所有校验通过且版本匹配后，候选 key 集合及对应的类型/值与当前资料相同，视为 no-op；条目顺序不影响相等性。no-op 返回 changed=false，revision 和 updatedAt 均不变。重新设置相同值、删除不存在的 key 可以构成 no-op，但空命令仍按 BR-UPF-005 拒绝。

返回 no-op 前以 authId、USER、ACTIVE 和 expectedRevision 执行最后一次权威条件读取；条件不匹配不能返回基于先前快照的成功。该读取是 no-op 的确认点，并发修改或禁用若发生在其后，不追溯否定此前的成功。

首版不提供幂等键或“请求只执行一次”的承诺。真实变更成功后用原 expectedRevision 重放会冲突；已经成功的 no-op 若状态未变，重放仍为 no-op。响应丢失、超时或版本冲突时，客户端重新读取当前资料，让用户确认差异后构造新命令；不得只换成新 revision 自动重放旧意图覆盖其他客户端修改。

<a id="br-upf-010"></a>
### BR-UPF-010：主体内嵌资料与单文档原子提交

基础资料内嵌在 Auth 自有 `auth_principals.profile` 中。USER 的账号状态和资料版本处于同一 document；字段目录独立共享，Session、consent、应用存储和追加式审计不作为此 profile 的组成部分。

仓储把逻辑 KV 保存为有界 `entries` 数组，每项为 `{key, valueType, value}`，按 key 的 ASCII 字典序存放且 key 唯一。key 是数据值，不作为 Mongo 更新路径；带点的名称不会被解释成嵌套字段。STRING/DATE 保存为 BSON string、INTEGER 为 BSON int32、BOOLEAN 为 BSON bool；DATE 由 valueType 区分。仓储读取时拒绝重复 key、未知存储类型或损坏的 profile 元数据，不静默合并或丢弃。

profile.revision 使用 BSON int64，profile.updatedAt 使用 BSON datetime。存储类型、key 语法、标量基本格式和元数据有效性属于结构校验；对未修改的历史值不重复应用当前字段目录的业务约束。内嵌 profile 不重复保存 authId，其归属由外层主体确定。

真实变更使用一次条件更新匹配 `authId + principalType=USER + accountStatus=ACTIVE + profile.revision=expectedRevision`，在同一次操作中写入候选 entries、新 revision 和 profile.updatedAt。禁止 upsert、整份主体替换、由客户端 key 拼接 `$set` 路径，或把部分条目分别提交。

该操作只改变 profile，不覆盖权限、Developer 状态、主体顶层 updatedAt 等其他事实。profile 的变化不能因为权限更新而被丢失，权限更新也不能用旧主体快照覆盖 profile。底层单文档原子性依据见 [MongoDB Atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/)。

若条件更新匹配数为 0，不报告成功，也不自动换版本重试；可通过新的权威读取区分主体不存在、非 USER、DISABLED 和版本冲突。若此时状态已再次变化而无法精确归因，返回并发冲突让客户端重读，不猜测成功。数据库异常返回不可用，未知提交结果按 BR-UPF-009 处理。

禁用先于本次条件更新生效时，本次写入失败；资料更新先完成则可以成功，之后的禁用不撤销已经提交的资料。这是本用例的并发边界，不提供跨所有会话的即时失效承诺。

<a id="br-upf-011"></a>
### BR-UPF-011：资料披露与操作记录

编辑结果和配套“读取本人资料”仅向通过本人身份与当前账号检查的调用者返回资料；不作为第三方应用资料 API，不广播完整资料事件，不自动建立或扩大 consent。

错误详情可以包含请求 key、稳定错误码和约束名，不回显字段值、其他用户资料、凭据或数据库内部结构。常规请求日志不得记录完整请求/响应资料正文。操作日志可记录 authId、requestId、结果和前后 revision；它不是与写入原子提交的不可变业务审计。首版不保存每次编辑的资料历史副本。

## 持久化与返回说明

`auth_principals` 中的 authId、principalType 及主体基础字段继续引用 [UC-AUTH-002 数据模型](UC-AUTH-002-batch-get-developer-statuses.md#数据模型)；权限字段继续引用 [UC-AUTH-004 数据模型](UC-AUTH-004-manage-reviewer-permission.md#数据模型)。本用例需要的增量和原子边界由 BR-UPF-004、008、010 定义。

SYSTEM 不初始化 profile。已有 USER 记录需要由明确的 provision/数据迁移工作包补齐 accountStatus 和 profile 后，才可使用本入口；迁移不能以创建一个虚假的 Developer 状态代替普通用户初始化。

## 异常与 transport 映射

| 原因 | 稳定 reason | HTTP / gRPC |
| --- | --- | --- |
| 用户身份缺失 | `USER_IDENTITY_REQUIRED` | 401 / UNAUTHENTICATED |
| 用户身份无效或 audience 不符 | `INVALID_USER_IDENTITY` | 401 / UNAUTHENTICATED |
| 非 USER 主体 | `USER_PROFILE_ACCESS_DENIED` | 403 / PERMISSION_DENIED |
| 账号已禁用 | `USER_ACCOUNT_DISABLED` | 403 / PERMISSION_DENIED |
| 可信 authId 对应主体不存在 | `USER_PRINCIPAL_NOT_FOUND` | 404 / NOT_FOUND |
| expectedRevision 缺失、非正或超出 int64 | `INVALID_USER_PROFILE_EXPECTED_REVISION` | 400 / INVALID_ARGUMENT |
| 空命令、重复/相交 key、key 格式或值分支非法 | `INVALID_USER_PROFILE_EDIT` | 400 / INVALID_ARGUMENT |
| set key 未发布 | `USER_PROFILE_FIELD_NOT_DEFINED` | 400 / INVALID_ARGUMENT |
| 值类型或约束不满足 | `INVALID_USER_PROFILE_FIELD_VALUE` | 400 / INVALID_ARGUMENT |
| 操作数、业务容量或 transport 大小超限 | `USER_PROFILE_LIMIT_EXCEEDED` | 413 / RESOURCE_EXHAUSTED |
| 版本已变化或无法归因的条件更新失败 | `USER_PROFILE_REVISION_CONFLICT` | 409 / ABORTED |
| revision 耗尽且请求需要真实变更 | `USER_PROFILE_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 定义目录暂不可用或无效 | `PROFILE_FIELD_CATALOG_UNAVAILABLE` | 503 / UNAVAILABLE |
| 账号/profile 数据缺失损坏、数据库暂不可用 | `USER_PROFILE_UNAVAILABLE` | 503 / UNAVAILABLE |
| 未预期内部异常 | `INTERNAL_ERROR` | 500 / INTERNAL |

表中的自定义 reason 由应用 adapter 映射；发生在框架解码之前的畸形请求或传输大小拦截，至少保持对应标准状态，不能承诺所有框架路径都返回同一结构化业务 reason。

业务错误判断顺序按主流程；身份认证优先于领域处理，基础传输大小限制可更早执行。当前账号检查先于版本冲突，版本检查先于字段目录校验；不依靠错误文本让客户端判断结果。详细校验只返回一个确定错误时，key 按 ASCII 字典序选择首个失败项。

## API 与交付依赖

- 这是经 Gateway 的用户能力，使用用户可信身份，不使用内部服务 identity 或单凭 service allowlist 授予编辑权。
- 候选 API 包为 `auth_center/v1/user_profile/`，方法为 `EditOwnProfile`；配套读取语义见查询契约。可执行 Proto、路由和 Gateway 到 Auth 的认证引导链路由实现工作包补齐，不能以未认证临时入口代替。
- `expectedRevision` 在逻辑命令中只有一个来源；首版各 transport 映射该显式字段，不再同时接受另一套 `If-Match` 前置条件。
- 登录、普通 USER provision、账号初始化/迁移、字段目录的实际初始内容和用户端确认页面仍需交付；本设计完成不代表生产链路已可用。

## 测试与验收

1. 普通 ACTIVE USER 可以新增、替换、删除本人字段；无 Developer 资格不影响操作。
2. 无效身份、SYSTEM、未知主体、DISABLED 均拒绝；请求不能选择其他 authId 或修改权限/账号状态。
3. 空资料初始化遵循 BR-UPF-008；读取或编辑不能静默修复缺失 profile/accountStatus。
4. STRING 边界按 code point、总容量按 UTF-8 bytes；INTEGER 边界、false、0、合法闰日、非法日期、类型错配及 null 都有验收样例。
5. 重复 set、重复 remove、set/remove 相交、空命令和未知 set key 整体失败，无部分删除或写入。
6. 删除不存在的合法 key 可以 no-op；删除现存未知目录 key 可以成功；纯删除在字段目录不可用时仍可执行。
7. 混合请求在目录或 set 校验失败时，remove 也不提交；未触及的历史值不被自动清除。
8. 字段数与容量恰好达到上限成功、超过一项失败；64 删加 64 新增按最终状态判定；大请求在无界解析前被拦截。
9. 相同 key/type/value 集合判定 no-op，不改变 revision/updatedAt；stale revision 即使内容相同仍冲突。
10. 两个真实变更使用同一 expectedRevision，最多一个成功；no-op 最终确认与并发真实更新、账号禁用的顺序得到正确处理。
11. 并发权限修改与资料修改不互相覆盖；profile 更新不改主体顶层 updatedAt；带点 key 作为数据保存而非更新路径。
12. 单文档写入失败不出现部分字段修改；网络超时后通过重新读取恢复，不盲目更新 expectedRevision 重放。
13. 返回与本次提交快照一致，条目稳定排序；请求日志和失败响应不泄露资料值。
14. 实现验收使用真实 MongoDB、真实 transport 与生产组合根；客户端单独验收本地导入、预览、选择、取消与明确提交。

## 非目标

- 用户创建、登录、账号禁用管理或注销恢复。
- 在线字段目录管理、类型演进、即时停用字段或字段级多版本。
- 学生真实性核验、资料审核、管理员代填或自动教务同步。
- 第三方应用读取、consent、Session、课程表等结构化业务数据。
- 修改历史、每字段版本、自动合并、全量清空通配符、请求幂等键。

## 变更记录

- 2026-09-22：建立本人资料编辑用例，承接共享字段定义与主体内嵌资料方向，提出显式 patch、容量、并发、no-op 和配套读取语义。
- 2026-09-22：完成接受前检查，接受资料编辑及配套查询的业务规则、容量上限和并发/错误语义；生产字段目录和认证接入作为实现依赖跟踪。
