# Optional local experiment ledger

Use this helper when the project lacks equivalent run tracking. Existing trackers remain appropriate. This is a Python 3.9+ standard-library CLI for macOS/Linux local filesystems. It checks reservations and preserves outcomes; it does **not** execute jobs, measure costs, enforce budgets, verify artifacts, or decide scientific value.

Keep the ledger with project evidence, outside the installed skill folder. Paths below are examples relative to a project directory; replace `/path/to/research-compass` with the installed skill's location.

## Workflow

Adapt [the synthetic example](../assets/experiment.example.json) into `experiment.json`. The sample is not a runnable scientific experiment and supplies no observed result. Use real provenance before reserving actual work.

```bash
python3 /path/to/research-compass/scripts/research_ledger.py check --ledger research/runs.json --spec experiment.json
python3 /path/to/research-compass/scripts/research_ledger.py plan --ledger research/runs.json --spec experiment.json
```

`check` reads only and is advisory. `plan` repeats the check under a local file lock and atomically records a reservation. Launch only after `plan` succeeds and the scientific decision/budget are appropriate. If another task reserves the run first, reuse or reconcile that run. Record the actual job ID and output path in project state; a reservation does not mean a job was launched.

After inspecting the real outputs, write a result JSON such as:

```json
{
  "outcome": "inconclusive",
  "summary": "Illustrative only: the paired interval crosses the predeclared meaningful effect.",
  "decision": "Check whether enough independent workloads are available before investing in another run.",
  "metrics": {"paired_latency_change_ms": null},
  "artifacts": ["research/evidence/E-001-analysis.md"]
}
```

Replace illustrative text and the path with actual evidence; the helper checks structure, not scientific truth or file existence.

```bash
python3 /path/to/research-compass/scripts/research_ledger.py finish --ledger research/runs.json --id E-001 --result result.json
python3 /path/to/research-compass/scripts/research_ledger.py status --ledger research/runs.json
```

Outcomes are `supported`, `refuted`, `inconclusive`, `invalid`, and operationally `cancelled`. Support/refutation is always scoped to the declared claim, conditions, and tested rival. Invalid or cancelled runs require `metrics: null`; put partial diagnostic measurements in their evidence artifacts. Cancelling a reservation does not terminate its process: first reconcile or stop the actual job owned by this task, then record the cancellation and why.

The same `finish` with the same result is idempotent. A different result cannot silently replace a completed one. For a later interpretation correction, preserve the original record and link a dated correction in the research state; consult that correction before interpreting or reusing the result.

## What is compared

The SHA-256 fingerprint covers the complete `execution` object using canonical JSON key order. Narrative, run IDs, hypothesis IDs, budgets, and timestamps outside `execution` do not alter it. Include all result-affecting inputs there:

- `code_version`: immutable revision **and** a digest of uncommitted changes, or a complete code snapshot digest. Include relevant untracked source files; a commit alone does not capture dirty code.
- `data_version`: immutable dataset/content version and exact split or subset identity.
- `protocol_version`: version of preprocessing, evaluation, units, aggregation, and stopping/sampling procedure.
- `config`: the method and all effective parameters, including defaults that matter. Include dependency/environment versions where they can change the result.
- `seed`: integer, or explicit `null` when no seed applies. For several randomness sources, add their full specification to `execution`.

Do not use moving labels such as `latest` or put run-specific output directories/timestamps inside `execution`. This is exact declared-input matching: numeric/string differences and altered metadata can change a hash even if execution is scientifically equivalent. The helper cannot detect a false version, hash live code, or establish independence.

Stable `question_id`, `hypothesis_id`, and `comparison_id` connect the runs to the research state. `comparison_id` identifies the contrast being studied across variants. The report shows prior runs sharing the question or comparison so the agent can review semantic repetition. Renaming IDs to bypass that review is not new information. Inspect the full relevant history when terminology changes.

## Intentional revisits

An exact repeat is blocked unless it references a finished matching execution with a documented `retry` or `replication`. A still-reserved identical execution is blocked even with a reason. Reconcile interrupted jobs before closing their reservation; do not infer that they ended from a new session.

Add a new run ID and a `revisit` object, for example:

```json
{
  "kind": "replication",
  "of": "E-001",
  "reason": "Measure hardware nondeterminism under an otherwise identical execution.",
  "change": "Independent process execution; inputs and seed held fixed intentionally.",
  "decision_rule": "Use the prespecified paired analysis after three replays; do not select the best replay."
}
```

- `replication`: statistical or technical repeat; state which. A new seed changes the fingerprint but still needs a scientific replication rationale.
- `retry`: repair of an `invalid` or `cancelled` run; specify the cause and remedy. If effective inputs change, update `execution` too.
- `extension`: changed operating condition or test. It cannot authorize an identical execution.

All revisits must link to a finished run in this ledger. A reason is necessary documentation, not evidence that a repeat is worthwhile. Budget and semantic-overlap decisions remain with the researcher.

## Integrity and limits

Exit codes: `0` success/eligible, `3` blocked reservation, `2` invalid input or file error. Missing ledgers read as empty; malformed existing ledgers are rejected without overwriting. JSON rejects duplicate keys and non-finite numbers. Writes use a lock and atomic replacement to prevent concurrent local reservations of an identical execution. Read-only checks return a snapshot that can become stale.

Do not edit the ledger by hand during operation. Keep it and its evidence backed up/versioned according to project practice. The lock is for cooperating local processes, not a distributed scheduler; shared/network storage and Windows are outside this helper's supported environment. Budget limits are declarations: the execution layer must implement timeouts and resource controls. A skill cannot guarantee that an agent will make good research decisions; inspect the resulting evidence and choices.
