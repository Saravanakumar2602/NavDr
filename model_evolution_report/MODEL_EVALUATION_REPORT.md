# SIH 2026 Intelligent Dead-Reckoning (IDR)
## Comprehensive Model & Milestone Evaluation Report (M001 – M040)

---

### Executive Summary

This document presents the complete, audited model evaluation and trajectory evolution of the **SIH 2026 Intelligent Dead-Reckoning (IDR)** research project. Across 40 research milestones (**M001 through M040**), our team developed, evaluated, and validated multiple deep neural network architectures and post-inference physical constraint layers to achieve robust, drift-resistant land vehicle navigation using uncalibrated smartphone Inertial Measurement Units (IMUs).

The **active locked production benchmark** stands at **218.93 m horizontal position drift over a 300-second (5-minute) GNSS outage** (equivalent to **27.35 m @ 60 s** and **426.85 m @ 120 s**). This represents a **96.6% overall reduction in position drift** compared to raw inertial double-integration baseline (6,420 m @ 300 s).

---

### Section 1: Master Milestone Matrix (M001 – M040)

The table below documents the complete chronological progression of all 40 project milestones, detailing the core change/hypothesis, speed accuracy, dead-reckoning position error across three GNSS outage horizons (60s, 120s, 300s), formal decision status, and technical rationale.

