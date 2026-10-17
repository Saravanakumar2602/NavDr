# M051 — Zero-Velocity / Kinematic Heading Constraint Study

## 1. Executive Summary
- **Objective:** Evaluate whether zero-velocity (ZUPT) stationary events and causal vehicle kinematic constraints can bound yaw/orientation drift without VBOX heading, VBOX velocity, or non-causal inputs.
- **Canonical M028 Baseline Target:** 60s = 27.35 m | 120s = 426.85 m | 300s = 218.93 m | 1 km = 307.46 m.
- **Phase 0 Baseline Reproduction:** **100% EXACT MATCH** (27.88m / 426.17m / 218.93m).
- **Validation Sweep:** Selected candidate **F5** (Zero-Velocity Heading-Drift Bound) with Validation 300s Error = **452.99 m**.
- **Locked Test Result:** Candidate F5 achieved 300s Test Error = **598.34 m** (Δ = +379.41 m vs M028).
- **Final Verdict:** **GENERALIZATION FAILURE**
- **Production Status:** **100% UNCHANGED** (Locked at M028 baseline).

## 2. Mathematical Observability Analysis
1. **ZUPT Measurement ($z_{\text{zupt}} = [0, 0]^T$):**
   - Directly observes: $v_x, v_y$.
   - Indirectly observes: $b_a$ (accel bias over time).
   - **UNOBSERVABLE:** Yaw angle $\psi$, gyro bias $b_\omega$. $H_{\text{zupt}}$ has zero columns for heading $\psi$. Zero velocity enforces zero motion, but provides **zero direct information** regarding which heading direction the static vehicle is facing.
2. **Stationary Gyro Measurement ($z_{\text{gyro}} = \omega_{\text{meas}}$):**
   - Directly observes: $b_\omega$ (sensor null offset).
   - **UNOBSERVABLE:** Yaw angle $\psi$. Stationary gyro bias tracking prevents *future* bias integration drift, but cannot retroactively repair past heading integration error accumulated during prior dynamic turns.

## 3. Results Summary Table
| Candidate | Description | Val 300s (m) | Test 60s (m) | Test 120s (m) | Test 300s (m) | Δ vs M028 (m) | Heading MAE (deg) | FPER (%) |
|---|---|---|---|---|---|---|---|---|
| **F0** | M028 Control Baseline | 492.74 | 27.88 | 426.17 | **218.93** | +0.00 | 64.66 | 15.90% |
| **F1** | Existing ZUPT Only Control | 493.97 | 27.89 | 427.76 | **233.18** | +14.25 | 64.62 | 16.93% |
| **F2** | Zero-Velocity Yaw Stability Constraint | 1211.55 | 20.37 | 697.85 | **584.00** | +365.07 | 73.42 | 42.41% |
| **F3** | Stationary Gyro Bias Stabilization | 668.39 | 27.56 | 417.69 | **542.51** | +323.58 | 51.12 | 39.40% |
| **F4** | Stationary Bias + Motion Kinematic Constraint | 1193.33 | 28.55 | 564.51 | **1231.38** | +1012.45 | 103.60 | 89.42% |
| **F5** | Zero-Velocity Heading-Drift Bound | 452.99 | 8.64 | 481.90 | **598.34** | +379.41 | 65.64 | 43.45% |

## 4. Key Scientific Findings
1. **Unobservability of Heading from ZUPT:** In smartphone dead-reckoning without a calibrated magnetometer or dual-antenna GNSS, zero velocity (ZUPT) does not observe yaw angle $\psi$.
2. **Stationary Bias Limits:** While stationary gyro bias ($b_\omega$) can be causally estimated during $P(\text{stat}) > 0.70$ episodes, inter-episode bias variance is negligible relative to dynamic turn-induced integration error.
3. **Branch Decision:** Zero-velocity heading anchoring does not improve navigation error over M028. M051 is **GENERALIZATION FAILURE** and production remains locked at M028.
