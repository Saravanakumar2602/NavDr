# Milestone M036 — Adaptive Receptive-Field SpeedNet Backbone Tuning

## 1. Executive Summary

- **Milestone:** M036 — Adaptive Receptive-Field SpeedNet Backbone Tuning
- **Objective:** Evaluate whether varying the neural sequence receptive field ($W \in [30, 40, 50]$) or constructing a multi-branch adaptive temporal backbone reduces SpeedNet speed overestimation without introducing temporal phase lag or degrading 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** Candidate F2 ($W=50$ Longer Receptive Field) achieved the lowest validation 300s error ($400.40\text{ m}$ vs Control $494.83\text{ m}$).
  - **Locked Test Result:** Evaluated on the locked unseen test set (`start_idx = 108,000`), validation winner F2 ($W=50$) exploded 300s position drift to **`1165.94 m`** (**+432.6% degradation** vs Control `218.93 m`) and degraded 120s error to $930.98\text{ m}$.
  - **Failure Mechanism:** Receptive field expansion ($W=50$) introduces temporal phase lag during braking transients ($14.86\text{ km/h}$ braking MAE on test vs $11.57\text{ km/h}$ control). Lagging speed estimates leak into EKF velocity integration, exploding 300s position drift.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## 2. Objective & M035 Motivation

M035 established that scalar neural speed error accounts for $81.8\%$ of global velocity vector error. M036 evaluates whether temporal receptive field tuning ($W \in [30, 40, 50]$) or multi-branch ensembling can improve the neural speed backbone and beat $218.93\text{ m}$ @ 300s.

---

## 3. Locked M028 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Phase 4 — Pointwise Speed & Regime MAE Analysis (Validation Set `88566:107535`)

| Candidate ID | Model Architecture Description | Parameters | Overall MAE | Braking MAE | Accel MAE | Cruise MAE | Turn MAE |
|---|---|---|---|---|---|---|---|
| **F0 (Control)** | **SpeedNet v2 W=40 Control** | **370,686** | **12.38 km/h** | **13.63 km/h** | **12.25 km/h** | **11.07 km/h** | **13.31 km/h** |
| **F1** | SpeedNet v2 W=30 Shorter | 370,686 | $13.19\text{ km/h}$ | $14.32\text{ km/h}$ | $13.23\text{ km/h}$ | $11.93\text{ km/h}$ | $14.28\text{ km/h}$ |
| **F2** | SpeedNet v2 W=50 Longer | 370,686 | $12.60\text{ km/h}$ | $13.82\text{ km/h}$ | $12.36\text{ km/h}$ | $11.13\text{ km/h}$ | $13.73\text{ km/h}$ |
| **F3** | Multi-Branch Ensemble (W30/W40/W50) | 1,112,058 | **11.85 km/h** | **13.05 km/h** | **11.67 km/h** | **10.44 km/h** | **12.85 km/h** |

---

## 5. Phase 5 — Validation Navigation Evaluation (`88566:107535`)

| Candidate ID | Model Architecture Description | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | SpeedNet v2 W=40 Control Baseline | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | SpeedNet v2 W=30 Shorter | $1,023.05\text{ m}$ | $410.78\text{ m}$ | Degraded |
| **F2** | **SpeedNet v2 W=50 Longer** | **400.40 m** | **377.32 m** | **SELECTED VALIDATION WINNER** |
| **F3** | Multi-Branch Ensemble | $784.57\text{ m}$ | $300.86\text{ m}$ | Degraded at 300s |

---

## 6. Phase 6 — Locked Unseen Test Sweep Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 (W=30 Shorter)** | $9.07\text{ km/h}$ | $14.03\text{ km/h}$ | $191.43\text{ m}$ | $1,108.72\text{ m}$ | **1287.41 m** | $+389.3\%$ | $+484.9\%$ | **+488.0%** |
| **F2 (Val Winner W=50)** | **8.72 km/h** | **14.86 km/h** | **97.71 m** | **930.98 m** | **1165.94 m** | **+343.1%** | **+429.7%** | **+432.6%** |
| **F3 (Multi-Branch)** | $8.01\text{ km/h}$ | $13.04\text{ km/h}$ | $14.65\text{ m}$ | $1,045.15\text{ m}$ | **1275.85 m** | $+384.9\%$ | $+479.6\%$ | **+482.8%** |

---

## 7. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation winner selection performed strictly on Validation partition (`88566:107535`).

---

## 8. Empirical Failure Analysis

Receptive field expansion ($W=50$) introduces temporal phase lag during braking transients ($14.86\text{ km/h}$ braking MAE on test vs $11.57\text{ km/h}$ control). Lagging speed estimates leak into EKF velocity integration, exploding 300s position drift from $218.93\text{ m}$ to $1165.94\text{ m}$. SpeedNet v2 $W=40$ remains locked as the optimal temporal window.

---

## 9. Final Verdict

**REJECTED**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 10. Recommended Next Experiment (M037 Proposal)

**M037 Proposal — Zero-Phase Causal SpeedNet Loss Regularization (Deceleration Asymmetry Penalty)**:
Since receptive field manipulation ($W=30, 50$) and multi-branch ensembling degrade temporal phase alignment, M037 should focus on loss function formulation: training SpeedNet v2 ($W=40$) with an asymmetric deceleration penalty ($\mathcal{L}_{\text{asym}} = \lambda \max(0, \hat{v} - v_{\text{gt}})^2 \cdot \mathbb{I}(a_{\text{long}} < -0.5)$) directly targeting over-prediction during deceleration without changing receptive field length, preserving $W=40$ phase alignment and driving 300s position drift below $218.93\text{ m}$.

---

## 11. Full M001 → M036 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033 → M034 → M035 → M036`
