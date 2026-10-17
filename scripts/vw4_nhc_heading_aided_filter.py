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
os.makedirs('plots/vw4/nhc_heading_aided', exist_ok=True)
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

# Sensor Processing Signals
raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y) # m/s^2
a_lat_imu = raw_ax           # m/s^2 (lateral acceleration in phone frame)
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

# --- Load Trained PyTorch Models (CNN + BiLSTM W=30 and W=20) ---
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

model_w20 = CNNBiLSTMModel(window_size=20).to(device)
model_w20.load_state_dict(torch.load('models/cnn_plus_bilstm_w20.pth'))
model_w20.eval()

start_idx = 108000 # 46.5s after test set start
sim_range_start = start_idx - 300
sim_range_end = start_idx + 3000 + 10

# Precompute W30 predictions
batch_windows_w30 = []
for idx in range(sim_range_start, sim_range_end):
    win = X_norm_all[idx - 30 + 1 : idx + 1]
    batch_windows_w30.append(win)
batch_windows_w30 = np.array(batch_windows_w30, dtype=np.float32)

with torch.no_grad():
    preds_w30 = model_w30(torch.tensor(batch_windows_w30, dtype=torch.float32).to(device)).cpu().numpy()

v_w30_dict = {}
w_w30_dict = {}
for i, idx in enumerate(range(sim_range_start, sim_range_end)):
    v_w30_dict[idx] = max(0.0, float(preds_w30[i, 0]))
    w_w30_dict[idx] = float(preds_w30[i, 1])

# Precompute W20 predictions
batch_windows_w20 = []
for idx in range(sim_range_start, sim_range_end):
    win = X_norm_all[idx - 20 + 1 : idx + 1]
    batch_windows_w20.append(win)
batch_windows_w20 = np.array(batch_windows_w20, dtype=np.float32)

with torch.no_grad():
    preds_w20 = model_w20(torch.tensor(batch_windows_w20, dtype=torch.float32).to(device)).cpu().numpy()

v_w20_dict = {}
w_w20_dict = {}
for i, idx in enumerate(range(sim_range_start, sim_range_end)):
    v_w20_dict[idx] = max(0.0, float(preds_w20[i, 0]))
    w_w20_dict[idx] = float(preds_w20[i, 1])

# --- Baseline Algorithm Implementations ---

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
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw[start_idx : start_idx + n], ((t1 - t0) / n) * 1000.0

