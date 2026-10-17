# Master Figure Index — M001 through M040

This document provides the complete, chronological index of all 196 research figures preserved in `final_report/figures/`.

---

## Master Benchmark Overview
- `figures/benchmark_evolution_master.png`: Chronological evolution line chart of 60s, 120s, and 300s integrated dead-reckoning position error across benchmark milestone stages (`M003` to `M040`).

---

## Milestone Figure Index

### M001 — Vw04 Dataset Formulation & EDA
- `figures/M001/M001_acceleration_comparison.png`: Raw accelerometer signal comparison between smartphone IMU and vehicle CAN/VBOX reference.
- `figures/M001/M001_accelerometer.png`: Tri-axial smartphone accelerometer readings over full dataset duration.
- `figures/M001/M001_gravity.png`: Smartphone Sensor Fusion gravity component isolation across X, Y, Z axes.
- `figures/M001/M001_gyroscope.png`: Tri-axial smartphone gyroscope readings showing vehicle roll, pitch, and yaw rates.
- `figures/M001/M001_magnetometer.png`: Smartphone magnetometer readings and uncalibrated magnetic field disturbances.
- `figures/M001/M001_orientation.png`: Estimated Euler roll, pitch, and yaw orientation angles.
- `figures/M001/M001_smartphone_gps.png`: Raw smartphone GNSS position trajectory vs VBOX RTK reference.
- `figures/M001/M001_speed_comparison.png`: Raw speed estimates derived from smartphone IMU integration vs VBOX ground-truth speed.
- `figures/M001/M001_trajectory_comparison.png`: Raw open-loop inertial double-integration 2D trajectory vs VBOX ground truth.
- `figures/M001/M001_vehicle_acceleration.png`: Derived longitudinal and lateral vehicle accelerations.
- `figures/M001/M001_vehicle_speed.png`: VBOX RTK ground-truth forward vehicle speed profile.
- `figures/M001/M001_vehicle_yaw_rate.png`: VBOX RTK ground-truth vehicle yaw-rate profile.
- `figures/M001/M001_wheel_speeds.png`: Individual wheel-speed sensor data from vehicle CAN bus reference.
- *(Plus 23 detailed exploratory diagnostic plots preserved in `figures/M001/`)*

### M002 — ML Baseline Speed & Yaw Modeling
- `figures/M002/M002_speed_prediction_scatter.png`: Parity scatter plot of neural speed predictions vs VBOX ground truth.
- `figures/M002/M002_yaw_rate_prediction_time_series.png`: Time-series plot of predicted yaw rate vs gyro reference.
- *(Plus 18 sequence model training and validation curve plots in `figures/M002/`)*

### M003 — SpeedNet v1 Baseline & Open-Loop DR
- `figures/M003/M003_open_loop_dr_trajectory.png`: Open-loop SpeedNet v1 dead-reckoning trajectory showing 1,465 m 300s position drift.
- `figures/M003/M003_position_error_vs_time.png`: Cumulative position error over 300s GNSS outage horizon.
- *(Plus 11 error decomposition plots in `figures/M003/`)*

### M004 — SpeedNet v2 Multi-Task & Kinematic Constraints
- `figures/M004/M004_speednet_v2_trajectory.png`: SpeedNet v2 + Raw Gyro + NHC 2D trajectory reaching 263.1 m 300s error.
- `figures/M004/M004_orientation_anchor_comparison.png`: Comparison of fixed vs adaptive orientation anchor trajectory drift.
- *(Plus 19 model evaluation plots in `figures/M004/`)*

### M005 — HeadingNet Orientation Module Ablation
- `figures/M005/M005_headingnet_yaw_error.png`: Pointwise yaw-rate MAE evaluation for HeadingNet $W=50$.
- `figures/M005/M005_headingnet_trajectory_drift.png`: Integrated position error showing 740 m drift (Task-metric mismatch).
- *(Plus 8 network training plots in `figures/M005/`)*

