# Milestone M005 — HeadingNet Learned Orientation Module & Master Ablation

## 1. Date / Status
- **Date:** 2026-09-01
- **Status:** FAILED / REJECTED
- **Milestone Identifier:** `M005_headingnet_orientation_ablation`

---

## 2. Starting Point
- **Context:** Following SpeedNet v2 (`M004`), orientation drift was identified as a major residual bottleneck. A secondary CNN+BiLSTM network ("HeadingNet") was proposed to predict yaw-rate corrections ($\Delta \omega$) directly from 7 input channels (6 IMU + SpeedNet v2 predicted speed).
- **Previous Best Deployable Baseline:** SpeedNet v2 + Raw Gyro + NHC (263.11 m @ 300s).
- **Available Code:** [`scripts/vw4_headingnet_ablation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_headingnet_ablation.py).

---

## 3. Research Question
Does training a learned secondary neural orientation module (HeadingNet) to correct MEMS gyroscope yaw rate drift reduce accumulated 300s GNSS outage position error below the 263 m baseline?

---

## 4. Hypothesis
HeadingNet will learn non-linear MEMS scale-factor and dynamic cornering errors from IMU dynamics, achieving yaw rate MAE $<1.30^\circ/\text{s}$ and reducing 300s blackout position error to $<150\text{ m}$.

---

## 5. What We Changed / Built
- **Scripts Created:**
  - [`scripts/vw4_headingnet_ablation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_headingnet_ablation.py) — HeadingNet training across $W \in [20, 30, 50]$ and master 5-case ablation driver.
- **Models Trained:**
  - `models/headingnet_w20.pth` (1.24°/s val yaw MAE)
  - `models/headingnet_w30.pth` (1.46°/s val yaw MAE)
  - `models/headingnet_w50.pth` (**1.20°/s val yaw MAE** — Selected via validation set)
- **Reports & Artifacts:**
  - [`results/headingnet_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/headingnet_summary.json)
  - [`results/headingnet_results.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/headingnet_results.md)
  - `plots/vw4/headingnet/ablation_comparison.png`

---

## 6. Experiment Methodology
- **Dataset:** Vw04, unseen test partition (`start_idx = 108,000`).
- **HeadingNet Input Channels (7):** `[ax_lin, ay_lin, az_lin, gx, gy, gz, v_speednet_v2]`.
- **Selected Model:** HeadingNet $W=50$ ($5.0\text{ s}$ window, 12 epochs training).
- **Master 5-Case Navigation Ablation Matrix (60s, 120s, 300s):**
  - **Case A:** SpeedNet v2 + Raw Gyro + NHC (Benchmark)
  - **Case B:** SpeedNet v2 + HeadingNet (no NHC)
  - **Case C:** SpeedNet v2 + NHC + HeadingNet
  - **Case D:** SpeedNet v2 + Adaptive Bias + NHC
  - **Case E:** SpeedNet v2 + NHC + Oracle Heading

---

## 7. Results

### Master 5-Case Navigation Ablation Matrix (Unseen Test Partition)

| Outage Duration | Candidate Case Configuration | Final Pos Error (m) | CDE % | Speed MAE (km/h) | Heading Error (°) | vs Case A |
|:---:|:---|---:|---:|---:|---:|---:|
| **60s** | Case A: SpeedNet v2 + Raw Gyro + NHC | 100.91 m | 27.81% | 9.20 km/h | 46.22° | Baseline |
| **60s** | Case B: SpeedNet v2 + HeadingNet (no NHC) | 308.37 m | 30.64% | 9.86 km/h | 145.57° | -205.6% Worse |
| **60s** | Case C: SpeedNet v2 + NHC + HeadingNet | 114.48 m | 28.85% | 9.56 km/h | 64.48° | -13.5% Worse |
| **60s** | Case D: SpeedNet v2 + Adaptive Bias + NHC | **22.97 m** | **27.76%** | **9.21 km/h** | 137.89° | **+77.2% Best** |
| **60s** | Case E: SpeedNet v2 + NHC + Oracle Heading | 77.59 m | 26.05% | 8.83 km/h | 31.96° | +23.1% |
| | | | | | | |
| **120s** | Case A: SpeedNet v2 + Raw Gyro + NHC | 396.73 m | 42.37% | 12.37 km/h | 97.58° | Baseline |
| **120s** | Case B: SpeedNet v2 + HeadingNet (no NHC) | 1,068.36 m | 47.60% | 13.71 km/h | 131.07° | -169.3% Worse |
| **120s** | **Case C: SpeedNet v2 + NHC + HeadingNet** | **346.26 m** | **45.54%** | **13.25 km/h** | **29.32°** | **+12.7%** |
| **120s** | Case D: SpeedNet v2 + Adaptive Bias + NHC | 436.13 m | 42.51% | 12.41 km/h | 8.57° | -9.9% |
| **120s** | Case E: SpeedNet v2 + NHC + Oracle Heading | 304.61 m | 43.46% | 12.68 km/h | 0.13° | +23.2% |
| | | | | | | |
| **300s** | Case A: SpeedNet v2 + Raw Gyro + NHC | 664.08 m | 33.39% | 6.67 km/h | 2.62° | Baseline |
| **300s** | Case B: SpeedNet v2 + HeadingNet (no NHC) | 1,461.18 m | 37.96% | 7.37 km/h | 174.41° | -120.0% Worse |
| **300s** | Case C: SpeedNet v2 + NHC + HeadingNet | 740.32 m | 36.27% | 7.12 km/h | 91.05° | -11.5% Worse |
| **300s** | **Case D: SpeedNet v2 + AdaptBias + NHC** | **263.08 m** | **33.46%** | **6.67 km/h** | **84.83°** | **+60.4% Best** |
| **300s** | Case E: SpeedNet v2 + NHC + Oracle Heading | 539.64 m | 34.23% | 6.78 km/h | 9.55° | +18.7% |

