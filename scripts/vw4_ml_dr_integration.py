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
os.makedirs('plots/vw4/ml_dr_integration', exist_ok=True)
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
idx_val_end = int(n_total * 0.85)   # 107535

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

# Normalize full dataset for ML inference
X_norm_all = (X_raw_all - train_mean) / train_std

# --- Load Trained PyTorch Models ---
class CNNBiLSTMModel(nn.Module):
    def __init__(self, window_size, in_channels=6, out_channels=2, hidden_dim=64):
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

model_w20 = CNNBiLSTMModel(window_size=20).to(device)
model_w20.load_state_dict(torch.load('models/cnn_plus_bilstm_w20.pth'))
model_w20.eval()

model_w30 = CNNBiLSTMModel(window_size=30).to(device)
model_w30.load_state_dict(torch.load('models/cnn_plus_bilstm_w30.pth'))
model_w30.eval()

# --- Algorithm 1: Raw Open-Loop DR ---
def run_raw_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    v_dr[0] = vbox_vel_ms[start_idx]
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for i in range(1, n):
        psi_dr[i] = psi_dr[i-1] + w_yaw[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_long[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        
        x_dr[i] = x_dr[i-1] + v_dr[i] * np.sin(psi_dr[i]) * dt
        y_dr[i] = y_dr[i-1] + v_dr[i] * np.cos(psi_dr[i]) * dt
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / n) * 1000.0
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw[start_idx : start_idx + n], lat_ms

# --- Algorithm 2: Calibrated Open-Loop DR ---
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
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw[start_idx : start_idx + n], lat_ms

# --- Algorithm 3: Classical 7-State EKF/INS Sensor Fusion ---
def run_ekf(start_idx, duration_sec):
    n = int(duration_sec / dt)
    pre_samples = 300 # 30s pre-outage GNSS aiding
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
    H = np.zeros((5, 7))
    for k_idx in range(5): H[k_idx, k_idx] = 1.0
    
    x_hist = []
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
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            psi_meas_unwrapped = x_state[4] + psi_diff
            
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], psi_meas_unwrapped])
            y_meas = z_gnss - H @ x_state
            S = H @ P @ H.T + R_gnss
            K = P @ H.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H) @ P
            
        x_hist.append(x_state.copy())
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / (pre_samples + n)) * 1000.0
        
    x_hist_arr = np.array(x_hist)[-n:]
    x_ekf = x_hist_arr[:, 0] - x_hist_arr[0, 0]
    y_ekf = x_hist_arr[:, 1] - x_hist_arr[0, 1]
    v_ekf = np.sqrt(x_hist_arr[:, 2]**2 + x_hist_arr[:, 3]**2)
    psi_ekf_deg = np.degrees(x_hist_arr[:, 4])
    w_yaw_ekf = w_yaw[start_idx : start_idx + n] - x_hist_arr[:, 6]
    return x_ekf, y_ekf, v_ekf, psi_ekf_deg, w_yaw_ekf, lat_ms

# --- Algorithm 4 & 5: Fast Vectorized Batch Inference ML DR ---
def run_ml_dr(model, window_size, start_idx, duration_sec):
    n = int(duration_sec / dt)
    
    # Prepare batch of sliding windows
    batch_windows = []
    for k in range(n):
        idx = start_idx + k
        win = X_norm_all[idx - window_size + 1 : idx + 1]
        batch_windows.append(win)
    batch_windows = np.array(batch_windows, dtype=np.float32)
    
    t0 = time.perf_counter()
    with torch.no_grad():
        x_tensor = torch.tensor(batch_windows, dtype=torch.float32).to(device)
        preds = model(x_tensor).cpu().numpy()
    t1 = time.perf_counter()
    lat_ms = float((t1 - t0) / n * 1000.0)
    
    v_dr = np.clip(preds[:, 0], 0.0, None)
    w_yaw_pred = preds[:, 1]
    
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    for k in range(1, n):
        psi_dr[k] = psi_dr[k-1] + w_yaw_pred[k] * dt
        x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
        y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw_pred, lat_ms

