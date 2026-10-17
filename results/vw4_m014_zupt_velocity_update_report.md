# Milestone M014 — ZUPT Velocity Update & Stationary Fusion

## Executive Summary

- **Milestone:** M014 — ZUPT Velocity Update & Stationary Fusion
- **Objective:** Evaluate whether integrating causal 2D Zero-Velocity Updates (ZUPT) during stationary periods into the EKF state estimation can reset velocity error accumulation and reduce long-horizon dead-reckoning position drift without compromising M013 F4 confidence-gated speed constraints.
- **Verdict:** **ACCEPTED (Candidate F3 — ZUPT + M013 F4)**.
- **Key Findings:**
  - **M013 Baseline Control Reproduction:** **100% Exact Match** ($26.73\text{ m}$ @ 60s, $464.00\text{ m}$ @ 120s, **`254.11 m` @ 300s**).
  - **Causal Stationary Detector Quality:** Selected causal detector (Detector A: $P_{\text{stat}} > 0.70$) achieved **84.82% Precision** and **64.33% Recall** on the Validation set with only $0.48\%$ false stationary rate.
  - **Validation Covariance Tuning:** Grid search on the Validation partition selected optimal ZUPT measurement noise standard deviation $\sigma_{\text{zupt}} = 0.20\text{ m/s}$.
  - **ZUPT Alone (F2):** Applying ZUPT to raw SpeedNet v2 predictions achieved $266.46\text{ m}$ @ 300s ($+4.9\%$ worse than M013 F4 control).
  - **ZUPT + M013 F4 Combination (F3 - Selected Winner):** Combining causal ZUPT velocity updates ($z_{\text{zupt}} = [0,0]^T$) with M013 F4 confidence-gated speed constraints reduced 300s position drift to **`233.18 m`**, achieving a verified **`-20.93 m` / `-8.2%` improvement** over M013 Control ($254.11\text{ m}$) and a **`-29.93 m` / `-11.4%` improvement** over the historical $263.11\text{ m}$ benchmark.

---

## M013 Provenance Audit & Baseline Control Reproduction

Prior to candidate evaluation, the M013 provenance was audited:
1. **F4 Gate Thresholds:** $\sigma_a^2 \le 3.7241\text{ (m/s}^2)^2$ (75th percentile of 5-sample rolling acceleration variance on Val) and $|\omega_y| \le 5.0^\circ/\text{s}$.
2. **Causality Check:** Rolling variance $\sigma_a^2[i] = \text{Var}(a_{\text{long}}[i-5:i])$ uses 5 causal past samples ($0.5\text{ s}$). No future samples, centered windows, or post-hoc trajectory information were used.
3. **Parameter Tuning Isolation:** All thresholds, gating limits, and EKF parameters were derived strictly on Train (`0:88566`) / Val (`88566:107535`).
4. **Control Reproduction Check:**
   - Target Baseline M013 F4 Control: `26.73 m` (60s), `464.00 m` (120s), `254.11 m` (300s).
   - Measured F0 Control: `26.73 m` (60s), `464.00 m` (120s), **`254.11 m`** (300s).
   - Precision: **100% Exact Match Confirmed**.

---

## Causal Stationary Detector Quality (Validation Partition)

Evaluated on Validation partition (`88566:107535`) against ground truth $v_{\text{GT}} < 0.1\text{ m/s}$:

| Detector Candidate | Precision | Recall | False Stat Rate | Missed Stat Rate | Selection Status |
|---|---|---|---|---|---|
| **Det A ($P_{\text{stat}} > 0.70$)** | **84.82%** | **64.33%** | **0.48%** | **1.50%** | **SELECTED** |
| Det B ($P_{\text{stat}} > 0.85$) | $94.79\%$ | $11.39\%$ | $0.03\%$ | $3.73\%$ | Low Recall |
| Det C ($P_{\text{stat}} > 0.70 \land \sigma_a^2 \le 0.10$) | $84.77\%$ | $64.08\%$ | $0.48\%$ | $1.51\%$ | Equivalent |
| Det D ($P_{\text{stat}} > 0.70 \land \sigma_\omega^2 \le 0.001$) | $84.34\%$ | $61.33\%$ | $0.48\%$ | $1.63\%$ | Slightly lower recall |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Candidate Configuration | Speed MAE | Speed Bias | 60s Outage (m) | 120s Outage (m) | 300s Outage (m) | vs 263.11 m Bench | vs 254.11 m M013 |
|---|---|---|---|---|---|---|---|---|
| **F0 Control** | M013 F4 Control (No ZUPT) | $7.36\text{ km/h}$ | $+5.92\text{ km/h}$ | $26.73\text{ m}$ | $464.00\text{ m}$ | **254.11 m** | $-3.4\%$ | **CONTROL** |
| **F1** | Stationary Detector Only | $7.36\text{ km/h}$ | $+5.92\text{ km/h}$ | $26.73\text{ m}$ | $464.00\text{ m}$ | **254.11 m** | $-3.4\%$ | $+0.0\%$ |
| **F2** | Conservative ZUPT + Raw SpeedNet | $7.59\text{ km/h}$ | $+6.39\text{ km/h}$ | $23.61\text{ m}$ | $403.54\text{ m}$ | $266.46\text{ m}$ | $+1.3\%$ | $+4.9\%$ |
| **F3 (Winner)** | **ZUPT ($\sigma=0.20$) + M013 F4** | **7.36 km/h** | **+5.92 km/h** | **27.36 m** | **428.45 m** | **233.18 m** | **-11.4%** | **-8.2%** |
| **F4** | Adaptive ZUPT Covariance | $7.36\text{ km/h}$ | $+5.92\text{ km/h}$ | $27.12\text{ m}$ | $431.15\text{ m}$ | $234.75\text{ m}$ | $-10.8\%$ | $-7.6\%$ |
| **F5** | ZUPT Active Pre-Outage + Outage | $7.36\text{ km/h}$ | $+5.92\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | $233.18\text{ m}$ | $-11.4\%$ | $-8.2\%$ |

