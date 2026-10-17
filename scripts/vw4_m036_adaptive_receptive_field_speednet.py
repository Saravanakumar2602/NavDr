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
w_yaw = -gyro_pitch

j_long_array = np.zeros(len(t_sync))
for k in range(1, len(t_sync)):
    j_long_array[k] = (a_long[k] - a_long[k-1]) / dt

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)

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

PRE_SAMPLES = 300

# Causal rolling IMU variance pre-computation for M013 F4
rolling_var_a = np.zeros(n_total)
for i in range(5, n_total):
    rolling_var_a[i] = np.var(a_long[i-5:i])
var_thresh_m013 = np.percentile(rolling_var_a[:idx_val_end], 75)
w_turn_thresh = np.radians(5.0)

# ── SpeedNet Prediction Engine ─────────────────────────────────────────────
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

    return v_dict, w_dict, prob_stat_dict, sum(p.numel() for p in model.parameters())

def get_f4_speed_dict(v_raw_dict):
    v_f4_dict = {}
    v_prev = 0.0
    for idx in range(n_total):
        v_net = v_raw_dict.get(idx, 0.0)
        a_m = a_long[idx]
        if rolling_var_a[idx] <= var_thresh_m013 and np.abs(w_yaw[idx]) <= w_turn_thresh:
            v_phys_bound = max(0.0, v_prev + a_m * dt)
            v_corr = min(v_net, v_phys_bound)
        else:
            v_corr = v_net
        v_f4_dict[idx] = v_corr
        v_prev = v_corr
    return v_f4_dict

print("Loading SpeedNet candidates...", flush=True)

# Candidate Models
# F0: W=40 Control Baseline
v_raw_w40, w_raw_w40, prob_stat_w40, params_w40 = get_speednet_predictions(40, 'models/speednet_v2_w40.pth')
v_f4_w40 = get_f4_speed_dict(v_raw_w40)

# F1: W=30 Shorter Receptive Field
v_raw_w30, w_raw_w30, prob_stat_w30, params_w30 = get_speednet_predictions(30, 'models/speednet_v2_w30.pth')
v_f4_w30 = get_f4_speed_dict(v_raw_w30)

# F2: W=50 Longer Receptive Field
v_raw_w50, w_raw_w50, prob_stat_w50, params_w50 = get_speednet_predictions(50, 'models/speednet_v2_w50.pth')
v_f4_w50 = get_f4_speed_dict(v_raw_w50)

# F3: Multi-Branch Causal Receptive-Field Fusion (W30/W40/W50 Adaptive Ensemble)
# Dynamic weighting based on causal acceleration variance:
# During high acceleration transients (high variance), shorter window W30 has less lag.
# During smooth cruise (low variance), longer window W50 has smoother noise reduction.
v_f4_multibranch = {}
prob_stat_multibranch = {}

for idx in range(n_total):
    var_c = rolling_var_a[idx]
    v30 = v_f4_w30.get(idx, 0.0)
    v40 = v_f4_w40.get(idx, 0.0)
    v50 = v_f4_w50.get(idx, 0.0)

    p30 = prob_stat_w30.get(idx, 0.0)
    p40 = prob_stat_w40.get(idx, 0.0)
    p50 = prob_stat_w50.get(idx, 0.0)

    if var_c > var_thresh_m013: # Dynamic transient -> weight W30/W40 higher (less lag)
        w30, w40, w50 = 0.50, 0.35, 0.15
    else: # Smooth cruise -> weight W40/W50 higher (smoother)
        w30, w40, w50 = 0.20, 0.40, 0.40

    v_f4_multibranch[idx] = w30 * v30 + w40 * v40 + w50 * v50
    prob_stat_multibranch[idx] = w30 * p30 + w40 * p40 + w50 * p50

params_multibranch = params_w30 + params_w40 + params_w50

# ── Navigation Engine for M036 ─────────────────────────────────────────────
def run_navigation_m036(
    v_ml_dict, prob_stat_dict, sim_start_idx=108000, duration_sec=300
):
    n = int(duration_sec / dt)
    pre_samples = PRE_SAMPLES
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
    R_nhc = 0.20**2

    H_zupt = np.zeros((2, 7))
    H_zupt[0, 2] = 1.0; H_zupt[1, 3] = 1.0
    R_z = (0.20**2) * np.eye(2)

    x_hist = []
    v_est_history = []
    v_meas_history = []

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
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], x_state[4] + psi_diff])
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

            # M028 Causal Jerk APM Logic (Benchmark Exact)
            if (not is_stat_pred) and (len(v_est_history) >= 5):
                is_decel = (a_long[idx] < -0.5)
                is_turn_ok = (np.abs(w_yaw[idx]) <= np.radians(3.0))

                if is_decel and is_turn_ok:
                    j_val = j_long_array[idx]
                    if j_val < -1.00:
                        delta_v_imu = np.sum(a_long[idx-4:idx+1]) * dt
                        v_anchor = v_est_history[-5]
                        z_apm = max(0.0, v_anchor + delta_v_imu)

                        if v_speednet > z_apm:
                            raw_corr = v_speednet - z_apm
                            bounded_corr = min(raw_corr, 0.50)
                            v_meas = v_speednet - bounded_corr

            v_meas_history.append(v_meas)

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
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
    return x_dr, y_dr, v_dr, psi_deg, np.array(v_meas_history)

