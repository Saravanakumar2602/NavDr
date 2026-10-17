# SIH 2026 — Intelligent Dead Reckoning (ISRO PS 26168)
## Official Research Story: From Benchmark Optimization to Real-World Smartphone Deployment

> **The SIH Research Journey:**
> **Problem → Baseline (M028) → Benchmark Optimization (M029) → Real-World Bus Validation → Domain-Shift Discovery → SpeedNet Ablation → Final Adaptive Hybrid Architecture (M032) → NavDR Deployment**

---

### 1. Problem Statement & Research Objective

GNSS-based navigation systems degrade or completely fail in challenging operational environments:
* **Urban Canyons & High-Rises** (Multipath signals & severe dilution of precision)
* **Tunnels, Underpasses & Underground Transit** (Complete signal loss)
* **Dense Forest Canopy & Deep Valleys** (Signal attenuation & masking)
* **GNSS Interference, Electronic Countermeasures & Jamming**

While smartphone IMUs (accelerometers and gyroscopes) are ubiquitous, lightweight, and continuously accessible, direct inertial double-integration fails rapidly due to MEMS sensor bias, thermal drift, high-frequency noise, phone placement vibrations, and accumulated quadratic position drift.

#### Core Research Objective
> **Build a lightweight, smartphone-based Intelligent Dead Reckoning (IDR) system that maintains continuous sub-lane navigation accuracy during prolonged GNSS outages and seamlessly re-aligns when GNSS signals return.**

---

### 2. First Prototype — M028 Baseline Architecture

We initialized our investigation by developing a baseline hybrid AI + physics architecture (**M028**):

$$\text{RAW IMU} \longrightarrow \text{SpeedNet v2 (1D CNN + BiLSTM)} \longrightarrow \text{7-State ENU EKF} \longrightarrow \text{NHC} \longrightarrow \text{ZUPT} \longrightarrow \text{APM} \longrightarrow \text{Dead-Reckoned Position}$$

M028 fused learned forward speed and stationary probabilities with standard inertial propagation and physical constraints.

#### Initial Benchmark Result (IO-VNBD Dataset — 300s Vw04 Outage)
* **300s Position Error:** **`218.93 m`**
* **Heading RMSE:** **`64.66°`**

This established our starting baseline.

---

### 3. Root Cause Investigation — Heading Drift Analysis

Before modifying the neural network weights, we performed a thorough error decomposition to identify the primary driver of position divergence.

Our analysis revealed a strong correlation:
$$\text{Gyro Bias / Yaw Error} \xrightarrow{\quad\quad} \text{Heading Drift} \xrightarrow{\quad\quad} \text{Velocity Projection Vector Error} \xrightarrow{\quad\quad} \text{Quadratic Position Divergence}$$

Rather than retraining neural weights, we focused our research efforts on **rearchitecting the navigation heading fusion strategy**.

---

### 4. M029 — Benchmark Optimization (Multi-Anchor Heading)

To address heading drift, we developed **M029**, introducing a multi-anchor heading hierarchy:

```text
                     GNSS Reference Course (When Available)
                                     ↓
                     Motion-Gated Zero-Yaw Constraint
                                     ↓
                         SpeedNet Neural Yaw Rate
                                     ↓
                    MEMS Gyro Bias-Corrected Propagation
```

#### Benchmark Results (IO-VNBD Dataset — 300s Vw04 Outage)
* **M028 Baseline:** `218.93 m`
* **M029 Multi-Anchor:** **`48.20 m`** (**`77.98% position error reduction`**)

> **🏆 Best Numerical Benchmark Result:** M029 represents our top-performing benchmark score on the canonical IO-VNBD dataset.

---

### 5. Transition to Real-World Smartphone Validation

Achieving strong results on a clean, benchmark dataset was a major milestone, but SIH Problem 26168 specifically mandates **real smartphone deployment**.

