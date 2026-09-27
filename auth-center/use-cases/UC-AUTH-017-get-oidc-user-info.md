# UC-AUTH-017：读取 OIDC 用户信息

状态：`PROPOSED`

## 目标与范围

持有效应用 access token 读取标准 UserInfo。只披露已授予且当前允许的 claims，沿用“用户主动提供、平台校验格式、不保证学生资料真实性”的边界。

## 输入与输出

GET/POST /userinfo，唯一 Authorization: Bearer access token。返回 application/json，最小 {"sub":"<pairwise subject>"}；无业务 envelope。完整认证/错误格式见 [OAuth/OIDC v1](../../platform/contracts/oauth-oidc-v1.md)。

## 主流程

1. Auth 自行查 access 摘要并在线验证用户、client、App 资格、grant/family、期限与 UserInfo audience。
2. 确认 openid，根据实际 token scope 与现有数据进行最小投影。
3. 返回与本 client ID Token 完全相同的 sub，不回传 token 或内部身份上下文。

## 业务规则

<a id="br-oau-012"></a>
### BR-OAU-012：UserInfo 在线授权与 subject 一致性

UserInfo 使用与 UC019 相同的有效 token 判断，但不递归调用委托签发 RPC，也不接受平台 Session 或 ID Token。必须有 openid 及 UserInfo audience。sub 来自共享协议的既有 pairwise 映射；缺失映射视为服务数据不一致，不能临时生成不同 subject。

应用必须核对 UserInfo sub 与已验证 ID Token sub 相同；不相同则拒绝绑定资料。

<a id="br-oau-013"></a>
### BR-OAU-013：最小资料披露

首版仅实现 openid→sub，email→当前激活邮箱的 email/email_verified=true；没有激活邮箱时同时省略两项。平台确认邮箱控制权不代表确认学生身份。资料 KV 中叫 email 的字段不能替代激活邮箱事实。

不默认支持 profile scope，不遍历全部动态资料，不披露 authId、学校密码、学号、association 标识、developer/reviewer 状态。未来资料字段 scope 映射须明确字段语义、授权文案和数据来源，再增加接口投影。token 有 email 才能返回邮箱，应用声明 email 或平台已绑定邮箱本身都不构成用户授权。

<a id="br-oau-014"></a>
### BR-OAU-014：资料读取的撤销与故障语义

UserInfo 在 Auth 本地一致检查点确认授权和读取投影；撤销提交后开始的读取必须拒绝。App 快照边界沿用委托契约，不承诺跨库串行。响应 no-store；空资料按字段省略，不通过上传/抓取学校信息补齐。依赖错误失败关闭，不能降级输出未授权的缓存资料。

## 验收场景

- openid-only 只返回 sub；email 获批且用户同意后才返回当前激活邮箱。
- 未绑定、邮箱更换、资料 KV 伪造 email 均按权威源投影；不自动披露其他字段。
- ID Token/Session 冒充 Bearer、跨用途 token、撤回/过期/family 撤销拒绝。
- 同一 sector subject 一致，不同 sector 不相关；同 client 的 ID Token/UserInfo sub 完全相同。

## 依赖与实现边界

依赖 UC015/018、UC011 激活邮箱事实、UC-APP-019。userinfo 标准 HTTP 适配器不经过 Session middleware，不能沿用本人资料查询直接返回全量资料。
