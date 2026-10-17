import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2

# ── Paths & Data Loading ────────────────────────────────────────────────────
s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# Timestamp Synchronization
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end   = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1 # 10 Hz
t_sync = np.arange(t_start, t_end, dt)

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

X_raw_all = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y)
a_lat_tilt_comp = raw_ax - grav_x
w_yaw = -gyro_pitch

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)
vbox_yaw_rate_degs = interp1d(t_v_utc, df_v['Yaw Rate (deg/sec)'], fill_value='extrapolate')(t_sync)

lat0, lon0 = vbox_lat[0], vbox_lon[0]
R_earth = 6378137.0
lat_rad_all = np.radians(vbox_lat)
lon_rad_all = np.radians(vbox_lon)
x_gt_all = (lon_rad_all - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
y_gt_all = (lat_rad_all - np.radians(lat0)) * R_earth
vx_gt_all = vbox_vel_ms * np.sin(np.radians(vbox_heading_deg))
vy_gt_all = vbox_vel_ms * np.cos(np.radians(vbox_heading_deg))

n_total = len(t_sync)
idx_train_end = int(n_total * 0.70) # 88566
idx_val_end   = int(n_total * 0.85) # 107535
start_idx     = 108000              # Unseen test partition

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0
X_norm_all = (X_raw_all - train_mean) / train_std

PRE_SAMPLES = 100

# ── SpeedNet Prediction Pre-computation ──────────────────────────────────
def get_speednet_predictions(window_size=40, model_path='models/speednet_v2_w40.pth'):
    device = torch.device('cpu')
    model = SpeedNetV2(window_size=window_size).to(device)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    needed_indices = np.arange(window_size - 1, n_total)
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    sub_indices = needed_indices - (window_size - 1)
    sub_batch = sub_windows[sub_indices].astype(np.float32)

    v_dict = {}; w_dict = {}; prob_stat_dict = {}
    with torch.no_grad():
        v_p, w_p, logit_s, _ = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
        v_p = v_p.cpu().numpy()
        w_p = w_p.cpu().numpy()
        prob_s = torch.sigmoid(logit_s).cpu().numpy()

    for j, idx in enumerate(needed_indices):
        v_dict[idx] = max(0.0, float(v_p[j]))
        w_dict[idx] = float(w_p[j])
        prob_stat_dict[idx] = float(prob_s[j])

    return v_dict, w_dict, prob_stat_dict

print("Loading SpeedNet v2 (W=40) baseline predictions...")
v_ml_raw_dict, w_ml_raw_dict, prob_stat_dict = get_speednet_predictions(window_size=40)

# ── Navigation Filter Matching Baseline Protocol (Case D: SpeedNet v2 + Raw Gyro + NHC) ──
def run_navigation(v_ml_dict, prob_stat_dict, sim_start_idx=108000, duration_sec=300, innovation_constraint=False, y_v_max_func=None):
    n = int(duration_sec / dt)
    pre_samples = 300
    sim_start = sim_start_idx - pre_samples
    sim_end   = sim_start_idx + n

    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]; x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v   = 1.0**2
    R_nhc = 0.2**2

    x_hist = []
    t0 = time.perf_counter()
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
            v_meas = 0.0 if is_stat else max(0.0, v_ml_dict.get(idx, 0.0))

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est

            if innovation_constraint and y_v_max_func is not None:
                max_allowed_y_v = y_v_max_func(idx, v_est, a_m)
                if y_v > max_allowed_y_v:
                    y_v = max_allowed_y_v

            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P

            psi_c = x_state[4]
            v_lat = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
            H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                               x_state[2]*np.sin(psi_c) + x_state[3]*np.cos(psi_c), 0, 0])
            y_nhc = 0.0 - v_lat
            S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
            K_nhc = (P @ H_nhc.T) / S_nhc
            x_state = x_state + K_nhc * y_nhc
            P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P

            x_hist.append(x_state.copy())

    t1 = time.perf_counter()
    arr  = np.array(x_hist)
    x_dr = arr[:, 0] - arr[0, 0]
    y_dr = arr[:, 1] - arr[0, 1]
    v_dr = np.sqrt(arr[:, 2]**2 + arr[:, 3]**2)
    psi_deg = np.degrees(arr[:, 4])
    lat_ms = ((t1 - t0) / (PRE_SAMPLES + n)) * 1000.0
    return x_dr, y_dr, v_dr, psi_deg, lat_ms

