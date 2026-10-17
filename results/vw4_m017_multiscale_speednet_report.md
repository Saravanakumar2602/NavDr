# Milestone M017 — Multi-Scale Temporal SpeedNet Ensemble Report

## Executive Summary

- **Milestone:** M017 — Multi-Scale Temporal SpeedNet Ensemble
- **Objective:** Determine whether shorter temporal sequence windows ($W=20$, $W=30$) or multi-scale temporal ensembling ($W=20 + W=40$) can improve SpeedNet's responsiveness to rapid braking/deceleration transients and reduce 300-second navigation position drift below $233.18\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M014 Baseline Control Reproduction:** **100% Exact Match** ($27.36\text{ m}$ @ 60s, $428.45\text{ m}$ @ 120s, **`233.18 m` @ 300s**).
  - **Shorter Windows Increased Braking Error:** $W=20$ increased braking MAE from $11.62\text{ km/h}$ to $13.01\text{ km/h}$, and $W=30$ increased braking MAE to $14.09\text{ km/h}$.
  - **Shorter Windows Degraded Navigation:** $W=20$ degraded 300s position error from **`233.18 m` to `745.76 m`** ($+219.8\%$ degradation). $W=30$ degraded 300s position error to **`1299.97 m`** ($+457.5\%$ degradation).
  - **Multi-Scale Ensembling (F4 & F5):** Combining $W=20$ and $W=40$ predictions ($\alpha = 0.25$ selected via validation) resulted in $657.56\text{ m}$ @ 300s ($+182.0\%$ degradation). Braking-selective ensembling (F5) resulted in $685.55\text{ m}$ @ 300s ($+194.0\%$ degradation).
  - **Core Scientific Insight:** $W=40$ (4.0 seconds of IMU temporal history) provides the optimal balance of temporal smoothing and kinematic context. Shorter windows ($W=20$, $W=30$) fail to average out vehicle vibration and pitch dynamics, introducing high-frequency prediction noise that degrades EKF velocity propagation.

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

## SpeedNet Architecture & Temporal Preprocessing Audit

- **Model Backbone:** 1D-CNN (32, 64 filters, kernel size 3) + BiLSTM (hidden dim 64, bidirectional) + Shared FC (64) + Multi-task regression heads.
- **Input Channels:** 6 IMU features (`ax_lin`, `ay_lin`, `az_lin`, `gx`, `gy`, `gz`) normalized by training partition mean/std.
- **Temporal Alignment Verification:** For any sequence window $W$, the target speed $v_{\text{gt}}$ is defined at the final timestep index $i + W - 1$. Identical feature scaling, loss function ($\text{SmoothL1Loss}$), optimizer ($\text{Adam}$), learning rate schedule ($\text{CosineAnnealingLR}$), and data splits were used across $W=20, 30, 40$.

---

## Driving Regime Speed MAE Breakdown (km/h)

Evaluated over the 300s test outage (3,000 samples at 10 Hz):

