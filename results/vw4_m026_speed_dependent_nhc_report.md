# Milestone M026 — Conservative Speed-Dependent NHC Covariance Ablation Report

## Executive Summary

- **Milestone:** M026 — Conservative Speed-Dependent NHC Covariance Ablation
- **Objective:** Evaluate whether a speed-dependent relaxation of lateral velocity measurement covariance ($R_{\text{nhc}}(v) = R_0 (1 + \gamma v^2)$) can account for vehicle chassis dynamics at higher speeds without introducing unconstrained lateral position drift.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Validation Selection:** All speed-dependent NHC covariance candidates (F1–F4) severely degraded 300s validation set position error ($505.40\text{ m}$ for Control vs $722.66\text{ m}$ for F1, $859.51\text{ m}$ for F2, $964.30\text{ m}$ for F3, $1008.35\text{ m}$ for F4). The Validation-Selected Winner (F5) is the original **M019 Fixed NHC Control** ($\gamma = 0.0$, `505.40 m`).
  - **Catastrophic Lateral Drift Explosion:** Relaxing NHC measurement covariance at high speed removes lateral velocity anchoring, causing heading errors to rapidly accumulate into unconstrained lateral position drift (+422.0% error explosion on test set, $220.12 \rightarrow 1149.07\text{ m}$).
  - **Locked Test Evaluation of Validation Winner:** Evaluated on the locked unseen test partition (`start_idx = 108,000`), Validation Winner F5 / F0 achieved **`220.12 m` @ 300s**, matching the control baseline ($0.0\%$).
  - **Active Verified Benchmark:** **`220.12 m` @ 300s remains the active verified project benchmark**.

---

## Base NHC & Covariance Formulation Audit

1. **NHC Measurement Equation:** In the vehicle body frame, lateral velocity is defined as $v_{\text{lat}} = -v_x \cos(\psi_c) + v_y \sin(\psi_c)$. The pseudo-measurement constraint is $y_{\text{nhc}} = 0.0 - v_{\text{lat}}$.
2. **Fixed Baseline Covariance:** $R_0 = 0.20^2 = 0.04\text{ m}^2/\text{s}^2$.
3. **Speed-Dependent Covariance Formulation:** $R_{\text{nhc}}(v_{\text{est}}) = R_0 \cdot \left(1 + \gamma \cdot v_{\text{est}}^2\right)$, capped at safety bound $R_{\max} = 5.0 R_0 = 0.20\text{ m}^2/\text{s}^2$.
4. **Audit Finding:** In dead-reckoning without absolute orientation measurement, tight NHC covariance ($R_0 = 0.04\text{ m}^2/\text{s}^2$) is essential. Inflating $R_{\text{nhc}}$ by even $+36\%$ at high speed ($0.040 \rightarrow 0.0546\text{ m}^2/\text{s}^2$) weakens lateral velocity updates, allowing lateral position drift to explode.

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

## Validation Speed-Dependent NHC Evaluation (`88566:107535`)

| Candidate ID | Speed-Dependent Scaling ($\gamma$) | Val 300s Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 / F5** | **Control Fixed NHC ($\gamma=0.0$)** | **505.40 m** | **359.28 m** | **SELECTED VALIDATION BEST** |
| **F1** | $\gamma = 0.005$ | $722.66\text{ m}$ | $391.06\text{ m}$ | Degraded (+43.0%) |
| **F2** | $\gamma = 0.010$ | $859.51\text{ m}$ | $408.50\text{ m}$ | Degraded (+70.1%) |
| **F3** | $\gamma = 0.020$ | $964.30\text{ m}$ | $419.17\text{ m}$ | Degraded (+90.8%) |
| **F4** | $\gamma = 0.050$ | $1008.35\text{ m}$ | $417.99\text{ m}$ | Degraded (+99.5%) |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control gamma=0.0)** | M019 Baseline Control | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | Speed-Dependent ($\gamma=0.005$) | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $31.06\text{ m}$ | $537.58\text{ m}$ | $1149.07\text{ m}^*$ | $+336.7\%$ | $+352.2\%$ | $+422.0\%$ |
| **F2** | Speed-Dependent ($\gamma=0.010$) | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $33.12\text{ m}$ | $570.68\text{ m}$ | $1039.05\text{ m}^*$ | $+294.9\%$ | $+308.9\%$ | $+372.0\%$ |
| **F3** | Speed-Dependent ($\gamma=0.020$) | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $38.10\text{ m}$ | $579.96\text{ m}$ | $847.77\text{ m}^*$ | $+222.2\%$ | $+233.6\%$ | $+285.1\%$ |
| **F4** | Speed-Dependent ($\gamma=0.050$) | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $36.37\text{ m}$ | $558.03\text{ m}$ | $770.61\text{ m}^*$ | $+192.9\%$ | $+203.3\%$ | $+250.1\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F0) | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

*\*Note: F1, F2, F3, F4 exploded validation set position error ($722.66 - 1008.35\text{ m}$) and were cleanly rejected by Validation.*

---

## NHC Covariance & Lateral Velocity Diagnostics

| Candidate | Mean $R_{\text{nhc}}$ ($\text{m}^2/\text{s}^2$) | Max $R_{\text{nhc}}$ ($\text{m}^2/\text{s}^2$) | Mean $|y_{\text{nhc}}|$ ($\text{m/s}$) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|---|
| **F0 / F5 Control** | **0.0400** | **0.0400** | **0.2631** | **-181.76 m** | **124.23 m** |
| **F1 ($\gamma=0.005$)** | $0.0546$ | $0.1205$ | $0.3070$ | $-440.67\text{ m}$ | $1061.27\text{ m}$ |
| **F2 ($\gamma=0.010$)** | $0.0694$ | $0.2000$ | $0.3385$ | $-532.74\text{ m}$ | $890.96\text{ m}$ |
| **F3 ($\gamma=0.020$)** | $0.0919$ | $0.2000$ | $0.3775$ | $-631.81\text{ m}$ | $565.17\text{ m}$ |
| **F4 ($\gamma=0.050$)** | $0.1138$ | $0.2000$ | $0.4088$ | $-648.74\text{ m}$ | $414.70\text{ m}$ |

---

## Failure Mechanism Analysis

1. **Destruction of Lateral Anchoring:** Tight NHC ($R_0 = 0.04\text{ m}^2/\text{s}^2$) is the sole physical mechanism preventing lateral velocity integration drift in 2D DR. Speed-dependent covariance inflation weakens lateral velocity innovation updates, allowing cross-track position error to explode from $124.23\text{ m}$ up to **$1061.27\text{ m}$**.
2. **Validation Protocol Selection:** All relaxed candidates failed validation selection ($722.66 - 1008.35\text{ m}$ vs Control $505.40\text{ m}$). F0 Control remains the validation winner.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m026_speed_dependent_nhc.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m026_speed_dependent_nhc.py)
- **Summary JSON:** `results/vw4_m026_speed_dependent_nhc_summary.json`
- **Predictions NPZ:** `results/vw4_m026_speed_dependent_nhc_predictions.npz`
- **Report Markdown:** [`results/vw4_m026_speed_dependent_nhc_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m026_speed_dependent_nhc_report.md)
- **Plot Directory:** `plots/vw4/m026_speed_dependent_nhc/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M026 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
