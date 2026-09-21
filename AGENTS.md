# AGENTS.md — iWUT 设计文档仓库

本仓库保存 iWUT 各 bounded context 的权威设计文档，当前包含 `app-center/`。

## 内容分工

| 路径 | 性质 | 权威性 |
| --- | --- | --- |
| `app-center/use-cases/UC-*.md` | UC 正文，内含 `BR-*` 权威定义 | **权威** |
| `app-center/adr/ADR-*.md` | 架构决定 | **权威** |
| `app-center/query-contracts/` | 读模型语义 | **权威** |
| `app-center/*.md`（README、vision、domain-model 等） | 规范与摘要 | 规范性以其中的 `BR-*` / `ADR-*` 引用为准 |
| `app-center/briefs/*.md` | **生成物**，工作包设计输入 | **非权威**，冲突时以源文件为准 |
| `tools/gen_brief.py`、`tools/brief-specs/` | brief 生成器与范围 spec | 工程代码 |
| `tools/registry.py` | 注册表机械列的生成与漂移检查 | 工程代码 |
| `tools/git-hooks/` | 本仓库的 git hooks | 工程代码 |

同一内容不得有两个权威定义。需要复用规则时引用原 ID 与锚点，不复制正文。

## 提交规范（强制）

每个 commit 的**标题**必须使用以下格式：

```text
:emoji: type: title
```

- `:emoji:` 使用可读的 gitmoji shortcode。
- `type` 必须是下列之一：

  ```text
  feat fix docs test refactor perf build ci chore revert
  ```

- `title` 使用英文、祈使式、简洁描述实际变化，不以句号结尾。

示例：

```text
:memo: docs: record acceptance for UC-APP-003
:sparkles: feat: add brief generator for work packages
:white_check_mark: test: verify brief staleness detection
:recycle: refactor: drop duplicated rule restatements from summaries
```

校验正则：

```text
^:[a-z0-9_+-]+: (feat|fix|docs|test|refactor|perf|build|ci|chore|revert): .+$
```

一个 commit 只承担一个可审查目的。生成物（`app-center/briefs/`）与触发它的源文件放在同一个 commit 中。

## brief 的生成与检查

brief 是给**单个工作包**用的设计输入，由脚本从权威正文抽取。生成是确定性的：同样的源必然产出逐字节相同的 brief。

```bash
# 横切工程基线（ADR 变更时才需重新生成）
python3 tools/gen_brief.py --baseline

# 单个 work package
python3 tools/gen_brief.py UC-APP-003

# 全部 curated brief
python3 tools/gen_brief.py --all

# 校验磁盘上的 brief 是否与源一致
python3 tools/gen_brief.py --check --all
```

**修改任何被 brief 引用的源文件（UC、ADR）后，必须在同一个 commit 中重新生成对应 brief。** pre-commit hook 会校验这一点，不一致即拒绝提交。

生成是 **fail closed** 的：spec 选中的小节、`BR-*` 或 ADR 章节在源文件中找不到时，生成直接失败并列出全部问题，不会产出残缺 brief。无法解析的设计输入不允许被静默省略。

## 注册表检查

`app-center/design-registry.md` 是索引，不是第二权威。它的**机械列**（ID / 标题 / 状态 / 权威位置）与「下一个可分配编号」表由 `tools/registry.py` 生成或校验；人类专属列（`BR-*` 的 `类型`、`备注`、`替代项`）仍手工维护，工具不碰。

```bash
# 校验机械列与源文档一致、ID 空间两个方向都闭合
python3 tools/registry.py --check

# 只重新生成「下一个可分配编号」表
python3 tools/registry.py --write
```

`--check` 覆盖：标题/状态漂移、权威位置链接失效、BR 锚点缺失、重复 ID、源文件里存在但注册表没有的 UC/BR、业务主题与行不匹配、Next ID 表过期。

已废弃、不再分配的编号声明在注册表内的 `<!-- retired: ... -->` 行。**它是 Next ID 计算的输入**：新增已废弃编号时必须改那一行，否则编号可能被重新分配。工具不会自动改写它。

**漂移时修源文档或修注册表行，不要两边同时手改。** `--write` 只处理可推导的 Next ID 表，不会替你消除语义漂移。

## git hooks

hooks 存放在 `tools/git-hooks/` 并纳入版本控制，通过 `core.hooksPath` 生效：

```bash
git config core.hooksPath tools/git-hooks
```

| hook | 作用 |
| --- | --- |
| `pre-commit` | 运行 `gen_brief.py --check --all` 与 `registry.py --check`；brief 过期或注册表漂移则拒绝提交 |
| `commit-msg` | 校验标题是否符合上面的 `:emoji: type: title` 格式；不符合则拒绝提交 |

新克隆仓库后必须执行一次上面的 `git config`，否则 hooks 不生效。

## 不要做

- 不要手工编辑 `app-center/briefs/` 下的文件；改源文件或 `tools/brief-specs/` 后重新生成。
- 不要把权威文档复制进代码仓库作为第二权威来源；代码仓库只通过 `AGENTS.md` 引用本仓库。
- 不要在权威文档里复述其它权威文档已定义的规则；需要引用时链接对应 ID 与锚点。
