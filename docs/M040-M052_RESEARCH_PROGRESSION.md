# IDR Research Progression: M040–M052
## From Navigation Error Attribution to Observability Analysis and Controlled Failure Closure

**Project**: SIH 2026 Intelligent Dead-Reckoning (IDR)  
**Dataset**: Vw04 Smartphone IMU + VBOX Ground Truth (10 Hz, 126,505 samples)  
**Scope**: Synthesis of Milestones M040 through M052  
**Canonical Deployed Production Baseline**: **M028 (SpeedNet v2 + M013 F4 + ZUPT + M019 APM + M028 Jerk Gate)**  
**Status of Production Pipeline**: **100% UNCHANGED (Locked at M028: 218.93 m @ 300 s / 307.46 m @ 1 km)**

---

## 1. Executive Research Snapshot

### Context and Core Challenge (at M040 Baseline)
Around milestone M040, the Intelligent Dead-Reckoning (IDR) pipeline had established a locked production baseline (**M028**) combining a deep neural speed estimator (**SpeedNet v2**, $W=40$), hard physical inference constraints (**M013 F4**), zero-velocity updates (**M014 ZUPT**), acceleration-integrated pseudo-measurements (**M019 APM**), and zero-latency IMU jerk gating (**M028 Jerk Gate**). This pipeline achieved an integrated 300 s position error of **218.93 m** on unseen locked test data ($start\_idx = 108,000$).

However, long-horizon evaluation against the Smart India Hackathon (SIH) requirement (**FPER < 10%** / **Error < 100 m/km**) revealed a major bottleneck: while the system easily passed the 60 s outage requirement (**27.35 m / 6.69% FPER**), navigation error escalated severely at longer horizons (**426.85 m at 120 s**, **218.93 m at 300 s**, and **307.46 m at 1 km**), leaving the maximum compliant distance capped at **491.50 m**.

### Key Research Insights (M040–M052)
Milestone M040 uncovered a critical filter phenomenon: **EKF Geometric Self-Cancellation**. In the production EKF, SpeedNet's slight scalar speed overestimation (+6.4 km/h during braking/turns) acts as a vital longitudinal anchor that counteracts lateral drift caused by un-aided gyro yaw integration drift. Substituting ground-truth (GT) speed into the EKF actually *degraded* 300 s navigation performance from **218.93 m to 511.62 m** (+133.7% error explosion).

Between M041 and M052, the research team conducted systematic, hypothesis-driven interventions across four logical phases to address this coupled error mechanism:

```
+--------------------------------------------------------------------------------------------------+
|                                    RESEARCH PROGRESSION PHASES                                   |
+--------------------------------------------------------------------------------------------------+
| PHASE A: Benchmark Compliance & Failure Localization (M040–M043)                                |
|   - Quantified SIH FPER limits & localized failure window to curved maneuvers (70s–120s).       |
|   - Proved 2D yaw is physically unobservable from 6-axis IMU without external reference.         |
+--------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+--------------------------------------------------------------------------------------------------+
| PHASE B: Turn/Heading & Measurement Intervention Attempts (M044–M049)                          |
|   - Evaluated turn measurement weighting (M044), learned gyro drift net (M046), and NHC          |
|     innovation gating (M047). All validation winners failed to generalize on locked test data.  |
|   - Proved EKF world-vs-body state formulations are mathematically identical (M048).              |
|   - Quantified heading information bounds via oracle anchors (M049).                             |
+--------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+--------------------------------------------------------------------------------------------------+
| PHASE C: Representation & Kinematic Constraint Attempts (M050–M051)                             |
|   - Evaluated learned body-frame velocity vectors (M050) and zero-velocity heading bounds (M051).|
|   - Proved ZUPT matrix H_zupt has rank 2 and provides zero yaw angle observability.              |
|   - Both validation winners degraded locked test performance (817.69 m and 598.34 m @ 300s).    |
+--------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+--------------------------------------------------------------------------------------------------+
| PHASE D: Physical Acceleration Hypothesis (M052)                                                 |
|   - Diagnosed large turn-induced centrifugal acceleration contamination (|a_c| up to 18.94 m/s²).|
|   - Direct compensation (F1_a0.2) won validation (488.80 m) but catastrophically degraded test    |
|     data to 1040.45 m @ 300s. Branch rejected.                                                   |
+--------------------------------------------------------------------------------------------------+
```

