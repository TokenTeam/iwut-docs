# App Center 工作包 brief（生成的派生制品）

状态：`GENERATED` — 本目录下的 `*.md` 由脚本生成，**不是权威设计文档**，不要手工编辑。

## 这是什么

`brief` 是给**一个工作包**用的设计输入：由脚本从 `docs/app-center/` 的权威正文里，抽取这个工作包刚好需要的小节，合成一个文件。目的是让实现 agent 读一个小文件，而不是整份整份地加载 UC 和 ADR。

权威性完全不变：

- 业务语义仍然以 `UC-*` / `BR-*` 为唯一权威，架构选择仍然以 `ADR-*` 为唯一权威。
- brief 与源文件冲突时，**一律以源文件为准**。
- brief 头部记录每个源文件的 sha256；生成是确定性的，可复现、可校验。

## 两种 brief

| 文件 | 内容 | 变化频率 |
| --- | --- | --- |
| `_engineering-baseline.md` | **对每个工作包都成立、无所属能力**的架构决定（ADR-003 依赖方向、ADR-004 事务与迁移、ADR-005 错误分类） | 低 |
| `UC-APP-XXX.md` | 该 UC 的正文小节 + 本 UC 权威 BR + 外部引用 BR + **该能力专属的** ADR 小节 | 每个工作包 |

**分层规则**：能力专属的 ADR 不进基线，跟着真正需要它的 UC spec 走。ADR-001（Scope Catalog）只对解析 scope 的 UC 成立，所以它在这些 UC 的 spec 里；ADR-002（Publication 分区）、ADR-006（Proto/API 仓库）同理，分别归发布类与 transport 类工作包。判据很简单：**如果某一行对某个工作包毫无意义，它就不属于基线。**

先读一次基线，之后每个工作包只需要读对应的 per-UC brief。

## 生成

```bash
# 横切基线（架构决定变化时才需要重新生成）
python3 tools/gen_brief.py --baseline

# 单个工作包
python3 tools/gen_brief.py UC-APP-003

# 只看抽取结果和体积报告，不落盘
python3 tools/gen_brief.py UC-APP-003 --stdout

# 不依赖手写 spec，用自动小节选择（用于发现 spec 是否过窄/过宽）
python3 tools/gen_brief.py UC-APP-003 --no-spec

# 校验磁盘上的 brief 是否与源一致（pre-commit hook 会跑这个）
python3 tools/gen_brief.py --check --all
```

脚本每次都会打印体积报告（brief vs 整文件加载），brief 超过 `--max-lines`（默认 300）会告警——这是"工作包太大"的机械信号。

## 范围由谁决定

抽取是机械的，**范围是人为判断**，写在 `tools/brief-specs/*.json`：

```json
{
  "uc_sections": ["目标与范围", "主流程", "..."],
  "adr_sections": { "ADR-003": ["决定", "Port 所有权"] }
}
```

`adr_sections` 支持子节路径（`"决定/第一阶段缓存"`），因为 ADR 的 `## 决定` 下常有 `###` 子节。

- `include_own_brs` / `include_external_brs`：是否纳入本 UC 权威 BR 与正文里引用的其他 UC 的 BR。
- 不写 `uc_sections` 时，默认取该 UC 所有 `##` 小节（`业务规则` 除外，它由 BR 块单独渲染）。

**调整范围时不要动权威正文**，只改 spec；权威正文只因为设计变化而改。

## brief 不覆盖的问题

brief 刻意不是全量设计。实现 agent 遇到未覆盖的问题时：

1. 先在 brief 的「未纳入本 brief 的源小节」里找标题，命中就按锚点查阅源文件。
2. 仍不确定，或发现两条权威规则冲突：停止受影响的实现，产出结构化 gap，路由给读全量概述文档的设计任务。
3. 设计更新权威正文后，重新生成 brief，再继续实现。

这条链路是「不自行发明业务行为」的落地方式，也是保持实现 agent 上下文窄的关键。
