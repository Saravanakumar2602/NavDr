# Milestone M041 — SIH Benchmark Compliance & Distance-Normalized Evaluation

## 1. Objective

The objective of **Milestone M041** is to perform a rigorous, leakage-free benchmark compliance audit of the locked production dead-reckoning pipeline against the Smart India Hackathon (SIH) problem requirement:

$$\text{Final Position Drift} < 10\% \text{ of Reference Distance Travelled during GNSS Outage}$$

This milestone marks the opening evaluation phase of **Round 3** of the Intelligent Dead-Reckoning (IDR) project. In accordance with strict research discipline, **no model modifications, retraining, EKF tuning, or pipeline changes were performed**. M041 establishes the exact numerical baseline and distance-normalized evaluation methodology for all subsequent Round-3 milestones (M042+).

---

## 2. SIH Requirement

The SIH problem statement mandates that position drift during a GNSS outage must remain below $10\%$ of the actual distance traversed by the vehicle. The canonical SIH benchmark example is:

$$\text{Allowable Drift} < 100\text{ metres position drift per } 1\text{ kilometre travelled}$$

To evaluate compliance objectively across varying vehicle speeds and outage durations, two primary distance-normalized metrics are defined:

1. **Final Position Error Ratio (FPER %)**:
   $$\text{FPER (\%)} = \frac{\text{Final Position Error (m)}}{\text{Reference Distance Travelled } (D_{\text{ref}}\text{, m})} \times 100$$

2. **Distance-Normalized Drift (Error per km)**:
   $$\text{Error per km (m/km)} = \frac{\text{Final Position Error (m)}}{\text{Reference Distance Travelled } (D_{\text{ref}}\text{, km})} = \text{FPER (\%)} \times 10$$

3. **SIH Compliance Criterion**:
   $$\text{PASS if } \text{FPER} < 10.00\% \quad (\text{Error per km} < 100.00\text{ m/km}); \quad \text{FAIL otherwise.}$$

---

## 3. Locked Production Pipeline

The production navigation pipeline locked at M028/M040 was executed without modification:

```
SpeedNet v2 (W=40, 6-Channel Normalized IMU)
   ↓
Raw Gyro Yaw Integration (w_yaw = -gyro_pitch)
   ↓
Fixed 2D Non-Holonomic Constraint (NHC R = 0.04 m²/s²)
   ↓
M013 F4 Hard Physical Speed Constraint (sigma_a² <= 3.72, |omega_y| <= 5 deg/s)
   ↓
M014 F3 Causal ZUPT (P(stat) > 0.70, ZUPT sigma = 0.20 m/s)
   ↓
M019 Acceleration-Integrated Pseudo-Measurement (a_long < -0.5 m/s², 0.5s causal integration, delta-v max = 0.50 m/s)
   ↓
M028 Causal Longitudinal Jerk Gate (j_long < -1.00 m/s³)
   ↓
EKF Navigation Estimator (7-State ENU Kinematic Filter)
```

**Locked Production Benchmark Errors**:
- **60 s Outage:** $27.35\text{ m}$ (independent run) / $27.88\text{ m}$ (continuous 300s slice)
- **120 s Outage:** $426.85\text{ m}$ (independent run) / $426.17\text{ m}$ (continuous 300s slice)
- **300 s Outage:** $218.93\text{ m}$ (exact match)

---

## 4. Dataset and Test Configuration

The audit was conducted strictly on the unseen test partition of the synchronized `Vw04` (Driver E) dataset:

- **Total Synchronized Timesteps:** $N = 126,523$ samples ($12,652.3\text{ s}$)
- **Training Partition:** Indices $0 \le k < 88,566$ (0.00% – 70.00%)
- **Validation Partition:** Indices $88,566 \le k < 107,535$ (70.00% – 85.00%)
- **Unseen Test Outage Start:** Index `start_idx = 108000` ($10,800.0\text{ s}$)
- **Sampling Frequency:** $f_s = 10\text{ Hz}$ ($\Delta t = 0.1\text{ s}$)
- **Outage Window:** UTC time $10,800.0\text{ s}$ to $11,100.0\text{ s}$ ($300\text{ s}$ total)
- **Initialization:** Prior $30.0\text{ s}$ (300 pre-samples) with GNSS measurement updates before blackout.

---

## 5. Reference Distance Method

The actual reference distance travelled by the vehicle during each GNSS outage interval ($D_{\text{ref}}$) was computed strictly from the VBOX ground-truth position trajectory $[x_{\text{gt}}, y_{\text{gt}}]$ using point-to-point 2D Euclidean step accumulation (reusing the canonical project method from `vw4_baseline_dr_experiment.py`):

