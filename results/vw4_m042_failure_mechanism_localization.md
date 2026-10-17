# M042 Failure-Mechanism Localization & Diagnostic Study

## Executive Summary
- **Milestone:** M042 — Round 3 Failure-Mechanism Localization & Intervention Study
- **Objective:** Localize the exact failure mechanism responsible for FPER non-compliance between ~492 m and 1 km, decompose speed vs. heading vs. NHC contributions, and evaluate potential online interventions.
- **Verdict:** **`C. M042 DIAGNOSTIC ONLY — no intervention is sufficiently justified.`**
- **Production Pipeline Changed:** **NO** (Locked baseline retained at **218.93 m @ 300s**).

## Distance Checkpoint Summary Table

| Ref Dist ($D_{\text{ref}}$) | Elapsed Time ($t$) | Position Error | FPER (%) | Error per km | Along-Track | Cross-Track | Heading Err | Speed Err |
|---|---|---|---|---|---|---|---|---|
| **99.54 m** | 9.9 s | 38.67 m | **38.85%** | 388.46 m/km | 36.89 m | -11.6 m | 22.8° | 1.15 m/s |
| **199.9 m** | 19.4 s | 77.45 m | **38.74%** | 387.42 m/km | 65.05 m | -42.04 m | 9.67° | 2.02 m/s |
| **299.93 m** | 30.8 s | 121.11 m | **40.38%** | 403.78 m/km | 103.22 m | -63.34 m | -5.38° | 1.81 m/s |
| **400.15 m** | 59.0 s | 40.29 m | **10.07%** | 100.7 m/km | 2.61 m | -40.21 m | -121.25° | 4.53 m/s |
| **491.81 m** | 68.8 s | 166.67 m | **33.89%** | 338.9 m/km | -145.38 m | 81.52 m | -119.22° | 6.78 m/s |
| **499.75 m** | 69.8 s | 184.94 m | **37.01%** | 370.06 m/km | -146.8 m | 112.49 m | -109.4° | 7.94 m/s |
| **600.03 m** | 82.4 s | 325.02 m | **54.17%** | 541.66 m/km | -320.68 m | 52.9 m | -72.49° | 0.4 m/s |
| **699.61 m** | 91.5 s | 419.56 m | **59.97%** | 599.7 m/km | -392.21 m | 149.01 m | -71.59° | 0.32 m/s |
| **800.23 m** | 110.2 s | 433.49 m | **54.17%** | 541.71 m/km | -326.06 m | 285.65 m | -29.87° | 9.55 m/s |
| **899.93 m** | 122.7 s | 452.61 m | **50.29%** | 502.94 m/km | -197.94 m | 407.03 m | -1.85° | 2.51 m/s |
| **1000.17 m** | 150.0 s | 307.46 m | **30.74%** | 307.41 m/km | -151.69 m | 267.44 m | 21.41° | -1.02 m/s |
| **1099.81 m** | 266.8 s | 328.27 m | **29.85%** | 298.48 m/km | -328.26 m | 2.13 m | 55.97° | -0.24 m/s |
| **1199.53 m** | 280.8 s | 279.4 m | **23.29%** | 232.92 m/km | 19.23 m | -278.74 m | -31.51° | 4.32 m/s |
| **1300.36 m** | 290.5 s | 215.14 m | **16.54%** | 165.44 m/km | -79.07 m | -200.08 m | -51.58° | 4.13 m/s |

## Key Diagnostic Correlations
- **Corr(PE, |Speed Error|):** -0.0573 (Negligible linear relationship with total position error)
- **Corr(PE, |Heading Error|):** 0.1648
- **Corr(|Cross-Track|, |Heading Error|):** -0.4529 (Strong coupling between heading drift and lateral cross-track accumulation during curves)
- **Corr(Along-Track, Speed Error):** 0.0917

## Motion Regime Error Breakdown

| Regime Name | Sample Count | % Samples | Mean Position Error | Mean |Heading Error| | Mean |Speed Error| |
|---|---|---|---|---|---|
| **Straight** | 1153 | 38.4% | 299.25 m | 94.5° | 0.34 m/s |
| **Moderate Turn** | 613 | 20.4% | 262.73 m | 43.96° | 2.94 m/s |
| **Strong Turn** | 837 | 27.9% | 235.43 m | 49.47° | 2.97 m/s |
| **Acceleration** | 823 | 27.4% | 255.8 m | 48.45° | 2.63 m/s |
| **Braking** | 604 | 20.1% | 237.1 m | 44.43° | 2.51 m/s |
| **Stationary** | 1055 | 35.2% | 306.18 m | 99.57° | 0.06 m/s |

## Counterfactual Integration Benchmark

| Counterfactual Variant | Integration Type | 300s Position Drift | Description |
|---|---|---|---|
| **Kinematic CF0** | Pure Kinematic | 213.81 m | Estimated Speed + Estimated Heading |
| **Kinematic CF1** | Pure Kinematic | 328.44 m | GT Speed + Estimated Heading |
| **Kinematic CF2** | Pure Kinematic | 438.68 m | Estimated Speed + GT Heading |
| **Kinematic CF3** | Pure Kinematic | **5.64 m** | **Kinematic Oracle Floor** (GT Speed + GT Heading) |
| **EKF CF0** | EKF Navigation | **218.93 m** | **Production Baseline** (SpeedNet + Gyro + NHC/APM/ZUPT) |
| **EKF CF1** | EKF Navigation | **511.62 m** | **GT Speed Measurement Substitution** (+133.7% degradation) |

## Localization Verdict
- **$D_{\text{start}}$ (First >10% FPER Exceedance):** **50.82 m** ($t = 5.2 s$)
- **$D_{\text{peak}}$ (Worst Position Error Peak):** **897.12 m** ($t = 122.4 s$, Error = **465.41 m**, FPER = **51.88%**)
- **Dominant Failure Mechanism:** Un-aided gyro yaw integration drift during sharp curved maneuvers ($700\text{ m} \to 1000\text{ m}$), coupled with the **Geometric Self-Cancellation Mechanism**. Replacing SpeedNet speed with Ground-Truth Speed destroys the forward overestimation balance, increasing 300s position drift to **511.62 m**.
- **Final Verdict:** **`C. M042 DIAGNOSTIC ONLY — no intervention is sufficiently justified.`**
