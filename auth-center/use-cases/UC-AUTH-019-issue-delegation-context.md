# UC-AUTH-019：校验应用访问凭据并签发可信委托上下文

状态：`PROPOSED`

## 目标与范围

受授权 Gateway 为即将转发的资源请求在线验证 opaque access token，得到目标路由专用的短期签名上下文。与 UC010 的平台 Session→USER 签发并列，不能混用。

## 输入与输出

精确内部 RPC、service permission、双凭据 metadata、输入和签名格式见 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md)。不提供 public introspection，也不向应用返回内部委托 JWS。

## 主流程

1. 验证 Gateway 服务身份及允许 route/audience，解析本地可信路由策略。
2. 按用途查 access token 摘要，确认期限、用户、grant/revision、family 和 token 撤销状态。
3. 从 App 重新确认稳定 client、当前发布/Tester 资格，检查当前 Developer，确认请求的 audience 和所有 route scopes 均被 token 与当前 Version 许可。
4. 在 Auth 原子授权确认点签发短期委托 JWS，Gateway 转发给指定资源；任何失败不返回半成品上下文。

## 业务规则

<a id="br-oau-018"></a>
### BR-OAU-018：服务调用者和用户授权双重门禁

Gateway 服务身份只允许调用签发方法，不授予终端用户任何业务权限。用户身份、client、grant、scope 只来自 Auth 的 access token 记录与当前权威状态，客户端自报 claims/角色全部忽略并拒绝相关越权字段。

有效 token 必须同时满足：用户 ACTIVE、应用管理员 APPROVED、client ACTIVE、当前 App 运行资格有效、grant ACTIVE 且 revision 一致、token scopes 仍是当前许可 scopes 的子集、token/family 未撤销未过期。签发时 Version ID 与当前不同不单独判定 token 失效；Tester episode、client 状态、grant revision 或 scope 资格变化仍失败关闭。原平台 Session 是否已退出不在条件中。

<a id="br-oau-019"></a>
### BR-OAU-019：路由许可与委托身份隔离

所有 requiredScopes 必须被 token 覆盖，audience 必须在 token 的受信资源集合。route policy 来源、digest 和 JWS 格式唯一引用 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md)。不能从请求 body/headers 取得任意 audience 或上游地址，不接受通配能力。

委托只表达当前用户让特定应用做特定范围操作；不投影用户 Developer/Reviewer/管理员权限，也不把 applicationId 当用户 subject。资源服务仍执行数据归属和具体业务条件检查。

<a id="br-oau-020"></a>
### BR-OAU-020：签发撤销一致性与在线依赖

最终确认与 grant/family/token 撤销及用户状态迁移共用本地写入栅栏；可沿用单实例应用锁加 Mongo 原子确认，不为未来 k8s 预建分布式锁。进程恢复后以数据库事实为准。签名失败不返回身份；事务确认未知不得乐观放行。

App 快照、委托期限及撤销传播上界按 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md) 执行；Auth/App 故障必须失败关闭。首版不缓存授权结果，不能为可用性退回仅验 JWT 或仅信任 client_id。

## 验收场景

- 正确 token/route 成功；ID Token、Session、service JWT、随机值不能替代 access token。
- scope、audience、policyDigest、method/path、client 资格任一不符均不签发。
- App 离线、过期快照、未知 kid、签名失败、Mongo 确认未知都失败关闭。
- grant/token/family 撤销及用户状态更新的并发测试覆盖本地栅栏；时钟和传播边界按共享契约验收。

## 依赖与实现边界

依赖 UC015/018、UC-APP-019、现有 service identity；UC-GW-002 与资源验证器消费输出。scope→route→audience 映射、资源服务委托支持尚需交付，不能复用现有 USER middleware 假装完成。详见 [委托上下文契约](../../platform/contracts/oauth-delegation-v1.md) 的启用门禁。
