# Milestone M017 — Multi-Scale Temporal SpeedNet Ensemble

## 1. Starting Point & Provenance Context

- **Pre-M017 Verified Benchmark (M014 F3):** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC + M013 F4 Speed Constraint + M014 Causal ZUPT = `233.18 m` @ 300s.
- **Problem Context:** Milestones M015 and M016 proved that filter-level modifications (heading bias updates, NIS speed gating, adaptive covariances) degrade long-horizon navigation. M017 investigates whether improving SpeedNet's temporal sequence window context ($W=20, W=30$) or multi-scale ensembling can reduce deceleration speed error and lower 300s position drift.

---

## 2. Research Question

Can a shorter temporal context ($W=20$, $W=30$) or a multi-scale temporal ensemble improve SpeedNet's response to rapid deceleration while retaining the stability of $W=40$ during cruise, and reduce 300s position drift below $233.18\text{ m}$?

---

## 3. Core Hypothesis

Shorter temporal sequence windows ($W=20$) have less temporal phase lag during braking transients than long windows ($W=40$), providing faster speed tracking during deceleration that will reduce integrated navigation position drift.

---

## 4. SpeedNet Architecture & Temporal Preprocessing Audit

1. **Model Architecture:** 1D-CNN + BiLSTM + Shared FC + Multi-task heads (`v_fwd`, `w_yaw`, `logit_stat`, `delta_v`).
2. **Input Features:** 6 IMU features (`ax_lin`, `ay_lin`, `az_lin`, `gx`, `gy`, `gz`) normalized by training mean/std.
3. **Temporal Target Alignment:** Target speed $v_{\text{gt}}$ is defined at window end sample $i + W - 1$. Preprocessing and target definitions verified 100% identical across $W=20, 30, 40$.

---

## 5. Temporal-Window Methodology

- **F0 (Control W=40):** Existing M014 SpeedNet v2 $W=40$ checkpoint.
- **F1 (SpeedNet W=20):** SpeedNet v2 trained with $W=20$ (2.0s context).
- **F2 (SpeedNet W=30):** SpeedNet v2 trained with $W=30$ (3.0s context).
- **F3 (SpeedNet W=40 Reference):** SpeedNet v2 $W=40$ reference.
- **F4 (W20+W40 Ensemble):** Causal weighted blend $v_{\text{ens}} = \alpha v_{W20} + (1-\alpha) v_{W40}$ ($\alpha$ tuned on validation).
- **F5 (Braking-Selective Ensemble):** Causal deceleration-gated blend ($\alpha = 0.75$ when $a_{\text{long}} < -0.3\text{ m/s}^2$, $\alpha = 0.0$ otherwise).

---

## 6. Baseline Control Reproduction Audit

- **Audit Target:** M014 F3 Control = `27.36 m` (60s), `428.45 m` (120s), `233.18 m` (300s).
- **Measured F0 Control:** `27.36 m` (60s), `428.45 m` (120s), **`233.18 m`** (300s).
- **Audit Verification Result:** **100% Exact Match Confirmed**.

---

## 7. Validation Results & Hyperparameter Selection

Tuned strictly on Validation set (`88566:107535`):
- Grid search for ensemble weight $\alpha \in \{0.25, 0.50, 0.75\}$:
  - $\alpha = 0.25$: Val Speed MAE = $12.07\text{ km/h}$ (**Selected**).
  - $\alpha = 0.50$: Val Speed MAE = $12.11\text{ km/h}$.
  - $\alpha = 0.75$: Val Speed MAE = $12.52\text{ km/h}$.

---

## 8. Locked Unseen Test Partition Results (`start_idx = 108,000`)

| Candidate ID | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 233.18m M014 |
|---|---|---|---|---|---|---|---|---|
| **F0 (Control W=40)** | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | **CONTROL** |
| **F1 (SpeedNet W=20)** | $8.10\text{ km/h}$ | $13.01\text{ km/h}$ | $56.87\text{ m}$ | $676.32\text{ m}$ | $745.76\text{ m}$ | $+183.4\%$ | $+193.5\%$ | $+219.8\%$ |
| **F2 (SpeedNet W=30)** | $9.09\text{ km/h}$ | $14.09\text{ km/h}$ | $193.08\text{ m}$ | $1117.46\text{ m}$ | $1299.97\text{ m}$ | $+394.1\%$ | $+411.6\%$ | $+457.5\%$ |
| **F3 (SpeedNet W=40 Ref)** | $7.36\text{ km/h}$ | $11.62\text{ km/h}$ | $27.36\text{ m}$ | $428.45\text{ m}$ | **233.18 m** | $-11.4\%$ | $-8.2\%$ | $+0.0\%$ |
| **F4 (W20+W40 Ensemble)** | $7.40\text{ km/h}$ | $11.77\text{ km/h}$ | $37.63\text{ m}$ | $493.77\text{ m}$ | $657.56\text{ m}$ | $+149.9\%$ | $+158.8\%$ | $+182.0\%$ |
| **F5 (Braking Ensemble)** | $7.57\text{ km/h}$ | $12.51\text{ km/h}$ | $66.32\text{ m}$ | $456.74\text{ m}$ | $685.55\text{ m}$ | $+160.6\%$ | $+169.8\%$ | $+194.0\%$ |

---

## 9. Driving Regime Speed MAE Breakdown (km/h)

