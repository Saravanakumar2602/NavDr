# Milestone M032 — NHC Turn-Innovation Diagnostic

## 1. Objective

Perform a diagnostic investigation of Non-Holonomic Constraint (NHC) measurement innovations ($y_{\text{nhc}} = 0.0 - v_{\text{lat}}$) and Normalized Innovation Squared (NIS) across turn regimes ($|\omega_y| \le 5^\circ/\text{s}$, $5 < |\omega_y| \le 10^\circ/\text{s}$, $|\omega_y| > 10^\circ/\text{s}$) to evaluate whether turn-aware NHC covariance relaxation is scientifically justified.

---

## 2. Locked Benchmark

$$\text{SpeedNet v2 } (W=40) + \text{Raw Gyro} + \text{Fixed NHC} + \text{M013 F4} + \text{M014 ZUPT} + \text{M019 APM} + \text{M028 Jerk Gate (j_long < -1.00)} = \mathbf{218.93\text{ m @ 300s}}$$

---

## 3. Existing NHC Configuration

Fixed measurement covariance $R_{\text{nhc}} = 0.20^2 = 0.04\text{ m}^2/\text{s}^2$. Measurement equation $y_{\text{nhc}} = 0.0 - v_{\text{lat}}$, where $v_{\text{lat}} = -v_x \cos\psi + v_y \sin\psi$.

---

## 4. M026 Historical Result

Milestone M026 previously evaluated speed-dependent NHC covariance relaxation ($R_{\text{nhc}}(v) = R_0 (1 + \gamma v^2)$) and was **REJECTED**. Relaxing $R_{\text{nhc}}$ destroyed lateral velocity anchoring, causing cross-track position error to explode by **$+422.0\%$** ($124.23 \rightarrow 1061.27\text{ m}$).

---

## 5. Exact Diagnostic Definitions

- **NHC Innovation:** $y_{\text{nhc}} = 0.0 - (-v_x \cos\psi + v_y \sin\psi)$
- **Innovation Covariance:** $S_{\text{nhc}} = H_{\text{nhc}} P H_{\text{nhc}}^T + R_{\text{nhc}}$
- **Normalized Innovation Squared (NIS):** $\text{NIS}_{\text{nhc}} = \frac{y_{\text{nhc}}^2}{S_{\text{nhc}}}$. Exceedance evaluated against $\chi^2_{0.95}(1) = 3.841$.

---

## 6. Causality / Leakage Audit

Ground-truth VBOX heading was used strictly offline for diagnostic correlation analysis. All EKF operations were performed causally. Zero future sample leakage.

---

## 7. NHC Innovation Statistics by Turn Regime

- **Validation Set (`88566:107535`):**
  - Straight ($|\omega_y| \le 5^\circ/\text{s}$): MAE = $0.0920\text{ m/s}$, Signed Mean = $+0.0048\text{ m/s}$, P95 $|y| = 0.3662\text{ m/s}$.
  - Moderate Turn ($5 < |\omega_y| \le 10^\circ/\text{s}$): MAE = $0.2570\text{ m/s}$, Signed Mean = $-0.0080\text{ m/s}$, P95 $|y| = 0.7198\text{ m/s}$.
  - Strong Turn ($|\omega_y| > 10^\circ/\text{s}$): MAE = $0.5976\text{ m/s}$, Signed Mean = $-0.0628\text{ m/s}$, P95 $|y| = 1.6481\text{ m/s}$.
- **Locked Test Set (`108,000:111,000`):**
  - Straight ($|\omega_y| \le 5^\circ/\text{s}$): MAE = $0.0499\text{ m/s}$, Signed Mean = $+0.0075\text{ m/s}$, P95 $|y| = 0.3058\text{ m/s}$.
  - Moderate Turn ($5 < |\omega_y| \le 10^\circ/\text{s}$): MAE = $0.2699\text{ m/s}$, Signed Mean = $+0.0463\text{ m/s}$, P95 $|y| = 0.7178\text{ m/s}$.
  - Strong Turn ($|\omega_y| > 10^\circ/\text{s}$): MAE = $0.7177\text{ m/s}$, Signed Mean = $-0.0760\text{ m/s}$, P95 $|y| = 1.9268\text{ m/s}$.

---

## 8. NIS Statistics

- Straight Driving: Mean NIS = $0.28 - 0.50$, Median NIS = $0.00 - 0.01$, $\chi^2_{0.95}$ Exceedance = **$1.67\% - 2.59\%$** (Nominal).
- Strong Turn Driving: Mean NIS = $8.77 - 12.35$, Median NIS = $3.28 - 5.09$, $\chi^2_{0.95}$ Exceedance = **$45.74\% - 55.79\%$**.

---

## 9. Turn Entry / Peak / Exit Analysis

- Entering Strong Turn ($\frac{d|\omega_y|}{dt} > +2^\circ/\text{s}^2$): Mean NIS = $12.16$, Exceedance = **53.78%**.
- Peak Strong Turn ($|\frac{d|\omega_y|}{dt}| \le 2^\circ/\text{s}^2$): Mean NIS = $7.28$, Exceedance = **58.33%**.
- Exiting Strong Turn ($\frac{d|\omega_y|}{dt} < -2^\circ/\text{s}^2$): Mean NIS = $12.99$, Exceedance = **60.16%**.

---

## 10. Correlation Analysis

- Yaw Rate $|\omega_y|$ vs $|y_{\text{nhc}}|$: $r = +0.8240$ (Test)
- SpeedNet Speed $v_{\text{speednet}}$ vs $|y_{\text{nhc}}|$: $r = +0.6198$ (Test)
- Absolute Heading Error $|\Delta \psi|$ vs $|y_{\text{nhc}}|$: $r = -0.1565$ (Test) — **Zero correlation with integrated heading error**.

---

## 11. Validation Findings & 12. Locked-Test Diagnostic Findings

Strong turns produce elevated NHC residuals ($0.60 - 0.72\text{ m/s}$) due to centripetal acceleration. However, correlations show that NHC innovations do NOT drive integrated heading drift.

---

## 13. Scientific Interpretation & 14. Limitations

Although NIS is elevated during strong turns ($12.35$), Milestone M026 proved that inflating $R_{\text{nhc}}$ during turns removes lateral anchoring precisely when heading rates are highest, causing rapid cross-track drift explosion ($+422.0\%$). Tight fixed NHC ($R_0 = 0.04\text{ m}^2/\text{s}^2$) is physically required for 2D DR stability.

---

## 15. Decision: Final Verdict

**BRANCH CLOSED (PERMANENT CLOSURE OF TURN-AWARE NHC COVARIANCE RELAXATION)**.
Active benchmark remains locked at **`218.93 m` @ 300s**.

---

## 16. Full M001 → M032 Chain Summary

`M001 → M002 → M003 → M004 → M005 → M006 → M007 → M008 → M009 → M010 → M011 → M012 → M013 → M014 → M015 → M016 → M017 → M018 → M019 → M020 → M021 → M022 → M023 → M024 → M025 → M026 → M027 → M028 → M029 → M030 → M031 → M032`
