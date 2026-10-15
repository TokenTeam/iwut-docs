<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->
<!-- python3 tools/gen_brief.py UC-AUTH-005 --spec tools/brief-specs/UC-AUTH-005.json -->
# Brief — UC-AUTH-005：用户编辑自己的资料

> **非权威派生制品。** 本文由脚本从 `docs/auth-center/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。
> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。

## 本次范围

| 项 | 值 |
| --- | --- |
| Use Case | `UC-AUTH-005` 用户编辑自己的资料 |
| 设计状态 | `ACCEPTED`（以 registry 为准） |
| 本 UC 权威 BR | `BR-UPF-001`、`BR-UPF-002`、`BR-UPF-003`、`BR-UPF-004`、`BR-UPF-005`、`BR-UPF-006`、`BR-UPF-007`、`BR-UPF-008`、`BR-UPF-009`、`BR-UPF-010`、`BR-UPF-011`、`BR-UPF-017`、`BR-UPF-018` |
| 外部引用 BR | — |
| ADR | —（未在 spec 中声明） |
| 平台共享 | `platform/contracts/trusted-identity-v1.md` |
| 配套查询 | `auth-center/query-contracts/user-profile-editing.md` |

## 遇到 brief 未覆盖的问题

本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：

1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。
2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：

   ```text
   blocked: true
   authority: <BR-*/UC-*/ADR-* 的权威位置>
   conflict: <一句话描述歧义或冲突>
   options: <可选方案>
   suggested: <建议方案>
   ```

3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。

## 用例正文

### 目标与范围

账号初始化、认证材料版本和 CLOSED 拒绝统一引用 [UC022](../use-cases/UC-AUTH-022-disable-and-restore-user-account.md#br-acc-002) 与 [UC025](../use-cases/UC-AUTH-025-close-own-account.md#br-acc-009)；不得在旧记录缺字段时补默认值或通过历史成功结果复活账号。 账号终止后的最小保留及审计保留期清理由 UC025/BR-ACC-012 定义；append-only 在保留期内成立，期满仅受控清理任务可删除。

> 已认证且账号可用的普通用户，明确提交要设置和删除的资料字段，在不覆盖其他客户端修改的前提下，一次性更新自己的资料。

本用例承接用户已确认的资料定位、字段定义方向，以及“主体内嵌基础资料”的存储方向。命令细节、容量限制、错误语义和首批生产字段目录均已接受；生产配置、客户端和 Gateway 接入仍按交付依赖推进。本文件是本用例与 `BR-UPF-*` 的唯一规则正文；此前设计笔记转为导航和示例。

本用例不注册用户、不修改登录凭据、不建立学校身份认证，不授予 Developer/Reviewer 权限，也不授权第三方应用读取资料。资料编辑不要求 Developer 资格。

### 参与者与前置条件

- 调用者通过 [trusted-identity-v1](../../platform/contracts/trusted-identity-v1.md) 提供面向 Auth Center 的有效用户身份；本能力的目标 audience 为 `iwut-auth-center`。
- 从可信身份提取 authId，读取 Auth 自有的 USER 主体及当前 accountStatus；具体规则见 [BR-UPF-004](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004)。
- 普通 USER 创建流程已建立 accountStatus 和初始 profile。该创建流程仍是独立实现依赖，本用例不隐式 provision、不在资料缺失时猜测初始状态。
- 使用 set 时，Auth 能提供符合 [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002) 的已发布字段定义。
- 设置当前就读年级时，Auth 能从 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 的权威时间表按服务端时间唯一确定当前学年；规则见 [BR-UPF-018](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018)。

用户先通过[资料编辑配套查询](../query-contracts/user-profile-editing.md)读取自己的资料和字段目录，在客户端编辑、预览并明确提交。本地教务导入只辅助填写，规则见 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)。

### 输入

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
  stringSetValue: []string
  academicGradeValue: AcademicGradeValue
}

AcademicGradeValue {
  stage: UNDERGRADUATE | MASTER | DOCTORAL
  year: positive int32
  finalYear: positive int32
  academicYear: int32
  confirmedAt: Instant? // response/storage only
}
```

authId 来自可信上下文，不接受请求中的目标用户 ID。客户端不提交 profile revision 的新值、时间戳、账号状态或资格/权限；这些都不是可编辑字段。