def compute_metrics_m036(x_dr, y_dr, v_dr, psi_deg, v_meas_arr, start, dur):
    n = int(dur / dt)
    ls, ln = vbox_lat[start], vbox_lon[start]
    xgt = (np.radians(vbox_lon[start:start+n]) - np.radians(ln)) * R_earth * np.cos(np.radians(ls))
    ygt = (np.radians(vbox_lat[start:start+n]) - np.radians(ls)) * R_earth
    vgt = vbox_vel_ms[start:start+n]
    pe  = np.sqrt((x_dr-xgt)**2 + (y_dr-ygt)**2)

    speed_mae  = float(np.mean(np.abs(v_meas_arr - vgt)) * 3.6)
    speed_bias = float(np.mean(v_meas_arr - vgt) * 3.6)

    heading_gt_rad = np.radians(vbox_heading_deg[start:start+n])
    dx = x_dr - xgt
    dy = y_dr - ygt
    along_track =  dx * np.sin(heading_gt_rad) + dy * np.cos(heading_gt_rad)
    cross_track = -dx * np.cos(heading_gt_rad) + dy * np.sin(heading_gt_rad)

    return {
        'final_pos_m': round(float(pe[-1]), 2),
        'mean_pos_m':  round(float(np.mean(pe)), 2),
        'max_pos_m':   round(float(np.max(pe)), 2),
        'final_along_m': round(float(along_track[-1]), 2),
        'final_cross_m': round(float(cross_track[-1]), 2),
        'speed_mae_kmh': round(speed_mae, 2),
        'speed_bias_kmh': round(speed_bias, 2),
        'pos_err_arr': pe,
        'x_dr': x_dr,
        'y_dr': y_dr
    }

# ── 1. Prove Active Control Benchmark Reproduction Exactly ─────────────────
print("\n======================================================================")
print("1. CONTROL BENCHMARK REPRODUCTION VERIFICATION")
print("======================================================================")

xd, yd, vd, pd_deg, vm = run_navigation_m036(v_f4_w40, prob_stat_w40, sim_start_idx=start_idx, duration_sec=300)
m_f0 = compute_metrics_m036(xd, yd, vd, pd_deg, vm, start_idx, 300)

p60  = compute_metrics_m036(*run_navigation_m036(v_f4_w40, prob_stat_w40, sim_start_idx=start_idx, duration_sec=60)[:4], run_navigation_m036(v_f4_w40, prob_stat_w40, sim_start_idx=start_idx, duration_sec=60)[4], start_idx, 60)['final_pos_m']
p120 = compute_metrics_m036(*run_navigation_m036(v_f4_w40, prob_stat_w40, sim_start_idx=start_idx, duration_sec=120)[:4], run_navigation_m036(v_f4_w40, prob_stat_w40, sim_start_idx=start_idx, duration_sec=120)[4], start_idx, 120)['final_pos_m']
p300 = m_f0['final_pos_m']

print(f"  Measured Active Benchmark (F0): 60s = {p60:.2f} m | 120s = {p120:.2f} m | 300s = {p300:.2f} m")
print(f"  Target Benchmark:               60s = 27.35 m | 120s = 426.85 m | 300s = 218.93 m")
assert abs(p300 - 218.93) < 0.5, f"Control reproduction failed! Measured {p300:.2f}m vs Target 218.93m"
print("  --> ACTIVE BENCHMARK REPRODUCTION 100% SUCCESSFUL!\n")

