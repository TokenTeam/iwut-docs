# 用户资料编辑配套查询

状态：`ACCEPTED`

本文定义用户开始编辑及冲突恢复所需的最小读取语义，不定义第三方应用数据开放。业务约束由 [UC-AUTH-005](../use-cases/UC-AUTH-005-edit-own-user-profile.md) 的 `BR-UPF-*` 拥有；本文不重复定义其校验和容量规则。

## 身份与范围

两个查询都使用面向 Auth Center 的用户可信身份，并按 [BR-UPF-004](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-004) 检查当前账号。无目标 authId 入参，不提供服务身份或管理员代查模式。

## GetOwnProfile

输入为空。输出为 UC-AUTH-005 的 `OwnUserProfileSnapshot`：完整 entries、revision、updatedAt；其初始化、排序和元数据含义引用该用例。不返回账号权限、凭据、会话或其他用户资料。

读取 Auth 权威主体 document 的单次一致快照，不使用客户端缓存或异步读投影作为版本权威；生产读路径避免滞后副本导致冲突恢复反复读到旧 revision。状态检查与资料取得来自同一次读取。查询的确认点为该读取，之后发生的并发禁用或修改不使已完成的读取追溯失效。

未提供资料的已初始化用户返回空 entries 和现有 revision；主体不存在与损坏/缺失 profile 按 UC-AUTH-005 的不同错误处理。读取不创建记录、不更新时间或版本。读取不需要字段目录可用，旧 key 的原始类型和值也原样交给本人，以支持显式清理；客户端不能把这些旧 key 当作允许重新 set 的定义。

## GetProfileEditingSchema

输入为空。输出为当前完整、一致的已发布 ProfileFieldDefinition 集合，以及 [BR-UPF-007](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-007) 的全局编辑限制投影。定义按 key 的 ASCII 字典序排列，无重复 key。

查询只描述平台支持的字段与限制，不包含任何用户值，不表示这些字段必填，也不构成应用授权目录。未配置任何资料字段时可以返回空定义集合；定义读取失败或配置无效返回 PROFILE_FIELD_CATALOG_UNAVAILABLE，不能伪装为空目录。

这份查询结果供表单说明和客户端预校验。服务端写入仍重新按 UC-AUTH-005 校验，不信任客户端提交或缓存的 schema。首版已发布字段定义的稳定性引用 [BR-UPF-002](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-002)，不另外引入字段 revision。

## 页面与冲突恢复

1. 读取本人资料与编辑 schema，保留资料 revision。
2. 用户在本地编辑；教务导入流程遵循 [BR-UPF-001](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-001)。
3. 明确提交时构造 set/remove 和读取到的 expectedRevision。
4. 成功后用返回完整快照替换本地已保存基线；未提交的本地编辑不能因此被静默丢弃。
5. 发生冲突或提交结果不确定时，重新读取本人资料，展示当前值与待提交差异，由用户决定保留/重做哪些修改；重试规则见 [BR-UPF-009](../use-cases/UC-AUTH-005-edit-own-user-profile.md#br-upf-009)。

## 交付边界

最终 Proto 与 Gateway 路由随用户资料实现工作包交付。字段目录具体内容、普通 USER provision 和登录仍是生产依赖；不能用查询读取或字段示例代替这些能力。
