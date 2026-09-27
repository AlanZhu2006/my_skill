---
name: research-compass
description: Turn an open research question or baseline into a testable direction and next decision using first-principles analysis, structural transfer, close prior work, and discriminating evidence. Use for scientific ideation, method design, mechanism diagnosis, or a continuing experiment campaign; not for a simple factual lookup or routine paper summary.
---

# Research Compass

Advance the user's research question, not a quota of ideas, papers, or runs. Seek a consequential, defensible contribution under the actual task and resource constraints. An explanation, simplification, negative finding, or method can be progress; unfamiliar components are not required. Respond in the user's language.

## Choose the work that changes the next decision

| Current need | Read only the relevant guidance |
| --- | --- |
| Find or assess a direction from a phenomenon, baseline, paper, or practical need | [Direction discovery](references/direction-discovery.md). For first-principles reframing or cross-domain analogy, also read [reframing](references/reframing.md). The dated [paper casebook](references/paper-patterns.md) is optional illustration, never a default target or substitute for current sources. |
| Turn a promising tension into an implementable and positioned contribution | [Contribution design](references/contribution-design.md); use direction discovery first only if the tension remains unclear. |
| Decide, run, interpret, or stop an experiment campaign | [Experiments](references/experiments.md). Use the optional [ledger](scripts/research_ledger.py) only when repeated runs need tracking and no suitable tracker exists; read its [guide](references/ledger.md) first. |

Do not run every mode. For a one-off discussion, an answer can be the complete artifact. For sustained work, adapt the [state template](assets/research-state.md) or existing project notes; do not create parallel paperwork.

## Hold the question steady; let the explanation change

Keep distinct: **question** (the desired understanding or capability), **claim** (the current explanation or proposed mechanism), **evidence** (what is actually observed and under which conditions), and **decision** (what to do next). When exploring a new topic, do not inherit a previous project's target simply because its notes are nearby. When continuing a project, read its relevant results, code, constraints, and pending work before proposing more.

Recover the task contract: who needs the result, available inputs and priors, required outputs, operating conditions, success criterion, and budget. Preserve the baseline's demonstrated advantage before changing it. Replacing the task, population, input privileges, or success criterion is a scope proposal requiring the user's direction, not an unannounced improvement.

Begin from a meaningful tension, not an absent module: a surprising result, failure, avoidable cost, incompatible assumption, missing information, or mismatch between the output and its use. Label its status as **local observation**, **source report**, **deduction from an explicit assumption**, or **untested hypothesis**. Missing evaluation is unknown coverage, not measured failure.

Abstract the tension to its causal structure—what variables, constraints, information paths, timescales, or objectives matter—before borrowing a named solution. First principles may yield a method without any analogy. A cross-domain analogy is useful only when the mapped relations, transfer condition, and likely break point are explicit. Do not force a conceptual reframe when a concrete bottleneck and a direct fix are already justified.

Make the intervention inspectable: what computation, representation, supervision, selection, or optimization changes; where it enters the existing system; what it should improve; what it costs; and when it should fail. Compare with the closest published mechanism and the strongest simple alternative. A theory-inspired design also needs a control that preserves incidental effects, such as compute or hyperparameter changes, while removing the claimed mechanism.

## Let evidence decide the claim

Use primary sources for paper claims and inspect implementation versions when code behavior matters. Separate author interpretation, reported ablation, inspected code, and local reproduction. Search for equivalent *mechanisms and conditions*, not merely similar titles. Popularity or a company name can prioritize reading, but neither establishes quality, originality, or transferability. State the search boundary instead of claiming exhaustive novelty.

Before spending on a consequential test, name the live claim, strongest rival, their differing predictions, validity checks, affordable cost, and what each plausible outcome would change. The cheapest decisive action may be a derivation, counterexample, source or code inspection, existing-result analysis, or controlled experiment. Do not run a benchmark or another seed when its outcomes cannot alter the decision.

Distinguish execution validity, comparison validity, and support for a claim. Retain negative and inconclusive evidence. Continue, revise, park, or stop when the evidence and budget warrant it; neither one broken run nor one close paper automatically ends a worthwhile question.

## Finish with the decision

Lead with the answer or best-supported direction at the user's requested depth. Make clear the need and baseline, consequential tension and evidence status, proposed mechanism or explanation, nearest rival and simple fix, decisive comparison, and boundary of the claim. Give one developed direction when that is what the evidence supports; do not manufacture a fixed number. If the premise is unresolved, say exactly which observation would choose between designs. Never claim novelty from an incomplete search or success from an unrun test.