### M006 — Second-Stage Residual Error Decomposition
- `figures/M006/M006_residual_error_breakdown.png`: Pie chart of 300s position drift breakdown (Braking 32.7%, Turns 29.9%).
- `figures/M006/M006_speed_bias_by_motion_regime.png`: Systematic positive speed overestimation (+6.4 km/h) during braking and turns.
- *(Plus 3 regime breakdown plots in `figures/M006/`)*

### M007 — SpeedNet v3 Regime-Aware Speed Estimation
- `figures/M007/M007_regime_classification_confusion_matrix.png`: Multi-task regime classification confusion matrix.
- `figures/M007/M007_v3_trajectory_drift.png`: SpeedNet v3 integrated dead-reckoning position error (938.9 m at 300s).
- *(Plus 5 model diagnostic plots in `figures/M007/`)*

### M008 — SpeedNet v2.5 Physics-Informed Features
- `figures/M008/M008_v25_feature_importance.png`: Feature importance of integrated acceleration and tilt angle inputs.
- `figures/M008/M008_v25_trajectory_comparison.png`: Dead-reckoning position error for feature variants (1611.6 m selected).
- *(Plus 2 feature evaluation plots in `figures/M008/`)*

### M009 — NHC / Vehicle Slip Observability Diagnostic
- `figures/M009/M009_sideslip_angle_distribution.png`: Apparent body sideslip distribution ($\beta = 0.000^\circ$).
- `figures/M009/M009_gt_yaw_nhc_contradiction.png`: Trajectory contradiction when combining GT Yaw with fixed NHC (556.3 m).
- *(Plus 8 diagnostic plots in `figures/M009/`)*

### M010 — Adaptive NHC Covariance & Velocity-Frame EKF
- `figures/M010/M010_adaptive_nhc_r_profile.png`: Dynamic $R_{\text{nhc}}(\omega)$ covariance inflation profile during turns.
- `figures/M010/M010_adaptive_nhc_lateral_drift.png`: Lateral position drift explosion (886.5 m) under $R_{\text{nhc}}$ relaxation.
- *(Plus 4 EKF diagnostic plots in `figures/M010/`)*

### M011 — Sequence Window / Temporal Context (SpeedNet v4)
- `figures/M011/M011_speednet_v4_window_mae.png`: Speed MAE across window sizes $W \in [40, 50, 60, 80]$.
- `figures/M011/M011_speednet_v4_trajectory.png`: Integrated position drift showing phase lag explosion (595.0 m).
- *(Plus 4 model evaluation plots in `figures/M011/`)*

### M012 — Kinematic Deceleration Loss (SpeedNet v5)
- `figures/M012/M012_kinematic_loss_weight_sweep.png`: Speed MAE and braking bias vs physical loss weight $\lambda$.
- `figures/M012/M012_v5_trajectory_drift.png`: Dead-reckoning position drift showing zero-prediction collapse (1026.5 m).
- *(Plus 4 loss ablation plots in `figures/M012/`)*

### M013 — Hard Physical Inference Constraint
- `figures/M013/M013_speed_truncation_profile.png`: Confidence-gated speed bound truncation profile during cruise and stops.
- `figures/M013/M013_m013_trajectory_comparison.png`: 300s position drift reduction to **254.1 m** under M013 F4.

### M014 — ZUPT Velocity Update & Stationary Fusion
- `figures/M014/M014_zupt_detector_activations.png`: Stationary ZUPT detector binary activation flags across outage.
- `figures/M014/M014_velocity_reset_profile.png`: EKF velocity state resets during vehicle stops.
- `figures/M014/M014_m014_trajectory_comparison.png`: 300s position drift reduction to **233.2 m** under M014 F3.

### M015 — Controlled Heading-Error Experiment
- `figures/M015/M015_gyro_bias_estimation.png`: ZARU causal gyro bias convergence profile during stops.
- `figures/M015/M015_heading_error_reduction.png`: Mean heading error reduction from 64.6° to 36.1°.
- `figures/M015/M015_m015_trajectory_degradation.png`: 300s position drift degradation to 324.7 m due to destruction of self-cancellation.

