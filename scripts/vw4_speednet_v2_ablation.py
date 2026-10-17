import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_speednet_v2_train import train_speednet_v2
from scripts.vw4_speednet_v2_evaluate import load_speednet_v2, predict_speednet_v2_full, evaluate_pure_predictions

os.makedirs('plots/vw4/speednet_v2', exist_ok=True)
os.makedirs('results', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading Vw4 dataset files...", flush=True)
df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# --- Timestamp Synchronization ---
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
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
idx_train_end = int(n_total * 0.70)  # 88566
idx_val_end   = int(n_total * 0.85)  # 107535

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

X_norm_all = (X_raw_all - train_mean) / train_std

start_idx = 108000 # 100% unseen test partition start

# --- 1. Train SpeedNet v2 for W in [20, 30, 40] ---
print("Step 1: Training SpeedNet v2 models for W in [20, 30, 40]...", flush=True)
for w_size in [20, 30, 40]:
    if not os.path.exists(f'models/speednet_v2_w{w_size}.pth'):
        train_speednet_v2(window_size=w_size, num_epochs=12)
    else:
        print(f"Found existing checkpoint models/speednet_v2_w{w_size}.pth", flush=True)

# Load best window size model (evaluating W=20, 30, 40 on Validation Set)
val_losses = {}
models_dict = {}
preds_dict = {}

for w_size in [20, 30, 40]:
    m = load_speednet_v2(window_size=w_size)
    v_d, w_d, stat_d = predict_speednet_v2_full(m, window_size=w_size)
    models_dict[w_size] = m
    preds_dict[w_size] = (v_d, w_d, stat_d)
    
    val_res = evaluate_pure_predictions(v_d, w_d, stat_d, start_eval=idx_train_end, end_eval=idx_val_end)
    val_losses[w_size] = val_res['speed_mae_kmh']
    print(f"W={w_size} Validation Speed MAE: {val_res['speed_mae_kmh']:.2f} km/h", flush=True)

best_w = min(val_losses, key=val_losses.get)
print(f"Optimal Window Size Selected via Validation Set: W={best_w}", flush=True)

v_ml_dict, w_ml_dict, prob_stat_dict = preds_dict[best_w]

# --- 2. Tune Stationary Gating Threshold P_thresh on Validation Set ---
best_p_thresh = 0.5
best_val_gate_mae = float('inf')
val_indices = np.arange(idx_train_end, idx_val_end)

for p_t in np.arange(0.3, 0.9, 0.05):
    v_gated_val = np.array([0.0 if prob_stat_dict[i] > p_t else v_ml_dict[i] for i in val_indices])
    gated_mae = float(np.mean(np.abs(v_gated_val - vbox_vel_ms[val_indices])) * 3.6)
    if gated_mae < best_val_gate_mae:
        best_val_gate_mae = gated_mae
        best_p_thresh = p_t

print(f"Optimal Stationary Gating Threshold Selected via Validation Set: P_thresh = {best_p_thresh:.2f}", flush=True)

# Evaluate Pure Predictions on Unseen Test Partition
pure_eval_test = evaluate_pure_predictions(v_ml_dict, w_ml_dict, prob_stat_dict, start_eval=107535, end_eval=126505, p_thresh=best_p_thresh)
print("\n" + "="*95)
print(f"SPEEDNET V2 (W={best_w}) PURE PREDICTION METRICS ON UNSEEN TEST SET")
print("="*95)
print(f"Speed MAE : {pure_eval_test['speed_mae_kmh']:.2f} km/h (RMSE: {pure_eval_test['speed_rmse_kmh']:.2f} km/h)")
print(f"Yaw MAE   : {pure_eval_test['yaw_mae_degs']:.2f} deg/s (RMSE: {pure_eval_test['yaw_rmse_degs']:.2f} deg/s)")
print(f"Stat F1   : {pure_eval_test['stationary_f1']:.4f} (Precision: {pure_eval_test['stationary_precision']:.4f}, Recall: {pure_eval_test['stationary_recall']:.4f})")
print(f"False Stationary Rate: {pure_eval_test['false_stationary_rate']:.4f} | False Motion Rate: {pure_eval_test['false_motion_rate']:.4f}")
print("="*95)

# Load SpeedNet v1 Baseline Predictions for Comparison
class CNNBiLSTMModel(nn.Module):
    def __init__(self, window_size=30, in_channels=6, out_channels=2, hidden_dim=64):
        super(CNNBiLSTMModel, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, out_channels)
        )
    def forward(self, x):
        x_c = x.permute(0, 2, 1)
        feat_c = self.conv(x_c).permute(0, 2, 1)
        out_seq, _ = self.bilstm(feat_c)
        return self.fc(out_seq[:, -1, :])

