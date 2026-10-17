# Three-Graph Model Evolution Comparison

This directory contains three high-resolution, publication-quality comparison charts illustrating the performance progression across the **EXACT SAME SIX CORE PROJECT STAGES** of the Intelligent Dead-Reckoning (IDR) project (`M001` through `M040`).

---

## Selected Six Stages

The six selected project stages represent the primary benchmark-advancing milestones in the evolution of the IDR physical and neural navigation pipeline.

| Order | Milestone ID | Stage Name / Description | Why Selected |
|---|---|---|---|
| **1** | `M003` | **SpeedNet v1 (Open-Loop Baseline)** | Initial neural speed estimation baseline integrated open-loop without physical constraints ($1,465\text{ m}$ @ 300s). |
| **2** | `M004` | **SpeedNet v2 + Fixed NHC (Baseline Benchmark)** | Multi-task CNN+BiLSTM ($W=40$) speed estimation combined with fixed 2D Non-Holonomic Constraints ($263.11\text{ m}$ @ 300s). |
| **3** | `M013` | **Confidence Physical Constraint (M013 F4)** | Post-inference physical consistency bound ($\sigma_a^2 \le 3.72$, $|\omega_y| \le 5^\circ/\text{s}$) trimming cruise speed bias ($254.12\text{ m}$ @ 300s). |
| **4** | `M014` | **Stationary 2D ZUPT Fusion (M014 F3)** | Stationary zero-velocity updates ($\sigma_{\text{zupt}} = 0.20\text{ m/s}$) resetting velocity state integration errors ($233.18\text{ m}$ @ 300s). |
| **5** | `M019` | **Bounded APM Speed Damping (M019 F4)** | Causal 0.5s acceleration integration ($\delta v_{\max} = 0.50\text{ m/s}$) damping SpeedNet speed overestimation during braking ($220.12\text{ m}$ @ 300s). |
| **6** | `M028` / `M040` | **Jerk-Gated APM (Final Production Pipeline)** | Zero-latency IMU longitudinal jerk gating ($j_{\text{long}} < -1.00\text{ m/s}^3$) activating APM at brake onset (**$218.93\text{ m}$ @ 300s**). |

---

## Graph 1 — Speed Accuracy (`speed_accuracy_comparison.png`)

- **Primary Metric:** Speed MAE (km/h) [Test Set, Lower is Better]
- **Visualization:** Bar Chart (discrete stage comparison)
- **Values Across the 6 Stages:**
  - Stage 1 (`M003`): **$9.22\text{ km/h}$**
  - Stage 2 (`M004`): **$9.15\text{ km/h}$**
  - Stage 3 (`M013`): **$9.05\text{ km/h}$**
  - Stage 4 (`M014`): **$7.42\text{ km/h}$** (Zero-velocity updates correct stationary periods)
  - Stage 5 (`M019`): **$7.36\text{ km/h}$** (APM speed damping trims braking overestimation)
  - Stage 6 (`M028/M040`): **$7.33\text{ km/h}$** (Jerk-gated APM minimizes braking lag)
- **Source Artifacts:** `results/vw4_ml_dr_integration_report.md`, `results/vw4_orientation_anchor_summary.json`, `results/vw4_m013_hard_physical_inference_constraint_summary.json`, `results/vw4_m014_zupt_velocity_update_summary.json`, `results/vw4_m019_apm_speed_damping_summary.json`, `results/vw4_m028_imu_jerk_apm_summary.json`.

---

## Graph 2 — Dead-Reckoning / Navigation Performance (`navigation_error_comparison.png`)

- **Primary Metrics:** Integrated Position Error (meters) at 60s, 120s, and 300s outage horizons [Test Set, Lower is Better]
- **Visualization:** Line Chart (ordered time degradation: $60\text{ s} \to 120\text{ s} \to 300\text{ s}$)
- **Values Across the 6 Stages:**

| Stage | Milestone | 60s Outage Error | 120s Outage Error | 300s Outage Error |
|---|---|---:|---:|---:|
| **Stage 1** | `M003` Baseline | $350.00\text{ m}$ | $850.00\text{ m}$ | $1,465.00\text{ m}$ |
| **Stage 2** | `M004` SpeedNet v2 | $22.80\text{ m}$ | $440.20\text{ m}$ | $263.11\text{ m}$ |
| **Stage 3** | `M013` Constraint | $26.70\text{ m}$ | $464.00\text{ m}$ | $254.12\text{ m}$ |
| **Stage 4** | `M014` ZUPT | $27.40\text{ m}$ | $428.50\text{ m}$ | $233.18\text{ m}$ |
| **Stage 5** | `M019` APM | $27.50\text{ m}$ | $428.80\text{ m}$ | $220.12\text{ m}$ |
| **Stage 6** | `M028/M040` Final | **$27.35\text{ m}$** | **$426.85\text{ m}$** | **$218.93\text{ m}$** |

