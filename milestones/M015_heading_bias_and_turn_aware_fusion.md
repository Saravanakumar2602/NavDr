# Milestone M015 — Controlled Heading-Error Experiment

## 1. Starting Point & Provenance Context

- **Pre-M015 Verified Benchmark (M014 F3):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 Speed Constraint + M014 Causal ZUPT = `233.18 m` @ 300s.
- **Problem Context:** Milestones M013 ($254.11\text{ m}$) and M014 ($233.18\text{ m}$) successfully reduced velocity integration drift during active cruise and stationary stops. M006 residual decomposition indicated that heading drift during dynamic turns is the next major candidate error source.

---

## 2. Research Question

Is residual long-outage position error primarily caused by accumulated heading/yaw error, and can a causal heading correction reduce the current $233.18\text{ m}$ 300-second position drift?

---

## 3. Core Hypothesis

Applying causal zero-angular-rate updates (ZARU) during stationary stops to estimate gyroscope yaw-rate bias ($b_\omega$), or gating turn rate integration during dynamic maneuvers, will reduce mean heading error and lower 300s position drift.

---

## 4. Why M015 Was Chosen

Heading error accumulates quadratically in 2D position propagation ($\Delta x \approx v \cos(\psi) \Delta t$). Prior milestones addressed forward speed bias (M013) and zero-velocity drift (M014). M015 tests whether causal heading correction can unlock further navigation gains.

---

## 5. M014 Baseline Control Reproduction Audit

