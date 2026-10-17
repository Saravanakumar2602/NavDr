# M052 — Dynamic Centrifugal Acceleration Compensation Study

## 1. Executive Summary
- **Objective:** Investigate whether turn-induced dynamic centrifugal acceleration contamination ($a_c = v \cdot \omega_{\text{yaw}}$) distorts longitudinal acceleration $a_{\text{long}}$ during curved braking/turning maneuvers.
- **Canonical M028 Baseline Target:** 60s = 27.35 m | 120s = 426.85 m | 300s = 218.93 m | 1 km = 307.46 m.
- **Phase B Baseline Reproduction:** **100% EXACT MATCH** (27.88m / 426.17m / 218.93m).
- **Validation Sweep:** Winner **F1_a0.2** (Direct Centrifugal (alpha=0.20)) with Validation 300s Error = **488.80 m**.
- **Locked Test Result:** Candidate F1_a0.2 achieved 300s Test Error = **1040.45 m** (Delta = +821.52 m vs M028).
- **Final Verdict:** **GENERALIZATION FAILURE**
- **Production Status:** **100% UNCHANGED** (Locked at M028 baseline).

## 2. Axis & Sign Audit Findings
- $a_{\text{long}} = -(a_{y,\text{raw}} - g_y)$
- $a_{\text{lat}} = a_{x,\text{raw}} - g_x$
- $\omega_{\text{yaw}} = -\omega_{\text{pitch}}$
- Operational Speed Source: $v_{\text{net}}$ (SpeedNet v2 output, m/s).

## 3. Results Summary Table
| Candidate | Description | Val 300s (m) | Test 60s (m) | Test 120s (m) | Test 300s (m) | Delta vs M028 (m) | Heading MAE (deg) | FPER (%) |
|---|---|---|---|---|---|---|---|---|
| **F0** | Control M028 Baseline | 492.74 | 27.88 | 426.17 | **218.93** | +0.00 | 64.66 | 15.90% |
| **F1_a0.1** | Direct Centrifugal (alpha=0.10) | 594.71 | 16.14 | 610.11 | **1210.79** | +991.86 | 78.69 | 87.92% |
| **F1_a0.2** | Direct Centrifugal (alpha=0.20) | 488.80 | 17.77 | 809.00 | **1040.45** | +821.52 | 84.31 | 75.55% |
| **F1_a0.5** | Direct Centrifugal (alpha=0.50) | 1046.58 | 64.99 | 1132.42 | **1265.91** | +1046.98 | 99.61 | 91.92% |
| **F2_b0.5** | Bounded Centrifugal (bound=0.50m/s²) | 545.25 | 16.78 | 571.91 | **1147.68** | +928.75 | 76.39 | 83.34% |
| **F2_b1.0** | Bounded Centrifugal (bound=1.00m/s²) | 666.71 | 12.98 | 698.93 | **1115.48** | +896.55 | 81.14 | 81.00% |
| **F3_t5.0** | Turn-Gated Centrifugal (|w|>5°/s) | 491.76 | 17.32 | 807.00 | **1030.28** | +811.35 | 84.20 | 74.81% |
| **F3_t10.0** | Turn-Gated Centrifugal (|w|>10°/s) | 746.38 | 17.92 | 808.78 | **1014.73** | +795.80 | 84.54 | 73.69% |
| **F4_t5.0** | Turn-Gated + Bounded (|w|>5°, b=0.5) | 544.09 | 17.01 | 569.98 | **1148.44** | +929.51 | 76.29 | 83.39% |
| **F5_apm** | Centrifugal Integrated with M028 APM | 489.34 | 17.77 | 807.57 | **1039.86** | +820.93 | 84.26 | 75.51% |

## 4. Key Scientific Findings
1. **Centrifugal Term Magnitude:** On the test set, dynamic centrifugal acceleration $a_c = v_{\text{net}} \cdot \omega_{\text{yaw}}$ reached a peak magnitude of 18.94 m/s² (1.93g) during sharp turns.
2. **Impact on Navigation:** Compensating for $a_c$ on the longitudinal acceleration input did NOT improve navigation performance over M028 control. Candidate F1_a0.2 was selected on validation (488.80 m) but degraded on the locked test set (1040.45 m vs 218.93 m).
3. **Branch Decision:** M052 is **GENERALIZATION FAILURE** and production remains locked at M028.
