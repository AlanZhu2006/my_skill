# Anti-Defensive Triage Rubric (Lead Planner Ruling Guide)

Use this rubric after receiving the Co-Planner's audit so that **rigorous grounding** and **research ambition** reinforce rather than cancel each other.

## 1. The Three-Class Decision Matrix

| Co-Planner Tag | Definition | Lead Planner Mandatory Action | Can Co-Planner Veto Core Idea? |
| --- | --- | --- | --- |
| **`[HARD-FACT]`** | Verified statistical fallacy (post-treatment/collider bias, wrong denominator), wrong metric/scorer formula, missing ground-truth labels in saved data, broken runtime/checksum invariant, or directly measured empirical counterexample. | **Accept 100% immediately** after quick spot-verification. Retract false claims, update equations/metrics, or redesign around real ground truth. | **Yes** (for the invalidated claim or physically impossible dependency). |
| **`[FIXABLE-SPEC]`** | Pseudocode ordering bug, bad default gate/init weight, bundled ablations that confound attribution, TBPTT/buffer edge case, or file-placement conflict with hash checks. | **Repair surgically** without throwing away the core hypothesis. Strip bundled changes into isolated variables. | **No** (fixes the realization, not the thesis). |
| **`[UNVERIFIED-RISK]`** | Unproven empirical capability ("features might not separate distractors"), speculative overhead, or tension with a frozen benchmark scorer/schedule. | **Convert into a cheap probe / MVV or split protocol tracks.** Never drop a high-upside hypothesis solely due to lack of prior proof. | **No** (Lead Planner holds final ruling authority). |

## 2. Recognizing Defensive Conservatism (Red Flags)

Watch for these five defensive reflexes in Co-Planner reviews — treat them as **prompts to sharpen**, not automatic stop signs:

1. **The "No Prior Evidence" Catch-22**:
   - *Defensive phrasing*: `"There is no evidence yet that mechanism X achieves a +10 pp gain → KILL X."`
   - *Lead response*: Novel mechanisms never have closed-loop evidence before being built. Ask instead: *"What is the cheapest 1-day offline/probe test that could raise or crush our prior on X?"*
2. **The Draft-Bug Guillotine**:
   - *Defensive phrasing*: `"Pseudocode line 142 looks up buffer before writing, and chunk=32 can span a capture boundary → KILL the whole paradigm."`
   - *Lead response*: Reclassify as `[FIXABLE-SPEC]`. Fix the 5-line bug; evaluate the paradigm on its fixed mechanics.
3. **The Scorer-Assert Horizon**:
   - *Defensive phrasing*: `"Existing audit script rejects non-periodic dispatch / hot-start motion → KILL the idea completely."`
   - *Lead response*: Respect the frozen benchmark contract in **Track A (Protocol-Strict)**, while keeping the scientific question alive in **Track B (System/Protocol Extension)** with explicit naming and matched controls.
4. **The Past-Regression Generalization**:
   - *Defensive phrasing*: `"Combining previous modules E+F hurt performance → reject any new architectural component and only tune a tiny safe baseline."`
   - *Lead response*: Heed the discipline against *uncontrolled multi-module stacking*, but do not conflate bad feature stacking with principled structural redesign. Enforce **one mechanism per ablation**.
5. **The Zero-Ambition Anchor**:
   - *Defensive phrasing*: `"Just distill the teacher with a slightly larger history window and report whatever small gain emerges."`
   - *Lead response*: Keep that safe baseline as a **strong comparator**, never as the sole ceiling of the research program if a deeper bottleneck remains unsolved.

## 3. Conditions for a Valid Lead Planner Overrule

When the Lead Planner deliberately overrules a Co-Planner `KILL` on an `[UNVERIFIED-RISK]` item, **all four conditions must hold**:

1. **Zero Fact Denial**: Every `[HARD-FACT]` finding from the Co-Planner has already been accepted and reflected in the revised design.
2. **MVV Diet**: The overruled idea is stripped to its **single highest-leverage mechanism** (no 5-module "kitchen sink" specs).
3. **Explicit Cheap Kill Criterion**: Define upfront what measurable result in a cheap diagnostic or single run will genuinely kill the bet (no moving goalposts).
4. **Transparent Disclosure to User**: Explicitly show the user:
   - What the Co-Planner objected to;
   - Why the Lead Planner chose to keep/test this specific bet anyway;
   - What cheap gate resolves the disagreement.

## 4. Quick Anti-Armchair Checklist (Self-Check Before Calling Co-Planner)

Before drafting a bold proposal, the Lead Planner should self-check these 5 items to avoid wasting a review round on avoidable `[HARD-FACT]` mistakes:

- [ ] **Exact Metric Check**: Did I read the *actual* scorer class executed at eval time (not an unused sibling file)?
- [ ] **Exact Data Schema Check**: Do the saved datasets/archives actually contain every label my auxiliary heads ask for?
- [ ] **Exact Cohort Validity**: Did I condition any subgroup statistic on a post-treatment outcome (`collider bias`) or confuse an accumulated score with elapsed time?
- [ ] **Exact Runtime Contract**: Do file hashes, tensor horizons, or schedule auditors restrict where new modules live?
- [ ] **Single-Variable Discipline**: If this experiment improves or drops by 3 pp, can I tell *which single change* caused it?
