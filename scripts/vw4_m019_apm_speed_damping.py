import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
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

PRE_SAMPLES = 300

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

print("Loading SpeedNet v2 (W=40) predictions...", flush=True)
v_ml_raw_dict, w_ml_raw_dict, prob_stat_dict = get_speednet_predictions(window_size=40)

# Causal rolling IMU variance pre-computation
rolling_var_a = np.zeros(n_total)
for i in range(5, n_total):
    rolling_var_a[i] = np.var(a_long[i-5:i])

# M013 F4 Speed Dictionary
v_f4_dict = {}
v_prev_f4 = 0.0
var_thresh = np.percentile(rolling_var_a[:idx_val_end], 75)
w_turn_thresh = np.radians(5.0)

for idx in range(n_total):
    v_net = v_ml_raw_dict.get(idx, 0.0)
    a_m = a_long[idx]
    if rolling_var_a[idx] <= var_thresh and np.abs(w_yaw[idx]) <= w_turn_thresh:
        v_phys_bound = max(0.0, v_prev_f4 + a_m * dt)
        v_corr = min(v_net, v_phys_bound)
    else:
        v_corr = v_net
    v_f4_dict[idx] = v_corr
    v_prev_f4 = v_corr

# ── Navigation & EKF Engine for M019 APM Speed Damping ──────────────────
def run_navigation_m019(
    v_ml_dict, prob_stat_dict, sim_start_idx=108000, duration_sec=300,
    enable_apm=False, apm_accel_thresh=-0.5, apm_bound_ms=1.5, apm_w_thresh_deg=5.0, enable_w_exclusion=False
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
    R_nhc = 0.2**2

    H_zupt = np.zeros((2, 7))
    H_zupt[0, 2] = 1.0; H_zupt[1, 3] = 1.0
    R_z = (0.20**2) * np.eye(2)

    x_hist = []
    v_est_history = []

    apm_stats = {
        'activations': 0,
        'corrections': [],
        'braking_updates': 0
    }

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

            # APM Pseudo-Measurement Logic
            if enable_apm and (not is_stat_pred) and (len(v_est_history) >= 5):
                is_decel = (a_long[idx] < apm_accel_thresh)
                is_turn_ok = (not enable_w_exclusion) or (np.abs(w_yaw[idx]) <= np.radians(apm_w_thresh_deg))

                if is_decel and is_turn_ok:
                    apm_stats['activations'] += 1
                    if vbox_vel_ms[idx] > 0.1 and a_long[idx] < -0.3:
                        apm_stats['braking_updates'] += 1

                    # 0.5s causal integration interval (5 samples)
                    delta_v_imu = np.sum(a_long[idx-4:idx+1]) * dt
                    v_anchor = v_est_history[-5]
                    z_apm = max(0.0, v_anchor + delta_v_imu)

                    # APM constraint: if SpeedNet overestimates relative to APM integrated velocity
                    if v_speednet > z_apm:
                        raw_corr = v_speednet - z_apm
                        bounded_corr = min(raw_corr, apm_bound_ms)
                        v_meas = v_speednet - bounded_corr
                        apm_stats['corrections'].append(bounded_corr * 3.6) # in km/h

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

    t1 = time.perf_counter()
    arr  = np.array(x_hist)
    x_dr = arr[:, 0] - arr[0, 0]
    y_dr = arr[:, 1] - arr[0, 1]
    v_dr = np.sqrt(arr[:, 2]**2 + arr[:, 3]**2)
    psi_deg = np.degrees(arr[:, 4])
    lat_ms = ((t1 - t0) / (pre_samples + n)) * 1000.0
    return x_dr, y_dr, v_dr, psi_deg, apm_stats, lat_ms

def compute_metrics_m019(x_dr, y_dr, v_dr, psi_deg, v_ml_dict, start, dur):
    n = int(dur / dt)
    ls, ln = vbox_lat[start], vbox_lon[start]
    xgt = (np.radians(vbox_lon[start:start+n]) - np.radians(ln)) * R_earth * np.cos(np.radians(ls))
    ygt = (np.radians(vbox_lat[start:start+n]) - np.radians(ls)) * R_earth
    vgt = vbox_vel_ms[start:start+n]
    pe  = np.sqrt((x_dr-xgt)**2 + (y_dr-ygt)**2)

    v_preds = np.array([v_ml_dict.get(i, 0.0) for i in range(start, start+n)])
    speed_mae  = float(np.mean(np.abs(v_preds - vgt)) * 3.6)
    speed_bias = float(np.mean(v_preds - vgt) * 3.6)

    return {
        'final_pos_m': round(float(pe[-1]), 2),
        'max_pos_m':   round(float(np.max(pe)), 2),
        'speed_mae_kmh': round(speed_mae, 2),
        'speed_bias_kmh': round(speed_bias, 2),
        'pos_err_arr': pe,
        'x_dr': x_dr,
        'y_dr': y_dr
    }

# ── 1. Prove M014 Control Reproduction Exactly ────────────────────────────
print("\n======================================================================")
print("1. M014 CONTROL REPRODUCTION VERIFICATION")
print("======================================================================")

xd, yd, vd, pd, _, _ = run_navigation_m019(v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=300)
m_f0 = compute_metrics_m019(xd, yd, vd, pd, v_f4_dict, start_idx, 300)

p60  = compute_metrics_m019(*run_navigation_m019(v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=60)[:4], v_f4_dict, start_idx, 60)['final_pos_m']
p120 = compute_metrics_m019(*run_navigation_m019(v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=120)[:4], v_f4_dict, start_idx, 120)['final_pos_m']
p300 = m_f0['final_pos_m']

print(f"  Measured M014 Control (F0):  60s = {p60:.2f} m | 120s = {p120:.2f} m | 300s = {p300:.2f} m")
print(f"  M014 Benchmark Target:       60s = 27.36 m | 120s = 428.45 m | 300s = 233.18 m")
assert abs(p300 - 233.18) < 0.5, f"M014 Control reproduction failed! Measured {p300:.2f}m vs Target 233.18m"
print("  --> M014 BASELINE CONTROL REPRODUCTION 100% SUCCESSFUL!\n")

# ── 2. Validation Grid Search for APM Parameters (Partition 88566:107535) ─
print("======================================================================")
print("2. VALIDATION APM PARAMETER GRID SEARCH (Partition 88566:107535)")
print("======================================================================")

best_val_err = float('inf')
best_apm_params = {}

for bound_ms in [0.5, 1.0, 1.5, 2.0]:
    for w_thresh in [3.0, 5.0, 10.0]:
        xd, yd, vd, pd, _, _ = run_navigation_m019(
            v_f4_dict, prob_stat_dict, sim_start_idx=idx_train_end + 300, duration_sec=300,
            enable_apm=True, apm_accel_thresh=-0.5, apm_bound_ms=bound_ms, apm_w_thresh_deg=w_thresh, enable_w_exclusion=True
        )
        m_val = compute_metrics_m019(xd, yd, vd, pd, v_f4_dict, idx_train_end + 300, 300)
        print(f"  Val APM Search: bound={bound_ms:.1f}m/s, w_thresh={w_thresh:.1f}deg -> Val 300s Error = {m_val['final_pos_m']:.2f} m", flush=True)
        if m_val['final_pos_m'] < best_val_err:
            best_val_err = m_val['final_pos_m']
            best_apm_params = {'bound_ms': bound_ms, 'w_thresh': w_thresh}

print(f"  Selected Validation APM Parameters: {best_apm_params} (Val Error = {best_val_err:.2f} m)\n", flush=True)

# ── 3. Candidate Sweep Execution ──────────────────────────────────────────
candidate_specs = [
    {
        'id': 'F0 (Control M014)',
        'desc': 'SpeedNet v2 W=40 Baseline Control (No APM)',
        'kwargs': {'enable_apm': False}
    },
    {
        'id': 'F1 (Unconstrained APM)',
        'desc': 'Unconstrained APM (a_long < -0.5 m/s²)',
        'kwargs': {'enable_apm': True, 'apm_accel_thresh': -0.5, 'apm_bound_ms': 100.0, 'enable_w_exclusion': False}
    },
    {
        'id': 'F2 (Bounded APM)',
        'desc': f"Bounded APM (bound={best_apm_params['bound_ms']} m/s)",
        'kwargs': {'enable_apm': True, 'apm_accel_thresh': -0.5, 'apm_bound_ms': best_apm_params['bound_ms'], 'enable_w_exclusion': False}
    },
    {
        'id': 'F3 (Turn-Exclusion APM)',
        'desc': f"Bounded APM + Turn Exclusion (w_thresh={best_apm_params['w_thresh']}°)",
        'kwargs': {'enable_apm': True, 'apm_accel_thresh': -0.5, 'apm_bound_ms': best_apm_params['bound_ms'], 'apm_w_thresh_deg': best_apm_params['w_thresh'], 'enable_w_exclusion': True}
    },
    {
        'id': 'F4 (Best Validated + M014)',
        'desc': 'Best Validated APM Strategy (F3)',
        'kwargs': {'enable_apm': True, 'apm_accel_thresh': -0.5, 'apm_bound_ms': best_apm_params['bound_ms'], 'apm_w_thresh_deg': best_apm_params['w_thresh'], 'enable_w_exclusion': True}
    }
]

results_table = []
nav_err_series = {}
traj_series = {}
apm_diagnostics_dict = {}

test_indices = np.arange(start_idx, start_idx + 3000)
v_gt_test = vbox_vel_ms[test_indices]
a_l_test  = a_long[test_indices]
w_y_test  = np.abs(w_yaw[test_indices])

mask_stat = (v_gt_test < 0.1)
mask_acc  = (~mask_stat) & (a_l_test > 0.3)
mask_brk  = (~mask_stat) & (a_l_test < -0.3)

print("======================================================================")
print("3. CANDIDATE SWEEP UNSEEN TEST RESULTS (start_idx = 108,000)")
print("======================================================================")
print(f"{'Variant Name':<26} | {'Speed MAE':<9} | {'Brake MAE':<10} | {'60s (m)':<7} | {'120s (m)':<8} | {'300s (m)':<8} | {'vs 263.11m'} | {'vs 254.11m'} | {'vs 233.18m'}")
print("-" * 125)

for spec in candidate_specs:
    cid = spec['id']
    dur_res = {}
    m_300 = None
    stats_300 = None

    for dur in [60, 120, 300]:
        xd, yd, vd, pd, stats, _ = run_navigation_m019(
            v_f4_dict, prob_stat_dict, sim_start_idx=start_idx, duration_sec=dur,
            **spec['kwargs']
        )
        m = compute_metrics_m019(xd, yd, vd, pd, v_f4_dict, start_idx, dur)
        dur_res[dur] = m['final_pos_m']
        if dur == 300:
            m_300 = m
            stats_300 = stats
            traj_series[cid] = (m['x_dr'], m['y_dr'])

    nav_err_series[cid] = m_300['pos_err_arr']
    apm_diagnostics_dict[cid] = stats_300

    v_pred_test = np.array([v_f4_dict.get(i, 0.0) for i in test_indices])
    v_diff_brk = (v_pred_test[mask_brk] - v_gt_test[mask_brk]) * 3.6
    brk_mae  = float(np.mean(np.abs(v_diff_brk)))

    pct_263 = float((dur_res[300] - 263.11) / 263.11 * 100.0)
    pct_254 = float((dur_res[300] - 254.11) / 254.11 * 100.0)
    pct_233 = float((dur_res[300] - 233.18) / 233.18 * 100.0)

    b_233 = "CONTROL" if "F0" in cid else f"{pct_233:+6.1f}%"

    results_table.append({
        'name': cid,
        'desc': spec['desc'],
        'speed_mae_kmh': m_300['speed_mae_kmh'],
        'speed_bias_kmh': m_300['speed_bias_kmh'],
        'brk_mae_kmh': round(brk_mae, 2),
        'err_60s': dur_res[60],
        'err_120s': dur_res[120],
        'err_300s': dur_res[300],
        'pct_vs_263': round(pct_263, 1),
        'pct_vs_254': round(pct_254, 1),
        'pct_vs_233': round(pct_233, 1)
    })

    print(f"{cid:<26} | {m_300['speed_mae_kmh']:>6.2f}k  | {brk_mae:>7.2f}k   | {dur_res[60]:>7.2f} | {dur_res[120]:>8.2f} | {dur_res[300]:>8.2f} | {pct_263:>+9.1f}% | {pct_254:>+9.1f}% | {b_233:>10}")

# ── 4. APM Diagnostic Metrics Summary ──────────────────────────────────────
print("\n======================================================================")
print("4. APM SPEED DAMPING DIAGNOSTIC METRICS SUMMARY")
print("======================================================================")
print(f"{'Candidate':<26} | {'Activations':<12} | {'Braking Updates':<16} | {'Mean Corr (km/h)':<18} | {'Max Corr (km/h)'}")
print("-" * 95)
for cid, stats in apm_diagnostics_dict.items():
    act = stats['activations']
    brk_u = stats['braking_updates']
    corrs = stats['corrections']
    m_corr = float(np.mean(corrs)) if len(corrs) > 0 else 0.0
    mx_corr = float(np.max(corrs)) if len(corrs) > 0 else 0.0
    print(f"{cid:<26} | {act:>12d} | {brk_u:>16d} | {m_corr:>18.2f} | {mx_corr:>15.2f}")

# ── Save Diagnostic Plots ─────────────────────────────────────────────────
os.makedirs('plots/vw4/m019_apm_speed_damping', exist_ok=True)
time_axis = np.arange(3000) * 0.1

# Plot 1: 300s Position Error vs Time
plt.figure(figsize=(10, 6))
for cid, p_err in nav_err_series.items():
    plt.plot(time_axis, p_err, label=f"{cid} ({p_err[-1]:.1f} m)")
plt.axhline(263.11, color='red', linestyle='--', label='Historical Benchmark (263.11 m)')
plt.axhline(254.11, color='blue', linestyle=':', label='M013 F4 Control (254.11 m)')
plt.axhline(233.18, color='green', linestyle='-', label='M014 Benchmark (233.18 m)')
plt.title('M019: APM Speed Damping 300s Navigation Error', fontsize=12, fontweight='bold')
plt.xlabel('Outage Elapsed Time (s)')
plt.ylabel('Position Error (m)')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper left', fontsize=8)
plt.tight_layout()
plt.savefig('plots/vw4/m019_apm_speed_damping/pos_error_vs_time.png', dpi=300)
plt.close()

# Plot 2: Trajectory Comparison
plt.figure(figsize=(9, 8))
ls_test, ln_test = vbox_lat[start_idx], vbox_lon[start_idx]
xgt_test = (np.radians(vbox_lon[test_indices]) - np.radians(ln_test)) * R_earth * np.cos(np.radians(ls_test))
ygt_test = (np.radians(vbox_lat[test_indices]) - np.radians(ls_test)) * R_earth
plt.plot(xgt_test, ygt_test, 'k-', linewidth=2.5, label='VBOX Ground Truth Trajectory')

for cid, (xd, yd) in traj_series.items():
    if cid in ['F0 (Control M014)', 'F1 (Unconstrained APM)', 'F3 (Turn-Exclusion APM)']:
        plt.plot(xd, yd, label=f"{cid} ({nav_err_series[cid][-1]:.1f} m)")

plt.title('M019: 2D Dead-Reckoning Trajectory Comparison', fontsize=12, fontweight='bold')
plt.xlabel('East Displacement (m)')
plt.ylabel('North Displacement (m)')
plt.grid(True, alpha=0.3)
plt.legend(loc='best', fontsize=9)
plt.axis('equal')
plt.tight_layout()
plt.savefig('plots/vw4/m019_apm_speed_damping/trajectory_comparison.png', dpi=300)
plt.close()

# Save JSON Summary & NPZ Predictions
summary_data = {
    'milestone': 'M019',
    'title': 'Acceleration-Integrated Pseudo-Measurement (APM) Speed Damping',
    'historical_benchmark': 263.11,
    'm013_control': 254.11,
    'm014_control': 233.18,
    'best_apm_params': best_apm_params,
    'results_table': results_table
}

with open('results/vw4_m019_apm_speed_damping_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

np.savez(
    'results/vw4_m019_apm_speed_damping_predictions.npz',
    test_indices=test_indices,
    v_gt=vbox_vel_ms[test_indices],
    pos_err_f0=nav_err_series['F0 (Control M014)'],
    pos_err_f1=nav_err_series['F1 (Unconstrained APM)'],
    pos_err_f3=nav_err_series['F3 (Turn-Exclusion APM)']
)

print("\nSaved M019 summary JSON and predictions NPZ.")
print("M019 execution complete.")
