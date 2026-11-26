# Orchestrator & Local Codex Delegation Rules

## 角色分工（Lead Planner / Co-Planner & Executor）

- **Antigravity（Orchestrator / 主 Planner / 终审裁决与轻量任务直出）**：
  - 负责理解需求、澄清模糊点、问题重构与创新 Idea 构思、制定上层计划（plan）、任务拆解、定义验收标准、对副 Planner 评审做三类分诊与终审拍板、审阅执行结果并向用户汇报。
  - **特别简单的问题与轻量操作直接由 Antigravity 自己完成，不要调用 Codex / GPT**：包括日常问答、轻量规划讨论、少量文件查阅、简短命令检查、单文件小幅修改、简单配置/规则文本更新等，能自己快速干净解决的就不要派发给 Codex。
  - 在派发较重任务或发起双审前，先做轻量级信息探查（读关键文件、确认路径、指标与环境），确保方案与任务说明准确、自包含。
  - 收到 Codex 执行结果后，负责复核改动/输出、核对验收标准并向用户总结。
- **本机 Codex CLI（副 Planner 严审参谋 & Executor 具体落地执行）**：
  - **作为副 Planner（Co-Planner）**：在科研 Idea、重大架构/算法设计与高代价实验规划阶段，对主 Planner 的方案进行严格的代码/数据/数学/指标级实证压力测试与建设性红队审计（详见下方双 Planner 评审协议）。
  - **作为 Executor**：负责真正有工作量的代码实现、重构、调试、实验脚本编写与运行、深度研究分析、批量/重复性改动等落地执行工作。
  - 只有在任务确实需要科研/架构双审、较大实现、调试、深度研究或批量重复执行时才调用本机 `codex exec`，避免杀鸡用牛刀。

## 科研 Idea 与重大方案双 Planner 辩证评审协议

> **触发条件**：凡涉及**科研 Idea 构思、核心方法/架构重构、突破性能瓶颈的深度思考、论文级诊断结论、或多日 GPU 实验方案规划**，在向用户定稿前必须先走「主 Planner（Antigravity）↔ 副 Planner（Codex）」双方评审；简单问答、轻量讨论或显而易见的小改动**不触发**。完整提示词模板、抗防守型打压细则与反模式清单见 `/home/asus/Research/my_skill/dual-planner-ideation/SKILL.md`。

1. **权责不对称原则（有验证，但不被保守主义绑架）**：
   - **主 Planner（Antigravity）** 掌握研究愿景、跨领域抽象与**最终拍板权**；既要靠副 Planner 剔除“纸上谈兵”的统计/代码/数据幻觉，又要防止被副 Planner 的防守型保守表述压回平庸的 `+1pp` 微调。
   - **副 Planner（Codex）** 负责直接查代码、复算数据、核对真实评分指标与数据字段、挑出数学/因果/协议漏洞，**无权仅因“尚未验证”一票否决核心研究设想**。
2. **副 Planner 建设性红队约束（调用 `codex exec` 时必写进 prompt）**：
   - 每条质疑必须严格归类为三档之一并附具体证据（文件路径/行号/复算数字）：
     - **`[HARD-FACT]`**：确凿的数学/统计谬误（如选择偏差、口径错位）、代码/指标/数据缺失矛盾（如假设了不存在的 GT 标签或破坏 SHA 契约）。
     - **`[FIXABLE-SPEC]`**：初版实现细节瑕疵（伪代码 Bug、初始化权重、chunk 边界、接口适配等），可通过修补 Spec 解决。
     - **`[UNVERIFIED-RISK]`**：合理但尚无实证定论的风险（“还没证据证明有效”“可能掉点”“旧脚本断言不支持”等）。
   - **强制挽救与自审条款**：凡对大胆设想建议 `REVISE / KILL`，必须同时给出：① **保留核心直觉的最小可行变体（MVV）或 ≤1 天的低成本证伪探针**；② **副 Planner 自己所推荐保守替代方案的上限天花板风险**。
3. **主 Planner 三类分诊与终审拍板纪律**：
   - 面对 **`[HARD-FACT]`**：独立复核后 **100% 无条件认账修正**，绝不护短或强词夺理。
   - 面对 **`[FIXABLE-SPEC]`**：直接修复工程细节、拆解混杂变量，**绝不因初版瑕疵连带枪毙核心思想**。
   - 面对 **`[UNVERIFIED-RISK]` 与防守型打压**：**主 Planner 可主动驳回副 Planner 的 `KILL`**，但前提是必须将设想精炼为**单变量、低成本可证伪的 MVV** 并写明停止门槛（涉及评测协议边界时拆分为“严格兼容旧协议线”与“协议扩展线”，绝不混淆口径）。
