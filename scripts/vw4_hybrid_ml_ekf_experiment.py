import os
import json
import time
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

# Ensure output directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('plots/vw4/hybrid_ml_ekf', exist_ok=True)
os.makedirs('results', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading Vw4 dataset files...")
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

# Sensor Processing Signals for Classical Baselines
raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y) # m/s^2
w_yaw = -gyro_pitch         # rad/s

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

# --- Normalization Parameters (Computed ONLY on Training Partition :88566) ---
n_total = len(t_sync)
idx_train_end = int(n_total * 0.70) # 88566

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

# Normalize full dataset for ML inference
X_norm_all = (X_raw_all - train_mean) / train_std

# --- Load Trained CNN + BiLSTM (W=30) PyTorch Model ---
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

# Unseen Test Partition Outage Start Index
start_idx = 108000 # 46.5s after test set start

# Fast sliding window batch inference for the outage simulation range (3300 samples)
sim_range_start = start_idx - 300
sim_range_end = start_idx + 3000 + 10

window_size = 30
batch_windows = []
for idx in range(sim_range_start, sim_range_end):
    win = X_norm_all[idx - window_size + 1 : idx + 1]
    batch_windows.append(win)

batch_windows = np.array(batch_windows, dtype=np.float32)
with torch.no_grad():
    x_tensor = torch.tensor(batch_windows, dtype=torch.float32).to(device)
    preds_range = model_w30(x_tensor).cpu().numpy()

# Map predictions back to global sample indices
v_ml_dict = {}
w_ml_dict = {}
for i, idx in enumerate(range(sim_range_start, sim_range_end)):
    v_ml_dict[idx] = max(0.0, float(preds_range[i, 0]))
    w_ml_dict[idx] = float(preds_range[i, 1])

# --- 1. Calibrated Open-Loop DR ---
def run_calib_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    b_accel_pre = np.mean(a_long[start_idx - 100 : start_idx])
    a_long_cal = a_long - b_accel_pre
    
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    v_dr[0] = vbox_vel_ms[start_idx]
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for i in range(1, n):
        psi_dr[i] = psi_dr[i-1] + w_yaw[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_long_cal[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        
        x_dr[i] = x_dr[i-1] + v_dr[i] * np.sin(psi_dr[i]) * dt
        y_dr[i] = y_dr[i-1] + v_dr[i] * np.cos(psi_dr[i]) * dt
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / n) * 1000.0
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw[start_idx : start_idx + n], lat_ms, None, None

# --- 2. ML-Only DR (CNN+BiLSTM W30) ---
def run_ml_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    v_dr = np.array([v_ml_dict[start_idx + k] for k in range(n)])
    w_yaw_pred = np.array([w_ml_dict[start_idx + k] for k in range(n)])
    
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for k in range(1, n):
        psi_dr[k] = psi_dr[k-1] + w_yaw_pred[k] * dt
        x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
        y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / n) * 1000.0
    
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw_pred, lat_ms, None, None