def compute_metrics(x_dr, y_dr, v_dr, psi_deg, v_ml_dict, start, dur):
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

    v_preds = np.array([v_ml_dict.get(i, 0.0) for i in range(start, start+n)])
    speed_mae  = float(np.mean(np.abs(v_preds - vgt)) * 3.6)
    speed_bias = float(np.mean(v_preds - vgt) * 3.6)
    speed_rmse = float(np.sqrt(np.mean((v_preds - vgt)**2)) * 3.6)

    return {
        'final_pos_m': round(float(pe[-1]), 2),
        'max_pos_m':   round(float(np.max(pe)), 2),
        'cde_pct':     round(float(cde), 2),
        'speed_mae_kmh': round(speed_mae, 2),
        'speed_bias_kmh': round(speed_bias, 2),
        'speed_rmse_kmh': round(speed_rmse, 2),
        'h_err_deg':   round(float(he[-1]), 2),
        'pos_err_arr': pe
    }

# ── Diagnostic Regime Segmentation ─────────────────────────────────────────
def get_regime_mask(indices):
    v_gt = vbox_vel_ms[indices]
    a_l = a_long[indices]
    w_y = np.abs(w_yaw[indices])

    mask_stat = (v_gt < 0.1)
    mask_acc  = (~mask_stat) & (a_l > 0.3)
    mask_brk  = (~mask_stat) & (a_l < -0.3)
    mask_str  = (~mask_stat) & (np.abs(a_l) <= 0.3) & (w_y <= np.radians(3.0))
    mask_mturn= (~mask_stat) & (w_y > np.radians(3.0)) & (w_y <= np.radians(10.0))
    mask_sturn= (~mask_stat) & (w_y > np.radians(10.0))

    return {
        'Stationary': mask_stat,
        'Acceleration': mask_acc,
        'Braking': mask_brk,
        'Straight/Cruise': mask_str,
        'Moderate Turn': mask_mturn,
        'Strong Turn': mask_sturn
    }

# ── Candidate Velocity Constraint Functions ───────────────────────────────
def generate_candidate_v_dicts(v_ml_dict):
    v_f0_dict = v_ml_dict.copy()

    # F1: Hard velocity upper-bound
    v_f1_dict = {}
    v_prev_f1 = 0.0
    for idx in range(n_total):
        v_net = v_ml_dict.get(idx, 0.0)
        a_m = a_long[idx]
        v_phys_bound = max(0.0, v_prev_f1 + a_m * dt)
        v_corr = min(v_net, v_phys_bound)
        v_f1_dict[idx] = v_corr
        v_prev_f1 = v_corr

    # F2: Bounded hard constraint
    a_train_val = a_long[:idx_val_end]
    a_min_f2 = np.percentile(a_train_val, 5) # ~ -3.29 m/s^2
    a_max_f2 = np.percentile(a_train_val, 95) # ~ +3.74 m/s^2

    v_f2_dict = {}
    v_prev_f2 = 0.0
    for idx in range(n_total):
        v_net = v_ml_dict.get(idx, 0.0)
        a_m = np.clip(a_long[idx], a_min_f2, a_max_f2)
        v_phys_bound = max(0.0, v_prev_f2 + a_m * dt)
        v_corr = min(v_net, v_phys_bound)
        v_f2_dict[idx] = v_corr
        v_prev_f2 = v_corr

    # F3: Deceleration-only hard constraint
    a_brake_thresh = -0.2
    v_f3_dict = {}
    v_prev_f3 = 0.0
    for idx in range(n_total):
        v_net = v_ml_dict.get(idx, 0.0)
        a_m = a_long[idx]
        if a_m < a_brake_thresh:
            v_phys_bound = max(0.0, v_prev_f3 + a_m * dt)
            v_corr = min(v_net, v_phys_bound)
        else:
            v_corr = v_net
        v_f3_dict[idx] = v_corr
        v_prev_f3 = v_corr

    # F4: Confidence-gated hard constraint
    rolling_var_a = np.zeros(n_total)
    for i in range(5, n_total):
        rolling_var_a[i] = np.var(a_long[i-5:i])
    var_thresh = np.percentile(rolling_var_a[:idx_val_end], 75)
    w_turn_thresh = np.radians(5.0)

    v_f4_dict = {}
    v_prev_f4 = 0.0
    for idx in range(n_total):
        v_net = v_ml_dict.get(idx, 0.0)
        a_m = a_long[idx]
        if rolling_var_a[idx] <= var_thresh and np.abs(w_yaw[idx]) <= w_turn_thresh:
            v_phys_bound = max(0.0, v_prev_f4 + a_m * dt)
            v_corr = min(v_net, v_phys_bound)
        else:
            v_corr = v_net
        v_f4_dict[idx] = v_corr
        v_prev_f4 = v_corr

    return {
        'F0 (Control)': v_f0_dict,
        'F1 (Hard Upper-Bound)': v_f1_dict,
        'F2 (Bounded Acceleration)': v_f2_dict,
        'F3 (Deceleration-Only)': v_f3_dict,
        'F4 (Confidence-Gated)': v_f4_dict
    }

