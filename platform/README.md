# 平台共享设计文档

状态：**权威** — 本目录保存跨 bounded context 的设计契约，只有真正跨系统的内容才放这里。

## 放什么、不放什么

| 内容 | 权威位置 | 说明 |
| --- | --- | --- |
| App Center 的业务语义（UC、BR、领域模型、能力内 ADR） | `app-center/` | 仍由 App Center 的正文与 `app-center/design-registry.md` 管理 |
| Auth Center 的业务语义（UC、BR、目录所有权） | `auth-center/` | 仍由 Auth Center 的正文与 `auth-center/design-registry.md` 管理 |
| 可执行 Proto / API 定义 | 独立 API 仓库 | 本仓库不放可执行契约，只放设计契约 |
| 跨系统决定（例如身份信任模型、gRPC-Web 终止位置） | `platform/adr/` | 记录为什么选择某种跨系统方案及其后果 |
| 稳定的身份、消息、路由格式 | `platform/contracts/` | 记录多方必须共同遵守、可做契约测试的格式与语义 |
| 某个能力的实现细节、单系统决策 | 对应能力目录 | 不要为了“看起来集中”而提升到平台层 |

判断标准：**如果一条规则只对一个 bounded context 成立，它就不属于 `platform/`。** 平台文档记录的是系统之间的约定，例如“可信身份 JWS 由谁签发、入口如何路由”，而不是某个服务内部如何实现。

## 权威边界

- 同一内容只能有一个权威定义。`platform/` 的文档**不复制** `app-center/`、`auth-center/` 或 Gateway 已有的正文；需要引用时链接原 ID 与锚点。
- `platform/` 文档**不登记进 `app-center/design-registry.md`**。那份注册表是 App Center 的索引，不是跨系统登记表。
- `platform/` 文档可以定义自己的跨系统决定或契约 ID；本仓库当前不为它生成注册表。
- 例如，采用“Auth Center 签发短期、指定 audience 的 JWS，Gateway 转发，App Center 本地验签”属于 `platform/adr/`；JWS header/claims、audience、有效期约束和转发载体属于 `platform/contracts/`。App Center 如何把已验证身份用于某个 UC，仍属于 `app-center/`。
- `platform/` 下的文档是权威设计正文，但**不自动进入任何 brief**。

## 与 brief 生成的关系

当前 App 设备认证与 Session 的跨端格式见 [auth-device-session-v1](contracts/auth-device-session-v1.md)，包括公钥、签名输入、学号关联声明、Session 载体、RPC 鉴权表及公开测试向量。Auth 自有业务和存储规则仍由对应 UC 拥有。

平台共享文档默认**不进入 engineering baseline**。只有某个 per-UC spec 在 `shared_sections` 里显式选择时，才会被抽取进那一份 brief：

```json
{
  "uc": "UC-APP-003",
  "shared_sections": {
    "platform/contracts/trusted-identity-v1.md": ["JWS Claims", "校验顺序"]
  }
}
```

规则：

- 键是**相对 docs 仓库根**的 POSIX 路径（`platform/…`），不是相对 `app-center/` 的路径，也不需要登记进 registry。
- 值是章节路径列表，语法与 `adr_sections` / `uc_sections` 相同，支持 `父节/子节`。
- 渲染顺序稳定：文件按路径字典序，章节按 spec 中的顺序。
- 选中的共享章节会出现在 brief 正文、未纳入小节索引、溯源表（含 sha256）与源体积统计中。
- 从 `app-center/briefs/` 输出位置看，平台文档里的相对链接会被重写为仍然正确的路径（例如 `../../platform/…`）。

生成是 **fail closed** 的：绝对路径、`..`、解析后经 symlink 逃逸 docs 仓库的路径、缺失文件、非普通 Markdown 文件、缺失章节都会被收集为问题并让生成失败，不会产出残缺 brief。

## 新增平台文档时

1. 先确认这条规则确实跨系统，且不能在原能力权威文档里定义。
2. 跨系统选择写入 `platform/adr/`，稳定格式写入 `platform/contracts/`；用 `#` 标题与 `##` / `###` 章节组织，便于 `shared_sections` 选择。
3. 需要被工作包使用时，在对应 `tools/brief-specs/<UC>.json` 里添加 `shared_sections`，不要复制正文到 `app-center/`。
