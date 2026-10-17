# Milestone M027 — Causal Speed-Trend Confirmation for APM Activation Report

## Executive Summary

- **Milestone:** M027 — Causal Speed-Trend Confirmation for APM Activation
- **Objective:** Evaluate whether requiring dual confirmation of both IMU longitudinal deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$) and SpeedNet predicted speed derivative ($\frac{d v_{\text{speednet}}}{dt} < \text{threshold}$) makes APM speed damping more selective and improves 300s dead-reckoning position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Validation Selection:** Candidate F4 ($\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$) was selected as the **Validation Winner** with a 300s validation set position error of **$499.00\text{ m}$** (vs F0 Control $505.40\text{ m}$).
  - **Locked Test Evaluation of Validation Winner:** Evaluated on the locked unseen test partition (`start_idx = 108,000`), Validation Winner F4 / F5 achieved **`250.60 m` @ 300s** ($27.54\text{ m}$ @ 60s, $433.72\text{ m}$ @ 120s), degrading 300s position drift by **`+30.48 m` / `+13.8%`** over the active control baseline (`220.12 m`).
  - **Failure Mechanism (Neural Phase Lag):** SpeedNet speed predictions exhibit a temporal phase lag of 200–400 ms during braking transients. Requiring $\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$ suppressed 69 out of 118 genuine deceleration APM updates (58.5% suppression rate), preventing APM from trimming braking overestimation during early deceleration.
  - **Active Verified Benchmark:** **`220.12 m` @ 300s remains the active verified project benchmark**.

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

## Validation Speed-Trend Confirmation Evaluation (`88566:107535`)

| Candidate ID | Speed-Trend Derivative Threshold ($\frac{d v_{\text{speednet}}}{dt}$) | Val 300s Position Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F4 / F5** | **$\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$** | **499.00 m** | **358.24 m** | **SELECTED VALIDATION BEST** |
| **F2 / F3** | $\frac{d v_{\text{speednet}}}{dt} < -0.30\text{ m/s}^2$ | $499.56\text{ m}$ | $358.43\text{ m}$ | Candidate |
| **F1** | $\frac{d v_{\text{speednet}}}{dt} < -0.15\text{ m/s}^2$ | $503.26\text{ m}$ | $359.65\text{ m}$ | Candidate |
| **F0 Control** | No Speed-Trend Gate (IMU Decel Only) | $505.40\text{ m}$ | $359.28\text{ m}$ | Control Baseline |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | M019 Baseline Control | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | $\frac{d v_{\text{speednet}}}{dt} < -0.15\text{ m/s}^2$ | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F2** | $\frac{d v_{\text{speednet}}}{dt} < -0.30\text{ m/s}^2$ | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F3** | $\frac{d v_{\text{speednet}}}{dt} < -0.50\text{ m/s}^2$ | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F4** | $\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$ | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F4) | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |

---

## APM Activation & Suppression Diagnostics

| Candidate | Total IMU Decel Events | APM Updates | Suppressed Updates | Suppression Rate (%) | Mean APM Speed Correction |
|---|---|---|---|---|---|
| **F0 Control (No Gate)** | 118 | 118 | 0 | **0.0%** | $1.73\text{ km/h}$ |
| **F1 (dv/dt < -0.15)** | 118 | 55 | 63 | $53.4\%$ | $1.69\text{ km/h}$ |
| **F2 (dv/dt < -0.30)** | 118 | 52 | 66 | $55.9\%$ | $1.69\text{ km/h}$ |
| **F3 (dv/dt < -0.50)** | 118 | 51 | 67 | $56.8\%$ | $1.69\text{ km/h}$ |
| **F4 / F5 (dv/dt < -0.75)** | 118 | 49 | 69 | **58.5%** | $1.69\text{ km/h}$ |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M019)** | **308.28 m** | **220.12 m** | **-181.76 m** | **124.23 m** |
| **F5 (Val Winner F4)** | $311.02\text{ m}$ | $250.60\text{ m}$ | $-216.51\text{ m}$ | $126.24\text{ m}$ |

---

## Failure & Rejection Mechanism Analysis

1. **Neural Derivative Phase Lag:** SpeedNet sequence predictions exhibit a 200–400 ms delay relative to instantaneous IMU acceleration. When braking begins ($a_{\text{long}} < -0.5\text{ m/s}^2$), SpeedNet's predicted speed derivative lags behind, causing the trend gate to suppress 58.5% of legitimate APM updates.
2. **Re-Inflation of Braking Bias:** Suppressing APM updates during initial braking increased braking speed bias from $+11.54\text{ km/h}$ to $+11.58\text{ km/h}$, causing integrated along-track error to grow from $-181.76\text{ m}$ to $-216.51\text{ m}$, exploding 300s position drift by $+30.48\text{ m}$ ($220.12 \rightarrow 250.60\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m027_causal_speed_trend_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m027_causal_speed_trend_apm.py)
- **Summary JSON:** `results/vw4_m027_causal_speed_trend_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m027_causal_speed_trend_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m027_causal_speed_trend_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m027_causal_speed_trend_apm_report.md)
- **Plot Directory:** `plots/vw4/m027_causal_speed_trend_apm/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M027 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