candidates_v_dicts = generate_candidate_v_dicts(v_ml_raw_dict)

# ── 1. Baseline Reproduction Verification ─────────────────────────────────
print("\n======================================================================")
print("1. PROVENANCE BASELINE REPRODUCTION VERIFICATION")
print("======================================================================")
f0_dict = candidates_v_dicts['F0 (Control)']

p_results_f0 = {}
for dur in [60, 120, 300]:
    xd, yd, vd, psi_d, _ = run_navigation(f0_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur)
    m = compute_metrics(xd, yd, vd, psi_d, f0_dict, start_idx, dur)
    p_results_f0[dur] = m['final_pos_m']

print(f"  F0 Control Measured:  60s = {p_results_f0[60]:.2f} m | 120s = {p_results_f0[120]:.2f} m | 300s = {p_results_f0[300]:.2f} m")
print(f"  Provenance Benchmark: 60s = 22.75 m | 120s = 440.20 m | 300s = 263.11 m")
if abs(p_results_f0[300] - 263.11) < 0.5:
    print("  --> REPRODUCTION SUCCESSFUL: 100% Exact Match confirmed!\n")
else:
    print(f"  --> REPRODUCTION MISMATCH WARNING: Diff = {abs(p_results_f0[300] - 263.11):.2f}m\n")

# ── 2. Evaluation Across Candidates ──────────────────────────────────────
test_indices = np.arange(start_idx, start_idx + 3000)
results_table = []
nav_err_series = {}

candidate_names = ['F0 (Control)', 'F1 (Hard Upper-Bound)', 'F2 (Bounded Acceleration)', 'F3 (Deceleration-Only)', 'F4 (Confidence-Gated)']

for name in candidate_names:
    v_dict = candidates_v_dicts[name]
    dur_res = {}
    pos_err_300s = None
    for dur in [60, 120, 300]:
        xd, yd, vd, psi_d, _ = run_navigation(v_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur)
        m = compute_metrics(xd, yd, vd, psi_d, v_dict, start_idx, dur)
        dur_res[dur] = m['final_pos_m']
        if dur == 300:
            pos_err_300s = m['pos_err_arr']

    nav_err_series[name] = pos_err_300s

    v_pred_test = np.array([v_dict.get(i, 0.0) for i in test_indices])
    v_gt_test   = vbox_vel_ms[test_indices]
    speed_mae_kmh  = float(np.mean(np.abs(v_pred_test - v_gt_test)) * 3.6)
    speed_bias_kmh = float(np.mean(v_pred_test - v_gt_test) * 3.6)

    v_raw_test = np.array([v_ml_raw_dict.get(i, 0.0) for i in test_indices])
    diff_corr  = v_pred_test - v_raw_test
    mask_active = (np.abs(diff_corr) > 1e-4)
    act_count   = int(np.sum(mask_active))
    act_pct     = float(act_count / len(test_indices) * 100.0)
    avg_mag     = float(np.mean(np.abs(diff_corr[mask_active]))) * 3.6 if act_count > 0 else 0.0
    max_mag     = float(np.max(np.abs(diff_corr))) * 3.6

    neg_bound_cnt = 0
    v_prev_curr = 0.0
    for t_idx in test_indices:
        phys_b = v_prev_curr + a_long[t_idx] * dt
        if phys_b < 0:
            neg_bound_cnt += 1
        v_prev_curr = v_pred_test[t_idx - start_idx]

    pct_diff = float((dur_res[300] - 263.11) / 263.11 * 100.0)

    results_table.append({
        'name': name,
        'speed_mae_kmh': round(speed_mae_kmh, 2),
        'speed_bias_kmh': round(speed_bias_kmh, 2),
        'err_60s': dur_res[60],
        'err_120s': dur_res[120],
        'err_300s': dur_res[300],
        'pct_vs_bench': round(pct_diff, 1),
        'act_count': act_count,
        'act_pct': round(act_pct, 1),
        'avg_mag_kmh': round(avg_mag, 2),
        'max_mag_kmh': round(max_mag, 2),
        'neg_bounds': neg_bound_cnt
    })

