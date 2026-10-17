# Milestone M030 — Causal Jerk-Deceleration Product Gating for Dynamic APM Activation Report

## Executive Summary

- **Milestone:** M030 — Causal Jerk-Deceleration Product Gating for Dynamic APM Activation
- **Objective:** Evaluate whether combining longitudinal acceleration and jerk into a joint product gate ($\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}} > \text{threshold}$) makes APM speed damping more selective and improves 300s dead-reckoning position drift below $218.93\text{ m}$.
- **Verdict:** **REJECTED (UNNECESSARY COMPLEXITY)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Validation Performance:** All product threshold candidates ($0.50 - 1.50\text{ m}^2/\text{s}^5$) yielded identical 300s validation error ($494.83\text{ m}$) as F0 Control, while candidate F5 ($2.00\text{ m}^2/\text{s}^5$) reached $494.73\text{ m}$ ($\Delta = 0.10\text{ m}$, practically tied). Per protocol safety rules, F0 Control was selected as the validation winner.
  - **Locked Test Evaluation:** Evaluated on the locked unseen test set (`start_idx = 108,000`), all product gate candidates F1 through F5 achieved **EXACTLY `218.93 m` @ 300s** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s), matching the M028 control ($+0.00\text{ m}$ change).
  - **Failure / Redundancy Mechanism:** When the M028 jerk condition ($j_{\text{long}} < -1.00\text{ m/s}^3$) and deceleration condition ($a_{\text{long}} < -0.50\text{ m/s}^2$) are already active, their product $\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}}$ naturally exceeds $0.50\text{ m}^2/\text{s}^5$. The product gate is physically redundant and adds unneeded complexity.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## M028 Control Reproduction Verification

- **Target Benchmark (M028 / M029 Active Best):**
  - 60s Outage: `27.35 m`
  - 120s Outage: `426.85 m`
  - 300s Outage: `218.93 m`
- **Measured F0 Control:**
  - 60s Outage: `27.35 m`
  - 120s Outage: `426.85 m`
  - 300s Outage: `218.93 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Validation Jerk-Deceleration Product Evaluation (`88566:107535`)

| Candidate ID | Product Threshold ($\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}}$) | Val 300s Position Error (m) | Val Mean Error (m) | Selection Status |
|---|---|---|---|---|
| **F0 Control** | **No Product Gate (M028 Jerk Gate Only)** | **494.83 m** | **356.99 m** | **SELECTED VALIDATION WINNER** |
| **F1** | $\mathcal{J}_{\text{prod}} > 0.50\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F2** | $\mathcal{J}_{\text{prod}} > 0.75\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F3** | $\mathcal{J}_{\text{prod}} > 1.00\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F4** | $\mathcal{J}_{\text{prod}} > 1.50\text{ m}^2/\text{s}^5$ | $494.83\text{ m}$ | $356.99\text{ m}$ | Tied with Control |
| **F5** | $\mathcal{J}_{\text{prod}} > 2.00\text{ m}^2/\text{s}^5$ | $494.73\text{ m}$ | $356.96\text{ m}$ | Practically Tied ($\Delta=0.10\text{ m}$) |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 220.12m M019 | vs 218.93m M028 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M028)** | M028 Baseline Control | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **CONTROL** |
| **F1** | $\mathcal{J}_{\text{prod}} > 0.50\text{ m}^2/\text{s}^5$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F2** | $\mathcal{J}_{\text{prod}} > 0.75\text{ m}^2/\text{s}^5$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F3** | $\mathcal{J}_{\text{prod}} > 1.00\text{ m}^2/\text{s}^5$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F4** | $\mathcal{J}_{\text{prod}} > 1.50\text{ m}^2/\text{s}^5$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F5** | $\mathcal{J}_{\text{prod}} > 2.00\text{ m}^2/\text{s}^5$ | $7.33\text{ km/h}$ | $11.57\text{ km/h}$ | $27.35\text{ m}$ | $426.85\text{ m}$ | $218.93\text{ m}$ | $-16.8\%$ | $-0.5\%$ | $+0.0\%$ |
| **F6 (Val Winner)** | Selected Best Validation (F0) | **7.33 km/h** | **11.57 km/h** | **27.35 m** | **426.85 m** | **218.93 m** | **-16.8%** | **-0.5%** | **0.0%** |

---

## APM Activation & Product Suppression Diagnostics

| Candidate | Total IMU Decel Events | APM Updates | Suppressed Updates | Suppression Rate (%) | Mean APM Speed Correction |
|---|---|---|---|---|---|
| **F0 Control (No Product Gate)** | 118 | 76 | 42 | **35.6%** | $1.76\text{ km/h}$ |
| **F1 ($\mathcal{J}_{\text{prod}} > 0.50$)** | 118 | 76 | 42 | $35.6\%$ | $1.76\text{ km/h}$ |
| **F2 ($\mathcal{J}_{\text{prod}} > 0.75$)** | 118 | 74 | 44 | $37.3\%$ | $1.76\text{ km/h}$ |
| **F3 ($\mathcal{J}_{\text{prod}} > 1.00$)** | 118 | 73 | 45 | $38.1\%$ | $1.76\text{ km/h}$ |
| **F4 ($\mathcal{J}_{\text{prod}} > 1.50$)** | 118 | 68 | 50 | $42.4\%$ | $1.76\text{ km/h}$ |
| **F5 ($\mathcal{J}_{\text{prod}} > 2.00$)** | 118 | 67 | 51 | $43.2\%$ | $1.76\text{ km/h}$ |

---

## Trajectory-Level & Along/Cross-Track Diagnostics

| Candidate | Mean Position Error (m) | Final Position Error (m) | Final Along-Track Error (m) | Final Cross-Track Error (m) |
|---|---|---|---|---|
| **F0 Control (M028)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |
| **F6 (Val Winner F0)** | **307.72 m** | **218.93 m** | **-180.25 m** | **124.16 m** |

---

## Scientific Rejection Reason

M030 REJECTED — active benchmark remains 218.93 m @ 300s.
Adding an explicit product threshold $\mathcal{J}_{\text{prod}} = a_{\text{long}} \cdot j_{\text{long}}$ on top of M028 is physically redundant, yielding zero validation or test position error improvement ($0.0\%$ change). F0 Control is retained for simplicity and model parsimony.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m030_jerk_deceleration_product_gate.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m030_jerk_deceleration_product_gate.py)
- **Summary JSON:** `results/vw4_m030_jerk_deceleration_product_gate_summary.json`
- **Predictions NPZ:** `results/vw4_m030_jerk_deceleration_product_gate_predictions.npz`
- **Report Markdown:** [`results/vw4_m030_jerk_deceleration_product_gate_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m030_jerk_deceleration_product_gate_report.md)
- **Plot Directory:** `plots/vw4/m030_jerk_deceleration_product_gate/`

---

## Final M030 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
