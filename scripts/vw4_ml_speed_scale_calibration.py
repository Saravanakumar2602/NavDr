import os
import sys
import json
import time
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())

# Ensure output directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('plots/vw4/ml_speed_calibration', exist_ok=True)
os.makedirs('results', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading Vw4 dataset files...", flush=True)
df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# --- 1. Timestamp Synchronization ---
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1 # 10 Hz
t_sync = np.arange(t_start, t_end, dt)

# Extract 6-Channel IMU Inputs
ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

X_raw_all = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

# Sensor Processing Signals
raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y)         # m/s^2
a_lat_tilt_comp = raw_ax - grav_x    # m/s^2
w_yaw = -gyro_pitch                  # rad/s (smartphone gyro yaw signal)

# VBOX Ground Truth
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

# --- Data Partitioning & Normalization ---
n_total = len(t_sync)
idx_train_end = int(n_total * 0.70)  # 88566
idx_val_end   = int(n_total * 0.85)  # 107535

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

X_norm_all = (X_raw_all - train_mean) / train_std

# --- Load Trained PyTorch Model (CNN + BiLSTM W=30) ---
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

device = torch.device('cpu')
model_w30 = CNNBiLSTMModel(window_size=30).to(device)
model_w30.load_state_dict(torch.load('models/cnn_plus_bilstm_w30.pth'))
model_w30.eval()

print("Precomputing ML predictions...", flush=True)
v_ml_dict = {}
w_ml_dict = {}

start_idx = 108000
needed_indices = np.concatenate([np.arange(idx_train_end, idx_val_end), np.arange(start_idx - 350, start_idx + 3010)])

# Fast numpy sliding window view extraction
sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(30, 6), axis=(0, 1)).squeeze(1)
# sub_windows[k] is window ending at index k+29 (i.e. idx = k+29)
# To get window for index `idx`, index into sub_windows is `idx - 29`

sub_indices = needed_indices - 29
sub_batch = sub_windows[sub_indices].astype(np.float32)

with torch.no_grad():
    preds_all = model_w30(torch.tensor(sub_batch, dtype=torch.float32).to(device)).cpu().numpy()

for j, idx in enumerate(needed_indices):
    v_ml_dict[idx] = max(0.0, float(preds_all[j, 0]))
    w_ml_dict[idx] = float(preds_all[j, 1])

# --- 2. Parameter Calibration ESTIMATED STRICTLY ON VALIDATION SET [88566:107535] ---
val_indices = np.arange(idx_train_end, idx_val_end)
v_val_ml = np.array([v_ml_dict[i] for i in val_indices])
v_val_gt = vbox_vel_ms[val_indices]

# Validation Error Before Calibration
val_mae_before = float(np.mean(np.abs(v_val_ml - v_val_gt)) * 3.6)
val_rmse_before = float(np.sqrt(np.mean((v_val_ml - v_val_gt)**2)) * 3.6)

# Exp 2: Global Scale alpha (v_corr = alpha * v_ml)
alpha_scale = float(np.sum(v_val_ml * v_val_gt) / max(1e-6, np.sum(v_val_ml**2)))

# Exp 3: Speed Offset beta (v_corr = v_ml + beta)
beta_offset = float(np.mean(v_val_gt - v_val_ml))

# Exp 4: Scale + Offset OLS (v_corr = alpha * v_ml + beta)
A_mat = np.column_stack([v_val_ml, np.ones_like(v_val_ml)])
alpha_ols, beta_ols = np.linalg.lstsq(A_mat, v_val_gt, rcond=None)[0]
alpha_ols = float(alpha_ols)
beta_ols = float(beta_ols)

# Exp 5: Low-Order Residual Model (v_corr = a2 * v_ml^2 + a1 * v_ml + a0)
poly_coeffs = np.polyfit(v_val_ml, v_val_gt, 2)
a2_poly, a1_poly, a0_poly = float(poly_coeffs[0]), float(poly_coeffs[1]), float(poly_coeffs[2])

# Validation Performance After Calibration
val_mae_scale = float(np.mean(np.abs(alpha_scale * v_val_ml - v_val_gt)) * 3.6)
val_rmse_scale = float(np.sqrt(np.mean((alpha_scale * v_val_ml - v_val_gt)**2)) * 3.6)