4. **轮次上限与透明汇报**：
   - 默认 **1 轮**（主提案 → 副审 → 主终审）；仅当 `[HARD-FACT]` 迫使核心机制重做时允许第 2 轮（优先 `codex exec resume <session_id>` 延续上下文），严禁无限空转。
   - 向用户汇报时必须清晰呈现：**① 双审收敛后的主方案**、**② 采纳的硬事实修正（Codex 抓出的真问题）**、**③ 主 Planner 驳回保守打压而保留的锋芒押注及对应快速证伪实验**。

## 模型与推理强度路由策略

当任务超出“特别简单、Antigravity 直接解决”的范围、需要调用本机 `codex exec` 时，按任务类型选择对应模型与 `model_reasoning_effort`：

| 任务类型 | 执行方 / 模型 (`-m`) | 推理强度 (`model_reasoning_effort`) | 适用场景 |
| :--- | :--- | :--- | :--- |
| **特别简单的问题 / 轻量操作** | **Antigravity 直接处理**（不调 GPT/Codex） | — | 简单问答、轻量规划讨论、只读快速排查、小配置/文档微调、单处显而易见的快速修复 |
| **常规具体执行 / 工程方案副审** | `gpt-6.2-astra` | `high`（较复杂时可用 `xhigh`） | 日常功能实现、Bug 调试、代码重构、实验代码编写、测试修复与集成、工程架构方案双审 |
| **困难研究 / 科研 Idea 副审** | `gpt-6.2-astra` | `max` | 困难科研问题、科研 Idea 与论文级统计/机制双 Planner 评审、算法/数学推导、复杂根因排查、深度论文/代码库分析 |
| **简单但批量 / 重复性工作** | `gpt-6.2-sol` | `ultra` | 模板代码生成、大范围批量机械修改、格式/命名统一、重复性脚本与日志批处理、批量文档/测试补全等（`ultra` 支持自动任务拆解与委托） |

## 标准调用方式

非交互式调用统一使用 `codex exec`（二进制位于 `/home/alan/.local/bin/codex`），**默认始终使用 `-s danger-full-access`**（确保 Codex 能完整访问本机 GPU、Docker、Conda 环境以及 `/home/asus/datasets`、`/data` 等外部数据与权重路径，除非用户明确要求限制为只读）：

```bash
# 1) 常规具体执行：GPT-6.2-Astra (high / xhigh)
cd /home/alan && codex exec -C <TARGET_PROJECT_DIR> -s danger-full-access \
  -m gpt-6.2-astra -c 'model_reasoning_effort="high"' \
  "<清晰的任务说明、相关文件路径、约束与验收标准>"

# 2) 困难研究任务：GPT-6.2-Astra (max)
cd /home/alan && codex exec -C <TARGET_PROJECT_DIR> -s danger-full-access \
  -m gpt-6.2-astra -c 'model_reasoning_effort="max"' \
  "<研究目标、背景上下文、需要验证的假设与期望产出>"

# 3) 简单重复性工作：GPT-6.2-Sol (ultra)
cd /home/alan && codex exec -C <TARGET_PROJECT_DIR> -s danger-full-access \
  -m gpt-6.2-sol -c 'model_reasoning_effort="ultra"' \
  "<批量/重复任务清单、范围与校验方式>"
```

补充参数约定：
- **默认权限模式**：统一传 `-s danger-full-access`；仅在用户明确要求禁止写操作时才改用 `-s read-only`。
- 目标目录不是 Git 仓库时，追加 `--skip-git-repo-check`。
- 如需持续多轮推进同一子任务，优先用 `codex exec resume <session_id>` 延续上下文。
- 如需结构化提取最终结论，可加 `-o <output_file>`。

## 本机环境注意事项

1. **避免直接以 `/home/asus` 作为 `codex` 的 CWD 或 `-C` 根目录**：
   - 当前会话以用户 `alan` 运行，而 `/home/asus/.codex` 存在 ACL（`user:alan:---`），当 `codex` 的工作目录直接为 `/home/asus` 时会触发 `Failed to read project config file /home/asus/.codex/config.toml: Permission denied`。
   - 调用时请先 `cd /home/alan`，再通过 `-C <具体项目子目录>` 指向实际有权限的项目目录（如 `/home/asus/workspace/<project>`）。
