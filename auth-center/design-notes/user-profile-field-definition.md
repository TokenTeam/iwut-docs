# 用户资料字段定义：最小结构

状态：`ACCEPTED`

本文保留字段模型说明与历史示例。规则正文已归入 [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) 的 `BR-UPF-*`，本文不构成第二权威。UC-AUTH-005 的编辑、容量和首批生产字段规则已接受，实际实现依赖继续跟踪。

## 已确认的资料定位

资料定位、客户端本地导入与明确提交的信任边界统一见 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)。

## 最小结构

结构和字段标识规则见 [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)，值类型与约束见 [BR-UPF-003](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-003)。下面是阅读视图：

```text
ProfileFieldDefinition {
  key
  label
  description
  valueType
  constraints
}
```

| 属性 | 用途摘要 |
| --- | --- |
| `key` | 客户端、用户资料与应用引用的稳定字段标识。 |
| `label` | 展示名称。 |
| `description` | 业务含义和填写说明。 |
| `valueType` | 值的基础类型。 |
| `constraints` | 对应类型的声明式校验规则。 |

## key

key 的语法、长度、唯一性及点分名称语义见 [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。MongoDB 如何保存 key 引用 [BR-UPF-010](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-010)。

## valueType 与 constraints

类型与精确校验规则统一见 [BR-UPF-003](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-003)，首批实际目录见 [BR-UPF-017](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-017)，锚定年级见 [BR-UPF-018](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-018)。新的基础类型或校验能力仍需要实现支持。

## 示例

以下是 2026-09-22 的历史结构示例，不是 BR-UPF-017 已接受的实际收集目录，也不得进入生产配置。

```json
{
  "key": "education.school_name",
  "label": "学校名称",
  "description": "用户选择向平台提供的一条当前就读记录中的学校名称，以用户提交的文本为准。",
  "valueType": "STRING",
  "constraints": {
    "maxLength": 100
  }
}
```

```json
{
  "key": "education.enrollment_year",
  "label": "入学年份",
  "description": "用户选择向平台提供的一条当前就读记录所对应的公历入学年份，不表示当前年级。",
  "valueType": "INTEGER",
  "constraints": {
    "minimum": 1900,
    "maximum": 2100
  }
}
```

对应的用户资料逻辑值可以是：

```json
{
  "education.school_name": "示例大学",
  "education.enrollment_year": 2024
}
```

## 相关规则导航

| 主题 | 权威位置 |
| --- | --- |
| 缺失值、显式删除与部分编辑 | [BR-UPF-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-005)、[BR-UPF-006](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-006)。 |
| 目录发布与字段稳定性 | [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)。 |
| 全局容量上限与字段自身限制 | [BR-UPF-007](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007)。 |
| 普通用户资料实例与并发版本 | [用户模型](user-model.md)、[BR-UPF-008](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-008)。 |
| 用户读取表单定义和自己的资料 | [资料编辑配套查询](../query-contracts/user-profile-editing.md)。 |
| 与应用读取授权的边界 | [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)、[BR-SCP-004](../use-cases/UC-AUTH-001-get-scope-catalog-snapshot.md#br-scp-004)。 |

字段定义不承担某位用户的 value、会话、权限或教务接口映射。普通生产字段均为用户确认；ACADEMIC_GRADE 的服务端学年锚点属于 BR-UPF-018 的封闭值元数据，不建立通用 verified/source 权限系统。多语言文案、表单控件和布局仍可在实际展示需求出现后设计。

## 后续方向

交付 BR-UPF-017/018 的真实目录、Profile API 类型、[UC029](../use-cases/UC-AUTH-029-manage-academic-year-rollover.md) 权威学年时间表与客户端；字段目录在线管理继续后移。第三方读取由已接受的 [UC-AUTH-028](../use-cases/UC-AUTH-028-disclose-user-profile-to-applications.md) 负责；[UC-AUTH-030](../use-cases/UC-AUTH-030-manage-application-user-storage.md) 的 ApplicationUserStorage 是独立 DRAFT，不属于资料字段目录。
