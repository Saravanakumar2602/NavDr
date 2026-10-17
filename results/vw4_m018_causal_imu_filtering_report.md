# Milestone M018 — Causal IMU Low-Pass Filtering & Signal Pre-Conditioning Report

## Executive Summary

- **Milestone:** M018 — Causal IMU Low-Pass Filtering & Signal Pre-Conditioning
- **Objective:** Evaluate whether applying causal Butterworth low-pass filtering ($f_c \in [2.0, 3.0, 4.0]\text{ Hz}$) to IMU measurements reduces high-frequency sensor noise and improves SpeedNet v2 dead-reckoning navigation without introducing phase lag.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M014 Baseline Control Reproduction:** **100% Exact Match** ($27.36\text{ m}$ @ 60s, $428.45\text{ m}$ @ 120s, **`233.18 m` @ 300s**).
  - **Validation Set Filter Audit:** On the Validation partition (`88566:107535`), **Raw (Unfiltered Control)** achieved the superior Speed MAE (**12.38 km/h**). Causal low-pass filtering degraded validation speed MAE to $17.89\text{ km/h}$ ($f_c=4.0\text{ Hz}$), $22.96\text{ km/h}$ ($f_c=3.0\text{ Hz}$), and $22.72\text{ km/h}$ ($f_c=2.0\text{ Hz}$).
  - **Input Distribution Shift & Phase Lag:** SpeedNet v2 was trained on raw IMU signals. Applying a causal Butterworth filter at inference time introduces a group delay ($\sim 200-300\text{ ms}$) and attenuates signal amplitude, causing severe model-input mismatch.
  - **Short/Mid Horizon Navigation Degradation:** $f_c=4.0\text{ Hz}$ filtering (F3) degraded 60s position error from $27.36\text{ m}$ to **$136.02\text{ m}$** ($+397.2\%$ error explosion), degraded 120s position error from $428.45\text{ m}$ to **$561.18\text{ m}$** ($+31.0\%$), and degraded braking speed MAE from $11.62\text{ km/h}$ to **$24.33\text{ km/h}$** ($+109.4\%$).
  - **Pathological 300s Metric Paradox:** While F3 produced a lower 300s endpoint distance ($182.03\text{ m}$), diagnostic analysis reveals this is an artifact of severe forward speed under-estimation ($15.29\text{ km/h}$ MAE vs $7.36\text{ km/h}$ for Control). Under-predicting speed shortened the integrated trajectory, coincidentally bringing the $t=300\text{ s}$ position closer to ground truth while destroying navigation accuracy at 60s and 120s.

---

## M014 Baseline Control Reproduction Verification

- **Target Benchmark (M014 F3 Winner):**
  - 60s Outage: `27.36 m`
  - 120s Outage: `428.45 m`
  - 300s Outage: `233.18 m`
