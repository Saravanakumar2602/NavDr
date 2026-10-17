# Milestone M012 — Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)

## 1. Executive Summary

- **Title:** Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)
- **Status:** **REJECTED**
- **Research Question:** Can a physically constrained speed-learning objective ($\mathcal{L}_{\text{kin}} = \text{ReLU}(\hat{v}_k - (\hat{v}_{k-1} + a_{\text{long},k} \Delta t))^2$) and zero-speed gating reduce systematic positive speed bias during deceleration without degrading dead-reckoning performance?
- **Key Finding:** Soft physical loss constraints cause optimization collapse into zero-prediction local minima or severe positive speed bias inflation ($+28.87\text{ km/h}$ braking bias), degrading 300s navigation error from $263.11\text{ m}$ to $1026.51\text{ m}$.

---

## 2. Research Context & Chain

- **Research Chain:** `M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012`
- **Preceding Milestone:** `M011 — SpeedNet v4 Temporal Context` (proved temporal window extension $W > 40$ introduces phase lag during braking).
- **Motivation:** M006, M008, and M011 consistently identified systematic braking speed overestimation ($+8.79\text{ km/h}$) as a key source of integrated position error. M012 investigates if constraining neural gradients using vehicle longitudinal acceleration ($a_{\text{long}}$) during deceleration forces the model to respect physical speed bounds.

---

## 3. Dataset & Provenance Protocol

- **Dataset:** Vw04 (10 Hz synchronized IMU/VBOX data)
- **Train Partition:** Samples `0 : 88566`
- **Val Partition:** Samples `88566 : 107535`
- **Unseen Test Partition:** Samples `108000 : 126505` (`start_idx = 108000`)
- **Evaluation Horizons:** 60 s (600 samples), 120 s (1200 samples), 300 s (3000 samples)
- **Anti-Leakage Rule:** Hyperparameter sweep and candidate selection strictly performed using Validation Speed MAE prior to locked test evaluation.

---

## 4. Methodological Formulation (SpeedNet v5)

SpeedNet v5 preserves the core BiLSTM architecture of SpeedNet v2 ($W=40$, 128 hidden units, 89,220 parameters) and introduces a composite loss function during training:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{MSE}}(\hat{v}, v_{\text{true}}) + \lambda_{\text{kin}} \cdot \mathcal{L}_{\text{kin}}$$

$$\mathcal{L}_{\text{kin}} = \frac{1}{N}\sum_{k=1}^N \text{ReLU}\left(\hat{v}_k - \left(\hat{v}_{k-1} + a_{\text{long},k} \cdot \Delta t\right)\right)^2$$

Where $a_{\text{long},k} = -(ay_{\text{raw}} - g_y)$ is the pitch-compensated longitudinal acceleration derived from accelerometer $ay_{\text{raw}}$ and gravity projection $g_y$.

---

## 5. Candidate Sweep & Validation Selection

| Candidate ID | Model Name | $\lambda_{\text{kin}}$ | Zero-Gating | Val Speed MAE | Val Speed Bias | Status |
|---|---|---|---|---|---|---|
| **F0 (Control)** | SpeedNet v2 Control | $0.0$ | No | **12.37 km/h** | $+1.33\text{ km/h}$ | Baseline Benchmark |
| **F1** | SpeedNet v5 | $0.01$ | No | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Collapsed ($v=0$) |
| **F2** | SpeedNet v5 | $0.05$ | No | **21.43 km/h** | $+18.92\text{ km/h}$ | **Selected Candidate** |
| **F3** | SpeedNet v5 | $0.20$ | No | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Collapsed ($v=0$) |
| **F4** | SpeedNet v5 | $0.05$ | Yes | $47.29\text{ km/h}$ | $-47.29\text{ km/h}$ | Collapsed ($v=0$) |

---

## 6. Baseline Reproduction Verification

- **Required Target:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC = `263.11 m` @ 300s
- **Measured Control Result (F0):**
  - 60s Error: `22.75 m`
  - 120s Error: `440.20 m`
  - 300s Error: `263.11 m`
- **Verification:** 100% exact reproduction confirmed.

---

## 7. Unseen Test Partition Results (`start_idx = 108000`)

