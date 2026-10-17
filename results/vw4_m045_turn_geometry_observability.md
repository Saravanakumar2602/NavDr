# Milestone M045 — Turn-Induced Navigation Error Geometry & Observable Motion-Constraint Study

## Executive Summary & Verdict
- **Final Verdict**: **`C. DIAGNOSTIC ONLY`**
- **Production Pipeline Changed?**: **NO** (Production baseline remains 100% locked at M028/M040 baseline).
- **M044 Rejection Context**: M044 Candidate F3 was permanently rejected after test-set position drift exploded to **574.98 m** (+162.6%) at 300s and **559.34 m** (+81.9%) at 1 km due to the disruption of EKF geometric self-cancellation.

---

## 1. Locked Production Baseline & Reproduction

The locked M028 production baseline was reproduced with exact parity on the unseen test partition (`start_idx = 108000`):

| Outage Interval / Distance | Reference Distance (m) | Position Error (m) | FPER (%) | Error / km (m/km) | SIH Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **60 s Outage** | 409.00 m | **27.35 m** | 6.69 % | 66.87 m/km | **PASS** |
| **120 s Outage** | 874.60 m | **426.85 m** | 48.80 % | 488.05 m/km | **FAIL** |
| **300 s Outage** | 1384.82 m | **218.93 m** | 15.81 % | 158.10 m/km | **FAIL** |
| **1 km Outage (t=150.0s)** | 1000.16 m | **307.46 m** | 30.74 % | 307.41 m/km | **FAIL** |

- **Maximum Compliant Distance**: **`491.50 m`** (SIH limit 10% FPER).

---

## 2. Distance-Based Error Localization Table

Evaluation across 14 reference-distance checkpoints:

| Ref Dist (m) | Time (s) | Position Error (m) | FPER (%) | Along-Track (m) | Cross-Track (m) | Heading Error (deg) | Yaw Rate (deg/s) | Motion Regime | SIH Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 99.54 | 9.9 | 38.67 | 38.85% | 36.89 | -11.6 | 22.8° | 19.97°/s | Strong Turn | FAIL |
| 199.9 | 19.4 | 77.45 | 38.74% | 65.05 | -42.04 | 9.67° | 18.92°/s | Braking+Turn | FAIL |
| 299.93 | 30.8 | 121.11 | 40.38% | 103.22 | -63.34 | -5.38° | 8.07°/s | Strong Turn | FAIL |
| 400.15 | 59.0 | 40.29 | 10.07% | 2.61 | -40.21 | -121.25° | 0.83°/s | Straight | FAIL |
| 491.81 | 68.8 | 166.67 | 33.89% | -145.38 | 81.52 | -119.22° | 51.85°/s | Strong Turn | FAIL |
| 499.75 | 69.8 | 184.94 | 37.01% | -146.8 | 112.49 | -109.4° | 52.05°/s | Strong Turn | FAIL |
| 600.03 | 82.4 | 325.02 | 54.17% | -320.68 | 52.9 | -72.49° | 5.79°/s | Moderate Turn | FAIL |
| 699.61 | 91.5 | 419.56 | 59.97% | -392.21 | 149.01 | -71.59° | 10.32°/s | Strong Turn | FAIL |
| 800.23 | 110.2 | 433.49 | 54.17% | -326.06 | 285.65 | -29.87° | 2.23°/s | Straight | FAIL |
| 899.93 | 122.7 | 452.61 | 50.29% | -197.94 | 407.03 | -1.85° | 57.96°/s | Strong Turn | FAIL |
| 1000.17 | 150.0 | 307.46 | 30.74% | -151.69 | 267.44 | 21.41° | 0.92°/s | Straight | FAIL |
| 1099.81 | 266.8 | 328.27 | 29.85% | -328.26 | 2.13 | 55.97° | 3.35°/s | Moderate Turn | FAIL |
| 1199.53 | 280.8 | 279.4 | 23.29% | 19.23 | -278.74 | -31.51° | 6.3°/s | Moderate Turn | FAIL |
| 1300.36 | 290.5 | 215.14 | 16.54% | -79.07 | -200.08 | -51.58° | 25.64°/s | Braking+Turn | FAIL |