### Current Status
All 13 milestones (M040–M052) have been fully executed, documented, and closed. Because every candidate intervention that improved validation performance failed on unseen locked test data, **no production pipeline changes were accepted**. The production baseline remains strictly locked at **M028** (**218.93 m @ 300 s**).

---

## 2. M040–M043: Establishing Where the Error Comes From

The initial research block focused on auditing system behavior, establishing benchmark compliance, localizing error sources, and analyzing mathematical observability.

### M040 — Counterfactual Consistency Audit
M040 audited the discrepancy between pure kinematic dead-reckoning and production EKF behavior.
- **Pure Kinematic Floor**: Replacing estimated speed and gyro yaw with VBOX GT speed and GT heading inside an open-loop kinematic integrator produced a trajectory floor error of **5.64 m @ 300 s**.
- **EKF Counterfactual Discrepancy**: Substituting GT speed into the production EKF degraded 300 s position error to **511.62 m** (and up to **672.48 m** in M045 audits).
- **Core Finding**: Proved the existence of **Geometric Self-Cancellation** inside the production EKF. Downweighting or altering SpeedNet updates during turns disrupts this delicate balance between longitudinal speed bias and cross-track heading drift.

### M041 — SIH Benchmark Compliance Audit
M041 established the formal, distance-normalized evaluation framework mandated by SIH (<10% FPER / <100 m/km).
- **60 s Outage ($D_{\text{ref}} = 409.00\text{ m}$)**: **27.35 m / 6.69% FPER** (**PASS**)
- **120 s Outage ($D_{\text{ref}} = 874.76\text{ m}$)**: **426.85 m / 48.80% FPER** (**FAIL**)
- **300 s Outage ($D_{\text{ref}} = 1384.63\text{ m}$)**: **218.93 m / 15.81% FPER** (**FAIL**)
- **1 km Travel ($D_{\text{ref}} = 1000.17\text{ m}$)**: **307.46 m / 30.74% FPER** (**FAIL**)
- **Maximum Compliant Distance**: **`491.50 m`**

### M042 — Failure Mechanism Localization
M042 localized the origin of the 120 s error explosion ($426.85\text{ m}$) to dynamic curved maneuvers occurring between $t = 70\text{ s}$ and $t = 120\text{ s}$ ($500\text{ m} \to 874\text{ m}$ reference distance).
1. Un-aided gyro yaw integration drift accumulated to **$-43.68^\circ$** at $t = 112\text{ s}$ ($800\text{ m}$).
2. Orientation error rotated forward velocity into the transverse direction, driving cross-track error to **$-414.77\text{ m}$** at 120 s.
3. Between $120\text{ s}$ and $300\text{ s}$, vehicle trajectory curvature reversed, causing along-track and cross-track drift components to partially self-cancel, pulling total position drift back down to **218.93 m** at 300 s.

### M043 — Heading Observability Audit
M043 investigated whether 2D yaw angle $\psi$ is observable from 6-axis smartphone IMU data during dynamic maneuvers.
- **Observability Result**: Proved mathematically and empirically that 2D vehicle yaw angle is strictly **unobservable** from 6-axis IMU signals (3-axis accel + 3-axis gyro) without an external heading reference (magnetometer or GNSS velocity vector).
- **Trajectory Dynamics**: Resolved early trajectory non-monotonicity, confirming that un-aided gyro drift accumulation is the primary driver of orientation error.

---

## 3. M044–M049: Controlled Attempts to Fix Turn/Heading Behavior

With error mechanisms localized to turn dynamics and heading drift, milestones M044 through M049 executed controlled intervention attempts.

