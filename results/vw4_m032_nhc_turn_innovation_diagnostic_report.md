# Milestone M032 — NHC Turn-Innovation Diagnostic Report

## Executive Summary

- **Milestone:** M032 — NHC Turn-Innovation Diagnostic
- **Objective:** Perform a diagnostic investigation of Non-Holonomic Constraint (NHC) measurement innovations ($y_{\text{nhc}} = 0.0 - v_{\text{lat}}$) and Normalized Innovation Squared (NIS) across turn regimes ($|\omega_y| \le 5^\circ/\text{s}$, $5 < |\omega_y| \le 10^\circ/\text{s}$, $|\omega_y| > 10^\circ/\text{s}$) to evaluate whether turn-aware NHC covariance relaxation is scientifically justified.
- **Verdict:** **BRANCH CLOSED (PERMANENT CLOSURE OF TURN-AWARE NHC RELAXATION)**.
- **Key Findings:**
  - **M028 Baseline Control Reproduction:** **100% Exact Match** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s, **`218.93 m` @ 300s**).
  - **Straight Driving Nominality:** During straight motion ($|\omega_y| \le 5^\circ/\text{s}$), NHC operates in perfect nominal equilibrium ($\text{MAE} = 0.05 - 0.09\text{ m/s}$, Mean NIS = $0.28 - 0.50$, $\chi^2$ exceedance = $1.7\% - 2.6\%$).
  - **Strong Turn Innovation Elevation:** During strong turns ($|\omega_y| > 10^\circ/\text{s}$), NHC MAE increases to $0.60 - 0.72\text{ m/s}$ ($r = +0.8240$ correlation with $|\omega_y|$), elevating Mean NIS to $8.77 - 12.35$ ($\chi^2$ exceedance = $45.7\% - 55.8\%$).
  - **Physical Mechanism & M026 Cross-Reference:** Elevated NHC innovation during turns reflects centripetal acceleration ($a_y = v \cdot \omega$) and minor chassis body slip. However, as proven in **Milestone M026**, relaxing $R_{\text{nhc}}$ destroys lateral velocity anchoring, causing cross-track position error to explode by **$+422.0\%$** ($124.23 \rightarrow 1061.27\text{ m}$).
  - **Final Branch Closure:** Tight fixed NHC ($R_0 = 0.04\text{ m}^2/\text{s}^2$) is mandatory for 2D DR stability. Re-inflating $R_{\text{nhc}}$ during turns is disproved. **The turn-aware NHC covariance branch is permanently closed**.
  - **Active Verified Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## Benchmark & Diagnostic Scope Lock

- **Active Benchmark:** SpeedNet v2 W=40 + Raw Gyro + Fixed NHC + M013 F4 + M014 ZUPT + M019 APM + M028 Jerk Gate = **`218.93 m` @ 300s** (60s = `27.35 m`, 120s = `426.85 m`).
- **Diagnostic Constraint:** M032 is strictly an offline diagnostic. No changes were made to EKF state, NHC covariance, ZUPT updates, SpeedNet weights, or outage integration.

---

## Validation Set NHC Innovation & NIS Diagnostics (`88566:107535`)

- Total Validation Outage Samples: 2,000 (200.0 s @ 10 Hz)

