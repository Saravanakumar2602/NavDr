# Milestone M033 — Causal SpeedNet Confidence-Weighted Velocity Innovation Fusion

## 1. Executive Summary

- **Milestone:** M033 — Causal SpeedNet Confidence-Weighted Velocity Innovation Fusion
- **Objective:** Evaluate whether scaling SpeedNet's measurement covariance $R_v(k) = R_0 (1 + \beta \cdot \sigma_{a, \text{causal}}^2)$ dynamically based on causal longitudinal acceleration variance reduces dead-reckoning drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** Candidate F1 ($\beta = 0.01$, 0.5s window) achieved $489.30\text{ m}$ on validation (`88566:107535`).
  - **Locked Test Result:** Validation winner F1 ($\beta = 0.01$) degraded 300s position error to **`225.86 m`** ($+6.93\text{ m}$ / **+3.2% degradation** vs Control `218.93 m`). Higher values of $\beta$ ($\beta \ge 0.05$) caused catastrophic drift explosion ($348.16 - 711.51\text{ m}$).
  - **Failure Mechanism:** Suppressing SpeedNet updates during transients forces open-loop double-integration of noisy IMU acceleration, accelerating tilt/bias error accumulation.

---

## 2. Objective & Hypothesis

Evaluate whether causal longitudinal acceleration variance predicts SpeedNet velocity error, and test whether dynamically scaling $R_v(k) = R_0 (1 + \beta \sigma_a^2)$ reduces 300s dead-reckoning position drift below $218.93\text{ m}$.

---

## 3. Locked M028 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Phase 1 — Diagnostic Methodology & Validation Results

- Pearson ($r$) and Spearman ($\rho$) rank correlation evaluated across causal windows $\{0.5, 1.0, 2.0, 5.0\}\text{ s}$:
  - **0.5s Window (5 samples):** Pearson $r = +0.0240$, Spearman $\rho = \mathbf{+0.2320}$, Q1 MAE = $8.44\text{ km/h}$, Q4 MAE = $13.37\text{ km/h}$ (Ratio Q4/Q1 = 1.58x).
  - **1.0s Window (10 samples):** Pearson $r = +0.0249$, Spearman $\rho = +0.2296$, Q1 MAE = $8.36\text{ km/h}$, Q4 MAE = $12.90\text{ km/h}$ (Ratio Q4/Q1 = 1.54x).
  - **2.0s Window (20 samples):** Pearson $r = +0.0223$, Spearman $\rho = +0.2098$, Q1 MAE = $8.72\text{ km/h}$, Q4 MAE = $12.18\text{ km/h}$ (Ratio Q4/Q1 = 1.40x).
  - **5.0s Window (50 samples):** Pearson $r = -0.0126$, Spearman $\rho = +0.1490$, Q1 MAE = $9.73\text{ km/h}$, Q4 MAE = $11.49\text{ km/h}$ (Ratio Q4/Q1 = 1.18x).
- **Window Selection:** 0.5s window selected based strictly on highest validation Spearman correlation.

---

## 5. Phase 2 & 3 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Scaling Parameter ($\beta$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | $\beta = 0.00$ (Fixed $R_v = 1.0$) | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | $\mathbf{\beta = 0.01}$ | **489.30 m** | **346.38 m** | **SELECTED VALIDATION WINNER** |
| **F2** | $\beta = 0.05$ | $807.11\text{ m}$ | $327.42\text{ m}$ | Degraded |
| **F3** | $\beta = 0.10$ | $1,093.39\text{ m}$ | $309.01\text{ m}$ | Severely Degraded |
| **F4** | $\beta = 0.25$ | $1,295.84\text{ m}$ | $305.52\text{ m}$ | Severely Degraded |

---

## 6. Locked Unseen Test Sweep Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\beta = 0.01$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.22\text{ m}$ | $444.56\text{ m}$ | **225.86 m** | $-14.2\%$ | $+2.6\%$ | **+3.2%** |
| **F2 ($\beta = 0.05$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $26.59\text{ m}$ | $571.73\text{ m}$ | **348.16 m** | $+32.3\%$ | $+58.2\%$ | **+59.0%** |
| **F3 ($\beta = 0.10$)** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $25.70\text{ m}$ | $761.15\text{ m}$ | **553.97 m** | $+110.5\%$ | $+151.7\%$ | **+153.0%** |
| **F4 ($\beta = 0.25$)** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $23.07\text{ m}$ | $917.65\text{ m}$ | **711.51 m** | $+170.4\%$ | $+223.2\%$ | **+225.0%** |
| **F5 (Val Winner F1)** | **7.33 km/h** | **11.57 km/h** | **27.22 m** | **444.56 m** | **225.86 m** | **-14.2%** | **+2.6%** | **+3.2%** |

---

## 7. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 8. Empirical Mechanism Interpretation & 9. Failure Analysis

Causal acceleration variance is empirically associated with increased SpeedNet speed error ($\rho = 0.2320$). However, down-weighting SpeedNet updates during high-variance transients forces the EKF to rely on open-loop double-integration of noisy IMU acceleration, accelerating tilt/bias error accumulation and degrading 120s and 300s position error (+3.2% to +225.0% degradation).

---

## 10. Final Verdict

**REJECTED (BRANCH PERMANENTLY CLOSED)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 11. Recommended Next Experiment (M034 Proposal)

**M034 Proposal — Longitudinal Acceleration Bias Estimator Integration**:
With measurement covariance modifications (M016, M026, M032, M033) permanently closed, residual error analysis shows that uncompensated accelerometer bias $b_{a, y}$ drives long-horizon velocity drift during straight cruising. M034 should evaluate a zero-velocity bias update during ZUPT intervals ($\dot{b}_a = 0$, $K_{ba}$ update during $P_{\text{stat}} > 0.70$) to bound accelerometer bias drift before outage onset, driving 300s position error below $218.93\text{ m}$.

---

## 12. Full M001 → M033 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033`
