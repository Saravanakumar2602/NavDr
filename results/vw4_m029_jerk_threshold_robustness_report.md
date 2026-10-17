# Milestone M029 — Jerk-Gate Robustness and Local Threshold Ablation Report

## Executive Summary

- **Milestone:** M029 — Jerk-Gate Robustness and Local Threshold Ablation
- **Objective:** Perform a fine-grained local threshold ablation around the M028 selected causal jerk gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) across candidate thresholds $[-1.25, -0.75]\text{ m/s}^3$ to determine whether M028 represents a smooth, physically robust operating plateau or a brittle local optimum.
- **Verdict:** **ROBUSTNESS CONFIRMED (ROBUST OPERATING PLATEAU VERIFIED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Local Neighborhood Flatness:** Across the entire local threshold neighborhood $[-1.25, -0.90]\text{ m/s}^3$, validation 300s position error remains **flat at $494.83\text{ m}$** (mean position error = $356.99\text{ m}$).
  - **Locked Test Robustness:** Test 300s position error across $[-1.00, -0.75]\text{ m/s}^3$ is **exactly `218.93 m`**, and varies by less than 6 cm across $[-1.25, -1.10]\text{ m/s}^3$ ($218.87\text{ m}$).
  - **No Spurious Benchmark Invention:** Because nearby local thresholds are practically and statistically indistinguishable ($\Delta < 0.03\%$), M029 confirms threshold robustness without inventing an unneeded sub-centimeter benchmark change.
  - **Active Verified Benchmark Retained:** **`218.93 m` @ 300s is retained as the active project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 F2 Active Best):**
  - 60s Outage: `27.35 m`
  - 120s Outage: `426.85 m`
  - 300s Outage: `218.93 m`
- **Measured F0 Control:**
  - 60s Outage: `27.35 m`
  - 120s Outage: `426.85 m`
  - 300s Outage: `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Validation Local Jerk Threshold Evaluation (`88566:107535`)

| Candidate ID | Local Jerk Threshold ($j_{\text{long}}$) | Val 300s Position Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F2 / F5** | **$j_{\text{long}} < -0.90\text{ m/s}^3$** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION BEST** |
| **F0 Control** | $j_{\text{long}} < -1.00\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Baseline |
| **F3** | $j_{\text{long}} < -1.10\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Candidate |
| **F4** | $j_{\text{long}} < -1.25\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Candidate |
| **F1** | $j_{\text{long}} < -0.75\text{ m/s}^3$ | $495.52\text{ m}$ | $357.13\text{ m}$ | Robust Candidate |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control -1.00)** | M028 Baseline Control | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1** | $j_{\text{long}} < -0.75\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F2 (Val Winner)** | $j_{\text{long}} < -0.90\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **+0.0%** |
| **F3** | $j_{\text{long}} < -1.10\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-0.6\%$ | $-0.0\%$ |
| **F4** | $j_{\text{long}} < -1.25\text{ m/s}^3$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-0.6\%$ | $-0.0\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F2) | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **+0.0%** |

---

## APM Activation & Local Threshold Sensitivity Diagnostics

| Candidate | Total IMU Decel Events | APM Updates | Suppressed Updates | Suppression Rate (%) | Mean APM Speed Correction |
|---|---|---|---|---|---|
| **F1 ($j_{\text{long}} < -0.75$)** | 118 | 78 | 40 | $33.9\%$ | $1.76\text{ km/h}$ |
| **F2 / F5 ($j_{\text{long}} < -0.90$)** | 118 | 77 | 41 | $34.7\%$ | $1.76\text{ km/h}$ |
| **F0 Control ($j_{\text{long}} < -1.00$)** | 118 | 76 | 42 | **35.6%** | $1.76\text{ km/h}$ |
| **F3 ($j_{\text{long}} < -1.10$)** | 118 | 73 | 45 | $38.1\%$ | $1.76\text{ km/h}$ |
| **F4 ($j_{\text{long}} < -1.25$)** | 118 | 71 | 47 | $39.8\%$ | $1.76\text{ km/h}$ |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M028 -1.00)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |
| **F2 / F5 (Val Winner -0.90)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |
| **F4 (Candidate -1.25)** | $307.69\text{ m}$ | $218.87\text{ m}$ | $-180.19\text{ m}$ | $124.15\text{ m}$ |

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m029_jerk_threshold_robustness.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m029_jerk_threshold_robustness.py)
- **Summary JSON:** `results/vw4_m029_jerk_threshold_robustness_summary.json`
- **Predictions NPZ:** `results/vw4_m029_jerk_threshold_robustness_predictions.npz`
- **Report Markdown:** [`results/vw4_m029_jerk_threshold_robustness_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m029_jerk_threshold_robustness_report.md)
- **Plot Directory:** `plots/vw4/m029_jerk_threshold_robustness/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M029 Verdict & Retained Active Benchmark

**ROBUSTNESS CONFIRMED**.

The ACTIVE VERIFIED PROJECT BENCHMARK is retained:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
