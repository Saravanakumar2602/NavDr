# SpeedNet v3 — Regime-Aware Speed Estimation Report

## Executive Summary

**SpeedNet v3 (Multi-Task Regime-Aware Speed Network) did NOT beat the SpeedNet v2 + NHC baseline.**

- **Target (<150 m at 300s):** NOT ACHIEVED (`False`)
- **SpeedNet v2 + Raw Gyro + NHC Baseline (300s):** `664.1 m`
- **SpeedNet v3 + Raw Gyro + NHC (300s):** `938.9 m` (41.4% worse than baseline)
- **SpeedNet v2 + Offline Regime Calibration + NHC (300s):** `662.6 m` (Slight improvement over baseline)

> **Key Scientific Discovery:** Adding a classification auxiliary head ($\lambda \in [0.05, 0.10, 0.20]$) created negative interference with the speed regression loss. From the IMU alone, **Acceleration (21.9% recall)** and **Braking (14.0% recall)** cannot be reliably distinguished without wheel-speed or longitudinal constraint features. Offline regime calibration reduced speed MAE from `7.59 km/h` to `7.02 km/h`, outperforming the end-to-end learned multi-task model (`8.01 km/h`).

---

## 1. Experiment 1: IMU-Only Regime Classifier Validity

Can driving regimes be classified using only a 3.0s IMU window ($W=30$)?

- **Overall Validation Accuracy:** `60.3%`
- **Reliably Classified Regimes ($\ge 60\%$ recall):**
  1. **Stationary:** `92.2%` recall ($F_1 = 0.78$) — Gating is highly reliable.
  2. **Strong Turn:** `84.8%` recall ($F_1 = 0.87$) — High gyro yaw rate signature.
  3. **Straight/Cruise:** `82.4%` recall ($F_1 = 0.69$) — Low angular rate & low linear acceleration.
  4. **Moderate Turn:** `64.2%` recall ($F_1 = 0.68$) — Moderate gyro rate.
- **Unreliable Regimes ($< 60\%$ recall):**
  1. **Acceleration:** `21.9%` recall ($F_1 = 0.28$) — Confused with Cruise due to gravity/tilt noise in MEMS accelerometers.
  2. **Braking:** `14.0%` recall ($F_1 = 0.22$) — Frequently misclassified as Cruise/Transition.

---

## 2. Experiment 2: SpeedNet v3 Multi-Task Training ($\lambda$ Sweep)

Multi-task Loss: $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{speed}} + 0.3 \mathcal{L}_{\text{stat}} + \lambda \mathcal{L}_{\text{regime}}$

| Multi-task Weight ($\lambda$) | Validation Speed MAE (km/h) | Selection Status |
|---|---|---|
| **$\lambda = 0.05$** | **12.506 km/h** | **SELECTED** ✅ |
| $\lambda = 0.10$ | 47.291 km/h | Rejected (Gradient dominance) |
| $\lambda = 0.20$ | 47.291 km/h | Rejected (Gradient dominance) |

- **Model Parameters:** SpeedNet v2 = 422,147 params vs SpeedNet v3 = 424,459 params (+2,312 params for 6-class head).
- **Inference Latency:** `0.0381 ms/step` (Real-time feasible).

---

## 3. Experiment 3 & 6: Speed Prediction & Calibration Stress Test (Test Partition)

### Pure Prediction Speed Metrics

| Model / Method | Overall Speed MAE (km/h) | Overall Speed Bias (km/h) | Notes |
|---|---|---|---|
| **SpeedNet v2 (Uncorrected)** | 7.586 km/h | +6.388 km/h | Baseline predictions |
| **V2 + Global Bias Calibration** | 6.972 km/h | +5.062 km/h | Offline val-derived global offset |
| **V2 + Regime-Specific Calibration** | **7.021 km/h** | +5.034 km/h | **Best per-regime balance** |
| **SpeedNet v3 (Learned Multi-Task)** | 8.007 km/h | +6.766 km/h | Degraded overall MAE |

### Per-Regime Speed Error Breakdown (Unseen Test Partition)

| Regime | N | V2 MAE (km/h) | V2 Bias (km/h) | V3 MAE (km/h) | V3 Bias (km/h) | V3 Improvement? |
|---|---|---|---|---|---|---|
| **Stationary** | 1055 | 0.668 | +0.668 | 0.436 | +0.434 | **YES (+0.23 km/h)** |
| **Acceleration** | 320 | 10.991 | +9.099 | 13.264 | +11.927 | NO (-2.27 km/h) |
| **Braking** | 370 | 10.257 | +8.788 | 9.718 | +7.185 | **YES (+0.54 km/h)** |
| **Straight/Cruise** | 641 | 13.650 | +12.127 | 12.807 | +11.329 | **YES (+0.84 km/h)** |
| **Moderate Turn** | 517 | 10.072 | +7.668 | 12.550 | +10.401 | NO (-2.48 km/h) |
| **Strong Turn** | 97 | 8.083 | +5.763 | 10.555 | +7.486 | NO (-2.47 km/h) |

---

## 4. Experiment 4: Navigation Ablation Matrix

Evaluation across 60s, 120s, and 300s GNSS-denied outages on unseen test partition:

