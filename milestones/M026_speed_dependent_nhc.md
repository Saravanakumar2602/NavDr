# Milestone M026 — Conservative Speed-Dependent NHC Covariance Ablation

## 1. Executive Summary

- **Milestone:** M026 — Conservative Speed-Dependent NHC Covariance Ablation
- **Objective:** Evaluate whether a speed-dependent relaxation of lateral velocity measurement covariance ($R_{\text{nhc}}(v) = R_0 (1 + \gamma v^2)$) can account for vehicle chassis dynamics at higher speeds without introducing unconstrained lateral position drift.
- **Verdict:** **REJECTED**.
- **Key Findings:** Speed-dependent NHC covariance inflation weakens lateral velocity anchoring, causing heading errors to rapidly accumulate into unconstrained cross-track position drift (+422.0% error explosion on test set, $220.12 \rightarrow 1149.07\text{ m}$). All relaxed candidates failed validation selection ($722.66 - 1008.35\text{ m}$ vs Control $505.40\text{ m}$). The Validation-Selected Winner (F5) is the original M019 Fixed NHC Control. Active benchmark remains **`220.12 m` @ 300s**.

---

## 2. Research Question

Is the fixed NHC lateral-velocity covariance ($R_0 = 0.04\text{ m}^2/\text{s}^2$) too restrictive at higher vehicle speeds, and can a small speed-dependent increase in NHC measurement covariance reduce measurement mismatch without allowing significant lateral drift?

---

## 3. Core Hypothesis

At higher vehicle speeds ($v > 15\text{ m/s}$), small unmodeled lateral motion or chassis suspension dynamics may make an extremely tight NHC measurement ($v_{\text{lateral}} \approx 0$) less accurate. A small speed-dependent scaling of measurement covariance ($R_{\text{nhc}}(v) = R_0(1 + \gamma v^2)$) might reduce EKF measurement innovation contradiction.

---

## 4. Why M026 Follows M025

Milestones M021–M025 (turn speed attenuation, APM window expansion, ZUPT transition gating, APM bound scaling, pitch compensation) were all cleanly rejected. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the active benchmark ($220.12\text{ m}$). M026 investigates whether a conservative relaxation of Non-Holonomic Constraints during high-speed cruising can improve overall 300s position drift.

---

## 5. Starting Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{ m @ 300s}}$$

---

## 6. Exact NHC Implementation Audit

- **Measurement Equation:** $y_{\text{nhc}} = 0.0 - v_{\text{lat}}$, where $v_{\text{lat}} = -v_x \cos(\psi_c) + v_y \sin(\psi_c)$.
- **Fixed Covariance:** $R_0 = 0.20^2 = 0.04\text{ m}^2/\text{s}^2$.
- **Speed Variable:** Causal EKF state speed $v_{\text{est}} = \sqrt{v_x^2 + v_y^2}$ (in $\text{m/s}$).

---

## 7. Candidate Configurations

- **F0 (Control M019):** Fixed NHC $R_{\text{nhc}} = R_0 = 0.04\text{ m}^2/\text{s}^2$ ($\gamma = 0.0$).
- **F1:** Speed-Dependent NHC with $\gamma = 0.005$ ($\text{s}^2/\text{m}^2$).
- **F2:** Speed-Dependent NHC with $\gamma = 0.010$ ($\text{s}^2/\text{m}^2$).
- **F3:** Speed-Dependent NHC with $\gamma = 0.020$ ($\text{s}^2/\text{m}^2$).
- **F4:** Speed-Dependent NHC with $\gamma = 0.050$ ($\text{s}^2/\text{m}^2$).
- **F5 (Best Validated + M019):** Selected winner from Validation set evaluation (`88566:107535`).

---

## 8. Covariance Formulation & Safety Cap

$$R_{\text{nhc}}(v_{\text{est}}) = \min\left(R_0 \cdot \left(1 + \gamma \cdot v_{\text{est}}^2\right), 5.0 R_0\right)$$
Safety cap $R_{\max} = 5.0 R_0 = 0.20\text{ m}^2/\text{s}^2$ defined before evaluation.

---

## 9. Dataset and Partition Provenance

- Train: `0:88566` (70%)
- Validation: `88566:107535` (15%)
- Unseen Test: `108000:111000` (300s outage, locked start `108,000`).

