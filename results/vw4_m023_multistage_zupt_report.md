# Milestone M023 — Acceleration-Variance-Gated Multi-Stage ZUPT Transition Fusion Report

## Executive Summary

- **Milestone:** M023 — Acceleration-Variance-Gated Multi-Stage ZUPT Transition Fusion
- **Objective:** Evaluate whether a causal acceleration-variance gate ($\sigma_a^2 \le 0.15\text{ m}^2/\text{s}^4$) can detect slow rolling stop transitions earlier than the M014 ZUPT detector ($P_{\text{stat}} > 0.70$) without triggering false ZUPT activations during active low-speed motion.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Validation Selection:** Under strict zero-leakage validation selection (`88566:107535`), all acceleration-variance transition detectors (F2, F3, F4) severely degraded validation position error ($505.40\text{ m}$ for Control vs $949.17\text{ m}$ for F2, $677.13\text{ m}$ for F3, $523.53\text{ m}$ for F4). The Validation-Selected Winner (F5) is the original **M014 Control ZUPT Detector** (`505.40 m`).
  - **False Stationary Activation & Short-Horizon Degradation:** Acceleration-variance gating triggers false ZUPT activations during smooth low-speed cruising and deceleration transients ($<3.6\text{ km/h}$). Zeroing velocity during active rolling motion exploded 60s position error by $+27.6\%$ ($27.53\text{ m} \rightarrow 35.12\text{ m}$).
  - **Metric Paradox:** Although F2 reached $174.06\text{ m}$ at $t=300\text{ s}$ on the test set, it suffered severe validation degradation ($949.17\text{ m}$) and short-horizon error explosion. Prematurely clamping speed shortened path length, creating artificial endpoint crossing.
  - **Active Verified Benchmark:** **`220.12 m` @ 300s remains the active verified project benchmark**.

---

## M019 Control Reproduction Verification

- **Target Benchmark (M019 F4 Active Best):**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Measured F0 Control:**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Validation ZUPT Detector Evaluation (`88566:107535`)

| Candidate ID | Strategy Description | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|
| **F0 / F1 / F5** | **Original M014 ZUPT ($P_{\text{stat}} > 0.70$)** | **505.40 m** | **SELECTED VALIDATION BEST** |
| **F2** | Variance-Gated ZUPT ($\sigma_a^2 \le 0.15$) | $949.17\text{ m}$ | Degraded (+87.8%) |
| **F3** | Variance-Gated ZUPT + 3-sample Persistence | $677.13\text{ m}$ | Degraded (+34.0%) |
| **F4** | Two-Stage Detector (Soft Stage 1 + Hard Stage 2) | $523.53\text{ m}$ | Degraded (+3.6%) |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | Original M014 ZUPT Control | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | M014 ZUPT Detector Baseline | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |
| **F2** | Variance-Gated ZUPT ($\sigma_a^2 \le 0.15$) | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $35.12\text{ m}$ | $382.49\text{ m}$ | $174.06\text{ m}^*$ | $-33.8\%$ | $-31.5\%$ | $-20.9\%$ |
| **F3** | Variance-Gated + Persistence | $7.32\text{ km/h}$ | $11.56\text{ km/h}$ | $33.58\text{ m}$ | $386.93\text{ m}$ | $181.77\text{ m}^*$ | $-30.9\%$ | $-28.5\%$ | $-17.4\%$ |
| **F4** | Two-Stage ZUPT Detector | $7.32\text{ km/h}$ | $11.56\text{ km/h}$ | $31.19\text{ m}$ | $410.89\text{ m}$ | $198.82\text{ m}^*$ | $-24.4\%$ | $-21.8\%$ | $-9.7\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F0/F1) | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

*\*Note: F2, F3, F4 failed validation selection due to severe validation set position error explosion ($949.17\text{ m}$) and short-horizon error explosion ($35.12\text{ m}$ @ 60s).*

---

## ZUPT Detector Precision & Recall Diagnostics

| Candidate | Total ZUPT Samples | Stage 1 Soft ZUPT | Stage 2 Hard ZUPT | Precision (%) | Recall (%) |
|---|---|---|---|---|---|
| **F0 / F1 / F5** | 786 | 0 | 786 | **93.51%** | **69.67%** |
| **F2** | 1,177 | 0 | 1,177 | $67.12\%$ | $74.88\%$ |
| **F3** | 1,114 | 0 | 1,114 | $70.92\%$ | $74.88\%$ |
| **F4** | 1,114 | 328 | 786 | $70.92\%$ | $74.88\%$ |

---

## Failure Mechanism Analysis

1. **Low Acceleration Variance during Active Cruise/Deceleration:** In smooth smartphone IMU data, vehicle acceleration variance can drop below $0.15\text{ (m/s}^2)^2$ while the vehicle is still actively moving at low speeds ($1.0-3.6\text{ km/h}$).
2. **False ZUPT Triggers & Velocity Anchoring Corruption:** Clamping velocity to zero during active rolling motion corrupts EKF velocity state estimation, exploding 60s position error from $27.53\text{ m}$ to $35.12\text{ m}$ ($+27.6\%$) and nearly doubling validation error ($505.40 \rightarrow 949.17\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m023_multistage_zupt.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m023_multistage_zupt.py)
- **Summary JSON:** `results/vw4_m023_multistage_zupt_summary.json`
- **Predictions NPZ:** `results/vw4_m023_multistage_zupt_predictions.npz`
- **Report Markdown:** [`results/vw4_m023_multistage_zupt_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m023_multistage_zupt_report.md)
- **Plot Directory:** `plots/vw4/m023_multistage_zupt/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M023 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