```
+------------------------------------------------------------------------------------------------------------------+
| Milestone | Candidate Intervention / Scope          | Val Outcome | Locked Test 300s | Verdict & Status            |
+------------------------------------------------------------------------------------------------------------------+
| M044      | Turn SpeedNet Downweighting (R_v x 10)  | Promising   | 574.98 m          | REJECTED (Destroyed Self-Can) |
| M045      | Turn Geometry & Observability Diagnostic| Diagnostic  | 218.93 m          | DIAGNOSTIC ONLY             |
| M046      | Learned Neural Gyro Drift Correction   | Winner F2   | 719.27 m          | REJECTED (Gen Failure)      |
| M047      | Turn NHC Innovation Gating (|w| thresh) | Winner F4   | 808.02 m          | REJECTED (Gen Failure)      |
| M048      | Body vs World EKF State Consistency     | Equivalent  | 218.93 m          | DIAGNOSTIC ONLY             |
| M049      | Intermittent Heading Anchor Feasibility | Oracle      | 497.78 m (20s)    | DIAGNOSTIC ONLY (Info Bound)|
+------------------------------------------------------------------------------------------------------------------+
```

### Detailed Breakdown
- **M044 (Turn Measurement Weighting)**: Attempted to inflate SpeedNet measurement covariance $R_v$ during high yaw-rate turns. Candidate F3 improved validation metrics but exploded locked test 300 s error to **574.98 m** (+162.6%) and 1 km error to **559.34 m** (+81.9%) by destroying EKF geometric self-cancellation.
- **M045 (Turn Geometry Diagnostic)**: Diagnostic audit showing strong turns induce $+3.5\text{ m/s}$ speed bias and $9.86\text{ m/s}$ NHC innovation residuals. Proved counterfactual GT Heading (CF2) reduces 300 s position error by **91.2% to 30.82 m**.
- **M046 (Learned Gyro Drift Correction)**: Trained a neural model to predict turn-dependent gyro drift corrections. Validation winner **F2** degraded locked test 300 s error to **719.27 m** (+228.5%).
- **M047 (Turn NHC Innovation Gating)**: Gated NHC updates during strong turns ($|\omega_y| > 2.0\text{ m/s}$). Validation winner **F4** ($154\text{ m}$ val) severely degraded locked test 300 s error to **808.02 m** and 1 km error to **1291.78 m** (129.16% FPER) by removing lateral damping.
- **M048 (EKF State Consistency)**: Evaluated whether world-frame velocity ($v_x, v_y$) vs body-frame velocity ($v_u, v_v$) state vectors affected filter stability. Proved both formulations are mathematically identical (both achieving exact **218.93 m @ 300 s**) with well-conditioned state covariance ($\kappa(P) < 1000$). Closed representation branch.
- **M049 (Intermittent Heading Anchor Feasibility)**: Oracle information-bound study. Proved an intermittent heading anchor ($\sigma_\psi = 1.0^\circ, \Delta T = 20\text{ s}$) recovers >80% of error, achieving **497.78 m @ 300 s**. Proved maintaining FPER < 10% over 1 km requires $\sigma_\psi \le 5.0^\circ$ at $\Delta T \le 5.0\text{ s}$.

---

## 4. M050–M052: Closing Additional Hypotheses

Milestones M050 through M052 tested deeper representation, kinematic observability, and physical acceleration hypotheses.

