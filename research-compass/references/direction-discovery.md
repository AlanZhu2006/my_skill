# Direction discovery: from observation to a research move

Use when the user seeks a question worth pursuing or a direction built on existing work. The output is a causal candidate with a decision-relevant test, not an architecture assembled from attractive components. Start from whichever evidence the user has; the routes below are alternatives, not stages to complete.

## Enter through evidence, not fashion

- **Phenomenon-first:** A method fails, succeeds unexpectedly, or exhibits a tradeoff. Separate the observation from the proposed explanation; check the measurement and an ordinary rival before designing around it.
- **Baseline-first:** Trace its inputs → representation/state → interactions → predictions → downstream use. Identify the capability it genuinely earns and the assumption, information path, target, or cost that becomes consequential in the intended setting. An absent module is not yet a bottleneck.
- **Paper-first:** For a strong recent work, inspect a predecessor, the changed computation or task contract, its decisive ablation, and its failure boundary. Infer the *research move*; do not claim to know the authors' private reasoning or equate impact with stars. See the optional [dated casebook](paper-patterns.md) for examples, then verify current primary sources.
- **Structure-first:** Describe the recipient problem without its field's labels. Search other fields for the same relation, optimization burden, information constraint, or failure mode. Read [reframing](reframing.md) to distinguish first-principles derivation from a valid structural analogy.

Define the recipient task before selecting an appealing donor. Ask what the output is used for, which inputs and priors are permitted, what errors matter, and what resources are scarce. A useful result in an easier input regime is not a solution to the original contract.

## Climb and descend the abstraction ladder

1. **Observable tension:** What happened, under what conditions, and with what provenance? A source's claim, an ablation, local replication, a formal implication, and an untested suspicion have different force. “Not evaluated” means unknown, not failed.
2. **Structural bottleneck:** Strip away dataset and module names. Specify the essential variables or entities, available observations and interventions, invariances or equivalences, temporal or spatial dependencies, and what is identifiable. Find the smallest assumption that could explain the tension. Distinguish necessities from conventions inherited from a benchmark or architecture.
3. **Generative move:** Change only what the bottleneck requires. Plausible moves include removing an unnecessary prediction burden, choosing sufficient variables, routing information by role or lifetime, changing the training signal, allocating computation where it has value, or transferring a mapped principle from another field. These are lenses, not an innovation checklist. A direct repair is acceptable when it is the best supported move.
4. **Instantiated mechanism:** State the concrete new computation, its location in the baseline, the preserved capability, expected cost, and a condition where it should fail. A conceptual slogan without a changed data flow is not a method.
5. **Differentiating consequence:** Give a prediction the closest prior solution or strongest simple repair would not make. If the candidate only renames a loss, increases capacity, or shifts a hidden hyperparameter, narrow the claim accordingly.

Move back down the ladder when the abstraction loses a real constraint. Move up when several proposed modules share the same unexamined premise. Do not require a theory before a cheap exploratory prototype, but do not present the prototype's gain as proof of that theory.

## Stress the direction before investing

Search the recipient and donor literatures by structural fingerprint: failure, variables, required relation or output, input privileges, and intervention. Compare the closest mechanism under comparable conditions. A close match can supply a baseline and narrow novelty; its existence alone does not make a useful question worthless. An unavailable paper or code path limits what can be claimed.

Give the candidate a serious null explanation: stronger data, compute, initialization, preprocessing, schedule, metric, post-processing, or a small baseline change. For a mathematical or analogical design, hold its incidental effects fixed and remove the proposed principle. Ask what observation would make you choose a different mechanism. If no affordable outcome changes the decision, postpone the test or revise the candidate.

Select for consequential need, fit to the evidence, explanatory economy, implementability, and cost of decisive evidence—not maximum novelty distance or a fixed numerical score. A candidate can be an algorithm, representation, measurement method, supported simplification, or carefully bounded negative result. If evidence is too thin for a method, identify the cheapest premise check and stop there.

## Communicate a decision, not a form

A compact proposal should let the reader recover: the task and baseline advantage; tension and its evidence status; the causal assumption; changed computation; nearest paper and simple rival; predicted benefit/cost/boundary; and the test whose outcomes lead to continue, revise, or stop. Use prose, a sketch, or a short card as appropriate. One developed direction is better than several variations of the same untested premise.
