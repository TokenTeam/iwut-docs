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

## git hooks

hooks 存放在 `tools/git-hooks/` 并纳入版本控制，通过 `core.hooksPath` 生效：

```bash
git config core.hooksPath tools/git-hooks
```

| hook | 作用 |
| --- | --- |
| `pre-commit` | 运行 `gen_brief.py --check --all`；brief 缺失或过期则拒绝提交 |
| `commit-msg` | 校验标题是否符合上面的 `:emoji: type: title` 格式；不符合则拒绝提交 |

新克隆仓库后必须执行一次上面的 `git config`，否则 hooks 不生效。

## 不要做

- 不要手工编辑 `app-center/briefs/` 下的文件；改源文件或 `tools/brief-specs/` 后重新生成。
- 不要把权威文档复制进代码仓库作为第二权威来源；代码仓库只通过 `AGENTS.md` 引用本仓库。
- 不要在权威文档里复述其它权威文档已定义的规则；需要引用时链接对应 ID 与锚点。