val_mae_ols = float(np.mean(np.abs(alpha_ols * v_val_ml + beta_ols - v_val_gt)) * 3.6)
val_rmse_ols = float(np.sqrt(np.mean((alpha_ols * v_val_ml + beta_ols - v_val_gt)**2)) * 3.6)

val_mae_poly = float(np.mean(np.abs(np.polyval(poly_coeffs, v_val_ml) - v_val_gt)) * 3.6)
val_rmse_poly = float(np.sqrt(np.mean((np.polyval(poly_coeffs, v_val_ml) - v_val_gt)**2)) * 3.6)

print("\n" + "="*95, flush=True)
print("VALIDATION SET PARAMETER CALIBRATION (STRICTLY ON PARTITION [88566:107535])", flush=True)
print("="*95, flush=True)
print(f"Validation MAE Before Calibration  : {val_mae_before:.2f} km/h (RMSE: {val_rmse_before:.2f} km/h)", flush=True)
print(f"Exp 2 Fitted Global Scale alpha    : {alpha_scale:.4f} -> Val MAE: {val_mae_scale:.2f} km/h", flush=True)
print(f"Exp 3 Fitted Speed Offset beta     : {beta_offset*3.6:.2f} km/h", flush=True)
print(f"Exp 4 Fitted Scale + Offset (OLS)  : alpha = {alpha_ols:.4f}, beta = {beta_ols*3.6:.2f} km/h -> Val MAE: {val_mae_ols:.2f} km/h", flush=True)
print(f"Exp 5 Fitted Poly Residual Model   : {a2_poly:.4f}*v^2 + {a1_poly:.4f}*v + {a0_poly*3.6:.2f} -> Val MAE: {val_mae_poly:.2f} km/h", flush=True)
print("="*95, flush=True)

# --- 3. EKF Navigation Engine with Speed Calibration ---
def run_calibrated_ekf(start_idx, duration_sec, calib_mode='baseline'):
    n = int(duration_sec / dt)
    pre_samples = 300
    sim_start = start_idx - pre_samples
    sim_end = start_idx + n
    
    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]
    x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]
    x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])
    
    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7))
    for k_idx in range(5): H_gnss[k_idx, k_idx] = 1.0
    
    R_v = (1.0)**2
    R_nhc = (0.2)**2
    
    x_hist = []
    w_hist = []
    
    t0 = time.perf_counter()
    for idx in range(sim_start, sim_end):
        is_outage = (idx >= start_idx)
        a_m = a_long[idx]
        w_m = w_yaw[idx]
        x, y, vx, vy, psi, ba, bw = x_state
        
        a_hat = a_m - ba
        w_hat = w_m - bw
        psi_new = psi + w_hat * dt
        ax_enu = a_hat * np.sin(psi_new)
        ay_enu = a_hat * np.cos(psi_new)
        
        vx_new = vx + ax_enu * dt
        vy_new = vy + ay_enu * dt
        x_new = x + vx_new * dt
        y_new = y + vy_new * dt
        x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])
        
        F = np.eye(7)
        F[0, 2] = dt; F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt; F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt; F[3, 5] = -np.cos(psi_new) * dt; F[4, 6] = -dt
        P = F @ P @ F.T + Q
        
        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            psi_meas_unwrapped = x_state[4] + psi_diff
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], psi_meas_unwrapped])
            y_meas = z_gnss - H_gnss @ x_state
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H_gnss) @ P
        else:
            # --- GNSS Outage Period: Apply Speed Calibration ---
            v_raw_ml = v_ml_dict[idx]
            
            if calib_mode == 'baseline':
                v_meas = v_raw_ml
            elif calib_mode == 'global_scale':
                v_meas = max(0.0, alpha_scale * v_raw_ml)
            elif calib_mode == 'speed_offset':
                v_meas = max(0.0, v_raw_ml + beta_offset)
            elif calib_mode == 'scale_offset':
                v_meas = max(0.0, alpha_ols * v_raw_ml + beta_ols)
            elif calib_mode == 'poly_residual':
                v_meas = max(0.0, float(np.polyval(poly_coeffs, v_raw_ml)))
            elif calib_mode == 'gt_oracle':
                v_meas = vbox_vel_ms[idx]
                
            # Update 1: Speed Measurement Update
            v_est = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2] / v_denom, x_state[3] / v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P
            
            # Update 2: Kinematic NHC Constraint (Always active)
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