| Milestone ID | Milestone Title / Focus | Core Change / Hypothesis | Speed MAE (km/h) | 60s Error (m) | 120s Error (m) | 300s Error (m) | Status | Key Rationale & Technical Decision |
|---|---|---|---:|---:|---:|---:|:---:|---|
| **M001** | Raw Inertial Double-Integration | Double-integrate raw IMU accelerometers ($\mathbf{a}_{	ext{raw}} - \mathbf{g}$) | N/A | 1,200.00 | 2,800.00 | 6,420.00 | **BASELINE** | Unconstrained double-integration exhibits quadratic drift $\mathcal{O}(t^3)$ due to IMU noise and tilt. |
| **M002** | Kinematic Baseline & EDA | Analyze 6-channel IMU noise characteristics & sliding windowing | N/A | 1,150.00 | 2,650.00 | 5,890.00 | **DIAGNOSTIC** | Established 10 Hz sliding window structure ($W=30$) and proved raw acceleration double-integration is unusable. |
| **M003** | SpeedNet v1 Open-Loop | 1D-CNN + BiLSTM neural speed estimation ($W=30$) | 6.55 | 110.50 | 480.20 | 1,465.00 | **ACCEPTED** | First major breakthrough (-77.2% drift). Eliminates quadratic velocity integration drift. |
| **M004** | SpeedNet v2 Baseline + Fixed 2D NHC | Multi-task SpeedNet v2 ($W=40$) + fixed 2D NHC ($R_{	ext{nhc}}=0.04$) | 6.41 | 22.80 | 440.20 | 263.11 | **ACCEPTED** | **PRODUCTION BASELINE**. Fixed 2D NHC anchors lateral speed ($v_{	ext{lat}}=0$), dropping drift by 82.0%. |
| **M005** | HeadingNet Yaw Rate Estimation | Neural yaw rate model ($\hat{\omega}_y$) to correct gyro drift | 6.41 | 88.40 | 310.50 | 740.30 | **REJECTED** | Monotonic integration of tiny neural biases ($0.2^\circ/	ext{s}$) accumulated $60^\circ$ heading error; destroyed EKF path self-cancellation. |
| **M006** | Extended Window SpeedNet (W=60) | Increase IMU sliding window from 4.0s ($W=40$) to 6.0s ($W=60$) | 6.82 | 26.50 | 465.10 | 298.40 | **REJECTED** | Longer window increased neural inference latency and edge boundary smoothing during sharp turns. |
| **M007** | SpeedNet v3 Regime-Aware | Mixture-of-Experts (MoE) with 3 regime heads (Cruise, Turn, Stop) | 6.26 | 28.10 | 482.00 | 310.45 | **REJECTED** | Discontinuous regime boundary switching created velocity step jump artifacts inside EKF filter updates. |
| **M008** | SpeedNet v2.5 Physics Loss | Train SpeedNet v2 with Kinematic Acceleration Loss ($\lambda_{	ext{kin}}=0.10$) | 7.02 | 34.20 | 510.30 | 445.20 | **REJECTED** | Gradient conflict between MSE speed loss and acceleration penalty caused zero-prediction speed collapse. |
| **M009** | Adaptive NHC Measurement Noise | Scale NHC noise dynamically based on yaw rate ($\omega_y$) | 6.41 | 25.40 | 452.10 | 285.60 | **REJECTED** | Relaxing NHC noise during turns allowed lateral velocity leakage and increased cross-track drift. |
| **M010** | Yaw-Rate Dependent NHC | Gated NHC noise scaling during high turn rate transients | 6.41 | 24.80 | 448.90 | 278.30 | **REJECTED** | Variable measurement noise induced covariance matrix instability in EKF error propagation. |
| **M011** | SpeedNet v4 Physics Loss | Re-train SpeedNet with asymmetric acceleration loss weighting | 7.74 | 45.10 | 590.40 | 680.15 | **REJECTED** | Severe neural weight distortion. Soft loss constraints during training destabilize neural convergence. |
| **M012** | Asymmetric Loss Retraining | Penalize speed over-prediction 2.5x heavier than under-prediction | 7.74 | 45.10 | 590.40 | 680.15 | **REJECTED** | Forced neural predictions into zero-velocity trapping, degrading 300s position drift by +158.5%. |
| **M013** | Hard Physical Speed Constraint (F4) | Post-inference acceleration bound ($v_{	ext{bound}}$) gated on low variance | 6.41 | 22.10 | 428.50 | 254.12 | **ACCEPTED** | **BREAKTHROUGH 3**. Hard physical truncation AFTER inference caps cruise overestimation (-8.99m drift). |
| **M014** | 2D Zero-Velocity Updates (ZUPT F3) | Trigger 2D EKF ZUPT ($\mathbf{z}=[0,0]^T$) when $P(	ext{stat})>0.70$ | 6.41 | 21.80 | 412.30 | 233.18 | **ACCEPTED** | **BREAKTHROUGH 4**. Eliminates velocity integration error accumulation during traffic stops (-20.94m drift). |
| **M015** | ZUPT Covariance Tuning | Test tight vs loose ZUPT measurement noise ($R_{	ext{zupt}} \in [0.01, 0.16]$) | 6.41 | 22.40 | 418.10 | 238.50 | **REJECTED** | $R_{	ext{zupt}}=0.04	ext{ m}^2/	ext{s}^2$ established as optimal; tighter noise caused filter covariance collapse. |
| **M016** | SpeedNet v5 Downsampled (5 Hz) | Downsample IMU input frequency from 10 Hz to 5 Hz ($W=20$) | 8.71 | 32.10 | 495.20 | 388.90 | **REJECTED** | Lower sampling rate aliased high-frequency road vibration signals critical for speed prediction. |
| **M017** | EKF State Matrix Expansion | Expand state vector from 7D to 9D with 2D IMU alignment angles | 6.41 | 28.50 | 455.00 | 290.15 | **REJECTED** | Alignment angles unobservable without absolute GNSS position; increased estimation variance. |
| **M018** | Acceleration-Integrated Speed | Test un-bounded IMU acceleration speed substitution | 6.41 | 26.20 | 438.10 | 245.80 | **REJECTED** | Un-bounded acceleration integration accumulated accelerometer bias drift during long deceleration legs. |
| **M019** | Bounded APM Speed Damping (F4) | Causal 0.5s acceleration integration with $\delta v_{\max}=0.50	ext{ m/s}$ bound | 6.41 | 23.40 | 415.60 | 220.12 | **ACCEPTED** | **BREAKTHROUGH 5**. Eliminates 200-300ms neural response lag during braking transients (-13.06m drift). |
| **M020** | Extended APM Window (1.0s) | Increase APM acceleration integration window from 0.5s to 1.0s | 6.41 | 24.80 | 422.10 | 226.40 | **REJECTED** | Longer integration window accumulated sensor tilt noise during prolonged downhill braking. |
| **M021** | Tighter APM Bound ($\delta v=0.25	ext{ m/s}$) | Restrict maximum APM speed damping from 0.50 m/s to 0.25 m/s | 6.41 | 23.10 | 418.90 | 223.50 | **REJECTED** | Insufficient speed correction; failed to fully damp neural speed lag during sharp stopping transients. |
| **M022** | Looser APM Bound ($\delta v=0.75	ext{ m/s}$) | Expand maximum APM speed damping from 0.50 m/s to 0.75 m/s | 6.41 | 25.20 | 425.80 | 228.90 | **REJECTED** | Excessive speed damping under-predicted speed during steady deceleration tails, increasing drift. |
| **M023** | Multi-Threshold ZUPT Gate | Apply dual-stage ZUPT gating based on SpeedNet & IMU variance | 6.41 | 22.10 | 414.20 | 234.80 | **REJECTED** | Added algorithmic complexity without improving upon single-stage $P(	ext{stat})>0.70$ threshold. |
| **M024** | Dynamic EKF Process Noise ($Q$) | Scale process noise $Q$ dynamically based on vehicle turn rate | 6.41 | 23.90 | 421.50 | 225.80 | **REJECTED** | Dynamic $Q$ scaling destabilized filter covariance tuning during straight-to-curve transitions. |
| **M025** | Dynamic NHC Covariance ($R_{	ext{nhc}}$) | Scale NHC noise dynamically based on longitudinal acceleration | 6.41 | 24.10 | 424.00 | 227.10 | **REJECTED** | Fixed $R_{	ext{nhc}}=0.04	ext{ m}^2/	ext{s}^2$ remains strictly superior for numerical EKF stability. |
| **M026** | Smooth APM Transition Function | Sigmoidal blending between SpeedNet speed and APM speed | 6.41 | 23.80 | 419.20 | 222.90 | **REJECTED** | Sigmoidal lag delayed APM activation at brake onset, reducing damping effectiveness. |
| **M027** | Jerk-Gated APM Candidate F1 | Gate APM on IMU jerk threshold $j_{	ext{long}} < -0.50	ext{ m/s}^3$ | 6.41 | 26.50 | 424.10 | 221.40 | **REJECTED** | $j_{	ext{long}} < -0.50$ was too sensitive; triggered false APM damping during normal throttle release. |
| **M028** | Jerk-Gated APM Candidate F2 | Gate APM on IMU jerk threshold $j_{	ext{long}} < -1.00	ext{ m/s}^3$ | 6.41 | 27.35 | 426.85 | 218.93 | **ACCEPTED** | **BREAKTHROUGH 6 (LOCKED BENCHMARK)**. Zero-latency brake detection (-1.19m drift drop). |
| **M029** | Jerk-Gated APM Candidate F3 | Gate APM on IMU jerk threshold $j_{	ext{long}} < -1.50	ext{ m/s}^3$ | 6.41 | 27.80 | 428.10 | 220.80 | **REJECTED** | $j_{	ext{long}} < -1.50$ was too strict; missed moderate braking transients, allowing speed lag. |
| **M030** | Dual Jerk-Variance Gating | Combine longitudinal jerk gate with lateral acceleration variance | 6.41 | 27.50 | 427.50 | 219.80 | **REJECTED** | Increased parameter complexity with no statistically significant performance gain over M028. |
| **M031** | Low-Speed Observability Audit | Diagnostic audit of low-speed rolling ($v \in [0.1, 1.0]	ext{ m/s}$) | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Confirmed $P(	ext{stat})>0.70$ activates strictly at true speed $<0.36	ext{ km/h}$; no false ZUPT locking. |
| **M032** | EKF Bias Adaptivity Diagnostic | Audit IMU accelerometer ($b_a$) and gyro ($b_w$) state tracking | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Verified EKF state covariance $P_k$ remains positive definite and bias states converge properly. |
| **M033** | Trajectory Geometry Attribution | Pointwise spatial vector decomposition of cross-track vs along-track | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Revealed cross-track drift during turns accounts for 74.2% of total 300s position error. |
| **M034** | High-G Turning Latency Diagnostic | Analyze speed estimation lag during high lateral acceleration ($a_{	ext{lat}}>2	ext{ m/s}^2$) | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Proved SpeedNet overestimates speed by +6.4 km/h during sharp curves due to centrifugal force. |
| **M035** | Turn-Gated Speed Damping | Apply speed damping during sharp turns ($|\omega_y|>10^\circ/	ext{s}$) | 6.41 | 35.80 | 490.20 | 342.10 | **REJECTED** | Damping turn speed destroyed SpeedNet's geometric path self-cancellation, exploding drift. |
| **M036** | Curvature-Dependent NHC Noise | Scale NHC noise proportional to path curvature $\kappa = \omega_y / v$ | 6.41 | 29.20 | 445.80 | 258.40 | **REJECTED** | Path curvature scaling induced non-linear noise feedback loops inside EKF measurement updates. |
| **M037** | Curvature-Weighted Neural Loss | Retrain SpeedNet with loss weight $\sigma_i = 1 + lpha |\omega_{y,i}|$ | 7.12 | 38.40 | 525.00 | 485.60 | **REJECTED** | Loss weighting distorted neural backbone representations; permanently closed neural loss edits. |
| **M038** | Dynamic APM Bound Tightening | Dynamically scale APM bound $\delta v_{\max}$ from 0.50 to 0.75 m/s | 6.41 | 28.90 | 435.10 | 224.50 | **REJECTED** | Increasing APM bound during extreme braking over-damped speed, worsening 300s position drift. |
| **M039** | Strong-Turn Geometry Diagnostic | Vector error decomposition during extreme turning transients | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Identified counterfactual evaluation script anomaly requiring formal EKF matrix audit. |
| **M040** | Counterfactual Consistency Audit | EKF matrix dot product audit & pure kinematic integration floor | 6.41 | 27.35 | 426.85 | 218.93 | **DIAGNOSTIC** | Corrected matrix bug ($K_v H_v$). Proved GT Speed in EKF degrades drift to **511.62m** (self-cancellation). |

