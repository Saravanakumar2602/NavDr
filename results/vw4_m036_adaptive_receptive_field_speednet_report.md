# Milestone M036 — Adaptive Receptive-Field SpeedNet Backbone Tuning Report

## Executive Summary

- **Milestone:** M036 — Adaptive Receptive-Field SpeedNet Backbone Tuning
- **Objective:** Evaluate whether varying the neural sequence receptive field ($W \in [30, 40, 50]$) or constructing a multi-branch adaptive temporal backbone reduces SpeedNet speed overestimation without introducing temporal phase lag or degrading 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Pointwise Speed MAE vs Integrated Navigation Disconnect:** Candidate F3 (Multi-Branch Ensemble) achieved the lowest pointwise speed MAE ($11.85\text{ km/h}$ vs Control $12.38\text{ km/h}$) and lowest 60s test error ($14.65\text{ m}$). However, F3 degraded 300s position drift to **`1275.85 m`** (**+482.8% degradation**).
  - **Validation Selection:** Candidate F2 ($W=50$ Longer Receptive Field) achieved the lowest validation 300s error ($400.40\text{ m}$ vs Control $494.83\text{ m}$).
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), validation winner F2 ($W=50$) exploded 300s position drift to **`1165.94 m`** (**+432.6% degradation** vs Control `218.93 m`) and degraded 120s error to $930.98\text{ m}$ (vs $426.85\text{ m}$).
  - **Failure Mechanism:** $W=30$ increases high-frequency noise due to loss of IMU temporal vibration smoothing. $W=50$ introduces temporal phase lag during braking transients, causing positive speed overestimation to leak into EKF velocity integration. Multi-branch ensembling distorts phase alignment across sliding windows.
  - **Receptive Field Lock:** **SpeedNet v2 $W=40$ is confirmed as the optimal, locked temporal receptive field**.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 4 — Pointwise Speed & Regime MAE Analysis (Validation Partition `88566:107535`)

| Candidate ID | Model Architecture Description | Parameters | Overall MAE | Braking MAE | Accel MAE | Cruise MAE | Turn MAE |
|---|---|---|---|---|---|---|---|
| **F0 (Control)** | **SpeedNet v2 W=40 Control** | **370,686** | **12.38 km/h** | **13.63 km/h** | **12.25 km/h** | **11.07 km/h** | **13.31 km/h** |
| **F1** | SpeedNet v2 W=30 Shorter | 370,686 | $13.19\text{ km/h}$ | $14.32\text{ km/h}$ | $13.23\text{ km/h}$ | $11.93\text{ km/h}$ | $14.28\text{ km/h}$ |
| **F2** | SpeedNet v2 W=50 Longer | 370,686 | $12.60\text{ km/h}$ | $13.82\text{ km/h}$ | $12.36\text{ km/h}$ | $11.13\text{ km/h}$ | $13.73\text{ km/h}$ |
| **F3** | Multi-Branch Ensemble (W30/W40/W50) | 1,112,058 | **11.85 km/h** | **13.05 km/h** | **11.67 km/h** | **10.44 km/h** | **12.85 km/h** |

---

## Phase 5 — Validation Navigation Evaluation (`88566:107535`)

| Candidate ID | Model Architecture Description | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | SpeedNet v2 W=40 Control Baseline | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | SpeedNet v2 W=30 Shorter | $1,023.05\text{ m}$ | $410.78\text{ m}$ | Degraded |
| **F2** | **SpeedNet v2 W=50 Longer** | **400.40 m** | **377.32 m** | **SELECTED VALIDATION WINNER** |
| **F3** | Multi-Branch Ensemble | $784.57\text{ m}$ | $300.86\text{ m}$ | Degraded at 300s |

---

## Phase 6 — Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 (W=30 Shorter)** | $9.07\text{ km/h}$ | $14.03\text{ km/h}$ | $191.43\text{ m}$ | $1,108.72\text{ m}$ | **1287.41 m** | $+389.3\%$ | $+484.9\%$ | **+488.0%** |
| **F2 (Val Winner W=50)** | **8.72 km/h** | **14.86 km/h** | **97.71 m** | **930.98 m** | **1165.94 m** | **+343.1%** | **+429.7%** | **+432.6%** |
| **F3 (Multi-Branch)** | $8.01\text{ km/h}$ | $13.04\text{ km/h}$ | $14.65\text{ m}$ | $1,045.15\text{ m}$ | **1275.85 m** | $+384.9\%$ | $+479.6\%$ | **+482.8%** |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M028 W=40)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |
| **F2 (Val Winner W=50)** | **705.42 m** | **1165.94 m** | **-1135.21 m** | **266.18 m** |

---

## Failure Mechanism & Receptive Field Lock

1. **Phase Lag in Larger Windows ($W=50$):** Receptive field expansion ($W=50$) introduces temporal phase lag during braking transients ($14.86\text{ km/h}$ braking MAE on test vs $11.57\text{ km/h}$ control). Lagging speed estimates leak into EKF velocity integration, exploding 300s position drift from $218.93\text{ m}$ to $1165.94\text{ m}$.
2. **Noise Propagation in Shorter Windows ($W=30$):** Receptive field reduction ($W=30$) loses IMU temporal vibration smoothing, increasing prediction jitter and exploding position drift to $1287.41\text{ m}$.
3. **Receptive Field Lock:** $W=40$ represents the optimal, locked temporal window for SpeedNet v2.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m036_adaptive_receptive_field_speednet.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m036_adaptive_receptive_field_speednet.py)
- **Summary JSON:** `results/vw4_m036_adaptive_receptive_field_speednet_summary.json`
- **Report Markdown:** [`results/vw4_m036_adaptive_receptive_field_speednet_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m036_adaptive_receptive_field_speednet_report.md)
- **Plot Directory:** `plots/vw4/m036_adaptive_receptive_field_speednet/`
  - `pos_error_vs_time.png`

---

## Final M036 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
