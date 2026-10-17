# Milestone M028 — Causal IMU Longitudinal-Acceleration Jerk Gating for APM Report

## Executive Summary

- **Milestone:** M028 — Causal IMU Longitudinal-Acceleration Jerk Gating for APM
- **Objective:** Evaluate whether a causal longitudinal acceleration jerk gate ($j_{\text{long}} = \frac{a_{\text{long}}[k] - a_{\text{long}}[k-1]}{\Delta t} < \text{threshold}$) can detect immediate mechanical braking onset zero-latency, refining M019 APM speed damping selectivity and lowering 300s dead-reckoning position drift below $220.12\text{ m}$.
- **Verdict:** **ACCEPTED (F5 / F2 Candidate: $j_{\text{long}} < -1.00\text{ m/s}^3$)**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Validation Selection:** Candidate F2 ($j_{\text{long}} < -1.00\text{ m/s}^3$) won validation selection with a 300s validation set position error of **$494.83\text{ m}$** (vs F0 Control $505.40\text{ m}$, a **$-10.57\text{ m}$ improvement**).
  - **Locked Test Evaluation of Validation Winner:** Evaluated on the locked unseen test partition (`start_idx = 108,000`), Validation Winner F2 / F5 achieved **`218.93 m` @ 300s** (60s = **`27.35 m`**, 120s = **`426.85 m`**), achieving consistent all-horizon position error reductions (**$-0.18\text{ m}$ @ 60s**, **$-1.94\text{ m}$ @ 120s**, **$-1.19\text{ m}$ @ 300s**).
  - **Plausible Physical Mechanism:** Unlike neural speed trends (M027), IMU acceleration jerk responds zero-latency to mechanical brake onset. Causal jerk gating ($j_{\text{long}} < -1.00\text{ m/s}^3$) filtered out 42 steady-state braking tail updates where deceleration was tapering off, focusing 76 high-confidence APM updates on the initial brake onset transient ($1.76\text{ km/h}$ mean correction).
  - **New Active Benchmark:** **`218.93 m` @ 300s becomes the new active verified project benchmark**.

---

## M019 Control Reproduction Verification

- **Target Benchmark (M019 F4 Active Best):**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Measured F0 Control:**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Validation Causal Jerk Evaluation (`88566:107535`)

| Candidate ID | Jerk Threshold ($j_{\text{long}}$) | Val 300s Position Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F2 / F5** | **$j_{\text{long}} < -1.00\text{ m/s}^3$** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F3** | $j_{\text{long}} < -1.50\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Candidate |
| **F4** | $j_{\text{long}} < -2.00\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Candidate |
| **F1** | $j_{\text{long}} < -0.50\text{ m/s}^3$ | $496.35\text{ m}$ | $357.31\text{ m}$ | Candidate |
| **F0 Control** | No Jerk Gate (M019 Baseline) | $505.40\text{ m}$ | $359.28\text{ m}$ | Control Baseline |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | M019 Baseline Control | **7.33 km/h** | **11.54 km/h** | $27.53\text{ m}$ | $428.79\text{ m}$ | $220.12\text{ m}$ | $-16.3\%$ | $-13.4\%$ | CONTROL |
| **F1** | $j_{\text{long}} < -0.50\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.67\text{ m}$ | $-16.9\%$ | $-13.9\%$ | $-0.7\%$ |
| **F2** | $j_{\text{long}} < -1.00\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-13.8%** | **-0.5%** |
| **F3** | $j_{\text{long}} < -1.50\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-13.9\%$ | $-0.6\%$ |
| **F4** | $j_{\text{long}} < -2.00\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $27.32\text{ m}$ | $423.60\text{ m}$ | $215.41\text{ m}$ | $-18.1\%$ | $-15.2\%$ | $-2.1\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F2) | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-13.8%** | **-0.5%** |

---

## APM Activation & Jerk Suppression Diagnostics

| Candidate | Total IMU Decel Events | APM Updates | Suppressed Updates | Suppression Rate (%) | Mean APM Speed Correction |
|---|---|---|---|---|---|
| **F0 Control (No Gate)** | 118 | 118 | 0 | **0.0%** | $1.73\text{ km/h}$ |
| **F1 ($j_{\text{long}} < -0.50$)** | 118 | 80 | 38 | $32.2\%$ | $1.76\text{ km/h}$ |
| **F2 / F5 ($j_{\text{long}} < -1.00$)** | 118 | 76 | 42 | **35.6%** | $1.76\text{ km/h}$ |
| **F3 ($j_{\text{long}} < -1.50$)** | 118 | 69 | 49 | $41.5\%$ | $1.76\text{ km/h}$ |
| **F4 ($j_{\text{long}} < -2.00$)** | 118 | 67 | 51 | $43.2\%$ | $1.76\text{ km/h}$ |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M019)** | $308.28\text{ m}$ | $220.12\text{ m}$ | $-181.76\text{ m}$ | $124.23\text{ m}$ |
| **F5 (Val Winner F2)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |

- **Trajectory Error Progression across Outage:**
  - $t=60\text{ s}$: F0 = $27.53\text{ m}$ vs F5 = **$27.35\text{ m}$** ($-0.18\text{ m}$)
  - $t=120\text{ s}$: F0 = $428.79\text{ m}$ vs F5 = **$426.85\text{ m}$** ($-1.94\text{ m}$)
  - $t=180\text{ s}$: F0 = $334.12\text{ m}$ vs F5 = **$333.20\text{ m}$** ($-0.92\text{ m}$)
  - $t=240\text{ s}$: F0 = $289.45\text{ m}$ vs F5 = **$288.70\text{ m}$** ($-0.75\text{ m}$)
  - $t=300\text{ s}$: F0 = $220.12\text{ m}$ vs F5 = **$218.93\text{ m}$** ($-1.19\text{ m}$)
- **Audit Conclusion:** The improvement is **uniform and persistent across all time horizons**, disproving endpoint distance cancellation.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m028_imu_jerk_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m028_imu_jerk_apm.py)
- **Summary JSON:** `results/vw4_m028_imu_jerk_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m028_imu_jerk_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m028_imu_jerk_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m028_imu_jerk_apm_report.md)
- **Plot Directory:** `plots/vw4/m028_imu_jerk_apm/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M028 Verdict & New Active Benchmark

**ACCEPTED (F5 / F2 Candidate)**.

The NEW ACTIVE VERIFIED PROJECT BENCHMARK is:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
