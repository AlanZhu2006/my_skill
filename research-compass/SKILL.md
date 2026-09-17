---
name: research-compass
description: Advance scientific research by finding meaningful openings in existing work, designing methods, intuitive reframing, and informative experiments. Use for developing research ideas, improving baselines, investigating mechanisms, continuing a project, or escaping an unproductive experiment loop while preserving the core question and budget.
---

# Research Compass

Make progress on a research question, not on a counter of experiments. Preserve the user's goal; allow explanations, representations, methods, and local plans to change. Use intuition to generate possibilities and evidence to decide what survives. Respond in the user's language.

Aim for a useful, defensible contribution relative to existing work. A promising direction may already have many papers, and a good new method may build almost entirely on known components. Seek a consequential remaining difficulty and a justified way forward; do not optimize for distance from all prior work or require a new paradigm.

## Establish the compass

Bind the question from the current user request. In open direction discovery, the question may be which phenomenon deserves investigation; do not substitute a previous project's question or architecture merely because its notes are available. Establish independent candidates before consulting old idea history for duplication or contrary evidence. The user's research interests guide exploration without forcing project reuse.

When continuing an established project or preparing another run, read its relevant notes, existing results, code and user constraints. Resume from evidence already present; a fresh session does not require a fresh baseline. Preserving the main question in this mode does not mean importing that question into unrelated discovery.

Distinguish four things:

- **Question:** what the user wants to understand or make possible, and why it matters.
- **Claim:** the specific explanation or capability currently being investigated.
- **Evidence:** observations with provenance, uncertainty, and validity limits.
- **Action:** the next intervention that could change a research decision.

For sustained work, keep a compact state file using [the state template](assets/research-state.md), adapted to existing project conventions. Preserve the question, constraints, success conditions, current uncertainty, available resources, and next decision. Do not create parallel logs if the project already has equivalents. For a one-off brainstorm, a concise answer can serve as the state.

Fix the main question at the level the user intended. Changing a solver, representation, or hypothesis can be part of the same question. Replacing the question, target population, success criterion, or task is a scope change: explain the evidence and seek the user's direction when it is outside existing authorization. Do not quietly improve an easier proxy and call the original problem solved.

Choose a finite working horizon within the user's budget and available resources. If no budget was supplied, proceed with reading, existing-result analysis, and small local probes that fit the current task; do not infer an unlimited or paid experiment campaign. Reuse prior authorization. A review checkpoint is a decision point, not a mandatory permission request.

## Choose the mode that resolves the current uncertainty

Do not mechanically run every mode on every iteration.

| Situation | Useful next move |
| --- | --- |
| A phenomenon has no satisfying explanation | Reframe it and derive distinguishable consequences. |
| A promising mechanism has an unresolved assumption | Inspect evidence or run the smallest discriminating test. |
| A result is surprisingly good | Check validity and a simpler rival explanation before expanding. |
| Several runs teach the same lesson | Consolidate, inspect external ideas, and reconsider the representation or premise. |
| A mechanism is already supported narrowly | Test its stated boundary or generalization; avoid reopening settled details. |
| Close papers overlap the proposed idea | Use them as baselines; locate what they resolve and what remains before revising the method or claim. |
| A meaningful limitation is sufficiently understood | Design and compare a concrete intervention; further reframing is optional. |
| Evidence is sufficient for the requested deliverable | Synthesize, report limits, and finish. |

### Discover: intuition with consequences

Use **See → Strip → Reframe → Unfold → Select → Verify** as thinking moves, not a questionnaire. Read [reframing.md](references/reframing.md) when generating ideas or escaping a plateau.

A clear practical bottleneck in a mature method is also a valid starting point. Use direct method development when it fits; a surprising phenomenon, cross-domain analogy or change of worldview is not a prerequisite.

Start with an actual tension: a success nobody explains well, a failure, redundancy, an information limit, a new observable, or an unexpected analogy. Describe it without inherited method names. Ask what remains when the backbone, benchmark, coordinates, and conventional task boundary are removed.

Consider genuinely different explanations when uncertainty warrants it, including a simple or null explanation. A candidate must produce a consequence that could distinguish it from a rival. Avoid manufacturing a fixed number of ideas or forcing a fashionable theory onto the problem. An intuitive sketch is a legitimate beginning; formalization should clarify it.

### Connect: look outside the current approach

Consult relevant primary papers and inspect open-source implementations before substantial investment in an unfamiliar approach or a novelty claim. For a stuck project, search for the structural problem in neighboring fields, not just the project's terminology. Use available browsing, repository, and paper tools; no specific provider or framework is required.

Record what a source actually contributes: its mechanism, assumptions, code location/version when inspected, and what transfers or fails to transfer. Distinguish a paper's claim, code behavior, and locally reproduced evidence. A repository link alone is not implementation inspection. If access is unavailable, state the gap and narrow the claim.

Treat related work as a source of baselines, useful components and unresolved boundaries. Separate overlap in the broad area, the specific problem, and the proposed solution under comparable conditions. Finding one or two close papers calls for positioning the contribution; their existence or popularity alone is not evidence to abandon the direction. A prior result can invalidate a claimed first or a particular method without closing the research question.

Use a dated candidate statement before a targeted equivalence search to preserve idea provenance; this is not a reason to postpone basic literature familiarization. Stop searching when the decision has enough support, or state the specific gap worth resolving next. See [reframing.md](references/reframing.md) for analogy and search methods, and [open-source-patterns.md](references/open-source-patterns.md) for the design sources behind this skill.

### Develop: turn the remaining difficulty into a method

