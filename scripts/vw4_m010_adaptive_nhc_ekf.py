# -*- coding: utf-8 -*-
"""
vw4_m010_adaptive_nhc_ekf.py
=============================
Milestone M010 — Adaptive NHC Measurement Covariance & Velocity-Frame EKF

Objective:
  Test whether dynamically relaxing the Non-Holonomic Constraint (NHC) measurement
  covariance R_nhc during high yaw-rate maneuvers reduces the NHC-heading contradiction
  and improves 300s dead-reckoning position accuracy.

Formulation:
  R_nhc(w) = R0 * (1 + kappa * |w_yaw|^2)
  Bounded variant:
  R_nhc(w) = clip(R0 * (1 + kappa * |w_yaw|^2), R0, R_max)

Rules:
  1. Provenance Baseline Lock: SpeedNet v2 + Raw Gyro + Fixed NHC = 263.11 m @ 300s
  2. Unseen Test Partition: start_idx = 108,000 (31.6 min test window)
  3. Validation Selection: Tune kappa and R_max ONLY on validation partition (88566:107535)
  4. Locked Evaluation: Test once on unseen test partition for 60s, 120s, and 300s
"""

import os, sys, io, time, json
import numpy as np
import pandas as pd
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.getcwd())

from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_speednet_v2_evaluate import (
    load_speednet_v2, predict_speednet_v2_full,
    t_sync, dt, n_total, idx_train_end, idx_val_end,
    ax_lin, ay_lin, az_lin, gx, gy, gz,
    raw_ax, raw_ay, grav_x, grav_y, gyro_pitch,
    a_long, w_yaw,
    vbox_lat, vbox_lon, vbox_vel_ms, vbox_heading_deg, vbox_yaw_rate_degs,
    x_gt_all, y_gt_all, vx_gt_all, vy_gt_all,
    X_norm_all, lat0, lon0, R_earth
)

os.makedirs('plots/vw4/m010_adaptive_nhc', exist_ok=True)
os.makedirs('results', exist_ok=True)

start_idx   = 108000       # Locked unseen test partition
val_start   = 88566        # Validation partition start
val_end     = 107535       # Validation partition end
PRE_SAMPLES = 300
R0          = 0.2**2       # 0.04 m²/s² baseline NHC covariance

print("Loading SpeedNet v2 (W=40) predictions...", flush=True)
model_v2 = load_speednet_v2(window_size=40)
v_ml_dict, w_ml_dict, prob_stat_dict = predict_speednet_v2_full(model_v2, window_size=40)