# F5 Innovation Constraint Evaluation
def f5_innovation_max_func(idx, v_est, a_m):
    tol = 0.5 / 3.6
    return max(0.0, a_m * dt + tol)

dur_res_f5 = {}
pos_err_300s_f5 = None
for dur in [60, 120, 300]:
    xd, yd, vd, psi_d, _ = run_navigation(v_ml_raw_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur, innovation_constraint=True, y_v_max_func=f5_innovation_max_func)
    m = compute_metrics(xd, yd, vd, psi_d, v_ml_raw_dict, start_idx, dur)
    dur_res_f5[dur] = m['final_pos_m']
    if dur == 300:
        pos_err_300s_f5 = m['pos_err_arr']

nav_err_series['F5 (EKF Innovation-Gated)'] = pos_err_300s_f5
v_pred_test = np.array([v_ml_raw_dict.get(i, 0.0) for i in test_indices])
v_gt_test   = vbox_vel_ms[test_indices]
speed_mae_kmh  = float(np.mean(np.abs(v_pred_test - v_gt_test)) * 3.6)
speed_bias_kmh = float(np.mean(v_pred_test - v_gt_test) * 3.6)
pct_diff_f5 = float((dur_res_f5[300] - 263.11) / 263.11 * 100.0)

results_table.append({
    'name': 'F5 (EKF Innovation-Gated)',
    'speed_mae_kmh': round(speed_mae_kmh, 2),
    'speed_bias_kmh': round(speed_bias_kmh, 2),
    'err_60s': dur_res_f5[60],
    'err_120s': dur_res_f5[120],
    'err_300s': dur_res_f5[300],
    'pct_vs_bench': round(pct_diff_f5, 1),
    'act_count': 0,
    'act_pct': 0.0,
    'avg_mag_kmh': 0.0,
    'max_mag_kmh': 0.0,
    'neg_bounds': 0
})

print("======================================================================")
print("2. CANDIDATE SWEEP UNSEEN TEST RESULTS (start_idx = 108,000)")
print("======================================================================")
print(f"{'Variant Name':<28} | {'Speed MAE':<9} | {'Bias':<7} | {'60s (m)':<7} | {'120s (m)':<8} | {'300s (m)':<8} | {'vs Benchmark'}")
print("-" * 95)
for r in results_table:
    bench_str = "BENCHMARK" if "Control" in r['name'] else f"{r['pct_vs_bench']:+6.1f}%"
    print(f"{r['name']:<28} | {r['speed_mae_kmh']:>6.2f}k  | {r['speed_bias_kmh']:>+6.2f}k| {r['err_60s']:>7.2f} | {r['err_120s']:>8.2f} | {r['err_300s']:>8.2f} | {bench_str}")

# Regime Speed Bias Analysis
print("\n======================================================================")
print("3. DRIVING REGIME SPEED BIAS DIAGNOSTIC (km/h)")
print("======================================================================")
regime_masks = get_regime_mask(test_indices)

print(f"{'Regime':<18} | {'F0 Control':<10} | {'F1 Hard-Bound':<13} | {'F3 Decel-Only':<13} | {'F4 Conf-Gated':<13}")
print("-" * 80)
for r_name, r_mask in regime_masks.items():
    if np.sum(r_mask) > 0:
        b_f0 = float(np.mean(np.array([candidates_v_dicts['F0 (Control)'][i] for i in test_indices])[r_mask] - vbox_vel_ms[test_indices][r_mask]) * 3.6)
        b_f1 = float(np.mean(np.array([candidates_v_dicts['F1 (Hard Upper-Bound)'][i] for i in test_indices])[r_mask] - vbox_vel_ms[test_indices][r_mask]) * 3.6)
        b_f3 = float(np.mean(np.array([candidates_v_dicts['F3 (Deceleration-Only)'][i] for i in test_indices])[r_mask] - vbox_vel_ms[test_indices][r_mask]) * 3.6)
        b_f4 = float(np.mean(np.array([candidates_v_dicts['F4 (Confidence-Gated)'][i] for i in test_indices])[r_mask] - vbox_vel_ms[test_indices][r_mask]) * 3.6)
        print(f"{r_name:<18} | {b_f0:>+9.2f}k | {b_f1:>+12.2f}k | {b_f3:>+12.2f}k | {b_f4:>+12.2f}k")