When selecting a contribution or proposing a method, read [contribution-design.md](references/contribution-design.md). Establish what the closest methods achieve, the important condition or cost they still struggle with, and whether that limitation is observed, reported, or only suspected. Missing evaluation alone does not prove a failure or a research gap.

Connect the remaining difficulty to a candidate cause and a concrete design change: what is computed, retained, selected, learned or optimized differently, why it could help, and what it costs. Reusing a backbone, objective, representation or component is legitimate. A module, loss, integration or engineering improvement can be research when its design addresses the difficulty and its added value is demonstrated. Neither small code changes nor familiar ingredients disqualify it.

If the user asks for a new method, develop a plausible method sketch and its strongest simple alternative, with a comparison that can separate them. Mark uncertain assumptions and place a cheap diagnostic before costly implementation when needed. Do not repeatedly stop at a literature audit or a list of limitations once there is enough basis to propose a method; equally, do not fabricate a gap or promise an improvement when the evidence is insufficient. A testable engineering rationale can justify an exploratory prototype before a complete causal theory exists.

### Decide: buy information that matters

Compare actions by their ability to change the next decision, their relevance to the main question, and their cost. A derivation, code inspection, visualization of existing failures, or literature check can be better than a new run. Do not invent numerical information-gain or novelty scores without a defensible model.

Before a consequential experiment, state briefly:

1. The claim and strongest live rival.
2. Their different predictions and the intervention or comparison that separates them.
3. What each plausible outcome would change, including an inconclusive outcome.
4. The validity checks, affordable budget, and stopping rule.

If every plausible outcome leaves the intended decision unchanged, redesign or skip the experiment. A test may establish a useful performance or cost advantage while the full mechanism remains unresolved; state which claim it can support. Explicitly requested deliverables or replications can also have value independent of hypothesis selection; name that value. A broad benchmark is justified when the decision is about generalization, not merely because it is easy to launch.

Read [experiments.md](references/experiments.md) for causal controls, uncertainty, repeated runs, and loop recovery. The optional [ledger helper](scripts/research_ledger.py) reserves run identities, checks exact duplicates, and retains outcomes. Read [ledger.md](references/ledger.md) before using it. It does not judge scientific equivalence or execute experiments.

### Test, interpret, and update

Use existing baselines if their code, data, and evaluation remain comparable. Freeze the evaluation contract before comparisons; log justified changes and establish a new comparable baseline when it changes. Keep exploration separate from confirmation and protect a final holdout where applicable.

Preserve code/config/data/protocol provenance and raw evidence. Use isolated changes when useful; never reset unrelated user work to keep a winning run. Do not run a sweep merely because resources are idle.

Classify a result as **supported within scope**, **refuted within scope**, **inconclusive**, or **invalid**. A crash is not a negative scientific result; a noisy improvement is not a demonstrated mechanism. A successful fix to an invalid setup restores the ability to test the claim; it does not itself support the claim.

Update what is believed, which alternatives remain, and the next decision. Keep negative evidence and useful failed attempts. Preserve a parked idea with a reason and a concrete revival condition instead of deleting it or retrying it under a new name. Progress can be an eliminated explanation, a narrower claim, a discovered confound, or a reproducible positive result.

## Prevent drift without becoming rigid

Before a new branch or further tuning, name its connection to the main question and the unresolved issue it addresses. Local parameter search is appropriate when evidence identifies a parameter-sensitive bottleneck; otherwise reconsider the mechanism or representation.

Review a branch when additional work is unlikely to change a decision, a premise fails, evidence contradicts it, costs exceed its value, or an agreed checkpoint is reached. Do not require an arbitrary number of failures. Equally, do not abandon a promising idea just because its first implementation fails: distinguish engineering failure, inadequate measurement, low power, and a refuted prediction.

On encountering close prior work, identify which claim it covers and assess the remaining useful difference before switching directions. Revise the claim or method within the same question when warranted. Retire a redundant proposal when the prior solution already meets the relevant need under comparable conditions and no worthwhile difference is supported; do not infer that an entire field is exhausted. Do not manufacture a tiny unevaluated condition solely to preserve a novelty story.

When stuck, stop queued work that is owned by this task and no longer useful. Summarize what the branch taught, inspect a relevant outside mechanism, and choose among repairing the test, changing the hypothesis, changing the representation, parking the branch, or ending the investigation. Keep a small active frontier that fits the budget; extra candidates can remain parked. Tree search and multiple agents are optional execution techniques, not requirements.

For long work, refresh the state at meaningful decisions. Resume from it after interruption or context loss, reconcile any running jobs before relaunching, and inspect the ledger/history before creating a new run. Skill instructions alone do not create background execution or scheduled follow-ups.

## Finish with a research decision

Complete the authorized work when the requested question/deliverable is adequately addressed. Also stop a campaign when its budget is exhausted, evidence says the branch is no longer worthwhile, or a genuine dependency blocks progress. Report partial conclusions honestly; stopping an experiment campaign is not proof that the research question is solved.

Give the user a concise, inspectable account of:

- The current answer or best hypothesis and how it serves the original question.
- The strongest evidence, rival explanation, and remaining uncertainty.
- For method development: closest baselines, the supported or suspected remaining difficulty, proposed design, intended contribution, and comparison that would establish it.
- The relevant outside connection and its limits, when one informed the work.
- What changed, what was parked, and the best next action or reason to stop.
- Links to concrete artifacts and the resources used when material.

Provide decision rationale and evidence, not a transcript of private deliberation. Do not claim novelty from a failed search, success from a selected seed, or autonomous activity that has not occurred.
