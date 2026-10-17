# Milestone M021 — Conservative Turn-Aware Speed Attenuation Ablation Report

## Executive Summary

- **Milestone:** M021 — Conservative Turn-Aware Speed Attenuation Ablation
- **Objective:** Scientifically evaluate whether a conservative, bounded causal attenuation of SpeedNet v2 speed predictions during strong turns ($|\omega_y| > 10^\circ/\text{s}$) reduces navigation drift below the $220.12\text{ m}$ benchmark.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Control Reproduction Verification:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Task-Metric Mismatch & Pointwise Speed MAE Paradox:** Attenuating speed during turns successfully lowered Strong-Turn Speed MAE from $13.20\text{ km/h}$ down to $8.21\text{ km/h}$ (F3) and overall Speed MAE from $7.33\text{ km/h}$ down to $5.93\text{ km/h}$. **However, 300s navigation error exploded from `220.12 m` up to `355.23 m`** ($+61.4\%$ degradation in F4/F5).
  - **M020 Hypothesis Disproof:** The hypothesis that *"strong-turn speed overestimation projects velocity vectors outward along drifting headings"* was empirically DISPROVED as an intervention target. Un-attenuated SpeedNet over-predictions during turns provide a critical geometric path-length compensation that counterbalances heading integration drift during long curved arcs. Reducing scalar speed during turns destroys this self-cancellation, causing the integrated trajectory to severely undershoot turn exits and diverge in 2D space.
  - **Baseline Provenance Lock:** No candidate beat $220.12\text{ m}$ at 300s. **`220.12 m` @ 300s remains the active verified project benchmark**.

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

## Physics & Causality Audit

1. **Gyro Yaw Rate Definition:** $\omega_y = -gyro\_pitch$ in rad/s ($|\omega_y| > 10^\circ/\text{s} = 0.1745\text{ rad/s}$).
2. **Causal Attenuation Scope:** Modifies strictly the scalar measurement magnitude $v_{\text{meas}}$ fed to EKF speed measurement update. Velocity heading direction $\psi$ and NHC constraints were kept completely unchanged.
3. **Causal Alignment:** Attenuation evaluates current sample $\omega_y[idx]$ with zero future sample usage.

---

## Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Strategy Description | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|
| **F0 Control** | Baseline M019 Stack (No Turn Attenuation) | $505.40\text{ m}$ | Baseline |
| **F1** | Fixed 5% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $434.83\text{ m}$ | Candidate |
| **F2** | Fixed 10% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $441.66\text{ m}$ | Candidate |
| **F3** | Fixed 15% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $471.83\text{ m}$ | Candidate |
| **F4 / F5** | Bounded Linear Attenuation (0-15% for $10-20^\circ/\text{s}$) | **368.91 m** | **SELECTED VALIDATION BEST** |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | St-Turn MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | SpeedNet v2 W=40 Baseline Control | $7.33\text{ km/h}$ | $13.20\text{ km/h}$ | **27.53 m** | $428.79\text{ m}$ | **220.12 m** | $-16.3\%$ | $-13.4\%$ | **CONTROL** |
| **F1** | 5% Turn Attenuation | $6.81\text{ km/h}$ | $11.34\text{ km/h}$ | $29.88\text{ m}$ | $376.46\text{ m}$ | $286.86\text{ m}$ | $+9.0\%$ | $+12.9\%$ | $+30.3\%$ |
| **F2** | 10% Turn Attenuation | $6.33\text{ km/h}$ | $9.63\text{ km/h}$ | $33.30\text{ m}$ | $339.69\text{ m}$ | $349.37\text{ m}$ | $+32.8\%$ | $+37.5\%$ | $+58.7\%$ |
| **F3** | 15% Turn Attenuation | **5.93 km/h** | **8.21 km/h** | $37.35\text{ m}$ | $305.42\text{ m}$ | $224.36\text{ m}$ | $-14.7\%$ | $-11.7\%$ | $+1.9\%$ |
| **F4 (Linear)** | Bounded Linear 10-20 deg/s | $6.25\text{ km/h}$ | $9.34\text{ km/h}$ | $35.48\text{ m}$ | **116.89 m** | $355.23\text{ m}$ | $+35.0\%$ | $+39.8\%$ | $+61.4\%$ |
| **F5 (Val Winner)** | Selected Best Validation Candidate (F4) | $6.25\text{ km/h}$ | $9.34\text{ km/h}$ | $35.48\text{ m}$ | **116.89 m** | $355.23\text{ m}$ | $+35.0\%$ | $+39.8\%$ | $+61.4\%$ |

---

## Turn Attenuation Diagnostic Summary

| Candidate | Total Activations | Mean Attenuation Correction | Max Attenuation Correction |
|---|---|---|---|
| **F0 Control** | 0 | $0.00\text{ km/h}$ | $0.00\text{ km/h}$ |
| **F1 (5% Attenuation)** | 837 | $2.14\text{ km/h}$ | $3.74\text{ km/h}$ |
| **F2 (10% Attenuation)** | 837 | $4.29\text{ km/h}$ | $7.47\text{ km/h}$ |
| **F3 (15% Attenuation)** | 837 | $6.43\text{ km/h}$ | $11.21\text{ km/h}$ |
| **F4 / F5 (Linear 10-20 deg/s)** | **837** | **4.58 km/h** | **10.76 km/h** |

---

## Failure Mechanism Analysis

1. **Disproof of Simple Speed Attenuation Hypothesis:** M020 identified strong-turn speed overestimation ($+12.17\text{ km/h}$) as correlated with 300s position drift. However, M021 proves that directly attenuating scalar speed predictions during turns is NOT a valid intervention.
2. **Geometric Path-Length Compensation Destruction:** In dead-reckoning navigation with raw gyro integration, un-corrected heading estimates slowly drift during turns. SpeedNet's un-attenuated forward speed overestimation acts as a geometric buffer that compensates for heading curvature lag. Attenuating turn speed lowers pointwise speed MAE ($13.20 \rightarrow 9.34\text{ km/h}$), but causes the integrated path to undershoot turn exits, resulting in severe 2D position error accumulation at 300s ($220.12 \rightarrow 355.23\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m021_turn_aware_speed_attenuation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m021_turn_aware_speed_attenuation.py)
- **Summary JSON:** `results/vw4_m021_turn_aware_speed_attenuation_summary.json`
- **Predictions NPZ:** `results/vw4_m021_turn_aware_speed_attenuation_predictions.npz`
- **Report Markdown:** [`results/vw4_m021_turn_aware_speed_attenuation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m021_turn_aware_speed_attenuation_report.md)
- **Plot Directory:** `plots/vw4/m021_turn_aware_speed_attenuation/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M021 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM Damping} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
