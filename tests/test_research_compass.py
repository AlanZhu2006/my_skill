"""Observable ledger behavior, including CLI persistence and concurrent reservations."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research-compass/scripts/research_ledger.py"
EXAMPLE = ROOT / "research-compass/assets/experiment.example.json"
MODULE_SPEC = importlib.util.spec_from_file_location("research_ledger", SCRIPT)
ledger = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(ledger)


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "runs.json"
        self.spec = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def cli(self, command, *arguments):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), command, "--ledger", str(self.path), *map(str, arguments)],
            text=True, capture_output=True, check=False)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def plan(self, spec=None):
        return self.cli("plan", "--spec", self.write("spec.json", spec or self.spec))

    def result(self, outcome="inconclusive"):
        artifact = self.root / "evidence.md"
        artifact.write_text("Synthetic fixture evidence, not a real scientific result.\n", encoding="utf-8")
        return {"outcome": outcome, "summary": "合成测试数据，保留不确定性。",
                "decision": "Inspect the independent sampling units before replication.",
                "metrics": None, "artifacts": [str(artifact)]}

    def finish(self, outcome="inconclusive"):
        return self.cli("finish", "--id", "E-001", "--result",
                        self.write("result.json", self.result(outcome)))

    def repeat(self, kind="replication"):
        spec = copy.deepcopy(self.spec)
        spec["id"] = "E-002"
        spec["revisit"] = {
            "kind": kind, "of": "E-001", "reason": "Test technical nondeterminism.",
            "change": "A new process, intentionally unchanged inputs.",
            "decision_rule": "Compare all three planned replays, never the best one."}
        return spec

    def test_check_is_read_only(self):
        code, report = self.cli("check", "--spec", self.write("spec.json", self.spec))
        self.assertEqual(code, 0)
        self.assertTrue(report["allowed"])
        self.assertFalse(self.path.exists())
        self.assertFalse(self.path.with_suffix(".json.lock").exists())

    def test_reservation_survives_new_process_and_renamed_claim(self):
        self.assertEqual(self.plan()[0], 0)
        spec = copy.deepcopy(self.spec)
        spec.update(id="new-name", hypothesis_id="new-hypothesis", claim="A renamed story")
        code, report = self.plan(spec)
        self.assertEqual(code, 3)
        self.assertEqual(report["exact_matches"][0]["id"], "E-001")
        self.assertEqual(len(json.loads(self.path.read_text())["runs"]), 1)

    def test_pending_repeat_blocked_even_with_reason(self):
        self.plan()
        self.assertEqual(self.plan(self.repeat())[0], 3)

    def test_key_order_does_not_change_identity(self):
        altered = copy.deepcopy(self.spec)
        altered["execution"] = dict(reversed(list(altered["execution"].items())))
        self.assertEqual(ledger.fingerprint(self.spec), ledger.fingerprint(altered))

    def test_changed_configuration_retains_scientific_history(self):
        self.plan()
        self.finish("refuted")
        spec = copy.deepcopy(self.spec)
        spec["id"] = "E-002"
        spec["execution"]["config"]["workload_size"] = 200
        code, report = self.plan(spec)
        self.assertEqual(code, 0)
        self.assertEqual(report["exact_matches"], [])
        self.assertEqual(report["related_runs"][0]["outcome"], "refuted")

    def test_finished_exact_repeat_requires_rationale(self):
        self.plan()
        self.finish()
        spec = copy.deepcopy(self.spec)
        spec["id"] = "E-002"
        self.assertEqual(self.plan(spec)[0], 3)
        self.assertEqual(self.plan(self.repeat())[0], 0)

    def test_retry_of_invalid_run_and_null_metrics(self):
        self.plan()
        self.assertEqual(self.finish("invalid")[0], 0)
        self.assertEqual(self.plan(self.repeat("retry"))[0], 0)
        old = json.loads(self.path.read_text())["runs"][0]["result"]
        self.assertIsNone(old["metrics"])
        self.assertEqual(old["outcome"], "invalid")

    def test_retry_cannot_relabel_a_valid_negative(self):
        self.plan()
        self.finish("refuted")
        self.assertEqual(self.plan(self.repeat("retry"))[0], 3)

    def test_extension_must_change_execution(self):
        self.plan()
        self.finish()
        spec = self.repeat("extension")
        self.assertEqual(self.plan(spec)[0], 3)
        spec["execution"]["data_version"] = "held-out-workload-v2"
        self.assertEqual(self.plan(spec)[0], 0)

    def test_revisit_must_link_to_actual_matching_run(self):
        self.plan()
        self.finish()
        spec = self.repeat()
        spec["revisit"]["of"] = "missing"
        self.assertEqual(self.plan(spec)[0], 3)

    def test_terminal_outcome_is_idempotent_and_cannot_be_overwritten(self):
        self.plan()
        self.finish("refuted")
        before = self.path.read_bytes()
        self.assertTrue(self.finish("refuted")[1]["unchanged"])
        self.assertEqual(self.finish("supported")[0], 2)
        self.assertEqual(self.path.read_bytes(), before)
        code, report = self.cli("status")
        self.assertEqual(code, 0)
        self.assertEqual(report["runs"][0]["outcome"], "refuted")

    def test_invalid_measurement_cannot_be_recorded_as_zero_score(self):
        self.plan()
        result = self.result("invalid")
        result["metrics"] = {"accuracy": 0}
        code, _ = self.cli("finish", "--id", "E-001", "--result", self.write("result.json", result))
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(self.path.read_text())["runs"][0]["status"], "planned")

    def test_cancelled_reservation_can_be_explicitly_retried(self):
        self.plan()
        self.finish("cancelled")
        self.assertEqual(self.plan(self.repeat("retry"))[0], 0)

    def test_unknown_run_cannot_be_finished(self):
        self.assertEqual(self.finish()[0], 2)
        self.assertFalse(self.path.exists())

    def test_missing_provenance_budget_and_seed_rejected(self):
        for mutate in (
                lambda s: s["execution"].pop("seed"),
                lambda s: s["execution"].update(code_version=""),
                lambda s: s["budget"].update(limit=-1),
                lambda s: s["budget"].update(limit=True),
                lambda s: s.update(decision="")):
            with self.subTest(mutation=mutate):
                spec = copy.deepcopy(self.spec)
                mutate(spec)
                self.assertEqual(self.plan(spec)[0], 2)
        self.assertFalse(self.path.exists())

    def test_duplicate_keys_nonfinite_and_overflow_json_rejected(self):
        path = self.root / "bad.json"
        for content in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                self.assertEqual(self.cli("plan", "--spec", path)[0], 2)
        self.assertFalse(self.path.exists())

    def test_corrupted_ledger_is_not_overwritten(self):
        self.path.write_text('{"version":1,"runs":[', encoding="utf-8")
        before = self.path.read_bytes()
        self.assertEqual(self.plan()[0], 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_changed_fingerprint_in_ledger_is_not_overwritten(self):
        self.plan()
        value = json.loads(self.path.read_text())
        value["runs"][0]["spec"]["execution"]["seed"] = 123
        self.path.write_text(json.dumps(value), encoding="utf-8")
        before = self.path.read_bytes()
        self.assertEqual(self.plan()[0], 2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_reservations_allow_one_execution(self):
        first = self.write("first.json", self.spec)
        second_spec = copy.deepcopy(self.spec)
        second_spec["id"] = "E-002"
        second = self.write("second.json", second_spec)
        processes = [subprocess.Popen(
            [sys.executable, str(SCRIPT), "plan", "--ledger", str(self.path), "--spec", str(path)],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for path in (first, second)]
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(stderr, "")
            json.loads(stdout)
        self.assertEqual(sorted(p.returncode for p in processes), [0, 3])
        self.assertEqual(len(json.loads(self.path.read_text())["runs"]), 1)


if __name__ == "__main__":
    unittest.main()
