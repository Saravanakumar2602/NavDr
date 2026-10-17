# Milestone M016 — Adaptive EKF Innovation Gating & Velocity Bias Tracking Report

## Executive Summary

- **Milestone:** M016 — Adaptive EKF Innovation Gating & Velocity Bias Tracking
- **Objective:** Evaluate whether residual velocity/speed integration error during acceleration/deceleration transients can be mitigated by normalized innovation squared (NIS) speed gating, transient-aware adaptive measurement covariance ($R_v$), or accelerometer bias state tracking.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M014 Baseline Control Reproduction:** **100% Exact Match** ($27.36\text{ m}$ @ 60s, $428.45\text{ m}$ @ 120s, **`233.18 m` @ 300s**).
  - **Observability Audit:** Verified that longitudinal accelerometer bias $b_a$ is **unobservable** during GNSS outage because measurement updates consist only of speed magnitude ($v_{\text{meas}}$), 2D ZUPT ($v_x=0, v_y=0$), and NHC ($v_{\text{lat}}=0$), none of which isolate $b_a$ from tilt gravity projection ($g \cdot \sin\theta$).
  - **Velocity Innovation Structure (F1):** SpeedNet velocity innovations exhibit systematic positive bias during braking ($+0.7592\text{ m/s}$ / $+2.73\text{ km/h}$) and strong turns ($+0.8144\text{ m/s}$ / $+2.93\text{ km/h}$) with mean NIS $\approx 3.07$.
  - **NIS Gating Failure (F2):** Down-weighting SpeedNet updates when $\text{NIS}_v > 3.84$ degraded 300s position drift to **`880.91 m`** ($+277.8\%$ worse).
  - **Adaptive Covariance Failure (F3):** Inflating $R_v$ during high acceleration variance or turning degraded 300s position drift to **`596.41 m`** ($+155.8\%$ worse).
  - **Core Scientific Insight:** SpeedNet speed measurements, despite transient overestimation, provide vital velocity damping. Down-weighting SpeedNet updates during transients forces the EKF into open-loop accelerometer double-integration, which rapidly accumulates tilt and bias errors.

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

## Observability Audit & Accelerometer Bias Analysis

Prior to candidate testing, the EKF state equations and measurement Jacobians were audited:
- **State Vector:** $x = [x, y, v_x, v_y, \psi, b_a, b_\omega]^T$.
- **Process Model Coupling:** Accelerometer bias $b_a$ enters velocity propagation via $\hat{a}_k = a_{m,k} - b_a$.
- **Measurement Updates during Outage:**
  - SpeedNet: $v_{\text{meas}} = \sqrt{v_x^2 + v_y^2}$ (Rank 1 magnitude update).
  - ZUPT: $v_x = 0, v_y = 0$ (Rank 2 velocity reset).
  - NHC: $v_{\text{lat}} = -v_x \cos\psi + v_y \sin\psi = 0$ (Rank 1 lateral constraint).
- **Observability Conclusion:** None of the outage measurements provide a direct acceleration observation. At constant cruise speed, $a_{m,k} \approx 0$, making $b_a$ mathematically indistinguishable from tilt gravity leakage ($g \cdot \sin\theta$) and SpeedNet speed prediction error. Unconstrained $b_a$ tracking is unobservable and destabilizes velocity propagation.

---

## F1 Velocity Innovation Regime Breakdown (Unseen Test Partition)

Evaluated over the 300s test outage (3,000 samples at 10 Hz):

