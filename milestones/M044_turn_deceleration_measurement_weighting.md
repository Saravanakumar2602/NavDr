# Milestone M044 — Causal Turn/Deceleration Measurement-Weighting Study

## 1. Objective & Research Hypothesis

The objective of **Milestone M044** is to evaluate whether causally downweighting SpeedNet velocity updates ($R_v$) or suppressing Acceleration-Integrated Pseudo-Measurements (APM) during strong turns ($|\omega_y| > \theta_\omega$) and braking ($j_{\text{long}} < \theta_j$) can reduce position drift in the $600\text{ m} \to 1000\text{ m}$ failure zone without estimating absolute heading or training new neural models.

### Hypothesis:
During severe curved maneuvers, un-aided gyro yaw integration drift rotates the forward velocity vector into the lateral direction. Downweighting SpeedNet velocity updates during turns was hypothesized to prevent the EKF from integrating forward velocity overestimation into lateral cross-track drift.

---

## 2. Locked Production Baseline & Phase 0 Reproduction

The production baseline locked at M028/M040 is:

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro Yaw} + \text{Fixed 2D NHC } (R=0.04) + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate } (j_{\text{long}} < -1.00)$$

### Phase 0 Baseline Reproduction Check:
- **60 s Outage:** $27.35\text{ m}$ (Independent) / $27.88\text{ m}$ (Continuous 300s slice) — **Verified**
- **120 s Outage:** $426.85\text{ m}$ (Independent) / $426.17\text{ m}$ (Continuous 300s slice) — **Verified**
- **300 s Outage:** $218.93\text{ m}$ — **Exact Match**
- **1 km Outage ($t=150.0\text{ s}$):** $307.46\text{ m}$ ($30.74\%$ FPER / $307.41\text{ m/km}$) — **Verified**

---

## 3. Intervention Candidate Families & Grid

Four measurement-weighting candidate families were formulated:
- **F0:** Locked M028 production baseline (Control).
- **F1:** Suppress APM updates during strong turns ($|\omega_y| > \theta_\omega$).
- **F2:** Suppress APM updates during strong turns + braking ($|\omega_y| > \theta_\omega$ AND $j_{\text{long}} < \theta_j$).
- **F3:** Downweight SpeedNet velocity updates ($R_v \times \text{scale}$) during strong turns ($|\omega_y| > \theta_\omega$).
- **F4:** Jointly suppress APM and downweight SpeedNet velocity updates during strong turns + braking.

### Pre-Declared Validation Grid:
- $|\omega_y|$ thresholds: $5.0, 7.5, 10.0, 12.5, 15.0^\circ/\text{s}$
- $j_{\text{long}}$ thresholds: $-0.5, -1.0, -1.5, -2.0\text{ m/s}^3$
- SpeedNet $R_v$ scaling factor: $\times 2.0, \times 5.0, \times 10.0, \times 25.0$

---

## 4. Phase 2 — Validation Candidate Selection

Evaluated strictly on the Validation Partition ($88,566 \le k < 107,535$, $300\text{ s}$):

- **Validation F0 Baseline Error:** **`492.74 m`**
- **Validation Grid Search Winner:** **Candidate F3**
  - Family: **F3** (SpeedNet Measurement-Variance Downweighting)
  - Turn Threshold: $|\omega_y| > \mathbf{12.5^\circ/s}$ ($0.218\text{ rad/s}$)
  - Jerk Threshold: $j_{\text{long}} < -0.5\text{ m/s}^3$
  - SpeedNet $R_v$ Scale: $\mathbf{\times 10.0}$
  - Validation 300s Error: **`145.08 m`** (**$70.5\%$ improvement on validation!**)

---

## 5. Phase 5 — Locked Unseen Test Partition Evaluation

The validation-selected Candidate F3 was evaluated **once** on the locked unseen test partition (`start_idx = 108000`):

### Primary SIH Performance Comparison Table

| Metric | Locked Production Baseline (F0) | Validation-Selected Candidate (F3) | Delta / Change | SIH Compliance Status |
|---|:---:|:---:|:---:|:---:|
| **60 s Position Error** | **27.35 m** (27.88 m) | **40.11 m** | +12.76 m (+46.7%) | <span style="color:green; font-weight:bold;">PASS</span> (Near limit 40.90 m) |
| **120 s Position Error** | **426.85 m** (426.17 m) | **376.29 m** | -50.56 m (-11.8%) | <span style="color:red; font-weight:bold;">FAIL</span> |
| **300 s Position Error** | **218.93 m** | **574.98 m** | **+356.05 m (+162.6%)** | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **1 km Position Error** | **307.46 m** | **559.34 m** | **+251.88 m (+81.9%)** | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **300 s FPER (%)** | **15.81 %** | **41.53 %** | +25.72 % | <span style="color:red; font-weight:bold;">FAIL</span> |
| **1 km FPER (%)** | **30.74 %** | **55.93 %** | +25.19 % | <span style="color:red; font-weight:bold;">FAIL</span> |
| **Max Compliant Distance** | **491.50 m** | **412.00 m** | -79.50 m | Reduced |

---

## 6. Physical Mechanism & Failure Mode Analysis

1. **Why did Candidate F3 fail on the unseen test set despite winning validation?**  
   Candidate F3 inflates SpeedNet velocity measurement variance ($R_v \times 10.0$) during turns. Downweighting SpeedNet speed updates forces the EKF to rely on open-loop accelerometer/gyro integration during turn maneuvers.
2. **Disruption of Geometric Self-Cancellation:**  
   As mathematically proven in M040 and M042, SpeedNet forward speed overestimation (+6.4 km/h) creates a positive velocity anchor that actively cancels backward along-track integration lag. Inflating $R_v$ during turns suppresses this forward speed anchor, causing along-track and cross-track drift to explode to **$574.98\text{ m}$ at 300s** (+162.6% error increase) and **$559.34\text{ m}$ at 1 km** (+81.9% error increase).

---

## 7. Phase 6 — Final Verdict

**`B. REJECTED — Candidate F3 is REJECTED on the locked test partition due to severe 300s and 1km drift expansion (+162.6% 300s degradation) caused by geometric self-cancellation disruption. Production baseline (218.93 m @ 300s) remains LOCKED.`**

**Production Pipeline Changed?** **NO**.

---

## 8. Summary of Lessons Learned

- **Lesson 1:** Validation gain does NOT guarantee test set generalization when modifying EKF measurement variance without an online orientation update.
- **Lesson 2:** Measurement-weighting interventions during turns disrupt EKF geometric self-cancellation, producing severe position drift expansion over long outages ($300\text{ s}$).
- **Lesson 3:** Scalar speed measurement modification cannot solve 2D vector drift when heading integration error dominates.

---

## 9. Recommended Next Research Direction (M045 Proposal)

Because scalar measurement weighting and static heading overrides both disrupt geometric self-cancellation, Round 3 must explore **coupled velocity-heading joint constraints / zero-velocity orientation anchoring or multi-regime kinematic state augmentation** that respects EKF geometric self-cancellation dynamics.
