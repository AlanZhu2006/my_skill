# Experiments that change decisions

## Before running

Use the shortest experiment card that makes the action assessable. This may be a paragraph in the current notes rather than a new file:

- **Question and scope:** link to the main question; state the population or operating regime.
- **Claim and rival:** predictions that differ under a specific intervention.
- **Evidence needed:** measurement, comparison, units, and effect size or qualitative pattern that matters.
- **Decision table:** what support, refutation, ambiguity, or invalidity would cause next.
- **Validity:** plausible confounds and the control or check that addresses each material one.
- **Provenance and budget:** code plus dirty changes, data/split, protocol, configuration, seed/randomness, cost cap, and abort condition.

If a threshold cannot yet be justified, use an exploratory pilot to characterize scale and variance. Label it exploratory; do not choose a threshold after seeing the outcome and present it as confirmatory.

## Match the test to the uncertainty

| Uncertainty | Often useful | Common trap |
| --- | --- | --- |
| Is the implementation valid? | Tiny known-answer case, unit/convention check, controlled input | Treating failed execution as a failed scientific idea |
| Does the proposed mechanism explain a gain? | Matched control, ablation, intervention, simpler rival | Reporting only the final benchmark score |
| Is the effect stable? | Paired comparisons, independent units, planned replications | Treating correlated frames or repeated seeds as independent evidence |
| Does it generalize? | Held-out conditions, boundary tests, representative workloads | Repeated tuning against the final test set |
| Is the formulation possible? | Identifiability argument, counterexample, idealized limit | Adding capacity to recover absent information |
| Is there already a solution? | Targeted paper/code inspection and compatible baseline | Implementing from a title or borrowing an incompatible result |

Control compute, preprocessing, data access, selection, and evaluation where they could explain the claimed difference. Do not demand every possible control for a small exploratory question. Report effect sizes and uncertainty at the right unit; a negative result only weakens a claim when the test could have detected its predicted effect.

Freeze a comparable evaluation contract. If the contract is flawed, fix it, version it, and reassess affected results. A better metric may be necessary, but switching metrics does not preserve old comparisons automatically.

## Repetition must have a purpose

First inspect existing runs, artifacts, pending jobs, and the scientific question they answered. Renaming a hypothesis, changing a seed, or adjusting a nearby parameter does not by itself create new information. Exact execution fingerprints help; semantic repetition still requires judgment.

Legitimate repeats include:

- **Statistical replication:** specified sampling units, uncertainty target or sample size, and a stopping/analysis rule. Use independent randomness when independence is required.
- **Technical reproducibility:** explicitly test deterministic replay, nondeterministic hardware, or environment effects; same-seed replay is not a new independent sample by default.
- **Repair of an invalid run:** identified cause, concrete correction, and evidence that the correction restores a valid test.
- **Changed conditions:** an explicit boundary/generalization hypothesis, with the changed variable and expected informative contrast.

Record which prior run is being revisited and why. Avoid optional stopping until a favorable seed appears. For sequential work, use a justified sequential analysis or label conclusions exploratory and confirm on fresh evidence.

## Interpret without erasing inconvenient evidence

Separate **execution validity**, **comparison validity**, and **the claim's evidential status**. A run marked `valid` may have executed correctly while its comparison changes several confounded factors; neither establishes a mechanism. Classify the declared test/claim, record the affected comparison, and retain usable raw observations. Different claims from the same run can have different evidential status.

| Outcome | Meaning | Next decision |
| --- | --- | --- |
| Supported within scope | The valid observation favors the claim over the tested rival | Test a boundary, strengthen confirmation, or finish the requested claim |
| Refuted within scope | A valid, sufficiently informative observation contradicts a prediction | Revise or park the claim; retain the counterevidence |
| Inconclusive | The test is valid but cannot separate the live explanations | Improve measurement/design only if its expected value justifies the cost |
| Invalid | Setup, data, execution, or evaluation prevents interpretation | Repair if worthwhile; exclude it from scientific effect estimates |

Record artifacts, effect/uncertainty where meaningful, surprises, belief changes, and the resulting action. Missing measurements are `null`, never fabricated zero scores. Keep negative and invalid records alongside successful ones.

## Recover from a loop

At a plateau, write the common lesson of recent runs in one or two sentences. Distinguish selecting a lucky best score from establishing a repeatable, practically useful advantage. The latter can support a method contribution while its complete causal explanation remains open. If the remaining task is legitimately optimization, bound it with a target and budget; otherwise inspect the live assumption that all variants share.

Useful recovery paths:

1. **Test repair:** a confound, invalid measurement, or low power prevented a fair test.
2. **Mechanism revision:** the shared causal explanation was wrong or incomplete.
3. **Representation revision:** the chosen variables hide the structure or required equivalences.
4. **External transfer:** another field has a mechanism that handles the same structural obstacle; check its assumptions locally.
5. **Scope proposal:** the original question may need renegotiation; distinguish this from an implementation change.
6. **Stop or park:** no affordable action is likely to change the decision now.

Do not run all six. Choose the path the evidence supports. A parked branch needs a revival condition such as new observations, removal of a specific confound, or access to a necessary dataset. “Try again later” is not a condition.

## Short hypothetical cases

**Eight near-identical tuning runs.** Review what they jointly establish before proposing a ninth. A targeted parameter probe is reasonable if a parameter-sensitive bottleneck is supported. Otherwise inspect a shared assumption and a relevant outside formulation. Running a fresh seed solely to seek a higher score adds selection bias.

**A striking gain after a new module.** The same change also doubled compute and altered preprocessing. The next useful comparison isolates those changes. Keep the result as a lead; do not yet credit the module's theoretical mechanism.

**An impossible inference regime.** If inputs do not identify the desired variable, a more powerful model may substitute a prior. Establish the ambiguity and its operational consequences before redesigning the estimator. A proposed new sensor or revised output may require a scope decision.

**Three negative seeds with wide uncertainty.** They may be insufficient to refute the predicted effect. Decide whether a powered replication would affect investment; otherwise report inconclusive and stop within budget. A fixed failure count is not a scientific stopping rule.
