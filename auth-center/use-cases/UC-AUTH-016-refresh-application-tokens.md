# UC-AUTH-016：刷新应用访问凭据

状态：`ACCEPTED`

## 目标与范围

用户显式允许离线访问后，应用无需再次进入登录页面即可在有限期限内刷新 access token。首版使用 refresh token rotation，不依赖 Redis。

## 输入与输出

POST /token，grant_type=refresh_token、refresh_token、可选 scope，client 认证沿用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。输出旋转后的 refresh token 及新 access token；不重新签发 ID Token，不把刷新当作一次用户重新认证。

## 主流程

1. 先校验登记 client 的认证，再验证 refresh 摘要及 family 归属。
2. 重新读取 App 资格、用户/开发者状态、grant revocationEpoch、family 闲置/绝对期限和请求范围。
3. 原子消费旧 refresh，登记下一代 refresh 与 access token，更新 family 的最近刷新时间和闲置截止时间，审计并确认提交。
4. 正确绑定的已消费 refresh 再次使用时，原子撤销整个 family，要求重新交互登录授权。

## 业务规则

<a id="br-oau-009"></a>
### BR-OAU-009：离线访问须单独同意

只在批准版本声明 offline_access、本次请求包含它、用户明确确认离线访问且配置启用刷新能力时签发 refresh。offline_access 不代表任何业务数据 scope，也不是仅凭既有平台 Session 就自动获得的权限。PUBLIC/CONFIDENTIAL 均可申请；secret 不能代替用户同意。

离线访问许可统一由 grant 中的 offline_access 表达，不另存可独立修改的 allowBackgroundAccess 开关。它只允许在用户不在场时通过既有 token endpoint 刷新，不授予业务数据权限，也不提供仅凭 client 身份或历史 grant 就能随时领取新 token 的接口。UI 可从授权记录派生“允许后台访问”展示，实际刷新仍须持有有效 refresh token 并满足本用例全部条件。

用户退出平台 Session 不撤销 refresh family；到期、撤销或当前资格失效均可终止后续刷新。没有 offline_access 时，已签发 access token 仍可在自身有效期和授权范围内使用，不把该 scope 当作用户在线状态检测。

<a id="br-oau-010"></a>
### BR-OAU-010：旋转重放与并发边界

每个 family 同时最多一个 ACTIVE refresh；每次刷新原子从 ACTIVE→CONSUMED 并创建下一代。正确认证/归属的旧代再次提交视为重放，撤销整个 family 及其 access tokens；陌生 client 或错误 secret 不得借此撤销他人 family。

family 采用“滑动闲置期限＋固定绝对上限”，具体时长见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。首次签发保存 createdAt、lastRefreshedAt（初始为空）、idleWindow、absoluteExpiresAt、idleExpiresAt；absoluteExpiresAt=createdAt+绝对时长，idleExpiresAt=min(createdAt+idleWindow, absoluteExpiresAt)。时长策略在创建 family 时固定，后续部署调整不重置既有 family 的期限。

刷新在最终原子确认点以 Auth 服务端时间 t 检查 `t < idleExpiresAt` 且 `t < absoluteExpiresAt`，等于截止时间也算过期。仅成功提交的刷新设置 lastRefreshedAt=t、idleExpiresAt=min(t+idleWindow, absoluteExpiresAt)，新 refresh 与该截止时间绑定；absoluteExpiresAt 永不后移。验证失败、事务回滚、普通资源访问、UserInfo 查询或平台 Session 活动均不续期。后台任务成功刷新也算使用，不表示用户本人近期活跃。

到期后不得用旧 refresh 重建 family、重置 createdAt 或复活凭据；必须重新经过 UC014/015，并满足 offline_access 的明确同意规则。该 family 下新 access token 的 expiresAt 为 min(签发时间+通常 access 时长, 本次 idleExpiresAt, absoluteExpiresAt)，响应 expires_in 如实返回；续期不修改已经签发的 access token 的 expiresAt。

首版没有重试宽限或明文恢复缓存。应用必须串行刷新；网络丢响应或并发刷新可能导致 family 被撤销，需重新授权。历史摘要至少保留至 family 绝对到期及必要清理宽限，不能先删旧摘要再声称检测了重放。

<a id="br-oau-011"></a>
### BR-OAU-011：刷新不得扩权或复活

