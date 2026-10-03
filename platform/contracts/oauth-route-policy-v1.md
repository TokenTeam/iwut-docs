# OAuth route policy v1

状态：`ACTIVE` — Auth UC019 的签发策略输入；Gateway 消费与资源验签仍须按 UC-GW-002 单独验收。

## 格式与摘要

跨服务权限语义引用 [OAuth delegation v1](oauth-delegation-v1.md)，本文件只固定可执行策略格式。Auth 从本地受信 JSON 文件加载，版本固定为整数 1，未知字段和重复 routeId 拒绝。首版无任意 rewrite 表达式：`path` 已是转发到资源服务后的路径模板；Gateway 必须使用同一固定重写结果。

```json
{
  "version": 1,
  "routes": [
    {
      "routeId": "resource-read",
      "audience": "resource-service",
      "protocol": "HTTP",
      "method": "GET",
      "path": "/items/{id}",
      "requiredScopes": ["items.read"],
      "allowedChannels": ["TEST"]
    }
  ],
  "callers": {
    "iwut-gateway": {
      "routes": ["resource-read"],
      "audiences": ["resource-service"]
    }
  }
}
```

示例资源并非平台已交付的默认能力。HTTP method 只允许 GET/POST/PUT/PATCH/DELETE/HEAD；模板仅支持字面路径段与完整 `{parameter}` 段。拒绝空段、dot segment、模板内 percent encoding、反斜线、query/fragment，以及相同协议/method 下可能重叠的模板。GRPC 的 method 是完整 `/package.Service/Method`，path 必须为空；不提供流式 RPC。

`policy_digest` 是以下规范字节的 SHA-256、小写十六进制，固定 64 字符：

1. 根对象只保留 `version`、`routes`，按此顺序输出。
2. routes 按 routeId 升序；每项字段按示例顺序全部输出，包含 GRPC 的空字符串 path。
3. requiredScopes、allowedChannels 按字符串升序输出、不得重复；不允许 null。
4. 使用 Go `encoding/json.Marshal` 的紧凑 UTF-8 JSON 编码规则，无 BOM、缩进或尾随换行；字符串转义采用其默认 HTML escaping。
5. `callers` 是 Auth 本地授权注册表，不进入共享摘要。服务身份必须另外具有 `auth.oauth.delegation.issue`；同时匹配本表 route 与 audience，不能只凭服务权限选任意 audience。

Auth 与 Gateway 对同一受信输入应生成完全相同摘要。摘要不匹配返回依赖/策略不可用，不降级使用请求方提供的 scope 或 audience。

## 启用与时钟

Auth 启用非空业务路由时，部署须明确声明资源委托验证已就绪，并确保每个 required scope 在其当前 Catalog 中启用且映射到该 audience；无完整映射时启动失败。声明不替代真实资源服务验收。

签发还需读取本机受信时间监控进程原子写入的 JSON：`{"observedAt":"<RFC3339 UTC>","offsetMillis":0}`。观测不得来自未来，年龄不得超过 10 秒，绝对偏移不得超过 1000 毫秒；缺失、损坏、过期或越界时停止签发并返回 UNAVAILABLE。签发开始与提交前均检查，不把一次启动时的健康状态永久复用。监控进程、目录权限与时钟同步由部署负责；调用方不得提供这个文件或其值。
