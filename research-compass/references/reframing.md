# First principles, reframing, and structural transfer

Use when the problem formulation itself is uncertain, a surprising result resists explanation, or the user proposes a cross-domain analogy. The moves below adapt the user's Razor Reframing method (See → Strip → Reframe → Unfold → Select → Verify). They are thinking options, not a mandatory ceremony. Start with the move that can change the current decision.

## See and strip: distinguish fact from inherited story

Describe the observation and its conditions before explaining it. A surprising success can expose a false necessity just as a failure can expose a missing capability. Check whether the observation survives a simple measurement, protocol, or implementation audit.

Strip away incidental names—backbone, benchmark, architecture fashion, and historical implementation choice—while retaining the real task. Identify:

- **State and observables:** what exists, what is measured, and what remains latent.
- **Permitted interventions:** what can be changed, queried, stored, optimized, or supervised.
- **Constraints and invariances:** what must be conserved or treated as equivalent; what is causally or physically unavailable.
- **Sufficient output:** what the user or downstream decision actually needs, not everything the existing model happens to predict.

This is first-principles reasoning. It may reveal an impossibility, a redundant target, or a smaller sufficient representation without importing any outside theory. Do not strip away a hard requirement merely to make the problem solvable; changing sensors, target population, or success criterion is a scope proposal.

## Reframe: change a useful relation, not the vocabulary

Try a new problem description only if it produces a different prediction or design. Examples of moves are output → decision-sufficient statistic, state → process, absolute coordinate → relative constraint, unconditional computation → event-triggered computation, or generation → verification. These are prompts, not a recipe or claim of novelty.

For a cross-domain analogy, map *relations and causal roles*, not nouns. A compact mapping needs:

| Element | Question |
| --- | --- |
| Donor fact | What mechanism is actually supported by a traceable source, and under what conditions? |
| Recipient need | What consequential tension in the user's task calls for it? |
| Shared structure | Which variables, dependencies, constraints, and failure modes correspond? |
| Transfer assumption | What must be true in the recipient for the donor mechanism to work? |
| Break point | Which information, control, scale, or objective difference may invalidate it? |
| New consequence | What computation and observable prediction follow here that a plain analogy would not? |

Search donors by an abstract failure signature, not only common field terminology. An apparent match may fail because the donor assumes observations or interventions the recipient lacks. For instance, [ResNet](https://arxiv.org/abs/1512.03385) gives an identity path across aligned network layers; carrying old spatial observations forward additionally requires deciding *which* observation corresponds and *how* its coordinates align. The transferable question is about bypassing a demonstrated bottleneck, not adding a skip connection by name.

## Unfold, select, verify

Derive the smallest mechanism in a sketch, equation, or few steps. State where it should work, where it should not, and which existing result it explains. Prefer one assumption that yields several consequences to several modules with unrelated justifications. Compare against a null or ordinary explanation: extra compute, data, regularization, changed timing, preprocessing, or evaluation.

For a theory-inspired method, use a **theory-destroying control**: keep incidental effects (inputs, budget, effective hyperparameters, smoothing, or schedule) while removing the claimed principle. The [ChordEdit original and reproduction](paper-patterns.md) illustrate why a useful algorithm and its proposed explanation must be evaluated separately. A theory is a design tool, not proof that its named mechanism caused the gain.

Choose the most useful surviving candidate by relevance, assumption burden, testability, prior overlap, and cost—not elegance alone. A first probe may be a derivation, counterexample, toy case, visualization, code audit, or experiment. A toy success supports only its own conditions. Stop a reframing pass when it yields a discriminating action, a sufficiently supported answer, or a precise dependency; do not turn analogies into an endless idea list.

For method positioning after a useful reframe, continue with [contribution design](contribution-design.md). For an actual test plan, use [experiments](experiments.md).
