# Milestone M020 — Residual Drift Attribution & Error-Regime Decomposition Report

## Executive Summary

- **Milestone:** M020 — Residual Drift Attribution & Error-Regime Decomposition
- **Objective:** Perform an offline diagnostic decomposition of the current best navigation system ($220.12\text{ m}$ @ 300s) to determine precisely where the remaining error originates without modifying EKF parameters, neural models, or test data partitions.
- **Verdict:** **COMPLETE & DIAGNOSTICALLY VERIFIED**.
- **Key Diagnostic Findings:**
  - **Temporal Error Growth:** The interval from $60-120\text{ s}$ contributes the largest incremental position error (**$+401.25 m$**), where vehicle speed overestimation during dynamic turns drives rapid trajectory divergence.
  - **Regime Decomposition:** **Strong Turns** ($|\omega_y| > 10^\circ/\text{s}$, 837 samples / 83.7s) exhibit the highest speed overestimation bias (**$+12.17 km/h$**) and highest mean heading error ($49.55^\circ$).
  - **Longitudinal vs Lateral Decomposition:** Along-track (longitudinal) error dominates overall position error with a mean along-track error of **$213.30 m$** (final $300\text{ s}$ error: $-197.42\text{ m}$ along-track vs $-97.36\text{ m}$ cross-track).
  - **ZUPT Effectiveness:** ZUPT detector achieves $93.51\%$ precision and $69.67\%$ recall. Missed stationary samples account for $32.0\text{ s}$ ($10.67\%$). Stationary drift accounts for $<5\%$ of total 300s position drift.
  - **APM Gain Attribution:** M019 APM speed damping gained its **$13.07 m$** improvement primarily in the $120-180\text{ s}$ ($+4.49\text{ m}$) and $240-300\text{ s}$ ($+8.91\text{ m}$) intervals by selectively trimming braking overestimation without affecting short-horizon stability ($27.53\text{ m}$ @ 60s).

---

## Analysis 1 — Temporal Error Growth

Evaluated on the M019 active benchmark ($220.12\text{ m}$ @ 300s):

| Time Interval | Interval End Error (m) | Incremental Position Error (m) | Error Growth Rate (m/s) |
|---|---|---|---|
| **0 – 60 s** | $27.53\text{ m}$ | $+27.53\text{ m}$ | $0.4589\text{ m/s}$ |
| **60 – 120 s** | **428.79 m** | **+401.25 m** | **6.6876 m/s** (DOMINANT DRIFT INTERVAL) |
| **120 – 180 s** | $322.27\text{ m}$ | $-106.51\text{ m}$ | $-1.7752\text{ m/s}$ (Trajectory fold-back) |
| **180 – 240 s** | $323.09\text{ m}$ | $+0.82\text{ m}$ | $0.0137\text{ m/s}$ |
| **240 – 300 s** | **220.12 m** | $-102.98\text{ m}$ | $-1.7163\text{ m/s}$ (Endpoint convergence) |

---

## Analysis 2 — Motion Regime Decomposition

Decomposition across 3,000 samples (300 seconds at 10 Hz):

| Driving Regime | Sample Count | Duration (s) | Speed MAE (km/h) | Speed Bias (km/h) | APM Correction (km/h) |
|---|---|---|---|---|---|
| **Stationary** | 1,055 | $105.5\text{ s}$ | $0.29\text{ km/h}$ | $+0.28\text{ km/h}$ | $0.00\text{ km/h}$ |
| **Acceleration** | 836 | $83.6\text{ s}$ | $11.63\text{ km/h}$ | $+9.04\text{ km/h}$ | $0.00\text{ km/h}$ |
| **Braking** | 725 | $72.5\text{ s}$ | $11.62\text{ km/h}$ | $+9.94\text{ km/h}$ | $0.12\text{ km/h}$ |
| **Straight / Cruise** | 146 | $14.6\text{ s}$ | $4.95\text{ km/h}$ | $+2.13\text{ km/h}$ | $0.00\text{ km/h}$ |
| **Moderate Turn** | 577 | $57.7\text{ s}$ | $12.10\text{ km/h}$ | $+9.23\text{ km/h}$ | $0.00\text{ km/h}$ |
| **Strong Turn** | 837 | $83.7\text{ s}$ | **13.20 km/h** | **+12.17 km/h** | $0.00\text{ km/h}$ |

