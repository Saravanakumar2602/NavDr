# Milestone M037 — Asymmetric Deceleration Loss Ablation

## 1. Executive Summary

- **Milestone:** M037 — Asymmetric Deceleration Loss Ablation
- **Objective:** Evaluate whether adding an asymmetric deceleration over-prediction penalty ($\mathcal{L}_{\text{asym}} = \lambda \max(0, \hat{v} - v_{\text{gt}})^2 \cdot \mathbb{I}(a_{\text{long}} < -0.5)$) to SpeedNet v2 ($W=40$) training reduces speed overestimation during braking without distorting speed predictions or degrading 300s position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** Candidate F2 ($\lambda=0.003$) achieved the lowest validation 300s error ($316.98\text{ m}$ vs Control $494.83\text{ m}$) due to artificial zero-speed collapse.
  - **Locked Test Result:** Evaluated on the locked unseen test set (`start_idx = 108,000`), validation winner F2 ($\lambda=0.003$) exploded 300s position drift to **`818.48 m`** (**+273.9% degradation** vs Control `218.93 m`) and degraded 120s error to $809.63\text{ m}$.
  - **Failure Mechanism:** Soft loss penalties force neural speed models into uncalibrated speed regimes that collapse on unseen data (reconfirming M012 findings). Post-inference physical constraints (M013 F4) remain superior to loss-based constraints.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## 2. Objective & Research Question

"Can we reduce SpeedNet's persistent positive speed overestimation during deceleration/braking by modifying ONLY the training loss, while preserving the $W=40$ temporal alignment and improving integrated dead-reckoning?"

---

## 3. Exact Baseline Configuration

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Candidate Loss Equation & Setup

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{speed}} + 0.5 \mathcal{L}_{\text{yaw}} + 0.5 \mathcal{L}_{\text{stat}} + 0.2 \mathcal{L}_{\Delta v} + \lambda \cdot \text{mean}\left(\max(0, \hat{v} - v_{\text{gt}})^2 \cdot \mathbb{I}(a_{\text{long}} < -0.5\text{ m/s}^2)\right)$$

- Candidate F0: $\lambda = 0.000$ (Control Baseline)
- Candidate F1: $\lambda = 0.001$
- Candidate F2: $\lambda = 0.003$
- Candidate F3: $\lambda = 0.010$
- Candidate F4: $\lambda = 0.030$

---

## 5. Phase 4 — Pointwise Speed & Regime MAE Analysis (Validation Set `88566:107535`)

| Candidate ID | Loss Hyperparameter ($\lambda$) | Overall Speed MAE | Braking Speed MAE | Braking Speed Bias | Accel Speed MAE | Turn Speed MAE |
|---|---|---|---|---|---|---|
| **F0 (Control)** | **$\lambda = 0.000$ (Control Baseline)** | **12.38 km/h** | **13.63 km/h** | **+0.52 km/h** | **12.25 km/h** | **13.31 km/h** |
| **F1** | $\lambda = 0.001$ | $14.00\text{ km/h}$ | $15.53\text{ km/h}$ | $+4.62\text{ km/h}$ | $13.63\text{ km/h}$ | $15.21\text{ km/h}$ |
| **F2** | $\lambda = 0.003$ | $47.29\text{ km/h}$ | $52.43\text{ km/h}$ | $-52.43\text{ km/h}$ | $46.67\text{ km/h}$ | $53.11\text{ km/h}$ |
| **F3** | $\lambda = 0.010$ | $12.51\text{ km/h}$ | $13.82\text{ km/h}$ | $+1.07\text{ km/h}$ | $12.29\text{ km/h}$ | $13.36\text{ km/h}$ |
| **F4** | $\lambda = 0.030$ | $13.18\text{ km/h}$ | $14.37\text{ km/h}$ | $+5.55\text{ km/h}$ | $13.13\text{ km/h}$ | $14.13\text{ km/h}$ |

---

## 6. Phase 5 — Validation Navigation Evaluation (`88566:107535`)

| Candidate ID | Loss Hyperparameter ($\lambda$) | Val 300s Position Error (m) | Val Mean Position Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 (Control)** | $\lambda = 0.000$ (Control Baseline) | $494.83\text{ m}$ | $356.99\text{ m}$ | Baseline |
| **F1** | $\lambda = 0.001$ | $1,050.28\text{ m}$ | $438.63\text{ m}$ | Degraded |
| **F2** | **$\lambda = 0.003$** | **316.98 m** | **259.27 m** | **SELECTED VALIDATION WINNER** |
| **F3** | $\lambda = 0.010$ | $1,146.17\text{ m}$ | $332.48\text{ m}$ | Degraded |
| **F4** | $\lambda = 0.030$ | $777.32\text{ m}$ | $413.05\text{ m}$ | Degraded |

---

## 7. Phase 6 — Locked Unseen Test Sweep Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($\lambda = 0.001$)** | $8.77\text{ km/h}$ | $13.80\text{ km/h}$ | $123.97\text{ m}$ | $735.75\text{ m}$ | **519.24 m** | $+97.3\%$ | $+135.9\%$ | **+137.2%** |
| **F2 (Val Winner $\lambda=0.003$)** | **16.53 km/h** | **26.81 km/h** | **383.52 m** | **809.63 m** | **818.48 m** | **+211.1%** | **+271.8%** | **+273.9%** |
| **F3 ($\lambda = 0.010$)** | $7.36\text{ km/h}$ | $11.90\text{ km/h}$ | $14.31\text{ m}$ | $880.40\text{ m}$ | **1289.82 m** | $+390.2\%$ | $+486.0\%$ | **+489.1%** |
| **F4 ($\lambda = 0.030$)** | $10.26\text{ km/h}$ | $16.21\text{ km/h}$ | $100.91\text{ m}$ | $909.20\text{ m}$ | **976.05 m** | $+271.0\%$ | $+343.4\%$ | **+345.8%** |

---

## 8. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation winner selection performed strictly on Validation partition (`88566:107535`).

---

## 9. Failure Analysis & Lessons Learned

Soft loss penalties force neural speed models into uncalibrated speed regimes that collapse on unseen data (reconfirming M012 findings). Post-inference physical constraints (M013 F4) remain vastly superior to loss-based constraints because M013 operates AFTER inference with strict physical bounds without distorting neural backbone weights.

---

## 10. Final Verdict

**REJECTED (BRANCH PERMANENTLY CLOSED)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 11. Recommended Next Experiment (M038 Proposal)

**M038 Proposal — Dynamic Physical Inference Constraint Tightening (Transient APM Acceleration Bounds)**:
With neural loss modifications (M012, M037), receptive field alterations (M011, M017, M036), and post-inference EKF gating (M015, M016, M021, M026, M031, M032, M033, M034, M035) all disproved and permanently closed, M038 should focus on refining the post-inference physical layer: adapting M019 APM correction bound $\delta v_{\max}$ dynamically based on local longitudinal jerk magnitude, allowing stronger APM speed damping ($\delta v_{\max} = 0.75\text{ m/s}$) ONLY during extreme braking onset ($j_{\text{long}} < -2.00\text{ m/s}^3$), driving 300s position drift below $218.93\text{ m}$.

---

## 12. Full M001 → M037 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033 → M034 → M035 → M036 → M037`