To test true real-world generalizability, we collected an independent, uncalibrated dataset using a **real smartphone mounted inside a moving heavy transit bus**:
* **Sensors Captured:** Accelerometer (400 Hz), Gyroscope (400 Hz), GNSS (1 Hz)
* **Duration:** $\sim 552\text{ seconds}$ ($\sim 9.2\text{ minutes}$)
* **Vehicle Domain:** Heavy Urban Bus (High mass, body roll, unique suspension harmonics)

---

### 6. Controlled GNSS-Denied Experiment Protocol

To evaluate dead-reckoning performance fairly on the real bus dataset, we designed a rigorous experimental protocol:
* **Outage Window:** $t = 265.0\text{ s} \longrightarrow 335.0\text{ s}$ (**$70\text{ seconds}$ continuous outage**)
* **Turn Dynamics:** Includes a sharp $90^\circ$ dynamic bus turn at $t \approx 310\text{ s}$
* **Blinding Protocol:** GNSS coordinates were hidden from the estimator during the outage interval and retained solely as ground-truth reference for evaluation.

> **Official Terminology:** *"Controlled GNSS outage simulation on real smartphone bus data."*

---

### 7. Real-World Domain-Shift Discovery

When we evaluated the benchmark winner (**M029**) on the real smartphone bus dataset, we discovered a significant failure mode:

* **M028 Baseline:** `53.77 m` @ 70s
* **M029 Multi-Anchor:** **`516.44 m` @ 70s** (Heading RMSE: `72.17°`)

#### Diagnostic Root Cause
The neural yaw-rate estimator in SpeedNet, calibrated on light passenger vehicles in the benchmark dataset, suffered from **severe cross-vehicle domain shift** when subjected to the structural vibrations and roll dynamics of a heavy bus during active turns. Direct fusion of neural yaw corrupted the EKF state and caused catastrophic position divergence.

---

### 8. Diagnostic Iteration — M030 Confidence-Gated Yaw

We developed **M030** to gate neural yaw fusion based on innovation thresholds:
$$\text{Trust Neural Yaw ONLY IF } |\omega_{\text{snet}} - \omega_{\text{gyro}}| \le \text{Threshold}$$

#### Results
* **M029:** `516.44 m`
* **M030:** `410.14 m`

While M030 mitigated some divergence, hard thresholding remained unstable during dynamic maneuvers. This proved that threshold-tuning could not solve the fundamental domain-shift issue.

---

### 9. Critical Scientific Ablation — Isolating the True AI Contribution

To determine the true utility of deep learning in dead reckoning, we conducted a controlled ablation study by removing SpeedNet's forward-speed measurement from the navigation pipeline.

#### Real Smartphone Bus Outage ($70\text{ s}$) Ablation Results

| Navigation System Configuration | 70s Position Error | Position RMSE | Drift Rate | Error Reduction |
| :--- | :---: | :---: | :---: | :---: |
| **Physics-Only Pure Inertial DR** | `604.58 m` | `285.12 m` | `8.637 m/s` | Baseline |
| **M028 Without SpeedNet Speed Update** | **`1044.84 m`** | `466.35 m` | `14.926 m/s` | Divergent |
| **M028 + SpeedNet Forward Speed Update** | **`53.77 m`** | `78.32 m` | `0.768 m/s` | **`94.85% Reduction`** |

#### Key Insight
> **The primary robust contribution of AI in Intelligent Dead Reckoning is learned forward-velocity estimation ($v_{\text{snet}}$), NOT neural yaw.**

---

### 10. Final Architecture Freeze — M032 Adaptive Hybrid IDR

Based on empirical evidence from our dual-dataset evaluations and ablation studies, we established the core design principle for **M032**:

* **AI (SpeedNet v2):** Estimates forward vehicle speed ($v_{\text{snet}}$) and stationary probability ($P_{\text{stat}}$).
* **Physics (MEMS Gyro):** Handles primary heading propagation ($\dot{\psi} = \omega_m - b_\omega$).
* **Filter (7-State ENU EKF):** Performs optimal state fusion with NHC, ZUPT, APM, and GNSS.