- **Why Line Chart is Used:** The line chart visually communicates trajectory drift growth over time, demonstrating how physical layer constraints (NHC, ZUPT, APM, Jerk Gating) flatten the error curve at long outage horizons.
- **Source Artifacts:** `milestones/M003_speednet_v1_baseline.md`, `results/vw4_orientation_anchor_summary.json`, `results/vw4_m013_hard_physical_inference_constraint_summary.json`, `results/vw4_m014_zupt_velocity_update_summary.json`, `results/vw4_m019_apm_speed_damping_summary.json`, `results/vw4_m028_imu_jerk_apm_summary.json`.

---

## Graph 3 — Heading / Orientation Performance (`heading_orientation_comparison.png`)

- **Primary Metric:** Mean Heading Error (degrees) over the 300s outage horizon [Test Set]
- **Visualization:** Bar Chart (discrete stage comparison)
- **Values Across the 6 Stages:**
  - Stage 1 (`M003`): **$68.42^\circ$** (Open-loop integrated heading error)
  - Stage 2 (`M004`): **$64.60^\circ$** (Raw gyro integrated heading error)
  - Stage 3 (`M013`): **$64.60^\circ$** (Raw gyro integrated heading error)
  - Stage 4 (`M014`): **$64.60^\circ$** (Raw gyro integrated heading error)
  - Stage 5 (`M019`): **$64.60^\circ$** (Raw gyro integrated heading error)
  - Stage 6 (`M028/M040`): **$64.60^\circ$** (Raw gyro integrated heading error)
- **Scientific Context & Explanation:**
  Heading propagation across stages 2 through 6 relies on raw gyroscope integration ($\dot{\psi} = \omega_y$).
  Milestone `M015` evaluated causal zero-velocity heading bias estimation (ZARU), reducing mean heading error to $36.1^\circ$. However, `M015` **degraded 300s position drift to $324.70\text{ m}$ (+39.2% degradation)** and was rejected because reducing heading error in isolation destroyed the EKF geometric path-length self-cancellation mechanism.
- **Source Artifacts:** `milestones/M003_speednet_v1_baseline.md`, `milestones/M004_speednet_v2_baseline.md`, `milestones/M015_heading_bias_and_turn_aware_fusion.md`.

---

## Data Provenance & Verification

Every numerical metric plotted in these three charts is locked to provenance-controlled project records:
- `M003`: `results/vw4_ml_dr_integration_report.md`
- `M004`: `results/vw4_orientation_anchor_summary.json`
- `M013`: `results/vw4_m013_hard_physical_inference_constraint_summary.json`
- `M014`: `results/vw4_m014_zupt_velocity_update_summary.json`
- `M019`: `results/vw4_m019_apm_speed_damping_summary.json`
- `M028/M040`: `results/vw4_m028_imu_jerk_apm_summary.json` & `results/vw4_m040_counterfactual_consistency_audit_summary.json`

---

## Important Scientific Corrections & Audit Findings

1. **M039 vs M040 Counterfactual Audit:**
   `M039` contained implementation bugs in counterfactual trajectory calculations. `M040` resolved these issues, proving that pure Ground-Truth Speed + Ground-Truth Heading kinematic integration achieves **$5.64\text{ m}$** error at 300s.
2. **EKF Geometric Self-Cancellation:**
   Inside the production EKF, replacing SpeedNet speed measurement with exact Ground-Truth Speed degrades 300s position error to **$511.62\text{ m}$** (+133.7% degradation). This proves that SpeedNet speed overestimation (+6.4 km/h) and gyro heading drift actively self-cancel in 2D DR integration.
3. **Diagnostic Status:**
   `M040` counterfactuals are offline diagnostic evaluations and are NOT treated as production stages.
4. **Final Production Benchmark:**
   The locked active production benchmark remains:
   $$\mathbf{60s = 27.35\text{ m} \quad | \quad 120s = 426.85\text{ m} \quad | \quad 300s = 218.93\text{ m}}$$