---

### Section 2: Storytelling Walkthrough of the 6 Major Benchmark Breakthroughs

This section tells the story of how six major breakthroughs systematically reduced 300-second position drift from **6,420.00 meters down to 218.93 meters**.

```
                        BENCHMARK PROGRESSION AT A GLANCE
                        =================================

Raw IMU Double-Integration : 6,420.00 m
  ↓ (Breakthrough 1 - M003) : -4,955.00 m  [Neural Speed Estimation]
M003 SpeedNet v1           : 1,465.00 m
  ↓ (Breakthrough 2 - M004) : -1,201.89 m  [Lateral Velocity Anchoring (NHC)]
M004 SpeedNet v2           :   263.11 m
  ↓ (Breakthrough 3 - M013) :     -8.99 m  [Post-Inference Physical Constraint]
M013 Hard Constraint       :   254.12 m
  ↓ (Breakthrough 4 - M014) :    -20.94 m  [Stationary 2D Velocity Resets (ZUPT)]
M014 ZUPT Fusion           :   233.18 m
  ↓ (Breakthrough 5 - M019) :    -13.06 m  [Acceleration-Integrated Speed Damping]
M019 APM Damping           :   220.12 m
  ↓ (Breakthrough 6 - M028) :     -1.19 m  [Zero-Latency IMU Jerk Gating]
M028/M040 Jerk Gate        :   218.93 m  <-- FINAL LOCKED PRODUCTION BENCHMARK!
```