# ── 2. Candidate Specifications for Ablation & Multi-Branch ────────────────
candidate_models = [
    {
        'id': 'F0 (Control W40)',
        'name': 'F0 (SpeedNet v2 W=40 Control)',
        'v_dict': v_f4_w40,
        'p_dict': prob_stat_w40,
        'params': params_w40
    },
    {
        'id': 'F1 (W30 Shorter)',
        'name': 'F1 (SpeedNet v2 W=30 Shorter)',
        'v_dict': v_f4_w30,
        'p_dict': prob_stat_w30,
        'params': params_w30
    },
    {
        'id': 'F2 (W50 Longer)',
        'name': 'F2 (SpeedNet v2 W=50 Longer)',
        'v_dict': v_f4_w50,
        'p_dict': prob_stat_w50,
        'params': params_w50
    },
    {
        'id': 'F3 (Multi-Branch Ensemble)',
        'name': 'F3 (Adaptive Multi-Branch W30/W40/W50)',
        'v_dict': v_f4_multibranch,
        'p_dict': prob_stat_multibranch,
        'params': params_multibranch
    }
]

# ── PHASE 4: POINTWISE SPEED & TEMPORAL LAG ANALYSIS (Validation Set) ─────
print("======================================================================")
print("PHASE 4: POINTWISE SPEED & TEMPORAL LAG ANALYSIS (Validation Set 88566:107535)")
print("======================================================================")

val_indices = np.arange(idx_train_end, idx_val_end)
v_gt_val = vbox_vel_ms[val_indices]
a_l_val  = a_long[val_indices]

mask_stat_val = (v_gt_val < 0.1)
mask_brk_val  = (~mask_stat_val) & (a_l_val < -0.3)
mask_acc_val  = (~mask_stat_val) & (a_l_val > 0.3)
mask_crs_val  = (~mask_stat_val) & (np.abs(a_l_val) <= 0.3) & (np.abs(w_yaw[val_indices]) <= np.radians(5.0))
mask_trn_val  = (~mask_stat_val) & (np.abs(w_yaw[val_indices]) > np.radians(10.0))

print(f"{'Variant Name':<32} | {'Overall MAE':<11} | {'Braking MAE':<11} | {'Accel MAE':<11} | {'Cruise MAE':<11} | {'Turn MAE':<11}")
print("-" * 105)

for spec in candidate_models:
    v_pred_val = np.array([spec['v_dict'].get(i, 0.0) for i in val_indices])
    e_val = np.abs(v_pred_val - v_gt_val) * 3.6

    ov_mae  = float(np.mean(e_val))
    brk_mae = float(np.mean(e_val[mask_brk_val]))
    acc_mae = float(np.mean(e_val[mask_acc_val]))
    crs_mae = float(np.mean(e_val[mask_crs_val]))
    trn_mae = float(np.mean(e_val[mask_trn_val]))

    print(f"{spec['name']:<32} | {ov_mae:>7.2f} km/h | {brk_mae:>7.2f} km/h | {acc_mae:>7.2f} km/h | {crs_mae:>7.2f} km/h | {trn_mae:>7.2f} km/h")

# ── PHASE 5: VALIDATION NAVIGATION EVALUATION (`88566:107535`) ─────────────
print("\n======================================================================")
print("PHASE 5: VALIDATION NAVIGATION EVALUATION (Partition 88566:107535)")
print("======================================================================")

best_val_err = float('inf')
best_val_name = 'F0 (Control W40)'
best_spec = candidate_models[0]

val_nav_results = []
for spec in candidate_models:
    xd, yd, vd, pd_deg, vm = run_navigation_m036(
        spec['v_dict'], spec['p_dict'], sim_start_idx=idx_train_end + 300, duration_sec=300
    )
    m_val = compute_metrics_m036(xd, yd, vd, pd_deg, vm, idx_train_end + 300, 300)
    val_nav_results.append((spec['id'], spec['name'], m_val['final_pos_m'], m_val['mean_pos_m']))
    print(f"  Val Candidate: {spec['name']:<40} -> Val 300s Error = {m_val['final_pos_m']:.2f} m (Mean = {m_val['mean_pos_m']:.2f} m)", flush=True)

    if m_val['final_pos_m'] < (best_val_err - 0.5):
        best_val_err = m_val['final_pos_m']
        best_val_name = spec['name']
        best_spec = spec

print(f"\n  Selected Validation Winner: {best_val_name} (Val Error = {best_val_err:.2f} m)", flush=True)

# ── PHASE 6: LOCKED UNSEEN TEST EVALUATION (`start_idx = 108,000`) ─────────
print("\n======================================================================")
print("PHASE 6: LOCKED UNSEEN TEST EVALUATION (start_idx = 108,000)")
print("======================================================================")

test_indices = np.arange(start_idx, start_idx + 3000)
v_gt_test = vbox_vel_ms[test_indices]
a_l_test  = a_long[test_indices]
mask_stat_t = (v_gt_test < 0.1)
mask_brk_t  = (~mask_stat_t) & (a_l_test < -0.3)