# --- Metrics Evaluator ---
def evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr_rads, start_idx, duration_sec, model_name):
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
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'psi_dr_deg': psi_dr_deg,
        'pos_err': pos_err,
        'x_gt': x_gt,
        'y_gt': y_gt,
        'v_gt': v_gt,
        'psi_gt_deg': psi_gt_deg
    }

# Place outage start strictly in UNSEEN TEST SET partition
# Test set indices: [107535 : 126505]
start_idx = 108000 # 46.5s after test set start

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    
    # 1. Raw DR
    xr, yr, vr, psir, wr, lat_r = run_raw_dr(start_idx, dur)
    res_r = evaluate_dr(xr, yr, vr, psir, wr, start_idx, dur, "1. Raw Open-Loop DR")
    res_r['latency_ms'] = round(lat_r, 4)
    
    # 2. Calibrated DR
    xc, yc, vc, psic, wc, lat_c = run_calib_dr(start_idx, dur)
    res_c = evaluate_dr(xc, yc, vc, psic, wc, start_idx, dur, "2. Calibrated Open-Loop DR")
    res_c['latency_ms'] = round(lat_c, 4)
    
    # 3. Classical EKF
    xe, ye, ve, psie, we, lat_e = run_ekf(start_idx, dur)
    res_e = evaluate_dr(xe, ye, ve, psie, we, start_idx, dur, "3. Classical 7-State EKF/INS")
    res_e['latency_ms'] = round(lat_e, 4)
    
    # 4. ML DR W20
    x20, y20, v20, psi20, w20, lat_20 = run_ml_dr(model_w20, 20, start_idx, dur)
    res_20 = evaluate_dr(x20, y20, v20, psi20, w20, start_idx, dur, "4. ML DR (CNN+BiLSTM, W=20)")
    res_20['latency_ms'] = round(lat_20, 4)
    
    # 5. ML DR W30
    x30, y30, v30, psi30, w30, lat_30 = run_ml_dr(model_w30, 30, start_idx, dur)
    res_30 = evaluate_dr(x30, y30, v30, psi30, w30, start_idx, dur, "5. ML DR (CNN+BiLSTM, W=30)")
    res_30['latency_ms'] = round(lat_30, 4)
    
    plot_data[dur] = [res_r, res_c, res_e, res_20, res_30]
    all_results.extend([res_r, res_c, res_e, res_20, res_30])

# Save clean JSON results without numpy array fields
json_results = []
for r in all_results:
    item = {k: v for k, v in r.items() if not isinstance(v, np.ndarray)}
    json_results.append(item)

