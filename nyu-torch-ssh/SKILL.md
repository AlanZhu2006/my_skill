---
name: nyu-torch-ssh
description: Operate shared NYU Torch HPC SSH ControlMaster sessions, Slurm GPU queues (including B200 preemptible, H100/A100 Tandon, and L40S public), Singularity containers, immutable source bundles, and scratch quota hygiene safely. Use when connecting to NYU Torch via `alantorch` or `torch`, verifying user identity (`yz11502`), running `sbatch --test-only`, submitting or monitoring Slurm jobs, transferring datasets/bundles via SCP or Globus, or troubleshooting SSH mux/PTY stalls.
---

# NYU Torch SSH & Slurm Operations

Use this skill whenever interacting with NYU Torch HPC (`login.torch.hpc.nyu.edu`). The full verified runbook, command recipes, and chronological incident records (§0–§31) live in [`references/ssh_handbook.md`](references/ssh_handbook.md). Always read the relevant section of `references/ssh_handbook.md` before submitting jobs, changing partitions/accounts, or troubleshooting SSH/Slurm issues.

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

### 2. Verified Accounts & GPU Partitions (§23, §31)

Check active associations with `sacctmgr -nP show assoc where user=yz11502 format=Cluster,Account,User,Partition,QOS,DefaultQOS` and test with `sbatch --test-only` before submitting:

- **Preemptible B200 (all 5 project accounts)**: omit `--qos` and pass `--comment="preemption=yes;requeue=true"` with `--gres=gpu:b200:1`:
  - `torch_pr_50_general`, `torch_pr_54_general` → partition `b200`
  - `torch_pr_50_tandon_advanced`, `torch_pr_50_tandon_priority`, `torch_pr_54_tandon_advanced` → partition `b200_tandon_prem`
  - Always handle `SIGTERM` and write atomic checkpoints for preemptible runs.
- **Standard non-preemptible GPU queues (`--qos=gpu48`)**:
  - `torch_pr_50_tandon_priority`: `h100_tandon`, `a100_tandon`, `l40s_public`
  - `torch_pr_50_general` / `torch_pr_54_general`: `l40s_public` (and check current `h200_public` / `h100_public` availability via `sbatch --test-only`).

### 3. Container & Conda Execution Pattern (§9.4, §31)

```bash
singularity exec --nv \
  -B /scratch/lg154 -B /scratch/yz11502 \
  /share/apps/images/cuda12.8.1-cudnn9.8.0-ubuntu24.04.2.sif \
  /scratch/lg154/conda-envs/memnav/bin/python your_script.py
```

- Never mutate shared conda environments under `/scratch/lg154/conda-envs/`.
- See [`references/ssh_handbook.md`](references/ssh_handbook.md) for Globus large transfers (§4.2), read-only localhost tunnels (§1.4), Singularity overlay mounts (§9), and full troubleshooting tables (§12–§31).
