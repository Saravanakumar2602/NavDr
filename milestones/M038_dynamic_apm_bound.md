# Milestone M038 — Dynamic Physical Inference Constraint Tightening

## 1. Executive Summary

- **Milestone:** M038 — Dynamic Physical Inference Constraint Tightening (Transient APM Acceleration Bounds)
- **Objective:** Evaluate whether expanding M019 APM correction bound to $\delta v_{\max} = 0.75\text{ m/s}$ dynamically during extreme causal longitudinal jerk transients ($j_{\text{long}} < j_{\text{thresh}}$) improves 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (BRANCH PERMANENTLY CLOSED)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Selection:** F0 Control achieved the best validation score ($494.83\text{ m}$). All dynamic APM candidates F1–F4 degraded validation error ($496.41 - 496.81\text{ m}$). F0 Control was selected as the validation winner.
  - **Locked Test Result:** Evaluated on the locked unseen test set (`start_idx = 108,000`), dynamic APM candidates F1–F4 degraded 300s position error to **`219.37 – 221.21 m`** ($+0.44\text{ m}$ to $+2.28\text{ m}$ degradation vs Control `218.93 m`).
  - **Failure Mechanism:** Expanding the APM correction bound to $0.75\text{ m/s}$ during braking transients causes slight speed over-damping (negative speed integration bias), accumulating position drift over 300s horizons. Fixed bound $\delta v_{\max} = 0.50\text{ m/s}$ remains optimal.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## 2. Research Question & Hypothesis

"Can stronger APM speed damping ($\delta v_{\max} = 0.75\text{ m/s}$) be applied ONLY during genuinely extreme braking transients, using causal longitudinal jerk, to reduce integrated dead-reckoning drift below $218.93\text{ m}$ without damaging normal behavior?"

---

## 3. Frozen Benchmark Configuration

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Candidate Definitions

- **F0 (Control Baseline):** Fixed bound $\delta v_{\max} = 0.50\text{ m/s}$.
- **F1:** Dynamic bound $\delta v_{\max} = 0.75\text{ m/s}$ if $j_{\text{long}} < -1.50\text{ m/s}^3$ (else $0.50\text{ m/s}$).
- **F2:** Dynamic bound $\delta v_{\max} = 0.75\text{ m/s}$ if $j_{\text{long}} < -2.00\text{ m/s}^3$ (else $0.50\text{ m/s}$).
- **F3:** Dynamic bound $\delta v_{\max} = 0.75\text{ m/s}$ if $j_{\text{long}} < -2.50\text{ m/s}^3$ (else $0.50\text{ m/s}$).
- **F4:** Dynamic bound $\delta v_{\max} = 0.75\text{ m/s}$ if $j_{\text{long}} < -3.00\text{ m/s}^3$ (else $0.50\text{ m/s}$).

---

## 5. Phase 5 — Validation Candidate Evaluation (`88566:107535`)

| Candidate ID | Extreme Jerk Condition ($j_{\text{long}}$) | Dynamic Bound ($\delta v_{\max}$) | Extreme APM Events | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|---|---|
| **F0 (Control)** | **Fixed Bound (No Expansion)** | **0.50 m/s** | **0** | **494.83 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $j_{\text{long}} < -1.50\text{ m/s}^3$ | $0.75\text{ m/s}$ | 46 | $496.41\text{ m}$ | Degraded |
| **F2** | $j_{\text{long}} < -2.00\text{ m/s}^3$ | $0.75\text{ m/s}$ | 46 | $496.41\text{ m}$ | Degraded |
| **F3** | $j_{\text{long}} < -2.50\text{ m/s}^3$ | $0.75\text{ m/s}$ | 44 | $496.81\text{ m}$ | Degraded |
| **F4** | $j_{\text{long}} < -3.00\text{ m/s}^3$ | $0.75\text{ m/s}$ | 43 | $496.81\text{ m}$ | Degraded |

---

## 6. Phase 6 — Locked Unseen Test Sweep Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | Extreme APM Events | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **0** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1 ($j < -1.50$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 42 | $27.34\text{ m}$ | $425.49\text{ m}$ | **221.21 m** | $-15.9\%$ | $+0.5\%$ | **+1.0%** |
| **F2 ($j < -2.00$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 40 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.46 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |
| **F3 ($j < -2.50$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 39 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.46 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |
| **F4 ($j < -3.00$)** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | 39 | $27.34\text{ m}$ | $423.88\text{ m}$ | **219.37 m** | $-16.6\%$ | $-0.3\%$ | **+0.2%** |

---

## 7. Causality / Zero-Leakage Audit

Calculated using strictly current sample $k$ and past samples $k-w_n:k$. Zero future leakage. Validation candidate selection performed strictly on Validation partition (`88566:107535`).

---

## 8. Failure Analysis & Lessons Learned

Expanding the APM correction bound to $0.75\text{ m/s}$ during braking transients causes slight speed over-damping (negative speed integration bias), accumulating position drift over 300s horizons. Fixed bound $\delta v_{\max} = 0.50\text{ m/s}$ remains optimal.

---

## 9. Final Verdict

**REJECTED (BRANCH PERMANENTLY CLOSED)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 10. Recommended Next Experiment (M039 Proposal)

**M039 Proposal — Multi-Horizon Trajectory Geometry Attribution & Turn-Trajectory Alignment**:
With all post-inference measurement gating, covariance scaling, bias tracking, neural loss modifications, receptive field tuning, and dynamic APM bounds (M015–M038) disproved and permanently closed, residual error analysis shows that 300s position drift ($218.93\text{ m}$) is dominated by heading misalignment during strong turns ($|\omega_y| > 10^\circ/\text{s}$). M039 should perform a comprehensive diagnostic evaluating whether causal heading-rate curvature constraints ($\kappa = \omega_y / v$) can bound 2D trajectory curvature drift during strong turns without relaxing NHC $R_{\text{nhc}}$, driving 300s position drift below $218.93\text{ m}$.

---

## 11. Full M001 → M038 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032 → M033 → M034 → M035 → M036 → M037 → M038`