# ─────────────────────────────────────────────────────────────────────────────
# CORE EKF NAVIGATION FILTER WITH ADAPTIVE NHC
# ─────────────────────────────────────────────────────────────────────────────
def run_adaptive_nhc_filter(sim_start_idx, duration_sec,
                             kappa=0.0, r_max=100.0,
                             use_nhc=True,
                             speed_source='ml', heading_source='imu'):
    """
    EKF Filter with Adaptive NHC Measurement Covariance:
      R_nhc(t) = clip(R0 * (1 + kappa * w_yaw^2), R0, R_max)
    """
    n = int(duration_sec / dt)
    sim_start = sim_start_idx - PRE_SAMPLES
    sim_end   = sim_start_idx + n

    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]; x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([4.0, 4.0, 0.04, 0.04, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v = 1.0**2

    x_hist = []
    r_nhc_hist = []
    nhc_res_hist = []

    t0 = time.perf_counter()
    for idx in range(sim_start, sim_end):
        is_outage = (idx >= sim_start_idx)
        a_m = a_long[idx]; w_m = w_yaw[idx]
        x, y, vx, vy, psi, ba, bw = x_state

        if heading_source == 'gt':
            psi_new = np.radians(vbox_heading_deg[idx])
        else:
            w_hat   = w_m - bw
            psi_new = psi + w_hat * dt

        a_hat  = a_m - ba
        ax_enu = a_hat * np.sin(psi_new)
        ay_enu = a_hat * np.cos(psi_new)
        vx_new = vx + ax_enu * dt
        vy_new = vy + ay_enu * dt
        x_new  = x  + vx_new * dt
        y_new  = y  + vy_new * dt
        x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])

        F = np.eye(7)
        F[0, 2] = dt; F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt; F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt; F[3, 5] = -np.cos(psi_new) * dt; F[4, 6] = -dt
        P = F @ P @ F.T + Q

        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], x_state[4] + psi_diff])
            y_meas = z_gnss - H_gnss @ x_state
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H_gnss) @ P
        else:
            p_stat = prob_stat_dict.get(idx, 0.0)
            is_stat = p_stat > 0.70

            if is_stat:
                v_meas = 0.0
            elif speed_source == 'gt':
                v_meas = float(vbox_vel_ms[idx])
            else:
                v_meas = max(0.0, v_ml_dict.get(idx, 0.0))

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P

            if use_nhc:
                psi_c = x_state[4]
                v_lat = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)

                # Adaptive R_nhc calculation
                # w_m is in rad/s
                r_nhc_adaptive = R0 * (1.0 + kappa * (w_m**2))
                r_nhc_current  = float(np.clip(r_nhc_adaptive, R0, r_max))
                r_nhc_hist.append(r_nhc_current)

                H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                                   x_state[2]*np.sin(psi_c) + x_state[3]*np.cos(psi_c), 0, 0])
                y_nhc = 0.0 - v_lat
                nhc_res_hist.append(y_nhc)
                S_nhc = float(H_nhc @ P @ H_nhc.T + r_nhc_current)
                K_nhc = (P @ H_nhc.T) / S_nhc
                x_state = x_state + K_nhc * y_nhc
                P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P
            else:
                r_nhc_hist.append(R0)
                nhc_res_hist.append(0.0)

            x_hist.append(x_state.copy())

    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / (PRE_SAMPLES + n)) * 1000.0

    arr  = np.array(x_hist)
    x_dr = arr[:, 0] - arr[0, 0]
    y_dr = arr[:, 1] - arr[0, 1]
    v_dr = np.sqrt(arr[:, 2]**2 + arr[:, 3]**2)
    psi_deg = np.degrees(arr[:, 4])
    return x_dr, y_dr, v_dr, psi_deg, np.array(r_nhc_hist), np.array(nhc_res_hist), lat_ms

