# NHC + Adaptive Heading Correction Experiment Report — Vw4 Sequence

## Executive Summary & Core Research Answers

> **Research Mandate:** *“Do NOT assume that NHC or heading correction will improve performance. If performance becomes worse, report that honestly.”*

This controlled research experiment evaluated Non-Holonomic Vehicle Constraints (NHC), IMU-based adaptive heading correction, and EKF state fusion on the 100% unseen test partition of Vw4 (`start_idx = 108,000`) across 60s, 120s, and 300s GNSS outages using the exact existing trained CNN + BiLSTM model (`models/cnn_plus_bilstm_w30.pth`).

---

### Core Questions & Definitive Answers

#### 1. Does NHC actually reduce drift?
**Answer:** **NO. Pure 2D NHC alone provides 0.0% reduction in position drift over open-loop 2D DR.**
* **Explanation:** Standard 2D kinematic position propagation ($\mathbf{v}_{\text{ENU}} = [\hat{v}_{\text{fwd}} \sin \psi, \hat{v}_{\text{fwd}} \cos \psi]^T$) already implicitly enforces zero lateral velocity ($v_{\text{lat}} = 0$). Enforcing 2D NHC mathematically reproduces Case A baseline exactly across all outages.

#### 2. Does adaptive heading correction actually reduce drift?
**Answer:** **YES.** **Case C (ML Speed + NHC + Adaptive Heading Correction)** achieves consistent, measurable drift reductions across all outage durations:
* **60s Outage:** Final position error drops from **364.70 meters (Baseline Case A)** down to **287.80 meters (Case C)** — a **21.1% drift reduction** ($4.80\text{ m/s}$ drift rate). Heading RMSE improves from **57.62° down to 39.88°**.
* **120s Outage:** Final position error drops from **1,024.64 meters (Baseline Case A)** down to **751.04 meters (Case C)** — a **26.7% drift reduction** ($6.26\text{ m/s}$ drift rate). Heading RMSE improves from **70.68° down to 40.45°**.
* **300s Outage:** Final position error drops from **1,465.33 meters (Baseline Case A)** down to **1,281.43 meters (Case C)** — a **12.6% drift reduction** ($4.27\text{ m/s}$ drift rate).

#### 3. Does EKF fusion (Case D) improve over current ML-DR?
**Answer:** **NO, IT DEGRADES PERFORMANCE.** EKF fusion (Case D) performed **worse** than open-loop Case C (and worse than Baseline Case A at 60s and 120s):
* **60s Outage:** Case D error increases to **659.58 m** (vs **364.70 m** for Baseline Case A and **287.80 m** for Case C).
* **120s Outage:** Case D error increases to **1,348.81 m** (vs **1,024.64 m** for Baseline Case A and **751.04 m** for Case C).
* **300s Outage:** Case D error increases to **1,575.35 m** (vs **1,465.33 m** for Baseline Case A and **1,281.43 m** for Case C).
* **Root Cause Analysis:** In the absence of GNSS position updates, unconstrained accelerometer bias drift ($b_a$) inside the 7-state EKF process Jacobian bleeds into velocity state propagation ($v_x, v_y$). Closed-loop ML speed measurement updates inside the EKF struggle against double-integrated accel drift, whereas open-loop kinematic integration (Case C) directly relies on bounded ML speed $\hat{v}_{\text{ML}}$.

#### 4. Which component provides the largest improvement?
**Answer:** **Adaptive Heading Correction (Straight-Line Zero-Lock + Centrifugal Acceleration Consistency Rule in Case C).**
* It achieved the lowest overall position error and lowest heading RMSE ($39.88^\circ$ at 60s, $40.45^\circ$ at 120s) without adding filter instability.

#### 5. What should be the SINGLE next experiment?
**Answer:** **Train an End-to-End Orientation-Aware Motion Network (Predicting 2D Displacement $[\Delta x, \Delta y]$ + Delta Heading $\Delta \psi$) OR Implement a Closed-Loop Heading-Constrained Graph Optimizer / Particle Filter.**

---

## 2. Quantitative Experimental Results Matrix