| Driving Regime | Count | F0 (W=40) | F1 (W=20) | F2 (W=30) | F4 (Ensemble $\alpha=0.25$) | F5 (Braking Ens) |
|---|---|---|---|---|---|---|
| **Stationary** | 1,055 | $0.29\text{ km/h}$ | $0.27\text{ km/h}$ | $0.14\text{ km/h}$ | $0.28\text{ km/h}$ | $0.29\text{ km/h}$ |
| **Acceleration** | 836 | $11.63\text{ km/h}$ | $12.62\text{ km/h}$ | $14.35\text{ km/h}$ | $11.64\text{ km/h}$ | $11.63\text{ km/h}$ |
| **Braking** | 725 | **11.62 km/h** | $13.01\text{ km/h}$ | $14.09\text{ km/h}$ | $11.77\text{ km/h}$ | $12.51\text{ km/h}$ |
| **Straight / Cruise** | 146 | **4.95 km/h** | $6.02\text{ km/h}$ | $7.11\text{ km/h}$ | $5.04\text{ km/h}$ | $4.95\text{ km/h}$ |
| **Moderate Turn** | 577 | $12.10\text{ km/h}$ | $12.53\text{ km/h}$ | $14.21\text{ km/h}$ | $11.90\text{ km/h}$ | $12.05\text{ km/h}$ |
| **Strong Turn** | 837 | **13.20 km/h** | $15.17\text{ km/h}$ | $17.20\text{ km/h}$ | $13.50\text{ km/h}$ | $14.02\text{ km/h}$ |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control W=40)** | SpeedNet v2 W=40 Baseline Control | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | SpeedNet v2 W=20 | $8.10\text{ km/h}$ | $13.01\text{ km/h}$ | $56.87\text{ m}$ | $676.32\text{ m}$ | $745.76\text{ m}$ | $+183.4\%$ | $+193.5\%$ | $+219.8\%$ |
| **F2** | SpeedNet v2 W=30 | $9.09\text{ km/h}$ | $14.09\text{ km/h}$ | $193.08\text{ m}$ | $1117.46\text{ m}$ | $1299.97\text{ m}$ | $+394.1\%$ | $+411.6\%$ | $+457.5\%$ |
| **F3** | SpeedNet v2 W=40 Reference | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F4** | W20+W40 Ensemble ($\alpha=0.25$) | $7.40\text{ km/h}$ | $11.77\text{ km/h}$ | $37.63\text{ m}$ | $493.77\text{ m}$ | $657.56\text{ m}$ | $+149.9\%$ | $+158.8\%$ | $+182.0\%$ |
| **F5** | Braking-Selective Ensemble | $7.57\text{ km/h}$ | $12.51\text{ km/h}$ | $66.32\text{ m}$ | $456.74\text{ m}$ | $685.55\text{ m}$ | $+160.6\%$ | $+169.8\%$ | $+194.0\%$ |

---

## Detailed Braking Metrics & Lag Analysis

| Candidate | Braking Speed MAE | Braking Speed Bias | Braking P95 Error | 300s Position Error |
|---|---|---|---|---|
| **F0 (W=40 Control)** | **11.62 km/h** | **+2.73 km/h** | **23.11 km/h** | **233.18 m** |
| **F1 (W=20)** | $13.01\text{ km/h}$ | $+3.45\text{ km/h}$ | $27.54\text{ km/h}$ | $745.76\text{ m}$ |
| **F2 (W=30)** | $14.09\text{ km/h}$ | $+4.12\text{ km/h}$ | $29.80\text{ km/h}$ | $1299.97\text{ m}$ |
| **F4 (W20+W40 Ensemble)** | $11.77\text{ km/h}$ | $+2.91\text{ km/h}$ | $24.02\text{ km/h}$ | $657.56\text{ m}$ |

- **Phase Lag Analysis:** Shorter sequence windows ($W=20$) did NOT reduce phase lag during braking; instead, $W=20$ increased high-frequency prediction noise during transient deceleration, causing higher peak overshoot ($27.54\text{ km/h}$ P95 error).

---

## Failure & Success Mechanism Analysis

1. **Why Shorter Sequence Windows ($W=20, W=30$) Failed:**
   Inertial sensors on road vehicles experience continuous high-frequency engine vibration, road bump noise, and transient chassis pitch dynamics. A $W=40$ window (4.0 seconds at 10 Hz) provides necessary temporal filtering for the BiLSTM backbone to separate true longitudinal vehicle motion from high-frequency vibration. Truncating the window to $W=20$ (2.0 seconds) degrades the network's ability to filter out pitch noise, resulting in noisier speed predictions across all regimes.
2. **Impact on EKF Integration:**
   High-variance speed predictions feed directly into the EKF measurement update, introducing random walk velocity noise that accumulates into severe 300s position drift ($233.18\text{ m} \rightarrow 745.76\text{ m}$).

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m017_multiscale_speednet.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m017_multiscale_speednet.py)
- **Summary JSON:** `results/vw4_m017_multiscale_speednet_summary.json`
- **Predictions NPZ:** `results/vw4_m017_multiscale_speednet_predictions.npz`
- **Plot Directory:** `plots/vw4/m017_multiscale_speednet/`
  - `pos_error_vs_time.png`
  - `speed_prediction_decel_zoom.png`
  - `trajectory_comparison.png`

---

## Conclusion & Benchmark Status

Milestone M017 is **REJECTED**. The active verified project benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$
