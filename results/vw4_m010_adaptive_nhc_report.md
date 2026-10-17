# Milestone M010 — Adaptive NHC Measurement Covariance & Velocity-Frame EKF Report

## Executive Summary

**Experiment:** `scripts/vw4_m010_adaptive_nhc_ekf.py`
**Dataset:** Vw04, unseen test partition, `start_idx = 108,000`
**Provenance-Locked Benchmark:** SpeedNet v2 + Raw Gyro + Fixed NHC = **`263.11 m` @ 300s**
**M010 Verdict:** **REJECTED**

- **Validation Parameter Selection:**
  - Swept $\kappa \in [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0]$ and $R_{\max} \in [1.0, 5.0, 20.0, 100.0]$ on validation set (`88566:107535`).
  - Selected parameters: **`$\kappa = 250.0$, $R_{\max} = 100.0$`** (Validation 300s error = `836.30 m`).
- **Locked Unseen Test Evaluation (Case F: Selected Model):**
  - **300s Position Error:** **`886.53 m`** (+623.42 m / +236.9% worse than benchmark `263.11 m`).
- **Baseline Reproduction:** Case A reproduced **`263.11 m`** at 300s with 100% precision.

> **Key Scientific Discovery:** Relaxing NHC measurement covariance ($R_{\text{nhc}}$ inflation) during dynamic cornering **degrades navigation performance**. When $R_{\text{nhc}}$ is inflated from $0.04\text{ m}^2/\text{s}^2$ up to $2.84\text{ m}^2/\text{s}^2$ during turns, the EKF loses lateral velocity anchor stability, allowing accumulated heading integration noise to project unconstrained lateral velocity drift into global position estimates ($1031.6\text{ m}$ in no-NHC limit vs $263.1\text{ m}$ in rigid NHC).

---

## 1. Experimental Methodology & Validation Selection

- **Formulation:** $R_{\text{nhc}}(\omega) = \text{clip}\left(R_0 \cdot (1 + \kappa \cdot |\omega_{\text{yaw}}|^2), R_0, R_{\max}\right)$, where $R_0 = 0.04\text{ m}^2/\text{s}^2$.
- **Validation Protocol:** 36 parameter combinations swept exclusively on validation outage (`88566:107535`).
- **Validation Selection:** $\kappa = 250.0, R_{\max} = 100.0$ achieved the lowest validation 300s error (`836.30 m`).

---

## 2. Locked Evaluation Results (Unseen Test Partition `start_idx = 108,000`)

| Case ID & Description | $\kappa$ | $R_{\max}$ | Use NHC | 60s Pos Error (m) | 120s Pos Error (m) | 300s Pos Error (m) | 300s CDE % | vs Benchmark |
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

## 3. Maneuver Regime Analysis (Fixed vs Adaptive NHC)

| Maneuver Regime | % Outage Time | Fixed $R_{\text{nhc}}$ (m²/s²) | Adaptive $R_{\text{nhc}}$ (m²/s²) | Fixed Residual MAE (m/s) | Adaptive Residual MAE (m/s) |
|---|---:|---:|---:|---:|---:|
| **Stationary** | 35.2% | 0.0400 | 0.0459 | 0.0024 m/s | 0.0040 m/s |
| **Acceleration** | 10.7% | 0.0400 | 1.1072 | 0.4205 m/s | 0.8155 m/s |
| **Braking** | 12.3% | 0.0400 | 0.5920 | 0.2948 m/s | 0.5967 m/s |
| **Straight/Cruise** | 21.4% | 0.0400 | 0.8296 | 0.3868 m/s | 0.7408 m/s |
| **Moderate Turn** | 17.2% | 0.0400 | 0.9696 | 0.4344 m/s | 0.9000 m/s |
| **Strong Turn** | 3.2% | **0.0400** | **2.8438** | **0.8054 m/s** | **2.5896 m/s** |

---

## 4. Scientific Explanation: Why Adaptive NHC Failed

1. **Loss of Lateral Velocity Anchor:** Enforcing rigid $R_0 = 0.04$ acts as a continuous low-pass anchor on lateral velocity states ($v_{\text{lat}} \approx 0$). Inflating $R_{\text{nhc}}$ to $2.84\text{ m}^2/\text{s}^2$ during turns opens the filter gain, allowing velocity integration errors to drift freely into lateral position components.
2. **Cumulative Drift Dominance:** While relaxing $R_{\text{nhc}}$ reduces local update residual spikes during turns, the unanchored velocity states drift rapidly during turn exits, producing an overall 300s position error of `886.53 m` (closer to the no-NHC limit of `1031.63 m`).

---

## 5. Artifact Inventory

- **Script:** [`scripts/vw4_m010_adaptive_nhc_ekf.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m010_adaptive_nhc_ekf.py)
- **Summary JSON:** [`results/vw4_m010_adaptive_nhc_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m010_adaptive_nhc_summary.json)
- **Plots Directory:** [`plots/vw4/m010_adaptive_nhc/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/m010_adaptive_nhc/) (6 plots)
- **Milestone:** [`milestones/M010_adaptive_nhc_velocity_frame_ekf.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/milestones/M010_adaptive_nhc_velocity_frame_ekf.md)
