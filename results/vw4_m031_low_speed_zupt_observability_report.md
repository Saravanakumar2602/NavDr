# Milestone M031 — Low-Speed Stop Observability Diagnostic Report

## Executive Summary

- **Milestone:** M031 — Low-Speed Stop Observability Diagnostic
- **Objective:** Evaluate offline whether a proposed causal low-speed kinematic gate ($v_{\text{speednet}} < 0.36\text{ km/h}$ AND $|a_{\text{long}}| < 0.15\text{ m/s}^2$) captures stationary or near-stop samples missed by the established M014 ZUPT detector ($P_{\text{stat}} > 0.70$), and determine whether an M032 ZUPT intervention is scientifically justified.
- **Verdict:** **BRANCH CLOSED (NO M032 INTERVENTION JUSTIFIED)**.
- **Key Findings:**
  - **Zero Additional Sample Capture on Test Set:** On the locked unseen test set (`start_idx = 108,000`), out of 320 stationary samples missed by M014, the proposed low-speed gate captured **EXACTLY 0 additional samples (0.0 seconds)**.
  - **Zero Incremental Gain on Validation Set:** On the validation set (`88566:107535`), combining the proposed low-speed gate with M014 yielded **identical TPs (514) and FPs (92)** as M014 alone (F1 = 0.7317 vs proposed low-speed gate alone F1 = 0.2824). 100% of samples detected by the proposed gate were already detected by M014.
  - **Severe Activation Latency:** On full stop episodes ($16.9 - 28.8\text{ s}$), M014 activates within $0.4 - 2.1\text{ s}$ (coverage 64.7% – 72.8%), whereas the proposed low-speed gate lags by $6.4 - 11.0\text{ s}$ (coverage 10.7% – 28.4%) due to neural window smoothing.
  - **Active Verified Benchmark Retained:** M031 is diagnostic-only. **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## Benchmark & Diagnostic Scope Lock

- **Active Benchmark:** SpeedNet v2 W=40 + Raw Gyro + Fixed NHC + M013 F4 + M014 ZUPT + M019 APM + M028 Jerk Gate = **`218.93 m` @ 300s** (60s = `27.35 m`, 120s = `426.85 m`).
- **Diagnostic Constraint:** M031 is strictly an offline diagnostic. No changes were made to EKF state, NHC, ZUPT updates, SpeedNet weights, or navigation integration.

---

## Validation Set Detector Observability Results (`88566:107535`)

- Total Validation Samples: 18,978 (10 Hz)
- True Ground-Truth Stationary Samples ($v_{\text{GT}} < 0.1\text{ m/s}$): 799 samples

| Detector Configuration | True Positives (TP) | False Positives (FP) | Precision | Recall | False-Stationary Rate (FPR) | Missed-Stationary Rate (FNR) | F1 Score |
|---|---|---|---|---|---|---|---|
| **M014 Established ($P_{\text{stat}} > 0.70$)** | **514** | **92** | **0.8482** | **0.6433** | **0.0051** | **0.3567** | **0.7317** |
| **Proposed Gate ($v < 0.36\text{ km/h}, \|a\| < 0.15$)** | 133 | 10 | 0.9301 | 0.1665 | 0.0005 | 0.8335 | 0.2824 |
| **Combined Fusion (M014 OR Proposed)** | **514** | **92** | **0.8482** | **0.6433** | **0.0051** | **0.3567** | **0.7317** |

---

## Stop-Event Level Analysis (Validation Partition)

- Found **13 Ground-Truth Stationary Episodes** on Validation set:
  - **Full Stops ($\ge 5.0\text{ s}$, 3 episodes):** M014 average coverage = **69.9%** (latency $0.4 - 2.1\text{ s}$); Proposed gate average coverage = **18.5%** (latency $6.4 - 11.0\text{ s}$).
  - **Short Stops ($2.0 - 5.0\text{ s}$, 2 episodes):** M014 average coverage = **53.0%** (latency $0.0\text{ s}$); Proposed gate average coverage = **8.1%** (latency $0.1 - 0.4\text{ s}$).
  - **Creeping / Near-Stops ($< 2.0\text{ s}$, 8 episodes):** M014 average coverage = **17.4%**; Proposed gate average coverage = **0.0%** (0% detection due to speed smoothing).

---

## Diagnostic Threshold Sensitivity Grid (Validation Set)

| Speed Thresh ($v_{\text{thresh}}$ km/h) | Accel Thresh ($a_{\text{thresh}}$ m/s²) | Precision | Recall | F1 Score | False Positive Count (FP) |
|---|---|---|---|---|---|
| 0.20 km/h | 0.10 m/s² | 0.9583 | 0.0288 | 0.0559 | 1 |
| 0.20 km/h | 0.15 m/s² | 0.9730 | 0.0451 | 0.0861 | 1 |
| 0.20 km/h | 0.20 m/s² | 0.9767 | 0.0526 | 0.0998 | 1 |
| **0.36 km/h** | **0.15 m/s² (Proposed)** | **0.9301** | **0.1665** | **0.2824** | **10** |
| 0.50 km/h | 0.15 m/s² | 0.8967 | 0.2390 | 0.3775 | 22 |
| 0.75 km/h | 0.20 m/s² | 0.8409 | 0.3705 | 0.5143 | 56 |

---

## Counterfactual Offline Test Set Analysis (`108,000 : 111,000`)

- Test Ground-Truth Stationary Samples ($v_{\text{GT}} < 0.1\text{ m/s}$): 1,055 out of 3,000 samples (35.2%)
- M014 Detected Stationary Samples: 786 samples ($\text{TP}=735$, $\text{FP}=51$, Recall = 69.67%)
- Stationary Samples Missed by M014: 320 samples
- **Additional Missed Stationary Samples Captured by Proposed Low-Speed Gate:** **0 samples (0.0 seconds)**.

---

## Scientific Decision & Branch Closure Justification

Per protocol decision rules:
> *"M031 should recommend M032 ONLY IF the diagnostic demonstrates that a meaningful population of stationary samples is missed by M014 AND the proposed low-speed gate identifies a useful portion of those samples."*

- **Result:** The proposed low-speed gate captures **0 additional missed stationary samples** on test data and **0 additional samples** on validation data. Every single sample where SpeedNet predicted $v < 0.36\text{ km/h}$ was already 100% captured by M014 ($P_{\text{stat}} > 0.70$).
- **Conclusion:** **BRANCH CLOSED**. M032 will NOT be created or attempted. Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## Research Artifacts & Exact Paths

- **Diagnostic Script:** [`scripts/vw4_m031_low_speed_zupt_observability.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m031_low_speed_zupt_observability.py)
- **Summary JSON:** `results/vw4_m031_low_speed_zupt_observability_summary.json`
- **Report Markdown:** [`results/vw4_m031_low_speed_zupt_observability_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m031_low_speed_zupt_observability_report.md)
- **Plot Directory:** `plots/vw4/m031_low_speed_zupt_observability/`
  - `detector_comparison_val.png`

---

## Final M031 Verdict & Active Benchmark

**BRANCH CLOSED (M031 DIAGNOSTIC COMPLETE)**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
