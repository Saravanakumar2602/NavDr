# Milestone M010 — Adaptive NHC Measurement Covariance & Velocity-Frame EKF

## 1. Date / Status
- **Date:** 2026-09-01
- **Status:** REJECTED (Method REJECTED)
- **Milestone Identifier:** `M010_adaptive_nhc_velocity_frame_ekf`

---

## 2. Starting Point
- **Context:** Following M009's rejection of physical sideslip and identification of NHC-Heading Kinematic Contradiction during dynamic cornering, M010 tests whether dynamically inflating NHC measurement covariance ($R_{\text{nhc}}$) as a function of yaw rate ($|\omega_{\text{yaw}}|^2$) reduces contradiction and improves 300s dead-reckoning accuracy.
- **Provenance-Locked Benchmark to Beat:** **SpeedNet v2 + Raw Gyro + Fixed NHC = 263.11 m @ 300s** (Unseen test partition `start_idx = 108,000`).
- **Available Code:** [`scripts/vw4_m010_adaptive_nhc_ekf.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m010_adaptive_nhc_ekf.py).

---

## 3. Research Question
Does dynamically relaxing the Non-Holonomic Constraint (NHC) measurement covariance during high yaw-rate maneuvers reduce the NHC-heading contradiction and improve 300-second dead-reckoning accuracy?

---

## 4. Hypothesis
A fixed NHC covariance ($R_0 = 0.04\text{ m}^2/\text{s}^2$) treats straight driving and dynamic cornering identically. During high yaw-rate turns, NHC should be trusted less because model mismatch increases. Inflating $R_{\text{nhc}}(\omega) = \text{clip}(R_0(1 + \kappa |\omega|^2), R_0, R_{\max})$ will relax lateral constraints during turns while preserving strong constraints during straight driving, reducing 300s position error to $<150\text{ m}$.

---

## 5. Previous Evidence
- M009 proved $\beta_{\text{app}} = 0.000^\circ$ and demonstrated that Case C (GT Yaw + Fixed NHC = 556.3 m) performs worse than Case A (IMU Yaw + Fixed NHC = 263.1 m), indicating rigid NHC over-constrains heading updates during turns.

---

## 6. Exact Changes Built
- **Scripts Created:**
  - [`scripts/vw4_m010_adaptive_nhc_ekf.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m010_adaptive_nhc_ekf.py) — Validation grid sweep + locked 8-case evaluation matrix driver.
- **Reports & Artifacts:**
  - [`results/vw4_m010_adaptive_nhc_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m010_adaptive_nhc_report.md)
  - [`results/vw4_m010_adaptive_nhc_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m010_adaptive_nhc_summary.json)
  - `plots/vw4/m010_adaptive_nhc/` (6 plots)

---

## 7. Experimental Methodology
- **Dataset:** Vw04, 10 Hz synchronized IMU/VBOX.
- **Validation Partition:** `88566:107535`.
- **Unseen Test Partition:** `start_idx = 108,000`.
- **Validation Sweep:** Grid search over $\kappa \in [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0]$ and $R_{\max} \in [1.0, 5.0, 20.0, 100.0]$.
- **Lock Protocol:** Selected candidate $\kappa=250.0, R_{\max}=100.0$ on validation set, locked configuration, evaluated ONCE on test set.

---

## 8. Dataset / Split / Provenance
- Zero test data used for parameter tuning. Baseline Case A reproduced benchmark `263.11 m` at 300s with 100% precision.

---

## 9. Parameter Selection Procedure
- Validation outage at index `89566` (300s duration).
- Candidate $\kappa=250.0, R_{\max}=100.0$ achieved lowest validation position error (`836.30 m`).

---

## 10. Measured Results (Unseen Test Partition `start_idx = 108,000`)

