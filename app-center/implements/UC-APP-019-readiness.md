# UC-APP-019 开工检查

状态：`WAITING_FOR_DESIGN_DECISIONS`

检查日期：2026-09-29

## 结论

UC-APP-019 的 App Center 数据依赖已经满足：UC-APP-018 提供稳定 registration、client identity、状态 epoch 和 confidential credential；UC-APP-002/003/004/005/007 已提供 Version 依附 OAuth 配置、批准 snapshot、review-v2 与 TEST 发布前 registration/credential 检查；UC-APP-009/010 提供 Tester episode；UC-APP-016 提供当前公开 ApplicationProfile 指针。

Auth 的 MongoDB 权威 Scope Catalog 仍未交付，但不阻塞本 App provider 纵切片。UC-APP-019 按 BR-OAC-007 原样返回批准 snapshot 的 required/optional scopes，不调用 App 的 requestable cache，也不替 Auth 判断当前 enabled；Auth OAuth 用例在消费 provider 后完成最终 enabled 校验。

当前尚不能把 UC-APP-019 改为 `ACCEPTED` 或生成实现 brief，因为入站 service identity 会改变可执行 Proto、安全配置和兼容承诺。consent 展示投影已经确认并同步到权威文档。

## 待确认决定一：App Center 入站 service identity

[trusted-service-identity-v1](../../platform/contracts/trusted-service-identity-v1.md) 当前只固定了 Auth Center 作为提供方时的 caller registry 和 full method 权限。App Center 现有 `IdentityVerifier` 验证的是 Auth 签发的 USER/reviewer trusted identity；它不能替代 service identity，因为 service token 不携带 permissions，权限必须来自提供方本地 caller registry。

建议采用与 Auth 对称的 App Center 入站配置：

- `APP_CENTER_SERVICE_CALLERS_B64`：相同 registry JSON schema，首版只登记 `iwut-auth-center` 的状态、公钥和 permissions。
- `APP_CENTER_SERVICE_IDENTITY_MAX_TTL` 与 `APP_CENTER_SERVICE_IDENTITY_CLOCK_SKEW`：分别限制 service JWS 最大寿命与时钟偏差；默认沿用 Auth provider 的 `1m` 与 `30s`。
- App provider audience 固定为 `iwut-app-center`；只注册原生 gRPC，不生成 HTTP annotation。
- full method 固定映射到五个独立 permission：`app.oauth.client.read`、`app.oauth.client.verify`、`app.oauth.runtime.resolve`、`app.oauth.context.resolve`、`app.oauth.redirects.read`。未知方法、caller、kid、permission 和 disabled caller 一律失败关闭。

这组入站配置与现有 `APP_CENTER_SERVICE_IDENTITY_ID/KID/AUDIENCE/PRIVATE_KEY/TTL` 的出站 signer 配置并存，前者验证 Auth→App，后者签发 App→Auth，不能共用权限来源。

## 已确认决定二：consent 展示投影与 TEST 边界

ApplicationVersion 审核与 TEST/GREY/STABLE 槽位选择解耦：审核只产生渠道无关发布资格，各槽位独立选择已批准 Version 并施加自己的资格规则。TEST 是已审核的小范围用户分发；开发版客户端任意 URL 直开不属于 Publication。

`RuntimeConfiguration.display` 固定为：

```text
ApplicationDisplay {
  profileRevisionId: ApplicationProfileRevisionId
  displayName: string
  optional description: string
  optional icon: string
}
```

- TEST 槽位设置与运行解析都要求当前公开 Profile；三个内容字段只来自该 APPROVED revision。
- 没有 `currentPublishedProfileRevisionId` 时，设置 TEST 槽位或解析运行配置失败关闭，不使用 Application 技术名称。
- Profile 指针存在但 revision 缺失、跨应用、非 APPROVED 或内容损坏属于内部不变量异常；不得退回技术名伪装成功。
- 输出保持纯文本/不透明 icon 字符串，不增加 HTML、资产抓取或 URL 可用性检查。
- `expectedRuntimeVersion` 纳入 profileRevisionId；登录前后或 code 兑换时资料指针变化要求重新开始或重新展示。

## 已明确、无需新增决策

- `PUBLIC_PKCE` 的 `tokenEndpointAuthMethod=none`，`CONFIDENTIAL_SECRET` 为 `client_secret_basic`；OAuth/OIDC v1 已明确不支持 `client_secret_post`。
- provider 快照期限取允许上限 5 秒；Auth 在每个安全边界重查，不能把期限解释为期间事实不会变化。
- `GetApplicationPublishedRedirects` 纳入已有 registration 的 type；DISABLED identity 仍保留 sector 回调事实，缺少该 type registration 才排除。
- `VerifyClientSecret` 对未知 client、PUBLIC、DISABLED、revision 不匹配和错误 secret 统一返回 `verified=false`，不泄漏摘要或细分失败原因。
- UC019 只实现 App provider；Auth grant、code、token、sector/sub 和 Scope enabled 检查仍由 UC-AUTH-014 及后续用例交付。

## 确认后的动作

1. 确认并同步 UC-APP-019、`app-oauth-client-v1` 与 `trusted-service-identity-v1` 的入站 service identity 配置。
2. 将 UC-APP-019 及共享契约改为 `ACCEPTED`，建立 `tools/brief-specs/UC-APP-019.json` 并由脚本生成 brief。
3. 把代码仓库 `AGENTS.md` 切换到 UC-APP-019，提交文档工作包后开始串行实现和最终 `make check-auth-app` 验收。