- **Measured F0 Control:**
  - 60s Outage: `27.36 m`
  - 120s Outage: `428.45 m`
  - 300s Outage: `233.18 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## IMU Spectral Audit (Train Partition `0:88566`)

- **Sampling Frequency:** $f_s = 10.0\text{ Hz}$ ($\Delta t = 0.1\text{ s}$, Nyquist frequency $f_{\text{nyq}} = 5.0\text{ Hz}$).
- **Power Spectral Density Analysis:** Accelerometer and gyroscope signals exhibit primary motion dynamics in the $0.0-1.5\text{ Hz}$ band. Secondary engine vibration and chassis pitch oscillations exist in the $2.0-4.5\text{ Hz}$ band.
- **Phase Delay:** Causal 2nd-order Butterworth filtering at $f_c=2.0, 3.0, 4.0\text{ Hz}$ introduces a 2 to 3 sample phase lag ($200-300\text{ ms}$).

---

## Validation Filter Cutoff Grid Search (`88566:107535`)

| Strategy Description | Filter Cutoff ($f_c$) | Validation Speed MAE (km/h) | Status |
|---|---|---|---|
| **Raw IMU (Control F0)** | **None** | **12.38 km/h** | **BEST VALIDATION** |
| All IMU Channels (F1) | $2.0\text{ Hz}$ | $22.72\text{ km/h}$ | $+83.5\%$ Degradation |
| All IMU Channels (F2) | $3.0\text{ Hz}$ | $22.96\text{ km/h}$ | $+85.5\%$ Degradation |
| All IMU Channels (F3) | $4.0\text{ Hz}$ | $17.89\text{ km/h}$ | $+44.5\%$ Degradation |

---

## Locked Unseen Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control Raw)** | SpeedNet v2 W=40 Baseline Control | **7.36 km/h** | **11.62 km/h** | **27.36 m** | **428.45 m** | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | All IMU $f_c=2.0\text{ Hz}$ | $17.93\text{ km/h}$ | $28.59\text{ km/h}$ | $344.93\text{ m}$ | $1030.50\text{ m}$ | $1184.56\text{ m}$ | $+350.2\%$ | $+366.2\%$ | $+408.0\%$ |
| **F2** | All IMU $f_c=3.0\text{ Hz}$ | $19.08\text{ km/h}$ | $29.98\text{ km/h}$ | $336.78\text{ m}$ | $978.81\text{ m}$ | $724.40\text{ m}$ | $+175.3\%$ | $+185.1\%$ | $+210.7\%$ |
| **F3** | All IMU $f_c=4.0\text{ Hz}$ | $15.29\text{ km/h}$ | $24.33\text{ km/h}$ | $136.02\text{ m}$ | $561.18\text{ m}$ | $182.03\text{ m}^*$ | $-30.8\%$ | $-28.4\%$ | $-21.9\%$ |
| **F4** | Accel Only $f_c=4.0\text{ Hz}$ | $7.43\text{ km/h}$ | $12.53\text{ km/h}$ | $11.54\text{ m}$ | $659.66\text{ m}$ | $699.00\text{ m}$ | $+165.7\%$ | $+175.1\%$ | $+199.8\%$ |
| **F5** | Gyro Only $f_c=4.0\text{ Hz}$ | $16.50\text{ km/h}$ | $25.61\text{ km/h}$ | $160.80\text{ m}$ | $1181.87\text{ m}$ | $900.02\text{ m}$ | $+242.1\%$ | $+254.2\%$ | $+286.0\%$ |
| **F6** | Best Filter ($f_c=4.0\text{ Hz}$) | $15.29\text{ km/h}$ | $24.33\text{ km/h}$ | $136.02\text{ m}$ | $561.18\text{ m}$ | $182.03\text{ m}^*$ | $-30.8\%$ | $-28.4\%$ | $-21.9\%$ |

*\*Note: The $182.03\text{ m}$ figure for F3/F6 is an artifact of severe forward speed under-estimation ($15.29\text{ km/h}$ MAE) that shortens the trajectory endpoint while degrading 60s position error by $+397.2\%$ ($136.02\text{ m}$ vs $27.36\text{ m}$).*

---

## Detailed Failure & Tradeoff Analysis

1. **Un-trained Input Distribution Shift:**
   SpeedNet v2 was trained on raw IMU inputs. Applying a causal filter during inference removes higher-frequency spectral energy that the model learned to rely on for motion feature extraction.
2. **Phase Lag during Braking:**
   Filter group delay slows the model's perception of braking onset, causing braking speed MAE to double ($11.62 \rightarrow 24.33\text{ km/h}$).
3. **Validation Criterion Rejection:**
   Because Raw IMU achieved the best Validation Speed MAE ($12.38\text{ km/h}$ vs $17.89\text{ km/h}$ for $f_c=4.0\text{ Hz}$), filtering fails the zero-leakage validation selection protocol.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m018_causal_imu_filtering.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m018_causal_imu_filtering.py)
- **Summary JSON:** `results/vw4_m018_causal_imu_filtering_summary.json`
- **Predictions NPZ:** `results/vw4_m018_causal_imu_filtering_predictions.npz`
- **Plot Directory:** `plots/vw4/m018_causal_imu_filtering/`
  - `psd_spectral_audit.png`
  - `raw_vs_filtered_imu_signals.png`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Conclusion & Benchmark Status

Milestone M018 is **REJECTED**. The active verified project benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$