# --- Metrics Evaluator ---
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
    h_rmse_deg = float(np.sqrt(np.mean(h_err_arr**2)))
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
        'h_rmse_deg': round(h_rmse_deg, 2),
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
        'v_gt': v_gt,
        'psi_gt_deg': psi_gt_deg
    }

exp_configs = [
    ("Exp 1: Baseline ML + NHC", 'baseline'),
    ("Exp 2: Global Speed Scale (alpha)", 'global_scale'),
    ("Exp 3: Speed Bias Offset (beta)", 'speed_offset'),
    ("Exp 4: Scale + Offset Calibration", 'scale_offset'),
    ("Exp 5: Poly Speed Residual", 'poly_residual'),
    ("Exp 6: GT Speed Diagnostic (Oracle)", 'gt_oracle')
]

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    for c_label, c_mode in exp_configs:
        x_dr, y_dr, v_dr, psi_dr_deg, w_dr, lat_ms = run_calibrated_ekf(start_idx, dur, calib_mode=c_mode)
        res = evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr, start_idx, dur, c_label)
        res['latency_ms'] = round(lat_ms, 4)
        plot_data[dur].append(res)
        all_results.append(res)

# Compute Improvements relative to Exp 1 Baseline and Exp 6 GT Speed Oracle
for dur in [60, 120, 300]:
    runs = plot_data[dur]
    base_pos = next(r['final_pos_err_m'] for r in runs if r['case_name'] == exp_configs[0][0])
    oracle_pos = next(r['final_pos_err_m'] for r in runs if r['case_name'] == exp_configs[5][0])
    max_removable_err = max(1e-3, base_pos - oracle_pos)
    
    for r in runs:
        imp_pct = float(((base_pos - r['final_pos_err_m']) / base_pos) * 100.0)
        pct_oracle_removed = float(((base_pos - r['final_pos_err_m']) / max_removable_err) * 100.0)
        r['pct_imp_vs_baseline'] = round(imp_pct, 2)
        r['pct_oracle_err_removed'] = round(max(0.0, min(100.0, pct_oracle_removed)), 2)

