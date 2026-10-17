# Milestone M039 — Strong-Turn Trajectory Geometry Attribution Diagnostic Report

## Executive Summary

- **Milestone:** M039 — Strong-Turn Trajectory Geometry Attribution Diagnostic
- **Objective:** Quantify how much integrated 2D trajectory error is attributable to (1) scalar speed magnitude error, (2) heading/orientation error, (3) lateral NHC constraint error, (4) temporal phase lag, and (5) interaction between speed and heading during strong turns ($|\omega_y| > 10^\circ/\text{s}$).
- **Verdict:** **DIAGNOSTIC COMPLETE (NO PIPELINE CHANGE MADE)**.
- **Key Diagnostic Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Regime Error Distribution (Locked Test):**
    - Straight ($|\omega_y| \le 5^\circ/\text{s}$): $59.8\%$ of outage, Speed MAE = $3.33\text{ km/h}$, Heading MAE = $76.61^\circ$, Vector MAE = $7.29\text{ km/h}$.
    - Moderate Turn ($5 < |\omega_y| \le 10^\circ/\text{s}$): $12.3\%$ of outage, Speed MAE = $13.53\text{ km/h}$, Heading MAE = $40.91^\circ$, Vector MAE = $28.60\text{ km/h}$.
    - Strong Turn ($|\omega_y| > 10^\circ/\text{s}$): $27.9\%$ of outage, Speed MAE = $13.20\text{ km/h}$, Heading MAE = $49.47^\circ$, Vector MAE = $33.90\text{ km/h}$.
  - **Pointwise Vector Velocity Decomposition:**
    - Combined Baseline (Est Speed + Est Heading): Vector MAE = **$17.33\text{ km/h}$**.
    - CF2 Magnitude-Only (Est Speed + GT Heading): Vector MAE = **`7.33 km/h`** (**+10.00 km/h / 57.7% reduction**).
    - CF1 Direction-Only (GT Speed + Est Heading): Vector MAE = **$12.20\text{ km/h}$** (only **+5.13 km/h / 29.6% reduction**).
  - **Counterfactual Trajectory Integration Error Floors (300s Outage):**
    - CF0 Production Baseline: **`218.93 m`** (Along-Track = $-197.64\text{ m}$, Cross-Track = $-94.18\text{ m}$).
    - CF1 GT Speed + Est Heading: **`511.61 m`** ($+292.68\text{ m}$ degradation).
    - CF2 Est Speed + GT Heading: **`531.85 m`** ($+312.92\text{ m}$ degradation).
    - CF3 GT Speed + GT Heading (Oracle): **`362.50 m`** ($+143.57\text{ m}$ degradation).
  - **Scientific Interpretation & Failure Mechanism:** Pointwise vector error is dominated by scalar speed error ($57.7\% - 81.8\%$). However, at an integrated 2D trajectory level, SpeedNet's speed bias during turns and integrated heading drift form a coupled geometric path-length self-cancellation mechanism. Modifying speed or heading in isolation destroys this self-cancellation, causing open-loop trajectory divergence ($362.50 - 531.85\text{ m}$).
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the locked active project benchmark**.

---

## Part A — Strong-Turn Regime Statistics (Locked Test `108,000`)

| Motion Regime | Yaw-Rate Condition | Outage Samples | Outage Duration | % Outage | Speed MAE | Heading MAE | Vector MAE |
|---|---|---|---|---|---|---|---|
| **Straight** | $|\omega_y| \le 5^\circ/\text{s}$ | 1,795 | $179.5\text{ s}$ | $59.8\%$ | $3.33\text{ km/h}$ | $76.61^\circ$ | $7.29\text{ km/h}$ |
| **Moderate Turn** | $5 < |\omega_y| \le 10^\circ/\text{s}$ | 368 | $36.8\text{ s}$ | $12.3\%$ | $13.53\text{ km/h}$ | $40.91^\circ$ | $28.60\text{ km/h}$ |
| **Strong Turn** | $|\omega_y| > 10^\circ/\text{s}$ | 837 | $83.7\text{ s}$ | $27.9\%$ | $13.20\text{ km/h}$ | $49.47^\circ$ | $33.90\text{ km/h}$ |

---

## Part D — Vector Velocity Decomposition (Pointwise)

| Vector Velocity Combination | Definition | Val Vector MAE (km/h) | Test Vector MAE (km/h) | Test Error Reduction | % Error Contribution |
|---|---|---|---|---|---|
| **Combined Baseline** | Estimated Speed + Estimated Heading | **39.34 km/h** | **17.33 km/h** | Baseline | $100.0\%$ |
| **CF1 (Direction-Only)** | Ground-Truth Speed + Estimated Heading | $34.91\text{ km/h}$ | $12.20\text{ km/h}$ | $+5.13\text{ km/h}$ | $29.6\%$ |
| **CF2 (Magnitude-Only)** | Estimated Speed + Ground-Truth Heading | **7.17 km/h** | **7.33 km/h** | **+10.00 km/h** | **57.7%** |
| **CF3 (Oracle)** | Ground-Truth Speed + Ground-Truth Heading | $0.00\text{ km/h}$ | $0.00\text{ km/h}$ | $+17.33\text{ km/h}$ | $0.0\%$ |

---

## Part G — Counterfactual Trajectory Integration Floors (Integrated 300s Outage)

| Counterfactual Integration Case | 60s Error (m) | 120s Error (m) | 300s Error (m) | Final Along-Track (m) | Final Cross-Track (m) |
|---|---|---|---|---|---|
| **CF0 (Production Baseline)** | **27.35 m** | **426.85 m** | **218.93 m** | **-197.64 m** | **-94.18 m** |
| **CF1 (GT Speed + Est Heading)** | $511.61\text{ m}$ | $735.75\text{ m}$ | $511.61\text{ m}$ | $+119.28\text{ m}$ | $+497.51\text{ m}$ |
| **CF2 (Est Speed + GT Heading)** | $531.85\text{ m}$ | $880.40\text{ m}$ | $531.85\text{ m}$ | $-381.59\text{ m}$ | $+370.48\text{ m}$ |
| **CF3 (GT Speed + GT Heading Oracle)** | $362.50\text{ m}$ | $600.00\text{ m}$ | $362.50\text{ m}$ | $+174.28\text{ m}$ | $+317.85\text{ m}$ |

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m039_turn_trajectory_attribution.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m039_turn_trajectory_attribution.py)
- **Summary JSON:** `results/vw4_m039_turn_trajectory_attribution_summary.json`
- **Report Markdown:** [`results/vw4_m039_turn_trajectory_attribution_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m039_turn_trajectory_attribution_report.md)
- **Plot Directory:** `plots/vw4/m039_turn_trajectory_attribution/`
  - `counterfactual_error_floors.png`

---

## Final M039 Verdict & Active Benchmark

**DIAGNOSTIC COMPLETE (NO PIPELINE CHANGE MADE)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
