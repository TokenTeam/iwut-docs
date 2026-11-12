# 本人脚本权限发现方案

本文保留五项权限版本的设计记录。2026-11-11 修订后的本人读取按 UC038 返回四项。

状态：`ACCEPTED`。2026-11-10 用户明确批准 Auth 接受并实现；业务规则唯一位于 [UC038 正文](../use-cases/UC-AUTH-038-manage-script-maintainer-permission.md#proposed-own-script-permissions)。

## 缺口核对与复用决定

现有 UC038 的目标 Get 和 Manage 均要求完整平台管理员，传入自己的 subjectAuthId 也按管理方法鉴权。旧 maintain 接口具有同样限制。UC027 的本人读取只公开 restore/search/suspend 三项 Application 权限。UC010 将脚本权限投影到 App audience，Auth audience 的身份载体和 BrowserSession 均不能供前端推断本人脚本职责。

已接受修订 UC038，增加独立的本人空请求 RPC，复用已有五项 `ScriptPermissions` 响应和共享 permissionRevision。普通本人读取与管理他人权限的参与者、可见集合和验证路径分别定义。新读取依赖当前 USER 在线确认，不依赖管理员初始化、邮箱或恢复就绪。

复用同一权限族可沿用五项枚举顺序、granted/effective 语义和限流。现有授权管理、App 精确业务鉴权及短期 JWS 窗口已有权威定义，本轮只为职责入口发现增加一个最小查询。

## 已接受的决定

1. 允许任意有效 ACTIVE USER 查询本人，包括没有脚本授权的普通用户。结果完整返回五项状态和共享版本，主体由可信身份固定。ACTIVE 本人成功响应中 granted 与 effective 相等。
2. 复用现有 ScriptPermissions 响应。无权限通过五项全部 false 表达；身份失效、停用、入口关闭或依赖失败分别报错，不合成为无权限。
3. 复用 `AUTH_SCRIPT_PERMISSION_ENDPOINTS_ENABLED` 总开关和现有读限流，新增精确 GET `/v1/users/me/script-permissions`。Gateway 按 SESSION → Auth audience 接入，Console surface 限定 ADMIN。进入该 surface 只决定交付路径，Auth 本人读取无需完整管理员资格。

## 交付与审核边界

本轮按接受结果替换 UC038 原“无普通用户自查询”的排除条款，把差异合入参与者、API 和 BR-SMP-004/005，再生成实施 brief。

API owner 在独立工作窗口新增空请求和精确方法，Auth 增加独立的普通 USER 方法分支和本人事务快照，Gateway/Console owner 接续路由和客户端消费。现有 API、实现和 Console 文档保持当前工作状态。

2026-11-09 提案时核对 Auth 父 HEAD `e92b96c4d144dbe2e9aba302332de6fe7d6ef38f` 及工作树，API `a57bb969f20141a183942a28e529c5c21ee5cc79`。当时没有已接受的五项脚本本人读契约，独立脚本人员的真实权限发现接入等待本修订接受和后端交付。

## 2026-11-10 接受前状态复核（历史）

接受前 Auth 本地与远端 master 均为 `8921b8354f3252a66f735e5e74489d6e62bfe749`，API 为 `7651f96ceb85f11784660521b0f3c8a7c30d7d57`，工作树干净。当时已推送的代码包含五项脚本权限的管理员授撤与 App 身份投影；`GetOwnScriptPermissions` 尚未进入 Proto 或实现，本修订仍为 PROPOSED。该历史状态已被下述实施授权取代。Console 的脚本本人权限发现接入等待该方法交付，应用动态和应用脚本引用按其各自已接受契约推进。

2026-11-10 实施授权：本人读取已接受，合入 BR-SMP-004/005，生成 brief 后串行交付 Auth/API。2026-11-09 与本次复核前的状态记录保留为历史。
