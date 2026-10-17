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
os.makedirs('plots/vw4/ml_nhc_heading', exist_ok=True)
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
grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y)         # m/s^2
a_lat_tilt_comp = raw_ax - grav_x    # m/s^2 (tilt-compensated lateral acceleration)
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

# --- Normalization Parameters (Computed ONLY on Training Partition :88566) ---
n_total = len(t_sync)
idx_train_end = int(n_total * 0.70) # 88566

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

# Normalize full dataset for ML inference
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

start_idx = 108000 # 46.5s after test set start
sim_range_start = start_idx - 300
sim_range_end = start_idx + 3000 + 10

# Precompute W30 ML predictions
batch_windows = []
for idx in range(sim_range_start, sim_range_end):
    win = X_norm_all[idx - 30 + 1 : idx + 1]
    batch_windows.append(win)
batch_windows = np.array(batch_windows, dtype=np.float32)

with torch.no_grad():
    preds_w30 = model_w30(torch.tensor(batch_windows, dtype=torch.float32).to(device)).cpu().numpy()

v_ml_dict = {}
w_ml_dict = {}
for i, idx in enumerate(range(sim_range_start, sim_range_end)):
    v_ml_dict[idx] = max(0.0, float(preds_w30[i, 0]))
    w_ml_dict[idx] = float(preds_w30[i, 1])

# Audit Pre-outage Stationary Gyro Bias Estimation (from stationary segment [start_idx - 100 : start_idx])
b_gyro_static = float(np.mean(w_yaw[start_idx - 100 : start_idx]))

# --- Case A: Existing ML DR (ML Speed + ML Yaw, No NHC, No Heading Anchor) ---
def run_case_a(start_idx, duration_sec):
    n = int(duration_sec / dt)
    v_dr = np.array([v_ml_dict[start_idx + k] for k in range(n)])
    w_dr = np.array([w_ml_dict[start_idx + k] for k in range(n)])
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

# --- General EKF Engine for Cases B, C, D, E ---
def run_ekf_case(start_idx, duration_sec, use_nhc=True, use_heading_anchor=False, use_gt_speed=False):
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
            # --- GNSS Outage Period ---
            v_meas = vbox_vel_ms[idx] if use_gt_speed else v_ml_dict[idx]
            w_ml = w_ml_dict[idx]
            
            # Update 1: Forward Speed Update
            v_est = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2] / v_denom, x_state[3] / v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P
            
            # Update 2: Kinematic NHC Lateral Velocity Constraint
            if use_nhc:
                psi_c = x_state[4]
                v_lat_est = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
                H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c), x_state[2] * np.sin(psi_c) + x_state[3] * np.cos(psi_c), 0, 0])
                y_nhc = 0.0 - v_lat_est
                S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
                K_nhc = (P @ H_nhc.T) / S_nhc
                x_state = x_state + K_nhc * y_nhc
                P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P
                
            # Update 3: Straight-Road Heading Anchor
            if use_heading_anchor:
                if abs(w_ml) < np.radians(0.5) and v_meas > 1.0:
                    y_w = (w_m - 0.0) - x_state[6]
                    H_w = np.array([0, 0, 0, 0, 0, 0, 1.0])
                    R_w = np.radians(0.5)**2
                    S_w = float(H_w @ P @ H_w.T + R_w)
                    K_w = (P @ H_w.T) / S_w
                    x_state = x_state + K_w * y_w
                    P = (np.eye(7) - np.outer(K_w, H_w)) @ P
                    
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

# --- Case F: ML Speed + GT Heading (Diagnostic Oracle Reference ONLY) ---
def run_case_f_oracle(start_idx, duration_sec):
    n = int(duration_sec / dt)
    v_dr = np.array([v_ml_dict[start_idx + k] for k in range(n)])
    psi_gt_deg = vbox_heading_deg[start_idx : start_idx + n]
    psi_dr_rad = np.radians(psi_gt_deg)
    
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    t0 = time.perf_counter()
    for k in range(1, n):
        x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr_rad[k]) * dt
        y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr_rad[k]) * dt
    t1 = time.perf_counter()
    w_gt = np.radians(vbox_yaw_rate_degs[start_idx : start_idx + n])
    return x_dr, y_dr, v_dr, psi_gt_deg, w_gt, ((t1 - t0) / n) * 1000.0

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
    w_gt_rads = np.radians(vbox_yaw_rate_degs[start_idx : start_idx + n])
    
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
        'w_gt': w_gt_rads,
        'psi_gt_deg': psi_gt_deg
    }