---

## 10. Validation Methodology

Validation winner selected strictly on Validation partition (`88566:107535`). F0 Control won validation with $505.40\text{ m}$ position error.

---

## 11. Test Methodology

Evaluated exactly once on locked unseen test partition (`start_idx = 108,000`).

---

## 12. Complete Candidate Results

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control gamma=0.0)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $31.06\text{ m}$ | $537.58\text{ m}$ | $1149.07\text{ m}^*$ | $+336.7\%$ | $+352.2\%$ | $+422.0\%$ |
| **F2** | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $33.12\text{ m}$ | $570.68\text{ m}$ | $1039.05\text{ m}^*$ | $+294.9\%$ | $+308.9\%$ | $+372.0\%$ |
| **F3** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $38.10\text{ m}$ | $579.96\text{ m}$ | $847.77\text{ m}^*$ | $+222.2\%$ | $+233.6\%$ | $+285.1\%$ |
| **F4** | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $36.37\text{ m}$ | $558.03\text{ m}$ | $770.61\text{ m}^*$ | $+192.9\%$ | $+203.3\%$ | $+250.1\%$ |
| **F5 (Val Winner)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

---

## 13. NHC Innovation Diagnostics

- **Mean Innovation Magnitude $|y_{\text{nhc}}|$:** F0 Control ($0.2631\text{ m/s}$), F1 ($0.3070\text{ m/s}$), F4 ($0.4088\text{ m/s}$). Relaxing $R_{\text{nhc}}$ increased lateral velocity residuals by $+55.4\%$.

---

## 14. Lateral Velocity & 15. Along/Cross-Track Diagnostics

- **Final Along-Track Error:** F0 Control ($-181.76\text{ m}$), F1 ($-440.67\text{ m}$).
- **Final Cross-Track Error:** F0 Control ($124.23\text{ m}$), F1 (**$1061.27\text{ m}$**). Cross-track lateral drift exploded by $+754\%$.

---

## 16. Endpoint-vs-Trajectory Analysis

All relaxed candidates severely degraded mean position error, final position error, 60s outage error, and 120s outage error. No false endpoint cancellation occurred; drift was uniformly catastrophic.

---

## 17. Failure / Success Mechanism

Tight NHC ($R_0 = 0.04\text{ m}^2/\text{s}^2$) is the sole physical mechanism preventing lateral velocity integration drift in 2D DR. Speed-dependent covariance inflation weakens lateral velocity innovation updates, allowing cross-track position error to explode from $124.23\text{ m}$ up to **$1061.27\text{ m}$**. F0 Control is the clear validation winner.

---

## 18. Causality / Leakage Audit

All calculations were performed causally using EKF state speed $v_{\text{est}}$. Zero future sample leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 19. Acceptance / Rejection Verdict

**REJECTED**.

---

## 20. Exact Research Artifacts Created

- **Script Path:** [`scripts/vw4_m026_speed_dependent_nhc.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m026_speed_dependent_nhc.py)
- **Summary JSON:** `results/vw4_m026_speed_dependent_nhc_summary.json`
- **Predictions NPZ:** `results/vw4_m026_speed_dependent_nhc_predictions.npz`
- **Report Markdown:** [`results/vw4_m026_speed_dependent_nhc_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m026_speed_dependent_nhc_report.md)
- **Plot Directory:** `plots/vw4/m026_speed_dependent_nhc/`

---

## 21. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 22. Next Research Decision (M027 Proposal)

**M027 Proposal — Causal Speed-Trend Deceleration Gating for Dynamic APM Activation**:
Milestones M021–M026 have conclusively disproved altering turn speed, expanding integration windows, changing ZUPT triggers, scaling 1D bounds, pitch compensation, and relaxing NHC. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the undisputed champion. M027 should investigate a Causal Speed-Trend Gating mechanism ($\frac{d v_{\text{speednet}}}{dt} < -0.3\text{ m/s}^2$) that activates APM speed damping ONLY when both IMU acceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$) and SpeedNet predicted speed trend confirm genuine deceleration, preventing false APM updates during steady cruise transients and lowering 300s position drift below $220.12\text{ m}$.

---

## 23. Full M001 → M026 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026`