```text
                                 SMARTPHONE IMU
                                       │
                      ┌────────────────┴────────────────┐
                      │                                 │
                      ▼                                 ▼
                MEMS Gyroscope                     SpeedNet v2
                      │                           1D CNN + BiLSTM
                      │                                 │
                      │                           ┌─────┴─────┐
                      │                           │           │
                      ▼                           ▼           ▼
               Primary Heading              Forward Speed   P_stat
                 Propagation                   (v_snet)       │
                      │                           │           │
                      └───────────────┬───────────┘           │
                                      ▼                       │
                               7-State ENU EKF ◄──────────────┘
                            [x, y, vx, vy, psi, ba, bw]
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                        NHC          APM         ZUPT
                         │            │            │
                         └────────────┴────────────┘
                                      │
                                      ▼
                             DR STATE POSITION
                                      │
                              GNSS RECOVERY
                                      │
                                      ▼
                             GNSS + INS FUSION
```

#### Final Performance Metrics

| Dataset / Benchmark | Architecture | Performance Score | Status |
| :--- | :--- | :---: | :--- |
| **IO-VNBD Benchmark (300s Outage)** | **M029 Multi-Anchor** | **`48.20 m`** | **🏆 Best Numerical Benchmark** |
| **IO-VNBD Benchmark (300s Outage)** | **M032 Adaptive Hybrid** | **`297.45 m`** | **PASS (< 500m Target)** |
| **Real Smartphone Bus (70s Outage)** | **M032 Adaptive Hybrid** | **`53.70 m`** | **🏆 Official Final Freeze** |
| **Real Smartphone Bus (No SpeedNet)** | **M032-NoSpeedNet** | **`1044.84 m`** | **Ablation Baseline** |

---

### 11. Final Scientific Conclusion

> **"Our research demonstrated that the top-performing benchmark architecture is not automatically the most robust deployment architecture. By validating against real smartphone sensor data and conducting rigorous ablation studies, we evolved from benchmark-optimized neural yaw toward an adaptive hybrid architecture where AI provides learned forward velocity and physics provides robust heading propagation."**

---

### 12. Headline Achievements

```text
🏆 GIVEN BENCHMARK (IO-VNBD)               🏆 REAL SMARTPHONE DEPLOYMENT (BUS)
   M029 Multi-Anchor                          M032 Adaptive Hybrid
   48.20 m @ 300s                             53.70 m @ 70s
   77.98% improvement over baseline           94.85% speed ablation reduction
```

---

### 13. High-Level SIH Presentation Journey

```text
SIH Problem Statement 26168
             │
      M028 Baseline
    218.93 m @ 300s Outage
             │
   Heading Drift Analysis
             │
 M029 Multi-Anchor Heading
  48.20 m @ 300s (IO-VNBD)
   77.98% Error Reduction
             │
   REAL SMARTPHONE DATA
   ~552s Urban Bus Recording
             │
    M029 Domain Shift
    516.44 m @ 70s Outage
             │
 M030 Neural-Yaw Gating
   Still Divergent (410m)
             │
   SPEEDNET ABLATION
   53.77m vs 1044.84m (94.85% Impact)
             │
 M032 FINAL ADAPTIVE HYBRID
  AI Speed + Physics Heading + EKF
             │
   53.70 m @ 70s Outage
   (REAL SMARTPHONE BUS TEST)
             │
           NavDR
    Navigate Beyond GNSS
```

---

### Model Freeze Status: **FROZEN**
* All navigation architectures (M028, M029, M030, M031, M032) and SpeedNet checkpoints (`models/speednet_v2_w40.pth`) are fully validated, documented, and frozen.
* Ready for production mobile app integration into **NavDR**.