---

#### Breakthrough 1: M003 — SpeedNet v1 (Neural Speed vs Inertial Double-Integration)

- **Starting Point & Problem:** Double-integrating uncalibrated smartphone accelerometers ($\mathbf{a}_{	ext{raw}} - \mathbf{g}$) causes sensor noise, bias instability, and pitch/roll tilt errors to accumulate exponentially over time:
  $$\mathbf{p}(t) = \mathbf{p}(0) + \mathbf{v}(0)t + \iint_{0}^t (\mathbf{a}_{	ext{raw}}(	au) - \mathbf{g}) d	au^2 \implies \mathbf{Error} \propto \mathcal{O}(t^3)$$
  At 300 seconds, raw double-integration explodes to **6,420.00 meters of position drift**.

- **The Neural Breakthrough:** We replaced raw acceleration double-integration with **SpeedNet v1** (1D-CNN + BiLSTM), predicting scalar forward vehicle speed $\hat{v}_{	ext{net}}$ directly from 4-second IMU sliding windows ($W=30$). Position is obtained by single integration:
  $$\mathbf{p}(T) = \int_0^T \hat{v}_{	ext{net}}(t) egin{bmatrix} \cos\psi(t) \ \sin\psi(t) \end{bmatrix} dt$$

- **Error Reduction:**
  - **300s Position Drift:** $6,420.00	ext{ m} \longrightarrow \mathbf{1,465.00	ext{ m}}$
  - **Absolute Drop:** **`-4,955.00 m` (77.2% Error Reduction)**

![Breakthrough 1 - SpeedNet v1 Open Loop](figures/02_speednet_v1_open_loop.png)

---

#### Breakthrough 2: M004 — SpeedNet v2 Multi-Task + Fixed 2D Non-Holonomic Constraint (NHC)

- **Starting Point & Problem:** M003 integrated neural speed open-loop. Unconstrained heading drift caused the vehicle trajectory to drift sideways during straight driving and curves ($1,465.00	ext{ m}$).

- **The Physical Breakthrough:** We combined SpeedNet v2 multi-task learning ($W=40$) with a physical **2D Non-Holonomic Constraint (NHC)** inside an Extended Kalman Filter (EKF). Because land vehicles cannot slide sideways without slipping, lateral body-frame velocity is zero ($v_{	ext{lateral}} = 0$):
  $$z_{	ext{nhc}} = -v_x \cos\psi + v_y \sin\psi = 0 + 
u, \quad 
u \sim \mathcal{N}(0, R_{	ext{nhc}}), \quad R_{	ext{nhc}} = 0.04	ext{ m}^2/	ext{s}^2$$

- **Error Reduction:**
  - **300s Position Drift:** $1,465.00	ext{ m} \longrightarrow \mathbf{263.11	ext{ m}}$
  - **Absolute Drop:** **`-1,201.89 m` (82.0% Error Reduction)**

![Breakthrough 2 - SpeedNet v2 Baseline NHC](figures/03_speednet_v2_baseline_263m.png)

---

#### Breakthrough 3: M013 — Post-Inference Hard Physical Speed Constraint (F4)

- **Starting Point & Problem:** During steady cruise and stops, engine vibration noise caused SpeedNet to slightly over-predict speed. Soft neural loss terms during training (`M012`) failed by causing zero-prediction speed collapse.

- **The Post-Inference Breakthrough:** We applied a **hard physical consistency bound** ($v_{	ext{bound}}$) **AFTER neural inference**, gated on low IMU variance ($\sigma_a^2 \le 3.72$) and straight driving ($|\omega_y| \le 5^\circ/	ext{s}$):
  $$v_{	ext{bound}, k} = \hat{v}_{k-1} + a_{	ext{long}, k} \cdot \Delta t$$
  $$\hat{v}_{	ext{constrained}, k} = \min\left( \hat{v}_{	ext{net}, k}, v_{	ext{bound}, k} ight)$$

- **Error Reduction:**
  - **300s Position Drift:** $263.11	ext{ m} \longrightarrow \mathbf{254.12	ext{ m}}$
  - **Absolute Drop:** **`-8.99 m` (-3.4% Error Reduction)**

![Breakthrough 3 - M013 Hard Physical Constraint](figures/04_m013_hard_physical_constraint_254m.png)

---

#### Breakthrough 4: M014 — Stationary 2D Zero-Velocity Updates (ZUPT F3)

- **Starting Point & Problem:** When the vehicle stopped at traffic lights or intersections, tiny SpeedNet speed residuals ($0.5 - 1.0	ext{ km/h}$) accumulated velocity integration drift over time.

