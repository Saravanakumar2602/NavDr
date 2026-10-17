# Milestone M047 — Turn-Segment Navigation Fusion Consistency Study

## 1. Objective & Background
Milestone **M047** investigates whether the EKF/NHC fusion architecture is internally inconsistent during turn/deceleration segments by evaluating whether fusing or gating NHC lateral velocity updates during turns improves distance-normalized navigation without modifying SpeedNet or gyro heading.

---

## 2. Relation to Previous Milestones
- **M032**: Established that NHC innovation increases strongly with yaw rate.
- **M040**: Corrected counterfactual auditing, proving SpeedNet forward speed overestimation provides an along-track anchor.
- **M043**: Established transient drift dynamics and non-monotonicity.
- **M044**: Permanently rejected SpeedNet variance downweighting (R_v x 10.0) during turns.
- **M045**: Established turn geometry, showing cross-track acceleration peaks during turns.
- **M046**: Permanently rejected learned causal gyro drift correction.

---

## 3. Exact Baseline Reproduction

- **60s Outage**: 27.35 m (Independent) / 27.88 m (Continuous) — **PASS**
- **120s Outage**: 426.85 m — **FAIL**
- **300s Outage**: **218.93 m** — **Exact Match**
- **1km Outage**: **307.46 m** (30.74% FPER) — **Exact Match**
- **Maximum Compliant Distance**: **`491.50 m`**

---

## 4. Experimental Results & Validation Selection

- **Validation Selection**: Candidate **`F4_thresh_2.0m/s`** selected on validation partition.
- **Locked Test Evaluation**:
  - 60s Error: **7.72 m** (Baseline: 27.35 m)
  - 120s Error: **1075.52 m** (Baseline: 426.85 m)
  - 300s Error: **808.02 m** (Baseline: 218.93 m)
  - 1km Error: **1291.78 m** (129.16%) (Baseline: 307.46 m / 30.74%)

---

## 5. Final Verdict & Status

**`B. REJECTED`**

- **Production Pipeline Changed?**: **NO (Production baseline remains 100% locked)**.
- **Next Research Direction**: Respect EKF geometric self-cancellation and maintain locked production baseline while exploring zero-velocity orientation anchoring or joint state observability in future work.