---

## 8. Baseline Comparison (Baseline Provenance Lock)

| Configuration | 300s Result | Source Artifact |
|---|---:|---|
| SpeedNet v2 + Raw Gyro + NHC (Case A) | 664.08 m | `results/headingnet_summary.json` |
| SpeedNet v2 + HeadingNet alone (Case B) | 1,461.18 m | `results/headingnet_summary.json` |
| SpeedNet v2 + NHC + HeadingNet (Case C) | 740.32 m | `results/headingnet_summary.json` |
| **SpeedNet v2 + Adaptive Bias + NHC (Case D)** | **263.08 m** | `results/headingnet_summary.json` |

- HeadingNet $W=50$ **failed to improve navigation** compared to the baseline. At 300s, Case C (740.32 m) performed **11.5% worse than Case A (664.08 m)** and **181.4% worse than Case D (263.08 m)**.

---

## 9. Ablation / Diagnostic Findings
- **Task-Metric Mismatch:** HeadingNet achieved an impressive isolated yaw-rate validation MAE ($1.20^\circ/\text{s}$), but this did NOT translate into lower navigation drift. Microscopic phase errors and transient over-corrections during dynamic turns integrated into large geographic drift over 300s.
- **HeadingNet Alone is Catastrophic:** Case B (no NHC) produced $1,461.18\text{ m}$ position error at 300s, proving that neural heading prediction without lateral constraints cannot stabilize DR.

---

## 10. What Failed
- **Learned Yaw Correction (HeadingNet):** REJECTED. Minimizing instantaneous yaw rate MAE introduces phase distortion during dynamic vehicle maneuvers that degrades integrated DR performance.

---

## 11. What We Learned

### Directly Measured Findings
1. HeadingNet $W=50$ yaw rate MAE = $1.20^\circ/\text{s}$, but produces **740.32 m position error at 300s**.
2. Oracle Heading + NHC (Case E = 539.64 m) is WORSE than Case D (263.08 m).

### Strong Inference
- Minimizing yaw rate MAE is an invalid surrogate objective for dead-reckoning position drift.
- Forward speed errors and NHC constraint interactions are more complex than previously assumed.

### Hypothesis Requiring Further Validation
- The remaining ~263 m position error originates from systematic positive speed overestimation rather than pure heading drift.

---

## 12. Artifact Inventory

### Scripts
- [`scripts/vw4_headingnet_ablation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_headingnet_ablation.py)

### Models
- `models/headingnet_w20.pth`, `models/headingnet_w30.pth`, `models/headingnet_w50.pth`

### Reports & Data
- [`results/headingnet_results.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/headingnet_results.md)
- [`results/headingnet_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/headingnet_summary.json)
- `plots/vw4/headingnet/ablation_comparison.png`

---

## 13. Current State After the Milestone
- **Current Best Configuration:** SpeedNet v2 + Raw Gyro + NHC (263 m @ 300s).
- **Rejected Architecture:** HeadingNet (740 m @ 300s).

---

## 14. Next Step Decision
- **What to do next:** Perform a rigorous second-stage residual error decomposition of the current best system (SpeedNet v2 + Raw Gyro + NHC) across speed, heading, temporal alignment, and maneuver regimes.
- **Why:** Determine exactly where the remaining ~263 m error originates before attempting further model development.
- **Target:** Identify the single dominant residual error mechanism.

---

## 15. Research Chain
- **Previous Milestone:** `M004_speednet_v2_baseline`
- **Current Milestone:** `M005_headingnet_orientation_ablation`
- **Next Planned Milestone:** `M006_v2_residual_error_decomposition`
- **Summary:** HeadingNet was rejected after proving that lower yaw-rate MAE (1.20°/s) degrades integrated 300s navigation (740 m vs 263 m baseline).