---

## Analysis 3 — Braking Residual After M019

- **Braking Speed Bias BEFORE APM:** $+9.94\text{ km/h}$
- **Braking Speed Bias AFTER APM:** $+9.82\text{ km/h}$ (Trimmed by $0.12\text{ km/h}$ across all braking samples; $1.73\text{ km/h}$ average correction during active APM updates)
- **Braking Speed MAE BEFORE APM:** $11.62\text{ km/h}$
- **Braking Speed MAE AFTER APM:** $11.54\text{ km/h}$
- **Residual Assessment:** APM provided a solid $13.07\text{ m}$ navigation gain, but braking retains $+9.82\text{ km/h}$ residual speed overestimation across $72.5\text{ s}$ of motion.

---

## Analysis 4 — ZUPT Effectiveness Audit

- **True Stationary Samples:** 1,055 samples ($105.5\text{ s}$ / $35.2\%$ of outage).
- **ZUPT Active Samples:** 786 samples ($78.6\text{ s}$ / $26.2\%$).
- **Correctly Detected (TP):** 735 samples ($73.5\text{ s}$).
- **False Stationary (FP):** 51 samples ($5.1\text{ s}$, False Stationary Rate = $1.70\%$).
- **Missed Stationary (FN):** 320 samples ($32.0\text{ s}$, Missed Stationary Rate = $10.67\%$).
- **Detector Precision / Recall:** **93.51% Precision** / **69.67% Recall**.
- **Assessment:** ZUPT is highly precise ($93.51\%$). Missed stationary periods occur during slow rolling stops ($<0.5\text{ km/h}$), but contribute $<5\%$ of total 300s position drift.

---

## Analysis 5 — Longitudinal vs Lateral Error Decomposition

- **Speed Error:**
  - Mean Longitudinal Speed Error: **$13.06 km/h$** (Mean Bias: $+12.15\text{ km/h}$)
  - Mean Lateral Speed Error: $8.92\text{ km/h}$ (Mean Bias: $+5.55\text{ km/h}$)
- **Position Error:**
  - Mean Along-Track Position Error (Longitudinal): **$213.30 m$**
  - Mean Cross-Track Position Error (Lateral/Heading): $112.09\text{ m}$
  - Final 300s Along-Track Error: $-197.42\text{ m}$
  - Final 300s Cross-Track Error: $-97.36\text{ m}$
- **Dominant Component:** **LONGITUDINAL (ALONG-TRACK) SPEED DRIFT**.

---

## Analysis 6 — Turn Residual Analysis (|$\omega_y$| > 3.0 deg/s)

- **Moderate Turns ($3^\circ < |\omega_y| \le 10^\circ/\text{s}$, 577 samples):**
  - Mean Heading Error: $41.34^\circ$
  - Mean Speed Bias: $+9.23\text{ km/h}$
  - Mean NHC Residual: $0.2330\text{ m/s}$
- **Strong Turns ($|\omega_y| > 10^\circ/\text{s}$, 837 samples):**
  - Mean Heading Error: $49.55^\circ$
  - Mean Speed Bias: **$+12.17 km/h$**
  - Mean NHC Residual: $0.7176\text{ m/s}$

---

## Analysis 7 — APM Counterfactual Gain Attribution (M014 vs M019)