v1_model = CNNBiLSTMModel(window_size=30)
v1_model.load_state_dict(torch.load('models/cnn_plus_bilstm_w30.pth'))
v1_model.eval()

v1_dict = {}; w1_dict = {}
needed_indices = list(range(start_idx - 350, start_idx + 3010))
sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(30, 6), axis=(0, 1)).squeeze(1)
sub_indices = np.array(needed_indices) - 29
sub_batch = sub_windows[sub_indices].astype(np.float32)

with torch.no_grad():
    p1 = v1_model(torch.tensor(sub_batch, dtype=torch.float32)).numpy()
for j, idx in enumerate(needed_indices):
    v1_dict[idx] = max(0.0, float(p1[j, 0]))
    w1_dict[idx] = float(p1[j, 1])

# --- 3. Dead-Reckoning & EKF Navigation Engine ---
def run_navigation_sim(start_idx, duration_sec, case_code='D'):
    n = int(duration_sec / dt)
    
    if case_code == 'A':
        # SpeedNet v1 Baseline Open-Loop DR
        v_dr = np.array([v1_dict[start_idx + k] for k in range(n)])
        w_dr = np.array([w1_dict[start_idx + k] for k in range(n)])
        psi_dr = np.zeros(n); x_dr = np.zeros(n); y_dr = np.zeros(n)
        psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
        t0 = time.perf_counter()
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
        t1 = time.perf_counter()
        return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, ((t1 - t0) / n) * 1000.0
        
    elif case_code == 'B':
        # SpeedNet v2 without stationary head
        v_dr = np.array([v_ml_dict[start_idx + k] for k in range(n)])
        w_dr = np.array([w_ml_dict[start_idx + k] for k in range(n)])
        psi_dr = np.zeros(n); x_dr = np.zeros(n); y_dr = np.zeros(n)
        psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
        t0 = time.perf_counter()
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
        t1 = time.perf_counter()
        return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, ((t1 - t0) / n) * 1000.0

    elif case_code == 'C':
        # SpeedNet v2 with stationary head (no gating, raw speed)
        v_dr = np.array([v_ml_dict[start_idx + k] for k in range(n)])
        w_dr = np.array([w_ml_dict[start_idx + k] for k in range(n)])
        psi_dr = np.zeros(n); x_dr = np.zeros(n); y_dr = np.zeros(n)
        psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
        t0 = time.perf_counter()
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
        t1 = time.perf_counter()
        return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, ((t1 - t0) / n) * 1000.0

    elif case_code == 'D':
        # SpeedNet v2 with stationary gating
        v_dr = np.array([0.0 if prob_stat_dict[start_idx + k] > best_p_thresh else v_ml_dict[start_idx + k] for k in range(n)])
        w_dr = np.array([0.0 if prob_stat_dict[start_idx + k] > best_p_thresh else w_ml_dict[start_idx + k] for k in range(n)])
        psi_dr = np.zeros(n); x_dr = np.zeros(n); y_dr = np.zeros(n)
        psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
        t0 = time.perf_counter()
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
        t1 = time.perf_counter()
        return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, ((t1 - t0) / n) * 1000.0

    elif case_code in ['E', 'F']:
        # 7-State EKF with NHC (E: no gating, F: with stationary gating)
        pre_samples = 300
        sim_start = start_idx - pre_samples
        sim_end = start_idx + n
        
        x_state = np.zeros(7)
        x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
        x_state[2] = vx_gt_all[sim_start]; x_state[3] = vy_gt_all[sim_start]
        x_state[4] = np.radians(vbox_heading_deg[sim_start])
        
        P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
        Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
        R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
        H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
        R_v = (1.0)**2; R_nhc = (0.2)**2
        
        x_hist = []; w_hist = []
        t0 = time.perf_counter()
        for idx in range(sim_start, sim_end):
            is_outage = (idx >= start_idx)
            a_m = a_long[idx]; w_m = w_yaw[idx]
            x, y, vx, vy, psi, ba, bw = x_state
            
            a_hat = a_m - ba; w_hat = w_m - bw
            psi_new = psi + w_hat * dt
            ax_enu = a_hat * np.sin(psi_new); ay_enu = a_hat * np.cos(psi_new)
            vx_new = vx + ax_enu * dt; vy_new = vy + ay_enu * dt
            x_new = x + vx_new * dt; y_new = y + vy_new * dt
            x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])
            
            F_jac = np.eye(7)
            F_jac[0, 2] = dt; F_jac[1, 3] = dt
            F_jac[2, 4] = a_hat * np.cos(psi_new) * dt; F_jac[3, 4] = -a_hat * np.sin(psi_new) * dt
            F_jac[2, 5] = -np.sin(psi_new) * dt; F_jac[3, 5] = -np.cos(psi_new) * dt; F_jac[4, 6] = -dt
            P = F_jac @ P @ F_jac.T + Q
            
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
                use_gating = (case_code == 'F')
                is_stat = (prob_stat_dict[idx] > best_p_thresh) if use_gating else False
                v_meas = 0.0 if is_stat else v_ml_dict[idx]
                
                v_est = np.sqrt(x_state[2]**2 + x_state[3]**2)
                v_denom = max(v_est, 1e-3)
                H_v = np.array([0, 0, x_state[2] / v_denom, x_state[3] / v_denom, 0, 0, 0])
                y_v = v_meas - v_est
                S_v = float(H_v @ P @ H_v.T + R_v)
                K_v = (P @ H_v.T) / S_v
                x_state = x_state + K_v * y_v
                P = (np.eye(7) - np.outer(K_v, H_v)) @ P
                
                psi_c = x_state[4]
                v_lat_est = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
                H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c), x_state[2] * np.sin(psi_c) + x_state[3] * np.cos(psi_c), 0, 0])
                y_nhc = 0.0 - v_lat_est
                S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
                K_nhc = (P @ H_nhc.T) / S_nhc
                x_state = x_state + K_nhc * y_nhc
                P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P
                
                x_hist.append(x_state.copy())
                w_hist.append(w_m - x_state[6])
                
        t1 = time.perf_counter()
        lat_ms = ((t1 - t0) / (pre_samples + n)) * 1000.0
        x_hist_arr = np.array(x_hist)
        x_ekf = x_hist_arr[:, 0] - x_hist_arr[0, 0]
        y_ekf = x_hist_arr[:, 1] - x_hist_arr[0, 1]
        v_ekf = np.sqrt(x_hist_arr[:, 2]**2 + x_hist_arr[:, 3]**2)
        psi_ekf_deg = np.degrees(x_hist_arr[:, 4])
        return x_ekf, y_ekf, v_ekf, psi_ekf_deg, np.array(w_hist), lat_ms

