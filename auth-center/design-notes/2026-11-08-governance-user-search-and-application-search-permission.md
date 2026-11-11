# 管理员用户搜索与 Application 搜索权限方案

状态：`ACCEPTED`。2026-11-08 用户明确接受 UC039 与 UC027/010 的方案并授权 Auth 实施。本文保留审核导航，业务规则以 UC 正文为准。

## 权威设计与复用决定

| 范围 | 权威位置 | 决定 |
| --- | --- | --- |
| 管理员定位用户 | [UC039](../use-cases/UC-AUTH-039-search-users-for-administration.md) | 新 UC，独立的人员信息披露与一致查询边界 |
| 管理 app.application.search | [UC027 已接受修订](../use-cases/UC-AUTH-027-manage-application-operations-permissions.md#proposed-application-search) | 复用三项既有 RPC、目标共享版本及审计，将管理和本人公开 allowlist 扩为三项 |
| 向 App 签发 search | [UC010 已接受修订](../use-cases/UC-AUTH-010-issue-user-identity-from-session.md#proposed-application-search-projection) | 扩展精确 App audience 清单，沿用既有签发与撤权窗口 |

UC039 不是平台管理员名单查询的附加过滤。人员目录的完整邮箱匹配和可见状态是独立披露，需要单独 UC。Application search 的管理条件与 UC027 现有权限一致，复用该 UC 能避免重复授撤、版本、审计和本人发现协议。

已将差异合入 ACCEPTED UC/BR，并先生成实施 brief；当前交付记录见 implements。

## 已接受的决定

1. 用户搜索首版只支持单一完整 Auth ID 或完整当前已验证邮箱，登录和非登录绑定都参与精确定位。最多一条结果，空查询和分页参数均拒绝。
2. 返回 ACTIVE/DISABLED USER 的 Auth ID、账号状态及可空 Developer 状态；邮箱、姓名和动态 Profile 不返回。合法 CLOSED/SYSTEM/不存在返回空集合，损坏数据和依赖失败单独报错。
3. 所有用户搜索要求完整平台管理员在线复核，仅用于 Admin 治理，转让对象继续由用户填写 opaque Auth ID。
4. Application search 复用 UC027，三项 App 权限独立授撤与本人发现。新增字符串 ID 本身不授予其他动作；签发与本人读取均读取当前权威权限和共享版本。
5. 撤权后的新签发和本人读取排除 search，已签 App JWS 继续遵守原 exp 与验签容差窗口。

## 依赖现状与后续顺序

本轮核对 Auth 父 HEAD `e92b96c` 及保留的本地工作树，API checkout `01f2ecb633120662d9a74d0263d9aebda37b6e16`。UC027 的管理和本人读取实现以固定双项 allowlist 工作，UC010 的 App 投影尚不含 search。既有 API 字符串 permission 和重复结果可承载新增精确 ID。

UC039 可复用现有唯一索引、邮箱规范化和目录、状态及管理者事务复核，新增自己的精确 API 与有界查询。UC027/010 需要正式扩大 allowlist 和联验。设计依赖已可闭合，已获实施授权。

按 Auth/API → Gateway → Console 与 App 真实联验交接。App UC051 的正式权限接入等待 Auth 实现和签发验收；App UC050 的本人入站转让读取独立推进。本轮只修改 Auth 文档与已有 Auth brief 的来源记录。共享签发/路由契约、App、Console、Gateway 和 API 由各 owner 在后续工作窗口接续。