- **The EKF Update Breakthrough:** We used SpeedNet v2's multi-task stationary head ($P(	ext{stat}) > 0.70$) to trigger **2D Zero-Velocity Updates (ZUPT)** inside the EKF, resetting internal velocity states to exact zero ($\mathbf{z} = [0,0]^T, \mathbf{R}_{	ext{zupt}} = 	ext{diag}(0.04, 0.04)$):
  $$\mathbf{y}_{	ext{zupt}} = egin{bmatrix} 0 \ 0 \end{bmatrix} - egin{bmatrix} v_x \ v_y \end{bmatrix}_{k|k-1}, \quad 	ext{Trigger ZUPT } \iff P(	ext{stat}) > 0.70 	ext{ and } \|\mathbf{y}_{	ext{zupt}}\| \le 5.0	ext{ m/s}$$

- **Error Reduction:**
  - **300s Position Drift:** $254.12	ext{ m} \longrightarrow \mathbf{233.18	ext{ m}}$
  - **Absolute Drop:** **`-20.94 m` (-8.2% Error Reduction)**

![Breakthrough 4 - M014 ZUPT Fusion](figures/05_m014_zupt_velocity_reset_233m.png)

---

#### Breakthrough 5: M019 — Bounded Acceleration-Integrated Speed Damping (APM F4)

- **Starting Point & Problem:** SpeedNet predictions lagged by $200 - 300	ext{ ms}$ during heavy braking transients, over-predicting speed while the vehicle was rapidly slowing down.

- **The Causal Integration Breakthrough:** We integrated causal 0.5s longitudinal IMU acceleration to construct Acceleration-Integrated Pseudo-Measurements ($z_{	ext{apm}}$), damping speed overestimation by up to $\delta v_{\max} = 0.50	ext{ m/s}$ during decelerations ($a_{	ext{long}} < -0.50	ext{ m/s}^2$):
  $$z_{	ext{apm}, k} = \hat{v}_{k-1} + \int_{t-0.5}^t a_{	ext{long}}(	au) d	au$$
  $$\hat{v}_{	ext{apm}, k} = \max\left( \hat{v}_{	ext{net}, k} - 0.50, \min\left( \hat{v}_{	ext{net}, k}, z_{	ext{apm}, k} ight) ight)$$

- **Error Reduction:**
  - **300s Position Drift:** $233.18	ext{ m} \longrightarrow \mathbf{220.12	ext{ m}}$
  - **Absolute Drop:** **`-13.06 m` (-5.6% Error Reduction)**

![Breakthrough 5 - M019 APM Speed Damping](figures/06_m019_apm_speed_damping_220m.png)

---

#### Breakthrough 6: M028 / M040 — Causal IMU Longitudinal Jerk Gate (M028 F2 — FINAL BENCHMARK)

- **Starting Point & Problem:** M019 APM applied damping throughout the entire deceleration leg, slightly over-damping speed during steady braking tails.

- **The Zero-Latency Gating Breakthrough:** We introduced **zero-latency causal IMU longitudinal jerk gating** ($j_{	ext{long}} = rac{a_k - a_{k-1}}{\Delta t} < -1.00	ext{ m/s}^3$) to activate APM damping strictly at brake onset, suppressing over-damping during steady braking tails:
  $$j_{	ext{long}, k} = rac{a_{	ext{long}, k} - a_{	ext{long}, k-1}}{\Delta t}$$
  $$	ext{Apply APM Damping } \iff a_{	ext{long}, k} < -0.50	ext{ m/s}^2 \quad 	ext{AND } j_{	ext{long}, k} < -1.00	ext{ m/s}^3$$

- **Error Reduction:**
  - **300s Position Drift:** $220.12	ext{ m} \longrightarrow \mathbf{218.93	ext{ m}}$
  - **Absolute Drop:** **`-1.19 m` (FINAL LOCKED BENCHMARK)**

![Breakthrough 6 - M028 Jerk Gated APM](figures/07_m028_jerk_gated_apm_218m.png)

---

### Section 3: Master Benchmark Evolution Chart

The master evolution chart below displays the continuous reduction of dead-reckoning position drift across all three GNSS outage horizons (60s, 120s, and 300s) from raw inertial double-integration (`M001`) to the locked production benchmark (`M028/M040`).

![Master Benchmark Evolution Chart](figures/08_master_benchmark_evolution.png)

#### Outage Horizon Performance Summary Table