$$D_{\text{ref}} = \sum_{k=\text{start\_idx}+1}^{\text{start\_idx}+N-1} \sqrt{(x_{\text{gt}}[k] - x_{\text{gt}}[k-1])^2 + (y_{\text{gt}}[k] - y_{\text{gt}}[k-1])^2}$$

**Verification of Distance Definitions:**
- **Step Accumulation ($D_{\text{ref}}$):** Cumulative 2D path length along reference curve (canonical).
- **Speed Integration ($\int v_{\text{vbox}} dt$):** Integrated ground-truth scalar velocity ($D_{\text{vel\_60}} = 405.85\text{ m}$, $D_{\text{vel\_120}} = 869.70\text{ m}$, $D_{\text{vel\_300}} = 1377.11\text{ m}$).
- **Point-to-Point Displacement:** Direct Euclidean distance between start and end coordinates ($D_{\text{disp\_60}} = 388.80\text{ m}$, $D_{\text{disp\_120}} = 817.08\text{ m}$, $D_{\text{disp\_300}} = 825.82\text{ m}$).

Step accumulation $D_{\text{ref}}$ was selected as the true reference path length because it reflects the real curvilinear distance traversed by the vehicle.

---

## 6. 60 s Outage Evaluation

- **Reference Travel Distance ($D_{\text{ref\_60}}$):** **`409.00 m`** ($0.4090\text{ km}$)
- **Production Position Drift:** **`27.35 m`** (Independent) / **`27.88 m`** (Continuous)
- **SIH Allowable Limit ($10\%$ of $D_{\text{ref}}$):** **`40.90 m`**
- **FPER (%):** **`6.69 %`** (Independent) / **`6.82 %`** (Continuous)
- **Error per km:** **`66.87 m/km`** (Independent) / **`68.17 m/km`** (Continuous)
- **SIH Margin ($10.00\% - \text{FPER}$):** **`+3.31 %`**
- **SIH Compliance Status:** <span style="color:green; font-weight:bold;">PASS</span> ($6.69\% < 10.00\%$, $< 100\text{ m/km}$)

---

## 7. 120 s Outage Evaluation

- **Reference Travel Distance ($D_{\text{ref\_120}}$):** **`874.76 m`** ($0.8748\text{ km}$)
- **Production Position Drift:** **`426.85 m`** (Independent) / **`426.17 m`** (Continuous)
- **SIH Allowable Limit ($10\%$ of $D_{\text{ref}}$):** **`87.48 m`**
- **FPER (%):** **`48.80 %`** (Independent) / **`48.72 %`** (Continuous)
- **Error per km:** **`487.96 m/km`** (Independent) / **`487.18 m/km`** (Continuous)
- **SIH Margin ($10.00\% - \text{FPER}$):** **`-38.80 %`**
- **SIH Compliance Status:** <span style="color:red; font-weight:bold;">FAIL</span> ($48.80\% \gg 10.00\%$, $> 100\text{ m/km}$)

---

## 8. 300 s Outage Evaluation

- **Reference Travel Distance ($D_{\text{ref\_300}}$):** **`1384.63 m`** ($1.3846\text{ km}$)
- **Production Position Drift:** **`218.93 m`** (Exact Match)
- **SIH Allowable Limit ($10\%$ of $D_{\text{ref}}$):** **`138.46 m`**
- **FPER (%):** **`15.81 %`**
- **Error per km:** **`158.11 m/km`**
- **SIH Margin ($10.00\% - \text{FPER}$):** **`-5.81 %`**
- **SIH Compliance Status:** <span style="color:red; font-weight:bold;">FAIL</span> ($15.81\% > 10.00\%$, $> 100\text{ m/km}$)

---

## 9. 1 km Evaluation

The SIH problem statement specifically highlights compliance at **1 kilometre of travel** ($< 100\text{ m}$ drift per $1\text{ km}$). The test outage trajectory was evaluated to locate the exact timestep where $D_{\text{ref}} \approx 1000\text{ m}$:

- **1 km Reached?** **YES** (The vehicle travels $1384.63\text{ m}$ over $300\text{ s}$).
- **Elapsed Outage Time ($T_{1\text{km}}$):** **`150.0 s`** (1,500 samples)
- **Exact Reference Distance ($D_{\text{ref\_1km}}$):** **`1000.17 m`** ($1.00017\text{ km}$)
- **Production Position Error at 1 km:** **`307.46 m`**
- **SIH Allowable Limit at 1 km:** **`100.02 m`**
- **FPER at 1 km:** **`30.74 %`**
- **Error per km at 1 km:** **`307.41 m/km`**
- **SIH 1 km Compliance Status:** <span style="color:red; font-weight:bold;">FAIL</span> ($307.46\text{ m} > 100.00\text{ m}$)

---

## 10. Distance-Normalized Results

### Primary Comparison Table