# Save JSON results without numpy arrays
json_results = {
    'val_calibration_params': {
        'val_mae_before_kmh': round(val_mae_before, 2),
        'val_rmse_before_kmh': round(val_rmse_before, 2),
        'alpha_scale': round(alpha_scale, 4),
        'val_mae_scale_kmh': round(val_mae_scale, 2),
        'beta_offset_kmh': round(beta_offset * 3.6, 2),
        'alpha_ols': round(alpha_ols, 4),
        'beta_ols_kmh': round(beta_ols * 3.6, 2),
        'val_mae_ols_kmh': round(val_mae_ols, 2),
        'poly_coeffs': [round(float(c), 6) for c in poly_coeffs],
        'val_mae_poly_kmh': round(val_mae_poly, 2)
    },
    'test_evaluation_results': [{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in all_results]
}

with open('results/vw4_ml_speed_calibration_results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

# Save test predictions NPZ file
test_n = int(300 / dt)
np.savez('results/vw4_ml_speed_calibration_predictions.npz',
         t_test=np.arange(test_n)*dt,
         v_gt_300s=plot_data[300][0]['v_gt'],
         v_raw_ml_300s=plot_data[300][0]['v_dr'],
         v_calib_ols_300s=plot_data[300][3]['v_dr'],
         x_gt_300s=plot_data[300][0]['x_gt'],
         y_gt_300s=plot_data[300][0]['y_gt'],
         x_baseline_300s=plot_data[300][0]['x_dr'],
         y_baseline_300s=plot_data[300][0]['y_dr'],
         x_ols_300s=plot_data[300][3]['x_dr'],
         y_ols_300s=plot_data[300][3]['y_dr'])

df_res = pd.DataFrame(json_results['test_evaluation_results'])[['duration_sec', 'case_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg', 'pct_imp_vs_baseline', 'pct_oracle_err_removed']]
print("\n" + "="*145, flush=True)
print("VW4 UNSEEN TEST SET: ML SPEED SCALE CALIBRATION ABLATION MATRIX", flush=True)
print("="*145, flush=True)
print(df_res.to_string(index=False), flush=True)
print("="*145, flush=True)

# --- 4. High-Resolution Visualizations (12 Plots) ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

case_colors = {
    "Exp 1: Baseline ML + NHC": "#9b59b6",
    "Exp 2: Global Speed Scale (alpha)": "#3498db",
    "Exp 3: Speed Bias Offset (beta)": "#e67e22",
    "Exp 4: Scale + Offset Calibration": "#27ae60",
    "Exp 5: Poly Speed Residual": "#16a085",
    "Exp 6: GT Speed Diagnostic (Oracle)": "#e74c3c"
}

case_styles = {
    "Exp 1: Baseline ML + NHC": ":",
    "Exp 2: Global Speed Scale (alpha)": "-.",
    "Exp 3: Speed Bias Offset (beta)": "--",
    "Exp 4: Scale + Offset Calibration": "-",
    "Exp 5: Poly Speed Residual": "-",
    "Exp 6: GT Speed Diagnostic (Oracle)": "-"
}

# Plot 1: Validation predicted speed vs ground truth
fig, ax = plt.subplots(figsize=(10, 5))
t_val = np.arange(len(v_val_gt)) * dt
ax.plot(t_val[:600], v_val_gt[:600]*3.6, 'k-', linewidth=2.0, label='VBOX Ground Truth')
ax.plot(t_val[:600], v_val_ml[:600]*3.6, color='#9b59b6', linestyle='--', linewidth=1.5, label='Raw ML Speed')
ax.plot(t_val[:600], (alpha_ols * v_val_ml[:600] + beta_ols)*3.6, color='#27ae60', linestyle='-', linewidth=1.8, label='Calibrated ML Speed (Exp 4)')
ax.set_title('Validation Partition: Speed Prediction vs Ground Truth (First 60s)', fontsize=14, fontweight='bold')
ax.set_xlabel('Validation Time (seconds)')
ax.set_ylabel('Speed (km/h)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/val_speed_pred_vs_gt.png', dpi=300)
plt.close()

# Plot 2: Validation residual before calibration
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist((v_val_ml - v_val_gt)*3.6, bins=50, color='#9b59b6', alpha=0.7, edgecolor='black')
ax.set_title(f'Validation Speed Residual Before Calibration (MAE = {val_mae_before:.2f} km/h)', fontsize=14, fontweight='bold')
ax.set_xlabel('Speed Error (km/h)')
ax.set_ylabel('Sample Frequency')
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/val_speed_residual_before_calib.png', dpi=300)
plt.close()

# Plot 3: Validation residual after calibration
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(((alpha_ols * v_val_ml + beta_ols) - v_val_gt)*3.6, bins=50, color='#27ae60', alpha=0.7, edgecolor='black')
ax.set_title(f'Validation Speed Residual After OLS Calibration (MAE = {val_mae_ols:.2f} km/h)', fontsize=14, fontweight='bold')
ax.set_xlabel('Speed Error (km/h)')
ax.set_ylabel('Sample Frequency')
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/val_speed_residual_after_calib.png', dpi=300)
plt.close()

# Plot 4: Test predicted speed vs ground truth (300s outage)
fig, ax = plt.subplots(figsize=(10, 5))
t_test = np.arange(test_n) * dt
v_test_gt = plot_data[300][0]['v_gt'] * 3.6
v_test_raw = plot_data[300][0]['v_dr'] * 3.6
v_test_cal = plot_data[300][3]['v_dr'] * 3.6
ax.plot(t_test[:600], v_test_gt[:600], 'k-', linewidth=2.0, label='VBOX Ground Truth')
ax.plot(t_test[:600], v_test_raw[:600], color='#9b59b6', linestyle='--', linewidth=1.5, label='Raw ML Speed (Exp 1)')
ax.plot(t_test[:600], v_test_cal[:600], color='#27ae60', linestyle='-', linewidth=1.8, label='Calibrated ML Speed (Exp 4)')
ax.set_title('Unseen Test Partition: 300s Outage Speed Prediction Comparison', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Speed (km/h)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/test_speed_pred_vs_gt.png', dpi=300)
plt.close()

# Plot 5: Test residual before/after calibration
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(t_test, np.abs(v_test_raw - v_test_gt), color='#9b59b6', linestyle='--', linewidth=1.5, label='Raw ML Speed Error')
ax.plot(t_test, np.abs(v_test_cal - v_test_gt), color='#27ae60', linestyle='-', linewidth=1.8, label='Calibrated ML Speed Error (Exp 4)')
ax.set_title('Unseen Test Partition: Absolute Speed Error Over 300s Outage', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Speed Absolute Error (km/h)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/test_speed_residual_before_after.png', dpi=300)
plt.close()

# Plots 6, 7, 8: Trajectory Comparisons for 60s, 120s, 300s
for dur in [60, 120, 300]:
    runs = plot_data[dur]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=3.0, label='VBOX Ground Truth')
    for r in runs:
        c_name = r['case_name']
        ax.plot(r['x_dr'], r['y_dr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=1.8, label=c_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Trajectory Comparison', fontsize=14, fontweight='bold')
    ax.set_xlabel('East Position (m)')
    ax.set_ylabel('North Position (m)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ml_speed_calibration/outage_{dur}s_trajectory.png', dpi=300)
    plt.close()

# Plot 9: 300s Position Error Growth
fig, ax = plt.subplots(figsize=(10, 6))
runs300 = plot_data[300]
for r in runs300:
    c_name = r['case_name']
    ax.plot(t_test, r['pos_err'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
ax.set_title('Vw4 Unseen Test Set: 300s Outage Position Error Growth Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Position Error (meters)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/outage_300s_position_error.png', dpi=300)
plt.close()

# Plot 10: Final Position Error Comparison Bar Chart
fig, ax = plt.subplots(figsize=(10, 6))
durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.13
for idx, (c_name, _) in enumerate(exp_configs):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    ax.bar(x_indices + idx * width, pos_errs, width, label=c_name, color=case_colors[c_name])
ax.set_title('Final Position Error (meters) Across Outage Blackouts', fontsize=14, fontweight='bold')
ax.set_xticks(x_indices + width * 2.5)
ax.set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
ax.set_ylabel('Final Position Error (m)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/final_position_error_comparison.png', dpi=300)
plt.close()

# Plot 11: Speed MAE Comparison Bar Chart
fig, ax = plt.subplots(figsize=(10, 6))
for idx, (c_name, _) in enumerate(exp_configs):
    speed_maes = [next(r['v_mae_kmh'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    ax.bar(x_indices + idx * width, speed_maes, width, label=c_name, color=case_colors[c_name])
ax.set_title('Speed MAE (km/h) Across Outage Blackouts', fontsize=14, fontweight='bold')
ax.set_xticks(x_indices + width * 2.5)
ax.set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
ax.set_ylabel('Speed MAE (km/h)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_speed_calibration/speed_mae_comparison.png', dpi=300)
plt.close()

# Plot 12: Calibration Parameter Comparison Bar Chart
fig, ax = plt.subplots(figsize=(8, 5))
calib_labels = ['Val Uncalib', 'Global Scale alpha', 'Offset beta (km/h)', 'OLS alpha', 'OLS beta (km/h)']
calib_vals = [val_mae_before, alpha_scale, beta_offset*3.6, alpha_ols, beta_ols*3.6]
colors_p = ['#9b59b6', '#3498db', '#e67e22', '#27ae60', '#16a085']
ax.bar(np.arange(len(calib_labels)), calib_vals, color=colors_p, width=0.5)
ax.set_title('Fitted Calibration Parameters (Validation Partition)', fontsize=14, fontweight='bold')
ax.set_xticks(np.arange(len(calib_labels)))
ax.set_xticklabels(calib_labels, rotation=15, ha='right', fontsize=9)
ax.grid(True, linestyle='--', alpha=0.5)
for i, v in enumerate(calib_vals):
    ax.text(i, v + 0.05, f"{v:.2f}", ha='center', fontweight='bold', fontsize=9)
plt.tight_layout()
summary_plot_file = 'plots/vw4/ml_speed_calibration/calibration_parameter_comparison.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}", flush=True)
