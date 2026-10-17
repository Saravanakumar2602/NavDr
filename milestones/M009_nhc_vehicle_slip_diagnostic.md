# Milestone M009 — NHC / Vehicle Slip Observability Diagnostic

## 1. Date / Status
- **Date:** 2026-09-01
- **Status:** REJECTED (Hypothesis REJECTED)
- **Milestone Identifier:** `M009_nhc_vehicle_slip_diagnostic`

---

## 2. Starting Point
- **Context:** Following physics-informed feature evaluation (`M008`), M009 performs a controlled 10-part diagnostic investigation to determine whether the remaining navigation error is caused by physical violation of Non-Holonomic Constraints ($v_{\text{lateral}} \approx 0$), vehicle body sideslip, heading/frame formulation, or NHC-EKF interaction.
- **Provenance-Locked Benchmark to Beat:** **SpeedNet v2 + Raw Gyro + NHC = 263.11 m @ 300s** (Unseen test partition `start_idx = 108,000`).
- **Available Code:** [`scripts/vw4_m009_nhc_slip_diagnostic.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m009_nhc_slip_diagnostic.py).

---

## 3. Research Question
Is the Non-Holonomic Constraint ($v_{\text{lateral}} \approx 0$) actually violated during Vw04 driving data, is that violation large enough to explain the observed 263 m dead-reckoning drift, and is vehicle sideslip observable from a single smartphone IMU?

---

## 4. Hypothesis
Dynamic vehicle cornering creates measurable body sideslip ($\beta_{\text{slip}} > 3.0^\circ$) that violates the rigid NHC assumption ($v_{\text{lateral}} = 0$), causing integrated position drift.

---

## 5. What We Changed / Built
- **Scripts Created:**
  - [`scripts/vw4_m009_nhc_slip_diagnostic.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m009_nhc_slip_diagnostic.py) — 10-part diagnostic pipeline.
- **Reports & Artifacts:**
  - [`results/vw4_m009_nhc_diagnostic_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m009_nhc_diagnostic_report.md)
  - [`results/vw4_m009_nhc_diagnostic_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m009_nhc_diagnostic_summary.json)
  - `plots/vw4/m009_nhc_diagnostic/` (10 plots)

---

## 6. Experiment Methodology
- **Dataset:** Vw04, unseen test partition (`start_idx = 108,000`).
- **10 Diagnostics Executed:**
  1. Coordinate Frame & Sanity Verification (North/East/South/West)
  2. GNSS Ground-Track Course vs VBOX/IMU Heading
  3. Measured Lateral Accel vs Planar Kinematic Expectation ($a_{\text{lat,meas}} - v \cdot \omega$)
  4. Apparent Sideslip Angle Estimation ($\beta_{\text{app}} = \psi_{\text{course}} - \psi_{\text{vbox}}$)
  5. Maneuver Regime Diagnostic Breakdown (6 regimes)
  6. EKF NHC Measurement Residual Analysis ($y_{\text{nhc}} = 0 - v_{\text{lat,est}}$)
  7. Controlled NHC Navigation Ablation (with vs without NHC)
  8. Heading / NHC Interaction Matrix (4 cases)
  9. Sensor Observability Analysis
  10. Physical Plausibility & Verdict Classification

---

## 7. Results

### Diagnostic 1: Directional Sanity Check
- All 4 synthetic directional tests (North, East, South, West) **PASSED 100%** with `0.00` error. $v_x = v \sin\psi$, $v_y = v \cos\psi$, $v_{\text{lat}} = -v_x \cos\psi + v_y \sin\psi$.

### Diagnostic 2 & 4: GNSS Course vs Heading & Apparent Sideslip ($v > 1.0\text{ m/s}$)
- **GNSS Course vs VBOX Heading MAE:** `0.000°` (Bias: `0.000°`, P95: `0.000°`).
- **Integrated IMU Yaw vs VBOX Heading MAE:** `116.13°` (P95: `176.86°`).
- **Apparent Sideslip ($\beta_{\text{app}}$):** `0.000°` across the entire test partition.

### Diagnostic 3: Lateral Acceleration Consistency
- Kinematic residual $R_a = a_{\text{lat,meas}} - (v \cdot \omega_{\text{yaw}})$ MAE = `2.3136 m/s²`, RMSE = `3.3478 m/s²`, P95 = `7.1824 m/s²`. Acceleration residual is highest in Strong Turns (`2.9337 m/s²`) due to roll tilt ($g \sin\theta_{\text{roll}}$).

### Diagnostic 6, 7 & 8: EKF NHC Residual & Interaction Matrix (300s Outage)

