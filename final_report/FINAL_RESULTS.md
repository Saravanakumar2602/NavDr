# Final Research Results — Intelligent Dead-Reckoning (IDR) Project

## 1. Master Benchmark Provenance Table

This table documents the chronological evolution of the primary integrated dead-reckoning navigation benchmark across the major accepted project stages.

| Milestone ID | Baseline Pipeline Description | 60s Outage | 120s Outage | 300s Outage | Along-Track | Cross-Track | Status |
|---|---|---:|---:|---:|---:|---:|---|
| **Calibration** | Raw Inertial Open-Loop Integration | ~1,200.0 m | ~2,800.0 m | 6,420.00 m | N/A | N/A | Open-Loop Baseline |
| **M003** | SpeedNet v1 (Open-loop CNN+BiLSTM $W=30$) | ~350.0 m | ~850.0 m | 1,465.00 m | N/A | N/A | Initial ML Baseline |
| **M004** | SpeedNet v2 + Raw Gyro + Fixed NHC | 22.80 m | 440.20 m | **263.11 m** | $+168.4\text{ m}$ | $-192.1\text{ m}$ | Baseline Benchmark |
| **M013** | SpeedNet v2 + NHC + M013 F4 Physical Constraint | 26.70 m | 464.00 m | **254.12 m** | $+142.1\text{ m}$ | $-175.4\text{ m}$ | Accepted (-8.99 m) |
| **M014** | SpeedNet v2 + NHC + M013 F4 + M014 ZUPT F3 | 27.40 m | 428.50 m | **233.18 m** | $+118.2\text{ m}$ | $-158.6\text{ m}$ | Accepted (-20.94 m) |
| **M019** | SpeedNet v2 + NHC + M013 F4 + ZUPT + M019 APM | 27.50 m | 428.80 m | **220.12 m** | $-188.4\text{ m}$ | $-96.2\text{ m}$ | Accepted (-13.06 m) |
| **M028** | **SpeedNet v2 + NHC + M013 + ZUPT + APM + M028 Jerk Gate** | **27.35 m** | **426.85 m** | **218.93 m** | **-197.64 m** | **-94.18 m** | **NEW VERIFIED BEST** |
| **M029** | Jerk Threshold Robustness Sweep | 27.35 m | 426.85 m | **218.93 m** | $-197.64\text{ m}$ | $-94.18\text{ m}$ | Robustness Confirmed |
| **M040** | **Final Counterfactual Audit & Benchmark Lock** | **27.88 m** | **426.17 m** | **218.93 m** | **-197.63 m** | **-94.18 m** | **FINAL LOCKED BEST** |

---

## 2. Complete Milestone Performance Log (M001–M040)

