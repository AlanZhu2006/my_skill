# My Skills

Reusable skills for Codex.

- [ICRA Human Review](icra-human-review/SKILL.md): evidence-grounded, human-calibrated pre-submission review of robotics papers.
- [Research Compass](research-compass/SKILL.md): intuition-led research with external connections, competing explanations, informative experiments, and explicit controls against drift and repetitive runs.

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

### Development checks

```bash
python3 -m unittest discover -s tests -v
```