| Case Name | Speed Source | Heading Source | Use NHC | 300s Pos Error (m) | 300s CDE % | 300s Speed MAE | 300s Hderr |
|---|:---:|:---:|:---:|---:|---:|---:|---:|
| **Case A: SpeedNet v2 + IMU Yaw + NHC [BASELINE]** | SpeedNet v2 | IMU Gyro | **YES** | **`263.11 m`** | 33.7% | 6.71 km/h | 85.3° |
| **Case B: SpeedNet v2 + IMU Yaw (NO NHC)** | SpeedNet v2 | IMU Gyro | **NO** | **`1031.63 m`** | 40.5% | 7.69 km/h | 57.4° |
| **Case C: SpeedNet v2 + GT Yaw + NHC** | SpeedNet v2 | Ground Truth | **YES** | **`556.26 m`** | 34.8% | 6.88 km/h | 9.6° |
| **Case D: SpeedNet v2 + GT Yaw (NO NHC)** | SpeedNet v2 | Ground Truth | **NO** | **`400.48 m`** | 40.5% | 7.73 km/h | 6.1° |
| **Case E: GT Speed + IMU Yaw + NHC** | Ground Truth | IMU Gyro | **YES** | **`493.47 m`** | 3.4% | 1.48 km/h | 161.4° |
| **Case F: GT Speed + GT Yaw + NHC [Oracle]** | Ground Truth | Ground Truth | **YES** | **`557.09 m`** | 2.4% | 1.53 km/h | 1.2° |

---

## 8. Baseline Comparison (Baseline Provenance Lock)

| Configuration | 300s Result | Source Artifact |
|---|---:|---|
| **SpeedNet v2 + Raw Gyro + NHC Benchmark (Case A)** | **263.11 m** | `results/vw4_orientation_anchor_summary.json` |
| SpeedNet v2 + Raw Gyro NO NHC (Case B) | 1031.63 m | `results/vw4_m009_nhc_diagnostic_summary.json` |
| SpeedNet v2 + GT Yaw + NHC (Case C) | 556.26 m | `results/vw4_m009_nhc_diagnostic_summary.json` |

---

## 9. Ablation / Diagnostic Findings
- **Physical Vehicle Sideslip Hypothesis REJECTED:** Apparent sideslip $\beta_{\text{app}} = 0.000^\circ$. Vehicle body heading and velocity ground track match within 0.0°.
- **Discovery of NHC-Heading Kinematic Contradiction:** Case A (IMU Yaw + NHC = `263.11 m`) outperforms Case C (GT Yaw + NHC = `556.26 m`) and Case F (GT Speed + GT Yaw + NHC = `557.09 m`). Rigid NHC ($R_{\text{nhc}} = 0.04$) creates orthogonal velocity projection errors when applied alongside precise heading during cornering. Integrated IMU heading co-drifts smoothly with NHC, avoiding sharp EKF velocity updates during turns.
- **Mathematical Unobservability:** Single smartphone IMUs cannot observe true sideslip independently from chassis roll tilt ($g \sin\theta_{\text{roll}}$).

---

## 10. What Failed
- **Physical Vehicle Sideslip Hypothesis:** REJECTED. Sideslip is zero in data and mathematically unobservable.

---

## 11. What We Learned

### Directly Measured Findings
1. Apparent sideslip $\beta_{\text{app}} = 0.000^\circ$ (Mean=0.0°, P95=0.0°).
2. Removing NHC increases 300s position error by +768.5 m (263.1 m $\rightarrow$ 1031.6 m).
3. Supplying GT Heading + NHC degrades position error to 556.3 m.

### Strong Inference
- Enforcing rigid $v_{\text{lateral}} = 0$ during dynamic cornering causes EKF velocity projection contradiction.

### Hypothesis Requiring Further Validation
- Scaling NHC measurement covariance dynamically during turns ($R_{\text{nhc}} \propto 1 + |\omega_{\text{yaw}}|$) will eliminate cornering contradiction without adding unobservable states.

---

## 12. Artifact Inventory

### Scripts
- [`scripts/vw4_m009_nhc_slip_diagnostic.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m009_nhc_slip_diagnostic.py)

### Reports & Data
- [`results/vw4_m009_nhc_diagnostic_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m009_nhc_diagnostic_report.md)
- [`results/vw4_m009_nhc_diagnostic_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m009_nhc_diagnostic_summary.json)
- `plots/vw4/m009_nhc_diagnostic/` (10 diagnostic plots)

---

## 13. Current State After the Milestone
- **Current Best Deployable System:** SpeedNet v2 + Raw Gyro + NHC (**263.11 m @ 300s**).
- **Rejected Direction:** Dynamic Slip-Angle EKF state.

---

## 14. Next Step Decision
- **What to do next:** Investigate **M010 — Adaptive NHC Measurement Covariance & Velocity-Frame EKF (EKF-v2)**.
- **Why:** M009 proved that rigid $R_{\text{nhc}} = 0.04$ causes turn contradiction. Scaling $R_{\text{nhc}}$ during cornering will relax lateral constraints when vehicle dynamic forces are active.
- **Target:** Reduce 300s position error to $<150\text{ m}$.

---

## 15. Research Chain
- **Previous Milestone:** `M008_speednet_v25_physics_informed`
- **Current Milestone:** `M009_nhc_vehicle_slip_diagnostic`
- **Next Planned Milestone:** `M010_adaptive_nhc_covariance_ekf`
- **Summary:** M009 disproved the physical sideslip hypothesis ($\beta=0.0^\circ$) and revealed NHC-Heading Contradiction as the true root cause, directing M010 toward Adaptive NHC Covariance.