set 使用带显式类型的条目列表，便于 transport 保留并拒绝重复 key，也能区分 DATE、STRING_SET 与普通 STRING。JSON/Proto 的最终线格式由独立 API 仓库落实，不能使用丢失字段存在性或类型信息的转换。缺少 value、null、同时指定多个值分支均为无效输入；`false`、`0` 有明确的值存在性。STRING_SET 是一个完整集合值，不把重复或顺序当作资料内容；ACADEMIC_GRADE 的 `confirmedAt` 只能由服务端生成，请求携带即拒绝。

示意命令（不是已发布 HTTP 请求契约）：

```json
{
  "expectedRevision": 3,
  "set": [
    {
      "key": "education.campus_areas",
      "value": { "stringSetValue": ["NANHU", "JIANHU"] }
    }
  ],
  "remove": ["contact.qq"]
}
```

生产字段清单见 [BR-UPF-017](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017)。expectedRevision、操作集合和容量边界分别见 [BR-UPF-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-005)、[BR-UPF-007](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007)、[BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)。

### 输出

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

profile 是本次操作在其原子确认点得到的完整持久资料快照，entries 按 key 的 ASCII 字典序排列，不因客户端只提交部分字段而省略其他已有字段。STRING_SET 元素按 ASCII 字典序返回。ACADEMIC_GRADE 返回用户最后确认的 stage/year/finalYear、服务端锚定的 academicYear 和 confirmedAt；当前有效年级由 BR-UPF-018 推算，不通过改写快照冒充新的用户确认。并发请求可以在本次操作完成后继续修改；该返回值不宣称是客户端收到响应瞬间的最新状态。

只返回资料，不混入主体权限、凭据、会话或第三方 consent。写入后的返回值由同一次更新返回，或由成功提交的确定性候选快照构造，不再通过无版本约束的第二次读取拼接结果。

### 主流程

1. 验证用户可信身份，取得 authId。
2. 校验命令形状、expectedRevision、操作数量、key 语法、类型分支与输入容量；结构不合法不访问资料仓储。
3. 读取主体和嵌入的 profile，确认存在、类型为 USER、账号 ACTIVE、存储结构完整。
4. 确认当前 profile.revision 等于 expectedRevision；过期版本立即冲突，不因为目标值碰巧相同而成功。
5. 对 set 批量取得本次使用的一致字段定义视图，校验每个赋值；ACADEMIC_GRADE 还校验请求观察的学年仍是服务端当前学年并生成确认时间；remove 按 [BR-UPF-006](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-006) 处理。
6. 在内存中从当前完整快照计算候选资料：保留未涉及的值，执行显式删除和设置，检查最终容量。
7. 按 [BR-UPF-009](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009) 判断是否真实变化；变更分支按 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010) 原子确认当前账号状态与版本，并一次性提交 profile。no-op 分支执行最后一次带相同身份、状态和版本条件的权威读取确认。
8. 返回 changed 和对应完整资料快照。

任一步业务校验失败均不提交任何资料变更。数据库超时或网络中断可能使提交结果不确定，不能将此类失败宣称为“必定没有写入”；客户端恢复规则见 [BR-UPF-009](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009)。

### 异常与 transport 映射

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
| ACADEMIC_GRADE 观察学年不再是当前学年 | `USER_PROFILE_ACADEMIC_YEAR_CONFLICT` | 409 / ABORTED |
| 操作数、业务容量或 transport 大小超限 | `USER_PROFILE_LIMIT_EXCEEDED` | 413 / RESOURCE_EXHAUSTED |
| 版本已变化或无法归因的条件更新失败 | `USER_PROFILE_REVISION_CONFLICT` | 409 / ABORTED |
| revision 耗尽且请求需要真实变更 | `USER_PROFILE_REVISION_EXHAUSTED` | 409 / FAILED_PRECONDITION |
| 定义目录暂不可用或无效 | `PROFILE_FIELD_CATALOG_UNAVAILABLE` | 503 / UNAVAILABLE |
| 学年时间表缺失、损坏、范围溢出或不能解释当前时间 | `ACADEMIC_YEAR_UNAVAILABLE` | 503 / UNAVAILABLE |
| 账号/profile 数据缺失损坏、数据库暂不可用 | `USER_PROFILE_UNAVAILABLE` | 503 / UNAVAILABLE |
| 未预期内部异常 | `INTERNAL_ERROR` | 500 / INTERNAL |

表中的自定义 reason 由应用 adapter 映射；发生在框架解码之前的畸形请求或传输大小拦截，至少保持对应标准状态，不能承诺所有框架路径都返回同一结构化业务 reason。

业务错误判断顺序按主流程；身份认证优先于领域处理，基础传输大小限制可更早执行。当前账号检查先于版本冲突，版本检查先于字段目录校验；不依靠错误文本让客户端判断结果。详细校验只返回一个确定错误时，key 按 ASCII 字典序选择首个失败项。

