# Design sources and deliberate adaptations

Reviewed on 2026-09-17. These are design references, not runtime dependencies. This skill uses independently written instructions and helper code. The comparisons describe the inspected sources, not guarantees about future versions or every use of those systems.

| Primary source | Useful pattern | Adaptation here |
| --- | --- | --- |
| [Karpathy: autoresearch](https://github.com/karpathy/autoresearch), especially [program.md](https://github.com/karpathy/autoresearch/blob/master/program.md) | Fixed evaluation, inexpensive experiments, persistent result records, simplicity as a consideration | Preserve comparable evaluation and provenance; use decision value beyond a single score, reuse a valid baseline, retain negative evidence, and give each campaign a stopping condition. The source's perpetual loop is not adopted. |
| [Sakana AI: AI Scientist v2](https://github.com/SakanaAI/AI-Scientist-v2) | Experiment management with branching search and multiple research stages | Keep a bounded frontier of competing explanations and revisit branches when evidence warrants it. Branch count, self-review, and search breadth do not establish scientific quality. Its code is not bundled. |
| [Agent Laboratory](https://github.com/SamuelSchmidgall/AgentLaboratory) | Literature, experimentation, reporting, and researcher involvement as connected phases | Carry assumptions and evidence between phases; involve the user for actual scope decisions. No fixed agent team, provider, or framework is required. |
| User's Razor Reframing brainstorm methodology, 2026-07-15 | See, Strip, Reframe, Unfold, Select, Verify; generate ideas through a more useful view of the phenomenon | Preserve conceptual discovery; add explicit research state, evidence-based branch decisions, repetition checks, and finite campaigns. Private examples and project findings are omitted. |

## Why these pieces belong together

A stable evaluation makes comparisons interpretable, but cannot decide whether the experiment answers the right question. A branch search can explore alternatives, but can multiply uninformative variants. Literature access supplies outside mechanisms, but a citation without a structural mapping does not transfer one. A compelling reframe generates predictions, but those predictions still need tests against simpler explanations.

Research Compass connects these at the decision level: preserve the question, make competing explanations visible, choose an informative affordable action, and retain its consequences for the next decision. This is a design hypothesis for a useful research workflow, not an empirical claim that the skill outperforms those projects.
