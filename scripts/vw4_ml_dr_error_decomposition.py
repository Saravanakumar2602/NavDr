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
os.makedirs('plots/vw4/ml_dr_error_decomposition', exist_ok=True)
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

# Fast sliding window batch inference for the outage simulation range
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

# --- 5 Ablation Case Implementations ---

def run_ablation_case(start_idx, duration_sec, case_letter):
    n = int(duration_sec / dt)
    
    v_gt_sub = vbox_vel_ms[start_idx : start_idx + n]
    w_gt_sub = np.radians(vbox_yaw_rate_degs[start_idx : start_idx + n])
    psi_gt_deg_sub = vbox_heading_deg[start_idx : start_idx + n]
    
    v_ml_sub = np.array([v_ml_dict[start_idx + k] for k in range(n)])
    w_ml_sub = np.array([w_ml_dict[start_idx + k] for k in range(n)])
    
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    w_dr = np.zeros(n)
    
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    if case_letter == 'A':
        # Case A: Ground-truth velocity + Ground-truth yaw rate
        v_dr = v_gt_sub
        w_dr = w_gt_sub
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
            
    elif case_letter == 'B':
        # Case B: ML velocity + Ground-truth yaw rate
        v_dr = v_ml_sub
        w_dr = w_gt_sub
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
            
    elif case_letter == 'C':
        # Case C: Ground-truth velocity + ML yaw rate
        v_dr = v_gt_sub
        w_dr = w_ml_sub
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
            
    elif case_letter == 'D':
        # Case D: ML velocity + ML yaw rate (reproduces current ML-DR exactly)
        v_dr = v_ml_sub
        w_dr = w_ml_sub
        for k in range(1, n):
            psi_dr[k] = psi_dr[k-1] + w_dr[k] * dt
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
            
    elif case_letter == 'E':
        # Case E: ML velocity + True heading
        v_dr = v_ml_sub
        w_dr = w_ml_sub
        psi_dr = np.radians(psi_gt_deg_sub)
        for k in range(1, n):
            x_dr[k] = x_dr[k-1] + v_dr[k] * np.sin(psi_dr[k]) * dt
            y_dr[k] = y_dr[k-1] + v_dr[k] * np.cos(psi_dr[k]) * dt
            
    return x_dr, y_dr, v_dr, np.degrees(psi_dr), w_dr

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
    final_v_err_kmh = float(abs(v_dr[-1] - v_gt[-1]) * 3.6)
    
    w_mae_degs = float(np.degrees(np.mean(np.abs(w_dr_rads - w_gt_rads))))
    w_rmse_degs = float(np.degrees(np.sqrt(np.mean((w_dr_rads - w_gt_rads)**2))))
    
    h_err_arr = np.abs((psi_dr_deg - psi_gt_deg + 180) % 360 - 180)
    final_h_err_deg = float(h_err_arr[-1])
    
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
        'final_v_err_kmh': round(final_v_err_kmh, 2),
        'w_mae_degs': round(w_mae_degs, 2),
        'w_rmse_degs': round(w_rmse_degs, 2),
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

ablation_cases = [
    ('A', 'Case A: GT Speed + GT Yaw'),
    ('B', 'Case B: ML Speed + GT Yaw'),
    ('C', 'Case C: GT Speed + ML Yaw'),
    ('D', 'Case D: ML Speed + ML Yaw'),
    ('E', 'Case E: ML Speed + True Heading')
]

all_results = []
plot_data = {}

for dur in [60, 120, 300]:
    plot_data[dur] = []
    for letter, case_name in ablation_cases:
        x_dr, y_dr, v_dr, psi_dr_deg, w_dr = run_ablation_case(start_idx, dur, letter)
        res = evaluate_dr(x_dr, y_dr, v_dr, psi_dr_deg, w_dr, start_idx, dur, case_name)
        plot_data[dur].append(res)
        all_results.append(res)

# Save structured JSON results without numpy arrays
json_results = []
for r in all_results:
    item = {k: v for k, v in r.items() if not isinstance(v, np.ndarray)}
    json_results.append(item)

with open('results/vw4_ml_dr_error_decomposition_results.json', 'w') as f:
    json.dump(json_results, f, indent=2)

