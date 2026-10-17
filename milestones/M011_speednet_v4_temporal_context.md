# Milestone M011 — Sequence Window / Temporal Context Experiment

## 1. Milestone ID
- **Identifier:** `M011_speednet_v4_temporal_context`

---

## 2. Date
- **Date:** 2026-09-01
- **Status:** REJECTED (Hypothesis REJECTED)

---

## 3. Start Point / Previous State
- **Context:** Following the rejection of dynamic slip states (`M009`) and adaptive NHC covariance (`M010`), M011 investigates whether expanding the temporal sequence context window ($W \in [40, 50, 60, 80]$, 4.0s to 8.0s sequence context) or introducing dilated temporal convolutions enables SpeedNet to observe long-horizon deceleration trends, eliminating systematic speed overestimation during braking.
- **Provenance-Locked Benchmark to Beat:** **SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC = 263.11 m @ 300s** (Unseen test partition `start_idx = 108,000`).
- **Available Code:** [`scripts/vw4_m011_speednet_v4_temporal_context.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m011_speednet_v4_temporal_context.py).

---

## 4. Research Question
Can increasing the temporal receptive field of SpeedNet improve speed estimation during braking/deceleration and reduce 300-second navigation drift below the provenance-locked SpeedNet v2 + Raw Gyro + Fixed NHC benchmark of 263.11 m?

---

## 5. Hypothesis
Expanding sequence window length ($W > 40$) or incorporating dilated 1D-CNN temporal convolutions ($d=2$) will provide multi-second temporal context, resolving deceleration ambiguity in 4.0s IMU windows and reducing speed bias during braking from $+8.79\text{ km/h} \rightarrow <3.0\text{ km/h}$, leading to 300s position error $<150\text{ m}$.

---

## 6. Why This Experiment Was Chosen
M006 residual decomposition proved that systematic forward-speed overestimation during braking causes $+322\text{ m}$ of the remaining error. Downstream EKF modifications (M005, M007, M008, M009, M010) failed to beat 263.11 m, isolating the neural speed estimator's temporal representation as the primary bottleneck.

---

## 7. Previous Evidence Supporting It
- SpeedNet v1 ($W=30$) produced 1,465 m error, while SpeedNet v2 ($W=40$) reduced error to 263.11 m, demonstrating that increasing sequence window length from 3.0s to 4.0s yielded a 5.5x reduction in navigation drift.

---

## 8. Changes Built
- **Scripts Created:**
  - [`scripts/vw4_m011_speednet_v4_temporal_context.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m011_speednet_v4_temporal_context.py) — Multi-window training, validation selection, locked unseen test evaluation, and braking regime diagnostic driver.
- **Models Trained:**
  - `models/speednet_v2_w40.pth` (F0 Control, Val MAE = 12.37 km/h)
  - `models/speednet_v2_w50.pth` (F1 Candidate, Val MAE = 12.62 km/h)
  - `models/speednet_v2_w60.pth` (F2 Candidate, Val MAE = 14.58 km/h)
  - `models/speednet_v2_w80.pth` (F3 Candidate, Val MAE = 47.29 km/h — Vanishing Gradient Local Min)
  - `models/speednet_v4_w60_d2.pth` (**F4 Selected Candidate, Val MAE = 12.18 km/h**)
