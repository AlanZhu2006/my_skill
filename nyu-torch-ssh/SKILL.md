---
name: nyu-torch-ssh
description: Operate shared NYU Torch HPC SSH ControlMaster sessions, Slurm GPU queues (including B200 preemptible, H100/A100 Tandon, and L40S public), Singularity containers, immutable source bundles, and scratch quota hygiene safely. Use when connecting to NYU Torch via `alantorch` or `torch`, verifying user identity (`yz11502`), running `sbatch --test-only`, submitting or monitoring Slurm jobs, transferring datasets/bundles via SCP or Globus, or troubleshooting SSH mux/PTY stalls.
---

# NYU Torch SSH & Slurm Operations

Use this skill whenever interacting with NYU Torch HPC (`login.torch.hpc.nyu.edu`). The full verified runbook, command recipes, and chronological incident records (§0–§32) live in [`references/ssh_handbook.md`](references/ssh_handbook.md). Always read the relevant section of `references/ssh_handbook.md` before submitting jobs, changing partitions/accounts, or troubleshooting SSH/Slurm issues.

## Six Non-Negotiable Rules (§0)

1. **Verify account identity first**: Reuse the active shared `alantorch`/`torch` ControlMaster belonging to `yz11502`. Always verify both `ssh -G` / `ssh -O check` and remote `id -un == yz11502`. Never reuse, kill, or replace another user's socket (such as `yz11445`).
2. **Never touch other users' processes or sockets**: Do not run `ssh -O exit` on a shared master, and never cancel or modify Slurm jobs you did not submit.
3. **Never submit duplicate jobs**: Confirm existing queue state (`squeue -u yz11502`) and run `sbatch --test-only` before submitting. Validate one full end-to-end single-GPU job before launching arrays or sweeps.
4. **Use immutable, checksum-verified source bundles**: Package code into a read-only bundle (`chmod -R a-w`) with relative-path `SOURCE_BUNDLE.sha256`, verify `sha256sum -c SOURCE_BUNDLE.sha256` both locally and remotely (and inside the Slurm job before running Python), and never mutate code under a running job.
5. **Protect `/scratch` inode quota**: Keep persistent run roots compact; route `TMPDIR`, `LIBFFI_TMPDIR`, `PYTHONPYCACHEPREFIX`, and ephemeral caches to `$SLURM_TMPDIR`. Never dump tens of thousands of loose files into `/scratch`.
6. **Verify live cluster state, never assume stale defaults**: Check live `sacctmgr`, `sinfo`, `myquota`, and `scontrol show job -dd <JOB_ID>` readbacks; update `references/ssh_handbook.md` whenever verified cluster rules change.

## Quick Reference

### 1. SSH Identity & Master Check (§1, §1.5, §31)

```bash
ssh -G alantorch | grep -E '^(user|hostname|controlpath|controlmaster|controlpersist) '
ssh -O check alantorch
ssh -o BatchMode=yes alantorch 'id -un; hostname'
```

- When passing an explicit ControlPath to `scp`, use `-o ControlPath=...` (never `-S`).
- Avoid running `import torch` or deep `find` scans over shared NFS conda directories on login nodes; inspect version files directly or run Python checks on compute nodes.

### 2. Verified Accounts, Fast Multi-Partition Scheduling & `--test-only` (§23, §31, §32)

Check active associations with `sacctmgr -nP show assoc where user=yz11502 format=Cluster,Account,User,Partition,QOS,DefaultQOS`, then compare 2–3 candidate account/partition pools with `sbatch --test-only` before submitting:

- **Why always compare with `sbatch --test-only` first**: Slurm runs the real scheduler dry-run without entering the queue, immediately showing the **estimated start time and target partition/node** (often hours earlier across pools), catching invalid account/QOS/partition/GRES combinations up front, and avoiding blind queue stalls or `sbatch -> scancel` churn. Always follow the actual `sbatch` with `scontrol show job -dd <JOB_ID>`.
- **Fast scheduling via multi-partition pools + preemptible B200 + Backfill**:
  - Combine compatible partitions in one `--partition=...` list so Slurm grabs the earliest open GPU instead of waiting on a single busy queue (e.g., `--account=torch_pr_50_general --partition=l40s,h100,h200,b200` for single-GPU evals, or `--account=torch_pr_50_tandon_advanced --partition=h200,b200_tandon_prem,b200` for 2-GPU training).
  - **Preemptible B200 (all 5 project accounts)**: omit `--qos` and pass `--comment="preemption=yes;requeue=true" --requeue --signal=B:TERM@120` with `--gres=gpu:b200:1` (or multi-partition list):
    - `torch_pr_50_general`, `torch_pr_54_general` → partition `b200`
    - `torch_pr_50_tandon_advanced`, `torch_pr_50_tandon_priority`, `torch_pr_54_tandon_advanced` → partition `b200_tandon_prem`
    - Always trap `SIGTERM`, write atomic checkpoints (`tmp -> fsync -> os.replace`), and pass `--open-mode=append` so preemption loses zero progress.
  - **Backfill discipline**: Prefer 1-GPU jobs/shards with measured realistic `--time` bounds (not blind `48:00:00`) so Slurm Backfill schedules them immediately in gaps left by large multi-GPU reservations.
  - **Live-training checkpoint isolation**: Never evaluate directly against a live training run's actively overwritten `best_adapter.pt`; copy it once into a read-only (`chmod a-w`) SHA-256-verified snapshot first.
- **Standard non-preemptible GPU queues (`--qos=gpu48`)**:
  - `torch_pr_50_tandon_priority`: `h100_tandon`, `a100_tandon`, `l40s_public`
  - `torch_pr_50_tandon_advanced` / `torch_pr_54_tandon_advanced`: `h200_tandon`, `h100_tandon`, `a100_tandon`
  - `torch_pr_50_general` / `torch_pr_54_general`: `h200_public`, `l40s_public` (verify live availability via `sbatch --test-only`).

### 3. Container & Conda Execution Pattern (§9.4, §31)

```bash
singularity exec --nv \
  -B /scratch/lg154 -B /scratch/yz11502 \
  /share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif \
  /scratch/lg154/conda-envs/memnav/bin/python your_script.py
```

- Never mutate shared conda environments under `/scratch/lg154/conda-envs/`.
- See [`references/ssh_handbook.md`](references/ssh_handbook.md) for Globus large transfers (§4.2), read-only localhost tunnels (§1.4), Singularity overlay mounts (§9), and full troubleshooting tables (§12–§31).
