#!/usr/bin/env python3
"""Keep `design-registry.md` mechanically consistent with the authoritative documents.

The registry stays hand-maintained for everything humans own (BR type, notes,
superseded-by). Only the derivable parts are generated or verified:

* `--write`  regenerate the "下一个可分配编号" table from the register itself.
* `--check`  verify every mechanical column (id / title / status / authoritative
             location) still matches its source document, and that the id space
             is closed in both directions.

Why the Next ID table is generated rather than typed: it is the mechanism that
stops a retired number from being reissued, so it must be computed from the
register plus the explicit retired list, never from memory.

Retired (never-to-be-reissued) ids are declared in the registry itself:

    <!-- retired: UC-APP-017 BR-PRF-033 ... -->

Usage (run from the docs repository root):
    python3 tools/registry.py --check
    python3 tools/registry.py --write
"""

from __future__ import annotations

import argparse
import re
import sys
from itertools import zip_longest
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
DOCS_REPO = WORKSPACE / "docs"
APP_CENTER = DOCS_REPO / "app-center"
REGISTRY = APP_CENTER / "design-registry.md"

NEXT_ID_SECTION = "下一个可分配编号"
BR_SECTION = "Business Rules"

ANY_ID = re.compile(r"^(?:UC-[A-Z]+-\d+|BR-[A-Z]+-\d+|ADR-\d+)$")
ID_CELL = re.compile(r"^`([^`]+)`$")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SECTION = re.compile(r"^## (.+?)\s*$")
BR_TOPIC = re.compile(r"^### (.+?) \(`(BR-[A-Z]+)`\)\s*$")
BR_HEADING = re.compile(r"^### (BR-[A-Z]+-\d+)\s*[：:]\s*(.+?)\s*$")
DOC_HEADING = re.compile(r"^# ((?:UC-[A-Z]+-\d+)|(?:ADR-\d+))\s*[：:]\s*(.+?)\s*$")
STATUS_LINE = re.compile(r"^状态：\s*`([A-Z_]+)`")
RETIRED = re.compile(r"<!--\s*retired:\s*(.*?)\s*-->")
NEXT_ID_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*`([^`]+)`\s*\|\s*$")

UC_NAMESPACE = "UC-APP"
ADR_NAMESPACE = "ADR"
UC_LABEL = "Use Case / App Center"
ADR_LABEL = "Architecture Decision"


def namespace_of(rid: str) -> str:
    return ADR_NAMESPACE if rid.startswith("ADR-") else rid.rsplit("-", 1)[0]


def number_of(rid: str) -> int:
    return int(rid.rsplit("-", 1)[1])


def format_id(namespace: str, number: int) -> str:
    width = max(3, len(str(number)))
    return f"ADR-{number:0{width}d}" if namespace == ADR_NAMESPACE else f"{namespace}-{number:0{width}d}"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_source(relative: str) -> str:
    return (APP_CENTER / relative).read_text(encoding="utf-8")


class Registry:
    def __init__(self, path: Path):
        self.path = path
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()
        self.sections = self._sections()
        self.rows = self._rows()
        self.retired = self._retired()

    def _sections(self) -> list[tuple[str, int, int]]:
        marks = [(index, match.group(1).strip())
                 for index, line in enumerate(self.lines)
                 if (match := SECTION.match(line))]
        return [(title, start, marks[i + 1][0] if i + 1 < len(marks) else len(self.lines))
                for i, (start, title) in enumerate(marks)]

    def section_lines(self, title: str) -> tuple[int, int]:
        for name, start, end in self.sections:
            if name == title:
                return start, end
        raise SystemExit(f"registry section not found: {title}")

    def _rows(self) -> list[dict]:
        rows = []
        for index, line in enumerate(self.lines):
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                continue
            match = ID_CELL.match(cells[0])
            if not match or not ANY_ID.match(match.group(1)):
                continue  # skips the Next ID table, whose first cell is a label
            link = MD_LINK.search(line)
            rows.append({
                "line": index,
                "id": match.group(1),
                "title": cells[1],
                "meta": cells[2],
                "target": link.group(1) if link else "",
            })
        return rows

    def _retired(self) -> list[str]:
        found: list[str] = []
        for line in self.lines:
            match = RETIRED.search(line)
            if match:
                found.extend(token for token in match.group(1).split() if ANY_ID.match(token))
        return found

    def br_topics(self) -> list[tuple[str, str]]:
        start, end = self.section_lines(BR_SECTION)
        topics = []
        for line in self.lines[start:end]:
            match = BR_TOPIC.match(line)
            if match:
                topics.append((match.group(1), match.group(2)))
        return topics

    def next_id_table(self) -> list[tuple[str, str]]:
        present: dict[str, int] = {}
        for rid in [row["id"] for row in self.rows] + self.retired:
            namespace = namespace_of(rid)
            present[namespace] = max(present.get(namespace, 0), number_of(rid))

        ordered = [(UC_LABEL, UC_NAMESPACE)]
        ordered += [(f"Business Rule / {name}", namespace) for name, namespace in self.br_topics()]
        ordered += [(ADR_LABEL, ADR_NAMESPACE)]
        return [(label, format_id(namespace, present.get(namespace, 0) + 1))
                for label, namespace in ordered]

    def current_next_id_lines(self) -> tuple[int, int]:
        start, end = self.section_lines(NEXT_ID_SECTION)
        table = [index for index in range(start, end) if self.lines[index].startswith("|")]
        if not table:
            raise SystemExit(f"no table found in registry section: {NEXT_ID_SECTION}")
        return table[0], table[-1] + 1

    def rendered_next_id_table(self) -> list[str]:
        lines = ["| 编号空间 | Next ID |", "| --- | --- |"]
        lines += [f"| {label} | `{next_id}` |" for label, next_id in self.next_id_table()]
        return lines


# --------------------------------------------------------------------- authoring


def scan_document(text: str) -> dict:
    """Read the authoritative id/title/status and BR headings out of one document."""
    facts: dict = {"id": None, "title": None, "status": None, "brs": [], "br_titles": {}}
    for line in text.splitlines():
        if facts["id"] is None and (match := DOC_HEADING.match(line)):
            facts["id"], facts["title"] = match.group(1), match.group(2)
            continue
        if facts["status"] is None and (match := STATUS_LINE.match(line)):
            facts["status"] = match.group(1)
            continue
        if match := BR_HEADING.match(line):
            facts["brs"].append(match.group(1))
            facts["br_titles"][match.group(1)] = match.group(2)
    return facts


def collect_facts() -> dict[str, dict]:
    documents: dict[str, dict] = {}
    for path in sorted((APP_CENTER / "use-cases").glob("UC-*.md")):
        documents[f"use-cases/{path.name}"] = scan_document(path.read_text(encoding="utf-8"))
    for path in sorted((APP_CENTER / "adr").glob("ADR-*.md")):
        documents[f"adr/{path.name}"] = scan_document(path.read_text(encoding="utf-8"))
    return documents


# ------------------------------------------------------------------------ checks


def next_id_row(line: str) -> tuple[str, str]:
    """Split a `| label | `ID` |` row; unparseable lines fall back to themselves."""
    match = NEXT_ID_ROW.match(line)
    if match:
        return match.group(1), match.group(2)
    fallback = line or "(missing row)"
    return fallback, fallback


def check(registry: Registry) -> list[str]:
    problems: list[str] = []
    documents = collect_facts()
    seen: dict[str, int] = {}

    for row in registry.rows:
        rid = row["id"]
        if rid in seen:
            problems.append(f"duplicate registry row for `{rid}` (lines {seen[rid]} and {row['line'] + 1})")
        seen[rid] = row["line"] + 1

        if not row["target"]:
            problems.append(f"`{rid}`: no authoritative location link")
            continue
        path, _, anchor = row["target"].partition("#")
        if path not in documents:
            problems.append(f"`{rid}`: authoritative location does not resolve: {path}")
            continue

        facts = documents[path]
        if rid.startswith("BR-"):
            if rid not in facts["br_titles"]:
                problems.append(f"`{rid}`: no `### {rid}` heading in {path}")
            elif normalize(facts["br_titles"][rid]) != normalize(row["title"]):
                problems.append(
                    f"`{rid}`: title drift — registry `{row['title']}` vs {path} `{facts['br_titles'][rid]}`"
                )
            if anchor and f'<a id="{anchor}"></a>' not in read_source(path):
                problems.append(f"`{rid}`: anchor target missing in {path}: #{anchor}")
            continue

        if facts["id"] != rid:
            problems.append(f"`{rid}`: {path} declares `{facts['id']}`")
            continue
        if normalize(facts["title"]) != normalize(row["title"]):
            problems.append(f"`{rid}`: title drift — registry `{row['title']}` vs {path} `{facts['title']}`")
        status = row["meta"].strip("`")
        if facts["status"] != status:
            problems.append(f"`{rid}`: status drift — registry `{status}` vs {path} `{facts['status']}`")

    # Reverse direction: nothing in the sources may be missing from the register.
    for path, facts in documents.items():
        if facts["id"] and facts["id"] not in seen:
            problems.append(f"{path} declares `{facts['id']}`, which has no registry row")
        for br_id in facts["brs"]:
            if br_id not in seen:
                problems.append(f"{path} defines `{br_id}`, which has no registry row")

    # Every namespace needs a business-topic heading, and vice versa.
    topics = {namespace for _, namespace in registry.br_topics()}
    for namespace in {namespace_of(row["id"]) for row in registry.rows if row["id"].startswith("BR-")}:
        if namespace not in topics:
            problems.append(f"business topic `{namespace}` has rows but no `### … (`{namespace}`)` heading")
    for namespace in topics:
        if not any(row["id"].startswith(f"{namespace}-") for row in registry.rows):
            problems.append(f"business topic heading `{namespace}` has no rows")

    # The derived table must match what is written down.
    start, end = registry.current_next_id_lines()
    actual = registry.lines[start:end]
    expected = registry.rendered_next_id_table()
    if actual != expected:
        details = []
        for current, computed in zip_longest(actual, expected, fillvalue=""):
            if current == computed:
                continue
            label, current_id = next_id_row(current)
            _, computed_id = next_id_row(computed)
            details.append(f"      {label}: registry `{current_id}` -> computed `{computed_id}`")
        problems.append(
            "Next ID table is out of date:\n" + "\n".join(details)
            + "\n      fix: python3 tools/registry.py --write"
        )

    return problems