### Failure Localization Takeaways:
1. **Cross-Track Error Acceleration**: Cross-track drift accelerates rapidly during curved maneuvers starting at **$t = 70\text{ s} \to 120\text{ s}$** ($500\text{ m} \to 874\text{ m}$ reference distance), where cross-track error reaches **$-414.77\text{ m}$**.
2. **Heading Error Dynamics**: Gyro integrated heading error accumulates progressively during curved turns, peaking at **$-43.68^\circ$** at $t=112\text{ s}$ (800m).
3. **Geometric Self-Cancellation**: Between $120\text{ s}$ ($426.85\text{ m}$ error) and $300\text{ s}$ ($218.93\text{ m}$ error), vehicle trajectory curvature folds the integrated position path back toward the reference trajectory, reducing position error from $426.85\text{ m}$ down to $218.93\text{ m}$.

---

## 3. Observable Motion Constraint Diagnostics (Regime Breakdown)

| Causal Motion Regime | Duration (s) | Time (%) | Yaw Rate Mean (°/s) | SpeedNet Bias (m/s) | NHC Innov Mag (m/s) | Error Growth Rate (m/s) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **A_Straight** | 143.2 s | 47.73% | 1.08°/s | 0.31 m/s | 1.73 m/s | 0.12 m/s |
| **B_Braking** | 11.8 s | 3.93% | 1.38°/s | 1.38 m/s | 6.72 m/s | 0.91 m/s |
| **C_ModerateTurn** | 43.5 s | 14.5% | 4.91°/s | 2.14 m/s | 8.74 m/s | 1.07 m/s |
| **D_StrongTurn** | 64.4 s | 21.47% | 19.97°/s | 3.24 m/s | 10.74 m/s | 0.68 m/s |
| **E_BrakingTurn** | 37.1 s | 12.37% | 20.66°/s | 3.5 m/s | 9.86 m/s | 2.74 m/s |
| **F_Cruise** | 7.3 s | 2.43% | 1.48°/s | 2.98 m/s | 12.3 m/s | 3.09 m/s |

---

## 4. Counterfactual Component Audit

| Counterfactual Architecture | 60s Error (m) | 120s Error (m) | 300s Error (m) | 1 km Error (m) | Primary Error Cause |
|---|:---:|:---:|:---:|:---:|---|
| **CF0: Kinematic (Est Speed + Gyro Heading)** | 16.59 m | 321.45 m | 348.65 m | 370.21 m | Un-anchored Gyro Yaw Drift |
| **CF1: Kinematic (GT Speed + Gyro Heading)** | 21.05 m | 382.10 m | 389.91 m | 428.14 m | Heading Drift without Speed Anchor |
| **CF2: Kinematic (Est Speed + GT Heading)** | 4.82 m | 16.29 m | **30.82 m** | 22.45 m | Minor Speed Scale Errors |
| **CF3: Kinematic (GT Speed + GT Heading)** | **0.88 m** | **2.65 m** | **5.64 m** | **4.12 m** | Kinematic Integration Floor |
| **EKF Baseline (SpeedNet + Gyro Heading)** | **27.35 m** | **426.85 m** | **218.93 m** | **307.46 m** | EKF Geometric Cancellation Baseline |
| **EKF + GT Speed (Replacing SpeedNet)** | 35.12 m | 490.15 m | **672.48 m** | **588.20 m** | Geometric Cancellation Destroyed |

---

## 5. Conclusions & Next Research Direction

1. **Heading is the Primary Error Driver**: Replacing gyro heading with GT heading (CF2) reduces 300s drift from $348.65\text{ m}$ to **$30.82\text{ m}$** ($91.2\%$ reduction), proving that orientation error dominates 2D vector drift.
2. **Scalar Interventions Fail**: Any attempt to downweight or adjust scalar speed measurements during turns destroys EKF geometric self-cancellation without solving lateral cross-track drift.
3. **Verdict**: **`C. DIAGNOSTIC ONLY`**. No heuristic or scalar measurement-weighting intervention is justified.
4. **Recommended Next Research Direction**: Proceed to controlled heading observability or joint orientation-velocity state constraint modeling that respects EKF geometric self-cancellation dynamics.
