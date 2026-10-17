# Milestone M034 — ZUPT Accelerometer Bias Observability & Correction Report

## Executive Summary

- **Milestone:** M034 — ZUPT Accelerometer Bias Observability & Correction
- **Objective:** Evaluate whether stationary ZUPT intervals ($P_{\text{stat}} > 0.70$) provide a stable, observable longitudinal acceleration bias estimate $b_a$ that improves subsequent inertial propagation and dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Stationary Residual Volatility:** Across 436 stationary ZUPT episodes on Train/Val, longitudinal acceleration residuals $a_{\text{long}}$ showed high inter-episode volatility ($\text{std} = 0.2504\text{ m/s}^2$, range = $1.2052\text{ m/s}^2$).
  - **Validation Selection:** F0 Control achieved the best validation score ($494.83\text{ m}$). All bias correction candidates F1–F3 ($\alpha \in [0.01, 0.10]$) degraded validation error ($495.67 - 497.79\text{ m}$). F0 Control was selected as the validation winner.
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), bias correction candidates F1–F3 severely degraded 300s position error to **`266.20 – 279.18 m`** (**+21.6% to +27.5% degradation** vs Control `218.93 m`) and degraded 120s error by $+16.4\text{ m}$ to $+22.3\text{ m}$.
  - **Physical Failure Mechanism:** Stationary $a_{\text{long}}$ residuals are dominated by vehicle chassis suspension pitch dynamics (pitch settling angle variations when stopping). Estimating $b_a$ during ZUPT captures vehicle pitch tilt rather than sensor bias, corrupting subsequent longitudinal motion integration.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 1 & 2 — Stationary ZUPT Bias Statistics (0:107,535)

- Total ZUPT Stationary Episodes Analyzed: 436 episodes
- Overall Stationary $a_{\text{long}}$ Mean Residual: $+0.1054\text{ m/s}^2$
- Overall Stationary $a_{\text{long}}$ Median Residual: $+0.0658\text{ m/s}^2$
- Overall Stationary $a_{\text{long}}$ Standard Deviation: $0.2573\text{ m/s}^2$
- Overall Stationary P95 Absolute Residual: $0.6081\text{ m/s}^2$
- Inter-Episode Mean Bias Standard Deviation: $0.2504\text{ m/s}^2$
- Inter-Episode Mean Bias Range: $1.2052\text{ m/s}^2$
- Consecutive Episode Bias Correlation: $r = +0.5726$

---

## Phase 4 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Update Rate ($\alpha$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | **No Bias Correction ($\alpha = 0.00$)** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $\alpha = 0.01$ | $495.67\text{ m}$ | $356.95\text{ m}$ | Degraded |
| **F2** | $\alpha = 0.05$ | $497.20\text{ m}$ | $357.67\text{ m}$ | Degraded |
| **F3** | $\alpha = 0.10$ | $497.79\text{ m}$ | $357.82\text{ m}$ | Degraded |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\alpha = 0.01$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.40\text{ m}$ | $443.26\text{ m}$ | **279.18 m** | $+6.1\%$ | $+26.8\%$ | **+27.5%** |
| **F2 ($\alpha = 0.05$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.80\text{ m}$ | $448.79\text{ m}$ | **271.24 m** | $+3.1\%$ | $+23.2\%$ | **+23.9%** |
| **F3 ($\alpha = 0.10$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.82\text{ m}$ | $449.14\text{ m}$ | **266.20 m** | $+1.2\%$ | $+20.9\%$ | **+21.6%** |
| **F4 (Val Winner F0)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **0.0%** |

---

## M016 Cross-Check & Failure Mechanism Analysis

1. **M016 Cross-Check:** Milestone M016 established that longitudinal accelerometer bias $b_a$ during outage is ill-posed and unobservable due to entanglement with tilt leakage. M034 confirms that ZUPT intervals do NOT solve this problem.
2. **Physical Failure Mechanism:** Vehicle chassis pitch dynamically changes every time the car stops (suspension pitch settling angle). Accelerometer residuals during ZUPT reflect vehicle pitch tilt rather than sensor bias. Applying this tilt offset as a persistent bias correction during driving corrupts forward velocity integration.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m034_zupt_accel_bias_observability.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m034_zupt_accel_bias_observability.py)
- **Summary JSON:** `results/vw4_m034_zupt_accel_bias_observability_summary.json`
- **Report Markdown:** [`results/vw4_m034_zupt_accel_bias_observability_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m034_zupt_accel_bias_observability_report.md)
- **Plot Directory:** `plots/vw4/m034_zupt_accel_bias_observability/`
  - `pos_error_vs_time.png`

---

## Final M034 Verdict & Active Benchmark

**REJECTED (BRANCH PERMANENTLY CLOSED)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