| Variant | Val MAE | Test MAE | 60s Outage (m) | 120s Outage (m) | 300s Outage (m) | vs Benchmark |
|---|---|---|---|---|---|---|
| **F0 Control (Benchmark)** | **12.37 km/h** | **7.59 km/h** | **22.75 m** | **440.20 m** | **263.11 m** | **BENCHMARK** |
| **F1 ($\lambda=0.01$)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |
| **F2 ($\lambda=0.05$, Selected)** | $21.43\text{ km/h}$ | $24.06\text{ km/h}$ | $430.64\text{ m}$ | $1084.89\text{ m}$ | **1026.51 m** | $+763.40\text{ m}$ ($+290.1\%$) |
| **F3 ($\lambda=0.20$)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |
| **F4 ($\lambda=0.05$ + Gating)** | $47.29\text{ km/h}$ | $16.53\text{ km/h}$ | $382.63\text{ m}$ | $808.91\text{ m}$ | $819.31\text{ m}$ | $+556.20\text{ m}$ ($+211.4\%$) |

---

## 8. Braking & Driving Regime Speed Bias Diagnostic

| Driving Regime | F0 Control Speed Bias | Selected F2 ($\lambda=0.05$) Speed Bias | Collapsed Variants (F1/F3/F4) Bias |
|---|---|---|---|
| **Stationary** | $+0.67\text{ km/h}$ | $+2.83\text{ km/h}$ | $-0.07\text{ km/h}$ |
| **Acceleration** | $+9.10\text{ km/h}$ | $+35.35\text{ km/h}$ | $-24.29\text{ km/h}$ |
| **Braking** | **+8.79 km/h** | **+28.87 km/h** | **-22.06 km/h** |
| **Straight / Cruise** | $+12.13\text{ km/h}$ | $+30.59\text{ km/h}$ | $-25.33\text{ km/h}$ |
| **Moderate Turn** | $+7.67\text{ km/h}$ | $+42.15\text{ km/h}$ | $-29.06\text{ km/h}$ |
| **Strong Turn** | $+5.76\text{ km/h}$ | $+50.49\text{ km/h}$ | $-23.82\text{ km/h}$ |

---

## 9. Physical Failure Mechanism Analysis

The failure of physical loss penalization stems from two key mathematical and optimization pathologies:

1. **Non-Bound Zero Penalty Incursion:**
   When $\hat{v}_{k-1} = 0$ (stationary vehicle) and $a_{\text{long},k} < 0$ (sensor noise or slope inclination), $\hat{v}_{k-1} + a_{\text{long},k} \Delta t < 0$. The loss term penalizes $\hat{v}_k - (\text{negative value}) > 0$, forcing the network to predict negative speeds or collapse to zero.
2. **Global Zero-Prediction Local Minimum:**
   Predicting $\hat{v}_k = 0$ everywhere produces zero MSE on zero-speed segments and zero kinematic penalty whenever $a_{\text{long}} \le 0$, creating a strong attractor in weight space.
3. **Hyper-Inflation in Escaped Candidates:**
   When candidate F2 ($\lambda_{\text{kin}}=0.05$) escaped zero-collapse, the network inflated overall speed outputs to offset the downward loss gradient, resulting in $+28.87\text{ km/h}$ braking bias.

---

## 10. Saved Research Artifacts & Provenance Files

- **Implementation Script:** [`scripts/vw4_m012_kinematic_deceleration_loss.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m012_kinematic_deceleration_loss.py)
- **Selected Checkpoint:** `models/speednet_v5_m012_selected.pth`
- **Summary JSON:** `results/vw4_m012_kinematic_deceleration_loss_summary.json`
- **Predictions NPZ:** `results/vw4_m012_kinematic_deceleration_loss_predictions.npz`
- **Formal Report:** [`results/vw4_m012_kinematic_deceleration_loss_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m012_kinematic_deceleration_loss_report.md)
- **Plots Directory:** `plots/vw4/m012_kinematic_deceleration_loss/`

---

## 11. Final Milestone Verdict

**REJECTED**.

The true provenance benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} = \mathbf{263.11\text{\bf ~m @ 300s}}$$

Soft physical loss functions applied directly to neural predictions cause optimization collapse and severe navigation degradation. Hard kinematic constraints must be enforced inside the EKF state estimation framework rather than soft neural loss functions.
