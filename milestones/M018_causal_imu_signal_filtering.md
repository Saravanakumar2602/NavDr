# Milestone M018 — Causal IMU Low-Pass Filtering & Signal Pre-Conditioning

## 1. Starting Point & Provenance Context

- **Pre-M018 Verified Benchmark (M014 F3):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 Speed Constraint + M014 Causal ZUPT = `233.18 m` @ 300s.
- **Problem Context:** Milestones M015–M017 established that filter-level modifications and sequence window truncation increase navigation drift. M018 investigates whether causal low-pass filtering of IMU measurements before SpeedNet v2 inference reduces high-frequency sensor noise and improves dead-reckoning navigation.

---

## 2. Research Question

Does causal low-pass filtering of IMU measurements reduce high-frequency sensor noise enough to improve SpeedNet's speed estimation and ultimately reduce 300s dead-reckoning position error?

---

## 3. Core Hypothesis

Applying a causal Butterworth low-pass filter ($f_c \in [2.0, 3.0, 4.0]\text{ Hz}$) to input accelerometer and gyroscope signals will remove vehicle vibration and pitch noise, producing cleaner neural speed predictions that lower 300s position drift.

---

## 4. Signal Audit & Spectral Analysis

1. **Sampling Parameters:** $f_s = 10.0\text{ Hz}$, $\Delta t = 0.1\text{ s}$, Nyquist limit $f_{\text{nyq}} = 5.0\text{ Hz}$.
2. **PSD Findings (Train Partition `0:88566`):** Primary motion dynamics occupy $0.0-1.5\text{ Hz}$. Engine vibrations and structural pitch noise reside in the $2.0-4.5\text{ Hz}$ band.
3. **Phase Lag:** Causal 2nd-order Butterworth filtering introduces a group delay of 2 to 3 samples ($200-300\text{ ms}$).

---

## 5. Filter Methodology & Candidate Definitions

- **Causality Constraint:** All filters implemented via causal single-pass `scipy.signal.lfilter` (zero future sample usage).
- **F0 (Control Unfiltered):** Raw IMU signals.
- **F1 (All IMU $f_c=2.0\text{ Hz}$):** Causal Butterworth low-pass filter on all 6 IMU channels.
- **F2 (All IMU $f_c=3.0\text{ Hz}$):** Causal Butterworth low-pass filter on all 6 IMU channels.
- **F3 (All IMU $f_c=4.0\text{ Hz}$):** Causal Butterworth low-pass filter on all 6 IMU channels.
- **F4 (Accel Only $f_c=4.0\text{ Hz}$):** Filter `ax, ay, az` only.
- **F5 (Gyro Only $f_c=4.0\text{ Hz}$):** Filter `gx, gy, gz` only.
- **F6 (Best Filter + M014):** Selected best validation strategy.

---

## 6. Baseline Control Reproduction Audit