# --- 3. Unified EKF Engine supporting Classical, Config A, B, C, D ---
def run_ekf_engine(start_idx, duration_sec, config_type='classical'):
    n = int(duration_sec / dt)
    pre_samples = 300 # 30s pre-outage GNSS aiding
    sim_start = start_idx - pre_samples
    sim_end = start_idx + n
    
    # State x = [x, y, vx, vy, psi, ba, bw]^T
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
    
    # Base ML measurement covariances
    R_v_base = (1.0)**2           # (1.0 m/s)^2
    R_w_base = np.radians(1.0)**2 # (1.0 deg/s)^2
    
    x_hist = []
    p_trace_hist = []
    innovations = []
    
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
        F[0, 2] = dt
        F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt
        F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt
        F[3, 5] = -np.cos(psi_new) * dt
        F[4, 6] = -dt
        
        P = F @ P @ F.T + Q
        
        if not is_outage:
            # Normal GNSS measurement update
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
            # GNSS Outage Period -> Ingest ML Measurements depending on Config A, B, C, D
            v_ml = v_ml_dict[idx]
            w_ml = w_ml_dict[idx]
            
            if config_type in ['config_a', 'config_c', 'config_d']:
                # ML Speed Measurement Update
                v_est = np.sqrt(x_state[2]**2 + x_state[3]**2)
                v_denom = max(v_est, 1e-3)
                H_v = np.array([0, 0, x_state[2] / v_denom, x_state[3] / v_denom, 0, 0, 0])
                
                y_v = v_ml - v_est
                if is_outage: innovations.append(y_v)
                
                R_v = R_v_base
                if config_type == 'config_d':
                    S_v = float(H_v @ P @ H_v.T + R_v)
                    normalized_res = abs(y_v) / np.sqrt(S_v)
                    if normalized_res > 2.0:
                        R_v *= (1.0 + 4.0 * (normalized_res - 2.0))
                    vib = np.std(X_raw_all[max(0, idx-10):idx+1, 0:3])
                    if vib > 2.0:
                        R_v *= (1.0 + vib)
                        
                S_v = float(H_v @ P @ H_v.T + R_v)
                K_v = (P @ H_v.T) / S_v
                x_state = x_state + K_v * y_v
                P = (np.eye(7) - np.outer(K_v, H_v)) @ P
                
            if config_type in ['config_b', 'config_c', 'config_d']:
                # ML Yaw Rate Measurement Update
                b_w_meas = w_m - w_ml
                y_w = b_w_meas - x_state[6]
                H_w = np.array([0, 0, 0, 0, 0, 0, 1.0])
                
                R_w = R_w_base
                if config_type == 'config_d':
                    S_w = float(H_w @ P @ H_w.T + R_w)
                    norm_w = abs(y_w) / np.sqrt(S_w)
                    if norm_w > 2.0:
                        R_w *= (1.0 + 3.0 * (norm_w - 2.0))
                        
                S_w = float(H_w @ P @ H_w.T + R_w)
                K_w = (P @ H_w.T) / S_w
                x_state = x_state + K_w * y_w
                P = (np.eye(7) - np.outer(K_w, H_w)) @ P

        if is_outage:
            p_trace_hist.append(np.trace(P))
            x_hist.append(x_state.copy())
            
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / (pre_samples + n)) * 1000.0
        
    x_hist_arr = np.array(x_hist)
    x_ekf = x_hist_arr[:, 0] - x_hist_arr[0, 0]
    y_ekf = x_hist_arr[:, 1] - x_hist_arr[0, 1]
    v_ekf = np.sqrt(x_hist_arr[:, 2]**2 + x_hist_arr[:, 3]**2)
    psi_ekf_deg = np.degrees(x_hist_arr[:, 4])
    w_yaw_ekf = w_yaw[start_idx : start_idx + n] - x_hist_arr[:, 6]
    
    return x_ekf, y_ekf, v_ekf, psi_ekf_deg, w_yaw_ekf, lat_ms, innovations, p_trace_hist