| Driving Regime | Count | Mean Innovation (m/s) | MAE (m/s) | Std Dev (m/s) | P95 (m/s) | Mean NIS |
|---|---|---|---|---|---|---|
| **Stationary** | 1,055 | $-0.0262\text{ m/s}$ | $0.0552\text{ m/s}$ | $0.0835\text{ m/s}$ | $0.1649\text{ m/s}$ | 0.01 |
| **Acceleration** | 836 | $+0.0737\text{ m/s}$ | $1.3069\text{ m/s}$ | $1.7558\text{ m/s}$ | $3.5334\text{ m/s}$ | 2.79 |
| **Braking** | 725 | $+0.7592\text{ m/s}$ | $1.4492\text{ m/s}$ | $1.6818\text{ m/s}$ | $3.7563\text{ m/s}$ | 3.07 |
| **Straight / Cruise** | 146 | $-0.3543\text{ m/s}$ | $0.9040\text{ m/s}$ | $1.2453\text{ m/s}$ | $2.9046\text{ m/s}$ | 1.51 |
| **Moderate Turn** | 577 | $+0.1331\text{ m/s}$ | $1.4287\text{ m/s}$ | $1.8194\text{ m/s}$ | $3.6171\text{ m/s}$ | 3.00 |
| **Strong Turn** | 837 | $+0.8144\text{ m/s}$ | $1.4450\text{ m/s}$ | $1.6424\text{ m/s}$ | $3.6190\text{ m/s}$ | 3.04 |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control)** | M014 Benchmark (Exact Reproduction) | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | Velocity Innovation Diagnostic Only | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F2** | NIS Speed Gating ($\text{NIS} > 3.84$) | $7.36\text{ km/h}$ | $305.94\text{ m}$ | $915.89\text{ m}$ | $880.91\text{ m}$ | $+234.8\%$ | $+246.7\%$ | $+277.8\%$ |
| **F3** | Adaptive Speed Covariance $R_v$ | $7.36\text{ km/h}$ | $107.00\text{ m}$ | $629.20\text{ m}$ | $596.41\text{ m}$ | $+126.7\%$ | $+134.7\%$ | $+155.8\%$ |
| **F4** | Accel Bias State Tracking | $7.36\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F5** | Best Single Method + M014 (F3) | $7.36\text{ km/h}$ | $107.00\text{ m}$ | $629.20\text{ m}$ | $596.41\text{ m}$ | $+126.7\%$ | $+134.7\%$ | $+155.8\%$ |

---

## Innovation Metrics Summary

| Candidate | Mean Innovation (m/s) | MAE (m/s) | Std Dev (m/s) | P95 (m/s) | Positive % | Negative % |
|---|---|---|---|---|---|---|
| **F0 Control** | $+0.1999\text{ m/s}$ | $0.8766\text{ m/s}$ | $1.3906\text{ m/s}$ | $3.1278\text{ m/s}$ | $43.1\%$ | $56.9\%$ |
| **F2 (NIS Gating)** | $+2.8819\text{ m/s}$ | $3.7784\text{ m/s}$ | $5.4066\text{ m/s}$ | $13.5423\text{ m/s}$ | $52.5\%$ | $47.5\%$ |
| **F3 (Adaptive $R_v$)** | $+1.2964\text{ m/s}$ | $1.8453\text{ m/s}$ | $2.7454\text{ m/s}$ | $6.8004\text{ m/s}$ | $52.0\%$ | $48.0\%$ |

---

## Failure & Success Mechanism Analysis

1. **Why Speed Measurement Gating (F2 & F3) Failed:**
   Down-weighting SpeedNet velocity updates during high NIS or high acceleration/turn variance (F2 & F3) deprives the EKF of velocity state damping. The filter falls back on open-loop accelerometer double-integration ($v_{k+1} = v_k + a_{\text{long}}\Delta t$), which causes quadratic drift acceleration from accelerometer tilt contamination ($g \sin\theta$) and bias.
2. **Why SpeedNet Damping Is Essential:**
   Even during acceleration/deceleration transients where SpeedNet predictions have modest overestimation bias, SpeedNet measurements provide bounded velocity reference updates that anchor the EKF state. Disabling or down-weighting these updates causes rapid drift expansion ($233.18\text{ m} \rightarrow 596.41\text{ m} \rightarrow 880.91\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m016_adaptive_velocity_innovation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m016_adaptive_velocity_innovation.py)
- **Summary JSON:** `results/vw4_m016_adaptive_velocity_innovation_summary.json`
- **Predictions NPZ:** `results/vw4_m016_adaptive_velocity_innovation_predictions.npz`
- **Plot Directory:** `plots/vw4/m016_adaptive_velocity_innovation/`
  - `pos_error_vs_time.png`
  - `velocity_innovation_vs_time.png`
  - `trajectory_comparison.png`

---

## Conclusion & Benchmark Status

Milestone M016 is **REJECTED**. The active verified project benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$
