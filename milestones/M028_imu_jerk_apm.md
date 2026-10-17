# Milestone M028 — Causal IMU Longitudinal-Acceleration Jerk Gating for APM

## 1. Executive Summary

- **Milestone:** M028 — Causal IMU Longitudinal-Acceleration Jerk Gating for APM
- **Objective:** Evaluate whether a causal longitudinal acceleration jerk gate ($j_{\text{long}} = \frac{a_{\text{long}}[k] - a_{\text{long}}[k-1]}{\Delta t} < \text{threshold}$) can detect immediate mechanical braking onset zero-latency, refining M019 APM speed damping selectivity and lowering 300s dead-reckoning position drift below $220.12\text{ m}$.
- **Verdict:** **ACCEPTED (F5 / F2 Candidate: $j_{\text{long}} < -1.00\text{ m/s}^3$)**.
- **Key Findings:** Candidate F2 ($j_{\text{long}} < -1.00\text{ m/s}^3$) won validation selection with a 300s validation set position error of **$494.83\text{ m}$** (vs F0 Control $505.40\text{ m}$, a **$-10.57\text{ m}$ improvement**). Evaluated on the locked unseen test partition (`start_idx = 108,000`), Validation Winner F2 / F5 achieved **`218.93 m` @ 300s** (60s = **`27.35 m`**, 120s = **`426.85 m`**), achieving consistent all-horizon position error reductions (**$-0.18\text{ m}$ @ 60s**, **$-1.94\text{ m}$ @ 120s**, **$-1.19\text{ m}$ @ 300s**). New active benchmark is **`218.93 m` @ 300s**.

---

## 2. Research Question

Can causal longitudinal-acceleration jerk provide useful information about braking onset for APM activation, and can jerk gating refine APM selectivity and reduce 300s navigation error below $220.12\text{ m}$?

---

## 3. Core Hypothesis

The derivative of IMU longitudinal acceleration (jerk) responds zero-latency to mechanical brake onset, unlike neural speed predictions (M027) which suffer from 200–400 ms sliding-window phase lag. Adding a causal negative jerk gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) filters out steady-state deceleration tail noise while preserving high-confidence brake initiation APM updates.

---

## 4. Why M028 Follows M027

Milestone M027 demonstrated that SpeedNet-predicted speed trend derivatives exhibited a 200–400 ms phase lag behind IMU acceleration, suppressing valid APM updates and degrading 300s drift (+13.8%). M028 addresses this limitation by using instantaneous IMU acceleration jerk ($j_{\text{long}}$), which operates zero-latency directly on raw sensor physics.

---

## 5. M019 Control Reproduction Verification

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{ m @ 300s}}$$
Measured F0 Control = **`27.53 m` (60s)**, **`428.79 m` (120s)**, **`220.12 m` (300s)**. 100% exact reproduction confirmed.

---

## 6. Longitudinal Acceleration Definition

$a_{\text{long}}[k] = -(raw\_ay[k] - grav\_y[k])$, where $raw\_ay$ is the raw body Y-axis accelerometer reading and $grav\_y$ is the sensor fusion gravity vector projection.

---

## 7. Causal Jerk Definition

$$j_{\text{long}}[k] = \frac{a_{\text{long}}[k] - a_{\text{long}}[k-1]}{\Delta t}$$
Sampling rate $f_s = 10\text{ Hz}$, $\Delta t = 0.1\text{ s}$. Uses strictly current sample $k$ and past sample $k-1$. Zero future leakage.

---

## 8. Candidate Thresholds

- **F0 (Control M019):** No jerk gate (IMU deceleration trigger $a_{\text{long}} < -0.5\text{ m/s}^2$ only).
- **F1:** Existing M019 deceleration AND $j_{\text{long}} < -0.50\text{ m/s}^3$.
- **F2:** Existing M019 deceleration AND $j_{\text{long}} < -1.00\text{ m/s}^3$.
- **F3:** Existing M019 deceleration AND $j_{\text{long}} < -1.50\text{ m/s}^3$.
- **F4:** Existing M019 deceleration AND $j_{\text{long}} < -2.00\text{ m/s}^3$.
- **F5 (Val Winner):** Selected winner on Validation set (`88566:107535`).

---

## 9. Validation Protocol

Thresholds selected strictly on Validation partition (`88566:107535`). Candidate F2 ($j_{\text{long}} < -1.00\text{ m/s}^3$) won validation with $494.83\text{ m}$ position error.

---

## 10. Validation Results & 11. Validation Winner

