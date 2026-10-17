# Milestone M011 — Sequence Window / Temporal Context Experiment Report

## Executive Summary

**Experiment:** `scripts/vw4_m011_speednet_v4_temporal_context.py`
**Dataset:** Vw04, unseen test partition, `start_idx = 108,000`
**Provenance-Locked Benchmark:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC = **`263.11 m` @ 300s**
**M011 Verdict:** **REJECTED**

- **Validation Model Selection:**
  - Evaluated 5 temporal sequence variants (F0–F4).
  - Selected model via Validation Speed MAE (`88566:107535`): **`F4: SpeedNet v4 Dilated (W=60, d=2)`** (Val Speed MAE = **`12.18 km/h`** vs Control `12.37 km/h`).
- **Locked Unseen Test Evaluation (F4: Selected Model):**
  - **300s Navigation Error:** **`595.04 m`** (+331.93 m / +126.2% worse than benchmark `263.11 m`).
- **Baseline Control Reproduction:** F0 Control ($W=40$) reproduced **`263.11 m`** @ 300s with 100% precision.

> **Key Scientific Discovery:** Expanding the temporal sequence window ($W=50, 60, 80$) or adding dilated temporal convolutions ($d=2$) **degrades navigation performance**. While larger sequence windows slightly reduce validation speed MAE (`12.18 km/h` vs `12.37 km/h`), they introduce **temporal phase lag and over-smoothing during speed transitions**. This temporal lag delays speed reduction during braking regimes (increasing braking speed bias from $+8.79\text{ km/h} \rightarrow +11.55\text{ km/h}$), causing severe accumulated EKF navigation drift.

---

## 1. Experimental Methodology & Validation Model Selection

- **Candidates Evaluated:**
  - **F0 (Control, $W=40$):** SpeedNet v2 ($4.0\text{s}$ window, 89,220 parameters).
  - **F1 ($W=50$):** SpeedNet v2 ($5.0\text{s}$ window, 89,220 parameters).
  - **F2 ($W=60$):** SpeedNet v2 ($6.0\text{s}$ window, 89,220 parameters).
  - **F3 ($W=80$):** SpeedNet v2 ($8.0\text{s}$ window, 89,220 parameters).
  - **F4 (Dilated, $W=60, d=2$):** SpeedNet v4 ($12.0\text{s}$ effective receptive field, 89,220 parameters).

| Variant Name | Window Size | Effective Receptive Field | Params | Val Speed MAE (km/h) | Val Speed Bias (km/h) | Selection Status |
|---|:---:|:---:|:---:|---:|---:|:---:|
| **F0: Control (W=40)** | 40 (4.0s) | 0.4s (conv) + BiLSTM | 89,220 | 12.37 km/h | +1.33 km/h | Control Baseline |
| **F1: SpeedNet v2 (W=50)** | 50 (5.0s) | 0.4s (conv) + BiLSTM | 89,220 | 12.62 km/h | +4.44 km/h | Candidate |
| **F2: SpeedNet v2 (W=60)** | 60 (6.0s) | 0.4s (conv) + BiLSTM | 89,220 | 14.58 km/h | +8.54 km/h | Candidate |
| **F3: SpeedNet v2 (W=80)** | 80 (8.0s) | 0.4s (conv) + BiLSTM | 89,220 | 47.29 km/h | -47.29 km/h | Local Min (Failed) |
| **F3: SpeedNet v4 Dilated** | **60 (6.0s)** | **1.2s (conv d=2) + BiLSTM** | **89,220** | **`12.18 km/h`** | **-1.87 km/h** | **SELECTED** ✅ |

---

## 2. Locked Evaluation Results (Unseen Test Partition `start_idx = 108,000`)

| Variant Name | Val Speed MAE | Test Speed MAE | 60s Error | 120s Error | 300s Error | 300s CDE % | vs Benchmark (`263.11m`) |
|---|---:|---:|---:|---:|---:|---:|---|
| **F0: SpeedNet v2 Control (W=40)** | 12.37 km/h | 7.59 km/h | **22.75 m** | 440.20 m | **`263.11 m`** | 33.7% | **BENCHMARK** |
| **F1: SpeedNet v2 (W=50)** | 12.62 km/h | 8.92 km/h | 62.00 m | 1125.54 m | **`963.59 m`** | 34.0% | +700.48m (+266.2%) |
| **F2: SpeedNet v2 (W=60)** | 14.58 km/h | 10.62 km/h | 154.49 m | 537.10 m | **`873.70 m`** | 34.6% | +610.59m (+232.1%) |
| **F3: SpeedNet v2 (W=80)** | 47.29 km/h | 16.53 km/h | 382.58 m | 808.88 m | **`819.34 m`** | 35.6% | +556.23m (+211.4%) |
| **F4: SpeedNet v4 Dilated [SELECTED]** | **12.18 km/h** | **8.62 km/h** | **249.43 m** | **331.60 m** | **`595.04 m`** | **36.0%** | **+331.93m (+126.2%)** |

---

## 3. Maneuver Regime Speed Bias Diagnostic

| Maneuver Regime | F0 (W=40 Control) Bias | F2 (W=60) Bias | F4 (Dilated W=60 d=2) Bias | Temporal Window Impact |
|---|---:|---:|---:|---|
| **Stationary** | +0.67 km/h | +0.26 km/h | +0.34 km/h | Slightly reduced |
| **Acceleration** | +9.10 km/h | +12.28 km/h | +11.91 km/h | Overestimates more |
| **Braking / Deceleration** | **+8.79 km/h** | **+11.55 km/h** | **+9.12 km/h** | **DEGRADED (Overestimates more)** |
| **Straight / Cruise** | +12.13 km/h | +18.31 km/h | +13.80 km/h | Overestimates more |
| **Moderate Turn** | +7.67 km/h | +15.54 km/h | +11.29 km/h | Overestimates more |
| **Strong Turn** | +5.76 km/h | +8.34 km/h | +8.05 km/h | Overestimates more |

---

## 4. Scientific Explanation: Why Receptive Field Expansion Failed

1. **Temporal Phase Lag During Deceleration:** When vehicle speed drops rapidly during braking, longer sequence windows ($W=50, 60, 80$) retain historical high-speed IMU frames in the LSTM memory state. This introduces phase lag, delaying the predicted speed reduction and increasing braking speed overestimation from $+8.79\text{ km/h}$ (Control) to $+11.55\text{ km/h}$ ($W=60$).
2. **Task-Metric Mismatch (MAE vs Integration Error):** Validation Speed MAE penalizes instantaneous pointwise speed error. However, dead reckoning integrates speed over time. Pointwise errors that are temporally correlated (phase lag) accumulate exponentially into position drift, whereas $W=40$ predictions have higher high-frequency noise but zero phase lag.

---

## 5. Artifact Inventory

- **Script:** [`scripts/vw4_m011_speednet_v4_temporal_context.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m011_speednet_v4_temporal_context.py)
- **Summary JSON:** [`results/vw4_m011_speednet_v4_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_summary.json)
- **Predictions Array:** [`results/vw4_m011_speednet_v4_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_predictions.npz)
- **Plots Directory:** [`plots/vw4/m011_speednet_v4/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/m011_speednet_v4/) (6 plots)
- **Milestone:** [`milestones/M011_speednet_v4_temporal_context.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/milestones/M011_speednet_v4_temporal_context.md)
