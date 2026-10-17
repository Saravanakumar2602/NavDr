# Milestone M007 — SpeedNet v3 Regime-Aware Speed Estimation & Multi-Task Analysis

## 1. Date / Status
- **Date:** 2026-09-01
- **Status:** FAILED / REJECTED
- **Milestone Identifier:** `M007_speednet_v3_regime_aware`

---

## 2. Starting Point
- **Context:** Building on residual error decomposition (`M006`), SpeedNet v3 evaluates whether adding a 6-class auxiliary regime classification head ($L_{\text{total}} = L_{\text{speed}} + 0.3 L_{\text{stat}} + \lambda L_{\text{regime}}$) reduces systematic positive speed bias (+6.39 km/h) during braking and turning.
- **Previous Best Deployable Baseline:** SpeedNet v2 + Raw Gyro + NHC (263.11 m @ 300s).
- **Available Code:** [`scripts/vw4_speednet_v3_regime_aware.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v3_regime_aware.py).

---

## 3. Research Question
Does multi-task regime classification training reduce SpeedNet's systematic positive speed bias during deceleration and turning, and does it reduce 300s GNSS blackout position error below the 263 m baseline?

---

## 4. Hypothesis
Enforcing regime classification loss ($\lambda \in [0.05, 0.10, 0.20]$) will force the network to internalize vehicle motion regimes (Acceleration, Braking, Turning), reducing speed bias from $+6.39\text{ km/h} \rightarrow <+2.0\text{ km/h}$ and position error to $<150\text{ m}$.

---

## 5. What We Changed / Built
- **Scripts Created:**
  - [`scripts/vw4_speednet_v3_regime_aware.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v3_regime_aware.py) — 6-experiment suite covering IMU regime validity, multi-task training, per-regime metrics, navigation ablation, drift attribution, and offline calibration stress testing.
- **Models Created:**
  - `models/speednet_v3_w30_lambda005.pth` (**12.51 km/h val speed MAE** — Selected via validation set)
  - `models/speednet_v3_w30_lambda010.pth` (47.29 km/h val speed MAE — Rejected due to gradient dominance)
  - `models/speednet_v3_w30_lambda020.pth` (47.29 km/h val speed MAE — Rejected)