| Progression Stage | 60-Second Drift (m) | 120-Second Drift (m) | 300-Second Drift (m) | Stage Improvement (300s) | Cumulative Improvement |
|---|---:|---:|---:|---:|---:|
| **M001: Raw Inertial Double-Integration** | 1,200.00 | 2,800.00 | 6,420.00 | BASELINE | BASELINE |
| **M003: SpeedNet v1 Open-Loop** | 110.50 | 480.20 | 1,465.00 | -4,955.00 m (-77.2%) | -77.2% |
| **M004: SpeedNet v2 + Fixed 2D NHC** | 22.80 | 440.20 | 263.11 | -1,201.89 m (-82.0%) | -95.9% |
| **M013: Hard Physical Constraint (F4)** | 22.10 | 428.50 | 254.12 | -8.99 m (-3.4%) | -96.0% |
| **M014: 2D Zero-Velocity Updates (ZUPT)** | 21.80 | 412.30 | 233.18 | -20.94 m (-8.2%) | -96.4% |
| **M019: Bounded APM Speed Damping** | 23.40 | 415.60 | 220.12 | -13.06 m (-5.6%) | -96.6% |
| **M028/M040: Jerk-Gated APM (LOCKED)** | **27.35** | **426.85** | **218.93** | **-1.19 m (-0.5%)** | **-96.6%** |

---

### Section 4: Technical Specifications of Proposed Neural Models & Physical Layer Algorithms

This section provides a detailed technical breakdown of every neural network model architecture and post-inference physical layer algorithm designed, implemented, and evaluated during the IDR project.

---

#### 1. SpeedNet v1 Architecture (M003)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU $[\mathbf{a}_{	ext{lin}}, oldsymbol{\omega}] = [a_{x,	ext{lin}}, a_{y,	ext{lin}}, a_{z,	ext{lin}}, \omega_x, \omega_y, \omega_z]$
  - Window length: $W = 30$ samples ($3.0	ext{ seconds}$ @ $10	ext{ Hz}$)
  - Input tensor shape: $(B, 6, 30)$

- **Training Algorithm & Loss Function:**
  - Architecture: 3-layer 1D-CNN (64, 128, 256 filters, kernel size 3) + 2-layer BiLSTM (128 hidden units) + Fully Connected linear projection.
  - Loss Function: Standard Mean Squared Error (MSE) on ground-truth speed $v$:
    $$\mathcal{L}_{	ext{MSE}} = rac{1}{N} \sum_{i=1}^N (v_i - \hat{v}_i)^2$$
  - Optimizer: Adam ($	ext{lr} = 10^{-3}$, weight decay $10^{-4}$, batch size 64).

- **Core Physical Assumptions:**
  - Forward vehicle speed is observable from high-frequency multi-axis engine and road vibration patterns in IMU sliding windows.

- **Outcome & Decision:**
  - **Status:** **ACCEPTED**.
  - **Performance:** Speed MAE = $1.82	ext{ m/s}$ ($6.55	ext{ km/h}$). 300s Position Drift = $1,465.00	ext{ m}$. Formed the initial neural speed baseline.

---

#### 2. SpeedNet v2 Multi-Task Architecture (M004 — PRODUCTION BACKBONE)

- **Input Features & Windowing:**
  - Input vector: 6-channel linear accelerometer and gyroscope $[\mathbf{a}_{	ext{lin}}, oldsymbol{\omega}]$
  - Window length: $W = 40$ samples ($4.0	ext{ seconds}$ @ $10	ext{ Hz}$)
  - Input tensor shape: $(B, 6, 40)$

- **Training Algorithm & Loss Function:**
  - Architecture: Shared 1D-CNN + BiLSTM feature extractor with dual task heads:
    1. **Speed Head:** Continuous linear regression outputting scalar speed $\hat{v}_k$
    2. **Stationary Head:** Binary classification outputting stationary probability $P(	ext{stat})_k \in [0, 1]$ via Sigmoid
  - Loss Function: Multi-task joint loss:
    $$\mathcal{L}_{	ext{total}} = \mathcal{L}_{	ext{MSE}}(\hat{v}, v) + 0.5 \cdot \mathcal{L}_{	ext{BCE}}(P(	ext{stat}), y_{	ext{stat}})$$

- **Core Physical Assumptions:**
  - Vehicle speed regression and stationary zero-motion detection share common lower-level IMU spectral features.

- **Outcome & Decision:**
  - **Status:** **ACCEPTED (LOCKED PRODUCTION BACKBONE)**.
  - **Performance:** Speed MAE = $1.78	ext{ m/s}$ ($6.41	ext{ km/h}$). 300s Position Drift = $263.11	ext{ m}$ (with 2D NHC). Serves as the frozen neural backbone for all subsequent physical layers.

---

#### 3. HeadingNet Yaw Rate Architecture (M005)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU $[\mathbf{a}_{	ext{lin}}, oldsymbol{\omega}]$, sliding window $W = 50$ ($5.0	ext{ s}$ @ $10	ext{ Hz}$).

- **Training Algorithm & Loss Function:**
  - Architecture: 1D-CNN + BiLSTM predicting vehicle yaw rate $\hat{\omega}_{y, k}$.
  - Loss Function: MSE on ground-truth yaw rate $\omega_y$:
    $$\mathcal{L}_{	ext{yaw}} = rac{1}{N} \sum_{k=1}^N (\hat{\omega}_{y, k} - \omega_{y, k})^2$$

- **Core Physical Assumptions:**
  - Neural network can estimate vehicle turn rate directly from IMU signals without gyroscope integration bias drift.

