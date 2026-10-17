# Milestone M025 — Pitch-Tilt-Compensated Longitudinal Acceleration for APM Report

## Executive Summary

- **Milestone:** M025 — Pitch-Tilt-Compensated Longitudinal Acceleration for APM
- **Objective:** Evaluate whether explicit pitch-tilt gravity compensation ($a_{\text{long,comp}} = a_{\text{long}} - g \sin\theta_{\text{pitch}}$) improves M019 APM acceleration integration during straight-line braking episodes ($a_{\text{long}} < -0.5\text{ m/s}^2$) and lowers 300s position drift below $220.12\text{ m}$.
- **Verdict:** **REJECTED**.
- **Key Findings:**
  - **M019 Baseline Control Reproduction:** **100% Exact Match** ($27.53\text{ m}$ @ 60s, $428.79\text{ m}$ @ 120s, **`220.12 m` @ 300s**).
  - **Physics & Coordinate Audit:** In the dataset preprocessing pipeline, `a_long = -(raw_ay - grav_y)` already subtracts `grav_y` (the Android/iOS Sensor Fusion gravity vector along the longitudinal axis). The measured mean vehicle pitch during straight braking is near-zero ($\theta_{\text{pitch}} \approx +0.01^\circ$).
  - **Validation Selection:** Direct pitch compensation (F1) and smoothed pitch compensation (F2) slightly degraded 300s validation set position error ($505.61\text{ m}$ and $505.55\text{ m}$ vs Control $505.40\text{ m}$). The Validation-Selected Winner (F4) is the **Original M019 Baseline Control** (`505.40 m`).
  - **Locked Test Evaluation of Validation Winner:** Evaluated on the locked unseen test partition (`start_idx = 108,000`), Validation Winner F4 / F0 achieved **`220.12 m` @ 300s**, matching the control baseline ($0.0\%$).
  - **Active Verified Benchmark:** **`220.12 m` @ 300s remains the active verified project benchmark**.

---

## Physics & Coordinate System Audit

1. **IMU Axis Convention:** Smartphone Y-axis aligns with the vehicle's forward longitudinal axis. Negative raw acceleration $-raw\_ay$ corresponds to forward vehicle acceleration.
2. **Gravity Compensation:** The preprocessing pipeline computes `a_long = -(raw_ay - grav_y)`. Here, `grav_y` represents the gravity vector projection along the Y axis extracted from sensor fusion.
3. **Pitch Angle Measurement:** Pitch angle is computed as $\theta_{\text{acc}} = \arctan2(grav\_y, \sqrt{grav\_x^2 + grav\_z^2})$.
4. **Audit Finding:** Because `grav_y` is already subtracted in `a_long`, static gravity pitch component is already removed. Subtracting an additional $g \sin\theta_{\text{acc}}$ term induces slight double-counting of gravity tilt, providing no physical benefit and slightly degrading validation position accuracy.

---

## M019 Control Reproduction Verification

- **Target Benchmark (M019 F4 Active Best):**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Measured F0 Control:**
  - 60s Outage: `27.53 m`
  - 120s Outage: `428.79 m`
  - 300s Outage: `220.12 m`
- **Reproduction Status:** **100% Exact Match Confirmed**.

---

## Validation Pitch Compensation Evaluation (`88566:107535`)

| Candidate ID | Pitch Compensation Mode | Val 300s Position Error (m) | Selection Status |
|---|---|---|---|
| **F0 / F3 / F4** | **Original M019 Control (No Comp)** | **505.40 m** | **SELECTED VALIDATION BEST** |
| **F1** | Direct Pitch Comp ($a_{\text{long}} - g \sin\theta_{\text{acc}}$) | $505.61\text{ m}$ | Degraded (+0.04%) |
| **F2** | EMA-Smoothed Pitch Comp ($\alpha=0.90$) | $505.55\text{ m}$ | Degraded (+0.03%) |

---

## Experimental Candidate Sweep & Locked Unseen Test Results (`start_idx = 108,000`)

| Candidate ID | Configuration Description | Speed MAE | Brake MAE | 60s Outage | 120s Outage | 300s Outage | vs 263.11m Bench | vs 254.11m M013 | vs 220.12m M019 |
|---|---|---|---|---|---|---|---|---|---|
| **F0 (Control M019)** | M019 Baseline Control | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **CONTROL** |
| **F1** | Direct Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.54\text{ m}$ | $428.82\text{ m}$ | $219.59\text{ m}^*$ | $-16.5\%$ | $-13.6\%$ | $-0.2\%$ |
| **F2** | EMA-Smoothed Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.53\text{ m}$ | $428.77\text{ m}$ | $219.72\text{ m}^*$ | $-16.5\%$ | $-13.5\%$ | $-0.2\%$ |
| **F3** | Braking-Only Pitch Comp | $7.33\text{ km/h}$ | $11.54\text{ km/h}$ | $27.53\text{ m}$ | $428.79\text{ m}$ | $220.12\text{ m}$ | $-16.3\%$ | $-13.4\%$ | $0.0\%$ |
| **F4 (Val Winner)** | Selected Best Validation (F0) | **7.33 km/h** | **11.54 km/h** | **27.53 m** | **428.79 m** | **220.12 m** | **-16.3%** | **-13.4%** | **0.0%** |

*\*Note: F1 and F2 were degraded on Validation ($505.61\text{ m}$ and $505.55\text{ m}$ vs F0 $505.40\text{ m}$). Under zero-leakage protocol rules, non-validation winners cannot replace the benchmark.*

---

## APM Pitch Diagnostics Summary

| Candidate | Total Activations | Mean Braking Pitch Angle | Mean APM Speed Correction |
|---|---|---|---|
| **F0 Control (No Comp)** | 118 | $+0.01^\circ$ | $1.73\text{ km/h}$ |
| **F1 (Direct Comp)** | 118 | $+0.01^\circ$ | $1.73\text{ km/h}$ |
| **F2 (Smoothed Comp)** | 118 | $+0.01^\circ$ | $1.73\text{ km/h}$ |
| **F3 (Braking Only)** | 118 | $+0.01^\circ$ | $1.73\text{ km/h}$ |

---

## Failure & Rejection Mechanism Analysis

1. **Redundancy of Gravity Subtraction:** Sensor fusion gravity vector `grav_y` already removes static pitch gravity bias from `a_long`. Additional explicit pitch angle compensation is redundant.
2. **Validation Protocol Selection:** All pitch compensation variants degraded 300s validation set position error ($505.61\text{ m}$ for F1 vs $505.40\text{ m}$ for Control). Under strict zero-leakage research rules, F0 Control remains the validation winner.

---

## Research Artifacts & Exact Paths

- **Implementation Script:** [`scripts/vw4_m025_pitch_tilt_apm.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m025_pitch_tilt_apm.py)
- **Summary JSON:** `results/vw4_m025_pitch_tilt_apm_summary.json`
- **Predictions NPZ:** `results/vw4_m025_pitch_tilt_apm_predictions.npz`
- **Report Markdown:** [`results/vw4_m025_pitch_tilt_apm_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m025_pitch_tilt_apm_report.md)
- **Plot Directory:** `plots/vw4/m025_pitch_tilt_apm/`
  - `pos_error_vs_time.png`
  - `trajectory_comparison.png`

---

## Final M025 Verdict & Active Benchmark

**REJECTED**.

The ACTIVE VERIFIED PROJECT BENCHMARK remains:

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM (0.5s, 0.50m/s)} = \mathbf{220.12\text{\bf ~m @ 300s}}$$
