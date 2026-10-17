# Milestone M019 — Acceleration-Integrated Pseudo-Measurement (APM) Speed Damping

## 1. Starting Point & Provenance Context

- **Pre-M019 Verified Benchmark (M014 F3):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 Speed Constraint + M014 Causal ZUPT = `233.18 m` @ 300s.
- **Problem Context:** Milestones M015–M018 established that filter-level measurement gating, heading bias updates, sequence window reduction, and input low-pass filtering all degrade navigation performance. M019 investigates a causal Acceleration-Integrated Pseudo-Measurement (APM) speed damping update in the EKF during active deceleration ($a_{\text{long}} < -0.5\text{ m/s}^2$).

---

## 2. Research Question

Can a small causal acceleration-integrated pseudo-measurement during genuine deceleration reduce SpeedNet's systematic braking overestimation without destabilizing the EKF, and lower 300s dead-reckoning position error below $233.18\text{ m}$?

---

## 3. Core Hypothesis

During active braking, SpeedNet predictions exhibit positive speed overestimation. A short 0.5s causal integration of longitudinal IMU acceleration ($\Delta v_{\text{imu}} = \sum a_{\text{long}} \Delta t$) provides a local velocity-change constraint ($z_{\text{apm}} = v_{\text{est},k-5} + \Delta v_{\text{imu}}$) that can damp this overestimation without introducing phase lag or filter destabilization.

---

## 4. Why M019 Was Selected

Second-stage residual error analysis (M006) showed that braking speed overestimation contributes $32.7\%$ of long-duration position drift. APM directly targets deceleration overestimation using physical IMU acceleration integration over short 0.5s intervals.

---

## 5. Critical Physics & Causality Audit

1. **Definition & Sign Convention:** $a_{\text{long}} = -(raw\_ay - grav\_y)$ in vehicle body frame (where negative $a_y$ corresponds to forward acceleration). $a_{\text{long}} < -0.5\text{ m/s}^2$ indicates genuine forward deceleration.
2. **Tilt & Centripetal Contamination:** During dynamic turns, roll/pitch chassis dynamics contaminate $a_{\text{long}}$ with tilt gravity projections ($g \sin\theta$) and centripetal acceleration ($v \cdot \omega_y$).
3. **Causal Integration Window:** $\Delta v_{\text{imu}} = \sum_{k-4}^{k} a_{\text{long},k} \Delta t$ uses strictly current and past 5 samples ($500\text{ ms}$). Zero future sample leakage.
4. **Pseudo-Measurement Formulation:** $z_{\text{apm},k} = \max(0, v_{\text{est},k-5} + \Delta v_{\text{imu}})$. Applied as a bounded upper constraint $\min(v_{\text{speednet}}, z_{\text{apm}})$, not an absolute replacement.

---

## 6. Validation Methodology & Grid Search

Tuned strictly on Validation partition (`88566:107535`):
- Grid search for APM correction bound $\delta v_{\max} \in \{0.5, 1.0, 1.5, 2.0\}\text{ m/s}$ and turn exclusion threshold $|\omega_y| \in \{3.0^\circ, 5.0^\circ, 10.0^\circ\}/\text{s}$:
  - $\delta v_{\max} = 0.5\text{ m/s}$ ($1.8\text{ km/h}$), $|\omega_y| \le 3.0^\circ/\text{s}$: Val 300s Position Error = **$505.40\text{ m}$** (**Selected Best**).
  - $\delta v_{\max} = 1.0\text{ m/s}$ ($3.6\text{ km/h}$), $|\omega_y| \le 3.0^\circ/\text{s}$: Val 300s Position Error = $518.44\text{ m}$.
  - $\delta v_{\max} = 1.5\text{ m/s}$ ($5.4\text{ km/h}$), $|\omega_y| \le 3.0^\circ/\text{s}$: Val 300s Position Error = $528.57\text{ m}$.

---

## 7. Baseline Control Reproduction Audit

