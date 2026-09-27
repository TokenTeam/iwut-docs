# UC-AUTH-015：兑换授权码并签发 OIDC 凭据

状态：`PROPOSED`

## 目标与范围

应用按登记认证方式兑换 code，得到独立 ID Token 和 access token。两种接入方式共用一次性授权码状态机，不签发通用平台 Session。

## 输入与输出

POST /token，grant_type=authorization_code、code、redirect_uri；PUBLIC 表单 client_id+code_verifier，CONFIDENTIAL HTTP Basic，并在发起时提交 PKCE 的情况下附 verifier。成功字段和 ID Token 校验约定见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

## 主流程

1. 读取 client 元数据，按登记类型校验认证；secret 验证结果必须与当前 configRevision 一致。
2. 查 code 摘要，验证 client、code 中绑定的精确 redirect、PKCE、期限和用途；使用 code 保存的 expected runtime tuple 与 authId 重新调用 App `ResolveAuthorizationContext`，确认当前 Version 回调仍包含该精确 URI，并重新确认用户、Developer、grant revision 及 scope。
3. 生成 opaque access token 与独立 ID Token；符合 UC-AUTH-016 时生成 refresh family。
4. 在原子确认点消费 code，登记凭据摘要、family 和审计，检查 grant/用户写入栅栏。
5. 仅确定提交成功后返回。客户端验证 OIDC 输出再建立自己的应用会话。

## 业务规则

<a id="br-oau-005"></a>
### BR-OAU-005：客户端认证与证明不可降级

认证方式由登记 client 决定，精确规则见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。secret 校验由 App 专用内部接口执行；Auth 必须把验证结果与本次配置 revision 对齐。PKCE challenge 已存在时没有 verifier/不匹配均失败；未提供 challenge 时提交 verifier 也拒绝，避免意外忽略证明。client 类型、code 绑定、nonce 和 verifier 不能由兑换请求重新指定。

<a id="br-oau-006"></a>
### BR-OAU-006：授权码一次性兑换与重放处置

code 只能消费一次；校验失败不消费正确 code。并发兑换通过原子状态迁移至多一个成功；发现已正确绑定到调用 client 的 code 被再次兑换时，返回 invalid_grant 并撤销该 code 已产生的 token family（包含 access token，即使没有 refresh token）。先验证 client 和 code 的绑定/证明，不能让匿名猜测触发他人 family 撤销。

签发结果未知时不返回秘密、不缓存可再次取出的明文 token；客户端重新发起授权。事务回滚不能留下已消费 code 却无对应凭据的可见中间状态。

<a id="br-oau-007"></a>
### BR-OAU-007：独立凭据与有界权限

access token 记录 tokenId/digest、authId、clientId、applicationId、grantId/revision、App 资格版本、scope、audiences、familyId、签发/到期/撤销状态。scope 来自 code 且仍为当前 grant 和应用许可的子集；audiences 只由 Auth 部署的 scope 资源映射得出。只含 openid/email 的 token 仅可访问 UserInfo，不因此获取其它资源。

ID Token 是面向 client 的登录证据，格式和 pairwise sub 由 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md) 定义；不与 access token 复用值、用途或 verifier。用户的资料/身份关联不是默认 claims，subject 不能由客户端指定。

<a id="br-oau-008"></a>
### BR-OAU-008：签发一致性与故障关闭

最终写入与 grant 撤销、family 撤销及用户可用状态检查共用 Auth 本地原子栅栏。App 外部快照只在限定时间有效，不声称跨库事务。secret 轮换、client 禁用、发布/Tester 资格变化、当前 Version 不再包含 code 绑定的精确 redirect URI，或凭据记录与快照不一致，均拒绝本次兑换。

未知/过期/错误 code 及错误 verifier 统一 invalid_grant；服务故障用 temporarily_unavailable。日志、审计和 metrics 不记录任何 token、code、secret 或 verifier。

## 验收场景

- PUBLIC S256、CONFIDENTIAL Basic、CONFIDENTIAL Basic+S256 三条正向路径产生不同 id_token/access_token。
- 缺 secret、认证来源冲突、PKCE 降级、跨 client code、redirect 不匹配失败。
- 并发兑换仅一份凭据提交，正确重放撤销原 family；错误 client 不能撤销他人 family。
- ID Token aud/nonce/at_hash 正确，同 sector sub 稳定且与学生关联无关。
- 授权撤回、App 快照过期、事务/签名失败、未知提交不会多发可用凭据。

## 依赖与实现边界

依赖 UC-AUTH-014、UC-APP-018/019 与 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。没有 UC-AUTH-016 时不签 refresh token；UC-AUTH-017 提供标准 UserInfo，UC-AUTH-019 为业务资源校验 access token。Mongo unique/TTL 索引与事务写入栅栏在实现工作包落实，不以 TTL 删除代替在线状态判断。

## 变更记录

- 2026-09-27：code 兑换以完整 App runtime/Tester tuple 重新解析，并确认当前批准 Version 仍包含 code 绑定的精确 redirect URI。
