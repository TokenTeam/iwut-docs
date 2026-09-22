# 用户模型：主体与用户资料

状态：`PROPOSED`

本文在[用户资料字段定义](user-profile-field-definition.md)基础上保留用户逻辑模型说明。资料编辑、初始化及内嵌存储的规则正文已归入 [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md)，下文通过 BR 引用提供摘要；登录、账号管理完整生命周期仍属于后续用例。UC-AUTH-005 至 009 均已 ACCEPTED；设备协议见[共享契约](../../platform/contracts/auth-device-session-v1.md)，实现与客户端交付分别验收。

## 模型边界

User 表达一个普通用户主体；UserProfile 表达该用户主动向平台提供的资料。二者通过同一个 authId 关联。字段定义属于共享目录，不为每位用户复制一份。

资料信任定位和主动提交边界见 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)，账号可用与本人访问条件见 [BR-UPF-004](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004)。

本草案聚焦三个问题：用户是谁、账号当前是否可用、用户主动保存了什么资料。登录证明、资格与权限、应用授权各自使用对应能力的规则。

## 用户主体

```text
User {
  authId: AuthId
  principalType: USER
  accountStatus: ACTIVE | DISABLED
  createdAt: Instant
  updatedAt: Instant
}
```

这是主体的最小逻辑视图，不是对已有 `auth_principals` 全部字段的重新定义。既有资格和权限字段继续由后文链接的权威用例拥有。

