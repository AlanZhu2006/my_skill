# Route A: baseline opportunities and reproducibility

## Find a question before a patch

A useful baseline is both a working platform and a set of claims to investigate. Read the computation and evaluation that actually produce the claimed behavior. A repository's visibility or age is not evidence that it fits the research question.

High-value openings often arise when:

- A claimed mechanism and an equally plausible simpler explanation predict different behavior under a controlled intervention.
- An expensive intermediate output may contain more information than the downstream decision needs.
- An assumed invariance, observability condition, distribution, or timing model breaks in an important regime.
- A component is useful only under a boundary condition that has not been isolated.
- A speed, quality, or robustness improvement shifts a system bottleneck instead of removing it.
- A surprising success suggests a representation that could simplify or unify an existing pipeline.

Do not turn limitations sections into an unfiltered wishlist. Pick the assumption whose resolution would change a meaningful decision and whose test is affordable. Pure hyperparameter tuning can be useful optimization but needs a reason to count as a research direction.

## Audit the resource bundle for the proposed action

Use a compact evidence table. For each resource record the exact link/file/version, what was inspected, what remains unknown, and whether the gap blocks this action.

| Resource | Evidence to inspect | Frequent mismatch |
| --- | --- | --- |
| Official source | Paper/project-to-repository link; substantive files and the relevant inference/training/evaluation entrypoint | A website branch, empty release, or unrelated namesake repository |
| Checkpoint | Model card and actual file listing; variant, architecture/config, preprocessing and loader | Foundation weights presented as the paper's fine-tuned model; teacher weights used as the released student |
| Data/environment | Accessible version/split, preparation path, simulator/assets or observation/action schema | A public simulator mistaken for released task data or counterfactual labels |
| Evaluation | Metric implementation, units, alignment, sampling and dataset split | A demo script mistaken for a comparable benchmark |
| Intervention access | The specific component can be modified and its effect isolated | Inference-only release used to promise a training-loss experiment |
| Compute/environment | Supported stack, documented device/memory/runtime and known local resources | Published inference FPS extrapolated into a fine-tuning cost estimate |
| Usage conditions | Code, weights and data licenses/access gates separately | Public metadata treated as accessible/downloaded files or unrestricted reuse |

Inspect enough to support the recommended action, not every file in the repository. Follow author links to model hubs/releases; inspect listings and the loader before claiming a usable checkpoint. Do not download large model files just to check existence. Gated/private/dead resources remain blockers unless access is actually known. Never imply license acceptance or credentials have been obtained.

A model can support one action and block another:

| Intended action | What must be available |
| --- | --- |
| Analyze existing outputs | Raw outputs, protocol and suitable measurements; no model weights necessarily needed |
| Inference diagnostic | Compatible runnable inference code, correct weights and sample input/evaluation |
| Fine-tuning intervention | Training path, trainable weights/config, compatible data and affordable compute |
| Distillation intervention | Teacher/student access, training objective/data pipeline and suitable comparisons |
| Full paper reproduction | The relevant complete protocol and resources, followed by an actual reproduced result |

## Describe readiness without overstating it

Use plain labels with explicit scope:

- **Locally validated for this action:** a relevant smoke test or stronger run succeeded; say exactly what ran. A loader test is not a reproduced paper.
- **Artifacts verified; not run:** inspectable code, compatible weights and other necessary artifacts have been located; environment/runtime remain untested.
- **Conditional:** plausible path with named unverified assumptions or access/resource gaps.
- **Blocked:** a required artifact or feasible execution path is missing; record a revival condition.

Conceptual value is a separate paragraph. Do not let a stronger novelty story upgrade a readiness label. “Code/model will be released” is a promise; “not found in this search” is bounded uncertainty, not proof no implementation exists.

## Design a meaningful extension

State the baseline, operating regime, suspected mechanism, intervention, rival prediction, comparison and decision rule. Control data, compute, preprocessing, selection and evaluation when they could explain the change. Tie a proposed edit to a verified file/function when possible; otherwise label the location as an implementation task, not an inspected fact.

Choose a cheap discriminating probe before broad training. A failure-case visualization, controlled perturbation, invariant check, matched-compute control or analysis of existing predictions may settle the key issue. If a needed training bundle is unavailable, see whether an inference diagnostic or an explicitly different open baseline can test a narrower claim.

Do not silently replace the baseline, dataset or target claim to bypass a blocker. An alternate baseline is a proposed test vehicle with its own assumptions. It does not establish reproduction of the unavailable system.