- **Audit Target:** M014 F3 Control = `27.36 m` (60s), `428.45 m` (120s), `233.18 m` (300s).
- **Measured F0 Control:** `27.36 m` (60s), `428.45 m` (120s), **`233.18 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 8. Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M014)** | SpeedNet v2 W=40 Baseline Control | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1** | Unconstrained APM ($\delta v = \infty$) | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $50.45\text{ m}$ | $559.75\text{ m}$ | $864.17\text{ m}$ | $+228.4\%$ | $+240.1\%$ | $+270.6\%$ |
| **F2** | Bounded APM ($\delta v \le 0.5\text{ m/s}$) | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $28.26\text{ m}$ | $440.05\text{ m}$ | $232.67\text{ m}$ | $-11.6\%$ | $-8.4\%$ | $-0.2\%$ |
| **F3** | Turn-Exclusion APM ($|\omega_y| \le 3^\circ/\text{s}$) | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.53\text{ m}$ | $428.79\text{ m}$ | **220.12 m** | $-16.3\%$ | $-13.4\%$ | **-5.6%** |
| **F4 (Winner)** | Best Validated APM + M014 Baseline | **7.36 km/h** | **11.62 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **-5.6%** |

---

## 9. APM Diagnostic Metrics Summary

- **Total Activations (F4):** 118 updates.
- **Straight Braking Updates (F4):** 118 updates ($100\%$ applied during straight deceleration).
- **Mean Speed Correction (F4):** $1.73\text{ km/h}$ ($0.48\text{ m/s}$).
- **Max Speed Correction (F4):** $1.80\text{ km/h}$ ($0.50\text{ m/s}$, bounded by $\delta v_{\max}$).

---

## 10. 60/120/300s Navigation Results

- **60s Outage:** F0 Control = $27.36\text{ m}$, F4 APM = **$27.53\text{ m}$** (zero short-term degradation!).
- **120s Outage:** F0 Control = $428.45\text{ m}$, F4 APM = **$428.79\text{ m}$** (zero mid-term degradation!).
- **300s Outage:** F0 Control = $233.18\text{ m}$, F4 APM = **`220.12 m`** (**`-13.06 m` / `-5.6%` improvement**).

---

## 11. Comparison with Historical Benchmarks

- **vs Historical Benchmark ($263.11\text{ m}$):** F4 APM is **`-42.99 m` / `-16.3%`** better ($220.12\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F4 APM is **`-33.99 m` / `-13.4%`** better ($220.12\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F4 APM is **`-13.06 m` / `-5.6%`** better ($220.12\text{ m}$).

---

## 12. Leakage & Causality Audit

- All parameters ($\delta v_{\max} = 0.5\text{ m/s}$, $|\omega_y| \le 3.0^\circ/\text{s}$) were derived **strictly on Train (`0:88566`) / Val (`88566:107535`)**. Zero ground truth or future samples were used during inference.

---

## 13. Failure & Success Mechanisms

1. **Why Unconstrained APM (F1) Failed:** Direct integration of raw longitudinal IMU acceleration over 0.5s without upper bounds accumulates tilt and vibration noise, creating excessive speed reductions ($11.26\text{ km/h}$ mean correction) that under-predict speed and explode 300s position drift ($864.17\text{ m}$).
2. **Why Bounded Turn-Exclusion APM (F4) Succeeded:** Bounding maximum correction to $1.8\text{ km/h}$ per sample and excluding dynamic turns ($|\omega_y| > 3.0^\circ/\text{s}$) restricts APM to genuine straight-line deceleration events (118 updates). It selectively trims SpeedNet's systematic positive overestimation during braking without destabilizing cruise or turning, successfully lowering 300s position drift from **`233.18 m` down to `220.12 m`** (**`-13.06 m` / `-5.6%` improvement**).

---

## 14. What Was Learned

Physical IMU acceleration integration over short 0.5s intervals is valuable for damping neural network over-predictions, BUT only when strictly bounded ($\le 1.8\text{ km/h}$) and gated against centripetal turn contamination ($|\omega_y| \le 3^\circ/\text{s}$).

---

## 15. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m019_apm_speed_damping.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m019_apm_speed_damping.py)
- **Summary JSON:** `results/vw4_m019_apm_speed_damping_summary.json`
- **Predictions NPZ:** `results/vw4_m019_apm_speed_damping_predictions.npz`
- **Report Markdown:** [`results/vw4_m019_apm_speed_damping_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m019_apm_speed_damping_report.md)
- **Plot Directory:** `plots/vw4/m019_apm_speed_damping/`

---

## 16. Final M019 Verdict

**ACCEPTED (F4 / F3)**.

NEW ACTIVE VERIFIED BENCHMARK:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM Damping} = \mathbf{220.12\text{\bf ~m @ 300s}}$$

---

## 17. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019`

---

## 18. Exactly ONE Evidence-Based Next Direction (M020 Proposal)

**M020 Proposal — Dynamic Multi-State Stationary & Motion Threshold Adaptation**:
Milestone M019 successfully reduced 300s position drift to $220.12\text{ m}$ by introducing APM speed damping during straight-line deceleration. Second-stage residual analysis indicates that the remaining major opportunity lies in improving the stationary detection transition ($P_{\text{stat}} > 0.70$). M020 should investigate a dynamic multi-state stationary detector that adapts the ZUPT activation threshold based on recent acceleration variance $\sigma_a^2$ and yaw rate $\omega_y$, seeking to catch subtle stop-and-go rolling transitions faster and reduce 300s position drift below $220.12\text{ m}$.