| Outage Duration | Experimental Candidate | Distance Traveled | CDE % | Final Pos Error (m) | Max Pos Error (m) | Drift Rate (m/s) | Speed MAE (km/h) | Final Heading Error (°) | Heading RMSE (°) | Latency (ms/step) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **60 sec** | **Case A: Existing ML-DR Baseline** | $855.33\text{ m}$ | 46.89% | 364.70 m | 364.70 m | 6.08 m/s | 13.16 km/h | 45.11° | 57.62° | 0.0020 ms |
| **60 sec** | **Case B: ML Speed + NHC Constraint** | $855.33\text{ m}$ | 46.89% | 364.70 m | 364.70 m | 6.08 m/s | 13.16 km/h | 45.11° | 57.62° | 0.0034 ms |
| **60 sec** | **Case C: ML Speed + NHC + Adaptive Heading** | $855.33\text{ m}$ | **46.89%** | **287.80 m** | **287.80 m** | **4.80 m/s** | 13.16 km/h | **34.97°** | **39.88°** | **0.0028 ms** |
| **60 sec** | **Case D: ML Speed + NHC + Heading + EKF** | $855.33\text{ m}$ | 39.70% | 659.58 m | 659.58 m | 10.99 m/s | **10.10 km/h** | 157.61° | 145.51° | 0.0335 ms |
| | | | | | | | | | | |
| **120 sec** | **Case A: Existing ML-DR Baseline** | $1,798.54\text{ m}$ | 56.97% | 1,024.64 m | 1,024.64 m | 8.54 m/s | 16.28 km/h | 109.76° | 70.68° | 0.0018 ms |
| **120 sec** | **Case B: ML Speed + NHC Constraint** | $1,798.54\text{ m}$ | 56.97% | 1,024.64 m | 1,024.64 m | 8.54 m/s | 16.28 km/h | 109.76° | 70.68° | 0.0030 ms |
| **120 sec** | **Case C: ML Speed + NHC + Adaptive Heading** | $1,798.54\text{ m}$ | **56.97%** | **751.04 m** | **751.04 m** | **6.26 m/s** | 16.28 km/h | **59.62°** | **40.45°** | **0.0027 ms** |
| **120 sec** | **Case D: ML Speed + NHC + Heading + EKF** | $1,798.54\text{ m}$ | 49.87% | 1,348.81 m | 1,348.81 m | 11.24 m/s | **13.36 km/h** | 158.19° | 137.42° | 0.0340 ms |
| | | | | | | | | | | |
| **300 sec** | **Case A: Existing ML-DR Baseline** | $2,555.32\text{ m}$ | 57.34% | 1,465.33 m | 1,465.33 m | 4.88 m/s | 10.94 km/h | 52.96° | 69.41° | 0.0018 ms |
| **300 sec** | **Case B: ML Speed + NHC Constraint** | $2,555.32\text{ m}$ | 57.34% | 1,465.33 m | 1,465.33 m | 4.88 m/s | 10.94 km/h | 52.96° | 69.41° | 0.0032 ms |
| **300 sec** | **Case C: ML Speed + NHC + Adaptive Heading** | $2,555.32\text{ m}$ | **57.34%** | **1,281.43 m** | **1,281.43 m** | **4.27 m/s** | 10.94 km/h | 103.02° | **53.68°** | **0.0027 ms** |
| **300 sec** | **Case D: ML Speed + NHC + Heading + EKF** | $2,555.32\text{ m}$ | 51.11% | 1,575.35 m | 1,639.13 m | 5.25 m/s | **8.98 km/h** | **22.65°** | 97.01° | 0.0387 ms |

---

## 3. Mathematical & Physical Sanity Verification

1. **Zero Ground-Truth Leakage:** No satellite GNSS position, velocity, or heading data was accessed during outage windows.
2. **Causal Processing:** Adaptive heading correction rules operate purely on instantaneous and past IMU accelerations ($a_{\text{lat, IMU}}$) and ML predictions ($\hat{w}_{\text{ML}}$). No future samples are used.
3. **VBOX Ground Truth Usage:** VBOX data was strictly isolated for post-experiment error calculation and trajectory plotting.

---

## 4. Persistence Artifacts

- Experiment Engine Script: [`scripts/vw4_ml_nhc_heading_experiment.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_ml_nhc_heading_experiment.py)
- Structured JSON Results: [`results/vw4_ml_nhc_heading_results.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_ml_nhc_heading_results.json)
- Generated Plots:
  - Trajectory: [`plots/vw4/ml_nhc_heading/outage_300s_trajectory.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_nhc_heading/outage_300s_trajectory.png)
  - Position Error Growth: [`plots/vw4/ml_nhc_heading/outage_300s_position_error.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_nhc_heading/outage_300s_position_error.png)
  - Heading Error Growth: [`plots/vw4/ml_nhc_heading/outage_300s_heading_error.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_nhc_heading/outage_300s_heading_error.png)
  - Speed Error Growth: [`plots/vw4/ml_nhc_heading/outage_300s_velocity_error.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_nhc_heading/outage_300s_velocity_error.png)
  - Summary Bar Chart: [`plots/vw4/ml_nhc_heading/summary_ablation_metrics.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_nhc_heading/summary_ablation_metrics.png)