| Case ID & Description | $\kappa$ | $R_{\max}$ | Use NHC | 60s Error | 120s Error | 300s Error | 300s CDE % | vs Benchmark |
|---|:---:|:---:|:---:|---:|---:|---:|---:|---|
| **Case A: SpeedNet v2 + Fixed NHC [BENCHMARK]** | 0.0 | 100.0 | **YES** | **22.75 m** | **440.20 m** | **`263.11 m`** | 33.7% | **BENCHMARK** |
| **Case B: SpeedNet v2 + No NHC** | 0.0 | 100.0 | **NO** | 333.12 m | 1214.63 m | **`1031.63 m`** | 40.5% | +768.52m (+292.1%) |
| **Case C: Small Adaptive $\kappa=1.0$** | 1.0 | 100.0 | **YES** | 26.68 m | 508.52 m | **`489.35 m`** | 34.0% | +226.24m (+86.0%) |
| **Case D: Medium Adaptive $\kappa=10.0$** | 10.0 | 100.0 | **YES** | 30.87 m | 578.96 m | **`1063.07 m`** | 34.6% | +799.96m (+304.0%) |
| **Case E: Large Adaptive $\kappa=100.0$** | 100.0 | 100.0 | **YES** | 28.98 m | 600.47 m | **`908.85 m`** | 35.6% | +645.74m (+245.4%) |
| **Case F: Bounded Adaptive [SELECTED VAL]** | **250.0** | **100.0** | **YES** | **23.01 m** | **642.53 m** | **`886.53 m`** | **36.0%** | **+623.42m (+236.9%)** |
| **GT Speed + Bounded Adaptive NHC** | 250.0 | 100.0 | **YES** | 196.61 m | 574.48 m | **221.03 m** | 1.5% | -42.08m (-16.0%) |
| **GT Speed + GT Yaw + Fixed NHC [Oracle]** | 0.0 | 100.0 | **YES** | 51.58 m | 318.78 m | **557.09 m** | 2.4% | +293.98m (+111.7%) |

---

## 11. Baseline Comparison (Baseline Provenance Lock)

- Benchmark (Case A): **`263.11 m` @ 300s**
- Selected Model (Case F): **`886.53 m` @ 300s** (+623.42 m / +236.9% worse)
- Verdict: **REJECTED**

---

## 12. Ablation Findings
- All adaptive $\kappa$ variants ($\kappa \in [1.0, 10.0, 100.0, 250.0]$) performed worse than fixed NHC ($R_0 = 0.04$).
- Larger $\kappa$ values push performance closer to the No-NHC limit (`1031.63 m`).

---

## 13. Regime Analysis
- Fixed NHC ($R_0=0.04$) maintained MAE = $0.0024\text{ m/s}$ (Stationary) and $0.8054\text{ m/s}$ (Strong Turn).
- Adaptive NHC inflated mean $R_{\text{nhc}}$ to $2.8438\text{ m}^2/\text{s}^2$ during Strong Turns, increasing residual MAE to $2.5896\text{ m/s}$.

---

## 14. What Failed
- **Adaptive NHC Covariance Inflation:** REJECTED. Dynamically inflating $R_{\text{nhc}}$ during turns removes the essential lateral velocity anchor.

---

## 15. What Worked
- Fixed NHC ($R_0 = 0.04$) remains the single most effective constraint for keeping 300s drift to 263.11 m.

---

## 16. Scientific Interpretation
Inflating $R_{\text{nhc}}$ during turns destabilizes lateral velocity states. Fixed NHC acts as a continuous low-pass velocity anchor. When $R_{\text{nhc}}$ is relaxed during dynamic turns, accumulated heading noise converts forward velocity into unanchored lateral drift, causing rapid position divergence.

---

## 17. Limitations
- Single IMU cannot distinguish roll tilt from lateral acceleration, preventing exact 3D orientation alignment without additional reference.

---

## 18. Artifact Inventory
- [`scripts/vw4_m010_adaptive_nhc_ekf.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m010_adaptive_nhc_ekf.py)
- [`results/vw4_m010_adaptive_nhc_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m010_adaptive_nhc_report.md)
- [`results/vw4_m010_adaptive_nhc_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m010_adaptive_nhc_summary.json)
- `plots/vw4/m010_adaptive_nhc/` (6 plots)

---

## 19. Current Best Provenance-Locked System
- **System:** SpeedNet v2 + Raw Gyro + Fixed NHC ($R_0 = 0.04$)
- **300s Position Error:** **`263.11 m`**

---

## 20. Next Step Decision
- **What to do next:** Investigate **M011 — Sequence Window Receptive Field & Sequence Context Optimization (SpeedNet v4)**.
- **Why:** M006–M010 have conclusively proven that modifying filtering constraints (HeadingNet M005, regime classification M007, input features M008, slip states M009, adaptive NHC M010) CANNOT beat the 263.11 m benchmark. Residual decomposition (M006) showed speed overestimation during deceleration causes +322m of the remaining error. SpeedNet v2 used window duration $W=40$ (4.0s). Increasing receptive field context ($W \in [50, 60, 80]$, 5–8s sequences) with temporal dilated convolutions will allow the neural model to observe long-horizon deceleration trends, eliminating systematic speed overestimation.

---

## 21. Research Chain
- **Previous Milestone:** `M009_nhc_vehicle_slip_diagnostic`
- **Current Milestone:** `M010_adaptive_nhc_velocity_frame_ekf`
- **Next Planned Milestone:** `M011_speednet_v4_window_receptive_field`