- **Audit Target:** M014 F3 Control = `27.36 m` (60s), `428.45 m` (120s), `233.18 m` (300s).
- **Measured F0 Control:** `27.36 m` (60s), `428.45 m` (120s), **`233.18 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 7. Validation Results (`88566:107535`)

| Strategy Description | Filter Cutoff ($f_c$) | Validation Speed MAE (km/h) | Status |
|---|---|---|---|
| **Raw IMU (Control F0)** | **None** | **12.38 km/h** | **BEST VALIDATION** |
| All IMU Channels (F1) | $2.0\text{ Hz}$ | $22.72\text{ km/h}$ | $+83.5\%$ Degradation |
| All IMU Channels (F2) | $3.0\text{ Hz}$ | $22.96\text{ km/h}$ | $+85.5\%$ Degradation |
| All IMU Channels (F3) | $4.0\text{ Hz}$ | $17.89\text{ km/h}$ | $+44.5\%$ Degradation |

*Conclusion:* Raw IMU achieved the best Speed MAE on Validation set. Causal filtering degraded validation speed prediction due to input distribution shift.

---

## 8. Locked Unseen Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control Raw)** | **7.36 km/h** | **11.62 km/h** | **27.36 m** | **428.45 m** | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | $17.93\text{ km/h}$ | $28.59\text{ km/h}$ | $344.93\text{ m}$ | $1030.50\text{ m}$ | $1184.56\text{ m}$ | $+350.2\%$ | $+366.2\%$ | $+408.0\%$ |
| **F2** | $19.08\text{ km/h}$ | $29.98\text{ km/h}$ | $336.78\text{ m}$ | $978.81\text{ m}$ | $724.40\text{ m}$ | $+175.3\%$ | $+185.1\%$ | $+210.7\%$ |
| **F3** | $15.29\text{ km/h}$ | $24.33\text{ km/h}$ | $136.02\text{ m}$ | $561.18\text{ m}$ | $182.03\text{ m}^*$ | $-30.8\%$ | $-28.4\%$ | $-21.9\%$ |
| **F4** | $7.43\text{ km/h}$ | $12.53\text{ km/h}$ | $11.54\text{ m}$ | $659.66\text{ m}$ | $699.00\text{ m}$ | $+165.7\%$ | $+175.1\%$ | $+199.8\%$ |
| **F5** | $16.50\text{ km/h}$ | $25.61\text{ km/h}$ | $160.80\text{ m}$ | $1181.87\text{ m}$ | $900.02\text{ m}$ | $+242.1\%$ | $+254.2\%$ | $+286.0\%$ |
| **F6** | $15.29\text{ km/h}$ | $24.33\text{ km/h}$ | $136.02\text{ m}$ | $561.18\text{ m}$ | $182.03\text{ m}^*$ | $-30.8\%$ | $-28.4\%$ | $-21.9\%$ |

---

## 9. Braking Analysis & Phase-Lag Diagnostics

- **Braking Speed MAE:** Control = $11.62\text{ km/h}$, F3 ($f_c=4\text{Hz}$) = $24.33\text{ km/h}$ (**$+109.4\%$ degradation**).
- **Phase Lag Effect:** Causal low-pass filtering introduced a $200-300\text{ ms}$ delay during deceleration, causing SpeedNet to severely overestimate speed during braking.

---

## 10. 60/120/300s Navigation Results

- **60s Outage:** Control = **$27.36\text{ m}$**, F3 = $136.02\text{ m}$ ($+397.2\%$ error explosion).
- **120s Outage:** Control = **$428.45\text{ m}$**, F3 = $561.18\text{ m}$ ($+31.0\%$ degradation).
- **300s Outage:** Control = **`233.18 m`**, F3 = $182.03\text{ m}^*$.

---

## 11. Comparison with Historical Benchmarks

- **vs Historical Benchmark ($263.11\text{ m}$):** F0 Control remains $-11.4\%$ better ($233.18\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F0 Control remains $-8.2\%$ better ($233.18\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F0 Control = **0.0% (Control)**.

---

## 12. Leakage & Causality Audit

- Causal single-pass `lfilter` was used. Zero future samples or non-causal smoothers (`filtfilt`) were employed.

---

## 13. Failure Mechanisms & Metric Paradox Analysis

1. **Un-trained Input Distribution Shift:** SpeedNet v2 was trained on raw IMU inputs. Filtering IMU inputs at inference time alters feature statistics, degrading speed prediction accuracy across all regimes ($7.36 \rightarrow 15.29\text{ km/h}$).
2. **Endpoint Distance Metric Paradox:** While F3 reached $182.03\text{ m}$ at $t=300\text{ s}$, it degraded 60s position error by $+397.2\%$ ($136.02\text{ m}$) and 120s error by $+31.0\%$ ($561.18\text{ m}$). Under-predicting forward speed shortened the total integrated path length, which happened to cross closer to ground truth at $t=300\text{ s}$ despite severe navigation trajectory distortion.

---

## 14. Success Mechanism (N/A - Milestone Rejected)

Filtering failed validation selection and degraded short-to-medium horizon navigation.

---

## 15. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m018_causal_imu_filtering.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m018_causal_imu_filtering.py)
- **Summary JSON:** `results/vw4_m018_causal_imu_filtering_summary.json`
- **Predictions NPZ:** `results/vw4_m018_causal_imu_filtering_predictions.npz`
- **Report Markdown:** [`results/vw4_m018_causal_imu_filtering_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m018_causal_imu_filtering_report.md)
- **Plot Directory:** `plots/vw4/m018_causal_imu_filtering/`

---

## 16. Final M018 Verdict

**REJECTED**.

Active Verified Benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$

---

## 17. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018`

---

## 18. Exactly ONE Evidence-Based Next Direction (M019 Proposal)

**M019 Proposal — Acceleration-Integrated Pseudo-Measurement (APM) Speed Damping**:
Milestones M011–M018 have proven that SpeedNet v2 $W=40$ with raw IMU inputs is the optimal neural backbone, and that filter gating, heading updates, window reduction, and input low-pass filtering all degrade navigation performance. M019 should investigate a causal Acceleration-Integrated Pseudo-Measurement (APM) speed damping update in the EKF during active deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$). Rather than modifying SpeedNet or gating updates, APM uses the physical IMU longitudinal acceleration integral over short 0.5s intervals to damp SpeedNet overestimation during braking, aiming to reduce 300s position drift below $233.18\text{ m}$.
