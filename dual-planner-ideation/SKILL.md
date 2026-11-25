---
name: dual-planner-ideation
description: Run a dialectical Lead Planner + Co-Planner peer-review loop for research ideation, major architecture redesigns, statistical diagnosis, and high-stakes experiment planning. Grounds bold ideas against real code, data, and metrics via an adversarial Co-Planner audit while preventing defensive incrementalism from killing ambitious hypotheses through 3-class triage ([HARD-FACT], [FIXABLE-SPEC], [UNVERIFIED-RISK]), Minimal Viable Variants (MVVs), and transparent overrule rules. Use for research ideation, method design, paper-level diagnosis, or major system plans; not for routine Q&A or small edits.
---

# Dual-Planner Ideation & Dialectical Review

Balance two symmetric failure modes of AI-assisted research planning:

1. **Armchair Over-Synthesis ("纸上谈兵")**: a Lead Planner alone invents grand multi-module stacks, extrapolates statistics with hidden selection bias, or assumes ground-truth labels and metric definitions that do not exist in the codebase.
2. **Defensive Incrementalism ("防守型打压")**: an adversarial Co-Planner reflexively issues blanket `KILL` verdicts whenever a bold idea is unproven yet or has draft-spec bugs, pulling the entire roadmap back into safe `+1 pp` local minima.

This skill defines an asymmetric **Lead Planner ↔ Co-Planner** workflow that verifies every premise against reality while preserving genuine research ambition.

## Trigger Scope

- **Use** for: novel research ideation, method/architecture redesigns, root-cause diagnosis of stubborn performance ceilings, paper-level statistical claims, and multi-day GPU experiment plans.
- **Skip** for: quick factual questions, single-file edits, routine debugging, or lightweight discussions where external review adds latency without changing decisions.

## Role Asymmetry

| Role | Primary Ownership | Authority Boundary |
| --- | --- | --- |
| **Lead Planner (主 Planner)** | Problem reframing, first-principles synthesis, novel mechanisms, simplicity/elegance, final triage & ruling. | Must verify core premises before proposing; **must accept** verified `[HARD-FACT]` corrections unconditionally; **retains final ruling authority** over `[UNVERIFIED-RISK]` tradeoffs. |
| **Co-Planner (副 Planner)** | Independent code/data/math/metric audit, bug & fallacy hunting, feasibility checks, minimal-falsification design. | Has **binding veto only on `[HARD-FACT]`** contradictions backed by concrete evidence (file:line, derivation, or recomputed numbers); **cannot kill** an ambitious hypothesis merely because it is unproven yet. |

## Three-Step Bounded Workflow

### Step 1 — Grounded Lead Draft
Before invoking the Co-Planner, inspect the essential codebase/data/metric files and formulate a crisp proposal containing:
1. **Core Tension & Thesis**: the exact failure mode or ceiling being attacked (separating observed facts from hypotheses).
2. **Proposed Mechanism**: the minimal conceptual change — explicitly separating the **core insight** from **draft engineering details**.
3. **Explicit Assumptions**: every assumption about data labels, metric definitions, compute/I/O, and evaluation protocol compliance.
4. **Proposed Cheap Verification**: what 1-day probe or single-variable experiment would falsify the thesis.

### Step 2 — Constructive Adversarial Co-Planner Audit
Invoke the Co-Planner (e.g., local Codex `gpt-6.2-astra` at `max` for research ideation/statistical audits, or `high`/`xhigh` for engineering architectures) using [`references/co-planner-prompt-template.md`](references/co-planner-prompt-template.md).

Every Co-Planner audit **must enforce three structural constraints**:
1. **Mandatory 3-Class Tagging** for every objection (with concrete evidence):
   - **`[HARD-FACT]`** — Verified math/statistical fallacy (e.g., post-treatment/collider bias, wrong denominator), metric misdefinition, missing dataset labels, or broken code/checksum invariant.
   - **`[FIXABLE-SPEC]`** — Draft realization bug (pseudocode edge case, initialization weight, module layout, training/eval boundary detail) that can be repaired without abandoning the core idea.
   - **`[UNVERIFIED-RISK]`** — Reasonable skepticism where empirical evidence does not yet exist either way, or protocol-scope tension that can be cleanly isolated.
2. **Mandatory Rescue / MVV Clause**: whenever recommending `REVISE` or `KILL` on an ambitious idea, the Co-Planner must also state the **cheapest Minimal Viable Variant (MVV) or ≤1-day falsification probe** that tests the core intuition without the bloated stack.
3. **Conservative Self-Audit Clause**: whenever advocating a safer incremental fallback, the Co-Planner must explicitly state that fallback's **ceiling risk** (what breakthrough it cannot achieve).

### Step 3 — Lead Planner 3-Class Triage & Final Ruling
Apply [`references/anti-defensive-rubric.md`](references/anti-defensive-rubric.md) rigorously:

1. **Absorb `[HARD-FACT]` with zero ego**: spot-check surprising code/data claims directly; if verified, retract or redesign immediately. Never argue against verified code or recomputed numbers.
2. **Repair `[FIXABLE-SPEC]` surgically**: fix the engineering bug and strip bundled confounds (never mix 4–5 unrelated changes into a single unattributable run), while **keeping the core idea intact**.
3. **Defend ambition against defensive `[UNVERIFIED-RISK]`**: do not surrender a high-upside hypothesis to defensive phrasing ("no evidence yet → kill"). Instead:
   - Strip speculative multi-layer stacks down to a **single-variable MVV**;
   - Pair any deliberately **overruled** Co-Planner `KILL` with an explicit **cheap kill criterion** (≤1–2 days);
   - Separate **Protocol-Strict Track** (fair head-to-head comparison under existing frozen rules) from **Next-Gen System Track** (protocol/cadence extensions), never conflating the two in headline metrics.

## Round Cap & Convergence

- **Default: 1 round** (`Lead Draft → Co-Planner Audit → Lead Ruling`).
- **Maximum: 2 rounds**, triggered **only** when Round 1 exposed a `[HARD-FACT]` that required replacing the core mechanism and the new MVV needs a quick sanity check (reuse the Co-Planner session when supported, e.g., `codex exec resume <session_id>`). Never spiral into open-ended debate.

## Required User-Facing Synthesis Format

Present one concise, transparent synthesis — never dump raw adversarial walls of text and never conceal disagreements:

1. **Converged Primary Plan**: the lean, grounded, ambitious recommendation after review.
2. **Accepted Hard Corrections (`[HARD-FACT]` / `[FIXABLE-SPEC]`)**: exact errors, fallacies, or repo realities caught by the Co-Planner and fixed.
3. **Preserved Bold Bets & Overrules (`[UNVERIFIED-RISK]`)**: where the Lead Planner intentionally pushed back against defensive conservatism, why the upside justifies testing it, and the exact cheap falsification gate.
4. **Immediate Next Action**: the single highest-information diagnostic or MVV experiment to run first.