df_res = pd.DataFrame(json_results)[['duration_sec', 'case_name', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'drift_rate_ms', 'v_mae_kmh', 'final_h_err_deg']]
print("\n" + "="*115)
print("VW4 UNSEEN TEST SET: ML DEAD-RECKONING ERROR DECOMPOSITION ABLATION MATRIX")
print("="*115)
print(df_res.to_string(index=False))
print("="*115)

# --- High-Quality Visualization Plot Generation ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'

case_colors = {
    'Case A: GT Speed + GT Yaw': '#2ecc71',
    'Case B: ML Speed + GT Yaw': '#3498db',
    'Case C: GT Speed + ML Yaw': '#e67e22',
    'Case D: ML Speed + ML Yaw': '#e74c3c',
    'Case E: ML Speed + True Heading': '#9b59b6'
}

case_styles = {
    'Case A: GT Speed + GT Yaw': ':',
    'Case B: ML Speed + GT Yaw': '--',
    'Case C: GT Speed + ML Yaw': '-.',
    'Case D: ML Speed + ML Yaw': '-',
    'Case E: ML Speed + True Heading': '-'
}

for dur in [60, 120, 300]:
    runs = plot_data[dur]
    t_arr = np.arange(dur * 10) * dt
    
    # Figure 1: Trajectory Comparison
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(runs[0]['x_gt'], runs[0]['y_gt'], 'k-', linewidth=3.0, label='VBOX Ground Truth')
    for r in runs:
        c_name = r['case_name']
        ax.plot(r['x_dr'], r['y_dr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Trajectory Error Decomposition', fontsize=14, fontweight='bold')
    ax.set_xlabel('East Position (m)')
    ax.set_ylabel('North Position (m)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=9, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ml_dr_error_decomposition/outage_{dur}s_trajectory.png', dpi=300)
    plt.close()
    
    # Figure 2: Position Error Growth vs Time
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in runs:
        c_name = r['case_name']
        ax.plot(t_arr, r['pos_err'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Position Error Growth Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Outage Time (seconds)')
    ax.set_ylabel('Position Error (meters)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=9, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ml_dr_error_decomposition/outage_{dur}s_position_error.png', dpi=300)
    plt.close()
    
    # Figure 3: Heading Error vs Time
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in runs:
        c_name = r['case_name']
        ax.plot(t_arr, r['h_err_arr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=2.0, label=c_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Heading Error Growth Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Outage Time (seconds)')
    ax.set_ylabel('Heading Error (degrees)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=9, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ml_dr_error_decomposition/outage_{dur}s_heading_error.png', dpi=300)
    plt.close()

    # Figure 4: Velocity Error vs Time
    fig, ax = plt.subplots(figsize=(10, 6))
    for r in runs:
        c_name = r['case_name']
        ax.plot(t_arr, r['vel_err_arr'], color=case_colors[c_name], linestyle=case_styles[c_name], linewidth=1.8, label=c_name)
    ax.set_title(f'Vw4 Unseen Test Set: {dur}s Outage Speed Error Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Outage Time (seconds)')
    ax.set_ylabel('Speed Error (km/h)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=9, loc='best')
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ml_dr_error_decomposition/outage_{dur}s_velocity_error.png', dpi=300)
    plt.close()

# Figure 5: Summary Ablation Bar Chart
fig, axs = plt.subplots(1, 2, figsize=(15, 6))
fig.suptitle('ML Dead-Reckoning Diagnostic Error Decomposition Summary', fontsize=14, fontweight='bold')

durations = [60, 120, 300]
x_indices = np.arange(len(durations))
width = 0.15

for idx, (letter, c_name) in enumerate(ablation_cases):
    pos_errs = [next(r['final_pos_err_m'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    cde_vals = [next(r['cde_pct'] for r in plot_data[d] if r['case_name'] == c_name) for d in durations]
    
    axs[0].bar(x_indices + idx * width, pos_errs, width, label=c_name, color=case_colors[c_name])
    axs[1].bar(x_indices + idx * width, cde_vals, width, label=c_name, color=case_colors[c_name])

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
axs[1].legend(fontsize=8, loc='best')

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
summary_plot_file = 'plots/vw4/ml_dr_error_decomposition/summary_ablation_metrics.png'
plt.savefig(summary_plot_file, dpi=300)
plt.close()
print(f"Saved plot: {summary_plot_file}")
