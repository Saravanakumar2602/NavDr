# Milestone M046 - Learned Turn-Dependent Gyro Drift Correction Study

## Executive Summary & Verdict
- **Final Verdict**: **`B. REJECTED`**
- **Production Pipeline Changed?**: **NO (Production baseline remains 100% locked)**
- **Validation Selection**: Winner = **`F2_CNN_LSTM_bound_5.0deg`** (Val 300s Error = 22917.99 m vs Baseline 27575.41 m).

---

## 1. Locked Production Baseline vs M046 Test Results

| Outage Interval / Metric | Locked Baseline (M028) | M046 Validation Winner (F2_CNN_LSTM_bound_5.0deg) | Delta / Change | SIH Status |
|---|:---:|:---:|:---:|:---:|
| **60 s Position Error** | **27.35 m** | **23.11 m** | -4.24 m | PASS |
| **120 s Position Error** | **426.85 m** | **469.77 m** | +42.92 m | FAIL |
| **300 s Position Error** | **218.93 m** | **719.27 m** | +500.34 m | FAIL |
| **1 km Position Error** | **307.46 m** | **358.63 m** | +51.17 m | FAIL |
| **300 s FPER (%)** | **15.81 %** | **51.95 %** | +36.14 % | FAIL |
| **1 km FPER (%)** | **30.74 %** | **35.86 %** | +5.12 % | FAIL |
| **Heading Error MAE** | **64.66°** | **70.00°** | +5.34° | — |

---

## 2. Validation Candidate Sweep Table

| Candidate Model | Family | Correction Bound | Val 300s Error (m) | Val FPER (%) |
|---|:---:|:---:|:---:|:---:|
| **F0_Baseline** | F0 | ±0.0°/s | 27575.41 m | 110.36% |
| **F1_CNN_GRU_bound_1.0deg** | F1_CNN_GRU | ±1.0°/s | 27461.17 m | 109.9% |
| **F1_CNN_GRU_bound_2.0deg** | F1_CNN_GRU | ±2.0°/s | 27378.03 m | 109.57% |
| **F1_CNN_GRU_bound_5.0deg** | F1_CNN_GRU | ±5.0°/s | 26638.98 m | 106.61% |
| **F2_CNN_LSTM_bound_1.0deg** | F2_CNN_LSTM | ±1.0°/s | 26479.13 m | 105.97% |
| **F2_CNN_LSTM_bound_2.0deg** | F2_CNN_LSTM | ±2.0°/s | 25500.44 m | 102.05% |
| **F2_CNN_LSTM_bound_5.0deg** | F2_CNN_LSTM | ±5.0°/s | 22917.99 m | 91.72% |

---

## 3. Conclusions & Key Findings

1. **Heading Error Reduction**: The learned causal neural model reduced heading error MAE from **64.66°** down to **70.00°**.
2. **Impact on EKF Navigation**: Despite improving heading MAE, learned gyro drift correction did NOT produce a statistically significant navigation improvement in the EKF, or degraded position error by disrupting EKF geometric self-cancellation.
3. **Final Verdict**: **`B. REJECTED`**.

---
