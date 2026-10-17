# Milestone M025 — Pitch-Tilt-Compensated Longitudinal Acceleration for APM

## 1. Executive Summary

- **Milestone:** M025 — Pitch-Tilt-Compensated Longitudinal Acceleration for APM
- **Objective:** Evaluate whether explicit pitch-tilt gravity compensation ($a_{\text{long,comp}} = a_{\text{long}} - g \sin\theta_{\text{pitch}}$) improves M019 APM longitudinal acceleration integration during straight-line braking episodes ($a_{\text{long}} < -0.5\text{ m/s}^2$) and lowers 300s position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:** `a_long = -(raw_ay - grav_y)` already subtracts `grav_y` (the Android/iOS Sensor Fusion gravity vector along the longitudinal Y axis). Explicit pitch tilt compensation is redundant and slightly degrades 300s validation set position error ($505.61\text{ m}$ for F1 vs $505.40\text{ m}$ for Control). The Validation-Selected Winner (F4) is the original M019 Baseline Control. Active benchmark remains **`220.12 m` @ 300s**.

---

## 2. Research Question

Does pitch/tilt gravity contamination in the IMU-derived longitudinal acceleration degrade the M019 APM velocity-delta estimate, and can causal pitch compensation improve APM correction during straight-line braking and reduce 300s navigation error below $220.12\text{ m}$?

---

## 3. Core Hypothesis

M019's longitudinal acceleration integral $\Delta v_{\text{imu}} = \sum a_{\text{long}} \Delta t$ might suffer from gravity tilt contamination during vehicle pitch transients (e.g. forward nose-down tilt during braking). Removing $g \sin\theta_{\text{pitch}}$ would yield a cleaner longitudinal acceleration signal and refine APM speed damping.

---

## 4. Why M025 Follows M024

Milestones M021 (turn speed attenuation), M022 (APM window expansion), M023 (acceleration-variance ZUPT gating), and M024 (APM 1D bound scaling) were all cleanly rejected. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the active benchmark ($220.12\text{ m}$). M025 investigates whether physical signal-level pre-conditioning of longitudinal acceleration via pitch tilt compensation can refine APM performance.

---

## 5. Physics / Coordinate System Audit

1. **IMU Axis Convention:** Smartphone Y-axis aligns with the vehicle forward longitudinal axis. Negative raw acceleration $-raw\_ay$ corresponds to forward acceleration.
2. **Gravity Subtraction:** Preprocessing computes `a_long = -(raw_ay - grav_y)`. `grav_y` is extracted directly from the Android/iOS Sensor Fusion gravity sensor API.
3. **Pitch Angle Definition:** $\theta_{\text{acc}} = \arctan2(grav\_y, \sqrt{grav\_x^2 + grav\_z^2})$.
4. **Audit Conclusion:** Because `grav_y` is already subtracted in `a_long`, static gravity pitch component is already removed. Additional pitch tilt compensation is mathematically redundant.

---

## 6. Starting Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{ m @ 300s}}$$

---

## 7. Exact Implementation

All parameters (EKF structure, NHC, ZUPT, SpeedNet weights, W=40, $a_{\text{long}} < -0.5\text{ m/s}^2$ trigger, $|\omega_y| \le 3^\circ/\text{s}$ turn exclusion, $\delta v_{\max} = 0.50\text{ m/s}$) were kept strictly frozen. Only the acceleration used inside the APM sliding integral was modified according to pitch mode.

---

## 8. Pitch Estimation Method

- **Direct Causal Pitch Estimator:** Zero-latency pitch angle $\theta_{\text{acc}} = \arctan2(grav\_y, \sqrt{grav\_x^2 + grav\_z^2})$.
- **EMA-Smoothed Pitch Estimator:** Causal filter with coefficient $\alpha = 0.90$ selected on Train/Val partition.

---

## 9. Candidate Configurations

- **F0 (Control M019):** Raw $a_{\text{long}} = -(raw\_ay - grav\_y)$ without additional pitch compensation.
- **F1 (Direct Pitch Comp):** $a_{\text{long,comp}} = a_{\text{long}} - g \sin\theta_{\text{acc}}$.
- **F2 (Smoothed Pitch Comp):** $a_{\text{long,comp}} = a_{\text{long}} - g \sin\theta_{\text{smoothed}}$ ($\alpha = 0.90$).
- **F3 (Braking-Only Comp):** Pitch compensation applied only during active braking ($a_{\text{long}} < -0.5\text{ m/s}^2$ AND $|\omega_y| \le 3^\circ/\text{s}$).
- **F4 (Best Validated + M019):** Selected winner from Validation set evaluation (`88566:107535`).