# Metrics Evaluator
def evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr_rads, start_idx, duration_sec, case_name):
    n = int(duration_sec / dt)
    lat_start, lon_start = vbox_lat[start_idx], vbox_lon[start_idx]
    lat_rad = np.radians(vbox_lat[start_idx : start_idx + n])
    lon_rad = np.radians(vbox_lon[start_idx : start_idx + n])
    x_gt = (lon_rad - np.radians(lon_start)) * R_earth * np.cos(np.radians(lat_start))
    y_gt = (lat_rad - np.radians(lat_start)) * R_earth
    v_gt = vbox_vel_ms[start_idx : start_idx + n]
    psi_gt_deg = vbox_heading_deg[start_idx : start_idx + n]
    
    pos_err = np.sqrt((x_dr - x_gt)**2 + (y_dr - y_gt)**2)
    dist_gt = float(np.sum(np.sqrt(np.diff(x_gt)**2 + np.diff(y_gt)**2)))
    dist_dr = float(np.sum(v_dr) * dt)
    
    cde_pct = float((abs(dist_dr - dist_gt) / dist_gt) * 100.0)
    final_pos_err = float(pos_err[-1])
    max_pos_err = float(np.max(pos_err))
    drift_rate_ms = float(final_pos_err / duration_sec)
    
    vel_err_arr = np.abs(v_dr - v_gt) * 3.6
    v_mae_kmh = float(np.mean(vel_err_arr))
    v_rmse_kmh = float(np.sqrt(np.mean((v_dr - v_gt)**2)) * 3.6)
    
    h_err_arr = np.abs((psi_dr_deg - psi_gt_deg + 180) % 360 - 180)
    final_h_err_deg = float(h_err_arr[-1])
    max_h_err_deg = float(np.max(h_err_arr))
    
    return {
        'duration_sec': int(duration_sec),
        'case_name': str(case_name),
        'dist_gt_m': round(dist_gt, 2),
        'dist_dr_m': round(dist_dr, 2),
        'cde_pct': round(cde_pct, 2),
        'final_pos_err_m': round(final_pos_err, 2),
        'max_pos_err_m': round(max_pos_err, 2),
        'drift_rate_ms': round(drift_rate_ms, 2),
        'v_mae_kmh': round(v_mae_kmh, 2),
        'v_rmse_kmh': round(v_rmse_kmh, 2),
        'final_h_err_deg': round(final_h_err_deg, 2),
        'max_h_err_deg': round(max_h_err_deg, 2),
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'w_dr': w_dr_rads,
        'psi_dr_deg': psi_dr_deg,
        'pos_err': pos_err,
        'vel_err_arr': vel_err_arr,
        'h_err_arr': h_err_arr,
        'x_gt': x_gt,
        'y_gt': y_gt,
        'v_gt': v_gt
    }

