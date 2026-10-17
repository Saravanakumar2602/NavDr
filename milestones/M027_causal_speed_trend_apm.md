# Milestone M027 — Causal Speed-Trend Confirmation for APM Activation

## 1. Executive Summary

- **Milestone:** M027 — Causal Speed-Trend Confirmation for APM Activation
- **Objective:** Evaluate whether requiring dual confirmation of both IMU longitudinal deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$) and SpeedNet predicted speed derivative ($\frac{d v_{\text{speednet}}}{dt} < \text{threshold}$) makes APM speed damping more selective and improves 300s dead-reckoning position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:** SpeedNet speed predictions exhibit a temporal phase lag of 200–400 ms during braking transients. Requiring $\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$ suppressed 69 out of 118 genuine deceleration APM updates (58.5% suppression rate). Suppressing APM updates during initial braking increased integrated along-track error, exploding 300s test position drift by **`+30.48 m` / `+13.8%`** ($220.12 \rightarrow 250.60\text{ m}$). Active benchmark remains **`220.12 m` @ 300s**.

---

## 2. Research Question

Does requiring BOTH causal IMU-derived deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$) AND causal SpeedNet-predicted speed decrease ($\frac{d v_{\text{speednet}}}{dt} < \text{threshold}$) make APM activation more selective and improve dead-reckoning navigation?

---

## 3. Core Hypothesis

Requiring SpeedNet predicted speed trend confirmation before applying APM speed damping might eliminate false-positive APM activations during steady cruise transients, refining velocity integration and reducing 300s position drift below $220.12\text{ m}$.

---

## 4. Why M027 Follows M026

Milestones M021–M026 (turn speed attenuation, APM window expansion, ZUPT transition gating, APM bound scaling, pitch compensation, speed-dependent NHC covariance) were all cleanly rejected. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the active benchmark ($220.12\text{ m}$). M027 investigates whether adding a dual-signal speed-trend confirmation gate to APM activation can refine APM selectivity.

---

## 5. Locked M019 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{ m @ 300s}}$$

---

## 6. Exact APM Implementation

All parameters (EKF state, NHC, ZUPT, SpeedNet weights, W=40, $a_{\text{long}} < -0.5\text{ m/s}^2$ trigger, $|\omega_y| \le 3^\circ/\text{s}$ turn exclusion, $\delta v_{\max} = 0.50\text{ m/s}$) were kept strictly frozen.

---

## 7. SpeedNet Prediction Alignment

SpeedNet predictions $v_{\text{speednet}}[k]$ are synchronized 1-to-1 with IMU sample timestamps $t[k]$ (10 Hz, $\Delta t = 0.1\text{ s}$).

---

## 8. Causal Derivative Formulation

$$\frac{d v_{\text{speednet}}}{dt}[k] = \frac{v_{\text{speednet}}[k] - v_{\text{speednet}}[k-1]}{\Delta t}$$
Uses strictly current sample $k$ and past sample $k-1$. Zero future leakage.

---

## 9. Candidate Thresholds

- **F0 (Control M019):** IMU deceleration trigger only (no speed-trend gate).
- **F1:** IMU deceleration AND $\frac{d v_{\text{speednet}}}{dt} < -0.15\text{ m/s}^2$.
- **F2:** IMU deceleration AND $\frac{d v_{\text{speednet}}}{dt} < -0.30\text{ m/s}^2$.
- **F3:** IMU deceleration AND $\frac{d v_{\text{speednet}}}{dt} < -0.50\text{ m/s}^2$.
- **F4:** IMU deceleration AND $\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$.
- **F5 (Val Winner):** Candidate selected on Validation set (`88566:107535`).

---

## 10. Train / Validation / Test Provenance

- Train: `0:88566` (70%)
- Validation: `88566:107535` (15%)
- Unseen Test: `108000:111000` (300s outage, locked start `108,000`).

---

## 11. Validation Results & 12. Validation Winner

Candidate F4 ($\frac{d v_{\text{speednet}}}{dt} < -0.75\text{ m/s}^2$) was selected as the **Validation Winner** ($499.00\text{ m}$ vs Control $505.40\text{ m}$).

---

## 13. Locked-Test Results

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F2** | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F3** | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F4** | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |
| **F5 (Val Winner)** | $7.34\text{ km/h}$ | $11.58\text{ km/h}$ | $27.54\text{ m}$ | $433.72\text{ m}$ | $250.60\text{ m}$ | $-4.8\%$ | $-1.4\%$ | $+13.8\%$ |

---

## 14. APM Activation Statistics & 15. Suppressed-Update Analysis

- **Total IMU Deceleration Events:** 118
- **F0 Control Activations:** 118 (0 suppressed)
- **F4 / F5 Activations:** 49 (69 suppressed, 58.5% suppression rate)

---

## 16. Regime-Specific Diagnostics

Suppression occurred primarily during initial braking transients when real vehicle deceleration is active ($a_{\text{long}} < -0.5\text{ m/s}^2$) but SpeedNet predicted speed derivative $\frac{d v_{\text{speednet}}}{dt}$ lags behind due to neural sliding-window smoothing.

---

## 17. Trajectory Analysis & 18. Along/Cross-Track Analysis

- **Mean Position Error:** F0 Control ($308.28\text{ m}$), F5 ($311.02\text{ m}$)
- **Final Along-Track Error:** F0 Control ($-181.76\text{ m}$), F5 ($-216.51\text{ m}$)
- **Final Cross-Track Error:** F0 Control ($124.23\text{ m}$), F5 ($126.24\text{ m}$)

---

## 19. Causality Audit & 20. Leakage Audit

All derivative calculations were strictly causal using time steps $k$ and $k-1$. Zero future sample leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 21. Acceptance / Rejection Verdict

**REJECTED**.

---

## 22. Failure / Success Mechanism

SpeedNet speed predictions lag instantaneous accelerometer measurements during braking transients. Requiring speed-trend confirmation suppresses 58.5% of valid APM updates, allowing braking overestimation to leak back into EKF velocity integration and degrading 300s position error by $+30.48\text{ m}$ ($220.12 \rightarrow 250.60\text{ m}$).

---

## 23. Artifacts Created

- **Script Path:** [`scripts/vw4_m027_causal_speed_trend_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m027_causal_speed_trend_apm.py)
- **Summary JSON:** `results/vw4_m027_causal_speed_trend_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m027_causal_speed_trend_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m027_causal_speed_trend_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m027_causal_speed_trend_apm_report.md)
- **Plot Directory:** `plots/vw4/m027_causal_speed_trend_apm/`

---

## 24. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 25. Next Research Decision (M028 Proposal)

**M028 Proposal — Longitudinal Acceleration Jerk Gating for APM Deceleration Initiation**:
Milestones M021–M027 have systematically disproved altering turn speed, expanding integration windows, changing ZUPT triggers, scaling 1D bounds, pitch compensation, relaxing NHC, and neural speed-trend gating. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the unbroken control ($220.12\text{ m}$). M028 should investigate an IMU Longitudinal Acceleration Jerk Gate ($j_{\text{long}} = \frac{a_{\text{long}}[k] - a_{\text{long}}[k-1]}{\Delta t} < -1.0\text{ m/s}^3$). Because IMU acceleration jerk reflects immediate mechanical brake onset without neural phase lag, M028 aims to detect real braking onset zero-latency, refining APM activation and lowering 300s position drift below $220.12\text{ m}$.

---

## 26. Full M001 → M027 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027`
