# Design and position a research contribution

Use when a consequential difficulty has been identified and the user wants a method, explanation, or publishable contribution. If the difficulty is only suspected, first use [direction discovery](direction-discovery.md) to identify an outcome-branching premise check. Do not require a conceptual revolution when a precise improvement addresses the real need.

## Establish the frontier, not an empty patch of literature

Identify the closest *working* solutions, not merely the most cited papers. Compare them under the intended task contract: inputs and privileged data, outputs and success criterion, mechanism, operating conditions, quality, cost, and evidence. Read primary papers and the implementation path when code behavior matters. Distinguish four kinds of overlap: same area, same problem, same mechanism, and same demonstrated capability. Similar vocabulary is not equivalence; different vocabulary is not novelty.

Write what the closest solution already does well before claiming a gap. A gap can be a reproducible failure, consequential excluded assumption, measured quality–cost tradeoff, or an important capability that remains unavailable under comparable conditions. Mark an untested condition as a hypothesis, not a failure. A close paper can make a direction *more* viable by providing a baseline, data, or mechanism to reuse; it only invalidates the claim it actually covers.

## Turn the difficulty into a computation

The method should answer: **What changes, why should that change matter, and what else could explain the same result?** Give enough detail to implement or challenge it:

- Existing path to preserve: inputs, intermediate representation or state, outputs, and the baseline's earned advantage.
- Changed path: what is computed, selected, stored, communicated, learned, or optimized differently; where and when it happens.
- Causal link: which documented burden the change removes or which missing capability it supplies.
- Predicted tradeoff: added compute/data/latency or a new failure boundary.
- Distinguishing evidence: closest method, strongest minimal repair, and an outcome on which they disagree.

For an architecture, show the data flow and relevant variables or interfaces rather than just module names. For a mathematical method, state the objective and assumptions; test whether a simpler update with matched effective settings explains the gain. For an empirical finding or diagnostic tool, specify which decision it changes. Familiar ingredients can be a valid contribution when their coupling yields a consequential, supported difference; merely combining them is not evidence of one.

Separate the **design hypothesis** (“this change may solve the burden”) from the **mechanism claim** (“it works for this reason”), **performance claim** (“it improves this outcome under these conditions”), and **priority claim** (“we are first”). Different evidence supports each. An exploratory prototype can justify further work without proving causality or generalization.

## Compare fairly and respond to overlap

Test against the nearest published mechanism and a strong simple alternative: retuning, longer training, more context, ordinary post-processing, or an existing backend, as appropriate. Match input privileges, data, compute, selection, and evaluation where they could explain the advantage. A new method may legitimately trade one resource for another; report that frontier rather than only a headline score.

If prior work already uses the proposed mechanism, credit it and locate a real difference in assumptions, coupling, cost, evidence, or capability. If the same solution meets the same need under comparable conditions, retire the redundant proposal or label a requested reproduction accurately. Do not manufacture a tiny untested condition to rescue novelty, but do not abandon a useful research question merely because its first design is known.

When the user's goal is a new method and evidence is sufficient, produce a plausible implementable sketch and its decisive comparison rather than ending with a literature audit. When the decisive premise is unresolved, name the cheapest probe and explain how each outcome would change the design. A failed first implementation may reflect engineering, measurement, or low power rather than a false research premise; a valid, informative contradiction should revise the claim.

The final contribution statement should be narrow enough to defend: “Under [task and conditions], [closest approach] faces [supported difficulty]; [specific changed computation] yields [targeted capability or tradeoff], as distinguished from [simple rival] by [comparison].” This is a compression test, not required wording.