# --- Metrics Evaluator ---
def evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr_rads, start_idx, duration_sec, model_name, innovations=None, p_trace=None):
    n = int(duration_sec / dt)
    lat_start, lon_start = vbox_lat[start_idx], vbox_lon[start_idx]
    lat_rad = np.radians(vbox_lat[start_idx : start_idx + n])
    lon_rad = np.radians(vbox_lon[start_idx : start_idx + n])
    x_gt = (lon_rad - np.radians(lon_start)) * R_earth * np.cos(np.radians(lat_start))
    y_gt = (lat_rad - np.radians(lat_start)) * R_earth
    v_gt = vbox_vel_ms[start_idx : start_idx + n]
    psi_gt_deg = vbox_heading_deg[start_idx : start_idx + n]
    w_gt_rads = np.radians(vbox_yaw_rate_degs[start_idx : start_idx + n])
    
    pos_err = np.sqrt((x_dr - x_gt)**2 + (y_dr - y_gt)**2)
    dist_gt = float(np.sum(np.sqrt(np.diff(x_gt)**2 + np.diff(y_gt)**2)))
    dist_dr = float(np.sum(v_dr) * dt)
    
    cde_pct = float((abs(dist_dr - dist_gt) / dist_gt) * 100.0)
    final_pos_err = float(pos_err[-1])
    max_pos_err = float(np.max(pos_err))
    drift_rate_ms = float(final_pos_err / duration_sec)
    
    v_mae_kmh = float(np.mean(np.abs(v_dr - v_gt)) * 3.6)
    v_rmse_kmh = float(np.sqrt(np.mean((v_dr - v_gt)**2)) * 3.6)
    final_v_err_kmh = float(abs(v_dr[-1] - v_gt[-1]) * 3.6)
    
    w_mae_degs = float(np.degrees(np.mean(np.abs(w_dr_rads - w_gt_rads))))
    w_rmse_degs = float(np.degrees(np.sqrt(np.mean((w_dr_rads - w_gt_rads)**2))))
    
    h_err_deg = float(abs((psi_dr_deg[-1] - psi_gt_deg[-1] + 180) % 360 - 180))
    
    innov_mean = float(np.mean(innovations)) if innovations and len(innovations) > 0 else 0.0
    innov_std = float(np.std(innovations)) if innovations and len(innovations) > 0 else 0.0
    final_p_trace = float(p_trace[-1]) if p_trace and len(p_trace) > 0 else 0.0
    
    return {
        'duration_sec': int(duration_sec),
        'model_name': str(model_name),
        'dist_gt_m': round(dist_gt, 2),
        'cde_pct': round(cde_pct, 2),
        'final_pos_err_m': round(final_pos_err, 2),
        'max_pos_err_m': round(max_pos_err, 2),
        'drift_rate_ms': round(drift_rate_ms, 2),
        'v_mae_kmh': round(v_mae_kmh, 2),
        'v_rmse_kmh': round(v_rmse_kmh, 2),
        'final_v_err_kmh': round(final_v_err_kmh, 2),
        'w_mae_degs': round(w_mae_degs, 2),
        'w_rmse_degs': round(w_rmse_degs, 2),
        'h_err_deg': round(h_err_deg, 2),
        'innov_mean': round(innov_mean, 4),
        'innov_std': round(innov_std, 4),
        'final_p_trace': round(final_p_trace, 4),
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'psi_dr_deg': psi_dr_deg,
        'pos_err': pos_err,
        'x_gt': x_gt,
        'y_gt': y_gt,
        'v_gt': v_gt,
        'psi_gt_deg': psi_gt_deg,
        'p_trace': p_trace
    }

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    
    # 1. Calibrated DR
    xc, yc, vc, psic, wc, lat_c, _, _ = run_calib_dr(start_idx, dur)
    res_c = evaluate_dr(xc, yc, vc, psic, wc, start_idx, dur, "1. Calibrated Open-Loop DR")
    res_c['latency_ms'] = round(lat_c, 4)
    
    # 2. Classical EKF
    xe, ye, ve, psie, we, lat_e, _, _ = run_ekf_engine(start_idx, dur, 'classical')
    res_e = evaluate_dr(xe, ye, ve, psie, we, start_idx, dur, "2. Classical 7-State EKF/INS")
    res_e['latency_ms'] = round(lat_e, 4)
    
    # 3. ML-Only DR W30
    xm, ym, vm, psim, wm, lat_m, _, _ = run_ml_dr(start_idx, dur)
    res_m = evaluate_dr(xm, ym, vm, psim, wm, start_idx, dur, "3. ML-Only DR (CNN+BiLSTM, W=30)")
    res_m['latency_ms'] = round(lat_m, 4)
    
    # 4. Hybrid Config A (ML Speed)
    xa, ya, va, psia, wa, lat_a, inv_a, p_a = run_ekf_engine(start_idx, dur, 'config_a')
    res_a = evaluate_dr(xa, ya, va, psia, wa, start_idx, dur, "4. Hybrid Config A (ML Speed)", inv_a, p_a)
    res_a['latency_ms'] = round(lat_a, 4)
    
    # 5. Hybrid Config B (ML Yaw Rate)
    xb, yb, vb, psib, wb, lat_b, inv_b, p_b = run_ekf_engine(start_idx, dur, 'config_b')
    res_b = evaluate_dr(xb, yb, vb, psib, wb, start_idx, dur, "5. Hybrid Config B (ML Yaw Rate)", inv_b, p_b)
    res_b['latency_ms'] = round(lat_b, 4)
    
    # 6. Hybrid Config C (Speed + Yaw Rate)
    x_c2, y_c2, v_c2, psi_c2, w_c2, lat_c2, inv_c2, p_c2 = run_ekf_engine(start_idx, dur, 'config_c')
    res_c2 = evaluate_dr(x_c2, y_c2, v_c2, psi_c2, w_c2, start_idx, dur, "6. Hybrid Config C (Speed + Yaw Rate)", inv_c2, p_c2)
    res_c2['latency_ms'] = round(lat_c2, 4)
    
    # 7. Hybrid Config D (Adaptive Weighting)
    xd, yd, vd, psid, wd, lat_d, inv_d, p_d = run_ekf_engine(start_idx, dur, 'config_d')
    res_d = evaluate_dr(xd, yd, vd, psid, wd, start_idx, dur, "7. Hybrid Config D (Adaptive Weighting)", inv_d, p_d)
    res_d['latency_ms'] = round(lat_d, 4)
    
    plot_data[dur] = [res_c, res_e, res_m, res_a, res_b, res_c2, res_d]
    all_results.extend([res_c, res_e, res_m, res_a, res_b, res_c2, res_d])

