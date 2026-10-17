# M044 Causal Turn/Deceleration Measurement-Weighting Study

## Executive Summary
- **Milestone:** M044 — Causal Turn/Deceleration Measurement-Weighting Study
- **Objective:** Evaluate whether causally reducing/suppressing APM pseudo-measurements or downweighting SpeedNet velocity updates during strong turns and braking improves distance-normalized navigation.
- **Validation Selection:** Candidate **`F3`** ($|\omega_y| > 12.5^\circ/\text{s}$, SpeedNet $R_v \times 10.0$) achieved validation gain ($492.74\text{ m} \to 145.08\text{ m}$).
- **Locked Test Evaluation:** On unseen test data, Candidate F3 **degraded 300s position drift from 218.93 m to 574.98 m (+162.6% error expansion)** and 1 km error from **307.46 m to 559.34 m (+81.9% error expansion)**.
- **Verdict:** **`B. REJECTED — Production pipeline retained at 218.93 m @ 300s baseline.`**
- **Production Pipeline Changed:** **NO**.

## Test Performance Comparison Table

| Metric | Locked Production Baseline (F0) | Validation-Selected Candidate (F3) | Delta / Change | Status |
|---|---|---|---|---|
| **60 s Error (m)** | **27.88 m** | 40.11 m | +12.76 m (+46.7%) | <span style="color:orange; font-weight:bold;">Slight Degraded</span> |
| **120 s Error (m)** | **426.17 m** | 376.29 m | -50.56 m (-11.8%) | <span style="color:green; font-weight:bold;">Slight Improved</span> |
| **300 s Error (m)** | **218.93 m** | 574.98 m | +356.05 m (+162.6%) | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **1 km Error (m)** | **307.46 m** | 559.34 m | +251.88 m (+81.9%) | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **300 s FPER (%)** | **15.81 %** | 41.53 % | +25.71 % | <span style="color:red; font-weight:bold;">FAIL</span> |
| **1 km FPER (%)** | **30.74 %** | 55.93 % | +25.19 % | <span style="color:red; font-weight:bold;">FAIL</span> |

## Physical Mechanism Breakdown
1. **Why did Candidate F3 fail on unseen test set?**  
   Downweighting SpeedNet velocity updates during turns ($R_v \times 10.0$) forces the EKF to rely strictly on open-loop gyro/accelerometer integration during turn maneuvers.
2. **Disruption of Geometric Self-Cancellation:**  
   As proven in M040 and M042, SpeedNet forward velocity overestimation actively compensates for along-track integration lag. Downweighting SpeedNet during turns suppresses this forward velocity anchor, exploding 300s position drift from $218.93\text{ m}$ to $574.98\text{ m}$.

## Final Verdict
**`B. REJECTED — Candidate F3 (selected on validation) is REJECTED on the locked test set due to severe 300s position error expansion (+162.6% degradation from 218.93m to 574.98m) and 1km error expansion (+81.9% degradation from 307.46m to 559.34m) caused by geometric self-cancellation disruption. The production pipeline remains LOCKED at M028/M040 baseline (218.93 m @ 300s).`**