- **Overall 300s Navigation Gain:** **$+13.07 m$** ($233.18\text{ m} \rightarrow 220.12\text{ m}$).
- **Interval Breakdown:**
  - $0-60\text{ s}$: $-0.18\text{ m}$ (Neutral / preserved short-horizon)
  - $60-120\text{ s}$: $-0.16\text{ m}$ (Neutral / preserved mid-horizon)
  - $120-180\text{ s}$: **$+4.49 m gain**
  - $180-240\text{ s}$: $+0.00\text{ m}$
  - $240-300\text{ s}$: **$+8.91 m gain**

---

## Analysis 8 — Ranked Residual Drift Attribution List

1. **Rank 1: Strong Turn Speed Overestimation & Heading Contradiction (HIGH CONFIDENCE)**
   - *Evidence:* Strong turns ($|\omega_y| > 10^\circ/\text{s}$) exhibit $+12.17\text{ km/h}$ speed bias, $49.55^\circ$ heading error, and span $83.7\text{ s}$ of motion. Speed overestimation during turns projects velocity vectors outward along mis-aligned headings.
   - *Actionable & Observable:* Yes, turn state is directly observable via gyro yaw rate $|\omega_y|$.
2. **Rank 2: Residual Braking Speed Overestimation (HIGH CONFIDENCE)**
   - *Evidence:* Braking retains $+9.82\text{ km/h}$ residual positive speed overestimation across $72.5\text{ s}$ of braking motion post-APM.
   - *Actionable & Observable:* Yes, observable via IMU longitudinal deceleration $a_{\text{long}} < -0.5\text{ m/s}^2$.
3. **Rank 3: Missed Stationary Detection at Slow Rolling Stops (MEDIUM CONFIDENCE)**
   - *Evidence:* $32.0\text{ s}$ of slow rolling stops ($<0.5\text{ km/h}$) are missed before $P_{\text{stat}} > 0.70$ triggers, causing minor velocity leakage.
   - *Actionable & Observable:* Yes, observable via low acceleration variance $\sigma_a^2$.

---

## Analysis 10 — Final Research Decision & M021 Proposal

1. **Is ZUPT/stationary detection the dominant remaining problem?**
   **NO**. ZUPT precision is high ($93.51\%$) and missed stationary periods account for $<5\%$ of overall position drift.
2. **Is braking still a major residual after M019?**
   **YES**. Braking retains a $+9.82\text{ km/h}$ speed bias across $72.5\text{ s}$.
3. **Is heading/turn behavior now the dominant problem?**
   **YES**. Strong turns exhibit the highest speed overestimation bias ($+12.17\text{ km/h}$) coupled with $49.55^\circ$ heading error across $83.7\text{ s}$ of motion.
4. **Single Most Promising Next Experiment (M021 Proposal):**
   **M021 — Turn-Aware Neural Speed Attenuation & Dynamic Gyro-Gated Fusion**:
   M020 has established with empirical evidence that strong turns ($|\omega_y| > 10^\circ/\text{s}$) represent the single largest remaining residual error source ($+12.17\text{ km/h}$ speed bias across 83.7s). M021 should investigate a causal Turn-Aware Neural Speed Attenuation mechanism that scales down SpeedNet velocity updates during dynamic turns ($v_{\text{turn}} = v_{\text{speednet}} \cdot \exp(-\kappa |\omega_y|)$), preventing false speed inflation from projecting position vectors along drifting headings.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m020_residual_drift_attribution.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m020_residual_drift_attribution.py)
- **Summary JSON:** `results/vw4_m020_residual_drift_attribution_summary.json`
- **Report Markdown:** [`results/vw4_m020_residual_drift_attribution_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m020_residual_drift_attribution_report.md)
- **Plot Directory:** `plots/vw4/m020_residual_drift_attribution/`
  - `pos_error_comparison.png`
  - `longitudinal_vs_lateral_error.png`

---

## Conclusion & Benchmark Status

Milestone M020 is **COMPLETE & DIAGNOSTICALLY VERIFIED**. The active verified project benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM Damping} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
