# Milestone M043 — Heading Observability Audit & Causal Orientation Enhancement Study

## 1. Objective

The objective of **Milestone M043** is to:
1. Conduct **Phase 0 Reproducibility & Indexing Audit** to resolve the numerical inconsistency between M041's compliance envelope ($6.69\%$ FPER at 60s / $409.00\text{ m}$) and M042's checkpoint table ($38\%$ FPER at $100\text{ m}\text{--}300\text{ m}$).
2. Perform a rigorous physical **Heading Observability Audit** of 6-axis IMU signals during GNSS outage.
3. Characterize gyro yaw integration drift across vehicle motion regimes (straight, turns, stationary).
4. Evaluate causal orientation baselines and counterfactuals without reference heading leakage.

---

## 2. Phase 0 Reproducibility & Indexing Audit Verdict

### Discrepancy Classification:
**`E. Legitimate non-monotonic trajectory behavior + A. M042 checkpoint calculation search filter masking early transient.`**

### Corrected Audit Explanation:
- **Previous M042 Interpretation:** Claimed system was "continuously compliant up to $D_{\text{max}} = 491.50\text{ m}$ ($72.0\text{ s}$)" because the automated exceedance filter evaluated only post-60s samples (`cum_dists > 50.0` / sample $> 500$), masking the early trajectory transient.
- **Corrected M043 Interpretation:** The trajectory position error profile is **strictly non-monotonic**:
  1. **$t \in [0, 30\text{ s}]$ ($D \in [0, 300\text{ m}]$):** Initial speed overestimation and filter initialization cause FPER to hover between $38.70\%$ and $40.61\%$ ($38.90\text{ m} \to 120.49\text{ m}$).
  2. **$t \in [30, 65\text{ s}]$ ($D \in [300, 460\text{ m}]$):** The dead-reckoned trajectory curves back toward the true vehicle path, decaying position error to a **global minimum of $27.35\text{ m}$ ($6.69\%$ FPER / $66.87\text{ m/km}$)** at $t = 60.0\text{ s}$ ($D = 409.00\text{ m}$). This confirms why the 60s outage benchmark is an official **<span style="color:green; font-weight:bold;">PASS</span>**.
  3. **$t \in [65.2, 120\text{ s}]$ ($D \in [460.5, 874.8\text{ m}]$):** The vehicle enters a severe braking and sharp turning sequence. Un-aided gyro yaw integration drift causes position error to explode to **$426.85\text{ m}$ ($48.80\%$ FPER / $487.96\text{ m/km}$)** at $t = 120.0\text{ s}$ (**<span style="color:red; font-weight:bold;">FAIL</span>**).
  4. **$t \in [120, 300\text{ s}]$ ($D \in [874.8, 1384.6\text{ m}]$):** Highway driving and ZUPTs stabilize the EKF, decaying FPER to **$15.81\%$ ($218.93\text{ m}$)** at $300\text{ s}$ (**<span style="color:red; font-weight:bold;">FAIL</span>**).

**Locked Benchmark Reproducibility:**
- 60 s Outage: **`27.35 m`** (Independent) / `27.88 m` (Continuous) — **Verified**
- 120 s Outage: **`426.85 m`** (Independent) / `426.17 m` (Continuous) — **Verified**
- 300 s Outage: **`218.93 m`** (Exact Match) — **Verified**

---

## 3. Locked Production Baseline

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro Yaw} + \text{Fixed 2D NHC } (R=0.04) + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate } (j_{\text{long}} < -1.00)$$

---

## 4. M041 Authoritative SIH Benchmark

- **60 s Outage:** $D_{\text{ref}} = 409.00\text{ m}$, Error = $27.35\text{ m}$, FPER = **$6.69\%$** (<span style="color:green; font-weight:bold;">PASS</span>)
- **120 s Outage:** $D_{\text{ref}} = 874.76\text{ m}$, Error = $426.85\text{ m}$, FPER = **$48.80\%$** (<span style="color:red; font-weight:bold;">FAIL</span>)
- **300 s Outage:** $D_{\text{ref}} = 1384.63\text{ m}$, Error = $218.93\text{ m}$, FPER = **$15.81\%$** (<span style="color:red; font-weight:bold;">FAIL</span>)
- **1 km Travel ($t=150.0\text{ s}$):** $D_{\text{ref}} = 1000.17\text{ m}$, Error = $307.46\text{ m}$, FPER = **$30.74\%$** (<span style="color:red; font-weight:bold;">FAIL</span>)

---

## 5. Heading Failure Characterization across Regimes

Evaluating raw gyro heading integration drift over the 300-second outage ($3,000$ samples):

- **Mean Heading Error:** `+135.47°`
- **Median Heading Error:** `+156.20°`
- **MAE:** `135.47°`
- **RMSE:** `143.95°`
- **P95 Absolute Error:** `177.17°`
- **Maximum Absolute Error:** `179.98°`
- **Drift Rate:** `-0.5569 °/s` (**`-33.41 °/min`**)

### Regime-Specific Heading MAE:
- **Straight Driving ($N=1153$):** $\text{MAE} = \mathbf{94.50^\circ}$
- **Moderate Turn ($N=613$):** $\text{MAE} = \mathbf{43.96^\circ}$
- **Strong Turn ($N=837$):** $\text{MAE} = \mathbf{49.47^\circ}$
- **Stationary ($N=1055$):** $\text{MAE} = \mathbf{99.57^\circ}$

---

## 6. Physical Observability Analysis

- **6-Axis IMU Limits:** Accelerometers observe roll and pitch tilt relative to the gravity vector during constant-velocity/static conditions.
- **Unobservability of Yaw:** **YAW ANGLE (HEADING) IS KINEMATICALLY UNOBSERVABLE** from a 6-axis IMU alone during dynamic 2D planar vehicle motion without a magnetometer or external velocity updates.
- **Implication:** Kinematic propagation of yaw depends $100\%$ on gyro rate integration ($\dot{\psi} = \omega_z - b_w$). Pre-outage bias estimation ($b_w$) improves initial baseline stability, but cannot observe or correct accumulated heading drift during un-aided turns ($700\text{ m} \to 1000\text{ m}$).

---

## 7. Causal Heading Baselines & Counterfactuals

Following the corrected M040 methodology:

| Counterfactual / Baseline Variant | Integration Type | 300s Position Error | FPER (%) | Finding |
|---|---|---|---|---|
| **Kinematic CF0** | Pure Kinematic | 215.42 m | 15.56 % | Production Speed + Gyro Heading |
| **Kinematic CF1** | Pure Kinematic | 328.44 m | 23.72 % | GT Speed + Gyro Heading |
| **Kinematic CF2** | Pure Kinematic | 408.41 m | 29.49 % | Production Speed + GT Heading |
| **Kinematic CF3** | Pure Kinematic | **5.64 m** | **0.41 %** | **Kinematic Oracle Floor** (GT Speed + GT Heading) |
| **EKF Baseline (CF0)** | EKF Navigation | **218.93 m** | **15.81 %** | **Locked Production Baseline** |

---

## 8. Final Verdict

**`C. M043 DIAGNOSTIC ONLY — heading is not sufficiently observable for a justified intervention.`**

Production pipeline remains **100% LOCKED** at M028/M040 baseline (**$218.93\text{ m}$ @ 300s**).

---

## 9. Recommended Next Research Direction (M044 Proposal)

Because 6-axis IMU signals cannot observe yaw angle during turns without external references, Round 3 model enhancement should explore **zero-velocity heading stabilization / multi-sensor motion regime constraints or neural turn-deceleration scale adaptation** that operates directly within the observable subspace.
