# Individual Model Performance Diagnostic Graphs

This directory (`model_evolution_report/individual_model_graphs/`) contains **23 individual, multi-panel diagnostic PNG graphs**, representing every evaluated model, architectural candidate, physical constraint layer, and counterfactual experiment across `M001` through `M040`.

Each graph is structured into three standardized diagnostic panels:
1. **Speed Accuracy Panel (Bar):** Evaluates Speed MAE (km/h) against benchmark standards.
2. **Navigation Position Error Panel (Line):** Traces 60s, 120s, and 300s integrated trajectory drift (m) against the locked $218.93\text{ m}$ benchmark.
3. **Heading / Orientation Error Panel (Bar):** Evaluates mean heading orientation error (degrees) over the outage horizon.

---

## Master Index of All 23 Individual Model Graphs

| Milestone ID | Model / Stage Name | Primary Graph Filename | Speed MAE | 300s Position Error | Decision |
|---|---|---|---:|---:|---|
| **M002** | CNN+BiLSTM Baseline Model | [`M002_ml_architecture_baseline.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M002_ml_architecture_baseline.png) | $9.22\text{ km/h}$ | $1,465.0\text{ m}$ | **SELECTED** |
| **M003** | SpeedNet v1 (Open-Loop DR) | [`M003_speednet_v1_open_loop.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M003_speednet_v1_open_loop.png) | $9.22\text{ km/h}$ | $1,465.0\text{ m}$ | **BASELINE** |
| **M004** | SpeedNet v2 + Fixed NHC | [`M004_speednet_v2_fixed_nhc.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M004_speednet_v2_fixed_nhc.png) | $9.15\text{ km/h}$ | **$263.11\text{ m}$** | **ACCEPTED** |
| **M005** | HeadingNet (Learned Yaw Model) | [`M005_headingnet_yaw_model.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M005_headingnet_yaw_model.png) | $9.15\text{ km/h}$ | $740.30\text{ m}$ | REJECTED |
| **M007** | SpeedNet v3 (Regime-Aware Model) | [`M007_speednet_v3_regime_aware.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M007_speednet_v3_regime_aware.png) | $10.45\text{ km/h}$ | $938.90\text{ m}$ | REJECTED |
| **M008** | SpeedNet v2.5 (Physics Features) | [`M008_speednet_v25_physics_features.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M008_speednet_v25_physics_features.png) | $11.20\text{ km/h}$ | $1,611.60\text{ m}$ | REJECTED |
| **M010** | Adaptive NHC Covariance Model | [`M010_adaptive_nhc_covariance.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M010_adaptive_nhc_covariance.png) | $9.15\text{ km/h}$ | $886.50\text{ m}$ | REJECTED |
| **M011** | SpeedNet v4 (Context W=60) | [`M011_speednet_v4_window_expansion.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M011_speednet_v4_window_expansion.png) | $8.90\text{ km/h}$ | $595.00\text{ m}$ | REJECTED |
| **M012** | SpeedNet v5 (Kinematic Decel Loss) | [`M012_speednet_v5_deceleration_loss.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M012_speednet_v5_deceleration_loss.png) | $14.20\text{ km/h}$ | $1,026.50\text{ m}$ | REJECTED |
| **M013** | Hard Physical Speed Constraint | [`M013_hard_physical_speed_constraint.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M013_hard_physical_speed_constraint.png) | $9.05\text{ km/h}$ | **$254.12\text{ m}$** | **ACCEPTED** |
| **M014** | Stationary 2D ZUPT Reset Model | [`M014_zupt_velocity_reset.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M014_zupt_velocity_reset.png) | $7.42\text{ km/h}$ | **$233.18\text{ m}$** | **ACCEPTED** |
| **M015** | Heading Bias Model (ZARU) | [`M015_heading_bias_zaru_model.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M015_heading_bias_zaru_model.png) | $7.42\text{ km/h}$ | $324.70\text{ m}$ | REJECTED |
| **M016** | Adaptive Velocity Innovation | [`M016_adaptive_velocity_innovation.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M016_adaptive_velocity_innovation.png) | $7.42\text{ km/h}$ | $596.40\text{ m}$ | REJECTED |
| **M017** | Multi-Scale SpeedNet Ensemble | [`M017_multiscale_speednet_ensemble.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M017_multiscale_speednet_ensemble.png) | $13.00\text{ km/h}$ | $657.60\text{ m}$ | REJECTED |
| **M018** | Causal Butterworth Filtered IMU | [`M018_causal_butterworth_filtered_imu.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M018_causal_butterworth_filtered_imu.png) | $17.90\text{ km/h}$ | $580.00\text{ m}$ | REJECTED |
| **M019** | APM Speed Damping Model | [`M019_apm_speed_damping.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M019_apm_speed_damping.png) | $7.36\text{ km/h}$ | **$220.12\text{ m}$** | **ACCEPTED** |
| **M021** | Turn Speed Attenuation Model | [`M021_turn_speed_attenuation.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M021_turn_speed_attenuation.png) | $5.93\text{ km/h}$ | $355.20\text{ m}$ | REJECTED |
| **M026** | Speed-Dependent NHC Model | [`M026_speed_dependent_nhc_covariance.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M026_speed_dependent_nhc_covariance.png) | $7.36\text{ km/h}$ | $1,149.10\text{ m}$ | REJECTED |
| **M028** | Causal IMU Jerk-Gated APM | [`M028_causal_imu_jerk_gated_apm.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M028_causal_imu_jerk_gated_apm.png) | $7.33\text{ km/h}$ | **$218.93\text{ m}$** | **FINAL BEST** |
| **M036** | Adaptive Receptive Field W50 | [`M036_adaptive_receptive_field_w50.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M036_adaptive_receptive_field_w50.png) | $11.80\text{ km/h}$ | $1,165.94\text{ m}$ | REJECTED |
| **M037** | Asymmetric Deceleration Loss | [`M037_asymmetric_deceleration_loss.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M037_asymmetric_deceleration_loss.png) | $16.50\text{ km/h}$ | $818.48\text{ m}$ | REJECTED |
| **M038** | Dynamic APM Bound Expansion | [`M038_dynamic_apm_bound_expansion.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M038_dynamic_apm_bound_expansion.png) | $7.33\text{ km/h}$ | $219.37\text{ m}$ | REJECTED |
| **M040** | EKF GT Speed Substitution | [`M040_ekf_gt_speed_substitution.png`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/model_evolution_report/individual_model_graphs/M040_ekf_gt_speed_substitution.png) | $0.00\text{ km/h}$ | $511.62\text{ m}$ | DIAGNOSTIC |

---

## Locked Final Benchmark
- **60s Outage Position Error:** **`27.35 m`**
- **120s Outage Position Error:** **`426.85 m`**
- **300s Outage Position Error:** **`218.93 m`**
- **Status:** **Permanently Locked.** No further experimentation performed.