### M016 — Adaptive EKF Innovation Gating & Bias Tracking
- `figures/M016/M016_nis_gating_innovations.png`: Normalized Innovation Squared (NIS) speed measurement residuals.
- `figures/M016/M016_adaptive_rv_profile.png`: Dynamic $R_v$ measurement covariance scaling during transients.
- `figures/M016/M016_m016_trajectory_degradation.png`: Position error explosion to 596.4 m under open-loop fallback.

### M017 — Multi-Scale Temporal SpeedNet Ensemble
- `figures/M017/M017_multiscale_ensemble_predictions.png`: Multi-window ($W20/W30/W40$) speed prediction comparison.
- `figures/M017/M017_w20_vibration_noise.png`: High-frequency prediction noise under short $W=20$ window.
- `figures/M017/M017_m017_trajectory_degradation.png`: Position error degradation (657.6 m) under multi-scale ensembling.

### M018 — Causal IMU Signal Pre-Conditioning
- `figures/M018/M018_butterworth_filter_frequency_response.png`: Causal Butterworth low-pass filter frequency response ($f_c=4\text{ Hz}$).
- `figures/M018/M018_filtered_imu_phase_lag.png`: Measured 200–300ms phase lag on IMU signals after filtering.
- `figures/M018/M018_60s_error_explosion.png`: 60s position error explosion to 136.0 m under causal filtering.
- `figures/M018/M018_m018_trajectory_degradation.png`: 300s position error degradation under filtered inference.

### M019 — Acceleration-Integrated Pseudo-Measurement (APM)
- `figures/M019/M019_apm_speed_reduction_profile.png`: Bounded APM speed damping corrections ($\delta v_{\max} = 0.50\text{ m/s}$) during braking.
- `figures/M019/M019_m019_trajectory_comparison.png`: 300s position drift reduction to **220.1 m** under M019 F4.

### M020 — Residual Drift Attribution Decomposition
- `figures/M020/M020_turn_speed_overestimation_bias.png`: Speed overestimation bias (+12.2 km/h) specifically during strong turns.
- `figures/M020/M020_turn_heading_error_growth.png`: Cumulative heading integration error across turn episodes.

### M021 — Conservative Turn Speed Attenuation
- `figures/M021/M021_attenuation_factor_profile.png`: Turn speed attenuation factor $\gamma(\omega)$ during strong turns.
- `figures/M021/M021_m021_trajectory_degradation.png`: Position error explosion to 355.2 m due to path-length compensation loss.

### M022 — APM Integration Window Ablation
- `figures/M022/M022_window_length_ablation.png`: 300s position error vs integration window length ($N \in [3, 5, 7, 10]$).
- `figures/M022/M022_m022_trajectory_degradation.png`: Test position error degradation to 238.6 m for $0.7\text{ s}$ window.

### M023 — Multi-Stage ZUPT Transition Fusion
- `figures/M023/M023_accel_variance_detector.png`: Low acceleration variance threshold ($\sigma_a^2 \le 0.15$) detector flags.
- `figures/M023/M023_false_zupt_rolling_motion.png`: False ZUPT triggering during active low-speed rolling (1.0–3.6 km/h).

### M024 — APM Correction-Magnitude Ablation
- `figures/M024/M024_magnitude_bound_ablation.png`: 300s position error vs APM max correction bound $\delta v_{\max} \in [0.25, 0.75]\text{ m/s}$.
- `figures/M024/M024_m024_trajectory_comparison.png`: Confirmation of $0.50\text{ m/s}$ as the optimal physical bound.

### M025 — Pitch-Tilt-Compensated APM
- `figures/M025/M025_pitch_tilt_acceleration.png`: Sensor Fusion gravity subtraction verification ($a_{\text{long}} = -(a_y - g_y)$).
- `figures/M025/M025_m025_trajectory_degradation.png`: Slight validation error degradation under redundant pitch compensation.

