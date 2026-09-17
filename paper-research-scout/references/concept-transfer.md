# Route B: turn a viewpoint into a new question

The Research Compass / Razor Reframing lineage contributes six moves: See, Strip, Reframe, Unfold, Select, Verify. Apply them to the paper's mechanism and then to a concrete recipient problem. Use only the detail that changes the decision.

## Extract what is portable

Describe the observation without its architecture name. Distinguish the paper's actual finding from its explanation and from your extrapolation. Ask which part would remain meaningful if the backbone, benchmark, parameter count and domain vocabulary disappeared.

Possible portable structures include an equivalence relation, a sufficient statistic, a feedback loop, a conservation rule, an identifiability limit, a conditional independence, a verification mechanism, or a way of allocating scarce observations. These are prompts for intuition, not mandatory theoretical labels.

A good viewpoint compresses several design choices and makes new consequences follow. An analogy that only renames an old loss has not yet earned research value.

## Map both domains explicitly

| Mapping element | Question |
| --- | --- |
| Donor fact | What observation or mechanism is actually supported, and where? |
| Recipient need | What concrete unresolved problem would benefit, and why is it relevant to this user? |
| Entities and relations | What corresponds to what? What counts as the same state/object/outcome? |
| Information and intervention | What can each domain observe, control, or verify? |
| Transfer assumption | Which condition makes the imported mechanism work? |
| Break point | What important difference could invalidate the transfer? |
| Consequence | What prediction or simplification follows that the existing approach would not give? |

Choose the recipient from a scientific need in the user's requested scope. A nearby personal project is not the default recipient. Use a mapping failure to discard or revise the idea. Do not decorate a proposal with every neighboring theory. A cross-domain move needs no donor checkpoint if its premise can be tested independently, but its proposed test vehicle must still be concrete.

## Develop competing explanations

Give the candidate its strongest simple rival: an established formulation, ordinary regularization, more compute, a useful bias, or a measurement effect. Derive an outcome on which the two disagree. If no outcome can separate them, the conceptual distinction may be cosmetic or the test may be inadequate.

The first probe can be a proof obligation, synthetic counterexample, controlled toy system, or reanalysis of existing data. Explain what it establishes and what it cannot establish. A toy success does not imply real-world scalability or validate the donor's reported performance.

## Check the recipient literature

Search the structural fingerprint in both domains: phenomenon, entities, required relation/output, assumptions and intervention. Include common synonyms, classical methods, negative results, and recent equivalents. Inspect primary sources for the closest candidates instead of relying on titles or an embedding similarity score.

For the nearest prior work, state what is shared and the specific change in mechanism, assumptions, capability or evidence. A new application may be valuable, but name its contribution accurately. An older paper can invalidate a supposed conceptual novelty even if today's donor paper is new.

Preserve a dated hypothesis before targeted equivalence search to track idea provenance; do not delay basic familiarization. If an equivalent exists, revise the question around an actually unresolved boundary, explanation or capability, or park it. Report search limits rather than “nobody has done this.”

## Avoid idea assembly by title

Hypothetical example: a paper finds that a representation is invariant to viewpoint. The leap “use it for camera localization” is incomplete. Does it retain distinctions needed to identify camera pose, or erase the very variable being estimated? Paired scenes and controlled camera changes can test that question before designing a new localization system.

The transferable insight may be the **test for sufficiency**, rather than the representation itself. This distinction often yields a smaller, more general research question. It remains a hypothesis until both domain assumptions and nearby prior work are checked.

## Stop at a discriminating next action

Keep enough alternatives to prevent fixation, but do not manufacture a list of ten ideas. Prefer a small set with genuinely different mechanisms and tractable tests. Park an interesting idea when its mapping has a known break or an unavailable dependency; record the new evidence that would make it worth reopening.