- **Reports & Artifacts:**
  - [`results/vw4_m011_speednet_v4_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_report.md)
  - [`results/vw4_m011_speednet_v4_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_summary.json)
  - [`results/vw4_m011_speednet_v4_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_predictions.npz)
  - `plots/vw4/m011_speednet_v4/` (6 diagnostic plots)

---

## 9. Experimental Methodology
- **Dataset:** Vw04, 10 Hz synchronized IMU/VBOX.
- **Train Partition:** `0:88566`.
- **Validation Partition:** `88566:107535`.
- **Unseen Test Partition:** `start_idx = 108,000`.
- **Model Selection Protocol:** Candidate selected exclusively on validation speed MAE (`88566:107535`).
- **Locked Evaluation Protocol:** Evaluated selected model ONCE on test set for 60s, 120s, and 300s outage durations using Raw Gyro + Fixed NHC ($R_0 = 0.04$).

---

## 10. Dataset and Partition Provenance
- Train: 88,566 samples (70%).
- Val: 18,969 samples (15%).
- Unseen Test: 18,970 samples (15%), `start_idx = 108,000`. Zero test data used for parameter tuning.

---

## 11. Baseline Configuration
- **F0 Control:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC ($R_0 = 0.04$). 300s position error = **`263.11 m`**.

---

## 12. Candidate Configurations
- **F1:** SpeedNet v2 ($W=50$, 5.0s window)
- **F2:** SpeedNet v2 ($W=60$, 6.0s window)
- **F3:** SpeedNet v2 ($W=80$, 8.0s window)
- **F4:** SpeedNet v4 Dilated ($W=60, d=2$, 12.0s effective receptive field)

---

## 13. Validation Results

| Variant Name | Parameters | Val Speed MAE (km/h) | Val Speed Bias (km/h) | Selection Status |
|---|:---:|---:|---:|:---:|
| F0: Control (W=40) | 89,220 | 12.37 km/h | +1.33 km/h | Baseline Control |
| F1: SpeedNet v2 (W=50) | 89,220 | 12.62 km/h | +4.44 km/h | Candidate |
| F2: SpeedNet v2 (W=60) | 89,220 | 14.58 km/h | +8.54 km/h | Candidate |
| F3: SpeedNet v2 (W=80) | 89,220 | 47.29 km/h | -47.29 km/h | Failed |
| **F4: SpeedNet v4 Dilated** | **89,220** | **`12.18 km/h`** | **-1.87 km/h** | **SELECTED** ✅ |

---

## 14. Locked Test Results (Unseen Test Partition `start_idx = 108,000`)

| Variant Name | Test Speed MAE | Test Speed Bias | 60s Error | 120s Error | 300s Error | 300s CDE % | vs Benchmark |
|---|---:|---:|---:|---:|---:|---:|---|
| **F0: SpeedNet v2 Control (W=40)** | **7.59 km/h** | **+7.99 km/h** | **22.75 m** | **440.20 m** | **`263.11 m`** | **33.7%** | **BENCHMARK** |
| F1: SpeedNet v2 (W=50) | 8.92 km/h | +8.41 km/h | 62.00 m | 1125.54 m | 963.59 m | 34.0% | +700.48m (+266.2%) |
| F2: SpeedNet v2 (W=60) | 10.62 km/h | +8.54 km/h | 154.49 m | 537.10 m | 873.70 m | 34.6% | +610.59m (+232.1%) |
| F3: SpeedNet v2 (W=80) | 16.53 km/h | -16.53 km/h | 382.58 m | 808.88 m | 819.34 m | 35.6% | +556.23m (+211.4%) |
| **F4: SpeedNet v4 Dilated [SELECTED]** | **8.62 km/h** | **+8.05 km/h** | **249.43 m** | **331.60 m** | **`595.04 m`** | **36.0%** | **+331.93m (+126.2%)** |

---

## 15. Navigation Results
- Selected candidate F4 achieved `595.04 m` position error at 300s (+331.93 m / +126.2% worse than benchmark `263.11 m`).

---

## 16. Ablation Findings
- **Braking Speed Bias Breakdown:**
  - F0 Control ($W=40$) Braking Bias: `+8.79 km/h`
  - F2 ($W=60$) Braking Bias: `+11.55 km/h`
  - F4 Dilated ($W=60, d=2$) Braking Bias: `+9.12 km/h`
- Expanding sequence window length **increased speed overestimation during braking** (+8.79 km/h $\rightarrow$ +11.55 km/h) due to temporal memory lag.

---

## 17. What Failed
- **Receptive Field Expansion (W=50, 60, 80 & Dilated W=60):** REJECTED.

---

## 18. What Worked
- SpeedNet v2 $W=40$ remains the optimal temporal sequence window length.

---

## 19. Scientific Interpretation
Expanding sequence window length introduces **temporal phase lag and over-smoothing during speed transitions**. Long BiLSTM memory retains historical high-speed frames during deceleration, delaying speed reduction and accumulating large navigation integration errors. Pointwise validation speed MAE does not capture temporal phase lag, creating a severe task-metric mismatch.

---

## 20. Learned Knowledge
1. Validation Speed MAE (`12.18 km/h` for F4 vs `12.37 km/h` for F0) does NOT correlate with integrated navigation drift (`595.04 m` vs `263.11 m`).
2. Expanding sequence window size beyond $W=40$ causes vanishing gradients ($W=80$) and phase lag ($W=50, 60$).

---

## 21. Artifact Inventory
- [`scripts/vw4_m011_speednet_v4_temporal_context.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m011_speednet_v4_temporal_context.py)
- [`results/vw4_m011_speednet_v4_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_report.md)
- [`results/vw4_m011_speednet_v4_summary.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_summary.json)
- [`results/vw4_m011_speednet_v4_predictions.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m011_speednet_v4_predictions.npz)
- `plots/vw4/m011_speednet_v4/` (6 plots)

---

## 22. Current Project State
- **Verified Best Deployable System:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC (**263.11 m @ 300s**).

---

## 23. Benchmark Comparison
- F0 Control ($W=40$): **263.11 m**
- F4 Selected Model: **595.04 m** (+331.93 m / +126.2% worse)

---

## 24. Decision / Verdict
- **M011 Verdict:** **REJECTED**

---

## 25. Next-Step Recommendation
- **What to do next:** Investigate **M012 — Kinematic Deceleration Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)**.
- **Why:** M006–M011 prove that standard neural regression losses (Smooth L1, MSE) fail to penalize physical overestimation during deceleration regimes, while sequence window expansion introduces phase lag. M012 will introduce an explicit physical kinematic upper bound constraint ($v_k \le v_{k-1} + a_{\text{long},k} \cdot \Delta t$) directly into the neural loss function during training, enforcing physical consistency with longitudinal IMU acceleration.

---

## 26. Research Chain
```
M001 (Dataset Formulation)
  └── M002 (ML Baselines Training)
        └── M003 (SpeedNet v1 Baseline)
              └── M004 (SpeedNet v2 Baseline: 263.11 m)
                    └── M005 (HeadingNet Ablation: Rejected)
                          └── M006 (Residual Error Decomposition)
                                └── M007 (SpeedNet v3 Regime-Aware: Rejected)
                                      └── M008 (SpeedNet v2.5 Physics Features: Rejected)
                                            └── M009 (NHC Slip Diagnostic: Rejected)
                                                  └── M010 (Adaptive NHC Covariance: Rejected)
                                                        └── M011 (Sequence Window Context: Rejected)
                                                              └── M012 (Kinematic Loss Constraint: Planned)
```
