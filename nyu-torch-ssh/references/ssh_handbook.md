# HPC 共享 SSH、Slurm、数据传输与故障排查手册

最后更新：2026-11-25（America/New_York；新增 §32 高效排卡实战规范：多分区抢占池组合、`sbatch --test-only` 对比选路法、Backfill 时限纪律、`SIGTERM` 零损原子续训与在训检查点只读快照隔离；此前 §31 见 B200 抢占提交语法及账户/分区/QoS/PyTorch 栈核验）

适用范围：NYU Torch HPC 上的 GEM / MemNav / Certified Episodic Compass / Pi3X
开发、数据传输、冻结评测与结果审计。

本文只整理**基础设施与可复现性问题**。方法效果、SR、统计显著性和论文结论以最新
`STATUS_*.md`、冻结 protocol、summary 与 independent verifier 为准。任何
infrastructure failure 都不能被解释为方法成功或失败。

## 0. 最重要的六条规则

1. 本项目共享入口对应 `yz11502`。2026-11-02 用户已授权 Mac 通过 `ssh torch`
   或 `ssh alantorch` 直接共享连接（§1.6）；工作站仍使用其本机的 `ssh alantorch`。
   复用所选机器上配置的默认 master，不另造任务专用 socket，不反复触发设备登录。
2. SSH 可用、Slurm controller 可用、GPU 可立即调度是三件不同的事，必须分别检查。
3. 每个配对 episode 的所有 arm 必须在同一 array element、同一节点和同一运行栈中
   完成；不同 episode 才允许分配到不同的合格 GPU。
4. `#SBATCH --time` 是**每个 array element**的上限，不是整个 array 的总时间；必须
   用完整 gate 的实测时长决定，不能沿用没有依据的 8 小时模板。
5. 小型源码 bundle/receipt 走 SCP、SFTP 或 rsync；大型数据集、模型、SquashFS
   overlay 和批量结果优先走 **Globus**。
6. 失败输出不删除、不覆盖。先保留日志和 partial output，再只重跑 exact failed
   index；summary 和 independent verifier 必须重新绑定到完整成功的依赖链。

### 0.1 默认执行顺序：先验证完整任务，再批量提交

新实验、新依赖或更换运行栈时，按下表推进。这里的 **gate** 指一项完整验证任务：
使用正式配置，走完配对运行、结果落盘和独立校验，而不只是成功 import 或启动服务。
已验证且未改变的部分复用原收据；改动影响到哪里，就重做对应检查。

| 顺序 | 做什么 | 进入下一步的条件 |
|---|---|---|
| 1. 连接与路径 | 用 `ssh alantorch` 确认账户；检查数据、配额、临时目录和输出位置 | 目标计算节点能读输入、写结果；见 §1、§6、§11–12 |
| 2. 依赖准备 | 固定解释器、源码、权重、容器与扩展库，完整打包并核验 | 实际运行环境加载的是预期文件；见 §5.4 |
| 3. 低成本预检 | 先检查全部输入、参数、CPU 逻辑、请求解析和输出字段 | 缺文件、错误参数与序列化问题在占用长时间 GPU 前暴露 |
| 4. GPU 完整验证 | 在拟用 GPU 上跑完整配对，覆盖长历史、目标切换和实际常驻状态 | 所有分支与独立校验通过，记录耗时、内存、显存和落盘量 |
| 5. 小批量运行 | 先低并发运行少量固定索引，确认服务隔离、端口和 I/O | 未出现新的运行故障，再逐步增加并发 |
| 6. 正式提交 | 显式传资源参数，读回 Slurm 状态，连接汇总与校验任务 | 索引、运行栈、时限和依赖都与计划相符；见 §2–3 |
| 7. 收尾与补跑 | 校验完整结果，保留失败记录，只补失败配对 | 结果可从持久存储复核；见 §9 |

优先测试容易拖到后期才出错的环节：第二臂模型加载、长历史显存峰值、最后一个目标、
真实图像请求、结果汇总和归档。验证样本按覆盖范围和资源需求选择，不按成功结果挑选。
正式配置下已完成并校验的 gate 样本只计一次；后续数组排除这些索引。
缩短步数或改过配置的工程测试单独保存，不并入正式结果。

连接配置、配额和可用分区会变化。下面保留的 socket、作业号与资源数值是项目记录；
实际使用时从 `ssh -G` 和集群状态读回，不直接照抄历史值。

## 1. 已确认的共享 SSH 配置

最近记录的 `ssh -G alantorch` 配置为：

- 用户：`yz11502`；
- 主机：`login.torch.hpc.nyu.edu`；
- `ControlMaster auto`；
- 默认 control socket：
  `/home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3`；
- `ControlPersist 86400`。

这个默认 socket 是工作站上的项目共享连接；Mac 直连使用 §1.6 的本机默认路径。
另一个解析为 `yz11445` 的活动 socket 属于不同账户，禁止复用、关闭或替换。

### 1.1 常用 SSH 命令

```bash
# 查看最终生效的用户、主机、socket 和复用设置
ssh -G alantorch | grep -E '^(user|hostname|controlmaster|controlpath|controlpersist) '

# 检查默认 master 是否仍活着；ControlPath 应从上一条命令读取
ssh -O check -o ControlPath=/home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3 alantorch

# 普通交互登录
ssh alantorch

# 最小身份检查
ssh alantorch 'id -un; hostname; date'

# no-PTY mux 卡住时，复现用户真实使用的 PTY 路径
ssh -tt -o BatchMode=yes -o ControlMaster=no \
  -S /home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3 \
  alantorch
```

登录后至少确认：

```bash
id -un       # 必须是 yz11502
hostname     # 应是 torch-login-*
date
pwd
```

### 1.2 2026-08-16 的 mux 误判

当时默认 master 能通过 `ssh -O check`，但下面的 no-PTY channel 卡在
`mux_client_request_session`：

```bash
ssh -o BatchMode=yes alantorch 'id -un; hostname'
```

这曾被错误解释为 MFA 过期或 HPC 宕机。实际情况是：用户普通登录正常，显式 PTY
立即进入 `torch-login-b-3`，SFTP/SCP 也能通过相同 master 工作。已复制的冻结协议在
远端复现 SHA-256：
`a019a49248950a537b14c651b7a812ba7ccb421504901f8a8de030d63ae3a230`。

因此正确结论只是：**一个 multiplexed no-PTY command channel 卡住**。底层原因没有
被证明，禁止进一步猜测为认证失效、网络中断或 Slurm 故障。

### 1.3 SSH 决策流程

1. 先运行 `ssh -G alantorch`，不要依赖记忆中的 socket 路径。
2. 再运行 `ssh -O check`。
3. no-PTY 超时时，先用显式 PTY 验证真实登录路径。
4. PTY 成功而 no-PTY 卡住时，把状态改变命令留在已认证 PTY 内执行；文件可继续通过
   同一默认 socket 的 SCP/SFTP 传输。
5. 不得仅凭一次 timeout 要求用户重新认证、宣布 HPC down 或把任务标记 blocked。
6. 登录节点曾缺少 `rg`；远端脚本启用 `set -e` 前必须先检查命令是否存在，必要时用
   `grep`、`find`、`sed` 等 POSIX/GNU 工具。

### 1.4 2026-08-21：复用 master 做临时只读 localhost tunnel

再次观察到：默认 master 的 `ssh -O check` 正常、已认证 PTY 正常，但新开的
`ssh alantorch hostname` / no-PTY session 仍可能无输出等待。此时不应绕过 master、
反复 device login 或宣称 HPC 失联。`~C` 在 multiplexed slave 中会明确返回
`escape not available to multiplexed sessions`；应通过 master control command 管理
转发。

当 SCP/SFTP 的新 channel 也无法及时建立、且只需拉取少量已解析文件时，验证过的
最小只读路径是：

```bash
# 1. 在已经认证的远端 PTY 中，仅绑定登录节点 localhost
python -m http.server REMOTE_PORT --bind 127.0.0.1 \
  --directory EXACT_READ_ONLY_ROOT >/tmp/PROJECT_http.log 2>&1 &
# 立即记录返回的 PID

# 2. 工作站通过权威 master 增加 localhost-only forwarding
ssh -S /home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3 \
  -O forward -L LOCAL_PORT:127.0.0.1:REMOTE_PORT alantorch

# 3. 只下载已解析的显式文件，并按 sealed receipt 逐项核验 SHA-256
curl --fail --silent --show-error \
  http://127.0.0.1:LOCAL_PORT/RELATIVE_FILE -o LOCAL_FILE
sha256sum LOCAL_FILE

# 4. 完成后立刻在远端 PTY kill 精确 PID，并撤销 forwarding
ssh -S /home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3 \
  -O cancel -L LOCAL_PORT:127.0.0.1:REMOTE_PORT alantorch
```

安全边界：server 和 tunnel 两端都只绑定 `127.0.0.1`；不能用 `0.0.0.0`；不能把
大数据集走这条路径；不能用目录级模糊下载；结束时必须 kill 精确 PID、cancel 精确
forward，并用原 benchmark/manifest 中的哈希验证每个文件。本次用该方式拉取
`621,086` bytes 的 NNR 最小镜像，benchmark、A/B trace、metadata、parquet 和三个
goal assets 全部逐项哈希一致。

### 1.5 2026-08-28：socket 可响应仍不代表账户正确

`ssh -S SOME_SOCKET alantorch ...` 会直接附着到 `SOME_SOCKET` 对应的 master；命令行
上的 alias 不会把这个 master 重新认证成 `ssh -G alantorch` 所声明的用户。因此，
“遍历 `~/.ssh/cm-*` 并选择第一个能运行命令的 socket”是错误且危险的做法。

本次同时存在两个可通过 `ssh -O check` 的 socket：默认 `yz11502` master 的新 no-PTY
channel 卡住，而较新的另一个 socket 可以立即执行命令，但远端 `id -un` 实际是
`yz11445`。后者能遍历 `/scratch/yz11502` 的部分目录，却不能读取 owner-only 的冻结
bundle，于是表现为数百个 `sha256sum: Permission denied`。这不是 bundle 损坏，也不是
Slurm 或文件系统故障；准备链在上传和 `sbatch` 前已 fail closed。

自动化必须同时验证连通性和身份：

```bash
expected_user=yz11502
socket=/home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3
actual_user=$(timeout 15 ssh -n -T -o BatchMode=yes \
  -o ControlMaster=no -S "$socket" alantorch 'id -un' 2>/dev/null || true)
test "$actual_user" = "$expected_user"
```

禁止把另一个账户的 responsive socket 当作 fallback，禁止关闭或修改它，也禁止在身份
未核对时执行远端写入、rsync 或 sbatch。`ssh -O check` 只能证明本地 master 进程接受
control 命令，不能证明它属于目标账户，也不能证明新 session channel 可用。

### 1.6 2026-11-02：Mac 直连与本机共享连接

用户明确授权在 Mac 上建立与工作站参数一致的连接复用。Mac 的
`/Users/alan/.ssh/config` 中，`torch` 与 `alantorch` 共用同一 Host 配置：

```sshconfig
Host torch alantorch
  HostName login.torch.hpc.nyu.edu
  User yz11502
  ControlMaster auto
  ControlPath ~/.ssh/cm-%C
  ControlPersist 24h
  ServerAliveInterval 60
  ServerAliveCountMax 30
  TCPKeepAlive yes
```

上面仅列访问与复用参数，既有其它连接选项保留。`ssh -G torch` 和
`ssh -G alantorch` 已核对：两者用户、主机、默认 ControlPath 相同，
ControlPersist=86400，保活间隔60秒、最多30次。连接文件属于各自客户端本机，
不能把 `/home/asus/.ssh/...` 当作 Mac 上可直接使用的 socket。

在 Mac 上优先按以下顺序操作；无需先经过工作站：

```sh
ssh -G torch | awk '/^(user|hostname|controlmaster|controlpath|controlpersist) /'
ssh -O check torch
# 默认 master 不存在时，由用户完成一次普通交互登录及所需认证：
ssh torch
# 已有 master 后，复用并核对身份：
ssh -o BatchMode=yes torch 'id -un; hostname; date; pwd'
```

只有实际 `ssh -O check` 与远端 `id -un=yz11502` 都通过，才能报告已连上。
本次修改时尚无 Mac 默认 master；配置核验不等于已经认证或已进入集群。
修改前已经打开、没有复用参数的 `ssh torch` 会话不会自动变成 master；
下次普通登录才会按新配置建立共享连接，不关闭或打断原会话。

若 master 正常而 no-PTY 通道卡住，从当前机器的 `ssh -G` 读出 ControlPath，
按 §1.1 的同一默认 master 显式 PTY 路径处理。Mac 不自带 Linux 的 `timeout`
命令；使用执行工具的有界会话并轮询同一 session，不重复发起认证。
需要从工作站访问时仍遵循原 `alantorch` 流程；两台机器各自复用本机默认 master，
均不得附着到其它账户的连接。

此节是 Mac 本地授权补充，未修改工作站 SSH 配置或其上游手册。以后同步上游时，
先核对下载哈希并合并本节，不能用较旧上游副本覆盖 Mac 访问说明。当前实时
Slurm 账户、QOS 与 GPU 资源仍必须登录后查询，不能从连接配置推断。

## 2. Slurm 常用命令

历史项目账户：`torch_pr_769_tandon_advanced`。2026-10-24 的 `yz11502` 关联中已不再列出该账户；新 Tandon 账户与实际通过提交预检的组合见 §23。本文旧脚本/作业号保留作历史记录，不能直接照抄账户。已预检的普通 GPU workflow 仍使用 QOS：`gpu48`。

### 2.1 查看分区、GPU 和队列

```bash
# 查看本项目已经验证过的三个 GPU 分区
sinfo -p h100_tandon,h200_public,a100_tandon \
  -o '%P %a %l %D %t %G'

# 查看自己的任务
squeue -u yz11502 \
  -o '%.18i %.12P %.22j %.10T %.10M %.10l %.6D %R'

# 查看同一项目账户正在占用/等待的资源
squeue -A torch_pr_769_tandon_advanced \
  -o '%.18i %.10u %.12P %.22j %.8T %.10M %.4D %b %R'

# 调度优先级与预计启动时间；预计时间会动态变化
sprio -j JOB_ID -l
squeue --start -j JOB_ID -o '%.18i %.10T %.19S %R'
```

### 2.2 查看历史状态、真实提交命令和节点

`squeue` 只适合活跃任务。任务完成后，`squeue -j JOB_ID` 可能返回
`Invalid job id specified`；这不表示 controller down，应改查 `sacct`。

```bash
sacct -j JOB_ID \
  --format=JobID,JobName%24,Partition%18,State,Elapsed,Timelimit,ExitCode,NodeList%16,Start,End -P

# 追溯完整 sbatch 提交行和工作目录
sacct -j JOB_ID -X \
  --format=JobID,JobName,SubmitLine%240,WorkDir%160 -P

# 查看活动任务的完整 Slurm 元数据
scontrol show job -dd JOB_ID

# array 显示 ID 与内部 JobId 不同时，查看映射
scontrol show job ARRAY_JOB_ID_ARRAY_INDEX | tr ' ' '\n' \
  | grep -E '^(JobId|ArrayJobId|ArrayTaskId|JobState|TimeLimit)='
```

### 2.3 查看日志与当前 arm

当前 SBATCH 通常使用 `%x_%A_%a`：job name、array job id、array index。

```bash
tail -n 200 /scratch/yz11502/Research/Nav-axis-uturn-results/slurm_logs/JOBNAME_ARRAYID_INDEX.out
tail -n 200 /scratch/yz11502/Research/Nav-axis-uturn-results/slurm_logs/JOBNAME_ARRAYID_INDEX.err

# 查最近完成的 episode receipt
find RUN_ROOT/evaluation -name completion.json \
  -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' | sort | tail

# 查常见硬错误；warning 不能脱离 exit status 单独定性
grep -RInE 'ABORT|Traceback|SIGABRT|CUDA error|RuntimeError|core dumped' \
  RUN_ROOT/logs RUN_ROOT/evaluation
```

### 2.4 标准提交模板

CLI 参数会覆盖 SBATCH 文件中的同名默认值。提交前必须显式核对 partition、account、
QOS、GPU、CPU、memory、time 和 array concurrency。`FROZEN_INDEX_SPEC` 必须由冻结
manifest 导出；不能假设索引连续，也不能把下面的占位符原样提交。例如 Final14 的
正式索引是 `0-20,42-62`，不是 `0-41`。分区只填写已通过完整 gate 的集合；其余资源
数值也须按本次实测替换。

```bash
FROZEN_INDEX_SPEC='REPLACE_WITH_EXACT_FROZEN_INDICES'
VALIDATED_PARTITIONS='REPLACE_WITH_PARTITIONS_THAT_PASSED_FULL_GATE'

eval_id=$(sbatch --parsable \
  --partition="${VALIDATED_PARTITIONS}" \
  --account=torch_pr_769_tandon_advanced \
  --qos=gpu48 \
  --gres=gpu:1 \
  --cpus-per-task=12 \
  --mem=96G \
  --time=01:00:00 \
  --array="${FROZEN_INDEX_SPEC}%4" \
  --export=ALL,... \
  MemNavData/slurm_EXPERIMENT_eval.sbatch)

summary_id=$(sbatch --parsable \
  --dependency=afterok:"$eval_id" --kill-on-invalid-dep=yes \
  --export=ALL,... MemNavData/slurm_EXPERIMENT_summary.sbatch)

verify_id=$(sbatch --parsable \
  --dependency=afterok:"$summary_id" --kill-on-invalid-dep=yes \
  --export=ALL,... MemNavData/slurm_EXPERIMENT_verify.sbatch)
```

