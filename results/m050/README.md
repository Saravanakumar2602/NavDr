# M050 — Learned Body-Frame Velocity Representation Summary

## Executive Summary
Milestone **M050** evaluated whether replacing scalar speed predictions ($v_{\text{fwd}}$) with deep-learned **body-frame velocity vector representations** ($v_{\text{forward}}, v_{\text{lateral}}$) improves integrated dead-reckoning navigation accuracy over the locked M028 production baseline ($218.93\text{ m}$ @ 300s).

Despite candidate **F1** (Body Velocity Network) winning candidate selection on validation by achieving a 300s validation navigation error of **107.48 m** (vs Control F0's $1248.83\text{ m}$), its performance collapsed on the unseen locked test set to **817.69 m** (+273.7% error explosion over M028).

Therefore, **M050 is officially classified as a GENERALIZATION FAILURE**. Production pipeline remains **100% UNCHANGED** at M028 baseline.

---

## Validation & Test Candidate Comparison

| Candidate | Description | Val 300s Error | Test 60s Error | Test 120s Error | Test 300s Error | Test 1km Error | Max Compliant Dist | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F0 (Control)** | M028 SpeedNet v2 (W=40) | 1248.83 m | **27.83 m** | **426.38 m** | **218.76 m** | **307.74 m** | **422.09 m** | **CONTROL** |
| **F1 (Selected)**| Dual-head Body Velocity ($v_{\text{fwd}}, v_{\text{lat}}$) | **107.48 m** | 383.88 m | 809.64 m | 817.69 m | 931.30 m | 0.00 m | **GENERALIZATION FAILURE** |
| **F2** | Multi-Task Velocity + Speed | 313.08 m | 22.61 m | 1114.77 m | 1577.72 m | 1429.40 m | 423.11 m | REJECTED |
| **F3** | Multi-Task Velocity + Accel | 697.52 m | 9.57 m | 925.36 m | 1277.49 m | 1186.09 m | 429.25 m | REJECTED |
| **F4** | Multi-Task Velocity + Speed + Accel | 164.32 m | 37.30 m | 1011.56 m | 1359.46 m | 1226.83 m | 415.02 m | REJECTED |

---

## Key Scientific Lessons
1. **Validation Overfitting**: Learning $v_{\text{forward}}$ and $v_{\text{lateral}}$ simultaneously without scalar speed constraints causes the network to overfit local trajectory dynamics in validation, leading to severe out-of-distribution drift on unseen test trajectories.
2. **Breakdown of EKF Geometric Self-Cancellation**: Predicting lateral velocity $v_{\text{lateral}}$ directly introduces systematic lateral biases that degrade EKF heading and cross-track damping during turns.
3. **Scalar Speed Anchor Importance**: Scalar forward speed predictions ($v_{\text{fwd}}$) act as a strong positive velocity anchor. Vector velocity targets without strict speed regularizers remove this dampening effect, accelerating error growth.

---

## Artifact Paths
- Python script: [`scripts/vw4_m050_learned_body_velocity.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m050_learned_body_velocity.py)
- Execution JSON: `results/m050/m050_results.json`
- Milestone Document: [`milestones/M050.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/milestones/M050.md)
- Diagnostic Plots: `results/plots/m050_*.png`
