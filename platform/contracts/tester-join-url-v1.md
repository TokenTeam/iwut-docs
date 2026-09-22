# Tester 加入 URL v1 契约

状态：`ACTIVE`

## 目的与范围

本契约定义 App Center URL builder 与前端扫描器共同使用的加入凭证格式。链接生成与轮换规则属于 [UC-APP-008](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md)，加入行为与用户身份属于 [UC-APP-009](../../app-center/use-cases/UC-APP-009-join-application-as-tester.md)。

当前允许使用 mock URL 入口，不要求目标页面真实存在。App Center 不访问、解析 DNS 或验证该入口可达性；mock 只指入口地址，链接 ID、secret、持久化和生命周期仍使用真实实现。

## URL 格式

```text
{prefix}#joinLinkId={joinLinkId}&secret={secret}
```

- prefix 是绝对 HTTP 或 HTTPS URL，具有非空 host，可包含路径；不包含 userinfo、query 或 fragment。保留合法前缀的路径和末尾斜杠，不额外拼接路径。
- fragment 使用 URL query 参数编码，生成顺序固定为 `joinLinkId`、`secret`，每个键出现一次。
- joinLinkId 是服务端生成的小写规范 UUIDv7；secret 使用 [BR-TST-004](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 的无填充 base64url 编码。
- 不在 URL 中加入用户身份、applicationId、RPC major 或 Version；后端按 joinLinkId 解析所属 Application，按认证上下文确定当前用户。
- secret 只放在 fragment，不放入 URL 路径或 query。完整 joinUrl 仍是敏感值，遵循 [BR-TST-004](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-004) 和 [BR-TST-008](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#br-tst-008)。

## 前端解析与请求

前端扫码后解析 fragment，取得唯一的 joinLinkId 和 secret，并携带当前用户的登录认证凭证调用 UC-APP-009。joinLinkId 放在该用例定义的路径，secret 放在请求正文；用户身份遵循既有 [trusted-identity-v1](trusted-identity-v1.md)，不信任二维码或请求正文中自行声明的 authId。

扫码不等于加入，生成或轮换链接也不创建 Membership。前端应拒绝缺少或重复的凭证键、非法 UUIDv7 或不符合 BR-TST-004 编码的 secret，不把凭证送入日志或第三方统计。本轮后端不实现前端页面、扫码组件或 UC-APP-009。

## 契约测试要求

- URL builder 在默认 mock 前缀和自定义 HTTP/HTTPS 前缀下都能生成可解析的 URL，正确保留路径。
- fragment 恰好包含 joinLinkId 和 secret，能无损还原服务端生成值；路径和 query 不含 secret。
- 明确无效的前缀、ID 或 secret 不能生成部分有效结果；不执行 DNS/HTTP 调用。
- 持久化只保存 BR-TST-004 定义的哈希；成功响应可返回 joinUrl，失败响应、日志和 trace 不得返回它。

## 配置所有权

App Center 的环境变量名、默认 mock 前缀和启动失败规则见 [UC-APP-008 配置与临时入口](../../app-center/use-cases/UC-APP-008-create-or-rotate-tester-join-link.md#配置与临时入口)。以后只替换部署前缀时，fragment 契约保持不变。