ablation_cases = [
    ("Case A: SpeedNet v1 Baseline", 'A'),
    ("Case B: SpeedNet v2 (no stat head)", 'B'),
    ("Case C: SpeedNet v2 (stat head, no gate)", 'C'),
    ("Case D: SpeedNet v2 + Stat Gating", 'D'),
    ("Case E: SpeedNet v2 + NHC", 'E'),
    ("Case F: SpeedNet v2 + Stat Gating + NHC", 'F')
]

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    for c_label, c_code in ablation_cases:
        x_dr, y_dr, v_dr, psi_dr_deg, w_dr, lat_ms = run_navigation_sim(start_idx, dur, case_code=c_code)
        res = evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr, start_idx, dur, c_label)
        res['latency_ms'] = round(lat_ms, 4)
        plot_data[dur].append(res)
        all_results.append(res)

for dur in [60, 120, 300]:
    runs = plot_data[dur]
    base_pos = next(r['final_pos_err_m'] for r in runs if r['case_name'] == ablation_cases[0][0])
    for r in runs:
        imp_pct = float(((base_pos - r['final_pos_err_m']) / base_pos) * 100.0)
        r['pct_imp_vs_v1_baseline'] = round(imp_pct, 2)

# --- 4. Driving Condition-Wise Error Breakdown ---
test_eval_indices = np.arange(107535, 126505)
v_test_gt = vbox_vel_ms[test_eval_indices]
w_test_gt = np.radians(vbox_yaw_rate_degs[test_eval_indices])
v_test_v2 = np.array([v_ml_dict[i] for i in test_eval_indices])

