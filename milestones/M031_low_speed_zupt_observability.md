# Milestone M031 — Low-Speed Stop Observability Diagnostic

## 1. Objective

Evaluate offline whether a proposed causal low-speed kinematic gate ($v_{\text{speednet}} < 0.36\text{ km/h}$ AND $|a_{\text{long}}| < 0.15\text{ m/s}^2$) captures stationary or near-stop samples missed by the established M014 ZUPT detector ($P_{\text{stat}} > 0.70$), and determine whether an M032 ZUPT intervention is scientifically justified.

---

## 2. Locked Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 3. Why This Is Diagnostic-Only

M031 is strictly an offline diagnostic to test stop observability. No changes were made to EKF navigation state, NHC, ZUPT updates, SpeedNet model, or outage integration. Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 4. Existing M014 Stationary Detector

$$\mathcal{D}_{\text{M014}} = (p_{\text{stat\_speednet}} > 0.70)$$

---

## 5. Proposed Low-Speed Detector & 6. Exact Equations and Thresholds

$$\mathcal{D}_{\text{low}} = (v_{\text{speednet}} < 0.36\text{ km/h}) \quad \text{AND} \quad (|a_{\text{long}}| < 0.15\text{ m/s}^2)$$
where $v_{\text{speednet}}$ is the SpeedNet forward speed prediction in km/h and $a_{\text{long}} = -(raw\_ay - grav\_y)$ is longitudinal accelerometer reading.

---

## 7. Causality / Leakage Audit

Ground-truth speed ($v_{\text{GT}} < 0.1\text{ m/s}$) was used strictly offline for diagnostic label comparison. Proposed detector signals use strictly causal runtime inputs ($v_{\text{speednet}}$ and $a_{\text{long}}$). Zero future leakage.

---

## 8. Validation Confusion Matrix & 9. Precision / Recall / FPR / FNR / F1

- Total Validation Samples: 18,978 (10 Hz)
- True Ground-Truth Stationary Samples ($v_{\text{GT}} < 0.1\text{ m/s}$): 799 samples

| Detector | TP | FP | TN | FN | Precision | Recall | FPR | FNR | F1 Score |
|---|---|---|---|---|---|---|---|---|---|
| **M014 ($P_{\text{stat}} > 0.70$)** | **514** | **92** | **18,087** | **285** | **0.8482** | **0.6433** | **0.0051** | **0.3567** | **0.7317** |
| **Proposed Low-Speed Gate** | 133 | 10 | 18,169 | 666 | 0.9301 | 0.1665 | 0.0005 | 0.8335 | 0.2824 |
| **Combined Fusion (M014 OR Prop)** | **514** | **92** | **18,087** | **285** | **0.8482** | **0.6433** | **0.0051** | **0.3567** | **0.7317** |

---

## 10. Episode-Level Analysis

- Found **13 Ground-Truth Stationary Episodes** on Validation set:
  - **Full Stops ($\ge 5.0\text{ s}$, 3 episodes):** M014 average coverage = **69.9%** (latency $0.4 - 2.1\text{ s}$); Proposed gate average coverage = **18.5%** (latency $6.4 - 11.0\text{ s}$).
  - **Short Stops ($2.0 - 5.0\text{ s}$, 2 episodes):** M014 average coverage = **53.0%** (latency $0.0\text{ s}$); Proposed gate average coverage = **8.1%** (latency $0.1 - 0.4\text{ s}$).
  - **Creeping / Near-Stops ($< 2.0\text{ s}$, 8 episodes):** M014 average coverage = **17.4%**; Proposed gate average coverage = **0.0%** (0% detection due to speed smoothing).

---

## 11. Threshold Sensitivity

Across all tested speed thresholds ($0.20 - 0.75\text{ km/h}$) and acceleration thresholds ($0.10 - 0.20\text{ m/s}^2$), recall remained low ($2.88\% - 37.05\%$) due to neural prediction smoothing during stops.

---

## 12. Comparison Against M014

On both Validation set and locked test set (`108,000 : 111,000`), the proposed low-speed gate captured **EXACTLY 0 additional missed stationary samples** beyond what M014 already captures. Combined Fusion yields identical performance as M014 alone.

---

## 13. Scientific Interpretation & 14. Whether Sufficient Evidence Exists for M032

Every sample where SpeedNet predicts low speed ($v < 0.36\text{ km/h}$) is already 100% assigned high static probability ($P_{\text{stat}} > 0.70$) by SpeedNet's multi-task static head. The proposed gate is completely redundant with M014.

---

## 15. Final Verdict

**BRANCH CLOSED**.
M031 DIAGNOSTIC COMPLETE — active benchmark remains 218.93 m @ 300s. No M032 intervention will be created.

---

## 16. Recommended Next Experiment (M032 Proposal)

**M032 Proposal — Dynamic Cross-Track Covariance Inflation during High-Angular-Rate Turns**:
With longitudinal speed damping (M019, M028) and ZUPT stop detection (M014) fully closed, diagnostic M020 established that residual turn overestimation (+12.2 km/h during $|\omega_y| > 10^\circ/\text{s}$) generates 49.5° heading error across turns. M032 should evaluate a dynamic EKF NHC measurement covariance scaling during sharp turns ($R_{\text{nhc}}(\omega) = R_0 (1 + \alpha |\omega_y|)$ for $\alpha \in [0.1, 0.5]$) to decouple lateral velocity updates during aggressive steering, driving 300s position drift below $218.93\text{ m}$.

---

## 17. Full M001 → M031 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031`
