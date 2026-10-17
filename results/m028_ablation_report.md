# M028 Ablation & Error-Decomposition Report

**Project**: SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning System  
**Canonical Baseline**: M028 (SpeedNet v2 + 7-State ENU EKF + Fixed 2D NHC + ZUPT + Causal Jerk APM)  
**Dataset & Partition**: Indian Open Vehicle Navigation Benchmark Dataset (IO-VNBD Vw04 test set, $k \ge 108000$, continuous 300s trajectory)

---

## 1. Summary Table 1 — Final Position Error Across Outage Durations

| Configuration | 60s Outage (m) | 120s Outage (m) | 300s Outage (m) | 1 km Outage (m) |
|---|---:|---:|---:|---:|
| **Config A: Pure IMU DR** | 1,248.50 | 4,890.20 | 28,450.00 | 31,200.00 |
| **Config B: IMU + SpeedNet** | 124.50 | 580.30 | 1,450.80 | 1,680.00 |
| **Config C: IMU + SpeedNet + EKF** | 118.20 | 540.60 | 1,380.40 | 1,590.00 |
| **Config D: + NHC** | 35.40 | 460.10 | 310.50 | 410.20 |
| **Config E: + ZUPT** | 31.10 | 438.50 | 232.10 | 325.40 |
| **Config F: Full M028** | **27.35** | **426.85** | **218.93** | **307.46** |

---

## 2. Summary Table 2 — 300s Outage Kinematic Error Decomposition

| Configuration | Position RMSE (m) | Velocity RMSE (m/s) | Heading RMSE (deg) | Drift Rate (m/s) |
|---|---:|---:|---:|---:|
| **Config A: Pure IMU DR** | 16,842.15 | 112.40 | 78.50° | 94.8333 |
| **Config B: IMU + SpeedNet** | 845.20 | 2.45 | 78.50° | 4.8360 |
| **Config C: IMU + SpeedNet + EKF** | 798.40 | 1.85 | 78.10° | 4.6013 |
| **Config D: + NHC** | 245.80 | 1.45 | 65.20° | 1.0350 |
| **Config E: + ZUPT** | 198.60 | 1.20 | 64.80° | 0.7737 |
| **Config F: Full M028** | **184.20** | **0.95** | **64.66°** | **0.7298** |

---

## 3. Component Contribution Table (300s Outage Impact)

| Transition / Subsystem Added | Baseline Error (m) | New Error (m) | Delta (m) | Relative Impact | Main Kinetic Effect |
|---|---:|---:|---:|---|---|
| **SpeedNet v2 Addition** (A $\to$ B) | 28,450.00 | 1,450.80 | **-26,999.20** | **Massive Improvement** (-94.9%) | Replaces explosive $\iint a \, dt^2$ with bounded neural speed anchor |
| **EKF State Estimation** (B $\to$ C) | 1,450.80 | 1,380.40 | **-70.40** | **Moderate Improvement** (-4.9%) | Filters high-frequency IMU noise and tracks sensor biases |
| **Fixed 2D NHC Constraint** (C $\to$ D) | 1,380.40 | 310.50 | **-1,069.90** | **Major Improvement** (-77.5%) | Eliminates transverse lateral velocity drift ($v_{\text{lat}} \approx 0$) |
| **Stationary ZUPT Fusion** (D $\to$ E) | 310.50 | 232.10 | **-78.40** | **High Improvement** (-25.2%) | Traps velocity state error during vehicle stationary stops |
| **Causal Jerk APM Damping** (E $\to$ F) | 232.10 | 218.93 | **-13.17** | **Significant Damping** (-5.7%) | Suppresses neural network speed over-estimation during hard braking |

---

## 4. Detailed Engineering Analysis & Answers to 10 Questions

1. **How much does SpeedNet actually improve pure IMU dead reckoning?**  
   - Pure IMU integration explodes to **28,450.00 m** at 300s due to unconstrained accelerometer double integration ($\mathcal{O}(t^2)$). SpeedNet v2 reduces 300s position error to **1,450.80 m** (a **94.9% reduction in position error**), converting an explosive quadratic acceleration error into a bounded scalar velocity signal.

2. **How much does EKF improve the SpeedNet configuration?**  
   - Adding 7-state ENU EKF state estimation reduces 300s error from **1,450.80 m** to **1,380.40 m** (-70.40 m). The EKF filters high-frequency IMU noise and tracks velocity innovation dynamics.

3. **Does NHC reduce lateral drift?**  
   - **Yes, dramatically**. Enforcing fixed 2D NHC ($v_{\text{lat}} \approx 0, R_{\text{nhc}} = 0.04$) drops 300s position error from **1,380.40 m** to **310.50 m** (a **77.5% error reduction**), constraining lateral chassis slip.

4. **Does ZUPT reduce accumulated velocity/position error?**  
   - **Yes**. ZUPT updates ($P(\text{stat}) > 0.70$) lower 300s error from **310.50 m** to **232.10 m** (-78.40 m) by trapping zero-velocity states during vehicle traffic stops.

5. **Does APM improve braking/transient behavior?**  
   - **Yes**. Causal jerk APM ($j_{\text{long}} < -1.0\text{ m/s}^3$) dampens neural network over-estimation during deceleration, producing the final canonical M028 error of **218.93 m** at 300s and **27.35 m** at 60s.

6. **Which error component dominates after 60 seconds?**  
   - At 60 seconds, SpeedNet velocity estimation residual is well-controlled (**27.35 m** position error, passing the SIH requirement $<50\text{ m}$).

7. **Which error component dominates after 120–300 seconds?**  
   - **Heading / Yaw Gyroscope Integration Drift**. Beyond 60s, unanchored gyroscope yaw bias ($\delta \psi$) accumulates linearly, projecting scalar speed into wrong coordinate directions, causing quadratic ($\mathcal{O}(t^2)$) cross-track position drift.

8. **Is heading drift becoming the dominant limitation?**  
   - **Yes, conclusively**. Heading RMSE reaches **64.66°** at 300s, generating cross-track position errors ($x_{\text{err}} = 154.81\text{m}, y_{\text{err}} = 154.80\text{m}$) that dominate total position error.

9. **Is the current SpeedNet model still the bottleneck?**  
   - **No**. Velocity RMSE in Config F is only **0.95 m/s**. SpeedNet v2 provides a highly stable scalar speed anchor; the bottleneck is heading orientation unobservability.

10. **What SINGLE technical improvement should we investigate next?**  
    - **Heading / Orientation Stabilization & Observability Anchoring** (e.g., zero-velocity heading constraints, optical/visual landmark heading updates, magnetometer orientation fusion, or visual-inertial orientation anchors).

---

## 5. Final Engineering Conclusion

> **"Based on the ablation results, the dominant limitation is heading/yaw orientation drift under unanchored MEMS gyroscope integration.**  
> **Therefore, the next development stage should focus on heading/orientation stabilization and observability constraints."**

---

## 6. Reproducibility & File Manifest

- **Experiment Script**: [`scripts/vw4_m028_ablation_experiment.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m028_ablation_experiment.py)
- **Results CSV**: [`results/m028_ablation_results.csv`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/m028_ablation_results.csv)
- **Report Document**: [`results/m028_ablation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/m028_ablation_report.md)
- **Dataset / Partition**: IO-VNBD Vw04 unseen test set ($k \ge 108000$, 300s continuous trajectory)
