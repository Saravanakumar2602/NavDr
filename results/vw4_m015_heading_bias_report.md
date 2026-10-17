# Milestone M015 — Controlled Heading-Error Experiment Report

## Executive Summary

- **Milestone:** M015 — Controlled Heading-Error Experiment
- **Objective:** Determine whether accumulated heading/yaw drift is the remaining primary navigation bottleneck and evaluate if causal stationary gyro bias estimation or turn-aware heading gating can reduce the current $233.18\text{ m}$ @ 300s benchmark without ground-truth leakage.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M014 Control Reproduction:** **100% Exact Match** ($27.36\text{ m}$ @ 60s, $428.45\text{ m}$ @ 120s, **`233.18 m` @ 300s**).
  - **Stationary Gyro Bias Estimation (F2):** Causal zero-angular-rate update (ZARU) for gyro bias reduced mean heading error from $64.62^\circ$ down to $36.12^\circ$ (a **$44.1\%$ reduction in heading error**) and improved short/mid-horizon position error ($27.36 \rightarrow 17.80\text{ m}$ @ 60s, $428.45 \rightarrow 264.48\text{ m}$ @ 120s).
  - **300s Position Degradation:** Despite reducing heading error by $44\%$, stationary gyro bias correction degraded 300s position drift from **`233.18 m` to `324.70 m`** ($+39.2\%$ degradation).
  - **Turn Clamping & Confidence Gating (F3 & F4):** Turn rate limits ($15^\circ/\text{s}$ cap) and confidence gating degraded 300s position error to $1091.87\text{ m}$ and $1352.76\text{ m}$, respectively.
  - **Core Scientific Insight:** Demonstrated a fundamental task-metric mismatch between heading error and integrated position drift. Small residual un-corrected gyro bias in raw gyro integration creates a geometric trajectory curvature that partially offsets NHC velocity propagation drift over 300 seconds. Causal bias corrections break this geometric cancellation, worsening long-horizon position drift.

---

## M014 Baseline Control Reproduction Verification

- **Target Benchmark (M014 F3 Winner):**
  - 60s Outage: `27.36 m`
  - 120s Outage: `428.45 m`
  - 300s Outage: `233.18 m`
- **Measured F0 Control:**
  - 60s Outage: `27.36 m`
  - 120s Outage: `428.45 m`
  - 300s Outage: `233.18 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Baseline Heading Error Regime Decomposition (F0 Control)

Evaluated over the 300s test outage (3,000 samples at 10 Hz):

| Driving Regime | Sample Count | Mean Heading Error (deg) | Max Heading Error (deg) |
|---|---|---|---|
| **Stationary** | 1,055 | $99.27^\circ$ | $179.82^\circ$ |
| **Acceleration** | 836 | $48.42^\circ$ | $149.62^\circ$ |
| **Braking** | 725 | $43.90^\circ$ | $150.86^\circ$ |
| **Straight / Cruise** | 146 | $48.61^\circ$ | $152.10^\circ$ |
| **Moderate Turn** | 577 | $41.40^\circ$ | $146.31^\circ$ |
| **Strong Turn** | 837 | $49.75^\circ$ | $147.80^\circ$ |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Mean H.Err | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control)** | M014 Benchmark (ZUPT + M013 F4) | $64.62^\circ$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | Stationary Bias Only (ZARU) | $38.74^\circ$ | $14.41\text{ m}$ | $300.78\text{ m}$ | $363.53\text{ m}$ | $+38.2\%$ | $+43.1\%$ | $+55.9\%$ |
| **F2** | Stationary Bias + M014 | **36.12°** | **17.80 m** | **264.48 m** | $324.70\text{ m}$ | $+23.4\%$ | $+27.8\%$ | $+39.2\%$ |
| **F3** | Turn-Aware Clamping ($15^\circ/\text{s}$) | $69.73^\circ$ | $132.28\text{ m}$ | $414.78\text{ m}$ | $1091.87\text{ m}$ | $+315.0\%$ | $+329.7\%$ | $+368.3\%$ |
| **F4** | Heading Confidence Gating | $73.34^\circ$ | $74.22\text{ m}$ | $559.27\text{ m}$ | $1352.76\text{ m}$ | $+414.1\%$ | $+432.4\%$ | $+480.1\%$ |
| **F5** | Best Validated + M014 (F2) | **36.12°** | **17.80 m** | **264.48 m** | $324.70\text{ m}$ | $+23.4\%$ | $+27.8\%$ | $+39.2\%$ |

---

## Detailed Heading-Specific Metrics

| Candidate | Mean H.Err | Median H.Err | P95 H.Err | Final H.Err | 60s Position | 120s Position | 300s Position |
|---|---|---|---|---|---|---|---|
| **F0 Control** | $64.62^\circ$ | $46.99^\circ$ | $149.33^\circ$ | $147.24^\circ$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** |
| **F2 (ZARU Bias + M014)** | **36.12°** | **25.29°** | **83.15°** | **81.04°** | **17.80 m** | **264.48 m** | $324.70\text{ m}$ |
| **F3 (Turn Clamping)** | $69.73^\circ$ | $51.04^\circ$ | $154.12^\circ$ | $151.09^\circ$ | $132.28\text{ m}$ | $414.78\text{ m}$ | $1091.87\text{ m}$ |

---

## Failure & Success Mechanism Analysis

1. **Heading Metric vs Navigation Metric Disconnect:**
   F2 (Stationary Bias + M014) reduced mean heading error from $64.62^\circ$ to $36.12^\circ$ and P95 heading error from $149.33^\circ$ to $83.15^\circ$, achieving superior short/mid horizon accuracy ($17.80\text{ m}$ @ 60s, $264.48\text{ m}$ @ 120s). However, at 300s, position error increased to $324.70\text{ m}$.
2. **Geometric Self-Cancellation Mechanism:**
   In the raw gyro control (F0), unadjusted gyro bias causes a constant slow rotation rate that bends the integrated trajectory into a mild curve. Over a 300-second closed-loop trajectory, this curvature happens to fold the trajectory back toward the origin, canceling out longitudinal over-speed drift. Correcting the gyro bias removes this artificial curvature, resulting in a straighter trajectory that drifts further away from ground truth at 300s.
3. **Turn Clamping Failure (F3 & F4):**
   Clamping maximum turn rate during sharp turns removes genuine rotational dynamics, leading to severe orientation mis-tracking and catastrophic position drift ($>1000\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m015_heading_bias_and_turn_aware_fusion.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m015_heading_bias_and_turn_aware_fusion.py)
- **Summary JSON:** `results/vw4_m015_heading_bias_summary.json`
- **Predictions NPZ:** `results/vw4_m015_heading_bias_predictions.npz`
- **Plot Directory:** `plots/vw4/m015_heading_bias_and_turn_aware_fusion/`
  - `pos_error_vs_time.png`
  - `heading_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Conclusion & Benchmark Status

Milestone M015 is **REJECTED**. The current active project benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$
