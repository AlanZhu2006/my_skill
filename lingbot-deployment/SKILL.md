---
name: lingbot-deployment
description: Run LingBot-Map streaming RGB-to-3D reconstruction, consume exported camera extrinsics accurately, select the FlashInfer attention backend, build joint multi-run streaming sessions, and render causally verified incremental point-cloud videos. Use when deploying or debugging LingBot-Map (`lingbot-map-long.pt`), diagnosing trajectory/point-cloud ghosting or reprojection errors, or auditing LingBot-Map outputs.
---

# LingBot-Map Deployment & Operations

Use this skill whenever running LingBot-Map, consuming its exported poses/depth maps, or rendering incremental 3D reconstruction videos. The complete verified operations handbook and experimental evidence live in [`references/lingbot_deployment.md`](references/lingbot_deployment.md). Always consult it for full recipes, script arguments, and known limitations.

## Environment Setup (§1)

Export all three variables before running LingBot-Map (required for FlashInfer JIT compilation and `-lcudart` linking; do not reinstall or mutate the shared conda env or shared `/home/asus/Research/lingbot-map` checkout):

```bash
export PATH=/home/asus/miniconda3/envs/lingbot-map/bin:$PATH
export CUDA_HOME=/home/asus/miniconda3/envs/lingbot-map
export LIBRARY_PATH=/home/asus/miniconda3/envs/lingbot-map/targets/x86_64-linux/lib${LIBRARY_PATH:+:$LIBRARY_PATH}
```

- Python: `/home/asus/miniconda3/envs/lingbot-map/bin/python`
- Checkpoint: `/home/asus/Research/lingbot-map/weights/lingbot-map-long.pt`
- Ignore the initial `pretrained_path: ''` constructor warning as long as the full checkpoint loads with zero missing/unexpected keys.

## Mandatory Conventions (§2)

1. **Pose double-inversion rule (§2.1)**:
   - `pose_encoding_to_extri_intri` outputs OpenCV `w2c`; `demo.py` inverts it once on export.
   - Use the exported matrix directly as `c2w` for camera centers/trajectories, **but** pass it through the official `unproject_depth_map_to_point_map` pipeline (which inverts it again) when unprojecting depth into 3D points.
   - Missing this causes late-sequence translation ghosting (~33–41 px median LK reprojection residual instead of ~1.5–2.9 px).
2. **Use FlashInfer, not `--use_sdpa`, for long sequences (§2.2)**:
   - `SDPAAttention.forward` currently appends k/v even when `_skip_append=True`, breaking equivalence whenever `keyframe_interval > 1`. Only use `--use_sdpa` when `keyframe_interval == 1`.
3. **Let `demo.py` choose `keyframe_interval` (§2.3)** (`1` for ≤320 frames, `ceil(N/320)` otherwise) and preserve official precision (`bf16` aggregator weights, `fp32` heads; §2.4).
4. **Respect streaming input constraints (§2.5–§2.6)**:
   - Feed dense RGB frames (stride 1 for smooth walking), image dimensions divisible by `patch_size=14` (`image_size=518`), `streaming` for ≤320 cached frames and `windowed` for very long sequences.
   - Outputs are in model units (not meters) without gravity; estimate the ground plane from the camera trajectory plane + known camera height rather than fitting the noisy point cloud directly.
5. **Do not post-register separate sessions; build a joint streaming session (§2.7, §2.9)**:
   - Separate LingBot sessions exhibit non-rigid relative drift (~26 cm median residual even after Sim(3) ICP).
   - To compare two runs sharing a release pose in one coordinate frame, concatenate Run 1 (reversed) + Run 2 (forward) into a single streaming session (raise `--max_frame_num 2048` if >1024 frames) and document pose causality explicitly.

## Verification Checklist (§3–§5)

Change **one setting at a time** and never hide pose bugs with point filtering. Verify every new integration with:

1. **LK reprojection check** (`audit_pose_convention.py`): median pairwise reprojection residual should be single-digit pixels (typically 1.5–2.9 px, not >30 px).
2. **Official viewer parity check**: point coordinates should agree with official viewer unprojection to ~`1e-7` model units.
3. **Trajectory Sim(3) diagnostic** (`inspect_lingbot.py`): comparative sanity check against odometry only (never treated as ground-truth metric accuracy).
4. **Causal visibility check** (`render_lingbot.py`): confirm `causal visibility PASS` (no point cloud rendered before its timestamp; first 8 frames act as scale anchor).

See [`references/lingbot_deployment.md`](references/lingbot_deployment.md) for full end-to-end commands, joint-session rendering rules (§2.8–§2.9), and outdoor/indoor delivery notes (§6–§17).
