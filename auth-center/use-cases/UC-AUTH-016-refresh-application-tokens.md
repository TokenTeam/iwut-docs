# UC-AUTH-016：刷新应用访问凭据

状态：`PROPOSED`

## 目标与范围

用户显式允许离线访问后，应用无需再次进入登录页面即可在有限期限内刷新 access token。首版使用 refresh token rotation，不依赖 Redis。

## 输入与输出

POST /token，grant_type=refresh_token、refresh_token、可选 scope，client 认证沿用 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。输出旋转后的 refresh token 及新 access token；不重新签发 ID Token，不把刷新当作一次用户重新认证。

## 主流程

1. 先校验登记 client 的认证，再验证 refresh 摘要及 family 归属。
2. 重新读取 App 资格、用户/开发者状态、grant revision、family 绝对期限和请求范围。
3. 原子消费旧 refresh，登记下一代 refresh 与 access token，审计并确认提交。
4. 正确绑定的已消费 refresh 再次使用时，原子撤销整个 family，要求重新交互登录授权。

## 业务规则

<a id="br-oau-009"></a>
### BR-OAU-009：离线访问须单独同意

只在批准版本声明 offline_access、本次请求包含它、用户明确确认离线访问且配置启用刷新能力时签发 refresh。offline_access 不代表任何业务数据 scope，也不是仅凭既有平台 Session 就自动获得的权限。PUBLIC/CONFIDENTIAL 均可申请；secret 不能代替用户同意。

family 的绝对期限和初始 token 期限见共享协议。用户退出平台 Session 不撤销它；主动撤回授权或撤销 family 才终止后续刷新。

<a id="br-oau-010"></a>
### BR-OAU-010：旋转重放与并发边界

每个 family 同时最多一个 ACTIVE refresh；每次刷新原子从 ACTIVE→CONSUMED 并创建下一代。正确认证/归属的旧代再次提交视为重放，撤销整个 family 及其 access tokens；陌生 client 或错误 secret 不得借此撤销他人 family。

首版没有重试宽限或明文恢复缓存。应用必须串行刷新；网络丢响应或并发刷新可能导致 family 被撤销，需重新授权。历史摘要至少保留至 family 绝对到期及必要清理宽限，不能先删旧摘要再声称检测了重放。

<a id="br-oau-011"></a>
### BR-OAU-011：刷新不得扩权或复活

省略 scope 沿用该 refresh 的集合；指定时必须含 openid 和 offline_access、且为旧 refresh 的子集。不再需要离线访问时通过 UC018 撤销 family 或重新取得不含 offline_access 的授权，不签发缺失离线许可的后继 refresh。缩减权限后，下一代 refresh 同样只保留缩减集合，不允许以后恢复为祖先集合；每次仍受当前 grant、App 资格与 Auth 映射限制。

grant revision 或 App 绑定版本变化、client 禁用/轮换、用户不可用、family 已撤销/到期均 invalid_grant。不能通过更新记录上的 revision 使旧授权重新有效。正常刷新不主动撤销尚未到期的同 family access token；family/授权撤销则统一生效。

## 验收场景

- 没有明确 offline_access 同意不返回 refresh；停用该能力时 discovery 同步收缩。
- 正常旋转，缩小后不能再扩大；绝对期限不随刷新延长。
- 双并发、丢响应重试、跨 client 重放、错误 secret、祖先 token 重放覆盖 family 状态与秘密保护。
- 用户撤回、部分 scope 撤回后再授予、client 轮换、Tester 重加均不能恢复旧 refresh。

## 依赖与实现边界

依赖 UC014/015、UC018 和 App 提供方。可在基础 code flow 后单独实现；未交付时不得接受 offline_access 或宣称 refresh grant 可用。
