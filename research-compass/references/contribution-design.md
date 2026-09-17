# Build a contribution from existing work

Use this when close prior work appears, when judging whether a direction is
worth pursuing, or when the user wants a new method. The unit of contribution
is the specific improvement or finding under stated conditions, not whether
an entire research area is untouched.

## Locate the frontier of the closest methods

Compare the relevant primary papers and implementations at the level needed
for the decision. A short comparison can record:

| Method | What it already solves | Assumptions / information / cost | Remaining limitation and evidence | What we can reuse or compare |
| --- | --- | --- | --- | --- |

Separate overlap in the topic, problem, mechanism and demonstrated capability.
Two papers about uncertainty in reconstruction do not establish that every
uncertainty-aware reconstruction method is equivalent. Conversely, different
terminology does not make the same computation new. Cite the closest work and
credit inherited parts explicitly.

Evidence of a remaining difficulty may be a reproducible failure, a documented
assumption that excludes an important setting, a measured resource tradeoff,
or a plausible concern needing a probe. Label these differently. “They did not
evaluate dataset X” establishes unknown coverage, not failure on X. Explain why
the setting matters and what makes existing methods insufficient before
presenting it as an opportunity.

Close work may increase the direction's feasibility by providing code, a
benchmark, or evidence that the problem matters. Do not use paper count, a
famous competitor, or a familiar ingredient as a novelty veto. It is enough
to locate a meaningful contribution relative to the nearest solutions;
an exhaustive proof of worldwide originality is unavailable and unnecessary
for a bounded exploratory investigation.

## Decide what useful difference is still possible

Potential contributions include a better algorithm for an established problem,
relaxing a consequential assumption, handling a recurring failure, a meaningful
quality/cost tradeoff, improved robustness or data efficiency, a justified
simplification, or making a previously inaccessible capability practical.
These are possibilities, not a checklist to fill.

Known components can form a new method when their selection, coupling or use
resolves a concrete obstacle. State what is inherited and what changes. A
small change can matter greatly; an elaborate architecture can add little.
Judge the size, reliability and relevance of the effect under fair comparison,
without requiring a new theory for every useful algorithmic improvement.

For an application transfer, explain the obstacle that makes direct reuse
inadequate and how the adaptation addresses it. Merely renaming a known method
or moving it to another dataset does not establish a method contribution.
A diagnostic or empirical study may be valuable in its own right, but when the
user requests a new method, use that diagnosis to guide a design whenever the
evidence permits.

Keep discovery of a good paper separate from finding a good baseline to extend.
A relatively mature paper with accessible code and a clear remaining bottleneck
can be an excellent research starting point. It need not be the most original
paper in today's reading list.

## Construct a method, with uncertainty visible

Develop a short chain in the current notes, using only the detail needed:

1. **Need and baseline:** what the user wants, and what the strongest relevant
   existing method achieves under the intended conditions.
2. **Remaining difficulty:** the failure, assumption or cost worth addressing;
   evidence for it and the best ordinary explanation.
3. **Design hypothesis:** the change in computation, objective, representation,
   information use or scheduling that could address the difficulty. Give enough
   inputs, outputs and steps for a sketch or pseudocode, plus expected overhead
   and a condition where it may fail.
4. **Claimed difference:** what is reused, what is proposed, and the improvement
   or capability being sought. Keep new-method and first-ever claims separate.
5. **Deciding comparison:** nearest method, simple fix, and a matched test or
   ablation that would justify the design. Distinguish an immediate premise
   check from the later evaluation needed to establish practical value.

An empirically motivated design can be worth a small prototype while its causal
explanation remains uncertain. Stage the investment instead of demanding that
every assumption be proven before proposing anything. When diagnosis is needed,
say which design decision its outcome changes; avoid endless diagnostics that
never lead back to the requested method.

## Respond proportionately to overlap

- **Shared area or problem:** continue with the strongest relevant methods as
  comparators. Reassess the proposed advantage, not the existence of the field.
- **Similar mechanism, different important assumptions or capability:** inspect
  whether that difference is real; retain or revise the method around a supported
  remaining difficulty. Treat untested conditions as hypotheses.
- **The initial method is already known, but the need remains unmet:** drop the
  first-ever claim, reuse the method as a baseline, and investigate the cause of
  the remaining limitation. A different solution within the same direction may
  still be worthwhile.
- **The same solution already meets the same need at comparable cost:** credit
  it and retire the redundant proposal unless another worthwhile difference has
  evidence. Reproduction can still be useful if requested, labeled accurately.
- **Evidence is insufficient:** identify the closest source or inexpensive
  comparison that would resolve the uncertainty; neither declare the direction
  dead nor invent a gap to rescue it.

Prefer a local revision of method or claim when the main question remains
valuable. Consider a different direction when the need is already met, expected
benefit is too small, the premise fails, or the cost is unjustified. There is no
required number of rescue attempts and no novelty quota.

## Hypothetical example

Suppose two open methods already select keyframes using geometric uncertainty.
An initial proposal to “add uncertainty-aware keyframes” is underspecified and
may overlap both. Inspect how they estimate uncertainty, choose frames and
handle the intended motion and resource constraints.

If evidence shows their fixed selection rule misses brief useful observations
under a realistic latency budget, a scheduling change could be a worthwhile
method. Explain why it addresses that failure and compare against both methods
and a simple threshold adjustment under the same budget. The uncertainty
principle can be inherited; the proposed contribution is the effective selection
rule and its supported advantage. If either baseline already handles that case,
or the threshold adjustment removes the alleged problem, revise or retire that
specific proposal. The existence of the two papers alone establishes neither
the gap nor a reason to abandon navigation or reconstruction.
