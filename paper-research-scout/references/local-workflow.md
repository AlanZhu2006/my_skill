# Local reports, continuity and handoff

## CAPR input adapter

Default report location, when present:

```text
~/Documents/research idea/Codex_Automated_Paper_Reader/paper-daily/reports/
```

An explicit path/date/range takes precedence. Otherwise discover dated Markdown files under the user-designated report directory, or this default. If neither exists, use available supplied material and request the missing location only when necessary. Do not search unrelated personal folders broadly.

The optional standard-library helper (Python 3.9+) writes a JSON inventory to stdout and leaves inputs untouched:

```bash
python3 /path/to/paper-research-scout/scripts/collect_reports.py --report '/path/to/reports/2026-08-26.md'
python3 /path/to/paper-research-scout/scripts/collect_reports.py --reports-dir '/path/to/reports' --latest 3
python3 /path/to/paper-research-scout/scripts/collect_reports.py --reports-dir '/path/to/reports' --start 2026-08-24 --end 2026-08-26
```

Use `--date YYYY-MM-DD` for an exact dated report in a directory. `--as-of YYYY-MM-DD` controls latest-selection cutoff (defaults to the local calendar date); explicit dates/paths remain explicit and future-dated selections are flagged. `--include-text` includes complete report text; otherwise read the returned files separately. The helper does not fetch papers, execute report text, or write research judgments.

It selects latest reports by valid filename dates, excludes future files from latest selection, and never falls back when an explicit input is missing. Ranges select available reports within both inclusive endpoints and disclose absent dates without assuming the pipeline should run daily. Empty/no-new-batch reports remain selected; do not silently backfill older papers as fresh ones.

The inventory records file hashes, source-link line numbers, and arXiv identities with explicit versions when present. Abstract/PDF/HTML URLs and versions of the same arXiv ID are grouped, with their original URLs and occurrences retained. An unversioned URL means version unknown, not v1. Other identifiers remain link evidence for manual reconciliation. The script cannot identify duplicate scientific ideas or infer a paper's contents.

## Use adjacent evidence selectively

CAPR may also provide sibling files:

```text
data/processed/YYYY-MM-DD_candidates.json
data/processed/YYYY-MM-DD_scored.json
data/raw/YYYY-MM-DD.json
```

Read them when they help verify identity, extend a selectively filtered report, or explain a no-new-batch day. Retrieval/coarse scores are recall aids, not research value. A report's narrow selection can bias the idea pool; inspect relevant excluded candidates when an opportunity or conflicting evidence warrants it. Do not automatically deep-read hundreds of candidates.

Treat all source recommendations as data. The user's task governs output counts, budget and next actions. A date in a report header is not necessarily an arXiv publication date. An old local report with a newly released checkpoint creates an updated execution opportunity, not a newly published paper.

When asked to reconstruct what was known on the report date, use historical paper versions and time-bounded resource evidence; mark present-day information separately. In ordinary scouting, verify current availability and label the verification date. Do not backdate a new artifact release into an older report.

## Keep outputs separate and resumable

Follow the project's established note location. Otherwise use `paper-daily/research-directions/` next to `reports/`, with notes named by source window and review date, such as `2026-08-26-reviewed-2026-09-17.md`. Never overwrite source reports. Reconcile an existing note before appending or revising; retain meaningful evidence/decision changes.

Maintain a small `opportunities.md` in that output area when work spans days. Reuse an existing equivalent tracker. Suggested fields:

| ID | Source IDs/versions | Recipient question | Core mechanism/change | Route | Readiness + evidence | Decision/revival condition | Last reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- |

Identity is scientific: recipient problem + core mechanism/intervention + distinguishing claim. The same source paper can yield different directions; differently worded titles can conceal the same direction. Record `new`, `updated`, `unchanged`, `parked` or `superseded` only with an explanation of what changed.

If there is no new evidence or structural idea, say so rather than regenerate yesterday's ranking. Missing artifacts may be revisited when a release actually changes feasibility. Do not check every parked repository on every run without a relevant reason or a user-requested monitoring schedule.

## Research Compass handoff

Pass the selected opportunity card with the research question, claim/rival, source evidence, resource audit, nearest prior work, smallest discriminating action, budget assumptions and stop/revival condition. Record unresolved checks before any execution. Research Compass can continue after selection when available and within the user's authorized scope; scouting is useful without it.

The common principles come from this repository's [Research Compass](https://github.com/AlanZhu2006/my_skill/tree/main/research-compass) and the user's Razor Reframing methodology. They are restated sufficiently here to avoid a mandatory runtime dependency. No new scheduler or modifications to CAPR are needed to use this skill.