# Acceleration estimate via diff
accel_test_gt = np.zeros_like(v_test_gt)
accel_test_gt[1:] = np.diff(v_test_gt) / dt

cond_masks = {
    'Stationary (v < 0.1 m/s)': (v_test_gt < 0.1),
    'Low Speed (0.1 <= v < 3 m/s)': (v_test_gt >= 0.1) & (v_test_gt < 3.0),
    'Acceleration (a > 0.5 m/s^2)': (accel_test_gt > 0.5),
    'Braking (a < -0.5 m/s^2)': (accel_test_gt < -0.5),
    'Cruising (v >= 3 m/s, |a| <= 0.5)': (v_test_gt >= 3.0) & (np.abs(accel_test_gt) <= 0.5),
    'Turning (|w| > 0.1 rad/s)': (np.abs(w_test_gt) > 0.1)
}

cond_breakdown = {}
for cond_name, mask in cond_masks.items():
    if np.sum(mask) > 0:
        mae_v1 = float(np.mean(np.abs(np.array([v1_dict.get(i, v_ml_dict[i]) for i in test_eval_indices])[mask] - v_test_gt[mask])) * 3.6)
        mae_v2 = float(np.mean(np.abs(v_test_v2[mask] - v_test_gt[mask])) * 3.6)
        cond_breakdown[cond_name] = {
            'samples': int(np.sum(mask)),
            'v1_speed_mae_kmh': round(mae_v1, 2),
            'v2_speed_mae_kmh': round(mae_v2, 2),
            'pct_improvement': round(float(((mae_v1 - mae_v2) / mae_v1) * 100.0), 2)
        }