| Outage Duration | Reference Distance ($D_{\text{ref}}$) | Final Position Error | FPER (%) | Error per km | SIH Allowable Limit | SIH Status |
|---|---|---|---|---|---|---|
| **60 s** | **409.00 m** | **27.35 m** | **6.69 %** | **66.87 m/km** | 40.90 m (10%) | <span style="color:green; font-weight:bold;">PASS</span> |
| **120 s** | **874.76 m** | **426.85 m** | **48.80 %** | **487.96 m/km** | 87.48 m (10%) | <span style="color:red; font-weight:bold;">FAIL</span> |
| **300 s** | **1384.63 m** | **218.93 m** | **15.81 %** | **158.11 m/km** | 138.46 m (10%) | <span style="color:red; font-weight:bold;">FAIL</span> |

### 1-km Distance Benchmark Table

| Metric | Current Production Pipeline | SIH Requirement | Compliance Status |
|---|---|---|---|
| **1 km reference distance reached?** | **YES** ($1000.17\text{ m}$) | Required | Met |
| **Time to travel 1 km ($T_{1\text{km}}$)** | **150.0 s** | N/A | Evaluated |
| **Error at ~1 km** | **307.46 m** | $< 100.00\text{ m}$ | <span style="color:red; font-weight:bold;">FAIL</span> |
| **FPER at 1 km** | **30.74 %** | $< 10.00\text{ \%}$ | <span style="color:red; font-weight:bold;">FAIL</span> |
| **Error per km** | **307.41 m/km** | $< 100.00\text{ m/km}$ | <span style="color:red; font-weight:bold;">FAIL</span> |
| **SIH overall 1 km status** | **NON-COMPLIANT** | PASS | <span style="color:red; font-weight:bold;">FAIL</span> |

---

## 11. PASS/FAIL Determination

- **60 s Outage:** <span style="color:green; font-weight:bold;">PASS</span> (FPER $6.69\% < 10.00\%$).
- **120 s Outage:** <span style="color:red; font-weight:bold;">FAIL</span> (FPER $48.80\% \gg 10.00\%$).
- **300 s Outage:** <span style="color:red; font-weight:bold;">FAIL</span> (FPER $15.81\% > 10.00\%$).
- **1 km Outage:** <span style="color:red; font-weight:bold;">FAIL</span> (FPER $30.74\% > 10.00\%$).

**Overall Production Pipeline Verdict:** The current locked production pipeline **FAILS** the SIH benchmark requirement for outages exceeding $60\text{ s}$ or travel distances exceeding $491.5\text{ m}$.

---

## 12. Sanity and Leakage Audit

1. **Positive Reference Distance:** Verified $D_{\text{ref\_60}} = 409.00\text{ m}$, $D_{\text{ref\_120}} = 874.76\text{ m}$, $D_{\text{ref\_300}} = 1384.63\text{ m}$ are strictly positive and monotonically increasing.
2. **Interval Slicing Integrity:** Verified that 60s distance is computed strictly over samples $[108000, 108600)$, 120s over $[108000, 109200)$, and 300s over $[108000, 111000)$. No 300s distance was leaked into 60s or 120s evaluations.
3. **Zero Test Data Leakage:** No VBOX position, velocity, or heading data was fed to the SpeedNet model or EKF estimator during the outage window. VBOX data was accessed exclusively for post-hoc reference distance and drift evaluation.
4. **Zero Model Alteration:** Model architecture, weights (`models/speednet_v2_w40.pth`), EKF parameters, and threshold gates remained $100\%$ untouched.
5. **Locked Benchmark Preservation:** The target benchmark numbers ($27.35\text{ m}$, $426.85\text{ m}$, $218.93\text{ m}$) were reproduced with $100\%$ mathematical consistency.

---

## 13. Interpretation & Practical SIH Operating Envelope

- **Operating Envelope Analysis:** Continuous tracking of FPER against traversed distance reveals that the system maintains $\text{FPER} < 10\%$ up to **$D_{\text{max}} = 491.50\text{ m}$** ($t = 72.0\text{ s}$).
- **The Turn-Deceleration Bottleneck:** Between $t = 72\text{ s}$ and $t = 150\text{ s}$ ($D_{\text{ref}} \in [490\text{ m}, 1000\text{ m}]$), the vehicle performs sharp braking and turn maneuvers. Heading errors integrated during these turns cause position drift to spike to $426.85\text{ m}$ ($48.80\%$).
- **Non-Monotonic Error Behavior:** Between $t = 150\text{ s}$ and $t = 300\text{ s}$, zero-velocity updates (ZUPTs) and straight-line trajectory segments allow the EKF to stabilize, causing FPER to decay from $48.80\%$ back down to $15.81\%$ ($218.93\text{ m}$).

---

## 14. Round-3 Starting Point & Target Gap

To satisfy the SIH requirement across full 300-second / multi-kilometre outages, the Round-3 model enhancement phase must achieve the following drift reductions:

