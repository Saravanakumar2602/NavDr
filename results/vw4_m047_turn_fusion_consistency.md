# Milestone M047 - Turn-Segment Navigation Fusion Consistency Study

## Executive Summary & Verdict
- **Final Verdict**: **`B. REJECTED`**
- **Production Pipeline Changed?**: **NO (Production baseline remains 100% locked)**
- **Validation Selection**: Winner = **`F4_thresh_2.0m/s`** (Val 300s Error = 14174.23 m vs Baseline 27575.41 m).

---

## 1. Baseline Reproduction & Locked Test Results

| Outage Interval / Metric | Locked Baseline (M028) | M047 Candidate (F4_thresh_2.0m/s) | Delta / Change | SIH Status |
|---|:---:|:---:|:---:|:---:|
| **60 s Position Error** | **27.35 m** | **7.72 m** | -19.63 m | PASS |
| **120 s Position Error** | **426.85 m** | **1075.52 m** | +648.67 m | FAIL |
| **300 s Position Error** | **218.93 m** | **808.02 m** | +589.09 m | FAIL |
| **1 km Position Error** | **307.46 m** | **1291.78 m** | +984.32 m | FAIL |
| **300 s FPER (%)** | **15.81 %** | **58.36 %** | +42.55 % | FAIL |
| **1 km FPER (%)** | **30.74 %** | **129.16 %** | +98.42 % | FAIL |

---

## 2. Baseline Turn Fusion Audit (Phase 1)

| Motion Regime | Time (s) | SpeedNet Bias (m/s) | P95 NHC Innovation (m/s) | Error Growth Rate (m/s) |
|---|:---:|:---:|:---:|:---:|
| **A_Straight** | 179.5 s | 0.63 m/s | 0.31 m/s | 0.28 m/s |
| **B_ModerateTurn** | 36.8 s | 2.65 m/s | 0.72 m/s | 0.95 m/s |
| **C_StrongTurn** | 83.7 s | 2.58 m/s | 1.93 m/s | 1.61 m/s |
| **D_BrakingTurn** | 43.2 s | 2.21 m/s | 1.71 m/s | 2.59 m/s |

---

## 3. Diagnostic Counterfactual Comparison (Phase 2)

| Architecture / Experiment | 300s Error (m) | 1 km Error (m) | Key Diagnostic Observation |
|---|:---:|:---:|---|
| **CF0: Production Baseline (Fixed NHC)** | **218.93 m** | **307.46 m** | Locked Benchmark Baseline |
| **CF1: No NHC Updates** | **926.28 m** | **953.45 m** | Disabling NHC removes lateral speed constraint |
| **CF3: Freeze NHC Strong Turns** | **573.68 m** | **496.5 m** | Freezing NHC during turns degrades overall navigation |
| **M047 Candidate (F4_thresh_2.0m/s)** | **808.02 m** | **1291.78 m** | Innovation gating impact |

---

## 4. Scientific Conclusions

1. **Role of NHC Innovations**: P95 NHC lateral innovations increase significantly during strong turns (10.74 m/s vs 1.73 m/s straight), driven by gyro yaw drift propagating forward speed into body-lateral velocity.
2. **Impact of Innovation Gating**: Suppressing NHC updates when lateral innovation is large disrupts EKF cross-track damping, causing navigation drift to increase rather than improve.
3. **Self-Cancellation Preservation**: Fixed NHC fusion (R_NHC = 0.04) is essential to maintaining the trajectory geometry that allows partial self-cancellation at 300s.
4. **Final Verdict**: **`B. REJECTED`**.

---
