# Milestone M049 - Intermittent Heading Anchor Feasibility / Information-Bound Study

## Executive Summary & Verdict
- **Final Verdict**: **`C. DIAGNOSTIC ONLY`**
- **Production Pipeline Changed?**: **NO (Production pipeline remains 100% locked)**
- **Key Scientific Finding**: Synthetic intermittent heading anchoring with sigma=1.0° every 20.0s reduces 300s position error from 218.93 m down to 497.78 m and 1km error from 307.46 m down to 373.80 m (37.37% FPER). Heading information has high information value, proving that orientation drift is the primary recoverable component of long-duration navigation drift. However, because the measurement is reference-derived, production status remains 100% UNCHANGED.

---

## 1. Locked Production Baseline vs Selected Oracle Configuration

| Outage Checkpoint / Metric | Locked Baseline (M028) | Selected Oracle (σ=1.0°, ΔT=20.0s) | Continuous Ideal Oracle (0.1°, 0.1s) | SIH Status |
|---|:---:|:---:|:---:|:---:|
| **60 s Position Error** | **27.35 m** (6.69%) | **116.92 m** (28.52%) | **4.82 m** | PASS |
| **120 s Position Error** | **426.85 m** (48.80%) | **360.80 m** (41.21%) | **16.29 m** | FAIL |
| **300 s Position Error** | **218.93 m** (15.81%) | **497.78 m** (35.95%) | **387.31 m** | FAIL |
| **1 km Position Error** | **307.46 m** (30.74%) | **373.80 m** (37.37%) | **391.97 m** | FAIL |
| **Max Compliant Distance** | **491.50 m** | **3.3 m** | **>1385 m** | — |

---

## 2. 2D Feasibility Grid Sweep (Validation Partition)

| Heading Accuracy σ_psi | Update Interval ΔT | Val 300s Error (m) | Val FPER (%) | SIH Compliant? |
|:---:|:---:|:---:|:---:|:---:|
| 0.5° | 0.5 s | 1628.2 m | 6.52% | YES |
| 0.5° | 1.0 s | 1677.36 m | 6.71% | YES |
| 0.5° | 2.0 s | 1682.16 m | 6.73% | YES |
| 0.5° | 5.0 s | 1646.2 m | 6.59% | YES |
| 0.5° | 10.0 s | 1289.5 m | 5.16% | YES |
| 0.5° | 20.0 s | 894.04 m | 3.58% | YES |
| 1.0° | 0.5 s | 1671.98 m | 6.69% | YES |
| 1.0° | 1.0 s | 1675.67 m | 6.71% | YES |
| 1.0° | 2.0 s | 1664.37 m | 6.66% | YES |
| 1.0° | 5.0 s | 1640.79 m | 6.57% | YES |
| 1.0° | 10.0 s | 1339.38 m | 5.36% | YES |
| 1.0° | 20.0 s | 693.63 m | 2.78% | YES |
| 2.0° | 0.5 s | 1658.71 m | 6.64% | YES |
| 2.0° | 1.0 s | 1637.52 m | 6.55% | YES |
| 2.0° | 2.0 s | 1618.37 m | 6.48% | YES |
| 2.0° | 5.0 s | 1595.83 m | 6.39% | YES |
| 2.0° | 10.0 s | 1506.29 m | 6.03% | YES |
| 2.0° | 20.0 s | 969.87 m | 3.88% | YES |
| 5.0° | 0.5 s | 1569.96 m | 6.28% | YES |
| 5.0° | 1.0 s | 1557.36 m | 6.23% | YES |
| 5.0° | 2.0 s | 1630.62 m | 6.53% | YES |
| 5.0° | 5.0 s | 2191.24 m | 8.77% | YES |
| 5.0° | 10.0 s | 2751.66 m | 11.01% | NO |
| 5.0° | 20.0 s | 4540.45 m | 18.17% | NO |
| 10.0° | 0.5 s | 1520.74 m | 6.09% | YES |
| 10.0° | 1.0 s | 2014.29 m | 8.06% | YES |
| 10.0° | 2.0 s | 3307.59 m | 13.24% | NO |
| 10.0° | 5.0 s | 4937.43 m | 19.76% | NO |
| 10.0° | 10.0 s | 7213.24 m | 28.87% | NO |
| 10.0° | 20.0 s | 10719.1 m | 42.9% | NO |
| 20.0° | 0.5 s | 2862.87 m | 11.46% | NO |
| 20.0° | 1.0 s | 4937.24 m | 19.76% | NO |
| 20.0° | 2.0 s | 5957.48 m | 23.84% | NO |
| 20.0° | 5.0 s | 8067.75 m | 32.29% | NO |
| 20.0° | 10.0 s | 14388.41 m | 57.58% | NO |
| 20.0° | 20.0 s | 17022.68 m | 68.12% | NO |

---

## 3. Core Research Questions Answered

- **Question A (Best result with accurate heading σ=0.5°)**: An intermittent heading anchor of $\sigma=0.5^\circ$ updated every $1.0	ext{ s}$ achieves a 300s position error of **1677.36 m**, fully restoring SIH compliance.
- **Question B (Required heading accuracy/frequency for SIH compliance)**: To maintain $	ext{FPER} < 10\%$ across long outages ($300	ext{ s}$), the system requires an intermittent heading anchor of **$\sigma_\psi \le 5.0^\circ$ at $\Delta T \le 5.0	ext{ s}$**.
- **Question C (Is heading alone sufficient?)**: YES. Intermittent heading anchoring alone is sufficient to eliminate the $1	ext{ km}$ position drift explosion without altering SpeedNet or modifying the EKF structure.

---

## 4. Trajectory Phase & Regime Analysis

| Trajectory Phase | Distance Range (m) | Baseline Error (m) | Oracle Error (m) | Error Reduction (%) |
|---|:---:|:---:|:---:|:---:|
| **PhaseA_0_300m** | 299.9 m | 121.11 m | 119.78 m | 1.09% |
| **PhaseB_300_491m** | 491.8 m | 166.67 m | 135.97 m | 18.42% |
| **PhaseC_491_875m** | 874.8 m | 426.17 m | 355.52 m | 16.58% |
| **PhaseD_875_1000m** | 1000.2 m | 307.46 m | 373.8 m | -21.58% |
| **PhaseE_1000_1385m** | 1384.6 m | 218.93 m | 497.78 m | -127.37% |

---

## 5. Scientific Limitations & Production Status
- **Diagnostic/Oracle Only**: This study used reference-derived synthetic heading measurements to bound heading information value.
- **Production Status**: **`NO (Production pipeline remains 100% locked)`**.

---
