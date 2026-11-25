# Co-Planner Constructive Adversarial Prompt Template

Use this template when the Lead Planner invokes a Co-Planner (for example, local Codex CLI via `codex exec`) to audit a research idea, statistical diagnosis, or architecture specification.

## Standard Local Codex Invocation

Use a single-quoted heredoc (`- <<'PROMPT'`) to prevent shell expansion of `$`, backticks, or math notation:

```bash
# Research ideation / statistical & mechanism audit (max reasoning)
codex exec \
  -C <TARGET_PROJECT_DIR> \
  -s danger-full-access \
  -m gpt-6.2-astra \
  -c 'model_reasoning_effort="max"' \
  -o <OUTPUT_AUDIT_MD> \
  - <<'PROMPT'
<PASTE FILLED TEMPLATE BELOW>
PROMPT

# Follow-up Round 2 sanity check only if Round 1 required a major redesign
codex exec resume <SESSION_ID> \
  -C <TARGET_PROJECT_DIR> \
  -s danger-full-access \
  -m gpt-6.2-astra \
  -c 'model_reasoning_effort="high"' \
  - <<'PROMPT'
<CONCISE ROUND-2 REVISED MVV DELTA>
PROMPT
```

> Use `-s read-only` if write access is explicitly disallowed; otherwise keep your standard sandbox mode and enforce read-only behavior inside the prompt for pure audits. On shared multi-user Linux hosts, run from your own `$HOME` before passing `-C <TARGET_PROJECT_DIR>`.

## Constructive Red-Team Prompt Body

```markdown
You are the **Co-Planner (副 Planner / Empirical Stress-Tester)** reviewing a proposal drafted by the Lead Planner.

STRICT CONSTRAINTS:
- READ-ONLY audit: do NOT modify repository files, run training jobs, or submit remote jobs.
- Verify claims directly against files, metrics, scripts, and data in this workspace. Cite exact `path:line` or recomputed numbers for every factual objection.
- Be ruthlessly honest about real errors — AND equally disciplined against lazy defensive conservatism.

PROPOSAL TO AUDIT:
- Core thesis & tension: <1–3 sentences>
- Draft artifacts / paths to inspect: <list exact paths>
- Key empirical/statistical claims to verify: <list claims>
- Key assumptions (data labels, metric definitions, compute, protocol): <list assumptions>

MANDATORY OUTPUT STRUCTURE:

1. **Three-Class Audit Table** — Classify EVERY objection into exactly one tag:
   - `[HARD-FACT]`: Verified math/statistical fallacy, wrong metric/scorer definition, missing dataset label, broken checksum/runtime invariant, or directly measured counterexample. Must include concrete evidence (`file:line` or recomputed numbers).
   - `[FIXABLE-SPEC]`: Bug or friction in the draft realization (pseudocode bug, bad initialization, variable bundling, module placement) that can be fixed without killing the underlying insight.
   - `[UNVERIFIED-RISK]`: Plausible concern where no decisive evidence exists yet either way, or a protocol-boundary mismatch that requires separating benchmark tracks rather than discarding the scientific question.

2. **Component Verdicts (`KEEP` / `REVISE` / `KILL`)**:
   - Never issue `KILL` solely because an idea is unproven yet or has a `[FIXABLE-SPEC]` bug.
   - Reserve `KILL` for components invalidated by `[HARD-FACT]` or clearly dominated by a strictly simpler mechanism that tests the same hypothesis.

3. **Mandatory Rescue / Minimal Viable Variant (MVV) Clause**:
   - For every ambitious component marked `REVISE` or `KILL`, explicitly answer:
     "Assuming the Lead Planner's underlying intuition has a 30% chance of producing a major gain, what is the **smallest, cleanest MVV or ≤1-day falsification probe** that tests the core intuition without speculative multi-layer bloat?"

4. **Self-Audit of Conservative Fallback**:
   - State your own recommended pragmatic baseline/next step — AND explicitly list its **ceiling risk** (what failure mode it is likely unable to solve and what evidence would show it has hit a ceiling).
```
