#!/usr/bin/env python3
"""Tests for `gen_brief.py` support of docs-root-level shared sources.

The generator is exercised in-process against a throwaway docs tree (so no real
design document is touched) plus one subprocess check against the real
repository. Run either:

    python3 tools/tests/test_gen_brief_shared.py
    python3 -m unittest discover -s tools/tests
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import gen_brief  # noqa: E402  (path setup must happen first)


UC_FILE = "use-cases/UC-TST-001-test.md"
UC_TEXT = "# UC-TST-001：测试用例\n\n状态：`ACCEPTED`\n\n## 目标与范围\n\n用例正文。\n"
SHARED_FILE = "platform/shared.md"
SHARED_TEXT = (
    "# 共享信任契约\n\n"
    "## 决定\n\n"
    "共享决定正文，引用 [UC](../app-center/use-cases/UC-TST-001-test.md) "
    "与 [同目录](other.md)。\n\n"
    "## 略\n\n未选中。\n"
)


class SharedSourceTestCase(unittest.TestCase):
    """Base fixture: a temporary docs repository laid out like the real one."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "app-center" / "use-cases").mkdir(parents=True)
        (self.root / "platform").mkdir(parents=True)
        (self.root / "app-center" / UC_FILE).write_text(UC_TEXT, encoding="utf-8")
        (self.root / SHARED_FILE).write_text(SHARED_TEXT, encoding="utf-8")
        (self.root / "platform" / "other.md").write_text("# 另一共享文档\n\n## 内容\n\nx\n", encoding="utf-8")

        self._saved = {name: getattr(gen_brief, name) for name in ("DOCS", "DOCS_REPO", "OUTPUT_REL")}
        gen_brief.DOCS = self.root / "app-center"
        gen_brief.DOCS_REPO = self.root
        gen_brief.OUTPUT_REL = "app-center/briefs"
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        for name, value in self._saved.items():
            setattr(gen_brief, name, value)
        self._tmp.cleanup()

    def registry(self) -> tuple[dict, dict, dict]:
        return (
            {"UC-TST-001": {"title": "测试用例", "path": UC_FILE, "status": "ACCEPTED"}},
            {},
            {},
        )

    def spec(self, shared_sections: dict) -> dict:
        return {
            "uc": "UC-TST-001",
            "uc_sections": ["目标与范围"],
            "shared_sections": shared_sections,
        }

    def build(self, shared_sections: dict) -> tuple[str, dict]:
        return gen_brief.build("UC-TST-001", self.spec(shared_sections), self.registry())


class SuccessTests(SharedSourceTestCase):
    def test_extracts_root_level_shared_section(self) -> None:
        brief, stats = self.build({SHARED_FILE: ["决定"]})

        self.assertIn("## 平台共享契约（按 spec 显式抽取）", brief)
        self.assertIn("### `platform/shared.md`：共享信任契约", brief)
        self.assertIn("#### 决定", brief)  # demoted to fit the brief outline
        self.assertIn("共享决定正文", brief)
        self.assertNotIn("未选中。", brief)  # only the selected section is embedded

    def test_shared_section_appears_in_body_omission_index_and_provenance(self) -> None:
        brief, stats = self.build({SHARED_FILE: ["决定"]})

        # body
        self.assertIn("共享决定正文", brief)
        # omission index lists the unselected sibling
        self.assertIn("- `platform/shared.md`（docs 根级共享文档）：略", brief)
        # provenance + sha256
        self.assertIn(f"| `{SHARED_FILE}` | 9 | `", brief)
        hash_line = next(line for line in brief.splitlines() if line.startswith(f"| `{SHARED_FILE}`"))
        self.assertRegex(hash_line, r"\|\s*`[0-9a-f]{12}`\s*\|$")

    def test_shared_sources_enter_source_volume_stats(self) -> None:
        uc_lines = len(UC_TEXT.splitlines())
        shared_lines = len(SHARED_TEXT.splitlines())

        _, stats = self.build({SHARED_FILE: ["决定"]})

        self.assertEqual(stats["source_paths"], [UC_FILE, SHARED_FILE])
        self.assertEqual(stats["baseline_lines"], uc_lines + shared_lines)
        self.assertGreater(stats["baseline_tokens"], 0)

    def test_shared_links_are_rewritten_for_the_brief_output_position(self) -> None:
        brief, _ = self.build({SHARED_FILE: ["决定"]})

        # from app-center/briefs/ both targets must still resolve
        self.assertIn("](../use-cases/UC-TST-001-test.md)", brief)
        self.assertIn("](../../platform/other.md)", brief)

    def test_only_spec_selected_shared_sources_render(self) -> None:
        brief, _ = self.build({SHARED_FILE: ["决定"]})
        self.assertNotIn("另一共享文档", brief)

    def test_render_is_deterministic_regardless_of_spec_key_order(self) -> None:
        first, _ = self.build({"platform/other.md": ["内容"], SHARED_FILE: ["决定"]})
        second, _ = self.build({SHARED_FILE: ["决定"], "platform/other.md": ["内容"]})
        self.assertEqual(first, second)


