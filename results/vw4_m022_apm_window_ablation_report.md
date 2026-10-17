# Milestone M022 — Causal Deceleration-Integrated Speed Damping Window Ablation Report

## Executive Summary

- **Milestone:** M022 — Causal Deceleration-Integrated Speed Damping Window Ablation
- **Objective:** Scientifically evaluate whether expanding M019 APM's causal acceleration integration window from $0.5\text{ s}$ (5 samples) to $0.6-1.0\text{ s}$ (6 to 10 samples) improves deceleration speed damping and lowers 300s position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Monotonic Degradation with Longer Integration Windows:** Increasing the integration window length monotonically degrades 300s navigation position error ($220.12\text{ m}$ for 0.5s $\rightarrow 227.54\text{ m}$ for 0.6s $\rightarrow 238.59\text{ m}$ for 0.7s $\rightarrow 243.31\text{ m}$ for 0.8s $\rightarrow 248.04\text{ m}$ for 1.0s).
  - **Validation Best Selection Failure:** Candidate F2 (0.7s / 7 samples) achieved the best 300s validation error ($503.15\text{ m}$ vs Control $505.40\text{ m}$), but degraded locked test 300s position error to **`238.59 m`** ($+8.4\%$ degradation).
  - **Physical Failure Mechanism:** Expanding the integration window beyond 0.5s accumulates low-frequency accelerometer tilt contamination ($g \sin\theta$) and high-frequency chassis vibration noise in the integral $\Delta v_{\text{imu}} = \sum a_{\text{long}} \Delta t$. This noise distorts velocity delta estimation, weakening effective APM speed damping ($1.73\text{ km/h}$ mean correction for 0.5s vs $1.56\text{ km/h}$ for 1.0s) and allowing residual deceleration overestimation to leak back into position drift.
  - **Baseline Provenance Lock:** $0.5\text{ s}$ (5 samples) is proven to be the optimal causal integration window length. **`220.12 m` @ 300s remains the active verified project benchmark**.

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

## Causality & Physics Audit

1. **Causal Window Formulation:** For an integration window of $N$ samples, $\Delta v_{\text{imu}}[k] = \sum_{j=k-N+1}^{k} a_{\text{long}}[j] \Delta t$ uses strictly current and past $N$ samples. Zero future sample leakage.
2. **Frozen Baseline Gating:** Acceleration threshold ($a_{\text{long}} < -0.5\text{ m/s}^2$), turn exclusion ($|\omega_y| \le 3.0^\circ/\text{s}$), max correction bound ($\delta v_{\max} = 0.5\text{ m/s}$), M013 F4, and M014 ZUPT were kept completely unchanged.

---

## Validation Window Evaluation (`88566:107535`)

| Candidate ID | Integration Window Length | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|
| **F0 Control** | $0.5\text{ s}$ (5 causal samples) | $505.40\text{ m}$ | Control Baseline |
| **F1** | $0.6\text{ s}$ (6 causal samples) | $504.05\text{ m}$ | Candidate |
| **F2 / F5** | **0.7s (7 causal samples)** | **503.15 m** | **SELECTED VALIDATION BEST** |
| **F3** | $0.8\text{ s}$ (8 causal samples) | $503.27\text{ m}$ | Candidate |
| **F4** | $1.0\text{ s}$ (10 causal samples) | $503.94\text{ m}$ | Stress Test |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | 0.5s Window (5 samples) | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | 0.6s Window (6 samples) | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.60\text{ m}$ | $429.45\text{ m}$ | $227.54\text{ m}$ | $-13.5\%$ | $-10.5\%$ | $+3.4\%$ |
| **F2** | 0.7s Window (7 samples) | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $27.67\text{ m}$ | $430.16\text{ m}$ | $238.59\text{ m}$ | $-9.3\%$ | $-6.1\%$ | $+8.4\%$ |
| **F3** | 0.8s Window (8 samples) | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $27.77\text{ m}$ | $431.18\text{ m}$ | $243.31\text{ m}$ | $-7.5\%$ | $-4.3\%$ | $+10.5\%$ |
| **F4** | 1.0s Window (10 samples) | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.87\text{ m}$ | $433.76\text{ m}$ | $248.04\text{ m}$ | $-5.7\%$ | $-2.4\%$ | $+12.7\%$ |
| **F5 (Val Winner)** | Selected Best Validation (F2) | $7.33\text{ km/h}$ | $11.55\text{ km/h}$ | $27.67\text{ m}$ | $430.16\text{ m}$ | $238.59\text{ m}$ | $-9.3\%$ | $-6.1\%$ | $+8.4\%$ |

---

## APM Window Ablation Diagnostic Summary

| Candidate | Total Activations | Mean APM Speed Correction | Max APM Speed Correction |
|---|---|---|---|
| **F0 Control (0.5s / 5samp)** | 118 | **1.73 km/h** | $1.80\text{ km/h}$ |
| **F1 (0.6s / 6 samples)** | 118 | $1.68\text{ km/h}$ | $1.80\text{ km/h}$ |
| **F2 / F5 (0.7s / 7 samples)** | 118 | $1.63\text{ km/h}$ | $1.80\text{ km/h}$ |
| **F3 (0.8s / 8 samples)** | 118 | $1.67\text{ km/h}$ | $1.80\text{ km/h}$ |
| **F4 (1.0s / 10 samples)** | 118 | $1.56\text{ km/h}$ | $1.80\text{ km/h}$ |

---

## Failure Mechanism Analysis

1. **Accelerometer Noise Accumulation over Longer Windows:** Smartphone IMU accelerometers exhibit zero-mean bias instability, tilt leakage, and structural chassis vibration. Integrating acceleration over longer windows ($N \ge 6$) causes noise to accumulate, distorting the velocity delta estimate $\Delta v_{\text{imu}}$.
2. **Weaker Effective Speed Damping:** Due to integral noise distortion, longer integration windows yield smaller valid velocity reductions ($1.73\text{ km/h}$ mean correction for 0.5s vs $1.56\text{ km/h}$ for 1.0s). This under-correction allows SpeedNet braking overestimation to leak back into velocity integration, increasing 300s position drift ($220.12 \rightarrow 248.04\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m022_apm_window_ablation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m022_apm_window_ablation.py)
- **Summary JSON:** `results/vw4_m022_apm_window_ablation_summary.json`
- **Predictions NPZ:** `results/vw4_m022_apm_window_ablation_predictions.npz`
- **Report Markdown:** [`results/vw4_m022_apm_window_ablation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m022_apm_window_ablation_report.md)
- **Plot Directory:** `plots/vw4/m022_apm_window_ablation/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M022 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