# Save clean JSON results without numpy array fields
json_results = []
for r in all_results:
    item = {k: v for k, v in r.items() if not isinstance(v, np.ndarray) and k != 'p_trace'}
    json_results.append(item)

with open('results/vw4_hybrid_ml_ekf_results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

df_res = pd.DataFrame(json_results)[['duration_sec', 'model_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'h_err_deg', 'latency_ms']]
print("\n" + "="*120)
print("VW4 UNSEEN TEST SET: HYBRID ML + EKF NAVIGATION EVALUATION MATRIX")
print("="*120)
print(df_res.to_string(index=False))
print("="*120)

# --- High-Quality Visualization Plot Generation ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

colors = {
    "1. Calibrated Open-Loop DR": "#7f8c8d",
    "2. Classical 7-State EKF/INS": "#e74c3c",
    "3. ML-Only DR (CNN+BiLSTM, W=30)": "#9b59b6",
    "4. Hybrid Config A (ML Speed)": "#2980b9",
    "5. Hybrid Config B (ML Yaw Rate)": "#e67e22",
    "6. Hybrid Config C (Speed + Yaw Rate)": "#16a085",
    "7. Hybrid Config D (Adaptive Weighting)": "#27ae60"
}

linestyles = {
    "1. Calibrated Open-Loop DR": ":",
    "2. Classical 7-State EKF/INS": "--",
    "3. ML-Only DR (CNN+BiLSTM, W=30)": "-.",
    "4. Hybrid Config A (ML Speed)": "-",
    "5. Hybrid Config B (ML Yaw Rate)": "-",
    "6. Hybrid Config C (Speed + Yaw Rate)": "-",
    "7. Hybrid Config D (Adaptive Weighting)": "-"
}

for dur in [60, 120, 300]:
    runs = plot_data[dur]
    t_arr = np.arange(dur * 10) * dt
    
    # Figure 1: 4-Subplot Comprehensive Breakdown
    fig, axs = plt.subplots(2, 2, figsize=(16, 11))
    fig.suptitle(f'Vw4 Unseen Test Set: {dur}-Second GNSS Outage Hybrid ML+EKF Evaluation', fontsize=15, fontweight='bold')
    
    # Subplot 1: Trajectory Comparison
    axs[0, 0].plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=2.5, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        axs[0, 0].plot(r['x_dr'], r['y_dr'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.8, label=m_name)
    axs[0, 0].set_title('Trajectory Comparison (East vs North)')
    axs[0, 0].set_xlabel('East Position (m)')
    axs[0, 0].set_ylabel('North Position (m)')
    axs[0, 0].grid(True, linestyle='--', alpha=0.5)
    axs[0, 0].legend(fontsize=7, loc='best')
    
    # Subplot 2: Position Error Growth Over Time
    for r in runs:
        m_name = r['model_name']
        axs[0, 1].plot(t_arr, r['pos_err'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.8, label=m_name)
    axs[0, 1].set_title('Position Error Growth Over Time')
    axs[0, 1].set_xlabel('Outage Time (seconds)')
    axs[0, 1].set_ylabel('Position Error (meters)')
    axs[0, 1].grid(True, linestyle='--', alpha=0.5)
    axs[0, 1].legend(fontsize=7, loc='best')
    
    # Subplot 3: Speed Tracking Comparison
    axs[1, 0].plot(t_arr, runs[0]['v_gt'] * 3.6, 'k-', linewidth=2.5, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        axs[1, 0].plot(t_arr, r['v_dr'] * 3.6, color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.6, label=m_name)
    axs[1, 0].set_title('Forward Speed Tracking')
    axs[1, 0].set_xlabel('Outage Time (seconds)')
    axs[1, 0].set_ylabel('Speed (km/h)')
    axs[1, 0].grid(True, linestyle='--', alpha=0.5)
    axs[1, 0].legend(fontsize=7, loc='best')
    
    # Subplot 4: EKF Covariance Trace Growth
    for r in runs:
        m_name = r['model_name']
        if r['p_trace'] is not None and len(r['p_trace']) > 0:
            axs[1, 1].plot(t_arr, r['p_trace'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.8, label=f"{m_name} Tr(P)")
    axs[1, 1].set_title('EKF State Covariance Trace Tr(P) Convergence')
    axs[1, 1].set_xlabel('Outage Time (seconds)')
    axs[1, 1].set_ylabel('Tr(P)')
    axs[1, 1].grid(True, linestyle='--', alpha=0.5)
    axs[1, 1].legend(fontsize=7, loc='best')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_file = f'plots/vw4/hybrid_ml_ekf/outage_{dur}s_hybrid_comparison.png'
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved plot: {plot_file}")

# Summary Bar Chart across Outage Durations
fig, axs = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('Hybrid ML + EKF Navigation Drift Metrics across Outage Durations', fontsize=14, fontweight='bold')

durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.11

method_names = [r['model_name'] for r in plot_data[60]]

for idx, m_name in enumerate(method_names):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['model_name'] == m_name) for d in durations]
    cde_vals = [next(r['cde_pct'] for r in plot_data[d] if r['model_name'] == m_name) for d in durations]
    
    axs[0].bar(x_indices + idx * width, pos_errs, width, label=m_name, color=colors[m_name])
    axs[1].bar(x_indices + idx * width, cde_vals, width, label=m_name, color=colors[m_name])

axs[0].set_title('Final Position Error (meters)')
axs[0].set_xticks(x_indices + width * 3)
axs[0].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[0].set_ylabel('Position Error (m)')
axs[0].grid(True, linestyle='--', alpha=0.5)

axs[1].set_title('Cumulative Drift Error (CDE %)')
axs[1].set_xticks(x_indices + width * 3)
axs[1].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[1].set_ylabel('CDE %')
axs[1].grid(True, linestyle='--', alpha=0.5)
axs[1].legend(fontsize=7, loc='best')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
summary_plot_file = 'plots/vw4/hybrid_ml_ekf/summary_hybrid_metrics.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}")
