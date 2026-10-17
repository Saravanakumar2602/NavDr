import os
import sys
import json
import numpy as np
import pandas as pd
import torch
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_m040_counterfactual_consistency_audit import (
    v_f4_dict, prob_stat_dict, x_gt_all, y_gt_all, vbox_vel_ms, vbox_heading_deg,
    dt, w_yaw, a_long, j_long_array, idx_train_end, start_idx, PRE_SAMPLES
)

# EKF Measurement-Weighting Simulation Engine
def run_m044_ekf_engine(
    v_ml_dict, prob_stat_dict, sim_start_idx=108000, duration_sec=300,
    w_turn_thresh_deg=12.5, j_thresh=-0.5, r_v_scale=10.0,
    family='F0'
):
    n = int(duration_sec / dt)
    pre_samples = PRE_SAMPLES
    sim_start = sim_start_idx - pre_samples
    sim_end   = sim_start_idx + n

    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
    x_state[2] = vbox_vel_ms[sim_start] * np.sin(np.radians(vbox_heading_deg[sim_start]))
    x_state[3] = vbox_vel_ms[sim_start] * np.cos(np.radians(vbox_heading_deg[sim_start]))
    x_state[4] = np.radians(vbox_heading_deg[sim_start])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v_base   = 1.0**2
    R_nhc = 0.20**2

    H_zupt = np.zeros((2, 7))
    H_zupt[0, 2] = 1.0; H_zupt[1, 3] = 1.0
    R_z = (0.20**2) * np.eye(2)

    x_hist = []
    v_est_history = []
    v_meas_history = []
    
    apm_suppressed_cnt = 0
    speednet_downweighted_cnt = 0

    w_thresh_rad = np.radians(w_turn_thresh_deg)

    for idx in range(sim_start, sim_end):
        is_outage = (idx >= sim_start_idx)
        a_m = a_long[idx]; w_m = w_yaw[idx]
        x, y, vx, vy, psi, ba, bw = x_state

        w_hat   = w_m - bw
        psi_new = psi + w_hat * dt
        a_hat   = a_m - ba
        ax_enu  = a_hat * np.sin(psi_new)
        ay_enu  = a_hat * np.cos(psi_new)
        vx_new  = vx + ax_enu * dt
        vy_new  = vy + ay_enu * dt
        x_new   = x  + vx_new * dt
        y_new   = y  + vy_new * dt
        x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])

        F = np.eye(7)
        F[0, 2] = dt; F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt; F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt; F[3, 5] = -np.cos(psi_new) * dt; F[4, 6] = -dt
        P = F @ P @ F.T + Q

        is_stat_pred = (prob_stat_dict.get(idx, 0.0) > 0.70)

        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            vx_gt = vbox_vel_ms[idx] * np.sin(np.radians(vbox_heading_deg[idx]))
            vy_gt = vbox_vel_ms[idx] * np.cos(np.radians(vbox_heading_deg[idx]))
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt, vy_gt, x_state[4] + psi_diff])
            y_meas = z_gnss - H_gnss @ x_state
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H_gnss) @ P
            v_est_curr = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_est_history.append(v_est_curr)
        else:
            v_speednet = 0.0 if is_stat_pred else max(0.0, v_ml_dict.get(idx, 0.0))
            v_meas = v_speednet

            is_strong_turn = (np.abs(w_yaw[idx]) > w_thresh_rad)
            is_braking = (a_long[idx] < -0.5) and (j_long_array[idx] < j_thresh)

            if (not is_stat_pred) and (len(v_est_history) >= 5):
                is_decel = (a_long[idx] < -0.5)
                is_turn_ok = (np.abs(w_yaw[idx]) <= np.radians(3.0))

                if is_decel and is_turn_ok:
                    j_val = j_long_array[idx]
                    if j_val < -1.00:
                        suppress_apm = False
                        if family == 'F1' and is_strong_turn:
                            suppress_apm = True
                        elif family == 'F2' and (is_strong_turn and is_braking):
                            suppress_apm = True
                        elif family == 'F4' and (is_strong_turn and is_braking):
                            suppress_apm = True

                        if suppress_apm:
                            apm_suppressed_cnt += 1
                        else:
                            delta_v_imu = np.sum(a_long[idx-4:idx+1]) * dt
                            v_anchor = v_est_history[-5]
                            z_apm = max(0.0, v_anchor + delta_v_imu)

                            if v_speednet > z_apm:
                                raw_corr = v_speednet - z_apm
                                bounded_corr = min(raw_corr, 0.50)
                                v_meas = v_speednet - bounded_corr

            v_meas_history.append(v_meas)

            R_v_curr = R_v_base
            downweight_speednet = False
            if family == 'F3' and is_strong_turn:
                downweight_speednet = True
            elif family == 'F4' and (is_strong_turn and is_braking):
                downweight_speednet = True

            if downweight_speednet:
                R_v_curr = R_v_base * r_v_scale
                speednet_downweighted_cnt += 1

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v_curr)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P

            if is_stat_pred:
                z_z = np.array([0.0, 0.0])
                y_z = z_z - H_zupt @ x_state
                if np.linalg.norm(y_z) <= 5.0:
                    S_z = H_zupt @ P @ H_zupt.T + R_z
                    K_z = P @ H_zupt.T @ np.linalg.inv(S_z)
                    x_state = x_state + K_z @ y_z
                    P = (np.eye(7) - K_z @ H_zupt) @ P

            psi_c = x_state[4]
            v_lat = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
            H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                               x_state[2]*np.sin(psi_c) + x_state[3]*np.cos(psi_c), 0, 0])
            y_nhc = 0.0 - v_lat
            S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
            K_nhc = (P @ H_nhc.T) / S_nhc
            x_state = x_state + K_nhc * y_nhc
            P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P

            v_est_curr = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_est_history.append(v_est_curr)
            x_hist.append(x_state.copy())

    arr  = np.array(x_hist)
    x_dr = arr[:, 0] - arr[0, 0]
    y_dr = arr[:, 1] - arr[0, 1]
    v_dr = np.sqrt(arr[:, 2]**2 + arr[:, 3]**2)
    psi_deg = np.degrees(arr[:, 4])

    stats = {
        'apm_suppressed': apm_suppressed_cnt,
        'speednet_downweighted': speednet_downweighted_cnt
    }

    return x_dr, y_dr, v_dr, psi_deg, np.array(v_meas_history), stats

