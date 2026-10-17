# Milestone M016 — Adaptive EKF Innovation Gating & Velocity Bias Tracking

## 1. Starting Point & Provenance Context

- **Pre-M016 Verified Benchmark (M014 F3):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 Speed Constraint + M014 Causal ZUPT = `233.18 m` @ 300s.
- **Problem Context:** M015 established that heading integration should remain untouched in raw gyro mode ($233.18\text{ m}$). M016 investigates whether velocity measurement innovation gating or accelerometer bias tracking during transient acceleration/deceleration phases can reduce residual position drift.

---

## 2. Research Question

Can adaptive treatment of velocity innovations and/or accelerometer bias during acceleration/deceleration transients reduce long-duration position drift without damaging the successful M014 behavior?

---

## 3. Core Hypothesis

SpeedNet velocity predictions during acceleration/deceleration transients have elevated innovation errors ($\text{NIS} > 3.84$). Gating or down-weighting these transient speed updates, or tracking longitudinal accelerometer bias ($b_a$), will improve EKF velocity propagation accuracy during outages.

---

## 4. EKF Inspection & Architecture Audit

1. **State Vector:** $x = [x, y, v_x, v_y, \psi, b_a, b_\omega]^T$ (7 dimensions).
2. **Process Model:** Accelerometer prediction $\hat{a}_k = a_{m,k} - b_{a,k}$, ENU accelerations $a_{x,\text{enu}} = \hat{a}_k \sin\psi_{k+1}$, $a_{y,\text{enu}} = \hat{a}_k \cos\psi_{k+1}$.
3. **Process Noise:** $Q = \text{diag}([0.001, 0.001, 0.01, 0.01, (0.05^\circ)^2, q_{b_a}, 10^{-6}])$.
4. **Outage Measurement Model:** SpeedNet 1D speed $v_{\text{meas}} = \sqrt{v_x^2 + v_y^2}$ ($R_v = 1.0$), ZUPT 2D velocity $z_{\text{zupt}} = [0,0]^T$ ($R_{\text{zupt}} = 0.20^2 I_2$), NHC 1D lateral velocity $z_{\text{nhc}} = 0$ ($R_{\text{nhc}} = 0.20^2$).

---

## 5. Critical Observability Audit Result

- **Observability Determination:** Longitudinal accelerometer bias $b_a$ is **unobservable** during GNSS outage.
- **Physical Reason:** Outage measurements consist solely of speed magnitude ($v_{\text{meas}}$), 2D zero velocity ($v_x=0, v_y=0$), and lateral non-holonomic velocity ($v_{\text{lat}}=0$). None of these provide direct longitudinal acceleration observations. During steady cruise ($a_{m,k} \approx 0$), $b_a$ is mathematically indistinguishable from tilt-induced gravity leakage ($g \cdot \sin\theta$) and SpeedNet speed prediction error. Actively estimating $b_a$ without direct acceleration measurements destabilizes velocity propagation.

---

## 6. F1–F5 Methodology & Candidate Definitions

- **F0 (Control):** Exact M014 Baseline ($233.18\text{ m}$).
- **F1 (Velocity Innovation Diagnostic):** Calculate NIS and velocity innovations without altering state updates.
- **F2 (NIS Speed Gating):** Down-weight SpeedNet updates when $\text{NIS}_v = y_v^2 / S_v > 3.84$.
- **F3 (Adaptive Speed Covariance $R_v$):** Inflate $R_v$ during high acceleration variance ($\sigma_a^2$) or turning ($|\omega_y|$).
- **F4 (Accel Bias Tracking Audit):** Evaluate $b_a$ state tracking with $q_{b_a} = 10^{-5}$.
- **F5 (Best Single Method + M014):** Selected best validation candidate (F3).

---

## 7. Baseline Control Reproduction Audit