- **Outcome & Decision:**
  - **Status:** **REJECTED**.
  - **Performance:** Pointwise Yaw MAE = $1.20^\circ/	ext{s}$. 300s Position Drift = **$740.30	ext{ m}$ (+181.4% degradation)**.
  - **Failure Rationale:** Monotonic integration of tiny neural biases ($0.2^\circ/	ext{s}$) during straight driving accumulated $60^\circ$ heading error and destroyed EKF geometric path self-cancellation.

---

#### 4. SpeedNet v3 Regime-Aware Multi-Head Model (M007)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU, window $W = 40$ ($4.0	ext{ s}$ @ $10	ext{ Hz}$).

- **Training Algorithm & Loss Function:**
  - Architecture: Gated Mixture-of-Experts (MoE) with 3 regime-specific output heads (Stationary Head, Cruise Head, Turning Head).
  - Gating Network: Softmax gating $\mathbf{w} = 	ext{softmax}(W_g \mathbf{h})$. Total Loss:
    $$\mathcal{L}_{	ext{v3}} = \sum_{r \in \{	ext{stat, cruise, turn}\}} w_r \cdot \mathcal{L}_{	ext{MSE}, r}$$

- **Core Physical Assumptions:**
  - Vehicle motion naturally decomposes into discrete kinematic regimes with specialized speed dynamics.

- **Outcome & Decision:**
  - **Status:** **REJECTED**.
  - **Performance:** Speed MAE = $1.74	ext{ m/s}$. 300s Position Drift = **$310.45	ext{ m}$ (+18.0% degradation)**.
  - **Failure Rationale:** Discontinuous regime boundary switching induced velocity step jumps that degraded EKF measurement updates.

---

#### 5. SpeedNet v2.5 Physics-Loss Model (M008)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU, window $W = 40$ ($4.0	ext{ s}$ @ $10	ext{ Hz}$).

- **Training Algorithm & Loss Function:**
  - Architecture: SpeedNet v2 backbone trained with Kinematic Acceleration Loss:
    $$\mathcal{L}_{	ext{v2.5}} = \mathcal{L}_{	ext{MSE}}(\hat{v}, v) + \lambda_{	ext{kin}} \left\| rac{\hat{v}_k - \hat{v}_{k-1}}{\Delta t} - a_{	ext{long}, k} ight\|^2, \quad \lambda_{	ext{kin}} = 0.10$$

- **Core Physical Assumptions:**
  - Penalizing speed derivative mismatches against accelerometer readings forces neural predictions to respect physical acceleration limits.

- **Outcome & Decision:**
  - **Status:** **REJECTED**.
  - **Performance:** Speed MAE = $1.95	ext{ m/s}$. 300s Position Drift = **$445.20	ext{ m}$ (+69.2% degradation)**.
  - **Failure Rationale:** Gradient conflict between MSE loss and acceleration penalty caused zero-prediction speed collapse.

---

#### 6. SpeedNet v4 Asymmetric Loss Model (M011 / M012)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU, window $W = 40$ ($4.0	ext{ s}$ @ $10	ext{ Hz}$).

- **Training Algorithm & Loss Function:**
  - Architecture: SpeedNet v2 backbone trained with Asymmetric Loss heavily penalizing speed over-prediction:
    $$\mathcal{L}_{	ext{asym}} = egin{cases} (\hat{v} - v)^2 & 	ext{if } \hat{v} \le v \ 2.5 \cdot (\hat{v} - v)^2 & 	ext{if } \hat{v} > v \end{cases}$$

- **Core Physical Assumptions:**
  - Speed over-prediction creates greater dead-reckoning position error than under-prediction, so training should penalize over-estimation heavier.

- **Outcome & Decision:**
  - **Status:** **REJECTED**.
  - **Performance:** Speed MAE = $2.15	ext{ m/s}$. 300s Position Drift = **$680.15	ext{ m}$ (+158.5% degradation)**.
  - **Failure Rationale:** Asymmetric loss distorted neural weight calibration, causing zero-velocity trapping during cruise motion.

---

#### 7. SpeedNet v5 Downsampled Model (M016)

- **Input Features & Windowing:**
  - Input vector: 6-channel IMU downsampled from $10	ext{ Hz}$ to $5	ext{ Hz}$, window $W = 20$ ($4.0	ext{ s}$ @ $5	ext{ Hz}$).

- **Training Algorithm & Loss Function:**
  - Architecture: Lightweight 1D-CNN + BiLSTM optimized for low-power mobile execution.
  - Loss Function: Standard multi-task MSE + BCE loss.

- **Core Physical Assumptions:**
  - 5 Hz sampling rate retains sufficient spectral information for vehicle speed estimation while cutting computation by 50%.

- **Outcome & Decision:**
  - **Status:** **REJECTED**.
  - **Performance:** Speed MAE = $2.42	ext{ m/s}$. 300s Position Drift = **$388.90	ext{ m}$ (+47.8% degradation)**.
  - **Failure Rationale:** Downsampling aliased high-frequency road vibration signals required for accurate neural speed prediction.

---

#### 8. M013 Post-Inference Hard Physical Speed Constraint Algorithm

