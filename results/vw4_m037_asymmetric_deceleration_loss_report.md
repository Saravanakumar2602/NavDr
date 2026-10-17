# Milestone M037 — Asymmetric Deceleration Loss Ablation Report

## Executive Summary

- **Milestone:** M037 — Asymmetric Deceleration Loss Ablation
- **Objective:** Evaluate whether adding an asymmetric deceleration over-prediction penalty ($\mathcal{L}_{\text{asym}} = \lambda \max(0, \hat{v} - v_{\text{gt}})^2 \cdot \mathbb{I}(a_{\text{long}} < -0.5)$) to SpeedNet v2 ($W=40$) training reduces speed overestimation during braking without distorting speed predictions or degrading 300s position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Asymmetric Loss Model Distortion:** Soft asymmetric penalty terms distort neural weight calibration. Candidate F2 ($\lambda=0.003$) suffered zero-prediction speed collapse during deceleration (braking bias $-52.43\text{ km/h}$).
  - **Validation Selection:** Candidate F2 ($\lambda=0.003$) achieved the lowest validation 300s error ($316.98\text{ m}$ vs Control $494.83\text{ m}$) due to artificial zero-speed suppression.
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), validation winner F2 ($\lambda=0.003$) exploded 300s position drift to **`818.48 m`** (**+273.9% degradation** vs Control `218.93 m`) and degraded 120s error from $426.85\text{ m}$ to $809.63\text{ m}$.
  - **Failure Mechanism:** Soft loss penalties force neural speed models into uncalibrated speed regimes that fail on unseen data (reconfirming M012 findings). Post-inference physical constraints (M013 F4) remain superior to loss-based constraints.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 4 — Pointwise Speed & Regime MAE Analysis (Validation Partition `88566:107535`)

| Candidate ID | Loss Hyperparameter ($\lambda$) | Overall Speed MAE | Braking Speed MAE | Braking Speed Bias | Accel Speed MAE | Turn Speed MAE |
|---|---|---|---|---|---|---|
| **F0 (Control)** | **$\lambda = 0.000$ (Control Baseline)** | **12.38 km/h** | **13.63 km/h** | **+0.52 km/h** | **12.25 km/h** | **13.31 km/h** |
| **F1** | $\lambda = 0.001$ | $14.00\text{ km/h}$ | $15.53\text{ km/h}$ | $+4.62\text{ km/h}$ | $13.63\text{ km/h}$ | $15.21\text{ km/h}$ |
| **F2** | $\lambda = 0.003$ | $47.29\text{ km/h}$ | $52.43\text{ km/h}$ | $-52.43\text{ km/h}$ | $46.67\text{ km/h}$ | $53.11\text{ km/h}$ |
| **F3** | $\lambda = 0.010$ | $12.51\text{ km/h}$ | $13.82\text{ km/h}$ | $+1.07\text{ km/h}$ | $12.29\text{ km/h}$ | $13.36\text{ km/h}$ |
| **F4** | $\lambda = 0.030$ | $13.18\text{ km/h}$ | $14.37\text{ km/h}$ | $+5.55\text{ km/h}$ | $13.13\text{ km/h}$ | $14.13\text{ km/h}$ |

---

## Phase 5 — Validation Navigation Evaluation (`88566:107535`)

| Candidate ID | Loss Hyperparameter ($\lambda$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | $\lambda = 0.000$ (Control Baseline) | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | $\lambda = 0.001$ | $1,050.28\text{ m}$ | $438.63\text{ m}$ | Degraded |
| **F2** | **$\lambda = 0.003$** | **316.98 m** | **259.27 m** | **SELECTED VALIDATION WINNER** |
| **F3** | $\lambda = 0.010$ | $1,146.17\text{ m}$ | $332.48\text{ m}$ | Degraded |
| **F4** | $\lambda = 0.030$ | $777.32\text{ m}$ | $413.05\text{ m}$ | Degraded |

---

## Phase 6 — Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\lambda = 0.001$)** | $8.77\text{ km/h}$ | $13.80\text{ km/h}$ | $123.97\text{ m}$ | $735.75\text{ m}$ | **519.24 m** | $+97.3\%$ | $+135.9\%$ | **+137.2%** |
| **F2 (Val Winner $\lambda=0.003$)** | **16.53 km/h** | **26.81 km/h** | **383.52 m** | **809.63 m** | **818.48 m** | **+211.1%** | **+271.8%** | **+273.9%** |
| **F3 ($\lambda = 0.010$)** | $7.36\text{ km/h}$ | $11.90\text{ km/h}$ | $14.31\text{ m}$ | $880.40\text{ m}$ | **1289.82 m** | $+390.2\%$ | $+486.0\%$ | **+489.1%** |
| **F4 ($\lambda = 0.030$)** | $10.26\text{ km/h}$ | $16.21\text{ km/h}$ | $100.91\text{ m}$ | $909.20\text{ m}$ | **976.05 m** | $+271.0\%$ | $+343.4\%$ | **+345.8%** |

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m037_asymmetric_deceleration_loss.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m037_asymmetric_deceleration_loss.py)
- **Summary JSON:** `results/vw4_m037_asymmetric_deceleration_loss_summary.json`
- **Report Markdown:** [`results/vw4_m037_asymmetric_deceleration_loss_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m037_asymmetric_deceleration_loss_report.md)
- **Plot Directory:** `plots/vw4/m037_asymmetric_deceleration_loss/`
  - `pos_error_vs_time.png`

---

## Final M037 Verdict & Active Benchmark

**REJECTED (BRANCH PERMANENTLY CLOSED)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