| Candidate ID | Jerk Threshold ($j_{\text{long}}$) | Val 300s Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F2 / F5** | **$j_{\text{long}} < -1.00\text{ m/s}^3$** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F3** | $j_{\text{long}} < -1.50\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Candidate |
| **F4** | $j_{\text{long}} < -2.00\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Candidate |
| **F1** | $j_{\text{long}} < -0.50\text{ m/s}^3$ | $496.35\text{ m}$ | $357.31\text{ m}$ | Candidate |
| **F0 Control** | No Jerk Gate (M019 Baseline) | $505.40\text{ m}$ | $359.28\text{ m}$ | Control Baseline |

---

## 12. Locked-Test Results

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | **7.33 km/h** | **11.54 km/h** | $27.53\text{ m}$ | $428.79\text{ m}$ | $220.12\text{ m}$ | $-16.3\%$ | $-13.4\%$ | CONTROL |
| **F1** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.67\text{ m}$ | $-16.9\%$ | $-13.9\%$ | $-0.7\%$ |
| **F2** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-13.8%** | **-0.5%** |
| **F3** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-13.9\%$ | $-0.6\%$ |
| **F4** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $27.32\text{ m}$ | $423.60\text{ m}$ | $215.41\text{ m}$ | $-18.1\%$ | $-15.2\%$ | $-2.1\%$ |
| **F5 (Val Winner)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-13.8%** | **-0.5%** |

---

## 13. Jerk Regime Diagnostics

- **Straight Deceleration Jerk:** Mean $j_{\text{long}} = -1.82\text{ m/s}^3$ during active braking initiation.
- **Cruise / Steady Motion Jerk:** Mean $j_{\text{long}} = +0.02\text{ m/s}^3$.

---

## 14. APM Activation / Suppression Diagnostics

- **Total IMU Deceleration Events:** 118
- **F0 Control Updates:** 118 (0 suppressed)
- **F2 / F5 Activations:** 76 (42 suppressed, 35.6% suppression rate)

---

## 15. Trajectory Analysis & 16. Along/Cross-Track Analysis

- **60s Outage Error:** F0 = $27.53\text{ m}$ vs F5 = **$27.35\text{ m}$** ($-0.18\text{ m}$)
- **120s Outage Error:** F0 = $428.79\text{ m}$ vs F5 = **$426.85\text{ m}$** ($-1.94\text{ m}$)
- **300s Outage Error:** F0 = $220.12\text{ m}$ vs F5 = **$218.93\text{ m}$** ($-1.19\text{ m}$)
- **Final Along-Track Error:** F0 = $-181.76\text{ m}$ vs F5 = **$-180.25\text{ m}$** ($-1.51\text{ m}$)
- **Final Cross-Track Error:** F0 = $124.23\text{ m}$ vs F5 = **$124.16\text{ m}$** ($-0.07\text{ m}$)

---

## 17. Causality Audit & 18. Leakage Audit

Uses strictly current sample $k$ and previous sample $k-1$. Zero future sample leakage. Threshold selected strictly on Validation partition (`88566:107535`).

---

## 19. Failure / Success Mechanism

Causal jerk gating ($j_{\text{long}} < -1.00\text{ m/s}^3$) operates zero-latency at mechanical brake onset. It suppresses 42 steady-state braking tail updates where deceleration tapers off and tilt noise begins accumulating, while retaining 76 high-confidence brake initiation APM updates ($1.76\text{ km/h}$ mean correction).

---

## 20. Acceptance / Rejection Verdict

**ACCEPTED (F5 / F2 Candidate)**.

---

## 21. Research Artifacts Created

- **Script Path:** [`scripts/vw4_m028_imu_jerk_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m028_imu_jerk_apm.py)
- **Summary JSON:** `results/vw4_m028_imu_jerk_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m028_imu_jerk_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m028_imu_jerk_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m028_imu_jerk_apm_report.md)
- **Plot Directory:** `plots/vw4/m028_imu_jerk_apm/`

---

## 22. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$

---

## 23. Next Research Decision (M029 Proposal)

**M029 Proposal — Joint Jerk-Deceleration APM Correction Scaling**:
Milestone M028 successfully broke the $220.12\text{ m}$ benchmark barrier by introducing causal longitudinal acceleration jerk gating ($j_{\text{long}} < -1.00\text{ m/s}^3$), achieving **`218.93 m` @ 300s**. M029 should investigate whether dynamic correction scaling based on jerk magnitude ($\delta v_{\max}(j_{\text{long}}) = \min(0.50, 0.25 + 0.10 \cdot |j_{\text{long}}|)$) can scale APM speed damping during intense braking onset without over-correcting mild deceleration, driving 300s position drift below $218.93\text{ m}$.

---

## 24. Full M001 → M028 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028`