- **120 s Outage:** Reduce error from $426.85\text{ m}$ ($48.80\%$) to $< 87.48\text{ m}$ ($< 10.00\%$) — **Requires $79.5\%$ drift reduction ($339.37\text{ m}$ improvement)**.
- **300 s Outage:** Reduce error from $218.93\text{ m}$ ($15.81\%$) to $< 138.46\text{ m}$ ($< 10.00\%$) — **Requires $36.8\%$ drift reduction ($80.47\text{ m}$ improvement)**.
- **1 km Outage:** Reduce error at 1 km from $307.46\text{ m}$ ($30.74\%$) to $< 100.00\text{ m}$ ($< 10.00\%$) — **Requires $67.5\%$ drift reduction ($207.46\text{ m}$ improvement)**.

---

## 15. Research Answers to Required Benchmark Questions

1. **Q1. What distance does the vehicle actually travel during 60 s?**
   - **Answer:** **`409.00 m`** ($0.4090\text{ km}$).
2. **Q2. What distance does it actually travel during 120 s?**
   - **Answer:** **`874.76 m`** ($0.8748\text{ km}$).
3. **Q3. What distance does it actually travel during 300 s?**
   - **Answer:** **`1384.63 m`** ($1.3846\text{ km}$).
4. **Q4. What is the SIH allowable position error for each?**
   - **Answer:** **`40.90 m`** (60s), **`87.48 m`** (120s), and **`138.46 m`** (300s).
5. **Q5. What is our current FPER for each?**
   - **Answer:** **`6.69 %`** (60s), **`48.80 %`** (120s), and **`15.81 %`** (300s).
6. **Q6. What is our current error in metres per kilometre?**
   - **Answer:** **`66.87 m/km`** (60s), **`487.96 m/km`** (120s), and **`158.11 m/km`** (300s).
7. **Q7. Does the current production system satisfy the <10% / <100 m/km requirement?**
   - **Answer:** **PASS for 60 s**; **FAIL for 120 s and 300 s**.
8. **Q8. Does it satisfy the requirement at approximately 1 km travelled?**
   - **Answer:** **NO (FAIL).** At $D_{\text{ref}} = 1000.17\text{ m}$ ($t = 150.0\text{ s}$), position drift is $307.46\text{ m}$ ($30.74\% / 307.41\text{ m/km}$ vs limit of $100.00\text{ m}$).
9. **Q9. If not, how much improvement is required?**
   - **Answer:** Position drift at 1 km must be reduced by **$207.46\text{ m}$ ($67.5\%$ reduction)**; drift at 300s must be reduced by **$80.47\text{ m}$ ($36.8\%$ reduction)**.
10. **Q10. What is the maximum travelled distance for which the current system remains below the 10% threshold?**
    - **Answer:** **`491.50 m`** ($t = 72.0\text{ s}$).
11. **Q11. What should become the primary benchmark for M042+?**
    - **Answer:** **SIH distance-normalized position drift, expressed primarily as metres per kilometre (m/km) and FPER (%)**, while retaining 60s, 120s, and 300s as secondary benchmark duration metrics.

---

## 16. Generated Artifact Paths

- **Audit Execution Script:** [`scripts/vw4_m041_sih_benchmark_audit.py`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m041_sih_benchmark_audit.py)
- **JSON Summary Results:** [`results/vw4_m041_sih_benchmark_audit.json`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m041_sih_benchmark_audit.json)
- **Markdown Audit Summary:** [`results/vw4_m041_sih_benchmark_audit.md`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m041_sih_benchmark_audit.md)
- **Plot 1 (Reference Distance vs Time):** [`results/plots/m041_reference_distance_vs_time.png`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/plots/m041_reference_distance_vs_time.png)
- **Plot 2 (Error vs Reference Distance):** [`results/plots/m041_error_vs_reference_distance.png`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/plots/m041_error_vs_reference_distance.png)
- **Plot 3 (FPER vs Reference Distance):** [`results/plots/m041_fper_vs_reference_distance.png`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/plots/m041_fper_vs_reference_distance.png)
- **Milestone Documentation:** [`milestones/M041_sih_benchmark_compliance_audit.md`](file:///C:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/milestones/M041_sih_benchmark_compliance_audit.md)

---

## 17. Conclusion & Next Steps

Milestone M041 confirms that our locked production pipeline is **60s-compliant** ($6.69\%$), but non-compliant over 120s ($48.80\%$), 300s ($15.81\%$), and 1 km ($30.74\%$).

**Confirmation:** Production code, EKF logic, SpeedNet models, and gating parameters were **NOT modified** during this audit.

With M041 established as the numerical starting point for Round 3, model enhancement planning for M042+ can now proceed based on distance-normalized metrics ($< 100\text{ m/km}$).
