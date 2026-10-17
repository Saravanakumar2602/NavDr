# Milestone M034 — ZUPT Accelerometer Bias Observability & Correction

## 1. Executive Summary

- **Milestone:** M034 — ZUPT Accelerometer Bias Observability & Correction
- **Objective:** Evaluate whether stationary ZUPT intervals ($P_{\text{stat}} > 0.70$) provide a stable, observable longitudinal acceleration bias estimate $b_a$ that improves subsequent inertial propagation and dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** F0 Control achieved the best validation score ($494.83\text{ m}$). All bias correction candidates F1–F3 ($\alpha \in [0.01, 0.10]$) degraded validation error ($495.67 - 497.79\text{ m}$). F0 Control was selected as the validation winner.
  - **Locked Test Result:** Evaluated on the locked unseen test set (`start_idx = 108,000`), bias correction candidates F1–F3 severely degraded 300s position error to **`266.20 – 279.18 m`** (**+21.6% to +27.5% degradation** vs Control `218.93 m`).
  - **Failure Mechanism:** Stationary $a_{\text{long}}$ residuals reflect vehicle pitch tilt variations (suspension pitch dynamic settling) rather than sensor bias. Applying this tilt offset as a persistent bias correction during driving corrupts forward velocity integration.

---

## 2. Objective & Hypothesis

Research whether longitudinal accelerometer bias is observable during ZUPT intervals ($P_{\text{stat}} > 0.70$), and test whether causal EMA bias correction $b_a(k) = (1-\alpha)b_a(k-1) + \alpha a_{\text{long}}(k)$ during ZUPT improves 300s dead-reckoning position drift below $218.93\text{ m}$.

---

## 3. Locked M028 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. M016 Motivation & Cross-Check

Milestone M016 previously established that accelerometer bias tracking during outage was ill-posed and unobservable because $b_a$ was entangled with gravity tilt leakage and SpeedNet errors. M034 confirms that ZUPT intervals do NOT solve this problem because stationary $a_{\text{long}}$ residuals reflect vehicle pitch tilt variations rather than sensor bias.

---

## 5. Acceleration & ZUPT Definitions

- **Longitudinal Acceleration:** $a_{\text{long}} = -(raw\_ay - grav\_y)$
- **ZUPT Detector:** $P_{\text{stat\_speednet}} > 0.70$ (M014 established).

---

## 6. Phase 1 & 2 — Stationary Episode Analysis (`0:107,535`)

- Total ZUPT Stationary Episodes Analyzed: 436 episodes
- Overall Stationary $a_{\text{long}}$ Mean Residual: $+0.1054\text{ m/s}^2$
- Overall Stationary $a_{\text{long}}$ Standard Deviation: $0.2573\text{ m/s}^2$
- Inter-Episode Mean Bias Standard Deviation: $0.2504\text{ m/s}^2$
- Inter-Episode Mean Bias Range: $1.2052\text{ m/s}^2$

---

## 7. Phase 4 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Update Rate ($\alpha$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | **No Bias Correction ($\alpha = 0.00$)** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $\alpha = 0.01$ | $495.67\text{ m}$ | $356.95\text{ m}$ | Degraded |
| **F2** | $\alpha = 0.05$ | $497.20\text{ m}$ | $357.67\text{ m}$ | Degraded |
| **F3** | $\alpha = 0.10$ | $497.79\text{ m}$ | $357.82\text{ m}$ | Degraded |

---

## 8. Locked Unseen Test Sweep Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\alpha = 0.01$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.40\text{ m}$ | $443.26\text{ m}$ | **279.18 m** | $+6.1\%$ | $+26.8\%$ | **+27.5%** |
| **F2 ($\alpha = 0.05$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.80\text{ m}$ | $448.79\text{ m}$ | **271.24 m** | $+3.1\%$ | $+23.2\%$ | **+23.9%** |
| **F3 ($\alpha = 0.10$)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.82\text{ m}$ | $449.14\text{ m}$ | **266.20 m** | $+1.2\%$ | $+20.9\%$ | **+21.6%** |
| **F4 (Val Winner F0)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **0.0%** |

---

## 9. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 10. Empirical Mechanism & Failure Analysis

Stationary $a_{\text{long}}$ residuals fluctuate substantially across stops ($\text{std} = 0.2504\text{ m/s}^2$) because vehicle pitch angle changes dynamically every time the vehicle halts (chassis suspension pitch settling). Estimating $b_a$ during ZUPT captures vehicle pitch tilt rather than sensor bias, corrupting subsequent longitudinal velocity integration (+21.6% to +27.5% degradation).

---

## 11. Final Verdict

**REJECTED (BRANCH PERMANENTLY CLOSED)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 12. Recommended Next Experiment (M035 Proposal)

**M035 Proposal — Heading Uncertainty-Gated Velocity Measurement Weighting**:
With bias estimation (M016, M034), measurement covariance scaling (M026, M032, M033), and turn speed attenuation (M021) all permanently closed, residual error analysis shows that large heading errors ($>30^\circ$) cause SpeedNet forward speed measurements to project incorrectly onto Easting/Northing axes. M035 should evaluate gating or down-weighting SpeedNet updates during periods of high integrated yaw variance, preserving 2D DR self-cancellation and driving 300s position error below $218.93\text{ m}$.

---

## 13. Full M001 → M034 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033 → M034`