### M050 — Learned Body-Frame Velocity Representation
- **Hypothesis**: Predicting full body-frame velocity vectors ($v_{\text{fwd}}, v_{\text{lat}}$) via deep learning provides better EKF motion representation than scalar speed $v_{\text{fwd}}$ alone.
- **Validation Selection**: Candidate **F1** (Body Velocity Network) won validation with an impressive 300 s error of **107.48 m** (vs Control F0's $1248.83\text{ m}$).
- **Locked Test Result**: Candidate **F1** failed to generalize on locked test data, producing a 300 s error of **817.69 m** (+273.7% degradation vs M028's **218.76 m**).
- **Failure Analysis**: F1's learned forward velocity bias aligned fortuitously with validation turns but doubled test forward MAE to $4.59\text{ m/s}$. Furthermore, noisy predicted lateral velocity disrupted EKF non-holonomic constraint (NHC) cross-track damping.
- **Verdict**: **GENERALIZATION FAILURE**. Production unchanged.

### M051 — Zero-Velocity / Kinematic Heading Constraint Study
- **Hypothesis**: Zero-velocity (ZUPT) stationary events and stationary gyro bias updates can bound long-duration yaw drift without external heading references.
- **Mathematical Proof**:
  1. $H_{\text{zupt}}$ matrix has rank 2 ($v_x, v_y$). Heading angle $\psi$ is strictly **unobservable** from zero velocity measurements.
  2. Stationary gyro bias updates observe sensor null offset $b_\omega$, but cannot retroactively repair past heading integration error accumulated during prior dynamic turns.
- **Experimental Result**: Validation winner **F5** ($452.99\text{ m}$ val) degraded locked test 300 s error to **598.34 m** (+379.41 m vs M028).
- **Verdict**: **GENERALIZATION FAILURE**. Production unchanged.

### M052 — Dynamic Centrifugal Acceleration Compensation Study
- **Hypothesis**: Dynamic turn-induced centrifugal acceleration contamination ($a_c = v \cdot \omega_{\text{yaw}}$) distorts longitudinal acceleration inputs $a_{\text{long}}$ during curved braking/turning maneuvers.
- **Axis Audit**: Sensor fusion coordinate convention: $a_{\text{long}} = -(\text{raw\_ay} - \text{grav\_y})$, $\omega_{\text{yaw}} = -\text{gyro\_pitch}$.
- **Diagnostic Empirical Findings**:
  - Straight motion mean $|a_c|$: **$0.1921\text{ m/s}^2$**
  - Turning motion mean $|a_c|$: **$3.7139\text{ m/s}^2$**
  - Braking + turning mean $|a_c|$: **$3.9805\text{ m/s}^2$**
  - Peak turning magnitude $|a_c|$: **$18.9368\text{ m/s}^2$** ($1.93\text{ g}$)
- **Experimental Result**: Direct centrifugal compensation candidate **F1_a0.2** won validation sweep (**488.80 m** vs Control $492.74\text{ m}$), but **catastrophically degraded locked test set** performance to **1040.45 m @ 300 s** (Delta = +821.52 m vs M028's **218.93 m**).
- **Verdict**: **GENERALIZATION FAILURE**. Production unchanged.

---

## 5. Master Comparison Table (M040–M052)

| Milestone | Research Question | Primary Approach | Val 300s (m) | Test 300s (m) | Test 1km (m) | Test FPER (%) | Verdict | Deployed Impact |
|---|---|---|:---:|:---:|:---:|:---:|---|---|
| **M028** | Jerk-gated APM speed damping | Zero-latency IMU jerk gate + APM | 494.80 | **218.93** | **307.46** | **15.81%** | **ACCEPTED** | **LOCKED BASELINE** |
| **M040** | Counterfactual filter audit | GT Speed substitution in EKF | — | 511.62 | 588.20 | 36.95% | AUDIT ONLY | No Pipeline Change |
| **M041** | SIH benchmark compliance | Distance-normalized audit | — | 218.93 | 307.46 | 15.81% | AUDIT ONLY | Compliance Framework |
| **M042** | Failure localization | Gyro yaw drift & curve analysis | — | 218.93 | 307.46 | 15.81% | DIAGNOSTIC | Localized 70–120s Fail |
| **M043** | Heading observability audit | 6-axis IMU yaw observability proof | — | 218.93 | 307.46 | 15.81% | AUDIT ONLY | Yaw Unobservable |
| **M044** | Turn measurement weighting | Inflate SpeedNet $R_v$ during turns | Promising | 574.98 | 559.34 | 41.53% | REJECTED | Self-Can Destroyed |
| **M045** | Turn geometry observability | Motion constraint & GT heading oracle | — | 30.82 | 22.45 | 2.22% | DIAGNOSTIC | GT Yaw -91.2% Drift |
| **M046** | Learned gyro drift net | Neural turn yaw-rate correction | Winner F2 | 719.27 | 358.63 | 51.95% | REJECTED | Gen Failure |
| **M047** | Turn NHC innovation gating | Gate NHC updates during turns | 154.00 | 808.02 | 1291.78 | 58.36% | REJECTED | Lateral Damping Lost |
| **M048** | EKF state consistency | World ($v_x,v_y$) vs Body ($v_u,v_v$) state | 494.80 | 218.93 | 307.46 | 15.81% | DIAGNOSTIC | Math Equivalent |
| **M049** | Intermittent heading oracle | External yaw anchor ($\sigma=1.0^\circ, \Delta T=20\text{s}$) | — | 497.78 | 373.80 | 35.95% | DIAGNOSTIC | Info Bound Proven |
| **M050** | Learned body velocity | Neural body vector ($v_{\text{fwd}}, v_{\text{lat}}$) | 107.48 | 817.69 | 931.30 | 59.05% | REJECTED | Gen Failure |
| **M051** | Zero-velocity heading constraint| ZUPT yaw stability & stationary gyro bias| 452.99 | 598.34 | 598.34 | 43.45% | REJECTED | ZUPT Yaw Unobservable|
| **M052** | Centrifugal accel compensation| Subtracted $a_c = v \cdot \omega_{\text{yaw}}$ from $a_{\text{long}}$ | 488.80 | 1040.45 | 1040.45 | 75.55% | REJECTED | Gen Failure |

---

## 6. Visualizations & Progression Graphs

![Figure 1: 300s Locked-Test Navigation Error Across M040–M052 Hypotheses](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/docs/plots/fig1_m040_m052_300s_progression.png)  
*Caption for Figure 1: Comparison of locked-test 300 s position errors across all M040–M052 hypotheses against the M028 production baseline (218.93 m, green dashed line). Candidates in magenta represent rejected pipeline interventions. Blue/purple bars indicate diagnostic oracle bounds.*

![Figure 2: SIH Benchmark Outage Performance vs. 10% FPER Threshold](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/docs/plots/fig2_sih_compliance_progression.png)  
*Caption for Figure 2: M028 production pipeline error vs. SIH 10% FPER target limits across outage windows. The system comfortably passes at 60 s (27.35 m vs 40.90 m limit) but fails at 120 s, 300 s, and 1 km horizons.*

![Figure 3: Turn Geometry, Gyro Yaw Drift & Geometric Self-Cancellation](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/docs/plots/fig3_turn_geometry_self_cancellation.png)  
*Caption for Figure 3: M042/M045 trajectory error dynamics showing un-aided gyro yaw drift accumulation (-43.68° at 112 s) driving a cross-track error spike at 120 s (426.85 m), followed by curve reversal self-cancellation pulling drift back down to 218.93 m at 300 s.*

![Figure 4: M052 Dynamic Centrifugal Acceleration Contamination](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/docs/plots/fig4_m052_centrifugal_diagnostic.png)  
*Caption for Figure 4: M052 diagnostic measuring centrifugal acceleration magnitude $|a_c| = v \cdot |\omega_{\text{yaw}}|$ across motion regimes, highlighting peak turning acceleration of 18.94 m/s².*

![Figure 5: Validation Selection vs. Unseen Locked Test Set Performance](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/docs/plots/fig5_validation_vs_test_generalization_trap.png)  
*Caption for Figure 5: The Generalization Trap: Comparison of validation 300 s error (blue) versus locked test set 300 s error (red) for M028 baseline and validation winners (M044, M046, M047, M050, M051, M052). Demonstrates why validation wins without locked-test verification lead to false positives.*

---

## 7. What We Learned (Evidence-Based Synthesis)

1. **Scalar Speed Alone Does Not Explain Navigation Failure**: SpeedNet v2 achieves strong speed prediction accuracy, but integrated navigation error is governed by non-linear vector integration over long time horizons.
2. **Heading & Path Geometry Are Intimately Coupled**: Turning maneuvers induce gyro yaw integration errors that rotate the velocity vector, transforming longitudinal motion into severe cross-track position drift.
3. **Pure Kinematics vs. EKF Counterfactuals Differ**: While GT speed in pure kinematic dead-reckoning reduces error, substituting GT speed into the production EKF degrades 300 s navigation (**511.62 m** vs **218.93 m**) due to loss of geometric self-cancellation.
4. **Fixed NHC Is Empirically Mandatory**: Non-holonomic constraints ($v_{\text{lateral}} \approx 0$) act as vital lateral velocity anchors. Relaxing NHC covariance ($R_{\text{nhc}}$) or gating NHC updates during turns destroys lateral damping and explodes position drift (+422% in M026, +269% in M047).
5. **Validation Selection Can Be a Generalization Trap**: Multiple candidates (M044, M046, M047, M050, M051, M052) achieved impressive validation wins (down to $107.48\text{ m}$ in M050) by over-fitting to validation turn geometry, but severely degraded on unseen locked test data.
6. **Neural Corrections Have Failed to Generalize**: Deep neural networks trained to predict body velocity vectors (M050) or turn-dependent gyro drift corrections (M046) failed to generalize across unseen test driving trajectories.
7. **ZUPT Does Not Observe Vehicle Yaw**: Zero-velocity updates ($H_{\text{zupt}}$ rank 2) constrain velocity and accelerometer bias, but provide **zero direct observability** for 2D heading angle $\psi$. Stationary gyro bias updates cannot repair past turn integration errors.
8. **Centrifugal Terms Are Large But Cannot Be Directly Subtracted**: Turn-induced centrifugal acceleration reaches peak magnitudes of $18.94\text{ m/s}^2$ ($1.93\text{ g}$), but directly subtracting $a_c$ from longitudinal IMU acceleration (M052) degrades test navigation performance to $1040.45\text{ m}$.
9. **Remaining Problem Is Coupled Observability**: The remaining dead-reckoning challenge is not a missing scalar speed fix, but an un-aided heading observability limitation during dynamic curved maneuvers.

---

## 8. Current System Status

```
+--------------------------------------------------------------------------------------------------+
|                                    CURRENT SYSTEM STATUS SUMMARY                                 |
+--------------------------------------------------------------------------------------------------+
| Deployed Production Baseline | M028 (SpeedNet v2 + M013 F4 + ZUPT + M019 APM + M028 Jerk Gate)  |
| Locked Benchmark 60s Outage  | 27.35 m  (6.69% FPER / 66.87 m/km)  [SIH COMPLIANT PASS]         |
| Locked Benchmark 120s Outage | 426.85 m (48.80% FPER / 487.96 m/km) [NON-COMPLIANT FAIL]        |
| Locked Benchmark 300s Outage | 218.93 m (15.81% FPER / 158.11 m/km) [NON-COMPLIANT FAIL]        |
| Locked Benchmark 1km Outage  | 307.46 m (30.74% FPER / 307.41 m/km) [NON-COMPLIANT FAIL]        |
| Max SIH-Compliant Envelope   | 491.50 m                                                          |
| Milestones M040–M052 Outcome | 13/13 Milestones Executed. 0 Production Pipeline Regressions.     |
| Production Codebase Status   | 100% LOCKED & UNCHANGED. M028 remains active production model.    |
+--------------------------------------------------------------------------------------------------+
```

---

## 9. Next Research Direction

Based on empirical evidence from M040–M052, the next logical research hypothesis (for future investigation beyond M052) is:

> **Causal Adaptive NHC Measurement Variance Scaling**: Dynamically scaling $R_{\text{nhc}}$ conditioned on causal angular acceleration ($\dot{\omega}_y$) or jerk transients to preserve lateral damping during steady turns while relaxing constraints only during transient entry/exit phases.

*Note: This hypothesis is strictly identified as a candidate for future work. No M053 baseline or pipeline changes have been created.*
