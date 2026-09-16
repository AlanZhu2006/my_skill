# Human-review calibration

Use these findings to calibrate behavior, not as a checklist for manuscripts.

## Empirical signals

- Expert evaluation of 2,960 criticisms from 82 Nature-family papers found that strong AI reviewers can surface valuable issues, but AI reviewers overlap with one another much more than human reviewers and exhibit recurring failures such as weak subfield knowledge, poor multi-file context management, and over-criticism of minor issues. Source: [Kim et al., 2026](https://arxiv.org/abs/2605.20668).
- PeerCheck reports that LLM reviews emphasize different topics from human reviews: models lean toward theory, while humans emphasize methodology and experiments. Chain-of-thought helped in their setting; retrieval had inconsistent effects. Source: [Chen et al., Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.1170/).
- Automated-review scores can be affected by stylistic rewriting and multiple AI reviewers can show excessive agreement. Source: [Baumann et al., ICML 2026 position paper](https://arxiv.org/abs/2605.03202).
- A controlled rewriting study of 120 ICLR papers found AI judgments most sensitive to evidence emphasis and novelty stance, followed by scope. Effects varied with reviewer, rewriter, and initial score; stricter prompts reduced ratings without consistently reducing rhetorical sensitivity. More rewrite rounds and reviewer feedback were not reliably better. Human scores characterized the original papers, not human responses to the rewritten variants. Source: [Li et al., arXiv:2608.08975v1](https://arxiv.org/abs/2608.08975v1), Sections 3–6 and Limitations. Use the operational distillation in [rhetoric-aware-review.md](rhetoric-aware-review.md), not the article's experimental rewriting prompts.
- OpenReviewer was trained on 79,000 ICLR/NeurIPS reviews and better matched human recommendation distributions than general models, but its published evaluation does not establish fine-grained correctness for robotics criticism. Source: [Idahl and Ahmadi, NAACL 2025](https://aclanthology.org/2025.naacl-demo.44/).

## Behavioral consequences

- Optimize concern precision and importance, not concern count.
- Preserve disagreement and uncertainty; repeated AI agreement is not human consensus.
- Give methodology, experimental design, protocol comparability, and main-table interpretation priority over generic theory requests for empirical robotics papers.
- Treat polished prose and mathematical density as weak quality signals.
- Require the manuscript's actual evidence to support every criticism.
- Prefer one decisive simple baseline to a broad baseline wish list.
- Prefer narrowing a claim when that resolves the concern; do not automatically request new experiments.
- Narrow a claim only when its actual scope exceeds the evidence. Do not treat cautious phrasing as a defect or add caution merely to sound rigorous.
- Separate the factual basis of a judgment from its rhetorical trigger. A fluent explanation of a score is not independent validation of the score.

## Failure patterns to reject

- Fixed quotas for strengths or weaknesses.
- Mandatory mathematics criticism even when math is not central.
- Exhaustive persona panels whose outputs are later averaged.
- Suggestions that expand the paper without changing its central inference.
- Repeated warnings already bounded once in a limitation.
- Acceptance-probability claims from one simulated review.
- Fixed reject-first priors or automatically selecting the harsher of two reviews.
- Repeated rewrites until a preferred model gives a favorable rating.