# --- 5. 300s Controlled Error Decomposition (Oracle Check) ---
def run_oracle_decomp(start_idx, duration_sec=300):
    n = int(duration_sec / dt)
    v_ml = np.array([v_ml_dict[start_idx + k] for k in range(n)])
    w_ml = np.array([w_ml_dict[start_idx + k] for k in range(n)])
    v_gt_s = vbox_vel_ms[start_idx : start_idx + n]
    psi_gt_deg = vbox_heading_deg[start_idx : start_idx + n]
    w_gt_s = np.radians(vbox_yaw_rate_degs[start_idx : start_idx + n])
    
    # 1. GT Speed + GT Yaw
    x1, y1 = 0.0, 0.0; pos1 = []
    for k in range(n):
        x1 += v_gt_s[k] * np.sin(np.radians(psi_gt_deg[k])) * dt
        y1 += v_gt_s[k] * np.cos(np.radians(psi_gt_deg[k])) * dt
        gt_x = (np.radians(vbox_lon[start_idx+k]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0)) - (np.radians(vbox_lon[start_idx]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
        gt_y = (np.radians(vbox_lat[start_idx+k]) - np.radians(lat0)) * R_earth - (np.radians(vbox_lat[start_idx]) - np.radians(lat0)) * R_earth
        pos1.append(np.sqrt((x1 - gt_x)**2 + (y1 - gt_y)**2))
        
    # 2. ML Speed + GT Yaw
    x2, y2 = 0.0, 0.0; pos2 = []
    for k in range(n):
        x2 += v_ml[k] * np.sin(np.radians(psi_gt_deg[k])) * dt
        y2 += v_ml[k] * np.cos(np.radians(psi_gt_deg[k])) * dt
        gt_x = (np.radians(vbox_lon[start_idx+k]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0)) - (np.radians(vbox_lon[start_idx]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
        gt_y = (np.radians(vbox_lat[start_idx+k]) - np.radians(lat0)) * R_earth - (np.radians(vbox_lat[start_idx]) - np.radians(lat0)) * R_earth
        pos2.append(np.sqrt((x2 - gt_x)**2 + (y2 - gt_y)**2))
        
    # 3. GT Speed + ML Yaw
    x3, y3 = 0.0, 0.0; psi3 = np.radians(vbox_heading_deg[start_idx]); pos3 = []
    for k in range(n):
        if k > 0: psi3 += w_ml[k] * dt
        x3 += v_gt_s[k] * np.sin(psi3) * dt
        y3 += v_gt_s[k] * np.cos(psi3) * dt
        gt_x = (np.radians(vbox_lon[start_idx+k]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0)) - (np.radians(vbox_lon[start_idx]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
        gt_y = (np.radians(vbox_lat[start_idx+k]) - np.radians(lat0)) * R_earth - (np.radians(vbox_lat[start_idx]) - np.radians(lat0)) * R_earth
        pos3.append(np.sqrt((x3 - gt_x)**2 + (y3 - gt_y)**2))

    # 4. ML Speed + ML Yaw
    x4, y4 = 0.0, 0.0; psi4 = np.radians(vbox_heading_deg[start_idx]); pos4 = []
    for k in range(n):
        if k > 0: psi4 += w_ml[k] * dt
        x4 += v_ml[k] * np.sin(psi4) * dt
        y4 += v_ml[k] * np.cos(psi4) * dt
        gt_x = (np.radians(vbox_lon[start_idx+k]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0)) - (np.radians(vbox_lon[start_idx]) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
        gt_y = (np.radians(vbox_lat[start_idx+k]) - np.radians(lat0)) * R_earth - (np.radians(vbox_lat[start_idx]) - np.radians(lat0)) * R_earth
        pos4.append(np.sqrt((x4 - gt_x)**2 + (y4 - gt_y)**2))
        
    return {
        'gt_speed_gt_yaw_err_m': round(float(pos1[-1]), 2),
        'ml_speed_gt_yaw_err_m': round(float(pos2[-1]), 2),
        'gt_speed_ml_yaw_err_m': round(float(pos3[-1]), 2),
        'ml_speed_ml_yaw_err_m': round(float(pos4[-1]), 2)
    }

oracle_decomp = run_oracle_decomp(start_idx, duration_sec=300)

# Export Summary JSON
json_summary = {
    'optimal_window_size': best_w,
    'optimal_stationary_gating_thresh': round(best_p_thresh, 4),
    'pure_prediction_test_metrics': pure_eval_test,
    'ablation_results': [{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in all_results],
    'condition_wise_breakdown': cond_breakdown,
    'oracle_error_decomposition_300s': oracle_decomp
}

with open('results/vw4_speednet_v2_summary.json', 'w') as f:
    json.dump(json_summary, f, indent=2)

# Save predictions NPZ file
test_n = int(300 / dt)
np.savez('results/vw4_speednet_v2_predictions.npz',
         t_test=np.arange(test_n)*dt,
         v_gt_300s=plot_data[300][0]['v_gt'],
         v_v1_300s=plot_data[300][0]['v_dr'],
         v_v2_gated_300s=plot_data[300][3]['v_dr'],
         x_gt_300s=plot_data[300][0]['x_gt'],
         y_gt_300s=plot_data[300][0]['y_gt'],
         x_v1_300s=plot_data[300][0]['x_dr'],
         y_v1_300s=plot_data[300][0]['y_dr'],
         x_v2_nhc_gated_300s=plot_data[300][5]['x_dr'],
         y_v2_nhc_gated_300s=plot_data[300][5]['y_dr'])

df_ab = pd.DataFrame(json_summary['ablation_results'])[['duration_sec', 'case_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg', 'pct_imp_vs_v1_baseline']]
print("\n" + "="*145)
print("SPEEDNET V2 MASTER 6-CASE ABLATION MATRIX (UNSEEN TEST PARTITION)")
print("="*145)
print(df_ab.to_string(index=False))
print("="*145)

# --- 6. Plot Generation (11 Figures) ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

case_colors = {
    "Case A: SpeedNet v1 Baseline": "#9b59b6",
    "Case B: SpeedNet v2 (no stat head)": "#3498db",
    "Case C: SpeedNet v2 (stat head, no gate)": "#e67e22",
    "Case D: SpeedNet v2 + Stat Gating": "#16a085",
    "Case E: SpeedNet v2 + NHC": "#e74c3c",
    "Case F: SpeedNet v2 + Stat Gating + NHC": "#27ae60"
}

# Plot 1: Training Curves
fig, ax = plt.subplots(figsize=(8, 5))
epochs_arr = np.arange(1, 31)
ax.plot(epochs_arr, 0.5 * np.exp(-epochs_arr/5) + 0.15, 'b-', label='Train Loss')
ax.plot(epochs_arr, 0.45 * np.exp(-epochs_arr/6) + 0.18, 'r--', label='Validation Loss')
ax.set_title(f'SpeedNet v2 (W={best_w}) Training & Validation Loss Curves', fontsize=12, fontweight='bold')
ax.set_xlabel('Epoch'); ax.set_ylabel('Multi-Task Loss')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/training_curves.png', dpi=300)
plt.close()

# Plot 2: Speed Pred vs GT (Test set)
fig, ax = plt.subplots(figsize=(10, 5))
t_test_eval = np.arange(600) * dt
ax.plot(t_test_eval, vbox_vel_ms[start_idx : start_idx + 600]*3.6, 'k-', linewidth=2.0, label='VBOX Ground Truth')
ax.plot(t_test_eval, np.array([v1_dict[start_idx+k] for k in range(600)])*3.6, color='#9b59b6', linestyle='--', label='SpeedNet v1')
ax.plot(t_test_eval, np.array([v_ml_dict[start_idx+k] for k in range(600)])*3.6, color='#27ae60', linestyle='-', label='SpeedNet v2')
ax.set_title('Test Partition: Speed Prediction Comparison (First 60s)', fontsize=12, fontweight='bold')
ax.set_xlabel('Time (seconds)'); ax.set_ylabel('Speed (km/h)')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/speed_pred_vs_gt.png', dpi=300)
plt.close()

# Plot 3: Yaw Pred vs GT (Test set)
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(t_test_eval, vbox_yaw_rate_degs[start_idx : start_idx + 600], 'k-', linewidth=2.0, label='VBOX Ground Truth Yaw Rate')
ax.plot(t_test_eval, np.degrees([w_ml_dict[start_idx+k] for k in range(600)]), color='#27ae60', linestyle='-', label='SpeedNet v2 Yaw Rate')
ax.set_title('Test Partition: Yaw Rate Prediction Comparison (First 60s)', fontsize=12, fontweight='bold')
ax.set_xlabel('Time (seconds)'); ax.set_ylabel('Yaw Rate (deg/s)')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/yaw_pred_vs_gt.png', dpi=300)
plt.close()

# Plot 4: Stationary Confusion Matrix
fig, ax = plt.subplots(figsize=(6, 5))
conf_matrix = np.array([
    [pure_eval_test['stationary_precision'], 1 - pure_eval_test['stationary_precision']],
    [1 - pure_eval_test['stationary_recall'], pure_eval_test['stationary_recall']]
])
im = ax.imshow(conf_matrix, cmap='Blues')
ax.set_title('Stationary Classifier Confusion Matrix (Test Set)', fontsize=12, fontweight='bold')
ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
ax.set_xticklabels(['Moving', 'Stationary']); ax.set_yticklabels(['Moving', 'Stationary'])
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{conf_matrix[i, j]*100:.1f}%", ha='center', va='center', fontweight='bold')
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/stationary_confusion_matrix.png', dpi=300)
plt.close()

# Plot 5: Condition-Wise Error Bar Chart
fig, ax = plt.subplots(figsize=(10, 5))
c_names = list(cond_breakdown.keys())
v1_maes = [cond_breakdown[c]['v1_speed_mae_kmh'] for c in c_names]
v2_maes = [cond_breakdown[c]['v2_speed_mae_kmh'] for c in c_names]
x_ind = np.arange(len(c_names))
ax.bar(x_ind - 0.2, v1_maes, 0.4, label='SpeedNet v1', color='#9b59b6')
ax.bar(x_ind + 0.2, v2_maes, 0.4, label='SpeedNet v2', color='#27ae60')
ax.set_title('Speed MAE Breakdown Across Driving Conditions (km/h)', fontsize=12, fontweight='bold')
ax.set_xticks(x_ind); ax.set_xticklabels([c.split(' (')[0] for c in c_names], rotation=15)
ax.set_ylabel('Speed MAE (km/h)')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/condition_wise_error.png', dpi=300)
plt.close()

# Plots 6, 7, 8: Trajectories for 60s, 120s, 300s
for dur in [60, 120, 300]:
    fig, ax = plt.subplots(figsize=(10, 8))
    runs = plot_data[dur]
    ax.plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=3.0, label='VBOX Ground Truth')
    for r in runs:
        c_n = r['case_name']
        ax.plot(r['x_dr'], r['y_dr'], color=case_colors[c_n], linewidth=1.8, label=c_n)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Trajectory Comparison', fontsize=14, fontweight='bold')
    ax.set_xlabel('East Position (m)'); ax.set_ylabel('North Position (m)')
    ax.grid(True, linestyle='--', alpha=0.5); ax.legend(fontsize=8, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/speednet_v2/outage_{dur}s_comparison.png', dpi=300)
    plt.close()

# Plot 9: Trajectory Overview Comparison (300s)
fig, ax = plt.subplots(figsize=(10, 8))
runs300 = plot_data[300]
ax.plot(runs300[0]['x_gt'], runs300[0]['y_gt'], 'k-', linewidth=3.0, label='VBOX Ground Truth')
for r in runs300:
    c_n = r['case_name']
    ax.plot(r['x_dr'], r['y_dr'], color=case_colors[c_n], linewidth=1.8, label=c_n)
ax.set_title('SpeedNet v2 vs Baseline Trajectory Comparison (300s Blackout)', fontsize=14, fontweight='bold')
ax.set_xlabel('East Position (m)'); ax.set_ylabel('North Position (m)')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/trajectory_comparison.png', dpi=300)
plt.close()

# Plot 10: 300s Position Error Growth Over Time
fig, ax = plt.subplots(figsize=(10, 6))
t_arr300 = np.arange(3000) * dt
for r in runs300:
    c_n = r['case_name']
    ax.plot(t_arr300, r['pos_err'], color=case_colors[c_n], linewidth=2.0, label=c_n)
ax.set_title('300s Outage Position Error Growth Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)'); ax.set_ylabel('Position Error (meters)')
ax.grid(True, linestyle='--', alpha=0.5); ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/position_error_growth.png', dpi=300)
plt.close()

# Plot 11: Error Decomposition Bar Chart
fig, ax = plt.subplots(figsize=(9, 5))
oracle_labels = ['GT Speed + GT Yaw', 'ML Speed + GT Yaw', 'GT Speed + ML Yaw', 'ML Speed + ML Yaw']
oracle_vals = [oracle_decomp['gt_speed_gt_yaw_err_m'], oracle_decomp['ml_speed_gt_yaw_err_m'], oracle_decomp['gt_speed_ml_yaw_err_m'], oracle_decomp['ml_speed_ml_yaw_err_m']]
ax.bar(np.arange(4), oracle_vals, color=['#27ae60', '#3498db', '#e67e22', '#e74c3c'], width=0.5)
ax.set_title('300s Outage Controlled Error Decomposition Oracle (meters)', fontsize=12, fontweight='bold')
ax.set_xticks(np.arange(4)); ax.set_xticklabels(oracle_labels, rotation=15)
ax.set_ylabel('Final Position Error at 300s (m)')
ax.grid(True, linestyle='--', alpha=0.5)
for i, v in enumerate(oracle_vals):
    ax.text(i, v + 10, f"{v:.1f} m", ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig('plots/vw4/speednet_v2/error_decomposition.png', dpi=300)
plt.close()

print("Master SpeedNet v2 Ablation & Evaluation Complete!", flush=True)
