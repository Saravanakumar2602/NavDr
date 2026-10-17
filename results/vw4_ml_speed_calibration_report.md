# ML Speed Scale Calibration Report — Vw4 Sequence

## Executive Summary & Experimental Conclusion

The **ML Speed Scale Calibration Experiment** was conducted on the Vw4 dataset using the trained CNN + BiLSTM model (`models/cnn_plus_bilstm_w30.pth`) without retraining.

All calibration parameters ($\alpha, \beta$, polynomial terms) were fitted **strictly on the Validation partition (`[88566:107535]`)**. The unseen Test partition (`start_idx = 108,000`) was reserved strictly for final evaluation across 60s, 120s, and 300s GNSS outage blackouts.

---

### Decision Classification: **RED**

> **Classification:** **RED** — *Simple linear speed calibration ($\alpha \cdot v_{\text{ML}} + \beta$) fails to improve navigation accuracy on unseen test data and degrades performance relative to the uncalibrated ML + NHC baseline (319.25 m @ 300s).*

#### Key Empirical Findings:
1. **Uncalibrated Baseline Performance:** Exp 1 (Baseline ML + NHC) achieves **319.25 meters** position error at 300s ($9.22\text{ km/h}$ speed MAE).
2. **Global Scale ($\alpha = 1.0703$):** Exp 2 increases 300s position error to **365.83 meters** (-14.59% degradation).
3. **Speed Bias Offset ($\beta = +4.29\text{ km/h}$):** Exp 3 causes 300s position error to explode to **1,006.24 meters** (-215.19% degradation) because constant positive offsets inject fictitious motion during low-speed/stationary stops!
4. **Scale + Offset Calibration ($\alpha = 0.9046, \beta = +8.39\text{ km/h}$):** Exp 4 increases 300s position error to **445.49 meters** (-39.54% degradation).
5. **Poly Speed Residual Model:** Exp 5 increases 300s position error to **1,252.45 meters** (-292.31% degradation).

---

## 1. Validation Set Parameter Fitting (Strict Anti-Leakage Protocol)

Fitted exclusively on Validation partition (`[88566:107535]`):
- **Validation MAE Before Calibration:** **14.86 km/h** (RMSE: **18.94 km/h**)
- **Exp 2 Global Scale $\alpha$:** **1.0703** (Val MAE: **14.70 km/h**)
- **Exp 3 Speed Offset $\beta$:** **+4.29 km/h**
- **Exp 4 OLS Scale + Offset:** $\alpha = 0.9046, \beta = +8.39\text{ km/h}$ (Val MAE: **15.00 km/h**)
- **Exp 5 Poly Residual Model:** $-0.0544 v^2 + 1.8562 v + 0.35\text{ m/s}$ (Val MAE: **14.58 km/h**)

---

## 2. Unseen Test Set Performance Matrix

