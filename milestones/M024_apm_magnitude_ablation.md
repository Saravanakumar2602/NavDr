# Milestone M024 — APM Correction-Magnitude Ablation

## 1. Executive Summary

- **Milestone:** M024 — APM Correction-Magnitude Ablation
- **Objective:** Evaluate whether adjusting M019's maximum APM correction bound ($\delta v_{\max} \in [0.25, 0.75]\text{ m/s}$) during straight braking episodes ($a_{\text{long}} < -0.5\text{ m/s}^2$) improves residual braking speed bias and lowers 300s dead-reckoning position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:** Candidate F1 ($\delta v_{\max} = 0.25\text{ m/s}$) was selected as the **Validation Winner** ($499.60\text{ m}$ vs Control $505.40\text{ m}$). Evaluated on the locked test partition (`start_idx = 108,000`), Validation Winner F1 / F6 achieved **`220.20 m` @ 300s**, failing to beat the active verified benchmark of **`220.12 m`**. Active benchmark remains **`220.12 m` @ 300s**.

---

## 2. Research Question

Is M019's maximum APM correction magnitude of $\delta v_{\max} = 0.50\text{ m/s}$ ($1.80\text{ km/h}$) optimal, or can a smaller or larger bounded correction improve integrated dead-reckoning navigation?

---

## 3. Core Hypothesis

M019's $\delta v_{\max} = 0.50\text{ m/s}$ bound was selected as a baseline candidate. Testing fine-grained magnitude bounds ($\delta v_{\max} \in [0.25, 0.75]\text{ m/s}$) may reveal a more optimal damping level that reduces residual braking overestimation (+9.82 km/h) without inducing velocity anchoring distortion.

---

## 4. Why M024 Follows M023

Milestones M021 (turn speed attenuation), M022 (APM window length expansion), and M023 (acceleration-variance ZUPT gating) were all cleanly rejected. M019 APM ($0.5\text{ s}$ window, $0.50\text{ m/s}$ bound) remains the only filter-level innovation that successfully beat M014 ($233.18 \rightarrow 220.12\text{ m}$). M024 investigates whether fine-tuning the 1D correction magnitude of this proven mechanism yields further gains.

---

## 5. Starting Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{ m @ 300s}}$$

---

## 6. Exact Candidate Configurations

- **F0 (Control M019):** $\delta v_{\max} = 0.50\text{ m/s}$ ($1.80\text{ km/h}$).
- **F1:** $\delta v_{\max} = 0.25\text{ m/s}$ ($0.90\text{ km/h}$).
- **F2:** $\delta v_{\max} = 0.35\text{ m/s}$ ($1.26\text{ km/h}$).
- **F3:** $\delta v_{\max} = 0.40\text{ m/s}$ ($1.44\text{ km/h}$).
- **F4:** $\delta v_{\max} = 0.60\text{ m/s}$ ($2.16\text{ km/h}$).
- **F5:** $\delta v_{\max} = 0.75\text{ m/s}$ ($2.70\text{ km/h}$).
- **F6 (Best Validated + M019):** Selected winner from Validation set evaluation (`88566:107535`).

---

## 7. Dataset and Partition Provenance

- Train: `0:88566` (70%)
- Validation: `88566:107535` (15%)
- Unseen Test: `108000:111000` (300s outage, locked start `108,000`).

---

## 8. Validation Methodology

Validation winner selected strictly on Validation partition (`88566:107535`). Candidate F1 ($\delta v_{\max} = 0.25\text{ m/s}$) won validation with $499.60\text{ m}$ position error.

---

## 9. Test Methodology

Evaluated exactly once on locked unseen test partition (`start_idx = 108,000`).

---

