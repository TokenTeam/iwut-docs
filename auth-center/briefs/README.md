# Auth Center 工作包 brief

状态：`ACTIVE`

本目录的 `UC-AUTH-*.md` 是由 `tools/gen_brief.py` 生成的非权威派生制品，不手工修改；本 README 是维护说明。规则冲突时以 UC、BR、查询契约和平台契约为准。

## 已生成工作包

- [UC-AUTH-011](UC-AUTH-011.md)：邮箱注册、已有账号绑定/更换、独立签名协议及真实邮件投递；不包含 UC012/013。

- [UC-AUTH-010](UC-AUTH-010.md)：由有效 Session 签发短期、audience 绑定的用户 JWS；Gateway 转发独立验收，首版无 Redis。

- [UC-AUTH-005](UC-AUTH-005.md)：已接受的用户资料编辑及配套查询。覆盖首次完整交付，因此体积可能超过脚本默认的 300 行提示阈值。
- [UC-AUTH-006](UC-AUTH-006.md)：创建用户、设备证明、必填学生关联与启动前离线迁移。
- [UC-AUTH-007](UC-AUTH-007.md)：登录、Session 在线检查与 10 会话 LRU。
- [UC-AUTH-008](UC-AUTH-008.md)：当前 Session 的定向幂等撤销。
- [UC-AUTH-009](UC-AUTH-009.md)：本人设备凭据撤销与 Session 失效传播。

以上设计均已 ACCEPTED；006–009 包含外部 BR 和共享设备协议，客户端及 Gateway 交付边界仍需遵守。

## 生成与检查

```bash
python3 tools/gen_brief.py --all
python3 tools/gen_brief.py --check --all
```

脚本按 UC 前缀选择 Auth 或 App 的注册表和输出目录；`--all` 覆盖两者的已配置 spec。`--baseline` 仍只生成 App Center 工程基线，不自动把 App 专属 ADR 变成 Auth 约束。

抽取范围在 `tools/brief-specs/UC-AUTH-005.json` 至 `UC-AUTH-011.json`：`uc_sections` 选择本 UC 章节，`include_own_brs` 选择本 UC 规则，`query_sections` 显式选择当前 context 的 `query-contracts/` 章节，`shared_sections` 选择 `platform/` 章节。查询和平台路径均相对 docs 仓库根，缺失章节、非法路径或来源逃逸会使生成失败。

查询契约同样进入溯源摘要、未纳入章节索引和漂移检查；修改选中的源文档后重新生成。设计已接受不等于依赖已交付，brief 中的实现依赖仍必须满足。