- **Reports & Artifacts:**
  - [`results/vw4_speednet_v3_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_report.md)
  - [`results/vw4_speednet_v3_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_summary.json)
  - [`results/vw4_speednet_v3_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_predictions.npz)
  - `plots/vw4/speednet_v3/regime_bias_mae.png`

---

## 6. Experiment Methodology
- **Dataset:** Vw04, unseen test partition (`start_idx = 108,000`).
- **6 Driving Regimes:** Stationary (0), Acceleration (1), Braking (2), Straight/Cruise (3), Moderate Turn (4), Strong Turn (5).
- **Architecture:** 1D-CNN + BiLSTM ($W=30$) with 3 output heads ($v_{\text{fwd}}$, $P_{\text{stat}}$, 6-class Regime Logits).
- **Navigation Filter:** SpeedNet v3 + Raw Gyro + NHC (no adaptive bias).

---

## 7. Results

### Experiment 1: IMU Regime Classifier Recall (Validation Partition)
- **Overall Accuracy:** `60.3%`
- **Reliably Classified Regimes ($\ge 60\%$ recall):** Stationary (92.2%), Strong Turn (84.8%), Straight/Cruise (82.4%), Moderate Turn (64.2%).
- **Poorly Classified Regimes ($< 60\%$ recall):** Acceleration (21.9%), Braking (14.0%). In a 3.0s IMU window, deceleration is confused with road slope/gravity tilt changes.

### Experiment 3 & 6: Speed Error & Calibration Stress Test (Unseen Test Partition)

| Model / Method | Overall Speed MAE | Overall Speed Bias | Notes |
|---|---|---|---|
| SpeedNet v2 (Uncorrected) | 7.586 km/h | +6.388 km/h | Baseline |
| V2 + Global Bias Calibration | 6.972 km/h | +5.062 km/h | Offline val offset |
| **V2 + Regime-Specific Calibration** | **7.021 km/h** | **+5.034 km/h** | **Best per-regime balance** |
| SpeedNet v3 (Learned Multi-Task) | 8.007 km/h | +6.766 km/h | Degraded speed accuracy |

### Experiment 4: Navigation Ablation Matrix

| Candidate Case | 60s Outage | 120s Outage | 300s Outage | 300s Speed MAE | vs Baseline |
|---|---:|---:|---:|---:|---|
| **Case A: SpeedNet v2 + NHC [Baseline]** | 100.91 m | 396.73 m | **664.08 m** | 6.67 km/h | Baseline |
| **Case B: SpeedNet v3 + NHC** | 96.30 m | 363.10 m | **938.90 m** | 6.94 km/h | -41.4% (Worse) |
| **Case C: SpeedNet v3 (no NHC)** | 147.80 m | 889.60 m | **1325.50 m** | 7.73 km/h | -99.6% (Worse) |
| **Case D: GT Speed + NHC** | 156.30 m | 746.50 m | **1077.70 m** | 1.50 km/h | -62.3% (Worse) |
| **Case E: V2 + Regime Calib + NHC** | 88.30 m | 412.20 m | **662.60 m** | 6.17 km/h | **+0.2% (Best)** |

---

## 8. Baseline Comparison (Baseline Provenance Lock)

| Configuration | 300s Result | Source Artifact |
|---|---:|---|
| SpeedNet v2 + NHC [Baseline] | 664.08 m | `results/vw4_speednet_v3_summary.json` (Case A) |
| SpeedNet v3 + NHC ($\lambda=0.05$) | 938.90 m | `results/vw4_speednet_v3_summary.json` (Case B) |
| **SpeedNet v2 + Offline Regime Calibration + NHC** | **662.60 m** | `results/vw4_speednet_v3_summary.json` (Case E) |

- SpeedNet v3 **failed to beat the baseline**, performing 41.4% worse (938.9 m vs 664.1 m). Val-derived offline regime calibration outperformed end-to-end multi-task learning (662.6 m vs 938.9 m).

---

## 9. Ablation / Diagnostic Findings
- **Multi-Task Gradient Competition:** Cross-entropy regime loss overwhelmed Smooth L1 speed loss for $\lambda \ge 0.10$ (val MAE exploded to $47.29\text{ km/h}$). Even at $\lambda = 0.05$, multi-task learning degraded overall test speed MAE ($8.01\text{ km/h}$ vs $7.59\text{ km/h}$ for v2).
- **IMU Braking Ambiguity:** Raw accelerometers over a 3.0s window cannot distinguish linear deceleration from pitch tilt without kinematic force integrals.

---

## 10. What Failed
- **SpeedNet v3 Multi-Task Architecture:** REJECTED. Auxiliary classification loss heads introduce negative gradient interference with speed regression.

---

## 11. What We Learned

### Directly Measured Findings
1. SpeedNet v3 + NHC produced **938.9 m position error at 300s** (failed target $<150\text{ m}$).
2. Offline regime calibration reduced test speed MAE to $7.02\text{ km/h}$ (outperforming learned V3 at $8.01\text{ km/h}$).

### Strong Inference
- Raw 6-channel IMU windows lack explicit kinematic energy features needed to distinguish vehicle braking from road slope changes.

### Hypothesis Requiring Further Validation
- Providing derived kinematic features ($\int a_{\text{long}} dt$, rolling IMU variance, tilt estimate) directly into the neural input (SpeedNet v2.5) will resolve braking speed bias without multi-task gradient loss interference.

---

## 12. Artifact Inventory

### Scripts
- [`scripts/vw4_speednet_v3_regime_aware.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v3_regime_aware.py)

### Models
- `models/speednet_v3_w30_lambda005.pth`
- `models/speednet_v3_w30_lambda010.pth`
- `models/speednet_v3_w30_lambda020.pth`

### Reports & Data
- [`results/vw4_speednet_v3_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_report.md)
- [`results/vw4_speednet_v3_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_summary.json)
- [`results/vw4_speednet_v3_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_predictions.npz)
- `plots/vw4/speednet_v3/regime_bias_mae.png`

---

## 13. Current State After the Milestone
- **Current Best Deployable System:** SpeedNet v2 + Raw Gyro + NHC (**263.11 m @ 300s**).
- **Rejected Architecture:** SpeedNet v3 Multi-Task (938.9 m @ 300s).

---

## 14. Next Step Decision
- **What to do next:** Design SpeedNet v2.5 with Physics-Informed Kinematic Features (integrated specific force delta $\int a_{\text{long}} dt$, rolling IMU variance, tilt angle estimate).
- **Why:** Provide explicit kinematic state features to resolve acceleration/deceleration ambiguity without adding multi-task classification heads.
- **Target:** Reduce 300s position error to $<150\text{ m}$.

---

## 15. Research Chain
- **Previous Milestone:** `M006_v2_residual_error_decomposition`
- **Current Milestone:** `M007_speednet_v3_regime_aware`
- **Next Planned Milestone:** `M008_speednet_v25_kinematic_features`
- **Summary:** SpeedNet v3 multi-task regime head was rejected due to loss interference, directing future work toward explicit physics-informed kinematic feature inputs (SpeedNet v2.5).