### API 与交付依赖

- 这是经 Gateway 的用户能力，使用用户可信身份，不使用内部服务 identity 或单凭 service allowlist 授予编辑权。
- API 包为 `auth_center/v1/user_profile/`，方法为 `EditOwnProfile`；配套读取语义见查询契约。实现扩展需要在独立 API Proto 中为 ProfileValue 增加 STRING_SET 与 ACADEMIC_GRADE 分支，并在 schema 投影 options、字符集、集合约束、日期上界和当前 academicYear；路由和 Gateway 到 Auth 的认证引导链路不能以未认证临时入口代替。
- `expectedRevision` 在逻辑命令中只有一个来源；首版各 transport 映射该显式字段，不再同时接受另一套 `If-Match` 前置条件。
- 登录、普通 USER provision、账号初始化/迁移、生产字段/Scope 目录装载、UC029 学年时间表和用户端确认页面仍需交付；本设计完成不代表生产链路已可用。新 key 不要求把说明性测试字段改义；部署若已有同名字段或非规范值，必须在启用前扫描并由显式迁移处理。

### 测试与验收

1. 普通 ACTIVE USER 可以新增、替换、删除本人字段；无 Developer 资格不影响操作。
2. 无效身份、SYSTEM、未知主体、DISABLED 均拒绝；请求不能选择其他 authId 或修改权限/账号状态。
3. 空资料初始化遵循 BR-UPF-008；读取或编辑不能静默修复缺失 profile/accountStatus。
4. STRING 边界按 code point、数字字符集只接受 ASCII `0`–`9`、总容量按 UTF-8 bytes；INTEGER 边界、false、0、合法闰日、未来生日、类型错配及 null 都有验收样例。
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
15. campus 集合拒绝空值、重复和目录外选项，忽略请求顺序并规范输出；一至六个合法片区及 remove 清空均覆盖。
16. 当前年级在学年内稳定、跨学年阶段内递增并在 finalYear 封顶；不自动本科转硕士。休学/留级纠正建立新锚点；旧 academicYear 请求冲突，时间表损坏/不可用失败关闭，学年更新时间到达不批量写 profile。

### 非目标

- 用户创建、登录、账号禁用管理或注销恢复。
- 在线字段目录管理、类型演进、即时停用字段或字段级多版本。学年时间表管理由 UC029 独立拥有。
- 学生真实性核验、资料审核、管理员代填、自动教务同步或自动识别休学/毕业。
- 第三方应用读取、consent、Session、课程表等结构化业务数据。
- 修改历史、每字段版本、自动合并、全量清空通配符、请求幂等键。

## 业务规则（UC-AUTH-005 权威正文）

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001 -->
### BR-UPF-001：主动提交与资料信任边界

资料是用户主动提供的学生资料，平台校验格式，不保证真实性。客户端从教务系统拉取内容后在本地展示，用户可以选择、修改或取消；只有明确提交的值进入本命令。平台不因启动客户端、登录或本地取数成功而隐式上传或自动刷新资料。

学校密码、登录 cookie 和原始教务响应不属于本资料能力，平台字段目录不得为这些凭据建立上传字段。客户端声明来源不能自动形成 verified 身份或平台资格。服务端的“格式校验成功”也不证明用户界面已完成确认，客户端交互需要独立验收。

