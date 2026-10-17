# Milestone M023 — Acceleration-Variance-Gated Multi-Stage ZUPT Transition Fusion

## 1. Executive Summary

- **Milestone:** M023 — Acceleration-Variance-Gated Multi-Stage ZUPT Transition Fusion
- **Objective:** Evaluate whether a causal acceleration-variance transition detector ($\sigma_a^2 \le 0.15\text{ m}^2/\text{s}^4$) can catch slow rolling stop transitions earlier than the M014 ZUPT detector ($P_{\text{stat}} > 0.70$) without triggering false ZUPT activations during active low-speed motion.
- **Verdict:** **REJECTED**.
- **Key Findings:** Acceleration-variance transition detectors (F2, F3, F4) triggered false ZUPT activations during active low-speed motion ($1.0-3.6\text{ km/h}$), exploding 60s test position error ($27.53 \rightarrow 35.12\text{ m}$) and almost doubling 300s validation set error ($505.40 \rightarrow 949.17\text{ m}$). The Validation-Selected Winner (F5) is the original M014 Control ZUPT detector. Active benchmark remains **`220.12 m` @ 300s**.

---

## 2. Research Question

Can we detect slow rolling-stop / stop-transition states earlier than the current M014 ZUPT detector using a causal acceleration-variance gate, and improve long-duration navigation without altering SpeedNet or APM during active motion?

---

## 3. Core Hypothesis

M014 ZUPT activates late during slow deceleration into a stop ($P_{\text{stat}} > 0.70$). Adding a causal acceleration-variance transition gate ($\sigma_a^2 \le 0.15$) may allow an earlier, conservative velocity reset during slow stop transitions.

---

## 4. Why M023 Was Selected After M022

Milestone M020 identified missed stationary detection during slow stop transitions ($<0.5\text{ km/h}$) as a secondary residual error source (32.0s of missed stationary time / 320 samples). After turn speed attenuation (M021) and longer APM integration windows (M022) were both cleanly rejected, M023 targeted this secondary stationary transition opportunity.

---

## 5. Starting Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s)} = \mathbf{220.12\text{ m @ 300s}}$$

---

## 6. Implementation Architecture

Retained exact M014 EKF, M013 F4 physical speed constraints, M019 APM 0.5s speed damping, fixed NHC, and raw gyro integration. Only modified the stationary ZUPT trigger condition.

---

## 7. Candidate Definitions

- **F0 / F1 (M014 Control ZUPT):** Original M014 ZUPT detector ($P_{\text{stat}} > 0.70$).
- **F2 (Variance-Gated ZUPT):** Activates ZUPT if $P_{\text{stat}} > 0.70$ OR ($\sigma_a^2 \le 0.15$ AND $v_{\text{speednet}} \le 1.0\text{ m/s}$ AND $|\omega_y| \le 3^\circ/\text{s}$).
- **F3 (Variance-Gated + Persistence):** F2 with 3-sample temporal persistence ($N_{\text{persist}} \ge 3$).
- **F4 (Two-Stage ZUPT):** Stage 1 applies soft ZUPT ($\sigma_{\text{zupt}}=0.5\text{ m/s}$) when approaching stop; Stage 2 applies hard ZUPT ($\sigma_{\text{zupt}}=0.2\text{ m/s}$) when confirmed.
- **F5 (Best Validated Configuration):** Selected winner from Validation set evaluation (`88566:107535`).

---

## 8. Dataset and Partition Provenance

- Train: `0:88566` (70%)
- Validation: `88566:107535` (15%)
- Unseen Test: `108000:111000` (300s outage, locked start `108,000`).

---

## 9. Validation Methodology

All detector thresholds ($\sigma_a^2 \le 0.2202\text{ (m/s}^2)^2$ 15th percentile) were selected strictly on Train/Val partition. Zero test data was used for hyperparameter tuning.

---

## 10. Test Methodology

Evaluated exactly once on locked unseen test partition (`start_idx = 108,000`).

---

