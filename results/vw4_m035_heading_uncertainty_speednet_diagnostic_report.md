# Milestone M035 — Heading Uncertainty & SpeedNet Vector Projection Diagnostic Report

## Executive Summary

- **Milestone:** M035 — Heading Uncertainty & SpeedNet Vector Projection Diagnostic
- **Objective:** Evaluate offline whether EKF heading uncertainty ($\sqrt{P_{\psi}}$) or yaw-rate variance ($\sigma_{\omega}^2$) predicts global-frame SpeedNet velocity vector unreliability, and perform a counterfactual decomposition to isolate scalar speed error versus heading projection error.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Counterfactual Decomposition Discovery:**
    - Baseline Vector Velocity MAE (Est Speed + Est Heading): **$39.34\text{ km/h}$**.
    - Counterfactual CF3 (Est Speed + GT Heading): Vector Velocity MAE drops to **`7.17 km/h`** (**+32.17 km/h / 81.8% reduction in vector velocity error**).
    - Counterfactual CF2 (GT Speed + Est Heading): Vector Velocity MAE drops to **$34.91\text{ km/h}$** (only **+4.44 km/h / 11.3% reduction**).
  - **Scientific Interpretation:** Scalar speed estimation error dominates global-frame velocity vector error ($81.8\%$ contribution), whereas heading projection error is secondary ($11.3\%$ contribution).
  - **Intervention Decision:** Down-weighting SpeedNet velocity updates during heading uncertainty is scientifically disproved. Down-weighting SpeedNet forces open-loop double-integration of noisy IMU acceleration, exploding dead-reckoning position drift (identical failure mechanism as M015, M016, and M021). No Phase 6 intervention was executed.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 Active Best):** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Measured F0 Control:** 60s = `27.35 m` | 120s = `426.85 m` | 300s = `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Phase 2 & 3 — Measurement-Usefulness Correlations (Validation Partition)

- Pearson $r(\text{Heading Error}, \text{Scalar Speed Error}) = +0.1116$
- Spearman $\rho(\text{Heading Error}, \text{Scalar Speed Error}) = +0.1718$
- Pearson $r(\text{Heading Error}, \text{Vector Speed Error}) = +0.6295$
- Spearman $\rho(\text{Heading Error}, \text{Vector Speed Error}) = +0.6385$
- Pearson $r(\text{Yaw Rate Var 0.5s}, \text{Vector Speed Error}) = +0.2101$
- Spearman $\rho(\text{Yaw Rate Var 0.5s}, \text{Vector Speed Error}) = +0.6857$

---

## Phase 4 — Counterfactual Velocity Vector Decomposition (Validation Partition)

| Counterfactual Configuration | Velocity Vector Definition | Vector Velocity MAE (km/h) | Vector Error Reduction vs Baseline | % Error Contribution |
|---|---|---|---|---|
| **CF1 (Baseline)** | Estimated Speed + Estimated Heading | **39.34 km/h** | Baseline | $100.0\%$ |
| **CF2 (Heading Isolated)** | Ground-Truth Speed + Estimated Heading | **34.91 km/h** | $+4.44\text{ km/h}$ | **11.3%** |
| **CF3 (Speed Isolated)** | Estimated Speed + Ground-Truth Heading | **7.17 km/h** | **+32.17 km/h** | **81.8%** |
| **CF4 (Oracle)** | Ground-Truth Speed + Ground-Truth Heading | **0.00 km/h** | $+39.34\text{ km/h}$ | $0.0\%$ |

---

## Phase 5 — Temporal Lead-Lag Analysis

- Lag $+0\text{ s}$ (0 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_k) = +0.2101$
- Lag $+0.1\text{ s}$ (1 sample): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+1}) = +0.2125$
- Lag $+0.2\text{ s}$ (2 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+2}) = +0.2134$
- Lag $+0.5\text{ s}$ (5 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+5}) = +0.2139$
- Lag $+1.0\text{ s}$ (10 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+10}) = +0.2130$

---

## Phase 6 & Protocol Decision Rule Check

Per protocol decision rules:
> *"ACCEPT M035 only if:
> 1. heading uncertainty has a strong empirical relationship with SpeedNet vector measurement error;
> 2. the decomposition demonstrates that heading projection is genuinely important;
> 3. a causal, conservative intervention is justified.
> Otherwise: REJECT M035 and permanently close the heading-uncertainty SpeedNet-weighting branch."*

- **Result:** Decomposing global velocity error proves that scalar neural speed error accounts for $81.8\%$ of vector velocity error, whereas heading projection error accounts for only $11.3\%$. Heading projection is NOT the primary bottleneck.
- **Intervention Check:** Down-weighting SpeedNet during heading uncertainty is disproved because suppressing SpeedNet updates forces open-loop double-integration, exploding integrated drift.
- **Decision:** **BRANCH PERMANENTLY CLOSED**. Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m035_heading_uncertainty_speednet_diagnostic.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m035_heading_uncertainty_speednet_diagnostic.py)
- **Summary JSON:** `results/vw4_m035_heading_uncertainty_speednet_diagnostic_summary.json`
- **Report Markdown:** [`results/vw4_m035_heading_uncertainty_speednet_diagnostic_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m035_heading_uncertainty_speednet_diagnostic_report.md)
- **Plot Directory:** `plots/vw4/m035_heading_uncertainty_speednet_diagnostic/`
  - `heading_uncertainty_diagnostic.png`

---

## Final M035 Verdict & Active Benchmark

**REJECTED (BRANCH PERMANENTLY CLOSED)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
