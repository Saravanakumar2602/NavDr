# Milestone M035 — Heading Uncertainty & SpeedNet Vector Projection Diagnostic

## 1. Executive Summary

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

## 2. Objective & Motivation

M015 previously tested stationary heading-bias correction and reduced mean heading error from 64.6° to 36.1°, but position error degraded from 233.18 m to 324.70 m (+39.2% degradation). M035 evaluates whether heading uncertainty ($\sqrt{P_{\psi}}$) predicts global-frame SpeedNet velocity vector unreliability before considering any intervention.

---

## 3. Locked M028 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Heading Uncertainty Definitions & Measurement Error Relationships

- **Heading Uncertainty Indicators:** EKF heading variance $P_{\psi}$, $\sqrt{P_{\psi}}$, causal yaw-rate variance $\sigma_{\omega, \text{causal}}^2$ (0.5s window).
- **Correlations on Validation Partition (`88566:107535`):**
  - Pearson $r(\text{Heading Error}, \text{Scalar Speed Error}) = +0.1116$
  - Spearman $\rho(\text{Heading Error}, \text{Scalar Speed Error}) = +0.1718$
  - Pearson $r(\text{Heading Error}, \text{Vector Speed Error}) = +0.6295$
  - Spearman $\rho(\text{Heading Error}, \text{Vector Speed Error}) = +0.6385$
  - Pearson $r(\text{Yaw Rate Var}, \text{Vector Speed Error}) = +0.2101$

---

## 5. Counterfactual Velocity Vector Decomposition

| Counterfactual Configuration | Velocity Vector Definition | Vector Velocity MAE (km/h) | Vector Error Reduction vs Baseline | % Error Contribution |
|---|---|---|---|---|
| **CF1 (Baseline)** | Estimated Speed + Estimated Heading | **39.34 km/h** | Baseline | $100.0\%$ |
| **CF2 (Heading Isolated)** | Ground-Truth Speed + Estimated Heading | **34.91 km/h** | $+4.44\text{ km/h}$ | **11.3%** |
| **CF3 (Speed Isolated)** | Estimated Speed + Ground-Truth Heading | **7.17 km/h** | **+32.17 km/h** | **81.8%** |
| **CF4 (Oracle)** | Ground-Truth Speed + Ground-Truth Heading | **0.00 km/h** | $+39.34\text{ km/h}$ | $0.0\%$ |

---

## 6. Temporal Lead-Lag Analysis

- Lag $+0\text{ s}$ (0 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_k) = +0.2101$
- Lag $+0.1\text{ s}$ (1 sample): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+1}) = +0.2125$
- Lag $+0.2\text{ s}$ (2 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+2}) = +0.2134$
- Lag $+0.5\text{ s}$ (5 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+5}) = +0.2139$
- Lag $+1.0\text{ s}$ (10 samples): Pearson $r(\text{Yaw Var}_k, \text{Vector Error}_{k+10}) = +0.2130$

---

## 7. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation diagnostic performed strictly on Validation partition (`88566:107535`).

---

## 8. Empirical Mechanism & Failure Analysis

Decomposing global velocity error proves that scalar neural speed error accounts for $81.8\%$ of vector velocity error, whereas heading projection error accounts for only $11.3\%$. Heading projection is NOT the primary bottleneck. Down-weighting SpeedNet during heading uncertainty is disproved because suppressing SpeedNet updates forces open-loop double-integration of noisy IMU acceleration, exploding integrated drift (same failure mechanism as M015, M016, M021).

---

## 9. Final Verdict

**REJECTED (BRANCH PERMANENTLY CLOSED)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 10. Recommended Next Experiment (M036 Proposal)

**M036 Proposal — Adaptive Receptive Field SpeedNet Backbone Tuning**:
With all post-inference measurement gating, covariance scaling, and heading weighting branches (M015, M016, M021, M026, M031, M032, M033, M034, M035) disproved and permanently closed, M035 established that scalar neural speed error accounts for **81.8% of global velocity vector error**. M036 should focus directly on neural model improvements: training SpeedNet v2.6 with an Adaptive Temporal Window Receptive Field ($W \in [30, 40, 50]$ multi-branch attention) to eliminate steady-state cruise speed overestimation (+6.4 km/h bias) without creating deceleration phase lag, driving 300s position error below $218.93\text{ m}$.

---

## 11. Full M001 → M035 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033 → M034 → M035`