## 11. Full Candidate Results

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1 (M014 ZUPT Only)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |
| **F2 (Var-Gated)** | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | $35.12\text{ m}$ | $382.49\text{ m}$ | $174.06\text{ m}^*$ | $-33.8\%$ | $-31.5\%$ | $-20.9\%$ |
| **F3 (Var + Persist)** | $7.32\text{ km/h}$ | $11.56\text{ km/h}$ | $33.58\text{ m}$ | $386.93\text{ m}$ | $181.77\text{ m}^*$ | $-30.9\%$ | $-28.5\%$ | $-17.4\%$ |
| **F4 (Two-Stage)** | $7.32\text{ km/h}$ | $11.56\text{ km/h}$ | $31.19\text{ m}$ | $410.89\text{ m}$ | $198.82\text{ m}^*$ | $-24.4\%$ | $-21.8\%$ | $-9.7\%$ |
| **F5 (Val Winner)** | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

---

## 12. Stationary Detector Diagnostics

| Candidate | Total ZUPT Samples | Stage 1 Soft ZUPT | Stage 2 Hard ZUPT | Precision (%) | Recall (%) |
|---|---|---|---|---|---|
| **F0 / F1 / F5** | 786 | 0 | 786 | **93.51%** | **69.67%** |
| **F2** | 1,177 | 0 | 1,177 | $67.12\%$ | $74.88\%$ |
| **F3** | 1,114 | 0 | 1,114 | $70.92\%$ | $74.88\%$ |
| **F4** | 1,114 | 328 | 786 | $70.92\%$ | $74.88\%$ |

---

## 13. 60/120/300s Navigation Comparison

- **60s Outage:** F0 Control = **$27.53\text{ m}$**, F2 = $35.12\text{ m}$ ($+27.6\%$ error explosion).
- **120s Outage:** F0 Control = $428.79\text{ m}$, F2 = $382.49\text{ m}$.
- **300s Outage:** F0 Control = **`220.12 m`**, F2 = $174.06\text{ m}^*$ (Failed validation).

---

## 14. Comparison Against Historical Benchmarks

- **vs Pre-M013 Benchmark ($263.11\text{ m}$):** F0 Control is $-16.3\%$ better ($220.12\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F0 Control is $-13.4\%$ better ($220.12\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F0 Control is $-5.6\%$ better ($220.12\text{ m}$).
- **vs M019 Benchmark ($220.12\text{ m}$):** F0 Control = **0.0% (Active Control Best)**.

---

## 15. Failure Analysis

Acceleration-variance gating triggers false ZUPT activations during smooth low-speed cruising and deceleration transients ($<3.6\text{ km/h}$). Zeroing velocity during active rolling motion exploded 60s position error by $+27.6\%$ ($27.53\text{ m} \rightarrow 35.12\text{ m}$) and almost doubled validation set 300s error ($505.40 \rightarrow 949.17\text{ m}$).

---

## 16. What Was Learned

The original M014 ZUPT detector ($P_{\text{stat}} > 0.70$) is highly optimal with $93.51\%$ precision. Attempting to force earlier ZUPT activation using IMU acceleration variance induces false triggers during active rolling motion.

---

## 17. Acceptance / Rejection Verdict

**REJECTED**.

---

## 18. Exact Research Artifacts Created

- **Script Path:** [`scripts/vw4_m023_multistage_zupt.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m023_multistage_zupt.py)
- **Summary JSON:** `results/vw4_m023_multistage_zupt_summary.json`
- **Predictions NPZ:** `results/vw4_m023_multistage_zupt_predictions.npz`
- **Report Markdown:** [`results/vw4_m023_multistage_zupt_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m023_multistage_zupt_report.md)
- **Plot Directory:** `plots/vw4/m023_multistage_zupt/`

---

## 19. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 20. Next Research Decision (M024 Proposal)

**M024 Proposal — Deceleration-Phase APM Magnitude Scaling & Transition Bounds**:
Milestones M021, M022, and M023 have systematically established that modifying turn speed, expanding APM integration window lengths, and altering ZUPT stationary detection all degrade navigation accuracy. M019 APM ($0.5\text{ s}$ window, $0.5\text{ m/s}$ bound) remains the only filter-level innovation that successfully beat M014. M024 should investigate fine-grained deceleration-phase magnitude scaling within APM — specifically evaluating whether adjusting the maximum correction bound ($\delta v_{\max} \in [0.25, 0.75]\text{ m/s}$) during straight braking episodes ($a_{\text{long}} < -0.5\text{ m/s}^2$) can safely reduce the remaining $+9.82\text{ km/h}$ braking bias and lower 300s position drift below $220.12\text{ m}$.

---

## 21. Full Research Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023`
