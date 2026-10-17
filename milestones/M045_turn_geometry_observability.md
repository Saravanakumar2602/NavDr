# Milestone M045 — Turn-Induced Navigation Error Geometry & Observable Motion-Constraint Study

## 1. Hypothesis & Research Intent
Milestone **M045** performs a comprehensive diagnostic investigation into how heading/yaw error interacts with vehicle curvature and velocity to create distance-normalized position drift ($<100\text{ m/km}$ / $\text{FPER} < 10\%$). The objective is to understand the exact geometry of turn-induced errors without retuning M044, training new models, or introducing non-causal measurements.

---

## 2. Locked Production Baseline & M044 Rejection Context

- **Locked Production Baseline**:
  $$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro Yaw} + \text{Fixed 2D NHC } (R=0.04) + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate}$$

- **M044 Rejection Summary**: Candidate F3 downweighted SpeedNet ($R_v \times 10.0$) during turns. It was permanently **REJECTED** because 300s position drift exploded from **$218.93\text{ m}$ to $574.98\text{ m}$ (+162.6%)** on the locked unseen test set by destroying EKF geometric self-cancellation.

---

## 3. Phase 0 Baseline Reproduction

- **60 s Outage**: $27.35\text{ m}$ (Independent) / $27.88\text{ m}$ (Continuous 300s slice) — **PASS**
- **120 s Outage**: $426.85\text{ m}$ (Independent) / $426.17\text{ m}$ (Continuous 300s slice) — **FAIL**
- **300 s Outage**: **$218.93\text{ m}$** — **Exact Match**
- **1 km Outage ($t=150.0\text{ s}$)**: **$307.46\text{ m}$** ($30.74\%$ FPER / $307.41\text{ m/km}$) — **Exact Match**
- **Maximum Compliant Distance**: **`491.50 m`**

---

## 4. Distance-Based Failure Localization & Turn Geometry

During curved maneuvers between $t = 70\text{ s}$ and $t = 120\text{ s}$ (reference distance $500\text{ m} \to 874\text{ m}$):
1. **Gyro Yaw Drift Accumulation**: Un-aided gyro yaw integration drift reaches $-43.68^\circ$ at $t=112\text{ s}$ ($800\text{ m}$).
2. **Cross-Track Error Explosion**: The orientation error rotates the forward velocity vector into the lateral direction, driving cross-track error to **$-414.77\text{ m}$** at $120\text{ s}$ ($874\text{ m}$).
3. **Geometric Self-Cancellation Dynamics**: Between $120\text{ s}$ and $300\text{ s}$, vehicle curvature reverses the vehicle orientation, causing along-track and cross-track drift components to partially cancel out, pulling total position drift back down to **$218.93\text{ m}$** at $300\text{ s}$.

---

## 5. Counterfactual Component Audit

| Architecture | 60s Error | 120s Error | 300s Error | 1 km Error | Dominant Impact |
|---|:---:|:---:|:---:|:---:|---|
| **CF0: Kinematic (Est Speed + Gyro Heading)** | 16.59 m | 321.45 m | 348.65 m | 370.21 m | Gyro Yaw Drift Baseline |
| **CF1: Kinematic (GT Speed + Gyro Heading)** | 21.05 m | 382.10 m | 389.91 m | 428.14 m | No Speed Anchor |
| **CF2: Kinematic (Est Speed + GT Heading)** | 4.82 m | 16.29 m | **30.82 m** | 22.45 m | **91.2% Drift Reduction** |
| **CF3: Kinematic (GT Speed + GT Heading)** | 0.88 m | 2.65 m | **5.64 m** | 4.12 m | Kinematic Floor |
| **EKF Baseline (SpeedNet + Gyro Heading)** | **27.35 m** | **426.85 m** | **218.93 m** | **307.46 m** | Locked Benchmark |
| **EKF + GT Speed (Replacing SpeedNet)** | 35.12 m | 490.15 m | **672.48 m** | **588.20 m** | Geometric Cancellation Destroyed |

---

## 6. Final Verdict & Next Research Direction

**`C. DIAGNOSTIC ONLY`**

- **Production Pipeline Changed?**: **NO**.
- **Key Insight**: Heading error is the sole fundamental cause of the 1 km FPER explosion. Scalar measurement manipulation during turns is proven to worsen navigation error by destroying EKF geometric self-cancellation.
- **Next Research Direction**: Research heading observability bounds or zero-velocity orientation anchoring in subsequent controlled milestones.
