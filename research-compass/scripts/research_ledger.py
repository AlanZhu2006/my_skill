#!/usr/bin/env python3
"""Local experiment reservations and immutable outcomes; Python 3.9+, POSIX."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile


class LedgerError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def reject_constant(value):
    raise LedgerError("Non-finite JSON number: " + value)


def unique_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise LedgerError("Duplicate JSON key: " + key)
        value[key] = item
    return value


def read_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        value = json.load(stream, parse_constant=reject_constant,
                          object_pairs_hook=unique_keys)
    canonical(value)  # Also reject overflowing numbers such as 1e999.
    return value


def require_object(value, name):
    if not isinstance(value, dict):
        raise LedgerError(name + " must be an object")


def require_text(value, fields, name):
    require_object(value, name)
    for field in fields:
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise LedgerError(name + "." + field + " must be nonempty text")


def validate_spec(spec):
    require_text(spec, ("id", "question_id", "hypothesis_id", "comparison_id",
                        "claim", "rival", "prediction", "decision", "stop_rule"), "spec")
    execution = spec.get("execution")
    require_text(execution, ("code_version", "data_version", "protocol_version"), "execution")
    require_object(execution.get("config"), "execution.config")
    if "seed" not in execution or (execution["seed"] is not None
                                   and type(execution["seed"]) is not int):
        raise LedgerError("execution.seed must be an integer or explicit null")
    budget = spec.get("budget")
    require_text(budget, ("unit",), "budget")
    limit = budget.get("limit")
    if type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0:
        raise LedgerError("budget.limit must be a positive finite number")
    if "revisit" in spec:
        revisit = spec["revisit"]
        require_text(revisit, ("kind", "of", "reason", "change", "decision_rule"), "revisit")
        if revisit["kind"] not in ("retry", "replication", "extension"):
            raise LedgerError("revisit.kind must be retry, replication, or extension")
    canonical(spec)


def fingerprint(spec):
    """Labels and narrative cannot make an identical execution look new."""
    return hashlib.sha256(canonical(spec["execution"]).encode("utf-8")).hexdigest()


def validate_result(result):
    require_text(result, ("outcome", "summary", "decision"), "result")
    if result["outcome"] not in ("supported", "refuted", "inconclusive", "invalid", "cancelled"):
        raise LedgerError("Unknown outcome")
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts or any(
            not isinstance(item, str) or not item.strip() for item in artifacts):
        raise LedgerError("result.artifacts must contain evidence paths or URLs")
    if "metrics" not in result:
        raise LedgerError("result.metrics is required; use null when not measured")
    if result["metrics"] is not None:
        require_object(result["metrics"], "result.metrics")
        for value in result["metrics"].values():
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise LedgerError("Metrics must be finite numbers or null")
    if result["outcome"] in ("invalid", "cancelled") and result["metrics"] is not None:
        raise LedgerError("Invalid/cancelled runs need null metrics; retain diagnostics in artifacts")
    canonical(result)


def load_ledger(path):
    if not path.exists():
        return {"version": 1, "runs": []}
    ledger = read_json(path)
    require_object(ledger, "ledger")
    if ledger.get("version") != 1 or not isinstance(ledger.get("runs"), list):
        raise LedgerError("Unsupported or malformed ledger; refusing to overwrite")
    ids = set()
    for run in ledger["runs"]:
        require_object(run, "run")
        spec = run.get("spec")
        validate_spec(spec)
        if spec["id"] in ids or run.get("fingerprint") != fingerprint(spec):
            raise LedgerError("Duplicate ID or inconsistent fingerprint in ledger")
        ids.add(spec["id"])
        if run.get("status") not in ("planned", "finished"):
            raise LedgerError("Invalid run status")
        if run["status"] == "finished":
            validate_result(run.get("result"))
        elif "result" in run:
            raise LedgerError("Planned run unexpectedly contains a result")
    return ledger


@contextmanager
def locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep a separate stable inode while replacing the ledger atomically.
    with path.with_name(path.name + ".lock").open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def save_ledger(path, ledger):
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(ledger, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def brief(run):
    spec = run["spec"]
    return {"id": spec["id"], "question_id": spec["question_id"],
            "comparison_id": spec["comparison_id"], "status": run["status"],
            "outcome": run.get("result", {}).get("outcome"),
            "decision": run.get("result", {}).get("decision", spec["decision"])}


def assess(ledger, spec):
    validate_spec(spec)
    runs = ledger["runs"]
    digest = fingerprint(spec)
    same = [run for run in runs if run["fingerprint"] == digest]
    related = [brief(run) for run in runs if
               run["spec"]["question_id"] == spec["question_id"] or
               run["spec"]["comparison_id"] == spec["comparison_id"]]
    reasons = []
    if any(run["spec"]["id"] == spec["id"] for run in runs):
        reasons.append("Run ID already exists; inspect/resume it instead of reserving it again")
    if any(run["status"] == "planned" for run in same):
        reasons.append("Identical execution is already reserved; reconcile its job before relaunching")
    revisit = spec.get("revisit")
    target = None
    if revisit:
        target = next((run for run in runs if run["spec"]["id"] == revisit["of"]), None)
        if target is None or target["status"] != "finished":
            reasons.append("A revisit must refer to a finished run in this ledger")
        elif revisit["kind"] == "retry" and target["result"]["outcome"] not in ("invalid", "cancelled"):
            reasons.append("A retry must repair an invalid or cancelled run")
    if same:
        if not revisit or revisit["kind"] not in ("retry", "replication"):
            reasons.append("Identical execution exists; reuse it or document a retry/replication")
        elif target not in same:
            reasons.append("An exact repeat must link to one of its matching executions")
    return {"allowed": not reasons, "fingerprint": digest, "reasons": reasons,
            "exact_matches": [brief(run) for run in same], "related_runs": related,
            "note": "Execution eligibility only; review scientific overlap and budget before launch."}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def operate(args):
    path = Path(args.ledger).expanduser().resolve()
    if args.command in ("check", "status"):
        ledger = load_ledger(path)  # Atomic replacement makes a lock-free snapshot safe.
        if args.command == "status":
            return {"runs": [brief(run) for run in ledger["runs"]]}, 0
        report = assess(ledger, read_json(args.spec))
        return report, 0 if report["allowed"] else 3
    with locked(path):
        ledger = load_ledger(path)
        if args.command == "plan":
            spec = read_json(args.spec)
            report = assess(ledger, spec)
            if not report["allowed"]:
                return report, 3
            ledger["runs"].append({"spec": spec, "fingerprint": report["fingerprint"],
                                   "status": "planned", "created_at": timestamp()})
            save_ledger(path, ledger)
            report["reserved"] = spec["id"]
            return report, 0
        result = read_json(args.result)
        validate_result(result)
        run = next((item for item in ledger["runs"] if item["spec"]["id"] == args.id), None)
        if run is None:
            raise LedgerError("Unknown run ID")
        if run["status"] == "finished":
            if run["result"] == result:
                return {"finished": args.id, "unchanged": True}, 0
            raise LedgerError("Outcome already recorded; preserve it and link a correction in project notes")
        run.update(status="finished", result=result, finished_at=timestamp())
        save_ledger(path, ledger)
        return {"finished": args.id, "outcome": result["outcome"]}, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "plan", "finish", "status"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--ledger", required=True, help="Project-local JSON ledger")
        if command in ("check", "plan"):
            sub.add_argument("--spec", required=True, help="Experiment specification JSON")
        if command == "finish":
            sub.add_argument("--id", required=True)
            sub.add_argument("--result", required=True, help="Outcome JSON with evidence links")
    args = parser.parse_args()
    try:
        report, code = operate(args)
    except (ValueError, OSError) as exc:
        report, code = {"error": str(exc)}, 2
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