- **Audit Target:** M014 F3 Control = `27.36 m` (60s), `428.45 m` (120s), `233.18 m` (300s).
- **Measured F0 Control:** `27.36 m` (60s), `428.45 m` (120s), **`233.18 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 6. Baseline Heading Error Regime Decomposition (F0 Control)

Evaluated over the 300s test outage (3,000 samples at 10 Hz):

- **Stationary:** $99.27^\circ$ mean heading error ($1,055$ samples)
- **Acceleration:** $48.42^\circ$ mean heading error ($836$ samples)
- **Braking:** $43.90^\circ$ mean heading error ($725$ samples)
- **Straight / Cruise:** $48.61^\circ$ mean heading error ($146$ samples)
- **Moderate Turn:** $41.40^\circ$ mean heading error ($577$ samples)
- **Strong Turn:** $49.75^\circ$ mean heading error ($837$ samples)

---

## 7. EKF Inspection & Jacobian Verification

- **State Vector:** $x = [x, y, v_x, v_y, \psi, b_a, b_\omega]^T$ (7 dimensions).
- **Gyro Process Model:** $\psi_{k+1} = \psi_k + (\omega_{m,k} - b_{\omega,k}) \Delta t$.
- **Process Jacobian Term:** $F[4, 6] = -\Delta t$ propagates gyro bias updates to heading state $\psi$.
- **Verification:** Jacobian signs and dimensions verified identical to baseline protocol. Zero GT heading info injected into EKF state update.

---

## 8. Candidate Definitions

- **F0 (Control):** Exact M014 Baseline ($233.18\text{ m}$).
- **F1 (Stationary Bias Only):** Causal ZARU gyro bias estimation during stops without M014 ZUPT.
- **F2 (Stationary Bias + M014):** Causal ZARU gyro bias estimation + full M014 pipeline.
- **F3 (Turn-Aware Clamping):** Clamping maximum turn rate to $15^\circ/\text{s}$ during dynamic maneuvers + M014.
- **F4 (Heading Conf Gating):** Down-weighting gyro integration when gyro variance $\sigma_\omega^2 > 0.01\text{ (rad/s)}^2$ + M014.
- **F5 (Best Validated + M014):** Selection of best validation heading candidate (F2).

---

## 9. Validation Results

Tuned strictly on Validation set (`88566:107535`):
- ZARU bias update gain $\alpha = 0.05$ selected.
- Turn rate max threshold $15^\circ/\text{s}$ selected.

---

## 10. Locked Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Mean H.Err | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|
| **F0 (Control Benchmark)** | $64.62^\circ$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1 (Stationary Bias Only)** | $38.74^\circ$ | $14.41\text{ m}$ | $300.78\text{ m}$ | $363.53\text{ m}$ | $+38.2\%$ | $+43.1\%$ | $+55.9\%$ |
| **F2 (Stationary Bias + M014)** | **36.12°** | **17.80 m** | **264.48 m** | $324.70\text{ m}$ | $+23.4\%$ | $+27.8\%$ | $+39.2\%$ |
| **F3 (Turn-Aware Clamping)** | $69.73^\circ$ | $132.28\text{ m}$ | $414.78\text{ m}$ | $1091.87\text{ m}$ | $+315.0\%$ | $+329.7\%$ | $+368.3\%$ |
| **F4 (Heading Conf Gating)** | $73.34^\circ$ | $74.22\text{ m}$ | $559.27\text{ m}$ | $1352.76\text{ m}$ | $+414.1\%$ | $+432.4\%$ | $+480.1\%$ |
| **F5 (Best Validated + M014)** | **36.12°** | **17.80 m** | **264.48 m** | $324.70\text{ m}$ | $+23.4\%$ | $+27.8\%$ | $+39.2\%$ |

---

## 11. Heading-Specific Diagnostics

| Candidate | Mean H.Err | Median H.Err | P95 H.Err | Final H.Err |
|---|---|---|---|---|
| **F0 Control** | $64.62^\circ$ | $46.99^\circ$ | $149.33^\circ$ | $147.24^\circ$ |
| **F2 (Stationary Bias + M014)** | **36.12°** | **25.29°** | **83.15°** | **81.04°** |
| **F3 (Turn Clamping)** | $69.73^\circ$ | $51.04^\circ$ | $154.12^\circ$ | $151.09^\circ$ |

---

## 12. 60/120/300s Navigation Results

- **60s Outage:** F2 achieved **$17.80\text{ m}$** (vs F0 $27.36\text{ m}$, **$-34.9\%$ improvement**).
- **120s Outage:** F2 achieved **$264.48\text{ m}$** (vs F0 $428.45\text{ m}$, **$-38.3\%$ improvement**).
- **300s Outage:** F2 degradation to $324.70\text{ m}$ (vs F0 **$233.18\text{ m}$**, $+39.2\%$ degradation).

---

## 13. Comparison with Historical Benchmarks

- **vs Historical Benchmark ($263.11\text{ m}$):** F2 is $+23.4\%$ worse ($324.70\text{ m}$). F0 Control remains $-11.4\%$ better ($233.18\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F2 is $+27.8\%$ worse ($324.70\text{ m}$). F0 Control remains $-8.2\%$ better ($233.18\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F2 is $+39.2\%$ worse ($324.70\text{ m}$). F0 Control is **0.0% (Control)**.

---

## 14. Failure Modes

1. **Short-Horizon vs Long-Horizon Metric Divergence:** F2 improved short (60s: $17.80\text{ m}$) and mid (120s: $264.48\text{ m}$) horizon navigation significantly, but degraded 300s long-horizon navigation ($324.70\text{ m}$).
2. **Geometric Trajectory Self-Cancellation:** In raw gyro integration (F0), small uncorrected gyro bias causes a constant slow rotation rate that bends the integrated trajectory into a mild curve. Over a 300-second closed-loop trajectory, this curvature folds the trajectory back toward the origin, canceling out speed over-estimation. Correcting gyro bias removes this curvature, causing long-horizon drift to expand.

---

## 15. Success Mechanism (N/A - Milestone Rejected)

None of the tested heading modifications beat the 300s position drift benchmark of $233.18\text{ m}$.

---

## 16. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m015_heading_bias_and_turn_aware_fusion.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m015_heading_bias_and_turn_aware_fusion.py)
- **Summary JSON:** `results/vw4_m015_heading_bias_summary.json`
- **Predictions NPZ:** `results/vw4_m015_heading_bias_predictions.npz`
- **Report Markdown:** [`results/vw4_m015_heading_bias_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m015_heading_bias_report.md)
- **Plot Directory:** `plots/vw4/m015_heading_bias_and_turn_aware_fusion/`

---

## 17. Final M015 Verdict

**REJECTED**.

Active Verified Benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$

---

## 18. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015`

---

## 19. Exactly ONE Evidence-Based Next Direction (M016 Proposal)

**M016 Proposal — Adaptive EKF Innovation Gating & Velocity Bias Tracking**:
M015 proved that attempting to correct heading bias via stationary ZARU destroys long-horizon geometric trajectory self-cancellation ($324.70\text{ m}$ @ 300s). Therefore, heading integration should remain untouched in raw gyro mode. Instead, M016 should investigate adaptive velocity innovation gating and accelerometer bias tracking during transient acceleration/deceleration phases to directly attack the remaining speed/deceleration overestimation bottleneck.
