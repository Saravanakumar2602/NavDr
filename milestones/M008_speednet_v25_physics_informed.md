# Milestone M008 — SpeedNet v2.5 Physics-Informed Features

## 1. Date / Status
- **Date:** 2026-09-01
- **Status:** FAILED / REJECTED
- **Milestone Identifier:** `M008_speednet_v25_physics_informed`

---

## 2. Starting Point
- **Context:** Following residual error decomposition (`M006`) and SpeedNet v3 rejection (`M007`), M008 evaluates whether adding physically derived features (integrated longitudinal acceleration $\Delta v_{\text{acc}}$, rolling IMU variance $a_{\text{var}}, \omega_{\text{var}}$, and pitch tilt angle $\theta_{\text{tilt}}$) directly into SpeedNet v2's neural input representation improves speed estimation and reduces 300s GNSS outage position error.
- **Provenance-Locked Benchmark to Beat:** **SpeedNet v2 + Raw Gyro + NHC = 263.11 m @ 300s** (Unseen test partition `start_idx = 108,000`).
- **Available Code:** [`scripts/vw4_speednet_v25_physics_informed.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v25_physics_informed.py).

---

## 3. Research Question
Can physically meaningful kinematic features improve SpeedNet v2's systematic speed estimation without introducing the navigation degradation observed with multi-task SpeedNet v3, and achieve a 300-second position error $<263.1\text{ m}$ on the locked unseen test partition?

---

## 4. Hypothesis
Adding derived kinematic features ($\Delta v_{\text{acc}}, a_{\text{var}}, \theta_{\text{tilt}}$) into the neural input layer will resolve gravity tilt/deceleration ambiguity in 3.0s IMU windows, reducing speed MAE from $8.87\text{ km/h} \rightarrow <6.0\text{ km/h}$ and position error from $263.1\text{ m} \rightarrow <150\text{ m}$.

---

## 5. What We Changed / Built
- **Scripts Created:**
  - [`scripts/vw4_speednet_v25_physics_informed.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v25_physics_informed.py) — 6-experiment physics feature engineering driver.
- **Models Trained (5 Checkpoints):**
  - `models/speednet_v25_f0_w30.pth` (6 ch, Val MAE = 13.35 km/h)
  - `models/speednet_v25_f1_w30.pth` (7 ch, Val MAE = 13.23 km/h)
  - `models/speednet_v25_f2_w30.pth` (8 ch, Val MAE = 47.29 km/h)
  - `models/speednet_v25_f3_w30.pth` (**7 ch, Val MAE = 13.10 km/h — Selected via Validation**)
  - `models/speednet_v25_f4_w30.pth` (10 ch, Val MAE = 13.71 km/h)