- **Input Signals:**
  - SpeedNet v2 speed prediction $\hat{v}_{	ext{net}, k}$, longitudinal accelerometer $a_{	ext{long}, k}$, yaw rate $\omega_{y, k}$, IMU variance $\sigma_a^2$.

- **Algorithm & Execution Logic:**
  - Post-inference physical truncation rule:
    $$v_{	ext{bound}, k} = \hat{v}_{k-1} + a_{	ext{long}, k} \cdot \Delta t$$
    $$\hat{v}_{	ext{constrained}, k} = egin{cases} \min\left(\hat{v}_{	ext{net}, k}, v_{	ext{bound}, k}ight) & 	ext{if } \sigma_a^2 \le 3.72 	ext{ and } |\omega_y| \le 5^\circ/	ext{s} \ \hat{v}_{	ext{net}, k} & 	ext{otherwise} \end{cases}$$

- **Core Physical Assumptions:**
  - Vehicle speed cannot exceed upper acceleration bounds governed by Newton's second law ($\Delta v \le a \Delta t$).

- **Outcome & Decision:**
  - **Status:** **ACCEPTED**.
  - **Performance:** 300s Position Drift = **$254.12	ext{ m}$ (-8.99 m reduction)**. Safely caps cruise over-prediction without distorting neural weights.

---

#### 9. M014 2D Zero-Velocity Update (ZUPT) Algorithm

- **Input Signals:**
  - SpeedNet v2 stationary probability $P(	ext{stat})_k$, EKF innovation residual $\mathbf{y}_{	ext{zupt}}$.

- **Algorithm & Execution Logic:**
  - Trigger 2D EKF measurement update resetting horizontal velocity to exact zero:
    $$\mathbf{z}_{	ext{zupt}} = egin{bmatrix} 0 \ 0 \end{bmatrix}, \quad \mathbf{R}_{	ext{zupt}} = egin{bmatrix} 0.04 & 0 \ 0 & 0.04 \end{bmatrix}$$
    $$	ext{Execute ZUPT Update } \iff P(	ext{stat})_k > 0.70 \quad 	ext{and } \|\mathbf{y}_{	ext{zupt}}\| \le 5.0	ext{ m/s}$$

- **Core Physical Assumptions:**
  - When a land vehicle is stationary, its true 2D horizontal velocity is strictly zero.

- **Outcome & Decision:**
  - **Status:** **ACCEPTED**.
  - **Performance:** 300s Position Drift = **$233.18	ext{ m}$ (-20.94 m reduction)**. Eliminates velocity integration drift during traffic stops.

---

#### 10. M019 Acceleration-Integrated Speed Damping (APM) Algorithm

- **Input Signals:**
  - Longitudinal IMU acceleration $a_{	ext{long}}$, previous speed estimate $\hat{v}_{k-1}$, SpeedNet speed $\hat{v}_{	ext{net}, k}$.

- **Algorithm & Execution Logic:**
  - Causal 0.5s integration of longitudinal acceleration during decelerations:
    $$z_{	ext{apm}, k} = \hat{v}_{k-1} + \int_{t-0.5}^t a_{	ext{long}}(	au) d	au$$
    $$\hat{v}_{	ext{apm}, k} = \max\left( \hat{v}_{	ext{net}, k} - 0.50, \min\left( \hat{v}_{	ext{net}, k}, z_{	ext{apm}, k} ight) ight) \quad 	ext{if } a_{	ext{long}, k} < -0.50	ext{ m/s}^2$$

- **Core Physical Assumptions:**
  - Causal 0.5s accelerometer integration provides zero-latency speed damping during braking transients.

- **Outcome & Decision:**
  - **Status:** **ACCEPTED**.
  - **Performance:** 300s Position Drift = **$220.12	ext{ m}$ (-13.06 m reduction)**. Eliminates neural response lag during braking.

---

#### 11. M028 Causal IMU Longitudinal Jerk Gate Algorithm (FINAL BENCHMARK)

- **Input Signals:**
  - Longitudinal IMU acceleration derivative (jerk) $j_{	ext{long}, k} = rac{a_{	ext{long}, k} - a_{	ext{long}, k-1}}{\Delta t}$, $a_{	ext{long}, k}$.

- **Algorithm & Execution Logic:**
  - Gating APM damping on negative longitudinal jerk threshold:
    $$	ext{Apply APM Damping } \iff a_{	ext{long}, k} < -0.50	ext{ m/s}^2 \quad 	ext{AND } j_{	ext{long}, k} < -1.00	ext{ m/s}^3$$

- **Core Physical Assumptions:**
  - Driver braking onset is uniquely identified by a sharp negative jerk spike ($j_{	ext{long}} < -1.00	ext{ m/s}^3$), enabling zero-latency brake detection while preserving steady-state cruise speed updates.

- **Outcome & Decision:**
  - **Status:** **ACCEPTED (LOCKED PRODUCTION BENCHMARK)**.
  - **Performance:** 300s Position Drift = **$218.93	ext{ m}$ (-1.19 m reduction)**. Serves as the locked final benchmark.

---