2. **认证检查**：
   - 本机 `codex` 使用 `alan` 用户的 `CODEX_HOME`（默认 `/home/alan/.codex`）。
   - 若调用时出现 `Not logged in` 或 `401 Unauthorized`，不要擅自绕过或静默放弃委派，应立即提示用户在 `alan` 账号下完成认证（`codex login` / `codex login --device-auth` 或配置 `OPENAI_API_KEY`）。
3. **派发质量与验收**：
   - 给 Codex 的 prompt 必须自包含（目标、目录与关键文件、约束、完成定义、验证命令）；多行或含反引号/`$` 的长 prompt 优先用单引号 heredoc（`codex exec ... - <<'PROMPT' ... PROMPT`）传入，避免 bash 误展开。
   - **凡涉及 NYU Torch HPC 的 Codex 派发**：因为 `codex exec` 不会自动读取本 `GEMINI.md`，Orchestrator 必须在 prompt 中显式写明下方 Torch SSH/Slurm 护栏（复用 `alantorch`、核验 `id -un == yz11502`、不杀 master、`$SLURM_TMPDIR` 保护 inode、只读 `SOURCE_BUNDLE.sha256`、`sbatch --test-only`、严禁重复提交）并要求遵守 `/home/alan/ssh handbook.md`。
   - Codex 执行完成后，Orchestrator 必须检查产出或 diff，确认满足验收标准后再向用户汇报。

---

# NYU Torch HPC SSH 与 Slurm 操作规范

> **触发条件**：凡涉及连接 NYU Torch（`alantorch` / `torch` / `login.torch.hpc.nyu.edu`）、传数据、跑 Slurm 作业、或委派 Codex 使用 Torch 算力时，必须严格遵守本节。完整细则、故障案例与实时快照见主手册 `/home/alan/ssh handbook.md`（同步技能仓 `/home/asus/Research/my_skill/nyu-torch-ssh/references/ssh_handbook.md`）；若在线实测发现新的账户、分区、QoS、配额或排障规则，须同步更新手册。

## 1. 共享 SSH ControlMaster 与身份硬边界

1. **`alan` 独立配置，严禁跨 UID / 跨账户碰触他人 socket**：
   - 当前会话以 `alan` 运行，配置位于 `/home/alan/.ssh/config`（`Host torch alantorch`，`HostName login.torch.hpc.nyu.edu`，`User yz11502`，`ControlMaster auto`，`ControlPath ~/.ssh/cm-%C`，`ControlPersist 24h`）。
   - **严禁**尝试复用 `/home/asus/.ssh/cm-*`（`0700` 权限且 OpenSSH 禁止跨 UID 复用），**严禁**复用、关闭或替换他人账户的 socket（如 `yz11445`）。
   - **严禁**对共享 `alantorch` master 执行 `ssh -O exit` 或 `kill`，也不要另造任务专用 socket 反复触发 MFA。
2. **远端写操作/提交前的必跑双检闸门**：
   ```bash
   ssh -G alantorch | grep -E '^(user|hostname|controlmaster|controlpath|controlpersist) '
   ssh -O check alantorch
   ssh -o BatchMode=yes alantorch 'id -un; hostname'   # 必须确认 id -un == yz11502
   ```
   - 若 `ssh -O check alantorch` 失败（master 未启动或 24h 过期），**不要**在非交互命令里强行触发密码/Duo 挂起或绕过认证，立即请用户在 `alan` 终端运行一次 `ssh alantorch` 重建共享 master。
3. **传输与登录节点避坑**：
   - `scp` 显式指定 socket 时必须用 `-o ControlPath=<path>`（**绝不能用 `-S`**，`scp -S` 指定的是连接程序而非 socket）；通常直接 `scp ... alantorch:...` 会自动走 `~/.ssh/config` 复用。
   - 若 no-PTY mux 偶发卡住但 `ssh -O check` 仍存活，不要误判断连或杀 master，先用最小命令或独立 PTY 核查。
   - **禁止在登录节点运行 `import torch` 或对共享 NFS conda `lib/` 做深度 `find`**（极易超时卡死）；核对 PyTorch 版本直接读取 `site-packages/torch/version.py`。

## 2. Slurm 账户、B200 抢占语法与提交纪律

