# Milestone M038 — Dynamic Physical Inference Constraint Tightening Report

## Executive Summary

- **Milestone:** M038 — Dynamic Physical Inference Constraint Tightening (Transient APM Acceleration Bounds)
- **Objective:** Evaluate whether expanding M019 APM correction bound to $\delta v_{\max} = 0.75\text{ m/s}$ dynamically during extreme causal longitudinal jerk transients ($j_{\text{long}} < j_{\text{thresh}}$) improves 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** F0 Control achieved the best validation score ($494.83\text{ m}$). All dynamic APM candidates F1–F4 degraded validation error ($496.41 - 496.81\text{ m}$). F0 Control was selected as the validation winner.
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), dynamic APM candidates F1–F4 degraded 300s position error to **`219.37 – 221.21 m`** ($+0.44\text{ m}$ to $+2.28\text{ m}$ degradation vs Control `218.93 m`).
  - **Physical Failure Mechanism:** Expanding the APM correction bound to $0.75\text{ m/s}$ during braking transients causes slight speed over-damping (negative speed integration bias), accumulating position drift over 300s horizons. Fixed bound $\delta v_{\max} = 0.50\text{ m/s}$ remains optimal.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 5 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Extreme Jerk Condition ($j_{\text{long}}$) | Dynamic Bound ($\delta v_{\max}$) | Extreme APM Events | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|---|---|
| **F0 (Control)** | **Fixed Bound (No Expansion)** | **0.50 m/s** | **0** | **494.83 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $j_{\text{long}} < -1.50\text{ m/s}^3$ | $0.75\text{ m/s}$ | 46 | $496.41\text{ m}$ | Degraded |
| **F2** | $j_{\text{long}} < -2.00\text{ m/s}^3$ | $0.75\text{ m/s}$ | 46 | $496.41\text{ m}$ | Degraded |
| **F3** | $j_{\text{long}} < -2.50\text{ m/s}^3$ | $0.75\text{ m/s}$ | 44 | $496.81\text{ m}$ | Degraded |
| **F4** | $j_{\text{long}} < -3.00\text{ m/s}^3$ | $0.75\text{ m/s}$ | 43 | $496.81\text{ m}$ | Degraded |

---

## Phase 6 — Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | Extreme APM Events | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **0** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($j < -1.50$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 42 | $27.34\text{ m}$ | $425.49\text{ m}$ | **221.21 m** | $-15.9\%$ | $+0.5\%$ | **+1.0%** |
| **F2 ($j < -2.00$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 40 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.46 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |
| **F3 ($j < -2.50$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 39 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.46 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |
| **F4 ($j < -3.00$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 39 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.37 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |

---

## Failure Mechanism Analysis & APM Bound Lock

1. **APM Bound Over-Damping:** Expanding APM correction magnitude to $\delta v_{\max} = 0.75\text{ m/s}$ during extreme braking transients over-damps forward speed updates, introducing slight negative integration bias that accumulates over long outage horizons ($219.37 - 221.21\text{ m}$ vs $218.93\text{ m}$).
2. **Correction Bound Lock:** Fixed bound $\delta v_{\max} = 0.50\text{ m/s}$ remains locked as the optimal physical APM correction bound.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m038_dynamic_apm_bound.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m038_dynamic_apm_bound.py)
- **Summary JSON:** `results/vw4_m038_dynamic_apm_bound_summary.json`
- **Report Markdown:** [`results/vw4_m038_dynamic_apm_bound_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m038_dynamic_apm_bound_report.md)
- **Plot Directory:** `plots/vw4/m038_dynamic_apm_bound/`
  - `pos_error_vs_time.png`

---

## Final M038 Verdict & Active Benchmark

**REJECTED (BRANCH PERMANENTLY CLOSED)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