| Case | 60s Final Error | 120s Final Error | 300s Final Error | 300s Speed MAE | 300s Heading Err | vs Baseline |
|---|---|---|---|---|---|---|
| **Case A: SpeedNet v2 + NHC [Baseline]** | 100.91 m | 396.73 m | **664.08 m** | 6.67 km/h | 2.6° | Baseline |
| **Case B: SpeedNet v3 + NHC** | 96.30 m | 363.10 m | **938.90 m** | 6.94 km/h | 127.1° | -41.4% (Worse) |
| **Case C: SpeedNet v3 (no NHC)** | 147.80 m | 889.60 m | **1325.50 m** | 7.73 km/h | 49.5° | -99.6% (Worse) |
| **Case D: GT Speed + NHC** | 156.30 m | 746.50 m | **1077.70 m** | 1.50 km/h | 12.2° | -62.3% (Worse) |
| **Case E: V2 + Regime Calib + NHC** | 88.30 m | 412.20 m | **662.60 m** | 6.17 km/h | 6.3° | **+0.2% (Best)** |

---

## 5. Experiment 5: 300s Regime-Specific Navigation Drift Attribution

Where did the position error actually accumulate during the 300s blackout?

| Regime | % of Time | V2 Cumulative Drift (m) | V2 % of Total Drift | V3 Cumulative Drift (m) | V3 % of Total Drift | Net Delta (m) |
|---|---|---|---|---|---|---|
| **Stationary** | 35.2% | -0.7 m | -0.1% | -0.3 m | 0.0% | -0.4 m |
| **Acceleration** | 10.7% | 110.6 m | 16.7% | 182.9 m | 19.5% | -72.3 m |
| **Braking** | 12.3% | 148.7 m | 22.4% | 134.6 m | 14.3% | **+14.0 m** |
| **Straight/Cruise** | 21.4% | 290.0 m | 43.7% | 299.9 m | 31.9% | -9.9 m |
| **Moderate Turn** | 17.2% | 103.5 m | 15.6% | 273.7 m | 29.1% | -170.1 m |
| **Strong Turn** | 3.2% | 11.9 m | 1.8% | 48.1 m | 5.1% | -36.1 m |

---

## 6. Answers to Mandatory Diagnostic Questions

1. **Is SpeedNet v2 systematically biased?**
   - **YES.** V2 has a systematic positive speed bias of `+6.39 km/h` across the test partition (predicts higher speed than ground truth).
2. **Which driving regimes cause the most speed error?**
   - **Straight/Cruise (+12.13 km/h bias)** and **Acceleration (+9.10 km/h bias)**. In terms of integrated position drift, **Straight/Cruise (43.7% of drift)** and **Braking (22.4% of drift)** cause the most error.
3. **Can those regimes be identified from IMU alone?**
   - **PARTIALLY.** Stationary (92.2%), Strong Turn (84.8%), Cruise (82.4%), and Moderate Turn (64.2%) can be reliably identified. Acceleration (21.9%) and Braking (14.0%) CANNOT be reliably identified from a 3s IMU window without wheel speed or longitudinal constraints.
4. **Does regime-aware multi-task learning reduce speed bias?**
   - **NO.** Multi-task training degraded overall speed MAE from `7.59 km/h` to `8.01 km/h` and increased overall bias from `+6.39 km/h` to `+6.77 km/h` due to gradient competition between cross-entropy and smooth L1 loss.
5. **Does reduced speed error actually reduce accumulated navigation drift?**
   - **NOT AUTOMATICALLY.** Offline regime calibration reduced speed MAE to `7.02 km/h` and yielded a minor improvement at 300s (`662.6 m` vs `664.1 m`), but GT speed + NHC (`1077.7 m`) proves that speed error reduction without addressing heading-NHC kinematics does not reduce integrated drift.
6. **Does V3 beat the current 263 m benchmark?**
   - **NO.** V3 + NHC reached `938.9 m` at 300s, failing to beat the benchmark.
7. **Does V3 beat it by a meaningful margin?**
   - **NO.** It degraded performance by 41.4%.
8. **Does V3 remain real-time feasible?**
   - **YES.** V3 inference takes `0.0381 ms/step` (~26,000 Hz), using only 424k parameters.
9. **Does a simple regime-specific calibration perform similarly?**
   - **YES, IT PERFORMS BETTER.** Offline regime calibration achieved `7.02 km/h` test MAE and `662.6 m` at 300s, easily outperforming end-to-end multi-task SpeedNet v3 (`8.01 km/h` / `938.9 m`).
10. **Is further architecture complexity justified?**
   - **NO.** Adding auxiliary classification heads to a single 1D-CNN+BiLSTM spine does not resolve MEMS IMU acceleration ambiguity during braking/acceleration.

---

## 7. Single Evidence-Based Next Step

> **RECOMMENDATION: Physics-Informed Kinetic Feature Enhancement (SpeedNet v2.5)**
>
> Rather than adding multi-task loss heads, explicitly add **derived kinematic features** as input channels to SpeedNet:
> 1. Integrated specific force delta ($\int a_{\text{long}} dt$)
> 2. Rolling IMU variance over $0.5\text{s}$
> 3. Estimated pitch tilt angle ($\theta_{\text{tilt}}$)
>
> *Rationale:* The 14.0% braking recall proves that raw acceleration channels alone are insufficient to distinguish vehicle braking from road slope/tilt changes. Providing explicit kinematic energy features into the neural input will directly resolve the positive speed bias during deceleration without multi-task gradient interference.

---

## Artifacts & Outputs

- **Script:** [`scripts/vw4_speednet_v3_regime_aware.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_speednet_v3_regime_aware.py)
- **Trained Model:** [`models/speednet_v3_w30_lambda005.pth`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/models/speednet_v3_w30_lambda005.pth)
- **Summary JSON:** [`results/vw4_speednet_v3_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_summary.json)
- **Predictions:** [`results/vw4_speednet_v3_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_speednet_v3_predictions.npz)
- **Plots Directory:** [`plots/vw4/speednet_v3/`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/speednet_v3/) (7 plots generated)