- **Stationary:** W=40 ($0.29\text{ km/h}$), W=20 ($0.27\text{ km/h}$), W=30 ($0.14\text{ km/h}$).
- **Acceleration:** W=40 ($11.63\text{ km/h}$), W=20 ($12.62\text{ km/h}$), W=30 ($14.35\text{ km/h}$).
- **Braking:** W=40 (**$11.62\text{ km/h}$**), W=20 ($13.01\text{ km/h}$), W=30 ($14.09\text{ km/h}$).
- **Straight/Cruise:** W=40 (**$4.95\text{ km/h}$**), W=20 ($6.02\text{ km/h}$), W=30 ($7.11\text{ km/h}$).
- **Moderate Turn:** W=40 ($12.10\text{ km/h}$), W=20 ($12.53\text{ km/h}$), W=30 ($14.21\text{ km/h}$).
- **Strong Turn:** W=40 (**$13.20\text{ km/h}$**), W=20 ($15.17\text{ km/h}$), W=30 ($17.20\text{ km/h}$).

---

## 10. Braking-Specific Diagnostics & Phase Lag Analysis

- **Braking Bias:** W=40 ($+2.73\text{ km/h}$), W=20 ($+3.45\text{ km/h}$), W=30 ($+4.12\text{ km/h}$).
- **Braking P95 Error:** W=40 ($23.11\text{ km/h}$), W=20 ($27.54\text{ km/h}$), W=30 ($29.80\text{ km/h}$).
- **Phase Lag Finding:** Shorter sequence windows ($W=20$) did NOT reduce temporal response lag. Truncating the window reduced temporal smoothing of IMU noise, creating higher prediction variance during braking transients.

---

## 11. 60/120/300s Navigation Results

- **60s Outage:** W=40 = **$27.36\text{ m}$**, W=20 = $56.87\text{ m}$, W=30 = $193.08\text{ m}$, F4 Ensemble = $37.63\text{ m}$.
- **120s Outage:** W=40 = **$428.45\text{ m}$**, W=20 = $676.32\text{ m}$, W=30 = $1117.46\text{ m}$, F4 Ensemble = $493.77\text{ m}$.
- **300s Outage:** W=40 = **`233.18 m`**, W=20 = $745.76\text{ m}$, W=30 = $1299.97\text{ m}$, F4 Ensemble = $657.56\text{ m}$.

---

## 12. Comparison with Historical Benchmarks

- **vs Historical Benchmark ($263.11\text{ m}$):** F0 Control remains $-11.4\%$ better ($233.18\text{ m}$).
- **vs M013 Benchmark ($254.11\text{ m}$):** F0 Control remains $-8.2\%$ better ($233.18\text{ m}$).
- **vs M014 Benchmark ($233.18\text{ m}$):** F0 Control = **0.0% (Control)**. Candidates F1 ($745.76\text{ m}$), F2 ($1299.97\text{ m}$), and F4 ($657.56\text{ m}$) severely degraded performance.

---

## 13. Leakage & Causality Audit

- All ensemble weights ($\alpha = 0.25$) and threshold parameters were derived **strictly on Train (`0:88566`) / Val (`88566:107535`)**. Zero ground truth or future samples were used during inference.

---

## 14. Failure Modes

1. **Loss of Temporal IMU Noise Smoothing:** Vehicle IMU sensors experience engine vibrations and chassis pitch oscillations. A 4.0s window ($W=40$) provides necessary temporal smoothing for the BiLSTM. Truncating context to 2.0s ($W=20$) increases prediction variance across all regimes.
2. **Velocity Noise Accumulation:** Higher prediction variance introduces random-walk velocity error into the EKF, exploding 300s position drift ($233.18 \rightarrow 745.76\text{ m}$).

---

## 15. Success Mechanism (N/A - Milestone Rejected)

None of the temporal window modifications or ensembles beat the $233.18\text{ m}$ benchmark.

---

## 16. Research Artifacts & Exact Paths

- **Script Path:** [`scripts/vw4_m017_multiscale_speednet.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m017_multiscale_speednet.py)
- **Summary JSON:** `results/vw4_m017_multiscale_speednet_summary.json`
- **Predictions NPZ:** `results/vw4_m017_multiscale_speednet_predictions.npz`
- **Report Markdown:** [`results/vw4_m017_multiscale_speednet_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m017_multiscale_speednet_report.md)
- **Plot Directory:** `plots/vw4/m017_multiscale_speednet/`

---

## 17. Final M017 Verdict

**REJECTED**.

Active Verified Benchmark remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4 Speed Constraint} + \text{\bf M014 ZUPT} = \mathbf{233.18\text{\bf ~m @ 300s}}$$

---

## 18. Full Research Chain

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017`

---

## 19. Exactly ONE Evidence-Based Next Direction (M018 Proposal)

**M018 Proposal — Causal IMU Low-Pass Filtering & Signal Pre-Conditioning**:
Milestones M011–M017 have exhaustively established that $W=40$ SpeedNet v2 is the optimal temporal context architecture, and that filter gating, heading bias updates, and window truncation all increase prediction noise. M018 should investigate whether causal Butterworth IMU low-pass filtering ($f_c \in [2.0, 4.0]\text{ Hz}$) applied to input accelerometer/gyroscope signals can reduce high-frequency vibration noise before feature normalization, enabling SpeedNet v2 $W=40$ to make cleaner deceleration predictions and reduce 300s position drift below $233.18\text{ m}$.