上传资料与向应用授予读取权限是不同动作。本用例不改变应用授权，也不自动为新字段扩张既有访问权限；Scope 的边界引用 [BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002 -->
### BR-UPF-002：平台字段定义与稳定标识

Auth 拥有共享 ProfileFieldDefinition：`key`、`label`、`description`、`valueType`、`constraints` 五项均存在；label 和 description 是非空有效 UTF-8 文本。字段定义不包含某位用户的值，不要求每位用户填写，也不隐含应用读取授权。

key 在目录中唯一，长度为 1–128 ASCII bytes，符合 `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$`。按完整原始字符串比较；点只用于名称组织，不表示对象路径或权限继承。

已发布 key、业务含义、valueType 和 constraints 在首版保持不变，key 不更名、不复用。展示文案可以修正但不改变含义。首版允许新增定义，不提供在线停用、删除或修改已发布校验规则的管理命令；这些变化由后续用例定义兼容和数据清理规则。

首版定义可由 Auth 自有、纳入版本管理的部署配置显式装载；启动时验证整个目录的唯一性、语法和类型约束，无效配置阻止该服务实例接流量。发布流程保留全部既有定义及其校验含义，不用客户端提交的 schema、测试 fixture 或 Scope 列表代替字段目录。一次 set 校验使用一个完整一致的定义视图，定义不完整或损坏时失败关闭。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-003 -->
### BR-UPF-003：字段值类型与声明式校验

| valueType | 值 | constraints |
| --- | --- | --- |
| `STRING` | 有效 UTF-8 文本 | `maxLength` 必填；`minLength` 可选、默认 1；二者为正整数且 min <= max，按 Unicode code point 计数。可选 `characterSet=ASCII_DIGITS` 要求每个字符为 `0`–`9`；可选 `options` 要求值精确命中一个稳定 option value。 |
| `INTEGER` | 有符号 32 位整数 | 可选 `minimum`、`maximum`，均为该类型范围内的整数且包含端点；同时存在时 minimum <= maximum。 |
| `BOOLEAN` | true 或 false | 空对象。 |
| `DATE` | 0001–9999 年范围内的真实公历日期，格式严格为 `YYYY-MM-DD`，无时区 | 可选 `notAfterToday=true`；today 取服务端当前时间在 `Asia/Shanghai` 的公历日期。 |
| `STRING_SET` | 无序且无重复的非空字符串集合 | `options`、`minItems`、`maxItems` 必填；每项必须精确命中一个 option value，且 `1 <= minItems <= maxItems <= options 数量`。 |
| `ACADEMIC_GRADE` | 用户在某个服务端学年确认的培养阶段、年级和该阶段最后学年 | 空对象；固定结构和推算规则见 [BR-UPF-018](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018)。 |

option 由稳定非空 ASCII value 和非空有效 UTF-8 label 组成，同一定义内 value 唯一；value 发布后不可改名或复用，label 可只改展示文字。未知类型、未知或错配 constraints 为无效定义。字段值分支必须与 valueType 一致；除 STRING_SET 与 ACADEMIC_GRADE 的显式结构外，null、数组、对象、任意脚本、隐式字符串转数字、默认值填充均不支持。不 trim、不折叠大小写、不做 Unicode 规范化；空格属于原始内容并计入长度，STRING 不能用空字符串表示删除。日期校验包含闰年和真实月份天数。

STRING_SET 的请求顺序不构成语义，重复元素或空集合拒绝；服务端按 option value 的 ASCII 字典序规范存储和返回。两个集合成员相同即相等。ACADEMIC_GRADE 不是学校验证事实，也不因时间推算变成验证事实。

这些类型只定义基础格式。学号等带前导零的标识应定义为 STRING；不得由 INTEGER 或字段值自动推导身份资格。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004 -->
### BR-UPF-004：仅当前可用用户编辑本人资料

目标 authId 只能来自通过 trusted-identity-v1 验证的用户身份。本用例不接受服务身份作为用户，不提供管理员代填，也不接受客户端指定其他用户。Developer 状态及 Reviewer permissions 不构成本用例的授权前提。

Auth 当前持久化主体必须为 USER 且 accountStatus 为 ACTIVE。SYSTEM 拒绝；未知主体返回 NotFound；DISABLED 拒绝。accountStatus 缺失或非法、profile 缺失或损坏都视为依赖数据不可用，不默认为 ACTIVE，不自动补空资料。有效的旧身份凭证不绕过此处的当前账号检查。

账号禁用命令需要写入同一主体的 accountStatus；其操作权限、会话撤销和完整生命周期不在本用例中定义。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-005 -->
### BR-UPF-005：显式设置与删除

set 对每个 key 新增或替换一个完整值；remove 删除列出的 key。未在两者出现的资料保持原样。

set 内重复 key、remove 内重复 key、set/remove 相交均拒绝整个命令，不采用“最后一个值获胜”或指定执行顺序来消除歧义。至少提供一个操作；缺省操作列表按空列表处理，但不得用 null 列表或含 null 条目替代有效结构。

删除一个已经不存在的合法 key 本身没有副作用。null、空字符串和漏传 key 不代表删除。不提供 `clearAll` 通配符，清空资料由客户端在读取当前快照后显式列出待删 key，并仍携带 expectedRevision。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-006 -->
### BR-UPF-006：写入校验与删除独立

每个 set key 必须存在于本次已发布字段定义视图，且值满足对应定义。未知 key、类型或约束不满足时整体失败；不能跳过无效字段后部分成功。

remove 只检查 key 语法和命令边界，不要求 key 仍在目录中；它只能删除已有值或成为 no-op，不能引入新资料。纯 remove 不依赖字段目录可用性。这也允许用户清理未来迁移遗留的未知字段。

未编辑的历史值不因本次命令而重新按当前目录校验或自动清除；仓储结构本身仍需完整有效。混合 set/remove 请求只要 set 校验失败，删除也不提交。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007 -->
### BR-UPF-007：操作与资料容量上限

首版容量规则如下，不能由每个客户端自行改变：

| 项目 | 上限 |
| --- | --- |
| 单次 set 条目数与 remove key 数之和 | 128 |
| 变更后资料字段总数 | 64 |
| 变更后资料逻辑容量 | 32 KiB（32768 bytes） |
| 单次命令逻辑容量 | 64 KiB（65536 bytes） |

逻辑容量统一计算：每项加上 key 的 UTF-8 byte 数；STRING 值计 UTF-8 bytes，INTEGER 计 4 bytes，BOOLEAN 计 1 byte，DATE 计 10 bytes；STRING_SET 计全部元素 UTF-8 bytes 之和；ACADEMIC_GRADE 计 stage ASCII bytes 加 year/finalYear/academicYear 各 4 bytes。资料容量对最终全部条目求和；命令容量对所有 set 的 key/value 和所有 remove 的 key 求和。revision、confirmedAt、JSON 标点、数组/类型标签和 BSON 元数据不计入此业务度量，因此它不等于传输大小或 BSON 大小。

客户端收到具体字段约束时，也需要知道这些全局上限。字段定义允许的单值长度不能绕过总容量。64 个删除加 64 个新增可以在一次命令中完成，只检查最终资料数量，而不把中间临时状态当作最终状态。

transport 另将解压后的单次请求 message/body 限为 128 KiB，并在无界分配前拒绝超限请求；原生 gRPC 按解压后的 protobuf message、HTTP 按解压后的 body 计量。该工程上限不替代应用层的逻辑容量校验。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008 -->
### BR-UPF-008：资料初始化与乐观并发

普通 USER 创建时初始化逻辑空资料，values 为空，revision 为 1，profile.updatedAt 等于主体 createdAt；本编辑用例只处理已经完成初始化的主体。

expectedRevision 必填且为正 int64。当前版本不匹配则冲突，即使目标值与现有值相同。每次真实变化将 revision 精确增加 1，并将 profile.updatedAt 设为服务端本次提交使用的 UTC 时间；时间戳不承担并发比较，也不保证因时钟调整严格递增。

revision 属于整份资料，与权限版本、目录版本和认证版本相互独立。任何写 profile 的生产路径都遵循本规则，不能绕过版本更新。revision 达到 int64 最大值时拒绝真实变更并报告耗尽，不回绕；合法 no-op 仍可返回原版本。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009 -->
### BR-UPF-009：无变化与结果不确定的重试

所有校验通过且版本匹配后，候选 key 集合及对应的类型/值与当前资料相同，视为 no-op；条目顺序和 STRING_SET 请求顺序不影响相等性。no-op 返回 changed=false，revision 和 updatedAt 均不变。重新设置相同值、删除不存在的 key 可以构成 no-op，但空命令仍按 BR-UPF-005 拒绝。

ACADEMIC_GRADE 的锚定 academicYear 属于值的一部分：同一当前学年重复设置相同 stage/year/finalYear 是 no-op；进入后续学年后，用户重新提交当前年级会建立新锚点和 confirmedAt，即使推算后的展示代码相同，也是真实变化并增加 revision。这使休学、留级或延期用户能够主动纠正自动推进结果。

返回 no-op 前以 authId、USER、ACTIVE 和 expectedRevision 执行最后一次权威条件读取；条件不匹配不能返回基于先前快照的成功。该读取是 no-op 的确认点，并发修改或禁用若发生在其后，不追溯否定此前的成功。

首版不提供幂等键或“请求只执行一次”的承诺。真实变更成功后用原 expectedRevision 重放会冲突；已经成功的 no-op 若状态未变，重放仍为 no-op。响应丢失、超时或版本冲突时，客户端重新读取当前资料，让用户确认差异后构造新命令；不得只换成新 revision 自动重放旧意图覆盖其他客户端修改。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010 -->
### BR-UPF-010：主体内嵌资料与单文档原子提交

基础资料内嵌在 Auth 自有 `auth_principals.profile` 中。USER 的账号状态和资料版本处于同一 document；字段目录独立共享，Session、consent、应用存储和追加式审计不作为此 profile 的组成部分。

仓储把逻辑 KV 保存为有界 `entries` 数组，每项为 `{key, valueType, value}`，按 key 的 ASCII 字典序存放且 key 唯一。key 是数据值，不作为 Mongo 更新路径；带点的名称不会被解释成嵌套字段。STRING/DATE 保存为 BSON string、INTEGER 为 BSON int32、BOOLEAN 为 BSON bool，STRING_SET 保存为规范排序的 BSON string array，ACADEMIC_GRADE 保存为带 stage/year/finalYear/academicYear/confirmedAt 的封闭 object；DATE 由 valueType 区分。仓储读取时拒绝重复 key、未知存储类型、非规范集合或损坏的 profile 元数据，不静默合并或丢弃。

profile.revision 使用 BSON int64，profile.updatedAt 使用 BSON datetime。存储类型、key 语法、标量基本格式和元数据有效性属于结构校验；对未修改的历史值不重复应用当前字段目录的业务约束。内嵌 profile 不重复保存 authId，其归属由外层主体确定。

真实变更使用一次条件更新匹配 `authId + principalType=USER + accountStatus=ACTIVE + profile.revision=expectedRevision`，在同一次操作中写入候选 entries、新 revision 和 profile.updatedAt。禁止 upsert、整份主体替换、由客户端 key 拼接 `$set` 路径，或把部分条目分别提交。

该操作只改变 profile，不覆盖权限、Developer 状态、主体顶层 updatedAt 等其他事实。profile 的变化不能因为权限更新而被丢失，权限更新也不能用旧主体快照覆盖 profile。底层单文档原子性依据见 [MongoDB Atomicity](https://www.mongodb.com/docs/manual/core/write-operations-atomicity/)。

若条件更新匹配数为 0，不报告成功，也不自动换版本重试；可通过新的权威读取区分主体不存在、非 USER、DISABLED 和版本冲突。若此时状态已再次变化而无法精确归因，返回并发冲突让客户端重读，不猜测成功。数据库异常返回不可用，未知提交结果按 BR-UPF-009 处理。

禁用先于本次条件更新生效时，本次写入失败；资料更新先完成则可以成功，之后的禁用不撤销已经提交的资料。这是本用例的并发边界，不提供跨所有会话的即时失效承诺。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-011 -->
### BR-UPF-011：资料披露与操作记录

编辑结果和配套“读取本人资料”仅向通过本人身份与当前账号检查的调用者返回资料；不作为第三方应用资料 API，不广播完整资料事件，不自动建立或扩大 consent。

错误详情可以包含请求 key、稳定错误码和约束名，不回显字段值、其他用户资料、凭据或数据库内部结构。常规请求日志不得记录完整请求/响应资料正文。操作日志可记录 authId、requestId、结果和前后 revision；它不是与写入原子提交的不可变业务审计。首版不保存每次编辑的资料历史副本。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017 -->
### BR-UPF-017：首批生产字段目录

首批生产目录固定为下表；全部字段可选、可显式删除，来源均为用户主动确认。格式校验只证明值符合约束，不证明姓名、联系方式、学籍或一卡通归属真实。字段 key、类型、选项 value 和约束按 BR-UPF-002 的已发布稳定性处理。

| key | label | valueType | constraints / 含义 |
| --- | --- | --- | --- |
| `basic.name` | 姓名 | `STRING` | `minLength=1`，`maxLength=80`。 |
| `basic.gender` | 性别 | `STRING` | options 仅 `MALE=男`、`FEMALE=女`；不提供其它选项，未提供用 remove 表达。 |
| `education.campus_areas` | 活动片区 | `STRING_SET` | `minItems=1`、`maxItems=6`；options 为 `NANHU=南湖`、`JIANHU=鉴湖`、`MAFANGSHAN_WEST=西院`、`MAFANGSHAN_EAST=东院`、`YUJIA_TOU=余家头`、`JUNSHAN=军山`。这是面向学生的活动片区分类，不宣称六项都是行政意义上的独立校区。 |
| `education.major` | 专业 | `STRING` | `minLength=1`，`maxLength=128`。 |
| `personal.birthday` | 生日 | `DATE` | `notAfterToday=true`。 |
| `education.campus_card_number` | 一卡通号 | `STRING` | `minLength=maxLength=6`，`characterSet=ASCII_DIGITS`；保留前导零。 |
| `contact.phone` | 手机号 | `STRING` | `minLength=maxLength=11`，`characterSet=ASCII_DIGITS`；不据此建立登录凭据或验证号码归属。 |
| `contact.qq` | QQ | `STRING` | `minLength=5`，`maxLength=12`，`characterSet=ASCII_DIGITS`；保留为文本标识。 |
| `education.current_grade` | 当前就读年级 | `ACADEMIC_GRADE` | 用户确认阶段、当时年级和阶段最后学年；服务端锚定学年并按 BR-UPF-018 推算。 |

这些字段不产生用户权限，不自动从注册学生关联、邮箱、教务数据或其它字段填充。第三方读取必须另行满足 UC028 的逐字段 scope；本目录本身不使任何值公开。

<!-- 权威位置: use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018 -->
### BR-UPF-018：当前就读年级的锚定与阶段内推进

用户设置 `education.current_grade` 时提交 stage、year、finalYear 和从当前编辑 schema 观察到的 academicYear；必须满足 `1 <= year <= finalYear`。stage 只允许 `UNDERGRADUATE`、`MASTER`、`DOCTORAL`。academicYear 不是用户可自由选择的资料：Auth 按服务端当前时间从 [UC029/BR-UPF-019](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md#br-upf-019) 的权威时间表取得当前学年，请求值必须与之相等；不匹配按学年冲突拒绝并要求刷新。服务端在原子提交时写 confirmedAt。

对当前学年 C 和已保存锚点 A，当前有效年级序号为 `min(year + (C - A), finalYear)`。C 小于 A、差值溢出、stage/数值非法、confirmedAt 缺失或权威时间表不能解释当前服务端时间均失败关闭。时间推进只改变派生读结果，不批量改写 profile，不增加 profile revision，也不伪造一次新的用户确认。

推算只在原 stage 内递增并在 finalYear 封顶：本科最后一年不会自动变为硕士一年，硕士也不会自动进入博士或“已毕业”。跨阶段、休学、留级、延期或学制变化只能由用户明确重新设置；新设置以当时当前学年建立新锚点。客户端可在学年切换后提示确认，但不得代替用户静默提交。

学年时间表由 Auth 按 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 持有：缺省逐年 9 月 1 日，平台管理员只能设置带年份且晚于当前时间的下一次更新时间；到点后学年增加一，并从该时间按上海本地公历逐年推进。时间表修改不改写 profile 或既有年级锚点，也不是学校对个人学籍的认证来源。GetOwnProfile 返回保存的锚点值；当前 schema 返回同一次服务端观察时刻的 currentAcademicYear，官方客户端与 UC028 使用本规则计算同一有效年级。

## 平台共享契约（按 spec 显式抽取）

> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `platform/contracts/trusted-identity-v1.md`：可信身份 JWS v1 契约（trusted-identity-v1）

#### 目的与范围

本契约定义一个短期、audience 绑定的身份凭证在系统内的线格式与校验语义。它只规定跨系统的信任边界，不规定任一服务内部如何实现签发或验签，也不规定某个 UseCase 如何消费身份。跨系统选择本身见 [ADR-PLAT-001](../../platform/adr/ADR-PLAT-001-trusted-identity-jws.md)。

签发方是 Auth Center；Gateway 只转发；App Center 及未来的其它消费方各自本地验签。

#### 错误边界

- 消费方对「身份缺失」和「身份无效（含签名、算法、kid、issuer、audience、时间、claims、状态非法）」都返回**认证失败**：HTTP `401 Unauthorized`，gRPC `UNAUTHENTICATED`。
- 认证失败返回消费能力自己的稳定 reason；Developer 入口继续使用 `ERROR_REASON_DEVELOPER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_DEVELOPER_IDENTITY`，Reviewer 决定入口使用 `ERROR_REASON_REVIEWER_IDENTITY_REQUIRED` / `ERROR_REASON_INVALID_REVIEWER_IDENTITY`。客户端按 reason 区分，不解析 message。
- 认证失败的 message 不得回显 token、公钥、kid、时钟细节或底层 crypto 错误。内部日志可保留 cause，但不得记录完整 JWS。
- 认证失败先于业务校验发生；身份未通过时不进入 UseCase，也不产生配额或写入副作用。
- `developer_status` 缺失、或存在但不是 `APPROVED`，以及可信 Reviewer 身份不含目标权限，
  都属于**授权失败**，由 UseCase 决定，映射为 HTTP `403` / gRPC
  `PERMISSION_DENIED`，不属于本契约的认证失败。

## 配套查询契约（按 spec 显式抽取）

> 这些是当前 bounded context 的查询契约；只有本 spec 显式选择的章节才被抽取。
> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。

### `auth-center/query-contracts/user-profile-editing.md`：用户资料编辑配套查询

#### 身份与范围

两个查询都使用面向 Auth Center 的用户可信身份，并按 [BR-UPF-004](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004) 检查当前账号。无目标 authId 入参，不提供服务身份或管理员代查模式。

#### GetOwnProfile

输入为空。输出为 UC-AUTH-005 的 `OwnUserProfileSnapshot`：完整 entries、revision、updatedAt；其初始化、排序和元数据含义引用该用例。不返回账号权限、凭据、会话或其他用户资料。STRING_SET 使用规范排序；ACADEMIC_GRADE 返回用户最后确认的 stage/year/finalYear、服务端锚定 academicYear 和 confirmedAt，不把随时间推算出的展示年级回写为新的用户确认。

读取 Auth 权威主体 document 的单次一致快照，不使用客户端缓存或异步读投影作为版本权威；生产读路径避免滞后副本导致冲突恢复反复读到旧 revision。状态检查与资料取得来自同一次读取。查询的确认点为该读取，之后发生的并发禁用或修改不使已完成的读取追溯失效。

未提供资料的已初始化用户返回空 entries 和现有 revision；主体不存在与损坏/缺失 profile 按 UC-AUTH-005 的不同错误处理。读取不创建记录、不更新时间或版本。读取不需要字段目录可用，旧 key 的原始类型和值也原样交给本人，以支持显式清理；客户端不能把这些旧 key 当作允许重新 set 的定义。

#### GetProfileEditingSchema

输入为空。输出为当前完整、一致的已发布 ProfileFieldDefinition 集合、[BR-UPF-007](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007) 的全局编辑限制投影，以及服务端当前 `academicYear`。定义按 key 的 ASCII 字典序排列，无重复 key；options 保持目录声明顺序用于展示，但其 value 的比较和 STRING_SET 规范排序仍按 UC005。

查询只描述平台支持的字段与限制，不包含任何用户值，不表示这些字段必填，也不构成应用授权目录。未配置任何资料字段时可以返回空定义集合；定义读取失败或配置无效返回 PROFILE_FIELD_CATALOG_UNAVAILABLE，不能伪装为空目录。生产目录包含 ACADEMIC_GRADE 时，academicYear 必须由 [UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 的权威时间表按同一次服务端观察时刻确定；时间表不可用返回 ACADEMIC_YEAR_UNAVAILABLE。academicYear 不是客户端可修改的资料，也不是 profile revision。

这份查询结果供表单说明、当前年级展示和客户端预校验。客户端按 BR-UPF-018 从保存的锚点与当前 academicYear 计算有效年级；提交 ACADEMIC_GRADE 时回传本次观察的 academicYear，服务端仍重新校验它当前有效。首版已发布字段定义的稳定性引用 [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)，不另外引入字段 revision。

#### 页面与冲突恢复

1. 读取本人资料与编辑 schema，保留资料 revision 和 schema 给出的当前 academicYear；ACADEMIC_GRADE 按 BR-UPF-018 计算展示值。
2. 用户在本地编辑；教务导入流程遵循 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)。
3. 明确提交时构造 set/remove 和读取到的 expectedRevision；当前年级赋值同时携带观察到的 academicYear，不上传 confirmedAt。
4. 成功后用返回完整快照替换本地已保存基线；未提交的本地编辑不能因此被静默丢弃。
5. 发生冲突或提交结果不确定时，重新读取本人资料，展示当前值与待提交差异，由用户决定保留/重做哪些修改；重试规则见 [BR-UPF-009](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009)。

#### 交付边界

Profile Proto 需要投影 STRING_SET、ACADEMIC_GRADE、options/字符集/集合/日期约束及当前 academicYear，Gateway 路由随用户资料实现工作包交付。BR-UPF-017 生产字段目录和 UC029 权威学年时间表需显式交付；普通 USER provision、登录和客户端确认体验仍是生产依赖，不能用查询读取或测试字段代替这些能力。

## 未纳入本 brief 的源小节

需要时按源文件锚点查阅；不要为了“看全”而整文件加载。

- `UC-AUTH-005`（use-cases/UC-AUTH-005-edit-own-user-profile.md）：持久化与返回说明、变更记录
- `platform/contracts/trusted-identity-v1.md`（docs 根级共享文档）：传输载体、JOSE Header、Claims、时间与有效期、校验顺序、密钥与轮换、Gateway 义务、旧未签名 JSON Header 不兼容的原因、关联文档、账号终止与资格退出

## 溯源

| 文件 | 行数 | sha256 |
| --- | --- | --- |
| `use-cases/UC-AUTH-005-edit-own-user-profile.md` | 340 | `a2e87a33efad` |
| `platform/contracts/trusted-identity-v1.md` | 139 | `38ad6f17d886` |
| `auth-center/query-contracts/user-profile-editing.md` | 37 | `595efd9c0e87` |