| Turn Regime | Sample Count | Duration (s) | Signed Mean $y$ (m/s) | MAE (m/s) | RMSE (m/s) | P95 $|y|$ (m/s) | Mean NIS | Median NIS | P95 NIS | $\chi^2_{0.95}$ Exceedance (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Straight ($|\omega_y| \le 5^\circ/\text{s}$)** | 1,311 | 131.1 s | $+0.0048$ | $0.0920$ | $0.1825$ | $0.3662$ | $0.4982$ | $0.0089$ | $1.9741$ | **2.59%** |
| **Moderate Turn ($5 < |\omega_y| \le 10^\circ/\text{s}$)** | 539 | 53.9 s | $-0.0080$ | $0.2570$ | $0.3578$ | $0.7198$ | $1.9094$ | $0.5946$ | $7.5869$ | **11.69%** |
| **Strong Turn ($|\omega_y| > 10^\circ/\text{s}$)** | 1,150 | 115.0 s | $-0.0628$ | $0.5976$ | $0.7700$ | $1.6481$ | $8.7746$ | $3.2751$ | $40.4129$ | **45.74%** |
| **-> Entering Strong Turn ($\frac{d|\omega_y|}{dt} > +2$)** | 756 | 75.6 s | $-0.0454$ | $0.5874$ | $0.7664$ | $1.6520$ | $8.6843$ | $2.9719$ | $40.4786$ | **44.31%** |
| **-> Peak Strong Turn ($|\frac{d|\omega_y|}{dt}| \le 2$)** | 25 | 2.5 s | $+0.0734$ | $0.6373$ | $0.8438$ | $1.3388$ | $10.4058$ | $3.9921$ | $26.8419$ | **52.00%** |
| **-> Exiting Strong Turn ($\frac{d|\omega_y|}{dt} < -2$)** | 369 | 36.9 s | $-0.1075$ | $0.6159$ | $0.7723$ | $1.6126$ | $8.8491$ | $3.5601$ | $38.7053$ | **48.24%** |

---

## Locked Unseen Test Set NHC Innovation & NIS Diagnostics (`108,000 : 111,000`)

- Total Test Outage Samples: 3,000 (300.0 s @ 10 Hz)

| Turn Regime | Sample Count | Duration (s) | Signed Mean $y$ (m/s) | MAE (m/s) | RMSE (m/s) | P95 $|y|$ (m/s) | Mean NIS | Median NIS | P95 NIS | $\chi^2_{0.95}$ Exceedance (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Straight ($|\omega_y| \le 5^\circ/\text{s}$)** | 1,795 | 179.5 s | $+0.0075$ | $0.0499$ | $0.1385$ | $0.3058$ | $0.2862$ | $0.0000$ | $1.3951$ | **1.67%** |
| **Moderate Turn ($5 < |\omega_y| \le 10^\circ/\text{s}$)** | 368 | 36.8 s | $+0.0463$ | $0.2699$ | $0.3669$ | $0.7178$ | $2.0042$ | $0.6295$ | $7.7589$ | **15.22%** |
| **Strong Turn ($|\omega_y| > 10^\circ/\text{s}$)** | 837 | 83.7 s | $-0.0760$ | $0.7177$ | $0.9152$ | $1.9268$ | $12.3470$ | $5.0932$ | $54.4965$ | **55.79%** |
| **-> Entering Strong Turn ($\frac{d|\omega_y|}{dt} > +2$)** | 569 | 56.9 s | $-0.0790$ | $0.7055$ | $0.9086$ | $1.9195$ | $12.1650$ | $4.5085$ | $53.5789$ | **53.78%** |
| **-> Peak Strong Turn ($|\frac{d|\omega_y|}{dt}| \le 2$)** | 12 | 1.2 s | $-0.0910$ | $0.6352$ | $0.7025$ | $1.0473$ | $7.2818$ | $5.8411$ | $16.7289$ | **58.33%** |
| **-> Exiting Strong Turn ($\frac{d|\omega_y|}{dt} < -2$)** | 256 | 25.6 s | $-0.0685$ | $0.7486$ | $0.9382$ | $1.9353$ | $12.9890$ | $6.3893$ | $55.5195$ | **60.16%** |

---

## Correlation Analysis

- **Validation Set Correlations:**
  - Yaw Rate $|\omega_y|$ vs $|y_{\text{nhc}}|$: $r = +0.7418$ | $r(\text{NIS}) = +0.6526$
  - SpeedNet Speed $v_{\text{speednet}}$ vs $|y_{\text{nhc}}|$: $r = +0.4817$ | $r(\text{NIS}) = +0.3150$
  - Absolute Heading Error $|\Delta \psi|$ vs $|y_{\text{nhc}}|$: $r = +0.0339$ | $r(\text{NIS}) = -0.0306$
- **Locked Test Set Correlations:**
  - Yaw Rate $|\omega_y|$ vs $|y_{\text{nhc}}|$: $r = +0.8240$ | $r(\text{NIS}) = +0.7399$
  - SpeedNet Speed $v_{\text{speednet}}$ vs $|y_{\text{nhc}}|$: $r = +0.6198$ | $r(\text{NIS}) = +0.3860$
  - Absolute Heading Error $|\Delta \psi|$ vs $|y_{\text{nhc}}|$: $r = -0.1565$ | $r(\text{NIS}) = -0.0490$

---

## Scientific Interpretation & Cross-Reference to M026

1. **Kinematic Origin of Turn Innovation:** NHC innovation magnitude is strongly correlated with yaw rate ($r = +0.8240$). During turns, centripetal acceleration ($a_y = v \cdot \omega$) generates physical body acceleration.
2. **Why Modifying NHC Covariance is Disproved (M026 Integration):** In Milestone M026, dynamic speed-dependent scaling of $R_{\text{nhc}}$ was evaluated and **REJECTED**. When $R_{\text{nhc}}$ is inflated during turns, EKF lateral velocity updates are suppressed. Without tight lateral velocity constraints ($R_0 = 0.04\text{ m}^2/\text{s}^2$), integrated cross-track position error explodes by **$+422.0\%$** ($124.23 \rightarrow 1061.27\text{ m}$).
3. **Conclusion:** Tight NHC is mandatory for 2D dead-reckoning stability. Re-inflating $R_{\text{nhc}}$ during turns is scientifically disproved.

---

## Final Decision & Branch Closure

Per protocol decision rules:
> *"M032 should recommend a future intervention ONLY IF strong turns show clearly elevated NHC innovation AND the evidence is strong enough to justify a carefully bounded experiment despite M026's previous failure. Otherwise: CLOSE THE TURN-AWARE NHC COVARIANCE BRANCH."*

- **Verdict:** **BRANCH CLOSED (PERMANENT CLOSURE OF TURN-AWARE NHC COVARIANCE RELAXATION)**.
- **Active Benchmark:** **`218.93 m` @ 300s remains the active verified project benchmark**.

---

## Research Artifacts & Exact Paths

- **Diagnostic Script:** [`scripts/vw4_m032_nhc_turn_innovation_diagnostic.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_m032_nhc_turn_innovation_diagnostic.py)
- **Summary JSON:** `results/vw4_m032_nhc_turn_innovation_diagnostic_summary.json`
- **Report Markdown:** [`results/vw4_m032_nhc_turn_innovation_diagnostic_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_m032_nhc_turn_innovation_diagnostic_report.md)
- **Plot Directory:** `plots/vw4/m032_nhc_turn_innovation_diagnostic/`
  - `nhc_innovation_time_series.png`

---

## Final Benchmark Lock

$$\text{\bf SpeedNet v2 } (W=40) + \text{\bf Raw Gyro} + \text{\bf Fixed NHC} + \text{\bf M013 F4} + \text{\bf M014 ZUPT} + \text{\bf M019 APM} + \text{\bf M028 Jerk Gate } (j_{\text{long}} < -1.00\text{ m/s}^3) = \mathbf{218.93\text{\bf ~m @ 300s}}$$