class FailClosedTests(SharedSourceTestCase):
    def test_shared_sections_must_be_an_object_even_when_empty(self) -> None:
        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build([])  # type: ignore[arg-type]
        self.assertTrue(any("must be an object" in problem for problem in caught.exception.problems))

    def test_section_paths_must_be_non_empty_strings(self) -> None:
        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({SHARED_FILE: ["决定", 7, " "]})  # type: ignore[list-item]
        joined = "\n".join(caught.exception.problems)
        self.assertIn("invalid section path: 7", joined)
        self.assertIn("invalid section path: ' '", joined)

    def test_missing_shared_section_fails_closed(self) -> None:
        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({SHARED_FILE: ["不存在的章节"]})
        problems = caught.exception.problems
        self.assertTrue(any("shared section not found" in problem for problem in problems), problems)

    def test_missing_shared_file_fails_closed(self) -> None:
        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({"platform/does-not-exist.md": ["决定"]})
        self.assertTrue(any("not found" in problem for problem in caught.exception.problems))

    def test_all_problems_are_reported_together(self) -> None:
        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({
                "platform/missing.md": ["决定"],
                SHARED_FILE: ["nope", "also-nope"],
            })
        joined = "\n".join(caught.exception.problems)
        self.assertIn("platform/missing.md", joined)
        self.assertIn("shared section not found: `platform/shared.md` → `nope`", joined)
        self.assertIn("shared section not found: `platform/shared.md` → `also-nope`", joined)

    def test_absolute_path_is_rejected(self) -> None:
        path, problem = gen_brief.resolve_shared_source("/etc/passwd")
        self.assertIsNone(path)
        self.assertIsNotNone(problem)
        self.assertIn("must be relative", problem)

        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({"/etc/passwd": ["决定"]})
        self.assertTrue(any("must be relative" in problem for problem in caught.exception.problems))

    def test_parent_traversal_is_rejected(self) -> None:
        for candidate in ("../outside.md", "platform/../../etc/passwd"):
            with self.subTest(candidate=candidate):
                path, problem = gen_brief.resolve_shared_source(candidate)
                self.assertIsNone(path)
                self.assertIn("`..`", problem)

    def test_shared_source_must_be_canonical_and_under_platform(self) -> None:
        cases = {
            "./platform/shared.md": "canonical POSIX form",
            "platform//shared.md": "canonical POSIX form",
            UC_FILE: "under `platform/`",
        }
        for candidate, expected in cases.items():
            with self.subTest(candidate=candidate):
                path, problem = gen_brief.resolve_shared_source(candidate)
                self.assertIsNone(path)
                self.assertIn(expected, problem)

    def test_windows_separators_are_rejected(self) -> None:
        path, problem = gen_brief.resolve_shared_source("platform\\shared.md")
        self.assertIsNone(path)
        self.assertIn("POSIX separators", problem)

    def test_link_that_resolves_outside_docs_is_left_unchanged(self) -> None:
        self.assertEqual(gen_brief.rewrite_links("[outside](../..)", SHARED_FILE), "[outside](../..)")

    def test_non_markdown_file_is_rejected(self) -> None:
        (self.root / "platform" / "notes.txt").write_text("not markdown\n", encoding="utf-8")
        path, problem = gen_brief.resolve_shared_source("platform/notes.txt")
        self.assertIsNone(path)
        self.assertIn("Markdown", problem)

    def test_directory_is_rejected(self) -> None:
        (self.root / "platform" / "adir.md").mkdir()
        path, problem = gen_brief.resolve_shared_source("platform/adir.md")
        self.assertIsNone(path)
        self.assertIn("not a regular file", problem)

    def test_symlink_escape_is_rejected(self) -> None:
        outside = Path(self._tmp.name).parent / "outside-shared.md"
        outside.write_text("# Outside\n\n## 决定\n\nleak\n", encoding="utf-8")
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        link = self.root / "platform" / "leak.md"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as error:  # pragma: no cover - platform dependent
            self.skipTest(f"symlinks unavailable: {error}")

        path, problem = gen_brief.resolve_shared_source("platform/leak.md")
        self.assertIsNone(path)
        self.assertIn("escapes the docs repository root", problem)

        with self.assertRaises(gen_brief.BriefInputError) as caught:
            self.build({"platform/leak.md": ["决定"]})
        self.assertTrue(any("escapes the docs repository root" in problem for problem in caught.exception.problems))


class BaselineTests(SharedSourceTestCase):
    def test_shared_sources_stay_out_of_the_baseline_unless_selected(self) -> None:
        spec = {"title": "工程基线", "adr_sections": {}}
        brief, stats = gen_brief.build(None, spec, self.registry())
        self.assertNotIn("平台共享契约", brief)
        self.assertEqual(stats["source_paths"], [])

    def test_shared_sources_can_be_selected_explicitly_in_the_baseline(self) -> None:
        spec = {"title": "工程基线", "adr_sections": {}, "shared_sections": {SHARED_FILE: ["决定"]}}
        brief, stats = gen_brief.build(None, spec, self.registry())
        self.assertIn("平台共享契约（按 spec 显式抽取）", brief)
        self.assertIn(SHARED_FILE, stats["source_paths"])


class RepositoryGateTests(unittest.TestCase):
    """The real repository must keep passing with no shared spec selected."""

    def test_check_all_does_not_regress(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "gen_brief.py"), "--check", "--all"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_shared_spec_keeps_app_center_briefs_byte_identical(self) -> None:
        before = (REPO_ROOT / "app-center" / "briefs" / "UC-APP-003.md").read_bytes()
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "gen_brief.py"), "UC-APP-003", "--stdout"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stdout, before)

    def test_failed_cli_generation_does_not_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec = temp / "broken.json"
            output = temp / "brief.md"
            sentinel = b"existing brief must survive\n"
            spec.write_text(
                '{"uc":"UC-APP-003","uc_sections":["目标与范围"],'
                '"include_own_brs":false,"include_external_brs":false,'
                '"shared_sections":{"platform/missing.md":["决定"]}}\n',
                encoding="utf-8",
            )
            output.write_bytes(sentinel)

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "gen_brief.py"),
                    "UC-APP-003",
                    "--spec",
                    str(spec),
                    "--out",
                    str(output),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to emit an incomplete design input", result.stderr)
            self.assertEqual(output.read_bytes(), sentinel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