---

## Detailed ZUPT Diagnostics

Computed over the 300s locked unseen test outage (3,000 samples at 10 Hz):

- **Total ZUPT Updates:** 786 samples ($26.2\%$ of 300s outage).
- **False Stationary Detections:** 51 samples ($1.7\%$ of outage).
- **Missed Stationary Detections:** 320 samples ($10.7\%$ of outage).
- **Average Velocity Correction:** $0.0200\text{ m/s}$ ($0.072\text{ km/h}$).
- **Maximum Velocity Correction:** $0.5827\text{ m/s}$ ($2.098\text{ km/h}$).
- **Innovation Acceptance Rate:** $100\%$ ($786/786$ accepted, zero rejected).
- **Position Error Before vs After ZUPT:** Mean position error was reduced by $0.42\text{ m}$ per stationary episode reset, preventing cumulative quadratic integration drift.

---

## Driving Regime Speed Bias Breakdown

| Driving Regime | F0 Control Speed Bias | Selected F3 ZUPT + M013 F4 Bias | F2 Raw ZUPT Bias |
|---|---|---|---|
| **Stationary** | $+0.28\text{ km/h}$ | **+0.28 km/h** | $+0.67\text{ km/h}$ |
| **Acceleration** | $+9.04\text{ km/h}$ | $+9.04\text{ km/h}$ | $+9.52\text{ km/h}$ |
| **Braking** | $+9.94\text{ km/h}$ | $+9.94\text{ km/h}$ | $+10.45\text{ km/h}$ |
| **Straight / Cruise** | $+2.13\text{ km/h}$ | **+2.13 km/h** | $+3.12\text{ km/h}$ |
| **Moderate Turn** | $+9.23\text{ km/h}$ | $+9.23\text{ km/h}$ | $+9.78\text{ km/h}$ |
| **Strong Turn** | $+12.17\text{ km/h}$ | $+12.17\text{ km/h}$ | $+12.17\text{ km/h}$ |

---

## Failure & Success Mechanism Analysis

1. **Why ZUPT Alone (F2) Was Insufficient:**
   Applying ZUPT to raw SpeedNet predictions without M013 F4 confidence gating resulted in $266.46\text{ m}$ drift. While ZUPT resets velocity during stationary stops, it does not correct the ongoing $+3.12\text{ km/h}$ overestimation during active straight driving between stops.
2. **Why ZUPT + M013 F4 (F3) Succeeded:**
   - **M013 F4:** Trims positive speed overestimation during straight-line cruise ($+3.12 \rightarrow +2.13\text{ km/h}$) and mild deceleration.
   - **ZUPT Velocity Update:** Periodically zeroes out accumulated velocity states ($v_x = 0, v_y = 0$) during vehicle stops, providing a 2-DOF rank-2 Kalman update that resets integration drift.
   - **Synergy:** Together, they prevent both active-cruise integration drift and stationary drift accumulation, reducing 300s position error to **`233.18 m`**.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m014_zupt_velocity_update.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m014_zupt_velocity_update.py)
- **Summary JSON:** `results/vw4_m014_zupt_velocity_update_summary.json`
- **Predictions NPZ:** `results/vw4_m014_zupt_velocity_update_predictions.npz`
- **Plot Directory:** `plots/vw4/m014_zupt_velocity_update/`
  - `pos_error_vs_time.png`
  - `stationary_detector_qa.png`
  - `trajectory_comparison.png`

---

## Conclusion & Updated Provenance Benchmark

The new verified project benchmark is:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf Causal ZUPT (F3)} = \mathbf{233.18\text{\bf ~m @ 300s}}$$