cases = [
    ("A. Existing ML DR", 'A'),
    ("B. ML DR + NHC", 'B'),
    ("C. ML DR + Heading Anchor", 'C'),
    ("D. ML DR + NHC + Heading Anchor", 'D'),
    ("E. GT Speed + ML Yaw + NHC (Diagnostic)", 'E'),
    ("F. ML Speed + GT Heading (Diagnostic)", 'F')
]

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    
    # Case A
    xa, ya, va, psia, wa, lat_a = run_case_a(start_idx, dur)
    r_a = evaluate_dr(xa, ya, va, psia, wa, start_idx, dur, cases[0][0])
    r_a['latency_ms'] = round(lat_a, 4)
    
    # Case B
    xb, yb, vb, psib, wb, lat_b = run_ekf_case(start_idx, dur, use_nhc=True, use_heading_anchor=False, use_gt_speed=False)
    r_b = evaluate_dr(xb, yb, vb, psib, wb, start_idx, dur, cases[1][0])
    r_b['latency_ms'] = round(lat_b, 4)
    
    # Case C
    xc, yc, vc, psic, wc, lat_c = run_ekf_case(start_idx, dur, use_nhc=False, use_heading_anchor=True, use_gt_speed=False)
    r_c = evaluate_dr(xc, yc, vc, psic, wc, start_idx, dur, cases[2][0])
    r_c['latency_ms'] = round(lat_c, 4)
    
    # Case D
    xd, yd, vd, psid, wd, lat_d = run_ekf_case(start_idx, dur, use_nhc=True, use_heading_anchor=True, use_gt_speed=False)
    r_d = evaluate_dr(xd, yd, vd, psid, wd, start_idx, dur, cases[3][0])
    r_d['latency_ms'] = round(lat_d, 4)
    
    # Case E (Diagnostic GT Speed + NHC)
    xe, ye, ve, psie, we, lat_e = run_ekf_case(start_idx, dur, use_nhc=True, use_heading_anchor=False, use_gt_speed=True)
    r_e = evaluate_dr(xe, ye, ve, psie, we, start_idx, dur, cases[4][0])
    r_e['latency_ms'] = round(lat_e, 4)
    
    # Case F (Diagnostic GT Heading)
    xf, yf, vf, psif, wf, lat_f = run_case_f_oracle(start_idx, dur)
    r_f = evaluate_dr(xf, yf, vf, psif, wf, start_idx, dur, cases[5][0])
    r_f['latency_ms'] = round(lat_f, 4)
    
    # Compute Percentage Improvements over Case A Baseline
    for r in [r_a, r_b, r_c, r_d, r_e, r_f]:
        pct_imp = float(((r_a['final_pos_err_m'] - r['final_pos_err_m']) / r_a['final_pos_err_m']) * 100.0)
        r['pct_imp_vs_baseline'] = round(pct_imp, 2)
        
    plot_data[dur] = [r_a, r_b, r_c, r_d, r_e, r_f]
    all_results.extend([r_a, r_b, r_c, r_d, r_e, r_f])

