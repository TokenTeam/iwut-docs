#!/usr/bin/env python3
"""Auth-context routing and query-contract provenance/fail-closed coverage."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import gen_brief  # noqa: E402


class AuthBriefTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        saved = {name: getattr(gen_brief, name) for name in (
            "DOCS_REPO", "DOCS", "REGISTRY", "CONTEXT_PREFIX", "OUTPUT_REL",
        )}
        self.addCleanup(lambda: [setattr(gen_brief, k, v) for k, v in saved.items()])
        gen_brief.DOCS_REPO = self.root
        for context, prefix in [("auth-center", "AUTH"), ("app-center", "APP")]:
            folder = self.root / context
            (folder / "use-cases").mkdir(parents=True)
            (folder / "query-contracts").mkdir()
            uc = f"UC-{prefix}-001"
            (folder / "use-cases" / f"{uc}.md").write_text(
                f"# {uc}：示例\n\n状态：`ACCEPTED`\n\n## 输入\n\n"
                f"{context} [查询](../query-contracts/profile.md#读取) [本节](#输入)\n",
                encoding="utf-8",
            )
            (folder / "design-registry.md").write_text(
                f"| `{uc}` | 示例 | `ACCEPTED` | [{uc}](use-cases/{uc}.md) |\n",
                encoding="utf-8",
            )
            (folder / "query-contracts/profile.md").write_text(
                "# 查询\n\n## 读取\n\n完整快照。\n\n## 未选\n\n暂不抽取。\n",
                encoding="utf-8",
            )
        gen_brief.select_context("UC-AUTH-001")

    def build(self, query=None):
        spec = {
            "uc": "UC-AUTH-001", "uc_sections": ["输入"],
            "query_sections": query if query is not None else {
                "auth-center/query-contracts/profile.md": ["读取"],
            },
        }
        return gen_brief.build("UC-AUTH-001", spec, gen_brief.load_registry())

    def test_context_routing_and_switch_back(self) -> None:
        auth, _ = self.build()
        self.assertIn("docs/auth-center/", auth)
        self.assertNotIn("docs/app-center/", auth)
        self.assertEqual(gen_brief.default_output("UC-AUTH-001"),
                         self.root / "auth-center/briefs/UC-AUTH-001.md")
        self.assertIn("](../use-cases/UC-AUTH-001.md#输入)", auth)
        self.assertIn("](../query-contracts/profile.md#读取)", auth)
        gen_brief.select_context("UC-APP-001")
        app, _ = gen_brief.build("UC-APP-001", {}, gen_brief.load_registry())
        self.assertIn("docs/app-center/", app)
        self.assertNotIn("UC-AUTH-001", app)
        self.assertEqual(gen_brief.default_output("UC-APP-001"),
                         self.root / "app-center/briefs/UC-APP-001.md")
        gen_brief.select_context(None)
        self.assertEqual(gen_brief.default_output(None),
                         self.root / "app-center/briefs/_engineering-baseline.md")

    def test_query_selection_provenance_and_drift(self) -> None:
        first, stats = self.build()
        self.assertIn("完整快照。", first)
        self.assertNotIn("暂不抽取。", first)
        self.assertIn("配套查询契约）：未选", first)
        self.assertIn("auth-center/query-contracts/profile.md", stats["source_paths"])
        source = self.root / "auth-center/query-contracts/profile.md"
        source.write_text(source.read_text() + "\n新的未选章节内容。\n", encoding="utf-8")
        second, _ = self.build()
        self.assertNotEqual(first, second, "Even unselected source edits must change provenance")
        self.assertEqual(second, self.build()[0], "Generation must be deterministic")

    def test_missing_or_foreign_query_sources_fail_closed(self) -> None:
        for path, section in [
            ("auth-center/query-contracts/profile.md", "不存在"),
            ("auth-center/query-contracts/missing.md", "读取"),
            ("app-center/query-contracts/profile.md", "读取"),
            ("auth-center/use-cases/UC-AUTH-001.md", "输入"),
            ("auth-center/query-contracts/../../app-center/query-contracts/profile.md", "读取"),
            ("/etc/passwd", "读取"),
        ]:
            with self.subTest(path=path, section=section):
                with self.assertRaises(gen_brief.BriefInputError):
                    self.build({path: [section]})

    def test_query_symlink_cannot_escape_context(self) -> None:
        link = self.root / "auth-center/query-contracts/leak.md"
        link.symlink_to(self.root / "app-center/query-contracts/profile.md")
        with self.assertRaises(gen_brief.BriefInputError):
            self.build({"auth-center/query-contracts/leak.md": ["读取"]})

    def test_query_spec_shape_and_baseline_are_checked(self) -> None:
        for query in [[], {"auth-center/query-contracts/profile.md": []},
                      {"auth-center/query-contracts/profile.md": [7]}]:
            with self.subTest(query=query), self.assertRaises(gen_brief.BriefInputError):
                self.build(query)
        with self.assertRaises(gen_brief.BriefInputError):
            gen_brief.build(None, {"query_sections": {}}, ({}, {}, {}))


class AuthCliTests(unittest.TestCase):
    def test_real_auth_brief_and_failing_query_preserve_output(self) -> None:
        repo = TOOLS.parent
        result = subprocess.run(
            [sys.executable, str(TOOLS / "gen_brief.py"), "UC-AUTH-005", "--stdout", "--quiet"],
            cwd=repo, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, (repo / "auth-center/briefs/UC-AUTH-005.md").read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            spec = Path(folder) / "broken.json"
            output = Path(folder) / "brief.md"
            spec.write_text('{"uc":"UC-AUTH-005","query_sections":'
                            '{"auth-center/query-contracts/missing.md":["读取"]}}')
            output.write_bytes(b"keep existing output\n")
            failed = subprocess.run(
                [sys.executable, str(TOOLS / "gen_brief.py"), "UC-AUTH-005",
                 "--spec", str(spec), "--out", str(output)],
                cwd=repo, capture_output=True,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(output.read_bytes(), b"keep existing output\n")


if __name__ == "__main__":
    unittest.main()