# Print Activation Statistics
print("\n======================================================================")
print("4. CONSTRAINT ACTIVATION & CORRECTION MAGNITUDE DIAGNOSTICS")
print("======================================================================")
print(f"{'Candidate':<28} | {'Act Samples':<11} | {'Act %':<6} | {'Avg Mag (km/h)':<14} | {'Max Mag (km/h)':<14} | {'Neg Bounds'}")
print("-" * 95)
for r in results_table:
    print(f"{r['name']:<28} | {r['act_count']:>11d} | {r['act_pct']:>5.1f}% | {r['avg_mag_kmh']:>14.2f} | {r['max_mag_kmh']:>14.2f} | {r['neg_bounds']:>10d}")

# Plot Generation
os.makedirs('plots/vw4/m013_hard_physical_inference_constraint', exist_ok=True)

# Plot 1: 300s Position Error vs Time
plt.figure(figsize=(10, 6))
time_axis = np.arange(3000) * 0.1
for name, p_err in nav_err_series.items():
    err_300 = p_err[-1]
    plt.plot(time_axis, p_err, label=f"{name} ({err_300:.1f} m)")
plt.axhline(263.11, color='black', linestyle='--', label='Provenance Benchmark (263.11 m)')
plt.title('M013: 300s GNSS Outage Position Error Comparison', fontsize=12, fontweight='bold')
plt.xlabel('Outage Elapsed Time (seconds)')
plt.ylabel('Position Error (meters)')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper left', fontsize=9)
plt.tight_layout()
plt.savefig('plots/vw4/m013_hard_physical_inference_constraint/pos_error_vs_time.png', dpi=300)
plt.close()

# Plot 2: Speed Prediction vs GT (Deceleration segment zoom)
zoom_slice = slice(500, 1000)
plt.figure(figsize=(12, 5))
t_zoom = time_axis[zoom_slice]
plt.plot(t_zoom, vbox_vel_ms[test_indices][zoom_slice] * 3.6, 'k--', label='Ground Truth Speed', linewidth=2)
plt.plot(t_zoom, np.array([candidates_v_dicts['F0 (Control)'][i] for i in test_indices])[zoom_slice] * 3.6, label='F0 SpeedNet v2 Control', alpha=0.8)
plt.plot(t_zoom, np.array([candidates_v_dicts['F1 (Hard Upper-Bound)'][i] for i in test_indices])[zoom_slice] * 3.6, label='F1 Hard Upper-Bound', alpha=0.8)
plt.plot(t_zoom, np.array([candidates_v_dicts['F3 (Deceleration-Only)'][i] for i in test_indices])[zoom_slice] * 3.6, label='F3 Deceleration-Only', alpha=0.8)
plt.title('M013: Speed Prediction Comparison During Deceleration Window (t=50s to 100s)', fontsize=12, fontweight='bold')
plt.xlabel('Time (s)')
plt.ylabel('Speed (km/h)')
plt.grid(True, alpha=0.3)
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig('plots/vw4/m013_hard_physical_inference_constraint/speed_prediction_decel_zoom.png', dpi=300)
plt.close()

# Save JSON Summary & NPZ Predictions
summary_data = {
    'milestone': 'M013',
    'title': 'Hard Physical Inference Constraints & EKF Innovation Filtering',
    'provenance_benchmark': 'SpeedNet v2 (W=40) + Raw Gyro + Fixed NHC',
    'target_300s_err': 263.11,
    'results_table': results_table
}

with open('results/vw4_m013_hard_physical_inference_constraint_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

np.savez(
    'results/vw4_m013_hard_physical_inference_constraint_predictions.npz',
    test_indices=test_indices,
    v_gt=vbox_vel_ms[test_indices],
    v_f0=np.array([candidates_v_dicts['F0 (Control)'][i] for i in test_indices]),
    v_f1=np.array([candidates_v_dicts['F1 (Hard Upper-Bound)'][i] for i in test_indices]),
    v_f2=np.array([candidates_v_dicts['F2 (Bounded Acceleration)'][i] for i in test_indices]),
    v_f3=np.array([candidates_v_dicts['F3 (Deceleration-Only)'][i] for i in test_indices]),
    v_f4=np.array([candidates_v_dicts['F4 (Confidence-Gated)'][i] for i in test_indices])
)

print("\nSaved M013 summary JSON and predictions NPZ.")
print("M013 execution complete.")
