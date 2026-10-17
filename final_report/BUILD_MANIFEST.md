# Final Report Build Manifest & Verification

## Package Build Metadata

- **Generated Timestamp:** `2026-09-02T18:58:15+05:30`
- **Total Milestones Covered:** 40 (`M001` through `M040`)
- **Total Research Figures Preserved:** 196 files
- **Final Production Benchmark:** **`218.93 m` @ 300s** (60s = `27.35 m`, 120s = `426.85 m`)
- **Final Production Pipeline:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 + M014 ZUPT + M019 APM + M028 Jerk Gate ($j_{\text{long}} < -1.00\text{ m/s}^3$)

---

## Figure Preservation Breakdown by Milestone

| Milestone ID | Milestone Title / Topic | Figures Copied | Source Directory / Artifact Path |
|---|---|---|---|
| **M001** | Vw04 Dataset Formulation & EDA | 36 | `plots/vw4/` + `.user_uploaded/` |
| **M002** | ML Baseline Speed & Yaw Modeling | 20 | `plots/vw4/baseline_experiment/`, etc. |
| **M003** | SpeedNet v1 Baseline & Open-Loop DR | 13 | `plots/vw4/ml_dr_error_decomposition/` |
| **M004** | SpeedNet v2 & Orientation Anchors | 21 | `plots/vw4/orientation_anchor/`, `speednet_v2/` |
| **M005** | HeadingNet Orientation Ablation | 10 | `plots/vw4/headingnet/` |
| **M006** | Residual Error Decomposition | 5 | `plots/vw4/v2_residual_decomposition/` |
| **M007** | SpeedNet v3 Regime-Aware Modeling | 7 | `plots/vw4/speednet_v3/` |
| **M008** | SpeedNet v2.5 Physics-Informed Features | 4 | `plots/vw4/speednet_v25/` |
| **M009** | NHC / Vehicle Slip Diagnostic | 10 | `plots/vw4/m009_nhc_diagnostic/` |
| **M010** | Adaptive NHC Covariance | 6 | `plots/vw4/m010_adaptive_nhc/` |
| **M011** | Temporal Context (SpeedNet v4) | 6 | `plots/vw4/m011_speednet_v4/` |
| **M012** | Kinematic Deceleration Loss (SpeedNet v5) | 6 | `plots/vw4/m012_kinematic_deceleration_loss/` |
| **M013** | Hard Physical Inference Constraint | 2 | `plots/vw4/m013_hard_physical_inference_constraint/` |
| **M014** | ZUPT Velocity Update & Fusion | 3 | `plots/vw4/m014_zupt_velocity_update/` |
| **M015** | Heading Bias & Turn-Aware Fusion | 3 | `plots/vw4/m015_heading_bias_and_turn_aware_fusion/` |
| **M016** | Adaptive Innovation & Bias Tracking | 3 | `plots/vw4/m016_adaptive_velocity_innovation/` |
| **M017** | Multi-Scale Temporal SpeedNet Ensemble | 3 | `plots/vw4/m017_multiscale_speednet/` |
| **M018** | Causal IMU Signal Pre-Conditioning | 4 | `plots/vw4/m018_causal_imu_filtering/` |
| **M019** | Acceleration-Integrated Pseudo-Measurement (APM) | 2 | `plots/vw4/m019_apm_speed_damping/` |
| **M020** | Residual Drift Attribution Decomposition | 2 | `plots/vw4/m020_residual_drift_attribution/` |
| **M021** | Conservative Turn Speed Attenuation | 2 | `plots/vw4/m021_turn_aware_speed_attenuation/` |
| **M022** | APM Integration Window Ablation | 2 | `plots/vw4/m022_apm_window_ablation/` |
| **M023** | Multi-Stage ZUPT Transition Fusion | 2 | `plots/vw4/m023_multistage_zupt/` |
| **M024** | APM Correction-Magnitude Ablation | 2 | `plots/vw4/m024_apm_magnitude_ablation/` |
| **M025** | Pitch-Tilt-Compensated APM | 2 | `plots/vw4/m025_pitch_tilt_apm/` |
| **M026** | Speed-Dependent NHC Covariance | 2 | `plots/vw4/m026_speed_dependent_nhc/` |
| **M027** | Causal Speed-Trend APM Gating | 2 | `plots/vw4/m027_causal_speed_trend_apm/` |
| **M028** | Causal IMU Jerk-Gated APM | 2 | `plots/vw4/m028_imu_jerk_apm/` |
| **M029** | Jerk Threshold Robustness Sweep | 2 | `plots/vw4/m029_jerk_threshold_robustness/` |
| **M030** | Jerk-Deceleration Product Gating | 2 | `plots/vw4/m030_jerk_deceleration_product_gate/` |
| **M031** | Low-Speed Stop Observability Diagnostic | 1 | `plots/vw4/m031_low_speed_zupt_observability/` |
| **M032** | NHC Turn-Innovation Diagnostic | 1 | `plots/vw4/m032_nhc_turn_innovation_diagnostic/` |
| **M033** | Confidence-Weighted $R_v$ Fusion | 1 | `plots/vw4/m033_speednet_confidence_rv/` |
| **M034** | ZUPT Accel Bias Observability | 1 | `plots/vw4/m034_zupt_accel_bias_observability/` |
| **M035** | Heading Uncertainty SpeedNet Weighting | 1 | `plots/vw4/m035_heading_uncertainty_speednet_diagnostic/` |
| **M036** | Adaptive Receptive-Field SpeedNet | 1 | `plots/vw4/m036_adaptive_receptive_field_speednet/` |
| **M037** | Asymmetric Deceleration Loss | 1 | `plots/vw4/m037_asymmetric_deceleration_loss/` |
| **M038** | Dynamic APM Correction Bound | 1 | `plots/vw4/m038_dynamic_apm_bound/` |
| **M039** | Strong-Turn Geometry Attribution | 1 | `plots/vw4/m039_turn_trajectory_attribution/` |
| **M040** | Counterfactual Consistency Audit | 1 | `plots/vw4/m040_counterfactual_consistency_audit/` |
| **TOTAL** | **M001 through M040 Summary** | **196** | **All 196 Plots Preserved Intact** |

---

## Safety & Integrity Verification Checklist

- [x] `final_report/` directory structure created successfully.
- [x] All 196 figure files copied without deletion, renaming, or modification of source files.
- [x] No existing milestone documentation or source code modified.
- [x] No `M041` experiment script or directory created.
- [x] Locked production benchmark verified as `218.93 m` @ 300s.
- [x] No models retrained or benchmark code altered.