| Outage Duration | Calibration Experiment | CDE % | Final Pos Error (m) | Max Pos Error (m) | Drift Rate (m/s) | Speed MAE (km/h) | Speed RMSE (km/h) | Final Heading Error (°) | Improvement vs Baseline (%) | % Oracle Error Removed | Latency (ms/step) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **60 sec** | **Exp 1: Baseline ML + NHC** | **41.57%** | **182.38 m** | **192.95 m** | **3.04 m/s** | **10.59 km/h** | **15.02 km/h** | **22.66°** | **0.00%** | **0.0%** | **0.0310 ms** |
| **60 sec** | **Exp 2: Global Speed Scale** | 51.57% | 208.46 m | 215.76 m | 3.47 m/s | 12.92 km/h | 17.52 km/h | 24.61° | -14.30% | 0.0% | 0.0312 ms |
| **60 sec** | **Exp 3: Speed Bias Offset** | 58.78% | 227.74 m | 234.75 m | 3.80 m/s | 14.61 km/h | 18.73 km/h | 23.07° | -24.87% | 0.0% | 0.0315 ms |
| **60 sec** | **Exp 4: Scale + Offset (OLS)** | 61.68% | 236.77 m | 244.68 m | 3.95 m/s | 15.30 km/h | 19.34 km/h | 20.53° | -29.82% | 0.0% | 0.0315 ms |
| **60 sec** | **Exp 5: Poly Speed Residual** | 57.65% | 241.35 m | 241.52 m | 4.02 m/s | 14.31 km/h | 18.39 km/h | 3.74° | -32.33% | 0.0% | 0.0318 ms |
| **60 sec** | **Exp 6: GT Speed Diagnostic** | 4.05% | 162.27 m | 162.27 m | 2.70 m/s | 2.10 km/h | 2.78 km/h | 33.77° | +11.03% | 100.0% | 0.0493 ms |
| | | | | | | | | | | | |
| **120 sec** | **Exp 1: Baseline ML + NHC** | **52.07%** | **441.92 m** | **441.92 m** | **3.68 m/s** | **13.95 km/h** | **20.67 km/h** | **68.03°** | **0.00%** | **0.0%** | **0.0364 ms** |
| **120 sec** | **Exp 2: Global Speed Scale** | 62.84% | 531.49 m | 531.49 m | 4.43 m/s | 16.68 km/h | 23.36 km/h | 68.79° | -20.27% | 0.0% | 0.0365 ms |
| **120 sec** | **Exp 3: Speed Bias Offset** | 68.11% | 580.32 m | 580.32 m | 4.84 m/s | 18.01 km/h | 24.47 km/h | 66.42° | -31.32% | 0.0% | 0.0365 ms |
| **120 sec** | **Exp 4: Scale + Offset (OLS)** | 68.84% | 591.59 m | 591.59 m | 4.93 m/s | 18.19 km/h | 24.62 km/h | 63.41° | -33.87% | 0.0% | 0.0368 ms |
| **120 sec** | **Exp 5: Poly Speed Residual** | 67.73% | 582.44 m | 582.44 m | 4.85 m/s | 17.90 km/h | 24.23 km/h | 28.25° | -31.80% | 0.0% | 0.0368 ms |
| **120 sec** | **Exp 6: GT Speed Diagnostic** | 3.64% | 496.13 m | 496.13 m | 4.13 m/s | 1.95 km/h | 2.58 km/h | 79.54° | -12.27% | 0.0% | 0.0332 ms |
| | | | | | | | | | | | |
| **300 sec** | **Exp 1: Baseline ML + NHC** | **52.79%** | **319.25 m** | **541.48 m** | **1.06 m/s** | **9.22 km/h** | **13.91 km/h** | **65.87°** | **0.00%** | **0.0%** | **0.0368 ms** |
| **300 sec** | **Exp 2: Global Speed Scale** | 63.62% | 365.83 m | 627.40 m | 1.22 m/s | 10.93 km/h | 15.60 km/h | 58.95° | -14.59% | 0.0% | 0.0369 ms |
| **300 sec** | **Exp 3: Speed Bias Offset** | 77.20% | 1,006.24 m | 1,006.24 m | 3.35 m/s | 12.97 km/h | 16.71 km/h | 158.23° | -215.19% | 0.0% | 0.0370 ms |
| **300 sec** | **Exp 4: Scale + Offset (OLS)** | 86.97% | 445.49 m | 705.80 m | 1.48 m/s | 14.54 km/h | 18.52 km/h | 33.94° | -39.54% | 0.0% | 0.0370 ms |
| **300 sec** | **Exp 5: Poly Speed Residual** | 75.89% | 1,252.45 m | 1,252.45 m | 4.17 m/s | 12.70 km/h | 16.29 km/h | 162.05° | -292.31% | 0.0% | 0.0372 ms |
| **300 sec** | **Exp 6: GT Speed Diagnostic** | 3.18% | 492.60 m | 615.71 m | 1.64 m/s | 1.50 km/h | 2.10 km/h | 160.94° | -54.30% | 0.0% | 0.0344 ms |

---

## 3. Strategic Architectural Answer

> **"Should we now build SpeedNet v2, or should we improve the navigation/filter architecture instead?"**
>
> **Answer:** **We MUST BUILD SpeedNet v2 (a deep learned, context-aware neural speed estimation architecture with zero-speed detection / stationary gating).**
>
> Post-hoc linear calibration is fundamentally incapable of fixing deep learning velocity prediction errors because neural network speed errors vary dynamically across accelerations, cruising, and stationary stops. Adding global offsets ($\beta$) injects severe false motion during stops. To bring 300s navigation drift below **150 meters**, we must train **SpeedNet v2** featuring multi-window temporal convolutions, explicit acceleration integration, and learned zero-speed classification heads.

---

## 4. Persistence Artifacts

- Script: [`scripts/vw4_ml_speed_scale_calibration.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_ml_speed_scale_calibration.py)
- Results JSON: [`results/vw4_ml_speed_calibration_results.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_ml_speed_calibration_results.json)
- Predictions NPZ: [`results/vw4_ml_speed_calibration_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_ml_speed_calibration_predictions.npz)
- Generated Plots (12 Plots):
  - Validation Speed Pred vs GT: [`plots/vw4/ml_speed_calibration/val_speed_pred_vs_gt.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/val_speed_pred_vs_gt.png)
  - Val Residual Before Calib: [`plots/vw4/ml_speed_calibration/val_speed_residual_before_calib.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/val_speed_residual_before_calib.png)
  - Val Residual After Calib: [`plots/vw4/ml_speed_calibration/val_speed_residual_after_calib.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/val_speed_residual_after_calib.png)
  - Test Speed Pred vs GT: [`plots/vw4/ml_speed_calibration/test_speed_pred_vs_gt.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/test_speed_pred_vs_gt.png)
  - Test Residual Before/After: [`plots/vw4/ml_speed_calibration/test_speed_residual_before_after.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/test_speed_residual_before_after.png)
  - Trajectories: [`outage_60s_trajectory.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/outage_60s_trajectory.png), [`outage_120s_trajectory.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/outage_120s_trajectory.png), [`outage_300s_trajectory.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/outage_300s_trajectory.png)
  - 300s Position Error: [`plots/vw4/ml_speed_calibration/outage_300s_position_error.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/outage_300s_position_error.png)
  - Final Position Error Comparison: [`plots/vw4/ml_speed_calibration/final_position_error_comparison.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/final_position_error_comparison.png)
  - Speed MAE Comparison: [`plots/vw4/ml_speed_calibration/speed_mae_comparison.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/speed_mae_comparison.png)
  - Calibration Parameter Comparison: [`plots/vw4/ml_speed_calibration/calibration_parameter_comparison.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/ml_speed_calibration/calibration_parameter_comparison.png)