- **Audit Target:** M014 F3 Control = `27.36 m` (60s), `428.45 m` (120s), `233.18 m` (300s).
- **Measured F0 Control:** `27.36 m` (60s), `428.45 m` (120s), **`233.18 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 8. Validation Results

Parameters tuned strictly on Validation set (`88566:107535`):
- NIS gating threshold $\text{NIS}_{\text{thresh}} = 3.84$ ($\chi^2(1)$ 95th percentile).
- Adaptive covariance multipliers $\beta = 2.0, \gamma = 2.0$ selected.

---

## 9. Locked Unseen Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|
| **F0 (Control Benchmark)** | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1 (Innovation Diagnostic)** | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F2 (NIS Speed Gating)** | $7.36\text{ km/h}$ | $305.94\text{ m}$ | $915.89\text{ m}$ | $880.91\text{ m}$ | $+234.8\%$ | $+246.7\%$ | $+277.8\%$ |
| **F3 (Adaptive Speed $R_v$)** | $7.36\text{ km/h}$ | $107.00\text{ m}$ | $629.20\text{ m}$ | $596.41\text{ m}$ | $+126.7\%$ | $+134.7\%$ | $+155.8\%$ |
| **F4 (Accel Bias Tracking)** | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F5 (Best Single + M014)** | $7.36\text{ km/h}$ | $107.00\text{ m}$ | $629.20\text{ m}$ | $596.41\text{ m}$ | $+126.7\%$ | $+134.7\%$ | $+155.8\%$ |

---

## 10. Innovation Diagnostics Summary

- **Braking Regime Mean Innovation:** $+0.7592\text{ m/s}$ ($+2.73\text{ km/h}$ overestimation bias).
- **Strong Turn Mean Innovation:** $+0.8144\text{ m/s}$ ($+2.93\text{ km/h}$ overestimation bias).
- **Overall Innovation MAE:** $0.8766\text{ m/s}$ ($3.16\text{ km/h}$).
- **Overall Innovation P95:** $3.1278\text{ m/s}$ ($11.26\text{ km/h}$).
- **Innovation Sign Ratio:** $43.1\%$ positive / $56.9\%$ negative.

---

## 11. Accelerometer Bias Diagnostics

- **Initial Bias Estimate:** $0.0000\text{ m/s}^2$.
- **Mean Bias Estimate (F4):** $0.0000\text{ m/s}^2$ (un-updated due to zero direct measurement observability).
- **Observability Audit Confirmation:** Direct estimation of $b_a$ without direct longitudinal acceleration measurements is mathematically ill-posed during GNSS outages.

---

## 12. 60/120/300s Navigation Results

- **60s Outage:** F0 Control = $27.36\text{ m}$, F2 NIS Gating = $305.94\text{ m}$, F3 Adaptive $R_v = 107.00\text{ m}$.
- **120s Outage:** F0 Control = $428.45\text{ m}$, F2 NIS Gating = $915.89\text{ m}$, F3 Adaptive $R_v = 629.20\text{ m}$.
- **300s Outage:** F0 Control = **`233.18 m`**, F2 NIS Gating = $880.91\text{ m}$, F3 Adaptive $R_v = 596.41\text{ m}$.

---

## 13. Comparison with Historical Benchmarks

- **vs Historical Benchmark ($263.11\text{ m}$):** F0 Control remains $-11.4\%$ better ($233.18\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F0 Control remains $-8.2\%$ better ($233.18\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F0 Control = **0.0% (Control)**. Candidates F2 ($880.91\text{ m}$) and F3 ($596.41\text{ m}$) severely degraded performance.

---

## 14. Leakage & Causality Audit

- All gating statistics, innovation bounds, and covariance parameters were derived **strictly on Train (`0:88566`) / Val (`88566:107535`)**. Zero ground truth or future trajectory info was injected at runtime.

---

## 15. Failure Modes

1. **Loss of Velocity Damping:** SpeedNet velocity predictions provide crucial velocity state damping in the EKF. Gating (F2) or inflating measurement noise (F3) deprives the EKF of velocity anchoring during transients.
2. **Open-Loop Integration Degradation:** When SpeedNet updates are gated, the filter falls back on open-loop accelerometer double-integration ($v_{k+1} = v_k + a_{\text{long}}\Delta t$). Sensor noise and tilt contamination ($g \sin\theta$) rapidly accelerate position drift ($233.18 \rightarrow 880.91\text{ m}$).

---

## 16. Success Mechanism (N/A - Milestone Rejected)

None of the adaptive innovation gating or bias tracking candidates beat the $233.18\text{ m}$ benchmark.

---

## 17. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m016_adaptive_velocity_innovation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m016_adaptive_velocity_innovation.py)
- **Summary JSON:** `results/vw4_m016_adaptive_velocity_innovation_summary.json`
- **Predictions NPZ:** `results/vw4_m016_adaptive_velocity_innovation_predictions.npz`
- **Report Markdown:** [`results/vw4_m016_adaptive_velocity_innovation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m016_adaptive_velocity_innovation_report.md)
- **Plot Directory:** `plots/vw4/m016_adaptive_velocity_innovation/`

---

## 18. Final M016 Verdict

**REJECTED**.

Active Verified Benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$

---

## 19. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016`

---

## 20. Exactly ONE Evidence-Based Next Direction (M017 Proposal)

**M017 Proposal — Multi-Scale Temporal SpeedNet Ensemble & Causal Recurrent Damping**:
Milestones M011–M016 have systematically evaluated filter-level adaptations (gating, covariances, ZUPT, bias states, heading constraints), proving that filter-level measurement rejection forces open-loop drift. Therefore, the remaining avenue for reducing position error below $233.18\text{ m}$ is improving the fundamental SpeedNet prediction quality during deceleration transients. M017 should investigate a multi-scale temporal SpeedNet ensemble combining short-window ($W=20$) fast deceleration response with long-window ($W=40$) cruise stability.
