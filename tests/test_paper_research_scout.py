"""Report-selection and source-provenance checks using isolated local fixtures."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "paper-research-scout/scripts/collect_reports.py"


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def report(self, name, text="# 合成日报\n[paper](https://arxiv.org/abs/2608.12345)\n"):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def cli(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), "--reports-dir", str(self.root),
                                 "--as-of", "2026-09-17", *map(str, args)],
                                text=True, capture_output=True, check=False)
        return result, json.loads(result.stdout) if result.returncode == 0 else None

    def test_latest_uses_dates_not_mtime_and_excludes_future(self):
        old = self.report("2026-08-26.md")
        self.report("2026-09-14.md")
        self.report("2026-09-20.md")
        self.report("2026-99-99.md")
        os.utime(old, (2000000000, 2000000000))
        process, value = self.cli()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(value["reports"][0]["report_date"], "2026-09-14")
        self.assertEqual(value["selection"]["excluded_future_dates"], ["2026-09-20"])
        self.assertTrue(value["warnings"])

    def test_explicit_date_does_not_get_replaced_by_latest(self):
        self.report("2026-08-26.md")
        self.report("2026-09-14.md")
        process, value = self.cli("--date", "2026-08-26")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(value["reports"][0]["report_date"], "2026-08-26")

    def test_missing_explicit_date_fails_without_fallback(self):
        self.report("2026-09-14.md")
        process, _ = self.cli("--date", "2026-08-26")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, "")

    def test_latest_no_new_batch_note_remains_selected(self):
        self.report("2026-09-13.md")
        self.report("2026-09-14.md", "No new candidate batch today.\n")
        _, value = self.cli()
        self.assertEqual(value["reports"][0]["report_date"], "2026-09-14")
        self.assertEqual(value["papers"], [])

    def test_range_reports_gaps_and_never_fills_them(self):
        self.report("2026-08-23.md")
        self.report("2026-08-25.md")
        self.report("2026-08-27.md")
        process, value = self.cli("--start", "2026-08-24", "--end", "2026-08-26")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(len(value["reports"]), 1)
        self.assertEqual(value["selection"]["missing_ranges"], [
            {"start": "2026-08-24", "end": "2026-08-24"},
            {"start": "2026-08-26", "end": "2026-08-26"}])

    def test_invalid_selection_arguments_fail(self):
        for args in [("--latest", "0"), ("--end", "2026-08-26"),
                     ("--start", "2026-08-26"), ("--date", "2026-02-30"),
                     ("--start", "2026-08-26", "--end", "2026-08-25"),
                     ("--date", "2026-08-26", "--latest", "1")]:
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args)[0].returncode, 2)

    def test_arxiv_versions_and_pdf_abstract_share_identity_but_keep_provenance(self):
        text = "\n".join(["# 合成材料", "[v1](https://arxiv.org/abs/2608.12345v1)",
                          "[v2 pdf](https://arxiv.org/pdf/2608.12345v2.pdf)",
                          "https://arxiv.org/html/2608.12345v2", "https://arxiv.org/abs/2608.12345。"])
        path = self.report("2026-08-26.md", text)
        _, value = self.cli("--report", path, "--include-text")
        self.assertEqual(len(value["papers"]), 1)
        paper = value["papers"][0]
        self.assertEqual(paper["versions"], [None, 1, 2])
        self.assertEqual([o["line"] for o in paper["occurrences"]], [2, 3, 4, 5])
        self.assertEqual(value["reports"][0]["text"], text)

    def test_cross_day_duplicates_retain_both_report_occurrences(self):
        self.report("2026-08-25.md")
        self.report("2026-08-26.md")
        _, value = self.cli("--latest", "2")
        self.assertEqual(len(value["papers"]), 1)
        self.assertEqual(len(value["papers"][0]["occurrences"]), 2)

    def test_legacy_ids_and_external_links(self):
        self.report("2026-08-26.md", "https://arxiv.org/abs/cs/9901001v2\nhttps://example.com/abs/2608.12345\n")
        _, value = self.cli()
        self.assertEqual(value["papers"][0]["id"], "arxiv:cs/9901001")
        self.assertEqual(len(value["papers"]), 1)
        self.assertEqual(len(value["reports"][0]["source_links"]), 2)

    def test_read_only_and_hash_matches_original_bytes(self):
        path = self.report("2026-08-26.md")
        before = path.read_bytes()
        _, value = self.cli("--report", path, "--report", path)
        self.assertEqual(len(value["reports"]), 1)
        self.assertEqual(value["reports"][0]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_explicit_future_input_flagged_not_silently_replaced(self):
        path = self.report("2026-09-20.md")
        _, value = self.cli("--report", path)
        self.assertEqual(value["reports"][0]["report_date"], "2026-09-20")
        self.assertIn("future-dated", value["warnings"][0])

    def test_empty_and_undated_explicit_reports_are_not_invented_papers(self):
        path = self.report("my-reading-notes.md", "")
        _, value = self.cli("--report", path)
        self.assertEqual(value["papers"], [])
        self.assertIsNone(value["reports"][0]["report_date"])
        self.assertIn("Empty", value["warnings"][0])

    def test_empty_directory_fails(self):
        self.assertEqual(self.cli()[0].returncode, 2)


if __name__ == "__main__":
    unittest.main()