| 字段 | 含义 | 设计来源或建议 |
| --- | --- | --- |
| `authId` | 稳定用户身份，用于关联资料、应用归属与审计 | 延续 [UC-AUTH-002 数据模型](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#数据模型)。不另造 profile 专用 userId，也不使用学号或邮箱作为身份 ID。 |
| `principalType` | 在统一主体模型中识别普通用户 | 既有模型区分 USER/SYSTEM，来源同上；User 视图固定为 USER，并非用户可选择的角色。 |
| `accountStatus` | 平台账号的整体可用性 | 编辑入口当前状态条件见 [BR-UPF-004](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004)；状态修改由后续账号管理用例定义。 |
| `createdAt` | 主体创建时间 | 延续既有主体模型的 UTC、创建后不变语义。 |
| `updatedAt` | 主体平台管理事实最近更新时间 | 延续既有主体模型；具体命令明确其更新范围。资料更新时间由 UserProfile 单独表达。 |

建议 authId 在主体生命周期内保持稳定，不因资料、登录标识或账号状态变化而替换；具体 USER 创建时机与 ID 分配方式由创建用例闭合。当前已有 Auth ID 对外契约不因本草案改变。

### accountStatus 的最小含义

- `ACTIVE`：账号未被整体禁用；具体操作仍取决于凭据、会话、资格和权限，状态本身不等于已认证或已授权。
- `DISABLED`：账号整体不可用；建议阻止新的登录、刷新会话和签发用户可信身份。禁用如何处理现有会话和已签发凭证，在账号管理用例中定义，不承诺本地验签的既有 token 立即失效。

账号禁用不等同于 Developer 暂停，也不等同于撤销某个 Reviewer permission。重新启用账号不自动重新授予已撤销的资格或权限。操作人权限、理由、审计和并发控制由后续账号管理用例定义。

首版暂不增加 PENDING、DELETED、注销恢复截止时间等字段；[BR-REG-002](../use-cases/UC-AUTH-006-create-user.md#br-reg-002) 已确定 USER 创建时直接为 ACTIVE。注销是否提供恢复窗口由后续用例决定，这里的两态不宣称完整生命周期已经设计完成。

## 用户资料

下面是逻辑阅读视图；初始化和版本见 [BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)，值类型见 [BR-UPF-003](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-003)，Mongo 内嵌表示见 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。

```text
UserProfile {
  authId: AuthId
  values: Map<FieldKey, ProfileValue>
  revision: int64
  updatedAt: Instant
}
```

| 字段 | 用途摘要 |
| --- | --- |
| `authId` | 关联普通用户主体；内嵌保存时由外层主体确定，不重复存储。 |
| `values` | 用户主动提交的稀疏 KV 逻辑集合。 |
| `revision` | 整份资料的并发版本。 |
| `updatedAt` | 资料最近一次内容变更时间。 |

普通 USER 的空资料初始化、并发冲突、无变化请求和重试分别引用 [BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)、[BR-UPF-009](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009)。不在本文另设规则。

### 逻辑示例

以下展示两个相关对象，不是公共 API 响应，也不表示主体字段和全部资料可以一起披露给应用。字段目录中的示例仍不等于已接受的实际收集清单。

```json
{
  "user": {
    "authId": "example-auth-id",
    "principalType": "USER",
    "accountStatus": "ACTIVE",
    "createdAt": "2026-09-22T08:00:00Z",
    "updatedAt": "2026-09-22T08:00:00Z"
  },
  "profile": {
    "authId": "example-auth-id",
    "values": {
      "education.school_name": "示例大学",
      "education.enrollment_year": 2024
    },
    "revision": 2,
    "updatedAt": "2026-09-22T09:00:00Z"
  }
}
```

主体创建后资料发生了一次真实修改，因此示例中 profile revision 为 2，两个 updatedAt 不同。学校名称和入学年份仍是字段目录约束的动态值，不成为 User 的固定字段。

## 已有资格与权限如何接入

已有规则继续通过 authId 与普通用户关联。本草案不重新分配编号、不复制它们的权威定义，也不据此把既有字段从 `auth_principals` 中迁出。

| 已有事实 | 权威位置 |
| --- | --- |
| Developer 资格与 `developerStatus` | [BR-DEV-004](../use-cases/UC-AUTH-002-batch-get-developer-statuses.md#br-dev-004) 及该 UC 数据模型。 |
| 人员权限 `permissions`、`permissionRevision` 与审计 | [UC-AUTH-004](../use-cases/UC-AUTH-004-manage-reviewer-permission.md#数据模型)。 |

这些事实与用户可编辑的资料分离；信任边界和资料更新范围引用 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)、[BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。

## 其他常见字段的归属

| 候选内容 | 建议归属 |
| --- | --- |
| 学校、学号、院系、专业、入学年份 | 按真实用途逐项进入 ProfileFieldDefinition；用户值进入 UserProfile.values。当前仅学校名称与入学年份有说明性示例，其余尚无完整定义。 |
| 昵称、头像 | 根据实际产品用途定义；本轮不默认增加公开个人主页能力或必填资料。 |
| 平台登录邮箱、邮箱验证事实、密码摘要 | 登录标识与凭据模型；设备凭据创建/登录见 UC-AUTH-006/007，邮箱认证方式仍待决定，不成为 User 的必填字段。若资料中以后有联系邮箱，也不能据此修改登录邮箱或取得验证状态。 |
| 学校账号密码、登录 cookie | 客户端本地凭据；遵循字段定义草案的上传边界。 |
| 设备凭据、Session、登录设备 | [UC-AUTH-007](../use-cases/UC-AUTH-007-login.md) 定义认证与会话，[UC-AUTH-008](../use-cases/UC-AUTH-008-revoke-own-session.md) 与 [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 定义两类撤销；均不属于学生资料，refresh token 尚未引入。 |
| 学生关联分组 | [BR-REG-004/005](../use-cases/UC-AUTH-006-create-user.md#br-reg-004) 的客户端声明关系，与资料和账号控制权独立。 |
| 应用对资料的读取同意记录 | 独立应用授权事实，通过 authId 关联，不在 User 上添加一个表示全部同意的布尔值。 |

## MongoDB 存储方向

根据已讨论的内嵌方向，UC-AUTH-005 的 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010) 定义主体 document 内的有界 profile。逻辑上的 Map 在持久化时由条目数组表达；共享字段定义独立保存。该规则同时规定资料更新范围，避免整份主体覆盖。

Session、consent、追加审计和应用存储的具体集合与生命周期仍由对应能力设计，不因与用户关联就全部进入 profile。

## 当前用例与后续方向

[UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) 已提出本人资料编辑的命令、异常与验收；开始编辑和冲突恢复的读取见[配套查询](../query-contracts/user-profile-editing.md)。

普通 USER 创建、登录和本人撤销已有 [UC-AUTH-006](../use-cases/UC-AUTH-006-create-user.md) 至 [UC-AUTH-009](../use-cases/UC-AUTH-009-revoke-own-credential.md) 的已接受设计；账号禁用管理、邮箱恢复和注销仍是后续独立用例。学生关联是独立于资料的客户端声明关系，边界见 [BR-REG-004](../use-cases/UC-AUTH-006-create-user.md#br-reg-004)，不代表已验证的学生身份。第一批资料字段及生产交付依赖见 [open-questions.md](../open-questions.md#用户资料生产交付)。