### M026 — Speed-Dependent NHC Covariance
- `figures/M026/M026_speed_dependent_r_profile.png`: Dynamic $R_{\text{nhc}}(v) = R_0(1+\gamma v^2)$ covariance expansion profile.
- `figures/M026/M026_cross_track_drift_explosion.png`: Cross-track position error explosion (1,149.1 m) under high-speed NHC relaxation.

### M027 — Causal Speed-Trend APM Gating
- `figures/M027/M027_speednet_derivative_lag.png`: Measured 200–400ms phase lag on SpeedNet derivative $dv/dt$.
- `figures/M027/M027_suppressed_apm_updates.png`: Suppression of 58.5% of valid APM updates due to derivative lag.

### M028 — Causal IMU Jerk-Gated APM
- `figures/M028/M028_longitudinal_jerk_profile.png`: Zero-latency causal longitudinal jerk signal ($j_{\text{long}} < -1.00\text{ m/s}^3$).
- `figures/M028/M028_m028_trajectory_comparison.png`: 300s position drift reduction to **218.93 m** under M028 F2.

### M029 — Jerk Threshold Robustness Sweep
- `figures/M029/M029_jerk_threshold_sweep_plateau.png`: Smooth, flat operating plateau across $j_{\text{thresh}} \in [-1.25, -0.75]\text{ m/s}^3$.
- `figures/M029/M029_m029_robustness_confirmation.png`: Confirmation of $218.93\text{ m}$ benchmark robustness (<6 cm variation).

### M030 — Jerk-Deceleration Product Gating
- `figures/M030/M030_product_gate_correlation.png`: Physical redundancy between jerk gate and deceleration trigger.
- `figures/M030/M030_m030_trajectory_comparison.png`: Test performance equivalence confirming product gate redundancy.

### M031 — Low-Speed Stop Observability Diagnostic
- `figures/M031/M031_low_speed_observability_coverage.png`: Zero additional missed low-speed samples captured by proposed gate.

### M032 — NHC Turn-Innovation Diagnostic
- `figures/M032/M032_nhc_turn_innovation_scatter.png`: Correlation scatter plot between NHC innovation and position error ($r = -0.1565$).

### M033 — Confidence-Weighted $R_v$ Fusion
- `figures/M033/M033_confidence_weighted_rv_profile.png`: Measurement covariance inflation profile $R_v(\sigma_a^2)$.

### M034 — ZUPT Accel Bias Observability
- `figures/M034/M034_stationary_accel_bias_residuals.png`: Inter-episode accelerometer residuals reflecting suspension pitch tilt settling.

### M035 — Heading Uncertainty SpeedNet Weighting
- `figures/M035/M035_heading_uncertainty_speednet_weights.png`: Vector velocity MAE decomposition showing scalar speed error dominance (81.8%).

### M036 — Adaptive Receptive-Field SpeedNet
- `figures/M036/M036_w50_braking_phase_lag.png`: Measured 200ms braking phase lag on SpeedNet $W=50$ predictions.

### M037 — Asymmetric Deceleration Loss
- `figures/M037/M037_asymmetric_loss_speed_bias.png`: Zero-prediction speed collapse under soft asymmetric deceleration loss.

### M038 — Dynamic APM Correction Bound
- `figures/M038/M038_dynamic_apm_bound_trajectory.png`: Position error degradation under dynamic $\delta v_{\max} = 0.75\text{ m/s}$ bound.

### M039 — Strong-Turn Geometry Attribution
- `figures/M039/M039_counterfactual_error_floors.png`: Pointwise vector error vs counterfactual trajectory integration floors.

### M040 — Counterfactual Consistency Audit
- `figures/M040/M040_ekf_counterfactual_audit.png`: Production EKF vs EKF-compatible Ground-Truth Speed measurement substitution ($511.62\text{ m}$).
