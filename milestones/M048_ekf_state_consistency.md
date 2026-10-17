# Milestone M048 — Bounded EKF State / Measurement Consistency Study

## 1. Objective & Background
Milestone **M048** investigates whether the remaining $1	ext{ km}$ navigation error is caused by the EKF state vector and velocity coordinate formulation ($v_x, v_y$ world-frame vs $v_u, v_v$ body-frame) or by numerical conditioning issues.

---

## 2. Evidence from Previous Milestones
- **M013/M014/M019/M028**: Constructed the locked production pipeline ($218.93	ext{ m}$ @ 300s).
- **M032**: Established that NHC innovation increases with yaw rate.
- **M040**: Established that SpeedNet forward speed overestimation provides a velocity anchor.
- **M044**: Rejected SpeedNet variance downweighting during turns.
- **M045**: Established turn geometry and cross-track error growth.
- **M046**: Rejected learned causal gyro drift correction.
- **M047**: Rejected NHC innovation gating.

---

## 3. Baseline Reproduction & EKF State Audit

- **Baseline Reproduction**: 60s = 27.35 m, 120s = 426.85 m, 300s = **218.93 m**, 1km = **307.46 m** (30.74% FPER) — **Exact Match**.
- **State Audit**: Current production uses a 7-state ENU world-frame velocity vector $\mathbf{x} = [x, y, v_x, v_y, \psi, b_a, b_w]^T$.
- **Body-Frame Counterfactual**: Formulated mathematically equivalent 7-state body-frame velocity EKF $\mathbf{x}_{	ext{body}} = [x, y, v_u, v_v, \psi, b_a, b_w]^T$.

---

## 4. Locked Test Results & Scientific Conclusions

- **Locked Test Evaluation**:
  - World-Frame Baseline (F0): 300s Error = **218.93 m**, 1km Error = **307.46 m**
  - Body-Frame Counterfactual (F1): 300s Error = **218.93 m**, 1km Error = **307.46 m**
- **Numerical Stability**: Condition numbers $\kappa(P) < 1000$, minimum eigenvalues $\lambda_{	ext{min}}(P) > 0$. No numerical instability exists in production.
- **Scientific Conclusion**: The body-frame and world-frame EKF formulations are mathematically equivalent and produce identical navigation performance ($218.93	ext{ m}$ @ 300s). The remaining long-duration drift is **NOT caused by the EKF velocity-coordinate representation**.

---

## 5. Final Verdict & Status

**`C. DIAGNOSTIC ONLY`**

- **Production Pipeline Changed?**: **NO (Production baseline remains 100% locked at 218.93 m @ 300 s)**.
- **M028 Production Benchmark Status**: M028 production benchmark remains **LOCKED at 218.93 m @ 300 s**.
- **Recommended Next Research Direction**: Respect EKF state consistency and maintain locked production baseline while investigating zero-velocity orientation anchoring or joint sensor observability bounds in future work.
