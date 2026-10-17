# SIH 2026 Problem Statement 26168 — Research Milestones Progression Map

This directory contains the complete, unabridged research progression and empirical evolution of our **AI-ML Based Intelligent Dead Reckoning (IDR) System** across **52 Milestones (M001–M052)**.

---

## Milestone Categorization & Phase Roadmap

### Phase 1: Baseline Formulation & Early ML Models (M001–M006)
- **[M001] Dataset Formulation**: Formulation of high-rate synchronized vehicle telemetry (100 Hz IMU + Dual-Antenna GNSS ground truth).
- **[M002] ML Baselines Training**: Training initial MLP, 1D-CNN, and LSTM speed regression baselines.
- **[M003] SpeedNet v1 Baseline**: First temporal window neural speed estimator ($W=30$).
- **[M004] SpeedNet v2 Baseline**: Multi-task CNN+BiLSTM architecture predicting forward speed, yaw rate, zero-speed probability, and auxiliary $\Delta v$.
- **[M005] HeadingNet Orientation Ablation**: Deep learning heading estimation ablation studies.
- **[M006] v2 Residual Error Decomposition**: Empirical breakdown of longitudinal vs lateral position drift components.

### Phase 2: SpeedNet Evolution & Kinematic Boundary Constraints (M007–M013)
- **[M007] SpeedNet v3 Regime-Aware**: Regime-conditioned speed inference.
- **[M008] SpeedNet v2.5 Physics-Informed**: Incorporating physics-informed loss terms.
- **[M009] NHC Vehicle Slip Diagnostic**: Quantifying lateral slip and non-holonomic constraint violation during aggressive cornering.
- **[M010] Adaptive NHC Velocity Frame EKF**: Velocity-frame EKF formulation with dynamic lateral covariance adaptation.
- **[M011] SpeedNet v4 Temporal Context**: Extending receptive field context windows ($W=60$).
- **[M012] Kinematic Deceleration Loss**: Penalizing unphysical acceleration predictions during hard braking.
- **[M013] Hard Physical Inference Constraint (F4)**: Confidence-gated physical speed upper-bounding.

### Phase 3: Adaptive Position/Velocity Correction (APM) & ZUPT Innovations (M014–M027)
- **[M014] ZUPT Velocity Update**: Zero-Velocity Update integration ($P(\text{stat}) > 0.70$).
- **[M015] Heading Bias & Turn-Aware Fusion**: Turn-conditioned heading bias estimation.
- **[M016] Adaptive Velocity Innovation & Bias Tracking**: Innovation-based measurement covariance tuning.
- **[M017] Multiscale Temporal SpeedNet**: Multi-scale receptive field feature fusion.
- **[M018] Causal IMU Signal Filtering**: Causal low-pass filtering of accelerometer noise.
- **[M019] APM Speed Damping**: First introduction of IMU acceleration-integrated pseudo-measurement damping ($\Delta v = 0.50\text{ m/s}$).
- **[M020] Residual Drift Attribution**: Sensitivity analysis attributing residual drift to orientation vs speed errors.
- **[M021] Turn-Aware Speed Attenuation**: Attenuating speed updates during sharp yaw transients.
- **[M022] APM Window Ablation**: Systematic window size ablation ($W \in [3, 5, 7, 10]$).
- **[M023] Multistage ZUPT**: Cascaded stationary detection.
- **[M024] APM Magnitude Ablation**: Damping bound parameter sweep ($b \in [0.25, 0.50, 1.00]\text{ m/s}$).
- **[M025] Pitch Tilt APM**: Pitch-compensated longitudinal acceleration integration.
- **[M026] Speed-Dependent NHC**: Dynamic lateral noise variance scaling as a function of forward speed.
- **[M027] Causal Speed Trend APM**: Acceleration trend extrapolation.

---

### Phase 4: Production Milestone M028 & Parameter Sensitivity (M028–M039)
- **[M028] CANONICAL PRODUCTION BASELINE**: Causal IMU Jerk-Gated APM with threshold $j_{\text{long}} < -1.0\text{ m/s}^3$.
  - **Locked Performance**: 60s = **27.35m**, 120s = **426.85m**, 300s = **218.93m**, 1km = **307.46m**.
- **[M029] Jerk Threshold Robustness**: Sweeping jerk thresholds $j_{\text{thresh}} \in [-0.5, -1.0, -1.5, -2.0]\text{ m/s}^3$.
- **[M030] Jerk-Deceleration Product Gate**: Evaluating combined $j_{\text{long}} \cdot a_{\text{long}}$ gating criteria.
- **[M031] Low-Speed ZUPT Observability**: Observability analysis of EKF velocity states during low-speed maneuvers.
- **[M032] NHC Turn Innovation Diagnostic**: Quantifying innovation spikes during high-rate cornering.
- **[M033] SpeedNet Confidence RV**: Dynamic measurement covariance scaling based on model softmax confidence.
- **[M034] ZUPT Accel Bias Observability**: Estimating accelerometer bias during stationary pauses.
- **[M035] Heading Uncertainty Diagnostic**: Quantifying heading error growth rates during long outages.
- **[M036] Adaptive Receptive Field SpeedNet**: Dynamic window selection in SpeedNet.
- **[M037] Asymmetric Deceleration Loss**: Asymmetric loss functions favoring deceleration accuracy.
- **[M038] Dynamic APM Bound**: Velocity-proportional APM bounds.
- **[M039] Turn Trajectory Attribution**: Spatial error decomposition across straight vs curved road segments.

---

### Phase 5: Scientific Audits & Counterfactual Validation (M040–M052)
- **[M040] Counterfactual Consistency Audit**: Cross-validation audit verifying absence of lookahead leakage.
- **[M041] SIH Benchmark Compliance Audit**: Formal compliance audit against SIH guidelines ($<50\text{m}$ for 60s, $<500\text{m}$ for 1km).
- **[M042] Failure Mechanism Localization**: Pinpointing exact conditions triggering drift spikes.
- **[M043] Heading Observability Audit**: Mathematical proof of unobservable heading drift under pure 2D IMU.
- **[M044] Turn Deceleration Measurement Weighting**: Measurement weighting during cornering.
- **[M045] Turn Geometry Observability**: Geometric analysis of turn radius vs drift acceleration.
- **[M046] Learned Gyro Drift Correction**: ML-predicted gyro bias subtraction.
- **[M047] Turn Fusion Consistency**: Consistency analysis of heading vs speed fusion.
- **[M048] EKF State Consistency**: Normalized Innovation Squared (NIS) consistency test.
- **[M049] Heading Anchor Feasibility**: Feasibility study of landmark visual heading anchors.
- **[M050] Learned Body Velocity**: Direct ML body-frame velocity regression study.
- **[M051] Zero-Velocity Heading Constraint**: Heading constraint during zero-velocity phases.
- **[M052] Dynamic Centrifugal Acceleration Compensation Study**: Investigation of turn-induced dynamic centrifugal acceleration compensation ($a_c = v \cdot \omega_{\text{yaw}}$). Confirmed generalization failure on test set, reinforcing **M028 as the true optimal production baseline**.

---

## Reproduction Instructions
Each milestone document references its corresponding evaluation script in the [`scripts/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/) directory. To evaluate any specific milestone, execute its script directly via Python.
