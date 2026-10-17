# M043 Heading Observability Audit & Causal Orientation Study

## Executive Summary
- **Milestone:** M043 — Heading Observability Audit & Causal Orientation Enhancement Study
- **Objective:** Perform Phase 0 audit resolving M042 vs M041 checkpoint consistency, analyze 6-axis IMU heading observability, characterize gyro yaw integration drift across motion regimes, and evaluate causal orientation baselines.
- **Phase 0 Audit Result:** **Resolved**. Inconsistency classified as `E. Legitimate non-monotonic trajectory behavior + A. M042 checkpoint search filter masking early transient.`. The position error curve is non-monotonic: starting high (~38%), dropping to 6.69% (27.35m) at 60s (409m) due to trajectory reconvergence, and exploding to 48.80% (426.85m) at 120s (874.76m) during curved braking.
- **Heading Observability Verdict:** **`C. M043 DIAGNOSTIC ONLY — heading is not sufficiently observable for a justified intervention.`**
- **Production Pipeline Changed:** **NO** (Locked baseline retained at **218.93 m @ 300s**).

## Heading Error Characterization across 300s Outage
- **Mean Heading Error:** -18.55°
- **Median Heading Error:** -22.54°
- **MAE:** 64.66°
- **RMSE:** 80.54°
- **P95 Absolute Error:** 157.6°
- **Maximum Absolute Error:** 179.86°
- **Drift Rate:** -0.4454°/s (-26.72°/min)

## Regime-Specific Heading MAE
- **Straight:** MAE = 94.5° (Max = 179.86°, N = 1153)
- **Moderate Turn:** MAE = 43.96° (Max = 170.43°, N = 613)
- **Strong Turn:** MAE = 49.47° (Max = 147.51°, N = 837)
- **Stationary:** MAE = 99.57° (Max = 179.86°, N = 1055)

## Counterfactual Heading Benchmark

| Counterfactual Variant | Integration Type | 300s Position Drift | Description |
|---|---|---|---|
| **Kinematic CF0** | Pure Kinematic | 213.81 m | Production Speed + Gyro Heading |
| **Kinematic CF1** | Pure Kinematic | 328.44 m | GT Speed + Gyro Heading |
| **Kinematic CF2** | Pure Kinematic | 438.68 m | Production Speed + GT Heading |
| **Kinematic CF3** | Pure Kinematic | **5.64 m** | **Kinematic Oracle Floor** (GT Speed + GT Heading) |
| **EKF Baseline (CF0)** | EKF Navigation | **218.93 m** | **Locked Production Baseline** |

## Physical Observability Rationale
A 6-axis IMU (accelerometer + gyroscope) observes roll and pitch tilt via gravity projection during stationary conditions, but YAW ANGLE IS KINEMATICALLY UNOBSERVABLE during dynamic 2D vehicle motion without magnetometer or external velocity updates. Causal bias estimation and zero-velocity locks cannot prevent integrated yaw drift during curved maneuvers (700m-1000m), and static heading overrides disrupt EKF geometric self-cancellation.

## Final Verdict
**`C. M043 DIAGNOSTIC ONLY — heading is not sufficiently observable for a justified intervention.`**
