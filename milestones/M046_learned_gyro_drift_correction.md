# Milestone M046 — Learned Turn-Dependent Gyro Drift Correction Study

## 1. Hypothesis & Research Intent
Milestone **M046** investigates whether a causal neural model can learn a turn-dependent correction to the integrated gyro yaw rate using only observable IMU/SpeedNet motion features without using VBOX heading as a runtime measurement or claiming absolute yaw observability.

---

## 2. Locked Production Baseline & Phase 0 Reproduction

- **Locked Baseline**: SpeedNet v2 (W=40) + Raw Gyro Yaw + Fixed 2D NHC + M013 F4 + M014 ZUPT + M019 APM + M028 Jerk Gate.
- **Reproduction**:
  - 60s Outage: 27.35 m (Independent) / 27.88 m (Continuous) — **PASS**
  - 120s Outage: 426.85 m — **FAIL**
  - 300s Outage: 218.93 m — **Exact Match**
  - 1km Outage: 307.46 m (30.74% FPER) — **Exact Match**

---

## 3. Validation Selection & Locked Test Results

- **Validation Selection**: Candidate **`F2_CNN_LSTM_bound_5.0deg`** selected on validation data.
- **Locked Test Results**:
  - 60s Error: **23.11 m** (Baseline: 27.35 m)
  - 120s Error: **469.77 m** (Baseline: 426.85 m)
  - 300s Error: **719.27 m** (Baseline: 218.93 m)
  - 1km Error: **358.63 m** (35.86%) (Baseline: 307.46 m / 30.74%)

---

## 4. Final Verdict

**`B. REJECTED`**

- **Production Pipeline Changed?**: **NO**.
- **Next Research Direction**: Proceed to subsequent controlled milestones respecting EKF geometric self-cancellation dynamics.
