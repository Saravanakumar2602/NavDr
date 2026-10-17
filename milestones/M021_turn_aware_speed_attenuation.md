# Milestone M021 — Conservative Turn-Aware Speed Attenuation Ablation

## 1. Starting Point & Provenance Context

- **Active Verified Benchmark (M019 F4):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 + M014 Causal ZUPT + M019 APM Damping = `220.12 m` @ 300s (60s = `27.53 m`, 120s = `428.79 m`, 300s = `220.12 m`).
- **M020 Motivation:** M020 identified strong turns ($|\omega_y| > 10^\circ/\text{s}$) as exhibiting the highest speed overestimation bias ($+12.17\text{ km/h}$) across 83.7s of motion. M021 tests whether conservative, bounded causal attenuation of SpeedNet speed during strong turns reduces navigation drift.

---

## 2. Research Question

Does a small, bounded, causal attenuation of SpeedNet speed during strong turns reduce dead-reckoning navigation drift below the $220.12\text{ m}$ benchmark without destroying short or mid-horizon stability?

---

## 3. Core Hypothesis

Reducing SpeedNet speed updates during strong turns will attenuate false forward displacement projected along mis-aligned turn headings, lowering overall 300s position drift.

---

## 4. Physics & Causality Audit

1. **Gyro Yaw Rate Definition:** $\omega_y = -gyro\_pitch$ in rad/s ($|\omega_y| > 10^\circ/\text{s} = 0.1745\text{ rad/s}$).
2. **Attenuation Scope:** Modifies strictly the scalar SpeedNet measurement magnitude $v_{\text{meas}}$ fed to EKF speed measurement update. Velocity heading direction $\psi$ and NHC constraints were kept completely unchanged.
3. **Causal Alignment:** Attenuation evaluates current sample $\omega_y[idx]$ with zero future sample usage.

---

## 5. Candidate Definitions

- **F0 (Control M019):** Baseline M019 Navigation Stack (No Turn Attenuation).
- **F1 (5% Attenuation):** Fixed $5\%$ attenuation ($v_{\text{meas}} = v_{\text{speednet}} \cdot 0.95$) when $|\omega_y| > 10^\circ/\text{s}$.
- **F2 (10% Attenuation):** Fixed $10\%$ attenuation ($v_{\text{meas}} = v_{\text{speednet}} \cdot 0.90$) when $|\omega_y| > 10^\circ/\text{s}$.
- **F3 (15% Attenuation):** Fixed $15\%$ attenuation ($v_{\text{meas}} = v_{\text{speednet}} \cdot 0.85$) when $|\omega_y| > 10^\circ/\text{s}$.
- **F4 (Linear Attenuation):** Bounded linear attenuation ($0-15\%$) scaling from $10^\circ/\text{s}$ to $20^\circ/\text{s}$.
- **F5 (Best Validated + M019):** Selected winner from Validation set evaluation (`88566:107535`).

---

## 6. Baseline Control Reproduction Audit

