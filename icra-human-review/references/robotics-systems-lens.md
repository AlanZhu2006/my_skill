# Empirical robotics and navigation lens

Use this lens to judge contribution and evidence, not to demand every listed experiment.

## Contribution test

Identify which contribution type the paper actually makes:

- new capability or problem formulation;
- new technical mechanism;
- new interface or systems principle;
- new empirical finding;
- use-inspired integration whose design and evidence teach a reusable lesson.

Existing components do not automatically make a contribution unoriginal. Ask whether the integration exposes a new constraint, interface, causal comparison, or capability that the components alone do not establish.

## Nearest-alternative test

Find the simplest alternative that could explain the headline gain. Common alternatives include raw retrieval, privileged role labels, more compute, longer action budget, a stronger controller, ground-truth pose/depth, easier query construction, or a changed success criterion.

Require one fair comparison that separates the proposed contribution from that alternative. Do not ask for many unrelated planners or datasets when they cannot answer that question.

## Protocol test

Check only protocol details that can change interpretation:

- causal versus expert or future history;
- paired populations and denominators;
- hidden versus supplied role labels;
- sensor and oracle inputs;
- success and stopping definitions;
- compute/action-budget parity;
- scene and episode independence;
- deployment-time fallback or intervention behavior.

Infrastructure receipts, hashes, and job identifiers belong in artifacts unless they are needed to establish fairness.

## Evidence test

Prefer closed-loop paired evidence for control claims. Distinguish:

- deployable method result;
- mechanism or oracle upper bound;
- offline diagnostic;
- pilot or anecdotal result;
- controlled survey that is not an end-to-end rollout.

Do not let a strong offline metric substitute for task success. Do not dismiss a clean, paired internal benchmark solely because no public benchmark has an identical contract.

## System-paper proportionality

- No real-robot experiment is a limitation, not an automatic rejection.
- A training-free or frozen-component system can be publishable if the interface principle and causal evidence are new and useful.
- Component count is not itself a weakness. Unclear necessity, hidden privilege, latency, or lack of ablation may be.
- A simple method need not beat every state of the art method if it demonstrates a distinct useful tradeoff.
- Long-range, lifelong, safety, or universality claims require matching evidence only when the paper actually makes those claims.