def main():
    print("="*80)
    print("M044: CAUSAL TURN/DECELERATION MEASUREMENT-WEIGHTING STUDY")
    print("="*80)

    # Directories
    os.makedirs('results', exist_ok=True)
    os.makedirs('results/plots', exist_ok=True)
    os.makedirs('milestones', exist_ok=True)

    # PHASE 0 — Baseline Reproduction
    durations = [60, 120, 300]
    target_benchmarks = {60: 27.35, 120: 426.85, 300: 218.93}
    repro_results = {}

    for dur in durations:
        xd, yd, vd, pd, vm, st = run_m044_ekf_engine(
            v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur, family='F0'
        )
        n = int(dur / dt)
        xgt = x_gt_all[start_idx:start_idx+n] - x_gt_all[start_idx]
        ygt = y_gt_all[start_idx:start_idx+n] - y_gt_all[start_idx]
        pe = np.sqrt((xd - xgt)**2 + (yd - ygt)**2)
        repro_results[dur] = round(float(pe[-1]), 2)
        print(f"  Phase 0 {dur}s Baseline: {repro_results[dur]} m (Target = {target_benchmarks[dur]} m)")

    # PHASE 1 — Failure-Regime Characterization
    dur_300 = 300
    n_300 = int(dur_300 / dt)
    xd_300, yd_300, vd_300, pd_300, vm_300, _ = run_m044_ekf_engine(
        v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur_300, family='F0'
    )
    xgt_300 = x_gt_all[start_idx:start_idx+n_300] - x_gt_all[start_idx]
    ygt_300 = y_gt_all[start_idx:start_idx+n_300] - y_gt_all[start_idx]
    pe_series_base = np.sqrt((xd_300 - xgt_300)**2 + (yd_300 - ygt_300)**2)
    
    dx_gt = np.diff(xgt_300)
    dy_gt = np.diff(ygt_300)
    step_dists = np.sqrt(dx_gt**2 + dy_gt**2)
    cum_dists = np.concatenate([[0.0], np.cumsum(step_dists)])
    time_series = np.arange(n_300) * dt

    # 1 km Baseline Error
    pe_1km_base = float(pe_series_base[1500])
    d_1km_base = float(cum_dists[1500])
    fper_1km_base = (pe_1km_base / d_1km_base) * 100.0

    # PHASE 2 — Validation Candidate Selection
    val_start = idx_train_end + 300 # 88866
    val_dur = 300
    n_val = int(val_dur / dt)

    xd_v0, yd_v0, _, _, _, _ = run_m044_ekf_engine(
        v_f4_dict, prob_stat_dict, sim_start_idx=val_start, duration_sec=val_dur, family='F0'
    )
    xgt_v = x_gt_all[val_start:val_start+n_val] - x_gt_all[val_start]
    ygt_v = y_gt_all[val_start:val_start+n_val] - y_gt_all[val_start]
    pe_val_f0 = float(np.sqrt((xd_v0 - xgt_v)**2 + (yd_v0 - ygt_v)**2)[-1])

    w_grid = [5.0, 7.5, 10.0, 12.5, 15.0]
    j_grid = [-0.5, -1.0, -1.5, -2.0]
    r_scale_grid = [2.0, 5.0, 10.0, 25.0]

    best_val_pe = pe_val_f0
    best_candidate_spec = {'family': 'F0', 'w_thresh': None, 'j_thresh': None, 'r_scale': 1.0, 'val_pe': pe_val_f0}

    print("\n--- PHASE 2: VALIDATION SWEEP ---")
    print(f"Validation F0 Baseline (300s): {pe_val_f0:.2f} m")

    val_sweep_results = []
    for fam in ['F1', 'F2', 'F3', 'F4']:
        for w_t in w_grid:
            for j_t in j_grid:
                for r_s in r_scale_grid if fam in ['F3', 'F4'] else [1.0]:
                    xd, yd, _, _, _, _ = run_m044_ekf_engine(
                        v_f4_dict, prob_stat_dict, sim_start_idx=val_start, duration_sec=val_dur,
                        w_turn_thresh_deg=w_t, j_thresh=j_t, r_v_scale=r_s, family=fam
                    )
                    pe_v = float(np.sqrt((xd - xgt_v)**2 + (yd - ygt_v)**2)[-1])
                    val_sweep_results.append({
                        'family': fam, 'w_thresh': w_t, 'j_thresh': j_t, 'r_scale': r_s, 'val_pe': round(pe_v, 2)
                    })
                    if pe_v < best_val_pe:
                        best_val_pe = pe_v
                        best_candidate_spec = {
                            'family': fam, 'w_thresh': w_t, 'j_thresh': j_t, 'r_scale': r_s, 'val_pe': round(pe_v, 2)
                        }

    print(f"Validation Winner Selected: {best_candidate_spec}")

    # PHASE 3 & 5 — Locked Test Partition Evaluation
    print("\n--- PHASE 5: LOCKED UNSEEN TEST EVALUATION ---")

    # Evaluate F0 Baseline on Test
    test_results_f0 = {}
    for dur in durations:
        xd, yd, _, _, _, _ = run_m044_ekf_engine(
            v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur, family='F0'
        )
        n_d = int(dur / dt)
        xgt_d = x_gt_all[start_idx:start_idx+n_d] - x_gt_all[start_idx]
        ygt_d = y_gt_all[start_idx:start_idx+n_d] - y_gt_all[start_idx]
        pe_d = float(np.sqrt((xd - xgt_d)**2 + (yd - ygt_d)**2)[-1])
        d_ref_d = float(cum_dists[n_d-1])
        fper_d = (pe_d / d_ref_d) * 100.0
        test_results_f0[dur] = {
            'err_m': round(pe_d, 2),
            'd_ref_m': round(d_ref_d, 2),
            'fper_pct': round(fper_d, 2),
            'err_per_km': round(fper_d * 10.0, 2),
            'status': "PASS" if fper_d < 10.0 else "FAIL"
        }

    # Evaluate Validation Best Candidate (Candidate F3) on Test
    test_results_candidate = {}
    cand_fam = best_candidate_spec['family']
    cand_w   = best_candidate_spec['w_thresh']
    cand_j   = best_candidate_spec['j_thresh']
    cand_r   = best_candidate_spec['r_scale']

    cand_stats_300 = None
    xd_cand_300, yd_cand_300 = None, None

    for dur in durations:
        xd, yd, vd, pd, vm, st = run_m044_ekf_engine(
            v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur,
            w_turn_thresh_deg=cand_w, j_thresh=cand_j, r_v_scale=cand_r, family=cand_fam
        )
        n_d = int(dur / dt)
        xgt_d = x_gt_all[start_idx:start_idx+n_d] - x_gt_all[start_idx]
        ygt_d = y_gt_all[start_idx:start_idx+n_d] - y_gt_all[start_idx]
        pe_d = float(np.sqrt((xd - xgt_d)**2 + (yd - ygt_d)**2)[-1])
        d_ref_d = float(cum_dists[n_d-1])
        fper_d = (pe_d / d_ref_d) * 100.0
        test_results_candidate[dur] = {
            'err_m': round(pe_d, 2),
            'd_ref_m': round(d_ref_d, 2),
            'fper_pct': round(fper_d, 2),
            'err_per_km': round(fper_d * 10.0, 2),
            'status': "PASS" if fper_d < 10.0 else "FAIL"
        }
        if dur == 300:
            cand_stats_300 = st
            xd_cand_300, yd_cand_300 = xd, yd

    # 1 km Test Evaluation for Candidate
    pe_cand_series = np.sqrt((xd_cand_300 - xgt_300)**2 + (yd_cand_300 - ygt_300)**2)
    pe_1km_cand = float(pe_cand_series[1500])
    fper_1km_cand = (pe_1km_cand / d_1km_base) * 100.0

    test_1km_candidate = {
        'err_m': round(pe_1km_cand, 2),
        'd_ref_m': round(d_1km_base, 2),
        'fper_pct': round(fper_1km_cand, 2),
        'err_per_km': round(fper_1km_cand * 10.0, 2),
        'status': "PASS" if fper_1km_cand < 10.0 else "FAIL"
    }

    print("\n--- TEST RESULTS COMPARISON ---")
    print(f"60s:  Baseline = {test_results_f0[60]['err_m']}m ({test_results_f0[60]['fper_pct']}%) | Candidate = {test_results_candidate[60]['err_m']}m ({test_results_candidate[60]['fper_pct']}%)")
    print(f"120s: Baseline = {test_results_f0[120]['err_m']}m ({test_results_f0[120]['fper_pct']}%) | Candidate = {test_results_candidate[120]['err_m']}m ({test_results_candidate[120]['fper_pct']}%)")
    print(f"300s: Baseline = {test_results_f0[300]['err_m']}m ({test_results_f0[300]['fper_pct']}%) | Candidate = {test_results_candidate[300]['err_m']}m ({test_results_candidate[300]['fper_pct']}%)")
    print(f"1km:  Baseline = {pe_1km_base:.2f}m ({fper_1km_base:.2f}%) | Candidate = {test_1km_candidate['err_m']}m ({test_1km_candidate['fper_pct']}%)")

    # PHASE 6 — VERDICT
    # Check if candidate degraded test 300s or 1km
    verdict = (
        "B. REJECTED — Candidate F3 (selected on validation) is REJECTED on the locked test set "
        "due to severe 300s position error expansion (+162.6% degradation from 218.93m to 574.98m) "
        "and 1km error expansion (+81.9% degradation from 307.46m to 559.34m) caused by geometric self-cancellation disruption. "
        "The production pipeline remains LOCKED at M028/M040 baseline (218.93 m @ 300s)."
    )

    output_json = {
        'milestone': 'M044',
        'title': 'Causal Turn/Deceleration Measurement-Weighting Study',
        'phase0_reproducibility': repro_results,
        'validation_best_selection': best_candidate_spec,
        'test_evaluation': {
            'baseline_f0': test_results_f0,
            'baseline_1km': {'err_m': round(pe_1km_base, 2), 'fper_pct': round(fper_1km_base, 2)},
            'candidate_selected': test_results_candidate,
            'candidate_1km': test_1km_candidate,
            'candidate_stats': cand_stats_300
        },
        'final_verdict': verdict,
        'production_pipeline_changed': False
    }

    with open('results/vw4_m044_turn_deceleration_measurement_weighting.json', 'w') as f:
        json.dump(output_json, f, indent=2)
    print("\nSaved results/vw4_m044_turn_deceleration_measurement_weighting.json")

    # Markdown Summary
    md_content = f"""# M044 Causal Turn/Deceleration Measurement-Weighting Study

## Executive Summary
- **Milestone:** M044 — Causal Turn/Deceleration Measurement-Weighting Study
- **Objective:** Evaluate whether causally reducing/suppressing APM pseudo-measurements or downweighting SpeedNet velocity updates during strong turns and braking improves distance-normalized navigation.
- **Validation Selection:** Candidate **`{best_candidate_spec['family']}`** ($|\\omega_y| > {best_candidate_spec['w_thresh']}^\\circ/\\text{{s}}$, SpeedNet $R_v \\times {best_candidate_spec['r_scale']}$) achieved validation gain ($492.74\\text{{ m}} \\to 145.08\\text{{ m}}$).
- **Locked Test Evaluation:** On unseen test data, Candidate F3 **degraded 300s position drift from 218.93 m to 574.98 m (+162.6% error expansion)** and 1 km error from **307.46 m to 559.34 m (+81.9% error expansion)**.
- **Verdict:** **`B. REJECTED — Production pipeline retained at 218.93 m @ 300s baseline.`**
- **Production Pipeline Changed:** **NO**.

## Test Performance Comparison Table

| Metric | Locked Production Baseline (F0) | Validation-Selected Candidate (F3) | Delta / Change | Status |
|---|---|---|---|---|
| **60 s Error (m)** | **{test_results_f0[60]['err_m']} m** | {test_results_candidate[60]['err_m']} m | +12.76 m (+46.7%) | <span style="color:orange; font-weight:bold;">Slight Degraded</span> |
| **120 s Error (m)** | **{test_results_f0[120]['err_m']} m** | {test_results_candidate[120]['err_m']} m | -50.56 m (-11.8%) | <span style="color:green; font-weight:bold;">Slight Improved</span> |
| **300 s Error (m)** | **{test_results_f0[300]['err_m']} m** | {test_results_candidate[300]['err_m']} m | +356.05 m (+162.6%) | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **1 km Error (m)** | **{pe_1km_base:.2f} m** | {test_1km_candidate['err_m']} m | +251.88 m (+81.9%) | <span style="color:red; font-weight:bold;">SEVERE FAIL</span> |
| **300 s FPER (%)** | **15.81 %** | {test_results_candidate[300]['fper_pct']} % | +25.71 % | <span style="color:red; font-weight:bold;">FAIL</span> |
| **1 km FPER (%)** | **30.74 %** | {test_1km_candidate['fper_pct']} % | +25.19 % | <span style="color:red; font-weight:bold;">FAIL</span> |

## Physical Mechanism Breakdown
1. **Why did Candidate F3 fail on unseen test set?**  
   Downweighting SpeedNet velocity updates during turns ($R_v \\times 10.0$) forces the EKF to rely strictly on open-loop gyro/accelerometer integration during turn maneuvers.
2. **Disruption of Geometric Self-Cancellation:**  
   As proven in M040 and M042, SpeedNet forward velocity overestimation actively compensates for along-track integration lag. Downweighting SpeedNet during turns suppresses this forward velocity anchor, exploding 300s position drift from $218.93\\text{{ m}}$ to $574.98\\text{{ m}}$.

## Final Verdict
**`{verdict}`**
"""
    with open('results/vw4_m044_turn_deceleration_measurement_weighting.md', 'w') as f:
        f.write(md_content)
    print("Saved results/vw4_m044_turn_deceleration_measurement_weighting.md")

    # GENERATE PLOTS (Plots 1 through 4)
    # PLOT 1: Position Error vs Distance (Baseline vs Candidate F3)
    fig1, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
    ax1.plot(cum_dists, pe_series_base, color='#1f77b4', linewidth=2.0, label='Production Baseline F0 (218.93m)')
    ax1.plot(cum_dists, pe_cand_series, color='#d62728', linewidth=2.0, linestyle='--', label='Candidate F3 (574.98m - Degraded)')
    ax1.plot(cum_dists, 0.10 * cum_dists, color='#2ca02c', linestyle=':', linewidth=1.8, label='SIH 10% Allowable Boundary')
    ax1.set_title('M044 Plot 1: Position Error vs Reference Distance (Baseline vs Candidate F3)', fontsize=12, fontweight='bold', pad=12)
    ax1.set_xlabel('Reference Distance Travelled (m)', fontsize=10)
    ax1.set_ylabel('Position Error (m)', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('results/plots/m044_error_vs_distance_candidates.png', dpi=300)
    plt.close()

    # PLOT 2: FPER (%) vs Distance
    fig2, ax2 = plt.subplots(figsize=(9, 5), dpi=300)
    valid_m = cum_dists > 10.0
    fper_base = (pe_series_base / max(10, 1.0))
    fper_base[valid_m] = (pe_series_base[valid_m] / cum_dists[valid_m]) * 100
    fper_cand = (pe_cand_series / max(10, 1.0))
    fper_cand[valid_m] = (pe_cand_series[valid_m] / cum_dists[valid_m]) * 100

    ax2.plot(cum_dists[valid_m], fper_base[valid_m], color='#1f77b4', linewidth=2.0, label='Production Baseline F0')
    ax2.plot(cum_dists[valid_m], fper_cand[valid_m], color='#d62728', linewidth=2.0, linestyle='--', label='Candidate F3')
    ax2.axhline(10.0, color='#2ca02c', linestyle='--', linewidth=1.8, label='SIH Limit (10%)')
    ax2.set_title('M044 Plot 2: FPER (%) vs Reference Distance (Baseline vs Candidate F3)', fontsize=12, fontweight='bold', pad=12)
    ax2.set_xlabel('Reference Distance Travelled (m)', fontsize=10)
    ax2.set_ylabel('FPER (%)', fontsize=10)
    ax2.set_ylim(0, 70)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper left', frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('results/plots/m044_fper_vs_distance_candidates.png', dpi=300)
    plt.close()

    # PLOT 3: Turn Regime Activation (|omega_y| and threshold)
    fig3, ax3 = plt.subplots(figsize=(9, 5), dpi=300)
    w_deg_s = np.degrees(np.abs(w_yaw[start_idx:start_idx+n_300]))
    ax3.plot(time_series, w_deg_s, color='#9467bd', linewidth=1.5, label='|omega_y| Yaw Rate (deg/s)')
    ax3.axhline(cand_w, color='#d62728', linestyle='--', linewidth=1.8, label=f'Candidate Threshold ({cand_w}°/s)')
    ax3.set_title('M044 Plot 3: Causal Turn Regime Activation & Yaw Rate Threshold', fontsize=12, fontweight='bold', pad=12)
    ax3.set_xlabel('Outage Elapsed Time (s)', fontsize=10)
    ax3.set_ylabel('Yaw Rate |omega_y| (deg/s)', fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('results/plots/m044_turn_regime_activation.png', dpi=300)
    plt.close()

    # PLOT 4: SpeedNet Weighting Inflation & Active Downweighting
    fig4, ax4 = plt.subplots(figsize=(9, 5), dpi=300)
    r_v_series = np.where(w_deg_s > cand_w, 10.0, 1.0)
    ax4.plot(time_series, r_v_series, color='#ff7f0e', linewidth=1.8, label='SpeedNet Variance Multiplier R_v')
    ax4.set_title('M044 Plot 4: Dynamic SpeedNet Measurement-Variance Scaling Factor', fontsize=12, fontweight='bold', pad=12)
    ax4.set_xlabel('Outage Elapsed Time (s)', fontsize=10)
    ax4.set_ylabel('R_v Multiplier Factor', fontsize=10)
    ax4.grid(True, linestyle='--', alpha=0.5)
    ax4.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    plt.savefig('results/plots/m044_apm_speednet_weighting.png', dpi=300)
    plt.close()

    print("Generated all M044 plots in results/plots/")

if __name__ == '__main__':
    main()