results_table = []
nav_err_series = {}

print(f"{'Variant Name':<34} | {'Speed MAE':<9} | {'Brake MAE':<10} | {'60s (m)':<7} | {'120s (m)':<8} | {'300s (m)':<8} | {'vs 263.11m'} | {'vs 220.12m'} | {'vs 218.93m'}")
print("-" * 133)

for spec in candidate_models:
    cid = spec['id']
    dur_res = {}
    m_300 = None
    vm_300 = None

    for dur in [60, 120, 300]:
        xd, yd, vd, pd_deg, vm = run_navigation_m036(
            spec['v_dict'], spec['p_dict'], sim_start_idx=start_idx, duration_sec=dur
        )
        m = compute_metrics_m036(xd, yd, vd, pd_deg, vm, start_idx, dur)
        dur_res[dur] = m['final_pos_m']
        if dur == 300:
            m_300 = m
            vm_300 = vm

    nav_err_series[cid] = m_300['pos_err_arr']

    v_diff_brk = (vm_300[mask_brk_t] - v_gt_test[mask_brk_t]) * 3.6
    brk_mae  = float(np.mean(np.abs(v_diff_brk)))
    brk_bias = float(np.mean(v_diff_brk))

    pct_263 = float((dur_res[300] - 263.11) / 263.11 * 100.0)
    pct_220 = float((dur_res[300] - 220.12) / 220.12 * 100.0)
    pct_218 = float((dur_res[300] - 218.93) / 218.93 * 100.0)

    b_218 = "CONTROL" if "F0" in cid else f"{pct_218:>+6.1f}%"

    results_table.append({
        'id': cid,
        'name': spec['name'],
        'params': spec['params'],
        'speed_mae_kmh': m_300['speed_mae_kmh'],
        'brk_mae_kmh': round(brk_mae, 2),
        'brk_bias_kmh': round(brk_bias, 2),
        'err_60s': dur_res[60],
        'err_120s': dur_res[120],
        'err_300s': dur_res[300],
        'mean_pos_m': m_300['mean_pos_m'],
        'final_along_m': m_300['final_along_m'],
        'final_cross_m': m_300['final_cross_m'],
        'pct_vs_263': round(pct_263, 1),
        'pct_vs_220': round(pct_220, 1),
        'pct_vs_218': round(pct_218, 1)
    })

    print(f"{spec['name']:<34} | {m_300['speed_mae_kmh']:>6.2f}k  | {brk_mae:>7.2f}k   | {dur_res[60]:>7.2f} | {dur_res[120]:>8.2f} | {dur_res[300]:>8.2f} | {pct_263:>+9.1f}% | {pct_220:>+9.1f}% | {b_218:>10}")

# Also output Validation Selected Winner explicit row (F4 / F5 entry)
val_winner_entry = next(r for r in results_table if r['id'] == best_spec['id'])
print(f"\n  Validation Winner Evaluation ({best_val_name}): 300s = {val_winner_entry['err_300s']:.2f} m (vs Benchmark 218.93 m)")

# Save Diagnostic Plots
os.makedirs('plots/vw4/m036_adaptive_receptive_field_speednet', exist_ok=True)
time_axis = np.arange(3000) * 0.1

plt.figure(figsize=(10, 6))
for cid, p_err in nav_err_series.items():
    plt.plot(time_axis, p_err, label=f"{cid} ({p_err[-1]:.1f} m)")
plt.axhline(263.11, color='red', linestyle='--', label='Pre-M013 Benchmark (263.11 m)')
plt.axhline(220.12, color='blue', linestyle=':', label='M019 Baseline (220.12 m)')
plt.axhline(218.93, color='green', linestyle='-', label='M028 Active Benchmark (218.93 m)')
plt.title('M036: Receptive Field SpeedNet Backbone Tuning 300s Position Error', fontsize=12, fontweight='bold')
plt.xlabel('Outage Elapsed Time (s)')
plt.ylabel('Position Error (m)')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.savefig('plots/vw4/m036_adaptive_receptive_field_speednet/pos_error_vs_time.png', dpi=300)
plt.close()

# Save Summary JSON
summary_data = {
    'milestone': 'M036',
    'title': 'Adaptive Receptive-Field SpeedNet Backbone Tuning',
    'active_benchmark': 218.93,
    'selected_val_winner': best_val_name,
    'val_nav_results': val_nav_results,
    'test_results_table': results_table
}

with open('results/vw4_m036_adaptive_receptive_field_speednet_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

print("\nSaved M036 summary JSON and diagnostic plot.")
print("M036 execution complete.")
