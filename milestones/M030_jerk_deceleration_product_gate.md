# Milestone M030 — Causal Jerk-Deceleration Product Gating for Dynamic APM Activation

## 1. Executive Summary

- **Milestone:** M030 — Causal Jerk-Deceleration Product Gating for Dynamic APM Activation
- **Objective:** Evaluate whether combining longitudinal acceleration and jerk into a joint product gate ($\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}} > \text{threshold}$) makes APM speed damping more selective and improves 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:** M030 REJECTED — active benchmark remains 218.93 m @ 300s. All product threshold candidates ($0.50 - 2.00\text{ m}^2/\text{s}^5$) yielded identical test position error to F0 Control (**`218.93 m` @ 300s**, $27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s). The product gate is physically redundant on top of M028 jerk gating and adds unnecessary complexity.

---

## 2. Objective & Research Question

Test whether APM activation can be made more selective by requiring both strong longitudinal deceleration ($a_{\text{long}} < -0.50\text{ m/s}^2$) AND strong negative longitudinal jerk ($j_{\text{long}} < -1.00\text{ m/s}^3$) via a joint product threshold $\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}} > \text{threshold}$.

---

## 3. Locked M028 / M029 Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 4. Exact Mathematical Definition of Product Gate

$$\mathcal{J}_{\text{prod}}[k] = a_{\text{long}}[k] \cdot j_{\text{long}}[k]$$
where $a_{\text{long}}[k] = -(raw\_ay[k] - grav\_y[k])$ and $j_{\text{long}}[k] = \frac{a_{\text{long}}[k] - a_{\text{long}}[k-1]}{\Delta t}$. Units: $(\text{m/s}^2)(\text{m/s}^3) = \text{m}^2/\text{s}^5$.

---

## 5. Candidate Thresholds

- **F0 (Control M028):** M028 Jerk gate only ($j_{\text{long}} < -1.00\text{ m/s}^3$).
- **F1:** $j_{\text{long}} < -1.00\text{ m/s}^3$ AND $\mathcal{J}_{\text{prod}} > 0.50\text{ m}^2/\text{s}^5$.
- **F2:** $j_{\text{long}} < -1.00\text{ m/s}^3$ AND $\mathcal{J}_{\text{prod}} > 0.75\text{ m}^2/\text{s}^5$.
- **F3:** $j_{\text{long}} < -1.00\text{ m/s}^3$ AND $\mathcal{J}_{\text{prod}} > 1.00\text{ m}^2/\text{s}^5$.
- **F4:** $j_{\text{long}} < -1.00\text{ m/s}^3$ AND $\mathcal{J}_{\text{prod}} > 1.50\text{ m}^2/\text{s}^5$.
- **F5:** $j_{\text{long}} < -1.00\text{ m/s}^3$ AND $\mathcal{J}_{\text{prod}} > 2.00\text{ m}^2/\text{s}^5$.
- **F6 (Val Winner):** Selected winner on Validation set (`88566:107535`).

---

## 6. Causal / Leakage Audit

Calculated using strictly current sample $k$ and past sample $k-1$. Zero future leakage. Validation selection performed strictly on Validation partition (`88566:107535`).

---

## 7. Validation Methodology & 8. Validation Table

Selected strictly on Validation partition (`88566:107535`). F0 Control selected as simpler winner per protocol safety rules.

| Candidate ID | Product Threshold ($\mathcal{J}_{\text{prod}}$) | Val 300s Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 Control** | **No Product Gate (M028 Jerk Gate Only)** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $\mathcal{J}_{\text{prod}} > 0.50\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F2** | $\mathcal{J}_{\text{prod}} > 0.75\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F3** | $\mathcal{J}_{\text{prod}} > 1.00\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F4** | $\mathcal{J}_{\text{prod}} > 1.50\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F5** | $\mathcal{J}_{\text{prod}} > 2.00\text{ m}^2/\text{s}^5$ | $494.73\text{ m}$ | $356.96\text{ m}$ | Practically Tied ($\Delta=0.10\text{ m}$) |

---

## 9. Locked-Test Table

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F2** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F3** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F4** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F5** | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F6 (Val Winner)** | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **0.0%** |

---

## 10. APM Activation Statistics & 11. Trajectory Statistics

- **Total IMU Deceleration Events:** 118
- **F0 Control Updates:** 76 (42 suppressed, 35.6% suppression rate)
- **Mean Position Error:** $307.72\text{ m}$
- **Final Along-Track Error:** $-180.25\text{ m}$
- **Final Cross-Track Error:** $124.16\text{ m}$

---

## 12. Benchmark Comparisons

- Historical 263.11 m Benchmark: **-16.8%** ($263.11 \rightarrow 218.93\text{ m}$)
- M019 APM 220.12 m Baseline: **-0.5%** ($220.12 \rightarrow 218.93\text{ m}$)
- M028 Jerk Gate Active Benchmark: **0.0%** (Identical)

---

## 13. Scientific Interpretation & 14. Failure Mechanism

When $j_{\text{long}} < -1.00\text{ m/s}^3$ is satisfied during genuine IMU deceleration events ($a_{\text{long}} < -0.50\text{ m/s}^2$), the product $\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}}$ naturally exceeds $0.50\text{ m}^2/\text{s}^5$. Adding an explicit product threshold on top of M028 is physically redundant and provides zero additional selectivity.

---

## 15. Final Verdict

**REJECTED**.
M030 REJECTED — active benchmark remains 218.93 m @ 300s.

---

## 16. Recommended Next Experiment (M031 Proposal)

**M031 Proposal — Low-Speed Kinematic ZUPT Gating for Precision Rolling-Stop Recovery**:
With speed damping optimization (M019, M028) fully resolved and confirmed, M031 should investigate a low-speed kinematic ZUPT activation gate ($v_{\text{speednet}} < 0.36\text{ km/h}$ AND $|a_{\text{long}}| < 0.15\text{ m/s}^2$). Rather than relying solely on neural static probability ($\text{prob}_{\text{stat}} > 0.70$), M031 aims to capture creeping rolling stops zero-latency, resetting residual velocity drift during urban traffic lights and driving 300s position error below $218.93\text{ m}$.

---

## 17. Full M001 → M030 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030`