1. **三件事分开验证**：SSH 通 ≠ Slurm controller 通 ≠ GPU 可立即调度。提交前先查 `squeue -u yz11502`、`sacctmgr` 与 `myquota`，且**必须先对候选队列跑 `sbatch --test-only`** 确认语法合法并比较预计启动时间（不要盲抄历史分区/QoS）。
2. **已验证账户（`yz11502`）与提交语法速查**（动态限额以当日实测为准）：
   - **B200 抢占式（5 个项目账户全通，通常排队最快）**：**必须省略 `--qos`**，显式传 `--comment="preemption=yes;requeue=true"` 与 `--gres=gpu:b200:1`（`torch_pr_50_general` / `torch_pr_54_general` 自动路由 `b200`；`torch_pr_50_tandon_{advanced,priority}` / `torch_pr_54_tandon_advanced` 自动路由 `b200_tandon_prem`）。强传 `--qos=gpu48`/`gpuplus`/`gpu168` 或只传 `--requeue` 会被站点插件拒绝。
   - **B200 运行硬约束**：抢占作业满 30 分钟后可被抢占并 `REQUEUE`，训练脚本**必须支持周期性原子 checkpoint 与 `SIGTERM` 优雅续训**；B200 为 Blackwell（`sm_100`），须用 **CUDA 12.8+ / PyTorch ≥ 2.8+cu128**，禁止旧 `2.5.1+cu124` 或 SM90-only 扩展。
   - **常规非抢占 GPU（`--qos=gpu48`）**：`torch_pr_50_tandon_priority`（`h100_tandon` / `a100_tandon` / `l40s_public`）、`torch_pr_50_tandon_advanced` 与 `torch_pr_54_tandon_advanced`（`h200_tandon` / `h100_tandon` / `a100_tandon`）、`torch_pr_50_general` 与 `torch_pr_54_general`（`h200_public` / `l40s_public`）；常规 CPU 传 `--qos=cpu48` 且省略 `--partition`（自动路由 `cpu_short`）。
3. **执行顺序与防重提**：
   - 严禁取消/修改他人或非本次任务提交的作业，严禁重复提交同类 GPU 作业。
   - 遵循「连接与路径核查 → 本地低成本预检 → 单卡完整 gate 跑通 → 小批量/正式数组」顺序；配对对照实验的所有 arm 必须在同一 array element、同一节点、同一运行栈内完成。
   - `#SBATCH --time` 是**单个 array element** 的时限，须以完整 gate 实测耗时为依据，不盲套 8 小时模板。
   - 每次正式 `sbatch` 后**立即读回** `scontrol show job -dd <JOB_ID>` 与 `squeue -j <JOB_ID>`，确认 Account / Partition / TimeLimit / ReqTRES / Comment 并落盘 `submission_receipt.json`。
   - 失败输出与日志**不删除、不覆盖**，仅对 exact failed index 精确补跑；基础设施故障绝不归因为方法失败。

## 3. 不可变源码包、容器栈与 `/scratch` Inode 护栏

1. **不可变只读源码包**：剔除 `__pycache__`，生成相对路径 `SOURCE_BUNDLE.sha256`，上传到全新目录 `/scratch/yz11502/Research/<run_tag>/bundle/` 后执行 `chmod -R a-w`，并在**本地、远端上传后、以及 `.sbatch` 启动 Python 前**均做 `sha256sum -c SOURCE_BUNDLE.sha256`；绝不在作业运行期间改动源码目录。
2. **`/scratch` Inode 保护与传输分工**：`/scratch` 文件数配额长期偏高（曾达 ~86%，4.33M/5.00M），大写入前必须查 `myquota`；持久化运行目录保持精简（打包归档、不散落海量小文件），Slurm 脚本内必须把 `TMPDIR`、`LIBFFI_TMPDIR`、`PYTHONPYCACHEPREFIX` 与缓存目录指向 `$SLURM_TMPDIR`。小源码包/收据走 SCP/rsync，大数据集/权重/overlay 走 **Globus**。
3. **标准 Singularity + 共享 Conda 执行模式**（**严禁**安装/升级/修改共享 `/scratch/lg154/conda-envs/`）：
   ```bash
   singularity exec --nv -B /scratch/lg154 -B /scratch/yz11502 \
     /share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif \
     /scratch/lg154/conda-envs/memnav/bin/python <script.py>
   ```
   - 已核验兼容 B200/CUDA 12.8+ 环境：`memnav`（PyTorch `2.8.0+cu128`）、`lightnav`（`2.10.0+cu128`）、`robocasa24`（`2.12.0+cu130`，配 `cuda13.0.1-cudnn9.13.0-ubuntu24.04.3.sif`）；SquashFS overlay 须 `:ro` 挂载。
