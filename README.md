# My Skills

Reusable skills for Codex.

- [ICRA Human Review](icra-human-review/SKILL.md): evidence-grounded, human-calibrated pre-submission review of robotics papers.
- [Research Compass](research-compass/SKILL.md): intuition-led research with external connections, competing explanations, informative experiments, and explicit controls against drift and repetitive runs.
- [Paper Research Scout](paper-research-scout/SKILL.md): turn daily paper reports into reproducible baseline opportunities and transferable conceptual directions, with verified sources and continuity across days.

## Research Compass / 研究罗盘

以稳定的研究问题为主线，允许假设、表示和方法被证据推翻。沿用 brainstorm 中“察 → 剥 → 转 → 演 → 选 → 证”的发现方式，把文献与开源实现、最小区分实验、失败记录和方向调整连成一个研究流程。

- 每个实验说明：区分什么解释、结果会改变哪个决定、何时停止。
- 遇到停滞时检查共同假设，寻找相邻领域的结构性联系；有依据地继续、修正或暂停。
- 复用有效基线，保留负结果；可选的本地记录工具检查相同实验，并明确记录重试和复现理由。
- 支持理论、算法和实证研究；不依赖某个模型、付费检索服务或多智能体框架。

### Install

Ask Codex's skill installer to install the folder:

```text
$skill-installer install https://github.com/AlanZhu2006/my_skill/tree/main/research-compass
```

For a repository-local installation, copy `research-compass/` into `.agents/skills/`. For personal discovery, it can live in `~/.agents/skills/`. See the [official skill documentation](https://developers.openai.com/codex/skills) for current discovery behavior. Installation is separate from cloning this collection.

### Use

```text
$research-compass 基于现有 brainstorm、代码和实验记录继续研究这个问题。
保持原始目标，检查当前解释及更简单的替代解释，参考相关论文和开源实现。
优先选择能改变下一步决定的工作；如果实验已经没有信息增量，重新审视问题。
本轮预算：两小时，只使用现有本地资源。保存结论和可恢复的研究状态。
```

The skill is also discoverable for relevant research requests. It does not itself launch background jobs or schedule future work. The optional Python helper records run plans and outcomes; it does not execute experiments or enforce resource limits. See its [usage and limits](research-compass/references/ledger.md).

## Paper Research Scout / 从论文发现研究方向

先粗筛论文的新颖机制与可信效果，再深读值得关注的工作，最后沿两条路线寻找值得投入的问题：

- **Baseline 切入点**：检查源码、准确的 checkpoint、数据和评估是否支持拟议实验，再寻找机制、表示、效率或适用边界上的实质问题。
- **观点迁移**：提炼论文的新视角，映射到另一个具体问题，检查成立条件、已有工作和能区分解释的最小验证。

默认关注 navigation、CV、perception、Gaussian、3D reconstruction 和 SLAM，降低 manipulation、VLA 与 humanoid control 的优先级，同时保留特别有价值的跨领域工作。先评价论文本身，明确要求时才映射到既有项目或架构。观点价值、实证可信度与可复现程度分别判断；先独立形成候选，再查历史去重。允许没有新方向或实验建议。选定方向后可交给 Research Compass 继续研究。

```text
$skill-installer install https://github.com/AlanZhu2006/my_skill/tree/main/paper-research-scout
```

```text
$paper-research-scout 阅读 ~/Documents/research idea/Codex_Automated_Paper_Reader/paper-daily/reports/2026-08-26.md。
先粗筛候选论文，说明哪些值得深读、哪些仍需证据，再找 baseline 切入点与可迁移观点。
核查论文、源码和权重；说明假设、最近已有工作、最小验证及停止条件。
默认开放找方向，不套用既有项目；形成独立候选后查历史去重，不启动训练。
```

也可以指定“最近三份日报”或日期范围。默认识别上述本地目录，也支持其他报告目录；显式给定的日期不会被最新日期替换。输出与原始日报分开保存。不因日报里写了实验建议就自动启动实验或创建定时任务。

### Development checks

```bash
python3 -m unittest discover -s tests -v
```