`--array=...%4` 只表示最多四个元素并发，不是预留四张 GPU。实际可能只有一张或零张。

`sbatch --test-only` 检查提交参数并估计调度时间，不执行依赖、渲染或导航测试。
正式提交后用 `scontrol show job -dd JOB_ID` 核对 `Partition`、`TimeLimit`、`ReqTRES`、
`Dependency` 和数组并发上限，保存实际提交命令。尤其留意 `safe_sbatch` 等封装器注入
的 CLI 默认值。参数优先级与 `--test-only` 的含义见 [Slurm sbatch 文档](https://slurm.schedmd.com/sbatch.html)。

`afterok` 只依据上游退出码；包装脚本必须把运行、归档和校验失败正确传回。
依赖整个数组时，须所有成员成功才会放行，见 [Slurm 数组依赖说明](https://slurm.schedmd.com/job_array.html)。
下游任务应紧接上游提交，避免短任务完成并从控制器清除后才绑定依赖；已有旧结果的
处理流程见 §19。提交命令超时先查作业是否已创建，不直接再执行一遍。

### 2.5 取消、保留和 exact retry

取消是状态改变操作，必须先解析准确目标。禁止用模糊 glob 或错误账户。

```bash
# 取消单个任务
scancel JOB_ID

# 只取消某个 array 中尚未启动的元素，保留 running/completed
scancel --state=PENDING ARRAY_JOB_ID

# 取消已经失效的 summary/verifier dependency
scancel SUMMARY_JOB_ID VERIFY_JOB_ID
```

如果 runtime abort 留下 partial directory：

1. 将该 episode、对应 server logs 和 buffer 整体移动到
   `RUN_ROOT/failed_attempts/<job_and_reason>/`；
2. 不删除、不覆盖，不把 partial metric 纳入结果；
3. 以相同 bundle、manifest、seed、arm 和 output contract 重跑 exact index；
4. summary 依赖同时绑定 retained running task、replacement array 和 exact retry；
5. verifier 仍只依赖新 summary。

重跑单位是该索引的完整配对，不是只补最后失败的一臂。已有若干动作或一个成功分支，
不等于可以恢复其余运行；除非已验证的 checkpoint 同时保存模拟器、模型/几何状态、
随机数状态和目标进度，否则从该配对起点重跑。HTTP 请求可能已推进流式状态，响应
丢失时也不能盲目重发同一观测。

## 3. 分区、并发与申请时长

### 3.1 分区选择

- 对允许跨合格硬件运行、episode 内严格配对的评测，只列入本次运行栈通过完整配对
  gate 的分区；有多个合格分区时，让 Slurm 选择最早合法资源。
- 若结论与 GPU 型号、数值稳定性或性能有关，必须固定一个分区，并在 receipt 中记录
  GPU name、UUID、driver 和显存。
- 不得为了缩短排队临时加入仅通过 import、短渲染或 server-ready 检查的分区。
- 同一个 episode 的五个 arm 不可拆到不同 GPU；跨机器 CUDA 非确定性曾让同一 Goal-A
  路径出现 `7.81 m` 与 `2.70 m` 的差异。

常见 pending reason：

| Slurm reason | 含义 | 正确处理 |
|---|---|---|
| `Priority` | 有更高优先级任务 | 查看 `sprio`/`squeue --start`，不是代码错误 |
| `QOSGrpGRES` | 项目/QOS 的 GPU 总量受限 | 查看 account 队列，等待额度释放 |
| `QOSMaxGRESPerUser` | 单用户 GPU 数达到上限 | 不要重复提交；等待自己的任务完成 |
| `Dependency` | 上游未成功完成 | 查上游 `sacct`，不要把它当排队 |
| `Resources` | 当前没有满足请求的节点 | 核对分区与资源规格 |
| `Invalid job id specified` | job 已不在 active queue 或 ID 错误 | 用 `sacct` 查历史，不代表 controller down |

### 3.2 申请时长规则

`#SBATCH --time` 作用于每个 array element。过大的上限会让本可 backfill 的短任务看起来
像长任务。

1. gate 的计时包括输入准备、server 启动、全部 paired arms、结果校验与归档。
2. 根据合格 GPU 上的连续运行、最大冻结 step budget、长历史和多臂常驻状态估算
   上界；不能只用快速成功样本。已有任务曾采用约 2–3 倍实测余量，具体仍须覆盖
   本任务的准备和收尾开销，并以小批量实际耗时复核。
3. 同时记录 requested time 与 observed time；总 wall-clock 还受排队和实际并发影响。
4. 提交后核查真正生效的时限：

   ```bash
   squeue -j JOB_ID -o '%.18i %.10T %.10M %.10l %R'
   ```

### 3.3 Final14 的 8 小时到 1 小时修正

- 五臂 gate 实测 `18:12`；随后成功元素约 `11--16` 分钟。
- 旧 SBATCH 却为每个元素申请 `08:00:00`。
- “约 12.6 小时”只是 42 个约 18 分钟任务单卡串行的算术总量，不是申请了 12 小时。
- 生产时限改为 `01:00:00`，仍有三倍以上 H100 实测余量，并明显改善短槽调度。

Torch Slurm 拒绝了用户态原地修改：

```text
scontrol update ... TimeLimit=01:00:00
Unspecified error
```

因此采用的安全流程是：保留 completed/running，只取消 pending，以完全相同参数和
explicit `--time=01:00:00` 重提 exact pending indices，再重建 summary/verifier
dependency。当前审计 ID：

- replacement array：`15903404`；
- unrelated Habitat-aborted index 4 exact retry：`15903546`；
- replacement summary/verifier：`15903547` / `15903548`。

这是 infrastructure-only correction，没有改变 population、方法、模型、阈值、seed、
arm 或成功判据。

## 4. 文件传输：SSH 与 Globus 如何分工

### 4.1 小文件：SCP/SFTP/rsync

适合 source bundle、脚本、manifest、receipt 和少量日志。

```bash
scp LOCAL_FILE alantorch:/scratch/yz11502/Research/DESTINATION/

# 显式复用 control socket 时，scp 要用 -o ControlPath；scp 的 -S
# 表示“连接程序”，不是 socket 路径。
scp -o BatchMode=yes -o ControlMaster=no \
  -o ControlPath=/home/asus/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3 \
  LOCAL_FILE alantorch:/scratch/yz11502/Research/DESTINATION/

rsync -av --partial --info=progress2 \
  LOCAL_DIR/ alantorch:/scratch/yz11502/Research/DESTINATION/

# 远端核验
ssh alantorch 'stat -c "%s %n" /scratch/yz11502/Research/DESTINATION/FILE; sha256sum /scratch/yz11502/Research/DESTINATION/FILE'
```

不要用 `rsync --delete`，除非用户明确授权且目标已被精确解析。

### 4.2 大文件：Globus

适合大型数据集、多 GB checkpoint、scene archives、SquashFS overlay 和批量结果镜像。
优先 collection-to-collection 直传，不要让数据绕经共享工作站或 SSH mux。

当前环境事实：工作站已有 `/home/asus/.local/bin/globus`；Torch 登录节点当前没有
`globus` CLI。因此通常应在工作站 CLI 或 Globus Web App 发起传输，HPC 端只做目标
路径和 checksum 审计。

```bash
# 工作站：登录、确认身份、查找 collection
globus login
globus whoami
globus version
globus endpoint search 'COLLECTION_NAME'

# 查看目标路径
globus ls COLLECTION_ID:/path/

# 递归传输；checksum sync 用于可安全恢复的重复提交
globus transfer \
  SOURCE_COLLECTION_ID:/source/path/ \
  DEST_COLLECTION_ID:/destination/path/ \
  --recursive \
  --sync-level checksum \
  --verify-checksum \
  --label 'memnav-dataset-or-overlay'

# 保存 transfer 返回的 task ID 后查询/等待
globus task show TASK_ID
globus task wait TASK_ID
```

禁止在没有明确授权时使用 `--delete-destination-extra`。Globus 显示 succeeded 只说明
传输任务完成，不替代项目自己的 SHA-256 与数据合约检查。

每次大文件传输必须记录：

- source/destination collection ID 与路径；
- Globus task ID；
- 预期文件数和总 bytes；
- destination 上的 checksum manifest identity；
- 数据集许可/TOS 已满足；
- 核验后是否设置为只读。

## 5. 不可变 bundle 与 checksum

### 5.1 常用核验命令

```bash
# receipt 本身的身份
sha256sum SOURCE_ROOT/SOURCE_BUNDLE.sha256

# 在正确根目录验证 receipt 内全部相对路径
(cd SOURCE_ROOT && sha256sum -c SOURCE_BUNDLE.sha256)

# 检查是否仍有可写文件
find SOURCE_ROOT -type f -perm /222 -print

# 嵌套部署 receipt 也必须在 relocation 后独立执行
(cd SOURCE_ROOT/pi3x_deployment && sha256sum -c OUTPUTS.sha256)
```

外层 `SOURCE_BUNDLE.sha256` 只能证明嵌套 receipt 的字节没变，不能证明嵌套 receipt
搬家后仍可执行。Pi3X Attempt 4 就因为 `OUTPUTS.sha256` 写入 5090 生产机绝对路径而在
HPC relocation 后失败；后续 receipt 必须只含相对路径，并运行 portable verifier。

### 5.2 打包闭包

- `required=(...)` 不能只列入口脚本；必须递归检查 repository-local imports。
- 提交脚本、子进程 launcher、环境脚本和配置也必须进入 bundle 身份；只改入口脚本
  却不更新 receipt，会让实际执行与记录的版本脱节。
- Final14 Attempt 1 漏掉冻结的 `strict_graph_blind_20260806.json`。
- Attempt 3 虽包含 `materialize_paper_online_a_scene.py`，却漏掉其本地依赖
  `materialize_online_a_traces.py`。
- 远端 exact container import smoke 必须发生在提交科学任务之前。
- 新 run root 必须不存在；旧 attempt 不复用、不改写。

### 5.3 只读 bundle 与 Python bytecode

对只读 bundle 直接运行 `py_compile` 会试图创建 `__pycache__`，Replica/GOAT 均因此在
零 episode 阶段失败。可选做法：

```bash
export PYTHONPYCACHEPREFIX="${SLURM_TMPDIR}/pycache_${SLURM_JOB_ID}"
python -m py_compile PATH/TO/MODULE.py
```

或对严格只读 preflight 使用 AST syntax audit，不产生 bytecode。禁止为了让
`py_compile` 通过而临时把冻结 bundle 改回可写。

### 5.4 依赖先构建，再冻结，再到目标环境验证

**先确认每个进程实际使用什么。** Habitat、模型服务和汇总工具可能使用不同 Python。
记录各自的绝对解释器路径、`sys.executable`、关键包版本与 `module.__file__`，并核对
容器、CUDA/PyTorch、NumPy 和本地扩展。包名相同、import 成功，不代表加载了正确副本。
9 月 17 日的[整合验证](../docs/VALIDATION_20260917.md)就发现另一份 LingBot checkout
的 attention 实现与冻结版本不同；应匹配原依赖，不能放宽哈希检查。

**在正式数组前完成安装与构建。** 缺少的依赖放入任务专用环境、overlay 或依赖目录，
不临时升级多人共用的 conda 环境。权重、配置、tokenizer 等资源提前准备并核验；
会延迟编译的 CUDA 扩展，要在匹配目标 GPU/CUDA 的构建或验证作业中执行一次真实调用。
记录构建命令与产物版本，避免每个数组成员临时下载或同时写同一可变缓存。
登录节点只做站点允许的轻量准备，GPU 编译和测试使用调度资源。

**打包包含运行全程需要的内容。** 不仅检查服务启动，还检查目标切换、图像审计、
结果序列化、压缩与汇总涉及的依赖。
[Replica 缺包记录](REPLICA_ATTEMPT2_DEPENDENCY_INCIDENT_20260814.json)中，漏打包
`depth_anything` 导致历史生成后才发现模型无法启动；§13 的 OpenCV 事故则来自
Habitat Python 与模型 Python 的环境差异。不要用另一个环境的整份 `site-packages`
补洞。完成构建后生成 checksum，传输到独立目录，在最终路径重新核验，再冻结供作业读取。

**用目标运行栈检查真实输入与输出。** 所有计划输入先检查路径、读取和协议条件，
再在正式 container/overlay/解释器中做实际模型前向、渲染与请求往返。
CPU 预检应覆盖真实图像解析和输出字段；GPU gate 再把全部分支跑到独立 verifier。
[multipart 事故](TABLE1_MULTIPART_REPAIR_STATUS_20260911.md)只在特定 JPEG 分块边界
触发，而[收据事故](HPC_HARDENING_20260821.md)是在运行完成后才发现关键字段没有写入。
因此 ready、退出码为零与结果可复核是三个分别需要检查的条件。

## 6. Singularity、EGL 与数据 overlay

Habitat client 与渲染必须在已验证的 container + `--nv` + read-only overlay 中运行：

```bash
singularity exec --nv \
  --overlay /scratch/lg154/Research/datasets/_overlays/mp3d_revisit_v0_pt1.sqf:ro \
  -B /scratch/lg154 -B /scratch/yz11502 \
  /share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif \
  COMMAND ...
```

提交前不仅检查 overlay 文件存在，还要检查：

- `stat` bytes 与冻结值一致；
- container 内 episode root 完全一致；
- exact manifest 引用的 parquet 能在该 container/overlay 中逐个打开；
- collection、construction 和 evaluation 三阶段使用同一挂载合约。

已发生过两类真实错误：

1. Final14 Attempt 2 使用 host 上只有 37 scenes、零 Final14 episode 的 extracted root，
   没有挂 PT1 SquashFS；
2. Attempt 5 的 collection/manifest 已正确使用 overlay，但 evaluation SBATCH 漏掉
   `--overlay`，第一 arm 在读取 parquet 前失败。

GOAT EGL 事故的根因也不是 GPU family：wrapper 覆盖 `LD_LIBRARY_PATH`，把 Singularity
`--nv` 注入的 `/.singularity.d/libs/libEGL.so.1` 换成普通容器 EGL。不要整体替换
`LD_LIBRARY_PATH`；必须保留 `--nv` 注入路径，并在 exact runtime 内做 EGL smoke。

## 7. Server、端口和 CUDA 生命周期

### 7.1 端口

“先探测空闲端口，加载模型后再 bind”存在 TOCTOU。Paper Attempt 6 中端口 `39788`
在这段窗口被占用，出现 `Address already in use`。

正式任务应使用 `retrying_server_launcher.py`：

- 在受限端口范围内重试；
- 写出实际端口文件和 launcher receipt；
- readiness 成功后才启动 evaluator；
- `trap` 中只清理本任务记录的 PID；
- 不因端口冲突修改方法或数据。

### 7.2 CUDA HTTP handoff

Pi3X/Habitat 共驻时曾出现：bare renderer 约 `5--12 ms`，但完整异步 lifecycle 中 render
约 `19.18 s`。模型常驻和显存容量测试都正常；强同步后恢复到约 `5.9 ms`。根因是
Flask response 返回时 CUDA work 仍在队列中，随后 Habitat EGL/CUDA 被迫承担等待。

当前 formal server 使用：

```text
--synchronize_cuda_http_handoff
```

它在 HTTP response 交接前调用 `torch.cuda.synchronize(agent.device)`。这属于运行时
正确性修复，不是 Pi3X 方法增益。排查类似问题时必须分别测：

1. bare Habitat renderer；
2. 模型仅常驻、无请求；
3. 完整 memory/plan lifecycle；
4. 强同步对照。

不能仅看到“Pi3X 加载后变慢”就得出显存不足或模型几何失败。

## 8. 开发中已遇到的问题总表

| 现象 | 已确认原因 | 正确处理 | 禁止的误判/操作 |
|---|---|---|---|
| no-PTY SSH 卡住 | mux command channel 问题 | 先验证默认 socket 与显式 PTY | 直接宣布 MFA/HPC 失效 |
| `scp -S /path/to/socket` 报 `Permission denied` | `scp -S` 把路径当作连接程序执行 | 使用 `-o ControlPath=/path/to/socket`；若 jobs 已提交，只补传同一 receipt | 因 receipt 上传失败重复提交科学 DAG |
| 登录到了错误用户 | 复用了 `yz11445` socket | `ssh -G` + `id -un` 双检 | 杀掉别人的 master |
| 一次命令暂时无输出 | checksum/SSH 命令仍在运行，调用方返回了 session ID | 继续 poll 同一 session，并先查 `squeue`/`sacct` | 立即重复提交；曾因此生成等价 `15892898`/`15892919`，后者已在启动前取消 |
| `Invalid job id specified` | job 已离开 active queue | 用 `sacct` 查历史 | 说 Slurm controller down |
| 长时间 pending | `Priority`/QOS/user GPU limit | 报告 exact reason 与 start estimate | 当成 evaluator 卡死 |
| 18 分钟任务申请 8 小时 | 沿用保守模板 | gate 后按实测改为 1 小时 | 用 requested time 推算真实 compute |
| `scontrol ... TimeLimit` 报 `Unspecified error` | 集群拒绝用户态原地修改该 array | 仅取消 pending，exact resubmit | 取消 completed/running 或重开 population |
| server `Address already in use` | port precheck/bind TOCTOU | retrying launcher + receipt | 改方法或忽略失败 task |
| source episode 为零 | host root 与 overlay root 混淆 | exact container + overlay preflight | 替换 scene 或放宽冻结条件 |
| evaluation 找不到 parquet | eval SBATCH 漏挂 overlay | 三阶段统一 mount contract | 认定数据不存在 |
| bundle import 缺文件 | 只打包入口，未递归闭包 | import closure audit + 新 immutable bundle | 原地补文件到冻结 bundle |
| nested checksum 搬家失败 | receipt 含生产机绝对路径 | relative receipt + relocated verification | 只信外层 bundle hash |
| empty scene builder 报错 | builder 错把合法零 history 当异常 | 输出 audited empty fragment | 借用别的 scene episode |
| readonly bundle 语法检查失败 | `py_compile` 写 `__pycache__` | 临时 pycache root 或 AST audit | 把 bundle chmod 回可写 |
| EGL context 创建失败 | 覆盖 `LD_LIBRARY_PATH` 丢失 `--nv` NVIDIA EGL | 保留注入库路径，exact EGL smoke | 归因于某个 GPU family |
| renderer 从毫秒变 19 秒 | 异步 CUDA HTTP handoff | response 前显式 synchronize | 归因于 Pi3X 能力或显存不足 |
| Habitat `core dumped` 且 depth cast warning | 原生 simulator/runtime abort；该次无完整 arm summary | 保留 partial/log/buffer，exact-index retry | 把 partial outcome 计入 SR |
| summary 因上游失败被取消 | `afterok` 正常 fail-closed | 修复 exact failed task 后重建 dependency | 绕过依赖直接汇总不完整分母 |
| summary 假设每 scene 2 条而实际 4 条 | hard-coded population size | 从 frozen manifest 读取 `episodes_per_scene` | 手工删记录迎合旧代码 |
| diagnostic 缺 `requests` 等包 | 使用了错误 interpreter/环境 | 绝对 interpreter 路径 + dependency import smoke | 临时在正式环境无记录安装 |
| `config.json not found` 等 warning | 不一定是 fatal；Pi3X server 后续可正常 ready | 结合 exit code、ready receipt 和 arm completion 判断 | 看到 warning 就宣布方法失败 |

## 9. 标准的提交前与结果后检查表

### 9.1 提交前

- [ ] `ssh -G`、`ssh -O check`、`id -un`、`hostname` 已核验；
- [ ] source bundle 与所有 nested receipts 在目标路径通过 SHA-256；
- [ ] 完整依赖与构建产物已准备，实际解释器和包路径正确；shell syntax、CPU 预检已通过；
- [ ] exact container、`--nv`、overlay、bind mounts 和 parquet 可读性已通过；
- [ ] partition/account/QOS/GPU/CPU/memory/time/array cap 已逐项确认；
- [ ] 完整配对 gate 连同归档、独立校验已通过；耗时及 RAM/VRAM 峰值已记录；
- [ ] 长历史、目标切换与多臂常驻需求已覆盖；新运行栈的小批量运行无新增故障；
- [ ] 用户字节/文件数配额、临时空间和计算节点输出可写性已检查；时限包含收尾余量；
- [ ] run root 不存在，输出路径不会覆盖旧 attempt；
- [ ] summary 和 independent verifier 使用 `afterok` 串联；
- [ ] 大文件已决定走 Globus，小 bundle 才走 SSH copy。

### 9.2 运行中

- [ ] 同时报 `completed / running / pending / failed` 数量；
- [ ] pending 报 exact Slurm reason；
- [ ] 记录节点与 GPU identity；
- [ ] 查看当前 arm，但不根据 partial outcomes 调方法或筛 population；
- [ ] 查看动作/请求进度、最新落盘时间和资源增长，不能只凭 GPU 利用率判断健康；
- [ ] 超过 60 秒的命令继续 poll 原 session，不重复提交；
- [ ] 发现 partial failure 时先保全现场。

### 9.3 完成后

- [ ] 所有预期 `completion.json` 数量与 manifest 一致；
- [ ] 每个 completion SHA 与 `.sha256` 一致；
- [ ] array 所有 scientific elements exit `0:0`；
- [ ] summary 成功且分母、paired fields、cluster 统计正确；
- [ ] independent verifier 返回 `verified=true`；
- [ ] 从持久存储重新读取并校验归档后，才清理本作业的临时数据；
- [ ] runtime incidents 单独记录，不混入方法结果；
- [ ] 最后才报告 aggregate SR、paired gain/loss、McNemar 和 cluster CI。

### 9.4 给收尾留时间，中断后保留可补跑的记录

申请的 walltime 应覆盖 **准备 + 运行 + 校验/归档 + 余量**。应用层截止时间要早于
Slurm 硬上限，并预留实测的收尾时间。例如现有
[Table I wrapper](run_table1_repaired_hpc.sh)在一小时作业内为 evaluator 设置
48 分钟超时，随后归档并保留原退出码；前面的准备也占总时限，不能据此假定总有
12 分钟可收尾。更长历史、更大输出和更慢 GPU 都要重新估算。

每项任务使用独立的临时目录、端口和输出目录。启动 Python 前设置可写且有空间的
`TMPDIR`、`LIBFFI_TMPDIR` 与 bytecode/cache 路径。检查用户配额和文件数，也检查
节点临时盘；§12 的 `MemoryError` 实际来自满的 `/tmp`，扩大 RAM 申请没有帮助。
归档目的地要从实际计算节点验证；§15 中 `/archive` 只能由登录节点写入，计算作业
须先落到可写的持久 scratch，再完成归档。

新 runner 的落盘策略应先经过小规模验证：完整配对完成后及时保存输出与哈希，
确认必需文件齐全后才发布完成标记。失败路径也保存日志、配置、进度和非零退出码；
节点临时盘不是备份。大数组尤其要避免“算完全部任务才第一次复制结果”。
已有 runner 的实现不完全相同：
[bearing wrapper](run_gem_reviewer_paper_controls_hpc.sh)直接调用 evaluator，
没有 Table I wrapper 的外层超时与归档步骤，使用前应核对整条调用链的收尾行为。

为新的收尾逻辑安排一个隔离工程测试，验证子进程失败或提前退出时能否保存现场、
释放本任务服务并正确失败；不要用正式运行测试取消。强制终止不一定会执行清理，
因此定期落盘与提前截止都需要，不能只依赖退出时的 `trap`。

出现故障先看 Slurm 状态、最后进度和日志，再决定补跑范围。`SIGABRT`、OOM、
超时、输入错误和校验失败分别处理；完整配对未结束就不发布结果。
[连续运行故障记录](REPAIRED_HM3D_CONSTRUCTION_RUNTIME_AUDIT_20260909.md)说明，
import、短渲染与模型 ready 全部通过，也不能排除几十个动作后的故障。
先在原配置下定位或验证兼容运行栈，再按 §2.5 补跑；增加时限不能修复崩溃，
换 GPU 也不能修复请求解析错误。

## 10. 本项目的标准路径

- immutable bundles：
  `/scratch/yz11502/Research/Nav-axis-uturn-source-bundles/`；
- run roots：
  `/scratch/yz11502/Research/Nav-axis-uturn-results/<experiment>/<RUN_TAG>`；
- Slurm logs：
  `/scratch/yz11502/Research/Nav-axis-uturn-results/slurm_logs/`；
- Habitat interpreter：
  `/scratch/lg154/conda-envs/habitat/bin/python`；
- model/server interpreter：
  `/scratch/lg154/conda-envs/memnav/bin/python`；
- standard Singularity image：
  `/share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif`。

HPC 上不要 `conda activate`，统一使用绝对 interpreter 路径。状态改变命令优先通过
已验证的共享 PTY；read-only 查询可通过正常工作的 no-PTY channel。本文应作为以后
所有 HPC 工作的强制 preflight 与故障分类入口。

## 11. 用户文件数配额与全盘空间（2026-09-06 核验）

Torch 上先运行站点命令 `myquota`。`quota -s` 可能因 NFS 权限返回
`Operation not permitted`；这不表示无法检查配额，也不代表配额无限。

本轮 yz11502 实测：scratch 1.37TB/5TB（27.39%），文件数
4,897,908/5,000,000（站点显示97%）；与此同时 `df -h /scratch` 显示全盘仍有603TB。
所以 `Disk quota exceeded` 的检查必须同时看 **用户字节配额和文件数配额**，
不能拿 `df` 的全盘剩余容量排除配额问题。以上只是2026-09-06快照，不是长期常数。

逐帧JPEG、重复runtime、源代码/依赖快照都应估算文件数预算。只对已确认的实验目录
做 `du --inodes -s EXACT_RUN_ROOT`；该命令包括目录，链接复用的run也不代表被引用
源目录的全部占用。避免无目的地递归扫描整个scratch。

准备新的长任务时，优先评估节点临时空间录制、结束后按query/arm归档持久化的可行性，
并保留内部文件SHA与可恢复索引；这是待验证的存储方案，不可未经verifier兼容检查
直接改变冻结产物布局。不要自动删除旧失败/成功记录来换空间；先确定恢复与保留范围。

## 12. 2026-09-08：`MemoryError` 也可能来自满的临时文件系统

在 `torch-login-a-0`，Habitat Python 3.9 导入 `quaternion → numba → llvmlite`，
在创建 `_ObjectCacheNotifyFunc` 时出现 `MemoryError`，host 和标准 container 都复现。
独立的 `ctypes.CFUNCTYPE(None)(lambda: None)` 已能复现，模型和 GPU 尚未加载。

同一时刻：`free -h` 显示约 83 GiB 可用，`ulimit -v` 为 unlimited，
但 `df -h /tmp` 为 2.0G/2.0G、100%。为本任务创建独立临时目录，并仅对子进程设置
`TMPDIR` 和 `LIBFFI_TMPDIR` 后，同一个解释器的 callback、quaternion、Habitat 导入都通过。
不能把这个异常称为模型显存不足，也不需要重装共享 conda。

诊断顺序：

1. 检查 `free -h`、`ulimit -v`、`df -h /tmp /dev/shm`。
2. 用实际解释器执行无模型的最小 callback 测试，再导入 Habitat。
3. 登录节点的少量预检可以在本任务精确 scratch 目录下 `mktemp -d`，
   将上述两个变量传给子进程；不要清理他人 `/tmp` 文件。
4. GPU 作业在任何 Python/FFmpeg 预检之前创建自己的 node-local 临时目录，
   设置 `TMPDIR`/`LIBFFI_TMPDIR`；逐帧 buffer 仍放节点临时盘，不迁回高文件数的 scratch。

这条只说明已验证的基础设施案例，不表示所有 `MemoryError` 都由 `/tmp` 占满造成。

## 13. 2026-09-08：新图像审计不能假设 Habitat 已安装 OpenCV

旧 evaluator 主要用 PIL/ImageIO；本轮深度栅格审计和视频入口用到 `cv2`。
实际 Habitat Python 3.9 没有 OpenCV，MemNav Python 3.10 有已运行的 headless 4.9.0。
因此旧任务完成不代表新增图像入口的依赖已经齐全。

本轮只把现有 `cv2` 及 `opencv_python_headless.libs` 复制到任务专属只读依赖目录，
绑定 SHA，并在原 Habitat Python 3.9 / NumPy 1.26.4 下验证 abi3 导入和 resize。
没有安装、升级或修改任何共享 conda 环境，也没有把另一解释器的整个 site-packages
混入 Habitat。新依赖由 `REPAIRED_HAB_EXTRA` 显式传递给所有 Habitat 子进程。

依赖路径：`/scratch/yz11502/Research/Nav-axis-uturn-source-bundles/repaired_hab_cv2_20260908`。
该目录不通用于任意 Python/NumPy 版本；其他组合仍需实际解释器验证。

## 14. 2026-09-09：连续运行故障不能用 import / 短渲染预检排除

修复版 HM3D `17196996_1` 通过全部导入、CLI、双场景渲染与模型启动后，
仍在 H100 gh008 出现约 19 秒 memory HTTP 完成间隔，56 步后 evaluator SIGABRT。
同一 bundle 的 shard 0 在 H100 gh003 正常完成，不能据此把所有 H100 归为故障节点。

本项目已有相似故障转 A100 补齐的实际记账：`17089916` 九项和 `17089989_16`
全部 COMPLETED。本次 exact shard retry `17201733_1` 因此显式使用
`safe_sbatch --partition=a100_tandon --array=1`，原代码/参数不变，仅增加
`PYTHONFAULTHANDLER=1`。不要只复用通用分区默认值而遗漏已有事故的运行规避记录。
也不要把该规避直接称为根因修复；状态以新终局和 verifier 为准。

若需进一步定位，记录连续 render、memory HTTP、planning HTTP 分项时间及 abort 堆栈；
HTTP 日志间隔不等于模型 forward 延迟。短渲染成功或依赖预检通过不等于 GPU/渲染
持续交接已稳定。仅补失败项，保留原失败输出，不靠加大时限或改导航参数掩盖异常。

本次 A100 重试最终 ga015 / 4:59 / COMPLETED，两条 A 均成功，verifier=true，
不再有持续 19 秒间隔。记录为本次运行规避成功；H100 根因仍未经过同卡受控验证。

## 15. 2026-09-09：大量 runtime buffer 的可恢复清理

scratch 达到 4,909,485/5,000,000 文件，而字节仅约 1.38/5 TB。只处理已解析的旧
runtime buffer，不删除数据集、模型、在线历史、冻结 bundle 或 metrics/trace/verifier。
对每个确切 buffer：归档全部文件及 SHA → 完整回读 → 核对原文件未变化 → 删除散文件。
原位置留下 `buffer.ARCHIVED_20260909.json` 恢复指针。

`/archive/yz11502` 在本次登录节点可写，但 CPU 试任务 `17243007_4` 的访问检查失败，
尚不能假设所有计算节点都挂载/允许访问它。该失败在删除前发生，没有数据损失。
已验证的两步流程是：计算节点先写 scratch `verified_archives/`；登录节点再转存
`/archive/yz11502/nav_runtime_buffers_20260909/`，核对完整包 SHA 后移除 scratch 重复包。
前一步主要释放文件数，后一步释放 scratch 字节；不要把“已压缩”写成“已转存”。

具体清单、恢复办法与作业状态见 `HPC_STORAGE_CLEANUP_20260909.md`。归档不是永久
备份承诺，仍受站点保留政策约束。新 eval 应在 node-local 写逐帧证据并按完整任务归档，
避免再次积累数百万散文件。

## 16. 2026-09-09：safe_sbatch 默认值也可能覆盖脚本分区

本次脚本明写 `#SBATCH --partition=a100_tandon`，但未传 CLI 分区时，
`safe_sbatch` 实际提交为 `a100_tandon,h100_tandon`。test-only 输出某个 A100
预计节点，并不证明允许分区只有 A100。必须提交后读取 `scontrol show job` 的
`Partition=`、`TimeLimit=`、`ReqTRES=` 和依赖。

`17253413/17253414` 在 PENDING、0 秒且无节点分配时发现此问题；原地修改分区
返回 `Unspecified error`。仅撤回这两个未启动数组，显式传入
`--partition=a100_tandon --account=torch_pr_769_tandon_advanced --qos=gpu48`
及原 GPU/CPU/memory/time 参数后，重交为 `17253441/17253442`。
实际回读仅 A100，源码、目标、seed 不变；撤回作业没有导航输出。

之后不可仅依赖 SBATCH 文件默认值或 test-only 的预计节点判断运行分区。

### 数组并发更新：错误输出之后也要核对实际状态

同日对17240715调整`ArrayTaskThrottle`时，`scontrol`对已展开元素返回
`Unspecified error`，但父数组和待启动范围已实际变为`%2`、随后`%1`；已有运行元素不中断。
因此既不能仅凭错误文本认定“完全没改”，也不能假设“全部成功”：
读取父数组`ArrayTaskThrottle=`、`ArrayTaskId=`以及运行/等待元素再判断。
这与上面的分区修改不同：分区当时实际没有改变。降低并发只是让其他任务有调度机会，
不是GPU预留；临时调整须记录恢复点，不修改冻结目标、种子或方法参数。

## 17. 2026-09-11：已认证 PTY 正常，SCP 新通道仍超时

本次默认 `yz11502` master 正常；显式 PTY 在 `Last login` 后暂时没有提示符。
只向**自己新开的 PTY**发送一次 Ctrl-C 后，正常得到 `id -un=yz11502` 和
`torch-login-a-0`，`squeue`、`myquota` 都可用。不关闭 master，不切到其他账户 socket。
随后两次有时限的 SCP 均超时，远端目标文件不存在。不能由此宣布 HPC/MFA 失效。

对本次 3.65 MB 源码包和小型 plan，使用相同 master 的 localhost-only **反向转发**：

1. 工作站只读 HTTP server 绑定 `127.0.0.1:46150`，根目录限定为本次打包目录，
   不使用 Research、用户目录或含凭据的目录。
2. 在共享 master 添加 `-O forward -R 127.0.0.1:46151:127.0.0.1:46150`。
3. 已核实身份的 HPC PTY 用 `curl --fail --max-time 45 http://127.0.0.1:46151/精确文件名`
   下载到事先核实不存在的新目标。两端的包/plan SHA-256 完全一致后才解包预检。
4. 结束后通过相同 master `-O cancel -R 127.0.0.1:46151:127.0.0.1:46150` 撤销转发，
   并停止自己启动、记录了精确 PID 的本地 HTTP server。不得停止其他服务或共享 master。

这与第 1.4 节的只读下载方向相反，但仍只有 localhost 可访问，流量经过已有 SSH。
只用于小源码/收据的传输恢复，不替代大型数据集和模型的 Globus 路径。

## 18. 2026-09-11：JPEG SHA 不一致也可能来自 multipart 分块解析

Table I 两个任务换 A100 节点后仍在相同位置失败。通过原归档复现发现：
请求体长度均为 65,539 bytes，Werkzeug 3.1.8 的 multipart 解析会在 64 KiB
分块附近把分隔符 CR 加到 JPEG 尾部。158 的异常 SHA 精确等于“原目标 JPEG + CR”，
110 的历史 JPEG 则直接保存了额外 CR。两个案例解码 RGB 不变，但字节检查正确拒绝。

处理方式：本机 CPU 构造边界复现 → HPC 原输入复现错误 SHA → 进程内保留完整 CRLF
解析边界 → 精确字节复验 → 只补原失败配对单元。不是关闭 SHA 校验、strip 文件，
或已经推进模型状态后重复 POST。无需安装 conda 依赖或改共享包。

修复入口：`multipart_crlf_repair.py`；实际归档复现：`audit_table1_multipart_repair.py`；
状态：`TABLE1_MULTIPART_REPAIR_STATUS_20260911.md`。新的预检除 import 和 CLI 外，
应包含跨 64 KiB 的单图/双图上传；普通小图 smoke 不覆盖这一故障。

## 19. 2026-09-11：动态后处理依赖与已结束作业

本次只读查询 `scontrol show config` 得到 **`MinJobAge = 64 sec`**。
构造、汇总这类短 CPU 作业可能已经正常完成，但后续 CPU 调度器尚未获得资源；
等它启动时，上游编号可能已不在 `squeue/scontrol` 的活跃记录中。

动态衔接 B/C 和最终复算时：

- 先用 `sacct -X -nP -j JOB_ID --format=State,ExitCode` 核实真实状态；
- 上游仍 pending/running 时，继续使用 `afterok` 依赖；
- 上游已 `COMPLETED / 0:0` 时，无需再等待已完成事件，可在核对所属 plan/阶段后提交后处理；
- 失败、取消或查不到可靠状态时，不推断为成功，也不放行最终报告。

该处理仅作用于后处理调度，不重跑导航，不改 frozen manifest 或补造缺失结果。
实现：`table2_final_postprocess.py`；后处理只申请 CPU，并从原始归档独立复算 SR/SPL。

## 20. 2026-09-11：NavMesh 重载造成离线碰撞复算不一致

Table II 的 `17357681_21` 已完成导航，但 verifier 复放一帧碰撞时相差约 2.4 cm。
本机与 HPC CPU 复核确认：同一份逐字节一致的 NavMesh，现场重建时有 2 个连通区域，
保存后重新加载有 3 个。以原始 GLB/设置重建后，164 个执行落点全部精确复现。

遇到这种日志时，先核对控制请求与碰撞环境，不要直接重跑 GPU、改成功标签或放宽容差。
允许的补充复核必须证明重建网格与原归档逐字节一致，并通过完整轨迹/深度/目标审计；
原失败归档移至明确的 `failed_attempts` 目录保留。它不改变导航 controller 或 physics 合约。

本次 CPU 作业 `17365241` 用时 22 秒、`COMPLETED / 0:0`；另一次独立原始归档复算通过。
修复说明：`TABLE2_COLLISION_REVERIFICATION_20260911.md`。
代码：`reverify_table2_collision_task.py`、`slurm_table2_collision_reverify.sbatch`。

## 21. 2026-09-11：调整现有数组并发，不重提样本

Table II A 数组的资源等待除了分区 `QOSGrpGRES`，也出现自身的 `JobArrayTaskLimit`。
本次先实查 `gpu48` 单用户上限为 16 GPU、`a100_tandon` 分区 QOS 总上限为 60 GPU，
再对已确认属于本任务的数组 `17357681` 使用：

```bash
scontrol update JobId=17357681 ArrayTaskThrottle=4
scontrol show job 17357681
squeue -u yz11502
```

原并发 2 改为 4，随后确实看到四个元素同时运行。这个操作不新增数组，不重跑样本；
每项 A100 / 1 GPU / 1 h、样本、seed 和同机配对规则均保持不变。
原协议若写明并发数量，必须单独记录资源调度补充，不能悄悄改写旧协议或提交收据。

此次更新对已结束成员输出错误提示，但根数组读取到 `ArrayTaskThrottle=4`，
随后 `%4` 及四项 running 证实修改已生效。以实际状态核验，不能仅凭提示重复提交。
并发上限提高不保证 QOS 配额立即可用，也不能通过加入未经验证的分区绕过排队。
详见 `TABLE2_RESOURCE_SCHEDULE_ADDENDUM_20260911.md`。

## 22. 2026-09-11：连续双臂的显存不能沿用单臂估计

逐段共同发题要求两臂都保留活跃状态，不能再把“同一张卡依次 reset 跑两臂”的显存
视为本任务需求。本机 Table II 首例 native A 完成后，其 LingBot live allocation 为
14.34 GB；保留它并执行 GEM A 时，约 48 GiB 卡在另一臂深度头申请 66 MiB 时 OOM。
其他工作区当时仍占显存，未停止它们。

私有 `private_cuda_trim` 只在该服务空闲时释放未使用的 allocator 块；原日志中 reserved
从 24.21 GB 降至 14.75 GB，allocated 不变。这不能释放仍有引用的 KV、尺度或历史状态。
因此不能将此 OOM 误判为 conda 依赖错误、靠 reset 活跃 memory 规避，或用单臂成功当作
双臂持续运行的通过证据。已经结束的失败 episode 则可在完整写入收据后释放其私有服务。

对应首例按既有稳定运行记录选 A100 80 GB、1 h，在一个作业/节点/GPU 上完成两臂；
正式规模仍待实测。四个端口使用 `claim_slurm_tcp_port_block ... 4`，不硬占别的端口。

本次 SSH 仍是默认 master 和原已认证 PTY；SCP 新通道再次超时，3.73 MB 源码包通过
仅 localhost 的反向转发完成传输并核对 SHA。临时 HTTP server 和转发已立即关闭。
若新 PTY 需 Ctrl-C 恢复提示符，应先单独发送 Ctrl-C、等提示符，再发送 `id -un`；
不要把控制字符和身份命令连在一次输入里，以免命令首字符被吞掉。

## 23. 2026-10-24：新 Tandon 账户、分区与共享连接核验

本次从工作站执行 `ssh -G alantorch`，仍解析为 `yz11502@login.torch.hpc.nyu.edu`，
ControlPath 仍为第1节的权威默认路径。起初socket不存在，普通交互登录要求Microsoft
设备验证；用户完成后 `ssh -O check` 成功。复用此master的PTY进入
`torch-login-b-1.hpc-infra.svc.cluster.local`，实际 `id -un=yz11502`。登录启动阶段曾暂时
停在Last login；仅向自己新开的PTY发送一次Ctrl-C后正常出现提示符。没有使用其他
账户socket、关闭master或更改SSH配置。设备码不写入持久记录。

远端日期使用EDT，本次关联查询发生在远端2026-10-23晚、北京时间2026-10-24。
`sacctmgr -nP show assoc where user=yz11502 format=Cluster,Account,User,Partition,QOS,DefaultQOS`
当前列出：

```text
torch_pr_50_general
torch_pr_50_tandon_advanced
torch_pr_50_tandon_priority
torch_pr_54_general
torch_pr_54_tandon_advanced
users
```

已查询的账户说明中，`torch_pr_50_tandon_advanced`和`torch_pr_50_tandon_priority`
的本次description均为`scene-x`，
`torch_pr_54_tandon_advanced`为`navigation`。账户归属、关联、可提交参数与实际可用额度
是不同信息。关联输出虽然显示QOS为`normal`，站点job-submit插件仍拒绝GPU作业显式
使用`--qos=normal`；必须通过实际参数的`sbatch --test-only`检查。

以下组合已于本次通过 **test-only参数/权限预检**：

| Account | Partition | QOS | 本次请求 |
|---|---|---|---|
| `torch_pr_50_tandon_advanced` | `h200_tandon` | `gpu48` | `gpu:h200:1`，4CPU，64G，10min |
| `torch_pr_50_tandon_advanced` | `h100_tandon` | `gpu48` | `gpu:h100:1`，4CPU，64G，10min |
| `torch_pr_50_tandon_priority` | `a100_tandon` | `gpu48` | `gpu:a100:1`，4CPU，64G，15min |
| `torch_pr_54_tandon_advanced` | `h200_tandon` | `gpu48` | `gpu:h200:1`，4CPU，64G，10min |
| `torch_pr_50_general` | `h200_public` | `gpu48` | `gpu:h200:1`，4CPU，64G，10min |
| `torch_pr_50_tandon_advanced` | `a100_tandon` | `gpu48` | `gpu:a100:1`，4CPU，64G，8min |
| `torch_pr_54_tandon_advanced` | `a100_tandon` | `gpu48` | `gpu:a100:1`，4CPU，64G，8min |

以上没有创建作业，不是运行栈/GPU gate通过记录；test-only打印的Job数字与预计启动
时间也不是已提交作业或资源预留。实际提交仍须指定完整资源并读回`scontrol`。

可复核的短请求示例（仅预检）：

```bash
sbatch --test-only \
  --partition=a100_tandon \
  --account=torch_pr_50_tandon_priority --qos=gpu48 \
  --gres=gpu:a100:1 --cpus-per-task=4 --mem=64G --time=00:15:00 \
  --wrap=/bin/true
```

`priority`不是通用分区通行证。本次该账户搭配`h200_tandon`、`h200`、`h200_plus`、
`h100_plus`或`b200`/`b200_tandon_prem`的所测组合被站点插件拒绝；不能因为`sinfo`
可见或`AllowAccounts=ALL`就推断可提交。当前可见`b200_tandon_prem`，但本次没有
验证其合法账户/QOS组合，也没有验证ABot旧CUDA12.4/SM90扩展对B200的兼容性。

本次`squeue -u yz11502`初查为空；没有取消或修改其他作业。配额快照为scratch
2.92TB/5TB、4,307,480/5,000,000文件，home16GB/50GB；它们会变化，后续仍需重查。
登录节点未发现`rg`，远端查询继续使用`grep/find/sed`。ABot历史成功栈与路径由
`research/abot_reproduction/pfw_hpc_gate_notes_20261024.md`记录，但新GPU型号、扩展、
精度/backend或训练路径均需单独gate，不能把上述提交预检当作方法验证。

该账户组合随后有一次实际ABot工程验证：`torch_pr_50_tandon_priority/a100_tandon/gpu48`
的job **20778758** 在ga015的A100-SXM4-80GB完成，申请15min、实际65s、ExitCode0:0，
独立verification=true；CPU依赖job20778756用59s完成。该栈是PyTorch2.5.1+cu124、BF16、
显式native PyTorch RoPE2D，验证了原生关闭等价与低分辨率反传，未执行optimizer更新。
它不是SM90 CUDA扩展、B200、Habitat/EGL或正式训练质量的验证记录。原报告位于
`/scratch/yz11502/Research/abot_pfw_goal_20261024_001/outputs/GPU_001/`，本地回读位置见
`research/abot_reproduction/ABOT_PFW_RESEARCH_PROPOSAL.md`第17节。

同栈的后续job **20783840** 在ga002以1A100、8min上限完成，实际122s、ExitCode0:0、
独立verification=true；包含234帧原生前向归档和16帧全分辨率PFW-on工程检查，
仍为零optimizer更新。此前`QOSGrpGRES`与未来预计启动时间只是排队快照；随后实际
由Backfill启动，无需重复提交。完整范围与结果以proposal及原始收据为准。

## 24. 2026-10-25：Tandon实际运行与终态作业依赖

本次继续复用第23节已认证的ControlMaster与同一ControlPath，没有关闭共享master、
改写SSH配置或重新触发设备认证。`torch_pr_50_tandon_priority/a100_tandon/gpu48`
又完成实际A100-SXM4-80GB运行：校准job **20813448** 用664s完成；反向审计job
**20816878** 用443s完成，均ExitCode0:0。资源为1A100、4CPU、64G、15min上限。
前者不是训练质量评测；后者验证固定图的反向执行合同，范围以
`research/abot_reproduction/ABOT_PFW_RESEARCH_PROPOSAL.md`第18节及收据为准。

`QOSGrpGRES`期间保留单个待运行作业；本轮再次观察到它随后被Backfill启动。
`--test-only`的预计时间仍不代表实际排队承诺，不据此反复复制GPU任务。

终态作业可能已从`scontrol`移除，尽管`sacct`和完成收据仍保留。本轮为已完成的
`20816878`追加`afterok`时收到`Job dependency problem`，没有创建新作业。
此时先核对`sacct`、completion及verification和源码/输入哈希，再提交CPU准入；
GPU继续依赖新CPU作业。不要为重新获得依赖ID而重跑已完成GPU工作。本轮拒绝与
处理记录保存在`/scratch/yz11502/Research/abot_pfw_goal_20261025_001/`的
`strict_dependency_rejection_001.json`及`strict_recovery_submission.json`。

两次有界`myquota`查询本轮超时；第23节2.92TB/5TB等数字仍是旧快照，不能当作
本轮配额核验。新增状态、派生统计和compact checkpoint的实际范围记在项目收据中。

同账户组合的严格反向恢复job **20817909** 随后在ga006完成，实际476s、ExitCode0:0、
verification=true。它仅在backward作用域启用严格确定性，避免把cuDNN设置误当作
整个attention反向的确定性保证；原默认策略失败仍单列。该工程验收未改变共享环境、
源代码checkout或CUDA扩展，未运行正式质量训练。完整范围见项目的
`pfw_strict_recovery_summary_20261025.json`。

## 25. 2026-10-25：MiTA v2原生工程检查与当前QoS快照

本轮继续先核对`ssh -G alantorch`和默认`ssh -O check`，复用原master
pid1351507及第1节ControlPath。独立observer PTY进入后再次确认`id -un=yz11502`、
`torch-login-b-1`；没有新建master、改SSH配置或重新触发设备认证。

新工作目录为`/scratch/yz11502/Research/abot_pfw_v2_native_20261025_001`，
`source_001`含83个文件，旧native150文件另验。小型源码与收据通过同一master的SCP；
原4GB基础checkpoint和RGB-D继续从原只读路径读取，未复制。只有本次约60MiB的compact
工程产物回读作本地哈希核验，不建立第二份完整模型或特征库。

实际作业均ExitCode0:0：CPU预检20829816（90秒，32tests与真实256帧schema），
配对GPU20832950（ga002，71秒），恢复GPU20836392（ga001，290秒）。GPU仍为
`torch_pr_50_tandon_priority/a100_tandon/gpu48`、1A100、4CPU、64G、15min上限，
PyTorch2.5.1+cu124与显式Torch RoPE2D。这里只记录运行栈与完整恢复工程范围；
三维任务效果和速度结论仍未建立，详见
[`ABOT_MITA_NATIVE_INTEGRATION_20261025.md`](../research/abot_reproduction/ABOT_MITA_NATIVE_INTEGRATION_20261025.md)。

再次遇到成功父作业已从controller清除：本轮没有重跑已完成的神经检查，而用只读receipt
核验CPU作业20832949、20836389作为新的`afterok`准入，并保存实际wrap命令和提交记录。
两项GPU始终顺序运行，无重复候选作业。`QOSGrpGRES`期间保留原任务，随后正常启动；
H100/H200的test-only预计时间并未促使更换运行栈。

本轮`sacctmgr`的新快照为：

```text
gpu48:       MaxTRESPU=gres/gpu=2
a100_tandon: GrpTRES=cpu=1184,gres/gpu=60,mem=14500G
h100_tandon: GrpTRES=cpu=1440,gres/gpu=60,mem=22500G
h200_tandon: GrpTRES=cpu=1792,gres/gpu=112,mem=28000G
```

这不是永久配额；特别不能把§21的旧16GPU/user快照作为当前值。查询命令为
`sacctmgr -nP show qos where name=gpu48 format=Name,GrpTRES,MaxTRESPU,MaxJobsPU`，
分区QoS同理按名称查询。`sinfo`物理资源与分区QoS上限仍应分开核对。

`timeout 15 myquota`本轮打印了home16GB/50GB、scratch2.92TB/5TB及
4,308,011/5,000,000文件，但在随后top-directory查询阶段超时，退出码124。
可保存已打印行作为该时刻快照，不能将整个命令称为正常完成。`df`显示的scratch
222TB剩余是文件系统总量，不是个人额度。

本轮收据与完整Slurm提交/终态账保存在上述新目录；本地回读位于
`.workspace-assets/abot_reproduction/pfw_v2_native_goal_20261025/`。收尾只退出本轮observer，
不关闭共享ControlMaster或其他账户连接。

## 26. 2026-10-25：v2训练校准、符号链接路径与有界主范围计价

本轮再次先执行`ssh -G alantorch`、默认`ssh -O check`，仍复用pid1351507的
`yz11502`共享master与第1节ControlPath。本轮observer PTY确认身份后进入
`torch-login-b-1`，未改SSH配置、关闭其他账户socket或发起新的设备认证。

新目录为`/scratch/yz11502/Research/abot_pfw_v2_research_20261025_001`。
先封存96文件source_001，发现CPU receipt checker对路径alias的误判后，保留原目录，
另建source_002；原native150文件、4GBcheckpoint及数据继续只读引用。源码和小收据
继续通过同一master的SCP传输，长训练不在登录节点执行。

CPU作业20843679的producer完成真实输入检查，但独立checker失败；原因是
`processed_tartanground_population_001/House...`是指向另一处理目录的符号链接，
catalog保存`Path.resolve()`后的路径，checker却要求它与声明alias字符串相等。
这不是输入内容、GT或模型失败。修复保留固定场景名、source-manifest SHA、连续帧ID、
逐文件路径与摘要核验，只移除对绝对父目录字符串的错误相等要求，并新增回归。
不能在没有内容身份核验的前提下仅按basename接受任意目录。

原三个GPU依赖和一个CPU merge候选20843680–20843683均未启动，确认PENDING后精确取消；
所有失败收据、旧source与日志保留。source_002重新以20844182完成CPU准入，32tests通过；
同一有界计划的新依赖链是校准20844183→20844184→CPU merge20844185→主范围计价20844186。
三个实际GPU任务仍各1A100/4CPU/64G/15min，应用上限780秒，没有扩大GPU工作预算。
CPU的producer=`pass`不等于Slurm作业成功，必须等最后的independent verifier也退出0。

本轮新读回的QoS快照为`gpu48 MaxTRESPU=gres/gpu=16`，与§25较早的2不同；
两者保留各自时刻，不把任何一份快照当永久额度。scratch此时仍约2.92TB/5TB，
4,308,147/5,000,000文件；完整query与退出码保存在`journal_001/access.json`。
调度预估不是承诺；本轮GPU test-only给出较晚时间，实际第一校准仍由正常调度开始。

方法、成本和最终终态记录见
[`ABOT_MITA_CALIBRATION_AND_ADAPTATION_PLAN_20261025.md`](../research/abot_reproduction/ABOT_MITA_CALIBRATION_AND_ADAPTATION_PLAN_20261025.md)。
本节不把训练校准或一次optimizer更新称为三维任务收益。

本轮终态：校准20844183在ga016用209秒、20844184在ga001用190秒，主范围计价
20844186在ga012用146秒，均COMPLETED/0:0及独立verification=true，合计545秒
（0.151389 GPUh）。实际仍是A100-SXM4-80GB、Torch2.5.1+cu124、Torch RoPE2D。
`QOSGrpGRES`期间保留原主范围任务，随后正常调度，没有复制任务或改用其他GPU。

CPU20844182实际141秒；merge20844185实际26秒，最终Partition由站点调度为`cs`
（保存的原提交为`cpu_short`），没有人工改分区。等待GPU期间增加一个单独有界的
4CPU/16G/5min数据schema验收20845421，在cs632用192秒完成，未使用GPU或运行神经模型。
四个实际CPU作业含首次失败149秒，共508秒；不要漏计失败，也不要重复算作业step。

原两个scalar normalizer NPZ约220MB继续留在HPC，它们不含QKV；没有复制基础模型或
特征归档。本地仅回读约1.13MB的JSON、日志、提交链和数据catalog压缩收据，SHA256为
`c0a65489f7ea4fd93c5660101df50da005a82d448e5296f6b1f0bccc09892842`。
远端CPU独立完成全部数值拟合核验；缺NPZ的本地复核明确只报告metadata核验。
终态`squeue -u yz11502`为空；只退出本轮observer，不关闭共享master。

## 27. 2026-10-25：主训练跨步残留图导致OOM，修复单独封存

本节是基础设施故障记录，不是方法效果。ABot五臂训练20853047在ga020失败，
实际5086秒、1GPU、ExitCode1:0；C2第6步原loss分配失败，此前53次Adam更新完成。
不能把它记为完整五臂试验，也不能只凭OOM判断单步模型放不下。

实际每臂结束已执行GC/empty_cache，但活跃显存A为67108864B，B64为16873673216B，
Bfull为33695536128B。逐步CPU弱引用试验定位到prediction的反向租约hook强引用
operation→target_result→历史计算图；Python GC不能发现全部跨C++autograd的引用环。
新增入口仅在关闭租约后清空该operation，保留过期反向拒绝机制；旧封存源码不改。
四reader的CPU loss、梯度、慢参数、Adam与RNG逐值等价检查通过。

修复bundle `MATCHED_RETRY_SOURCE_001`共153文件，manifest为
`3d40cad13f41e2fbbd3a29a7be258bb5499b5571a095aef0b80314b3604cadea`。
CPU20861985实际121秒、65项检查及真实输入准入通过。完整五臂重跑20861986在ga012
启动，仍为`torch_pr_50_tandon_priority/a100_tandon/gpu48`、1A100、4CPU、64G，
本次上限3小时，不自动重试。新增watchdog在每次更新返回后检查活跃显存，
增长超过本臂首步512MiB或整臂释放后超过1GiB即保存失败并退出；其开销另列。
早期B64四步最大增长3848192B，A释放后64MiB。全部五臂和各次释放尚待完整验收。

原依赖20854385/20854386被Slurm取消、Elapsed0、无分配，不能按请求时限计GPU小时。
取消证明单独核Start Unknown、NodeList None assigned、AllocNodes0；严格的已分配作业
账本解析器不得仅凭空AllocTRES猜零。新续训CPU20862626、GPU20862627只在本次重跑
和CPU检查均成功后执行，GPU请求9000秒；不复制正在运行的候选作业。

新一轮10GPU小时按主作业实际elapsed×GPU数累计，包含失败及分配内加载，不重复算
`.batch/.extern`，不计排队。5086已结算秒加运行/依赖任务完整时限的预留上界为24886秒，
该上界不是已使用时间。此前§26的545秒单列为上一轮已完成任务。本轮小收据和失败
输出均保留，基础权重及大checkpoint继续留在HPC，不关闭共享SSH master。

## 28. 2026-10-25：UID0取消后的共同边界恢复

第二次五臂作业20861986在ga012由UID0取消，SIGTERM日志与sacct终态一致：
`CANCELLED by 0`，实际8268秒，低于10800秒时限。没有第二次OOM证据。
原report因突然终止仍为running，保留原字节；79次已确认Adam中，前四臂各16、
D2仅15。五臂的own8及0/8评测全部存在。原检查器CPU20873964用32秒真实核对
全部9个已登记compact的SHA/大小、source/native与现存评测合同，结果
`metadata_verified=true, partial=true, verified=false`；这不等于完成16。

Slurm的Reason是最后的阻塞原因，不能把本次字段QOSGrpGRES当作取消因果。
[Slurm sacct说明](https://slurm.schedmd.com/sacct.html)明确给出该定义。
[NYU当前提交说明](https://services.rt.nyu.edu/docs/hpc/submitting_jobs/slurm_submitting_jobs/)
列出了ga节点低GPU利用率自动取消政策；本job的batch TRES有gpuutil=71，
该单一汇总值不能证明或排除瞬时/窗口政策触发。本次具体取消原因仍未确认，
不联系或冒充管理员，不用无意义GPU计算掩盖利用率。

新科学执行scope单独封存为`RECOVERY16_SOURCE_001`和`RECOVERY32_SOURCE_001`，
两者相同182文件manifest为
`134ad4d8343ac942b90de12b2bbaf17b3f98bb3f43aa49abdcc187cfe10f09ee`。
模型、loss、训练scope、LR、精度和容量均保持原规则；恢复语义明确：
五臂分别加载自己的完整Adam/RNG/sampler8，统一重跑9–16，再从新共同16继续17–32。
旧79中保留40、回滚39，回滚成本全部保留。每个新终点仍在一个GPU分配内
完成全五臂，不拼接旧四臂16与新D2。完整Adam/RNG需要新增phase8准入，
原partial checker只校验compact字节，不能替代此检查。

本地新增helper/driver/checker16项和入口原11项CPU测试通过；HPC实际准入须另行
记录。提交链为CPU16 **20875365** → GPU16 **20875366**（6000秒）→
CPU32 **20875367** → GPU32 **20875368**（8100秒），均afterok并自动取消无效依赖。
CPU32在父GPU终态后重新从sacct生成实际账本，不使用过期预留。GPU只采样
CUDA_VISIBLE_DEVICES指定的本次单个GPU，每10秒记录一次util/memory/power；
退出只清理该observer的PID。SIGTERM仅尽力写partial，不保证KillWait内落盘，
不在半个Adam更新中保存可恢复权重。

新GPU脚本遵循当前NYU文档的默认自动分区路由。2026-10-25实测
`torch_pr_50_tandon_priority + gpu:a100:1 + gpu48`在不显式给partition或显式
a100_tandon两种test-only下均被接受并路由a100_tandon；test-only不分配GPU，
开始时间和Preempts列表只是调度预测，不能据此手动取消别人的任务。
同项目advanced账户的H100/A100 test-only也被接受，但当时预测更晚，未提交
重复候选，仍使用priority账户。历史§23显式组合保留为当时记录。

旧依赖20862626/20862627及20854385/20854386均未分配GPU，已取消。已结算
两个真实GPU作业共13354秒（3.709444GPUh）；加入上述两新请求的完整上限，
预留上界27454秒，仍不是已用时间。取消小收据归档SHA256为
`3d10af05dcc20f8a73f6c7fabd5baf97dde3c11ed8ade62cbc4a2e4dea685c48`。

后续实际准入：CPU16 **20875365 COMPLETED/0:0、136秒**，27项CPU测试及五臂
own8完整payload检查通过；检查覆盖慢参数、完整Adam moments/step、RNG结构与
sampler next9/index0，没有执行成熟模型或初始化CUDA。anchor8 certificate SHA为
`15173ac9acace815a1524d76c19f004bfb505e674f4b443244ec0c0035710c32`。
CUDA RNG的真实设备恢复仍须GPU入口检查，CPU通过不能写成GPU已恢复。
截至2026-10-25 09:40 UTC，20875366仍PENDING/QOSGrpGRES；其余两任务等待依赖，
排队不计入GPU消耗。本地只回读8,010,782B小收据归档，SHA为
`8bb4fa8ecfbd33960c95048a616f6215c15c29ed1f16ad0157d92f03ab7d4052`，
独立核对全部16条completion收据摘要；没有下载或反序列化HPC上的大PT。

恢复GPU16随后在ga021 **COMPLETED/0:0、4523秒**；完整独立检查通过，
五臂各新增8次更新、8/16评测及own16保存齐全，释放后各64MiB。主report SHA为
`7133c9e26a4ecd66092db087f750874b86c9e43d8e73e46a62c90a564b307039`。
CPU32 **20875367 COMPLETED/0:0、139秒**，当前GPU20875368待调度；该CPU前置
确实在父GPU终态后生成根目录`campaign_gpu_ledger_before_recovery32_001.json`，
raw sacct SHA为`7e9ab27553d00cc54047287771aa0dc7a9ac91a4aa4dad7be34759f42f338af1`。
三个已分配GPU作业累计17877秒（4.965833GPUh）。本地回读恢复16小收据
10,138,655B、SHA`71914eac1e3613f5138018b749dbb52fb2feb78476a5f3b04206ece9cb0dc388`，
重核14条小文件摘要；五份PT继续仅在HPC，不能把本地metadata核验写成重算Adam。

## 29. 2026-10-25：共同32完成，冻结推理顺序接续

GPU32 **20875368** 在ga002/A10080GB **COMPLETED/0:0、7556秒**，五臂各17–32、
80次新Adam、10次主评测及4次同C2干预完整，own24/32各五份通过独立核验。
四次已分配GPU累计25433秒（7.064722GPUh），失败和取消均保留。仅回读19,604,157B
小收据归档，SHA为`4d6a28ea6dd12bcf1e733997684e5d5183007325dca947b2d1e0d66a4b123315`；
本地重核27条小文件摘要，10份大PT不下载。

后续source统一使用原字节并集245文件，manifest
`c7ab09d6e8db8f223ecbf0c531b09dad5870f14ba8f15cc0a6e97ff9551dab70`。
它包含实际恢复父182与旧评测219的全部原文件；父检查override仍指原182目录，
不能把新245清单冒充父manifest。六个NEW薄SBATCH在`journal_001`单独核SHA，
不执行旧脚本正文里硬编码旧source210/219路径的版本。所有GPU仍为原账户
`torch_pr_50_tandon_priority/gpu48`、1A100/4CPU/64G，默认自动分区路由；
CPU为`torch_pr_50_general/cpu48`、4CPU/16G、900秒，实际可被路由到cs节点。

确认链CPU **20884776** 于cs630 **COMPLETED/0:0、118秒**。其root前置先用
终态sacct刷新四个已分配GPU账本，再由独立CPU进程冻结唯一共同32端点：
`frozen_common32_endpoint_001.json`，SHA
`34a36fe0e65a859355aa427bf4eb6146fd4208c3fc2c721e668fece70147728c`。
该元数据工具不构造模型、不读PT内容、不初始化CUDA；它不能替代随后实际CPU/GPU
入口的权重/GT完整检查。GPU **20884777** 已在ga005运行确认，申请3600秒，
不能在其终态前将申请或排队计成已用时间。

继续使用root独占、排他落盘的控制器形成afterok链：长前缀CPU/GPU
**20886401/20886402**（GPU3600秒）→reader成本CPU/GPU **20886403/20886404**
（GPU900秒）→相同历史注意力占比诊断CPU/GPU **20886405/20886407**
（GPU1800秒）。每段CPU在父终态后以5/6/7个真实GPU主作业刷新账本，再验证
本阶段与全部剩余预留；CPU840秒外层timeout覆盖前置与原入口，GPU仅在CPU通过后
分配。控制器SHA为`7b57c023e82749ec39bf2a4be225906ee07f8a927884d30196cd857babac496b`。
全部未结算GPU的完整时限加已结算的最坏上界为35333秒，不是实际用量。
不得人工提前创建这些前置拥有的排他ledger/plan/action文件，或重新冻结已存在端点。

推理只恢复各自慢参数与已学bias，不应用Adam或训练RNG；每片段重建状态。
所有GPU observer仍仅采样CUDA_VISIBLE_DEVICES指定的单个GPU，退出仅清理自己的
observer PID。共享SSH master继续保持，不关闭其他会话或修改全局CUDA环境。


### 29.1 确认作业末尾校验失败；独立 CPU 取证中（2026-10-25 13:50 UTC）

确认 GPU **20884777** 在 ga005 已终态 **FAILED/1:0，实际1628秒**。
神经推理 producer 已完成全部6144次调用、15主评测与9项同权重干预，0次Adam；
末尾原checker `918df088…f336f` 将source端的raw-bytes mask SHA与geometry端的
shape/dtype加raw-bytes SHA直接比较而失败。90组总数全部相等，但这还不能单独
证明相同掩码；必须以NEW独立CPU审计从原SHA绑定GT包的同一布尔数组重算两种
编码，并逐帧核验，再仅适配原checker输入副本执行其它完整检查。
原report/completion和FAILED状态均保留，不能给原目录补写一个冒充原checker通过的
verification，也不据此自动重跑GPU。

五个已分配GPU作业累计 **27061秒（7.516944 GPUh）**。原依赖链
20886401/20886402/20886403/20886404/20886405/20886407均自动CANCELLED，
elapsed0、AllocTRES空、AllocNodes0，未分配GPU。不要触碰不属本实验的20886406。
11列原sacct证明SHA为`052dd0d551d70ed9f6ca795638612d76f1fd585a6227f61c6c9ea5a038451d6a`。
原确认小收据连同失败日志已回读6,590,626B，归档SHA为
`99abafee4f48a599c7de56370ee66ed1766b958484e61d062b8c543312451915`。

旧root longplan工具要求确认COMPLETED，不能把FAILED伪造为COMPLETED以绕过。
独立审计通过后，另写明确绑定新审计、原FAILED1628秒和同一共同32端点的root准入
动作与新提交收据；原source245长前缀模型、旧控制器和排他锁全部保持原字节。


### 29.2 NEW CPU 取证通过，原模型与共同端点不变（2026-10-25 14:12 UTC）

独立CPU **20887922 COMPLETED/0:0，48秒**（cs646）；producer完整检查33.542秒，
原own权重文件/数据链检查仍全开，18个同数组双哈希与90组逐帧计数均吻合。
独立saved checker e2e3a751…d30b82重新核对小收据、原GT包掩码和两种编码；
它不再次反序列化PT，不能被描述为再次运行神经模型。原GPU FAILED/1628秒、
原918df checker未适配失败均保持。新审计SHA为
`0c8a06ab28d9572949a2a1ed86427f93809bef3f34a8b82582ebbe60b876a804`，
独立verification SHA为`dab1274300ee1f3970ccb641f1b72215c99f73db6d8f0b4bab75d14610555be2`。
249文件源码在原245之上仅新增producer/checker及两测试；manifest
`7e975c379ed6979736ae1ed313735a8bc102ddc6c71c9f39c98b999a0140ec76`。
小收据归档6,595,577B，SHA`2d28003b51fa634d9c3ea1a19e906b5d703aa2275e5a358d2ac42be0b70f87a6`，
本地全部14项completion摘要重核通过。

NEW root helper `pfw_root_longplan_after_confirmation_rescue.py` SHA为
`3b15410ab2fcc09ce26b44e718043c76de31e6301426f6ac627fc01dc1794420`；
在私有加载的旧40f工具中仅替换确认终态准入回调，独立验证新取证，再由原longplan
生成并检查相同age208_only/3600/3300/9414调用计划；不改旧工具或source245。
新plan为`longprefix_plan_common32_rescued_002.json`，SHA
`868a4cc6fe38e848041fc90ddaa03ba55ef9f0075ce3a54e792cc3addbdf8dec`。

新排他控制器SHA`fb2ee12d07873e65d14a4f573468f9230517a17210770b874d471697e38cb526`
提交CPU/GPU **20887931/20887932 → 20887933/20887934 → 20887935/20887936**，
首CPU依赖取证CPU成功，原六个取消作业不重用。长前缀CPU20887931已在cs638
COMPLETED/0:0、75秒；长前缀GPU20887932已在ga029运行，剩余四个等待依赖。
新ledger名称均002，第一份包含五个真实已分配作业、原FAILED确认1628秒；
已结算27061+全部剩余申请6300=33361秒，仍不可视为实际已运行33361秒。

### 29.3 三分支占比诊断接续（2026-10-25 14:38 UTC）

另提交只读诊断CPU **20889244** afterok:20887936 → GPU **20889245** afterok:20889244；
排队未执行。GPU固定1200秒/app900、CPU900秒/整段840秒，仍同账户/QOS/自动A100路由。
仅在两条相同长路线、冻结C2共同32上做逐query D2 raw选择，以raw-LSE差保持
local/summary/raw三路占比；1569次模型调用、一次额外原生reader检查、0更新，非主排名。
source262 manifest `9f913761d46515669af56169eee1d22daf24330cc9bc9e10a4749de60b626141`
保留原mass253全部字节。当前完整请求最坏上界34561秒，实际已结算仍27061秒。
CPU入口将在父mass终态后现场核对八个既有GPU主作业；包含原确认FAILED1628秒，
不删除失败/取消成本。root控制器SHA为
`549054ebfd911934df9d611395c2b3cdaa6cd4b8674feb682c5b083192582cd4`。
这是确认后追加的机制诊断，未修改原source245/253模型或重新选择共同32端点。

### 29.4 长前缀与reader core正常终态（2026-10-25 15:00 UTC）

GPU **20887932** ga029 COMPLETED/0:0、2385秒，原source245 checker
`771fe34a…99ef13`完整通过，10主评测＋2年龄干预、9414调用/0更新均齐全。
report SHA `e22bb80495b78e0be1880efe6532bf8db0f08d432d74ee9462b3852e7926a439`；
小归档7,648,062B，SHA`2c33c7d094c388a1924ed6e9946c6676aeefdcb7fb55b3991cf30af8c34e4fd5`，
本地全部26项completion摘要重核通过，不重新运行NN或GT投影。

GPU **20887934** ga033 COMPLETED/0:0、344秒；512模型调用捕获六组真实状态，
3000次prepare＋原分块reader计时和数值对照通过。小归档189,461B，SHA
`ec85ca2bd35414e59ef10d02cd0df0107428f1e2d18b52657f12fe4fc8223a20`，
本地五项completion摘要及原245 saved checker标量/来源回读通过。
七个已分配GPU累计 **29790秒（8.275 GPUh）**，旧545秒仍单列排除。
后续总history mass诊断20887936现已在ga020运行，raw分支诊断仍等依赖；
运行与排队请求均不当作终态实耗。正式任务与成本解释分别见研究目录的
ABOT_MITA_LONGPREFIX_OBSERVATIONS_20261025.md和ABOT_MITA_READER_CORE_OBSERVATIONS_20261025.md。

### 29.5 总占比与三分支控制完成（2026-10-25 16:35 UTC 回读）

GPU **20887936** ga020 COMPLETED/0:0、899秒；GPU **20889245** ga006
COMPLETED/0:0、578秒，原saved checker均通过。两者合计4707次模型帧调用、
0次Adam；前者匹配总history mass，后者匹配local/summary/raw三分支占比，
不是额外训练新臂。source253/262与共同32端点不变。
TOTAL report SHA `7dc20a37ae3679a771e736dee6f544264ac51220b09e67343f1baddd7ef3d0dc`；
RAW report SHA `485268e57c376630e4f59dab7623b3aabbae0e402490dca12295496680e6a523`。
小归档分别15,637,118B/15,521,641B，SHA为
`751f9eeed8546723dd4e62372d86732dbebcd31364ed8d80e8966475883b3eb6`和
`0d2ab2ad5851ffb05798dab528e53b66e81fae8e37001d4d17112d76b2baa96c`；
本地各64项completion摘要重核。九个真实已分配终态GPU作业现共
**31267秒=8.685278 GPUh**，含原失败/取消，旧545秒仍另列。

### 29.6 NEW 最后完整五臂周期、finished dependency age-out（2026-10-25）

用户要求实际至少10 GPUh；旧36000秒是阶段自设上限，不将8.685h冒充完成。
原阶段与冻结合同保留，另有NEW全五臂own32→48两轮scope：GPU8100秒/app7800，
新有界范围40500秒。真实31267＋完整请求8100=39367≤40500只是最坏预留，
不是已用39367秒。只做一轮至40的实测成本估计不足36000秒，因此选完整两轮，
不只延长赢家、不读partial质量挑端点、不空转补时；主确认端点仍32。
source253 manifest `c52731cb3ad8490f606a20bd081b27f47538c26f613746d224bd4381377a148b`，
协议 `7547cac70d1e5ac23ebf1bbc807dbffe79a4ec2ecb822764e44b37cafd36f487`，
checker `894a30f387c6b76a2cb78b1b59bec02b142cfcc7d3a740610b71d5c7d0291ddc`。

第一份提交001的CPU sbatch因`Job dependency problem`返回1，无stdout/job ID，
没有创建CPU/GPU或新增费用。其afterok:20889245虽在sacct显示COMPLETED，
但已从live Slurm controller age-out，scontrol已无此job。不能重新提交旧排他脚本、
伪造父状态或删除失败收据。独立拒绝证明SHA
`26dc5699f63655283dd99538787250d550190d5dc719ded8cb21eb9ed9ca6701`保留。
NEW controller002只移除已失效的CPU依赖，在CPU入口仍现场核九个真实终态；
GPU仍afterok新CPU。新controller SHA
`7b67e0c097fddea16d5315f27b5f1d5158962cd504773c3f3afb9778dedd2917`。
这是调度依赖修复，未更改模型、训练配方、数据或原冻结范围。

实际CPU **20893198** cs646 COMPLETED/0:0、219秒，执行6项CPU测试并检查完整
own32慢参数/Adam/RNG来源；不是把本地合并17项称为CPU实际17项。
report SHA `b1ae09614fc7953f1d6ce629b0d14987675d5194c7facb172298e27911ad5fd7`，
completion `a5e5ffcfa54d1c3500e885710b6abea8baa94bd0d899d49d5bda834e969191af`。
19,680,468B小归档SHA
`494acf53d1488e5948385ed9db8eac4526e55bb5520cfcd953a78b9c34112a82`已下载重核。
GPU **20893199** 正在ga008以同一tandon account/QOS/1A100运行；尚未终态结算。

metadata helper只在私有CPU子进程使用空CUDA选择器；提交GPU前恢复环境并去掉
继承的`CUDA_VISIBLE_DEVICES`/`SBATCH_*`，由Slurm分配可见设备。不要把root局部
metadata环境泄漏到sbatch，不改共享全局环境。进度003只读本项目report与已知job，
不查看其他用户GPU。共享SSH master继续保留。

### 29.7 NEW GT-only CPU 深度尾部核查（2026-10-25 16:57 UTC 回读）

用户要求重读原论文并归因。原生TG配置/base的80m过滤与本轮stored-mask规则
存在差异，故新增一个只读NumPy CPU审计，不改训练、GT mask或主指标。
CPU **20896377** cs613 **COMPLETED/0:0，10秒**，统计内部7.136秒，
3项实际CPU测试通过。它只读两场景各64帧、384个depth/mask/camera文件，
每文件size/SHA、逐帧valid数与完整mask raw-byte SHA全部匹配；不读RGB/模型/PT，
不导入Torch、不新增GPU用量。root仍独占SSH与提交，原共享socket未重建。

source3文件manifest `5bd500b53b6d965c386ef984ec702a3f840857edf343a2b87b3dc3d38e7ad786`，
report `587eceddc6d49ae1d1cdfc841efea39d9641d1c315ab6f29170724eb6c60ef87`，
completion `125dbb98abe6ed01a6b9db1d43ca21f04bfa9043534a747384785202519e9300`。
10,168B小归档SHA `9896739360532a3f60d4a8e166cdd79ff3ff5c4a5ab3d14efda4ff10d24df9e7`
已回读并重核report/test摘要。Desert的z>80仅占原有效像素1.8133%，却占GT平方
范数和98.23%；这是GT分布事实，不冒充预测残差/语义sky/小收益唯一根因。

下一项只读共同32的三臂六eval诊断尚在NEW本地准备，拟900秒/app780、0更新。
其端点独立于运行中48；新范围可把48完整8100秒保守预留而并行，不读取partial
质量，最坏31267＋8100＋900=40267≤40500。正式提交仍须实际CPU准入、完整
源闭包、新排他动作收据与fresh10job账本；旧冻结阶段36000上限不改写。

### 29.8 深度残差复播完成，原模型输出逐值保持（2026-10-25）

NEW source256 manifest `7cc33e5fc5bfe863ddd318bbc6d7f59cbf96d15f16154bfeeac3c77e5e31ccfb`
为原245全字节＋8个新文件＋2个SBATCH＋1个root元数据ledger工具；不能把它
记作255。原245/182/48source253及共同32端点原字节不变。
CPU **20898214** gl011 **COMPLETED/0:0、88秒**；实际9项CPU测试29.426秒，
公共CPU入口及独立saved checker均通过。测试日志在journal单独绑定，
不冒充CPU report内部执行或神经/真实权重TEMP mock的验收。

GPU **20898217** ga011 **COMPLETED/0:0、491秒**，producer450.549秒，
A/Bfull/C2各自own32、相同两条原256帧开发窗，6eval/1536模型帧/0更新。
六份原point/pose输出SHA完全一致，原GT和primary保持，新的深度bin加和及
scale-only RPEt算术由原e6e checker通过。source256只读before-final原9账本与
48的source/pricing元数据；48仍RUNNING时保守预留完整8100秒，新的900秒请求
使最坏40267≤40500，不把running观察elapsed再加一次到8100。

report `71284de04d9300390e2e06c61c21e324b3295abe3797b9873b872eb65d523745`，
completion `28aed1fe491288e91188583d59cd8a0f068c876982c5b0dbbb410fc424c19cca`，
verification `3bf1d2e406d3e147c1b0391dfce3f0df71b6951bfdaf7be86073f0809fb85902`。
11,972,020B小归档SHA `8177a83cfd3d814ee4393e0b7366265f8e4a07b6041c1df176ba64c2774301d8`
已回读，44项completion摘要重核。默认本地Python无Torch，导入原confirmation
helper会失败；使用`/home/asus/miniconda3/envs/pi3x/bin/python`只读重执原checker、
显式映射本地source/vendor后，与saved proof逐值一致，CUDA未初始化。
此环境导入失败不是原GPU核验失败，不因此重跑GPU。

十个已分配终态GPU现共 **31758秒=8.821667 GPUh**，另有48训练仍运行。
17:24:44 UTC的独立`sacct`观察收据记录11个主作业终态＋运行elapsed实际已达
36342秒=10.095 GPUh；其中运行elapsed只是已观测下界，不冒充终态结算，
也没有据此在五臂48尚未齐时结束goal。最终用48的真实终态elapsed再结总账。

诊断显示Desert近1.81%远点占P·G约78%，会通过全局LS尺度影响大量近点；
它们只占原mean残差和约31.43%，不能把GT平方量98%写成预测误差98%。
重建GT-z<80次级尺度不逐值复刻raw-depth80m阈值，原primary保留；点图约0.11%
次级差和RPEt翻向不构成MiTA稳定获胜。完整解释见
ABOT_MITA_DEPTH_METRIC_REPLAY_OBSERVATIONS_20261026.md。

### 29.9 五臂48完整终态与最终实耗（2026-10-25 18:03 UTC 后回读）

GPU **20893199** ga008 **COMPLETED/0:0、7125秒**；producer6981.675秒，
原source253/894a checker `verified=true, partial=false, complete_comparison=true,
missing_payloads=[]`。五臂各从own32完整恢复后执行33–48，80次新Adam、
10次48评测、18000模型调用/23040输入帧；40只存checkpoint，不评测。
report `a21ab0374951024adf0cde27b5839e7dd61b87f18ad56933a3e9f15ddd234d9b`，
completion `8596b127f3bed154707f30e8c0ad40139e8dcf6ecfe2badc0660e6b73a31ce3f`，
run `8cb366a82b5db695c195ebe3ae7e9ccc6aa8a170e6be53c81854a19096c62030`，
verification `87e4da60ebfd87c35a43b8ed9338e85b207e36fa48b7bb3f65d0561e367f7235`。

24,940,953B小归档SHA `d6b4dee04b3ad87c3a887d6653dbde0b232b227f682be481a3e8b73e3d26354e`
已下载完整并重核35个小completion文件。10个own40/48 PT共23,855,525,016B留在HPC，
未下载或本地再hash；本地新标量adapter绑定原远端full proof，不能说本地重新
完整检查Adam/RNG。显式使用pi3x环境完成source253/parent182与标量分析，
原32确认端点不变。各臂释放后allocated回到67,895,296B，工作已正常退出。

最终独立`final_campaign_gpu_settlement_001.json`与raw sacct包含11个主GPU作业，
全部终态、各1GPU，**38883秒=10.800833 GPUh（10小时48分3秒）**。
计算为原九终态31267＋最后训练7125＋只读深度复播491；含失败/取消，
旧545秒另列，CPU/排队/请求时限/`.batch/.extern`不重复计算。NEW cap40500，
实耗低于上限、reserved=0，没有本goal待跑GPU；旧冻结36000范围和所有原收据保留。
原价格8100请求不是7125实际的替代，17:24的running下界证明也不替代本终态总账。

最终C2原point宏比A低0.03590%，但0→48 DID仍为正、原32确认没有净提升；
48没有重做新的确认/年龄/mass干预。后续raw-only固定生命周期专家和校准只是
本地未执行设计，不记作已训练方法或新GPU成果。完整表、全轨迹图和原数据/尺度
归因均在研究目录保存；共享SSH master和其他用户/项目作业未被关闭或修改。

## 30. 2026-10-26：全18层MiTA转换的新任务与独立依赖

新任务先重新读取`ssh -G alantorch`、默认`ssh -O check`，仍复用原master
pid1351507及权威ControlPath。新PTY最初停在登录启动，向该PTY发送一次Ctrl-C后，
确认`id -un=yz11502`、`torch-login-b-1`；没有关闭master、换账户socket或重认证。
本次配额快照为scratch3.01TB/5TB、4,315,173/5,000,000文件，home16GB/50GB；
登录节点`/tmp`约2.6GB空闲，实际作业继续使用专属node-local临时目录。

独立任务根为`/scratch/yz11502/Research/abot_mita_core_goal_20261026_001`；旧模型、
数据、环境和已经结算的10.800833GPUh实验保持只读。继承解释器为Torch2.5.1+cu124、
Python3.10、CXX11ABI=false。原环境没有flash-attn/flashinfer，因此从官方release
下载匹配wheel，用`--no-deps --no-compile --target 新任务/deps/python`隔离安装：
flash-attn2.7.4.post1及flashinfer-python0.2.5+cu124torch2.5；没有升级共享环境。
FlashInfer大wheel首次HTTP下载超时后保留partial，续传完成并匹配官方index SHA
`e6dd9e83ea85a1f135fe35393ae2ff2693e5d8150a3b94d5a7a26a29f73b89fa`。
安装成功不代表CUDA验证通过，实际kernel调用留给调度GPU。

本轮显式资源组合再次通过test-only：
`torch_pr_50_tandon_advanced/h100_tandon/gpu48`和
`torch_pr_50_tandon_priority/a100_tandon/gpu48`，各1GPU/8CPU/128G/20min。
实际CPU准入job **20911235**：`cpu_short/torch_pr_50_general/cpu48`，4CPU/16G，
在cs624 **COMPLETED/0:0、69秒**；26项CPU测试与独立checker通过，24个任务源文件
和97个vendor Python源文件校验通过。源manifest SHA
`bb6d4763daceaccab4fef312c1f751be57c0c7012ee9832859b57613ef2270d6`。
128×64训练计划的19,608个唯一资产路径存在，但不能据此声称已训练或完整GT质量QA。

依赖该CPU成功的1A100完整工程job **20911300** 已提交，20min上限、8CPU/128G，
当前回读为`PENDING/QOSGrpGRES`，尚无GPU实耗或CUDA结果。保留这一份等待任务，
没有因预计启动时间或共享额度不足而重复提交。新任务初始总上限为6GPUh、最多并发1GPU；
这是本研究阶段的资源范围，不是集群账户的通用规则。结果和后续终态以本任务账本为准。

### 30.1 全层数值诊断与真实训练步通过（2026-10-26）

上段的排队状态已结束。原 GPU **20911300** 在 A100 上 FAILED/1:0、68秒：
单算子输出与 Q/K/V 梯度通过，但全模型分块/逐帧点图相对差0.02351，超过原0.005
容差，未执行Adam。保留原失败，不把后续修复追记成原job成功。

NEW 诊断 CPU **20913613** COMPLETED/0:0、60秒，GPU **20913615**
COMPLETED/0:0、90秒。定位到逐帧与批量encoder的BF16数值差经硬路由放大；
统一原逐帧encoder输出F32值后，MiTA分块/逐帧点图相对差约4e-7。分页NHD与
功能路径采用同一QKV连续布局。诊断不提供训练准入，也没有测得提速成功。

NEW SOURCE_004 manifest SHA
`76373935db27775a777e1a5128f83cab3280209a6c7854b58563bb8810405a2b`；
CPU **20916281** COMPLETED/0:0、39秒，GPU **20916282**
COMPLETED/0:0、84秒，独立checker给出`verified=true, eligible_for_fit=true`。
原相对0.005/绝对0.05容差保持；MiTA分页与功能输出完全一致，分块/逐帧点图
相对差4.0015e-7。16帧原Pi3Loss＋四层特征蒸馏完成一次真实Adam：
630,227,542参数、862张量、18个global QKV梯度均有效，encoder冻结，更新后重置全部状态。
report SHA `7bb8c4b71398cfc634abbec8554e155c4c304a0fc3ab3c7a73b018a448349b55`。

累计本轮HPC GPU实际242秒；另计根代理单独授权的本地小算子profile保守2秒，
合计244秒、reserved=0。该本地profile不载神经模型、峰值allocated约89.5MiB、
进程已退出，且与HPC GPU无重叠；RTX4090时间不作为A100性能证据。下一步为同机
原ABot/MiTA各固定128×64帧适配，先验证完整64帧teacher/student反向显存与预算。

### 30.2 固定128×64全层配对训练提交（2026-10-26）

NEW SOURCE_005保留SOURCE_004全部30文件原字节，再加入配对fit与静态pack探针的
完整导入闭包，共41文件；manifest SHA
`8dce95f822fb677e7055442438c236b47ddfb279c62dbd8516c49de5cc3944f5`。
本地冻结namespace的13项CPU检查通过；远端解包后再次核验全清单。
root控制器`ae573ae0…6eb7fe`先以`sacct`确认本轮三个GPU主作业均终态，
242秒HPC＋保守2秒本地profile=244秒；244＋新完整10800秒预留=11044≤21600。
排队不算实耗，旧10.800833GPUh仍单列。

实际新CPU **20917455**：4CPU/16G/600秒，`cpu_short/torch_pr_50_general/cpu48`；
GPU **20917458**：1A100/8CPU/128G/10800秒，
`a100_tandon/torch_pr_50_tandon_priority/gpu48`，`afterok:20917455`。
两臂在一个GPU分配中按相同固定128步、每步64帧、同训练数据与原任务＋蒸馏执行。
CPU入口先跑同源静态pack6合同与fit7合同，并重新绑定完整GPU准入。
GPU入口先执行最多120秒的小算子探针；它失败时保留独立失败，不改变已经通过
准入的原fast算子训练。正式fit有10500秒应用上限，先做完整64帧、无Adam的
teacher/student反向与显存/配对预算核验；不足时保存partial并非零退出，不缩步。
提交receipt SHA `fdfa957ce929ec9360edf8149a6e0b3449da27a2cb7423bc365d556e35fe86a8`。
当前两job待调度；不会因为等待而重复提交或启动本地GPU。

后续CPU20917455在cs606 **COMPLETED/0:0、58秒**，两项同源CPU checker通过；
fit CPU report SHA `836e07579df832cdd51fd5d2a0c4f3ad938f6a0f5e6edc951fb08b8d78d65456`。
GPU20917458经过`QOSGrpGRES`正常开始，在ga007运行；没有复制任务或换GPU栈。
静态pack小算子CUDA输出/梯度/dummy零梯度均通过；完整算子fast约1.637ms、
static约1.523ms、Torch FLASH dense约0.236ms，仍没有提速成功。
64帧独立teacher/student反向通过，峰值allocated36,012,802,048B；加Adam与foreach的
逻辑估计43,575,532,552B不是已执行Adam峰值。配对耗时预留8724.8秒低于剩余应用
10447.7秒，入口开始正式固定128步两臂。最新观察dense已实际17次Adam；
running elapsed只是观察下界，仍保守预留完整10800秒，不将其重复加入244秒终态实耗。

### 30.3 NEW 固定端点部署对照自动依赖链（2026-10-26）

SOURCE_006完整保留SOURCE_005的41文件原字节，加原生BF16评分、单次分页gather、
固定形状Graph与只读评测入口等导入闭包，共57文件；manifest SHA
`fdeb722e21a4740875a8ff0c1a1f378fccf0d6bd22a3059fcf87501337dd31e5`。
本地冻结namespace的27项CPU合同通过。新root控制器
`1274087e…7421a7`只做元数据/Slurm提交，不运行NN或读取训练质量挑方案。

CPU **20920376**（4CPU/16G/600秒）`afterok:20917458`，
GPU **20920378**（1A100/8CPU/128G/2400秒）`afterok:20920376`；
仍是同一已验证account/QOS组合，所有GPU顺序执行。提交时训练job仍RUNNING，
终态实耗244秒＋原训练完整10800秒预留＋新2400秒预留=13444≤21600；
不把运行elapsed再加一次，不把未来预留称为实耗。receipt SHA
`93d6b53f22c5b6ae6ad54b57cc8ae8089f512dd6f36c313004effc75774ce8cd`。

CPU入口必须重新验证两臂完整128端点及其full payload proof；只流式hash，
不反序列化成熟PT或构造模型。GPU入口重新按端点128整段耗时核验2220秒应用预算。
同一GPU比较dense128原FlashInfer、MiTA128原fast、同MiTA权重static+fused、
native-BF16-score+fused及预声明Graph第五候选；全部0 Adam，成熟PT只mmap CPU，
仅复制862个慢参数，不恢复GPU Adam/RNG。Graph先在同GPU隔离子进程验证，
失败明确保留并跳过该候选，不替换普通reader；四个核心比较不因此冒称Graph成功。
W48只做合成算子定价，不记为三维扩窗评测。源/作业仍待实际完成，不能提前称比较成功。

### 30.4 部署入口应用时限异常修正，未重跑训练（2026-10-26）

审查发现可选Graph的generic Exception处理可能吞掉父应用TimeoutError；
嵌套capture还可能将其包装为GraphCaptureUnsupported。原SOURCE_006保持只读。
原CPU20920376和GPU20920378均在PENDING状态精确取消；sacct确认
`CANCELLED by 4421311, ElapsedRaw=0, AllocNodes=0, AllocTRES空`，没有GPU实耗。

NEW SOURCE_006B仅改同一评测入口的父deadline异常类型为专用BaseException，
使其穿过可选candidate/capture的Exception处理；Graph子进程自己的120秒超时
仍记录为候选失败。57个文件中只改这一文件；manifest SHA
`077f65ee7219650226b4f0687cf7d056c4f8c0b1bef349466a17da3c46259052`。
本地冻结namespace27项CPU测试通过，另一次真实CPU SIGALRM确认不会被optional
Exception捕获，未初始化CUDA。没有更改模型、训练、数据或评分口径。

新CPU **20925878** `afterok:20917458` → GPU **20925880**
`afterok:20925878`，资源时限不变，输出改为IMPL_CPU_002/IMPL_GPU_002。
新控制器SHA `2d315cc4…777b41`，提交receipt SHA
`e2fecc56ac8e14410087d82a043952340e0b0c47bb158ae1b6088682fe795203`。
最大预留仍244＋10800＋2400=13444秒；不重复计算已取消的零分配作业。
此时原训练已实际完成两臂各128次Adam，正保存MiTA端点并完成最终评测；
完整训练proof与Slurm终态尚待回读，不提前追记训练成功。

### 30.5 全配对训练与五部署终态，最后的缓存/整模型成本审计

上述训练已在ga007 **COMPLETED/0:0、5748秒**，两臂各128次真实Adam、
各8192帧训练呈现；保存两个7,563,830,264B端点，含完整Adam/RNG。
独立checker在HPC流式重hash完整PT并确认两端点；report SHA
`ed27d933d5c7e3587375d7124aa892cfd503e05654b464e4dae7d9d596ab810a`。
大PT留HPC，只下载小收据闭包；本地再次检查源、JSON/标量及完整依赖绑定，
不把缺本地PT的metadata检查冒称重新hash完整权重，不重算NN/GT。

CPU20925878在cs612 COMPLETED/0:0、93秒；部署GPU20925880在ga004
**COMPLETED/0:0、1512秒**。8320次完整模型帧调用、0 Adam，五条件全部完成；
report SHA `144e24bf273195e1093e15d0f30165f3c23a94ba0e4fa2f70d6df8bf7eb76fd9`。
Graph在该GPU独立小算子数学、不同输入与replay验证后才进入NN计时；
没有把失败候选替换为普通reader。W48仍只有合成算子，不能视作三维评测。
研究效果详见proposal及结果报告，不用基础设施成功代表提速成功。

推理基线审查发现官方infer构造默认`freeze_encoder=False`，而train构造默认为True；
PyTorch2.5.1的AMP权重缓存会检查FP32叶子参数的`requires_grad`，即便no_grad也是如此。
因此NEW SOURCE_007固定同一权重和任务，只比较推理flag/cache合同，并测真实整模型
global-read置零成本反事实与模块kernel profile；置零不算可用三维方法。
manifest SHA `d07f3a1e756ab302b0361f8f324d36ccdf4a8bf7e437ee0388bf9550c7fd21f9`，
63文件，本地冻结namespace16项CPU检查通过。固定第一个既有dev场景，最多4227次
完整帧调用、0 Adam；所有权重value hash、版本、dtype与flag恢复单列检查，
额外BF16权重cache的显存不得漏报。

CPU **20927998** `afterok:20925880`，cs609 COMPLETED/0:0、86秒；
GPU **20928000** `afterok:20927998`，1A100/8CPU/128G/1500秒，应用1320秒，
仍用`a100_tandon/torch_pr_50_tandon_priority/gpu48`，当前PENDING。
提交receipt SHA `c4ffb8cd4cc689f043a96b66c3ae2ebb7dc9854786dd367eac78e0959c1bc906`。
此时本轮HPC已结算7502秒＋保守本地2秒=7504秒；仅预留此1500秒，
最坏9004秒≤21600。此前零分配取消作业仍计0，旧10.800833GPUh继续单列。

该成本审计GPU20928000已在ga021 **COMPLETED/0:0、695秒**，4227次完整帧调用、
0 Adam，独立checker通过。report SHA
`b14b7e1e34f60b0ef4786ffa33fd1b3b374b715f905378bc80b78041df1c3851`；
completion SHA `d34f635269b14fa33a7e46b77de4bee0e5d7c20322cbeea5aee4c18d8bd65fab`。
当前本轮已结算HPC8197秒＋保守本地2秒=8199秒，reserved=0。

**共同RoPE回退的归因边界。** 该轮仍共用Torch RoPE2D；其官方Python路径每次
`int(positions.max())`取GPU scalar，LUT已缓存也不会跳过。由36层与原heads调用
结构可推导每帧56次2D RoPE调用（不是实测同步耗时）。旧curope仅按SM90构建，
不把它视为A100优化后端；CUDA与Torch对BF16频率量化顺序也不能假定相同。
因此准备一次额外、0更新的共同后端诊断：直接复用原Torch cos/sin LUT的
推理Triton融合RoPE，先独立数值/布局/位置界检查，再共同用于dense/MiTA两端点。
vendor与全部旧冻结源保持不变，不把公共后端加速记成MiTA收益。
这是当前goal内最后一次共同后端比较，拟最多7555完整帧调用/1800秒1GPU；
当前只是准备，尚未提交或预留，不在8199秒之外虚报实耗。

### 30.6 共同数学匹配RoPE2D的最后一次配对部署提交

SOURCE_008完整继承SOURCE_007的63文件原字节，新增6文件，共69文件；manifest SHA
`20d984f3c84bd295d73459e1804a8c5b7b1dd57f51283f36ca28ceac68476060`。
本地冻结namespace的15项CPU合同通过，无CUDA初始化。真实native patch坐标会加1，
因此20×36网格的LUT长度37（special为0），不是未平移网格的36；在GPU运行前源码
复核已修正。清理receipt与hash异常不能覆盖ApplicationDeadline的CPU合同也已通过。

第一次root controller仅在CPU `sbatch --test-only`返回`Job dependency problem`，
未实际提交任何CPU/GPU job。sacct仍可见已完成20928000，但`scontrol show job`
返回Invalid job id：完成父作业已不在controller可依赖记录中。保留第一次request/receipt，
不伪造旧依赖、不将它记成GPU失败。NEW控制器002先以sacct确认所有六个旧GPU
主job终态、已结算8199秒，并由CPU入口重验完整父proof；CPU无需依赖这个已完成
且不在controller的旧job，GPU仍必须`afterok`新CPU。

实际新CPU **20931779**：4CPU/16G/600秒，cpu_short/general/cpu48；
GPU **20931781**：1A100/8CPU/128G/1800秒、应用1620秒，
a100_tandon/torch_pr_50_tandon_priority/gpu48，`afterok:20931779`。
root控制器SHA `13e66e52a04aaa0d3586396279612263406b3c4af4a9df8fd50bbfb8d551c345`；
提交receipt SHA `6f87c4b5b78078f0b77b6afc1de7bd0c89dc10c0daec94aa6cb3c84c970bd1b7`。
本轮已结算8199秒＋唯一新1800秒预留=9999≤21600；不把排队或预留计作实耗。
先GPU逐位oracle与Graph独立验证，再做既有两dev/原128端点的共同后端对照、
第一个dev的zero-read和3帧profile，最多7555完整帧、0 Adam。当前尚无该后端CUDA结果。

### 30.7 共同后端对照完成与本阶段最终结算

CPU20931779在cs605 **COMPLETED/0:0、91秒**，15项合同及独立checker通过；
GPU20931781在ga002 **COMPLETED/0:0、1004秒**，7555次完整帧、0 Adam。
12组实际FP32/BF16 RoPE逐位oracle、越界flag、输入不变/输出所有权均通过；
原生MiTA body和Graph亦在同GPU重新验证。每个fused NN case实际46592=56×832次
RoPE调用，profile3752=56×67；47个共享alias与全部参数值/版本/dtype/flags恢复通过。
report SHA `5a8ee8a68e34de8260dfbe9b749f0bd0cbcc93055b7374ab7ef3feb4f780c139`；
completion SHA `40dfa93ebc54ead0ab0d24d119431846681fd346d9634848482ecfe2adb87980`。

最终小收据闭包1570文件、39,019,938B，SHA
`5017ec6f858d6fb2b00c56e3ddbb19d38b693863c35cc1736176108f8906b175`，已SCP下载、
重hash并以同冻结SOURCE008 checker在本地重放全部小收据依赖校验。完整PT仍只留HPC；
不声称本地又执行NN、GT或重新hash外部大权重。图表纯CPU从绑定JSON生成。

该轮共同融合RoPE下，两个既有dev的dense78.861ms、MiTA Graph97.562ms；MiTA
仍慢23.7%且几何更差，停止当前W12候选追加训练。方法结论和限制见完整结果报告；
不能把低层数学/系统验证通过当作MiTA提速成功。

本阶段七个GPU主job实耗：68＋90＋84＋5748＋1512＋695＋1004=**9201 GPU秒**；
另保守计本地旧小算子profile2秒，合计**9203秒=2.556389 GPUh，reserved=0**。
全部本任务作业终态，无并发或挂起的GPU分配。旧SOURCE006取消作业0秒/0节点，
source008初次controller仅test-only拒绝、无job；H100仅test-only查资源，未实际提交。
此前10.800833 GPUh campaign仍独立列账，不为填满本阶段6小时上限再运行。
末次sacct核准20916282节点为ga010；数值证据以对应报告与终态收据为准。


## 31. 2026-11-24：`alan` 工作站共享连接、B200 抢占语法突破与最新集群快照

### 31.1 工作站 `alan` 独立 ControlMaster 配置（区别于 `asus`）

工作站上 `/home/asus/.ssh` 权限为 `0700`（属主 `asus`），Linux 与 OpenSSH 禁止以 `alan`（`uid=1001`）跨 UID 复用 `/home/asus/.ssh/cm-*`。因此为 `alan` 按 §1.6 配置独立 `~/.ssh/config`（`chmod 600`）：

- 路径：`/home/alan/.ssh/config`（`Host torch alantorch`，`User yz11502`，`HostName login.torch.hpc.nyu.edu`，`ControlMaster auto`，`ControlPath ~/.ssh/cm-%C`，`ControlPersist 24h`）；
- `ssh -G alantorch` 实际解析 socket：`/home/alan/.ssh/cm-e3ce4155ccb925413d599e13706baddf79fddff3`；
- 用户以 `alan` 完成一次交互认证后，`ssh -O check alantorch` 返回 `Master running`，远端实测 `id -un=yz11502`、`torch-login-a-5.hpc-infra.svc.cluster.local`、`2026-11-24T14:29:49-05:00`。

### 31.2 实测账户与配额快照（2026-11-24 14:29 EST）

`my_slurm_accounts` / `sacctmgr` 当前列出 `yz11502` 的 6 个关联账户（与 §23 一致）：

| Account | Description |
|---|---|
| `torch_pr_50_general` | `scene-x` |
| `torch_pr_50_tandon_advanced` | `scene-x` |
| `torch_pr_50_tandon_priority` | `scene-x` |
| `torch_pr_54_general` | `navigation` |
| `torch_pr_54_tandon_advanced` | `navigation` |
| `users` | `users` |

配额快照（`timeout 12 myquota` 在 top-5 统计阶段超时前已打印主表）：
- `/home`：`16 GB / 50 GB`（`32.80%`），`20,503 / 30k` 文件（`68.00%`）
- `/scratch`：`3.04 TB / 5.00 TB`（`60.72%`），`4,327,933 / 5.00M` 文件（`86.00%`）— 剩余约 `1.96 TB`、`~672k` 文件，新任务严禁向 `/scratch` 落大量散帧文件，须打包或落 `$SLURM_TMPDIR`
- `/archive`：`341 GB / 2.00 TB`（`17.05%`），`552 / 20k` 文件（`2.00%`）

同日 `sacctmgr` QoS 快照：`gpu48`（`MaxWall=2-00:00:00`，本轮先后观测到 `MaxTRESPU=gres/gpu=16` 与 `gres/gpu=2`，动态调整以当日查询为准）、`gpu168`（`gres/gpu=4`，`7-00:00:00`）、`gpuplus`（`gres/gpu=96`，`7-00:00:00`）、`cpu48`（`cpu=3000,mem=6000G`，`2-00:00:00`）。

### 31.3 关键突破：B200 抢占提交语法（`--comment="preemption=yes;requeue=true"`）

此前 §23 观察到直接对 `b200` / `b200_tandon_prem` 传 `--qos=gpu48`（或仅传 `--requeue`、或 `--qos=gpuplus`/`gpu168`）均被站点 job-submit 插件拒绝（`Error partition '...' is not valid for this job`）。

本次对照 NYU RT Torch 文档实测确认：**申请抢占式 B200 必须显式传入 `--comment="preemption=yes;requeue=true"` 且不强制指定不兼容的 `--qos`**（让站点插件自动路由）：

```bash
# B200 抢占式预检模板（可自动路由到 b200 或 b200_tandon_prem）
sbatch --test-only \
  --account=torch_pr_50_general \
  --gres=gpu:b200:1 --cpus-per-task=4 --mem=64G --time=00:15:00 \
  --comment="preemption=yes;requeue=true" \
  --wrap=/bin/true
```

**2026-11-24 全量 `sbatch --test-only` 实测通过矩阵**（未创建作业，不代表 GPU 运行栈 gate 通过）：

| 模式 | Account | Partition（实测路由） | QOS / Comment | GPU / 资源 |
|---|---|---|---|---|
| **B200 抢占** | `torch_pr_50_general` | 自动 → `b200`（`PreemptMode=REQUEUE`，15 节点/120 B200） | `--comment="preemption=yes;requeue=true"` | `gpu:b200:1` |
| **B200 抢占** | `torch_pr_54_general` | 自动 → `b200` | `--comment="preemption=yes;requeue=true"` | `gpu:b200:1` |
| **B200 抢占** | `torch_pr_50_tandon_advanced` | 自动 → `b200_tandon_prem`（2 节点/16 B200）；显式 `b200` 亦通过 | `--comment="preemption=yes;requeue=true"` | `gpu:b200:1` |
| **B200 抢占** | `torch_pr_50_tandon_priority` | 自动 → `b200_tandon_prem` | `--comment="preemption=yes;requeue=true"` | `gpu:b200:1` |
| **B200 抢占** | `torch_pr_54_tandon_advanced` | 自动 → `b200_tandon_prem` | `--comment="preemption=yes;requeue=true"` | `gpu:b200:1` |
| **常规 GPU** | `torch_pr_50_tandon_priority` | `a100_tandon`、**`h100_tandon`**（本次新确认通过）、`l40s_public`（拒 `h200_tandon`） | `--qos=gpu48` | `a100` / `h100` / `l40s` |
| **常规 GPU** | `torch_pr_50_tandon_advanced` | `h200_tandon`、`h100_tandon`、`a100_tandon` | `--qos=gpu48` | `h200` / `h100` / `a100` |
| **常规 GPU** | `torch_pr_54_tandon_advanced` | `h200_tandon`、`h100_tandon`、`a100_tandon` | `--qos=gpu48` | `h200` / `h100` / `a100` |
| **常规 GPU** | `torch_pr_50_general` / `torch_pr_54_general` | `h200_public`、`l40s_public` | `--qos=gpu48` | `h200` / `l40s` |
| **常规 CPU** | `torch_pr_50_general` | 自动 → `cpu_short`（注意显式 `--qos=cpu_short` 会被拒，应传 `--qos=cpu48` 且省略 `--partition`） | `--qos=cpu48` | CPU only |

⚠️ **抢占作业与 B200 兼容性注意**：
1. 抢占作业运行满 30 分钟后可被高优作业抢占并 `REQUEUE`，训练脚本**必须支持周期性断点保存与 `SIGTERM` 优雅续训**。
2. B200 为 Blackwell（`sm_100`），须使用 **CUDA 12.8+ 与 PyTorch ≥ 2.8+cu128**（不能使用旧的 `2.5.1+cu124` 或 SM90-only 自定义扩展）。

### 31.4 远端现有 Conda PyTorch 版本与容器镜像核对（直接读取 `version.py`，避免登录节点 import torch）

| 路径 | PyTorch / CUDA 版本 | 适用硬件 |
|---|---|---|
| `/scratch/lg154/conda-envs/memnav/bin/python` | `2.8.0+cu128`（Python 3.10） | A100 / H100 / H200 / L40S / **B200**（与本地 `lingbot-map` 版本一致） |
| `/scratch/lg154/conda-envs/lightnav/bin/python` | `2.10.0+cu128`（Python 3.11） | A100 / H100 / H200 / L40S / **B200** |
| `/scratch/lg154/conda-envs/robocasa24/bin/python` | `2.12.0+cu130` | CUDA 13 栈 / B200 |
| `/scratch/lg154/conda-envs/gr00t/bin/python` | `2.5.1+cu124` | 仅旧栈（A100/H100/H200），不适合 B200 |
| `/scratch/lg154/conda-envs/openpi/bin/python` | `2.7.1+cu126` | A100/H100/H200 |

已核对可用 Singularity 镜像：
- `/share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif`（匹配 `memnav` `2.8.0+cu128`）
- `/share/apps/images/cuda13.0.1-cudnn9.13.0-ubuntu24.04.3.sif`

远端数据集确认：`/scratch/lg154/Research/datasets/mp3d` 及 `_overlays/mp3d_revisit_v0_pt{1,2}.sqf` 可读。
- **登录节点避坑提示**：切勿在登录节点执行 `find` 扫描 NFS 下的 conda `lib/` 或直接 `import torch`（易超时）；查包版本直接读 `site-packages/torch/version.py` 即可。

---

## 32. 2026-11-25：高效排卡实战规范、多分区抢占池与 `sbatch --test-only` 对比选路法

在 2026-11-24 至 2026-11-25 的大规模多模型闭环（`3,726+` 次 Habitat 闭环）与 2×GPU DDP 蒸馏长训实践中，验证了一套稳定、高速且零算力浪费的排卡与容错规范。

### 32.1 为什么能快速排到卡：四项协同策略

1. **多分区回退池（Multi-Partition List）替代死等单分区**：
   - 只要任务运行栈已在多个兼容 GPU 架构上通过 Gate 验证（例如 CUDA 12.8 + PyTorch ≥ 2.8 兼容 `l40s / h100 / h200 / b200`），提交时应将所有合格分区写成逗号列表，让 Slurm 调度器直接选取**预计最早开机**的节点，而不是盯死某一个高拥堵队列：
     - **2 卡训练（可抢占续训）**：`--account=torch_pr_50_tandon_advanced --partition=h200,b200_tandon_prem,b200 --comment="preemption=yes;requeue=true" --requeue --signal=B:TERM@120`（省略 `--qos`）。实测 2×H200 运行至 Step 264 遭抢占后，自动无缝切换至 `b200_tandon_prem`（`gb001` 2×B200），单步耗时下降约 `35%`（`~23.5 s → ~17.5 s`）。
     - **单卡评测 / Gate**：`--account=torch_pr_50_general --partition=l40s,h100,h200,b200 --comment="preemption=yes;requeue=true" --requeue --signal=B:TERM@120`。
   - 若结论对特定 GPU 型号/精度/延迟敏感（如严格微基准计时），仍遵循 §3.1 固定单分区并在 receipt 中记录 GPU 型号与驱动。
2. **代码级支持 `SIGTERM` 原子断点，敢用抢占式高算力池**：
   - 抢占式 B200 池（`b200` / `b200_tandon_prem`）排队压力显著低于常规非抢占长队，但运行满 30 分钟后随时可能被 `REQUEUE`。
   - 只要作业同时配置 `--requeue --signal=B:TERM@120 --open-mode=append`，并在训练/评测循环中捕获 `SIGTERM` 预警信号 + 每步/每条样本原子落盘（`tmp -> flush -> fsync -> os.replace`），即便发生多次抢占也能实现**零算力损失自动续跑**（实测长训连续经历 2 次抢占，Step 264 → Step 608 → Step 770+ 零丢步）。
3. **单卡小粒度 + 贴合实测的 `--time`，吃满 Slurm Backfill 红利**：
   - 大型 8 卡长时任务等待整机凑齐期间，节点会产生大量零散 1–2 卡与数小时空窗；Slurm Backfill 调度器会优先将**申请卡数少（1 卡）且 `--time` 精准合理**（如 1–8 小时，切忌无脑填 `48:00:00`）的作业直接塞入空窗秒开。
4. **提交前先核对实时 `sacctmgr` 与 `sinfo`，多账户灵活路由**：
   - 结合 `yz11502` 下的多项目账户（`torch_pr_50_general`、`torch_pr_50_tandon_advanced`、`torch_pr_50_tandon_priority`、`torch_pr_54_*`），根据当日实时负载选择最优合法账户，不盲抄历史脚本。

### 32.2 为什么 `sbatch --test-only` 对比选路明显优于盲交

`sbatch --test-only` 会让 Slurm 调度器执行完整校验与排期模拟，但**不实际创建或入队作业**，核心优势有四点：

1. **量化对比各候选池的预计开机时间**：对 2–3 个候选 Account + Partition 组合并行跑 `--test-only`，调度器会直接打印预计启动时间与落地节点（2026-11-25 实测同脚本：`torch_pr_50_general` + `l40s,h100,h200,b200` 预计 `04:38` 于 `gl057` 启动，而 `h100_tandon` 预计 `11:58` 于 `gh002` 启动，一眼省下约 7 小时等待）。
2. **当场拦截非法组合**：如 `b200_tandon_prem` 与不兼容 `--qos`、超额 CPU/内存或越界时间上限，在入队前 1 秒报错修正。
3. **零队列污染与零误撤风险**：避免“先盲交 → 发现卡 `Priority` → 手动 `scancel`”带来的误操作与调度历史干扰。
4. **与提交后 `scontrol show job -dd <JOB_ID>` 形成闭环**：预检定通道，提交后立刻回读确认实际生效的 `Partition`、`QOS`、`Requeue`、`TimeLimit`、`Comment`、`Dependency` 与 `StdOut`。

```bash
# 提交前：对比两个合法候选通道的预计启动时间（不入队、无副作用）
sbatch --test-only --account=torch_pr_50_general --partition=l40s,h100,h200,b200 your_job.sbatch
sbatch --test-only --account=torch_pr_50_tandon_advanced --partition=b200_tandon_prem,h200_tandon,h100_tandon your_job.sbatch

# 选定最早通道正式提交并立即回读生效配置
job_id=$(sbatch --parsable --account=torch_pr_50_general --partition=l40s,h100,h200,b200 your_job.sbatch)
scontrol show job -dd "$job_id" | grep -E 'JobId=|Account=|QOS=|Partition=|JobState=|Requeue=|TimeLimit=|Comment=|StdOut='
```

### 32.3 抢占容错与并发评测的数据安全契约

- **优雅接管 `SIGTERM`**：在 Slurm 包装脚本中 `trap` `SIGTERM` 写入预警文件路径（如 `PREEMPT_FILE`），Python 主循环在每条样本或训练步边界检查该标志，一旦触发立即安全落盘并退出特定码（由 Slurm `--requeue` 自动重排）。
- **在训 checkpoint 并发评测必须做只读快照**：当训练任务（如 `train_full`）仍在持续更新 `best_adapter.pt` 时，若要提前用已有 checkpoint 并行跑评测，必须先拷贝为独立只读文件并固定 SHA-256（`cp best_adapter.pt snapshot.pt && chmod a-w snapshot.pt && sha256sum snapshot.pt`），严禁直接读取活跃训练路径，杜绝读写竞态与口径漂移。
- **容器内环境变量显式透传**：Singularity 镜像自带环境变量可能覆盖宿主机 `TMPDIR`，应通过 `SINGULARITYENV_*` 显式透传 `SLURM_TMPDIR`、`TMPDIR`、`LIBFFI_TMPDIR`、`PYTHONPYCACHEPREFIX`、`HF_HOME`、`TORCH_HOME`、`TRITON_CACHE_DIR`，彻底避免节点 `/tmp` 写爆或 `/scratch`（已达 ~86% inode 配额）产生大量碎片缓存。

### 32.4 运维实测补充避坑

- **no-PTY `scp` 卡住时的小包替代路径**：若默认共享 ControlMaster 的 `ssh -O check` 正常且显式 PTY 正常，但 no-PTY `scp` 挂起，切勿关闭共享 master；对于轻量源码包（< 1 MB）或已校验 JSON 收据，可在已认证 PTY 中用 `tar czf - | base64` 传输，落地后立即执行 `sha256sum --strict -c SOURCE_BUNDLE.sha256` 逐项验签（大文件与数据集仍走 Globus）。
- **单点硬件异常精确补跑**：数组评测中若极少数分片在特定节点（如偶发 Hopper `ExitCode 6:0`）异常中止，遵循 §0 保留失败日志，仅对 exact failed indices 指定已验健康分区（如 `l40s,b200`）精确重跑补齐，再以独立 CPU verifier 重放全部结果。

---

## 33. 2026-11-26：NYU Torch 2 小时 GPU 低利用率自动杀卡红线与 H200/B200 单卡多 Worker 装箱规范

### 33.1 实测集群杀卡策略（2026-11-25 现场记录）

2026-11-25 实测作业 `24595359`（`isok_arm5`，单环境串行 `batch=1` Habitat-Sim + 4B VLM 闭环评估）在 `gh115`（`h200`，`gpu48`）运行至 `02:05:24` 时，收到 NYU HPC 自动监控邮件并被强行取消（`cancel_job=1`）：

- **实测参数**：`Partition=h200`，`Node:gh115, GPUIdx:5, AveUtil:38.60`，`warning_criteria=75%`，`cancellation_criteria=60%`，触发窗口为 **连续低利用率超过 2 小时**（阈值取决于 GPU 型号，H200/B200 最严格）。
- **物理根因**：单环境串行 `batch=1` 闭环中，CPU 侧 Habitat 渲染 + 噪声/遮挡合成 + Python 预处理占每步 ~55 ms，而 4B 模型在 H200/B200 上 `batch=1` 前向仅 ~35 ms，导致单进程物理利用率上限被锁在 ~35–40%，超过 2 小时必触发杀卡。

### 33.2 使用 H200 / B200 跑闭环评估的铁律：单卡多 Worker 分片装箱（`AveUtil 85–95%`）

不要为了躲避杀卡而放弃 H200（141 GB）/ B200（180 GB）的算力与快排池，正确做法是**按显存自适应单卡多 Worker 并行装箱**，把 CPU 渲染空窗完全交错填满：

1. **按卡型与模型显存自适应选择单卡并发度 `K`**（脚本启动时读 `nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits`）：
   - **4B 模型（单进程 ~10 GB）**：`B200 (180 GB) → K=5`、`H200 (141 GB) → K=4`、`H100 (80 GB) → K=3`、`L40S (48 GB) → K=2`；
   - **7B–8B 模型（单进程 ~18–22 GB）**：`B200 → K=4`、`H200 → K=3–4`、`H100 → K=2`、`L40S → K=1–2`。
   - 排队估算：单进程利用率 $p \approx 0.386$ 时，`K=4` 独立异步进程并发可将 GPU 空闲率压至 $(1-p)^4 \approx 14\%$（实测 **`AveUtil ≈ 85–95%`**），同时总墙钟耗时缩短 `3–4×`（多数评估压进 `< 1.5 h`，同时享受高利用率与短于 2 小时窗口的双重保护）。
2. **数值完全等价且零模型代码改动**：每个 Worker 仍运行原生 `batch=1` 推理，各跑互不重叠的 episode/arm 分片，写独立原子分片文件 `shard_${k}.json`（无目录锁竞争），全部结束后合并并通过独立 verifier 校验。
3. **CPU 与启动防抖配置**：
   - 按 **`3 CPU 核 / worker`、`20–24 GB RAM / worker`** 申请（如 `K=4` 配 `--cpus-per-task=12 --mem=96G`）；
   - 每个 Worker 强制 `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`，防止多线程抢核饿死 GPU；
   - 错峰启动 `sleep $((k * 5))`，避免 `K` 个进程同秒读权重和 3D 场景引发瞬时 I/O 尖峰。
4. **若确实只能跑单进程串行 `batch=1`**：
   - 严禁在 `--partition` 中混入 `h200` / `b200`，必须锁死 `--partition=l40s`（或 `a100_tandon`），或按 Slurm Array 拆成 `< 1h45m` 短分片；
   - 严禁只靠 `--cpus-per-task=8 --mem=64G` 盲申过多资源，单进程串行 Habitat 用 `--cpus-per-task=4 --mem=32G` 即可。
5. **内嵌 `nvidia-smi` 利用率哨兵（Gate 1 必验）**：
   - 在 sbatch 作业中启动轻量后台采样（每 60 秒记录 `utilization.gpu,memory.used` 与滚动均值），在 Gate 1 前 5–10 分钟即确认 `AveUtil >= 80%`，杜绝盲跑满 2 小时才收到杀卡邮件。

```bash
# 轻量 GPU 利用率哨兵示例（放入 sbatch 后台，作业结束前 kill）
(while true; do
  ts=$(date +%H:%M:%S)
  u=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits | head -n1)
  echo "[GPU_MON $ts] util_pct,mem_used_mb,mem_total_mb = $u"
  sleep 60
done) &
GPU_MON_PID=$!
trap 'kill "$GPU_MON_PID" 2>/dev/null || true' EXIT
```

### 33.3 `/scratch` 与 `/home` 配额预警治理（防 80% 日常报警）

- NYU Torch 任意文件系统空间或文件数超过 **80%** 即持续触发配额预警（2026-11-25 实测：`/scratch` 文件数 `4,331,166 / 5,000,000 = 86.00%`、`/home` 文件数 `20,503 / 30,000 = 68.00%`、`pip` 缓存 `7.2 GB`）。
- 治本原则：① 历史散文件数据集与自建 Conda 环境打成 `.sqf` SquashFS overlay（百万文件 → 1 个 inode，Singularity `--overlay foo.sqf:ro` 零解压直挂）；② 完结历史项目打 `.tar.zst` 迁入 `/archive`（自动备份、不自动清理）；③ 所有作业通过 `SINGULARITYENV_*` 将缓存锁到 `$SLURM_TMPDIR`，实验结果一律单 JSON / 分片合并落盘。