# Save JSON results without numpy arrays
json_results = [{k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for r in all_results]

with open('results/vw4_ml_nhc_heading_results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

df_res = pd.DataFrame(json_results)[['duration_sec', 'case_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg', 'pct_imp_vs_baseline', 'latency_ms']]
print("\n" + "="*145)
print("VW4 UNSEEN TEST SET: CONTROLLED ML + NHC + HEADING ANCHOR ABLATION MATRIX")
print("="*145)
print(df_res.to_string(index=False))
print("="*145)

# --- High-Quality Visualization Plot Generation (10 Plots) ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

case_colors = {
    "A. Existing ML DR": "#9b59b6",
    "B. ML DR + NHC": "#3498db",
    "C. ML DR + Heading Anchor": "#e67e22",
    "D. ML DR + NHC + Heading Anchor": "#27ae60",
    "E. GT Speed + ML Yaw + NHC (Diagnostic)": "#16a085",
    "F. ML Speed + GT Heading (Diagnostic)": "#e74c3c"
}

case_styles = {
    "A. Existing ML DR": ":",
    "B. ML DR + NHC": "-",
    "C. ML DR + Heading Anchor": "-.",
    "D. ML DR + NHC + Heading Anchor": "-",
    "E. GT Speed + ML Yaw + NHC (Diagnostic)": "--",
    "F. ML Speed + GT Heading (Diagnostic)": "-"
}

# Plots 1, 2, 3: Trajectory Comparisons for 60s, 120s, 300s
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
    plt.savefig(f'plots/vw4/ml_nhc_heading/outage_{dur}s_trajectory.png', dpi=300)
    plt.close()

# Plot 4: 300s Position Error Growth Over Time
fig, ax = plt.subplots(figsize=(10, 6))
runs300 = plot_data[300]
t_arr300 = np.arange(3000) * dt
for r in runs300:
    c_name = r['case_name']
    ax.plot(t_arr300, r['pos_err'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
ax.set_title('Vw4 Unseen Test Set: 300s Outage Position Error Growth Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Position Error (meters)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/outage_300s_position_error.png', dpi=300)
plt.close()

# Plot 5: 300s Heading Error Growth Over Time
fig, ax = plt.subplots(figsize=(10, 6))
for r in runs300:
    c_name = r['case_name']
    ax.plot(t_arr300, r['h_err_arr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
ax.set_title('Vw4 Unseen Test Set: 300s Outage Heading Error Growth Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Heading Error (degrees)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/outage_300s_heading_error.png', dpi=300)
plt.close()

# Plot 6: 300s Speed Error Growth Over Time
fig, ax = plt.subplots(figsize=(10, 6))
for r in runs300:
    c_name = r['case_name']
    ax.plot(t_arr300, r['vel_err_arr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=1.8, label=c_name)
ax.set_title('Vw4 Unseen Test Set: 300s Outage Speed Error Over Time', fontsize=14, fontweight='bold')
ax.set_xlabel('Outage Time (seconds)')
ax.set_ylabel('Speed Error (km/h)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/outage_300s_speed_error.png', dpi=300)
plt.close()

# Plot 7: CDE Comparison Bar Chart
fig, ax = plt.subplots(figsize=(10, 6))
durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.13
for idx, (c_name, _) in enumerate(cases):
    cde_vals = [next(r['cde_pct'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    ax.bar(x_indices + idx * width, cde_vals, width, label=c_name, color=case_colors[c_name])
ax.set_title('Cumulative Distance Error (CDE %) Across Outage Blackouts', fontsize=14, fontweight='bold')
ax.set_xticks(x_indices + width * 2.5)
ax.set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
ax.set_ylabel('CDE %')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/cde_comparison.png', dpi=300)
plt.close()

# Plot 8: Final Position Error Comparison Bar Chart
fig, ax = plt.subplots(figsize=(10, 6))
for idx, (c_name, _) in enumerate(cases):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    ax.bar(x_indices + idx * width, pos_errs, width, label=c_name, color=case_colors[c_name])
ax.set_title('Final Position Error (meters) Across Outage Blackouts', fontsize=14, fontweight='bold')
ax.set_xticks(x_indices + width * 2.5)
ax.set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
ax.set_ylabel('Final Position Error (m)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/final_position_error_comparison.png', dpi=300)
plt.close()

# Plot 9: Final Heading Error Comparison Bar Chart
fig, ax = plt.subplots(figsize=(10, 6))
for idx, (c_name, _) in enumerate(cases):
    h_errs = [next(r['final_h_err_deg'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    ax.bar(x_indices + idx * width, h_errs, width, label=c_name, color=case_colors[c_name])
ax.set_title('Final Heading Error (degrees) Across Outage Blackouts', fontsize=14, fontweight='bold')
ax.set_xticks(x_indices + width * 2.5)
ax.set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
ax.set_ylabel('Heading Error (deg)')
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(fontsize=8, loc='best')
plt.tight_layout()
plt.savefig('plots/vw4/ml_nhc_heading/heading_error_comparison.png', dpi=300)
plt.close()

# Plot 10: Ablation Summary Matrix Dashboard Chart
fig, axs = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('Controlled ML + NHC + Heading Anchor Ablation Dashboard', fontsize=14, fontweight='bold')
for idx, (c_name, _) in enumerate(cases):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    pct_imps = [next(r['pct_imp_vs_baseline'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    axs[0].bar(x_indices + idx * width, pos_errs, width, label=c_name, color=case_colors[c_name])
    axs[1].bar(x_indices + idx * width, pct_imps, width, label=c_name, color=case_colors[c_name])

axs[0].set_title('Final Position Error (meters)')
axs[0].set_xticks(x_indices + width * 2.5)
axs[0].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[0].set_ylabel('Position Error (m)')
axs[0].grid(True, linestyle='--', alpha=0.5)

axs[1].set_title('Percentage Improvement vs Baseline (%)')
axs[1].set_xticks(x_indices + width * 2.5)
axs[1].set_xticklabels(['60s Outage', '120s Outage', '300s Outage'])
axs[1].set_ylabel('Improvement %')
axs[1].grid(True, linestyle='--', alpha=0.5)
axs[1].legend(fontsize=7, loc='best')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
summary_plot_file = 'plots/vw4/ml_nhc_heading/ablation_summary.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}")