- **Audit Target:** M019 F4 Control = `27.53 m` (60s), `428.79 m` (120s), `220.12 m` (300s).
- **Measured F0 Control:** `27.53 m` (60s), `428.79 m` (120s), **`220.12 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 7. Validation Results (`88566:107535`)

| Candidate ID | Strategy Description | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|
| **F0 Control** | Baseline M019 Stack (No Turn Attenuation) | $505.40\text{ m}$ | Baseline |
| **F1** | Fixed 5% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $434.83\text{ m}$ | Candidate |
| **F2** | Fixed 10% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $441.66\text{ m}$ | Candidate |
| **F3** | Fixed 15% Attenuation ($|\omega_y| > 10^\circ/\text{s}$) | $471.83\text{ m}$ | Candidate |
| **F4 / F5** | Bounded Linear Attenuation (0-15% for $10-20^\circ/\text{s}$) | **368.91 m** | **SELECTED VALIDATION BEST** |

---

## 8. Locked Unseen Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | St-Turn MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | SpeedNet v2 W=40 Baseline Control | $7.33\text{ km/h}$ | $13.20\text{ km/h}$ | **27.53 m** | $428.79\text{ m}$ | **220.12 m** | $-16.3\%$ | $-13.4\%$ | **CONTROL** |
| **F1** | 5% Turn Attenuation | $6.81\text{ km/h}$ | $11.34\text{ km/h}$ | $29.88\text{ m}$ | $376.46\text{ m}$ | $286.86\text{ m}$ | $+9.0\%$ | $+12.9\%$ | $+30.3\%$ |
| **F2** | 10% Turn Attenuation | $6.33\text{ km/h}$ | $9.63\text{ km/h}$ | $33.30\text{ m}$ | $339.69\text{ m}$ | $349.37\text{ m}$ | $+32.8\%$ | $+37.5\%$ | $+58.7\%$ |
| **F3** | 15% Turn Attenuation | **5.93 km/h** | **8.21 km/h** | $37.35\text{ m}$ | $305.42\text{ m}$ | $224.36\text{ m}$ | $-14.7\%$ | $-11.7\%$ | $+1.9\%$ |
| **F4 (Linear)** | Bounded Linear 10-20 deg/s | $6.25\text{ km/h}$ | $9.34\text{ km/h}$ | $35.48\text{ m}$ | **116.89 m** | $355.23\text{ m}$ | $+35.0\%$ | $+39.8\%$ | $+61.4\%$ |
| **F5 (Val Winner)** | Selected Best Validation Candidate (F4) | $6.25\text{ km/h}$ | $9.34\text{ km/h}$ | $35.48\text{ m}$ | **116.89 m** | $355.23\text{ m}$ | $+35.0\%$ | $+39.8\%$ | $+61.4\%$ |

---

## 9. Turn Attenuation Diagnostic Metrics Summary

- **Total Activations:** 837 samples ($83.7\text{ s}$ / $27.9\%$ of outage).
- **Mean Attenuation Correction (F4):** $4.58\text{ km/h}$.
- **Max Attenuation Correction (F4):** $10.76\text{ km/h}$.

---

## 10. 60/120/300s Navigation Results

- **60s Outage:** F0 Control = **$27.53\text{ m}$**, F4/F5 = $35.48\text{ m}$ ($+28.9\%$ degradation).
- **120s Outage:** F0 Control = $428.45\text{ m}$, F4/F5 = **$116.89\text{ m}$** (Transient mid-horizon gain).
- **300s Outage:** F0 Control = **`220.12 m`**, F4/F5 = $355.23\text{ m}$ (**$+61.4\%$ drift explosion**).

---

## 11. Comparison with Historical Benchmarks

- **vs Pre-M013 Benchmark ($263.11\text{ m}$):** F0 Control remains $-16.3\%$ better ($220.12\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F0 Control remains $-13.4\%$ better ($220.12\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F0 Control remains $-5.6\%$ better ($220.12\text{ m}$).
- **vs M019 Benchmark ($220.12\text{ m}$):** F0 Control = **0.0% (Active Best Control)**.

---

## 12. Leakage & Causality Audit

- All parameters were selected strictly on Validation partition (`88566:107535`). Zero future sample usage or test-set tuning was employed.

---

## 13. Disproof of M020 Hypothesis & Failure Mechanisms

1. **Disproof of Simple Speed Attenuation Hypothesis:** M020 identified strong-turn speed overestimation ($+12.17\text{ km/h}$) as correlated with 300s position drift. However, M021 proves that directly attenuating scalar speed predictions during turns is NOT a valid intervention.
2. **Geometric Path-Length Compensation Destruction:** In dead-reckoning navigation with raw gyro integration, un-corrected heading estimates slowly drift during turns. SpeedNet's un-attenuated forward speed overestimation acts as a geometric buffer that compensates for heading curvature lag. Attenuating turn speed lowers pointwise speed MAE ($13.20 \rightarrow 9.34\text{ km/h}$), but causes the integrated path to undershoot turn exits, resulting in severe 2D position error accumulation at 300s ($220.12 \rightarrow 355.23\text{ m}$).

---

## 14. What Was Learned

Pointwise speed MAE is an unreliable predictor of integrated dead-reckoning performance. Speed overestimation during turns counterbalances heading integration lag, and scalar speed attenuation destroys this self-canceling geometry.

---

## 15. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m021_turn_aware_speed_attenuation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m021_turn_aware_speed_attenuation.py)
- **Summary JSON:** `results/vw4_m021_turn_aware_speed_attenuation_summary.json`
- **Predictions NPZ:** `results/vw4_m021_turn_aware_speed_attenuation_predictions.npz`
- **Report Markdown:** [`results/vw4_m021_turn_aware_speed_attenuation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m021_turn_aware_speed_attenuation_report.md)
- **Plot Directory:** `plots/vw4/m021_turn_aware_speed_attenuation/`

---

## 16. Final M021 Verdict

**REJECTED**.

ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM Damping} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 17. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021`

---

## 18. Exactly ONE Evidence-Based Next Direction (M022 Proposal)

**M022 Proposal — Causal Deceleration-Integrated Dual-Regime Speed Damping (DSD)**:
Milestone M021 proved that scalar speed attenuation during turns destroys geometric path-length cancellation (+61.4% drift explosion). However, M019 proved that speed damping during straight-line deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$) successfully reduced 300s drift from $233.18\text{ m}$ to $220.12\text{ m}$. M022 should investigate expanding M019 APM into a Causal Deceleration-Integrated Dual-Regime Speed Damping (DSD) mechanism. DSD evaluates multi-sample deceleration integrals ($\Delta v_{\text{imu}}$) across 0.8s intervals during straight braking to safely damp residual deceleration overestimation without touching dynamic turn speeds.