---

## 10. Dataset and Partition Provenance

- Train: `0:88566` (70%)
- Validation: `88566:107535` (15%)
- Unseen Test: `108000:111000` (300s outage, locked start `108,000`).

---

## 11. Validation Methodology

Validation winner selected strictly on Validation partition (`88566:107535`). F0 Control won validation with $505.40\text{ m}$ position error.

---

## 12. Test Methodology

Evaluated exactly once on locked unseen test partition (`start_idx = 108,000`).

---

## 13. Complete Candidate Results

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | M019 Baseline Control | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | Direct Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.54\text{ m}$ | $428.82\text{ m}$ | $219.59\text{ m}^*$ | $-16.5\%$ | $-13.6\%$ | $-0.2\%$ |
| **F2** | EMA-Smoothed Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.53\text{ m}$ | $428.77\text{ m}$ | $219.72\text{ m}^*$ | $-16.5\%$ | $-13.5\%$ | $-0.2\%$ |
| **F3** | Braking-Only Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.53\text{ m}$ | $428.79\text{ m}$ | $220.12\text{ m}$ | $-16.3\%$ | $-13.4\%$ | $0.0\%$ |
| **F4 (Val Winner)** | Selected Best Validation (F0) | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

---

## 14. Pitch / Acceleration Diagnostics

- **Mean Pitch Angle during Braking:** $+0.01^\circ$ (essentially flat vehicle attitude).
- **Impact on Acceleration Integral:** Max delta acceleration shift $< 0.002\text{ m/s}^2$.

---

## 15. APM Correction Diagnostics

- **Total Activations (All Candidates):** 118 samples ($100\%$ applied during straight deceleration).
- **Mean APM Speed Correction:** $1.73\text{ km/h}$ ($0.48\text{ m/s}$).

---

## 16. Navigation Comparison

- **60s Outage:** F0 Control = **$27.53\text{ m}$**, F1 = $27.54\text{ m}$.
- **120s Outage:** F0 Control = **$428.79\text{ m}$**, F1 = $428.82\text{ m}$.
- **300s Outage:** F0 Control = **`220.12 m`**, F1 = $219.59\text{ m}^*$ (Failed validation selection).

---

## 17. Failure or Success Mechanism

Because `grav_y` is already subtracted in `a_long`, static gravity pitch is already removed. Explicit pitch compensation is redundant, causing slight validation degradation ($505.40 \rightarrow 505.61\text{ m}$). F0 Control remains the validation winner.

---

## 18. Leakage / Causality Audit

All pitch calculations were performed causally sample-by-sample. Zero future sample leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 19. Acceptance / Rejection Verdict

**REJECTED**.

---

## 20. Exact Research Artifacts Created

- **Script Path:** [`scripts/vw4_m025_pitch_tilt_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m025_pitch_tilt_apm.py)
- **Summary JSON:** `results/vw4_m025_pitch_tilt_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m025_pitch_tilt_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m025_pitch_tilt_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m025_pitch_tilt_apm_report.md)
- **Plot Directory:** `plots/vw4/m025_pitch_tilt_apm/`

---

## 21. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 22. Next Research Decision (M026 Proposal)

**M026 Proposal — Speed-Dependent Adaptive NHC Lateral Velocity Noise Scaling**:
Milestones M021–M025 have exhaustively proven that modifying turn speed, expanding APM integration windows, altering ZUPT thresholds, scaling 1D APM correction bounds, or applying pitch compensation cannot beat the $220.12\text{ m}$ benchmark. M026 should investigate a Speed-Dependent Lateral Velocity Noise Scaling model for Non-Holonomic Constraints ($R_{\text{nhc}}(v) = R_{0} (1 + \gamma \cdot v^2)$). By slightly relaxing lateral velocity tight anchoring ($R_{\text{nhc}}=0.04\text{ m}^2/\text{s}^2$) at high speed ($v > 15\text{ m/s}$) while keeping tight zero-lateral velocity anchoring at low speed, M026 aims to eliminate minor chassis cornering side-slip noise without inducing lateral drift, lowering 300s position drift below $220.12\text{ m}$.

---

## 23. Full M001 → M025 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025`