Refresh family 保存 authId、applicationId、clientId、grantId、原 channel/rpcApiMajor、client authorizationEpoch、Tester episode、grant revocationEpoch 和已授予的 refreshScopeCeiling F。省略 scope 使用 F；显式 scope 必须包含 openid/offline_access 且为 F 子集，越界返回 invalid_scope，不能以 grant 后来增加了 scope（包括同渠道另一 client 新增同意）为理由扩大旧 family。新权限通过 UC014/015 取得新凭据。

本次拟用集合记为 Q。Auth 先通过 ResolveClientRuntimeConfiguration 读取 token 原 channel/major 的当前版本，再用返回的 registration/runtime tuple 调用 ResolveAuthorizationContext；不能把签发时旧 Version tuple 作为刷新前置值，也不能根据请求换 major/channel。必须验证 family 的 authId/applicationId/channel 与所引用共享 grant 完全一致，并验证 client 的 App 归属；共享 grant 不允许另一 client 使用该 family。确认用户、client、Tester episode 和 grant epoch 有效后，实际签发 access scopes 为 `Q∩G∩D∩C`，C 为 UC014/BR-OAU-001 定义的 Auth 当前目录许可集合，必须仍包含 openid/offline_access，否则 invalid_grant、不签后继凭据。本次 token 响应 scope 必须如实返回实际集合。

自动求交只限制本次 access token，不裁剪历史 G，也不把当前 D/C 写成下一代 refresh 的永久上限。下一代 refresh 保留 Q 作为 ceiling；仅客户端显式缩小 Q 才永久缩小该 family 上限。因 D 暂时缩小或 Catalog enabled=false 而未使用的、原本已同意的 scope，可在版本许可和目录启用恢复时由 refresh 再次取得，但永远不能超过 F/G。本用例不弹 UI 或自动扩大用户同意。

grant revocationEpoch 或 client authorizationEpoch 不匹配、client 禁用、用户不可用、Tester episode 改变、family 撤销/到期均 invalid_grant。grant 仅增加权限而 revision 改变、单纯 Version/publication/credentialRevision 变化不使 family 失效。共享 grant 的撤销对同应用同渠道所有 client 的 family 生效；单个 client 的禁用或 authorizationEpoch 变化仅使该 client 的凭据失效，不修改共享 G 或撤销另一 client 的 family。CONFIDENTIAL 必须使用当前 secret。正常刷新不撤销同 family 尚未到期的 access token，family/用户撤销仍统一生效；不能覆盖旧 epoch 来恢复已撤销凭据。

## 验收场景

- 没有明确 offline_access 同意不返回 refresh；停用该能力时 discovery 同步收缩。
- 同渠道另一 client 新增同意不扩大原 family ceiling；用户撤回共享授权使两类 client 的旧 family 均失效，禁用单个 client 不撤销另一 client 的 family。
- 正常旋转同时延长闲置截止时间，但不延长绝对期限；按协议首版时长，第 20 天刷新后闲置截止为第 50 天，持续有效至第 179 天时，刷新后最多到第 180 天。
- 30 天未刷新、恰好达到任一截止时间均拒绝；持续刷新也不能越过第 180 天。单纯调用资源、查询 UserInfo、平台登录或失败刷新不续期。
- 事务回滚不更新期限；提交成功但响应丢失仍遵循严格轮换/重放规则，不返回旧 token 的可重试副本。
- 临近 family 截止时，新 access token 的 expires_in 相应缩短；刷新不延长已发出的 access token。
- 客户端显式缩小 ceiling 后不能扩大，D 临时变小不裁剪 G/ceiling。
- 当前版本移除 email 或 Catalog 停用 email，refresh 返回不含 email 的 access，不裁剪 G/ceiling；许可恢复后可在原 ceiling/G 内取得包含 email 的新 access，不要求再次同意。
- openid 或 offline_access 停用导致缺少必需刷新权限，本次刷新失败、不消费 refresh、不续期；恢复也不能复活已过期/已撤销 family。
- 双并发、丢响应重试、跨 client 重放、错误 secret、祖先 token 重放覆盖 family 状态与秘密保护。
- 用户撤回、部分 scope 撤回后再授予、Tester 重加均不能恢复旧 refresh；secret 轮换要求后续使用新 secret，但不删除 family。

## 依赖与实现边界

依赖 UC014/015、UC018 和 App 提供方。可在基础 code flow 后单独实现；未交付时不得接受 offline_access 或宣称 refresh grant 可用。