# ------------------------------------------------------------------------- write


def write(registry: Registry) -> bool:
    """Rewrite only the Next ID table; every other column stays human-owned."""
    start, end = registry.current_next_id_lines()
    rendered = registry.rendered_next_id_table()
    if registry.lines[start:end] == rendered:
        return False
    lines = registry.lines[:start] + rendered + registry.lines[end:]
    registry.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify the registry against its sources; non-zero on drift")
    parser.add_argument("--write", action="store_true", help="regenerate the Next ID table in place")
    parser.add_argument("--quiet", action="store_true", help="suppress success output")
    args = parser.parse_args()

    if args.check == args.write:
        raise SystemExit("pass exactly one of --check or --write")

    if not REGISTRY.exists():
        raise SystemExit(f"registry not found: {REGISTRY}")

    registry = Registry(REGISTRY)

    if args.write:
        changed = write(registry)
        if not args.quiet:
            print("registry Next ID table updated" if changed else "registry Next ID table already current",
                  file=sys.stderr)
        return 0

    problems = check(registry)
    if problems:
        print("registry check FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("", file=sys.stderr)
        print("the registry is an index, not a second authority: fix the row or the source, never both by hand.",
              file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"registry check OK ({len(registry.rows)} rows, {len(registry.retired)} retired ids)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
