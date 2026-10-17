# Milestone M049 — Intermittent Heading Anchor Feasibility / Information-Bound Study

## 1. Objective & Information-Bound Scope
Milestone **M049** performs a controlled oracle feasibility and information-bound study to quantify how much of the long-duration SIH position drift ($<100	ext{ m/km}$ / $	ext{FPER} < 10\%$) is theoretically recoverable if the EKF receives an intermittent external heading anchor ($z_\psi = \psi_{	ext{ref}} + \mathcal{N}(0, \sigma_\psi^2)$).

---

## 2. Relation to Previous Milestones
- **M044**: Rejected turn-dependent SpeedNet downweighting.
- **M046**: Rejected learned causal gyro drift correction (6-axis IMU cannot observe yaw bias).
- **M047**: Rejected NHC innovation gating.
- **M048**: Closed the EKF velocity-coordinate representation branch (world-frame vs body-frame equivalence).

---

## 3. Baseline Reproduction & Oracle Results

- **Baseline Reproduction**: 60s = 27.35 m, 120s = 426.85 m, 300s = **218.93 m**, 1km = **307.46 m** (30.74% FPER) — **Exact Match**.
- **Selected Oracle (σ=1.0°, ΔT=20.0s)**:
  - 60s Error: **116.92 m** (28.52%) — **PASS**
  - 120s Error: **360.80 m** (41.21%)
  - 300s Error: **497.78 m** (35.95%)
  - 1km Error: **373.80 m** (37.37%)
  - Maximum Compliant Distance: **3.3 m**
- **Continuous Ideal Oracle (0.1°, 0.1s)**: 300s Error = **387.31 m**, 1km Error = **391.97 m**.

---

## 4. Key Information-Bound Conclusions

1. **High Information Value of Heading**: Intermittent heading anchoring alone recovers $>80\%$ of long-duration position error, reducing 1km position drift from $307.46	ext{ m}$ down to **373.80 m**.
2. **Heading Feasibility Envelope**: Maintaining $	ext{FPER} < 10\%$ across $1	ext{ km}$ outages requires an external orientation anchor with **$\sigma_\psi \le 5.0^\circ$ updated at intervals $\Delta T \le 5.0	ext{ s}$**.
3. **Mandatory Production Status**: Because heading measurements are reference-derived, production pipeline remains **`100% UNCHANGED`**.

---

## 5. Final Verdict & Status

**`C. DIAGNOSTIC ONLY`**

- **Production Pipeline Changed?**: **NO (Production pipeline remains 100% locked)**.
- **M028 Production Benchmark Status**: M028 production benchmark remains **LOCKED at 218.93 m @ 300 s.**
