# Milestone M029 — Jerk-Gate Robustness and Local Threshold Ablation

## 1. Executive Summary

- **Milestone:** M029 — Jerk-Gate Robustness and Local Threshold Ablation
- **Objective:** Evaluate local threshold sensitivity around the M028 causal jerk gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) across $[-1.25, -0.75]\text{ m/s}^3$ to determine whether M028 represents a smooth, physically robust operating plateau or a brittle local optimum.
- **Verdict:** **ROBUSTNESS CONFIRMED**.
- **Key Findings:** Across the entire local threshold neighborhood $[-1.25, -0.90]\text{ m/s}^3$, validation 300s position error remains flat at **$494.83\text{ m}$**. On locked test data, position drift is **exactly `218.93 m`** across $[-1.00, -0.75]\text{ m/s}^3$ and varies by less than 6 cm across $[-1.25, -1.10]\text{ m/s}^3$ ($218.87\text{ m}$). Proves M028 is an exceptionally smooth, stable operating plateau. Active benchmark remains **`218.93 m` @ 300s**.

---

## 2. Research Question

Is the M028 position error reduction robust around the selected jerk threshold ($j_{\text{long}} < -1.00\text{ m/s}^3$), or is $-1.00\text{ m/s}^3$ a noisy local optimum?

---

## 3. Core Hypothesis

If causal jerk gating reflects physical brake onset rather than noise overfitting, nearby thresholds in the local neighborhood $[-1.25, -0.75]\text{ m/s}^3$ should produce consistent, stable navigation performance without performance cliffs.

---

## 4. Why M029 Follows M028

Milestone M028 achieved a new verified benchmark of **`218.93 m` @ 300s** by adding causal jerk gating ($j_{\text{long}} < -1.00\text{ m/s}^3$). M029 performs a necessary local robustness audit around $-1.00\text{ m/s}^3$ to verify operating stability before introducing further architectural changes.

---

## 5. M028 Baseline Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 6. Candidate Thresholds

- **F0 (Control M028):** $j_{\text{long}} < -1.00\text{ m/s}^3$.
- **F1:** $j_{\text{long}} < -0.75\text{ m/s}^3$.
- **F2:** $j_{\text{long}} < -0.90\text{ m/s}^3$.
- **F3:** $j_{\text{long}} < -1.10\text{ m/s}^3$.
- **F4:** $j_{\text{long}} < -1.25\text{ m/s}^3$.
- **F5 (Val Winner):** Selected winner on Validation set (`88566:107535`).

---

## 7. Validation Methodology & 8. Validation Results

Thresholds selected strictly on Validation partition (`88566:107535`). Candidate F2 ($j_{\text{long}} < -0.90\text{ m/s}^3$) tied with F0 Control at **$494.83\text{ m}$**.

| Candidate ID | Jerk Threshold ($j_{\text{long}}$) | Val 300s Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F2 / F5** | **$j_{\text{long}} < -0.90\text{ m/s}^3$** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION BEST (TIED)** |
| **F0 Control** | $j_{\text{long}} < -1.00\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Baseline |
| **F3** | $j_{\text{long}} < -1.10\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Candidate |
| **F4** | $j_{\text{long}} < -1.25\text{ m/s}^3$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Robust Candidate |
| **F1** | $j_{\text{long}} < -0.75\text{ m/s}^3$ | $495.52\text{ m}$ | $357.13\text{ m}$ | Robust Candidate |

---

## 9. Validation Winner

Candidate F2 / F5 ($j_{\text{long}} < -0.90\text{ m/s}^3$).

---

## 10. Locked-Test Results

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control -1.00)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F2 (Val Winner)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **+0.0%** |
| **F3** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-0.6\%$ | $-0.0\%$ |
| **F4** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.32\text{ m}$ | $426.77\text{ m}$ | $218.87\text{ m}$ | $-16.8\%$ | $-0.6\%$ | $-0.0\%$ |
| **F5 (Val Winner)** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **+0.0%** |

---

## 11. Threshold Sensitivity & 12. APM Activation Sensitivity

- Across $[-1.00, -0.75]\text{ m/s}^3$, APM activations vary smoothly from 76 to 78 updates (33.9% – 35.6% suppression rate), maintaining an identical 300s test error of **`218.93 m`**.
- Across $[-1.25, -1.10]\text{ m/s}^3$, APM activations vary from 71 to 73 updates (38.1% – 39.8% suppression rate), maintaining test error within 6 cm (**`218.87 m`**).

---

## 13. Trajectory Analysis & 14. Along/Cross-Track Analysis

- **Mean Position Error:** F0 = $307.72\text{ m}$, F2 = $307.72\text{ m}$, F4 = $307.69\text{ m}$.
- **Final Along-Track Error:** F0 = $-180.25\text{ m}$, F2 = $-180.25\text{ m}$, F4 = $-180.19\text{ m}$.
- **Final Cross-Track Error:** F0 = $124.16\text{ m}$, F2 = $124.16\text{ m}$, F4 = $124.15\text{ m}$.

---

## 15. Causality Audit & 16. Leakage Audit

Uses strictly current sample $k$ and past sample $k-1$. Zero future leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 17. Robustness Conclusion & 18. Acceptance / Rejection

**ROBUSTNESS CONFIRMED**.

Rather than inventing a trivial sub-centimeter benchmark modification based on noise, M029 confirms that $j_{\text{long}} \approx -1.00\text{ m/s}^3$ represents a smooth, stable, physically robust operating plateau. The active benchmark remains **`218.93 m` @ 300s**.

---

## 19. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$

---

## 20. Next Research Decision (M030 Proposal)

**M030 Proposal — Causal Jerk-Deceleration Product Gating for Dynamic APM Activation**:
Having confirmed in M029 that jerk gating is physically robust around $j_{\text{long}} < -1.00\text{ m/s}^3$, M030 should evaluate whether a joint Jerk-Deceleration Product Gate ($\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}} > 0.75\text{ (m/s}^2)(\text{m/s}^3)$) can detect high-power braking initiation (where both acceleration magnitude AND jerk magnitude are simultaneously large), selectively trimming braking overestimation without suppressing mild rolling deceleration, driving 300s position drift below $218.93\text{ m}$.

---

## 21. Full M001 → M029 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029`