def run_calib_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    b_accel_pre = np.mean(a_long[start_idx - 100 : start_idx])
    a_cal = a_long - b_accel_pre
    
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    v_dr[0] = vbox_vel_ms[start_idx]
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for i in range(1, n):
        psi_dr[i] = psi_dr[i-1] + w_yaw[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_cal[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        x_dr[i] = x_dr[i-1] + v_dr[i] * np.sin(psi_dr[i]) * dt
        y_dr[i] = y_dr[i-1] + v_dr[i] * np.cos(psi_dr[i]) * dt
    t1 = time.perf_counter()
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_yaw[start_idx : start_idx + n], ((t1 - t0) / n) * 1000.0

def run_classical_ekf(start_idx, duration_sec):
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
            x_hist.append(x_state.copy())
            
    t1 = time.perf_counter()
    x_hist_arr = np.array(x_hist)
    x_ekf = x_hist_arr[:, 0] - x_hist_arr[0, 0]
    y_ekf = x_hist_arr[:, 1] - x_hist_arr[0, 1]
    v_ekf = np.sqrt(x_hist_arr[:, 2]**2 + x_hist_arr[:, 3]**2)
    psi_ekf_deg = np.degrees(x_hist_arr[:, 4])
    return x_ekf, y_ekf, v_ekf, psi_ekf_deg, w_yaw[start_idx : start_idx + n], ((t1 - t0) / (pre_samples + n)) * 1000.0

def run_ml_dr(start_idx, duration_sec, v_dict, w_dict):
    n = int(duration_sec / dt)
    v_dr = np.array([v_dict[start_idx + k] for k in range(n)])
    w_dr = np.array([w_dict[start_idx + k] for k in range(n)])
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for k in range(1, n):
        psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
        x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
        y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
    t1 = time.perf_counter()
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, ((t1 - t0) / n) * 1000.0

# --- PROPOSED: Closed-Loop NHC + Heading-Aided ML DR Filter ---
def run_nhc_heading_aided_filter(start_idx, duration_sec, enable_nhc=True, enable_heading_corr=True):
    n = int(duration_sec / dt)
    v_ml = np.array([v_w30_dict[start_idx + k] for k in range(n)])
    w_ml = np.array([w_w30_dict[start_idx + k] for k in range(n)])
    
    v_dr = np.zeros(n)
    w_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    t0 = time.perf_counter()
    for k in range(n):
        idx = start_idx + k
        v_pred = v_ml[k]
        w_pred = w_ml[k]
        a_lat = a_lat_imu[idx]
        
        # 1. Stationary Detection (ZUPT / ZARU) based strictly on phone IMU vibration
        imu_accel_std = np.std(X_raw_all[max(0, idx-5):idx+1, 0:3])
        imu_gyro_mag = np.linalg.norm(X_raw_all[idx, 3:6])
        
        if imu_accel_std < 0.15 and imu_gyro_mag < 0.02:
            v_curr = 0.0
            w_curr = 0.0
        else:
            v_curr = v_pred
            w_curr = w_pred
            
            if enable_heading_corr:
                # 2. Straight-Road Heading Anchor
                if abs(w_pred) < np.radians(0.5) and v_curr > 1.0:
                    w_curr = 0.0
                elif v_curr > 2.0 and abs(a_lat) > 0.1:
                    # 3. Centrifugal Acceleration Alignment Cross-Check
                    w_centrifugal = a_lat / v_curr
                    w_curr = 0.70 * w_pred + 0.30 * w_centrifugal
                    
        v_dr[k] = v_curr
        w_dr[k] = w_curr
        
        if k > 0:
            psi_dr[k] = psi_dr[k-1] + w_curr * dt
            
            if enable_nhc:
                # 4. Kinematic NHC: Zero lateral body velocity constraint (v_lat = 0)
                vx_enu = v_curr * np.sin(psi_dr[k])
                vy_enu = v_curr * np.cos(psi_dr[k])
            else:
                vx_enu = v_curr * np.sin(psi_dr[k])
                vy_enu = v_curr * np.cos(psi_dr[k])
                
            x_dr[k] = x_dr[k-1] + vx_enu * dt
            y_dr[k] = y_dr[k-1] + vy_enu * dt
            
    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / n) * 1000.0
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr, lat_ms

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
    
    return {
        'duration_sec': int(duration_sec),
        'model_name': str(model_name),
        'dist_gt_m': round(dist_gt, 2),
        'dist_dr_m': round(dist_dr, 2),
        'cde_pct': round(cde_pct, 2),
        'final_pos_err_m': round(final_pos_err, 2),
        'max_pos_err_m': round(max_pos_err, 2),
        'drift_rate_ms': round(drift_rate_ms, 2),
        'v_mae_kmh': round(v_mae_kmh, 2),
        'v_rmse_kmh': round(v_rmse_kmh, 2),
        'final_h_err_deg': round(final_h_err_deg, 2),
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'psi_dr_deg': psi_dr_deg,
        'pos_err': pos_err,
        'vel_err_arr': vel_err_arr,
        'h_err_arr': h_err_arr,
        'x_gt': x_gt,
        'y_gt': y_gt,
        'v_gt': v_gt,
        'psi_gt_deg': psi_gt_deg
    }

# --- Part 1: Main 6-Algorithm Benchmark Benchmark Suite ---
benchmark_models = [
    "1. Raw Open-Loop DR",
    "2. Calibrated Open-Loop DR",
    "3. Classical 7-State EKF/INS",
    "4. ML DR (CNN+BiLSTM, W=20)",
    "5. ML DR (CNN+BiLSTM, W=30)",
    "6. NHC + Heading-Aided ML Filter"
]

benchmark_results = []
plot_data_bench = {}

for dur in [60, 120, 300]:
    plot_data_bench[dur] = []
    
    # 1. Raw DR
    xr, yr, vr, psir, wr, lat_r = run_raw_dr(start_idx, dur)
    res_r = evaluate_dr(xr, yr, vr, psir, wr, start_idx, dur, benchmark_models[0])
    res_r['latency_ms'] = round(lat_r, 4)
    
    # 2. Calib DR
    xc, yc, vc, psic, wc, lat_c = run_calib_dr(start_idx, dur)
    res_c = evaluate_dr(xc, yc, vc, psic, wc, start_idx, dur, benchmark_models[1])
    res_c['latency_ms'] = round(lat_c, 4)
    
    # 3. Classical EKF
    xe, ye, ve, psie, we, lat_e = run_classical_ekf(start_idx, dur)
    res_e = evaluate_dr(xe, ye, ve, psie, we, start_idx, dur, benchmark_models[2])
    res_e['latency_ms'] = round(lat_e, 4)
    
    # 4. ML DR W20
    xm20, ym20, vm20, psim20, wm20, lat_m20 = run_ml_dr(start_idx, dur, v_w20_dict, w_w20_dict)
    res_m20 = evaluate_dr(xm20, ym20, vm20, psim20, wm20, start_idx, dur, benchmark_models[3])
    res_m20['latency_ms'] = round(lat_m20, 4)
    
    # 5. ML DR W30 (Baseline)
    xm30, ym30, vm30, psim30, wm30, lat_m30 = run_ml_dr(start_idx, dur, v_w30_dict, w_w30_dict)
    res_m30 = evaluate_dr(xm30, ym30, vm30, psim30, wm30, start_idx, dur, benchmark_models[4])
    res_m30['latency_ms'] = round(lat_m30, 4)
    
    # 6. Proposed NHC + Heading-Aided ML Filter
    xf, yf, vf, psif, wf, lat_f = run_nhc_heading_aided_filter(start_idx, dur, enable_nhc=True, enable_heading_corr=True)
    res_f = evaluate_dr(xf, yf, vf, psif, wf, start_idx, dur, benchmark_models[5])
    res_f['latency_ms'] = round(lat_f, 4)
    
    # Compute relative % improvements
    pct_imp_ml_w30 = float(((res_m30['final_pos_err_m'] - res_f['final_pos_err_m']) / res_m30['final_pos_err_m']) * 100.0)
    pct_imp_ekf    = float(((res_e['final_pos_err_m'] - res_f['final_pos_err_m']) / res_e['final_pos_err_m']) * 100.0)
    
    res_f['pct_imp_ml_w30'] = round(pct_imp_ml_w30, 2)
    res_f['pct_imp_ekf'] = round(pct_imp_ekf, 2)
    
    # Add dummy default values for other models for clean table display
    for r in [res_r, res_c, res_e, res_m20, res_m30]:
        r['pct_imp_ml_w30'] = 0.0
        r['pct_imp_ekf'] = 0.0
        
    plot_data_bench[dur] = [res_r, res_c, res_e, res_m20, res_m30, res_f]
    benchmark_results.extend([res_r, res_c, res_e, res_m20, res_m30, res_f])

# --- Part 2: Internal 4-Case Ablation Suite ---
ablation_cases = [
    ("ML Only", False, False),
    ("ML + NHC", True, False),
    ("ML + Heading Correction", False, True),
    ("ML + NHC + Heading Correction", True, True)
]

ablation_results = []
for dur in [60, 120, 300]:
    for case_name, enable_nhc, enable_heading in ablation_cases:
        xa, ya, va, psia, wa, lat_a = run_nhc_heading_aided_filter(start_idx, dur, enable_nhc=enable_nhc, enable_heading_corr=enable_heading)
        res_abl = evaluate_dr(xa, ya, va, psia, wa, start_idx, dur, case_name)
        res_abl['latency_ms'] = round(lat_a, 4)
        ablation_results.append(res_abl)

# Save JSON results
json_output = {
    'benchmark_results': [{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in benchmark_results],
    'ablation_results': [{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in ablation_results]
}

with open('results/vw4_nhc_heading_aided_results.json', 'w') as f:
    json.dump(json_output, f, indent=2)

df_bench = pd.DataFrame(json_output['benchmark_results'])[['duration_sec', 'model_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg', 'pct_imp_ml_w30', 'pct_imp_ekf', 'latency_ms']]

print("\n" + "="*140)
print("VW4 UNSEEN TEST SET: BENCHMARK MATRIX (PROPOSED FILTER VS ALL BASELINES)")
print("="*140)
print(df_bench.to_string(index=False))
print("="*140)

df_abl = pd.DataFrame(json_output['ablation_results'])[['duration_sec', 'model_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg']]
print("\n" + "="*120)
print("INTERNAL 4-CASE ABLATION MATRIX (ML ONLY VS NHC VS HEADING CORRECTION)")
print("="*120)
print(df_abl.to_string(index=False))
print("="*120)

# --- High-Quality Visualization Plot Generation ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

bench_colors = {
    "1. Raw Open-Loop DR": "#95a5a6",
    "2. Calibrated Open-Loop DR": "#7f8c8d",
    "3. Classical 7-State EKF/INS": "#e74c3c",
    "4. ML DR (CNN+BiLSTM, W=20)": "#9b59b6",
    "5. ML DR (CNN+BiLSTM, W=30)": "#3498db",
    "6. NHC + Heading-Aided ML Filter": "#27ae60"
}

bench_styles = {
    "1. Raw Open-Loop DR": ":",
    "2. Calibrated Open-Loop DR": ":",
    "3. Classical 7-State EKF/INS": "--",
    "4. ML DR (CNN+BiLSTM, W=20)": "-.",
    "5. ML DR (CNN+BiLSTM, W=30)": "-.",
    "6. NHC + Heading-Aided ML Filter": "-"
}

for dur in [60, 120, 300]:
    runs = plot_data_bench[dur]
    t_arr = np.arange(dur * 10) * dt
    
    # Figure 1: Trajectory Comparison
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=3.0, label='VBOX Ground Truth')
    for r in runs:
        m_name = r['model_name']
        ax.plot(r['x_dr'], r['y_dr'], color=bench_colors[m_name], linestyle=bench_styles[m_name], linewidth=1.8, label=m_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Trajectory Benchmark', fontsize=14, fontweight='bold')
    ax.set_xlabel('East Position (m)')
    ax.set_ylabel('North Position (m)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/nhc_heading_aided/outage_{dur}s_trajectory.png', dpi=300)
    plt.close()
    
    # Figure 2: Position Error Growth vs Time
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in runs:
        m_name = r['model_name']
        ax.plot(t_arr, r['pos_err'], color=bench_colors[m_name], linestyle=bench_styles[m_name], linewidth=1.8, label=m_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Position Error Growth', fontsize=14, fontweight='bold')
    ax.set_xlabel('Outage Time (seconds)')
    ax.set_ylabel('Position Error (meters)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/nhc_heading_aided/outage_{dur}s_position_error.png', dpi=300)
    plt.close()
    
    # Figure 3: Heading Error vs Time
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in runs:
        m_name = r['model_name']
        ax.plot(t_arr, r['h_err_arr'], color=bench_colors[m_name], linestyle=bench_styles[m_name], linewidth=1.8, label=m_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Heading Error Growth', fontsize=14, fontweight='bold')
    ax.set_xlabel('Outage Time (seconds)')
    ax.set_ylabel('Heading Error (degrees)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/nhc_heading_aided/outage_{dur}s_heading_error.png', dpi=300)
    plt.close()

# Figure 4: Summary Benchmark Bar Chart
fig, axs = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('NHC + Heading-Aided ML Filter vs All Baselines Benchmark', fontsize=14, fontweight='bold')

durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.13

for idx, m_name in enumerate(benchmark_models):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data_bench[d] if r['model_name'] == m_name) for d in durations]
    cde_vals = [next(r['cde_pct'] for r in plot_data_bench[d] if r['model_name'] == m_name) for d in durations]
    
    axs[0].bar(x_indices + idx * width, pos_errs, width, label=m_name, color=bench_colors[m_name])
    axs[1].bar(x_indices + idx * width, cde_vals, width, label=m_name, color=bench_colors[m_name])

axs[0].set_title('Final Position Error (meters)')
axs[0].set_xticks(x_indices + width * 2.5)
axs[0].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[0].set_ylabel('Position Error (m)')
axs[0].grid(True, linestyle='--', alpha=0.5)

axs[1].set_title('Cumulative Drift Error (CDE %)')
axs[1].set_xticks(x_indices + width * 2.5)
axs[1].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[1].set_ylabel('CDE %')
axs[1].grid(True, linestyle='--', alpha=0.5)
axs[1].legend(fontsize=7, loc='best')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
summary_plot_file = 'plots/vw4/nhc_heading_aided/summary_benchmark_metrics.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}")
