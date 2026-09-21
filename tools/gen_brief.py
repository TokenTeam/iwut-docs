#!/usr/bin/env python3
"""Generate a task-scoped design brief from the authoritative App Center docs.

A brief is a *derived, non-authoritative* artifact: it extracts exactly the
design text one work package needs, so an implementation agent reads one small
file instead of whole use-case and ADR files. Conflicts always resolve to the
sources listed under "溯源" in the generated brief.

Usage (run from the docs repository root):
    python3 tools/gen_brief.py UC-APP-003
    python3 tools/gen_brief.py --baseline
    python3 tools/gen_brief.py --all
    python3 tools/gen_brief.py --check --all
    python3 tools/gen_brief.py UC-APP-003 --stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
DOCS = WORKSPACE / "docs" / "app-center"
REGISTRY = DOCS / "design-registry.md"
DEFAULT_SPEC_DIR = WORKSPACE / "docs" / "tools" / "brief-specs"

# Canonical paths as seen from the docs repository root. They are fixed rather
# than derived from the current directory so that generated briefs are
# byte-identical no matter where the generator is invoked.
SCRIPT_REL = "tools/gen_brief.py"
SPECS_REL = "tools/brief-specs"

# Authorization prose lives here; it is rendered from the BR blocks instead.
BR_SECTION_TITLE = "业务规则"
DEFAULT_UC_EXCLUDES = {BR_SECTION_TITLE}

ID_CELL = re.compile(r"`((?:UC|BR|ADR)-[A-Z]*-?\d+)`")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CJK = re.compile(r"[\u3400-\u9fff\u3000-\u303f\uff00-\uffef]")
HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*$")
FENCE = re.compile(r"^\s*```")
BR_ANCHOR = re.compile(r'^<a id="(br-[a-z]+-\d+)"></a>$')
BR_HEADING = re.compile(r"^###\s+(BR-[A-Z]+-\d+)")
BR_TOKEN = re.compile(r"\b(BR-[A-Z]+-\d+)\b")
BR_RANGE = re.compile(
    r"(BR-[A-Z]+-\d+)\s*(?:至|到|~|～|–|—|\.\.\.?)\s*(BR-[A-Z]+-\d+)"
)


# --------------------------------------------------------------------------- registry


def load_registry() -> tuple[dict, dict, dict]:
    """Return (use_cases, business_rules, adrs) parsed from the registry tables."""
    use_cases: dict[str, dict] = {}
    business_rules: dict[str, dict] = {}
    adrs: dict[str, dict] = {}

    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        ids = ID_CELL.findall(line)
        link = MD_LINK.search(line)
        if not ids or not link:
            continue  # Next-ID rows and prose mentions carry no authoritative link.
        rid = ids[0]
        target = link.group(1).partition("#")[0].strip()
        # cell 0 is the id, cell 1 the title, cell 2 the status/type.
        cells = [cell.strip().replace("`", "") for cell in line.strip().strip("|").split("|")]
        meta = {"title": cells[1], "path": target}

        if rid.startswith("UC-APP-"):
            meta["status"] = cells[2]
            use_cases[rid] = meta
        elif rid.startswith("BR-"):
            meta["type"] = cells[2]
            business_rules[rid] = meta
        elif rid.startswith("ADR-"):
            meta["status"] = cells[2]
            adrs[rid] = meta

    return use_cases, business_rules, adrs


def read_doc(rel_path: str) -> str:
    return (DOCS / rel_path).read_text(encoding="utf-8")


# --------------------------------------------------------------------------- markdown


def heading_marks(text: str) -> tuple[list[str], list[tuple[int, int, str]]]:
    """Return (lines, [(line_index, level, title)]) ignoring fenced code blocks."""
    lines = text.splitlines()
    marks: list[tuple[int, int, str]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            marks.append((index, len(match.group(1)), match.group(2)))
    return lines, marks


def section_paths(text: str) -> list[str]:
    """All selectable paths: `## 决定`, `## 决定/### 子节`, and `### …` under `##`."""
    _, marks = heading_marks(text)
    paths: list[str] = []
    for index, (_, level, title) in enumerate(marks):
        if level == 2:
            paths.append(title)
        elif level == 3:
            parent = next((marks[j][2] for j in range(index - 1, -1, -1) if marks[j][1] == 2), None)
            if parent:
                paths.append(f"{parent}/{title}")
    return paths


def extract_section(text: str, path: str) -> str | None:
    """Extract a section body by path, e.g. `决定` or `决定/第一阶段缓存`."""
    parts = path.split("/")
    target_level = len(parts) + 1
    lines, marks = heading_marks(text)
    start = None
    for index, (_, level, title) in enumerate(marks):
        if level != target_level or title != parts[-1]:
            continue
        if target_level == 3:
            parent = next((marks[j][2] for j in range(index - 1, -1, -1) if marks[j][1] == 2), None)
            if parent != parts[0]:
                continue
        start = index
        break
    if start is None:
        return None
    begin = marks[start][0]
    end = len(lines)
    for index in range(start + 1, len(marks)):
        if marks[index][1] <= target_level:
            end = marks[index][0]
            break
    return "\n".join(lines[begin:end]).rstrip()


def demote(text: str, levels: int) -> str:
    """Push embedded headings down so the brief keeps a single outline."""
    lines, _ = heading_marks(text)
    out: list[str] = []
    in_fence = False
    for line in lines:
        if FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        match = HEADING.match(line) if not in_fence else None
        out.append("#" * (len(match.group(1)) + levels) + " " + match.group(2) if match else line)
    return "\n".join(out)


def rewrite_links(text: str, src_rel: str) -> str:
    """Make relative links resolve from `briefs/` instead of the source directory."""
    src_dir = posixpath.dirname(src_rel)
    if not src_dir:
        return text

    def replace(match: re.Match) -> str:
        target = match.group(1)
        if target.startswith(("#", "/", "http://", "https://", "mailto:")):
            return match.group(0)
        path, separator, anchor = target.partition("#")
        if not path or path.startswith("../"):
            return match.group(0)
        return f"](../{src_dir}/{path}{separator}{anchor})"

    return re.sub(r"\]\(([^)]+)\)", replace, text)


def embed(text: str, src_rel: str, levels: int) -> str:
    return demote(rewrite_links(text, src_rel), levels)


def collapse_omitted(paths: list[str]) -> list[str]:
    """Drop `parent/child` entries when `parent` is already listed."""
    present = set(paths)
    return [p for p in paths if "/" not in p or p.split("/")[0] not in present]


def br_block(text: str, br_id: str) -> str | None:
    """Extract one BR authority block; the anchor line is dropped.

    The anchor line normally sits immediately *before* the `### BR-…` heading,
    so the scan for the block end must start at the heading, not at the anchor.
    """
    lines = text.splitlines()
    anchor = f'<a id="{br_id.lower()}"></a>'

    heading_index = None
    for index, line in enumerate(lines):
        match = BR_HEADING.match(line.strip())
        if match and match.group(1) == br_id:
            heading_index = index
            break

    if heading_index is not None:
        start = heading_index
        if heading_index > 0 and lines[heading_index - 1].strip() == anchor:
            start = heading_index - 1
        scan_from = heading_index
    else:
        anchor_index = next((i for i, line in enumerate(lines) if line.strip() == anchor), None)
        if anchor_index is None:
            return None
        start = anchor_index
        scan_from = anchor_index

    end = len(lines)
    for index in range(scan_from + 1, len(lines)):
        stripped = lines[index].strip()
        if BR_ANCHOR.match(stripped) or re.match(r"^#{1,3}\s", stripped):
            end = index
            break

    block = [line for line in lines[start:end] if not BR_ANCHOR.match(line.strip())]
    return "\n".join(block).strip() or None


def mentioned_brs(text: str) -> list[str]:
    """BR ids referenced by a UC, with `BR-A-001 至 BR-A-005` ranges expanded."""
    seen: list[str] = []
    for match in BR_RANGE.finditer(text):
        first, second = match.group(1), match.group(2)
        topic_a, number_a = first.rsplit("-", 1)
        topic_b, number_b = second.rsplit("-", 1)
        if topic_a != topic_b:
            continue
        for number in range(int(number_a), int(number_b) + 1):
            seen.append(f"{topic_a}-{number:03d}")
    seen.extend(match.group(1) for match in BR_TOKEN.finditer(text))
    ordered: list[str] = []
    for br_id in seen:
        if br_id not in ordered:
            ordered.append(br_id)
    return ordered


# --------------------------------------------------------------------------- helpers


def sort_brs(ids) -> list[str]:
    def key(br_id: str):
        topic, number = br_id.rsplit("-", 1)
        return (topic, int(number))

    return sorted(set(ids), key=key)


def short_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def estimate_tokens(text: str) -> int:
    """Rough BPE estimate: ~1 token per CJK char, ~1 per 3.6 non-CJK chars."""
    cjk = len(CJK.findall(text))
    return int(cjk + (len(text) - cjk) / 3.6)


def compact_number_list(ids: list[str]) -> str:
    if not ids:
        return "—"
    groups: list[tuple[str, list[int]]] = []
    for br_id in sort_brs(ids):
        topic, number = br_id.rsplit("-", 1)
        if groups and groups[-1][0] == topic:
            groups[-1][1].append(int(number))
        else:
            groups.append((topic, [int(number)]))
    parts = []
    for topic, numbers in groups:
        numbers = sorted(numbers)
        if len(numbers) == 1:
            parts.append(f"`{topic}-{numbers[0]:03d}`")
        elif len(numbers) == 2:
            parts.append(f"`{topic}-{numbers[0]:03d}`、`{topic}-{numbers[1]:03d}`")
        elif numbers == list(range(numbers[0], numbers[-1] + 1)):
            parts.append(f"`{topic}-{numbers[0]:03d}`–`{topic}-{numbers[-1]:03d}`（{len(numbers)} 条）")
        else:
            parts.append("、".join(f"`{topic}-{n:03d}`" for n in numbers))
    return "，".join(parts)


# --------------------------------------------------------------------------- render


def render_adr_sections(spec_adrs: dict, adrs: dict, add) -> dict[str, list[str]]:
    """Render selected ADR sections and report which paths made it in."""
    included: dict[str, list[str]] = {}
    if not spec_adrs:
        return included
    add("## 架构决定（仅本次需要的章节）")
    add("")
    for adr_id in sorted(spec_adrs):
        meta = adrs.get(adr_id)
        if meta is None:
            print(f"warning: unknown ADR: {adr_id}", file=sys.stderr)
            continue
        adr_text = read_doc(meta["path"])
        add(f"### {adr_id}：{meta['title']}（`{meta.get('status', '?')}`）")
        add("")
        included[adr_id] = []
        for path in spec_adrs[adr_id]:
            body = extract_section(adr_text, path)
            if body is None:
                print(f"warning: ADR section not found in {meta['path']}: {path}", file=sys.stderr)
                continue
            included[adr_id].append(path)
            # Normalise depth: a selected `##` section and a selected `###`
            # subsection both land at `####` under the ADR heading.
            source_level = len(path.split("/")) + 1
            add(embed(body, meta["path"], 4 - source_level))
            add("")
    return included


def render_baseline(spec: dict, registry: tuple[dict, dict, dict]) -> tuple[str, dict]:
    """Cross-cutting engineering brief: true for every work package, rarely changes."""
    _, _, adrs = registry
    spec_adrs: dict[str, list[str]] = spec.get("adr_sections", {})
    title = spec.get("title", "工程基线")

    lines: list[str] = []
    add = lines.append
    add("<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->")
    add(f"<!-- python3 {SCRIPT_REL} --baseline -->")
    add(f"# Brief — {title}")
    add("")
    add("> **非权威派生制品。** 跨能力的工程约定，对每个实现工作包都成立；与源文件冲突时以 §溯源 为准。")
    add("> 变化很少：读一次后可以长期复用，不必随每个 UC 重新加载。")
    add("")

    add("## 本次范围")
    add("")
    add("| 项 | 值 |")
    add("| --- | --- |")
    add("| 类型 | 跨能力工程基线（不绑定单个 UC） |")
    add("| ADR | " + "、".join(f"`{a}`" for a in sorted(spec_adrs)) + " |")
    add("| 变化频率 | 低；仅在架构决定变化时重新生成 |")
    add("")
    add("## 遇到 brief 未覆盖的问题")
    add("")
    add("先查 §未纳入本 brief 的源小节；仍不确定，或发现两条权威规则冲突，产出结构化 gap 并路由给设计任务，不要自行发明。")
    add("")

    adr_included = render_adr_sections(spec_adrs, adrs, add)

    add("## 未纳入本 brief 的源小节")
    add("")
    add("需要时按源文件锚点查阅；不要为了“看全”而整文件加载。")
    add("")
    for adr_id in sorted(spec_adrs):
        meta = adrs.get(adr_id)
        if meta is None:
            continue
        omitted = collapse_omitted(
            [p for p in section_paths(read_doc(meta["path"])) if p not in adr_included.get(adr_id, [])]
        )
        if omitted:
            add(f"- `{adr_id}`（{meta['path']}）：" + "、".join(omitted))
    add("")

    add("## 溯源")
    add("")
    add("| 文件 | 行数 | sha256 |")
    add("| --- | --- | --- |")
    source_paths = [adrs[a]["path"] for a in sorted(spec_adrs) if a in adrs]
    for path in source_paths:
        add(f"| `{path}` | {len(read_doc(path).splitlines())} | `{short_hash(DOCS / path)}` |")
    add("")

    brief = "\n".join(lines).rstrip() + "\n"
    stats = {
        "brief_lines": len(brief.splitlines()),
        "brief_bytes": len(brief.encode("utf-8")),
        "brief_tokens": estimate_tokens(brief),
        "baseline_lines": sum(len(read_doc(p).splitlines()) for p in source_paths),
        "baseline_bytes": sum(len(read_doc(p).encode("utf-8")) for p in source_paths),
        "baseline_tokens": sum(estimate_tokens(read_doc(p)) for p in source_paths),
        "source_paths": source_paths,
        "own_brs": [],
        "external_brs": [],
    }
    return brief, stats


def render(uc_id: str, spec: dict, registry: tuple[dict, dict, dict]) -> tuple[str, dict]:
    use_cases, business_rules, adrs = registry
    if uc_id not in use_cases:
        raise SystemExit(f"unknown use case: {uc_id}")

    uc = use_cases[uc_id]
    uc_path = uc["path"]
    uc_text = read_doc(uc_path)

    wanted_sections = spec.get("uc_sections")
    if wanted_sections is None:
        wanted_sections = [p for p in section_paths(uc_text) if "/" not in p and p not in DEFAULT_UC_EXCLUDES]

    own_brs = sort_brs(br for br, meta in business_rules.items() if meta["path"] == uc_path) \
        if spec.get("include_own_brs", True) else []
    external_brs = sort_brs(
        br for br in mentioned_brs(uc_text)
        if br in business_rules and business_rules[br]["path"] != uc_path
    ) if spec.get("include_external_brs", True) else []

    external_sources: dict[str, list[str]] = {}
    for br_id in external_brs:
        external_sources.setdefault(business_rules[br_id]["path"], []).append(br_id)
    owner_of = {meta["path"]: uid for uid, meta in use_cases.items()}

    spec_adrs: dict[str, list[str]] = spec.get("adr_sections", {})

    lines: list[str] = []
    add = lines.append

    add("<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->")
    add(f"<!-- python3 {SCRIPT_REL} {uc_id} --spec {SPECS_REL}/{uc_id}.json -->")
    add(f"# Brief — {uc_id}：{uc['title']}")
    add("")
    add("> **非权威派生制品。** 本文由脚本从 `docs/app-center/` 抽取，只用于给本次工作包提供输入。")
    add("> 与源文件冲突时，一律以 §溯源 中列出的源文件为准；不要手工编辑本文，也不要把它当作第二权威。")
    add("")

    add("## 本次范围")
    add("")
    add("| 项 | 值 |")
    add("| --- | --- |")
    add(f"| Use Case | `{uc_id}` {uc['title']} |")
    add(f"| 设计状态 | `{uc.get('status', '?')}`（以 registry 为准） |")
    add(f"| 本 UC 权威 BR | {compact_number_list(own_brs)} |")
    if external_brs:
        owners = "、".join(f"`{owner_of.get(p, p)}`" for p in sorted(external_sources))
        add(f"| 外部引用 BR | {compact_number_list(external_brs)}（来自 {owners}） |")
    else:
        add("| 外部引用 BR | — |")
    if spec_adrs:
        add("| ADR | " + "、".join(f"`{a}`" for a in sorted(spec_adrs)) + " |")
    else:
        add("| ADR | —（未在 spec 中声明） |")
    add("")

    add("## 遇到 brief 未覆盖的问题")
    add("")
    add("本 brief 刻意不覆盖全部设计。按以下顺序处理，**不要自行发明业务行为**：")
    add("")
    add("1. 先在 §未纳入本 brief 的源小节 找标题，命中则按锚点查阅对应源文件。")
    add("2. 仍无法确定，或发现两条权威规则冲突：**停止受影响的实现**，产出一条结构化 gap：")
    add("")
    add("   ```text")
    add("   blocked: true")
    add("   authority: <BR-*/UC-*/ADR-* 的权威位置>")
    add("   conflict: <一句话描述歧义或冲突>")
    add("   options: <可选方案>")
    add("   suggested: <建议方案>")
    add("   ```")
    add("")
    add("3. gap 由设计任务（读全量概述文档的那个角色）解决并更新权威正文后，重新生成本 brief，再继续实现。")
    add("")

    included_uc: list[str] = []
    add("## 用例正文")
    add("")
    for path in wanted_sections:
        if path.split("/")[0] == BR_SECTION_TITLE:
            continue  # rendered from the authority blocks below
        body = extract_section(uc_text, path)
        if body is None:
            print(f"warning: section not found in {uc_path}: {path}", file=sys.stderr)
            continue
        included_uc.append(path)
        add(embed(body, uc_path, 1))
        add("")

    if own_brs:
        add(f"## 业务规则（{uc_id} 权威正文）")
        add("")
        for br_id in own_brs:
            block = br_block(uc_text, br_id)
            if block is None:
                print(f"warning: BR block not found: {br_id}", file=sys.stderr)
                continue
            add(f"<!-- 权威位置: {uc_path}#{br_id.lower()} -->")
            add(embed(block, uc_path, 0))
            add("")

    external_included: dict[str, list[str]] = {}
    if external_brs:
        add("## 外部引用的业务规则")
        add("")
        add("> 这些规则的权威正文不在本 UC 中，只抽取本次实现需要的条款；规则只有一个定义来源。")
        add("")
        for path, ids in external_sources.items():
            source_text = read_doc(path)
            external_included[path] = []
            add(f"### 来自 `{owner_of.get(path, path)}`")
            add("")
            for br_id in sort_brs(ids):
                block = br_block(source_text, br_id)
                if block is None:
                    print(f"warning: external BR not found: {br_id} in {path}", file=sys.stderr)
                    continue
                external_included[path].append(br_id)
                add(f"<!-- 权威位置: {path}#{br_id.lower()} -->")
                add(embed(block, path, 0))
                add("")

    adr_included = render_adr_sections(spec_adrs, adrs, add)

    add("## 未纳入本 brief 的源小节")
    add("")
    add("需要时按源文件锚点查阅；不要为了“看全”而整文件加载。")
    add("")
    omitted_uc = collapse_omitted(
        [p for p in section_paths(uc_text) if p not in included_uc and p.split("/")[0] != BR_SECTION_TITLE]
    )
    if omitted_uc:
        add(f"- `{uc_id}`（{uc_path}）：" + "、".join(omitted_uc))
    for path, ids in external_sources.items():
        source_text = read_doc(path)
        omitted = collapse_omitted(
            [p for p in section_paths(source_text) if p.split("/")[0] != BR_SECTION_TITLE]
        )
        if omitted:
            add(f"- `{owner_of.get(path, path)}`（{path}）：" + "、".join(omitted))
    for adr_id in sorted(spec_adrs):
        meta = adrs.get(adr_id)
        if meta is None:
            continue
        omitted = collapse_omitted(
            [p for p in section_paths(read_doc(meta["path"])) if p not in adr_included.get(adr_id, [])]
        )
        if omitted:
            add(f"- `{adr_id}`（{meta['path']}）：" + "、".join(omitted))
    add("")

    add("## 溯源")
    add("")
    add("| 文件 | 行数 | sha256 |")
    add("| --- | --- | --- |")
    source_paths = [uc_path]
    for path in list(external_sources) + [adrs[a]["path"] for a in sorted(spec_adrs) if a in adrs]:
        if path not in source_paths:
            source_paths.append(path)
    for path in source_paths:
        add(f"| `{path}` | {len(read_doc(path).splitlines())} | `{short_hash(DOCS / path)}` |")
    add("")

    brief = "\n".join(lines).rstrip() + "\n"
    stats = {
        "brief_lines": len(brief.splitlines()),
        "brief_bytes": len(brief.encode("utf-8")),
        "brief_tokens": estimate_tokens(brief),
        "baseline_lines": sum(len(read_doc(p).splitlines()) for p in source_paths),
        "baseline_bytes": sum(len(read_doc(p).encode("utf-8")) for p in source_paths),
        "baseline_tokens": sum(estimate_tokens(read_doc(p)) for p in source_paths),
        "source_paths": source_paths,
        "own_brs": own_brs,
        "external_brs": external_brs,
    }
    return brief, stats


def default_output(target: str | None) -> Path:
    name = "_engineering-baseline.md" if target is None else f"{target}.md"
    return DOCS / "briefs" / name


def default_spec(target: str | None) -> Path:
    name = "_baseline.json" if target is None else f"{target}.json"
    return DEFAULT_SPEC_DIR / name


def build(target: str | None, spec: dict, registry: tuple[dict, dict, dict]) -> tuple[str, dict]:
    return render_baseline(spec, registry) if target is None else render(target, spec, registry)


def discover_targets() -> list[str | None]:
    """Baseline plus every curated per-UC spec, in a stable order."""
    specs = sorted(p.stem for p in DEFAULT_SPEC_DIR.glob("*.json") if not p.name.startswith("_"))
    return [None, *specs]


def report(label: str, stats: dict, max_lines: int) -> None:
    saved = 1 - stats["brief_tokens"] / max(stats["baseline_tokens"], 1)
    print("", file=sys.stderr)
    print(f"size report [{label}] — brief vs loading the source files in full", file=sys.stderr)
    print(f"  brief    : {stats['brief_lines']:>5} lines  {stats['brief_bytes']:>7} bytes  ~{stats['brief_tokens']:>6} tokens", file=sys.stderr)
    print(f"  baseline : {stats['baseline_lines']:>5} lines  {stats['baseline_bytes']:>7} bytes  ~{stats['baseline_tokens']:>6} tokens", file=sys.stderr)
    print(f"  reduction: {saved:+.0%} tokens across {len(stats['source_paths'])} source files", file=sys.stderr)
    if stats["brief_lines"] > max_lines:
        print(f"  WARNING  : brief exceeds {max_lines} lines — the work package is probably too large, or the spec is too greedy", file=sys.stderr)


def regenerate_command(target: str | None) -> str:
    return f"python3 {SCRIPT_REL} --baseline" if target is None \
        else f"python3 {SCRIPT_REL} {target}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("uc", nargs="?", help="use case id, e.g. UC-APP-003 (omit with --baseline or --all)")
    parser.add_argument("--baseline", action="store_true", help="target the cross-cutting engineering baseline brief")
    parser.add_argument("--all", action="store_true", help="operate on the baseline and every curated spec")
    parser.add_argument("--check", action="store_true",
                        help="verify the brief on disk matches its sources; non-zero exit when stale or missing")
    parser.add_argument("--spec", type=Path, help="brief spec JSON; defaults to docs/tools/brief-specs/<UC>.json if present")
    parser.add_argument("--no-spec", action="store_true", help="ignore any spec and use automatic section selection")
    parser.add_argument("--out", type=Path, help="output path; only valid for a single target")
    parser.add_argument("--stdout", action="store_true", help="write the brief to stdout instead of a file")
    parser.add_argument("--max-lines", type=int, default=300, help="warn when the brief exceeds this many lines")
    parser.add_argument("--quiet", action="store_true", help="suppress the success output")
    args = parser.parse_args()

    if args.all and (args.baseline or args.uc):
        raise SystemExit("--all cannot be combined with a use case id or --baseline")
    if args.out and (args.all or (args.baseline and args.uc)):
        raise SystemExit("--out is only valid for a single target")

    if args.all:
        targets = discover_targets()
    elif args.baseline:
        targets = [None]
    else:
        if not args.uc:
            raise SystemExit("a use case id is required unless --baseline or --all is given")
        targets = [args.uc]

    registry = load_registry()
    stale: list[tuple[Path, str, str | None]] = []

    for target in targets:
        if args.spec:
            spec_path: Path | None = args.spec
        elif args.no_spec:
            spec_path = None
        else:
            spec_path = default_spec(target)

        spec: dict = {}
        if spec_path is not None and spec_path.exists():
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
        elif args.spec:
            raise SystemExit(f"spec not found: {spec_path}")

        brief, stats = build(target, spec, registry)
        out_path = args.out or default_output(target)
        label = "baseline" if target is None else target

        if args.check:
            if not out_path.exists():
                stale.append((out_path, "missing", target))
            elif out_path.read_text(encoding="utf-8") != brief:
                stale.append((out_path, "stale", target))
            continue

        if args.stdout:
            sys.stdout.write(brief)
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(brief, encoding="utf-8")
            if not args.quiet:
                try:
                    shown = out_path.relative_to(WORKSPACE)
                except ValueError:
                    shown = out_path
                print(f"wrote {shown}", file=sys.stderr)

        if not args.quiet:
            report(label, stats, args.max_lines)

    if args.check:
        if stale:
            print("brief check FAILED:", file=sys.stderr)
            for path, reason, target in stale:
                try:
                    shown = path.relative_to(WORKSPACE)
                except ValueError:
                    shown = path
                print(f"  {reason:>7}: {shown}", file=sys.stderr)
                print(f"           regenerate: {regenerate_command(target)}", file=sys.stderr)
            print("", file=sys.stderr)
            print("the brief is the implementation agent's input; a stale brief silently feeds an outdated design.", file=sys.stderr)
            return 1
        if not args.quiet:
            print(f"brief check OK ({len(targets)} brief(s))", file=sys.stderr)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