- **Reports & Artifacts:**
  - [`results/vw4_speednet_v25_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_report.md)
  - [`results/vw4_speednet_v25_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_summary.json)
  - [`results/vw4_speednet_v25_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_predictions.npz)
  - `plots/vw4/speednet_v25/feature_diagnostics.png`

---

## 6. Experiment Methodology
- **Dataset:** Vw04, unseen test partition (`start_idx = 108,000`).
- **Feature Normalization Protocol:** Mean ($\boldsymbol{\mu}_{\text{train}}$) and std ($\boldsymbol{\sigma}_{\text{train}}$) computed strictly on training set (`0:88566`). Zero test data used for normalization.
- **Model Selection Protocol:** Model variant selected exclusively on validation set MAE (`88566:107535`).
- **Evaluated Variants:**
  - **F0 (Control, 6 ch):** SpeedNet v2 original IMU channels.
  - **F1 (7 ch):** F0 + `[dv_acc]` (window-causal integrated longitudinal acceleration).
  - **F2 (8 ch):** F0 + `[a_var, w_var]` (0.5s rolling variance of longitudinal accel and yaw rate).
  - **F3 (7 ch):** F0 + `[tilt_angle]` (derived gravity pitch-tilt angle).
  - **F4 (10 ch):** F0 + `[dv_acc, a_var, w_var, tilt_angle]` (Combined physics set).
- **Navigation Filter:** Candidate Speed + Raw Gyro + NHC (no adaptive bias, no regime loss).

---

## 7. Results

### Experiment 2 & 3: Model Selection & Pure Speed Metrics (Unseen Test Partition)

| Feature Variant | Channels | Val Speed MAE (km/h) | Selection Status | Test Speed MAE (km/h) | Test Speed Bias (km/h) | Test Speed RMSE (km/h) |
|---|:---:|---:|---|---:|---:|---:|
| F0 (Control) | 6 ch | 13.354 km/h | Control | **8.866 km/h** | **+7.988 km/h** | 14.757 km/h |
| F1 (+ Integrated Accel) | 7 ch | 13.230 km/h | Candidate | 9.141 km/h | +8.408 km/h | 14.684 km/h |
| F2 (+ Rolling Variance) | 8 ch | 47.291 km/h | Local min | 16.525 km/h | -16.525 km/h | 22.602 km/h |
| **F3 (+ Tilt Angle)** | **7 ch** | **13.097 km/h** | **SELECTED** ✅ | 9.017 km/h | +7.954 km/h | 14.827 km/h |
| F4 (Combined Physics Set) | 10 ch | 13.711 km/h | Candidate | 9.021 km/h | +8.050 km/h | **14.276 km/h** |

### Experiment 4: Navigation Ablation Matrix (Raw Gyro + NHC)

| Candidate Case | 60s Outage | 120s Outage | 300s Outage | 300s Speed MAE | vs Benchmark (263.1m) |
|---|---:|---:|---:|---:|---|
| **SpeedNet v2 + Raw Gyro + NHC Benchmark** | 22.75 m | 440.20 m | **263.11 m** | 6.71 km/h | **BENCHMARK** |
| **F0: Control (W=30 setup)** | 226.67 m | 981.44 m | 1441.01 m | 7.98 km/h | +447.7% Worse |
| **F1: + Integrated Accel Delta** | 162.44 m | 467.55 m | **887.47 m** | 8.30 km/h | +237.3% Worse |
| **F2: + Short-Term IMU Variance** | 382.58 m | 813.61 m | 823.86 m | 15.05 km/h | +213.1% Worse |
| **F3: + Estimated Tilt Angle (Selected)** | 315.91 m | 1068.72 m | **1611.58 m** | 8.12 km/h | **+512.5% Worse** |
| **F4: + Combined Physics Features** | 323.92 m | 946.58 m | 1175.04 m | 7.99 km/h | +346.6% Worse |
| **GT Speed + Raw Gyro + NHC** | 155.39 m | 741.20 m | 1071.19 m | 1.50 km/h | Oracle |

---

## 8. Baseline Comparison (Baseline Provenance Lock)

| Configuration | 300s Result | Source Artifact |
|---|---:|---|
| **SpeedNet v2 + Raw Gyro + NHC Benchmark** | **263.11 m** | `results/vw4_orientation_anchor_summary.json` |
| F1: SpeedNet v2.5 + Integrated Accel + NHC | 887.47 m | `results/vw4_speednet_v25_summary.json` |
| F3: SpeedNet v2.5 + Tilt Angle + NHC (Selected) | 1611.58 m | `results/vw4_speednet_v25_summary.json` |

- **Verdict:** **FAILURE.** Selected model F3 produced `1611.58 m` position error at 300s, failing to beat the `263.11 m` benchmark (+1,348.47 m / +512.5% worse).
- F1 (+Integrated Accel) showed navigation improvement over control in the $W=30$ setup (`887.47 m` vs `1441.01 m`), but still failed to beat the provenance-locked SpeedNet v2 $W=40$ benchmark (`263.11 m`).

---

## 9. Ablation / Diagnostic Findings
- **Tilt Angle Feature Sensitivity:** Pitch tilt angle (F3) achieved the lowest validation MAE (`13.10 km/h`), but its small prediction oscillations during turns excited state covariance in the EKF filter, degrading heading tracking (`178.4°` heading error) and producing large position drift.
- **Integrated Acceleration Benefit:** Integrated acceleration (F1) stabilized velocity integration during straight-line driving, reducing 300s position error from 1441.01 m (F0) to 887.47 m.
- **Persistent Positive Speed Bias:** Derived physics features did NOT eliminate the systematic positive speed bias (`+7.95` to `+8.41 km/h`).

---

## 10. What Failed
- **SpeedNet v2.5 Physics Feature Input Set:** REJECTED. Derived physics features fed into 1D-CNN+BiLSTM layers fail to resolve systematic positive speed overestimation during braking.

---

## 11. What We Learned

### Directly Measured Findings
1. Selected model F3 (+Tilt Angle) achieved `13.10 km/h` val speed MAE, but produced **1611.58 m position error at 300s**.
2. F1 (+Integrated Accel) achieved **887.47 m at 300s** (best physics variant), but failed to beat the `263.1 m` benchmark.

### Strong Inference
- Input feature engineering alone cannot eliminate speed overestimation during deceleration without explicit structural constraints.

### Hypothesis Requiring Further Validation
- The fundamental remaining bottleneck is the **EKF Kinematic Observation Model** itself. When NHC ($v_{\text{lateral}} \approx 0$) is active during cornering, velocity errors interact non-linearly with yaw rate states, causing heading divergence even with perfect speed inputs.

---

## 12. Artifact Inventory

### Scripts
- [`scripts/vw4_speednet_v25_physics_informed.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v25_physics_informed.py)

### Models
- `models/speednet_v25_f0_w30.pth` through `models/speednet_v25_f4_w30.pth`

### Reports & Data
- [`results/vw4_speednet_v25_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_report.md)
- [`results/vw4_speednet_v25_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_summary.json)
- [`results/vw4_speednet_v25_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v25_predictions.npz)
- `plots/vw4/speednet_v25/feature_diagnostics.png`

---

## 13. Current State After the Milestone
- **Current Best Deployable System:** SpeedNet v2 + Raw Gyro + NHC (**263.11 m @ 300s**).
- **Rejected Variant:** SpeedNet v2.5 Physics Features (1611.58 m @ 300s).

---

## 14. Next Step Decision
- **What to do next:** Investigate **M009 — Dynamic Slip-Angle Aware Kinematic EKF (EKF-v2)**.
- **Why:** Case D (GT Speed + Raw Gyro + NHC = 1071 m in $W=30$ setup) and M006 (GT Speed + GT Heading + NHC = 557 m) proved that the standard NHC assumption ($v_{\text{lateral}} = 0$) creates state contradiction during vehicle cornering when body slip angles are non-zero.
- **Target:** Reduce 300s position error to $<150\text{ m}$ by relaxing $v_{\text{lateral}} = 0$ during dynamic turns using a learned body slip angle model.

---

## 15. Research Chain
- **Previous Milestone:** `M007_speednet_v3_regime_aware`
- **Current Milestone:** `M008_speednet_v25_physics_informed`
- **Next Planned Milestone:** `M009_slip_angle_kinematic_ekf`
- **Summary:** M008 demonstrated that input feature engineering fails to beat the 263.1 m benchmark, shifting focus to solving the NHC cornering contradiction via Dynamic Slip-Angle modeling in M009.
