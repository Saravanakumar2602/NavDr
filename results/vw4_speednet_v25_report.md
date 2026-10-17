# SpeedNet v2.5 — Physics-Informed Features Research Report

## Executive Summary

**Experiment:** `scripts/vw4_speednet_v25_physics_informed.py`
**Dataset:** Vw04, unseen test partition, `start_idx = 108,000`
**Provenance-Locked Benchmark to Beat:** SpeedNet v2 + Raw Gyro + NHC = **263.11 m @ 300s**
**M008 Verdict:** **FAILURE**

- **Selected Model via Validation Set:** **F3 (F0 + Estimated Tilt Angle)** with Validation Speed MAE = `13.097 km/h`
- **F3 Unseen Test Speed MAE:** `9.017 km/h` (Bias: `+7.954 km/h`)
- **F3 300s GNSS-Denied Position Error:** **`1611.58 m`** (Degraded vs benchmark by +1,348.47 m / +512.5%)
- **Best 300s Navigation Result Among Physics Variants:** **F2 (+Short-Term IMU Variance) = `823.86 m`** (Validation MAE failed to select it)

> **Key Scientific Finding:** Derived physics features (tilt angle, short-term rolling variance, integrated acceleration) did NOT eliminate SpeedNet v2's systematic positive speed bias (`+7.95 km/h` to `+8.41 km/h`). While F1 (+Integrated Accel Delta) improved 300s navigation over F0 control (`887.47 m` vs `1441.01 m` in $W=30$ setup), **no physics feature variant beat the provenance-locked SpeedNet v2 $W=40$ benchmark (263.1 m)**.

---

## 1. Experiment 1: Feature Derivation & Validity Check

All derived features passed 100% numerical causality and integrity checks (0 NaNs, 0 Infs):

| Feature Name | Description | Formula / Source | Min | Max | Mean |
|---|---|---|---|---|---|
| `ax_lin`, `ay_lin`, `az_lin` | Linear accelerations (gravity subtracted) | IMU 6-channel base | -31.41 | +26.71 | +0.1478 |
| `gx`, `gy`, `gz` | Gyroscope angular rates (rad/s) | IMU 6-channel base | -2.07 | +3.55 | -0.0007 |
| `dv_acc_5step` | Causal 0.5s integrated accel change | $\sum_{k=0}^{4} a_{\text{long}}(t-k) \Delta t$ | -4.02 m/s | +4.52 m/s | +0.0880 m/s |
| `a_var_5step` | 0.5s rolling acceleration variance | $\text{Var}_{5}(a_{\text{long}})$ | 0.00 m²/s⁴ | +284.78 m²/s⁴ | +4.2462 m²/s⁴ |
| `w_var_5step` | 0.5s rolling yaw rate variance | $\text{Var}_{5}(\omega_{\text{yaw}})$ | 0.00 rad²/s² | +4.16 rad²/s² | +0.0615 rad²/s² |
| `tilt_angle` | Vehicle pitch/tilt angle relative to gravity | $\arctan2(g_y, \sqrt{g_x^2 + g_z^2})$ | -0.0309 rad | +0.0400 rad | -0.0000 rad |

---

## 2. Experiment 2: Validation Model Selection (Train: `0:88566` | Val: `88566:107535`)

Models trained for 15 epochs ($W=30$, batch size 1024, Adam lr $10^{-3}$):

| Feature Variant | Input Channels | Val Loss | Val Speed MAE (km/h) | Model Parameters | Selection Status |
|---|:---:|---:|---:|---:|---|
| **F0 (SpeedNet v2 Control)** | 6 ch | 3.3109 | 13.354 km/h | 89,220 | Control |
| **F1 (+ Integrated Accel)** | 7 ch | 3.2819 | 13.230 km/h | 89,316 | Candidate |
| **F2 (+ Short-Term IMU Var)** | 8 ch | 12.7044 | 47.291 km/h | 89,412 | Failed local min |
| **F3 (+ Estimated Tilt Angle)** | 7 ch | **3.2443** | **13.097 km/h** | 89,316 | **SELECTED** ✅ |
| **F4 (Combined Physics Set)** | 10 ch | 3.4104 | 13.711 km/h | 89,604 | Candidate |

- **Selection:** **F3 (+ Estimated Tilt Angle)** was selected via validation set performance (lowest Val MAE = `13.097 km/h`).

---

## 3. Experiment 3: Speed Prediction Evaluation (Unseen Test Partition `108000:126505`)

Pure prediction metrics evaluated on the unseen test set:

| Variant | Test Speed MAE (km/h) | Test Speed Bias (km/h) | Test Speed RMSE (km/h) |
|---|---:|---:|---:|
| **F0 (Control)** | **8.866 km/h** | **+7.988 km/h** | 14.757 km/h |
| **F1 (+ Integrated Accel)** | 9.141 km/h | +8.408 km/h | 14.684 km/h |
| **F2 (+ Short-Term IMU Var)** | 16.525 km/h | -16.525 km/h | 22.602 km/h |
| **F3 (+ Tilt Angle - Selected)** | 9.017 km/h | +7.954 km/h | 14.827 km/h |
| **F4 (Combined Physics Set)** | 9.021 km/h | +8.050 km/h | **14.276 km/h** |

