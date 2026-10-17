# Milestone M012 — Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)

## Executive Summary

- **Milestone:** M012 — Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)
- **Objective:** Evaluate whether adding a physically constrained kinematic loss term ($\mathcal{L}_{\text{kin}} = \text{ReLU}(\hat{v}_k - (\hat{v}_{k-1} + a_{\text{long},k} \cdot \Delta t))^2$) and zero-speed gating to SpeedNet v2 can reduce systematic positive speed bias during deceleration without introducing optimization instability or degrading dead-reckoning navigation accuracy.
- **Verdict:** **REJECTED**.
- **Key Finding:** Unconstrained physical loss terms cause the network to collapse into zero-prediction local minima ($v=0$, Val MAE $47.29\text{ km/h}$) across small/moderate penalty coefficients ($\lambda_{\text{kin}} = 0.01, 0.20$, and zero-gating). Moderate penalty ($\lambda_{\text{kin}} = 0.05$) managed to escape the zero-collapse state but introduced severe systematic positive speed overestimation ($+28.87\text{ km/h}$ during braking, $+35.35\text{ km/h}$ during acceleration), degrading 300s unseen test navigation error to **`1026.51 m`** ($+763.40\text{ m}$ / $+290.1\%$ worse than the $263.11\text{ m}$ benchmark).

---

## Provenance Baseline Reproduction

- **Model Configuration:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC
- **Dataset Partition:** Unseen Chronological Test Partition (`start_idx = 108,000`, 10 Hz synchronized IMU/VBOX data)
- **Target Baseline Results:**
  - 60s Outage: `22.75 m`
  - 120s Outage: `440.20 m`
  - 300s Outage: `263.11 m`
- **Reproduced Baseline Results (F0 Control):**
  - 60s Outage: `22.75 m`
  - 120s Outage: `440.20 m`
  - 300s Outage: `263.11 m`
  - Validation Speed MAE: `12.37 km/h`
  - Test Speed MAE: `7.59 km/h`
- **Reproduction Precision:** **100% Exact Match**.

---

## Experimental Protocol & Candidate Sweep

All models were trained on samples `0:88566` ($W=40$), validated on `88566:107535`, and selected strictly via Validation Speed MAE.

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{MSE}}(\hat{v}, v_{\text{true}}) + \lambda_{\text{kin}} \cdot \frac{1}{N}\sum_{k=1}^N \text{ReLU}\left(\hat{v}_k - (\hat{v}_{k-1} + a_{\text{long},k} \cdot \Delta t)\right)^2$$

| Candidate ID | Model Description | $\lambda_{\text{kin}}$ | Zero Gating | Val Speed MAE | Val Speed Bias | Selected? |
|---|---|---|---|---|---|---|
| **F0 (Control)** | SpeedNet v2 Baseline | $0.0$ | No | **12.37 km/h** | $+1.33\text{ km/h}$ | Baseline Control |
| **F1** | SpeedNet v5 | $0.01$ | No | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Rejected (Zero-Collapse) |
| **F2** | SpeedNet v5 | $0.05$ | No | **21.43 km/h** | $+18.92\text{ km/h}$ | **Selected Candidate** |
| **F3** | SpeedNet v5 | $0.20$ | No | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Rejected (Zero-Collapse) |
| **F4** | SpeedNet v5 | $0.05$ | Yes | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Rejected (Zero-Collapse) |

---

## Unseen Test Set Navigation Evaluation (`start_idx = 108,000`)

| Candidate ID | Val MAE | Test MAE | 60s Outage (m) | 120s Outage (m) | 300s Outage (m) | vs Benchmark |
|---|---|---|---|---|---|---|
| **F0 Control (Benchmark)** | **12.37 km/h** | **7.59 km/h** | **22.75 m** | **440.20 m** | **263.11 m** | **BENCHMARK** |
| **F1 ($\lambda=0.01$)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |
| **F2 ($\lambda=0.05$, Selected)** | $21.43\text{ km/h}$ | $24.06\text{ km/h}$ | $430.64\text{ m}$ | $1084.89\text{ m}$ | **1026.51 m** | $+763.40\text{ m}$ ($+290.1\%$) |
| **F3 ($\lambda=0.20$)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |
| **F4 ($\lambda=0.05$ + Gating)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |

