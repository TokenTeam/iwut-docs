# UC-AUTH-018：查看及收回本人应用授权

状态：`PROPOSED`

## 目标与范围

用户用有效平台 Session 查看自己的应用授权、撤回部分 scopes 或全部授权；应用另可通过标准 revocation endpoint 定向撤销自己持有的 token。两类入口主体与影响范围必须分开。

## 输入与输出

本人接口：ListOwnApplicationGrants(cursor,pageSize≤50)、RevokeOwnApplicationGrant(grantId,expectedRevision,mode=ALL|SCOPES,scopes[])。返回当前 scope/status/revision 与最小应用展示信息，不含 token。

应用接口：POST /revoke，token、可选 token_type_hint（access_token/refresh_token），登记 client 的认证，见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。PUBLIC 提交 client_id；confidential 使用 Basic。

## 主流程

1. 本人查询从当前 Session 解析 authId，不接受任意目标用户；只返回本人 grant。
2. 本人明确提交撤销范围，Auth 校验归属、revision，原子收缩/撤销 grant 并记录审计。
3. 旧 code、access、refresh 后续通过 grant revision 检查统一失效；不必同步遍历每条 token 文档。
4. 应用 token 撤销先认证 client，匹配 token 所属 client 后撤销对应 token 或 family；对未知/已撤销值幂等成功。

## 业务规则

<a id="br-oau-015"></a>
### BR-OAU-015：本人查询和范围撤销

本人入口仅接受有效 ACTIVE USER Session，目标从 Session 决定。列表按 client 分组展示应用、授权时间、scope 和当前状态，同一 Application 的 public/confidential client 分开显示，不能误导成已一键撤销所有接入。

允许撤回 required scope，包括 openid；应用可能不能继续运行，UI 应说明，但服务端不得强制保留。撤回 openid 等同撤销该 grant 全部；其余部分撤回保留剩余集合。App 暂时不可用时仍允许本人列表/撤销，用存储的 application/client ID 与历史展示快照标明名称可能过时；不因无法查询 App 阻止用户收回授权。

<a id="br-oau-016"></a>
### BR-OAU-016：撤销版本和重授隔离

首次全部撤销或实际 scope 收缩都原子递增 revision，并与签发/确认共用 grant 写入栅栏。全部撤销置 REVOKED、清空当前集合；记录不可变审计，保留 ID 与历史版本。expectedRevision 不匹配返回冲突及当前状态，不能用旧 UI 覆盖后来授权；同 revision 下无变化的重复操作返回当前结果，不额外递增。

任何旧 token/code 的 grant revision 不等于当前值即不可用，即使它仅使用保留下来的 scope。重新同意通过 UC014 产生新 revision，不能复活旧凭据；已同意但尚未兑换的 code 同样受约束。

<a id="br-oau-017"></a>
### BR-OAU-017：应用 token 撤销与平台登录分离

客户端撤销 access token 仅撤销该条 access；撤销 refresh token 撤销整个 family 及其 access tokens。已消费 refresh 仍能识别其 family；未知、不属于调用 client 或已撤销值均按协议成功且不改变他人记录。该入口不需要原平台 Session，不接受把学生关联或 email 当 token。

用户授权撤回不删除平台用户、不撤销其平台 Session，不保证第三方本地会话立即退出或删除已取得数据。应用若希望撤回整个 grant 应引导用户到本人授权管理，不把一个 token 的 revocation 偷换为全应用授权删除。

## 验收场景

- 越权 grantId、错误 revision、跨用户列表拒绝；App 离线仍能撤回。
- 部分撤回后所有旧代 token 失效，重新授权不复活；required scope 也可撤回。
- 与 code 兑换/refresh/委托签发并发，必须有明确先后顺序，无撤销后新签成功。
- PUBLIC/CONFIDENTIAL revocation，错误 hint fallback 查询受支持类型、未知 token 幂等、外部 client 不可撤销他人 token。

## 依赖与实现边界

依赖平台 Session 与 UC014 grant 模型；和 UC015/016/019 一起实现撤销栅栏。本人 API 的 Proto/HTTP annotation 在 API 仓库固定，必须走有效 Session，不能错误地标为匿名标准端点。
