#!/usr/bin/env python3
"""Generate a task-scoped design brief from authoritative design documents.

A brief is a *derived, non-authoritative* artifact: it extracts exactly the
design text one work package needs, so an implementation agent reads one small
file instead of whole use-case and ADR files. Conflicts always resolve to the
sources listed under "溯源" in the generated brief.

Usage (run from the docs repository root):
    python3 tools/gen_brief.py UC-APP-003
    python3 tools/gen_brief.py UC-AUTH-005
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
from pathlib import Path, PurePosixPath

WORKSPACE = Path(__file__).resolve().parents[2]
DOCS = WORKSPACE / "docs" / "app-center"
DOCS_REPO = DOCS.parent
REGISTRY = DOCS / "design-registry.md"
DEFAULT_SPEC_DIR = WORKSPACE / "docs" / "tools" / "brief-specs"

# Canonical paths as seen from the docs repository root. They are fixed rather
# than derived from the current directory so that generated briefs are
# byte-identical no matter where the generator is invoked.
SCRIPT_REL = "tools/gen_brief.py"
SPECS_REL = "tools/brief-specs"

# Registry paths are relative to the active bounded context; shared platform
# sources selected by a spec are relative to the docs repository root. Keeping
# both conventions lets app-center briefs stay byte-identical while still
# linking out to `platform/…`.
CONTEXT_PREFIX = "app-center"
OUTPUT_REL = "app-center/briefs"


def select_context(target: str | None) -> None:
    """Select one context per CLI target; --baseline remains App Center only."""
    global DOCS, REGISTRY, CONTEXT_PREFIX, OUTPUT_REL
    if target is None or re.fullmatch(r"UC-APP-\d+", target):
        context = "app-center"
    elif re.fullmatch(r"UC-AUTH-\d+", target):
        context = "auth-center"
    else:
        raise SystemExit(f"unsupported use case id: {target}")
    CONTEXT_PREFIX = context
    DOCS = DOCS_REPO / context
    REGISTRY = DOCS / "design-registry.md"
    OUTPUT_REL = f"{context}/briefs"


class BriefInputError(Exception):
    """Raised when a brief cannot be assembled faithfully from its sources.

    A brief that silently omits a selected section would hand the implementation
    agent an incomplete design while every gate still reports OK: the check gate
    compares bytes, so it validates consistency, not completeness. Missing or
    unresolvable design input is therefore a hard failure, not a warning.
    """

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))

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

        if rid.startswith(("UC-APP-", "UC-AUTH-")):
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


def context_rel(rel_path: str) -> str:
    """Docs-root-relative form of an active-context registry path."""
    return f"{CONTEXT_PREFIX}/{rel_path}"


def resolve_shared_source(rel_path: str, *, query: bool = False) -> tuple[Path | None, str | None]:
    """Resolve a docs-root-relative shared source, failing closed.

    Returns `(resolved_path, None)` when the path is a canonical, docs-root-
    relative `platform/…` path (or the active context's `query-contracts/`
    when query=True) to a regular Markdown file, or `(None, problem)`
    otherwise. Absolute paths and any `..` segment are rejected outright;
    symlinks are resolved and must still land inside the docs repository, so a
    link cannot smuggle in a file from outside the tree.
    """
    if not isinstance(rel_path, str) or not rel_path:
        return None, f"shared source path must be a non-empty string: {rel_path!r}"
    if rel_path != rel_path.strip():
        return None, f"shared source path has surrounding whitespace: {rel_path!r}"
    if "\x00" in rel_path:
        return None, f"shared source path contains a NUL byte: {rel_path!r}"
    if "\\" in rel_path:
        return None, f"shared source path must use POSIX separators: {rel_path!r}"

    pure = PurePosixPath(rel_path)
    if pure.is_absolute():
        return None, f"shared source path must be relative to the docs repository root: {rel_path!r}"
    if any(part == ".." for part in pure.parts):
        return None, f"shared source path may not contain `..`: {rel_path!r}"
    canonical = pure.as_posix()
    if rel_path != canonical:
        return None, f"shared source path must be canonical POSIX form `{canonical}`: {rel_path!r}"
    allowed = (CONTEXT_PREFIX, "query-contracts") if query else ("platform",)
    if pure.parts[:len(allowed)] != allowed:
        return None, f"shared source must be under `{'/'.join(allowed)}/`: {rel_path!r}"

    try:
        root = DOCS_REPO.resolve()
        candidate = (DOCS_REPO / pure).resolve()
    except (OSError, RuntimeError) as error:
        return None, f"cannot resolve shared source path {rel_path!r}: {error}"
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"shared source path escapes the docs repository root: {rel_path!r}"

    if query:
        try:
            candidate.relative_to(root.joinpath(*allowed))
        except ValueError:
            return None, f"query source escapes its context's query-contracts directory: {rel_path!r}"

    if not candidate.exists():
        return None, f"shared source file not found: {rel_path!r}"
    if not candidate.is_file():
        return None, f"shared source is not a regular file: {rel_path!r}"
    if candidate.suffix.lower() != ".md":
        return None, f"shared source is not a Markdown file: {rel_path!r}"
    return candidate, None


def shared_display(rel_path: str) -> str:
    """Canonical docs-root-relative display form used in generated briefs."""
    return PurePosixPath(rel_path).as_posix()


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
    """Make relative links resolve from `briefs/` instead of the source directory.

    `src_rel` is relative to the docs repository root, e.g.
    `app-center/adr/ADR-001-…md` or `platform/…md`. A link is resolved against
    the source file's directory and then re-expressed relative to the brief
    output directory, so both App Center sources and root-level platform
    sources land on the correct target.
    """
    src_dir = PurePosixPath(src_rel).parent
    out_dir = PurePosixPath(OUTPUT_REL)

    def replace(match: re.Match) -> str:
        target = match.group(1)
        if target.startswith("#") and CONTEXT_PREFIX == "auth-center":
            # A curated brief can omit the destination section, and BR anchors
            # are stripped when embedding. Resolve to the authoritative source.
            return f"]({posixpath.relpath(src_rel, str(out_dir))}{target})"
        if target.startswith(("#", "/", "http://", "https://", "mailto:")):
            return match.group(0)
        path, separator, anchor = target.partition("#")
        if not path:
            return match.group(0)
        resolved = posixpath.normpath(posixpath.join(str(src_dir), path))
        if resolved == ".." or resolved.startswith("../"):
            return match.group(0)  # points outside the docs tree; leave it alone
        return f"]({posixpath.relpath(resolved, str(out_dir))}{separator}{anchor})"

    return re.sub(r"\]\(([^)]+)\)", replace, text)


def embed(text: str, src_rel: str, levels: int) -> str:
    return demote(rewrite_links(text, src_rel), levels)


def collapse_omitted(paths: list[str]) -> list[str]:
    """Drop `parent/child` entries when `parent` is already listed."""
    present = set(paths)
    return [p for p in paths if "/" not in p or p.split("/")[0] not in present]


def first_heading_title(text: str) -> str | None:
    """Title of the first level-1 heading, used to label a shared source."""
    for _, level, title in heading_marks(text)[1]:
        if level == 1:
            return title
    return None


def collect_shared_sources(spec_shared: object, problems: list[str], *, query: bool = False) -> list[dict]:
    """Resolve, validate, and read every spec-selected docs-root shared source.

    Rendering order is stable: file keys are sorted by their canonical
    docs-root-relative path, and sections keep the order the spec declares.
    Every problem found is accumulated so one failed generation reports them
    all; a single unreadable source or missing section still fails the build.
    """
    field = "query_sections" if query else "shared_sections"
    if spec_shared is None:
        return []
    if not isinstance(spec_shared, dict):
        problems.append(f"`{field}` must be an object mapping a docs-root-relative path to a section list")
        return []
    if not spec_shared:
        return []

    records: list[dict] = []
    valid_items: list[tuple[str, object]] = []
    for raw_rel, sections in spec_shared.items():
        if not isinstance(raw_rel, str):
            problems.append(f"shared source path must be a non-empty string: {raw_rel!r}")
            continue
        valid_items.append((raw_rel, sections))

    for raw_rel, sections in sorted(valid_items, key=lambda item: shared_display(item[0])):
        display = shared_display(raw_rel)
        if not isinstance(sections, list) or not sections:
            problems.append(f"`{field}[{display!r}]` must be a non-empty list of section paths")
            continue
        resolved, problem = resolve_shared_source(raw_rel, query=query)
        if problem is not None:
            problems.append(problem)
            continue

        try:
            text = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            problems.append(f"cannot read shared source `{display}` as UTF-8 Markdown: {error}")
            continue
        included: list[str] = []
        for path in sections:
            if not isinstance(path, str) or not path or path != path.strip():
                problems.append(
                    f"`{field}[{display!r}]` contains an invalid section path: {path!r}"
                )
                continue
            if path in included:
                continue
            if extract_section(text, path) is None:
                problems.append(f"shared section not found: `{display}` → `{path}`")
                continue
            included.append(path)

        records.append({
            "rel": display,
            "path": resolved,
            "text": text,
            "included": included,
            "title": first_heading_title(text),
        })
    return records


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


def display_path(path: Path) -> str:
    """Show a path relative to the docs repository root, then the workspace."""
    resolved = path.resolve()
    for base in (DOCS_REPO.resolve(), WORKSPACE.resolve()):
        try:
            return str(resolved.relative_to(base))
        except ValueError:
            continue
    return str(path)


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


def render_adr_sections(spec_adrs: dict, adrs: dict, add, problems: list[str]) -> dict[str, list[str]]:
    """Render selected ADR sections and report which paths made it in."""
    included: dict[str, list[str]] = {}
    if not spec_adrs:
        return included
    add("## 架构决定（仅本次需要的章节）")
    add("")
    for adr_id in sorted(spec_adrs):
        meta = adrs.get(adr_id)
        if meta is None:
            problems.append(f"spec selects ADR `{adr_id}`, which is not registered in design-registry.md")
            continue
        adr_text = read_doc(meta["path"])
        add(f"### {adr_id}：{meta['title']}（`{meta.get('status', '?')}`）")
        add("")
        included[adr_id] = []
        for path in spec_adrs[adr_id]:
            body = extract_section(adr_text, path)
            if body is None:
                problems.append(f"ADR section not found: `{adr_id}` → `{path}` in {meta['path']}")
                continue
            included[adr_id].append(path)
            # Normalise depth: a selected `##` section and a selected `###`
            # subsection both land at `####` under the ADR heading.
            source_level = len(path.split("/")) + 1
            add(embed(body, context_rel(meta["path"]), 4 - source_level))
            add("")
    return included


def render_shared_sections(records: list[dict], add, problems: list[str], *, query: bool = False) -> dict[str, list[str]]:
    """Render spec-selected root-level shared sections and report what made it in.

    A shared source is *not* part of the engineering baseline: it only appears
    when a spec names it in `shared_sections`. Files render in the stable order
    produced by `collect_shared_sources`.
    """
    included: dict[str, list[str]] = {}
    if not records:
        return included
    add("## 配套查询契约（按 spec 显式抽取）" if query else "## 平台共享契约（按 spec 显式抽取）")
    add("")
    if query:
        add("> 这些是当前 bounded context 的查询契约；只有本 spec 显式选择的章节才被抽取。")
    else:
        add("> 这些是 `docs/` 根下的跨系统共享设计输入，**不进入工程基线**；只有本 spec 显式选择的章节才被抽取。")
    add("> 与源文件冲突时，仍以 §溯源 中列出的源文件为准。")
    add("")
    for record in records:
        rel = record["rel"]
        header = f"### `{rel}`"
        if record["title"]:
            header += f"：{record['title']}"
        add(header)
        add("")
        included[rel] = []
        for path in record["included"]:
            body = extract_section(record["text"], path)
            if body is None:  # defensive: collect_shared_sources already verified presence
                problems.append(f"shared section not found: `{rel}` → `{path}`")
                continue
            included[rel].append(path)
            # Same depth normalisation as ADRs: `##` and `###` both land at `####`.
            source_level = len(path.split("/")) + 1
            add(embed(body, rel, 4 - source_level))
            add("")
    return included


def source_metrics(sources: list[tuple[str, Path]]) -> tuple[list[tuple[str, Path, str]], int, int, int]:
    """Read each source once and return (rows, lines, bytes, tokens)."""
    rows: list[tuple[str, Path, str]] = []
    total_lines = total_bytes = total_tokens = 0
    for display, actual in sources:
        text = actual.read_text(encoding="utf-8")
        rows.append((display, actual, text))
        total_lines += len(text.splitlines())
        total_bytes += len(text.encode("utf-8"))
        total_tokens += estimate_tokens(text)
    return rows, total_lines, total_bytes, total_tokens


def add_unique_source(sources: list[tuple[str, Path]], seen: set[Path], display: str, actual: Path) -> None:
    resolved = actual.resolve()
    if resolved in seen:
        return
    seen.add(resolved)
    sources.append((display, actual))


def render_baseline(spec: dict, registry: tuple[dict, dict, dict], problems: list[str]) -> tuple[str, dict]:
    """Cross-cutting engineering brief: true for every work package, rarely changes."""
    _, _, adrs = registry
    spec_adrs: dict[str, list[str]] = spec.get("adr_sections", {})
    spec_shared: object = spec.get("shared_sections", {})
    shared_records = collect_shared_sources(spec_shared, problems)
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
    if shared_records:
        add("| 平台共享 | " + "、".join(f"`{record['rel']}`" for record in shared_records) + " |")
    add("| 变化频率 | 低；仅在架构决定变化时重新生成 |")
    add("")
    add("## 遇到 brief 未覆盖的问题")
    add("")
    add("先查 §未纳入本 brief 的源小节；仍不确定，或发现两条权威规则冲突，产出结构化 gap 并路由给设计任务，不要自行发明。")
    add("")

    adr_included = render_adr_sections(spec_adrs, adrs, add, problems)
    shared_included = render_shared_sections(shared_records, add, problems)

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
    for record in shared_records:
        omitted = collapse_omitted(
            [p for p in section_paths(record["text"]) if p not in shared_included.get(record["rel"], [])]
        )
        if omitted:
            add(f"- `{record['rel']}`（docs 根级共享文档）：" + "、".join(omitted))
    add("")

    add("## 溯源")
    add("")
    add("| 文件 | 行数 | sha256 |")
    add("| --- | --- | --- |")
    sources: list[tuple[str, Path]] = []
    seen_sources: set[Path] = set()
    for adr_id in sorted(spec_adrs):
        if adr_id in adrs:
            path = adrs[adr_id]["path"]
            add_unique_source(sources, seen_sources, path, DOCS / path)
    for record in shared_records:
        add_unique_source(sources, seen_sources, record["rel"], record["path"])
    rows, total_lines, total_bytes, total_tokens = source_metrics(sources)
    for display, actual, text in rows:
        add(f"| `{display}` | {len(text.splitlines())} | `{short_hash(actual)}` |")
    add("")

    brief = "\n".join(lines).rstrip() + "\n"
    stats = {
        "brief_lines": len(brief.splitlines()),
        "brief_bytes": len(brief.encode("utf-8")),
        "brief_tokens": estimate_tokens(brief),
        "baseline_lines": total_lines,
        "baseline_bytes": total_bytes,
        "baseline_tokens": total_tokens,
        "source_paths": [display for display, _ in sources],
        "own_brs": [],
        "external_brs": [],
    }
    return brief, stats


def render(uc_id: str, spec: dict, registry: tuple[dict, dict, dict], problems: list[str]) -> tuple[str, dict]:
    use_cases, business_rules, adrs = registry
    if uc_id not in use_cases:
        raise SystemExit(f"unknown use case: {uc_id}")

    uc = use_cases[uc_id]
    uc_path = uc["path"]
    uc_text = read_doc(uc_path)

    wanted_sections = spec.get("uc_sections")
    if wanted_sections is None:
        wanted_sections = [p for p in section_paths(uc_text) if "/" not in p and p not in DEFAULT_UC_EXCLUDES]

    mentioned = mentioned_brs(uc_text)
    for br_id in mentioned:
        if br_id not in business_rules:
            problems.append(
                f"{uc_id} references `{br_id}`, which is not registered in design-registry.md "
                "(typo, or an ID that was never registered)"
            )

    own_brs = sort_brs(br for br, meta in business_rules.items() if meta["path"] == uc_path) \
        if spec.get("include_own_brs", True) else []
    external_brs = sort_brs(
        br for br in mentioned
        if br in business_rules and business_rules[br]["path"] != uc_path
    ) if spec.get("include_external_brs", True) else []

    external_sources: dict[str, list[str]] = {}
    for br_id in external_brs:
        external_sources.setdefault(business_rules[br_id]["path"], []).append(br_id)
    owner_of = {meta["path"]: uid for uid, meta in use_cases.items()}

    spec_adrs: dict[str, list[str]] = spec.get("adr_sections", {})
    spec_shared: object = spec.get("shared_sections", {})
    shared_records = collect_shared_sources(spec_shared, problems)
    query_records = collect_shared_sources(spec.get("query_sections"), problems, query=True)

    lines: list[str] = []
    add = lines.append

    add("<!-- GENERATED FILE — DO NOT EDIT. Regenerate with: -->")
    add(f"<!-- python3 {SCRIPT_REL} {uc_id} --spec {SPECS_REL}/{uc_id}.json -->")
    add(f"# Brief — {uc_id}：{uc['title']}")
    add("")
    if shared_records:
        add(f"> **非权威派生制品。** 本文由脚本从 `docs/{CONTEXT_PREFIX}/` 与 spec 显式选择的 `docs/` 共享文档抽取，只用于给本次工作包提供输入。")
    else:
        # Keep legacy briefs byte-identical when no shared source is selected.
        add(f"> **非权威派生制品。** 本文由脚本从 `docs/{CONTEXT_PREFIX}/` 抽取，只用于给本次工作包提供输入。")
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
    if shared_records:
        add("| 平台共享 | " + "、".join(f"`{record['rel']}`" for record in shared_records) + " |")
    if query_records:
        add("| 配套查询 | " + "、".join(f"`{record['rel']}`" for record in query_records) + " |")
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
            problems.append(f"UC section not found: `{uc_id}` → `{path}` in {uc_path}")
            continue
        included_uc.append(path)
        add(embed(body, context_rel(uc_path), 1))
        add("")

    if own_brs:
        add(f"## 业务规则（{uc_id} 权威正文）")
        add("")
        for br_id in own_brs:
            block = br_block(uc_text, br_id)
            if block is None:
                problems.append(
                    f"BR block not found: `{br_id}` is registered to {uc_path} but has no `### {br_id}` heading there"
                )
                continue
            add(f"<!-- 权威位置: {uc_path}#{br_id.lower()} -->")
            add(embed(block, context_rel(uc_path), 0))
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
                    problems.append(f"external BR block not found: `{br_id}` in {path}")
                    continue
                external_included[path].append(br_id)
                add(f"<!-- 权威位置: {path}#{br_id.lower()} -->")
                add(embed(block, context_rel(path), 0))
                add("")

    adr_included = render_adr_sections(spec_adrs, adrs, add, problems)
    shared_included = render_shared_sections(shared_records, add, problems)
    query_included = render_shared_sections(query_records, add, problems, query=True)

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
    for record in shared_records:
        omitted = collapse_omitted(
            [p for p in section_paths(record["text"]) if p not in shared_included.get(record["rel"], [])]
        )
        if omitted:
            add(f"- `{record['rel']}`（docs 根级共享文档）：" + "、".join(omitted))
    for record in query_records:
        omitted = collapse_omitted(
            [p for p in section_paths(record["text"]) if p not in query_included.get(record["rel"], [])]
        )
        if omitted:
            add(f"- `{record['rel']}`（配套查询契约）：" + "、".join(omitted))
    add("")

    add("## 溯源")
    add("")
    add("| 文件 | 行数 | sha256 |")
    add("| --- | --- | --- |")
    sources: list[tuple[str, Path]] = []
    seen_sources: set[Path] = set()
    add_unique_source(sources, seen_sources, uc_path, DOCS / uc_path)
    for path in list(external_sources) + [adrs[a]["path"] for a in sorted(spec_adrs) if a in adrs]:
        add_unique_source(sources, seen_sources, path, DOCS / path)
    for record in shared_records + query_records:
        add_unique_source(sources, seen_sources, record["rel"], record["path"])
    rows, total_lines, total_bytes, total_tokens = source_metrics(sources)
    for display, actual, text in rows:
        add(f"| `{display}` | {len(text.splitlines())} | `{short_hash(actual)}` |")
    add("")

    brief = "\n".join(lines).rstrip() + "\n"
    stats = {
        "brief_lines": len(brief.splitlines()),
        "brief_bytes": len(brief.encode("utf-8")),
        "brief_tokens": estimate_tokens(brief),
        "baseline_lines": total_lines,
        "baseline_bytes": total_bytes,
        "baseline_tokens": total_tokens,
        "source_paths": [display for display, _ in sources],
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


def build(target: str | None, spec: dict, registry: tuple[dict, dict, dict],
          spec_path: Path | None = None) -> tuple[str, dict]:
    """Assemble a brief, failing closed when any selected design input is missing."""
    problems: list[str] = []

    if target is None and "query_sections" in spec:
        problems.append("`query_sections` belongs to per-UC briefs, not the engineering baseline")

    declared = spec.get("uc")
    if target is not None and declared is not None and declared != target:
        where = display_path(spec_path) if spec_path is not None else f"{display_path(default_spec(target))} (default)"
        problems.append(f"spec declares `uc: {declared}` but is being applied to `{target}` ({where})")

    brief, stats = render_baseline(spec, registry, problems) if target is None \
        else render(target, spec, registry, problems)
    if problems:
        raise BriefInputError(problems)
    return brief, stats


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
    parser.add_argument("uc", nargs="?", help="use case id, e.g. UC-APP-003 or UC-AUTH-005 (omit with --baseline or --all)")
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

    stale: list[tuple[Path, str, str | None]] = []
    broken: list[tuple[str, list[str]]] = []

    for target in targets:
        select_context(target)
        registry = load_registry()
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

        out_path = args.out or default_output(target)
        label = "baseline" if target is None else target

        try:
            brief, stats = build(target, spec, registry, spec_path)
        except BriefInputError as error:
            # Never emit a partial brief: a brief that silently omits a rule is
            # worse than no brief, because every downstream gate still passes.
            broken.append((label, error.problems))
            continue

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
                print(f"wrote {display_path(out_path)}", file=sys.stderr)

        if not args.quiet:
            report(label, stats, args.max_lines)

    exit_code = 0

    if broken:
        print("brief generation FAILED — refusing to emit an incomplete design input:", file=sys.stderr)
        for label, problems in broken:
            print(f"  [{label}]", file=sys.stderr)
            for problem in problems:
                print(f"    - {problem}", file=sys.stderr)
        print("", file=sys.stderr)
        print("fix the authoritative document or the brief spec; do not weaken the check.", file=sys.stderr)
        exit_code = 1

    if args.check and stale:
        print("brief check FAILED:", file=sys.stderr)
        for path, reason, target in stale:
            print(f"  {reason:>7}: {display_path(path)}", file=sys.stderr)
            print(f"           regenerate: {regenerate_command(target)}", file=sys.stderr)
        print("", file=sys.stderr)
        print("the brief is the implementation agent's input; a stale brief silently feeds an outdated design.", file=sys.stderr)
        exit_code = 1

    if exit_code == 0 and args.check and not args.quiet:
        print(f"brief check OK ({len(targets)} brief(s))", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