def compute_metrics(x_dr, y_dr, v_dr, psi_deg, start, dur):
    n = int(dur / dt)
    ls, ln = vbox_lat[start], vbox_lon[start]
    xgt = (np.radians(vbox_lon[start:start+n]) - np.radians(ln)) * R_earth * np.cos(np.radians(ls))
    ygt = (np.radians(vbox_lat[start:start+n]) - np.radians(ls)) * R_earth
    vgt = vbox_vel_ms[start:start+n]
    hgt = vbox_heading_deg[start:start+n]
    pe  = np.sqrt((x_dr-xgt)**2 + (y_dr-ygt)**2)
    dist_gt = float(np.sum(np.sqrt(np.diff(xgt)**2+np.diff(ygt)**2)))
    dist_dr = float(np.sum(v_dr)*dt)
    cde = abs(dist_dr-dist_gt)/dist_gt*100
    he  = np.abs((psi_deg - hgt + 180) % 360 - 180)
    return {
        'final_pos_m': round(float(pe[-1]), 2),
        'max_pos_m':   round(float(np.max(pe)), 2),
        'drift_rate':  round(float(pe[-1]/dur), 4),
        'cde_pct':     round(float(cde), 2),
        'v_mae_kmh':   round(float(np.mean(np.abs(v_dr-vgt)))*3.6, 2),
        'h_err_deg':   round(float(he[-1]), 2),
        'pos_err_arr': pe.tolist(),
        'x_dr': x_dr.tolist(), 'y_dr': y_dr.tolist(),
        'x_gt': xgt.tolist(), 'y_gt': ygt.tolist(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: VALIDATION PARAMETER SWEEP (kappa, R_max) ON VALIDATION SET
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("STEP 1: VALIDATION PARAMETER SWEEP ON VALIDATION SET (88566:107535)", flush=True)
print("="*70, flush=True)

kappa_grid = [0.0, 1.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0]
rmax_grid  = [1.0, 5.0, 20.0, 100.0]

# Evaluate 300s outage on validation set at val_start + 1000
val_sim_start = val_start + 1000
val_sweep_results = []

best_val_score = float('inf')
best_kappa     = 0.0
best_rmax      = 100.0

print(f"  Sweeping kappa x R_max over validation outage (300s at idx={val_sim_start}):", flush=True)
for k in kappa_grid:
    for rm in rmax_grid:
        xd, yd, vd, psi_d, _, _, _ = run_adaptive_nhc_filter(val_sim_start, 300, kappa=k, r_max=rm, use_nhc=True)
        m = compute_metrics(xd, yd, vd, psi_d, val_sim_start, 300)
        val_sweep_results.append({'kappa': k, 'r_max': rm, 'val_300s_pos_m': m['final_pos_m'], 'val_cde': m['cde_pct']})

        if m['final_pos_m'] < best_val_score:
            best_val_score = m['final_pos_m']
            best_kappa     = k
            best_rmax      = rm

print(f"\n  Validation Parameter Selection Summary:", flush=True)
print(f"    Best Validation 300s Position Error: {best_val_score:.2f} m")
print(f"    Selected kappa: {best_kappa}")
print(f"    Selected R_max: {best_rmax}")

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: LOCKED EXPERIMENTAL MATRIX EVALUATION (UNSEEN TEST PARTITION)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("STEP 2: LOCKED EVALUATION ON UNSEEN TEST PARTITION (start_idx = 108,000)", flush=True)
print("Provenance Benchmark (SpeedNet v2 + Fixed NHC): 263.11 m @ 300s", flush=True)
print("="*70, flush=True)

test_cases = [
    ("Case A: SpeedNet v2 + Raw Gyro + Fixed NHC [BENCHMARK]", 0.0,   100.0, True,  'ml', 'imu'),
    ("Case B: SpeedNet v2 + Raw Gyro (NO NHC)",                0.0,   100.0, False, 'ml', 'imu'),
    ("Case C: SpeedNet v2 + Adaptive NHC (Small kappa=1.0)",   1.0,   100.0, True,  'ml', 'imu'),
    ("Case D: SpeedNet v2 + Adaptive NHC (Medium kappa=10.0)",  10.0,  100.0, True,  'ml', 'imu'),
    ("Case E: SpeedNet v2 + Adaptive NHC (Large kappa=100.0)", 100.0, 100.0, True,  'ml', 'imu'),
    (f"Case F: Bounded Adaptive NHC (Selected Val: k={best_kappa}, Rmax={best_rmax})", best_kappa, best_rmax, True, 'ml', 'imu'),
    ("GT Speed + Raw Gyro + Bounded Adaptive NHC",             best_kappa, best_rmax, True, 'gt', 'imu'),
    ("GT Speed + GT Yaw + Fixed NHC [Oracle Floor]",          0.0,   100.0, True,  'gt', 'gt'),
]

eval_matrix_results = []
print(f"\n  {'Case Name':<58} {'60s (m)':>8} {'120s (m)':>9} {'300s (m)':>9} {'300s CDE%':>9} {'vs Base':>10}", flush=True)
print("  " + "-"*108, flush=True)

# First run Benchmark Case A to verify baseline reproduction
baseline_300s_pos = 0.0

for name, k, rm, unhc, ss, hs in test_cases:
    row = {'case_name': name, 'kappa': k, 'r_max': rm, 'use_nhc': unhc, 'speed_source': ss, 'heading_source': hs}
    for dur in [60, 120, 300]:
        xd, yd, vd, psi_d, r_hist, res_hist, lat = run_adaptive_nhc_filter(start_idx, dur, kappa=k, r_max=rm, use_nhc=unhc, speed_source=ss, heading_source=hs)
        m = compute_metrics(xd, yd, vd, psi_d, start_idx, dur)
        row[f'{dur}s'] = m
        row[f'{dur}s_r_hist'] = r_hist.tolist()
        row[f'{dur}s_res_hist'] = res_hist.tolist()

    pos60  = row['60s']['final_pos_m']
    pos120 = row['120s']['final_pos_m']
    pos300 = row['300s']['final_pos_m']
    cde300 = row['300s']['cde_pct']

    if name.startswith("Case A"):
        baseline_300s_pos = pos300
        delta_str = "BENCHMARK"
    else:
        diff = pos300 - baseline_300s_pos
        pct  = (diff / baseline_300s_pos) * 100
        delta_str = f"{diff:>+6.1f}m ({pct:>+5.1f}%)"

    row['change_vs_baseline_m'] = round(pos300 - baseline_300s_pos, 2)
    eval_matrix_results.append(row)
    print(f"  {name:<58} {pos60:>8.1f} {pos120:>9.1f} {pos300:>9.1f} {cde300:>8.1f}% {delta_str:>10}", flush=True)

# Baseline reproduction check
print(f"\n  REPRODUCED PROVENANCE BASELINE (Case A): {baseline_300s_pos:.2f} m @ 300s (Target = 263.11 m)", flush=True)
assert abs(baseline_300s_pos - 263.11) < 2.0, f"Baseline reproduction error! Expected ~263.11m, got {baseline_300s_pos:.2f}m"

# Selected Case F (Val-Selected Model) performance
case_f_pos300 = eval_matrix_results[5]['300s']['final_pos_m']
print(f"  SELECTED VAL MODEL (Case F: k={best_kappa}, Rmax={best_rmax}): {case_f_pos300:.2f} m @ 300s", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# M010 VERDICT & CLASSIFICATION
# ─────────────────────────────────────────────────────────────────────────────
BENCHMARK_TARGET = 263.11
MAJOR_TARGET     = 150.0

if case_f_pos300 < MAJOR_TARGET:
    m010_verdict = "MAJOR SUCCESS"
    verdict_desc = f"Selected Adaptive NHC [{case_f_pos300:.2f} m] achieved the secondary target (<150 m)!"
elif case_f_pos300 < BENCHMARK_TARGET - 2.0:
    m010_verdict = "MEANINGFUL IMPROVEMENT"
    verdict_desc = f"Selected Adaptive NHC [{case_f_pos300:.2f} m] beat the 263.11 m benchmark by {BENCHMARK_TARGET - case_f_pos300:.2f} m!"
elif abs(case_f_pos300 - BENCHMARK_TARGET) <= 2.0:
    m010_verdict = "NO MEANINGFUL CHANGE"
    verdict_desc = f"Selected Adaptive NHC [{case_f_pos300:.2f} m] performed identically to the 263.11 m benchmark."
else:
    m010_verdict = "REJECTED"
    verdict_desc = f"Selected Adaptive NHC [{case_f_pos300:.2f} m] degraded 300s navigation compared to the 263.11 m benchmark (+{case_f_pos300 - BENCHMARK_TARGET:.2f} m)."

print(f"\n" + "="*70, flush=True)
print(f"M010 VERDICT: {m010_verdict}", flush=True)
print(f"  {verdict_desc}", flush=True)
print("="*70, flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# REGIME ANALYSIS FOR ADAPTIVE NHC
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("MANEUVER REGIME ANALYSIS: FIXED VS ADAPTIVE NHC (300s Outage)", flush=True)
print("="*70, flush=True)

REGIME_NAMES = ['Stationary', 'Acceleration', 'Braking', 'Straight/Cruise', 'Moderate Turn', 'Strong Turn']
a_long_gt_all = np.gradient(vbox_vel_ms, dt)
w_gt_abs_all  = np.abs(vbox_yaw_rate_degs)

regime_labels = np.full(n_total, 3, dtype=np.int64)
regime_labels[w_gt_abs_all >= 14.3] = 5  # ~0.25 rad/s
regime_labels[(w_gt_abs_all >= 2.87) & (w_gt_abs_all < 14.3)] = 4 # 0.05..0.25 rad/s
not_turning = (w_gt_abs_all < 2.87)
regime_labels[not_turning & (a_long_gt_all >= 0.5)]  = 1
regime_labels[not_turning & (a_long_gt_all <= -0.5)] = 2
regime_labels[vbox_vel_ms < 0.1] = 0

n300 = 3000
reg_test300 = regime_labels[start_idx:start_idx+n300]

r_hist_caseA = np.array(eval_matrix_results[0]['300s_r_hist']) # Fixed NHC (R0 = 0.04)
r_hist_caseF = np.array(eval_matrix_results[5]['300s_r_hist']) # Bounded Adaptive NHC
res_hist_A   = np.array(eval_matrix_results[0]['300s_res_hist'])
res_hist_F   = np.array(eval_matrix_results[5]['300s_res_hist'])

regime_breakdown = []
print(f"  {'Regime':<18} {'%time':>6} | {'R_NHC Fixed':>12} {'R_NHC Adapt':>12} | {'Res MAE Fixed':>14} {'Res MAE Adapt':>14}", flush=True)
print("  " + "-"*85, flush=True)

for rid, rname in enumerate(REGIME_NAMES):
    mask = (reg_test300 == rid)
    n_r  = int(np.sum(mask))
    if n_r == 0: continue
    pct_t = round(n_r / n300 * 100, 1)

    r_fix_m = round(float(np.mean(r_hist_caseA[mask])), 4)
    r_ada_m = round(float(np.mean(r_hist_caseF[mask])), 4)
    res_fix_m = round(float(np.mean(np.abs(res_hist_A[mask]))), 4)
    res_ada_m = round(float(np.mean(np.abs(res_hist_F[mask]))), 4)

    regime_breakdown.append({
        'regime': rname, 'pct_time': pct_t,
        'r_nhc_fixed': r_fix_m, 'r_nhc_adaptive': r_ada_m,
        'res_mae_fixed': res_fix_m, 'res_mae_adaptive': res_ada_m
    })
    print(f"  {rname:<18} {pct_t:>5.1f}% | {r_fix_m:>12.4f} {r_ada_m:>12.4f} | {res_fix_m:>14.4f} {res_ada_m:>14.4f}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTS GENERATION
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating diagnostic plots...", flush=True)
P_DIR = 'plots/vw4/m010_adaptive_nhc'
t300 = np.arange(n300) * dt

# Plot 1: Position Error vs Time (All Cases)
fig, ax = plt.subplots(figsize=(12, 6))
colors_p = ['#4CAF50', '#F44336', '#FF9800', '#2196F3', '#9C27B0', '#009688', '#E91E63', '#607D8B']
for i, r in enumerate(eval_matrix_results):
    lbl = f"{r['case_name'][:40]} ({r['300s']['final_pos_m']:.1f}m)"
    ls = '--' if r['heading_source'] == 'gt' else '-'
    lw = 2.2 if i in [0, 5] else 1.2
    ax.plot(t300, r['300s']['pos_err_arr'], label=lbl, color=colors_p[i % len(colors_p)], linestyle=ls, linewidth=lw)

ax.axhline(BENCHMARK_TARGET, color='red', linestyle=':', label=f'Benchmark ({BENCHMARK_TARGET}m)')
ax.axhline(MAJOR_TARGET, color='gold', linestyle=':', label=f'Target (<{MAJOR_TARGET}m)')
ax.set_xlabel('Time in Outage (s)'); ax.set_ylabel('Position Error (m)')
ax.set_title('M010 — 300s Dead-Reckoning Position Error Growth (Adaptive NHC)', fontweight='bold')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/pos_error_vs_time.png', dpi=150); plt.close()

# Plot 2: Adaptive R_NHC(t) vs Yaw Rate Over Time
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
w_yaw_degs_300 = vbox_yaw_rate_degs[start_idx:start_idx+n300]
ax1.plot(t300, np.abs(w_yaw_degs_300), color='#FF9800', label='Absolute Yaw Rate (|w_yaw| deg/s)')
ax1.set_ylabel('Yaw Rate (deg/s)'); ax1.legend(); ax1.grid(True, alpha=0.3)
ax1.set_title('M010 — Dynamic R_NHC(t) Inflation During Cornering (300s Outage)', fontweight='bold')

ax2.plot(t300, r_hist_caseA, label='Fixed R_NHC (Case A = 0.04)', color='#4CAF50', linewidth=1.5)
ax2.plot(t300, r_hist_caseF, label=f'Adaptive R_NHC (Case F: k={best_kappa}, Rmax={best_rmax})', color='#009688', linewidth=1.8)
ax2.set_xlabel('Time in Outage (s)'); ax2.set_ylabel('R_NHC Covariance (m²/s²)')
ax2.legend(); ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/adaptive_r_nhc_vs_time.png', dpi=150); plt.close()

# Plot 3: NHC Residual vs Time (Fixed vs Adaptive)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(t300, res_hist_A, label=f'Fixed NHC Residual (Case A MAE={np.mean(np.abs(res_hist_A)):.4f} m/s)', color='#4CAF50', alpha=0.7)
ax.plot(t300, res_hist_F, label=f'Adaptive NHC Residual (Case F MAE={np.mean(np.abs(res_hist_F)):.4f} m/s)', color='#009688', alpha=0.85)
ax.set_xlabel('Time in Outage (s)'); ax.set_ylabel('NHC Residual y_nhc (m/s)')
ax.set_title('M010 — EKF NHC Measurement Residual: Fixed vs Adaptive Covariance', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/nhc_residual_vs_time.png', dpi=150); plt.close()

# Plot 4: Position Error Comparison Bar Chart (60s, 120s, 300s)
fig, ax = plt.subplots(figsize=(12, 6))
c_names4 = [r['case_name'][:30] for r in eval_matrix_results]
p60_vals  = [r['60s']['final_pos_m'] for r in eval_matrix_results]
p120_vals = [r['120s']['final_pos_m'] for r in eval_matrix_results]
p300_vals = [r['300s']['final_pos_m'] for r in eval_matrix_results]

x4 = np.arange(len(c_names4))
w4 = 0.25
ax.bar(x4 - w4, p60_vals, w4, label='60s Error (m)', color='#4CAF50')
ax.bar(x4, p120_vals, w4, label='120s Error (m)', color='#2196F3')
ax.bar(x4 + w4, p300_vals, w4, label='300s Error (m)', color='#F44336')
ax.set_xticks(x4); ax.set_xticklabels(c_names4, rotation=35, ha='right', fontsize=8)
ax.axhline(BENCHMARK_TARGET, color='black', linestyle=':', label=f'Benchmark ({BENCHMARK_TARGET}m)')
ax.set_ylabel('Position Error (m)')
ax.set_title('M010 — Multi-Horizon Outage Navigation Performance Matrix', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/multi_horizon_comparison.png', dpi=150); plt.close()

# Plot 5: Regime-wise R_NHC and Residual Bar Chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
r_names5 = [r['regime'] for r in regime_breakdown]
r_fix5   = [r['r_nhc_fixed'] for r in regime_breakdown]
r_ada5   = [r['r_nhc_adaptive'] for r in regime_breakdown]
res_fix5 = [r['res_mae_fixed'] for r in regime_breakdown]
res_ada5 = [r['res_mae_adaptive'] for r in regime_breakdown]

x5 = np.arange(len(r_names5))
ax1.bar(x5 - 0.2, r_fix5, 0.35, label='Fixed R_NHC', color='#4CAF50')
ax1.bar(x5 + 0.2, r_ada5, 0.35, label='Adaptive R_NHC', color='#009688')
ax1.set_xticks(x5); ax1.set_xticklabels(r_names5, rotation=30, ha='right')
ax1.set_ylabel('Mean R_NHC Covariance (m²/s²)'); ax1.set_title('Mean R_NHC by Maneuver Regime', fontweight='bold')
ax1.legend(); ax1.grid(True, alpha=0.3)

ax2.bar(x5 - 0.2, res_fix5, 0.35, label='Fixed Residual MAE', color='#FF9800')
ax2.bar(x5 + 0.2, res_ada5, 0.35, label='Adaptive Residual MAE', color='#E91E63')
ax2.set_xticks(x5); ax2.set_xticklabels(r_names5, rotation=30, ha='right')
ax2.set_ylabel('Residual MAE (m/s)'); ax2.set_title('NHC Residual MAE by Maneuver Regime', fontweight='bold')
ax2.legend(); ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{P_DIR}/regime_r_nhc_and_residual.png', dpi=150); plt.close()

# Plot 6: Validation Parameter Sweep Heatmap / Surface
fig, ax = plt.subplots(figsize=(8, 6))
sweep_df = pd.DataFrame(val_sweep_results)
pivot_df = sweep_df.pivot(index='kappa', columns='r_max', values='val_300s_pos_m')
im = ax.imshow(pivot_df.values, cmap='viridis_r')
ax.set_xticks(np.arange(len(pivot_df.columns)))
ax.set_yticks(np.arange(len(pivot_df.index)))
ax.set_xticklabels(pivot_df.columns)
ax.set_yticklabels(pivot_df.index)
ax.set_xlabel('R_max'); ax.set_ylabel('kappa')
ax.set_title('M010 — Validation Set Parameter Sweep Heatmap (300s Error m)', fontweight='bold')
fig.colorbar(im, ax=ax)
for ii in range(len(pivot_df.index)):
    for jj in range(len(pivot_df.columns)):
        val_c = pivot_df.values[ii, jj]
        ax.text(jj, ii, f'{val_c:.1f}', ha='center', va='center', color='white' if val_c > pivot_df.values.mean() else 'black', fontsize=8)
plt.tight_layout()
plt.savefig(f'{P_DIR}/val_parameter_sweep_heatmap.png', dpi=150); plt.close()

print(f"  Diagnostic plots saved to {P_DIR}/", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE SUMMARY JSON
# ─────────────────────────────────────────────────────────────────────────────
summary_data = {
    'milestone': 'M010',
    'experiment': 'Adaptive NHC Measurement Covariance & Velocity-Frame EKF',
    'dataset': 'Vw04',
    'test_start': start_idx,
    'provenance_benchmark_300s_m': BENCHMARK_TARGET,
    'verdict': m010_verdict,
    'verdict_description': verdict_desc,
    'selected_val_parameters': {
        'best_kappa': best_kappa,
        'best_r_max': best_rmax,
        'val_300s_pos_m': best_val_score
    },
    'selected_case_f_300s_pos_m': case_f_pos300,
    'change_vs_benchmark_m': round(case_f_pos300 - BENCHMARK_TARGET, 2),
    'pct_change_vs_benchmark': round((case_f_pos300 - BENCHMARK_TARGET)/BENCHMARK_TARGET * 100, 2),
    'validation_sweep_results': val_sweep_results,
    'unseen_test_evaluation_matrix': [
        {k: v for k, v in r.items() if not k.endswith('_hist')} for r in eval_matrix_results
    ],
    'regime_breakdown': regime_breakdown
}

with open('results/vw4_m010_adaptive_nhc_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

print("M010 summary JSON saved.", flush=True)
print("M010 execution complete.", flush=True)