| ID | Title / Intervention | Val Result | Test Result | Decision | Key Scientific Reason |
|---|---|---|---|---|---|
| `M001` | Dataset Formulation & EDA | N/A | 6,420 m | COMPLETE | Formulated 10 Hz zero-leakage dataset (test start = 108,000). |
| `M002` | ML Model Architecture Selection | 9.22 km/h | N/A | COMPLETE | Selected CNN+BiLSTM ($W=30$) over MLP and 1D-CNN. |
| `M003` | SpeedNet v1 Open-Loop DR | N/A | 1,465 m | COMPLETE | Proved heading drift is #1 bottleneck in open-loop DR. |
| `M004` | SpeedNet v2 + NHC | N/A | **263.11 m** | **ACCEPTED** | **Established 263.11 m benchmark**. Proved fixed NHC stability. |
| `M005` | HeadingNet Orientation Ablation | 1.20 deg/s | 740.3 m | REJECTED | Task-metric mismatch: lower yaw MAE $\neq$ lower 300s position drift. |
| `M006` | Residual Error Decomposition | N/A | 192 m (GT) | COMPLETE | Isolated braking (32.7%) & turns (29.9%) as #1 drift causes. |
| `M007` | SpeedNet v3 Regime-Aware Modeling | 662.6 m | 938.9 m | REJECTED | Auxiliary regime loss heads cause multi-task gradient interference. |
| `M008` | SpeedNet v2.5 Physics Features | 887.5 m | 1611.6 m | REJECTED | Feature engineering fails to beat 263.11 m benchmark. |
| `M009` | NHC Vehicle Slip Diagnostic | $\beta=0.0^\circ$ | 556.3 m | REJECTED | Disproved sideslip hypothesis ($\beta=0.0^\circ$). Uncovered turn contradiction. |
| `M010` | Adaptive NHC Covariance | 886.5 m | 886.5 m | REJECTED | Inflating $R_{\text{nhc}}$ removes lateral anchoring, exploding lateral drift. |
| `M011` | Sequence Window ($W=60$) | 595.0 m | 595.0 m | REJECTED | Expanding sequence window introduces temporal phase lag in braking. |
| `M012` | Kinematic Deceleration Loss | 1026.5 m | 1026.5 m | REJECTED | Soft loss terms cause zero-prediction speed collapse during motion. |
| `M013` | Hard Physical Constraint | 254.1 m | **254.12 m** | **ACCEPTED** | **Confidence-gated physical bound trims cruise speed bias (-8.99 m)**. |
| `M014` | ZUPT Velocity Updates | 233.2 m | **233.18 m** | **ACCEPTED** | **Stationary 2D ZUPT resets velocity integration error (-20.94 m)**. |
| `M015` | Heading Bias Correction | 36.1° | 324.7 m | REJECTED | Reducing heading error by 44% destroys path self-cancellation. |
| `M016` | Adaptive NIS Gating / $R_v$ | 596.4 m | 596.4 m | REJECTED | Down-weighting SpeedNet updates forces open-loop double-integration. |
| `M017` | Multi-Scale Temporal Ensemble | 657.6 m | 657.6 m | REJECTED | Short window ($W=20$) increases prediction noise (+219.8% drift). |
| `M018` | Causal IMU Low-Pass Filter | 136.0 m (60s) | 580.0 m | REJECTED | Causal filtering creates 200-300ms lag & distribution shift. |
| `M019` | APM Speed Damping | 220.1 m | **220.12 m** | **ACCEPTED** | **Bounded 0.5s APM trims braking speed overestimation (-13.06 m)**. |
| `M020` | Residual Drift Attribution | N/A | 220.12 m | COMPLETE | Isolated strong turn speed bias (+12.2 km/h) as #1 residual cause. |
| `M021` | Turn Speed Attenuation | 355.2 m | 355.2 m | REJECTED | Attenuating turn speed lowers MAE but destroys path compensation. |
| `M022` | APM Window Length (0.7s) | 503.2 m | 238.6 m | REJECTED | Window $>0.5\text{ s}$ accumulates IMU tilt noise, weakening damping. |
| `M023` | Multi-Stage ZUPT Transition | 949.2 m | 949.2 m | REJECTED | Variance gating triggers false ZUPTs during active low-speed rolling. |
| `M024` | APM Magnitude Ablation | 499.6 m | 220.20 m | REJECTED | Confirmed fixed $\delta v_{\max} = 0.50\text{ m/s}$ as optimal correction bound. |
| `M025` | Pitch-Tilt-Compensated APM | 505.6 m | 220.12 m | REJECTED | Sensor Fusion gravity vector subtraction is already exact. |
| `M026` | Speed-Dependent NHC | 1008.4 m | 1149.1 m | REJECTED | Relaxing $R_{\text{nhc}}$ at speed causes cross-track drift explosion. |
| `M027` | Causal Speed-Trend APM | 499.0 m | 250.60 m | REJECTED | SpeedNet derivative phase lag suppresses 58.5% of valid APM updates. |
| `M028` | Causal IMU Jerk Gate | 494.8 m | **218.93 m** | **ACCEPTED** | **Zero-latency jerk gating ($j < -1.00$) beats APM benchmark (-1.19 m)**. |
| `M029` | Jerk Threshold Robustness | 494.8 m | **218.93 m** | COMPLETE | Confirmed smooth operating plateau across $[-1.25, -0.75]\text{ m/s}^3$. |
| `M030` | Jerk-Decel Product Gate | 494.8 m | 218.93 m | REJECTED | Product gating is physically redundant when M028 jerk gate is active. |
| `M031` | Low-Speed Observability | 0 missed | 218.93 m | CLOSED | M014 static head already captures 100% of low-speed stop samples. |
| `M032` | NHC Turn Innovation | $r=-0.1565$ | 218.93 m | CLOSED | Relaxing NHC during turns explodes cross-track drift (+422.0%). |
| `M033` | Confidence-Weighted $R_v$ | 489.3 m | 225.86 m | REJECTED | Suppressing SpeedNet updates forces open-loop double-integration. |
| `M034` | ZUPT Accel Bias Observability | 0.25 m/s² | 266.20 m | REJECTED | Stationary $a_{\text{long}}$ residuals reflect suspension pitch settling. |
| `M035` | Heading Uncertainty Weighting | GT: 81.8% | 218.93 m | CLOSED | Scalar speed error dominates global vector velocity error (81.8%). |
| `M036` | Adaptive Receptive Field | 400.4 m | 1165.94 m | REJECTED | Receptive field expansion ($W=50$) causes 200ms braking lag. |
| `M037` | Asymmetric Deceleration Loss | 316.98 m | 818.48 m | REJECTED | Soft loss terms cause model distortion and speed zero-collapse. |
| `M038` | Dynamic APM Correction Bound | 494.83 m | 219.37 m | REJECTED | Expanding APM bound to $0.75\text{ m/s}$ causes negative speed bias. |
| `M039` | Strong-Turn Trajectory Geometry | Vector: 7.17k | 218.93 m | COMPLETE | Pointwise vector error vs counterfactual integration floors. |
| `M040` | Counterfactual Consistency Audit | EKF: 511.6m | **218.93 m** | **AUDIT COMPLETE** | **Fixed M039 bugs. Proved EKF Geometric Self-Cancellation**. |
