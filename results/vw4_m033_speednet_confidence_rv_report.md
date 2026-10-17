# Milestone M033 — Causal SpeedNet Confidence-Weighted Velocity Innovation Fusion Report

## Executive Summary

- **Milestone:** M033 — Causal SpeedNet Confidence-Weighted Velocity Innovation Fusion
- **Objective:** Evaluate whether scaling SpeedNet's measurement covariance $R_v(k) = R_0 (1 + \beta \cdot \sigma_{a, \text{causal}}^2)$ dynamically based on causal longitudinal acceleration variance reduces dead-reckoning drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Phase 1 Diagnostic Evidence:** Causal longitudinal acceleration variance exhibits a weak positive rank correlation with absolute SpeedNet error ($\rho = 0.2320$ for 0.5s window). SpeedNet MAE in the highest variance quartile (Q4 = $13.37\text{ km/h}$) was 1.58x higher than the lowest quartile (Q1 = $8.44\text{ km/h}$).
  - **Validation Selection:** Candidate F1 ($\beta = 0.01$, 0.5s window) was selected on the validation partition (`88566:107535`) with 300s position error of $489.30\text{ m}$ (vs F0 Control $494.83\text{ m}$).
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), the validation winner F1 ($\beta = 0.01$) degraded 300s position error to **`225.86 m`** ($+6.93\text{ m}$ / **+3.2% degradation** vs Control `218.93 m`) and degraded 120s error to $444.56\text{ m}$ (vs $426.85\text{ m}$). Higher values of $\beta$ ($\beta \ge 0.05$) caused catastrophic drift explosion ($348.16 - 711.51\text{ m}$).
  - **Failure Mechanism:** Down-weighting SpeedNet updates during high-variance transients forces the EKF into open-loop double-integration of noisy IMU acceleration, accelerating tilt/bias error accumulation and degrading multi-horizon trajectory stability.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 1 — Causal Acceleration Variance Diagnostic (`88566:107535`)

| Window Length | Pearson Correlation ($r$) | Spearman Rank Correlation ($\rho$) | Q1 Speed MAE (km/h) | Q4 Speed MAE (km/h) | Q4/Q1 Error Ratio | Selection Status |
|---|---|---|---|---|---|---|
| **0.5s (5 samples)** | **+0.0240** | **+0.2320** | **8.44 km/h** | **13.37 km/h** | **1.58x** | **SELECTED BEST WINDOW** |
| **1.0s (10 samples)** | $+0.0249$ | $+0.2296$ | $8.36\text{ km/h}$ | $12.90\text{ km/h}$ | $1.54\text{ x}$ | Secondary |
| **2.0s (20 samples)** | $+0.0223$ | $+0.2098$ | $8.72\text{ km/h}$ | $12.18\text{ km/h}$ | $1.40\text{ x}$ | Secondary |
| **5.0s (50 samples)** | $-0.0126$ | $+0.1490$ | $9.73\text{ km/h}$ | $11.49\text{ km/h}$ | $1.18\text{ x}$ | Weakest |

---

## Phase 2 & 3 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Scaling Parameter ($\beta$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | $\beta = 0.00$ (Fixed $R_v = 1.0$) | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | $\mathbf{\beta = 0.01}$ | **489.30 m** | **346.38 m** | **SELECTED VALIDATION WINNER** |
| **F2** | $\beta = 0.05$ | $807.11\text{ m}$ | $327.42\text{ m}$ | Degraded |
| **F3** | $\beta = 0.10$ | $1,093.39\text{ m}$ | $309.01\text{ m}$ | Severely Degraded |
| **F4** | $\beta = 0.25$ | $1,295.84\text{ m}$ | $305.52\text{ m}$ | Severely Degraded |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\beta = 0.01$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.22\text{ m}$ | $444.56\text{ m}$ | **225.86 m** | $-14.2\%$ | $+2.6\%$ | **+3.2%** |
| **F2 ($\beta = 0.05$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $26.59\text{ m}$ | $571.73\text{ m}$ | **348.16 m** | $+32.3\%$ | $+58.2\%$ | **+59.0%** |
| **F3 ($\beta = 0.10$)** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $25.70\text{ m}$ | $761.15\text{ m}$ | **553.97 m** | $+110.5\%$ | $+151.7\%$ | **+153.0%** |
| **F4 ($\beta = 0.25$)** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $23.07\text{ m}$ | $917.65\text{ m}$ | **711.51 m** | $+170.4\%$ | $+223.2\%$ | **+225.0%** |
| **F5 (Val Winner F1)** | **7.33 km/h** | **11.57 km/h** | **27.22 m** | **444.56 m** | **225.86 m** | **-14.2%** | **+2.6%** | **+3.2%** |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M028)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |
| **F5 (Val Winner F1)** | **315.82 m** | **225.86 m** | **-186.42 m** | **128.05 m** |

---

## Failure Mechanism Analysis

Scaling measurement variance $R_v(k) = R_0 (1 + \beta \sigma_a^2)$ during high-acceleration transients reduces Kalman Gain ($K_v = \frac{P H_v^T}{H_v P H_v^T + R_v}$). Consequently, EKF velocity updates are suppressed during dynamic maneuvers, forcing the filter to rely on open-loop double-integration of noisy accelerometer measurements. Unobservable IMU tilt errors accumulate rapidly during open-loop propagation, degrading 120s and 300s position drift.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m033_speednet_confidence_rv.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m033_speednet_confidence_rv.py)
- **Summary JSON:** `results/vw4_m033_speednet_confidence_rv_summary.json`
- **Report Markdown:** [`results/vw4_m033_speednet_confidence_rv_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m033_speednet_confidence_rv_report.md)
- **Plot Directory:** `plots/vw4/m033_speednet_confidence_rv/`
  - `pos_error_vs_time.png`

---

## Final M033 Verdict & Active Benchmark

**REJECTED (BRANCH PERMANENTLY CLOSED)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
