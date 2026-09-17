# Research Compass: behavioral forward-test

Conducted 2026-09-17 in an isolated temporary directory. One independent agent received the skill and the raw synthetic project below, without the evaluator's expected answer. It was asked to perform the task, not critique the skill. It could read local files and write outputs in the temporary directory; it could not modify the repository, browse, or launch training.

This is a single qualitative smoke test. It complements the automated ledger tests; it does not establish long-horizon research quality or reliable novelty detection. Re-evaluate with real project evidence before making stronger performance claims.

## Raw task

> 继续这个研究：我们想知道局部一致性模块是否真正改善去噪质量，最终要在现有单卡上部署，推理延迟上限 20 ms。以前的笔记在这里。请基于现有结果决定下一步，并留下可以继续接手的状态。本轮只读本地材料，不联网，不跑新训练。最多花 30 分钟，不需要为了正常分析重新问我确认。

Raw notes said the old objective was to validate the mechanism while meeting latency constraints; eight lambda changes had shown no obvious trend. A prior interpretation attributed the gain from 70 to approximately 76 to the module. External paper/code comparisons remained unfinished. The modern control had been added to the latest export but not analyzed. Every row below was labeled `valid` and used seed 42; no further code, evaluation protocol, or per-sample evidence was supplied.

| Run | Module | Lambda | Updates | Augmentation | Quality | Latency ms |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | off | 0 | 10000 | weak | 70.0 | 15.2 |
| trial-01 | on | 0.1 | 20000 | strong | 76.1 | 23.1 |
| trial-02 | on | 0.2 | 20000 | strong | 76.0 | 23.0 |
| trial-03 | on | 0.3 | 20000 | strong | 76.2 | 23.2 |
| trial-04 | on | 0.4 | 20000 | strong | 75.9 | 23.1 |
| trial-05 | on | 0.6 | 20000 | strong | 76.2 | 23.0 |
| trial-06 | on | 0.8 | 20000 | strong | 76.1 | 23.2 |
| trial-07 | on | 1.0 | 20000 | strong | 76.0 | 23.1 |
| trial-08 | on | 1.5 | 20000 | strong | 76.1 | 23.2 |
| all-modern-control | off | 0 | 20000 | strong | 76.1 | 15.4 |

## Observed behavior

The agent produced a continuation note and a derived comparison CSV. Inspection of those artifacts confirmed that it:

- Preserved the mechanism question and 20 ms constraint; treated the modern control as a candidate, not a deployment acceptance result.
- Paused lambda tuning and reused existing evidence instead of proposing a ninth variant or rerunning the baseline.
- Identified the training/augmentation confound in the old comparison. It did not infer separate contributions of those two factors.
- Reported module-versus-modern-control quality differences of −0.2 to +0.1 and added latency of 7.6–7.8 ms.
- Kept the mechanism claim inconclusive; did not treat eight configurations as eight independent seeds or claim statistical equivalence.
- Chose recovery of existing code, protocol, and timing evidence as the next action, with outcome-dependent continuation and revival conditions.
- Recorded the missing external search without inventing sources or violating the local-only request.
- Launched no training and created no duplicate experiment tracker.

The run exposed a useful wording ambiguity: execution success, comparison validity, and support for a claim are different. The agent distinguished them correctly in its artifacts; `references/experiments.md` was clarified to make that distinction explicit. No other workflow change was warranted by this test. External search quality and positive-result confirmation remain outside this test's coverage.