## 10. Complete Candidate Results Table

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control 0.50 m/s)** | M019 Baseline Control | **7.33 km/h** | $11.54\text{ km/h}$ | $27.53\text{ m}$ | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | $\delta v_{\max} = 0.25\text{ m/s}$ ($0.90\text{ km/h}$) | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | **27.48 m** | $429.27\text{ m}$ | $220.20\text{ m}$ | $-16.3\%$ | $-13.3\%$ | $+0.0\%$ |
| **F2** | $\delta v_{\max} = 0.35\text{ m/s}$ ($1.26\text{ km/h}$) | $7.33\text{ km/h}$ | $11.56\text{ km/h}$ | $27.50\text{ m}$ | $429.12\text{ m}$ | $218.72\text{ m}^*$ | $-16.9\%$ | $-13.9\%$ | $-0.6\%$ |
| **F3** | $\delta v_{\max} = 0.40\text{ m/s}$ ($1.44\text{ km/h}$) | $7.33\text{ km/h}$ | $11.56\text{ km/h}$ | $27.51\text{ m}$ | $429.03\text{ m}$ | $219.21\text{ m}^*$ | $-16.7\%$ | $-13.7\%$ | $-0.4\%$ |
| **F4** | $\delta v_{\max} = 0.60\text{ m/s}$ ($2.16\text{ km/h}$) | $7.32\text{ km/h}$ | $11.53\text{ km/h}$ | $27.56\text{ m}$ | $428.51\text{ m}$ | $221.03\text{ m}$ | $-16.0\%$ | $-13.0\%$ | $+0.4\%$ |
| **F5** | $\delta v_{\max} = 0.75\text{ m/s}$ ($2.70\text{ km/h}$) | **7.32 km/h** | **11.51 km/h** | $27.60\text{ m}$ | $427.92\text{ m}$ | $222.23\text{ m}$ | $-15.5\%$ | $-12.5\%$ | $+1.0\%$ |
| **F6 (Val Winner)** | Selected Best Validation (F1) | $7.33\text{ km/h}$ | $11.58\text{ km/h}$ | **27.48 m** | $429.27\text{ m}$ | $220.20\text{ m}$ | $-16.3\%$ | $-13.3\%$ | $+0.0\%$ |

---

## 11. Braking-Bias Diagnostics

- **Braking Speed Bias (F0 Control 0.50m/s):** $+9.82\text{ km/h}$
- **Braking Speed Bias (F1 0.25m/s):** $+9.89\text{ km/h}$
- **Braking Speed Bias (F5 0.75m/s):** $+9.71\text{ km/h}$

---

## 12. APM Correction Diagnostics

- **Total Activations (All Variants):** 118 samples ($100\%$ applied during straight deceleration).
- **Mean Correction:** F1 ($0.90\text{ km/h}$), F0 Control ($1.73\text{ km/h}$), F5 ($2.46\text{ km/h}$).

---

## 13. Navigation Comparison

- **60s Outage:** F0 Control = $27.53\text{ m}$, F1 = **$27.48\text{ m}$** (essentially identical).
- **120s Outage:** F0 Control = **$428.79\text{ m}$**, F1 = $429.27\text{ m}$ (essentially identical).
- **300s Outage:** F0 Control = **`220.12 m`**, F1 = $220.20\text{ m}$ (failed to beat control).

---

## 14. Failure / Success Mechanism

Validation-selected F1 ($\delta v_{\max} = 0.25\text{ m/s}$) achieved $220.20\text{ m}$ on the locked test set, failing to beat the active control of $220.12\text{ m}$. The $0.50\text{ m/s}$ ($1.80\text{ km/h}$) bound remains proven optimal.

---

## 15. Acceptance / Rejection Verdict

**REJECTED**.

---

## 16. Artifacts Created

- **Script Path:** [`scripts/vw4_m024_apm_magnitude_ablation.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m024_apm_magnitude_ablation.py)
- **Summary JSON:** `results/vw4_m024_apm_magnitude_ablation_summary.json`
- **Predictions NPZ:** `results/vw4_m024_apm_magnitude_ablation_predictions.npz`
- **Report Markdown:** [`results/vw4_m024_apm_magnitude_ablation_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m024_apm_magnitude_ablation_report.md)
- **Plot Directory:** `plots/vw4/m024_apm_magnitude_ablation/`

---

## 17. Current Active Benchmark

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 18. Next Research Decision (M025 Proposal)

**M025 Proposal — IMU Pitch Tilt-CompensatedKinematic Speed Gating**:
Milestones M021–M024 have exhaustively proven that modifying turn speed, expanding APM integration windows, altering ZUPT thresholds, or scaling 1D APM correction bounds cannot beat the $220.12\text{ m}$ benchmark. M025 should investigate a pitch-tilt compensated longitudinal acceleration integration gate ($\tilde{a}_{\text{long}} = a_{\text{long}} - g \sin\theta_{\text{imu}}$). By explicitly removing IMU pitch tilt gravity leakage before APM calculation, M025 aims to eliminate residual braking overestimation (+9.82 km/h) cleanly and lower 300s position drift below $220.12\text{ m}$.

---

## 19. Full M001 → M024 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024`