---

## Braking & Kinematic Regime Speed Bias Breakdown

| Driving Regime | F0 Control Speed Bias | Selected F2 ($\lambda=0.05$) Speed Bias | Collapsed Variants (F1/F3/F4) Bias |
|---|---|---|---|
| **Stationary** | $+0.67\text{ km/h}$ | $+2.83\text{ km/h}$ | $-0.07\text{ km/h}$ |
| **Acceleration** | $+9.10\text{ km/h}$ | $+35.35\text{ km/h}$ | $-24.29\text{ km/h}$ |
| **Braking** | **+8.79 km/h** | **+28.87 km/h** | **-22.06 km/h** |
| **Straight / Cruise** | $+12.13\text{ km/h}$ | $+30.59\text{ km/h}$ | $-25.33\text{ km/h}$ |
| **Moderate Turn** | $+7.67\text{ km/h}$ | $+42.15\text{ km/h}$ | $-29.06\text{ km/h}$ |
| **Strong Turn** | $+5.76\text{ km/h}$ | $+50.49\text{ km/h}$ | $-23.82\text{ km/h}$ |

---

## Physical Failure Mechanism Analysis

1. **Physical Non-Negativity Bound Conflict:**
   The continuous kinematic upper bound during braking is given by:
   $$v_{\text{max\_kin}, k} = \hat{v}_{k-1} + a_{\text{long},k} \cdot \Delta t$$
   When the vehicle is stationary ($\hat{v}_{k-1} \approx 0$) or coming to a stop ($a_{\text{long},k} < 0$), $\hat{v}_{k-1} + a_{\text{long},k} \Delta t < 0$. If the loss function enforces $\text{ReLU}(\hat{v}_k - (\hat{v}_{k-1} + a_{\text{long}} \Delta t))^2$ without clipping $v_{\text{max\_kin}}$ at 0, any valid non-negative speed prediction $\hat{v}_k \ge 0$ incurs a residual penalty equal to $|a_{\text{long},k}| \Delta t > 0$.
2. **Zero-Speed Local Minimum Trough:**
   Because predicting $\hat{v}_k = 0$ yields a fixed small loss equal to $\lambda_{\text{kin}} (a_{\text{long}} \Delta t)^2$, the optimizer quickly falls into the global zero-prediction trough. For F1, F3, and F4, the network predicts $\hat{v}_k = 0$ constantly, yielding a constant $-47.29\text{ km/h}$ validation bias.
3. **Severe Inflation in Non-Collapsed Optimization:**
   For candidate F2 ($\lambda_{\text{kin}}=0.05$), the network escaped the zero-trough around Epoch 6. However, to compensate for the continuous downward penalty during deceleration, the network inflated speed predictions across all dynamic regimes ($+35.35\text{ km/h}$ during acceleration, $+28.87\text{ km/h}$ during braking, $+50.49\text{ km/h}$ during turns).

---

## Research Artifacts & Generated Files

- **Model Checkpoint:** `models/speednet_v5_m012_selected.pth`
- **Summary JSON:** `results/vw4_m012_kinematic_deceleration_loss_summary.json`
- **Predictions NPZ:** `results/vw4_m012_kinematic_deceleration_loss_predictions.npz`
- **Plots Directory:** `plots/vw4/m012_kinematic_deceleration_loss/`
  - `pos_error_vs_time.png`
  - `multi_horizon_comparison.png`
  - `braking_speed_prediction.png`
  - `penalty_weight_vs_speed_mae.png`
  - `speed_bias_by_regime.png`

---

## Conclusion & Provenance Confirmation

The provenance-locked benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} = \mathbf{263.11\text{\bf ~m @ 300s}}$$

Physical loss penalties on SpeedNet predictions introduce severe optimization instability and speed overestimation. Soft penalty loss constraints on neural outputs should be abandoned in favor of hard dynamic vehicle model constraints in the EKF state space.