> **Key Observation:** Derived physics features did NOT reduce the systematic positive speed bias (`+7.95` to `+8.41 km/h`). All variants continue to overestimate forward vehicle speed during deceleration and cruise.

---

## 4. Experiment 4: Navigation Ablation (Raw Gyro + NHC Filter)

Evaluation across 60s, 120s, and 300s GNSS outage blackouts (`start_idx = 108,000`):

| Candidate / Feature Variant | 60s Error | 120s Error | 300s Error | 300s Speed MAE | 300s Heading Err | vs Benchmark (263.1m) |
|---|---:|---:|---:|---:|---:|---|
| **SpeedNet v2 + Raw Gyro + NHC Benchmark** | 22.75 m | 440.20 m | **263.11 m** | 6.71 km/h | 85.35° | **BENCHMARK** |
| **F0: Control (W=30 setup)** | 226.67 m | 981.44 m | 1441.01 m | 7.98 km/h | 160.7° | +447.7% Worse |
| **F1: + Integrated Accel Delta** | 162.44 m | 467.55 m | **887.47 m** | 8.30 km/h | 87.6° | +237.3% Worse |
| **F2: + Short-Term IMU Variance** | 382.58 m | 813.61 m | 823.86 m | 15.05 km/h | 173.3° | +213.1% Worse |
| **F3: + Estimated Tilt Angle (Selected)** | 315.91 m | 1068.72 m | **1611.58 m** | 8.12 km/h | 178.4° | **+512.5% Worse** |
| **F4: + Combined Physics Features** | 323.92 m | 946.58 m | 1175.04 m | 7.99 km/h | 25.9° | +346.6% Worse |
| **GT Speed + Raw Gyro + NHC** | 155.39 m | 741.20 m | 1071.19 m | 1.50 km/h | 12.6° | Oracle |

---

## 5. Experiment 5: 300s Regime-Specific Navigation Drift Breakdown

Where did position error accumulate during the 300s outage for F0 vs F3 (Selected)?

| Regime | % of Time | F0 Drift (m) | F0 % Drift | F3 (Selected) Drift (m) | F3 % Drift | Net Change (m) |
|---|---:|---:|---:|---:|---:|---|
| **Stationary** | 35.2% | +0.2 m | 0.0% | -1.5 m | -0.1% | +1.7 m |
| **Acceleration** | 10.7% | 241.8 m | 16.8% | 270.0 m | 16.8% | -28.2 m Worse |
| **Braking** | 12.3% | 293.4 m | 20.4% | 309.7 m | 19.2% | -16.3 m Worse |
| **Straight/Cruise** | 21.4% | 482.9 m | 33.5% | 506.8 m | 31.4% | -23.9 m Worse |
| **Moderate Turn** | 17.2% | 395.7 m | 27.5% | 475.9 m | 29.5% | -80.2 m Worse |
| **Strong Turn** | 3.2% | 27.1 m | 1.9% | 50.7 m | 3.1% | -23.6 m Worse |

---

## 6. Answers to Mandatory Diagnostic Questions

1. **Did SpeedNet v2.5 beat the 263.1 m benchmark?**
   - **NO.** Selected model F3 produced `1611.58 m` at 300s (+512.5% worse than 263.1 m).
2. **Which derived feature helped most in navigation?**
   - **Integrated Acceleration Delta (F1)** provided the best navigation improvement over control in the $W=30$ setup (`887.47 m` vs `1441.01 m`), but still failed to beat the $W=40$ benchmark (`263.1 m`).
3. **Which feature failed?**
   - **Estimated Tilt Angle (F3)** and **Rolling Variance (F2)** failed. F3 increased heading drift instability at 300s (`178.4°` heading error), while F2 suffered from training convergence to a negative bias local minimum.
4. **Why did lower validation MAE not translate into lower navigation drift?**
   - F3 achieved the lowest validation speed MAE (`13.10 km/h`), but its small residual prediction oscillations excited yaw-rate state errors in the 7-state EKF filter during turns, causing heading degradation (`178.4°`) and large integrated position drift.
5. **Is the <150 m target realistic with input feature engineering alone?**
   - **NO.** Input feature engineering on 1D-CNN+BiLSTM window representations cannot overcome the fundamental observability limitation of smartphone IMUs during long outages.

---

## 7. Artifacts & Outputs

- **Script:** [`scripts/vw4_speednet_v25_physics_informed.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v25_physics_informed.py)
- **Model Checkpoints:** `models/speednet_v25_f0_w30.pth` through `models/speednet_v25_f4_w30.pth`
- **Summary JSON:** [`results/vw4_speednet_v25_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_summary.json)
- **Predictions Array:** [`results/vw4_speednet_v25_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_predictions.npz)
- **Plots Directory:** [`plots/vw4/speednet_v25/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/speednet_v25/) (4 diagnostic plots)