with open('results/vw4_ml_dr_results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

df_res = pd.DataFrame(json_results)[['duration_sec', 'model_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'h_err_deg', 'latency_ms']]
print("\n" + "="*115)
print("VW4 UNSEEN TEST SET: DEAD-RECKONING COMPARATIVE EVALUATION MATRIX")
print("="*115)
print(df_res.to_string(index=False))
print("="*115)

# --- High-Quality Visualization Plot Generation ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

colors = {
    "1. Raw Open-Loop DR": "#e74c3c",
    "2. Calibrated Open-Loop DR": "#e67e22",
    "3. Classical 7-State EKF/INS": "#2980b9",
    "4. ML DR (CNN+BiLSTM, W=20)": "#9b59b6",
    "5. ML DR (CNN+BiLSTM, W=30)": "#27ae60"
}

linestyles = {
    "1. Raw Open-Loop DR": ":",
    "2. Calibrated Open-Loop DR": "--",
    "3. Classical 7-State EKF/INS": "-.",
    "4. ML DR (CNN+BiLSTM, W=20)": "-",
    "5. ML DR (CNN+BiLSTM, W=30)": "-"
}

for dur in [60, 120, 300]:
    runs = plot_data[dur]
    t_arr = np.arange(dur * 10) * dt
    
    # Figure 1: 4-Subplot Comprehensive Breakdown
    fig, axs = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(f'Vw4 Unseen Test Set: {dur}-Second GNSS Outage Comparative Evaluation', fontsize=15, fontweight='bold')
    
    # Subplot 1: Trajectory Comparison
    axs[0, 0].plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=2.5, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        axs[0, 0].plot(r['x_dr'], r['y_dr'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=2.0, label=m_name)
    axs[0, 0].set_title('Trajectory Comparison (East vs North)')
    axs[0, 0].set_xlabel('East Position (m)')
    axs[0, 0].set_ylabel('North Position (m)')
    axs[0, 0].grid(True, linestyle='--', alpha=0.5)
    axs[0, 0].legend(fontsize=8)
    
    # Subplot 2: Position Drift Over Time
    for r in runs:
        m_name = r['model_name']
        axs[0, 1].plot(t_arr, r['pos_err'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=2.0, label=m_name)
    axs[0, 1].set_title('Position Error Growth Over Time')
    axs[0, 1].set_xlabel('Outage Time (seconds)')
    axs[0, 1].set_ylabel('Position Error (meters)')
    axs[0, 1].grid(True, linestyle='--', alpha=0.5)
    axs[0, 1].legend(fontsize=8)
    
    # Subplot 3: Forward Velocity Estimation
    axs[1, 0].plot(t_arr, runs[0]['v_gt'] * 3.6, 'k-', linewidth=2.5, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        axs[1, 0].plot(t_arr, r['v_dr'] * 3.6, color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.8, label=m_name)
    axs[1, 0].set_title('Forward Velocity Estimation')
    axs[1, 0].set_xlabel('Outage Time (seconds)')
    axs[1, 0].set_ylabel('Speed (km/h)')
    axs[1, 0].grid(True, linestyle='--', alpha=0.5)
    axs[1, 0].legend(fontsize=8)
    
    # Subplot 4: Heading Tracking
    axs[1, 1].plot(t_arr, runs[0]['psi_gt_deg'], 'k-', linewidth=2.5, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        axs[1, 1].plot(t_arr, r['psi_dr_deg'], color=colors[m_name], linestyle=linestyles[m_name], linewidth=1.8, label=m_name)
    axs[1, 1].set_title('Heading Orientation Tracking')
    axs[1, 1].set_xlabel('Outage Time (seconds)')
    axs[1, 1].set_ylabel('Heading (degrees)')
    axs[1, 1].grid(True, linestyle='--', alpha=0.5)
    axs[1, 1].legend(fontsize=8)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_file = f'plots/vw4/ml_dr_integration/outage_{dur}s_comparison.png'
    plt.savefig(plot_file, dpi=300)
    plt.close()
    print(f"Saved plot: {plot_file}")

# Summary Bar Chart across Outage Durations
fig, axs = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Vw4 Navigation Drift Metrics across Outage Durations', fontsize=14, fontweight='bold')

durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.15

method_names = [r['model_name'] for r in plot_data[60]]

for idx, m_name in enumerate(method_names):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['model_name'] == m_name) for d in durations]
    cde_vals = [next(r['cde_pct'] for r in plot_data[d] if r['model_name'] == m_name) for d in durations]
    
    axs[0].bar(x_indices + idx * width, pos_errs, width, label=m_name, color=colors[m_name])
    axs[1].bar(x_indices + idx * width, cde_vals, width, label=m_name, color=colors[m_name])

axs[0].set_title('Final Position Error (meters)')
axs[0].set_xticks(x_indices + width * 2)
axs[0].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[0].set_ylabel('Position Error (m)')
axs[0].grid(True, linestyle='--', alpha=0.5)

axs[1].set_title('Cumulative Drift Error (CDE %)')
axs[1].set_xticks(x_indices + width * 2)
axs[1].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[1].set_ylabel('CDE %')
axs[1].grid(True, linestyle='--', alpha=0.5)
axs[1].legend(fontsize=8)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
summary_plot_file = 'plots/vw4/ml_dr_integration/summary_metrics_comparison.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}")
